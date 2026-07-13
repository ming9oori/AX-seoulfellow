#!/usr/bin/env python3
"""Corrected DEV bake-off with separate repeat and order audits and F1-F4 tasks."""

from __future__ import annotations

import csv
import json
import os
import statistics
from collections import Counter
from pathlib import Path
from typing import Any

import r2_api
import r2_blre as blre
from run_r2_bakeoff import boundary_schema, fixed_units, f1, logical_control


EXPERIMENT_ID = "zaije_ldr_r2_20260712_blre_v1"
CONFIGS = {
    "C01": "gpt-4o-mini-2024-07-18",
    "C02": "gpt-4.1-mini-2025-04-14",
    "C03": "gpt-4o-2024-08-06",
    "C04": "gpt-4.1-2025-04-14",
    "C05": "gpt-4.1-nano-2025-04-14",
}
TASKS = {
    "F1": {
        "fields": {"semantic_mode": ["DESCRIPTIVE", "DEFINITIONAL", "NORMATIVE", "PROCEDURAL", "CAUSAL_EVALUATIVE", "META_DISCOURSE", "UNDERDETERMINED"]},
        "instruction": "Return semantic_mode only. Apply the locked semantic-mode definitions.",
    },
    "F2": {
        "fields": {"deontic_force": ["NONE", "REQUIREMENT", "RECOMMENDATION", "PROHIBITION", "PERMISSION_OR_ABILITY", "UNDERDETERMINED"], "polarity": ["POSITIVE", "NEGATIVE", "MIXED", "NOT_APPLICABLE", "UNDERDETERMINED"]},
        "instruction": "Return deontic_force and polarity only. Do not infer deontic force without explicit language.",
    },
    "F3": {
        "fields": {"conditionality": ["NONE", "EXPLICIT_CONDITION", "IMPLICIT_CONTEXT", "EXCEPTION", "UNDERDETERMINED"], "epistemic_status": ["ASSERTED", "REPORTED_OR_ATTRIBUTED", "HYPOTHETICAL", "QUESTIONED_OR_CHALLENGED", "UNDERDETERMINED"]},
        "instruction": "Return conditionality and epistemic_status only.",
    },
    "F4": {
        "fields": {"promotion": ["GENERAL_RULE", "DOMAIN_ASSERTION", "EXAMPLE_INSTANCE", "TEMPLATE_SCHEMA", "DISCOURSE_ONLY", "DO_NOT_PROMOTE", "UNDERDETERMINED"]},
        "instruction": "Return promotion only. Discourse and examples must not become GENERAL_RULE.",
    },
}


def task_schema(config: str, repeat: int, task: str) -> dict[str, Any]:
    properties: dict[str, Any] = {"claim_unit_id": {"type": "string"}, "configuration_id": {"type": "string", "enum": [config]}, "repeat_id": {"type": "integer", "enum": [repeat]}}
    for field, labels in TASKS[task]["fields"].items():
        properties[field] = {"type": "string", "enum": labels}
    item = {"type": "object", "additionalProperties": False, "required": list(properties), "properties": properties}
    return {"type": "object", "additionalProperties": False, "required": ["annotations"], "properties": {"annotations": {"type": "array", "items": item}}}


