---
id: chip.circuit.serdes-io-phy-ai-chiplets
title: SerDes and High-Speed I/O PHYs for AI Chiplet Interconnects
status: draft
layer: 30-circuit-ip-primitives
layer_path: 30-circuit-ip-primitives/serdes-io-phy/ai-chiplet-interconnects
parent: chip.circuit.digital-ip-blocks-ai-soc
secondary_layers: [20-manufacturing-process-integration, 60-interconnect-power-thermal, 120-scale-up-system]
granularity: concept
concept_type: component
scale_scope: [die, package, rack]
reasoning_roles: [enabler, bottleneck, constraint]
tags: [serdes, phy, ucie, chiplet, pam4, pll, clock-distribution, io-die, co-packaged-optics, d2d]
aliases: [high-speed I/O for chiplets, D2D PHY, SerDes for AI, chiplet IO die, UCIe PHY]
sources: [ucie-spec-2-0-2024, alphawave-alphachip1600-2025, synopsys-1p6t-ethernet-2025, analog-bits-tsmc-n3p-n2p-2025, perceptia-ppll03-2025, silicon-creations-clocking-ipsoc-2025, lightmatter-synopsys-cpo-2026, keysight-ucie-phy-designer-2025]
---

# SerDes and High-Speed I/O PHYs for AI Chiplet Interconnects

## Overview

AI accelerator scaling has hit the reticle limit (~800 mm² per die). Chiplet disaggregation is the industry's answer — breaking a monolithic die into smaller compute, memory, and I/O chiplets connected through high-speed die-to-die (D2D) interfaces. At the physical layer, all chiplet communication depends on SerDes (Serializer/Deserializer) and PHY (physical layer) IP that converts parallel on-die data to serial off-die signals and back.

- [supported][src:ucie-spec-2-0-2024] UCIe 2.0 defines a D2D PHY supporting up to 32 GT/s per pin, 0.8–1.2 pJ/bit energy efficiency, and 6–9 ns end-to-end latency across standard and advanced packaging.
- [supported][src:alphawave-alphachip1600-2025] Silicon-proven I/O chiplets (AlphaCHIP1600-IO) demonstrate 16 lanes of 112G multi-standard SerDes delivering 1.6 Tbps aggregate bandwidth, integrating UCIe, PCIe 6.0, and 800G Ethernet in a single die.
- [inference][src:synopsys-1p6t-ethernet-2025] The SerDes data rate roadmap (112G → 224G PAM4) is paced by AI cluster bandwidth demands — 1.6T Ethernet requires 224G lanes, and the 45 dB channel loss budget at these rates drives DSP-based equalization architectures.

## The SerDes PHY in AI Accelerators

### Why SerDes Matters for AI

Every bit crossing a die boundary in a multi-die AI accelerator must travel through a SerDes PHY. The PHY's energy per bit, bandwidth density, and latency directly constrain:

- **Chiplet bandwidth**: tensor parallelism over chiplets requires 100s of GB/s per chiplet edge — SerDes lane count and per-lane rate set the ceiling.
- **Package cost**: lower-loss channels (silicon interposer vs. organic substrate) reduce SerDes power but increase packaging cost — the PHY-channel co-design determines system TCO.
- **Scale-up vs. scale-out boundary**: the latency gap between on-package UCIe (~6 ns) and off-package Ethernet (~1 μs) determines which operations stay local and which go distributed.

- [inference] A 16-lane UCIe 2.0 link at 32 GT/s delivers 512 GB/s per edge. For a typical 4-chiplet AI accelerator, four such edges provide 2 TB/s of aggregate chiplet bandwidth — comparable to HBM3 bandwidth (~3–4 TB/s) but at 0.8 pJ/bit vs. HBM's ~3–4 pJ/bit.

### Electrical Signaling: NRZ → PAM4 → 224G

| Generation | Signaling | Per-Lane Rate | Channel Loss Budget | Power | Status (2025) |
|---|---|---|---|---|---|
| 56G (PCIe 5.0) | NRZ | 32 GT/s | ~30 dB | ~5 pJ/bit | Legacy production |
| 112G (PCIe 6.0) | PAM4 | 64 GT/s | ~36 dB | ~3 pJ/bit | Mainstream production |
| 224G (PCIe 7.0) | PAM4 | 128 GT/s | ~45 dB | ~5 pJ/bit | Sampling, early production |

