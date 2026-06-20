from datetime import date

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


def _safe_forecast(engine, park, target_date):
    try:
        return get_date_forecast(engine, park, target_date)
    except Exception as error:
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


def _attach_forecasts(engine, days):
    enriched = []
    for day in days:
        item = dict(day)
        if item.get("type") == "park" and item.get("park"):
            item["forecast"] = _safe_forecast(engine, item["park"], item["date"])
        enriched.append(item)
    return enriched


def get_trip_week_plan(engine):
    alternate_days = []
    for day in ALTERNATE_SWAP["days"]:
        item = dict(day)
        item["forecast"] = _safe_forecast(engine, item["park"], item["date"])
        alternate_days.append(item)

    return {
        "trip_name": "Columbus Day Week 2027",
        "start_date": TRIP_START.isoformat(),
        "end_date": TRIP_END.isoformat(),
        "status": "provisional",
        "party_schedule_status": "2027 MNSSHP dates not yet loaded",
        "constraints": [
            "One park per day",
            "No park hopping",
            "Each park visited once",
            "Beach Club rest day stays fixed",
            "AKL / private-tour flex day stays fixed",
        ],
        "days": _attach_forecasts(engine, BASE_DAYS),
        "alternate_swap": {
            **ALTERNATE_SWAP,
            "days": alternate_days,
        },
    }
