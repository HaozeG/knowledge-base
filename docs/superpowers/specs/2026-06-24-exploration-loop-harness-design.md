# Exploration Loop Harness Design

## Goal

Define one long-running harness for testing whether the knowledge base can grow from a concrete hardware accelerator design into useful, queryable concepts. The harness should let an agent start from a hardware/software/workload description, explore trustworthy sources one focused component at a time, temporarily stage candidate knowledge, evaluate the staged work with deterministic metrics, and automatically promote acceptable draft content.

The harness is an object-level content-growth loop. It must not change its own rules while running.

## Existing Context

The repository already treats agents as controllers inside harnesses. The current contracts define objectives, mutable surfaces, immutable surfaces, sensors, actuators, evaluators, promotion rules, logging, and human controls.

The new exploration loop should reuse existing contracts instead of replacing them:

- `knowledge-ingestion.md` governs whether promoted content is acceptable as knowledge-base draft material.
- `graph-export.md` governs regenerated graph and index artifacts after promotion.
- `meta-harness.md` remains the only path for changing harnesses, validators, ontology, source policy, or evaluator logic.

## Harness Shape

Add one new object-level harness:

```text
system/harnesses/exploration-loop.md
```

The harness owns this loop:

1. Choose a focused target.
2. Spawn one clean-context subagent.
3. Stage temporary artifacts.
4. Score the attempt.
5. Promote accepted work.
6. Log the outcome and next directions.
7. Repeat until the user interrupts or stops the loop.

The loop may create temporary files only under:

```text
temp/exploration-runs/<run-id>/
```

Promotion to permanent locations is automatic only after hard gates pass and the fixed score crosses threshold. Normal promotion does not require human approval if the promoted content follows the existing knowledge-ingestion harness.

## Mutable And Immutable Surfaces

Temporary mutable surfaces:

- `temp/exploration-runs/<run-id>/`

Permanent mutable surfaces after acceptance:

- `concepts/`
- `sources/source-registry.yaml`
- `graph/edges.jsonl`
- `inbox/candidate-sources/`
- `use-cases/`
- `graph/concept-index.json`
- `system/run-ledger.jsonl`

Immutable during the automated exploration loop:

- `system/`
- `scripts/`
- harness definitions
- validators
- metric weights and thresholds
- ontology definitions
- source-quality rules
- existing verified concepts
- raw source material, unless explicitly copied into candidate notes

The loop cannot mark concepts `verified`, upgrade source tiers, delete or merge permanent concepts, or add market/investment conclusions.

## Subagent Context Contract

Each exploration cycle starts one subagent with clean context. The subagent receives only:

- the selected seed description or starting files,
- the active exploration-loop harness contract,
- the required ontology and source-quality rules,
- related concept files selected by the main loop,
- previous run guidance, if available.

The subagent should focus on one component, mechanism, workload mapping question, or software-control question. It should not conduct broad multi-topic exploration in one attempt.

The subagent may write only temporary artifacts in the run folder:

- candidate source notes,
- proposed concept drafts,
- proposed edge additions,
- source registry proposals,
- metric input files,
- run summary,
- next-step guidance.

## Evaluator

The evaluator has hard gates first, then a fixed composite threshold.

Hard gates:

- Temporary content must fit existing ontology fields and source policy.
- Promoted concepts can only be `seed` or `draft`.
- Important factual claims need source IDs or explicit uncertainty labels such as `open`, `supported`, `inference`, or `speculative`.
- Source tiers must be conservative.
- Product-family-first placement is rejected.
- The attempt must pass required validation commands.
- The loop must not modify system rules, validators, metric weights, or ontology.

Composite score:

```text
score =
  (creativity_score + coverage_gap_score)
  * category_staleness_multiplier
  - quality_risk_penalty
```

The initial acceptance threshold is fixed by policy:

```text
score >= 1.0
```

Changing this threshold or the metric weights later requires the meta-harness.

The category staleness multiplier is capped:

```text
1.0 <= category_staleness_multiplier <= 1.5
```

This lets useful work in stale categories count more, without allowing staleness to override quality problems.

Metric intent:

- `creativity_score` rewards useful new typed edges relative to existing graph size, with extra weight for connecting hot parent categories to sparse or emerging child concepts.
- `coverage_gap_score` rewards useful material under categories with few descendants.
- `category_staleness_multiplier` rewards work under categories whose descendant concepts or ledger entries have not been updated recently.
- `quality_risk_penalty` penalizes weak sources, unsupported certainty, duplicate concepts, product-family-first placement, broad unfocused exploration, and excessive speculative claims.

The scoring script must be deterministic and auditable. It should not search online, call a model, or mutate files.

## Loop Control Flow

Each cycle follows this control flow:

1. Select a focused target from the user-provided accelerator design, previous run guidance, or fallback category policy.
2. Create `temp/exploration-runs/<run-id>/`.
3. Start one clean-context subagent.
4. Let the subagent search focused, trustworthy resources for one component or mechanism.
5. Stage candidate artifacts in the run folder.
6. Evaluate hard gates.
7. Compute the fixed-threshold score.
8. If accepted, promote artifacts into permanent knowledge-base locations.
9. Rebuild and validate graph artifacts.
10. Append a permanent run-ledger entry.
11. Record next exploration directions.
12. Start the next cycle.

If the attempt is rejected:

1. Append or retain a compact rejection record.
2. Remove or quarantine unpromoted candidate content.
3. Try a new focused target.

If five consecutive attempts fail to proceed:

1. Select the sparsest or stalest knowledge category.
2. Start a new exploration from that category.
3. Record an escalation hint that a higher-intelligence model may be useful.

The loop continues until the user asks it to stop.

## Cleanup And Recovery

User interrupt:

- Finish the current filesystem operation.
- Append an interrupted-run log if possible.
- Leave promoted files intact.
- Quarantine unpromoted temporary files under the run folder.

Crash or restart:

- Inspect the latest run folder.
- Determine whether the attempt was promoted, rejected, or incomplete.
- Never promote partial temporary artifacts without rerunning hard gates and scoring.

Failed promotion:

- Do not partially accept content.
- Keep a compact failure log.
- Restore or quarantine any candidate files that were not fully promoted.

## Required Durable Artifacts

Implementation should add:

- `system/harnesses/exploration-loop.md`
- updates to `system/harnesses/README.md`
- updates to `system/agent-operating-manual.md`
- `scripts/evaluate_exploration.py`
- `.gitignore` coverage for runtime `temp/` artifacts if needed
- a recorded use case for the hardware-accelerator exploration scenario

The validator should also recognize the new harness as a first-class harness.

## Validation Plan

The implementation should support these checks:

```bash
python3 scripts/build_index.py
python3 scripts/validate_ontology.py
python3 scripts/validate_harnesses.py
python3 scripts/evaluate_exploration.py temp/exploration-runs/<sample-run>
git diff --check
```

For the design-only step, the expected validation is a spec self-review plus `git diff --check`.

## Out Of Scope

This design does not start the automated loop. It also does not define actual hardware accelerator seed content, online-search ranking details, model selection policy, or exact metric weights beyond the score shape and multiplier cap.

Those belong in the implementation plan or in later meta-harness changes after the written design is reviewed.
