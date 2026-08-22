"""CastleWatch Railway API entrypoint with family-mode filters.

The shared Flask app in app.py owns route registration and production request
guards. This Railway entrypoint only applies family-mode attraction exclusions
before Gunicorn serves the app object.
"""

from app import app, NON_RIDE_EXPERIENCE_KEYWORDS

FAMILY_MODE_EXCLUSIONS = [
    "single rider",
]

for keyword in FAMILY_MODE_EXCLUSIONS:
    if keyword not in NON_RIDE_EXPERIENCE_KEYWORDS:
        NON_RIDE_EXPERIENCE_KEYWORDS.append(keyword)
