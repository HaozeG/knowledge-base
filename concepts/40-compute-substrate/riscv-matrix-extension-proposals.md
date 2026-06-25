---
id: hw.riscv.matrix-extension-proposals
title: RISC-V Matrix Extension Proposals
status: seed
layer: 40-compute-substrate
layer_path: 40-compute-substrate/riscv/matrix-datapath
parent: hw.riscv.vector-extension
secondary_layers: [50-memory-data-movement, 110-workload-mapping, 140-performance-cost-utilization-model]
granularity: mechanism
concept_type: architecture_pattern
scale_scope: [unit, tile]
reasoning_roles: [enabler, claim_to_verify]
tags: [riscv, matrix, ame, ime, vme, ai, ml, outer-product, hpc]
aliases: [RISC-V Matrix Extensions, Zvma, Zvopmm, Zvvm]
sources: [riscv-ame-tg-charter, sifive-zvma-proposal-2024, sifive-zvma-slides-2025, riscv-ame-mailing-list-2025, riscv-ime-spec-draft, riscv-ime-ratification-plan, riscv-ime-mailing-list-2025, riscv-vme-charter, riscv-vme-ratification-plan, riscv-ame-vme-poll-2025, riscv-tsc-gap-analysis-2025, riscv-matrix-blog-alibaba, t1-zvma-microarchitecture-2025, arm-sme-introduction-blog, arm-sme-learning-paths, riscv-summit-matrix-session-2024, nvidia-a100-architecture-whitepaper-2020]
---

# RISC-V Matrix Extension Proposals

## First-Principle Explanation

Matrix multiplication occupies a unique place in the compute spectrum: it is regular enough to be specialized, and data-intensive enough that specialization matters. A single MxK-by-KxN matrix multiply performs O(MKN) multiply-accumulate operations on O(MK + KN) elements, giving an arithmetic intensity that grows with matrix size. The first-principle constraint is a fundamental tension between **data movement cost** and **compute density**:

- Outer-product formulation: loading two N-element vectors produces N^2 multiply-accumulates (data reuse ratio of N:2 in the inner loop)
- Systolic execution: data flows through a 2D array of processing elements, maximizing local reuse
- The same data element is used many times; capturing this reuse in the ISA avoids re-fetching from memory or even from a general-purpose register file

Specialized matrix units exploit this by providing:
- **higher throughput per watt** (dedicated datapaths, lower instruction-fetch overhead per operation)
- **mixed-precision accumulation** (widening accumulators without additional architectural complexity)
- **explicit tiling and data movement** (the ISA or API manages the dataflow, not the programmer)

## Overview

The RISC-V ecosystem has three competing proposals for adding matrix multiply acceleration to the ISA. None are ratified as of mid-2026. All are tasked through RISC-V International task groups and represent different points in the design space between architectural state cost, peak throughput, and integration with the ratified RISC-V Vector Extension (RVV 1.0).

- **AME** (Attached Matrix Extension): maximal performance through a separate matrix register file and tile-based outer-product execution
- **IME** (Integrated Matrix Extension): minimal new state by reusing the vector register file for matrix data
- **VME** (Vector Matrix Extension): middle path, adding dedicated matrix accumulator registers while remaining closely coupled to RVV

- [supported][src:riscv-tsc-gap-analysis-2025] The 2025 RISC-V TSC gap analysis identified AI/Vector/Matrix extensions as the top priority across all membership tiers, with all three TGs (IME, VME, AME) confirmed as active.
- [supported][src:riscv-ame-vme-poll-2025] An April 2025 sense poll of IME/AME TG members revealed support for all three approaches among RISC-V member companies, leading to formalization of the VME TG.
- [supported][src:riscv-matrix-blog-alibaba] Two fundamental architectural approaches exist for matrix extensions: reusing existing vector registers (Architecture 1) versus adding independent matrix register state (Architecture 2).

## Comparison: AME vs IME vs VME

