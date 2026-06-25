#!/usr/bin/env python3
"""Tests for the deterministic exploration evaluator."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "evaluate_exploration.py"
FIXTURES = Path("use-cases") / "fixtures" / "exploration-loop"
INDEX = FIXTURES / "index.json"
LEDGER = FIXTURES / "run-ledger.jsonl"


def load_module():
    spec = importlib.util.spec_from_file_location("evaluate_exploration", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ExplorationEvaluatorTests(unittest.TestCase):
    def setUp(self) -> None:
        if not SCRIPT.exists():
            self.fail(f"missing evaluator implementation: {SCRIPT}")

    def run_eval(self, fixture_name: str, *extra_args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                str(FIXTURES / fixture_name),
                "--index",
                str(INDEX),
                "--ledger",
                str(LEDGER),
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

    def load_fixture(self, fixture_name: str) -> dict:
        return json.loads((FIXTURES / fixture_name / "manifest.json").read_text(encoding="utf-8"))

    def load_index(self) -> dict:
        return json.loads(INDEX.read_text(encoding="utf-8"))

    def write_ledger(self, entries: list[dict]) -> Path:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        path = Path(temp_dir.name) / "run-ledger.jsonl"
        path.write_text(
            "\n".join(json.dumps(entry) for entry in entries) + "\n",
            encoding="utf-8",
        )
        return path

    def test_accepts_fixture_that_crosses_threshold(self) -> None:
        result = self.run_eval("accepted")
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["decision"], "accept")
        self.assertEqual(payload["creativity_score"], 1.05)
        self.assertEqual(payload["coverage_gap_score"], 0.3333)
        self.assertEqual(payload["category_staleness_multiplier"], 1.5)
        self.assertEqual(payload["quality_risk_penalty"], 0.0)
        self.assertEqual(payload["score"], 2.075)
        self.assertGreaterEqual(payload["score"], payload["threshold"])
        self.assertEqual(payload["hard_gate_codes"], [])
        self.assertEqual(payload["evaluator_schema_version"], 2)
        self.assertEqual(payload["run_history"]["direction_policy"], "continue")
        self.assertIn("metrics", payload)
        self.assertIn("next_targets", payload)
        self.assertIn("combined_score", payload)
        self.assertGreaterEqual(payload["combined_score"], 0.0)
        self.assertLessEqual(payload["combined_score"], 1.0)
        for metric in payload["metrics"].values():
            self.assertGreaterEqual(metric["value"], 0.0)
            self.assertLessEqual(metric["value"], 1.0)

    def test_combined_score_is_normalized_but_legacy_score_is_preserved(self) -> None:
        result = self.run_eval("accepted")
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)

        self.assertEqual(payload["score"], 2.075)
        self.assertGreater(payload["score"], 1.0)
        self.assertGreaterEqual(payload["combined_score"], 0.0)
        self.assertLessEqual(payload["combined_score"], 1.0)
        self.assertEqual(payload["metrics"]["score"]["value"], payload["combined_score"])
        self.assertEqual(payload["metrics"]["graph_connectivity"]["value"], 1.0)
        self.assertEqual(payload["metrics"]["graph_connectivity"]["raw_value"], 1.05)
        self.assertEqual(payload["metrics"]["graph_connectivity"]["range_status"], "clipped_high")

    def test_metric_outputs_are_bounded_across_decision_types(self) -> None:
        cases = [
            ("accepted", 0),
            ("rejected", 0),
            ("tier-d-source-fail", 1),
        ]
        for fixture_name, expected_returncode in cases:
            with self.subTest(fixture_name=fixture_name):
                result = self.run_eval(fixture_name, "--allow-reject")
                self.assertEqual(result.returncode, expected_returncode, result.stderr)
                payload = json.loads(result.stdout)
                self.assertGreaterEqual(payload["combined_score"], 0.0)
                self.assertLessEqual(payload["combined_score"], 1.0)
                for metric in payload["metrics"].values():
                    self.assertGreaterEqual(metric["value"], 0.0)
                    self.assertLessEqual(metric["value"], 1.0)

    def test_combined_score_clamps_component_ranges(self) -> None:
        module = load_module()

        high = module.combined_score(
            {
                "graph_connectivity": 999,
                "coverage_gap": 2,
                "evidence_strength": 1,
                "claim_hygiene": 1,
                "focus_score": 1,
                "rejection_recovery": 1,
                "guidance_quality": 1,
                "quality_risk": 1,
                "legacy_score": 4,
            }
        )
        low = module.combined_score(
            {
                "graph_connectivity": -1,
                "coverage_gap": -1,
                "evidence_strength": -1,
                "claim_hygiene": -1,
                "focus_score": -1,
                "rejection_recovery": -1,
                "guidance_quality": -1,
                "quality_risk": -1,
                "legacy_score": -1,
            }
        )

        self.assertEqual(high, 1.0)
        self.assertEqual(low, 0.0)

    def test_rejected_fixture_can_be_reported_without_failing_command(self) -> None:
        result = self.run_eval("rejected", "--allow-reject")
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["decision"], "reject")
        self.assertEqual(payload["creativity_score"], 0.25)
        self.assertEqual(payload["coverage_gap_score"], 0.2667)
        self.assertEqual(payload["category_staleness_multiplier"], 1.0)
        self.assertEqual(payload["quality_risk_penalty"], 0.0)
        self.assertEqual(payload["score"], 0.5167)
        self.assertLess(payload["score"], payload["threshold"])
        self.assertEqual(payload["hard_gate_codes"], [])

    def test_rejected_fixture_fails_without_allow_reject(self) -> None:
        result = self.run_eval("rejected")
        self.assertEqual(result.returncode, 2)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["decision"], "reject")

    def test_verified_status_hard_gate_failure_returns_error(self) -> None:
        result = self.run_eval("verified-status-fail", "--allow-reject")
        self.assertEqual(result.returncode, 1)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["decision"], "hard_gate_fail")
        self.assertEqual(payload["hard_gate_codes"], ["STATUS_FORBIDDEN"])

    def test_tier_d_source_hard_gate_failure_returns_error(self) -> None:
        result = self.run_eval("tier-d-source-fail", "--allow-reject")
        self.assertEqual(result.returncode, 1)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["decision"], "hard_gate_fail")
        self.assertEqual(payload["hard_gate_codes"], ["SOURCE_TIER_D"])

    def test_layer_mismatch_hard_gate_failure_returns_error(self) -> None:
        module = load_module()
        manifest = self.load_fixture("accepted")
        manifest["proposed_nodes"][0]["layer"] = "70-execution-architecture"

        payload = module.evaluate(manifest, self.load_index(), LEDGER, "2026-06-24")

        self.assertEqual(payload["decision"], "hard_gate_fail")
        self.assertEqual(payload["hard_gate_codes"], ["NODE_LAYER_MISMATCH"])

    def test_undeclared_source_hard_gate_failure_returns_error(self) -> None:
        module = load_module()
        manifest = self.load_fixture("accepted")
        manifest["proposed_nodes"][0]["sources"] = ["unregistered-social-post"]
        manifest["proposed_sources"] = []

        payload = module.evaluate(manifest, self.load_index(), LEDGER, "2026-06-24")

        self.assertEqual(payload["decision"], "hard_gate_fail")
        self.assertEqual(payload["hard_gate_codes"], ["SOURCE_NOT_DECLARED"])

    def test_unknown_edge_type_hard_gate_failure_returns_error(self) -> None:
        module = load_module()
        manifest = self.load_fixture("accepted")
        manifest["proposed_edges"][0]["type"] = "loosely_related_to"

        payload = module.evaluate(manifest, self.load_index(), LEDGER, "2026-06-24")

        self.assertEqual(payload["decision"], "hard_gate_fail")
        self.assertIn("EDGE_TYPE_UNKNOWN", payload["hard_gate_codes"])

    def test_candidate_edge_mismatch_requires_rejection_accounting(self) -> None:
        module = load_module()
        manifest = self.load_fixture("accepted")
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir)
            (run_dir / "candidate-edges.jsonl").write_text(
                "\n".join(json.dumps(edge) for edge in manifest["proposed_edges"])
                + "\n"
                + json.dumps(
                    {
                        "source": "chip.interconnect.on-package-fabric",
                        "target": "hw.gpu.memory-hierarchy",
                        "type": "depends_on",
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            payload = module.evaluate(manifest, self.load_index(), LEDGER, "2026-06-24", run_dir)

        self.assertEqual(payload["decision"], "hard_gate_fail")
        self.assertIn("CANDIDATE_EDGE_ACCOUNTING_MISMATCH", payload["hard_gate_codes"])

    def test_multiplier_is_capped(self) -> None:
        module = load_module()
        self.assertEqual(module.compute_staleness_multiplier(None, "2026-06-24"), 1.5)
        self.assertEqual(module.compute_staleness_multiplier("2026-06-24", "2026-06-24"), 1.0)
        self.assertEqual(module.compute_staleness_multiplier("2025-06-24", "2026-06-24"), 1.5)

    def test_mixed_old_and_new_ledger_rows_are_normalized_without_recomputing_scores(self) -> None:
        module = load_module()
        ledger = self.write_ledger(
            [
                {
                    "id": "old-accepted",
                    "timestamp": "2026-06-20T10:00:00",
                    "harness": "exploration-loop",
                    "status": "completed",
                    "decision": "accept",
                    "score": 2.025,
                    "artifacts": ["concepts/40-compute-substrate/example.md"],
                    "next_hint": "Legacy next hint.",
                },
                {
                    "id": "new-rejected",
                    "timestamp": "2026-06-21T10:00:00",
                    "harness": "exploration-loop",
                    "status": "completed",
                    "decision": "reject",
                    "evaluator_schema_version": 2,
                    "metrics": {"score": {"value": 0.5}},
                    "target_category": "70-execution-architecture",
                },
            ]
        )

        entries = module.load_ledger_entries(ledger)

        self.assertEqual(entries[0]["evaluator_schema_version"], 1)
        self.assertEqual(entries[0]["score"], 2.025)
        self.assertEqual(entries[0]["next_hint"], "Legacy next hint.")
        self.assertEqual(entries[1]["evaluator_schema_version"], 2)

    def test_three_same_direction_rejections_require_pivot_guidance(self) -> None:
        module = load_module()
        ledger = self.write_ledger(
            [
                {
                    "id": f"reject-{index}",
                    "timestamp": f"2026-06-2{index}T10:00:00",
                    "harness": "exploration-loop",
                    "status": "completed",
                    "decision": "reject",
                    "target_category": "70-execution-architecture",
                    "target_parent": "hw.gpu.overview",
                }
                for index in range(1, 4)
            ]
        )
        manifest = self.load_fixture("rejected")

        payload = module.evaluate(manifest, self.load_index(), ledger, "2026-06-24")

        self.assertEqual(payload["run_history"]["rejection_streak"], 3)
        self.assertEqual(payload["run_history"]["same_direction_rejection_streak"], 3)
        self.assertEqual(payload["run_history"]["direction_policy"], "pivot_required")
        self.assertTrue(payload["next_targets"])
        self.assertNotEqual(payload["next_targets"][0]["target_category"], "70-execution-architecture")

    def test_five_rejections_force_pivot_but_do_not_stop_the_loop(self) -> None:
        module = load_module()
        ledger = self.write_ledger(
            [
                {
                    "id": f"reject-{index}",
                    "timestamp": f"2026-06-{10 + index}T10:00:00",
                    "harness": "exploration-loop",
                    "status": "completed",
                    "decision": "reject",
                    "target_category": "70-execution-architecture",
                    "target_parent": "hw.gpu.overview",
                }
                for index in range(1, 6)
            ]
        )

        payload = module.evaluate(self.load_fixture("rejected"), self.load_index(), ledger, "2026-06-24")

        self.assertEqual(payload["run_history"]["direction_policy"], "forced_pivot")
        self.assertFalse(payload["run_history"]["should_stop"])
        self.assertIn("forced pivot", payload["run_history"]["guidance"].lower())

    def test_five_accepts_continue_without_permission_prompt(self) -> None:
        module = load_module()
        ledger = self.write_ledger(
            [
                {
                    "id": f"accept-{index}",
                    "timestamp": f"2026-06-{10 + index}T10:00:00",
                    "harness": "exploration-loop",
                    "status": "completed",
                    "decision": "accept",
                    "target_category": "40-compute-substrate",
                    "artifacts": ["concepts/40-compute-substrate/example.md"],
                }
                for index in range(1, 6)
            ]
        )

        payload = module.evaluate(self.load_fixture("accepted"), self.load_index(), ledger, "2026-06-24")

        self.assertEqual(payload["run_history"]["accept_streak"], 5)
        self.assertEqual(payload["run_history"]["direction_policy"], "continue")
        self.assertFalse(payload["run_history"]["should_stop"])
        self.assertNotIn("shall I proceed", payload["run_history"]["guidance"].lower())


if __name__ == "__main__":
    raise SystemExit(unittest.main())
