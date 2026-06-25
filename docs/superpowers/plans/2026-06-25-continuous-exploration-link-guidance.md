# Continuous Exploration Link Guidance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add deterministic link-guidance metadata, non-empty continuous exploration target generation, and stricter second-hand source classification rules.

**Architecture:** Keep concept Markdown as the source of truth. `scripts/build_index.py` will preserve optional link-guidance frontmatter and emit derived indexes; `scripts/evaluate_exploration.py` will rank fallback `next_targets` from graph gaps, weak links, open questions, source quality, and rejection history. Policy docs will define the intended behavior, while tests pin the deterministic contract.

**Tech Stack:** Python standard library, `unittest`, Markdown/YAML-like frontmatter, JSON/JSONL fixtures.

---

## File Structure

- Modify `scripts/build_index.py`: parse a narrow subset of nested frontmatter for `link_hints`, preserve `keywords` and `exploration_questions`, and emit derived indexes.
- Modify `scripts/test_build_index.py`: add helper-level tests for link-guidance parsing and derived indexes.
- Modify `scripts/evaluate_exploration.py`: expand `next_targets()` with deterministic target classes and source-quality fallback targets.
- Modify `scripts/test_evaluate_exploration.py`: add evaluator tests for non-empty fallback targets, open questions, weak links, and low-tier source targets.
- Modify `use-cases/fixtures/exploration-loop/index.json`: add optional fields needed by evaluator fixtures.
- Modify `system/source-quality.md`: document second-hand media and Chinese platform tier defaults.
- Modify `system/harnesses/exploration-loop.md`: encode seed exhaustion as pivot, not stop.
- Modify `system/ontology.md`: document optional link-guidance concept fields.
- Modify `README.md`: add a compact note under Link Policy and Autonomous Exploration Loop.

Do not mass-edit existing concept files or source registry entries in this plan. Existing dirty worktree changes must be preserved. Commit checkpoints below are for a clean worktree or isolated worktree only; otherwise skip commits and report the changed files.

---

### Task 1: Add Indexer Tests For Link Guidance Metadata

**Files:**
- Modify: `scripts/test_build_index.py`

- [ ] **Step 1: Add tests for parsing nested `link_hints` and derived indexes**

Add these tests inside `BuildIndexTests`:

```python
    def test_parse_frontmatter_keeps_link_guidance_fields(self) -> None:
        text = """---
id: hw.gpu.tensor-memory-accelerator
title: Tensor Memory Accelerator
keywords: [tensor memory accelerator, asynchronous copy]
exploration_questions: [What workloads benefit from TMA?, Which runtime exposes TMA?]
link_hints:
  - target: hw.gpu.memory-hierarchy
    relation: depends_on
    reason: TMA moves tensor-shaped data through the memory hierarchy.
---
Body
"""

        metadata, body = build_index.parse_frontmatter(text)

        self.assertEqual(body, "Body\n")
        self.assertEqual(
            metadata["keywords"],
            ["tensor memory accelerator", "asynchronous copy"],
        )
        self.assertEqual(
            metadata["exploration_questions"],
            ["What workloads benefit from TMA?", "Which runtime exposes TMA?"],
        )
        self.assertEqual(
            metadata["link_hints"],
            [
                {
                    "target": "hw.gpu.memory-hierarchy",
                    "relation": "depends_on",
                    "reason": "TMA moves tensor-shaped data through the memory hierarchy.",
                }
            ],
        )

    def test_link_guidance_indexes_are_derived_from_nodes_and_edges(self) -> None:
        nodes = [
            {
                "id": "hw.gpu.tensor-memory-accelerator",
                "keywords": ["tensor memory accelerator", "async copy"],
                "sources": ["nvidia-hopper"],
                "source_refs": ["nvidia-hopper"],
                "exploration_questions": ["Which compiler layer exposes TMA?"],
                "link_hints": [
                    {
                        "target": "hw.gpu.memory-hierarchy",
                        "relation": "depends_on",
                        "reason": "TMA moves data through memory hierarchy.",
                    },
                    {
                        "target": "software.runtime.cuda-streams",
                        "relation": "implemented_by",
                        "reason": "Runtime exposure remains unresolved.",
                    },
                ],
            },
            {
                "id": "hw.gpu.memory-hierarchy",
                "keywords": ["memory hierarchy"],
                "sources": ["nvidia-hopper"],
                "source_refs": [],
                "exploration_questions": [],
                "link_hints": [],
            },
        ]
        edges = [
            {
                "source": "hw.gpu.tensor-memory-accelerator",
                "target": "hw.gpu.memory-hierarchy",
                "type": "depends_on",
            }
        ]

        indexes = build_index.link_guidance_indexes(nodes, edges)

        self.assertEqual(
            indexes["by_keyword"]["tensor memory accelerator"],
            ["hw.gpu.tensor-memory-accelerator"],
        )
        self.assertEqual(
            indexes["by_source"]["nvidia-hopper"],
            ["hw.gpu.memory-hierarchy", "hw.gpu.tensor-memory-accelerator"],
        )
        self.assertEqual(
            indexes["open_questions"],
            [
                {
                    "concept": "hw.gpu.tensor-memory-accelerator",
                    "question": "Which compiler layer exposes TMA?",
                }
            ],
        )
        self.assertEqual(indexes["weakly_connected"], ["hw.gpu.memory-hierarchy"])
        self.assertEqual(
            indexes["unresolved_link_hints"],
            [
                {
                    "source": "hw.gpu.tensor-memory-accelerator",
                    "target": "software.runtime.cuda-streams",
                    "relation": "implemented_by",
                    "reason": "Runtime exposure remains unresolved.",
                }
            ],
        )
```

