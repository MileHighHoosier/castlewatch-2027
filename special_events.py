import os
from datetime import datetime, timezone

TRIP_DATES = [
    "2027-10-09",
    "2027-10-10",
    "2027-10-11",
    "2027-10-12",
    "2027-10-13",
    "2027-10-14",
    "2027-10-15",
    "2027-10-16",
]

BASE_ASSIGNMENTS = {
    "2027-10-10": "Magic Kingdom",
    "2027-10-11": "Hollywood Studios",
    "2027-10-13": "Epcot",
    "2027-10-14": "Animal Kingdom",
}

ALTERNATE_ASSIGNMENTS = {
    "2027-10-10": "Epcot",
    "2027-10-11": "Hollywood Studios",
    "2027-10-13": "Magic Kingdom",
    "2027-10-14": "Animal Kingdom",
}


def _configured_party_dates():
    raw = os.getenv("MNSSHP_2027_DATES", "")
    return sorted({value.strip() for value in raw.split(",") if value.strip()})


def _schedule_status(party_dates):
    configured = os.getenv("MNSSHP_2027_SCHEDULE_STATUS", "").strip().lower()
    if configured in {"unreleased", "partial", "official"}:
        return configured
    return "official" if party_dates else "unreleased"


def _park_hours_status():
    configured = os.getenv("WDW_2027_PARK_HOURS_STATUS", "").strip().lower()
    if configured in {"unreleased", "partial", "official"}:
        return configured
    return "unreleased"


def _party_signal(target_date, party_dates, schedule_status):
    if target_date not in {"2027-10-10", "2027-10-13"}:
        return None

    is_swap_date = target_date == "2027-10-13"

    if schedule_status == "official":
        if target_date in party_dates:
            return {
                "id": "mnsshp",
                "status": "confirmed_event",
                "severity": "high",
                "label": (
                    "Magic Kingdom swap date is a confirmed MNSSHP night"
                    if is_swap_date
                    else "Confirmed MNSSHP night"
                ),
                "summary": (
                    "Do not move Magic Kingdom to Wednesday; regular day-guest hours would end early."
                    if is_swap_date
                    else "Regular Magic Kingdom hours are expected to end early for day guests."
                ),
            }
        return {
            "id": "mnsshp",
            "status": "confirmed_clear",
            "severity": "low",
            "label": (
                "Magic Kingdom swap date is clear"
                if is_swap_date
                else "No MNSSHP loaded for this date"
            ),
            "summary": (
                "Wednesday is clear in the loaded official party schedule and can serve as the Magic Kingdom swap date."
                if is_swap_date
                else "This date is clear in the loaded official party schedule."
            ),
        }

    if is_swap_date:
        return {
            "id": "mnsshp",
            "status": "swap_date_unknown",
            "severity": "medium",
            "label": "Magic Kingdom swap-date status unknown",
            "summary": "Confirm Wednesday is not an MNSSHP night before moving Magic Kingdom here.",
        }

    return {
        "id": "mnsshp",
        "status": "possible_event",
        "severity": "high",
        "label": "Possible MNSSHP night — schedule unreleased",
        "summary": "Do not lock the Magic Kingdom assignment until Disney publishes the 2027 party calendar.",
    }


def _day_signals(party_dates, schedule_status, hours_status):
    signals = {target_date: [] for target_date in TRIP_DATES}

    for target_date in TRIP_DATES:
        party = _party_signal(target_date, party_dates, schedule_status)
        if party:
            signals[target_date].append(party)

    signals["2027-10-11"].append({
        "id": "columbus_day",
        "status": "confirmed_holiday",
        "severity": "high",
        "label": "Columbus Day",
        "summary": "Expect holiday-weekend attendance pressure even when historical ride samples look quieter.",
    })

    for target_date in ["2027-10-10", "2027-10-11", "2027-10-13", "2027-10-14"]:
        signals[target_date].append({
            "id": "park_hours",
            "status": "official" if hours_status == "official" else "unreleased",
            "severity": "medium" if hours_status != "official" else "low",
            "label": "Official park hours loaded" if hours_status == "official" else "2027 park hours not loaded",
            "summary": "Early Entry, regular closing time and Extended Evening Hours remain provisional." if hours_status != "official" else "Use the loaded operating hours for final arrival and evening planning.",
        })

    signals["2027-10-13"].append({
        "id": "extended_evening_hours",
        "status": "unreleased" if hours_status != "official" else "check_eligibility",
        "severity": "medium",
        "label": "Extended Evening Hours not confirmed",
        "summary": "Eligibility depends on the final resort and Disney's 2027 operating calendar.",
    })

    return signals


