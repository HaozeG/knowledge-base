---
id: hw.riscv.power-thermal-interconnect
title: Power and Thermal Modeling for AI Accelerator Interconnects
status: draft
layer: 60-interconnect-power-thermal
layer_path: 60-interconnect-power-thermal/power-thermal/interconnect-modeling
parent: hw.riscv.noc-interconnect-matrix-accelerators
secondary_layers: [10-physical-limits-materials, 20-manufacturing-process-integration, 140-performance-cost-utilization-model]
granularity: concept
concept_type: interconnect_pattern
scale_scope: [unit, tile, die, package, rack]
reasoning_roles: [bottleneck, constraint]
tags: [power-modeling, thermal-management, noc, interconnect, energy-efficiency, pJ-per-bit, liquid-cooling, power-density, dvfs, ai-accelerator]
aliases: [AI interconnect power, NoC energy modeling, thermal design for accelerators, interconnect power wall]
sources: [floonoc-ieee-tvlsi-2025, wedbush-1400w-cooling-2025, siemens-thermal-ai-chip-2026, arteris-noc-power-2025, jetcool-broadcom-2026, ieee-liquid-cooling-25d-2026]
---

# Power and Thermal Modeling for AI Accelerator Interconnects

## First-Principle Explanation

Every bit moved on an AI accelerator costs energy. The first-principle constraint is the **interconnect power wall**:

```text
total_power = compute_power + memory_power + interconnect_power
interconnect_power = Σ(link_energy_per_bit × bandwidth × hop_count)
data_movement_energy / compute_energy ≈ 100-1000× per operation
```

The organizer's brutal reality: moving a 32-bit operand 1 mm across a chip costs ~10× more energy than a 32-bit multiply. Moving it off-chip costs ~100× more. Moving it across a rack costs ~1000× more. This energy hierarchy determines everything about AI accelerator architecture — from PE placement to NoC topology to chiplet partitioning.

- [supported][src:floonoc-ieee-tvlsi-2025] FlooNoC achieves 0.15 pJ/B/hop energy efficiency — 3× better than general-purpose NoCs. At 645 Gb/s/link, each link consumes ~97 mW. An 8×4 mesh (32 routers, 288 RISC-V cores) with aggregate 103 Tb/s bandwidth consumes ~15.5 W in the NoC alone.
- [supported][src:arteris-noc-power-2025] Data movement is the dominant energy cost in modern SoCs, with 10-13% of chip silicon area dedicated to interconnect logic. For AI accelerators with high PE counts and large shared scratchpads, interconnect power can exceed 20% of total chip power.
- [supported][src:wedbush-1400w-cooling-2025] AI accelerator TDPs have crossed the 1,400W barrier (NVIDIA GB300, AMD MI355X), with 2026 projections reaching 1,800-2,300W (NVIDIA Rubin). At these power levels, every watt saved in the interconnect directly reduces cooling cost and prevents thermal throttling.

## Interconnect Power Modeling

### Energy Breakdown per Bit-Meter

- [inference] The energy cost hierarchy for data movement in AI accelerators:
  | Movement Type | Energy (pJ/bit) | Relative to 32b MAC | Notes |
  |---|---|---|---|
  | Register file access | 0.02-0.05 | 0.01× | Within a PE |
  | PE-to-PE (adjacent, NoC) | 0.15 (FlooNoC) | 0.1× | 1-hop on optimized NoC |
  | L1 scratchpad access | 0.5-2 | 0.3-1× | Shared across PE cluster |
  | Cross-cluster NoC (multi-hop) | 0.5-5 | 1-3× | Mesh/torus routing |
  | L2/L3 cache access | 5-20 | 3-12× | Larger arrays, longer wires |
  | HBM access (on-package) | 3-7 (HBM3e) | 2-4× | Through silicon interposer |
  | Inter-chiplet (UCIe D2D) | 0.25-0.5 | 0.15-0.3× | Advanced packaging |
  | Inter-chip (NVLink, PCIe) | 20-50 | 12-30× | Off-package |
  | Inter-node (Ethernet/IB) | 500-2000+ | 300-1200× | Across rack/datacenter |

- [speculative] The 3-orders-of-magnitude range in energy cost per bit explains why AI accelerator architecture is fundamentally a data-locality optimization problem. Every level of the memory hierarchy exists to keep data at the lowest energy tier for as many operations as possible before moving it to a higher energy tier.

### NoC Power Components

