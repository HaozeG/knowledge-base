# Exploration Loop Harness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a first-class exploration-loop harness with deterministic metric evaluation, temp-run isolation, automatic draft promotion policy, and validation coverage.

**Architecture:** Keep the autonomous search loop as a documented harness contract, not as a running agent daemon. Add one deterministic Python evaluator that reads the current graph index, run ledger, and one staged temp-run manifest, then emits JSON scoring output without mutating files. Update routing docs and harness validation so future agents can select and execute the harness consistently.

**Tech Stack:** Markdown harness docs, Python 3 standard library, JSON/JSONL fixtures, existing `scripts/build_index.py`, `scripts/validate_ontology.py`, and `scripts/validate_harnesses.py`.

---

## File Structure

- Create `scripts/evaluate_exploration.py`: pure scoring script for one exploration run folder. It reads `manifest.json`, `graph/concept-index.json`, and `system/run-ledger.jsonl`; writes JSON to stdout; exits nonzero when hard gates fail or score is below threshold unless `--allow-reject` is passed.
- Create `scripts/test_evaluate_exploration.py`: standard-library `unittest` suite for accepted, rejected, hard-gate, and staleness multiplier behavior.
- Create `use-cases/fixtures/exploration-loop/accepted/manifest.json`: sample accepted staged run fixture.
- Create `use-cases/fixtures/exploration-loop/rejected/manifest.json`: sample rejected staged run fixture.
- Create `use-cases/fixtures/exploration-loop/hard-gate-fail/manifest.json`: sample forbidden staged run fixture.
- Create `system/harnesses/exploration-loop.md`: new harness contract.
- Modify `scripts/validate_harnesses.py`: add `exploration-loop.md` to required harnesses.
- Modify `system/harnesses/README.md`: list the new harness.
- Modify `system/agent-operating-manual.md`: route long-running exploration tasks to the new harness.
- Modify `.gitignore`: ignore runtime `temp/` artifacts.
- Create `use-cases/2026-06-24-exploration-loop-harness.md`: recorded design/validation use case.

## Manifest Contract

Each staged run folder must contain `manifest.json`:

```json
{
  "run_id": "run-2026-06-24-sample",
  "target_category": "60-interconnect-power-thermal",
  "target_parent": "hw.gpu.overview",
  "description": "Explore on-package accelerator fabric concepts for a hypothetical AI accelerator.",
  "proposed_nodes": [
    {
      "id": "chip.interconnect.on-package-fabric",
      "title": "On-Package Accelerator Fabric",
      "status": "draft",
      "layer": "60-interconnect-power-thermal",
      "parent": "hw.gpu.overview",
      "concept_type": "interconnect_pattern",
      "sources": ["sample-primary-architecture-doc"],
      "claim_labels": ["supported", "open"]
    }
  ],
  "proposed_edges": [
    {
      "source": "chip.interconnect.on-package-fabric",
      "target": "hw.gpu.overview",
      "type": "depends_on",
      "confidence": "working"
    },
    {
      "source": "chip.interconnect.on-package-fabric",
      "target": "programmer.roofline-model",
      "type": "constrained_by",
      "confidence": "working"
    }
  ],
  "proposed_sources": [
    {
      "id": "sample-primary-architecture-doc",
      "tier": "A"
    }
  ]
}
```

## Scoring Formula

The evaluator computes:

```text
score =
  (creativity_score + coverage_gap_score)
  * category_staleness_multiplier
  - quality_risk_penalty
```

Initial fixed policy:

```text
acceptance_threshold = 1.0
1.0 <= category_staleness_multiplier <= 1.5
```

Hard gates fail when:

- a proposed node has `status` outside `seed` or `draft`;
- a proposed node id already exists;
- a proposed node has no source ids and no `open` or `speculative` claim label;
- a proposed source uses tier `D`;
- a proposed edge endpoint is neither an existing node nor a proposed node;
- `target_category` is empty;
- the manifest is invalid JSON.

