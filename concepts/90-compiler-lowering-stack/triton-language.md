---
id: software.kernel.triton-language
title: Triton Language — Block-Level GPU Kernel Programming for AI
status: draft
layer: 90-compiler-lowering-stack
layer_path: 90-compiler-lowering-stack/kernel-languages/triton
parent: software.compiler.ml-compiler-lowering-riscv
secondary_layers: [80-programming-interface-dsl, 100-runtime-execution-system, 110-workload-mapping]
granularity: concept
concept_type: dsl
scale_scope: [unit, tile, die]
reasoning_roles: [enabler, abstraction, mapping]
tags: [triton, gpu-kernel, block-tiling, shared-memory, autotune, warp-specialization, flash-attention]
aliases: [Triton language, Triton GPU kernels, block-level GPU programming, Triton compiler]
sources: [triton-kernel-guide-2025, triton-autotune-warp-spec-2025, amd-triton-optimizations-2025, learnai-triton-tutorial-2025]
---

# Triton Language — Block-Level GPU Kernel Programming for AI

## Overview

Triton is an open-source programming language and compiler (developed by OpenAI, now under the Triton open-source community) for writing GPU kernels in Python. Unlike CUDA, which requires the programmer to reason about individual threads, warps, and shared memory banks, Triton operates at the block level — the programmer specifies tile sizes and data access patterns, and the Triton compiler handles thread mapping, shared memory allocation, memory coalescing, and synchronization automatically. Triton is the kernel generation backend for `torch.compile`, FlashAttention, and most production AI kernel optimization.

- [supported][src:triton-kernel-guide-2025] Triton's block-level abstraction replaces per-thread programming with per-tile programming: the kernel author defines operations on `[BLOCK_M, BLOCK_N]` tiles, and the compiler maps tiles to GPU thread blocks, threads within blocks, and SIMD lanes within threads. This eliminates three classes of CUDA bugs: thread indexing errors, shared memory bank conflicts, and warp divergence from manual warp-level logic.
- [inference] Triton's rise mirrors the shift from assembly to C in the 1980s: it provides a higher-level abstraction that captures ~90–95% of peak GPU performance while reducing kernel development time by 5–10× vs. equivalent CUDA. The remaining 5–10% (exotic warp-level tricks, register allocation micro-optimization) is accessible via Gluon, Triton's lower-level companion language.

## Block-Level Programming Model

### Tiles, Not Threads

- [supported][src:learnai-triton-tutorial-2025] A Triton kernel operates on multi-dimensional tiles defined by compile-time constants (`BLOCK_M`, `BLOCK_N`, `BLOCK_K`). Data is loaded from global memory (DRAM) into the tile, computed in registers, accumulated in shared memory, and written back. The compiler automatically: (1) maps the tile to a thread block; (2) distributes operations across warps using a vectorized execution model; (3) inserts synchronization barriers between tile loads/stores; (4) optimizes memory access patterns for coalescing.
- [inference] The block-level abstraction naturally matches GPU memory hierarchy: a tile's size determines how much data stays in shared memory vs. DRAM. Choosing `BLOCK_M=128, BLOCK_N=128, BLOCK_K=32` for a matrix multiply means 128×32 + 32×128 = 8,192 elements in shared memory at ~2 bytes each = 16 KB — well within the 228 KB shared memory budget, leaving room for double buffering. The same calculation in CUDA requires manual shared memory bank conflict avoidance, which Triton handles automatically.

### Autotuning

- [supported][src:triton-autotune-warp-spec-2025] The `@triton.autotune` decorator automates the search for optimal tile sizes, warp counts, and pipeline stages. The programmer provides a set of candidate configurations; Triton compiles and benchmarks each on the target hardware, caching the best configuration per input shape. This replaces the manual trial-and-error tuning that consumes days of CUDA kernel development.
- [inference] Autotuning is particularly valuable for cross-hardware deployment: the same Triton kernel can target NVIDIA (CUDA), AMD (ROCm/HIP), and future accelerators by simply re-running the autotuner. The optimal tile sizes differ per hardware — NVIDIA H100 prefers larger tiles (256×128) to saturate Tensor Cores, while AMD MI300X prefers smaller tiles (128×64) due to different matrix core granularity.

