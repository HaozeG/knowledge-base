---
id: industry.ai.inference-as-a-service
title: AI Inference-as-a-Service and the Neocloud Economy
status: draft
layer: 150-supply-chain-business
layer_path: 150-supply-chain-business/inference/inference-as-a-service
parent: industry.riscv.ai-supply-chain
secondary_layers: [130-scale-out-distributed-system, 140-performance-cost-utilization-model, 160-market-narrative]
granularity: overview
concept_type: business_constraint
scale_scope: [ecosystem]
reasoning_roles: [enabler, bottleneck]
tags: [inference, inference-as-a-service, neocloud, token-economics, gpu-marketplace, business-model, utilization, margin, ai-economy]
aliases: [inference-as-a-service, AI token economics, GPU neocloud economy, model hosting business models]
sources: [nasdaq-digitalocean-inference-2026, rafay-nvidia-token-factory-2026, creandum-hostedai-neocloud-2026, htx-inference-scarcity-2026, baseten-inference-ipo-2026, infinitix-gpu-economy-2026]
---

# AI Inference-as-a-Service and the Neocloud Economy

## First-Principle Explanation

The AI infrastructure business is splitting into two economies with fundamentally different unit economics:

```text
Training economy:  one-time CapEx, sells GPU-hours, fixed capacity, margin = price - cost/hour
Inference economy: recurring OpEx, sells tokens, elastic capacity, margin = price/token - cost/token

The training-to-inference revenue pivot: GPU-hour model → $18K/GPU/year. Token model → $158K/GPU/year.
Same hardware. Different business model. 8.6× revenue difference.
```

The organizer's insight: **the inference economy is 10-50× larger than the training economy by volume, but GPU-hour pricing models capture only a fraction of the value**. Moving from selling GPU-hours (a commodity) to selling tokens (a differentiated service) is the economic transformation driving the AI infrastructure market in 2025-2026.

- [supported][src:baseten-inference-ipo-2026] Inference providers are growing at explosive rates: Baseten reached ~$600M ARR by Q1 2026 (from $200M earlier in the quarter), Together AI surpassed $1B ARR at $7.5B valuation, and Modal reached $3B ARR at $4.65B valuation. These are pure inference-play companies — they don't train models, they serve them.
- [supported][src:nasdaq-digitalocean-inference-2026] DigitalOcean reported 70% of its $120M AI customer ARR came from higher-margin inference services and core cloud products, not bare metal GPU rentals. Inference demand still exceeds supply, with pricing holding or rising.
- [supported][src:htx-inference-scarcity-2026] JP Morgan estimates the inference market at 10-50× the size of training. Anthropic took over SpaceX's entire Colossus 1 datacenter (220K+ GPUs, 300+ MW) in May 2026 and dedicated it entirely to inference — not training.

## The GPU-to-Token Business Model Pivot

### Unit Economics

| Metric | GPU-as-a-Service (GaaS) | Token-as-a-Service (TaaS) |
|---|---|---|
| Pricing unit | $/GPU-hour | $/million tokens |
| Revenue per H100/year (70% util) | ~$18,400 | ~$157,680 |
| Revenue per B200/year (60% util) | ~$26,000 | ~$315,360 |
| Gross margin | 14-16% | 40-70%+ |
| Hardware refresh sensitivity | Extreme (6-12 month cycles) | Moderate (inference more forgiving) |
| Differentiation | None (commodity) | Model quality, latency, routing |

- [supported][src:rafay-nvidia-token-factory-2026] NVIDIA's Token Factory offering (March 2026) turns GPU clusters into self-service AI monetization engines. The key insight: new GPU generations deliver 10-35× inference throughput improvement, which in a token model translates directly into higher revenue. In a GPU-hour model, that throughput gain is invisible to the top line.
- [inference] The GPU-hour model has a structural flaw: it charges for time, not value. A Blackwell GPU serving 10× more tokens per second than a Hopper GPU should generate 10× more revenue — but at $/hour pricing, it generates the same revenue (actually less, since Blackwell GPUs face faster depreciation). The token model aligns pricing with value delivered.

## The Neocloud Market Structure

### Growth and Fragmentation

- [speculative][src:creandum-hostedai-neocloud-2026] Neoclouds — independent GPU-as-a-Service operators — have grown >200% in the past year, with Forrester forecasting $20B in 2026 revenue. Over 100 neoclouds exist globally, 10-15 at scale. The market is highly fragmented, creating an opportunity for aggregation.
- [inference] The fragmentation has structural causes: GPU supply is constrained (only NVIDIA makes H100/B200), demand is insatiable (every AI company needs inference capacity), and the barriers to entry are low (lease GPUs, rent datacenter space, install Kubernetes). But the barriers to profitability are high — McKinsey reports GPU rental gross margins at only 14-16%.

