---
id: system.reliability.fault-tolerance-distributed-training
title: Fault Tolerance and Reliability Engineering for Distributed AI Training
status: draft
layer: 130-scale-out-distributed-system
layer_path: 130-scale-out-distributed-system/reliability/fault-tolerance-distributed-training
parent: system.riscv.distributed-ai-clusters
secondary_layers: [100-runtime-execution-system, 140-performance-cost-utilization-model]
granularity: concept
concept_type: architecture_pattern
scale_scope: [node, cluster]
reasoning_roles: [bottleneck, enabler, constraint]
tags: [fault-tolerance, checkpoint, elastic-training, resilience, peer-to-peer-recovery, straggler-mitigation]
aliases: [distributed training reliability, fault tolerance AI training, checkpoint recovery, elastic training]
sources: [aws-checkpointless-training-2025, lazarus-moe-resilient-2025, nvidia-resiliency-extension-2025]
---

# Fault Tolerance and Reliability Engineering for Distributed AI Training

## Overview

A distributed training run on 10,000+ GPUs lasting weeks will experience hundreds of failures — GPU errors, network drops, node crashes, and storage faults. Without fault tolerance, a single GPU failure kills the entire job, wasting all progress since the last checkpoint. With fault tolerance — checkpointing, peer-to-peer recovery, and elastic reconfiguration — the training run absorbs failures transparently, maintaining >90% goodput (useful compute time / wall-clock time) at cluster scales where MTTF is measured in minutes.

- [supported][src:aws-checkpointless-training-2025] AWS SageMaker HyperPod's checkpointless training achieves 80–93% recovery time reduction (from 15–30+ minutes to under 2 minutes) via peer-to-peer state replication over EFA interconnects. Failed processes recover independently without killing the entire job, preserving CUDA context, compiler cache, and GPU state. Training goodput reaches ~95% on clusters with thousands of accelerators.
- [supported][src:lazarus-moe-resilient-2025] Lazarus (2025) achieves up to 5.7× speedup over standard MoE training under frequent node failures by adaptively reallocating expert replicas and using a provably optimal expert placement algorithm. After a failure, all surviving nodes remain productive — zero GPU idle time during recovery.
- [inference] Fault tolerance is the unsung hero of large-scale AI training: without it, Meta's Llama 3 405B training (16,000 H100s, 54 days, 419 failures) would have been impossible. The physics of failure is unforgiving: MTTF scales inversely with cluster size, dropping from ~7.9 hours at 1,024 GPUs to ~14 minutes at 131,072 GPUs. At 100K GPUs, you need a checkpoint every 1.5 minutes just to keep progress loss under 5%.

## The Failure Physics

### Failure Scaling Laws

- [inference] MTTF at cluster scale is approximately MTTF_per_GPU / N, where N is the number of GPUs. With MTTF_per_GPU ~8,000 hours (typical for H100), a 16,384-GPU cluster experiences a failure every ~30 minutes. In practice, correlated failures (power events, network partitions, switch failures) make the empirical MTTF worse — Meta observed a failure every ~3 hours at 16K GPUs.
- [inference] 78% of failures are hardware-related: GPU XID/SXID errors (60%), network link flaps and InfiniBand port errors (20%), CPU/memory/disk errors (20%). The remaining 22% are software: NCCL hangs, CUDA driver errors, PyTorch framework bugs. Hardware failures are independently distributed (approximately); software failures are correlated (a NCCL hang can stall the entire job).

### Checkpointing Economics

- [inference] A training run saves checkpoints to durable storage so that on failure, execution resumes from the last checkpoint. The optimization problem: choose checkpoint interval T_c such that (T_c + MTTR) / T_c × training_time is minimized, where MTTR is the recovery time. If checkpointing takes 60 seconds and recovery takes 120 seconds, with MTTF = 30 minutes, the optimal interval is ~6 minutes — losing ~4% of training time to checkpoint overhead.
- [inference] At extreme scale (100K GPUs, 1T-parameter model), a checkpoint is ~15 TB. At 200 GB/s aggregate write bandwidth (assuming distributed checkpoint writes in parallel), saving takes ~75 seconds. With MTTF = 90 seconds, the checkpoint must complete within the MTTF window, or you're always checkpointing and never training. This is why MLPerf Storage v2.0 established checkpointing as a first-class benchmark alongside training throughput.

## Recovery Strategies

### Peer-to-Peer State Replication

- [inference] The checkpointless approach eliminates persistent storage from the recovery path: each GPU's state (model weights, optimizer states, data loader position) is replicated to K peer GPUs over the high-speed interconnect (NVLink + InfiniBand/RoCE). When a GPU fails, its peers reconstruct the lost state from their replicas and redistribute. This reduces recovery from minutes (reading checkpoint from storage) to seconds (reading from peer GPU memory over the interconnect). The cost: K× memory overhead and K× interconnect bandwidth during normal operation.

### Elastic Training

- [supported][src:nvidia-resiliency-extension-2025] NVIDIA's Resiliency Extension (NVRx v0.5.0) provides in-job restart without SLURM reallocation: hung ranks are detected (via heartbeat monitoring), terminated, and restarted within the existing allocation. The surviving ranks continue computing while the failed ranks restart. This avoids the 30–120 second overhead of SLURM job reallocation. NVRx also includes straggler detection: monitoring per-GPU performance to identify and mitigate slow ranks before they cause NCCL collective timeouts.

## Open Questions

- OPEN: Can peer-to-peer state replication scale to 100K+ GPU clusters, or does the quadratic replication overhead (K connections per GPU) become prohibitive, requiring hierarchical replication topologies?
- OPEN: As training runs extend to months (GPT-5 scale), do software failures (NCCL hangs, CUDA driver bugs) become the dominant failure mode that hardware-level fault tolerance cannot address?
- VERIFY: AWS's claim of 95% goodput with checkpointless training is vendor-provided — independent benchmarks on equivalent open-source infrastructure are not yet available.

## See Also

- [[system.riscv.distributed-ai-clusters]] — RISC-V distributed clusters where fault tolerance must be implemented from scratch.
- [[system.ai.collective-communication-algorithms]] — NCCL collectives where hung ranks cause cascading failures.
- [[workload.ai.model-parallelism-strategies]] — Model parallelism where a failed GPU affects only its partition.
- [[model.ai-datacenter-tco]] — TCO model where failure recovery overhead is a direct cost multiplier.
- [[software.gpu.runtime-execution-systems]] — GPU runtime where checkpoint and recovery coordination is managed.
- [[system.networking.rdma-smartnic-ai-cluster]] — RDMA networking where peer-to-peer recovery traffic shares the scale-out fabric.
