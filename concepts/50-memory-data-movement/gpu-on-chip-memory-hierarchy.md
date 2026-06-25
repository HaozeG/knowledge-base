---
id: hw.gpu.on-chip-memory-hierarchy
title: GPU On-Chip Memory Hierarchy — Registers, Shared Memory, L1/L2 Cache, and TMEM
status: draft
layer: 50-memory-data-movement
layer_path: 50-memory-data-movement/gpu/on-chip-memory-hierarchy
parent: hw.gpu.memory-hierarchy
secondary_layers: [40-compute-substrate, 70-execution-architecture, 110-workload-mapping]
granularity: concept
concept_type: memory_pattern
scale_scope: [unit, tile, die]
reasoning_roles: [bottleneck, enabler, locality_strategy]
tags: [register-file, shared-memory, L1-cache, L2-cache, tmem, bandwidth, latency, gpu-memory-hierarchy]
aliases: [GPU SM memory, on-chip GPU cache, register file GPU, shared memory SM, GPU L1 L2]
sources: [blackwell-memory-architecture-2025, b200-tmem-microarchitecture-2025, gpu-memory-hierarchy-zeroentropy-2025, bentoml-gpu-architecture-2025]
---

# GPU On-Chip Memory Hierarchy — Registers, Shared Memory, L1/L2, and TMEM

## Overview

The GPU on-chip memory hierarchy is a multi-level cache and scratchpad system designed to feed data to thousands of ALUs with minimal latency. Unlike CPUs, which rely primarily on hardware-managed caches, GPUs expose a mix of hardware-managed caches (L1, L2) and software-managed scratchpads (shared memory, registers) that give the programmer and compiler explicit control over data placement. The evolution from H100 to B200 marks a structural shift: dedicated tensor memory (TMEM) and a much larger L2 cache reconfigure the hierarchy for AI workloads.

- [supported][src:blackwell-memory-architecture-2025] The H100 memory hierarchy: 256 KB registers + 256 KB SRAM (configurable L1/shared memory) per SM, 50 MB L2 cache, 80 GB HBM3 at 3.35 TB/s. The B200 reconfigures this: 256 KB registers + 128 KB L1/shared memory (default) + 256 KB TMEM per SM, ~126 MB L2 cache (dual-die partitioned), 192 GB HBM3e at 8 TB/s. The L1/shared memory reduction is compensated by TMEM and a 2.5× larger L2.
- [supported][src:b200-tmem-microarchitecture-2025] TMEM (Tensor Memory) is a dedicated 256 KB per-SM on-chip memory used exclusively by Tensor Core operations. It provides 16 TB/s read + 8 TB/s write bandwidth per SM — additive to L1/shared memory bandwidth — and reduces Tensor Core data access latency by 58% vs. H100's global memory path. TMEM is accessed via new `tcgen05` instructions that move data between shared memory and TMEM.
- [inference] The TMEM innovation reflects a structural insight: AI training and inference spend 70–90% of compute time in matmul operations. A dedicated memory tier for Tensor Cores eliminates L1 cache contention between matmul data and element-wise operation data, creating two independent memory pipelines that don't interfere. This is the memory hierarchy equivalent of having separate instruction and data caches.

## Memory Tier Characteristics

| Tier | H100 per SM | B200 per SM | Latency | Scope | Managed By |
|---|---|---|---|---|---|
| Register File | 256 KB | 256 KB | ~1 cycle | Per-thread | Compiler |
| L1/Shared Memory | 256 KB (max 228K SMEM) | 128 KB (default) | ~20–30 cycles | Per-SM | HW (L1) + Programmer (SMEM) |
| TMEM | — | 256 KB | ~20 cycles | Per-SM, Tensor Core only | Programmer (tcgen05) |
| L2 Cache | 50 MB (chip-wide) | ~126 MB (63 MB × 2 dies) | ~200 cycles | Chip-wide | Hardware |
| HBM | 80 GB, 3.35 TB/s | 192 GB, 8 TB/s | ~400+ cycles | Global | Programmer + Driver |

### Register File

- [inference] The register file is the fastest and most constrained memory tier. At 256 KB per SM with 64 warps and 255 registers per thread max, the register file holds 64 × 32 × 255 = 522,240 bytes = 510 KB — exceeding the physical 256 KB means registers spill to L1 cache (or worse, to L2/HBM). Register spilling is the single largest performance hazard for complex kernels.
- [inference] Each register read costs 0 cycles (absorbed in the operand collection stage), but register bank conflicts serialize reads. With 64 banks of 32 bits each, a warp that uniformly accesses 32 different registers in 32 different banks completes in 1 cycle. A warp where all 32 threads want register R%64 (same bank) serializes to 32 cycles — a 32× slowdown per instruction.

### Shared Memory and L1 Cache

