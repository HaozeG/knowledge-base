---
id: programmer.roofline-model
title: Roofline Performance Model
status: draft
layer: 140-performance-cost-utilization-model
layer_path: 140-performance-cost-utilization-model/arithmetic-intensity
parent: hw.gpu.overview
secondary_layers: [50-memory-data-movement, 110-workload-mapping]
granularity: model
concept_type: performance_model
scale_scope: [tile, die, node]
reasoning_roles: [indicator, bottleneck]
tags: [performance, roofline, arithmetic-intensity, bandwidth, gpu]
aliases: [roofline model]
sources: [williams-roofline-2009]
---

# Roofline Performance Model

## First-Principle Explanation

Roofline is a visual performance model based on two limits:

```text
memory bandwidth limit: performance <= bandwidth * arithmetic intensity
compute limit: performance <= peak compute throughput
```

Arithmetic intensity is the amount of work done per byte moved. Low arithmetic intensity points toward memory-bound behavior. High arithmetic intensity creates the possibility of compute-bound behavior.

## Why It Matters

Roofline is a compact way to prevent bad GPU reasoning. A GPU can have enormous peak compute throughput while a workload still runs slowly because it moves too much data or cannot reuse data efficiently.

## Key Terms

| Term | Meaning |
| --- | --- |
| FLOPs | Floating-point operations |
| Arithmetic intensity | Operations per byte of data movement |
| Bandwidth ceiling | Maximum performance implied by memory bandwidth |
| Compute ceiling | Maximum performance implied by compute throughput |
| Ridge point | Arithmetic intensity where the memory and compute ceilings meet |

## Verified Claims

- [verified][src:williams-roofline-2009] Roofline relates performance to arithmetic intensity, memory bandwidth, and peak compute throughput.
- [inference][src:williams-roofline-2009] Roofline is useful for deciding whether to focus on data movement, locality, or compute utilization.

## Industry Logic

Roofline helps evaluate accelerator claims. More peak FLOPs matter only when workloads can reach enough arithmetic intensity and software can use the relevant hardware path.

## Related Concepts

- [[hw.gpu.overview|GPU Architecture Overview]]
- [[hw.gpu.memory-hierarchy|GPU Memory Hierarchy]]
- [[hw.gpu.tensor-cores|Tensor Cores]]

## Open Questions

- OPEN: Add worked examples for GEMM, attention, elementwise ops, and reductions.
