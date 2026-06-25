---
id: hw.riscv.noc-interconnect-matrix-accelerators
title: NoC and Interconnect for Multi-PE RISC-V Matrix Accelerators
status: draft
layer: 60-interconnect-power-thermal
layer_path: 60-interconnect-power-thermal/riscv/noc-matrix-accelerators
parent: hw.riscv.multi-pe-matrix-microarchitecture
secondary_layers: [40-compute-substrate, 50-memory-data-movement, 70-execution-architecture]
granularity: mechanism
concept_type: interconnect_pattern
scale_scope: [tile, die, package]
reasoning_roles: [bottleneck, enabler]
tags: [riscv, noc, interconnect, mesh, hierarchical, mempool, floonoc, multi-pe, matrix-accelerator, synchronization, scaling]
aliases: [RISC-V matrix accelerator interconnect, NoC for matrix PEs, PE interconnect fabric]
sources: [riedel-floonoc-ieee-tvlsi-2025, iguaz-fractalsync-acm-cf-2025, riedel-mempool-flavors-arxiv-2025, shen-mempool-spatz-date-2025, rozk-reconfigurable-noc-ieee-jssc-2026]
---

# NoC and Interconnect for Multi-PE RISC-V Matrix Accelerators

## First-Principle Explanation

A multi-PE matrix accelerator is only as fast as the data supply to its PEs. For a grid of P computing elements each capable of M MACs/cycle, the aggregate compute throughput is P × M, but realized throughput is gated by:

```text
utilization = min(data_bandwidth / (P × M × bytes_per_op), 1)
```

The interconnect fabric between PEs is the physical realization of data_bandwidth. The first-principle constraint is a **fan-out problem**: each PE needs operands, and each operand may come from memory, a neighbor PE, or a shared buffer. The interconnect must deliver these operands without serializing the PEs.

The design space is shaped by three forces:
- **Latency**: time from operand request to delivery; determines minimum tile size for efficient execution
- **Bandwidth**: aggregate bytes/cycle across all links; determines maximum sustainable PE count
- **Area/power overhead**: interconnect cost grows with link count and topology complexity; must not dominate PE area

- [supported][src:riedel-floonoc-ieee-tvlsi-2025] FlooNoC achieves 645 Gb/s/link with 0.15 pJ/B/hop in 12nm FinFET, at only 3.5% area overhead per tile in an 8×4 mesh of RISC-V cluster tiles (288 cores total, 103 Tb/s aggregate bandwidth).
- [supported][src:riedel-mempool-flavors-arxiv-2025] MemPool's hierarchical shared-L1 interconnect achieves 1/3/5 cycle latency (tile/group/cluster level) for up to 1024 PEs in GF 12nm, enabling >96% core utilization on signal processing kernels.
- [supported][src:iguaz-fractalsync-acm-cf-2025] MAGIA's 2D mesh FlooNoC connecting RISC-V + RedMulE matrix accelerator tiles achieves 43× speedup on barrier synchronization vs. software atomics, with <0.01% area overhead for the synchronization hardware.

## Interconnect Topologies for Multi-PE Matrix Accelerators

RISC-V multi-PE systems use three broad interconnect strategies, ordered by coupling tightness:

| Topology | Latency | Bandwidth Scaling | Area Overhead | Max PEs Demonstrated | Best For |
|---|---|---|---|---|---|
| **Hierarchical shared-L1** (MemPool) | 1–5 cycles | O(N banks) crossbar, saturates at ~1024 PEs | ~10% of tile | 1024 (MemPool), 256 (Spatz cluster) | Irregular kernels, fine-grained sharing |
| **2D mesh NoC** (FlooNoC/MAGIA) | O(√N) hops | O(√N) bisection | 3.5% per tile | 256 (MAGIA 16×16), 288 (FlooNoC 8×4) | Regular dataflow, scalable GEMM |
| **Reconfigurable NoC** (ROZK) | Configurable per dataflow | Stationary-dependent | Higher (configurable switches) | 16 PEs (4×4) | Mixed-precision DNN, sparse patterns |

### Hierarchical Shared-L1 (MemPool Pattern)

The hierarchical shared-L1 pattern is the tightest coupling: all PEs share a single multi-banked L1 scratchpad through a low-latency interconnect tree.

