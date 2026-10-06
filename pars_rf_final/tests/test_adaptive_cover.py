import json
from pathlib import Path
import sys
import unittest
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from kg_rag.adaptive_aspects import AdaptiveAspectExtractor
from kg_rag.role_clause import RoleClauseExtractor
from kg_rag.cover_selection import select_adaptive_set, select_coverage_set


class AdaptiveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = json.loads((ROOT / "config/aspect_rules.json").read_text())
        cls.new = AdaptiveAspectExtractor(cls.rules)
        cls.uncapped = AdaptiveAspectExtractor(cls.rules, cls.new.kiwi, structured=False)
        cls.old = RoleClauseExtractor(cls.rules, cls.new.kiwi)

    def check_raw(self, q, rows):
        for a in rows:
            for s in a["source_spans"] + a["anchor_spans"] + a.get("constraint_spans", []) + a.get("merged_source_spans", []):
                self.assertEqual(s["text"], q[s["start"]:s["end"]])
            self.assertEqual(a["search_text"], " | ".join(s["text"] for s in
                a["anchor_spans"] + a.get("constraint_spans", []) + a["source_spans"]))

    def test_four_independent_requests(self):
        q = "설계 검토는 누가 담당하고, 언제 수행하며, 무엇을 확인하고, 어디에 기록하나요?"
        self.assertEqual(len(self.new.extract(q)), 4)
        self.assertLessEqual(len(self.old.extract(q)), 3)
        self.check_raw(q, self.new.extract(q))

    def test_conditions_not_independent_requests(self):
        q = "기회분석이 끝난 뒤 제안참여 의사결정 전에는 어떤 결정이 이루어집니까?"
        rows = self.new.extract(q)
        self.assertEqual(len(rows), 1)
        self.assertGreaterEqual(len(rows[0]["condition_links"]), 2)
        self.assertIn("끝난 뒤", rows[0]["search_text"])
        self.assertIn("의사결정 전", rows[0]["search_text"])
        self.check_raw(q, rows)

    def test_external_conditions_preserved(self):
        q = "10일 이내, 승인 전에 누가 검토하고, 어디에 기록하나요?"
        rows = self.new.extract(q)
        self.assertTrue(any(c["scope"] == "shared_unresolved" for a in rows for c in a["condition_links"]))
        self.assertTrue(all("10일" in a["search_text"] for a in rows))
        self.check_raw(q, rows)

    def test_negative_numeric_and_comparison(self):
        for q in ["검토하지 않아도 되는 경우는 언제인가요?", "10일 이내 어떤 서류를 제출하나요?",
                  "A가 아닌 경우 어떻게 처리하나요?", "A와 B는 어떻게 다른가요?"]:
            rows = self.new.extract(q)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["search_text"], q)

    def test_no_padding(self):
        self.assertEqual(len(self.new.extract("담당자는 누구인가요?")), 1)

    def test_fallback(self):
        self.assertEqual(self.new.extract("검토 절차 설명 부탁드립니다.")[0]["search_text"], "검토 절차 설명 부탁드립니다.")

    def test_no_cap_twelve(self):
        q = ", ".join(f"업무{i}는 누가 담당하나요?" for i in range(12))
        self.assertEqual(len(self.new.extract(q)), 12)

    def test_deterministic(self):
        q = "검토는 누가 하고, 무엇을 확인하나요?"
        self.assertEqual(self.new.extract(q), self.new.extract(q))

    def test_empty(self):
        with self.assertRaises(ValueError):
            self.new.extract(" ")

    def test_selector_backward_equivalence(self):
        rng = np.random.default_rng(2)
        for m in (1, 2, 3):
            R, M = rng.random(10), rng.random((m, 10))
            ids = [str(i) for i in range(10)]
            self.assertEqual(select_coverage_set(ids, R, M).to_dict(), select_adaptive_set(ids, R, M).to_dict())

    def test_selector_four_complementary(self):
        ids = ["a", "b", "c", "d"]
        result = select_adaptive_set(ids, np.ones(4), np.eye(4), K=4)
        self.assertEqual(result.evidence_ids, ids)
        self.assertAlmostEqual(result.objective, 1)

    def test_selector_invalid_empty(self):
        with self.assertRaises(ValueError):
            select_adaptive_set(["a"], [1], np.zeros((0, 1)))

    def test_selector_default_still_capped(self):
        with self.assertRaises(ValueError):
            select_coverage_set(["a"], [1], np.ones((4, 1)))

    def test_legacy_all_210_outputs_unchanged(self):
        path = ROOT / "runs/pars_cover_latest_adapted_210_20261001/retrieval.jsonl"
        if not path.exists():
            self.skipTest("Historical artifacts not available")
        checked = 0
        for line in path.read_text().splitlines():
            row = json.loads(line)
            if row["method"] == "PARS_COVER":
                self.assertEqual(self.old.extract(row["question"]), row["aspects"])
                checked += 1
        self.assertEqual(checked, 210)


if __name__ == "__main__":
    unittest.main()
