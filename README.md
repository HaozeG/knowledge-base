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
- Quality rule: important claims must point to stable source IDs. Source lookup prefers `sources/source-registry.sqlite` when present and falls back to the compatibility export at `sources/source-registry.yaml`.

## Layout

```text
knowledge-base/
  concepts/              # Human-readable concept pages
  graph/                 # Typed edges and generated graph index
  scripts/               # Local tooling
  viewer/                # Static read-only graph viewer
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

Open the static graph viewer:

```bash
python3 -m http.server
```

Then visit:

```text
http://127.0.0.1:8000/viewer/
```

The viewer is read-only and loads `graph/concept-index.json` directly. It needs a local static server because browser file URLs cannot reliably fetch the JSON index.

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

## Autonomous Exploration Loop

Use the exploration-loop harness when the next step is autonomous knowledge-base growth from a hardware/software/workload seed. The loop stages all candidate work under `temp/exploration-runs/<run-id>/` and promotes only runs that pass deterministic hard gates and the fixed score threshold.

Preflight before starting an autonomous session:

```bash
python3 scripts/build_index.py
python3 scripts/validate_ontology.py
python3 scripts/validate_harnesses.py
python3 scripts/test_evaluate_exploration.py
```

Create a seed for the run, either in the agent prompt or as a temporary file:

```text
temp/exploration-runs/<run-id>/seed.md
```

The seed should include:

- accelerator architecture or design hypothesis
- target workloads
- relevant software stack assumptions
- starting concept IDs or files
- any previous run guidance that should constrain the next attempt

Autonomous runner setup:

1. Start from `system/agent-operating-manual.md`.
2. Select `system/harnesses/exploration-loop.md`.
3. Read the seed, related concept files, `system/ontology.md`, `system/source-quality.md`, and previous run guidance.
4. For each attempt, start one clean-context subagent with only those inputs.
5. Stage candidate files, candidate source notes, graph-edge additions, and `manifest.json` under `temp/exploration-runs/<run-id>/`.
6. Evaluate the staged run:

```bash
python3 scripts/evaluate_exploration.py temp/exploration-runs/<run-id> --allow-reject
```

The evaluator emits versioned JSON. Schema version 2 keeps the legacy top-level `score` field but adds normalized `combined_score`, bounded scalar metrics, hard-gate records, artifact accounting, run-history streaks, and ranked `next_targets`. Older ledger rows with only `score` and `next_hint` remain valid historical input; do not recompute them under newer metrics.

If the evaluator accepts the run, promote the staged draft content into the permanent knowledge-base locations allowed by the harness, then run:

```bash
python3 scripts/build_index.py
python3 scripts/validate_ontology.py
python3 scripts/validate_harnesses.py
```

Accepted runs should append a compact record to `system/run-ledger.jsonl`, including timestamp, run id, target, source summary, metric JSON, promotion actions, and next-step guidance.

If the evaluator rejects the run, keep only a compact rejection log under the run folder, remove or quarantine unpromoted candidate artifacts, and follow `run_history.direction_policy`. `pivot_required` means choose a different layer or parent concept. `forced_pivot` means choose a sparse or stale category outside the failed direction. Neither policy is a stop condition.

For the first autonomous test, run a bounded smoke session with a three-attempt cap before enabling the long-running mode. In long-running mode, the loop continues until the user asks it to stop, an external budget is exhausted, or repository validation reaches an unrecoverable failure.

Source storage:

- `sources/source-registry.yaml` remains the compatibility export agents can read and diff.
- `sources/source-registry.sqlite` is preferred when present for scalable source lookup.
- Initialize or refresh the database from YAML with:

```bash
python3 scripts/sync_sources.py --from-yaml
```

Stop and cleanup rules:

- Finish the current file operation before stopping.
- Preserve already-promoted permanent files.
- Leave interrupted temporary artifacts under `temp/exploration-runs/<run-id>/` with an `interrupted` log entry, or quarantine them under that run folder.
- Do not modify harnesses, validators, metric weights, ontology, source-quality rules, or existing verified concepts during the autonomous loop. Use the meta-harness for those changes.

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
