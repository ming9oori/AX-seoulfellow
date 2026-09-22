from __future__ import annotations

import base64
import json
import math
import os
import random
import sqlite3
import struct
import threading
import time
from pathlib import Path
from typing import Any, Literal, Sequence

import numpy as np
from openai import OpenAI
from pydantic import BaseModel, ConfigDict, Field

from .common import normalize_text, stable_hash, utc_now


class QueryProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    answer_shape: Literal[
        "FACT", "LIST", "DEFINITION", "REASON", "METHOD", "COMPARISON", "PROCEDURE"
    ]
    target_facets: list[
        Literal[
            "identity",
            "action",
            "object",
            "outcome",
            "definition",
            "triple",
            "qualifier",
            "condition",
            "temporal",
            "cause",
            "comparison",
            "procedure",
            "evidence",
        ]
    ] = Field(min_length=1, max_length=8)
    knowledge_functions: list[
        Literal["fact", "procedure", "definition", "rule", "recommendation", "decision"]
    ] = Field(min_length=1, max_length=6)
    key_terms: list[str] = Field(min_length=1, max_length=12)
    requires_qualifiers: bool
    requires_structured_fact: bool
    rationale: str = Field(max_length=300)


class QuestionAspects(BaseModel):
    """Question-only decomposition used by the conservative Aspect ablation."""

    model_config = ConfigDict(extra="forbid")

    domain_objects: list[str] = Field(min_length=1, max_length=10)
    actions: list[str] = Field(min_length=1, max_length=8)
    constraints: list[str] = Field(max_length=8)
    desired_information: list[str] = Field(min_length=1, max_length=8)
    search_terms: list[str] = Field(min_length=1, max_length=12)
    rationale: str = Field(max_length=300)


class AnswerOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    answer: str = Field(max_length=700)
    citations: list[str] = Field(max_length=5)
    status: Literal["ANSWERED", "INSUFFICIENT"]
    limitation: str = Field(max_length=400)


class VerificationOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    supported: bool
    corrected_answer: str = Field(max_length=700)
    supported_citations: list[str] = Field(max_length=5)
    unsupported_claims: list[str] = Field(max_length=8)
    limitation: str = Field(max_length=400)


class ParaphraseVariant(BaseModel):
    model_config = ConfigDict(extra="forbid")

    variant_type: Literal["alias_synonym", "scenario_query", "colloquial_query"]
    question: str = Field(min_length=5, max_length=300)
    transformation_summary: str = Field(max_length=240)


class ParaphraseBatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    variants: list[ParaphraseVariant] = Field(min_length=3, max_length=3)


class ParaphraseValidation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    variant_type: Literal["alias_synonym", "scenario_query", "colloquial_query"]
    same_information_need: bool
    no_added_or_removed_constraints: bool
    no_answer_leakage: bool
    natural_korean: bool
    rationale: str = Field(max_length=320)


class ParaphraseValidationBatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    validations: list[ParaphraseValidation] = Field(min_length=3, max_length=3)


QUERY_PROFILE_INSTRUCTION = """You analyze Korean enterprise proposal-work questions.
Return only the requested structured object. Analyze the question itself; no answer or
retrieved context is available. Select properties that must be matched to answer it.
Use qualifiers for time, condition, scope, exception, purpose, or comparison. Use
structured_fact when subject-predicate-object detail is likely needed. Do not invent
domain facts."""


QUESTION_ASPECT_INSTRUCTION = """You decompose a Korean enterprise bid/proposal-work
question into retrieval aspects. Use only information explicitly present in the
question. Never answer the question and never invent a company, process, condition,
artifact, or domain fact. Keep short noun or verb phrases rather than sentences.

- domain_objects: the business objects, artifacts, actors, or process areas being asked about
- actions: requested actions, decisions, comparisons, or procedures
- constraints: explicit time, condition, scope, purpose, exception, or quantity constraints;
  return an empty list when none is stated
- desired_information: what the answer must provide, without supplying that answer
- search_terms: faithful aliases or normalized terms grounded in the question only

Return only the requested structured object."""


