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
- Account/device migration: Section 5 is complete and production-verified; family-key recovery remains enabled and retirement is not authorized.
- Automated quality control: broad regression protection now covers the core planning, live-operations, sync/account, safety and mobile-browser paths reviewed in Section 4.
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

Normal shared-plan read/write/history/restore and Operations paths accept one explicitly selected family key or protected device credential. The family key retains owner-equivalent recovery behavior; verified device roles enforce Owner/Editor write, restore and Operations access and Viewer read/history-only access.

## Accounts, invitations and device management

The account/device migration is **complete through Section 5** and passed production Owner/two-device verification on August 29, 2026.

Implemented:

- family/member/device/invite tables,
- owner/editor/viewer role helpers,
- hashed device and invite tokens,
- device access checks,
- explicit family-key-only owner-device bootstrap tied to the seeded owner member,
- invite creation and atomic single-consumption acceptance,
- device list,
- rename,
- revoke,
- frontend device-management UI/plumbing,
- proxy-managed `Secure`, `HttpOnly`, `SameSite=Strict` device credentials scoped to the shared-family proxy path,
- acknowledged one-time migration from legacy raw device-token storage to the protected cookie,
- explicit family-key/device-cookie selection for device management without silent fallback,
- dual family-key/device authorization for normal shared-plan read, write, history, history-version, restore and Operations paths,
- exact server-enforced Owner/Editor/Viewer permissions across those normal routes,
- one typed frontend authorization abstraction across manual sync, guarded autosave, history/restore and Operations,
- Viewer read/history-only controls with no attempted autosave, restore or Operations access,
- authoritative `legacy_family_key_enabled` enforcement across family-key device-management and shared-plan requests while the production value remains enabled,
- revoked-device denial across device management and shared-plan read/history/version/write/restore/Operations without mutation or family-key fallback,
- selected protected-cookie `401` cleanup that expires the cookie, clears safe device metadata and leaves an explicit disconnected selection,
- family-key-only owner-device revocation with transaction locking and explicit replacement bootstrap,
- primary/previous/family-key compatibility pepper verification with successful-use rehash for active devices and open invites,
- one-time bootstrap/invite credentials removed before setup responses reach browser JavaScript,
- bounded validation for persisted/returned device and invite credentials,
- credential-management errors no longer append raw backend response bodies,
- credential-adjacent Family devices UI is regression-checked against dynamic HTML sinks,
- automated tests for much of the newer account behavior,
- completed production verification documentation.

Remaining boundaries:

- the legacy direct frontend proxy remains key-only and has no current in-repository caller,
- family-key recovery remains configured and enabled,
- family-key retirement is a separate future decision and is not authorized.

Section 5A finalized the authoritative remaining-work contract in `docs/accounts_migration_contract.md`. The audit reconciled both deployed repositories, recorded the current authorization matrix and ten migration gaps, and divided the remaining implementation into separately approved 5B–5E batches. It did not change account state or production authorization.

Section 5B finalized the owner-bootstrap and protected-credential foundation. It did not enable device credentials for normal shared-plan operations, create a production owner-device record, or disable the family key.

Section 5C finalized normal shared-plan dual authorization and the exact Owner/Editor/Viewer role matrix. It preserved family-key recovery, version conflicts, history retention, payload limits and restore-as-new-version behavior; it did not create a production device or pull 5D hardening or 5E production verification forward.

Section 5D finalized revoked-credential denial, the still-enabled authoritative legacy-key gate, owner recovery, pepper continuity and protected-cookie failure cleanup. It did not create a production device, alter a secret or pepper environment value, change the production legacy-key flag value, retire the family key or pull 5E real-device verification forward.

Section 5E completed the live production run. A protected Owner was bootstrapped and persisted; a second device passed Editor and Viewer role boundaries, self-rename, Owner-managed revocation and clean revoked-cookie-only denial without family-key fallback. Family-key recovery was explicitly reverified, the final shared plan reached version 17 with history intact, and the October 9–16, 2027 trip profile and manual recommendation control remained unchanged. Temporary Editor/Viewer devices were revoked, the tested Owner remains active, and Railway plus the authoritative frontend Vercel deployment remained green.

### Current account migration rule

**Do not disable or remove `CASTLEWATCH_FAMILY_KEY`.**

Family-key retirement may only be reconsidered after:

1. at least one active owner device exists and is manually verified,
2. device-authorized normal shared-plan and Editor/Viewer role boundaries pass production checks,
3. revocation and recovery pass production checks without hidden family-key fallback,
4. production two-device verification passes,
5. the user separately and explicitly approves retirement.

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

