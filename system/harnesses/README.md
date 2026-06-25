# Harnesses

Harnesses define how agents may operate on this knowledge base.

Each harness specifies:

- objective
- mutable surfaces
- immutable surfaces
- sensors
- actuators
- evaluator
- promotion policy
- logging contract
- human controls

Agents should pick one harness per task. Combining harnesses is allowed only when one is clearly the object-level loop and the other is a review loop.

## Available Harnesses

| Harness | Purpose |
| --- | --- |
| `knowledge-ingestion.md` | Convert sources and notes into concept drafts |
| `ontology-review.md` | Place concepts and improve hierarchy |
| `concept-review.md` | Review concept quality and verification readiness |
| `query-synthesis.md` | Answer questions from the KB with citations and uncertainty |
| `graph-export.md` | Regenerate and validate graph/index artifacts |
| `exploration-loop.md` | Run long-lived, metric-gated autonomous exploration with temporary staging |
| `cheap-model-drift-audit.md` | Audit low-cost exploration runs for procedural and format drift |
| `meta-harness.md` | Change the system design, ontology, policies, harnesses, or validators |
