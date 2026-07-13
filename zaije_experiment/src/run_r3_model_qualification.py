#!/usr/bin/env python3
"""Qualify one pointwise primary measurer and one independent falsifier on DEV."""

from __future__ import annotations

import getpass
import hashlib
import json
import os
import re
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any

import r2_api
import r3_apre as apre


PRIMARY = {
    "C02": "gpt-4.1-mini-2025-04-14",
    "C03": "gpt-4o-2024-08-06",
    "C04": "gpt-4.1-2025-04-14",
}
FALSIFIER = {
    "C01": "gpt-4o-mini-2024-07-18",
    "C03": "gpt-4o-2024-08-06",
    "C04": "gpt-4.1-2025-04-14",
}
FACETS = {
    "IS_PROCEDURAL": "The anchor states or specifies an action, method, process, or operational step.",
    "IS_NORMATIVE": "The anchor requires, recommends, prohibits, or permits an action, explicitly or implicitly.",
    "GENERALIZABLE_RULE": "The anchor presents a reusable general rule rather than only one specific instance.",
    "SPECIFIC_EXAMPLE_INSTANCE": "The anchor is a concrete example, illustration, or case instance.",
}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def claim_schema() -> dict[str, Any]:
    return {
        "type": "object", "additionalProperties": False,
        "required": ["anchor_id", "claimhood", "evidence_support"],
        "properties": {
            "anchor_id": {"type": "string"},
            "claimhood": {"type": "string", "enum": ["CLAIM_BEARING", "NON_CLAIM", "UNDERDETERMINED"]},
            "evidence_support": {"type": "string", "enum": ["SUPPORTED", "CONTRADICTED", "UNDERDETERMINED"]},
        },
    }


def facet_schema() -> dict[str, Any]:
    return {
        "type": "object", "additionalProperties": False,
        "required": ["proposal_id", "decision"],
        "properties": {
            "proposal_id": {"type": "string"},
            "decision": {"type": "string", "enum": ["SUPPORTED", "NOT_SUPPORTED", "UNDERDETERMINED"]},
        },
    }


def falsifier_schema() -> dict[str, Any]:
    return {
        "type": "object", "additionalProperties": False,
        "required": ["proposal_id", "decision"],
        "properties": {
            "proposal_id": {"type": "string"},
            "decision": {"type": "string", "enum": ["SUPPORTED", "CONTRADICTED", "UNDERDETERMINED"]},
        },
    }


def context_payload(record: dict[str, Any], anchor: dict[str, Any]) -> list[dict[str, str]]:
    by_id = {item["span_id"]: item for item in record["context_spans"]}
    return [{
        "span_id": span_id,
        "text": by_id[span_id]["text_by_program"],
        "relation": relation,
    } for span_id, relation in zip(anchor["context_span_ids"], anchor["context_relations"])]


def anchor_score(anchor: dict[str, Any]) -> tuple[int, int, str]:
    text = anchor["text_by_program"]
    predicate = bool(re.search(r"(?:한다|된다|이다|있다|없다|필요|권장|해야|말한다|높다|낮다|수립|작성|분석|평가)", text))
    useful_length = 12 <= len(text) <= 180
    return (int(predicate) * 2 + int(useful_length), min(len(text), 180), anchor["anchor_id"])


def select_representatives(records: list[dict[str, Any]]) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    selected = []
    for record in records:
        anchor = max(record["anchors"], key=anchor_score)
        selected.append((record, anchor))
    return selected


def claim_payload(record: dict[str, Any], anchor: dict[str, Any], source_override: str | None = None) -> dict[str, Any]:
    return {
        "evidence_id": record["evidence_id"],
        "anchor_id": anchor["anchor_id"],
        "document_context": {"chapter": record.get("chapter", ""), "section": record.get("section", "")},
        "source_text": record["raw_text"] if source_override is None else source_override,
        "anchor_text": anchor["text_by_program"],
        "context_spans": context_payload(record, anchor) if source_override is None else [],
    }


def f1(left: set[str], right: set[str]) -> float:
    if not left and not right:
        return 1.0
    if not left or not right:
        return 0.0
    precision = len(left & right) / len(left)
    recall = len(left & right) / len(right)
    return 2 * precision * recall / (precision + recall) if precision + recall else 0.0


