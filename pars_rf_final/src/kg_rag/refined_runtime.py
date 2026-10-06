"""Online callable for unseen questions; saved-score runner uses the same core."""
from time import perf_counter
from .refined_cover import candidate_union, select_variant
from .shared_context import render_shared_context


def score_candidates(question, ids, R, M, raw, reranker):
    indices = candidate_union(ids, R, M)
    passages = [raw.packages[ids[j]].evidence["name"] for j in indices]
    lengths = reranker.tokenizer([question]*len(passages), passages, truncation=False,
                                padding=False, return_length=True)["length"]
    reranker._score_cache.clear()
    logits = reranker.score(question, passages)
    return indices, logits, {"candidate_count": len(indices),
        "truncated_pairs": sum(n > reranker.max_length for n in lengths),
        "max_pair_tokens": max(lengths, default=0), "ce_max_length": reranker.max_length}


def build_refined_row(question, source, ids, R, M, indices, logits, raw, variant):
    selected = select_variant(ids, R, M, indices, logits, variant)
    row = render_shared_context([raw.packages[e].evidence for e in selected["evidence_ids"]],7000)
    row.update({"question": question, "method": "PARS_REFINED", "condition": "D0_ORIGINAL",
                "source_variant": variant, "selection": selected,
                "aspects": source["aspects"], "pcf_candidates": source["pcf_candidates"],
                "taskframe_candidates": source["taskframe_candidates"],
                "evidence": [{"evidence_id": e, "rank": i} for i,e in enumerate(selected["evidence_ids"],1)],
                "candidate_evidence_ids": [ids[j] for j in indices] if variant.startswith("CE_") else list(ids),
                "status": "RETRIEVED" if selected["evidence_ids"] else "NO_CONTEXT"})
    return row


def retrieve_refined(adaptive_runtime, reranker, question, variant):
    start = perf_counter()
    source, scores = adaptive_runtime.retrieve(question, "COVER_STRUCTURED")
    raw = adaptive_runtime.base.embedded.raw
    indices, logits, diagnostic = (score_candidates(question, scores.evidence_ids, scores.R, scores.M, raw, reranker)
                                   if variant.startswith("CE_") else ([], [], {}))
    row = build_refined_row(question, source, scores.evidence_ids, scores.R, scores.M,
                            indices, logits, raw, variant)
    row.update(ce_diagnostic=diagnostic, full_retrieval_ms=1000*(perf_counter()-start))
    return row
