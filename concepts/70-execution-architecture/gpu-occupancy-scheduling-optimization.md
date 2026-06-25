---
id: hw.gpu.occupancy-and-scheduling-optimization
title: GPU Occupancy Modeling and Thread Block Scheduling Optimization
status: draft
layer: 70-execution-architecture
layer_path: 70-execution-architecture/gpu/occupancy-scheduling-optimization
parent: hw.gpu.overview
secondary_layers: [90-compiler-lowering-stack, 100-runtime-execution-system, 110-workload-mapping]
granularity: concept
concept_type: performance_model
scale_scope: [tile, die]
reasoning_roles: [bottleneck, mapping, locality_strategy]
tags: [occupancy, thread-block, sm-scheduling, register-pressure, shared-memory, warp-allocation]
aliases: [GPU occupancy, thread block scheduling, SM occupancy modeling, warp allocation optimization]
sources: [nvidia-occupancy-calculator-2025, nvidia-cuda-occupancy-api-2025]
---

# GPU Occupancy Modeling and Thread Block Scheduling Optimization

## Overview

Occupancy is the ratio of active warps to the maximum warps an SM can support — it determines how effectively the GPU hides memory and execution latency through warp-level parallelism. Occupancy is constrained by three per-SM resources: register file capacity (256 KB per SM), shared memory capacity (~228 KB per SM), and the maximum thread block and warp count per SM. The occupancy equation determines whether a kernel is latency-bound (low occupancy, insufficient warps to hide stalls) or throughput-bound (high occupancy, warps saturate execution pipelines).

- [supported][src:nvidia-occupancy-calculator-2025] NVIDIA's Occupancy Calculator (CUDA Toolkit) models the interaction of registers per thread, shared memory per block, and thread block size to predict achieved occupancy. For an A100 SM: max 2,048 threads (64 warps), max 32 thread blocks, 65,536 registers (256 KB), and 164 KB shared memory (configurable). The limiting resource determines the maximum concurrent thread blocks: occupancy = min(warps_from_threads, warps_from_registers, warps_from_shared_memory) / 64.
- [inference] The occupancy-performance relationship is not monotonic: a kernel with 50% occupancy and high instruction-level parallelism (ILP) can outperform one with 100% occupancy and low ILP because each warp provides more independent instructions to hide latency. The optimal occupancy is where occupancy × ILP is maximized. This requires the compiler (register allocation, loop unrolling) and the runtime (thread block size selection) to co-optimize.

## The Occupancy Equation

### Resource Constraints

- [inference] For a kernel using R registers per thread, S bytes of shared memory per thread block, and T threads per block:
  - Thread constraint: warp_count_threads = T / 32 × ceil(2048 / T) / 64  (blocks_per_SM × warps_per_block)
  - Register constraint: blocks_registers = floor(65536 / (T × R)), warp_count_reg = blocks_registers × T / 32 / 64
  - Shared memory constraint: blocks_shared = floor(164000 / S), warp_count_shm = blocks_shared × T / 32 / 64
  - Occupancy = min(warp_count_threads, warp_count_reg, warp_count_shm) / 64, clamped to [0, 1]
- [inference] The register constraint is typically binding for compute-bound kernels: a GEMM kernel using 128 registers per thread with 256 threads per block → blocks_reg = 65536/(256×128) = 2 blocks per SM → 2×256/32 = 16 warps → 25% occupancy. Reducing registers to 64 raises occupancy to 50% but may increase instruction count (register spilling). The compiler's register allocation pass makes this trade-off; the `__launch_bounds__` directive lets the programmer influence it.

### Impact on AI Workloads

- [inference] AI kernels fall into three occupancy regimes: (1) matrix multiply (GEMM, convolution) — register-bound at high tile sizes, typically 25–50% occupancy but high ILP from loop unrolling; (2) element-wise and normalization (ReLU, LayerNorm, Softmax) — memory-bound at all occupancy levels, benefit most from fusion to amortize memory access; (3) attention (FlashAttention) — shared-memory-bound by the block size needed for tiled attention, typically 50–75% occupancy. The kernel designer chooses tile sizes to balance register pressure and shared memory usage, guided by the Occupancy Calculator.

## Thread Block Scheduling

- [supported][src:nvidia-cuda-occupancy-api-2025] The CUDA Occupancy API (`cudaOccupancyMaxPotentialBlockSize`) automates the thread block size selection: given the kernel's register and shared memory usage, it returns the block size that maximizes occupancy. The API also provides `cudaOccupancyMaxActiveBlocksPerMultiprocessor` for runtime occupancy queries.
- [inference] Thread block scheduling across SMs is managed by the GigaThread Engine (NVIDIA's hardware block scheduler): as SMs become available (thread blocks complete), new blocks are dispatched from the grid. The dispatch granularity is one thread block per SM. For a grid with 1,000 blocks and 108 SMs (A100), approximately 9–10 waves of blocks are needed, with each wave taking the time of the slowest block. Occupancy determines how many blocks execute concurrently per SM, which determines the number of waves — higher occupancy means fewer, larger waves; lower occupancy means more, smaller waves.

## Open Questions

- OPEN: As GPU memories shift from fixed-allocation (register file, shared memory) to more flexible VMM-based allocation (TMEM, expandable segments), does the traditional occupancy model need to be reformulated for elastic resources?
- OPEN: Can ML-guided occupancy optimization (trained on kernel performance data) outperform the analytical Occupancy Calculator by capturing non-linear interactions between ILP, memory latency, and occupancy?
- VERIFY: The claim that 50% occupancy + high ILP can outperform 100% occupancy is based on established CUDA optimization guidance; counterexamples exist for memory-bound kernels where occupancy dominates ILP.

## See Also

- [[hw.gpu.overview]] — GPU architecture overview where SM configuration and occupancy constraints originate.
- [[hw.gpu.warp-scheduler-simt]] — Warp scheduler where occupancy determines the pool of schedulable warps.
- [[hw.gpu.on-chip-memory-hierarchy]] — On-chip memory hierarchy where register and shared memory constraints are physical.
- [[hw.gpu.thread-blocks-occupancy]] — Thread blocks and occupancy model overview.
- [[software.compiler.power-aware-compilation]] — Compiler optimizations where register allocation decisions affect occupancy.
- [[workload.ai.rvv-kernel-patterns]] — Kernel patterns where occupancy optimization determines tile sizes and launch configurations.
