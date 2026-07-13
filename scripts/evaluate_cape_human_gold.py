#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Validate adjudicated CAPE-KG gold labels and score actual LLM outputs.

This script is intentionally conservative: pending adjudication rows are not
treated as gold, and paper-claimable metrics are emitted only for chunks whose
adjudication status is complete.
"""

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_EXP_DIR = Path("experiments/cape_kg_eacl_20260627")
DEFAULT_VALID_FILES = [
    "49_qwen3_8b_condition_baselines_120_valid.jsonl",
    "49_qwen3_8b_b2_b4_condition_baselines_120_valid.jsonl",
    "49_qwen3_8b_cape_ablation_120_valid.jsonl",
]

COMPLETED_ADJUDICATION_STATUSES = {
    "adjudicated",
    "completed",
    "complete",
    "final",
    "accepted",
    "no_disagreement_adjudicated",
}
REJECTED_EDGE_DECISIONS = {"reject", "rejected", "unsupported", "remove", "removed"}
PROCEDURAL_EDGE_TYPES = {
    "HAS_STEP",
    "PRECEDES",
    "BRANCHES_TO",
    "HAS_GUARD_CONDITION",
    "FEEDS_INTO",
    "USED_AS_INPUT_FOR",
    "HAS_DECISION_GATEWAY",
    "HAS_REVIEW_CHECKPOINT",
}
CQ_TARGETS = [
    ("CQ1", {"HAS_STEP", "PRECEDES"}),
    ("CQ2", {"USES_INPUT"}),
    ("CQ3", {"PRODUCES"}),
    ("CQ4", {"PERFORMED_BY"}),
    ("CQ5", {"HAS_DECISION_GATEWAY"}),
    ("CQ6", {"HAS_GUARD_CONDITION"}),
    ("CQ7", {"FEEDS_INTO", "USED_AS_INPUT_FOR"}),
    ("CQ8", {"HAS_REVIEW_CHECKPOINT"}),
    ("CQ9", {"HAS_PRINCIPLE"}),
    ("CQ10", {"EVIDENCED_BY"}),
    ("CQ11", {"REQUIRES_CAPABILITY", "CANDIDATE_ALIGNS_WITH"}),
    ("CQ12", {"PROCESS_CONTEXT", "CANDIDATE_ALIGNS_WITH"}),
]

METRIC_FIELDNAMES = [
    "source_file",
    "condition",
    "rows",
    "chunks",
    "raw_rows",
    "parse_or_generation_error_rows",
    "partial_json_repaired_rows",
    "pred_edges",
    "pred_nodes",
    "pred_triples",
    "pred_mappings",
    "gold_edge_instances",
    "gold_node_instances",
    "gold_evidence_instances",
    "edge_exact_precision",
    "edge_exact_recall",
    "edge_exact_f1",
    "edge_exact_tp",
    "predicate_precision",
    "predicate_recall",
    "predicate_f1",
    "node_label_precision",
    "node_label_recall",
    "node_label_f1",
    "evidence_precision",
    "evidence_recall",
    "evidence_f1",
    "evidence_exact_match",
    "unsupported_edge_rate",
    "edge_evidence_attachment_rate",
    "schema_edge_rate",
    "ontology_conformance",
    "ontology_violation_count",
    "procedural_edge_count",
    "procedural_consistency",
    "procedural_violation_count",
    "precedence_cycle_count",
    "cq_gold_applicable_count",
    "cq_answered_count",
    "cq_answerability",
    "mapping_evidence_attachment_rate",
    "claim_status",
]


def read_json(path, default=None):
    path = Path(path)
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path):
    rows = []
    issues = []
    path = Path(path)
    if not path.exists():
        issues.append(issue("error", "missing_file", f"Missing JSONL file: {path}"))
        return rows, issues
    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                issues.append(issue("error", "json_parse_error", str(exc), line=line_no))
                continue
            row["_line_no"] = line_no
            rows.append(row)
    return rows, issues


def write_json(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_csv(path, rows, fieldnames):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({name: row.get(name, "") for name in fieldnames})


def write_text(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def issue(level, code, message, chunk_id=None, line=None):
    row = {"level": level, "code": code, "message": message}
    if chunk_id:
        row["chunk_id"] = chunk_id
    if line:
        row["line"] = line
    return row


def norm_label(value):
    value = str(value or "").strip().lower()
    value = re.sub(r"\s+", "", value)
    value = re.sub(r"[`'\"“”‘’()\[\]{}<>:;,.!?/\\|_-]+", "", value)
    return value


def norm_text(value):
    return " ".join(str(value or "").strip().split()).lower()


def norm_predicate(value):
    return str(value or "").strip().upper()


def norm_evidence_id(value):
    value = str(value or "").strip()
    if value.startswith("EA-"):
        value = value[3:]
    return value


def status_value(row):
    return norm_text(row.get("adjudication_status") or row.get("annotation_status"))


def is_completed_adjudication(row):
    return status_value(row) in COMPLETED_ADJUDICATION_STATUSES


def edge_decision(edge):
    return norm_text(edge.get("decision") or edge.get("adjudication_decision") or edge.get("status"))


def is_rejected_gold_edge(edge):
    return edge_decision(edge) in REJECTED_EDGE_DECISIONS


def prf(tp, fp, fn):
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "precision": round(precision, 6),
        "recall": round(recall, 6),
        "f1": round(f1, 6),
    }


def counter_prf(pred_counter, gold_counter):
    tp = sum((pred_counter & gold_counter).values())
    pred_total = sum(pred_counter.values())
    gold_total = sum(gold_counter.values())
    scores = prf(tp, pred_total - tp, gold_total - tp)
    scores.update({"tp": tp, "fp": pred_total - tp, "fn": gold_total - tp})
    return scores


def load_schema(exp_dir):
    schema = read_json(Path(exp_dir) / "02_schema/cape_schema.json", default={}) or {}
    node_types = set(schema.get("node_types") or [])
    edge_types = set(schema.get("edge_types") or [])
    domain_range = {}
    for predicate, spec in (schema.get("domain_range") or {}).items():
        domain_range[norm_predicate(predicate)] = {
            "subject_types": set(spec.get("subject_types") or []),
            "object_types": set(spec.get("object_types") or []),
        }
    return {
        "node_types": node_types,
        "edge_types": edge_types,
        "domain_range": domain_range,
    }


def load_chunk_context(exp_dir):
    rows, issues = read_jsonl(Path(exp_dir) / "01_data/evaluation_chunks.jsonl")
    chunks = {}
    for row in rows:
        chunk_id = row.get("chunk_id")
        if not chunk_id:
            continue
        sentence_ids = {norm_evidence_id(v) for v in row.get("sentence_ids") or []}
        chunk_text = row.get("text") or row.get("chunk_text") or ""
        sentence_texts = {}
        for offset in row.get("sentence_offsets") or []:
            sentence_id = norm_evidence_id(offset.get("sentence_id"))
            if not sentence_id:
                continue
            try:
                start = int(offset.get("chunk_char_start"))
                end = int(offset.get("chunk_char_end"))
            except (TypeError, ValueError):
                continue
            if 0 <= start <= end <= len(chunk_text):
                sentence_texts[sentence_id] = chunk_text[start:end]
        chunks[chunk_id] = {
            "line_no": row.get("_line_no"),
            "sentence_ids": sentence_ids,
            "sentence_texts": sentence_texts,
            "text": chunk_text,
        }
    return chunks, issues


def evidence_keys_from_item(item):
    keys = set()
    if not isinstance(item, dict):
        return keys
    anchor_ids = item.get("evidence_anchor_ids") or []
    if not isinstance(anchor_ids, list):
        anchor_ids = []
    for value in anchor_ids:
        normalized = norm_evidence_id(value)
        if normalized:
            keys.add(normalized)
    spans = item.get("evidence_spans") or []
    if not isinstance(spans, list):
        spans = []
    for span in spans:
        if not isinstance(span, dict):
            continue
        normalized = norm_evidence_id(span.get("evidence_anchor_id") or span.get("sentence_id"))
        if normalized:
            keys.add(normalized)
    return keys


def evidence_text_spans(item):
    spans = []
    if not isinstance(item, dict):
        return spans
    evidence_spans = item.get("evidence_spans") or []
    if not isinstance(evidence_spans, list):
        evidence_spans = []
    for span in evidence_spans:
        if not isinstance(span, dict):
            continue
        text = norm_text(span.get("text"))
        if text:
            spans.append(text)
    return spans


def chunk_sentence_text(chunk_context, chunk_id, sentence_id):
    sentence_id = norm_evidence_id(sentence_id)
    if not sentence_id:
        return ""
    return (chunk_context.get(chunk_id, {}).get("sentence_texts") or {}).get(sentence_id, "")


def validate_gold_evidence_payload(row, item, chunk_context, issues, index, item_kind):
    chunk_id = row.get("chunk_id")
    line_no = row.get("_line_no")
    label = "Gold node" if item_kind == "gold_node" else "Gold item"
    evidence_ids = set()
    text_spans = []

    def add_anchor(value, anchor_index, field_label):
        normalized = norm_evidence_id(value)
        if normalized:
            evidence_ids.add(normalized)
            return
        issues.append(
            issue(
                "error",
                f"{item_kind}_empty_evidence_anchor_id",
                f"{label} {index} {field_label}[{anchor_index}] is empty.",
                chunk_id,
                line_no,
            )
        )

    def validate_span(span, span_index, field_label):
        if not isinstance(span, dict):
            issues.append(
                issue(
                    "error",
                    f"{item_kind}_evidence_span_not_object",
                    f"{label} {index} {field_label}[{span_index}] must be a JSON object.",
                    chunk_id,
                    line_no,
                )
            )
            return
        span_id = norm_evidence_id(span.get("evidence_anchor_id") or span.get("sentence_id"))
        raw_span_text = str(span.get("text") or "")
        span_text = norm_text(raw_span_text)
        if span_id:
            evidence_ids.add(span_id)
        if span_text:
            text_spans.append(span_text)
        if not span_id and not span_text:
            issues.append(
                issue(
                    "error",
                    f"{item_kind}_empty_evidence_span",
                    f"{label} {index} {field_label}[{span_index}] has neither text nor sentence/evidence id.",
                    chunk_id,
                    line_no,
                )
            )

        start_raw = span.get("start_char")
        end_raw = span.get("end_char")
        has_start = start_raw not in (None, "")
        has_end = end_raw not in (None, "")
        if has_start != has_end:
            issues.append(
                issue(
                    "error",
                    f"{item_kind}_incomplete_evidence_span_offsets",
                    f"{label} {index} {field_label}[{span_index}] must provide both start_char and end_char.",
                    chunk_id,
                    line_no,
                )
            )
        elif has_start and has_end:
            try:
                start = int(start_raw)
                end = int(end_raw)
            except (TypeError, ValueError):
                issues.append(
                    issue(
                        "error",
                        f"{item_kind}_invalid_evidence_span_offsets",
                        f"{label} {index} {field_label}[{span_index}] offsets must be integers.",
                        chunk_id,
                        line_no,
                    )
                )
                return
            if start < 0 or end < 0 or start > end:
                issues.append(
                    issue(
                        "error",
                        f"{item_kind}_invalid_evidence_span_offsets",
                        f"{label} {index} {field_label}[{span_index}] offsets must satisfy 0 <= start_char <= end_char.",
                        chunk_id,
                        line_no,
                    )
                )
            elif span_id:
                sentence_text = chunk_sentence_text(chunk_context, chunk_id, span_id)
                if sentence_text:
                    if end > len(sentence_text):
                        issues.append(
                            issue(
                                "error",
                                f"{item_kind}_evidence_span_offsets_outside_sentence",
                                f"{label} {index} {field_label}[{span_index}] offsets exceed sentence `{span_id}` length.",
                                chunk_id,
                                line_no,
                            )
                        )
                    elif raw_span_text and sentence_text[start:end] != raw_span_text:
                        issues.append(
                            issue(
                                "error",
                                f"{item_kind}_evidence_span_text_mismatch",
                                f"{label} {index} {field_label}[{span_index}] text does not match sentence `{span_id}` at start_char/end_char.",
                                chunk_id,
                                line_no,
                            )
                        )
                    elif not raw_span_text:
                        issues.append(
                            issue(
                                "error",
                                f"{item_kind}_evidence_span_offsets_without_text",
                                f"{label} {index} {field_label}[{span_index}] provides offsets but no text to verify.",
                                chunk_id,
                                line_no,
                            )
                        )

    def validate_container(container, field_prefix=""):
        if not isinstance(container, dict):
            return
        anchor_values = container.get("evidence_anchor_ids")
        if anchor_values is not None and not isinstance(anchor_values, list):
            issues.append(
                issue(
                    "error",
                    f"{item_kind}_evidence_anchor_ids_not_list",
                    f"{label} {index} {field_prefix}evidence_anchor_ids must be a list.",
                    chunk_id,
                    line_no,
                )
            )
        elif isinstance(anchor_values, list):
            for anchor_index, value in enumerate(anchor_values, start=1):
                add_anchor(value, anchor_index, f"{field_prefix}evidence_anchor_ids")

        span_values = container.get("evidence_spans")
        if span_values is None and any(key in container for key in ("evidence_anchor_id", "sentence_id", "text", "start_char", "end_char")):
            span_values = [container]
        if span_values is not None and not isinstance(span_values, list):
            issues.append(
                issue(
                    "error",
                    f"{item_kind}_evidence_spans_not_list",
                    f"{label} {index} {field_prefix}evidence_spans must be a list.",
                    chunk_id,
                    line_no,
                )
            )
        elif isinstance(span_values, list):
            for span_index, span in enumerate(span_values, start=1):
                validate_span(span, span_index, f"{field_prefix}evidence_spans")

    validate_container(item)
    embedded = item.get("evidence") if isinstance(item, dict) else None
    if embedded is not None:
        if isinstance(embedded, dict):
            validate_container(embedded, "evidence.")
        elif isinstance(embedded, list):
            for embedded_index, value in enumerate(embedded, start=1):
                if isinstance(value, dict):
                    validate_span(value, embedded_index, "evidence")
                elif norm_evidence_id(value):
                    add_anchor(value, embedded_index, "evidence")
                elif norm_text(value):
                    text_spans.append(norm_text(value))
                else:
                    issues.append(
                        issue(
                            "error",
                            f"{item_kind}_empty_evidence_item",
                            f"{label} {index} evidence[{embedded_index}] is empty.",
                            chunk_id,
                            line_no,
                        )
                    )
        elif norm_text(embedded):
            text_spans.append(norm_text(embedded))
        else:
            issues.append(
                issue(
                    "error",
                    f"{item_kind}_evidence_invalid_type",
                    f"{label} {index} evidence must be a non-empty string, list, or object.",
                    chunk_id,
                    line_no,
                )
            )

    if not evidence_ids and not text_spans:
        issues.append(issue("error", f"{item_kind}_missing_evidence", f"{label} {index} has no evidence.", chunk_id, line_no))
    if text_spans and not evidence_ids:
        issues.append(
            issue(
                "warning",
                f"{item_kind}_text_span_without_id",
                f"{label} {index} has text evidence but no sentence/evidence id.",
                chunk_id,
                line_no,
            )
        )

    allowed_sentence_ids = chunk_context.get(chunk_id, {}).get("sentence_ids") or set()
    for evidence_id in sorted(evidence_ids):
        if allowed_sentence_ids and evidence_id not in allowed_sentence_ids:
            issues.append(
                issue(
                    "error",
                    f"{item_kind}_evidence_outside_chunk",
                    f"{label} {index} evidence `{evidence_id}` is not in this chunk.",
                    chunk_id,
                    line_no,
                )
            )


def gold_edge_label(edge, side):
    if side == "source":
        return edge.get("source_label") or edge.get("subject") or edge.get("source_id")
    return edge.get("target_label") or edge.get("object") or edge.get("target_id")


def gold_edge_type(edge, side):
    if side == "source":
        return edge.get("source_type") or edge.get("subject_type")
    return edge.get("target_type") or edge.get("object_type")


def gold_edge_key(chunk_id, edge):
    return (
        chunk_id,
        norm_label(gold_edge_label(edge, "source")),
        norm_predicate(edge.get("predicate") or edge.get("edge_type")),
        norm_label(gold_edge_label(edge, "target")),
    )


def pred_edge_key(chunk_id, edge):
    return (
        chunk_id,
        norm_label(edge.get("subject") or edge.get("source_label") or edge.get("source")),
        norm_predicate(edge.get("predicate") or edge.get("edge_type")),
        norm_label(edge.get("object") or edge.get("target_label") or edge.get("target")),
    )


def gold_node_key(chunk_id, node):
    return (
        chunk_id,
        norm_label(node.get("label") or node.get("node_id")),
    )


def endpoint_node_keys(chunk_id, edge):
    keys = []
    source = norm_label(gold_edge_label(edge, "source"))
    target = norm_label(gold_edge_label(edge, "target"))
    if source:
        keys.append((chunk_id, source))
    if target:
        keys.append((chunk_id, target))
    return keys


def pred_node_keys_from_edge(chunk_id, edge):
    keys = []
    source = norm_label(edge.get("subject") or edge.get("source_label") or edge.get("source"))
    target = norm_label(edge.get("object") or edge.get("target_label") or edge.get("target"))
    if source:
        keys.append((chunk_id, source))
    if target:
        keys.append((chunk_id, target))
    return keys


def pred_edge_label(edge, side):
    if side == "source":
        return edge.get("subject") or edge.get("source_label") or edge.get("source")
    return edge.get("object") or edge.get("target_label") or edge.get("target")


def pred_edge_type(edge, side):
    if side == "source":
        return edge.get("subject_type") or edge.get("source_type")
    return edge.get("object_type") or edge.get("target_type")


def edge_schema_valid(predicate, subject_type, object_type, schema):
    predicate = norm_predicate(predicate)
    if not predicate or predicate not in schema["edge_types"]:
        return False
    if predicate not in schema["domain_range"]:
        return True
    spec = schema["domain_range"][predicate]
    subject_types = spec["subject_types"]
    object_types = spec["object_types"]
    subject_ok = "Any" in subject_types or not subject_types or (subject_type and subject_type in subject_types)
    object_ok = "Any" in object_types or not object_types or (object_type and object_type in object_types)
    return bool(subject_ok and object_ok)


def pred_edge_record(chunk_id, edge):
    return {
        "chunk_id": chunk_id,
        "subject": norm_label(pred_edge_label(edge, "source")),
        "object": norm_label(pred_edge_label(edge, "target")),
        "predicate": norm_predicate(edge.get("predicate") or edge.get("edge_type")),
        "subject_type": pred_edge_type(edge, "source"),
        "object_type": pred_edge_type(edge, "target"),
    }


def has_precedence_cycle(records):
    graph = defaultdict(set)
    for record in records:
        if record["predicate"] != "PRECEDES" or not record["subject"] or not record["object"]:
            continue
        graph[record["subject"]].add(record["object"])

    visiting = set()
    visited = set()

    def visit(node):
        if node in visiting:
            return True
        if node in visited:
            return False
        visiting.add(node)
        for nxt in graph.get(node, set()):
            if visit(nxt):
                return True
        visiting.remove(node)
        visited.add(node)
        return False

    return any(visit(node) for node in list(graph))


def procedural_metrics(records, schema):
    procedural_records = [record for record in records if record["predicate"] in PROCEDURAL_EDGE_TYPES]
    procedural_count = len(procedural_records)
    if not procedural_count:
        return {
            "procedural_edge_count": 0,
            "procedural_consistency": 0.0,
            "procedural_violation_count": 0,
            "precedence_cycle_count": 0,
        }

    violation_count = 0
    for record in procedural_records:
        if not edge_schema_valid(record["predicate"], record["subject_type"], record["object_type"], schema):
            violation_count += 1

    cycle_count = 0
    for _, chunk_records in group_records_by_chunk(procedural_records).items():
        if has_precedence_cycle(chunk_records):
            cycle_count += 1
    violation_count += cycle_count

    consistency = max(0.0, 1.0 - (violation_count / procedural_count))
    return {
        "procedural_edge_count": procedural_count,
        "procedural_consistency": round(consistency, 6),
        "procedural_violation_count": violation_count,
        "precedence_cycle_count": cycle_count,
    }


def group_records_by_chunk(records):
    by_chunk = defaultdict(list)
    for record in records:
        by_chunk[record["chunk_id"]].append(record)
    return by_chunk


def cq_answerability(pred_predicates, gold_predicates):
    pred_set = {predicate for _, predicate in pred_predicates}
    gold_set = {predicate for _, predicate in gold_predicates}
    applicable = 0
    answered = 0
    for _, predicates in CQ_TARGETS:
        if gold_set & predicates:
            applicable += 1
            if pred_set & predicates:
                answered += 1
    score = answered / applicable if applicable else 0.0
    return {
        "cq_gold_applicable_count": applicable,
        "cq_answered_count": answered,
        "cq_answerability": round(score, 6),
    }


def validate_node(row, node, schema, issues, index, chunk_context=None):
    chunk_id = row.get("chunk_id")
    line_no = row.get("_line_no")
    if not isinstance(node, dict):
        issues.append(issue("error", "gold_node_not_object", f"Gold node {index} must be a JSON object.", chunk_id, line_no))
        return
    node_type = node.get("type")
    label = node.get("label") or node.get("node_id")
    if not label:
        issues.append(issue("error", "gold_node_missing_label", f"Gold node {index} has no label.", chunk_id, line_no))
    if node_type and schema["node_types"] and node_type not in schema["node_types"]:
        issues.append(
            issue(
                "error",
                "gold_node_unknown_type",
                f"Gold node {index} uses unknown type `{node_type}`.",
                chunk_id,
                line_no,
            )
        )
    validate_gold_evidence_payload(row, node, chunk_context or {}, issues, index, "gold_node")


def validate_edge(row, edge, schema, chunk_context, issues, index):
    chunk_id = row.get("chunk_id")
    line_no = row.get("_line_no")
    if not isinstance(edge, dict):
        issues.append(issue("error", "gold_edge_not_object", f"Gold edge {index} must be a JSON object.", chunk_id, line_no))
        return
    predicate = norm_predicate(edge.get("predicate") or edge.get("edge_type"))
    source_label = gold_edge_label(edge, "source")
    target_label = gold_edge_label(edge, "target")
    source_type = gold_edge_type(edge, "source")
    target_type = gold_edge_type(edge, "target")

    if is_rejected_gold_edge(edge):
        issues.append(issue("warning", "rejected_edge_inside_gold", f"Gold edge {index} is marked rejected.", chunk_id, line_no))
        return
    if not source_label:
        issues.append(issue("error", "gold_edge_missing_source", f"Gold edge {index} has no source label/id.", chunk_id, line_no))
    if not target_label:
        issues.append(issue("error", "gold_edge_missing_target", f"Gold edge {index} has no target label/id.", chunk_id, line_no))
    if not predicate:
        issues.append(issue("error", "gold_edge_missing_predicate", f"Gold edge {index} has no predicate.", chunk_id, line_no))
    elif schema["edge_types"] and predicate not in schema["edge_types"]:
        issues.append(issue("error", "gold_edge_unknown_predicate", f"Gold edge {index} uses unknown predicate `{predicate}`.", chunk_id, line_no))

    if predicate in schema["domain_range"]:
        spec = schema["domain_range"][predicate]
        subject_types = spec["subject_types"]
        object_types = spec["object_types"]
        if source_type and "Any" not in subject_types and subject_types and source_type not in subject_types:
            issues.append(
                issue(
                    "error",
                    "gold_edge_domain_violation",
                    f"Gold edge {index} predicate `{predicate}` does not allow subject type `{source_type}`.",
                    chunk_id,
                    line_no,
                )
            )
        if target_type and "Any" not in object_types and object_types and target_type not in object_types:
            issues.append(
                issue(
                    "error",
                    "gold_edge_range_violation",
                    f"Gold edge {index} predicate `{predicate}` does not allow target type `{target_type}`.",
                    chunk_id,
                    line_no,
                )
            )

    anchor_values = edge.get("evidence_anchor_ids")
    if anchor_values is not None and not isinstance(anchor_values, list):
        issues.append(
            issue(
                "error",
                "gold_edge_evidence_anchor_ids_not_list",
                f"Gold edge {index} evidence_anchor_ids must be a list.",
                chunk_id,
                line_no,
            )
        )
    elif isinstance(anchor_values, list):
        for anchor_index, value in enumerate(anchor_values, start=1):
            if not norm_evidence_id(value):
                issues.append(
                    issue(
                        "error",
                        "gold_edge_empty_evidence_anchor_id",
                        f"Gold edge {index} evidence_anchor_ids[{anchor_index}] is empty.",
                        chunk_id,
                        line_no,
                    )
                )

    span_values = edge.get("evidence_spans")
    if span_values is not None and not isinstance(span_values, list):
        issues.append(
            issue(
                "error",
                "gold_edge_evidence_spans_not_list",
                f"Gold edge {index} evidence_spans must be a list.",
                chunk_id,
                line_no,
            )
        )
    elif isinstance(span_values, list):
        for span_index, span in enumerate(span_values, start=1):
            if not isinstance(span, dict):
                issues.append(
                    issue(
                        "error",
                        "gold_edge_evidence_span_not_object",
                        f"Gold edge {index} evidence_spans[{span_index}] must be a JSON object.",
                        chunk_id,
                        line_no,
                    )
                )
                continue
            span_id = norm_evidence_id(span.get("evidence_anchor_id") or span.get("sentence_id"))
            raw_span_text = str(span.get("text") or "")
            span_text = norm_text(raw_span_text)
            if not span_id and not span_text:
                issues.append(
                    issue(
                        "error",
                        "gold_edge_empty_evidence_span",
                        f"Gold edge {index} evidence_spans[{span_index}] has neither text nor sentence/evidence id.",
                        chunk_id,
                        line_no,
                    )
                )

            start_raw = span.get("start_char")
            end_raw = span.get("end_char")
            has_start = start_raw not in (None, "")
            has_end = end_raw not in (None, "")
            if has_start != has_end:
                issues.append(
                    issue(
                        "error",
                        "gold_edge_incomplete_evidence_span_offsets",
                        f"Gold edge {index} evidence_spans[{span_index}] must provide both start_char and end_char.",
                        chunk_id,
                        line_no,
                    )
                )
            elif has_start and has_end:
                try:
                    start = int(start_raw)
                    end = int(end_raw)
                except (TypeError, ValueError):
                    issues.append(
                        issue(
                            "error",
                            "gold_edge_invalid_evidence_span_offsets",
                            f"Gold edge {index} evidence_spans[{span_index}] offsets must be integers.",
                            chunk_id,
                            line_no,
                        )
                    )
                else:
                    if start < 0 or end < 0 or start > end:
                        issues.append(
                            issue(
                                "error",
                                "gold_edge_invalid_evidence_span_offsets",
                                f"Gold edge {index} evidence_spans[{span_index}] offsets must satisfy 0 <= start_char <= end_char.",
                                chunk_id,
                                line_no,
                            )
                        )
                    elif span_id:
                        sentence_text = chunk_sentence_text(chunk_context, chunk_id, span_id)
                        if sentence_text:
                            if end > len(sentence_text):
                                issues.append(
                                    issue(
                                        "error",
                                        "gold_edge_evidence_span_offsets_outside_sentence",
                                        f"Gold edge {index} evidence_spans[{span_index}] offsets exceed sentence `{span_id}` length.",
                                        chunk_id,
                                        line_no,
                                    )
                                )
                            elif raw_span_text and sentence_text[start:end] != raw_span_text:
                                issues.append(
                                    issue(
                                        "error",
                                        "gold_edge_evidence_span_text_mismatch",
                                        f"Gold edge {index} evidence_spans[{span_index}] text does not match sentence `{span_id}` at start_char/end_char.",
                                        chunk_id,
                                        line_no,
                                    )
                                )
                            elif not raw_span_text:
                                issues.append(
                                    issue(
                                        "error",
                                        "gold_edge_evidence_span_offsets_without_text",
                                        f"Gold edge {index} evidence_spans[{span_index}] provides offsets but no text to verify.",
                                        chunk_id,
                                        line_no,
                                    )
                                )

    evidence_ids = evidence_keys_from_item(edge)
    text_spans = evidence_text_spans(edge)
    if not evidence_ids and not text_spans:
        issues.append(issue("error", "gold_edge_missing_evidence", f"Gold edge {index} has no evidence.", chunk_id, line_no))
    if text_spans and not evidence_ids:
        issues.append(
            issue(
                "warning",
                "gold_edge_text_span_without_id",
                f"Gold edge {index} has text evidence but no sentence/evidence id.",
                chunk_id,
                line_no,
            )
        )

    allowed_sentence_ids = chunk_context.get(chunk_id, {}).get("sentence_ids") or set()
    for evidence_id in sorted(evidence_ids):
        if allowed_sentence_ids and evidence_id not in allowed_sentence_ids:
            issues.append(
                issue(
                    "error",
                    "gold_edge_evidence_outside_chunk",
                    f"Gold edge {index} evidence `{evidence_id}` is not in this chunk.",
                    chunk_id,
                    line_no,
                )
            )


def validate_adjudication(rows, read_issues, schema, chunk_context, adjudication_file):
    issues = list(read_issues)
    status_counts = Counter()
    seen_chunks = Counter()
    completed_rows = []
    explicit_node_count = 0
    derived_node_keys = Counter()
    edge_count = 0
    evidence_count = 0

    for row in rows:
        chunk_id = row.get("chunk_id")
        line_no = row.get("_line_no")
        if not chunk_id:
            issues.append(issue("error", "missing_chunk_id", "Adjudication row has no chunk_id.", line=line_no))
            continue
        seen_chunks[chunk_id] += 1
        if chunk_id not in chunk_context:
            issues.append(issue("error", "unknown_chunk_id", "Adjudication row chunk_id is not in evaluation set.", chunk_id, line_no))
        status_counts[status_value(row) or "missing"] += 1
        if not is_completed_adjudication(row):
            continue

        completed_rows.append(row)
        nodes = row.get("adjudicated_gold_nodes") or row.get("gold_nodes") or []
        edges = row.get("adjudicated_gold_edges") or row.get("gold_edges") or []
        if not isinstance(nodes, list):
            issues.append(issue("error", "gold_nodes_not_list", "Gold nodes must be a list.", chunk_id, line_no))
            nodes = []
        if not isinstance(edges, list):
            issues.append(issue("error", "gold_edges_not_list", "Gold edges must be a list.", chunk_id, line_no))
            edges = []
        if not nodes and not edges:
            issues.append(issue("warning", "completed_chunk_without_gold_items", "Completed chunk has no gold nodes or edges.", chunk_id, line_no))

        edge_keys = Counter()
        for index, node in enumerate(nodes, start=1):
            validate_node(row, node, schema, issues, index, chunk_context)
            if not isinstance(node, dict):
                continue
            key = gold_node_key(chunk_id, node)
            if key[1]:
                derived_node_keys[key] += 1
                explicit_node_count += 1
        for index, edge in enumerate(edges, start=1):
            validate_edge(row, edge, schema, chunk_context, issues, index)
            if not isinstance(edge, dict):
                continue
            if is_rejected_gold_edge(edge):
                continue
            key = gold_edge_key(chunk_id, edge)
            if all(key):
                edge_keys[key] += 1
            for node_key in endpoint_node_keys(chunk_id, edge):
                derived_node_keys[node_key] += 1
            edge_count += 1
            evidence_count += len(evidence_keys_from_item(edge)) + len(evidence_text_spans(edge))
        for key, count in edge_keys.items():
            if count > 1:
                issues.append(issue("warning", "duplicate_gold_edge", f"Duplicate gold edge appears {count} times.", chunk_id, line_no))

    for chunk_id, count in seen_chunks.items():
        if count > 1:
            issues.append(issue("error", "duplicate_adjudication_chunk", f"Chunk appears {count} times in adjudication file.", chunk_id))

    error_count = sum(1 for item in issues if item["level"] == "error")
    warning_count = sum(1 for item in issues if item["level"] == "warning")
    gold_item_count = len(derived_node_keys) + edge_count + evidence_count
    completed_count = len(completed_rows)
    if completed_count == 0:
        status = "pending_human_adjudication"
    elif error_count:
        status = "validation_errors"
    else:
        status = "valid_adjudicated_gold"

    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "adjudication_file": str(adjudication_file),
        "total_rows": len(rows),
        "unique_chunks": len(seen_chunks),
        "completed_adjudicated_chunks": completed_count,
        "pending_or_incomplete_chunks": len(rows) - completed_count,
        "status_counts": dict(sorted(status_counts.items())),
        "explicit_gold_nodes": explicit_node_count,
        "derived_gold_node_instances": len(derived_node_keys),
        "adjudicated_gold_edges": edge_count,
        "adjudicated_gold_evidence_links": evidence_count,
        "gold_item_count_for_readiness": gold_item_count,
        "validation_error_count": error_count,
        "validation_warning_count": warning_count,
        "issue_counts": dict(sorted(Counter(item["code"] for item in issues).items())),
        "issues": issues[:500],
        "issue_count_truncated": max(0, len(issues) - 500),
        "paper_ready_minimums": {
            "completed_chunks_ge_100": completed_count >= 100,
            "gold_items_ge_500": gold_item_count >= 500,
            "no_validation_errors": error_count == 0,
        },
        "claim_status": status,
    }


def build_gold_by_chunk(rows):
    gold_by_chunk = {}
    for row in rows:
        if not is_completed_adjudication(row):
            continue
        chunk_id = row.get("chunk_id")
        if not chunk_id or chunk_id in gold_by_chunk:
            continue
        nodes = row.get("adjudicated_gold_nodes") or row.get("gold_nodes") or []
        edges = [
            edge
            for edge in (row.get("adjudicated_gold_edges") or row.get("gold_edges") or [])
            if not is_rejected_gold_edge(edge)
        ]
        gold_by_chunk[chunk_id] = {"nodes": nodes, "edges": edges}
    return gold_by_chunk


def gold_counters_for_chunks(gold_by_chunk, chunk_ids):
    edge_counter = Counter()
    predicate_counter = Counter()
    node_counter = Counter()
    evidence_counter = Counter()
    for chunk_id in chunk_ids:
        gold = gold_by_chunk.get(chunk_id)
        if not gold:
            continue
        for node in gold["nodes"]:
            key = gold_node_key(chunk_id, node)
            if key[1]:
                node_counter[key] += 1
        for edge in gold["edges"]:
            edge_key = gold_edge_key(chunk_id, edge)
            if all(edge_key):
                edge_counter[edge_key] += 1
            predicate = norm_predicate(edge.get("predicate") or edge.get("edge_type"))
            if predicate:
                predicate_counter[(chunk_id, predicate)] += 1
            for node_key in endpoint_node_keys(chunk_id, edge):
                node_counter[node_key] += 1
            for evidence_id in evidence_keys_from_item(edge):
                evidence_counter[(chunk_id, evidence_id)] += 1
            for span_text in evidence_text_spans(edge):
                evidence_counter[(chunk_id, f"span:{span_text}")] += 1
    return {
        "edges": edge_counter,
        "predicates": predicate_counter,
        "nodes": node_counter,
        "evidence": evidence_counter,
    }


def load_raw_counts(valid_path, scored_chunk_ids):
    raw_name = valid_path.name.replace("49_", "48_").replace("_valid.jsonl", "_raw.jsonl")
    raw_path = valid_path.with_name(raw_name)
    rows, _ = read_jsonl(raw_path)
    counts = defaultdict(Counter)
    for row in rows:
        chunk_id = row.get("chunk_id")
        if scored_chunk_ids and chunk_id not in scored_chunk_ids:
            continue
        condition = row.get("condition", "unknown")
        counts[condition]["raw_rows"] += 1
        if row.get("parse_error") or row.get("error"):
            counts[condition]["parse_or_generation_error_rows"] += 1
        if row.get("partial_json_repaired"):
            counts[condition]["partial_json_repaired_rows"] += 1
    return counts


def prediction_evidence_ids(item):
    return {norm_evidence_id(value) for value in item.get("evidence_anchor_ids", []) if norm_evidence_id(value)}


def add_prediction_edge(agg, chunk_id, edge, schema):
    predicate = norm_predicate(edge.get("predicate") or edge.get("edge_type"))
    agg["edge_items"] += 1
    evidence_ids = prediction_evidence_ids(edge)
    if evidence_ids:
        agg["edge_items_with_evidence"] += 1
    if predicate in schema["edge_types"]:
        agg["schema_valid_edges"] += 1
    subject_type = pred_edge_type(edge, "source")
    object_type = pred_edge_type(edge, "target")
    if edge_schema_valid(predicate, subject_type, object_type, schema):
        agg["ontology_valid_edges"] += 1
    key = pred_edge_key(chunk_id, edge)
    if key[1] and key[2] and key[3]:
        agg["pred_edges"][key] += 1
    if predicate:
        agg["pred_predicates"][(chunk_id, predicate)] += 1
    record = pred_edge_record(chunk_id, edge)
    if record["subject"] and record["predicate"] and record["object"]:
        agg["pred_edge_records"].append(record)
    for node_key in pred_node_keys_from_edge(chunk_id, edge):
        agg["pred_nodes"][node_key] += 1
    for evidence_id in evidence_ids:
        agg["pred_evidence"][(chunk_id, evidence_id)] += 1


def evaluate_valid_file(valid_path, gold_by_chunk, schema):
    scored_chunk_ids = set(gold_by_chunk)
    raw_counts = load_raw_counts(valid_path, scored_chunk_ids)
    rows, _ = read_jsonl(valid_path)
    by_condition = defaultdict(lambda: {
        "source_file": valid_path.name,
        "rows": 0,
        "chunks": set(),
        "pred_edges": Counter(),
        "pred_predicates": Counter(),
        "pred_nodes": Counter(),
        "pred_evidence": Counter(),
        "pred_edge_records": [],
        "pred_triples": 0,
        "pred_mappings": 0,
        "edge_items": 0,
        "edge_items_with_evidence": 0,
        "schema_valid_edges": 0,
        "ontology_valid_edges": 0,
        "mapping_items_with_evidence": 0,
    })

    for row in rows:
        chunk_id = row.get("chunk_id")
        if chunk_id not in scored_chunk_ids:
            continue
        condition = row.get("condition", "unknown")
        agg = by_condition[condition]
        agg["rows"] += 1
        agg["chunks"].add(chunk_id)
        for node in row.get("nodes", []):
            label = norm_label(node.get("label"))
            if label:
                agg["pred_nodes"][(chunk_id, label)] += 1
            for evidence_id in prediction_evidence_ids(node):
                agg["pred_evidence"][(chunk_id, evidence_id)] += 1
        for edge in row.get("edges", []):
            add_prediction_edge(agg, chunk_id, edge, schema)
        for triple in row.get("triples", []):
            agg["pred_triples"] += 1
            triple_edge = {
                "subject": triple.get("subject") or triple.get("sub"),
                "predicate": triple.get("predicate") or triple.get("rel"),
                "object": triple.get("object") or triple.get("obj"),
                "evidence_anchor_ids": triple.get("evidence_anchor_ids") or [],
            }
            add_prediction_edge(agg, chunk_id, triple_edge, schema)
        for mapping in row.get("mappings", []):
            agg["pred_mappings"] += 1
            evidence_ids = prediction_evidence_ids(mapping)
            if evidence_ids:
                agg["mapping_items_with_evidence"] += 1
            for evidence_id in evidence_ids:
                agg["pred_evidence"][(chunk_id, evidence_id)] += 1

    results = []
    for condition, agg in sorted(by_condition.items()):
        gold = gold_counters_for_chunks(gold_by_chunk, agg["chunks"])
        edge_scores = counter_prf(agg["pred_edges"], gold["edges"])
        predicate_scores = counter_prf(agg["pred_predicates"], gold["predicates"])
        node_scores = counter_prf(agg["pred_nodes"], gold["nodes"])
        evidence_scores = counter_prf(agg["pred_evidence"], gold["evidence"])
        raw = raw_counts.get(condition, Counter())
        edge_evidence_rate = agg["edge_items_with_evidence"] / agg["edge_items"] if agg["edge_items"] else 0.0
        schema_edge_rate = agg["schema_valid_edges"] / agg["edge_items"] if agg["edge_items"] else 0.0
        ontology_conformance = agg["ontology_valid_edges"] / agg["edge_items"] if agg["edge_items"] else 0.0
        unsupported_edge_rate = edge_scores["fp"] / sum(agg["pred_edges"].values()) if agg["pred_edges"] else 0.0
        mapping_evidence_rate = agg["mapping_items_with_evidence"] / agg["pred_mappings"] if agg["pred_mappings"] else 0.0
        procedural = procedural_metrics(agg["pred_edge_records"], schema)
        cq = cq_answerability(agg["pred_predicates"], gold["predicates"])
        results.append({
            "source_file": agg["source_file"],
            "condition": condition,
            "rows": agg["rows"],
            "chunks": len(agg["chunks"]),
            "raw_rows": raw.get("raw_rows", agg["rows"]),
            "parse_or_generation_error_rows": raw.get("parse_or_generation_error_rows", 0),
            "partial_json_repaired_rows": raw.get("partial_json_repaired_rows", 0),
            "pred_edges": sum(agg["pred_edges"].values()),
            "pred_nodes": sum(agg["pred_nodes"].values()),
            "pred_triples": agg["pred_triples"],
            "pred_mappings": agg["pred_mappings"],
            "gold_edge_instances": sum(gold["edges"].values()),
            "gold_node_instances": sum(gold["nodes"].values()),
            "gold_evidence_instances": sum(gold["evidence"].values()),
            "edge_exact_precision": edge_scores["precision"],
            "edge_exact_recall": edge_scores["recall"],
            "edge_exact_f1": edge_scores["f1"],
            "edge_exact_tp": edge_scores["tp"],
            "predicate_precision": predicate_scores["precision"],
            "predicate_recall": predicate_scores["recall"],
            "predicate_f1": predicate_scores["f1"],
            "node_label_precision": node_scores["precision"],
            "node_label_recall": node_scores["recall"],
            "node_label_f1": node_scores["f1"],
            "evidence_precision": evidence_scores["precision"],
            "evidence_recall": evidence_scores["recall"],
            "evidence_f1": evidence_scores["f1"],
            "evidence_exact_match": evidence_scores["precision"],
            "unsupported_edge_rate": round(unsupported_edge_rate, 6),
            "edge_evidence_attachment_rate": round(edge_evidence_rate, 6),
            "schema_edge_rate": round(schema_edge_rate, 6),
            "ontology_conformance": round(ontology_conformance, 6),
            "ontology_violation_count": agg["edge_items"] - agg["ontology_valid_edges"],
            "procedural_edge_count": procedural["procedural_edge_count"],
            "procedural_consistency": procedural["procedural_consistency"],
            "procedural_violation_count": procedural["procedural_violation_count"],
            "precedence_cycle_count": procedural["precedence_cycle_count"],
            "cq_gold_applicable_count": cq["cq_gold_applicable_count"],
            "cq_answered_count": cq["cq_answered_count"],
            "cq_answerability": cq["cq_answerability"],
            "mapping_evidence_attachment_rate": round(mapping_evidence_rate, 6),
            "claim_status": "human_gold",
        })
    return results


def evaluate_predictions(exp_dir, valid_files, gold_by_chunk, schema):
    all_rows = []
    for valid_path in valid_files:
        valid_path = Path(valid_path)
        if not valid_path.is_absolute():
            valid_path = Path(exp_dir) / valid_path
        if not valid_path.exists():
            continue
        all_rows.extend(evaluate_valid_file(valid_path, gold_by_chunk, schema))
    return all_rows


def build_validation_report(summary):
    lines = [
        "# CAPE-KG Human Gold Validation",
        "",
        f"Generated: {summary['generated_at_utc']}",
        "",
        "## Status",
        "",
        f"- Claim status: {summary['claim_status']}",
        f"- Completed/adjudicated chunks: {summary['completed_adjudicated_chunks']}",
        f"- Pending/incomplete chunks: {summary['pending_or_incomplete_chunks']}",
        f"- Gold item count for readiness: {summary['gold_item_count_for_readiness']}",
        f"- Validation errors: {summary['validation_error_count']}",
        f"- Validation warnings: {summary['validation_warning_count']}",
        "",
        "## Readiness Gates",
        "",
    ]
    for key, value in summary["paper_ready_minimums"].items():
        lines.append(f"- {key}: {value}")
    lines += ["", "## Status Counts", ""]
    for key, value in summary["status_counts"].items():
        lines.append(f"- {key}: {value}")
    if summary["issue_counts"]:
        lines += ["", "## Issue Counts", ""]
        for key, value in summary["issue_counts"].items():
            lines.append(f"- {key}: {value}")
    if summary["issues"]:
        lines += ["", "## First Issues", ""]
        for item in summary["issues"][:25]:
            if item.get("chunk_id"):
                location = item["chunk_id"]
            elif item.get("line"):
                location = f"line {item['line']}"
            else:
                location = "file"
            lines.append(f"- [{item['level']}] {item['code']} ({location}): {item['message']}")
    if summary["issue_count_truncated"]:
        lines.append(f"- Additional issues omitted: {summary['issue_count_truncated']}")
    lines.append("")
    return "\n".join(lines)


def build_evaluation_report(metrics, validation_summary, output_dir):
    lines = [
        "# CAPE-KG Human-Gold Evaluation",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        "This report scores actual LLM outputs against adjudicated human gold only.",
        "If no chunks are adjudicated, metrics remain empty and no paper claim is supported.",
        "",
        "## Gold Status",
        "",
        f"- Claim status: {validation_summary['claim_status']}",
        f"- Completed/adjudicated chunks: {validation_summary['completed_adjudicated_chunks']}",
        f"- Gold item count for readiness: {validation_summary['gold_item_count_for_readiness']}",
        "",
    ]
    if not metrics:
        lines += [
            "## Metrics",
            "",
            "No human-gold metrics were produced because no completed adjudicated chunks were available.",
            "",
        ]
    else:
        lines += [
            "## Metrics",
            "",
            "| condition | chunks | edges | exact F1 | node F1 | evidence EM | ontology | procedural | CQ | unsupported | parse/error rows |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
        for row in sorted(metrics, key=lambda r: (r["source_file"], r["condition"])):
            lines.append(
                f"| {row['condition']} | {row['chunks']} | {row['pred_edges']} | "
                f"{row['edge_exact_f1']} | {row['node_label_f1']} | "
                f"{row['evidence_exact_match']} | {row['ontology_conformance']} | "
                f"{row['procedural_consistency']} | {row['cq_answerability']} | "
                f"{row['unsupported_edge_rate']} | {row['parse_or_generation_error_rows']} |"
            )
        lines.append("")
        lines += [
            "## Metric Notes",
            "",
            "- `ontology` is the strict domain/range/schema conformance rate over predicted edges.",
            "- `procedural` penalizes procedural schema violations and PRECEDES cycles.",
            "- `CQ` is the fraction of gold-applicable competency-question predicate groups covered by the predicted graph.",
            "- `unsupported` is the exact-edge false-positive rate against adjudicated human gold.",
            "",
        ]
    lines += [
        "## Output Files",
        "",
        f"- Validation summary: `{output_dir / 'human_gold_validation_summary.json'}`",
        f"- Validation report: `{output_dir / 'human_gold_validation_report.md'}`",
        f"- Metrics CSV: `{output_dir / 'human_gold_metrics.csv'}`",
        f"- Metrics JSON: `{output_dir / 'human_gold_metrics.json'}`",
        "",
    ]
    return "\n".join(lines)


def run(args):
    exp_dir = Path(args.experiment_dir)
    output_dir = exp_dir / "04_evaluation"
    adjudication_file = Path(args.adjudication_file) if args.adjudication_file else exp_dir / "01_data/gold_annotation/full_120/adjudication.jsonl"
    valid_files = args.valid_file or DEFAULT_VALID_FILES

    schema = load_schema(exp_dir)
    chunk_context, chunk_issues = load_chunk_context(exp_dir)
    adjudication_rows, read_issues = read_jsonl(adjudication_file)
    validation_summary = validate_adjudication(
        adjudication_rows,
        chunk_issues + read_issues,
        schema,
        chunk_context,
        adjudication_file,
    )
    gold_by_chunk = build_gold_by_chunk(adjudication_rows)
    metrics = []
    if validation_summary["completed_adjudicated_chunks"] and validation_summary["validation_error_count"] == 0:
        metrics = evaluate_predictions(exp_dir, valid_files, gold_by_chunk, schema)

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "experiment_dir": str(exp_dir),
        "adjudication_file": str(adjudication_file),
        "source_valid_files": [str(Path(exp_dir) / path) if not Path(path).is_absolute() else str(path) for path in valid_files],
        "validation": validation_summary,
        "metrics": metrics,
        "claim_status": "human_gold" if metrics else validation_summary["claim_status"],
    }

    write_json(output_dir / "human_gold_validation_summary.json", validation_summary)
    write_text(output_dir / "human_gold_validation_report.md", build_validation_report(validation_summary))
    write_csv(output_dir / "human_gold_metrics.csv", metrics, METRIC_FIELDNAMES)
    write_json(output_dir / "human_gold_metrics.json", payload)
    write_text(output_dir / "human_gold_evaluation_report.md", build_evaluation_report(metrics, validation_summary, output_dir))
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-dir", default=str(DEFAULT_EXP_DIR))
    parser.add_argument("--adjudication-file", default="")
    parser.add_argument("--valid-file", action="append", help="Optional valid JSONL file. Repeat to evaluate multiple files.")
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
