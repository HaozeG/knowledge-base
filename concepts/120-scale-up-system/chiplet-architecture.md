---
id: system.scale.chiplet-architecture
title: Chiplet-Based Scale-Up Architecture for AI Accelerators
status: draft
layer: 120-scale-up-system
layer_path: 120-scale-up-system/chiplet/scale-up-architecture
parent: system.scale.scale-up-vs-scale-out
secondary_layers: [20-manufacturing-process-integration, 30-circuit-ip-primitives, 60-interconnect-power-thermal]
granularity: concept
concept_type: scaling_strategy
scale_scope: [die, package, node]
reasoning_roles: [scale_up_strategy, enabler]
tags: [chiplet, ucie, d2d, scale-up, advanced-packaging, interposer, die-disaggregation, ai-accelerator]
aliases: [chiplet architecture for AI, die-to-die interconnect, UCIe-based scale-up, multi-die AI accelerator]
sources: [tsmc-cowos-roadmap-2026, ucie-standard-2025, epoch-ai-chip-supply-chain-2025, semiconductor-engineering-chiplet-design-2025]
---

# Chiplet-Based Scale-Up Architecture for AI Accelerators

## First-Principle Explanation

A monolithic AI accelerator is bounded by the reticle limit (~858 mm²). A chiplet-based accelerator bypasses this limit by partitioning the design across multiple smaller dies, each within the reticle limit, connected by die-to-die (D2D) interfaces. The first-principle tradeoff:

```text
monolithic_die:  max_compute_per_chip = reticle_area × transistor_density × utilization
                 cost = wafer_cost / (dies_per_wafer × yield) — yield falls exponentially with area

chiplet_design:  max_compute_per_package = Σ(chiplet_area_i × transistor_density_i)
                 cost = Σ(wafer_cost_i / (dies_per_wafer_i × yield_i)) + packaging_cost
                 D2D_overhead = die_edge_bandwidth × D2D_energy_per_bit × D2D_latency
```

The organizer's insight: **chiplets decouple the yield economics from the compute economics**. A monolithic 800 mm² die at N3 yields ~45% good dies. The same design partitioned into 4× 200 mm² chiplets yields ~82% per chiplet — and you only need all 4 to work if they're non-redundant. With redundancy (5 chiplets, any 4 work), the package yield approaches 95%+.

- [supported][src:epoch-ai-chip-supply-chain-2025] Advanced packaging (CoWoS) — not logic wafers — was the primary AI chip bottleneck in 2025. CoWoS capacity grew from ~12K wpm (2023) to ~65-75K wpm (2025). The bottleneck shift from front-end (wafers) to back-end (packaging) is a direct consequence of the chiplet transition.
- [supported][src:semiconductor-engineering-chiplet-design-2025] Heterogeneous node mixing is the economic logic behind chiplets: compute tiles on N3/N2 for maximum logic density, SRAM tiles on N5/N4 where SRAM scaling has plateaued, and I/O tiles on mature nodes. AMD's 3D V-Cache is the leading commercial example.
- [speculative][src:tsmc-cowos-roadmap-2026] CoWoS interposer size is scaling from 3.3× reticle (2024) to 8× reticle (2027), enabling 4 compute dies + 12 HBM stacks in a single package. This is the physical mechanism that makes chiplet-based scale-up viable — without interposer scaling, chiplet count is limited by interposer area.

## Die Disaggregation Strategies

### Compute-Memory Disaggregation

- [inference] The most common chiplet partitioning: separate compute dies (logic-heavy, latest node) from memory dies (SRAM-heavy, N-1 or N-2 node). This exploits the SRAM scaling gap — SRAM density improves only ~1.1-1.3× per node while logic improves ~1.5-2×. Putting SRAM on the latest node wastes expensive transistor area; putting it on N-2 saves cost without hurting performance (SRAM speed is dominated by array organization, not transistor speed).
- [speculative] The extreme of compute-memory disaggregation is 3D stacking: AMD's V-Cache stacks an additional SRAM die directly on top of the compute die, connected by through-silicon vias (TSVs). The 3D connection provides ~2 TB/s/mm² bandwidth at ~0.1 pJ/bit — an order of magnitude better than 2.5D interposer connections (~200 GB/s/mm, ~0.5 pJ/bit).

### I/O Disaggregation

- [speculative] I/O chiplets on mature nodes (N7, N12) house the PHYs for HBM, PCIe, UCIe, and Ethernet. The economic logic: I/O circuits don't scale with process node (analog/mixed-signal PHYs are limited by physics, not transistor density), so putting them on the latest node wastes expensive die area. I/O disaggregation can reduce compute die area by 15-25%.
- [inference] The I/O chiplet strategy mirrors the industry's transition from monolithic server CPUs (Intel Xeon, all I/O on-die) to chiplet-based designs (AMD EPYC, separate I/O die). The same economic forces that drove CPU disaggregation now drive AI accelerator disaggregation — just at larger scale.

## D2D Interconnect Standards

### UCIe: The Emerging Standard

- [supported][src:ucie-standard-2025] UCIe (Universal Chiplet Interconnect Express) has emerged as the industry-standard D2D interface, supporting 16-32 Gb/s per lane at 0.25-0.5 pJ/bit. Key features:
  - **Standard (2D) package**: up to 16 Gb/s/lane, ~0.5 pJ/bit, organic substrate
  - **Advanced (2.5D) package**: up to 32 Gb/s/lane, ~0.25 pJ/bit, silicon interposer or bridge
  - **Protocol layering**: physical layer (D2D PHY) + adapter layer (protocol translation: PCIe, CXL, AXI, CHI)