- [supported][src:riedel-mempool-flavors-arxiv-2025] Baseline MemPool organizes 256 Snitch cores into tiles of 4 cores each, groups of 4 tiles, and a cluster of 4 groups (16 tiles total), with interconnect latency of 1 cycle within a tile, 3 cycles within a group, and 5 cycles across the cluster.
- [speculative][src:riedel-mempool-flavors-arxiv-2025] The hierarchical interconnect is the key enabler of MemPool's programmability: any PE can access any L1 bank in at most 5 cycles, eliminating the need for explicit DMA programming or software-managed data distribution.
- [speculative][src:shen-mempool-spatz-date-2025] TCDM burst access extends the shared-L1 pattern to 1024 FPUs (MemPool-Spatz) by allowing a PE to request multiple consecutive words in a single transaction, reducing arbitration overhead by 3.26× on memory-bound kernels.

The shared-L1 pattern's limitation is bandwidth saturation: as PE count grows, the probability of bank conflicts increases. For matrix multiply, this means tiling strategy must account for L1 bank mapping to avoid stride-induced conflicts.

### 2D Mesh NoC (FlooNoC / MAGIA Pattern)

The 2D mesh NoC pattern decouples PE clusters into independent tiles connected by a packet-switched mesh. Each tile has its own local memory (scratchpad + DMA), and tiles communicate via router-to-router hops.

- [supported][src:riedel-floonoc-ieee-tvlsi-2025] FlooNoC uses wide physical links (512-bit data + control), AXI4-compatible end-to-end protocol, and source-routed packets with credit-based flow control. At 1 GHz in 12nm, it sustains 645 Gb/s per link.
- [supported][src:iguaz-fractalsync-acm-cf-2025] MAGIA tiles each contain a RISC-V cv32e40x control core, RedMulE matrix accelerator (24×8 semi-systolic array), 1 MiB L1 SPM, and iDMA engine, all connected to a FlooNoC router. The mesh scales from 2×2 to 16×16 tiles (256 PEs).
- [speculative][src:iguaz-fractalsync-acm-cf-2025] The RedMulE accelerator within each MAGIA tile is a 24×8 semi-systolic array optimized for GEMM — the NoC's role is to distribute input tiles and collect output tiles, not to participate in the inner MAC loop. This separation (NoC for coarse-grained data movement, local PE array for fine-grained compute) is the key architectural insight enabling linear scaling to 256 tiles.

The mesh NoC's advantage is scalability: adding tiles adds routers and links proportionally, keeping per-tile bandwidth roughly constant. The disadvantage is higher latency for non-neighbor communication (up to √(2N) hops across the mesh).

### Reconfigurable NoC (ROZK Pattern)

The reconfigurable NoC pattern allows the interconnect topology to change per dataflow (weight-stationary, input-stationary, output-stationary), optimizing data movement for each layer of a DNN.

- [speculative][src:rozk-reconfigurable-noc-ieee-jssc-2026] ROZK's reconfigurable NoC supports tri-stationary dataflow by reconfiguring switch connections between PEs — for a convolutional layer, weights can be stationary in PEs while activations flow through; for a fully-connected layer, the NoC reconfigures for output-stationary dataflow.
- [speculative][src:rozk-reconfigurable-noc-ieee-jssc-2026] At 409 MHz in 28nm, ROZK achieves 191 GOPS (0% sparsity) and 324 GOPS (60% sparsity) with a 64-bit RISC-V host core. The reconfigurable NoC adds area overhead but enables zero-skipping by gating inactive PEs.

## Synchronization at Scale

As PE count grows, synchronization overhead becomes a first-order performance limiter. In a bulk-synchronous parallel (BSP) execution model, every matrix tile operation requires a barrier before the next tile can begin.

- [supported][src:iguaz-fractalsync-acm-cf-2025] FractalSync achieves 43× speedup over software atomic-based barriers by using a hierarchical hardware barrier tree: PEs within a tile synchronize locally (1 cycle), tiles within a group synchronize via dedicated barrier links (2–3 cycles), and groups synchronize at the cluster level (4–5 cycles). Total barrier latency for 256 PEs is 5 cycles.
- [speculative][src:iguaz-fractalsync-acm-cf-2025] The fractal synchronization pattern maps naturally to the mesh topology: each router in the FlooNoC mesh aggregates barrier signals from its subtree, reducing the global barrier to O(log N) instead of O(N) latency. The <0.01% area overhead makes it practical to include in every tile.

