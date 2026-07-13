#!/usr/bin/env python3
"""Run boundary and field repeatability bake-off on DEV_EXPOSED data."""

from __future__ import annotations

import json
import os
import statistics
from collections import Counter
from pathlib import Path
from typing import Any

import r2_api
import r2_blre as blre


EXPERIMENT_ID = "zaije_ldr_r2_20260712_blre_v1"
CONFIGS = {
    "C01": "gpt-4o-mini-2024-07-18",
    "C02": "gpt-4.1-mini-2025-04-14",
    "C03": "gpt-4o-2024-08-06",
    "C04": "gpt-4.1-2025-04-14",
}
SEMANTIC = ["DESCRIPTIVE", "DEFINITIONAL", "NORMATIVE", "PROCEDURAL", "CAUSAL_EVALUATIVE", "META_DISCOURSE", "UNDERDETERMINED"]
DEONTIC = ["NONE", "REQUIREMENT", "RECOMMENDATION", "PROHIBITION", "PERMISSION_OR_ABILITY", "UNDERDETERMINED"]
POLARITY = ["POSITIVE", "NEGATIVE", "MIXED", "NOT_APPLICABLE", "UNDERDETERMINED"]
CONDITIONALITY = ["NONE", "EXPLICIT_CONDITION", "IMPLICIT_CONTEXT", "EXCEPTION", "UNDERDETERMINED"]
EPISTEMIC = ["ASSERTED", "REPORTED_OR_ATTRIBUTED", "HYPOTHETICAL", "QUESTIONED_OR_CHALLENGED", "UNDERDETERMINED"]
PROMOTION = ["GENERAL_RULE", "DOMAIN_ASSERTION", "EXAMPLE_INSTANCE", "TEMPLATE_SCHEMA", "DISCOURSE_ONLY", "DO_NOT_PROMOTE", "UNDERDETERMINED"]


def boundary_schema(config: str, repeat: int) -> dict[str, Any]:
    decision = {"type": "object", "additionalProperties": False, "required": ["candidate_id", "contains_proposition", "self_contained", "minimal_without_material_loss", "discourse_only", "decision", "reason_code"], "properties": {"candidate_id": {"type": "string"}, "contains_proposition": {"type": "boolean"}, "self_contained": {"type": "boolean"}, "minimal_without_material_loss": {"type": "boolean"}, "discourse_only": {"type": "boolean"}, "decision": {"type": "string", "enum": ["KEEP", "DROP", "UNDERDETERMINED", "MISSING_CANDIDATE"]}, "reason_code": {"type": "string", "enum": ["PROPOSITION_MINIMAL", "NOT_PROPOSITION", "FRAGMENT", "NON_MINIMAL_SUPERSET", "DISCOURSE_CLAIM", "TABLE_SEPARATOR", "AMBIGUOUS", "BOUNDARY_NOT_IN_LATTICE"]}}}
    item = {"type": "object", "additionalProperties": False, "required": ["evidence_id", "configuration_id", "repeat_id", "candidate_decisions", "missing_candidate"], "properties": {"evidence_id": {"type": "string"}, "configuration_id": {"type": "string", "enum": [config]}, "repeat_id": {"type": "integer", "enum": [repeat]}, "candidate_decisions": {"type": "array", "items": decision}, "missing_candidate": {"type": "boolean"}}}
    return {"type": "object", "additionalProperties": False, "required": ["annotations"], "properties": {"annotations": {"type": "array", "items": item}}}


def field_schema(config: str, repeat: int) -> dict[str, Any]:
    item = {"type": "object", "additionalProperties": False, "required": ["claim_unit_id", "configuration_id", "repeat_id", "semantic_mode", "deontic_force", "polarity", "conditionality", "epistemic_status", "promotion"], "properties": {"claim_unit_id": {"type": "string"}, "configuration_id": {"type": "string", "enum": [config]}, "repeat_id": {"type": "integer", "enum": [repeat]}, "semantic_mode": {"type": "string", "enum": SEMANTIC}, "deontic_force": {"type": "string", "enum": DEONTIC}, "polarity": {"type": "string", "enum": POLARITY}, "conditionality": {"type": "string", "enum": CONDITIONALITY}, "epistemic_status": {"type": "string", "enum": EPISTEMIC}, "promotion": {"type": "string", "enum": PROMOTION}}}
    return {"type": "object", "additionalProperties": False, "required": ["annotations"], "properties": {"annotations": {"type": "array", "items": item}}}


def f1(left: set[str], right: set[str]) -> float:
    return 2 * len(left & right) / (len(left) + len(right)) if left or right else 1.0


