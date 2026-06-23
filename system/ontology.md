# Ontology

The ontology gives agents and humans a shared map for placing concepts.

## Ontology Rule

Use a pattern-first ontology.

Do not make product families the top-level structure:

```text
GPU / TPU / Cerebras / Trainium / Gaudi
```

Instead, place concepts by the stable mechanism they explain:

```text
compute substrate / memory movement / interconnect / execution / software control / scaling / business logic
```

Products and companies are case studies that instantiate patterns.

## Concept Coordinates

Each concept uses these placement fields:

| Field | Purpose | Example |
| --- | --- | --- |
| `layer` | Compact filter bucket | `50-memory-system` |
| `layer_path` | Visual tree placement | `50-memory-system/gpu/on-chip-and-package-memory` |
| `parent` | Collapsible concept hierarchy | `hw.gpu.overview` |
| `secondary_layers` | Other layers touched by the concept | `[40-compute-substrate, 100-runtime-execution]` |
| `concept_type` | What kind of thing the concept is | `mechanism` |
| `scale_scope` | Physical or operational scale where the concept matters | `[tile, die]` |
| `reasoning_roles` | How the concept helps explain systems or markets | `[bottleneck, enabler]` |

Use `layer_path` for sidebars, tree maps, and graph clustering. Use explicit graph edges for typed causal relationships.

## Central Stack

| Layer | ID Prefix Examples | Scope |
| --- | --- | --- |
| `00-orientation` | `stack.*` | Maps, entry points, learning paths |
| `10-physical-limits-materials` | `physics.*`, `silicon.materials.*` | Energy, heat, wire delay, defects, materials, electron transport |
| `20-manufacturing-process-integration` | `silicon.process.*`, `chip.integration.*` | Process nodes, lithography, yield, wafer-scale integration, packaging method |
| `30-circuit-ip-primitives` | `chip.circuit.*`, `chip.ip.*` | SRAM bitcells, SerDes, PHY, standard cells, primitive blocks |
| `40-compute-substrate` | `hw.compute.*`, `chip.accelerator.*` | Matrix units, Tensor Cores, systolic arrays, PEs, vector lanes |
| `50-memory-data-movement` | `chip.memory.*`, `hw.memory.*` | HBM, SRAM, cache, scratchpad, DMA/TMA, locality, bandwidth |
| `60-interconnect-power-thermal` | `chip.interconnect.*`, `system.power.*` | NoC, NVLink, wafer fabric, power delivery, cooling, thermal density |
| `70-execution-architecture` | `hw.gpu.*`, `hw.dataflow.*` | SIMT, dataflow, spatial execution, scheduling machinery |
| `80-programming-interface-dsl` | `software.dsl.*`, `programmer.api.*` | CUDA C++, Triton language, JAX, PyTorch graph, kernel DSLs |
| `90-compiler-lowering-stack` | `software.compiler.*`, `software.ir.*` | XLA, MLIR, LLVM, PTX, HLO, tiling, fusion, layout assignment |
| `100-runtime-execution-system` | `software.runtime.*`, `system.runtime.*` | Launch, streams, graph execution, allocators, collectives runtime, orchestration |
| `110-workload-mapping` | `workload.ai.*` | GEMM, attention, MoE, inference serving, parallelism strategy, kernel algorithms |
| `120-scale-up-system` | `system.scale_up.*` | Bigger local domains: chiplets, wafer-scale, NVLink domains, rack-scale shared accelerator domains |
| `130-scale-out-distributed-system` | `system.scale_out.*` | Multi-node clusters, pods, collectives, network topology, distributed training |
| `140-performance-cost-utilization-model` | `model.performance.*`, `model.cost.*` | Roofline, occupancy, TCO, utilization, bottleneck models |
| `150-supply-chain-business` | `industry.*` | Capacity, vendors, margins, ecosystem lock-in, capex, customer concentration |
| `160-market-narrative` | `market.*` | Investor narratives, hype cycles, valuation logic, risk framing |

## Scale Scope

Use `scale_scope` to avoid confusing local and distributed versions of the same word.

| Scope | Meaning |
| --- | --- |
| `unit` | One lane, PE, Tensor Core, core, or primitive execution unit |
| `tile` | SM, compute tile, PE group, matrix unit, local scheduling group |
| `die` | One chip or reticle-scale die |
| `package` | Multi-die package, HBM stack domain, interposer, wafer-scale processor |
| `node` | One server, appliance, or accelerator box |
| `rack` | Rack-scale system or tightly coupled rack fabric |
| `cluster` | Multi-rack or pod-scale training/inference system |
| `datacenter` | Facility-level power, cooling, networking, and operations |
| `ecosystem` | Supply chain, software ecosystem, developer adoption, market structure |

## Scale-Up vs Scale-Out

Scale-up and scale-out are first-class concepts.

| Strategy | Meaning | Examples |
| --- | --- | --- |
| Scale-up | Make one local domain larger, tighter, or faster | HBM integration, chiplets, wafer-scale engine, NVLink domain |
| Scale-out | Connect many domains through a network | GPU clusters, TPU pods, distributed training, multi-rack inference |

