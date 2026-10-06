"""PARS-Cover numeric core, isolated from the legacy retriever dispatcher.

External embedding preparation and experiment orchestration are deliberately
separate. No Gold, answer, qid, cross-encoder or Aspect graph probe is accepted.
The routing gap policy must be explicitly chosen after the documented mismatch
between the new specification and the legacy implementation is resolved.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import exp

import numpy as np

from .cover_index import CoverIndex
from .cover_selection import select_coverage_set, select_independent_singletons
from .retrieval import MAPPING_RELATION_WEIGHT
from .shared_context import render_shared_context

COVER_METHODS = ("PARS_COVER", "PARS_COVER_NO_SET", "PARS_COVER_TEXT_ONLY")


def _vector(values, dimensions):
    value = np.asarray(values, dtype=np.float32)
    if value.shape != (dimensions,) or not np.isfinite(value).all():
        raise ValueError("Invalid embedding shape or nonfinite vector")
    if not np.isclose(np.linalg.norm(value), 1, rtol=1e-4, atol=1e-5):
        raise ValueError("Expected an L2-normalized embedding")
    return value


def select_pcf_top3(question_vector, index):
    scores = index.group_scores("pcf", question_vector,
                                {"identity": .35, "description": .45, "path": .20},
                                condition="D0_ORIGINAL")
    return [{"id": key, "score": float(np.clip(value, 0, 1))}
            for key, value in sorted(scores.items(), key=lambda x: (-x[1], x[0]))[:3]]


def select_taskframe_top3(question_vector, pcf_top3, index, cover_index, *, gap_policy):
    if gap_policy not in {"spec_fill_missing", "legacy_union_top3"}:
        raise ValueError("Routing gap policy requires an explicit confirmed choice")
    semantic = index.group_scores("taskframe", question_vector,
                                   {"identity": .25, "definition": .25, "aliases": .15, "evidence": .35},
                                   condition="D0_ORIGINAL")
    semantic = {k: float(np.clip(v, 0, 1)) for k, v in semantic.items()}
    distances = {p["id"]: cover_index.pcf_distances(p["id"]) for p in pcf_top3}
    prior = {}
    for mapping in index.mappings:
        relation = mapping["relationship_type"]
        if relation not in MAPPING_RELATION_WEIGHT:
            continue
        properties = mapping.get("properties", {})
        values = []
        for key in ("confidence", "coverage_score"):
            value = properties.get(key)
            value = .5 if value in (None, "") else float(value)
            if not np.isfinite(value) or not 0 <= value <= 1:
                raise ValueError(f"Mapping {key} is outside [0,1]")
            values.append(value)
        metadata = .55 + .25 * values[0] + .20 * values[1]
        for pcf in pcf_top3:
            distance = distances[pcf["id"]].get(mapping["pcf_id"])
            if distance is None or distance > 2:
                continue
            tid = mapping["taskframe_id"]
            if tid not in semantic:
                raise ValueError("TaskFrame mapping references unknown node")
            value = pcf["score"] * exp(-.55 * distance) * MAPPING_RELATION_WEIGHT[relation] * metadata
            prior[tid] = max(prior.get(tid, 0), value)
    candidates = set(prior)
    ordered = sorted(semantic, key=lambda t: (-semantic[t], t))
    if len(candidates) < 3:
        if gap_policy == "legacy_union_top3":
            candidates.update(ordered[:3])
        else:
            for tid in ordered:
                if len(candidates) >= 3:
                    break
                candidates.add(tid)
    output = [{"id": tid, "semantic_score": semantic[tid], "pcf_prior": prior.get(tid, 0),
               "score": .75 * semantic[tid] + .25 * prior.get(tid, 0),
               "candidate_source": "pcf" if tid in prior else "global_fallback"}
              for tid in candidates]
    return sorted(output, key=lambda t: (-t["score"], t["id"]))[:3]


@dataclass(frozen=True)
class EmbeddedCoverIndex:
    raw: CoverIndex
    evidence_ids: tuple[str, ...]
    vectors: np.ndarray
    owner_indices: np.ndarray
    text_view_indices: np.ndarray
    dimensions: int

    @classmethod
    def prepare(cls, raw: CoverIndex, vectors_by_view_id, *, dimensions: int = 1536):
        ids = tuple(sorted(raw.packages))
        positions = {eid: j for j, eid in enumerate(ids)}
        if set(vectors_by_view_id) != {v.view_id for v in raw.views}:
            raise ValueError("Embedding mapping must match the complete view set")
        vectors = np.asarray([_vector(vectors_by_view_id[v.view_id], dimensions)
                              for v in raw.views], dtype=np.float32).reshape((-1, dimensions))
        owners = np.asarray([positions[v.evidence_id] for v in raw.views], dtype=np.int64)
        text_by_id = {v.evidence_id: j for j, v in enumerate(raw.views) if v.kind == "evidence_text"}
        text_indices = np.asarray([text_by_id[eid] for eid in ids], dtype=np.int64)
        for arr in (vectors, owners, text_indices):
            arr.setflags(write=False)
        return cls(raw, ids, vectors, owners, text_indices, dimensions)


@dataclass(frozen=True)
class EvidenceScores:
    evidence_ids: tuple[str, ...]
    R: np.ndarray
    M: np.ndarray
    text_M: np.ndarray
    H: np.ndarray
    g: np.ndarray
    p: np.ndarray
    t: np.ndarray
    argmax_view_indices: np.ndarray


def score_evidence_once(question, question_vector, aspect_vectors,
                        pcf_top3, taskframe_top3, index: EmbeddedCoverIndex,
                        *, legacy_index, beta: float = .1, aspect_limit=3) -> EvidenceScores:
    if beta != .1:
        raise ValueError("v1 beta is fixed at 0.10")
    if not isinstance(question, str) or not question.strip():
        raise ValueError("Empty question")
    q = _vector(question_vector, index.dimensions)
    av = np.asarray([_vector(a, index.dimensions) for a in aspect_vectors], dtype=np.float32)
    if len(av) < 1 or (aspect_limit is not None and len(av) > aspect_limit):
        raise ValueError("Aspect vector count outside configured contract")
    # Only the original question invokes hybrid lexical/semantic scoring.
    hybrid = legacy_index.evidence_hybrid_scores(question, q)
    if set(hybrid) != set(index.evidence_ids):
        raise ValueError("Hybrid scores must cover exactly the complete Evidence corpus")
    H = np.asarray([hybrid[eid] for eid in index.evidence_ids], dtype=np.float64)
    if not np.isfinite(H).all() or (H < -1e-6).any() or (H > 1+1e-6).any():
        raise ValueError("Invalid hybrid scores")
    H = np.clip(H, 0, 1)
    frame_scores = {t["id"]: t["score"] for t in taskframe_top3}
    distances = [index.raw.pcf_distances(p["id"]) for p in pcf_top3]
    p, t = np.zeros(len(H)), np.zeros(len(H))
    for j, eid in enumerate(index.evidence_ids):
        package = index.raw.packages[eid]
        p[j] = max((1/(1+d[pid]) for d in distances for pid in package.pcf_ids if pid in d), default=0)
        t[j] = max((frame_scores[tid] for tid in package.taskframe_ids if tid in frame_scores), default=0)
    if not np.isfinite(t).all() or (t < 0).any() or (t > 1).any():
        raise ValueError("Invalid TaskFrame score")
    g = .9 + .1 * (.5 * p + .5 * t)
    R = g * H
    similarities = np.clip(av @ index.vectors.T, 0, 1)
    maximum = np.zeros((len(av), len(H)), dtype=np.float32)
    winners = np.full((len(av), len(H)), -1, dtype=np.int64)
    # Segment maxima; sorted canonical view IDs make tied argmax deterministic.
    for a in range(len(av)):
        np.maximum.at(maximum[a], index.owner_indices, similarities[a])
        for v, owner in enumerate(index.owner_indices):
            if winners[a, owner] == -1 and similarities[a, v] == maximum[a, owner]:
                winners[a, owner] = v
    M = maximum * g[None, :]
    text_M = similarities[:, index.text_view_indices] * g[None, :]
    if not (M + 1e-7 >= text_M).all():
        raise AssertionError("Full M is smaller than TEXT_ONLY M")
    for arr in (R, M, text_M, H, g, p, t, winners):
        arr.setflags(write=False)
    return EvidenceScores(index.evidence_ids, R, M, text_M, H, g, p, t, winners)


def select_scored_evidence(scores: EvidenceScores, index: EmbeddedCoverIndex,
                           *, method: str, fixed_budget: int) -> dict:
    if method not in COVER_METHODS:
        raise ValueError(f"Unknown PARS-Cover method: {method}")
    matrix = scores.text_M if method == "PARS_COVER_TEXT_ONLY" else scores.M
    selector = select_independent_singletons if method == "PARS_COVER_NO_SET" else select_coverage_set
    selected = selector(scores.evidence_ids, scores.R, matrix)
    provenance = []
    for position in selected.indices:
        eid = scores.evidence_ids[position]
        package = index.raw.packages[eid]
        matched = []
        for a in range(matrix.shape[0]):
            v = int(index.text_view_indices[position] if method == "PARS_COVER_TEXT_ONLY"
                    else scores.argmax_view_indices[a, position])
            view = index.raw.views[v]
            matched.append({"aspect_index": a, "view_id": view.view_id, "node_id": view.node_id,
                            "kind": view.kind, "text": view.text, "score": float(matrix[a, position]),
                            "supported_by": view.support, "query_match_is_stored_edge": False})
        provenance.append({"evidence_id": eid, "matched_views": matched,
                           "context_edges": package.context_edges,
                           "R": float(scores.R[position]), "H": float(scores.H[position]),
                           "g": float(scores.g[position]), "p": float(scores.p[position]),
                           "t": float(scores.t[position])})
    rendered = render_shared_context([index.raw.packages[eid].evidence for eid in selected.evidence_ids],
                                     fixed_budget)
    return {"method": method, "candidate_count": len(scores.evidence_ids),
            "selection": selected.to_dict(), "provenance": provenance, **rendered}
