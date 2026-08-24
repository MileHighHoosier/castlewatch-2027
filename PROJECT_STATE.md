# CastleWatch Project State

_Last rebaseline: August 2026_

## Purpose

CastleWatch is a private-family Walt Disney World planning and trip-operations system for the October 9-16, 2027 trip. It combines live attraction conditions, historical wait patterns, trip-week planning, reservations, resorts, transportation guidance, weather/event awareness, Lightning Lane tracking, and shared family trip state.

CastleWatch is an unofficial personal planning tool and is not affiliated with Disney.

## Production architecture

- **Frontend:** Next.js application in `MileHighHoosier/castlewatch-frontend`, deployed on Vercel.
- **Backend:** Flask/Python application in this repository, deployed on Railway.
- **Database:** Railway PostgreSQL.
- **Live attraction source:** Queue Times.
- **Weather alert source:** weather.gov.
- **Trip-week calendar/event intelligence:** backend calendar ingestion plus provisional rules when official 2027 data is unavailable.
- **Family sync:** browser-local trip state can be uploaded to/downloaded from a shared PostgreSQL document with optimistic versioning and history.

## Current product maturity

The original feature roadmap is mostly implemented, but CastleWatch is not yet production-hardened enough to treat every recommendation as fully dependable. A reasonable rebaseline is:

- Core tracking and planning foundation: mostly complete.
- Trip-week planning and decision support: substantial, but the unified recommendation engine is incomplete.
- Historical prediction: useful directional signal, not a precise 2027 crowd model.
- Shared family sync/history: substantial implementation.
- Account/device migration: partially implemented and not ready for family-key retirement.
- Automated quality control: stronger for newer sync/account work than for older planning features.
- Documentation and handoff quality: rebaselined in Section 1 and maintained as repository source of truth.

## Major implemented capabilities

### Live park operations

- Four-park dashboard.
- Current ride waits and open/closed status.
- Historical planning insights.
- Heat/area pressure view.
- Live Plan recommendations with multiple planning modes.
- Shows, activities and character layers.
- Emergency break/leave-park behavior.
- Weather-aware planning with last-known advisory preservation and stale/unknown reliability states.
- Manual Lightning Lane window tracking and conflict guidance.

### Trip planning

- October 2027 Trip Week planner.
- Base itinerary and alternate Magic Kingdom/Epcot scenario.
- Historical same-weekday forecast signals.
- Special-event intelligence and calendar ingestion.
- Editable overnight resorts.
- Getting There transportation guidance and leave-by calculations.
- Reservation templates, reservation conflicts and reservation-aware scenario comparison.
- User-approved scenario application/undo/lock behavior.

### Unified Trip Week decision engine

`castlewatch-frontend/app/lib/tripDecisionEngine.ts` already compares the base and alternate itinerary using:

- event risk,
- confirmed/provisional reservation conflicts,
- no-park-hopping preference,
- overnight resort/transportation convenience,
- historical crowd signals,
- readiness/confidence indicators.

The engine can recommend **keep**, **swap**, **wait**, or **review**, but Trip Week Phase 2 is not complete. Weather and Lightning Lane are currently readiness inputs rather than fully integrated scenario-scoring signals, and transportation is still scored mainly through broad resort-category heuristics.

## Shared family sync

Implemented behavior includes:

- shared family trip document in PostgreSQL,
- optimistic `expectedVersion` writes,
- version-conflict detection,
- PostgreSQL write locking,
- 25-version history retention,
- restore-as-new-version,
- browser-local sync metadata,
- guarded upload/download behavior,
- operations/usage support.

The legacy `CASTLEWATCH_FAMILY_KEY` remains the established credential for normal shared-plan read/write/history/restore operations.

## Accounts, invitations and device management

The account/device migration is **partially implemented**.

Implemented:

