#!/usr/bin/env python3
"""Source registry storage helpers.

SQLite is preferred when present so source lookup can scale past a large YAML
file. YAML remains the compatibility format for existing agents and diffs.
"""

from __future__ import annotations

import re
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB_FILE = ROOT / "sources" / "source-registry.sqlite"
DEFAULT_YAML_FILE = ROOT / "sources" / "source-registry.yaml"
SOURCE_ID_RE = re.compile(r"^\s*-\s+id:\s*([A-Za-z0-9_.:-]+)\s*$", re.MULTILINE)


def read_source_ids(
    db_path: Path = DEFAULT_DB_FILE,
    yaml_path: Path = DEFAULT_YAML_FILE,
) -> tuple[set[str], list[str]]:
    if db_path.exists():
        return read_source_ids_from_sqlite(db_path)
    return read_source_ids_from_yaml(yaml_path)


def read_source_ids_from_sqlite(db_path: Path) -> tuple[set[str], list[str]]:
    try:
        with sqlite3.connect(db_path) as connection:
            rows = connection.execute("SELECT id FROM sources ORDER BY id").fetchall()
    except sqlite3.Error as exc:
        return set(), [f"{db_path} source database error: {exc}"]

    source_ids = {str(row[0]) for row in rows if row and row[0]}
    if not source_ids:
        return source_ids, [f"{db_path} has no source ids"]
    return source_ids, []


def read_source_ids_from_yaml(yaml_path: Path) -> tuple[set[str], list[str]]:
    if not yaml_path.exists():
        return set(), [f"{yaml_path} not found"]

    text = yaml_path.read_text(encoding="utf-8")
    source_ids = set(SOURCE_ID_RE.findall(text))
    if not source_ids:
        return source_ids, [f"{yaml_path} has no source ids"]
    return source_ids, []


def initialize_sqlite_from_yaml(
    db_path: Path = DEFAULT_DB_FILE,
    yaml_path: Path = DEFAULT_YAML_FILE,
) -> None:
    records = read_source_records_from_yaml(yaml_path)
    if not records:
        _, errors = read_source_ids_from_yaml(yaml_path)
        raise ValueError("; ".join(errors or [f"{yaml_path} has no source records"]))

    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS sources (
                id TEXT PRIMARY KEY,
                title TEXT,
                tier TEXT,
                yaml_text TEXT
            )
            """
        )
        for record in records:
            connection.execute(
                """
                INSERT INTO sources (id, title, tier, yaml_text)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    title=excluded.title,
                    tier=excluded.tier,
                    yaml_text=excluded.yaml_text
                """,
                (
                    record["id"],
                    record.get("title", ""),
                    record.get("tier", ""),
                    record.get("yaml_text", ""),
                ),
            )


def read_source_records_from_yaml(yaml_path: Path) -> list[dict[str, str]]:
    if not yaml_path.exists():
        return []

    records: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    raw_lines: list[str] = []
    for raw_line in yaml_path.read_text(encoding="utf-8").splitlines():
        stripped = raw_line.strip()
        if stripped.startswith("- id:"):
            if current is not None:
                current["yaml_text"] = "\n".join(raw_lines)
                records.append(current)
            current = {"id": clean_yaml_scalar(stripped.split(":", 1)[1])}
            raw_lines = [raw_line]
            continue
        if current is None:
            continue
        raw_lines.append(raw_line)
        if raw_line.startswith("  ") and ":" in stripped:
            key, value = stripped.split(":", 1)
            if key in {"title", "tier"}:
                current[key] = clean_yaml_scalar(value)

    if current is not None:
        current["yaml_text"] = "\n".join(raw_lines)
        records.append(current)
    return records


def clean_yaml_scalar(value: str) -> str:
    return value.strip().strip("\"'")
