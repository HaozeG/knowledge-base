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
COMBINED_THRESHOLD = 0.7
EVALUATOR_SCHEMA_VERSION = 2

ALLOWED_PROMOTION_STATUS = {"seed", "draft"}
LOW_RISK_SOURCE_TIERS = {"A", "B"}
MID_RISK_SOURCE_TIERS = {"C"}
HIGH_RISK_SOURCE_TIERS = {"D"}
KNOWN_SOURCE_TIERS = LOW_RISK_SOURCE_TIERS | MID_RISK_SOURCE_TIERS | HIGH_RISK_SOURCE_TIERS
SAFE_CLAIM_LABELS = {"open", "supported", "inference", "speculative"}
ALLOWED_EDGE_TYPES = {
    "decomposes_into",
    "depends_on",
    "constrained_by",
    "enables",
    "competes_with",
    "measured_by",
    "implemented_by",
    "explains_market_logic_for",
    "mentions",
}
KNOWN_LAYERS = [
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
]


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


def load_ledger_entries(ledger_file: Path = LEDGER_FILE) -> list[dict[str, Any]]:
    if not ledger_file.exists():
        return []

    entries: list[dict[str, Any]] = []
    for line in ledger_file.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            raw_entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(raw_entry, dict):
            entries.append(normalize_ledger_entry(raw_entry))
    return entries


def normalize_ledger_entry(entry: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(entry)
    normalized.setdefault("evaluator_schema_version", 1)
    normalized["decision"] = normalize_decision(entry.get("decision"))
    normalized.setdefault("target_category", infer_target_category(entry))
    normalized.setdefault("target_parent", str(entry.get("target_parent") or ""))
    return normalized


def normalize_decision(value: Any) -> str:
    decision = str(value or "").lower()
    if decision in {"accept", "accepted"}:
        return "accept"
    if decision in {"reject", "rejected"}:
        return "reject"
    if decision in {"hard_gate_fail", "failed", "fail"}:
        return "hard_gate_fail"
    return decision


def infer_target_category(entry: dict[str, Any]) -> str:
    category = str(entry.get("target_category") or "")
    if category:
        return category
    for artifact in as_list(entry.get("artifacts")):
        if not isinstance(artifact, str):
            continue
        if artifact.startswith("concepts/"):
            parts = artifact.split("/")
            if len(parts) > 1:
                return parts[1]
    return ""


def run_history(
    manifest: dict[str, Any],
    ledger_file: Path = LEDGER_FILE,
    *,
    window: int = 10,
) -> dict[str, Any]:
    entries = [
        entry
        for entry in load_ledger_entries(ledger_file)
        if str(entry.get("harness") or "") in {"", "exploration-loop"}
    ]
    recent = entries[-window:]
    target_category = str(manifest.get("target_category") or "")
    target_parent = str(manifest.get("target_parent") or "")

    rejection_streak = streak_count(entries, {"reject", "hard_gate_fail"})
    hard_gate_failure_streak = streak_count(entries, {"hard_gate_fail"})
    accept_streak = streak_count(entries, {"accept"})
    same_direction_rejection_streak = same_direction_streak(
        entries,
        target_category,
        target_parent,
    )

    if rejection_streak >= 5:
        direction_policy = "forced_pivot"
        guidance = "Five or more consecutive rejected attempts require a forced pivot to a different direction; continue autonomously after selecting a new target."
    elif rejection_streak >= 3 or same_direction_rejection_streak >= 2:
        direction_policy = "pivot_required"
        guidance = "Repeated rejections in this direction require searching a different layer or parent concept."
    else:
        direction_policy = "continue"
        guidance = "Continue autonomously; milestone summaries are informational and do not require permission prompts."

    return {
        "recent_attempts": len(recent),
        "rejection_streak": rejection_streak,
        "hard_gate_failure_streak": hard_gate_failure_streak,
        "same_direction_rejection_streak": same_direction_rejection_streak,
        "accept_streak": accept_streak,
        "direction_policy": direction_policy,
        "should_stop": False,
        "guidance": guidance,
    }


def streak_count(entries: list[dict[str, Any]], decisions: set[str]) -> int:
    count = 0
    for entry in reversed(entries):
        if str(entry.get("decision") or "") in decisions:
            count += 1
            continue
        break
    return count


def same_direction_streak(
    entries: list[dict[str, Any]],
    target_category: str,
    target_parent: str,
) -> int:
    if not target_category:
        return 0
    count = 0
    for entry in reversed(entries):
        if str(entry.get("decision") or "") not in {"reject", "hard_gate_fail"}:
            break
        if str(entry.get("target_category") or "") != target_category:
            break
        entry_parent = str(entry.get("target_parent") or "")
        if target_parent and entry_parent and entry_parent != target_parent:
            break
        count += 1
    return count


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


def hard_gate_results(
    manifest: dict[str, Any],
    index: dict[str, Any],
    run_dir: Path | None = None,
) -> tuple[list[str], list[str]]:
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
        edge_type = str(edge.get("type") or "")
        if not source or not target:
            add_gate(codes, errors, "PROPOSED_EDGE_INVALID", "proposed edge must include source and target")
            continue
        if edge_type not in ALLOWED_EDGE_TYPES:
            add_gate(codes, errors, "EDGE_TYPE_UNKNOWN", f"proposed edge has unknown type: {edge_type or '<missing>'}")
        if source not in valid_ids:
            add_gate(codes, errors, "EDGE_SOURCE_NOT_FOUND", f"proposed edge source not found: {source}")
        if target not in valid_ids:
            add_gate(codes, errors, "EDGE_TARGET_NOT_FOUND", f"proposed edge target not found: {target}")

    if run_dir is not None:
        artifact_codes, artifact_errors = artifact_accounting_gates(manifest, run_dir)
        codes.extend(artifact_codes)
        errors.extend(artifact_errors)

    return codes, errors


def artifact_accounting(manifest: dict[str, Any], run_dir: Path | None) -> dict[str, Any]:
    manifest_edges = len([edge for edge in as_list(manifest.get("proposed_edges")) if isinstance(edge, dict)])
    manifest_sources = len([source for source in as_list(manifest.get("proposed_sources")) if isinstance(source, dict)])
    candidate_edges = count_jsonl(run_dir / "candidate-edges.jsonl") if run_dir else None
    candidate_sources = count_candidate_sources(run_dir / "candidate-sources.yaml") if run_dir else None
    return {
        "manifest_edges": manifest_edges,
        "candidate_edges": candidate_edges,
        "manifest_sources": manifest_sources,
        "candidate_sources": candidate_sources,
    }


def artifact_accounting_gates(manifest: dict[str, Any], run_dir: Path) -> tuple[list[str], list[str]]:
    codes: list[str] = []
    errors: list[str] = []
    accounting = artifact_accounting(manifest, run_dir)

    if (
        accounting["candidate_edges"] is not None
        and accounting["candidate_edges"] != accounting["manifest_edges"]
        and not as_list(manifest.get("rejected_edges"))
    ):
        add_gate(
            codes,
            errors,
            "CANDIDATE_EDGE_ACCOUNTING_MISMATCH",
            "candidate-edges.jsonl count must match proposed_edges or rejected_edges must explain omissions",
        )

    if (
        accounting["candidate_sources"] is not None
        and accounting["candidate_sources"] < accounting["manifest_sources"]
    ):
        add_gate(
            codes,
            errors,
            "CANDIDATE_SOURCE_ACCOUNTING_MISMATCH",
            "candidate-sources.yaml must include every proposed source id",
        )
    return codes, errors


def count_jsonl(path: Path) -> int | None:
    if not path.exists():
        return None
    return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())


