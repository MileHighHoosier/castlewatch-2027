from datetime import datetime

import requests
from sqlalchemy import text


def collect_wait_times_without_schema(
    engine,
    parks,
    is_character_meet,
    is_non_ride_experience,
    request_get=requests.get,
):
    """Collect Queue Times data without running schema DDL inside a live request.

    Schema creation/migration is handled during application startup. Keeping DDL
    out of refresh requests avoids ACCESS EXCLUSIVE table locks that can block
    concurrent dashboard history reads.
    """
    inserted = 0
    skipped_character_meets = 0
    skipped_non_ride_experiences = 0
    park_results = []

    with engine.connect() as connection:
        for park in parks:
            url = f"https://queue-times.com/parks/{park['id']}/queue_times.json"
            response = request_get(url, timeout=20)
            response.raise_for_status()
            data = response.json()

            park_inserted = 0
            park_skipped_character_meets = 0
            park_skipped_non_rides = 0

            for land in data.get("lands", []):
                for ride in land.get("rides", []):
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
        total = connection.execute(text("SELECT COUNT(*) FROM wait_times")).scalar()

    return {
        "inserted": inserted,
        "skipped_character_meets": skipped_character_meets,
        "skipped_non_ride_experiences": skipped_non_ride_experiences,
        "total_historical_entries": total,
        "parks": park_results,
        "updated_at": datetime.utcnow().isoformat() + "Z",
    }
