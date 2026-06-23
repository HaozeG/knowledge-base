#!/usr/bin/env python3
"""Validate concept metadata against the central ontology.

This is intentionally stricter than build_index.py. The indexer answers
"can a graph be generated?", while this validator answers "does this concept
follow the ontology?"
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import build_index


ROOT = Path(__file__).resolve().parents[1]

ALLOWED_LAYERS = {
    "00-orientation",
    "10-physical-limits-materials",
    "20-manufacturing-process-integration",
    "30-circuit-ip-primitives",
    "40-compute-substrate",
    "50-memory-data-movement",
    "60-interconnect-power-thermal",
    "70-execution-architecture",
    "80-programming-interface-dsl",
    "90-compiler-lowering-stack",
    "100-runtime-execution-system",
    "110-workload-mapping",
    "120-scale-up-system",
    "130-scale-out-distributed-system",
    "140-performance-cost-utilization-model",
    "150-supply-chain-business",
    "160-market-narrative",
}

ALLOWED_GRANULARITIES = {
    "map",
    "overview",
    "concept",
    "mechanism",
    "model",
    "metric",
    "case-study",
}

ALLOWED_CONCEPT_TYPES = {
    "physical_limit",
    "manufacturing_method",
    "component",
    "architecture_pattern",
    "memory_pattern",
    "interconnect_pattern",
    "execution_model",
    "programming_interface",
    "dsl",
    "intermediate_representation",
    "compiler_stack",
    "runtime_mechanism",
    "workload_pattern",
    "kernel_algorithm",
    "scaling_strategy",
    "performance_model",
    "metric",
    "business_constraint",
    "case_study",
    "market_narrative",
}

ALLOWED_SCALE_SCOPES = {
    "unit",
    "tile",
    "die",
    "package",
    "node",
    "rack",
    "cluster",
    "datacenter",
    "ecosystem",
}

ALLOWED_REASONING_ROLES = {
    "constraint",
    "enabler",
    "bottleneck",
    "bottleneck_mitigation",
    "abstraction",
    "mapping",
    "synchronization",
    "locality_strategy",
    "scale_up_strategy",
    "scale_out_strategy",
    "indicator",
    "claim_to_verify",
}


def as_list(value: Any) -> list[str]:
    if value is None or value == "":
        return []
    if isinstance(value, list):
        return value
    return [str(value)]


def validate_membership(
    concept_id: str,
    field: str,
    values: list[str],
    allowed: set[str],
    errors: list[str],
    *,
    required: bool = True,
) -> None:
    if not values:
        if required:
            errors.append(f"{concept_id}: {field} must not be empty")
        return
    for value in values:
        if value not in allowed:
            errors.append(f"{concept_id}: unknown {field} value: {value}")


def validate_node(node: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    concept_id = node["id"]
    layer = node.get("layer", "")
    layer_path = node.get("layer_path", "")
    path = node.get("path", "")

    validate_membership(concept_id, "layer", [layer], ALLOWED_LAYERS, errors)
    validate_membership(
        concept_id,
        "secondary_layers",
        [value for value in as_list(node.get("secondary_layers")) if value],
        ALLOWED_LAYERS,
        errors,
        required=False,
    )
    validate_membership(
        concept_id, "granularity", [node.get("granularity", "")], ALLOWED_GRANULARITIES, errors
    )
    validate_membership(
        concept_id, "concept_type", [node.get("concept_type", "")], ALLOWED_CONCEPT_TYPES, errors
    )
    validate_membership(
        concept_id, "scale_scope", as_list(node.get("scale_scope")), ALLOWED_SCALE_SCOPES, errors
    )
    validate_membership(
        concept_id,
        "reasoning_roles",
        as_list(node.get("reasoning_roles")),
        ALLOWED_REASONING_ROLES,
        errors,
    )

    if layer and layer_path and not layer_path.startswith(layer):
        errors.append(f"{concept_id}: layer_path must start with layer: {layer_path}")
    if layer and path and not path.startswith(f"concepts/{layer}/"):
        errors.append(f"{concept_id}: file path should live under concepts/{layer}/, got {path}")

    return errors


def main() -> int:
    nodes, mention_edges, concept_errors = build_index.read_concepts()
    source_ids, source_registry_errors = build_index.read_source_ids()
    typed_edges, edge_errors = build_index.read_typed_edges()
    all_edges = typed_edges + mention_edges

    errors: list[str] = []
    errors.extend(concept_errors)
    errors.extend(source_registry_errors)
    errors.extend(edge_errors)
    errors.extend(build_index.validate_edges(nodes, all_edges))
    errors.extend(build_index.validate_hierarchy(nodes))
    errors.extend(build_index.validate_sources(nodes, source_ids))
    for node in nodes:
        errors.extend(validate_node(node))

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print(f"Ontology validation passed for {len(nodes)} concepts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
