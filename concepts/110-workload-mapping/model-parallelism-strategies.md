---
id: workload.ai.model-parallelism-strategies
title: AI Model Parallelism Strategies for Large-Scale Training and Inference
status: draft
layer: 110-workload-mapping
layer_path: 110-workload-mapping/parallelism/model-parallelism-strategies
parent: workload.ai.rvv-kernel-patterns
secondary_layers: [100-runtime-execution-system, 120-scale-up-system, 130-scale-out-distributed-system, 140-performance-cost-utilization-model]
granularity: concept
concept_type: workload_pattern
scale_scope: [tile, die, node, cluster]
reasoning_roles: [enabler, mapping, bottleneck, locality_strategy, scale_out_strategy]
tags: [tensor-parallelism, pipeline-parallelism, data-parallelism, expert-parallelism, sequence-parallelism, fsdp, zero, megatron, deepspeed, model-parallelism]
aliases: [3D parallelism, hybrid parallelism, distributed training strategies, model sharding, FSDP ZeRO]
sources: [megatron-lm-tp-2020, deepspeed-zero-2021, gpipe-pipeline-2019, megatron-core-5d-2025, galvatron-auto-parallel-2025, fsdp-model-parallelism-tmlr-2025, jax-scaling-book-2025, moe-parallel-folding-2025]
---

# AI Model Parallelism Strategies for Large-Scale Training and Inference

## Overview

When an AI model is too large to fit on a single accelerator, or when training throughput must exceed what one device can provide, the model must be partitioned across multiple devices. The choice of how to partition — which dimensions of the computation to split and how to communicate between partitions — is the central design problem of distributed AI training and inference.

- [supported][src:megatron-lm-tp-2020] The fundamental constraint is that any parallelism strategy must respect the forward/backward data dependencies of the model computation graph. The optimal partition minimizes communication while balancing compute across devices, subject to the hardware topology (intra-node NVLink bandwidth vs. inter-node network bandwidth vs. memory capacity).
- [supported][src:fsdp-model-parallelism-tmlr-2025] Contrary to earlier assumptions, model parallelism (TP/PP) improves global throughput even when combined with FSDP — purely data-parallel approaches suffer >30% power efficiency reduction at scale due to exposed communication. 2D parallelism (FSDP + TP) is the practical sweet spot for models up to ~70B parameters.

## The Five Parallelism Dimensions

### 1. Data Parallelism (DP)

Data parallelism replicates the model on every device and partitions the training batch. Each device computes gradients on its data shard, then gradients are averaged (AllReduce) across all devices.

- [supported][src:deepspeed-zero-2021] Pure DP is memory-inefficient because every device stores a full copy of model parameters, gradients, and optimizer states. For a 70B-parameter model in BF16 + Adam, this requires ~1,120 GB per device — impossible on any single GPU.
- [inference] DP communication cost is O(model_size) per step via AllReduce, but this can overlap with compute. DP scales well on bandwidth-constrained interconnects because AllReduce algorithms (ring, tree) distribute the bandwidth load.

### 2. Tensor Parallelism (TP)

Tensor parallelism splits individual layer weight matrices across devices. For a linear layer `Y = XW`, column-parallel TP splits W into `[W₁, W₂]` across 2 devices, each computing `Yᵢ = XWᵢ`, then concatenating results via AllGather.

- [supported][src:megatron-lm-tp-2020] Megatron-LM-style TP splits both the Attention and MLP sublayers, inserting one AllReduce (or AllGather + ReduceScatter) per Transformer layer in the forward pass. This makes TP strongly dependent on intra-node bandwidth — typically deployed within an NVLink domain (8 GPUs) where bandwidth exceeds 600 GB/s.
- [inference][src:jax-scaling-book-2025] TP becomes communication-bound when the model dimension `F > Y × C / W_ici`, where `Y` is the TP degree, `C` is chip FLOPs, and `W_ici` is interconnect bandwidth. For LLaMA 3-70B (F ≈ 30,000) on TPU v5p: 8-way TP stays in the compute-bound regime; 16-way TP hits the communication wall.
- [inference] TP's critical limitation: the AllReduce inside each layer is on the critical path and cannot overlap with compute. This makes TP the most bandwidth-sensitive of all parallelism strategies.

