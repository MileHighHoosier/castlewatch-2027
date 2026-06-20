import os
import requests
from datetime import datetime

from flask import Flask, jsonify, request
from flask_cors import CORS
from sqlalchemy import create_engine, text

from tomorrow_forecast import get_tomorrow_forecast
from trip_week import get_trip_week_plan

app = Flask(__name__)
CORS(app)

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable is missing")

engine = create_engine(DATABASE_URL)

# Queue Times park IDs for the four Walt Disney World theme parks.
PARKS = [
    {"id": 6, "name": "Magic Kingdom"},
    {"id": 5, "name": "Epcot"},
    {"id": 7, "name": "Hollywood Studios"},
    {"id": 8, "name": "Animal Kingdom"},
]

# Approximate Walt Disney World Resort coordinates for official weather alerts.
WDW_LATITUDE = 28.3772
WDW_LONGITUDE = -81.5707
WEATHER_USER_AGENT = os.getenv(
    "WEATHER_USER_AGENT",
    "CastleWatch/1.0 personal Disney planning app; contact: castlewatch@example.com",
)

HEAT_ALERT_KEYWORDS = [
    "heat advisory",
    "excessive heat warning",
    "excessive heat watch",
]

STORM_ALERT_KEYWORDS = [
    "severe thunderstorm warning",
    "severe thunderstorm watch",
    "tornado warning",
    "tornado watch",
    "flash flood warning",
]

CHARACTER_MEET_KEYWORDS = [
    "meet",
    "greet",
    "character",
    "princess fairytale hall",
    "adventurers outpost",
    "royal sommerhus",
    "town square theater",
]

# Queue Times includes many shows, trails, exhibits, play areas, and walkthroughs.
# CastleWatch is intended to focus on ride-demand attractions only.
NON_RIDE_EXPERIENCE_KEYWORDS = [
    "affection section",
    "animal care",
    "beauty and the beast live on stage",
    "bird",
    "boneyard",
    "conservation station",
    "discovery island trails",
    "entertainment",
    "exploration trail",
    "feathered friends",
    "festival",
    "finding nemo",
    "gorilla falls",
    "hall of presidents",
    "hoop-dee-doo",
    "indiana jones epic stunt spectacular",
    "journey of water",
    "lightning mcqueen",
    "live on stage",
    "mickey shorts theater",
    "muppet*vision",
    "muppet vision",
    "nighttime spectacular",
    "play disney parks",
    "rafiki",
    "sing-along",
    "stage",
    "swiss family treehouse",
    "the american adventure",
    "the boneyard",
    "tiki room",
    "tom sawyer island",
    "trail",
    "tree of life awakenings",
    "vacation fun",
    "walt disney presents",
    "wildlife express train",
]

PARK_ALIASES = {
    "mk": "Magic Kingdom",
    "magic kingdom": "Magic Kingdom",
    "epcot": "Epcot",
    "hs": "Hollywood Studios",
    "hollywood studios": "Hollywood Studios",
    "animal kingdom": "Animal Kingdom",
    "ak": "Animal Kingdom",
}


def is_character_meet(name):
    if not name:
        return False

    normalized = name.lower()
    return any(keyword in normalized for keyword in CHARACTER_MEET_KEYWORDS)


def is_non_ride_experience(name):
    if not name:
        return True

    normalized = name.lower()
    return any(keyword in normalized for keyword in NON_RIDE_EXPERIENCE_KEYWORDS)


def should_include_attraction(name):
    return not is_character_meet(name) and not is_non_ride_experience(name)


def normalize_park(value):
    if not value:
        return "Magic Kingdom"

    normalized = value.strip().lower()
    return PARK_ALIASES.get(normalized, value.strip())


def alert_text(feature):
    properties = feature.get("properties") or {}
    parts = [
        properties.get("event"),
        properties.get("headline"),
        properties.get("description"),
        properties.get("instruction"),
    ]
    return " ".join(str(part) for part in parts if part).lower()


def classify_weather_alert(feature):
    text_value = alert_text(feature)
    if any(keyword in text_value for keyword in HEAT_ALERT_KEYWORDS):
        return "hot"
    if any(keyword in text_value for keyword in STORM_ALERT_KEYWORDS):
        return "storm"
    return None


def get_weather_advisory():
    url = "https://api.weather.gov/alerts/active"
    response = requests.get(
        url,
        params={"point": f"{WDW_LATITUDE},{WDW_LONGITUDE}"},
        headers={
            "Accept": "application/geo+json",
            "User-Agent": WEATHER_USER_AGENT,
        },
        timeout=12,
    )
    response.raise_for_status()
    data = response.json()
    features = data.get("features") or []

    classified_alerts = []
    for feature in features:
        mode = classify_weather_alert(feature)
        if not mode:
            continue
        properties = feature.get("properties") or {}
        classified_alerts.append({
            "mode": mode,
            "event": properties.get("event"),
            "headline": properties.get("headline") or properties.get("event"),
            "severity": properties.get("severity"),
            "effective": properties.get("effective"),
            "expires": properties.get("expires"),
            "source": "weather.gov",
        })

    if not classified_alerts:
        return {
            "advisoryActive": False,
            "mode": "normal",
            "advisoryType": None,
            "headline": None,
            "expiresAt": None,
            "source": "weather.gov",
            "checkedAt": datetime.utcnow().isoformat() + "Z",
        }

    primary = next((alert for alert in classified_alerts if alert["mode"] == "hot"), classified_alerts[0])
    return {
        "advisoryActive": True,
        "mode": primary["mode"],
        "advisoryType": primary.get("event"),
        "headline": primary.get("headline"),
        "expiresAt": primary.get("expires"),
        "source": primary.get("source"),
        "alerts": classified_alerts,
        "checkedAt": datetime.utcnow().isoformat() + "Z",
    }