| Dimension | AME (Attached Matrix Ext.) | IME (Integrated Matrix Ext.) | VME (Vector-Matrix Ext.) |
|---|---|---|---|
| **Spec name** | Zvma (SiFive proposal) | Zvvm family | Zvopmm |
| **Register model** | Dedicated 2D matrix tile registers (16 @ TEW=8, 4 @ TEW=32, etc.) | Matrix data lives entirely in existing RVV v0-v31 registers | New dedicated accumulator register file; vector registers as source operands |
| **RVV dependency** | None (standalone unit; optional data movement with RVV) | Requires RVV (matrix data in vector registers) | Requires RVV (reads vector source operands, closely coupled) |
| **Tile size approach** | TE x TE square tiles; TE scaled with VLEN (VLEN/4 >= TE >= 4) | M=N=(VLEN/SEW)/lambda tiles in vector register groups; K_eff = lambda x W x LMUL | Matrix-dimension-agnostic (similar to VLA); uses vsetvl-like mechanisms |
| **Accumulation strategy** | Outer-product tile accumulate (C += A^T x B); KMAX=4 (minimum 4 VLEN loads from A and B) | No architecturally visible accumulators per charter; computes C = A x B^T + C in vector regs | Outer-product accumulate into new accumulator register file |
| **Max accumulators** | 4 tile accumulators at TEW=32 (mt0, mt4, mt8, mt12); criticized for area cost | Subset of 32 vector registers used as accumulators; area-efficient | Implementation-defined accumulator register count |
| **Data types** | INT8/INT4, OCP MX FP4/FP8, BF16/FP16, FP32, FP64 variants | INT8, FP16, BF16, FP32, FP64 + MX types (~30+ extension variants) | AI/ML-focused: FP8, BF16, FP16, INT8, INT4 (explicitly excluding HPC FP64) |
| **2D load/store** | Yes (matrix tile load/store instructions) | No (relies on standard vector load/store) | No (standard row/column major memory order) |
| **Outer product debate** | Yes, tile outer product (fat K design) | Active inner vs. outer product debate; inner product scales better <256-bit VLEN, outer >256-bit | Yes, outer product as fundamental primitive |
| **Encoding space** | OP-V / OP-VE space | 32-bit encoding alongside vector ISA | vsetvl-like instruction setup |
| **Target market** | Datacenter HPC/DL, high-performance designs | HPC (FP64, large GEMM) and AI/ML; low-to-mid-range inference | AI/ML inference and training primary; HPC secondary |
| **Context-switch cost** | Higher (save/restore full matrix register file) | Lower (matrix data already in vector registers; few CSRs) | Moderate (new accumulator register file) |
| **Ratification target** | No public timeline available | Aug 2026 (Plan Approved Dec 2025, v0.6 Mar 2026, v0.9 Jun 2026) | Jul 2026 (Plan Approval Feb 2026, Freeze May 2026, Public Review May 2026) |
| **Reference implementation** | SiFive LLVM MC-layer (XSfmm*); T1 uarch proposal by Jiuyang Liu | IME spec draft on GitHub; Unicamp QEMU workload analysis | VME charter and PoW documents; mailing list active Jul 2025 |
| **Key proponents** | SiFive (Krste Asanovic), Alibaba (Qiu Jing), VRULL (Philipp Tomsich) | Andes Technology, Unicamp (Guido Araujo, acting chair), T-Head | Ventana Micro, Rivos, SiFive, Akeana, Aril |
| **Key critiques** | 4 tile accumulators costs 4x area; KMAX=4 forces wide pipeline registers; random tile read creates wiring congestion | Inner product does not scale CI with VLEN for output-stationary scheduling; no architecturally visible accumulators limits HPC | AI/ML scope limited; FP64 excluded; overlap with AME at high-performance end |

- [speculative][src:sifive-zvma-proposal-2024] AME (Zvma) proposes TEW=32 tiles with TE x TE element dimensions (TE power of 2, VLEN/4 >= TE >= 4), with 4 tile accumulators at TEW=32 encoding.
- [speculative][src:sifive-zvma-slides-2025] KMAX=4 in AME requires 8 cycles minimum load time (4 VLEN from A and 4 from B), forcing block normalization and wide carry-save pipeline registers.
- [speculative][src:riscv-ime-mailing-list-2025] Inner product IME is better suited for VLEN <= 256; outer product scales computational intensity naturally for VLEN > 256. (Unicamp analysis.)
- [speculative][src:riscv-ime-ratification-plan] IME targets ~90% peak GEMM performance and ~2x performance over vector for other kernels.
- [speculative][src:riscv-vme-charter] VME's basic matrix multiply operation takes two vector registers, computes their outer product, and accumulates N^2 MACs from two N-element vectors.
- [speculative][src:sifive-zvma-proposal-2024] AME tile punning: one TEW=32 tile (mt0) can be addressed as two TEW=16 tiles (mt0, mt2) or two TEW=64 tiles (mt0, mt2) with halved dimensions.

## Architectural Approaches in Detail

### AME (Attached Matrix Extension)

AME defines a standalone matrix compute unit with its own architectural state. It can be implemented without RVV, though data movement between vector and matrix registers is provided when both are present.

