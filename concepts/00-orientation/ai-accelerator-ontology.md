---
id: stack.ai-accelerator-ontology
title: AI Accelerator Ontology
status: draft
layer: 00-orientation
layer_path: 00-orientation/ontology/ai-accelerators
parent: stack.silicon-to-programmer
secondary_layers: [40-compute-substrate, 50-memory-data-movement, 80-programming-interface-dsl, 120-scale-up-system, 130-scale-out-distributed-system]
granularity: map
concept_type: architecture_pattern
scale_scope: [ecosystem]
reasoning_roles: [abstraction, mapping]
tags: [ontology, accelerator, gpu, tpu, wafer-scale, compiler, runtime, scaling]
aliases: [accelerator ontology, AI hardware ontology]
sources: []
---

# AI Accelerator Ontology

## First-Principle Explanation

AI accelerators should be compared by stable patterns, not by product family names.

The central comparison path is:

```text
physical limits
  -> manufacturing and integration
  -> compute substrate
  -> memory and data movement
  -> interconnect, power, and thermal constraints
  -> execution architecture
  -> programming interface, compiler, and runtime
  -> workload mapping
  -> scale-up and scale-out systems
  -> performance, cost, and utilization
  -> business and market logic
```

## Why It Matters

GPU, TPU, Cerebras wafer-scale systems, Trainium, Gaudi, FPGA-based accelerators, and custom ASICs can all be placed in the same ontology. This avoids making GPU concepts the hidden default.

## Key Terms

| Term | Meaning |
| --- | --- |
| Pattern-first | Organize by mechanism before product family |
| Case study | A product or system that instantiates several patterns |
| Scale scope | The physical or operational boundary where a concept matters |
| Software control | DSL, compiler, runtime, and workload mapping layers |

## Verified Claims

- [open] This is an ontology map and does not yet make source-backed technical claims.

## Usage Questions

For any accelerator or system, ask:

```text
Where is compute?
Where is memory?
How far does data move?
How is parallelism exposed?
Who schedules work: hardware, compiler, runtime, or programmer?
What workload shape fits?
What is scaled up?
What is scaled out?
What bottleneck is reduced?
What bottleneck becomes worse?
What supply-chain constraint appears?
```

## Related Concepts

- [[hw.gpu.overview|GPU Architecture Overview]]
- [[case.cerebras.wafer-scale-engine|Cerebras Wafer-Scale Engine]]
- [[system.scale.scale-up-vs-scale-out|Scale Up vs Scale Out]]
- [[software.control.dsl-compiler-runtime|DSL, Compiler, and Runtime Separation]]

## Open Questions

- OPEN: Add TPU, Trainium, Gaudi, and FPGA case-study pages.
- OPEN: Add visual hierarchy rendering from `layer_path` and `scale_scope`.

