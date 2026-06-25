---
id: workload.ai.multi-model-serving
title: Multi-Model Inference Serving and Workload Composition
status: draft
layer: 110-workload-mapping
layer_path: 110-workload-mapping/inference/multi-model-serving
parent: workload.ai.rvv-kernel-patterns
secondary_layers: [100-runtime-execution-system, 130-scale-out-distributed-system, 140-performance-cost-utilization-model]
granularity: concept
concept_type: kernel_algorithm
scale_scope: [node, rack, cluster]
reasoning_roles: [mapping, bottleneck]
tags: [inference, serving, multi-model, batching, scheduling, heterogeneous, lora, agentic, workload, ai]
aliases: [multi-model inference, LLM serving patterns, heterogeneous batching, inference workload scheduling]
sources: [bucketserve-ieee-2025, routebalance-arxiv-2026, lorax-predibase-2026, plaserve-mlsys-2026, dyorc-acm-socc-2025, lodestar-arxiv-2026]
---

# Multi-Model Inference Serving and Workload Composition

## First-Principle Explanation

Production AI inference is not one model on one GPU — it is dozens of models, hundreds of fine-tuned variants, serving thousands of concurrent requests with different latency requirements, context lengths, and cost budgets. The first-principle scheduling problem is:

```text
throughput_loss = fraction of GPU cycles wasted on:
  1. Padding overhead:  requests in a batch with different sequence lengths waste compute on padding tokens
  2. Model switching:    loading/unloading model weights between different models
  3. KV-cache imbalance: requests with different context lengths create uneven memory pressure
  4. Priority inversion:  batch requests with urgent latency requirements wait behind batch-friendly requests

optimal_schedule = minimize Σ(throughput_loss) subject to per-request SLO constraints
```

The organizer's insight: **naive batching can waste 40-60% of GPU compute**. Bucket-based batching, priority-aware scheduling, and heterogeneous continuous batching recover most of this waste — but each optimization adds scheduling complexity.

- [supported][src:bucketserve-ieee-2025] BucketServe groups requests into buckets of homogeneous sequence lengths, eliminating padding overhead within each bucket. Adaptive bucket splitting/merging and priority-aware scheduling achieve 3.58× throughput improvement over UELLM and handle 1.93× more load under SLO attainment vs. DistServe.
- [supported][src:routebalance-arxiv-2026] RouteBalance jointly optimizes model routing and load balancing across heterogeneous GPU clusters (13 instances, 28 GPUs, 4 model sizes). Batched in-process predictor achieves 2.6-4.1× throughput improvement at high load. The key insight: pricing latency at model-selection time yields the main benefit — routing decisions made before the request is dispatched to a specific model instance.
- [supported][src:lorax-predibase-2026] LoRAX demonstrates heterogeneous continuous batching: packing requests targeting different LoRA adapters into the same batch, with adapter exchange scheduling (async prefetch/offload between GPU/CPU). Scales to 1,000+ fine-tuned models on a single GPU.

## Batching Strategies

### Continuous Batching

- [inference] Continuous batching (also called iteration-level scheduling) is the baseline for modern LLM serving. Unlike static batching (wait for a full batch before processing), continuous batching adds/removes requests at each iteration boundary. This eliminates the batching latency vs. throughput tradeoff — new requests join the next iteration without waiting for the current batch to complete.
- [speculative] The remaining inefficiency in continuous batching is padding: when requests in a batch have different sequence lengths (prefill) or generate different numbers of tokens (decode), the shorter requests waste compute on padding tokens. The padding overhead is proportional to the variance in request lengths — high variance (mix of short chat and long document summarization) means high padding waste.

### Bucket-Based Batching

- [supported][src:bucketserve-ieee-2025] BucketServe addresses padding overhead by grouping requests into buckets of homogeneous sequence lengths. Each bucket processes as a separate batch with minimal padding. Adaptive bucket splitting/merging handles the dynamic case: when a bucket grows too large (causing OOM risk), it splits; when two buckets shrink, they merge. This achieves near-zero padding overhead at the cost of reduced batch size per bucket (fewer requests in each homogeneous group).
- [speculative] The bucket approach is analogous to memory allocator design (slab allocation): fixed-size buckets eliminate fragmentation but reduce utilization if request sizes don't match bucket sizes. The optimal number of buckets depends on the request length distribution — too few buckets wastes compute on padding, too many buckets wastes GPU on small batch sizes.

### Prefill-Length-Aware Batching

- [supported][src:plaserve-mlsys-2026] PLA-Serve disaggregates long-prefill and short-prefill requests into separate queues with length-aware batching. Long-prefill requests (documents, RAG context) are compute-bound and benefit from high batch sizes; short-prefill requests (chat messages) are latency-sensitive and need fast turnaround. The dual-queue design reduces prefill latency >30% vs. vanilla SGLang and improves throughput 35% under high concurrency.
- [inference] The length-aware approach recovers the intuition that prefill is NOT one workload — it's a bimodal distribution of short-interactive and long-batch requests that have fundamentally different optimization goals.