- [inference] UCIe's protocol layering is the key architectural innovation: it separates the physical D2D connection (which must be optimized for the specific package technology) from the logical protocol (which must be compatible with existing SoC interfaces). This enables a UCIe-connected chiplet to look like a PCIe device, a CXL.mem device, or a CHI-coherent peer — depending on which protocol adapter is instantiated.

### Bandwidth and Latency Hierarchy

- [speculative] D2D interconnect sits between on-chip NoC and off-package interconnect in the bandwidth/latency hierarchy:
  | Interconnect | Bandwidth | Latency | Energy/bit | Use |
  |---|---|---|---|---|
  | On-chip NoC | 100-1000 GB/s/mm | <10 ns | 0.1-0.5 pJ | PE-to-PE, PE-to-SRAM |
  | D2D (UCIe advanced) | 50-200 GB/s/mm | 2-5 ns | 0.25-0.5 pJ | Chiplet-to-chiplet |
  | D2D (UCIe standard) | 10-50 GB/s/mm | 5-10 ns | 0.5-1 pJ | Chiplet-to-chiplet (organic) |
  | Inter-package (NVLink) | 100-900 GB/s | 100-500 ns | 5-20 pJ | GPU-to-GPU |
  | Inter-node (InfiniBand) | 50-400 GB/s | 1-10 µs | 50-200 pJ | Node-to-node |

- [inference] The bandwidth and latency cliff between D2D and inter-package (2 orders of magnitude in latency, 1-2 orders in energy) explains why chiplet-based scale-up is viable but multi-package scale-out is hard: chiplets on the same interposer can share memory at near-on-chip latency, while GPUs across NVLink must explicitly manage data movement.

## Chiplet Partitioning Strategies for AI

### Tensor Parallelism Over Chiplets

- [speculative] For large models that exceed a single chiplet's memory capacity, tensor parallelism splits the model across chiplets. Each chiplet holds a slice of the weight matrix and computes its portion of the output. The D2D interconnect carries activations (forward pass) and gradients (backward pass) between chiplets. The bandwidth requirement: model_dim × batch_size × tokens_per_second per chiplet boundary.
- [inference] For a 70B model with model_dim=8192, batch=64, generating 1000 tok/s: the inter-chiplet bandwidth requirement is ~8K × 64 × 1000 × 2 bytes (FP16) = ~1 GB/s per chiplet boundary — well within UCIe advanced (50+ GB/s). Tensor parallelism over chiplets is NOT bandwidth-limited if the partitioning is done correctly.

### Memory Pooling Over Chiplets

- [speculative] CXL.mem over UCIe enables memory pooling: multiple compute chiplets share a common pool of HBM stacks through a CXL memory fabric. This is architecturally analogous to NUMA in multi-socket servers but at the package level. The key constraint: CXL.mem latency (~50-100 ns over UCIe) is 5-10× higher than on-package HBM latency (~10 ns), creating a NUMA-like memory hierarchy within the package.
- [inference] The intra-package NUMA problem means chiplet partitioning must be NUMA-aware: place model parameters on the HBM closest to the chiplet that accesses them most frequently. The compiler (not the hardware) must manage this — the chiplet memory hierarchy is software-visible.

## Implications for RISC-V Scale-Up

- [speculative] RISC-V's open ISA creates a unique opportunity for chiplet-based scale-up: different chiplets can use different RISC-V core designs (in-order for I/O, OoO for compute, vector for prefill, matrix for GEMM) while maintaining ISA compatibility at the RVV/matrix extension level. The UCIe protocol layer translates between different internal interconnects (AXI, CHI, TileLink) — the chiplet interface is protocol-agnostic.
- [inference] The RISC-V chiplet thesis: an AI accelerator package with 1× Ventana Veyron-class OoO chiplet (prefill), 8× Esperanto ET-Minion-class in-order chiplets (decode), 1× I/O chiplet (HBM, PCIe, UCIe), and 1× SRAM chiplet (large L3 cache) — all RISC-V, all UCIe-connected, all standard ISA. This is only possible because RISC-V doesn't have the ARM/x86 licensing model that restricts who can build what type of core.

## Open Questions

- OPEN: Will UCIe achieve the interoperability vision (mixing chiplets from different vendors in the same package), or will practical chiplet integration require per-design validation that makes multi-vendor chiplets uneconomical?
- OPEN: What is the optimal chiplet granularity? Smaller chiplets have higher yield but more D2D interfaces (and D2D power). Larger chiplets have fewer interfaces but lower yield. The economic optimum depends on defect density, D2D energy cost, and chiplet test cost.
- OPEN: Can CXL.mem over UCIe provide low enough latency for AI training (where gradient synchronization is latency-sensitive), or is it limited to inference (where memory access patterns are more predictable and latency-tolerant)?
- VERIFY: CoWoS interposer scaling to 8× reticle (2027) is from TSMC roadmap presentations; actual production availability may differ.
- VERIFY: UCIe 32 Gb/s/lane at 0.25 pJ/bit is the specification target; real silicon measurements at volume are limited.
