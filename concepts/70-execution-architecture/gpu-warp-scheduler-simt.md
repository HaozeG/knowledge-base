---
id: hw.gpu.warp-scheduler-simt
title: GPU Warp Scheduler, SIMT Execution, and Operand Delivery
status: draft
layer: 70-execution-architecture
layer_path: 70-execution-architecture/gpu/warp-scheduler-simt-execution
parent: hw.gpu.simt
secondary_layers: [40-compute-substrate, 90-compiler-lowering-stack, 100-runtime-execution-system]
granularity: concept
concept_type: execution_model
scale_scope: [unit, tile, die]
reasoning_roles: [enabler, bottleneck, mapping, locality_strategy]
tags: [warp-scheduler, simt, scoreboard, register-file, bank-conflict, ilp, occupancy, tensor-core]
aliases: [NVIDIA warp scheduler, SIMT execution model, GPU warp execution, scoreboard scheduling]
sources: [nvidia-cuda-programming-guide-2025, gpu-microarchitecture-warp-scheduler-2025, gpgpu-sim-execution-model-2025, zhihu-warp-scheduler-design-2025]
---

# GPU Warp Scheduler, SIMT Execution, and Operand Delivery

## Overview

The GPU warp scheduler is the hardware unit that decides which warps (groups of 32 threads) execute instructions on which cycles. It is the microarchitectural heart of the SIMT (Single Instruction, Multiple Thread) execution model: it manages the illusion that thousands of threads execute independently while physically issuing instructions from a small number of warps through a shared set of execution units.

- [supported][src:nvidia-cuda-programming-guide-2025] An NVIDIA SM (Streaming Multiprocessor) contains 4 warp schedulers (GA100+), each capable of issuing one instruction per cycle to one of the execution pipelines (FP32, INT32, Tensor Core, LSU, or SFU). With independent instruction issue per scheduler, an SM can dispatch up to 4 instructions per cycle across its 4 schedulers. A warp that stalls on a memory load is replaced by a ready warp in the same cycle — this zero-cycle context switch is the fundamental latency-hiding mechanism of GPUs.
- [supported][src:gpu-microarchitecture-warp-scheduler-2025] Modern warp schedulers use GTO (Greedy Then Oldest) or LRR (Loose Round Robin) scheduling policies. GTO keeps dispatching from the same warp until it stalls, then switches to the oldest ready warp. GTO typically yields better performance because draining a warp frees its register file and shared memory allocation sooner, allowing new thread blocks to be scheduled.
- [inference] The warp scheduler's throughput is constrained by three bottlenecks: scoreboard stalls (register dependencies not yet resolved), dispatch stalls (operand collector cannot gather source operands fast enough from the register file), and issue stalls (no ready warp has an instruction the target pipeline can execute).

## SIMT Execution Model

### Warps, Threads, and Lockstep

- [inference] A warp of 32 threads executes in lockstep: all threads share a single program counter and execute the same instruction each cycle. Threads that diverge (take different branch paths) are serialized via a SIMT stack that tracks which threads are active on which branch path. Pre-Volta GPUs used a simple reconvergence stack; Volta+ introduced independent thread scheduling where each thread has its own PC, allowing finer-grained interleaving of divergent paths at the cost of more complex warp scheduler state.
- [inference] The 32-thread warp size is a design parameter that balances several constraints: larger warps amortize instruction fetch and decode energy across more ALUs but increase register file port pressure and reduce effective occupancy for divergent workloads. AMD GPUs use 64-thread wavefronts; the trade-off is the same but with different optimal points.

### Latency Hiding Through Warp-Level Parallelism

- [inference] The fundamental latency-hiding equation: L_hide = N_warps × I_per_warp × T_issue, where L_hide is the latency being hidden (e.g., 400 cycles for global memory), N_warps is the number of ready warps, I_per_warp is the average number of independent instructions per warp, and T_issue is the issue rate. To hide a 400-cycle memory latency with 4 ready warps, each warp must sustain 100 independent instructions between memory accesses — achievable for compute-bound kernels, impossible for memory-bound ones.
- [inference] This is why occupancy (number of resident warps per SM) is not the sole performance metric: a kernel with 4 warps at high ILP may outperform one with 16 warps at low ILP. The effective latency-hiding capacity is occupancy × ILP. Compiler optimizations (loop unrolling, instruction scheduling) increase ILP; runtime decisions (thread block size) control occupancy. The optimal point is where the product is maximized within register file and shared memory constraints.

## Scoreboard and Register File

### Scoreboard Operation

