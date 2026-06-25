---
id: hw.riscv.vector-extension
title: RISC-V Vector Extension (RVV 1.0)
status: draft
layer: 40-compute-substrate
layer_path: 40-compute-substrate/riscv/vector-datapath
parent: stack.ai-accelerator-ontology
secondary_layers: [70-execution-architecture, 90-compiler-lowering-stack]
granularity: mechanism
concept_type: architecture_pattern
scale_scope: [unit, tile, die]
reasoning_roles: [enabler, mapping]
tags: [riscv, vector, rvv, vla, simd, ai, ml, open-isa]
aliases: [RVV 1.0, RISC-V V extension, vector-length-agnostic]
sources: [riscv-v-spec-ratified-2021, lee-isc23-rvv-overview, perotti-rvv-embedded-ml-2024, gupta-conv-rvv-chalmers-2023, garcia-llm-rvv-sophgo-2025, tan-opt-sparse-matrix-rvv-2025, greenblatt-tvm-rvv-autotune-2026, esperanto-risc-v-ai-2021, ventana-veyron-v2-rvv-2023, tenstorrent-ocelot-rvv-2024, siFive-ame-proposal-2025, ventus-gpgpu-whitepaper]
---

# RISC-V Vector Extension (RVV 1.0)

## First-Principle Explanation

The RISC-V Vector Extension (RVV 1.0) is a ratified instruction set extension that adds vector processing capability to the RISC-V ISA. Its central design choice is **vector-length-agnostic (VLA) execution**: code is written independently of the hardware vector length (VLEN), and the same binary runs on implementations with VLEN ranging from 128 bits to 65536 bits.

The first-principle constraint is a tradeoff between generality and specialization:

```text
vector-length-agnostic ISA -> software portability across hardware generations
implementation-defined VLEN + runtime length configuration -> no compile-time fixed width, no static optimization certainty
```

RVV provides a flat register file of 32 vector registers (v0-v31), each VLEN bits wide. The programmer or compiler configures three key parameters at runtime via the `vsetvli` instruction:

| Parameter | Meaning | Effect |
|-----------|---------|--------|
| **SEW** (Selected Element Width) | Element width in bits (8, 16, 32, 64) | Determines number of elements per register for a given VLEN |
| **LMUL** (Register Grouping) | Groups of 1, 2, 4, or 8 registers (also fractional 1/2, 1/4, 1/8) | Controls the ratio of architectural registers vs. per-instruction data width |
| **VL** (Vector Length) | Runtime-set active vector length | Dynamic strip-mining: processes min(ApplicationVL, VLMAX) elements per iteration |

The hardware defines VLMAX = LMUL x VLEN / SEW. The `vsetvli` instruction returns VL = min(AVL, VLMAX), enabling automatic remainder handling without scalar tail loops.

Mask registers use v0 as the default mask. Every vector instruction can optionally be masked (using the `vm` field in encoding), with tail and mask agnostic/undisturbed policies (`ta`/`tu`, `ma`/`mu`) set via the `vtype` CSR.

## How It Compares to GPU SIMT and Fixed-Width SIMD

**vs. Fixed-Width SIMD (x86 SSE/AVX, ARM NEON):**

Fixed-width SIMD encodes the vector width into the ISA. A new width (e.g., AVX-256 to AVX-512) typically requires new ISA extensions, new instruction encodings, and often recompilation. RVV and its VLA model eliminate this: the same binary runs on 128-bit and 4096-bit implementations. The cost is that every loop iteration pays the runtime `vsetvli` configuration overhead, and compiler auto-vectorization for VLA ISAs is less mature than for fixed-width SIMD.

**vs. SVE (ARM Scalable Vector Extension):**

Both RVV and ARM SVE use VLA design, but differ in details:

- RVV uses `vsetvli` for dynamic strip-mining; SVE uses predicate registers (`whilelt`) for loop control. RVV's approach eliminates scalar remainder loops, while SVE's predicate model is considered cleaner for compiler auto-vectorization.
- RVV uniquely offers LMUL register grouping (1x to 8x and fractional), allowing flexible register pressure management. LMUL > 1 bundles multiple registers for wider operations, which benefits throughput but complicates the "compile once, run anywhere" promise if LMUL is fixed at compile time.
- RVV's widening and narrowing instructions can break lane boundaries, adding microarchitectural complexity; SVE was designed with lane-bounded data routing.
- SVE has more mature compiler auto-vectorization support (GCC/LLVM); RVV's support is maturing rapidly but lags slightly.

**vs. GPU SIMT:**

RVV and GPU SIMT share a similar hardware substrate -- vector lanes executing a single instruction across multiple data elements. The key difference is the abstraction:

- SIMT presents a per-thread programming model with automatic warp grouping and hardware divergence handling. The programmer sees N independent threads; the hardware groups them.
- RVV presents an explicit vector model: the programmer/compiler manages vector length, masking, and strip-mining directly. There is no automatic divergence hardware; masking is explicit.
- Projects like Ventus GPGPU and Chengying (OpenGPGPU) bridge this gap by adding SIMT-stack divergence handling (branch/reconvergence instructions) on top of RVV, fixing VLEN to the warp size (typically 32 elements). This demonstrates that RVV can serve as the ISA substrate for a GPU-like SIMT implementation.
- SIMT uses warp switching for latency hiding; RVV uses deeply pipelined vector functional units with chaining.

