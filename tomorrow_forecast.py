from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import text

WDW_TIMEZONE = ZoneInfo("America/New_York")

TIME_BLOCKS = [
    {"key": "morning", "label": "Morning", "window": "8:00–11:00 AM", "start": 8, "end": 11},
    {"key": "midday", "label": "Midday", "window": "11:00 AM–2:00 PM", "start": 11, "end": 14},
    {"key": "afternoon", "label": "Afternoon", "window": "2:00–5:00 PM", "start": 14, "end": 17},
    {"key": "evening", "label": "Evening", "window": "5:00–10:00 PM", "start": 17, "end": 22},
]


def _postgres_dow(date_value):
    # Python: Monday=0. PostgreSQL EXTRACT(DOW): Sunday=0.
    return (date_value.weekday() + 1) % 7


def _block_case_sql():
    clauses = []
    for block in TIME_BLOCKS:
        clauses.append(
            f"WHEN local_hour >= {block['start']} AND local_hour < {block['end']} THEN '{block['key']}'"
        )
    return "CASE " + " ".join(clauses) + " ELSE NULL END"


def _block_metadata(key):
    return next((block for block in TIME_BLOCKS if block["key"] == key), None)


def _ensure_indexes(connection):
    connection.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_wait_times_park_created_at
        ON wait_times (park, created_at)
    """))
    connection.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_wait_times_park_ride_created_at
        ON wait_times (park, ride_name, created_at DESC)
    """))
    connection.commit()


def _load_block_rows(connection, park, target_dow=None):
    block_case = _block_case_sql()
    weekday_filter = "AND local_dow = :target_dow" if target_dow is not None else ""
    params = {"park": park}
    if target_dow is not None:
        params["target_dow"] = target_dow

    result = connection.execute(text(f"""
        WITH localized AS (
            SELECT
                wait_time,
                (((created_at AT TIME ZONE 'UTC') AT TIME ZONE 'America/New_York')) AS local_ts
            FROM wait_times
            WHERE park = :park
              AND ride_name IS NOT NULL
              AND wait_time IS NOT NULL
              AND wait_time >= 0
              AND created_at IS NOT NULL
              AND is_open IS DISTINCT FROM FALSE
        ), bucketed AS (
            SELECT
                wait_time,
                local_ts::date AS local_date,
                EXTRACT(DOW FROM local_ts)::INTEGER AS local_dow,
                EXTRACT(HOUR FROM local_ts)::INTEGER AS local_hour
            FROM localized
        ), labeled AS (
            SELECT
                wait_time,
                local_date,
                local_dow,
                {block_case} AS block_key
            FROM bucketed
        )
        SELECT
            block_key,
            COUNT(*)::INTEGER AS samples,
            COUNT(DISTINCT local_date)::INTEGER AS distinct_days,
            ROUND(AVG(wait_time))::INTEGER AS average_wait
        FROM labeled
        WHERE block_key IS NOT NULL
          {weekday_filter}
        GROUP BY block_key
    """), params)

    rows = []
    for row in result:
        metadata = _block_metadata(row.block_key)
        if not metadata:
            continue
        rows.append({
            "key": row.block_key,
            "label": metadata["label"],
            "window": metadata["window"],
            "samples": int(row.samples or 0),
            "distinct_days": int(row.distinct_days or 0),
            "average_wait": int(row.average_wait or 0),
        })

    order = {block["key"]: index for index, block in enumerate(TIME_BLOCKS)}
    return sorted(rows, key=lambda row: order.get(row["key"], 99))


def _weighted_average(blocks):
    total_samples = sum(block["samples"] for block in blocks)
    if total_samples <= 0:
        return 0
    weighted = sum(block["average_wait"] * block["samples"] for block in blocks)
    return round(weighted / total_samples)


