---
id: chip.circuit.analog-mixed-signal-sensor-ip
title: Analog and Mixed-Signal Sensor IP for AI Accelerator Health Monitoring
status: draft
layer: 30-circuit-ip-primitives
layer_path: 30-circuit-ip-primitives/analog/sensor-health-monitoring
parent: hw.riscv.vector-extension
secondary_layers: [10-physical-limits-materials, 60-interconnect-power-thermal]
granularity: concept
concept_type: component
scale_scope: [unit, die]
reasoning_roles: [enabler, constraint]
tags: [analog-ip, temperature-sensor, voltage-monitor, pvt-sensor, health-monitoring]
aliases: [analog sensor IP, PVT sensor, temperature monitor, die health monitoring, process monitor]
sources: [analog-bits-pvt-sensor-tsmc-2025]
---

# Analog and Mixed-Signal Sensor IP for AI Accelerator Health Monitoring

## Overview

AI accelerators operating at 1,000W+ require continuous monitoring of temperature, voltage, and process variation across the die to prevent thermal runaway, detect aging degradation, and enable dynamic voltage/frequency scaling. Analog/mixed-signal sensor IP — temperature sensors, voltage droop detectors, and PVT (process-voltage-temperature) monitors — provides the telemetry that the power management and reliability systems depend on. These sensors occupy <0.1% of die area but are essential for safe operation at advanced nodes.

- [supported][src:analog-bits-pvt-sensor-tsmc-2025] Analog Bits' PVT sensor portfolio on TSMC N3P/N2P provides temperature sensing to ±1°C accuracy, voltage droop detection at <10 mV resolution with <1 ns response time, and process corner identification (SS/TT/FF) from on-die ring oscillator frequency. Multiple sensors are distributed across the die (typically one per 10–20 mm²) to capture spatial thermal gradients and localized IR drop.
- [inference] The sensor telemetry enables closed-loop power management: temperature sensors trigger throttling when junction temperature exceeds 95°C; droop detectors trigger voltage margining when a compute spike causes >50 mV supply droop; PVT monitors enable per-die voltage optimization — each chip runs at the minimum V_dd that meets timing for its specific process corner, saving 5–15% power vs. worst-case corner voltage.

## Sensor Architecture

- [inference] Three primary sensor types integrated into AI accelerator dies: (1) BJT-based temperature sensors measuring V_BE change (~2 mV/°C) with ±1°C accuracy after factory calibration; (2) ring oscillator droop detectors — supply voltage change shifts oscillator frequency proportionally, detected within 1–2 ns by comparing against a reference clock; (3) process monitors — ring oscillator frequency distributions across the die identify slow/fast process corners and within-die variation for adaptive body biasing.
- [inference] Sensor placement is a physical design optimization: placing sensors near hotspots (Tensor Core arrays, HBM PHYs) provides the most actionable thermal data but creates routing congestion; placing sensors uniformly provides spatial coverage but may miss localized hotspots. The typical strategy: one sensor per 10–20 mm², with additional sensors near known high-power-density blocks.

## Open Questions

- OPEN: Can on-die sensors achieve sufficient accuracy (±1°C, ±5mV) without per-die factory calibration (which adds test cost), or is statistical post-silicon calibration across wafer-level variation sufficient?
- OPEN: As accelerators move toward chiplet architectures, does each chiplet require its own sensor suite, or can inter-chiplet thermal coupling be modeled accurately enough that sensors on the base die suffice for all chiplets?
- VERIFY: The sub-nanosecond droop detection claim is vendor-provided — actual response time depends on sensor placement and signal routing delay to the power management controller.

## See Also

- [[hw.riscv.vector-extension]] — RISC-V vector cores whose health these sensors monitor.
- [[system.power.ai-accelerator-power-delivery]] — PDN where droop detectors provide the feedback for closed-loop regulation.
- [[physics.materials.energy-limits-beyond-cmos]] — Physical limits that PVT sensors monitor and mitigate.
- [[hw.riscv.power-thermal-interconnect]] — Power/thermal interconnect where sensor telemetry drives management decisions.
- [[silicon.process.node-selection-fabrication-ai]] — Process node where sensor accuracy requirements tighten with smaller margins.
- [[chip.design.eda-and-ai-design-automation]] — EDA tools where sensor IP is integrated into the physical design flow.
