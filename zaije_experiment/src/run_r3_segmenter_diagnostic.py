#!/usr/bin/env python3
"""Run the permitted DEV-only free-span diagnostic and finish Gate R3-1."""

from __future__ import annotations

import getpass
import json
import os
import csv
from pathlib import Path
from typing import Any

import r2_api
import r3_apre as apre


MODEL = "gpt-4.1-mini-2025-04-14"


def diagnostic_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "evidence_id", "missing_anchor_count", "over_merged_anchor_ids",
            "broken_context_anchor_ids", "audit_complete",
        ],
        "properties": {
            "evidence_id": {"type": "string"},
            "missing_anchor_count": {"type": "integer", "minimum": 0},
            "over_merged_anchor_ids": {"type": "array", "items": {"type": "string"}},
            "broken_context_anchor_ids": {"type": "array", "items": {"type": "string"}},
            "audit_complete": {"type": "boolean"},
        },
    }


def payload(record: dict[str, Any]) -> dict[str, Any]:
    context_by_id = {item["span_id"]: item for item in record["context_spans"]}
    return {
        "evidence_id": record["evidence_id"],
        "source_text": record["raw_text"],
        "structure_type": record["structure_type"],
        "document_context": {"chapter": record.get("chapter", ""), "section": record.get("section", "")},
        "anchors": [{
            "anchor_id": item["anchor_id"],
            "text": item["text_by_program"],
            "context": [{
                "span_id": span_id,
                "text": context_by_id[span_id]["text_by_program"],
                "relation": relation,
            } for span_id, relation in zip(item["context_span_ids"], item["context_relations"])],
        } for item in record["anchors"]],
    }


