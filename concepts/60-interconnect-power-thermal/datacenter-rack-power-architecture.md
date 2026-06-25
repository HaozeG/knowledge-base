---
id: system.power.datacenter-rack-power-architecture
title: Datacenter Rack Power Architecture — from 20kW to 200kW AI Racks
status: draft
layer: 60-interconnect-power-thermal
layer_path: 60-interconnect-power-thermal/power/datacenter-rack-architecture
parent: stack.ai-accelerator-ontology
secondary_layers: [120-scale-up-system, 130-scale-out-distributed-system, 140-performance-cost-utilization-model]
granularity: concept
concept_type: architecture_pattern
scale_scope: [rack, datacenter, ecosystem]
reasoning_roles: [constraint, bottleneck, enabler]
tags: [rack-power, datacenter, 200kw, power-distribution, busbar, 48v]
aliases: [AI rack power, datacenter power architecture, 200kW rack, rack-level power delivery]
sources: [nvidia-gb200-rack-power-2025, datacenter-rack-power-evolution-2025]
---

# Datacenter Rack Power Architecture — from 20kW to 200kW AI Racks

## Overview

The transition from air-cooled 20kW racks to liquid-cooled 120–200kW AI racks is the single largest datacenter infrastructure change since the transition from mainframes to commodity servers. A 200kW rack (NVIDIA GB200 NVL72) draws more power than 10 racks of traditional enterprise servers combined, requiring fundamental redesign of power distribution, busbar current capacity, backup power topology, and facility-level electrical infrastructure.

- [supported][src:nvidia-gb200-rack-power-2025] NVIDIA's GB200 NVL72 rack consumes 120–140kW and requires three-phase 480V AC input with on-rack rectification to 48V DC distribution. The 48V busbar carries >2,500A and must maintain <1% voltage droop across the rack height. The rack's power density (140kW per ~1m² footprint) exceeds the cooling and electrical capacity of 90% of existing datacenters — deployment requires greenfield construction or major brownfield retrofit.
- [inference] The rack power architecture defines the envelope of feasible GPU deployment: a datacenter floor with 10MW of electrical capacity can host ~500 traditional 20kW racks (10,000+ servers) or ~70 NVL72 racks (5,040 GPUs). The per-GPU compute density improvement (72 GPUs per rack vs. 8 per traditional server) means fewer racks per MW, but each rack requires fundamentally different electrical, cooling, and structural infrastructure.

## Power Distribution Evolution

| Era | Rack Power | Voltage | Busbar Current | Cooling | Representative |
|---|---|---|---|---|---|
| 2010s (enterprise) | 5–10kW | 208V AC | ~50A | Air | Standard 42U rack |
| 2020s (early AI) | 20–40kW | 415V AC | ~100A | Air + rear-door HX | DGX A100, H100 |
| 2024-25 (liquid) | 50–100kW | 480V 3-phase AC → 48V DC | ~1,000A | Direct-to-chip liquid | DGX B200 |
| 2025-26 (NVL72) | 120–140kW | 480V 3-phase AC → 48V DC | >2,500A | Full liquid (UQD) | GB200 NVL72 |
| 2027 (Rubin) | 200–250kW | TBD (possibly 800V DC) | TBD (>5,000A at 48V) | Two-phase or immersion | Vera Rubin NVL144 |

- [supported][src:datacenter-rack-power-evolution-2025] The transition from 48V to 800V DC rack-level distribution is under active investigation for >200kW racks: at 48V, 250kW requires >5,200A on the busbar — exceeding the practical current-carrying capacity of copper busbars within rack dimensional constraints. 800V DC distribution reduces current to ~310A, making busbar design feasible but requiring new power supply unit (PSU) designs capable of 800V input.

## Open Questions

- OPEN: Will the datacenter industry standardize on 800V DC rack-level distribution (following the automotive industry's 800V EV architecture) or converge on an intermediate voltage (380V DC) that balances current reduction with existing PSU compatibility?
- OPEN: Can existing datacenters be economically retrofitted for >100kW racks, or does the combination of electrical, cooling, and structural requirements make greenfield construction the only viable path for NVL72-class deployments?
- VERIFY: The >5,200A current estimate at 48V for 250kW racks assumes no intermediate voltage step — real rack architectures may distribute at higher voltage and step down at the server level.

## See Also

- [[stack.ai-accelerator-ontology]] — Central ontology that rack power architecture instantiates as a physical constraint.
- [[system.power.ai-accelerator-power-delivery]] — On-die/package PDN that the rack-level power architecture feeds.
- [[system.scale.nvlink-nvswitch-domain]] — NVL72 domain where rack power architecture is co-designed with NVSwitch.
- [[model.ai-datacenter-tco]] — TCO model where rack power infrastructure is a major CapEx component.
- [[silicon.process.node-selection-fabrication-ai]] — Process node choice affects GPU TDP and thus rack power requirements.
- [[hw.riscv.power-thermal-interconnect]] — Power/thermal modeling co-designed with rack power architecture.