def fixed_units(lattices: list[dict[str, Any]]) -> list[dict[str, Any]]:
    units = []
    for lattice in lattices:
        candidates = lattice["candidates"]
        non_separator = [item for item in candidates if not (lattice["structure_type"] == "TABLE" and re_separator(item["text_by_program"]))]
        chosen = max(non_separator or candidates, key=lambda item: (item["end_char"] - item["start_char"], -item["start_char"]))
        units.append({"claim_unit_id": f"DEV_{chosen['candidate_id']}", "evidence_id": lattice["evidence_id"], "candidate_id": chosen["candidate_id"], "locked_text": chosen["text_by_program"], "structure_type": lattice["structure_type"]})
    return units


def re_separator(text: str) -> bool:
    stripped = text.replace("|", "").replace("-", "").replace(":", "").strip()
    return not stripped


def logical_control(row: dict[str, Any]) -> bool:
    if row["semantic_mode"] == "META_DISCOURSE" and row["promotion"] not in {"DISCOURSE_ONLY", "DO_NOT_PROMOTE", "EXAMPLE_INSTANCE", "UNDERDETERMINED"}:
        return False
    if row["deontic_force"] == "PROHIBITION" and row["polarity"] not in {"NEGATIVE", "MIXED", "UNDERDETERMINED"}:
        return False
    return True


