"""Isolated exact-text embedding cache; no reads/writes to historical caches."""
from __future__ import annotations

import hashlib
import json
import sqlite3
import numpy as np
import tiktoken

from .common import normalize_text


class CoverEmbeddingBackend:
    def __init__(self, api, path):
        self.api = api
        self.db = sqlite3.connect(path)
        self.db.execute("CREATE TABLE IF NOT EXISTS vectors (key TEXT PRIMARY KEY, vector BLOB NOT NULL)")
        self.tokenizer = tiktoken.encoding_for_model(api.config["models"]["embedding"])
        self.dimensions = api.config["models"]["embedding_dimensions"]
        self.memory = {}
        self.stats = {"hits": 0, "misses": 0, "requests": 0}
        self.allow_api = True

    def embed_exact(self, texts, *, namespace="pars-cover-direct-views-v1", batch_size=128):
        if any(not isinstance(t, str) or not t.strip() for t in texts):
            raise ValueError("Empty exact input is forbidden")
        models = self.api.config["models"]
        def key(text):
            payload = [models["embedding_provider"], models["embedding"], self.dimensions, namespace,
                       hashlib.sha256(text.encode()).hexdigest()]
            return hashlib.sha256(json.dumps(payload).encode()).hexdigest()
        keys = [key(t) for t in texts]
        missing = {}
        for k, text in zip(keys, texts):
            if k not in self.memory:
                row = self.db.execute("SELECT vector FROM vectors WHERE key=?", (k,)).fetchone()
                if row:
                    self.memory[k] = np.frombuffer(row[0], dtype="<f4").copy()
            if k in self.memory:
                self.stats["hits"] += 1
            else:
                missing.setdefault(k, text)
        self.stats["misses"] += len(missing)
        if missing and not self.allow_api:
            raise RuntimeError("Warm benchmark embedding cache miss")
        batches, batch, count = [], [], 0
        limit = self.api.config["retrieval"]["embedding_max_batch_tokens"]
        for k, text in missing.items():
            size = len(self.tokenizer.encode(text, disallowed_special=()))
            if size > self.api.config["retrieval"]["embedding_max_input_tokens"]:
                raise ValueError("Oversized embedding input; no truncation")
            if batch and (len(batch) >= min(batch_size, 128) or count + size > limit):
                batches.append(batch)
                batch, count = [], 0
            batch.append((k, text))
            count += size
        if batch:
            batches.append(batch)
        for batch in batches:
            vectors = self.api.embed_batch([t for _, t in batch], self.tokenizer)
            self.stats["requests"] += 1
            for (k, _), vector in zip(batch, vectors):
                self.memory[k] = vector
                self.db.execute("INSERT INTO vectors VALUES (?, ?)", (k, vector.astype("<f4").tobytes()))
            self.db.commit()
        return [self.memory[k] for k in keys]

    def embed(self, texts, *, batch_size=64, input_type="document"):
        # Match legacy normalization and empty sentinel, isolated from direct-view contract.
        return self.embed_exact([normalize_text(t) or "[EMPTY]" for t in texts],
                                namespace="legacy-normalized-text-v1", batch_size=batch_size)
