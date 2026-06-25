---
id: software.riscv.ai-runtime-execution
title: RISC-V AI Runtime Execution for Multi-PE Matrix Accelerators
status: draft
layer: 100-runtime-execution-system
layer_path: 100-runtime-execution-system/riscv/ai-runtime
parent: software.riscv.ai-software-ecosystem
secondary_layers: [50-memory-data-movement, 60-interconnect-power-thermal, 80-programming-interface-dsl]
granularity: mechanism
concept_type: runtime_mechanism
scale_scope: [tile, die, package]
reasoning_roles: [enabler, bottleneck, mapping]
tags: [riscv, runtime, scheduler, memory-management, dispatch, multi-pe, accelerator, dma, scratchpad]
aliases: [RISC-V AI runtime, multi-PE dispatch, RISC-V accelerator runtime]
sources: [wang-das-kilo-core-arxiv-2025, medea-heterogeneous-arxiv-2025, montagna-copiftv2-arxiv-2026, burrello-multivic-arxiv-2025, tisac-evas-isca-2026, tenstorrent-metal-runtime-2026]
---

# RISC-V AI Runtime Execution for Multi-PE Matrix Accelerators

## First-Principle Explanation

A multi-PE matrix accelerator has a fundamental **dispatch problem**: given a DNN layer expressed as a graph of tensor operations, the runtime must decompose it into PE-sized tiles, assign tiles to available PEs, manage the data movement between scratchpad memories, and synchronize PE completion — all while keeping PEs busy and minimizing memory traffic.

The first-principle tension is between **static scheduling** (compiler-determined, zero runtime overhead, but brittle to dynamic conditions) and **dynamic scheduling** (runtime-adaptive, handles variable execution times, but adds dispatch latency):

```text
Static scheduling:  compiler partitions work, runtime just executes — optimal when all PEs are identical and execution times are predictable
Dynamic scheduling: runtime monitors PE states and dispatches work on-the-fly — necessary when PEs are heterogeneous, workloads have variable sparsity, or memory contention is unpredictable
```

- [supported][src:wang-das-kilo-core-arxiv-2025] A dynamic allocation scheme (DAS) for 1024-PE RISC-V clusters achieves 1.94× speedup over static allocation by remapping L1 addresses at runtime to minimize bank conflicts, with <0.1% area overhead in 12nm FinFET.
- [supported][src:montagna-copiftv2-arxiv-2026] COPIFTv2 augments the Snitch RISC-V core with lightweight queues for fine-grained integer-FP thread communication, achieving 1.49× speedup and 1.47× energy efficiency gain with peak IPC of 1.81 — directly applicable to multi-PE dispatch where control-plane latency limits utilization.
- [supported][src:burrello-multivic-arxiv-2025] MultiVic uses a central management core that orchestrates DMA transfers to local scratchpad memories following a statically determined schedule, ensuring freedom from interference in time-predictable neural network inference.

## Runtime Architecture Patterns

RISC-V multi-PE runtimes fall into three patterns based on who schedules work:

| Pattern | Scheduler | PE Model | Memory Model | Best For | Example |
|---|---|---|---|---|---|
| **Centralized static** | One management core, compile-time schedule | Homogeneous PEs | DMA to per-PE scratchpad | Time-predictable inference | MultiVic |
| **Distributed dynamic** | Per-PE work-stealing or queue-based | Homogeneous PEs | Shared L1 with bank-aware allocation | High-utilization GEMM | DAS (MemPool) |
| **Heterogeneous hybrid** | Central scheduler + per-accelerator drivers | Heterogeneous (RISC-V + NPU + CGRA) | Per-accelerator memory + shared buffer | Mixed DNN workloads | MEDEA |

### Centralized Static Dispatch (MultiVic Pattern)

- [supported][src:burrello-multivic-arxiv-2025] MultiVic's central management core pre-computes a DMA schedule: for each layer, it determines which tiles go to which PE, when DMAs should fire, and when PEs should start execution. The schedule is static but guarantees freedom from interference — no two PEs ever compete for the same memory bank simultaneously.
- [speculative][src:burrello-multivic-arxiv-2025] The static approach works well for CNNs and other feed-forward networks where execution time per layer is data-independent, but breaks down for dynamic-shape workloads (variable-length sequences in Transformers) and sparse computation where per-tile execution time varies.

### Distributed Dynamic Dispatch (DAS / MemPool Pattern)

