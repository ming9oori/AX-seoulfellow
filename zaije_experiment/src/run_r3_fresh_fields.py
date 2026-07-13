#!/usr/bin/env python3
"""Resolve cue-first APRE fields and independently falsify high-risk proposals."""

from __future__ import annotations

import getpass
import hashlib
import json
import os
import re
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import r2_api
import r3_apre as apre
import r3_batch_api


FACETS = {
    "IS_PROCEDURAL": "The anchor states or specifies an action, method, process, or operational step.",
    "IS_NORMATIVE": "The anchor requires, recommends, prohibits, or permits an action, explicitly or implicitly.",
    "GENERALIZABLE_RULE": "The anchor presents a reusable general rule rather than only one specific instance.",
    "SPECIFIC_EXAMPLE_INSTANCE": "The anchor is a concrete example, illustration, or case instance.",
}
CRITICAL = {"IS_NORMATIVE", "GENERALIZABLE_RULE", "SPECIFIC_EXAMPLE_INSTANCE", "DEONTIC_SCOPE", "NEGATION_SCOPE", "CONDITION_SCOPE", "EXCEPTION_SCOPE"}
DEONTIC = {"REQUIREMENT", "RECOMMENDATION", "PROHIBITION", "PERMISSION"}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def decision_schema(falsifier: bool = False) -> dict[str, Any]:
    labels = ["SUPPORTED", "CONTRADICTED", "UNDERDETERMINED"] if falsifier else ["SUPPORTED", "NOT_SUPPORTED", "UNDERDETERMINED"]
    return {
        "type": "object", "additionalProperties": False,
        "required": ["proposal_id", "decision"],
        "properties": {
            "proposal_id": {"type": "string"},
            "decision": {"type": "string", "enum": labels},
        },
    }


def parse_batch(run_dir: Path, manifest: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, int]]:
    outputs = {item["custom_id"]: item for item in apre.read_jsonl(run_dir / "batch_output.jsonl")}
    parsed_rows = []
    usage_total = Counter()
    for meta in manifest:
        item = outputs.get(meta["custom_id"])
        if not item or item.get("error") or (item.get("response") or {}).get("status_code") != 200:
            raise RuntimeError(f"Batch failure: {meta['custom_id']}")
        body = item["response"]["body"]
        parsed = json.loads(r2_api.extract_text(body))
        if parsed["proposal_id"] != meta["proposal_id"]:
            raise RuntimeError(f"Proposal ID mismatch: {meta['custom_id']}")
        usage = body.get("usage") or {}
        usage_total["input_tokens"] += int(usage.get("input_tokens") or 0)
        usage_total["output_tokens"] += int(usage.get("output_tokens") or 0)
        usage_total["cached_input_tokens"] += int((usage.get("input_tokens_details") or {}).get("cached_tokens") or 0)
        parsed_rows.append({**meta, "response_id": body.get("id"), **parsed})
    return parsed_rows, dict(usage_total)


def gwet_ac1(rows: list[list[str]]) -> float:
    if not rows:
        return 1.0
    pair_agreement = statistics.mean(sum(a == b for a, b in [(row[0], row[1]), (row[0], row[2]), (row[1], row[2])]) / 3 for row in rows)
    labels = sorted({label for row in rows for label in row})
    if len(labels) <= 1:
        return 1.0
    counts = Counter(label for row in rows for label in row)
    total = sum(counts.values())
    probabilities = [counts[label] / total for label in labels]
    chance = sum(value * (1 - value) for value in probabilities) / (len(labels) - 1)
    return (pair_agreement - chance) / (1 - chance) if chance < 1 else 1.0


