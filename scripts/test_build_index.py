#!/usr/bin/env python3
"""Focused tests for graph index generation helpers."""

from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

import build_index
import source_store


class BuildIndexTests(unittest.TestCase):
    def test_index_root_name_is_stable_for_linked_worktrees(self) -> None:
        worktree_root = Path("/tmp/exploration-loop-harness")

        self.assertEqual(build_index.index_root_name(worktree_root), "knowledge-base")

    def test_source_ids_are_read_from_sqlite_when_database_exists(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "source-registry.sqlite"
            with sqlite3.connect(db_path) as connection:
                connection.execute(
                    "CREATE TABLE sources (id TEXT PRIMARY KEY, title TEXT, tier TEXT)"
                )
                connection.execute(
                    "INSERT INTO sources (id, title, tier) VALUES (?, ?, ?)",
                    ("sqlite-source", "SQLite Source", "A"),
                )

            source_ids, errors = source_store.read_source_ids(
                db_path=db_path,
                yaml_path=Path(temp_dir) / "missing.yaml",
            )

        self.assertEqual(source_ids, {"sqlite-source"})
        self.assertEqual(errors, [])

    def test_source_ids_fall_back_to_yaml_when_sqlite_is_absent(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            yaml_path = Path(temp_dir) / "source-registry.yaml"
            yaml_path.write_text(
                "sources:\n- id: yaml-source\n  title: YAML Source\n  tier: B\n",
                encoding="utf-8",
            )

            source_ids, errors = source_store.read_source_ids(
                db_path=Path(temp_dir) / "missing.sqlite",
                yaml_path=yaml_path,
            )

        self.assertEqual(source_ids, {"yaml-source"})
        self.assertEqual(errors, [])

    def test_can_initialize_sqlite_from_yaml_source_ids(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            yaml_path = Path(temp_dir) / "source-registry.yaml"
            db_path = Path(temp_dir) / "source-registry.sqlite"
            yaml_path.write_text(
                "sources:\n- id: first-source\n  title: First\n  tier: A\n- id: second-source\n  title: Second\n  tier: B\n",
                encoding="utf-8",
            )

            source_store.initialize_sqlite_from_yaml(db_path=db_path, yaml_path=yaml_path)
            source_ids, errors = source_store.read_source_ids(db_path=db_path, yaml_path=yaml_path)
            with sqlite3.connect(db_path) as connection:
                row = connection.execute(
                    "SELECT title, tier FROM sources WHERE id = ?",
                    ("first-source",),
                ).fetchone()

        self.assertEqual(source_ids, {"first-source", "second-source"})
        self.assertEqual(row, ("First", "A"))
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
