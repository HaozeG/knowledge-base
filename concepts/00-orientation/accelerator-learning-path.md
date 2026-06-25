---
id: stack.ai-accelerator-learning-path
title: AI Accelerator Knowledge Map — Learning Path from Hardware to Production
status: draft
layer: 00-orientation
layer_path: 00-orientation/learning/accelerator-knowledge-map
parent: stack.ai-accelerator-ontology
secondary_layers: [40-compute-substrate, 80-programming-interface-dsl, 140-performance-cost-utilization-model]
granularity: map
concept_type: architecture_pattern
scale_scope: [ecosystem]
reasoning_roles: [abstraction, enabler]
tags: [learning-path, knowledge-map, accelerator-education, hardware-to-production, stack-overview]
aliases: [AI accelerator learning path, knowledge map for accelerators, hardware-to-production learning]
sources: [ai-infra-learning-track-2025, cornell-ml-accelerators-2025, amd-ai-academy-2025]
---

# AI Accelerator Knowledge Map — Learning Path from Hardware to Production

## Overview

Understanding AI accelerators requires traversing a stack from physical limits through hardware architecture, software control, and production deployment. This concept provides a structured learning path through the knowledge base, organized by progressive depth. Each phase links to the relevant concepts in this KB.

- [inference] The AI accelerator stack has six layers: (1) physical limits and manufacturing, (2) circuit primitives and compute substrates, (3) memory, interconnect, and execution architecture, (4) programming interfaces and compilers, (5) runtime, workload mapping, and scaling systems, (6) performance modeling, supply chain, and market dynamics. Each layer builds on the layer below: you cannot understand compilers without understanding the execution architecture they target; you cannot evaluate market narratives without understanding the supply chain physics they describe.

## Learning Path

### Phase 1: Physical Foundations and Manufacturing (Layers 10–20)

Start with the physical constraints that bound all accelerator design.

1. [[physics.materials.energy-limits-beyond-cmos]] — Why Dennard scaling ended and what fundamental energy limits mean for accelerator design.
2. [[physics.materials.interconnect-scaling-limits]] — Why wires are now slower than transistors, and how this shapes architecture.
3. [[silicon.process.euv-high-na-lithography]] — How chips are manufactured and why lithography is the ultimate pacing item.
4. [[silicon.process.node-selection-fabrication-ai]] — Process node economics and the reticle limit that drives chiplet adoption.
5. [[silicon.process.advanced-packaging-ai]] — 2.5D/3D packaging as the physical enabler of scale-up.
6. [[silicon.process.3d-integration-ai]] — Hybrid bonding and vertical stacking.

### Phase 2: Compute, Memory, and Interconnect (Layers 30–70)

Understand the building blocks of an accelerator.

7. [[chip.circuit.sram-cim-ai-accelerators]] — On-chip memory circuits: SRAM and compute-in-memory.
8. [[chip.circuit.digital-ip-blocks-ai-soc]] — DMA, NoC routers, memory controllers — the digital infrastructure.
9. [[chip.circuit.serdes-io-phy-ai-chiplets]] — High-speed I/O: from chiplet D2D to rack-scale networking.
10. [[hw.compute.numerical-precision-ai]] — FP8/FP4/MX formats and why 4-bit inference is the new standard.
11. [[hw.compute.sparsity-ai-accelerators]] — Structured pruning and sparse Tensor Cores.
12. [[hw.gpu.tensor-cores]] — The matrix multiply engine that powers modern AI.
13. [[hw.gpu.on-chip-memory-hierarchy]] — Registers, shared memory, L1/L2, and TMEM.
14. [[hw.gpu.warp-scheduler-simt]] — How the GPU executes warps and hides latency.
15. [[hw.riscv.vector-extension]] — RISC-V vector processing as an alternative compute substrate.
16. [[hw.riscv.execution-architecture]] — The RISC-V execution model spectrum.
17. [[hw.riscv.power-thermal-interconnect]] — Power and thermal constraints on accelerator design.
18. [[hw.riscv.power-thermal-interconnect]] — Power and thermal constraints on accelerator design.

### Phase 3: Software Control (Layers 80–100)

Understand how programmers and compilers control the hardware.

