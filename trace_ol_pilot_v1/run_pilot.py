#!/usr/bin/env python3
"""Execute the locked TRACE-OL pilot experiment end to end."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pilot_lib as lib


HERE = Path(__file__).resolve().parent
INPUT_CANDIDATES = sorted((HERE.parent / "handoff-hanyang").rglob("자이제_1.xlsx"))
DEFAULT_INPUT = INPUT_CANDIDATES[0] if len(INPUT_CANDIDATES) == 1 else HERE.parent / "handoff-hanyang" / "자이제_1.xlsx"
DEFAULT_OUTPUT = HERE / "runs" / "pilot_run_20260710_v1"
MODEL_MINI = "gpt-4o-mini-2024-07-18"
MODEL_STRONG = "gpt-4o-2024-08-06"
PRICING = {
    MODEL_MINI: {"input": 0.15, "cached": 0.075, "output": 0.60},
    MODEL_STRONG: {"input": 2.50, "cached": 1.25, "output": 10.00},
}
MAX_CALLS = 80
MAX_INPUT_TOKENS = 600_000
MAX_OUTPUT_TOKENS = 250_000
MAX_STRONG_CALLS = 8


def canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha(value: Any) -> str:
    data = value if isinstance(value, bytes) else canonical(value).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def strictify(node: Any) -> Any:
    """Make the local schema compatible with OpenAI strict structured output."""
    if isinstance(node, list):
        return [strictify(item) for item in node]
    if not isinstance(node, dict):
        return node
    result = {key: strictify(value) for key, value in node.items() if key not in {"$schema", "$id", "title", "default"}}
    if "const" in result and "type" not in result:
        const_type = {str: "string", bool: "boolean", int: "integer", float: "number"}.get(type(result["const"]))
        if const_type:
            result["type"] = const_type
    if result.get("type") == "object" and "properties" in result:
        result["required"] = list(result["properties"])
        result["additionalProperties"] = False
    return result


def annotation_batch_schema() -> dict[str, Any]:
    base = strictify(read_json(HERE / "schemas" / "atomic_work_claim_schema_v0.2.json"))
    defs = base.pop("$defs")
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["annotations"],
        "properties": {"annotations": {"type": "array", "items": base}},
        "$defs": defs,
    }


def triple_batch_schema() -> dict[str, Any]:
    spanless_triple = {
        "type": "object", "additionalProperties": False,
        "required": ["subject", "predicate", "object", "source_span"],
        "properties": {
            "subject": {"type": "string"}, "predicate": {"type": "string"},
            "object": {"type": "string"}, "source_span": {"type": "string"},
        },
    }
    item = {
        "type": "object", "additionalProperties": False, "required": ["evidence_id", "triples"],
        "properties": {"evidence_id": {"type": "string"}, "triples": {"type": "array", "items": spanless_triple}},
    }
    return {"type": "object", "additionalProperties": False, "required": ["items"], "properties": {"items": {"type": "array", "items": item}}}


def selective_schema() -> dict[str, Any]:
    annotation = annotation_batch_schema()
    claim = annotation["properties"]["annotations"]["items"]["properties"]["claims"]["items"]
    return {
        "type": "object", "additionalProperties": False, "required": ["decisions"],
        "properties": {"decisions": {"type": "array", "items": {
            "type": "object", "additionalProperties": False,
            "required": ["candidate_id", "evidence_id", "decision", "claim", "reason_code"],
            "properties": {
                "candidate_id": {"type": "string"}, "evidence_id": {"type": "string"},
                "decision": {"type": "string", "enum": ["accept", "reject", "abstain", "needs_review"]},
                "claim": {"anyOf": [claim, {"type": "null"}]},
                "reason_code": {"type": "string"},
            },
        }}},
        "$defs": annotation["$defs"],
    }


def adjudicator_schema() -> dict[str, Any]:
    annotation = annotation_batch_schema()
    annotation_item = annotation["properties"]["annotations"]["items"]
    return {
        "type": "object", "additionalProperties": False, "required": ["adjudications"],
        "properties": {"adjudications": {"type": "array", "items": {
            "type": "object", "additionalProperties": False,
            "required": ["evidence_id", "decision", "final_annotation", "reason_code"],
            "properties": {
                "evidence_id": {"type": "string"},
                "decision": {"type": "string", "enum": ["A_ACCEPT", "B_ACCEPT", "C_ACCEPT", "MERGED_CORRECTION", "SPLIT", "NEEDS_REVIEW"]},
                "final_annotation": annotation_item,
                "reason_code": {"type": "string", "enum": ["SPAN", "TYPE", "MODALITY", "POLARITY", "CONDITION", "PROMOTION", "ARGUMENT", "SENSE", "INSUFFICIENT_EVIDENCE"]},
            },
        }}},
        "$defs": annotation["$defs"],
    }


@dataclass
class ApiLedger:
    output_dir: Path
    api_key: str
    calls: list[dict[str, Any]] = field(default_factory=list)
    input_tokens: int = 0
    output_tokens: int = 0
    strong_calls: int = 0

    def __post_init__(self) -> None:
        recovery_path = self.output_dir / "recovery_failed_calls.json"
        if not recovery_path.exists():
            return
        for row in read_json(recovery_path):
            usage = {
                "input_tokens": int(row["estimated_input_tokens"]),
                "output_tokens": int(row["observed_output_tokens"]),
                "input_tokens_details": {"cached_tokens": 0},
            }
            self._record(
                row["phase"], row["model_id"], "unavailable", "failed-no-cache", [], usage,
                False, float(row["estimated_cost_usd"]), status="FAILED_TRUNCATED_ESTIMATED",
            )

    def _cached_path(self, cache_key: str) -> Path:
        return self.output_dir / "cache" / f"{cache_key}.json"

    def call(
        self,
        *,
        phase: str,
        model: str,
        prompt: str,
        payload: Any,
        schema_name: str,
        schema: dict[str, Any],
        evidence_ids: list[str],
        max_output_tokens: int = 20_000,
    ) -> dict[str, Any]:
        prompt_hash = sha(prompt)
        payload_hash = sha(payload)
        cache_key = sha([model, prompt_hash, payload_hash, schema_name, lib.SCHEMA_VERSION])
        cache_path = self._cached_path(cache_key)
        if cache_path.exists():
            cached = read_json(cache_path)
            cached_usage = cached.get("usage", {})
            self._record(phase, model, prompt_hash, cache_key, evidence_ids, cached_usage, True, self._cost(model, cached_usage), status="SUCCESS_CACHE_REUSE")
            print(f"[cache] {phase}: {len(evidence_ids)} evidence", flush=True)
            return cached["parsed"]

        if self.real_calls >= MAX_CALLS:
            raise RuntimeError("API hard stop: max_total_calls=80")
        if model == MODEL_STRONG and self.strong_calls >= MAX_STRONG_CALLS:
            raise RuntimeError("API hard stop: max_strong_model_calls=8")

        user_payload = canonical(payload)
        request_body = {
            "model": model,
            "input": [
                {"role": "system", "content": [{"type": "input_text", "text": prompt}]},
                {"role": "user", "content": [{"type": "input_text", "text": user_payload}]},
            ],
            "text": {"format": {"type": "json_schema", "name": schema_name, "strict": True, "schema": schema}},
            "temperature": 0,
            "max_output_tokens": max_output_tokens,
        }
        raw = json.dumps(request_body, ensure_ascii=False).encode("utf-8")
        request = urllib.request.Request(
            "https://api.openai.com/v1/responses", data=raw, method="POST",
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
        )
        started = time.time()
        last_error: Exception | None = None
        for attempt in range(2):
            try:
                with urllib.request.urlopen(request, timeout=180) as response:
                    body = json.loads(response.read().decode("utf-8"))
                parsed = json.loads(extract_output_text(body))
                usage = body.get("usage") or {}
                cost = self._cost(model, usage)
                cache_path.parent.mkdir(parents=True, exist_ok=True)
                write_json(cache_path, {"response_id": body.get("id"), "usage": usage, "parsed": parsed})
                self._record(phase, model, prompt_hash, cache_key, evidence_ids, usage, False, cost, attempt, time.time() - started, "SUCCESS")
                print(f"[api {self.real_calls:02d}/{MAX_CALLS}] {phase}: {len(evidence_ids)} evidence, {usage.get('input_tokens', 0)} in/{usage.get('output_tokens', 0)} out", flush=True)
                return parsed
            except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, json.JSONDecodeError, KeyError) as exc:
                last_error = exc
                if isinstance(exc, urllib.error.HTTPError):
                    detail = exc.read().decode("utf-8", errors="replace")[:2_000]
                    last_error = RuntimeError(f"HTTP {exc.code}: {detail}")
                if attempt == 0:
                    time.sleep(2)
        raise RuntimeError(f"OpenAI call failed in {phase}: {last_error}")

    @property
    def real_calls(self) -> int:
        return len(self.calls)

    def _cost(self, model: str, usage: dict[str, Any]) -> float:
        prices = PRICING[model]
        inp = int(usage.get("input_tokens") or 0)
        out = int(usage.get("output_tokens") or 0)
        cached = int((usage.get("input_tokens_details") or {}).get("cached_tokens") or 0)
        return ((inp - cached) * prices["input"] + cached * prices["cached"] + out * prices["output"]) / 1_000_000

    def _record(
        self, phase: str, model: str, prompt_hash: str, cache_key: str, evidence_ids: list[str],
        usage: dict[str, Any], cache_hit: bool, cost: float, retry: int = 0, latency: float = 0.0,
        status: str = "SUCCESS",
    ) -> None:
        inp = int(usage.get("input_tokens") or 0)
        out = int(usage.get("output_tokens") or 0)
        if self.input_tokens + inp > MAX_INPUT_TOKENS or self.output_tokens + out > MAX_OUTPUT_TOKENS:
            raise RuntimeError("API hard stop: token budget exceeded")
        self.input_tokens += inp
        self.output_tokens += out
        if model == MODEL_STRONG:
            self.strong_calls += 1
        self.calls.append({
            "call_index": len(self.calls) + 1, "phase": phase, "model_id": model,
            "prompt_hash": prompt_hash, "cache_key": cache_key, "evidence_ids": "|".join(evidence_ids),
            "input_tokens": inp, "cached_input_tokens": int((usage.get("input_tokens_details") or {}).get("cached_tokens") or 0),
            "output_tokens": out, "estimated_cost_usd": round(cost, 8), "cache_hit": cache_hit,
            "retry_count": retry, "latency_seconds": round(latency, 3), "status": status,
        })

    def save(self) -> dict[str, Any]:
        fields = ["call_index", "phase", "model_id", "prompt_hash", "cache_key", "evidence_ids", "input_tokens", "cached_input_tokens", "output_tokens", "estimated_cost_usd", "cache_hit", "retry_count", "latency_seconds", "status"]
        write_csv(self.output_dir / "cost_ledger.csv", self.calls, fields)
        write_jsonl(self.output_dir / "api_call_ledger.jsonl", self.calls)
        total_cost = sum(float(row["estimated_cost_usd"]) for row in self.calls)
        strong_cost = sum(float(row["estimated_cost_usd"]) for row in self.calls if row["model_id"] == MODEL_STRONG)
        summary = {
            "actual_api_calls": self.real_calls, "cache_hits": sum(row["cache_hit"] for row in self.calls),
            "input_tokens": self.input_tokens, "output_tokens": self.output_tokens,
            "estimated_cost_usd": round(total_cost, 6), "strong_model_calls": self.strong_calls,
            "failed_truncated_calls": sum(row["status"].startswith("FAILED") for row in self.calls),
            "strong_model_cost_share": round(strong_cost / total_cost, 4) if total_cost else 0.0,
            "hard_caps": {"calls": MAX_CALLS, "input_tokens": MAX_INPUT_TOKENS, "output_tokens": MAX_OUTPUT_TOKENS, "strong_calls": MAX_STRONG_CALLS},
        }
        write_json(self.output_dir / "api_budget_summary.json", summary)
        return summary


def extract_output_text(response: dict[str, Any]) -> str:
    parts = []
    for output in response.get("output") or []:
        for content in output.get("content") or []:
            if content.get("type") == "output_text":
                parts.append(content["text"])
            elif content.get("type") == "refusal":
                raise RuntimeError(f"Model refusal: {content.get('refusal')}")
    if not parts:
        raise KeyError("No output_text in response")
    return "".join(parts)


def prompt_file(name: str, output_contract: str) -> str:
    text = (HERE / "prompts" / name).read_text(encoding="utf-8")
    text = text.split("[INPUT]", 1)[0].strip()
    return text + "\n\n[STRICT OUTPUT CONTRACT]\n" + output_contract


def sample_bundles(all_bundles: list[dict[str, Any]], sample: list[dict[str, Any]]) -> list[dict[str, Any]]:
    wanted = {row["evidence_id"] for row in sample}
    return [bundle for bundle in all_bundles if bundle["target"]["evidence_id"] in wanted]


def public_annotations(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Remove internal gate/evaluation fields from schema-conformant exports."""
    output = json.loads(json.dumps(rows, ensure_ascii=False))
    for row in output:
        row.pop("triples", None)
        for claim in row.get("claims") or []:
            claim.pop("confidence", None)
    return output


