# Section 6 production smoke verification

## Status

**Section 6C complete and finalized August 30, 2026.**

Sections 6A, 6B and 6C are complete and finalized. Section 6D remains unstarted.

Section 6 verifies the deployed Vercel/Railway system across critical user flows. It is a production-verification phase, not a feature sprint. Any defect discovered here must be isolated, documented and separately repaired with the normal test/build/deployment gates.

The live tracker is backend issue #53.

## Safety boundaries

- Keep `CASTLEWATCH_FAMILY_KEY` and `legacy_family_key_enabled` configured and enabled.
- Never place a family key, raw device token, raw invite token, token hash or pepper in source, GitHub, logs or screenshots.
- Prefer read-only production checks. Any state-changing verification must be minimal, reversible or content-identical, and explicitly approved before it runs.
- Do not recreate the Section 5E Editor/Viewer device lifecycle unless a specific gap or regression requires it.
- Preserve shared history, the active protected Owner and the approved October 9–16, 2027 trip assumptions.
- Do not automatically apply a Trip Week itinerary or recommendation change.
- Treat the real `castlewatch-frontend` Vercel project as authoritative. The obsolete `castlewatch-2027` Vercel integration may report a known unrelated failure.

## Verification batches

### 6A — Production baseline and smoke contract

Confirm the exact production heads, CI and deployment status; verify the live frontend and backend health; verify protected endpoints fail closed without credentials; record the invariant baseline; and define the remaining smoke batches.

### 6B — Core website flows

Verify the production navigation, four park dashboards, live/closed attraction behavior, historical planning information, weather reliability states, shows, activities, characters, Live Plan, Lightning Lane guidance and emergency modes.

### 6C — Trip Week and shared-plan flows

Verify Trip Week presentation and recommendation reasoning, trip profile/reservations/resorts/transportation, safe Owner shared-plan status/history/backup behavior and role-boundary evidence. Reuse completed Section 5E production evidence where repeating a credential lifecycle would create unnecessary risk.

### 6D — Mobile, failure-state and Section 6 closeout

Verify the critical mobile layout and touch flows, graceful degradation and sanitized failure states, reconcile production-verification issues, run the final automated regression/build gates and close Section 6.

Each batch requires its own Start and Finalize checkpoint.

## Section 6A acceptance criteria

- [x] Frontend and backend default branches resolve to the finalized Section 5 closeout commits.
- [x] The Section 5 closeout pull requests are merged.
- [x] The relevant GitHub Actions workflows passed.
- [x] The authoritative frontend Vercel and backend Railway deployment statuses are successful.
- [x] The live production frontend returns HTTP 200.
- [x] Railway `/health` returns HTTP 200 with `{"status":"ok"}`.
- [x] Unauthenticated shared-plan, history, Operations and device-access reads return sanitized HTTP 401 responses.
- [x] Production CORS grants the CastleWatch frontend origin and does not grant an unrelated origin.
- [x] The Section 5E invariant baseline is recorded without exposing credentials.
- [x] A fresh trusted-Owner browser check confirms shared version 17 remains up to date under `Ryan Brave Owner`.

## Section 6A automated evidence

Verified August 30, 2026:

- frontend `main`: `1598d6498d447f6e0ce18b06c4bba6090bdb85d2`;
- backend `main`: `b590baf35d1dd222d2ee9e4ab7e407386745c4e5`;
- frontend PR #45 and backend PR #52 are merged;
- frontend and backend **Family sync reliability** workflow runs completed successfully on the closeout PR heads;
- the frontend merge commit reports successful deployment from the real `castlewatch-frontend` Vercel project;
- the backend merge commit reports successful Railway deployment;
- `https://castlewatch-frontend.vercel.app/` returned HTTP 200;
- `https://castlewatch-2027-production.up.railway.app/health` returned HTTP 200 with `{"status":"ok"}`;
- unauthenticated `GET` requests to `/api/family-trip`, `/api/family-trip/history`, `/api/family-trip/operations` and `/api/family-trip/devices/access` returned HTTP 401 with the stable unauthorized response and no internal exception text;
- the backend returned `Access-Control-Allow-Origin: https://castlewatch-frontend.vercel.app` for the production frontend origin and no allow-origin grant for `https://example.com`.
- a fresh trusted-Owner production screenshot confirmed **Connected · v17**, shared version 17, `Ryan Brave Owner · owner`, **Up to date**, and guarded autosave off.

