import hashlib
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta

import requests
from sqlalchemy import text

SOURCE_KEY = "themeparks_wiki_wdw_2027_10"
SOURCE_LABEL = "ThemeParks.wiki Walt Disney World schedule"
TARGET_YEAR = 2027
TARGET_MONTH = 10
STALE_AFTER_HOURS = int(os.getenv("CALENDAR_STALE_AFTER_HOURS", "24"))
REQUEST_TIMEOUT_SECONDS = int(os.getenv("CALENDAR_REQUEST_TIMEOUT_SECONDS", "10"))
CALENDAR_USER_AGENT = os.getenv(
    "CALENDAR_USER_AGENT",
    "CastleWatch/1.0 personal Disney planning app; contact: castlewatch@example.com",
)

TRIP_DATES = {
    "2027-10-09",
    "2027-10-10",
    "2027-10-11",
    "2027-10-12",
    "2027-10-13",
    "2027-10-14",
    "2027-10-15",
    "2027-10-16",
}

PARK_IDS = {
    "Magic Kingdom": "75ea578a-adc8-4116-a54d-dccb60765ef9",
    "Epcot": "47f90d2c-e191-4239-a466-5892ef59a88b",
    "Hollywood Studios": "288747d1-8b4f-4a64-867e-ea7c9b27bad8",
    "Animal Kingdom": "1c84a229-8862-4648-9c71-378ddd2c7693",
}

RELEVANT_PARK_DATES = {
    ("Magic Kingdom", "2027-10-10"),
    ("Hollywood Studios", "2027-10-11"),
    ("Epcot", "2027-10-13"),
    ("Animal Kingdom", "2027-10-14"),
}


def _utcnow():
    return datetime.utcnow()


def _iso(value):
    if not value:
        return None
    if isinstance(value, str):
        return value
    return value.isoformat() + "Z"


def _setup_cache(connection):
    connection.execute(text("""
        CREATE TABLE IF NOT EXISTS calendar_ingestion_cache (
            source_key TEXT PRIMARY KEY,
            source_label TEXT,
            payload TEXT,
            content_hash TEXT,
            last_checked_at TIMESTAMP,
            last_success_at TIMESTAMP,
            last_changed_at TIMESTAMP,
            last_error TEXT
        )
    """))
    connection.commit()


def _read_cache(engine):
    with engine.connect() as connection:
        _setup_cache(connection)
        row = connection.execute(text("""
            SELECT source_key, source_label, payload, content_hash,
                   last_checked_at, last_success_at, last_changed_at, last_error
            FROM calendar_ingestion_cache
            WHERE source_key = :source_key
        """), {"source_key": SOURCE_KEY}).mappings().first()

    if not row:
        return None

    payload = None
    if row.get("payload"):
        try:
            payload = json.loads(row["payload"])
        except (TypeError, json.JSONDecodeError):
            payload = None

    return {
        **dict(row),
        "payload": payload,
    }


def _write_success(engine, payload, content_hash, checked_at, changed, error_message=None):
    existing = _read_cache(engine)
    changed_at = checked_at if changed or not existing else existing.get("last_changed_at")

    with engine.connect() as connection:
        _setup_cache(connection)
        connection.execute(text("""
            INSERT INTO calendar_ingestion_cache (
                source_key, source_label, payload, content_hash,
                last_checked_at, last_success_at, last_changed_at, last_error
            ) VALUES (
                :source_key, :source_label, :payload, :content_hash,
                :last_checked_at, :last_success_at, :last_changed_at, :last_error
            )
            ON CONFLICT (source_key) DO UPDATE SET
                source_label = EXCLUDED.source_label,
                payload = EXCLUDED.payload,
                content_hash = EXCLUDED.content_hash,
                last_checked_at = EXCLUDED.last_checked_at,
                last_success_at = EXCLUDED.last_success_at,
                last_changed_at = EXCLUDED.last_changed_at,
                last_error = EXCLUDED.last_error
        """), {
            "source_key": SOURCE_KEY,
            "source_label": SOURCE_LABEL,
            "payload": json.dumps(payload, sort_keys=True),
            "content_hash": content_hash,
            "last_checked_at": checked_at,
            "last_success_at": checked_at,
            "last_changed_at": changed_at,
            "last_error": error_message,
        })
        connection.commit()


