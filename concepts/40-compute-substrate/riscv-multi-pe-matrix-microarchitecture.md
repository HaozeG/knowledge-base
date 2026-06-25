---
id: hw.riscv.multi-pe-matrix-microarchitecture
title: Multi-PE Matrix Microarchitecture for RISC-V
status: draft
layer: 40-compute-substrate
layer_path: 40-compute-substrate/riscv/multi-pe-matrix
parent: hw.riscv.matrix-extension-proposals
secondary_layers: [50-memory-data-movement, 70-execution-architecture, 110-workload-mapping]
granularity: mechanism
concept_type: architecture_pattern
scale_scope: [unit, tile, die]
reasoning_roles: [enabler, bottleneck, mapping]
tags: [riscv, matrix, multi-pe, microarchitecture, systolic-array, outer-product, spatial-architecture, pe-array, gemm, ai-acceleration]
aliases: [RISC-V matrix PE organization, matrix spatial microarchitecture, RVV PE clustering]
sources: [perotti-spatz-ieee-tcad-2025, nojehdeh-camp-micro-2025, cammarata-quadrilatero-acm-2025, saumell-mte-bsc-2025, venieri-ame-pim-acm-cf-2026, ieee-outer-product-ci-2026, cai-taurus-2025, shen-mempool-spatz-date-2025, ieee-area-optimized-matrix-edge-2025, sinigaglia-maestro-arxiv-2025]
---

# Multi-PE Matrix Microarchitecture for RISC-V

## First-Principle Explanation

Matrix multiplication on silicon is fundamentally a dataflow orchestration problem. A GEMM operation C[M×N] += A[M×K] × B[K×N] performs O(MKN) MAC operations on O(MK+KN+MN) elements. The compute-to-data ratio grows with dimension size, but only if the microarchitecture can keep processing elements fed. The first-principle constraint is:

```text
PE throughput ∝ (PE count × MAC/cycle/PE) × utilization
utilization   ∝ min(data supply rate / data consumption rate, 1)
data supply   ∝ (memory bandwidth, register file ports, interconnect topology)
```

When you scale from one PE to many, the organizer faces a trilemma:
- **Few large PEs** (wide vector units, high LMUL): high per-PE throughput but poor scaling — each PE needs many register file ports and wide memory interfaces
- **Many small PEs** (compact vector units, narrow MACs): better area scaling but higher inter-PE communication overhead and synchronization cost
- **Systolic array PEs**: eliminate register file port scaling entirely by connecting PEs directly, but impose rigid dataflow that hurts utilization on non-GEMM kernels

The art of multi-PE matrix microarchitecture is choosing the PE granularity, interconnect topology, and memory hierarchy that keeps the most PEs busy for the target workload mix.

- [supported][src:perotti-spatz-ieee-tcad-2025] A 2-KiB latch-based VRF enables compact vector PEs that can be efficiently clustered — Spatz achieves 7.7 FMA/cycle across 8 FPUs in a dual-core cluster at 1 GHz in 12nm, with 96.6% FPU utilization on matrix multiply.
- [supported][src:nojehdeh-camp-micro-2025] CAMP (Cartesian Accumulative Matrix Pipeline) adds intra-lane and inter-lane accumulators to a standard vector pipeline, achieving 17× speedup on ARM A64FX and 23× on RISC-V edge SoC with only 1–4% area overhead.
- [supported][src:ieee-outer-product-ci-2026] The outer-product computation model can achieve 99.6% of the theoretical computational intensity upper bound using existing RISC-V vector registers organized as a 2D grid, without dedicated matrix register files.

## Multi-PE Organization Spectrum

RISC-V matrix implementations span a spectrum from tightly-coupled vector PE clusters to fully specialized systolic arrays:

| Organization | PE Granularity | Per-PE State | Interconnect | Peak Utilization | Flexibility | Area Cost |
|---|---|---|---|---|---|---|
| **Clustered Vector PEs** (Spatz) | 4-FPU per PE, 2 PEs/cluster | 2 KiB VRF per PE | Shared L1 scratchpad (crossbar) | 96.6% on matmul, 95% on 2D conv | High (full RVV programmability) | Moderate (VRF + FPU dominates) |
| **Vector + Accumulator Ext.** (CAMP) | Standard vector lanes + accumulator registers | Vector regs + accumulator SRAM | Intra-lane + inter-lane accumulator network | >90% on quantized GEMM | High (reuses vector pipeline) | Low (1–4% area overhead) |
| **Matrix Coprocessor** (Quadrilatero) | 4×4 MAC grid (16 PEs) | 8×128b matrix regs | Weight-stationary systolic array | 99.4% on MatMul | Moderate (matrix ISA only) | 0.65 mm² in 65nm |
| **In-Core Systolic** (MTE) | Variable tile, systolic PE chain | Tile registers in-core | Diagonal-injection systolic | ~89% (3.5× over RVV) | Low (matrix tile ops only) | 2.31% area increase |
| **Wide-Pipeline Matrix** (Ventana Veyron V3) | 16 execution pipes, 5 vector/matrix | Matrix register file per core | Macro-op fusion, multi-issue | ~24 TFLOPS/core FP8 | High (full CPU + matrix) | Large (datacenter-class die) |
| **PIM Outer-Product** (AME-PIM) | HBM-PIM pseudo-channels | In-memory accumulators | HBM channel array | 59.4 FLOP/cycle | Low (AME ISA subset) | Zero (reuses HBM logic) |

