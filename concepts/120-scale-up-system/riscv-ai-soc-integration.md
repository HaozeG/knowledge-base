---
id: hw.riscv.ai-soc-integration-reference
title: RISC-V AI SoC Integration — Reference Designs from Esperanto, Ventana, and Tenstorrent
status: draft
layer: 120-scale-up-system
layer_path: 120-scale-up-system/riscv/ai-soc-integration-reference
parent: hw.riscv.vector-extension
secondary_layers: [40-compute-substrate, 50-memory-data-movement, 130-scale-out-distributed-system]
granularity: case-study
concept_type: case_study
scale_scope: [die, package, node]
reasoning_roles: [indicator, enabler]
tags: [riscv-soc, esperanto, ventana, tenstorrent, ai-accelerator, soc-integration]
aliases: [RISC-V AI SoC, Esperanto ET-SoC, Ventana Veyron, Tenstorrent Blackhole, AI chip integration]
sources: [esperanto-et-soc-2025, ventana-veyron-2025, tenstorrent-blackhole-2025]
---

# RISC-V AI SoC Integration — Esperanto, Ventana, and Tenstorrent Reference Designs

## Overview

Three RISC-V-based AI accelerator designs illustrate the spectrum of RISC-V SoC integration strategies: Esperanto's ET-SoC (1,088 RISC-V cores with vector units on a single die, targeting inference), Ventana's Veyron V3 (high-performance OoO RISC-V cores with custom matrix extensions, targeting cloud AI), and Tenstorrent's Blackhole (RISC-V processor cores managing a spatial array of matrix compute units, targeting both training and inference). Each represents a different bet on how RISC-V cores should integrate with AI acceleration hardware.

- [inference] Esperanto's ET-SoC represents the "many small cores" strategy: 1,088 ET-Minion 64-bit RISC-V cores, each with a custom RVV-like vector unit (VLEN=256), interconnected via a mesh NoC. The design targets inference efficiency through massive parallelism — each small core handles one part of the computation with minimal control overhead. Total power: ~120W at 1 GHz; peak throughput: ~200 TOPS (INT8).
- [inference] Ventana's Veyron V3 represents the "few large cores" strategy: high-performance OoO RISC-V cores (8-wide decode, 512-entry ROB) with custom matrix extensions for AI acceleration. The design targets both general-purpose compute and AI acceleration in a single core, avoiding the host/accelerator split. This is the "AI-extended CPU" approach — the matrix extensions are ISA-level additions to a general-purpose core.
- [inference] Tenstorrent's Blackhole represents the "spatial array with RISC-V control" strategy: an array of Tensix cores (each containing 5 RISC-V processor cores + a matrix compute engine + local SRAM) interconnected via a 2D mesh NoC. The RISC-V cores manage data movement, operand delivery, and synchronization; the matrix engines handle computation. This is a spatial dataflow architecture with RISC-V as the control fabric.

## Design Comparison

| Aspect | Esperanto ET-SoC | Ventana Veyron V3 | Tenstorrent Blackhole |
|---|---|---|---|
| RISC-V cores | 1,088 (in-order) | 8–16 (OoO, 8-wide) | ~700 (5 per Tensix × 140 Tensix) |
| Vector/Matrix | Custom RVV (VLEN=256) | Custom matrix ext (Ventana MX) | Dedicated matrix engine |
| Interconnect | Mesh NoC | Coherent ring | 2D mesh NoC |
| Memory | LPDDR5 + on-chip SRAM | DDR5 + HBM (optional) | GDDR6 + local SRAM per Tensix |
| Target | Inference (edge/datacenter) | Cloud AI + general compute | Training + inference |
| Power | ~120W | ~200–350W | ~300W |

## Open Questions

- OPEN: Will RISC-V AI SoC designs converge toward a standard template (e.g., RISC-V control cores + RVV compute array + mesh NoC), or will the diversity of architectural approaches persist, reflecting the openness of the RISC-V ecosystem?
- OPEN: Can the "many small cores" approach (Esperanto) compete with the GPU SIMT model for LLM inference, or is the granularity mismatch — thousands of tiny cores vs. 132 large SMs — fundamentally disadvantageous for the large-matrix operations that dominate transformer inference?
- VERIFY: Esperanto's 200 TOPS (INT8) at 120W is vendor-claimed — independent benchmark validation against MLPerf is not yet available.

## See Also

- [[hw.riscv.vector-extension]] — RVV 1.0 ISA that Esperanto's ET-Minion cores implement.
- [[hw.riscv.execution-architecture]] — Execution architecture spectrum (in-order → OoO → spatial) that these designs span.
- [[hw.riscv.multi-pe-matrix-microarchitecture]] — Multi-PE microarchitecture that Tenstorrent's Tensix cores instantiate.
- [[system.riscv.distributed-ai-clusters]] — Distributed RISC-V clusters built from these SoCs.
- [[industry.riscv.ai-supply-chain]] — Supply chain dynamics affecting RISC-V AI SoC availability.
- [[system.scale.chiplet-architecture]] — Chiplet architecture that Ventana's chiplet-based approach leverages.
