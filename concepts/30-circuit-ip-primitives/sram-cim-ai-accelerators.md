---
id: chip.circuit.sram-cim-ai-accelerators
title: On-Chip SRAM and Compute-in-Memory for AI Accelerators
status: draft
layer: 30-circuit-ip-primitives
layer_path: 30-circuit-ip-primitives/sram-cim/ai-accelerators
parent: hw.riscv.multi-pe-matrix-microarchitecture
secondary_layers: [40-compute-substrate, 50-memory-data-movement]
granularity: mechanism
concept_type: component
scale_scope: [unit, tile]
reasoning_roles: [enabler, bottleneck]
tags: [sram, compute-in-memory, cim, memory-compiler, ai-accelerator, circuit-design, bitcell, low-power]
aliases: [SRAM for AI accelerators, compute-in-memory, AI memory circuits, on-chip SRAM scaling]
sources: [m31-ull-memory-compiler-tsmc-n6e-2025, dream-cim-ieee-tcasai-2025, accelcim-dataflow-arxiv-2026, lpae-cim-approximate-adder-2025, fermi-ml-sram-macro-arxiv-2025, nature-cfet-6t-sram-2026, microelectronics-pim-imc-survey-2026, dmatrix-3d-dram-2026, dac-photonic-sram-2025]
---

# On-Chip SRAM and Compute-in-Memory for AI Accelerators

## First-Principle Explanation

Every AI accelerator — whether a GPU tensor core, a RISC-V matrix PE, or a TPU systolic array — is built on SRAM. The fundamental circuit-level constraint is:

```text
AI throughput ∝ (MAC_operations / second)
MAC_operations / second = min(compute_throughput, memory_bandwidth / bits_per_operation)
memory_bandwidth = SRAM_capacity × access_rate / area
```

