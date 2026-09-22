#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path


STRATA = (
    "direct_lookup",
    "paraphrase_alias",
    "multi_evidence",
    "pcf_hierarchy",
    "condition_relation",
    "unanswerable_hard_negative",
)
ORIGINS = {
    "practitioner_interview",
    "query_log",
    "training_session",
    "scenario_workshop",
}
BEHAVIORS = {"answer_with_evidence", "answer_with_limitation", "abstain"}
REVIEW_STATUSES = {"draft", "question_frozen", "annotated", "approved", "rejected"}
BOOLEAN_FIELDS = (
    "source_answerable",
    "ontology_answerable",
    "evidence_only_sufficient",
    "graph_structure_required",
)
JSON_FIELDS = (
    "gold_evidence_span_ids",
    "gold_taskframe_ids",
    "gold_fact_ids",
    "gold_pcf_ids",
    "gold_relation_types",
    "gold_path",
)
REQUIRED_COLUMNS = (
    "qa_id",
    "question",
    "question_origin",
    "query_stratum",
    "scenario_id",
    *BOOLEAN_FIELDS,
    "expected_behavior",
    "answer",
    "unanswerable_reason",
    *JSON_FIELDS,
    "min_hops",
    "split",
    "review_status",
    "reviewer_1",
    "reviewer_2",
    "review_notes",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate an independent QA V2 CSV")
    parser.add_argument("csv_path", type=Path)
    parser.add_argument(
        "--allow-incomplete",
        action="store_true",
        help="Validate the blank 60-slot collection template without requiring annotations",
    )
    parser.add_argument(
        "--skip-pilot-quota",
        action="store_true",
        help="Do not require exactly 10 rows for each of the six pilot strata",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    with args.csv_path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        columns = reader.fieldnames or []
        rows = list(reader)

    errors: list[str] = []
    missing_columns = [column for column in REQUIRED_COLUMNS if column not in columns]
    if missing_columns:
        errors.append(f"missing columns: {missing_columns}")

    qids = [row.get("qa_id", "").strip() for row in rows]
    if any(not qid for qid in qids):
        errors.append("empty qa_id")
    duplicates = [qid for qid, count in Counter(qids).items() if qid and count > 1]
    if duplicates:
        errors.append(f"duplicate qa_id: {duplicates}")

    counts = Counter(row.get("query_stratum", "").strip() for row in rows)
    unknown_strata = sorted(set(counts) - set(STRATA))
    if unknown_strata:
        errors.append(f"unknown query_stratum: {unknown_strata}")
    if not args.skip_pilot_quota:
        wrong = {stratum: counts[stratum] for stratum in STRATA if counts[stratum] != 10}
        if wrong or len(rows) != 60:
            errors.append(f"pilot quota must be 10 per stratum and 60 total: {wrong}, total={len(rows)}")

    for line_number, row in enumerate(rows, start=2):
        prefix = f"line {line_number} ({row.get('qa_id', '')})"
        parsed_json: dict[str, object] = {}
        status = row.get("review_status", "").strip()
        if status and status not in REVIEW_STATUSES:
            errors.append(f"{prefix}: invalid review_status={status!r}")
        behavior = row.get("expected_behavior", "").strip()
        if behavior and behavior not in BEHAVIORS:
            errors.append(f"{prefix}: invalid expected_behavior={behavior!r}")
        origin = row.get("question_origin", "").strip()
        if origin and origin not in ORIGINS:
            errors.append(f"{prefix}: invalid question_origin={origin!r}")
        for field in BOOLEAN_FIELDS:
            value = row.get(field, "").strip().lower()
            if value and value not in {"true", "false"}:
                errors.append(f"{prefix}: {field} must be true or false")
        for field in JSON_FIELDS:
            value = row.get(field, "").strip()
            if not value:
                continue
            try:
                parsed_json[field] = json.loads(value)
            except json.JSONDecodeError as exc:
                errors.append(f"{prefix}: invalid JSON in {field}: {exc.msg}")

        if args.allow_incomplete:
            continue
        for field in ("question", "question_origin", "scenario_id", *BOOLEAN_FIELDS, "expected_behavior"):
            if not row.get(field, "").strip():
                errors.append(f"{prefix}: empty required value {field}")
        if behavior in {"answer_with_evidence", "answer_with_limitation"}:
            if not row.get("answer", "").strip():
                errors.append(f"{prefix}: answer is required for {behavior}")
            if not parsed_json.get("gold_evidence_span_ids") and not parsed_json.get(
                "gold_pcf_ids"
            ):
                errors.append(f"{prefix}: an answerable row needs evidence or PCF Gold")
        if behavior == "abstain" and not row.get("unanswerable_reason", "").strip():
            errors.append(f"{prefix}: abstain requires unanswerable_reason")
        if status == "approved" and (
            not row.get("reviewer_1", "").strip() or not row.get("reviewer_2", "").strip()
        ):
            errors.append(f"{prefix}: approved rows require two reviewers")

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        raise SystemExit(1)

    print(f"OK: {args.csv_path} ({len(rows)} rows)")
    print("strata:", dict(sorted(counts.items())))
    print("review_status:", dict(sorted(Counter(row.get("review_status", "") for row in rows).items())))


if __name__ == "__main__":
    main()
