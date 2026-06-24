"""CastleWatch API entrypoint with family-mode filters and private trip storage.

This wrapper imports the existing Flask API from app.py, then extends its
ride-demand filter before Gunicorn serves the app. It keeps the working API
implementation intact while filtering items that are poor defaults for a
family of four, such as single rider listings, and registers the protected
shared-family-trip endpoints.
"""

from app import app, engine, NON_RIDE_EXPERIENCE_KEYWORDS
from family_trip import get_family_trip, put_family_trip

FAMILY_MODE_EXCLUSIONS = [
    "single rider",
]

for keyword in FAMILY_MODE_EXCLUSIONS:
    if keyword not in NON_RIDE_EXPERIENCE_KEYWORDS:
        NON_RIDE_EXPERIENCE_KEYWORDS.append(keyword)


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
