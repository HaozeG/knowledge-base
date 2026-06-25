---
id: hw.riscv.execution-architecture
title: RISC-V AI Execution Architecture
status: draft
layer: 70-execution-architecture
layer_path: 70-execution-architecture/riscv/execution-architecture
parent: hw.riscv.vector-extension
secondary_layers: [40-compute-substrate, 50-memory-data-movement, 100-runtime-execution-system]
granularity: concept
concept_type: execution_model
scale_scope: [unit, tile, die]
reasoning_roles: [abstraction, mapping, bottleneck]
tags: [riscv, execution, pipeline, microarchitecture, out-of-order, in-order, vector, multi-pe, warp, simt, ai, accelerator]
aliases: [RISC-V execution model, RISC-V core microarchitecture for AI, RVV pipeline architecture]
sources: [nvidia-cuda-programming-guide-v13.3, perotti-spatz-ieee-tcad-2025, shen-mempool-spatz-date-2025, montagna-copiftv2-arxiv-2026, garcia-llm-rvv-sophgo-2025, ventana-veyron-v2-rvv-2023, riscv-v-spec-ratified-2021, wang-das-kilo-core-arxiv-2025, burrello-multivic-arxiv-2025, tenstorrent-metal-runtime-2026]
---

# RISC-V AI Execution Architecture

## First-Principle Explanation

Executing an AI kernel on silicon is a scheduling problem across two dimensions: **time** (pipeline depth, instruction-level parallelism within a core) and **space** (data-level parallelism across vector lanes and multiple PEs). The RISC-V ecosystem spans the full trade-space:

```text
Throughput ∝ (instructions per cycle) × (data elements per instruction) × (PE count) × utilization
utilization ∝ min(frontend_feed_rate, backend_execution_rate, data_supply_rate)
```

The first-principle organizer is **how the architecture resolves the tension between programmability and throughput**:

- **GPU SIMT**: hardware-managed threads hide latency; programmer writes scalar threads, hardware groups into warps. Throughput comes from massive thread count, not from wide per-thread vectors.
- **RISC-V in-order vector**: software-managed vectors with explicit length control; programmer writes vector code, hardware executes lane-by-lane. Throughput comes from vector width and chaining, not from OoO instruction reordering.
- **RISC-V OoO vector**: hardware reorders both scalar and vector instructions; throughput comes from ILP + DLP combined. The cost is area and power — OoO vector cores can be 2–3× larger than in-order equivalents at the same VLEN.
- **RISC-V many-core spatial**: many small in-order cores with local scratchpads, coordinated by explicit message passing. Throughput comes from core count, not per-core width.

- [supported][src:riscv-v-spec-ratified-2021] The RVV 1.0 specification defines vector-length-agnostic (VLA) execution: software sets the application vector length (AVL) via `vsetvli`, and hardware executes with its native VLEN. This decouples software from hardware width — the same binary runs on a 128-bit embedded core and a 8192-bit HPC machine.
- [supported][src:perotti-spatz-ieee-tcad-2025] Spatz demonstrates that a compact 2-KiB latch-based VRF enables efficient in-order vector execution with 96.6% FPU utilization on matrix multiply — proving that in-order vector cores can achieve high utilization without OoO hardware.
- [supported][src:montagna-copiftv2-arxiv-2026] COPIFTv2 shows that lightweight hardware queues between integer and FP threads improve PE dispatch latency by 1.49×, demonstrating that execution coordination overhead is a first-order bottleneck for multi-PE RISC-V systems.

## The Execution Model Spectrum

RISC-V AI systems span four execution models, each trading off different resources:

| Execution Model | Issue Width | Vector Width | Pipeline Depth | Scheduling | Area per Core | Best For | Example |
|---|---|---|---|---|---|---|---|
| **In-order narrow vector** | 1–2 | 128–256 bit | 4–8 stages | Static, compiler-scheduled | ~0.1–0.5 mm² | Edge inference, DSP | SiFive X280, Snitch |
| **In-order wide vector** | 1–2 | 512–2048 bit | 5–10 stages | Static + hardware chaining | ~0.5–2 mm² | HPC vector, batched GEMM | Ara, Vitruvius, Spatz |
| **Out-of-order wide vector** | 3–8 | 128–512 bit | 12–15 stages | Dynamic, hardware OoO + vector | ~3–10 mm² | Datacenter CPU + AI | Ventana Veyron V2/V3, T-Head C910 |
| **Many-core spatial (in-order)** | 1 | 256–512 bit | 3–5 stages | Explicit message passing | ~0.05–0.2 mm² per core | Massively parallel AI | Esperanto ET-Minion, Tenstorrent Tensix |

