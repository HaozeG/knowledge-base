---
id: software.gpu.runtime-execution-systems
title: GPU Runtime Execution Systems — Streams, Graphs, and Command Scheduling
status: draft
layer: 100-runtime-execution-system
layer_path: 100-runtime-execution-system/gpu/runtime-execution-streams-graphs
parent: software.riscv.ai-runtime-execution
secondary_layers: [80-programming-interface-dsl, 90-compiler-lowering-stack, 110-workload-mapping]
granularity: concept
concept_type: runtime_mechanism
scale_scope: [tile, die, node]
reasoning_roles: [enabler, bottleneck, abstraction, mapping]
tags: [cuda-streams, cuda-graphs, kernel-launch, command-scheduling, gpu-driver, gpu-runtime, asynchronous-execution, latence-hiding]
aliases: [CUDA runtime, GPU command scheduling, CUDA streams and graphs, kernel launch overhead, GPU execution model]
sources: [cuda-graphs-nvidia-2025, urgengo-kernel-launch-2025, opara-operator-parallelism-2025, cuda-programming-guide-2025]
---

# GPU Runtime Execution Systems — Streams, Graphs, and Command Scheduling

## Overview

The GPU runtime execution system is the software layer that transforms compiled kernels into work executing on GPU hardware. It manages command submission from the CPU host to the GPU device, orchestrates concurrent execution across multiple hardware queues, and minimizes the latency gap between "code is ready to run" and "code is running." For AI workloads with thousands of small kernel invocations per training step, the runtime's efficiency determines whether the GPU is computing or waiting.

- [supported][src:cuda-programming-guide-2025] The CUDA runtime stack has three layers: the **user-mode driver** (libcuda) translates API calls into hardware command packets, the **kernel-mode driver** manages device memory and submits command buffers to the GPU, and the **GPU command processor** (CP) fetches and dispatches commands to execution units. Each layer adds queueing and dispatch latency.
- [supported][src:urgengo-kernel-launch-2025] Launching 323 small kernels for an autonomous driving perception model took 7 ms — 35% of total GPU execution time — at ~5–10 µs per kernel launch. For AI inference with many element-wise and normalization ops, kernel launch overhead can dominate total latency if not managed through batching or graph capture.
- [inference] The fundamental tension in GPU runtime design: the CPU-to-GPU command submission path is a serial bottleneck, while the GPU's execution units are massively parallel. The runtime must batch, pipeline, and precompile work to keep the GPU fed without the CPU becoming the limiting factor.

## CUDA Streams: Concurrent Execution

A CUDA stream is an ordered sequence of GPU operations (kernel launches, memory copies, events) that execute in FIFO order within the stream but may execute concurrently with operations in other streams.

- [inference] Streams enable three forms of concurrency: (1) **kernel/kernel concurrency** — multiple kernels from different streams occupying different SMs simultaneously if each doesn't consume all SMs; (2) **kernel/copy concurrency** — a kernel executing while a DMA engine transfers data between host and device; (3) **copy/copy concurrency** — bidirectional transfers on dual-DMA engines.
- [inference] Effective stream usage requires understanding the GPU's hardware queues: NVIDIA GPUs have one compute engine queue and one or two copy engine queues. All kernel launches compete for the single compute queue — streams only help if kernels don't saturate the GPU. The Hyper-Q feature (Kepler+) provides 32 hardware work queues, allowing true concurrent kernel execution from multiple streams.
- [inference] For AI training, a common stream pattern: Stream 1 runs the forward pass kernel, Stream 2 runs the backward pass of the previous layer (overlapped), and Stream 3 runs gradient AllReduce via NCCL. This 3-stream pipeline can hide ~30–40% of the training step's non-compute time.

## CUDA Graphs: Precompiled Execution

CUDA Graphs decouple the definition of GPU work from its submission. Instead of launching each kernel individually (paying per-launch overhead), the application defines a DAG of operations once, instantiates it (compiles into an optimized command buffer), and replays it with a single lightweight call.