- [speculative][src:perotti-spatz-ieee-tcad-2025] Spatz's 2-KiB VRF is the key enabler of multi-PE clustering — a "big" VRF (hundreds of KiB) would make per-PE area prohibitive for clustering. The latch-based SCM VRF occupies minimal area while providing sufficient operand bandwidth for 4 FPUs.
- [speculative][src:nojehdeh-camp-micro-2025] CAMP reduces functional unit stall rate from 80% to <10% by adding hierarchical accumulators that decouple the multiply pipeline from the accumulate pipeline, allowing the multipliers to stay busy while accumulations complete asynchronously.
- [speculative][src:cammarata-quadrilatero-acm-2025] Quadrilatero's 4×4 weight-stationary systolic array achieves 99.4% FPU utilization because the weight-stationary dataflow eliminates repeated weight loads — each weight is loaded once and reused across all output activations in its row.

## Clustered Vector PE Pattern (Spatz)

The clustered vector PE pattern is the most general and programmable approach. Each PE is a self-contained RVV vector processor, and multiple PEs share a local scratchpad memory.

- [supported][src:perotti-spatz-ieee-tcad-2025] The Spatz cluster contains two Snitch-Spatz core complexes, each with 4 trans-precision FPUs (fp8/fp16/fp32/fp64) and a 2-KiB VRF, sharing a 128-KiB L1 scratchpad (16 SRAM banks).
- [supported][src:shen-mempool-spatz-date-2025] MemPool-Spatz scales the clustered pattern to 1024 FPUs using TCDM burst access, achieving 3.26× bandwidth improvement over baseline shared-L1 clusters on memory-bound kernels.
- [speculative][src:perotti-spatz-ieee-tcad-2025] The key architectural insight: by keeping the VRF small (2 KiB), the vector unit itself stays compact, enabling multiple instances to share one L1 memory without interconnect congestion. A large VRF (e.g., 128 KiB) would dominate area and make multi-PE clustering uneconomical.

The limitation of clustered vector PEs is that each PE operates independently on its own tile of the matrix. Inter-PE synchronization for reduction operations (e.g., partial sum accumulation across PEs) requires explicit shared-memory communication through the scratchpad, adding latency and reducing utilization on small matrix dimensions.

## Outer-Product Accumulator Pattern (CAMP / VME-style)

Rather than clustering independent PEs, the outer-product accumulator pattern extends the vector pipeline itself with dedicated accumulator registers and inter-lane reduction networks.

- [supported][src:nojehdeh-camp-micro-2025] CAMP introduces a hybrid multiplier design that supports 4-bit and 8-bit multiplications within the same datapath, with intra-lane accumulators for partial products and inter-lane accumulators for cross-lane reduction.
- [speculative][src:nojehdeh-camp-micro-2025] The CAMP accumulator hierarchy is two-level: intra-lane accumulators sum partial products within a single vector lane (low latency, no cross-lane wiring), while inter-lane accumulators handle cross-lane reductions required by the outer product (higher latency, routed through a reduction tree).
- [speculative][src:ieee-outer-product-ci-2026] The outer-product model's computational intensity advantage comes from its data reuse pattern: loading two N-element vectors feeds N² multiply-accumulate operations, giving O(N) reuse. At 2048-bit VLEN with SEW=8, this is 256× reuse in a single instruction.

This pattern is architecturally aligned with VME's outer-product approach and IME's outer-product variant. It adds moderate state (accumulator registers) but avoids the full cost of a dedicated matrix register file.

## Systolic Array Pattern (Quadrilatero / MTE / Taurus)

The systolic array pattern eliminates the register file bottleneck entirely. PEs are arranged in a 2D grid with nearest-neighbor connections; data flows through the array rhythmically, and each PE performs one MAC per cycle.

