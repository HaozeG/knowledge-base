---
id: software.riscv.ai-software-ecosystem
title: RISC-V AI Software Ecosystem for Matrix Acceleration
status: draft
layer: 80-programming-interface-dsl
layer_path: 80-programming-interface-dsl/riscv/ai-ecosystem
parent: hw.riscv.matrix-extension-proposals
secondary_layers: [90-compiler-lowering-stack, 100-runtime-execution-system, 110-workload-mapping]
granularity: overview
concept_type: programming_interface
scale_scope: [ecosystem]
reasoning_roles: [enabler, bottleneck, mapping]
tags: [riscv, ai, software, mlir, tvm, openblas, eigen, compiler, framework, inference, training, ecosystem]
aliases: [RISC-V AI software stack, RVV ML ecosystem, RISC-V matrix software]
sources: [lei-mlir-rvv-xdsl-2025, puzikova-eigen-rvv-pact-2025, greenblatt-tvm-rvv-autotune-2026, google-coral-roadmap-2026, ventana-ruca-ai-platform-2025, riscv-ame-software-roadmap-2024, riscv-matrix-software-tg-2025, riscv-eu-roadmap-2025, nuclei-rvv-ai-library-2025]
---

# RISC-V AI Software Ecosystem for Matrix Acceleration

## First-Principle Explanation

Hardware acceleration is useless without software that can target it. The first-principle problem for RISC-V AI software is a **compilation mapping problem**: take a high-level ML model expressed in a framework (PyTorch, JAX, TensorFlow) and lower it through multiple intermediate representations to machine code that exploits RVV vector instructions and future matrix extensions — while maintaining portability across different RISC-V implementations with different VLEN, supported extensions, and matrix ISA variants.

The central tension is between **portability** and **performance**:

```text
Portability:  one binary runs on any RISC-V implementation (VLA helps, but matrix ISA variants break this)
Performance:  optimal code exploits specific VLEN, LMUL, cache sizes, and matrix tile dimensions
Resolution:   compiler auto-tuning (TVM MetaSchedule), JIT compilation (MLIR/IREE), or source-level portability layers
```

- [supported][src:lei-mlir-rvv-xdsl-2025] MLIR with xDSL custom lowerings generates RVV code that outperforms OpenBLAS by 10–35% on GEMM and BERT-Large workloads on K230 and BananaPi F3 hardware, reaching 12.2 GFLOPS vs. 5.1 GFLOPS baseline.
- [supported][src:puzikova-eigen-rvv-pact-2025] Eigen library RVV support achieves 2.5–3× speedup over scalar on RISC-V platforms, outperforming OpenBLAS by 11% on key linear algebra operations — critical for TensorFlow and PyTorch which use Eigen as their CPU backend.
- [supported][src:greenblatt-tvm-rvv-autotune-2026] TVM MetaSchedule on RVV 1.0 hardware achieves 46% mean improvement over GCC autovectorization and 35% over LLVM on commercial RVV 1.0 silicon, with smaller code footprint than hand-crafted libraries.

## The RISC-V AI Software Stack

The stack maps cleanly to the ontology layers:

| Stack Layer | Ontology Layer | RISC-V Status (2026) | Key Projects |
|---|---|---|---|
| **ML Framework** | 80 (DSL/Interface) | PyTorch, JAX, TensorFlow via RISE; LiteRT for edge | RISE project, Google Coral |
| **Compiler/IR** | 90 (Compiler Lowering) | MLIR + xDSL operational; TVM MetaSchedule operational | MLIR RISC-V backend, IREE, TVM |
| **Math Libraries** | 90 (Compiler Lowering) | OpenBLAS, Eigen with RVV; BLIS in progress | OpenBLAS RVV, Eigen RVV, Nuclei AI Lib |
| **Runtime** | 100 (Runtime Execution) | LiteRT runtime, ONNX Runtime, vendor-specific | LiteRT, ONNX Runtime RISC-V |
| **Kernel Patterns** | 110 (Workload Mapping) | GEMM, attention, convolution patterns mapped to RVV | Greenblatt 2026, Nuclei kernels |

## Compiler Frameworks: MLIR, TVM, and xDSL

### MLIR + xDSL Pathway

- [supported][src:lei-mlir-rvv-xdsl-2025] The MLIR + xDSL approach uses custom intermediate representations in xDSL (a Python-native MLIR dialect framework) to progressively lower high-level tensor operations to hardware-aware C code with RVV intrinsics. The key insight is that xDSL's Python DSL allows rapid prototyping of new lowering passes without modifying the C++ MLIR core.
- [speculative][src:lei-mlir-rvv-xdsl-2025] The approach generates micro-kernels with explicit LMUL grouping and strip-mining loops, achieving better register allocation than general-purpose compilers (GCC, LLVM) because the lowering passes are aware of RVV's VLA semantics at each transformation step.

For matrix extensions (AME/IME/VME), the MLIR pathway is the planned integration point: the AME task group's software roadmap targets an MLIR dialect for AME operations, with lowering from standard MLIR linalg/memref dialects to AME-specific tile operations.

### TVM MetaSchedule Pathway

- [supported][src:greenblatt-tvm-rvv-autotune-2026] TVM's MetaSchedule framework uses probabilistic cost models to search the space of valid RVV tiling configurations, automatically discovering tile sizes, LMUL settings, and loop orders that maximize throughput on a given RVV implementation.
- [speculative][src:greenblatt-tvm-rvv-autotune-2026] The key advantage over hand-crafted libraries is auto-tuning: as new RVV implementations ship with different VLEN, cache sizes, and memory bandwidth, TVM re-tunes rather than requiring manual re-optimization. This is particularly important given the diversity of RISC-V implementations (from 128-bit edge chips to 1024-bit datacenter cores).

