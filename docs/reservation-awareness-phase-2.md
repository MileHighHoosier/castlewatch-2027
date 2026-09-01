# Reservation Awareness Phase 2 + 60-day planner

**Started September 1, 2026.** This document is the scope and safety contract for backend issue [#85](https://github.com/MileHighHoosier/castlewatch-2027/issues/85). The Start checkpoint changes documentation and tracking only; product implementation begins separately with `Start Reservation Awareness Phase 2A`.

## Existing foundation

CastleWatch already has a substantial reservation foundation in the frontend:

- browser-local provisional and confirmed reservation records;
- quick-add templates for Bibbidi Bobbidi Boutique, Cinderella's Royal Table, 1900 Park Fare, lightsaber building, private tours and flights;
- date, time, duration, arrival-buffer and location details;
- resort-aware routes and conservative leave-by guidance;
- same-day overlap, transfer and park-assignment warnings;
- shared-plan sync/history and reservation-aware Trip Week decision evidence.

The backend stores and versions the shared family-trip payload as an opaque plan and records a reservation count for operations reporting. It does not currently own booking-window rules. Phase 2 extends this foundation instead of creating a second reservation system.

## Product boundary

A **booking target** is a desired future booking attempt. A **reservation** is an actual or provisional trip booking. They are related but distinct:

- changing a target never creates, deletes, confirms or edits a reservation automatically;
- a successfully booked target may be linked explicitly to a reservation by the user;
- existing reservation records remain valid without booking-target fields;
- itinerary, park order, resort assignments and recommendation approval remain user-controlled.

The 60-day planner is a planning horizon, not a claim that every product follows one universal 60-day policy. Each calculated opening or deadline must retain its rule, provenance, as-of state and any manual override. Unverified, missing, stale or inapplicable rules remain visible and must not be presented as official fact.

## Delivery checkpoints

### Reservation Awareness Phase 2A — planning contract and booking-window engine

- Add an additive, version-tolerant booking-target contract and safe normalization for absent or malformed optional fields.
- Represent target type, priority, desired trip date, booking status, rule provenance/as-of state, opening/deadline calculation and manual override separately.
- Make calculations deterministic and timezone/date-boundary safe.
- Keep unverified or unavailable rules explicit and neutral; never invent official dates.
- Preserve the current reservation payload, shared sync/history and decision behavior.

### Reservation Awareness Phase 2B — 60-day planner

- Present a prioritized timeline for BBB, CRT, 1900 Park Fare, lightsaber building, tours and user-defined targets.
- Show opening dates, deadlines, countdown/readiness states, assumptions and official-verification needs.
- Allow priorities and planning dates to be adjusted without changing reservations or itinerary.
- Keep the mobile surface readable at the existing 390×844 contract viewport.

### Reservation Awareness Phase 2C — attempt and contingency workflow

- Support planned, attempted, booked, unavailable and backup lifecycle states.
- Record attempts and user-selected fallback choices without fabricating availability.
- Link a booked target to an existing or explicitly created reservation only through a deliberate user action.
- Explain downstream timing, reservation and Trip Week effects before any separate approved change.

### Reservation Awareness Phase 2D — in-app reminders and release verification

- Surface upcoming, due, overdue and needs-verification booking actions inside CastleWatch.
- Do not send email, text or push notifications; delivery belongs to the later Notifications and change-alerts phase.
- Run focused contracts, full frontend/backend regression, production build, mobile smoke and read-only production verification.
- Finalize the parent phase only after separate checklist and Finalize approvals.

## Rule and date safety

1. A catalog rule is not automatically authoritative. Store a source label, the date it was reviewed and whether official verification is still required.
2. A user-entered opening date or deadline is an explicit override and must be labeled as such.
3. Calculations use calendar dates in the trip's planning timezone; they must not drift because a browser or server uses UTC.
4. A missing, malformed, stale or non-applicable rule produces an explainable needs-verification state, not a guessed date.
5. Later implementation may include carefully sourced defaults, but live policy research and any rule refresh require their own evidence and tests.

## Data and ownership boundaries

| Concern | Owner | Phase 2 rule |
| --- | --- | --- |
| Booking-target calculation and UI | Frontend | Browser-owned and additive to the current trip-planning model |
| Actual reservation records | Frontend | Existing contract remains backward-compatible |
| Shared family-trip versions/history | Backend API and database | Continue storing the client plan without interpreting booking rules |
| Decision evidence | Frontend | Only explicit, assignable target/reservation effects may contribute |
| External alerts | Later Notifications phase | Out of scope |
| Official policy truth | Named source plus user verification | Never inferred silently |

No dependency/runtime or database-schema change is approved by this Start checkpoint. If a later checkpoint proves one necessary, it must document the reason and preserve rollback/backward compatibility.

## Safety invariants

- No production/shared-plan, itinerary, reservation, resort, recommendation, credential or device mutation occurs during the Start checkpoint.
- No automatic booking, itinerary rearrangement, scenario approval, upload, restore or credential action is introduced.
- Existing local and shared payloads remain readable when booking-target data is absent.
- Raw credentials, family keys and token material never enter source, logs, screenshots or planning records.
- `CASTLEWATCH_FAMILY_KEY` and `legacy_family_key_enabled` remain configured and enabled until a separately authorized retirement decision.

## Parent acceptance

Reservation Awareness Phase 2 can finalize only when:

- opening/deadline calculations and override precedence are deterministic and explainable;
- named and custom booking targets have a usable 60-day timeline;
- lifecycle and contingency actions are explicit and user-controlled;
- in-app reminder/readiness states do not imply external delivery;
- reservation, transportation, shared sync/history and Trip Week decisions remain regression-protected;
- exact-head frontend/backend CI, production build, mobile smoke and read-only production verification pass;
- every implementation checkpoint has its own Start, test checklist and Finalize approval.

## Exact next command

`Start Reservation Awareness Phase 2A`