- [inference] NoC power breaks down into:
  1. **Link power** (~60%): driving wires between routers. Scales with link width × frequency × wire length. Wide links (FlooNoC's AXI4-compliant multi-byte links) amortize router overhead but increase per-link energy.
  2. **Router power** (~30%): crossbar switching, buffer SRAM, arbitration logic. Scales with port count × flit width. Each additional port adds ~15% router power.
  3. **Clock/power distribution** (~10%): clock tree and power grid losses across the NoC fabric.
- [speculative] The 0.15 pJ/B/hop in FlooNoC is achieved by: wide links (amortize per-flit overhead), dedicated physical links for control (avoid arbitration on latency-critical paths), and minimizing buffer depth (AI bulk transfers don't need deep buffering).

### Interconnect Power Scaling with PE Count

- [inference] For an N-PE accelerator with mesh NoC:
  ```text
  interconnect_power(N) ∝ N × avg_hop_count × link_power_per_hop
  avg_hop_count ≈ √N for 2D mesh
  interconnect_power(N) ∝ N^1.5
  ```
  This N^1.5 scaling means interconnect power grows faster than compute power (which scales ~N). At some PE count, interconnect power dominates total chip power. This is the **interconnect-limited scale ceiling**.
- [speculative] MemPool-Spatz's 1024-PE shared-L1 cluster is a direct response to this scaling law: by using a single-hop shared L1 (crossbar) instead of a multi-hop mesh, avg_hop_count = 1 regardless of PE count, recovering linear scaling. The cost is crossbar area and wiring, which grow with N² — a different limit.

## Thermal Modeling and Management

### The Power Density Crisis

- [supported][src:wedbush-1400w-cooling-2025] AI accelerator TDPs: NVIDIA B200 (1,000-1,200W), GB300 (1,400W), Rubin R100 (1,800-2,300W projected), Rubin Ultra (3,600W projected by 2027). At these power levels, traditional air cooling is obsolete — chips lose up to 30% peak performance to thermal throttling without liquid cooling.
- [supported][src:siemens-thermal-ai-chip-2026] Power density has become the critical metric, not total power. Sustained heat flux of 4 W/mm² per device is now the design target for multi-kilowatt ASICs. 3D IC hotspots can reach power densities compared to "the surface of the sun."
- [inference] For multi-PE RISC-V accelerators at lower power levels (25-200W), the thermal challenge is different: not total heat removal but **hotspot management**. A cluster of 256 PEs doing synchronized GEMM creates a concentrated hotspot that can exceed local thermal limits even when total chip power is within budget.

### Thermal-Aware Interconnect Design

- [speculative] Three thermal-aware design strategies for AI accelerator interconnects:
  1. **Activity migration**: the runtime scheduler rotates GEMM tile assignments across PEs to spread thermal load over time, preventing sustained hotspots. Analogous to wear leveling in SSDs.
  2. **Thermal-aware routing**: the NoC router avoids paths through thermally stressed regions, adding 1-2 extra hops to route around hotspots. The energy cost of extra hops is offset by preventing thermal throttling of compute units.
  3. **DVFS for interconnect**: link frequency and voltage are independently scaled based on utilization. During memory-bound kernel phases (low compute, high data movement), link frequency is increased; during compute-bound phases, link frequency is reduced to lower interconnect power and redirect thermal budget to compute units.

### Cooling Technology Landscape

- [supported][src:jetcool-broadcom-2026] Direct-to-chip liquid cooling targeting multi-kilowatt ASICs at 4 W/mm² heat flux is now production-ready (JetCool/Flex/Broadcom collaboration). Manifold-jet impingement microchannel cooling demonstrated at 2,500W load with thermal resistance of 0.028 K/W.
- [supported][src:ieee-liquid-cooling-25d-2026] Integrated diamond heat spreaders with embedded microfluidic channels achieve 0.02°C/W thermal resistance under 2,000W load — 50% reduction over passive diamond spreaders. This is critical for 2.5D/3D integrated AI accelerators where chiplets and HBM stacks create multi-level thermal interfaces.
- [speculative] For RISC-V AI accelerators at edge/embedded power levels (<100W), passive cooling remains viable, but the trend toward higher PE counts (MemPool's 1024 FPUs) pushes even "low-power" designs into active cooling territory. The thermal design point shifts from "can we cool it?" to "can we cool it without destroying the cost advantage?"

## Power/Performance/Cost Tradeoffs

- [inference] The interconnect power wall creates a trilemma:
  ```text
  high_bandwidth → wide_links × high_frequency → high_interconnect_power → cooling_cost
  low_interconnect_power → narrow_links × low_frequency → bandwidth_bottleneck → PE_starvation
  wide_links × low_frequency → moderate_bandwidth + moderate_power → area_cost (wider wires need more metal layers)
  ```
  FlooNoC's solution (wide links at moderate frequency, 0.15 pJ/B/hop) optimizes the energy-per-bit metric rather than raw bandwidth or raw power. The key insight: for AI bulk transfers, energy efficiency matters more than peak bandwidth because transfers are large and regular.

- [speculative] For RISC-V AI accelerators specifically, the power modeling challenge is different from GPUs: RISC-V designs span 4 orders of magnitude in power (0.1W edge inference to 200W+ datacenter), and a single power model cannot cover this range. The interconnect power model must be parameterized by PE count, process node, link width, and topology.

## Open Questions

- OPEN: At what PE count does interconnect power exceed compute power for a RISC-V mesh NoC? The N^1.5 scaling law suggests a crossover at ~500-1000 PEs for current technology, but real silicon data is unavailable.
- OPEN: Can thermal-aware runtime scheduling (activity migration, thermal-aware routing) achieve >10% sustained performance improvement, or is the benefit limited to 2-5%? Published results are simulation-only and vary widely by workload.
- OPEN: What is the energy-optimal NoC topology for AI matrix workloads specifically? Mesh (regular, simple) vs. concentrated mesh (fewer routers, more PEs per router) vs. tree (lowest hop count for broadcast, worst for all-to-all)? The answer depends on the communication pattern mix (broadcast weights, reduce gradients, all-to-all for attention).
- VERIFY: FlooNoC 0.15 pJ/B/hop is simulated at 12nm; silicon validation would likely show higher energy due to routing congestion and clock tree losses not captured in simulation.
- VERIFY: The 1,400W-to-3,600W TDP trajectory is based on vendor roadmaps and analyst projections; actual shipping silicon TDPs may differ.