- [supported][src:gpu-memory-hierarchy-zeroentropy-2025] Shared memory (programmer-managed scratchpad) and L1 cache (hardware-managed) share the same physical SRAM, configurable between different splits per kernel launch. Shared memory is the primary mechanism for collaborative data reuse within a thread block: all threads in a block can access the same shared memory allocation, enabling tiled matrix multiply and convolution where each thread contributes a tile to shared memory, then all threads read from the shared tile.
- [inference] Shared memory has 32 banks (each 4 bytes wide on modern GPUs). Bank conflicts follow the pattern: if threads T and T+16 access addresses differing by 32 × 4 = 128 bytes, they hit the same bank and serialize. The classic optimization: pad shared memory arrays by 1 element to shift bank mappings and avoid conflicts. Compilers (nvcc) automatically pad in some cases; explicit padding via `__align__` is needed for others.

### L2 Cache

- [supported][src:bentoml-gpu-architecture-2025] The L2 cache is chip-wide and hardware-managed, serving as the last on-chip coherence point before HBM. B200's 126 MB L2 (63 MB per die) is partitioned across two dies connected via 10 TB/s NV-HBI. Cross-die L2 access adds ~50–100 ns latency — a NUMA-like penalty that kernel schedulers and the L2 replacement policy must account for.
- [inference] L2 capacity has grown 2.5× from H100 → B200 because AI model sizes have outpaced HBM capacity growth. A larger L2 captures more of the working set that would otherwise evict to HBM, reducing both HBM bandwidth pressure and average memory latency. For a Llama-3-70B model (~140 GB BF16), H100's 50 MB L2 captures ~0.036% of parameters; B200's 126 MB captures ~0.09% — still small, but the 2.5× improvement helps disproportionately because hot weights and KV-cache entries have heavy-tailed access distributions.

### TMEM and the Tensor Memory Pipeline

- [supported][src:b200-tmem-microarchitecture-2025] TMEM introduces a split memory pipeline for tensor operations. Non-tensor instructions continue using the L1/shared memory → register path. Tensor Core MMA instructions use shared memory → TMEM → Tensor Core direct path. This eliminates the L1/L2 contention bottleneck that was the primary performance limiter for mixed tensor+scalar workloads on H100.
- [inference] The programming model: data flows from HBM → L2 → shared memory → TMEM → Tensor Cores. The programmer uses `tcgen05` instructions to explicitly stage data from shared memory to TMEM, overlapping this data movement with Tensor Core computation on previously staged data — a software-pipelined producer-consumer pattern. This gives the programmer fine-grained control over data movement that a hardware prefetcher cannot reliably provide.

## Impact on AI Workloads

- [inference] For a typical Transformer forward pass: attention weights (QK^T) are compute-bound at small sequence lengths and memory-bound at large sequence lengths. The TMEM + larger L2 in B200 shifts the crossover point: with 16 TB/s TMEM bandwidth feeding Tensor Cores, attention stays compute-bound for longer sequences. For a 2,048-token sequence, H100 is memory-bound (QK^T is bandwidth-limited by L1 bandwidth); B200 remains compute-bound (TMEM feeds Tensor Cores faster than they consume).
- [inference] The register file pressure from FP4/FP8 precision: lower precision increases per-warp throughput, which increases register demand (more operations in flight). B200 maintains the same 256 KB register file as H100 — a conscious design choice that pairs well with the larger L2 and TMEM, since the compiler can aggressively spill less-frequently-used registers to L1 (which now has less contention from tensor data thanks to TMEM).

## Open Questions

- OPEN: At what point does the TMEM model (separate tensor memory pipeline) generalize to non-tensor operations? Could future architectures provide domain-specific memory tiers for other operation classes (reduction, scatter/gather, sorting)?
- OPEN: The dual-die L2 NUMA penalty (~50–100 ns) is small relative to total L2 latency (~200 ns), but does it accumulate to a measurable performance penalty for multi-tenant serving where different tenants' data lands on different dies?
- VERIFY: TMEM bandwidth of 16 TB/s read + 8 TB/s write per SM is from NVIDIA's architecture whitepaper — independent benchmarks via microbenchmarking are not yet available for B200.

## See Also

- [[hw.gpu.memory-hierarchy]] — GPU memory hierarchy overview that this concept decomposes from.
- [[hw.gpu.tensor-cores]] — Tensor Cores that consume data from TMEM and shared memory.
- [[hw.gpu.warp-scheduler-simt]] — Warp schedulers that manage register file access and operand collection.
- [[hw.gpu.tensor-memory-accelerator]] — TMA (Tensor Memory Accelerator) for asynchronous data movement across memory tiers.
- [[hw.riscv.vector-memory-hierarchy]] — RISC-V vector memory hierarchy for comparison with GPU on-chip memory.
- [[hw.compute.numerical-precision-ai]] — Numerical precision affects register pressure and memory bandwidth demand.
