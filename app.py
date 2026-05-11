import os

from flask import Flask
from sqlalchemy import create_engine

app = Flask(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)

@app.route("/")
def home():
    try:
        connection = engine.connect()
        connection.close()

        return "CastleWatch Backend + Database Online"

    except Exception as e:
        return f"Database Error: {str(e)}"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