The known starting invariant from the finalized Section 5E production evidence is:

- shared version 17;
- `Columbus Day Week 2027`;
- October 9–16, 2027;
- two adults and two children;
- no park hopping;
- zero bookings;
- **Wait / Keep the base plan provisional** while official 2027 MNSSHP dates remain unavailable;
- `Ryan Brave Owner` active;
- temporary Editor/Viewer devices revoked;
- guarded autosave off;
- family-key recovery enabled.

No production data, credential, dependency/runtime, schema, itinerary, reservation, recommendation, device record or family-key setting was changed by the automated Section 6A checks.

All Section 6A acceptance criteria passed. PR #54 finalizes the checkpoint without starting Section 6B.

## Section 6B start checkpoint

Started August 30, 2026 as a separate checkpoint from Section 6A.

Section 6B verifies the already-deployed core website experience. It does not add features or authorize itinerary, shared-plan, account/device, credential, dependency/runtime, schema or production-data changes. Any defect discovered during the smoke run must be recorded and repaired separately through the normal test/build/deployment gates before the affected criterion can pass.

The 6B smoke run will:

1. verify the six-destination navigation shell without evaluating the Trip Week or Getting There content reserved for 6C;
2. open Magic Kingdom, Epcot, Hollywood Studios and Animal Kingdom and verify each park dashboard resolves the selected park correctly;
3. inspect live/open and closed-attraction presentation, update/source context and historical directional planning information without treating historical evidence as a precise 2027 forecast;
4. verify weather reliability/status presentation and that current information is not falsely represented when evidence is stale or unavailable;
5. verify Shows, Activities and Characters remain correctly separated and usable;
6. exercise Live Plan recommendations and explanations without completing rides or changing the approved itinerary;
7. exercise temporary browser-local Lightning Lane guidance and restore the starting browser state afterward;
8. exercise temporary browser-local emergency break/leave-park controls and restore the starting browser state afterward.

Production mutations are not part of the start checkpoint. Before any temporary browser-local state change is used as evidence, its starting state must be recorded and the check must be reversible. Section 6B must not upload/download the shared plan, create a backup, restore history, change trip/profile/reservation/resort data, apply or lock an itinerary scenario, manage devices, use an invite, expose a credential or alter family-key recovery.

## Section 6B acceptance criteria

- [x] All six primary navigation destinations respond correctly, with the four park destinations loading the corresponding selected-park view.
- [x] Each park dashboard presents usable attraction data or an explicit unavailable state rather than a blank, stale-looking or internally detailed failure.
- [x] Live/open and closed-attraction behavior, update/source context and park switching remain coherent across all four parks.
- [x] Historical planning information is available where supported and remains clearly directional rather than a precise 2027 prediction.
- [x] Weather-aware planning presents an honest current, stale or unavailable reliability state and preserves conservative guidance.
- [x] Shows, Activities and Characters are separated correctly, usable and free of obvious unrelated or past-only entries.
- [x] Live Plan produces usable mode-appropriate recommendations/explanations without silently changing the itinerary.
- [x] Temporary Lightning Lane guidance behaves coherently and the original browser-local state is restored after verification.
- [x] Temporary emergency break/leave-park behavior works for the selected park and the original browser-local state is restored after verification.
- [x] No production data, shared-plan version, credential, device record, itinerary, reservation, recommendation approval, dependency/runtime, schema or family-key setting changes during 6B.

