# Reservation Awareness Phase 2B checkpoint (CW-018)

**Status:** Implemented and locally verified September 9, 2026; awaiting separate authorization to publish branches and open review pull requests. Merge and deployment are not authorized.

**Tracker:** backend issue [#93](https://github.com/MileHighHoosier/castlewatch-2027/issues/93) under parent issue [#85](https://github.com/MileHighHoosier/castlewatch-2027/issues/85).

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
- [x] Source, as-of date, verification and manual-override provenance are visible.
- [x] Planner source is declarative and has no reservation, itinerary, resort or approval mutation path.
- [x] Existing exact valid/malformed/absent shared booking-target payload behavior remains unchanged.
- [x] Focused Phase 2A/2B contracts pass.
- [x] Full frontend contracts pass.
- [x] Next.js production build and TypeScript validation pass.
- [x] Local 390×844 mobile browser smoke is updated; this runner has no supported Chrome executable, so execution remains an exact-head CI gate after publication.
- [x] Backend tracker validation and unchanged backend contracts pass.
- [x] Both local branches are committed with review-ready evidence.
- [ ] Separate user authorization is received before publishing either branch or opening review pull requests.

## Preserved boundaries

- Booking targets never create, edit, confirm or delete reservations.
- Phase 2B does not expose the Phase 2C attempted/booked/unavailable/backup workflow.
- No booking target changes itinerary order, park assignments, resorts or recommendation approval.
- Family-key recovery and `legacy_family_key_enabled` remain unchanged and enabled.
- No backend API, persistence schema, dependency/runtime, production/shared data, credential/device or hosting configuration change is included.
- The obsolete `castlewatch-2027` Vercel project is not altered.
- Phase 2C and Phase 2D remain paused.

## Local validation evidence

- Frontend implementation commit: `e79a81c4018dc534eef7453f18ef92cdb68bde83` on local branch `feat/cw-018-reservation-awareness-phase-2b`.
- Focused Phase 2A/2B contracts: **13 passed**.
- Full frontend contracts: **163 passed**.
- Next.js 16.2.6 production build and TypeScript validation: **passed**.
- Updated 390×844 mobile browser smoke: **not executable locally** because this runner has no supported Chrome binary; the test remains mandatory in exact-head CI after publication.
- Backend tracker validator: **passed** with 13 active/future tasks.
- Full unchanged backend contracts: **102 passed** using the exact pinned requirements.
- No production or shared-plan write was performed.

## Stop rules

- Stop on a regression in reservation/shared-sync compatibility, malformed raw-payload preservation, family-key recovery or manual itinerary controls.
- Stop if the planner would need an invented official booking rule or a backend/schema change.
- Do not publish, open pull requests, merge or deploy without the corresponding separate user authorization.

## Exact next action

Local acceptance evidence is complete. To publish both branches and open review pull requests, the user must separately authorize:

`I approve publishing both CW-018 branches to the configured GitHub repositories and opening review pull requests. Do not merge or deploy.`

Do not begin Phase 2C or Phase 2D.
