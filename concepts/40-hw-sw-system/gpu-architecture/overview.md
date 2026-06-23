---
id: hw.gpu.overview
title: GPU Architecture Overview
status: draft
layer: hw-sw-system
tags: [gpu, architecture, parallelism, ai-systems]
aliases: [gpu architecture]
sources: [nvidia-cuda-programming-guide-v13.3, nvidia-a100-architecture-whitepaper-2020, williams-roofline-2009]
---

# GPU Architecture Overview

## First-Principle Explanation

A GPU is a throughput machine. It spends silicon area on many parallel execution lanes and high-bandwidth memory paths instead of optimizing for the lowest latency of one instruction stream.

The core tradeoff is:

```text
more parallel work + enough data locality + enough memory bandwidth -> high throughput
```

This is different from a latency-oriented CPU model. A GPU wins when a workload can expose many similar operations, tolerate scheduling latency, and reuse data close to the compute units.

## Why It Matters

Modern AI workloads contain large matrix and tensor operations. Those operations can expose massive parallelism and reuse, which maps well to GPUs when the software stack keeps the hardware fed.

For industry analysis, GPU architecture is not just "more FLOPs." It is a system of compute units, memory hierarchy, interconnect, programming model, libraries, numerical formats, and utilization constraints.

## Key Terms

| Term | Meaning |
| --- | --- |
| SM | Streaming Multiprocessor, NVIDIA's repeated GPU compute block |
| Warp | A group of threads scheduled together in NVIDIA CUDA execution |
| SIMT | Single Instruction, Multiple Threads execution model |
| Occupancy | Active warps relative to hardware capacity |
| HBM | High Bandwidth Memory used by many datacenter GPUs |
| Tensor Core | Specialized matrix math unit in modern NVIDIA GPUs |

## Verified Claims

- [supported][src:nvidia-cuda-programming-guide-v13.3] CUDA exposes a programming model where kernels execute across many threads organized through the GPU programming abstraction.
- [supported][src:nvidia-a100-architecture-whitepaper-2020] NVIDIA A100 organizes compute around repeated Streaming Multiprocessors and includes specialized Tensor Core, HBM, L2 cache, and NVLink-related system features.
- [inference][src:nvidia-cuda-programming-guide-v13.3][src:williams-roofline-2009] GPU performance should be reasoned about as both compute throughput and data movement, not peak FLOPs alone.

## Industry Logic

GPU market strength is partly explained by the match between AI workloads and GPU throughput architecture. The durable logic is workload fit:

```text
dense tensor math -> high parallelism and reuse -> GPU utilization opportunity -> datacenter demand
```

The fragile part is company-specific valuation. That depends on supply, margins, competition, software lock-in, customer concentration, and capex timing.

## Related Concepts

- [[hw.gpu.simt|SIMT Execution Model]]
- [[hw.gpu.memory-hierarchy|GPU Memory Hierarchy]]
- [[hw.gpu.thread-blocks-occupancy|Thread Blocks and Occupancy]]
- [[hw.gpu.tensor-cores|Tensor Cores]]
- [[programmer.roofline-model|Roofline Performance Model]]

## Open Questions

- VERIFY: Add architecture-neutral GPU sources beyond NVIDIA.
- OPEN: Split vendor-specific NVIDIA concepts from general GPU architecture concepts.