- family/member/device/invite tables,
- owner/editor/viewer role helpers,
- hashed device and invite tokens,
- device access checks,
- invite creation and atomic single-consumption acceptance,
- device list,
- rename,
- revoke,
- frontend device-management UI/plumbing,
- bounded validation for persisted/returned device and invite credentials,
- credential-management errors no longer append raw backend response bodies,
- credential-adjacent Family devices UI is regression-checked against dynamic HTML sinks,
- automated tests for much of the newer account behavior,
- production verification documentation.

Not complete:

- device-token authorization has not fully replaced the family key for normal shared-plan read/write/history/restore/operations paths,
- owner-device bootstrap/verification is not complete,
- `legacy_family_key_enabled` is not yet the authoritative gate for legacy-key access,
- production two-device verification remains open,
- family-key retirement must not occur yet.

### Current account migration rule

**Do not disable or remove `CASTLEWATCH_FAMILY_KEY`.**

Family-key retirement may only be reconsidered after:

1. normal shared-plan endpoints support the intended device-token authorization model,
2. at least one active owner device exists and is manually verified,
3. Editor/Viewer permissions are regression-tested,
4. revocation and recovery paths are verified in production,
5. the user explicitly approves retirement.

## Prediction status

Current forecasting is a historical directional model. It supports:

- same-weekday comparisons,
- time-of-day blocks,
- sample counts,
- distinct-day counts,
- confidence based on evidence volume,
- best/peak historical windows.

Prediction Phase 2 still needs:

- stronger seasonal effects,
- holiday and special-event separation,
- recent-trend weighting,
- park-hours normalization,
- better confidence calibration,
- cross-park effects.

Do not present current 2027 forecasts as precise predictions.

## Rebaseline stabilization status

### Section 1 - Authoritative project documentation

**Complete.** Canonical project state, architecture, roadmap and agent instructions are now stored in the repositories rather than relying on chat history.

### Section 2A - Backend request hardening

**Complete and production-verified on August 22, 2026.**

Implemented and verified:

- ride-refresh writes are serialized and bounded by a persistent PostgreSQL cooldown,
- internal HTTP 5xx payloads are sanitized,
- backend `.gitignore` protection covers secrets/local artifacts,
- Railway uses multiple Gunicorn workers so long collection work does not monopolize all reads,
- `/api/rides` is a pure nonblocking read path and no longer performs schema/setup or surprise collection work,
- focused backend regression tests pass,
- live iPhone verification confirmed normal closed-park behavior returned,
- live History returned a real value rather than a false zero,
- History and Updated stayed unchanged during the cooldown verification window, consistent with prevention of an immediate duplicate refresh.

Remaining caveat: `/api/refresh-rides` is still a public GET endpoint for compatibility. The cooldown materially reduces abuse/duplication risk, but full authorization/interface hardening remains future stabilization work.

### Section 2B - Weather reliability

**Complete and production-verified on August 22, 2026.**

Implemented and verified:

- transient weather refresh failures no longer clear a previously known automatic heat/storm advisory,
- automatic weather state explicitly distinguishes `current`, `stale`, and `unknown`,
- the last successful weather-check timestamp advances only after a valid successful response,
- a previously automatic heat/storm mode is cleared only after a successful response confirms no advisory,
- stale/unknown weather is surfaced in the frontend instead of being silently treated as normal,
- manual Weather OK/Heat/Storm controls and same-day manual Weather OK override behavior are preserved,
- touched weather UI uses safe text rendering rather than dynamic `innerHTML`,
- backend weather selection gives shelter-first storm/tornado alerts priority over simultaneous heat alerts,
- weather-provider failures return HTTP 502 with unknown/null weather state rather than falsely reporting normal conditions,
- focused frontend weather reliability tests, the frontend production build, backend tests, and backend production-module compilation passed,
- the merged frontend commit deployed successfully to Vercel and the merged backend commit deployed successfully to Railway.

### Section 2C - Account/input hardening

**Complete and production-deployed on August 22, 2026.**

Implemented and verified:

