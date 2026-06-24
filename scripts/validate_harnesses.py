#!/usr/bin/env python3
"""Validate agent harness contracts.

This keeps harness files agent-friendly: every harness must expose the same
control surfaces so agents can select and execute them consistently.
"""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HARNESSES_DIR = ROOT / "system" / "harnesses"
MANUAL_FILE = ROOT / "system" / "agent-operating-manual.md"

REQUIRED_HARNESS_FILES = {
    "knowledge-ingestion.md",
    "ontology-review.md",
    "concept-review.md",
    "query-synthesis.md",
    "graph-export.md",
    "meta-harness.md",
    "exploration-loop.md",
}

REQUIRED_SECTIONS = {
    "## Purpose",
    "## Objective",
    "## Mutable Surfaces",
    "## Immutable Surfaces",
    "## Sensors",
    "## Actuators",
    "## Evaluator",
    "## Promotion Policy",
    "## Logging Contract",
    "## Human Controls",
}


def validate_file(path: Path) -> list[str]:
    errors: list[str] = []
    text = path.read_text(encoding="utf-8")
    for section in sorted(REQUIRED_SECTIONS):
        if section not in text:
            errors.append(f"{path.relative_to(ROOT)} missing section: {section}")
    if "python3 scripts/build_index.py" not in text:
        errors.append(f"{path.relative_to(ROOT)} must mention build_index sensor")
    return errors


def main() -> int:
    errors: list[str] = []

    if not MANUAL_FILE.exists():
        errors.append(f"{MANUAL_FILE.relative_to(ROOT)} not found")
    else:
        manual = MANUAL_FILE.read_text(encoding="utf-8")
        for file_name in sorted(REQUIRED_HARNESS_FILES):
            if f"system/harnesses/{file_name}" not in manual:
                errors.append(f"agent manual does not route to {file_name}")

    if not HARNESSES_DIR.exists():
        errors.append(f"{HARNESSES_DIR.relative_to(ROOT)} not found")
    else:
        existing = {path.name for path in HARNESSES_DIR.glob("*.md") if path.name != "README.md"}
        for file_name in sorted(REQUIRED_HARNESS_FILES - existing):
            errors.append(f"missing harness file: system/harnesses/{file_name}")
        for file_name in sorted(REQUIRED_HARNESS_FILES & existing):
            errors.extend(validate_file(HARNESSES_DIR / file_name))

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print(f"Harness validation passed for {len(REQUIRED_HARNESS_FILES)} harnesses")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
