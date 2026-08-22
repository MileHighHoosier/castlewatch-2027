from sqlalchemy import text


def get_latest_rides(engine, should_include_attraction):
    """Read latest ride rows without schema changes or collection work.

    This path is used by the live Park Command Center and must remain responsive
    while a background collector is inserting new observations.
    """
    with engine.connect() as connection:
        table_exists = connection.execute(
            text("SELECT to_regclass('public.wait_times')")
        ).scalar()
        if not table_exists:
            return []

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

        return [
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