## Task 1: Add Evaluator Tests And Fixtures

**Files:**
- Create: `scripts/test_evaluate_exploration.py`
- Create: `use-cases/fixtures/exploration-loop/accepted/manifest.json`
- Create: `use-cases/fixtures/exploration-loop/rejected/manifest.json`
- Create: `use-cases/fixtures/exploration-loop/hard-gate-fail/manifest.json`

- [ ] **Step 1: Create accepted fixture**

Create `use-cases/fixtures/exploration-loop/accepted/manifest.json`:

```json
{
  "run_id": "fixture-accepted",
  "target_category": "60-interconnect-power-thermal",
  "target_parent": "hw.gpu.overview",
  "description": "Accepted fixture with enough graph contribution under a stale category.",
  "proposed_nodes": [
    {
      "id": "chip.interconnect.on-package-fabric",
      "title": "On-Package Accelerator Fabric",
      "status": "draft",
      "layer": "60-interconnect-power-thermal",
      "parent": "hw.gpu.overview",
      "concept_type": "interconnect_pattern",
      "sources": ["sample-primary-architecture-doc"],
      "claim_labels": ["supported", "open"]
    }
  ],
  "proposed_edges": [
    {
      "source": "chip.interconnect.on-package-fabric",
      "target": "hw.gpu.overview",
      "type": "depends_on",
      "confidence": "working"
    },
    {
      "source": "chip.interconnect.on-package-fabric",
      "target": "programmer.roofline-model",
      "type": "constrained_by",
      "confidence": "working"
    },
    {
      "source": "hw.gpu.tensor-cores",
      "target": "chip.interconnect.on-package-fabric",
      "type": "depends_on",
      "confidence": "working"
    }
  ],
  "proposed_sources": [
    {
      "id": "sample-primary-architecture-doc",
      "tier": "A"
    }
  ]
}
```

- [ ] **Step 2: Create rejected fixture**

Create `use-cases/fixtures/exploration-loop/rejected/manifest.json`:

```json
{
  "run_id": "fixture-rejected",
  "target_category": "70-execution-architecture",
  "target_parent": "hw.gpu.overview",
  "description": "Rejected fixture with too little graph contribution.",
  "proposed_nodes": [
    {
      "id": "hw.execution.minor-scheduler-note",
      "title": "Minor Scheduler Note",
      "status": "seed",
      "layer": "70-execution-architecture",
      "parent": "hw.gpu.overview",
      "concept_type": "execution_model",
      "sources": [],
      "claim_labels": ["open"]
    }
  ],
  "proposed_edges": [],
  "proposed_sources": []
}
```

- [ ] **Step 3: Create hard-gate-fail fixture**

Create `use-cases/fixtures/exploration-loop/hard-gate-fail/manifest.json`:

```json
{
  "run_id": "fixture-hard-gate-fail",
  "target_category": "160-market-narrative",
  "target_parent": "hw.gpu.overview",
  "description": "Hard gate failure because verified promotion is forbidden.",
  "proposed_nodes": [
    {
      "id": "market.accelerator-guaranteed-winner",
      "title": "Accelerator Guaranteed Winner",
      "status": "verified",
      "layer": "160-market-narrative",
      "parent": "hw.gpu.overview",
      "concept_type": "market_narrative",
      "sources": ["sample-social-post"],
      "claim_labels": ["supported"]
    }
  ],
  "proposed_edges": [
    {
      "source": "market.accelerator-guaranteed-winner",
      "target": "hw.gpu.overview",
      "type": "explains_market_logic_for",
      "confidence": "working"
    }
  ],
  "proposed_sources": [
    {
      "id": "sample-social-post",
      "tier": "D"
    }
  ]
}
```

- [ ] **Step 4: Write failing evaluator tests**

Create `scripts/test_evaluate_exploration.py`:

```python
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
```

- [ ] **Step 5: Run tests to verify they fail**

Run:

```bash
python3 scripts/test_evaluate_exploration.py
```

Expected: FAIL or ERROR because `scripts/evaluate_exploration.py` does not exist.

- [ ] **Step 6: Commit fixtures and failing tests**

```bash
git add scripts/test_evaluate_exploration.py use-cases/fixtures/exploration-loop/
git commit -m "test: add exploration evaluator fixtures"
```

## Task 2: Implement Deterministic Evaluator

**Files:**
- Create: `scripts/evaluate_exploration.py`
- Test: `scripts/test_evaluate_exploration.py`

- [ ] **Step 1: Create evaluator script**

Create `scripts/evaluate_exploration.py`:

```python
#!/usr/bin/env python3
"""Evaluate one staged exploration run without mutating repository state."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
INDEX_FILE = ROOT / "graph" / "concept-index.json"
LEDGER_FILE = ROOT / "system" / "run-ledger.jsonl"
THRESHOLD = 1.0
ALLOWED_PROMOTION_STATUS = {"seed", "draft"}
LOW_RISK_SOURCE_TIERS = {"A", "B"}
MID_RISK_SOURCE_TIERS = {"C"}
HIGH_RISK_SOURCE_TIERS = {"D"}
SAFE_UNCERTAINTY_LABELS = {"open", "supported", "inference", "speculative"}


def load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"{path} not found") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path} invalid JSON: {exc}") from exc


def load_index(path: Path = INDEX_FILE) -> dict[str, Any]:
    return load_json(path)


def load_manifest(run_dir: Path) -> dict[str, Any]:
    return load_json(run_dir / "manifest.json")


def parse_date(value: str) -> date:
    return datetime.fromisoformat(value[:10]).date()


def latest_category_date(category: str, ledger_file: Path = LEDGER_FILE) -> str | None:
    if not ledger_file.exists():
        return None

    latest: date | None = None
    for line in ledger_file.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        artifacts = entry.get("artifacts") or []
        if not any(isinstance(item, str) and item.startswith(f"concepts/{category}/") for item in artifacts):
            continue
        timestamp = str(entry.get("timestamp", ""))
        if not timestamp:
            continue
        try:
            entry_date = parse_date(timestamp)
        except ValueError:
            continue
        if latest is None or entry_date > latest:
            latest = entry_date
    return latest.isoformat() if latest else None


def compute_staleness_multiplier(latest_date: str | None, today: str) -> float:
    if latest_date is None:
        return 1.5

    today_date = parse_date(today)
    latest = parse_date(latest_date)
    age_days = max((today_date - latest).days, 0)
    if age_days <= 14:
        return 1.0
    if age_days >= 180:
        return 1.5
    return round(1.0 + ((age_days - 14) / (180 - 14)) * 0.5, 4)


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def index_by_id(nodes: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(node.get("id")): node for node in nodes if node.get("id")}


def direct_child_count(nodes: list[dict[str, Any]], parent_id: str) -> int:
    return sum(1 for node in nodes if node.get("parent") == parent_id)


def category_count(nodes: list[dict[str, Any]], category: str) -> int:
    return sum(1 for node in nodes if node.get("layer") == category)


def hard_gate_errors(manifest: dict[str, Any], index: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    nodes = index.get("nodes") or []
    existing_ids = set(index_by_id(nodes))
    proposed_nodes = as_list(manifest.get("proposed_nodes"))
    proposed_edges = as_list(manifest.get("proposed_edges"))
    proposed_sources = as_list(manifest.get("proposed_sources"))
    proposed_ids = {str(node.get("id")) for node in proposed_nodes if isinstance(node, dict) and node.get("id")}

    if not manifest.get("target_category"):
        errors.append("target_category must not be empty")

    for node in proposed_nodes:
        if not isinstance(node, dict):
            errors.append("proposed_nodes entries must be objects")
            continue
        node_id = str(node.get("id", ""))
        status = str(node.get("status", ""))
        sources = [str(item) for item in as_list(node.get("sources")) if item]
        claim_labels = {str(item) for item in as_list(node.get("claim_labels")) if item}
        if not node_id:
            errors.append("proposed node missing id")
        if node_id in existing_ids:
            errors.append(f"proposed node already exists: {node_id}")
        if status not in ALLOWED_PROMOTION_STATUS:
            errors.append(f"proposed node {node_id} status {status} is forbidden; use seed or draft")
        if not sources and not (claim_labels & {"open", "speculative"}):
            errors.append(f"proposed node {node_id} needs sources or open/speculative claim labels")
        unknown_labels = claim_labels - SAFE_UNCERTAINTY_LABELS
        if unknown_labels:
            errors.append(f"proposed node {node_id} has unknown claim labels: {sorted(unknown_labels)}")

    for source in proposed_sources:
        if not isinstance(source, dict):
            errors.append("proposed_sources entries must be objects")
            continue
        source_id = str(source.get("id", ""))
        tier = str(source.get("tier", ""))
        if not source_id:
            errors.append("proposed source missing id")
        if tier in HIGH_RISK_SOURCE_TIERS:
            errors.append(f"proposed source {source_id} uses tier D, which cannot promote content")

    valid_ids = existing_ids | proposed_ids
    for edge in proposed_edges:
        if not isinstance(edge, dict):
            errors.append("proposed_edges entries must be objects")
            continue
        source = str(edge.get("source", ""))
        target = str(edge.get("target", ""))
        if source not in valid_ids:
            errors.append(f"proposed edge source not found: {source}")
        if target not in valid_ids:
            errors.append(f"proposed edge target not found: {target}")

    return errors


def quality_risk_penalty(manifest: dict[str, Any]) -> float:
    penalty = 0.0
    for source in as_list(manifest.get("proposed_sources")):
        if not isinstance(source, dict):
            penalty += 0.2
            continue
        tier = str(source.get("tier", ""))
        if tier in MID_RISK_SOURCE_TIERS:
            penalty += 0.15
        elif tier in HIGH_RISK_SOURCE_TIERS:
            penalty += 1.0
        elif tier not in LOW_RISK_SOURCE_TIERS:
            penalty += 0.25

    description = str(manifest.get("description", "")).lower()
    broad_markers = ["everything", "all topics", "broad survey", "market winner", "stock"]
    if any(marker in description for marker in broad_markers):
        penalty += 0.25
    return round(penalty, 4)


def creativity_score(manifest: dict[str, Any], index: dict[str, Any]) -> float:
    nodes = index.get("nodes") or []
    node_count = max(int(index.get("node_count") or len(nodes) or 1), 1)
    proposed_edges = [edge for edge in as_list(manifest.get("proposed_edges")) if isinstance(edge, dict)]
    proposed_nodes = [node for node in as_list(manifest.get("proposed_nodes")) if isinstance(node, dict)]
    proposed_ids = {str(node.get("id")) for node in proposed_nodes if node.get("id")}
    target_parent = str(manifest.get("target_parent") or "")

    useful_edges = 0
    for edge in proposed_edges:
        source = str(edge.get("source", ""))
        target = str(edge.get("target", ""))
        if source in proposed_ids or target in proposed_ids:
            useful_edges += 1

    edge_component = min(0.8, useful_edges / node_count * 8.0)
    hot_parent_bonus = 0.0
    if target_parent and direct_child_count(nodes, target_parent) >= 2 and proposed_nodes:
        hot_parent_bonus = 0.25
    return round(edge_component + hot_parent_bonus, 4)


def coverage_gap_score(manifest: dict[str, Any], index: dict[str, Any]) -> float:
    nodes = index.get("nodes") or []
    target_category = str(manifest.get("target_category") or "")
    proposed_nodes = [node for node in as_list(manifest.get("proposed_nodes")) if isinstance(node, dict)]
    if not target_category or not proposed_nodes:
        return 0.0

    existing_count = category_count(nodes, target_category)
    sparsity = max(0.0, 1.0 - min(existing_count, 10) / 10.0)
    contribution = min(len(proposed_nodes), 3) / 3.0
    return round(sparsity * contribution, 4)


def evaluate(manifest: dict[str, Any], index: dict[str, Any], today: str) -> dict[str, Any]:
    errors = hard_gate_errors(manifest, index)
    latest_date = latest_category_date(str(manifest.get("target_category") or ""))
    multiplier = compute_staleness_multiplier(latest_date, today)
    creativity = creativity_score(manifest, index)
    coverage_gap = coverage_gap_score(manifest, index)
    penalty = quality_risk_penalty(manifest)
    score = round((creativity + coverage_gap) * multiplier - penalty, 4)

    if errors:
        decision = "hard_gate_fail"
    elif score >= THRESHOLD:
        decision = "accept"
    else:
        decision = "reject"

    return {
        "run_id": manifest.get("run_id", ""),
        "decision": decision,
        "score": score,
        "threshold": THRESHOLD,
        "creativity_score": creativity,
        "coverage_gap_score": coverage_gap,
        "category_staleness_multiplier": multiplier,
        "category_latest_update": latest_date,
        "quality_risk_penalty": penalty,
        "hard_gate_errors": errors,
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir", type=Path, help="Directory containing manifest.json")
    parser.add_argument("--today", default=date.today().isoformat(), help="YYYY-MM-DD for deterministic tests")
    parser.add_argument("--allow-reject", action="store_true", help="Exit 0 for below-threshold rejections")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    try:
        index = load_index()
        manifest = load_manifest(args.run_dir)
        payload = evaluate(manifest, index, args.today)
    except ValueError as exc:
        print(json.dumps({"decision": "hard_gate_fail", "hard_gate_errors": [str(exc)]}, indent=2))
        return 1

    print(json.dumps(payload, indent=2, sort_keys=True))
    if payload["decision"] == "hard_gate_fail":
        return 1
    if payload["decision"] == "reject" and not args.allow_reject:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
```

