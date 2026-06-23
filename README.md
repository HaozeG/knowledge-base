# Silicon to Programmer Knowledge Base

This is a local-first knowledge base for understanding AI and semiconductor industry logic from first principles.

The working stack is:

```text
silicon -> chip -> hardware/software system -> programmer -> industry and market logic
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
  system/                # Operating rules, templates, workflow docs
  inbox/                 # Raw notes and candidate sources
```

## Quick Start

Build the graph index:

```bash
python3 knowledge-base/scripts/build_index.py
```

Inspect the generated file:

```bash
less knowledge-base/graph/concept-index.json
```

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

