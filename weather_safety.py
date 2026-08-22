def prioritize_weather_advisory(payload):
    """Prefer shelter-first storm mode when multiple official alerts are active."""
    if not isinstance(payload, dict) or payload.get("advisoryActive") is not True:
        return payload

    alerts = payload.get("alerts") or []
    if not isinstance(alerts, list):
        return payload

    primary = next(
        (alert for alert in alerts if isinstance(alert, dict) and alert.get("mode") == "storm"),
        None,
    )
    if primary is None:
        primary = next(
            (alert for alert in alerts if isinstance(alert, dict) and alert.get("mode") == "hot"),
            None,
        )

    if primary is None:
        return payload

    return {
        **payload,
        "mode": primary.get("mode"),
        "advisoryType": primary.get("event"),
        "headline": primary.get("headline") or primary.get("event"),
        "expiresAt": primary.get("expires"),
        "source": primary.get("source") or payload.get("source"),
    }
