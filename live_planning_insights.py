from datetime import datetime

from sqlalchemy import text


def get_live_planning_insights(engine, park, should_include_attraction):
    """Return dashboard historical insights without blocking on tomorrow forecast work.

    The Park Command Center needs historical totals and current-vs-typical
    comparisons. Tomorrow forecasting is a separate planning concern and should
    not be allowed to make the live dashboard's History stat disappear.
    """
    current_hour = datetime.utcnow().hour

    with engine.connect() as connection:
        historical_rows = connection.execute(text("""
            WITH latest AS (
                SELECT DISTINCT ON (ride_name)
                    ride_name,
                    land,
                    wait_time,
                    is_open,
                    created_at
                FROM wait_times
                WHERE park = :park
                  AND ride_name IS NOT NULL
                  AND created_at IS NOT NULL
                ORDER BY ride_name, created_at DESC
            ), history AS (
                SELECT
                    ride_name,
                    land,
                    COUNT(*) AS samples,
                    ROUND(AVG(wait_time))::INTEGER AS average_wait,
                    MAX(wait_time) AS peak_wait,
                    ROUND(AVG(CASE WHEN EXTRACT(HOUR FROM created_at) = :current_hour THEN wait_time ELSE NULL END))::INTEGER AS same_hour_average,
                    COUNT(CASE WHEN EXTRACT(HOUR FROM created_at) = :current_hour THEN 1 END) AS same_hour_samples
                FROM wait_times
                WHERE park = :park
                  AND ride_name IS NOT NULL
                  AND created_at IS NOT NULL
                GROUP BY ride_name, land
            )
            SELECT
                h.ride_name,
                h.land,
                h.samples,
                h.average_wait,
                h.peak_wait,
                h.same_hour_average,
                h.same_hour_samples,
                l.wait_time AS current_wait,
                l.is_open,
                l.created_at AS current_updated_at
            FROM history h
            LEFT JOIN latest l ON h.ride_name = l.ride_name
            ORDER BY h.average_wait DESC NULLS LAST
        """), {
            "park": park,
            "current_hour": current_hour,
        })

        rides = []
        for row in historical_rows:
            if not should_include_attraction(row.ride_name):
                continue

            typical_wait = (
                row.same_hour_average
                if row.same_hour_samples
                and row.same_hour_samples >= 3
                and row.same_hour_average is not None
                else row.average_wait
            )
            current_wait = row.current_wait if row.current_wait is not None else 0
            opportunity_score = max((typical_wait or 0) - current_wait, 0)
            pressure_score = max(current_wait - (typical_wait or 0), 0)

            rides.append({
                "name": row.ride_name,
                "land": row.land,
                "samples": row.samples,
                "average_wait": row.average_wait,
                "peak_wait": row.peak_wait,
                "same_hour_average": row.same_hour_average,
                "same_hour_samples": row.same_hour_samples,
                "current_wait": current_wait,
                "is_open": row.is_open,
                "typical_wait": typical_wait,
                "opportunity_score": opportunity_score,
                "pressure_score": pressure_score,
                "current_updated_at": row.current_updated_at.isoformat() if row.current_updated_at else None,
            })

    open_rides = [ride for ride in rides if ride.get("is_open") is not False]
    best_now = sorted(
        open_rides,
        key=lambda ride: (-ride["opportunity_score"], ride["current_wait"], -(ride["samples"] or 0)),
    )[:5]
    unusually_high = sorted(
        open_rides,
        key=lambda ride: (-ride["pressure_score"], -ride["current_wait"]),
    )[:5]
    reliable_low_wait = sorted(
        open_rides,
        key=lambda ride: (
            ride["typical_wait"] if ride["typical_wait"] is not None else 999,
            ride["current_wait"],
        ),
    )[:5]

    land_map = {}
    for ride in rides:
        land = ride["land"] or "Unassigned Area"
        land_map.setdefault(land, []).append(ride)

    lands = []
    for land, land_rides in land_map.items():
        open_land_rides = [ride for ride in land_rides if ride.get("is_open") is not False]
        if not open_land_rides:
            continue

        avg_current = round(sum(ride["current_wait"] for ride in open_land_rides) / len(open_land_rides))
        avg_typical_values = [
            ride["typical_wait"]
            for ride in open_land_rides
            if ride["typical_wait"] is not None
        ]
        avg_typical = round(sum(avg_typical_values) / len(avg_typical_values)) if avg_typical_values else 0

        lands.append({
            "land": land,
            "open_rides": len(open_land_rides),
            "average_current_wait": avg_current,
            "average_typical_wait": avg_typical,
            "trend": (
                "better_than_usual"
                if avg_current < avg_typical
                else "busier_than_usual"
                if avg_current > avg_typical
                else "normal"
            ),
        })

    lands = sorted(
        lands,
        key=lambda land: land["average_current_wait"] - land["average_typical_wait"],
    )

    summary = "Historical sample is still small. Recommendations will improve as CastleWatch collects more refreshes."
    if len(rides) >= 5:
        if best_now and best_now[0]["opportunity_score"] > 0:
            summary = f"{best_now[0]['name']} looks better than its historical pattern right now."
        elif reliable_low_wait:
            summary = f"{reliable_low_wait[0]['name']} is the safest low-wait option based on current and historical data."

    return {
        "park": park,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "current_hour_utc": current_hour,
        "historical_entries_analyzed": sum(ride["samples"] for ride in rides),
        "rides_analyzed": len(rides),
        "summary": summary,
        "best_now": best_now,
        "unusually_high": unusually_high,
        "reliable_low_wait": reliable_low_wait,
        "land_trends": lands,
        "tomorrow_forecast": {
            "status": "deferred",
            "summary": "Tomorrow forecasting is intentionally separate from the live dashboard response.",
        },
    }