- invite acceptance locks matching invite rows before consumption so simultaneous requests cannot both create devices from one invite,
- already-consumed invites are rejected and the final accepted-state update is conditioned on the invite still being open,
- persisted/returned `cwdev_` device tokens and `cwinv_` invite tokens are bounded and validated on user-facing credential paths,
- malformed saved device credentials are ignored rather than trusted,
- malformed invite tokens are rejected client-side,
- raw backend response text is no longer appended to user-visible Family devices errors,
- credential-adjacent Family devices components are regression-checked to avoid `innerHTML` and `dangerouslySetInnerHTML`,
- family-key compatibility and persistent device-token storage remain intentionally unchanged during the migration,
- backend tests and production-module compilation passed,
- frontend tests and the production Next.js build passed,
- merged backend and frontend commits deployed successfully to Railway and Vercel.

### Section 2D - Origin/CORS hardening

**Complete and production-verified on August 22, 2026.**

Implemented and verified:

- the effective production Flask CORS policy is narrowed at the shared `app.py` boundary despite legacy `core_app.py` still initializing Flask-CORS globally,
- the CastleWatch production Vercel origin and CastleWatch project/team preview-origin pattern remain browser-readable,
- exact additional origins can be supplied through `CASTLEWATCH_ALLOWED_ORIGINS` for controlled local/staging use,
- unrelated origins, including unrelated Vercel sites, do not receive CORS grant headers,
- allowed methods/headers are bounded and credentialed CORS remains disabled,
- regression tests cover allowed production/preview origins, denied origins/preflights and configured local development,
- the merged Railway deployment succeeded,
- iPhone production verification confirmed the normal Vercel-to-Railway path still loaded live backend data and reported Backend connected.

### Section 3 - Dependency management

**Complete and production-deployed on August 23, 2026.**

CastleWatch now has a reproducible known-good dependency/runtime baseline and a controlled, reversible upgrade procedure across both repositories.

#### Section 3A - Dependency/runtime baseline

**Complete.** The exact known-good direct dependency versions and CI runtimes for both repositories were inventoried and documented before changing installation behavior. Stabilization policy is to exact-pin the proven baseline first rather than combine reproducibility work with opportunistic upgrades.

#### Section 3B - Backend dependency controls

**Complete and production-deployed.**

Implemented and verified:

- all six direct backend dependencies are exact-pinned to the green Section 3A baseline,
- `.python-version` pins Python 3.12.14 for Railway's source-controlled runtime selection,
- GitHub Actions uses the same Python 3.12.14 interpreter,
- regression checks detect backend dependency or runtime/CI drift,
- the change contains no application behavior, account/family-key, or frontend modifications,
- the merged Railway deployment succeeded.

#### Section 3C - Frontend dependency controls

**Complete and production-deployed on August 22, 2026.**

Implemented and verified:

- all direct frontend `latest` declarations were replaced with the exact versions already proven by the committed lockfile,
- `package.json` now declares Node `22.x`, aligned with CastleWatch CI and the supported Vercel runtime major,
- `package-lock.json` root metadata was synchronized without changing any transitive dependency version,
- the lockfile package name was normalized from the legacy `castlewatch-phase-one-filepack` name to `castlewatch-frontend`,
- dependency-policy regression tests verify exact manifest pins, lockfile alignment, direct resolved versions, Node 22 CI and continued deterministic `npm ci` usage,
- a clean `npm ci`, full frontend tests and production Next.js build passed,
- the actual `castlewatch-frontend` Vercel preview passed,
- frontend PR #32 was squash-merged and the merged production Vercel deployment reported success.

### Section 3D - Controlled upgrade policy and final dependency verification

**Complete and production-deployed on August 23, 2026.**

Implemented and verified:

