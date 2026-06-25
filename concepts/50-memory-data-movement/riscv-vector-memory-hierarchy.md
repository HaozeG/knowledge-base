---
id: hw.riscv.vector-memory-hierarchy
title: RISC-V Vector AI SoC Memory Hierarchy and Data Movement
status: draft
layer: 50-memory-data-movement
layer_path: 50-memory-data-movement/riscv/vector-memory
parent: hw.riscv.vector-extension
secondary_layers: [40-compute-substrate, 60-interconnect-power-thermal, 140-performance-cost-utilization-model]
granularity: concept
concept_type: memory_pattern
scale_scope: [unit, tile, die, package]
reasoning_roles: [constraint, bottleneck, bottleneck_mitigation, locality_strategy]
tags: [riscv, rvv, memory, cache, dma, bandwidth, ai, vector, vla, interconnect, hbm, ddr, scratchpad]
aliases: [RVV memory system, RISC-V vector SoC data movement]
sources: [cnx-c908-aiot-2022, spacemit-k1-datasheet-2024, ventana-veyron-v2-hc2023, esperanto-etsoc1-hc2021, epi-vpu-bandwidth-2023, riscv-v-spec-ratified-2021, gemmini-berkeley-eecs2022, chipyard-gemmini-docs-2024, magia-fractalsync-2025, riscv-iommu-spec, semidynamics-vector-unit, t-head-c908-aliyun-2022, k230-technical-manual]
---

# RISC-V Vector AI SoC Memory Hierarchy and Data Movement

## First-Principle Explanation

A wide vector unit (256-bit to 4096-bit VLEN) requires commensurate memory bandwidth. The memory system -- cache hierarchy, scratchpads, prefetchers, DMA engines, and on-chip interconnect -- often determines realized AI performance more than peak vector throughput.

The first-principle constraint is a fundamental bandwidth tension:

```text
vector width doubles  -> elements per instruction double   -> data consumption doubles
DRAM bandwidth grows  -> ~15-25% per generation (HBM, DDR) -> does not double
cache capacity grows  -> ~2x per generation (SRAM scaling) -> does not match VLEN scaling
```

This gap means RISC-V AI SoC architects cannot simply scale VLEN and expect proportional performance gains. The memory hierarchy design -- cache depth, scratchpad sizing, interconnect topology, and data movement engines -- determines the realized fraction of peak vector throughput.

## Key Claims