- [ ] **Step 2: Run the focused tests and verify failure**

Run:

```bash
python3 scripts/test_build_index.py
```

Expected: fail because `parse_frontmatter()` does not parse nested list-of-maps and `link_guidance_indexes()` is not defined.

- [ ] **Step 3: Commit checkpoint if using a clean isolated worktree**

Run only in a clean or isolated worktree:

```bash
git add scripts/test_build_index.py
git commit -m "test: cover link guidance indexing"
```

Expected: commit succeeds. In the current dirty worktree, skip this step.

---

### Task 2: Implement Link Guidance Parsing And Indexes

**Files:**
- Modify: `scripts/build_index.py`
- Modify: `scripts/test_build_index.py`

- [ ] **Step 1: Add nested frontmatter parser helpers**

In `scripts/build_index.py`, add this helper below `parse_scalar()`:

```python
def parse_nested_list(lines: list[str], start_index: int) -> tuple[list[dict[str, Any]], int]:
    items: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    index = start_index
    while index < len(lines):
        raw_line = lines[index]
        if raw_line and not raw_line.startswith(" "):
            break
        stripped = raw_line.strip()
        if not stripped:
            index += 1
            continue
        if stripped.startswith("- "):
            if current is not None:
                items.append(current)
            current = {}
            remainder = stripped[2:].strip()
            if remainder and ":" in remainder:
                key, value = remainder.split(":", 1)
                current[key.strip()] = parse_scalar(value)
        elif current is not None and ":" in stripped:
            key, value = stripped.split(":", 1)
            current[key.strip()] = parse_scalar(value)
        index += 1
    if current is not None:
        items.append(current)
    return items, index
```

- [ ] **Step 2: Update `parse_frontmatter()` to support `link_hints`**

Replace the current loop inside `parse_frontmatter()` with:

```python
    lines = match.group(1).splitlines()
    index = 0
    while index < len(lines):
        raw_line = lines[index]
        line = raw_line.strip()
        if not line or line.startswith("#"):
            index += 1
            continue
        if ":" not in line:
            index += 1
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        if key == "link_hints" and not value.strip():
            nested, index = parse_nested_list(lines, index + 1)
            metadata[key] = nested
            continue
        metadata[key] = parse_scalar(value)
        index += 1
```

- [ ] **Step 3: Add link-guidance fields to nodes**

In the node dictionary created by `read_concepts()`, add:

```python
                "keywords": metadata.get("keywords", []),
                "link_hints": metadata.get("link_hints", []),
                "exploration_questions": metadata.get("exploration_questions", []),
```

