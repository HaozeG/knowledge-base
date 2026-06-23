# Ontology Review Harness

## Purpose

Place concepts in the central pattern-first ontology and improve hierarchy without making the system GPU-centric or product-centric.

## Objective

Maintain a stable ontology that supports GPU, TPU, Cerebras, Trainium, Gaudi, FPGA, custom ASIC, compiler/runtime, scale-up, and scale-out concepts.

## Mutable Surfaces

- `concepts/`
- `graph/edges.jsonl`
- `use-cases/`
- `system/run-ledger.jsonl`

## Immutable Surfaces

- `system/ontology.md`, unless using `meta-harness.md`
- `scripts/validate_ontology.py`, unless using `meta-harness.md`
- `system/source-quality.md`

## Sensors

```bash
python3 scripts/build_index.py
python3 scripts/validate_ontology.py
```

Also inspect:

- concept frontmatter
- `layer_path`
- `parent`
- `secondary_layers`
- `concept_type`
- `scale_scope`
- `reasoning_roles`

## Actuators

- Move concept files into neutral layer directories.
- Adjust frontmatter placement fields.
- Add typed graph edges.
- Record placement tests under `use-cases/`.

## Evaluator

Pass when:

- files live under `concepts/<layer>/`
- product families are case studies, not top-level layers
- scale-up and scale-out concepts are distinct
- DSL, compiler, runtime, and workload mapping are distinct
- validator passes

Fail when:

- a product family becomes the organizing root
- GPU-specific directory structure hides the general ontology
- mixed concepts cannot be queried cleanly by layer or scale scope

## Promotion Policy

- Keep ambiguous concepts as `draft`.
- Split concepts when one page mixes different concept types or layers.
- Use case-study pages for products and companies.

## Logging Contract

Record changed concept IDs, placement decisions, unresolved ambiguities, and validation results.

## Human Controls

Use `meta-harness.md` and ask for approval before changing allowed ontology values.

