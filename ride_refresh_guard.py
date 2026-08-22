from datetime import datetime, timedelta, timezone

from sqlalchemy import text

DEFAULT_REFRESH_INTERVAL_SECONDS = 300
RIDE_REFRESH_LOCK_ID = 20271009
RIDE_REFRESH_STATE_KEY = "ride_refresh"
REFRESH_GUARD_VERSION = "persistent-v2"


def _as_utc(value):
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _now_utc(now=None):
    return _as_utc(now) if now is not None else datetime.now(timezone.utc)


def refresh_is_due(last_refresh, now=None, interval_seconds=DEFAULT_REFRESH_INTERVAL_SECONDS):
    if last_refresh is None:
        return True
    interval = max(int(interval_seconds), 1)
    return _as_utc(last_refresh) <= _now_utc(now) - timedelta(seconds=interval)


def _ensure_refresh_state_table(connection):
    connection.execute(text("""
        CREATE TABLE IF NOT EXISTS castlewatch_runtime_state (
            state_key TEXT PRIMARY KEY,
            last_completed_at TIMESTAMPTZ,
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """))


def _persisted_refresh(connection):
    _ensure_refresh_state_table(connection)
    return connection.execute(text("""
        SELECT last_completed_at
        FROM castlewatch_runtime_state
        WHERE state_key = :state_key
    """), {"state_key": RIDE_REFRESH_STATE_KEY}).scalar()


def _latest_wait_refresh(connection):
    table_exists = connection.execute(text("SELECT to_regclass('public.wait_times')")).scalar()
    if not table_exists:
        return None
    return connection.execute(text("SELECT MAX(created_at) FROM wait_times")).scalar()


def _latest_known_refresh(connection):
    candidates = [
        _persisted_refresh(connection),
        _latest_wait_refresh(connection),
    ]
    normalized = [_as_utc(value) for value in candidates if value is not None]
    return max(normalized) if normalized else None


def _record_refresh(connection, completed_at):
    _ensure_refresh_state_table(connection)
    connection.execute(text("""
        INSERT INTO castlewatch_runtime_state
            (state_key, last_completed_at, updated_at)
        VALUES
            (:state_key, :completed_at, NOW())
        ON CONFLICT (state_key)
        DO UPDATE SET
            last_completed_at = EXCLUDED.last_completed_at,
            updated_at = NOW()
    """), {
        "state_key": RIDE_REFRESH_STATE_KEY,
        "completed_at": _as_utc(completed_at),
    })


def _iso(value):
    normalized = _as_utc(value)
    return normalized.isoformat().replace("+00:00", "Z") if normalized else None


def _base_result(status, refreshed, latest, interval):
    return {
        "status": status,
        "refreshed": refreshed,
        "last_refresh": _iso(latest),
        "minimum_interval_seconds": interval,
        "refresh_guard": REFRESH_GUARD_VERSION,
    }


def guarded_collect_wait_times(
    engine,
    collect_wait_times,
    interval_seconds=DEFAULT_REFRESH_INTERVAL_SECONDS,
    now=None,
):
    """Serialize and rate-limit expensive Queue Times collection work.

    The advisory transaction lock is acquired before freshness is checked so two
    near-simultaneous requests cannot both decide a refresh is due. A dedicated
    PostgreSQL state row records the last successful collection; the newest
    wait_times timestamp remains a fallback for migration/backfill safety.
    """
    interval = max(int(interval_seconds), 1)
    check_time = _now_utc(now)

    with engine.begin() as connection:
        acquired = bool(connection.execute(
            text("SELECT pg_try_advisory_xact_lock(:lock_id)"),
            {"lock_id": RIDE_REFRESH_LOCK_ID},
        ).scalar())
        if not acquired:
            return _base_result("refresh_in_progress", False, None, interval)

        latest = _latest_known_refresh(connection)
        if not refresh_is_due(latest, check_time, interval):
            return _base_result("refresh_not_due", False, latest, interval)

        result = dict(collect_wait_times() or {})
        completed_at = _now_utc()
        _record_refresh(connection, completed_at)
        result.update(_base_result("refreshed", True, completed_at, interval))
        return result
