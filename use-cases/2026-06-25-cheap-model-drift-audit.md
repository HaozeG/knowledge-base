---
id: use-case.cheap-model-drift-audit-2026-06-25
title: Cheap Model Exploration Drift Audit
status: recorded
date: 2026-06-25
harness: cheap-model-drift-audit
source_ids: []
related_concepts: [hw.riscv.vector-extension, hw.riscv.matrix-extension-proposals, workload.ai.rvv-kernel-patterns]
---

# Cheap Model Exploration Drift Audit

Date: 2026-06-25

## Goal

Replay three local exploration run traces as low-cost exploration outputs and check where they drift from the required evaluator, artifact, and continuation contracts.

## Audited Runs

| Run | Evaluator decision | Combined score | Drift found |
| --- | --- | ---: | --- |
| `run-2026-06-25-001` | `hard_gate_fail` | 0.8460 | `NODE_ALREADY_EXISTS`; `CANDIDATE_EDGE_ACCOUNTING_MISMATCH` because 8 candidate edges became 5 manifest edges without explicit rejected-edge accounting |
| `run-2026-06-25-002` | `hard_gate_fail` | 0.8423 | `NODE_ALREADY_EXISTS` when replayed after promotion |
| `run-2026-06-25-005` | `hard_gate_fail` | 0.8605 | `NODE_ALREADY_EXISTS` when replayed after promotion |

## Findings

- Metric output is normalized defensively: each scalar metric `value` and `combined_score` stays in `0..1`, while each metric also keeps `raw_value` and `range_status` so clipping does not hide metric-design drift.
- The legacy top-level `score` remains historical compatibility output and can exceed `1`; it must not be treated as the normalized quality score.
- Replaying already-promoted runs against the current graph correctly fails with `NODE_ALREADY_EXISTS`; auditors should distinguish replay-state drift from original-run quality.
- Run `001` exposed real format drift: `candidate-edges.jsonl` had more entries than `manifest.proposed_edges`, and the omitted edges were not represented as rejected artifacts with reasons.
- The evaluator reports `accept_streak: 5` with `direction_policy: continue` and `should_stop: false`, so five accepted runs are not a stopping condition.
- SQLite source lookup was initialized from YAML and `build_index.py` succeeded with `sources/source-registry.sqlite` present.

## Corrective Actions

- Added `system/harnesses/cheap-model-drift-audit.md` for periodic low-cost run audits.
- Added metric-bound tests across accepted, rejected, and hard-gate outputs.
- Added combined-score normalization tests for extreme component values, plus raw/range-status checks for clipped metrics.
- Initialized `sources/source-registry.sqlite` from `sources/source-registry.yaml`.

## Validation Commands

```bash
python3 scripts/evaluate_exploration.py temp/exploration-runs/run-2026-06-25-001 --today 2026-06-25 --allow-reject
python3 scripts/evaluate_exploration.py temp/exploration-runs/run-2026-06-25-002 --today 2026-06-25 --allow-reject
python3 scripts/evaluate_exploration.py temp/exploration-runs/run-2026-06-25-005 --today 2026-06-25 --allow-reject
python3 scripts/test_evaluate_exploration.py
python3 scripts/sync_sources.py --from-yaml
python3 scripts/build_index.py
python3 scripts/validate_harnesses.py
```
