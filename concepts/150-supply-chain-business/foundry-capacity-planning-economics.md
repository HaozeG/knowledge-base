---
id: industry.foundry.capacity-planning-economics
title: Semiconductor Foundry Capacity Planning and Wafer Allocation Economics
status: draft
layer: 150-supply-chain-business
layer_path: 150-supply-chain-business/foundry/capacity-planning-economics
parent: stack.ai-accelerator-ontology
secondary_layers: [20-manufacturing-process-integration, 140-performance-cost-utilization-model]
granularity: concept
concept_type: business_constraint
scale_scope: [ecosystem]
reasoning_roles: [bottleneck, constraint, indicator]
tags: [foundry, capacity-planning, tsmc, wafer-allocation, semiconductor-economics]
aliases: [wafer capacity planning, TSMC allocation, foundry economics, semiconductor investment cycle]
sources: [tsmc-capacity-expansion-2025]
---

# Semiconductor Foundry Capacity Planning and Wafer Allocation Economics

## Overview

Semiconductor foundry capacity cannot be created on demand — a new fab requires 3–5 years from ground-breaking to volume production and costs $20–40B for a leading-edge facility. The foundry wafer allocation "season" (typically Q4 for the following year) determines which chip vendors get how many wafers at which nodes. This allocation process is the single most important supply-side determinant of AI chip availability — more than architecture, more than software, more than demand. TSMC, controlling ~90% of advanced node capacity (<7nm), effectively allocates the global AI computing supply.

- [supported][src:tsmc-capacity-expansion-2025] TSMC's 2025 capital expenditure is ~$35–40B, funding capacity expansion across N3 (3nm, ~100K WPM), N2 (2nm GAA, ~30K WPM initial), and CoWoS advanced packaging (~130K WPM by end-2026). Wafer allocation follows a structured process: customers submit demand forecasts 12–18 months ahead, TSMC allocates capacity based on strategic relationship tier (NVIDIA Tier 1, hyperscalers Tier 2, startups Tier 3), and pricing is negotiated per-allocation — advanced node wafer prices are non-public but estimated at $20–25K per N3 wafer and $25–30K per N2 wafer.
- [inference] The wafer allocation economics create a self-reinforcing cycle: Tier-1 customers (NVIDIA) get guaranteed capacity at volume-discounted pricing, enabling them to ship more chips, grow revenue faster, and commit to larger future allocations. Tier-3 customers (AI chip startups) get residual capacity at premium pricing (if any), constraining their ability to scale and reinforcing Tier-1 dominance. The allocation process is the structural mechanism that perpetuates NVIDIA's market share despite competitive architectures from AMD, Intel, and startups.

## Capacity Investment Cycle

- [inference] The foundry capacity cycle is a classic bullwhip dynamic: AI demand signals in 2024 triggered capacity commitments that deliver wafers in 2027. If AI demand grows faster than TSMC projected in 2024, the 2027 capacity will be insufficient; if AI demand disappoints, the 2027 capacity will be stranded. The semiconductor industry's history is littered with both types of forecasting errors, and the speed of AI market evolution makes accurate 3-year forecasting essentially impossible.
- [inference] The geopolitical dimension compounds the allocation challenge: TSMC's Arizona fabs (5nm and 3nm) are 20–30% more expensive per wafer than Taiwan fabs but qualify for CHIPS Act subsidies and satisfy "trusted foundry" requirements for U.S. government AI chips. The capacity allocation is now a trilateral optimization: commercial customers want the lowest cost (Taiwan), U.S. government customers require trusted foundry (Arizona), and TSMC wants to maximize long-term revenue across both.

## Open Questions

- OPEN: Will the foundry capacity investment cycle create an oversupply situation in 2027–2028 that benefits AI chip buyers but destroys foundry margins, or is AI demand sufficiently elastic to absorb whatever capacity is built?
- OPEN: Can Samsung and Intel Foundry Services break TSMC's near-monopoly on advanced node capacity, or does TSMC's process leadership + capacity scale + customer relationship depth create an insurmountable three-way moat?
- VERIFY: TSMC's wafer prices ($20–30K per advanced wafer) are industry estimates — actual prices are negotiated per customer, per node, per volume tier, and are among the most closely guarded commercial secrets in the semiconductor industry.

## See Also

- [[stack.ai-accelerator-ontology]] — Central ontology that foundry capacity economics underpins.
- [[silicon.process.node-selection-fabrication-ai]] — Process node selection constrained by foundry capacity availability.
- [[industry.ai.supply-chain-bottlenecks]] — Supply chain where foundry capacity is the ultimate bottleneck.
- [[silicon.process.euv-high-na-lithography]] — EUV tool allocation that determines leading-edge wafer capacity.
- [[model.ai-datacenter-tco]] — TCO where wafer cost is the largest single BOM component.
- [[chip.design.eda-and-ai-design-automation]] — EDA tool costs that add to the per-design overhead of each tapeout.