## Key Microarchitectural Implications

- **SLEN = VLEN**: The RVV 1.0 spec requires the vector register file to be byte-consecutive (SLEN = VLEN). This simplifies the programming model but adds complexity to lane-based microarchitectures for data routing across lanes.
- **LMUL and data routing**: LMUL > 1 requires forwarding data across register bundles within a single cycle or pipeline stage, increasing routing congestion at wider implementations.
- **Cross-lane operations**: Instructions like `vrgather` (gather from arbitrary elements) and widening/narrowing ops that cross lane boundaries require significant crossbar or multi-cycle routing, impacting clock frequency and area.

## Why It Matters for AI

RVV 1.0 is the ratified foundation on which the open RISC-V AI accelerator ecosystem is being built. It provides a standard, portable vector compute substrate that can scale from embedded inference (128-bit VLEN, Zve* subsets) to datacenter-class matrix engines (4096+ bit VLEN with LMUL grouping).

**Workload mapping:**

| AI Workload | RVV Mapping Quality | Notes |
|-------------|---------------------|-------|
| GEMM (dense MM) | Good | Strip-mined outer product with LMUL grouping. Paper results show 23x speedup over scalar for GEMM. Performance is shape- and arithmetic-intensity-dependent. |
| Conv (Conv2D/3D) | Good to Moderate | im2col+GEMM maps directly. Direct convolution scales well with long vectors. Winograd performs better at smaller VLEN. No single algorithm dominates across all layer shapes. |
| Attention (self-attention) | Moderate | QKV projection maps as GEMM. Softmax benefits from vector reductions. Scaled dot-product attention requires element-wise vector ops. Limited published analysis; early results show configuration-dependent benefit. |
| Embedding / Gather-Scatter | Moderate | Gather/scatter instructions exist but performance depends on access pattern regularity. Sparse operations need structured sparsity for efficiency. |
| Element-wise (ReLU, LayerNorm) | Excellent | Uniform vector operations with high arithmetic intensity per memory access. |

**Software ecosystem status:**

- LLVM and GCC both support RVV 1.0 auto-vectorization and intrinsics.
- Official C/C++ intrinsic API specification exists.
- TVM (Apache) has experimental RVV backend with MetaSchedule auto-tuning. Early results show 46% improvement over GCC auto-vec and 29% over muRISCV-NN for tensor programs.
- OpenBLAS, BLIS, and other numerical libraries have RVV-optimized kernels.
- TensorFlow Lite Micro has RVV-accelerated kernels (4x-28x over scalar; up to 25x over compiler auto-vec).
- The auto-vectorization quality gap vs. fixed-width SIMD (AVX/NEON) is narrowing but not closed.

**Vendor implementations in silicon:**

| Vendor | Chip | VLEN | Status |
|--------|------|------|--------|
| T-Head (Alibaba) | XuanTie C908 | 128-bit RVV 1.0 | Shipping |
| SpacemiT | K1 (Banana Pi BPI-F3) | 256-bit RVV 1.0 | Shipping |
| Esperanto | ET-SoC-1 Gen2 | RVV 1.0 + proprietary tensor | In development (planning) |
| Ventana (Qualcomm) | Veyron V2 | 512-bit RVV 1.0 + matrix | Announced 2023, planned 2026 |
| Tenstorrent | Wormhole / Blackhole | RVV 1.0 in Ocelot baby cores | Shipping |

Note: Esperanto's ET-SoC-1 Gen1 uses a pre-RVV proprietary vector/tensor extension; Gen2 will adopt RVV 1.0. Tenstorrent uses RVV 1.0 in control/coordination processors (Baby RISC-V cores), not the main tensor compute datapath.

## Related Concepts

- [[hw.gpu.simt|SIMT Execution Model]] -- competitor via abstraction, possible substrate for GPU-like execution on RISC-V
- [[hw.gpu.tensor-cores|Tensor Cores]] -- competitor for matrix/systolic specialization, possible complement via AME
- [[hw.gpu.overview|GPU Architecture Overview]] -- contrast for VLA vs. SIMT philosophy
- [[programmer.roofline-model|Roofline Performance Model]] -- measures whether RVV benefits are bottlenecked by compute or memory
- [[stack.ai-accelerator-ontology|AI Accelerator Ontology]] -- parent concept in the stack

## Open Questions

- VERIFY: Add in-depth comparison of RVV vs SVE2 compiler auto-vectorization quality across a standard benchmark suite (PolyBench, SPEC). Current evidence is from a single KTH thesis (2024).
- VERIFY: Characterize RVV performance on attention mechanisms (FlashAttention-style fused kernels). Only one 2025 paper evaluated LLM inference, and it used RVV 0.7.1 (pre-ratification).
- OPEN: Does fractional LMUL (LMUL < 1) provide measurable benefit in practice, or is it primarily a specification artifact?
- OPEN: How much area and power does cross-lane data routing consume in wide (512+ bit) RVV implementations vs. lane-bounded SVE or SIMT designs?
- OPEN: The RISC-V Matrix Extension has three competing proposals (SiFive AME "attached matrix", IME "integrated matrix", and VME "vector matrix"). Their status, convergence path, and timeline are unresolved. See source [siFive-ame-proposal-2025] for SiFive's position.
- TODO: Evaluate maturity of TVM/MLIR RVV backend for production ML workload deployment.
