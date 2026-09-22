#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping


BASE_DIR = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a synthetic general-question extension with frozen parent Gold"
    )
    parser.add_argument(
        "--source-csv",
        type=Path,
        default=BASE_DIR.parent / "AX/qa_dataset/outputs/full_terra_v1/qa_dataset.csv",
    )
    parser.add_argument(
        "--aligned-gold",
        type=Path,
        default=BASE_DIR / "runs/full_20260919/03_aligned_gold.jsonl",
    )
    parser.add_argument(
        "--specs",
        type=Path,
        default=Path(__file__).resolve().parent / "general_query_specs_20260920.json",
    )
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def portable_path(path: Path) -> str:
    """Record paths relative to KG-RAG instead of leaking a local home path."""
    return Path(os.path.relpath(path.resolve(), BASE_DIR.resolve())).as_posix()


def unique(values: Iterable[Any]) -> list[Any]:
    output: list[Any] = []
    for value in values:
        if value not in output:
            output.append(value)
    return output


def main() -> None:
    args = parse_args()
    with args.source_csv.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        source_fields = list(reader.fieldnames or [])
        source_rows = list(reader)
    source_by_qid = {row["qa_id"]: row for row in source_rows}
    if len(source_by_qid) != len(source_rows):
        raise ValueError("The source dataset contains duplicate qa_id values")

    gold_rows = [
        json.loads(line)
        for line in args.aligned_gold.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    gold_by_qid = {row["qid"]: row for row in gold_rows}
    specs = json.loads(args.specs.read_text(encoding="utf-8"))
    questions: list[Mapping[str, Any]] = specs["questions"]
    extension_qids = [str(item["qa_id"]) for item in questions]
    if len(extension_qids) != len(set(extension_qids)):
        raise ValueError("The general-question specification has duplicate qa_id values")
    if set(extension_qids) & set(source_by_qid):
        raise ValueError("General-question qa_id values overlap the source dataset")
    normalized_questions = [" ".join(str(item["question"]).split()) for item in questions]
    if len(normalized_questions) != len(set(normalized_questions)):
        raise ValueError("The general-question specification has duplicate questions")

    extra_fields = [
        "gold_taskframe_ids",
        "gold_pcf_ids",
        "question_origin",
        "query_stratum",
        "scenario_id",
        "parent_qids",
        "synthetic_extension",
        "graph_structure_required",
        "evidence_only_sufficient",
    ]
    fields = source_fields + [field for field in extra_fields if field not in source_fields]
    extension_rows: list[dict[str, str]] = []
    for item in questions:
        numeric_id = int(str(item["qa_id"]).rsplit("-", 1)[-1])
        partition = "synthetic_tuning" if numeric_id % 2 else "synthetic_holdout"
        parents = [str(value) for value in item["parent_qids"]]
        missing = [qid for qid in parents if qid not in source_by_qid or qid not in gold_by_qid]
        if missing:
            raise ValueError(f"Unknown parent qids for {item['qa_id']}: {missing}")
        parent_gold = [gold_by_qid[qid] for qid in parents]
        evidence_ids = unique(
            evidence_id
            for parent in parent_gold
            for evidence_id in parent.get("gold_evidence_ids", [])
        )
        if not evidence_ids:
            raise ValueError(f"No frozen Gold evidence for {item['qa_id']}: {parents}")
        taskframe_ids = unique(
            node_id
            for parent in parent_gold
            for node_id in parent.get("gold_taskframe_ids", [])
        )
        fact_ids = unique(
            node_id
            for parent in parent_gold
            for node_id in parent.get("gold_fact_ids", [])
        )
        pcf_ids = unique(
            node_id
            for parent in parent_gold
            for node_id in parent.get("gold_pcf_ids", [])
        )
        relation_types = unique(
            relation
            for parent in parent_gold
            for relation in parent.get("gold_relation_types", [])
        )
        answers = unique(
            source_by_qid[qid].get("answer", "").strip()
            for qid in parents
            if source_by_qid[qid].get("answer", "").strip()
        )
        row = {field: "" for field in fields}
        row.update(
            {
                "qa_id": str(item["qa_id"]),
                "question": " ".join(str(item["question"]).split()),
                "answer": "\n".join(answers),
                "chapter_no": "GENERAL",
                "chapter_title": "일반 수주·제안 업무 질문",
                "section_no": str(item["scenario_id"]),
                "section_title": str(item["query_stratum"]),
                "question_type": str(item["query_stratum"]),
                "difficulty": "medium",
                "answerable": "true",
                "source_answerable": "true",
                "ontology_answerable": "true",
                "expected_behavior": "answer_with_evidence",
                "evidence_mode": "frozen_parent_gold",
                "evidence_text": "[]",
                "gold_evidence_span_ids": json.dumps(evidence_ids, ensure_ascii=False),
                "gold_taskframe_ids": json.dumps(taskframe_ids, ensure_ascii=False),
                "gold_fact_ids": json.dumps(fact_ids, ensure_ascii=False),
                "gold_pcf_ids": json.dumps(pcf_ids, ensure_ascii=False),
                "gold_relation_types": json.dumps(relation_types, ensure_ascii=False),
                "gold_path": "[]",
                "min_hops": "",
                "split": partition,
                "review_status": "synthetic_not_human_reviewed",
                "review_notes": "Gold is inherited from frozen parent QA before retrieval.",
                "source_file": args.specs.name,
                "generation_model": "manual_scenario_generalization",
                "prompt_version": "general-operational-extension-v1",
                "generated_at": "2026-09-20",
                "question_origin": "synthetic_scenario_generalization",
                "query_stratum": str(item["query_stratum"]),
                "scenario_id": str(item["scenario_id"]),
                "parent_qids": json.dumps(parents, ensure_ascii=False),
                "synthetic_extension": "true",
                "graph_structure_required": "true" if len(parents) > 1 else "false",
                "evidence_only_sufficient": "false" if len(parents) > 1 else "true",
            }
        )
        extension_rows.append(row)

    output_rows = [{field: row.get(field, "") for field in fields} for row in source_rows]
    output_rows.extend(extension_rows)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(output_rows)

    manifest = {
        "name": specs["name"],
        "methodological_status": specs["methodological_status"],
        "source_count": len(source_rows),
        "extension_count": len(extension_rows),
        "expanded_count": len(output_rows),
        "strata": dict(Counter(row["query_stratum"] for row in extension_rows)),
        "partitions": dict(Counter(row["split"] for row in extension_rows)),
        "inputs": {
            "source_csv": {"path": portable_path(args.source_csv), "sha256": sha256(args.source_csv)},
            "aligned_gold": {"path": portable_path(args.aligned_gold), "sha256": sha256(args.aligned_gold)},
            "specs": {"path": portable_path(args.specs), "sha256": sha256(args.specs)},
        },
        "output": {"path": portable_path(args.output), "sha256": sha256(args.output)},
        "gold_policy": "Union of frozen aligned Gold from declared parent_qids; retrieval outputs are never read.",
    }
    manifest_path = args.output.with_suffix(".manifest.json")
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
