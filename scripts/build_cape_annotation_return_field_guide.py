#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build a field-level guide for CAPE-KG human annotation return files."""

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path

from import_cape_gold_annotation import ANNOTATION_EDITABLE_FIELDS, ANNOTATION_STATUSES, IMMUTABLE_FIELDS
from validate_cape_human_review_returns import COMPLETED_ANNOTATION_STATUSES


DEFAULT_EXP_DIR = Path("experiments/cape_kg_eacl_20260627")


def read_json(path, default=None):
    path = Path(path)
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path, limit=None):
    rows = []
    path = Path(path)
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
            if limit is not None and len(rows) >= limit:
                break
    return rows


def write_json(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_csv(path, rows, fieldnames):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def first_existing(paths):
    for path in paths:
        path = Path(path)
        if path.exists():
            return path
    return None


def ordered_keys(row):
    return [key for key in row.keys() if key != "_line_no"]


def sample_metadata(exp_dir):
    sample_file = first_existing(
        [
            exp_dir
            / "05_review/human_gold_batches/full_120_priority_batch_001/annotator_A_full_120_priority_batch_001.jsonl",
            exp_dir / "01_data/gold_annotation/full_120/annotator_A.jsonl",
            exp_dir / "01_data/gold_annotation/full_120/annotator_B.jsonl",
        ]
    )
    rows = read_jsonl(sample_file, limit=1) if sample_file else []
    row = rows[0] if rows else {}
    silver_edges = row.get("silver_candidate_edges") or []
    first_edge = silver_edges[0] if silver_edges and isinstance(silver_edges[0], dict) else {}
    spans = first_edge.get("component_evidence_spans") or []
    first_span = spans[0] if spans and isinstance(spans[0], dict) else {}
    return {
        "sample_file": str(sample_file) if sample_file else "",
        "top_level_fields": ordered_keys(row),
        "silver_candidate_edge_fields": ordered_keys(first_edge),
        "component_evidence_span_fields": ordered_keys(first_span),
        "sample_row_count_checked": len(rows),
    }


def field_rows(schema, metadata):
    schema = schema or {}
    editable = set(ANNOTATION_EDITABLE_FIELDS)
    immutable = set(IMMUTABLE_FIELDS)
    context_only = {
        "chunk_text",
        "instructions",
        "silver_candidate_edges",
        "silver_candidate_edge_count",
        "package",
        "chapter_id",
        "section_id",
        "page_start",
        "page_end",
    }
    rows = []
    descriptions = {
        "annotation_status": "검수 상태. 완료 행은 completed 또는 needs_adjudication으로 둔다.",
        "annotator_id": "검수자 식별자. A/B 독립 검수 구분을 위해 비워두지 않는다.",
        "gold_nodes": "원문에서 명시적으로 지지되는 최종 node 목록.",
        "gold_edges": "accept한 candidate edge 및 추가로 발견한 명시적 edge 목록.",
        "rejected_candidate_reference_ids": "reject한 silver candidate의 reference_id 목록.",
        "missing_but_supported_notes": "candidate에는 없지만 원문상 지지되는 누락 항목 메모.",
        "comments": "불확실성, adjudication 필요 사유, 특이사항.",
        "time_minutes": "해당 row 검수 소요 시간.",
    }
    for field in metadata.get("top_level_fields") or []:
        if field in editable:
            policy = "reviewer_editable"
        elif field in immutable or field in context_only:
            policy = "immutable_or_context"
        else:
            policy = "context_not_applied_by_import"
        rows.append(
            {
                "scope": "top_level",
                "field": field,
                "edit_policy": policy,
                "required_when_completed": "yes" if field == "annotation_status" else "conditional",
                "allowed_values": ", ".join(sorted(ANNOTATION_STATUSES)) if field == "annotation_status" else "",
                "validator_effect": validator_effect_for_field(field),
                "notes": descriptions.get(field, ""),
            }
        )

    for field in schema.get("gold_node_fields") or []:
        rows.append(
            {
                "scope": "gold_nodes[]",
                "field": field,
                "edit_policy": "reviewer_editable_nested",
                "required_when_completed": "when_node_added",
                "allowed_values": "",
                "validator_effect": "validate_node()가 schema/type/evidence shape를 검사한다.",
                "notes": "원문에서 직접 지지되는 node만 추가한다.",
            }
        )

    for field in schema.get("gold_edge_fields") or []:
        rows.append(
            {
                "scope": "gold_edges[]",
                "field": field,
                "edit_policy": "reviewer_editable_nested",
                "required_when_completed": "when_edge_accepted_or_added",
                "allowed_values": "",
                "validator_effect": "validate_edge()와 candidate coverage preflight가 edge shape/evidence를 검사한다.",
                "notes": "candidate를 accept할 때는 reference_id 또는 candidate_reference_id를 보존한다.",
            }
        )
    return rows


def validator_effect_for_field(field):
    if field in IMMUTABLE_FIELDS:
        return "import preflight가 원본과 달라지면 immutable_field_changed error를 낸다."
    if field == "annotation_status":
        return "completed/needs_adjudication만 완료로 집계된다."
    if field == "gold_edges":
        return "completed row에서 accept된 candidate 또는 추가 edge 근거를 검사한다."
    if field == "rejected_candidate_reference_ids":
        return "completed row의 미처리 candidate edge를 막기 위해 사용된다."
    if field == "comments":
        return "needs_adjudication row에서는 비어 있으면 error다."
    if field in ANNOTATION_EDITABLE_FIELDS:
        return "import 시 원본 row에 반영되는 editable field다."
    return "검수 참고 또는 provenance 필드이며 import merge 대상은 아니다."


def render_md(payload):
    metadata = payload["field_inventory"]
    schema = payload["annotation_schema_summary"]
    editable_fields = payload["editable_fields"]
    immutable_fields = payload["immutable_fields"]
    completed = payload["completed_status_values"]

    lines = [
        "# CAPE-KG Annotation Return Field Guide",
        "",
        f"Generated: `{payload['generated_at_utc']}`",
        f"Claim status: `{payload['claim_status']}`",
        "",
        "이 문서는 CAPE-KG human-gold annotation 반환 JSONL을 작성할 때 어떤 필드를 수정하고 어떤 필드를 보존해야 하는지 정리한 내부 검수 가이드다. 원문 chunk text를 재수록하지 않고 field policy와 validator 규칙만 요약한다.",
        "",
        "## Scope",
        "",
        "- 대상 파일: priority-100 A/B annotation batch의 `*.reviewed.jsonl` 반환 파일.",
        "- 기준 schema: `experiments/cape_kg_eacl_20260627/01_data/gold_annotation/annotation_schema.json`.",
        "- 반환 파일 목록: `experiments/cape_kg_eacl_20260627/05_review/human_review_master_return_files.csv`.",
        "- 이 문서는 human-gold 결과 자체가 아니며, A/B 검수, IAA, adjudication, human-gold scoring 전에는 논문 성능 claim으로 사용할 수 없다.",
        "",
        "## Reviewer-Editable Fields",
        "",
        "| Field | 작성 방법 | Validator 영향 |",
        "| --- | --- | --- |",
    ]
    editable_notes = {
        "annotation_status": f"`pending_human_annotation`, `in_progress`, `{completed[0]}`, `{completed[1]}` 중 하나. 완료 행은 `{completed[0]}` 또는 `{completed[1]}`.",
        "annotator_id": "검수자 ID. A/B 독립 검수 추적을 위해 유지 또는 명시적으로 기입.",
        "gold_nodes": "원문에서 명시적으로 지지되는 node만 추가. node_id/type/label/evidence를 schema에 맞춘다.",
        "gold_edges": "accept한 candidate edge 또는 원문에서 새로 발견한 edge. candidate accept 시 `reference_id` 또는 `candidate_reference_id`를 보존.",
        "rejected_candidate_reference_ids": "reject한 silver candidate의 `reference_id`를 모두 넣는다.",
        "missing_but_supported_notes": "candidate에는 없지만 원문 근거가 명확한 누락 node/edge 메모.",
        "comments": "`needs_adjudication`이면 반드시 사유를 작성.",
        "time_minutes": "해당 row 검수 소요 시간.",
    }
    for field in editable_fields:
        lines.append(f"| `{field}` | {editable_notes.get(field, '')} | {validator_effect_for_field(field)} |")

    lines += [
        "",
        "## Immutable Fields",
        "",
        "아래 필드는 검수자가 원칙적으로 수정하지 않는다. import preflight는 핵심 불변 필드가 원본과 달라지면 실패한다.",
        "",
        "| Field | 이유 |",
        "| --- | --- |",
    ]
    for field in immutable_fields:
        lines.append(f"| `{field}` | 원본 chunk/package provenance 보존. |")
    lines += [
        "| `silver_candidate_edges` | candidate 판단 대상이므로 원본을 보존한다. accept/reject 결과는 `gold_edges`와 `rejected_candidate_reference_ids`에 기록한다. |",
        "| `silver_candidate_edge_count` | 원본 candidate 수 확인용이다. |",
        "| `instructions` | batch 작성 지침 원본이다. |",
        "",
        "## Completion Rules",
        "",
        "1. 완료로 집계하려면 `annotation_status`를 `completed` 또는 `needs_adjudication`으로 둔다.",
        "2. `needs_adjudication`을 사용할 때는 `comments`에 애매한 이유를 반드시 쓴다.",
        "3. candidate edge가 있는 completed row에서는 모든 candidate가 둘 중 하나로 처리되어야 한다: `gold_edges`에서 accept되거나 `rejected_candidate_reference_ids`에 reject로 기록된다.",
        "4. candidate를 accept할 때는 edge triple만 베끼지 말고 `reference_id` 또는 `candidate_reference_id`를 같이 남긴다. reference가 없으면 source/predicate/target key matching으로 일부 확인되지만, reference 보존이 가장 안전하다.",
        "5. `gold_nodes`와 `gold_edges`는 chunk text 안에서 명시적으로 지지되는 항목만 포함한다. 추론만으로 추가하지 않는다.",
        "",
        "## Candidate Edge Handling",
        "",
        "| 판단 | 기록 위치 | 최소 기록 |",
        "| --- | --- | --- |",
        "| Accept | `gold_edges[]` | source/target id 또는 label, predicate, evidence anchor/span, decision, reference_id 또는 candidate_reference_id |",
        "| Reject | `rejected_candidate_reference_ids[]` | silver candidate의 reference_id |",
        "| Ambiguous | `annotation_status=needs_adjudication`, `comments` | 왜 accept/reject가 어려운지 구체적으로 기록 |",
        "| Missing but supported | `gold_edges[]` 또는 `gold_nodes[]`, `missing_but_supported_notes` | 원문 exact evidence와 추가 사유 |",
        "",
        "## Gold Node Fields",
        "",
        f"`gold_nodes[]` field set: `{', '.join(schema.get('gold_node_fields') or [])}`",
        "",
        "## Gold Edge Fields",
        "",
        f"`gold_edges[]` field set: `{', '.join(schema.get('gold_edge_fields') or [])}`",
        "",
        "권장 추가 key: candidate를 accept한 edge에는 `reference_id` 또는 `candidate_reference_id`를 보존한다.",
        "",
        "## JSON Shape Examples",
        "",
        "Candidate accept/reject가 섞인 completed row의 핵심 shape:",
        "",
        "```json",
        json.dumps(
            {
                "annotation_status": "completed",
                "annotator_id": "A",
                "gold_edges": [
                    {
                        "source_id": "node_id_or_blank",
                        "source_label": "source label",
                        "source_type": "DomainTask",
                        "predicate": "USES_INPUT",
                        "target_id": "node_id_or_blank",
                        "target_label": "target label",
                        "target_type": "Artifact",
                        "evidence_anchor_ids": ["anchor_id"],
                        "evidence_spans": [{"text": "short exact span", "sentence_id": "sentence_id"}],
                        "decision": "accepted",
                        "reference_id": "candidate_reference_id",
                    }
                ],
                "rejected_candidate_reference_ids": ["candidate_reference_id_to_reject"],
                "comments": "",
                "time_minutes": 6,
            },
            ensure_ascii=False,
            indent=2,
        ),
        "```",
        "",
        "`needs_adjudication` row의 핵심 shape:",
        "",
        "```json",
        json.dumps(
            {
                "annotation_status": "needs_adjudication",
                "gold_edges": [],
                "rejected_candidate_reference_ids": [],
                "comments": "source와 target은 보이지만 predicate 방향이 불명확함.",
            },
            ensure_ascii=False,
            indent=2,
        ),
        "```",
        "",
        "## Validation Commands",
        "",
        "반환 파일을 실제 반영하기 전 반드시 preflight를 먼저 실행한다.",
        "",
        "```bash",
        "python3 scripts/validate_cape_human_review_returns.py \\",
        "  --experiment-dir experiments/cape_kg_eacl_20260627",
        "```",
        "",
        "dry-run wrapper:",
        "",
        "```bash",
        "PYTHON_BIN=python3 LLM_PYTHON=python3 APPLY_IMPORTS=0 \\",
        "bash scripts/run_cape_human_return_apply.sh",
        "```",
        "",
        "실제 반영은 preflight와 dry-run이 모두 통과한 뒤 `APPLY_IMPORTS=1`로 실행한다.",
        "",
        "## Field Inventory Observed in Current Batch",
        "",
        f"- Sample file: `{metadata.get('sample_file')}`",
        f"- Top-level fields: `{', '.join(metadata.get('top_level_fields') or [])}`",
        f"- Silver candidate edge fields: `{', '.join(metadata.get('silver_candidate_edge_fields') or [])}`",
        f"- Component evidence span fields: `{', '.join(metadata.get('component_evidence_span_fields') or [])}`",
        "",
        "## Claim Boundary",
        "",
        "이 guide는 반환 파일 작성 오류를 줄이기 위한 운영 산출물이다. 현재 상태는 not human-gold이며, human-gold claim은 다음이 모두 끝난 뒤에만 가능하다: A/B annotation 반환, IAA 계산, adjudication 완료, adjudicated gold 기준 scoring.",
    ]
    return "\n".join(lines) + "\n"


def run(args):
    exp_dir = Path(args.experiment_dir)
    release_dir = exp_dir / "06_release"
    review_dir = exp_dir / "05_review"
    schema_path = exp_dir / "01_data/gold_annotation/annotation_schema.json"
    schema = read_json(schema_path, {}) or {}
    metadata = sample_metadata(exp_dir)
    rows = field_rows(schema, metadata)
    generated_at = datetime.now(timezone.utc).isoformat()

    payload = {
        "generated_at_utc": generated_at,
        "experiment_dir": str(exp_dir),
        "schema_path": str(schema_path),
        "claim_status": "annotation_return_field_guide_ready_pending_human_returns",
        "annotation_schema_summary": {
            "required_chunk_fields": schema.get("required_chunk_fields") or [],
            "gold_node_fields": schema.get("gold_node_fields") or [],
            "gold_edge_fields": schema.get("gold_edge_fields") or [],
            "completed_status_values": sorted(COMPLETED_ANNOTATION_STATUSES),
        },
        "editable_fields": ANNOTATION_EDITABLE_FIELDS,
        "immutable_fields": IMMUTABLE_FIELDS,
        "completed_status_values": sorted(COMPLETED_ANNOTATION_STATUSES),
        "allowed_annotation_statuses": sorted(ANNOTATION_STATUSES),
        "field_inventory": metadata,
        "field_rows": rows,
        "validation_commands": {
            "preflight": f"python3 scripts/validate_cape_human_review_returns.py --experiment-dir {exp_dir}",
            "dry_run": "PYTHON_BIN=python3 LLM_PYTHON=python3 APPLY_IMPORTS=0 bash scripts/run_cape_human_return_apply.sh",
            "apply": "PYTHON_BIN=python3 LLM_PYTHON=python3 APPLY_IMPORTS=1 bash scripts/run_cape_human_return_apply.sh",
        },
    }

    md_path = release_dir / "annotation_return_field_guide_ko.md"
    json_path = release_dir / "annotation_return_field_guide.json"
    csv_path = review_dir / "annotation_return_field_checklist.csv"
    write_text(md_path, render_md(payload))
    write_json(json_path, payload)
    write_csv(
        csv_path,
        rows,
        [
            "scope",
            "field",
            "edit_policy",
            "required_when_completed",
            "allowed_values",
            "validator_effect",
            "notes",
        ],
    )
    print(json.dumps({"markdown": str(md_path), "json": str(json_path), "csv": str(csv_path)}, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-dir", default=str(DEFAULT_EXP_DIR))
    run(parser.parse_args())


if __name__ == "__main__":
    main()
