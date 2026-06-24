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
- Permanent draft promotion is automatic when hard gates pass and the fixed score crosses threshold.
- The score is `(creativity_score + coverage_gap_score) * category_staleness_multiplier - quality_risk_penalty`.
- `category_staleness_multiplier` is capped between `1.0` and `1.5`.
- Metric weights and thresholds can change only through the meta-harness.
- Each exploration attempt uses one clean-context subagent.
- Five consecutive failures trigger fallback to the sparsest or stalest category and an escalation hint.

## Validation Commands

```bash
python3 scripts/test_build_index.py
python3 scripts/test_evaluate_exploration.py
python3 scripts/evaluate_exploration.py use-cases/fixtures/exploration-loop/accepted --index use-cases/fixtures/exploration-loop/index.json --ledger use-cases/fixtures/exploration-loop/run-ledger.jsonl --today 2026-06-24
python3 scripts/evaluate_exploration.py use-cases/fixtures/exploration-loop/rejected --index use-cases/fixtures/exploration-loop/index.json --ledger use-cases/fixtures/exploration-loop/run-ledger.jsonl --today 2026-06-24 --allow-reject
python3 scripts/build_index.py
python3 scripts/validate_ontology.py
python3 scripts/validate_harnesses.py
git diff --check
```

## Expected Result

The accepted fixture crosses the fixed threshold. The rejected fixture reports a below-threshold rejection without mutation. The hard-gate fixtures fail because verified promotion and tier-D source promotion are forbidden.
