#!/usr/bin/env python3
"""Focused tests for graph index generation helpers."""

from __future__ import annotations

import unittest
from pathlib import Path

import build_index


class BuildIndexTests(unittest.TestCase):
    def test_index_root_name_is_stable_for_linked_worktrees(self) -> None:
        worktree_root = Path("/tmp/exploration-loop-harness")

        self.assertEqual(build_index.index_root_name(worktree_root), "knowledge-base")


if __name__ == "__main__":
    unittest.main()
