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
- product-family-first placement is rejected
- validator commands pass
- the loop does not modify system rules, validators, metric weights, or ontology

The fixed score is:

```text
score =
  (creativity_score + coverage_gap_score)
  * category_staleness_multiplier
  - quality_risk_penalty
```

Initial acceptance policy:

```text
score >= 1.0
1.0 <= category_staleness_multiplier <= 1.5
```

Changing the threshold, weights, or scoring formula requires the meta-harness.

## Promotion Policy

If hard gates pass and score crosses the fixed threshold, promote staged artifacts automatically under the knowledge-ingestion contract.

If hard gates fail or score is below threshold:

- record a compact rejection log
- remove or quarantine unpromoted candidate files
- try a new focused target

After five consecutive attempts fail to proceed, select the sparsest or stalest category and record an escalation hint that a higher-intelligence model may be useful.

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

Accepted runs append to `system/run-ledger.jsonl`. Rejected or interrupted runs keep compact logs under the run folder unless the user asks to preserve more detail.

## Human Controls

The loop continues until the user asks it to stop.

Ask before:

- changing harnesses, validators, metric weights, ontology, or source policy
- marking concepts `verified`
- upgrading source tiers
- deleting or merging permanent concepts
- adding market or investment conclusions
- broadening a single attempt beyond one focused component or mechanism