- [supported][src:cnx-c908-aiot-2022][src:t-head-c908-aliyun-2022] The T-Head XuanTie C908 implements 128-bit RVV 1.0 with 32 KB L1 I-cache, 32 KB L1 D-cache, and 256 KB unified L2 cache per core, targeting AIoT applications at 1.6 GHz.
- [supported][src:spacemit-k1-datasheet-2024] The SpacemiT K1 implements 256-bit RVV 1.0 across 8 X60 cores with 32 KB L1I/L1D per core, 512 KB L2 cache per cluster (1 MB total), and 512 KB TCM in the AI cluster. DRAM bandwidth is ~10.6 GB/s via 32-bit LPDDR4X-2666.
- [supported][src:ventana-veyron-v2-hc2023] The Ventana Veyron V2 implements 512-bit RVV 1.0 on 4 nm TSMC with 128 KB L1 D-cache and 512 KB L1 I-cache per core, 1.5 MB private L2 per core, and 128 MB shared L3 per 32-core cluster. Supports 12-channel DDR5-5600 with optional HBM3.
- [supported][src:esperanto-etsoc1-hc2021][src:epi-vpu-bandwidth-2023] Esperanto's ET-SoC-1 uses a many-core (1088 core) approach with per-core 4 KB L1 data scratchpad, shared 4 MB SRAM per 32-core shire, and mesh NoC. Each ET-Minion core has 512-bit integer / 256-bit FP vector paths.
- [supported][src:epi-vpu-bandwidth-2023] The EPI/BSC FPGA study showed scalar code plateaus at ~2 bytes/cycle, while vector code with VL=256 elements (2048-bit registers for FP64) continues benefiting from bandwidth up to 64 bytes/cycle. Long vectors reduce memory latency sensitivity: at high added latency, scalar code slows by 8.8x while long-vector code slows by only ~3.6x.
- [supported][src:riscv-v-spec-ratified-2021] RVV 1.0 defines three vector load/store patterns: unit-stride, strided, and indexed (scatter/gather). Fault-only-first loads are limited to unit-stride due to encoding constraints and security concerns about probing arbitrary page accessibility.
- [supported][src:gemmini-berkeley-eecs2022][src:chipyard-gemmini-docs-2024] In open-source RISC-V AI accelerators (Gemmini), data movement uses explicit DMA (mvin/mvout) between DRAM and software-managed scratchpads over TileLink, with double-buffering to hide memory latency. This contrasts with hardware-managed cache hierarchies in general-purpose CPUs.
- [inference][src:epi-vpu-bandwidth-2023][src:ventana-veyron-v2-hc2023] A 512-bit VLEN unit at 3.6 GHz needs ~230 GB/s for unit-stride load saturation. Ventana's 12-channel DDR5-5600 provides ~537 GB/s theoretical peak, suggesting memory bandwidth is not the bottleneck for a single core but becomes critical at 32+ core scaling without HBM.
- [inference][src:spacemit-k1-datasheet-2024] The SpacemiT K1's 10.6 GB/s DRAM bandwidth is sufficient for the 256-bit vector unit only at modest clock speeds and low occupancy. For fully saturated vector ALUs, external bandwidth is the primary constraint; the 512 KB TCM in the AI cluster provides latency-critical local storage.
- [inference][src:epi-vpu-bandwidth-2023] The ratio of vector compute throughput to memory bandwidth (bytes/FLOP) is the key design metric for RVV AI SoCs. Without commensurate bandwidth scaling, increasing VLEN yields diminishing returns -- the roofline model's memory-bound ceiling.

## Memory System Tiers in RVV AI SoCs

RVV AI SoC memory hierarchies span three tiers, reflecting different market segments:

### Tier 1: Edge AI (128-256 bit VLEN)

**Representative silicon:** T-Head C908 (128-bit), SpacemiT K1 (256-bit)

| Parameter | C908 (K230 SoC) | SpacemiT K1 |
|-----------|-----------------|-------------|
| VLEN | 128-bit RVV 1.0 | 256-bit RVV 1.0 |
| Core count | 1-2 | 8 (dual cluster) |
| L1 D-cache | 32 KB | 32 KB per core |
| L2 cache | 256 KB unified | 512 KB per cluster, no L3 |
| TCM | None | 512 KB (AI cluster only) |
| DRAM | 32-bit LPDDR4/DDR3 | 32-bit LPDDR4X-2666 |
| DRAM BW | ~4-8 GB/s (est.) | ~10.6 GB/s |
| Process | 12 nm (est.) | 22 nm |
| Power | ~2 W | ~3.5 W |
| Coherency | DMA-noncoherent | Cluster-coherent |

Key observation: Edge RVV SoCs are strongly memory-bandwidth-bound. The C908's 128-bit VLEN at 1.6 GHz needs ~25.6 GB/s for saturated vector loads, but the DDR3/4 interface provides only 4-8 GB/s. Similarly, the K1's 256-bit VLEN at ~1.8 GHz needs ~57.6 GB/s but has only 10.6 GB/s. The vector ALU is underutilized for bandwidth-intensive kernels.

The SpacemiT K1's 512 KB TCM in the AI cluster is a notable design choice: it provides latency-critical local storage for tiled matrix operations from the custom IME instructions, bypassing the L2 cache hierarchy entirely.

### Tier 2: Server-Class (512-bit VLEN)

**Representative silicon:** Ventana Veyron V2

