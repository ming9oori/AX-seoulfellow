#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build an EACL-oriented CAPE-KG experiment package from the current AX-EPAK KG.

The referenced EACL plan requires human gold annotation and LLM baselines. This
script creates the reproducible experimental scaffold that can be run now:

- a 100+ chunk evaluation subset,
- a silver reference set derived from the current evidence-grounded KG,
- baseline/proposed proxy predictions for metric wiring and ablation sanity,
- annotation and review sheets for replacing silver labels with human gold,
- reports for evidence grounding, ontology conformance, procedural consistency,
  CQ answerability, taxonomy mapping, and paper readiness.

The reports explicitly mark silver/proxy results as non-claimable for a paper
until human adjudicated labels and actual LLM baseline generations are added.
"""

import argparse
import csv
import hashlib
import json
import math
import statistics
from collections import Counter, defaultdict, deque
from datetime import datetime, timezone
from pathlib import Path


RUN_DATE = "2026-06-27"
DEFAULT_KG_DIR = Path("outputs")
DEFAULT_EXP_DIR = Path("experiments/cape_kg_eacl_20260627")

NODE_TYPES = [
    "DomainTask",
    "ProcedureStep",
    "DecisionGateway",
    "GuardCondition",
    "Artifact",
    "ArtifactFlow",
    "Role",
    "ReviewCheckpoint",
    "Principle",
    "Risk",
    "EvidenceAnchor",
    "NCSCompetencyUnit",
    "PCFElement",
    "MappingCandidate",
]

EDGE_TYPES = [
    "HAS_STEP",
    "PRECEDES",
    "BRANCHES_TO",
    "HAS_GUARD_CONDITION",
    "USES_INPUT",
    "PRODUCES",
    "FEEDS_INTO",
    "PERFORMED_BY",
    "HAS_DECISION_GATEWAY",
    "HAS_REVIEW_CHECKPOINT",
    "HAS_PRINCIPLE",
    "HAS_RISK",
    "EVIDENCED_BY",
    "REQUIRES_CAPABILITY",
    "PROCESS_CONTEXT",
    "CANDIDATE_ALIGNS_WITH",
    # Existing internal KG spelling retained for compatibility.
    "USED_AS_INPUT_FOR",
]

DOMAIN_RANGE = {
    "HAS_STEP": ({"DomainTask"}, {"ProcedureStep"}),
    "PRECEDES": ({"DomainTask", "ProcedureStep", "ReviewCheckpoint"}, {"DomainTask", "ProcedureStep", "ReviewCheckpoint"}),
    "BRANCHES_TO": ({"DecisionGateway"}, {"DomainTask", "ProcedureStep"}),
    "HAS_GUARD_CONDITION": ({"DecisionGateway"}, {"GuardCondition"}),
    "USES_INPUT": ({"DomainTask", "ProcedureStep"}, {"Artifact"}),
    "PRODUCES": ({"DomainTask", "ProcedureStep"}, {"Artifact"}),
    "FEEDS_INTO": ({"Artifact"}, {"DomainTask", "ProcedureStep"}),
    "USED_AS_INPUT_FOR": ({"Artifact"}, {"DomainTask", "ProcedureStep"}),
    "PERFORMED_BY": ({"DomainTask", "ProcedureStep"}, {"Role"}),
    "HAS_DECISION_GATEWAY": ({"DomainTask", "ProcedureStep"}, {"DecisionGateway"}),
    "HAS_REVIEW_CHECKPOINT": ({"DomainTask", "ProcedureStep"}, {"ReviewCheckpoint"}),
    "HAS_PRINCIPLE": ({"DomainTask", "ProcedureStep"}, {"Principle"}),
    "HAS_RISK": ({"DomainTask", "ProcedureStep"}, {"Risk"}),
    "EVIDENCED_BY": (None, {"EvidenceAnchor"}),
    "REQUIRES_CAPABILITY": ({"DomainTask"}, {"NCSCompetencyUnit"}),
    "PROCESS_CONTEXT": ({"DomainTask"}, {"PCFElement"}),
    "CANDIDATE_ALIGNS_WITH": ({"DomainTask"}, {"NCSCompetencyUnit", "PCFElement"}),
}

CQS = [
    ("CQ1", "수주·제안 업무는 어떤 주요 Task와 절차 단계로 구성되는가?", ["HAS_STEP", "PRECEDES"]),
    ("CQ2", "각 Task는 어떤 입력 자료를 사용하는가?", ["USES_INPUT"]),
    ("CQ3", "각 Task는 어떤 산출물을 생성하는가?", ["PRODUCES"]),
    ("CQ4", "각 Task는 누가 수행하거나 책임지는가?", ["PERFORMED_BY"]),
    ("CQ5", "어떤 의사결정 지점이 존재하는가?", ["HAS_DECISION_GATEWAY"]),
    ("CQ6", "의사결정에는 어떤 조건이나 판단 기준이 필요한가?", ["HAS_GUARD_CONDITION"]),
    ("CQ7", "산출물은 다음 업무에서 어떻게 사용되는가?", ["FEEDS_INTO", "USED_AS_INPUT_FOR"]),
    ("CQ8", "제안서 리뷰는 어떤 단계에서 어떻게 수행되는가?", ["HAS_REVIEW_CHECKPOINT"]),
    ("CQ9", "각 업무에서 지켜야 할 원칙은 무엇인가?", ["HAS_PRINCIPLE"]),
    ("CQ10", "각 지식 항목은 원문 어느 chunk/page/span에 근거가 있는가?", ["EVIDENCED_BY"]),
    ("CQ11", "특정 업무는 어떤 NCS 능력단위와 관련되는가?", ["REQUIRES_CAPABILITY", "CANDIDATE_ALIGNS_WITH"]),
    ("CQ12", "특정 업무는 PCF 프로세스 체계상 어디에 위치하는가?", ["PROCESS_CONTEXT", "CANDIDATE_ALIGNS_WITH"]),
]


def sha1_text(text, size=12):
    return hashlib.sha1(str(text).encode("utf-8")).hexdigest()[:size]


def strip_prefix_suffix(value, prefix="", suffix=""):
    value = str(value)
    if prefix and value.startswith(prefix):
        value = value[len(prefix):]
    if suffix and value.endswith(suffix):
        value = value[:-len(suffix)]
    return value


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def read_jsonl(path):
    rows = []
    with Path(path).open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def write_jsonl(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True))
            f.write("\n")


def write_text(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_csv(path, rows, fieldnames=None):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = list(rows)
    if fieldnames is None:
        fieldnames = []
        for row in rows:
            for key in row:
                if key not in fieldnames:
                    fieldnames.append(key)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def load_kg(kg_dir):
    kg_dir = Path(kg_dir)
    return {
        "summary": read_json(kg_dir / "run_summary.json"),
        "chunks": read_jsonl(kg_dir / "02_ocr/layer2_chunks.jsonl"),
        "nodes": read_jsonl(kg_dir / "07_layer2_graph/layer2_nodes.jsonl"),
        "edges": read_jsonl(kg_dir / "07_layer2_graph/layer2_edges.jsonl"),
        "evidence": read_jsonl(kg_dir / "07_layer2_graph/layer2_evidence_index.jsonl"),
        "ncs_mapping": read_jsonl(kg_dir / "08_mapping/l2_ncs_mapping_candidates.jsonl"),
        "pcf_mapping": read_jsonl(kg_dir / "08_mapping/l2_pcf_mapping_candidates.jsonl"),
    }


def select_chunks(chunks, sample_size):
    by_chapter = defaultdict(list)
    for chunk in sorted(chunks, key=lambda c: c["chunk_id"]):
        by_chapter[chunk.get("chapter_id") or "CH00"].append(chunk)
    selected = []
    seen = set()
    # Round-robin across chapters first to avoid concentrating the benchmark.
    queues = {chapter: deque(rows) for chapter, rows in sorted(by_chapter.items())}
    while len(selected) < min(sample_size, len(chunks)) and queues:
        for chapter in list(queues):
            if len(selected) >= min(sample_size, len(chunks)):
                break
            q = queues[chapter]
            if not q:
                queues.pop(chapter, None)
                continue
            chunk = q.popleft()
            if chunk["chunk_id"] not in seen:
                selected.append(chunk)
                seen.add(chunk["chunk_id"])
    # Deterministic fill if any chapter had too few chunks.
    for chunk in sorted(chunks, key=lambda c: c["chunk_id"]):
        if len(selected) >= min(sample_size, len(chunks)):
            break
        if chunk["chunk_id"] not in seen:
            selected.append(chunk)
            seen.add(chunk["chunk_id"])
    return selected


def make_reference(kg, selected_chunks):
    selected_ids = {c["chunk_id"] for c in selected_chunks}
    node_by_id = {n["node_id"]: n for n in kg["nodes"]}
    evidence_by_id = {e["evidence_anchor_id"]: e for e in kg["evidence"]}

    ref_edges = []
    ref_nodes = {}
    ref_evidence = {}
    for edge in kg["edges"]:
        edge_evidence = [evidence_by_id[eid] for eid in edge.get("evidence_anchor_ids", []) if eid in evidence_by_id]
        if not any(ev.get("chunk_id") in selected_ids for ev in edge_evidence):
            continue
        source = node_by_id.get(edge["source_id"], {})
        target = node_by_id.get(edge["target_id"], {})
        spans = []
        for ev in edge_evidence:
            if ev.get("chunk_id") in selected_ids:
                ref_evidence[ev["evidence_anchor_id"]] = ev
                spans.append(
                    {
                        "evidence_anchor_id": ev["evidence_anchor_id"],
                        "chunk_id": ev.get("chunk_id"),
                        "page": ev.get("page"),
                        "sentence_id": ev.get("sentence_id"),
                        "start_char": ev.get("span_start", 0),
                        "end_char": ev.get("span_end", 0),
                        "text": ev.get("text", ""),
                    }
                )
        ref = {
            "reference_id": "REF-" + sha1_text(edge["edge_id"], 16),
            "source_id": edge["source_id"],
            "source_label": source.get("label", edge["source_id"]),
            "source_type": source.get("type"),
            "predicate": edge["predicate"],
            "target_id": edge["target_id"],
            "target_label": target.get("label", edge["target_id"]),
            "target_type": target.get("type"),
            "evidence_spans": spans,
            "evidence_anchor_ids": [s["evidence_anchor_id"] for s in spans],
            "confidence": edge.get("confidence", 1.0),
            "source_edge_id": edge["edge_id"],
            "silver_status": "silver_reference_from_current_kg_pending_human_adjudication",
        }
        ref_edges.append(ref)
        if source:
            ref_nodes[source["node_id"]] = source
        if target:
            ref_nodes[target["node_id"]] = target
    return list(ref_nodes.values()), ref_edges, list(ref_evidence.values())


def evidence_mode(edge, mode):
    spans = edge.get("evidence_spans", [])
    if mode == "none":
        return [], []
    if mode == "chunk":
        chunk_ids = sorted({s["chunk_id"] for s in spans if s.get("chunk_id")})
        return [{"chunk_id": c, "anchor_type": "chunk_anchor"} for c in chunk_ids], []
    if mode == "sentence":
        return spans, [s["evidence_anchor_id"] for s in spans]
    return spans, [s["evidence_anchor_id"] for s in spans]


def predicted_edge(ref, condition, evidence="sentence", predicate=None, keep_types=True, confidence_delta=0.0):
    spans, anchor_ids = evidence_mode(ref, evidence)
    pred = {
        "prediction_id": f"PRED-{condition}-{sha1_text(ref['reference_id'], 12)}",
        "condition": condition,
        "source_id": ref["source_id"],
        "source_label": ref["source_label"],
        "source_type": ref["source_type"] if keep_types else "Unknown",
        "predicate": predicate or ref["predicate"],
        "target_id": ref["target_id"],
        "target_label": ref["target_label"],
        "target_type": ref["target_type"] if keep_types else "Unknown",
        "evidence_spans": spans,
        "evidence_anchor_ids": anchor_ids,
        "confidence": round(max(0.0, min(1.0, ref.get("confidence", 0.75) + confidence_delta)), 4),
        "source_reference_id": ref["reference_id"],
    }
    return pred


def make_predictions(ref_edges):
    predictions = {}
    ordered = sorted(ref_edges, key=lambda r: r["reference_id"])

    # B0: plain triple extraction proxy. Keeps labels but drops schema types and most predicates.
    b0 = []
    for idx, ref in enumerate(ordered):
        if idx % 10 in {0, 1, 2, 3, 4, 5}:
            pred = ref["predicate"] if idx % 4 == 0 else "RELATED_TO"
            b0.append(predicted_edge(ref, "B0_plain_llm_proxy", evidence="chunk", predicate=pred, keep_types=False, confidence_delta=-0.25))
    predictions["B0_plain_llm_proxy"] = b0

    # B1: predicate constrained proxy. Allowed predicates, weaker evidence and some recall loss.
    b1 = []
    for idx, ref in enumerate(ordered):
        if idx % 10 in {0, 1, 2, 3, 4, 5, 6, 7}:
            b1.append(predicted_edge(ref, "B1_predicate_constrained_proxy", evidence="sentence", keep_types=False, confidence_delta=-0.15))
    predictions["B1_predicate_constrained_proxy"] = b1

    # B2: current project baseline. Uses current KG edges but without CAPE-specific span slot scoring.
    b2 = [predicted_edge(ref, "B2_current_project_baseline", evidence="sentence", keep_types=True, confidence_delta=-0.05) for ref in ordered]
    predictions["B2_current_project_baseline"] = b2

    # B4: taxonomy-RAG proxy. Keeps task/artifact/process edges likely useful for mapping.
    taxonomy_preds = []
    taxonomy_predicates = {"USES_INPUT", "PRODUCES", "PERFORMED_BY", "HAS_PRINCIPLE", "HAS_RISK"}
    for ref in ordered:
        if ref["predicate"] in taxonomy_predicates:
            taxonomy_preds.append(predicted_edge(ref, "B4_taxonomy_rag_proxy", evidence="sentence", keep_types=True, confidence_delta=-0.08))
    predictions["B4_taxonomy_rag_proxy"] = taxonomy_preds

    # B5: procedural prompt baseline. Focuses on procedural edges only.
    procedural_predicates = {"HAS_STEP", "PRECEDES", "HAS_DECISION_GATEWAY", "HAS_GUARD_CONDITION", "FEEDS_INTO", "USED_AS_INPUT_FOR"}
    b5 = [predicted_edge(ref, "B5_procedural_prompt_proxy", evidence="sentence", keep_types=True, confidence_delta=-0.10) for ref in ordered if ref["predicate"] in procedural_predicates]
    predictions["B5_procedural_prompt_proxy"] = b5

    # P and ablations.
    p = [predicted_edge(ref, "P_cape_kg_silver", evidence="sentence", keep_types=True, confidence_delta=0.02) for ref in ordered]
    predictions["P_cape_kg_silver"] = p
    predictions["P_minus_CQ_proxy"] = [pred for i, pred in enumerate(p) if i % 12 not in {0, 1}]
    predictions["P_minus_Evidence_proxy"] = [dict(pred, condition="P_minus_Evidence_proxy", evidence_spans=[], evidence_anchor_ids=[]) for pred in p]
    predictions["P_minus_Procedural_schema_proxy"] = [dict(pred, condition="P_minus_Procedural_schema_proxy") for pred in p if pred["predicate"] not in procedural_predicates]
    predictions["P_minus_Validator_proxy"] = p + [
        dict(
            pred,
            prediction_id=pred["prediction_id"] + "-invalid",
            condition="P_minus_Validator_proxy",
            predicate="PRODUCES",
            target_type="Role",
            target_label=pred["target_label"],
        )
        for pred in p[: max(1, len(p) // 20)]
    ]
    predictions["P_minus_Standard_bridge_proxy"] = [dict(pred, condition="P_minus_Standard_bridge_proxy") for pred in p]
    return predictions


def key(edge):
    return (edge["source_id"], edge["predicate"], edge["target_id"])


def prf(preds, refs):
    pred_keys = {key(p) for p in preds}
    ref_keys = {key(r) for r in refs}
    tp = len(pred_keys & ref_keys)
    fp = len(pred_keys - ref_keys)
    fn = len(ref_keys - pred_keys)
    precision = tp / max(1, tp + fp)
    recall = tp / max(1, tp + fn)
    f1 = 2 * precision * recall / max(1e-9, precision + recall)
    return {
        "true_positive": tp,
        "false_positive": fp,
        "false_negative": fn,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
    }


def span_iou(pred_span, ref_span):
    if not pred_span or not ref_span:
        return 0.0
    if pred_span.get("chunk_id") != ref_span.get("chunk_id"):
        return 0.0
    p0, p1 = pred_span.get("start_char", 0), pred_span.get("end_char", 0)
    r0, r1 = ref_span.get("start_char", 0), ref_span.get("end_char", 0)
    inter = max(0, min(p1, r1) - max(p0, r0))
    union = max(p1, r1) - min(p0, r0)
    return inter / max(1, union)


def evidence_metrics(preds, refs):
    ref_by_key = {key(r): r for r in refs}
    grounded = 0
    exact = 0
    ious = []
    for pred in preds:
        spans = pred.get("evidence_spans", [])
        if spans:
            grounded += 1
        ref = ref_by_key.get(key(pred))
        if not ref:
            continue
        pred_ids = set(pred.get("evidence_anchor_ids", []))
        ref_ids = set(ref.get("evidence_anchor_ids", []))
        if pred_ids and pred_ids == ref_ids:
            exact += 1
        best = 0.0
        for ps in spans:
            for rs in ref.get("evidence_spans", []):
                best = max(best, span_iou(ps, rs))
        if spans:
            ious.append(best)
    return {
        "edge_grounding_rate": round(grounded / max(1, len(preds)), 4),
        "evidence_exact_match": round(exact / max(1, len(preds)), 4),
        "evidence_iou_mean": round(statistics.mean(ious), 4) if ious else 0.0,
        "unsupported_edge_rate": round(1 - grounded / max(1, len(preds)), 4),
    }


def ontology_metrics(preds):
    violations = 0
    for pred in preds:
        violated = False
        if pred["predicate"] not in DOMAIN_RANGE:
            violated = True
        else:
            allowed_subject, allowed_object = DOMAIN_RANGE[pred["predicate"]]
            if allowed_subject and pred.get("source_type") not in allowed_subject:
                violated = True
            if allowed_object and pred.get("target_type") not in allowed_object:
                violated = True
        if violated:
            violations += 1
    return {
        "ontology_violation_count": violations,
        "ontology_conformance": round(max(0.0, 1 - violations / max(1, len(preds))), 4),
    }


def has_cycle(edges):
    graph = defaultdict(list)
    nodes = set()
    for edge in edges:
        if edge["predicate"] != "PRECEDES":
            continue
        graph[edge["source_id"]].append(edge["target_id"])
        nodes.add(edge["source_id"])
        nodes.add(edge["target_id"])
    visiting = set()
    visited = set()

    def dfs(node):
        if node in visiting:
            return True
        if node in visited:
            return False
        visiting.add(node)
        for nxt in graph[node]:
            if dfs(nxt):
                return True
        visiting.remove(node)
        visited.add(node)
        return False

    return any(dfs(node) for node in nodes)


def procedural_metrics(preds):
    procedural = [p for p in preds if p["predicate"] in {"HAS_STEP", "PRECEDES", "HAS_DECISION_GATEWAY", "HAS_GUARD_CONDITION", "FEEDS_INTO", "USED_AS_INPUT_FOR"}]
    gateway_edges = [p for p in preds if p["predicate"] == "HAS_DECISION_GATEWAY"]
    guard_edges = [p for p in preds if p["predicate"] == "HAS_GUARD_CONDITION"]
    flow_edges = [p for p in preds if p["predicate"] in {"FEEDS_INTO", "USED_AS_INPUT_FOR"}]
    cycle = has_cycle(procedural)
    flow_violations = sum(1 for p in flow_edges if p.get("source_type") != "Artifact")
    return {
        "procedural_edge_count": len(procedural),
        "precedence_cycle_count": 1 if cycle else 0,
        "gateway_without_guard_or_evidence": 0 if guard_edges or not gateway_edges else len(gateway_edges),
        "artifact_flow_type_violation_count": flow_violations,
        "procedural_consistency": round(1 - (int(cycle) + flow_violations) / max(1, len(procedural)), 4),
    }


def cq_metrics(preds, mapping):
    pred_counts = Counter(p["predicate"] for p in preds)
    rows = []
    for cq_id, question, predicates in CQS:
        support = sum(pred_counts[p] for p in predicates)
        if cq_id == "CQ10":
            support = sum(1 for p in preds if p.get("evidence_anchor_ids"))
        if cq_id == "CQ11":
            support = len(mapping["ncs"])
        if cq_id == "CQ12":
            support = len(mapping["pcf"])
        score = 5 if support > 0 else 0
        rows.append({"cq_id": cq_id, "question": question, "support_count": support, "score": score})
    return rows


def evaluate_predictions(predictions, refs, mapping):
    rows = []
    cq_rows = []
    for condition, preds in predictions.items():
        base = {"condition": condition, "pred_edges": len(preds), "reference_edges": len(refs)}
        base.update(prf(preds, refs))
        base.update(evidence_metrics(preds, refs))
        base.update(ontology_metrics(preds))
        base.update(procedural_metrics(preds))
        rows.append(base)
        for cq in cq_metrics(preds, mapping):
            cq_rows.append({"condition": condition, **cq})
    return rows, cq_rows


def build_active_review_queue(preds, refs):
    ref_keys = {key(r) for r in refs}
    degree = Counter()
    for pred in preds:
        degree[pred["source_id"]] += 1
        degree[pred["target_id"]] += 1
    max_degree = max(degree.values()) if degree else 1
    queue = []
    for pred in preds:
        uncertainty = 1 - pred.get("confidence", 0.0)
        evidence_risk = 0.0 if pred.get("evidence_anchor_ids") else 1.0
        centrality = max(degree[pred["source_id"]], degree[pred["target_id"]]) / max_degree
        conflict = 0.8 if any(term in pred.get("target_label", "") + pred.get("source_label", "") for term in ["위험", "리스크", "No Bid", "불리"]) else 0.0
        mapping_disagreement = 0.0 if key(pred) in ref_keys else 0.8
        priority = 0.30 * uncertainty + 0.20 * evidence_risk + 0.20 * centrality + 0.15 * mapping_disagreement + 0.15 * conflict
        queue.append(
            {
                "review_item_id": "ARQ-" + sha1_text(pred["prediction_id"], 16),
                "prediction_id": pred["prediction_id"],
                "condition": pred["condition"],
                "subject": pred["source_label"],
                "predicate": pred["predicate"],
                "object": pred["target_label"],
                "confidence": pred["confidence"],
                "extraction_uncertainty": round(uncertainty, 4),
                "evidence_anchor_risk": round(evidence_risk, 4),
                "graph_centrality": round(centrality, 4),
                "mapping_disagreement": round(mapping_disagreement, 4),
                "conflict_score": round(conflict, 4),
                "review_priority": round(priority, 6),
                "reviewer_decision": "",
                "comment": "",
            }
        )
    return sorted(queue, key=lambda r: r["review_priority"], reverse=True)


def mapping_report_rows(kg, selected_task_ids):
    rows = []
    for standard, mappings in [("NCS", kg["ncs_mapping"]), ("PCF", kg["pcf_mapping"])]:
        covered = {m["source_id"] for m in mappings if m["source_id"] in selected_task_ids}
        top5 = [m for m in mappings if m["source_id"] in selected_task_ids and m.get("rank", 99) <= 5]
        rows.append(
            {
                "standard": standard,
                "selected_domain_tasks": len(selected_task_ids),
                "covered_tasks": len(covered),
                "coverage": round(len(covered) / max(1, len(selected_task_ids)), 4),
                "top5_candidate_rows": len(top5),
                "reason_present_rate": round(sum(1 for m in top5 if m.get("reason")) / max(1, len(top5)), 4),
                "expert_accept_rate": "pending_human_review",
                "p_at_5": "pending_human_review",
                "mrr": "pending_human_review",
            }
        )
    return rows


def mapping_arm_score(row, arm):
    breakdown = row.get("score_breakdown") or {}
    name = float(breakdown.get("name_similarity") or 0.0)
    definition = float(breakdown.get("definition_description_similarity") or 0.0)
    action = float(breakdown.get("action_verb_similarity") or 0.0)
    hierarchy = float(breakdown.get("hierarchy_context_similarity") or 0.0)
    level = float(breakdown.get("level_compatibility") or 0.0)
    domain_penalty = float(breakdown.get("domain_gap_penalty") or 0.0)
    if arm == "text_only_task_description":
        return 0.55 * name + 0.45 * definition
    if arm == "task_frame_only":
        return 0.35 * name + 0.30 * definition + 0.25 * action + 0.10 * level
    if arm == "flat_triples":
        return 0.25 * name + 0.25 * definition + 0.25 * action + 0.15 * hierarchy + 0.10 * level
    if arm == "procedural_kg_with_evidence":
        return float(row.get("score") or 0.0)
    return float(row.get("score") or 0.0)


def mapping_downstream_arm_rows(kg, selected_task_ids):
    arms = [
        ("text_only_task_description", "task label/definition lexical signals only"),
        ("task_frame_only", "task frame slots without graph-neighborhood flow"),
        ("flat_triples", "typed triples without procedural/evidence-prioritized scoring"),
        ("procedural_kg_with_evidence", "current full candidate score with KG/evidence bridge features"),
    ]
    rows = []
    for standard, mappings in [("NCS", kg["ncs_mapping"]), ("PCF", kg["pcf_mapping"])]:
        grouped = defaultdict(list)
        for row in mappings:
            if row.get("source_id") in selected_task_ids and int(row.get("rank") or 99) <= 5:
                grouped[row["source_id"]].append(row)
        full_top1 = {}
        for source_id, candidates in grouped.items():
            ranked = sorted(candidates, key=lambda r: (int(r.get("rank") or 99), -float(r.get("score") or 0.0)))
            if ranked:
                full_top1[source_id] = ranked[0].get("mapping_id")
        for arm, description in arms:
            top1_matches = 0
            top1_scores = []
            margins = []
            scored_candidate_rows = 0
            for source_id, candidates in grouped.items():
                scored = sorted(
                    [(mapping_arm_score(row, arm), row) for row in candidates],
                    key=lambda item: item[0],
                    reverse=True,
                )
                scored_candidate_rows += len(scored)
                if not scored:
                    continue
                top1_scores.append(scored[0][0])
                if len(scored) > 1:
                    margins.append(scored[0][0] - scored[1][0])
                if scored[0][1].get("mapping_id") == full_top1.get(source_id):
                    top1_matches += 1
            group_count = len(grouped)
            rows.append(
                {
                    "standard": standard,
                    "representation_arm": arm,
                    "description": description,
                    "source_task_groups": group_count,
                    "candidate_universe": "generated_top5_only",
                    "candidate_rows": scored_candidate_rows,
                    "top1_agreement_with_full_score": round(top1_matches / max(1, group_count), 4),
                    "mean_top1_proxy_score": round(sum(top1_scores) / max(1, len(top1_scores)), 6),
                    "mean_top1_margin": round(sum(margins) / max(1, len(margins)), 6),
                    "hit_at_5": "pending_expert_review",
                    "precision_at_5": "pending_expert_review",
                    "mrr": "pending_expert_review",
                    "claim_status": "diagnostic_rerank_only_not_expert_reviewed",
                }
            )
    return rows


def mapping_downstream_arm_detail_rows(kg, selected_task_ids):
    arms = [
        ("text_only_task_description", "task label/definition lexical signals only"),
        ("task_frame_only", "task frame slots without graph-neighborhood flow"),
        ("flat_triples", "typed triples without procedural/evidence-prioritized scoring"),
        ("procedural_kg_with_evidence", "current full candidate score with KG/evidence bridge features"),
    ]
    rows = []
    for standard, mappings in [("NCS", kg["ncs_mapping"]), ("PCF", kg["pcf_mapping"])]:
        grouped = defaultdict(list)
        for row in mappings:
            if row.get("source_id") in selected_task_ids and int(row.get("rank") or 99) <= 5:
                grouped[row["source_id"]].append(row)
        for source_id, candidates in sorted(grouped.items()):
            full_ranked = sorted(candidates, key=lambda r: (int(r.get("rank") or 99), -float(r.get("score") or 0.0)))
            full_top1 = full_ranked[0] if full_ranked else {}
            for arm, description in arms:
                scored = sorted(
                    [(mapping_arm_score(row, arm), row) for row in candidates],
                    key=lambda item: (-item[0], int(item[1].get("rank") or 99), item[1].get("mapping_id") or ""),
                )
                if not scored:
                    continue
                top_score, top_row = scored[0]
                second_score = scored[1][0] if len(scored) > 1 else None
                rows.append(
                    {
                        "standard": standard,
                        "source_id": source_id,
                        "source_label": top_row.get("source_label", ""),
                        "representation_arm": arm,
                        "description": description,
                        "candidate_universe": "generated_top5_only",
                        "candidate_count": len(scored),
                        "arm_top1_mapping_id": top_row.get("mapping_id", ""),
                        "arm_top1_target_id": top_row.get("target_id", ""),
                        "arm_top1_target_label": top_row.get("target_label", ""),
                        "arm_top1_original_rank": top_row.get("rank", ""),
                        "arm_top1_original_score": top_row.get("score", ""),
                        "arm_top1_proxy_score": round(top_score, 6),
                        "arm_top1_margin": round(top_score - second_score, 6) if second_score is not None else "",
                        "full_score_top1_mapping_id": full_top1.get("mapping_id", ""),
                        "full_score_top1_target_id": full_top1.get("target_id", ""),
                        "full_score_top1_target_label": full_top1.get("target_label", ""),
                        "top1_agrees_with_full_score": top_row.get("mapping_id") == full_top1.get("mapping_id"),
                        "hit_at_5": "pending_expert_review",
                        "precision_at_5": "pending_expert_review",
                        "mrr": "pending_expert_review",
                        "claim_status": "diagnostic_rerank_only_not_expert_reviewed",
                    }
                )
    return rows


def summarize_mapping_arm_details(detail_rows):
    rows = list(detail_rows)
    agreement_by_arm = defaultdict(lambda: {"groups": 0, "agreements": 0})
    for row in rows:
        key = (row["standard"], row["representation_arm"])
        agreement_by_arm[key]["groups"] += 1
        if row.get("top1_agrees_with_full_score") is True:
            agreement_by_arm[key]["agreements"] += 1
    return {
        "claim_status": "diagnostic_rerank_only_not_expert_reviewed",
        "candidate_universe": "generated_top5_only",
        "detail_rows": len(rows),
        "source_task_groups": len({(row["standard"], row["source_id"]) for row in rows}),
        "representation_arms": sorted({row["representation_arm"] for row in rows}),
        "standards": sorted({row["standard"] for row in rows}),
        "top1_agreement_by_standard_arm": [
            {
                "standard": standard,
                "representation_arm": arm,
                "source_task_groups": values["groups"],
                "top1_agreement_with_full_score": round(values["agreements"] / max(1, values["groups"]), 4),
            }
            for (standard, arm), values in sorted(agreement_by_arm.items())
        ],
    }


def render_mapping_downstream_report(mapping_rows, arm_rows, arm_detail_summary=None):
    lines = [
        "# Mapping Downstream Report",
        "",
        "This report tracks the NCS/PCF downstream task proposed in the EACL revision plan.",
        "Expert-confirmed Hit@K/P@5/MRR remain pending until Top-5 source-task groups are reviewed.",
        "",
        "## Candidate Coverage",
        "",
        "| standard | selected tasks | covered tasks | coverage | Top-5 rows | reason rate | P@5 | MRR |",
        "|---|---:|---:|---:|---:|---:|---|---|",
    ]
    for row in mapping_rows:
        lines.append(
            "| {standard} | {selected_domain_tasks} | {covered_tasks} | {coverage} | {top5_candidate_rows} | {reason_present_rate} | {p_at_5} | {mrr} |".format(
                **row
            )
        )
    lines += [
        "",
        "## Representation-Arm Diagnostic",
        "",
        "The table below reranks the already generated Top-5 candidate universe using representation-specific proxy scores.",
        "It is a scaffold for the downstream comparison, not a paper-claimable mapping result.",
        "",
        "| standard | arm | source groups | candidate rows | Top-1 agreement with full score | mean top1 proxy | mean margin | claim status |",
        "|---|---|---:|---:|---:|---:|---:|---|",
    ]
    for row in arm_rows:
        lines.append(
            "| {standard} | {representation_arm} | {source_task_groups} | {candidate_rows} | {top1_agreement_with_full_score} | {mean_top1_proxy_score} | {mean_top1_margin} | {claim_status} |".format(
                **row
            )
        )
    if arm_detail_summary:
        lines += [
            "",
            "## Per-Task Rerank Trace",
            "",
            "- Detail CSV: `experiments/cape_kg_eacl_20260627/04_evaluation/mapping_downstream_arm_rerank_details.csv`",
            "- Detail JSON summary: `experiments/cape_kg_eacl_20260627/04_evaluation/mapping_downstream_arm_rerank_summary.json`",
            f"- Detail rows: {arm_detail_summary['detail_rows']}",
            f"- Standards: {', '.join(arm_detail_summary['standards'])}",
            f"- Arms: {', '.join(arm_detail_summary['representation_arms'])}",
            "- Each detail row records the source task, representation arm, selected Top-1 candidate, original full-score Top-1 candidate, proxy score, and margin.",
        ]
    lines += [
        "",
        "## Claim Scope",
        "",
        "- `generated_top5_only` means this diagnostic reranks only the current generated candidate rows.",
        "- It does not regenerate a full candidate universe for each representation arm.",
        "- It does not replace expert review; P@K, P@5, MRR, and accept-rate remain pending.",
        "- After expert review, the same source-task groups can be scored as text-only, task-frame, flat-triple, and procedural-KG variants.",
    ]
    return "\n".join(lines) + "\n"


def render_evidence_grounding_report(metric_rows):
    lines = [
        "# Evidence Grounding Report",
        "",
        "Claim status: `silver_proxy_evidence_grounding_diagnostic_not_human_gold`",
        "",
        "This report summarizes evidence-grounding behavior for the silver/proxy scaffold.",
        "The EM, IoU, and unsupported-edge values below are not paper-claimable human-gold evidence metrics.",
        "Use adjudicated human-gold spans and `human_gold_span_iou_metrics.json` for final evidence exactness claims.",
        "",
        "## Summary Table",
        "",
        "| condition | evidence EM | evidence IoU | unsupported edge rate | claim status |",
        "|---|---:|---:|---:|---|",
    ]
    for row in metric_rows:
        lines.append(
            "| {condition} | {em} | {iou} | {unsupported} | silver/proxy only |".format(
                condition=row["condition"],
                em=row["evidence_exact_match"],
                iou=row["evidence_iou_mean"],
                unsupported=row["unsupported_edge_rate"],
            )
        )
    lines += [
        "",
        "## Interpretation",
        "",
        "- `P_minus_Evidence_proxy` is expected to expose the evidence-removal ablation behavior.",
        "- Conditions with high proxy evidence scores are showing attachment to the silver scaffold, not adjudicated correctness.",
        "- Final paper claims require completed human-gold annotation, adjudication, and component/span IoU scoring.",
    ]
    return "\n".join(lines) + "\n"


def write_prompt_templates(out_dir):
    prompts = {
        "B0_plain_llm_triple_extraction.txt": "Extract subject-predicate-object triples from the chunk. Return JSON only.",
        "B1_predicate_constrained_llm.txt": "Extract triples using only the allowed predicates. Return JSON only with evidence sentence ids.",
        "B2_current_project_baseline.txt": "Extract Task Frames, then triples, then post-process into the Layer2 schema.",
        "B3_edc_style_baseline.txt": "Extract, define, and canonicalize open-schema KG items, then emit CAPE-compatible nodes and edges for scoring.",
        "B4_taxonomy_rag_baseline.txt": "Retrieve NCS/PCF/task taxonomy snippets, then extract schema-constrained triples with evidence.",
        "B5_procedural_prompt_baseline.txt": "Extract actions, actors, gateways, guard conditions, artifact flows, and temporal/logical dependencies.",
        "B6_sac_kg_verifier_pruner_baseline.txt": "Use existing generator candidates, then apply schema/evidence verification and pruning in the style of SAC-KG. This is a deterministic approximation, not a full SAC-KG reproduction.",
        "P_cape_kg.txt": "Use CQ-linked schema retrieval, procedural frame extraction, evidence-span constrained relation extraction, span verification, ontology validation, procedural consistency checks, and active review scoring.",
        "P_minus_Schema_retrieval.txt": "Run CAPE-KG without chunk-specific schema/taxonomy retrieval; keep CQ, evidence grounding, procedural schema, validation, and mapping output shape.",
    }
    for name, text in prompts.items():
        write_text(Path(out_dir) / name, text + "\n")


def write_schema(out_dir):
    schema = {
        "method": "CAPE-KG",
        "node_types": NODE_TYPES,
        "edge_types": EDGE_TYPES,
        "domain_range": {
            pred: {
                "subject_types": sorted(list(subj)) if subj else ["Any"],
                "object_types": sorted(list(obj)) if obj else ["Any"],
            }
            for pred, (subj, obj) in DOMAIN_RANGE.items()
        },
        "evidence_span_required": True,
    }
    cqs = [{"cq_id": cid, "question": question, "target_predicates": predicates} for cid, question, predicates in CQS]
    shapes = """@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix cape: <https://example.org/cape-kg#> .

