"""Strict, secret-safe API adapter for the reconstructed PARS-Cover contract.

Preserves the legacy Responses endpoint and Pydantic local output validation.
Adds explicit decoding, strict wire schemas, transient-only retry and failure types.
No credential, raw exception, HTTP body/header, or client repr is logged.
"""
from __future__ import annotations

import json
import time
from typing import Callable

import numpy as np
from openai import APIConnectionError, APIStatusError, OpenAI

from .openai_backend import AnswerOutput, VerificationOutput
from .shared_context import validate_local_citations


class CoverAPIError(RuntimeError):
    def __init__(self, kind, *, status=None, attempts=1):
        self.kind, self.status, self.attempts = kind, status, attempts
        super().__init__(kind)

    def record(self):
        return {"kind": self.kind, "http_status": self.status, "attempts": self.attempts}


class CoverAPI:
    def __init__(self, api_key, config, *, client=None, on_event=None, sleep=time.sleep):
        self.config = config
        self.client = client or OpenAI(api_key=api_key, base_url="https://api.openai.com/v1",
                                      max_retries=0, timeout=90)
        self.on_event = on_event or (lambda event: None)
        self.sleep = sleep

    def _call(self, kind: str, operation: Callable):
        for attempt in range(self.config["generation"]["max_retries"] + 1):
            self.on_event({"kind": kind, "event": "request", "attempt": attempt + 1})
            try:
                response = operation()
            except (APIConnectionError, APIStatusError) as exc:
                status = getattr(exc, "status_code", None)
                transient = isinstance(exc, APIConnectionError) or status == 429 or (status is not None and status >= 500)
                failure = ("AUTHENTICATION" if status == 401 else "PERMISSION" if status == 403
                           else "RATE_LIMIT" if status == 429 else "CONNECTION" if status is None
                           else "API_STATUS")
                self.on_event({"kind": kind, "event": "failure", "failure": failure,
                               "http_status": status, "attempt": attempt + 1})
                if not transient or attempt == self.config["generation"]["max_retries"]:
                    raise CoverAPIError(failure, status=status, attempts=attempt + 1) from None
                self.sleep(min(30, 2 ** attempt))
                continue
            usage = getattr(response, "usage", None)
            self.on_event({"kind": kind, "event": "success", "attempt": attempt + 1,
                           "model": getattr(response, "model", None),
                           "usage": usage.model_dump() if usage else None})
            return response
        raise AssertionError("Unreachable retry loop")

    def embed_batch(self, texts, tokenizer):
        if not texts or any(not isinstance(t, str) or not t.strip() for t in texts):
            raise ValueError("Empty embedding input")
        sizes = [len(tokenizer.encode(t, disallowed_special=())) for t in texts]
        limits = self.config["retrieval"]
        if max(sizes) > limits["embedding_max_input_tokens"] or sum(sizes) > limits["embedding_max_batch_tokens"]:
            raise ValueError("Embedding token limit exceeded; input is never truncated")
        if len(texts) > limits["embedding_batch_size"]:
            raise ValueError("Embedding batch size exceeded")
        models = self.config["models"]
        response = self._call("embedding", lambda: self.client.embeddings.create(
            model=models["embedding"], dimensions=models["embedding_dimensions"],
            input=texts, encoding_format="float"))
        data = sorted(response.data, key=lambda row: row.index)
        if [row.index for row in data] != list(range(len(texts))):
            raise CoverAPIError("EMBEDDING_INDEX_MISMATCH")
        vectors = np.asarray([row.embedding for row in data], dtype=np.float32)
        if vectors.shape != (len(texts), models["embedding_dimensions"]) or not np.isfinite(vectors).all():
            raise CoverAPIError("EMBEDDING_SHAPE_OR_FINITE")
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        if np.any(norms <= 0):
            raise CoverAPIError("ZERO_EMBEDDING")
        return vectors / norms

    def structured(self, kind, prompt, schema, user_input, citation_map):
        if kind not in {"answer", "verifier"}:
            raise ValueError("Unknown generation kind")
        settings = self.config["generation"]
        response = self._call(kind, lambda: self.client.responses.create(
            model=self.config["models"]["answer_generator"], instructions=prompt,
            input=[{"role": "user", "content": user_input}],
            text={"format": {"type": "json_schema", "name": kind + "_output",
                             "strict": True, "schema": schema}},
            temperature=settings["temperature"], top_p=settings["top_p"],
            max_output_tokens=settings["max_output_tokens"], store=False))
        if response.status == "incomplete":
            raise CoverAPIError("TRUNCATION_OR_INCOMPLETE")
        for item in response.output:
            for content in getattr(item, "content", []):
                if getattr(content, "type", None) == "refusal":
                    raise CoverAPIError("REFUSAL")
        if response.status != "completed":
            raise CoverAPIError("RESPONSE_NOT_COMPLETED")
        model = AnswerOutput if kind == "answer" else VerificationOutput
        try:
            value = model.model_validate_json(response.output_text).model_dump()
            field = "citations" if kind == "answer" else "supported_citations"
            validate_local_citations(value[field], citation_map)
        except (ValueError, TypeError):
            raise CoverAPIError("SCHEMA_OR_CITATION_VALIDATION") from None
        return value