def setup_database(connection):
    connection.execute(text("""
        CREATE TABLE IF NOT EXISTS wait_times (
            id SERIAL PRIMARY KEY,
            park TEXT,
            ride_name TEXT,
            land TEXT,
            wait_time INTEGER,
            is_open BOOLEAN,
            created_at TIMESTAMP
        )
    """))

    connection.execute(text("""
        ALTER TABLE wait_times
        ADD COLUMN IF NOT EXISTS park TEXT
    """))

    connection.execute(text("""
        ALTER TABLE wait_times
        ADD COLUMN IF NOT EXISTS land TEXT
    """))

    connection.execute(text("""
        ALTER TABLE wait_times
        ADD COLUMN IF NOT EXISTS is_open BOOLEAN
    """))


def collect_wait_times():
    inserted = 0
    skipped_character_meets = 0
    skipped_non_ride_experiences = 0
    park_results = []

    with engine.connect() as connection:
        setup_database(connection)

        for park in PARKS:
            url = f"https://queue-times.com/parks/{park['id']}/queue_times.json"
            response = requests.get(url, timeout=20)
            response.raise_for_status()
            data = response.json()

            park_inserted = 0
            park_skipped_character_meets = 0
            park_skipped_non_rides = 0
            lands = data.get("lands", [])

            for land in lands:
                rides = land.get("rides", [])

                for ride in rides:
                    name = ride.get("name")

                    if is_character_meet(name):
                        skipped_character_meets += 1
                        park_skipped_character_meets += 1
                        continue

                    if is_non_ride_experience(name):
                        skipped_non_ride_experiences += 1
                        park_skipped_non_rides += 1
                        continue

                    wait_time = ride.get("wait_time")
                    if wait_time is None:
                        continue

                    connection.execute(text("""
                        INSERT INTO wait_times
                        (park, ride_name, land, wait_time, is_open, created_at)
                        VALUES
                        (:park, :ride_name, :land, :wait_time, :is_open, :created_at)
                    """), {
                        "park": park["name"],
                        "ride_name": name,
                        "land": land.get("name"),
                        "wait_time": wait_time,
                        "is_open": ride.get("is_open"),
                        "created_at": datetime.utcnow(),
                    })

                    inserted += 1
                    park_inserted += 1

            park_results.append({
                "park": park["name"],
                "inserted": park_inserted,
                "skipped_character_meets": park_skipped_character_meets,
                "skipped_non_ride_experiences": park_skipped_non_rides,
            })

        connection.commit()

        total = connection.execute(text("""
            SELECT COUNT(*) FROM wait_times
        """)).scalar()

    return {
        "inserted": inserted,
        "skipped_character_meets": skipped_character_meets,
        "skipped_non_ride_experiences": skipped_non_ride_experiences,
        "total_historical_entries": total,
        "parks": park_results,
        "updated_at": datetime.utcnow().isoformat() + "Z",
    }


def get_historical_planning_insights(park):
    current_hour = datetime.utcnow().hour

    with engine.connect() as connection:
        setup_database(connection)

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
        "tomorrow_forecast": get_tomorrow_forecast(engine, park),
    }


@app.route("/")
def home():
    return jsonify({
        "name": "CastleWatch API",
        "status": "online",
        "parks": [park["name"] for park in PARKS],
        "note": "Use /api/refresh-rides to collect current ride waits, /api/rides to read latest data, /api/planning-insights for historical and tomorrow planning analysis, /api/trip-week for the 2027 trip plan, and /api/weather-advisory for official weather alert mode.",
    })


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


@app.route("/api/weather-advisory")
def api_weather_advisory():
    try:
        return jsonify(get_weather_advisory())
    except Exception as error:
        return jsonify({
            "advisoryActive": False,
            "mode": "normal",
            "source": "weather.gov",
            "status": "error",
            "message": str(error),
            "checkedAt": datetime.utcnow().isoformat() + "Z",
        }), 502


@app.route("/api/refresh-rides")
def api_refresh_rides():
    try:
        return jsonify(collect_wait_times())
    except Exception as error:
        return jsonify({
            "status": "error",
            "message": str(error),
        }), 500


@app.route("/api/planning-insights")
def api_planning_insights():
    try:
        park = normalize_park(request.args.get("park", "Magic Kingdom"))
        return jsonify(get_historical_planning_insights(park))
    except Exception as error:
        return jsonify({
            "status": "error",
            "message": str(error),
        }), 500


@app.route("/api/trip-week")
def api_trip_week():
    try:
        return jsonify(get_trip_week_plan(engine))
    except Exception as error:
        return jsonify({
            "status": "error",
            "message": str(error),
        }), 500


@app.route("/api/rides")
def api_rides():
    with engine.connect() as connection:
        setup_database(connection)

        count = connection.execute(text("""
            SELECT COUNT(*) FROM wait_times
            WHERE park IS NOT NULL
        """)).scalar()

        if count == 0:
            collect_wait_times()

        result = connection.execute(text("""
            SELECT DISTINCT ON (park, ride_name)
                park,
                ride_name,
                land,
                wait_time,
                is_open,
                created_at
            FROM wait_times
            WHERE ride_name IS NOT NULL
              AND park IS NOT NULL
              AND park <> ''
            ORDER BY park, ride_name, created_at DESC
        """))

        rides = [
            {
                "park": row.park,
                "name": row.ride_name,
                "land": row.land,
                "wait_time": row.wait_time,
                "is_open": row.is_open,
                "created_at": row.created_at.isoformat() if row.created_at else None,
            }
            for row in result
            if should_include_attraction(row.ride_name)
        ]

    return jsonify(rides)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8080)))
