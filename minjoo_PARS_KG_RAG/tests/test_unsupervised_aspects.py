from __future__ import annotations

import hashlib
import math
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from kg_rag.openai_backend import OpenAIBackend
from kg_rag.retrieval import GraphIndex
from kg_rag.unsupervised_aspects import (
    EMBEDDING_UNSUPERVISED_ASPECT_METHODS,
    P1G_PCF_GROUNDED,
    P1U_ATTENTION_SEEKER,
    P1U_EMBEDRANK_MMR,
    PCFGroundedAspectExtractor,
    UnsupervisedAspectExtractor,
    attention_seeker_token_scores,
)


class _DeterministicBackend:
    def __init__(self) -> None:
        self.calls: list[tuple[list[str], str]] = []

    @staticmethod
    def _vector(text: str) -> list[float]:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        values = np.asarray([1.0 + digest[index] for index in range(8)], dtype=np.float32)
        values /= np.linalg.norm(values)
        return values.tolist()

    def embed(self, texts, *, batch_size=64, input_type="document"):
        values = list(texts)
        self.calls.append((values, input_type))
        return [self._vector(text) for text in values]


class _FakeSentenceTransformer:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def encode(self, texts, **kwargs):
        self.calls.append({"texts": list(texts), **kwargs})
        return np.asarray([[3.0, 4.0, 0.0] for _ in texts], dtype=np.float32)


class _FakeAttentionScorer:
    def __init__(self) -> None:
        self.calls: list[tuple[str, int]] = []

    def score(self, question, candidates):
        self.calls.append((question, len(candidates)))
        return {
            (candidate.text.replace(" ", "").lower(), candidate.kind): float(
                len(candidate.terms) * 100 - candidate.order
            )
            for candidate in candidates
        }


class _FakeGraph:
    def __init__(self) -> None:
        self.mappings_by_tf = {"TF1": [{"pcf_id": "PCF1"}]}
        self.taskmentions = {
            "TM1": {
                "_taskframe_id": "TF1",
                "_evidence_ids": ["EV1"],
            }
        }
        self.facts = {
            "F1": {
                "_frame_links": [{"taskframe_id": "TF1"}],
                "_evidence_ids": ["EV1"],
            }
        }

    @staticmethod
    def group_scores(kind, query_vector, weights, *, condition):
        del query_vector, weights, condition
        if kind == "pcf":
            return {"PCF1": 0.9, "PCF2": 0.2}
        if kind == "taskframe":
            return {"TF1": 0.8, "TF2": 0.1}
        raise AssertionError(kind)

    @staticmethod
    def evidence_hybrid_scores(question, query_vector):
        del question, query_vector
        return {"EV1": 0.85, "EV2": 0.15}

    @staticmethod
    def pcf_distance(left, right):
        return 0 if left == right else 4


