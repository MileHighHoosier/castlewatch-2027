from weather_safety import prioritize_weather_advisory


def test_storm_mode_outranks_heat_when_both_are_active():
    payload = {
        "advisoryActive": True,
        "mode": "hot",
        "advisoryType": "Heat Advisory",
        "headline": "Heat Advisory",
        "expiresAt": "2026-08-22T23:00:00Z",
        "source": "weather.gov",
        "alerts": [
            {
                "mode": "hot",
                "event": "Heat Advisory",
                "headline": "Heat Advisory",
                "expires": "2026-08-22T23:00:00Z",
                "source": "weather.gov",
            },
            {
                "mode": "storm",
                "event": "Tornado Warning",
                "headline": "Tornado Warning for Orange County",
                "expires": "2026-08-22T19:00:00Z",
                "source": "weather.gov",
            },
        ],
    }

    result = prioritize_weather_advisory(payload)

    assert result["mode"] == "storm"
    assert result["advisoryType"] == "Tornado Warning"
    assert result["headline"] == "Tornado Warning for Orange County"
    assert result["expiresAt"] == "2026-08-22T19:00:00Z"


def test_heat_remains_primary_when_no_storm_alert_exists():
    payload = {
        "advisoryActive": True,
        "mode": "hot",
        "alerts": [
            {
                "mode": "hot",
                "event": "Excessive Heat Warning",
                "headline": "Excessive Heat Warning",
                "expires": "2026-08-22T23:00:00Z",
                "source": "weather.gov",
            }
        ],
    }

    result = prioritize_weather_advisory(payload)

    assert result["mode"] == "hot"
    assert result["advisoryType"] == "Excessive Heat Warning"


def test_inactive_weather_payload_is_left_unchanged():
    payload = {
        "advisoryActive": False,
        "mode": "normal",
        "source": "weather.gov",
    }

    assert prioritize_weather_advisory(payload) is payload


def test_unknown_alert_entries_do_not_replace_existing_primary_state():
    payload = {
        "advisoryActive": True,
        "mode": "hot",
        "headline": "Heat Advisory",
        "alerts": [{"mode": "other", "event": "Air Quality Alert"}],
    }

    assert prioritize_weather_advisory(payload) is payload
