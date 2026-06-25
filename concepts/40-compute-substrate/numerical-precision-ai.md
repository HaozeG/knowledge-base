---
id: hw.compute.numerical-precision-ai
title: Numerical Precision Formats for AI Accelerators
status: draft
layer: 40-compute-substrate
layer_path: 40-compute-substrate/precision/numerical-precision-ai
parent: hw.gpu.tensor-cores
secondary_layers: [50-memory-data-movement, 80-programming-interface-dsl, 90-compiler-lowering-stack, 110-workload-mapping]
granularity: concept
concept_type: architecture_pattern
scale_scope: [unit, tile, die, ecosystem]
reasoning_roles: [enabler, bottleneck, constraint]
tags: [precision, fp8, fp4, mx, block-floating-point, quantization, bf16, ieee-754]
aliases: [low-precision AI, FP8 inference, FP4 training, MX format, microscaling, block FP]
sources: [nvidia-fp8-blog-2024, nvidia-blackwell-nvfp4-2025, nvidia-mxfp8-blackwell-2025, nvidia-h100-architecture-2022, nvidia-tf32-2020, ocp-mx-spec-v1-2023, ocp-fp8-spec-2023, ieee-754-2019, fireattention-v4-fp4-2025, amd-mi355x-cdna4-2025, samsung-hbm-roadmap-2025, riscv-bf16-spec-v1-2025, riscv-zvfbfa-proposal-2025, llm-fp8-optimization-ieee-2025]
---

# Numerical Precision Formats for AI Accelerators

## Overview

Numerical precision is a first-order design parameter for AI accelerators. Halving the bit width per value roughly doubles the number of operations per second in fixed-area compute units, halves the memory bandwidth required per element, and halves the storage footprint — at the cost of some accuracy. The evolution from FP32 → FP16/BF16 → FP8 → FP4 over 2020–2025 has been the single largest contributor to AI throughput gains, exceeding architecture-level improvements in some generations.

- [supported][src:nvidia-h100-architecture-2022] The H100 FP8 Tensor Core achieves 2× the throughput of FP16 Tensor Core operations at roughly equal area, by packing twice as many 8-bit multiplies into the same systolic array width.
- [supported][src:nvidia-blackwell-nvfp4-2025] Blackwell NVFP4 achieves 4× the throughput of FP8 (8× BF16) by using 4-bit E2M1 elements with dual-level block scaling.
- [supported][src:ocp-mx-spec-v1-2023] The OCP Microscaling (MX) standard defines a family of block-scaled formats (MXFP8, MXFP6, MXFP4, MXINT8) where a shared E8M0 scale factor applies to blocks of 32 elements, decoupling dynamic range from per-element precision.

## Precision Spectrum

### Standard IEEE 754 and Brain Float Formats

| Format | Bits | Exponent | Mantissa | Dynamic Range | Typical Use |
|--------|------|----------|----------|---------------|-------------|
| FP32 | 32 | 8 | 23 | ~10³⁸ | Reference, accumulation |
| FP16 (IEEE) | 16 | 5 | 10 | ~65K | Legacy inference |
| BF16 | 16 | 8 | 7 | ~10³⁸ | Training forward/backward |
| TF32 (NVIDIA) | 19 | 8 | 10 | ~10³⁸ | Tensor Core accumulation |

- [supported][src:ieee-754-2019] IEEE 754-2019 defines FP32 and FP16 formats, but BF16 is not an IEEE format; it originated at Google for TPU and was widely adopted because its 8-bit exponent matches FP32's dynamic range, eliminating overflow concerns during training.
- [supported][src:nvidia-tf32-2020] TF32 is a truncated FP32 format used internally by NVIDIA Tensor Cores since Ampere: 19-bit internal representation with FP32's exponent range and FP16's mantissa precision. It is the default math mode in PyTorch and TensorFlow.

### 8-Bit Formats: FP8 E4M3 / E5M2

- [supported][src:nvidia-fp8-blog-2024] NVIDIA, ARM, and Intel jointly proposed two FP8 variants: **E4M3** (4 exponent, 3 mantissa bits, max value ±448) optimized for forward-pass weights and activations, and **E5M2** (5 exponent, 2 mantissa bits, max value ±57,344) optimized for backward-pass gradients where dynamic range dominates. This dual-format strategy is known as "hybrid" FP8 training.
- [supported][src:ocp-fp8-spec-2023] OCP adopted these same formats into the OCP FP8 specification, making them an open standard beyond NVIDIA.
- [inference][src:nvidia-fp8-blog-2024] FP8 inference requires per-tensor or per-channel scaling factors applied in software or via the Transformer Engine's delayed scaling algorithm to keep values within the E4M3 representable range.

### 4-Bit Formats: NVFP4 and MXFP4

