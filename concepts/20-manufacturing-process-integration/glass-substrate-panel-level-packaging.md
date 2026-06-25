---
id: silicon.process.glass-substrate-advanced-packaging
title: Glass Core Substrates and Panel-Level Packaging for AI Chips
status: draft
layer: 20-manufacturing-process-integration
layer_path: 20-manufacturing-process-integration/packaging/glass-substrate-panel-level
parent: silicon.process.advanced-packaging-ai
secondary_layers: [10-physical-limits-materials, 60-interconnect-power-thermal, 150-supply-chain-business]
granularity: concept
concept_type: manufacturing_method
scale_scope: [package, ecosystem]
reasoning_roles: [enabler, bottleneck, bottleneck_mitigation]
tags: [glass-substrate, panel-level-packaging, FOPLP, CoPoS, advanced-packaging, Intel, Absolics]
aliases: [glass core substrate, panel-level packaging, FOPLP, glass interposer, CoPoS]
sources: [intel-glass-core-clearwater-2026, wedbush-glass-substrate-age-2026, tsmc-copos-panel-level-2025]
---

# Glass Core Substrates and Panel-Level Packaging for AI Chips

## Overview

Organic substrates (ABF, BT resin) have been the standard packaging material for decades, but they are reaching fundamental limits at the die sizes (~800 mm² reticle limit × multiple chiplets) and power levels (1,000W+) of modern AI accelerators. Glass core substrates offer a step-change improvement: glass has 10–100× lower signal loss, 3–10× higher dimensional stability (CTE matched to silicon at 3–9 ppm/°C), and can support 10× finer through-glass via (TGV) pitch than organic substrates. Panel-level packaging (FOPLP) extends this to rectangular panels (500×500 mm+) rather than round wafers (300 mm diameter), increasing area utilization from ~45% to ~81% and reducing cost by 10–20%.

- [supported][src:intel-glass-core-clearwater-2026] Intel Clearwater Forest (Xeon 6+) began shipping in January 2026 — the first mass-produced chips using glass core substrates. The 10-2-10 stack (10 redistribution layers + 800 µm glass core + 10 RDL layers) with Foveros Direct 3D bonding at <45 µm bump pitch demonstrates glass is production-ready for high-volume manufacturing.
- [supported][src:wedbush-glass-substrate-age-2026] Absolics (SKC subsidiary) is building the world's first dedicated commercial glass substrate production line in Covington, Georgia ($600M investment, CHIPS Act funded), targeting late 2026 mass production with 500×500 mm panels. Prototypes are under evaluation by AMD and AWS. This represents the first neutral (non-Intel) glass substrate supply for the broader AI chip industry.
- [inference] Glass substrates represent the packaging industry's answer to the CoWoS bottleneck: if glass interposers can match silicon interposer performance at panel-level costs, the CoWoS capacity constraint is broken. Glass is the only material that combines the electrical performance of silicon (low loss tangent) with the dimensional scalability of organic substrates (large panels, square format).

## Why Glass Now

### Material Properties

| Property | Organic (ABF) | Silicon | Glass | Advantage |
|---|---|---|---|---|
| Dielectric loss (Df) | 0.01–0.02 | 0.001–0.005 | 0.001–0.005 | 10× better than organic |
| CTE (ppm/°C) | 15–18 | 2.6 | 3–9 | Matches silicon |
| Surface roughness | ~500 nm | <1 nm | <1 nm | Enables fine-pitch RDL |
| Panel size | 510×515 mm | 300 mm (round) | 500×500 mm+ | 81% area utilization |
| Young's modulus | ~25 GPa | 170 GPa | 70–90 GPa | Resists warpage |

- [inference] The CTE match between glass (3–9 ppm/°C) and silicon (2.6 ppm/°C) is the killer feature: organic substrates expand 5–7× more than silicon when heated, creating thermal stress at the die-to-substrate interface that limits bump pitch and stack height. Glass eliminates this mismatch, enabling finer bump pitch (<45 µm) and taller stacks (16+ layers of HBM) without thermal cycling failure.

### Panel-Level Economics

- [supported][src:tsmc-copos-panel-level-2025] TSMC's CoPoS (Chip-on-Panel-on-Substrate) roadmap starts from 310×310 mm panels in 2026, with volume production targeted for 2028–2029. NVIDIA is named as the first strategic partner. The panel format exploits the natural rectangular shape of AI accelerator packages, achieving ~81% area utilization vs. ~45% for round wafers — a 1.8× density advantage that translates to ~10–20% cost reduction per packaged chip.
- [inference] The panel-level transition mirrors the semiconductor industry's historical shift from 200mm to 300mm wafers (1990s–2000s), where the larger format enabled economies of scale that smaller formats could not match. The economic driver is the same: larger panels amortize the fixed cost of lithography, deposition, and inspection across more chips per panel. The difference: 300mm → 500mm+ is a shape change (round → rectangular) as well as a size change, which requires retooling the entire packaging line.

## Challenges and Risks

### Manufacturing Defects

- [inference] Glass is brittle: through-glass via (TGV) drilling, wafer dicing, and thermal cycling all create microcrack risks (industry term: SeWaRe — Severe Wafer-level Reliability issues). Intel's NoSeWaRe demonstration (NEPCON Japan, January 2026) showed crack-free 78×77 mm glass packages, proving the manufacturing process is viable but not trivial. The main techniques: LPKF's LIDE (Laser Induced Deep Etching) for crack-free TGV formation, and CTE-tailored glass formulations (Corning, Schott, AGC) to balance silicon-matching vs. PCB-matching requirements.

### Supply Chain Concentration

- [inference] The glass substrate supply chain mirrors the EUV supply chain in its concentration: Corning, Schott, AGC, and NEG control the specialty glass market; LPKF controls the LIDE TGV drilling equipment; DISCO controls precision dicing; Onto Innovation controls glass substrate inspection. This concentration creates the same single-source risk that CoWoS creates for advanced packaging — a production interruption at any single supplier cascades through the entire AI chip supply chain.

## Open Questions

- OPEN: Can glass substrates match silicon interposer reliability for >10-year datacenter deployments (thermal cycling, humidity, mechanical stress), or will organic substrates remain preferred for reliability-critical applications despite lower performance?
- OPEN: Will the panel-level transition (FOPLP, CoPoS) break the TSMC CoWoS monopoly, or will TSMC's first-mover advantage in panel-level glass packaging extend its dominance from wafer-level to panel-level packaging?
- VERIFY: Intel's Clearwater Forest glass substrate yield is not publicly disclosed — the "mass production" claim may represent low single-digit percentage yields that are economically non-viable for price-sensitive markets.

## See Also

- [[silicon.process.advanced-packaging-ai]] — Advanced packaging overview that glass substrates extend.
- [[silicon.process.3d-integration-ai]] — 3D integration where glass interposers enable finer-pitch stacking.
- [[industry.ai.supply-chain-bottlenecks]] — CoWoS bottleneck that glass substrates may alleviate.
- [[silicon.process.node-selection-fabrication-ai]] — Process node economics affected by packaging cost structure.
- [[system.scale.chiplet-architecture]] — Chiplet architecture where glass interposers connect multiple dies.
- [[system.power.ai-accelerator-power-delivery]] — PDN where glass's dimensional stability enables vertical power delivery.
