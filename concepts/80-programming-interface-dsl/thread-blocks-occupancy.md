---
id: hw.gpu.thread-blocks-occupancy
title: Thread Blocks and Occupancy
status: draft
layer: 80-programming-interface-dsl
layer_path: 80-programming-interface-dsl/cuda/thread-hierarchy
parent: hw.gpu.simt
secondary_layers: [70-execution-architecture, 140-performance-cost-utilization-model]
granularity: mechanism
concept_type: programming_interface
scale_scope: [tile, die]
reasoning_roles: [abstraction, mapping, indicator]
tags: [gpu, cuda, occupancy, scheduling, latency-hiding]
aliases: [cuda blocks, gpu occupancy]
sources: [nvidia-cuda-programming-guide-v13.3]
---

# Thread Blocks and Occupancy

## First-Principle Explanation

GPU hardware hides latency by keeping many independent pieces of work available. CUDA exposes this through grids, blocks, and threads.

The practical question is not only "how many operations exist?" but:

```text
can enough independent work be resident and schedulable while memory and pipelines are waiting?
```

Occupancy is one signal for this, but high occupancy alone does not guarantee high performance.

## Why It Matters

Thread-block sizing affects scheduling, register pressure, shared memory use, and latency hiding. This is a programmer-visible handle on architecture utilization.

## Key Terms

| Term | Meaning |
| --- | --- |
| Grid | Full launch space for a CUDA kernel |
| Block | Group of threads that can cooperate through shared memory and synchronization |
| Resident block | A block currently assigned to an SM |
| Occupancy | Ratio of active warps to maximum possible active warps |
| Latency hiding | Scheduling other work while one warp waits |

## Verified Claims

- [supported][src:nvidia-cuda-programming-guide-v13.3] CUDA kernels use thread hierarchy concepts including grids, blocks, and threads.
- [inference][src:nvidia-cuda-programming-guide-v13.3] Occupancy is a utilization-related signal, but kernel performance also depends on memory behavior, instruction mix, and dependency structure.

## Industry Logic

Occupancy links architecture to software skill. Hardware peak performance does not become economic value unless compilers, libraries, and programmers can expose enough parallel work.

## Related Concepts

- [[hw.gpu.overview|GPU Architecture Overview]]
- [[hw.gpu.simt|SIMT Execution Model]]
- [[hw.gpu.memory-hierarchy|GPU Memory Hierarchy]]
- [[hw.gpu.thread-block-clusters|Thread Block Clusters]]

## Open Questions

- VERIFY: Add concrete examples from CUDA occupancy calculator or official occupancy docs.
