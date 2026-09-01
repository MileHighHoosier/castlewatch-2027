# Section 8D Test Checklist

_Started September 1, 2026_

## Status

**In review.** Repository, build, exact-head CI, mobile-smoke, compilation and deployment-status gates pass. The remaining gate is a read-only visual verification of the deployed mobile decision surface. Section 8D is not finalized.

## Implementation under test

- frontend PR [#55](https://github.com/MileHighHoosier/castlewatch-frontend/pull/55), merged as `e46498ba5721015938856660a2b0f5773b65330b`;
- backend implementation-status PR [#80](https://github.com/MileHighHoosier/castlewatch-2027/pull/80), merged as `719a5ae5a0a0720be9c9e9eb50a71887510b4393`.

## Passed gates

- [x] Frontend contract suite: 138 tests passed.
- [x] Frontend production build passed TypeScript and static/dynamic route generation.
- [x] Frontend exact-head GitHub Actions run `33457916392` passed under Node 22.
- [x] The same exact-head run passed the dependency-free 390×844 Chrome mobile smoke.
- [x] Section 8D explanation regressions verify deterministic category order, score labels, evidence state/source/context, affected reservations and the explicit apply/undo/lock/unlock surface.
- [x] Existing keep/swap/wait/review, confirmed-reservation, no-park-hopping, transportation, weather and Lightning Lane regressions remain green.
- [x] Backend exact-head GitHub Actions run `33458203389` passed the full backend contract suite and production-module compilation.
- [x] Tracker validation passed with 14 active/future tasks; five focused tracker tests passed.
- [x] Vercel reports a successful deployment for frontend merge `e46498ba5721015938856660a2b0f5773b65330b`.
- [x] Railway reports a successful deployment for backend merge `719a5ae5a0a0720be9c9e9eb50a71887510b4393`.
- [x] No dependency/runtime, schema, credential/device or family-key change is present.

## Pending production presentation gate

The automated production browser connection was unavailable in this session. No alternate login, credential entry or mutating action was attempted. Two screenshots from the live mobile Trip Week page are required:

1. the recommendation card showing the scenario scores and the `Plan changes are never automatic` statement;
2. the expanded `Decision evidence & reservation impact` section showing both scenario headings and at least one category's state, source and point contribution.

The screenshots are read-only evidence. Do not apply, undo, lock, unlock, upload, restore, disconnect, rename, revoke or change any shared-plan, itinerary, reservation, resort, credential or device state.

## Finalize boundary

After the production screenshots pass, the checklist may be merged and the exact next command becomes `Finalize Section 8D`. `Finalize Section 8` remains a later separate approval.

## Exact next command

`Submit Section 8D production screenshots`
