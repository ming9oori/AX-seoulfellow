#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Prepare expert review files for CAPE-KG NCS/PCF mapping candidates."""

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_EXP_DIR = Path("experiments/cape_kg_eacl_20260627")
DEFAULT_KG_DIR = Path("outputs")


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


def write_json(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


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


def review_row(candidate, standard):
    return {
        "standard": standard,
        "mapping_id": candidate.get("mapping_id"),
        "source_id": candidate.get("source_id"),
        "source_label": candidate.get("source_label"),
        "source_type": candidate.get("source_type"),
        "target_id": candidate.get("target_id"),
        "target_label": candidate.get("target_label"),
        "target_type": candidate.get("target_type"),
        "mapping_type": candidate.get("mapping_type"),
        "rank": candidate.get("rank"),
        "score": candidate.get("score"),
        "score_breakdown": candidate.get("score_breakdown", {}),
        "reason": candidate.get("reason"),
        "expert_decision": "",
        "relevance_grade": "",
        "explanation_quality_score": "",
        "review_status": "pending_expert_review",
        "reviewer_id": "",
        "comment": "",
        "claim_status": "not_gold_until_expert_reviewed",
    }


def build_protocol(path):
    path = Path(path)
    if path.exists():
        existing = path.read_text(encoding="utf-8")
        if "## 4. Accept 기준" in existing and "## 10. Completion checklist" in existing:
            return
    text = """# CAPE-KG NCS/PCF Mapping Expert Review Protocol

Review one source task at a time. For each NCS or PCF Top-5 candidate, decide
whether the target is an acceptable downstream alignment for the source task.

## Decision Values

- `accepted`: the target is a valid or defensible mapping for the task.
- `rejected`: the target is not a valid mapping.
- `unsure`: the reviewer cannot decide from the available evidence.

Optional `relevance_grade` values:

- `0`: unrelated
- `1`: weakly related but not acceptable
- `2`: acceptable
- `3`: best or highly appropriate

Optional `explanation_quality_score` values:

- `1`: the generated reason is misleading or not useful
- `2`: the reason is weak and misses important alignment evidence
- `3`: the reason is understandable but incomplete
- `4`: the reason is useful and mostly sufficient
- `5`: the reason clearly justifies the expert decision

Rows with `accepted` or relevance grade `2`/`3` are treated as expert-confirmed
positive mappings by the evaluator. `relevance_grade` is also used for nDCG@10.
`explanation_quality_score` is averaged over completed Top-5 groups as an
explanation-quality diagnostic. Use `review_status=completed` when a row has
been reviewed.

Optional browser workbench:

```bash
python3 scripts/build_cape_mapping_review_workbench.py \\
  --experiment-dir experiments/cape_kg_eacl_20260627
```

Open `01_data/mapping_review/mapping_review_workbench.html`, export the reviewed
JSONL, then validate and import it with:

```bash
python3 scripts/import_cape_mapping_review.py \\
  --experiment-dir experiments/cape_kg_eacl_20260627 \\
  --reviewed-file experiments/cape_kg_eacl_20260627/01_data/mapping_review/mapping_review_items.reviewed.jsonl
```

If the dry run passes, apply it with `--apply`. The importer checks immutable row
keys, validates decision/status values, and creates a backup before overwriting
`mapping_review_items.jsonl`.

After review, run:

```bash
python3 scripts/evaluate_cape_mapping_review.py \\
  --experiment-dir experiments/cape_kg_eacl_20260627
```
"""
    write_text(path, text)


def build_package(exp_dir, kg_dir):
    exp_dir = Path(exp_dir)
    kg_dir = Path(kg_dir)
    out_dir = exp_dir / "01_data/mapping_review"
    out_dir.mkdir(parents=True, exist_ok=True)

    ncs = [review_row(row, "NCS") for row in read_jsonl(kg_dir / "08_mapping/l2_ncs_mapping_candidates.jsonl")]
    pcf = [review_row(row, "PCF") for row in read_jsonl(kg_dir / "08_mapping/l2_pcf_mapping_candidates.jsonl")]
    all_rows = sorted(ncs + pcf, key=lambda r: (r["standard"], r["source_id"], int(r.get("rank") or 99), r["target_id"]))

    fieldnames = [
        "standard",
        "mapping_id",
        "source_id",
        "source_label",
        "target_id",
        "target_label",
        "target_type",
        "mapping_type",
        "rank",
        "score",
        "reason",
        "expert_decision",
        "relevance_grade",
        "explanation_quality_score",
        "review_status",
        "reviewer_id",
        "comment",
    ]
    write_jsonl(out_dir / "mapping_review_items.jsonl", all_rows)
    write_jsonl(out_dir / "mapping_review_ncs.jsonl", ncs)
    write_jsonl(out_dir / "mapping_review_pcf.jsonl", pcf)
    write_csv(out_dir / "mapping_review_sheet.csv", all_rows, fieldnames)
    build_protocol(out_dir / "mapping_review_protocol.md")

    by_standard = Counter(row["standard"] for row in all_rows)
    by_source = {(row["standard"], row["source_id"]) for row in all_rows}
    manifest = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "output_dir": str(out_dir),
        "review_items": str(out_dir / "mapping_review_items.jsonl"),
        "review_sheet": str(out_dir / "mapping_review_sheet.csv"),
        "protocol": str(out_dir / "mapping_review_protocol.md"),
        "ncs_review_file": str(out_dir / "mapping_review_ncs.jsonl"),
        "pcf_review_file": str(out_dir / "mapping_review_pcf.jsonl"),
        "candidate_rows": len(all_rows),
        "candidate_rows_by_standard": dict(sorted(by_standard.items())),
        "source_task_standard_pairs": len(by_source),
        "decision_values": ["accepted", "rejected", "unsure"],
        "positive_rule": "expert_decision=accepted or relevance_grade in {2,3}",
        "graded_mapping_metrics": ["hit_at_1", "hit_at_3", "hit_at_5", "precision_at_5", "mrr", "ndcg_at_10"],
        "explanation_quality_score_values": ["1", "2", "3", "4", "5"],
        "import_command": (
            "python3 scripts/import_cape_mapping_review.py --experiment-dir "
            "experiments/cape_kg_eacl_20260627 --reviewed-file "
            "experiments/cape_kg_eacl_20260627/01_data/mapping_review/"
            "mapping_review_items.reviewed.jsonl"
        ),
        "claim_status": "pending_expert_review",
    }
    write_json(out_dir / "mapping_review_manifest.json", manifest)
    return manifest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-dir", default=str(DEFAULT_EXP_DIR))
    parser.add_argument("--kg-dir", default=str(DEFAULT_KG_DIR))
    args = parser.parse_args()
    print(json.dumps(build_package(args.experiment_dir, args.kg_dir), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