def _comparison_label(percent_difference):
    if percent_difference <= -15:
        return "noticeably_quieter"
    if percent_difference <= -7:
        return "slightly_quieter"
    if percent_difference >= 15:
        return "noticeably_busier"
    if percent_difference >= 7:
        return "slightly_busier"
    return "near_typical"


def _summary(weekday, comparison, source):
    if source != "same_weekday":
        return f"Not enough matching {weekday} history yet, so this forecast uses the park's overall day pattern."

    messages = {
        "noticeably_quieter": f"Prior {weekday}s have usually been noticeably quieter than the park's average day.",
        "slightly_quieter": f"Prior {weekday}s have usually been slightly quieter than the park's average day.",
        "noticeably_busier": f"Prior {weekday}s have usually been noticeably busier than the park's average day.",
        "slightly_busier": f"Prior {weekday}s have usually been slightly busier than the park's average day.",
        "near_typical": f"Prior {weekday}s have usually been close to the park's average day.",
    }
    return messages[comparison]


def _confidence(source, samples, distinct_days):
    if source != "same_weekday":
        return {"level": "low", "label": "Low confidence"}
    if samples >= 250 and distinct_days >= 6:
        return {"level": "high", "label": "Higher confidence"}
    if samples >= 100 and distinct_days >= 3:
        return {"level": "medium", "label": "Medium confidence"}
    return {"level": "early", "label": "Early signal"}


def get_tomorrow_forecast(engine, park):
    now_eastern = datetime.now(WDW_TIMEZONE)
    tomorrow = (now_eastern + timedelta(days=1)).date()
    weekday = tomorrow.strftime("%A")
    target_dow = _postgres_dow(tomorrow)

    with engine.connect() as connection:
        _ensure_indexes(connection)
        connection.execute(text("SET LOCAL statement_timeout = '9000ms'"))
        weekday_blocks = _load_block_rows(connection, park, target_dow)
        overall_blocks = _load_block_rows(connection, park)

    weekday_samples = sum(block["samples"] for block in weekday_blocks)
    weekday_days = max([block["distinct_days"] for block in weekday_blocks] or [0])
    weekday_ready = weekday_samples >= 40 and weekday_days >= 2 and len(weekday_blocks) >= 2

    source = "same_weekday" if weekday_ready else "overall_baseline"
    forecast_blocks = weekday_blocks if weekday_ready else overall_blocks
    forecast_samples = sum(block["samples"] for block in forecast_blocks)
    forecast_days = max([block["distinct_days"] for block in forecast_blocks] or [0])

    if not forecast_blocks:
        return {
            "date": tomorrow.isoformat(),
            "weekday": weekday,
            "timezone": "America/New_York",
            "status": "learning",
            "source": "insufficient_data",
            "summary": "CastleWatch is still collecting enough history to forecast tomorrow.",
            "confidence": {"level": "low", "label": "Low confidence"},
            "blocks": [],
            "best_window": None,
            "peak_window": None,
        }

    forecast_average = _weighted_average(forecast_blocks)
    overall_average = _weighted_average(overall_blocks)
    percent_difference = 0
    if overall_average > 0:
        percent_difference = round(((forecast_average - overall_average) / overall_average) * 100)

    comparison = _comparison_label(percent_difference) if source == "same_weekday" else "near_typical"
    best_window = min(forecast_blocks, key=lambda block: (block["average_wait"], -block["samples"]))
    peak_window = max(forecast_blocks, key=lambda block: (block["average_wait"], block["samples"]))

    return {
        "date": tomorrow.isoformat(),
        "weekday": weekday,
        "timezone": "America/New_York",
        "status": "ready" if source == "same_weekday" else "fallback",
        "source": source,
        "comparison": comparison,
        "comparison_percent": percent_difference,
        "summary": _summary(weekday, comparison, source),
        "confidence": _confidence(source, forecast_samples, forecast_days),
        "sample_count": forecast_samples,
        "distinct_days": forecast_days,
        "blocks": forecast_blocks,
        "best_window": best_window,
        "peak_window": peak_window,
    }