class UnsupervisedAspectTests(unittest.TestCase):
    def test_pcf_grounded_extractor_uses_equal_rank_signals_without_gold(self) -> None:
        backend = _DeterministicBackend()
        extractor = PCFGroundedAspectExtractor(
            backend,
            _FakeGraph(),
            {"selected_k": 3},
        )
        rows = [
            {
                "qa_id": "Q1",
                "question": "제안서 작성 전에 고객 요구조건을 어떻게 확인하나요?",
                "answer": "추출기가 보면 안 되는 정답",
                "evidence_text": "추출기가 보면 안 되는 Gold 근거",
            }
        ]

        result = extractor.extract_many(rows)

        profile = result[0]["variants"][P1G_PCF_GROUNDED]
        metadata = profile["extractor"]
        self.assertEqual(metadata["trainable_parameters"], 0)
        self.assertEqual(metadata["aggregation"], "equal_weight_reciprocal_rank_sum")
        self.assertEqual(
            set(metadata["signal_names"]),
            {
                "question_relevance",
                "pcf_support",
                "taskframe_support",
                "evidence_support",
                "path_consistency",
            },
        )
        self.assertLessEqual(len(metadata["selected"]), 3)
        self.assertLessEqual(len(metadata["grounded_top"]), 3)
        self.assertEqual(
            metadata["routing_rule"],
            "intent_then_constraint_then_multiword_action_domain_"
            "then_grounded_rank_backfill",
        )
        self.assertTrue(profile["rerank_terms"])
        self.assertEqual(
            profile["rerank_terms"],
            [item["query_text"] for item in metadata["selected"]],
        )
        self.assertEqual(profile["search_terms"], profile["rerank_terms"])
        serialized = repr(result)
        self.assertNotIn("보면 안 되는 정답", serialized)
        self.assertNotIn("보면 안 되는 Gold 근거", serialized)
        self.assertTrue(
            all(role == "query" for _, role in backend.calls),
            backend.calls,
        )

    def test_extracts_all_fixed_variants_without_answer_or_evidence(self) -> None:
        backend = _DeterministicBackend()
        extractor = UnsupervisedAspectExtractor(
            backend,
            {
                "selected_k": 5,
                "relevance_weight": 0.85,
                "idf_weight": 0.15,
                "mmr_lambda": 0.8,
            },
        )
        rows = [
            {
                "qa_id": "Q1",
                "question": "제안서 작성 전에 고객 요구조건을 어떻게 확인하나요?",
                "answer": "추출기가 보아서는 안 되는 정답",
                "evidence_text": "추출기가 보아서는 안 되는 근거",
            },
            {
                "qa_id": "Q2",
                "question": "RFP 발행 후 수주 전략은 어떻게 달라지나요?",
                "answer": "비공개 정답",
                "evidence_text": "비공개 근거",
            },
        ]

        first = extractor.extract_many(rows)
        second = extractor.extract_many(rows)

        self.assertEqual(first, second)
        self.assertEqual(
            set(first[0]["variants"]),
            set(EMBEDDING_UNSUPERVISED_ASPECT_METHODS),
        )
        profile = first[0]["variants"][P1U_EMBEDRANK_MMR]
        self.assertTrue(profile["domain_objects"])
        self.assertTrue(profile["actions"])
        self.assertTrue(profile["stage_terms"]["pcf"])
        self.assertTrue(profile["stage_terms"]["taskframe"])
        self.assertTrue(profile["stage_terms"]["fact"])
        serialized = repr(first)
        self.assertNotIn("보아서는 안 되는 정답", serialized)
        self.assertNotIn("보아서는 안 되는 근거", serialized)
        self.assertIn("query", {role for _, role in backend.calls})
        self.assertIn("document", {role for _, role in backend.calls})

    def test_attention_seeker_equations_match_naive_reference(self) -> None:
        import torch

        attentions = torch.tensor(
            [
                [
                    [
                        [0.1, 0.2, 0.3, 0.4],
                        [0.4, 0.3, 0.2, 0.1],
                        [0.25, 0.25, 0.25, 0.25],
                        [0.3, 0.1, 0.4, 0.2],
                    ],
                    [
                        [0.4, 0.3, 0.2, 0.1],
                        [0.1, 0.2, 0.3, 0.4],
                        [0.2, 0.4, 0.1, 0.3],
                        [0.25, 0.25, 0.25, 0.25],
                    ],
                ],
                [
                    [
                        [0.2, 0.2, 0.2, 0.4],
                        [0.3, 0.2, 0.4, 0.1],
                        [0.1, 0.5, 0.2, 0.2],
                        [0.4, 0.1, 0.1, 0.4],
                    ],
                    [
                        [0.3, 0.3, 0.1, 0.3],
                        [0.2, 0.1, 0.5, 0.2],
                        [0.4, 0.2, 0.2, 0.2],
                        [0.1, 0.4, 0.3, 0.2],
                    ],
                ],
            ],
            dtype=torch.float32,
        )
        hypothesis = torch.tensor([0.0, 1.0, 0.0, 1.0])
        valid = torch.ones(4)

        actual = attention_seeker_token_scores(attentions, hypothesis, valid)
        expected = torch.zeros(4)
        for layer in range(attentions.shape[0]):
            for head in range(attentions.shape[1]):
                relevance = []
                for query_token in range(4):
                    value = float(attentions[layer, head, query_token] @ hypothesis)
                    relevance.append(value if hypothesis[query_token] else 0.0)
                map_relevance = sum(relevance) / 4.0
                for key_token in range(4):
                    expected[key_token] += sum(
                        attentions[layer, head, query_token, key_token]
                        * relevance[query_token]
                        * map_relevance
                        for query_token in range(4)
                    )
        expected *= hypothesis

        self.assertTrue(torch.allclose(actual, expected, atol=1e-6))
        self.assertEqual(actual[0].item(), 0.0)
        self.assertEqual(actual[2].item(), 0.0)

    def test_attention_variant_is_question_only_and_embedding_free(self) -> None:
        backend = _DeterministicBackend()
        scorer = _FakeAttentionScorer()
        extractor = UnsupervisedAspectExtractor(
            backend,
            {
                "variants": [P1U_ATTENTION_SEEKER],
                "selected_k": 5,
            },
            attention_scorer=scorer,
        )
        rows = [
            {
                "qa_id": "Q1",
                "question": "RFP 발행 후 제안서 요구조건을 어떻게 확인하나요?",
                "answer": "보면 안 되는 정답",
                "evidence_text": "보면 안 되는 근거",
            }
        ]

        result = extractor.extract_many(rows)

        self.assertEqual(backend.calls, [])
        self.assertEqual(len(scorer.calls), 1)
        self.assertEqual(set(result[0]["variants"]), {P1U_ATTENTION_SEEKER})
        profile = result[0]["variants"][P1U_ATTENTION_SEEKER]
        self.assertTrue(profile["search_terms"])
        self.assertTrue(profile["stage_terms"]["pcf"])
        self.assertTrue(profile["stage_terms"]["taskframe"])
        self.assertTrue(profile["stage_terms"]["fact"])
        self.assertNotIn("보면 안 되는 정답", repr(result))
        self.assertNotIn("보면 안 되는 근거", repr(result))

    def test_stage_terms_are_embedded_as_query_views(self) -> None:
        graph = GraphIndex.__new__(GraphIndex)
        graph.backend = _DeterministicBackend()
        aspects = {
            "stage_terms": {
                "pcf": ["수주 전략"],
                "taskframe": ["고객 요구 확인"],
                "fact": ["제안서 작성 전", "요구조건"],
            }
        }

        vectors = graph.aspect_vectors(aspects)

        self.assertEqual(set(vectors), {"pcf", "taskframe", "fact"})
        texts, input_type = graph.backend.calls[-1]
        self.assertEqual(texts, ["수주 전략", "고객 요구 확인", "제안서 작성 전 요구조건"])
        self.assertEqual(input_type, "query")

    def test_local_embedding_roles_have_separate_normalized_cache_entries(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            backend = OpenAIBackend(
                cache_path=Path(directory) / "cache.sqlite",
                embedding_model="test/local",
                embedding_dimensions=3,
                embedding_provider="sentence_transformers",
                embedding_revision="fixed",
                embedding_query_prompt_name="query",
                profiler_model="unused",
                generator_model="unused",
            )
            model = _FakeSentenceTransformer()
            backend._local_embedder = model

            query = backend.embed(["같은 문장"], input_type="query")[0]
            document = backend.embed(["같은 문장"], input_type="document")[0]

            self.assertEqual(len(model.calls), 2)
            self.assertEqual(model.calls[0]["prompt_name"], "query")
            self.assertNotIn("prompt_name", model.calls[1])
            self.assertAlmostEqual(math.sqrt(sum(value * value for value in query)), 1.0)
            self.assertAlmostEqual(math.sqrt(sum(value * value for value in document)), 1.0)


if __name__ == "__main__":
    unittest.main()
