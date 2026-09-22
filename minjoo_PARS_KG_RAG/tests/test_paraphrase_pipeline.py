from __future__ import annotations

import json
import sys
import threading
import unittest
from pathlib import Path
from types import SimpleNamespace

from pydantic import BaseModel


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
QA_V2 = ROOT / "qa_v2"
for path in (SRC, QA_V2):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from kg_rag.openai_backend import OpenAIBackend
from paraphrase_pipeline import (
    build_challenge_rows,
    build_parent_records,
    validate_challenge_rows,
)
from summarize_paraphrase_retrieval import summarize


class FixedScorer:
    def score(self, question, evidence_texts):
        return 0.5

    def band(self, score):
        return "medium"


class DummyOutput(BaseModel):
    value: str


class EmptyCache:
    def get_llm(self, cache_key):
        return None

    def put_llm(self, cache_key, **kwargs):
        return None


class CapturingResponses:
    def __init__(self):
        self.requests = []

    def parse(self, **kwargs):
        self.requests.append(kwargs)
        return SimpleNamespace(output_parsed=DummyOutput(value="ok"), id="resp-test")


class ParaphrasePipelineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.source = [
            {
                "qa_id": "Q1",
                "question": "제안 전략은 어떻게 수립하나요?",
                "answer": "정보를 분석해 차별화 전략을 수립합니다.",
                "evidence_text": '["정보를 분석해 차별화 전략을 수립한다."]',
                "source_answerable": "True",
                "expected_behavior": "answer_with_evidence",
            }
        ]
        self.aligned = [
            {
                "qid": "Q1",
                "gold_evidence_ids": ["EV1"],
                "gold_taskframe_ids": ["TF1"],
                "gold_pcf_ids": ["PCF1"],
                "gold_fact_ids": [],
                "gold_relation_types": [],
                "gold_path": [],
                "min_hops": None,
            }
        ]
        self.parents = build_parent_records(self.source, self.aligned)
        validations = [
            {
                "variant_type": variant_type,
                "same_information_need": True,
                "no_added_or_removed_constraints": True,
                "no_answer_leakage": True,
                "natural_korean": True,
                "rationale": "동일한 질문입니다.",
            }
            for variant_type in ("alias_synonym", "scenario_query", "colloquial_query")
        ]
        self.record = {
            "variants": [
                {
                    "variant_type": "alias_synonym",
                    "question": "제안 방향은 어떤 방식으로 세우나요?",
                    "transformation_summary": "동의어",
                },
                {
                    "variant_type": "scenario_query",
                    "question": "입찰을 준비할 때 제안 전략을 어떻게 잡아야 하나요?",
                    "transformation_summary": "상황형",
                },
                {
                    "variant_type": "colloquial_query",
                    "question": "제안 전략은 어떻게 잡죠?",
                    "transformation_summary": "구어체",
                },
            ],
            "validations": validations,
            "generation_model": "test-generator",
            "generation_response_id": "gen-1",
            "validation_model": "test-validator",
            "validation_response_id": "val-1",
            "generated_at": "2026-09-20T00:00:00+00:00",
        }

    def test_builds_four_rows_and_preserves_gold(self) -> None:
        rows = build_challenge_rows(
            self.parents, {"Q1": self.record}, scorer=FixedScorer()
        )
        errors, summary = validate_challenge_rows(rows, self.parents)

        self.assertEqual(errors, [])
        self.assertEqual(len(rows), 4)
        self.assertEqual(summary["expected_complete_row_count"], 4)
        self.assertTrue(all(json.loads(row["gold_evidence_span_ids"]) == ["EV1"] for row in rows))
        self.assertTrue(all(row["evidence_text"] == "[]" for row in rows))

    def test_detects_gold_or_answer_mutation(self) -> None:
        rows = build_challenge_rows(
            self.parents, {"Q1": self.record}, scorer=FixedScorer()
        )
        rows[1]["answer"] = "바뀐 답"
        rows[2]["gold_evidence_span_ids"] = '["EV2"]'

        errors, _ = validate_challenge_rows(rows, self.parents)

        self.assertTrue(any("reference answer changed" in error for error in errors))
        self.assertTrue(any("frozen gold_evidence_span_ids changed" in error for error in errors))

    def test_generator_prompt_cannot_receive_answer_or_evidence(self) -> None:
        backend = object.__new__(OpenAIBackend)
        backend.generator_model = "generator"
        backend.paraphrase_validator_model = "validator"
        calls = []

        def fake_parse(**kwargs):
            calls.append(kwargs)
            return {}, "response", False

        backend._parse = fake_parse
        backend.generate_paraphrase_variants(question="원 질문")
        backend.validate_paraphrase_variants(
            question="원 질문",
            reference_answer="비밀 정답",
            variants=[{"variant_type": "alias_synonym", "question": "후보"}],
        )

        generation_payload = json.loads(calls[0]["user_input"])
        validation_payload = json.loads(calls[1]["user_input"])
        self.assertEqual(set(generation_payload), {"original_question", "required_variant_types"})
        self.assertNotIn("비밀 정답", calls[0]["user_input"])
        self.assertNotIn("evidence", calls[0]["user_input"].lower())
        self.assertEqual(validation_payload["reference_answer"], "비밀 정답")
        self.assertNotIn("evidence", calls[1]["user_input"].lower())

    def test_non_reasoning_model_omits_reasoning_request_option(self) -> None:
        backend = object.__new__(OpenAIBackend)
        responses = CapturingResponses()
        backend.client = SimpleNamespace(responses=responses)
        backend.cache = EmptyCache()
        backend.reasoning_effort = None
        backend.max_retries = 0
        backend._llm_locks_guard = threading.Lock()
        backend._llm_locks = {}

        backend._parse(
            model="gpt-4o-mini-2024-07-18",
            kind="test",
            instruction="test",
            user_input="test",
            response_model=DummyOutput,
            max_output_tokens=20,
        )

        self.assertNotIn("reasoning", responses.requests[0])

    def test_summary_uses_paired_method_and_parent_deltas(self) -> None:
        qa_rows = [
            {
                "qa_id": "Q1",
                "parent_qa_id": "Q1",
                "variant_type": "original_control",
                "lexical_overlap_band": "high",
                "lexical_overlap_score": "0.8",
            },
            {
                "qa_id": "Q1__P_ALIAS",
                "parent_qa_id": "Q1",
                "variant_type": "alias_synonym",
                "lexical_overlap_band": "low",
                "lexical_overlap_score": "0.2",
            },
        ]
        metric_rows = []
        values = {
            ("Q1", "B0_EVIDENCE_HYBRID"): 1.0,
            ("Q1", "V2_EVIDENCE_GRAPH_LATE_FUSION"): 1.0,
            ("Q1__P_ALIAS", "B0_EVIDENCE_HYBRID"): 0.0,
            ("Q1__P_ALIAS", "V2_EVIDENCE_GRAPH_LATE_FUSION"): 1.0,
        }
        for (qid, method), value in values.items():
            row = {
                "qid": qid,
                "method": method,
                "condition": "D0_ORIGINAL",
                **{metric: value for metric in (
                    "evidence_hit_at_1",
                    "evidence_hit_at_5",
                    "evidence_recall_at_5",
                    "complete_evidence_set_at_5",
                    "evidence_mrr",
                )},
                "taskframe_recall_at_3": None,
                "fact_recall_at_12": None,
                "pcf_recall_at_3": None,
            }
            metric_rows.append(row)

        report = summarize(qa_rows, metric_rows, bootstrap_iterations=20, seed=7)
        paired = next(
            row
            for row in report["paired_method_deltas"]
            if row["left_method"] == "V2_EVIDENCE_GRAPH_LATE_FUSION"
            and row["right_method"] == "B0_EVIDENCE_HYBRID"
            and row["metric"] == "evidence_recall_at_5"
            and row["scope"] == "paraphrase_lexical_band"
        )
        self.assertEqual(paired["mean_delta_left_minus_right"], 1.0)
        degradation = next(
            row
            for row in report["paired_paraphrase_degradation"]
            if row["method"] == "B0_EVIDENCE_HYBRID"
            and row["metric"] == "evidence_recall_at_5"
            and row["scope"] == "variant_type"
        )
        self.assertEqual(degradation["mean_delta_paraphrase_minus_original"], -1.0)


if __name__ == "__main__":
    unittest.main()
