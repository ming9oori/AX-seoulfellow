from __future__ import annotations

from typing import Any, Mapping, Sequence


class CrossEncoderReranker:
    """Pinned Hugging Face sequence-classification reranker.

    Heavy dependencies are imported lazily so legacy retrieval methods can run
    in the CPU-only experiment environment without loading PyTorch or a model.
    """

    def __init__(self, config: Mapping[str, Any]) -> None:
        import torch
        from transformers import AutoModelForSequenceClassification, AutoTokenizer

        self.model_id = str(config["model"])
        self.revision = str(config["revision"])
        self.device = str(config.get("device", "cuda" if torch.cuda.is_available() else "cpu"))
        self.batch_size = int(config.get("batch_size", 16))
        self.max_length = int(config.get("max_length", 512))
        if self.device.startswith("cuda") and not torch.cuda.is_available():
            raise RuntimeError("Cross-encoder requested CUDA, but CUDA is unavailable")

        self._torch = torch
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_id,
            revision=self.revision,
            use_fast=True,
        )
        dtype = torch.float16 if self.device.startswith("cuda") else torch.float32
        self.model = AutoModelForSequenceClassification.from_pretrained(
            self.model_id,
            revision=self.revision,
            dtype=dtype,
        )
        self.model.to(self.device)
        self.model.eval()
        self._score_cache: dict[tuple[str, str], float] = {}

    def score(self, question: str, passages: Sequence[str]) -> list[float]:
        if not passages:
            return []
        normalized_question = str(question)
        requested = [str(passage) for passage in passages]
        missing = list(
            dict.fromkeys(
                passage
                for passage in requested
                if (normalized_question, passage) not in self._score_cache
            )
        )
        torch = self._torch
        with torch.inference_mode():
            for offset in range(0, len(missing), self.batch_size):
                chunk = missing[offset : offset + self.batch_size]
                encoded = self.tokenizer(
                    [normalized_question] * len(chunk),
                    chunk,
                    padding=True,
                    truncation=True,
                    max_length=self.max_length,
                    return_tensors="pt",
                )
                encoded = {key: value.to(self.device) for key, value in encoded.items()}
                logits = self.model(**encoded).logits
                if logits.ndim == 2 and logits.shape[1] == 1:
                    logits = logits[:, 0]
                elif logits.ndim == 2:
                    logits = logits[:, -1]
                values = [float(value) for value in logits.float().cpu().tolist()]
                for passage, value in zip(chunk, values):
                    self._score_cache[(normalized_question, passage)] = value
        output = [
            self._score_cache[(normalized_question, passage)]
            for passage in requested
        ]
        if len(output) != len(passages):
            raise RuntimeError("Cross-encoder output length mismatch")
        return output
