#!/usr/bin/env python3
"""Prepare cached LLM Aspect profiles for a controlled extractor comparison.

Only the Aspect contents differ between the local and LLM arms.  The routing
decision is copied from the local question-only applicability controller so an
LLM profile is not advantaged merely because older caches predate that field.
"""

from __future__ import annotations

import argparse
import csv
import json
from copy import deepcopy
from pathlib import Path
from typing import Any, Mapping


LOCAL_METHOD = "P1U_ATTENTION_SEEKER_ASPECT_CROSS_ENCODER_MMR"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Adapt cached LLM Aspect rows to the frozen common routing gate"
    )
    parser.add_argument("--qa-csv", type=Path, required=True)
    parser.add_argument("--llm-aspects", type=Path, required=True)
    parser.add_argument("--local-aspects", type=Path, required=True)
    parser.add_argument("--query-profiles", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--output-local",
        type=Path,
        help="Optionally write the matching local rows in the same QA order",
    )
    parser.add_argument("--output-query-profiles", type=Path)
    parser.add_argument("--limit", type=int)
    return parser.parse_args()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def normalized(value: Any) -> str:
    return " ".join(str(value or "").split())


def by_qid(rows: list[Mapping[str, Any]], label: str) -> dict[str, Mapping[str, Any]]:
    output: dict[str, Mapping[str, Any]] = {}
    for row in rows:
        qid = str(row.get("qid") or "")
        if not qid:
            raise ValueError(f"{label} contains a row without qid")
        if qid in output:
            raise ValueError(f"{label} contains a duplicate qid: {qid}")
        output[qid] = row
    return output


def main() -> None:
    args = parse_args()
    with args.qa_csv.open(encoding="utf-8-sig", newline="") as handle:
        qa_rows = list(csv.DictReader(handle))
    if args.limit is not None:
        if args.limit < 1:
            raise ValueError("limit must be positive")
        qa_rows = qa_rows[: args.limit]
    llm = by_qid(read_jsonl(args.llm_aspects), "LLM profiles")
    local = by_qid(read_jsonl(args.local_aspects), "local profiles")
    if bool(args.query_profiles) != bool(args.output_query_profiles):
        raise ValueError(
            "query-profiles and output-query-profiles must be supplied together"
        )
    query_profiles = (
        by_qid(read_jsonl(args.query_profiles), "query profiles")
        if args.query_profiles
        else {}
    )

    output: list[dict[str, Any]] = []
    local_output: list[dict[str, Any]] = []
    query_profile_output: list[dict[str, Any]] = []
    for qa in qa_rows:
        qid = str(qa["qa_id"])
        if qid not in llm or qid not in local:
            raise ValueError(f"Missing cached Aspect profile for {qid}")
        llm_row = llm[qid]
        local_row = local[qid]
        question = normalized(qa["question"])
        if normalized(llm_row.get("question")) != question:
            raise ValueError(f"LLM question mismatch for {qid}")
        if normalized(local_row.get("question")) != question:
            raise ValueError(f"Local question mismatch for {qid}")

        variants = local_row.get("variants", {})
        local_profile = variants.get(LOCAL_METHOD, {}) if isinstance(variants, dict) else {}
        applicability = local_profile.get("applicability")
        if not isinstance(applicability, dict) or "score" not in applicability:
            raise ValueError(f"Local applicability is missing for {qid}")
        aspects = deepcopy(llm_row.get("aspects"))
        if not isinstance(aspects, dict) or not aspects:
            raise ValueError(f"LLM Aspect content is missing for {qid}")
        aspects["applicability"] = deepcopy(applicability)
        aspects["comparison_adapter"] = {
            "version": "common-question-only-gate-v1",
            "gate_source": LOCAL_METHOD,
            "content_source": "cached_llm_aspect_extraction",
            "gold_or_evidence_used": False,
        }
        output.append(
            {
                "qid": qid,
                "question": question,
                "aspects": aspects,
                "response_id": llm_row.get("response_id", ""),
                "cached": True,
                "error": llm_row.get("error", ""),
            }
        )
        local_output.append(deepcopy(dict(local_row)))
        if query_profiles:
            if qid not in query_profiles:
                raise ValueError(f"Missing query profile for {qid}")
            query_row = query_profiles[qid]
            if normalized(query_row.get("question")) != question:
                raise ValueError(f"Query Profile question mismatch for {qid}")
            query_profile_output.append(deepcopy(dict(query_row)))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in output),
        encoding="utf-8",
    )
    print(f"wrote {args.output} ({len(output)} rows)")
    if args.output_local:
        args.output_local.parent.mkdir(parents=True, exist_ok=True)
        args.output_local.write_text(
            "".join(
                json.dumps(row, ensure_ascii=False) + "\n" for row in local_output
            ),
            encoding="utf-8",
        )
        print(f"wrote {args.output_local} ({len(local_output)} rows)")
    if args.output_query_profiles:
        args.output_query_profiles.parent.mkdir(parents=True, exist_ok=True)
        args.output_query_profiles.write_text(
            "".join(
                json.dumps(row, ensure_ascii=False) + "\n"
                for row in query_profile_output
            ),
            encoding="utf-8",
        )
        print(
            f"wrote {args.output_query_profiles} "
            f"({len(query_profile_output)} rows)"
        )


if __name__ == "__main__":
    main()
