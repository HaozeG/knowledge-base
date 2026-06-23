---
id: system.scale.scale-up-vs-scale-out
title: Scale Up vs Scale Out
status: draft
layer: 120-scale-up-system
layer_path: 120-scale-up-system/scale-up-vs-scale-out
parent: stack.ai-accelerator-ontology
secondary_layers: [130-scale-out-distributed-system, 50-memory-data-movement, 60-interconnect-power-thermal, 140-performance-cost-utilization-model]
granularity: concept
concept_type: scaling_strategy
scale_scope: [package, node, rack, cluster, datacenter]
reasoning_roles: [scale_up_strategy, scale_out_strategy, bottleneck, mapping]
tags: [scaling, scale-up, scale-out, cluster, rack, ai-systems]
aliases: [scaling strategy]
sources: []
---

# Scale Up vs Scale Out

## First-Principle Explanation

AI systems scale by expanding a local compute domain, connecting many domains, or doing both.

```text
scale up: keep compute, memory, and communication closer
scale out: add more independent units and pay network/synchronization costs
```

Scale-up reduces some communication boundaries but usually increases manufacturing, packaging, thermal, power, or local scheduling difficulty. Scale-out increases total capacity but introduces collectives, network topology, stragglers, failures, and orchestration overhead.

## Why It Matters

Many AI industry narratives are scaling narratives:

- HBM and advanced packaging are scale-up bottlenecks.
- InfiniBand, Ethernet, NVSwitch, and collectives are scale-out bottlenecks.
- Wafer-scale systems try to move some work from scale-out into a larger local domain.
- Rack-scale accelerator systems try to create a larger local-like domain before the cluster boundary.

## Key Terms

| Term | Meaning |
| --- | --- |
| Scale-up | Increase local capacity or locality within one package, node, or tightly coupled domain |
| Scale-out | Increase capacity by connecting many nodes or racks |
| Communication boundary | Place where data movement or synchronization becomes expensive |
| Bisection bandwidth | Network bandwidth across a partition of a system |
| Collective | Distributed communication pattern such as all-reduce or all-to-all |

## Verified Claims

- [open] Add source-backed claims when specific systems are compared.

## Related Concepts

- [[case.cerebras.wafer-scale-engine|Cerebras Wafer-Scale Engine]]
- [[hw.gpu.memory-hierarchy|GPU Memory Hierarchy]]
- [[programmer.roofline-model|Roofline Performance Model]]

## Open Questions

- OPEN: Add all-reduce and all-to-all concepts under scale-out.
- OPEN: Add rack-scale accelerator system examples.

