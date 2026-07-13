#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Prepare expert-review files for CAPE-KG NCS-PCF crosswalk candidates."""

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_EXP_DIR = Path("experiments/cape_kg_eacl_20260627")

EDITABLE_FIELDS = [
    "expert_decision",
    "utility_grade",
    "explanation_quality_score",
    "review_status",
    "reviewer_id",
    "comment",
]

FIELDNAMES = [
    "crosswalk_id",
    "source_id",
    "source_label",
    "crosswalk_rank",
    "ncs_target_id",
    "ncs_target_label",
    "pcf_target_id",
    "pcf_target_label",
    "ncs_rank",
    "pcf_rank",
    "bridge_score",
    "rank_component",
    "score_component",
    "reason_component",
    "supporting_mapping_ids_json",
    "supporting_reasons_json",
    "bridge_support_type",
    "expert_decision",
    "utility_grade",
    "explanation_quality_score",
    "review_status",
    "reviewer_id",
    "comment",
    "claim_status",
]


def read_csv_rows(path):
    path = Path(path)
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, fieldnames):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def write_jsonl(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


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


def write_json(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def as_int(value, default=999):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def row_key(row):
    return (
        str(row.get("crosswalk_id") or "").strip(),
        str(row.get("source_id") or "").strip(),
        str(row.get("ncs_target_id") or "").strip(),
        str(row.get("pcf_target_id") or "").strip(),
        str(row.get("crosswalk_rank") or "").strip(),
    )


def review_row(row):
    out = {field: row.get(field, "") for field in FIELDNAMES if field not in EDITABLE_FIELDS + ["claim_status"]}
    out.update(
        {
            "expert_decision": "",
            "utility_grade": "",
            "explanation_quality_score": "",
            "review_status": "pending_expert_review",
            "reviewer_id": "",
            "comment": "",
            "claim_status": "not_gold_until_crosswalk_expert_reviewed",
        }
    )
    return out


def build_protocol(path):
    text = """# CAPE-KG NCS-PCF Crosswalk Expert Review Protocol

This package reviews bridge-supported NCS-PCF crosswalk candidates. Each row
connects one Layer2 DomainTask to one NCS candidate and one PCF candidate.

## Decision Values

- `accepted`: the NCS-PCF pair is a defensible crosswalk for the shared Layer2 task.
- `rejected`: the pair is not a valid or useful crosswalk.
- `unsure`: the reviewer cannot decide from the available evidence.

## Utility Grade

- `0`: unrelated or misleading pair
- `1`: weakly related but not useful as a crosswalk
- `2`: useful/defensible crosswalk candidate
- `3`: strong crosswalk candidate

## Explanation Quality Score

- `1`: supporting reasons are misleading or not useful
- `2`: supporting reasons are weak
- `3`: supporting reasons are understandable but incomplete
- `4`: supporting reasons are mostly sufficient
- `5`: supporting reasons clearly justify the decision

Complete rows must include `expert_decision`, `utility_grade`,
`explanation_quality_score`, `review_status=completed`, `reviewer_id`, and a
short `comment`. Completed source-task groups become evaluable only when every
ranked candidate for that source task has been reviewed.

Expected return file:

```text
experiments/cape_kg_eacl_20260627/01_data/crosswalk_review/crosswalk_review_items.reviewed.jsonl
```

Validate/import:

```bash
python3 scripts/import_cape_crosswalk_review.py \\
  --experiment-dir experiments/cape_kg_eacl_20260627 \\
  --reviewed-file experiments/cape_kg_eacl_20260627/01_data/crosswalk_review/crosswalk_review_items.reviewed.jsonl
```

If the dry run passes, add `--apply`, then refresh the evaluation:

```bash
python3 scripts/evaluate_cape_crosswalk_review.py \\
  --experiment-dir experiments/cape_kg_eacl_20260627
```
"""
    write_text(path, text)


def build_package(exp_dir):
    exp_dir = Path(exp_dir)
    source_csv = exp_dir / "04_evaluation/ncs_pcf_crosswalk_candidates.csv"
    out_dir = exp_dir / "01_data/crosswalk_review"
    source_rows = read_csv_rows(source_csv)
    existing_by_key = {row_key(row): row for row in read_jsonl(out_dir / "crosswalk_review_items.jsonl")}
    review_rows = [review_row(row) for row in source_rows]
    for row in review_rows:
        previous = existing_by_key.get(row_key(row))
        if not previous:
            continue
        for field in EDITABLE_FIELDS + ["claim_status"]:
            if previous.get(field) not in (None, ""):
                row[field] = previous.get(field)
    review_rows.sort(key=lambda row: (row.get("source_id") or "", as_int(row.get("crosswalk_rank")), row.get("crosswalk_id") or ""))

    write_jsonl(out_dir / "crosswalk_review_items.jsonl", review_rows)
    write_csv(out_dir / "crosswalk_review_sheet.csv", review_rows, FIELDNAMES)
    build_protocol(out_dir / "crosswalk_review_protocol.md")

    source_counts = Counter(row.get("source_id") for row in review_rows)
    rank_counts = Counter(str(row.get("crosswalk_rank") or "") for row in review_rows)
    manifest = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "experiment_dir": str(exp_dir),
        "source_candidates_csv": str(source_csv),
        "output_dir": str(out_dir),
        "review_items": str(out_dir / "crosswalk_review_items.jsonl"),
        "review_sheet": str(out_dir / "crosswalk_review_sheet.csv"),
        "protocol": str(out_dir / "crosswalk_review_protocol.md"),
        "expected_reviewed_file": str(out_dir / "crosswalk_review_items.reviewed.jsonl"),
        "candidate_rows": len(review_rows),
        "source_task_count": len(source_counts),
        "rows_per_source_min": min(source_counts.values()) if source_counts else 0,
        "rows_per_source_max": max(source_counts.values()) if source_counts else 0,
        "rank_counts": dict(sorted(rank_counts.items(), key=lambda item: as_int(item[0]))),
        "decision_values": ["accepted", "rejected", "unsure"],
        "utility_grade_values": ["0", "1", "2", "3"],
        "explanation_quality_score_values": ["1", "2", "3", "4", "5"],
        "claim_status": "pending_crosswalk_expert_review",
        "import_command": (
            "python3 scripts/import_cape_crosswalk_review.py --experiment-dir "
            "experiments/cape_kg_eacl_20260627 --reviewed-file "
            "experiments/cape_kg_eacl_20260627/01_data/crosswalk_review/"
            "crosswalk_review_items.reviewed.jsonl"
        ),
    }
    write_json(out_dir / "crosswalk_review_manifest.json", manifest)
    return manifest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-dir", default=str(DEFAULT_EXP_DIR))
    args = parser.parse_args()
    print(json.dumps(build_package(args.experiment_dir), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