### 3. Pipeline Parallelism (PP)

Pipeline parallelism splits the model by depth — device 1 owns layers 1–N/k, device 2 owns layers N/k+1–2N/k, etc. Activations flow sequentially through the pipeline.

- [supported][src:gpipe-pipeline-2019] GPipe introduced microbatch pipeline parallelism: split each training batch into M microbatches, inject them into the pipeline sequentially, and accumulate gradients across microbatches. This achieves high utilization at the cost of activation memory proportional to M.
- [inference] The 1F1B (One Forward, One Backward) schedule from PipeDream reduces activation memory by injecting backward passes as soon as a device finishes its forward pass for a microbatch. Interleaved 1F1B (Megatron-LM) further reduces the pipeline bubble by interleaving multiple pipeline stages per device, reducing idle time from O(P-1)/M to O(P-1)/(M×V) where V is the number of virtual stages per device.
- [inference] PP is best deployed across nodes where inter-node bandwidth (100–400 GB/s with InfiniBand/RoCE) is lower than intra-node NVLink. PP communication is point-to-point and scales with activation size, not model size.

### 4. Sequence Parallelism (SP) / Context Parallelism (CP)

For long-context models (128K+ tokens), the attention computation's O(L²) memory makes even single-layer execution infeasible. Sequence parallelism splits the input sequence across devices along the token dimension.

- [inference] SP is typically paired with TP: Ring Attention splits Q/K/V blocks across SP groups, communicating KV blocks through peer-to-peer rings. For a 128K-token sequence with 8-way SP, each device computes attention on a 16K-token window, reducing per-device attention memory by 8×.
- [inference] The communication pattern is All-to-All for KV redistribution between attention blocks, which is more complex than TP's AllReduce and benefits from high-radix networks.

### 5. Expert Parallelism (EP)

Mixture of Experts (MoE) models route each token to a subset of expert networks. Expert parallelism distributes experts across devices and uses All-to-All communication to route tokens to their assigned experts.

- [supported][src:moe-parallel-folding-2025] MoE Parallel Folding decouples Attention and MoE layer parallelization, allowing each to adopt its optimal configuration — TP for attention layers (dense computation) and EP for expert layers (sparse routing). This achieves up to 49.3% MFU on Mixtral 8×22B across 1,024 GPUs.

## FSDP and ZeRO: Sharded Data Parallelism

FSDP (Fully Sharded Data Parallelism) in PyTorch and ZeRO in DeepSpeed take a different approach: they shard model parameters, gradients, and optimizer states across data-parallel devices, AllGathering parameters on-demand just before each layer's forward pass and discarding them after the backward pass.

- [supported][src:deepspeed-zero-2021] ZeRO-3 partitions all three (parameters, gradients, optimizer states) across DP ranks, reducing per-device memory to O(model_size/P). For an 8-GPU cluster: a 70B model drops from ~1,120 GB per device to ~140 GB, making it feasible on 80 GB GPUs.
- [inference][src:jax-scaling-book-2025] FSDP's communication pattern (AllGather + ReduceScatter per layer) can overlap with compute for the previous layer. The compute-bound condition is `B/X > C/W_ici` where `B` is global batch tokens, `X` is FSDP devices, `C` is chip FLOPs, and `W_ici` is interconnect bandwidth. With sufficient batch size, FSDP scales to 10,000+ devices before becoming communication-bound.
- [inference] The practical distinction between FSDP and ZeRO-3 has narrowed in 2025: both achieve O(1/P) memory scaling. FSDP is natively integrated into PyTorch; ZeRO provides additional optimizations (1-bit Adam compression, CPU/NVMe offload) for extreme-scale training.

## Hybrid Parallelism: The 3D/5D Recipe

Production training of frontier models uses all dimensions simultaneously:

| Model | Parameters | GPUs | Parallelism Configuration |
|---|---|---|---|
| Llama 3 405B | 405B | 16K H100 | FSDP + TP(8) + PP(16) |
| DeepSeek-V3 | 671B (MoE) | 2,048 H800 | TP(8) + EP(64) + PP(8) + DP |
| GPT-4 (est.) | ~1.8T (MoE) | 25K H100 | 5D: TP + PP + EP + DP + SP |

