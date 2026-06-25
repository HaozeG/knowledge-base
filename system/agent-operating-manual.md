# Agent Operating Manual

This is the entry point for agents working in this knowledge base.

Agents are controllers inside a harness. The harness defines the objective, allowed actions, observations, evaluator, logging, and escalation rules. Do not act as an unconstrained note-taking assistant.

## Startup Sequence

Before changing content, read these files in order:

1. `system/system-design.md`
2. `system/ontology.md`
3. `system/source-quality.md`
4. `system/agent-writing-guide.md`
5. The relevant file under `system/harnesses/`
6. Existing concepts related to the task
7. Existing use-case records if the task resembles a prior test

## Harness Selection

| Task | Harness |
| --- | --- |
| Add or process a source | `system/harnesses/knowledge-ingestion.md` |
| Place or reorganize concepts | `system/harnesses/ontology-review.md` |
| Review concept quality and verification readiness | `system/harnesses/concept-review.md` |
| Answer a user question from the KB | `system/harnesses/query-synthesis.md` |
| Regenerate graph/index artifacts | `system/harnesses/graph-export.md` |
| Run long-lived autonomous exploration from a hardware/software/workload seed | `system/harnesses/exploration-loop.md` |
| Audit low-cost exploration runs for procedure or format drift | `system/harnesses/cheap-model-drift-audit.md` |
| Change ontology, policies, evaluators, or harnesses | `system/harnesses/meta-harness.md` |

## Default Control Loop

```text
1. Identify the user goal.
2. Choose one harness.
3. Load required system files and related concepts.
4. State assumptions in the working notes or use-case record.
5. Make the smallest scoped change.
6. Run required sensors.
7. Evaluate against the harness acceptance rules.
8. Record the result in `system/run-ledger.jsonl`.
9. Report changed files, validation results, and remaining risks.
```

## Permission Model

Allowed without extra approval:

- Create or edit concept drafts.
- Add source registry entries with conservative source tiers.
- Add typed graph edges.
- Add use-case records.
- Regenerate `graph/concept-index.json`.
- Append to `system/run-ledger.jsonl`.
- Create temporary exploration artifacts under `temp/exploration-runs/<run-id>/`.
- Promote exploration artifacts to draft content when the exploration-loop hard gates and fixed score pass.

Approval-gated:

- Mark a concept `verified`.
- Upgrade source quality tier.
- Change ontology values, source policy, harness contracts, or validators.
- Change exploration-loop metric weights, thresholds, or evaluator logic.
- Delete or consolidate existing concepts.
- Add market or investment conclusions.

Forbidden:

- Treat product pages, marketing claims, or AI-generated page summaries as verified facts.
- Make product families the top-level ontology.
- Mix technical mechanism and stock conclusion in the same concept page.
- Change evaluator scripts and content artifacts in the same unrecorded loop.
- Delete raw source notes after ingestion.

## Required Sensors

Run these after ontology or concept edits:

```bash
python3 scripts/build_index.py
python3 scripts/validate_ontology.py
```

Run this after harness edits:

```bash
python3 scripts/validate_harnesses.py
```

## Logging

Every meaningful run appends one JSONL entry to `system/run-ledger.jsonl` with:

```text
id
timestamp (from `date` instruction)
harness
goal
status
decision
artifacts
next_hint
```

## User-Facing Output

Final responses should include:

- What changed.
- What validation ran.
- What remains draft or unverified.
- Which harness was used.
- Any open questions that block promotion to verified status.
