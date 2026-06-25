# Continuous Exploration And Link Guidance Design

## Goal

Improve the knowledge-base growth loop so it can keep discovering useful concepts and graph links as the node count grows.

The change should solve three problems:

- candidate edge search will become too expensive and noisy if every new node is compared with every existing node
- autonomous exploration must not treat a seed topic, local layer checklist, or exhausted first-pass idea list as a natural stop condition
- source tiers need stricter handling for second-hand media and aggregation platforms, especially when they summarize primary technical or business information without independent verification

This is a meta-harness design. The exploration loop itself should continue to stage object-level content under `temp/exploration-runs/<run-id>/`; these system-level changes should happen only through the meta-harness path.

## Existing Context

The repository already has the right high-level contracts:

- `system/harnesses/exploration-loop.md` says long-running mode continues until user stop, budget exhaustion, or unrecoverable validation failure.
- `scripts/evaluate_exploration.py` emits ranked `next_targets`.
- `system/source-quality.md` defines source tiers A through D.
- `graph/concept-index.json` is the generated data contract for local tools and the read-only graph viewer.

The gap is mechanical guidance. The loop can say "never stop" but still fail in practice if target generation depends too much on the current seed or on a human-like judgment that the agent has exhausted relevant ideas. Likewise, source policy says tiers must be conservative, but it does not yet spell out how to classify second-hand media and platform reposts.

## Approaches Considered

### Approach A: Policy-Only

Update `exploration-loop.md` and `source-quality.md` with stronger wording.

This is low risk and quick, but it does not give future agents or scripts a concrete way to rank candidate edges or select the next exploration target. It is likely to repeat the previous failure mode: the agent can read "do not stop" but still claim no relevant target remains.

### Approach B: Add Concept Link Hints Only

Add concept-level fields such as `keywords`, `link_hints`, and `exploration_questions`, then make the indexer expose them.

This improves edge discovery and local search, but it still leaves the continuous loop dependent on ad hoc agent judgment when a seed direction becomes stale.

### Approach C: Add Link Hints And Target-Generation Mechanics

Add concept-level link hints, generate searchable indexes from them, and update exploration target ranking so the loop always has fallback target classes beyond the original seed.

This is the recommended approach. It keeps the system local-first and deterministic while giving agents a durable target queue. It also keeps source-tier changes separate from object-level concept writing.

## Recommended Design

Implement Approach C in three layers:

1. Concept metadata and generated indexes for edge discovery.
2. Exploration target generation that cannot terminate merely because the seed topic feels exhausted.
3. Source-tier policy changes that conservatively demote second-hand media and aggregation platforms.

## Link Guidance Model

Concept frontmatter should support optional fields:

```yaml
keywords:
  - tensor memory accelerator
  - asynchronous copy
link_hints:
  - target: hw.gpu.memory-hierarchy
    relation: depends_on
    reason: TMA exists to move tensor-shaped data through the memory hierarchy.
exploration_questions:
  - What workload shapes make this mechanism useful?
  - Which compiler or runtime layer exposes this capability?
```

Field meaning:

- `keywords`: normalized phrases that help locate candidate neighbors without scanning every paragraph.
- `link_hints`: explicit human- or agent-authored candidate edges. They are not promoted graph edges until reviewed or accepted by a harness.
- `exploration_questions`: open directions that should feed future target generation.

Generated `graph/concept-index.json` should expose these fields per node and may add derived indexes:

- keyword to concept IDs
- source ID to concept IDs
- open question to concept ID
- weakly connected concept IDs
- concepts with link hints that are not yet present in `graph/edges.jsonl`

The generated index should remain backward-compatible for the viewer. New fields can be optional; existing tools should not need schema migration.

## Candidate Edge Search

Future edge search should use staged narrowing:

1. Start from the active target concept, seed topic, or proposed node.
2. Collect candidate neighbors from:
   - exact `link_hints`
   - shared `keywords`
   - shared `sources`
   - matching `reasoning_roles`
   - compatible `scale_scope`
   - same parent or adjacent layer in `layer_path`
   - existing edge neighborhoods around the parent concept
3. Rank candidates by evidence and structural value:
   - exact link hint
   - same source family or primary source trail
   - cross-layer bridge value
   - sparse or weakly connected target
   - matching scale and reasoning role
4. Require typed-edge justification before promotion.

The algorithm should avoid all-pairs comparison across the full graph. It should produce a bounded candidate set per node, such as top 20 candidates, and require the agent or evaluator to account for accepted and rejected candidate edges.

## Continuous Exploration Target Generator

The exploration loop should treat every accepted, rejected, or exhausted attempt as producing another target queue. "No more relevant ideas from the seed" is a pivot signal, not a stop condition.

Target classes should include:

- `seed_continuation`: direct next ideas from the current seed
- `open_question`: unresolved `exploration_questions` from existing concepts
- `weak_link`: concepts with few typed graph edges
- `missing_bridge`: adjacent layers with no clear connecting concept
- `source_trail`: primary sources cited by a concept that imply unmodeled mechanisms
- `stale_layer`: layers not updated recently in the ledger
- `sparse_layer`: layers with low concept count
- `source_quality_upgrade`: concepts relying on weak sources that need A/B replacements
- `case_to_pattern`: product or event case studies that should be generalized into reusable mechanisms
- `pattern_to_case`: abstract mechanisms that need concrete case studies
- `analogy_pivot`: a mechanism in one layer or architecture family that suggests a counterpart elsewhere

Target ranking should combine:

- graph sparsity
- layer staleness
- weak connectivity
- unresolved open questions
- poor evidence strength
- cross-layer bridge value
- repeated rejection history

The evaluator should always return non-empty `next_targets` unless repository validation is unrecoverably failing or an explicit external budget is exhausted. If no agent-proposed target survives, the fallback should be deterministic: choose sparse or stale categories, weakly connected concepts, or open questions outside the failed direction.

## Loop Semantics

The loop should not define completion as "all concept layers have at least one page" or "the seed topic has no obvious next idea." Those are milestones only.

Valid stop conditions:

- user explicitly stops the loop
- external budget is exhausted
- repository validation reaches an unrecoverable failure
- required external dependency is unavailable and no local fallback exists

Invalid stop conditions:

- seed topic seems exhausted
- all central stack layers have some coverage
- all currently proposed targets were rejected
- current model cannot think of another relevant idea
- milestone summary has been produced

If the current model claims exhaustion, the harness should force a target-generation pass using the deterministic fallback classes above. If that still produces low-quality targets, the loop should pivot to source-quality upgrade, stale layer review, weak-link repair, or open-question expansion.

## Source Tier Reclassification

`system/source-quality.md` should make source classification more explicit:

| Source Kind | Default Tier | Notes |
| --- | --- | --- |
| Peer-reviewed paper, standard, official architecture doc, official programming guide, regulatory filing | A | Primary source for the claims it directly supports |
| Vendor technical blog, conference talk, reputable teardown with methods, analyst report with transparent methodology | B | Can support draft claims; verified status needs strong fit to the claim |
| Business reporting, interviews, second-hand media summaries, article rewrites, platform reposts with attribution | C | Useful for discovery, chronology, and market narrative, not verified technical mechanism claims |
| Unsourced repost, social media, forum, content farm, AI-generated page, unattributed Chinese platform summary, rumor compilation | D | Can create questions only; cannot verify claims |

Second-hand media such as 36kr-style business reporting or Chinese platform reposts should default to C when they clearly attribute claims to primary sources, interviews, filings, or named reports. They should default to D when attribution is missing, unverifiable, circular, or based on rumor.

Tier upgrades should require checking the source's evidence basis, not just publisher reputation. A translated, summarized, or reposted version of a primary source does not inherit the primary source tier.

## Evaluator And Validator Changes

Implementation should update:

- `scripts/build_index.py` to preserve optional `keywords`, `link_hints`, and `exploration_questions`.
- `scripts/evaluate_exploration.py` to rank `next_targets` using the expanded target classes.
- `scripts/evaluate_exploration.py` hard gates or scalar metrics to penalize undeclared source attribution and weak source dependence.
- `system/source-quality.md` to document second-hand media classification.
- `system/harnesses/exploration-loop.md` to define target exhaustion as pivot, not stop.
- Tests or fixtures under `use-cases/fixtures/exploration-loop/` for non-empty fallback targets and source-tier demotion.

The evaluator should remain deterministic. It should not call a model or search the network.

## Data Compatibility

Existing concepts do not need to gain all new fields immediately. New fields are optional.

Existing graph edges remain the authoritative typed graph. `link_hints` are candidate guidance only and should not be rendered as accepted edges unless promoted into `graph/edges.jsonl`.

Existing source tiers should not be mass-edited without separate review. The source policy change should affect new entries first, then a later audit can reclassify existing entries.

## Validation Plan

Design validation:

```bash
git diff --check
```

Implementation validation:

```bash
python3 scripts/build_index.py
python3 scripts/validate_ontology.py
python3 scripts/validate_harnesses.py
python3 scripts/test_evaluate_exploration.py
git diff --check
```

Add focused tests for:

- concept index keeps optional link-guidance fields
- evaluator returns non-empty fallback `next_targets` when no proposed target survives
- repeated rejection causes pivot target classes instead of stop language
- source-tier scoring penalizes C and rejects D for promoted claims as it does today
- sample second-hand media source is classified C or D, not A or B

## Out Of Scope

This design does not:

- run the autonomous exploration loop
- edit existing concept content
- mass-reclassify existing sources
- change the graph viewer UI
- allow agents to mark concepts verified
- weaken any source-quality or promotion rule

## Approval Gate

After review, implementation should proceed through the meta-harness because it changes source policy, harness behavior, generated index fields, and evaluator target ranking.