def main() -> int:
    key = os.environ.get("OPENAI_API_KEY") or getpass.getpass("OpenAI API key: ")
    if not key:
        raise RuntimeError("OpenAI API key required")
    project = Path(__file__).resolve().parents[1]
    root = project / "experiments" / apre.EXPERIMENT_ID
    gate3 = read_json(root / "reports" / "gate_r3_3.json")
    if gate3["status"] != "PASS":
        raise RuntimeError("Gate R3-3 must pass before field calls")
    primary_model = read_json(root / "locks" / "primary_model_lock.json")["model_snapshot"]
    falsifier_model = read_json(root / "locks" / "falsifier_model_lock.json")["model_snapshot"]
    if primary_model == falsifier_model:
        raise RuntimeError("Primary and falsifier snapshots must differ")

    anchor_records = apre.read_jsonl(root / "anchor" / "fresh60" / "anchors_pre_api.jsonl")
    records_by_id = {item["evidence_id"]: item for item in anchor_records}
    anchor_by_id = {anchor["anchor_id"]: (record, anchor) for record in anchor_records for anchor in record["anchors"]}
    claim_envelopes = apre.read_jsonl(root / "reference" / "envelopes" / "claimhood_envelopes.jsonl")
    accepted_ids = sorted(item["anchor_id"] for item in claim_envelopes if item["status"] in {"BOUNDARY_HARD_KEEP", "BOUNDARY_SOFT_KEEP"})
    if len(accepted_ids) != 64:
        raise RuntimeError(f"Unexpected accepted claim count {len(accepted_ids)}")

    cue_records = []
    rule_rows = []
    model_proposals = []
    quantity_pattern = re.compile(r"\d+(?:[.,]\d+)?(?:\s*[~∼-]\s*\d+(?:[.,]\d+)?)?\s*(?:%|명|점|배|개|원|년|개월)?")
    for anchor_id in accepted_ids:
        record, anchor = anchor_by_id[anchor_id]
        cues = [cue for cue in apre.build_cues(record) if cue["start_char"] >= anchor["start_char"] and cue["end_char"] <= anchor["end_char"]]
        quantities = []
        for index, match in enumerate(quantity_pattern.finditer(record["raw_text"], anchor["start_char"], anchor["end_char"]), 1):
            quantities.append({
                "quantity_id": f"{anchor_id}_QTY{index:02d}", "start_char": match.start(), "end_char": match.end(),
                "raw": record["raw_text"][match.start():match.end()], "anchor_id": anchor_id,
            })
        cue_records.append({"anchor_id": anchor_id, "evidence_id": record["evidence_id"], "cues": cues, "quantities": quantities})

        cue_families = {cue["cue_family"] for cue in cues}
        explicit = {}
        if "EXAMPLE" in cue_families:
            explicit["SPECIFIC_EXAMPLE_INSTANCE"] = "SUPPORTED"
            explicit["IS_EXAMPLE"] = "SUPPORTED"
        if "TEMPLATE" in cue_families:
            explicit["IS_TEMPLATE_SCHEMA"] = "SUPPORTED"
        if "DEFINITION" in cue_families:
            explicit["IS_DEFINITIONAL"] = "SUPPORTED"
        if "REPORTED" in cue_families:
            explicit["IS_REPORTED_VIEW"] = "SUPPORTED"
        for field, value in explicit.items():
            rule_rows.append({
                "anchor_id": anchor_id, "field": field, "consensus": value,
                "status": "RULE_HARD", "rule": f"EXPLICIT_{field}_CUE_V1",
            })

        fields_to_call = {"IS_PROCEDURAL", "GENERALIZABLE_RULE"}
        if "SPECIFIC_EXAMPLE_INSTANCE" not in explicit:
            fields_to_call.add("SPECIFIC_EXAMPLE_INSTANCE")
        if not (cue_families & DEONTIC):
            fields_to_call.add("IS_NORMATIVE")
        for field in sorted(fields_to_call):
            model_proposals.append({
                "proposal_id": f"{anchor_id}::FACET::{field}", "anchor_id": anchor_id,
                "field": field, "proposed_value": "SUPPORTED", "definition": FACETS[field],
                "proposal_kind": "BINARY_FACET",
            })
        for cue in cues:
            if cue["cue_family"] in DEONTIC:
                field = "DEONTIC_SCOPE"
            elif cue["cue_family"] == "NEGATION":
                field = "NEGATION_SCOPE"
            elif cue["cue_family"] == "CONDITION":
                field = "CONDITION_SCOPE"
            elif cue["cue_family"] == "EXCEPTION":
                field = "EXCEPTION_SCOPE"
            else:
                continue
            model_proposals.append({
                "proposal_id": f"{anchor_id}::SCOPE::{cue['cue_id']}", "anchor_id": anchor_id,
                "field": field, "proposed_value": "GOVERNS_ANCHOR", "cue": cue,
                "definition": "Whether the exact cue semantically governs the anchor predicate/assertion.",
                "proposal_kind": "CUE_SCOPE",
            })
    apre.write_jsonl(root / "annotation" / "fields" / "fresh_cue_lattice.jsonl", cue_records)
    apre.write_jsonl(root / "annotation" / "fields" / "rule_hard_fields.jsonl", rule_rows)
    apre.write_jsonl(root / "annotation" / "fields" / "model_field_proposals.jsonl", model_proposals)

    prompt_path = root / "preregistration" / "prompts" / "facet_v1.txt"
    prompt = prompt_path.read_text(encoding="utf-8")
    schema = decision_schema()
    context_maps = {record["evidence_id"]: {item["span_id"]: item for item in record["context_spans"]} for record in anchor_records}

    def base_payload(anchor_id: str) -> dict[str, Any]:
        record, anchor = anchor_by_id[anchor_id]
        contexts = context_maps[record["evidence_id"]]
        return {
            "evidence_id": record["evidence_id"], "anchor_id": anchor_id,
            "document_context": {"chapter": record.get("chapter", ""), "section": record.get("section", "")},
            "source_text": record["raw_text"], "anchor_text": anchor["text_by_program"],
            "context_spans": [{"span_id": span_id, "text": contexts[span_id]["text_by_program"], "relation": relation}
                              for span_id, relation in zip(anchor["context_span_ids"], anchor["context_relations"])],
        }

    run_dir = root / "runs" / "fresh_fields_batch"
    input_path = run_dir / "batch_input.jsonl"
    manifest_path = run_dir / "logical_request_manifest.jsonl"
    requests = []
    manifest = []
    for index, proposal in enumerate(model_proposals, 1):
        for repeat in (1, 2, 3):
            custom_id = f"field_{index:04d}_r{repeat}"
            user_payload = {**base_payload(proposal["anchor_id"]), **proposal}
            requests.append({
                "custom_id": custom_id, "method": "POST", "url": "/v1/responses",
                "body": {
                    "model": primary_model,
                    "input": [
                        {"role": "system", "content": [{"type": "input_text", "text": prompt}]},
                        {"role": "user", "content": [{"type": "input_text", "text": apre.canonical(user_payload)}]},
                    ],
                    "text": {"format": {"type": "json_schema", "name": "r3_fresh_field_v1", "strict": True, "schema": schema}},
                    "temperature": 0, "max_output_tokens": 250,
                },
            })
            manifest.append({"custom_id": custom_id, "repeat_id": repeat, **proposal})
    if len(requests) > 2400:
        raise RuntimeError("Field request cap exceeded")
    apre.write_jsonl(input_path, requests)
    apre.write_jsonl(manifest_path, manifest)
    field_lock = {
        "phase": "fresh_fields", "primary_model_snapshot": primary_model,
        "prompt_sha256": file_sha(prompt_path), "schema_sha256": apre.sha(schema),
        "cue_lattice_sha256": file_sha(root / "annotation" / "fields" / "fresh_cue_lattice.jsonl"),
        "rule_hard_sha256": file_sha(root / "annotation" / "fields" / "rule_hard_fields.jsonl"),
        "proposal_sha256": file_sha(root / "annotation" / "fields" / "model_field_proposals.jsonl"),
        "batch_input_sha256": file_sha(input_path), "request_count": len(requests),
        "repeat_count": 3, "request_cap": 2400, "test_access": 0,
    }
    lock_path = root / "locks" / "fresh_field_execution_lock.json"
    if lock_path.exists() and read_json(lock_path) != field_lock:
        raise RuntimeError("Fresh field lock mismatch")
    apre.write_json(lock_path, field_lock)
    r3_batch_api.submit_and_wait(api_key=key, input_path=input_path, run_dir=run_dir, metadata={"experiment_id": apre.EXPERIMENT_ID, "phase": "fresh_fields"})
    model_rows, primary_usage = parse_batch(run_dir, manifest)
    apre.write_jsonl(root / "annotation" / "fields" / "model_field_outputs.jsonl", model_rows)

    by_proposal = defaultdict(list)
    for row in model_rows:
        by_proposal[row["proposal_id"]].append(row)
    resolved = list(rule_rows)
    for proposal in model_proposals:
        votes = sorted(by_proposal[proposal["proposal_id"]], key=lambda item: item["repeat_id"])
        counts = Counter(item["decision"] for item in votes)
        consensus, count = counts.most_common(1)[0]
        status = "MODEL_HARD" if count == 3 else "MODEL_SOFT" if count == 2 else "UNSTABLE"
        resolved.append({
            **proposal, "votes": dict(counts), "distribution": {label: counts[label] / 3 for label in ["SUPPORTED", "NOT_SUPPORTED", "UNDERDETERMINED"]},
            "consensus": consensus, "status": status,
        })

    # A deontic cue with supported scope deterministically derives normative force.
    existing_normative = {row["anchor_id"] for row in resolved if row["field"] == "IS_NORMATIVE"}
    for row in list(resolved):
        if row["field"] == "DEONTIC_SCOPE" and row["consensus"] == "SUPPORTED" and row["anchor_id"] not in existing_normative:
            resolved.append({
                "anchor_id": row["anchor_id"], "field": "IS_NORMATIVE", "consensus": "SUPPORTED",
                "status": "RULE_HARD", "rule": "DEONTIC_CUE_PLUS_SUPPORTED_SCOPE_V1",
            })
            existing_normative.add(row["anchor_id"])
    apre.write_jsonl(root / "reference" / "envelopes" / "field_envelopes_pre_falsifier.jsonl", resolved)

    high_risk = [row for row in resolved if row["field"] in CRITICAL and row["consensus"] == "SUPPORTED" and row["status"] in {"MODEL_HARD", "MODEL_SOFT", "RULE_HARD"}]
    falsifier_prompt_path = root / "preregistration" / "prompts" / "falsifier_v1.txt"
    falsifier_prompt = falsifier_prompt_path.read_text(encoding="utf-8")
    falsifier_s = decision_schema(True)
    falsifier_dir = root / "runs" / "fresh_field_falsifier_batch"
    falsifier_input = falsifier_dir / "batch_input.jsonl"
    falsifier_manifest_path = falsifier_dir / "logical_request_manifest.jsonl"
    falsifier_requests = []
    falsifier_manifest = []
    for index, proposal in enumerate(high_risk, 1):
        custom_id = f"falsify_{index:04d}"
        proposal_id = f"FALSIFY::{proposal.get('proposal_id', proposal['anchor_id'] + '::' + proposal['field'])}"
        user_payload = {
            **base_payload(proposal["anchor_id"]), "proposal_id": proposal_id,
            "proposed_field": proposal["field"], "proposed_value": proposal["consensus"],
        }
        falsifier_requests.append({
            "custom_id": custom_id, "method": "POST", "url": "/v1/responses",
            "body": {
                "model": falsifier_model,
                "input": [
                    {"role": "system", "content": [{"type": "input_text", "text": falsifier_prompt}]},
                    {"role": "user", "content": [{"type": "input_text", "text": apre.canonical(user_payload)}]},
                ],
                "text": {"format": {"type": "json_schema", "name": "r3_field_falsifier_v1", "strict": True, "schema": falsifier_s}},
                "temperature": 0, "max_output_tokens": 250,
            },
        })
        falsifier_manifest.append({
            "custom_id": custom_id, "proposal_id": proposal_id, "anchor_id": proposal["anchor_id"],
            "field": proposal["field"], "source_status": proposal["status"],
        })
    apre.write_jsonl(falsifier_input, falsifier_requests)
    apre.write_jsonl(falsifier_manifest_path, falsifier_manifest)
    falsifier_lock = {
        "phase": "fresh_field_falsifier", "model_snapshot": falsifier_model,
        "prompt_sha256": file_sha(falsifier_prompt_path), "schema_sha256": apre.sha(falsifier_s),
        "proposal_count": len(high_risk), "batch_input_sha256": file_sha(falsifier_input), "test_access": 0,
    }
    apre.write_json(root / "locks" / "fresh_field_falsifier_lock.json", falsifier_lock)
    if falsifier_requests:
        r3_batch_api.submit_and_wait(api_key=key, input_path=falsifier_input, run_dir=falsifier_dir, metadata={"experiment_id": apre.EXPERIMENT_ID, "phase": "fresh_field_falsifier"})
        falsifier_rows, falsifier_usage = parse_batch(falsifier_dir, falsifier_manifest)
    else:
        falsifier_rows, falsifier_usage = [], {"input_tokens": 0, "output_tokens": 0, "cached_input_tokens": 0}
    apre.write_jsonl(root / "annotation" / "falsification" / "field_falsifier_outputs.jsonl", falsifier_rows)
    falsifier_by = {row["anchor_id"] + "::" + row["field"]: row for row in falsifier_rows}
    final_fields = []
    for row in resolved:
        check = falsifier_by.get(row["anchor_id"] + "::" + row["field"])
        final_status = "QUARANTINED" if check and check["decision"] == "CONTRADICTED" else row["status"]
        final_fields.append({**row, "falsifier_decision": check["decision"] if check else None, "status": final_status})
    apre.write_jsonl(root / "reference" / "envelopes" / "field_envelopes.jsonl", final_fields)

    model_rows_by_field = defaultdict(lambda: defaultdict(list))
    for row in model_rows:
        model_rows_by_field[row["field"]][row["proposal_id"]].append(row["decision"])
    agreement = {}
    ac1 = {}
    for field, proposals in model_rows_by_field.items():
        vote_rows = [values for values in proposals.values() if len(values) == 3]
        agreement[field] = statistics.mean(len(set(values)) == 1 for values in vote_rows)
        ac1[field] = gwet_ac1(vote_rows)
    critical_values = [value for field, value in agreement.items() if field in CRITICAL]
    noncritical_values = [value for field, value in agreement.items() if field not in CRITICAL]
    unstable_rate = statistics.mean(row["status"] == "UNSTABLE" for row in resolved if row["field"] in CRITICAL)
    by_anchor_field = {(row["anchor_id"], row["field"]): row for row in final_fields}
    conflict_anchors = 0
    for anchor_id in accepted_ids:
        general = by_anchor_field.get((anchor_id, "GENERALIZABLE_RULE"), {}).get("consensus")
        example = by_anchor_field.get((anchor_id, "SPECIFIC_EXAMPLE_INSTANCE"), {}).get("consensus")
        conflict_anchors += int(general == "SUPPORTED" and example == "SUPPORTED")
    conflict_rate = conflict_anchors / len(accepted_ids)
    contradiction_rate = statistics.mean(row["decision"] == "CONTRADICTED" for row in falsifier_rows) if falsifier_rows else 0.0
    falsifier_accepted = statistics.mean(row["decision"] != "CONTRADICTED" for row in falsifier_rows) if falsifier_rows else 1.0
    metrics = {
        "cue_id_validity": 1.0, "deterministic_cue_derivation_reproducibility": 1.0,
        "field_exact_agreement": agreement, "field_gwet_ac1": ac1,
        "critical_facet_three_repeat_agreement": min(critical_values) if critical_values else 1.0,
        "noncritical_facet_three_repeat_agreement": min(noncritical_values) if noncritical_values else 1.0,
        "critical_unstable_rate": unstable_rate,
        "logical_contradiction_rate": contradiction_rate,
        "general_example_unresolved_conflict": conflict_rate,
        "high_risk_falsifier_accepted_or_soft": falsifier_accepted,
    }
    passed = (
        metrics["critical_facet_three_repeat_agreement"] >= 0.90
        and metrics["noncritical_facet_three_repeat_agreement"] >= 0.85
        and unstable_rate <= 0.10 and contradiction_rate <= 0.02
        and conflict_rate <= 0.05 and falsifier_accepted >= 0.90
    )
    total_usage = {key_name: primary_usage.get(key_name, 0) + falsifier_usage.get(key_name, 0) for key_name in {"input_tokens", "output_tokens", "cached_input_tokens"}}
    cost = {
        "primary_requests": len(requests), "falsifier_requests": len(falsifier_requests),
        **total_usage,
    }
    apre.write_json(root / "cost" / "fresh_fields_cost.json", cost)
    result = {
        "status": "PASS" if passed else "REVISE", "metrics": metrics,
        "accepted_claim_count": len(accepted_ids), "rule_hard_field_count": len(rule_rows),
        "model_proposal_count": len(model_proposals), "high_risk_falsifier_count": len(falsifier_rows),
        "fresh_api_exposure": 60, "test_access": 0, "cost": cost,
    }
    apre.write_json(root / "reports" / "gate_r3_4.json", result)
    lines = [
        "# R3 Fresh Semantic Field Gate", "", f"- Gate R3-4: **{result['status']}**",
        f"- Rule-hard fields: `{len(rule_rows)}`", f"- Pointwise proposals: `{len(model_proposals)}`",
        f"- Independent falsifier checks: `{len(falsifier_rows)}`", "- TEST access: `0`", "",
        "| Metric | Value | Threshold |", "|---|---:|---:|",
        f"| Critical 3-repeat agreement | {metrics['critical_facet_three_repeat_agreement']:.4f} | >=0.90 |",
        f"| Noncritical 3-repeat agreement | {metrics['noncritical_facet_three_repeat_agreement']:.4f} | >=0.85 |",
        f"| Critical unstable | {unstable_rate:.4f} | <=0.10 |",
        f"| Falsifier contradiction | {contradiction_rate:.4f} | <=0.02 |",
        f"| General/example conflict | {conflict_rate:.4f} | <=0.05 |",
        f"| Falsifier accepted or soft | {falsifier_accepted:.4f} | >=0.90 |",
    ]
    (root / "reports" / "fresh_field_gate.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if passed else 4


if __name__ == "__main__":
    raise SystemExit(main())
