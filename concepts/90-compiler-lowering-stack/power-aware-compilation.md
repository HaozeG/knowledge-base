---
id: software.compiler.power-aware-compilation
title: Power-Aware and Thermal-Aware Compilation for AI Accelerators
status: draft
layer: 90-compiler-lowering-stack
layer_path: 90-compiler-lowering-stack/power-aware/power-thermal-compilation
parent: software.compiler.ml-compiler-lowering-riscv
secondary_layers: [60-interconnect-power-thermal, 100-runtime-execution-system, 140-performance-cost-utilization-model]
granularity: concept
concept_type: compiler_stack
scale_scope: [unit, tile, die]
reasoning_roles: [mapping, enabler]
tags: [compiler, power-aware, dvfs, thermal-aware, energy-efficiency, code-generation, power-gating, ml-accelerator, scheduling]
aliases: [power-aware compiler, DVFS-aware compilation, thermal-aware code generation, energy-optimizing compiler for AI]
sources: [powerflow-dnn-arxiv-2026, ascend-dvfs-acm-2025, zerodvfs-arxiv-2026, hidvfs-arxiv-2026]
---

# Power-Aware and Thermal-Aware Compilation for AI Accelerators

## First-Principle Explanation

A compiler that generates correct code is necessary but not sufficient. A power-aware compiler also decides **when to run fast and when to run slow** — trading performance for energy when the performance isn't needed. The first-principle optimization:

```text
energy_saved = Σ (P_high × t_high - P_low × t_low) for each operator/layer where DVFS is applied
performance_lost = Σ (t_low - t_high) for each operator/layer where DVFS is applied
constraint: total_performance_lost < deadline_slack

The compiler's job: find the Pareto-optimal set of {frequency, voltage, power_gating} for each operator
that minimizes energy subject to the end-to-end latency deadline.
```

The organizer's insight: **AI inference is periodic and deadline-constrained**. A model serving real-time video at 30 FPS has a 33ms deadline per frame — running faster than 33ms wastes energy with zero user-visible benefit. The compiler knows the operator graph, the per-operator execution time at each frequency, and the deadline. It can compute the optimal frequency schedule as an ILP problem.

- [supported][src:powerflow-dnn-arxiv-2026] PowerFlow-DNN achieves energy within 0.68% of the exact ILP oracle for compiler-directed fine-grained power orchestration on a TSMC 40nm DNN accelerator. Up to 37% energy reduction vs. aggressive baselines while handling a combinatorial schedule space of 10¹⁶⁰ states — provably near-optimal.
- [supported][src:ascend-dvfs-acm-2025] Fine-grained DVFS on Ascend NPU at operator granularity achieves 13.44% AI core power reduction and 4.95% NPU chip power reduction with only 1.76% performance degradation on GPT-3 training. The key: temperature-dependent power modeling as convex piecewise linear functions.
- [supported][src:zerodvfs-arxiv-2026] ZeroDVFS demonstrates LLM-guided zero-shot DVFS: 13 code-level semantic features extracted by an LLM enable DVFS scheduling on never-before-seen workloads with 7.09× better energy efficiency and 4.0× better makespan vs. Linux ondemand governor across Jetson TX2, Orin NX, RubikPi, and Intel Core i7.

## Compiler-Directed Power Orchestration

### The Inter-Layer DVFS Problem

- [supported][src:powerflow-dnn-arxiv-2026] PowerFlow-DNN formulates periodic DNN inference as an inter-layer power-scheduling problem. Each layer has a known execution time at each DVFS state. The compiler selects a DVFS state per layer such that:
  1. Total execution time ≤ period deadline
  2. Total energy is minimized
  3. DVFS transitions between layers (voltage/frequency ramp time) are accounted for
  4. The schedule space (10¹⁶⁰ states for a typical DNN) is pruned through ILP formulation
- [inference] The ILP formulation works because the DNN operator graph is (mostly) a linear chain — each layer has one predecessor and one successor. The energy minimization decomposes into a chain-constrained optimization that ILP solvers can handle. For DAGs with branches and merges (e.g., multi-branch networks, MoE), the ILP becomes exponentially harder — but branch-level parallelism provides slack that DVFS can exploit.

### Temperature-Dependent Power Modeling

- [supported][src:ascend-dvfs-acm-2025] The Ascend NPU work demonstrates that power is NOT a linear function of frequency when temperature is considered. As the chip heats up, leakage current increases, making the same frequency draw more power. The compiler must model this temperature-dependent effect: a DVFS schedule that's optimal at 25°C may be suboptimal at 85°C because the leakage penalty at high frequency grows with temperature.
- [speculative] The temperature feedback loop creates a compiler optimization problem with state: the optimal frequency for layer N depends on the chip temperature at the start of layer N, which depends on the power dissipation of layers 1..N-1, which depends on their frequencies. This is a dynamic programming problem with temperature state — the compiler must solve it with a thermal RC model of the chip.

