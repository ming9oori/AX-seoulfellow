#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build review worklists for structural follow-up found in CAPE-KG diagnostics."""

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_EXP_DIR = Path("experiments/cape_kg_eacl_20260627")
DEFAULT_OUTPUTS_DIR = Path("outputs")

REVIEW_TERMS = (
    "review",
    "checkpoint",
    "검토",
    "리뷰",
    "승인",
    "심사",
    "점검",
    "체크",
    "품질",
    "충실도",
    "Blue Team",
    "Pink Team",
    "Red Team",
)


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


def short_text(value, limit=240):
    value = str(value or "").replace("\n", " ").strip()
    return value if len(value) <= limit else value[: limit - 3] + "..."


def node_text(node, include_definition=False):
    keys = ["node_id", "label", "label_ko", "label_en", "aliases"]
    if include_definition:
        keys.append("definition")
    return " ".join(
        str(node.get(key) or "")
        for key in keys
    )


def contains_review_signal(node):
    text = node_text(node, include_definition=False).lower()
    return any(term.lower() in text for term in REVIEW_TERMS)


def matched_review_terms(node):
    text = node_text(node, include_definition=False).lower()
    return sorted({term for term in REVIEW_TERMS if term.lower() in text})


def evidence_preview(node, evidence_by_id):
    previews = []
    for eid in node.get("evidence_anchor_ids", [])[:3]:
        ev = evidence_by_id.get(eid) or {}
        if ev:
            previews.append(f"{eid}: p.{ev.get('page')} {short_text(ev.get('text'), 160)}")
        else:
            previews.append(eid)
    return " | ".join(previews)


def label_for_node(node):
    return str(node.get("label") or node.get("label_ko") or node.get("label_en") or node.get("node_id") or "")


def labels_for_ids(node_by_id, node_ids):
    labels = []
    for node_id in node_ids:
        node = node_by_id.get(node_id) or {}
        label = label_for_node(node)
        labels.append(f"{node_id}:{label}" if label else node_id)
    return labels


def review_checkpoint_candidates(nodes, edges, evidence_by_id):
    by_target = defaultdict(list)
    by_source = defaultdict(list)
    for edge in edges:
        by_target[edge.get("target_id")].append(edge)
        by_source[edge.get("source_id")].append(edge)

    rows = []
    for node in nodes:
        if node.get("type") not in {"DomainTask", "ProcedureStep"}:
            continue
        if not contains_review_signal(node):
            continue
        terms = matched_review_terms(node)
        incoming_has_step = [edge for edge in by_target.get(node.get("node_id"), []) if edge.get("predicate") == "HAS_STEP"]
        parent_task_id = node.get("parent_task_id") or (incoming_has_step[0].get("source_id") if incoming_has_step else "")
        outgoing_preds = sorted({edge.get("predicate") for edge in by_source.get(node.get("node_id"), []) if edge.get("predicate")})
        incoming_preds = sorted({edge.get("predicate") for edge in by_target.get(node.get("node_id"), []) if edge.get("predicate")})
        has_projected_checkpoint = "HAS_REVIEW_CHECKPOINT" in outgoing_preds
        action = "confirm_projected_review_checkpoint_or_keep_existing_type"
        if node.get("type") == "ProcedureStep":
            action = "confirm_projected_review_checkpoint" if has_projected_checkpoint else "consider_add_HAS_REVIEW_CHECKPOINT_from_step"
        elif node.get("type") == "DomainTask":
            action = "consider_retyping_or_linking_as_review_checkpoint"
        rows.append(
            {
                "gap_type": "cq8_review_checkpoint_candidate",
                "node_id": node.get("node_id"),
                "label": node.get("label"),
                "current_type": node.get("type"),
                "parent_task_id": parent_task_id,
                "incoming_predicates": ",".join(incoming_preds),
                "outgoing_predicates": ",".join(outgoing_preds),
                "evidence_anchor_count": len(node.get("evidence_anchor_ids") or []),
                "evidence_preview": evidence_preview(node, evidence_by_id),
                "matched_review_terms": ",".join(terms),
                "recommended_action": action,
                "human_decision": "",
                "human_notes": "",
            }
        )
    rows.sort(key=lambda row: (row["current_type"], row["node_id"]))
    return rows


