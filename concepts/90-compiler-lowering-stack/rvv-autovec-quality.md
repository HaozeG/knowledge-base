---
id: software.compiler.rvv-autovec-quality
title: RVV vs SVE2 vs AVX-512 Compiler Auto-Vectorization Quality
status: draft
layer: 90-compiler-lowering-stack
layer_path: 90-compiler-lowering-stack/riscv/autovec-quality
parent: hw.riscv.vector-extension
secondary_layers: [40-compute-substrate, 80-programming-interface-dsl]
granularity: concept
concept_type: compiler_stack
scale_scope: [unit, tile]
reasoning_roles: [mapping, bottleneck]
tags: [riscv, rvv, sve2, avx512, autovectorization, gcc, llvm, compiler-quality, vla, vector-length-agnostic]
aliases: [RVV auto-vectorization quality, VLA compiler maturity comparison, RISC-V vector compiler gap]
sources: [modin-kth-rvv-autovec-2024, arras-gcc-rvv-vs-aarch64-cauldron-2025, luke-lau-llvm-rvv-improvements-2025, bataev-llvm-rvv-book-2026, multicoreware-valve-cross-isa-2025, risc-v-tsvc-hpc-sc25, arm-ssve-auto-vec-paper-2025, comparison-vec-x86-arm-2025, llvm-rvv-strided-loads-rise-2025, llvm-rvv-vp-gather-scatter-2025, arras-gcc-rvv-cost-model-tuning-2024, risc-v-llvm-rvv-summit-2025, greenblatt-tvm-rvv-autotune-2026, gcc-avx512-masked-vec-2023, ffmpeg-rvv-autovec-discussion-2025]
---

# RVV vs SVE2 vs AVX-512 Compiler Auto-Vectorization Quality

## First-Principle Explanation

Vector-length-agnostic (VLA) ISAs decouple the program from the hardware vector width. This portability comes at a compiler cost: the compiler cannot assume a fixed vector length and must generate dynamically strip-mined or predicated loops whose efficiency depends on the quality of code generation, cost modelling, and runtime dispatch mechanisms.

The compiler auto-vectorization problem for VLA ISAs has three fundamental axes:

1. **Coverage**: What fraction of vectorizable loops does the compiler recognize and transform?
2. **Code quality**: How close does the generated code come to the machine's roofline ceiling?
3. **Scalability**: Does the generated code benefit automatically from wider vector hardware, or must it be recompiled?

RVV (RISC-V Vector Extension), ARM SVE2, and x86 AVX-512 represent three points in this design space: RVV and SVE2 are VLA (with different strip-mining mechanisms), while AVX-512 is fixed-width with masking. Their compiler maturity levels differ significantly as of 2025-2026.

## Coverage: How Many Loops Can Each Compiler Vectorize?

The TSVC-2 benchmark suite (151 test cases covering common vectorization patterns) provides the most directly comparable coverage data:

| Architecture | Compiler | TSVC-2 Loops Vectorized | Source |
|---|---|---|---|
| ARM SVE | GCC | 115 / 151 (76%) | Brank & Pleiter / RuyiSDK |
| RISC-V RVV | GCC 14.2 | 96 / 151 (64%) | RuyiSDK replication study |
| x86-64 AVX2 | GCC 14.2 | 71 / 151 (47%) | RuyiSDK replication study |
| x86 (any SIMD) | GCC | ~54% | arXiv 2502.11906 (TSVC2) |
| x86 (any SIMD) | LLVM/Clang | ~46% | arXiv 2502.11906 (TSVC2) |
| ARM (any SIMD) | GCC | ~56% | arXiv 2502.11906 (TSVC2) |
| ARM (any SIMD) | LLVM/Clang | ~47% | arXiv 2502.11906 (TSVC2) |

[inference][src:risc-v-tsvc-hpc-sc25, comparison-vec-x86-arm-2025] RVV GCC covers ~64% of TSVC-2, trailing SVE GCC by ~12 percentage points (19 test cases). This gap represents loops that GCC's RVV backend fails to auto-vectorize but its SVE backend handles successfully.

[inference][src:comparison-vec-x86-arm-2025] GCC consistently exceeds Clang in vectorization coverage on both x86 (~54% vs ~46%) and ARM (~56% vs ~47%), suggesting GCC's vectorizer is more aggressive at recognizing vectorizable loop patterns regardless of target ISA.

**Important caveat**: TSVC-2 was designed for fixed-width SIMD and under-represents VLA-specific patterns (masked operations, predicated loops, segmented loads/stores, mixed-precision). The SC25 RISC-V workshop paper identifies that some RVV instructions have no corresponding TSVC-2 test case, meaning coverage metrics may underestimate true capability for VLA-relevant patterns.

## GCC vs LLVM Auto-Vectorization for RVV

[supported][src:modin-kth-rvv-autovec-2024] The KTH thesis comparing GCC 14 and LLVM 17 for RVV auto-vectorization found structural differences in code generation strategy:

