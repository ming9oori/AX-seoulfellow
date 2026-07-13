#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build NCS-PCF crosswalk candidates supported by shared Layer2 task bridges."""

import argparse
import csv
import hashlib
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_EXP_DIR = Path("experiments/cape_kg_eacl_20260627")
DEFAULT_OUTPUTS_DIR = Path("outputs")

FIELDNAMES = [
    "crosswalk_id",
    "crosswalk_rank",
    "source_id",
    "source_label",
    "ncs_target_id",
    "ncs_target_label",
    "pcf_target_id",
    "pcf_target_label",
    "ncs_rank",
    "pcf_rank",
    "ncs_score",
    "pcf_score",
    "bridge_score",
    "rank_component",
    "score_component",
    "reason_component",
    "supporting_mapping_ids_json",
    "supporting_reasons_json",
    "bridge_support_type",
    "claim_status",
]


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


def write_jsonl(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def write_json(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_csv(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for row in rows:
            writer.writerow({name: row.get(name, "") for name in FIELDNAMES})


def sha1_text(value, size=16):
    return hashlib.sha1(str(value).encode("utf-8")).hexdigest()[:size]


def as_int(value, default=999):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def as_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def group_by_source(rows, top_k):
    grouped = defaultdict(list)
    for row in rows:
        if as_int(row.get("rank")) <= top_k:
            grouped[row.get("source_id")].append(row)
    for source_id in list(grouped):
        grouped[source_id].sort(key=lambda row: (as_int(row.get("rank")), -as_float(row.get("score"))))
    return grouped


def source_score_norms(rows):
    max_score = max((as_float(row.get("score")) for row in rows), default=0.0)
    if max_score <= 0:
        return {row.get("mapping_id"): 0.0 for row in rows}
    return {row.get("mapping_id"): as_float(row.get("score")) / max_score for row in rows}


def crosswalk_row(source_id, ncs_row, pcf_row, ncs_norm, pcf_norm, top_k):
    ncs_rank = as_int(ncs_row.get("rank"))
    pcf_rank = as_int(pcf_row.get("rank"))
    rank_component = ((top_k + 1 - ncs_rank) / top_k + (top_k + 1 - pcf_rank) / top_k) / 2
    score_component = (ncs_norm.get(ncs_row.get("mapping_id"), 0.0) + pcf_norm.get(pcf_row.get("mapping_id"), 0.0)) / 2
    reason_component = 1.0 if ncs_row.get("reason") and pcf_row.get("reason") else 0.0
    bridge_score = 0.45 * rank_component + 0.40 * score_component + 0.15 * reason_component
    key = "|".join([source_id or "", ncs_row.get("target_id") or "", pcf_row.get("target_id") or ""])
    return {
        "crosswalk_id": "CW-" + sha1_text(key),
        "source_id": source_id,
        "source_label": ncs_row.get("source_label") or pcf_row.get("source_label") or "",
        "ncs_target_id": ncs_row.get("target_id") or "",
        "ncs_target_label": ncs_row.get("target_label") or "",
        "pcf_target_id": pcf_row.get("target_id") or "",
        "pcf_target_label": pcf_row.get("target_label") or "",
        "ncs_rank": ncs_rank,
        "pcf_rank": pcf_rank,
        "ncs_score": as_float(ncs_row.get("score")),
        "pcf_score": as_float(pcf_row.get("score")),
        "bridge_score": round(bridge_score, 6),
        "rank_component": round(rank_component, 6),
        "score_component": round(score_component, 6),
        "reason_component": round(reason_component, 6),
        "supporting_mapping_ids": [ncs_row.get("mapping_id"), pcf_row.get("mapping_id")],
        "supporting_mapping_ids_json": json.dumps([ncs_row.get("mapping_id"), pcf_row.get("mapping_id")], ensure_ascii=False),
        "supporting_reasons": [ncs_row.get("reason", ""), pcf_row.get("reason", "")],
        "supporting_reasons_json": json.dumps([ncs_row.get("reason", ""), pcf_row.get("reason", "")], ensure_ascii=False),
        "bridge_support_type": "shared_layer2_domain_task",
        "claim_status": "candidate_only_pending_expert_review",
    }


def build_crosswalks(ncs_rows, pcf_rows, top_k, max_pairs_per_source):
    ncs_by_source = group_by_source(ncs_rows, top_k)
    pcf_by_source = group_by_source(pcf_rows, top_k)
    shared_sources = sorted(set(ncs_by_source) & set(pcf_by_source))
    all_pairs = []
    top_pairs = []
    for source_id in shared_sources:
        ncs_group = ncs_by_source[source_id]
        pcf_group = pcf_by_source[source_id]
        ncs_norm = source_score_norms(ncs_group)
        pcf_norm = source_score_norms(pcf_group)
        pairs = [
            crosswalk_row(source_id, ncs_row, pcf_row, ncs_norm, pcf_norm, top_k)
            for ncs_row in ncs_group
            for pcf_row in pcf_group
        ]
        pairs.sort(key=lambda row: (-as_float(row.get("bridge_score")), as_int(row.get("ncs_rank")), as_int(row.get("pcf_rank"))))
        all_pairs.extend(pairs)
        for idx, row in enumerate(pairs[:max_pairs_per_source], start=1):
            row = dict(row)
            row["crosswalk_rank"] = idx
            top_pairs.append(row)
    return all_pairs, top_pairs, shared_sources


def render_report(summary, top_pairs):
    lines = [
        "# CAPE-KG NCS-PCF Crosswalk Candidate Report",
        "",
        f"Generated: {summary['generated_at_utc']}",
        "",
        "This report implements the revised plan's downstream Output 3: NCS-PCF crosswalk candidates with Layer2 bridge support.",
        "The candidates are generated by joining NCS and PCF Top-K mappings that share the same Layer2 DomainTask.",
        "They are not expert-confirmed crosswalk labels.",
        "",
        "## Summary",
        "",
        f"- Shared Layer2 source tasks: {summary['shared_source_tasks']}",
        f"- All crosswalk pairs: {summary['all_pair_count']}",
        f"- Top crosswalk candidates: {summary['candidate_count']}",
        f"- Top-K per standard: {summary['top_k_per_standard']}",
        f"- Max pairs per source: {summary['max_pairs_per_source']}",
        f"- Claim status: `{summary['claim_status']}`",
        "",
        "## Top Candidates",
        "",
        "| rank | source task | NCS candidate | PCF candidate | bridge score | NCS rank | PCF rank |",
        "|---:|---|---|---|---:|---:|---:|",
    ]
    for row in top_pairs[:30]:
        lines.append(
            f"| {row.get('crosswalk_rank', '')} | {str(row.get('source_label', '')).replace('|', '/')} | "
            f"{str(row.get('ncs_target_label', '')).replace('|', '/')} | "
            f"{str(row.get('pcf_target_label', '')).replace('|', '/')} | "
            f"{row.get('bridge_score')} | {row.get('ncs_rank')} | {row.get('pcf_rank')} |"
        )
    lines += [
        "",
        "## Claim Scope",
        "",
        "- These rows are bridge-supported candidate pairs, not a gold NCS-PCF crosswalk.",
        "- Expert review is still required before reporting crosswalk precision, accept-rate, or utility claims.",
        "- The score combines within-task rank strength, normalized candidate scores, and whether both component mappings include reasons.",
        "",
    ]
    return "\n".join(lines)


def run(args):
    exp_dir = Path(args.experiment_dir)
    outputs_dir = Path(args.outputs_dir)
    ncs_rows = read_jsonl(outputs_dir / "08_mapping/l2_ncs_mapping_candidates.jsonl")
    pcf_rows = read_jsonl(outputs_dir / "08_mapping/l2_pcf_mapping_candidates.jsonl")
    all_pairs, top_pairs, shared_sources = build_crosswalks(
        ncs_rows,
        pcf_rows,
        top_k=args.top_k,
        max_pairs_per_source=args.max_pairs_per_source,
    )
    generated_at = datetime.now(timezone.utc).isoformat()
    summary = {
        "generated_at_utc": generated_at,
        "experiment_dir": str(exp_dir),
        "outputs_dir": str(outputs_dir),
        "top_k_per_standard": args.top_k,
        "max_pairs_per_source": args.max_pairs_per_source,
        "ncs_candidate_rows": len(ncs_rows),
        "pcf_candidate_rows": len(pcf_rows),
        "shared_source_tasks": len(shared_sources),
        "all_pair_count": len(all_pairs),
        "candidate_count": len(top_pairs),
        "claim_status": "candidate_only_pending_expert_review",
        "output_files": {
            "all_pairs_jsonl": str(outputs_dir / "08_mapping/l2_ncs_pcf_crosswalk_all_pairs.jsonl"),
            "candidates_jsonl": str(outputs_dir / "08_mapping/l2_ncs_pcf_crosswalk_candidates.jsonl"),
            "candidates_csv": str(exp_dir / "04_evaluation/ncs_pcf_crosswalk_candidates.csv"),
            "summary_json": str(exp_dir / "04_evaluation/ncs_pcf_crosswalk_summary.json"),
            "report_md": str(exp_dir / "04_evaluation/ncs_pcf_crosswalk_report.md"),
        },
    }
    write_jsonl(outputs_dir / "08_mapping/l2_ncs_pcf_crosswalk_all_pairs.jsonl", all_pairs)
    write_jsonl(outputs_dir / "08_mapping/l2_ncs_pcf_crosswalk_candidates.jsonl", top_pairs)
    write_csv(exp_dir / "04_evaluation/ncs_pcf_crosswalk_candidates.csv", top_pairs)
    write_json(exp_dir / "04_evaluation/ncs_pcf_crosswalk_summary.json", summary)
    write_text(exp_dir / "04_evaluation/ncs_pcf_crosswalk_report.md", render_report(summary, top_pairs))
    print(json.dumps(summary, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-dir", default=str(DEFAULT_EXP_DIR))
    parser.add_argument("--outputs-dir", default=str(DEFAULT_OUTPUTS_DIR))
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--max-pairs-per-source", type=int, default=10)
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
