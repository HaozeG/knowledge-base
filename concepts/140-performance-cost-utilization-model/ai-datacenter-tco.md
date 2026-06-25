---
id: model.ai-datacenter-tco
title: Datacenter Total Cost of Ownership for AI Accelerators
status: draft
layer: 140-performance-cost-utilization-model
layer_path: 140-performance-cost-utilization-model/datacenter/ai-tco
parent: model.riscv.roofline-matrix-performance
secondary_layers: [60-interconnect-power-thermal, 20-manufacturing-process-integration, 160-market-narrative, 130-scale-out-distributed-system]
granularity: model
concept_type: performance_model
scale_scope: [node, rack, cluster, datacenter]
reasoning_roles: [bottleneck, indicator]
tags: [tco, cost-model, datacenter, inference, training, gpu, utilization, power, cooling, pue, token-economics, cloud-vs-onprem]
aliases: [AI datacenter TCO, GPU total cost of ownership, inference cost per token, AI infrastructure economics]
sources: [sciencedirect-lcoai-2026, sitepoint-local-llm-tco-2026, introl-gpu-tco-model-2025, tokens-per-watt-2026-guide, lyceum-cloud-onprem-breakeven-2026, spheron-inference-power-cost-2026]
---

# Datacenter Total Cost of Ownership for AI Accelerators

## First-Principle Explanation

An AI accelerator's performance on paper (peak FLOPs, bandwidth) means nothing without understanding what it costs to own and operate. The first-principle TCO model is:

```text
TCO_per_useful_token = (Capex_amortized + Opex) / useful_tokens_produced
Capex_amortized = (GPU_cost + server_cost + networking_cost + storage_cost + facility_cost) / amortization_hours
Opex = power_cost × PUE + cooling_cost + staffing_cost + maintenance_cost
useful_tokens = peak_tokens × utilization_rate × software_efficiency_factor
```

The organizer's brutal arithmetic: **hardware is only ~35% of 5-year TCO**. The remaining 65% is power, cooling, staffing, networking, and facilities. A $30,000 GPU that sits idle at 25% utilization has 4× the cost per delivered token of the same GPU at 80% utilization. Utilization — not peak performance — is the variable that determines solvency.

- [supported][src:sciencedirect-lcoai-2026] The Levelized Cost of AI (LCOAI) framework integrates hardware depreciation, refresh cycles, cluster topology efficiency, failure rates, PUE, and energy costs into a unified $/inference metric. Analogous to LCOE in energy economics — it enables apples-to-apples comparison across GPU generations, cloud providers, and on-prem deployments.
- [supported][src:introl-gpu-tco-model-2025] A 100-GPU H100 cluster has a 5-year TCO of ~$15.7M, of which hardware is ~35% ($5.3M). Annual OpEx is $1.4M (power, cooling, space, licenses). Personnel (4-6 FTEs) adds $745K-$1.12M/year. Hardware cost is visible upfront; everything else is hidden and recurring.
- [supported][src:tokens-per-watt-2026-guide] Tokens per watt has become the defining metric in 2026 because datacenters are power-capped, not space-capped. A power-constrained datacenter that can draw 10 MW doesn't care about FLOPs — it cares about tokens per megawatt-hour.

## The TCO Model Decomposed

### Capex Components

| Component | 100-GPU H100 Cluster | % of Capex | Notes |
|---|---|---|---|
| GPU hardware (100× H100) | $3,000,000 | 57% | $30K/GPU at stabilized pricing |
| Compute servers | $500,000 | 9% | 13× 8-GPU nodes |
| Networking (InfiniBand NDR) | $450,000 | 8% | 400 Gb/s per GPU |
| Storage (5 PB NVMe) | $600,000 | 11% | Training data + checkpoints |
| Power infrastructure | $400,000 | 8% | Redundant PDUs, UPS, generators |
| Cooling systems | $350,000 | 7% | Liquid cooling or CRAC units |
| **Total Capex** | **$5,300,000** | 100% | |