## Scheduling Strategies

### DVFS Granularity Levels

- [inference] Three DVFS granularity levels, in order of increasing energy savings and implementation complexity:
  1. **Workload-level** (coarsest): one frequency for the entire inference. Simple, no compiler changes needed, but leaves most energy savings on the table (only helps when the workload is consistently below deadline).
  2. **Layer-level**: per-layer frequency. PowerFlow-DNN's approach. Captures inter-layer slack (a slow layer followed by a fast layer). Requires the compiler to insert DVFS transition instructions between layers.
  3. **Operator-level** (finest): per-operator frequency within a layer. The Ascend NPU approach. Captures intra-layer slack (e.g., a matmul followed by an element-wise op within the same fused layer). Requires hardware support for millisecond-level DVFS transitions.
- [speculative] Layer-level DVFS captures ~80% of the theoretical energy savings with ~20% of the implementation complexity of operator-level DVFS. The reason: most DNN execution time is concentrated in a few layers (attention, FFN), and those layers have similar optimal frequencies. Operator-level DVFS helps most for fused operators with mismatched compute/memory profiles (e.g., matmul + activation in one kernel).

### Thermal-Aware Scheduling

- [supported][src:hidvfs-arxiv-2026] HiDVFS demonstrates hierarchical multi-agent DVFS scheduling with temperature regularizers. Three collaborative agents (core/frequency selection, core combination management, task priority setting) jointly optimize makespan with a temperature penalty term. Achieves 3.44× speedup over GearDVFS and 50.4% energy reduction on BOTS benchmarks.
- [inference] The temperature regularizer is the key innovation: instead of treating temperature as a hard constraint ("never exceed 85°C"), it's treated as a soft penalty in the optimization objective. This allows the scheduler to occasionally run hot if the performance gain justifies it, while avoiding sustained high-temperature operation that causes throttling.

## Zero-Shot and Learning-Based DVFS

- [supported][src:zerodvfs-arxiv-2026] ZeroDVFS uses LLM-extracted semantic features (13 code-level features: loop count, branch density, memory access pattern, etc.) to guide DVFS decisions on never-before-seen workloads. The LLM doesn't make DVFS decisions — it extracts features that a lightweight RL model uses for scheduling. This enables zero-shot deployment: a new model architecture can be scheduled optimally without profiling it first.
- [speculative] The LLM-as-feature-extractor pattern is architecturally elegant: the LLM brings semantic understanding of code structure ("this is a reduction loop, memory-bound"), while the RL model brings operational knowledge of the hardware ("memory-bound loops benefit from lower frequency because the memory controller is the bottleneck"). The separation keeps the LLM out of the control loop (too slow) while leveraging its code understanding.

## Implications for RISC-V Compilation

- [speculative] RISC-V AI compilation has an untapped power-aware opportunity: the RVV ISA's vl (vector length) register provides a hardware-level knob that GPUs lack. By reducing vl (processing fewer elements per vector instruction), the compiler can reduce per-instruction energy without changing frequency. A 256-bit vector operation at vl=128 (half the elements) uses approximately half the datapath energy. This is a compiler-controlled, instruction-level power scaling mechanism with zero transition latency — no DVFS ramp time.
- [inference] The RISC-V vl-as-power-knob is analogous to SIMD width throttling in x86 (AVX-512 → AVX-256 transitions cause frequency drops) but without the frequency penalty: RISC-V vector instructions at reduced vl don't trigger a frequency change. The compiler can use vl to implement layer-level energy scaling without the DVFS transition overhead that plagues GPU and x86 power management.

## Open Questions

- OPEN: Is operator-level DVFS (millisecond transitions) worth the hardware complexity vs. layer-level DVFS (tens of milliseconds)? The additional energy savings (<5% in the Ascend NPU study) may not justify the hardware cost for most accelerators.
- OPEN: Can LLM-guided zero-shot DVFS generalize across hardware architectures (ARM → RISC-V → x86) or is retraining needed per ISA? ZeroDVFS shows cross-platform results but all platforms are ARM-based.
- OPEN: What is the actual energy savings from RISC-V vl-based power scaling vs. frequency-based DVFS? No published comparison exists. The zero-transition-latency advantage of vl scaling suggests it could outperform DVFS for fine-grained (layer-level) power management.
- VERIFY: PowerFlow-DNN 0.68% optimality gap is against ILP oracle on a specific DNN accelerator at 40nm; results on modern nodes (7nm, 5nm) with different DVFS characteristics may differ.
- VERIFY: Ascend NPU 13.44% power reduction is measured on vendor hardware; independent reproduction on non-Ascend platforms is needed to validate the temperature-dependent power modeling approach.
