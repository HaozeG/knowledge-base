---
id: physics.materials.interconnect-scaling-limits
title: Wire Delay and the Interconnect Scaling Bottleneck in Advanced VLSI
status: draft
layer: 10-physical-limits-materials
layer_path: 10-physical-limits-materials/interconnect/interconnect-scaling-limits
parent: physics.materials.energy-limits-beyond-cmos
secondary_layers: [20-manufacturing-process-integration, 30-circuit-ip-primitives, 60-interconnect-power-thermal]
granularity: concept
concept_type: physical_limit
scale_scope: [unit, die]
reasoning_roles: [constraint, bottleneck]
tags: [wire-delay, rc-scaling, interconnect, copper, ruthenium, low-k, repeater, resistivity, electron-scattering]
aliases: [interconnect bottleneck, RC delay, wire scaling, copper resistivity wall, BEOL scaling]
sources: [science-copper-interconnect-wall-2025, ieee-irds-interconnect-2025, uta-interconnect-energy-dissertation-2025, ruthenium-interconnect-2025]
---

# Wire Delay and the Interconnect Scaling Bottleneck in Advanced VLSI

## Overview

For most of semiconductor history, transistor switching speed was the performance bottleneck. At advanced nodes (≤5nm), this has inverted: the wires connecting transistors are now slower than the transistors they connect. The RC delay of a minimum-pitch copper interconnect can be 20× the switching time of a FinFET or GAA transistor — meaning data spends more time traveling between logic gates than being processed by them.

- [supported][src:science-copper-interconnect-wall-2025] At ~15 nm wire width (2nm-class node minimum pitch), copper interconnect RC delay reaches 20× the transistor switching speed. This is a physical limit rooted in copper's 40 nm electron mean free path — when wire widths fall below the mean free path, surface and grain-boundary scattering dominate, causing resistivity to increase super-linearly. A 15 nm copper wire has roughly 3–4× the resistivity of bulk copper.
- [supported][src:ieee-irds-interconnect-2025] The IEEE IRDS roadmap projects tight-pitch interconnect resistance rising from 474 Ω/μm (2025, 2.1nm equivalent) to 920 Ω/μm (2028, 1.5nm) to ~1,450 Ω/μm (2031, 1.0nm equivalent). Each node transition worsens the wire delay problem independently of transistor improvement.
- [inference] The interconnect bottleneck is the physical reason why clock frequencies stopped scaling around 2005 and why architectures shifted toward parallelism (multi-core, GPU, AI accelerators). If wire delay doesn't scale, the only way to get more work done per unit time is to do more independent work in parallel. AI accelerators are, at the physical level, an architectural response to the wire delay problem.

## The Physics of RC Delay

### Why Wires Get Slower When Transistors Get Faster

- [inference] The RC delay of a wire of length L scales as R × C × L². Transistor gate delay scales as C_gate × V_dd / I_on, which improves with each node (smaller C_gate, lower V_dd). Wire RC delay does not automatically improve — in fact, it worsens because:
  - **Resistance (R)** increases as cross-sectional area shrinks, compounded by surface scattering at narrow widths
  - **Capacitance (C)** does not decrease proportionally because wire spacing scales with pitch, maintaining sidewall coupling
  - **Length (L)** between logic gates does not scale — chip die size remains roughly constant, so global wire lengths are unchanged
- [inference] The result: local interconnect delay (within a standard cell) scales mildly with technology. Semi-global interconnect delay (between functional blocks, 100–1,000 μm) stays roughly constant. Global interconnect delay (across the die, >1 mm) worsens with each node because repeaters add their own gate delays that don't scale as fast as wire RC increases.

### The Repeater Solution and Its Limits

- [inference] Inserting repeaters (inverters) at regular intervals changes RC delay from O(L²) to O(L) — each repeater segment has a fraction of the total RC. The optimal repeater spacing is L_opt = sqrt(R_driver × C_wire / (R_wire × C_input)). As wire resistance increases at advanced nodes, L_opt shrinks, requiring more repeaters per wire. Eventually the repeaters consume more area and power than the logic they connect — the "repeater wall."
- [inference] At 2nm-class nodes, the optimal repeater spacing for minimum-pitch copper is ~50–100 μm, requiring 100–200 repeaters for a 10 mm global wire. Each repeater adds ~5–10 ps of gate delay and ~1–2 μW of leakage. For a chip with 10,000 global wires, repeaters alone can consume 10–20W of power — before any useful logic is done.