| Dimension | LLVM 17 | GCC 14 |
|---|---|---|
| Vector-length mode | Tends to use specified (VLS) fixed vector length | Produces more vector-length agnostic (VLA) code |
| Scalability | Does not automatically scale to wider vectors | Scales naturally to wider vector units |
| Executed instructions | Better (fewer instructions) | Worse |
| Simulated cycles | Worse | Better (lower cycle count) |
| VLA-mode at medium VL | Better in instructions and cycles | Worse |
| VLA-mode at large VL | Gap narrows | Gap narrows |

[inference][src:modin-kth-rvv-autovec-2024] LLVM generates fewer instructions per loop but GCC generates better-scheduled code with fewer cycles. The VLS vs VLA choice is the key differentiator: VLS code may be faster on specific hardware but won't benefit from future wider vectors, undermining a core VLA promise.

[supported][src:luke-lau-llvm-rvv-improvements-2025] LLVM RVV auto-vectorization has improved significantly from Clang 17 to Clang 20. SPEC CPU 2017 on SpacemiT X60 shows 8.7% geometric mean improvement. Key improvements include:
- SLP vectorizer now supports non-power-of-two vectorization factors (e.g., RGB pixel size 3)
- Better bfloat16/FP16 support via Zvfbfmin/Zvfhmin
- vsetvli insertion moved after register allocation for more aggressive scheduling
- Initial tail folding support for strip-mined loops

## GCC RVV vs AArch64 SVE2: Quantified Gap

[supported][src:arras-gcc-rvv-vs-aarch64-cauldron-2025] The GNU Tools Cauldron 2025 presentation compared GCC 15.2 code generation for RISC-V (RVV) vs AArch64 (SVE2) on SPEC CPU 2017 with 256-bit vectors on QEMU. Key gap measurements:

| Metric | Observation |
|---|---|
| Dynamic instruction count (DIC) | RISC-V consistently higher |
| 507.cactuBSSN hot block | 6,563 RVV insns vs 3,104 SVE2 insns (+111%) |
| 549.fotonik3d hot block | 63 insns vs 42 insns (+50%) |
| 554.roms exp function | 6.21% runtime (scalar libm) vs 1.64% (vectorized libm) |

**Root causes identified:**

1. **Missing scaled addressing mode**: AArch64 can do `ld1w {z30.s}, p7/z, [x3, x0, lsl #2]` (base + index << scale) in one instruction; RISC-V needs separate `addi` + `vle32.v`. This is an ISA-level gap, not a compiler bug.

2. **LMUL_MAX tuning**: Using `--param riscv-autovec-lmul-max=dynamic` reduced DIC from 835B to 578B, substantially closing the gap. The default static LMUL setting was overly conservative.

3. **Missing vector-scalar fusion**: GCC 15.2 lacked patterns to fuse `vfmv.v.f` + `vfmmadd.vv` into `vfmmadd.vf`. A patch series has been merged, reducing DIC in 554.roms_r by -9% in the affected block.

4. **Scalar memset expansion**: AArch64 GCC expands memset inline (or uses MOPS instructions); RISC-V GCC emitted calls to scalar libc memset (46 insns vs 5). Patches submitted.

5. **Missing SIMD math library**: AArch64 has `libmvec` with vectorized `exp`, `sin`, etc.; RISC-V lacks this entirely. The 554.roms exp function scalar cost (6.21% runtime vs 1.64%) is directly attributable to this gap.

## Specific RVV Auto-Vectorization Quality Gaps

[supported][src:risc-v-tsvc-hpc-sc25] The SC25 RISC-V workshop paper and the LLVM dev meeting presentation identified specific TSVC kernels where auto-vectorization underperforms:

| TSVC Kernel | Performance Gap (Clang RVV vs best) | Root Cause |
|---|---|---|
| s231 | 16.5x worse | Loop interchange not performed |
| s2275 | 4.2x worse | Outer-loop vectorization missing |
| s1161 | 3.2x worse | If-conversion / control-flow handling |
| s3111 | 3.1x worse | Interleaving not applied |
| s31111 | 2.5x worse | SLP vectorization: FP reduction cost |
| s291 | 2.5x worse | Loop peeling not applied |
| s242 | 2.5x worse | Predictive commoning missing |
| s128 | 2.1x worse | Cost-model: scatter store handling |

[inference][src:risc-v-tsvc-hpc-sc25] When manual loop transformations (distribute + interchange) are applied, gaps widen dramatically: s2102 becomes 35.7x worse, s2275 becomes 22.3x worse under Clang. This indicates the compiler is leaving substantial performance on the table that manual optimization can recover.

[inference][src:arras-gcc-rvv-cost-model-tuning-2024] GCC's RVV cost model continues to be tuned. The `scalar_to_vec_cost` adjustment from 1 to 3 (January 2024) addressed over-vectorization of small loops. By comparison, AArch64 uses `scalar_to_vec = 4` and `vec_to_scalar = 4` with regular operation cost of 2, suggesting AArch64's more conservative defaults produce better heuristics.

