# Concept Review Harness

## Purpose

Evaluate concept pages for clarity, ontology fit, citation quality, and verification readiness.

## Objective

Prevent weak or unsupported knowledge from becoming central memory.

## Mutable Surfaces

- concept pages under review
- `graph/edges.jsonl`
- `use-cases/`
- `system/run-ledger.jsonl`

## Immutable Surfaces

- source quality policy
- ontology definitions
- validator scripts

## Sensors

```bash
python3 scripts/build_index.py
python3 scripts/validate_ontology.py
```

Review manually:

- first-principle explanation
- key terms
- verified claims
- source IDs
- open questions
- related concepts
- industry logic separation

## Actuators

- Downgrade status if claims are unsupported.
- Add `VERIFY`, `OPEN`, or `ASSUMPTION` marks.
- Add missing related links.
- Recommend splits.
- Record quality score in a use-case file.

## Evaluator

Score each concept from 1 to 5 on:

- ontology fit
- first-principle clarity
- source traceability
- uncertainty handling
- graph usefulness
- market/technical separation

## Promotion Policy

- No concept becomes `verified` without human approval.
- Vendor claims require cross-checking for verified status.
- Concepts with mixed layers should be split before promotion.

## Logging Contract

Record reviewed concept IDs, score, findings, missing evidence, and next actions.

## Human Controls

Escalate if a concept affects market conclusions, source policy, or ontology structure.

