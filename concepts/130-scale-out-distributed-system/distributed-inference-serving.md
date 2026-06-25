---
id: system.ai.distributed-inference-serving
title: Distributed AI Inference Serving and Scheduling
status: draft
layer: 130-scale-out-distributed-system
layer_path: 130-scale-out-distributed-system/inference/distributed-serving
parent: system.riscv.distributed-ai-clusters
secondary_layers: [100-runtime-execution-system, 110-workload-mapping, 140-performance-cost-utilization-model]
granularity: concept
concept_type: scaling_strategy
scale_scope: [node, rack, cluster, datacenter]
reasoning_roles: [mapping, bottleneck, scale_out_strategy]
tags: [distributed, inference, serving, disaggregated, prefill, decode, kv-cache, scheduling, orchestration, load-balancing, ai]
aliases: [distributed inference serving, disaggregated inference, LLM serving architecture, prefill-decode disaggregation]
sources: [nvidia-dynamo-2026, kthena-cncf-2026, hexagent-arxiv-2026, prfaas-arxiv-2026, rayserve-disaggregated-2025]
---

# Distributed AI Inference Serving and Scheduling

## First-Principle Explanation

Serving an LLM at scale is a scheduling problem across two asymmetric phases. The first-principle tension is the **prefill-decode asymmetry**:

```text
Prefill:  compute-bound, processes all input tokens at once, latency matters (TTFT — time to first token)
Decode:   memory-bound, generates one token per step, throughput matters (TPS — tokens per second)

Efficient monolithic serving is impossible because:
- Prefill wants high FLOPs, low memory bandwidth — saturates compute, leaves memory idle
- Decode wants high memory bandwidth, moderate FLOPs — saturates memory, leaves compute idle
```

The solution is **disaggregated serving**: deploy separate prefill and decode clusters, each optimized for its phase, connected by a KV-cache transfer network. This is architecturally analogous to separating training (prefill-like, compute-bound) from inference (decode-like, memory-bound) at the cluster level.

- [supported][src:nvidia-dynamo-2026] NVIDIA Dynamo is an open-source datacenter-scale distributed inference framework that provides disaggregated prefill/decode, KV-aware routing, and SLA-based planner autoscaling. Reports 7× higher throughput for DeepSeek R1 on GB200 NVL72 and 2× faster TTFT via KV-aware routing.
- [supported][src:prfaas-arxiv-2026] Prefill-as-a-Service (PrfaaS) demonstrates cross-datacenter disaggregation: prefill runs on compute-dense remote clusters, KV-cache transfers over commodity Ethernet, and local PD clusters handle decode. Achieves 54% higher throughput and 64% lower P90 TTFT for 1T-parameter models.
- [supported][src:kthena-cncf-2026] Kthena (CNCF/Volcano sub-project) provides Kubernetes-native inference orchestration with topology-aware scheduling, KV-cache-aware routing, and PD disaggregation. Achieves 2.73× throughput increase and 73.5% TTFT reduction vs. random routing.

## Disaggregated Serving Architecture

### Prefill-Decode Separation

- [inference] The case for disaggregation is structural: prefill and decode have different compute/memory ratios, different latency requirements, and different scaling behaviors.
  - **Prefill** processes the entire input sequence in one forward pass. It's compute-bound (many FLOPs per token), benefits from high batch sizes (amortize weight loads), and determines TTFT. Prefill hardware: high-FLOP GPUs, high network bandwidth for KV transfer.
  - **Decode** generates one token per step autoregressively. It's memory-bandwidth-bound (reads all KV-cache, writes one token's worth), benefits from high memory bandwidth and large KV-cache capacity, and determines throughput (TPS). Decode hardware: high-memory-bandwidth GPUs, large HBM capacity.
- [speculative] The optimal prefill:decode GPU ratio depends on the input:output token ratio. For chat (short input, long output), decode dominates — 3-5× more decode GPUs than prefill GPUs. For summarization/RAG (long input, short output), prefill dominates — 2-3× more prefill GPUs. A static cluster wastes GPUs on whichever phase is underutilized; disaggregation enables independent scaling.

### KV-Cache Routing

- [supported][src:nvidia-dynamo-2026] KV-aware routing is the key enabling technology for disaggregated serving. When a prefill instance generates KV-cache, the router must decide which decode instance receives it. The routing decision is constrained by:
  1. **Cache affinity**: sending the request to a decode instance that already has relevant KV-cache (prefix caching) avoids recomputation
  2. **Load balance**: distributing requests evenly across decode instances to prevent hotspots
  3. **KV-cache capacity**: each decode instance has finite KV-cache memory; routing must respect per-instance capacity limits
- [supported][src:kthena-cncf-2026] Kthena's topology-aware scheduler maps the KV-cache transfer path onto the physical network topology, minimizing cross-rack and cross-switch transfers. This reduces KV-transfer latency by 40-60% compared to random placement in the same cluster.

### Multi-Tier KV-Cache Offloading

- [speculative] KV-cache memory is the binding constraint on decode throughput. A 70B model with 100K tokens of context requires ~35 GB of KV-cache per request — at batch size 64, that's 2.2 TB, exceeding any single GPU's HBM. Multi-tier offloading extends effective capacity:
  1. **GPU HBM** (fastest, smallest): active requests currently being decoded
  2. **CPU DRAM** (medium speed, medium capacity): recently completed requests, ready for reuse
  3. **SSD/NVMe** (slowest, largest): cold requests, swapped in when needed
  4. **Remote memory** (network-attached): cross-instance KV-cache sharing
