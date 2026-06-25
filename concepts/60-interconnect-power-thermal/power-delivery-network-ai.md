---
id: system.power.ai-accelerator-power-delivery
title: Power Delivery Networks for AI Accelerators — PDN, IR Drop, and Voltage Regulation
status: draft
layer: 60-interconnect-power-thermal
layer_path: 60-interconnect-power-thermal/power-delivery/pdn-ir-drop-voltage-regulation
parent: hw.riscv.power-thermal-interconnect
secondary_layers: [20-manufacturing-process-integration, 30-circuit-ip-primitives, 120-scale-up-system]
granularity: concept
concept_type: architecture_pattern
scale_scope: [die, package, node]
reasoning_roles: [constraint, bottleneck, enabler]
tags: [power-delivery, pdn, ir-drop, voltage-regulation, decoupling-capacitor, chiplet-power, vpd]
aliases: [PDN design, IR drop management, power delivery network, AI accelerator power, on-die VRM]
sources: [saras-stile-package-passive-2025, ieee-chiplet-pdn-rl-2025, ai-accelerator-pdn-nextpcb-2025]
---

# Power Delivery Networks for AI Accelerators — PDN, IR Drop, and Voltage Regulation

## Overview

AI accelerators consume 1,000–1,400W at sub-1V voltages, drawing over 2,000A of current. Delivering this power from the board-level voltage regulator to billions of on-die transistors, across multiple chips in a multi-die package, with less than 3% voltage droop, is the power delivery network (PDN) design problem. The PDN is a distributed RLC network spanning the voltage regulator module (VRM), PCB planes, package substrate, interposer, and on-die metal layers. Every impedance in this chain contributes to IR drop and transient voltage noise that can cause timing errors and functional failures.

- [supported][src:ai-accelerator-pdn-nextpcb-2025] Modern AI accelerators (H100, B200, MI300X) require >1,000A at 0.6–0.85V core voltage. Target PDN impedance has shrunk to <100 µΩ — a 20 mV IR drop on an 0.8V rail represents 2.5% voltage loss, sufficient to trigger setup/hold timing violations in high-frequency logic. The PDN must maintain this impedance from DC to >100 MHz, spanning six orders of magnitude in frequency.
- [supported][src:saras-stile-package-passive-2025] Traditional decoupling uses multi-layer ceramic capacitors (MLCCs) on the PCB, but parasitic inductance in the package-to-board connection limits their effectiveness above ~10–50 MHz. Saras Micro Devices' STILE technology embeds capacitors and inductors directly in the package substrate, reducing the PDN loop inductance by 10–30× and enabling effective decoupling up to the on-die capacitance resonance (~100–500 MHz).
- [inference] The PDN is the physical manifestation of the power wall: as transistor density increases (more gates switching) and voltage decreases (narrower noise margins), the current per unit area increases while the tolerable voltage droop decreases. This is an unsustainable trajectory — at 2nm and below, further voltage scaling may be limited not by transistor physics but by the impossibility of delivering clean power across the chip.

## PDN Architecture

### The Multi-Tier Impedance Challenge

- [inference] A PDN has four impedance tiers, each dominating at a different frequency range:
  - **VRM (DC–100 kHz)**: Voltage regulator module on the PCB; low bandwidth, high current capacity. Regulates to within ~10 mV of target voltage.
  - **Bulk capacitance (100 kHz–1 MHz)**: Large electrolytic/tantalum capacitors on the PCB; smooth VRM switching noise and provide charge for millisecond-scale current transients.
  - **Mid-frequency MLCCs (1–50 MHz)**: Ceramic capacitors on the PCB near the package; handle microsecond-scale transients from workload phase changes.
  - **High-frequency/on-package (50–500 MHz+)**: On-package capacitors (STILE, embedded silicon caps) and on-die decoupling; handle nanosecond-scale switching noise from simultaneous gate switching.
- [inference] The impedance of each tier must be below the target impedance Z_target = ΔV_allowed / ΔI_transient at its frequency range. With ΔV_allowed = 24 mV (3% of 0.8V) and ΔI_transient = 200A (typical for a 1,000W GPU under workload transition), Z_target = 120 µΩ across the entire frequency range. Achieving this requires the impedance contributions of all four tiers to anti-resonate constructively, not create impedance peaks where the PDN is effectively open-circuit.

### Vertical Power Delivery (VPD)

- [inference] VPD is the emerging solution for >1,000W accelerators: instead of delivering power laterally through the package substrate from perimeter VRMs, VPD delivers power vertically through the back of the package or directly through the PCB under the die. This reduces the current path length from centimeters to millimeters, cutting PDN loop inductance proportionally. NVIDIA's GB200 and future Rubin designs are expected to use VPD, following the pattern set by Intel's Foveros Direct and TSMC's InFO-PoP.
- [inference] The trade-off: VPD requires through-silicon vias (TSVs) through the die or package, which consume area and add manufacturing complexity. It also requires the backside of the die to be accessible for power connections — incompatible with traditional flip-chip packaging where the backside is used for heat dissipation. This forces a choice: cool from the front, power from the back, or use microfluidic cooling channels within the die itself.

### Chiplet PDN Co-Design

- [supported][src:ieee-chiplet-pdn-rl-2025] Multi-chiplet AI accelerators create a PDN co-design problem: each chiplet has its own power requirements, but the interposer and package PDN is shared. Simultaneous switching current (SSC) from multiple chiplets creates resonant noise at frequencies determined by the interposer RLC and the decoupling capacitor placement. Deep reinforcement learning approaches are emerging for optimal decap placement across chiplets, exploring trillion-configuration design spaces.
- [inference] Chiplet disaggregation — beneficial for manufacturing yield and process node mixing — makes the PDN problem harder because each chiplet boundary adds package-level interconnect impedance. The same UCIe D2D links that provide high-bandwidth data communication create high-frequency current transients that the PDN must absorb. The chiplet PDN design is fundamentally a multi-objective optimization: minimize total impedance while minimizing decap area cost, subject to per-chiplet voltage droop constraints.

## Open Questions

- OPEN: Can vertical power delivery scale to 3,600W+ (Vera Rubin Ultra) without requiring fundamentally new power semiconductor materials (GaN, SiC) at the package level, or does the current density exceed what silicon interposers can support?
- OPEN: Will AI workloads drive PDN design toward software-defined, workload-coupled architectures where the PDN adapts its impedance profile to the expected current transient profile, or is the latency of VRM adaptation too slow for microsecond-scale transients?
- VERIFY: The claim that STILE achieves 10–30× loop inductance reduction is vendor-provided; independent third-party PDN measurements on production AI accelerator packages are not publicly available.

## See Also

- [[hw.riscv.power-thermal-interconnect]] — Power and thermal modeling that the PDN design feeds into.
- [[system.scale.chiplet-architecture]] — Chiplet architecture where multi-die PDN co-design is critical.
- [[silicon.process.advanced-packaging-ai]] — Advanced packaging technologies (TSV, interposer) that enable vertical power delivery.
- [[chip.circuit.serdes-io-phy-ai-chiplets]] — SerDes I/O where simultaneous switching noise stresses the PDN.
- [[silicon.process.node-selection-fabrication-ai]] — Process node selection where voltage scaling and PDN impedance constraints interact.
- [[model.ai-datacenter-tco]] — TCO model where power delivery efficiency affects OpEx through electricity costs.