- [supported][src:alphawave-alphachip1600-2025] 112G PAM4 SerDes is the current production standard for AI chiplet I/O, achieving ~3 pJ/bit in advanced nodes (5nm/3nm). The WidEye™ DSP architecture provides adaptive equalization across 36+ dB channels.
- [inference][src:synopsys-1p6t-ethernet-2025] 224G PAM4 doubles per-lane bandwidth but requires significant DSP investment: the 45 dB channel loss target demands multi-tap DFE (Decision Feedback Equalization) and FEC (Forward Error Correction), which add ~20–30 ns of latency and ~30% power overhead vs. 112G.

## UCIe: The Die-to-Die Interconnect Standard

UCIe (Universal Chiplet Interconnect Express) is the open standard for D2D communication, jointly developed by Intel, AMD, Arm, TSMC, Samsung, and hyperscalers. It defines both the protocol layer (CXL/PCIe compatible) and the PHY layer (electrical and optical).

- [supported][src:ucie-spec-2-0-2024] UCIe 2.0 (August 2024) supports 32 GT/s per pin, 3D hybrid bonding packaging, quarter-rate clocking, and variable link width. BER targets range from 10⁻¹² (standard packaging) to 10⁻¹⁵ (advanced packaging with FEC).
- [inference] UCIe's dual-mode architecture is key to AI accelerator design: **UCIe-S** (standard package, organic substrate) for lower-cost scale-out chiplet links at 16–24 GT/s, and **UCIe-A** (advanced package, silicon interposer/bridge) for high-bandwidth scale-up links at 24–32 GT/s with sub-1 pJ/bit efficiency.
- [inference] The UCIe 3.0 roadmap targets 64 GT/s per lane and native optical integration, which would enable optical chiplet-to-chiplet links with sub-pJ/bit energy at cm-to-meter distances — blurring the boundary between on-package and off-package communication.

### UCIe PHY Architecture

```text
┌──────────────────────────────────────────┐
│  UCIe Protocol Layer (CXL.io / PCIe /    │
│  streaming / raw mode)                   │
├──────────────────────────────────────────┤
│  UCIe D2D Adapter (link state, CRC,     │
│  retry, lane repair)                     │
├──────────────────────────────────────────┤
│  UCIe PHY (TX FIFO → serializer →       │
│  driver → channel → CTLE/DFE →          │
│  deserializer → RX FIFO)                │
├──────────────────────────────────────────┤
│  Channel (organic substrate / silicon    │
│  interposer / hybrid bond)              │
└──────────────────────────────────────────┘
```

- [inference] The PHY's CTLE (Continuous Time Linear Equalizer) + DFE (Decision Feedback Equalizer) chain compensates for channel loss. For UCIe-A on silicon interposer (~2–5 dB loss), a simple CTLE suffices at <0.5 pJ/bit. For UCIe-S on organic substrate (~20–36 dB loss), a full CTLE + multi-tap DFE is required at 1–2 pJ/bit.

## Analog and Mixed-Signal IP for AI SoCs

Beyond the SerDes data path, every AI accelerator SoC requires a suite of analog/mixed-signal IP to function:

### Clock Distribution and PLLs

- [supported][src:perceptia-ppll03-2025] All-digital PLLs (e.g., Perceptia pPLL03) provide <4.2 ps peak jitter at up to 5 GHz, with fractional-N synthesis for generating multiple clock domains from a single reference. For AI accelerators with heterogeneous chiplets (compute at N3, I/O at N7, memory at N5), per-chiplet PLLs must maintain <1 ps skew across the package for synchronous D2D links.
- [supported][src:silicon-creations-clocking-ipsoc-2025] Clock distribution in multi-die AI SoCs must account for power delivery network (PDN) noise coupling into PLL supply rails — supply-induced jitter can exceed intrinsic PLL jitter by 2–3× if the PDN resonance aligns with clock modulation frequencies.
- [inference] Pinless PLL architectures (where the LC tank is integrated on-die without external crystal pins) are becoming standard for AI chiplets because external clock pins consume scarce bump/ball allocation and are vulnerable to package-induced phase noise.

### Power Delivery and Management