## How TVM/MLIR Changes the Picture

[supported][src:greenblatt-tvm-rvv-autotune-2026] A 2025 paper integrates RVV into TVM's MetaSchedule auto-tuning framework. Results on 256-bit RVV 1.0 silicon (Banana Pi BPI-F3 / SpacemiT K1):

| Comparison | Improvement |
|---|---|
| TVM + MetaSchedule vs GCC auto-vec | 46% mean latency improvement |
| TVM + MetaSchedule vs muRISCV-NN hand-tuned | 29% improvement for single matmul |
| TVM + MetaSchedule vs LLVM auto-vec | 35% average improvement |

[supported][src:luke-lau-llvm-rvv-improvements-2025] MLIR-based approaches change the picture in three ways:

1. **Higher-level optimization**: MLIR dialects (Linalg, Vector, SCF) allow loop transformations (tiling, fusion, distribution) at a higher abstraction level, bypassing the loop vectorizer's pattern-matching limitations. The 16.5x gap on loop interchange in s231 would be addressed at the MLIR level, not at the LLVM/GCC backend.

2. **Auto-tuning replaces static heuristics**: TVM's MetaSchedule uses probabilistic program search to find optimal tile sizes, vectorization factors, and loop orders for each kernel-hardware pair. This bypasses the compiler's static cost model, which is the main source of suboptimal code generation.

3. **Gap still exists for irregular patterns**: Auto-tuning matches or exceeds hand-tuned libraries for regular tensor programs (GEMM, Conv2D), but irregular patterns (gather/scatter, sparse, dynamic shapes) remain challenging for both MLIR-based and traditional approaches.

[inference][src:greenblatt-tvm-rvv-autotune-2026, risc-v-tsvc-hpc-sc25] TVM/MLIR addresses the coverage gap by applying vectorization at a higher IR level where loop structure is explicit, rather than relying on the backend vectorizer to re-discover it from lowered code. However, auto-tuning cost (minutes to hours per kernel) and lack of dynamic shape support limit production deployment.

## Comparison with AVX-512 Fixed-Width Auto-Vectorization

[supported][src:comparison-vec-x86-arm-2025] AVX-512 auto-vectorization is the most mature of the three ISAs due to decades of x86 compiler investment, but has its own gaps:

- GCC covers ~54% of TSVC-2 on x86 vs ~46% for Clang
- All compilers avoid 512-bit ZMM registers on Intel hardware by default due to frequency/voltage penalties (up to 50us voltage transitions); full-width vectorization requires explicit `-mprefer-vector-width=512`
- GCC 14 introduced fully masked vectorization for AVX-512 (`--param vect-partial-vector-usage=2`), enabling small-trip-count loop vectorization without scalar epilogues - not yet enabled by default
- AVX-512 masked operations are structurally similar to SVE predication, making GCC's SVE backend more transferable to RVV than the AVX-512 backend

[supported][src:gcc-avx512-masked-vec-2023] GCC's AVX-512 fully masked vectorization (commit r14-1925) uses integer-mode masks from vector compares rather than SVE-style `while_ult` predicates. This architectural difference means RVV's mask model (v0 default mask register) is closer to AVX-512's masking than to SVE's predication, complicating the reuse of SVE-tuned compiler passes.

## Runtime Dispatch Limitation

[supported][src:ffmpeg-rvv-autovec-discussion-2025] A key cross-cutting limitation: neither GCC nor LLVM can do runtime dispatch for VLA ISAs. The FFmpeg-devel discussion (May 2025) confirms that both compilers "remain incapable of selecting optimized loops depending on runtime CPU capabilities" for RVV/SVE. This means:

- RVV code must be compiled with a minimum VLEN assumption unless using intrinsics with explicit strip-mining
- SVE2 code similarly lacks runtime vector-length dispatch
- In contrast, x86 AVX-512 can use CPUID feature detection with function multiversioning (`target_clones`)
- TVM/MLIR's auto-tuning partially addresses this via compiled kernel variants selected at runtime

## Open Questions

- OPEN: Does the RVV auto-vec gap vs SVE2 narrow to <5% with GCC 16/LLVM 22? Current trajectory suggests 1-2 release cycles to parity for common patterns.
- OPEN: Will a RISC-V vector math library (analogous to libmvec) materialize from the RISE project or academia? This is the single largest remaining gap for HPC workloads.
- OPEN: Can TVM/MLIR's higher-level approach fully bypass backend auto-vectorization quality gaps, or does the backend cost model remain limiting for irregular patterns?
- VERIFY: How does the SpacemiT X60 and Ventana Veyron V2 silicon performance correlate with QEMU-based cycle estimates in published comparisons?
- OPEN: Will the RISC-V matrix extension (IME/VME) change the compiler quality landscape by making vectorization less critical for the most compute-intensive kernels?