## Heterogeneous Model Serving

### Multi-LoRA Serving

- [supported][src:lorax-predibase-2026] LoRAX supports 1,000+ fine-tuned model variants on a single GPU through two mechanisms:
  1. **Heterogeneous continuous batching**: requests targeting different LoRA adapters are packed into the same batch. Each request applies its own adapter weights (small matrices, typically 0.1-1% of base model size) to the shared base model activations.
  2. **Adapter exchange scheduling**: adapters are asynchronously prefetched from CPU to GPU before their requests are scheduled, and offloaded after completion. The scheduler predicts which adapters will be needed next and pipelines the transfer with computation.
- [speculative] Multi-LoRA serving is economically transformative: a single GPU that previously served one model can now serve 1,000 fine-tuned variants at near-identical throughput. The GPU utilization ceiling is now determined by adapter I/O bandwidth (CPU↔GPU transfer) and KV-cache capacity, not compute throughput.

### Multi-Model Routing

- [supported][src:routebalance-arxiv-2026] RouteBalance's key contribution is fusing model selection (which model variant to use for this request) with load balancing (which GPU instance to route to). The batched predictor stack takes ~32ms per decision at 12 req/s — fast enough for online serving. Pricing latency at model-selection time (choosing a smaller/cheaper model when queue depth is high) provides the majority of the throughput benefit.
- [inference] The fused routing approach mirrors the compiler optimization of "code generation combined with register allocation" — separating the two decisions (first pick model, then find GPU) produces locally optimal but globally suboptimal assignments. Joint optimization finds assignments where both dimensions align.

## Workload Composition Patterns

### Agentic Workloads

- [inference] Agentic AI workloads (where an LLM plans, calls tools, reflects, and iterates) create bursty, DAG-structured request patterns that break traditional Poisson arrival assumptions. A single user query may spawn 5-50 LLM calls with dependencies (tool output feeds into the next reasoning step). The scheduler must reason about the DAG, not individual requests.
- [speculative] The agentic workload pattern favors heterogeneous hardware: cheap/fast models for planning (routing to small GPUs or even CPU inference), powerful models for reasoning (routing to large GPUs), and specialized models for tool-specific tasks (code generation, search summarization). This is the workload pattern that heterogeneous RISC-V clusters are best suited for — each model variant can run on the RISC-V PE configuration optimized for its compute/memory profile.

### Dynamic Workflow Composition

- [supported][src:dyorc-acm-socc-2025] DyOrc handles dynamic ML workflows where model components are conditionally activated based on intermediate results. Speculative scheduling pre-loads components predicted to be needed; multi-tier message passing uses shared memory for co-located components and RDMA for remote ones; proactive component loading reduces cold-start latency. Achieves 4-198% latency improvement over Ray Serve and Triton.
- [inference] The trend from static model serving (one model, one GPU, fixed pipeline) toward dynamic workflow composition (many models, many GPUs, conditional activation) increases scheduling complexity but also increases the value of intelligent scheduling — the gap between naive and optimal grows with workflow complexity.

## Implications for RISC-V Workload Mapping

- [speculative] RISC-V's architectural diversity (1-1024 PEs, in-order to OoO, RVV to matrix extensions) maps naturally to heterogeneous multi-model serving:
  - **Tiny models** (routing, classification): single in-order RVV core, <1W
  - **LoRA adapters**: small in-order PE cluster with shared L1, batch-optimized
  - **Base model decode**: many small PEs with local scratchpad, memory-bandwidth-optimized
  - **Base model prefill**: wide OoO vector core or matrix-extended PE, compute-optimized
- [inference] The RISC-V heterogeneous serving thesis: one RISC-V SoC with mixed PE types can serve the full model hierarchy that currently requires 3-4 different GPU types. The economic advantage is not peak throughput but utilization — matching hardware to workload reduces idle GPU cycles.

## Open Questions

- OPEN: What is the optimal number of bucket sizes for production LLM workloads? Too few buckets wastes compute on padding; too many buckets wastes GPU on small batch size. The answer is workload-dependent and no general solution exists.
- OPEN: Can multi-LoRA serving (1,000+ adapters on one GPU) be extended to full model variants (different base models on one GPU)? The weight difference is 100-1000× larger, exceeding practical CPU↔GPU transfer bandwidth.
- OPEN: Does agentic workload scheduling benefit from hardware-level support (priority queues in the PE dispatch unit) or is software-level scheduling (DAG-aware router) sufficient? COPIFTv2-style hardware queues suggest hardware support could reduce dispatch overhead, but no integrated system exists.
- VERIFY: BucketServe 3.58× throughput is against UELLM baseline on specific workload traces; results on production traces with different length distributions may vary significantly.
- VERIFY: LoRAX 1,000+ adapter support assumes LoRA rank ≤ 64 and base model ≤ 13B parameters; scaling to larger base models or higher-rank adapters may hit GPU memory limits.
