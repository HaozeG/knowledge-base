---
id: software.interface.declarative-qos-ai-inference
title: Declarative QoS and SLO Specification for AI Inference
status: draft
layer: 80-programming-interface-dsl
layer_path: 80-programming-interface-dsl/inference/declarative-qos
parent: software.riscv.ai-software-ecosystem
secondary_layers: [100-runtime-execution-system, 110-workload-mapping, 150-supply-chain-business]
granularity: concept
concept_type: programming_interface
scale_scope: [node, rack, cluster]
reasoning_roles: [abstraction, mapping]
tags: [qos, slo, declarative, inference, serving, programming-interface, policy, latency, throughput, priority]
aliases: [SLO-as-code, declarative QoS for AI, inference policy language, AI serving QoS specification]
sources: [nvidia-dynamo-sla-planner-2026, kthena-qos-policy-2026, kubernetes-priority-class-2025, csdn-llm-qos-2026]
---

# Declarative QoS and SLO Specification for AI Inference

## First-Principle Explanation

Specifying "serve this model with good latency" is insufficient for production AI inference. The first-principle requirement is a machine-readable contract between the application (what latency is acceptable) and the infrastructure (what resources are available):

```text
SLO = {metric: "TTFT", target: "100ms", percentile: "P95", window: "5m", action: "scale_up"}
QoS_policy = {priority: "high", preemption: "allowed", isolation: "dedicated_sm_group", max_queue_depth: 10}
```

Without declarative QoS, every inference deployment hard-codes scheduling logic (priority queues, timeout values, retry logic) in application code. This is unmaintainable at scale — changing a latency target requires redeploying the application, and each application team reinvents the same scheduling infrastructure.

- [supported][src:nvidia-dynamo-sla-planner-2026] NVIDIA Dynamo's SLA-based planner translates declarative SLO targets (TTFT < X ms, TPOT < Y ms, throughput > Z tok/s) into autoscaling decisions: how many prefill instances, how many decode instances, what KV-cache routing policy. The planner continuously monitors SLO attainment and adjusts allocation when actual performance drifts from target.
- [supported][src:kubernetes-priority-class-2025] Kubernetes PriorityClasses provide a declarative mechanism for pod scheduling priority with preemption policy. For GPU inference: `high-priority` → guaranteed GPU allocation + preemption rights; `low-priority` → best-effort, preemptible. Kubernetes' ResourceQuotas and LimitRanges extend this to per-tenant GPU resource budgets.

## The SLO Specification Problem

### Metrics That Matter

- [inference] AI inference SLOs operate on four dimensions that general-purpose service SLOs (latency/availability) don't capture:
  1. **TTFT** (Time To First Token): user-perceived latency before seeing any output. SLO: typically 100-500ms for interactive, 1-5s for batch.
  2. **TPOT** (Time Per Output Token): the gap between consecutive tokens. SLO: typically 20-50ms (human reading speed is ~200ms/token; faster is better for responsiveness).
  3. **Throughput** (tokens/second): aggregate system capacity. SLO: "serve X requests/second with Y concurrent users."
  4. **Quality** (model variant): the model size/quantization tradeoff. SLO: "use 70B-FP16 for priority=high, 7B-FP8 for priority=low."
- [speculative] The four dimensions create a Pareto frontier: you can't optimize all four simultaneously. Higher throughput → worse TTFT (batching increases queue depth). Lower TTFT → worse quality (swap to smaller model). Higher quality → worse throughput (larger model = fewer concurrent requests per GPU). The SLO specification must express which tradeoffs are acceptable for each workload class.

### Declarative vs. Imperative QoS

- [inference] Declarative QoS ("I want P95 TTFT < 100ms") is fundamentally different from imperative QoS ("allocate 4 SMs to this request, set priority=7, install a 100ms timer"). Declarative QoS separates the what from the how — the scheduler decides how to achieve the target, and can change its strategy as conditions change (load, hardware, model version) without changing the specification.
- [speculative] The declarative approach is enabled by the maturation of autoscaling controllers (Kubernetes HPA/VPA, Dynamo SLA Planner). As long as the scheduler has a feedback loop (measure actual SLO attainment → compare to target → adjust allocation), declarative specifications are sufficient. The key enabler is fast feedback — if it takes 5 minutes to detect an SLO violation, the declarative approach fails (too slow to prevent user-facing degradation).

