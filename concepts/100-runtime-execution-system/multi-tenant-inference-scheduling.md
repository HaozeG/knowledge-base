---
id: software.ai.multi-tenant-inference-scheduling
title: Multi-Tenant GPU Scheduling and QoS for AI Inference
status: draft
layer: 100-runtime-execution-system
layer_path: 100-runtime-execution-system/inference/multi-tenant-scheduling
parent: software.riscv.ai-runtime-execution
secondary_layers: [110-workload-mapping, 130-scale-out-distributed-system, 150-supply-chain-business]
granularity: mechanism
concept_type: runtime_mechanism
scale_scope: [node, rack, cluster]
reasoning_roles: [bottleneck, mapping]
tags: [runtime, scheduling, multi-tenant, gpu, qos, slo, priority-inversion, preemption, interference, inference, ai]
aliases: [multi-tenant GPU scheduling, inference QoS, priority-aware GPU scheduling, SLO-driven inference runtime]
sources: [daris-ieee-2025, driftsched-arxiv-2026, sysart-gpu-qos-2025, csdn-llm-qos-2026, zhao-interference-acm-2025]
---

# Multi-Tenant GPU Scheduling and QoS for AI Inference

## First-Principle Explanation

A GPU serving multiple tenants is a shared resource with no built-in fairness. The first-principle scheduling problem is **priority inversion by co-location interference**:

```text
Without QoS:
  High-priority request A (TTFT < 100ms) dispatched → GPU busy with low-priority batch B (1000 tokens, 500ms remaining)
  A waits 500ms → TTFT = 500ms (5× SLO violation)
  Cause: the GPU has no notion of priority — it executes whatever is loaded, in order

With QoS:
  High-priority request A arrives → scheduler preempts low-priority batch B → loads A → executes A → TTFT = 80ms
  Batch B resumes → total latency increase for B = 80ms (acceptable for batch workload)
  Mechanism: preemption with state preservation (KV-cache checkpoint, weight reload if needed)
```

The organizer's insight: **the GPU is a shared resource with coarse-grained preemption (seconds, not microseconds) and no hardware priority queues**. This makes it fundamentally different from CPU scheduling (microsecond preemption, hardware priority registers). GPU scheduling is closer to OS process scheduling in the 1960s — before hardware support for preemptive multitasking existed.

- [supported][src:daris-ieee-2025] DARIS demonstrates priority-based real-time DNN scheduling through spatio-temporal partitioning: high-priority tasks get dedicated SM groups and preemption slots, achieving 100% deadline satisfaction for high-priority tasks and <2% deadline miss rate for low-priority tasks. High-priority response times are 33% better than low-priority.
- [supported][src:driftsched-arxiv-2026] DriftSched addresses runtime token drift — observed output lengths deviating from admission-time estimates — which causes workload misclassification and queue imbalance. SJF scheduling reduces median latency by ~42% and P99 by ~16% vs. FIFO under sustained contention. Adaptive bias correction reduces estimation error by ~39-41%.
- [supported][src:csdn-llm-qos-2026] A production QoS system using dynamic priority scoring (tenant class × model complexity × latency sensitivity) achieved 57% reduction in P95 latency for high-priority tasks and SLA hit rate improvement from 88.3% to 99.1%.

## The Multi-Tenant Scheduling Problem

### Co-location Interference

- [supported][src:zhao-interference-acm-2025] GPU co-location interference can cause kernel execution time to reach **151.66% of profiled values** at P95. The root cause: static interference prediction models degrade under changing workloads because a batch may co-locate with different batches over its lifetime, and each co-location pair has different interference characteristics.
- [inference] Co-location interference is the GPU equivalent of CPU cache thrashing — but worse, because GPU context switches are 100-1000× more expensive (reloading model weights, rebuilding KV-cache). A CPU can context-switch in microseconds; a GPU serving a 70B model takes seconds to swap model weights. This asymmetry makes traditional OS scheduling techniques (time-slicing, priority queues) inapplicable without modification.

### Priority Inversion Patterns

- [speculative] Three priority inversion patterns in GPU inference:
  1. **Batch-length inversion**: a low-priority request with 2000 output tokens blocks a high-priority request with 50 output tokens. The long request isn't more important — it's just longer. SJF (Shortest Job First) scheduling mitigates this but starves long requests.
  2. **Prefill-decode inversion**: a low-priority prefill (compute-bound, 500ms) blocks a high-priority decode step (memory-bound, 20ms). The prefill isn't lower priority — it's just in the GPU first. Disaggregated prefill/decode eliminates this by separating the two phases onto different GPUs.
  3. **Model-switching inversion**: a low-priority request using a small model blocks a high-priority request using a large model, because unloading/reloading model weights takes seconds. LoRA-based serving mitigates this (swap only adapter weights, not base model) but doesn't help when different base models are involved.
- [inference] The three patterns share a common cause: the GPU's scheduling granularity is determined by the largest uninterruptible unit of work (a full forward pass), which can be 100ms-2s for LLM inference. This is 10³-10⁴× coarser than CPU scheduling quanta (100µs-10ms), making preemption proportionally more expensive.

## Scheduling Techniques

### Spatio-Temporal Partitioning