def main() -> int:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY required")
    experiment_root = Path(__file__).resolve().parents[1]
    root = experiment_root / "experiments" / EXPERIMENT_ID
    run_dir = root / "runs" / "model_bakeoff"
    lattices = blre.read_jsonl(root / "candidates" / "lattice" / "model_bakeoff.jsonl")
    if len(lattices) != 24:
        raise RuntimeError("Bake-off lock mismatch")
    boundary_prompt = (root / "preregistration" / "prompts" / "boundary_v1.txt").read_text(encoding="utf-8")
    field_prompt = (root / "preregistration" / "prompts" / "field_v1.txt").read_text(encoding="utf-8")
    client = r2_api.Client(run_dir, api_key, EXPERIMENT_ID, "model_bakeoff", max_calls=100)
    boundary_rows, field_rows = [], []
    for config, model in CONFIGS.items():
        for repeat in (1, 2):
            for batch_index in range(0, len(lattices), 8):
                batch = lattices[batch_index:batch_index + 8]
                payload_items = []
                for lattice in batch:
                    candidates = [{key: item[key] for key in ["candidate_id", "start_char", "end_char", "text_by_program", "candidate_level", "structure_type"]} for item in lattice["candidates"]]
                    if repeat == 2:
                        candidates.reverse()
                    payload_items.append({"evidence_id": lattice["evidence_id"], "raw_text": lattice["raw_text"], "structure_type": lattice["structure_type"], "candidates": candidates})
                parsed = client.call(phase=f"boundary_{config}_r{repeat}_b{batch_index // 8 + 1:02d}", model=model, prompt=boundary_prompt, payload={"items": payload_items}, schema_name=f"boundary_{config.lower()}_r{repeat}", schema=boundary_schema(config, repeat), item_ids=[row["evidence_id"] for row in batch], repeat_id=str(repeat))
                boundary_rows.extend(parsed["annotations"])
    units = fixed_units(lattices)
    for config, model in CONFIGS.items():
        for repeat in (1, 2):
            for batch_index in range(0, len(units), 8):
                batch = units[batch_index:batch_index + 8]
                parsed = client.call(phase=f"field_{config}_r{repeat}_b{batch_index // 8 + 1:02d}", model=model, prompt=field_prompt, payload={"items": batch}, schema_name=f"field_{config.lower()}_r{repeat}", schema=field_schema(config, repeat), item_ids=[row["claim_unit_id"] for row in batch], repeat_id=str(repeat))
                field_rows.extend(parsed["annotations"])
    blre.write_jsonl(run_dir / "boundary_outputs.jsonl", boundary_rows)
    blre.write_jsonl(run_dir / "field_outputs.jsonl", field_rows)
    cost = client.save()

    lattice_ids = {lattice["evidence_id"]: {item["candidate_id"] for item in lattice["candidates"]} for lattice in lattices}
    metrics = {}
    model_cost = Counter()
    for ledger_row in client.ledger:
        model_cost[ledger_row["model_snapshot"]] += int(ledger_row["input_tokens"]) + int(ledger_row["output_tokens"])
    max_cost = max(model_cost.values())
    for config, model in CONFIGS.items():
        boundary = [row for row in boundary_rows if row["configuration_id"] == config]
        fields = [row for row in field_rows if row["configuration_id"] == config]
        by_boundary = {(row["evidence_id"], row["repeat_id"]): row for row in boundary}
        by_field = {(row["claim_unit_id"], row["repeat_id"]): row for row in fields}
        f1s, valid, missing = [], 0, 0
        for evidence_id in lattice_ids:
            left = by_boundary[(evidence_id, 1)]; right = by_boundary[(evidence_id, 2)]
            left_keep = {item["candidate_id"] for item in left["candidate_decisions"] if item["decision"] == "KEEP"}
            right_keep = {item["candidate_id"] for item in right["candidate_decisions"] if item["decision"] == "KEEP"}
            f1s.append(f1(left_keep, right_keep))
            left_ids = [item["candidate_id"] for item in left["candidate_decisions"]]
            right_ids = [item["candidate_id"] for item in right["candidate_decisions"]]
            valid += int(set(left_ids) == lattice_ids[evidence_id] and set(right_ids) == lattice_ids[evidence_id] and len(left_ids) == len(set(left_ids)) and len(right_ids) == len(set(right_ids)))
            missing += int(left["missing_candidate"] or right["missing_candidate"])
        field_names = ["semantic_mode", "deontic_force", "polarity", "conditionality", "epistemic_status", "promotion"]
        expected_field_keys = {(unit["claim_unit_id"], repeat) for unit in units for repeat in (1, 2)}
        field_completeness = len(set(by_field) & expected_field_keys) / len(expected_field_keys)
        ims = {field: sum((unit["claim_unit_id"], 1) in by_field and (unit["claim_unit_id"], 2) in by_field and by_field[(unit["claim_unit_id"], 1)][field] == by_field[(unit["claim_unit_id"], 2)][field] for unit in units) / len(units) for field in field_names}
        controls = sum(logical_control(row) for row in fields) / len(fields) if fields else 0.0
        boundary_f1 = statistics.mean(f1s)
        critical_ims = min(ims["semantic_mode"], ims["deontic_force"], ims["polarity"], ims["promotion"])
        eligible = valid == len(lattice_ids) and field_completeness == 1.0 and controls >= 0.95 and boundary_f1 >= 0.85 and critical_ims >= 0.85 and client.failures / max(1, client.attempts) <= 0.01
        stability = (boundary_f1 + statistics.mean(ims.values())) / 2
        score = 0.35 * stability + 0.25 * controls + 0.15 * (1 - missing / len(lattice_ids)) + 0.15 * controls + 0.10 * (1 - model_cost[model] / max_cost)
        metrics[config] = {"model_snapshot": model, "boundary_repeat_f1": boundary_f1, "boundary_repeat_f1_evidence_median": statistics.median(f1s), "candidate_id_validity": valid / len(lattice_ids), "missing_candidate_rate": missing / len(lattice_ids), "field_output_completeness": field_completeness, "field_ims": ims, "critical_field_ims": critical_ims, "deterministic_control_accuracy": controls, "normalized_token_cost": model_cost[model] / max_cost, "model_score": score, "eligible": eligible}
    selected = [config for config in sorted(CONFIGS, key=lambda key: metrics[key]["model_score"], reverse=True) if metrics[config]["eligible"]][:3]
    status = "PASS" if len(selected) == 3 else "REVISE"
    result = {"status": status, "selected_panel": selected, "metrics": metrics, "cost": cost, "prompt_hashes": {"boundary": blre.sha(boundary_prompt), "field": blre.sha(field_prompt)}, "schema_hashes": {config: {"boundary_r1": blre.sha(boundary_schema(config, 1)), "field_r1": blre.sha(field_schema(config, 1))} for config in CONFIGS}}
    blre.write_json(root / "reports" / "model_bakeoff_metrics.json", result)
    blre.write_json(root / "preregistration" / "model_panel_lock.json", {"status": status, "selected_configurations": selected, "models": {config: CONFIGS[config] for config in selected}, "selection_metrics_hash": blre.sha(metrics), "fresh_pilot_accessed": False})
    lines = ["# R2 Model Bake-off", "", f"- Status: **{status}**", f"- Selected panel: `{', '.join(selected) if selected else 'NONE'}`", f"- API calls: {cost['real_calls']}", f"- Estimated cost: ${cost['estimated_cost_usd']:.6f}", "", "| Config | Boundary F1 | Critical IMS | Controls | Eligible | Score |", "|---|---:|---:|---:|---|---:|"]
    for config in CONFIGS:
        row = metrics[config]; lines.append(f"| {config} | {row['boundary_repeat_f1']:.4f} | {row['critical_field_ims']:.4f} | {row['deterministic_control_accuracy']:.4f} | {row['eligible']} | {row['model_score']:.4f} |")
    (root / "reports" / "model_bakeoff_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"status": status, "selected_panel": selected, "metrics": metrics, "cost": cost}, ensure_ascii=False, indent=2))
    return 0 if status == "PASS" else 4


if __name__ == "__main__":
    raise SystemExit(main())
