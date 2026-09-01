# CastleWatch Roadmap

_Last rebaseline: August 2026_

This roadmap supersedes older chat-only progress estimates. It should be updated when a phase is finalized.

## Current phase: Product roadmap development

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

Status: **Complete - production-deployed August 24, 2026**

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
- **4C - transportation/reservation and Lightning Lane contracts: Complete and production-deployed August 24, 2026.** Fourteen focused frontend contracts now protect the approved trip/split-stay defaults, reservation transportation and conservative leave-by guidance, Getting There bus projections, reservation conflict/overlap/transfer boundaries, malformed Lightning Lane windows, deterministic Lightning Lane status/urgency/conflict/next-selection guidance, and safe ride-name rendering. The split-stay defaults were corrected so October 12-14 use Beach Club. Exact-head Node 22 CI passed clean installation, all 51 frontend tests and the production Next.js build; frontend PR #35 was squash-merged at `94e3f4aa944c6ecde6aac5c0667c78df45ec8721`; the real `castlewatch-frontend` production Vercel deployment succeeded. No backend, dependency, account/family-key, park-order or automatic itinerary change was included.
- **4D - Park Command Center, Live Plan and emergency-mode contracts: Complete and production-deployed August 24, 2026.** Nineteen focused frontend contracts now protect Park Command Center normalization, live/closed/non-ride behavior, heat pressure and rope-drop ordering; Live Plan modes, wait-cap fallback, historical-signal safety, completed-ride filtering and replacement explanations; and all four park emergency plans, conservative fallback, weather precedence and explicit activation. QC also corrected the active emergency overlay so park or heat/storm changes cannot leave stale guidance visible. Exact-head Node 22 CI passed clean installation, all 70 frontend tests and the production Next.js build; frontend PR #36 was squash-merged at `8ad963a61c65e0f9f90e9635ecf5406ac7e41491`; the real `castlewatch-frontend` Vercel production deployment succeeded. No backend, itinerary, dependency/runtime, account/family-key, reservation, park-order, shows/activities/characters or 4E E2E work was included.
- **4E - shows/activities/characters plus the smallest practical mobile browser/E2E suite: Complete and production-deployed August 24, 2026.** Twelve focused frontend contracts now protect show schedule parsing/sorting/past-state, WDW source filtering, show/character separation, activity eligibility/badges/use cases/order and text-safe names. QC centralized true meet-and-greet classification, kept character-themed activities such as Enchanted Tales with Belle under Activities, excluded timed stage shows from ride-demand planning, filtered past-only shows and unrelated Orlando content, and stabilized the six-button mobile layout with an explicit device-width viewport. Exact-head Node 22 CI passed clean installation, all 82 frontend tests, the production Next.js build and a dependency-free 390×844 Chrome smoke through navigation, Activities, timed showtimes, Characters, Epcot switching and zero horizontal overflow; frontend PR #37 was squash-merged at `53830cc16c33ebf4bdc4058fe994c15f290c80ae`; the real `castlewatch-frontend` preview and merged production Vercel deployments succeeded. No backend product code, dependency/lockfile/runtime, itinerary, reservation, park-order, account/family-key, database or 4F work was included.
- **4F - full regression/build review and Section 4 closeout: Complete and production-deployed August 24, 2026.** Exact-head Python 3.12.14 CI installed the pinned backend requirements, passed all 69 contracts and compiled every active root production module; QC replaced the partial compile list and made live-planning UTC hour/timestamp generation consistent. Exact-head Node 22 CI completed clean `npm ci`, passed all 82 frontend contracts, built the production app and passed the dependency-free 390×844 Chrome smoke. Backend PR #42 merged at `1db9c1ac6e00d3555eda9a000b94b9dc67a63aed` and Railway succeeded; frontend PR #38 merged at `416e8d0deb3c4740f046dd0afa6f9cfe0377cca3` and the real frontend Vercel production deployment succeeded. No dependency/runtime version, itinerary, reservation, account/family-key, database or Section 5 work was included.

### Section 5 - Accounts / invitations / device migration completion

Status: **Complete - production-verified August 29, 2026**

Current recommendation: **finish the migration rather than abandon it**, because much of the foundation already exists.

Implementation batches:

- **5A - architecture audit and migration contract: Complete and production-deployed August 24, 2026.** The deployed backend/frontend foundation was reconciled with backend issue #10 and frontend issue #25; already-completed account gates were inventoried; ten remaining migration gaps and the target authorization matrix were recorded; and owner-bootstrap, protected credential, role, recovery, pepper-continuity and non-retirement boundaries were fixed in `docs/accounts_migration_contract.md`. Exact-head Python 3.12.14 CI passed clean installation, all 69 backend contracts and full production-module compilation; the audited frontend head passed all 82 contracts and its production build. Backend PR #44 was squash-merged at `8d970cfff75d6b859e3b242f5d0b0d312d0151c5`, and Railway succeeded. No production code, schema, data, credential, dependency, runtime, itinerary, account state or frontend behavior changed.
- **5B - owner-device bootstrap and protected credential foundation: Complete and production-deployed August 24, 2026.** Backend owner bootstrap is an explicit family-key-only action tied to the seeded owner member, prevents a second active owner device, permits replacement only after revocation and leaves the legacy-key flag enabled. The frontend proxy now keeps acknowledged device credentials in a narrow `Secure`, `HttpOnly`, `SameSite=Strict` cookie, strips one-time credentials before browser JavaScript receives setup responses, migrates legacy local credentials only after server acknowledgment and requires explicit credential selection without silent fallback. Exact-head CI passed clean Python 3.12.14 installation, all 79 backend contracts and compilation plus clean Node 22 installation, all 90 frontend contracts, production build and mobile browser smoke. Backend PR #46 merged at `5456a272041f2d329b26ff7cd4b1a338e8960d51` and Railway succeeded; frontend PR #39 merged at `c7b2159d7774ce6d01682626f71da4a2f2dc5dfb` and the real frontend Vercel production deployment succeeded. No production owner-device record, schema/data, dependency/runtime, itinerary or normal shared-plan authorization change was included, and the family key remains configured and enabled.
- **5C - normal shared-plan dual authorization and role enforcement: Complete and production-deployed August 24, 2026.** Normal shared-plan read, history, history-version, write, restore and Operations routes now authorize exactly one selected family key or protected device credential. The backend enforces Owner/Editor read-write-restore-Operations access and Viewer read/history-only access inside the existing transaction boundary; one typed frontend authorization layer applies the same controls across manual sync, guarded autosave, history/restore and Operations without trusting browser role metadata or silently falling back. Exact-head CI passed clean Python 3.12.14 installation, all 82 backend contracts and compilation plus clean Node 22 installation, all 99 frontend contracts, production build and mobile browser smoke. Backend PR #48 merged at `d8b7fa630cbd2a20a77044b04c5d1f3ae9565918` and Railway succeeded; frontend PR #40 merged at `283b0da71b4a540c74e09360d5b599b8ecc57086` and the real `castlewatch-frontend` Vercel production deployment succeeded. No production device was created and no schema/data, dependency/runtime, itinerary, legacy-key flag, pepper, last-owner or family-key recovery change occurred.
- **5D - revocation, recovery and legacy-gate hardening: Complete and production-deployed August 24, 2026.** Every family-key authorization path now reads the authoritative `legacy_family_key_enabled` value while production remains enabled; revoked device credentials are denied across device management and shared-plan read/history/version/write/restore/Operations without mutation or fallback. Owner-device revocation is serialized and restricted to explicit family-key recovery, followed by replacement bootstrap. New credentials use the primary pepper while active credentials and open invites can transition through a previous pepper or the family-key compatibility source and rehash on successful use. A selected protected-cookie `401` now clears the cookie and safe device metadata and leaves an explicit disconnected selection instead of silently using a saved family key. Recovery/rollback guidance was updated. Exact-head CI passed clean Python 3.12.14 installation, all 90 backend contracts and full production-module compilation plus clean Node 22 installation, all 104 frontend contracts, the production build and mobile browser smoke. Backend PR #50 merged at `79094f56af9b8d0be18fae6e518365d6775bd35a` and Railway succeeded; frontend PR #41 merged at `f591f5b140e5ca0654f04a1433963d7ba560bd71` and the real `castlewatch-frontend` Vercel production deployment succeeded. No production device, secret or pepper environment value, legacy-key flag value, schema/data, dependency/runtime, itinerary or retirement behavior changed; the family key remains configured and enabled.
- **5E - production two-device verification and Section 5 closeout: Complete and production-verified August 29, 2026.** Frontend PRs #42–#44 supplied the isolated self-rename, explicit family-key recovery-selection and confirmed content-identical backup controls needed for the live run. A protected production Owner persisted; a second real browser/phone with no family key passed Editor and Viewer role boundaries, history/restore/Operations controls, self-rename, Owner-managed revocation and clean rejected-cookie cleanup without fallback. Append-only history remained intact through shared version 17, the October 9–16 trip profile and manual recommendation control remained unchanged, temporary devices were revoked, and Railway plus the authoritative frontend Vercel deployment remained green. The family key and production legacy-key flag remain enabled.

