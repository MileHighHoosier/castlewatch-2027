import json
from datetime import datetime, timedelta, timezone

from flask import jsonify
from sqlalchemy import text

from family_trip import (
    FAMILY_TRIP_ID,
    HISTORY_LIMIT,
    MAX_PAYLOAD_BYTES,
    _authorization_error,
    _json_value,
    setup_family_trip_database,
)

GIB_BYTES = 1024 ** 3
RAILWAY_EGRESS_USD_PER_GIB = 0.05
RAILWAY_VOLUME_USD_PER_GIB_MONTH = 0.15
PRICING_REVIEWED_AT = "2026-07-05"
RESPONSE_OVERHEAD_BYTES = 1024


def _utc_now():
    return datetime.now(timezone.utc)


def _as_utc(value):
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _serialized_size(value):
    if value is None:
        return 0
    normalized = _json_value(value)
    encoded = json.dumps(
        normalized,
        separators=(",", ":"),
        ensure_ascii=False,
        sort_keys=True,
    ).encode("utf-8")
    return len(encoded)


def _usd_for_bytes(byte_count, rate_per_gib):
    return round((max(byte_count, 0) / GIB_BYTES) * rate_per_gib, 10)


def _warning(level, code, message):
    return {
        "level": level,
        "code": code,
        "message": message,
    }


