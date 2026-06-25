---
id: system.scale.nvlink-nvswitch-domain
title: NVLink and NVSwitch — GPU Scale-Up Interconnect Domains
status: draft
layer: 120-scale-up-system
layer_path: 120-scale-up-system/nvidia/nvlink-nvswitch-scaleup-domain
parent: system.scale.chiplet-architecture
secondary_layers: [60-interconnect-power-thermal, 130-scale-out-distributed-system]
granularity: concept
concept_type: architecture_pattern
scale_scope: [die, package, node, rack]
reasoning_roles: [enabler, scale_up_strategy, bottleneck]
tags: [nvlink, nvswitch, scale-up, gpu-interconnect, nvl72, superpod, fat-tree, gb200]
aliases: [NVIDIA NVLink, NVSwitch domain, GPU scale-up fabric, NVL72, GPU interconnect topology]
sources: [nvlink-scale-up-introl-2025, gb200-nvl72-reference-2025, nvidia-nvlink-evolution-2025, gpuyard-nvlink-blackwell-2026]
---

# NVLink and NVSwitch — GPU Scale-Up Interconnect Domains

## Overview

NVLink is NVIDIA's proprietary GPU-to-GPU interconnect — a high-bandwidth, low-latency link that creates a scale-up domain within which GPUs communicate as if they were a single large accelerator. NVSwitch is the crossbar switch that connects multiple GPUs in a non-blocking fabric, removing the need for direct GPU-to-GPU cabling and making every GPU equidistant from every other GPU. Together, they form the scale-up backbone of NVIDIA's AI computing strategy.

- [supported][src:nvlink-scale-up-introl-2025] NVLink bandwidth has doubled roughly every generation: 300 GB/s (V100, NVLink 2.0, 2017) → 600 GB/s (A100, 3.0) → 900 GB/s (H100, 4.0) → 1.8 TB/s (B200, 5.0) → 3.6 TB/s (Rubin, 6.0, 2026). At 1.8 TB/s, NVLink 5.0 is 14× the bandwidth of PCIe Gen5 x16 (~128 GB/s). The scale-up fabric bandwidth now rivals or exceeds HBM bandwidth within each GPU.
- [supported][src:gb200-nvl72-reference-2025] The GB200 NVL72 rack integrates 72 B200 GPUs via 18 NVSwitch ASICs in a fully non-blocking topology, achieving 130 TB/s aggregate bidirectional bandwidth. Every GPU is one NVSwitch hop from every other GPU — there are no multi-hop paths within the rack. Total GPU memory in the domain: 13.4 TB HBM3E.
- [inference] The architectural significance of NVL72: it transforms a rack of 72 independent GPUs into a single 130 TB/s scale-up domain. This means tensor parallelism (which requires all-to-all communication within a layer) can span 72 GPUs without crossing into the scale-out network (InfiniBand/RoCE). For a model like GPT-4, the entire attention mechanism can live within one NVLink domain — only pipeline parallelism and data parallelism need the external network.

## NVLink Generation Evolution

| Architecture | NVLink Gen | Links/GPU | Per-GPU BW | Per-Link Rate | Key Innovation |
|---|---|---|---|---|---|
| Pascal P100 | 1.0 | 4 | 160 GB/s | 40 GB/s | First GPU-to-GPU direct link |
| Volta V100 | 2.0 | 6 | 300 GB/s | 50 GB/s | First NVSwitch (DGX-2, 16 GPU) |
| Ampere A100 | 3.0 | 12 | 600 GB/s | 50 GB/s | NVSwitch 2.0, SHARP in-network reduction |
| Hopper H100 | 4.0 | 18 | 900 GB/s | 50 GB/s | NVSwitch 3.0, 25.6 Tb/s per switch |
| Blackwell B200 | 5.0 | 18 | 1.8 TB/s | 100 GB/s | NVSwitch 4.0, 72-GPU single domain |
| Rubin VR200 | 6.0 | TBD | 3.6 TB/s | TBD | NVL144, Kyber rack, Switch Blade |

- [inference] The NVSwitch transition from board-level switch (DGX-2, 2018) to rack-level switch fabric (GB200 NVL72, 2025) mirrors the transition from SMP buses to switched fabrics in the server industry in the 1990s. The switch overhead (power, latency, silicon area) is justified by the elimination of N² direct GPU-to-GPU links and the architectural simplification of a single-hop fabric.

## The NVL72 Architecture

### Physical Topology