- [ ] **Step 2: Run evaluator tests**

Run:

```bash
python3 scripts/test_evaluate_exploration.py
```

Expected: `OK`.

- [ ] **Step 3: Run accepted fixture directly**

Run:

```bash
python3 scripts/evaluate_exploration.py use-cases/fixtures/exploration-loop/accepted --today 2026-06-24
```

Expected: JSON output with `"decision": "accept"` and `"score"` greater than or equal to `1.0`.

- [ ] **Step 4: Run rejected fixture directly**

Run:

```bash
python3 scripts/evaluate_exploration.py use-cases/fixtures/exploration-loop/rejected --today 2026-06-24 --allow-reject
```

Expected: JSON output with `"decision": "reject"` and process exit `0`.

- [ ] **Step 5: Commit evaluator implementation**

```bash
git add scripts/evaluate_exploration.py scripts/test_evaluate_exploration.py
git commit -m "feat: add exploration evaluator"
```

## Task 3: Add Exploration Harness Contract

**Files:**
- Create: `system/harnesses/exploration-loop.md`

- [ ] **Step 1: Create harness document**

Create `system/harnesses/exploration-loop.md`:

```markdown
# Exploration Loop Harness

## Purpose

Run long-lived, focused exploration cycles that grow the knowledge base from a hardware/software/workload seed while keeping candidate work isolated until deterministic evaluation accepts it.

## Objective

Discover useful accelerator concepts, sources, and graph links without weakening source quality, ontology placement, or evaluator integrity.

## Mutable Surfaces

Temporary before acceptance:

- `temp/exploration-runs/<run-id>/`

Permanent after acceptance:

- `concepts/`
- `sources/source-registry.yaml`
- `graph/edges.jsonl`
- `inbox/candidate-sources/`
- `use-cases/`
- `graph/concept-index.json`
- `system/run-ledger.jsonl`

## Immutable Surfaces

- `system/`
- `scripts/`
- harness definitions
- validators
- metric weights and thresholds
- ontology definitions
- source-quality rules
- existing verified concepts
- raw source material, unless copied into candidate notes

## Sensors

```bash
python3 scripts/build_index.py
python3 scripts/validate_ontology.py
python3 scripts/validate_harnesses.py
python3 scripts/evaluate_exploration.py temp/exploration-runs/<run-id>
```

Also inspect:

- staged `manifest.json`
- candidate concept drafts
- candidate source notes
- candidate edge additions
- metric JSON output
- previous run guidance

## Actuators

- Select one focused exploration target.
- Start one clean-context subagent with only the seed files, harness contract, ontology/source rules, related concepts, and previous guidance.
- Search focused, trustworthy resources for one component, mechanism, workload mapping question, or software-control question.
- Stage temporary candidate artifacts under `temp/exploration-runs/<run-id>/`.
- Promote accepted draft content into permanent knowledge-base locations.
- Regenerate `graph/concept-index.json`.
- Append run-ledger entries and next-step directions.
- Quarantine or remove rejected temporary candidate artifacts.

## Evaluator

Hard gates pass only when:

- candidate content follows ontology and source policy
- promoted concepts are only `seed` or `draft`
- important factual claims have source IDs or explicit uncertainty labels
- source tiers are conservative
- product-family-first placement is rejected
- validator commands pass
- the loop does not modify system rules, validators, metric weights, or ontology

The fixed score is:

```text
score =
  (creativity_score + coverage_gap_score)
  * category_staleness_multiplier
  - quality_risk_penalty