- [ ] **Step 4: Add derived index helper functions**

Add these helpers below `group_nodes()`:

```python
def sorted_unique(values: list[str]) -> list[str]:
    return sorted(set(value for value in values if value))


def edge_key(edge: dict[str, Any]) -> tuple[str, str, str]:
    return (
        str(edge.get("source") or ""),
        str(edge.get("target") or ""),
        str(edge.get("type") or ""),
    )


def link_guidance_indexes(nodes: list[dict[str, Any]], edges: list[dict[str, Any]]) -> dict[str, Any]:
    by_keyword: dict[str, list[str]] = {}
    by_source: dict[str, list[str]] = {}
    open_questions: list[dict[str, str]] = []
    unresolved_link_hints: list[dict[str, str]] = []
    degree: dict[str, int] = {str(node.get("id")): 0 for node in nodes}
    accepted_edges = {edge_key(edge) for edge in edges}

    for edge in edges:
        source = str(edge.get("source") or "")
        target = str(edge.get("target") or "")
        if source in degree:
            degree[source] += 1
        if target in degree:
            degree[target] += 1

    for node in nodes:
        node_id = str(node.get("id") or "")
        for keyword in node.get("keywords") or []:
            by_keyword.setdefault(str(keyword), []).append(node_id)
        for source_id in sorted_unique(list(node.get("sources") or []) + list(node.get("source_refs") or [])):
            by_source.setdefault(source_id, []).append(node_id)
        for question in node.get("exploration_questions") or []:
            open_questions.append({"concept": node_id, "question": str(question)})
        for hint in node.get("link_hints") or []:
            if not isinstance(hint, dict):
                continue
            relation = str(hint.get("relation") or hint.get("type") or "")
            target = str(hint.get("target") or "")
            if (node_id, target, relation) in accepted_edges:
                continue
            unresolved_link_hints.append(
                {
                    "source": node_id,
                    "target": target,
                    "relation": relation,
                    "reason": str(hint.get("reason") or ""),
                }
            )

    return {
        "by_keyword": {key: sorted_unique(value) for key, value in sorted(by_keyword.items())},
        "by_source": {key: sorted_unique(value) for key, value in sorted(by_source.items())},
        "open_questions": sorted(open_questions, key=lambda item: (item["concept"], item["question"])),
        "weakly_connected": sorted(node_id for node_id, count in degree.items() if count <= 1),
        "unresolved_link_hints": sorted(
            unresolved_link_hints,
            key=lambda item: (item["source"], item["target"], item["relation"]),
        ),
    }
```

- [ ] **Step 5: Include derived indexes in `main()`**

In the `indexes` dictionary, add:

```python
            "link_guidance": link_guidance_indexes(nodes, all_edges),
```

- [ ] **Step 6: Run tests**

Run:

```bash
python3 scripts/test_build_index.py
python3 scripts/build_index.py
```

Expected:

- `scripts/test_build_index.py` passes.
- `scripts/build_index.py` writes `graph/concept-index.json` without errors.

- [ ] **Step 7: Commit checkpoint if using a clean isolated worktree**

Run only in a clean or isolated worktree:

```bash
git add scripts/build_index.py scripts/test_build_index.py graph/concept-index.json
git commit -m "feat: index link guidance metadata"
```

Expected: commit succeeds. In the current dirty worktree, skip this step.

---

### Task 3: Add Evaluator Tests For Continuous Target Classes

**Files:**
- Modify: `scripts/test_evaluate_exploration.py`
- Modify: `use-cases/fixtures/exploration-loop/index.json`

- [ ] **Step 1: Extend fixture index with link-guidance fields**

Update representative nodes in `use-cases/fixtures/exploration-loop/index.json`:

```json
{
  "id": "hw.gpu.memory-hierarchy",
  "layer": "50-memory-data-movement",
  "parent": "hw.gpu.overview",
  "sources": ["sample-secondary-media"],
  "source_refs": ["sample-secondary-media"],
  "exploration_questions": ["Which runtime layer exposes memory movement mechanisms?"],
  "link_hints": [
    {
      "target": "software.runtime.launch",
      "relation": "depends_on",
      "reason": "Runtime launch behavior affects memory movement overlap."
    }
  ]
}
```

