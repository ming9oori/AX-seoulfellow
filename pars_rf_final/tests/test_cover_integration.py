from __future__ import annotations
import copy
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

import httpx
import numpy as np
from openai import AuthenticationError, RateLimitError
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from kg_rag.cover_api import CoverAPI, CoverAPIError
from kg_rag.cover_cache import CoverEmbeddingBackend
from kg_rag.cover_config import validate_config
from kg_rag.role_clause import RoleClauseExtractor
from kg_rag.openai_backend import ANSWER_INSTRUCTION, VERIFIER_INSTRUCTION


class RoleClauseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.extractor = RoleClauseExtractor(json.loads((ROOT / "config/aspect_rules.json").read_text()))

    def assert_raw(self, question, aspects):
        self.assertTrue(1 <= len(aspects) <= 3)
        self.assertEqual(aspects, self.extractor.extract(question))
        for a in aspects:
            for s in [*a["source_spans"], *a["anchor_spans"]]:
                self.assertEqual(s["text"], question[s["start"]:s["end"]])
            self.assertEqual(a["search_text"], " | ".join(s["text"] for s in [*a["anchor_spans"], *a["source_spans"]]))

    def test_parallel_intents(self):
        q = "제안서 검토는 언제 하고, 무엇을 확인하나요?"
        result = self.extractor.extract(q)
        self.assert_raw(q, result)
        intents = [a for a in result if "intent" in a["roles"]]
        self.assertEqual(len(intents), 2)
        self.assertTrue(all("제안서 검토" in a["search_text"] for a in intents))

    def test_two_temporal_boundaries(self):
        q = "기회분석이 끝난 뒤 제안참여 의사결정 전에는 어떤 결정이 이루어집니까?"
        result = self.extractor.extract(q)
        self.assert_raw(q, result)
        joined = " ".join(a["search_text"] for a in result)
        for phrase in ["기회분석이 끝난 뒤", "제안참여 의사결정 전"]:
            self.assertIn(phrase, joined)
        self.assertNotIn("영업참여 결정", joined)
        self.assertEqual(sum("intent" in a["roles"] for a in result), 1)

    def test_negative_numeric_fixtures(self):
        for q, retained in [("언제 검토하지 않아도 되나요?", "않아도"),
                            ("10일 이내 어떤 문서를 제출하나요?", "10일"),
                            ("A가 아닌 경우 어떻게 처리하나요?", "아닌"),
                            ("A와 B는 어떻게 다른가요?", "어떻게 다른가요")]:
            result = self.extractor.extract(q)
            self.assert_raw(q, result)
            self.assertIn(retained, " ".join(a["search_text"] for a in result))

    def test_overflow_preserves_conditions(self):
        q = "1일 이내, 3명 이상, 승인 후, 제출 전에 누가 무엇을 어떻게 확인하나요?"
        result = self.extractor.extract(q)
        self.assert_raw(q, result)
        joined = " ".join(a["search_text"] for a in result)
        for retained in ["1일", "이내", "3명", "이상", "승인 후", "제출 전"]:
            self.assertIn(retained, joined)
        self.assertTrue(any(a["bundled"] for a in result))

    def test_original_whitespace_offsets(self):
        q = "  제안서\n 검토는   언제 하나요?  "
        self.assert_raw(q, self.extractor.extract(q))

    def test_empty_rejected(self):
        with self.assertRaises(ValueError):
            self.extractor.extract(" ")