```

Initial acceptance policy:

```text
score >= 1.0
1.0 <= category_staleness_multiplier <= 1.5
```

Changing the threshold, weights, or scoring formula requires the meta-harness.

## Promotion Policy

If hard gates pass and score crosses the fixed threshold, promote staged artifacts automatically under the knowledge-ingestion contract.

If hard gates fail or score is below threshold:

- record a compact rejection log
- remove or quarantine unpromoted candidate files
- try a new focused target

After five consecutive attempts fail to proceed, select the sparsest or stalest category and record an escalation hint that a higher-intelligence model may be useful.

## Logging Contract

For every attempt, record:

- timestamp
- run id
- selected target
- source summary
- candidate artifacts
- metric output
- accept, reject, interrupted, or failed decision
- promotion actions, if any
- next-step guidance

Accepted runs append to `system/run-ledger.jsonl`. Rejected or interrupted runs keep compact logs under the run folder unless the user asks to preserve more detail.

## Human Controls

The loop continues until the user asks it to stop.

Ask before:

- changing harnesses, validators, metric weights, ontology, or source policy
- marking concepts `verified`
- upgrading source tiers
- deleting or merging permanent concepts
- adding market or investment conclusions
- broadening a single attempt beyond one focused component or mechanism
```

- [ ] **Step 2: Commit harness document**

