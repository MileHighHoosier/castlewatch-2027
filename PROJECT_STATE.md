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

**In progress. Sections 3A, 3B and 3C are complete; Section 3D is next.**

#### Section 3A - Dependency/runtime baseline

**Complete.** The exact known-good direct dependency versions and CI runtimes for both repositories were inventoried and documented before changing installation behavior. Stabilization policy is to exact-pin the proven baseline first rather than combine reproducibility work with opportunistic upgrades.

#### Section 3B - Backend dependency controls

**Complete and merged.**

Implemented and verified:

- all six direct backend dependencies are exact-pinned to the green Section 3A baseline,
- `.python-version` pins Python 3.12.14 for Railway's source-controlled runtime selection,
- GitHub Actions uses the same Python 3.12.14 interpreter,
- regression checks detect backend dependency or runtime/CI drift,
- the change contains no application behavior, account/family-key, or frontend modifications.

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

**Next.** Document the normal safe dependency-upgrade procedure and perform the final cross-repository dependency/regression verification required to close Section 3 before moving to broader automated quality-control expansion.

## Known rebaseline findings still requiring remediation

### High priority

- Accounts/device migration is incomplete and must not be mistaken for completed family-key replacement.
- The ride-refresh endpoint remains a public GET even though 2A now rate-limits/serializes the expensive work.

### Important hardening/maintainability

- Long-lived family/device credentials currently live in browser `localStorage`; remaining dynamic `innerHTML` usage elsewhere still raises the impact of any XSS defect.
- Frontend behavior relies in several places on imperative DOM patching and polling rather than shared React state.
- Section 3D still needs to document the controlled dependency-upgrade procedure and close the dependency-management phase with full cross-repository verification.
- Automated regression coverage is concentrated around family sync/account work and is sparse for older park-planning features.
- Legacy scaffold code remains beside production code and needs cleanup or explicit archiving.
- Legacy `core_app.py` still initializes Flask-CORS globally; Section 2D safely enforces the effective narrowed browser policy at the production boundary, but eventual core cleanup remains maintainability debt.
- The obsolete `castlewatch-2027` Vercel project integration can still report failures for frontend commits even when the real `castlewatch-frontend` project is healthy; deployment integration cleanup remains future hygiene work.
- Both repositories are public while personal trip dates and itinerary assumptions are encoded in source; repository privacy/config separation should be decided explicitly.

## Where development stopped before the rebaseline

The most recent pre-rebaseline development thread was the Accounts / Invitations / Device Management migration and production verification work. The frontend production-verification issue for the Family devices panel remained open. The prior Trip Week Phase 2 plan is no longer a clean "next feature" because the decision engine already exists in partial form.

## Current development phase

**CastleWatch Rebaseline & Stabilization - Section 3D next**

Do not add major new product features until the rebaseline/stabilization work completes dependency controls, improves automated regression coverage, and resolves the account/device migration direction.

## Exact next priorities

1. **Section 3D - controlled dependency-upgrade policy and final cross-repository dependency verification.**
2. **Section 4 - broaden automated quality-control coverage.**
3. Finish or deliberately freeze the Accounts/Device migration; current recommendation is to finish it.
4. Production smoke verification.
5. Establish a lightweight project/task tracker.
6. Resume and complete Trip Week Phase 2 unified recommendation engine.

See `ROADMAP.md` for the broader order and `ARCHITECTURE.md` for system boundaries.