| Parameter | Veyron V2 |
|-----------|------------|
| VLEN | 512-bit RVV 1.0 |
| Core per cluster | 32 |
| Die count | Up to 6 chiplets (192 cores) |
| L1 D-cache | 128 KB per core |
| L1 I-cache | 512 KB per core |
| L2 cache | 1.5 MB private per core |
| L3 cache | 128 MB shared per cluster |
| Memory | 12-channel DDR5-5600 or HBM3 |
| DRAM BW (DDR5) | ~537 GB/s theoretical |
| Mesh BW | 5 TB/s on-chip per chiplet |
| Process | 4 nm |
| Clock | 3.6-3.85 GHz |
| Interconnect | UCIe for chiplet, PCIe 5.0 |

Key observation: The Veyron V2's memory hierarchy is architecturally comparable to server-class CPUs (AMD EPYC, Intel Xeon), not GPUs. The deep cache hierarchy (128 KB L1D, 1.5 MB private L2, 128 MB shared L3) is designed to keep the 512-bit vector unit fed while maintaining cache coherency across 32 cores. The 128 MB L3 per cluster is unusually large, suggesting Ventana expects significant data reuse in vectorized workloads.

The per-core 512-bit RVV 1.0 unit with 0.5 TOPS/GHz INT8 matrix accelerator means each core at 3.6 GHz delivers ~1.8 TOPS INT8. A 32-core cluster delivers ~57.6 TOPS, requiring ~5 GB/s per TOPS if memory-bound -- the 12-channel DDR5-5600 provides ~537 GB/s, giving ~9.3 GB/s per TOPS, a comfortable ratio.

### Tier 3: Many-Core AI Accelerator (Hybrid Memory Model)

**Representative silicon:** Esperanto ET-SoC-1

| Parameter | ET-SoC-1 |
|-----------|----------|
| Cores | 1088 ET-Minion + 4 ET-Maxion |
| Vector | Proprietary: 512-bit int / 256-bit FP per core |
| Per-core memory | 4 KB L1 data scratchpad/cache |
| Neighborhood (8 cores) | Shared I-cache, cooperative load |
| Shire (32 cores) | 4 MB SRAM (4x 1 MB banks, 512-bit crossbar) |
| Full chip | 34 shires + memory shires |
| DRAM | LPDDR4x, 24 x 64-bit chips on 6-chip card |
| Aggregate BW | 819 GB/s (6-chip OCP card) |
| On-chip fabric | Mesh NoC with atomics, barriers, IPI |
| Process | 7 nm |
| Power envelope | <120 W (6-chip card) |

Key observation: Esperanto's memory hierarchy is closer to GPU scratchpad memory than CPU cache hierarchy. Each ET-Minion core has only 4 KB of local scratchpad -- not enough to hold a full vector register file (512-bit vector x 32 registers = 2 KB). The 4 MB SRAM per shire is software-partitionable as scratchpad, private L2 cache, or shared L3.

The "cooperative load" mechanism -- where one core's L2 load is broadcast to all 8 cores in a neighborhood -- is a unique design. It reduces redundant DRAM traffic when all cores in a neighborhood access the same data, which is common in ML recommendation models with large shared embedding tables.

## RVV Memory Model vs. Hardware Reality

### Access Pattern Implications

The RVV 1.0 memory model defines three data movement patterns, each with distinct hardware implications:

**Unit-stride:**
- Best spatial locality; sequential addresses trigger efficient hardware prefetchers
- The hardware can coalesce the entire vector load into a single cache line request stream
- QEMU fast-path implementation achieved ~13-36x speedup by using memcpy-based bulk copies for unmasked unit-stride operations
- Whole-register loads/stores (`vl1r.v`, `vs1r.v`) are a special unit-stride pattern that bypasses LMUL and SEW, loading VLEN bits regardless of configured element width -- used for register save/restore and bulk data movement

**Strided:**
- Regular access pattern with variable stride; hardware prefetchers can learn the stride pattern
- Cache line utilization depends on element size relative to stride: small elements with large strides waste cache capacity
- Negative and zero strides are valid, complicating prefetcher design
- Strided segment loads (`vlsseg`) add further pattern complexity

**Indexed (scatter/gather):**
- Random access pattern by construction; violates spatial locality assumptions
- Heavy TLB pressure: each element may reference a different virtual page
- Cache line utilization is poor -- often a single element per cache line
- Ordered vs. unordered variants: unordered allows hardware reordering for better memory-level parallelism
- ASSUMPTION: For AI workloads, indexed loads are primarily useful for sparse embedding lookups and attention-based gather operations

