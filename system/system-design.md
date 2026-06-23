# System Design

## Goal

Build a local-first, agent-friendly knowledge base for AI and semiconductor industry understanding.

The durable reasoning path is:

```text
silicon constraint -> chip architecture -> HW/SW system -> programmer model -> industry logic -> market narrative
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
frontmatter + wikilinks + claim source IDs
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
| `system/ontology.md` | Layer, edge, and claim-status definitions |
| `system/source-quality.md` | Citation and verification standard |
| `system/ingestion-workflow.md` | Harness design for adding new knowledge |
| `system/run-ledger.jsonl` | Append-only operational history |

## Visual Interface Direction

The visual UI should consume `graph/concept-index.json`.

Each node already has:

- `id`
- `title`
- `status`
- `layer`
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
- click node to open Markdown file path
- filter by layer, status, tag, source
- highlight unverified draft nodes

Editing can stay file-based until the content model stabilizes.

## Minimal Harnesses

### Knowledge Ingestion Harness

Turns a paper, vendor doc, report, or user note into source entries, claims, concept updates, graph edges, and open questions.

### Concept Review Harness

Checks concept quality: source IDs, first-principle clarity, graph links, uncertainty marks, and technical/market separation.

### Query Harness

Answers user questions by retrieving related concept pages and returning:

- mechanism
- citations
- related concepts
- market logic if applicable
- open questions

### Graph Export Harness

Regenerates graph JSON and validates node IDs, edge targets, and source IDs.

## GPU Architecture Vertical Slice

The seed slice starts with:

- `hw.gpu.overview`
- `hw.gpu.simt`
- `hw.gpu.memory-hierarchy`
- `hw.gpu.thread-blocks-occupancy`
- `hw.gpu.tensor-cores`
- `programmer.roofline-model`

This slice is intentionally chosen because GPU architecture connects all target levels:

```text
chip resources -> GPU system architecture -> CUDA/programmer model -> AI workload fit -> industry logic
```

## Promotion Policy

| From | To | Requirement |
| --- | --- | --- |
| `seed` | `draft` | Coherent explanation, tags, related concepts, and candidate sources |
| `draft` | `verified` | Important claims cite acceptable sources and pass human review |
| any | `deprecated` | Superseded, misleading, or replaced by better concept |

## Next Build Steps

1. Add source-registry validation for source quality tier and required fields.
2. Add concept review script for missing sections and unsupported `verified` status.
3. Add more GPU concepts: SM, warp scheduler, HBM, NVLink, CUDA libraries, kernel launch overhead.
4. Build a static graph viewer over `graph/concept-index.json`.
5. Add query examples that separate technical mechanism from market narrative.

