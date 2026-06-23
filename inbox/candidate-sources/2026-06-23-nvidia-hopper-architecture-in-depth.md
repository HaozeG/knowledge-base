---
source_id: nvidia-hopper-architecture-in-depth-2022
title: NVIDIA Hopper Architecture In-Depth
status: triaged
quality_tier: B
url: https://developer.nvidia.com/blog/nvidia-hopper-architecture-in-depth/
---

# Candidate Source: NVIDIA Hopper Architecture In-Depth

## Why This Source Was Chosen

This official NVIDIA technical blog is a good ingestion test because it touches multiple layers at once:

- accelerator architecture: SM changes, Tensor Cores, DPX
- memory system: Tensor Memory Accelerator, shared memory, L2, HBM3
- programming model: thread block clusters and asynchronous barriers
- scale-out system: NVLink, NVSwitch, NVLink Switch System
- workload pattern: transformers, LLM training and inference, dynamic programming

## Triage

- Source type: official vendor technical article.
- Source quality: B.
- Reason for B instead of A: useful technical detail, but vendor performance claims and product claims should be cross-checked against architecture whitepapers, CUDA docs, and independent measurements before promotion to `verified`.
- Handling note: ignore page-level AI-generated summaries and use the article body, official docs, or linked primary sources for accepted claims.

## Candidate Claims

- [supported][src:nvidia-hopper-architecture-in-depth-2022] Hopper adds Tensor Memory Accelerator machinery for asynchronous movement between global memory and shared memory.
- [supported][src:nvidia-hopper-architecture-in-depth-2022] Hopper adds thread block clusters as a CUDA hierarchy level above thread blocks.
- [supported][src:nvidia-hopper-architecture-in-depth-2022] Hopper adds FP8 Tensor Core support and a Transformer Engine for transformer workloads.
- [supported][src:nvidia-hopper-architecture-in-depth-2022] Hopper extends scale-out connectivity through NVLink/NVSwitch/NVLink Switch System features.

## Concepts To Update Or Create

- Create `hw.gpu.tensor-memory-accelerator`.
- Create `hw.gpu.thread-block-clusters`.
- Later: create `hw.gpu.fp8-transformer-engine`.
- Later: create `system.cluster.nvlink-switch-system`.

## Open Questions

- VERIFY: Which claims are repeated in the H100 architecture whitepaper?
- VERIFY: Which features are exposed in CUDA docs versus described only in product material?
- OPEN: How should we separate general GPU architecture ideas from Hopper-specific mechanisms?
