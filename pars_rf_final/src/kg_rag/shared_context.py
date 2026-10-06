"""Question/Gold-independent evidence-only context budgeting (spec section 11)."""
from __future__ import annotations

import hashlib
from math import ceil
from typing import Mapping, Sequence


class ContextBudgetError(ValueError):
    pass


def evidence_block(evidence: Mapping, rank: int) -> str:
    if not 1 <= rank <= 5:
        raise ValueError("v1 local citation ranks must be 1..5")
    text = evidence.get("name")
    if not isinstance(text, str) or not text.strip():
        raise ValueError("Evidence body is missing; never silently substitute metadata")
    if not evidence.get("id"):
        raise ValueError("Evidence ID is missing")
    return (f"[E{rank}]\nevidence_id: {evidence['id']}\n"
            f"source: {evidence.get('source_file', '')}\n"
            f"page: {evidence.get('page', '')}\n"
            f"section: {evidence.get('section_path', '')}\ntext:\n{text}")


def context_budget(evidence: Sequence[Mapping], K: int = 5) -> dict:
    if not isinstance(K, int) or not 1 <= K <= 5:
        raise ValueError("v1 K must be 1..5")
    lengths = sorted((len(evidence_block(e, 1)) for e in evidence), reverse=True)
    count = min(K, len(lengths))
    required = sum(lengths[:K]) + 2 * max(0, count - 1)
    budget = max(6000, ceil(required / 1000) * 1000)
    return {"mode": "shared_evidence_only", "evidence_count": len(lengths),
            "K": K, "required_chars": required, "budget_chars": budget,
            "safety_limit_chars": 32000,
            "status": "BLOCKED_CONTEXT_BUDGET" if budget > 32000 else "READY",
            "token_limit_verified": False}


def render_shared_context(selected_evidence: Sequence[Mapping], fixed_budget: int) -> dict:
    if not isinstance(fixed_budget, int) or not 6000 <= fixed_budget <= 32000:
        raise ContextBudgetError("BLOCKED_CONTEXT_BUDGET: expected 6000..32000 chars")
    if len(selected_evidence) > 5:
        raise ValueError("More than five selected EvidenceSpans")
    ids = [e["id"] for e in selected_evidence]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate selected Evidence ID")
    context = "\n\n".join(evidence_block(e, i) for i, e in enumerate(selected_evidence, 1))
    if len(context) > fixed_budget:
        raise ContextBudgetError("BLOCKED_CONTEXT_BUDGET: evidence cannot be truncated")
    return {"context": context, "context_sha256": hashlib.sha256(context.encode()).hexdigest(),
            "selected_evidence_ids": ids, "delivered_evidence_ids": ids.copy(),
            "citation_map": {f"E{i}": e for i, e in enumerate(ids, 1)},
            "context_chars": len(context), "truncated": False,
            "context_mode": "shared_evidence_only", "budget_chars": fixed_budget}


def validate_local_citations(citations, citation_map: Mapping[str, str]) -> list[str]:
    if not isinstance(citations, list) or len(citations) > 5:
        raise ValueError("Invalid citation array")
    if any(not isinstance(c, str) or c not in citation_map for c in citations):
        raise ValueError("Citation is not a delivered local Evidence ID")
    if len(set(citations)) != len(citations):
        raise ValueError("Duplicate citation")
    return [citation_map[c] for c in citations]
