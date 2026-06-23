#!/usr/bin/env python3
"""Build a small graph/search index from Markdown concepts and JSONL edges.

This script intentionally uses only the Python standard library. Frontmatter is
kept flat so agents can edit it safely and the parser stays transparent.
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CONCEPTS_DIR = ROOT / "concepts"
EDGES_FILE = ROOT / "graph" / "edges.jsonl"
OUT_FILE = ROOT / "graph" / "concept-index.json"
SOURCE_REGISTRY_FILE = ROOT / "sources" / "source-registry.yaml"

FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
WIKILINK_RE = re.compile(r"\[\[([A-Za-z0-9_.:-]+)(?:\|([^\]]+))?\]\]")
SOURCE_REF_RE = re.compile(r"\[src:([A-Za-z0-9_.:-]+)\]")
SOURCE_ID_RE = re.compile(r"^\s*-\s+id:\s*([A-Za-z0-9_.:-]+)\s*$", re.MULTILINE)


def parse_scalar(value: str) -> Any:
    value = value.strip()
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [item.strip().strip("\"'") for item in inner.split(",")]
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False
    return value.strip("\"'")


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}, text

    metadata: dict[str, Any] = {}
    for raw_line in match.group(1).splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        metadata[key.strip()] = parse_scalar(value)

    body = text[match.end() :]
    return metadata, body


def read_concepts() -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    nodes: list[dict[str, Any]] = []
    mention_edges: list[dict[str, Any]] = []
    errors: list[str] = []
    seen_ids: set[str] = set()

    for path in sorted(CONCEPTS_DIR.rglob("*.md")):
        text = path.read_text(encoding="utf-8")
        metadata, body = parse_frontmatter(text)
        concept_id = metadata.get("id")
        title = metadata.get("title") or path.stem.replace("-", " ").title()

        if not concept_id:
            errors.append(f"{path.relative_to(ROOT)} is missing frontmatter id")
            continue
        if concept_id in seen_ids:
            errors.append(f"duplicate concept id: {concept_id}")
            continue
        seen_ids.add(concept_id)

        rel_path = path.relative_to(ROOT).as_posix()
        wikilinks = []
        source_refs = sorted(set(SOURCE_REF_RE.findall(body)))
        for match in WIKILINK_RE.finditer(body):
            target = match.group(1)
            label = match.group(2) or target
            wikilinks.append({"target": target, "label": label})
            mention_edges.append(
                {
                    "source": concept_id,
                    "target": target,
                    "type": "mentions",
                    "confidence": "extracted",
                    "notes": f"Extracted from wikilink label: {label}",
                }
            )

        nodes.append(
            {
                "id": concept_id,
                "title": title,
                "status": metadata.get("status", "seed"),
                "layer": metadata.get("layer", "unknown"),
                "layer_path": metadata.get("layer_path", metadata.get("layer", "unknown")),
                "parent": metadata.get("parent", ""),
                "secondary_layers": metadata.get("secondary_layers", []),
                "granularity": metadata.get("granularity", "concept"),
                "concept_type": metadata.get("concept_type", ""),
                "scale_scope": metadata.get("scale_scope", []),
                "reasoning_roles": metadata.get("reasoning_roles", []),
                "tags": metadata.get("tags", []),
                "aliases": metadata.get("aliases", []),
                "sources": metadata.get("sources", []),
                "source_refs": source_refs,
                "path": rel_path,
                "href": rel_path,
                "wikilinks": wikilinks,
            }
        )

    return nodes, mention_edges, errors


def read_source_ids() -> tuple[set[str], list[str]]:
    if not SOURCE_REGISTRY_FILE.exists():
        return set(), [f"{SOURCE_REGISTRY_FILE.relative_to(ROOT)} not found"]

    text = SOURCE_REGISTRY_FILE.read_text(encoding="utf-8")
    source_ids = set(SOURCE_ID_RE.findall(text))
    if not source_ids:
        return source_ids, [f"{SOURCE_REGISTRY_FILE.relative_to(ROOT)} has no source ids"]
    return source_ids, []


def read_typed_edges() -> tuple[list[dict[str, Any]], list[str]]:
    edges: list[dict[str, Any]] = []
    errors: list[str] = []
    if not EDGES_FILE.exists():
        return edges, errors

    for line_number, raw_line in enumerate(EDGES_FILE.read_text(encoding="utf-8").splitlines(), 1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        try:
            edge = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"{EDGES_FILE.relative_to(ROOT)}:{line_number}: invalid JSON: {exc}")
            continue
        for key in ("source", "target", "type"):
            if key not in edge:
                errors.append(f"{EDGES_FILE.relative_to(ROOT)}:{line_number}: missing {key}")
        edges.append(edge)

    return edges, errors


def validate_edges(nodes: list[dict[str, Any]], edges: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    ids = {node["id"] for node in nodes}
    for edge in edges:
        source = edge.get("source")
        target = edge.get("target")
        edge_type = edge.get("type")
        if source not in ids:
            errors.append(f"edge source not found: {source} -> {target} ({edge_type})")
        if target not in ids:
            errors.append(f"edge target not found: {source} -> {target} ({edge_type})")
    return errors


def validate_hierarchy(nodes: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    ids = {node["id"] for node in nodes}
    for node in nodes:
        parent = node.get("parent")
        if not parent:
            continue
        if parent == node["id"]:
            errors.append(f"node cannot be its own parent: {node['id']}")
        elif parent not in ids:
            errors.append(f"parent id not found: {node['id']} -> {parent}")
    return errors


def validate_sources(nodes: list[dict[str, Any]], source_ids: set[str]) -> list[str]:
    errors: list[str] = []
    for node in nodes:
        page_sources = set(node.get("sources") or [])
        cited_sources = set(node.get("source_refs") or [])
        for source_id in sorted(page_sources | cited_sources):
            if source_id not in source_ids:
                errors.append(f"source id not found: {node['id']} cites {source_id}")
        for source_id in sorted(cited_sources - page_sources):
            errors.append(f"source ref not listed in frontmatter: {node['id']} cites {source_id}")
    return errors


def group_nodes(nodes: list[dict[str, Any]], field: str) -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = {}
    for node in nodes:
        values = node.get(field)
        if not isinstance(values, list):
            values = [values] if values else []
        for value in values:
            grouped.setdefault(value, []).append(node["id"])
    return {key: sorted(value) for key, value in sorted(grouped.items())}


def main() -> int:
    nodes, mention_edges, concept_errors = read_concepts()
    source_ids, source_registry_errors = read_source_ids()
    typed_edges, edge_errors = read_typed_edges()
    all_edges = typed_edges + mention_edges
    validation_errors = validate_edges(nodes, all_edges)
    hierarchy_errors = validate_hierarchy(nodes)
    source_errors = validate_sources(nodes, source_ids)

    index = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "root": ROOT.name,
        "node_count": len(nodes),
        "edge_count": len(all_edges),
        "source_count": len(source_ids),
        "indexes": {
            "by_concept_type": group_nodes(nodes, "concept_type"),
            "by_granularity": group_nodes(nodes, "granularity"),
            "by_layer": group_nodes(nodes, "layer"),
            "by_reasoning_role": group_nodes(nodes, "reasoning_roles"),
            "by_scale_scope": group_nodes(nodes, "scale_scope"),
        },
        "nodes": nodes,
        "edges": all_edges,
        "errors": concept_errors
        + source_registry_errors
        + edge_errors
        + validation_errors
        + hierarchy_errors
        + source_errors,
    }

    OUT_FILE.write_text(json.dumps(index, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if index["errors"]:
        for error in index["errors"]:
            print(f"ERROR: {error}", file=sys.stderr)
        print(f"Wrote {OUT_FILE.relative_to(ROOT)} with errors", file=sys.stderr)
        return 1

    print(
        f"Wrote {OUT_FILE.relative_to(ROOT)} with {index['node_count']} nodes and {index['edge_count']} edges"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
