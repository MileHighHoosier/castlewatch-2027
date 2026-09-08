# Reservation Awareness Phase 2A checkpoint (CW-017)

**Status:** Active; bounded implementation is published for review.

**Tracker:** backend issue [#90](https://github.com/MileHighHoosier/castlewatch-2027/issues/90) under parent issue [#85](https://github.com/MileHighHoosier/castlewatch-2027/issues/85), with implementation PR [#57](https://github.com/MileHighHoosier/castlewatch-frontend/pull/57) and documentation PR [#91](https://github.com/MileHighHoosier/castlewatch-2027/pull/91).

## Verified baseline

- Backend `main`: `093e7f30c2777c4959984e6587f621b0a9042bb3`.
- Frontend `main`: `0ed5b79e8612bb941678f6d68930b773e1ad49b8`.
- CW-016 is finalized and production-verified.
- Shared production plan remains version 17; no read/write production action is part of 2A implementation review.

## Authorized scope

Phase 2A adds only the frontend-owned planning contract and pure booking-window engine:

- an additive booking-target collection in the existing family-trip payload;
- separate target type, priority, desired trip date, booking status, linked reservation reference and notes;
- separate booking-rule provenance, source URL, as-of date, verification state, opening offset and deadline offset;
- separate per-date manual opening/deadline overrides;
- deterministic date-only opening/deadline calculations carrying `America/New_York` planning-zone semantics;
- neutral explicit output for malformed, unavailable, inconsistent or unverified rules;
- local persistence and exact family-sync round trips without requiring a backend schema or interpretation change.

No official booking dates or policy defaults are added. Phase 2A supplies the contract and calculation behavior only.

## Acceptance checklist

- [x] Older payloads with no `bookingTargets` field remain valid and do not gain a phantom field.
- [x] Valid booking-target collections retain unknown per-target extensions and require unique non-empty IDs.
- [x] Malformed optional booking-target data normalizes to an empty runtime view while the raw shared source round-trips unchanged.
- [x] Verified offsets calculate deterministically across month and leap-day boundaries.
- [x] Unverified calculations remain labeled `needs_verification`; unavailable rules return no invented date.
- [x] Opening and deadline overrides take precedence independently.
- [x] Inconsistent rule ordering fails neutral; an explicit per-date override does not validate the other inconsistent field.
- [x] Reservation validation, unknown-payload preservation, shared-sync conflict behavior, family-key authorization and manual itinerary controls remain regression-protected.
- [x] No dependency/runtime, backend API, database schema, production data, itinerary, reservation, credential/device, family-key or hosting configuration change is included.
- [x] Publish the frontend implementation branch after explicit user approval as PR [#57](https://github.com/MileHighHoosier/castlewatch-frontend/pull/57).
- [x] Publish and link documentation PR [#91](https://github.com/MileHighHoosier/castlewatch-2027/pull/91).
- [ ] Pass exact-head frontend and backend CI, including the Node 22 mobile browser smoke.
- [ ] Review and separately authorize Phase 2A Finalize before any merge or deployment.

## Current validation evidence

Frontend PR [#57](https://github.com/MileHighHoosier/castlewatch-frontend/pull/57) exact remote head: `4394ab030edf1d4331a95cb64d5ae78e7a3be53e` (`Add Phase 2A booking window contract`).

- Full frontend contracts: **157 passed**.
- Next.js 16.2.6 production build and TypeScript validation: **passed**.
- Focused 2A contracts: **7 passed** within the full suite.
- Local mobile browser smoke: **not run** because this runner has no supported Chrome executable; this remains an exact-head CI gate.
- Backend tracker validator: **passed** with 13 active/future tasks.
- Full unchanged backend contracts: **101 passed**; production-module compilation also passed.

## Preserved boundaries

- Booking targets never create, edit, confirm or delete reservations.
- No booking target changes the itinerary, park order, resort assignments or recommendation approval.
- Existing family sync/history remains opaque to the backend and version-tolerant in the frontend.
- Family-key recovery and `legacy_family_key_enabled` remain unchanged and enabled.
- Production data is not read or mutated by this implementation checkpoint.
- Phase 2B UI, Phase 2C workflow behavior and Phase 2D reminders are not started.
- The obsolete `castlewatch-2027` Vercel project is not altered.

## Stop and rollback rules

- Stop if exact-head CI exposes a regression or if the authoritative `castlewatch-frontend` preview is not Ready.
- Do not bypass branch protections or the obsolete Vercel project's failed check.
- Before merge authorization, rollback is branch deletion only; `main` and production are unchanged.
- After review, Phase 2A still requires separate Finalize and rollout instructions. Phase 2B remains blocked until 2A is finalized.

## Exact next command

`Review CW-017 exact-head CI and pull requests`

Review both PRs, exact-head CI and the authoritative frontend preview. Do not merge or deploy.
