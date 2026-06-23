# Graph Export Harness

## Purpose

Regenerate and validate graph/index artifacts for visual UI, search, and query harnesses.

## Objective

Keep generated graph artifacts synchronized with Markdown concepts and typed edges.

## Mutable Surfaces

- `graph/concept-index.json`
- `system/run-ledger.jsonl`

## Immutable Surfaces

- concept Markdown files
- `graph/edges.jsonl`
- source registry
- ontology
- validator scripts

## Sensors

```bash
python3 scripts/build_index.py
python3 scripts/validate_ontology.py
```

## Actuators

- Regenerate `graph/concept-index.json`.
- Report node count, edge count, source count, and validation errors.
- Append run-ledger entry if the export is part of a larger task.

## Evaluator

Pass when:

- indexer exits successfully
- `errors` in `concept-index.json` is empty
- ontology validator passes
- generated index includes grouping fields for visual filters

## Promotion Policy

Generated artifacts are kept when validation passes. If validation fails, fix source files rather than hand-editing generated JSON.

## Logging Contract

Record counts and command results when graph export is part of an agent run.

## Human Controls

None for regeneration. Ask before changing schema shape consumed by external tools.

