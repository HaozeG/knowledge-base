# Query Synthesis Harness

## Purpose

Answer user questions using the knowledge base as the retrieval and reasoning entry point.

## Objective

Produce higher-quality answers than generic LLM responses by grounding answers in verified concepts, citations, graph relationships, and open questions.

## Mutable Surfaces

- `use-cases/`
- `system/run-ledger.jsonl`

Optional, only if the user asks to preserve the result:

- concept pages
- graph edges

## Immutable Surfaces

- source registry tiers
- concept verification status
- ontology
- harness contracts

## Sensors

Read:

- `graph/concept-index.json`
- relevant concept pages
- source registry entries
- related use-case records

Run after any edits:

```bash
python3 scripts/build_index.py
python3 scripts/validate_ontology.py
```

## Actuators

- Produce answer with mechanism, citations, related concepts, open questions, and market logic if applicable.
- Record query test as a use case when evaluating quality.
- Suggest concept gaps.

## Evaluator

Pass when the answer:

- separates mechanism from narrative
- distinguishes verified, supported, inferred, and speculative claims
- cites source IDs or concept pages
- surfaces related concepts
- names open questions

Fail when the answer:

- invents citations
- treats market movement as technical proof
- hides uncertainty
- bypasses existing concept structure

## Promotion Policy

Query answers do not promote concepts. They can propose ingestion or review tasks.

## Logging Contract

For recorded query tests, store the question, retrieved concepts, synthesized answer, quality score, and missing concepts in `use-cases/`.

## Human Controls

Escalate financial, investment, or legal conclusions. The KB can explain mechanisms and hypotheses, not provide investment advice.