## Key Performance Techniques

### Fused Kernels

- [inference] Triton's primary performance advantage over eager PyTorch is kernel fusion: a single Triton kernel can implement an entire fused softmax (max reduction → exp → sum reduction → normalize) or fused LayerNorm (mean → variance → normalize → affine). Each fused kernel eliminates 3–5 intermediate tensor writes/reads, reducing global memory traffic by 60–80%. PyTorch eager mode materializes each intermediate tensor; `torch.compile` + Triton fuses them into a single kernel pass.

### Warp Specialization

- [supported][src:triton-autotune-warp-spec-2025] Automatic warp specialization (added 2025) partitions a kernel into producer and consumer warp groups: producer warps asynchronously load data from global memory into shared memory buffers; consumer warps compute on previously loaded data. This software-pipelines data movement and computation, overlapping them rather than sequentializing them. Warp specialization achieves ~20–30% throughput improvement on memory-bound kernels (attention, convolution) at the cost of increased shared memory usage for double/triple buffering.

### FlashAttention in Triton

- [inference] FlashAttention is the canonical Triton success story: the original FlashAttention paper implemented the algorithm in CUDA (~500 lines); the Triton reimplementation is ~100 lines and achieves 95% of the CUDA performance. The key insight: Triton's block-level programming model is a natural fit for the tiled attention algorithm (load Q, K, V tiles into shared memory → compute local attention → accumulate). The CUDA implementation spends half its code on shared memory management that Triton handles automatically.

## Cross-Platform Portability

- [supported][src:amd-triton-optimizations-2025] AMD has invested heavily in Triton for ROCm: the Triton compiler now generates optimized HIP kernels for AMD GPUs (MI300X, MI355X), with automatic mapping to AMD matrix cores (MFMA, WMMA instructions). AMD-specific optimizations include stream pipelining (global loads → shared memory → matrix cores), block ping-pong (interleaving two warps for better occupancy), and LDS (Local Data Share) usage minimization.
- [inference] Triton's cross-platform portability is strategically significant for the non-NVIDIA AI accelerator ecosystem. RISC-V AI accelerators, AMD GPUs, and custom ASICs can all be targeted by Triton if someone writes a Triton backend for them. This makes Triton a de facto standard for compute kernel portability, analogous to what LLVM provides for CPU code — write once, autotune per target.

## Open Questions

- OPEN: Can Triton's block-level abstraction capture every optimization that hand-coded CUDA can, or will there always be a performance gap requiring CUTLASS/CUB-level manual control?
- OPEN: As Triton becomes the default kernel language for `torch.compile`, does the CUDA programming model (and NVIDIA's CUDA moat) become less relevant, or does NVIDIA's hardware-specific Triton backend (CUTLASS-based) maintain an advantage?
- VERIFY: The claim that Triton achieves 95% of hand-optimized CUDA performance is based on matmul and attention benchmarks — performance on irregular kernels (sparse operations, sorting) may differ significantly.

## See Also

- [[software.compiler.ml-compiler-lowering-riscv]] — ML compiler lowering where Triton serves as the kernel generation backend.
- [[software.compiler.ml-compiler-lowering-riscv]] — ML compiler lowering where TorchInductor generates Triton kernels for GPU execution.
- [[workload.ai.rvv-kernel-patterns]] — Kernel patterns (GEMM, attention) that Triton implements at the block level.
- [[hw.compute.numerical-precision-ai]] — Numerical precision (FP8, FP4) supported by Triton's Tensor Core codegen.
- [[software.riscv.ai-software-ecosystem]] — RISC-V AI software ecosystem where Triton could provide kernel portability.
