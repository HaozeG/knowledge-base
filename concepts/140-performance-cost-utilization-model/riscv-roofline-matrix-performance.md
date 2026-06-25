---
id: model.riscv.roofline-matrix-performance
title: Roofline and Performance Modeling for RISC-V Matrix Accelerators
status: draft
layer: 140-performance-cost-utilization-model
layer_path: 140-performance-cost-utilization-model/riscv/roofline-matrix
parent: hw.riscv.multi-pe-matrix-microarchitecture
secondary_layers: [40-compute-substrate, 50-memory-data-movement, 110-workload-mapping]
granularity: model
concept_type: performance_model
scale_scope: [unit, tile, die]
reasoning_roles: [bottleneck, mapping]
tags: [riscv, roofline, performance-model, arithmetic-intensity, gemm, rvv, matrix, utilization, bottleneck]
aliases: [RISC-V matrix roofline, RVV performance modeling, RISC-V accelerator bottleneck analysis]
sources: [purayil-troop-ieee-iccd-2025, morgado-carm-arxiv-2026, wang-ara-cooptimization-arxiv-2026, sg2042-llm-inference-roofline-2025, ieee-outer-product-ci-2026, spacemit-k1-ime-roofline-2025]
---

# Roofline and Performance Modeling for RISC-V Matrix Accelerators

## First-Principle Explanation

A roofline model plots attainable performance (FLOP/s) against arithmetic intensity (FLOP/byte) for a given compute platform. The model reveals two hard ceilings:

```text
Compute roof:   peak FLOP/s of the hardware (determined by PE count × MAC/cycle × clock)
Bandwidth roof: peak FLOP/s = arithmetic_intensity × peak_bytes/s (determined by memory hierarchy)
Attainable:     min(compute_roof, arithmetic_intensity × bandwidth_roof)
```

The first-principle insight is that **every RISC-V matrix accelerator design point shifts these roofs differently**. A cluster of Spatz PEs (high bandwidth via shared L1, moderate compute) has a different roofline shape than a wide-pipeline Ventana Veyron V3 (high compute, memory-bound on most kernels) or a systolic Quadrilatero (high compute at low area, but rigid dataflow limits effective AI).

- [supported][src:purayil-troop-ieee-iccd-2025] TROOP micro-architectural optimizations on Spatz achieve at-the-roofline performance for memory-bound GEMV/DOTP/AXPY kernels: 1.5× speedup on GEMV, 2.2× on DOTP, 2.6× on AXPY, with 45% energy efficiency improvement and <7% area overhead in 12nm.
- [supported][src:sg2042-llm-inference-roofline-2025] On the SOPHON SG2042 (64-core RISC-V with RVV v0.7.1), enabling RVV in OpenBLAS speeds up LLM inference by up to 1.3×, but benefits are configuration-dependent — RVV can hurt GEMM in memory-bound regimes (low batch sizes) while helping in compute-bound regimes (high batch sizes), exactly as roofline theory predicts.
- [supported][src:morgado-carm-arxiv-2026] The CARM (Cache-Aware Roofline Model) tool now supports RISC-V with assembly microbenchmarks for all vector ISA extensions and memory hierarchy levels, achieving <1% deviation in constructed roofs.

## Roofline Shapes Across RISC-V Matrix Architectures

The roofline shape is a diagnostic fingerprint for each architecture class:

| Architecture | Compute Roof | Bandwidth Roof | Typical Bottleneck | Representative |
|---|---|---|---|---|
| **Compact vector cluster** (Spatz 2×4 FPU) | ~15.7 DP-GFLOPS (1 GHz, 12nm) | ~64 GB/s (128 KiB L1 scratchpad) | Memory-bound below ~0.25 AI | Spatz dual-PE |
| **Wide-pipeline CPU** (Ventana Veyron V3) | ~24 TFLOPS FP8/core | ~200-500 GB/s (L2/L3 cache) | Memory-bound for most LLM inference | Ventana Veyron V3 |
| **Systolic array** (Quadrilatero 4×4) | 3.2 GOPS FP32 (100 MHz) | ~3.2 GB/s (local buffer) | Balanced at tile size; rigid | Quadrilatero |
| **Multi-cluster NoC** (MAGIA 16×16) | ~65 TFLOPS FP16 (256 tiles) | ~200 GB/s per cluster edge | Inter-cluster bandwidth | MAGIA |