### The Margin Problem

- [speculative] The neocloud margin problem is a textbook commodity trap: GPU rental is undifferentiated (an H100 is an H100 regardless of who rents it), switching costs are zero (APIs are interchangeable), and the hyperscalers (AWS, Azure, GCP) have structural cost advantages (power purchase agreements, custom silicon, amortized facilities). The only way out is differentiation — moving up the stack to higher-margin inference services.
- [supported][src:creandum-hostedai-neocloud-2026] Hosted·ai addresses the margin problem through GPU virtualization: software that enables 3-5× GPU overcommitment through dynamic memory caching, turning negative-margin operators profitable within 12 months without additional CapEx. The industry-average GPU utilization is ~13% (Wesco analysis of 4,000+ K8s clusters); even OpenAI operates at ~33%.

## The Aggregation Layer

### Capital-Light Marketplace Model

- [speculative][src:htx-inference-scarcity-2026] The most interesting business model innovation is the capital-light GPU marketplace (Hyperbolic). The thesis: aggregate fragmented GPU supply from 100+ neoclouds, route inference requests to the cheapest/fastest available GPU, capture a spread without owning hardware. This is structurally analogous to Uber (aggregate fragmented driver supply) or Airbnb (aggregate fragmented room supply).
- [inference] The capital-light model has a structural advantage in a deflationary hardware market: as GPU prices fall (new generations arrive every 6-12 months), hardware-heavy operators suffer depreciation, but capital-light aggregators profit from increased fragmentation and price competition. The aggregator wins whether GPU prices go up (supply shortage → spread widens) or down (oversupply → fragmentation increases).

### The Token Factory Model

- [supported][src:rafay-nvidia-token-factory-2026] The alternative model is vertical integration (NVIDIA's Token Factory): pair GPU infrastructure with cloud services (storage, databases, networking), deploy models as scalable APIs, meter by token consumption. DigitalOcean's "Agentic Inference Cloud" is the exemplar — 70% of AI revenue from higher-margin services, not bare metal.
- [inference] The vertical integration vs. aggregation debate is unresolved. Vertical integration captures more margin per transaction but requires CapEx and operational complexity. Aggregation captures less margin but requires no CapEx and scales with market fragmentation. The likely outcome: both models coexist, with hyperscalers vertically integrated and neoclouds aggregated through marketplaces.

## Implications for RISC-V AI

- [speculative] The inference-as-a-service economy creates a structural opportunity for RISC-V AI hardware:
  1. **Token economics favor low-cost hardware**: in a token model, revenue per GPU is proportional to throughput. A RISC-V accelerator delivering 1/10 the throughput of an H100 at 1/100 the cost is 10× more profitable per dollar invested — even if it's slower per chip.
  2. **Utilization is the binding constraint**: industry-average GPU utilization is 13-33%. RISC-V's architectural flexibility (right-size the PE count for the workload) enables higher utilization at lower scale — a 16-PE RISC-V cluster at 80% utilization is more capital-efficient than an H100 at 25%.
  3. **The long tail of inference**: as the inference market fragments (1,000s of fine-tuned models, specialized agents, domain-specific inference), the GPU model (one expensive chip serving one large model) becomes economically suboptimal for the long tail. RISC-V's many-small-chips model fits the fragmented inference economy.
- [inference] The RISC-V inference thesis is the opposite of the NVIDIA training thesis: NVIDIA wins training because training is compute-intensive, concentrated (few large models), and CUDA-locked. RISC-V wins the inference long tail because inference is fragmented (many small models), price-sensitive, and the CUDA moat is weaker.

## Open Questions

- OPEN: Will the token-based pricing model survive GPU commoditization? If inference hardware becomes a commodity (multiple vendors, open interfaces), token pricing may compress toward GPU-hour pricing as competition erodes the spread.
- OPEN: Can neoclouds consolidate into a viable second tier below hyperscalers, or will the hyperscalers' structural advantages (power, scale, custom silicon) eventually absorb the entire market?
- OPEN: Is the capital-light GPU marketplace model defensible? Network effects (more supply → better routing → more demand → more supply) provide a moat, but hyperscalers can replicate the routing layer with their existing infrastructure.
- VERIFY: Baseten $600M ARR, Together AI $1B+ ARR, and Modal $3B ARR figures are from industry reports and may include non-inference revenue or be based on annualized run rates rather than GAAP revenue.
- VERIFY: The 13% industry-average GPU utilization figure is from a single Wesco analysis of K8s clusters; production utilization for dedicated inference clusters is likely higher but undisclosed.
