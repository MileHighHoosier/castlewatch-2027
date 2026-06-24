"""CastleWatch core Flask entrypoint.

The original application implementation lives in core_app.py. This wrapper keeps
all existing routes and helpers available while ensuring private family-trip
storage is registered even when Railway launches `gunicorn app:app` instead of
the repository's api_server entrypoint.
"""

from core_app import *  # noqa: F401,F403
from family_trip import get_family_trip, put_family_trip


@app.route("/api/family-trip", methods=["GET"])
def api_get_family_trip():
    try:
        return get_family_trip(engine)
    except Exception as error:
        return {
            "status": "error",
            "message": str(error),
        }, 500


@app.route("/api/family-trip", methods=["PUT"])
def api_put_family_trip():
    try:
        return put_family_trip(engine)
    except Exception as error:
        return {
            "status": "error",
            "message": str(error),
        }, 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8080)))