```bash
git add system/harnesses/exploration-loop.md
git commit -m "docs: add exploration loop harness"
```

## Task 4: Route And Validate The New Harness

**Files:**
- Modify: `scripts/validate_harnesses.py`
- Modify: `system/harnesses/README.md`
- Modify: `system/agent-operating-manual.md`

- [ ] **Step 1: Update harness validator required files**

In `scripts/validate_harnesses.py`, change `REQUIRED_HARNESS_FILES` to:

```python
REQUIRED_HARNESS_FILES = {
    "knowledge-ingestion.md",
    "ontology-review.md",
    "concept-review.md",
    "query-synthesis.md",
    "graph-export.md",
    "meta-harness.md",
    "exploration-loop.md",
}
```

- [ ] **Step 2: Update harness README table**

In `system/harnesses/README.md`, replace the Available Harnesses table with:

```markdown
| Harness | Purpose |
| --- | --- |
| `knowledge-ingestion.md` | Convert sources and notes into concept drafts |
| `ontology-review.md` | Place concepts and improve hierarchy |
| `concept-review.md` | Review concept quality and verification readiness |
| `query-synthesis.md` | Answer questions from the KB with citations and uncertainty |
| `graph-export.md` | Regenerate and validate graph/index artifacts |
| `exploration-loop.md` | Run long-lived, metric-gated autonomous exploration with temporary staging |
| `meta-harness.md` | Change the system design, ontology, policies, harnesses, or validators |
```

