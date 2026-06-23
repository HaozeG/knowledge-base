# Agent Writing Guide

Agents should treat this repository as a durable knowledge system, not as a scratchpad.

## Write Path

0. Start from `system/agent-operating-manual.md` and choose one harness under `system/harnesses/`.
1. Put raw notes and unprocessed source snippets under `inbox/`.
2. Register candidate sources in `sources/source-registry.yaml`.
3. Create or update concept pages under `concepts/`.
4. Add typed graph edges to `graph/edges.jsonl`.
5. Run `python3 scripts/build_index.py`.
6. Run `python3 scripts/validate_ontology.py`.
7. Run `python3 scripts/validate_harnesses.py` after harness or system edits.
8. Record meaningful runs in `system/run-ledger.jsonl`.

## Concept Page Rules

- Use English in stored files.
- Keep frontmatter flat so local tooling can parse it without dependencies.
- Prefer stable first-principle explanations over news-driven framing.
- Mark uncertainty directly.
- Use source IDs, not only raw URLs, in claims.
- Do not mark a page `verified` unless important claims have adequate citations.

## Edit Safety

- Preserve existing user notes unless asked to consolidate them.
- Do not delete raw source material after processing.
- Do not silently change source quality tiers.
- Do not upgrade claim status without evidence.
- Do not mix stock conclusions into technical concepts; link to market concepts instead.

## Instructive Marks

Use these marks consistently:

- `TODO:` missing content.
- `OPEN:` unanswered question.
- `VERIFY:` claim needs stronger citation.
- `ASSUMPTION:` explicit reasoning step.
- `DO_NOT_MERGE:` known conflict or unresolved contradiction.
