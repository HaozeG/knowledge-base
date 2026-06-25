---
id: software.compiler.ml-compiler-lowering-riscv
title: ML Compiler Lowering for RISC-V AI Accelerators
status: draft
layer: 90-compiler-lowering-stack
layer_path: 90-compiler-lowering-stack/riscv/ml-compiler-lowering
parent: software.compiler.rvv-autovec-quality
secondary_layers: [80-programming-interface-dsl, 100-runtime-execution-system, 110-workload-mapping]
granularity: concept
concept_type: compiler_stack
scale_scope: [unit, tile, die]
reasoning_roles: [mapping, enabler, bottleneck]
tags: [mlir, tvm, iree, xla, compiler, riscv, rvv, lowering, tiling, microkernel, ai, ml, code-generation]
aliases: [RISC-V ML compiler, MLIR for RISC-V AI, TVM/IREE RISC-V backend, AI compiler lowering for RVV]
sources: [ahmad-iree-riscv-arxiv-2025, ethz-mlir-snitch-cgo-2025, sifive-ai-ml-stack-riscv-2025, ieie-iree-bytecode-riscv-2026, greenblatt-tvm-rvv-autotune-2026]
---

# ML Compiler Lowering for RISC-V AI Accelerators

## First-Principle Explanation

Getting a PyTorch model to run efficiently on RISC-V vector hardware requires a multi-level compiler stack. The first-principle challenge is the **representation gap**:

```text
PyTorch op (high-level, dataflow)  →  MLIR/TVM dialect (mid-level, structured)  →  LLVM IR (low-level, SSA)  →  RISC-V machine code (ISA-specific)
```

Each lowering step must preserve semantics while exposing optimization opportunities. The gap between "matrix multiply" (one PyTorch call) and "RVV vfmacc with LMUL=8, VLEN=256, strip-mined in 4 loops" is enormous — and filling it correctly is the compiler's job.

The organizer's insight: **ML compiler lowering is not just code generation — it is a search problem over tiling dimensions, loop orders, vector widths, and memory layouts**. The compiler must find the combination that maximizes utilization for a specific hardware target, and the search space is combinatorially large (typically 10⁶-10⁹ valid configurations for a single matmul).

- [supported][src:ahmad-iree-riscv-arxiv-2025] Enabling RISC-V microkernel support in IREE achieved **50× single-thread decode improvement** and **17× multi-thread improvement** on a MILK-V Jupiter board (VLEN=256, 8 cores) running Llama-3.2-1B. The key technique: VLEN-aware tiling where M,N,K dimensions are chosen as (6, VLEN/4, 1) for prefill and (1, VLEN/8, 1) for decode.
- [supported][src:ethz-mlir-snitch-cgo-2025] A multi-level MLIR compiler backend for RISC-V with Snitch extensions achieved **90% FPU utilization** on representative ML kernels. The structured, abstraction-driven backend methodology combines domain knowledge (tiling, vectorization) with hardware-specific ISA encoding.
- [supported][src:sifive-ai-ml-stack-riscv-2025] SiFive's production AI/ML stack uses IREE + SiFive LLVM compiler + SiFive Kernel Library (SKL), demonstrating end-to-end PyTorch → ONNX → IREE → RVV deployment for BEV perception and LLM inference on the SiFive XM platform.

## The ML Compiler Stack

### Compiler Options for RISC-V AI

| Compiler | IR | Strengths for RISC-V | Limitations |
|---|---|---|---|
| **IREE (MLIR-based)** | MLIR (linalg, vector, SCF) | VLEN-aware tiling, microkernel library, upstream LLVM RISC-V backend | Requires hand-authored microkernels for peak performance |
| **TVM** | Relay / TIR | Auto-tuning (AutoTVM/AutoScheduler), BYOC for custom accelerators | RISC-V backend maturity lags x86/ARM; auto-tuning overhead |
| **XLA (OpenXLA)** | HLO → LLVM | Google-maintained, battle-tested on TPU/GPU | RISC-V support is community-driven, not first-class |
| **MLIR (bare)** | Custom dialects | Maximum flexibility, can target any RISC-V ISA extension | Requires building the entire lowering pipeline from scratch |
| **GLOW (PyTorch)** | Glow IR → LLVM | Facebook-maintained, ONNX → Glow path | RISC-V support minimal; mostly ARM/x86 focused |

### IREE/MILR Pipeline

- [supported][src:ahmad-iree-riscv-arxiv-2025] IREE's lowering pipeline for RISC-V:
  1. **linalg.matmul** (high-level structured op) → decomposed into **linalg.mmt4d** (4D matrix multiply-tile op)
  2. **linalg.mmt4d** → tiled with M,N,K determined by VLEN: M₀=6, N₀=VLEN/4, K₀=1 for prefill batch GEMM
  3. Tiled linalg → **vector dialect** → vectorized RVV intrinsics with explicit LMUL and SEW
  4. Vector dialect → **LLVM IR** with RISC-V vector instructions → **RISC-V machine code**