## Implementation Patterns

### SLO-as-Code

- [supported][src:nvidia-dynamo-sla-planner-2026] Dynamo's SLA specification is expressed as configuration (YAML/JSON), not code. An example policy:
  ```yaml
  sla:
    ttft_p95_ms: 100
    tpot_p95_ms: 30
    throughput_min_tps: 1000
  scaling:
    prefill_min: 2
    prefill_max: 8
    decode_min: 4
    decode_max: 32
  routing:
    kv_cache_affinity: prefix_hash
    load_balance_policy: shortest_queue
  ```
  The SLA Planner translates this into concrete actions: when TTFT P95 exceeds 100ms, scale up prefill instances; when throughput drops below 1000 TPS, scale up decode instances.
- [inference] The SLO-as-code pattern is architecturally identical to Infrastructure-as-Code (Terraform, Pulumi): a declarative specification of desired state, with a controller that continuously reconciles actual state toward desired state. The difference is the feedback latency — Terraform reconciliation happens in minutes (provisioning VMs), while SLO reconciliation must happen in seconds (autoscaling inference instances).

### Priority Class Hierarchy

- [supported][src:kubernetes-priority-class-2025] Kubernetes PriorityClasses map naturally to inference QoS tiers:
  - `inference-critical` (priority 1,000,000,000): real-time interactive inference, preempts everything, guaranteed GPU
  - `inference-high` (priority 100,000): latency-sensitive but not critical, may be preempted by critical
  - `inference-batch` (priority 10,000): throughput-optimized batch inference, preemptible, best-effort
  - `inference-background` (priority 0): model evaluation, A/B testing, can wait indefinitely
- [speculative] The four-tier hierarchy creates a priority ladder: background work fills idle GPU cycles, batch work takes what background doesn't use, high-priority takes what's left, and critical takes whatever it needs. This is the same priority hierarchy used in CPU scheduling (real-time → interactive → batch → background), adapted for GPU inference's coarser preemption granularity.

### Token-Bucket Rate Limiting

- [speculative] Multi-tenant inference platforms (Together AI, Baseten, Modal) use token-bucket rate limiting to enforce per-tenant quotas. Each tenant has a token bucket with a rate (tokens/second) and burst capacity (max tokens in flight). When a tenant exceeds their rate, requests are queued (not rejected) with a delay proportional to the overshoot. This provides hard multi-tenancy isolation without hard GPU partitioning — the token bucket is a software-level resource control that doesn't require MIG or hardware partitioning.

## Implications for RISC-V AI

- [speculative] Declarative QoS specifications are hardware-agnostic by design — "P95 TTFT < 100ms" doesn't care whether it's served by an H100 or a RISC-V PE cluster. This creates an opportunity for RISC-V: if the QoS specification is declarative and the scheduler is hardware-aware, RISC-V accelerators can compete purely on cost-per-SLO-attainment. The customer specifies "serve this model at this SLO at this price" and the scheduler routes to whatever hardware achieves it cheapest.
- [inference] The declarative QoS model is the technical prerequisite for a RISC-V GPU cloud marketplace: without it, each hardware type requires custom scheduling logic, creating a software barrier to entry. With declarative QoS, a new RISC-V accelerator can join the cluster, register its capabilities (max batch size, SLO-attainment profile), and immediately start serving requests — the scheduler handles the rest.

## Open Questions

- OPEN: Can declarative SLO specifications capture the full complexity of production AI inference, or will there always be edge cases requiring imperative control (e.g., "during model update, temporarily relax TTFT SLO to 500ms")?
- OPEN: What is the minimum feedback latency for effective SLO-driven autoscaling? Dynamo targets ~10s; faster feedback enables tighter SLO guarantees but adds control loop instability.
- OPEN: Will the industry converge on a standard SLO specification format (analogous to OpenAPI for REST APIs or Pulumi for infrastructure), or will each inference platform maintain its own incompatible specification?
- VERIFY: Dynamo SLA Planner is vendor-provided; independent evaluation of SLO attainment under production workloads is not available.