- [supported][src:zhihu-warp-scheduler-design-2025] The scoreboard tracks per-warp register readiness: for each warp, a bitmask with one bit per architectural register. When an instruction writes register R_dst, bit R_dst is set to 1 (busy). Subsequent instructions check their source registers against the scoreboard and stall if any source bit is 1. When the writing instruction completes (typically 4–8 cycles for FP32, 8–16 for Tensor Core MMA), the bit is cleared. The scoreboard is a fully associative lookup per warp with single-cycle latency — its area and power scale with the number of warps and registers per SM.
- [inference] Scoreboard pressure is the dominant occupancy limiter for math-heavy kernels: each additional warp requires 32× (register count per thread) scoreboard bits plus the physical register file entries. At 255 registers per thread × 64 warps per SM (A100), the register file holds 64K registers of 32 bits = 256 KB, and the scoreboard tracks 64 × 255 = 16,320 bits. This is why reducing register usage per thread can increase occupancy more effectively than reducing shared memory usage.

### Register File Bank Conflicts

- [inference] The register file is organized into banks (64 banks on GA100, 32 bits per bank). Each cycle, the operand collector reads up to 3 source operands per warp instruction (2 sources + potential predicate). If multiple threads within a warp access the same bank in the same cycle, the access serializes — a register bank conflict. The bank index for register R in thread T is (R + T) % num_banks for stride-1 access patterns, or simply R % num_banks for uniform access.
- [inference] Bank conflicts typically cost 1 additional cycle per conflict with up to 3-way conflicts being common in unrolled loops with large register arrays. A kernel using 64+ registers per thread and accessing a strided array of 64 elements across the warp sees every access conflict with every other — a worst-case 32-cycle penalty per instruction. Mitigation: pad register arrays to odd sizes (avoid multiples of bank count), use `__restrict__` to allow the compiler to reorder accesses, and restructure computations to reduce live register count.

## Tensor Core Instruction Scheduling

- [inference] MMA (matrix multiply-accumulate) instructions differ from scalar instructions: they operate on entire warp register files simultaneously (all 32 threads contribute their 4×8 FP16 matrices to a collective 16×16×16 MMA). The scoreboard treats the MMA's destination register block atomically — all destination registers go busy when the MMA issues and clear simultaneously when it completes. This means the scheduler cannot issue any instruction touching those registers for the full MMA latency (8–16 cycles on A100, 4–8 on H100 with async MMA).
- [inference] Hopper's WGMMA (Warp Group MMA) decouples the MMA trigger from data movement: the scheduler fires a WGMMA trigger instruction, then continues executing other independent instructions from the same warp while TMA asynchronously feeds data from shared memory into the Tensor Core accumulator. Synchronization is explicit via `wgmma.wait_group` barriers. This is the hardware-level realization of the producer-consumer pattern between data movement and computation.

## Comparison with RISC-V Execution Architecture

- [inference] GPU warp scheduling and RISC-V vector execution represent two ends of a spectrum: GPU warps are hardware-managed (the scheduler transparently context-switches stalled warps), while RISC-V vectors are software-managed (the programmer or compiler explicitly controls vector length and strip-mining). Each approach has distinct advantages: GPU hardware scheduling provides better latency hiding for irregular workloads with unpredictable memory access patterns; RISC-V software scheduling provides better determinism and lower area overhead for regular compute-bound workloads.
- [inference] The warp scheduler's complexity (scoreboard tracking, multi-issue logic, SIMT stack management) is a significant fraction of SM area — estimated at 10–15% of SM logic area excluding register files and shared memory. RISC-V vector processors avoid this overhead entirely, dedicating the equivalent area to additional vector ALUs or larger register files — a design trade-off that favors throughput over generality.

## Open Questions

- OPEN: As NVIDIA moves toward asynchronous execution (TMA, WGMMA, device-side graph launch), does the traditional scoreboard-based warp scheduler become a bottleneck that must be replaced by a fully dataflow-driven dispatch model?
- OPEN: Can independent thread scheduling (Volta+) eventually eliminate the SIMT stack entirely, or does full per-thread scheduling require prohibitive per-thread state that negates the area advantage of SIMT?
- VERIFY: The claim that the warp scheduler occupies 10–15% of SM logic area is an estimate based on die photo analysis — NVIDIA does not publish per-unit area breakdowns.

## See Also

- [[hw.gpu.simt]] — SIMT execution model overview that the warp scheduler implements.
- [[hw.riscv.execution-architecture]] — RISC-V execution architecture offering a different scheduling philosophy.
- [[hw.gpu.overview]] — GPU architecture overview including SM organization.
- [[hw.gpu.tensor-cores]] — Tensor Cores whose MMA instructions the warp scheduler dispatches.
- [[hw.gpu.thread-blocks-occupancy]] — Occupancy model where warp scheduler capacity is the limiting resource.
- [[hw.compute.numerical-precision-ai]] — Numerical precision choice affects per-instruction throughput and warp scheduler pressure.
