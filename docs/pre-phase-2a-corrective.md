# Pre–Phase 2A corrective checkpoint

Started September 7, 2026 after the user authorized the independent audit's bounded corrections.

## Separate start checkpoint

- Backend baseline: `750d2a0a8fa44a32b4cdb437852cca44052b9283`.
- Frontend baseline: `e46498ba5721015938856660a2b0f5773b65330b`.
- Phase 2A product implementation remains paused; its booking-target contract, calculation engine and UI are not included here.
- Scope: mixed-version payload preservation, reservation validation, scenario-specific blockers, weather calendar/freshness regression coverage, and authoritative handoff reconciliation.
- Preserve current role enforcement, explicit credential selection, family-key recovery, optimistic version locking, history and manual itinerary control.
- Do not mutate production/shared data or change dependencies, database schema, runtime or hosting configuration.

## Acceptance and release gates

1. Reproduce audit defects in isolated tests; protect old-client and rollback behavior before introducing new shared fields.
2. Run focused and full frontend/backend suites, frontend build, backend compilation and tracker validation.
3. Publish paired reviewable changes with exact-head CI evidence. No automatic merge or production deployment.
4. Obtain separate rollout authorization, deploy the backend compatibility guard before the frontend, and perform the separately approved checklist.
5. Finalize separately only after required release evidence passes. Do not reinterpret historical screenshots as fresh authenticated verification.

## Current status

The original temporary Work commits were lost before publication and cannot be recovered. On September 8, 2026 the user authorized a controlled reconstruction with new commit identities. The published corrective commits do not claim the lost SHAs.

**Finalized September 8, 2026.** The backend and frontend corrections passed exact-head review, rolled out backend first, passed production verification, and were finalized without starting Reservation Awareness Phase 2A.

## Surviving reconstruction evidence

- backend and frontend `main` still match the audited baselines above;
- backend issue [#87](https://github.com/MileHighHoosier/castlewatch-2027/issues/87) preserves the exact authorized scope and exclusions;
- the complete original frontend corrective Git tree survives as `073ae31cfb3b080427b2be972ea314dd1a78cf00`, including its 17-file blob map;
- the backend start-checkpoint tree survives as `1fbdad1b3ffc9af98ad30840ee59c9bec322c721`;
- the interrupted task record preserves the intended backend file list, behavior, focused tests, full-suite counts and rollout order;
- the lost backend final tree was recorded as `18662f5fa68474d717555271e647fab992704111`, but that object was never published and cannot be fetched.

## Reconstructed behavior

Backend:

- validates the shared `reservations` collection before any write;
- preserves optimistic-version precedence, then rejects a current-version write that omits existing root fields or down-revs `schemaVersion`;
- applies the same compatibility protection before restoring an older snapshot;
- adds regression coverage for malformed reservations, additive fields, destructive older-client writes, schema downgrade and restore safety.

Frontend:

- retains unknown downloaded root and known-object extension fields while rebuilding the local payload;
- rejects unsupported newer schemas and malformed reservations without silently replacing their stored source;
- makes malformed reservation input force a Review recommendation and block local reservation mutations;
- calculates generic reservation blockers against the preferred scenario while preserving intrinsic timing/no-hopping constraints;
- assigns calendar days in `America/New_York` and refreshes elapsed-time evidence every minute and on focus/page-show;
- adds focused regressions for payload round trips, malformed data, preferred-scenario blockers, Orlando midnight boundaries and weather aging.

## Reconstruction differences

- Commit SHAs and branch names are necessarily new.
- The 17 original frontend file blobs were reconstructed byte-for-byte from the surviving Git tree before this README-equivalent handoff note was updated for the new branch name.
- The backend behavior and test intent are reconstructed from the issue, audit and recorded patch transcript. The final backend tree object is unavailable, so documentation wording cannot be proven byte-identical to the lost temporary commit.
- No feature, dependency, schema, credential, production-data or itinerary scope was added.

## Local verification

Passed on the reconstructed worktrees:

- backend full suite: **101 passed**;
- backend active root-module compilation: **passed**;
- project tracker validator: **valid (13 tasks)**;
- frontend full contract suite: **150 passed**;
- frontend production Next.js build and TypeScript validation: **passed**;
- frontend functional blobs, excluding the reconstruction-specific README update, match the surviving corrective Git tree;
- staged diff checks: **passed**.

The local runtime supplied Python 3.12.13 and Node 24.19.0. Exact pinned Python 3.12.14 / Node 22 execution and the 390×844 Chrome smoke remain required in GitHub Actions. The local mobile smoke could not start because this environment has no supported Chrome executable; no browser assertion failed.

## Final rollout evidence

- Backend PR [#88](https://github.com/MileHighHoosier/castlewatch-2027/pull/88) retained authorized head `048baf821f317f19e2b9d2b26078818505719291` and merged as `c4f4f015ea2f8987463293bb19f1d210edf7ace3`.
- Railway reported the backend deployment successful. Production `/health`, root and `/api/trip-week` reads returned HTTP 200; an unauthenticated family-plan read returned the expected HTTP 401.
- A production family-key recovery read connected through the frontend and loaded shared version 17 without saving, restoring or otherwise mutating shared data.
- Frontend PR [#56](https://github.com/MileHighHoosier/castlewatch-frontend/pull/56) retained authorized head `5780b5ca38777172272a4462d09b4fd2ba05ed4d` and merged as `0ed5b79e8612bb941678f6d68930b773e1ad49b8`.
- The correct `castlewatch-frontend` Vercel production deployment succeeded, and post-merge frontend workflow run 89 passed.
- Read-only production smoke passed for live ride/history data, Railway connectivity, Trip Week dates and scenario evidence, elapsed-time cache presentation, and authenticated shared-plan reads. No application-origin browser console errors were observed.
- The separate obsolete `castlewatch-2027` Vercel project remains unchanged. Its known one-second failure is configuration-only: the configured Root Directory `website` does not exist. Cleanup remains tracked separately as CW-009.
- No production/shared plan, itinerary, reservation, resort, credential/device, schema, dependency or hosting configuration was changed outside the authorized deployments.

## Rollout and rollback order

1. Review both PRs and require exact-head CI.
2. After separate rollout approval, deploy the backend compatibility/validation guard first.
3. Verify Railway health and shared-plan read behavior without mutation.
4. Deploy the frontend preservation/date/scenario correction.
5. Run the separately approved corrective production checklist.
6. Roll back frontend first, then backend, if the paired rollout fails. Do not introduce booking-target fields while either corrective side is absent.

CW-016 is finalized. Reservation Awareness Phase 2A remains paused and requires separate explicit authorization before any feature work begins.
