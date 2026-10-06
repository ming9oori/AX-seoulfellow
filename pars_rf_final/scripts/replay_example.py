"""Replay the recorded real question without API calls or model downloads."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def replay(check_aspects=True):
    import numpy as np
    from kg_rag.refined_cover import candidate_union, select_variant

    example = json.loads((ROOT / "examples/real_question.json").read_text())
    expected, ce = example["retrieval"], example["ce"]
    with np.load(ROOT / "examples/real_question_scores.npz", allow_pickle=False) as saved:
        ids, R, M = saved["evidence_ids"].tolist(), saved["R"], saved["M"]
    indices = candidate_union(ids, R, M, question_k=40, aspect_k=20)
    assert indices == ce["indices"], "Candidate union differs from recorded run"
    assert [ids[i] for i in indices] == expected["candidate_evidence_ids"]
    selected = select_variant(ids, R, M, indices, ce["logits"], "CE_TOP5")
    assert selected["evidence_ids"] == expected["selected_evidence_ids"]
    if check_aspects:
        from kg_rag.adaptive_aspects import AdaptiveAspectExtractor
        rules = json.loads((ROOT / "config/aspect_rules.json").read_text())
        actual = AdaptiveAspectExtractor(rules).extract(expected["question"])
        assert actual == expected["aspects"], "Aspect extraction differs from recorded run"
    result = {
        "passed": True,
        "question": expected["question"],
        "aspect_texts": [a["search_text"] for a in expected["aspects"]],
        "aspect_extraction_recomputed": check_aspects,
        "candidate_count": len(indices),
        "selected_evidence_ids": selected["evidence_ids"],
        "stored_answer": example["answer"]["prediction_answer"],
        "stored_citations": example["answer"]["citations"],
        "api_calls": 0,
        "scope": "Candidate union and CE ranking replay from saved scores; answer is stored, not newly generated.",
    }
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scores-only", action="store_true", help="Skip Kiwi; only NumPy is required")
    args = parser.parse_args()
    print(json.dumps(replay(not args.scores_only), ensure_ascii=False, indent=2))
