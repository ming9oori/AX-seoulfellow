"""Relevance-first evidence selection. No Gold, references or qids accepted."""
from __future__ import annotations
import numpy as np
from .cover_selection import _validate


def candidate_union(ids, R, M, *, question_k=40, aspect_k=20):
    ids, r, m = _validate(ids, R, M, 5, .8, aspect_limit=None)
    if question_k < 1 or aspect_k < 1:
        raise ValueError("Positive candidate quotas required")
    def top(v, k):
        return sorted(range(len(ids)), key=lambda j: (-v[j], ids[j]))[:k]
    candidates = set(top(r, question_k))
    for values in m:
        candidates.update(top(values, aspect_k))
    return sorted(candidates, key=lambda j: ids[j])


def sigmoid_logits(logits):
    x = np.asarray(logits, dtype=np.float64)
    if x.ndim != 1 or not np.isfinite(x).all():
        raise ValueError("Finite logit vector required")
    # Stable, monotone transformation; not a calibrated support probability.
    return np.exp(-np.logaddexp(0, -x))


def relevance_first_select(ids, relevance, M, *, coverage=True, K=5, lam=.8):
    ids, r, m = _validate(ids, relevance, M, K, lam, aspect_limit=None)
    if not ids:
        return {"evidence_ids": [], "selection_order": [], "steps": [], "effective_lambda": 1.0}
    # With one requirement, coverage adds no distinct information need. Rank by
    # relevance directly; do not duplicate the original question as a second goal.
    effective = lam if coverage and len(m) > 1 else 1.0
    gated = m * r[None, :]
    order = sorted(range(len(ids)), key=lambda j: (-r[j], ids[j]))
    selected = [order[0]]
    best = gated[:, order[0]].copy()
    steps = [{"evidence_id": ids[order[0]], "reason": "highest_relevance_anchor", "relevance": float(r[order[0]])}]
    remaining = set(order[1:])
    while remaining and len(selected) < K:
        gains = (effective / K) * r + ((1-effective) / len(m)) * np.maximum(gated-best[:,None], 0).sum(axis=0)
        j = min(remaining, key=lambda i: (-gains[i], -r[i], ids[i]))
        steps.append({"evidence_id": ids[j], "reason": "relevance_plus_uncovered_gain", "gain": float(gains[j]), "relevance": float(r[j])})
        selected.append(j); remaining.remove(j); best = np.maximum(best, gated[:,j])
    delivered = sorted(selected, key=lambda j: (-r[j], ids[j]))
    return {"evidence_ids": [ids[j] for j in delivered], "selection_order": [ids[j] for j in selected],
            "steps": steps, "effective_lambda": effective, "coverage_is_support_probability": False}


def select_variant(ids, R, M, candidate_indices, logits, variant):
    if variant not in {"HYBRID_TOP5", "HYBRID_ANCHORED_COVER", "CE_TOP5", "CE_ANCHORED_COVER"}:
        raise ValueError("Unknown refinement variant")
    if variant.startswith("CE_"):
        idx = np.asarray(candidate_indices, dtype=int)
        if len(idx) != len(logits) or len(set(idx.tolist())) != len(idx):
            raise ValueError("Candidate/logit mismatch")
        if np.any(idx < 0) or np.any(idx >= len(ids)):
            raise ValueError("Candidate index outside corpus")
        labels = [ids[j] for j in idx]
        r, m = sigmoid_logits(logits), np.asarray(M)[:,idx]
    else:
        labels, r, m = ids, R, M
    return relevance_first_select(labels, r, m, coverage=variant.endswith("COVER"))
