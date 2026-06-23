# Source Quality Policy

The knowledge base should separate durable technical facts from interpretations and market narratives.

## Source Tiers

| Tier | Description | Examples |
| --- | --- | --- |
| A | Primary technical or scientific source | Peer-reviewed paper, standard, official architecture doc, official programming guide, SEC filing |
| B | Credible expert or industry analysis | Conference talk, reputable teardown, vendor blog with technical detail, analyst report with methods |
| C | News or secondary summary | Business reporting, interview, article summarizing technical facts |
| D | Unverified source | Social media, forum, unsourced blog, raw LLM answer |

## Acceptance Rules

- A concept can be `seed` without citations.
- A concept can be `draft` with candidate citations and clear open questions.
- A concept should become `verified` only when its important claims cite A-tier or strong B-tier sources.
- D-tier sources can create questions, but cannot verify claims.
- Market claims must cite their own evidence and must not inherit certainty from technical facts.

## Claim Format

Use explicit claim lines when a page is intended to become verified:

```text
- [supported][src:nvidia-cuda-programming-guide-v13.3] A CUDA kernel is executed by many threads organized into blocks and grids.
- [inference][src:williams-roofline-2009] A kernel with low arithmetic intensity is usually more sensitive to memory bandwidth than peak compute throughput.
```

## Review Questions

- Is the claim technical, economic, or speculative?
- Is the citation primary enough for the claim?
- Does the claim confuse vendor-specific behavior with general GPU architecture?
- Does the page distinguish mechanism from consequence?
- Does the page expose open questions instead of hiding uncertainty?