Also add this top-level `indexes` shape:

```json
"indexes": {
  "link_guidance": {
    "open_questions": [
      {
        "concept": "hw.gpu.memory-hierarchy",
        "question": "Which runtime layer exposes memory movement mechanisms?"
      }
    ],
    "unresolved_link_hints": [
      {
        "source": "hw.gpu.memory-hierarchy",
        "target": "software.runtime.launch",
        "relation": "depends_on",
        "reason": "Runtime launch behavior affects memory movement overlap."
      }
    ],
    "weakly_connected": ["software.runtime.launch", "industry.capacity"],
    "by_source": {
      "sample-secondary-media": ["hw.gpu.memory-hierarchy"]
    },
    "by_keyword": {}
  }
}
```

If preserving existing fixture formatting is easier, use `json.dumps(..., indent=2)` from a temporary script, then inspect the diff.

- [ ] **Step 2: Add tests for target classes**

Add these tests inside `ExplorationEvaluatorTests`:

```python
    def test_next_targets_include_open_questions_and_unresolved_link_hints(self) -> None:
        module = load_module()
        payload = module.evaluate(self.load_fixture("rejected"), self.load_index(), LEDGER, "2026-06-24")
        sources = {target["source"] for target in payload["next_targets"]}

        self.assertIn("open_question", sources)
        self.assertIn("unresolved_link_hint", sources)
        self.assertTrue(payload["next_targets"])

    def test_next_targets_remain_non_empty_when_agent_targets_are_filtered_by_pivot(self) -> None:
        module = load_module()
        ledger = self.write_ledger(
            [
                {
                    "id": f"reject-{index}",
                    "timestamp": f"2026-06-{10 + index}T10:00:00",
                    "harness": "exploration-loop",
                    "status": "completed",
                    "decision": "reject",
                    "target_category": "70-execution-architecture",
                    "target_parent": "hw.gpu.overview",
                }
                for index in range(1, 4)
            ]
        )
        manifest = self.load_fixture("rejected")
        manifest["proposed_next_targets"] = [
            {
                "target_category": "70-execution-architecture",
                "target_parent": "hw.gpu.overview",
                "rationale": "Filtered because pivot requires leaving this category.",
            }
        ]

        payload = module.evaluate(manifest, self.load_index(), ledger, "2026-06-24")

        self.assertEqual(payload["run_history"]["direction_policy"], "pivot_required")
        self.assertTrue(payload["next_targets"])
        self.assertTrue(
            all(target["target_category"] != "70-execution-architecture" for target in payload["next_targets"])
        )

    def test_low_quality_source_trail_generates_upgrade_target(self) -> None:
        module = load_module()
        index = self.load_index()
        index["nodes"].append(
            {
                "id": "market.accelerator-rumor",
                "layer": "160-market-narrative",
                "parent": "",
                "sources": ["sample-platform-repost"],
                "source_refs": ["sample-platform-repost"],
            }
        )
        index.setdefault("source_tiers", {})["sample-platform-repost"] = "D"

        payload = module.evaluate(self.load_fixture("rejected"), index, LEDGER, "2026-06-24")

        self.assertIn("source_quality_upgrade", {target["source"] for target in payload["next_targets"]})
```

- [ ] **Step 3: Run evaluator tests and verify failure**

Run:

```bash
python3 scripts/test_evaluate_exploration.py
```

Expected: fail because `next_targets()` does not yet emit `open_question`, `unresolved_link_hint`, or `source_quality_upgrade`.

- [ ] **Step 4: Commit checkpoint if using a clean isolated worktree**

Run only in a clean or isolated worktree:

```bash
git add scripts/test_evaluate_exploration.py use-cases/fixtures/exploration-loop/index.json
git commit -m "test: cover continuous exploration targets"
```

Expected: commit succeeds. In the current dirty worktree, skip this step.

---

### Task 4: Implement Continuous Exploration Target Ranking

**Files:**
- Modify: `scripts/evaluate_exploration.py`

- [ ] **Step 1: Add helpers for index link guidance**

Add these helpers above `next_targets()`:

```python
def index_link_guidance(index: dict[str, Any]) -> dict[str, Any]:
    indexes = index.get("indexes")
    if not isinstance(indexes, dict):
        return {}
    guidance = indexes.get("link_guidance")
    return guidance if isinstance(guidance, dict) else {}


def node_by_id(index: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(node.get("id")): node for node in index_nodes(index)}


def category_for_node(nodes_by_id: dict[str, dict[str, Any]], node_id: str) -> str:
    node = nodes_by_id.get(node_id)
    if not node:
        return ""
    return str(node.get("layer") or "")


def add_candidate(
    candidates: list[dict[str, Any]],
    *,
    target_category: str,
    target_parent: str,
    rationale: str,
    source: str,
    rank_score: float,
) -> None:
    if not target_category:
        return
    candidates.append(
        {
            "target_category": target_category,
            "target_parent": target_parent,
            "rationale": rationale,
            "source": source,
            "rank_score": round(rank_score, 4),
        }
    )
```

- [ ] **Step 2: Add target sources inside `next_targets()`**

Inside `next_targets()` after agent-proposed targets are collected and before graph-gap layer fallback, add:

```python
    guidance = index_link_guidance(index)
    nodes_by_id = node_by_id(index)

    for item in as_list(guidance.get("open_questions")):
        if not isinstance(item, dict):
            continue
        concept = str(item.get("concept") or "")
        category = category_for_node(nodes_by_id, concept)
        if pivot and category == target_category:
            continue
        add_candidate(
            candidates,
            target_category=category,
            target_parent=concept,
            rationale=f"Open exploration question on {concept}: {item.get('question')}",
            source="open_question",
            rank_score=1.35,
        )

    for item in as_list(guidance.get("unresolved_link_hints")):
        if not isinstance(item, dict):
            continue
        source_id = str(item.get("source") or "")
        target_id = str(item.get("target") or "")
        source_category = category_for_node(nodes_by_id, source_id)
        target_category_from_hint = category_for_node(nodes_by_id, target_id)
        category = target_category_from_hint or source_category
        if pivot and category == target_category:
            continue
        add_candidate(
            candidates,
            target_category=category,
            target_parent=target_id or source_id,
            rationale=f"Unresolved link hint {source_id} -> {target_id}: {item.get('reason')}",
            source="unresolved_link_hint",
            rank_score=1.3,
        )

    for node_id in as_list(guidance.get("weakly_connected")):
        concept = str(node_id)
        category = category_for_node(nodes_by_id, concept)
        if pivot and category == target_category:
            continue
        add_candidate(
            candidates,
            target_category=category,
            target_parent=concept,
            rationale=f"Weakly connected concept {concept} needs typed graph repair.",
            source="weak_link",
            rank_score=1.2,
        )

    source_tiers = index.get("source_tiers") if isinstance(index.get("source_tiers"), dict) else {}
    for node in nodes:
        weak_sources = [
            source_id
            for source_id in as_list(node.get("sources"))
            if str(source_tiers.get(str(source_id), "")) in {"C", "D"}
        ]
        if not weak_sources:
            continue
        category = str(node.get("layer") or "")
        if pivot and category == target_category:
            continue
        add_candidate(
            candidates,
            target_category=category,
            target_parent=str(node.get("id") or ""),
            rationale=f"Concept relies on weak sources that need A/B replacement: {', '.join(weak_sources)}.",
            source="source_quality_upgrade",
            rank_score=1.15,
        )
```

- [ ] **Step 3: Preserve graph-gap fallback**

Keep the existing `for category in KNOWN_LAYERS` fallback. This is what guarantees non-empty `next_targets` when link guidance is absent.

- [ ] **Step 4: Run evaluator tests**

Run:

```bash
python3 scripts/test_evaluate_exploration.py
```

Expected: all evaluator tests pass.

- [ ] **Step 5: Commit checkpoint if using a clean isolated worktree**

Run only in a clean or isolated worktree:

```bash
git add scripts/evaluate_exploration.py scripts/test_evaluate_exploration.py use-cases/fixtures/exploration-loop/index.json
git commit -m "feat: rank continuous exploration targets"
```

