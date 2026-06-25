---
id: system.networking.rdma-smartnic-ai-cluster
title: RDMA, SmartNICs, and Scale-Out Networking for AI Clusters
status: draft
layer: 130-scale-out-distributed-system
layer_path: 130-scale-out-distributed-system/networking/rdma-smartnic-cluster-fabric
parent: system.ai.collective-communication-algorithms
secondary_layers: [60-interconnect-power-thermal, 120-scale-up-system, 150-supply-chain-business]
granularity: concept
concept_type: architecture_pattern
scale_scope: [node, rack, cluster]
reasoning_roles: [enabler, bottleneck, scale_out_strategy]
tags: [rdma, roce, infiniband, smartnic, dpu, scale-out, 400g, 800g, uec, gse]
aliases: [RDMA for AI, RoCEv2, InfiniBand networking, SmartNIC DPU, AI cluster fabric]
sources: [mellanox-connectx8-2025, sugong-scalefabric-2026, uec-1-0-ethernet-2025, kiwi-moore-800g-snic-2025, zte-three-domain-scale-2026]
---

# RDMA, SmartNICs, and Scale-Out Networking for AI Clusters

## Overview

When an AI training run spans more GPUs than fit in a single NVLink domain, the network connecting those domains becomes the performance bottleneck. Scale-out networking for AI clusters uses RDMA (Remote Direct Memory Access) to move data directly between GPU memories without CPU involvement, SmartNICs/DPUs to offload network processing, and high-radix switches to connect thousands of GPUs. The competition between InfiniBand (proprietary, optimized) and Ethernet+RoCE (open, converging rapidly) is the defining dynamic of AI cluster networking in 2025–2026.

- [supported][src:mellanox-connectx8-2025] NVIDIA ConnectX-8 is the benchmark scale-out NIC: 400/800 Gb/s, PCIe Gen6, integrated switch, supporting both InfiniBand NDR and RoCEv2. RDMA enables GPU-to-GPU data transfer at ~0.9 μs end-to-end latency without CPU involvement — the CPU's only role is to set up the RDMA queue pair and then stay out of the data path.
- [supported][src:uec-1-0-ethernet-2025] The Ultra Ethernet Consortium (UEC) 1.0 specification (June 2025) introduces packet spraying, credit-based flow control (CBFC), and link-layer retransmission (LLR) to make Ethernet competitive with InfiniBand at 10K+ GPU scale. Supported by Broadcom (Tomahawk 6), Marvell (Teralynx T10), and NVIDIA (Spectrum-6), UEC represents the industry's bet that Ethernet will win the scale-out networking standard war.
- [inference] The fundamental trade-off: InfiniBand delivers lower latency and lossless delivery out of the box but is a single-vendor (NVIDIA) solution with proprietary switches and NICs. RoCEv2 + UEC delivers competitive performance at lower cost with multi-vendor interoperability but requires careful congestion control tuning (PFC, ECN, DCQCN) that breaks down at extreme scale (>10K GPUs) due to PFC storm and incast congestion pathologies.

## RDMA: The Foundation

### How RDMA Works

- [inference] RDMA allows one GPU's NIC to write data directly into another GPU's memory, bypassing the CPU and kernel network stack entirely. The flow: GPU kernel finishes → DMA to NIC buffer → RDMA write over the network → remote NIC DMA to remote GPU memory → signal completion. The CPUs on both ends are uninvolved after queue pair setup. This achieves ~0.9 μs end-to-end latency vs. ~10–50 μs for kernel TCP.
- [inference] RDMA's zero-copy model is critical for GPU clusters because GPU memory bandwidth (3–8 TB/s for HBM) far exceeds CPU memory bandwidth (~100–200 GB/s for DDR5). If gradient data had to pass through CPU memory during AllReduce, the CPU memory bus would be the bottleneck. RDMA keeps data entirely within the GPU-NIC-GPU path, avoiding the CPU memory bottleneck.

### InfiniBand vs. RoCEv2

| Property | InfiniBand (IB) | RoCEv2 (Ethernet) |
|---|---|---|
| Latency (end-to-end) | ~0.9 μs | ~1.5–3 μs (tuned) |
| Lossless delivery | Native credit-based | PFC + ECN (complex) |
| Max scalability | ~49K GPUs/subnet (NDR) | Theoretically unlimited (IP) |
| Multi-vendor | NVIDIA/Mellanox only | Broadcom, Marvell, Cisco, etc. |
| Cost per 400G port | ~$1,500–2,000 | ~$800–1,200 |
| Switch radix | 64 ports (QM9790) | 128+ ports (Tomahawk 5) |