- [supported][src:gb200-nvl72-reference-2025] Each NVL72 rack contains 18 compute trays (2 GB200 Superchips each = 4 B200 GPUs per tray) and 9 switch trays (2 NVSwitch 4.0 ASICs each = 144 NVLink ports total). Every B200 GPU connects to every NVSwitch — a crossbar topology with no oversubscription. The result: any GPU can communicate with any other GPU at full NVLink 5.0 bandwidth (1.8 TB/s) in a single switch hop.
- [inference] The crossbar topology means the fabric scales as O(G × S) where G is GPU count and S is switch port count. At 72 GPUs × 18 ports/GPU = 1,296 endpoints, the 144 NVSwitch ports are non-blocking because each NVSwitch handles 72 ports (1,296 / 18 NVSwitches = 72 ports/switch). The switch silicon is the scaling limit: to go from 72 to 144 GPUs requires doubling the per-switch radix, which is why NVL144 waits for next-gen NVSwitch silicon.

### The 576-GPU SuperPOD

- [inference] Eight NVL72 racks form a 576-GPU SuperPOD using a two-tier fat-tree of NVSwitch ASICs: Tier-1 (288 switches, within each rack) and Tier-2 (144 switches, across racks). Total fabric bandwidth exceeds 1 PB/s. The fat-tree topology adds one hop of latency for cross-rack communication: intra-rack is 1 switch hop; cross-rack is 3 hops (GPU → Tier-1 → Tier-2 → Tier-1 → GPU).
- [inference] The 576-GPU domain pushes the scale-up/scale-out boundary outward: operations that previously required InfiniBand (scale-out) now fit within the NVSwitch fabric (scale-up). This reduces the latency gap between intra- and inter-GPU communication from ~10× (NVLink ~1 μs vs. InfiniBand ~10 μs) to ~2× (intra-rack NVSwitch ~1 μs vs. cross-rack NVSwitch ~2–3 μs). The implication: tensor parallelism can span hundreds of GPUs, not just eight.

## Comparison with Scale-Out Alternatives

| Property | NVLink/NVSwitch (Scale-Up) | InfiniBand NDR400 (Scale-Out) | UCIe (D2D) |
|---|---|---|---|
| Per-link BW | 100 GB/s (NVLink 5.0) | 50 GB/s (NDR400) | 32 GT/s (~64 GB/s equiv.) |
| Latency | ~1 μs (one switch hop) | ~5–10 μs (end-to-end) | ~6–9 ns (on-package) |
| Max domain size | 576 GPU (SuperPOD) | 10,000+ GPU | 2–16 chiplets per package |
| Power per bit | ~3–5 pJ/bit | ~10–20 pJ/bit | 0.5–1.2 pJ/bit |
| Standard | Proprietary (NVIDIA) | Open (IBTA) | Open (UCIe Consortium) |

- [inference] NVLink occupies a unique position: it is a proprietary, single-vendor technology that provides a competitive moat. No competitor can build an NVLink-equivalent fabric without NVIDIA's switch silicon. AMD's Infinity Fabric and Intel's XeLink offer similar functionality but at lower scale (MI355X supports 8-GPU domains via Infinity Fabric 4.0). The 72-GPU NVLink domain is currently unmatched in the industry.
- [inference] The NVSwitch moat is reinforced by the software stack: NCCL's topology-aware collective communication algorithms are tuned for NVSwitch topologies. Even if a competitor built equivalent switch hardware, they would need to replicate NCCL-level software integration to achieve comparable performance — a multi-year effort.

## Open Questions

- OPEN: At what domain size does the NVSwitch fat-tree overhead (power, latency, cost) exceed the benefit of keeping traffic within the scale-up domain? Is 576 GPUs the practical ceiling, or can the architecture scale to thousands of GPUs?
- OPEN: Will the industry converge on an open standard for GPU scale-up interconnects (UCIe extended to rack-scale, or CXL 3.0 fabric), or will proprietary fabrics (NVLink, Infinity Fabric) remain the performance leaders indefinitely?
- VERIFY: The claim that NVLink 6.0 achieves 3.6 TB/s per GPU (Rubin) is from industry analyst projections and NVIDIA roadmap presentations — actual silicon specifications are pending CES 2026.

## See Also

- [[system.scale.chiplet-architecture]] — Chiplet architecture where NVLink bridges between packages.
- [[system.scale.scale-up-vs-scale-out]] — The scale-up/scale-out framework that NVLink and NVSwitch embody.
- [[system.ai.collective-communication-algorithms]] — NCCL collectives tuned for NVSwitch topologies.
- [[chip.circuit.serdes-io-phy-ai-chiplets]] — SerDes PHYs that provide the physical layer for NVLink signaling.
- [[workload.ai.model-parallelism-strategies]] — Model parallelism constrained by NVLink domain boundaries.
- [[system.riscv.distributed-ai-clusters]] — RISC-V clusters that lack an NVLink-equivalent and take a different approach.