- canonical `DEPENDENCY_POLICY.md` defines safe dependency/runtime upgrades and rollback behavior,
- direct dependencies remain exact-pinned and floating `latest`/caret/tilde declarations are prohibited by policy unless a future architecture decision explicitly changes that rule,
- dependency changes must stay isolated from unrelated feature work when practical,
- major framework/runtime upgrades are treated as architecture changes,
- security upgrades can be expedited but still require appropriate test/build/deployment gates,
- automatic dependency-update merging is prohibited,
- `DEPENDENCY_BASELINE.md` is the known-good rollback reference,
- backend and frontend `AGENTS.md` files now require dependency/runtime work to follow the canonical policy and baseline,
- exact-head backend CI passed clean installation, the full backend contract suite, and production-module compilation,
- exact-head frontend CI passed deterministic `npm ci`, the full frontend test suite, and the production Next.js build,
- no application code, dependency versions, lockfile versions, runtime versions, database behavior, account/family-key behavior, or Trip Week behavior changed in 3D,
- backend PR #34 and frontend PR #33 were merged,
- the merged Railway deployment succeeded and the real `castlewatch-frontend` production Vercel deployment succeeded.

### Section 4 - Automated quality-control expansion

**In progress as of August 24, 2026.**

#### Section 4A - QC inventory and Trip Week core decision contracts

**Complete, merged and production-deployed on August 23, 2026.**

Implemented and verified:

- current automated coverage was inventoried across both repositories and recorded in backend issue #35;
- direct frontend regression contracts now protect the existing Trip Week decision engine's `Wait`, `Review`, `Swap` and `Keep` outcomes;
- confirmed reservation conflicts cannot be hidden by a lower aggregate scenario score;
- the approved no-park-hopping constraint remains a stronger cross-park reservation penalty;
- swap guidance remains a manual user-approval action rather than an automatic itinerary mutation;
- the fixtures preserve the approved October 9-16, 2027 real-trip assignments, family profile and split-resort planning model;
- all 37 frontend tests passed under the required Node 22 CI runtime;
- the production Next.js build passed;
- frontend PR #34 was squash-merged at `fac7ff1fcbe7310d2a4ff25f59fc4fdd02a9549f`;
- the real `castlewatch-frontend` production Vercel deployment succeeded.

No application code, itinerary state, account/family-key behavior, dependency or runtime version changed in 4A.

#### Section 4B - Historical/date forecasting and calendar/event contracts

**Complete, merged and production-deployed on August 24, 2026.**

Implemented and verified:

- 16 focused backend contracts now protect same-weekday evidence thresholds, directional comparison boundaries, confidence, best/peak historical windows, overall-baseline fallback and learning state;
- historical outputs remain directional signals rather than invented precise 2027 predictions;
- calendar extraction distinguishes regular operating hours from ticketed events, Early Entry and Extended Evening Hours;
- partial calendar refreshes preserve last-known-good data for failed parks, while total failures preserve stale cached intelligence;
- unreleased, clean Sunday, clean alternate and conflicting MNSSHP schedules retain their provisional/base/swap/manual-review outcomes;
- stale cached calendars are not reported as current official data;
- forecasts and event signals remain attached to the exact approved base and alternate park/date assignments;
- isolated forecast failures and calendar-intelligence failures degrade safely without exposing raw internal exception text;
- the calendar parser no longer lets a timed MNSSHP ticketed event overwrite the true regular park closing time;
- exact-head GitHub Actions passed the pinned Python 3.12.14 dependency installation, full backend contract suite and production-module compilation;
- backend PR #37 was squash-merged at `b40239860192f72ce58c5e01fafc60e22e8d0887`;
- the merged Railway deployment succeeded.

No frontend, itinerary, account/family-key, dependency, runtime or database-schema change was included in 4B.

#### Section 4C - Transportation/reservation and Lightning Lane contracts

**Complete, merged and production-deployed on August 24, 2026.**

Implemented and verified:

- 14 focused frontend contracts now protect the approved October 9-16, 2027 family profile and value resort → Beach Club → AKL split stay;
- default overnight assignments correctly use Beach Club for October 12-14;
- reservation transportation selects the correct overnight/same-day resort and retains conservative leave-by guidance;
- Getting There leave-by and bus-arrival projections use worst-case travel time plus the intended buffers;
- no-park-hopping park conflicts, multi-park days, overlaps, insufficient transfers and exact transfer boundaries remain distinguishable;
- malformed or reversed saved Lightning Lane windows degrade safely;
- Lightning Lane status, urgency, next-hour conflict guidance and next-selection hints remain deterministic under a controlled clock;
- saved/user-entered Lightning Lane ride names render as text rather than dynamic HTML;
- exact-head GitHub Actions passed Node 22 setup, clean dependency installation, all 51 frontend tests and the production Next.js build;
- frontend PR #35 was squash-merged at `94e3f4aa944c6ecde6aac5c0667c78df45ec8721`;
- the real `castlewatch-frontend` production Vercel deployment succeeded.