- [supported][src:nvidia-blackwell-nvfp4-2025] NVIDIA NVFP4 uses **E2M1** element format (2 exponent, 1 mantissa bits) with dual-level block scaling: a per-16-element block scale stored in FP8 (E4M3) format, and a per-tensor scale stored in FP32. This provides 4-bit storage at FP8-like effective precision for most LLM weight tensors.
- [supported][src:ocp-mx-spec-v1-2023] MXFP4 also uses E2M1 elements with E8M0 shared scales across 32-value blocks. The key design insight: weight and activation tensors have locally smooth distributions; sharing one exponent per small block exploits this local smoothness while using minimal bits per element.
- [supported][src:fireattention-v4-fp4-2025] In production, NVFP4 achieves <1% accuracy degradation on MMLU benchmarks (e.g., DeepSeek-R1 MMLU: 90.8% FP8 → 90.7% FP4) while delivering ~2× throughput and ~1.8× memory reduction vs FP8.

## Block Floating Point and Microscale (MX) Formats

Block floating point (BFP) is an old signal-processing technique where a group of numbers shares a single exponent. Modern MX formats refine this idea with per-block scale factors rather than a single global exponent.

- [supported][src:ocp-mx-spec-v1-2023] The OCP MX specification defines a family: **MXFP8** (E5M2 or E4M3 elements), **MXFP6** (E3M2 or E2M3), **MXFP4** (E2M1), and **MXINT8**. All use an 8-bit E8M0 shared scale per 32 elements, stored in a separate scale tensor.
- [inference][src:ocp-mx-spec-v1-2023] The E8M0 scale format carries exponent-only information with zero mantissa bits: values range from 2⁻¹²⁷ to 2¹²⁷, providing enormous dynamic range independent of the narrow element format. This is the key enabler: the scale absorbs outliers that would otherwise saturate narrow formats.
- [inference][src:amd-mi355x-cdna4-2025] AMD CDNA4 (MI355X) adds native MXFP4/MXFP6 matrix core support, roughly doubling FP8 throughput. AWS Trainium 3 (NeuronCore-v4) similarly supports MXFP4 and MXFP8 matmul natively, achieving 4× throughput vs BF16/FP16.

### NVFP4 vs MXFP4

- [supported][src:nvidia-blackwell-nvfp4-2025] NVFP4 differs from MXFP4 in scale granularity: NVFP4 uses 16-element blocks with FP8 scale + FP32 per-tensor scale; MXFP4 uses 32-element blocks with E8M0 scale. NVFP4's finer granularity gives slightly better accuracy for tensors with rapidly varying magnitude (e.g., attention query/key outer products).
- [inference][src:nvidia-mxfp8-blackwell-2025] Blackwell also supports MXFP8 (E4M3 + E8M0) as a first-class format alongside NVFP4, using Transformer Engine's `MXFP8BlockScaling` recipe. This allows E4M3 to be used for both forward and backward passes without the E5M2 fallback.

## Hardware Implications

### Area, Power, and Throughput

- [supported][src:ieee-754-2019] Integer and fixed-point multipliers scale roughly with the square of bit width. A 4-bit integer multiply uses ~1/16 the area of a 16-bit multiply and ~1/64 the area of a 32-bit multiply. Floating-point adds exponent alignment and normalization overhead, but the quadratic scaling in the mantissa multiplier dominates for narrow formats.
- [inference][src:nvidia-h100-architecture-2022] In practice, doubling the number of operations per clock at half precision does not require halving the multiplier area because the systolic array control logic, accumulators, and register files do not halve. H100 achieves roughly 2× FP8 throughput vs FP16 (3958 vs 1979 TFLOPS) at similar die area.
- [inference][src:nvidia-blackwell-nvfp4-2025] Moving from FP8 to NVFP4 effectively quadruples the width of the systolic array data path, but the block-scaling logic (E8M0 multiply, FP32 scale accumulators) adds area overhead. The net effect is 2× throughput gain vs FP8 for Blackwell at similar power, not 4×.

### Memory Bandwidth and Capacity

- [supported][src:samsung-hbm-roadmap-2025] HBM bandwidth growth (~1.5–2× per generation) lags compute growth (~2–4× per generation). Reducing per-element bit width is the primary lever for closing the bandwidth gap: FP4 halves memory traffic vs FP8, quadrupling effective arithmetic intensity in the roofline model.
- [inference] At the datacenter level, FP4 inference reduces both HBM capacity requirements (smaller KV-cache per request) and HBM bandwidth pressure (fewer bytes per token), which directly improves TCO by allowing more concurrent requests per GPU. See [[model.ai-datacenter-tco]].

### RISC-V Precision Extensions