### Fault-Only-First and Speculative Execution

Fault-only-first (FoF) loads are a key RVV mechanism for speculative vectorization:

- Only unit-stride FoF is defined; strided and indexed FoF were excluded for encoding scarcity and security (probing arbitrary page accessibility)
- The first active element always completes or faults (forward progress guarantee)
- Later elements that would fault are skipped, and VL is reduced
- Implementations may speculatively process a full VL and flush on misspeculation
- Cross-page handling is microarchitecturally significant: QEMU uses a `probe_pages` helper to check two pages per FoF operation, with segment loads requiring multi-page probe logic

- [inference][src:riscv-v-spec-ratified-2021] FoF loads serve as the RVV equivalent of speculative vectorization mechanisms found in GPU SIMT (where some threads can be masked without penalty). However, RVV FoF is limited to unit-stride, making it less general than SVE's non-faulting gather capability.

### TLB and Page Fault Interaction

- Vector loads/stores can hit TLB for each cache line, not each element -- unit-stride naturally amortizes TLB lookups
- Strided and indexed patterns can trigger multiple TLB misses per instruction, increasing memory access latency
- The RVV specification allows implementations to process elements in any order for unordered indexed operations, providing flexibility for TLB prefetch scheduling
- For FoF loads, successful elements must leave TLB/PTE state unchanged in terms of access/dirty bits, requiring careful microarchitectural handling

## Bandwidth Analysis

### Bandwidth Requirements by VLEN

For a vector unit performing unit-stride loads at full throughput:

| VLEN | 1.0 GHz (per core) | 2.0 GHz | 3.6 GHz | 4.0 GHz |
|------|-------------------|---------|---------|---------|
| 128-bit | 16 GB/s | 32 GB/s | 58 GB/s | 64 GB/s |
| 256-bit | 32 GB/s | 64 GB/s | 115 GB/s | 128 GB/s |
| 512-bit | 64 GB/s | 128 GB/s | 230 GB/s | 256 GB/s |
| 1024-bit | 128 GB/s | 256 GB/s | 461 GB/s | 512 GB/s |
| 2048-bit | 256 GB/s | 512 GB/s | 922 GB/s | 1024 GB/s |

Assumptions: Unit-stride load of a full VLEN register every cycle at SEW=64 (8 bytes/element). Real throughput is lower due to pipeline bubbles, cache misses, and LMUL grouping effects.

### Bandwidth Supply vs. Demand

| Memory Technology | Channel Width | Effective BW per Controller | Notes |
|------------------|--------------|----------------------------|-------|
| LPDDR4X-4266 | 32-bit | ~17 GB/s | Edge AI (C908, K1-class) |
| LPDDR4X-2666 | 32-bit | ~10.6 GB/s | SpacemiT K1 |
| DDR5-5600 | 64-bit per channel | ~44.8 GB/s per channel | Ventana Veyron V2 (12 channels = ~537 GB/s) |
| DDR5-6400 | 64-bit | ~51.2 GB/s per channel | Server class |
| HBM2e | 1024-bit per stack | ~460 GB/s per stack | GPU-class bandwidth |
| HBM3 | 1024-bit per stack | ~819 GB/s per stack | H100-class bandwidth |
| HBM3e | 1024-bit per stack | ~1.2 TB/s per stack | B200-class bandwidth |

- [speculative] A single 512-bit VLEN core at 3.6 GHz needs ~230 GB/s peak. One DDR5-5600 channel provides ~45 GB/s. A typical server-class DDR5 configuration (8-12 channels) provides 360-540 GB/s -- sufficient for 1-2 cores at full bandwidth, but scaling beyond 2 cores requires HBM.
- [supported][src:esperanto-etsoc1-hc2021] Esperanto's 1088-core ET-SoC-1 addresses the bandwidth gap through massive thread-level parallelism: 12,288 hardware threads (2 per core x 6 chips) hide memory latency through context switching, similar to GPU warp scheduling.