def annotate_batches(
    ledger: ApiLedger, *, phase: str, model: str, prompt: str, bundles: list[dict[str, Any]],
    sample_rows: list[dict[str, Any]], role: str, prompt_version: str, max_batches: int | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    sample_ids = {bundle["target"]["evidence_id"] for bundle in bundles}
    rows = [row for row in sample_rows if row["evidence_id"] in sample_ids]
    batches = lib.pack_bundles(bundles, rows)
    output: list[dict[str, Any]] = []
    issues: list[dict[str, Any]] = []
    skipped: list[str] = []
    for batch_index, batch in enumerate(batches):
        ids = [bundle["target"]["evidence_id"] for bundle in batch]
        if max_batches is not None and batch_index >= max_batches:
            skipped.extend(ids)
            continue
        result = ledger.call(
            phase=f"{phase}_batch_{batch_index + 1:02d}", model=model, prompt=prompt,
            payload={"evidence_bundles": batch}, schema_name=f"{phase.lower()}_annotations",
            schema=annotation_batch_schema(), evidence_ids=ids,
        )
        by_id = {row.get("evidence_id"): row for row in result.get("annotations") or []}
        for bundle in batch:
            eid = bundle["target"]["evidence_id"]
            raw = by_id.get(eid, {"evidence_id": eid, "claims": []})
            normalized, row_issues = lib.normalize_annotation(raw, bundle, role, model, prompt_version)
            output.append(normalized)
            issues.extend(row_issues)
    return output, issues, skipped


def direct_triples_to_claims(items: list[dict[str, Any]], bundles_by_id: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    predictions = []
    for item in items:
        eid = item["evidence_id"]
        source = bundles_by_id[eid]["target"]["text"]
        claims = []
        for index, triple in enumerate(item.get("triples") or []):
            span_text = triple.get("source_span") or ""
            start = source.find(span_text)
            if start < 0:
                continue
            claims.append({
                "claim_id": f"e0:{lib.stable_hash([eid, triple, index], 28)}",
                "source_span": {"evidence_id": eid, "text": span_text, "start": start, "end": start + len(span_text)},
                "claim_family": "FACTUAL", "claim_type": "DescriptiveFact",
                "arguments": [], "predicate_normalized": triple.get("predicate") or "RELATED_TO",
                "modality": "DESCRIPTIVE", "polarity": "POSITIVE", "conditions": [], "exceptions": [],
                "scope_span": None, "purpose_span": None, "promotion_target": "FACT_ASSERTION",
                "decision": "ACCEPT", "uncertainty_code": "NONE",
            })
        predictions.append({"evidence_id": eid, "bundle_id": bundles_by_id[eid]["bundle_id"], "annotator": {"role": "E0_DirectTriple", "model_id": MODEL_MINI, "prompt_version": "system_E0_v0.1", "schema_version": lib.SCHEMA_VERSION}, "claims": claims, "triples": item.get("triples") or []})
    return predictions


def run_direct_triple(ledger: ApiLedger, bundles: list[dict[str, Any]], sample_rows: list[dict[str, Any]], bundles_by_id: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    prompt = prompt_file("system_E0_direct_triple.txt", "Return one JSON object with exactly one key `items`; include one item for every input evidence_id.")
    output = []
    for index, batch in enumerate(lib.pack_bundles(bundles, sample_rows)):
        ids = [row["target"]["evidence_id"] for row in batch]
        result = ledger.call(phase=f"E0_batch_{index + 1:02d}", model=MODEL_MINI, prompt=prompt, payload={"evidence_bundles": batch}, schema_name="e0_direct_triples", schema=triple_batch_schema(), evidence_ids=ids)
        output.extend(result.get("items") or [])
    return direct_triples_to_claims(output, bundles_by_id)


def run_selective(ledger: ApiLedger, phase: str, candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not candidates:
        return []
    prompt = prompt_file("system_E3_E4_selective.txt", "Return one JSON object with key `decisions`; each input candidate_id must occur once. `claim` is null unless a valid accepted correction is returned.")
    payload_rows = [{"candidate_id": row["candidate_id"], "evidence_id": row["evidence_id"], "priority": row["priority"], "candidate": row["claim"], "evidence_bundle": row["bundle"]} for row in candidates]
    result = ledger.call(phase=phase, model=MODEL_MINI, prompt=prompt, payload={"selected_candidates": payload_rows}, schema_name=f"{phase.lower()}_decisions", schema=selective_schema(), evidence_ids=sorted({row["evidence_id"] for row in candidates}), max_output_tokens=10_000)
    return result.get("decisions") or []


def apply_lfs(annotations: list[dict[str, Any]], active_lfs: list[dict[str, Any]], bundles_by_id: dict[str, dict[str, Any]]) -> tuple[list[dict[str, Any]], int]:
    output = json.loads(json.dumps(annotations, ensure_ascii=False))
    corrected = 0
    for annotation in output:
        text = bundles_by_id[annotation["evidence_id"]]["target"]["text"]
        for claim in annotation.get("claims") or []:
            matches = [lf for lf in active_lfs if lf["cue"] == "generic" or lf["cue"] in text]
            if not matches:
                continue
            lf = max(matches, key=lambda row: row["validation_precision"])
            claim["claim_type"] = lf["claim_type"]
            claim["confidence"] = max(float(claim.get("confidence", 0.5)), float(lf["validation_precision"]))
            if claim["decision"] == "NEEDS_REVIEW" and claim["confidence"] >= 0.90:
                claim["decision"] = "ACCEPT"
                if claim["promotion_target"] == "NEEDS_REVIEW":
                    claim["promotion_target"] = "RULE_NODE" if claim["claim_type"] in lib.HIGH_RISK_TYPES else "FACT_ASSERTION"
                corrected += 1
    return output, corrected


def build_reference(
    ledger: ApiLedger, sample: list[dict[str, Any]], bundles: list[dict[str, Any]], bundles_by_id: dict[str, dict[str, Any]], out: Path,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    contract = "Return one JSON object with exactly one key `annotations`; include exactly one schema-valid annotation for every input evidence_id."
    prompt_a = prompt_file("reference_A.txt", contract)
    prompt_b = prompt_file("reference_B.txt", contract)
    a, issues_a, _ = annotate_batches(ledger, phase="reference_A", model=MODEL_MINI, prompt=prompt_a, bundles=bundles, sample_rows=sample, role="annotator_A", prompt_version="reference_A_v0.1")
    b, issues_b, _ = annotate_batches(ledger, phase="reference_B", model=MODEL_MINI, prompt=prompt_b, bundles=bundles, sample_rows=sample, role="annotator_B", prompt_version="reference_B_v0.1")
    write_jsonl(out / "reference" / "annotator_A_raw.jsonl", a)
    write_jsonl(out / "reference" / "annotator_B_raw.jsonl", b)
    a_by = {row["evidence_id"]: row for row in a}; b_by = {row["evidence_id"]: row for row in b}
    agreement: dict[str, dict[str, Any]] = {}
    disagreement_ids = []
    for eid in sorted(a_by):
        complete, detail = lib.annotation_agreement(a_by[eid], b_by[eid])
        agreement[eid] = {"agreed": complete, **detail}
        if not complete:
            disagreement_ids.append(eid)

    # Reserve calls for E0/E1 B2 and one call each for E3/E4 and D.
    b2_rows = [row for row in sample if row["split"] == "B2_LOCKED"]
    b2_bundles = [bundles_by_id[row["evidence_id"]] for row in b2_rows]
    system_reserve = 2 * len(lib.pack_bundles(b2_bundles, b2_rows)) + 3
    available_c_batches = max(0, MAX_CALLS - ledger.real_calls - system_reserve)
    c_bundles = [bundles_by_id[eid] for eid in disagreement_ids]
    c_rows = [row for row in sample if row["evidence_id"] in set(disagreement_ids)]
    prompt_c = prompt_file("reference_C_disagreement.txt", contract)
    c, issues_c, c_skipped = annotate_batches(ledger, phase="reference_C", model=MODEL_MINI, prompt=prompt_c, bundles=c_bundles, sample_rows=c_rows, role="annotator_C", prompt_version="reference_C_v0.1", max_batches=available_c_batches)
    write_jsonl(out / "reference" / "annotator_C_raw.jsonl", c)
    c_by = {row["evidence_id"]: row for row in c}

    references: list[dict[str, Any]] = []
    unresolved: list[dict[str, Any]] = []
    for eid in sorted(a_by, key=lambda x: bundles_by_id[x]["metadata"]["excel_row"]):
        if agreement[eid]["agreed"]:
            references.append({"evidence_id": eid, "agreement_tier": "Silver-A", "resolution": "A_B_CRITICAL_AGREEMENT", "annotation": a_by[eid]})
            continue
        if eid not in c_by:
            references.append({"evidence_id": eid, "agreement_tier": "Challenge", "resolution": "C_SKIPPED_API_CAP", "annotation": a_by[eid]})
            continue
        resolved, conflicts = lib.resolve_three_way(a_by[eid], b_by[eid], c_by[eid])
        if resolved is not None:
            references.append({"evidence_id": eid, "agreement_tier": "Silver-B", "resolution": "A_B_C_MAJORITY", "annotation": resolved})
        else:
            unresolved.append({"evidence_id": eid, "bundle": bundles_by_id[eid], "A": a_by[eid], "B": b_by[eid], "C": c_by[eid], "conflicts": conflicts})

    # D is deliberately tiny so the strong-model cost share remains bounded.
    high_risk = [row for row in unresolved if any(conflict.get("high_risk") for conflict in row["conflicts"])][:1]
    adjudicated: dict[str, dict[str, Any]] = {}
    if high_risk and ledger.real_calls < MAX_CALLS - system_reserve + 1:
        prompt_d = prompt_file("reference_D_adjudicator.txt", "Return one JSON object with key `adjudications`; do not add facts outside the supplied candidates and evidence.")
        ids = [row["evidence_id"] for row in high_risk]
        d_payload = {"high_risk_conflicts": high_risk}
        mini_cost = sum(float(row["estimated_cost_usd"]) for row in ledger.calls)
        projected_d_cost = ((len(prompt_d) + len(canonical(d_payload))) / 4 * PRICING[MODEL_STRONG]["input"] + 1_800 * PRICING[MODEL_STRONG]["output"]) / 1_000_000
        if projected_d_cost / max(mini_cost + projected_d_cost, 1e-9) <= 0.15:
            result = ledger.call(phase="reference_D_high_risk", model=MODEL_STRONG, prompt=prompt_d, payload=d_payload, schema_name="reference_d_adjudications", schema=adjudicator_schema(), evidence_ids=ids, max_output_tokens=1_800)
            adjudicated = {row["evidence_id"]: row for row in result.get("adjudications") or []}
    for row in unresolved:
        decision = adjudicated.get(row["evidence_id"])
        if decision and decision["decision"] != "NEEDS_REVIEW":
            annotation, d_issues = lib.normalize_annotation(decision["final_annotation"], row["bundle"], "adjudicator_D", MODEL_STRONG, "reference_D_v0.1")
            if not d_issues:
                references.append({"evidence_id": row["evidence_id"], "agreement_tier": "Silver-B", "resolution": f"D_{decision['decision']}", "annotation": annotation})
                continue
        references.append({"evidence_id": row["evidence_id"], "agreement_tier": "Challenge", "resolution": "UNRESOLVED_OR_D_REVIEW", "annotation": row["A"]})

    references.sort(key=lambda row: bundles_by_id[row["evidence_id"]]["metadata"]["excel_row"])
    issues = issues_a + issues_b + issues_c
    write_jsonl(out / "reference" / "reference_annotations.jsonl", references)
    write_jsonl(out / "reference" / "span_validation_issues.jsonl", issues)
    write_json(out / "reference" / "ab_agreement_details.json", agreement)
    challenge = [row for row in references if row["agreement_tier"] == "Challenge"]
    write_jsonl(out / "reference" / "challenge_set.jsonl", challenge)
    total_claims = sum(len(row.get("claims") or []) for row in a + b + c)
    summary = {
        "version": "TRACE-LLM-Silver-v0.1", "total_targets": len(references),
        "tier_counts": dict(Counter(row["agreement_tier"] for row in references)),
        "resolved_coverage": round(sum(row["agreement_tier"] != "Challenge" for row in references) / len(references), 4),
        "challenge_rate": round(len(challenge) / len(references), 4),
        "ab_agreement_rate": round(sum(row["agreed"] for row in agreement.values()) / len(agreement), 4),
        "source_span_validity": round(1 - len(issues) / max(1, total_claims + len(issues)), 4),
        "semantic_invalid_claims_removed": len(issues), "c_skipped_evidence": len(c_skipped),
        "independence": "pseudo-independent: same model snapshot, separate prompts and API calls",
        "human_gold_available": False,
    }
    write_json(out / "metrics_reference.json", summary)
    return references, summary


def system_token_summary(ledger: ApiLedger) -> dict[str, int]:
    result: dict[str, int] = Counter()
    for row in ledger.calls:
        prefix = row["phase"].split("_batch", 1)[0].split("_selected", 1)[0]
        result[prefix] += int(row["input_tokens"]) + int(row["output_tokens"])
    return dict(result)


def write_reports(out: Path, sample_audit: dict[str, Any], reference: dict[str, Any], metrics: dict[str, Any], api: dict[str, Any], neo: dict[str, Any], extras: dict[str, Any]) -> None:
    rows = []
    for system, value in metrics.items():
        rows.append({"system": system, **{key: value[key] for key in ["claim_precision", "claim_recall", "claim_f1", "family_macro_f1", "fine_type_macro_f1", "modality_macro_f1", "promotion_macro_f1", "graph_f1", "critical_error_rate"]}, "bootstrap_95_ci": value["bootstrap_95_ci"]})
    write_json(out / "metrics_claim.json", metrics)
    write_csv(out / "metrics_claim.csv", rows, list(rows[0]))
    critical_rows = []
    for system, value in metrics.items():
        critical_rows.append({"system": system, **value["critical_errors"]})
    fields = ["system"] + sorted({key for row in critical_rows for key in row if key != "system"})
    write_csv(out / "critical_errors.csv", critical_rows, fields)
    write_json(out / "metrics_graph.json", {system: {"graph_f1": row["graph_f1"]} for system, row in metrics.items()})
    write_json(out / "bootstrap_summary.json", {system: row["bootstrap_95_ci"] for system, row in metrics.items()})

    e1 = metrics["E1_full_llm"]; e4 = metrics["E4_selective_distill"]
    e0 = metrics["E0_direct_triple"]
    critical_reduction = (e0["critical_error_rate"] - e1["critical_error_rate"]) / max(e0["critical_error_rate"], 1e-9)
    gates = {
        "source_span_validity_ge_0_98": reference["source_span_validity"] >= 0.98,
        "silver_resolved_coverage_ge_0_80": reference["resolved_coverage"] >= 0.80,
        "challenge_rate_le_0_20": reference["challenge_rate"] <= 0.20,
        "claim_first_critical_error_reduction_ge_0_30": critical_reduction >= 0.30,
        "e4_vs_e1_macro_f1_gap_le_0_05": e1["family_macro_f1"] - e4["family_macro_f1"] <= 0.05,
        "e4_vs_e1_token_ratio_le_0_40": extras["e4_e1_token_ratio"] <= 0.40,
        "distillation_call_reduction_ge_0_20": extras["distillation_call_reduction"] >= 0.20,
        "provenance_path_coverage_eq_1": neo["validation"]["provenance_path_coverage"] == 1.0,
        "competency_queries_ge_8_of_10": neo["cq_passed"] >= 8 and neo["cq_total"] == 10,
    }
    write_json(out / "success_gates.json", {"gates": gates, "passed": sum(gates.values()), "total": len(gates), "status": "GO" if all(gates.values()) else "STOP_OR_REVISE"})
    lines = [
        "# TRACE-OL 자이제 파일럿 실험 결과",
        "", "## 실행 개요", "",
        f"- 입력: `자이제_1.xlsx` ({sample_audit['sample_count']}건 표본 / 전체 1,366건)",
        f"- 분할: CAL {sample_audit['split_counts']['CAL']} / B1 {sample_audit['split_counts']['B1']} / B2_LOCKED {sample_audit['split_counts']['B2_LOCKED']}",
        f"- Reference: Silver-A {reference['tier_counts'].get('Silver-A', 0)}, Silver-B {reference['tier_counts'].get('Silver-B', 0)}, Challenge {reference['tier_counts'].get('Challenge', 0)}",
        f"- API: {api['actual_api_calls']}회, input {api['input_tokens']:,} tokens, output {api['output_tokens']:,} tokens, 추정 ${api['estimated_cost_usd']:.4f}",
        "- Reference 성격: 동일 low-cost model snapshot의 별도 prompt/call에 의한 pseudo-independent LLM-Silver; human gold가 아님",
        "", "## 시스템 비교", "",
        "| 시스템 | Claim F1 | Family macro-F1 | Graph F1 | Critical error rate |",
        "|---|---:|---:|---:|---:|",
    ]
    for system, value in metrics.items():
        lines.append(f"| {system} | {value['claim_f1']:.4f} | {value['family_macro_f1']:.4f} | {value['graph_f1']:.4f} | {value['critical_error_rate']:.4f} |")
    lines += ["", "## 성공 게이트", ""]
    for name, passed in gates.items():
        lines.append(f"- [{'x' if passed else ' '}] {name}")
    lines += [
        "", "## Neo4j", "",
        f"- 노드/관계 내보내기: Claim {neo['claims']}, Concept {neo['concepts']}, Assertion {neo['assertions']}, Relationship {neo['relationships']}",
        f"- 정적 무결성 검사: {neo['validation']['status']}; provenance coverage {neo['validation']['provenance_path_coverage']:.4f}",
        f"- Competency query: {neo['cq_passed']}/{neo['cq_total']}",
        f"- 실제 Neo4j DB 로드: {extras['neo4j_runtime_status']}",
        "", "## 해석 제약", "",
        "1. 성능 수치는 인간 gold가 아닌 TRACE-LLM-Silver 대비 일치도이다.",
        "2. Challenge는 primary metric에서 제외했다.",
        "3. Neo4j runtime이 없으면 CSV·Cypher·정적 무결성까지만 검증한 결과이다.",
        "4. 최종 연구 보고 전에 blind human subset 검증이 필요하다.",
    ]
    (out / "pilot_result_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def neo4j_runtime_status() -> str:
    docker = shutil.which("docker")
    if not docker:
        return "NOT_RUN: docker executable unavailable"
    try:
        result = subprocess.run([docker, "info"], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=15, text=True)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return f"NOT_RUN: docker preflight failed ({type(exc).__name__})"
    if result.returncode != 0:
        first = next((line.strip() for line in result.stderr.splitlines() if line.strip()), "daemon unavailable")
        if "permission denied" in result.stderr.lower():
            return "NOT_RUN: Docker daemon socket permission denied"
        return f"NOT_RUN: {first[:180]}"
    return "AVAILABLE_NOT_REQUIRED: export package was statically validated"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--force", action="store_true", help="replace generated outputs but retain API cache")
    args = parser.parse_args()
    input_path = args.input.resolve(); out = args.output.resolve()
    if not input_path.exists():
        raise FileNotFoundError(input_path)
    actual_hash = hashlib.sha256(input_path.read_bytes()).hexdigest()
    locked_hash = "e8c5f174b65eccd7a50dbd2e0e216ea870a6aedfd16b3e4538d6486aea15cf1f"
    if actual_hash != locked_hash:
        raise RuntimeError(f"Input hash differs from run lock: {actual_hash}")
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is required and is never read from a project file")
    out.mkdir(parents=True, exist_ok=True)

    print("[1/7] source normalization, bundle construction, and leakage-safe sampling", flush=True)
    all_units, all_bundles, source_profile = lib.build_all_bundles(input_path)
    sample, sample_audit = lib.sample_and_split(all_units)
    bundles = sample_bundles(all_bundles, sample)
    bundles_by_id = {bundle["target"]["evidence_id"]: bundle for bundle in all_bundles}
    write_jsonl(out / "document_graph.jsonl", all_units)
    write_jsonl(out / "evidence_bundles_all.jsonl", all_bundles)
    write_csv(out / "pilot_manifest.csv", lib.manifest_rows(sample), list(lib.manifest_rows(sample)[0]))
    write_json(out / "sampling_audit.json", sample_audit)
    write_json(out / "source_profile.json", source_profile)
    duplicate_rows = [{"duplicate_cluster_id": key, "evidence_ids": [row["evidence_id"] for row in rows]} for key, rows in sorted(lib._group_by(all_units, "duplicate_cluster_id").items()) if key and len(rows) > 1]
    write_json(out / "duplicate_clusters.json", duplicate_rows)
    b2_ids = sorted(row["evidence_id"] for row in sample if row["split"] == "B2_LOCKED")
    write_json(out / "b2_lock_manifest.json", {"locked_at": "2026-07-10", "seed": lib.SEED, "evidence_ids": b2_ids, "lock_hash": sha(b2_ids), "policy": "no post-result tuning"})
    shutil.copy2(HERE / "config" / "pilot_experiment_config_v1.yaml", out / "pilot_experiment_config_v1.yaml")
    shutil.copy2(HERE / "config" / "pilot_run_lock_v1.yaml", out / "pilot_run_lock_v1.yaml")

    ledger = ApiLedger(out, api_key)
    print("[2/7] building TRACE-LLM-Silver reference (A/B, disagreement-only C, high-risk D)", flush=True)
    references, reference_summary = build_reference(ledger, sample, bundles, bundles_by_id, out)
    ref_by_id = {row["evidence_id"]: row for row in references}

    print("[3/7] CAL and B1 selective/distillation stages", flush=True)
    e2_all = [lib.heuristic_annotation(bundles_by_id[row["evidence_id"]]) for row in sample]
    write_jsonl(out / "systems" / "E2_all_predictions.jsonl", public_annotations(e2_all))
    b1a_ids = {row["evidence_id"] for row in sample if row["b1_subsplit"] == "B1a_distill_induction"}
    b1b_ids = {row["evidence_id"] for row in sample if row["b1_subsplit"] == "B1b_lf_validation"}
    e2_b1a = [row for row in e2_all if row["evidence_id"] in b1a_ids]
    e3_candidates = lib.selected_candidates(e2_b1a, bundles_by_id)
    e3_decisions = run_selective(ledger, "E3_selected_B1a", e3_candidates)
    e3_b1a = lib.apply_selective_decisions(e2_b1a, e3_decisions)
    write_jsonl(out / "systems" / "E3_B1a_predictions.jsonl", public_annotations(e3_b1a))
    write_jsonl(out / "distillation" / "b1a_selected_candidates.jsonl", [{key: value for key, value in row.items() if key != "bundle"} for row in e3_candidates])
    write_jsonl(out / "distillation" / "b1a_decisions.jsonl", e3_decisions)
    lf_candidates = lib.derive_lf_candidates(e3_decisions, bundles_by_id)
    b1b_bundles = [bundles_by_id[eid] for eid in b1b_ids]
    lf_registry = lib.validate_lf_candidates(lf_candidates, b1b_bundles, ref_by_id)
    write_json(out / "distillation" / "lf_registry.json", lf_registry)
    active_lfs = [row for row in lf_registry if row["status"] == "ACTIVE"]

    print("[4/7] locked B2 systems E0/E1/E2/E4 and flat ablation", flush=True)
    b2_rows = [row for row in sample if row["split"] == "B2_LOCKED"]
    b2_ids_set = {row["evidence_id"] for row in b2_rows}
    b2_bundles = [bundles_by_id[row["evidence_id"]] for row in b2_rows]
    e0 = run_direct_triple(ledger, b2_bundles, b2_rows, bundles_by_id)
    e1_prompt = prompt_file("system_E1_full_claim.txt", "Return one JSON object with exactly one key `annotations`; include exactly one annotation for every input evidence_id.")
    e1, e1_issues, _ = annotate_batches(ledger, phase="E1", model=MODEL_MINI, prompt=e1_prompt, bundles=b2_bundles, sample_rows=b2_rows, role="E1_FullLLM", prompt_version="system_E1_v0.1")
    e2_b2 = [row for row in e2_all if row["evidence_id"] in b2_ids_set]
    e2_distilled, lf_auto_resolved = apply_lfs(e2_b2, active_lfs, bundles_by_id)
    e4_candidates = lib.selected_candidates(e2_distilled, bundles_by_id)
    e4_decisions = run_selective(ledger, "E4_selected_B2", e4_candidates)
    e4 = lib.apply_selective_decisions(e2_distilled, e4_decisions)
    ablation_ids = {row["evidence_id"] for row in b2_rows if row["stratum"] in {"table_formula_evaluation", "procedure_decision"}}
    e2_flat = [lib.heuristic_annotation(bundles_by_id[eid], flat=True, role="E2_flat_ablation") for eid in sorted(ablation_ids)]
    write_jsonl(out / "systems" / "E0_B2_direct_triples.jsonl", [{"evidence_id": row["evidence_id"], "triples": row.get("triples") or []} for row in e0])
    e0 = public_annotations(e0)
    e1 = public_annotations(e1)
    e2_b2 = public_annotations(e2_b2)
    e4 = public_annotations(e4)
    e2_flat = public_annotations(e2_flat)
    for name, rows in [("E0_B2_evaluation_projection", e0), ("E0_B2_predictions", e0), ("E1_B2_predictions", e1), ("E2_B2_predictions", e2_b2), ("E4_B2_predictions", e4), ("E2_flat_B2_subset_predictions", e2_flat)]:
        write_jsonl(out / "systems" / f"{name}.jsonl", rows)
    write_jsonl(out / "systems" / "E1_span_validation_issues.jsonl", e1_issues)
    write_jsonl(out / "distillation" / "e4_selected_candidates.jsonl", [{key: value for key, value in row.items() if key != "bundle"} for row in e4_candidates])
    write_jsonl(out / "distillation" / "e4_decisions.jsonl", e4_decisions)

    print("[5/7] claim/graph/error metrics and bootstrap confidence intervals", flush=True)
    metrics = {}
    for name, predictions in [("E0_direct_triple", e0), ("E1_full_llm", e1), ("E2_no_llm", e2_b2), ("E4_selective_distill", e4)]:
        value = lib.evaluate_predictions(predictions, [row for row in references if row["evidence_id"] in b2_ids_set])
        value["bootstrap_95_ci"] = lib.bootstrap_claim_f1(value, 2000)
        metrics[name] = value
    flat_refs = [row for row in references if row["evidence_id"] in ablation_ids]
    flat_metric = lib.evaluate_predictions(e2_flat, flat_refs)
    flat_metric["bootstrap_95_ci"] = lib.bootstrap_claim_f1(flat_metric, 2000)
    metrics["E2_flat_ablation_subset"] = flat_metric

    print("[6/7] Neo4j audit/operational export and integrity checks", flush=True)
    neo_summary = lib.export_neo4j(out, sample, references, e4)
    runtime_status = neo4j_runtime_status()

    print("[7/7] budget ledger, success gates, and result report", flush=True)
    api_summary = ledger.save()
    tokens = system_token_summary(ledger)
    e1_tokens = max(1, tokens.get("E1", 0))
    e4_tokens = tokens.get("E4", 0)
    extras = {
        "active_lfs": len(active_lfs), "lf_candidates": len(lf_candidates), "lf_auto_resolved": lf_auto_resolved,
        "e3_selected": len(e3_candidates), "e4_selected": len(e4_candidates),
        "e4_e1_token_ratio": round(e4_tokens / e1_tokens, 4),
        "distillation_call_reduction": round(max(0.0, 1 - len(e4_candidates) / max(1, len(e3_candidates))), 4),
        "system_tokens": tokens, "neo4j_runtime_status": runtime_status,
    }
    write_reports(out, sample_audit, reference_summary, metrics, api_summary, neo_summary, extras)
    checklist = {
        "status": "COMPLETE_WITH_LIMITATIONS" if runtime_status.startswith("NOT_RUN") else "COMPLETE",
        "required_artifacts": {name: (out / name).exists() for name in ["pilot_manifest.csv", "document_graph.jsonl", "evidence_bundles_all.jsonl", "metrics_reference.json", "metrics_claim.json", "metrics_graph.json", "critical_errors.csv", "bootstrap_summary.json", "cost_ledger.csv", "pilot_result_report.md", "professor_report_TRACE_OL_pilot_20260710.md"]},
        "neo4j_exports": {name: (out / "neo4j" / name).exists() for name in ["neo4j_documents.csv", "neo4j_sections.csv", "neo4j_evidence.csv", "neo4j_claims.csv", "neo4j_concepts.csv", "neo4j_assertions.csv", "neo4j_rules.csv", "neo4j_conditions.csv", "neo4j_relationships.csv", "neo4j_constraints.cypher", "neo4j_import.cypher", "neo4j_validation_queries.cypher", "external_csv_validation.json", "external_csv_validation.md"]},
        "limitations": ["No human gold: metrics are agreement against LLM-Silver", runtime_status],
    }
    write_json(out / "checklist_status.json", checklist)
    write_json(out / "run_summary.json", {"source": source_profile, "sampling": sample_audit, "reference": reference_summary, "api": api_summary, "neo4j": neo_summary, "extras": extras, "output_dir": str(out)})
    print(f"completed: {out}", flush=True)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FATAL: {exc}", file=sys.stderr, flush=True)
        raise
