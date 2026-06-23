---
id: hw.gpu.simt
title: SIMT Execution Model
status: draft
layer: 70-execution-architecture
layer_path: 70-execution-architecture/gpu/simt
parent: hw.gpu.overview
secondary_layers: [80-programming-interface-dsl]
granularity: mechanism
concept_type: execution_model
scale_scope: [tile, die]
reasoning_roles: [abstraction, mapping]
tags: [gpu, simt, cuda, warp, execution]
aliases: [single instruction multiple threads, warp execution]
sources: [nvidia-cuda-programming-guide-v13.3]
---

# SIMT Execution Model

## First-Principle Explanation

SIMT turns many programmer-visible threads into groups that the hardware can schedule efficiently. The programmer writes code as if each thread has its own control flow and data, while the hardware groups threads to execute common instructions together.

The first-principle constraint is control coherence:

```text
threads doing the same instruction on different data -> efficient grouped execution
threads diverging into different paths -> scheduling and utilization cost
```

## Why It Matters

SIMT explains why GPUs like regular, data-parallel kernels. It also explains why branch divergence, irregular memory access, and small workloads can underuse the hardware.

## Key Terms

| Term | Meaning |
| --- | --- |
| Thread | Programmer-visible unit of execution |
| Warp | NVIDIA scheduling group of CUDA threads |
| Divergence | Threads in a group need different control paths |
| Predication | Conditional execution technique that can avoid some branch overhead |

## Verified Claims

- [supported][src:nvidia-cuda-programming-guide-v13.3] CUDA's programming guide describes GPU programming around many threads and includes SIMT kernel execution as a core concept.
- [inference][src:nvidia-cuda-programming-guide-v13.3] Workloads with coherent control flow are generally easier to map efficiently to SIMT execution than highly divergent workloads.

## Industry Logic

SIMT is one reason AI tensor programs are a strong GPU fit: many operations apply the same instruction pattern across large data arrays. It is also a reason that not every workload benefits equally from GPUs.

## Related Concepts

- [[hw.gpu.overview|GPU Architecture Overview]]
- [[hw.gpu.thread-blocks-occupancy|Thread Blocks and Occupancy]]

## Open Questions

- VERIFY: Add AMD wavefront and Intel Xe terminology for cross-vendor comparison.
