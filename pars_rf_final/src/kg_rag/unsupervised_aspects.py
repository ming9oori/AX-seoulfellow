from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

import numpy as np
from kiwipiepy import Kiwi

from .common import normalize_text


P1U_TFIDF = "P1U_TFIDF_ASPECT_CROSS_ENCODER_MMR"
P1U_EMBEDRANK = "P1U_EMBEDRANK_ASPECT_CROSS_ENCODER_MMR"
P1U_EMBEDRANK_MMR = "P1U_EMBEDRANK_MMR_ASPECT_CROSS_ENCODER_MMR"
P1U_ATTENTION_SEEKER = "P1U_ATTENTION_SEEKER_ASPECT_CROSS_ENCODER_MMR"
P1G_PCF_GROUNDED = "P1G_PCF_GROUNDED_ASPECT_CROSS_ENCODER_MMR"
P1P_PARS = "P1P_PCF_ANCHORED_PROPERTY_RELATIONAL_SUBGRAPH_MMR"
P1B_PROFILE_FREE = "P1B_PCF_FIRST_PROFILE_FREE_CROSS_ENCODER_MMR"
P1G_PROFILE_FREE = "P1G_PCF_GROUNDED_ASPECT_PROFILE_FREE_MMR"
P1P_PARS_PROFILE_FREE = (
    "P1P_PCF_ANCHORED_PROPERTY_RELATIONAL_SUBGRAPH_PROFILE_FREE_MMR"
)

QUESTION_ONLY_UNSUPERVISED_ASPECT_METHODS = (
    P1U_TFIDF,
    P1U_EMBEDRANK,
    P1U_EMBEDRANK_MMR,
    P1U_ATTENTION_SEEKER,
)
EMBEDDING_UNSUPERVISED_ASPECT_METHODS = QUESTION_ONLY_UNSUPERVISED_ASPECT_METHODS[:-1]
UNSUPERVISED_ASPECT_METHODS = (
    *QUESTION_ONLY_UNSUPERVISED_ASPECT_METHODS,
    P1G_PCF_GROUNDED,
)


NOMINAL_TAGS = {"NNG", "NNP", "NNB", "NR", "NP", "SL", "SN", "SH", "XR"}
NOMINAL_AFFIX_TAGS = {"XPN", "XSN"}
VERBAL_TAG_PREFIXES = ("VV", "VA")
VERBAL_SUFFIX_TAGS = {"XSV", "XSA"}

# These are grammatical stop terms, not learned domain labels. Domain vocabulary is
# discovered from the question collection through document frequency and embeddings.
STOP_TERMS = {
    "것",
    "수",
    "등",
    "어떤",
    "어떻",
    "무엇",
    "누구",
    "얼마",
    "이유",
    "내용",
    "항목",
    "의미",
    "하",
    "되",
    "이",
    "있",
    "없",
    "같",
    "필요",
    "중요",
    "저",
}
CONSTRAINT_MARKERS = {
    "전",
    "후",
    "뒤",
    "때",
    "경우",
    "조건",
    "예외",
    "이상",
    "이하",
    "이내",
    "범위",
    "대상",
    "목적",
    "위하",
    "보다",
    "현재",
    "과거",
}


@dataclass(frozen=True)
class AspectCandidate:
    text: str
    kind: str
    terms: tuple[str, ...]
    order: int
    spans: tuple[tuple[int, int], ...] = ()

    @property
    def query_text(self) -> str:
        """Return a particle-free retrieval view while retaining the source span."""
        return " ".join(dict.fromkeys(self.terms))


def attention_seeker_token_scores(
    attentions: Any,
    candidate_mask: Any,
    valid_mask: Any,
) -> Any:
    """Apply Attention-Seeker's short-document Equations 3--5.

    ``attentions`` has shape ``[layer, head, query_token, key_token]``.
    Candidate tokens define the hypothesis vector H. The implementation keeps
    the computation separate from model loading so the paper formula can be
    unit-tested with small synthetic tensors.
    """
    import torch

    maps = attentions.float()
    hypothesis = candidate_mask.to(device=maps.device, dtype=maps.dtype)
    valid = valid_mask.to(device=maps.device, dtype=maps.dtype)
    if maps.ndim != 4 or maps.shape[-1] != maps.shape[-2]:
        raise ValueError("attentions must have shape [layer, head, token, token]")
    if hypothesis.ndim != 1 or hypothesis.shape[0] != maps.shape[-1]:
        raise ValueError("candidate_mask length must match the attention maps")
    if valid.shape != hypothesis.shape:
        raise ValueError("valid_mask must have the same shape as candidate_mask")
    if not bool(torch.any(hypothesis > 0)):
        return torch.zeros_like(hypothesis)

    # S_lh = A_lh H (Eq. 3), followed by the paper's query-token mask.
    vector_relevance = torch.einsum("lhij,j->lhi", maps, hypothesis)
    vector_relevance = vector_relevance * hypothesis.view(1, 1, -1)
    # R_lh is the average relevance of the attention vectors (Eq. 4).
    denominator = torch.clamp(valid.sum(), min=1.0)
    map_relevance = (vector_relevance * valid.view(1, 1, -1)).sum(dim=-1)
    map_relevance = map_relevance / denominator
    # B aggregates the dynamically weighted rows across every layer/head (Eq. 5).
    scores = torch.einsum(
        "lhij,lhi,lh->j",
        maps,
        vector_relevance,
        map_relevance,
    )
    return scores * hypothesis