**Complete and production-deployed on August 24, 2026.**

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

#### Section 4E - Shows/activities/characters and mobile browser/E2E contracts

**Complete, merged and production-deployed on August 24, 2026.**

Implemented and verified:

- 12 focused frontend contracts protect show schedule parsing/sorting/past-state, WDW source filtering, show/character separation, activity eligibility/badges/use cases/order and text-safe names;
- true meet-and-greet classification is centralized, while character-themed activities such as Enchanted Tales with Belle remain under Activities unless they are true meets;
- timed stage shows remain outside ride-demand planning and receive consistent Show/A/C guidance;
- past-only shows no longer appear as upcoming and unrelated Orlando content fails closed;
- the explicit device-width viewport and two-row, three-column mobile navigation preserve six primary controls with 44-pixel section touch targets;
- a dependency-free Chrome smoke passed at 390×844 through primary navigation, Activities, mocked live showtimes, Characters, Epcot switching and zero horizontal overflow;
- exact-head GitHub Actions passed Node 22 setup, clean dependency installation, all 82 frontend tests, the production Next.js build and the Chrome smoke;
- frontend PR #37 was squash-merged at `53830cc16c33ebf4bdc4058fe994c15f290c80ae`;
- the real `castlewatch-frontend` preview and merged production Vercel deployments succeeded.

No backend product code, dependency/lockfile/runtime, itinerary, reservation, park-order, account/family-key, database or 4F work was included in 4E.

#### Section 4F - Full regression/build review and Section 4 closeout

**Complete, merged and production-deployed on August 24, 2026.**

Implemented and verified:

- the exact post-4E production heads were reviewed across both repositories with no later roadmap work pulled forward;
- exact-head backend GitHub Actions used Python 3.12.14, installed the pinned requirements, passed all 69 contracts and compiled every active root production module with `python -m py_compile *.py`;
- backend CI no longer relies on a hand-maintained partial production-module list;
- live-planning query-hour and generated-at output now share one timezone-aware UTC instant, preserving the established RFC 3339 `Z` shape and eliminating the Python 3.12 deprecation warning;
- exact-head frontend GitHub Actions used Node 22, completed clean `npm ci`, passed all 82 contracts, built the production Next.js app and passed the dependency-free 390×844 Chrome smoke;
- the browser smoke confirmed six primary buttons, three mobile columns, Activities, timed showtimes, Characters, Epcot switching and zero horizontal overflow;
- frontend QC documentation now describes the complete contract/build/browser gate and no longer contains the stale Section 1 pre-merge note;
- backend PR #42 was squash-merged at `1db9c1ac6e00d3555eda9a000b94b9dc67a63aed`, and the Railway production deployment succeeded;
- frontend PR #38 was squash-merged at `416e8d0deb3c4740f046dd0afa6f9cfe0377cca3`, and the real `castlewatch-frontend` production Vercel deployment succeeded;
- the pre-existing unlinked `/sexy` concept route was recorded as legacy/experimental surface and intentionally left unchanged rather than silently removed during QC closeout.

No dependency/runtime version, lockfile, itinerary, reservation, park-order, account/family-key, database, automatic itinerary or Section 5 work was included in 4F.

**Section 4 is complete.**

### Section 5 - Accounts / invitations / device migration completion

**Complete and production-verified on August 29, 2026.**

#### Section 5A - Architecture audit and migration contract

**Complete, merged and production-deployed on August 24, 2026.**

Implemented and verified:

- the exact post-Section-4 backend and frontend production heads were audited against the deployed account/device code, historical design documents, backend issue #10 and frontend production-verification issue #25;
- already-deployed schema, token helpers, device/invite routes, frontend clients and device-management UI were inventoried so earlier account gates are not repeated;
- ten remaining gaps were recorded, including the absent owner-device bootstrap, family-key-only normal shared-plan routes, unwired normal-route role enforcement, non-authoritative legacy-key flag, masked device-only checks, JavaScript-readable raw device credential, pepper-continuity requirement and incomplete production verification;
- `docs/accounts_migration_contract.md` now defines the target Owner/Editor/Viewer matrix, one-credential/no-silent-fallback rule, protected same-origin credential boundary, owner bootstrap, recovery, last-owner and non-retirement requirements;
- the remaining work is divided into separately approved 5B–5E batches;
- exact-head Python 3.12.14 GitHub Actions completed a clean dependency install, passed all 69 backend contracts and compiled every active root production module;
- the audited frontend head separately passed all 82 contracts and the production Next.js build;
- backend PR #44 was squash-merged at `8d970cfff75d6b859e3b242f5d0b0d312d0151c5`, and the Railway production deployment succeeded.