- [ ] **Step 3: Update agent manual harness selection**

In `system/agent-operating-manual.md`, replace the Harness Selection table with:

```markdown
| Task | Harness |
| --- | --- |
| Add or process a source | `system/harnesses/knowledge-ingestion.md` |
| Place or reorganize concepts | `system/harnesses/ontology-review.md` |
| Review concept quality and verification readiness | `system/harnesses/concept-review.md` |
| Answer a user question from the KB | `system/harnesses/query-synthesis.md` |
| Regenerate graph/index artifacts | `system/harnesses/graph-export.md` |
| Run long-lived autonomous exploration from a hardware/software/workload seed | `system/harnesses/exploration-loop.md` |
| Change ontology, policies, evaluators, or harnesses | `system/harnesses/meta-harness.md` |
```

- [ ] **Step 4: Add permission model note**

In `system/agent-operating-manual.md`, under "Allowed without extra approval", add:

```markdown
- Create temporary exploration artifacts under `temp/exploration-runs/<run-id>/`.
- Promote exploration artifacts to draft content when the exploration-loop hard gates and fixed score pass.
```

Under "Approval-gated", add:

```markdown
- Change exploration-loop metric weights, thresholds, or evaluator logic.
```

- [ ] **Step 5: Run harness validator**

Run:

```bash
python3 scripts/validate_harnesses.py
```

Expected: `Harness validation passed for 7 harnesses`.

- [ ] **Step 6: Commit routing and validator updates**

```bash
git add scripts/validate_harnesses.py system/harnesses/README.md system/agent-operating-manual.md
git commit -m "docs: route exploration loop harness"
```

## Task 5: Ignore Runtime Temp Artifacts

**Files:**
- Modify: `.gitignore`

- [ ] **Step 1: Add temp ignore rule**

Append to `.gitignore`:

```gitignore
temp/
```

- [ ] **Step 2: Verify fixtures remain tracked**

Run:

```bash
git status --short --ignored
```

Expected: output shows no ignored `use-cases/fixtures/` files. Runtime `temp/` is ignored only when present.

- [ ] **Step 3: Commit gitignore update**

```bash
git add .gitignore
git commit -m "chore: ignore exploration temp artifacts"
```

## Task 6: Record Use Case

**Files:**
- Create: `use-cases/2026-06-24-exploration-loop-harness.md`

- [ ] **Step 1: Create use-case record**

Create `use-cases/2026-06-24-exploration-loop-harness.md`:

```markdown
# Exploration Loop Harness Use Case

Date: 2026-06-24

## Goal

Verify that the knowledge-base design can support a long-running harness that starts from a new hardware accelerator design, stages temporary exploration results, evaluates graph-growth usefulness, and promotes acceptable draft content without human approval for each normal draft promotion.

## Scenario

The user describes a hardware accelerator, its software stack, and target workloads. The exploration loop chooses one focused component or mechanism, starts a clean-context subagent, searches trustworthy sources, stages temporary candidate artifacts, evaluates the attempt, and either promotes or rejects the run.

## Accepted Design Decisions

- Temporary artifacts are allowed only under `temp/exploration-runs/<run-id>/`.
- Permanent draft promotion is automatic when hard gates pass and the fixed score crosses threshold.
- The score is `(creativity_score + coverage_gap_score) * category_staleness_multiplier - quality_risk_penalty`.
- `category_staleness_multiplier` is capped between `1.0` and `1.5`.
- Metric weights and thresholds can change only through the meta-harness.
- Each exploration attempt uses one clean-context subagent.
- Five consecutive failures trigger fallback to the sparsest or stalest category and an escalation hint.

## Validation Commands

```bash
python3 scripts/test_evaluate_exploration.py
python3 scripts/evaluate_exploration.py use-cases/fixtures/exploration-loop/accepted --today 2026-06-24
python3 scripts/evaluate_exploration.py use-cases/fixtures/exploration-loop/rejected --today 2026-06-24 --allow-reject
python3 scripts/build_index.py
python3 scripts/validate_ontology.py
python3 scripts/validate_harnesses.py
git diff --check
```

## Expected Result

The accepted fixture crosses the fixed threshold. The rejected fixture reports a below-threshold rejection without mutation. The hard-gate fixture fails because verified promotion and tier-D source promotion are forbidden.
```

- [ ] **Step 2: Commit use-case record**

```bash
git add use-cases/2026-06-24-exploration-loop-harness.md
git commit -m "docs: record exploration loop use case"
```

## Task 7: Run Full Verification

**Files:**
- Verify all changed files.

- [ ] **Step 1: Run evaluator unit tests**

```bash
python3 scripts/test_evaluate_exploration.py
```

Expected: `OK`.

- [ ] **Step 2: Run accepted evaluator fixture**

```bash
python3 scripts/evaluate_exploration.py use-cases/fixtures/exploration-loop/accepted --today 2026-06-24
```

Expected: JSON with `"decision": "accept"`.

- [ ] **Step 3: Run rejected evaluator fixture**

```bash
python3 scripts/evaluate_exploration.py use-cases/fixtures/exploration-loop/rejected --today 2026-06-24 --allow-reject
```

Expected: JSON with `"decision": "reject"`.

- [ ] **Step 4: Run index build**

```bash
python3 scripts/build_index.py
```

Expected: `Wrote graph/concept-index.json with ... nodes and ... edges`.

- [ ] **Step 5: Run ontology validation**

```bash
python3 scripts/validate_ontology.py
```

Expected: `Ontology validation passed for ... concepts`.

- [ ] **Step 6: Run harness validation**

```bash
python3 scripts/validate_harnesses.py
```

Expected: `Harness validation passed for 7 harnesses`.

- [ ] **Step 7: Run whitespace check**

```bash
git diff --check
```

Expected: no output and exit code `0`.

- [ ] **Step 8: Inspect final diff**

```bash
git diff --stat HEAD
git status --short
```

Expected: only intended exploration-loop implementation files are modified or added.

- [ ] **Step 9: Final commit if needed**

If any verification-only adjustments remain uncommitted after prior task commits:

```bash
git add .
git commit -m "chore: verify exploration loop harness"
```

If working tree is clean, skip this step.

## Self-Review Checklist

- The new harness contract has every section required by `scripts/validate_harnesses.py`.
- The new harness mentions `python3 scripts/build_index.py`.
- The agent manual routes long-running hardware/software/workload exploration to `exploration-loop.md`.
- Runtime temp files are ignored, while committed fixtures live under `use-cases/fixtures/`.
- The evaluator is deterministic, pure, and emits JSON to stdout.
- The evaluator does not perform online search, model calls, or mutations.
- The evaluator enforces hard gates before accepting a scored run.
- The staleness multiplier is capped between `1.0` and `1.5`.
- The fixed threshold is `score >= 1.0`.
- Changing metric weights or thresholds requires the meta-harness.
- Full verification commands pass before reporting completion.
