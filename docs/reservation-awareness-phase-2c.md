# Reservation Awareness Phase 2C checkpoint (CW-019)

**Status:** Started September 13, 2026 and published for review September 14, 2026. The bounded exact-head smoke-harness correction is published; its CI/Vercel evidence and independent review are pending. Phase 2D has not started.

**Tracker:** dedicated backend issue [#96](https://github.com/MileHighHoosier/castlewatch-2027/issues/96) under parent issue [#85](https://github.com/MileHighHoosier/castlewatch-2027/issues/85), frontend PR [#59](https://github.com/MileHighHoosier/castlewatch-frontend/pull/59), and documentation PR [#97](https://github.com/MileHighHoosier/castlewatch-2027/pull/97). Publication of the existing branches and review pull requests was separately authorized September 13, 2026.

## Verified baseline

- Backend `main`: `44a335b6a1b77233d6ff55864a43a229d592259d` (finalized CW-018 closeout documentation).
- Frontend `main`: `a82ddaa2628cf139e35c2a917b0033a2e18b81e3` (finalized CW-018 implementation).
- Local documentation branch: `docs/cw-019-reservation-awareness-phase-2c`.
- Local frontend branch: `feat/cw-019-reservation-awareness-phase-2c`.
- Phase 2A and Phase 2B remain complete, production-verified and finalized.

## Authorized scope

Phase 2C adds only the explicit attempt and contingency workflow over the finalized booking-target planner:

- planned, attempted, booked, unavailable and backup target lifecycle states;
- dated attempt/result records with user-entered notes;
- a dated, user-entered fallback choice that does not claim or infer availability;
- deliberate linking of a booked target to an existing reservation selected by the user;
- clear explanation that target lifecycle actions do not alter reservations, itinerary, transportation, Trip Week or recommendation approval;
- additive, version-tolerant optional lifecycle fields that preserve the Phase 2A calculation/storage contract and Phase 2B cooperative-write protocol.

The planner does not create a reservation. A family member must deliberately create or edit the reservation in the existing Trip Week reservation surface, then return to the planner and select that exact record. Linking stores only the reservation identifier on the booking target. The reservation remains authoritative for its date, time, location, confirmation status, timing/transportation guidance, conflict warnings and Trip Week effects.

## Acceptance checklist

- [x] The user separately authorized `Start Reservation Awareness Phase 2C`.
- [x] Exact backend and frontend remote `main` baselines were verified before branching.
- [x] Isolated local CW-019 documentation and frontend branches were created from those exact baselines.
- [x] Existing Phase 2A targets remain valid when Phase 2C attempt/fallback fields are absent.
- [x] Attempt and unavailable actions append dated, user-controlled records without claiming live availability.
- [x] Backup selection requires a user-entered choice and valid action date; no alternative is invented.
- [x] Booked state requires a deliberate link to an existing reservation; missing or deleted links warn without cleaning stored data.
- [x] The planner has no reservation, itinerary, resort, shared-upload, restore or recommendation-approval writer.
- [x] Unlinking is deliberate, returns the target to attempted and does not modify or delete the reservation or attempt history.
- [x] All lifecycle writes use the existing latest-valid-collection callback under the Phase 2B exclusive Web Lock.
- [x] Concurrent target additions and lifecycle writes retain unknown fields and both valid changes.
- [x] Malformed/future-format target storage remains write-protected by the finalized Phase 2B protocol.
- [x] Phase 2A booking-window calculations, readiness behavior, raw helpers, serialized shared payload and family-sync/history behavior remain unchanged.
- [x] No external reminders, automatic booking, itinerary mutation, policy defaults, dependency/runtime change or backend schema/API change is introduced.
- [x] Focused Phase 2A/2B/2C contracts pass locally.
- [x] Full frontend contracts and the Next.js production build pass locally.
- [ ] Rendered 390×844 lifecycle and multi-tab smoke pass in exact-head Node 22 CI. Local Chrome availability is not assumed.
- [x] Backend tracker validation and unchanged backend contracts pass locally.
- [x] Separate user authorization was received before creating issue #96, publishing branches or opening review pull requests.
- [x] The dedicated issue, existing frontend branch and existing documentation branch were published as issue #96, frontend PR #59 and documentation PR #97 without merge or deployment.
- [x] The initial exact-head run's multi-tab failure was isolated to a smoke completion race: deterministic writer tests and the full suite passed, while the harness checked only rendered `aria-busy` before confirming that the real Web Lock queue had drained.
- [x] The smoke now waits for both held and pending `castlewatch.booking-targets.v1.write` entries to clear before accepting the rendered idle state, with a deterministic harness regression for held, pending, idle and still-rendering states.
- [ ] Frontend and documentation exact-head CI and the authoritative `castlewatch-frontend` preview pass.
- [ ] Independent post-publication review accepts the exact heads and all evidence.
- [ ] Separate Finalize authorization is received before any merge or deployment.

## Lifecycle and contingency rules

1. `Record attempt` appends an `attempted` record and changes only the target state.
2. `Record unavailable result` records the family's observed outcome; it is not a live inventory check or official availability claim.
3. `Select this backup` requires the family to name the fallback and action date. CastleWatch does not populate or validate its availability.
4. `Link reservation & mark booked` re-reads reservation storage, refuses malformed storage or a missing identifier, appends a booked result and stores the selected reservation ID on the target.
5. A booked/link-bearing target must be deliberately unlinked before another lifecycle action. Unlinking leaves the reservation and historical attempt records unchanged.
6. Legacy booked targets with no link, deleted links and links outside booked state remain readable and receive an explicit warning. Nothing is silently normalized or written.

## Compatibility and safety boundaries

- `attempts` and `fallbackChoice` are optional additive target fields; no payload or database schema version changes.
- Unknown booking-target root, rule, override, attempt and fallback fields survive reads and lifecycle writes.
- Every planner mutation continues through `updateBookingTargets`, which acquires `castlewatch.booking-targets.v1.write` before read/validate/change/save. Missing lock support and malformed/future-format target storage fail closed.
- Shared upload/download/history authorization, `expectedVersion`, family-key recovery and `legacy_family_key_enabled` are unchanged.
- Reservation storage is read only from the booking planner. Malformed reservation storage disables linking and is not repaired or overwritten.
- Phase 2C does not alter production/shared-plan data, the October 9–16, 2027 itinerary, reservations, resorts, credentials/devices, dependencies/runtime, Railway, Vercel or the obsolete secondary Vercel project.
- Phase 2D reminders and all additional development remain paused.

## Local validation evidence

- Initial frontend head `eb2d177321b61b899da2116c7e95aff60acde23a` passed its full contract suite and production build in CI run `34801378007`, then failed only the rendered multi-tab completion assertion `add preserves the other tab's addition` (`0 !== 1`). The harness had accepted `aria-busy="false"` without first proving that the cross-tab write-lock queue was empty.
- Corrected frontend head `eaaf71c0cbdb8cfecb4634c45ed3c41b32c909d1` changes only the smoke completion barrier and adds its deterministic regression; application code and write behavior are unchanged.
- Focused booking-target calculation/timeline/lifecycle/storage/shared-sync/harness contracts: **31 passed**.
- Full frontend suite: **181 passed**.
- Next.js 16.2.6 production build and TypeScript validation: **passed** after replacing a temporary worktree-only `node_modules` symlink that Turbopack correctly rejected; no manifest or dependency changed.
- The rendered smoke covers planned → attempted → unavailable → backup → booked → explicit unlink, verifies reservation storage is byte-for-byte unchanged, and adds lifecycle attempts to both real-lock queue orders. It now also requires the actual booking-target Web Lock queue and rendered saving state to be idle before examining persisted results.
- Local mobile smoke launch stopped before browser execution because no Chrome executable is installed; no smoke pass is claimed. The updated 390×844 lifecycle/multi-tab scenario remains a required exact-head Node 22 CI gate.
- Backend tracker validation: **passed (13 active/future tasks)**. Full unchanged backend contracts: **102 passed** in the repository's pinned test environment.

## Publication and stop rules

- Continue only on the two published CW-019 branches and existing review PRs; do not create replacement branches or PRs.
- Stop on any calculation/readiness, reservation/shared-sync, malformed-storage, cooperative-lock, family-key, build, mobile or tracker/backend regression.
- Do not merge, deploy, mutate production/shared-plan data, begin Phase 2D or alter the obsolete Vercel project.

## Exact next action

`Perform an independent review of CW-019 Phase 2C at the exact heads of frontend PR #59 and backend documentation PR #97. Verify the Phase 2C contract and acceptance criteria, lifecycle truthfulness, reservation-link safety, Phase 2A/2B calculation/storage/shared-sync compatibility, regression coverage, documentation accuracy, exact-head CI, mobile smoke, and the authoritative castlewatch-frontend preview. State whether controlled finalization is safe and identify any blocker. Do not modify, merge, deploy, begin Phase 2D, alter protected data, or alter the obsolete Vercel project.`