No production code, schema, data, credential, dependency, runtime, itinerary, account state or frontend behavior changed in 5A. `CASTLEWATCH_FAMILY_KEY` remains configured and enabled.

#### Section 5B - Owner-device bootstrap and protected credential foundation

**Complete, merged and production-deployed on August 24, 2026.**

Implemented and verified:

- backend owner bootstrap is an explicit family-key-only action tied to the seeded active owner member;
- bootstrap locks the seeded owner, prevents a second active owner device, allows explicit replacement after revocation, returns only safe metadata outside the one-time setup response and leaves `legacy_family_key_enabled` unchanged;
- bootstrap and invite-acceptance one-time credential responses are non-cacheable;
- the Next.js proxy stores device credentials in a narrowly scoped `Secure`, `HttpOnly`, `SameSite=Strict` cookie and removes raw credentials before setup responses reach browser JavaScript;
- legacy raw local device credentials migrate only after server acknowledgment; failed migration remains recoverable, and browser-readable storage keeps safe display metadata only;
- device-management requests select exactly one family-key or protected-cookie credential, with no silent fallback after a selected device credential is missing, rejected or revoked;
- same-origin JSON validation, response scrubbing and credential-clearing contracts protect the proxy boundary;
- normal shared-plan read/write/history/restore/operations actions remain family-key-only for the separately approved 5C batch;
- exact-head Python 3.12.14 GitHub Actions completed clean installation, passed all 79 backend contracts and compiled the production modules;
- exact-head Node 22 GitHub Actions completed clean installation, passed all 90 frontend contracts, built the production application and passed the mobile browser smoke;
- backend PR #46 was squash-merged at `5456a272041f2d329b26ff7cd4b1a338e8960d51`, and Railway succeeded;
- frontend PR #39 was squash-merged at `c7b2159d7774ce6d01682626f71da4a2f2dc5dfb`, and the real `castlewatch-frontend` Vercel production deployment succeeded.

No production owner-device record was created, no existing account/shared-trip/history data or schema changed, and no dependency/runtime, itinerary, reservation, park-order or automatic-plan change was included. `CASTLEWATCH_FAMILY_KEY` remains configured and enabled.

#### Section 5C - Normal shared-plan dual authorization and role enforcement

**Complete, merged and production-deployed on August 24, 2026.**

Implemented and verified:

- normal shared-plan read, history, history-version, write, restore and Operations routes accept exactly one explicitly selected family key or protected device credential;
- backend authorization runs inside the existing shared-plan transaction and enforces Owner/Editor read-write-restore-Operations access plus Viewer read/history-only access from the verified server record;
- requests with both credential types, malformed or revoked credentials, or a device outside the fixed `family` workspace are rejected without family-key fallback;
- one typed frontend authorization abstraction now governs manual sync, guarded autosave, history/version/restore and Operations;
- Viewer UI remains read/history-only and does not offer or attempt upload, autosave, restore or Operations actions, while server enforcement remains authoritative;
- family-key recovery, optimistic version conflicts, history retention, payload limits and restore-as-new-version behavior remain regression-protected;
- exact-head Python 3.12.14 GitHub Actions completed clean installation, passed all 82 backend contracts and compiled the production modules;
- exact-head Node 22 GitHub Actions completed clean installation, passed all 99 frontend contracts, built the production application and passed the mobile browser smoke;
- backend PR #48 was squash-merged at `d8b7fa630cbd2a20a77044b04c5d1f3ae9565918`, and Railway succeeded;
- frontend PR #40 was squash-merged at `283b0da71b4a540c74e09360d5b599b8ecc57086`, and the real `castlewatch-frontend` Vercel production deployment succeeded.

No production owner-device record was created, no existing account/shared-trip/history data or schema changed, and no dependency/runtime, itinerary, reservation, park-order, legacy-key flag, pepper, last-owner or automatic-plan change was included. `CASTLEWATCH_FAMILY_KEY` remains configured and enabled.

#### Section 5D - Revocation, recovery and legacy-gate hardening

**Complete, merged and production-deployed on August 24, 2026.**

Implemented and verified:

- every family-key device-management and shared-plan request reads `legacy_family_key_enabled` from the fixed workspace, and a disabled value fails closed without changing device-authorized access;
- revoked credentials are denied across device access/list/invite/rename/revoke/bootstrap and shared-plan read/history/history-version/write/restore/Operations paths without state mutation or family-key fallback;
- a selected protected-device `401` expires the protected cookie, clears safe browser device metadata and records an explicit disconnected selection rather than selecting a saved family key;
- the current device cannot revoke itself, an owner device cannot revoke an owner peer, and owner-device revocation is serialized and restricted to the explicit family-key recovery path before replacement bootstrap;
- new credentials use the primary pepper, while active devices and open invites can verify through the previous pepper or family-key compatibility source and rehash to the primary pepper after successful use;
- `docs/accounts_recovery_rollback.md` now documents safe browser recovery, owner replacement, authoritative-flag recovery, pepper transition/rollback and deployment rollback without exposing secret values;
- exact-head Python 3.12.14 GitHub Actions completed clean installation, passed all 90 backend contracts and compiled every active root production module;
- exact-head Node 22 GitHub Actions completed clean installation, passed all 104 frontend contracts, built the production application and passed the mobile browser smoke;
- backend PR #50 was squash-merged at `79094f56af9b8d0be18fae6e518365d6775bd35a`, and Railway plus the production health endpoint succeeded;
- frontend PR #41 was squash-merged at `f591f5b140e5ca0654f04a1433963d7ba560bd71`, and the real `castlewatch-frontend` Vercel production deployment succeeded.

No production owner-device record was created, no secret or pepper environment value or legacy-key flag value changed, and no existing account/shared-trip/history data, schema, dependency/runtime, itinerary, reservation, park-order, automatic-plan or family-key retirement change was included. `CASTLEWATCH_FAMILY_KEY` remains configured and enabled.

#### Section 5E - Production two-device verification and Section 5 closeout

**Complete and production-verified on August 29, 2026.**

Implemented and verified:

- frontend PR #42 merged at `fe964bec64f1d2071c899e2ea5d8bf3d79a1e949`, completing protected-device self-rename;
- frontend PR #43 merged at `f87f5b761cb0cec7c74defad723a3790bf85a6fd`, making family-key recovery selection explicitly verifiable;
- frontend PR #44 merged at `f7b5ccbf38081ff044808899ef7c965c2e04e1cd`, adding confirmed content-identical manual backups; all 111 frontend tests and the production build passed, and the authoritative Vercel deployment succeeded;
- family-key recovery and a persistent protected Owner device were verified on the trusted production browser;
- a second real browser/phone with no family key passed Editor read/write/history/restore/Operations behavior, Viewer read/history-only enforcement, server-authoritative role checks and self-rename;
- Owner-managed revocation produced timestamped revoked rows, and the untouched revoked-cookie-only browser was rejected, cleared into an explicit disconnected state and never fell back to the family key;
- content-identical backup/restore checks preserved append-only history, followed by one deliberate optimistic upload that corrected only the trip name and created shared version 17;
- final invariants are `Columbus Day Week 2027`, October 9–16, 2027, two adults, two children, no park hopping, zero bookings and the unchanged **Wait / Keep the base plan provisional** recommendation state;
- `Ryan Brave Owner` remains active, temporary Editor/Viewer devices are revoked, device rows expose safe metadata only, and Railway `/health` plus the authoritative frontend deployment remained green;
- no raw credential or secret entered source, GitHub, logs or screenshots, and no dependency/runtime, schema, itinerary order, reservation, automatic recommendation, legacy-key flag or family-key retirement change was included.

**Section 5 is complete. `CASTLEWATCH_FAMILY_KEY` and `legacy_family_key_enabled` remain configured and enabled.**

### Section 6A - Production baseline and smoke contract

**Complete and finalized August 30, 2026.**

Automated baseline evidence:

- frontend `main` is `1598d6498d447f6e0ce18b06c4bba6090bdb85d2`, and backend `main` is `b590baf35d1dd222d2ee9e4ab7e407386745c4e5`;
- frontend PR #45 and backend PR #52 are merged, their relevant Family sync reliability workflows passed, and the authoritative Vercel/Railway deployment statuses are successful;
- the live production frontend returned HTTP 200, and Railway `/health` returned HTTP 200 with status `ok`;
- unauthenticated shared-plan, history, Operations and device-access reads returned sanitized HTTP 401 responses;
- production CORS granted the real CastleWatch frontend origin and did not grant an unrelated origin;
- the finalized Section 5E invariant baseline remains shared version 17, the approved October 9–16, 2027 trip/profile, zero bookings, the unchanged **Wait / Keep the base plan provisional** recommendation, one active protected Owner, revoked temporary devices, guarded autosave off and enabled family-key recovery.
- a fresh trusted-Owner production screenshot confirmed **Connected · v17**, shared version 17, `Ryan Brave Owner · owner`, **Up to date**, and guarded autosave off.

