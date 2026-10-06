"""PARS-Cover spec section 10: pure, deterministic selection on frozen R/M.

No embedding, graph, reranker, tokenizer or network dependencies live here.
This implementation is derived from the Markdown specification; the referenced
companion coverage_selector.py was not supplied.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Sequence

import numpy as np


@dataclass(frozen=True)
class SelectionResult:
    evidence_ids: list[str]
    indices: list[int]
    steps: list[dict]
    objective: float
    stopped_zero_gain: bool

    def to_dict(self) -> dict:
        return asdict(self)


def _validate(evidence_ids: Sequence[str], R, M, K: int, lam: float, aspect_limit=3):
    ids = list(evidence_ids)
    if not all(isinstance(x, str) and x for x in ids):
        raise ValueError("Evidence IDs must be nonempty strings")
    if len(set(ids)) != len(ids):
        raise ValueError("Duplicate Evidence ID")
    if isinstance(K, bool) or not isinstance(K, int) or K < 1:
        raise ValueError("K must be a positive integer")
    if not np.isfinite(lam) or not 0 <= lam <= 1:
        raise ValueError("lambda must be finite and in [0,1]")
    r, m = np.asarray(R, dtype=np.float64), np.asarray(M, dtype=np.float64)
    if r.shape != (len(ids),) or m.ndim != 2 or m.shape[1] != len(ids):
        raise ValueError("Expected R[N] and M[aspects,N]")
    if m.shape[0] < 1 or (aspect_limit is not None and m.shape[0] > aspect_limit):
        raise ValueError("Aspect count outside configured contract")
    for name, arr in (("R", r), ("M", m)):
        if not np.isfinite(arr).all() or (arr < 0).any() or (arr > 1).any():
            raise ValueError(f"{name} must contain finite scores in [0,1]")
    return ids, r, m


def _select(evidence_ids, R, M, K, lam, independent, aspect_limit=3):
    ids, r, m = _validate(evidence_ids, R, M, K, lam, aspect_limit)
    selected, steps = [], []
    remaining = set(range(len(ids)))
    best = np.zeros(m.shape[0], dtype=np.float64)
    stopped = False
    for _ in range(min(K, len(ids))):
        increments = np.maximum(m - best[:, None], 0)
        coverage = ((1 - lam) / m.shape[0]) * increments.sum(axis=0)
        relevance = (lam / K) * r
        gain = relevance + coverage
        singleton = relevance + ((1 - lam) / m.shape[0]) * m.sum(axis=0)
        criterion = singleton if independent else gain
        index = min(remaining, key=lambda j: (-criterion[j], -r[j], ids[j]))
        # The spec uses epsilon for greedy termination and strict positivity
        # for NO_SET; preserve this distinction for tiny nonzero inputs.
        threshold = 0.0 if independent else 1e-12
        if criterion[index] <= threshold:
            stopped = True
            break
        before = best.copy()
        best = np.maximum(best, m[:, index])
        steps.append({
            "rank": len(selected) + 1, "evidence_id": ids[index],
            "selection_score": float(criterion[index]),
            "marginal_gain": float(gain[index]),
            "relevance_component": float(relevance[index]),
            "coverage_increment": float(coverage[index]),
            "best_before": before.tolist(), "best_after": best.tolist(),
        })
        selected.append(index)
        remaining.remove(index)
    objective = (lam / K) * r[selected].sum() + (1 - lam) * best.mean()
    return SelectionResult([ids[j] for j in selected], selected, steps,
                           float(objective), stopped)


def select_coverage_set(evidence_ids, R, M, K: int = 5,
                        lam: float = 0.5) -> SelectionResult:
    """Return greedy selection order, without a final relevance re-sort."""
    return _select(evidence_ids, R, M, K, lam, False)


def select_independent_singletons(evidence_ids, R, M, K: int = 5,
                                  lam: float = 0.5) -> SelectionResult:
    """Same scores and objective, but rank independent singleton values."""
    return _select(evidence_ids, R, M, K, lam, True)


def select_adaptive_set(evidence_ids, R, M, K=5, lam=.5, *, independent=False):
    """Same frozen objective and tie rules, allowing any positive Aspect count."""
    return _select(evidence_ids, R, M, K, lam, independent, aspect_limit=None)