SRAM determines both the **memory bandwidth roof** (how fast operands reach the MAC units) and the **area/power floor** (SRAM can occupy 50-70% of an AI accelerator's die area). Improving SRAM density and energy directly improves AI accelerator efficiency.

The first-principle challenge: conventional 6T-SRAM cell-area scaling has **stalled since the 3 nm node** due to quantum effects, routing congestion, and parasitic RC delay. This creates a density wall — logic transistors continue scaling, but SRAM doesn't, making on-chip memory an increasingly dominant fraction of accelerator die area.

- [supported][src:microelectronics-pim-imc-survey-2026] In a comprehensive 2019–2025 survey, SRAM CIM achieves peaks of 600 TOPS/W and 1.5 TOPS/mm², but ADC/DAC peripherals consume 50–95% of total energy and converter chains can be 10–12× larger than the compute array.
- [supported][src:nature-cfet-6t-sram-2026] A 3-Tier CFET 6T-SRAM using 2D-TMD channels achieves 29.5% area reduction over 2-Tier CFET, >39% lower write energy, and 24.9% EDP improvement — a potential path through the SRAM density wall at Angstrom nodes.

## SRAM Density Wall and Novel Bitcells

The slowdown in SRAM cell-area scaling is the most critical circuit-level constraint for AI accelerators:

- [supported][src:nature-cfet-6t-sram-2026] Industry has observed unprecedented slowdown in SRAM cell-area scaling since the 3 nm node. Physical limits (quantum confinement, parasitic RC, routing congestion) prevent proportional scaling with logic transistors. CFET architectures stack nFET and pFET vertically, recovering area without requiring lithography improvements.
- [speculative][src:nature-cfet-6t-sram-2026] If 3-Tier CFET SRAM achieves 29.5% area reduction at angstrom nodes, a large AI accelerator with 200 mm² of SRAM could reduce to ~140 mm², freeing 60 mm² for additional compute logic. At ~1 TOPS/mm² for logic, this translates to ~60 additional TOPS from the same die.

## Compute-in-Memory (CIM): Eliminating the Von Neumann Bottleneck at the Circuit Level

CIM embeds multiply-accumulate operations directly within the SRAM array, eliminating the energy and latency cost of moving data from memory to compute units. This is the circuit-level instantiation of the data-movement principles discussed in the memory hierarchy (layer 50) and NoC (layer 60) concepts.

- [supported][src:dream-cim-ieee-tcasai-2025] DREAM-CIM uses 8T SRAM cells for "free" bitwise NAND-based multiplication during read, achieving 5097 TOPS/W and 3854 TOPS/mm² at 22nm (normalized to 1-bit MAC). Per-inference energy: 0.1 mJ (MNIST), 0.2 mJ (YOLOv6), 11.0 mJ (CIFAR-10).
- [supported][src:fermi-ml-sram-macro-arxiv-2025] FERMI-ML uses a novel 9T XNOR-based bitcell (5T storage + 4T compute), achieving 1.93 TOPS throughput and 364 TOPS/W at 350 MHz in 65nm with Posit-4 or FP-4 precision.
- [speculative][src:dream-cim-ieee-tcasai-2025] The key CIM insight is that SRAM read operations already perform analog computation (bitline voltage is a weighted sum of cell currents). By making this computation intentional rather than parasitic, CIM eliminates the ADC/DAC bottleneck that plagues analog CIM — DREAM-CIM's digital approach replaces ADCs with simple sense amplifiers.

## The ADC/DAC Bottleneck

- [supported][src:microelectronics-pim-imc-survey-2026] The ADC/DAC overhead is the dominant energy and area cost in analog CIM: converters consume 50–95% of total energy and can be 10–12× larger than the compute array. This is why purely digital CIM approaches (DREAM-CIM, LPAE CIM) are gaining traction — they avoid ADCs entirely by using digital sense amplifiers.
- [supported][src:lpae-cim-approximate-adder-2025] LPAE CIM replaces full adders with OR gates in the adder tree, achieving 148.5 TOPS/W at 4-bit precision with dynamically adjustable 1–8 bit input activation and reconfigurable 4/8 bit weight storage.

## Memory Compilers for AI Accelerators

- [supported][src:m31-ull-memory-compiler-tsmc-n6e-2025] M31's Ultra-Low Leakage memory compilers on TSMC N6e offer One Port Register Files, ELL (Extreme Low Leakage) compilers with 50% power reduction in deep sleep, and Low-VDD compilers operating down to 0.5V. These are the commercial IP building blocks that AI accelerator designers instantiate for on-chip scratchpads and register files.
- [inference] The availability of production memory compilers on advanced nodes (TSMC N6e) is a prerequisite for competitive AI accelerator design — without them, every team must design custom SRAM macros, adding 6–12 months to tapeout schedules.

## System-Level Integration: From Macro to Accelerator

- [supported][src:accelcim-dataflow-arxiv-2026] AccelCIM addresses the gap between CIM macro-level efficiency (often reported at 500+ TOPS/W) and system-level performance (often <100 TOPS/W after integration losses). The framework systematically explores macro configurations and macro-array organizations, validated with cycle-accurate simulation and post-layout PPA analysis.
- [speculative][src:accelcim-dataflow-arxiv-2026] The primary system-level loss mechanisms are: (1) data marshaling between CIM macros and non-CIM logic, (2) under-utilization when DNN layer dimensions don't match macro dimensions, and (3) peripheral circuit power that scales with macro count.
- [supported][src:dmatrix-3d-dram-2026] At the chiplet scale, d-Matrix scaled SRAM to 2 GB per card, but die-to-die interconnect becomes the new bottleneck: bandwidth per mm of edge, latency per hop, and energy per bit. Their 3D stacked DRAM (Pavehawk) targets 20 TB/s per stack (10× HBM4) at 0.3–0.4 pJ/bit vs. 3–4 pJ/bit for HBM4.

## Emerging: Photonic SRAM

- [speculative][src:dac-photonic-sram-2025] Differential photonic SRAM (pSRAM) uses optical readout to overcome rising bitline/wordline capacitance in scaled electrical SRAM, achieving 4.10 TOPS and 3.02 TOPS/W in 45 nm photonic CMOS. This is early-stage research but addresses a fundamental scaling limit: as wires shrink, their RC delay increases, making electrical SRAM access increasingly expensive.

## Open Questions

- OPEN: Will 3-Tier CFET SRAM enter production in time (2028–2030) to prevent the SRAM density wall from limiting AI accelerator scaling, or will alternative approaches (3D-stacked DRAM, photonic SRAM, MRAM) become necessary?
- OPEN: Can digital CIM approaches (DREAM-CIM, LPAE CIM) scale to the precision requirements of training (FP16/BF16) or will they remain inference-only? Analog CIM's precision limitations are well-documented.
- OPEN: What is the optimal CIM macro size for transformer workloads? Small macros (4 KB) offer flexibility but high peripheral overhead; large macros (64 KB+) offer density but poor utilization on irregular attention patterns.
- VERIFY: M31's 50% deep-sleep power reduction and 0.5V operation are vendor claims; independent validation in a full accelerator tapeout has not been published.
- VERIFY: The 600 TOPS/W peak for SRAM CIM (survey) includes idealized simulation results; silicon-validated efficiencies are typically 30–50% lower.
