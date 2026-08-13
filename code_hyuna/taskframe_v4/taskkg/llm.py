from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import random
import re
import time
from typing import Any
import urllib.error
import urllib.request

from .utils import read_json, stable_id, text, write_json


@dataclass(frozen=True)
class LLMConfig:
    api_key: str
    api_base: str
    model: str
    timeout: float
    max_retries: int
    rate_limit_seconds: float

    @classmethod
    def from_env(cls) -> "LLMConfig":
        key = os.environ.get("TASKFRAME_API_KEY", "").strip()
        model = os.environ.get("TASKFRAME_MODEL", "").strip()
        if not key or not model:
            raise ValueError(
                "TASKFRAME_API_KEY와 TASKFRAME_MODEL이 필요합니다. "
                ".env를 작성하거나 --backend heuristic을 사용하세요."
            )
        return cls(
            api_key=key,
            api_base=os.environ.get(
                "TASKFRAME_API_BASE", "https://api.openai.com/v1"
            ).rstrip("/"),
            model=model,
            timeout=float(os.environ.get("TASKFRAME_TIMEOUT", "180")),
            max_retries=int(os.environ.get("TASKFRAME_MAX_RETRIES", "4")),
            rate_limit_seconds=float(
                os.environ.get("TASKFRAME_RATE_LIMIT_SECONDS", "0.2")
            ),
        )


def parse_json(content: str) -> Any:
    value = content.strip()
    value = re.sub(r"^```(?:json)?\s*", "", value, flags=re.I)
    value = re.sub(r"\s*```$", "", value)
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        decoder = json.JSONDecoder()
        starts = sorted(pos for pos in (value.find("{"), value.find("[")) if pos >= 0)
        for start in starts:
            try:
                result, _ = decoder.raw_decode(value[start:])
                return result
            except json.JSONDecodeError:
                pass
    raise ValueError("LLM 응답에서 JSON을 찾지 못했습니다.")


class ChatJSONClient:
    def __init__(self, config: LLMConfig, cache_dir: Path, use_cache: bool = True):
        self.config = config
        self.cache_dir = cache_dir
        self.use_cache = use_cache
        cache_dir.mkdir(parents=True, exist_ok=True)

    def call(self, stage: str, key: str, system: str, user: str) -> Any:
        call_id = stable_id(
            "CALL", self.config.api_base, self.config.model, stage, key, system, user,
            length=24,
        )
        cache_path = self.cache_dir / stage / f"{call_id}.json"
        if self.use_cache and cache_path.exists():
            return read_json(cache_path)["parsed"]
        payload: dict[str, Any] = {
            "model": self.config.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0,
            "response_format": {"type": "json_object"},
        }
        error: Exception | None = None
        for attempt in range(1, self.config.max_retries + 1):
            request = urllib.request.Request(
                f"{self.config.api_base}/chat/completions",
                data=json.dumps(payload, ensure_ascii=False).encode(),
                headers={
                    "Authorization": f"Bearer {self.config.api_key}",
                    "Content-Type": "application/json",
                },
                method="POST",
            )
            try:
                with urllib.request.urlopen(request, timeout=self.config.timeout) as response:
                    envelope = json.loads(response.read().decode())
                content = envelope["choices"][0]["message"]["content"]
                if isinstance(content, list):
                    content = "".join(
                        text(part.get("text")) for part in content if isinstance(part, dict)
                    )
                parsed = parse_json(str(content))
                write_json(
                    cache_path,
                    {"stage": stage, "model": self.config.model, "parsed": parsed},
                )
                if self.config.rate_limit_seconds:
                    time.sleep(self.config.rate_limit_seconds)
                return parsed
            except urllib.error.HTTPError as exc:
                body = exc.read().decode(errors="replace")[:1200]
                error = RuntimeError(f"LLM HTTP {exc.code}: {body}")
                if exc.code == 400 and "response_format" in body:
                    payload.pop("response_format", None)
                elif exc.code not in {408, 409, 429, 500, 502, 503, 504}:
                    raise error
            except (urllib.error.URLError, OSError, KeyError, ValueError) as exc:
                error = exc
            if attempt < self.config.max_retries:
                print(
                    f"[llm-retry] stage={stage} attempt={attempt}/"
                    f"{self.config.max_retries} error={type(error).__name__}: {error}"
                )
                time.sleep(min(30, 2 ** (attempt - 1) + random.random()))
        raise RuntimeError(f"LLM 호출 실패(stage={stage}): {error}")