ANSWER_INSTRUCTION = """You are a grounded Korean QA assistant for proposal work.
Use only the supplied retrieval context. Never use outside knowledge. Answer the
question directly in one or two clean Korean sentences. Put evidence identifiers such
as E1 only in the citations field, not in the answer body. If the context does not
contain enough information, set status to INSUFFICIENT and state the missing support
briefly. A PCF label is classification context, not proof of a detailed practice."""


VERIFIER_INSTRUCTION = """You are the online grounding verifier, not an offline answer
judge. Check the draft only against the supplied context. Remove or correct every claim
not directly supported. Preserve useful limitations. Return a concise one- or two-
sentence corrected Korean answer. Cite only evidence IDs that exist in the context. If
the context is insufficient, say so rather than guessing. You never see a gold answer."""


PARAPHRASE_GENERATOR_INSTRUCTION = """You create Korean retrieval stress-test
questions for enterprise bid and proposal work. Return exactly one question for each
requested variant type. Preserve the original information need, answer scope, modality,
and every condition. Never answer the question. Never add a company, product, amount,
deadline, policy, exception, or other fact that is absent from the original question.

- alias_synonym: use natural aliases, synonyms, or a substantially different sentence
  structure; do not merely change particles or endings.
- scenario_query: place the same information need in a generic work situation, without
  adding a condition that would change the correct answer.
- colloquial_query: write a concise, natural question that a coworker might ask, without
  dropping important scope.

You receive only the original question. Do not infer or reconstruct source wording,
evidence passages, or the answer. If prior candidates are supplied, use only their safe
failure-code labels to make a new attempt."""


PARAPHRASE_VALIDATOR_INSTRUCTION = """You validate Korean paraphrases for a retrieval
stress test. This is a separate validation pass. Compare each candidate with the
original question and reference answer. Do not rewrite a candidate and do not supply a
better question. Mark same_information_need true only when the same answer would fully
answer both questions. Mark no_added_or_removed_constraints false if time, actor, scope,
purpose, modality, number of requested items, or any other condition changed. Mark
no_answer_leakage false if the candidate states or strongly gives away the reference
answer. Mark natural_korean false for awkward or ambiguous language. Use a short reason;
never quote the reference answer in the reason."""


