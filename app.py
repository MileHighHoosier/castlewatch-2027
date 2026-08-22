"""CastleWatch core Flask entrypoint.

The original application implementation lives in core_app.py. This wrapper keeps
all existing routes and helpers available while ensuring private family-trip
storage is registered even when Railway launches `gunicorn app:app` instead of
the repository's api_server entrypoint.
"""

from core_app import *  # noqa: F401,F403
from accounts_routes import (
    accept_family_invite,
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
from operations import get_family_trip_operations
from response_security import GENERIC_SERVER_ERROR_MESSAGE, sanitize_server_error_payload


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
        return accept_family_invite(engine)
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