### Comparison with GPU Memory Hierarchy

| Dimension | GPU (H100) | RISC-V Server (Veyron V2) | RISC-V Edge (K1) |
|-----------|-----------|--------------------------|-------------------|
| Memory type | HBM3 | DDR5 / HBM3 | LPDDR4X |
| Peak BW | 3.35 TB/s | ~537 GB/s (DDR5) | ~10.6 GB/s |
| L2/LLC | 50 MB shared | 128 MB L3 shared | 1 MB L2 (no L3) |
| L1/scratchpad | 128 KB SM + 228 KB shared | 128 KB L1D | 32 KB L1D + 512 KB TCM |
| BW per FLOP (FP16) | ~1.7 B/FLOP (H100) | Variable | Low |
| Latency hiding | Warp switching | Cache hierarchy + OoO | Cache + multithreading |
| DM/TMA | TMA (async copy engine) | DMA via TileLink/CHI (RoCC) | DMA (CPU-driven) |

GPU memory hierarchy relies on massive thread parallelism (thousands of concurrent warps) for latency hiding, with a relatively small L2 (50 MB) for a 3.35 TB/s HBM interface. RISC-V server designs (Veyron V2) use deeper cache hierarchies (128 MB L3) to serve fewer, larger vector threads. Edge designs (K1) use modest caches with limited bandwidth and TCM bypass for latency-critical paths.

[supported][src:ventana-veyron-v2-hc2023][src:epi-vpu-bandwidth-2023] The GPU approach trades cache capacity for bandwidth (HBM); the RISC-V server approach trades bandwidth for cache depth. Neither is universally superior -- workload characteristics determine which tradeoff wins.

## Prefetch and DMA Patterns

### Software Prefetch in RVV

RVV currently has no ratified vector prefetch instruction. The ratified Zicbop extension provides scalar cache-block prefetch hints (`PREFETCH.R`, `PREFETCH.W`, `PREFETCH.I`) that operate on scalar addresses with immediate offsets.

The RISC-V CMO TG discussed whether vector prefetch instructions are necessary. The consensus from community experts (Greg Favor, Krste Asanovic) was:

- RVV programs already express high memory-level parallelism (MLP) through vector loads, making software prefetch less beneficial than in scalar code
- Hardware prefetchers can learn strided patterns from the vector load stream
- A vector prefetch instruction would need to operate similarly to vector load/store instructions (register-register address update, variable VL), adding encoding complexity

[supported][src:riscv-v-spec-ratified-2021] In practice, RVV vector loads serve as implicit prefetches: the VLEN-wide load brings in more data than immediately needed, and the memory system treats vector loads as prefetch hints. Non-faulting masked loads can be used for explicit software prefetching ahead of the current access point.

### Comparison with GPU TMA

GPU Tensor Memory Accelerator (TMA) provides a dedicated hardware unit for async copy of tensor-shaped blocks between global memory and shared memory. Key differences with RVV patterns:

| Aspect | GPU TMA | RVV Patterns (Current) |
|--------|---------|----------------------|
| Hardware support | Dedicated TMA unit in SM | Vector loads/stores; some DMA via RoCC accelerators |
| Data shape | 2D/3D tensor tiles | Linear (unit-stride), strided, gather/scatter |
| Programmability | CUDA cp.async, TMA descriptor | Inline vector assembly, intrinsics |
| Asynchrony | Warp-level async, fully decoupled from thread execution | Synchronous vector loads; separate DMA engine for accelerator data movement |
| Register pressure | No registers consumed for transfer | Vector registers consumed during load |
| Equivalent mechanism | No direct RVV equivalent | Closest: whole-register load/store; DMA for accelerator scratchpads |

- [inference][src:gemmini-berkeley-eecs2022][src:magia-fractalsync-2025] The closest RVV-equivalent to GPU TMA is the DMA engine design in open-source RISC-V AI accelerators like Gemmini: explicit `mvin`/`mvout` instructions move data between DRAM and scratchpad memories, with double-buffering for latency hiding. This is architecturally more similar to GPU's explicit shared memory management than to TMA's fully asynchronous tensor copy.