class SqliteCache:
    def __init__(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        self._local = threading.local()
        self._initialize()

    def _connection(self) -> sqlite3.Connection:
        connection = getattr(self._local, "connection", None)
        if connection is None:
            connection = sqlite3.connect(self.path, timeout=120)
            connection.execute("PRAGMA journal_mode=WAL")
            connection.execute("PRAGMA synchronous=NORMAL")
            self._local.connection = connection
        return connection

    def _initialize(self) -> None:
        connection = sqlite3.connect(self.path)
        try:
            connection.executescript(
                """
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS embeddings (
                    model TEXT NOT NULL,
                    text_hash TEXT NOT NULL,
                    dimensions INTEGER NOT NULL,
                    vector BLOB NOT NULL,
                    created_at TEXT NOT NULL,
                    PRIMARY KEY (model, text_hash)
                );
                CREATE TABLE IF NOT EXISTS llm_outputs (
                    cache_key TEXT PRIMARY KEY,
                    model TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    response_id TEXT,
                    payload TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )
            connection.commit()
        finally:
            connection.close()

    def get_embedding(self, model: str, text_hash: str) -> np.ndarray | None:
        row = self._connection().execute(
            "SELECT dimensions, vector FROM embeddings WHERE model=? AND text_hash=?",
            (model, text_hash),
        ).fetchone()
        if row is None:
            return None
        dimensions, blob = row
        return np.frombuffer(blob, dtype="<f4", count=dimensions).copy()

    def get_embeddings(
        self, model: str, text_hashes: Sequence[str]
    ) -> dict[str, np.ndarray]:
        unique_hashes = list(dict.fromkeys(text_hashes))
        output: dict[str, np.ndarray] = {}
        connection = self._connection()
        for offset in range(0, len(unique_hashes), 800):
            chunk = unique_hashes[offset : offset + 800]
            placeholders = ",".join("?" for _ in chunk)
            rows = connection.execute(
                f"SELECT text_hash, dimensions, vector FROM embeddings "
                f"WHERE model=? AND text_hash IN ({placeholders})",
                (model, *chunk),
            ).fetchall()
            for text_hash, dimensions, blob in rows:
                output[text_hash] = np.frombuffer(
                    blob, dtype="<f4", count=dimensions
                ).copy()
        return output

    def put_embedding(self, model: str, text_hash: str, vector: Sequence[float]) -> None:
        values = [float(value) for value in vector]
        blob = struct.pack(f"<{len(values)}f", *values)
        connection = self._connection()
        connection.execute(
            "INSERT OR REPLACE INTO embeddings VALUES (?, ?, ?, ?, ?)",
            (model, text_hash, len(values), blob, utc_now()),
        )
        connection.commit()

    def put_embeddings(
        self, model: str, values: Sequence[tuple[str, Sequence[float]]]
    ) -> None:
        rows = []
        created_at = utc_now()
        for text_hash, vector in values:
            floats = [float(value) for value in vector]
            rows.append(
                (
                    model,
                    text_hash,
                    len(floats),
                    struct.pack(f"<{len(floats)}f", *floats),
                    created_at,
                )
            )
        connection = self._connection()
        connection.executemany(
            "INSERT OR REPLACE INTO embeddings VALUES (?, ?, ?, ?, ?)", rows
        )
        connection.commit()

    def get_llm(self, cache_key: str) -> dict[str, Any] | None:
        row = self._connection().execute(
            "SELECT payload FROM llm_outputs WHERE cache_key=?", (cache_key,)
        ).fetchone()
        return json.loads(row[0]) if row else None

    def put_llm(
        self,
        cache_key: str,
        *,
        model: str,
        kind: str,
        response_id: str,
        payload: dict[str, Any],
    ) -> None:
        connection = self._connection()
        connection.execute(
            "INSERT OR REPLACE INTO llm_outputs VALUES (?, ?, ?, ?, ?, ?)",
            (
                cache_key,
                model,
                kind,
                response_id,
                json.dumps(payload, ensure_ascii=False),
                utc_now(),
            ),
        )
        connection.commit()


class OpenAIBackend:
    def __init__(
        self,
        *,
        cache_path: Path,
        embedding_model: str,
        profiler_model: str,
        generator_model: str,
        aspect_analyzer_model: str | None = None,
        paraphrase_validator_model: str | None = None,
        embedding_dimensions: int = 1024,
        embedding_provider: str = "openai",
        embedding_revision: str | None = None,
        embedding_device: str = "cpu",
        embedding_dtype: str = "float32",
        embedding_max_length: int | None = None,
        embedding_query_prompt_name: str | None = None,
        reasoning_effort: str | None = "low",
        max_retries: int = 5,
        timeout: float = 180.0,
    ) -> None:
        self.embedding_provider = normalize_text(embedding_provider).lower() or "openai"
        if self.embedding_provider not in {"openai", "sentence_transformers"}:
            raise ValueError(
                "embedding_provider must be 'openai' or 'sentence_transformers'"
            )
        api_key_present = bool(os.getenv("OPENAI_API_KEY"))
        if self.embedding_provider == "openai" and not api_key_present:
            raise RuntimeError("OPENAI_API_KEY is not set in the current process.")
        self.client = OpenAI(timeout=timeout) if api_key_present else None
        self.cache = SqliteCache(cache_path)
        self.embedding_model = embedding_model
        self.embedding_dimensions = int(embedding_dimensions)
        self.embedding_revision = normalize_text(embedding_revision)
        self.embedding_device = normalize_text(embedding_device) or "cpu"
        self.embedding_dtype = normalize_text(embedding_dtype).lower() or "float32"
        self.embedding_max_length = (
            int(embedding_max_length) if embedding_max_length is not None else None
        )
        self.embedding_query_prompt_name = normalize_text(
            embedding_query_prompt_name
        )
        self.profiler_model = profiler_model
        self.generator_model = generator_model
        self.aspect_analyzer_model = aspect_analyzer_model or profiler_model
        self.paraphrase_validator_model = paraphrase_validator_model or generator_model
        self.reasoning_effort = reasoning_effort
        self.max_retries = max_retries
        self._llm_locks_guard = threading.Lock()
        self._llm_locks: dict[str, threading.Lock] = {}
        self._local_embedder = None
        self._local_embedder_lock = threading.Lock()

    def _embedding_cache_model(self, input_type: str) -> str:
        if self.embedding_provider == "openai":
            # Preserve the historical cache namespace so the new provider switch
            # cannot silently invalidate or alter the published OpenAI condition.
            return f"{self.embedding_model}:dimensions={self.embedding_dimensions}"
        role = "text"
        if self.embedding_query_prompt_name:
            role = input_type
        revision = self.embedding_revision or "default"
        prompt = (
            self.embedding_query_prompt_name
            if role == "query"
            else "none"
        )
        max_length = self.embedding_max_length or "model-default"
        return (
            f"{self.embedding_provider}:{self.embedding_model}:revision={revision}:"
            f"dimensions={self.embedding_dimensions}:role={role}:prompt={prompt}:"
            f"max_length={max_length}:dtype={self.embedding_dtype}"
        )

    def _require_openai_client(self) -> OpenAI:
        if self.client is None:
            raise RuntimeError(
                "OPENAI_API_KEY is required for profiling, generation, verification, "
                "and OpenAI-hosted embeddings."
            )
        return self.client

    def _get_local_embedder(self):
        if self._local_embedder is not None:
            return self._local_embedder
        with self._local_embedder_lock:
            if self._local_embedder is not None:
                return self._local_embedder
            import torch
            from sentence_transformers import SentenceTransformer

            dtype_by_name = {
                "float16": torch.float16,
                "fp16": torch.float16,
                "bfloat16": torch.bfloat16,
                "bf16": torch.bfloat16,
                "float32": torch.float32,
                "fp32": torch.float32,
            }
            if self.embedding_dtype not in dtype_by_name:
                raise ValueError(
                    f"Unsupported local embedding dtype: {self.embedding_dtype}"
                )
            kwargs: dict[str, Any] = {
                "device": self.embedding_device,
                "model_kwargs": {
                    "torch_dtype": dtype_by_name[self.embedding_dtype],
                },
            }
            if self.embedding_revision:
                kwargs["revision"] = self.embedding_revision
            model = SentenceTransformer(self.embedding_model, **kwargs)
            if self.embedding_max_length is not None:
                model.max_seq_length = self.embedding_max_length
            self._local_embedder = model
            return model

    def _llm_lock(self, cache_key: str) -> threading.Lock:
        """Serialize identical requests so concurrent cache misses stay identical."""
        with self._llm_locks_guard:
            return self._llm_locks.setdefault(cache_key, threading.Lock())

    def _retry(self, operation):
        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                return operation()
            except Exception as exc:
                last_error = exc
                if attempt >= self.max_retries:
                    break
                delay = min(30.0, (2**attempt) + random.random())
                time.sleep(delay)
        assert last_error is not None
        raise last_error

    def embed(
        self,
        texts: Sequence[str],
        *,
        batch_size: int = 64,
        input_type: Literal["query", "document"] = "document",
    ) -> list[Sequence[float]]:
        if input_type not in {"query", "document"}:
            raise ValueError("input_type must be 'query' or 'document'")
        normalized = [normalize_text(text) or "[EMPTY]" for text in texts]
        text_hashes = [stable_hash(text) for text in normalized]
        cache_model = self._embedding_cache_model(input_type)
        cached_values = self.cache.get_embeddings(
            cache_model, text_hashes
        )
        vectors: list[Sequence[float] | None] = [None] * len(normalized)
        missing_by_hash: dict[str, tuple[str, list[int]]] = {}
        for index, (text, text_hash) in enumerate(zip(normalized, text_hashes)):
            cached = cached_values.get(text_hash)
            if cached is not None:
                vectors[index] = cached
                continue
            if text_hash not in missing_by_hash:
                missing_by_hash[text_hash] = (text, [])
            missing_by_hash[text_hash][1].append(index)

        missing = list(missing_by_hash.items())
        for offset in range(0, len(missing), batch_size):
            chunk = missing[offset : offset + batch_size]
            inputs = [item[1][0] for item in chunk]
            if self.embedding_provider == "openai":
                client = self._require_openai_client()

                def call():
                    return client.embeddings.create(
                        model=self.embedding_model,
                        input=inputs,
                        dimensions=self.embedding_dimensions,
                        encoding_format="base64",
                    )

                response = self._retry(call)
                ordered = sorted(response.data, key=lambda item: item.index)
                if len(ordered) != len(chunk):
                    raise RuntimeError("Embedding response length mismatch")
                raw_vectors: list[Sequence[float]] = []
                for item in ordered:
                    if isinstance(item.embedding, str):
                        decoded = base64.b64decode(item.embedding)
                        vector = np.frombuffer(decoded, dtype="<f4").astype(float).tolist()
                    else:
                        vector = [float(value) for value in item.embedding]
                    raw_vectors.append(vector)
            else:
                model = self._get_local_embedder()
                encode_kwargs: dict[str, Any] = {
                    "batch_size": batch_size,
                    "convert_to_numpy": True,
                    "normalize_embeddings": True,
                    "show_progress_bar": False,
                }
                if input_type == "query" and self.embedding_query_prompt_name:
                    encode_kwargs["prompt_name"] = self.embedding_query_prompt_name
                raw = model.encode(inputs, **encode_kwargs)
                raw_vectors = np.asarray(raw, dtype=np.float32).tolist()
                if len(raw_vectors) != len(chunk):
                    raise RuntimeError("Local embedding response length mismatch")
            cache_values: list[tuple[str, list[float]]] = []
            for (text_hash, (_, indices)), raw_vector in zip(chunk, raw_vectors):
                vector = [float(value) for value in raw_vector]
                if len(vector) < self.embedding_dimensions:
                    raise RuntimeError(
                        f"Embedding dimension {len(vector)} is smaller than requested "
                        f"{self.embedding_dimensions}"
                    )
                if len(vector) > self.embedding_dimensions:
                    vector = vector[: self.embedding_dimensions]
                norm = math.sqrt(sum(value * value for value in vector))
                if norm:
                    vector = [value / norm for value in vector]
                cache_values.append((text_hash, vector))
                for index in indices:
                    vectors[index] = vector
            self.cache.put_embeddings(cache_model, cache_values)

        if any(vector is None for vector in vectors):
            raise RuntimeError("Failed to populate every embedding")
        return [vector for vector in vectors if vector is not None]

    def _parse(
        self,
        *,
        model: str,
        kind: str,
        instruction: str,
        user_input: str,
        response_model: type[BaseModel],
        max_output_tokens: int,
    ) -> tuple[dict[str, Any], str, bool]:
        cache_key = stable_hash(
            {
                "model": model,
                "kind": kind,
                "instruction": instruction,
                "input": user_input,
                "schema": response_model.model_json_schema(),
                "reasoning_effort": self.reasoning_effort,
                "max_output_tokens": max_output_tokens,
            }
        )
        with self._llm_lock(cache_key):
            cached = self.cache.get_llm(cache_key)
            if cached is not None:
                return cached["value"], cached.get("response_id", "cache"), True

            def call():
                client = self._require_openai_client()
                request: dict[str, Any] = {
                    "model": model,
                    "instructions": instruction,
                    "input": [{"role": "user", "content": user_input}],
                    "text_format": response_model,
                    "max_output_tokens": max_output_tokens,
                    "store": False,
                }
                if self.reasoning_effort:
                    request["reasoning"] = {"effort": self.reasoning_effort}
                return client.responses.parse(
                    **request,
                )

            response = self._retry(call)
            parsed = response.output_parsed
            if parsed is None:
                raise RuntimeError(f"Structured {kind} response is empty")
            value = parsed.model_dump()
            self.cache.put_llm(
                cache_key,
                model=model,
                kind=kind,
                response_id=response.id,
                payload={"value": value, "response_id": response.id},
            )
            return value, response.id, False

    def profile_question(self, question: str) -> tuple[dict[str, Any], str, bool]:
        return self._parse(
            model=self.profiler_model,
            kind="query_profile",
            instruction=QUERY_PROFILE_INSTRUCTION,
            user_input=f"[QUESTION]\n{normalize_text(question)}",
            response_model=QueryProfile,
            max_output_tokens=800,
        )

    def analyze_question_aspects(self, question: str) -> tuple[dict[str, Any], str, bool]:
        return self._parse(
            model=self.aspect_analyzer_model,
            kind="question_aspects_v1",
            instruction=QUESTION_ASPECT_INSTRUCTION,
            user_input=f"[QUESTION]\n{normalize_text(question)}",
            response_model=QuestionAspects,
            max_output_tokens=700,
        )

    def generate_answer(
        self,
        *,
        question: str,
        context: str,
        max_output_tokens: int,
    ) -> tuple[dict[str, Any], str, bool]:
        user_input = f"[QUESTION]\n{normalize_text(question)}\n\n[RETRIEVAL CONTEXT]\n{context}"
        return self._parse(
            model=self.generator_model,
            kind="answer_generation",
            instruction=ANSWER_INSTRUCTION,
            user_input=user_input,
            response_model=AnswerOutput,
            max_output_tokens=max_output_tokens,
        )

    def verify_answer(
        self,
        *,
        question: str,
        context: str,
        draft: dict[str, Any],
        max_output_tokens: int,
    ) -> tuple[dict[str, Any], str, bool]:
        user_input = (
            f"[QUESTION]\n{normalize_text(question)}\n\n"
            f"[RETRIEVAL CONTEXT]\n{context}\n\n"
            f"[DRAFT]\n{json.dumps(draft, ensure_ascii=False)}"
        )
        return self._parse(
            model=self.generator_model,
            kind="online_grounding_verification",
            instruction=VERIFIER_INSTRUCTION,
            user_input=user_input,
            response_model=VerificationOutput,
            max_output_tokens=max_output_tokens,
        )

    def generate_paraphrase_variants(
        self,
        *,
        question: str,
        prior_failure_codes: dict[str, list[str]] | None = None,
    ) -> tuple[dict[str, Any], str, bool]:
        """Generate three question-only rewrites without answer or evidence context."""
        payload: dict[str, Any] = {
            "original_question": normalize_text(question),
            "required_variant_types": [
                "alias_synonym",
                "scenario_query",
                "colloquial_query",
            ],
        }
        if prior_failure_codes:
            payload["prior_failure_codes"] = prior_failure_codes
        return self._parse(
            model=self.generator_model,
            kind="paraphrase_challenge_generation_v1",
            instruction=PARAPHRASE_GENERATOR_INSTRUCTION,
            user_input=json.dumps(payload, ensure_ascii=False),
            response_model=ParaphraseBatch,
            max_output_tokens=1200,
        )

    def validate_paraphrase_variants(
        self,
        *,
        question: str,
        reference_answer: str,
        variants: Sequence[dict[str, Any]],
    ) -> tuple[dict[str, Any], str, bool]:
        """Validate rewrites in a separate call; source passages are never included."""
        payload = {
            "original_question": normalize_text(question),
            "reference_answer": normalize_text(reference_answer),
            "candidates": [
                {
                    "variant_type": normalize_text(item.get("variant_type")),
                    "question": normalize_text(item.get("question")),
                }
                for item in variants
            ],
        }
        return self._parse(
            model=self.paraphrase_validator_model,
            kind="paraphrase_challenge_validation_v1",
            instruction=PARAPHRASE_VALIDATOR_INSTRUCTION,
            user_input=json.dumps(payload, ensure_ascii=False),
            response_model=ParaphraseValidationBatch,
            max_output_tokens=1200,
        )
