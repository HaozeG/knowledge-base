---
id: hw.gpu.tensor-core-mma-programming
title: GPU Tensor Core MMA Programming and Instruction-Level Optimization
status: draft
layer: 70-execution-architecture
layer_path: 70-execution-architecture/gpu/tensor-core-mma-programming
parent: hw.gpu.overview
secondary_layers: [40-compute-substrate, 90-compiler-lowering-stack, 110-workload-mapping]
granularity: concept
concept_type: execution_model
scale_scope: [unit, tile, die]
reasoning_roles: [enabler, mapping, bottleneck]
tags: [tensor-core, mma, wgmma, warp-group, matrix-multiply, instruction-scheduling]
aliases: [MMA instruction, Tensor Core programming, WGMMA, warp-group MMA, CUDA Tensor Core]
sources: [nvidia-mma-cuda-programming-2025, nvidia-wgmma-hopper-2025]
---

# GPU Tensor Core MMA Programming and Instruction-Level Optimization

## Overview

Tensor Cores are specialized matrix multiply-accumulate units in NVIDIA GPUs, accessed through MMA (matrix multiply-accumulate) instructions at the PTX/SASS level or through the `mma.sync` API in CUDA. Programming Tensor Cores directly — rather than relying on library implementations (cuBLAS, CUTLASS) — is necessary for achieving peak throughput on custom operations that library APIs cannot express. The MMA programming model has evolved from synchronous warp-level operations (Volta–Ampere) to asynchronous warp-group operations (Hopper's WGMMA), each generation giving the programmer more control over data movement and pipeline overlap.

- [supported][src:nvidia-mma-cuda-programming-2025] CUDA's `mma.sync` API provides warp-level matrix multiply-accumulate in a single PTX instruction: `mma.sync.aligned.m16n8k16.row.col.f32.f16.f16.f32` performs a 16×8×16 matrix multiply (FP16 inputs, FP32 accumulation) across all 32 threads in a warp, with each thread contributing a specific fragment of the input and output matrices. The programmer is responsible for loading data into registers in the exact layout the MMA instruction expects — incorrect register layouts cause silent correctness errors.
- [supported][src:nvidia-wgmma-hopper-2025] Hopper's WGMMA (Warp Group MMA) extends the MMA model: a warp group of 128 threads (4 warps) collaboratively executes a larger matrix multiply (64×N×16 or larger). WGMMA is asynchronous — the instruction fires and the warp scheduler continues executing other instructions while TMA feeds data to the Tensor Core and writes results. Synchronization is explicit via `wgmma.wait_group` barriers, enabling deep software pipelining of data movement and computation.
- [inference] The evolution from synchronous warp MMA to asynchronous warp-group WGMMA mirrors the broader GPU trend toward decoupled data movement and computation. MMA requires the programmer to orchestrate both data movement and computation in lockstep; WGMMA separates them, allowing the programmer to issue all data movement first, then all computation, overlapping them automatically. This is the same pattern as CUDA graphs vs. individual kernel launches, applied at the instruction level.

## MMA Instruction Architecture

### Warp-Level MMA (Volta–Ampere)

- [inference] The basic MMA instruction operates on a warp (32 threads), each holding a fragment of the A, B, and C matrices in its registers. The fragment layout is determined by the matrix dimensions and data types: for FP16 m16n8k16, thread i holds A[i%4][i/4] (4×8 fragment), B[i%8][i/8] (8×4 fragment), and C[i%4][i/4] (4×8 accumulator). The MMA instruction computes C += A × B in a single cycle across all 32 threads, with each thread's fragment contributing to the overall result.
- [inference] The register pressure from MMA is significant: a single m16n8k16 FP16 MMA requires 8 registers per thread for A, B, and C fragments (24 registers total). A warp-level kernel with multiple MMA operations per thread can easily consume 128+ registers, limiting occupancy to 25–50%. The programmer must balance tile size (larger is more efficient per MMA) against register pressure (larger reduces occupancy).

### Warp-Group MMA (Hopper WGMMA)

- [inference] WGMMA extends the warp-group concept: 4 warps (128 threads) form a warp group that executes MMA operations collectively. The WGMMA instruction `wgmma.mma_async.sync.aligned.m64n128k16.f32.f16.f16` performs a 64×128×16 matrix multiply across the warp group. WGMMA is asynchronous — the warp scheduler issues the instruction and immediately continues, allowing other independent instructions from the same warp group to execute while the Tensor Core processes the MMA.
- [inference] WGMMA's key innovation is the separation of data staging (shared memory → registers → Tensor Core) from computation scheduling. The programmer uses `tcgen05` instructions to move data from shared memory to the Tensor Core's internal accumulator (TMEM on Blackwell), then fires WGMMA to compute on the staged data. This two-level pipeline (stage from SMEM, compute from TMEM) enables near-100% Tensor Core utilization for large matrix multiplies.

## Performance Considerations

- [inference] The critical performance factors for MMA programming: (1) register layout conformance — MMA instructions require exact register layouts; a single misplaced element produces silent wrong results; (2) bank conflict avoidance — the operand collector reads 3 source operands per instruction from the register file; bank conflicts serialize reads and can double instruction latency; (3) tile size selection — larger tiles amortize MMA instruction overhead but increase register pressure, reducing occupancy.
- [inference] For AI inference with FP8 precision on Hopper: the optimal MMA configuration is typically m16n16k32 (FP8→FP32 accumulation), achieving 2× throughput vs. FP16. Blackwell's FP4 MMA (m32n32k64) doubles throughput again. The tile size scales inversely with precision: as bit width halves, the optimal tile doubles, maintaining roughly constant register pressure and occupancy.

## Open Questions

- OPEN: Will future GPU architectures expose the Tensor Core's internal microarchitecture (accumulator pipeline, forwarding paths) at the instruction level, or will WGMMA remain the lowest-level abstraction available to programmers?
- OPEN: As WGMMA becomes asynchronous, does the GPU effectively become a dataflow architecture at the instruction level — tiles flow from shared memory through Tensor Cores to output registers, with the programmer specifying data movement graphs rather than instruction streams?
- VERIFY: The claim that FP8 optimal tile size is m16n16k32 is based on NVIDIA's CUTLASS research — optimal tile sizes for Blackwell FP4 are preliminary.

## See Also

- [[hw.gpu.overview]] — GPU architecture overview where Tensor Core MMA instructions execute.
- [[hw.gpu.tensor-cores]] — Tensor Core architecture that MMA instructions target.
- [[hw.gpu.warp-scheduler-simt]] — Warp scheduler that dispatches MMA and WGMMA instructions.
- [[hw.compute.numerical-precision-ai]] — Numerical precision that determines MMA throughput per instruction.
- [[software.kernel.triton-language]] — Triton language where tl.dot() maps to MMA instructions.
- [[workload.ai.rvv-kernel-patterns]] — Kernel patterns that MMA programming implements at the instruction level.
