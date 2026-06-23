# Ontology

The ontology gives agents and humans a shared map for placing concepts.

## Layers

| Layer | Prefix | Scope |
| --- | --- | --- |
| Silicon | `silicon.*` | Devices, process nodes, lithography, yield, power, thermal limits |
| Chip | `chip.*` | Die architecture, memory, interconnect, packaging, accelerators |
| HW/SW System | `hw.*` | GPU systems, CPU/GPU interaction, compilers, runtimes, kernels |
| Programmer | `programmer.*` | Performance models, APIs, frameworks, workload mapping |
| Industry | `industry.*` | Supply chain, capex, capacity, pricing power, company strategy |
| Market | `market.*` | Investor narratives, hype cycles, valuation logic, risk framing |

## Edge Types

Use typed edges when a relationship should appear in a graph UI.

| Type | Meaning |
| --- | --- |
| `decomposes_into` | A concept breaks into smaller concepts |
| `depends_on` | A concept requires another concept to make sense |
| `constrained_by` | A physical, economic, or software constraint limits a concept |
| `enables` | One concept creates a capability used by another |
| `competes_with` | Concepts are alternative approaches |
| `measured_by` | A metric or model evaluates a concept |
| `implemented_by` | A software or hardware mechanism realizes a concept |
| `explains_market_logic_for` | A technical concept explains an industry or market narrative |
| `mentions` | A weak link extracted from Markdown wikilinks |

## Claim Status

| Status | Meaning |
| --- | --- |
| `verified` | Backed by strong source evidence |
| `supported` | Backed by credible but incomplete evidence |
| `inference` | Reasoned from verified or supported concepts |
| `speculative` | Useful hypothesis, not accepted as fact |
| `open` | Needs investigation |

## First-Principle Axes

Prefer explanations that reduce a concept to stable constraints:

- Energy movement: moving data usually costs energy and time.
- Distance: physical distance affects latency, bandwidth, power, and clocking.
- Parallelism: throughput comes from doing many independent operations at once.
- Locality: reuse near compute reduces pressure on distant memory.
- Precision: numerical format affects bandwidth, storage, hardware area, and accuracy.
- Yield: larger and more complex manufacturing surfaces increase defect exposure.
- Utilization: peak capability matters only when software can keep hardware busy.

