#!/usr/bin/env python3
"""Validate the canonical CastleWatch project tracker structure."""

from __future__ import annotations

import re
import sys
from pathlib import Path


HEADERS = [
    "ID",
    "Phase",
    "Task",
    "Status",
    "Owner/agent",
    "Acceptance criteria",
    "Dependencies",
    "QC status",
    "GitHub",
    "Last update",
    "Exact next action",
]
ALLOWED_STATUSES = {
    "IN_PROGRESS",
    "NOT_STARTED",
    "BLOCKED",
    "NEEDS_DECISION",
    "DEFERRED",
}
ALLOWED_QC = {"NOT_RUN", "IN_REVIEW", "PASSED", "NOT_APPLICABLE"}
ID_PATTERN = re.compile(r"CW-\d{3}")
DATE_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}")
FORBIDDEN_SECRET_PATTERNS = (
    re.compile(r"cwdev_", re.IGNORECASE),
    re.compile(r"cwinv_", re.IGNORECASE),
    re.compile(r"CASTLEWATCH_FAMILY_KEY\s*=", re.IGNORECASE),
)


def _cells(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _active_table(text: str) -> tuple[list[str], list[list[str]]]:
    marker = "## Active and future work"
    section_start = text.find(marker)
    if section_start < 0:
        return [], []

    lines = text[section_start:].splitlines()
    header_index = next(
        (index for index, line in enumerate(lines) if line.lstrip().startswith("| ID |")),
        None,
    )
    if header_index is None:
        return [], []

    header = _cells(lines[header_index])
    rows: list[list[str]] = []
    for line in lines[header_index + 2 :]:
        if not line.startswith("|"):
            break
        rows.append(_cells(line))
    return header, rows


def validate_tracker_text(text: str) -> list[str]:
    errors: list[str] = []
    header, rows = _active_table(text)

    if header != HEADERS:
        errors.append(f"active table headers must be exactly: {HEADERS}")
    if not rows:
        errors.append("active table must contain at least one task row")
        return errors

    seen_ids: set[str] = set()
    parsed_rows: list[dict[str, str]] = []
    for row_number, row in enumerate(rows, start=1):
        if len(row) != len(HEADERS):
            errors.append(
                f"row {row_number} has {len(row)} fields; expected {len(HEADERS)}"
            )
            continue
        record = dict(zip(HEADERS, row))
        parsed_rows.append(record)
        task_id = record["ID"]
        if not ID_PATTERN.fullmatch(task_id):
            errors.append(f"row {row_number} has invalid task ID {task_id!r}")
        elif task_id in seen_ids:
            errors.append(f"duplicate task ID: {task_id}")
        seen_ids.add(task_id)
        for field, value in record.items():
            if not value:
                errors.append(f"{task_id or f'row {row_number}'} has blank field {field!r}")
        if record["Status"] not in ALLOWED_STATUSES:
            errors.append(f"{task_id} has invalid status {record['Status']!r}")
        if record["QC status"] not in ALLOWED_QC:
            errors.append(f"{task_id} has invalid QC status {record['QC status']!r}")
        if not DATE_PATTERN.fullmatch(record["Last update"]):
            errors.append(f"{task_id} has invalid last-update date {record['Last update']!r}")
        if record["Exact next action"].strip().lower() in {"tbd", "none", "n/a"}:
            errors.append(f"{task_id} must have an executable exact next action")

    known_ids = {record["ID"] for record in parsed_rows}
    for record in parsed_rows:
        task_id = record["ID"]
        dependencies = record["Dependencies"]
        if dependencies == "None":
            continue
        for dependency in (item.strip() for item in dependencies.split(",")):
            if not ID_PATTERN.fullmatch(dependency):
                errors.append(f"{task_id} has invalid dependency {dependency!r}")
            elif dependency == task_id:
                errors.append(f"{task_id} cannot depend on itself")
            elif dependency not in known_ids:
                errors.append(f"{task_id} depends on unknown task {dependency}")

    for pattern in FORBIDDEN_SECRET_PATTERNS:
        if pattern.search(text):
            errors.append(f"tracker contains forbidden credential pattern {pattern.pattern!r}")

    return errors


def validate_tracker(path: Path) -> tuple[list[str], int]:
    text = path.read_text(encoding="utf-8")
    errors = validate_tracker_text(text)
    _, rows = _active_table(text)
    return errors, len(rows)


def main(argv: list[str] | None = None) -> int:
    arguments = argv if argv is not None else sys.argv[1:]
    path = Path(arguments[0]) if arguments else Path("PROJECT_TRACKER.md")
    errors, task_count = validate_tracker(path)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"{path}: valid ({task_count} tasks)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

