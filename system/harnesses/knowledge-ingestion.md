# Knowledge Ingestion Harness

## Purpose

Convert papers, vendor docs, industry reports, and user notes into source entries, concept drafts, graph edges, and open questions.

## Objective

Improve knowledge coverage without degrading citation quality or provenance.

## Mutable Surfaces

- `concepts/`
- `sources/source-registry.sqlite`, when present
- `sources/source-registry.yaml` compatibility export
- `graph/edges.jsonl`
- `inbox/candidate-sources/`
- `use-cases/`
- `system/run-ledger.jsonl`

## Immutable Surfaces

- `system/source-quality.md`
- `system/ontology.md`
- `system/harnesses/`
- validator scripts
- raw source material, unless the user explicitly asks for cleanup

## Sensors

```bash
python3 scripts/build_index.py
python3 scripts/validate_ontology.py
```

Also inspect:

- related concept pages
- source registry entry
- candidate-source note
- graph edge changes

## Actuators

- Register source with conservative tier.
- Create candidate-source note.
- Create or update concept drafts.
- Add typed edges.
- Add open questions.
- Append run-ledger entry.

## Evaluator

Pass when:

- important claims cite source IDs
- source tier is conservative
- new concepts use central ontology fields
- graph/index validation passes
- unsupported claims are marked `open`, `supported`, `inference`, or `speculative`

Fail when:

- product marketing claims are marked verified
- source IDs are missing
- concept placement is product-family-first
- technical facts and market conclusions are mixed

## Promotion Policy

- `seed` to `draft`: explanation, ontology fields, related concepts, and candidate sources exist.
- `draft` to `verified`: human approval plus strong source evidence.
- unresolved contradictions: record open question, do not promote.

## Logging Contract

Append one `system/run-ledger.jsonl` entry with source IDs, changed concepts, generated artifacts, and next verification hints.

## Human Controls

Ask for approval before:

- upgrading source tier
- marking verified
- deleting or merging concepts
- adding stock or company conclusions
