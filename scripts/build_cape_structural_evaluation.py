#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Evaluate ontology conformance, procedural consistency, and CQ answerability."""

import argparse
import csv
import json
from collections import Counter, defaultdict, deque
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_EXP_DIR = Path("experiments/cape_kg_eacl_20260627")
DEFAULT_OUTPUTS_DIR = Path("outputs")

PROCEDURAL_PREDICATES = {
    "HAS_STEP",
    "PRECEDES",
    "BRANCHES_TO",
    "HAS_GUARD_CONDITION",
    "USES_INPUT",
    "PRODUCES",
    "FEEDS_INTO",
    "USED_AS_INPUT_FOR",
    "PERFORMED_BY",
    "HAS_DECISION_GATEWAY",
    "HAS_REVIEW_CHECKPOINT",
}

CQ_ROWS = [
    ("CQ1", "Task/step composition and order", ["HAS_STEP", "PRECEDES"]),
    ("CQ2", "Task input artifacts", ["USES_INPUT"]),
    ("CQ3", "Task output artifacts", ["PRODUCES"]),
    ("CQ4", "Task responsible roles", ["PERFORMED_BY"]),
    ("CQ5", "Decision gateways", ["HAS_DECISION_GATEWAY"]),
    ("CQ6", "Decision guard conditions", ["HAS_GUARD_CONDITION"]),
    ("CQ7", "Artifact flow between tasks", ["FEEDS_INTO", "USED_AS_INPUT_FOR"]),
    ("CQ8", "Review checkpoints", ["HAS_REVIEW_CHECKPOINT"]),
    ("CQ9", "Principles", ["HAS_PRINCIPLE"]),
    ("CQ10", "Evidence grounding", ["EVIDENCED_BY"]),
    ("CQ11", "NCS capability alignment", ["REQUIRES_CAPABILITY", "CANDIDATE_ALIGNS_WITH"]),
    ("CQ12", "PCF process context", ["PROCESS_CONTEXT", "CANDIDATE_ALIGNS_WITH"]),
]