def count_candidate_sources(path: Path) -> int | None:
    if not path.exists():
        return None
    count = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip().startswith("- id:"):
            count += 1
    return count


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


def clamp01(value: float) -> float:
    return round(min(1.0, max(0.0, value)), 4)


def metric_record(value: float, threshold: float, higher_is_better: bool, rationale: str) -> dict[str, Any]:
    raw_value = round(value, 4)
    normalized_value = clamp01(value)
    passed = normalized_value >= threshold if higher_is_better else normalized_value <= threshold
    if value < 0.0:
        range_status = "clipped_low"
    elif value > 1.0:
        range_status = "clipped_high"
    else:
        range_status = "in_range"
    return {
        "value": normalized_value,
        "raw_value": raw_value,
        "range_status": range_status,
        "threshold": threshold,
        "status": "pass" if passed else "warn",
        "rationale": rationale,
    }


def scalar_metrics(
    manifest: dict[str, Any],
    index: dict[str, Any],
    history: dict[str, Any],
    creativity: float,
    coverage_gap: float,
    multiplier: float,
    penalty: float,
    score: float,
) -> dict[str, Any]:
    evidence = evidence_strength(manifest)
    claim_hygiene_value = claim_hygiene(manifest)
    focus = focus_score(manifest)
    recovery = rejection_recovery_score(history)
    guidance = guidance_quality_score(manifest, history)
    normalized_legacy = clamp01(score / max(THRESHOLD, 0.0001))
    risk_score = clamp01(1.0 - penalty)
    combined = combined_score(
        {
            "graph_connectivity": creativity,
            "coverage_gap": coverage_gap * multiplier,
            "evidence_strength": evidence,
            "claim_hygiene": claim_hygiene_value,
            "focus_score": focus,
            "rejection_recovery": recovery,
            "guidance_quality": guidance,
            "quality_risk": risk_score,
            "legacy_score": normalized_legacy,
        }
    )
    return {
        "score": metric_record(combined, COMBINED_THRESHOLD, True, "Normalized combined evaluator score; legacy aggregate remains top-level score."),
        "legacy_score": metric_record(normalized_legacy, 1.0, True, "Normalized view of the legacy aggregate score retained for compatibility."),
        "graph_connectivity": metric_record(creativity, 0.25, True, "Measures useful typed graph links attached to proposed nodes."),
        "coverage_gap": metric_record(coverage_gap * multiplier, 0.25, True, "Rewards sparse or stale categories without overriding hard gates."),
        "evidence_strength": metric_record(evidence, 0.5, True, "Measures proposed source tier mix."),
        "claim_hygiene": metric_record(claim_hygiene_value, 0.5, True, "Measures explicit supported/inference/speculative/open labeling."),
        "focus_score": metric_record(focus, 0.5, True, "Penalizes broad survey phrasing and multi-topic sprawl."),
        "rejection_recovery": metric_record(recovery, 0.5, True, "Measures whether repeated failures are being redirected."),
        "guidance_quality": metric_record(guidance, 0.5, True, "Measures whether next targets are specific enough for autonomous continuation."),
        "quality_risk_penalty": metric_record(penalty, 0.5, False, "Penalizes weak sources and broad unfocused descriptions."),
    }


