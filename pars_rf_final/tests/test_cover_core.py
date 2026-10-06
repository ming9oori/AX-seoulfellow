from __future__ import annotations

import copy
import itertools
from pathlib import Path
import sys
import unittest
from collections import Counter
from types import SimpleNamespace

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from kg_rag.cover_selection import select_coverage_set, select_independent_singletons
from kg_rag.shared_context import (context_budget, render_shared_context, ContextBudgetError,
                                    validate_local_citations)
from kg_rag.cover_index import build_cover_index, parse_qualifiers
from kg_rag.cover_retrieval import (EmbeddedCoverIndex, score_evidence_once,
                                    select_scored_evidence, select_pcf_top3,
                                    select_taskframe_top3)


def snapshot():
    return {
        "evidence_spans": [{"properties": {"id": e, "name": text, "source_file": "doc",
                                            "page": 1, "section_path": "S"}, "sections": []}
                           for e, text in [("E1", "검토한다."), ("E2", "제출한다."), ("E3", "고아 원문.")]],
        "pcf_processes": [{"properties": {"id": i}} for i in ("P1", "P2", "P3", "DISCONNECTED")],
        "pcf_child_of": [{"child_id": "P2", "parent_id": "P1"}, {"child_id": "P3", "parent_id": "P2"}],
        "taskframes": [{"properties": {"id": f"T{i}"}} for i in range(1, 5)],
        "pcf_mappings": [{"taskframe_id": "T1", "pcf_id": "P2", "relationship_type": "MAPS_TO_PCF", "properties": {}}],
        "facts": [{"properties": {"id": "F1", "subject_raw": "검토자", "predicate_raw": "검토한다",
                                     "object_raw": "제안서", "qualifiers": '[{"type":"temporal","text":"제출 전"}]',
                                     "knowledge_function": "procedure", "quality_status": "accepted"},
                   "evidence_ids": ["E1"], "frame_links": [{"taskframe_id": "T1", "relationship_type": "HAS_CORE_FACT"}],
                   "taskmention_links": []},
                  {"properties": {"id": "F2", "name": "다른 원문의 사실", "quality_status": "accepted"},
                   "evidence_ids": ["E2"], "frame_links": [{"taskframe_id": "T1", "relationship_type": "HAS_CONTEXT_FACT"}],
                   "taskmention_links": []}],
        "taskmentions": [{"properties": {"id": "M1", "name": "검토", "action_raw": "검토한다",
                                             "focal_object_raw": "제안서", "intended_outcome_raw": "오류 제거"},
                          "taskframe_id": "T1", "evidence_ids": ["E1"]}],
    }


class SelectionTests(unittest.TestCase):
    def setUp(self):
        self.ids = ["A", "B", "C"]
        self.r = np.array([.90, .88, .85])
        self.m = np.array([[.95, .94, .10], [.10, .10, .95]])

    def test_spec_example(self):
        self.assertEqual(select_coverage_set(self.ids, self.r, self.m, K=2).evidence_ids, ["A", "C"])
        self.assertEqual(select_independent_singletons(self.ids, self.r, self.m, K=2).evidence_ids, ["A", "B"])

    def test_permutation_invariance(self):
        for order in itertools.permutations(range(3)):
            o = list(order)
            self.assertEqual(select_coverage_set([self.ids[i] for i in o], self.r[o], self.m[:, o], K=2).evidence_ids,
                             ["A", "C"])

    def test_zero_stop(self):
        self.assertEqual(select_coverage_set(["A"], [0], [[0]]).evidence_ids, [])

    def test_empty(self):
        self.assertEqual(select_coverage_set([], [], np.empty((1, 0))).objective, 0)

    def test_fixed_K_with_small_N(self):
        result = select_coverage_set(["A"], [1], [[0]], K=5)
        self.assertAlmostEqual(result.objective, .1)

    def test_duplicate_id(self):
        with self.assertRaises(ValueError):
            select_coverage_set(["A", "A"], [0, 0], [[0, 0]])

    def test_invalid_scores(self):
        for bad in (float("nan"), float("inf"), -1, 1.1):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                select_coverage_set(["A"], [bad], [[.5]])

    def test_invalid_shapes_and_parameters(self):
        for kwargs in ({"K": 0}, {"K": 1.5}, {"lam": -1}, {"lam": float("nan")}):
            with self.assertRaises(ValueError):
                select_coverage_set(["A"], [.5], [[.5]], **kwargs)
        with self.assertRaises(ValueError):
            select_coverage_set(["A"], [.5], [])

    def test_tie_break_R_then_ID(self):
        result = select_coverage_set(["B", "A"], [.5, .5], [[.5, .5]])
        self.assertEqual(result.evidence_ids, ["A", "B"])

    def test_no_final_resort(self):
        result = select_coverage_set(["A", "B"], [.1, .9], [[1, 0]], K=2)
        self.assertEqual(result.evidence_ids, ["A", "B"])

    def test_input_arrays_unchanged_and_marginals_sum(self):
        r, m = self.r.copy(), self.m.copy()
        result = select_coverage_set(self.ids, self.r, self.m, K=2)
        np.testing.assert_array_equal(r, self.r)
        np.testing.assert_array_equal(m, self.m)
        self.assertAlmostEqual(sum(x["marginal_gain"] for x in result.steps), result.objective)

    def test_no_set_strict_positive(self):
        self.assertEqual(select_independent_singletons(["A"], [1e-14], [[0]]).evidence_ids, ["A"])
        self.assertEqual(select_coverage_set(["A"], [1e-14], [[0]]).evidence_ids, [])