- [supported][src:daris-ieee-2025] DARIS combines spatial partitioning (dedicated SM groups per priority class) with temporal staging (preemption slots between batches). The spatial component ensures high-priority requests always have reserved compute; the temporal component ensures they don't wait for a long batch to complete. The oversubscription technique (allocating more work than the GPU can strictly handle) improves utilization while maintaining priority guarantees.
- [speculative] For RISC-V multi-PE systems, spatio-temporal partitioning maps naturally: dedicate PEs to priority classes (spatial) and use the runtime dispatcher to preempt low-priority work at PE boundaries (temporal). The advantage over GPU: RISC-V PEs are smaller and more numerous, enabling finer-grained spatial partitioning (dedicate 4 of 256 PEs to high-priority rather than 20 of 132 SMs).

### Token-Drift-Aware Scheduling

- [supported][src:driftsched-arxiv-2026] DriftSched's key contribution: recognizing that LLM output length estimates at admission time are systematically wrong (models generate variable-length outputs). A request admitted as "short" (50 tokens) may generate 200 tokens, becoming a "long" request mid-execution. This token drift causes the request to be in the wrong scheduling class, degrading QoS for genuinely short requests.
- [inference] The token drift problem is isomorphic to CPU branch prediction: the scheduler makes decisions based on predicted future behavior, and mispredictions are costly. Adaptive bias correction (DriftSched's 39-41% error reduction) is the GPU equivalent of a better branch predictor — it reduces the cost of misprediction without eliminating prediction entirely.

### Preemption Mechanisms

- [speculative][src:sysart-gpu-qos-2025] Three GPU preemption mechanisms, in order of increasing cost:
  1. **KV-cache checkpoint**: save the current request's KV-cache to CPU memory, preempt the GPU, restore KV-cache later. Cost: tens of milliseconds (KV-cache size × PCIe bandwidth). Works only when model weights stay loaded.
  2. **Batch boundary preemption**: wait for the current batch iteration to complete (typically 20-50ms for decode), then preempt before the next iteration starts. Cost: zero additional latency beyond the current iteration. The simplest and most common approach.
  3. **Full context switch**: save KV-cache AND unload model weights, load new model, restore new request's KV-cache. Cost: seconds to tens of seconds (model size × PCIe bandwidth). Used only for model switching, not priority preemption.
- [inference] The practical implication: priority preemption in GPU inference is viable only at batch boundaries (20-50ms granularity). This is acceptable for interactive serving (TTFT SLOs of 100-500ms) but insufficient for hard real-time (sub-millisecond SLOs). GPU inference cannot serve hard-real-time workloads — a fundamental limitation of the architecture.

## QoS Architecture

- [supported][src:csdn-llm-qos-2026] A production multi-tenant QoS system has four components:
  1. **Priority scoring**: dynamic priority = f(tenant_class, model_complexity, latency_sensitivity, task_type). Recalculated per-request.
  2. **Resource scoring**: each GPU replica scored on utilization, memory pressure, queue depth, and historical P95 latency penalty. Requests routed to the replica with the best score for their priority class.
  3. **SLA risk scoring**: predicted probability of missing SLO given current queue depth and request characteristics. High-risk requests get priority boost or are rejected early (HTTP 429) rather than queued and timed out.
  4. **Cold/hot path failover**: if the primary GPU replica is overloaded, requests are routed to a hot standby or cold-started on an idle GPU.
- [inference] The four-component architecture mirrors TCP congestion control: priority scoring = packet classification, resource scoring = path selection, SLA risk scoring = congestion window, failover = retransmission. The analogy is not superficial — both systems manage shared resources (network links / GPUs) with heterogeneous traffic (video/voice/data / high/low priority inference) under SLO constraints (latency / TTFT).

## Implications for RISC-V AI Runtimes

- [speculative] RISC-V multi-PE runtimes have structural advantages for multi-tenant scheduling:
  1. **Finer preemption granularity**: RISC-V PEs complete individual tiles (microseconds) rather than full forward passes (milliseconds to seconds). Preemption at tile boundaries reduces worst-case blocking time by 10³-10⁴×.
  2. **Spatial isolation by construction**: PE clusters with private scratchpads are naturally isolated — a noisy neighbor on PE cluster A doesn't affect PE cluster B's memory bandwidth. GPU SMs share L2 cache and memory bandwidth, making isolation harder.
  3. **No model-weight-switching penalty**: small RISC-V PEs serving small models or LoRA adapters can keep weights in local scratchpad permanently. Switching between models is a pointer change, not a weight reload.
- [inference] The RISC-V multi-tenant scheduling thesis: many small PEs with local scratchpads provide hardware-enforced isolation that software QoS systems on GPUs must emulate through complex preemption and partitioning logic. The hardware simplicity of RISC-V PEs is a QoS advantage, not a limitation.

## Open Questions

- OPEN: Can GPU preemption granularity be reduced below batch boundaries (20-50ms)? Mid-iteration preemption would require saving partial KV-cache and partial attention state — theoretically possible but no production implementation exists.
- OPEN: What is the optimal spatial partitioning for multi-tenant RISC-V clusters? Dedicating PEs to priority classes wastes capacity when high-priority load is low; dynamic repartitioning adds scheduling overhead. The tradeoff depends on workload variance.
- OPEN: Can token-drift prediction be improved beyond DriftSched's 39-41% error reduction? The fundamental limit is the inherent unpredictability of LLM output lengths — no predictor can be perfect when the generating process is stochastic.
- VERIFY: DARIS results are from an IEEE conference paper; the <2% deadline miss rate for low-priority tasks is under specific workload assumptions (fixed DNN models, known execution times). LLM inference with variable output lengths would likely show higher miss rates.
- VERIFY: The production QoS system (CSDN blog) achieving 99.1% SLA hit rate is from a single deployment; generalizability to different GPU types and workload mixes is unverified.
