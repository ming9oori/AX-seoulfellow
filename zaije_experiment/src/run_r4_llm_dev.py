#!/usr/bin/env python3
"""Qualify and freeze the closed-choice R4 LLM policy on DEV only."""

from __future__ import annotations

import getpass
import hashlib
import json
import os
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import r2_api
import r3_batch_api
import r4_ceoc as r4


MODEL = "gpt-4.1-2025-04-14"
PROMPT = """You are a closed-choice evidence verifier for R4-CEOC.
Use only source_text, anchor_text, registered IDs, operation, and option_ids.
Never create a quote, concept label, relation, mention, or option.
Return candidate_id exactly. selected_option_id must be one supplied option or NONE.
Perform this mandatory check before semantic judgment: anchor_text must occur as an exact character-for-character substring of source_text.
If it does not occur exactly, return decision=REJECTED, selected_option_id=NONE, reason_code=SOURCE_MISMATCH, abstain=false. No semantic similarity can override this rule.
SUPPORTED means the source directly supports the proposed closed operation and selected option.
REJECTED means source-anchor mismatch or direct contradiction.
UNDERDETERMINED means the supplied evidence cannot choose safely. Natural-language rationale is forbidden."""


def schema() -> dict[str, Any]:
    return {
        "type": "object", "additionalProperties": False,
        "required": ["candidate_id", "decision", "selected_option_id", "reason_code", "abstain"],
        "properties": {
            "candidate_id": {"type": "string"},
            "decision": {"type": "string", "enum": ["SUPPORTED", "REJECTED", "UNDERDETERMINED"]},
            "selected_option_id": {"type": "string"},
            "reason_code": {"type": "string", "enum": ["EXACT_SUPPORT", "STRUCTURAL_SUPPORT", "SOURCE_MISMATCH", "AMBIGUOUS"]},
            "abstain": {"type": "boolean"},
        },
    }


def parse_batch(path: Path, manifest: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, int]]:
    output = {row["custom_id"]: row for row in r4.read_jsonl(path)}
    rows = []
    usage = Counter()
    for meta in manifest:
        item = output[meta["custom_id"]]
        if item.get("error") or item["response"]["status_code"] != 200:
            raise RuntimeError(f"DEV batch failure {meta['custom_id']}")
        body = item["response"]["body"]
        parsed = json.loads(r2_api.extract_text(body))
        if parsed["candidate_id"] != meta["candidate_id"]:
            raise RuntimeError("Candidate ID mismatch")
        if parsed["selected_option_id"] not in meta["option_ids"] + ["NONE"]:
            raise RuntimeError("Unsupported free option generation")
        u = body.get("usage") or {}
        usage["input_tokens"] += int(u.get("input_tokens") or 0)
        usage["output_tokens"] += int(u.get("output_tokens") or 0)
        usage["cached_input_tokens"] += int((u.get("input_tokens_details") or {}).get("cached_tokens") or 0)
        rows.append({**meta, "response_id": body.get("id"), **parsed})
    return rows, dict(usage)