Expected: commit succeeds. In the current dirty worktree, skip this step.

---

### Task 5: Add Source Tier Policy Tests

**Files:**
- Modify: `scripts/test_evaluate_exploration.py`

- [ ] **Step 1: Add tests for second-hand source treatment**

Add this test inside `ExplorationEvaluatorTests`:

```python
    def test_tier_c_second_hand_source_penalizes_but_does_not_hard_gate(self) -> None:
        module = load_module()
        manifest = self.load_fixture("accepted")
        manifest["proposed_sources"] = [
            {
                "id": "sample-second-hand-business-media",
                "tier": "C",
                "type": "second-hand-media-summary",
            }
        ]
        manifest["proposed_nodes"][0]["sources"] = ["sample-second-hand-business-media"]

        payload = module.evaluate(manifest, self.load_index(), LEDGER, "2026-06-24")

        self.assertNotIn("SOURCE_TIER_D", payload["hard_gate_codes"])
        self.assertGreater(payload["quality_risk_penalty"], 0.0)
        self.assertLess(payload["metrics"]["evidence_strength"]["value"], 1.0)
```

The existing `test_tier_d_source_hard_gate_failure_returns_error()` already covers D-tier rejection.

- [ ] **Step 2: Run evaluator tests**

Run:

```bash
python3 scripts/test_evaluate_exploration.py
```

Expected: pass if existing C-tier penalty behavior is intact. If it fails, inspect `quality_risk_penalty()` and `evidence_strength_score()` before changing policy.

- [ ] **Step 3: Commit checkpoint if using a clean isolated worktree**

Run only in a clean or isolated worktree:

```bash
git add scripts/test_evaluate_exploration.py
git commit -m "test: cover second-hand source penalty"
```

Expected: commit succeeds. In the current dirty worktree, skip this step.

---

### Task 6: Update Policy And Harness Docs

**Files:**
- Modify: `system/source-quality.md`
- Modify: `system/harnesses/exploration-loop.md`
- Modify: `system/ontology.md`
- Modify: `README.md`

- [ ] **Step 1: Update source quality policy**

Replace the existing source tier table in `system/source-quality.md` with:

```markdown
| Tier | Description | Examples |
| --- | --- | --- |
| A | Primary technical, scientific, regulatory, or financial source | Peer-reviewed paper, standard, official architecture doc, official programming guide, SEC filing |
| B | Credible expert or industry analysis with visible method or direct technical detail | Conference talk, reputable teardown, vendor technical blog, analyst report with methods |
| C | Secondary reporting or attributed summary | Business reporting, interview, article rewrite, translated summary, second-hand media post, 36kr-style business article with attribution |
| D | Unverified or weakly attributed source | Social media, forum, unsourced blog, raw LLM answer, content farm, unattributed Chinese platform repost, rumor compilation |
```

Add this section after Acceptance Rules:

```markdown
## Second-Hand And Platform Sources

Publisher reputation does not automatically determine tier. Classify the evidence basis.

- A translated, summarized, or reposted version of a primary source does not inherit the primary source tier.
- 36kr-style business reporting, Chinese platform posts, media rewrites, and attributed second-hand summaries default to Tier C.
- If attribution is missing, circular, unverifiable, or rumor-based, default to Tier D.
- Tier C can support discovery, chronology, and market-narrative drafts, but it cannot verify technical mechanism claims by itself.
- Tier D can create questions only and cannot verify claims.
```

- [ ] **Step 2: Update exploration loop stop semantics**

In `system/harnesses/exploration-loop.md`, add this under Promotion Policy after the forced pivot paragraph:

```markdown
Seed exhaustion is not a stop condition. If an agent reports that it has exhausted all relevant ideas from the seed topic, convert that report into a pivot event and select the next target from open questions, weak graph links, stale layers, sparse layers, source-quality upgrades, source trails, or case-to-pattern generalization.

Layer coverage is not a stop condition. Filling every central stack layer once is only a milestone; long-running mode should continue growing, repairing, cross-linking, and re-evidencing the knowledge base.
```

In Human Controls, add:

```markdown
Invalid stop reasons include: seed exhausted, all layers touched, no current agent-proposed targets, current model cannot think of another idea, or milestone summary completed.
```