class LocalAttentionSeekerScorer:
    """Local multilingual encoder adaptation of Attention-Seeker (COLING 2025).

    The paper evaluates Llama/BERT attention maps. This implementation uses a
    pinned multilingual encoder and Korean Kiwi candidates, so it is an explicit
    task/language adaptation rather than a claim of exact benchmark reproduction.
    It performs no generation, prompting, fine-tuning, or external API call.
    """

    PAPER_URL = "https://aclanthology.org/2025.coling-main.335/"

    def __init__(self, config: Mapping[str, Any]) -> None:
        self.model_name = normalize_text(
            config.get("attention_model", "BAAI/bge-m3")
        )
        self.revision = normalize_text(config.get("attention_revision"))
        self.device = normalize_text(config.get("attention_device", "cpu")) or "cpu"
        self.dtype = normalize_text(config.get("attention_dtype", "float32")).lower()
        self.max_length = int(config.get("attention_max_length", 256))
        self.candidate_length_normalization_power = float(
            config.get("attention_candidate_length_normalization_power", 0.0)
        )
        if self.max_length < 8:
            raise ValueError("attention_max_length must be at least 8")
        if not 0.0 <= self.candidate_length_normalization_power <= 1.0:
            raise ValueError(
                "attention_candidate_length_normalization_power must be between 0 and 1"
            )
        self._tokenizer = None
        self._model = None

    def _load(self) -> tuple[Any, Any]:
        if self._tokenizer is not None and self._model is not None:
            return self._tokenizer, self._model
        import torch
        from transformers import AutoModel, AutoTokenizer

        dtype_by_name = {
            "float16": torch.float16,
            "fp16": torch.float16,
            "bfloat16": torch.bfloat16,
            "bf16": torch.bfloat16,
            "float32": torch.float32,
            "fp32": torch.float32,
        }
        if self.dtype not in dtype_by_name:
            raise ValueError(f"Unsupported attention dtype: {self.dtype}")
        kwargs: dict[str, Any] = {
            "dtype": dtype_by_name[self.dtype],
            # Eager attention is required because optimized SDPA kernels do not
            # necessarily return per-head attention maps.
            "attn_implementation": "eager",
        }
        tokenizer_kwargs: dict[str, Any] = {}
        if self.revision:
            kwargs["revision"] = self.revision
            tokenizer_kwargs["revision"] = self.revision
        tokenizer = AutoTokenizer.from_pretrained(
            self.model_name,
            **tokenizer_kwargs,
        )
        if not getattr(tokenizer, "is_fast", False):
            raise RuntimeError("Attention-Seeker requires a fast tokenizer for offsets")
        model = AutoModel.from_pretrained(self.model_name, **kwargs)
        model.to(self.device)
        model.eval()
        self._tokenizer = tokenizer
        self._model = model
        return tokenizer, model

    @staticmethod
    def _token_indices(
        candidate: AspectCandidate,
        offsets: Sequence[Sequence[int]],
    ) -> list[int]:
        output: list[int] = []
        for index, offset in enumerate(offsets):
            start, end = int(offset[0]), int(offset[1])
            if start == end:
                continue
            if any(
                start < span_end and end > span_start
                for span_start, span_end in candidate.spans
            ):
                output.append(index)
        return output

    def score(
        self,
        question: str,
        candidates: Sequence[AspectCandidate],
    ) -> dict[tuple[str, str], float]:
        import torch

        tokenizer, model = self._load()
        encoded = tokenizer(
            normalize_text(question),
            return_tensors="pt",
            return_offsets_mapping=True,
            truncation=True,
            max_length=self.max_length,
        )
        offsets = encoded.pop("offset_mapping")[0].tolist()
        model_inputs = {key: value.to(self.device) for key, value in encoded.items()}
        candidate_indices = {
            (_key(candidate.text), candidate.kind): self._token_indices(
                candidate,
                offsets,
            )
            for candidate in candidates
        }
        union = sorted(
            {index for values in candidate_indices.values() for index in values}
        )
        token_count = len(offsets)
        candidate_mask = torch.zeros(token_count, device=self.device, dtype=torch.float32)
        if union:
            candidate_mask[union] = 1.0
        # For an unpadded single sequence this denominator is exactly the paper's
        # token count n. The mask only protects the formula if a padded tokenizer
        # configuration is introduced later; special tokens remain part of n.
        valid_mask = model_inputs["attention_mask"][0].to(dtype=torch.float32)

        with torch.inference_mode():
            output = model(
                **model_inputs,
                output_attentions=True,
                return_dict=True,
            )
            if not output.attentions or any(value is None for value in output.attentions):
                raise RuntimeError("The local encoder did not return attention maps")
            maps = torch.stack([value[0] for value in output.attentions], dim=0)
            token_scores = attention_seeker_token_scores(
                maps,
                candidate_mask,
                valid_mask,
            )

        result: dict[tuple[str, str], float] = {}
        for candidate in candidates:
            key = (_key(candidate.text), candidate.kind)
            indices = candidate_indices[key]
            score = float(token_scores[indices].sum().item()) if indices else 0.0
            if indices and self.candidate_length_normalization_power:
                score /= len(set(indices)) ** self.candidate_length_normalization_power
            orthographic_words = re.findall(r"[가-힣A-Za-z0-9]+", candidate.text)
            if len(orthographic_words) <= 1 and len(candidate.spans) > 1:
                score /= len(candidate.spans)
            result[key] = score
        return result


def _key(text: str) -> str:
    return re.sub(r"\s+", "", normalize_text(text)).lower()


def _unique(values: Sequence[str], limit: int) -> list[str]:
    output: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = normalize_text(value)
        key = _key(text)
        if not text or not key or key in seen:
            continue
        seen.add(key)
        output.append(text)
        if len(output) >= limit:
            break
    return output


