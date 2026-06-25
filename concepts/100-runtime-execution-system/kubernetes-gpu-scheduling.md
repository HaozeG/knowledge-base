---
id: software.orchestration.ai-workload-scheduling-kubernetes
title: AI Workload Orchestration — Kubernetes Scheduling for GPU Clusters
status: draft
layer: 100-runtime-execution-system
layer_path: 100-runtime-execution-system/orchestration/kubernetes-gpu-scheduling
parent: stack.ai-accelerator-ontology
secondary_layers: [130-scale-out-distributed-system, 140-performance-cost-utilization-model]
granularity: concept
concept_type: runtime_mechanism
scale_scope: [node, rack, cluster]
reasoning_roles: [enabler, bottleneck, mapping]
tags: [kubernetes, gpu-scheduling, workload-orchestration, Kueue, MIG, gang-scheduling]
aliases: [Kubernetes GPU scheduling, AI workload orchestration, Kueue Volcano, gang scheduling GPU]
sources: [kueue-gpu-scheduling-2025, kubernetes-dra-gpu-2025]
---

# AI Workload Orchestration — Kubernetes Scheduling for GPU Clusters

## Overview

Training a 1,000-GPU model or serving inference on 10,000 concurrent users requires orchestrating GPU resources across hundreds of nodes. Kubernetes, the dominant container orchestration platform, has evolved from CPU-centric batch scheduling to GPU-aware workload management — but the AI workload pattern (gang scheduling, elastic scaling, multi-tenant GPU sharing) stresses Kubernetes' original design assumptions and requires extensions like Kueue, Volcano, and Dynamic Resource Allocation (DRA).

- [supported][src:kueue-gpu-scheduling-2025] Kueue (Kubernetes-native, CNCF Sandbox) implements queue-based GPU scheduling: workloads are submitted to ClusterQueues with resource quotas, and Kueue admits workloads based on priority, fairness, and resource availability. Gang scheduling ensures all pods of a distributed training job start simultaneously (every pod waits until all requested GPUs are available), avoiding partial allocations that waste GPU hours. Preemption policies allow higher-priority inference workloads to preempt lower-priority training jobs.
- [inference] The fundamental scheduling challenge for AI: training workloads require gang scheduling (all-or-nothing GPU allocation) and are long-running (hours to weeks); inference workloads require elastic scaling (add/remove GPU capacity based on request load) and are latency-sensitive (preemption causes SLO violations). A single scheduler must handle both workload classes without one starving the other — a real-time systems problem at cluster scale.

## GPU-Aware Scheduling Extensions

- [supported][src:kubernetes-dra-gpu-2025] Dynamic Resource Allocation (DRA) (Kubernetes 1.31+) enables GPU-aware scheduling: instead of the scheduler counting GPUs as scalar resources ("8 GPUs"), DRA models GPUs with attributes (model, MIG partition, NVLink topology, InfiniBand affinity). A training job requesting "8 H100 GPUs with NVLink and NDR InfiniBand on the same NUMA node" can be expressed as a DRA resource claim that the scheduler resolves to specific physical GPUs with topological constraints.
- [inference] MIG (Multi-Instance GPU) partitioning adds a sharing dimension: a single H100 can be partitioned into 7 independent GPU instances, each with dedicated compute and memory resources. The scheduler must decide whether to allocate whole GPUs to a single tenant (training) or partition GPUs across multiple tenants (inference), weighing throughput vs. utilization. Kueue's flavor-based scheduling allows cluster operators to define "whole-GPU" and "MIG-partitioned" resource flavors with different pricing and preemption policies.

## Open Questions

- OPEN: Can Kubernetes-based GPU scheduling achieve the utilization levels (80%+) that proprietary cluster managers (NVIDIA Base Command, Google Borg) achieve, or does the abstraction overhead of the Kubernetes API impose an irreducible utilization penalty for AI workloads?
- OPEN: As GPU clusters scale to 100K+ GPUs, does the centralized Kubernetes scheduler become a bottleneck that requires a hierarchical/tiered scheduling architecture?
- VERIFY: DRA's latency for GPU attribute resolution at 10K+ node scale is not yet benchmarked — the Kubernetes scheduler's scheduling throughput may limit cluster size.

## See Also

- [[stack.ai-accelerator-ontology]] — Central ontology that workload orchestration instantiates.
- [[system.riscv.distributed-ai-clusters]] — RISC-V clusters where Kubernetes scheduling must handle heterogeneous accelerators.
- [[software.ai.multi-tenant-inference-scheduling]] — Multi-tenant GPU scheduling at the per-GPU level below cluster orchestration.
- [[model.ai-datacenter-tco]] — TCO model where GPU utilization (driven by scheduling efficiency) is a dominant factor.
- [[system.ai.collective-communication-algorithms]] — NCCL collectives that gang-scheduled training jobs depend on.
- [[software.gpu.runtime-execution-systems]] — Per-GPU runtime execution that the cluster scheduler manages lifecycle for.