- [supported][src:analog-bits-tsmc-n3p-n2p-2025] On-die power management IP on TSMC N3P/N2P includes low-dropout regulators (LDOs), power supply droop detectors (detecting <10 mV dips in <1 ns), and PVT (process-voltage-temperature) sensors. For AI accelerators drawing 500–1400W, these IP blocks enable fine-grained per-tile power gating and dynamic voltage/frequency scaling.
- [inference] The Cerebras WSE-3 co-design with Analog Bits demonstrates that wafer-scale power delivery requires distributed LDO networks and thousands of on-die droop detectors — a pattern that applies to any large multi-die AI accelerator. Per-die power management IP is the circuit-level enabler of chiplet disaggregation.

### The I/O Chiplet Architecture

- [supported][src:alphawave-alphachip1600-2025] The I/O chiplet pattern (AlphaCHIP1600-IO) separates SerDes PHYs, UCIe D2D, PCIe/CXL, and Ethernet MAC/PCS onto a dedicated die fabricated in a mature, low-leakage node (N7/N6), while compute dies use the most advanced logic node (N3/N2). This exploits the fact that analog SerDes circuits scale poorly beyond N5 — migrating SerDes from N3 to N7 saves ~30% area cost with no performance penalty.
- [inference] I/O chiplets also decouple the SerDes qualification timeline from the compute die tape-out: SerDes IP requires extensive characterization across voltage, temperature, and process corners, which can add 6–12 months to a monolithic tape-out. Pre-qualified I/O chiplets eliminate this from the critical path.

## Co-Packaged Optics and the Optical Future

- [supported][src:lightmatter-synopsys-cpo-2026] Co-packaged optics (CPO) integrates optical engines directly onto the AI accelerator package, bypassing the electrical SerDes bottleneck for off-package communication. Lightmatter's Passage™ platform with Synopsys 224G SerDes achieves 1.6 Tbps per fiber using 16-wavelength DWDM at 112G per lane.
- [inference] Optical D2D links would fundamentally change chiplet architecture: if inter-chiplet bandwidth is no longer constrained by bump pitch and substrate loss, much larger chiplet counts (16–64) become practical. However, laser power efficiency (~10–20%), thermal sensitivity, and packaging reliability remain open challenges for production CPO in 2026.

## Connection to Chiplet Architecture

- [supported][src:ucie-spec-2-0-2024] UCIe is the physical enabler of the chiplet thesis: without a standardized D2D PHY, every multi-die design is a custom integration project. UCIe provides the physical and protocol interoperability layer, analogous to what PCIe provided for board-level expansion in the 2000s.
- [inference] The SerDes energy cost per bit is the performance-price anchor for chiplet disaggregation. If D2D energy is 0.5 pJ/bit and HBM energy is 3 pJ/bit, moving data chiplet-to-chiplet is 6× cheaper than moving it to HBM. This creates a strong incentive to keep data on-package across chiplets rather than off-package in HBM — reinforcing the compute-near-memory and 3D stacking trends.

## Open Questions

- OPEN: Will 224G PAM4 SerDes in production (2026–2027) reach the <2 pJ/bit efficiency needed for cost-effective AI chiplet interconnects, or will the DSP power overhead keep it above 5 pJ/bit and push adoption to optical interconnects?
- OPEN: Can UCIe achieve true multi-vendor interoperability (an AMD compute chiplet talking to an Intel I/O chiplet), or will UCIe remain a "standard" that each vendor implements with proprietary extensions?
- OPEN: At what chiplet count does the package-level routing congestion (bump pitch, substrate layer count) make electrical D2D infeasible, forcing a transition to optical?
- VERIFY: The claimed 30% area savings from I/O chiplet node migration (compute at N3, I/O at N7) needs public validation. Current claims are vendor-provided and may not include the UCIe D2D bridge area overhead.

## See Also

- [[chip.circuit.digital-ip-blocks-ai-soc]] — Digital IP blocks (DMA, NoC, memory controllers) that consume the I/O bandwidth SerDes provides.
- [[system.scale.chiplet-architecture]] — Chiplet scale-up architecture that depends on D2D PHYs for inter-die communication.
- [[silicon.process.advanced-packaging-ai]] — Advanced packaging (CoWoS, EMIB) that provides the physical channel for UCIe PHYs.
- [[hw.riscv.power-thermal-interconnect]] — Power and thermal modeling for interconnects — SerDes power is a major contributor.
- [[silicon.process.node-selection-fabrication-ai]] — Process node selection for compute vs. I/O dies.
- [[hw.riscv.noc-interconnect-matrix-accelerators]] — On-die NoC interconnects — the on-die to off-die boundary where SerDes sits.