class ContextTests(unittest.TestCase):
    def test_corpus_budget_and_exact_bodies(self):
        rows = [r["properties"] for r in snapshot()["evidence_spans"]]
        rows[0]["name"] = "공백  두 개\n원문\t보존" + "가" * 6200
        budget = context_budget(rows)
        self.assertEqual(budget["budget_chars"], 7000)
        out = render_shared_context(rows, 7000)
        self.assertIn(rows[0]["name"], out["context"])
        self.assertEqual(out["selected_evidence_ids"], out["delivered_evidence_ids"])
        self.assertFalse(out["truncated"])

    def test_no_truncation(self):
        with self.assertRaises(ContextBudgetError):
            render_shared_context([{"id": "E", "name": "x"*6100}], 6000)

    def test_safety_limit(self):
        self.assertEqual(context_budget([{"id": "E", "name": "x"*33000}])["status"], "BLOCKED_CONTEXT_BUDGET")

    def test_empty_context(self):
        self.assertEqual(render_shared_context([], 6000)["context"], "")

    def test_citations_only_delivered(self):
        self.assertEqual(validate_local_citations(["E1"], {"E1": "permanent"}), ["permanent"])
        for cites in (["E2"], ["permanent"], ["E1", "E1"], "E1"):
            with self.assertRaises(ValueError):
                validate_local_citations(cites, {"E1": "permanent"})


class IndexTests(unittest.TestCase):
    def test_direct_support_no_sibling_and_orphan(self):
        idx = build_cover_index(snapshot())
        self.assertNotIn("F2", {v.node_id for v in idx.packages["E1"].views})
        self.assertEqual(len(idx.packages["E3"].views), 1)
        self.assertEqual(idx.packages["E3"].taskframe_ids, set())
        self.assertEqual(idx.packages["E1"].pcf_ids, {"P2"})  # not P1 ancestor

    def test_scope_excludes_multisupport_but_keeps_context(self):
        s = snapshot()
        s["taskmentions"][0]["evidence_ids"] = ["E1", "E2"]
        idx = build_cover_index(s)
        self.assertNotIn("M1", {v.node_id for v in idx.views})
        self.assertIn("T1", idx.packages["E2"].taskframe_ids)
        self.assertEqual(idx.audit["counts"]["TaskMention_multi_support_property_excluded"], 1)

    def test_explicit_multisupport_scope(self):
        s = snapshot()
        s["taskmentions"][0]["evidence_ids"] = ["E1", "E2"]
        idx = build_cover_index(s, property_scopes={"M1": {"mention_base": ["E1"], "object": ["E1"]}})
        self.assertIn("M1", {v.node_id for v in idx.packages["E1"].views})
        self.assertNotIn("M1", {v.node_id for v in idx.packages["E2"].views})

    def test_quality_filters(self):
        s = snapshot()
        s["facts"][0]["properties"]["quality_status"] = "quarantined"
        s["taskmentions"][0]["properties"]["quality_status"] = "review_required"
        idx = build_cover_index(s)
        self.assertEqual(len(idx.packages["E1"].views), 1)
        self.assertEqual(idx.packages["E1"].taskframe_ids, set())

    def test_qualifier_parser(self):
        audit = Counter()
        for v in (None, [], {}, "", "null", "[]"):
            self.assertEqual(parse_qualifiers(v, audit), [])
        self.assertEqual(parse_qualifiers({"text": "전", "type": "temporal"}, audit)[0]["text"], "전")
        self.assertEqual(parse_qualifiers("{bad", audit), [])
        self.assertEqual(audit["qualifier_invalid_json"], 1)
        self.assertEqual(parse_qualifiers(7, audit), [])
        self.assertEqual(audit["qualifier_invalid_shape"], 1)

    def test_no_metadata_in_views(self):
        idx = build_cover_index(snapshot())
        self.assertTrue(all(v.node_type in {"EvidenceSpan", "Fact", "TaskMention"} for v in idx.views))
        self.assertTrue(all(v.kind not in {"metadata", "aliases", "section"} for v in idx.views))

    def test_missing_claim_not_invented(self):
        s = snapshot()
        s["facts"][0]["properties"] = {"id": "F1", "qualifiers": {"text": "제출 전"}, "knowledge_function": "procedure"}
        idx = build_cover_index(s)
        self.assertNotIn("F1", {v.node_id for v in idx.views})

    def test_duplicate_text_ids_remain_distinct(self):
        s = snapshot()
        s["evidence_spans"][1]["properties"]["name"] = s["evidence_spans"][0]["properties"]["name"]
        self.assertEqual(len(build_cover_index(s).packages), 3)

    def test_real_distances_and_disconnected_components(self):
        idx = build_cover_index(snapshot())
        self.assertEqual(idx.pcf_distances("P1"), {"P1": 0, "P2": 1, "P3": 2})
        self.assertNotIn("DISCONNECTED", idx.pcf_distances("P1"))

    def test_snapshot_not_modified(self):
        s = snapshot()
        before = copy.deepcopy(s)
        build_cover_index(s)
        self.assertEqual(s, before)


