---
id: workload.ai.rvv-kernel-patterns
title: AI Kernel Mapping Strategies on RISC-V Vector Extension
status: draft
layer: 110-workload-mapping
layer_path: 110-workload-mapping/riscv/kernel-patterns
parent: hw.riscv.vector-extension
secondary_layers: [40-compute-substrate, 50-memory-data-movement, 90-compiler-lowering-stack]
granularity: concept
concept_type: kernel_algorithm
scale_scope: [unit, tile, die]
reasoning_roles: [mapping, enabler, bottleneck]
tags: [riscv, rvv, gemm, convolution, attention, elementwise, layernorm, kernel, ai, workload-mapping, cuda]
aliases: [RVV kernel patterns, RISC-V AI kernel mapping, RVV GEMM tiling, RVV conv algorithms]
sources: [gupta-conv-rvv-chalmers-2023, garcia-llm-rvv-sophgo-2025, greenblatt-tvm-rvv-autotune-2026, tan-opt-sparse-matrix-rvv-2025, perotti-rvv-embedded-ml-2024, modin-kth-rvv-autovec-2024, esperanto-risc-v-ai-2021, ventana-veyron-v2-rvv-2023, riscv-v-spec-ratified-2021, cnx-c908-aiot-2022, spacemit-k1-datasheet-2024, epi-vpu-bandwidth-2023, ventus-gpgpu-whitepaper]
---

# AI Kernel Mapping Strategies on RISC-V Vector Extension

## First-Principle Explanation

AI kernel mapping on RVV is the problem of decomposing workload-level operations (GEMM, convolution, attention, element-wise) into sequences of vector instructions that maximize the fraction of peak compute and memory throughput realized on a given RVV implementation.

The central constraint is a mapping tension between VLA abstraction and fixed-shape kernels:

```text
VLA programming model   -> kernel must work on any VLEN, cannot hardcode tile shapes
fixed-shape AI kernels  -> GEMM MxNxK, Conv NCHW, attention BxSxD have natural dimension ordering
mapping resolution      -> strip-mining, LMUL grouping, layout transforms reconcile these
```

RVV provides 32 vector registers (v0-v31), each VLEN bits wide. LMUL groups 1/2/4/8 registers into a logical operand. The micro-kernel designer chooses LMUL, SEW, and tile shapes to balance register pressure, data reuse, and memory traffic. This is architecturally similar to CUDA register tiling, but without shared memory for inter-thread data exchange and without warp-level shuffle instructions.

## GEMM on RVV: Tiled Outer-Product Micro-Kernel

### Micro-Kernel Design

[supported][src:greenblatt-tvm-rvv-autotune-2026][src:perotti-rvv-embedded-ml-2024] GEMM on RVV uses a tiled outer-product pattern. The micro-kernel computes a small sub-block of C = A x B using vector registers for accumulation:

- A-tile (Mr x Kc): loaded into a set of vector registers with LMUL grouping
- B-tile (Kc x Nr): loaded into another set of vector registers
- C-tile (Mr x Nr): accumulated in a grid of vector register pairs or quadruples

The outer-product formulation is natural for RVV because:
- `vfmacc.vv` (fused multiply-add) operates on two vector register operands, accumulating into a third
- LMUL=8 allows up to 256 elements per operation (with VLEN=1024 and SEW=32)
- Strip-mining with `vsetvli` handles the remaining K dimension automatically

[inference][src:greenblatt-tvm-rvv-autotune-2026] The TVM MetaSchedule experiments on 256-bit RVV 1.0 silicon found the optimal micro-kernel tile sizes are smaller than on GPU equivalents:
- Mr=4, Nr=4 (256-bit VLEN), versus Mr=16, Nr=16 for CUDA with Tensor Cores
- The smaller tile reflects the absence of shared memory: all reuse must happen in vector registers
- LMUL=4 (8 vector registers per operand group) provides the best tradeoff between width and register pressure for 256-bit VLEN

### Tiling Hierarchy

RVV GEMM tiling differs from CUDA GEMM tiling in one structural way:

| Layer | CUDA GEMM | RVV GEMM |
|-------|-----------|----------|
| Outer loop | Grid-level block tiling over M, N, K | Same: loop nests over M, N, K |
| Thread-block tile | Shared memory tile (e.g., 128x128) | Not applicable: no thread block |
| Register tile | Per-thread register tiling (warp-level) | LMUL-based register tiling |
| Inner loop | Warp-level matrix multiply (mma.sync) | Strip-mined vfmacc (no synchronization) |

[supported][src:tan-opt-sparse-matrix-rvv-2025] For structured-sparse GEMM, RVV can exploit `vfmacc.vv` with a sparse index operand. The proposed vindexmac extension targets this pattern directly, achieving 25-33% runtime improvement for 2:4 structured sparsity on 256-bit RVV.

