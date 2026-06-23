import os
from datetime import datetime, timezone

from calendar_ingestion import get_calendar_ingestion_status

TRIP_DATES = [
    "2027-10-09",
    "2027-10-10",
    "2027-10-11",
    "2027-10-12",
    "2027-10-13",
    "2027-10-14",
    "2027-10-15",
    "2027-10-16",
]

BASE_ASSIGNMENTS = {
    "2027-10-10": "Magic Kingdom",
    "2027-10-11": "Hollywood Studios",
    "2027-10-13": "Epcot",
    "2027-10-14": "Animal Kingdom",
}

ALTERNATE_ASSIGNMENTS = {
    "2027-10-10": "Epcot",
    "2027-10-11": "Hollywood Studios",
    "2027-10-13": "Magic Kingdom",
    "2027-10-14": "Animal Kingdom",
}

VALID_SCHEDULE_STATUSES = {"unreleased", "partial", "official"}


def _configured_party_dates():
    raw = os.getenv("MNSSHP_2027_DATES", "")
    return sorted({value.strip() for value in raw.split(",") if value.strip()})


def _configured_status(variable_name):
    configured = os.getenv(variable_name, "").strip().lower()
    return configured if configured in VALID_SCHEDULE_STATUSES else None


def _display_time(value):
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return parsed.strftime("%-I:%M %p")
    except (TypeError, ValueError):
        return str(value)


def _party_signal(target_date, party_dates, schedule_status):
    if target_date not in {"2027-10-10", "2027-10-13"}:
        return None

    is_swap_date = target_date == "2027-10-13"

    if schedule_status == "official":
        if target_date in party_dates:
            return {
                "id": "mnsshp",
                "status": "confirmed_event",
                "severity": "high",
                "label": (
                    "Magic Kingdom swap date is a confirmed MNSSHP night"
                    if is_swap_date
                    else "Confirmed MNSSHP night"
                ),
                "summary": (
                    "Do not move Magic Kingdom to Wednesday; regular day-guest hours would end early."
                    if is_swap_date
                    else "Regular Magic Kingdom hours are expected to end early for day guests."
                ),
            }
        return {
            "id": "mnsshp",
            "status": "confirmed_clear",
            "severity": "low",
            "label": (
                "Magic Kingdom swap date is clear"
                if is_swap_date
                else "No MNSSHP loaded for this date"
            ),
            "summary": (
                "Wednesday is clear in the loaded official party schedule and can serve as the Magic Kingdom swap date."
                if is_swap_date
                else "This date is clear in the loaded official party schedule."
            ),
        }

    if is_swap_date:
        return {
            "id": "mnsshp",
            "status": "swap_date_unknown",
            "severity": "medium",
            "label": "Magic Kingdom swap-date status unknown",
            "summary": "Confirm Wednesday is not an MNSSHP night before moving Magic Kingdom here.",
        }

    return {
        "id": "mnsshp",
        "status": "possible_event",
        "severity": "high",
        "label": "Possible MNSSHP night — schedule unreleased",
        "summary": "Do not lock the Magic Kingdom assignment until Disney publishes the 2027 party calendar.",
    }


def _park_hours_signal(target_date, park, hours_status, calendar_data):
    hours = (calendar_data.get("park_hours") or {}).get(f"{park}|{target_date}")
    if hours:
        opening = _display_time(hours.get("openingTime"))
        closing = _display_time(hours.get("closingTime"))
        times = "–".join(value for value in [opening, closing] if value)
        return {
            "id": "park_hours",
            "status": "official",
            "severity": "low",
            "label": f"{park} hours loaded",
            "summary": f"{times}. Use the loaded operating window for arrival and evening planning." if times else "Official operating hours are loaded for this park day.",
        }

    return {
        "id": "park_hours",
        "status": hours_status,
        "severity": "medium" if hours_status != "official" else "low",
        "label": "2027 park hours partially loaded" if hours_status == "partial" else "2027 park hours not loaded",
        "summary": "Early Entry, regular closing time and Extended Evening Hours remain provisional.",
    }


