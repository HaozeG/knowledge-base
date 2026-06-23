---
id: hw.gpu.memory-hierarchy
title: GPU Memory Hierarchy
status: draft
layer: hw-sw-system
tags: [gpu, memory, hbm, cache, shared-memory, bandwidth]
aliases: [gpu memory system]
sources: [nvidia-cuda-programming-guide-v13.3, nvidia-a100-architecture-whitepaper-2020, williams-roofline-2009]
---

# GPU Memory Hierarchy

## First-Principle Explanation

Moving data is expensive. A GPU memory hierarchy exists to keep data close enough to many execution lanes so that compute units are not idle waiting for distant memory.

The basic hierarchy is:

```text
registers/shared memory/cache/HBM/interconnect/host memory
```

Each level trades capacity, latency, bandwidth, programmability, and sharing scope.

## Why It Matters

AI workloads are often described by FLOPs, but many kernels are limited by memory movement. GPU performance depends on whether the software can reuse data near compute and issue memory accesses that use the available bandwidth efficiently.

## Key Terms

| Term | Meaning |
| --- | --- |
| Register | Fast per-thread storage |
| Shared memory | Programmer-managed on-chip memory shared by threads in a block |
| L2 cache | Larger on-chip cache shared across GPU resources |
| HBM | High-bandwidth off-chip memory close to the GPU package |
| Arithmetic intensity | Work per byte of data movement |

## Verified Claims

- [supported][src:nvidia-a100-architecture-whitepaper-2020] NVIDIA A100 includes HBM2 memory and L2 cache as major parts of its architecture.
- [supported][src:nvidia-cuda-programming-guide-v13.3] CUDA exposes memory spaces and memory behavior that programmers must understand for performance.
- [verified][src:williams-roofline-2009] The roofline model relates attainable performance to arithmetic intensity, memory bandwidth, and compute peak.

## Industry Logic

HBM capacity, bandwidth, packaging, and memory supply can become industry bottlenecks because AI accelerators need to feed many compute units. This links GPU architecture to packaging, memory vendors, and datacenter system design.

## Related Concepts

- [[hw.gpu.overview|GPU Architecture Overview]]
- [[programmer.roofline-model|Roofline Performance Model]]

## Open Questions

- OPEN: Add HBM-specific concept under `chip.memory`.
- OPEN: Add interconnect and multi-GPU memory hierarchy concepts.

