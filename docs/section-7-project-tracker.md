# Section 7 lightweight project tracker

## Status

**Tracker implemented and checklist passed August 31, 2026 — separate Finalize checkpoint pending.**

Section 6 is complete. The canonical tracker, cross-repository reconciliation, maintenance rules, fresh-agent handoff and repeatable structural QC now exist. The live tracker is backend issue [#61](https://github.com/MileHighHoosier/castlewatch-2027/issues/61).

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

## Implemented tracker contract

The implementation checklist established canonical `PROJECT_TRACKER.md` with stable CastleWatch task IDs and these required fields:

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

## Checklist evidence

- Both repositories were audited at backend `78926483a8509825703ec093dadee8d257301259` and frontend `90fa1f5eb3d2803e728ce7fcf067fd6f8edd6c0f`.
- The audit found two open issues: the Section 7 backend tracker [#61](https://github.com/MileHighHoosier/castlewatch-2027/issues/61) and frontend usage-counter issue [#14](https://github.com/MileHighHoosier/castlewatch-frontend/issues/14). Frontend #14 remains visible as a user decision because completed Operations v1 did not establish that the browser-local counters are unwanted.
- `PROJECT_TRACKER.md` contains 15 stable active/future task rows covering current, known rebaseline and roadmap work. Sections 1–6 remain one completed summary instead of noisy active rows.
- The tracker documents explicit status/QC vocabularies and maintenance rules for Start, checklist, defect and Finalize checkpoints.
- Its fresh-agent handoff identifies the current phase, blocker, repository sources and exact next command.
- `scripts/validate_project_tracker.py` and `tests/test_project_tracker.py` enforce the exact schema, required cells, stable unique IDs, allowed vocabularies, valid dependencies, dates, executable next actions and forbidden credential patterns.
- The work made no production/product/data/credential/device/dependency/runtime/schema/family-key mutation.

## Acceptance criteria

- [x] One canonical version-controlled tracker location is established.
- [x] The tracker covers backend and frontend work with stable task IDs.
- [x] Every active row includes all ten required fields.
- [x] Status and QC vocabularies are documented and consistently used.
- [x] Open issues in both repositories are reconciled without reopening completed work.
- [x] Remaining roadmap and known rebaseline work is represented at an appropriate level.
- [x] Completed Sections 1–6 remain summarized rather than expanded into active task rows.
- [x] Maintenance rules define updates at Start, checklist, defect and Finalize checkpoints.
- [x] A fresh-agent handoff can identify the current phase, blockers and exact next command from the tracker and linked repository sources.
- [x] A repeatable QC check validates tracker structure, unique task IDs and allowed vocabulary values.
- [x] No production/product/data/credential/device/dependency/runtime/schema/family-key mutation occurs during Section 7.

The Section 7 implementation and test checklist is complete. Section 7 remains open only for the separately commanded Finalize checkpoint. Section 8 remains unstarted.