- [supported][src:introl-gpu-tco-model-2025] Above ~50 GPU scale, networking and storage become significant line items. At 100 GPUs, networking (InfiniBand) is 8% of Capex. At 1,000 GPUs, networking can exceed 15% due to multi-tier switch fabrics.
- [inference] GPU cost as a fraction of total Capex declines with scale: at 8 GPUs it's ~80% (one server, simple networking); at 1,000 GPUs it's ~50% (scale-out networking, distributed storage, facility-level power/cooling dominate).

### Opex Components

| Component | Annual Cost | % of Annual Opex | Notes |
|---|---|---|---|
| Electricity (GPU + overhead) | $732,000 | 51% | 1.76 MW × $0.12/kWh × 1.4 PUE |
| Staffing (4-6 FTEs) | $745,000-$1,120,000 | 52-60% | ML ops, sysadmin, network, facilities |
| Maintenance contracts | $250,000 | 18% | Server/GPU vendor support |
| Colocation/space | $180,000 | 13% | 10-15 racks at $1,500/rack/month |
| Software licenses | $60,000 | 4% | Cluster management, monitoring |

- [inference] Staffing dominates at small scale (1-8 GPUs: $2.85/GPU/hour for a $200K engineer managing 8 GPUs). At 128 GPUs managed by the same engineer, it drops to $0.18/GPU/hour. This is the primary economic argument for scale — and the primary reason cloud GPU providers can profitably undercut small on-prem deployments.

### The PUE Multiplier

- [supported][src:spheron-inference-power-cost-2026] PUE (Power Usage Effectiveness) directly multiplies every electricity dollar. A 1,000-GPU H100 cluster at PUE 1.45 vs. 1.15 at $0.12/kWh differs by ~$32,700/month (~$1.18M over 36 months) — same GPUs, same workloads, purely from cooling choice.
  - Air-cooled: PUE 1.3-1.5 (30-50% overhead)
  - Liquid-assisted (DLC, rear-door HX): PUE 1.1-1.2 (10-20% overhead)
  - Immersion cooling: PUE 1.03-1.05 (3-5% overhead)
- [inference] At Blackwell/Rubin rack densities (30-100 kW/rack), air cooling is impossible — the cooling plan is no longer a facilities afterthought but a first-order GPU purchasing decision. Under a power cap, liquid cooling provides ~17% more tokens per megawatt than air cooling with identical GPUs.

## Utilization: The Variable That Decides Everything

- [supported][src:lyceum-cloud-onprem-breakeven-2026] The on-prem vs. cloud break-even is almost entirely a utilization question:
  | GPU Utilization | Recommendation |
  |---|---|
  | <40% | Cloud only — on-prem fixed costs dominate |
  | 40-60% | Cloud primary, on-prem for predictable base load |
  | 60-70% | Break-even zone — model carefully with actual workload patterns |
  | 70-85% | On-prem primary, cloud burst for spikes |
  | >85% | On-prem maximum ROI |

- [speculative] The utilization curve is non-linear: a cluster at 25% utilization costs 4× per delivered token vs. the same cluster at 80%. But above 85%, queueing delays degrade user experience — the "optimal" utilization is 75-85%, not 100%. The gap between 75% and 85% is the difference between a money-losing and a money-making AI deployment.

## Cost Per Token Economics

- [supported][src:sitepoint-local-llm-tco-2026] Self-hosted Llama 3.1 70B on 8× H100: ~$1.90/M tokens (FP16), ~$0.95-1.10/M tokens (FP8). At 50M tokens/day with 36-month amortization: ~$7.15/M tokens. API pricing for equivalent quality (GPT-4.1): $2.00/M input, $8.00/M output.
- [supported][src:tokens-per-watt-2026-guide] Software optimization compounds faster than hardware refresh cycles. The B200 went from ~$0.11/M tokens at launch to ~$0.02/M tokens two months later — same silicon, same power draw, only the serving stack improved. Quantization (FP16→FP8): ~2× cost reduction. Continuous batching: ~3-4× utilization improvement. Speculative decoding: ~2-3× throughput increase. Combined: ~16× effective cost reduction vs. naive deployment.
- [inference] The compounding effect of software optimizations means that **TCO models must be dynamic, not static**. A TCO model written when a GPU launches will be wrong within 3 months as the serving stack matures. The B200's 5.5× cost improvement in 2 months is not unusual — it's the norm for new hardware platforms.

