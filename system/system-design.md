# System Design

## Goal

Build a local-first, agent-friendly knowledge base for AI and semiconductor industry understanding.

The durable reasoning path is:

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

## Design Principles

1. Markdown is the source of truth.
2. Graph JSON is generated, not manually edited.
3. Claims carry source IDs.
4. Technical mechanism is separated from market interpretation.
5. First-principle explanations come before company or stock conclusions.
6. Agents can add drafts, but humans approve `verified` status.

## Architecture

```text
concept Markdown files
        |
        v
frontmatter + layer_path + parent + wikilinks + claim source IDs
        |
        v
graph/edges.jsonl --------+
        |                 |
        v                 v
scripts/build_index.py -> graph/concept-index.json
                              |
                              v
future graph UI / search / query harness
```

## Core Artifacts

| Artifact | Role |
| --- | --- |
| `concepts/**/*.md` | Human-readable knowledge pages |
| `sources/source-registry.yaml` | Stable source IDs and quality tiers |
| `graph/edges.jsonl` | Typed graph edges for UI and reasoning |
| `graph/concept-index.json` | Generated graph/search artifact |
| `system/agent-operating-manual.md` | Required entry point for agents |
| `system/harnesses/*.md` | Bounded contracts for agent work |
| `system/ontology.md` | Layer, edge, and claim-status definitions |
| `system/source-quality.md` | Citation and verification standard |
| `system/ingestion-workflow.md` | Harness design for adding new knowledge |
| `use-cases/*.md` | Recorded user scenarios, tests, and quality evaluations |
| `system/run-ledger.jsonl` | Append-only operational history |

## Visual Interface Direction

The visual UI should consume `graph/concept-index.json`.

Each node already has:

- `id`
- `title`
- `status`
- `layer`
- `layer_path`
- `parent`
- `granularity`
- `concept_type`
- `scale_scope`
- `reasoning_roles`
- `tags`
- `path`
- `href`
- `sources`
- `wikilinks`

Each edge has:

- `source`
- `target`
- `type`
- `confidence`
- `notes`

The first UI should be read-only:

- node graph
- collapsible hierarchy from `parent`
- layer/tree clustering from `layer_path`
- click node to open Markdown file path
- filter by layer, status, tag, source, granularity, concept type, scale scope
- highlight unverified draft nodes

Editing can stay file-based until the content model stabilizes.

## Minimal Harnesses

### Knowledge Ingestion Harness

Defined in `system/harnesses/knowledge-ingestion.md`. Turns a paper, vendor doc, report, or user note into source entries, claims, concept updates, graph edges, and open questions.

### Concept Review Harness

Defined in `system/harnesses/concept-review.md`. Checks concept quality: source IDs, first-principle clarity, graph links, uncertainty marks, and technical/market separation.

### Query Harness

Defined in `system/harnesses/query-synthesis.md`.

Answers user questions by retrieving related concept pages and returning:

- mechanism
- citations
- related concepts
- market logic if applicable
- open questions

### Graph Export Harness

Defined in `system/harnesses/graph-export.md`. Regenerates graph JSON and validates node IDs, edge targets, ontology values, and source IDs.

### Ontology Review Harness

Defined in `system/harnesses/ontology-review.md`. Places concepts in the pattern-first ontology and prevents product-family-first organization.

### Meta-Harness

Defined in `system/harnesses/meta-harness.md`. Changes system design, ontology, harness contracts, policies, validators, or generated schema with stricter review.

## Accelerator Architecture Vertical Slice

The seed slice started with GPU concepts, but the central organization is accelerator-neutral. Current anchor concepts include:

- `hw.gpu.overview`
- `hw.gpu.simt`
- `hw.gpu.memory-hierarchy`
- `hw.gpu.thread-blocks-occupancy`
- `hw.gpu.tensor-cores`
- `programmer.roofline-model`
- `case.cerebras.wafer-scale-engine`
- `system.scale.scale-up-vs-scale-out`
- `software.control.dsl-compiler-runtime`

This slice is intentionally kept pattern-first:

```text
compute substrate -> memory/data movement -> execution/software control -> scaling -> workload fit -> industry logic
```

## Promotion Policy

| From | To | Requirement |
| --- | --- | --- |
| `seed` | `draft` | Coherent explanation, tags, related concepts, and candidate sources |
| `draft` | `verified` | Important claims cite acceptable sources and pass human review |
| any | `deprecated` | Superseded, misleading, or replaced by better concept |

## Next Build Steps

1. Add concept review script for missing sections and unsupported `verified` status.
2. Add neutral examples across TPU, Trainium, Gaudi, FPGA, custom ASIC, and rack-scale systems.
3. Split mixed concepts such as CUDA thread hierarchy vs GPU occupancy model.
4. Build a static graph viewer over `graph/concept-index.json`.
5. Add query examples that separate technical mechanism from market narrative.
