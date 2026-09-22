#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml


QA_V2_DIR = Path(__file__).resolve().parent
PROJECT_DIR = QA_V2_DIR.parent
WORKSPACE_DIR = PROJECT_DIR.parent
if str(QA_V2_DIR) not in sys.path:
    sys.path.insert(0, str(QA_V2_DIR))

from paraphrase_pipeline import (  # noqa: E402
    OUTPUT_COLUMNS,
    LexicalOverlapScorer,
    build_parent_records,
    load_gold_overrides,
    normalize_text,
    read_csv,
    read_jsonl,
    validate_challenge_rows,
    write_json,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate a paraphrase challenge CSV")
    parser.add_argument("challenge_csv", type=Path)
    parser.add_argument(
        "--source-csv",
        type=Path,
        default=WORKSPACE_DIR / "AX" / "qa_dataset" / "outputs" / "full_terra_v1" / "qa_dataset.csv",
    )
    parser.add_argument(
        "--aligned-gold",
        type=Path,
        default=PROJECT_DIR / "runs" / "full_20260919" / "03_aligned_gold.jsonl",
    )
    parser.add_argument(
        "--gold-overrides",
        type=Path,
        default=QA_V2_DIR / "paraphrase_gold_overrides.json",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=PROJECT_DIR / "config" / "experiment.yaml",
    )
    parser.add_argument("--allow-incomplete", action="store_true")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--report-json", type=Path, default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    with args.config.open(encoding="utf-8") as handle:
        config: dict[str, Any] = yaml.safe_load(handle)
    parents = build_parent_records(
        read_csv(args.source_csv),
        read_jsonl(args.aligned_gold),
        excluded_qids=set(config["evaluation"].get("development_qids", [])),
        gold_overrides=load_gold_overrides(args.gold_overrides),
        limit=args.limit,
    )
    rows = read_csv(args.challenge_csv)
    errors, summary = validate_challenge_rows(
        rows, parents, allow_incomplete=args.allow_incomplete
    )
    columns = set(rows[0]) if rows else set()
    missing_columns = sorted(set(OUTPUT_COLUMNS) - columns)
    if missing_columns:
        errors.append(f"missing columns: {missing_columns}")

    parent_by_qid = {parent["qid"]: parent for parent in parents}
    scorer = LexicalOverlapScorer()
    for line_number, row in enumerate(rows, start=2):
        parent = parent_by_qid.get(normalize_text(row.get("parent_qa_id")))
        if parent is None:
            continue
        expected_score = scorer.score(normalize_text(row.get("question")), parent["evidence_texts"])
        try:
            stored_score = float(row.get("lexical_overlap_score", ""))
        except (TypeError, ValueError):
            errors.append(f"line {line_number}: invalid lexical_overlap_score")
            continue
        if abs(stored_score - expected_score) > 0.0000011:
            errors.append(
                f"line {line_number}: lexical overlap mismatch "
                f"stored={stored_score:.6f}, expected={expected_score:.6f}"
            )
        expected_band = scorer.band(expected_score)
        if normalize_text(row.get("lexical_overlap_band")) != expected_band:
            errors.append(
                f"line {line_number}: lexical band mismatch "
                f"stored={row.get('lexical_overlap_band')!r}, expected={expected_band!r}"
            )

    summary["error_count"] = len(errors)
    summary["status"] = "valid" if not errors else "invalid"
    if args.report_json:
        write_json(args.report_json, {"summary": summary, "errors": errors})
    if errors:
        for error in errors[:100]:
            print(f"ERROR: {error}")
        if len(errors) > 100:
            print(f"ERROR: ... {len(errors) - 100} additional errors")
        raise SystemExit(1)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
