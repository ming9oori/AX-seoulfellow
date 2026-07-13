#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build a pre-formal annotation calibration pack from non-priority pilot rows."""

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_EXP_DIR = Path("experiments/cape_kg_eacl_20260627")
DEFAULT_PACKAGE = "full_120"


CSV_FIELDS = [
    "calibration_id",
    "chunk_id",
    "page_start",
    "page_end",
    "focus",
    "candidate_edges",
    "predicate_mix",
    "component_span_issue_count",
    "sample_reference_id",
    "sample_source_label",
    "sample_predicate",
    "sample_target_label",
    "sample_evidence_anchor_ids",
    "sample_evidence_excerpt",
    "recommended_check",
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


def read_csv(path):
    path = Path(path)
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_json(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_csv(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in CSV_FIELDS})


def write_text(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def truncate(text, limit=260):
    text = " ".join(str(text or "").split())
    if len(text) <= limit:
        return text
    return text[:limit].rsplit(" ", 1)[0] + "..."


def component_issue_count(edge):
    count = 0
    for span in edge.get("component_evidence_spans") or []:
        if span.get("span_method") in {"label_not_found_in_sentence", "full_sentence_proxy"}:
            count += 1
    return count


def predicate_mix(edges):
    counts = Counter(edge.get("predicate") for edge in edges if edge.get("predicate"))
    return "; ".join(f"{pred}:{count}" for pred, count in counts.most_common(5))


def edge_score(edge):
    score = component_issue_count(edge)
    predicate = str(edge.get("predicate") or "")
    if predicate in {"HAS_DECISION_GATEWAY", "HAS_GUARD_CONDITION", "HAS_RISK"}:
        score += 3
    if predicate in {"USES_INPUT", "PRODUCES", "PERFORMED_BY"}:
        score += 1
    return score


def focus_for(row, edge):
    predicate = str(edge.get("predicate") or "")
    if predicate in {"HAS_DECISION_GATEWAY", "HAS_GUARD_CONDITION"}:
        return "decision_or_condition_boundary"
    if predicate == "HAS_RISK":
        return "risk_requires_explicit_text"
    if predicate == "PERFORMED_BY":
        return "role_relation_must_be_direct"
    if predicate in {"USES_INPUT", "PRODUCES", "FEEDS_INTO", "USED_AS_INPUT_FOR"}:
        return "artifact_flow_direction"
    if component_issue_count(edge):
        return "evidence_span_repair"
    if len(row.get("silver_candidate_edges") or []) >= 30:
        return "dense_candidate_pruning"
    return "schema_type_boundary"


def recommendation(focus):
    mapping = {
        "decision_or_condition_boundary": "DecisionGateway와 GuardCondition은 판단/분기 또는 조건 표현이 chunk text에 직접 있을 때만 accept한다.",
        "risk_requires_explicit_text": "Risk는 위험, 실패 요인, 주의사항이 명시된 경우에만 gold로 둔다.",
        "role_relation_must_be_direct": "PERFORMED_BY는 역할과 수행 업무가 같은 문장 또는 직접 연결된 근거에 있을 때만 accept한다.",
        "artifact_flow_direction": "입력/산출/전달 방향을 확인한다. 업무가 artifact를 쓰는지, artifact가 업무로 전달되는지 방향을 바꾸지 않는다.",
        "evidence_span_repair": "label_not_found 또는 full_sentence_proxy는 자동 제안일 뿐이다. source/predicate/target이 실제 근거에 있는지 다시 확인한다.",
        "dense_candidate_pruning": "candidate가 많을수록 자동 accept를 금지하고 evidence 단위로 reject list를 꼼꼼히 남긴다.",
        "schema_type_boundary": "DomainTask, ProcedureStep, Artifact, Role, Principle, Risk의 type boundary를 먼저 확정한 뒤 edge를 판단한다.",
    }
    return mapping.get(focus, mapping["schema_type_boundary"])


def build_examples(rows, max_examples):
    candidates = []
    for row in rows:
        edges = row.get("silver_candidate_edges") or []
        if not edges:
            continue
        best_edge = sorted(edges, key=edge_score, reverse=True)[0]
        focus = focus_for(row, best_edge)
        issue_count = sum(component_issue_count(edge) for edge in edges)
        candidates.append(
            {
                "row": row,
                "edge": best_edge,
                "focus": focus,
                "score": edge_score(best_edge) + min(len(edges), 50) / 10 + min(issue_count, 120) / 20,
                "issue_count": issue_count,
            }
        )
    selected = []
    used_chunks = set()
    used_focus = Counter()
    for item in sorted(candidates, key=lambda item: item["score"], reverse=True):
        chunk_id = item["row"].get("chunk_id")
        if chunk_id in used_chunks:
            continue
        if used_focus[item["focus"]] >= 2 and len(used_focus) >= 5:
            continue
        selected.append(item)
        used_chunks.add(chunk_id)
        used_focus[item["focus"]] += 1
        if len(selected) >= max_examples:
            break
    return selected


def render_markdown(payload):
    lines = [
        "# CAPE-KG Annotation Calibration Pack",
        "",
        f"Generated: {payload['generated_at_utc']}",
        f"Experiment: `{payload['experiment_dir']}`",
        f"Source package: `{payload['source_package']}`",
        "",
        "이 파일은 formal priority-100 annotation을 시작하기 전 annotator A/B가 같은 기준을 이해하도록 만든 내부 calibration 자료입니다.",
        "여기에 포함된 예시는 정답지가 아니며, 논문용 human-gold evidence도 아닙니다.",
        "",
        "## 사용 원칙",
        "",
        "- priority batch 001-005의 formal annotation은 annotator A/B가 독립적으로 수행한다.",
        "- calibration 예시는 formal 100개 priority batch와 겹치지 않는 non-priority rows에서 뽑았다.",
        "- 이 자료는 rule alignment와 edge/evidence 판단 연습용이다.",
        "- 토론하더라도 특정 formal priority chunk의 정답을 만들거나 공유하지 않는다.",
        "- 모든 최종 판단은 `chunk_text`와 evidence span에 직접 근거가 있어야 한다.",
        "",
        "## Calibration Focus",
        "",
        "| focus | examples | decision rule |",
        "| --- | ---: | --- |",
    ]
    for focus, count in payload["focus_counts"].items():
        lines.append(f"| `{focus}` | {count} | {recommendation(focus)} |")
    lines += [
        "",
        "## Examples",
        "",
        "| id | chunk | pages | focus | candidate | evidence excerpt | check |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in payload["examples"]:
        candidate = f"{row['sample_source_label']} --{row['sample_predicate']}--> {row['sample_target_label']}"
        pages = f"{row['page_start']}-{row['page_end']}"
        lines.append(
            f"| {row['calibration_id']} | `{row['chunk_id']}` | {pages} | `{row['focus']}` | "
            f"{candidate} | {row['sample_evidence_excerpt']} | {row['recommended_check']} |"
        )
    lines += [
        "",
        "## 반환 파일과의 관계",
        "",
        "- 이 calibration pack은 `.reviewed.jsonl` 반환 파일을 만들지 않는다.",
        "- minimum paper gate는 여전히 10개 A/B reviewed JSONL, adjudication edited JSONL, IAA, human-gold scoring이 필요하다.",
        "- 이 파일을 근거로 silver candidate를 자동 accept하면 안 된다.",
        "",
    ]
    return "\n".join(lines)


def run(args):
    exp_dir = Path(args.experiment_dir)
    package = args.package
    source_path = exp_dir / "01_data/gold_annotation" / package / "annotator_A.jsonl"
    assignment_summary_path = exp_dir / "06_release/annotation_batch_assignment_summary.json"
    assignment_summary = {}
    if assignment_summary_path.exists():
        assignment_summary = json.loads(assignment_summary_path.read_text(encoding="utf-8"))
    priority_chunks = {
        chunk_id
        for batch in assignment_summary.get("batches", [])
        for chunk_id in batch.get("chunk_ids", [])
        if chunk_id
    }
    rows = [row for row in read_jsonl(source_path) if row.get("chunk_id") not in priority_chunks]
    examples = []
    for index, item in enumerate(build_examples(rows, args.max_examples), start=1):
        row = item["row"]
        edge = item["edge"]
        evidence = edge.get("primary_evidence") or {}
        examples.append(
            {
                "calibration_id": f"CAL-{index:02d}",
                "chunk_id": row.get("chunk_id", ""),
                "page_start": row.get("page_start", ""),
                "page_end": row.get("page_end", ""),
                "focus": item["focus"],
                "candidate_edges": len(row.get("silver_candidate_edges") or []),
                "predicate_mix": predicate_mix(row.get("silver_candidate_edges") or []),
                "component_span_issue_count": item["issue_count"],
                "sample_reference_id": edge.get("reference_id", ""),
                "sample_source_label": edge.get("source_label", ""),
                "sample_predicate": edge.get("predicate", ""),
                "sample_target_label": edge.get("target_label", ""),
                "sample_evidence_anchor_ids": ";".join(edge.get("evidence_anchor_ids") or []),
                "sample_evidence_excerpt": truncate(evidence.get("text", "")),
                "recommended_check": recommendation(item["focus"]),
            }
        )

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "experiment_dir": str(exp_dir),
        "source_package": package,
        "source_file": str(source_path),
        "claim_status": "calibration_only_not_human_gold_evidence",
        "formal_priority_overlap_count": 0,
        "example_count": len(examples),
        "focus_counts": dict(Counter(row["focus"] for row in examples)),
        "examples": examples,
        "outputs": {
            "json": str(exp_dir / "06_release/annotation_calibration_pack.json"),
            "markdown": str(exp_dir / "06_release/annotation_calibration_pack_ko.md"),
            "csv": str(exp_dir / "05_review/annotation_calibration_examples.csv"),
        },
    }
    write_json(payload["outputs"]["json"], payload)
    write_csv(payload["outputs"]["csv"], examples)
    write_text(payload["outputs"]["markdown"], render_markdown(payload))
    print(json.dumps(payload["outputs"], ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-dir", default=str(DEFAULT_EXP_DIR))
    parser.add_argument("--package", default=DEFAULT_PACKAGE)
    parser.add_argument("--max-examples", type=int, default=12)
    run(parser.parse_args())


if __name__ == "__main__":
    main()
