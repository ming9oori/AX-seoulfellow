from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from kg_rag.retrieval import (
    FIXED_PROPERTY_METHODS,
    METHODS,
    QUERY_PROFILE_METHODS,
    GraphIndex,
    GroupIndex,
    QPARetriever,
    StoredGraphEdge,
)
from kg_rag.unsupervised_aspects import (
    P1B_PROFILE_FREE,
    P1G_PROFILE_FREE,
    P1P_PARS,
    P1P_PARS_PROFILE_FREE,
)


class _DenseOnlyGraph:
    def __init__(self) -> None:
        self.evidence = {
            "EV1": {
                "name": "첫 번째 근거",
                "source_file": "source.pdf",
                "page": 1,
                "section_path": "1",
            },
            "EV2": {
                "name": "두 번째 근거",
                "source_file": "source.pdf",
                "page": 2,
                "section_path": "2",
            },
        }
        self.taskframes = {}
        self.facts = {}
        self.taskmentions = {}
        self.hybrid_called = False

    def question_vector(self, question: str):
        return object()

    def evidence_dense_scores(self, question: str, query_vector):
        return {"EV1": 0.25, "EV2": 0.90}

    def evidence_hybrid_scores(self, question: str, query_vector):
        self.hybrid_called = True
        raise AssertionError("Vanilla Dense RAG must not invoke BM25/hybrid scoring")


class _FixedCrossEncoder:
    model_id = "test/reranker"
    revision = "fixed"

    def score(self, question: str, passages):
        values = {
            "전역 1": 0.2,
            "전역 2": 0.1,
            "전역 중복": 0.0,
            "그래프 정답": 2.0,
        }
        return [values[text] for text in passages]


class _P1Graph:
    def __init__(self) -> None:
        self.evidence = {
            "E1": {"name": "전역 1", "section_path": "A"},
            "E2": {"name": "전역 2", "section_path": "A"},
            "E3": {"name": "전역 중복", "section_path": "A"},
            "G1": {"name": "그래프 정답", "section_path": "B"},
        }
        self.indices = {
            "evidence": GroupIndex(
                ids=["E1", "E2", "E3", "G1"],
                matrices={
                    "text": np.asarray(
                        [[1.0, 0.0], [0.99, 0.01], [0.98, 0.02], [0.0, 1.0]],
                        dtype=np.float32,
                    )
                },
                available={"text": np.asarray([True, True, True, True])},
            )
        }


class _DirectAspectGraph:
    def __init__(self) -> None:
        self.evidence = {
            "E1": {"name": "가격 근거", "section_path": "A"},
            "E2": {"name": "위험 근거", "section_path": "B"},
            "E3": {"name": "일반 근거", "section_path": "C"},
        }
        self.taskframes = {}
        self.facts = {}
        self.taskmentions = {}

    def question_vector(self, question: str):
        return question

    def evidence_hybrid_scores(self, question: str, query_vector):
        self.asserted_vector = query_vector
        return {
            "가격 조건": {"E1": 0.90, "E2": 0.20, "E3": 0.10},
            "위험 등급": {"E1": 0.30, "E2": 0.95, "E3": 0.20},
        }[question]