Without hardware barrier support, multi-PE matrix accelerators waste an increasing fraction of cycles on synchronization as PE count scales — a 256-PE software barrier can take hundreds of cycles, erasing the throughput gains from adding PEs.

## PE-to-Accelerator Communication Patterns

In heterogeneous multi-PE systems (RISC-V control core + matrix accelerator per tile), the interconnect must handle two communication classes:

- [inference] **Control-plane communication**: RISC-V cores issue commands to accelerators, read status registers, and handle exceptions. This is low-bandwidth, latency-sensitive traffic — the control core should not wait hundreds of cycles for accelerator response.
- [inference] **Data-plane communication**: Accelerators read/write matrix tiles to/from scratchpad memories and DMA engines. This is high-bandwidth, throughput-sensitive traffic — the interconnect must sustain full accelerator throughput without stalling.
- [speculative][src:riedel-mempool-flavors-arxiv-2025] In Vectorial MemPool (Spatz flavor), the Snitch scalar core and Spatz vector unit share the same L1 interconnect port. For vectorized kernels with 94% Spatz utilization, the scalar core's memory traffic is negligible, so the shared port is not a bottleneck. For mixed scalar/vector workloads, contention at the L1 port can reduce utilization.

## Scaling Limits and Bottlenecks

- [inference] From published data, three scaling regimes emerge:
  1. **< 64 PEs**: Shared-L1 hierarchical interconnect (MemPool) provides the lowest latency and highest utilization. Bank conflicts are manageable with 16+ L1 banks.
  2. **64–256 PEs**: 2D mesh NoC (FlooNoC/MAGIA) overtakes shared-L1 in aggregate bandwidth. Hierarchical barriers (FractalSync) become necessary to maintain utilization above 80%.
  3. **> 256 PEs**: Multi-cluster architectures with inter-cluster NoC (FlooNoC between MemPool clusters) are required. The bottleneck shifts from PE-to-memory bandwidth to inter-cluster synchronization latency.
- [speculative][src:shen-mempool-spatz-date-2025] The 1024-FPU MemPool-Spatz configuration uses TCDM burst access to push the shared-L1 bottleneck beyond 256 PEs, but the crossbar arbitration logic grows as O(N²) with PE count, suggesting a practical limit around 1024 PEs for shared-L1 without hierarchical decomposition.
- [speculative][src:riedel-floonoc-ieee-tvlsi-2025] FlooNoC's 3.5% area overhead per tile enables linear area scaling: doubling the mesh doubles the interconnect area but also doubles the number of routers, maintaining constant bisection bandwidth per PE. The practical limit is on-chip wiring congestion at ~1000+ links (already demonstrated at 8×4 = 32 routers).

## Open Questions

- OPEN: What is the optimal PE-to-router ratio? MAGIA assigns one router per tile (one RISC-V + one RedMulE); MemPool assigns one interconnect port per 4 cores. Is there a systematic trade-off model?
- OPEN: How does 3D integration (hybrid bonding, as explored in the 1L2D near-DRAM architecture) change the interconnect design space? Vertical Through-Silicon Vias (TSVs) offer much higher bandwidth density than planar wires but add thermal constraints.
- OPEN: Can reconfigurable NoCs (ROZK-style) scale beyond 16 PEs? The configuration overhead (reconfiguring switches per layer) may dominate execution time for small DNN layers.
- OPEN: What is the energy cost of FlooNoC's wide physical links (512-bit) at the 12nm node vs. narrower links at higher frequency? The 0.15 pJ/B/hop figure is state-of-the-art but has not been independently reproduced.
- VERIFY: No published comparison exists of MemPool hierarchical interconnect vs. FlooNoC mesh running the same matrix multiply workload at iso-PE-count and iso-technology.
- VERIFY: The 1024-FPU MemPool-Spatz configuration exists only in simulation (RTL + gate-level netlist); no fabricated silicon with >256 FPUs in a single shared-L1 cluster has been demonstrated.