Section 5 verified the technical prerequisites below; legacy family-key retirement still requires a separate explicit user approval:

- normal shared-plan endpoints accept the intended device-token model,
- owner-device bootstrap exists,
- Editor/Viewer permissions are regression-tested,
- revocation/recovery behavior is proven,
- production two-device verification passes,
- the user explicitly approves any future retirement option.

Until then: **do not remove or disable `CASTLEWATCH_FAMILY_KEY`.**

### Section 6 - Production smoke verification

Status: **Complete — production-verified August 31, 2026**

Verify the deployed Vercel/Railway system across critical flows and close or update production-verification issues.

Implementation batches:

- **6A - production baseline and smoke contract: Complete August 30, 2026.** Exact production heads, CI/deployments, live frontend/backend health, protected-endpoint failure safety and the invariant baseline passed. A fresh trusted-Owner browser check confirmed shared version 17 remains up to date under the protected Owner credential. No production data, credential, code, dependency/runtime, schema, itinerary, reservation, device record or family-key setting changed.
- **6B - core website flows: Complete and finalized August 30, 2026.** Navigation, all four park dashboards, live/open and closed-attraction behavior, update/source context, historical directional planning, current weather reliability plus conservative temporary guards, Shows/Activities/Characters, all three Live Plan modes, temporary browser-local Lightning Lane guidance and temporary emergency mode passed in production. Frontend PRs [#47](https://github.com/MileHighHoosier/castlewatch-frontend/pull/47) and [#49](https://github.com/MileHighHoosier/castlewatch-frontend/pull/49) repaired the two discovered defects through exact Node 22 CI, production builds, mobile browser smoke, authoritative Vercel deployment and repeated production checks. Temporary state was restored, and no server-side production/shared-plan/credential/device/itinerary/reservation/family-key state changed. Trip Week/shared-plan work completed in 6C; mobile/failure-state closeout remains in 6D.
- **6C - Trip Week and shared-plan flows: Complete and finalized August 30, 2026.** The approved Trip Week profile, zero-booking reservation baseline, saved Base plan and resorts, trip-day/resort-aware Getting There guidance, unified recommendation reasoning and manual approval boundaries, protected Owner shared version 17 connection, retained history/provenance and existing role evidence passed production verification. Section 5E content-identical backup evidence was reused, no new defect was found and no production/shared-plan/profile/itinerary/reservation/resort/recommendation/credential/device/family-key mutation occurred. Mobile/failure-state closeout remains in 6D.
- **6D - mobile, failure-state and Section 6 closeout: Complete and finalized August 31, 2026.** The 390×844 mobile layout, touch targets, sticky navigation, critical park/Trip Week/Getting There/shared-plan paths, role-appropriate confirmation/read-only/unavailable states and isolated failure/recovery behavior passed. Backend gates passed 90 contracts and compilation; frontend gates passed 114 contracts under Node 22, production build and mobile smoke. Frontend issue [#50](https://github.com/MileHighHoosier/castlewatch-frontend/issues/50) was repaired and production-verified through PR [#51](https://github.com/MileHighHoosier/castlewatch-frontend/pull/51). No production/shared-plan/trip/account/credential/device/dependency/runtime/schema/family-key state changed, and Section 6 is closed.

The governing checklist is `docs/section-6-production-smoke.md`, and backend issue #53 is the live tracker. Each batch requires its own Start and Finalize checkpoint.

### Section 7 - Lightweight project tracker

Status: **Complete and finalized August 31, 2026**

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

Canonical `PROJECT_TRACKER.md` now manages backend, frontend, known rebaseline and roadmap work while completed Sections 1–7 remain summarized. The tracker defines explicit status/QC vocabularies and Start/checklist/defect/Finalize maintenance rules; its fresh-agent handoff identifies the current phase, blocker and exact next command. `scripts/validate_project_tracker.py` plus focused tests enforce its schema, IDs, vocabulary, dependencies, dates, next actions and credential-safety boundary. The governing contract is `docs/section-7-project-tracker.md`, and backend issue [#61](https://github.com/MileHighHoosier/castlewatch-2027/issues/61) records the completed checklist. Section 7 closed without starting Section 8 or changing production/product/data/credential/device/dependency/runtime/schema/family-key state.

### Section 8 - Resume product development

Status: **Complete — production-verified and finalized September 1, 2026**

Complete **Trip Week Phase 2 - Unified Recommendation Engine** rather than restarting it.

The existing engine already uses event, reservation, resort/transportation and historical crowd signals. Remaining work should integrate missing signals and replace broad heuristics where justified while keeping itinerary changes user-approved.

The bounded delivery contract is recorded in `docs/section-8-trip-week-phase-2.md` and backend issue [#66](https://github.com/MileHighHoosier/castlewatch-2027/issues/66):

- **8A:** typed evidence and scoring contract with neutral unusable-signal behavior and current-outcome regression baselines;
- **8B:** reservation and no-park-hopping preservation plus one Getting There-aligned transportation model;
- **8C:** horizon/freshness-aware weather and date/park-assignable Lightning Lane constraints;
- **8D:** decision explainability, manual-control preservation and coordinated release verification.

The Start checkpoint changes documentation and work state only. It does not change recommendation logic, the itinerary, saved/shared data, production state, credentials/devices, schema, dependencies/runtime, deployment configuration or family-key state.

Section 8A frontend PR [#52](https://github.com/MileHighHoosier/castlewatch-frontend/pull/52) added a typed, source-owned evidence contract and made scenario totals derive from those contributions. Unavailable, stale, out-of-horizon, non-assignable and non-finite evidence is deterministically neutral. Direct fixtures preserve keep/swap/wait/review, reservation and no-park-hopping behavior. The separate [Section 8A test checklist](docs/section-8a-test-checklist.md) passed before the user authorized Finalize. Section 8A is complete.

Section 8B frontend PR [#53](https://github.com/MileHighHoosier/castlewatch-frontend/pull/53) replaced duplicated broad transportation assumptions with one reusable route/timing model shared by Getting There, reservation leave-by guidance and Trip Week scenario scoring. Only routes assignable to the scenario park date and previous-night resort contribute; unknown origins remain explicit and neutral. Base/alternate split-stay, reservation and resort-transfer regressions accompany the preserved confirmed-booking/no-hopping/manual-control gates. The separate [Section 8B test checklist](docs/section-8b-test-checklist.md) passed frontend/backend/mobile gates and read-only production verification before the user separately authorized Finalize. Section 8B is complete.

Section 8C frontend PR [#54](https://github.com/MileHighHoosier/castlewatch-frontend/pull/54) added a seven-day trustworthy weather horizon, six-hour automatic freshness enforcement and date/park-assignable Lightning Lane constraints. Unavailable, stale, out-of-horizon, legacy-unassigned and otherwise unusable signals remain explicit and neutral. New trip-day Lightning Lane saves carry the active park and current date. Usable evidence joins scenario totals/readiness while current recommendation outcomes and manual approval stay regression-protected. The separate [Section 8C test checklist](docs/section-8c-test-checklist.md) passed 134 frontend contracts, production build, exact-head mobile CI, backend tracker/compile gates and read-only production verification before the user separately authorized Finalize. Section 8C is complete.

Section 8D frontend PR [#55](https://github.com/MileHighHoosier/castlewatch-frontend/pull/55) added the bounded user-facing explainability layer: scenario evidence is grouped by category and names score contribution, usability state, provenance and date/park context; affected reservations are explicit; and the card states that itinerary changes are never automatic. Apply, undo, lock and unlock behavior is unchanged. The [Section 8D checklist](docs/section-8d-test-checklist.md) passed 138 frontend contracts, the production build, exact-head Node 22/mobile CI, backend contracts/compilation, tracker gates, successful Vercel/Railway deployment statuses and read-only mobile screenshots of the score/control surface plus expanded Base and alternate evidence. The user separately authorized Section 8D Finalize and then parent Section 8 Finalize. Section 8 is complete; the exact next command is `Start Reservation Awareness Phase 2`.

---

## Product roadmap after stabilization

### 1. Complete Trip Week Phase 2

Status: **Complete — production-verified and finalized September 1, 2026**

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

Status: **Not started — exact next command is `Start Reservation Awareness Phase 2`**

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
