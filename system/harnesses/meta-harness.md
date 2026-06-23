# Meta-Harness

## Purpose

Change the knowledge-base system itself: ontology, source policy, harness contracts, validators, index schema, or agent operating rules.

## Objective

Improve the system without corrupting evaluator integrity or weakening verification standards.

## Mutable Surfaces

- `system/`
- `scripts/`
- `README.md`
- `graph/concept-index.json`
- `use-cases/`
- `system/run-ledger.jsonl`

## Immutable Surfaces

- existing verified concepts unless separately reviewed
- raw source material
- source tiers, unless explicitly reviewed

## Sensors

```bash
python3 scripts/build_index.py
python3 scripts/validate_ontology.py
python3 scripts/validate_harnesses.py
git diff --check
```

## Actuators

- Change ontology definitions.
- Change harness contracts.
- Change validators.
- Add or revise templates.
- Record system-level tests.

## Evaluator

Pass when:

- object-level tasks still validate
- harnesses have required sections
- ontology remains product-neutral
- source policy is not weakened
- run ledger records the system change

Fail when:

- evaluator and content are changed without recording the meta-level reason
- product families become top-level ontology
- agent permissions become broader without human approval

## Promotion Policy

Meta changes should be reviewed more strictly than content changes. Keep new policies in draft if they are not yet tested.

## Logging Contract

Record motivation, changed system files, validator results, and any backward-incompatible schema changes.

## Human Controls

Ask before:

- weakening verification rules
- deleting harnesses
- changing generated index schema expected by a UI
- allowing agents to mark concepts verified