- [speculative] The four models are not competitors — they form a Pareto frontier. In-order narrow vector minimizes area/energy per operation but caps per-thread throughput. OoO wide vector maximizes single-thread throughput but wastes area on speculative hardware that AI kernels rarely use. Many-core spatial maximizes aggregate throughput per mm² but requires explicit data distribution that complicates programming.
- [speculative] The critical insight: AI matrix kernels are **control-regular** — the same instruction sequence repeats billions of times with different data. This means the branch predictor, register renaming, and scheduler of an OoO core are largely idle during GEMM, while the vector lanes are saturated. An in-order core with good vector chaining can achieve the same vector utilization at 1/3 the area.

## Vector Pipeline Microarchitecture

RISC-V vector units universally adopt a **lane-based microarchitecture** where the vector register file is split across lanes, each lane containing one element of each vector register.

### Lane Organization

- [supported][src:riscv-v-spec-ratified-2021] The RVV spec defines VLEN (total vector register width in bits) and DLEN (datapath width per lane). A VLEN=512, DLEN=64 implementation has 8 lanes, each processing 64 bits per cycle. Vector instructions with SEW=32 process 2 elements per lane per cycle; SEW=8 processes 8 elements per lane per cycle.
- [inference] The lane-based organization is not just an implementation convenience — it is the architectural key to VLA. Wider VLEN = more lanes, not wider per-lane datapaths. Software written for VLEN=128 runs correctly on VLEN=8192 by simply processing more elements per instruction.

### Vector Chaining

Vector chaining is the RISC-V equivalent of GPU operand forwarding: the result of one vector instruction feeds directly into the next without round-tripping through the VRF.

- [speculative] Without chaining, a vector multiply-add sequence (vmul.vv → vadd.vv) requires:
  1. Write all vmul results to VRF (VLEN elements)
  2. Read all results back as vadd operands
  This doubles VRF bandwidth pressure and adds pipeline bubbles equal to the vector pipeline depth.

- [speculative] With chaining, the first element result from the multiplier feeds directly into the adder on the next cycle, creating a fused multiply-add pipeline across instructions. The VRF read/write bandwidth is halved, and pipeline bubbles are eliminated. T1 (Torrent-1) implements full Load→Exec→Store→Load chaining across 4 VFU slots per lane.

### Stripmining and LMUL

- [supported][src:riscv-v-spec-ratified-2021] Stripmining is the canonical RVV loop pattern: `vsetvli` sets VL to min(AVL, VLMAX), the vector body executes, then remaining elements are decremented. When remaining < VLMAX, the hardware processes fewer elements in the final iteration — naturally, without predication or conditional execution.
- [speculative] LMUL (vector register grouping) is the mechanism that allows vector register files to be shared across different SEW without wasted capacity. At LMUL=8, a single vector instruction operates across 8 concatenated registers, giving effective vector lengths up to VLEN×8/SEW elements. This is critical for matrix operations where operand reuse demands long vectors.

### Pipeline Depth Tradeoff

- [inference] Pipeline depth in vector units is dominated by the VFU (Vector Functional Unit) latency, not the frontend. A 4-stage frontend (fetch, decode, issue, read) followed by an 8-cycle VFU pipeline (multiply) gives a 12-stage effective depth for vector multiply. Deepening the VFU pipeline (to hit higher clock frequency) increases the chaining penalty — each additional VFU stage that can't be bypassed adds a bubble cycle between dependent vector instructions.

## Multi-PE Execution Coordination

When multiple RISC-V PEs share a matrix workload, execution coordination becomes the dominant utilization limiter. The problem is analogous to GPU warp scheduling but implemented in software or lightweight hardware rather than a hardware warp scheduler.

### Coordination Patterns

| Pattern | Mechanism | Latency (cycles) | PE Utilization Ceiling | Example |
|---|---|---|---|---|
| **Barrier synchronization** | Shared-memory barriers | 10–50 | ~70% at 256 PEs | MultiVic |
| **Queue-based dispatch** | Hardware producer-consumer queues | 2–5 | ~90% at 4 PEs | COPIFTv2 (Snitch) |
| **DMA + semaphore** | DMA completion interrupts or polling | 50–200 | ~60% at 16 PEs | Spatz cluster |
| **Dataflow triggering** | PE starts on data arrival | 1–3 | ~95% at 1024 PEs | MemPool-Spatz (theoretical) |

