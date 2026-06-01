"""CastleWatch API entrypoint with family-mode filters.

This wrapper imports the existing Flask API from app.py, then extends its
ride-demand filter before Gunicorn serves the app. It keeps the working API
implementation intact while filtering items that are poor defaults for a
family of four, such as single rider listings.
"""

from app import app, NON_RIDE_EXPERIENCE_KEYWORDS

FAMILY_MODE_EXCLUSIONS = [
    "single rider",
]

for keyword in FAMILY_MODE_EXCLUSIONS:
    if keyword not in NON_RIDE_EXPERIENCE_KEYWORDS:
        NON_RIDE_EXPERIENCE_KEYWORDS.append(keyword)