- [ ] **Step 3: Update ontology with optional link guidance fields**

Add a section after Concept Coordinates in `system/ontology.md`:

```markdown
## Optional Link Guidance Fields

Concepts may include optional fields that guide future graph repair and exploration:

| Field | Purpose |
| --- | --- |
| `keywords` | Normalized phrases for local candidate-neighbor search |
| `link_hints` | Candidate typed edges that are not yet promoted into `graph/edges.jsonl` |
| `exploration_questions` | Open questions that should feed future exploration targets |

`link_hints` are guidance only. A hint becomes an accepted graph edge only after a harness promotes it into `graph/edges.jsonl`.
```

- [ ] **Step 4: Update README**

Under `Autonomous Exploration Loop`, add:

```markdown
The loop treats seed exhaustion as a pivot signal, not as completion. If the seed direction is exhausted, choose the next target from open questions, weak graph links, stale or sparse layers, source-quality upgrades, source trails, or case-to-pattern generalization.
```

Under `Link Policy`, add:

```markdown
Concepts may also carry optional `keywords`, `link_hints`, and `exploration_questions` frontmatter. These fields guide candidate edge search and future exploration, but `graph/edges.jsonl` remains the accepted typed-edge source of truth.
```

- [ ] **Step 5: Validate harness docs**

Run:

```bash
python3 scripts/validate_harnesses.py
```

Expected: passes.

- [ ] **Step 6: Commit checkpoint if using a clean isolated worktree**

Run only in a clean or isolated worktree:

```bash
git add system/source-quality.md system/harnesses/exploration-loop.md system/ontology.md README.md
git commit -m "docs: define continuous exploration and source tiers"
```

Expected: commit succeeds. In the current dirty worktree, skip this step.

---

### Task 7: Full Verification

**Files:**
- No new files. Verify all changed files.

- [ ] **Step 1: Run indexer tests**

Run:

```bash
python3 scripts/test_build_index.py
```

Expected: all tests pass.

- [ ] **Step 2: Run evaluator tests**

Run:

```bash
python3 scripts/test_evaluate_exploration.py
```

Expected: all tests pass.

- [ ] **Step 3: Rebuild index**

Run:

```bash
python3 scripts/build_index.py
```

Expected: writes `graph/concept-index.json` without errors.

- [ ] **Step 4: Run repo validators**

Run:

```bash
python3 scripts/validate_ontology.py
python3 scripts/validate_harnesses.py
```

Expected: both pass.

- [ ] **Step 5: Check whitespace**

Run:

```bash
git diff --check
```

Expected: no output and exit code 0.

- [ ] **Step 6: Inspect changed files**

Run:

```bash
git status --short
git diff -- docs/superpowers/specs/2026-06-25-continuous-exploration-link-guidance-design.md docs/superpowers/plans/2026-06-25-continuous-exploration-link-guidance.md scripts/build_index.py scripts/test_build_index.py scripts/evaluate_exploration.py scripts/test_evaluate_exploration.py system/source-quality.md system/harnesses/exploration-loop.md system/ontology.md README.md use-cases/fixtures/exploration-loop/index.json
```

Expected: diff shows only the intended implementation plus the approved spec and plan. Existing unrelated dirty files remain untouched.

---

## Self-Review

Spec coverage:

- Candidate connecting edges are covered by Tasks 1 and 2 through `keywords`, `link_hints`, `exploration_questions`, and derived indexes.
- Continuous growth and never-ending loop semantics are covered by Tasks 3, 4, and 6.
- Source classification for second-hand media and Chinese platform reposts is covered by Tasks 5 and 6.
- Backward compatibility is covered by optional fields and unchanged accepted edge source of truth.

Placeholder scan:

- No red-flag markers or unnamed "add tests" steps remain.

Type consistency:

- `link_hints` uses `target`, `relation`, and `reason` in parser tests, indexer output, and evaluator target generation.
- `exploration_questions` are exposed as objects with `concept` and `question` in the derived index.
- `next_targets` keeps existing fields: `target_category`, `target_parent`, `rationale`, `source`, `rank_score`, and `rank`.