- [supported][src:megatron-core-5d-2025] Megatron-Core now supports 5D hybrid parallelism (TP + EP + Context Parallelism + DP + PP), where each dimension serves a distinct role: TP handles dense layer sharding within a node, EP routes tokens to experts across nodes, CP manages long-sequence attention, PP distributes depth across node groups, and DP enables data scaling.
- [inference] The allocation rule of thumb: place bandwidth-hungry communication (TP) within NVLink domains, latency-tolerant communication (PP, DP) across network domains, and capacity-oriented communication (EP, ZeRO) across the full cluster.

## Communication Cost at Scale

- [supported][src:jax-scaling-book-2025] Each parallelism strategy has a distinct communication fingerprint:
  - **TP**: 2×B×D bytes of AllReduce per layer, on the critical path
  - **PP**: point-to-point activation transfer, ~B×D per stage boundary
  - **FSDP/ZeRO-3**: 2×D×F bytes of AllGather + ReduceScatter per layer, overlapping with compute
  - **EP**: All-to-All for token dispatch/combine, volume proportional to expert capacity
- [inference] For a 175B-parameter model on 1,024 H100 GPUs with 400 Gbps InfiniBand: TP(8) within each node, PP(16) across node groups, and FSDP across 8 remaining DP replicas. Total per-step communication: ~800 GB for TP (inside NVLink, hidden), ~200 GB for PP (point-to-point), and ~1.5 TB for FSDP (overlapped with compute).

## Automated Parallelism Search

Manually tuning 3–5 parallelism dimensions for each model is combinatorially expensive. Automated frameworks are emerging:

- [supported][src:galvatron-auto-parallel-2025] Galvatron formulates the parallelism configuration as a constrained optimization: minimize total step time subject to per-device memory constraints, using layer-wise and phase-wise strategy optimization with runtime adaptation. This eliminates weeks of manual tuning per model/hardware combination.
- [inference] GSPMD (used in JAX/TPU training) takes a compiler-driven approach: the user annotates a few tensor dimensions, and the XLA compiler automatically derives the full sharding plan with a cost-model-driven combinatorial search. This generalizes well for Transformer architectures but is less flexible for novel architectures.

## Implications for RISC-V AI Clusters

- [inference] RISC-V AI clusters, with lower per-node compute density but potentially higher node counts, favor communication-efficient strategies: FSDP with large batch sizes (to stay compute-bound), PP to exploit the many-node topology, and EP for MoE models. TP is less favorable because RISC-V clusters typically lack NVLink-equivalent high-bandwidth intra-node fabrics.
- [inference] The scaling behavior difference between GPU and RISC-V clusters creates a parallelism strategy divergence: GPU clusters lean on TP + FSDP + PP (3D) with TP as the primary intra-node strategy; RISC-V clusters would lean on FSDP + EP + PP (3D) with EP as the primary intra-node strategy, exploiting the natural many-core topology.

## Open Questions

- OPEN: Can fully automated parallelism search (Galvatron, GSPMD) match or exceed manually tuned 3D parallelism configurations for frontier-scale models (>500B parameters)? Current evidence is limited to models under 100B.
- OPEN: As model architectures move beyond standard Transformers (Mamba, RWKV, liquid networks), do the standard parallelism dimensions still apply, or do state-space models require fundamentally different partitioning strategies?
- OPEN: What is the optimal parallelism configuration for heterogeneous clusters mixing GPU, TPU, and RISC-V devices? Current frameworks assume homogeneous hardware.

## See Also

- [[workload.ai.rvv-kernel-patterns]] — Kernel-level mapping strategies (GEMM, attention) that serve as building blocks for parallelism.
- [[workload.ai.multi-model-serving]] — Multi-model serving that parallelizes across model variants, complementing within-model parallelism.
- [[system.scale.scale-up-vs-scale-out]] — The scale-up/scale-out framework that parallelism strategies map onto.
- [[system.riscv.distributed-ai-clusters]] — RISC-V distributed clusters where parallelism strategies must adapt to different hardware topology.
- [[system.ai.distributed-inference-serving]] — Inference serving where parallelism affects prefill/decode disaggregation.
- [[software.riscv.ai-runtime-execution]] — Runtime execution that implements the per-device side of parallelism strategies.