## Math Libraries

### OpenBLAS

OpenBLAS is the most widely deployed BLAS implementation and is the primary target for HPC-focused matrix acceleration on RISC-V. The AME task group's software roadmap lists OpenBLAS as a target library, with the plan being to add AME-intrinsic micro-kernels alongside existing RVV micro-kernels.

- [inference] The cross-committee discussion on Matrix Software APIs (April 2025) identified a critical unresolved question: should OpenBLAS ship a single binary that uses runtime dispatch (checking for AME/IME/VME at load time), or should it ship ISA-specific binaries? The VLA nature of RVV already supports binary portability for vector code; matrix extensions break this because they add new architectural state (tile registers, accumulator registers) that must be saved/restored on context switch.

### Eigen with RVV

- [supported][src:puzikova-eigen-rvv-pact-2025] The Eigen linear algebra library now has full RVV support, achieving 2.5–3× speedup over scalar and outperforming OpenBLAS by 11%. Eigen is the CPU backend for TensorFlow and PyTorch, making this integration directly impactful for ML framework support on RISC-V.
- [speculative][src:puzikova-eigen-rvv-pact-2025] Eigen's packet-based abstraction (processing multiple elements per SIMD "packet") maps naturally to RVV's VLA model, as the packet size adapts to VLEN at compile time through preprocessor macros.

### Vendor Libraries

- [speculative][src:nuclei-rvv-ai-library-2025] Nuclei's RVV AI library (China) provides optimized GEMM, convolution, and activation kernels for int8/int16/fp16/bf16/fp32, including custom BF16 support that avoids FP32 conversion overhead and a matrix extension (Xxlvqmacc) following the IME group specification.

## Hardware Platform Software Stacks

### Google Coral (RISC-V NPU)

- [supported][src:google-coral-roadmap-2026] Google's Coral platform has a concrete RISC-V roadmap: Milestone 2 (Q4 2025) delivers RVV 1.0 execution with VLEN=128, int8/int16, and MLIR compiler support from the LiteRT (TensorFlow Lite) frontend. Milestone 3 (2026) adds VLEN=512, FP32/FP16/BF16, and JAX frontend support, targeting Gemma model deployment.
- [speculative][src:google-coral-roadmap-2026] The Coral software stack's evolution from CNN-only (Milestone 2) to Transformer-capable (Milestone 3) mirrors the industry trajectory — RVV alone suffices for CNN inference, but Transformer attention requires either larger VLEN or matrix extension support for efficient GEMV.

### Ventana RUCA (Unified Compute Architecture)

- [speculative][src:ventana-ruca-ai-platform-2025] Ventana's RUCA provides a shared ISA across scalar, vector, and matrix execution, with a software stack supporting TVM, ONNX, and TFLite today, and tracking PyTorch enablement through the RISE project. The unified ISA approach means the same compiler infrastructure generates code for all three execution modes.

## Standardization and Ecosystem Coordination

- [speculative][src:riscv-matrix-software-tg-2025] The April 2025 cross-committee discussion on Matrix Software APIs proposed a "service extensions" concept: a set of standard services (subroutine call interfaces, state management) that all implementations claiming a matrix extension must provide. This would enable binary-compatible library distributions across different RISC-V matrix hardware — analogous to how x86 libraries work across Intel and AMD CPUs.
- [speculative][src:riscv-eu-roadmap-2025] The EU RISC-V roadmap projects full platform toolchain integration (MS9) by 2031, with matrix ISA extensions (rank-1 outer product) targeted for 2025–2027 and a dual octal-core AI chiplet by 2033.

## Inference vs. Training Maturity

- [inference] The RISC-V AI software ecosystem in 2026 is substantially more mature for inference than training:
  - **Inference**: RVV 1.0 is production-ready with TVM, Eigen, OpenBLAS, LiteRT, and ONNX support. Multiple hardware platforms (K230, BananaPi F3, SpacemiT K1) run inference workloads today. Google Coral targets production wearable inference on RISC-V by 2026.
  - **Training**: Matrix extensions (required for competitive training throughput) are still in standardization. PyTorch training support is tracked via RISE but not yet production-ready. The DeepSeek-inspired RISC-V training architecture proposal exists as a design document, not silicon.
- [speculative] The GEMV bottleneck in LLM decode (generating one token at a time, each requiring a matrix-vector multiply) is the immediate target for matrix extensions — GEMV arithmetic intensity is O(1), making it memory-bound on RVV, whereas matrix extensions with dedicated accumulators can improve throughput through higher data reuse.

## Open Questions

- OPEN: Will a unified MLIR dialect for RISC-V matrix operations emerge, or will AME, IME, and VME each require separate dialects? The AME TG's software roadmap assumes a single dialect, but the cross-committee discussion acknowledges the possibility of divergence.
- OPEN: How will the service extensions proposal resolve binary compatibility? If each matrix ISA variant requires its own OpenBLAS binary, the software distribution complexity scales with the number of ratified extensions.
- OPEN: Can the TVM MetaSchedule approach (auto-tuning) keep pace with the rate of new RISC-V hardware implementations, or will manual library optimization remain necessary for peak performance on flagship implementations?
- OPEN: When will PyTorch training on RISC-V be production-ready? The RISE project coordinates this but has not published a target date.
- VERIFY: The 10–35% MLIR+xDSL improvement over OpenBLAS (Lei et al., 2025) was measured on pre-production RISC-V hardware with VLEN=256. Results on production hardware (VLEN=128 or VLEN=1024) may differ.
- VERIFY: Google Coral's Milestone 3 timeline (2026) depends on internal Google hardware schedules and may shift.