def _day_signals(party_dates, schedule_status, hours_status, calendar_data):
    signals = {target_date: [] for target_date in TRIP_DATES}

    for target_date in TRIP_DATES:
        party = _party_signal(target_date, party_dates, schedule_status)
        if party:
            signals[target_date].append(party)

    signals["2027-10-11"].append({
        "id": "columbus_day",
        "status": "confirmed_holiday",
        "severity": "high",
        "label": "Columbus Day",
        "summary": "Expect holiday-weekend attendance pressure even when historical ride samples look quieter.",
    })

    for target_date, park in BASE_ASSIGNMENTS.items():
        signals[target_date].append(
            _park_hours_signal(target_date, park, hours_status, calendar_data)
        )

    extended = [
        entry for entry in calendar_data.get("extended_evening_hours", [])
        if entry.get("date") == "2027-10-13"
    ]
    if extended:
        parks = ", ".join(sorted({entry.get("park") for entry in extended if entry.get("park")}))
        signals["2027-10-13"].append({
            "id": "extended_evening_hours",
            "status": "official",
            "severity": "low",
            "label": "Extended Evening Hours loaded",
            "summary": f"Extended Evening Hours are represented for {parks or 'the selected park'}. Confirm resort eligibility before relying on them.",
        })
    else:
        signals["2027-10-13"].append({
            "id": "extended_evening_hours",
            "status": "unreleased" if hours_status != "official" else "not_listed",
            "severity": "medium",
            "label": "Extended Evening Hours not confirmed",
            "summary": "Eligibility depends on the final resort and Disney's 2027 operating calendar.",
        })

    return signals


def _scenario(name, assignments, party_dates, schedule_status, hours_status):
    risk_score = 0
    reasons = []

    magic_kingdom_date = next(
        (target_date for target_date, park in assignments.items() if park == "Magic Kingdom"),
        None,
    )

    if magic_kingdom_date:
        if schedule_status == "official" and magic_kingdom_date in party_dates:
            risk_score += 5
            reasons.append(f"Magic Kingdom falls on a confirmed party night: {magic_kingdom_date}.")
        elif schedule_status != "official" and magic_kingdom_date in {"2027-10-10", "2027-10-13"}:
            risk_score += 3
            reasons.append(f"Magic Kingdom remains exposed to an unreleased party schedule on {magic_kingdom_date}.")

    if assignments.get("2027-10-11"):
        risk_score += 2
        reasons.append("Hollywood Studios remains on Columbus Day, so rope-drop planning should stay aggressive.")

    if hours_status != "official":
        risk_score += 1
        reasons.append("Official 2027 park hours are not fully loaded yet.")

    return {
        "id": name,
        "label": "Base plan" if name == "base" else "MNSSHP alternate",
        "assignments": assignments,
        "event_risk_score": risk_score,
        "reasons": reasons,
        "lock_status": "provisional" if schedule_status != "official" or hours_status != "official" else "review",
    }


def _recommendation(base, alternate, party_dates, schedule_status):
    sunday_party = "2027-10-10" in party_dates
    wednesday_party = "2027-10-13" in party_dates

    if schedule_status != "official":
        return {
            "status": "wait_for_calendar",
            "preferred_scenario": "base",
            "headline": "Keep the base plan provisional",
            "summary": "The 2027 MNSSHP schedule is not official. Do not move Magic Kingdom until the party dates are loaded.",
            "decision_rule": "Use the alternate only when Sunday is a confirmed party night and Wednesday is confirmed clear.",
        }

    if sunday_party and not wednesday_party:
        return {
            "status": "recommend_swap",
            "preferred_scenario": "alternate",
            "headline": "Use the MNSSHP alternate",
            "summary": "Sunday is a confirmed party night and Wednesday is clear, so the swap preserves a fuller regular Magic Kingdom day.",
            "decision_rule": "Check confirmed reservations before applying the swap.",
        }

    if not sunday_party:
        return {
            "status": "recommend_base",
            "preferred_scenario": "base",
            "headline": "Keep Magic Kingdom on Sunday",
            "summary": "Sunday is clear in the loaded party schedule, so the base plan avoids unnecessary reservation disruption.",
            "decision_rule": "Continue monitoring official park hours.",
        }

    return {
        "status": "manual_review",
        "preferred_scenario": "base" if base["event_risk_score"] <= alternate["event_risk_score"] else "alternate",
        "headline": "Both Magic Kingdom options need review",
        "summary": "The loaded party schedule does not provide a clean Sunday-to-Wednesday swap.",
        "decision_rule": "Compare reservation impacts and official park hours before locking the park order.",
    }


def _source_note(calendar_status, data_status, source_name):
    ingestion_status = calendar_status.get("status")
    last_success = calendar_status.get("last_success_at")

    if ingestion_status == "unavailable":
        return f"{source_name} could not be checked and no cached schedule is available."
    if ingestion_status == "stale":
        return f"Using the last successful cached schedule from {last_success or 'an earlier check'}; refresh is overdue."
    if ingestion_status == "partial":
        return f"Some park schedules updated, while failed parks retained their last known good data."
    if data_status == "official":
        return f"Official schedule entries were detected automatically. Last successful check: {last_success or 'just now'}."
    if data_status == "partial":
        return f"Some 2027 schedule entries were detected automatically. Last successful check: {last_success or 'just now'}."
    return f"The source was checked automatically, but official 2027 entries are not available yet."