19. [[software.control.dsl-compiler-runtime]] — The three-layer software stack: express, compile, execute.
20. [[software.control.dsl-compiler-runtime]] — The three-layer programming model for accelerators.
21. [[software.kernel.triton-language]] — Block-level GPU kernel programming.
22. [[software.compiler.ml-compiler-lowering-riscv]] — MLIR/TVM/IREE compilation for accelerators.
23. [[software.compiler.rvv-autovec-quality]] — Auto-vectorization quality and its limits.
24. [[software.compiler.power-aware-compilation]] — Compiler-directed power optimization.
25. [[software.riscv.ai-software-ecosystem]] — The RISC-V AI software stack.
26. [[software.gpu.runtime-execution-systems]] — CUDA streams, graphs, and command scheduling.
27. [[software.gpu.runtime-execution-systems]] — GPU runtime execution including memory management.
28. [[software.ai.multi-tenant-inference-scheduling]] — QoS and multi-tenant GPU scheduling.
29. [[software.interface.declarative-qos-ai-inference]] — SLO specification for AI serving.

### Phase 4: Workloads, Scaling, and Economics (Layers 110–160)

Understand how workloads map to hardware and how scaling and economics shape the industry.

30. [[workload.ai.rvv-kernel-patterns]] — GEMM, attention, and convolution mapping patterns.
31. [[workload.ai.model-parallelism-strategies]] — Tensor, pipeline, expert, and sequence parallelism.
32. [[workload.ai.multi-model-serving]] — Serving heterogeneous models at scale.
33. [[system.scale.scale-up-vs-scale-out]] — The fundamental scaling choice.
34. [[system.scale.chiplet-architecture]] — How chiplets extend scale-up beyond the reticle limit.
35. [[system.scale.nvlink-nvswitch-domain]] — NVIDIA's scale-up fabric evolution.
36. [[system.riscv.distributed-ai-clusters]] — RISC-V-based distributed computing.
37. [[system.ai.distributed-inference-serving]] — Disaggregated prefill/decode for inference.
38. [[system.ai.collective-communication-algorithms]] — AllReduce, ring, tree, and NCCL.
39. [[system.networking.rdma-smartnic-ai-cluster]] — RDMA, SmartNICs, and scale-out fabric.
40. [[programmer.roofline-model]] — The universal performance model.
41. [[model.riscv.roofline-matrix-performance]] — RISC-V-specific roofline analysis.
42. [[model.ai-datacenter-tco]] — Total cost of ownership for AI infrastructure.
43. [[model.metrics.mlperf-ai-benchmarking]] — Standardized AI accelerator benchmarking.
44. [[industry.ai.supply-chain-bottlenecks]] — CoWoS, HBM, and foundry constraints.
45. [[industry.ai.inference-as-a-service]] — The token economy and inference business models.
46. [[industry.riscv.ai-supply-chain]] — RISC-V supply chain dynamics.
47. [[market.semiconductor.ai-competitive-landscape]] — NVIDIA, AMD, and custom ASIC competition.
48. [[market.ai.cost-deflation-investment-dynamics]] — 10×/year cost decline and hyperscaler capex.
49. [[market.riscv.ai-investment-narrative]] — The investment case for RISC-V AI.

## Cross-Cutting Themes

- **The Energy-Distance-Parallelism Trilemma**: Every accelerator design is a trade-off between energy (moving data costs energy), distance (longer wires cost more energy and latency), and parallelism (more parallel units increase throughput but increase coordination cost). These three constraints recur at every level of the stack.
- **The Precision-Bandwidth-Sparsity Trade-Off**: Throughput can be increased by reducing precision (FP16→FP8→FP4), reducing data movement (better locality, fusion, tiling), or skipping computation (sparsity, MoE). All three are partially redundant and partially complementary — the optimal design uses all three.
- **Scale-Up vs. Scale-Out Throughout the Stack**: The scale-up/scale-out boundary appears at every level: on-die (monolithic vs. chiplet), on-package (HBM vs. off-package DRAM), on-node (NVLink vs. InfiniBand), and on-cluster (single datacenter vs. multi-datacenter). Each boundary represents a latency/cost/capacity trade-off.

## Open Questions

- OPEN: As the KB grows, should this learning path split into separate paths for different roles (hardware architect, compiler engineer, ML researcher, investor), or does a unified path provide irreducible cross-disciplinary value?
- OPEN: Which critical concepts are missing from this KB that would make this learning path complete? Candidates: reinforcement learning hardware, video/generative model accelerators, neuromorphic computing.

## See Also

- [[stack.ai-accelerator-ontology]] — The central ontology that organizes all concepts.
- [[stack.silicon-to-programmer]] — The silicon-to-programmer bridge concept.
- [[hw.gpu.overview]] — GPU architecture overview as a concrete instantiation of the learning path.