class VanillaDenseRAGTests(unittest.TestCase):
    def test_dense_score_is_raw_cosine_without_metadata_or_clipping(self) -> None:
        graph = GraphIndex.__new__(GraphIndex)
        graph._dense_scores = {}
        graph.indices = {
            "evidence": GroupIndex(
                ids=["EV1", "EV2"],
                matrices={"text": np.asarray([[-1.0, 0.0], [-0.5, 0.0]], dtype=np.float32)},
                available={"text": np.asarray([True, True])},
            )
        }

        scores = graph.evidence_dense_scores(
            "질문", np.asarray([1.0, 0.0], dtype=np.float32)
        )

        self.assertEqual(scores, {"EV1": -1.0, "EV2": -0.5})

    def test_uses_only_dense_evidence_ranking_and_no_graph_context(self) -> None:
        graph = _DenseOnlyGraph()
        retriever = QPARetriever(
            graph=graph,
            config={"evidence_top_k": 2, "context_max_chars": 6000},
        )

        result = retriever.retrieve(
            qid="Q1",
            question="질문",
            method="B0_VANILLA_DENSE_RAG",
            condition="D0_ORIGINAL",
            profile={},
        )

        self.assertEqual([item["evidence_id"] for item in result["evidence"]], ["EV2", "EV1"])
        self.assertTrue(all(item["source"] == "global_evidence_dense" for item in result["evidence"]))
        self.assertFalse(graph.hybrid_called)
        self.assertEqual(result["pcf_candidates"], [])
        self.assertEqual(result["taskframe_candidates"], [])
        self.assertNotIn("PCF CLASSIFICATION", result["context"])
        self.assertNotIn("QUERY-ACTIVATED FACETS", result["context"])
        self.assertEqual(
            result["telemetry"]["retrieval_strategy"],
            "evidence_text_embedding_cosine_only",
        )
        self.assertFalse(result["telemetry"]["query_profile_used"])
        self.assertFalse(result["telemetry"]["graph_used"])
        self.assertFalse(result["telemetry"]["bm25_used"])


