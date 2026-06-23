from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date

from flask import has_request_context, request

from calendar_ingestion import refresh_calendar_ingestion
from special_events import get_special_event_intelligence
from tomorrow_forecast import get_date_forecast

TRIP_START = date(2027, 10, 9)
TRIP_END = date(2027, 10, 16)

BASE_DAYS = [
    {
        "date": "2027-10-09",
        "type": "arrival",
        "title": "Arrival day",
        "subtitle": "Check in and keep the evening flexible.",
    },
    {
        "date": "2027-10-10",
        "type": "park",
        "park": "Magic Kingdom",
        "title": "Magic Kingdom",
        "subtitle": "BBB + Cinderella's Royal Table day. Provisional until 2027 MNSSHP dates are released.",
        "mnsshp_status": "schedule_unreleased",
        "mnsshp_label": "Potential party night — provisional",
    },
    {
        "date": "2027-10-11",
        "type": "park",
        "park": "Hollywood Studios",
        "title": "Hollywood Studios",
        "subtitle": "Columbus Day park day. Keep the rope-drop plan aggressive.",
        "holiday": "Columbus Day",
    },
    {
        "date": "2027-10-12",
        "type": "rest",
        "title": "Beach Club rest day",
        "subtitle": "Pool and resort reset day with 1900 Park Fare later.",
    },
    {
        "date": "2027-10-13",
        "type": "park",
        "park": "Epcot",
        "title": "Epcot",
        "subtitle": "Convenient after the Beach Club night and still provisional as the Magic Kingdom swap partner.",
    },
    {
        "date": "2027-10-14",
        "type": "park",
        "park": "Animal Kingdom",
        "title": "Animal Kingdom",
        "subtitle": "Single full park day with an early arrival focus.",
    },
    {
        "date": "2027-10-15",
        "type": "flex",
        "title": "AKL / private-tour flex day",
        "subtitle": "Animal Kingdom Lodge resort day unless the private tour is scheduled here.",
    },
    {
        "date": "2027-10-16",
        "type": "departure",
        "title": "Departure day",
        "subtitle": "No park planned.",
    },
]

ALTERNATE_SWAP = {
    "condition": "Use this only if Sunday, Oct. 10 is confirmed as an MNSSHP night and Wednesday, Oct. 13 is confirmed as a normal Magic Kingdom night.",
    "reason": "This preserves a full regular Magic Kingdom day without adding a park hopper or a repeat visit.",
    "days": [
        {
            "date": "2027-10-10",
            "park": "Epcot",
            "title": "Epcot",
        },
        {
            "date": "2027-10-13",
            "park": "Magic Kingdom",
            "title": "Magic Kingdom",
        },
    ],
}


def _unavailable_forecast(target_date, error):
    return {
        "date": target_date,
        "status": "unavailable",
        "source": "error",
        "summary": "Historical forecast is temporarily unavailable.",
        "confidence": {"level": "low", "label": "Unavailable"},
        "best_window": None,
        "peak_window": None,
        "message": str(error),
    }


def _forecast_requests():
    requests = []
    for day in BASE_DAYS:
        if day.get("type") == "park" and day.get("park"):
            requests.append((day["park"], day["date"]))
    for day in ALTERNATE_SWAP["days"]:
        requests.append((day["park"], day["date"]))
    return list(dict.fromkeys(requests))


def _load_forecasts(engine):
    forecasts = {}
    requests = _forecast_requests()

    with ThreadPoolExecutor(max_workers=4) as executor:
        future_map = {
            executor.submit(get_date_forecast, engine, park, target_date): (park, target_date)
            for park, target_date in requests
        }
        for future in as_completed(future_map):
            park, target_date = future_map[future]
            try:
                forecasts[(park, target_date)] = future.result()
            except Exception as error:
                forecasts[(park, target_date)] = _unavailable_forecast(target_date, error)

    return forecasts


def _signal_map(intelligence):
    return {
        item["date"]: item.get("signals", [])
        for item in intelligence.get("day_signals", [])
    }


def _attach_forecasts_and_events(days, forecasts, signals):
    enriched = []
    for day in days:
        item = dict(day)
        if item.get("type") == "park" and item.get("park"):
            item["forecast"] = forecasts.get(
                (item["park"], item["date"]),
                _unavailable_forecast(item["date"], "Forecast was not returned."),
            )
        item["special_event_signals"] = signals.get(item["date"], [])
        enriched.append(item)
    return enriched


def _alternate_signals(day, signals):
    day_signals = [dict(signal) for signal in signals.get(day["date"], [])]

    if day["date"] == "2027-10-10" and day.get("park") == "Epcot":
        for signal in day_signals:
            if signal.get("id") != "mnsshp":
                continue

            if signal.get("status") == "confirmed_event":
                signal["label"] = "Sunday Magic Kingdom is a confirmed MNSSHP night"
                signal["summary"] = "The alternate uses Epcot because regular Magic Kingdom day-guest hours would end early."
            elif signal.get("status") == "confirmed_clear":
                signal["label"] = "Sunday Magic Kingdom is clear"
                signal["summary"] = "The loaded party calendar does not require using Epcot as an event-driven alternate."
            else:
                signal["label"] = "Sunday Magic Kingdom party status unknown"
                signal["summary"] = "The alternate uses Epcot because Sunday may become an MNSSHP night at Magic Kingdom."

    return day_signals


def _force_calendar_refresh_requested():
    if not has_request_context():
        return False
    return request.args.get("refresh_calendar", "").strip().lower() in {"1", "true", "yes"}


def get_trip_week_plan(engine):
    forecasts = _load_forecasts(engine)
    force_calendar_refresh = _force_calendar_refresh_requested()
    if force_calendar_refresh:
        refresh_calendar_ingestion(engine, force=True)
    intelligence = get_special_event_intelligence(
        engine,
        refresh_if_stale=not force_calendar_refresh,
    )
    signals = _signal_map(intelligence)

    alternate_days = []
    for day in ALTERNATE_SWAP["days"]:
        item = dict(day)
        item["forecast"] = forecasts.get(
            (item["park"], item["date"]),
            _unavailable_forecast(item["date"], "Forecast was not returned."),
        )
        item["special_event_signals"] = _alternate_signals(item, signals)
        alternate_days.append(item)

    return {
        "trip_name": "Columbus Day Week 2027",
        "start_date": TRIP_START.isoformat(),
        "end_date": TRIP_END.isoformat(),
        "status": "provisional",
        "party_schedule_status": intelligence["sources"][0]["note"],
        "constraints": [
            "One park per day",
            "No park hopping",
            "Each park visited once",
            "Beach Club rest day stays fixed",
            "AKL / private-tour flex day stays fixed",
        ],
        "days": _attach_forecasts_and_events(BASE_DAYS, forecasts, signals),
        "alternate_swap": {
            **ALTERNATE_SWAP,
            "days": alternate_days,
        },
        "special_event_intelligence": intelligence,
    }