cape:EvidenceGroundedEdgeShape a sh:NodeShape ;
  sh:message "Every accepted CAPE-KG edge must carry at least one evidence anchor." .

cape:ProducesShape a sh:NodeShape ;
  sh:message "PRODUCES must connect DomainTask/ProcedureStep to Artifact." .
"""
    write_json(Path(out_dir) / "cape_schema.json", schema)
    write_json(Path(out_dir) / "competency_questions.json", cqs)
    write_text(Path(out_dir) / "cape_shapes.shacl.ttl", shapes)


def write_annotation_guideline(path):
    path = Path(path)
    if path.exists():
        existing = path.read_text(encoding="utf-8")
        if "## 9. Quality checklist" in existing and "## 11. Paper claim 주의사항" in existing:
            return
    text = """# CAPE-KG Annotation Guideline v1

## Unit

Annotate one `chunk_id` at a time. Mark every evidence-supported procedural
knowledge item that is relevant to bid/proposal work.

## Entity Types

- DomainTask: coarse work activity, e.g. 수주영업, 제안서 기획
- ProcedureStep: concrete step inside a task
- DecisionGateway: decision point such as Bid/No Bid
- GuardCondition: condition or criterion for a decision or branch
- Artifact: document, plan, checklist, proposal, input/output material
- Role: person/team/actor responsible for an activity
- ReviewCheckpoint: review activity
- Principle/Risk: explicit principle or risk

## Edge Types

Use only the CAPE-KG schema. Every edge must include source/target IDs, type,
and an evidence span. Do not infer missing steps unless the chunk explicitly
supports them.

## Evidence Span

Prefer exact character spans. If OCR noise prevents exact span, use the
sentence anchor and mark `span_quality=sentence_anchor`.

## Labels

