---
id: hw.riscv.dataflow-execution-model
title: Dataflow Execution Models for RISC-V Multi-PE AI Accelerators
status: draft
layer: 70-execution-architecture
layer_path: 70-execution-architecture/riscv/dataflow-execution-models
parent: hw.riscv.multi-pe-matrix-microarchitecture
secondary_layers: [90-compiler-lowering-stack, 100-runtime-execution-system]
granularity: concept
concept_type: execution_model
scale_scope: [tile, die]
reasoning_roles: [enabler, mapping, bottleneck]
tags: [dataflow, spatial-architecture, cgra, systolic-array, execution-model, riscv-pe]
aliases: [dataflow execution RISC-V, spatial architecture, CGRA, systolic dataflow]
sources: [dataflow-spatial-architecture-2025]
---

# Dataflow Execution Models for RISC-V Multi-PE AI Accelerators

## Overview

When a chip has hundreds or thousands of processing elements (PEs), the challenge shifts from "how fast can each PE compute" to "how efficiently can data flow between PEs." The dataflow execution model determines the spatial and temporal pattern of data movement across the PE array — and this choice fundamentally constrains what workloads the accelerator can execute efficiently. RISC-V-based multi-PE designs are experimenting with multiple dataflow paradigms, each optimized for different workload classes.

- [inference] Three canonical dataflow models compete in RISC-V multi-PE designs: (1) systolic dataflow — data flows rhythmically through the array in a fixed spatial-temporal pattern, optimal for dense matrix multiply but rigid for irregular computations; (2) dataflow-triggered execution — PEs fire when their input operands arrive, enabling dynamic scheduling at the cost of handshake overhead; (3) SIMD/vector dataflow — a central controller broadcasts instructions to all PEs with predicated execution masks, optimal for regular data-parallel workloads but wastes PEs on divergent execution.
- [inference] The dataflow model choice is the central architectural decision for multi-PE accelerators: it determines the compiler's ability to map diverse workloads, the hardware's area efficiency (systolic eliminates instruction fetch per PE), and the system's tolerance for irregularity (dataflow-triggered handles sparsity naturally; SIMD does not). RISC-V's openness enables hybrid approaches that mix dataflow models across different PE clusters — a flexibility that proprietary architectures rarely expose.

## Dataflow Models Compared

| Model | Scheduling | Area Efficiency | Irregular Workloads | Example |
|---|---|---|---|---|
| Systolic | Static, compile-time | Highest (no I-fetch) | Worst (rigid pattern) | Google TPU, Quadrilatero |
| Dataflow-triggered | Dynamic, data-arrival | Medium (handshake logic) | Best (natural sparsity) | CAMP, Spatial architectures |
| SIMD/Vector | Central controller | Medium (shared I-fetch) | Poor (divergence waste) | RVV with chaining |
| Systolic+SIMD hybrid | Static + predication | Good | Moderate | Spatz, MemPool |

## Compiler Co-Design

- [inference] The dataflow model and the compiler are co-designed: a systolic array requires the compiler to tile and schedule operations into a fixed temporal pattern (the "systolic schedule"); a dataflow-triggered array requires the compiler to map the computation graph to PEs such that token-passing between PEs matches the dataflow graph edges. The compiler's optimization target shifts from "minimize instructions" (von Neumann) to "minimize data movement" (dataflow).
- [inference] RISC-V's MLIR-based compilation flow (IREE, TVM) represents dataflow mapping as a dialect-level optimization: the `linalg` dialect describes the computation pattern, the `affine` dialect specifies the loop nest, and the dataflow dialect maps the affine schedule to spatial PE coordinates. This multi-level IR approach is necessary because no single level captures both the computation semantics and the spatial constraints.

## Open Questions

- OPEN: Can a hybrid dataflow architecture that switches between systolic, dataflow-triggered, and SIMD modes per-layer match the efficiency of architectures optimized for a single dataflow model, or does the flexibility overhead negate the benefit?
- VERIFY: The energy cost of dataflow-triggered handshake logic (token buffers, ready/valid signals) vs. systolic register-to-register transfer has been estimated in simulation but not measured in fabricated RISC-V multi-PE chips.

## See Also

- [[hw.riscv.multi-pe-matrix-microarchitecture]] — Multi-PE microarchitecture that dataflow execution models organize.
- [[hw.riscv.execution-architecture]] — RISC-V execution architecture that dataflow models extend.
- [[software.compiler.ml-compiler-lowering-riscv]] — ML compiler lowering where dataflow mapping is a dialect-level optimization.
- [[workload.ai.rvv-kernel-patterns]] — Kernel patterns that dataflow models optimize for.
- [[hw.riscv.noc-interconnect-matrix-accelerators]] — NoC interconnects that implement dataflow movement between PEs.
- [[hw.riscv.vector-memory-hierarchy]] — Memory hierarchy that dataflow-triggered execution depends on for operand delivery.