## Cloud vs. On-Prem Break-Even

- [supported][src:lyceum-cloud-onprem-breakeven-2026] Cloud on-demand GPU pricing is 3-10× the effective cost of owned hardware for continuous 24/7 workloads. But cloud's advantage is flexibility: no capital commitment, instant scale-up/down, and the provider absorbs utilization risk. The break-even depends on utilization:
  - At 25% utilization: cloud always wins
  - At 50% utilization: on-prem breaks even at ~4-6 months
  - At 80% utilization: on-prem breaks even at ~2-3 months
- [speculative] For RISC-V AI accelerators, the cloud vs. on-prem calculus is different: there is no RISC-V cloud GPU market (yet). RISC-V AI hardware is on-prem by default. The lack of a cloud rental market for RISC-V accelerators is a structural disadvantage — it eliminates the "try before you buy" path and forces capital commitment upfront.

## Geography Arbitrage

- [supported][src:spheron-inference-power-cost-2026] Electricity cost varies ~3× across geographies: Pacific NW hydro (~$0.04/kWh) vs. California (~$0.18-0.22/kWh). For a 1,000-GPU H100 cluster consuming 1.76 MW, the 3-year electricity cost spread between cheapest and most expensive US markets is ~$9.6M — more than the cost of 300 additional H100s.
- [inference] Geography arbitrage is one of the largest and most underappreciated levers in AI TCO. Moving a 1,000-GPU training cluster from California to the Pacific Northwest saves $7M over 3 years in electricity alone — enough to buy 230 additional H100s. The constraint is latency: inference must be close to users; training can be anywhere with sufficient power and cooling.

## Implications for RISC-V AI TCO

- [speculative] RISC-V AI accelerators have a structural TCO advantage and a structural TCO disadvantage:
  - **Advantage**: lower per-chip cost (no licensing fees, simpler designs on mature nodes). A RISC-V accelerator on 12nm might cost $50-200/chip vs. $30,000 for an H100. This changes the utilization math: low utilization hurts a $30K GPU much more than a $200 accelerator. RISC-V can profitably serve workloads where GPU utilization would be uneconomical.
  - **Disadvantage**: no cloud rental market (no "try before you buy"), no established software stack (higher staffing cost for custom integration), lower per-chip throughput (need more chips for the same workload, increasing networking and power costs). The TCO advantage erodes at scale where GPU utilization approaches 80%+ and software maturity reduces staffing overhead.
- [inference] The sweet spot for RISC-V AI TCO is moderate-scale inference (1-10M tokens/day) with predictable workloads where GPU utilization would be 30-50% — too high for cloud to be cheap, too low for GPU on-prem to be efficient. This is the "RISC-V TCO window" — and it closes as inference volumes scale up.

## Open Questions

- OPEN: What is the actual TCO per token for a RISC-V AI accelerator in production? No published TCO data exists for any RISC-V AI deployment at scale. The economic case is entirely model-based, not empirical.
- OPEN: At what inference volume does the RISC-V TCO advantage over GPU disappear? The crossover depends on RISC-V accelerator throughput, GPU utilization at that volume, and the rate of GPU software stack improvement. Preliminary modeling suggests 10-50M tokens/day as the crossover range, but this is highly sensitive to assumptions.
- OPEN: Will a RISC-V cloud GPU market emerge? The absence limits RISC-V's ability to capture the "try before you buy" segment. A RISC-V cloud offering (akin to AWS Graviton for ARM servers) would be transformative for RISC-V AI adoption.
- VERIFY: LCOAI is a newly proposed framework (2026); adoption and validation across real deployments are pending.
- VERIFY: All cost-per-token figures are vendor-provided or analyst-estimated; actual production costs are confidential. The B200 $0.11→$0.02 trajectory is from a single industry blog post, not audited data.
