# Silicon to Programmer Knowledge Base

This is a local-first knowledge base for understanding AI and semiconductor industry logic from first principles.

The working stack is:

```text
physical limits/materials
  -> manufacturing/process/integration
  -> circuit/IP primitives
  -> compute substrate
  -> memory/data movement
  -> interconnect/power/thermal
  -> execution architecture
  -> programming interface/DSL
  -> compiler/lowering
  -> runtime/execution system
  -> workload mapping
  -> scale-up system
  -> scale-out distributed system
  -> performance/cost/utilization model
  -> supply-chain/business logic
  -> market narrative
```

The source of truth is Markdown. A small local indexer turns concept files and graph edges into JSON that can power visual interfaces, search, and future agent harnesses.

## MVP Scope

- Source files: Markdown with simple YAML frontmatter.
- Graph files: JSONL edges plus wikilinks inside Markdown.
- Index output: `graph/concept-index.json`.
- First vertical slice: GPU architecture.
- Quality rule: important claims must point to source IDs in `sources/source-registry.yaml`.

## Layout

```text
knowledge-base/
  concepts/              # Human-readable concept pages
  graph/                 # Typed edges and generated graph index
  scripts/               # Local tooling
  sources/               # Source registry and citation metadata
  system/                # Operating rules, harnesses, templates, workflow docs
  use-cases/             # Recorded tests and user workflows
  inbox/                 # Raw notes and candidate sources
```

## Quick Start

Build the graph index:

```bash
python3 scripts/build_index.py
python3 scripts/validate_ontology.py
python3 scripts/validate_harnesses.py
```

Inspect the generated file:

```bash
less graph/concept-index.json
```

## Agent Entry Point

Agents should start with:

```text
system/agent-operating-manual.md
```

Then choose one harness from:

```text
system/harnesses/
```

The harness defines mutable surfaces, immutable surfaces, sensors, evaluators, logging, promotion rules, and human escalation boundaries.

## Concept Status

- `seed`: early scaffold, useful for navigation but not complete.
- `draft`: has a coherent explanation and candidate citations.
- `verified`: important claims have acceptable citations.
- `deprecated`: kept for history, not recommended as current knowledge.

## Link Policy

Use both link forms:

- Markdown links or wikilinks in concept prose for reading flow.
- `graph/edges.jsonl` for typed graph edges that a UI can render.

Example wikilink:

```text
[[hw.gpu.memory-hierarchy|GPU memory hierarchy]]
```

Example typed edge:

```json
{"source":"hw.gpu.overview","target":"hw.gpu.memory-hierarchy","type":"decomposes_into","confidence":"working"}
```

## Hierarchy Policy

Concept frontmatter carries visual hierarchy fields:

- `layer`: compact filter bucket.
- `layer_path`: tree path for visual grouping.
- `parent`: parent concept ID for collapsible views.
- `granularity`: map, overview, concept, mechanism, model, metric, or case-study.
- `concept_type`: what kind of thing the concept is.
- `scale_scope`: where the concept matters, from unit to ecosystem.
- `reasoning_roles`: how the concept helps explain systems or markets.