## Section 6B production evidence and finalization

Verified August 30, 2026:

- all six primary navigation destinations responded, and Magic Kingdom, Epcot, Hollywood Studios and Animal Kingdom each resolved the selected-park view;
- all four park dashboards returned usable attraction data with coherent live/open or closed presentation, update timestamps, Railway `/api/rides` source context, historical sample counts and a connected backend;
- tomorrow and historical planning copy remained explicitly directional and separate from the live response rather than claiming a precise 2027 prediction;
- Railway weather advisory returned HTTP 200 with a current `weather.gov` no-advisory result, while temporary Heat and Storm selections produced conservative A/C/short-walk and shelter-first guidance before Weather OK was restored;
- Shows, Activities and Characters rendered usable separated panels across all four parks with upcoming or explicit verify-timing states;
- Max rides, Low-stress and Cool down produced distinct Animal Kingdom recommendations with explicit Why chosen and historical context, without starting a route or changing the itinerary;
- temporary emergency mode showed the Animal Kingdom reset/leave-park plan and made Lightning Lane guidance secondary, then returned to its inactive starting state;
- a temporary Lightning Lane window produced coherent next-window guidance and was removed to restore the empty starting state after the production repair described below; and
- no server-side production data, shared-plan version, credential, device record, itinerary, reservation, recommendation approval, dependency/runtime, schema or family-key setting changed.

Two production defects were isolated and repaired through the normal frontend gates before the affected criteria passed:

