# Cheap Model Drift Audit Harness

## Purpose

Audit low-cost or lightweight exploration runs for drift from required procedure, evaluator contracts, source registration, and artifact formats.

## Objective

Find repeatable ways cheap exploration runs deviate from the exploration-loop contract before those deviations enter permanent concepts, sources, graph edges, or run-ledger records.

## Mutable Surfaces

- `use-cases/`
- `temp/exploration-runs/<run-id>/drift-audit.md`
- `system/run-ledger.jsonl`, only for recording the audit run itself

## Immutable Surfaces

- `concepts/`
- `graph/edges.jsonl`
- `graph/concept-index.json`
- `sources/source-registry.yaml`
- `sources/source-registry.sqlite`
- `system/ontology.md`
- `system/source-quality.md`
- evaluator scripts and metric weights, unless using `meta-harness.md`

## Sensors

```bash
python3 scripts/build_index.py
python3 scripts/validate_ontology.py
python3 scripts/validate_harnesses.py
python3 scripts/evaluate_exploration.py temp/exploration-runs/<run-id> --allow-reject
```

Also inspect:

- candidate concept frontmatter and body format
- candidate source notes vs. manifest source IDs
- candidate edge file vs. manifest edge accounting
- evaluator schema version and scalar metric ranges
- whether next-step guidance respects rejection-streak policy

## Actuators

- Select three or more completed or synthetic low-cost exploration run folders.
- Run the evaluator against each run without promoting content.
- Classify drift by category: manifest mismatch, source mismatch, edge schema, metric range, ledger compatibility, prompt/stop behavior, and next-target guidance.
- Record drift findings and required harness/evaluator changes in a use-case file.
- Escalate repeated drift patterns to `meta-harness.md` before changing evaluator logic.

## Evaluator

The audit passes when:

- every evaluated run produces parseable evaluator JSON
- every scalar metric value is in the `0..1` range
- old run-ledger rows remain readable without migration
- rejected runs produce pivot or improvement guidance instead of stopping
- accepted-run milestone summaries do not ask for permission to continue in long-running mode
- source IDs are resolved through SQLite when present or YAML fallback when absent

The audit fails when any drift category appears without a recorded finding and follow-up action.

## Promotion Policy

This harness does not promote exploration artifacts into permanent concepts, sources, or graph edges. It only records audit results and recommended fixes.

## Logging Contract

Record:

- audit run id
- audited exploration run ids
- model class or cost tier when known
- evaluator decision and schema version for each run
- drift categories found
- corrective actions taken or recommended
- whether the issue belongs to exploration-loop, source storage, evaluator metrics, or agent instructions

## Human Controls

Ask before:

- changing evaluator thresholds or metric weights
- modifying ontology or source policy
- deleting or rewriting audited run artifacts
- treating cheap-model output as verified content