class P1CrossEncoderMMRTests(unittest.TestCase):
    def test_preserves_p0_quota_and_promotes_cross_encoder_candidate(self) -> None:
        retriever = QPARetriever(
            graph=_P1Graph(),
            config={
                "evidence_top_k": 3,
                "p0_cross_encoder_rerank": {
                    "candidate_k": 4,
                    "p0_evidence_quota": 2,
                    "rrf_k": 60,
                    "p0_weight": 1.0,
                    "cross_encoder_weight": 2.0,
                    "mmr_lambda": 0.9,
                    "same_section_penalty": True,
                },
            },
            cross_encoder=_FixedCrossEncoder(),
        )
        p0_candidates = {
            evidence_id: {
                "evidence_id": evidence_id,
                "score": score,
                "source": "fact_path" if evidence_id == "G1" else "global_evidence_fallback",
                "taskframe_id": "TF1" if evidence_id == "G1" else "",
                "fact_id": "F1" if evidence_id == "G1" else "",
                "fact_relationship": "HAS_CORE_FACT" if evidence_id == "G1" else "",
                "taskmention_id": "",
            }
            for evidence_id, score in {
                "E1": 1.0,
                "E2": 0.9,
                "E3": 0.8,
                "G1": 0.1,
            }.items()
        }

        selected, telemetry = retriever._p0_cross_encoder_mmr_candidates(
            question="질문",
            p0_candidates=p0_candidates,
        )
        selected_ids = {item["evidence_id"] for item in selected}

        self.assertEqual(len(selected), 3)
        self.assertTrue({"E1", "E2", "G1"}.issubset(selected_ids))
        self.assertEqual(telemetry["p0_evidence_quota"], 2)
        self.assertEqual(telemetry["model"], "test/reranker")
        graph_item = next(item for item in selected if item["evidence_id"] == "G1")
        self.assertEqual(graph_item["cross_encoder_rank"], 1)
        self.assertEqual(graph_item["p0_rank"], 4)
        self.assertEqual(graph_item["original_source"], "fact_path")

    def test_aspect_blend_keeps_original_question_dominant(self) -> None:
        blended = QPARetriever._blend_scores(
            {"A": 1.0, "B": 0.0},
            {"A": 0.0, "B": 1.0},
            0.25,
        )

        self.assertEqual(blended, {"A": 0.75, "B": 0.25})

    def test_aspect_rerank_can_override_quota_and_mmr_without_changing_base(self) -> None:
        retriever = QPARetriever(
            graph=_P1Graph(),
            config={
                "evidence_top_k": 3,
                "p0_cross_encoder_rerank": {
                    "candidate_k": 4,
                    "p0_evidence_quota": 2,
                    "rrf_k": 60,
                    "p0_weight": 1.0,
                    "cross_encoder_weight": 2.0,
                    "mmr_lambda": 0.9,
                    "same_section_penalty": True,
                },
                "aspect_analysis": {
                    "rerank_cross_encoder_weight": 0.5,
                    "rerank_base_path_quota": 1,
                    "rerank_mmr_lambda": 0.95,
                },
            },
            cross_encoder=_FixedCrossEncoder(),
        )
        p0_candidates = {
            evidence_id: {
                "evidence_id": evidence_id,
                "score": score,
                "source": "global_evidence_fallback",
                "taskframe_id": "",
                "fact_id": "",
                "fact_relationship": "",
                "taskmention_id": "",
                "base_path_rank": rank,
            }
            for rank, (evidence_id, score) in enumerate(
                {"E1": 1.0, "E2": 0.9, "E3": 0.8, "G1": 0.1}.items(), 1
            )
        }

        _, base_telemetry = retriever._p0_cross_encoder_mmr_candidates(
            question="질문",
            p0_candidates=p0_candidates,
            quota_rank_field="base_path_rank",
        )
        _, aspect_telemetry = retriever._p0_cross_encoder_mmr_candidates(
            question="질문",
            p0_candidates=p0_candidates,
            quota_rank_field="base_path_rank",
            aspect_queries=["비용 조건"],
        )

        self.assertEqual(base_telemetry["p0_evidence_quota"], 2)
        self.assertEqual(base_telemetry["mmr_lambda"], 0.9)
        self.assertEqual(aspect_telemetry["p0_evidence_quota"], 1)
        self.assertEqual(aspect_telemetry["mmr_lambda"], 0.95)
        self.assertEqual(aspect_telemetry["weights"]["aspect_cross_encoder"], 0.5)

    def test_stage_specific_aspect_weights_override_default(self) -> None:
        retriever = QPARetriever(
            graph=None,
            config={
                "aspect_analysis": {
                    "semantic_blend_weight": 0.25,
                    "stage_semantic_blend_weights": {
                        "pcf": 0.30,
                        "taskframe": 0.10,
                    },
                }
            },
        )

        self.assertEqual(
            retriever._aspect_stage_weights(),
            {"pcf": 0.30, "taskframe": 0.10, "fact": 0.25},
        )

    def test_dual_path_rrf_rewards_shared_candidates_and_keeps_graph_metadata(self) -> None:
        retriever = QPARetriever(
            graph=None,
            config={
                "evidence_top_k": 2,
                "aspect_analysis": {
                    "dual_path_branch_candidate_k": 3,
                    "dual_path_rrf_k": 60,
                    "dual_path_base_weight": 1.0,
                    "dual_path_aspect_weight": 1.0,
                },
            },
        )
        base = {
            "B": {"evidence_id": "B", "score": 1.0, "source": "global_evidence_fallback"},
            "X": {"evidence_id": "X", "score": 0.9, "source": "global_evidence_fallback"},
        }
        aspect = {
            "A": {"evidence_id": "A", "score": 1.0, "source": "fact_path", "fact_id": "F1"},
            "X": {"evidence_id": "X", "score": 0.8, "source": "fact_path", "fact_id": "F2"},
        }

        fused, telemetry = retriever._dual_path_candidates(base, aspect)

        self.assertGreater(fused["X"]["score"], fused["A"]["score"])
        self.assertGreater(fused["X"]["score"], fused["B"]["score"])
        self.assertEqual(fused["X"]["source"], "dual_path_both")
        self.assertEqual(fused["X"]["fact_id"], "F2")
        self.assertEqual(telemetry["intersection_candidate_count"], 1)

    def test_dual_path_keeps_pars_representative_route_with_its_subgraph(self) -> None:
        retriever = QPARetriever(
            graph=None,
            config={
                "evidence_top_k": 1,
                "aspect_analysis": {
                    "dual_path_branch_candidate_k": 1,
                    "dual_path_rrf_k": 60,
                },
            },
        )
        base = {
            "E1": {
                "evidence_id": "E1",
                "score": 1.0,
                "source": "fact_path",
                "taskframe_id": "TF_BASE",
                "fact_id": "F_BASE",
            }
        }
        pars = {
            "E1": {
                "evidence_id": "E1",
                "score": 0.1,
                "source": "property_relational_subgraph",
                "taskframe_id": "TF_PARS",
                "fact_id": "F_PARS",
                "subgraph_nodes": [{"id": "F_PARS", "label": "Fact"}],
                "subgraph_edges": [
                    {"from": "F_PARS", "type": "SUPPORTED_BY", "to": "E1"}
                ],
            }
        }

        fused, _ = retriever._dual_path_candidates(base, pars)

        self.assertEqual(fused["E1"]["taskframe_id"], "TF_PARS")
        self.assertEqual(fused["E1"]["fact_id"], "F_PARS")
        self.assertEqual(fused["E1"]["subgraph_nodes"][0]["id"], "F_PARS")

    def test_p1p_three_path_rrf_combines_recall_and_subgraph_precision(self) -> None:
        retriever = QPARetriever(
            graph=None,
            config={
                "evidence_top_k": 2,
                "aspect_analysis": {
                    "dual_path_branch_candidate_k": 3,
                    "dual_path_rrf_k": 60,
                },
            },
        )
        base = {
            "SHARED": {"evidence_id": "SHARED", "score": 0.8},
            "BASE": {"evidence_id": "BASE", "score": 0.7},
        }
        direct = {
            "SHARED": {
                "evidence_id": "SHARED",
                "score": 0.9,
                "matched_aspect": "고객 조건",
            },
            "DIRECT": {"evidence_id": "DIRECT", "score": 0.8},
        }
        pars = {
            "SHARED": {
                "evidence_id": "SHARED",
                "score": 0.6,
                "taskframe_id": "TF1",
                "fact_id": "F1",
                "subgraph_nodes": [{"id": "F1", "label": "Fact"}],
                "subgraph_edges": [
                    {"from": "F1", "type": "SUPPORTED_BY", "to": "SHARED"}
                ],
            },
            "PARS": {"evidence_id": "PARS", "score": 0.5},
        }

        fused, telemetry = retriever._p1p_three_path_candidates(
            base, direct, pars
        )

        self.assertGreater(fused["SHARED"]["score"], fused["BASE"]["score"])
        self.assertEqual(fused["SHARED"]["fact_id"], "F1")
        self.assertEqual(fused["SHARED"]["matched_aspect"], "고객 조건")
        self.assertEqual(fused["SHARED"]["base_path_rank"], 1)
        self.assertEqual(fused["SHARED"]["direct_aspect_path_rank"], 1)
        self.assertEqual(fused["SHARED"]["pars_path_rank"], 1)
        self.assertEqual(telemetry["weights"], {
            "base": 1.0,
            "direct_aspect": 1.0,
            "pars": 1.0,
        })

    def test_direct_aspect_branch_uses_strongest_query_without_creating_edge(self) -> None:
        retriever = QPARetriever(
            graph=_DirectAspectGraph(),
            config={
                "evidence_top_k": 2,
                "aspect_analysis": {
                    "direct_evidence_query_k": 2,
                    "direct_evidence_candidate_k": 2,
                },
            },
        )

        candidates, telemetry = retriever._direct_aspect_evidence_candidates(
            ["가격 조건", "위험 등급", "가격 조건"]
        )

        self.assertEqual(set(candidates), {"E1", "E2"})
        self.assertEqual(candidates["E1"]["matched_aspect"], "가격 조건")
        self.assertEqual(candidates["E2"]["matched_aspect"], "위험 등급")
        self.assertEqual(candidates["E2"]["source"], "aspect_evidence_direct")
        self.assertEqual(telemetry["query_count"], 2)
        self.assertFalse(telemetry["stored_as_neo4j_edge"])

    def test_context_labels_direct_aspect_as_query_time_route(self) -> None:
        retriever = QPARetriever(
            graph=_DirectAspectGraph(),
            config={"context_max_chars": 6000},
        )

        context = retriever._render_context(
            method="P1U_ATTENTION_SEEKER_ASPECT_CROSS_ENCODER_MMR",
            condition="D0_ORIGINAL",
            profile={},
            pcf_candidates=[],
            taskframes=[],
            selected=[
                {
                    "evidence_id": "E2",
                    "matched_aspect": "위험 등급",
                    "taskframe_id": "",
                    "fact_id": "",
                    "taskmention_id": "",
                }
            ],
        )

        self.assertIn('Aspect("위험 등급") -> EvidenceSpan', context)
        self.assertIn("not a stored Neo4j edge", context)


