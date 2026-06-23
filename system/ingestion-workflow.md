# Ingestion Workflow Design

This document defines the draft workflow for turning papers, architecture docs, reports, and user notes into durable knowledge-base content.

## Objective

Convert new material into concept pages, claim-level citations, graph edges, and open questions while preserving provenance.

## Environment

- Source of truth: `knowledge-base/concepts/**/*.md`
- Source registry: `knowledge-base/sources/source-registry.yaml`
- Graph edges: `knowledge-base/graph/edges.jsonl`
- Raw inputs: `knowledge-base/inbox/`
- Generated index: `knowledge-base/graph/concept-index.json`
- Ledger: `knowledge-base/system/run-ledger.jsonl`

## Harness Contract

```yaml
name: knowledge-ingestion
purpose: convert trusted sources and notes into durable concept knowledge
objective: improve coverage and citation quality without degrading source provenance
users: human owner starts and accepts ingestion
mutable_surfaces:
  - knowledge-base/concepts/
  - knowledge-base/graph/edges.jsonl
  - knowledge-base/sources/source-registry.yaml
  - knowledge-base/system/run-ledger.jsonl
immutable_surfaces:
  - raw downloaded source files unless explicitly approved
  - source quality policy during ordinary ingestion
  - generated evaluator scripts during content generation
sensors:
  - source registry checks
  - frontmatter parser
  - graph indexer
  - citation completeness review
actuators:
  - create concept draft
  - update concept page
  - add graph edge
  - register source
  - append ledger entry
promotion_policy:
  - seed to draft when explanation, related concepts, and candidate citations exist
  - draft to verified only after important claims pass source-quality review
rollback_policy:
  - git diff is the rollback boundary
  - generated graph index can be regenerated
human_controls:
  - user approves source-tier changes
  - user approves verified status
  - user resolves contradictory sources
```

## Loop

1. **Capture**
   - Put raw note, URL, PDF path, or excerpt under `inbox/`.
   - Register bibliographic metadata and quality tier in `sources/source-registry.yaml`.

2. **Triage**
   - Identify whether the input is primary technical evidence, industry interpretation, market narrative, or unverified lead.
   - Decide which concepts it touches.
   - For online articles, ignore page-level AI-generated summaries unless the task is explicitly about evaluating that summary.

3. **Extract Claims**
   - Extract claims as atomic statements.
   - Assign each claim a status: `verified`, `supported`, `inference`, `speculative`, or `open`.
   - Attach source IDs immediately.

4. **Map to Concepts**
   - Update existing concept pages when possible.
   - Create a new concept only when the idea has stable identity and likely future reuse.
   - Keep market interpretation separate from technical mechanism.

5. **Add Graph Edges**
   - Add typed edges to `graph/edges.jsonl`.
   - Add wikilinks in prose for reader navigation.

6. **Evaluate**
   - Run the local indexer.
   - Check for missing IDs, duplicate IDs, broken edges, and unsupported important claims.
   - Keep the generated JSON out of conceptual review unless it fails structurally.

7. **Record**
   - Append the ingestion result to `system/run-ledger.jsonl`.
   - Include source IDs, changed concepts, unresolved questions, and next hints.

## Reviewer Checklist

- Does each important claim have a source ID?
- Is the source tier strong enough for the claim?
- Are first-principle constraints explicit?
- Are vendor-specific statements scoped to the vendor?
- Are graph edges typed and useful?
- Are open questions preserved?
- Is market logic separated from technical fact?

## Future Automation

The first automated version should be conservative:

- `ingest_source.py`: register a source and create a candidate note.
- `extract_claims.py`: produce a claim draft, not accepted knowledge.
- `review_concept.py`: lint frontmatter, citations, and edges.
- `build_index.py`: generate graph JSON for UI and search.