class APIContractTests(unittest.TestCase):
    def setUp(self):
        self.config = yaml.safe_load((ROOT / "config/experiment_pars_cover_v1.yaml").read_text())
        self.events = []
        self.client = Mock()
        self.api = CoverAPI("unused", self.config, client=self.client, on_event=self.events.append, sleep=lambda _: None)

    def test_strict_config(self):
        validate_config(self.config)
        for section, key, value in [("retrieval", "beta", .2), ("generation", "unknown", 0),
                                    ("benchmark", "repeats", 1)]:
            config = copy.deepcopy(self.config)
            config[section][key] = value
            with self.assertRaises(ValueError):
                validate_config(config)

    def test_auth_never_retried_or_leaked(self):
        response = httpx.Response(401, request=httpx.Request("POST", "https://api.openai.com/v1/embeddings"))
        op = Mock(side_effect=AuthenticationError("SECRET_EXAMPLE", response=response, body=None))
        with self.assertRaises(CoverAPIError) as caught:
            self.api._call("embedding", op)
        self.assertEqual(op.call_count, 1)
        self.assertNotIn("SECRET_EXAMPLE", json.dumps(self.events) + str(caught.exception))

    def test_transient_retry_max_six(self):
        response = httpx.Response(429, request=httpx.Request("POST", "https://api.openai.com/v1/embeddings"))
        op = Mock(side_effect=RateLimitError("private detail", response=response, body=None))
        with self.assertRaises(CoverAPIError):
            self.api._call("embedding", op)
        self.assertEqual(op.call_count, 6)

    def test_refusal_and_truncation_separate(self):
        for response, kind in [(SimpleNamespace(status="incomplete", usage=None, output=[]), "TRUNCATION_OR_INCOMPLETE"),
                               (SimpleNamespace(status="completed", usage=None, output=[SimpleNamespace(content=[SimpleNamespace(type="refusal")])]), "REFUSAL")]:
            self.client.responses.create.return_value = response
            with self.assertRaises(CoverAPIError) as caught:
                self.api.structured("answer", "p", {}, "q", {})
            self.assertEqual(caught.exception.kind, kind)

    def test_invalid_citation_rejected(self):
        payload = {"answer": "답", "citations": ["E9"], "status": "ANSWERED", "limitation": ""}
        self.client.responses.create.return_value = SimpleNamespace(status="completed", usage=None, output=[], output_text=json.dumps(payload))
        with self.assertRaises(CoverAPIError):
            self.api.structured("answer", "p", {}, "q", {"E1": "EV1"})

    def test_local_length_validation_and_explicit_decoding(self):
        payload = {"answer": "가"*701, "citations": [], "status": "INSUFFICIENT", "limitation": ""}
        self.client.responses.create.return_value = SimpleNamespace(status="completed", usage=None, output=[], output_text=json.dumps(payload))
        with self.assertRaises(CoverAPIError):
            self.api.structured("answer", "p", {}, "q", {})
        kwargs = self.client.responses.create.call_args.kwargs
        self.assertEqual(kwargs["temperature"], 0)
        self.assertEqual(kwargs["max_output_tokens"], 350)
        self.assertTrue(kwargs["text"]["format"]["strict"])

    def test_assets_preserve_legacy_prefix_and_schema_keys(self):
        for name, prefix in [("answer", ANSWER_INSTRUCTION), ("verifier", VERIFIER_INSTRUCTION)]:
            self.assertTrue((ROOT / f"prompts/{name}_system.txt").read_text().startswith(prefix))
            schema = json.loads((ROOT / f"schemas/{name}_output.json").read_text())
            self.assertEqual(set(schema["required"]), set(schema["properties"]))
            self.assertFalse(schema["additionalProperties"])

    def test_exact_cache_does_not_merge_whitespace_or_templates(self):
        self.api.embed_batch = Mock(side_effect=lambda texts, tokenizer: np.ones((len(texts), 1536), dtype=np.float32) / np.sqrt(1536))
        with tempfile.TemporaryDirectory() as d:
            backend = CoverEmbeddingBackend(self.api, Path(d) / "test.sqlite")
            backend.embed_exact(["a b", "a  b", "a b"])
            self.assertEqual(self.api.embed_batch.call_args.args[0], ["a b", "a  b"])
            backend.embed_exact(["a b"])
            self.assertEqual(self.api.embed_batch.call_count, 1)
            backend.embed_exact(["a b"], namespace="different")
            self.assertEqual(self.api.embed_batch.call_count, 2)
            backend.allow_api = False
            with self.assertRaises(RuntimeError):
                backend.embed_exact(["unseen"])
            backend.db.close()


if __name__ == "__main__":
    unittest.main()