class PropertyRelationalSubgraphTests(unittest.TestCase):
    def test_p1p_is_registered_as_an_experiment_method(self) -> None:
        self.assertIn(P1P_PARS, METHODS)
        self.assertIn(P1B_PROFILE_FREE, METHODS)
        self.assertIn(P1G_PROFILE_FREE, METHODS)
        self.assertIn(P1P_PARS_PROFILE_FREE, METHODS)

    def test_final_p1p_is_profile_free_and_uses_fixed_property_weights(self) -> None:
        for method in (
            P1B_PROFILE_FREE,
            P1G_PROFILE_FREE,
            P1P_PARS_PROFILE_FREE,
        ):
            self.assertNotIn(method, QUERY_PROFILE_METHODS)
            self.assertIn(method, FIXED_PROPERTY_METHODS)

        retriever = QPARetriever(
            graph=_DirectAspectGraph(),
            config={"context_max_chars": 6000},
        )
        context = retriever._render_context(
            method=P1P_PARS_PROFILE_FREE,
            condition="D0_ORIGINAL",
            profile={
                "answer_shape": "LIST",
                "target_facets": ["triple"],
                "knowledge_functions": ["fact"],
            },
            pcf_candidates=[],
            taskframes=[],
            selected=[
                {
                    "evidence_id": "E2",
                    "taskframe_id": "",
                    "fact_id": "",
                    "taskmention_id": "",
                }
            ],
        )

        self.assertNotIn("QUERY-ACTIVATED FACETS", context)

    def test_property_matching_selects_the_strongest_available_view(self) -> None:
        graph = GraphIndex.__new__(GraphIndex)
        graph.indices = {
            "fact": GroupIndex(
                ids=["F1", "F2"],
                matrices={
                    "identity": np.asarray(
                        [[0.0, 1.0], [1.0, 0.0]], dtype=np.float32
                    ),
                    "triple": np.asarray(
                        [[1.0, 0.0], [0.0, 1.0]], dtype=np.float32
                    ),
                },
                available={
                    "identity": np.asarray([True, True]),
                    "triple": np.asarray([True, False]),
                },
            )
        }
        graph._group_texts = {
            "fact": {
                "F1": {"identity": "약한 식별 정보", "triple": "강한 삼중항"},
                "F2": {"identity": "강한 식별 정보", "triple": ""},
            }
        }

        matches = graph.schema_property_matches(
            np.asarray([1.0, 0.0], dtype=np.float32),
            condition="D0_ORIGINAL",
        )

        self.assertEqual(matches["F1"]["property_view"], "triple")
        self.assertEqual(matches["F1"]["property_text"], "강한 삼중항")
        self.assertEqual(matches["F2"]["property_view"], "identity")

    def test_minimal_subgraph_is_a_union_of_real_connected_paths(self) -> None:
        graph = GraphIndex.__new__(GraphIndex)
        graph.graph_node_labels = {
            "E1": "EvidenceSpan",
            "F1": "Fact",
            "TF1": "TaskFrame",
            "P1": "PCFProcess",
        }
        graph.stored_graph_edges = {
            "e1": StoredGraphEdge("e1", "F1", "SUPPORTED_BY", "E1", "supported by"),
            "e2": StoredGraphEdge("e2", "TF1", "HAS_CORE_FACT", "F1", "core fact"),
            "e3": StoredGraphEdge("e3", "TF1", "MAPS_TO_PCF", "P1", "maps to pcf"),
        }
        graph.graph_adjacency = {
            "E1": [("F1", "e1")],
            "F1": [("E1", "e1"), ("TF1", "e2")],
            "TF1": [("F1", "e2"), ("P1", "e3")],
            "P1": [("TF1", "e3")],
        }
        graph.evidence_support_nodes = {
            "E1": frozenset({"E1", "F1", "TF1", "P1"})
        }
        graph.evidence_support_edges = {"E1": frozenset({"e1", "e2", "e3"})}

        nodes, edges = graph.minimal_evidence_subgraph("E1", ["P1"])

        self.assertEqual(set(nodes), {"E1", "F1", "TF1", "P1"})
        self.assertEqual(set(edges), {"e1", "e2", "e3"})
        for edge_id in edges:
            edge = graph.stored_graph_edges[edge_id]
            self.assertIn(edge.source, nodes)
            self.assertIn(edge.target, nodes)

    def test_edge_semantics_keep_explanatory_fields_only(self) -> None:
        text = GraphIndex._edge_semantic_text(
            "MAPS_TO_PCF",
            {
                "reason": "고객 분석 근거",
                "mapping_role": "primary",
                "run_id": "technical-run-id",
                "created_at": "2026-09-21",
            },
        )

        self.assertIn("고객 분석 근거", text)
        self.assertIn("primary", text)
        self.assertNotIn("technical-run-id", text)
        self.assertNotIn("2026-09-21", text)


class LateFusionSelectionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.retriever = QPARetriever(
            graph=None,  # The pure selection helper does not access GraphIndex.
            config={
                "evidence_top_k": 5,
                "late_fusion": {
                    "reranker": "weighted_rrf",
                    "global_candidate_k": 20,
                    "graph_candidate_k": 20,
                    "global_evidence_quota": 3,
                    "rrf_k": 60,
                    "global_weight": 1.0,
                    "graph_weight": 1.0,
                },
            },
        )

    def test_preserves_top_three_global_candidates(self) -> None:
        hybrid = {f"E{index}": 1.0 - index / 100 for index in range(1, 11)}
        graph = {
            "G1": {"evidence_id": "G1", "score": 0.99, "fact_id": "F1"},
            "G2": {"evidence_id": "G2", "score": 0.98, "fact_id": "F2"},
        }

        selected, telemetry = self.retriever._late_fusion_candidates(graph, hybrid)
        selected_ids = {item["evidence_id"] for item in selected}

        self.assertEqual(len(selected), 5)
        self.assertEqual([item["evidence_id"] for item in selected[:3]], ["E1", "E2", "E3"])
        self.assertTrue({"E1", "E2", "E3"}.issubset(selected_ids))
        self.assertEqual(telemetry["global_evidence_quota"], 3)
        self.assertEqual(telemetry["selected_global_count"], 3)
        self.assertEqual(telemetry["selected_graph_count"], 2)

    def test_marks_candidates_returned_by_both_branches(self) -> None:
        hybrid = {"E1": 1.0, "E2": 0.9, "E3": 0.8, "E4": 0.7, "E5": 0.6}
        graph = {
            "E4": {
                "evidence_id": "E4",
                "score": 0.95,
                "taskframe_id": "TF1",
                "fact_id": "F1",
            }
        }

        selected, _ = self.retriever._late_fusion_candidates(graph, hybrid)
        item = next(value for value in selected if value["evidence_id"] == "E4")

        self.assertEqual(item["source"], "late_fusion_both")
        self.assertEqual(item["global_rank"], 4)
        self.assertEqual(item["graph_rank"], 1)
        self.assertEqual(item["fact_id"], "F1")


class V2QualityFilterTests(unittest.TestCase):
    def test_filters_inactive_superseded_and_quarantined_facts(self) -> None:
        self.assertFalse(QPARetriever._allow_v2_fact({"active": False}))
        self.assertFalse(QPARetriever._allow_v2_fact({"lifecycleStatus": "superseded"}))
        self.assertFalse(QPARetriever._allow_v2_fact({"quality_status": "quarantined"}))
        self.assertTrue(QPARetriever._allow_v2_fact({"active": True, "quality_status": "accepted"}))

    def test_filters_taskmentions_requiring_review(self) -> None:
        self.assertFalse(
            QPARetriever._allow_v2_taskmention({"quality_status": "review_required"})
        )
        self.assertTrue(QPARetriever._allow_v2_taskmention({"quality_status": "accepted"}))


if __name__ == "__main__":
    unittest.main()