### LMUL and Throughput

[supported][src:riscv-v-spec-ratified-2021] LMUL determines the number of vector registers grouped per operand:
- LMUL=1: 1 register (minimum width), good for short vectors and low register pressure
- LMUL=2,4,8: grouped registers for wider operations, up to 8x32=256 registers worth of state per operation
- Fractional LMUL (1/2, 1/4, 1/8): sub-register operations, LMUL < 1 masks half the register file per instruction

[inference][src:ventana-veyron-v2-rvv-2023][src:epi-vpu-bandwidth-2023] For maximum GEMM throughput, LMUL=8 should be preferred when the kernel is compute-bound. However, on memory-bound systems (edge RVV SoCs with limited DRAM bandwidth), LMUL=8 may worsen underutilization because the wider load cannot be fed. The EPI FPGA study found that long vectors reduce memory latency sensitivity but increase bandwidth requirements proportionally.

[inference][src:modin-kth-rvv-autovec-2024] Compiler auto-vectorization for GEMM typically uses LMUL=1 or LMUL=2 by default, missing the throughput gains from LMUL=4/8. The TVM auto-tuning approach selects LMUL as a tunable parameter, which partially explains its 46% improvement over GCC auto-vec.

## Convolution on RVV

### Algorithm Choices

[supported][src:gupta-conv-rvv-chalmers-2023] The IPDPS 2023 study by Gupta et al. systematically compared convolution algorithms on long-vector architectures (RVV and ARM SVE):

**im2col + GEMM:**
- Most natural mapping: convert convolution to matrix multiply, reuse GEMM micro-kernel
- Memory overhead: im2col expansion increases memory footprint by R*S (kernel height * width), e.g., 9x for 3x3 conv
- On RVV, the im2col transformation itself is vectorizable as unit-stride loads with strided store patterns
- Best at large batch sizes where GEMM efficiency outweighs memory overhead

**Direct Convolution:**
- Avoids im2col memory expansion entirely
- Uses nested loops with vector loads from sliding windows
- Strided loads (`vlsseg`) for input channel dimension; unit-stride for spatial dimension
- Performance depends on VLEN: longer vectors amortize the loop overhead of sliding window shifts
- At 4096-bit VLEN, direct convolution approaches im2col+GEMM efficiency because the sliding window fits in vector registers

**Winograd Convolution:**
- Uses minimal filtering theory: F(2x2, 3x3) reduces multiply count by 2.25x
- Transform overhead: input/output transforms add vector operations that are proportional to tile count
- On RVV, Winograd transforms are element-wise vector ops (very efficient)
- Best at smaller VLEN (128-256 bit) where transform overhead is a smaller fraction of total work
- At larger VLEN, Winograd's advantage diminishes because GEMM efficiency improves and transform overhead scales

[inference][src:gupta-conv-rvv-chalmers-2023][src:perotti-rvv-embedded-ml-2024] No single convolution algorithm dominates across all RVV configurations. The optimal choice depends on:
- VLEN (longer vectors favor direct + GEMM)
- Cache size (larger cache favors im2col)
- Kernel size (3x3 favors Winograd; 7x7+ favors direct)
- Stride and dilation (irregular strides penalize im2col)

### The Convolution Mapping Table

| Algorithm | Best VLEN Regime | Memory Overhead | Compute Efficiency | RVV Suitability |
|-----------|-----------------|-----------------|-------------------|-----------------|
| im2col+GEMM | All VLEN | High (R*S) | Highest (reuses GEMM micro-kernel) | Good: im2col is vectorizable |
| Direct | VLEN >= 1024 | None | Moderate (sliding window overhead) | Good: strided loads available |
| Winograd | VLEN <= 256 | Low (transform constants) | High (fewer multiplies) | Very good: transforms are vector ops |

## Attention Mechanisms on RVV

[supported][src:garcia-llm-rvv-sophgo-2025] The 2025 study evaluating LLM inference on a 64-core RISC-V CPU (SG2042, RVV 0.7.1) provides initial data points for attention on RVV. Findings are limited by the pre-ratification RVV version and the absence of optimized fused kernels.

### QKV Projection

- Maps as batch GEMM of dimension (B * S, D) x (D, 3D_h * H)
- The same RVV GEMM micro-kernel applies, tiled over the batch*sequence dimension
- No special attention-specific optimization -- identical to any other GEMM call in the model
- CUBLAS-style batched GEMM is not an RVV instruction; the loop over heads is handled by the compiler or TVM schedule

### Scaled Dot-Product Attention

The core operation S = Q x K^T (scaled) followed by softmax and P x V:

1. **QK^T multiply**: GEMM of dimension (B*H*S, D_h) x (B*H*D_h, S). Each head is a small GEMM (typical D_h=64-128). On RVV, these small dimensions favor direct vector matmul over tiled GEMM because tile overhead dominates at small sizes.