- [supported][src:wang-das-kilo-core-arxiv-2025] DAS (Dynamic Allocation Scheme) adds a runtime-programmable address remapping hardware unit between PEs and the L1 scratchpad. When a PE requests memory, the remapper translates the logical address to a physical bank based on current load, spreading accesses to minimize bank conflicts. The remapping is reconfigured per-layer by the runtime.
- [speculative][src:wang-das-kilo-core-arxiv-2025] The key insight: static bank mapping (e.g., low-order address bits determine bank) creates hotspots when multiple PEs access the same matrix row/column. DAS's runtime remapping breaks these patterns by periodically shuffling the mapping, achieving 0.81 PE utilization on attention workloads (vs. ~0.5 for static mapping).
- [speculative] The 0.81 PE utilization is a practical upper bound for dynamic scheduling on shared-L1 clusters — the remaining 0.19 is lost to irreducible bank conflicts, DMA latency, and synchronization overhead.

### Heterogeneous Hybrid Dispatch (MEDEA Pattern)

- [speculative][src:medea-heterogeneous-arxiv-2025] MEDEA manages a heterogeneous platform (RISC-V + NMC + CGRA accelerators) by making design-time decisions about which kernel runs on which accelerator, then adapting at runtime through DVFS and memory-aware tiling. The runtime monitors energy and latency budgets per kernel and adjusts accelerator clock frequency and tile sizes accordingly.
- [speculative][src:medea-heterogeneous-arxiv-2025] The 38% energy reduction comes from avoiding the one-size-fits-all trap: running all kernels on the "fastest" accelerator wastes energy on memory-bound kernels, while running all kernels on the "most efficient" accelerator misses deadlines on compute-bound kernels.

## PE-Level Dispatch Primitives

- [supported][src:montagna-copiftv2-arxiv-2026] COPIFTv2 adds two hardware queues per Snitch core (one for integer→FP dispatch, one for FP→integer completion), enabling a producer-consumer pattern where the integer thread queues work for the FP unit and continues executing control logic. This is directly applicable to matrix PE dispatch: the control core queues a GEMM tile, the matrix accelerator executes it, and the control core prepares the next tile in parallel.
- [inference] The 1.49× speedup from COPIFTv2 demonstrates that PE-level dispatch latency is a first-order bottleneck: even with perfect scheduling, if the control core spends 40% of its time managing accelerator dispatch rather than doing useful work, PE utilization cannot exceed 60%.

## Memory Management for Multi-PE Runtimes

- [speculative] Three levels of memory management interact at runtime:
  1. **Inter-PE**: DAS-style bank-aware allocation distributes tiles across L1 banks
  2. **PE-local**: scratchpad double-buffering hides DMA latency — while PE computes on buffer A, DMA fills buffer B
  3. **Global**: DMA engines move data between L1 scratchpad, L2/L3 cache, and off-chip DRAM
- [inference] The runtime's primary memory-management task is to orchestrate these three levels so that no PE waits for data. For matrix multiply on a 256-PE cluster, this means the runtime must issue DMA transfers for the next tile before the current tile completes, requiring accurate per-tile execution-time prediction.

## Industry Context

- [speculative][src:tenstorrent-metal-runtime-2026] Tenstorrent's Metal Runtime is a bare-metal runtime for their RISC-V-based AI accelerators that handles scheduling, memory movement, and execution across a massively parallel mesh of RISC-V cores. The runtime's design reflects the industry's recognition that compiler-only scheduling is insufficient for production AI workloads — dynamic conditions (varying batch sizes, sparse activations, hardware faults) require runtime adaptation.

## Open Questions

- OPEN: What is the optimal PE-to-scheduler ratio? One scheduler per 4 PEs (Snitch cluster), per 256 PEs (MultiVic), or per-system? The answer depends on dispatch latency tolerance and workload granularity.
- OPEN: Can DAS-style runtime bank remapping be extended to multi-cluster systems with NoC interconnect? The remapping logic assumes a shared L1 crossbar; extending to mesh NoC requires distributed bank-state tracking.
- OPEN: How will matrix ISA extensions (AME/IME/VME) change the runtime dispatch model? Tile-based matrix operations have different granularity (larger tiles) than vector operations, potentially reducing dispatch frequency and making static scheduling more viable.
- VERIFY: DAS results (1.94× speedup, 0.81 PE utilization) are from simulation in 12nm; no silicon validation exists for the remapping hardware at 1024-PE scale.
- VERIFY: COPIFTv2's Snitch-based results assume 2-core clusters; scaling to 256+ core clusters may introduce queue contention not captured in the dual-core evaluation.