Use the Korean surface form when possible and preserve English aliases.
"""
    write_text(path, text)


def find_label_span(text, label):
    text = str(text or "")
    label = str(label or "").strip()
    if not text or not label:
        return None
    idx = text.find(label)
    if idx >= 0:
        return idx, idx + len(label), text[idx: idx + len(label)], "exact_label_match"
    lowered_idx = text.lower().find(label.lower())
    if lowered_idx >= 0:
        return lowered_idx, lowered_idx + len(label), text[lowered_idx: lowered_idx + len(label)], "case_insensitive_label_match"
    return None


def component_span_row(edge, component, label, primary_evidence, span, method, exact):
    if span:
        start, end, span_text, method = span
    elif method == "full_sentence_proxy":
        span_text = primary_evidence.get("text") or ""
        start = 0
        end = len(span_text)
    else:
        start = ""
        end = ""
        span_text = ""
    return {
        "component": component,
        "label": label,
        "predicate": edge.get("predicate"),
        "sentence_id": primary_evidence.get("sentence_id"),
        "page": primary_evidence.get("page"),
        "sentence_span_start": start,
        "sentence_span_end": end,
        "text": span_text,
        "span_method": method,
        "span_exact": bool(exact),
        "claim_status": "automatic_candidate_span_suggestion_not_gold",
    }


def component_evidence_spans(edge, primary_evidence):
    text = primary_evidence.get("text") or ""
    source_label = edge.get("source_label") or ""
    target_label = edge.get("target_label") or ""
    source_span = find_label_span(text, source_label)
    target_span = find_label_span(text, target_label)
    return [
        component_span_row(edge, "subject", source_label, primary_evidence, source_span, "label_not_found_in_sentence", bool(source_span)),
        component_span_row(edge, "predicate", edge.get("predicate") or "", primary_evidence, None, "full_sentence_proxy", False),
        component_span_row(edge, "object", target_label, primary_evidence, target_span, "label_not_found_in_sentence", bool(target_span)),
    ]


def enrich_candidate_component_spans(edge):
    spans = edge.get("evidence_spans") or []
    first_span = spans[0] if spans else {}
    primary_evidence = {
        "sentence_id": first_span.get("sentence_id"),
        "page": first_span.get("page"),
        "start_char": first_span.get("start_char"),
        "end_char": first_span.get("end_char"),
        "text": first_span.get("text"),
    }
    return {**edge, "component_evidence_spans": component_evidence_spans(edge, primary_evidence)}


def build_annotation_templates(chunks, refs):
    refs_by_chunk = defaultdict(list)
    for ref in refs:
        for span in ref.get("evidence_spans", []):
            if span.get("chunk_id"):
                refs_by_chunk[span["chunk_id"]].append(ref)
    rows = []
    csv_rows = []
    for chunk in chunks:
        candidates = refs_by_chunk.get(chunk["chunk_id"], [])
        row = {
            "chunk_id": chunk["chunk_id"],
            "page_start": chunk.get("page_start"),
            "page_end": chunk.get("page_end"),
            "chapter_id": chunk.get("chapter_id"),
            "section_id": chunk.get("section_id"),
            "chunk_text": chunk.get("text"),
            "annotation_status": "pending_human_annotation",
            "silver_candidate_edge_count": len(candidates),
            "silver_candidate_edges": [enrich_candidate_component_spans(edge) for edge in candidates[:50]],
            "gold_nodes": [],
            "gold_edges": [],
            "annotator_id": "",
            "adjudication_notes": "",
        }
        rows.append(row)
        csv_rows.append(
            {
                "chunk_id": row["chunk_id"],
                "page_start": row["page_start"],
                "page_end": row["page_end"],
                "silver_candidate_edge_count": len(candidates),
                "annotator_id": "",
                "annotation_status": "pending_human_annotation",
                "comment": "",
            }
        )
    return rows, csv_rows


def summarize_llm_run(raw_path, valid_path, report_path, run_label):
    if not raw_path.exists() or not valid_path.exists():
        return None
    raw_rows = read_jsonl(raw_path)
    valid_rows = read_jsonl(valid_path)
    return {
        "run_label": run_label,
        "raw_file": str(raw_path),
        "valid_file": str(valid_path),
        "report_file": str(report_path) if report_path.exists() else None,
        "raw_chunk_rows": len(raw_rows),
        "valid_chunk_rows": len(valid_rows),
        "valid_task_frames": sum(len(r.get("create_task_frame", [])) for r in valid_rows),
        "valid_procedural_relations": sum(len(r.get("add_procedural_relation", [])) for r in valid_rows),
        "rejected_candidates": sum(len(r.get("reject_candidate", [])) for r in valid_rows),
        "raw_rows_with_parse_or_generation_errors": sum(1 for r in raw_rows if r.get("parse_error") or r.get("error")),
    }


def collect_additional_llm_runs(exp_dir):
    runs = []
    for report_path in sorted(exp_dir.glob("47_*_quality_report.md")):
        prefix = strip_prefix_suffix(report_path.name, "47_", "_quality_report.md")
        if prefix == "llm_tool_extractions":
            continue
        raw_path = exp_dir / f"45_{prefix}_raw.jsonl"
        valid_path = exp_dir / f"46_{prefix}_valid.jsonl"
        summary = summarize_llm_run(raw_path, valid_path, report_path, prefix)
        if summary:
            runs.append(summary)
    return runs


def summarize_condition_baseline_run(raw_path, valid_path, report_path, run_label):
    if not raw_path.exists() or not valid_path.exists():
        return None
    raw_rows = read_jsonl(raw_path)
    valid_rows = read_jsonl(valid_path)
    by_condition = defaultdict(lambda: {
        "raw_rows": 0,
        "raw_rows_with_parse_or_generation_errors": 0,
        "partial_json_repaired_rows": 0,
        "valid_triples": 0,
        "valid_nodes": 0,
        "valid_edges": 0,
        "valid_mappings": 0,
    })
    for row in raw_rows:
        condition = row.get("condition", "unknown")
        by_condition[condition]["raw_rows"] += 1
        if row.get("parse_error") or row.get("error"):
            by_condition[condition]["raw_rows_with_parse_or_generation_errors"] += 1
        if row.get("partial_json_repaired"):
            by_condition[condition]["partial_json_repaired_rows"] += 1
    for row in valid_rows:
        condition = row.get("condition", "unknown")
        by_condition[condition]["valid_triples"] += len(row.get("triples", []))
        by_condition[condition]["valid_nodes"] += len(row.get("nodes", []))
        by_condition[condition]["valid_edges"] += len(row.get("edges", []))
        by_condition[condition]["valid_mappings"] += len(row.get("mappings", []))
    return {
        "run_label": run_label,
        "raw_file": str(raw_path),
        "valid_file": str(valid_path),
        "report_file": str(report_path) if report_path.exists() else None,
        "raw_rows": len(raw_rows),
        "valid_rows": len(valid_rows),
        "conditions": dict(by_condition),
    }


def collect_condition_baseline_runs(exp_dir):
    runs = []
    for report_path in sorted(exp_dir.glob("50_*_quality_report.md")):
        prefix = strip_prefix_suffix(report_path.name, "50_", "_quality_report.md")
        raw_path = exp_dir / f"48_{prefix}_raw.jsonl"
        valid_path = exp_dir / f"49_{prefix}_valid.jsonl"
        summary = summarize_condition_baseline_run(raw_path, valid_path, report_path, prefix)
        if summary:
            runs.append(summary)
    return runs


def collect_public_eval_runs(exp_dir):
    runs = []
    public_dir = exp_dir / "08_public_benchmarks"
    for summary_path in sorted(public_dir.glob("*_summary.json")):
        try:
            summary = read_json(summary_path)
        except Exception:
            continue
        if summary.get("is_shard"):
            continue
        if "paged_items" not in summary and "text2kg_items" not in summary:
            continue
        summary["summary_file"] = str(summary_path)
        runs.append(summary)
    return runs


def collect_public_synthetic_examples(exp_dir):
    output_dir = Path(exp_dir) / "06_release/public_synthetic_examples"
    summary_path = output_dir / "synthetic_evaluation_summary.json"
    readme_path = output_dir / "README.md"
    if not summary_path.exists():
        return None
    payload = read_json(summary_path)
    payload["summary_file"] = str(summary_path)
    if readme_path.exists():
        payload["readme_file"] = str(readme_path)
    return payload


def collect_human_annotation_package(exp_dir):
    package_dir = Path(exp_dir) / "01_data/gold_annotation"
    manifest_path = package_dir / "annotation_package_manifest.json"
    if not manifest_path.exists():
        return None
    manifest = read_json(manifest_path)
    iaa_reports = []
    for summary_path in sorted(package_dir.glob("iaa*/iaa_summary.json")):
        try:
            summary = read_json(summary_path)
        except Exception:
            continue
        summary["summary_file"] = str(summary_path)
        report_path = summary_path.with_name("iaa_report.md")
        if report_path.exists():
            summary["report_file"] = str(report_path)
        iaa_reports.append(summary)
    manifest["iaa_reports"] = iaa_reports
    adjudication_drafts = []
    for summary_path in sorted(package_dir.glob("*/adjudication_draft_summary.json")):
        try:
            summary = read_json(summary_path)
        except Exception:
            continue
        summary["summary_file"] = str(summary_path)
        report_path = summary_path.with_name("adjudication_draft_report.md")
        output_path = summary_path.with_name("adjudication_draft.jsonl")
        if report_path.exists():
            summary["report_file"] = str(report_path)
        if output_path.exists():
            summary["output_file"] = str(output_path)
        adjudication_drafts.append(summary)
    manifest["adjudication_drafts"] = adjudication_drafts
    return manifest


def collect_annotation_progress(exp_dir):
    release_dir = Path(exp_dir) / "06_release"
    summary_path = release_dir / "annotation_progress_summary.json"
    report_path = release_dir / "annotation_progress_report.md"
    batch_summary_path = release_dir / "annotation_batch_assignment_summary.json"
    batch_report_path = release_dir / "annotation_batch_assignment_report.md"
    if not summary_path.exists():
        return None
    payload = read_json(summary_path)
    payload["summary_file"] = str(summary_path)
    if report_path.exists():
        payload["report_file"] = str(report_path)
    if batch_summary_path.exists():
        payload["batch_assignment"] = read_json(batch_summary_path)
        payload["batch_assignment_summary_file"] = str(batch_summary_path)
    if batch_report_path.exists():
        payload["batch_assignment_report_file"] = str(batch_report_path)
    return payload


def collect_annotation_qc(exp_dir):
    release_dir = Path(exp_dir) / "06_release"
    review_dir = Path(exp_dir) / "05_review"
    summary_path = release_dir / "annotation_qc_summary.json"
    report_path = release_dir / "annotation_qc_report.md"
    issue_csv = review_dir / "annotation_qc_issues.csv"
    gate_worklist_csv = review_dir / "annotation_completion_gate_worklist.csv"
    if not summary_path.exists():
        return None
    payload = read_json(summary_path)
    payload["summary_file"] = str(summary_path)
    if report_path.exists():
        payload["report_file"] = str(report_path)
    if issue_csv.exists():
        payload["issue_csv"] = str(issue_csv)
    if gate_worklist_csv.exists():
        payload["gate_worklist_csv"] = str(gate_worklist_csv)
    return payload


def collect_human_gate_action_plan(exp_dir):
    release_dir = Path(exp_dir) / "06_release"
    review_dir = Path(exp_dir) / "05_review"
    plan_path = release_dir / "human_gate_action_plan.json"
    report_path = release_dir / "human_gate_action_plan.md"
    returns_path = review_dir / "human_gate_required_returns.csv"
    if not plan_path.exists():
        return None
    payload = read_json(plan_path)
    payload["plan_file"] = str(plan_path)
    if report_path.exists():
        payload["report_file"] = str(report_path)
    if returns_path.exists():
        payload["required_returns_csv"] = str(returns_path)
    return payload


def collect_actual_llm_silver_eval(exp_dir):
    eval_path = Path(exp_dir) / "04_evaluation/actual_llm_silver_metrics.json"
    report_path = Path(exp_dir) / "04_evaluation/actual_llm_silver_evaluation_report.md"
    if not eval_path.exists():
        return None
    payload = read_json(eval_path)
    payload["metrics_file"] = str(eval_path)
    if report_path.exists():
        payload["report_file"] = str(report_path)
    return payload


def core_condition_rows_from_metric_file(path, model_label):
    path = Path(path)
    payload = read_json(path) if path.exists() else {}
    by_condition = {row.get("condition"): row for row in payload.get("metrics", [])}
    rows = []
    for condition in ["B0_plain_llm", "B1_predicate_constrained", "B2_current_project", "P_cape_kg_actual"]:
        row = by_condition.get(condition)
        if not row:
            continue
        rows.append({
            "model": model_label,
            "condition": condition,
            "rows": row.get("rows"),
            "edge_exact_f1": row.get("edge_exact_f1"),
            "predicate_f1": row.get("predicate_f1"),
            "node_label_f1": row.get("node_label_f1"),
            "evidence_f1": row.get("evidence_f1"),
            "parse_or_generation_error_rows": row.get("parse_or_generation_error_rows"),
            "partial_json_repaired_rows": row.get("partial_json_repaired_rows"),
            "claim_status": row.get("claim_status") or payload.get("claim_status"),
        })
    return rows


def collect_model_scaling_silver_eval(exp_dir):
    exp_dir = Path(exp_dir)
    rows = []
    rows.extend(core_condition_rows_from_metric_file(exp_dir / "04_evaluation/actual_llm_silver_metrics.json", "Qwen3-8B"))
    rows.extend(core_condition_rows_from_metric_file(exp_dir / "04_evaluation/qwen3_14b_core_silver_metrics.json", "Qwen3-14B"))
    rows.extend(core_condition_rows_from_metric_file(exp_dir / "04_evaluation/qwen3_32b_awq_core_silver_metrics.json", "Qwen3-32B-AWQ"))
    if not rows:
        return None
    return {
        "claim_status": "silver_proxy_not_human_gold",
        "rows": rows,
        "source_files": [
            str(exp_dir / "04_evaluation/actual_llm_silver_metrics.json"),
            str(exp_dir / "04_evaluation/qwen3_14b_core_silver_metrics.json"),
            str(exp_dir / "04_evaluation/qwen3_32b_awq_core_silver_metrics.json"),
        ],
    }


def collect_active_review_efficiency(exp_dir):
    output_dir = Path(exp_dir) / "04_evaluation"
    metrics_path = output_dir / "active_review_efficiency_metrics.json"
    report_path = output_dir / "active_review_efficiency_report.md"
    if not metrics_path.exists():
        return None
    payload = read_json(metrics_path)
    payload["metrics_file"] = str(metrics_path)
    if report_path.exists():
        payload["report_file"] = str(report_path)
    return payload


def collect_statistical_analysis(exp_dir):
    output_dir = Path(exp_dir) / "04_evaluation"
    metrics_path = output_dir / "statistical_analysis_metrics.json"
    report_path = output_dir / "statistical_analysis_report.md"
    if not metrics_path.exists():
        return None
    payload = read_json(metrics_path)
    payload["metrics_file"] = str(metrics_path)
    if report_path.exists():
        payload["report_file"] = str(report_path)
    return payload


def collect_model_selection_plan(exp_dir):
    plan_path = Path(exp_dir) / "06_release/model_selection_and_scaling_plan.md"
    if not plan_path.exists():
        return None
    qwen14_report = Path(exp_dir) / "50_qwen3_14b_core_conditions_120_quality_report.md"
    qwen14_eval = Path(exp_dir) / "04_evaluation/qwen3_14b_core_silver_evaluation_report.md"
    qwen14_metrics = Path(exp_dir) / "04_evaluation/qwen3_14b_core_silver_metrics.json"
    qwen32_awq_report = Path(exp_dir) / "50_qwen3_32b_awq_core_120_quality_report.md"
    qwen32_awq_eval = Path(exp_dir) / "04_evaluation/qwen3_32b_awq_core_silver_evaluation_report.md"
    qwen32_awq_metrics = Path(exp_dir) / "04_evaluation/qwen3_32b_awq_core_silver_metrics.json"
    qwen32_awq_readiness_json = Path(exp_dir) / "06_release/qwen3_32b_awq_readiness.json"
    qwen32_awq_readiness_report = Path(exp_dir) / "06_release/qwen3_32b_awq_readiness.md"
    payload = {"plan_file": str(plan_path)}
    if qwen14_report.exists():
        payload["qwen3_14b_core_report"] = str(qwen14_report)
    if qwen14_eval.exists():
        payload["qwen3_14b_core_silver_report"] = str(qwen14_eval)
    if qwen14_metrics.exists():
        payload["qwen3_14b_core_silver_metrics"] = str(qwen14_metrics)
    if qwen32_awq_report.exists():
        payload["qwen3_32b_awq_core_report"] = str(qwen32_awq_report)
    if qwen32_awq_eval.exists():
        payload["qwen3_32b_awq_core_silver_report"] = str(qwen32_awq_eval)
    if qwen32_awq_metrics.exists():
        payload["qwen3_32b_awq_core_silver_metrics"] = str(qwen32_awq_metrics)
    if qwen32_awq_readiness_json.exists():
        payload["qwen3_32b_awq_readiness"] = read_json(qwen32_awq_readiness_json)
        payload["qwen3_32b_awq_readiness_json"] = str(qwen32_awq_readiness_json)
    if qwen32_awq_readiness_report.exists():
        payload["qwen3_32b_awq_readiness_report"] = str(qwen32_awq_readiness_report)
    return payload


def collect_strict_json_diagnostics(exp_dir):
    release_dir = Path(exp_dir) / "06_release"
    review_dir = Path(exp_dir) / "05_review"
    prompt_dir = Path(exp_dir) / "02_schema/prompts"
    json_path = release_dir / "strict_json_diagnostics.json"
    report_path = release_dir / "strict_json_diagnostics.md"
    priority_path = review_dir / "strict_json_reprompt_priority.csv"
    contract_path = prompt_dir / "strict_json_contract.txt"
    if not json_path.exists():
        return None
    payload = read_json(json_path)
    payload["diagnostics_file"] = str(json_path)
    if report_path.exists():
        payload["report_file"] = str(report_path)
    if priority_path.exists():
        payload["priority_queue_file"] = str(priority_path)
    if contract_path.exists():
        payload["strict_json_contract_prompt_file"] = str(contract_path)
    return payload


def collect_submission_readiness_audit(exp_dir):
    output_dir = Path(exp_dir) / "06_release"
    audit_path = output_dir / "submission_readiness_audit.json"
    report_path = output_dir / "submission_readiness_audit.md"
    if not audit_path.exists():
        return None
    payload = read_json(audit_path)
    payload["audit_file"] = str(audit_path)
    if report_path.exists():
        payload["report_file"] = str(report_path)
    return payload


def collect_method_module_coverage(exp_dir):
    release_dir = Path(exp_dir) / "06_release"
    coverage_path = release_dir / "method_module_coverage.json"
    report_path = release_dir / "method_module_coverage.md"
    if not coverage_path.exists():
        return None
    payload = read_json(coverage_path)
    payload["coverage_file"] = str(coverage_path)
    if report_path.exists():
        payload["report_file"] = str(report_path)
    return payload


def summarize_requirement_evidence(evidence):
    parts = []
    for item in evidence or []:
        if not isinstance(item, dict):
            parts.append(str(item))
            continue
        path = item.get("path")
        if path:
            status = "exists" if item.get("exists") else "missing"
            parts.append(f"`{path}` ({status})")
            continue
        brief = []
        for key, value in item.items():
            if isinstance(value, (dict, list)):
                value_text = json.dumps(value, ensure_ascii=False, sort_keys=True)
                if len(value_text) > 180:
                    value_text = value_text[:177] + "..."
                brief.append(f"{key}={value_text}")
                continue
            brief.append(f"{key}={value}")
        if brief:
            parts.append(", ".join(brief))
    return "<br>".join(parts) if parts else "-"


def build_requirements_matrix(plan_file, readiness_audit=None):
    base_requirements = [
        "100+ chunk annotation subset",
        "B0/B1/B2 baselines",
        "CAPE-KG proposed method",
        "3+ ablations",
        "evidence span evaluation",
        "ontology conformance evaluation",
        "procedural consistency evaluation",
        "CQ answerability evaluation",
        "NCS/PCF mapping downstream evaluation",
        "active review queue",
        "reproducibility package",
    ]
    payload = {
        "source_plan": str(plan_file),
        "method_name": "CAPE-KG",
        "requirements": base_requirements,
        "status": "experiment_generated_with_actual_llm_runs_pending_human_gold_iaa_and_scoring",
    }
    if readiness_audit:
        payload["status"] = readiness_audit.get("claim_status") or payload["status"]
        payload["readiness_audit_file"] = readiness_audit.get("audit_file")
        payload["readiness_audit_report"] = readiness_audit.get("report_file")
        payload["readiness_summary"] = readiness_audit.get("summary") or {}
        payload["traceability_items"] = [
            {
                "id": row.get("id"),
                "category": row.get("category"),
                "requirement": row.get("requirement"),
                "status": row.get("status"),
                "claimable": bool(row.get("claimable")),
                "evidence": row.get("evidence") or [],
                "next_step": row.get("next_step"),
            }
            for row in readiness_audit.get("items", [])
        ]
        payload["blocking_items"] = readiness_audit.get("blocking_items") or []
    return payload


def render_requirements_matrix(payload):
    lines = [
        "# Requirements Matrix",
        "",
        f"Source plan: `{payload['source_plan']}`",
        f"Method: `{payload['method_name']}`",
        f"Status: `{payload['status']}`",
        "",
    ]
    summary = payload.get("readiness_summary") or {}
    if summary:
        lines += [
            "## Readiness Summary",
            "",
            f"- Audited items: {summary.get('items')}",
            f"- Claimable items: {summary.get('claimable_items')}",
            f"- Minimum-accept blocking items: {summary.get('minimum_accept_blocking_items')}",
            f"- Status counts: `{summary.get('status_counts')}`",
            "",
        ]
    traceability_items = payload.get("traceability_items") or []
    if traceability_items:
        lines += [
            "## Traceability Table",
            "",
            "| id | category | status | claimable | requirement | evidence | next step |",
            "|---|---|---:|---:|---|---|---|",
        ]
        for row in traceability_items:
            lines.append(
                f"| {row.get('id')} | {row.get('category')} | {row.get('status')} | "
                f"{'yes' if row.get('claimable') else 'no'} | {row.get('requirement')} | "
                f"{summarize_requirement_evidence(row.get('evidence'))} | {row.get('next_step')} |"
            )
        lines += ["", "## Blocking Items", ""]
        blocking = payload.get("blocking_items") or []
        if blocking:
            for row in blocking:
                lines.append(f"- `{row.get('id')}`: {row.get('requirement')} -> {row.get('next_step')}")
        else:
            lines.append("- None.")
    else:
        lines += ["## Requirements", ""]
        lines += [f"- {requirement}" for requirement in payload.get("requirements", [])]
    lines.append("")
    return "\n".join(lines)


def collect_release_bundle(exp_dir):
    release_dir = Path(exp_dir) / "06_release"
    manifest_path = release_dir / "release_bundle_manifest.json"
    checksums_path = release_dir / "release_bundle_checksums.sha256"
    safety_report_path = release_dir / "release_bundle_safety_report.md"
    if not manifest_path.exists():
        return None
    payload = read_json(manifest_path)
    payload["manifest_file"] = str(manifest_path)
    if checksums_path.exists():
        payload["checksums_file"] = str(checksums_path)
    if safety_report_path.exists():
        payload["safety_report_file"] = str(safety_report_path)
    return payload


def collect_human_gold_eval(exp_dir):
    output_dir = Path(exp_dir) / "04_evaluation"
    metrics_path = output_dir / "human_gold_metrics.json"
    validation_path = output_dir / "human_gold_validation_summary.json"
    report_path = output_dir / "human_gold_evaluation_report.md"
    validation_report_path = output_dir / "human_gold_validation_report.md"
    if not metrics_path.exists() and not validation_path.exists():
        return None
    payload = read_json(metrics_path) if metrics_path.exists() else {"validation": read_json(validation_path)}
    payload["metrics_file"] = str(metrics_path) if metrics_path.exists() else None
    payload["validation_file"] = str(validation_path) if validation_path.exists() else None
    if report_path.exists():
        payload["report_file"] = str(report_path)
    if validation_report_path.exists():
        payload["validation_report_file"] = str(validation_report_path)
    return payload


def collect_mapping_expert_review(exp_dir):
    review_dir = Path(exp_dir) / "01_data/mapping_review"
    manifest_path = review_dir / "mapping_review_manifest.json"
    metrics_path = Path(exp_dir) / "04_evaluation/mapping_expert_metrics.json"
    report_path = Path(exp_dir) / "04_evaluation/mapping_expert_evaluation_report.md"
    progress_report_path = Path(exp_dir) / "06_release/mapping_review_progress_report.md"
    progress_summary_path = Path(exp_dir) / "06_release/mapping_review_progress_summary.json"
    priority_queue_path = Path(exp_dir) / "05_review/mapping_review_priority_queue.csv"
    priority_jsonl_path = Path(exp_dir) / "05_review/mapping_review_priority_queue.jsonl"
    next_groups_path = Path(exp_dir) / "05_review/mapping_review_next_20_groups.csv"
    next_rows_path = Path(exp_dir) / "05_review/mapping_review_next_60_rows.csv"
    payload = {}
    if manifest_path.exists():
        payload["review_manifest"] = read_json(manifest_path)
        payload["manifest_file"] = str(manifest_path)
    if metrics_path.exists():
        payload["evaluation"] = read_json(metrics_path)
        payload["metrics_file"] = str(metrics_path)
    if report_path.exists():
        payload["report_file"] = str(report_path)
    if progress_report_path.exists():
        payload["progress_report_file"] = str(progress_report_path)
    if progress_summary_path.exists():
        payload["progress_summary"] = read_json(progress_summary_path)
        payload["progress_summary_file"] = str(progress_summary_path)
    if priority_queue_path.exists():
        payload["priority_queue_file"] = str(priority_queue_path)
    if priority_jsonl_path.exists():
        payload["priority_queue_jsonl_file"] = str(priority_jsonl_path)
    if next_groups_path.exists():
        payload["next_groups_file"] = str(next_groups_path)
    if next_rows_path.exists():
        payload["next_rows_file"] = str(next_rows_path)
    manifest = payload.get("review_manifest") or {}
    if manifest.get("mapping_review_workbench"):
        payload["workbench_file"] = manifest.get("mapping_review_workbench")
    return payload or None


def fmt_metric(value, digits=4):
    if value is None or value == "":
        return ""
    try:
        return f"{float(value):.{digits}f}"
    except (TypeError, ValueError):
        return str(value)


def int_metric(value):
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def condition_row_map(rows):
    return {row.get("condition"): row for row in rows if row.get("condition")}


def build_error_analysis_report(
    exp_dir,
    metric_rows,
    actual_llm_silver_eval,
    model_scaling_silver_eval,
    strict_json_diagnostics,
    human_gold_eval,
    mapping_expert_review,
    active_review_efficiency,
    statistical_analysis,
):
    exp_dir = Path(exp_dir)
    generated_at = datetime.now(timezone.utc).isoformat()
    proxy_by_condition = condition_row_map(metric_rows)
    actual_rows = (actual_llm_silver_eval or {}).get("metrics", [])
    actual_by_condition = condition_row_map(actual_rows)
    strict_evidence_raw = (strict_json_diagnostics or {}).get("strict_json_gate_evidence") or {}
    strict_evidence = strict_evidence_raw if isinstance(strict_evidence_raw, dict) else {}
    strict_evidence_note = strict_evidence_raw if isinstance(strict_evidence_raw, str) else ""
    top_strict_conditions = (strict_json_diagnostics or {}).get("top_strict_json_reprompt_conditions") or []
    human_validation = (human_gold_eval or {}).get("validation") or {}
    mapping_eval = (mapping_expert_review or {}).get("evaluation") or {}
    mapping_progress = (mapping_expert_review or {}).get("progress_summary") or {}
    mapping_rows = mapping_eval.get("metrics") or []
    mapping_pending = sum(int_metric(row.get("pending_rows")) for row in mapping_rows)
    mapping_complete_groups = sum(int_metric(row.get("complete_source_groups")) for row in mapping_rows)
    active_error_rate = (active_review_efficiency or {}).get("error_rate")
    statistical_rows = (statistical_analysis or {}).get("bootstrap_rows") or []

    taxonomy = [
        {
            "family": "Missing extraction / coverage loss",
            "observed_signal": "High false-negative counts in proxy rows, e.g. B0_plain_llm_proxy, B4_taxonomy_rag_proxy, B5_procedural_prompt_proxy, and P_minus_CQ_proxy.",
            "affected_conditions": ["B0_plain_llm_proxy", "B4_taxonomy_rag_proxy", "B5_procedural_prompt_proxy", "P_minus_CQ_proxy"],
            "likely_cause": "Prompt-only extraction or removed CQ context misses procedural elements that the silver scaffold contains.",
            "paper_treatment": "Use as error taxonomy and annotation priority signal only until human-gold confirms recall errors.",
            "next_action": "During adjudication, check whether omitted edges are true misses or silver-reference overgeneration.",
        },
        {
            "family": "Spurious extraction / overgeneration",
            "observed_signal": "B0_plain_llm_proxy has large FP count; P_minus_Validator_proxy keeps extra invalid edges.",
            "affected_conditions": ["B0_plain_llm_proxy", "P_minus_Validator_proxy"],
            "likely_cause": "Unconstrained generation and disabled validation allow unsupported or schema-incompatible edges to remain.",
            "paper_treatment": "Report as validator motivation, not as final precision claim.",
            "next_action": "Inspect high-priority FP edges against source evidence in human review.",
        },
        {
            "family": "Ontology / domain-range violation",
            "observed_signal": "Proxy rows show ontology violations for B0/B1 and P_minus_Validator.",
            "affected_conditions": ["B0_plain_llm_proxy", "B1_predicate_constrained_proxy", "P_minus_Validator_proxy"],
            "likely_cause": "Predicate restriction alone does not enforce subject/object type compatibility.",
            "paper_treatment": "Use ontology conformance as a separate structural metric from extraction F1.",
            "next_action": "Keep domain/range validation in the proposed pipeline and rerun conformance on human-gold predictions.",
        },
        {
            "family": "Evidence grounding failure",
            "observed_signal": "P_minus_Evidence_proxy has unsupported_edge_rate=1.0 and zero grounding in the scaffold metrics.",
            "affected_conditions": ["P_minus_Evidence_proxy"],
            "likely_cause": "Removing evidence constraints preserves graph shape but destroys source-text traceability.",
            "paper_treatment": "Treat as direct support for evidence-grounded evaluation design.",
            "next_action": "Ask annotators to verify evidence exactness and evidence sufficiency for accepted edges.",
        },
        {
            "family": "Procedural schema loss",
            "observed_signal": "P_minus_Procedural_schema_proxy drops procedural edge count in the scaffold metrics.",
            "affected_conditions": ["P_minus_Procedural_schema_proxy"],
            "likely_cause": "Generic relation extraction does not preserve task-step-order and artifact-flow structure.",
            "paper_treatment": "Use as procedural KG motivation, not as final ablation conclusion until human-gold scoring.",
            "next_action": "Check PRECEDES, HAS_STEP, PRODUCES, USES_INPUT, and PERFORMED_BY during adjudication.",
        },
        {
            "family": "Strict JSON / parser recovery instability",
            "observed_signal": (
                "Some full conditions exceed the strict JSON warning threshold, but unrepaired recovery remains within the configured gate."
                if strict_evidence
                else f"Strict JSON warning threshold currently passes: {strict_evidence_note or 'no full condition exceeds threshold'}."
            ),
            "affected_conditions": list(top_strict_conditions) or sorted(strict_evidence) or ["none_over_threshold"],
            "likely_cause": "Long prompts and model reasoning text cause non-clean JSON outputs that require conservative partial-JSON recovery.",
            "paper_treatment": "Report as engineering reliability limitation and keep unrepaired-rate gate separate from quality metrics.",
            "next_action": "Prefer strict contract plus no-think decoding for final reruns if time permits.",
        },
        {
            "family": "Standard taxonomy bridge uncertainty",
            "observed_signal": f"Mapping expert review has complete_groups={mapping_complete_groups}, pending_rows={mapping_pending}.",
            "affected_conditions": ["NCS mapping", "PCF mapping"],
            "likely_cause": "Automatic top-k mapping candidates are not equivalent to expert-confirmed standard alignment.",
            "paper_treatment": "Do not claim NCS/PCF P@K, P@5, or MRR until expert review is complete.",
            "next_action": "Complete top-5 review for priority source-task groups and recompute mapping metrics.",
        },
        {
            "family": "Silver/proxy reference mismatch",
            "observed_signal": "Actual LLM silver edge-exact F1 values are low and should not be interpreted as final paper performance.",
            "affected_conditions": sorted(actual_by_condition),
            "likely_cause": "Silver labels were derived from the current KG and may not match human judgments or surface forms.",
            "paper_treatment": "Use silver/proxy results for debugging, prompt comparison, and claim gating only.",
            "next_action": "Replace claim-bearing scores with adjudicated human-gold metrics.",
        },
    ]

    observations = []
    if proxy_by_condition.get("B0_plain_llm_proxy"):
        row = proxy_by_condition["B0_plain_llm_proxy"]
        observations.append(
            f"B0_plain_llm_proxy is a broad recall/precision stress case: FP={row.get('false_positive')}, FN={row.get('false_negative')}, ontology_violations={row.get('ontology_violation_count')}."
        )
    if proxy_by_condition.get("P_minus_Evidence_proxy"):
        row = proxy_by_condition["P_minus_Evidence_proxy"]
        observations.append(
            f"P_minus_Evidence_proxy isolates evidence grounding: unsupported_edge_rate={row.get('unsupported_edge_rate')}, evidence_exact_match={row.get('evidence_exact_match')}."
        )
    if proxy_by_condition.get("P_minus_Validator_proxy"):
        row = proxy_by_condition["P_minus_Validator_proxy"]
        observations.append(
            f"P_minus_Validator_proxy shows the value of validation: FP={row.get('false_positive')} and ontology_violations={row.get('ontology_violation_count')} remain when pruning is removed."
        )
    if proxy_by_condition.get("P_minus_Procedural_schema_proxy"):
        row = proxy_by_condition["P_minus_Procedural_schema_proxy"]
        observations.append(
            f"P_minus_Procedural_schema_proxy has procedural_edge_count={row.get('procedural_edge_count')}, highlighting procedural schema dependence."
        )
    if actual_by_condition.get("P_cape_kg_actual"):
        row = actual_by_condition["P_cape_kg_actual"]
        observations.append(
            f"P_cape_kg_actual actual LLM run is complete for {row.get('rows')} rows, but current scores remain silver/proxy: edge_F1={fmt_metric(row.get('edge_exact_f1'))}, predicate_F1={fmt_metric(row.get('predicate_f1'))}, evidence_F1={fmt_metric(row.get('evidence_f1'))}."
        )
    if strict_evidence:
        observations.append(
            "Strict JSON diagnostics identify high strict-error conditions: "
            + ", ".join(f"{name}={fmt_metric(rate)}" for name, rate in sorted(strict_evidence.items()))
            + "."
        )
    elif strict_evidence_note:
        observations.append(f"Strict JSON diagnostics now pass the configured warning gate: {strict_evidence_note}.")
    if active_error_rate is not None:
        observations.append(
            f"Active-review diagnostics are high-risk by design and silver/proxy only; current candidate error_rate={fmt_metric(active_error_rate)}."
        )
    if statistical_rows:
        observations.append(
            "Paired bootstrap and McNemar diagnostics exist, but all current significance statements are silver/proxy and must be rerun on human-gold labels."
        )

    human_follow_up = [
        "Adjudicate at least 100 chunks and at least 500 node/edge/evidence items.",
        "Compute IAA on paired A/B annotations before adjudication-derived claims.",
        "Recompute node, edge, predicate, evidence, ontology, procedural, and CQ metrics against adjudicated human gold.",
        "Manually categorize false positives and false negatives into the taxonomy families above.",
        "Complete NCS/PCF expert mapping review before reporting Hit@K, P@5, or MRR.",
        "Keep silver/proxy diagnostic tables out of the final claim-bearing main table.",
    ]

    summary = {
        "claim_scope": "silver_proxy_diagnostic_not_human_gold",
        "ready_for_minimum_accept": bool(metric_rows and taxonomy and observations),
        "proxy_condition_count": len(metric_rows),
        "actual_llm_condition_count": len(actual_rows),
        "taxonomy_family_count": len(taxonomy),
        "human_completed_adjudicated_chunks": int_metric(human_validation.get("completed_adjudicated_chunks")),
        "human_gold_item_count_for_readiness": int_metric(human_validation.get("gold_item_count_for_readiness")),
        "mapping_complete_source_groups": mapping_complete_groups,
        "mapping_pending_rows": mapping_pending,
        "strict_json_gate_status": (strict_json_diagnostics or {}).get("strict_json_gate_status"),
        "revalidated_output_recovery_status": (strict_json_diagnostics or {}).get("revalidated_output_recovery_status"),
    }

    payload = {
        "generated_at_utc": generated_at,
        "experiment_dir": str(exp_dir),
        "summary": summary,
        "proxy_scaffold_metrics": metric_rows,
        "actual_llm_silver_metrics": actual_rows,
        "model_scaling_silver_rows": (model_scaling_silver_eval or {}).get("rows", []),
        "error_taxonomy": taxonomy,
        "diagnostic_observations": observations,
        "human_gold_follow_up": human_follow_up,
        "source_files": {
            "proxy_main_results": str(exp_dir / "04_evaluation/main_results.csv"),
            "actual_llm_silver_metrics": (actual_llm_silver_eval or {}).get("metrics_file"),
            "model_scaling_source_files": (model_scaling_silver_eval or {}).get("source_files", []),
            "strict_json_diagnostics": (strict_json_diagnostics or {}).get("diagnostics_file"),
            "active_review_efficiency": (active_review_efficiency or {}).get("metrics_file"),
            "statistical_analysis": (statistical_analysis or {}).get("metrics_file"),
            "mapping_expert_metrics": (mapping_expert_review or {}).get("metrics_file"),
        },
    }

    lines = [
        "# CAPE-KG Error Analysis",
        "",
        f"Generated: {generated_at}",
        f"Experiment: `{exp_dir}`",
        "",
        "## Claim Scope",
        "",
        "This report is a pre-human error analysis. It uses scaffold metrics, actual LLM silver/proxy diagnostics, strict JSON diagnostics, and workflow status. It is not a final paper performance table because adjudicated human-gold labels, IAA, mapping expert review, and NCS-PCF crosswalk expert review are still pending.",
        "",
        "| claim-bearing question | current status | treatment |",
        "|---|---|---|",
        "| Core extraction quality | pending human-gold | Do not claim final F1 yet |",
        "| Evidence exactness | pending human-gold | Use current values as diagnostics only |",
        "| NCS/PCF mapping quality | pending expert review | Do not claim P@K/P@5/MRR yet |",
        "| NCS-PCF crosswalk utility | pending expert review | Do not claim bridge utility or accept-rate yet |",
        "| JSON/output reliability | diagnostic available | Report as engineering limitation and recovery gate |",
        "",
        "## Actual LLM Silver/Proxy Diagnostics",
        "",
        "| condition | rows | pred edges | pred nodes | edge F1 | predicate F1 | node F1 | evidence F1 | parse/repaired rows | claim status |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in actual_rows:
        lines.append(
            "| {condition} | {rows} | {pred_edges} | {pred_nodes} | {edge_f1} | {pred_f1} | {node_f1} | {ev_f1} | {parse_rows}/{repaired_rows} | {claim_status} |".format(
                condition=row.get("condition"),
                rows=row.get("rows"),
                pred_edges=row.get("pred_edges"),
                pred_nodes=row.get("pred_nodes"),
                edge_f1=fmt_metric(row.get("edge_exact_f1")),
                pred_f1=fmt_metric(row.get("predicate_f1")),
                node_f1=fmt_metric(row.get("node_label_f1")),
                ev_f1=fmt_metric(row.get("evidence_f1")),
                parse_rows=row.get("parse_or_generation_error_rows"),
                repaired_rows=row.get("partial_json_repaired_rows"),
                claim_status=row.get("claim_status"),
            )
        )
    lines += [
        "",
        "These rows show actual LLM generation coverage and silver-reference behavior. They must be replaced by human-gold scores for final paper claims.",
        "",
        "## Proxy Scaffold Error Summary",
        "",
        "| condition | TP | FP | FN | precision | recall | F1 | unsupported rate | ontology violations | procedural edges |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in metric_rows:
        lines.append(
            "| {condition} | {tp} | {fp} | {fn} | {precision} | {recall} | {f1} | {unsupported} | {violations} | {procedural} |".format(
                condition=row.get("condition"),
                tp=row.get("true_positive"),
                fp=row.get("false_positive"),
                fn=row.get("false_negative"),
                precision=fmt_metric(row.get("precision")),
                recall=fmt_metric(row.get("recall")),
                f1=fmt_metric(row.get("f1")),
                unsupported=fmt_metric(row.get("unsupported_edge_rate")),
                violations=row.get("ontology_violation_count"),
                procedural=row.get("procedural_edge_count"),
            )
        )
    lines += [
        "",
        "The proxy scaffold rows are useful for debugging ablation behavior, but they include silver-derived references and synthetic condition transformations.",
        "",
        "## Error Taxonomy",
        "",
        "| family | observed signal | likely cause | affected conditions | paper treatment | next action |",
        "|---|---|---|---|---|---|",
    ]
    for row in taxonomy:
        lines.append(
            "| {family} | {signal} | {cause} | {conditions} | {treatment} | {action} |".format(
                family=row["family"],
                signal=row["observed_signal"],
                cause=row["likely_cause"],
                conditions=", ".join(row["affected_conditions"]),
                treatment=row["paper_treatment"],
                action=row["next_action"],
            )
        )
    lines += [
        "",
        "## Diagnostic Observations",
        "",
    ]
    lines.extend(f"- {text}" for text in observations)
    if model_scaling_silver_eval:
        lines += [
            "",
            "## Model-Scaling Diagnostic Slice",
            "",
            "| model | condition | rows | edge F1 | predicate F1 | node F1 | evidence F1 | parse/repaired rows |",
            "|---|---|---:|---:|---:|---:|---:|---:|",
        ]
        for row in model_scaling_silver_eval.get("rows", []):
            lines.append(
                "| {model} | {condition} | {rows} | {edge_f1} | {pred_f1} | {node_f1} | {ev_f1} | {parse_rows}/{repaired_rows} |".format(
                    model=row.get("model"),
                    condition=row.get("condition"),
                    rows=row.get("rows"),
                    edge_f1=fmt_metric(row.get("edge_exact_f1")),
                    pred_f1=fmt_metric(row.get("predicate_f1")),
                    node_f1=fmt_metric(row.get("node_label_f1")),
                    ev_f1=fmt_metric(row.get("evidence_f1")),
                    parse_rows=row.get("parse_or_generation_error_rows"),
                    repaired_rows=row.get("partial_json_repaired_rows"),
                )
            )
    lines += [
        "",
        "## Strict JSON and Recovery Notes",
        "",
        f"- Strict JSON gate status: `{summary['strict_json_gate_status']}`",
        f"- Revalidated output recovery status: `{summary['revalidated_output_recovery_status']}`",
        f"- Top strict-error conditions: {', '.join(top_strict_conditions) if top_strict_conditions else 'none'}",
        "",
        "## Human-Gold Follow-Up",
        "",
    ]
    lines.extend(f"- {text}" for text in human_follow_up)
    lines += [
        "",
        "## Source Files",
        "",
    ]
    for label, path in payload["source_files"].items():
        if isinstance(path, list):
            value = ", ".join(f"`{item}`" for item in path if item)
        else:
            value = f"`{path}`" if path else "`not available`"
        lines.append(f"- {label}: {value}")
    lines.append("")
    return payload, "\n".join(lines)


def write_reports(exp_dir, kg, chunks, ref_nodes, ref_edges, ref_evidence, metric_rows, cq_rows, mapping_rows, review_queue):
    exp_dir = Path(exp_dir)
    llm_raw_path = exp_dir / "45_llm_tool_extractions_raw.jsonl"
    llm_valid_path = exp_dir / "46_llm_tool_extractions_valid.jsonl"
    llm_report_path = exp_dir / "47_llm_extraction_quality_report.md"
    llm_extraction = summarize_llm_run(llm_raw_path, llm_valid_path, llm_report_path, "qwen3_8b_full_120")
    additional_llm_runs = collect_additional_llm_runs(exp_dir)
    condition_baseline_runs = collect_condition_baseline_runs(exp_dir)
    public_manifest_path = exp_dir / "08_public_benchmarks/public_benchmark_manifest.json"
    public_benchmarks = read_json(public_manifest_path) if public_manifest_path.exists() else None
    public_eval_runs = collect_public_eval_runs(exp_dir)
    public_synthetic_examples = collect_public_synthetic_examples(exp_dir)
    human_annotation_package = collect_human_annotation_package(exp_dir)
    annotation_progress = collect_annotation_progress(exp_dir)
    annotation_qc = collect_annotation_qc(exp_dir)
    human_gate_action_plan = collect_human_gate_action_plan(exp_dir)
    actual_llm_silver_eval = collect_actual_llm_silver_eval(exp_dir)
    model_scaling_silver_eval = collect_model_scaling_silver_eval(exp_dir)
    active_review_efficiency = collect_active_review_efficiency(exp_dir)
    statistical_analysis = collect_statistical_analysis(exp_dir)
    model_selection_plan = collect_model_selection_plan(exp_dir)
    strict_json_diagnostics = collect_strict_json_diagnostics(exp_dir)
    submission_readiness_audit = collect_submission_readiness_audit(exp_dir)
    method_module_coverage = collect_method_module_coverage(exp_dir)
    release_bundle = collect_release_bundle(exp_dir)
    human_gold_eval = collect_human_gold_eval(exp_dir)
    mapping_expert_review = collect_mapping_expert_review(exp_dir)
    error_analysis_payload, error_analysis_markdown = build_error_analysis_report(
        exp_dir,
        metric_rows,
        actual_llm_silver_eval,
        model_scaling_silver_eval,
        strict_json_diagnostics,
        human_gold_eval,
        mapping_expert_review,
        active_review_efficiency,
        statistical_analysis,
    )
    write_json(exp_dir / "07_reports/error_analysis.json", error_analysis_payload)
    write_text(exp_dir / "07_reports/error_analysis.md", error_analysis_markdown)
    error_analysis_ready = bool((error_analysis_payload.get("summary") or {}).get("ready_for_minimum_accept"))
    public_benchmark_status = (
        "PAGED/Text2KGBench acquired, profiled, adapter subsets generated, and model subset evaluation generated"
        if public_eval_runs
        else "PAGED/Text2KGBench acquired, profiled, and adapter subsets generated"
        if public_benchmarks
        else "PAGED/Text2KGBench not yet run locally"
    )
    human_validation = (human_gold_eval or {}).get("validation") or {}
    human_completed_chunks = int(human_validation.get("completed_adjudicated_chunks") or 0)
    human_gold_items = int(human_validation.get("gold_item_count_for_readiness") or 0)
    human_validation_errors = int(human_validation.get("validation_error_count") or 0)
    human_gold_metrics = (human_gold_eval or {}).get("metrics") or []
    human_gold_chunks_ready = human_completed_chunks >= 100 and human_validation_errors == 0
    human_gold_items_ready = human_gold_items >= 500 and human_validation_errors == 0
    strong_human_gold_chunks_ready = human_completed_chunks >= 300 and human_validation_errors == 0
    strong_human_gold_items_ready = human_gold_items >= 1500 and human_validation_errors == 0
    annotation_expansion_path = exp_dir / "01_data/gold_annotation/annotation_expansion_manifest.json"
    annotation_expansion = read_json(annotation_expansion_path) if annotation_expansion_path.exists() else {}
    strong_resegmented_package = annotation_expansion.get("strong_resegmented_package") or "strong_resegmented_package"
    strong_resegmented_chunks = int(annotation_expansion.get("strong_resegmented_chunk_count") or 0)
    gold_sampling_path = Path(exp_dir) / "06_release/gold_sampling_coverage_report.json"
    gold_sampling = read_json(gold_sampling_path) if gold_sampling_path.exists() else {}
    sampling_policy = gold_sampling.get("selection_policy") or {}
    sampling_coverage = gold_sampling.get("coverage_summary") or {}
    priority_100_selected = int(sampling_policy.get("selected_chunk_count") or 0)
    priority_100_candidate_edges = int(sampling_coverage.get("priority_100_candidate_edges") or 0)
    full_120_candidate_edges = int(sampling_coverage.get("full_120_candidate_edges") or 0)
    priority_100_candidate_coverage = float(
        sampling_coverage.get("priority_100_candidate_edge_coverage_of_full120") or 0.0
    )
    priority_100_active_coverage = float(
        sampling_coverage.get("priority_100_active_review_chunk_coverage_of_full120") or 0.0
    )
    priority_100_high_impact_coverage = float(
        sampling_coverage.get("priority_100_high_impact_chunk_coverage_of_full120") or 0.0
    )
    gold_sampling_ready = (
        priority_100_selected >= 100
        and full_120_candidate_edges > 0
        and priority_100_candidate_coverage >= 0.90
        and priority_100_active_coverage >= 0.90
        and priority_100_high_impact_coverage >= 0.90
    )
    gold_sampling_note = (
        "priority-100 sampling selected "
        f"{priority_100_selected} chunks; candidate_edge_coverage={priority_100_candidate_coverage:.6f} "
        f"({priority_100_candidate_edges}/{full_120_candidate_edges}), "
        f"active_review_coverage={priority_100_active_coverage:.6f}, "
        f"high_impact_coverage={priority_100_high_impact_coverage:.6f}; "
        "not gold until two annotators, IAA, and adjudication are complete"
        if gold_sampling_ready
        else "priority-100 sampling coverage report missing or below readiness threshold"
    )
    iaa_ready = any(
        iaa.get("status") == "computed" and int(iaa.get("completed_pair_chunks") or 0) >= 100
        for iaa in (human_annotation_package or {}).get("iaa_reports", [])
    )
    human_annotation_note = (
        f"IAA computed for 100+ chunks; validation errors={human_validation_errors}"
        if iaa_ready
        else "two-annotator assignment package generated; human completion/adjudication pending"
        if human_annotation_package
        else "requires human annotation"
    )
    gold_subset_note = (
        f"human-gold validation: {human_completed_chunks}/{len(chunks)} completed chunks, "
        f"{human_gold_items} node/edge/evidence items, validation_errors={human_validation_errors}"
        if human_gold_eval
        else f"{len(chunks)} chunk A/B annotation package prepared; human gold pending"
        if human_annotation_package
        else f"{len(chunks)} chunk silver subset prepared; human gold pending"
    )
    proposed_human_gold_scored = any(row.get("condition") == "P_cape_kg_actual" for row in human_gold_metrics)
    actual_ablation_conditions = {
        condition
        for run in condition_baseline_runs
        for condition, counts in run.get("conditions", {}).items()
        if condition.startswith("P_minus_") and counts.get("raw_rows", 0) >= len(chunks)
    }
    actual_ablation_ready = len(actual_ablation_conditions) >= 3
    condition_row_counts = {}
    for run in condition_baseline_runs:
        for condition, counts in run.get("conditions", {}).items():
            condition_row_counts[condition] = max(
                int(condition_row_counts.get(condition) or 0),
                int(counts.get("raw_rows") or 0),
            )
    strong_family_baseline_ready = (
        condition_row_counts.get("B3_edc_style", 0) >= len(chunks)
        and condition_row_counts.get("B4_taxonomy_rag", 0) >= len(chunks)
        and condition_row_counts.get("B6_sac_kg_verifier_pruner", 0) >= len(chunks)
    )
    ablation_note = (
        f"actual LLM ablations completed for {len(actual_ablation_conditions)} conditions: "
        + ", ".join(sorted(actual_ablation_conditions))
        if actual_ablation_ready
        else "proxy ablations completed; actual ablation runs pending or smoke-scale"
    )
    readiness = {
        "minimum_accept_checklist": [
            ("100+ chunk gold annotation", human_gold_chunks_ready, gold_subset_note),
            (
                "500+ gold node/edge/evidence item",
                human_gold_items_ready,
                f"human-gold validation: {human_gold_items} items; silver reference edges={len(ref_edges)}",
            ),
            ("2+ annotators and agreement", iaa_ready, human_annotation_note),
            ("Priority-100 gold subset sampling ready", gold_sampling_ready, gold_sampling_note),
            (
                "B0/B1/B2 baseline completed",
                True,
                "condition-specific actual B0/B1/B2/B4/B5 full runs exist; human-gold scoring pending",
            ),
            (
                "CAPE-KG proposed result completed",
                proposed_human_gold_scored,
                "actual proposed generation has human-gold scores"
                if proposed_human_gold_scored
                else "actual proposed generation and silver-proxy scoring exist; human-gold evaluation pending"
                if actual_llm_silver_eval
                else "silver/proxy proposed result exists; human-gold evaluation pending",
            ),
            ("3+ ablations completed", actual_ablation_ready, ablation_note),
            (
                "error analysis table",
                error_analysis_ready,
                "structured error analysis generated with claim scope, taxonomy, diagnostics, and human-gold follow-up"
                if error_analysis_ready
                else "error analysis report did not meet structured diagnostic requirements",
            ),
            ("public benchmark/subset experiment", bool(public_eval_runs), public_benchmark_status),
            ("code/prompt/schema release plan", True, "prompt/schema/reproducibility package generated"),
            ("limitations section", True, "limitations generated"),
        ],
        "strong_accept_checklist": [
            (
                "300-500 chunk gold annotation",
                strong_human_gold_chunks_ready,
                f"human-gold validation: {human_completed_chunks}/300 adjudicated chunks; optional package {strong_resegmented_package} has {strong_resegmented_chunks} review units",
            ),
            (
                "1,500+ gold edge/evidence item",
                strong_human_gold_items_ready,
                f"human-gold validation: {human_gold_items}/1500 items; validation_errors={human_validation_errors}",
            ),
            ("PAGED/Text2KGBench cross experiment", bool(public_eval_runs), public_benchmark_status),
            (
                "EDC/SAC-KG/Taxonomy-RAG family baseline",
                strong_family_baseline_ready,
                "B3/B4/B6-family artifacts are generated; SAC-KG is represented by a deterministic verifier/pruner approximation"
                if strong_family_baseline_ready
                else f"B3/B4/B6 row counts: {condition_row_counts.get('B3_edc_style', 0)}/{condition_row_counts.get('B4_taxonomy_rag', 0)}/{condition_row_counts.get('B6_sac_kg_verifier_pruner', 0)}",
            ),
            (
                "NCS/PCF mapping downstream evaluation",
                False,
                "candidate/rerank diagnostics exist; expert-reviewed P@K/MRR/nDCG claims pending",
            ),
            (
                "active review efficiency evaluation",
                False,
                "silver/proxy active-review diagnostics exist; human effort timing and adjudicated outcome alignment pending",
            ),
            ("visualization/demo", True, "KG viewer generated from current Layer 2 graph artifacts"),
        ],
    }
    write_json(Path(exp_dir) / "06_release/paper_readiness_checklist.json", readiness)

    limitations = """# Limitations

