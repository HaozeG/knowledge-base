---
id: software.control.dsl-compiler-runtime
title: DSL, Compiler, and Runtime Separation
status: draft
layer: 80-programming-interface-dsl
layer_path: 80-programming-interface-dsl/software-control-separation
parent: stack.ai-accelerator-ontology
secondary_layers: [90-compiler-lowering-stack, 100-runtime-execution-system, 110-workload-mapping]
granularity: concept
concept_type: architecture_pattern
scale_scope: [tile, die, node, cluster]
reasoning_roles: [abstraction, mapping]
tags: [software, dsl, compiler, runtime, workload-mapping]
aliases: [software control stack]
sources: []
---

# DSL, Compiler, and Runtime Separation

## First-Principle Explanation

Software controls accelerator hardware through several distinct layers:

```text
DSL or API: what can be expressed
compiler: how expression is transformed and lowered
runtime: how compiled work is launched and coordinated
workload mapping: how the model or kernel fits the machine
```

These layers should not be collapsed into one "software stack" bucket. Different AI accelerators win or lose depending on which layer hides the hardest hardware constraints.

## Why It Matters

GPU systems often rely on CUDA and library maturity. TPU systems rely heavily on graph compilation and layout decisions. Wafer-scale and spatial dataflow systems depend on mapping work onto a large fabric. Custom ASICs are only useful when the compiler/runtime can expose enough workload fit.

## Key Terms

| Term | Meaning |
| --- | --- |
| DSL | Domain-specific language or constrained programming interface |
| IR | Intermediate representation used during compiler lowering |
| Runtime | Dynamic execution and coordination layer |
| Workload mapping | Assignment of AI model operations to hardware and communication resources |

## Verified Claims

- [open] This is a conceptual separation and needs specific source-backed examples.

## Placement Examples

| Example | Primary Layer | Reason |
| --- | --- | --- |
| Triton language | `80-programming-interface-dsl` | User-facing tiled kernel DSL |
| MLIR dialect | `90-compiler-lowering-stack` | Intermediate representation for lowering |
| CUDA streams | `100-runtime-execution-system` | Runtime execution ordering and overlap |
| FlashAttention | `110-workload-mapping` | Kernel algorithm that maps attention to memory hierarchy |

## Related Concepts

- [[hw.gpu.thread-blocks-occupancy|Thread Blocks and Occupancy]]
- [[hw.gpu.tensor-memory-accelerator|Tensor Memory Accelerator]]
- [[system.scale.scale-up-vs-scale-out|Scale Up vs Scale Out]]

## Open Questions

- OPEN: Split Triton into language, compiler lowering, and autotuning/runtime concepts.
- OPEN: Add XLA, MLIR, CUDA streams, NCCL, and FlashAttention as separate concept pages.

