# Section 7 lightweight project tracker

## Status

**Section 7 started — separate start checkpoint opened August 31, 2026.**

Section 6 is complete. Section 7 is scoped, but no implementation acceptance criterion is complete yet. The live tracker is backend issue [#61](https://github.com/MileHighHoosier/castlewatch-2027/issues/61).

## Goal

Establish one lightweight, durable tracker for CastleWatch work across the backend and frontend repositories. A fresh agent should be able to identify the current phase, active work, blockers, QC state and exact next action without reconstructing the project from chat history.

The canonical tracker will be version-controlled in the backend repository because that repository already owns the cross-repository `PROJECT_STATE.md`, `ROADMAP.md` and checkpoint contracts. GitHub issues, pull requests and repository documentation remain authoritative evidence; the tracker links to them and does not replace them.

## Boundaries

- Do not start Section 8 or implement a product feature during Section 7.
- Do not create a second competing tracker in a spreadsheet, chat-only artifact or frontend repository.
- Keep the active tracker concise: completed Sections 1–6 remain summarized, while active and future work receives actionable rows.
- Do not mark a task complete without linked acceptance and QC evidence.
- Do not place secrets, family keys, raw credentials, token hashes, peppers or private operational data in the tracker.
- Do not change production behavior, dependencies/runtime, schema, trip/shared-plan data, itinerary control, credentials, devices or family-key configuration.
- Keep `CASTLEWATCH_FAMILY_KEY` and `legacy_family_key_enabled` configured and enabled.

## Planned tracker contract

The implementation checklist will establish a canonical `PROJECT_TRACKER.md` with stable CastleWatch task IDs and these required fields:

1. phase;
2. task;
3. status;
4. owner/agent;
5. acceptance criteria;
6. dependencies;
7. QC status;
8. linked GitHub issue/PR;
9. last update; and
10. exact next action.

Status and QC values must use explicit documented vocabularies rather than free-form near-duplicates. Every active row must provide an executable next action or identify the blocking dependency. Cross-repository tasks must link both repositories where applicable.

## Execution plan

After this separate Start checkpoint is merged, the Section 7 checklist will:

1. inspect open issues and relevant pull requests in both CastleWatch repositories;
2. reconcile those records with `PROJECT_STATE.md`, `ROADMAP.md` and known rebaseline findings;
3. design the compact canonical table and its status/QC vocabularies;
4. seed active and future work without expanding completed Sections 1–6 into noisy historical rows;
5. define maintenance rules for Start, checklist, defect-repair and Finalize checkpoints;
6. verify that a fresh-agent handoff can recover the current phase, blockers and next command from repository sources alone; and
7. add a repeatable structural QC check so missing fields, duplicate task IDs and invalid vocabulary values are caught.

## Acceptance criteria

- [ ] One canonical version-controlled tracker location is established.
- [ ] The tracker covers backend and frontend work with stable task IDs.
- [ ] Every active row includes all ten required fields.
- [ ] Status and QC vocabularies are documented and consistently used.
- [ ] Open issues in both repositories are reconciled without reopening completed work.
- [ ] Remaining roadmap and known rebaseline work is represented at an appropriate level.
- [ ] Completed Sections 1–6 remain summarized rather than expanded into active task rows.
- [ ] Maintenance rules define updates at Start, checklist, defect and Finalize checkpoints.
- [ ] A fresh-agent handoff can identify the current phase, blockers and exact next command from the tracker and linked repository sources.
- [ ] A repeatable QC check validates tracker structure, unique task IDs and allowed vocabulary values.
- [ ] No production/product/data/credential/device/dependency/runtime/schema/family-key mutation occurs during Section 7.

This checkpoint defines scope only. Section 7 remains open until the tracker is implemented, checked against both repositories and closed through a separate Finalize checkpoint. Section 8 remains unstarted.
