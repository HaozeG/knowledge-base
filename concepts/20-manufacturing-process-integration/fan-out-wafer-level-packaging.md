---
id: silicon.process.fan-out-wafer-level-packaging
title: Fan-Out Wafer-Level Packaging (FOWLP) for AI and Mobile Chips
status: draft
layer: 20-manufacturing-process-integration
layer_path: 20-manufacturing-process-integration/packaging/fan-out-wlp
parent: silicon.process.advanced-packaging-ai
secondary_layers: [30-circuit-ip-primitives, 60-interconnect-power-thermal, 150-supply-chain-business]
granularity: concept
concept_type: manufacturing_method
scale_scope: [package, ecosystem]
reasoning_roles: [enabler, bottleneck]
tags: [fan-out, wafer-level-packaging, FOWLP, InFO, RDL, molding-compound]
aliases: [FOWLP, fan-out WLP, wafer-level fan-out, integrated fan-out, InFO]
sources: [tsmc-info-advanced-packaging-2025]
---

# Fan-Out Wafer-Level Packaging (FOWLP) for AI and Mobile Chips

## Overview

Fan-out wafer-level packaging (FOWLP) embeds semiconductor dies in a molded wafer and builds redistribution layers (RDL) that "fan out" beyond the die edges, creating a larger package footprint without a traditional substrate. Unlike flip-chip packaging (which requires an organic substrate between die and PCB) or silicon interposer packaging (CoWoS, which requires an expensive silicon interposer), FOWLP achieves fine-pitch interconnects at lower cost by using molded epoxy compound and thin-film RDL directly on the reconstituted wafer.

- [supported][src:tsmc-info-advanced-packaging-2025] TSMC's InFO (Integrated Fan-Out) is the dominant FOWLP technology, used in Apple's A-series and M-series processors since 2016. InFO-PoP (Package-on-Package) stacks mobile DRAM directly on the fan-out package, achieving <0.5mm total package height. InFO-oS (on Substrate) extends FOWLP to larger die sizes (>400mm²) by mounting the fan-out package on an organic substrate. InFO-Ai targets AI accelerators specifically, integrating multiple chiplets with fine-pitch RDL.
- [inference] FOWLP occupies a strategic middle ground in the packaging hierarchy: cheaper than CoWoS (silicon interposer) but with finer pitch than standard flip-chip. For AI accelerators where cost sensitivity limits CoWoS adoption (inference chips, edge accelerators), FOWLP provides ~70% of the interconnect density at ~40% of the cost. The trade-off: FOWLP's molded compound has higher CTE mismatch (~10 ppm/°C) with silicon than silicon interposer (~2.6 ppm/°C), limiting the maximum package size before thermal cycling reliability becomes a concern.

## Process Flow and Architecture

### Reconstitution and RDL

- [inference] FOWLP process: (1) known-good dies are placed face-down on a temporary carrier with precise spacing; (2) epoxy molding compound encapsulates the dies, forming a "reconstituted wafer"; (3) the carrier is removed and thin-film RDL layers (copper traces + polyimide dielectric) are built on the active face, redistributing die pads to a larger array of solder bumps; (4) the molded wafer is diced into individual packages. The key enabling technology is the ability to build multi-layer RDL with line/space of 2/2μm or finer — approaching the density of chip-level BEOL.
- [inference] RDL line/space is the critical performance parameter: 2/2μm RDL supports ~2,500 bumps per mm²; 5/5μm supports ~500 bumps per mm². For AI accelerators with HBM interfaces requiring thousands of die-to-die connections, RDL density directly determines whether FOWLP can serve as a CoWoS alternative. TSMC's InFO-Ai targets 2/2μm RDL for chiplet integration; ASE's FOCoS (Fan-Out Chip on Substrate) targets 5/5μm for cost-sensitive applications.

### Comparison with Alternatives

| Technology | Die-to-Die Pitch | Relative Cost | Max Package Size | Best For |
|---|---|---|---|---|
| CoWoS (Si interposer) | <1μm | 1.0× (reference) | >3× reticle | Training GPUs, HPC |
| FOWLP (InFO) | 2–5μm | 0.3–0.5× | ~1.5× reticle | Inference, mobile, edge |
| EMIB (Intel) | <10μm | 0.5–0.7× | Flexible (local bridges) | Heterogeneous integration |
| Flip-chip (organic) | >20μm | 0.1–0.2× | Unlimited | Low-cost, low-density |

## Open Questions

- OPEN: Can FOWLP's RDL density (currently 2/2μm) reach 1/1μm by 2028, making it a viable CoWoS alternative for training-class AI accelerators, or does the CTE mismatch impose an irreducible reliability limit at sub-2μm pitch?
- OPEN: Will FOWLP's cost advantage over CoWoS persist as panel-level processing (FoPLP) scales, or will CoWoS's wafer-level efficiency improvements close the gap?
- VERIFY: The claim that FOWLP achieves ~70% of CoWoS interconnect density at ~40% cost is an industry estimate — actual cost-per-interconnect depends on volume and specific package design.

## See Also

- [[silicon.process.advanced-packaging-ai]] — Advanced packaging overview that FOWLP instantiates.
- [[silicon.process.3d-integration-ai]] — 3D integration where FOWLP serves as the base package for stacked configurations.
- [[system.scale.chiplet-architecture]] — Chiplet architecture where FOWLP provides the physical chiplet-to-chiplet interconnect.
- [[silicon.process.glass-substrate-advanced-packaging]] — Glass substrates that may replace molded compound in future FOWLP generations.
- [[silicon.process.node-selection-fabrication-ai]] — Process node selection where packaging cost structure affects node choice.
- [[industry.ai.supply-chain-bottlenecks]] — CoWoS bottleneck that FOWLP provides an alternative path around.