- [supported][src:montagna-copiftv2-arxiv-2026] COPIFTv2 adds two hardware queues per Snitch core: one for integer→FP work dispatch, one for FP→integer completion. This enables the control core to queue the next GEMM tile while the FP unit executes the current tile, effectively hiding dispatch latency. The 1.49× speedup demonstrates that dispatch coordination — not compute throughput — is the bottleneck for small multi-PE clusters.
- [supported][src:wang-das-kilo-core-arxiv-2025] At 1024-PE scale (MemPool), static coordination breaks down: bank conflicts from synchronized PE access patterns reduce utilization to ~50%. DAS restores utilization to 81% by dynamically remapping PE-to-bank assignments at runtime.
- [inference] The coordination cost grows with PE count: O(N) for barrier-based, O(log N) for tree-reduce, and O(1) for dataflow-triggered (but dataflow-triggered requires hardware support not present in standard RISC-V cores).

### Comparison with GPU Warp Scheduling

- [supported][src:nvidia-cuda-programming-guide-v13.3] A GPU SM has a hardware warp scheduler that manages 64+ warps per SM, context-switching between warps on every cycle to hide memory latency. Each warp context (PC, register file slice) is pre-allocated in hardware.
- [inference] RISC-V multi-PE systems lack hardware warp scheduling. Instead, they rely on one of two approaches:
  1. **Software-managed parallelism** (Esperanto, MultiVic): the compiler or runtime statically partitions work across PEs; PEs execute independently without dynamic context switching.
  2. **Lightweight hardware dispatch** (Tenstorrent Tensix, COPIFTv2): hardware queues or triggers coordinate PE work without full thread-level context switching.
- [speculative] The absence of hardware warp scheduling is simultaneously RISC-V's biggest weakness (higher coordination overhead, lower utilization on irregular workloads) and its biggest strength (no area/power cost for warp state, enabling more PEs per mm²). For regular AI kernels, the area efficiency of many simple in-order PEs beats the utilization advantage of GPU SMs.

## Real-World Implementations

### Tenstorrent Tensix — Many-Core Spatial with Hardware Dispatch

- [speculative] Each Tensix tile contains 5 "Baby RISC-V" cores (RV32IM, single-issue in-order, ~1 GHz): one master (Brisc), three compute-phase specialists (Trisc T0/T1/T2 for Unpack/Math/Pack), and one NoC DMA handler (Ncrisc). This is not general-purpose multi-core — it's a **phase-specialized execution pipeline** where each core owns one stage of the tensor compute pipeline.
- [speculative] The MOP Expander in the Tensix frontend expands single instructions into thousands of micro-operations — this is the key mechanism that bridges RISC-V's narrow issue width with the wide backend (Matrix Unit: 4.096 TFLOP/s, Vector Unit: 32-lane SIMD). The Replay Expander repeats instruction sequences up to 32×, effectively turning a loop into a hardware-unrolled pipeline.
- [inference] The Tensix execution model is a hybrid: RISC-V cores provide the control plane (programmable, debuggable, standard ISA), while the MOP/Replay expanders and backend units provide the data plane (high-throughput, fixed-function). This separation is architecturally elegant — the control plane changes rarely (once per layer), the data plane runs at full throughput.

### Ventana Veyron V2/V3 — OoO Wide Vector with Macro-Op Fusion

- [speculative] Ventana Veyron V3 deploys 16 execution pipelines per core: 5 integer, 3 load/store, 3 scalar FP, and 5 vector/matrix. At 4.2 GHz with FP8 support, it delivers 24 TFLOPS/core — equivalent to ~3 NVIDIA H100 SMs in a single CPU core.
- [speculative] The macro-op fusion engine dynamically encodes 1–5 RISC-V instructions into a single internal macro-op. For AI workloads, this means frequent instruction pairs (vload + vmul, vmul + vadd) become single macro-ops, effectively doubling the frontend bandwidth for vector code. The 200+ entry scheduler buffers these macro-ops, providing enough ILP window to overlap vector execution with scalar control flow.
- [inference] Veyron V3's 5 vector/matrix pipes are the widest vector execution backend in any announced RISC-V core. The design point — 4.2 GHz, 16 pipelines, macro-op fusion — competes directly with Arm Neoverse V3 and AMD Zen 5 in the datacenter CPU market, while adding AI-specific matrix throughput that general-purpose server CPUs lack.