def read_json(path, default=None):
    path = Path(path)
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path):
    path = Path(path)
    if not path.exists():
        return []
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_json(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_csv(path, rows, fieldnames):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def write_text(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def schema_maps(schema):
    node_types = set(schema.get("node_types") or [])
    edge_types = set(schema.get("edge_types") or [])
    domain_range = {}
    for predicate, rule in (schema.get("domain_range") or {}).items():
        subjects = set(rule.get("subject_types") or [])
        objects = set(rule.get("object_types") or [])
        if "Any" in subjects:
            subjects = None
        if "Any" in objects:
            objects = None
        domain_range[predicate] = (subjects, objects)
    return node_types, edge_types, domain_range


def edge_id(edge, index):
    return edge.get("edge_id") or edge.get("rel_id") or f"edge_{index:06d}"


def validate_ontology(nodes, edges, schema):
    node_types, edge_types, domain_range = schema_maps(schema)
    node_by_id = {row.get("node_id"): row for row in nodes if row.get("node_id")}
    issues = []
    predicate_counts = Counter()
    node_type_counts = Counter(row.get("type") or "" for row in nodes)

    unknown_node_type_count = 0
    for row in nodes:
        node_type = row.get("type")
        if node_type not in node_types:
            unknown_node_type_count += 1
            issues.append({
                "severity": "error",
                "issue_type": "unknown_node_type",
                "node_id": row.get("node_id"),
                "node_type": node_type,
            })

    dangling_edge_count = 0
    unknown_predicate_count = 0
    domain_range_violation_count = 0
    evidence_missing_count = 0
    checked_domain_range_count = 0

    for idx, edge in enumerate(edges):
        eid = edge_id(edge, idx)
        predicate = edge.get("predicate")
        predicate_counts[predicate] += 1
        source = node_by_id.get(edge.get("source_id"))
        target = node_by_id.get(edge.get("target_id"))
        if not source or not target:
            dangling_edge_count += 1
            issues.append({
                "severity": "error",
                "issue_type": "dangling_edge",
                "edge_id": eid,
                "predicate": predicate,
                "source_id": edge.get("source_id"),
                "target_id": edge.get("target_id"),
            })
            continue
        if predicate not in edge_types:
            unknown_predicate_count += 1
            issues.append({
                "severity": "error",
                "issue_type": "unknown_predicate",
                "edge_id": eid,
                "predicate": predicate,
            })
        if not edge.get("evidence_anchor_ids"):
            evidence_missing_count += 1
            issues.append({
                "severity": "warning",
                "issue_type": "missing_evidence_anchor",
                "edge_id": eid,
                "predicate": predicate,
            })
        if predicate in domain_range:
            checked_domain_range_count += 1
            allowed_sources, allowed_targets = domain_range[predicate]
            source_type = source.get("type")
            target_type = target.get("type")
            bad_source = allowed_sources is not None and source_type not in allowed_sources
            bad_target = allowed_targets is not None and target_type not in allowed_targets
            if bad_source or bad_target:
                domain_range_violation_count += 1
                issues.append({
                    "severity": "error",
                    "issue_type": "domain_range_violation",
                    "edge_id": eid,
                    "predicate": predicate,
                    "source_type": source_type,
                    "target_type": target_type,
                    "allowed_source_types": sorted(allowed_sources) if allowed_sources is not None else ["Any"],
                    "allowed_target_types": sorted(allowed_targets) if allowed_targets is not None else ["Any"],
                })

    edge_count = len(edges)
    conformance_issues = (
        dangling_edge_count
        + unknown_predicate_count
        + domain_range_violation_count
        + evidence_missing_count
        + unknown_node_type_count
    )
    conformance_rate = 1.0 if edge_count == 0 else 1.0 - (conformance_issues / max(1, edge_count + len(nodes)))
    return {
        "node_count": len(nodes),
        "edge_count": edge_count,
        "known_node_type_count": len(node_types),
        "known_edge_type_count": len(edge_types),
        "unknown_node_type_count": unknown_node_type_count,
        "unknown_predicate_count": unknown_predicate_count,
        "dangling_edge_count": dangling_edge_count,
        "domain_range_checked_edge_count": checked_domain_range_count,
        "domain_range_violation_count": domain_range_violation_count,
        "evidence_missing_edge_count": evidence_missing_count,
        "ontology_conformance_issue_count": conformance_issues,
        "ontology_conformance_rate": round(max(0.0, conformance_rate), 6),
        "node_type_counts": dict(node_type_counts),
        "predicate_counts": dict(predicate_counts),
        "issues": issues,
    }


def has_cycle(adjacency):
    indegree = Counter()
    nodes = set(adjacency)
    for src, targets in adjacency.items():
        nodes.update(targets)
        for target in targets:
            indegree[target] += 1
    q = deque([node for node in nodes if indegree[node] == 0])
    seen = 0
    while q:
        node = q.popleft()
        seen += 1
        for target in adjacency.get(node, []):
            indegree[target] -= 1
            if indegree[target] == 0:
                q.append(target)
    return seen != len(nodes)


def validate_procedural(nodes, edges):
    node_by_id = {row.get("node_id"): row for row in nodes if row.get("node_id")}
    by_source = defaultdict(list)
    by_target = defaultdict(list)
    precedence = defaultdict(set)
    issues = []
    procedural_edge_count = 0
    for idx, edge in enumerate(edges):
        predicate = edge.get("predicate")
        if predicate in PROCEDURAL_PREDICATES:
            procedural_edge_count += 1
        source_id = edge.get("source_id")
        target_id = edge.get("target_id")
        by_source[source_id].append(edge)
        by_target[target_id].append(edge)
        if predicate == "PRECEDES":
            precedence[source_id].add(target_id)

    precedence_cycle_count = 1 if has_cycle(precedence) else 0
    if precedence_cycle_count:
        issues.append({"severity": "error", "issue_type": "precedes_cycle", "detail": "PRECEDES graph contains at least one cycle."})

    gateway_count = sum(1 for node in nodes if node.get("type") == "DecisionGateway")
    gateway_without_branch_count = 0
    gateway_without_guard_count = 0
    for node in nodes:
        if node.get("type") != "DecisionGateway":
            continue
        node_id = node.get("node_id")
        outgoing = by_source.get(node_id, [])
        if not any(edge.get("predicate") == "BRANCHES_TO" for edge in outgoing):
            gateway_without_branch_count += 1
            issues.append({"severity": "warning", "issue_type": "gateway_without_branch", "node_id": node_id})
        if not any(edge.get("predicate") == "HAS_GUARD_CONDITION" for edge in outgoing):
            gateway_without_guard_count += 1
            issues.append({"severity": "warning", "issue_type": "gateway_without_guard", "node_id": node_id})

    artifact_flow_direction_violation_count = 0
    for idx, edge in enumerate(edges):
        predicate = edge.get("predicate")
        if predicate not in {"FEEDS_INTO", "USED_AS_INPUT_FOR"}:
            continue
        source = node_by_id.get(edge.get("source_id"), {})
        target = node_by_id.get(edge.get("target_id"), {})
        if source.get("type") != "Artifact" or target.get("type") not in {"DomainTask", "ProcedureStep"}:
            artifact_flow_direction_violation_count += 1
            issues.append({
                "severity": "error",
                "issue_type": "artifact_flow_direction_violation",
                "edge_id": edge_id(edge, idx),
                "predicate": predicate,
                "source_type": source.get("type"),
                "target_type": target.get("type"),
            })

    task_count = sum(1 for node in nodes if node.get("type") == "DomainTask")
    step_count = sum(1 for node in nodes if node.get("type") == "ProcedureStep")
    task_or_step_without_io_count = 0
    for node in nodes:
        if node.get("type") not in {"DomainTask", "ProcedureStep"}:
            continue
        node_id = node.get("node_id")
        incident = by_source.get(node_id, []) + by_target.get(node_id, [])
        has_io = any(edge.get("predicate") in {"USES_INPUT", "PRODUCES", "FEEDS_INTO", "USED_AS_INPUT_FOR"} for edge in incident)
        if not has_io:
            task_or_step_without_io_count += 1
            issues.append({"severity": "warning", "issue_type": "task_or_step_without_artifact_io", "node_id": node_id})

    violation_count = (
        precedence_cycle_count
        + artifact_flow_direction_violation_count
        + gateway_without_branch_count
        + gateway_without_guard_count
    )
    consistency_rate = 1.0 if procedural_edge_count == 0 else 1.0 - (violation_count / max(1, procedural_edge_count + gateway_count))
    return {
        "procedural_edge_count": procedural_edge_count,
        "task_count": task_count,
        "procedure_step_count": step_count,
        "decision_gateway_count": gateway_count,
        "precedence_cycle_count": precedence_cycle_count,
        "gateway_without_branch_count": gateway_without_branch_count,
        "gateway_without_guard_count": gateway_without_guard_count,
        "artifact_flow_direction_violation_count": artifact_flow_direction_violation_count,
        "task_or_step_without_artifact_io_count": task_or_step_without_io_count,
        "procedural_consistency_issue_count": violation_count,
        "procedural_consistency_rate": round(max(0.0, consistency_rate), 6),
        "issues": issues,
    }


def cq_answerability(edges, ncs_mapping, pcf_mapping):
    predicate_counts = Counter(edge.get("predicate") for edge in edges)
    evidence_grounded_edges = sum(1 for edge in edges if edge.get("evidence_anchor_ids"))
    ncs_mapping_count = len(ncs_mapping)
    pcf_mapping_count = len(pcf_mapping)
    rows = []
    answerable = 0
    for cq_id, question, predicates in CQ_ROWS:
        if cq_id == "CQ10":
            count = evidence_grounded_edges
            support_source = "edge.evidence_anchor_ids"
        elif cq_id == "CQ11":
            count = ncs_mapping_count
            support_source = "l2_ncs_mapping_candidates.jsonl"
        elif cq_id == "CQ12":
            count = pcf_mapping_count
            support_source = "l2_pcf_mapping_candidates.jsonl"
        else:
            count = sum(predicate_counts.get(predicate, 0) for predicate in predicates)
            support_source = "layer2_edges"
        ok = count > 0
        if ok:
            answerable += 1
        rows.append({
            "cq_id": cq_id,
            "question": question,
            "required_predicates": ",".join(predicates),
            "support_source": support_source,
            "supporting_edge_count": count,
            "answerable_by_current_kg": ok,
            "claim_status": "kg_structural_diagnostic_not_human_gold",
        })
    return {
        "cq_count": len(rows),
        "answerable_cq_count": answerable,
        "cq_answerability_rate": round(answerable / len(rows), 6) if rows else 0.0,
        "rows": rows,
    }


def render_report(payload):
    o = payload["ontology_conformance"]
    p = payload["procedural_consistency"]
    cq = payload["cq_answerability"]
    lines = [
        "# CAPE-KG Structural Evaluation",
        "",
        f"Generated: {payload['generated_at_utc']}",
        f"Claim status: `{payload['claim_status']}`",
        "",
        "This report evaluates the current built KG structure. It is not a replacement for human-gold scoring.",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Nodes | {o['node_count']} |",
        f"| Edges | {o['edge_count']} |",
        f"| Ontology conformance rate | {o['ontology_conformance_rate']} |",
        f"| Domain/range violations | {o['domain_range_violation_count']} |",
        f"| Dangling edges | {o['dangling_edge_count']} |",
        f"| Evidence-missing edges | {o['evidence_missing_edge_count']} |",
        f"| Procedural consistency rate | {p['procedural_consistency_rate']} |",
        f"| Procedural edges | {p['procedural_edge_count']} |",
        f"| PRECEDES cycle count | {p['precedence_cycle_count']} |",
        f"| Gateway without branch | {p['gateway_without_branch_count']} |",
        f"| Gateway without guard | {p['gateway_without_guard_count']} |",
        f"| Artifact-flow direction violations | {p['artifact_flow_direction_violation_count']} |",
        f"| CQ answerability rate | {cq['cq_answerability_rate']} |",
        f"| Answerable CQs | {cq['answerable_cq_count']} / {cq['cq_count']} |",
        "",
        "## CQ Answerability",
        "",
        "| CQ | support count | answerable | support source | predicates |",
        "|---|---:|---:|---|---|",
    ]
    for row in cq["rows"]:
        lines.append(
            f"| {row['cq_id']} | {row['supporting_edge_count']} | "
            f"{'yes' if row['answerable_by_current_kg'] else 'no'} | "
            f"`{row['support_source']}` | `{row['required_predicates']}` |"
        )
    lines += [
        "",
        "## Interpretation",
        "",
        "- Ontology conformance checks node types, predicates, dangling edges, domain/range constraints, and evidence-anchor presence.",
        "- Procedural consistency checks PRECEDES cycles, gateway branch/guard availability, and artifact-flow direction.",
        "- CQ answerability is structural: a CQ is answerable if at least one supporting predicate exists in the current KG.",
        "- Human-gold evaluation must still recompute these metrics against adjudicated labels before final paper claims.",
        "",
    ]
    return "\n".join(lines)


def run(args):
    exp_dir = Path(args.experiment_dir)
    outputs_dir = Path(args.outputs_dir)
    eval_dir = exp_dir / "04_evaluation"
    schema = read_json(exp_dir / "02_schema/cape_schema.json", {}) or {}
    nodes = read_jsonl(outputs_dir / "07_layer2_graph/layer2_nodes.jsonl")
    edges = read_jsonl(outputs_dir / "07_layer2_graph/layer2_edges.jsonl")
    ncs_mapping = read_jsonl(outputs_dir / "08_mapping/l2_ncs_mapping_candidates.jsonl")
    pcf_mapping = read_jsonl(outputs_dir / "08_mapping/l2_pcf_mapping_candidates.jsonl")

    ontology = validate_ontology(nodes, edges, schema)
    procedural = validate_procedural(nodes, edges)
    cq = cq_answerability(edges, ncs_mapping, pcf_mapping)
    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "experiment_dir": str(exp_dir),
        "outputs_dir": str(outputs_dir),
        "schema_file": str(exp_dir / "02_schema/cape_schema.json"),
        "nodes_file": str(outputs_dir / "07_layer2_graph/layer2_nodes.jsonl"),
        "edges_file": str(outputs_dir / "07_layer2_graph/layer2_edges.jsonl"),
        "ncs_mapping_file": str(outputs_dir / "08_mapping/l2_ncs_mapping_candidates.jsonl"),
        "pcf_mapping_file": str(outputs_dir / "08_mapping/l2_pcf_mapping_candidates.jsonl"),
        "claim_status": "kg_structural_diagnostic_not_human_gold",
        "ontology_conformance": ontology,
        "procedural_consistency": procedural,
        "cq_answerability": cq,
    }

    write_json(eval_dir / "structural_evaluation_metrics.json", payload)
    write_csv(
        eval_dir / "structural_evaluation_summary.csv",
        [
            {"metric": "ontology_conformance_rate", "value": ontology["ontology_conformance_rate"]},
            {"metric": "domain_range_violation_count", "value": ontology["domain_range_violation_count"]},
            {"metric": "evidence_missing_edge_count", "value": ontology["evidence_missing_edge_count"]},
            {"metric": "procedural_consistency_rate", "value": procedural["procedural_consistency_rate"]},
            {"metric": "precedence_cycle_count", "value": procedural["precedence_cycle_count"]},
            {"metric": "gateway_without_branch_count", "value": procedural["gateway_without_branch_count"]},
            {"metric": "gateway_without_guard_count", "value": procedural["gateway_without_guard_count"]},
            {"metric": "artifact_flow_direction_violation_count", "value": procedural["artifact_flow_direction_violation_count"]},
            {"metric": "cq_answerability_rate", "value": cq["cq_answerability_rate"]},
            {"metric": "answerable_cq_count", "value": cq["answerable_cq_count"]},
        ],
        ["metric", "value"],
    )
    write_csv(
        eval_dir / "cq_answerability_structural.csv",
        cq["rows"],
        ["cq_id", "question", "required_predicates", "support_source", "supporting_edge_count", "answerable_by_current_kg", "claim_status"],
    )
    write_json(eval_dir / "ontology_conformance_metrics.json", ontology)
    write_json(eval_dir / "procedural_consistency_metrics.json", procedural)
    write_json(eval_dir / "cq_answerability_structural_metrics.json", cq)
    report = render_report(payload)
    write_text(eval_dir / "structural_evaluation_report.md", report)
    write_text(eval_dir / "ontology_conformance_report.md", report)
    write_text(eval_dir / "procedural_consistency_report.md", report)
    print(json.dumps({
        "metrics_json": str(eval_dir / "structural_evaluation_metrics.json"),
        "report_md": str(eval_dir / "structural_evaluation_report.md"),
        "ontology_conformance_rate": ontology["ontology_conformance_rate"],
        "procedural_consistency_rate": procedural["procedural_consistency_rate"],
        "cq_answerability_rate": cq["cq_answerability_rate"],
        "claim_status": payload["claim_status"],
    }, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-dir", default=str(DEFAULT_EXP_DIR))
    parser.add_argument("--outputs-dir", default=str(DEFAULT_OUTPUTS_DIR))
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