def gateway_gap_rows(nodes, edges, evidence_by_id):
    node_by_id = {node.get("node_id"): node for node in nodes if node.get("node_id")}
    by_source = defaultdict(list)
    by_target = defaultdict(list)
    successors = defaultdict(set)
    for edge in edges:
        by_source[edge.get("source_id")].append(edge)
        by_target[edge.get("target_id")].append(edge)
        if edge.get("predicate") == "PRECEDES":
            successors[edge.get("source_id")].add(edge.get("target_id"))

    rows = []
    for node in nodes:
        if node.get("type") != "DecisionGateway":
            continue
        outs = by_source.get(node.get("node_id"), [])
        pred_counts = Counter(edge.get("predicate") for edge in outs)
        if pred_counts.get("BRANCHES_TO", 0) > 0:
            continue
        guard_edges = [edge for edge in outs if edge.get("predicate") == "HAS_GUARD_CONDITION"]
        guard_condition_ids = [edge.get("target_id") for edge in guard_edges if edge.get("target_id")]
        incoming_context = [edge for edge in by_target.get(node.get("node_id"), []) if edge.get("predicate") == "HAS_DECISION_GATEWAY"]
        context_sources = [edge.get("source_id") for edge in incoming_context if edge.get("source_id")]
        branch_candidates = []
        for source_id in context_sources:
            branch_candidates.extend(sorted(successors.get(source_id, [])))
            source_node = node_by_id.get(source_id) or {}
            if source_node.get("type") in {"DomainTask", "ProcedureStep"}:
                branch_candidates.append(source_id)
        branch_candidates = sorted({item for item in branch_candidates if item})
        branch_candidates_preview = branch_candidates[:12]
        rows.append(
            {
                "gap_type": "gateway_without_branch",
                "gateway_id": node.get("node_id"),
                "gateway_label": node.get("label"),
                "guard_condition_edges": pred_counts.get("HAS_GUARD_CONDITION", 0),
                "guard_condition_ids": ",".join(guard_condition_ids),
                "guard_condition_labels": " | ".join(labels_for_ids(node_by_id, guard_condition_ids)),
                "incoming_task_count": len(context_sources),
                "incoming_task_ids": ",".join(context_sources),
                "incoming_task_labels": " | ".join(labels_for_ids(node_by_id, context_sources)),
                "candidate_branch_target_ids": ",".join(branch_candidates_preview),
                "candidate_branch_target_labels": " | ".join(labels_for_ids(node_by_id, branch_candidates_preview)),
                "evidence_anchor_count": len(node.get("evidence_anchor_ids") or []),
                "evidence_preview": evidence_preview(node, evidence_by_id),
                "recommended_action": "add_BRanches_TO_only_if_source_text_supports_the_outcomes",
                "human_decision": "",
                "human_notes": "",
            }
        )
    rows.sort(key=lambda row: row["gateway_id"])
    return rows


def render_report(summary, review_rows, gateway_rows):
    lines = [
        "# CAPE-KG Structural Gap Worklist",
        "",
        f"Generated: {summary['generated_at_utc']}",
        f"Claim status: `{summary['claim_status']}`",
        "",
        "This worklist turns structural diagnostics into reviewable repair candidates. It does not modify the KG automatically.",
        "",
        "## Summary",
        "",
        "| Item | Value |",
        "|---|---:|",
        f"| Review checkpoint candidates | {summary['review_checkpoint_candidate_count']} |",
        f"| Gateway branch gaps | {summary['gateway_branch_gap_count']} |",
        f"| Structural CQ answerability | {summary['structural_cq_answerability_rate']} |",
        f"| Procedural consistency | {summary['procedural_consistency_rate']} |",
        "",
        "## Review Checkpoint Candidates",
        "",
        "| node | type | label | recommended action |",
        "|---|---|---|---|",
    ]
    for row in review_rows[:50]:
        lines.append(
            f"| `{row['node_id']}` | {row['current_type']} | {row['label']} | {row['recommended_action']} |"
        )
    if len(review_rows) > 50:
        lines.append(f"| ... | ... | {len(review_rows) - 50} more rows in CSV | ... |")
    lines += [
        "",
        "## Gateway Branch Gaps",
        "",
        "| gateway | label | guards | incoming tasks | candidate branch targets |",
        "|---|---|---:|---:|---|",
    ]
    for row in gateway_rows:
        targets = row.get("candidate_branch_target_labels") or row.get("candidate_branch_target_ids")
        lines.append(
            f"| `{row['gateway_id']}` | {row['gateway_label']} | {row['guard_condition_edges']} | "
            f"{row['incoming_task_count']} | `{targets}` |"
        )
    lines += [
        "",
        "## Interpretation",
        "",
        "- Review-signaled `ProcedureStep` rows are now projected to `ReviewCheckpoint` through `HAS_REVIEW_CHECKPOINT`; this list remains for human confirmation and possible cleanup.",
        "- Gateway branch edges should not be synthesized automatically unless source evidence clearly states branch outcomes.",
        "- Human review can use these rows to confirm projected checkpoints, retype a node, or add `BRANCHES_TO` edges.",
        "",
    ]
    return "\n".join(lines)


