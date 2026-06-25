---
id: physics.materials.thermal-noise-nanoscale-devices
title: Thermal Noise and Stochastic Effects in Nanoscale Semiconductor Devices
status: draft
layer: 10-physical-limits-materials
layer_path: 10-physical-limits-materials/noise/thermal-noise-nanoscale
parent: stack.ai-accelerator-ontology
secondary_layers: [30-circuit-ip-primitives, 40-compute-substrate, 60-interconnect-power-thermal]
granularity: concept
concept_type: physical_limit
scale_scope: [unit, die]
reasoning_roles: [constraint, bottleneck]
tags: [thermal-noise, shot-noise, random-telegraph-noise, stochastic-computing, nanoscale]
aliases: [Johnson-Nyquist noise, shot noise, RTN, transistor noise, stochastic effects]
sources: [ieee-thermal-noise-nanoscale-2025]
---

# Thermal Noise and Stochastic Effects in Nanoscale Semiconductor Devices

## Overview

At nanoscale dimensions, electronic noise transitions from a second-order effect to a first-order design constraint. Thermal (Johnson-Nyquist) noise, shot noise, and random telegraph noise (RTN) set fundamental limits on signal integrity, analog circuit precision, and SRAM stability. For AI accelerators — which integrate billions of transistors operating at sub-1V with margins measured in millivolts — noise-induced errors in SRAM bitcells, analog compute-in-memory arrays, and high-speed I/O receivers directly limit achievable performance and yield.

- [supported][src:ieee-thermal-noise-nanoscale-2025] The three primary noise mechanisms at nanoscale: (1) thermal noise — voltage fluctuations from random thermal motion of charge carriers, power ∝ kT, dominant in resistive channels; (2) shot noise — current fluctuations from discrete electron arrival times, power ∝ qI, dominant in tunneling and Schottky barriers; (3) random telegraph noise (RTN) — discrete switching of current between two or more levels caused by single-charge trapping/detrapping at oxide interface defects, dominant in small-area devices (<100nm²) where a single trap can modulate 5–20% of drive current.
- [inference] The noise floor for analog compute-in-memory (CIM) accelerators is set by thermal + RTN noise: in a 6-bit ADC reading a CIM array output, thermal noise limits the effective number of bits (ENOB) to 4–5 bits at 1 GHz sampling rates — fundamentally constraining the precision of analog AI computation. Digital accelerators avoid this by operating at voltage swings large enough that noise-induced bit errors are negligible (BER < 10⁻¹⁵), but at a significant energy cost.

## Noise Mechanisms and AI Impact

### SRAM Bitcell Stability

- [inference] RTN is the dominant SRAM yield limiter at advanced nodes: a single trapped charge in the gate oxide of one transistor in a 6T SRAM cell can shift the cell's static noise margin (SNM) by 10–30 mV, sufficient to cause read upset or write failure. At 3nm and below, RTN-induced bitcell failures occur at a rate that requires ECC (error-correcting codes) even for L1 caches — historically, ECC was reserved for L2/L3 due to area overhead. The AI accelerator implication: SRAM capacity that was previously "free" (no ECC overhead) now requires 10–15% area overhead for single-error correction.

### Analog CIM Precision Limits

- [inference] Analog CIM accelerators (Mythic, Untether AI, TetraMem) perform matrix multiply by encoding weights as conductances in memory cells and summing currents on bitlines. Thermal noise current (I_noise = sqrt(4kT/R × BW)) adds directly to the summed current, creating an error term that is proportional to sqrt(bandwidth) and inversely proportional to sqrt(resistance). At 1 GHz inference throughput with 10KΩ cells, thermal noise limits the signal-to-noise ratio to ~30 dB (~5 ENOB) — acceptable for inference but insufficient for training where gradient accumulation requires >10 ENOB.

## Mitigation and Stochastic Computing

- [inference] Three mitigation strategies: (1) increase signal swing (raise V_dd) — effective but increases energy quadratically; (2) oversampling and averaging — each 4× increase in samples improves SNR by 3 dB (1/2 bit), trading throughput for precision; (3) stochastic computing — embrace noise by representing values as probabilities encoded in random bitstreams, converting noise from error source to computational resource. Stochastic computing is academically promising but has not achieved commercial adoption due to the extreme bitstream lengths required (>1,000 bits for 10-bit precision).

## Open Questions

- OPEN: Can stochastic computing techniques make analog CIM viable for training (which requires >8-bit precision), or is the noise floor an irreducible barrier that limits CIM to inference-only applications?
- OPEN: As transistor dimensions shrink below 2nm, does RTN become the dominant failure mechanism that makes SRAM scaling below a certain bitcell area economically non-viable regardless of lithography capability?
- VERIFY: The 5 ENOB limit for analog CIM at 1 GHz is based on simplified thermal noise models — real CIM arrays face additional noise sources (power supply noise, capacitive coupling, temperature gradients) that degrade ENOB further.

## See Also

- [[stack.ai-accelerator-ontology]] — Central ontology that physical noise constraints bound.
- [[physics.materials.energy-limits-beyond-cmos]] — Beyond-CMOS physics where noise limits motivate new device types.
- [[chip.circuit.sram-cim-ai-accelerators]] — SRAM and CIM circuits directly affected by thermal and RTN noise.
- [[silicon.process.node-selection-fabrication-ai]] — Process node selection where noise-limited yield determines economic viability.
- [[hw.compute.numerical-precision-ai]] — Numerical precision where analog noise sets the floor on achievable bits.
- [[physics.materials.interconnect-scaling-limits]] — Interconnect scaling where thermal noise in long wires affects signal integrity.
