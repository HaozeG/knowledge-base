---
id: stack.ai-accelerator-taxonomy-reference
title: AI Accelerator Taxonomy — Architecture, Workload, and Deployment Classification
status: draft
layer: 00-orientation
layer_path: 00-orientation/taxonomy/accelerator-classification
parent: stack.ai-accelerator-ontology
secondary_layers: [40-compute-substrate, 80-programming-interface-dsl, 160-market-narrative]
granularity: map
concept_type: architecture_pattern
scale_scope: [ecosystem]
reasoning_roles: [abstraction, enabler]
tags: [taxonomy, classification, accelerator-types, architecture-comparison]
aliases: [AI accelerator classification, accelerator taxonomy, chip architecture comparison]
sources: [accelerator-taxonomy-survey-2025]
---

# AI Accelerator Taxonomy — Architecture, Workload, and Deployment Classification

## Overview

The AI accelerator landscape spans at least six fundamentally different architectural approaches, each optimized for different points in the compute-memory-flexibility design space. This taxonomy classifies accelerators by their architectural primitives, target workloads, and deployment scale, providing a structured framework for comparing designs across vendors and generations.

- [inference] AI accelerators can be classified along three orthogonal axes: (1) compute substrate — the fundamental arithmetic unit (GPU SIMT, TPU systolic, dataflow, neuromorphic, FPGA reconfigurable, RISC-V vector); (2) memory architecture — the memory hierarchy strategy (HBM-backed cache hierarchy, SRAM-only deterministic, wafer-scale on-chip SRAM, compute-in-memory); (3) programmability — the software interface abstraction level (CUDA C++ explicit, Triton block-level, XLA graph-level, TVM auto-tuned, fixed-function).
- [inference] The taxonomy reveals why no single architecture dominates all workloads: GPUs (SIMT + HBM cache hierarchy + CUDA) excel at training due to flexibility and ecosystem; TPUs (systolic + HBM + XLA) excel at dense inference due to deterministic throughput; Groq LPUs (SIMD + SRAM-only + compiler-controlled) excel at low-latency decode; Cerebras WSE (dataflow + wafer-scale SRAM) excels at sparse and irregular workloads. The market fragments along workload lines, not vendor lines.

## Taxonomy Axes

### Compute Substrate Classification

| Class | Examples | Peak Ops/Cycle | Flexibility | Best Workload |
|---|---|---|---|---|
| SIMT (GPU) | NVIDIA H100/B200, AMD MI300X | Very high (Tensor Cores) | Very high (CUDA) | Training, general inference |
| Systolic Array | Google TPU, Amazon Trainium | Very high | Low (XLA compiler) | Dense matmul inference |
| Dataflow / CGRA | Cerebras WSE, SambaNova RDU | High | Medium (compiler-mapped) | Sparse, irregular, streaming |
| Vector (RISC-V) | Esperanto, Ventana, Tenstorrent | Medium | High (RVV, custom ISAs) | Inference, edge AI |
| FPGA Reconfigurable | Xilinx Versal, Intel Agilex | Medium-low | Highest (HDL/HLS) | Custom ops, prototyping |
| Neuromorphic | Intel Loihi, IBM NorthPole | Low (spike-based) | Low | Event-driven, sensor AI |

### Memory Architecture Classification

| Class | Examples | On-Chip Capacity | Off-Chip BW | Latency Determinism |
|---|---|---|---|---|
| HBM Cache Hierarchy | H100 (80GB HBM), B200 (192GB HBM3e) | 50-126 MB L2 per chip | 3.35-8 TB/s | Low (cache misses) |
| SRAM-Only | Groq LPU, Cerebras WSE-3 (44GB SRAM) | All on-chip | N/A (no off-chip) | Perfect (compiler-controlled) |
| CIM / PIM | d-Matrix, Untether AI, Samsung HBM-PIM | Embedded in memory | Memory-native | Medium (analog noise) |
| Near-Memory | Tenstorrent (LPDDR), edge infer chips | Small SRAM + DRAM | DDR/LPDDR rates | Low (DRAM timing) |

## Open Questions

- OPEN: Will the taxonomy converge toward 2–3 dominant classes (GPU SIMT for training, systolic for inference, SRAM-only for edge), or will workload diversity force continued architectural diversity?
- OPEN: Where do state-space models (Mamba, RWKV) and liquid networks fit in this taxonomy — do they require new architectural primitives beyond matmul and attention?

## See Also

- [[stack.ai-accelerator-ontology]] — Central ontology that this taxonomy organizes.
- [[stack.ai-accelerator-learning-path]] — Learning path through the taxonomy concepts.
- [[system.scale.scale-up-vs-scale-out]] — Scale-up/scale-out as a deployment classification axis.
- [[hw.compute.numerical-precision-ai]] — Numerical precision as a cross-cutting taxonomy dimension.
- [[market.semiconductor.ai-competitive-landscape]] — Competitive landscape organized by taxonomy classes.
- [[industry.ai.startup-landscape-consolidation]] — Startup landscape where taxonomy reveals architectural bets.