- [speculative][src:ahmad-iree-riscv-arxiv-2025] The VLEN-aware tiling strategy is the critical optimization: tiling for VLEN=256 produces matrices sized to exactly fill a vector register group, eliminating tail-predicated elements in the inner loop. For VLEN=128, the same binary would use different tile sizes — but RVV's VLA property means no recompilation is needed, only retuning of tile parameters.

### TVM/AutoTVM Approach

- [supported][src:greenblatt-tvm-rvv-autotune-2026] TVM's auto-tuning approach for RISC-V vector targets: AutoTVM/AutoScheduler explores the tiling space (M, N, K tile sizes, loop order, unroll factors, vector width) using simulated annealing or XGBoost-guided search. For RVV targets, the search is constrained by VLEN, LMUL range, and available vector register count.
- [speculative][src:greenblatt-tvm-rvv-autotune-2026] The auto-tuning cost (hours to days of on-device or simulator measurement) is a barrier to rapid deployment. IREE's hand-authored microkernel approach (pre-tuned libraries like SKL) trades auto-tuning time for engineering time — a reasonable trade when the hardware target is fixed (SiFive XM platform) but less scalable to diverse RISC-V implementations.

### Multi-Level Lowering Architecture

- [supported][src:ethz-mlir-snitch-cgo-2025] The ETH Zürich approach demonstrates a structured, multi-level methodology:
  1. **High-level dialect** (linalg): hardware-agnostic tiling, fusion, and bufferization
  2. **Mid-level dialect** (custom Snitch ops): hardware-specific but ISA-agnostic — encodes FREP (floating-point repetition) and SSR (stream semantic registers) concepts
  3. **Low-level dialect** (LLVM + Snitch intrinsics): ISA-specific encoding, register allocation, instruction scheduling
- [inference] This three-level separation is architecturally elegant: level 1 is reusable across any RISC-V target, level 2 encodes the accelerator's unique capabilities (SSR, FREP, DMA), and level 3 handles the messy details of instruction encoding. The separation allows a new RISC-V accelerator (e.g., IME with outer-product) to reuse levels 1 and 3 while only customizing level 2.

## VLEN-Aware Tiling

- [inference] VLEN-aware tiling is the central technique for RISC-V AI compilation. The principle: choose tile dimensions such that each inner dimension is a multiple of VLMAX (VLEN/SEW × LMUL). For VLEN=256, SEW=32, LMUL=4: VLMAX = (256/32) × 4 = 32 elements. A tile of 32×32 elements exactly fills one vector register group.
- [speculative] The tile size constraint creates a discrete optimization problem: for given matrix dimensions (M, N, K), find tile sizes that are (a) multiples of VLMAX, (b) fit in the available register file (32 vector registers), and (c) maximize arithmetic intensity. The constraint (b) is often the binding one — a 32×32 tile requires 2×32² = 2,048 elements of register storage, which at SEW=32 requires 2,048/32 = 64 vector registers — exceeding the 32-register limit. Practical tiles are typically 16×16 or smaller.

## IREE RISC-V Deployment Performance

- [supported][src:ieie-iree-bytecode-riscv-2026] A lightweight IREE bytecode interpreter for 32-bit RISC-V (Rocket-SoC, 256 KB memory) achieved **21.14× performance improvement** on MNIST with microkernel optimization. Deployment size was **6.39× smaller than official IREE** and **16.52× smaller than TVM runtime** — critical for embedded RISC-V AI where memory is the binding constraint.
- [speculative] The 16× size advantage over TVM runtime comes from IREE's bytecode representation: TVM's runtime includes a full graph executor and operator library, while IREE's bytecode is a compact VM instruction stream that the runtime interprets. For edge AI on resource-constrained RISC-V SoCs (SpacemiT K1, SOPHGO SG2042), the deployment size difference determines whether a model fits at all.

## Open Questions

- OPEN: Will IREE or TVM become the dominant ML compiler for RISC-V AI? IREE has momentum (SiFive, 10xEngineers, upstream LLVM) and a cleaner architecture, but TVM's auto-tuning and broader hardware support (VTA, BYOC) give it reach. The answer may depend on whether RISC-V AI hardware converges on a few standard platforms (favoring IREE's hand-tuned microkernel approach) or remains diverse (favoring TVM's auto-tuning).
- OPEN: How will matrix ISA extensions (AME/IME/VME) change the compiler lowering problem? Matrix extensions raise the abstraction level — a single matrix-multiply instruction replaces dozens of vector instructions — but require the compiler to reason about 2D tile registers rather than 1D vector registers. The IREE lowering pipeline will need a new dialect between linalg and vector for matrix tiles.
- OPEN: Can MLIR's linalg dialect express all AI kernels efficiently, or will custom dialects always be needed for peak performance? The Snitch SSR/FREP extensions required custom MLIR ops — suggesting that ISA-specific dialects will remain necessary for non-standard hardware features.
- VERIFY: IREE RISC-V 50× decode improvement was measured on Llama-3.2-1B (a small model); scaling to 7B+ models may show different bottlenecks (memory bandwidth, not compute).
- VERIFY: SiFive's end-to-end PyTorch → XM platform deployment is demonstrated but performance numbers are vendor-provided, not independently benchmarked.
