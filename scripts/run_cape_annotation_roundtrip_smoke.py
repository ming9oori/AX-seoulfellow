#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Run a non-claimable CAPE-KG annotation pipeline smoke test.

The test uses a tiny copy of existing annotation rows and silver candidates to
exercise import validation, IAA, adjudication draft generation, human-gold
validation, and scoring code paths without modifying the real gold files.
"""

import argparse
import csv
import json
import sys
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from compute_cape_annotation_iaa import compute as compute_iaa  # noqa: E402
from evaluate_cape_human_gold import (  # noqa: E402
    DEFAULT_VALID_FILES,
    METRIC_FIELDNAMES,
    build_gold_by_chunk,
    evaluate_predictions,
    load_chunk_context,
    load_schema,
    norm_evidence_id,
    validate_adjudication,
)
from import_cape_gold_annotation import merge_rows, validate_import  # noqa: E402
from prepare_cape_adjudication_draft import build_draft  # noqa: E402


DEFAULT_EXP_DIR = Path("experiments/cape_kg_eacl_20260627")
DEFAULT_OUT_DIR = DEFAULT_EXP_DIR / "06_release/annotation_roundtrip_smoke"


def read_jsonl(path):
    rows = []
    with Path(path).open("r", encoding="utf-8") as f:
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


def write_csv(path, rows, fieldnames):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({name: row.get(name, "") for name in fieldnames})


def issue(level, code, message, evidence=None):
    return {
        "level": level,
        "code": code,
        "message": message,
        "evidence": evidence or {},
    }


def evidence_ids_from_candidate(candidate):
    ids = []
    for value in candidate.get("evidence_anchor_ids") or []:
        normalized = norm_evidence_id(value)
        if normalized and normalized not in ids:
            ids.append(normalized)
    primary = candidate.get("primary_evidence") or {}
    primary_sentence = norm_evidence_id(primary.get("sentence_id"))
    if primary_sentence and primary_sentence not in ids:
        ids.insert(0, primary_sentence)
    return ids


def in_chunk_evidence_ids(candidate, row, chunk_context):
    evidence_ids = evidence_ids_from_candidate(candidate)
    allowed = chunk_context.get(row.get("chunk_id"), {}).get("sentence_ids") or set()
    if not allowed:
        return evidence_ids
    return [value for value in evidence_ids if norm_evidence_id(value) in allowed]


def chunk_sentence_text(row, chunk_context, sentence_id):
    sentence_id = norm_evidence_id(sentence_id)
    context = chunk_context.get(row.get("chunk_id"), {})
    text = (context.get("sentence_texts") or {}).get(sentence_id)
    if text:
        return text
    return row.get("chunk_text") or row.get("text") or ""


def candidate_is_valid_for_row(candidate, row, schema, chunk_context):
    predicate = str(candidate.get("predicate") or "").strip().upper()
    if predicate not in schema["edge_types"]:
        return False
    spec = schema["domain_range"].get(predicate)
    if spec:
        source_type = candidate.get("source_type")
        target_type = candidate.get("target_type")
        source_ok = not spec["subject_types"] or source_type in spec["subject_types"] or "Any" in spec["subject_types"]
        target_ok = not spec["object_types"] or target_type in spec["object_types"] or "Any" in spec["object_types"]
        if not source_ok or not target_ok:
            return False
    allowed = chunk_context.get(row.get("chunk_id"), {}).get("sentence_ids") or set()
    evidence_ids = evidence_ids_from_candidate(candidate)
    return bool(evidence_ids and (not allowed or any(norm_evidence_id(value) in allowed for value in evidence_ids)))


def select_rows(rows_a, rows_b, template_rows, schema, chunk_context, sample_size):
    by_b = {row.get("chunk_id"): row for row in rows_b}
    by_template = {row.get("chunk_id"): row for row in template_rows}
    selected = []
    for row_a in rows_a:
        chunk_id = row_a.get("chunk_id")
        row_b = by_b.get(chunk_id)
        template = by_template.get(chunk_id)
        if not row_b or not template:
            continue
        for candidate in row_a.get("silver_candidate_edges") or []:
            if candidate_is_valid_for_row(candidate, row_a, schema, chunk_context):
                selected.append((row_a, row_b, template, candidate))
                break
        if len(selected) >= sample_size:
            break
    return selected


def gold_from_candidate(candidate, row, chunk_context):
    evidence_ids = in_chunk_evidence_ids(candidate, row, chunk_context)[:1]
    primary = deepcopy(candidate.get("primary_evidence") or {})
    if primary:
        primary_sentence = norm_evidence_id(primary.get("sentence_id"))
        selected_sentence = evidence_ids[0] if evidence_ids else primary_sentence
        if evidence_ids and primary_sentence not in {norm_evidence_id(value) for value in evidence_ids}:
            span_text = chunk_sentence_text(row, chunk_context, selected_sentence)
            primary = {
                "evidence_anchor_id": selected_sentence,
                "sentence_id": selected_sentence,
                "page": primary.get("page"),
                "start_char": 0,
                "end_char": len(span_text),
                "text": span_text,
            }
        else:
            primary["evidence_anchor_id"] = selected_sentence
            primary["sentence_id"] = selected_sentence
    source_node = {
        "node_id": candidate.get("source_id"),
        "label": candidate.get("source_label"),
        "type": candidate.get("source_type"),
        "evidence_anchor_ids": evidence_ids,
    }
    target_node = {
        "node_id": candidate.get("target_id"),
        "label": candidate.get("target_label"),
        "type": candidate.get("target_type"),
        "evidence_anchor_ids": evidence_ids,
    }
    edge = {
        "source_id": candidate.get("source_id"),
        "source_label": candidate.get("source_label"),
        "source_type": candidate.get("source_type"),
        "predicate": candidate.get("predicate"),
        "target_id": candidate.get("target_id"),
        "target_label": candidate.get("target_label"),
        "target_type": candidate.get("target_type"),
        "evidence_anchor_ids": evidence_ids,
        "evidence_spans": [primary] if primary else [],
        "decision": "accepted",
        "reference_id": candidate.get("reference_id"),
    }
    return [source_node, target_node], [edge]


def reviewed_row(original, candidate, annotator_id, chunk_context):
    row = deepcopy(original)
    nodes, edges = gold_from_candidate(candidate, original, chunk_context)
    row["annotation_status"] = "completed"
    row["annotator_id"] = annotator_id
    row["gold_nodes"] = nodes
    row["gold_edges"] = edges
    row["rejected_candidate_reference_ids"] = []
    row["missing_but_supported_notes"] = []
    row["comments"] = "Roundtrip smoke test row; not human gold and not paper evidence."
    row["time_minutes"] = 0
    return row


def import_dry_run(original_rows, reviewed_rows, schema, chunk_context):
    issues = validate_import(original_rows, reviewed_rows, schema, chunk_context, allow_partial=False)
    errors = [item for item in issues if item["level"] == "error"]
    warnings = [item for item in issues if item["level"] == "warning"]
    merged_rows, summary = merge_rows(original_rows, reviewed_rows, allow_partial=False) if not errors else ([], {})
    return {
        "status": "validated_dry_run" if not errors else "failed_validation",
        "error_count": len(errors),
        "warning_count": len(warnings),
        "errors": errors[:100],
        "warnings": warnings[:100],
        "summary": summary,
    }, merged_rows


def render_report(payload):
    lines = [
        "# CAPE-KG Annotation Roundtrip Smoke Test",
        "",
        f"Generated: {payload['generated_at_utc']}",
        f"Overall status: `{payload['overall_status']}`",
        f"Claim status: `{payload['claim_status']}`",
        "",
        "This is an engineering smoke test only. It uses copied rows and silver candidates to verify the pipeline mechanics; it is not human gold and must not be used as paper evidence.",
        "",
        "## Summary",
        "",
        f"- Sample chunks: {payload['sample_size']}",
        f"- Import dry-run errors: {payload['import_error_count']}",
        f"- IAA status: {payload['iaa_summary'].get('status')}",
        f"- Completed paired chunks: {payload['iaa_summary'].get('completed_pair_chunks')}",
        f"- Adjudication validation errors: {payload['validation_summary'].get('validation_error_count')}",
        f"- Completed adjudicated chunks in smoke: {payload['validation_summary'].get('completed_adjudicated_chunks')}",
        f"- Smoke metric rows: {payload['metric_rows']}",
        "",
        "## Files",
        "",
    ]
    for key, value in payload["files"].items():
        lines.append(f"- {key}: `{value}`")
    if payload["issues"]:
        lines += ["", "## Issues", ""]
        for item in payload["issues"]:
            lines.append(f"- [{item['level']}] {item['code']}: {item['message']}")
    lines.append("")
    return "\n".join(lines)


def run(args):
    exp_dir = Path(args.experiment_dir)
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    gold_dir = exp_dir / "01_data/gold_annotation/full_120"

    schema = load_schema(exp_dir)
    chunk_context, chunk_issues = load_chunk_context(exp_dir)
    issues = [
        issue(item.get("level", "error"), item.get("code", "chunk_context_issue"), item.get("message", ""), item)
        for item in chunk_issues
    ]

    rows_a = read_jsonl(gold_dir / "annotator_A.jsonl")
    rows_b = read_jsonl(gold_dir / "annotator_B.jsonl")
    template_rows = read_jsonl(gold_dir / "adjudication.jsonl")
    selected = select_rows(rows_a, rows_b, template_rows, schema, chunk_context, args.sample_size)
    if len(selected) < args.sample_size:
        issues.append(
            issue(
                "error",
                "insufficient_smoke_rows",
                f"Only {len(selected)} valid rows were available for a {args.sample_size}-row smoke test.",
            )
        )

    target_a = [deepcopy(item[0]) for item in selected]
    target_b = [deepcopy(item[1]) for item in selected]
    template = [deepcopy(item[2]) for item in selected]
    reviewed_a = [reviewed_row(item[0], item[3], "A", chunk_context) for item in selected]
    reviewed_b = [reviewed_row(item[1], item[3], "B", chunk_context) for item in selected]

    files = {
        "a_target": str(out_dir / "a_target.jsonl"),
        "b_target": str(out_dir / "b_target.jsonl"),
        "a_reviewed": str(out_dir / "a_reviewed.jsonl"),
        "b_reviewed": str(out_dir / "b_reviewed.jsonl"),
        "a_merged": str(out_dir / "a_merged.jsonl"),
        "b_merged": str(out_dir / "b_merged.jsonl"),
        "adjudication_template": str(out_dir / "adjudication_template.jsonl"),
        "adjudication_draft": str(out_dir / "adjudication_draft.jsonl"),
        "iaa_summary": str(out_dir / "iaa_summary.json"),
        "validation_summary": str(out_dir / "validation_summary.json"),
        "metrics_csv": str(out_dir / "human_gold_metrics_smoke.csv"),
        "metrics_json": str(out_dir / "human_gold_metrics_smoke.json"),
        "summary": str(out_dir / "roundtrip_smoke_summary.json"),
        "report": str(out_dir / "roundtrip_smoke_report.md"),
    }

    write_jsonl(files["a_target"], target_a)
    write_jsonl(files["b_target"], target_b)
    write_jsonl(files["a_reviewed"], reviewed_a)
    write_jsonl(files["b_reviewed"], reviewed_b)
    write_jsonl(files["adjudication_template"], template)

    import_a, merged_a = import_dry_run(target_a, reviewed_a, schema, chunk_context)
    import_b, merged_b = import_dry_run(target_b, reviewed_b, schema, chunk_context)
    write_json(out_dir / "a_import_report.json", import_a)
    write_json(out_dir / "b_import_report.json", import_b)
    if import_a["error_count"] or import_b["error_count"]:
        issues.append(issue("error", "import_validation_failed", "Smoke reviewed rows failed import validation."))
    write_jsonl(files["a_merged"], merged_a)
    write_jsonl(files["b_merged"], merged_b)

    iaa_summary = compute_iaa(Path(files["a_merged"]), Path(files["b_merged"]))
    write_json(files["iaa_summary"], iaa_summary)
    if iaa_summary.get("status") != "computed":
        issues.append(issue("error", "iaa_not_computed", "IAA smoke did not produce computed metrics."))

    draft_rows, draft_summary = build_draft(
        Path(files["a_merged"]),
        Path(files["b_merged"]),
        Path(files["adjudication_template"]),
        "roundtrip_smoke",
    )
    write_jsonl(files["adjudication_draft"], draft_rows)
    write_json(out_dir / "adjudication_draft_summary.json", draft_summary)

    validation_summary = validate_adjudication(draft_rows, [], schema, chunk_context, Path(files["adjudication_draft"]))
    write_json(files["validation_summary"], validation_summary)
    if validation_summary.get("validation_error_count"):
        issues.append(issue("error", "adjudication_validation_failed", "Smoke adjudication draft has validation errors."))

    gold_by_chunk = build_gold_by_chunk(draft_rows)
    metrics = evaluate_predictions(exp_dir, DEFAULT_VALID_FILES, gold_by_chunk, schema)
    write_csv(files["metrics_csv"], metrics, METRIC_FIELDNAMES)
    write_json(files["metrics_json"], {"claim_status": "roundtrip_smoke_not_paper_evidence", "metrics": metrics})
    if not metrics:
        issues.append(issue("warning", "no_prediction_metrics", "Smoke validation passed, but no prediction rows were scored."))

    import_error_count = import_a["error_count"] + import_b["error_count"]
    blocking_issues = [item for item in issues if item["level"] == "error"]
    overall_status = "FAIL" if blocking_issues else "PASS"
    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "experiment_dir": str(exp_dir),
        "output_dir": str(out_dir),
        "overall_status": overall_status,
        "claim_status": "roundtrip_smoke_not_paper_evidence",
        "sample_size": len(selected),
        "requested_sample_size": args.sample_size,
        "import_error_count": import_error_count,
        "import_warning_count": import_a["warning_count"] + import_b["warning_count"],
        "iaa_summary": iaa_summary,
        "adjudication_draft_summary": draft_summary,
        "validation_summary": validation_summary,
        "metric_rows": len(metrics),
        "issues": issues,
        "files": files,
    }
    write_json(files["summary"], payload)
    write_text(files["report"], render_report(payload))
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    if overall_status != "PASS":
        raise SystemExit(1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-dir", default=str(DEFAULT_EXP_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUT_DIR))
    parser.add_argument("--sample-size", type=int, default=3)
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