def combined_score(components: dict[str, float]) -> float:
    weights = {
        "graph_connectivity": 0.18,
        "coverage_gap": 0.14,
        "evidence_strength": 0.16,
        "claim_hygiene": 0.14,
        "focus_score": 0.12,
        "rejection_recovery": 0.08,
        "guidance_quality": 0.08,
        "quality_risk": 0.06,
        "legacy_score": 0.04,
    }
    total_weight = sum(weights.values())
    weighted = sum(clamp01(components.get(name, 0.0)) * weight for name, weight in weights.items())
    return clamp01(weighted / total_weight)


def evidence_strength(manifest: dict[str, Any]) -> float:
    sources = [source for source in as_list(manifest.get("proposed_sources")) if isinstance(source, dict)]
    if not sources:
        return 0.0
    total = 0.0
    for source in sources:
        tier = str(source.get("tier") or "")
        if tier == "A":
            total += 1.0
        elif tier == "B":
            total += 0.75
        elif tier == "C":
            total += 0.35
    return round(total / len(sources), 4)


def claim_hygiene(manifest: dict[str, Any]) -> float:
    nodes = [node for node in as_list(manifest.get("proposed_nodes")) if isinstance(node, dict)]
    if not nodes:
        return 0.0
    good = 0
    for node in nodes:
        labels = {str(label) for label in as_list(node.get("claim_labels")) if label}
        sources = [source for source in as_list(node.get("sources")) if source]
        if labels and (sources or labels <= {"open", "speculative"}):
            good += 1
    return round(good / len(nodes), 4)


def focus_score(manifest: dict[str, Any]) -> float:
    description = str(manifest.get("description") or "").lower()
    broad_markers = ["everything", "all topics", "broad survey", "complete ecosystem", "market winner", "stock"]
    penalty = sum(0.2 for marker in broad_markers if marker in description)
    secondary_layers = 0
    for node in as_list(manifest.get("proposed_nodes")):
        if isinstance(node, dict):
            secondary_layers += len(as_list(node.get("secondary_layers")))
    if secondary_layers > 4:
        penalty += 0.2
    return round(max(0.0, 1.0 - penalty), 4)


def rejection_recovery_score(history: dict[str, Any]) -> float:
    if history["direction_policy"] == "continue":
        return 1.0
    if history["direction_policy"] in {"pivot_required", "forced_pivot"}:
        return 0.5
    return 0.0


def guidance_quality_score(manifest: dict[str, Any], history: dict[str, Any]) -> float:
    proposed = [item for item in as_list(manifest.get("proposed_next_targets")) if isinstance(item, dict)]
    if proposed:
        useful = sum(1 for item in proposed if item.get("target_category") and item.get("rationale"))
        return round(useful / len(proposed), 4)
    return 0.75 if history["direction_policy"] == "continue" else 0.5