class UnsupervisedAspectExtractor:
    """Question-only, label-free aspect candidates for the PCF-first retriever.

    Candidate phrases come from Korean POS structure. Depending on the selected
    variant, ranking uses corpus IDF, question/candidate embedding similarity,
    MMR diversity, or Attention-Seeker self-attention scores. No answer, evidence
    passage, graph node, or Gold identifier is visible here.
    """

    VERSION = "p1u-question-only-v3"

    def __init__(
        self,
        backend: Any,
        config: Mapping[str, Any] | None = None,
        *,
        attention_scorer: Any | None = None,
    ) -> None:
        values = dict(config or {})
        self.backend = backend
        self.kiwi = Kiwi()
        requested = values.get("variants", EMBEDDING_UNSUPERVISED_ASPECT_METHODS)
        self.variants = tuple(str(value) for value in requested)
        unknown = set(self.variants) - set(QUESTION_ONLY_UNSUPERVISED_ASPECT_METHODS)
        if unknown:
            raise ValueError(f"Unknown unsupervised Aspect variants: {sorted(unknown)}")
        if not self.variants:
            raise ValueError("At least one unsupervised Aspect variant is required")
        self.selected_k = int(values.get("selected_k", 5))
        self.candidate_batch_size = int(values.get("candidate_batch_size", 256))
        self.relevance_weight = float(values.get("relevance_weight", 0.85))
        self.idf_weight = float(values.get("idf_weight", 0.15))
        self.mmr_lambda = float(values.get("mmr_lambda", 0.80))
        self.attention_weight = float(values.get("attention_weight", 1.0))
        self.attention_embedding_weight = float(
            values.get("attention_embedding_weight", 0.0)
        )
        self.attention_idf_weight = float(values.get("attention_idf_weight", 0.0))
        self.attention_mmr_lambda = float(values.get("attention_mmr_lambda", 1.0))
        if self.selected_k < 1:
            raise ValueError("unsupervised Aspect selected_k must be positive")
        if self.candidate_batch_size < 1:
            raise ValueError("candidate_batch_size must be positive")
        if self.relevance_weight < 0 or self.idf_weight < 0:
            raise ValueError("EmbedRank weights must be non-negative")
        total = self.relevance_weight + self.idf_weight
        if total <= 0:
            raise ValueError("EmbedRank weights must have a positive sum")
        self.relevance_weight /= total
        self.idf_weight /= total
        if not 0.0 <= self.mmr_lambda <= 1.0:
            raise ValueError("Aspect MMR lambda must be between zero and one")
        attention_total = (
            self.attention_weight
            + self.attention_embedding_weight
            + self.attention_idf_weight
        )
        if min(
            self.attention_weight,
            self.attention_embedding_weight,
            self.attention_idf_weight,
        ) < 0 or attention_total <= 0:
            raise ValueError("Attention hybrid weights must be non-negative and non-zero")
        self.attention_weight /= attention_total
        self.attention_embedding_weight /= attention_total
        self.attention_idf_weight /= attention_total
        if not 0.0 <= self.attention_mmr_lambda <= 1.0:
            raise ValueError("attention_mmr_lambda must be between zero and one")
        self.attention_scorer = attention_scorer
        if P1U_ATTENTION_SEEKER in self.variants and self.attention_scorer is None:
            self.attention_scorer = LocalAttentionSeekerScorer(values)

    @staticmethod
    def _content_term(token: Any) -> str:
        value = normalize_text(token.form).lower()
        return "" if value in STOP_TERMS else value

    def _candidates(self, question: str) -> list[AspectCandidate]:
        text = normalize_text(question)
        tokens = list(self.kiwi.tokenize(text))
        candidates: dict[tuple[str, str], AspectCandidate] = {}
        order = 0

        def add(
            value: str,
            kind: str,
            terms: Sequence[str],
            spans: Sequence[tuple[int, int]] | None = None,
        ) -> None:
            nonlocal order
            phrase = normalize_text(value).strip(".,?!()[]{}\"'")
            normalized_terms = tuple(
                dict.fromkeys(
                    term
                    for term in (normalize_text(item).lower() for item in terms)
                    if term and term not in STOP_TERMS
                )
            )
            phrase_key = _key(phrase)
            if not phrase_key or not normalized_terms:
                return
            if len(phrase_key) < 2 and not any(char.isdigit() for char in phrase_key):
                return
            canonical_key = _key(" ".join(normalized_terms))
            if len(canonical_key) < 2 and not any(
                char.isdigit() for char in canonical_key
            ):
                return
            normalized_spans = tuple(
                dict.fromkeys(
                    (int(start), int(end))
                    for start, end in (spans or ())
                    if 0 <= int(start) < int(end) <= len(text)
                )
            )
            if not normalized_spans:
                normalized_spans = tuple(
                    (match.start(), match.end())
                    for match in re.finditer(re.escape(phrase), text, flags=re.IGNORECASE)
                )
            # Inflected surfaces such as `역량은` and `역량으로` are one
            # retrieval concept. Keep the original span for the attention score,
            # but merge candidates by their canonical content morphemes.
            key = (canonical_key, kind)
            if key in candidates:
                previous = candidates[key]
                candidates[key] = AspectCandidate(
                    text=previous.text,
                    kind=previous.kind,
                    terms=previous.terms,
                    order=previous.order,
                    spans=tuple(dict.fromkeys((*previous.spans, *normalized_spans))),
                )
                return
            candidates[key] = AspectCandidate(
                text=phrase,
                kind=kind,
                terms=normalized_terms,
                order=order,
                spans=normalized_spans,
            )
            order += 1

        def surface(chunk: Sequence[Any]) -> str:
            start = int(chunk[0].start)
            end = int(chunk[-1].start + chunk[-1].len)
            return text[start:end]

        def token_span(chunk: Sequence[Any]) -> tuple[int, int]:
            return (
                int(chunk[0].start),
                int(chunk[-1].start + chunk[-1].len),
            )

        noun_runs: list[list[Any]] = []
        current: list[Any] = []
        for token in tokens:
            if token.tag in NOMINAL_TAGS or token.tag in NOMINAL_AFFIX_TAGS:
                current.append(token)
            else:
                if current:
                    noun_runs.append(current)
                    current = []
        if current:
            noun_runs.append(current)

        for run in noun_runs:
            content = [token for token in run if self._content_term(token)]
            if not content:
                continue
            add(
                surface(run),
                "domain",
                [self._content_term(token) for token in content],
                [token_span(run)],
            )
            base_positions = [
                index for index, token in enumerate(run) if self._content_term(token)
            ]
            for size in (1, 2, 3):
                for offset in range(0, len(base_positions) - size + 1):
                    first = base_positions[offset]
                    last = base_positions[offset + size - 1]
                    chunk = run[first : last + 1]
                    add(
                        surface(chunk),
                        "domain",
                        [self._content_term(token) for token in chunk],
                        [token_span(chunk)],
                    )

        for index, token in enumerate(tokens):
            form = self._content_term(token)
            if token.tag in VERBAL_SUFFIX_TAGS and index > 0:
                previous = tokens[index - 1]
                previous_form = self._content_term(previous)
                if previous_form and previous.tag in NOMINAL_TAGS:
                    add(
                        surface([previous]),
                        "action",
                        [previous_form],
                        [token_span([previous])],
                    )
            if token.tag.startswith(VERBAL_TAG_PREFIXES) and form:
                add(
                    token.form,
                    "action",
                    [form],
                    [token_span([token])],
                )
                prior = [
                    item
                    for item in tokens[max(0, index - 4) : index]
                    if item.tag in NOMINAL_TAGS and self._content_term(item)
                ]
                if prior:
                    nearest = prior[-2:]
                    add(
                        " ".join([*(item.form for item in nearest), token.form]),
                        "action",
                        [*(self._content_term(item) for item in nearest), form],
                        [token_span([item]) for item in (*nearest, token)],
                    )

            marker = normalize_text(token.form)
            if marker in CONSTRAINT_MARKERS or token.tag == "SN":
                nearby = []
                for item in tokens[max(0, index - 3) : min(len(tokens), index + 3)]:
                    term = self._content_term(item)
                    if term and (
                        item.tag in NOMINAL_TAGS
                        or item.tag in NOMINAL_AFFIX_TAGS
                        or item.tag.startswith(VERBAL_TAG_PREFIXES)
                    ):
                        nearby.append(item)
                if nearby:
                    nearby = nearby[-4:]
                    add(
                        surface(nearby),
                        "constraint",
                        [self._content_term(item) for item in nearby],
                        [token_span(nearby)],
                    )

        # Orthographic word candidates recover surface forms when morphological
        # ambiguity splits a domain word unexpectedly (for example, 제안). The POS
        # analysis still gates each word, so particles and interrogatives alone do
        # not become candidates.
        for match in re.finditer(r"[가-힣A-Za-z0-9]+(?:/[A-Za-z0-9]+)*", text):
            word = match.group(0)
            analyzed = list(self.kiwi.tokenize(word))
            terms = [
                self._content_term(item)
                for item in analyzed
                if item.tag in NOMINAL_TAGS
                or item.tag.startswith(VERBAL_TAG_PREFIXES)
            ]
            terms = [term for term in terms if term]
            has_nominal = any(item.tag in NOMINAL_TAGS for item in analyzed)
            if has_nominal and terms:
                span = (match.start(), match.end())
                add(word, "domain", terms, [span])

        for match in re.finditer(
            r"[A-Za-z][A-Za-z0-9]*(?:\s*/\s*[A-Za-z0-9]+)+|[A-Za-z]{2,}",
            text,
        ):
            add(
                match.group(0),
                "domain",
                [match.group(0).lower()],
                [(match.start(), match.end())],
            )

        # Preserve clause-level information needs for long or multi-intent
        # questions. Token-level salience alone otherwise over-selects several
        # overlapping phrases from the first clause.
        clause_matches = list(re.finditer(r"[^,;?!]+", text))
        for match in clause_matches:
            clause = normalize_text(match.group(0))
            analyzed = list(self.kiwi.tokenize(clause))
            terms = [
                self._content_term(token)
                for token in analyzed
                if token.tag in NOMINAL_TAGS
                or token.tag.startswith(VERBAL_TAG_PREFIXES)
            ]
            terms = [term for term in terms if term]
            if len(set(terms)) >= 2 and (
                len(clause_matches) > 1 or len(set(terms)) >= 6
            ):
                add(
                    clause,
                    "intent",
                    terms,
                    [(match.start(), match.end())],
                )

        return list(candidates.values())

    def _question_terms(self, question: str) -> set[str]:
        return {
            term
            for token in self.kiwi.tokenize(normalize_text(question))
            if (term := self._content_term(token))
            and (
                token.tag in NOMINAL_TAGS
                or token.tag in NOMINAL_AFFIX_TAGS
                or token.tag.startswith(VERBAL_TAG_PREFIXES)
            )
        }

    @staticmethod
    def _cosine(left: np.ndarray, right: np.ndarray) -> float:
        return float(np.clip(left @ right, -1.0, 1.0))

    @staticmethod
    def _minmax(
        values: Mapping[tuple[str, str], float],
    ) -> dict[tuple[str, str], float]:
        if not values:
            return {}
        minimum = min(values.values())
        maximum = max(values.values())
        span = maximum - minimum
        if span <= 1e-12:
            return {key: 1.0 for key in values}
        return {key: (value - minimum) / span for key, value in values.items()}

    def _rank(
        self,
        candidates: Sequence[AspectCandidate],
        vectors: Mapping[str, np.ndarray] | None,
        question_vector: np.ndarray | None,
        idf: Mapping[str, float],
        *,
        variant: str,
        attention_scores: Mapping[tuple[str, str], float] | None = None,
    ) -> tuple[list[AspectCandidate], dict[tuple[str, str], float]]:
        if not candidates:
            return [], {}
        maximum_idf = max(idf.values(), default=1.0)
        minimum_idf = min(idf.values(), default=0.0)
        span = max(maximum_idf - minimum_idf, 1e-9)
        idf_features: dict[tuple[str, str], float] = {}
        embedding_features: dict[tuple[str, str], float] = {}
        attention_features: dict[tuple[str, str], float] = {}
        for candidate in candidates:
            key = (_key(candidate.text), candidate.kind)
            values = [idf.get(term, maximum_idf) for term in candidate.terms]
            idf_score = sum((value - minimum_idf) / span for value in values) / len(values)
            idf_features[key] = idf_score
            if vectors is not None and question_vector is not None:
                embedding_features[key] = max(
                    0.0,
                    self._cosine(
                        question_vector,
                        vectors[_key(candidate.query_text)],
                    ),
                )
            if attention_scores is not None:
                attention_features[key] = float(attention_scores.get(key, 0.0))

        base: dict[tuple[str, str], float] = {}
        if variant == P1U_ATTENTION_SEEKER:
            if attention_scores is None:
                raise RuntimeError("Attention-Seeker scores are missing")
            normalized_attention = self._minmax(attention_features)
            normalized_embedding = self._minmax(embedding_features)
            for candidate in candidates:
                key = (_key(candidate.text), candidate.kind)
                base[key] = (
                    self.attention_weight * normalized_attention[key]
                    + self.attention_embedding_weight
                    * normalized_embedding.get(key, 0.0)
                    + self.attention_idf_weight * idf_features[key]
                )
        else:
            for candidate in candidates:
                key = (_key(candidate.text), candidate.kind)
                length_bonus = 0.03 * min(2, max(0, len(candidate.terms) - 1))
                if variant == P1U_TFIDF:
                    score = idf_features[key] + length_bonus
                else:
                    if vectors is None or question_vector is None:
                        raise RuntimeError("EmbedRank vectors are missing")
                    score = (
                        self.relevance_weight * embedding_features[key]
                        + self.idf_weight * idf_features[key]
                        + length_bonus
                    )
                base[key] = float(score)

        ordered = sorted(
            candidates,
            key=lambda item: (
                -base[(_key(item.text), item.kind)],
                -len(item.terms),
                item.order,
                item.text,
            ),
        )
        ranking_mmr_lambda = (
            self.mmr_lambda
            if variant == P1U_EMBEDRANK_MMR
            else self.attention_mmr_lambda
            if variant == P1U_ATTENTION_SEEKER
            else 1.0
        )
        if ranking_mmr_lambda >= 1.0:
            return ordered, base
        if vectors is None:
            raise RuntimeError("Aspect MMR requires candidate embeddings")

        selected: list[AspectCandidate] = []
        remaining = list(ordered)
        while remaining:
            best: AspectCandidate | None = None
            best_key: tuple[float, float, int, int, str] | None = None
            for candidate in remaining:
                candidate_key = (_key(candidate.text), candidate.kind)
                redundancy = 0.0
                candidate_terms = set(candidate.terms)
                for chosen in selected:
                    chosen_terms = set(chosen.terms)
                    lexical_overlap = len(candidate_terms & chosen_terms) / max(
                        1,
                        min(len(candidate_terms), len(chosen_terms)),
                    )
                    semantic_overlap = max(
                        0.0,
                        self._cosine(
                            vectors[_key(candidate.query_text)],
                            vectors[_key(chosen.query_text)],
                        ),
                    )
                    redundancy = max(
                        redundancy,
                        lexical_overlap,
                        semantic_overlap,
                    )
                mmr = ranking_mmr_lambda * base[candidate_key] - (
                    1.0 - ranking_mmr_lambda
                ) * redundancy
                tie = (
                    mmr,
                    base[candidate_key],
                    len(candidate.terms),
                    -candidate.order,
                    candidate.text,
                )
                if best_key is None or tie > best_key:
                    best_key = tie
                    best = candidate
            assert best is not None
            selected.append(best)
            remaining.remove(best)
        return selected, base

    def _profile(
        self,
        question: str,
        ranked: Sequence[AspectCandidate],
        scores: Mapping[tuple[str, str], float],
        *,
        variant: str,
    ) -> dict[str, Any]:
        selected = list(ranked[: self.selected_k])
        selected_first = [*selected, *ranked]
        domains = [item.query_text for item in selected_first if item.kind == "domain"]
        actions = [item.query_text for item in selected_first if item.kind == "action"]
        constraints = [
            item.query_text for item in selected_first if item.kind == "constraint"
        ]
        intents = [item.query_text for item in selected_first if item.kind == "intent"]
        selected_texts = [item.query_text for item in selected]
        fallback = selected_texts[:1]

        pcf_terms = _unique(domains[:3] + intents[:1] + actions[:1] + selected_texts, 5)
        taskframe_terms = _unique(actions[:2] + intents[:2] + domains[:2] + selected_texts, 5)
        fact_terms = _unique(
            constraints[:2] + intents[:2] + actions[:2] + domains[:2] + selected_texts,
            6,
        )
        rerank_terms = _unique(
            intents[:2]
            + constraints[:2]
            + [value for value in actions if len(value.split()) >= 2]
            + [value for value in domains if len(value.split()) >= 2]
            + [
                value
                for value in selected_texts
                if len(value.split()) >= 2 or len(_key(value)) >= 5
            ],
            5,
        )
        marker_groups = {
            "constraint": (
                " 경우",
                " 전",
                " 후",
                " 때",
                "부터",
                "까지",
                "이상",
                "이하",
                "예외",
            ),
            "comparison": ("차이", "다르", "비교", "보다", "각각"),
            "multi_intent": (" 및 ", "그리고", "동시에", "며,", "고,"),
        }
        normalized_question = f" {normalize_text(question)} "
        marker_hits = {
            name: any(marker in normalized_question for marker in markers)
            for name, markers in marker_groups.items()
        }
        distinct_kinds = len({item.kind for item in selected if item.kind != "intent"})
        applicability_score = min(
            1.0,
            0.15
            + 0.20 * (distinct_kinds >= 2)
            + 0.20 * bool(constraints)
            + 0.15 * marker_hits["comparison"]
            + 0.20 * marker_hits["multi_intent"]
            + 0.10 * (len(normalized_question) >= 45),
        )
        return {
            "domain_objects": _unique(domains, 8) or fallback,
            "actions": _unique(actions, 6) or fallback,
            "constraints": _unique(constraints, 6),
            "desired_information": _unique(selected_texts, 4),
            "search_terms": _unique(selected_texts, self.selected_k),
            "rerank_terms": rerank_terms or _unique(selected_texts, 3),
            "stage_terms": {
                "pcf": pcf_terms or fallback,
                "taskframe": taskframe_terms or fallback,
                "fact": fact_terms or fallback,
            },
            "applicability": {
                "score": applicability_score,
                "recommended": applicability_score >= 0.35,
                "marker_hits": marker_hits,
                "distinct_selected_kinds": distinct_kinds,
            },
            "rationale": (
                "question-only POS candidates ranked without labels, answers, evidence, "
                "graph nodes, or Gold identifiers"
            ),
            "extractor": {
                "version": self.VERSION,
                "variant": variant,
                "selected_k": self.selected_k,
                "relevance_weight": self.relevance_weight,
                "idf_weight": self.idf_weight,
                "mmr_lambda": self.mmr_lambda if variant == P1U_EMBEDRANK_MMR else None,
                "attention_hybrid_weights": (
                    {
                        "attention": self.attention_weight,
                        "embedding": self.attention_embedding_weight,
                        "idf": self.attention_idf_weight,
                    }
                    if variant == P1U_ATTENTION_SEEKER
                    else None
                ),
                "attention_mmr_lambda": (
                    self.attention_mmr_lambda
                    if variant == P1U_ATTENTION_SEEKER
                    else None
                ),
                "paper": (
                    {
                        "name": "Attention-Seeker",
                        "venue": "COLING 2025",
                        "url": LocalAttentionSeekerScorer.PAPER_URL,
                        "reproduction_scope": (
                            "short-document equations 3-5 adapted to Kiwi candidates "
                            "and a local multilingual encoder"
                        ),
                    }
                    if variant == P1U_ATTENTION_SEEKER
                    else None
                ),
                "selected": [
                    {
                        "text": item.text,
                        "query_text": item.query_text,
                        "kind": item.kind,
                        "score": scores.get((_key(item.text), item.kind), 0.0),
                    }
                    for item in selected
                ],
            },
        }

    def extract_many(
        self, rows: Sequence[Mapping[str, Any]]
    ) -> list[dict[str, Any]]:
        questions = [normalize_text(row["question"]) for row in rows]
        candidates_by_qid = {
            str(row["qa_id"]): self._candidates(question)
            for row, question in zip(rows, questions)
        }
        document_frequency: Counter[str] = Counter()
        for question in questions:
            document_frequency.update(self._question_terms(question))
        count = max(1, len(questions))
        idf = {
            term: math.log((count + 1.0) / (frequency + 1.0)) + 1.0
            for term, frequency in document_frequency.items()
        }

        candidate_texts = _unique(
            [
                candidate.query_text
                for candidates in candidates_by_qid.values()
                for candidate in candidates
            ],
            limit=sum(len(values) for values in candidates_by_qid.values()) or 1,
        )
        needs_embedding_ranking = bool(
            {P1U_EMBEDRANK, P1U_EMBEDRANK_MMR} & set(self.variants)
        ) or (
            P1U_ATTENTION_SEEKER in self.variants
            and (
                self.attention_embedding_weight > 0
                or self.attention_mmr_lambda < 1.0
            )
        )
        candidate_vectors: dict[str, np.ndarray] = {}
        question_values: Sequence[Sequence[float] | None]
        if needs_embedding_ranking:
            candidate_values = self.backend.embed(
                candidate_texts,
                batch_size=self.candidate_batch_size,
                input_type="document",
            )
            candidate_vectors = {
                _key(text): np.asarray(vector, dtype=np.float32)
                for text, vector in zip(candidate_texts, candidate_values)
            }
            question_values = self.backend.embed(
                questions,
                batch_size=self.candidate_batch_size,
                input_type="query",
            )
        else:
            question_values = [None] * len(questions)

        output: list[dict[str, Any]] = []
        for row, question, question_value in zip(rows, questions, question_values):
            qid = str(row["qa_id"])
            candidates = candidates_by_qid[qid]
            if not candidates:
                fallback = AspectCandidate(
                    question,
                    "domain",
                    (question,),
                    0,
                    ((0, len(question)),),
                )
                candidates = [fallback]
                if (
                    needs_embedding_ranking
                    and _key(fallback.query_text) not in candidate_vectors
                ):
                    candidate_vectors[_key(fallback.query_text)] = np.asarray(
                        self.backend.embed(
                            [fallback.query_text],
                            batch_size=1,
                            input_type="document",
                        )[0],
                        dtype=np.float32,
                    )
            attention_scores = None
            if P1U_ATTENTION_SEEKER in self.variants:
                if self.attention_scorer is None:
                    raise RuntimeError("Attention-Seeker scorer is not configured")
                attention_scores = self.attention_scorer.score(question, candidates)
            variants: dict[str, Any] = {}
            for variant in self.variants:
                ranked, scores = self._rank(
                    candidates,
                    candidate_vectors if needs_embedding_ranking else None,
                    (
                        np.asarray(question_value, dtype=np.float32)
                        if question_value is not None
                        else None
                    ),
                    idf,
                    variant=variant,
                    attention_scores=attention_scores,
                )
                variants[variant] = self._profile(
                    question,
                    ranked,
                    scores,
                    variant=variant,
                )
            output.append(
                {
                    "qid": qid,
                    "question": question,
                    "variants": variants,
                    "extractor_version": self.VERSION,
                }
            )
        return output


