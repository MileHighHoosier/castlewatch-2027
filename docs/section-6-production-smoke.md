# Section 6 production smoke verification

## Status

**Section 6B started — separate start checkpoint opened August 30, 2026.**

Section 6A is complete and finalized. Section 6B is now scoped for execution, but no 6B acceptance criterion is complete yet. Sections 6C and 6D remain unstarted.

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

- [ ] All six primary navigation destinations respond correctly, with the four park destinations loading the corresponding selected-park view.
- [ ] Each park dashboard presents usable attraction data or an explicit unavailable state rather than a blank, stale-looking or internally detailed failure.
- [ ] Live/open and closed-attraction behavior, update/source context and park switching remain coherent across all four parks.
- [ ] Historical planning information is available where supported and remains clearly directional rather than a precise 2027 prediction.
- [ ] Weather-aware planning presents an honest current, stale or unavailable reliability state and preserves conservative guidance.
- [ ] Shows, Activities and Characters are separated correctly, usable and free of obvious unrelated or past-only entries.
- [ ] Live Plan produces usable mode-appropriate recommendations/explanations without silently changing the itinerary.
- [ ] Temporary Lightning Lane guidance behaves coherently and the original browser-local state is restored after verification.
- [ ] Temporary emergency break/leave-park behavior works for the selected park and the original browser-local state is restored after verification.
- [ ] No production data, shared-plan version, credential, device record, itinerary, reservation, recommendation approval, dependency/runtime, schema or family-key setting changes during 6B.

This start checkpoint establishes scope only. Section 6B remains in progress until a separate Finalize checkpoint records the evidence, any defects and every acceptance decision.
