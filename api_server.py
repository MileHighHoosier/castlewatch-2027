"""CastleWatch API entrypoint with family-mode filters and production guards.

The core Flask app owns route registration, including private family-trip
storage. This Railway entrypoint applies family-mode attraction exclusions and
wraps the expensive ride-refresh route with a persisted cooldown + PostgreSQL
advisory lock so repeated requests cannot trigger duplicate collection work.
"""

from flask import jsonify

from app import app, NON_RIDE_EXPERIENCE_KEYWORDS, collect_wait_times, engine
from ride_refresh_guard import guarded_collect_wait_times

FAMILY_MODE_EXCLUSIONS = [
    "single rider",
]

for keyword in FAMILY_MODE_EXCLUSIONS:
    if keyword not in NON_RIDE_EXPERIENCE_KEYWORDS:
        NON_RIDE_EXPERIENCE_KEYWORDS.append(keyword)


def guarded_api_refresh_rides():
    try:
        return jsonify(guarded_collect_wait_times(engine, collect_wait_times))
    except Exception:
        app.logger.exception("CastleWatch ride refresh failed")
        return jsonify({
            "status": "error",
            "message": "CastleWatch could not refresh ride data.",
        }), 500


# Preserve the existing URL/HTTP contract while replacing the unbounded write
# behavior for the Railway production entrypoint.
app.view_functions["api_refresh_rides"] = guarded_api_refresh_rides
