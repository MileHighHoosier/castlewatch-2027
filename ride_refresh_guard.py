from datetime import datetime, timedelta, timezone

from sqlalchemy import text

DEFAULT_REFRESH_INTERVAL_SECONDS = 300
RIDE_REFRESH_LOCK_ID = 20271009


def _utc_naive(value):
    if value is None:
        return None
    if value.tzinfo is not None:
        return value.astimezone(timezone.utc).replace(tzinfo=None)
    return value


def _now_utc_naive(now=None):
    if now is None:
        return datetime.now(timezone.utc).replace(tzinfo=None)
    return _utc_naive(now)


def refresh_is_due(last_refresh, now=None, interval_seconds=DEFAULT_REFRESH_INTERVAL_SECONDS):
    if last_refresh is None:
        return True
    interval = max(int(interval_seconds), 1)
    return _utc_naive(last_refresh) <= _now_utc_naive(now) - timedelta(seconds=interval)


def _latest_refresh(connection):
    table_exists = connection.execute(text("SELECT to_regclass('public.wait_times')")).scalar()
    if not table_exists:
        return None
    return connection.execute(text("SELECT MAX(created_at) FROM wait_times")).scalar()


def _iso(value):
    normalized = _utc_naive(value)
    return normalized.isoformat() + "Z" if normalized else None


def guarded_collect_wait_times(engine, collect_wait_times, interval_seconds=DEFAULT_REFRESH_INTERVAL_SECONDS, now=None):
    interval = max(int(interval_seconds), 1)
    check_time = _now_utc_naive(now)

    with engine.begin() as connection:
        latest = _latest_refresh(connection)
        if not refresh_is_due(latest, check_time, interval):
            return {
                "status": "refresh_not_due",
                "refreshed": False,
                "last_refresh": _iso(latest),
                "minimum_interval_seconds": interval,
            }

        acquired = bool(connection.execute(
            text("SELECT pg_try_advisory_xact_lock(:lock_id)"),
            {"lock_id": RIDE_REFRESH_LOCK_ID},
        ).scalar())
        if not acquired:
            return {
                "status": "refresh_in_progress",
                "refreshed": False,
                "last_refresh": _iso(latest),
                "minimum_interval_seconds": interval,
            }

        latest = _latest_refresh(connection)
        if not refresh_is_due(latest, check_time, interval):
            return {
                "status": "refresh_not_due",
                "refreshed": False,
                "last_refresh": _iso(latest),
                "minimum_interval_seconds": interval,
            }

        result = dict(collect_wait_times() or {})
        result.update({
            "status": "refreshed",
            "refreshed": True,
            "minimum_interval_seconds": interval,
        })
        return result