class PCFGroundedAspectExtractor(UnsupervisedAspectExtractor):
    """Route graph-grounded, information-bearing Aspects to direct search.

    This is the project-specific P1-G extractor.  It does not use transformer
    attention, an LLM prompt, labels, answers, or Gold evidence.  Korean
    linguistic candidates are probed against PCFProcess, TaskFrame, and
    EvidenceSpan indices.  Five candidate rankings are fused with an unweighted
    reciprocal-rank sum, so there are no learned or hand-tuned feature weights.
    A deterministic role-and-specificity rule then routes answer intents and
    explicit constraints first, followed by multiword actions/domain objects;
    the grounded ranking fills any remaining slots.  This prevents a generic
    unigram from displacing a more informative phrase without introducing a
    numeric score weight.

    The five signals are: question relevance, PCF support, TaskFrame support,
    EvidenceSpan support, and stored-edge path consistency.  ``selected_k`` is
    the only method-specific configurable value.
    """

    VERSION = "p1g-pcf-grounded-role-routing-v2"
    PROBE_K = 3
    SIGNAL_NAMES = (
        "question_relevance",
        "pcf_support",
        "taskframe_support",
        "evidence_support",
        "path_consistency",
    )

    def __init__(
        self,
        backend: Any,
        graph: Any,
        config: Mapping[str, Any] | None = None,
    ) -> None:
        # Reuse only the project's Korean linguistic candidate generator and
        # profile formatter.  The TF-IDF variant below is never executed.
        values = dict(config or {})
        values["variants"] = [P1U_TFIDF]
        super().__init__(backend, values)
        self.graph = graph

        self._frame_pcfs: dict[str, set[str]] = {}
        for frame_id, mappings in graph.mappings_by_tf.items():
            self._frame_pcfs[frame_id] = {
                str(item["pcf_id"])
                for item in mappings
                if item.get("pcf_id")
            }

        self._evidence_frames: dict[str, set[str]] = {}
        for mention in graph.taskmentions.values():
            frame_id = normalize_text(mention.get("_taskframe_id"))
            for evidence_id in mention.get("_evidence_ids", []):
                if frame_id:
                    self._evidence_frames.setdefault(str(evidence_id), set()).add(
                        frame_id
                    )
        for fact in graph.facts.values():
            frame_ids = {
                normalize_text(link.get("taskframe_id"))
                for link in fact.get("_frame_links", [])
                if normalize_text(link.get("taskframe_id"))
            }
            for evidence_id in fact.get("_evidence_ids", []):
                self._evidence_frames.setdefault(str(evidence_id), set()).update(
                    frame_ids
                )

    @staticmethod
    def _top(scores: Mapping[str, float], limit: int) -> list[tuple[str, float]]:
        return sorted(scores.items(), key=lambda item: (-float(item[1]), item[0]))[
            :limit
        ]

    @staticmethod
    def _dense_descending_ranks(
        values: Mapping[tuple[str, str], float],
    ) -> dict[tuple[str, str], int]:
        """Assign equal values an equal rank; the next distinct value gets +1."""
        distinct = sorted({float(value) for value in values.values()}, reverse=True)
        rank_by_value = {value: index for index, value in enumerate(distinct, start=1)}
        return {key: rank_by_value[float(value)] for key, value in values.items()}

    def _pcf_match(self, left: str, right: str) -> bool:
        if left == right:
            return True
        distance = self.graph.pcf_distance(left, right)
        return distance is not None and distance <= 2

    def _path_consistency(
        self,
        pcfs: Sequence[tuple[str, float]],
        frames: Sequence[tuple[str, float]],
        evidence: Sequence[tuple[str, float]],
    ) -> tuple[float, float, float]:
        """Return equal-weight PCF↔TaskFrame and TaskFrame↔Evidence agreement."""
        pcf_frame = 0.0
        for pcf_rank, (pcf_id, _) in enumerate(pcfs, start=1):
            for frame_rank, (frame_id, _) in enumerate(frames, start=1):
                if any(
                    self._pcf_match(pcf_id, mapped_pcf)
                    for mapped_pcf in self._frame_pcfs.get(frame_id, set())
                ):
                    pcf_frame = max(
                        pcf_frame,
                        1.0 / (pcf_rank * frame_rank),
                    )

        frame_evidence = 0.0
        for frame_rank, (frame_id, _) in enumerate(frames, start=1):
            for evidence_rank, (evidence_id, _) in enumerate(evidence, start=1):
                if frame_id in self._evidence_frames.get(evidence_id, set()):
                    frame_evidence = max(
                        frame_evidence,
                        1.0 / (frame_rank * evidence_rank),
                    )
        return (
            0.5 * (pcf_frame + frame_evidence),
            pcf_frame,
            frame_evidence,
        )

    def _candidate_signals(
        self,
        question_vector: np.ndarray,
        candidate: AspectCandidate,
        candidate_vector: np.ndarray,
    ) -> dict[str, Any]:
        pcf_scores = self.graph.group_scores(
            "pcf",
            candidate_vector,
            {"identity": 0.35, "description": 0.45, "path": 0.20},
            condition="D0_ORIGINAL",
        )
        frame_scores = self.graph.group_scores(
            "taskframe",
            candidate_vector,
            {
                "identity": 0.25,
                "definition": 0.25,
                "aliases": 0.15,
                "evidence": 0.35,
            },
            condition="D0_ORIGINAL",
        )
        evidence_scores = self.graph.evidence_hybrid_scores(
            candidate.query_text,
            candidate_vector,
        )
        pcfs = self._top(pcf_scores, self.PROBE_K)
        frames = self._top(frame_scores, self.PROBE_K)
        evidence = self._top(evidence_scores, self.PROBE_K)
        consistency, pcf_frame, frame_evidence = self._path_consistency(
            pcfs,
            frames,
            evidence,
        )
        return {
            "question_relevance": max(
                0.0,
                self._cosine(question_vector, candidate_vector),
            ),
            "pcf_support": max((value for _, value in pcfs), default=0.0),
            "taskframe_support": max((value for _, value in frames), default=0.0),
            "evidence_support": max((value for _, value in evidence), default=0.0),
            "path_consistency": consistency,
            "pcf_taskframe_consistency": pcf_frame,
            "taskframe_evidence_consistency": frame_evidence,
            "top_pcf_ids": [node_id for node_id, _ in pcfs],
            "top_taskframe_ids": [node_id for node_id, _ in frames],
            "top_evidence_ids": [node_id for node_id, _ in evidence],
        }

    @staticmethod
    def _redundant(
        candidate: AspectCandidate,
        selected: Sequence[AspectCandidate],
    ) -> bool:
        terms = set(candidate.terms)
        for chosen in selected:
            chosen_terms = set(chosen.terms)
            if terms == chosen_terms:
                return True
            # A shorter phrase adds no new concept when it is wholly contained
            # in an already selected phrase of the same linguistic role.
            if candidate.kind == chosen.kind and terms < chosen_terms:
                return True
        return False

    def _rank_grounded(
        self,
        question: str,
        candidates: Sequence[AspectCandidate],
        question_vector: np.ndarray,
        candidate_vectors: Mapping[str, np.ndarray],
    ) -> tuple[
        list[AspectCandidate],
        dict[tuple[str, str], float],
        dict[tuple[str, str], dict[str, Any]],
    ]:
        signals: dict[tuple[str, str], dict[str, Any]] = {}
        for candidate in candidates:
            key = (_key(candidate.text), candidate.kind)
            signals[key] = self._candidate_signals(
                question_vector,
                candidate,
                candidate_vectors[_key(candidate.query_text)],
            )

        per_signal_ranks = {
            name: self._dense_descending_ranks(
                {key: float(value[name]) for key, value in signals.items()}
            )
            for name in self.SIGNAL_NAMES
        }
        # Parameter-free, equal-contribution reciprocal-rank fusion.  Dividing by
        # the signal count keeps the score in (0, 1] without changing order.
        scores = {
            key: sum(1.0 / per_signal_ranks[name][key] for name in self.SIGNAL_NAMES)
            / len(self.SIGNAL_NAMES)
            for key in signals
        }
        ordered = sorted(
            candidates,
            key=lambda item: (
                -scores[(_key(item.text), item.kind)],
                -len(item.terms),
                item.order,
                item.text,
            ),
        )
        diverse: list[AspectCandidate] = []
        for candidate in ordered:
            if not self._redundant(candidate, diverse):
                diverse.append(candidate)
            if len(diverse) >= self.selected_k:
                break
        if len(diverse) < self.selected_k:
            for candidate in ordered:
                if candidate not in diverse:
                    diverse.append(candidate)
                if len(diverse) >= self.selected_k:
                    break
        return [*diverse, *(item for item in ordered if item not in diverse)], scores, signals

    def extract_many(
        self,
        rows: Sequence[Mapping[str, Any]],
    ) -> list[dict[str, Any]]:
        questions = [normalize_text(row["question"]) for row in rows]
        candidates_by_qid = {
            str(row["qa_id"]): self._candidates(question)
            for row, question in zip(rows, questions)
        }
        for row, question in zip(rows, questions):
            qid = str(row["qa_id"])
            if not candidates_by_qid[qid]:
                candidates_by_qid[qid] = [
                    AspectCandidate(
                        question,
                        "domain",
                        (question,),
                        0,
                        ((0, len(question)),),
                    )
                ]

        candidate_texts = _unique(
            [
                candidate.query_text
                for candidates in candidates_by_qid.values()
                for candidate in candidates
            ],
            limit=sum(len(values) for values in candidates_by_qid.values()) or 1,
        )
        candidate_values = self.backend.embed(
            candidate_texts,
            batch_size=self.candidate_batch_size,
            input_type="query",
        )
        candidate_vectors = {
            _key(text): np.asarray(vector, dtype=np.float32)
            for text, vector in zip(candidate_texts, candidate_values)
        }
        question_values = self.backend.embed(
            questions,
            batch_size=self.candidate_batch_size,
            input_type="query",
        )

        output: list[dict[str, Any]] = []
        for row, question, question_value in zip(rows, questions, question_values):
            qid = str(row["qa_id"])
            ranked, scores, signals = self._rank_grounded(
                question,
                candidates_by_qid[qid],
                np.asarray(question_value, dtype=np.float32),
                candidate_vectors,
            )
            profile = self._profile(
                question,
                ranked,
                scores,
                variant=P1G_PCF_GROUNDED,
            )
            grounded_top = ranked[: self.selected_k]
            # `_profile` deterministically orders answer intents, constraints,
            # multiword actions/domain objects, and finally score-ranked
            # backfill.  Materialize the first K values as the method's actual
            # routed Aspects so telemetry, documentation, and executed queries
            # cannot diverge.
            routed_queries = _unique(
                profile.get("rerank_terms", []),
                self.selected_k,
            )
            by_query: dict[str, AspectCandidate] = {}
            for item in ranked:
                by_query.setdefault(_key(item.query_text), item)
            routed = [
                by_query[_key(query)]
                for query in routed_queries
                if _key(query) in by_query
            ]
            profile["search_terms"] = routed_queries
            profile["rerank_terms"] = routed_queries
            profile["rationale"] = (
                "Korean linguistic candidates scored by equal-weight rank fusion of "
                "question relevance, PCF support, TaskFrame support, EvidenceSpan "
                "support, and stored-edge path consistency, then routed by a "
                "deterministic role-and-specificity rule; no LLM, attention, labels, "
                "answers, or Gold identifiers"
            )
            profile["extractor"] = {
                "name": "PCF-Grounded Aspect Routing (P1-G)",
                "version": self.VERSION,
                "variant": P1G_PCF_GROUNDED,
                "selected_k": self.selected_k,
                "aggregation": "equal_weight_reciprocal_rank_sum",
                "signal_names": list(self.SIGNAL_NAMES),
                "probe_k": self.PROBE_K,
                "trainable_parameters": 0,
                "routing_rule": (
                    "intent_then_constraint_then_multiword_action_domain_"
                    "then_grounded_rank_backfill"
                ),
                "selected": [
                    {
                        "text": item.text,
                        "query_text": item.query_text,
                        "kind": item.kind,
                        "score": scores[(_key(item.text), item.kind)],
                        "signals": signals[(_key(item.text), item.kind)],
                    }
                    for item in routed
                ],
                "grounded_top": [
                    {
                        "text": item.text,
                        "query_text": item.query_text,
                        "kind": item.kind,
                        "score": scores[(_key(item.text), item.kind)],
                    }
                    for item in grounded_top
                ],
            }
            output.append(
                {
                    "qid": qid,
                    "question": question,
                    "variants": {P1G_PCF_GROUNDED: profile},
                    "extractor_version": self.VERSION,
                }
            )
        return output
