from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from run_experiment import (
    generate_answers,
    make_profiles,
    run_retrieval,
    validate_question_artifact,
)
from kg_rag.unsupervised_aspects import (
    P1B_PROFILE_FREE,
    P1G_PCF_GROUNDED,
    P1G_PROFILE_FREE,
    P1P_PARS_PROFILE_FREE,
)


class _FailingBackend:
    def profile_question(self, question: str):
        raise RuntimeError("profile unavailable")

    def generate_answer(self, **kwargs):
        raise RuntimeError("generation unavailable")


class _SuccessfulBackend:
    def generate_answer(self, **kwargs):
        return {
            "answer": "근거에 따른 답변입니다.",
            "citations": ["E1"],
            "status": "ANSWERED",
            "limitation": "",
        }, "generation-id", False

    def verify_answer(self, **kwargs):
        return {
            "supported": True,
            "corrected_answer": "근거에 따른 답변입니다.",
            "supported_citations": ["E1"],
            "unsupported_claims": [],
            "limitation": "",
        }, "verification-id", False


class _ProfileFreeCaptureRetriever:
    def __init__(self) -> None:
        self.calls = []

    def retrieve(self, **kwargs):
        self.calls.append(kwargs)
        return {
            "qid": kwargs["qid"],
            "question": kwargs["question"],
            "method": kwargs["method"],
            "condition": kwargs["condition"],
            "status": "NO_CONTEXT",
            "evidence": [],
            "context": "",
        }


class StrictRunTests(unittest.TestCase):
    def test_profile_free_final_method_runs_without_profile_artifact(self) -> None:
        retriever = _ProfileFreeCaptureRetriever()
        grounded = {
            "search_terms": ["고객 요구"],
            "rerank_terms": ["고객 요구"],
        }
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "retrieval.jsonl"
            run_retrieval(
                [{"qa_id": "Q1", "question": "질문"}],
                [],
                retriever,
                {
                    "methods": [
                        P1B_PROFILE_FREE,
                        P1G_PROFILE_FREE,
                        P1P_PARS_PROFILE_FREE,
                    ],
                    "conditions": ["D0_ORIGINAL"],
                },
                output,
                unsupervised_aspect_profiles=[
                    {
                        "qid": "Q1",
                        "variants": {P1G_PCF_GROUNDED: grounded},
                    }
                ],
            )

        self.assertEqual(len(retriever.calls), 3)
        by_method = {call["method"]: call for call in retriever.calls}
        self.assertTrue(all(call["profile"] is None for call in retriever.calls))
        self.assertIsNone(by_method[P1B_PROFILE_FREE]["aspects"])
        self.assertEqual(by_method[P1G_PROFILE_FREE]["aspects"], grounded)
        self.assertEqual(by_method[P1P_PARS_PROFILE_FREE]["aspects"], grounded)

    def test_reused_question_artifact_must_match_selected_dataset(self) -> None:
        qa_rows = [{"qa_id": "Q1", "question": "원래 질문"}]
        with self.assertRaisesRegex(ValueError, "does not match"):
            validate_question_artifact(
                qa_rows,
                [{"qid": "Q1", "question": "다른 질문"}],
                label="test artifact",
            )

    def test_profile_fallback_can_be_disabled(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "profiles.jsonl"
            with self.assertRaisesRegex(RuntimeError, "fallback is disabled"):
                make_profiles(
                    [{"qa_id": "Q1", "question": "질문"}],
                    _FailingBackend(),
                    output,
                    concurrency=1,
                    allow_fallback=False,
                )

    def test_configured_heuristic_profile_does_not_call_api(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "profiles.jsonl"
            profiles = make_profiles(
                [{"qa_id": "Q1", "question": "제안서 작성 절차는 무엇인가요?"}],
                _FailingBackend(),
                output,
                concurrency=1,
                allow_fallback=False,
                mode="heuristic",
            )

        self.assertEqual(profiles[0]["profile"]["profile_source"], "heuristic")
        self.assertFalse(profiles[0]["profile"]["fallback"])
        self.assertEqual(profiles[0]["error"], "")

    def test_answer_api_failure_blocks_evaluation_after_writing_diagnostics(self) -> None:
        retrieval = [
            {
                "qid": "Q1",
                "question": "질문",
                "method": "P0_QPA",
                "condition": "D0_ORIGINAL",
                "status": "RETRIEVED",
                "evidence": [{"evidence_id": "EV1"}],
                "context": "[E1]\ntext: 근거",
            }
        ]
        config = {
            "generation": {
                "max_output_tokens": 100,
                "concurrency": 1,
                "fail_on_api_error": True,
            }
        }

        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "answers.jsonl"
            with self.assertRaisesRegex(RuntimeError, "evaluation is intentionally blocked"):
                generate_answers(retrieval, _FailingBackend(), config, output)
            saved = [json.loads(line) for line in output.read_text().splitlines()]
            self.assertEqual(saved[0]["status"], "API_FAILED")
            self.assertTrue(saved[0]["api_failed"])

    def test_answer_artifact_carries_cited_graph_and_query_time_provenance(self) -> None:
        route = {
            "stored_graph_nodes": [{"label": "EvidenceSpan", "id": "EV1"}],
            "stored_graph_edges": [],
            "query_time_route": {
                "from_type": "Aspect",
                "from_text": "위험 등급",
                "to_type": "EvidenceSpan",
                "to_id": "EV1",
                "stored_as_neo4j_edge": False,
            },
        }
        retrieval = [
            {
                "qid": "Q1",
                "question": "질문",
                "method": "P1U_ATTENTION_SEEKER_ASPECT_CROSS_ENCODER_MMR",
                "condition": "D0_ORIGINAL",
                "status": "RETRIEVED",
                "evidence": [
                    {
                        "evidence_id": "EV1",
                        "rank": 1,
                        "source_file": "source.pdf",
                        "page": 3,
                        "section_path": "1.2",
                        "source": "aspect_evidence_direct",
                        "provenance": route,
                    }
                ],
                "context": "[E1]\ntext: 근거",
            }
        ]
        config = {
            "generation": {
                "max_output_tokens": 100,
                "concurrency": 1,
                "fail_on_api_error": True,
            }
        }

        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "answers.jsonl"
            answers = generate_answers(
                retrieval,
                _SuccessfulBackend(),
                config,
                output,
            )

        self.assertEqual(answers[0]["citations"], ["EV1"])
        self.assertEqual(len(answers[0]["citation_provenance"]), 1)
        self.assertEqual(
            answers[0]["citation_provenance"][0]["provenance"],
            route,
        )


if __name__ == "__main__":
    unittest.main()