- [supported][src:riscv-bf16-spec-v1-2025] RISC-V has ratified **Zfbfmin**, **Zvfbfmin**, and **Zvfbfwma** for scalar and vector BF16 support. The `vfwmaccbf16.v[vf]` instruction provides widening BF16 multiply-accumulate — the critical primitive for BF16 matrix multiply.
- [supported][src:riscv-zvfbfa-proposal-2025] The proposed **Zvfbfa** extension adds full BF16 arithmetic via an `altfmt` bit in the `vtype` CSR that redefines 16-bit FP operations as BF16 when set. The proposed **Zvfofp8min** adds FP8 (E4M3/E5M2) conversion instructions with saturation — the first step toward FP8 compute on RISC-V.
- [inference] RISC-V's precision roadmap runs behind NVIDIA/AMD by roughly one generation: FP8 native compute is still at the proposal stage while NVIDIA is shipping NVFP4. However, RISC-V's vector-length-agnostic (VLA) model means that software-controlled `vl` can implement sub-byte blocking without silicon changes — trading higher software complexity for hardware simplicity. See [[hw.riscv.matrix-extension-proposals]].

## Open Questions

- OPEN: Can MXFP4 training from scratch match BF16/FP8 accuracy for models beyond the 120B scale? The GPT-OSS 120B result is promising but a single data point.
- OPEN: Will the industry converge on MX as a single standard or fragment into NVFP4 (NVIDIA), MXFP4 (OCP), and AMD's format? MXFP4 and NVFP4 are close but not identical. The OCP spec provides an open-standard umbrella, while NVIDIA's NVFP4 gives best-in-class accuracy on NVIDIA hardware.
- OPEN: Does the 4-bit floor (E2M1) represent a fundamental accuracy limit, or can 2-bit formats (ternary {−1,0,1} or binary {1.0, −1.0} weights) work for inference? BitNet-style 1.58-bit models claim viability but have not been demonstrated at frontier scales.
- VERIFY: The area/power scaling of block-scaling logic vs. narrower multipliers needs silicon-measured data. Current claims are based on synthesis estimates, not fabricated test chips (except NVIDIA's proprietary Blackwell measurements).

## References

- [nvidia-fp8-blog-2024] NVIDIA. "Floating-Point 8: An Introduction to Efficient, Lower-Precision AI Training." 2024.
- [nvidia-blackwell-nvfp4-2025] NVIDIA. "Introducing NVFP4 for Efficient and Accurate Low-Precision Inference." 2025.
- [nvidia-mxfp8-blackwell-2025] NVIDIA. "MXFP8 Block Scaling — Transformer Engine." 2025.
- [nvidia-h100-architecture-2022] NVIDIA. "NVIDIA H100 Tensor Core GPU Architecture." 2022.
- [nvidia-tf32-2020] NVIDIA. "TensorFloat-32 in the A100 GPU." 2020.
- [ocp-mx-spec-v1-2023] Open Compute Project. "OCP Microscaling Formats (MX) v1.0 Specification." 2023.
- [ocp-fp8-spec-2023] Open Compute Project. "OCP 8-bit Floating Point Specification (OFP8)." 2023.
- [ieee-754-2019] IEEE. "IEEE 754-2019 Standard for Floating-Point Arithmetic." 2019.
- [fireattention-v4-fp4-2025] Fireworks AI. "FireAttention V4: Industry-Leading Latency and Cost Efficiency with FP4." 2025.
- [amd-mi355x-cdna4-2025] AMD. "AMD Instinct MI355X Accelerator." 2025.
- [samsung-hbm-roadmap-2025] Samsung. "Samsung HBM Roadmap: HBM3e → HBM4." 2025.
- [riscv-bf16-spec-v1-2025] RISC-V International. "RISC-V BF16 Extension Specification v1.0." 2025.
- [riscv-zvfbfa-proposal-2025] Waterman, A. "Zvfbfa / Zvfofp8min Proposal." 2025.
- [riscv-matrix-extension-proposals-concept] Knowledge base concept: `hw.riscv.matrix-extension-proposals`.
- [ai-datacenter-tco-concept] Knowledge base concept: `model.ai-datacenter-tco`.

## See Also

- [[hw.gpu.tensor-cores]] — NVIDIA Tensor Core architecture that consumes these precision formats.
- [[hw.riscv.vector-extension]] — RISC-V Vector Extension with Zvfbfmin/Zvfbfwma for BF16.
- [[hw.riscv.matrix-extension-proposals]] — RISC-V Matrix Extension proposals that target FP8/FP4 compute.
- [[programmer.roofline-model]] — Roofline model where precision choice shifts the arithmetic intensity.
- [[hw.riscv.vector-memory-hierarchy]] — Memory bandwidth constraint that precision formats help mitigate.
- [[software.compiler.power-aware-compilation]] — Precision as a power/energy optimization knob.
- [[model.ai-datacenter-tco]] — TCO impact of precision via memory savings and throughput gains.
