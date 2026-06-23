---
id: use-case.central-ontology-placement-2026-06-23
title: Central Ontology Placement Test
status: recorded
date: 2026-06-23
harness: ontology-review
related_concepts: [stack.ai-accelerator-ontology, system.scale.scale-up-vs-scale-out, software.control.dsl-compiler-runtime, case.cerebras.wafer-scale-engine, hw.gpu.overview]
---

# Central Ontology Placement Test

## User Scenario

Question:

```text
Can the ontology organize GPU concepts, non-GPU accelerators, scale-up/out systems, and compiler/DSL/runtime concepts without collapsing everything into a GPU-centric software/hardware bucket?
```

Expected behavior:

- Product families are not top-level categories.
- GPU and Cerebras can both be placed as case branches under common patterns.
- DSL, compiler, runtime, and workload mapping are distinct.
- Scale-up and scale-out are central, not afterthoughts.
- Concepts can have one primary layer plus secondary layers.

## Placement Cases

| Example | Primary Layer | Type | Scale Scope | Reasoning Role | Result |
| --- | --- | --- | --- | --- | --- |
| Tensor Core | `40-compute-substrate` | `component` | `unit`, `tile`, `die` | `enabler` | Pass |
| GPU memory hierarchy | `50-memory-data-movement` | `memory_pattern` | `unit` to `node` | `bottleneck`, `locality_strategy` | Pass |
| Tensor Memory Accelerator | `50-memory-data-movement` | `runtime_mechanism` | `tile`, `die` | `bottleneck_mitigation` | Pass |
| SIMT | `70-execution-architecture` | `execution_model` | `tile`, `die` | `abstraction`, `mapping` | Pass |
| Thread blocks | `80-programming-interface-dsl` | `programming_interface` | `tile`, `die` | `abstraction`, `mapping` | Pass with note |
| Triton language | `80-programming-interface-dsl` | `dsl` | `tile`, `die` | `abstraction`, `mapping` | Pass as future concept |
| MLIR dialect | `90-compiler-lowering-stack` | `intermediate_representation` | `die`, `node`, `cluster` | `abstraction`, `mapping` | Pass as future concept |
| CUDA streams | `100-runtime-execution-system` | `runtime_mechanism` | `die`, `node` | `synchronization` | Pass as future concept |
| FlashAttention | `110-workload-mapping` | `kernel_algorithm` | `tile`, `die` | `locality_strategy` | Pass as future concept |
| Cerebras WSE | `120-scale-up-system` | `case_study` | `package`, `node` | `scale_up_strategy`, `locality_strategy` | Pass |
| TPU pod | `130-scale-out-distributed-system` | `case_study` | `rack`, `cluster` | `scale_out_strategy` | Pass as future concept |
| All-reduce | `130-scale-out-distributed-system` | `interconnect_pattern` | `cluster` | `synchronization`, `bottleneck` | Pass as future concept |
| Roofline | `140-performance-cost-utilization-model` | `performance_model` | `tile`, `die`, `node` | `indicator`, `bottleneck` | Pass |
| HBM bottleneck narrative | `160-market-narrative` | `market_narrative` | `ecosystem` | `claim_to_verify`, `indicator` | Pass as future concept |

## Notes On Ambiguous Cases

### Thread Blocks And Occupancy

The current page mixes two ideas:

- thread blocks as programming-interface abstraction
- occupancy as performance/utilization model

Current placement is acceptable for the MVP, but the ontology suggests a future split:

```text
software.cuda.thread-hierarchy
model.performance.gpu-occupancy
```

### Tensor Memory Accelerator

TMA touches memory hierarchy, execution architecture, runtime exposure, and workload mapping. The primary home should remain `50-memory-data-movement` because its core purpose is moving data more effectively.

### Cerebras WSE

Cerebras should not become a top-level ontology branch. It is a case study that instantiates:

```text
wafer-scale integration
scale-up system architecture
distributed on-chip memory
spatial fabric
compiler/runtime workload mapping
```

This confirms that the ontology is not GPU-limited.

## Test Answer

The ontology can now answer:

```text
How do GPU, Cerebras, and compiler/runtime concepts relate?
```

with a structured comparison:

```text
GPU:
  primary pattern: SIMT execution + Tensor Core compute + HBM hierarchy
  scaling: package/node scale-up, cluster scale-out
  software control: CUDA, libraries, compiler/runtime maturity

Cerebras:
  primary pattern: wafer-scale scale-up
  scaling: larger local compute/memory/fabric domain
  software control: compiler/runtime maps work to spatial fabric

Triton/XLA/MLIR/CUDA runtime:
  not "software misc"
  separated into programming interface, compiler lowering, runtime execution, and workload mapping
```

## Quality Evaluation

| Dimension | Score | Notes |
| --- | ---: | --- |
| Non-GPU coverage | 5/5 | Cerebras WSE fits as a case study without distorting the tree. |
| Software layering clarity | 5/5 | DSL, compiler, runtime, and workload mapping are distinct. |
| Scaling clarity | 5/5 | Scale-up and scale-out are first-class and separately testable. |
| Graph friendliness | 4/5 | `layer_path`, `parent`, `scale_scope`, and typed edges support a visual UI; viewer still missing. |
| Concept purity | 4/5 | Thread blocks and occupancy remains mixed and should split later. |
| Verification quality | 4/5 | Placement test is strong; some future examples need sources before becoming concept pages. |

Overall score: 27/30.

## Findings

- The central ontology should be pattern-first and product-neutral.
- `scale_scope` is essential; it prevents confusing on-chip bandwidth, package bandwidth, rack bandwidth, and cluster bandwidth.
- Software control needs four separate layers: DSL/API, compiler/lowering, runtime/execution, workload mapping.
- Case-study pages are the right way to include products such as Cerebras WSE, TPU pods, NVL racks, and Trainium systems.

## Next Improvements

1. Split `hw.gpu.thread-blocks-occupancy` into CUDA thread hierarchy and GPU occupancy model.
2. Add placeholder or draft concepts for Triton, MLIR, CUDA streams, FlashAttention, all-reduce, HBM bottleneck narrative.
3. Add a simple ontology linter that validates allowed `layer`, `concept_type`, `scale_scope`, and `reasoning_roles` values.
4. Build a graph viewer with layer and scale-scope filters.

