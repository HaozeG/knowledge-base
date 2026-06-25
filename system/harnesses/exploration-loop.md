# Exploration Loop Harness

## Purpose

Run long-lived, focused exploration cycles that grow the knowledge base from a hardware/software/workload seed while keeping candidate work isolated until deterministic evaluation accepts it.

## Objective

Discover useful accelerator concepts, sources, and graph links without weakening source quality, ontology placement, or evaluator integrity.

## Mutable Surfaces

Temporary before acceptance:

- `temp/exploration-runs/<run-id>/`

Permanent after acceptance:

- `concepts/`
- `sources/source-registry.sqlite`
- `sources/source-registry.yaml`
- `graph/edges.jsonl`
- `inbox/candidate-sources/`
- `use-cases/`
- `graph/concept-index.json`
- `system/run-ledger.jsonl`

## Immutable Surfaces

- `system/harnesses/`
- `system/ontology.md`
- `system/source-quality.md`
- `system/agent-operating-manual.md`
- `system/system-design.md`
- `scripts/`
- harness definitions
- validators
- metric weights and thresholds
- ontology definitions
- source-quality rules
- existing verified concepts
- raw source material, unless copied into candidate notes

## Sensors

```bash
python3 scripts/build_index.py
python3 scripts/validate_ontology.py
python3 scripts/validate_harnesses.py
python3 scripts/evaluate_exploration.py temp/exploration-runs/<run-id> --allow-reject
```

Also inspect:

- staged `manifest.json`
- candidate concept drafts
- candidate source notes
- candidate edge additions
- metric JSON output
- previous run guidance

## Actuators

- Select one focused exploration target.
- Start one clean-context subagent with only the seed files, harness contract, ontology/source rules, related concepts, and previous guidance.
- Search focused, trustworthy resources for one component, mechanism, workload mapping question, or software-control question.
- Stage temporary candidate artifacts under `temp/exploration-runs/<run-id>/`.
- Promote accepted draft content into permanent knowledge-base locations.
- Regenerate `graph/concept-index.json`.
- Append run-ledger entries and next-step directions.
- Quarantine or remove rejected temporary candidate artifacts.

## Evaluator

Hard gates pass only when:

- candidate content follows ontology and source policy
- promoted concepts are only `seed` or `draft`
- important factual claims have source IDs or explicit uncertainty labels
- source tiers are conservative
- staged candidate artifacts match the accepted manifest, or rejected artifacts are explicitly accounted for
- proposed graph edges use known ontology edge types
- product-family-first placement is rejected
- validator commands pass
- the loop does not modify system rules, validators, metric weights, or ontology

Evaluator output is versioned. New output uses `evaluator_schema_version: 2`; older ledger rows without that field are treated as schema version 1 and remain valid historical evidence. Do not recompute old scores under new metrics.

Hard gates decide eligibility. Scalar metrics explain quality, recovery state, and threshold guidance. Every scalar metric `value` and `combined_score` must stay in the `0..1` range. If a raw metric exceeds that range, the evaluator must retain `raw_value` and `range_status` so normalization does not hide metric-design drift:

```text
graph_connectivity
coverage_gap
evidence_strength
claim_hygiene
focus_score
rejection_recovery
guidance_quality
quality_risk_penalty
```

The compatibility aggregate `score` remains available for older workflows and may exceed `1`. New accept/reject decisions should require both:

```text
legacy score >= 1.0
combined_score >= 0.7
1.0 <= category_staleness_multiplier <= 1.5
```

Changing the threshold, weights, or scoring formula requires the meta-harness.

## Promotion Policy

If hard gates pass and score crosses the fixed threshold, promote staged artifacts automatically under the knowledge-ingestion contract.

If hard gates fail or score is below threshold:

- record a compact rejection log
- remove or quarantine unpromoted candidate files
- try a new focused target based on evaluator guidance

Continuous rejection recovery:

- after two same-direction rejections, prefer a different layer or parent concept
- after three consecutive rejections, follow `direction_policy: pivot_required`
- after five consecutive rejections, follow `direction_policy: forced_pivot`
- forced pivot is not a stop condition; select a sparse or stale category outside the failed direction and continue

Milestone summaries are informational. Do not ask whether to proceed after a fixed number of successful runs in long-running mode. Continue until the user explicitly stops the loop, an external budget is exhausted, or repository validation fails in a way that cannot be recovered automatically.

External hook failures, such as a missing local hook runtime, are non-blocking unless they corrupt repository state or cause validator failures. Record them as runtime notes and continue from the next valid run boundary.

## Logging Contract

For every attempt, record:

- timestamp
- run id
- selected target
- source summary
- candidate artifacts
- metric output
- accept, reject, interrupted, or failed decision
- promotion actions, if any
- next-step guidance

New ledger entries should include structured `metrics`, `run_history`, and `next_targets` when available. Agents must continue reading older rows that only have `score` and `next_hint`.

Accepted runs append to `system/run-ledger.jsonl`. Rejected or interrupted runs keep compact logs under the run folder unless the user asks to preserve more detail.

## Human Controls

**NEVER STOP**: Once the experiment loop has begun (after the initial setup), do NOT pause to ask the human if you should continue. Do NOT ask "should I keep going?" or "is this a good stopping point?". The human might be asleep, or gone from a computer and expects you to continue working *indefinitely* until you are manually stopped. You are autonomous. If you run out of ideas, think harder — read papers referenced in the code, re-read the in-scope files for new angles, try combining previous near-misses. The loop runs until the human interrupts you, period.

Example use case, the user provides a topic as a inital topic, you should start exploring and bringing ideas into the knowledge base. The utimate goal is not filling all concept layers, but continuously exploring for knowledge, concepts, ideas, growing the knowledge base into a reliable local knowledge collection.