"""CastleWatch API entrypoint with family-mode filters.

The core Flask app now owns all route registration, including private family
trip storage. This wrapper only applies family-mode attraction exclusions before
Gunicorn serves the shared app object.
"""

from app import app, NON_RIDE_EXPERIENCE_KEYWORDS

FAMILY_MODE_EXCLUSIONS = [
    "single rider",
]

for keyword in FAMILY_MODE_EXCLUSIONS:
    if keyword not in NON_RIDE_EXPERIENCE_KEYWORDS:
        NON_RIDE_EXPERIENCE_KEYWORDS.append(keyword)
