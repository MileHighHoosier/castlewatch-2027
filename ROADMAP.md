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

Status: **Complete**

Priority findings addressed in this section:

- bound and serialize the ride-refresh write path,
- narrow effective browser CORS origins,
- stop returning raw internal exceptions to clients,
- add backend `.gitignore`,
- reduce unsafe dynamic HTML/credential exposure in touched credential/weather paths,
- make invite acceptance atomic.

Implementation batches:

- **2A - backend request hardening: Complete and production-verified.** Ride-refresh writes are bounded/serialized with persisted cooldown state, internal 5xx responses are sanitized, backend secret/local-artifact ignore rules are in place, Railway runs enough workers to keep reads available during collection, and `/api/rides` is now a pure nonblocking read path rather than performing schema/setup or collection work. Automated regression tests pass. iPhone verification on August 22, 2026 confirmed normal closed-park behavior returned, History restored to a real value (35,169), and both History and Updated remained unchanged 20-30 seconds after the initial refresh. The refresh endpoint remains a public GET for compatibility and still requires later authorization/interface hardening before CastleWatch is considered production-hardened.
- **2B - weather reliability: Complete and production-verified August 22, 2026.** Last-known automatic heat/storm warnings survive transient refresh failures; weather state distinguishes current/stale/unknown; stale or unavailable weather is shown explicitly instead of being treated as normal; automatic modes clear only after a successful no-advisory response; manual weather controls remain intact; touched weather UI no longer uses dynamic `innerHTML`; severe storm/tornado alerts outrank simultaneous heat alerts; backend weather-provider failures return unknown/null state with HTTP 502. Frontend weather tests and production build passed, backend tests and production-module compilation passed, and the merged Vercel/Railway deployments both reported success.
- **2C - account/input hardening: Complete and production-deployed August 22, 2026.** Invite acceptance is single-consumption under concurrency by locking the invite before verification/consumption; already-consumed invites are rejected; final acceptance is conditioned on the invite remaining open. User-facing device/invite credential paths validate bounded `cwdev_`/`cwinv_` values, malformed persisted credentials are ignored, malformed invite input is rejected, raw backend response text is no longer appended to Family devices errors, and credential-adjacent UI is regression-checked against dynamic HTML sinks. Family-key compatibility and persistent device-token storage remain unchanged. Backend tests/compilation, frontend tests/build, and merged Railway/Vercel deployments all passed.
- **2D - origin/CORS hardening: Complete and production-verified August 22, 2026.** The production Flask boundary now restricts browser-readable cross-origin responses to the CastleWatch production Vercel origin, the CastleWatch project/team preview-origin pattern, and exact additional origins supplied through `CASTLEWATCH_ALLOWED_ORIGINS`. Unrelated origins lose CORS grant headers, allowed methods/headers are bounded, credentials remain disabled, and regression tests cover production, preview, denied, preflight, and configured-local-origin cases. The merged Railway deployment succeeded and iPhone production verification confirmed the normal Vercel-to-Railway path still loaded live backend data and reported Backend connected.

### Section 3 - Dependency management

Status: **Complete — production-deployed August 23, 2026**

Goal achieved: installs are reproducible, the known-good backend/frontend dependency and runtime baselines are explicit, drift is regression-checked, and future upgrades follow a controlled rollback-aware policy without automatic or opportunistic package movement.

Implementation batches:

- **3A - dependency/runtime baseline: Complete.** Exact known-good backend and frontend direct dependency versions and CI runtimes were inventoried and documented before installation behavior changed.
- **3B - backend dependency controls: Complete and production-deployed.** Backend direct dependencies are exact-pinned to the verified working baseline, `.python-version` pins Python 3.12.14 for the Railway source-controlled runtime, GitHub Actions uses the same interpreter, regression checks guard dependency/runtime drift, and the merged Railway deployment succeeded.
- **3C - frontend dependency controls: Complete and production-deployed August 22, 2026.** All direct frontend `latest` declarations were replaced with exact lockfile-proven versions, `package.json` declares Node `22.x`, package-lock root metadata was synchronized without moving any transitive dependency version, and dependency-policy tests guard manifest/lockfile/runtime/`npm ci` alignment. Clean `npm ci`, full frontend tests, the production Next.js build, Vercel preview, and the merged production Vercel deployment all succeeded.
- **3D - controlled upgrade policy and full dependency regression verification: Complete and production-deployed August 23, 2026.** Canonical `DEPENDENCY_POLICY.md` now defines isolated, exact-version, test/build/deployment and rollback gates for future backend/frontend dependency and runtime changes; both repository agent instructions require that policy; `DEPENDENCY_BASELINE.md` is the known-good rollback reference; backend exact-head clean install/tests/compilation and frontend deterministic `npm ci`/tests/production build passed; the 3D changes contained no application/package/runtime behavior changes; backend PR #34 and frontend PR #33 merged; the resulting Railway and real `castlewatch-frontend` Vercel production deployments both succeeded.

### Section 4 - Automated quality-control expansion

Status: **In progress - 4A and 4B complete and production-deployed; 4C next**

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

Implementation batches:

- **4A - QC inventory + Trip Week core decision contracts: Complete and production-deployed August 23, 2026.** Automated coverage was inventoried across both repositories. Five direct frontend contracts now protect `Wait`, `Review`, `Swap` and `Keep` outcomes, confirmed-reservation safety, no-park-hopping weighting, readiness/blocker output and manual itinerary approval. All 37 frontend tests, Node 22 CI and the production Next.js build passed; frontend PR #34 was squash-merged at `fac7ff1fcbe7310d2a4ff25f59fc4fdd02a9549f`; the real `castlewatch-frontend` Vercel production deployment succeeded. No application behavior, itinerary, account/family-key behavior, dependency or runtime version changed.
- **4B - historical/date forecasting and calendar/event contracts: Complete and production-deployed August 24, 2026.** Sixteen focused backend contracts now protect same-weekday thresholds, directional comparisons, confidence/windows, overall fallback and learning states; official/partial calendar extraction; last-known-good cache preservation; unreleased/base/swap/manual-review event outcomes; stale-source labeling; and exact Trip Week park/date signal attachment. QC also corrected ticketed MNSSHP entries overwriting regular operating hours and replaced raw internal fallback exceptions with stable generic messages. Exact-head Python 3.12.14 CI passed the full backend suite and production-module compilation; backend PR #37 was squash-merged at `b40239860192f72ce58c5e01fafc60e22e8d0887`; the merged Railway deployment succeeded. No frontend, itinerary, account/family-key, dependency, runtime or database-schema change was included.
- **4C - transportation/reservation and Lightning Lane contracts: Next.**
- **4D - Park Command Center, Live Plan and emergency-mode contracts: Planned.**
- **4E - shows/activities/characters plus the smallest practical mobile browser/E2E suite: Planned.**
- **4F - full regression/build review and Section 4 closeout: Planned.**

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
