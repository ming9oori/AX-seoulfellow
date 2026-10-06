"""Adaptive Cover runtime; original-question routing and original-body context."""
from time import perf_counter
from .adaptive_aspects import AdaptiveAspectExtractor
from .cover_retrieval import score_evidence_once, select_pcf_top3, select_taskframe_top3
from .cover_selection import select_adaptive_set
from .shared_context import render_shared_context


class AdaptiveRuntime:
    def __init__(self, base, rules):
        self.base = base
        self.extractors = {False: AdaptiveAspectExtractor(rules, base.graph.kiwi, structured=False),
                           True: AdaptiveAspectExtractor(rules, base.graph.kiwi)}

    def retrieve(self, question, method):
        if method == "PARS_COVER":
            rows, scores = self.base.cover(question, methods=[method], include_scores=True)
            return rows[0], scores
        if method not in {"COVER_UNCAPPED", "COVER_STRUCTURED", "STRUCTURED_NO_SET", "STRUCTURED_TEXT_ONLY"}:
            raise ValueError("Unknown adaptive method")
        b = self.base
        b.clear_query_scores()
        start = perf_counter()
        aspects = self.extractors[method != "COVER_UNCAPPED"].extract(question)
        aspect_end = perf_counter()
        texts = list(dict.fromkeys([question, *[a["search_text"] for a in aspects]]))
        # Template is still exact original spans joined by |. Reuse only identical
        # model/dimension/namespace/text keys; changed text cannot hit an old key.
        vectors = dict(zip(texts, b.backend.embed_exact(texts, namespace="pars-cover-query-role-clause-v1")))
        embed_end = perf_counter()
        pcfs = select_pcf_top3(vectors[question], b.graph)
        frames = select_taskframe_top3(vectors[question], pcfs, b.graph, b.embedded.raw,
                                      gap_policy=b.config["retrieval"]["cover_gap_policy"])
        scores = score_evidence_once(question, vectors[question], [vectors[a["search_text"]] for a in aspects],
                                    pcfs, frames, b.embedded, legacy_index=b.graph, aspect_limit=None)
        score_end = perf_counter()
        matrix = scores.text_M if method == "STRUCTURED_TEXT_ONLY" else scores.M
        selected = select_adaptive_set(scores.evidence_ids, scores.R, matrix,
                                       independent=method == "STRUCTURED_NO_SET")
        row = render_shared_context([b.embedded.raw.packages[e].evidence for e in selected.evidence_ids], b.budget)
        best = matrix[:, selected.indices].max(axis=1) if selected.indices else matrix.sum(axis=1)*0
        matches = []
        for j in selected.indices:
            matches.append({"evidence_id": scores.evidence_ids[j], "R": float(scores.R[j]),
                            "aspect_scores": matrix[:, j].tolist(),
                            "matched_view_ids": [b.embedded.raw.views[int(b.embedded.text_view_indices[j]
                                if method == "STRUCTURED_TEXT_ONLY" else scores.argmax_view_indices[i, j])].view_id
                                for i in range(len(aspects))]})
        row.update({"method": method, "condition": "D0_ORIGINAL", "question": question,
                    "aspects": aspects, "pcf_candidates": pcfs, "taskframe_candidates": frames,
                    "selection": selected.to_dict(), "candidate_count": len(scores.evidence_ids),
                    "evidence": [{"evidence_id": e, "rank": i} for i, e in enumerate(selected.evidence_ids, 1)],
                    "status": "RETRIEVED" if selected.indices else "NO_CONTEXT", "provenance": matches,
                    "aspect_best_similarity": best.tolist(),
                    "coverage_is_logical_support": False,
                    "timing": {"total_ms": 1000*(perf_counter()-start),
                               "aspect_extract_ms": 1000*(aspect_end-start),
                               "embedding_ms": 1000*(embed_end-aspect_end),
                               "routing_scoring_ms": 1000*(score_end-embed_end)}})
        return row, scores