def _write_failure(engine, checked_at, error_message):
    existing = _read_cache(engine)

    with engine.connect() as connection:
        _setup_cache(connection)
        if existing:
            connection.execute(text("""
                UPDATE calendar_ingestion_cache
                SET last_checked_at = :last_checked_at,
                    last_error = :last_error
                WHERE source_key = :source_key
            """), {
                "source_key": SOURCE_KEY,
                "last_checked_at": checked_at,
                "last_error": error_message,
            })
        else:
            connection.execute(text("""
                INSERT INTO calendar_ingestion_cache (
                    source_key, source_label, payload, content_hash,
                    last_checked_at, last_success_at, last_changed_at, last_error
                ) VALUES (
                    :source_key, :source_label, NULL, NULL,
                    :last_checked_at, NULL, NULL, :last_error
                )
            """), {
                "source_key": SOURCE_KEY,
                "source_label": SOURCE_LABEL,
                "last_checked_at": checked_at,
                "last_error": error_message,
            })
        connection.commit()


def _normalize_schedule_item(item):
    if not isinstance(item, dict):
        return None

    date_value = item.get("date") or item.get("scheduleDate")
    if not date_value or not str(date_value).startswith("2027-10"):
        return None

    return {
        "date": str(date_value)[:10],
        "type": item.get("type") or item.get("scheduleType") or item.get("status"),
        "description": item.get("description") or item.get("name") or item.get("title"),
        "openingTime": item.get("openingTime") or item.get("startTime") or item.get("start"),
        "closingTime": item.get("closingTime") or item.get("endTime") or item.get("end"),
    }


