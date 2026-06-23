---
id: hw.gpu.tensor-cores
title: Tensor Cores
status: draft
layer: hw-sw-system
tags: [gpu, tensor-core, matrix-math, ai, precision]
aliases: [matrix acceleration]
sources: [nvidia-a100-architecture-whitepaper-2020, markidis-tensor-core-2018, williams-roofline-2009]
---

# Tensor Cores

## First-Principle Explanation

Tensor Cores are specialized matrix math units. They exploit a repeated structure in AI and HPC workloads: many operations are dense matrix multiply-accumulate operations.

The first-principle tradeoff is specialization:

```text
specialized matrix datapath -> higher throughput and efficiency
less general than ordinary scalar/vector execution -> depends on workload shape and precision tolerance
```

## Why It Matters

AI training and inference rely heavily on matrix multiplication. Specialized matrix units can dramatically raise peak throughput, but real speedup depends on software using the right data layouts, numerical formats, batching, and memory movement.

## Key Terms

| Term | Meaning |
| --- | --- |
| MMA | Matrix multiply-accumulate |
| WMMA | CUDA warp-level matrix multiply-accumulate API |
| Mixed precision | Using lower precision inputs or operations with higher precision accumulation |
| TF32 | NVIDIA Ampere Tensor Core mode for FP32-like workflows with reduced multiply precision |

## Verified Claims

- [supported][src:nvidia-a100-architecture-whitepaper-2020] NVIDIA A100 includes third-generation Tensor Cores with support for multiple AI and HPC data types.
- [supported][src:markidis-tensor-core-2018] Tensor Core performance and precision depend on programming approach and numerical behavior, not only hardware peak claims.
- [inference][src:williams-roofline-2009] Tensor Core peak throughput can be bottlenecked by memory movement or insufficient arithmetic intensity.

## Industry Logic

Tensor Cores explain why AI accelerators are not only "GPUs with more cores." Matrix-specialized datapaths, numerical formats, libraries, and model architectures co-evolve.

## Related Concepts

- [[hw.gpu.overview|GPU Architecture Overview]]
- [[hw.gpu.memory-hierarchy|GPU Memory Hierarchy]]
- [[programmer.roofline-model|Roofline Performance Model]]

## Open Questions

- VERIFY: Add Hopper and Blackwell Tensor Core changes as separate vendor-specific concepts.
- OPEN: Add precision concept covering FP32, TF32, BF16, FP16, FP8, and accumulation.