- frontend PR [#47](https://github.com/MileHighHoosier/castlewatch-frontend/pull/47) classified `Disney Jr. Mickey Mouse Clubhouse Live!` as entertainment, excluded it from ride demand and Live Plan, preserved its Activities presentation, passed exact Node 22 CI and deployed successfully from the authoritative Vercel project at merge `26caf3989b92faf60da95b6688c09f05231c5def`;
- frontend PR [#49](https://github.com/MileHighHoosier/castlewatch-frontend/pull/49) made Lightning Lane Add, Used/Undo and Remove rerender immediately, added a browser add/remove round-trip regression, passed exact Node 22 CI and deployed successfully from the authoritative Vercel project at merge `ae63c89fb7194139df40d7a7d0609cdb6084a7eb`.

All Section 6B acceptance criteria passed. This separate Finalize checkpoint closes 6B without starting 6C or 6D.

## Section 6C start checkpoint

Started August 30, 2026 as a separate checkpoint from Section 6B.

Section 6C verifies the already-deployed Trip Week and shared-plan experience. It does not add features, change the approved trip, authorize a recommendation, recreate the Section 5E device lifecycle or authorize a production write. Any defect discovered during the smoke run must be recorded and repaired separately through the normal test/build/deployment gates before the affected criterion can pass.

The 6C smoke run will:

1. verify the saved `Columbus Day Week 2027` profile remains October 9–16, 2027 for two adults and two children, with no park hopping and zero bookings;
2. inspect the saved base itinerary, overnight resort assignments and trip-day presentation without applying, locking or undoing a scenario;
3. verify reservation summaries, readiness and conflict presentation accurately reflect the current zero-booking baseline;
4. verify Getting There transportation guidance uses the selected trip day and overnight resort context, remains understandable and does not claim precise guaranteed travel times;
5. inspect the unified recommendation's outcome, confidence, risk comparison, blockers and next actions while preserving manual user approval over itinerary changes;
6. verify the protected Owner connection, selected credential, shared version, synchronization state and guarded-autosave state before any shared-plan action;
7. inspect current and historical shared versions, backup provenance and restore controls without restoring a version;
8. verify manual content-identical backup behavior only if the user separately confirms that minimal append-only production write immediately before it runs; otherwise reuse the completed Section 5E backup evidence and verify the control/read path only; and
9. reuse the completed Section 5E Editor/Viewer authorization evidence unless a specific regression requires a separately approved new device lifecycle.

The start checkpoint makes no production mutation. Section 6C must not upload or download over local changes, create a backup, restore history, alter trip/profile/reservation/resort data, apply/undo/lock an itinerary scenario, enable guarded autosave, manage devices, accept an invite, expose a credential or alter family-key recovery. Any later minimal content-identical backup requires a fresh baseline check and separate user confirmation; it must preserve append-only history and all approved trip invariants.

## Section 6C acceptance criteria

- [x] Trip Week presents `Columbus Day Week 2027`, October 9–16, 2027, two adults, two children, no park hopping and zero bookings without unexplained drift.
- [x] The base itinerary, trip-day cards and overnight resort assignments render coherently without an automatic scenario change.
- [x] Reservation counts, details, readiness and conflict presentation accurately reflect the current zero-booking baseline.
- [x] Getting There provides usable trip-day/resort-aware transportation guidance and clearly directional rather than guaranteed timing.
- [x] The unified recommendation remains understandable, exposes its outcome, confidence, comparison, blockers and next actions, and preserves manual approval for any itinerary change.
- [x] Apply, undo and lock controls do not mutate the itinerary unless the user explicitly approves that action; no such action is authorized by this checkpoint.
- [x] The trusted browser reports the protected `Ryan Brave Owner` credential, shared version 17, an up-to-date baseline and guarded autosave off before shared-plan verification begins.
- [x] Current and historical shared versions, provenance and eligible Owner controls are readable without restoring or overwriting history.
- [x] Manual-backup behavior is verified safely using either the completed Section 5E content-identical evidence or a separately confirmed content-identical backup after a fresh baseline check.
- [x] Owner/Editor/Viewer boundaries remain supported by current automated contracts and the completed Section 5E production evidence without unnecessarily recreating credentials or devices.
- [x] No unauthorized production/shared-plan/profile/itinerary/reservation/resort/recommendation/credential/device/dependency/runtime/schema/family-key mutation occurs during 6C.

## Section 6C production evidence and finalization

Verified August 30, 2026:

- a trusted-Owner screenshot and full-page PDF showed `Columbus Day Week 2027`, October 9–16, 2027, one park per day, no park hopping, two adults, two children and zero bookings/confirmed reservations;
- the saved Base plan remained active, all trip-day cards and overnight resort assignments rendered coherently, and no scenario was applied, undone or locked;
- the unified recommendation remained **Wait for official data / Keep the base plan provisional**, showed low confidence, compared the Base plan with the MNSSHP alternate, identified unreleased official 2027 MNSSHP dates as the blocker and gave explicit next actions;
- the trusted browser showed **Connected · v17**, `Ryan Brave Owner · owner`, shared version 17, **Up to date**, guarded autosave **Off** and a protected-device label for the Owner;
- an isolated production-browser read verified trip-day/resort-aware Getting There guidance for Sunday Value Resort to Magic Kingdom and Wednesday Beach Club to Epcot International Gateway, then restored the temporary selected day to Sunday and returned to Trip Week;
- Backup History & Restore reported 13 retained snapshots, marked shared version 17 **Current**, kept older versions readable and preserved restore provenance including v16 restored from v14 and v14/v13 restored from v11;
- historical versions exposed preview controls, but no preview or restore was opened;
- the safe manual-backup criterion reused the completed Section 5E content-identical backup evidence, so no new backup or append-only production write was needed;
- current backend contracts plus completed Section 5E production evidence supported the Owner/Editor/Viewer boundaries without recreating devices; and
- no upload, download, backup, restore, guarded-autosave, trip/profile, reservation, resort, recommendation, credential/device, dependency/runtime, schema or family-key mutation occurred.

No new defect was found during 6C. All Section 6C acceptance criteria passed. This separate Finalize checkpoint closes 6C without starting 6D.
