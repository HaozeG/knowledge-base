---
id: hw.gpu.thread-block-clusters
title: Thread Block Clusters
status: draft
layer: 80-programming-interface-dsl
layer_path: 80-programming-interface-dsl/cuda/thread-block-clusters
parent: hw.gpu.thread-blocks-occupancy
secondary_layers: [70-execution-architecture, 100-runtime-execution-system]
granularity: mechanism
concept_type: programming_interface
scale_scope: [tile, die]
reasoning_roles: [abstraction, synchronization, locality_strategy]
tags: [gpu, hopper, cuda, thread-blocks, locality, synchronization]
aliases: [block clusters, CUDA clusters]
sources: [nvidia-hopper-architecture-in-depth-2022]
---

# Thread Block Clusters

## First-Principle Explanation

Classic CUDA exposes a hierarchy of grids, blocks, and threads. Hopper adds a level where multiple thread blocks can be grouped so they are scheduled concurrently and can cooperate across SMs.

The first-principle logic is locality control:

```text
one block is too small for some locality patterns
  -> group blocks that must cooperate
  -> expose synchronization and data sharing across nearby SM resources
```

## Why It Matters

Thread block clusters make some cross-block cooperation more explicit. This matters when kernels need coordinated data movement, shared-memory exchange, or synchronization at a scope larger than a single block but smaller than an entire grid.

They also show a recurring GPU architecture pattern: hardware adds a feature, then the programming model grows so software can express enough structure to use it.

## Key Terms

| Term | Meaning |
| --- | --- |
| Thread block | CUDA group of threads that can cooperate through shared memory and synchronization |
| Cluster | Hopper-era group of thread blocks scheduled to cooperate across SMs |
| Distributed shared memory | Mechanism for shared-memory-like access across blocks in a cluster |
| Synchronization scope | The set of work units that can coordinate through a synchronization primitive |

## Verified Claims

- [supported][src:nvidia-hopper-architecture-in-depth-2022] Hopper adds thread block clusters as a CUDA hierarchy level above thread blocks.
- [supported][src:nvidia-hopper-architecture-in-depth-2022] The article connects thread block clusters with cross-SM cooperation, asynchronous units, and distributed shared memory.
- [inference][src:nvidia-hopper-architecture-in-depth-2022] Thread block clusters are best understood as a programming-model exposure of hardware locality and synchronization constraints.

## Industry Logic

Thread block clusters are not a market story by themselves. They matter because they make new hardware mechanisms usable by libraries and kernel authors. If CUDA libraries exploit them well, the effective performance gap between architectures can widen for supported workloads.

## Related Concepts

- [[hw.gpu.thread-blocks-occupancy|Thread Blocks and Occupancy]]
- [[hw.gpu.simt|SIMT Execution Model]]
- [[hw.gpu.tensor-memory-accelerator|Tensor Memory Accelerator]]
- [[hw.gpu.memory-hierarchy|GPU Memory Hierarchy]]

## Open Questions

- VERIFY: Cross-check the programming model details against the CUDA Programming Guide.
- OPEN: Add examples for cluster-level synchronization and distributed shared memory.
- OPEN: Compare with non-NVIDIA programming models if similar hierarchy appears elsewhere.