### Esperanto ET-Minion — Massively Parallel In-Order Vector

- [speculative] The ET-Minion core is a single-issue in-order RISC-V core with a 512-bit vector/tensor unit delivering 128 INT8 ops/cycle. 1,088 Minion cores per chip at ~25W total power. The execution model is pure MIMD: each core runs its own instruction stream, coordinated through shared memory.
- [speculative] The architectural bet: for regular AI kernels, 1,000 simple in-order cores at 25W deliver more aggregate throughput than 10 complex OoO cores at 25W. The bet paid off for CNNs (near-linear scaling demonstrated) but broke down for large transformer models where the 132 GB/s memory bandwidth became the bottleneck before core count mattered.
- [inference] Esperanto's failure illustrates the execution architecture's dependency on memory hierarchy: a brilliant execution model is useless if the memory system can't feed it. The 1,088 Minion cores were starved — the execution architecture was overprovisioned relative to the memory architecture.

### SiFive X-Series and T-Head C910 — Mid-Range Execution

- [speculative] SiFive X280 (in-order, 8-stage, dual-issue scalar, 128-bit vector with decoupled vector pipeline) targets edge AI/DSP where deterministic execution matters more than peak throughput. T-Head C910 (12-stage OoO, 3-issue, 8-execution pipes, dual 128-bit vector) targets higher-end embedded and entry server.
- [inference] The X280 and C910 represent the "good enough" middle of the execution spectrum — they provide RVV compatibility for AI kernels without the area/power cost of Veyron-class OoO or the programming complexity of Tensix-class many-core. For edge inference at batch=1, their execution capability is well-matched to the memory bandwidth available.

## Execution Architecture vs. Memory Wall

- [inference] The execution architecture cannot be evaluated independently of the memory hierarchy. A simple model:
  ```text
  effective_throughput = min(peak_compute_throughput, memory_bandwidth / arithmetic_intensity)
  ```
  For matrix multiply (AI ≈ N/3 for dimension N), the memory wall hits at:
  - 128-bit RVV @ 1 GHz: ~256 GFLOP/s FP16, memory wall at ~800 GB/s for N=512
  - 512-bit OoO RVV @ 3 GHz: ~3 TFLOP/s FP16, memory wall at ~9 TB/s for N=512
  - 1024-core in-order @ 1 GHz: ~2 TFLOP/s FP16 (aggregate), memory wall at ~6 TB/s for N=512
- [speculative] Most RISC-V AI systems today are **compute-bound on paper but memory-bound in practice** because real matrix dimensions are smaller than roofline assumptions, and real memory bandwidth (especially for multi-PE shared L1) is well below peak.

## Open Questions

- OPEN: What is the optimal scalar-to-vector pipeline coupling? Decoupled (SiFive X280: scalar and vector pipelines operate independently) vs. tightly-coupled (Ventana Veyron: unified OoO scheduler manages both). Decoupled is simpler and more power-efficient; tightly-coupled enables ILP across scalar/vector boundaries for mixed AI+control workloads.
- OPEN: Can hardware chaining in RISC-V vector units ever match GPU operand forwarding efficiency? GPU SMs have register file bandwidth proportional to warp count; RISC-V VRF bandwidth is fixed per lane. For element-wise operations, chaining is equivalent; for reductions and permutations, GPU warp shuffle instructions have no RISC-V equivalent.
- OPEN: The Tensix phase-specialized execution model (separate cores for Unpack/Math/Pack) has no published academic comparison against unified-PE approaches (Spatz, Ara) at iso-technology. Is phase specialization worth the control complexity?
- OPEN: Macro-op fusion (Ventana V3) vs. wider decode (Ventana V2's 15-wide) — which approach delivers better energy efficiency for AI vector code? Fusion reduces frontend energy but adds fusion engine complexity; wider decode is simpler but burns more frontend power.
- VERIFY: Tenstorrent Tensix MOP Expander and Replay Expander details are from vendor documentation, not independent microarchitectural analysis.
- VERIFY: Ventana Veyron V3 24 TFLOPS/core FP8 is a vendor claim; independent benchmarking on AI kernels is not available.
- VERIFY: Esperanto ET-Minion 128 INT8 ops/cycle per core is from vendor documentation; independent microbenchmarks are unavailable since the RTL was open-sourced post-closure.