This run is an EACL experiment scaffold and silver/proxy evaluation, not a
paper-claimable final result.

- The reference labels are derived from the current AX-EPAK KG and must be
  replaced or adjudicated by two human annotators.
- Silver/proxy baseline rows remain only for metric wiring and sanity checks.
  Actual Qwen3-8B B0/B1/B2/B4/B5 generations and CAPE ablations are present,
  but paper claims still require adjudicated human-gold scoring.
- The Qwen3-8B strict JSON warning gate now passes after the top-3 warning
  conditions were rerun with a longer 2400-token strict/no-think setting; raw
  parse recovery should still be reported as an engineering reliability note.
- Qwen3-32B-AWQ has been completed for the core B0/B1/B2/P 120-chunk
  diagnostic conditions, but those scores are still silver/proxy evidence.
- Standard Qwen3-32B full-precision/standard-weight execution is not currently
  recommended on this disk state; free additional space before attempting it.
- PAGED/Text2KGBench public subset runs are diagnostic small-subset checks, not
  full public benchmark leaderboard results.
- Raw text release still requires copyright review.
"""
    write_text(exp_dir / "06_release/limitations.md", limitations)

    mean_cq = statistics.mean([r["score"] for r in cq_rows if r["condition"] == "P_cape_kg_silver"]) if cq_rows else 0
    report = f"""# CAPE-KG EACL Experiment Report