def build_family_operations_report(current, history_rows, now=None):
    now = _as_utc(now) or _utc_now()
    history_rows = list(history_rows or [])

    current_payload = current.get("payload") if current else None
    current_version = int(current.get("version") or 0) if current else 0
    current_updated_at = _as_utc(current.get("updated_at")) if current else None
    current_payload_bytes = _serialized_size(current_payload)

    history_sizes = [_serialized_size(row.get("payload")) for row in history_rows]
    history_bytes = sum(history_sizes)
    history_count = len(history_rows)
    average_snapshot_bytes = round(history_bytes / history_count) if history_count else 0
    projected_history_bytes = average_snapshot_bytes * HISTORY_LIMIT
    projected_database_json_bytes = current_payload_bytes + projected_history_bytes

    day_ago = now - timedelta(hours=24)
    week_ago = now - timedelta(days=7)
    history_times = [
        timestamp
        for timestamp in (_as_utc(row.get("created_at")) for row in history_rows)
        if timestamp is not None
    ]
    versions_last_24_hours = sum(timestamp >= day_ago for timestamp in history_times)
    versions_last_7_days = sum(timestamp >= week_ago for timestamp in history_times)

    estimated_full_read_bytes = current_payload_bytes + RESPONSE_OVERHEAD_BYTES
    estimated_guarded_autosave_bytes = (
        (current_payload_bytes + RESPONSE_OVERHEAD_BYTES) * 2
    )

    warnings = []
    payload_ratio = current_payload_bytes / MAX_PAYLOAD_BYTES if MAX_PAYLOAD_BYTES else 0
    if payload_ratio >= 0.8:
        warnings.append(_warning(
            "critical",
            "payload_near_limit",
            "The shared-plan payload is at least 80% of its safety limit.",
        ))
    elif payload_ratio >= 0.5:
        warnings.append(_warning(
            "warning",
            "payload_growing",
            "The shared-plan payload is above 50% of its safety limit.",
        ))

    if versions_last_24_hours >= 500:
        warnings.append(_warning(
            "critical",
            "very_high_version_churn",
            "At least 500 shared versions were created in the last 24 hours.",
        ))
    elif versions_last_24_hours >= 100:
        warnings.append(_warning(
            "warning",
            "high_version_churn",
            "At least 100 shared versions were created in the last 24 hours.",
        ))

    if history_count >= HISTORY_LIMIT:
        warnings.append(_warning(
            "info",
            "history_at_retention_limit",
            "Backup history is at its retention limit; the oldest snapshot is pruned when a new version is saved.",
        ))

    if not current:
        warnings.append(_warning(
            "info",
            "shared_plan_empty",
            "No shared family plan has been initialized yet.",
        ))

    return {
        "status": "ok",
        "generatedAt": now.isoformat(),
        "scope": "family_trip",
        "measurement": "estimate_from_current_database_state",
        "storage": {
            "currentVersion": current_version,
            "currentUpdatedAt": current_updated_at.isoformat() if current_updated_at else None,
            "currentPayloadBytes": current_payload_bytes,
            "payloadLimitBytes": MAX_PAYLOAD_BYTES,
            "payloadLimitUsedPercent": round(payload_ratio * 100, 2),
            "retainedHistoryCount": history_count,
            "historyLimit": HISTORY_LIMIT,
            "retainedHistoryBytes": history_bytes,
            "averageSnapshotBytes": average_snapshot_bytes,
            "projectedHistoryBytesAtLimit": projected_history_bytes,
            "projectedDatabaseJsonBytesAtLimit": projected_database_json_bytes,
        },
        "activity": {
            "versionsRetained": history_count,
            "versionsCreatedLast24Hours": versions_last_24_hours,
            "versionsCreatedLast7Days": versions_last_7_days,
            "note": "Version counts come from retained backup timestamps and may undercount activity after old snapshots are pruned.",
        },
        "transferEstimates": {
            "estimatedRailwayEgressBytesPerFullRead": estimated_full_read_bytes,
            "estimatedRailwayEgressBytesPerGuardedAutosave": estimated_guarded_autosave_bytes,
            "note": "A guarded autosave is modeled as one preflight read and one save response. Request uploads are not counted as Railway egress.",
        },
        "costEstimates": {
            "estimatedRailwayEgressUsdPerFullRead": _usd_for_bytes(
                estimated_full_read_bytes,
                RAILWAY_EGRESS_USD_PER_GIB,
            ),
            "estimatedRailwayEgressUsdPerGuardedAutosave": _usd_for_bytes(
                estimated_guarded_autosave_bytes,
                RAILWAY_EGRESS_USD_PER_GIB,
            ),
            "estimatedRailwayVolumeUsdPerMonthAtHistoryLimit": _usd_for_bytes(
                projected_database_json_bytes,
                RAILWAY_VOLUME_USD_PER_GIB_MONTH,
            ),
            "note": "These estimates cover CastleWatch family-plan JSON transfer and storage only, not Railway CPU, RAM, database overhead, Vercel usage, taxes, or provider plan fees.",
        },
        "pricingAssumptions": {
            "railwayNetworkEgressUsdPerGiB": RAILWAY_EGRESS_USD_PER_GIB,
            "railwayVolumeStorageUsdPerGiBMonth": RAILWAY_VOLUME_USD_PER_GIB_MONTH,
            "reviewedAt": PRICING_REVIEWED_AT,
            "source": "Railway pricing documentation",
        },
        "controls": {
            "readOnlyReport": True,
            "telemetryRowsWritten": False,
            "historyLimit": HISTORY_LIMIT,
            "payloadLimitBytes": MAX_PAYLOAD_BYTES,
        },
        "warnings": warnings,
    }


def get_family_trip_operations(engine):
    authorization_error = _authorization_error()
    if authorization_error:
        return authorization_error

    with engine.begin() as connection:
        setup_family_trip_database(connection)
        current = connection.execute(text("""
            SELECT payload, version, updated_at
            FROM family_trip_state
            WHERE id = :id
        """), {"id": FAMILY_TRIP_ID}).mappings().first()
        history_rows = connection.execute(text("""
            SELECT version, payload, created_at
            FROM family_trip_history
            WHERE id = :id
            ORDER BY version DESC
            LIMIT :history_limit
        """), {
            "id": FAMILY_TRIP_ID,
            "history_limit": HISTORY_LIMIT,
        }).mappings().all()

    return jsonify(build_family_operations_report(current, history_rows))