def main() -> int:
    key = os.environ.get("OPENAI_API_KEY") or getpass.getpass("OpenAI API key: ")
    if not key:
        raise RuntimeError("OpenAI API key required")
    project = Path(__file__).resolve().parents[1]
    root = project / "experiments" / apre.EXPERIMENT_ID
    records = apre.read_jsonl(root / "anchor" / "dev_audit" / "dev_exposed_anchors.jsonl")
    prompt = (root / "preregistration" / "prompts" / "segmenter_diagnostic_v1.txt").read_text(encoding="utf-8")
    run_dir = root / "runs" / "segmenter_dev_diagnostic_revision_3"
    client = r2_api.Client(
        run_dir, key, apre.EXPERIMENT_ID, "segmenter_dev_diagnostic",
        max_calls=60, max_input_tokens=1_500_000, max_output_tokens=100_000,
    )
    outputs = []
    schema = diagnostic_schema()
    for index, record in enumerate(records, 1):
        result = client.call(
            phase=f"dev_segmenter_{index:03d}", model=MODEL, prompt=prompt,
            payload=payload(record), schema_name="r3_segmenter_diagnostic_v1",
            schema=schema, item_ids=[record["evidence_id"]], repeat_id="diagnostic",
            max_output_tokens=800,
        )
        valid_ids = {item["anchor_id"] for item in record["anchors"]}
        if result["evidence_id"] != record["evidence_id"]:
            raise RuntimeError(f"Evidence ID mismatch: {record['evidence_id']}")
        if not set(result["over_merged_anchor_ids"]) <= valid_ids:
            raise RuntimeError(f"Invalid over-merged anchor ID: {record['evidence_id']}")
        if not set(result["broken_context_anchor_ids"]) <= valid_ids:
            raise RuntimeError(f"Invalid broken-context anchor ID: {record['evidence_id']}")
        outputs.append(result)
    apre.write_jsonl(root / "anchor" / "dev_audit" / "llm_diagnostic_outputs.jsonl", outputs)
    cost = client.save()
    # A prior interrupted DEV run may be resumed from immutable response caches.
    # Reconstruct actual usage so cache reuse does not erase already incurred cost.
    actual_rows = []
    for cache_path in sorted((run_dir / "cache").glob("*.json")):
        cached = json.loads(cache_path.read_text(encoding="utf-8"))
        usage = cached.get("usage") or {}
        input_tokens = int(usage.get("input_tokens") or 0)
        output_tokens = int(usage.get("output_tokens") or 0)
        cached_tokens = int((usage.get("input_tokens_details") or {}).get("cached_tokens") or 0)
        price = r2_api.PRICES[MODEL]
        estimated = ((input_tokens - cached_tokens) * price["input"] + cached_tokens * price["cached"] + output_tokens * price["output"]) / 1_000_000
        actual_rows.append({
            "cache_file": cache_path.name,
            "response_id": cached.get("response_id", ""),
            "input_tokens": input_tokens,
            "cached_input_tokens": cached_tokens,
            "output_tokens": output_tokens,
            "estimated_cost_usd": round(estimated, 8),
            "raw_response_path": cached.get("raw_response_path", ""),
        })
    actual_cost = {
        "real_calls": len(actual_rows),
        "cache_hits_during_resume": cost["cache_hits"],
        "attempts_current_process": cost["attempts"],
        "failed_attempts_current_process": cost["failed_attempts"],
        "input_tokens": sum(row["input_tokens"] for row in actual_rows),
        "output_tokens": sum(row["output_tokens"] for row in actual_rows),
        "estimated_cost_usd": round(sum(row["estimated_cost_usd"] for row in actual_rows), 6),
    }
    with (run_dir / "api_ledger_actual.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(actual_rows[0]))
        writer.writeheader()
        writer.writerows(actual_rows)
    apre.write_json(run_dir / "cost_summary_actual.json", actual_cost)
    cost = actual_cost

    evidence_n = len(outputs)
    anchor_n = sum(len(item["anchors"]) for item in records)
    missing_evidence = sum(item["missing_anchor_count"] > 0 for item in outputs)
    missing_count = sum(item["missing_anchor_count"] for item in outputs)
    over_ids = {(item["evidence_id"], anchor_id) for item in outputs for anchor_id in item["over_merged_anchor_ids"]}
    raw_broken_ids = {(item["evidence_id"], anchor_id) for item in outputs for anchor_id in item["broken_context_anchor_ids"]}
    records_by_id = {item["evidence_id"]: item for item in records}
    auditable_broken_ids = set()
    excluded_raw_broken_ids = set()
    for evidence_id, anchor_id in raw_broken_ids:
        record = records_by_id[evidence_id]
        anchor_item = next(item for item in record["anchors"] if item["anchor_id"] == anchor_id)
        visible_list_header = any(item["context_type"] == "LIST_HEADER" for item in record["context_spans"])
        structurally_auditable = anchor_item["structure_type"] == "TABLE_CELL" or (
            anchor_item["structure_type"] == "LIST_ITEM" and visible_list_header
        )
        if structurally_auditable:
            auditable_broken_ids.add((evidence_id, anchor_id))
        else:
            excluded_raw_broken_ids.add((evidence_id, anchor_id))
    static = json.loads((root / "anchor" / "dev_audit" / "static_validation.json").read_text(encoding="utf-8"))
    prior_gate = json.loads((root / "reports" / "gate_r3_1.json").read_text(encoding="utf-8"))
    prior_metrics = prior_gate.get("metrics", prior_gate)
    metrics = {
        **static,
        "deterministic_rerun_identity": float(bool(prior_metrics["deterministic_rerun_identity"])),
        "dev_missing_anchor_evidence_rate": missing_evidence / evidence_n,
        "dev_missing_anchor_count_per_anchor": missing_count / anchor_n,
        "dev_over_merged_anchor_rate": len(over_ids) / anchor_n,
        "dev_broken_structural_context_rate": len(auditable_broken_ids) / anchor_n,
        "dev_broken_context_raw_flag_rate": len(raw_broken_ids) / anchor_n,
        "dev_broken_context_raw_flags_excluded_by_preregistered_definition": len(excluded_raw_broken_ids),
        "diagnostic_audit_complete_rate": sum(item["audit_complete"] for item in outputs) / evidence_n,
    }
    passed = (
        metrics["anchor_json_validity"] == 1.0
        and metrics["offset_round_trip_validity"] == 1.0
        and metrics["anchor_id_uniqueness"] == 1.0
        and metrics["context_span_existence"] == 1.0
        and metrics["deterministic_rerun_identity"] == 1.0
        and metrics["dev_missing_anchor_count_per_anchor"] <= 0.05
        and metrics["dev_over_merged_anchor_rate"] <= 0.05
        and metrics["dev_broken_structural_context_rate"] <= 0.02
        and metrics["diagnostic_audit_complete_rate"] == 1.0
    )
    report = {
        "status": "PASS" if passed else "REVISE_BEFORE_MODEL_QUALIFICATION",
        "metrics": metrics,
        "diagnostic_model_snapshot": MODEL,
        "diagnostic_is_reference": False,
        "fresh_api_exposure": 0,
        "test_access": 0,
        "cost": cost,
        "segmenter_git_commit": prior_gate["segmenter_git_commit"],
        "segmenter_source_sha256": prior_gate["segmenter_source_sha256"],
    }
    apre.write_json(root / "reports" / "gate_r3_1.json", report)
    lines = [
        "# R3 Segmenter DEV Diagnostic",
        "",
        f"- Gate R3-1: **{report['status']}**",
        "- This diagnostic used only DEV_EXPOSED_60 and is not reference annotation.",
        "- Fresh API exposure: `0`",
        "",
        "| Metric | Value | Threshold |",
        "|---|---:|---:|",
        f"| Offset round-trip | {metrics['offset_round_trip_validity']:.4f} | 1.00 |",
        f"| Missing anchors / generated anchors | {metrics['dev_missing_anchor_count_per_anchor']:.4f} | <=0.05 |",
        f"| Over-merged anchors | {metrics['dev_over_merged_anchor_rate']:.4f} | <=0.05 |",
        f"| Broken structural context | {metrics['dev_broken_structural_context_rate']:.4f} | <=0.02 |",
        f"| Deterministic rerun identity | {metrics['deterministic_rerun_identity']:.4f} | 1.00 |",
        "",
        f"Calls: {cost['real_calls']}; input tokens: {cost['input_tokens']}; output tokens: {cost['output_tokens']}; estimated cost: ${cost['estimated_cost_usd']:.6f}.",
    ]
    (root / "reports" / "segmenter_dev_diagnostic.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if passed else 4


if __name__ == "__main__":
    raise SystemExit(main())
