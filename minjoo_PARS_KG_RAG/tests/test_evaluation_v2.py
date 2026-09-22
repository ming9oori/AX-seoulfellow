from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from kg_rag.evaluation import (
    ANSWER_COMPARISON_PAIRS,
    align_gold_evidence,
    evaluate_retrieval,
)


class ExplicitGoldTests(unittest.TestCase):
    def setUp(self) -> None:
        self.snapshot = {
            "evidence_spans": [
                {"properties": {"id": "EV1", "name": "첫 번째 근거", "page": 1}},
                {"properties": {"id": "EV2", "name": "두 번째 근거", "page": 2}},
            ],
            "facts": [
                {
                    "properties": {"id": "F1"},
                    "evidence_ids": ["EV1", "EV2"],
                    "frame_links": [{"taskframe_id": "TF1"}],
                }
            ],
            "taskmentions": [],
            "pcf_mappings": [
                {
                    "taskframe_id": "TF1",
                    "pcf_id": "PCF1",
                    "relationship_type": "MAPS_TO_PCF",
                }
            ],
        }
        self.qa_row = {
            "qa_id": "Q1",
            "evidence_text": "[]",
            "gold_evidence_span_ids": '["EV1", "EV2"]',
            "gold_taskframe_ids": '["TF1"]',
            "gold_fact_ids": '["F1"]',
            "gold_pcf_ids": '["PCF1"]',
            "gold_relation_types": '["SUPPORTED_BY"]',
            "gold_path": '["TF1", "F1", "EV1"]',
            "min_hops": "2",
            "expected_behavior": "answer_with_evidence",
            "source_answerable": "true",
            "ontology_answerable": "true",
            "graph_structure_required": "true",
        }

    def test_explicit_gold_overrides_text_alignment(self) -> None:
        aligned, report = align_gold_evidence([self.qa_row], self.snapshot)

        self.assertEqual(aligned[0]["gold_evidence_ids"], ["EV1", "EV2"])
        self.assertEqual(aligned[0]["gold_fact_ids"], ["F1"])
        self.assertEqual(aligned[0]["gold_taskframe_ids"], ["TF1"])
        self.assertEqual(aligned[0]["gold_pcf_ids"], ["PCF1"])
        self.assertEqual(aligned[0]["min_hops"], 2)
        self.assertEqual(report["qa_with_explicit_gold_evidence"], 1)

    def test_complete_evidence_and_fact_recall(self) -> None:
        gold, _ = align_gold_evidence([self.qa_row], self.snapshot)
        retrieval = [
            {
                "qid": "Q1",
                "method": "V2_EVIDENCE_GRAPH_LATE_FUSION",
                "condition": "D0_ORIGINAL",
                "evidence": [{"evidence_id": "EV2"}, {"evidence_id": "EV1"}],
                "taskframe_candidates": [{"id": "TF1"}],
                "fact_candidates": [{"id": "F1"}],
                "pcf_candidates": [{"id": "PCF1"}],
                "status": "RETRIEVED",
            }
        ]

        per_question, summary = evaluate_retrieval(retrieval, gold)

        self.assertEqual(per_question[0]["complete_evidence_set_at_5"], 1.0)
        self.assertEqual(per_question[0]["fact_recall_at_12"], 1.0)
        self.assertEqual(per_question[0]["complete_gold_node_chain"], 1.0)
        self.assertEqual(summary[0]["complete_evidence_set_at_5"], 1.0)

    def test_vanilla_dense_rag_has_no_graph_metric_denominator(self) -> None:
        gold, _ = align_gold_evidence([self.qa_row], self.snapshot)
        retrieval = [
            {
                "qid": "Q1",
                "method": "B0_VANILLA_DENSE_RAG",
                "condition": "D0_ORIGINAL",
                "evidence": [{"evidence_id": "EV1"}],
                "taskframe_candidates": [],
                "fact_candidates": [],
                "pcf_candidates": [],
                "status": "RETRIEVED",
            }
        ]

        per_question, summary = evaluate_retrieval(retrieval, gold)

        self.assertIsNone(per_question[0]["taskframe_recall_at_3"])
        self.assertEqual(summary[0]["taskframe_recall_at_3_n"], 0)
        self.assertIsNone(per_question[0]["pcf_recall_at_3"])
        self.assertEqual(summary[0]["pcf_recall_at_3_n"], 0)

    def test_primary_answer_comparison_is_registered(self) -> None:
        self.assertIn(
            ("P0_QPA", "B0_VANILLA_DENSE_RAG"),
            ANSWER_COMPARISON_PAIRS,
        )


if __name__ == "__main__":
    unittest.main()
