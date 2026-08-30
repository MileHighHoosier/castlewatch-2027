# Section 6 production smoke verification

## Status

**Section 6A started August 30, 2026.**

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
- [ ] A fresh trusted-Owner browser check confirms shared version 17 remains up to date under `Ryan Brave Owner`.

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
