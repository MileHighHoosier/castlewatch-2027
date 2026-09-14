# Reservation Awareness Phase 2B checkpoint (CW-018)

**Status:** Complete, production-verified and finalized September 13, 2026. Phase 2C subsequently started under the separately authorized [CW-019 checkpoint](reservation-awareness-phase-2c.md).

**Tracker:** backend issue [#93](https://github.com/MileHighHoosier/castlewatch-2027/issues/93) under parent issue [#85](https://github.com/MileHighHoosier/castlewatch-2027/issues/85), frontend PR [#58](https://github.com/MileHighHoosier/castlewatch-frontend/pull/58), and documentation PR [#94](https://github.com/MileHighHoosier/castlewatch-2027/pull/94).

## Verified baseline

- Backend `main`: `1bb1df39ffe42ce5a7f75fa0c400f8d7e93db90f` (finalized CW-017 documentation).
- Frontend `main`: `977778c82ac9c6811ca0ad9c88139e77a291b925` (finalized CW-017 implementation).
- Local documentation branch: `docs/cw-018-reservation-awareness-phase-2b`.
- Local frontend branch: `feat/cw-018-reservation-awareness-phase-2b`.
- CW-017 is complete, production-verified and finalized.

## Authorized scope

Phase 2B adds only the user-facing frontend planner over the Phase 2A contract:

- a prioritized timeline for Bibbidi Bobbidi Boutique, Cinderella's Royal Table, 1900 Park Fare, lightsaber building, tours and user-defined targets;
- deterministic opening, optional deadline and countdown/readiness presentation;
- explicit rule source, source URL, as-of date, verification state, assumptions and manual-override labels;
- user-controlled target creation and edits to title, type, priority, desired planning date, rule metadata, manual dates and notes;
- a mobile-readable 390×844 interaction surface;
- lossless local/shared booking-target compatibility and fail-closed handling for malformed raw target data.

No official booking-policy defaults are added. A named quick-add target begins with no booking rule and no date; the family must add verified inputs or a labeled manual override.

## Acceptance checklist

- [x] Exact backend and frontend remote `main` baselines were verified before branching.
- [x] CW-018 issue #93 and isolated local branches were established.
- [x] Named and custom target controls create booking targets only, with no policy defaults.
- [x] Timeline ordering is priority-first and deterministic within each priority.
- [x] Opening, open-window, deadline and passed-deadline boundary states use date-only comparisons.
- [x] Missing, unverified, unavailable, malformed or inconsistent rule/override inputs remain explicit and neutral.
- [x] A newly quick-added target with missing inputs shows the neutral `Date needed` state.
- [x] A labeled manual opening date remains actionable when the desired trip date and optional deadline are absent.
- [x] Source-only rule metadata does not invalidate that labeled manual opening date.
- [x] Missing-input handling does not suppress genuine inconsistent-rule warnings.
- [x] A common exclusive Web Lock covers the complete planner read/validate/change/save operation, so overlapping participating tabs preserve other valid targets.
- [x] Malformed/future-format raw storage arriving while a write waits is preserved without running the mutation.
- [x] Deterministic read/save interleavings and rendered two-tab add/edit/clear-rule/clear-overrides/remove actions are covered in both queue orders.
- [x] Missing-lock/write/callback failures fail closed; explicit shared download/restore coordinate with planner writes without changing payload or authorization semantics.
- [x] Source, as-of date, verification and manual-override provenance are visible.
- [x] Planner source is declarative and has no reservation, itinerary, resort or approval mutation path.
- [x] Existing exact valid/malformed/absent shared booking-target payload behavior remains unchanged.
- [x] Focused Phase 2A/2B contracts pass.
- [x] Full frontend contracts pass.
- [x] Next.js production build and TypeScript validation pass.
- [x] Rendered 390×844 mobile and multi-tab smoke pass in exact-head CI; local Chrome is unavailable and is not claimed as a local pass.
- [x] Backend tracker validation and unchanged backend contracts pass.
- [x] Both local branches are committed with review-ready evidence.
- [x] Separate user authorization was received before publishing both branches and opening review pull requests.
- [x] Corrected frontend exact-head CI, including the Node 22 mobile smoke, and the authoritative `castlewatch-frontend` preview pass.
- [x] Independent review confirms PR #94's current-head CI using its post-publication PR evidence/checks, not a self-referential SHA in this commit.
- [x] Independent review accepts the overlapping-write correction and cooperative-lock rollout boundary.
- [x] Separate Finalize authorization is received before any merge or deployment.

## Preserved boundaries

- Booking targets never create, edit, confirm or delete reservations.
- Phase 2B does not expose the Phase 2C attempted/booked/unavailable/backup workflow.
- No booking target changes itinerary order, park assignments, resorts or recommendation approval.
- Family-key recovery and `legacy_family_key_enabled` remain unchanged and enabled.
- No backend API, persistence schema, dependency/runtime, production/shared data, credential/device or hosting configuration change is included.
- The obsolete `castlewatch-2027` Vercel project is not altered.
- Phase 2C remained paused throughout CW-018; it later started under CW-019. Phase 2D remains paused.

## Overlapping-write protocol and compatibility

The previous latest-storage helper fixed sequential stale tabs but left a read-modify-write race. The correction uses the origin-scoped exclusive Web Lock `castlewatch.booking-targets.v1.write` before reading storage; validation, operation and save run within the same critical section. Pending operations therefore observe the preceding write, not their component's stale array. No localStorage lock fallback or new serialized field is introduced.

All current application target-writing entry points participate: planner mutations, explicit shared download, and history restore. Shared replacements remain intentional, user-authorized replacements with the existing authorization/version checks; their synchronous Phase 2A raw helpers and payload serialization remain unchanged. A planner operation queued behind a malformed/future-format replacement refuses to overwrite it. Unsupported Web Locks fails closed before a write (including before remote history restore). Write/callback errors release the lock.

UI event values and newly generated IDs are captured before queueing. Optimistic planner drafts are display-only, not saved arrays; completion/failure, storage events and focus reconcile to valid stored state. Malformed storage clears editable cards and blocks writes.

**Cooperative boundary:** Web Locks coordinate participating writers, not arbitrary external localStorage edits or old app tabs that lack this protocol. Reload/close old pre-correction tabs before any later authorized rollout, and require future application writers to use the same lock. No production data or shared restore was exercised during verification.

## Validation evidence

- Authorized correction parents: frontend `506aa5d49f08a7b6ce49b276599bd8bed57e0352`; backend documentation `6b3bcbc6a92a48288d62c1728dedd5c899026165`. Only the existing PR branches are updated.
- New frontend PR #58 head: `06cf358ae762aa6963540f246435088531884b8c`.
- Focused Phase 2A/2B contracts: **22 passed**. Deterministic fixtures request a second write after the first read but before its save for add/edit/clear/remove; queued malformed/future payloads, unknown-field preservation, missing locks, write failure and callback failure are covered.
- Full frontend contracts: **172 passed**.
- Next.js 16.2.6 production build and TypeScript validation: **passed**. No dependency/runtime manifest changes.
- Local browser execution could not start because Chrome was missing; the attempted temporary browser download timed out. This is not recorded as a smoke pass.
- Exact-head Node 22 [CI run 34738798725](https://github.com/MileHighHoosier/castlewatch-frontend/actions/runs/34738798725), job `103674840729`: **passed**, including 172 contracts, build and 390×844 mobile smoke. The checked-out PR merge tree `5a2aef3726f0eaf1b37b4ae6148e9e6fce313ef9` equals the reviewed head tree.
- The rendered smoke confirms existing quick-add/source-only/manual-opening readiness transitions, then real Web Locks across two pages: **10 ordered action pairs** (add, edit, clear rule, clear overrides, remove versus a second-tab add, both queue orders) and **3 malformed/future-storage interleavings**. It checks queue contention, captured event values, preserved unrelated targets, final stored data, both rendered collections and error rollback.
- Current authoritative [preview](https://vercel.com/castlewatch/castlewatch-frontend/Bj7ERvuRgvVamtosLH765x5QmqkJ): `dpl_Bj7ERvuRgvVamtosLH765x5QmqkJ`, **READY**, project `prj_9mB5vAdSO9g0UoFZNbNIWIDksHWN`, team `castlewatch`. Vercel metadata confirms the full new frontend head, PR #58 and existing feature branch.
- Backend tracker validator: **passed (13 active/future tasks)**. Full backend contracts: **102 passed locally**. PR #94 records this documentation revision's resulting SHA and exact-head backend CI after publication. Backend application code is unchanged; only documentation and tracker assertions are updated.
- Before rollout, the user confirmed that all old CastleWatch tabs were closed on every browser and device.

## Finalize and production evidence

- Backend documentation PR [#94](https://github.com/MileHighHoosier/castlewatch-2027/pull/94) remained at reviewed head `ed003304e07c824484fa0e3a24d23a15d3fd4703` and merged first as `5386c72780952e14a001ef08169dece8841f2e73`.
- Post-merge backend CI run [34762130384](https://github.com/MileHighHoosier/castlewatch-2027/actions/runs/34762130384) passed. Railway deployment `ea178cea-74bc-4736-a931-b760e64b05f3` succeeded for the exact merge.
- Production backend `/health`, root, `/api/trip-week` and `/api/rides` reads returned HTTP 200. Unauthenticated `/api/family-trip` returned the expected HTTP 401 without mutation.
- Frontend PR [#58](https://github.com/MileHighHoosier/castlewatch-frontend/pull/58) remained at reviewed head `06cf358ae762aa6963540f246435088531884b8c` and merged second as `a82ddaa2628cf139e35c2a917b0033a2e18b81e3`.
- Post-merge frontend CI run [34762232352](https://github.com/MileHighHoosier/castlewatch-frontend/actions/runs/34762232352) passed all 172 contracts, the production build, 390×844 mobile smoke, 10 ordered rendered two-tab action pairs and 3 malformed/future-storage interleavings.
- The authoritative `castlewatch-frontend` production deployment `dpl_HKRRybeDZTirzQF4imS93pdBupmx` reported Ready for the exact frontend merge. The canonical CastleWatch and Operations pages returned HTTP 200, exposed the Booking Planner navigation/read-only Operations surface and retained the configured Railway backend; live `/api/rides` data returned HTTP 200.
- No shared-plan, booking-target, itinerary, reservation, resort, recommendation, credential/device, family-key, database-schema, dependency/runtime or hosting-configuration data was changed. The obsolete secondary Vercel project remained untouched.

### Historical evidence (not current-head gates)

- Initial `d5a4e260...` and `bace8bef...` reviews led to quick-add neutrality and optional-date/manual-opening corrections. Later readiness fixes cover source-only metadata, genuine inconsistent rules and invalid dates without changing Phase 2A calculation/storage semantics.
- Intermediate smoke runs `34423681014` and `34423886060` failed in harness timing/escaping assertions. Those defects were corrected before `da1f46036246b4adbe959db55d51da21be99d65a`, whose run `34424110389` passed; its Ready preview is `dpl_ApHswspkRF19h7v3nwk85ck8fa3Y`.
- Sequential stale-write head `506aa5d49f08a7b6ce49b276599bd8bed57e0352` passed 19 focused/169 full tests, run `34488901427` and Ready preview `dpl_2u2JCL2VjgwzxLpcTMK7QgFziBrC`; these did not prove overlapping-write safety. New evidence above supersedes them.
- Backend predecessor `6b3bcbc6a92a48288d62c1728dedd5c899026165` passed run `34489992135`; it is not evidence for the new documentation head.
- The obsolete secondary `castlewatch-2027` project's nonexistent `website` root remains a separate known configuration issue; it was not altered.

## Stop rules

- Stop on a regression in reservation/shared-sync compatibility, malformed raw-payload preservation, family-key recovery or manual itinerary controls.
- Stop if the planner would need an invented official booking rule or a backend/schema change.
- Do not publish, open pull requests, merge or deploy without the corresponding separate user authorization.

## Historical handoff

`Start Reservation Awareness Phase 2C`

The user later authorized this command and CW-019 now owns the active handoff. Follow the canonical tracker and [Phase 2C checkpoint](reservation-awareness-phase-2c.md); keep Phase 2D paused.