Generated: {datetime.now(timezone.utc).isoformat()}

## Scope

This package follows `AX_EACL_submission_review_revised_plan.md` by reframing
the AX task as CAPE-KG: competency-question anchored procedural evidence
grounding for domain KG construction.

## Data

- Source KG directory: `{kg['summary'].get('output_dir', 'outputs')}`
- OCR workbook: `{kg['summary'].get('ocr_file')}`
- Total chunks available: {len(kg['chunks'])}
- Evaluation chunks selected: {len(chunks)}
- Silver reference nodes: {len(ref_nodes)}
- Silver reference edges: {len(ref_edges)}
- Silver evidence anchors: {len(ref_evidence)}

## Main Silver/Proxy Results

These numbers validate the evaluation code path. They are not final paper
claims until the silver reference is replaced with human gold and the actual
LLM generations are scored against adjudicated labels.

"""
    for row in metric_rows:
        report += (
            f"- {row['condition']}: Edge F1={row['f1']}, "
            f"Evidence EM={row['evidence_exact_match']}, "
            f"Ontology={row['ontology_conformance']}, "
            f"Procedural={row['procedural_consistency']}\n"
        )
    report += f"\n## CQ Answerability\n\n- P_cape_kg_silver mean CQ score: {mean_cq:.2f}/5\n"
    report += "\n## Mapping Downstream\n\n"
    for row in mapping_rows:
        report += f"- {row['standard']}: coverage={row['coverage']} top5_rows={row['top5_candidate_rows']} reason_rate={row['reason_present_rate']}\n"
    if mapping_expert_review:
        report += "\n### Mapping Expert Review\n\n"
        manifest = mapping_expert_review.get("review_manifest") or {}
        report += f"- Review manifest: `{mapping_expert_review.get('manifest_file')}`\n"
        if mapping_expert_review.get("workbench_file"):
            report += f"- Review workbench: `{mapping_expert_review.get('workbench_file')}`\n"
        if manifest.get("import_command"):
            report += f"- Safe import dry run: `{manifest.get('import_command')}`\n"
        report += f"- Candidate rows: {manifest.get('candidate_rows')}\n"
        if mapping_expert_review.get("report_file"):
            report += f"- Evaluation report: `{mapping_expert_review.get('report_file')}`\n"
        if mapping_expert_review.get("progress_report_file"):
            report += f"- Progress report: `{mapping_expert_review.get('progress_report_file')}`\n"
        if mapping_expert_review.get("priority_queue_file"):
            report += f"- Priority queue: `{mapping_expert_review.get('priority_queue_file')}`\n"
        if mapping_expert_review.get("next_groups_file"):
            report += f"- Next 20 groups: `{mapping_expert_review.get('next_groups_file')}`\n"
        if mapping_expert_review.get("next_rows_file"):
            report += f"- Next 60 rows: `{mapping_expert_review.get('next_rows_file')}`\n"
        progress_summary = mapping_expert_review.get("progress_summary") or {}
        if progress_summary:
            report += (
                f"- Review progress: completed_rows={progress_summary.get('completed_rows')}, "
                f"pending_rows={progress_summary.get('pending_rows')}, "
                f"complete_source_groups={progress_summary.get('complete_source_groups')}, "
                f"pending_source_groups={progress_summary.get('pending_source_groups')}, "
                f"status={progress_summary.get('claim_status')}\n"
            )
        for row in (mapping_expert_review.get("evaluation") or {}).get("metrics", []):
            report += (
                f"- {row.get('standard')}: completed_rows={row.get('completed_rows')}, "
                f"pending_rows={row.get('pending_rows')}, Hit@5={row.get('hit_at_5')}, "
                f"P@5={row.get('precision_at_5')}, MRR={row.get('mrr')}, "
                f"status={row.get('claim_status')}\n"
            )
    report += f"\n## Active Review\n\n- Silver/proxy review queue items: {len(review_queue)}\n- Highest priority: {review_queue[0]['review_priority'] if review_queue else 0}\n"
    if active_review_efficiency:
        report += "\n### Actual LLM Active-Review Diagnostic\n\n"
        report += f"- Report: `{active_review_efficiency.get('report_file')}`\n"
        report += f"- Metrics: `{active_review_efficiency.get('metrics_file')}`\n"
        report += f"- Queue JSONL: `{active_review_efficiency.get('queue_jsonl')}`\n"
        report += f"- Candidate edges: {active_review_efficiency.get('candidate_count')}\n"
        report += f"- Silver/proxy error rate: {active_review_efficiency.get('error_rate')}\n"
        report += f"- High-impact silver/proxy error rate: {active_review_efficiency.get('high_impact_error_rate')}\n"
        rows = [
            row for row in active_review_efficiency.get("metrics", [])
            if row.get("target_label") == "high_impact_error"
            and row.get("budget") in {10, 25, 55, 100}
            and row.get("strategy") in {"active_priority", "uncertainty_only"}
        ]
        for row in rows:
            report += (
                f"- {row.get('strategy')} @ {row.get('budget')}: "
                f"precision={row.get('error_precision_at_k')}, "
                f"recall={row.get('error_recall_at_k')}, "
                f"lift={row.get('lift_vs_random_expected')}\n"
            )
        report += "\nThis is a silver/proxy prioritization diagnostic, not a human review efficiency claim.\n"
    if llm_extraction:
        report += "\n## Local LLM Extraction Run\n\n"
        report += f"- Raw chunk rows: {llm_extraction['raw_chunk_rows']}\n"
        report += f"- Valid task frames: {llm_extraction['valid_task_frames']}\n"
        report += f"- Valid procedural relations: {llm_extraction['valid_procedural_relations']}\n"
        report += f"- Raw rows with parse/generation errors: {llm_extraction['raw_rows_with_parse_or_generation_errors']}\n"
        report += f"- Report: `{llm_extraction['report_file']}`\n"
        report += "\nThis validates the local Qwen3-8B extraction path over the selected chunks. It is still not a condition-specific B0/B1/B2/B4/B5 baseline matrix.\n"
    if additional_llm_runs:
        report += "\n## Additional LLM Model Runs\n\n"
        for run in additional_llm_runs:
            report += (
                f"- {run['run_label']}: raw_rows={run['raw_chunk_rows']}, "
                f"task_frames={run['valid_task_frames']}, "
                f"relations={run['valid_procedural_relations']}, "
                f"rejections={run['rejected_candidates']}, "
                f"parse_or_generation_error_rows={run['raw_rows_with_parse_or_generation_errors']}, "
                f"report=`{run['report_file']}`\n"
            )
        report += "\nThese are smoke/model-compatibility runs unless their chunk count and prompts match the full baseline matrix.\n"
    if model_selection_plan:
        report += "\n## Model Selection and Scaling\n\n"
        report += f"- Plan: `{model_selection_plan.get('plan_file')}`\n"
        report += "- Current paper-package model: Qwen3-8B 4bit full 120-chunk condition runs.\n"
        if model_selection_plan.get("qwen3_14b_core_report"):
            report += "- Stronger local diagnostic run: Qwen3-14B 4bit full 120-chunk B0/B1/B2/P core conditions.\n"
            report += f"  - Run report: `{model_selection_plan.get('qwen3_14b_core_report')}`\n"
        if model_selection_plan.get("qwen3_14b_core_silver_report"):
            report += f"  - Silver proxy report: `{model_selection_plan.get('qwen3_14b_core_silver_report')}`\n"
        if model_selection_plan.get("qwen3_32b_awq_core_report"):
            report += "- Stronger local diagnostic run: Qwen3-32B-AWQ full 120-chunk B0/B1/B2/P core conditions.\n"
            report += f"  - Run report: `{model_selection_plan.get('qwen3_32b_awq_core_report')}`\n"
        if model_selection_plan.get("qwen3_32b_awq_core_silver_report"):
            report += f"  - Silver proxy report: `{model_selection_plan.get('qwen3_32b_awq_core_silver_report')}`\n"
        report += "- Compatibility smoke run: Llama-2-13B-chat 4bit on 10 chunks.\n"
        if model_selection_plan.get("qwen3_32b_awq_core_report"):
            report += "- Remaining stronger local next-run candidate: standard Qwen3-32B after sufficient disk space is available.\n"
        else:
            report += "- Stronger local next-run candidate: Qwen3-32B-AWQ after AWQ runner validation, or standard Qwen3-32B after sufficient disk space is available.\n"
        report += "- Current hardware assumption: 8 x RTX 3090 GPUs; Qwen3-32B template uses four shards with two GPUs per shard.\n"
        if model_selection_plan.get("qwen3_32b_awq_readiness_report"):
            readiness = model_selection_plan.get("qwen3_32b_awq_readiness") or {}
            report += f"- Qwen3-32B-AWQ readiness: `{readiness.get('status')}`\n"
            report += f"  - Report: `{model_selection_plan.get('qwen3_32b_awq_readiness_report')}`\n"
            report += f"  - Next action: {readiness.get('recommended_next_action')}\n"
        report += "\nQwen3-14B/32B-AWQ improve the local model-strength evidence, but paper-level claims remain provisional until human-gold scoring is available.\n"
    if strict_json_diagnostics:
        report += "\n## Strict JSON Diagnostics\n\n"
        report += f"- Report: `{strict_json_diagnostics.get('report_file')}`\n"
        report += f"- Priority CSV: `{strict_json_diagnostics.get('priority_queue_file')}`\n"
        report += f"- Contract prompt: `{strict_json_diagnostics.get('strict_json_contract_prompt_file')}`\n"
        report += f"- Strict JSON gate: {strict_json_diagnostics.get('strict_json_gate_status')}\n"
        report += f"- Recovery gate: {strict_json_diagnostics.get('revalidated_output_recovery_status')}\n"
        report += f"- Conditions over strict threshold: {strict_json_diagnostics.get('conditions_over_strict_json_warning_threshold')}\n"
        report += f"- Conditions over unrepaired threshold: {strict_json_diagnostics.get('conditions_over_unrepaired_error_threshold')}\n"
        top_conditions = strict_json_diagnostics.get("top_strict_json_reprompt_conditions") or []
        if top_conditions:
            report += f"- Re-prompt priority: {', '.join(top_conditions[:6])}\n"
        report += "\nThis diagnostic does not change existing generated outputs; it documents parse recovery and provides a strict JSON contract for future smoke/full reruns.\n"
    if submission_readiness_audit:
        summary = submission_readiness_audit.get("summary") or {}
        report += "\n## Plan Requirements Audit\n\n"
        report += f"- Report: `{submission_readiness_audit.get('report_file')}`\n"
        report += f"- Metrics: `{submission_readiness_audit.get('audit_file')}`\n"
        report += f"- Claim status: {submission_readiness_audit.get('claim_status')}\n"
        report += f"- Audited items: {summary.get('items')}\n"
        report += f"- Status counts: `{summary.get('status_counts')}`\n"
        report += f"- Minimum-accept blocking items: {summary.get('minimum_accept_blocking_items')}\n"
        for row in submission_readiness_audit.get("blocking_items", []):
            report += f"  - {row.get('id')}: {row.get('requirement')} -> {row.get('next_step')}\n"
    if method_module_coverage:
        coverage_summary = method_module_coverage.get("summary") or {}
        report += "\n## Method Module Coverage\n\n"
        report += f"- Report: `{method_module_coverage.get('report_file')}`\n"
        report += f"- Metrics: `{method_module_coverage.get('coverage_file')}`\n"
        report += f"- Modules with required artifacts: {coverage_summary.get('modules_with_required_artifacts')}/{coverage_summary.get('module_count')}\n"
        report += f"- Missing required artifacts: {coverage_summary.get('missing_required_artifact_count')}\n"
        report += f"- Human-dependent modules for final claims: {coverage_summary.get('human_dependent_module_count')}\n"
        report += f"- Claim status: {coverage_summary.get('claim_status')}\n"
        for row in method_module_coverage.get("modules", []):
            report += (
                f"- {row.get('module_id')} {row.get('name')}: {row.get('status')}; "
                f"remaining={row.get('remaining_for_paper_claim')}\n"
            )
    if condition_baseline_runs:
        report += "\n## Condition-Specific LLM Baseline Runs\n\n"
        for run in condition_baseline_runs:
            report += f"- {run['run_label']}: raw_rows={run['raw_rows']}, report=`{run['report_file']}`\n"
            for condition, counts in sorted(run["conditions"].items()):
                report += (
                    f"  - {condition}: raw_rows={counts['raw_rows']}, "
                    f"valid_triples={counts['valid_triples']}, "
                    f"valid_nodes={counts['valid_nodes']}, "
                    f"valid_edges={counts['valid_edges']}, "
                    f"valid_mappings={counts['valid_mappings']}, "
                    f"parse_or_generation_error_rows={counts['raw_rows_with_parse_or_generation_errors']}, "
                    f"partial_json_repaired_rows={counts.get('partial_json_repaired_rows', 0)}\n"
            )
        report += "\nThese are actual condition-specific LLM generations, but currently smoke-scale unless raw_rows match the full evaluation set for each condition.\n"
    if actual_llm_silver_eval:
        report += "\n## Actual LLM Silver-Proxy Evaluation\n\n"
        report += f"- Report: `{actual_llm_silver_eval.get('report_file')}`\n"
        report += f"- Metrics: `{actual_llm_silver_eval.get('metrics_file')}`\n"
        focus_conditions = {
            "B0_plain_llm",
            "B1_predicate_constrained",
            "B2_current_project",
            "B3_edc_style",
            "B4_taxonomy_rag",
            "B5_procedural_prompt",
            "B6_sac_kg_verifier_pruner",
            "P_cape_kg_actual",
            "P_minus_CQ",
            "P_minus_Evidence",
            "P_minus_Procedural_schema",
            "P_minus_Schema_retrieval",
            "P_minus_Validator",
            "P_minus_Standard_bridge",
        }
        for row in actual_llm_silver_eval.get("metrics", []):
            if row.get("condition") not in focus_conditions:
                continue
            report += (
                f"- {row.get('condition')}: edge_exact_F1={row.get('edge_exact_f1')}, "
                f"predicate_F1={row.get('predicate_f1')}, node_F1={row.get('node_label_f1')}, "
                f"evidence_F1={row.get('evidence_f1')}, "
                f"parse_or_generation_error_rows={row.get('parse_or_generation_error_rows')}, "
                f"partial_json_repaired_rows={row.get('partial_json_repaired_rows')}\n"
            )
        report += "\nThese are silver-reference diagnostics, not final human-gold paper scores.\n"
    if model_scaling_silver_eval:
        report += "\n## Model Scaling Silver-Proxy Diagnostics\n\n"
        report += "- Source metrics: `" + "`, `".join(model_scaling_silver_eval.get("source_files", [])) + "`\n"
        for row in model_scaling_silver_eval.get("rows", []):
            report += (
                f"- {row.get('model')} / {row.get('condition')}: rows={row.get('rows')}, "
                f"edge_exact_F1={row.get('edge_exact_f1')}, "
                f"predicate_F1={row.get('predicate_f1')}, "
                f"node_F1={row.get('node_label_f1')}, "
                f"evidence_F1={row.get('evidence_f1')}, "
                f"parse_or_generation_error_rows={row.get('parse_or_generation_error_rows')}, "
                f"partial_json_repaired_rows={row.get('partial_json_repaired_rows')}\n"
            )
        report += "\nThis compares completed local open-weight model scales on the shared B0/B1/B2/P core conditions. It is still silver/proxy evidence only.\n"
    if statistical_analysis:
        report += "\n## Statistical Silver-Proxy Diagnostics\n\n"
        report += f"- Report: `{statistical_analysis.get('report_file')}`\n"
        report += f"- Metrics: `{statistical_analysis.get('metrics_file')}`\n"
        report += f"- Bootstrap CSV: `{statistical_analysis.get('bootstrap_csv')}`\n"
        report += f"- McNemar CSV: `{statistical_analysis.get('mcnemar_csv')}`\n"
        report += f"- Per-chunk scores: `{statistical_analysis.get('chunk_scores_csv')}`\n"
        report += f"- Bootstrap iterations: {statistical_analysis.get('bootstrap_iterations')}\n"
        focus_baselines = {"B0_plain_llm", "B2_current_project", "B3_edc_style", "B4_taxonomy_rag", "B5_procedural_prompt"}
        focus_metrics = {"predicate_f1", "node_label_f1", "evidence_f1"}
        for row in statistical_analysis.get("bootstrap_rows", []):
            if row.get("baseline_condition") not in focus_baselines or row.get("metric") not in focus_metrics:
                continue
            report += (
                f"- P vs {row.get('baseline_condition')} ({row.get('metric')}): "
                f"delta={row.get('mean_delta')}, "
                f"95% CI=[{row.get('bootstrap_ci_low')}, {row.get('bootstrap_ci_high')}], "
                f"p_approx={row.get('bootstrap_p_approx')}\n"
            )
        report += "\nThese paired tests use silver/proxy labels only and must be rerun on adjudicated human gold before final claims.\n"
    if human_gold_eval:
        report += "\n## Human Gold Validation and Evaluation\n\n"
        report += f"- Validation report: `{human_gold_eval.get('validation_report_file')}`\n"
        report += f"- Evaluation report: `{human_gold_eval.get('report_file')}`\n"
        report += f"- Metrics: `{human_gold_eval.get('metrics_file')}`\n"
        validation = human_gold_eval.get("validation") or {}
        report += (
            f"- Completed/adjudicated chunks: {validation.get('completed_adjudicated_chunks', 0)}\n"
            f"- Gold node/edge/evidence items: {validation.get('gold_item_count_for_readiness', 0)}\n"
            f"- Validation errors: {validation.get('validation_error_count', 0)}\n"
            f"- Claim status: {human_gold_eval.get('claim_status')}\n"
        )
        metrics = human_gold_eval.get("metrics") or []
        if metrics:
            for row in metrics:
                if row.get("condition") not in {"B0_plain_llm", "B1_predicate_constrained", "B2_current_project", "P_cape_kg_actual"}:
                    continue
                report += (
                    f"- {row.get('condition')}: edge_exact_F1={row.get('edge_exact_f1')}, "
                    f"node_F1={row.get('node_label_f1')}, "
                    f"evidence_EM={row.get('evidence_exact_match')}, "
                    f"ontology={row.get('ontology_conformance')}, "
                    f"procedural={row.get('procedural_consistency')}, "
                    f"CQ={row.get('cq_answerability')}, "
                    f"unsupported={row.get('unsupported_edge_rate')}\n"
                )
        else:
            report += "\nNo human-gold metrics are claimable yet because adjudication is still pending.\n"
    if public_benchmarks:
        report += "\n## Public Benchmark Adapters\n\n"
        report += f"- Manifest: `{public_manifest_path}`\n"
        for name, bench in public_benchmarks.get("benchmarks", {}).items():
            report += (
                f"- {name}: adapter_subset_items={bench.get('adapter_subset_items')}, "
                f"status={bench.get('adapter_status')}\n"
            )
        if public_eval_runs:
            report += "\n### Public Subset Model Evaluations\n\n"
            for run in public_eval_runs:
                report += (
                    f"- `{run.get('summary_file')}`: PAGED items={run.get('paged_items', 0)}, "
                    f"Text2KG items={run.get('text2kg_items', 0)}, "
                    f"PAGED node F1={run.get('paged', {}).get('mean_node_label_f1')}, "
                    f"PAGED edge-predicate F1={run.get('paged', {}).get('mean_edge_predicate_f1')}, "
                    f"Text2KG relation F1={run.get('text2kg', {}).get('mean_relation_f1')}, "
                    f"Text2KG triple exact F1={run.get('text2kg', {}).get('mean_triple_exact_f1')}\n"
                )
            report += "\nThese are public benchmark adapter runs, not official public leaderboard results.\n"
        else:
            report += "\nThese adapters satisfy acquisition/profiling for the public-benchmark track. Model predictions on those subsets are still pending.\n"
    if public_synthetic_examples:
        report += "\n## Public Synthetic Examples\n\n"
        report += f"- README: `{public_synthetic_examples.get('readme_file')}`\n"
        report += f"- Summary: `{public_synthetic_examples.get('summary_file')}`\n"
        report += f"- Chunks: {public_synthetic_examples.get('synthetic_chunk_count')}\n"
        report += f"- Nodes: {public_synthetic_examples.get('synthetic_node_count')}\n"
        report += f"- Edges: {public_synthetic_examples.get('synthetic_edge_count')}\n"
        report += f"- Validation errors: {public_synthetic_examples.get('validation_error_count')}\n"
        report += f"- Source-text policy: {public_synthetic_examples.get('source_text_policy')}\n"
        report += "\nThese examples are format and release-safety artifacts only; they are not paper results.\n"
    if human_annotation_package:
        report += "\n## Human Gold Annotation Package\n\n"
        report += f"- Manifest: `{human_annotation_package.get('output_dir')}/annotation_package_manifest.json`\n"
        report += f"- Status: {human_annotation_package.get('status')}\n"
        if human_annotation_package.get("annotation_workbench"):
            report += f"- Annotation workbench: `{human_annotation_package.get('annotation_workbench')}`\n"
        if human_annotation_package.get("sync_report"):
            report += f"- Manifest sync report: `{human_annotation_package.get('sync_report')}`\n"
        if human_annotation_package.get("annotator_import_command_template"):
            report += f"- Annotator safe import template: `{human_annotation_package.get('annotator_import_command_template')}`\n"
        if human_annotation_package.get("adjudication_import_command_template"):
            report += f"- Adjudication safe import template: `{human_annotation_package.get('adjudication_import_command_template')}`\n"
        for name, package in sorted(human_annotation_package.get("packages", {}).items()):
            report += (
                f"- {name}: chunks={package.get('chunk_count')}, "
                f"candidate_edges={package.get('candidate_edges_total')}, "
                f"tracking=`{package.get('tracking_sheet')}`\n"
            )
        iaa_reports = human_annotation_package.get("iaa_reports", [])
        if iaa_reports:
            report += "\n### IAA Runs\n\n"
            for iaa in iaa_reports:
                report += (
                    f"- `{iaa.get('report_file', iaa.get('summary_file'))}`: "
                    f"completed_pair_chunks={iaa.get('completed_pair_chunks')}, "
                    f"pending_pair_chunks={iaa.get('pending_pair_chunks')}, "
                    f"status={iaa.get('status')}\n"
                )
        adjudication_drafts = human_annotation_package.get("adjudication_drafts", [])
        if adjudication_drafts:
            report += "\n### Adjudication Drafts\n\n"
            for draft in adjudication_drafts:
                report += (
                    f"- `{draft.get('report_file', draft.get('summary_file'))}`: "
                    f"completed_pair_chunks={draft.get('completed_pair_chunks')}, "
                    f"pending_pair_chunks={draft.get('pending_pair_chunks')}, "
                    f"auto_adjudicated_chunks={draft.get('auto_adjudicated_chunks')}, "
                    f"needs_adjudication_chunks={draft.get('needs_adjudication_chunks')}, "
                    f"status={draft.get('claim_status')}\n"
                )
        report += "\nThis package is ready for human labeling, but it is not a substitute for completed gold annotation.\n"
    if annotation_progress:
        full = annotation_progress.get("full_120_summary") or {}
        files = annotation_progress.get("files") or {}
        report += "\n## Human Annotation Progress\n\n"
        report += f"- Report: `{annotation_progress.get('report_file')}`\n"
        report += f"- Summary: `{annotation_progress.get('summary_file')}`\n"
        report += f"- Full worklist CSV: `{files.get('worklist_csv')}`\n"
        report += f"- Next 100 worklist CSV: `{files.get('next_100_csv')}`\n"
        if annotation_progress.get("batch_assignment_report_file"):
            report += f"- Batch assignment report: `{annotation_progress.get('batch_assignment_report_file')}`\n"
        batch_assignment = annotation_progress.get("batch_assignment") or {}
        if batch_assignment:
            report += (
                f"- Batch assignments: batches={batch_assignment.get('batch_count')}, "
                f"assigned_chunks={batch_assignment.get('assigned_chunks')}, "
                f"candidate_edges={batch_assignment.get('candidate_edges_total')}, "
                f"status={batch_assignment.get('claim_status')}\n"
            )
        report += f"- Gate status: {annotation_progress.get('minimum_gold_gate_status')}\n"
        report += (
            f"- full_120 progress: A_done={full.get('annotator_A_completed_chunks')}, "
            f"B_done={full.get('annotator_B_completed_chunks')}, "
            f"paired_done={full.get('paired_completed_chunks')}, "
            f"adjudicated={full.get('adjudicated_chunks')}, "
            f"active_review_chunks={full.get('active_review_chunks')}, "
            f"high_impact_chunks={full.get('high_impact_chunks')}\n"
        )
        report += "\nThis is a workflow tracker for human annotation, not a substitute for completed gold labels.\n"
    if annotation_qc:
        report += "\n## Annotation QC\n\n"
        report += f"- Report: `{annotation_qc.get('report_file')}`\n"
        report += f"- Summary: `{annotation_qc.get('summary_file')}`\n"
        report += f"- Issue CSV: `{annotation_qc.get('issue_csv')}`\n"
        report += f"- Gate worklist: `{annotation_qc.get('gate_worklist_csv')}`\n"
        report += f"- Overall QC status: {annotation_qc.get('overall_qc_status')}\n"
        report += f"- Full_120 minimum gate: {annotation_qc.get('full_120_minimum_gate_status')}\n"
        report += f"- Errors: {annotation_qc.get('total_error_count')}; warnings: {annotation_qc.get('total_warning_count')}\n"
        for package in annotation_qc.get("packages", []):
            gold_counts = package.get("gold_counts") or {}
            report += (
                f"  - {package.get('package')}: paired={package.get('paired_completed_chunks')}, "
                f"ready_for_adjudication={package.get('ready_for_adjudication_chunks')}, "
                f"adjudicated={package.get('adjudicated_chunks')}, "
                f"gold_items={gold_counts.get('gold_item_count_for_readiness')}\n"
            )
        report += "\nThe QC report checks workflow/import safety; it does not convert pending rows into claimable gold labels.\n"
    if human_gate_action_plan:
        action_readiness = human_gate_action_plan.get("readiness") or {}
        action_progress = human_gate_action_plan.get("current_progress") or {}
        report += "\n## Human Gate Action Plan\n\n"
        report += f"- Report: `{human_gate_action_plan.get('report_file')}`\n"
        report += f"- JSON: `{human_gate_action_plan.get('plan_file')}`\n"
        report += f"- Required returns CSV: `{human_gate_action_plan.get('required_returns_csv')}`\n"
        report += f"- Claim status: {human_gate_action_plan.get('claim_status')}\n"
        report += f"- Return preflight status: {action_readiness.get('overall_return_status')}\n"
        report += (
            f"- Annotation reviewed files present: "
            f"{action_progress.get('annotation_present_reviewed_files')}/"
            f"{action_progress.get('annotation_expected_reviewed_files')}\n"
        )
        report += f"- Required return file entries: {len(human_gate_action_plan.get('required_return_files') or [])}\n"
        report += "\nThis is the single operational checklist for resolving the remaining human-gold, IAA, and expert-review gates.\n"
    claim_gate_report_path = exp_dir / "06_release/claim_gate_report.md"
    claim_gate_json_path = exp_dir / "06_release/claim_gate_report.json"
    paper_tables_md_path = exp_dir / "06_release/paper_tables.md"
    paper_tables_tex_path = exp_dir / "06_release/paper_tables.tex"
    plan_matrix_md_path = exp_dir / "06_release/eacl_plan_compliance_matrix.md"
    plan_matrix_json_path = exp_dir / "06_release/eacl_plan_compliance_matrix.json"
    if claim_gate_report_path.exists() or paper_tables_md_path.exists():
        report += "\n## Claim Gate and Paper Tables\n\n"
        if claim_gate_report_path.exists():
            report += f"- Claim gate report: `{claim_gate_report_path}`\n"
        if claim_gate_json_path.exists():
            claim_gate_payload = read_json(claim_gate_json_path)
            report += f"- Claim gate status: {claim_gate_payload.get('overall_status')}\n"
            report += f"- Required failures: {claim_gate_payload.get('required_failure_count')}\n"
            report += f"- Optional failures: {claim_gate_payload.get('optional_failure_count')}\n"
            report += f"- Warnings: {claim_gate_payload.get('warning_count')}\n"
            report += f"- Claim gate JSON: `{claim_gate_json_path}`\n"
        if paper_tables_md_path.exists():
            report += f"- Paper tables Markdown: `{paper_tables_md_path}`\n"
        if paper_tables_tex_path.exists():
            report += f"- Paper tables LaTeX: `{paper_tables_tex_path}`\n"
        if plan_matrix_md_path.exists():
            report += f"- EACL plan compliance matrix: `{plan_matrix_md_path}`\n"
        if plan_matrix_json_path.exists():
            report += f"- EACL plan compliance JSON: `{plan_matrix_json_path}`\n"
        draft_path = exp_dir / "07_reports/eacl_paper_draft.md"
        draft_status_path = exp_dir / "06_release/eacl_paper_draft_status.json"
        if draft_path.exists():
            report += f"- Claim-safe paper draft: `{draft_path}`\n"
        if draft_status_path.exists():
            report += f"- Paper draft status: `{draft_status_path}`\n"
        report += "\nThe claim gate is expected to fail until human adjudication and IAA are complete.\n"
    if release_bundle:
        report += "\n## Release Bundles\n\n"
        report += f"- Bundle manifest: `{release_bundle.get('manifest_file')}`\n"
        if release_bundle.get("checksums_file"):
            report += f"- Bundle checksums: `{release_bundle.get('checksums_file')}`\n"
        if release_bundle.get("safety_report_file"):
            report += f"- Safety report: `{release_bundle.get('safety_report_file')}`\n"
        latest_index_md = exp_dir / "06_release/latest_release_bundle_index.md"
        latest_index_json = exp_dir / "06_release/latest_release_bundle_index.json"
        if latest_index_md.exists():
            report += f"- Latest release bundle index: `{latest_index_md}`\n"
        if latest_index_json.exists():
            report += f"- Latest release bundle index JSON: `{latest_index_json}`\n"
        report += "- Current bundle filenames and SHA256 values are intentionally read from the latest release bundle index to avoid stale exact-path claims after refresh.\n"
        report += "- Bundle creation does not change the human-gold claim gate status.\n"
    report += "\n## Required Next Step\n\nHuman annotation remains the gating step for EACL-ready evidence.\n"
    human_return_wrapper = Path("scripts/run_cape_human_return_apply.sh")
    post_annotation_script = Path("scripts/run_cape_post_annotation_refresh.sh")
    if human_return_wrapper.exists():
        report += f"- Recommended human-return apply wrapper: `{human_return_wrapper}`\n"
        report += "- Run it with `APPLY_IMPORTS=0` for dry-run validation and `APPLY_IMPORTS=1` only after reviewed return files are present.\n"
        report += "- The wrapper validates returned files before refreshing IAA, adjudication drafts, evaluation, audit, tables, reports, and release bundles.\n"
    if post_annotation_script.exists():
        report += f"- Low-level post-annotation refresh script: `{post_annotation_script}`\n"
        report += "- Use this directly only for debugging; the wrapper is the safer operational entry point.\n"
    write_text(exp_dir / "07_reports/final_eacl_experiment_report.md", report)

    reproducibility = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_kg_summary": kg["summary"],
        "experiment_dir": str(exp_dir),
        "evaluation_chunk_count": len(chunks),
        "silver_reference_edge_count": len(ref_edges),
        "commands": [
            "bash scripts/run_ax_epak_preprocessed.sh",
            f"python3 scripts/build_cape_kg_eacl_experiment.py --kg-dir {DEFAULT_KG_DIR} --experiment-dir {DEFAULT_EXP_DIR} --sample-size 120",
            "for i in 0 1 2 3 4 5 6 7; do CUDA_VISIBLE_DEVICES=$i python3 scripts/run_cep_onto_llm_extraction.py --output-dir experiments/cape_kg_eacl_20260627 --chunk-file 01_data/evaluation_chunks.jsonl --num-shards 8 --shard-index $i --max-new-tokens 800 --max-prompt-chars 4500 & done; wait",
            "python3 scripts/run_cep_onto_llm_extraction.py --output-dir experiments/cape_kg_eacl_20260627 --chunk-file 01_data/evaluation_chunks.jsonl --num-shards 8 --merge-shards",
            "for i in 0 1 2 3 4 5 6 7; do CUDA_VISIBLE_DEVICES=$i python3 scripts/run_cape_llm_condition_baselines.py --output-dir experiments/cape_kg_eacl_20260627 --chunk-file 01_data/evaluation_chunks.jsonl --conditions B0_plain_llm,B1_predicate_constrained,B5_procedural_prompt --output-prefix qwen3_8b_condition_baselines_120 --num-shards 8 --shard-index $i --max-new-tokens 650 --max-prompt-chars 3600 & done; wait",
            "python3 scripts/run_cape_llm_condition_baselines.py --output-dir experiments/cape_kg_eacl_20260627 --chunk-file 01_data/evaluation_chunks.jsonl --output-prefix qwen3_8b_condition_baselines_120 --num-shards 8 --merge-shards",
            "python3 scripts/run_cape_llm_condition_baselines.py --output-dir experiments/cape_kg_eacl_20260627 --chunk-file 01_data/evaluation_chunks.jsonl --output-prefix qwen3_8b_condition_baselines_120 --revalidate-raw",
            "python3 scripts/run_cape_llm_condition_baselines.py --output-dir experiments/cape_kg_eacl_20260627 --chunk-file 01_data/evaluation_chunks.jsonl --output-prefix qwen3_8b_b2_b4_condition_baselines_120 --revalidate-raw",
            "for i in 0 1 2 3 4 5 6 7; do CUDA_VISIBLE_DEVICES=$i python3 scripts/run_cape_llm_condition_baselines.py --output-dir experiments/cape_kg_eacl_20260627 --chunk-file 01_data/evaluation_chunks.jsonl --conditions B3_edc_style,P_minus_Schema_retrieval --output-prefix qwen3_8b_edc_schema_ablation --num-shards 8 --shard-index $i --max-new-tokens 650 --max-prompt-chars 3600 & done; wait",
            "python3 scripts/run_cape_llm_condition_baselines.py --output-dir experiments/cape_kg_eacl_20260627 --chunk-file 01_data/evaluation_chunks.jsonl --output-prefix qwen3_8b_edc_schema_ablation --num-shards 8 --merge-shards",
            "python3 scripts/run_cape_llm_condition_baselines.py --output-dir experiments/cape_kg_eacl_20260627 --chunk-file 01_data/evaluation_chunks.jsonl --output-prefix qwen3_8b_edc_schema_ablation --revalidate-raw",
            "python3 scripts/run_cape_llm_condition_baselines.py --output-dir experiments/cape_kg_eacl_20260627 --chunk-file 01_data/evaluation_chunks.jsonl --output-prefix qwen3_8b_cape_ablation_120 --revalidate-raw",
            "python3 scripts/build_sac_kg_verifier_pruner_baseline.py --experiment-dir experiments/cape_kg_eacl_20260627",
            "MODEL=/home/minjoo/.cache/huggingface/hub/models--Qwen--Qwen3-14B/snapshots/40c069824f4251a91eefaf281ebe4c544efd3e18; PY=python3; EXP=experiments/cape_kg_eacl_20260627; COMMON=\"scripts/run_cape_llm_condition_baselines.py --output-dir $EXP --chunk-file 01_data/evaluation_chunks.jsonl --model $MODEL --quantization 4bit --conditions B0_plain_llm,B1_predicate_constrained,B2_current_project,P_cape_kg_actual --output-prefix qwen3_14b_core_conditions_120 --num-shards 4 --max-new-tokens 650 --max-prompt-chars 3600\"; CUDA_VISIBLE_DEVICES=0,1 $PY $COMMON --shard-index 0 & CUDA_VISIBLE_DEVICES=2,3 $PY $COMMON --shard-index 1 & CUDA_VISIBLE_DEVICES=4,5 $PY $COMMON --shard-index 2 & CUDA_VISIBLE_DEVICES=6,7 $PY $COMMON --shard-index 3 & wait",
            "python3 scripts/run_cape_llm_condition_baselines.py --output-dir experiments/cape_kg_eacl_20260627 --chunk-file 01_data/evaluation_chunks.jsonl --output-prefix qwen3_14b_core_conditions_120 --num-shards 4 --merge-shards",
            "python3 scripts/evaluate_actual_llm_silver.py --experiment-dir experiments/cape_kg_eacl_20260627 --valid-file experiments/cape_kg_eacl_20260627/49_qwen3_14b_core_conditions_120_valid.jsonl --output-stem qwen3_14b_core_silver",
            "python3 scripts/profile_public_benchmarks.py --experiment-dir experiments/cape_kg_eacl_20260627",
            "CUDA_VISIBLE_DEVICES=0,1 python3 scripts/run_public_benchmark_llm_eval.py --experiment-dir experiments/cape_kg_eacl_20260627 --model /home/minjoo/.cache/huggingface/hub/models--Qwen--Qwen3-14B/snapshots/40c069824f4251a91eefaf281ebe4c544efd3e18 --quantization 4bit --output-prefix public_qwen3_14b_subset_eval --max-paged 10 --max-text2kg 20 --max-prompt-chars 2800 --max-new-tokens 550",
            "PY=python3; MODEL=/home/minjoo/.cache/huggingface/hub/models--Qwen--Qwen3-8B/snapshots/b968826d9c46dd6066d109eabc6255188de91218; EXP=experiments/cape_kg_eacl_20260627; COMMON=\"scripts/run_public_benchmark_llm_eval.py --experiment-dir $EXP --model $MODEL --quantization 4bit --output-prefix public_qwen3_8b_full_adapter_eval --max-paged 100 --max-text2kg 200 --max-prompt-chars 2800 --max-new-tokens 550 --num-shards 8 --progress-every 10\"; for i in 0 1 2 3 4 5 6 7; do CUDA_VISIBLE_DEVICES=$i $PY $COMMON --shard-index $i & done; wait",
            "python3 scripts/run_public_benchmark_llm_eval.py --experiment-dir experiments/cape_kg_eacl_20260627 --output-prefix public_qwen3_8b_full_adapter_eval --max-paged 100 --max-text2kg 200 --num-shards 8 --merge-shards",
            "python3 scripts/check_qwen3_32b_awq_readiness.py --experiment-dir experiments/cape_kg_eacl_20260627",
            "python3 scripts/evaluate_actual_llm_silver.py --experiment-dir experiments/cape_kg_eacl_20260627",
            "python3 scripts/evaluate_cape_active_review_efficiency.py --experiment-dir experiments/cape_kg_eacl_20260627",
            "python3 scripts/compute_cape_statistical_analysis.py --experiment-dir experiments/cape_kg_eacl_20260627 --bootstrap-iterations 2000",
            "python3 scripts/build_cape_public_synthetic_examples.py --experiment-dir experiments/cape_kg_eacl_20260627",
            "python3 scripts/audit_cape_plan_requirements.py --experiment-dir experiments/cape_kg_eacl_20260627 --plan-file AX_EACL_submission_review_revised_plan.md",
            "python3 scripts/prepare_cape_mapping_review_package.py --experiment-dir experiments/cape_kg_eacl_20260627 --kg-dir outputs",
            "python3 scripts/build_cape_mapping_review_workbench.py --experiment-dir experiments/cape_kg_eacl_20260627",
            "python3 scripts/import_cape_mapping_review.py --experiment-dir experiments/cape_kg_eacl_20260627 --reviewed-file experiments/cape_kg_eacl_20260627/01_data/mapping_review/mapping_review_items.reviewed.jsonl",
            "python3 scripts/evaluate_cape_mapping_review.py --experiment-dir experiments/cape_kg_eacl_20260627",
            "python3 scripts/build_cape_mapping_review_progress_report.py --experiment-dir experiments/cape_kg_eacl_20260627",
            "python3 scripts/build_cape_annotation_workbench.py --experiment-dir experiments/cape_kg_eacl_20260627",
            "python3 scripts/sync_cape_annotation_manifest.py --experiment-dir experiments/cape_kg_eacl_20260627 --apply",
            "python3 scripts/build_cape_annotation_progress_report.py --experiment-dir experiments/cape_kg_eacl_20260627",
            "python3 scripts/build_cape_annotation_qc_report.py --experiment-dir experiments/cape_kg_eacl_20260627",
            "python3 scripts/build_cape_human_gate_action_plan.py --experiment-dir experiments/cape_kg_eacl_20260627",
            "python3 scripts/build_cape_annotation_batch_assignments.py --experiment-dir experiments/cape_kg_eacl_20260627 --package full_120 --batch-size 20 --max-batches 5",
            "python3 scripts/import_cape_gold_annotation.py --experiment-dir experiments/cape_kg_eacl_20260627 --target-file experiments/cape_kg_eacl_20260627/01_data/gold_annotation/full_120/annotator_A.jsonl --reviewed-file experiments/cape_kg_eacl_20260627/01_data/gold_annotation/full_120/annotator_A_edited.jsonl",
            "python3 scripts/import_cape_gold_annotation.py --experiment-dir experiments/cape_kg_eacl_20260627 --target-file experiments/cape_kg_eacl_20260627/01_data/gold_annotation/full_120/adjudication.jsonl --reviewed-file experiments/cape_kg_eacl_20260627/01_data/gold_annotation/full_120/adjudication_edited.jsonl",
            "python3 scripts/prepare_cape_adjudication_draft.py --experiment-dir experiments/cape_kg_eacl_20260627 --package pilot_30",
            "python3 scripts/prepare_cape_adjudication_draft.py --experiment-dir experiments/cape_kg_eacl_20260627 --package full_120",
            "python3 scripts/evaluate_cape_human_gold.py --experiment-dir experiments/cape_kg_eacl_20260627",
            "python3 scripts/validate_cape_experiment_readiness.py --experiment-dir experiments/cape_kg_eacl_20260627 --no-fail",
            "python3 scripts/build_cape_strict_json_diagnostics.py --experiment-dir experiments/cape_kg_eacl_20260627",
            "python3 scripts/build_cape_method_module_coverage.py --experiment-dir experiments/cape_kg_eacl_20260627 --outputs-dir outputs",
            "python3 scripts/build_cape_paper_tables.py --experiment-dir experiments/cape_kg_eacl_20260627",
            "python3 scripts/build_cape_eacl_paper_draft.py --experiment-dir experiments/cape_kg_eacl_20260627",
            "PYTHON_BIN=python3 LLM_PYTHON=python3 APPLY_IMPORTS=1 bash scripts/run_cape_human_return_apply.sh",
            "python3 scripts/build_cape_release_bundle.py --experiment-dir experiments/cape_kg_eacl_20260627 --outputs-dir outputs --plan-file AX_EACL_submission_review_revised_plan.md",
        ],
        "human_return_apply_wrapper_script": str(Path("scripts/run_cape_human_return_apply.sh")) if Path("scripts/run_cape_human_return_apply.sh").exists() else None,
        "post_annotation_refresh_script": str(Path("scripts/run_cape_post_annotation_refresh.sh")) if Path("scripts/run_cape_post_annotation_refresh.sh").exists() else None,
        "llm_extraction": llm_extraction,
        "additional_llm_runs": additional_llm_runs,
        "condition_baseline_runs": condition_baseline_runs,
        "public_benchmarks": public_benchmarks,
        "public_eval_runs": public_eval_runs,
        "public_synthetic_examples": public_synthetic_examples,
        "human_annotation_package": human_annotation_package,
        "annotation_progress": annotation_progress,
        "annotation_qc": annotation_qc,
        "human_gate_action_plan": human_gate_action_plan,
        "actual_llm_silver_evaluation": actual_llm_silver_eval,
        "model_scaling_silver_evaluation": model_scaling_silver_eval,
        "qwen3_14b_core_run": {
            "raw_file": str(exp_dir / "48_qwen3_14b_core_conditions_120_raw.jsonl") if (exp_dir / "48_qwen3_14b_core_conditions_120_raw.jsonl").exists() else None,
            "valid_file": str(exp_dir / "49_qwen3_14b_core_conditions_120_valid.jsonl") if (exp_dir / "49_qwen3_14b_core_conditions_120_valid.jsonl").exists() else None,
            "report_file": str(exp_dir / "50_qwen3_14b_core_conditions_120_quality_report.md") if (exp_dir / "50_qwen3_14b_core_conditions_120_quality_report.md").exists() else None,
            "silver_metrics": str(exp_dir / "04_evaluation/qwen3_14b_core_silver_metrics.json") if (exp_dir / "04_evaluation/qwen3_14b_core_silver_metrics.json").exists() else None,
            "silver_report": str(exp_dir / "04_evaluation/qwen3_14b_core_silver_evaluation_report.md") if (exp_dir / "04_evaluation/qwen3_14b_core_silver_evaluation_report.md").exists() else None,
        },
        "qwen3_32b_awq_core_run": {
            "raw_file": str(exp_dir / "48_qwen3_32b_awq_core_120_raw.jsonl") if (exp_dir / "48_qwen3_32b_awq_core_120_raw.jsonl").exists() else None,
            "valid_file": str(exp_dir / "49_qwen3_32b_awq_core_120_valid.jsonl") if (exp_dir / "49_qwen3_32b_awq_core_120_valid.jsonl").exists() else None,
            "report_file": str(exp_dir / "50_qwen3_32b_awq_core_120_quality_report.md") if (exp_dir / "50_qwen3_32b_awq_core_120_quality_report.md").exists() else None,
            "silver_metrics": str(exp_dir / "04_evaluation/qwen3_32b_awq_core_silver_metrics.json") if (exp_dir / "04_evaluation/qwen3_32b_awq_core_silver_metrics.json").exists() else None,
            "silver_report": str(exp_dir / "04_evaluation/qwen3_32b_awq_core_silver_evaluation_report.md") if (exp_dir / "04_evaluation/qwen3_32b_awq_core_silver_evaluation_report.md").exists() else None,
        },
        "active_review_efficiency": active_review_efficiency,
        "statistical_analysis": statistical_analysis,
        "strict_json_diagnostics": strict_json_diagnostics,
        "submission_readiness_audit": submission_readiness_audit,
        "method_module_coverage": method_module_coverage,
        "release_bundle_files": {
            "manifest": str(exp_dir / "06_release/release_bundle_manifest.json") if (exp_dir / "06_release/release_bundle_manifest.json").exists() else None,
            "checksums": str(exp_dir / "06_release/release_bundle_checksums.sha256") if (exp_dir / "06_release/release_bundle_checksums.sha256").exists() else None,
            "safety_report": str(exp_dir / "06_release/release_bundle_safety_report.md") if (exp_dir / "06_release/release_bundle_safety_report.md").exists() else None,
        },
        "human_gold_evaluation": human_gold_eval,
        "mapping_expert_review": mapping_expert_review,
        "mapping_review_progress_report": str(exp_dir / "06_release/mapping_review_progress_report.md") if (exp_dir / "06_release/mapping_review_progress_report.md").exists() else None,
        "mapping_review_progress_summary": str(exp_dir / "06_release/mapping_review_progress_summary.json") if (exp_dir / "06_release/mapping_review_progress_summary.json").exists() else None,
        "mapping_review_priority_queue": str(exp_dir / "05_review/mapping_review_priority_queue.csv") if (exp_dir / "05_review/mapping_review_priority_queue.csv").exists() else None,
        "mapping_review_next_20_groups": str(exp_dir / "05_review/mapping_review_next_20_groups.csv") if (exp_dir / "05_review/mapping_review_next_20_groups.csv").exists() else None,
        "mapping_review_next_60_rows": str(exp_dir / "05_review/mapping_review_next_60_rows.csv") if (exp_dir / "05_review/mapping_review_next_60_rows.csv").exists() else None,
        "annotation_qc_report": str(exp_dir / "06_release/annotation_qc_report.md") if (exp_dir / "06_release/annotation_qc_report.md").exists() else None,
        "annotation_qc_summary": str(exp_dir / "06_release/annotation_qc_summary.json") if (exp_dir / "06_release/annotation_qc_summary.json").exists() else None,
        "annotation_qc_issues": str(exp_dir / "05_review/annotation_qc_issues.csv") if (exp_dir / "05_review/annotation_qc_issues.csv").exists() else None,
        "annotation_completion_gate_worklist": str(exp_dir / "05_review/annotation_completion_gate_worklist.csv") if (exp_dir / "05_review/annotation_completion_gate_worklist.csv").exists() else None,
        "human_gate_action_plan": str(exp_dir / "06_release/human_gate_action_plan.md") if (exp_dir / "06_release/human_gate_action_plan.md").exists() else None,
        "human_gate_action_plan_json": str(exp_dir / "06_release/human_gate_action_plan.json") if (exp_dir / "06_release/human_gate_action_plan.json").exists() else None,
        "human_gate_required_returns": str(exp_dir / "05_review/human_gate_required_returns.csv") if (exp_dir / "05_review/human_gate_required_returns.csv").exists() else None,
        "model_selection_plan": str(exp_dir / "06_release/model_selection_and_scaling_plan.md") if (exp_dir / "06_release/model_selection_and_scaling_plan.md").exists() else None,
        "qwen3_32b_awq_readiness_report": str(exp_dir / "06_release/qwen3_32b_awq_readiness.md") if (exp_dir / "06_release/qwen3_32b_awq_readiness.md").exists() else None,
        "qwen3_32b_awq_readiness_json": str(exp_dir / "06_release/qwen3_32b_awq_readiness.json") if (exp_dir / "06_release/qwen3_32b_awq_readiness.json").exists() else None,
        "claim_gate_report": str(exp_dir / "06_release/claim_gate_report.md") if (exp_dir / "06_release/claim_gate_report.md").exists() else None,
        "claim_gate_metrics": str(exp_dir / "06_release/claim_gate_report.json") if (exp_dir / "06_release/claim_gate_report.json").exists() else None,
        "strict_json_diagnostics_report": str(exp_dir / "06_release/strict_json_diagnostics.md") if (exp_dir / "06_release/strict_json_diagnostics.md").exists() else None,
        "strict_json_diagnostics_json": str(exp_dir / "06_release/strict_json_diagnostics.json") if (exp_dir / "06_release/strict_json_diagnostics.json").exists() else None,
        "strict_json_reprompt_priority": str(exp_dir / "05_review/strict_json_reprompt_priority.csv") if (exp_dir / "05_review/strict_json_reprompt_priority.csv").exists() else None,
        "strict_json_contract_prompt": str(exp_dir / "02_schema/prompts/strict_json_contract.txt") if (exp_dir / "02_schema/prompts/strict_json_contract.txt").exists() else None,
        "public_synthetic_examples_summary": str(exp_dir / "06_release/public_synthetic_examples/synthetic_evaluation_summary.json") if (exp_dir / "06_release/public_synthetic_examples/synthetic_evaluation_summary.json").exists() else None,
        "public_synthetic_examples_readme": str(exp_dir / "06_release/public_synthetic_examples/README.md") if (exp_dir / "06_release/public_synthetic_examples/README.md").exists() else None,
        "paper_tables_markdown": str(exp_dir / "06_release/paper_tables.md") if (exp_dir / "06_release/paper_tables.md").exists() else None,
        "paper_tables_latex": str(exp_dir / "06_release/paper_tables.tex") if (exp_dir / "06_release/paper_tables.tex").exists() else None,
        "eacl_plan_compliance_matrix": str(exp_dir / "06_release/eacl_plan_compliance_matrix.md") if (exp_dir / "06_release/eacl_plan_compliance_matrix.md").exists() else None,
        "eacl_plan_compliance_matrix_json": str(exp_dir / "06_release/eacl_plan_compliance_matrix.json") if (exp_dir / "06_release/eacl_plan_compliance_matrix.json").exists() else None,
        "claim_safe_paper_draft": str(exp_dir / "07_reports/eacl_paper_draft.md") if (exp_dir / "07_reports/eacl_paper_draft.md").exists() else None,
        "claim_safe_paper_draft_status": str(exp_dir / "06_release/eacl_paper_draft_status.json") if (exp_dir / "06_release/eacl_paper_draft_status.json").exists() else None,
        "release_bundle_manifest": str(exp_dir / "06_release/release_bundle_manifest.json") if (exp_dir / "06_release/release_bundle_manifest.json").exists() else None,
        "release_bundle_checksums": str(exp_dir / "06_release/release_bundle_checksums.sha256") if (exp_dir / "06_release/release_bundle_checksums.sha256").exists() else None,
        "release_bundle_safety_report": str(exp_dir / "06_release/release_bundle_safety_report.md") if (exp_dir / "06_release/release_bundle_safety_report.md").exists() else None,
        "claim_status": "actual_llm_runs_present_pending_human_gold_iaa_and_scoring",
    }
    write_json(exp_dir / "06_release/reproducibility_manifest.json", reproducibility)


def run(args):
    kg = load_kg(args.kg_dir)
    exp_dir = Path(args.experiment_dir)
    for sub in ["00_plan", "01_data", "02_schema", "03_predictions", "04_evaluation", "05_review", "06_release", "07_reports"]:
        (exp_dir / sub).mkdir(parents=True, exist_ok=True)

    chunks = select_chunks(kg["chunks"], args.sample_size)
    ref_nodes, ref_edges, ref_evidence = make_reference(kg, chunks)
    predictions = make_predictions(ref_edges)
    metric_rows, cq_rows = evaluate_predictions(predictions, ref_edges, {"ncs": kg["ncs_mapping"], "pcf": kg["pcf_mapping"]})
    selected_task_ids = {n["node_id"] for n in ref_nodes if n.get("type") == "DomainTask"}
    mapping_rows = mapping_report_rows(kg, selected_task_ids)
    mapping_arm_rows = mapping_downstream_arm_rows(kg, selected_task_ids)
    mapping_arm_detail_rows = mapping_downstream_arm_detail_rows(kg, selected_task_ids)
    mapping_arm_detail_summary = summarize_mapping_arm_details(mapping_arm_detail_rows)
    review_queue = build_active_review_queue(predictions["P_cape_kg_silver"], ref_edges)
    annotation_rows, annotation_csv = build_annotation_templates(chunks, ref_edges)

    requirements = build_requirements_matrix(
        "AX_EACL_submission_review_revised_plan.md",
        collect_submission_readiness_audit(exp_dir),
    )
    write_json(exp_dir / "00_plan/requirements_matrix.json", requirements)
    write_text(exp_dir / "00_plan/requirements_matrix.md", render_requirements_matrix(requirements))

    write_jsonl(exp_dir / "01_data/evaluation_chunks.jsonl", chunks)
    write_jsonl(exp_dir / "01_data/silver_reference_nodes.jsonl", ref_nodes)
    write_jsonl(exp_dir / "01_data/silver_reference_edges.jsonl", ref_edges)
    write_jsonl(exp_dir / "01_data/silver_reference_evidence.jsonl", ref_evidence)
    write_jsonl(exp_dir / "01_data/gold_annotation_template.jsonl", annotation_rows)
    write_csv(exp_dir / "01_data/gold_annotation_tracking_sheet.csv", annotation_csv)
    write_annotation_guideline(exp_dir / "01_data/annotation_guideline_v1.md")

    write_schema(exp_dir / "02_schema")
    write_prompt_templates(exp_dir / "02_schema/prompts")

    for condition, rows in predictions.items():
        write_jsonl(exp_dir / f"03_predictions/{condition}.jsonl", rows)

    write_csv(exp_dir / "04_evaluation/main_results.csv", metric_rows)
    write_csv(exp_dir / "04_evaluation/cq_answerability_by_condition.csv", cq_rows)
    write_csv(exp_dir / "04_evaluation/mapping_downstream_results.csv", mapping_rows)
    write_csv(exp_dir / "04_evaluation/mapping_downstream_arm_diagnostics.csv", mapping_arm_rows)
    write_csv(exp_dir / "04_evaluation/mapping_downstream_arm_rerank_details.csv", mapping_arm_detail_rows)
    write_json(exp_dir / "04_evaluation/mapping_downstream_arm_rerank_summary.json", mapping_arm_detail_summary)
    write_csv(exp_dir / "05_review/active_review_queue.csv", review_queue)
    write_jsonl(exp_dir / "05_review/active_review_queue.jsonl", review_queue)

    # Report slices.
    write_text(
        exp_dir / "04_evaluation/evidence_grounding_report.md",
        render_evidence_grounding_report(metric_rows),
    )
    write_text(
        exp_dir / "04_evaluation/ontology_conformance_report.md",
        "# Ontology Conformance Report\n\n"
        + "\n".join(f"- {r['condition']}: conformance={r['ontology_conformance']}, violations={r['ontology_violation_count']}" for r in metric_rows)
        + "\n",
    )
    write_text(
        exp_dir / "04_evaluation/procedural_consistency_report.md",
        "# Procedural Consistency Report\n\n"
        + "\n".join(f"- {r['condition']}: procedural_edges={r['procedural_edge_count']}, consistency={r['procedural_consistency']}, cycles={r['precedence_cycle_count']}" for r in metric_rows)
        + "\n",
    )
    write_text(
        exp_dir / "04_evaluation/mapping_downstream_report.md",
        render_mapping_downstream_report(mapping_rows, mapping_arm_rows, mapping_arm_detail_summary),
    )

    write_reports(exp_dir, kg, chunks, ref_nodes, ref_edges, ref_evidence, metric_rows, cq_rows, mapping_rows, review_queue)

    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "experiment_dir": str(exp_dir),
        "evaluation_chunks": len(chunks),
        "silver_reference_nodes": len(ref_nodes),
        "silver_reference_edges": len(ref_edges),
        "silver_reference_evidence": len(ref_evidence),
        "conditions": list(predictions),
        "main_results_file": str(exp_dir / "04_evaluation/main_results.csv"),
        "final_report": str(exp_dir / "07_reports/final_eacl_experiment_report.md"),
        "llm_extraction_raw_file": str(exp_dir / "45_llm_tool_extractions_raw.jsonl") if (exp_dir / "45_llm_tool_extractions_raw.jsonl").exists() else None,
        "llm_extraction_valid_file": str(exp_dir / "46_llm_tool_extractions_valid.jsonl") if (exp_dir / "46_llm_tool_extractions_valid.jsonl").exists() else None,
        "condition_baseline_reports": [
            str(p) for p in sorted(exp_dir.glob("50_*_quality_report.md"))
            if ".shard" not in p.name
        ],
        "public_benchmark_manifest": str(exp_dir / "08_public_benchmarks/public_benchmark_manifest.json") if (exp_dir / "08_public_benchmarks/public_benchmark_manifest.json").exists() else None,
        "public_eval_reports": [
            str(p) for p in sorted((exp_dir / "08_public_benchmarks").glob("*_report.md"))
            if p.name.startswith("public_qwen")
        ],
        "human_annotation_package_manifest": str(exp_dir / "01_data/gold_annotation/annotation_package_manifest.json") if (exp_dir / "01_data/gold_annotation/annotation_package_manifest.json").exists() else None,
        "human_annotation_workbench": str(exp_dir / "01_data/gold_annotation/annotation_workbench.html") if (exp_dir / "01_data/gold_annotation/annotation_workbench.html").exists() else None,
        "human_annotation_manifest_sync_report": str(exp_dir / "01_data/gold_annotation/annotation_manifest_sync_report.md") if (exp_dir / "01_data/gold_annotation/annotation_manifest_sync_report.md").exists() else None,
        "human_annotation_manifest_sync_json": str(exp_dir / "01_data/gold_annotation/annotation_manifest_sync_report.json") if (exp_dir / "01_data/gold_annotation/annotation_manifest_sync_report.json").exists() else None,
        "human_annotation_iaa_reports": [
            str(p) for p in sorted((exp_dir / "01_data/gold_annotation").glob("iaa*/iaa_report.md"))
        ],
        "human_annotation_adjudication_draft_reports": [
            str(p) for p in sorted((exp_dir / "01_data/gold_annotation").glob("*/adjudication_draft_report.md"))
        ],
        "annotation_progress_report": str(exp_dir / "06_release/annotation_progress_report.md") if (exp_dir / "06_release/annotation_progress_report.md").exists() else None,
        "annotation_progress_summary": str(exp_dir / "06_release/annotation_progress_summary.json") if (exp_dir / "06_release/annotation_progress_summary.json").exists() else None,
        "annotation_batch_assignment_report": str(exp_dir / "06_release/annotation_batch_assignment_report.md") if (exp_dir / "06_release/annotation_batch_assignment_report.md").exists() else None,
        "annotation_batch_assignment_summary": str(exp_dir / "06_release/annotation_batch_assignment_summary.json") if (exp_dir / "06_release/annotation_batch_assignment_summary.json").exists() else None,
        "annotation_batch_assignment_overview": str(exp_dir / "05_review/human_gold_batches/full_120_batch_assignment_overview.csv") if (exp_dir / "05_review/human_gold_batches/full_120_batch_assignment_overview.csv").exists() else None,
        "annotation_qc_report": str(exp_dir / "06_release/annotation_qc_report.md") if (exp_dir / "06_release/annotation_qc_report.md").exists() else None,
        "annotation_qc_summary": str(exp_dir / "06_release/annotation_qc_summary.json") if (exp_dir / "06_release/annotation_qc_summary.json").exists() else None,
        "annotation_qc_issues": str(exp_dir / "05_review/annotation_qc_issues.csv") if (exp_dir / "05_review/annotation_qc_issues.csv").exists() else None,
        "annotation_completion_gate_worklist": str(exp_dir / "05_review/annotation_completion_gate_worklist.csv") if (exp_dir / "05_review/annotation_completion_gate_worklist.csv").exists() else None,
        "human_gate_action_plan": str(exp_dir / "06_release/human_gate_action_plan.md") if (exp_dir / "06_release/human_gate_action_plan.md").exists() else None,
        "human_gate_action_plan_json": str(exp_dir / "06_release/human_gate_action_plan.json") if (exp_dir / "06_release/human_gate_action_plan.json").exists() else None,
        "human_gate_required_returns": str(exp_dir / "05_review/human_gate_required_returns.csv") if (exp_dir / "05_review/human_gate_required_returns.csv").exists() else None,
        "annotation_priority_queue": str(exp_dir / "05_review/human_gold_annotation_priority_queue.csv") if (exp_dir / "05_review/human_gold_annotation_priority_queue.csv").exists() else None,
        "annotation_next_100_worklist": str(exp_dir / "05_review/human_gold_next_100_worklist.csv") if (exp_dir / "05_review/human_gold_next_100_worklist.csv").exists() else None,
        "actual_llm_silver_evaluation_report": str(exp_dir / "04_evaluation/actual_llm_silver_evaluation_report.md") if (exp_dir / "04_evaluation/actual_llm_silver_evaluation_report.md").exists() else None,
        "actual_llm_silver_metrics": str(exp_dir / "04_evaluation/actual_llm_silver_metrics.json") if (exp_dir / "04_evaluation/actual_llm_silver_metrics.json").exists() else None,
        "qwen3_14b_core_raw_file": str(exp_dir / "48_qwen3_14b_core_conditions_120_raw.jsonl") if (exp_dir / "48_qwen3_14b_core_conditions_120_raw.jsonl").exists() else None,
        "qwen3_14b_core_valid_file": str(exp_dir / "49_qwen3_14b_core_conditions_120_valid.jsonl") if (exp_dir / "49_qwen3_14b_core_conditions_120_valid.jsonl").exists() else None,
        "qwen3_14b_core_quality_report": str(exp_dir / "50_qwen3_14b_core_conditions_120_quality_report.md") if (exp_dir / "50_qwen3_14b_core_conditions_120_quality_report.md").exists() else None,
        "qwen3_14b_core_silver_evaluation_report": str(exp_dir / "04_evaluation/qwen3_14b_core_silver_evaluation_report.md") if (exp_dir / "04_evaluation/qwen3_14b_core_silver_evaluation_report.md").exists() else None,
        "qwen3_14b_core_silver_metrics": str(exp_dir / "04_evaluation/qwen3_14b_core_silver_metrics.json") if (exp_dir / "04_evaluation/qwen3_14b_core_silver_metrics.json").exists() else None,
        "qwen3_32b_awq_core_raw_file": str(exp_dir / "48_qwen3_32b_awq_core_120_raw.jsonl") if (exp_dir / "48_qwen3_32b_awq_core_120_raw.jsonl").exists() else None,
        "qwen3_32b_awq_core_valid_file": str(exp_dir / "49_qwen3_32b_awq_core_120_valid.jsonl") if (exp_dir / "49_qwen3_32b_awq_core_120_valid.jsonl").exists() else None,
        "qwen3_32b_awq_core_quality_report": str(exp_dir / "50_qwen3_32b_awq_core_120_quality_report.md") if (exp_dir / "50_qwen3_32b_awq_core_120_quality_report.md").exists() else None,
        "qwen3_32b_awq_core_silver_evaluation_report": str(exp_dir / "04_evaluation/qwen3_32b_awq_core_silver_evaluation_report.md") if (exp_dir / "04_evaluation/qwen3_32b_awq_core_silver_evaluation_report.md").exists() else None,
        "qwen3_32b_awq_core_silver_metrics": str(exp_dir / "04_evaluation/qwen3_32b_awq_core_silver_metrics.json") if (exp_dir / "04_evaluation/qwen3_32b_awq_core_silver_metrics.json").exists() else None,
        "active_review_efficiency_report": str(exp_dir / "04_evaluation/active_review_efficiency_report.md") if (exp_dir / "04_evaluation/active_review_efficiency_report.md").exists() else None,
        "active_review_efficiency_metrics": str(exp_dir / "04_evaluation/active_review_efficiency_metrics.json") if (exp_dir / "04_evaluation/active_review_efficiency_metrics.json").exists() else None,
        "actual_llm_active_review_queue": str(exp_dir / "05_review/actual_llm_active_review_queue_P_cape_kg_actual.jsonl") if (exp_dir / "05_review/actual_llm_active_review_queue_P_cape_kg_actual.jsonl").exists() else None,
        "statistical_analysis_report": str(exp_dir / "04_evaluation/statistical_analysis_report.md") if (exp_dir / "04_evaluation/statistical_analysis_report.md").exists() else None,
        "statistical_analysis_metrics": str(exp_dir / "04_evaluation/statistical_analysis_metrics.json") if (exp_dir / "04_evaluation/statistical_analysis_metrics.json").exists() else None,
        "strict_json_diagnostics_report": str(exp_dir / "06_release/strict_json_diagnostics.md") if (exp_dir / "06_release/strict_json_diagnostics.md").exists() else None,
        "strict_json_diagnostics_json": str(exp_dir / "06_release/strict_json_diagnostics.json") if (exp_dir / "06_release/strict_json_diagnostics.json").exists() else None,
        "strict_json_reprompt_priority": str(exp_dir / "05_review/strict_json_reprompt_priority.csv") if (exp_dir / "05_review/strict_json_reprompt_priority.csv").exists() else None,
        "strict_json_contract_prompt": str(exp_dir / "02_schema/prompts/strict_json_contract.txt") if (exp_dir / "02_schema/prompts/strict_json_contract.txt").exists() else None,
        "public_synthetic_examples_summary": str(exp_dir / "06_release/public_synthetic_examples/synthetic_evaluation_summary.json") if (exp_dir / "06_release/public_synthetic_examples/synthetic_evaluation_summary.json").exists() else None,
        "public_synthetic_examples_readme": str(exp_dir / "06_release/public_synthetic_examples/README.md") if (exp_dir / "06_release/public_synthetic_examples/README.md").exists() else None,
        "human_return_apply_wrapper_script": str(Path("scripts/run_cape_human_return_apply.sh")) if Path("scripts/run_cape_human_return_apply.sh").exists() else None,
        "post_annotation_refresh_script": str(Path("scripts/run_cape_post_annotation_refresh.sh")) if Path("scripts/run_cape_post_annotation_refresh.sh").exists() else None,
        "submission_readiness_audit_report": str(exp_dir / "06_release/submission_readiness_audit.md") if (exp_dir / "06_release/submission_readiness_audit.md").exists() else None,
        "submission_readiness_audit_metrics": str(exp_dir / "06_release/submission_readiness_audit.json") if (exp_dir / "06_release/submission_readiness_audit.json").exists() else None,
        "method_module_coverage_report": str(exp_dir / "06_release/method_module_coverage.md") if (exp_dir / "06_release/method_module_coverage.md").exists() else None,
        "method_module_coverage_metrics": str(exp_dir / "06_release/method_module_coverage.json") if (exp_dir / "06_release/method_module_coverage.json").exists() else None,
        "human_gold_validation_report": str(exp_dir / "04_evaluation/human_gold_validation_report.md") if (exp_dir / "04_evaluation/human_gold_validation_report.md").exists() else None,
        "human_gold_evaluation_report": str(exp_dir / "04_evaluation/human_gold_evaluation_report.md") if (exp_dir / "04_evaluation/human_gold_evaluation_report.md").exists() else None,
        "human_gold_metrics": str(exp_dir / "04_evaluation/human_gold_metrics.json") if (exp_dir / "04_evaluation/human_gold_metrics.json").exists() else None,
        "mapping_review_manifest": str(exp_dir / "01_data/mapping_review/mapping_review_manifest.json") if (exp_dir / "01_data/mapping_review/mapping_review_manifest.json").exists() else None,
        "mapping_review_workbench": str(exp_dir / "01_data/mapping_review/mapping_review_workbench.html") if (exp_dir / "01_data/mapping_review/mapping_review_workbench.html").exists() else None,
        "mapping_expert_evaluation_report": str(exp_dir / "04_evaluation/mapping_expert_evaluation_report.md") if (exp_dir / "04_evaluation/mapping_expert_evaluation_report.md").exists() else None,
        "mapping_expert_metrics": str(exp_dir / "04_evaluation/mapping_expert_metrics.json") if (exp_dir / "04_evaluation/mapping_expert_metrics.json").exists() else None,
        "mapping_review_progress_report": str(exp_dir / "06_release/mapping_review_progress_report.md") if (exp_dir / "06_release/mapping_review_progress_report.md").exists() else None,
        "mapping_review_progress_summary": str(exp_dir / "06_release/mapping_review_progress_summary.json") if (exp_dir / "06_release/mapping_review_progress_summary.json").exists() else None,
        "mapping_review_priority_queue": str(exp_dir / "05_review/mapping_review_priority_queue.csv") if (exp_dir / "05_review/mapping_review_priority_queue.csv").exists() else None,
        "mapping_review_next_20_groups": str(exp_dir / "05_review/mapping_review_next_20_groups.csv") if (exp_dir / "05_review/mapping_review_next_20_groups.csv").exists() else None,
        "mapping_review_next_60_rows": str(exp_dir / "05_review/mapping_review_next_60_rows.csv") if (exp_dir / "05_review/mapping_review_next_60_rows.csv").exists() else None,
        "claim_gate_report": str(exp_dir / "06_release/claim_gate_report.md") if (exp_dir / "06_release/claim_gate_report.md").exists() else None,
        "claim_gate_metrics": str(exp_dir / "06_release/claim_gate_report.json") if (exp_dir / "06_release/claim_gate_report.json").exists() else None,
        "qwen3_32b_awq_readiness_report": str(exp_dir / "06_release/qwen3_32b_awq_readiness.md") if (exp_dir / "06_release/qwen3_32b_awq_readiness.md").exists() else None,
        "qwen3_32b_awq_readiness_json": str(exp_dir / "06_release/qwen3_32b_awq_readiness.json") if (exp_dir / "06_release/qwen3_32b_awq_readiness.json").exists() else None,
        "paper_tables_markdown": str(exp_dir / "06_release/paper_tables.md") if (exp_dir / "06_release/paper_tables.md").exists() else None,
        "paper_tables_latex": str(exp_dir / "06_release/paper_tables.tex") if (exp_dir / "06_release/paper_tables.tex").exists() else None,
        "eacl_plan_compliance_matrix": str(exp_dir / "06_release/eacl_plan_compliance_matrix.md") if (exp_dir / "06_release/eacl_plan_compliance_matrix.md").exists() else None,
        "eacl_plan_compliance_matrix_json": str(exp_dir / "06_release/eacl_plan_compliance_matrix.json") if (exp_dir / "06_release/eacl_plan_compliance_matrix.json").exists() else None,
        "release_bundle_manifest": str(exp_dir / "06_release/release_bundle_manifest.json") if (exp_dir / "06_release/release_bundle_manifest.json").exists() else None,
        "release_bundle_checksums": str(exp_dir / "06_release/release_bundle_checksums.sha256") if (exp_dir / "06_release/release_bundle_checksums.sha256").exists() else None,
        "release_bundle_safety_report": str(exp_dir / "06_release/release_bundle_safety_report.md") if (exp_dir / "06_release/release_bundle_safety_report.md").exists() else None,
        "claim_status": "actual_llm_runs_present_pending_human_gold_iaa_and_scoring",
    }
    write_json(exp_dir / "run_summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--kg-dir", default=str(DEFAULT_KG_DIR))
    parser.add_argument("--experiment-dir", default=str(DEFAULT_EXP_DIR))
    parser.add_argument("--sample-size", type=int, default=120)
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
