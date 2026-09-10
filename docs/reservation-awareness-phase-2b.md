# Reservation Awareness Phase 2B checkpoint (CW-018)

**Status:** Implemented with the stale-write correction published after independent review September 10, 2026. Final frontend exact-head CI and the authoritative preview pass; this documentation evidence requires its own exact-head CI before renewed independent readiness review. Merge and deployment are not authorized.

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
- [x] Planner actions apply to the latest valid stored target collection so a stale tab preserves valid targets added elsewhere.
- [x] Source, as-of date, verification and manual-override provenance are visible.
- [x] Planner source is declarative and has no reservation, itinerary, resort or approval mutation path.
- [x] Existing exact valid/malformed/absent shared booking-target payload behavior remains unchanged.
- [x] Focused Phase 2A/2B contracts pass.
- [x] Full frontend contracts pass.
- [x] Next.js production build and TypeScript validation pass.
- [x] Local 390×844 mobile browser smoke is updated; this runner has no supported Chrome executable, so execution remains an exact-head CI gate after publication.
- [x] Backend tracker validation and unchanged backend contracts pass.
- [x] Both local branches are committed with review-ready evidence.
- [x] Separate user authorization was received before publishing both branches and opening review pull requests.
- [x] Corrected frontend exact-head CI, including the Node 22 mobile smoke, and the authoritative `castlewatch-frontend` preview pass.
- [ ] This final documentation evidence passes PR #94 exact-head CI after publication.
- [ ] Separate Finalize authorization is received before any merge or deployment.

## Preserved boundaries

- Booking targets never create, edit, confirm or delete reservations.
- Phase 2B does not expose the Phase 2C attempted/booked/unavailable/backup workflow.
- No booking target changes itinerary order, park assignments, resorts or recommendation approval.
- Family-key recovery and `legacy_family_key_enabled` remain unchanged and enabled.
- No backend API, persistence schema, dependency/runtime, production/shared data, credential/device or hosting configuration change is included.
- The obsolete `castlewatch-2027` Vercel project is not altered.
- Phase 2C and Phase 2D remain paused.

## Local validation evidence

- Initial frontend review head: `d5a4e26045fb270d7b0ae8c51a1e8fc5a3a60706`; first corrected head: `bace8bef57181c89363ef292618411f0df46a839`.
- Initial exact-head review corrected missing quick-add neutrality and a manual opening without optional deadline/trip date. Independent post-correction review found that source-only metadata could still invalidate the manual opening and missing-input shortcuts could hide genuinely inconsistent rules.
- The readiness correction remained isolated to Phase 2B presentation plus focused/rendered tests. A later independent review found that planner actions committed stale component state and could erase a valid target added in another tab.
- The bounded storage correction applies each planner operation to the latest valid stored collection before saving and retains malformed-storage write protection. The finalized Phase 2A serialized shape, calculation behavior and shared-sync contract remain unchanged.
- Corrected frontend PR #58 head: `506aa5d49f08a7b6ce49b276599bd8bed57e0352`.
- Focused Phase 2A/2B contracts: **19 passed**, including the new multi-tab/storage regression.
- Full frontend contracts: **169 passed**.
- Next.js 16.2.6 production build and TypeScript validation: **passed**.
- Local 390×844 mobile browser smoke remains unavailable because this runner has no supported Chrome binary. Exact-head runs `34423681014` and `34423886060` exposed timing and escaping defects only in the newly expanded smoke assertion while the contracts and production build passed; both harness defects were corrected.
- Reviewed predecessor head `da1f46036246b4adbe959db55d51da21be99d65a` passed Node 22 CI run `34424110389`, including rendered quick-add, source-only and manual-opening transitions at 390×844. Its authoritative Ready preview was `dpl_ApHswspkRF19h7v3nwk85ck8fa3Y`.
- Corrected exact-head Node 22 CI run `34488901427`: **passed**, including all 169 contracts, the production build and rendered 390×844 mobile smoke.
- Corrected authoritative `castlewatch-frontend` preview deployment `dpl_2u2JCL2VjgwzxLpcTMK7QgFziBrC`: **Ready**.
- The obsolete `castlewatch-2027` Vercel failure remains the known nonexistent `website` root configuration and was not altered.
- Backend tracker validator: **passed** with 13 active/future tasks.
- Full unchanged backend contracts: **102 passed** using the exact pinned requirements.
- No production or shared-plan write was performed.

## Stop rules

- Stop on a regression in reservation/shared-sync compatibility, malformed raw-payload preservation, family-key recovery or manual itinerary controls.
- Stop if the planner would need an invented official booking rule or a backend/schema change.
- Do not publish, open pull requests, merge or deploy without the corresponding separate user authorization.

## Exact next action

Publish this final evidence update to documentation PR #94 and require its exact-head backend CI to pass. Stop on failure and otherwise stop for renewed independent review of both exact heads. Only after that review approves readiness may separate `Finalize Reservation Awareness Phase 2B` authorization be requested. Do not begin Phase 2C or Phase 2D.
