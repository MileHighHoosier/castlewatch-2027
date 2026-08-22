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
- Documentation and handoff quality: rebaselined in Section 1 and now maintained as repository source of truth.

## Major implemented capabilities

### Live park operations

- Four-park dashboard.
- Current ride waits and open/closed status.
- Historical planning insights.
- Heat/area pressure view.
- Live Plan recommendations with multiple planning modes.
- Shows, activities and character layers.
- Emergency break/leave-park behavior.
- Weather-aware planning.
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
- invite creation and acceptance,
- device list,
- rename,
- revoke,
- frontend device-management UI/plumbing,
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
- live History returned a real value (35,169) rather than a false zero,
- History and Updated stayed unchanged 20-30 seconds after the initial refresh, consistent with the cooldown preventing an immediate duplicate refresh.

Remaining caveat: `/api/refresh-rides` is still a public GET endpoint for compatibility. The cooldown materially reduces abuse/duplication risk, but full authorization/interface hardening remains future stabilization work.

### Section 2B - Weather reliability

**Next.** Preserve last-known heat/storm warnings across transient weather-refresh failures and explicitly represent stale/unknown weather state rather than silently clearing an active warning.

## Known rebaseline findings still requiring remediation

### High priority

- Weather frontend behavior can clear a previously active automatic warning when the weather request fails; stale last-known warnings should be preserved instead.
- Accounts/device migration is incomplete and must not be mistaken for completed family-key replacement.
- The ride-refresh endpoint remains a public GET even though 2A now rate-limits/serializes the expensive work.

### Important hardening/maintainability

- Global Flask CORS should be narrowed for protected routes.
- Long-lived family/device credentials currently live in browser `localStorage`; dynamic `innerHTML` usage raises the impact of any XSS defect.
- Invite acceptance should be made atomic against concurrent acceptance.
- Frontend behavior relies in several places on imperative DOM patching and polling rather than shared React state.
- Backend dependencies are unpinned; frontend manifest uses `latest` ranges even though the lockfile currently stabilizes installs.
- Automated regression coverage is concentrated around family sync/account work and is sparse for older park-planning features.
- Legacy scaffold code remains beside production code and needs cleanup or explicit archiving.
- Both repositories are public while personal trip dates and itinerary assumptions are encoded in source; repository privacy/config separation should be decided explicitly.

## Where development stopped before the rebaseline

The most recent pre-rebaseline development thread was the Accounts / Invitations / Device Management migration and production verification work. The frontend production-verification issue for the Family devices panel remained open. The prior Trip Week Phase 2 plan is no longer a clean "next feature" because the decision engine already exists in partial form.

## Current development phase

**CastleWatch Rebaseline & Stabilization - Section 2B next**

Do not add major new product features until the rebaseline/stabilization work fixes the remaining high-priority reliability/security issues, improves automated regression coverage, and resolves the account/device migration direction.

## Exact next priorities

1. **Section 2B - Weather reliability.**
2. Section 2C - account/input hardening.
3. Section 2D - origin/CORS hardening.
4. Dependency-management controls.
5. Broaden automated quality-control coverage.
6. Finish or deliberately freeze the Accounts/Device migration; current recommendation is to finish it.
7. Production smoke verification.
8. Establish a lightweight project/task tracker.
9. Resume and complete Trip Week Phase 2 unified recommendation engine.

See `ROADMAP.md` for the broader order and `ARCHITECTURE.md` for system boundaries.