### DMA and IOMMU Patterns for AI Accelerators

RISC-V AI SoCs use several data movement patterns:

**1. RoCC Accelerator DMA (Gemmini-style)**
- Accelerator connects via RoCC interface to RISC-V core
- TileLink provides coherent memory access
- DMA engine executes mvin/mvout for scratchpad data movement
- Access-execute decoupling: load/compute/stores in separate queues
- Double-buffering: one scratchpad buffer used for compute, other for DMA transfer

**2. iDMA + NoC (MAGIA-style)**
- Per-tile DMA engine (iDMA) handles data movement between scratchpad and main memory
- Global mesh NoC (AXI4) connects all tiles
- One-sided DMA reads/writes for inter-tile communication
- Hardware barrier synchronization (FractalSync) for BSP execution

**3. Cache-Coherent Interconnect Patterns**
- TileLink TL-C: lightweight cached/coherent protocol for open-source RISC-V SoCs
- AMBA CHI: high-performance coherent protocol for multi-accelerator designs (Ventana, Qualcomm)
- Hybrid approaches: coherent fabric (CHI/TileLink) for CPU + LLC + coherent accelerators, separate non-coherent fabric for high-throughput DMA traffic

[supported][src:riscv-iommu-spec] The RISC-V IOMMU maps per-process virtual address spaces into DMA address spaces for accelerators, providing isolation and enabling zero-copy data movement. It adds latency and software overhead for context setup.

[supported][src:magia-fractalsync-2025][src:gemmini-berkeley-eecs2022] The RISC-V AI accelerator ecosystem is converging on a pattern where: (1) each compute tile has a software-managed scratchpad, (2) DMA engines handle explicit data movement, (3) the coherent interconnect enables shared LLC access, and (4) synchronization is hardware-accelerated for bulk-synchronous parallel execution.

## Open Questions

- OPEN: Do full-scale RVV implementations (Ventana Veyron V2 production silicon) show the same bandwidth vs. VLEN scaling relationships predicted by the EPI FPGA study, or do real cache hierarchy effects change the picture?
- OPEN: As matrix extensions (AME/IME/VME) add dedicated tile registers with 2D load/store, how should the memory hierarchy adapt -- wider cache ports, separate matrix data paths, or shared vector/matrix bandwidth?
- OPEN: Will RISC-V ratify a vector prefetch instruction, or will hardware prefetchers and implicit vector-load prefetching remain the primary approach?
- OPEN: How does the RISC-V IOMMU overhead (context setup, TLB invalidation) compare to GPU IOMMU (NVIDIA's MIG/PCIe SR-IOV) for multi-tenant AI workloads?
- OPEN: The SpacemiT K1's observed >10% memory latency jitter in SPEC benchmarks requires investigation -- is it a microarchitectural issue in the L2 arbitration logic, or a fundamental property of cache-less L3 hierarchies?
- VERIFY: Characterize real DRAM bandwidth utilization for 256-bit/512-bit VLEN RVV silicon across a set of bandwidth-bound AI kernels (GEMM, attention, convolution).
- VERIFY: Add bandwidth utilization data from published Veyron V2 benchmarks once available.

## Related Concepts

- [[hw.riscv.vector-extension|RISC-V Vector Extension (RVV 1.0)]] -- parent concept; the compute substrate fed by this memory hierarchy
- [[hw.riscv.matrix-extension-proposals|RISC-V Matrix Extension Proposals]] -- matrix extensions that will impose 2D tile data movement on the same memory hierarchy
- [[hw.gpu.memory-hierarchy|GPU Memory Hierarchy]] -- comparison point for bandwidth, cache, and scratchpad design
- [[hw.gpu.tensor-memory-accelerator|Tensor Memory Accelerator]] -- comparison point for asynchronous data movement mechanisms
- [[programmer.roofline-model|Roofline Performance Model]] -- measures whether RVV vector benefits are bottlenecked by compute or memory
- [[stack.ai-accelerator-ontology|AI Accelerator Ontology]] -- parent of the parent concept in the stack