Some systems blur the boundary. A Cerebras wafer-scale engine is mostly a scale-up strategy; an NVIDIA rack-scale system may behave like a local domain for some workloads while still living inside a larger scale-out cluster.

## Software Control Separation

Keep DSL, compiler, runtime, and workload mapping separate.

| Layer | Question | Examples |
| --- | --- | --- |
| `80-programming-interface-dsl` | What can the user or framework express? | CUDA C++, Triton language, PyTorch graph, JAX |
| `90-compiler-lowering-stack` | How does intent become device-specific executable work? | XLA, MLIR, LLVM, PTX, fusion, tiling |
| `100-runtime-execution-system` | What happens dynamically at execution time? | CUDA streams, memory allocator, graph executor, NCCL runtime |
| `110-workload-mapping` | How does the AI workload fit the machine? | FlashAttention, GEMM tiling, tensor parallelism, MoE routing |

If a project spans several layers, split the concept pages. For example:

```text
software.dsl.triton-language
software.compiler.triton-lowering
software.runtime.triton-autotune-cache
```

## Granularity

| Granularity | Meaning |
| --- | --- |
| `map` | A navigation or learning map |
| `overview` | A broad concept that organizes children |
| `concept` | A reusable idea with stable identity |
| `mechanism` | A concrete hardware/software mechanism |
| `model` | A quantitative or qualitative reasoning model |
| `metric` | A measured quantity or benchmark |
| `case-study` | A bounded example, product, article, or event |

## Concept Types

| Type | Meaning |
| --- | --- |
| `physical_limit` | A basic physical constraint |
| `manufacturing_method` | A fabrication, packaging, or integration method |
| `component` | A concrete hardware component |
| `architecture_pattern` | A reusable architectural pattern |
| `memory_pattern` | A memory hierarchy or data movement pattern |
| `interconnect_pattern` | A local or distributed communication pattern |
| `execution_model` | How work is scheduled or executed |
| `programming_interface` | An API, language, or user-facing abstraction |
| `dsl` | A domain-specific language |
| `intermediate_representation` | Compiler representation or IR |
| `compiler_stack` | Compiler system or lowering path |
| `runtime_mechanism` | Dynamic execution, scheduling, allocation, or communication mechanism |
| `workload_pattern` | Workload shape or algorithmic pattern |
| `kernel_algorithm` | A specific kernel algorithm or implementation strategy |
| `scaling_strategy` | Scale-up or scale-out strategy |
| `performance_model` | Model for bottlenecks, throughput, latency, cost, or utilization |
| `metric` | Measured quantity |
| `business_constraint` | Supply, demand, margin, customer, or ecosystem constraint |
| `case_study` | Product, system, company, or event used to instantiate patterns |
| `market_narrative` | Market explanation or claim to evaluate |

## Reasoning Roles

| Role | Meaning |
| --- | --- |
| `constraint` | Limits what is possible |
| `enabler` | Makes a capability practical |
| `bottleneck` | Controls throughput, adoption, cost, or supply |
| `bottleneck_mitigation` | Reduces a known bottleneck |
| `abstraction` | Hides lower-level detail |
| `mapping` | Maps workloads to hardware or systems |
| `synchronization` | Coordinates work across units |
| `locality_strategy` | Reduces data movement through placement or reuse |
| `scale_up_strategy` | Expands a local compute domain |
| `scale_out_strategy` | Expands a distributed compute system |
| `indicator` | Useful signal for business or market reasoning |
| `claim_to_verify` | A technical or market assertion requiring evidence |

## Prefix Guidance

The concept ID prefix does not need to mirror the layer exactly. For example, `hw.gpu.tensor-memory-accelerator` can sit in `50-memory-system` because its main role is data movement, while still keeping the `hw.gpu.*` namespace.

## Edge Types

Use typed edges when a relationship should appear in a graph UI.

| Type | Meaning |
| --- | --- |
| `decomposes_into` | A concept breaks into smaller concepts |
| `depends_on` | A concept requires another concept to make sense |
| `constrained_by` | A physical, economic, or software constraint limits a concept |
| `enables` | One concept creates a capability used by another |
| `competes_with` | Concepts are alternative approaches |
| `measured_by` | A metric or model evaluates a concept |
| `implemented_by` | A software or hardware mechanism realizes a concept |
| `explains_market_logic_for` | A technical concept explains an industry or market narrative |
| `mentions` | A weak link extracted from Markdown wikilinks |

## Claim Status

| Status | Meaning |
| --- | --- |
| `verified` | Backed by strong source evidence |
| `supported` | Backed by credible but incomplete evidence |
| `inference` | Reasoned from verified or supported concepts |
| `speculative` | Useful hypothesis, not accepted as fact |
| `open` | Needs investigation |

## First-Principle Axes

Prefer explanations that reduce a concept to stable constraints:

- Energy movement: moving data usually costs energy and time.
- Distance: physical distance affects latency, bandwidth, power, and clocking.
- Parallelism: throughput comes from doing many independent operations at once.
- Locality: reuse near compute reduces pressure on distant memory.
- Precision: numerical format affects bandwidth, storage, hardware area, and accuracy.
- Yield: larger and more complex manufacturing surfaces increase defect exposure.
- Utilization: peak capability matters only when software can keep hardware busy.