- [supported][src:cammarata-quadrilatero-acm-2025] Quadrilatero's 4×4 systolic array uses weight-stationary dataflow: weights are pre-loaded into PEs, input activations flow left-to-right, and partial sums flow top-to-bottom. At 100 MHz in 65nm, it consumes 34 mW while achieving 99.4% FPU utilization on fp32 MatMul.
- [supported][src:saumell-mte-bsc-2025] MTE integrates a systolic array directly into the Sargantana in-order RISC-V core, using diagonal injection dataflow (inspired by the Axon architecture) to feed the array. It achieves 3.5× speedup over RVV with only 2.31% area increase.
- [speculative][src:saumell-mte-bsc-2025] Diagonal injection addresses the systolic array startup problem: instead of feeding PEs from one corner (which leaves corner PEs idle during fill/drain phases), diagonal injection feeds all diagonals simultaneously, reducing fill/drain overhead by O(array_dimension).
- [speculative][src:cammarata-quadrilatero-acm-2025] The weight-stationary dataflow choice is critical for edge AI: weights are loaded once per tile and reused across many input activations, minimizing energy spent on data movement. This is optimal for inference where weights are constant.

The primary limitation of systolic arrays is inflexibility: they are highly efficient for dense GEMM but poorly utilize PEs for element-wise operations, reductions, or irregular access patterns. Systems like Quadrilatero address this by pairing the systolic array with a scalar/vector core for non-GEMM operations.

## Wide-Pipeline Matrix Pattern (Ventana Veyron V3)

The wide-pipeline matrix pattern takes the opposite approach from compact PE clustering: build very wide execution pipelines with dedicated matrix registers and use macro-op fusion to sustain high issue rates.

- [speculative] Ventana Veyron V3 deploys 16 execution pipelines per core with 5 dedicated vector/matrix pipes, achieving 24 TFLOPS/core at FP8. A 192-core chiplet scales to 4.5 PFLOPS. This represents the datacenter-class extreme of the multi-PE spectrum.
- [speculative] Macro-op fusion combines multiple RVV/matrix instructions into single internal operations, reducing frontend pressure and allowing the wide backend to stay fed without requiring impossibly wide instruction fetch.

This pattern is architecturally closest to AME with dedicated tile registers, targeting maximum single-thread matrix throughput rather than multi-PE spatial scaling. It competes directly with ARM SME in the datacenter CPU market.

## PIM Outer-Product Pattern (AME-PIM)

The PIM outer-product pattern moves matrix compute into the memory itself, using HBM-PIM processing elements near the memory banks.

- [supported][src:venieri-ame-pim-acm-cf-2026] AME-PIM maps the RISC-V AME ISA onto Samsung Aquabolt-XL HBM-PIM using a reduction-free outer-product dataflow. It achieves 14.9 GFLOP/s (59.4 FLOP/cycle) on a single HBM pseudo-channel for 128×4096 tiles.
- [speculative][src:venieri-ame-pim-acm-cf-2026] The reduction-free dataflow resolves a fundamental tension: HBM-PIM banks lack native cross-bank reduction hardware. By decomposing the outer product into a sequence of matrix-vector operations where each step accumulates within a single column, it avoids cross-bank reductions entirely.

## Scalability Comparison

- [inference] Across the five patterns, three scaling regimes emerge:
  1. **Linear PE scaling** (clustered vector, wide-pipeline): throughput scales with PE count until memory bandwidth saturates. MemPool-Spatz demonstrates linear scaling to 1024 FPUs with burst access.
  2. **Quadratic PE scaling** (systolic array): throughput scales with array area (N² PEs for an N×N array), but utilization depends on matrix dimensions matching the array size.
  3. **Memory-proportional scaling** (PIM): throughput scales with HBM channel count; each channel operates independently without inter-channel communication overhead.
- [speculative][src:shen-mempool-spatz-date-2025] The TCDM burst access mechanism in MemPool-Spatz is the critical enabler for scaling beyond ~100 PEs: without burst access, the shared L1 scratchpad becomes the bottleneck, limiting utilization on memory-bound kernels to well below 50%.

## Open Questions

- OPEN: What is the optimal PE granularity for a given technology node and target workload mix? Spatz (4 FPU/PE, 2 KiB VRF) demonstrates efficient clustering at 12nm, but the trade-space (2 FPU/PE? 8 FPU/PE?) is not systematically characterized.
- OPEN: Can a single multi-PE organization efficiently handle both dense GEMM (systolic array sweet spot) and sparse/irregular attention patterns? The Quadrilatero approach (systolic array + scalar core) is one answer, but end-to-end utilization data for mixed workloads is missing.
- OPEN: How do the three ISA proposals (AME/IME/VME) map to the five microarchitectural patterns? Which ISA features are required, recommended, or irrelevant for each pattern?
- OPEN: Does CAMP's hierarchical accumulator network scale beyond 512-bit vector lengths without introducing timing closure issues at high clock frequencies?
- OPEN: The MemPool-Spatz 1024-FPU configuration has not been fabricated — what are the real (not simulated) power, thermal, and yield implications of a monolithic 1024-FPU die?
- VERIFY: No published head-to-head comparison exists of the same matrix workload implemented on Spatz (clustered vector PEs), Quadrilatero (systolic array), and CAMP (accumulator-extended vector) at iso-technology and iso-area.
- VERIFY: Ventana Veyron V3 performance claims (24 TFLOPS/core) are from vendor marketing materials, not independent benchmarking.
