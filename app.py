import os
import requests
from datetime import datetime

from flask import Flask
from sqlalchemy import create_engine, text
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)

WAIT_API = "https://queue-times.com/parks/6/queue_times.json"

@app.route("/")
def home():

    try:

        response = requests.get(WAIT_API)

        data = response.json()

        lands = data.get("lands", [])

        connection = engine.connect()

        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS wait_times (
                id SERIAL PRIMARY KEY,
                ride_name TEXT,
                land TEXT,
                wait_time INTEGER,
                created_at TIMESTAMP
            )
        """))

        inserted = 0

        for land in lands:

            rides = land.get("rides", [])

            for ride in rides:

                name = ride.get("name")

                wait_time = ride.get("wait_time")

                if wait_time is None:
                    continue

                connection.execute(text("""
                    INSERT INTO wait_times
                    (ride_name, wait_time, created_at)

                    VALUES
                    (:ride_name, :wait_time, :created_at)
                """), {
                    "ride_name": name,
                    "wait_time": wait_time,
                    "created_at": datetime.utcnow()
                })

                inserted += 1

        connection.commit()

        result = connection.execute(text("""
            SELECT COUNT(*) FROM wait_times
        """))

        total = result.scalar()

        connection.close()

        return (
            f"Inserted {inserted} rides. "
            f"Total historical entries: {total}"
        )

    except Exception as e:

        return f"System Error: {str(e)}"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

@app.route("/health")
def health():
    return {"status": "ok"}

@app.route("/api/rides")
def api_rides():

    with engine.connect() as connection:

        result = connection.execute(text("""
            SELECT DISTINCT ON (ride_name)
                ride_name,
                wait_time,
                created_at
            FROM wait_times
            ORDER BY ride_name, created_at DESC
        """))

        rides = [
            {
                "name": row.ride_name,
                "wait_time": row.wait_time,
                "created_at": str(row.created_at)
            }
            for row in result
        ]

    return rides