2. **Scaling**: Element-wise `vfmul` with scalar `1/sqrt(D_h)`.

3. **Softmax reduction**:
   - Find max: `vfredmax` across S dimension
   - Subtract max: `vfsub` (numerical stability)
   - Exponentiate: `vfexp` (polynomial approximation or lookup)
   - Sum: `vfredsum`
   - Normalize: `vfdiv`
   - All softmax operations are vectorizable and map naturally to RVV vector instructions

4. **PV multiply**: Another small GEMM of dimension (S, D_h) x (D_h, S). Same as step 1.

[inference][src:garcia-llm-rvv-sophgo-2025] The challenge for attention on RVV is not instruction availability but kernel fusion. FlashAttention-style fused kernels that avoid materializing the full SxS attention matrix require either:
- TVM/MLIR-level fusion of the softmax reduction with the matrix multiply
- Or explicit fused kernel implementations with tile-level control flow

RVV's VLA model makes tile-level control flow within fused kernels harder to express than in CUDA, where tile shapes are compile-time constants. The TVM MetaSchedule approach can explore fusion strategies, but its auto-tuning cost limits per-kernel exploration.

### Comparison with CUDA FlashAttention

| Aspect | CUDA FlashAttention | RVV Approach |
|--------|-------------------|--------------|
| Tiling | 2D tile over S and D_h, shared memory staging | Strip-mined 1D or 2D tile, registers only |
| Softmax online | Online softmax with tile-level rescaling | Serial softmax per S-dimension (no shared memory) |
| Memory hierarchy | Global -> shared -> registers | Global -> L1/L2 -> registers (CPU cache) |
| Synchronization | __syncthreads between tiles | No synchronization needed (single-thread vector) |
| Fused kernel | Fused matmul+softmax+matmul in one kernel | Needs compiler fusion; not available in standard libraries |

[open] FlashAttention-style online softmax fusion on RVV has not been demonstrated in published work. The key question is whether CPU cache hierarchy can replace shared memory for tile-level data reuse in fused attention kernels, or whether register-only tiling forces smaller tiles that reduce arithmetic intensity below the roofline balance point.

## Element-Wise and Normalization Operations

### Element-Wise Activation Functions

[supported][src:perotti-rvv-embedded-ml-2024][src:riscv-v-spec-ratified-2021] Element-wise operations on RVV achieve the highest mapping efficiency among all AI kernel types because they are uniform vector operations with no cross-element dependency:

- **ReLU**: `vfmax.vf vd, vs2, f0` (max with zero) -- single instruction
- **GELU**: Polynomial approximation using `vfmul`, `vfadd`, `vfmacc` -- fully vectorized
- **Sigmoid / Tanh**: Table lookup with polynomial interpolation, or direct polynomial approximation
- **SiLU / Swish**: `vfdiv`, `vfadd`, `vfmul` for x * sigmoid(x)

The mask register (v0) handles activation function variants with conditional behavior (e.g., PReLU with learned negative slope). Unlike CUDA where divergent activations cause warp serialization, RVV masking has no performance penalty beyond the additional mask operation itself.

### Layer Normalization

[inference][src:garcia-llm-rvv-sophgo-2025][src:greenblatt-tvm-rvv-autotune-2026] LayerNorm on RVV follows a natural three-pass vector reduction pattern:

1. **Mean computation**: `vfredsum` across the hidden dimension to compute sum, then `vfdiv` for mean
2. **Variance computation**: `vfsub` (x - mean), vfmul (square), `vfredsum` (sum of squares), `vfdiv` for variance
3. **Normalization**: `vfsub` (x - mean), `vfdiv` by sqrt(var + epsilon)

Each step uses the full vector width. The three sequential passes are unavoidable (each depends on the previous), creating a dependency chain that limits throughput on narrow VLEN units.

[speculative] LayerNorm on RVV is expected to be memory-bandwidth-bound on edge SoCs (K1, C908) and compute-bound on server-class implementations (Veyron V2). The reduction passes require full-vector-width reads of the input -- the 32 KB L1 D-cache on the K1 can hold only 8192 FP32 elements, so large hidden dimensions (D >= 4096) may spill to L2.

### Batch Normalization and RMSNorm

- BatchNorm: Training mode requires running statistics across batch dimension (not trivially vectorized); inference mode is element-wise (`vfsub` mean, `vfdiv` std)
- RMSNorm: Simplified LayerNorm without mean subtraction -- two passes (RMS computation + normalize) instead of three

## Comparison with CUDA Kernel Patterns

### Structural Differences

