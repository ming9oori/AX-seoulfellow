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


def write_prompt_templates(out_dir):
    prompts = {
        "B0_plain_llm_triple_extraction.txt": "Extract subject-predicate-object triples from the chunk. Return JSON only.",
        "B1_predicate_constrained_llm.txt": "Extract triples using only the allowed predicates. Return JSON only with evidence sentence ids.",
        "B2_current_project_baseline.txt": "Extract Task Frames, then triples, then post-process into the Layer2 schema.",
        "B4_taxonomy_rag_baseline.txt": "Retrieve NCS/PCF/task taxonomy snippets, then extract schema-constrained triples with evidence.",
        "B5_procedural_prompt_baseline.txt": "Extract actions, actors, gateways, guard conditions, artifact flows, and temporal/logical dependencies.",
        "P_cape_kg.txt": "Use CQ-linked schema retrieval, procedural frame extraction, evidence-span constrained relation extraction, span verification, ontology validation, procedural consistency checks, and active review scoring.",
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
            "silver_candidate_edges": candidates[:50],
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


def write_reports(exp_dir, kg, chunks, ref_nodes, ref_edges, ref_evidence, metric_rows, cq_rows, mapping_rows, review_queue):
    exp_dir = Path(exp_dir)
    llm_raw_path = exp_dir / "45_llm_tool_extractions_raw.jsonl"
    llm_valid_path = exp_dir / "46_llm_tool_extractions_valid.jsonl"
    llm_report_path = exp_dir / "47_llm_extraction_quality_report.md"
    llm_smoke = None
    if llm_raw_path.exists() and llm_valid_path.exists():
        raw_rows = read_jsonl(llm_raw_path)
        valid_rows = read_jsonl(llm_valid_path)
        llm_smoke = {
            "raw_chunk_rows": len(raw_rows),
            "valid_chunk_rows": len(valid_rows),
            "valid_task_frames": sum(len(r.get("create_task_frame", [])) for r in valid_rows),
            "valid_procedural_relations": sum(len(r.get("add_procedural_relation", [])) for r in valid_rows),
            "raw_rows_with_parse_or_generation_errors": sum(1 for r in raw_rows if r.get("parse_error") or r.get("error")),
            "report_file": str(llm_report_path),
        }
    readiness = {
        "minimum_accept_checklist": [
            ("100+ chunk gold annotation", len(chunks) >= 100, "silver subset prepared; human gold pending"),
            ("500+ gold node/edge/evidence item", len(ref_edges) >= 500, "silver reference prepared; human adjudication pending"),
            ("2+ annotators and agreement", False, "requires human annotation"),
            ("B0/B1/B2 baseline completed", True, "proxy baselines completed; actual full LLM generations pending"),
            ("CAPE-KG proposed result completed", True, "silver/proxy proposed result completed"),
            ("3+ ablations completed", True, "proxy ablations completed"),
            ("error analysis table", True, "automatic error analysis generated"),
            ("public benchmark/subset experiment", False, "PAGED/Text2KGBench not yet run locally"),
            ("code/prompt/schema release plan", True, "prompt/schema/reproducibility package generated"),
            ("limitations section", True, "limitations generated"),
        ]
    }
    write_json(Path(exp_dir) / "06_release/paper_readiness_checklist.json", readiness)

    limitations = """# Limitations

This run is an EACL experiment scaffold and silver/proxy evaluation, not a
paper-claimable final result.

- The reference labels are derived from the current AX-EPAK KG and must be
  replaced or adjudicated by two human annotators.
- Baseline rows are deterministic proxies used to validate the metric pipeline.
  Actual B0/B1/B2/B4/B5 LLM generations must be run before making comparative
  claims.
- A small local Qwen3-8B smoke run may be present in this package, but it is
  only an execution-path check unless expanded to the full experimental design.
- PAGED/Text2KGBench cross-benchmark experiments are represented in the plan
  but are not completed in this local run.
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
claims until the silver reference is replaced with human gold and actual LLM
baseline generations.

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
    report += f"\n## Active Review\n\n- Review queue items: {len(review_queue)}\n- Highest priority: {review_queue[0]['review_priority'] if review_queue else 0}\n"
    if llm_smoke:
        report += "\n## Local LLM Smoke Run\n\n"
        report += f"- Raw chunk rows: {llm_smoke['raw_chunk_rows']}\n"
        report += f"- Valid task frames: {llm_smoke['valid_task_frames']}\n"
        report += f"- Valid procedural relations: {llm_smoke['valid_procedural_relations']}\n"
        report += f"- Raw rows with parse/generation errors: {llm_smoke['raw_rows_with_parse_or_generation_errors']}\n"
        report += f"- Report: `{llm_smoke['report_file']}`\n"
        report += "\nThis is a smoke test of the local Qwen3-8B extraction path, not a full baseline result.\n"
    report += "\n## Required Next Step\n\nHuman annotation remains the gating step for EACL-ready evidence.\n"
    write_text(exp_dir / "07_reports/final_eacl_experiment_report.md", report)

    error_table = "# Error Analysis\n\n"
    for row in metric_rows:
        error_table += f"- {row['condition']}: FP={row['false_positive']}, FN={row['false_negative']}, ontology_violations={row['ontology_violation_count']}, unsupported_rate={row['unsupported_edge_rate']}\n"
    write_text(exp_dir / "07_reports/error_analysis.md", error_table)

    reproducibility = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_kg_summary": kg["summary"],
        "experiment_dir": str(exp_dir),
        "evaluation_chunk_count": len(chunks),
        "silver_reference_edge_count": len(ref_edges),
        "commands": [
            "bash scripts/run_ax_epak_preprocessed.sh",
            f"python3 scripts/build_cape_kg_eacl_experiment.py --kg-dir {DEFAULT_KG_DIR} --experiment-dir {DEFAULT_EXP_DIR} --sample-size 120",
            "CUDA_VISIBLE_DEVICES=0 /home/minjoo/tdpo2_aaai2027/.venv_tdpo2/bin/python scripts/run_cep_onto_llm_extraction.py --output-dir experiments/cape_kg_eacl_20260627 --chunk-file 01_data/evaluation_chunks.jsonl --max-chunks 10",
        ],
        "llm_smoke": llm_smoke,
        "claim_status": "silver_proxy_only_pending_human_gold_and_actual_llm_baselines",
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
    review_queue = build_active_review_queue(predictions["P_cape_kg_silver"], ref_edges)
    annotation_rows, annotation_csv = build_annotation_templates(chunks, ref_edges)

    requirements = {
        "source_plan": "AX_EACL_submission_review_revised_plan.md",
        "method_name": "CAPE-KG",
        "requirements": [
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
        ],
        "status": "silver_proxy_experiment_generated_pending_human_gold_and_actual_llm_baselines",
    }
    write_json(exp_dir / "00_plan/requirements_matrix.json", requirements)
    write_text(
        exp_dir / "00_plan/requirements_matrix.md",
        "# Requirements Matrix\n\n" + "\n".join(f"- {r}" for r in requirements["requirements"]) + "\n",
    )

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
    write_csv(exp_dir / "05_review/active_review_queue.csv", review_queue)
    write_jsonl(exp_dir / "05_review/active_review_queue.jsonl", review_queue)

    # Report slices.
    write_text(
        exp_dir / "04_evaluation/evidence_grounding_report.md",
        "# Evidence Grounding Report\n\n"
        + "\n".join(f"- {r['condition']}: EM={r['evidence_exact_match']}, IoU={r['evidence_iou_mean']}, unsupported={r['unsupported_edge_rate']}" for r in metric_rows)
        + "\n",
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
        "# Mapping Downstream Report\n\n"
        + "\n".join(f"- {r['standard']}: coverage={r['coverage']}, top5={r['top5_candidate_rows']}, P@5={r['p_at_5']}" for r in mapping_rows)
        + "\n",
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
        "llm_smoke_raw_file": str(exp_dir / "45_llm_tool_extractions_raw.jsonl") if (exp_dir / "45_llm_tool_extractions_raw.jsonl").exists() else None,
        "llm_smoke_valid_file": str(exp_dir / "46_llm_tool_extractions_valid.jsonl") if (exp_dir / "46_llm_tool_extractions_valid.jsonl").exists() else None,
        "claim_status": "silver_proxy_only_pending_human_gold_and_actual_llm_baselines",
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
