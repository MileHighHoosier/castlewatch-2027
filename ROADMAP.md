# CastleWatch Roadmap

_Last rebaseline: August 2026_

This roadmap supersedes older chat-only progress estimates. It should be updated when a phase is finalized.

## Current phase: Rebaseline & Stabilization

### Section 1 - Authoritative project documentation

Status: **Complete**

Deliverables:

- `PROJECT_STATE.md`
- `ARCHITECTURE.md`
- `AGENTS.md`
- current roadmap
- current frontend README

No product behavior changes belong in this section.

### Section 2 - Immediate security and reliability fixes

Status: **In progress**

Priority findings:

- protect/internalize the ride-refresh write path,
- narrow CORS for protected services,
- stop returning raw internal exceptions to clients,
- add backend `.gitignore`,
- reduce unsafe dynamic HTML/credential exposure,
- make invite acceptance atomic.

Implementation batches:

- **2A - backend request hardening: Complete and production-verified.** Ride-refresh writes are bounded/serialized with persisted cooldown state, internal 5xx responses are sanitized, backend secret/local-artifact ignore rules are in place, Railway runs enough workers to keep reads available during collection, and `/api/rides` is now a pure nonblocking read path rather than performing schema/setup or collection work. Automated regression tests pass. iPhone verification on August 22, 2026 confirmed normal closed-park behavior returned, History restored to a real value (35,169), and both History and Updated remained unchanged 20-30 seconds after the initial refresh. The refresh endpoint remains a public GET for compatibility and still requires later authorization/interface hardening before CastleWatch is considered production-hardened.
- **2B - weather reliability: Complete and production-verified August 22, 2026.** Last-known automatic heat/storm warnings survive transient refresh failures; weather state distinguishes current/stale/unknown; stale or unavailable weather is shown explicitly instead of being treated as normal; automatic modes clear only after a successful no-advisory response; manual weather controls remain intact; touched weather UI no longer uses dynamic `innerHTML`; severe storm/tornado alerts outrank simultaneous heat alerts; backend weather-provider failures return unknown/null state with HTTP 502. Frontend weather tests and production build passed, backend tests and production-module compilation passed, and the merged Vercel/Railway deployments both reported success.
- **2C - account/input hardening: Next.** Make invite acceptance atomic and reduce unsafe dynamic HTML around browser-held credentials.
- **2D - origin/CORS hardening:** narrow browser origins after the production frontend origin set is verified so current iPhone access is not accidentally blocked.

### Section 3 - Dependency management

- replace uncontrolled dependency ranges with deliberate version policy,
- preserve reproducible frontend/backend builds,
- document safe dependency upgrade procedure.

### Section 4 - Automated quality-control expansion

Add regression coverage for core product behavior, especially:

- Park Command Center,
- Live Plan,
- Trip Week decision engine,
- historical/date forecasting,
- calendar/event intelligence,
- transportation/leave-by calculations,
- Lightning Lane behavior,
- emergency break mode,
- weather behavior,
- shows/activities/characters,
- key mobile flows.

Add end-to-end browser coverage when practical.

### Section 5 - Accounts / invitations / device migration completion

Current recommendation: **finish the migration rather than abandon it**, because much of the foundation already exists.

Required before legacy family-key retirement can even be considered:

- normal shared-plan endpoints accept the intended device-token model,
- owner-device bootstrap exists,
- Editor/Viewer permissions are regression-tested,
- revocation/recovery behavior is proven,
- production two-device verification passes,
- the user explicitly approves any future retirement option.

Until then: **do not remove or disable `CASTLEWATCH_FAMILY_KEY`.**

### Section 6 - Production smoke verification

Verify the deployed Vercel/Railway system across critical flows and close or update production-verification issues.

### Section 7 - Lightweight project tracker

Establish a simple durable tracker for:

- phase,
- task,
- status,
- owner/agent,
- acceptance criteria,
- dependencies,
- QC status,
- linked GitHub issue/PR,
- last update,
- exact next action.

The tracker manages work; GitHub remains the source of truth for code and repository documentation.

### Section 8 - Resume product development

Complete **Trip Week Phase 2 - Unified Recommendation Engine** rather than restarting it.

The existing engine already uses event, reservation, resort/transportation and historical crowd signals. Remaining work should integrate missing signals and replace broad heuristics where justified while keeping itinerary changes user-approved.

---

## Product roadmap after stabilization

### 1. Complete Trip Week Phase 2

Goals:

- combine official event dates and park hours,
- reservations,
- overnight resorts,
- transportation time,
- weather when forecast horizon is appropriate,
- historical crowd intelligence,
- Lightning Lane constraints/readiness,
- no-park-hopping constraint,
- confidence/readiness.

Output should remain understandable: keep, swap, wait or review, with reasons and affected reservations.

### 2. Reservation Awareness Phase 2 + 60-day planner

Build largely together:

- booking-opening dates,
- dining/experience deadlines,
- BBB, CRT, 1900 Park Fare, lightsaber and tour priorities,
- booked/attempted/unavailable/backup statuses,
- reminders before reservation windows,
- contingency choices when priority bookings fail.

### 3. Prediction Phase 2

Improve historical forecasts with:

- stronger weekday comparisons,
- seasonal/October effects,
- holiday/special-event separation,
- recent-trend weighting,
- park-hours normalization,
- confidence calibration,
- better handling of changing attraction inventories.

### 4. Cross-park ripple prediction

Estimate displacement caused by:

- early park closures/special events,
- weather,
- major attraction outages,
- unusual operating schedules,
- other cross-park pressure shifts.

This depends on Prediction Phase 2 being stronger first.

### 5. Notifications and change alerts

Notify only for actionable changes such as:

- MNSSHP dates published,
- park hours materially change,
- itinerary/reservation conflict appears,
- meaningful weather risk,
- booking/planning deadline approaches,
- major attraction status affects the active plan.

### 6. Trip-Day Command Center / mobile polish

Refine active-park use around the smallest useful set of information:

- next reservation,
- leave-by time,
- current weather risk,
- live attraction conditions,
- Lightning Lane window,
- best nearby move,
- break/exit recommendation.

Improve information hierarchy with collapsed day cards, summary-first views and less technical detail by default.

### 7. Ongoing reliability and observability

Continue improving:

- source-schema change detection,
- API health history,
- ingestion alerts,
- backup verification,
- deployment smoke checks,
- data-source provenance,
- recovery procedures.

## Deferred / not yet started

- Cross-park ripple prediction.
- Full 60-day pre-trip planner.
- General notification/change-alert system.

## Roadmap rule

Do not start a later roadmap phase merely because it is interesting. Finish or explicitly defer the current dependency first. Update `PROJECT_STATE.md` and this roadmap whenever a phase is finalized.
