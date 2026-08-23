"""CastleWatch core Flask entrypoint.

The original application implementation lives in core_app.py. This wrapper keeps
all existing routes and helpers available while ensuring private family-trip
storage and production request guards are registered even when Railway launches
`gunicorn app:app` instead of the repository's api_server entrypoint.
"""

from flask import jsonify
from sqlalchemy import text

from core_app import *  # noqa: F401,F403
from accounts_routes import (
    check_family_device_access,
    create_family_invite,
    list_family_devices,
    rename_family_device,
    revoke_family_device,
)
from family_trip import (
    get_family_trip,
    get_family_trip_history,
    get_family_trip_history_version,
    put_family_trip,
    restore_family_trip_version,
)
from invite_acceptance import accept_family_invite_atomic
from live_planning_insights import get_live_planning_insights
from operations import get_family_trip_operations
from response_security import GENERIC_SERVER_ERROR_MESSAGE, sanitize_server_error_payload
from ride_collection import collect_wait_times_without_schema
from ride_read import get_latest_rides
from ride_refresh_guard import guarded_collect_wait_times
from weather_safety import prioritize_weather_advisory

SCHEMA_BOOTSTRAP_LOCK_ID = 20271010


def bootstrap_wait_times_schema():
    """Ensure the wait-times schema before serving traffic, not during refreshes."""
    with engine.begin() as connection:
        connection.execute(
            text("SELECT pg_advisory_xact_lock(:lock_id)"),
            {"lock_id": SCHEMA_BOOTSTRAP_LOCK_ID},
        )
        setup_database(connection)


bootstrap_wait_times_schema()


@app.after_request
def sanitize_internal_server_errors(response):
    """Prevent caught exception text from leaking through production JSON."""
    if response.status_code < 500 or not response.is_json:
        return response

    payload = response.get_json(silent=True)
    sanitized = sanitize_server_error_payload(payload, response.status_code)
    if sanitized != payload:
        response.set_data(app.json.dumps(sanitized))
        response.headers["Content-Type"] = "application/json"
        response.headers["Cache-Control"] = "no-store, max-age=0"
    return response


def _internal_error(context, error):
    app.logger.error(
        "CastleWatch backend failure: %s",
        context,
        exc_info=(type(error), error, error.__traceback__),
    )
    return {
        "status": "error",
        "message": GENERIC_SERVER_ERROR_MESSAGE,
    }, 500


def _collect_wait_times_request_safe():
    return collect_wait_times_without_schema(
        engine,
        PARKS,
        is_character_meet,
        is_non_ride_experience,
    )


def guarded_api_refresh_rides():
    """Keep the public refresh URL while bounding expensive collection writes."""
    try:
        return jsonify(guarded_collect_wait_times(engine, _collect_wait_times_request_safe))
    except Exception as error:
        return _internal_error("ride refresh", error)


def resilient_api_rides():
    """Serve ride reads without schema changes or surprise collection work."""
    try:
        return jsonify(get_latest_rides(engine, should_include_attraction))
    except Exception as error:
        return _internal_error("ride data read", error)


def resilient_api_planning_insights():
    """Keep live historical insights independent from heavier forecast work."""
    try:
        park = normalize_park(request.args.get("park", "Magic Kingdom"))
        return jsonify(get_live_planning_insights(engine, park, should_include_attraction))
    except Exception as error:
        return _internal_error("live planning insights", error)


def resilient_api_weather_advisory():
    """Return official alerts with shelter-first severe-weather prioritization."""
    try:
        return jsonify(prioritize_weather_advisory(get_weather_advisory()))
    except Exception as error:
        app.logger.error(
            "CastleWatch backend failure: weather advisory",
            exc_info=(type(error), error, error.__traceback__),
        )
        return jsonify({
            "advisoryActive": None,
            "mode": None,
            "source": "weather.gov",
            "status": "unknown",
            "message": GENERIC_SERVER_ERROR_MESSAGE,
            "checkedAt": datetime.utcnow().isoformat() + "Z",
        }), 502


# Install production guards at the shared Flask-app layer so both `app:app` and
# `api_server:app` deployment entrypoints use the same protected endpoints.
app.view_functions["api_refresh_rides"] = guarded_api_refresh_rides
app.view_functions["api_rides"] = resilient_api_rides
app.view_functions["api_planning_insights"] = resilient_api_planning_insights
app.view_functions["api_weather_advisory"] = resilient_api_weather_advisory


@app.route("/api/family-trip", methods=["GET"])
def api_get_family_trip():
    try:
        return get_family_trip(engine)
    except Exception as error:
        return _internal_error("family trip read", error)


@app.route("/api/family-trip", methods=["PUT"])
def api_put_family_trip():
    try:
        return put_family_trip(engine)
    except Exception as error:
        return _internal_error("family trip write", error)


@app.route("/api/family-trip/history", methods=["GET"])
def api_get_family_trip_history():
    try:
        return get_family_trip_history(engine)
    except Exception as error:
        return _internal_error("family trip history read", error)


@app.route("/api/family-trip/history/<int:version>", methods=["GET"])
def api_get_family_trip_history_version(version):
    try:
        return get_family_trip_history_version(engine, version)
    except Exception as error:
        return _internal_error("family trip history version read", error)


@app.route("/api/family-trip/restore", methods=["POST"])
def api_restore_family_trip_version():
    try:
        return restore_family_trip_version(engine)
    except Exception as error:
        return _internal_error("family trip restore", error)


@app.route("/api/family-trip/operations", methods=["GET"])
def api_get_family_trip_operations():
    try:
        return get_family_trip_operations(engine)
    except Exception as error:
        return _internal_error("family trip operations read", error)


@app.route("/api/family-trip/devices/access", methods=["GET"])
def api_check_family_device_access():
    try:
        return check_family_device_access(engine)
    except Exception as error:
        return _internal_error("family device access check", error)


@app.route("/api/family-trip/devices", methods=["GET"])
def api_list_family_devices():
    try:
        return list_family_devices(engine)
    except Exception as error:
        return _internal_error("family device list", error)


@app.route("/api/family-trip/invites", methods=["POST"])
def api_create_family_invite():
    try:
        return create_family_invite(engine)
    except Exception as error:
        return _internal_error("family invite creation", error)


@app.route("/api/family-trip/devices/accept-invite", methods=["POST"])
def api_accept_family_invite():
    try:
        return accept_family_invite_atomic(engine)
    except Exception as error:
        return _internal_error("family invite acceptance", error)


@app.route("/api/family-trip/devices/rename", methods=["POST"])
def api_rename_family_device():
    try:
        return rename_family_device(engine)
    except Exception as error:
        return _internal_error("family device rename", error)


@app.route("/api/family-trip/devices/revoke", methods=["POST"])
def api_revoke_family_device():
    try:
        return revoke_family_device(engine)
    except Exception as error:
        return _internal_error("family device revoke", error)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8080)))