def get_special_event_intelligence(engine=None, refresh_if_stale=True):
    calendar_status = (
        get_calendar_ingestion_status(engine, refresh_if_stale=refresh_if_stale)
        if engine is not None
        else {
            "source": "Environment configuration",
            "status": "unreleased",
            "checked_at": None,
            "last_success_at": None,
            "last_changed_at": None,
            "changed": False,
            "error": None,
            "data": {
                "party_dates": [],
                "mnsshp_status": "unreleased",
                "park_hours_status": "unreleased",
                "park_hours": {},
                "early_entry": [],
                "extended_evening_hours": [],
                "relevant_park_dates_loaded": 0,
                "relevant_park_dates_expected": 4,
            },
        }
    )
    calendar_data = calendar_status.get("data") or {}

    configured_party_dates = _configured_party_dates()
    automatic_party_dates = calendar_data.get("party_dates") or []
    party_dates = sorted(set(configured_party_dates).union(automatic_party_dates))

    configured_schedule_status = _configured_status("MNSSHP_2027_SCHEDULE_STATUS")
    configured_hours_status = _configured_status("WDW_2027_PARK_HOURS_STATUS")
    schedule_status = configured_schedule_status or (
        "official" if configured_party_dates else calendar_data.get("mnsshp_status", "unreleased")
    )
    hours_status = configured_hours_status or calendar_data.get("park_hours_status", "unreleased")

    signals = _day_signals(
        party_dates,
        schedule_status,
        hours_status,
        calendar_data,
    )
    base = _scenario("base", BASE_ASSIGNMENTS, party_dates, schedule_status, hours_status)
    alternate = _scenario("alternate", ALTERNATE_ASSIGNMENTS, party_dates, schedule_status, hours_status)

    ingestion_status = calendar_status.get("status", "unreleased")
    if ingestion_status in {"stale", "unavailable"}:
        overall_status = ingestion_status
    elif schedule_status == "official" and hours_status == "official":
        overall_status = "official"
    elif schedule_status == "partial" or hours_status == "partial" or ingestion_status == "partial":
        overall_status = "partial"
    else:
        overall_status = "provisional"

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "trip_start": TRIP_DATES[0],
        "trip_end": TRIP_DATES[-1],
        "overall_status": overall_status,
        "calendar_ingestion": calendar_status,
        "calendar_data": calendar_data,
        "sources": [
            {
                "id": "mnsshp_calendar",
                "label": "ThemeParks.wiki MNSSHP schedule",
                "status": schedule_status if ingestion_status not in {"stale", "unavailable"} else ingestion_status,
                "data_status": schedule_status,
                "loaded_dates": party_dates,
                "note": _source_note(calendar_status, schedule_status, "The MNSSHP calendar"),
            },
            {
                "id": "park_hours",
                "label": "ThemeParks.wiki park-hours calendar",
                "status": hours_status if ingestion_status not in {"stale", "unavailable"} else ingestion_status,
                "data_status": hours_status,
                "note": _source_note(calendar_status, hours_status, "The park-hours calendar"),
            },
        ],
        "tracked_items": [
            {
                "id": "mnsshp",
                "name": "Mickey's Not-So-Scary Halloween Party",
                "park": "Magic Kingdom",
                "priority": "critical",
                "schedule_status": schedule_status,
            },
            {
                "id": "columbus_day",
                "name": "Columbus Day",
                "park": None,
                "priority": "high",
                "schedule_status": "confirmed",
            },
            {
                "id": "early_entry",
                "name": "Early Theme Park Entry",
                "park": "All parks",
                "priority": "medium",
                "schedule_status": "official" if calendar_data.get("early_entry") else hours_status,
            },
            {
                "id": "extended_evening_hours",
                "name": "Extended Evening Hours",
                "park": "Selected parks",
                "priority": "medium",
                "schedule_status": "official" if calendar_data.get("extended_evening_hours") else hours_status,
            },
        ],
        "day_signals": [
            {"date": target_date, "signals": signals[target_date]}
            for target_date in TRIP_DATES
            if signals[target_date]
        ],
        "scenarios": {
            "base": base,
            "alternate": alternate,
        },
        "recommendation": _recommendation(base, alternate, party_dates, schedule_status),
    }