- [supported][src:sugong-scalefabric-2026] China's domestic InfiniBand alternative (Sugon scaleFabric) supports 114,000 GPUs per subnet — 2.33× NVIDIA NDR's 49K limit — with 400G NICs, 80-port 400G/800G switches, and 0.93 μs end-to-end RDMA. Deployed at 30,000 GPU scale in Zhengzhou for 10+ months of continuous operation.

### UEC and the Ethernet Convergence

- [inference] UEC 1.0 addresses the three pathologies of RoCEv2 at scale: (1) PFC storms — credit-based flow control eliminates the need for PFC entirely; (2) ECMP imbalance — packet spraying distributes flows across all available paths instead of hashing to a single path per flow; (3) tail latency — link-layer retransmission recovers lost packets in microseconds instead of milliseconds via TCP retransmission. If UEC delivers on these promises, Ethernet achieves InfiniBand-class performance with Ethernet-class economics.
- [inference] The parallel development of China's GSE (Global Scheduling Ethernet) is significant: GSE's N2N (network-to-network) mode works without requiring NIC upgrades — existing RoCEv2 NICs benefit from GSE-enabled switches. This backward compatibility could accelerate adoption in China's 10K+ GPU clusters where replacing thousands of NICs is cost-prohibitive.

## SmartNICs and DPUs

- [inference] A SmartNIC (or DPU — Data Processing Unit) integrates a programmable processor (ARM/RISC-V cores), hardware accelerators for RDMA and crypto, and high-speed SerDes onto the network interface card. The DPU offloads infrastructure tasks (network virtualization, storage compression, security) that would otherwise consume CPU cores better spent on training orchestration.
- [inference] For AI clusters, the key DPU value proposition is reducing the "CPU tax": in a 10K-GPU cluster, ~30% of host CPU cycles are spent on data movement and network stack processing. Offloading this to DPUs frees ~3,000 CPU cores for training orchestration, improving overall training throughput by 20–25%. The DPU is the network equivalent of TMA (Tensor Memory Accelerator) for on-die data movement — it automates data transfer so compute units can focus on compute.
- [supported][src:kiwi-moore-800g-snic-2025] 800G SmartNICs (Kiwi Moore, Cloud-Mind) are entering the market with per-lane 400G SerDes, PCIe switch integration, and per-microsecond congestion control. These represent the shift from 400G mainstream to 800G emerging — the same transition occurring in switch fabrics.

## Scale-Out at 10K+ GPU Scale

- [inference] The networking challenge at 10K+ GPU scale is fundamentally different from 1K scale: at 1K GPUs, a single AllReduce operation involves ~1K peers exchanging ~1 GB each — total fabric load ~1 TB per step, easily handled by a 400 Gbps × 1,000 port fabric. At 100K GPUs, the same AllReduce exchanges ~100 TB per step — requiring multi-tiered switch fabrics, hierarchical reduction algorithms, and congestion control that doesn't collapse under incast.
- [supported][src:zte-three-domain-scale-2026] The industry is coalescing around a three-domain interconnect model: Scale-Up (NVLink/UALink within a supernode), Scale-Out (RDMA/Ethernet across supernodes), and Scale-Across (optical/OTN across datacenters). Each domain has different latency, bandwidth, and cost requirements. The Scale-Out domain is where RDMA, SmartNICs, and UEC/Ethernet compete — and where the majority of cluster networking CapEx is spent.

## Open Questions

- OPEN: Will UEC 1.0 Ethernet match InfiniBand latency at 100K+ GPU scale, or will the complexity of making Ethernet lossless create operational fragility that favors proprietary IB for the largest training runs?
- OPEN: As China develops domestic alternatives (scaleFabric IB, GSE Ethernet, Cloud-Mind DPU), does the global AI networking market bifurcate into China and non-China supply chains, or do open standards bridge the gap?
- VERIFY: The claim that DPUs improve training throughput by 20–25% is based on vendor projections — independent benchmarks on production-scale clusters are not yet publicly available.

## See Also

- [[system.ai.collective-communication-algorithms]] — Collective algorithms (AllReduce, AllGather) that RDMA transports.
- [[system.scale.nvlink-nvswitch-domain]] — NVLink scale-up domain that RDMA scale-out complements.
- [[system.scale.scale-up-vs-scale-out]] — Scale-up/scale-out framework that RDMA-enabled Ethernet implements.
- [[chip.circuit.serdes-io-phy-ai-chiplets]] — SerDes PHYs that provide the physical layer for 400G/800G signaling.
- [[system.riscv.distributed-ai-clusters]] — RISC-V distributed clusters that benefit from open RDMA/Ethernet fabrics.
- [[industry.ai.supply-chain-bottlenecks]] — Supply chain constraints that affect switch and NIC availability.