- [speculative][src:riscv-ame-tg-charter] The AME unit is "self-contained and orthogonal to other architectural resources," supporting matrix load/store, matrix-matrix and vector-matrix arithmetic, permutation, sparsity, and predication.
- [speculative][src:sifive-zvma-proposal-2024] AME tile dimensions are parametric: TE (tile elements per side) is a power of 2 between 4 and VLEN/4. For VLEN=512, TE ranges 4-128; for VLEN=256, TE ranges 4-64.
- [speculative][src:t1-zvma-microarchitecture-2025] T1 proposed "fat K" approach extends K range when TE < VLEN/4 to better utilize long vector registers, using PingPong SRAM banks with 2x2 PE subarrays.
- [speculative][src:riscv-ame-mailing-list-2025] Earl Killian (Aril) raised concerns that KMAX=4 disallows area-efficient KMAX=1 implementations, as it forces pipeline registers in carry-save trees and block normalization logic.

AME is architecturally closest to ARM SME (separate ZA tile register, outer-product engine) and Intel AMX (dedicated tile registers), though SME reuses SVE vector registers as source operands.

### IME (Integrated Matrix Extension)

IME is the most conservative approach in terms of architectural state. By placing matrix data in the existing vector register file, it minimizes context-switch overhead and reuses the RVV infrastructure.

- [speculative][src:riscv-ime-spec-draft] IME supports ~30+ extension variants across integer (Zvvi8i32mm), FP16/BF16 (Zvvfp16fp32mm, Zvvbf16fp32mm), FP32 (Zvvfp32mm), and FP64 (Zvvfp64mm), plus MX types.
- [speculative][src:riscv-ime-ratification-plan] IME timeline targets ratification by August 2026, making it potentially the first matrix extension to ratify.

The core design tension in IME is the inner-product vs. outer-product choice. Inner product (favored by SiFive/Andrew Waterman for simplicity and low area) does not scale computational intensity with VLEN under output-stationary scheduling. Outer product (favored by Unicamp for HPC) requires more register ports and accumulator state. The draft spec leaves the implementation choice open.

### VME (Vector-Matrix Extension)

VME occupies a middle position: it adds new accumulator register state (addressing the key IME limitation for AI/ML workloads) while remaining closely coupled to RVV (avoiding the full complexity of AME).

- [speculative][src:riscv-vme-charter] VME is "dimension agnostic" like RVV, using `vsetvl`-like mechanisms to set matrix dimensions. It specifically targets AI/ML data types (FP8, BF16, FP16, INT8, INT4) and explicitly excludes large HPC types like FP64.
- [speculative][src:riscv-vme-ratification-plan] VME targets TSC ratification by July 2026 and BoD ratification by July 30, 2026 — the most aggressive timeline of the three proposals.
- [speculative][src:riscv-vme-charter] VME provides data transfer instructions between accumulator registers and vector registers supporting both row-major and column-major access, enabling "free" matrix transpose.

## Comparison with Non-RISC-V Matrix Architectures

### ARM SME (Scalable Matrix Extension)

ARM SME is the closest non-RISC-V analog and the most relevant comparison point. Both SME and the RISC-V proposals target CPU-integrated matrix acceleration using VLA-like principles.

| Dimension | ARM SME | RISC-V AME (closest analog) | Key Difference |
|---|---|---|---|
| **Vector base** | SVE/SVE2 (VLA, predicate-based) | RVV 1.0 (VLA, LMUL-based) | Different VLA implementations |
| **Register model** | ZA tile (SVL x SVL bytes); SVE Z/P registers as sources | Matrix tile registers (TE x TE elements); RVV v0-v31 as optional sources | SME has one ZA tile; AME has 4+ tile specifiers |
| **Streaming mode** | PSTATE.SM (separate execution mode) | No equivalent; all operations in same mode | SME requires mode switching; AME does not |
| **Outer product** | Outer product of A[H] and B[W] into C[H x W] tile | Outer product tile accumulate (C += A^T x B) | Similar mathematical formulation |
| **Data types** | FP32, FP64, BF16, FP16, INT8 | INT8/4, MX FP4/8, BF16/FP16, FP32, FP64 | Broader AI precision support in AME (MX types) |
| **Binary portability** | SVL implementation-defined (128-2048) | TE implementation-defined (VLEN/4 >= TE >= 4) | Both VLA; both require runtime length discovery |
| **Ratification** | Ratified (Armv9-A, shipping in Neoverse V-series) | Pre-ratification | SME is production-ready; RISC-V proposals are pre-ratification |
| **Multi-vector extensions** | SME2 adds multi-vector FMOPA, ZT0 register | Not yet proposed for AME | SME2 is a second-generation extension building on SME |

- [supported][src:arm-sme-introduction-blog] ARM SME uses a streaming SVE mode (PSTATE.SM) where SME storage and instructions are available alongside a significant subset of SVE2 instructions.
- [supported][src:arm-sme-introduction-blog] SME computes outer products of vectors A[H] and B[W] producing an HxW matrix accumulated into the ZA tile.

RISC-V AME's tile register model is architecturally similar to ARM SME's ZA tile, but with a key difference: SME maintains a single ZA tile and provides 2D predication for row/column-level masking, while AME proposes multiple independent tile specifiers (up to 4 at TEW=32) and tile punning for different element widths.