- [supported][src:cuda-graphs-nvidia-2025] A CUDA Graph launch costs ~2.5 µs + ~1 ns per node on Ampere, compared to 400 µs for launching 100 kernels sequentially via streams. For iterative workloads replayed thousands of times, the upfront instantiation cost (100s of µs to ms) amortizes to near zero per replay.
- [inference] Graph instantiation performs whole-graph optimizations: kernel fusion (merging adjacent element-wise ops into a single kernel), memory aliasing (reusing intermediate buffers across non-overlapping graph segments), and concurrent scheduling (identifying independent nodes and assigning them to parallel execution queues). These optimizations go beyond what individual kernel launches can express.
- [inference] CUDA 12.4+ **conditional nodes** enable dynamic control flow within graphs (if/else, loops) evaluated on-device without CPU round-trips. This is critical for inference serving where the execution path depends on request parameters (batch size, sequence length) — the runtime can branch within the graph rather than rebuilding it per request.

### Graph Capture vs. Explicit Construction

- [inference] **Stream capture** (`cudaStreamBeginCapture`): the runtime records all operations submitted to a stream into a graph automatically. Simple to use but limited — captures only what the stream API exposes. Unknown sizes or control flow break capture.
- [inference] **Explicit graph API** (`cudaGraphAddKernelNode`): the application manually builds the DAG node-by-node. More verbose but supports dynamic parameters via `cudaGraphExecUpdate` — changing kernel arguments without re-instantiating the entire graph. This is the production approach for AI inference where tensor shapes change per request.

## Device-Side Execution and Self-Scheduling

- [inference] CUDA 12.0+ **device-side graph launch** allows a GPU kernel to launch a CUDA Graph directly from device code. This enables GPU self-scheduling — a single persistent kernel on the GPU can dispatch sub-graphs without CPU involvement. For AI inference, this eliminates the CPU from the token-generation hot loop entirely.
- [inference] The extreme case: **CUDA device-side kernel launches** (dynamic parallelism) allow any GPU thread to launch new kernels. While potentially eliminating CPU bottlenecks, the launch granularity (thread-level) creates scheduling overhead within the GPU itself. Device-side graph launch provides a middle ground: one GPU-level decision triggers a pre-compiled graph.

## Comparison with RISC-V Runtime

- [inference] GPU runtime design is shaped by the host/device split — the CPU is the "orchestrator" that submits work to the GPU "accelerator." RISC-V AI runtimes collapse this split: the PE array and the control processor share the same ISA and memory space. This eliminates the kernel launch overhead problem entirely (PE dispatch is a function call, not a driver command), but requires the PE runtime to handle scheduling and resource allocation that GPU drivers provide as a service.
- [inference] CUDA Graphs are solving a problem that RISC-V runtimes don't have: the CPU-to-accelerator command submission bottleneck. However, RISC-V runtimes face the analogous challenge of coordinating hundreds of PEs with sub-microsecond dispatch granularity — a problem GPU runtimes avoid by dispatching at warp granularity (32 threads per scheduler tick).

## Open Questions

- OPEN: Can CUDA Graphs achieve "zero dispatch" — fully eliminating the CPU from the execution loop — for all AI inference patterns, or do varying batch sizes and dynamic control flow always require CPU involvement for some requests?
- OPEN: As GPU architectures add more asynchronous engines (DMA, tensor, shader), does the stream model need to evolve into a general task graph model where all GPU operations are graph nodes?
- VERIFY: The claimed ~2.5 µs graph launch latency on Ampere — what is the measured latency on Blackwell with FP4 kernels, and does the smaller per-kernel compute time (due to FP4 throughput) re-expose the launch overhead?

## See Also

- [[software.riscv.ai-runtime-execution]] — RISC-V AI runtime execution and its different approach to dispatch.
- [[software.control.dsl-compiler-runtime]] — The DSL/compiler/runtime separation framework.
- [[workload.ai.multi-model-serving]] — Multi-model serving that depends on efficient runtime dispatch.
- [[software.ai.multi-tenant-inference-scheduling]] — Multi-tenant scheduling built on the runtime execution infrastructure.
- [[software.compiler.ml-compiler-lowering-riscv]] — ML compiler lowering that generates the kernels the runtime dispatches.
