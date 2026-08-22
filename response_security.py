GENERIC_SERVER_ERROR_MESSAGE = "CastleWatch could not complete the request."


def sanitize_server_error_payload(payload, status_code):
    """Replace internal 5xx error details before JSON leaves the backend.

    Route handlers may still keep stable status/source fields for client behavior,
    but exception text should never be returned to browsers.
    """
    if status_code < 500 or not isinstance(payload, dict):
        return payload

    sanitized = dict(payload)
    if "message" in sanitized:
        sanitized["message"] = GENERIC_SERVER_ERROR_MESSAGE
    return sanitized