No backend, dependency, account/family-key, park-order or automatic itinerary change was included in 4C.

#### Section 4D - Park Command Center, Live Plan and emergency-mode contracts

**Complete, merged and production-deployed on August 24, 2026.**

Implemented and verified:

- 19 focused frontend contracts protect Park Command Center normalization, live/closed/non-ride behavior, heat pressure and rope-drop ordering;
- Live Plan Max rides, Low-stress and Cool down recommendations, wait-cap fallback, historical-signal safety, completed-ride filtering and replacement explanations;
- all four park emergency plans, conservative fallback, weather precedence and explicit activation;
- the active emergency overlay now refreshes on park or heat/storm changes so stale guidance does not persist;
- exact-head GitHub Actions passed Node 22 setup, clean dependency installation, all 70 frontend tests and the production Next.js build;
- frontend PR #36 was squash-merged at `8ad963a61c65e0f9f90e9635ecf5406ac7e41491`;
- the real `castlewatch-frontend` production Vercel deployment succeeded.

No backend, itinerary, dependency/runtime, account/family-key, reservation, park-order, shows/activities/characters or 4E E2E work was included in 4D.

**Next Section 4 batch: 4E - shows/activities/characters plus the smallest practical mobile browser/E2E suite.**

## Known rebaseline findings still requiring remediation

### High priority

- Accounts/device migration is incomplete and must not be mistaken for completed family-key replacement.
- The ride-refresh endpoint remains a public GET even though 2A now rate-limits/serializes the expensive work.

### Important hardening/maintainability

- Long-lived family/device credentials currently live in browser `localStorage`; remaining dynamic `innerHTML` usage elsewhere still raises the impact of any XSS defect.
- Frontend behavior relies in several places on imperative DOM patching and polling rather than shared React state.
- Automated regression coverage is concentrated around family sync/account work and is sparse for older park-planning features.
- Legacy scaffold code remains beside production code and needs cleanup or explicit archiving.
- Legacy `core_app.py` still initializes Flask-CORS globally; Section 2D safely enforces the effective narrowed browser policy at the production boundary, but eventual core cleanup remains maintainability debt.
- The obsolete `castlewatch-2027` Vercel project integration can still report failures for frontend commits even when the real `castlewatch-frontend` project is healthy; deployment integration cleanup remains future hygiene work.
- Both repositories are public while personal trip dates and itinerary assumptions are encoded in source; repository privacy/config separation should be decided explicitly.

## Where development stopped before the rebaseline

The most recent pre-rebaseline development thread was the Accounts / Invitations / Device Management migration and production verification work. The frontend production-verification issue for the Family devices panel remained open. The prior Trip Week Phase 2 plan is no longer a clean "next feature" because the decision engine already exists in partial form.

## Current development phase

**CastleWatch Rebaseline & Stabilization - Section 4 in progress**

Sections 4A, 4B, 4C and 4D are complete. Section 4E is next. Do not add major new product features until the remaining rebaseline/stabilization quality-control work improves automated regression coverage and the account/device migration direction is resolved.

## Exact next priorities

1. **Section 4E - add shows/activities/characters contracts plus the smallest practical mobile browser/E2E suite.**
2. Finish or deliberately freeze the Accounts/Device migration; current recommendation is to finish it.
3. Production smoke verification.
4. Establish a lightweight project/task tracker.
5. Resume and complete Trip Week Phase 2 unified recommendation engine.

See `ROADMAP.md` for the broader order and `ARCHITECTURE.md` for system boundaries.
