#!/usr/bin/env python3
"""Lock, submit, and evaluate the fresh APRE pointwise claimhood Batch."""

from __future__ import annotations

import getpass
import hashlib
import json
import os
import statistics
from collections import Counter
from pathlib import Path
from typing import Any

import r2_api
import r3_apre as apre
import r3_batch_api


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def f1(left: set[str], right: set[str]) -> float:
    if not left and not right:
        return 1.0
    if not left or not right:
        return 0.0
    precision = len(left & right) / len(left)
    recall = len(left & right) / len(right)
    return 2 * precision * recall / (precision + recall) if precision + recall else 0.0


def extract_text(response: dict[str, Any]) -> str:
    return r2_api.extract_text(response)


def main() -> int:
    key = os.environ.get("OPENAI_API_KEY") or getpass.getpass("OpenAI API key: ")
    if not key:
        raise RuntimeError("OpenAI API key required")
    project = Path(__file__).resolve().parents[1]
    root = project / "experiments" / apre.EXPERIMENT_ID
    gate0 = read_json(root / "reports" / "gate_r3_0.json")
    gate1 = read_json(root / "reports" / "gate_r3_1.json")
    gate2 = read_json(root / "reports" / "gate_r3_2.json")
    if gate0["status"] != "PASS" or gate1["status"] != "PASS" or gate2["status"] != "PASS":
        raise RuntimeError("R3-0 through R3-2 must pass before fresh claimhood")
    model_lock = read_json(root / "locks" / "primary_model_lock.json")
    model = model_lock["model_snapshot"]
    if model != "gpt-4.1-2025-04-14":
        raise RuntimeError("Unexpected locked primary model")

    imported = root / "data" / "r3_pilot_60_imported_unexposed.jsonl"
    imported_lock = read_json(root / "locks" / "imported_fresh60_lock.json")
    if file_sha(imported) != imported_lock["source_membership_sha256"]:
        raise RuntimeError("Imported fresh membership changed")
    anchor_path = root / "anchor" / "fresh60" / "anchors_pre_api.jsonl"
    records = apre.read_jsonl(anchor_path)
    anchors = [(record, anchor) for record in records for anchor in record["anchors"]]
    if len(records) != 60 or len(anchors) != 70:
        raise RuntimeError(f"Unexpected fresh anchor cardinality {len(records)}/{len(anchors)}")

    prompt_path = root / "preregistration" / "prompts" / "claimhood_v1.txt"
    schema_path = root / "preregistration" / "claimhood_schema_v1.json"
    prompt = prompt_path.read_text(encoding="utf-8")
    schema = read_json(schema_path)
    prompt_schema_lock = read_json(root / "locks" / "prompt_schema_lock.json")
    for path in [prompt_path, schema_path]:
        relative = str(path.relative_to(root))
        if file_sha(path) != prompt_schema_lock[relative]:
            raise RuntimeError(f"Prompt/schema lock mismatch: {relative}")

    context_maps = {record["evidence_id"]: {item["span_id"]: item for item in record["context_spans"]} for record in records}

    def payload(record: dict[str, Any], anchor: dict[str, Any], source_override: str | None = None) -> dict[str, Any]:
        by_id = context_maps[record["evidence_id"]]
        return {
            "evidence_id": record["evidence_id"], "anchor_id": anchor["anchor_id"],
            "document_context": {"chapter": record.get("chapter", ""), "section": record.get("section", "")},
            "source_text": record["raw_text"] if source_override is None else source_override,
            "anchor_text": anchor["text_by_program"],
            "context_spans": [] if source_override is not None else [{
                "span_id": span_id, "text": by_id[span_id]["text_by_program"], "relation": relation,
            } for span_id, relation in zip(anchor["context_span_ids"], anchor["context_relations"])],
        }

    run_dir = root / "runs" / "fresh_claimhood_batch"
    input_path = run_dir / "batch_input.jsonl"
    manifest_path = run_dir / "logical_request_manifest.jsonl"
    run_dir.mkdir(parents=True, exist_ok=True)
    request_rows = []
    manifest_rows = []
    for index, (record, anchor) in enumerate(anchors, 1):
        for repeat in (1, 2, 3):
            custom_id = f"claim_{index:03d}_r{repeat}"
            request_rows.append({
                "custom_id": custom_id, "method": "POST", "url": "/v1/responses",
                "body": {
                    "model": model,
                    "input": [
                        {"role": "system", "content": [{"type": "input_text", "text": prompt}]},
                        {"role": "user", "content": [{"type": "input_text", "text": apre.canonical(payload(record, anchor))}]},
                    ],
                    "text": {"format": {"type": "json_schema", "name": "r3_fresh_claimhood_v1", "strict": True, "schema": schema}},
                    "temperature": 0, "max_output_tokens": 300,
                },
            })
            manifest_rows.append({
                "custom_id": custom_id, "kind": "claimhood", "repeat_id": repeat,
                "evidence_id": record["evidence_id"], "anchor_id": anchor["anchor_id"],
            })
    mismatch_n = 20
    for index, (record, anchor) in enumerate(anchors[:mismatch_n], 1):
        mismatch_record = anchors[(index + 29) % len(anchors)][0]
        custom_id = f"mismatch_{index:03d}"
        request_rows.append({
            "custom_id": custom_id, "method": "POST", "url": "/v1/responses",
            "body": {
                "model": model,
                "input": [
                    {"role": "system", "content": [{"type": "input_text", "text": prompt}]},
                    {"role": "user", "content": [{"type": "input_text", "text": apre.canonical(payload(record, anchor, mismatch_record["raw_text"]))}]},
                ],
                "text": {"format": {"type": "json_schema", "name": "r3_fresh_claimhood_control_v1", "strict": True, "schema": schema}},
                "temperature": 0, "max_output_tokens": 300,
            },
        })
        manifest_rows.append({
            "custom_id": custom_id, "kind": "mismatch_control", "repeat_id": 0,
            "evidence_id": record["evidence_id"], "anchor_id": anchor["anchor_id"],
        })
    if len(request_rows) != 230:
        raise RuntimeError("Fresh request count changed")
    apre.write_jsonl(input_path, request_rows)
    apre.write_jsonl(manifest_path, manifest_rows)

    execution_lock = {
        "experiment_id": apre.EXPERIMENT_ID,
        "phase": "fresh_claimhood",
        "primary_model_snapshot": model,
        "falsifier_model_snapshot": read_json(root / "locks" / "falsifier_model_lock.json")["model_snapshot"],
        "imported_fresh60_sha256": file_sha(imported),
        "fresh_anchor_file_sha256": file_sha(anchor_path),
        "segmenter_source_sha256": gate1["segmenter_source_sha256"],
        "claimhood_prompt_sha256": file_sha(prompt_path),
        "claimhood_schema_sha256": file_sha(schema_path),
        "logical_request_manifest_sha256": file_sha(manifest_path),
        "batch_input_sha256": file_sha(input_path),
        "anchor_count": len(anchors), "claimhood_repeats": 3,
        "mismatch_control_count": mismatch_n, "request_count": len(request_rows),
        "candidate_order_exposure": 0, "request_cap": 3000,
        "same_id_repilot_allowed": False, "test_access": 0,
    }
    lock_path = root / "locks" / "fresh_claimhood_execution_lock.json"
    if lock_path.exists() and read_json(lock_path) != execution_lock:
        raise RuntimeError("Fresh claimhood lock already exists with different contents")
    apre.write_json(lock_path, execution_lock)

    r3_batch_api.submit_and_wait(
        api_key=key, input_path=input_path, run_dir=run_dir,
        metadata={"experiment_id": apre.EXPERIMENT_ID, "phase": "fresh_claimhood"},
    )
    output_rows = apre.read_jsonl(run_dir / "batch_output.jsonl")
    output_by = {item["custom_id"]: item for item in output_rows}
    if len(output_by) != len(request_rows):
        raise RuntimeError(f"Batch output cardinality mismatch {len(output_by)}/{len(request_rows)}")
    manifest_by = {item["custom_id"]: item for item in manifest_rows}
    parsed_rows = []
    input_tokens = output_tokens = cached_tokens = 0
    for custom_id, meta in manifest_by.items():
        item = output_by[custom_id]
        response = item.get("response") or {}
        if response.get("status_code") != 200 or item.get("error"):
            raise RuntimeError(f"Batch request failed: {custom_id}")
        body = response["body"]
        parsed = json.loads(extract_text(body))
        if parsed["anchor_id"] != meta["anchor_id"]:
            raise RuntimeError(f"Anchor ID mismatch: {custom_id}")
        usage = body.get("usage") or {}
        input_tokens += int(usage.get("input_tokens") or 0)
        output_tokens += int(usage.get("output_tokens") or 0)
        cached_tokens += int((usage.get("input_tokens_details") or {}).get("cached_tokens") or 0)
        parsed_rows.append({**meta, "response_id": body.get("id"), **parsed})
    apre.write_jsonl(root / "annotation" / "claimhood" / "fresh_claimhood_outputs.jsonl", parsed_rows)

    claims = [item for item in parsed_rows if item["kind"] == "claimhood"]
    controls = [item for item in parsed_rows if item["kind"] == "mismatch_control"]
    by_anchor: dict[str, list[dict[str, Any]]] = {}
    for anchor_id in {item["anchor_id"] for item in claims}:
        by_anchor[anchor_id] = sorted([item for item in claims if item["anchor_id"] == anchor_id], key=lambda item: item["repeat_id"])
    envelopes = []
    for anchor_id, votes in sorted(by_anchor.items()):
        labels = [item["claimhood"] for item in votes]
        supports = [item["evidence_support"] for item in votes]
        counts = Counter(labels)
        if counts["CLAIM_BEARING"] == 3 and set(supports) == {"SUPPORTED"}:
            status = "BOUNDARY_HARD_KEEP"
        elif counts["CLAIM_BEARING"] == 2 and supports.count("SUPPORTED") >= 2:
            status = "BOUNDARY_SOFT_KEEP"
        elif counts["NON_CLAIM"] == 3:
            status = "BOUNDARY_HARD_DROP"
        elif counts["NON_CLAIM"] == 2:
            status = "BOUNDARY_SOFT_DROP"
        else:
            status = "BOUNDARY_UNSTABLE"
        envelopes.append({
            "anchor_id": anchor_id, "votes": dict(counts), "support_votes": dict(Counter(supports)),
            "status": status,
        })
    apre.write_jsonl(root / "reference" / "envelopes" / "claimhood_envelopes.jsonl", envelopes)
    exact = statistics.mean(len({item["claimhood"] for item in votes}) == 1 for votes in by_anchor.values())
    repeat_sets = []
    for repeat in (1, 2, 3):
        repeat_sets.append({item["anchor_id"] for item in claims if item["repeat_id"] == repeat and item["claimhood"] == "CLAIM_BEARING" and item["evidence_support"] == "SUPPORTED"})
    pairwise = [f1(repeat_sets[0], repeat_sets[1]), f1(repeat_sets[0], repeat_sets[2]), f1(repeat_sets[1], repeat_sets[2])]
    usable = statistics.mean(item["status"] != "BOUNDARY_UNSTABLE" for item in envelopes)
    unstable = 1 - usable
    mismatch_false_keep = statistics.mean(item["claimhood"] == "CLAIM_BEARING" and item["evidence_support"] == "SUPPORTED" for item in controls)
    duplicate_consistency = statistics.mean(
        sum(votes[left]["claimhood"] == votes[right]["claimhood"] for left, right in [(0, 1), (0, 2), (1, 2)]) / 3
        for votes in by_anchor.values()
    )
    metrics = {
        "schema_validity": 1.0, "anchor_id_validity": 1.0,
        "whole_anchor_three_repeat_exact_agreement": exact,
        "positive_anchor_pairwise_f1": pairwise,
        "positive_anchor_pairwise_f1_median": statistics.median(pairwise),
        "hard_plus_soft_claimhood_coverage": usable,
        "boundary_unstable_rate": unstable,
        "mismatch_negative_control_false_keep": mismatch_false_keep,
        "exact_duplicate_consistency": duplicate_consistency,
        "candidate_list_order_exposure": 0,
    }
    passed = (
        exact >= 0.90 and statistics.median(pairwise) >= 0.90 and usable >= 0.90
        and unstable <= 0.10 and mismatch_false_keep <= 0.05
        and duplicate_consistency >= 0.95
    )
    standard_cost = ((input_tokens - cached_tokens) * 2.0 + cached_tokens * 0.5 + output_tokens * 8.0) / 1_000_000
    cost = {
        "request_count": len(request_rows), "input_tokens": input_tokens,
        "cached_input_tokens": cached_tokens, "output_tokens": output_tokens,
        "standard_price_upper_bound_usd": round(standard_cost, 6),
        "batch_discount_not_assumed": True,
    }
    apre.write_json(root / "cost" / "fresh_claimhood_cost.json", cost)
    result = {
        "status": "PASS" if passed else "REVISE",
        "metrics": metrics, "envelope_counts": dict(Counter(item["status"] for item in envelopes)),
        "fresh_anchor_count": len(anchors), "fresh_api_request_count": len(request_rows),
        "fresh_api_exposure": 60, "test_access": 0, "cost": cost,
    }
    apre.write_json(root / "reports" / "gate_r3_3.json", result)
    lines = [
        "# R3 Fresh Pointwise Claimhood Gate",
        "", f"- Gate R3-3: **{result['status']}**", f"- Primary snapshot: `{model}`",
        f"- Fresh Evidence exposed: `{result['fresh_api_exposure']}`", "- TEST access: `0`", "",
        "| Metric | Value | Threshold |", "|---|---:|---:|",
        f"| 3-repeat exact agreement | {exact:.4f} | >=0.90 |",
        f"| Positive pairwise F1 median | {statistics.median(pairwise):.4f} | >=0.90 |",
        f"| HARD+SOFT coverage | {usable:.4f} | >=0.90 |",
        f"| UNSTABLE | {unstable:.4f} | <=0.10 |",
        f"| Mismatch false KEEP | {mismatch_false_keep:.4f} | <=0.05 |",
        f"| Duplicate consistency | {duplicate_consistency:.4f} | >=0.95 |",
        "", f"Requests: {len(request_rows)}; input tokens: {input_tokens}; output tokens: {output_tokens}.",
    ]
    (root / "reports" / "fresh_claimhood_gate.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if passed else 4


if __name__ == "__main__":
    raise SystemExit(main())