## Material Solutions Beyond Copper

### Ruthenium (Ru)

- [supported][src:ruthenium-interconnect-2025] Ruthenium has an electron mean free path of 6.6 nm (vs. copper's 40 nm), making it substantially more conductive than copper at sub-10 nm widths. At 6 nm line width, Ru resistivity including barrier is approximately half of copper's. TSMC and Intel are qualifying Ru for M0–M2 local interconnect layers at N2/20A nodes.
- [inference] Ru's main disadvantage: higher bulk resistivity (7.1 μΩ·cm vs. copper's 1.68 μΩ·cm). This means Ru outperforms Cu only at very narrow widths (<12 nm); for wider upper-level metal (global interconnects), copper remains superior. The likely end-state is a dual-metal stack: Ru for local interconnect (M0–M2), Cu for semi-global and global (M3+).

### Cobalt, Topological Semimetals, and Airgaps

- [inference] Cobalt (Co) is already used for M0 in some processes (TSMC N7+) because of better gap-fill in narrow trenches and higher electromigration resistance. Its resistivity is higher than Cu at all widths, making it a manufacturability choice, not a performance one.
- [inference] Topological semimetals (NbAs, NbP, CoSi) exhibit a counterintuitive property: resistivity decreases with shrinking dimensions because topologically protected surface states carry current with reduced backscattering. At <10 nm widths, MoP shows line resistance comparable to Cu and Ru. However, integration into CMOS BEOL flows remains at the research stage (2025).
- [inference] Airgaps (k=1.0, replacing low-k dielectric at k~2.5) reduce wire capacitance by up to 17% — significant but not transformative. The integration challenge is mechanical: airgap structures must survive CMP (chemical-mechanical planarization) and thermal cycling without collapsing. Selective removal of sacrificial layers is the preferred integration path.

## Impact on AI Accelerator Architecture

- [inference] The interconnect bottleneck is a first-order constraint on AI accelerator design:
  - **Systolic arrays** minimize wire delay by connecting PEs directly (nearest-neighbor only), avoiding global wires for data movement — they are an architectural answer to the wire delay problem.
  - **HBM integration** places memory as close as physically possible to compute (silicon interposer, ~100 μm gap), minimizing the wire length between memory and logic — a packaging answer to the wire delay problem.
  - **Chiplet disaggregation** accepts that global wires across a monolithic die are too slow and breaks the die into smaller chiplets with local interconnect, connected by SerDes — a system-level answer to the wire delay problem.
- [inference] The physical limit narrative: transistors got faster, wires didn't. Every major AI accelerator architectural innovation — systolic arrays, HBM, chiplets, NoC, 3D stacking — is, at root, a strategy for reducing the distance data must travel on wires.

## Open Questions

- OPEN: Can topological semimetals transition from research to production BEOL by 2030, or will the CMOS industry settle on Ru for local interconnect and accept the scaling slowdown?
- OPEN: At what wire width does the interconnect problem become unsolvable by material substitution alone, forcing a transition to optical or superconducting on-chip interconnects?
- VERIFY: The claimed 20× RC delay vs. transistor switching at 15 nm width is from a 2025 Science article based on IRDS projections — actual silicon measurements at 2nm-class nodes are not yet publicly available.

## See Also

- [[physics.materials.energy-limits-beyond-cmos]] — Beyond-CMOS device physics that the interconnect bottleneck complements.
- [[silicon.process.node-selection-fabrication-ai]] — Process node selection where interconnect scaling constrains die size and design.
- [[chip.circuit.digital-ip-blocks-ai-soc]] — Digital IP blocks where repeaters and wire planning are critical.
- [[hw.riscv.power-thermal-interconnect]] — Power/thermal modeling where wire RC contributes to total power.
- [[silicon.process.advanced-packaging-ai]] — Advanced packaging as a response to the interconnect bottleneck.
- [[chip.circuit.serdes-io-phy-ai-chiplets]] — SerDes as the bridge between die-level interconnect and package-level interconnect.
