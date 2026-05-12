import os
from datetime import datetime

from flask import Flask
from sqlalchemy import create_engine, text

app = Flask(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)

@app.route("/")
def home():

    try:
        connection = engine.connect()

        # Create table if missing
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS wait_times (
                id SERIAL PRIMARY KEY,
                ride_name TEXT,
                wait_time INTEGER,
                created_at TIMESTAMP
            )
        """))

        # Insert test data
        connection.execute(text("""
            INSERT INTO wait_times
            (ride_name, wait_time, created_at)

            VALUES
            (:ride_name, :wait_time, :created_at)
        """), {
            "ride_name": "Space Mountain",
            "wait_time": 55,
            "created_at": datetime.utcnow()
        })

        connection.commit()

        # Count rows
        result = connection.execute(text("""
            SELECT COUNT(*) FROM wait_times
        """))

        count = result.scalar()

        connection.close()

        return f"CastleWatch Database Entries: {count}"

    except Exception as e:

        return f"Database Error: {str(e)}"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
