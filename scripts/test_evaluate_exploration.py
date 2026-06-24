#!/usr/bin/env python3
"""Tests for the deterministic exploration evaluator."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "evaluate_exploration.py"
FIXTURES = ROOT / "use-cases" / "fixtures" / "exploration-loop"


def load_module():
    spec = importlib.util.spec_from_file_location("evaluate_exploration", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ExplorationEvaluatorTests(unittest.TestCase):
    def run_eval(self, fixture_name: str, *extra_args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                str(FIXTURES / fixture_name),
                "--today",
                "2026-06-24",
                *extra_args,
            ],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

    def test_accepts_fixture_that_crosses_threshold(self) -> None:
        result = self.run_eval("accepted")
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["decision"], "accept")
        self.assertGreaterEqual(payload["score"], payload["threshold"])
        self.assertGreaterEqual(payload["category_staleness_multiplier"], 1.0)
        self.assertLessEqual(payload["category_staleness_multiplier"], 1.5)
        self.assertEqual(payload["hard_gate_errors"], [])

    def test_rejected_fixture_can_be_reported_without_failing_command(self) -> None:
        result = self.run_eval("rejected", "--allow-reject")
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["decision"], "reject")
        self.assertLess(payload["score"], payload["threshold"])
        self.assertEqual(payload["hard_gate_errors"], [])

    def test_rejected_fixture_fails_without_allow_reject(self) -> None:
        result = self.run_eval("rejected")
        self.assertEqual(result.returncode, 2)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["decision"], "reject")

    def test_hard_gate_failure_returns_error(self) -> None:
        result = self.run_eval("hard-gate-fail", "--allow-reject")
        self.assertEqual(result.returncode, 1)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["decision"], "hard_gate_fail")
        self.assertTrue(any("verified" in item for item in payload["hard_gate_errors"]))
        self.assertTrue(any("tier D" in item for item in payload["hard_gate_errors"]))

    def test_multiplier_is_capped(self) -> None:
        module = load_module()
        self.assertEqual(module.compute_staleness_multiplier(None, "2026-06-24"), 1.5)
        self.assertEqual(module.compute_staleness_multiplier("2026-06-24", "2026-06-24"), 1.0)
        self.assertEqual(module.compute_staleness_multiplier("2025-06-24", "2026-06-24"), 1.5)


if __name__ == "__main__":
    raise SystemExit(unittest.main())
