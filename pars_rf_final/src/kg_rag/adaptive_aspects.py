"""Question-only variable requirements with conservative condition attachment.

No learned equivalence classifier: only deterministic morphology signatures are
deduplicated. Ambiguous scope is recorded, not asserted as logically resolved.
All search strings are assembled exclusively from original-question spans.
"""
from __future__ import annotations
import copy
import re
from .role_clause import RoleClauseExtractor


class AdaptiveAspectExtractor(RoleClauseExtractor):
    version = "adaptive_requirements_v1"

    def __init__(self, rules, kiwi=None, *, structured=True):
        super().__init__(rules, kiwi, uncapped=True)
        self.structured = structured

    def _signature(self, text):
        # Preserve every content token AND condition cue. Do not collapse synonyms
        # or use cosine similarity to erase opposite temporal/negative conditions.
        tokens = self.kiwi.tokenize(text)
        content = tuple((t.form, t.tag) for t in tokens
                        if t.tag.startswith(("N", "V", "XR", "SL", "SN")))
        conditions = tuple(m.group() for m in self.constraint.finditer(text))
        cues = tuple(m.group() for m in self.cues.finditer(text))
        return content, conditions, cues

    def extract(self, question):
        candidates = super().extract(question)
        if not self.structured:
            return [{**a, "rule_version": "role_clause_uncapped_v1"} for a in candidates]
        primary = [copy.deepcopy(a) for a in candidates if "constraint" not in a["roles"]]
        constraints = [s for a in candidates if "constraint" in a["roles"] for s in a["source_spans"]]
        if not primary:
            raise AssertionError("Original-question fallback missing")
        all_primary_spans = [s for a in primary for s in a["source_spans"]]
        first_cue = self.cues.search(question)
        external = [c for c in constraints if not any(
            s["start"] <= c["start"] and c["end"] <= s["end"] for s in all_primary_spans)
            or (len(primary) > 1 and first_cue and c["end"] <= first_cue.start())]
        output, signatures = [], {}
        for a in primary:
            # Preserve the complete original topic instead of a generic nearest
            # noun (e.g. 'stage'). Only inherited anchors are replaced.
            if a["anchor_spans"] and first_cue and first_cue.start() > 0:
                end = first_cue.start()
                while end > 0 and question[end-1].isspace():
                    end -= 1
                a["anchor_spans"] = [{"start": 0, "end": end, "text": question[:end]}]
            local = [c for c in constraints if any(
                s["start"] <= c["start"] and c["end"] <= s["end"] for s in a["source_spans"])]
            # External conditions (e.g. a comma-separated prefix) are not dropped.
            # Preserve conservatively for each requirement; mark uncertain scope.
            additions = [c for c in external if not any(
                s["start"] <= c["start"] and c["end"] <= s["end"]
                for s in [*a["anchor_spans"], *a["source_spans"]])]
            a["condition_links"] = ([{"span": c, "scope": "local"} for c in local] +
                                    [{"span": c, "scope": "shared_unresolved"} for c in external])
            a["constraint_spans"] = additions
            a["search_text"] = " | ".join(s["text"] for s in
                [*a["anchor_spans"], *additions, *a["source_spans"]])
            a["rule_version"] = self.version
            a["bundled"] = False
            a["merged_source_spans"] = []
            a["selection_reason"] = "independent_information_request" if "intent" in a["roles"] else "original_question_fallback"
            signature = self._signature(a["search_text"])
            # Empty signatures cannot justify semantic equivalence.
            key = signature if signature[0] else (a["search_text"],)
            if key in signatures:
                kept = output[signatures[key]]
                kept["merged_source_spans"].extend(a["source_spans"])
                kept["condition_links"].extend(a["condition_links"])
                kept["selection_reason"] = "equivalent_morphology_merged"
            else:
                signatures[key] = len(output)
                output.append(a)
        for i, a in enumerate(output, 1):
            a["aspect_id"] = f"a{i}"
        return output
