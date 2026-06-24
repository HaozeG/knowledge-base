#!/usr/bin/env python3
"""Evaluate one staged exploration run without mutating repository state."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
INDEX_FILE = ROOT / "graph" / "concept-index.json"
LEDGER_FILE = ROOT / "system" / "run-ledger.jsonl"
THRESHOLD = 1.0

ALLOWED_PROMOTION_STATUS = {"seed", "draft"}
LOW_RISK_SOURCE_TIERS = {"A", "B"}
MID_RISK_SOURCE_TIERS = {"C"}
HIGH_RISK_SOURCE_TIERS = {"D"}
KNOWN_SOURCE_TIERS = LOW_RISK_SOURCE_TIERS | MID_RISK_SOURCE_TIERS | HIGH_RISK_SOURCE_TIERS
SAFE_CLAIM_LABELS = {"open", "supported", "inference", "speculative"}


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"{path} not found") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path} invalid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def load_index(path: Path = INDEX_FILE) -> dict[str, Any]:
    return load_json(path)


def load_manifest(run_dir: Path) -> dict[str, Any]:
    return load_json(run_dir / "manifest.json")


def parse_date(value: str) -> date:
    return datetime.fromisoformat(value[:10]).date()


def compute_staleness_multiplier(latest_date: str | None, today: str) -> float:
    if latest_date is None:
        return 1.5

    age_days = max((parse_date(today) - parse_date(latest_date)).days, 0)
    if age_days <= 14:
        return 1.0
    if age_days >= 180:
        return 1.5
    return round(1.0 + ((age_days - 14) / (180 - 14)) * 0.5, 4)


def latest_category_date(category: str, ledger_file: Path = LEDGER_FILE) -> str | None:
    if not category or not ledger_file.exists():
        return None

    latest: date | None = None
    artifact_prefix = f"concepts/{category}/"
    for line in ledger_file.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(entry, dict):
            continue
        artifacts = as_list(entry.get("artifacts"))
        if not any(isinstance(item, str) and item.startswith(artifact_prefix) for item in artifacts):
            continue
        timestamp = str(entry.get("timestamp") or "")
        if not timestamp:
            continue
        try:
            entry_date = parse_date(timestamp)
        except ValueError:
            continue
        if latest is None or entry_date > latest:
            latest = entry_date
    return latest.isoformat() if latest else None


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def index_nodes(index: dict[str, Any]) -> list[dict[str, Any]]:
    return [node for node in as_list(index.get("nodes")) if isinstance(node, dict)]


def index_by_id(nodes: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(node.get("id")): node for node in nodes if node.get("id")}


def direct_child_count(nodes: list[dict[str, Any]], parent_id: str) -> int:
    return sum(1 for node in nodes if node.get("parent") == parent_id)


def category_count(nodes: list[dict[str, Any]], category: str, target_parent: str) -> int:
    return sum(
        1
        for node in nodes
        if node.get("layer") == category and (not target_parent or node.get("id") != target_parent)
    )


def add_gate(
    codes: list[str],
    errors: list[str],
    code: str,
    message: str,
) -> None:
    codes.append(code)
    errors.append(message)


def hard_gate_results(manifest: dict[str, Any], index: dict[str, Any]) -> tuple[list[str], list[str]]:
    codes: list[str] = []
    errors: list[str] = []
    nodes = index_nodes(index)
    existing_ids = set(index_by_id(nodes))
    proposed_nodes = as_list(manifest.get("proposed_nodes"))
    proposed_edges = as_list(manifest.get("proposed_edges"))
    proposed_sources = as_list(manifest.get("proposed_sources"))
    target_category = str(manifest.get("target_category") or "")
    proposed_ids = {
        str(node.get("id"))
        for node in proposed_nodes
        if isinstance(node, dict) and node.get("id")
    }
    declared_source_ids = {
        str(source.get("id"))
        for source in proposed_sources
        if isinstance(source, dict) and source.get("id")
    }

    if not target_category:
        add_gate(codes, errors, "TARGET_CATEGORY_EMPTY", "target_category must not be empty")

    for node in proposed_nodes:
        if not isinstance(node, dict):
            add_gate(codes, errors, "PROPOSED_NODE_INVALID", "proposed_nodes entries must be objects")
            continue

        node_id = str(node.get("id") or "")
        status = str(node.get("status") or "")
        sources = [str(item) for item in as_list(node.get("sources")) if item]
        claim_labels = {str(item) for item in as_list(node.get("claim_labels")) if item}

        if "layer" in node and str(node.get("layer") or "") != target_category:
            add_gate(
                codes,
                errors,
                "NODE_LAYER_MISMATCH",
                f"proposed node {node_id or '<missing>'} layer must match target_category",
            )

        if not node_id:
            add_gate(codes, errors, "PROPOSED_NODE_MISSING_ID", "proposed node missing id")
        elif node_id in existing_ids:
            add_gate(codes, errors, "NODE_ALREADY_EXISTS", f"proposed node already exists: {node_id}")

        if status not in ALLOWED_PROMOTION_STATUS:
            add_gate(
                codes,
                errors,
                "STATUS_FORBIDDEN",
                f"proposed node {node_id or '<missing>'} status {status or '<missing>'} is forbidden",
            )

        if not sources and not (claim_labels & {"open", "speculative"}):
            add_gate(
                codes,
                errors,
                "NODE_NEEDS_SOURCE_OR_UNCERTAINTY",
                f"proposed node {node_id or '<missing>'} needs sources or open/speculative claim labels",
            )

        undeclared_sources = sorted(source for source in sources if source not in declared_source_ids)
        if undeclared_sources:
            add_gate(
                codes,
                errors,
                "SOURCE_NOT_DECLARED",
                f"proposed node {node_id or '<missing>'} cites undeclared sources: {undeclared_sources}",
            )

        unknown_labels = sorted(claim_labels - SAFE_CLAIM_LABELS)
        if unknown_labels:
            add_gate(
                codes,
                errors,
                "CLAIM_LABEL_UNKNOWN",
                f"proposed node {node_id or '<missing>'} has unknown claim labels: {unknown_labels}",
            )

    for source in proposed_sources:
        if not isinstance(source, dict):
            add_gate(codes, errors, "PROPOSED_SOURCE_INVALID", "proposed_sources entries must be objects")
            continue

        source_id = str(source.get("id") or "")
        tier = str(source.get("tier") or "")
        if not source_id:
            add_gate(codes, errors, "PROPOSED_SOURCE_MISSING_ID", "proposed source missing id")
        if tier and tier not in KNOWN_SOURCE_TIERS:
            add_gate(codes, errors, "PROPOSED_SOURCE_INVALID", f"proposed source {source_id or '<missing>'} has unknown tier {tier}")
        if tier in HIGH_RISK_SOURCE_TIERS:
            add_gate(codes, errors, "SOURCE_TIER_D", f"proposed source {source_id or '<missing>'} uses tier D")

    valid_ids = existing_ids | proposed_ids
    for edge in proposed_edges:
        if not isinstance(edge, dict):
            add_gate(codes, errors, "PROPOSED_EDGE_INVALID", "proposed_edges entries must be objects")
            continue

        source = str(edge.get("source") or "")
        target = str(edge.get("target") or "")
        if not source or not target:
            add_gate(codes, errors, "PROPOSED_EDGE_INVALID", "proposed edge must include source and target")
            continue
        if source not in valid_ids:
            add_gate(codes, errors, "EDGE_SOURCE_NOT_FOUND", f"proposed edge source not found: {source}")
        if target not in valid_ids:
            add_gate(codes, errors, "EDGE_TARGET_NOT_FOUND", f"proposed edge target not found: {target}")

    return codes, errors


def quality_risk_penalty(manifest: dict[str, Any]) -> float:
    penalty = 0.0
    for source in as_list(manifest.get("proposed_sources")):
        if not isinstance(source, dict):
            penalty += 0.2
            continue
        tier = str(source.get("tier") or "")
        if tier in MID_RISK_SOURCE_TIERS:
            penalty += 0.15
        elif tier in HIGH_RISK_SOURCE_TIERS:
            penalty += 1.0
        elif tier not in LOW_RISK_SOURCE_TIERS:
            penalty += 0.25

    description = str(manifest.get("description") or "").lower()
    broad_markers = ["everything", "all topics", "broad survey", "market winner", "stock"]
    if any(marker in description for marker in broad_markers):
        penalty += 0.25
    return round(penalty, 4)


def creativity_score(manifest: dict[str, Any], index: dict[str, Any]) -> float:
    nodes = index_nodes(index)
    node_count = max(int(index.get("node_count") or len(nodes) or 1), 1)
    proposed_edges = [edge for edge in as_list(manifest.get("proposed_edges")) if isinstance(edge, dict)]
    proposed_nodes = [node for node in as_list(manifest.get("proposed_nodes")) if isinstance(node, dict)]
    proposed_ids = {str(node.get("id")) for node in proposed_nodes if node.get("id")}
    target_parent = str(manifest.get("target_parent") or "")

    useful_edges = 0
    for edge in proposed_edges:
        source = str(edge.get("source") or "")
        target = str(edge.get("target") or "")
        if source in proposed_ids or target in proposed_ids:
            useful_edges += 1

    edge_component = min(0.8, useful_edges / node_count * 8.0)
    hot_parent_bonus = 0.0
    if target_parent and proposed_nodes and direct_child_count(nodes, target_parent) >= 2:
        hot_parent_bonus = 0.25
    return round(edge_component + hot_parent_bonus, 4)


def coverage_gap_score(manifest: dict[str, Any], index: dict[str, Any]) -> float:
    nodes = index_nodes(index)
    target_category = str(manifest.get("target_category") or "")
    target_parent = str(manifest.get("target_parent") or "")
    proposed_nodes = [node for node in as_list(manifest.get("proposed_nodes")) if isinstance(node, dict)]
    if not target_category or not proposed_nodes:
        return 0.0

    existing_count = category_count(nodes, target_category, target_parent)
    sparsity = max(0.0, 1.0 - min(existing_count, 10) / 10.0)
    contribution = min(len(proposed_nodes), 3) / 3.0
    return round(sparsity * contribution, 4)


def compute_score(creativity: float, coverage_gap: float, multiplier: float, penalty: float) -> float:
    score = (Decimal(str(creativity)) + Decimal(str(coverage_gap))) * Decimal(str(multiplier))
    score -= Decimal(str(penalty))
    return float(score.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP).normalize())


def evaluate(manifest: dict[str, Any], index: dict[str, Any], ledger_file: Path, today: str) -> dict[str, Any]:
    hard_gate_codes, hard_gate_errors = hard_gate_results(manifest, index)
    latest_date = latest_category_date(str(manifest.get("target_category") or ""), ledger_file)
    multiplier = compute_staleness_multiplier(latest_date, today)
    creativity = creativity_score(manifest, index)
    coverage_gap = coverage_gap_score(manifest, index)
    penalty = quality_risk_penalty(manifest)
    score = compute_score(creativity, coverage_gap, multiplier, penalty)

    if hard_gate_codes:
        decision = "hard_gate_fail"
    elif score >= THRESHOLD:
        decision = "accept"
    else:
        decision = "reject"

    return {
        "run_id": manifest.get("run_id", ""),
        "decision": decision,
        "score": score,
        "threshold": THRESHOLD,
        "creativity_score": creativity,
        "coverage_gap_score": coverage_gap,
        "category_staleness_multiplier": multiplier,
        "category_latest_update": latest_date,
        "quality_risk_penalty": penalty,
        "hard_gate_errors": hard_gate_errors,
        "hard_gate_codes": hard_gate_codes,
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir", type=Path, help="Directory containing manifest.json")
    parser.add_argument("--index", type=Path, default=INDEX_FILE, help="Path to concept-index.json")
    parser.add_argument("--ledger", type=Path, default=LEDGER_FILE, help="Path to run-ledger.jsonl")
    parser.add_argument("--today", default=date.today().isoformat(), help="YYYY-MM-DD for deterministic tests")
    parser.add_argument("--allow-reject", action="store_true", help="Exit 0 for below-threshold rejections")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    try:
        index = load_index(args.index)
        manifest = load_manifest(args.run_dir)
        payload = evaluate(manifest, index, args.ledger, args.today)
    except (OSError, ValueError) as exc:
        payload = {
            "run_id": "",
            "decision": "hard_gate_fail",
            "score": 0.0,
            "threshold": THRESHOLD,
            "creativity_score": 0.0,
            "coverage_gap_score": 0.0,
            "category_staleness_multiplier": 1.0,
            "category_latest_update": None,
            "quality_risk_penalty": 0.0,
            "hard_gate_errors": [str(exc)],
            "hard_gate_codes": ["INVALID_INPUT"],
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 1

    print(json.dumps(payload, indent=2, sort_keys=True))
    if payload["decision"] == "hard_gate_fail":
        return 1
    if payload["decision"] == "reject" and not args.allow_reject:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