def balanced_accuracy(expected: list[bool], predicted: list[bool]) -> float:
    positive = [int(p == e) for e, p in zip(expected, predicted) if e]
    negative = [int(p == e) for e, p in zip(expected, predicted) if not e]
    return (statistics.mean(positive) + statistics.mean(negative)) / 2


def actual_cost(run_dir: Path) -> dict[str, Any]:
    seen = set()
    totals = defaultdict(float)
    model_tokens: dict[str, int] = defaultdict(int)
    for path in sorted((run_dir / "raw_responses").glob("*.json")):
        raw = read_json(path)
        response_id = raw.get("id") or path.name
        if response_id in seen:
            continue
        seen.add(response_id)
        model = raw.get("model", "")
        usage = raw.get("usage") or {}
        inp = int(usage.get("input_tokens") or 0)
        out = int(usage.get("output_tokens") or 0)
        cached = int((usage.get("input_tokens_details") or {}).get("cached_tokens") or 0)
        price = r2_api.PRICES[model]
        cost = ((inp - cached) * price["input"] + cached * price["cached"] + out * price["output"]) / 1_000_000
        totals["input_tokens"] += inp
        totals["output_tokens"] += out
        totals["cached_input_tokens"] += cached
        totals["estimated_cost_usd"] += cost
        model_tokens[model] += inp + out
    return {
        "real_calls": len(seen),
        "input_tokens": int(totals["input_tokens"]),
        "output_tokens": int(totals["output_tokens"]),
        "cached_input_tokens": int(totals["cached_input_tokens"]),
        "estimated_cost_usd": round(totals["estimated_cost_usd"], 6),
        "tokens_by_model": dict(model_tokens),
    }