- [inference] The multi-tier hierarchy is architecturally identical to the CPU cache hierarchy (L1→L2→L3→DRAM) but for KV-cache. The scheduling problem — which requests to keep in which tier — is a textbook cache replacement problem with the twist that KV-cache size varies per request (it's proportional to sequence length).

## Scheduling and Orchestration

### Workload-Aware Scheduling

- [supported][src:hexagent-arxiv-2026] HexAGenT models each agentic LLM request as an online-revealed DAG (the agent decides which tools to call based on previous outputs). The scheduler prioritizes requests by projected risk of missing the workflow-level SLO, jointly selecting prefill placement, decode placement, and local queue priority. Reduces SLO violations by 45% at 95% attainment and 80.5% at 99% attainment vs. request-level scheduling.
- [inference] The key insight: in agentic workflows, individual LLM calls are steps in a larger DAG. Optimizing each call independently (minimize per-call latency) can increase workflow-level latency if it causes later calls to queue behind less urgent work. Workflow-aware scheduling optimizes the end-to-end DAG completion time, not individual call latency.

### Heterogeneous Hardware Scheduling

- [speculative] Production AI clusters are increasingly heterogeneous: A100s for batch inference, H100s for interactive serving, H200s for long-context, B200s for frontier models. The scheduler must match requests to the right GPU type based on:
  - Model compatibility (not all GPUs support all model sizes)
  - Latency requirements (interactive <100ms TTFT, batch can tolerate seconds)
  - Context length (short context fits on any GPU, long context requires high-HBM GPUs)
  - Cost sensitivity (batch inference can use cheaper/older GPUs)
- [speculative] For RISC-V AI clusters, heterogeneous scheduling is both an opportunity and a challenge. RISC-V accelerators come in diverse configurations (1-1024 PEs, 128-8192-bit VLEN, with/without matrix extensions), creating a rich scheduling space. But the lack of a unified serving framework (no RISC-V equivalent of Dynamo or vLLM) means each deployment builds custom scheduling — increasing staffing cost and reducing utilization.

### Cluster-Level Load Balancing

- [inference] At cluster scale (100+ GPUs), load imbalance is the dominant utilization killer. If one decode instance is overloaded (40 requests) while another is underloaded (10 requests), the overloaded instance's latency increases for all 40 requests, while the underloaded instance's capacity is wasted. The cost of imbalance is quadratic: the slowest instance determines end-to-end latency for all requests routed to it.
- [speculative] Three load-balancing strategies, in order of sophistication:
  1. **Round-robin**: simple, stateless, but blind to load — works only when all requests have identical resource requirements (never true in practice)
  2. **Shortest-queue**: routes to the instance with fewest active requests — better than round-robin but doesn't account for request size variation
  3. **KV-aware with capacity prediction**: predicts each request's KV-cache footprint, routes to minimize imbalance while respecting cache affinity — the current state of the art (Dynamo, Kthena)

## Implications for RISC-V Distributed Inference

- [speculative] RISC-V AI clusters have a structural fit with disaggregated serving:
  - **Many small PEs map naturally to decode**: decode is embarrassingly parallel (each request is independent), and many small in-order RISC-V cores with local scratchpads can serve independent decode requests efficiently — analogous to how CDN edge nodes serve independent HTTP requests.
  - **Few large PEs map naturally to prefill**: prefill is compute-bound and benefits from wide vector units and matrix accelerators. A RISC-V cluster could deploy a few Ventana Veyron-class OoO vector cores for prefill and many Esperanto ET-Minion-class in-order cores for decode.
- [inference] The disaggregated prefill/decode pattern validates the RISC-V architectural thesis: heterogeneity is the norm, not the exception. The x86/ARM model of "one core design for everything" is economically suboptimal for AI serving — different phases need different hardware. RISC-V's open ISA enables exactly this: mix different core designs on the same SoC or across the same cluster.

## Open Questions

- OPEN: Can KV-cache transfer latency (over Ethernet/IP) be reduced below the 10ms threshold needed for interactive serving? Current cross-datacenter transfers are 50-200ms; within-rack RDMA can achieve <1ms but requires InfiniBand or RoCE. The gap between Ethernet and RDMA is the gating factor for wide-area disaggregation.
- OPEN: Is disaggregated serving economically viable for models smaller than 70B parameters? The overhead of KV-cache transfer and separate cluster management may exceed the utilization benefit for smaller models where monolithic serving already achieves >80% GPU utilization.
- OPEN: How will RISC-V matrix extensions (AME/IME/VME) change the prefill/decode hardware allocation? Matrix-extended RISC-V cores could serve both prefill and decode efficiently, reducing the case for disaggregation — or enable finer-grained disaggregation (per-PE rather than per-node).
- VERIFY: Dynamo's 7× throughput improvement is on DeepSeek R1 (MoE, 671B parameters) on GB200 NVL72 — results on dense models at smaller scale may be less dramatic.
- VERIFY: PrfaaS cross-datacenter results assume dedicated high-bandwidth inter-datacenter links; performance over shared/public internet would be substantially worse.