- [speculative][src:purayil-troop-ieee-iccd-2025] The TROOP optimizations specifically target the **bandwidth-limited region** of the roofline: decoupled load-store interfaces allow memory requests to proceed in parallel with compute, shadow buffers hide VRF bank conflicts, and address scrambling distributes accesses evenly across SRAM banks. These are all mechanisms for pushing the bandwidth roof higher without increasing raw SRAM bandwidth.
- [speculative][src:wang-ara-cooptimization-arxiv-2026] The Ara multi-lane vector processor's sustained-throughput gap (only 59.3% of peak for GEMM) is explained by roofline analysis: the memory-side data supply cannot keep up with the compute-side demand at the processor's arithmetic intensity operating point. The 1.33× geometric-mean speedup from co-optimization closes 12.2% of the gap.

## Measured vs. Ideal Arithmetic Intensity

- [supported][src:spacemit-k1-ime-roofline-2025] On the Spacemit K1 with IME (Intelligent Matrix Engine), measured arithmetic intensity is significantly lower than ideal because the vector register file size limits tile dimensions, forcing redundant load/store operations. A 16×16×16 GEMM kernel achieves only a fraction of the theoretical AI due to register spilling.
- [inference] This measured-vs-ideal AI gap is a general phenomenon for VLA architectures: the ideal AI assumes tile sizes can grow with VLEN, but register file capacity (32 vector registers × VLEN bits) imposes a hard limit. For VLEN=256 and SEW=32, the register file holds 256 elements total — a 16×16 tile consumes all 32 registers, leaving zero for software pipelining or double buffering.
- [speculative][src:ieee-outer-product-ci-2026] The outer-product model achieves 99.6% of the theoretical CI upper bound by organizing vector registers as a 2D grid, effectively using all register bits for matrix data rather than address computation or loop control. The remaining 0.4% gap comes from the need to reload one operand per outer-product step.

## Automated Roofline Tooling for RISC-V

- [supported][src:morgado-carm-arxiv-2026] CARM (Cache-Aware Roofline Model) provides the first automated roofline analysis for RISC-V. It generates assembly-level microbenchmarks for each cache level and vector ISA extension, constructs bandwidth and compute roofs from empirical measurements, and plots application performance points against the resulting model. The <1% deviation from hand-tuned benchmarks makes it a practical replacement for manual roofline construction.
- [inference] Before CARM, RISC-V developers had to manually construct roofline models using vendor datasheets (often unavailable for open-source designs) or hand-written microbenchmarks (error-prone, especially for multi-level caches). CARM's automation is particularly valuable for the fragmented RISC-V hardware landscape, where each implementation (Spacemit K1, SOPHON SG2042, BananaPi F3, Ventana Veyron) has different memory hierarchy parameters.

## Diagnostic Use of Roofline in Practice

- [supported][src:sg2042-llm-inference-roofline-2025] The SOPHON SG2042 study used roofline modeling as a diagnostic tool to explain why RVV acceleration of LLM inference is configuration-dependent: at low batch sizes, the GEMM arithmetic intensity falls in the memory-bound region (below the bandwidth roof), where RVV cannot help; at high batch sizes, AI crosses into the compute-bound region, where RVV's higher FLOP/s delivers the 1.3× speedup.
- [inference] This diagnostic pattern generalizes: for any new RISC-V matrix hardware, the roofline model predicts which kernels will benefit from matrix ISA extensions (those currently in the compute-bound region with RVV) and which will not (those already at the bandwidth roof).

## Open Questions

- OPEN: The CARM tool supports RVV but has not been extended to matrix extensions (AME/IME/VME). How will matrix ISA extensions change the roofline — do they raise the compute roof (more FLOP/s), change the bandwidth roof (tile load/store semantics), or both?
- OPEN: What is the "effective" arithmetic intensity of outer-product matrix operations when accounting for accumulator register pressure? The ideal analysis (99.6% of CI upper bound) assumes unlimited accumulator bandwidth, which may not hold for multi-PE implementations.
- OPEN: How does the roofline change for sparse matrix operations? The compute roof remains the same, but the bandwidth roof effectively shifts right (higher AI for the same data movement) when zeros are skipped — but sparse access patterns may introduce new bottlenecks (gather/scatter latency).
- VERIFY: TROOP's claimed 45% energy efficiency improvement was measured on a single Spatz PE cluster (2×4 FPU). Whether these gains scale to multi-cluster configurations (MemPool-Spatz with 256+ FPUs) is unverified.
- VERIFY: The CARM tool's RISC-V support has been validated against known x86 and ARM platforms for methodology correctness, but independent reproduction of the <1% deviation claim on RISC-V hardware is not yet published.
