# Rebaseline Section 2A production regression

Status: Open

## Observed on iPhone production verification

After the Section 2A refresh-guard deployment and subsequent read-availability deployment, the Park Command Center History value remains `0` across repeated browser reloads even though the same production database previously showed approximately 29,900 Epcot historical entries.

The screenshots confirm that `0` is stable across reloads, but this is not an acceptable pass condition because the frontend renders `0` whenever planning insights are unavailable.

## Known facts

- The frontend renders `insights?.historical_entries_analyzed || 0`, so a failed/missing planning-insights response is indistinguishable from a real zero-history database.
- The frontend requests `/api/planning-insights` during initial load.
- The frontend also schedules a background ride refresh during initial ride-data loading.
- Railway now runs two Gunicorn workers with a 120-second request timeout.
- Backend CI and deployment checks are green.
- No code intentionally deletes historical wait rows.

## Required correction before Section 2B

1. Make planning-insights availability observable instead of converting failure to `0`.
2. Prevent initial History loading from racing unnecessarily with background collection.
3. Verify that the production planning-insights endpoint returns the existing Epcot historical count.
4. Re-run one iPhone screenshot verification only after the corrective deployment is ready.

Do not mark Section 2A production-verified until History is restored and duplicate refreshes remain bounded.