def _scenario(name, assignments, party_dates, schedule_status, hours_status):
    risk_score = 0
    reasons = []

    magic_kingdom_date = next(
        (target_date for target_date, park in assignments.items() if park == "Magic Kingdom"),
        None,
    )

    if magic_kingdom_date:
        if schedule_status == "official" and magic_kingdom_date in party_dates:
            risk_score += 5
            reasons.append(f"Magic Kingdom falls on a confirmed party night: {magic_kingdom_date}.")
        elif schedule_status != "official" and magic_kingdom_date in {"2027-10-10", "2027-10-13"}:
            risk_score += 3
            reasons.append(f"Magic Kingdom remains exposed to an unreleased party schedule on {magic_kingdom_date}.")

    if assignments.get("2027-10-11"):
        risk_score += 2
        reasons.append("Hollywood Studios remains on Columbus Day, so rope-drop planning should stay aggressive.")

    if hours_status != "official":
        risk_score += 1
        reasons.append("Official 2027 park hours are not loaded yet.")

    return {
        "id": name,
        "label": "Base plan" if name == "base" else "MNSSHP alternate",
        "assignments": assignments,
        "event_risk_score": risk_score,
        "reasons": reasons,
        "lock_status": "provisional" if schedule_status != "official" or hours_status != "official" else "review",
    }


def _recommendation(base, alternate, party_dates, schedule_status):
    sunday_party = "2027-10-10" in party_dates
    wednesday_party = "2027-10-13" in party_dates

    if schedule_status != "official":
        return {
            "status": "wait_for_calendar",
            "preferred_scenario": "base",
            "headline": "Keep the base plan provisional",
            "summary": "The 2027 MNSSHP schedule is not official. Do not move Magic Kingdom until the party dates are loaded.",
            "decision_rule": "Use the alternate only when Sunday is a confirmed party night and Wednesday is confirmed clear.",
        }

    if sunday_party and not wednesday_party:
        return {
            "status": "recommend_swap",
            "preferred_scenario": "alternate",
            "headline": "Use the MNSSHP alternate",
            "summary": "Sunday is a confirmed party night and Wednesday is clear, so the swap preserves a fuller regular Magic Kingdom day.",
            "decision_rule": "Check confirmed reservations before applying the swap.",
        }

    if not sunday_party:
        return {
            "status": "recommend_base",
            "preferred_scenario": "base",
            "headline": "Keep Magic Kingdom on Sunday",
            "summary": "Sunday is clear in the loaded party schedule, so the base plan avoids unnecessary reservation disruption.",
            "decision_rule": "Continue monitoring official park hours.",
        }

    return {
        "status": "manual_review",
        "preferred_scenario": "base" if base["event_risk_score"] <= alternate["event_risk_score"] else "alternate",
        "headline": "Both Magic Kingdom options need review",
        "summary": "The loaded party schedule does not provide a clean Sunday-to-Wednesday swap.",
        "decision_rule": "Compare reservation impacts and official park hours before locking the park order.",
    }


def get_special_event_intelligence():
    party_dates = _configured_party_dates()
    schedule_status = _schedule_status(party_dates)
    hours_status = _park_hours_status()
    signals = _day_signals(party_dates, schedule_status, hours_status)
    base = _scenario("base", BASE_ASSIGNMENTS, party_dates, schedule_status, hours_status)
    alternate = _scenario("alternate", ALTERNATE_ASSIGNMENTS, party_dates, schedule_status, hours_status)

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "trip_start": TRIP_DATES[0],
        "trip_end": TRIP_DATES[-1],
        "overall_status": "official" if schedule_status == "official" and hours_status == "official" else "provisional",
        "sources": [
            {
                "id": "mnsshp_calendar",
                "label": "Walt Disney World MNSSHP calendar",
                "status": schedule_status,
                "loaded_dates": party_dates,
                "note": "Official 2027 dates have not been loaded." if schedule_status != "official" else "Official party dates are loaded.",
            },
            {
                "id": "park_hours",
                "label": "Walt Disney World park-hours calendar",
                "status": hours_status,
                "note": "Official 2027 park hours have not been loaded." if hours_status != "official" else "Official park hours are loaded.",
            },
        ],
        "tracked_items": [
            {
                "id": "mnsshp",
                "name": "Mickey's Not-So-Scary Halloween Party",
                "park": "Magic Kingdom",
                "priority": "critical",
                "schedule_status": schedule_status,
            },
            {
                "id": "columbus_day",
                "name": "Columbus Day",
                "park": None,
                "priority": "high",
                "schedule_status": "confirmed",
            },
            {
                "id": "early_entry",
                "name": "Early Theme Park Entry",
                "park": "All parks",
                "priority": "medium",
                "schedule_status": hours_status,
            },
            {
                "id": "extended_evening_hours",
                "name": "Extended Evening Hours",
                "park": "Selected parks",
                "priority": "medium",
                "schedule_status": hours_status,
            },
        ],
        "day_signals": [
            {"date": target_date, "signals": signals[target_date]}
            for target_date in TRIP_DATES
            if signals[target_date]
        ],
        "scenarios": {
            "base": base,
            "alternate": alternate,
        },
        "recommendation": _recommendation(base, alternate, party_dates, schedule_status),
    }
