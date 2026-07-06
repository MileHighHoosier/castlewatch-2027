"""CastleWatch core Flask entrypoint.

The original application implementation lives in core_app.py. This wrapper keeps
all existing routes and helpers available while ensuring private family-trip
storage is registered even when Railway launches `gunicorn app:app` instead of
the repository's api_server entrypoint.
"""

from core_app import *  # noqa: F401,F403
from family_trip import (
    get_family_trip,
    get_family_trip_history,
    get_family_trip_history_version,
    put_family_trip,
    restore_family_trip_version,
)
from operations import get_family_trip_operations


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


@app.route("/api/family-trip/history", methods=["GET"])
def api_get_family_trip_history():
    try:
        return get_family_trip_history(engine)
    except Exception as error:
        return {
            "status": "error",
            "message": str(error),
        }, 500


@app.route("/api/family-trip/history/<int:version>", methods=["GET"])
def api_get_family_trip_history_version(version):
    try:
        return get_family_trip_history_version(engine, version)
    except Exception as error:
        return {
            "status": "error",
            "message": str(error),
        }, 500


@app.route("/api/family-trip/restore", methods=["POST"])
def api_restore_family_trip_version():
    try:
        return restore_family_trip_version(engine)
    except Exception as error:
        return {
            "status": "error",
            "message": str(error),
        }, 500


@app.route("/api/family-trip/operations", methods=["GET"])
def api_get_family_trip_operations():
    try:
        return get_family_trip_operations(engine)
    except Exception as error:
        return {
            "status": "error",
            "message": str(error),
        }, 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8080)))
