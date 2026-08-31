# Section 8 — Trip Week Phase 2

_Start checkpoint · August 31, 2026_

## Purpose

Section 8 completes the existing Trip Week unified recommendation engine. It does not restart or replace the current engine.

The engine already compares the October 9–16, 2027 base itinerary with the existing Magic Kingdom/EPCOT alternate and can return **keep**, **swap**, **wait**, or **review**. The current calculation combines backend event/calendar risk, confirmed and provisional reservation conflicts, the no-park-hopping constraint, overnight resort convenience, historical directional crowd signals, and readiness/confidence. Scenario changes remain manually approved.

Backend issue [#66](https://github.com/MileHighHoosier/castlewatch-2027/issues/66) is the authoritative Section 8 checklist.

## Start-checkpoint result

The cross-repository audit found no duplicate open Section 8 issue or pull request. The implementation surface is:

- backend `trip_week.py` and the calendar/event/forecast modules that supply Trip Week evidence;
- frontend `app/lib/tripDecisionEngine.ts`, which currently owns scenario scoring and outcomes;
- frontend trip profile, reservation, resort, transportation, weather, Lightning Lane and approval modules that own browser-local planning inputs;
- `TripWeekDecisionPanel.tsx` and `TripWeekDecisionCard.tsx`, which assemble and present the decision.

The current engine is substantial and will be extended incrementally. The Start checkpoint changes documentation and work state only; it does not change product logic, saved plans, production data, credentials, devices, database schema, dependencies/runtime, deployment configuration or family-key state.

## Evidence contract

Each Section 8 signal must expose enough information to explain whether and how it affected a scenario:

| Field | Required meaning |
| --- | --- |
| Availability | Available, unavailable, out of horizon, stale or not assignable |
| Provenance | Backend calendar/forecast or the named browser-local planning source |
| Freshness | Timestamp or explicit reason that freshness does not apply |
| Confidence | Calibrated evidence strength, separate from score magnitude |
| Contribution | Deterministic scenario score contribution; zero when evidence is not safely usable |
| Explanation | User-readable reason tied to the affected date, park, booking or route |

Unavailable, stale, out-of-horizon and unassignable evidence must remain visible and neutral. A missing signal must never silently inherit another signal or become fabricated evidence.

## Delivery checkpoints

### 8A — Evidence and scoring contract

Create the typed evidence/contribution model and regression fixtures around the current engine before changing recommendation behavior.

Acceptance:

- typed availability, provenance, freshness, confidence, contribution and explanation fields;
- deterministic neutral behavior for unusable evidence;
- existing keep/swap/wait/review outcomes preserved by direct regression fixtures;
- backend and frontend ownership boundaries remain explicit;
- no itinerary mutation or production-state change.

Implementation status: frontend PR [#52](https://github.com/MileHighHoosier/castlewatch-frontend/pull/52) merged the typed source-owned evidence contract at `408617e0691ddfb5fa95a460e41e860cecda5b4a`. Scenario totals now derive from explicit evidence contributions; unusable and non-finite evidence is neutral; an unknown origin resort cannot silently inherit the default; and keep/swap/wait/review fixtures remain stable. The [separate Section 8A test checklist](section-8a-test-checklist.md) passed on August 31, 2026. Section 8A remains in progress until the separately commanded Finalize checkpoint.

### 8B — Reservations and transportation

Align recommendation scoring with the existing reservation and Getting There models.

Acceptance:

- confirmed reservation conflicts remain a hard `review` gate;
- the no-park-hopping constraint remains enforced;
- duplicated broad transportation scoring is replaced by one reusable route/timing model aligned with Getting There;
- only evidence assignable to a scenario date and origin resort contributes to its score;
- base/alternate resort, transfer and reservation cases have regression coverage.

### 8C — Weather and Lightning Lane

Integrate these signals only when the saved evidence can validly affect the compared Trip Week scenarios.

Acceptance:

- weather has an explicit trustworthy horizon and freshness state and is neutral outside that horizon;
- Lightning Lane constraints are backward-compatible and contribute only when validly assigned to a trip date and park;
- current unassignable Lightning Lane windows remain neutral rather than being guessed into a scenario;
- no official product rule, booking or forecast is inferred when it is not present;
- missing, stale, invalid and actionable cases have regression coverage.

### 8D — Explainability and release verification

Complete the user-facing decision surface and verify the coordinated release.

Acceptance:

- scenario score breakdown, evidence state, blockers, confidence and affected reservations are understandable;
- apply, undo and lock remain user-controlled;
- frontend tests, production build and 390×844 mobile smoke pass;
- backend tests and active production-module compilation pass;
- the authoritative production UI is verified without mutating shared data or credentials;
- project state, architecture, roadmap and tracker are updated in a separately approved Finalize checkpoint.

## Invariants and non-goals

- Keep the October 9–16, 2027 trip dates and current base/alternate scenario definitions unless separately approved.
- Never auto-apply an itinerary change.
- Historical forecasts remain directional evidence, not precise 2027 predictions.
- Long-range weather does not contribute before the trustworthy forecast horizon.
- Do not create a second transportation truth source.
- Do not pull Reservation Awareness Phase 2, Prediction Phase 2, cross-park ripple prediction, notifications or the Trip-Day Command Center into Section 8.
- Do not change production data, shared-plan versions, account/device state, credentials, schema, dependencies/runtime or deployment configuration as an incidental part of Section 8.
- Keep `CASTLEWATCH_FAMILY_KEY` and `legacy_family_key_enabled` configured and enabled.

## Checkpoint workflow

Section 8 uses separate approvals:

1. `Start Section 8A`
2. implementation/checklist evidence for 8A
3. `Finalize Section 8A`
4. repeat for 8B, 8C and 8D
5. `Finalize Section 8` only after all four batches and production verification pass

The exact next command after the Section 8A checklist is `Finalize Section 8A`.