def next_targets(
    manifest: dict[str, Any],
    index: dict[str, Any],
    ledger_file: Path,
    history: dict[str, Any],
    today: str,
) -> list[dict[str, Any]]:
    nodes = index_nodes(index)
    target_category = str(manifest.get("target_category") or "")
    pivot = history["direction_policy"] in {"pivot_required", "forced_pivot"}
    candidates: list[dict[str, Any]] = []

    for proposed in as_list(manifest.get("proposed_next_targets")):
        if isinstance(proposed, dict) and proposed.get("target_category"):
            category = str(proposed.get("target_category"))
            if pivot and category == target_category:
                continue
            candidates.append(
                {
                    "target_category": category,
                    "target_parent": str(proposed.get("target_parent") or ""),
                    "rationale": str(proposed.get("rationale") or "Agent-proposed target."),
                    "source": "agent_proposed",
                }
            )

    for category in KNOWN_LAYERS:
        if pivot and category == target_category:
            continue
        count = category_count(nodes, category, "")
        latest = latest_category_date(category, ledger_file)
        multiplier = compute_staleness_multiplier(latest, today)
        sparsity = max(0.0, 1.0 - min(count, 10) / 10.0)
        candidates.append(
            {
                "target_category": category,
                "target_parent": "stack.ai-accelerator-ontology",
                "rationale": f"Layer has {count} indexed concepts and staleness multiplier {multiplier}.",
                "source": "graph_gap",
                "rank_score": round(sparsity + multiplier - 1.0, 4),
            }
        )

    deduped: dict[str, dict[str, Any]] = {}
    for candidate in candidates:
        category = candidate["target_category"]
        existing = deduped.get(category)
        if existing is None or candidate.get("rank_score", 1.0) > existing.get("rank_score", 1.0):
            deduped[category] = candidate

    ranked = sorted(
        deduped.values(),
        key=lambda item: (float(item.get("rank_score", 1.0)), item["target_category"]),
        reverse=True,
    )
    for rank, item in enumerate(ranked[:5], 1):
        item["rank"] = rank
        item.setdefault("rank_score", round(1.0 / rank, 4))
    return ranked[:5]


def evaluate(
    manifest: dict[str, Any],
    index: dict[str, Any],
    ledger_file: Path,
    today: str,
    run_dir: Path | None = None,
) -> dict[str, Any]:
    hard_gate_codes, hard_gate_errors = hard_gate_results(manifest, index, run_dir)
    latest_date = latest_category_date(str(manifest.get("target_category") or ""), ledger_file)
    multiplier = compute_staleness_multiplier(latest_date, today)
    creativity = creativity_score(manifest, index)
    coverage_gap = coverage_gap_score(manifest, index)
    penalty = quality_risk_penalty(manifest)
    score = compute_score(creativity, coverage_gap, multiplier, penalty)
    history = run_history(manifest, ledger_file)
    metrics = scalar_metrics(
        manifest,
        index,
        history,
        creativity,
        coverage_gap,
        multiplier,
        penalty,
        score,
    )
    normalized_score = float(metrics["score"]["value"])

    if hard_gate_codes:
        decision = "hard_gate_fail"
    elif score >= THRESHOLD and normalized_score >= COMBINED_THRESHOLD:
        decision = "accept"
    else:
        decision = "reject"

    return {
        "evaluator_schema_version": EVALUATOR_SCHEMA_VERSION,
        "run_id": manifest.get("run_id", ""),
        "decision": decision,
        "score": score,
        "combined_score": normalized_score,
        "threshold": THRESHOLD,
        "combined_threshold": COMBINED_THRESHOLD,
        "creativity_score": creativity,
        "coverage_gap_score": coverage_gap,
        "category_staleness_multiplier": multiplier,
        "category_latest_update": latest_date,
        "quality_risk_penalty": penalty,
        "hard_gate_errors": hard_gate_errors,
        "hard_gate_codes": hard_gate_codes,
        "hard_gates": [
            {"code": code, "message": message}
            for code, message in zip(hard_gate_codes, hard_gate_errors)
        ],
        "metrics": metrics,
        "artifact_accounting": artifact_accounting(manifest, run_dir),
        "run_history": history,
        "next_targets": next_targets(manifest, index, ledger_file, history, today),
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
        payload = evaluate(manifest, index, args.ledger, args.today, args.run_dir)
    except (OSError, ValueError) as exc:
        payload = {
            "evaluator_schema_version": EVALUATOR_SCHEMA_VERSION,
            "run_id": "",
            "decision": "hard_gate_fail",
            "score": 0.0,
            "combined_score": 0.0,
            "threshold": THRESHOLD,
            "combined_threshold": COMBINED_THRESHOLD,
            "creativity_score": 0.0,
            "coverage_gap_score": 0.0,
            "category_staleness_multiplier": 1.0,
            "category_latest_update": None,
            "quality_risk_penalty": 0.0,
            "hard_gate_errors": [str(exc)],
            "hard_gate_codes": ["INVALID_INPUT"],
            "hard_gates": [{"code": "INVALID_INPUT", "message": str(exc)}],
            "metrics": {},
            "artifact_accounting": {},
            "run_history": {
                "recent_attempts": 0,
                "rejection_streak": 0,
                "hard_gate_failure_streak": 0,
                "same_direction_rejection_streak": 0,
                "accept_streak": 0,
                "direction_policy": "continue",
                "should_stop": False,
                "guidance": "Input failed before run history could be evaluated.",
            },
            "next_targets": [],
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
