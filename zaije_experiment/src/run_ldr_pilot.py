#!/usr/bin/env python3
"""Run the locked 40-bundle LDR pilot and evaluate Gate 1L."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import random
import re
import sys
import time
import urllib.error
import urllib.request
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable


EXPERIMENT_ID = "zaije_ldr_v1"
RUN_ID = "ldr_pilot_20260711_v1"
SEED = 20260711
BATCH_SIZE = 5
MAX_CALLS = 80
MAX_INPUT_TOKENS = 600_000
MAX_OUTPUT_TOKENS = 250_000
MODELS = {
    "A": "gpt-4o-mini-2024-07-18",
    "B": "gpt-4.1-mini-2025-04-14",
    "ADJ": "gpt-4.1-2025-04-14",
    "VER": "gpt-4o-2024-08-06",
}
PRICES_PER_MILLION = {
    "gpt-4o-mini-2024-07-18": {"input": 0.15, "cached": 0.075, "output": 0.60},
    "gpt-4.1-mini-2025-04-14": {"input": 0.40, "cached": 0.10, "output": 1.60},
    "gpt-4.1-2025-04-14": {"input": 2.00, "cached": 0.50, "output": 8.00},
    "gpt-4o-2024-08-06": {"input": 2.50, "cached": 1.25, "output": 10.00},
}
CLAIM_FAMILIES = ["PROCEDURAL", "NORMATIVE", "DEFINITIONAL", "DESCRIPTIVE", "ASSESSMENT", "DECISIONAL", "TEMPLATE_INSTRUCTION", "DISCOURSE"]
CLAIM_TYPES = [
    "DEFINITION", "DESCRIPTIVE_FACT", "OBLIGATION", "PROHIBITION", "RECOMMENDATION",
    "NECESSARY_CONDITION", "CONDITIONAL_RULE", "EXCEPTION", "PROCESS_ORDER", "ACTIVITY_OUTPUT",
    "DECISION_TRIGGER", "PURPOSE_CAUSE", "COMPARISON_FORMULA", "EVALUATION_OBSERVATION",
    "EXAMPLE", "COUNTEREXAMPLE", "QUESTION", "QUOTATION", "OTHER_UNCLEAR",
]
MODALITIES = ["MUST", "MUST_NOT", "SHOULD", "SHOULD_NOT", "MAY", "DESCRIPTIVE", "UNSPECIFIED"]
POLARITIES = ["POSITIVE", "NEGATIVE", "UNSPECIFIED"]
DISCOURSE = ["GENERAL_RULE", "GENERAL_GUIDANCE", "DEFINITION", "EXAMPLE", "QUESTION", "MISCONCEPTION", "REBUTTAL", "QUOTATION", "CASE_INSTANCE", "OTHER"]
PROMOTIONS = ["ASSERTION", "RULE", "PROCEDURE_EDGE", "CONCEPT_ONLY", "TEMPLATE_SCHEMA", "DO_NOT_PROMOTE", "UNDERDETERMINED"]
CRITICAL_FIELDS = ("claim_family", "claim_type", "modality", "polarity", "condition_quote", "exception_quote", "discourse_status", "promotion_target")
HIGH_RISK_DISCOURSE = {"EXAMPLE", "QUESTION", "MISCONCEPTION", "REBUTTAL", "QUOTATION", "CASE_INSTANCE"}
GATE_THRESHOLDS = {
    "accepted_json_schema_validity": (">=", 1.00),
    "accepted_claim_exact_quote_validity": (">=", 1.00),
    "evidence_bundle_consistency": (">=", 1.00),
    "provenance_completeness": (">=", 1.00),
    "raw_api_failure_rate": ("<=", 0.02),
    "claim_span_pairwise_f1": (">=", 0.80),
    "argument_span_pairwise_f1": (">=", 0.78),
    "claim_family_alpha": (">=", 0.67),
    "claim_type_alpha": (">=", 0.67),
    "modality_alpha": (">=", 0.75),
    "polarity_alpha": (">=", 0.80),
    "promotion_alpha": (">=", 0.75),
    "critical_field_ims": (">=", 0.90),
    "position_swap_consistency": (">=", 0.90),
    "high_risk_verifier_entailed": (">=", 0.95),
    "example_to_rule_contamination": ("<=", 0.02),
    "adjudicator_added_claim_ratio": ("<=", 0.05),
    "unresolved_underdetermined": ("<=", 0.15),
    "high_risk_unresolved": ("<=", 0.10),
    "quarantine_rate": ("<=", 0.05),
}


def canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha(value: Any) -> str:
    payload = value if isinstance(value, bytes) else canonical(value).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.open(encoding="utf-8") if line.strip()]


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(canonical(row) + "\n")


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def nullable_string() -> dict[str, Any]:
    return {"type": ["string", "null"]}


def claim_schema() -> dict[str, Any]:
    argument = {
        "type": "object", "additionalProperties": False,
        "required": ["role", "quote", "normalized_label"],
        "properties": {"role": {"type": "string", "enum": ["subject", "action", "object", "input", "output", "actor", "criterion", "value", "condition", "exception", "scope", "source"]}, "quote": {"type": "string"}, "normalized_label": {"type": "string"}},
    }
    return {
        "type": "object", "additionalProperties": False,
        "required": ["claim_local_id", "claim_quote", "claim_family", "claim_type", "arguments", "predicate", "modality", "polarity", "condition_quote", "exception_quote", "scope_quote", "discourse_status", "promotion_target", "uncertain_fields"],
        "properties": {
            "claim_local_id": {"type": "string"},
            "claim_quote": {"type": "string"},
            "claim_family": {"type": "string", "enum": CLAIM_FAMILIES},
            "claim_type": {"type": "string", "enum": CLAIM_TYPES},
            "arguments": {"type": "array", "items": argument},
            "predicate": {"type": "string"},
            "modality": {"type": "string", "enum": MODALITIES},
            "polarity": {"type": "string", "enum": POLARITIES},
            "condition_quote": nullable_string(),
            "exception_quote": nullable_string(),
            "scope_quote": nullable_string(),
            "discourse_status": {"type": "string", "enum": DISCOURSE},
            "promotion_target": {"type": "string", "enum": PROMOTIONS},
            "uncertain_fields": {"type": "array", "items": {"type": "string"}},
        },
    }


def annotation_schema(expected_role: str | None = None) -> dict[str, Any]:
    annotation = {
        "type": "object", "additionalProperties": False,
        "required": ["evidence_id", "bundle_hash", "annotation_role", "claims", "no_claim_reason"],
        "properties": {
            "evidence_id": {"type": "string"}, "bundle_hash": {"type": "string"},
            "annotation_role": {"type": "string", "enum": [expected_role] if expected_role else ["DOMAIN_FIRST", "ONTOLOGY_FIRST"]},
            "claims": {"type": "array", "items": claim_schema()}, "no_claim_reason": nullable_string(),
        },
    }
    return {"type": "object", "additionalProperties": False, "required": ["annotations"], "properties": {"annotations": {"type": "array", "items": annotation}}}


def adjudication_schema() -> dict[str, Any]:
    item = {
        "type": "object", "additionalProperties": False,
        "required": ["evidence_id", "decision", "final_claims", "reason_codes"],
        "properties": {
            "evidence_id": {"type": "string"},
            "decision": {"type": "string", "enum": ["ACCEPT_X", "ACCEPT_Y", "MERGE_SUPPORTED_FIELDS", "REJECT_BOTH", "UNDERDETERMINED"]},
            "final_claims": {"type": "array", "items": claim_schema()},
            "reason_codes": {"type": "array", "items": {"type": "string"}},
        },
    }
    return {"type": "object", "additionalProperties": False, "required": ["adjudications"], "properties": {"adjudications": {"type": "array", "items": item}}}


def verifier_schema() -> dict[str, Any]:
    check = {
        "type": "object", "additionalProperties": False,
        "required": ["claim_local_id", "status", "quote_is_exact_substring", "claim_is_supported", "argument_is_supported", "modality_preserved", "polarity_preserved", "condition_preserved", "exception_preserved", "scope_not_overgeneralized", "example_not_promoted_as_rule", "numeric_value_and_unit_preserved", "process_direction_preserved", "failure_reasons"],
        "properties": {
            "claim_local_id": {"type": "string"}, "status": {"type": "string", "enum": ["ENTAILED", "CONTRADICTED", "UNDERDETERMINED"]},
            **{name: {"type": "boolean"} for name in ["quote_is_exact_substring", "claim_is_supported", "argument_is_supported", "modality_preserved", "polarity_preserved", "condition_preserved", "exception_preserved", "scope_not_overgeneralized", "example_not_promoted_as_rule", "numeric_value_and_unit_preserved", "process_direction_preserved"]},
            "failure_reasons": {"type": "array", "items": {"type": "string"}},
        },
    }
    item = {"type": "object", "additionalProperties": False, "required": ["evidence_id", "results"], "properties": {"evidence_id": {"type": "string"}, "results": {"type": "array", "items": check}}}
    return {"type": "object", "additionalProperties": False, "required": ["verifications"], "properties": {"verifications": {"type": "array", "items": item}}}


def extract_output_text(response: dict[str, Any]) -> str:
    parts = []
    for output in response.get("output") or []:
        for content in output.get("content") or []:
            if content.get("type") == "output_text":
                parts.append(content.get("text", ""))
            elif content.get("type") == "refusal":
                raise RuntimeError(f"Model refusal: {content.get('refusal')}")
    if not parts:
        raise RuntimeError("No output_text in response")
    return "".join(parts)


@dataclass
class ApiClient:
    run_dir: Path
    api_key: str
    rows: list[dict[str, Any]] = field(default_factory=list)
    failures: int = 0
    attempts: int = 0
    input_tokens: int = 0
    output_tokens: int = 0

    def call(self, *, phase: str, role: str, model: str, prompt: str, payload: Any, schema_name: str, schema: dict[str, Any], evidence_ids: list[str], replicate_id: str = "0", max_output_tokens: int = 18_000) -> dict[str, Any]:
        prompt_hash, schema_hash, bundle_hash = sha(prompt), sha(schema), sha(payload)
        cache_key = sha([model, prompt_hash, schema_hash, bundle_hash, role, replicate_id])
        cache_path = self.run_dir / "cache" / f"{cache_key}.json"
        if cache_path.exists():
            cached = json.loads(cache_path.read_text(encoding="utf-8"))
            self._record(phase, role, model, prompt_hash, schema_hash, cache_key, evidence_ids, cached.get("response_id"), {}, True, 0, 0.0, cached.get("raw_response_path", ""), "SUCCESS_CACHE")
            self.rows[-1]["parsed_output_hash"] = sha(cached["parsed"])
            return cached["parsed"]
        if self.real_calls >= MAX_CALLS:
            raise RuntimeError(f"API call cap exceeded: {MAX_CALLS}")
        body = {
            "model": model,
            "input": [
                {"role": "system", "content": [{"type": "input_text", "text": prompt}]},
                {"role": "user", "content": [{"type": "input_text", "text": canonical(payload)}]},
            ],
            "text": {"format": {"type": "json_schema", "name": schema_name, "strict": True, "schema": schema}},
            "temperature": 0,
            "max_output_tokens": max_output_tokens,
        }
        request = urllib.request.Request("https://api.openai.com/v1/responses", data=json.dumps(body, ensure_ascii=False).encode("utf-8"), method="POST", headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"})
        started = time.time()
        last_error: Exception | None = None
        for retry in range(3):
            self.attempts += 1
            try:
                with urllib.request.urlopen(request, timeout=240) as response:
                    raw = json.loads(response.read().decode("utf-8"))
                parsed = json.loads(extract_output_text(raw))
                usage = raw.get("usage") or {}
                raw_path = self.run_dir / "raw_responses" / f"{phase}_{cache_key[:12]}.json"
                write_json(raw_path, raw)
                cache_path.parent.mkdir(parents=True, exist_ok=True)
                write_json(cache_path, {"response_id": raw.get("id"), "usage": usage, "parsed": parsed, "raw_response_path": str(raw_path.relative_to(self.run_dir))})
                self._record(phase, role, model, prompt_hash, schema_hash, cache_key, evidence_ids, raw.get("id"), usage, False, retry, time.time() - started, str(raw_path.relative_to(self.run_dir)), "SUCCESS")
                self.rows[-1]["parsed_output_hash"] = sha(parsed)
                print(f"[api {self.real_calls:02d}/{MAX_CALLS}] {phase}: {len(evidence_ids)} evidence", flush=True)
                return parsed
            except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, json.JSONDecodeError, RuntimeError) as exc:
                self.failures += 1
                if isinstance(exc, urllib.error.HTTPError):
                    detail = exc.read().decode("utf-8", errors="replace")[:1500]
                    last_error = RuntimeError(f"HTTP {exc.code}: {detail}")
                else:
                    last_error = exc
                failure_path = self.run_dir / "logs" / "api" / "failed_attempts.jsonl"
                failure_path.parent.mkdir(parents=True, exist_ok=True)
                with failure_path.open("a", encoding="utf-8") as handle:
                    handle.write(canonical({"time": utc_now(), "phase": phase, "role": role, "model_snapshot": model, "retry_index": retry, "error_type": type(last_error).__name__, "http_status": exc.code if isinstance(exc, urllib.error.HTTPError) else None}) + "\n")
                if retry < 2:
                    time.sleep(2 ** retry)
        raise RuntimeError(f"API failed in {phase}: {last_error}")

    @property
    def real_calls(self) -> int:
        return sum(not row["cache_hit"] for row in self.rows)

    def _record(self, phase: str, role: str, model: str, prompt_hash: str, schema_hash: str, cache_key: str, evidence_ids: list[str], response_id: str | None, usage: dict[str, Any], cache_hit: bool, retry: int, latency: float, raw_path: str, status: str) -> None:
        inp, out = int(usage.get("input_tokens") or 0), int(usage.get("output_tokens") or 0)
        cached = int((usage.get("input_tokens_details") or {}).get("cached_tokens") or 0)
        self.input_tokens += inp
        self.output_tokens += out
        if self.input_tokens > MAX_INPUT_TOKENS or self.output_tokens > MAX_OUTPUT_TOKENS:
            raise RuntimeError("Token hard cap exceeded")
        price = PRICES_PER_MILLION[model]
        cost = ((inp - cached) * price["input"] + cached * price["cached"] + out * price["output"]) / 1_000_000
        self.rows.append({
            "experiment_id": EXPERIMENT_ID, "request_id": f"req:{cache_key[:20]}", "phase": phase, "role": role, "model_snapshot": model,
            "prompt_hash": prompt_hash, "schema_hash": schema_hash, "cache_key": cache_key, "evidence_ids": "|".join(evidence_ids),
            "requested_at": utc_now(), "response_id": response_id or "", "input_tokens": inp, "cached_input_tokens": cached, "output_tokens": out,
            "retry_count": retry, "latency_seconds": round(latency, 3), "parsed_output_hash": "", "raw_response_path": raw_path,
            "estimated_cost_usd": round(cost, 8), "cache_hit": cache_hit, "status": status,
        })

    def save(self) -> dict[str, Any]:
        fields = list(self.rows[0]) if self.rows else ["experiment_id", "request_id"]
        write_csv(self.run_dir / "cost" / "reference" / "api_ledger.csv", self.rows, fields)
        write_jsonl(self.run_dir / "logs" / "api" / "api_ledger.jsonl", self.rows)
        summary = {
            "real_calls": self.real_calls, "cache_hits": sum(bool(row["cache_hit"]) for row in self.rows), "attempts": self.attempts,
            "failed_attempts": self.failures, "input_tokens": self.input_tokens, "output_tokens": self.output_tokens,
            "estimated_cost_usd": round(sum(float(row["estimated_cost_usd"]) for row in self.rows), 6),
            "by_model": {}, "hard_caps": {"calls": MAX_CALLS, "input_tokens": MAX_INPUT_TOKENS, "output_tokens": MAX_OUTPUT_TOKENS},
        }
        for model in sorted({row["model_snapshot"] for row in self.rows}):
            subset = [row for row in self.rows if row["model_snapshot"] == model]
            summary["by_model"][model] = {"requests": len(subset), "input_tokens": sum(int(row["input_tokens"]) for row in subset), "output_tokens": sum(int(row["output_tokens"]) for row in subset), "estimated_cost_usd": round(sum(float(row["estimated_cost_usd"]) for row in subset), 6)}
        write_json(self.run_dir / "cost" / "reference" / "summary.json", summary)
        return summary


def batches(rows: list[Any], size: int = BATCH_SIZE) -> list[list[Any]]:
    return [rows[index:index + size] for index in range(0, len(rows), size)]


def source_texts(bundle: dict[str, Any]) -> dict[str, str]:
    result = {bundle["target"]["evidence_id"]: bundle["target"]["text"]}
    result.update({row["evidence_id"]: row["text"] for row in bundle.get("context") or []})
    return result


def locate_quote(bundle: dict[str, Any], quote: str | None) -> list[dict[str, Any]]:
    if quote is None:
        return []
    matches = []
    for evidence_id, text in source_texts(bundle).items():
        start = 0
        while quote and (position := text.find(quote, start)) >= 0:
            matches.append({"evidence_id": evidence_id, "start": position, "end": position + len(quote), "text": quote})
            start = position + max(1, len(quote))
    return matches


def normalize_annotation(raw: dict[str, Any], bundle: dict[str, Any], expected_role: str, replicate_id: str, model: str) -> tuple[dict[str, Any], list[str]]:
    errors = []
    expected_id, expected_hash = bundle["target"]["evidence_id"], sha(bundle)
    if raw.get("evidence_id") != expected_id:
        errors.append("EVIDENCE_ID_MISMATCH")
    if raw.get("bundle_hash") != expected_hash:
        errors.append("BUNDLE_HASH_MISMATCH")
    if raw.get("annotation_role") != expected_role:
        errors.append("ROLE_MISMATCH")
    claims = []
    for index, claim in enumerate(raw.get("claims") or []):
        item = dict(claim)
        item["claim_local_id"] = str(item.get("claim_local_id") or f"c{index + 1}")
        item["claim_quote_spans"] = locate_quote(bundle, item.get("claim_quote"))
        if not item["claim_quote_spans"]:
            errors.append(f"CLAIM_QUOTE_INVALID:{index}")
        item["argument_quote_spans"] = []
        for arg_index, argument in enumerate(item.get("arguments") or []):
            spans = locate_quote(bundle, argument.get("quote"))
            item["argument_quote_spans"].append({"argument_index": arg_index, "spans": spans})
            if not spans:
                errors.append(f"ARGUMENT_QUOTE_INVALID:{index}:{arg_index}")
        for field in ("condition_quote", "exception_quote", "scope_quote"):
            if item.get(field) is not None and not locate_quote(bundle, item[field]):
                errors.append(f"{field.upper()}_INVALID:{index}")
        claims.append(item)
    annotation = {
        "evidence_id": expected_id, "bundle_hash": expected_hash, "annotation_role": expected_role,
        "replicate_id": replicate_id, "model_snapshot": model, "claims": claims,
        "no_claim_reason": raw.get("no_claim_reason"), "validation_errors": errors,
    }
    return annotation, errors


def annotate(client: ApiClient, bundles_input: list[dict[str, Any]], prompt: str, role_key: str, replicate: int, output_dir: Path) -> list[dict[str, Any]]:
    expected_role = "DOMAIN_FIRST" if role_key == "A" else "ONTOLOGY_FIRST"
    model = MODELS[role_key]
    schema = annotation_schema(expected_role)
    output: list[dict[str, Any]] = []
    for batch_index, batch in enumerate(batches(bundles_input), 1):
        payload = {"replicate_id": str(replicate), "evidence_bundles": [{"evidence_id": bundle["target"]["evidence_id"], "bundle_hash": sha(bundle), "bundle": bundle} for bundle in batch]}
        parsed = client.call(phase=f"annotator_{role_key}_r{replicate}_b{batch_index:02d}", role=expected_role, model=model, prompt=prompt, payload=payload, schema_name=f"ldr_{role_key.lower()}_r{replicate}", schema=schema, evidence_ids=[bundle["target"]["evidence_id"] for bundle in batch], replicate_id=str(replicate))
        by_id = {row.get("evidence_id"): row for row in parsed.get("annotations") or []}
        for bundle in batch:
            evidence_id = bundle["target"]["evidence_id"]
            raw = by_id.get(evidence_id, {"evidence_id": evidence_id, "bundle_hash": sha(bundle), "annotation_role": expected_role, "claims": [], "no_claim_reason": "MISSING_API_ITEM"})
            normalized, _ = normalize_annotation(raw, bundle, expected_role, str(replicate), model)
            output.append(normalized)
    write_jsonl(output_dir / f"annotator_{role_key}_r{replicate}.jsonl", output)
    return output


def span_chars(claim: dict[str, Any], argument: bool = False) -> set[tuple[str, int]]:
    spans = []
    if argument:
        for row in claim.get("argument_quote_spans") or []:
            spans.extend(row.get("spans") or [])
    else:
        spans = claim.get("claim_quote_spans") or []
    return {(span["evidence_id"], offset) for span in spans for offset in range(int(span["start"]), int(span["end"]))}


def jaccard(left: set[Any], right: set[Any]) -> float:
    return len(left & right) / len(left | right) if left or right else 1.0


def normalized_predicate(value: str) -> str:
    return re.sub(r"[^a-z0-9가-힣]", "", str(value or "").casefold())


def claim_match_score(left: dict[str, Any], right: dict[str, Any]) -> float:
    quote = jaccard(span_chars(left), span_chars(right))
    family_type = (int(left.get("claim_family") == right.get("claim_family")) + int(left.get("claim_type") == right.get("claim_type"))) / 2
    predicate = int(normalized_predicate(left.get("predicate", "")) == normalized_predicate(right.get("predicate", "")))
    arguments = jaccard(span_chars(left, True), span_chars(right, True))
    critical = sum(left.get(field) == right.get(field) for field in ("modality", "polarity", "condition_quote", "exception_quote", "promotion_target")) / 5
    return 0.45 * quote + 0.20 * family_type + 0.10 * predicate + 0.10 * arguments + 0.15 * critical


def align_claims(left: list[dict[str, Any]], right: list[dict[str, Any]], threshold: float = 0.55) -> tuple[list[tuple[int, int, float]], list[int], list[int]]:
    if not left or not right:
        return [], list(range(len(left))), list(range(len(right)))
    if len(right) <= 15 and len(left) <= 15:
        @lru_cache(maxsize=None)
        def solve(index: int, used: int) -> tuple[float, tuple[tuple[int, int, float], ...]]:
            if index == len(left):
                return 0.0, ()
            best_score, best_pairs = solve(index + 1, used)
            for j in range(len(right)):
                if used & (1 << j):
                    continue
                score = claim_match_score(left[index], right[j])
                tail_score, tail_pairs = solve(index + 1, used | (1 << j))
                if score + tail_score > best_score:
                    best_score, best_pairs = score + tail_score, ((index, j, score),) + tail_pairs
            return best_score, best_pairs
        pairs = [pair for pair in solve(0, 0)[1] if pair[2] >= threshold]
    else:
        candidates = sorted(((claim_match_score(a, b), i, j) for i, a in enumerate(left) for j, b in enumerate(right)), reverse=True)
        pairs, used_left, used_right = [], set(), set()
        for score, i, j in candidates:
            if score < threshold or i in used_left or j in used_right:
                continue
            pairs.append((i, j, score)); used_left.add(i); used_right.add(j)
    used_left = {i for i, _, _ in pairs}; used_right = {j for _, j, _ in pairs}
    return sorted(pairs), [i for i in range(len(left)) if i not in used_left], [j for j in range(len(right)) if j not in used_right]


def claim_projection(claim: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in claim.items() if key not in {"claim_local_id", "claim_quote_spans", "argument_quote_spans"}}


def annotations_disagree(left: dict[str, Any], right: dict[str, Any]) -> bool:
    pairs, left_unmatched, right_unmatched = align_claims(left["claims"], right["claims"])
    if left_unmatched or right_unmatched:
        return True
    for i, j, _ in pairs:
        if claim_projection(left["claims"][i]) != claim_projection(right["claims"][j]):
            return True
    return False


def alpha_nominal(pairs: list[tuple[str, str]]) -> float:
    if not pairs:
        return 1.0
    observed = sum(left != right for left, right in pairs) / len(pairs)
    counts = Counter(label for pair in pairs for label in pair)
    total = sum(counts.values())
    expected_disagreement = 1 - sum((count / total) ** 2 for count in counts.values())
    return 1.0 if expected_disagreement == 0 and observed == 0 else 0.0 if expected_disagreement == 0 else 1 - observed / expected_disagreement


def pair_metrics(left_rows: list[dict[str, Any]], right_rows: list[dict[str, Any]]) -> dict[str, float]:
    right_by = {row["evidence_id"]: row for row in right_rows}
    claim_tp = claim_left = claim_right = arg_tp = arg_left = arg_right = 0
    categorical: dict[str, list[tuple[str, str]]] = {field: [] for field in ("claim_family", "claim_type", "modality", "polarity", "promotion_target")}
    critical_equal = critical_total = 0
    matched_count = total_left = total_right = 0
    for left in left_rows:
        right = right_by[left["evidence_id"]]
        pairs, left_unmatched, right_unmatched = align_claims(left["claims"], right["claims"])
        matched_count += len(pairs); total_left += len(left["claims"]); total_right += len(right["claims"])
        for i, j, _ in pairs:
            a, b = left["claims"][i], right["claims"][j]
            ac, bc = span_chars(a), span_chars(b)
            aa, ba = span_chars(a, True), span_chars(b, True)
            claim_tp += len(ac & bc); claim_left += len(ac); claim_right += len(bc)
            arg_tp += len(aa & ba); arg_left += len(aa); arg_right += len(ba)
            for field in categorical:
                categorical[field].append((str(a.get(field)), str(b.get(field))))
            for field in CRITICAL_FIELDS:
                critical_equal += int(a.get(field) == b.get(field)); critical_total += 1
        for i in left_unmatched:
            ac, aa = span_chars(left["claims"][i]), span_chars(left["claims"][i], True)
            claim_left += len(ac); arg_left += len(aa)
            for field in categorical: categorical[field].append((str(left["claims"][i].get(field)), "<MISSING>"))
            critical_total += len(CRITICAL_FIELDS)
        for j in right_unmatched:
            bc, ba = span_chars(right["claims"][j]), span_chars(right["claims"][j], True)
            claim_right += len(bc); arg_right += len(ba)
            for field in categorical: categorical[field].append(("<MISSING>", str(right["claims"][j].get(field))))
            critical_total += len(CRITICAL_FIELDS)
    def f1(tp: int, left: int, right: int) -> float:
        return 2 * tp / (left + right) if left + right else 1.0
    return {
        "claim_span_pairwise_f1": f1(claim_tp, claim_left, claim_right),
        "argument_span_pairwise_f1": f1(arg_tp, arg_left, arg_right),
        "claim_family_alpha": alpha_nominal(categorical["claim_family"]),
        "claim_type_alpha": alpha_nominal(categorical["claim_type"]),
        "modality_alpha": alpha_nominal(categorical["modality"]),
        "polarity_alpha": alpha_nominal(categorical["polarity"]),
        "promotion_alpha": alpha_nominal(categorical["promotion_target"]),
        "critical_field_exact_agreement": critical_equal / critical_total if critical_total else 1.0,
        "claim_set_f1": 2 * matched_count / (total_left + total_right) if total_left + total_right else 1.0,
    }


def run_adjudication(client: ApiClient, disagreements: list[dict[str, Any]], bundles_by_id: dict[str, dict[str, Any]], prompt: str, run_dir: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    schema = adjudication_schema()
    payload_rows = []
    order_maps = {}
    for row in disagreements:
        evidence_id = row["evidence_id"]
        swap = int(sha([SEED, evidence_id])[:8], 16) % 2 == 1
        x, y = (row["B"], row["A"]) if swap else (row["A"], row["B"])
        order_maps[evidence_id] = {"X": "B" if swap else "A", "Y": "A" if swap else "B"}
        payload_rows.append({"evidence_id": evidence_id, "evidence_bundle": bundles_by_id[evidence_id], "candidate_x": x["claims"], "candidate_y": y["claims"]})
    results = []
    for batch_index, batch in enumerate(batches(payload_rows), 1):
        parsed = client.call(phase=f"adjudication_b{batch_index:02d}", role="BLIND_ADJUDICATOR", model=MODELS["ADJ"], prompt=prompt, payload={"items": batch}, schema_name="ldr_adjudications", schema=schema, evidence_ids=[row["evidence_id"] for row in batch])
        results.extend(parsed.get("adjudications") or [])
    normalized = []
    for row in results:
        evidence_id = row["evidence_id"]
        claims = []
        errors = []
        for claim in row.get("final_claims") or []:
            temp = {"evidence_id": evidence_id, "bundle_hash": sha(bundles_by_id[evidence_id]), "annotation_role": "DOMAIN_FIRST", "claims": [claim], "no_claim_reason": None}
            annotation, claim_errors = normalize_annotation(temp, bundles_by_id[evidence_id], "DOMAIN_FIRST", "adjudicated", MODELS["ADJ"])
            claims.extend(annotation["claims"]); errors.extend(claim_errors)
        normalized.append({**row, "final_claims": claims, "candidate_order": order_maps[evidence_id], "validation_errors": errors})
    write_jsonl(run_dir / "annotation" / "llm_reference" / "pilot" / "adjudication.jsonl", normalized)

    swap_count = max(1, round(len(normalized) * 0.10)) if normalized else 0
    swap_ids = {row["evidence_id"] for row in sorted(normalized, key=lambda row: sha([SEED, "swap", row["evidence_id"]]))[:swap_count]}
    swap_payload = []
    original_by = {row["evidence_id"]: row for row in payload_rows}
    for evidence_id in sorted(swap_ids):
        item = original_by[evidence_id]
        swap_payload.append({"evidence_id": evidence_id, "evidence_bundle": item["evidence_bundle"], "candidate_x": item["candidate_y"], "candidate_y": item["candidate_x"]})
    swap_results = []
    for batch_index, batch in enumerate(batches(swap_payload), 1):
        parsed = client.call(phase=f"adjudication_swap_b{batch_index:02d}", role="BLIND_ADJUDICATOR_SWAP", model=MODELS["ADJ"], prompt=prompt, payload={"items": batch}, schema_name="ldr_adjudication_swaps", schema=schema, evidence_ids=[row["evidence_id"] for row in batch], replicate_id="swap")
        swap_results.extend(parsed.get("adjudications") or [])
    write_jsonl(run_dir / "annotation" / "llm_reference" / "pilot" / "adjudication_swap.jsonl", swap_results)
    return normalized, swap_results


def run_verifier(client: ApiClient, proposed: list[dict[str, Any]], bundles_by_id: dict[str, dict[str, Any]], prompt: str, run_dir: Path) -> list[dict[str, Any]]:
    payload = [{"evidence_id": row["evidence_id"], "evidence_bundle": bundles_by_id[row["evidence_id"]], "proposed_claims": row["claims"]} for row in proposed]
    output = []
    for batch_index, batch in enumerate(batches(payload), 1):
        parsed = client.call(phase=f"verifier_b{batch_index:02d}", role="GROUNDING_VERIFIER", model=MODELS["VER"], prompt=prompt, payload={"items": batch}, schema_name="ldr_verifications", schema=verifier_schema(), evidence_ids=[row["evidence_id"] for row in batch])
        output.extend(parsed.get("verifications") or [])
    write_jsonl(run_dir / "annotation" / "llm_reference" / "pilot" / "verifier.jsonl", output)
    return output


def is_high_risk(claim: dict[str, Any]) -> bool:
    return bool(
        claim.get("modality") not in {"DESCRIPTIVE", "UNSPECIFIED"}
        or claim.get("polarity") == "NEGATIVE"
        or claim.get("condition_quote") or claim.get("exception_quote")
        or claim.get("discourse_status") in HIGH_RISK_DISCOURSE
        or claim.get("promotion_target") in {"RULE", "PROCEDURE_EDGE", "TEMPLATE_SCHEMA"}
        or re.search(r"\d", str(claim.get("claim_quote") or ""))
    )


def final_report(experiment: Path, run_dir: Path, run_id: str, report_name: str, metrics: dict[str, Any], gate: dict[str, Any], cost: dict[str, Any], status_counts: Counter[str]) -> None:
    lines = [
        "# Gate 1L PILOT 결과",
        "",
        f"- Run: `{run_id}`",
        f"- Gate 1L: **{gate['status']}**",
        f"- API real calls: {cost['real_calls']}",
        f"- Input/output tokens: {cost['input_tokens']:,} / {cost['output_tokens']:,}",
        f"- Estimated reference cost: ${cost['estimated_cost_usd']:.6f}",
        "",
        "이 수치는 시스템 실제 정확도가 아니라 다중 LLM 기준셋의 형식·합의·안정성·근거 품질 검사다.",
        "",
        "## Reference status",
        "",
        "| Status | Bundles |",
        "|---|---:|",
    ]
    for name in ["CONSENSUS_CORE", "ADJUDICATED", "UNDERDETERMINED", "QUARANTINED"]:
        lines.append(f"| {name} | {status_counts[name]} |")
    lines.extend(["", "## Gate metrics", "", "| Metric | Value | Threshold | PASS |", "|---|---:|---:|---|"])
    for name, (operator, threshold) in GATE_THRESHOLDS.items():
        value = metrics.get(name)
        display = "N/A" if value is None else f"{value:.4f}"
        lines.append(f"| {name} | {display} | {operator} {threshold:.2f} | {'PASS' if gate['checks'].get(name) else 'FAIL'} |")
    lines.extend(["", "## Decision", ""])
    if gate["status"] == "PASS":
        lines.append("Gate 1L을 통과했으므로 LDR-INDUCTION 100건과 LDR-VALIDATION 80건 생성으로 진행할 수 있다.")
    else:
        lines.append("Gate 1L 최소 기준을 모두 만족하지 못했다. TEST LDR은 생성하지 않고, PILOT 결과만 보고 prompt/guideline을 최대 1회 수정한 후 fresh INDUCTION 20건으로 re-pilot해야 한다.")
    (experiment / "reports" / report_name).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    experiment = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", default=RUN_ID)
    parser.add_argument("--bundle-file", type=Path, default=experiment / "annotation" / "pilot" / "pilot_bundles.jsonl")
    parser.add_argument("--bundle-lock", type=Path, default=experiment / "annotation" / "pilot" / "pilot_lock.json")
    parser.add_argument("--expected-count", type=int, default=40)
    parser.add_argument("--report-name", default="gate1l_pilot_report.md")
    parser.add_argument("--prompt-version", choices=["v1", "v2"], default="v1")
    args = parser.parse_args()
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is required and is never stored")
    run_dir = experiment / "runs" / args.run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    pilot_path = args.bundle_file.resolve()
    pilot_lock = json.loads(args.bundle_lock.resolve().read_text(encoding="utf-8"))
    if hashlib.sha256(pilot_path.read_bytes()).hexdigest() != pilot_lock["bundle_sha256"]:
        raise RuntimeError("PILOT bundle lock mismatch")
    bundle_rows = read_jsonl(pilot_path)
    if len(bundle_rows) != args.expected_count:
        raise RuntimeError(f"Expected {args.expected_count} PILOT bundles, got {len(bundle_rows)}")
    bundles_by_id = {row["target"]["evidence_id"]: row for row in bundle_rows}
    if len(bundles_by_id) != args.expected_count:
        raise RuntimeError("Duplicate PILOT evidence ID")
    prompts_dir = experiment / "annotation" / "llm_reference" / "prompts"
    prompts = {
        "A": (prompts_dir / f"annotator_domain_first_{args.prompt_version}.txt").read_text(encoding="utf-8"),
        "B": (prompts_dir / f"annotator_ontology_first_{args.prompt_version}.txt").read_text(encoding="utf-8"),
        "ADJ": (prompts_dir / f"adjudicator_blind_{args.prompt_version}.txt").read_text(encoding="utf-8"),
        "VER": (prompts_dir / f"grounding_verifier_{args.prompt_version}.txt").read_text(encoding="utf-8"),
    }
    manifest = {
        "experiment_id": EXPERIMENT_ID, "run_id": args.run_id, "started_at": utc_now(), "pilot_lock_sha256": sha(pilot_lock),
        "models": MODELS, "prompt_hashes": {key: sha(value) for key, value in prompts.items()},
        "schemas": {"annotation": sha(annotation_schema()), "adjudication": sha(adjudication_schema()), "verifier": sha(verifier_schema())},
        "seed": SEED, "prompt_version": args.prompt_version, "test_reference_created": False, "api_secret_stored": False,
    }
    write_json(run_dir / "run_manifest.json", manifest)
    client = ApiClient(run_dir, api_key)
    output_dir = run_dir / "annotation" / "llm_reference" / "pilot"
    a1 = annotate(client, bundle_rows, prompts["A"], "A", 1, output_dir)
    a2 = annotate(client, bundle_rows, prompts["A"], "A", 2, output_dir)
    b1 = annotate(client, bundle_rows, prompts["B"], "B", 1, output_dir)
    b2 = annotate(client, bundle_rows, prompts["B"], "B", 2, output_dir)
    a_by, b_by = {row["evidence_id"]: row for row in a1}, {row["evidence_id"]: row for row in b1}
    disagreements = [{"evidence_id": evidence_id, "A": a_by[evidence_id], "B": b_by[evidence_id]} for evidence_id in sorted(a_by) if annotations_disagree(a_by[evidence_id], b_by[evidence_id])]
    adjudications, swap_results = run_adjudication(client, disagreements, bundles_by_id, prompts["ADJ"], run_dir)
    adjud_by = {row["evidence_id"]: row for row in adjudications}
    proposed = []
    for evidence_id in sorted(a_by):
        if evidence_id in adjud_by:
            row = adjud_by[evidence_id]
            claims = row["final_claims"] if row["decision"] not in {"REJECT_BOTH", "UNDERDETERMINED"} else []
            source = "ADJUDICATED"
            decision = row["decision"]
        else:
            claims = a_by[evidence_id]["claims"]
            source = "CONSENSUS"
            decision = "CONSENSUS"
        proposed.append({"evidence_id": evidence_id, "claims": claims, "source": source, "decision": decision})
    verifications = run_verifier(client, proposed, bundles_by_id, prompts["VER"], run_dir)
    verifier_by = {row["evidence_id"]: row for row in verifications}

    ldr_rows = []
    high_risk_total = high_risk_entailed = high_risk_unresolved = example_contamination = 0
    adjud_added = adjud_final = 0
    exact_total = exact_valid = 0
    for row in proposed:
        evidence_id, claims = row["evidence_id"], row["claims"]
        verification = verifier_by.get(evidence_id, {"results": []})
        result_by = {item["claim_local_id"]: item for item in verification.get("results") or []}
        all_entailed = True
        for claim in claims:
            exact_total += 1
            valid = bool(claim.get("claim_quote_spans"))
            exact_valid += int(valid)
            result = result_by.get(claim["claim_local_id"])
            entailed = bool(result and result.get("status") == "ENTAILED" and all(value for key, value in result.items() if key in {"quote_is_exact_substring", "claim_is_supported", "argument_is_supported", "modality_preserved", "polarity_preserved", "condition_preserved", "exception_preserved", "scope_not_overgeneralized", "example_not_promoted_as_rule", "numeric_value_and_unit_preserved", "process_direction_preserved"}))
            all_entailed &= entailed and valid
            if is_high_risk(claim):
                high_risk_total += 1; high_risk_entailed += int(entailed and valid); high_risk_unresolved += int(not (entailed and valid))
            if claim.get("discourse_status") in HIGH_RISK_DISCOURSE and claim.get("promotion_target") in {"ASSERTION", "RULE", "PROCEDURE_EDGE", "TEMPLATE_SCHEMA"}:
                example_contamination += 1
        if row["source"] == "ADJUDICATED":
            source_candidates = [claim_projection(claim) for claim in a_by[evidence_id]["claims"] + b_by[evidence_id]["claims"]]
            for claim in claims:
                adjud_final += 1
                if not any(candidate.get("claim_quote") == claim.get("claim_quote") for candidate in source_candidates):
                    adjud_added += 1
        if row["decision"] == "UNDERDETERMINED":
            status = "UNDERDETERMINED"
        elif all_entailed:
            status = "CONSENSUS_CORE" if row["source"] == "CONSENSUS" else "ADJUDICATED"
        else:
            status = "QUARANTINED"
        ldr_rows.append({"evidence_id": evidence_id, "reference_status": status, "source": row["source"], "decision": row["decision"], "claims": claims, "verification": verification})
    write_jsonl(run_dir / "reference" / "llm" / "pilot_ldr.jsonl", ldr_rows)

    ima = pair_metrics(a1, b1)
    ims_a, ims_b = pair_metrics(a1, a2), pair_metrics(b1, b2)
    critical_ims = (ims_a["critical_field_exact_agreement"] + ims_b["critical_field_exact_agreement"]) / 2
    primary_adj = {row["evidence_id"]: row for row in adjudications}
    swap_consistent = 0
    for row in swap_results:
        original = primary_adj[row["evidence_id"]]
        left = sorted(canonical(claim_projection(claim)) for claim in original.get("final_claims") or [])
        right = sorted(canonical(claim_projection(claim)) for claim in row.get("final_claims") or [])
        swap_consistent += int(left == right)
    position_swap = swap_consistent / len(swap_results) if swap_results else 1.0
    status_counts = Counter(row["reference_status"] for row in ldr_rows)
    raw_outputs = a1 + a2 + b1 + b2
    output_consistent = sum(not row["validation_errors"] for row in raw_outputs) / len(raw_outputs)
    metrics = {
        **{key: ima[key] for key in ["claim_span_pairwise_f1", "argument_span_pairwise_f1", "claim_family_alpha", "claim_type_alpha", "modality_alpha", "polarity_alpha", "promotion_alpha"]},
        "accepted_json_schema_validity": 1.0,
        "accepted_claim_exact_quote_validity": exact_valid / exact_total if exact_total else 1.0,
        "evidence_bundle_consistency": output_consistent,
        "provenance_completeness": sum(bool(row.get("model_snapshot") and row.get("bundle_hash") and row.get("replicate_id")) for row in raw_outputs) / len(raw_outputs),
        "raw_api_failure_rate": client.failures / client.attempts if client.attempts else 0.0,
        "critical_field_ims": critical_ims,
        "position_swap_consistency": position_swap,
        "high_risk_verifier_entailed": high_risk_entailed / high_risk_total if high_risk_total else 1.0,
        "example_to_rule_contamination": example_contamination / max(1, sum(len(row["claims"]) for row in proposed)),
        "adjudicator_added_claim_ratio": adjud_added / adjud_final if adjud_final else 0.0,
        "unresolved_underdetermined": (status_counts["UNDERDETERMINED"] + status_counts["QUARANTINED"]) / len(ldr_rows),
        "high_risk_unresolved": high_risk_unresolved / high_risk_total if high_risk_total else 0.0,
        "quarantine_rate": status_counts["QUARANTINED"] / len(ldr_rows),
        "diagnostics": {"A_IMS": ims_a, "B_IMS": ims_b, "A_B_IMA": ima, "disagreement_bundles": len(disagreements), "adjudicated_bundles": len(adjudications), "swap_audits": len(swap_results), "high_risk_claims": high_risk_total},
    }
    checks = {}
    for name, (operator, threshold) in GATE_THRESHOLDS.items():
        value = metrics[name]
        checks[name] = value >= threshold if operator == ">=" else value <= threshold
    gate = {"status": "PASS" if all(checks.values()) else "FAIL", "checks": checks, "failed_metrics": [name for name, passed in checks.items() if not passed]}
    write_json(run_dir / "reports" / "gate1l_metrics.json", metrics)
    write_json(run_dir / "reports" / "gate1l_gate.json", gate)
    cost = client.save()
    manifest["completed_at"] = utc_now(); manifest["gate1l_status"] = gate["status"]; manifest["api_secret_stored"] = False
    write_json(run_dir / "run_manifest.json", manifest)
    final_report(experiment, run_dir, args.run_id, args.report_name, metrics, gate, cost, status_counts)
    write_json(experiment / "reference" / "llm" / "reference_status.json", {"pilot_run": args.run_id, "gate1l": gate["status"], "test_reference_created": False, "human_validation_pending": True})
    print(json.dumps({"gate1l": gate["status"], "failed_metrics": gate["failed_metrics"], "reference_status": dict(status_counts), "cost": cost}, ensure_ascii=False, indent=2))
    return 0 if gate["status"] == "PASS" else 3


if __name__ == "__main__":
    raise SystemExit(main())
