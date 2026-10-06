"""Question-only retrieval dispatcher; evaluators and Gold never enter this module."""
from __future__ import annotations

from collections import deque
from time import perf_counter
import numpy as np

from .common import normalize_text
from .cover_retrieval import (COVER_METHODS, select_pcf_top3, select_taskframe_top3,
                              score_evidence_once, select_scored_evidence)
from .retrieval import QPARetriever
from .role_clause import RoleClauseExtractor
from .shared_context import render_shared_context
from .unsupervised_aspects import PCFGroundedAspectExtractor, P1G_PCF_GROUNDED, P1P_PARS_PROFILE_FREE


class CoverRuntime:
    def __init__(self, graph, embedded, backend, config, legacy_config, rules, budget):
        self.graph, self.embedded, self.backend = graph, embedded, backend
        self.config, self.legacy_config, self.budget = config, legacy_config, budget
        self.extractor = RoleClauseExtractor(rules, kiwi=graph.kiwi)
        self.legacy_extractor = PCFGroundedAspectExtractor(backend, graph, legacy_config["pcf_grounded_aspect"])
        self.reranker = None
        self.legacy_retriever = None
        self.child_edges = {(e["child_id"], e["parent_id"]) for e in graph.snapshot["pcf_child_of"]}

    def load_legacy(self):
        if self.reranker is None:
            from .reranking import CrossEncoderReranker
            self.reranker = CrossEncoderReranker(self.legacy_config["retrieval"]["p0_cross_encoder_rerank"])
            self.legacy_retriever = QPARetriever(self.graph, self.legacy_config["retrieval"], cross_encoder=self.reranker)

    def clear_query_scores(self):
        self.graph._question_vectors.clear()
        self.graph._hybrid_scores.clear()
        self.graph._dense_scores.clear()

    def _metadata_provenance(self, rows, pcfs, frames):
        raw = self.embedded.raw
        frame_values = {f["id"]: f["score"] for f in frames}
        for row in rows:
            package = raw.packages[row["evidence_id"]]
            candidates = []
            for pcf in pcfs:
                distances = raw.pcf_distances(pcf["id"])
                candidates.extend((distances[p], pcf["id"], p) for p in package.pcf_ids if p in distances)
            if candidates:
                distance, source, target = min(candidates)
                parents, queue = {source: None}, deque([source])
                while queue and target not in parents:
                    node = queue.popleft()
                    for neighbor in sorted(raw.pcf_adjacency.get(node, [])):
                        if neighbor not in parents:
                            parents[neighbor] = node
                            queue.append(neighbor)
                path, node = [], target
                while parents[node] is not None:
                    other = parents[node]
                    child, parent = (node, other) if (node, other) in self.child_edges else (other, node)
                    path.append({"source": child, "type": "CHILD_OF", "target": parent,
                                 "origin": "stored_snapshot_endpoint"})
                    node = other
                row["pcf_prior_provenance"] = {"selected_pcf": source, "direct_mapped_pcf": target,
                                                "undirected_distance": distance, "stored_edges": path[::-1]}
            else:
                row["pcf_prior_provenance"] = None
            tids = package.taskframe_ids & frame_values.keys()
            row["taskframe_prior_winner"] = min(tids, key=lambda t: (-frame_values[t], t)) if tids else None

    def cover(self, question, methods=COVER_METHODS, *, include_scores=False):
        self.clear_query_scores()
        start = perf_counter()
        aspects = self.extractor.extract(question)
        aspect_end = perf_counter()
        texts = list(dict.fromkeys([question, *[a["search_text"] for a in aspects]]))
        if len(texts) > 4:
            raise AssertionError("Question plus at most three aspects")
        vectors = dict(zip(texts, self.backend.embed_exact(texts, namespace="pars-cover-query-role-clause-v1")))
        embedded_end = perf_counter()
        pcfs = select_pcf_top3(vectors[question], self.graph)
        frames = select_taskframe_top3(vectors[question], pcfs, self.graph, self.embedded.raw,
                                     gap_policy=self.config["retrieval"]["cover_gap_policy"])
        routing_end = perf_counter()
        scores = score_evidence_once(question, vectors[question], [vectors[a["search_text"]] for a in aspects],
                                     pcfs, frames, self.embedded, legacy_index=self.graph)
        scoring_end = perf_counter()
        output = []
        for method in methods:
            selection_start = perf_counter()
            row = select_scored_evidence(scores, self.embedded, method=method, fixed_budget=self.budget)
            self._metadata_provenance(row["provenance"], pcfs, frames)
            end = perf_counter()
            row.update({"condition": "D0_ORIGINAL", "question": question, "aspects": aspects,
                        "pcf_candidates": pcfs, "taskframe_candidates": frames,
                        "evidence": [{"evidence_id": e, "rank": i} for i, e in enumerate(row["selected_evidence_ids"], 1)],
                        "status": "RETRIEVED" if row["selected_evidence_ids"] else "NO_CONTEXT",
                        "timing": {"aspect_extract_ms": 1000 * (aspect_end - start),
                                   "embedding_lookup_ms": 1000 * (embedded_end - aspect_end),
                                   "routing_ms": 1000 * (routing_end - embedded_end),
                                   "evidence_scoring_ms": 1000 * (scoring_end - routing_end),
                                   "selection_provenance_context_ms": 1000 * (end - selection_start),
                                   "total_ms": 1000 * (end - start),
                                   "shared_three_method_execution": len(methods) > 1},
                        "score_reuse": "R/M computed once for all three variants" if len(methods) > 1 else "standalone recomputation"})
            output.append(row)
        return (output, scores) if include_scores else output

    def legacy(self, question):
        if self.legacy_retriever is None:
            raise RuntimeError("Load legacy model outside timed retrieval")
        self.clear_query_scores()
        self.reranker._score_cache.clear()
        self.reranker._torch.cuda.synchronize()
        start = perf_counter()
        # This constant is only a logging identifier; no dataset ID/answer/Gold is passed.
        aspects = self.legacy_extractor.extract_many([{"qa_id": "query", "question": question}])[0]["variants"][P1G_PCF_GROUNDED]
        aspect_end = perf_counter()
        row = self.legacy_retriever.retrieve(qid="query", question=question, method=P1P_PARS_PROFILE_FREE,
                                           condition="D0_ORIGINAL", aspects=aspects)
        retrieval_end = perf_counter()
        ids = [e["evidence_id"] for e in row["evidence"]]
        legacy_context_chars = len(row["context"])
        row.update(render_shared_context([self.graph.evidence[e] for e in ids], self.budget))
        self.reranker._torch.cuda.synchronize()
        end = perf_counter()
        row.update({"method": "LEGACY_PARS", "legacy_method_id": P1P_PARS_PROFILE_FREE,
                    "legacy_context_chars_not_used": legacy_context_chars,
                    "timing": {"aspect_extract_embedding_grounding_ms": 1000 * (aspect_end - start),
                               "legacy_retrieval_combined_ms": 1000 * (retrieval_end - aspect_end),
                               "shared_context_ms": 1000 * (end - retrieval_end),
                               "total_ms": 1000 * (end - start)}})
        return row