def _fetch_park_schedule(park_name, park_id):
    url = f"https://api.themeparks.wiki/v1/entity/{park_id}/schedule"
    response = requests.get(
        url,
        params={"year": TARGET_YEAR, "month": TARGET_MONTH},
        headers={"Accept": "application/json", "User-Agent": CALENDAR_USER_AGENT},
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    data = response.json()
    raw_schedule = data.get("schedule") if isinstance(data, dict) else data
    if not isinstance(raw_schedule, list):
        raw_schedule = []

    normalized = []
    for item in raw_schedule:
        parsed = _normalize_schedule_item(item)
        if parsed:
            normalized.append(parsed)

    normalized.sort(key=lambda item: (
        item.get("date") or "",
        item.get("openingTime") or "",
        item.get("description") or "",
    ))

    return {
        "park": park_name,
        "url": url,
        "schedule": normalized,
        "returned_items": len(normalized),
    }


def _fetch_all_schedules():
    results = {}
    errors = {}

    with ThreadPoolExecutor(max_workers=4) as executor:
        future_map = {
            executor.submit(_fetch_park_schedule, park_name, park_id): park_name
            for park_name, park_id in PARK_IDS.items()
        }
        for future in as_completed(future_map):
            park_name = future_map[future]
            try:
                results[park_name] = future.result()
            except Exception as error:
                errors[park_name] = str(error)

    return results, errors


def _combined_text(item):
    values = [item.get("type"), item.get("description")]
    return " ".join(str(value) for value in values if value).lower().replace("’", "'")


def _is_operating(item):
    text_value = _combined_text(item)
    return (
        str(item.get("type") or "").upper() == "OPERATING"
        or "park open" in text_value
        or (item.get("openingTime") and item.get("closingTime") and "early entry" not in text_value and "extended evening" not in text_value)
    )


def _is_mnsshp(item):
    text_value = _combined_text(item)
    return "not-so-scary" in text_value or "not so scary" in text_value or "mnsshp" in text_value


def _is_early_entry(item):
    text_value = _combined_text(item)
    return "early theme park entry" in text_value or "early entry" in text_value


def _is_extended_evening(item):
    text_value = _combined_text(item)
    return "extended evening" in text_value


def _extract_calendar_data(payload):
    park_schedules = payload.get("park_schedules") or {}
    park_hours = {}
    early_entry = []
    extended_evening = []
    party_dates = set()
    covered_operating_dates = set()

    for park_name, park_payload in park_schedules.items():
        schedule = (park_payload or {}).get("schedule") or []
        for item in schedule:
            date_value = item.get("date")
            if not date_value:
                continue

            if _is_operating(item):
                covered_operating_dates.add((park_name, date_value))
                if date_value in TRIP_DATES:
                    park_hours[f"{park_name}|{date_value}"] = {
                        "park": park_name,
                        "date": date_value,
                        "openingTime": item.get("openingTime"),
                        "closingTime": item.get("closingTime"),
                        "description": item.get("description") or "Park operating hours",
                    }

            if park_name == "Magic Kingdom" and _is_mnsshp(item):
                party_dates.add(date_value)

            if _is_early_entry(item):
                early_entry.append({"park": park_name, **item})

            if _is_extended_evening(item):
                extended_evening.append({"park": park_name, **item})

    relevant_coverage = len(RELEVANT_PARK_DATES.intersection(covered_operating_dates))
    if relevant_coverage == len(RELEVANT_PARK_DATES):
        park_hours_status = "official"
    elif relevant_coverage > 0:
        park_hours_status = "partial"
    else:
        park_hours_status = "unreleased"

    # Seeing any October MNSSHP entries indicates the party calendar is represented
    # in the source. Candidate dates absent from that loaded month can then be treated
    # as clear. Until that happens, CastleWatch keeps the schedule provisional.
    mnsshp_status = "official" if party_dates else "unreleased"

    return {
        "party_dates": sorted(party_dates),
        "mnsshp_status": mnsshp_status,
        "park_hours_status": park_hours_status,
        "park_hours": park_hours,
        "early_entry": early_entry,
        "extended_evening_hours": extended_evening,
        "relevant_park_dates_loaded": relevant_coverage,
        "relevant_park_dates_expected": len(RELEVANT_PARK_DATES),
    }


def _content_hash(payload):
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _status_from_cache(cache, partial=False, changed=False):
    payload = (cache or {}).get("payload") or {}
    last_success_at = (cache or {}).get("last_success_at")
    last_checked_at = (cache or {}).get("last_checked_at")
    last_changed_at = (cache or {}).get("last_changed_at")
    last_error = (cache or {}).get("last_error")

    if not payload:
        status = "unavailable" if last_error else "unreleased"
        freshness_hours = None
    elif not last_success_at:
        status = "unavailable"
        freshness_hours = None
    else:
        freshness_hours = max((_utcnow() - last_success_at).total_seconds() / 3600, 0)
        if partial:
            status = "partial"
        elif freshness_hours > STALE_AFTER_HOURS:
            status = "stale"
        else:
            status = "fresh"

    return {
        "source_key": SOURCE_KEY,
        "source": SOURCE_LABEL,
        "status": status,
        "checked_at": _iso(last_checked_at),
        "last_success_at": _iso(last_success_at),
        "last_changed_at": _iso(last_changed_at),
        "freshness_hours": round(freshness_hours, 1) if freshness_hours is not None else None,
        "changed": changed,
        "error": last_error,
        "data": _extract_calendar_data(payload) if payload else {
            "party_dates": [],
            "mnsshp_status": "unreleased",
            "park_hours_status": "unreleased",
            "park_hours": {},
            "early_entry": [],
            "extended_evening_hours": [],
            "relevant_park_dates_loaded": 0,
            "relevant_park_dates_expected": len(RELEVANT_PARK_DATES),
        },
    }


def refresh_calendar_ingestion(engine, force=True):
    checked_at = _utcnow()
    existing = _read_cache(engine)

    if not force and existing and existing.get("last_checked_at"):
        age = checked_at - existing["last_checked_at"]
        if age < timedelta(hours=STALE_AFTER_HOURS):
            return _status_from_cache(existing)

    fetched, errors = _fetch_all_schedules()
    existing_payload = (existing or {}).get("payload") or {}
    existing_parks = existing_payload.get("park_schedules") or {}

    if not fetched:
        error_message = "; ".join(f"{park}: {message}" for park, message in sorted(errors.items())) or "Calendar source returned no usable schedules."
        _write_failure(engine, checked_at, error_message)
        return _status_from_cache(_read_cache(engine))

    merged_parks = dict(existing_parks)
    merged_parks.update(fetched)
    payload = {
        "year": TARGET_YEAR,
        "month": TARGET_MONTH,
        "park_schedules": merged_parks,
        "successful_parks": sorted(fetched.keys()),
        "failed_parks": sorted(errors.keys()),
    }
    digest = _content_hash(payload)
    changed = digest != (existing or {}).get("content_hash")
    error_message = "; ".join(f"{park}: {message}" for park, message in sorted(errors.items())) or None
    _write_success(engine, payload, digest, checked_at, changed, error_message)

    return _status_from_cache(_read_cache(engine), partial=bool(errors), changed=changed)


def get_calendar_ingestion_status(engine, refresh_if_stale=True):
    cache = _read_cache(engine)
    if refresh_if_stale:
        return refresh_calendar_ingestion(engine, force=False)
    return _status_from_cache(cache)
