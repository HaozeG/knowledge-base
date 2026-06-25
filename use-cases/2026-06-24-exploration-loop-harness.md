---
id: use-case.exploration-loop-harness-2026-06-24
title: Exploration Loop Harness Test
status: recorded
date: 2026-06-24
harness: exploration-loop
source_ids: []
related_concepts: [stack.ai-accelerator-ontology, hw.gpu.overview, programmer.roofline-model]
---

# Exploration Loop Harness Use Case

Date: 2026-06-24

## Goal

Verify that the knowledge-base design can support a long-running harness that starts from a new hardware accelerator design, stages temporary exploration results, evaluates graph-growth usefulness, and promotes acceptable draft content without human approval for each normal draft promotion.

## Scenario

The user describes a hardware accelerator, its software stack, and target workloads. The exploration loop chooses one focused component or mechanism, starts a clean-context subagent, searches trustworthy sources, stages temporary candidate artifacts, evaluates the attempt, and either promotes or rejects the run.

## Accepted Design Decisions

- Temporary artifacts are allowed only under `temp/exploration-runs/<run-id>/`.
- Permanent draft promotion is automatic when hard gates pass and evaluator thresholds are crossed.
- Evaluator output is versioned. Version 2 adds structured hard gates, normalized `combined_score`, bounded scalar metrics, artifact accounting, run-history streaks, and ranked next targets while preserving the legacy top-level `score` field.
- `category_staleness_multiplier` is capped between `1.0` and `1.5`.
- Metric weights and thresholds can change only through the meta-harness.
- Each exploration attempt uses one clean-context subagent.
- Consecutive rejections trigger direction guidance: two same-direction rejections prefer a new direction, three rejections require pivot, and five rejections force pivot without stopping the loop.
- Five accepted runs are not a stop condition or permission prompt in long-running mode.
- Old ledger rows with only `score` and `next_hint` remain readable and are not reinterpreted under new metrics.
- Source lookup prefers `sources/source-registry.sqlite` when present and falls back to `sources/source-registry.yaml`.

## Validation Commands

```bash
python3 scripts/test_build_index.py
python3 scripts/test_evaluate_exploration.py
python3 scripts/sync_sources.py --from-yaml --db /tmp/source-registry.sqlite
python3 scripts/evaluate_exploration.py use-cases/fixtures/exploration-loop/accepted --index use-cases/fixtures/exploration-loop/index.json --ledger use-cases/fixtures/exploration-loop/run-ledger.jsonl --today 2026-06-24
python3 scripts/evaluate_exploration.py use-cases/fixtures/exploration-loop/rejected --index use-cases/fixtures/exploration-loop/index.json --ledger use-cases/fixtures/exploration-loop/run-ledger.jsonl --today 2026-06-24 --allow-reject
python3 scripts/build_index.py
python3 scripts/validate_ontology.py
python3 scripts/validate_harnesses.py
git diff --check
```

## Expected Result

The accepted fixture crosses the legacy and normalized thresholds and emits schema version 2 fields. The rejected fixture reports a below-threshold rejection without mutation. The hard-gate fixtures fail because verified promotion, tier-D source promotion, unknown edge types, or artifact-accounting drift are forbidden. Mixed old/new ledger rows load without migration.
