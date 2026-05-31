import os
import requests
from datetime import datetime

from flask import Flask, jsonify
from flask_cors import CORS
from sqlalchemy import create_engine, text

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

CHARACTER_MEET_KEYWORDS = [
    "meet",
    "greet",
    "character",
    "princess fairytale hall",
    "adventurers outpost",
    "royal sommerhus",
    "town square theater",
]


def is_character_meet(name):
    if not name:
        return False

    normalized = name.lower()
    return any(keyword in normalized for keyword in CHARACTER_MEET_KEYWORDS)


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
    park_results = []

    with engine.connect() as connection:
        setup_database(connection)

        for park in PARKS:
            url = f"https://queue-times.com/parks/{park['id']}/queue_times.json"
            response = requests.get(url, timeout=20)
            response.raise_for_status()
            data = response.json()

            park_inserted = 0
            park_skipped = 0
            lands = data.get("lands", [])

            for land in lands:
                rides = land.get("rides", [])

                for ride in rides:
                    name = ride.get("name")

                    if is_character_meet(name):
                        skipped_character_meets += 1
                        park_skipped += 1
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
                "skipped_character_meets": park_skipped,
            })

        connection.commit()

        total = connection.execute(text("""
            SELECT COUNT(*) FROM wait_times
        """)).scalar()

    return {
        "inserted": inserted,
        "skipped_character_meets": skipped_character_meets,
        "total_historical_entries": total,
        "parks": park_results,
        "updated_at": datetime.utcnow().isoformat() + "Z",
    }


@app.route("/")
def home():
    return jsonify({
        "name": "CastleWatch API",
        "status": "online",
        "parks": [park["name"] for park in PARKS],
        "note": "Use /api/refresh-rides to collect current ride waits and /api/rides to read the latest data.",
    })


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


@app.route("/api/refresh-rides")
def api_refresh_rides():
    try:
        return jsonify(collect_wait_times())
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
        ]

    return jsonify(rides)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8080)))