def main() -> int:
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("OPENAI_API_KEY required")
    experiment_root = Path(__file__).resolve().parents[1]
    root = experiment_root / "experiments" / EXPERIMENT_ID
    run_dir = root / "runs" / "model_bakeoff_decomposed"
    lattices = blre.read_jsonl(root / "candidates" / "lattice" / "model_bakeoff.jsonl")
    units = fixed_units(lattices)
    boundary_prompt = (root / "preregistration" / "prompts" / "boundary_v1.txt").read_text(encoding="utf-8")
    field_base = (root / "preregistration" / "prompts" / "field_v1.txt").read_text(encoding="utf-8")
    client = r2_api.Client(run_dir, key, EXPERIMENT_ID, "model_bakeoff_decomposed", max_calls=150)
    boundary_rows, order_rows, task_rows = [], [], []
    for config, model in CONFIGS.items():
        for repeat in (1, 2):
            for start in range(0, len(lattices), 8):
                batch = lattices[start:start + 8]
                payload = {"items": [{"evidence_id": lattice["evidence_id"], "raw_text": lattice["raw_text"], "structure_type": lattice["structure_type"], "candidates": [{key: item[key] for key in ["candidate_id", "start_char", "end_char", "text_by_program", "candidate_level", "structure_type"]} for item in lattice["candidates"]]} for lattice in batch]}
                parsed = client.call(phase=f"boundary_{config}_r{repeat}_b{start // 8 + 1:02d}", model=model, prompt=boundary_prompt, payload=payload, schema_name=f"boundary_{config.lower()}_r{repeat}", schema=boundary_schema(config, repeat), item_ids=[row["evidence_id"] for row in batch], repeat_id=str(repeat))
                boundary_rows.extend(parsed["annotations"])
        audit_batch = lattices[:8]
        audit_payload = {"items": [{"evidence_id": lattice["evidence_id"], "raw_text": lattice["raw_text"], "structure_type": lattice["structure_type"], "candidates": list(reversed([{key: item[key] for key in ["candidate_id", "start_char", "end_char", "text_by_program", "candidate_level", "structure_type"]} for item in lattice["candidates"]]))} for lattice in audit_batch]}
        parsed = client.call(phase=f"boundary_order_{config}", model=model, prompt=boundary_prompt, payload=audit_payload, schema_name=f"boundary_order_{config.lower()}", schema=boundary_schema(config, 1), item_ids=[row["evidence_id"] for row in audit_batch], repeat_id="order")
        order_rows.extend(parsed["annotations"])

    for task in TASKS:
        prompt = field_base + "\n\nCURRENT SUBTASK:\n" + TASKS[task]["instruction"]
        for config, model in CONFIGS.items():
            for repeat in (1, 2):
                for start in range(0, len(units), 12):
                    batch = units[start:start + 12]
                    parsed = client.call(phase=f"{task}_{config}_r{repeat}_b{start // 12 + 1:02d}", model=model, prompt=prompt, payload={"items": batch}, schema_name=f"{task.lower()}_{config.lower()}_r{repeat}", schema=task_schema(config, repeat, task), item_ids=[row["claim_unit_id"] for row in batch], repeat_id=str(repeat))
                    for row in parsed["annotations"]:
                        task_rows.append({"task": task, **row})
    blre.write_jsonl(run_dir / "boundary_outputs.jsonl", boundary_rows)
    blre.write_jsonl(run_dir / "boundary_order_audit.jsonl", order_rows)
    blre.write_jsonl(run_dir / "field_task_outputs.jsonl", task_rows)
    cost = client.save()
    actual_cost_path = run_dir / "cost_summary_actual.json"
    if actual_cost_path.exists():
        cost = json.loads(actual_cost_path.read_text(encoding="utf-8"))

    lattice_ids = {lattice["evidence_id"]: {item["candidate_id"] for item in lattice["candidates"]} for lattice in lattices}
    metrics = {}
    token_cost = Counter()
    ledger_for_cost: list[dict[str, Any]] = client.ledger
    actual_ledger_path = run_dir / "api_ledger_actual.csv"
    if actual_ledger_path.exists():
        with actual_ledger_path.open(encoding="utf-8", newline="") as handle:
            ledger_for_cost = list(csv.DictReader(handle))
    for row in ledger_for_cost:
        token_cost[row["model_snapshot"]] += int(row["input_tokens"]) + int(row["output_tokens"])
    max_cost = max(token_cost.values())
    for config, model in CONFIGS.items():
        boundaries = [row for row in boundary_rows if row["configuration_id"] == config]
        by_boundary = {(row["evidence_id"], row["repeat_id"]): row for row in boundaries}
        field_values: dict[tuple[str, int], dict[str, str]] = {}
        for row in task_rows:
            if row["configuration_id"] != config:
                continue
            key_id = (row["claim_unit_id"], row["repeat_id"])
            field_values.setdefault(key_id, {}).update({field: row[field] for field in TASKS[row["task"]]["fields"]})
        boundary_scores, complete_boundary, missing = [], 0, 0
        for evidence_id, expected_ids in lattice_ids.items():
            left, right = by_boundary.get((evidence_id, 1)), by_boundary.get((evidence_id, 2))
            if left is None or right is None:
                boundary_scores.append(0.0)
                missing += 1
                continue
            left_ids = [item["candidate_id"] for item in left["candidate_decisions"]]; right_ids = [item["candidate_id"] for item in right["candidate_decisions"]]
            complete_boundary += int(set(left_ids) == expected_ids and set(right_ids) == expected_ids and len(left_ids) == len(set(left_ids)) and len(right_ids) == len(set(right_ids)))
            left_keep = {item["candidate_id"] for item in left["candidate_decisions"] if item["decision"] == "KEEP"}; right_keep = {item["candidate_id"] for item in right["candidate_decisions"] if item["decision"] == "KEEP"}
            boundary_scores.append(f1(left_keep, right_keep)); missing += int(left["missing_candidate"] or right["missing_candidate"])
        config_order_rows = [row for row in order_rows if row["configuration_id"] == config]
        order_by = {row["evidence_id"]: row for row in config_order_rows}
        order_consistency = []
        for lattice in lattices[:8]:
            standard = by_boundary.get((lattice["evidence_id"], 1)); reverse = order_by.get(lattice["evidence_id"])
            if standard is None or reverse is None:
                order_consistency.append(0.0)
                continue
            standard_keep = {item["candidate_id"] for item in standard["candidate_decisions"] if item["decision"] == "KEEP"}; reverse_keep = {item["candidate_id"] for item in reverse["candidate_decisions"] if item["decision"] == "KEEP"}
            order_consistency.append(f1(standard_keep, reverse_keep))
        all_fields = [field for task in TASKS.values() for field in task["fields"]]
        field_ims = {field: sum(field_values.get((unit["claim_unit_id"], 1), {}).get(field) == field_values.get((unit["claim_unit_id"], 2), {}).get(field) and field in field_values.get((unit["claim_unit_id"], 1), {}) for unit in units) / len(units) for field in all_fields}
        field_completeness = sum(all(field in field_values.get((unit["claim_unit_id"], repeat), {}) for field in all_fields) for unit in units for repeat in (1, 2)) / (len(units) * 2)
        combined_rows = [{**{"claim_unit_id": unit["claim_unit_id"]}, **field_values.get((unit["claim_unit_id"], repeat), {})} for unit in units for repeat in (1, 2)]
        controls = sum(logical_control(row) for row in combined_rows if all(field in row for field in all_fields)) / max(1, sum(all(field in row for field in all_fields) for row in combined_rows))
        boundary_repeat = statistics.mean(boundary_scores)
        critical_ims = min(field_ims["semantic_mode"], field_ims["deontic_force"], field_ims["polarity"], field_ims["promotion"])
        order_output_complete = len(config_order_rows) == 8 and len(order_by) == 8
        eligible = complete_boundary == len(lattice_ids) and order_output_complete and field_completeness == 1.0 and controls >= 0.95 and boundary_repeat >= 0.85 and critical_ims >= 0.85 and client.failures / max(1, client.attempts) <= 0.01
        stability = (boundary_repeat + statistics.mean(field_ims.values())) / 2
        score = 0.35 * stability + 0.25 * controls + 0.15 * (1 - missing / len(lattice_ids)) + 0.15 * controls + 0.10 * (1 - token_cost[model] / max_cost)
        metrics[config] = {"model_snapshot": model, "boundary_repeat_f1": boundary_repeat, "boundary_repeat_f1_median": statistics.median(boundary_scores), "candidate_id_validity": complete_boundary / len(lattice_ids), "candidate_order_output_completeness": order_output_complete, "candidate_order_consistency": statistics.mean(order_consistency), "missing_candidate_rate": missing / len(lattice_ids), "field_output_completeness": field_completeness, "field_ims": field_ims, "critical_field_ims": critical_ims, "deterministic_control_accuracy": controls, "model_score": score, "eligible": eligible}
    selected = [config for config in sorted(CONFIGS, key=lambda key: metrics[key]["model_score"], reverse=True) if metrics[config]["eligible"]][:3]
    status = "PASS" if len(selected) == 3 else "REVISE"
    result = {"status": status, "selected_panel": selected, "metrics": metrics, "cost": cost, "fresh_pilot_accessed": False}
    blre.write_json(root / "reports" / "model_bakeoff_decomposed_metrics.json", result)
    blre.write_json(root / "preregistration" / "model_panel_lock.json", {"status": status, "selected_configurations": selected, "models": {config: CONFIGS[config] for config in selected}, "selection_metrics_hash": blre.sha(metrics), "boundary_prompt_hash": blre.sha(boundary_prompt), "field_base_prompt_hash": blre.sha(field_base), "task_schema_hashes": {task: blre.sha(task_schema("C01", 1, task)) for task in TASKS}, "fresh_pilot_accessed": False})
    lines = ["# R2 Decomposed Model Bake-off", "", f"- Status: **{status}**", f"- Selected: `{', '.join(selected) if selected else 'NONE'}`", f"- Calls: {cost['real_calls']}", f"- Cost: ${cost['estimated_cost_usd']:.6f}", "", "| Config | Boundary F1 | Order | Critical IMS | Complete | Eligible | Score |", "|---|---:|---:|---:|---:|---|---:|"]
    for config in CONFIGS:
        row = metrics[config]; lines.append(f"| {config} | {row['boundary_repeat_f1']:.4f} | {row['candidate_order_consistency']:.4f} | {row['critical_field_ims']:.4f} | {row['field_output_completeness']:.4f} | {row['eligible']} | {row['model_score']:.4f} |")
    (root / "reports" / "model_bakeoff_decomposed_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if status == "PASS" else 4


if __name__ == "__main__":
    raise SystemExit(main())