| Aspect | CUDA Kernel | RVV Kernel |
|--------|------------|------------|
| Parallelism model | Thousands of threads grouped into warps | Single thread with explicit vector length (strip-mining) |
| Tiling mechanism | Thread block + shared memory + warp-level ops | Strip-mined loops + LMUL register grouping |
| Synchronization | __syncthreads, __syncwarp, cooperative groups | None (single-thread) -- synchronization is between CPU threads/DMA |
| Divergence handling | Warp serialization for divergent branches | Masked execution (no performance penalty for masked-off lanes) |
| Memory hierarchy | Global -> shared memory -> registers (explicit) | Global -> L1/L2/LLC cache -> registers (implicit hardware cache) |
| Fused kernels | Manual: one kernel launch, multiple operations | TVM/compiler fusion required; single-thread sequential |
| Occupancy tuning | Occupancy-constrained by register count, shared memory, block size | Not applicable: single thread uses all available vector resources |
| Micro-kernel | Warp-level matrix multiply (mma.sync / wmma) | Outer-product vfmacc with LMUL grouping |

### When Each Model Excels

[supported][src:ventus-gpgpu-whitepaper] **RVV advantages:**
- No thread scheduling overhead: all compute is explicit in the single instruction stream
- No synchronization cost: element-wise and reduction kernels run without barrier overhead
- Masking has no warp divergence penalty: uniform cost for all elements regardless of mask status
- CPU cache hierarchy reduces need for explicit shared memory management (but gives up predictable latency)

**CUDA advantages:**
- Shared memory enables cooperative tiling: threads in a warp can exchange data without register spills
- Tensor Cores provide 10-100x higher peak throughput than vector units for matrix math
- Warp-level shuffle provides cross-lane data exchange that RVV's vrgather cannot match for arbitrary permutation
- Occupancy-based latency hiding works for irregular workloads where vector chaining cannot

[inference][src:greenblatt-tvm-rvv-autotune-2026][src:ventana-veyron-v2-rvv-2023] The comparison gap narrows significantly when RVV implementations reach 512+ bit VLEN with LMUL=8. A 512-bit RVV unit at 3.6 GHz delivers ~0.5 TFLOPS FP32 per core. A 32-core cluster at ~16 TFLOPS FP32 competes with GPU ranges (A100: ~19.5 TFLOPS FP32). However, this comparison ignores the GPU's Tensor Core advantage (~312 TFLOPS FP16 on A100) which remains unapproachable for pure vector RVV.

## Open Questions

- VERIFY: What are the maximal practical GEMM tile sizes (Mr, Nr) for various RVV VLEN (128/256/512/1024/2048) without register spilling? Current evidence is from TVM auto-tuning on 256-bit only.
- VERIFY: Can FlashAttention-style online softmax fusion be implemented on RVV using either manual intrinsics or TVM schedules? The key question is whether the CPU cache hierarchy can replace GPU shared memory for tile-level data reuse.
- OPEN: What is the LMUL=8 micro-kernel design for GEMM? Theoretical peak throughput requires LMUL=8, but register pressure from C-tile accumulation may prevent its use for all tile dimensions.
- OPEN: Do RVV strided loads provide efficient convolution performance for non-unit strides (stride=2, 4), or is there a performance cliff? The RVV spec allows up to 2048-element stride, but hardware implementations may pipeline poorly.
- OPEN: For attention on RVV, does the small-D_h regime (D_h=64-128 typical for multi-head attention) favor direct vector matmul over tiled GEMM, and if so, what is the VLEN-dependent crossover point?
- OPEN: Will the RISC-V Matrix Extension (IME/VME/AME) change the GEMM kernel mapping landscape by adding dedicated matrix register files? The SiFive AME proposal adds outer-product accumulation in a matrix register file, which would replace the LMUL-based vector micro-kernel.

## Related Concepts

- [[hw.riscv.vector-extension|RISC-V Vector Extension (RVV 1.0)]] -- parent concept; the vector ISA that kernel patterns target
- [[hw.riscv.vector-memory-hierarchy|RVV Memory Hierarchy]] -- data movement constraints that determine whether kernels are compute-bound or memory-bound
- [[software.compiler.rvv-autovec-quality|RVV Compiler Auto-Vectorization Quality]] -- compiler coverage limits affect which kernels can be mapped via auto-vec vs. requiring manual intrinsics or TVM
- [[hw.riscv.matrix-extension-proposals|RISC-V Matrix Extension Proposals]] -- future extension that could subsume GEMM kernel mapping
- [[hw.gpu.tensor-cores|GPU Tensor Cores]] -- competing approach for matrix multiply acceleration
- [[hw.gpu.simt|GPU SIMT Execution Model]] -- competing execution model for data-parallel compute
- [[programmer.roofline-model|Roofline Performance Model]] -- measures whether kernel implementations are compute or memory bound
- [[software.control.dsl-compiler-runtime|DSL / Compiler / Runtime Stack]] -- enables kernel fusion and auto-tuning approaches that bypass manual kernel implementation
