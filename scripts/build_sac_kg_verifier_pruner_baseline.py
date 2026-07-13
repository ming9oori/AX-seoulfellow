#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build a SAC-KG-style verifier/pruner baseline from existing LLM candidates.

This is not a full SAC-KG reproduction. It reuses already generated CAPE/EDC/
taxonomy candidates as the generator pool, then applies deterministic schema,
evidence, and pruning checks to produce a comparable baseline artifact.
"""

import argparse
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_EXP_DIR = Path("experiments/cape_kg_eacl_20260627")
DEFAULT_OUTPUT_PREFIX = "sac_kg_verifier_pruner_baseline"
DEFAULT_CONDITION = "B6_sac_kg_verifier_pruner"
DEFAULT_INPUTS = [
    "49_qwen3_8b_cape_ablation_120_valid.jsonl",
    "49_qwen3_8b_b2_b4_condition_baselines_120_valid.jsonl",
    "49_qwen3_8b_edc_schema_ablation_valid.jsonl",
]
SOURCE_PRIORITY = {
    "P_cape_kg_actual": 0.12,
    "B4_taxonomy_rag": 0.08,
    "B3_edc_style": 0.05,
    "B2_current_project": 0.03,
    "P_minus_Schema_retrieval": 0.02,
}


def read_json(path, default=None):
    path = Path(path)
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path):
    rows = []
    path = Path(path)
    if not path.exists():
        return rows
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


def write_jsonl(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def write_text(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def clean_text(value, limit=160):
    if value is None:
        return ""
    value = re.sub(r"\s+", " ", str(value)).strip()
    return value[:limit]


def norm(value):
    return re.sub(r"[\W_]+", "", str(value).lower(), flags=re.UNICODE)


def token_set(value):
    return {tok for tok in re.split(r"[\s,;:/()\[\]{}<>\"'`|]+", str(value).lower()) if len(tok) >= 2}


def confidence(value):
    try:
        return max(0.0, min(1.0, float(value)))
    except Exception:
        return 0.0


def sentence_map(chunk):
    text = chunk.get("text") or ""
    mapping = {}
    for row in chunk.get("sentence_offsets", []):
        sid = row.get("sentence_id")
        if not sid:
            continue
        start = int(row.get("chunk_char_start") or 0)
        end = int(row.get("chunk_char_end") or 0)
        mapping[sid] = text[start:end].strip()
    if not mapping:
        for sid in chunk.get("sentence_ids", []):
            mapping[sid] = text
    return mapping


def valid_evidence(ids, allowed):
    out = []
    seen = set()
    for value in ids or []:
        value = clean_text(value, 80)
        if value in allowed and value not in seen:
            seen.add(value)
            out.append(value)
    return out


def text_support_score(labels, evidence_ids, sentences):
    evidence_text = " ".join(sentences.get(eid, "") for eid in evidence_ids)
    evidence_norm = norm(evidence_text)
    if not evidence_norm:
        return 0.0
    score = 0.0
    for label in labels:
        label = clean_text(label)
        if not label:
            continue
        label_norm = norm(label)
        if label_norm and label_norm in evidence_norm:
            score = max(score, 1.0)
            continue
        toks = token_set(label)
        if toks:
            hit = sum(1 for tok in toks if norm(tok) in evidence_norm)
            if hit:
                score = max(score, min(0.8, hit / max(1, len(toks))))
    return score


def load_schema(exp_dir):
    schema = read_json(exp_dir / "02_schema/cape_schema.json", {}) or {}
    allowed_nodes = set(schema.get("node_types") or [])
    allowed_edges = set(schema.get("edge_types") or [])
    domain_range = {}
    for pred, spec in (schema.get("domain_range") or {}).items():
        subjects = set(spec.get("subject_types") or [])
        objects = set(spec.get("object_types") or [])
        if "Any" in subjects:
            subjects = set()
        if "Any" in objects:
            objects = set()
        domain_range[pred] = (subjects, objects)
    local_nodes = {
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
    }
    local_edges = {
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
        "USED_AS_INPUT_FOR",
    }
    return allowed_nodes & local_nodes, allowed_edges & local_edges, domain_range


def group_candidates(exp_dir, input_files):
    by_chunk = defaultdict(list)
    for name in input_files:
        path = exp_dir / name
        for row in read_jsonl(path):
            condition = row.get("condition") or ""
            if condition not in SOURCE_PRIORITY:
                continue
            item = dict(row)
            item["_source_file"] = str(path)
            by_chunk[row.get("chunk_id")].append(item)
    return by_chunk


def domain_range_ok(edge, domain_range):
    predicate = edge.get("predicate")
    if predicate not in domain_range:
        return False
    allowed_subjects, allowed_objects = domain_range[predicate]
    subject_type = edge.get("subject_type") or ""
    object_type = edge.get("object_type") or ""
    if allowed_subjects and subject_type not in allowed_subjects:
        return False
    if allowed_objects and object_type not in allowed_objects:
        return False
    return True


def add_candidate(bucket, key, item, source_condition, support, source_bonus):
    score = round(confidence(item.get("confidence")) + source_bonus + 0.15 * support, 6)
    current = bucket.get(key)
    payload = dict(item)
    payload["_score"] = score
    payload["_source_conditions"] = sorted(set(item.get("_source_conditions", [])) | {source_condition})
    if current is None or score > current["_score"]:
        bucket[key] = payload
    else:
        current["_source_conditions"] = sorted(set(current.get("_source_conditions", [])) | {source_condition})


def build_chunk_output(chunk, candidates, allowed_nodes, allowed_edges, domain_range, args):
    allowed_eids = set(chunk.get("sentence_ids", []))
    sentences = sentence_map(chunk)
    stats = Counter()
    node_candidates = {}
    edge_candidates = {}
    mapping_candidates = {}
    node_type_by_label = {}

    for row in candidates:
        source_condition = row.get("condition") or ""
        source_bonus = SOURCE_PRIORITY.get(source_condition, 0.0)
        for item in row.get("nodes", []) or []:
            label = clean_text(item.get("label"))
            node_type = clean_text(item.get("type"), 80)
            evidence = valid_evidence(item.get("evidence_anchor_ids"), allowed_eids)
            if not label or not evidence or node_type not in allowed_nodes:
                stats["node_rejected_schema_or_evidence"] += 1
                continue
            support = text_support_score([label], evidence, sentences)
            if support < args.min_node_support:
                stats["node_pruned_low_support"] += 1
                continue
            payload = {
                "label": label,
                "type": node_type,
                "evidence_anchor_ids": evidence,
                "confidence": round(confidence(item.get("confidence")), 3),
            }
            key = (label.casefold(), node_type)
            add_candidate(node_candidates, key, payload, source_condition, support, source_bonus)
            node_type_by_label[label.casefold()] = node_type

    for row in candidates:
        source_condition = row.get("condition") or ""
        source_bonus = SOURCE_PRIORITY.get(source_condition, 0.0)
        for item in row.get("edges", []) or []:
            subject = clean_text(item.get("subject"))
            obj = clean_text(item.get("object"))
            predicate = clean_text(item.get("predicate"), 80).upper()
            evidence = valid_evidence(item.get("evidence_anchor_ids"), allowed_eids)
            subject_type = clean_text(item.get("subject_type"), 80) or node_type_by_label.get(subject.casefold(), "")
            object_type = clean_text(item.get("object_type"), 80) or node_type_by_label.get(obj.casefold(), "")
            if not subject or not obj or not evidence or predicate not in allowed_edges:
                stats["edge_rejected_schema_or_evidence"] += 1
                continue
            if subject.casefold() == obj.casefold():
                stats["edge_pruned_self_loop"] += 1
                continue
            edge = {
                "subject": subject,
                "subject_type": subject_type,
                "predicate": predicate,
                "object": obj,
                "object_type": object_type,
                "evidence_anchor_ids": evidence,
                "confidence": round(confidence(item.get("confidence")), 3),
            }
            if not domain_range_ok(edge, domain_range):
                stats["edge_pruned_domain_range"] += 1
                continue
            support = text_support_score([subject, obj], evidence, sentences)
            if support < args.min_edge_support:
                stats["edge_pruned_low_support"] += 1
                continue
            key = (subject.casefold(), predicate, obj.casefold())
            add_candidate(edge_candidates, key, edge, source_condition, support, source_bonus)

    endpoint_nodes = {}
    for edge in edge_candidates.values():
        for label_key, label_field, type_field in [
            (edge["subject"].casefold(), "subject", "subject_type"),
            (edge["object"].casefold(), "object", "object_type"),
        ]:
            node_type = edge.get(type_field) or node_type_by_label.get(label_key, "")
            if not node_type:
                continue
            node_key = (edge[label_field].casefold(), node_type)
            if node_key not in node_candidates:
                endpoint_nodes[node_key] = {
                    "label": edge[label_field],
                    "type": node_type,
                    "evidence_anchor_ids": edge["evidence_anchor_ids"],
                    "confidence": max(0.5, round(edge.get("confidence", 0.0) - 0.05, 3)),
                    "_score": edge.get("_score", 0.0) - 0.01,
                    "_source_conditions": edge.get("_source_conditions", []),
                }
    node_candidates.update(endpoint_nodes)

    for row in candidates:
        source_condition = row.get("condition") or ""
        source_bonus = SOURCE_PRIORITY.get(source_condition, 0.0)
        for item in row.get("mappings", []) or []:
            source_task = clean_text(item.get("source_task"))
            standard = clean_text(item.get("standard"), 20).upper()
            target_label = clean_text(item.get("target_label"))
            evidence = valid_evidence(item.get("evidence_anchor_ids"), allowed_eids)
            if not source_task or not target_label or standard not in {"NCS", "PCF"} or not evidence:
                stats["mapping_rejected_schema_or_evidence"] += 1
                continue
            support = text_support_score([source_task], evidence, sentences)
            if support < args.min_node_support:
                stats["mapping_pruned_low_support"] += 1
                continue
            payload = {
                "source_task": source_task,
                "standard": standard,
                "target_label": target_label,
                "evidence_anchor_ids": evidence,
                "confidence": round(confidence(item.get("confidence")), 3),
            }
            key = (source_task.casefold(), standard, target_label.casefold())
            add_candidate(mapping_candidates, key, payload, source_condition, support, source_bonus)

    def strip_private(row):
        return {k: v for k, v in row.items() if not k.startswith("_")}

    def top_rows(bucket, limit):
        rows = sorted(bucket.values(), key=lambda row: (-row.get("_score", 0.0), row.get("label") or row.get("subject") or row.get("source_task") or ""))
        return [strip_private(row) for row in rows[:limit]]

    nodes = top_rows(node_candidates, args.max_nodes_per_chunk)
    edges = top_rows(edge_candidates, args.max_edges_per_chunk)
    mappings = top_rows(mapping_candidates, args.max_mappings_per_chunk)
    stats["input_candidate_rows"] = len(candidates)
    stats["accepted_nodes"] = len(nodes)
    stats["accepted_edges"] = len(edges)
    stats["accepted_mappings"] = len(mappings)
    return {
        "chunk_id": chunk["chunk_id"],
        "condition": args.condition,
        "nodes": nodes,
        "edges": edges,
        "triples": [],
        "mappings": mappings,
    }, stats


def build_report(args, summary, raw_path, valid_path):
    lines = [
        "# SAC-KG-Style Verifier/Pruner Baseline",
        "",
        f"Generated: {summary['generated_at_utc']}",
        f"Condition: `{args.condition}`",
        f"Raw file: `{raw_path}`",
        f"Valid file: `{valid_path}`",
        "",
        "This is a deterministic SAC-KG-style approximation. It uses existing LLM outputs as generator candidates and applies schema/evidence verification plus pruning. It is not a full SAC-KG reproduction.",
        "",
        "## Summary",
        "",
        f"- Chunks: {summary['chunks']}",
        f"- Raw rows: {summary['raw_rows']}",
        f"- Valid rows: {summary['valid_rows']}",
        f"- Accepted nodes: {summary['accepted_nodes']}",
        f"- Accepted edges: {summary['accepted_edges']}",
        f"- Accepted mappings: {summary['accepted_mappings']}",
        "",
        "## Verifier/Pruner Counters",
        "",
    ]
    for key, value in sorted(summary["counters"].items()):
        lines.append(f"- {key}: {value}")
    return "\n".join(lines) + "\n"


def run(args):
    exp_dir = Path(args.experiment_dir)
    chunks = read_jsonl(exp_dir / "01_data/evaluation_chunks.jsonl")
    by_chunk = group_candidates(exp_dir, args.input_valid_file)
    allowed_nodes, allowed_edges, domain_range = load_schema(exp_dir)
    raw_rows = []
    valid_rows = []
    counters = Counter()

    for chunk in chunks:
        valid, stats = build_chunk_output(chunk, by_chunk.get(chunk["chunk_id"], []), allowed_nodes, allowed_edges, domain_range, args)
        counters.update(stats)
        valid_rows.append(valid)
        raw_rows.append({
            "chunk_id": chunk["chunk_id"],
            "condition": args.condition,
            "parse_error": None,
            "error": None,
            "source_valid_files": args.input_valid_file,
            "candidate_rows": stats.get("input_candidate_rows", 0),
            "verifier_pruner_counters": dict(stats),
            "parsed": valid,
        })

    raw_path = exp_dir / f"48_{args.output_prefix}_raw.jsonl"
    valid_path = exp_dir / f"49_{args.output_prefix}_valid.jsonl"
    report_path = exp_dir / f"50_{args.output_prefix}_quality_report.md"
    summary_path = exp_dir / f"50_{args.output_prefix}_summary.json"
    write_jsonl(raw_path, raw_rows)
    write_jsonl(valid_path, valid_rows)

    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "condition": args.condition,
        "chunks": len(chunks),
        "raw_rows": len(raw_rows),
        "valid_rows": len(valid_rows),
        "accepted_nodes": sum(len(row["nodes"]) for row in valid_rows),
        "accepted_edges": sum(len(row["edges"]) for row in valid_rows),
        "accepted_mappings": sum(len(row["mappings"]) for row in valid_rows),
        "counters": dict(counters),
        "source_valid_files": args.input_valid_file,
        "raw_file": str(raw_path),
        "valid_file": str(valid_path),
        "report_file": str(report_path),
    }
    write_json(summary_path, summary)
    write_text(report_path, build_report(args, summary, raw_path, valid_path))
    print(json.dumps(summary, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-dir", default=str(DEFAULT_EXP_DIR))
    parser.add_argument("--output-prefix", default=DEFAULT_OUTPUT_PREFIX)
    parser.add_argument("--condition", default=DEFAULT_CONDITION)
    parser.add_argument("--input-valid-file", action="append", default=None)
    parser.add_argument("--min-node-support", type=float, default=0.0)
    parser.add_argument("--min-edge-support", type=float, default=0.0)
    parser.add_argument("--max-nodes-per-chunk", type=int, default=30)
    parser.add_argument("--max-edges-per-chunk", type=int, default=15)
    parser.add_argument("--max-mappings-per-chunk", type=int, default=5)
    args = parser.parse_args()
    if args.input_valid_file is None:
        args.input_valid_file = list(DEFAULT_INPUTS)
    run(args)


if __name__ == "__main__":
    main()
