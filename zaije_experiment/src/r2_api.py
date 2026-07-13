#!/usr/bin/env python3
"""Minimal Responses API client with immutable raw-response and usage ledgers."""

from __future__ import annotations

import csv
import hashlib
import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PRICES = {
    "gpt-4o-mini-2024-07-18": {"input": 0.15, "cached": 0.075, "output": 0.60},
    "gpt-4.1-mini-2025-04-14": {"input": 0.40, "cached": 0.10, "output": 1.60},
    "gpt-4o-2024-08-06": {"input": 2.50, "cached": 1.25, "output": 10.00},
    "gpt-4.1-2025-04-14": {"input": 2.00, "cached": 0.50, "output": 8.00},
    "gpt-4.1-nano-2025-04-14": {"input": 0.10, "cached": 0.025, "output": 0.40},
}


def canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha(value: Any) -> str:
    payload = value if isinstance(value, bytes) else canonical(value).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def extract_text(response: dict[str, Any]) -> str:
    parts = []
    for output in response.get("output") or []:
        for content in output.get("content") or []:
            if content.get("type") == "output_text":
                parts.append(content["text"])
            elif content.get("type") == "refusal":
                raise RuntimeError("REFUSAL")
    if not parts:
        raise RuntimeError("NO_OUTPUT_TEXT")
    return "".join(parts)


@dataclass
class Client:
    run_dir: Path
    api_key: str
    experiment_id: str
    category: str
    max_calls: int = 300
    max_input_tokens: int = 2_000_000
    max_output_tokens: int = 500_000
    ledger: list[dict[str, Any]] = field(default_factory=list)
    attempts: int = 0
    failures: int = 0

    def call(self, *, phase: str, model: str, prompt: str, payload: Any, schema_name: str, schema: dict[str, Any], item_ids: list[str], repeat_id: str = "1", max_output_tokens: int = 16000) -> dict[str, Any]:
        prompt_hash, schema_hash, payload_hash = sha(prompt), sha(schema), sha(payload)
        cache_key = sha([model, prompt_hash, schema_hash, payload_hash, phase, repeat_id])
        cache_path = self.run_dir / "cache" / f"{cache_key}.json"
        if cache_path.exists():
            cached = json.loads(cache_path.read_text(encoding="utf-8"))
            self._record(phase, model, prompt_hash, schema_hash, cache_key, item_ids, cached.get("response_id", ""), {}, True, 0, 0.0, cached["raw_response_path"], sha(cached["parsed"]), "SUCCESS_CACHE")
            return cached["parsed"]
        if self.real_calls >= self.max_calls:
            raise RuntimeError("API_CALL_CAP")
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
                parsed = json.loads(extract_text(raw))
                usage = raw.get("usage") or {}
                raw_path = self.run_dir / "raw_responses" / f"{phase}_{cache_key[:12]}.json"
                write_json(raw_path, raw)
                cache_path.parent.mkdir(parents=True, exist_ok=True)
                write_json(cache_path, {"response_id": raw.get("id"), "usage": usage, "parsed": parsed, "raw_response_path": str(raw_path.relative_to(self.run_dir))})
                self._record(phase, model, prompt_hash, schema_hash, cache_key, item_ids, raw.get("id", ""), usage, False, retry, time.time() - started, str(raw_path.relative_to(self.run_dir)), sha(parsed), "SUCCESS")
                print(f"[api {self.real_calls:03d}/{self.max_calls}] {phase}: {len(item_ids)} items", flush=True)
                return parsed
            except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, json.JSONDecodeError, RuntimeError) as exc:
                self.failures += 1
                last_error = exc
                status = exc.code if isinstance(exc, urllib.error.HTTPError) else None
                failure_path = self.run_dir / "failed_attempts.jsonl"
                failure_path.parent.mkdir(parents=True, exist_ok=True)
                with failure_path.open("a", encoding="utf-8") as handle:
                    handle.write(canonical({"time": now(), "phase": phase, "model": model, "retry": retry, "error_type": type(exc).__name__, "http_status": status}) + "\n")
                if retry < 2:
                    time.sleep(2 ** retry)
        raise RuntimeError(f"API_FAILED:{phase}:{type(last_error).__name__}")

    @property
    def real_calls(self) -> int:
        return sum(not row["cache_hit"] for row in self.ledger)

    def _record(self, phase: str, model: str, prompt_hash: str, schema_hash: str, cache_key: str, item_ids: list[str], response_id: str, usage: dict[str, Any], cache_hit: bool, retry: int, latency: float, raw_path: str, output_hash: str, status: str) -> None:
        inp, out = int(usage.get("input_tokens") or 0), int(usage.get("output_tokens") or 0)
        cached = int((usage.get("input_tokens_details") or {}).get("cached_tokens") or 0)
        prior_in = sum(int(row["input_tokens"]) for row in self.ledger)
        prior_out = sum(int(row["output_tokens"]) for row in self.ledger)
        if prior_in + inp > self.max_input_tokens or prior_out + out > self.max_output_tokens:
            raise RuntimeError("TOKEN_CAP")
        price = PRICES[model]
        cost = 0.0 if cache_hit else ((inp - cached) * price["input"] + cached * price["cached"] + out * price["output"]) / 1_000_000
        self.ledger.append({"experiment_id": self.experiment_id, "category": self.category, "phase": phase, "model_snapshot": model, "request_id": f"req:{cache_key[:20]}", "prompt_hash": prompt_hash, "schema_hash": schema_hash, "cache_key": cache_key, "item_ids": "|".join(item_ids), "response_id": response_id, "requested_at": now(), "input_tokens": inp, "cached_input_tokens": cached, "output_tokens": out, "retry_count": retry, "latency_seconds": round(latency, 3), "raw_response_path": raw_path, "parsed_output_hash": output_hash, "estimated_cost_usd": round(cost, 8), "cache_hit": cache_hit, "status": status})

    def save(self) -> dict[str, Any]:
        fields = list(self.ledger[0]) if self.ledger else ["experiment_id"]
        path = self.run_dir / "api_ledger.csv"
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields); writer.writeheader(); writer.writerows(self.ledger)
        summary = {"real_calls": self.real_calls, "cache_hits": sum(bool(row["cache_hit"]) for row in self.ledger), "attempts": self.attempts, "failed_attempts": self.failures, "input_tokens": sum(int(row["input_tokens"]) for row in self.ledger), "output_tokens": sum(int(row["output_tokens"]) for row in self.ledger), "estimated_cost_usd": round(sum(float(row["estimated_cost_usd"]) for row in self.ledger), 6)}
        write_json(self.run_dir / "cost_summary.json", summary)
        return summary