def main() -> int:
    key = os.environ.get("OPENAI_API_KEY") or getpass.getpass("OpenAI API key: ")
    if not key:
        raise RuntimeError("OpenAI API key required")
    project = Path(__file__).resolve().parents[1]
    root = project / "experiments" / apre.EXPERIMENT_ID
    gate1 = read_json(root / "reports" / "gate_r3_1.json")
    if gate1["status"] != "PASS":
        raise RuntimeError("Gate R3-1 must pass before model qualification")

    records = apre.read_jsonl(root / "anchor" / "dev_audit" / "dev_qualification_anchors.jsonl")
    selected = select_representatives(records)
    if len(selected) != 24:
        raise RuntimeError(f"Expected 24 qualification Evidence, got {len(selected)}")
    selection_rows = [{
        "evidence_id": record["evidence_id"], "anchor_id": anchor["anchor_id"],
        "anchor_text": anchor["text_by_program"], "selection_rule": "MAX_PREDICATE_LENGTH_SCORE_V1",
    } for record, anchor in selected]
    apre.write_jsonl(root / "controls" / "dev_qualification_representatives_24.jsonl", selection_rows)

    claim_prompt = (root / "preregistration" / "prompts" / "claimhood_v1.txt").read_text(encoding="utf-8")
    facet_prompt = (root / "preregistration" / "prompts" / "facet_v1.txt").read_text(encoding="utf-8")
    falsifier_prompt = (root / "preregistration" / "prompts" / "falsifier_v1.txt").read_text(encoding="utf-8")
    run_dir = root / "runs" / "model_role_qualification"
    client = r2_api.Client(
        run_dir, key, apre.EXPERIMENT_ID, "model_role_qualification",
        max_calls=1000, max_input_tokens=4_000_000, max_output_tokens=800_000,
    )

    claim_rows = []
    facet_rows = []
    primary_control_rows = []
    falsifier_rows = []
    claim_s = claim_schema()
    facet_s = facet_schema()
    falsifier_s = falsifier_schema()

    for config, model in PRIMARY.items():
        for repeat in (1, 2):
            for index, (record, anchor) in enumerate(selected, 1):
                result = client.call(
                    phase=f"primary_claim_{config}_r{repeat}_{index:02d}", model=model,
                    prompt=claim_prompt, payload=claim_payload(record, anchor),
                    schema_name="r3_claimhood_v1", schema=claim_s,
                    item_ids=[anchor["anchor_id"]], repeat_id=str(repeat), max_output_tokens=300,
                )
                if result["anchor_id"] != anchor["anchor_id"]:
                    raise RuntimeError("Primary qualification anchor ID mismatch")
                claim_rows.append({"configuration_id": config, "model_snapshot": model, "repeat_id": repeat, **result})

            for facet, definition in FACETS.items():
                for index, (record, anchor) in enumerate(selected, 1):
                    proposal_id = f"{anchor['anchor_id']}::{facet}"
                    payload = {
                        **claim_payload(record, anchor),
                        "proposal_id": proposal_id,
                        "proposed_facet": facet,
                        "facet_definition": definition,
                    }
                    result = client.call(
                        phase=f"primary_facet_{config}_r{repeat}_{facet}_{index:02d}", model=model,
                        prompt=facet_prompt, payload=payload, schema_name="r3_binary_facet_v1",
                        schema=facet_s, item_ids=[proposal_id], repeat_id=str(repeat), max_output_tokens=250,
                    )
                    if result["proposal_id"] != proposal_id:
                        raise RuntimeError("Facet proposal ID mismatch")
                    facet_rows.append({
                        "configuration_id": config, "model_snapshot": model, "repeat_id": repeat,
                        "anchor_id": anchor["anchor_id"], "facet": facet, **result,
                    })

        positive_controls = selected[:12]
        negative_controls = []
        for index, (record, anchor) in enumerate(selected[:12]):
            mismatch_source = selected[(index + 12) % len(selected)][0]["raw_text"]
            negative_controls.append((record, anchor, mismatch_source))
        for expected, controls in [(True, [(r, a, None) for r, a in positive_controls]), (False, negative_controls)]:
            for index, (record, anchor, source_override) in enumerate(controls, 1):
                result = client.call(
                    phase=f"primary_control_{config}_{int(expected)}_{index:02d}", model=model,
                    prompt=claim_prompt, payload=claim_payload(record, anchor, source_override),
                    schema_name="r3_claimhood_control_v1", schema=claim_s,
                    item_ids=[anchor["anchor_id"]], repeat_id="control", max_output_tokens=300,
                )
                if result["anchor_id"] != anchor["anchor_id"]:
                    raise RuntimeError("Primary control anchor ID mismatch")
                accepted = result["claimhood"] == "CLAIM_BEARING" and result["evidence_support"] == "SUPPORTED"
                primary_control_rows.append({
                    "configuration_id": config, "model_snapshot": model,
                    "control_expected_positive": expected, "accepted": accepted,
                    "anchor_id": anchor["anchor_id"], **result,
                })

    supported_controls = selected[:12]
    contradicted_controls = []
    for index, (record, anchor) in enumerate(selected[:12]):
        contradicted_controls.append((record, anchor, selected[(index + 12) % len(selected)][0]["raw_text"]))
    for config, model in FALSIFIER.items():
        for repeat in (1, 2):
            for expected, controls in [
                ("SUPPORTED", [(r, a, None) for r, a in supported_controls]),
                ("CONTRADICTED", contradicted_controls),
            ]:
                for index, (record, anchor, source_override) in enumerate(controls, 1):
                    proposal_id = f"FAL::{config}::r{repeat}::{expected}::{index:02d}"
                    item_payload = claim_payload(record, anchor, source_override)
                    item_payload.update({
                        "proposal_id": proposal_id,
                        "proposed_field": "EVIDENCE_SUPPORT",
                        "proposed_value": "THE_ANCHOR_IS_SUPPORTED_BY_SOURCE_TEXT",
                    })
                    result = client.call(
                        phase=f"falsifier_{config}_r{repeat}_{expected}_{index:02d}", model=model,
                        prompt=falsifier_prompt, payload=item_payload,
                        schema_name="r3_falsifier_control_v1", schema=falsifier_s,
                        item_ids=[proposal_id], repeat_id=str(repeat), max_output_tokens=250,
                    )
                    if result["proposal_id"] != proposal_id:
                        raise RuntimeError("Falsifier proposal ID mismatch")
                    falsifier_rows.append({
                        "configuration_id": config, "model_snapshot": model, "repeat_id": repeat,
                        "expected": expected, "anchor_id": anchor["anchor_id"], **result,
                    })

    apre.write_jsonl(root / "annotation" / "qualification" / "primary_claimhood.jsonl", claim_rows)
    apre.write_jsonl(root / "annotation" / "qualification" / "primary_facets.jsonl", facet_rows)
    apre.write_jsonl(root / "controls" / "primary_controls.jsonl", primary_control_rows)
    apre.write_jsonl(root / "controls" / "falsifier_controls.jsonl", falsifier_rows)
    client.save()
    cost = actual_cost(run_dir)
    apre.write_json(run_dir / "cost_summary_actual.json", cost)

    primary_metrics = {}
    for config, model in PRIMARY.items():
        rows = [item for item in claim_rows if item["configuration_id"] == config]
        by = {(item["anchor_id"], item["repeat_id"]): item for item in rows}
        exact = [by[(anchor["anchor_id"], 1)]["claimhood"] == by[(anchor["anchor_id"], 2)]["claimhood"] for _, anchor in selected]
        positive_sets = []
        for repeat in (1, 2):
            positive_sets.append({
                anchor["anchor_id"] for _, anchor in selected
                if by[(anchor["anchor_id"], repeat)]["claimhood"] == "CLAIM_BEARING"
                and by[(anchor["anchor_id"], repeat)]["evidence_support"] == "SUPPORTED"
            })
        facets = [item for item in facet_rows if item["configuration_id"] == config]
        facet_by = {(item["proposal_id"], item["repeat_id"]): item["decision"] for item in facets}
        facet_agreement = {
            facet: statistics.mean(
                facet_by[(f"{anchor['anchor_id']}::{facet}", 1)] == facet_by[(f"{anchor['anchor_id']}::{facet}", 2)]
                for _, anchor in selected
            ) for facet in FACETS
        }
        controls = [item for item in primary_control_rows if item["configuration_id"] == config]
        control_ba = balanced_accuracy(
            [item["control_expected_positive"] for item in controls],
            [item["accepted"] for item in controls],
        )
        metrics = {
            "model_snapshot": model,
            "structured_output_validity": 1.0,
            "anchor_id_validity": 1.0,
            "claimhood_repeat_agreement": statistics.mean(exact),
            "positive_anchor_set_f1": f1(positive_sets[0], positive_sets[1]),
            "critical_facet_repeat_agreement": min(facet_agreement.values()),
            "facet_repeat_agreement": facet_agreement,
            "deterministic_control_balanced_accuracy": control_ba,
            "api_failure_rate": 0.0,
        }
        metrics["qualified"] = (
            metrics["claimhood_repeat_agreement"] >= 0.92
            and metrics["positive_anchor_set_f1"] >= 0.90
            and metrics["critical_facet_repeat_agreement"] >= 0.90
            and metrics["deterministic_control_balanced_accuracy"] >= 0.95
        )
        primary_metrics[config] = metrics

    falsifier_metrics = {}
    for config, model in FALSIFIER.items():
        rows = [item for item in falsifier_rows if item["configuration_id"] == config]
        supported = [item["decision"] == "SUPPORTED" for item in rows if item["expected"] == "SUPPORTED"]
        contradicted = [item["decision"] == "CONTRADICTED" for item in rows if item["expected"] == "CONTRADICTED"]
        by = defaultdict(dict)
        for item in rows:
            control_key = (item["expected"], item["anchor_id"])
            by[control_key][item["repeat_id"]] = item["decision"]
        repeat_agreement = statistics.mean(item[1] == item[2] for item in by.values())
        supported_recall = statistics.mean(supported)
        contradicted_recall = statistics.mean(contradicted)
        ba = (supported_recall + contradicted_recall) / 2
        metrics = {
            "model_snapshot": model,
            "schema_validity": 1.0,
            "proposal_id_validity": 1.0,
            "supported_control_recall": supported_recall,
            "contradicted_control_recall": contradicted_recall,
            "balanced_accuracy": ba,
            "repeat_agreement": repeat_agreement,
            "api_failure_rate": 0.0,
        }
        metrics["qualified"] = supported_recall >= 0.90 and contradicted_recall >= 0.90 and ba >= 0.92 and repeat_agreement >= 0.90
        falsifier_metrics[config] = metrics

    qualified_primary = [key for key in PRIMARY if primary_metrics[key]["qualified"]]
    qualified_primary.sort(key=lambda key: (
        primary_metrics[key]["claimhood_repeat_agreement"],
        primary_metrics[key]["critical_facet_repeat_agreement"],
        -cost["tokens_by_model"].get(PRIMARY[key], 0),
    ), reverse=True)
    selected_primary = qualified_primary[0] if qualified_primary else None
    qualified_falsifiers = [
        key for key in FALSIFIER
        if falsifier_metrics[key]["qualified"]
        and (selected_primary is None or FALSIFIER[key] != PRIMARY[selected_primary])
    ]
    qualified_falsifiers.sort(key=lambda key: (
        falsifier_metrics[key]["balanced_accuracy"],
        falsifier_metrics[key]["repeat_agreement"],
        -cost["tokens_by_model"].get(FALSIFIER[key], 0),
    ), reverse=True)
    selected_falsifier = qualified_falsifiers[0] if qualified_falsifiers else None
    status = "PASS" if selected_primary and selected_falsifier else "REVISE_BEFORE_R3_PILOT"
    result = {
        "status": status,
        "primary_metrics": primary_metrics,
        "falsifier_metrics": falsifier_metrics,
        "selected_primary": selected_primary,
        "selected_falsifier": selected_falsifier,
        "fresh_api_exposure": 0,
        "test_access": 0,
        "cost": cost,
    }
    apre.write_json(root / "reports" / "gate_r3_2.json", result)

    lock_common = {
        "qualification_metrics_sha256": apre.sha({"primary": primary_metrics, "falsifier": falsifier_metrics}),
        "fresh_api_exposure_at_lock": 0,
    }
    apre.write_json(root / "locks" / "primary_model_lock.json", {
        **lock_common, "configuration_id": selected_primary,
        "model_snapshot": PRIMARY.get(selected_primary) if selected_primary else None,
    })
    apre.write_json(root / "locks" / "falsifier_model_lock.json", {
        **lock_common, "configuration_id": selected_falsifier,
        "model_snapshot": FALSIFIER.get(selected_falsifier) if selected_falsifier else None,
    })
    lock_files = [
        root / "preregistration" / "prompts" / "claimhood_v1.txt",
        root / "preregistration" / "prompts" / "facet_v1.txt",
        root / "preregistration" / "prompts" / "falsifier_v1.txt",
        root / "preregistration" / "claimhood_schema_v1.json",
        root / "preregistration" / "field_schema_v1.json",
        root / "preregistration" / "falsifier_schema_v1.json",
    ]
    apre.write_json(root / "locks" / "prompt_schema_lock.json", {
        str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest() for path in lock_files
    })

    lines = [
        "# R3 Pointwise Model Role Qualification",
        "",
        f"- Gate R3-2: **{status}**",
        f"- Primary: `{selected_primary or 'NONE'}`",
        f"- Falsifier: `{selected_falsifier or 'NONE'}`",
        "- Data: DEV_EXPOSED_24 only",
        "- Fresh API exposure: `0`",
        "",
        "| Primary | Claim agreement | Positive F1 | Critical facet | Control BA | Qualified |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for config, metrics in primary_metrics.items():
        lines.append(f"| {config} | {metrics['claimhood_repeat_agreement']:.4f} | {metrics['positive_anchor_set_f1']:.4f} | {metrics['critical_facet_repeat_agreement']:.4f} | {metrics['deterministic_control_balanced_accuracy']:.4f} | {metrics['qualified']} |")
    lines.extend(["", "| Falsifier | Supported recall | Contradicted recall | BA | Repeat | Qualified |", "|---|---:|---:|---:|---:|---|"])
    for config, metrics in falsifier_metrics.items():
        lines.append(f"| {config} | {metrics['supported_control_recall']:.4f} | {metrics['contradicted_control_recall']:.4f} | {metrics['balanced_accuracy']:.4f} | {metrics['repeat_agreement']:.4f} | {metrics['qualified']} |")
    lines.extend(["", f"Actual calls: {cost['real_calls']}; input tokens: {cost['input_tokens']}; output tokens: {cost['output_tokens']}; estimated cost: ${cost['estimated_cost_usd']:.6f}."])
    (root / "reports" / "model_role_qualification.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if status == "PASS" else 4


if __name__ == "__main__":
    raise SystemExit(main())