def run(args):
    exp_dir = Path(args.experiment_dir)
    outputs_dir = Path(args.outputs_dir)
    eval_dir = exp_dir / "04_evaluation"
    review_dir = exp_dir / "05_review"
    nodes = read_jsonl(outputs_dir / "07_layer2_graph/layer2_nodes.jsonl")
    edges = read_jsonl(outputs_dir / "07_layer2_graph/layer2_edges.jsonl")
    evidence = read_jsonl(outputs_dir / "07_layer2_graph/layer2_evidence_index.jsonl")
    evidence_by_id = {row.get("evidence_anchor_id"): row for row in evidence if row.get("evidence_anchor_id")}
    structural = read_json(eval_dir / "structural_evaluation_metrics.json", {}) or {}

    review_rows = review_checkpoint_candidates(nodes, edges, evidence_by_id)
    gateway_rows = gateway_gap_rows(nodes, edges, evidence_by_id)
    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "experiment_dir": str(exp_dir),
        "outputs_dir": str(outputs_dir),
        "claim_status": "structural_gap_worklist_pending_human_review",
        "review_checkpoint_candidate_count": len(review_rows),
        "gateway_branch_gap_count": len(gateway_rows),
        "structural_cq_answerability_rate": (structural.get("cq_answerability") or {}).get("cq_answerability_rate"),
        "procedural_consistency_rate": (structural.get("procedural_consistency") or {}).get("procedural_consistency_rate"),
        "human_gate_effect": "does_not_change_minimum_11_file_paper_gate",
        "outputs": {
            "review_checkpoint_candidates_csv": str(review_dir / "structural_review_checkpoint_candidates.csv"),
            "gateway_branch_gaps_csv": str(review_dir / "structural_gateway_branch_gaps.csv"),
            "summary_json": str(eval_dir / "structural_gap_worklist_summary.json"),
            "report_md": str(eval_dir / "structural_gap_worklist_report.md"),
        },
    }

    write_csv(
        review_dir / "structural_review_checkpoint_candidates.csv",
        review_rows,
        [
            "gap_type",
            "node_id",
            "label",
            "current_type",
            "parent_task_id",
            "incoming_predicates",
            "outgoing_predicates",
            "evidence_anchor_count",
            "evidence_preview",
            "matched_review_terms",
            "recommended_action",
            "human_decision",
            "human_notes",
        ],
    )
    write_csv(
        review_dir / "structural_gateway_branch_gaps.csv",
        gateway_rows,
        [
            "gap_type",
            "gateway_id",
            "gateway_label",
            "guard_condition_edges",
            "guard_condition_ids",
            "guard_condition_labels",
            "incoming_task_count",
            "incoming_task_ids",
            "incoming_task_labels",
            "candidate_branch_target_ids",
            "candidate_branch_target_labels",
            "evidence_anchor_count",
            "evidence_preview",
            "recommended_action",
            "human_decision",
            "human_notes",
        ],
    )
    write_json(eval_dir / "structural_gap_worklist_summary.json", summary)
    write_text(eval_dir / "structural_gap_worklist_report.md", render_report(summary, review_rows, gateway_rows))
    print(json.dumps(summary, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-dir", default=str(DEFAULT_EXP_DIR))
    parser.add_argument("--outputs-dir", default=str(DEFAULT_OUTPUTS_DIR))
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