### NVIDIA Tensor Cores

NVIDIA Tensor Cores are the dominant matrix acceleration technology in AI training and inference, deployed in every NVIDIA GPU since Volta (2017).

| Dimension | NVIDIA Tensor Cores | RISC-V Matrix Extensions (General) |
|---|---|---|
| **Architecture** | Warp-level specialized matrix units within SM | CPU ISA extension for matrix operations |
| **Register model** | CUDA fragments (distributed across warp threads) | ISA-visible tile/accumulator registers |
| **Data placement** | Shared memory / register-level tiles | Memory / vector register / tile register |
| **Programming** | CUDA WMMA/MMA API, cuBLAS, Triton | Compiler intrinsics, MLIR, future library support |
| **Matrix geometry** | Fixed warp-level tile sizes (16x16, 8x32, etc.) | Parametric (TE, KMAX, VLA-style) |
| **Data types** | FP64/FP32/TF32/FP16/BF16/FP8/INT8/INT4 | INT8/4, MX FP4/8, BF16/FP16, FP32, FP64 (varies by proposal) |
| **Peak throughput** | ~Tensor TFLOPS per GPU (proprietary, generation-dependent) | Implementation-defined (depends on TE/LMUL/clock) |
| **Specialization** | Fixed dataflow (systolic array / outer product per generation) | Flexible outer product / inner product per proposal |

- [supported][src:nvidia-a100-architecture-whitepaper-2020] (from tensor-cores.md) NVIDIA A100 includes third-generation Tensor Cores with support for multiple AI and HPC data types.

The critical architectural distinction is that Tensor Cores are a **fixed-geometry, fixed-dataflow** hardware unit exposed through a GPU programming model, while the RISC-V matrix extensions are **parametric ISAs** intended for CPU-style execution with compiler-driven tiling and data movement.

### Google TPU Systolic Arrays

Google's TPU uses a large 2D systolic array (Matrix Multiply Unit / MXU) as its primary compute engine.

| Dimension | Google TPU (v2/v3/v4) | RISC-V Matrix Extensions |
|---|---|---|
| **Architecture** | Dedicated ASIC with massive systolic array | CPU ISA extension for general-purpose CPUs |
| **Array size** | 128x128 (TPUv2/v3), larger in v4 | Implementation-defined (TE x TE, DTE x DTE microarch) |
| **Data type** | BF16 primary (v2/v3), FP8 (v4) | Multiple types (varies by proposal) |
| **Control** | Sequential instruction stream (CISC-style) | Integrated with CPU scalar/vector pipeline |
| **Memory** | Large on-chip SRAM (HBM-scratchpad model) | Standard cache hierarchy or scratchpad |
| **Flexibility** | Single dataflow pattern per operation | Multiple matrix shapes, configurable accumulation |

The TPU represents the "fully specialized" end of the spectrum, while RISC-V matrix extensions represent the "ISA-integrated" end. The TPU's advantage comes from massive array-level parallelism and co-designed memory bandwidth; RISC-V's advantage comes from integration with a general-purpose CPU ecosystem and parametric scaling across market segments.

## Open Questions

- OPEN: Will the three proposals converge into a unified specification, or will all three become separate RISC-V standards serving different market segments? The April 2025 poll showed support for all three, and a software compatibility TG is proposed but not yet formed.
- OPEN: What is the actual convergence timeline? IME targets Aug 2026 ratification, VME targets Jul 2026, but AME has no public timeline — and no proposal has reached public review as of mid-2026.
- OPEN: Does IME's inner-product vs. outer-product debate have a resolution path? The draft spec leaves the implementation choice open, which may impair binary portability across IME implementations.
- OPEN: How will the matrix extension interact with RISC-V's hypervisor and context-switching model, especially for AME with its large matrix register state? (Context-switch cost was raised in AME TG discussions.)
- OPEN: Can the software ecosystem (compilers, libraries, runtimes) efficiently target three different matrix ISAs, or will a compatibility layer be needed for portable code?
- OPEN: How does VME differentiate from AME at the high-performance end? If both support outer product with dedicated accumulator state, the distinction may blur in practice.
- OPEN: What is the relationship between the Dot Product extension (pursued through Vector SIG) and the three matrix TGs? Krste's original slide showed a fourth "dot product" category that may become a simpler, earlier-ratified alternative.
- VERIFY: No published microarchitecture analysis exists comparing AME vs. VME vs. IME area, power, and performance at equivalent implementation points (VLEN, process node). The debate is currently qualitative.
- DO_NOT_MERGE: This concept covers three competing proposals that may diverge or converge before ratification. Any merge to verified status will need to track which proposals actually ratify and whether they coexist or supersede each other.