class ScoreTests(unittest.TestCase):
    def setUp(self):
        self.raw = build_cover_index(snapshot())
        vectors = {v.view_id: ([1, 0] if v.kind != "evidence_text" else [0, 1]) for v in self.raw.views}
        self.idx = EmbeddedCoverIndex.prepare(self.raw, vectors, dimensions=2)
        self.calls = 0
        def hybrid(question, vector):
            self.calls += 1
            return {"E1": .9, "E2": .8, "E3": .7}
        self.legacy = SimpleNamespace(evidence_hybrid_scores=hybrid)

    def score(self):
        return score_evidence_once("질문", [1, 0], [[1, 0]], [{"id": "P1", "score": .8}],
                                    [{"id": "T1", "score": .6}], self.idx, legacy_index=self.legacy)

    def test_scores_scope_bounds_and_full_text_relation(self):
        s = self.score()
        self.assertTrue(np.all(s.M >= s.text_M))
        self.assertTrue(np.all((s.g >= .9) & (s.g <= 1)))
        self.assertAlmostEqual(s.g[2], .9)
        self.assertAlmostEqual(s.p[0], .5)
        self.assertFalse(s.R.flags.writeable)

    def test_single_scoring_across_ablations_and_context_order(self):
        s = self.score()
        self.legacy.evidence_hybrid_scores = lambda *a: (_ for _ in ()).throw(AssertionError("rescore"))
        for method in ("PARS_COVER", "PARS_COVER_NO_SET", "PARS_COVER_TEXT_ONLY"):
            result = select_scored_evidence(s, self.idx, method=method, fixed_budget=6000)
            self.assertEqual(result["selection"]["evidence_ids"], result["delivered_evidence_ids"])
            self.assertEqual(result["candidate_count"], 3)
        self.assertEqual(self.calls, 1)

    def test_argmax_tie_uses_canonical_view_id(self):
        s = self.score()
        for j, eid in enumerate(s.evidence_ids):
            matching = [v.view_id for v in self.idx.raw.views if v.evidence_id == eid and v.kind != "evidence_text"]
            if matching:
                self.assertEqual(self.raw.views[s.argmax_view_indices[0,j]].view_id, min(matching))

    def test_invalid_embedding_norm(self):
        with self.assertRaises(ValueError):
            EmbeddedCoverIndex.prepare(self.raw, {v.view_id: [1, 1] for v in self.raw.views}, dimensions=2)

    def test_routing_has_no_aspect_input_and_three_total_frames(self):
        def groups(kind, vector, weights, condition):
            return {"P1": .8, "P2": .7, "P3": .6} if kind == "pcf" else {"T1": .1, "T2": .9, "T3": .8, "T4": .7}
        legacy = SimpleNamespace(group_scores=groups, mappings=snapshot()["pcf_mappings"])
        pcfs = select_pcf_top3([1, 0], legacy)
        frames = select_taskframe_top3([1, 0], pcfs, legacy, self.raw, gap_policy="spec_fill_missing")
        self.assertEqual(len(frames), 3)
        self.assertEqual({f["id"] for f in frames}, {"T1", "T2", "T3"})
        for ignored_aspects in (["A"], ["different"]):
            self.assertEqual(frames, select_taskframe_top3([1, 0], pcfs, legacy, self.raw, gap_policy="spec_fill_missing"))

    def test_unresolved_routing_choice_fails(self):
        with self.assertRaises(ValueError):
            select_taskframe_top3(None, [], None, self.raw, gap_policy="unresolved")

    def test_routing_policies_are_not_silently_equated(self):
        def groups(kind, vector, weights, condition):
            return {"T1": .01, "T2": 1., "T3": .99, "T4": .98}
        legacy = SimpleNamespace(group_scores=groups, mappings=snapshot()["pcf_mappings"])
        p = [{"id": "P1", "score": .01}]
        full = select_taskframe_top3([1, 0], p, legacy, self.raw, gap_policy="legacy_union_top3")
        spec = select_taskframe_top3([1, 0], p, legacy, self.raw, gap_policy="spec_fill_missing")
        self.assertNotEqual([f["id"] for f in full], [f["id"] for f in spec])


if __name__ == "__main__":
    unittest.main()