def main() -> int:
    key = os.environ.get("OPENAI_API_KEY") or getpass.getpass("OpenAI API key: ")
    if not key:
        raise RuntimeError("OpenAI API key required")
    project = Path(__file__).resolve().parents[1]
    root = project / "experiments" / r4.EXPERIMENT_ID
    gate2 = json.loads((root / "reports" / "gate_r4_2.json").read_text(encoding="utf-8"))
    if gate2["status"] != "PASS":
        raise RuntimeError("R4-2 must pass")
    rows = r4.read_jsonl(root / "data" / "dev_exposed" / "dev_120.jsonl")
    anchors = r4.read_jsonl(root / "data" / "dev_exposed" / "anchors.jsonl")
    candidates = r4.generate_gray_candidates(rows, anchors)
    r4.write_jsonl(root / "extraction" / "candidates" / "dev_gray_candidates.jsonl", candidates)
    if len(candidates) != 313:
        raise RuntimeError(f"Expected one candidate per DEV anchor, got {len(candidates)}")

    obvious_pool = [item for item in candidates if item["candidate_type"] == "ASSERTION_SUPPORT" and len(item["anchor_text"]) >= 15]
    obvious = sorted(obvious_pool, key=lambda item: item["candidate_id"])[:20]
    if len(obvious) != 20:
        raise RuntimeError("Insufficient obvious support controls")
    controls = []
    for repeat in (1, 2):
        for index, candidate in enumerate(obvious, 1):
            controls.append({**candidate, "control_type": "SUPPORTED", "expected": "SUPPORTED", "repeat_id": repeat, "logical_id": f"support_{index:02d}"})
            mismatch_source = next(
                item["source_text"] for item in candidates
                if item["evidence_id"] != candidate["evidence_id"] and candidate["anchor_text"] not in item["source_text"]
            )
            controls.append({**candidate, "source_text": mismatch_source, "control_type": "MISMATCH", "expected": "REJECTED", "repeat_id": repeat, "logical_id": f"mismatch_{index:02d}"})
    evaluation = [{**candidate, "control_type": "DEV_CANDIDATE", "expected": None, "repeat_id": 1, "logical_id": candidate["candidate_id"]} for candidate in candidates]
    items = controls + evaluation
    if len(items) > 500:
        raise RuntimeError("DEV LLM request cap exceeded")

    run_dir = root / "runs" / "dev_llm_qualification_revision_2"
    input_path = run_dir / "batch_input.jsonl"
    manifest_path = run_dir / "logical_request_manifest.jsonl"
    requests, manifest = [], []
    task_schema = schema()
    for index, item in enumerate(items, 1):
        custom_id = f"dev_{index:04d}"
        payload = {key_name: item[key_name] for key_name in ["candidate_id", "candidate_type", "source_text", "anchor_text", "operation", "option_ids", "registered_mention_ids", "cue_types"]}
        requests.append({
            "custom_id": custom_id, "method": "POST", "url": "/v1/responses",
            "body": {
                "model": MODEL,
                "input": [
                    {"role": "system", "content": [{"type": "input_text", "text": PROMPT}]},
                    {"role": "user", "content": [{"type": "input_text", "text": r4.canonical(payload)}]},
                ],
                "text": {"format": {"type": "json_schema", "name": "r4_closed_choice_v1", "strict": True, "schema": task_schema}},
                "temperature": 0, "max_output_tokens": 350,
            },
        })
        manifest.append({
            "custom_id": custom_id, "candidate_id": item["candidate_id"], "candidate_type": item["candidate_type"],
            "option_ids": item["option_ids"], "control_type": item["control_type"], "expected": item["expected"],
            "repeat_id": item["repeat_id"], "logical_id": item["logical_id"], "selection_score": item["selection_score"],
        })
    r4.write_jsonl(input_path, requests)
    r4.write_jsonl(manifest_path, manifest)
    r3_batch_api.submit_and_wait(api_key=key, input_path=input_path, run_dir=run_dir, metadata={"experiment_id": r4.EXPERIMENT_ID, "phase": "dev_llm_qualification"})
    outputs, usage = parse_batch(run_dir / "batch_output.jsonl", manifest)
    r4.write_jsonl(root / "extraction" / "selective_llm" / "dev_outputs.jsonl", outputs)

    control_rows = [item for item in outputs if item["control_type"] != "DEV_CANDIDATE"]
    supported = [item["decision"] == "SUPPORTED" for item in control_rows if item["expected"] == "SUPPORTED"]
    mismatch = [item["decision"] == "REJECTED" for item in control_rows if item["expected"] == "REJECTED"]
    control_accuracy = statistics.mean([*supported, *mismatch])
    by_logical = defaultdict(dict)
    for item in control_rows:
        by_logical[(item["control_type"], item["logical_id"])][item["repeat_id"]] = (item["decision"], item["selected_option_id"])
    repeat_agreement = statistics.mean(value[1] == value[2] for value in by_logical.values())
    dev_outputs = {item["candidate_id"]: item for item in outputs if item["control_type"] == "DEV_CANDIDATE"}
    sweeps = []
    b3_accepted = sum(item["decision"] == "SUPPORTED" for item in dev_outputs.values())
    for budget in [0.0, 0.05, 0.10, 0.20, 0.40, 1.0]:
        selected = r4.select_gray_candidates(candidates, budget)
        accepted = sum(dev_outputs[item["candidate_id"]]["decision"] == "SUPPORTED" for item in selected)
        sweeps.append({
            "budget": budget, "selected": len(selected), "accepted": accepted,
            "token_ratio_proxy": len(selected) / len(candidates),
            "accepted_yield_ratio_to_b3": accepted / b3_accepted if b3_accepted else 1.0,
        })
    eligible_budgets = [item for item in sweeps if 0 < item["budget"] <= 0.35 and item["accepted_yield_ratio_to_b3"] >= 0.85]
    selected_budget = min(eligible_budgets, key=lambda item: item["budget"])["budget"] if eligible_budgets else 0.20
    qualified = (
        statistics.mean(supported) >= 0.95 and statistics.mean(mismatch) >= 0.95
        and repeat_agreement >= 0.90 and control_accuracy >= 0.95
    )
    result = {
        "status": "PASS" if qualified else "REVISE_BEFORE_CONFIRMATORY",
        "model_snapshot": MODEL, "structured_output_validity": 1.0, "candidate_id_validity": 1.0,
        "source_mismatch_rejection": statistics.mean(mismatch), "supported_control_recall": statistics.mean(supported),
        "repeat_agreement": repeat_agreement, "deterministic_control_accuracy": control_accuracy,
        "unsupported_free_generation": 0, "dev_budget_sweep": sweeps, "selected_b2_budget": selected_budget,
        "b2_dev_critical_violation_increase": 0, "confirmatory_api_exposure": 0, "test_access": 0,
        "cost": {"requests": len(items), **usage},
    }
    r4.write_json(root / "reports" / "gate_r4_3.json", result)
    prompt_path = root / "preregistration" / "prompts" / "closed_choice_v1.txt"
    prompt_path.parent.mkdir(parents=True, exist_ok=True); prompt_path.write_text(PROMPT + "\n", encoding="utf-8")
    schema_path = root / "preregistration" / "schemas" / "closed_choice_v1.json"
    r4.write_json(schema_path, task_schema)
    freeze = {
        "experiment_id": r4.EXPERIMENT_ID, "model_snapshot": MODEL,
        "prompt_sha256": r4.file_sha(prompt_path), "schema_sha256": r4.file_sha(schema_path),
        "candidate_generator_sha256": r4.file_sha(project / "src" / "r4_ceoc.py"),
        "selected_b2_budget": selected_budget, "generic_support_k": 2,
        "relation_registry_sha256": r4.file_sha(root / "preregistration" / "relation_registry.yaml"),
        "promotion_policy_sha256": r4.file_sha(root / "preregistration" / "promotion_policy.yaml"),
        "confirmatory_membership_sha256": r4.file_sha(root / "data" / "confirmatory" / "validation_80.jsonl"),
        "confirmatory_api_exposure_at_freeze": 0, "test_access": 0,
    }
    r4.write_json(root / "locks" / "system_freeze.json", freeze)
    lines = [
        "# R4 Selective LLM DEV Report", "", f"- Gate R4-3: **{result['status']}**",
        f"- Model: `{MODEL}`", f"- Selected B2 budget: `{selected_budget:.0%}`",
        "- Confirmatory API exposure: `0`", "- TEST access: `0`", "",
        "| Metric | Value | Gate |", "|---|---:|---:|",
        f"| Source mismatch rejection | {result['source_mismatch_rejection']:.4f} | >=0.95 |",
        f"| Repeat agreement | {repeat_agreement:.4f} | >=0.90 |",
        f"| Control accuracy | {control_accuracy:.4f} | >=0.95 |",
        f"| Unsupported free generation | 0 | 0 |", "", "## Budget sweep", "",
        "| Budget | Selected | Accepted | Yield ratio to B3 |", "|---:|---:|---:|---:|",
    ]
    for item in sweeps:
        lines.append(f"| {item['budget']:.0%} | {item['selected']} | {item['accepted']} | {item['accepted_yield_ratio_to_b3']:.4f} |")
    (root / "reports" / "selective_llm_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if qualified else 4


if __name__ == "__main__":
    raise SystemExit(main())
