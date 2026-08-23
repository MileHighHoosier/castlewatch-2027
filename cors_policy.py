"""CastleWatch browser-origin policy.

The legacy application initializes Flask-CORS globally in core_app.py. Until that
large legacy module is split up, this module applies a final response guard that
removes wildcard/reflected CORS headers for unapproved browser origins and
normalizes headers for CastleWatch's approved Vercel origins.
"""

import os
import re

from flask import request

PRODUCTION_ORIGINS = (
    "https://castlewatch-frontend.vercel.app",
    "https://castlewatch-frontend-castlewatch.vercel.app",
)

# Vercel preview aliases observed for the CastleWatch team/project follow this
# project + branch/deployment + team pattern. Keep it scoped to this project and
# team instead of allowing arbitrary *.vercel.app origins.
PREVIEW_ORIGIN_PATTERN = re.compile(
    r"^https://castlewatch-frontend-(?:git-[a-z0-9-]+|[a-z0-9]+)-castlewatch\.vercel\.app$"
)

CORS_RESPONSE_HEADERS = (
    "Access-Control-Allow-Origin",
    "Access-Control-Allow-Credentials",
    "Access-Control-Allow-Headers",
    "Access-Control-Allow-Methods",
    "Access-Control-Expose-Headers",
    "Access-Control-Max-Age",
)

ALLOWED_METHODS = "GET, POST, PUT, OPTIONS"
ALLOWED_HEADERS = (
    "Accept, Content-Type, X-CastleWatch-Family-Key, "
    "X-CastleWatch-Device-Token"
)


def configured_extra_origins():
    """Return exact additional origins from CASTLEWATCH_ALLOWED_ORIGINS."""
    raw = os.getenv("CASTLEWATCH_ALLOWED_ORIGINS", "")
    return tuple(
        value.strip().rstrip("/")
        for value in raw.split(",")
        if value.strip()
    )


def origin_is_allowed(origin):
    if not isinstance(origin, str):
        return False
    normalized = origin.strip().rstrip("/")
    if not normalized:
        return False
    if normalized in PRODUCTION_ORIGINS:
        return True
    if normalized in configured_extra_origins():
        return True
    return PREVIEW_ORIGIN_PATTERN.fullmatch(normalized) is not None


def _append_vary_origin(response):
    existing = response.headers.get("Vary", "")
    values = [value.strip() for value in existing.split(",") if value.strip()]
    if not any(value.lower() == "origin" for value in values):
        values.append("Origin")
    if values:
        response.headers["Vary"] = ", ".join(values)


def enforce_castlewatch_cors(response):
    """Apply the final browser-visible CORS policy to a Flask response."""
    origin = request.headers.get("Origin")

    for header in CORS_RESPONSE_HEADERS:
        response.headers.pop(header, None)

    if not origin or not origin_is_allowed(origin):
        return response

    normalized = origin.strip().rstrip("/")
    response.headers["Access-Control-Allow-Origin"] = normalized
    response.headers["Access-Control-Allow-Methods"] = ALLOWED_METHODS
    response.headers["Access-Control-Allow-Headers"] = ALLOWED_HEADERS
    response.headers["Access-Control-Max-Age"] = "600"
    _append_vary_origin(response)
    return response


def install_cors_enforcement(app):
    """Install the guard so it runs after legacy Flask-CORS processing.

    Flask executes app-level after_request handlers in reverse registration
    order. Inserting this guard at index zero makes it the final response step,
    after the legacy Flask-CORS callback imported from core_app.py.
    """
    functions = app.after_request_funcs.setdefault(None, [])
    if enforce_castlewatch_cors not in functions:
        functions.insert(0, enforce_castlewatch_cors)