The Section 6A checks did not change production data, credentials, code, dependencies/runtime, schema, itinerary, reservations, recommendation state, device records or the family-key setting. All 6A acceptance criteria passed, and PR #54 finalizes the checkpoint without starting 6B. The governing checklist and the 6A–6D scope are recorded in `docs/section-6-production-smoke.md`.

### Section 6B - Core website flows

**Complete and finalized August 30, 2026.**

Production verification passed for the six-destination navigation shell; all four park dashboards; live/open and closed-attraction presentation; update/source context; historical directional planning; current weather reliability plus conservative temporary Heat/Storm guards; Shows, Activities and Characters; all three Live Plan modes; temporary browser-local Lightning Lane guidance; and temporary emergency mode. Every temporary browser-local state was restored, and no shared-plan, itinerary, reservation, credential, device, dependency/runtime, schema or family-key state changed.

The run found two isolated frontend defects. Frontend PR [#47](https://github.com/MileHighHoosier/castlewatch-frontend/pull/47) corrected the Disney Jr. show classification and frontend PR [#49](https://github.com/MileHighHoosier/castlewatch-frontend/pull/49) fixed delayed Lightning Lane mutation feedback; both passed exact Node 22 CI, the full frontend contract suite, production build and mobile browser smoke, deployed successfully through the authoritative `castlewatch-frontend` Vercel project and passed repeated production checks. Trip Week, shared-plan, reservations, resorts, transportation and role-boundary verification remain reserved for 6C. Mobile-specific and forced-failure verification remain reserved for 6D.

### Section 6C - Trip Week and shared-plan flows

**Complete and finalized August 30, 2026.**

Production verification passed for the approved Trip Week profile and zero-booking baseline; saved Base plan, trip-day cards and overnight resorts; reservation readiness; trip-day/resort-aware Getting There guidance; unified recommendation reasoning and manual approval boundaries; protected Owner connection at shared version 17; synchronization and guarded-autosave state; retained history and restore provenance; and the current Owner/Editor/Viewer contract and completed Section 5E production evidence.

The trusted Owner remained `Ryan Brave Owner · owner`, connected and up to date at shared version 17 with guarded autosave off. Backup History & Restore retained 13 snapshots, marked version 17 current and preserved older-version provenance. The completed Section 5E content-identical backup evidence was reused, so 6C made no upload, download, backup, restore, trip/profile/reservation/resort, recommendation, credential/device, dependency/runtime/schema or family-key mutation. No new defect was found. Section 6D starts separately below.

### Section 6D - Mobile, failure-state and Section 6 closeout

**Complete and finalized August 31, 2026.**

Production verification passed for the established 390×844 mobile portrait layout, six-destination navigation, touch targets, sticky navigation, park and Trip Week paths, Getting There, shared-plan/Family devices/history/Operations role boundaries, confirmation and warning states, and isolated backend/source/credential failure behavior. Failure evidence remained explicit and sanitized, rejected unauthorized credentials without silent family-key fallback and recovered cleanly.

The final backend gates passed all 90 contracts and production-module compilation. The frontend gates passed 114 contracts under Node 22, the production Next.js build and the dependency-free 390×844 mobile smoke. The only 6D finding, frontend issue [#50](https://github.com/MileHighHoosier/castlewatch-frontend/issues/50), was repaired in frontend PR [#51](https://github.com/MileHighHoosier/castlewatch-frontend/pull/51) at `90fa1f5eb3d2803e728ce7fcf067fd6f8edd6c0f`, deployed successfully through the authoritative `castlewatch-frontend` Vercel project and visually reverified in the connected Owner production view. No production shared-plan/profile/itinerary/reservation/resort/recommendation/credential/device/dependency/runtime/schema/family-key state changed.

**Section 6 is complete. `CASTLEWATCH_FAMILY_KEY` and `legacy_family_key_enabled` remain configured and enabled.**

### Section 7 - Lightweight project tracker

**Complete and finalized August 31, 2026.**

Section 7 established canonical `PROJECT_TRACKER.md` for backend and frontend work with 15 stable active/future task IDs; explicit status and QC vocabularies; the required phase, task, owner, acceptance, dependency, evidence, update and next-action fields; reconciliation with both repositories; checkpoint maintenance rules; fresh-agent handoff verification; and repeatable structural QC in `scripts/validate_project_tracker.py` plus focused tests.

The audit reconciled backend issue [#61](https://github.com/MileHighHoosier/castlewatch-2027/issues/61), frontend issue [#14](https://github.com/MileHighHoosier/castlewatch-frontend/issues/14), the roadmap and known rebaseline debt without reopening completed Sections 1–6. Frontend #14 remains an explicit user decision rather than being silently closed. Implementation PR [#63](https://github.com/MileHighHoosier/castlewatch-2027/pull/63) and handoff-alignment PR [#64](https://github.com/MileHighHoosier/castlewatch-2027/pull/64) passed the required validation and CI gates. The separately approved Finalize checkpoint closed Section 7 and issue #61 without starting Section 8 or changing application behavior, production data, credentials, devices, dependencies/runtime, schema or family-key configuration. `docs/section-7-project-tracker.md` is the governing contract.

### Section 8 - Trip Week Phase 2 unified recommendation engine

**Started August 31, 2026; implementation has not started.**

The Start audit confirmed that Section 8 extends the substantial existing frontend engine rather than replacing it. The current keep/swap/wait/review decision already combines backend event/calendar risk, reservation conflicts, no-park-hopping, overnight resort convenience and historical directional crowd evidence while preserving manual scenario approval.

`docs/section-8-trip-week-phase-2.md` and backend issue [#66](https://github.com/MileHighHoosier/castlewatch-2027/issues/66) divide delivery into separately approved 8A–8D checkpoints: typed evidence/scoring contracts; reservation and transportation alignment; trustworthy weather and assignable Lightning Lane integration; then explainability and coordinated release verification. Unavailable, stale, out-of-horizon or unassignable evidence must be explicit and neutral. Confirmed reservation conflicts remain a hard review gate, and itinerary changes remain user-approved.

The Start checkpoint changes documentation and tracker state only. It does not change recommendation behavior, the October 9–16, 2027 plan, saved/shared data, production state, credentials/devices, schema, dependencies/runtime, deployment configuration or family-key state.

## Known rebaseline findings still requiring remediation

### High priority

- The ride-refresh endpoint remains a public GET even though 2A now rate-limits/serializes the expensive work.

### Important hardening/maintainability

- 5B moved acknowledged device credentials out of long-term browser `localStorage`; a legacy raw record is retained only until protected-cookie migration is acknowledged. Remaining dynamic `innerHTML` usage elsewhere is still general XSS/maintainability debt.
- Frontend behavior relies in several places on imperative DOM patching and polling rather than shared React state.
- Section 4 broadened automated regression coverage across core park-planning, trip-planning, safety, sync/account and mobile-browser behavior; production functional smoke verification and future feature-specific contracts remain separate work.
- Legacy scaffold code remains beside production code and needs cleanup or explicit archiving.
- Legacy `core_app.py` still initializes Flask-CORS globally; Section 2D safely enforces the effective narrowed browser policy at the production boundary, but eventual core cleanup remains maintainability debt.
- The obsolete `castlewatch-2027` Vercel project integration can still report failures for frontend commits even when the real `castlewatch-frontend` project is healthy; deployment integration cleanup remains future hygiene work.
- Both repositories are public while personal trip dates and itinerary assumptions are encoded in source; repository privacy/config separation should be decided explicitly.

## Where development stopped before the rebaseline

The most recent pre-rebaseline development thread was the Accounts / Invitations / Device Management migration and production verification work. The frontend production-verification issue for the Family devices panel remained open. The prior Trip Week Phase 2 plan is no longer a clean "next feature" because the decision engine already exists in partial form.

## Current development phase

**Trip Week Phase 2 - Section 8 started**

Sections 1–7 are complete. Section 8's bounded 8A–8D delivery contract is open, but no implementation batch has started. Keep `CASTLEWATCH_FAMILY_KEY` configured and enabled; no later retirement option is authorized without a separate explicit user approval.

## Exact next priorities

1. **Run `Start Section 8A` to begin the typed evidence and scoring contract.**
2. Preserve the existing recommendation outcomes and manual approval boundary while establishing explicit neutral behavior for unusable signals.

See `ROADMAP.md` for the broader order and `ARCHITECTURE.md` for system boundaries.
