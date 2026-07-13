#!/usr/bin/env python3
"""Validate two blind PILOT annotations and compute preliminary IAA."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


REQUIRED_COUNT = 40
CATEGORY_FIELDS = ("claim_family", "claim_type", "modality", "promotion_target")
THRESHOLDS = {
    "span_pairwise_f1": 0.85,
    "claim_family_alpha": 0.80,
    "claim_type_alpha": 0.75,
    "modality_alpha": 0.75,
    "promotion_target_alpha": 0.75,
}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.open(encoding="utf-8") if line.strip()]


def spans(claim: dict[str, Any]) -> set[tuple[str, int]]:
    result = set()
    for span in claim.get("source_spans") or []:
        evidence_id = str(span.get("evidence_id") or "")
        start, end = int(span.get("start", 0)), int(span.get("end", 0))
        result.update((evidence_id, offset) for offset in range(start, max(start, end)))
    return result


def claim_overlap(left: dict[str, Any], right: dict[str, Any]) -> float:
    a, b = spans(left), spans(right)
    return len(a & b) / len(a | b) if a or b else 0.0


def align_claims(left: list[dict[str, Any]], right: list[dict[str, Any]]) -> list[tuple[dict[str, Any] | None, dict[str, Any] | None]]:
    candidates = sorted(((claim_overlap(a, b), i, j) for i, a in enumerate(left) for j, b in enumerate(right)), reverse=True)
    used_left: set[int] = set()
    used_right: set[int] = set()
    pairs: list[tuple[dict[str, Any] | None, dict[str, Any] | None]] = []
    for overlap, i, j in candidates:
        if overlap <= 0 or i in used_left or j in used_right:
            continue
        used_left.add(i)
        used_right.add(j)
        pairs.append((left[i], right[j]))
    pairs.extend((claim, None) for i, claim in enumerate(left) if i not in used_left)
    pairs.extend((None, claim) for j, claim in enumerate(right) if j not in used_right)
    return pairs


def alpha_nominal(pairs: list[tuple[str, str]]) -> float | None:
    if not pairs:
        return None
    observed = sum(left != right for left, right in pairs) / len(pairs)
    labels = Counter(label for pair in pairs for label in pair)
    total = sum(labels.values())
    expected_agreement = sum((count / total) ** 2 for count in labels.values())
    expected_disagreement = 1.0 - expected_agreement
    if expected_disagreement == 0:
        return 1.0 if observed == 0 else 0.0
    return 1.0 - observed / expected_disagreement


def validate_annotation(row: dict[str, Any]) -> list[str]:
    errors = []
    if row.get("completion_status") != "COMPLETE":
        errors.append("completion_status must be COMPLETE")
    bundle = row.get("evidence_bundle") or {}
    texts = {bundle.get("target", {}).get("evidence_id"): bundle.get("target", {}).get("text", "")}
    texts.update({item.get("evidence_id"): item.get("text", "") for item in bundle.get("context") or []})
    for index, claim in enumerate(row.get("claims") or []):
        for field in CATEGORY_FIELDS:
            if not claim.get(field):
                errors.append(f"claim[{index}].{field} missing")
        for span_index, span in enumerate(claim.get("source_spans") or []):
            text = texts.get(span.get("evidence_id"))
            start, end = span.get("start"), span.get("end")
            if text is None or not isinstance(start, int) or not isinstance(end, int) or text[start:end] != span.get("text"):
                errors.append(f"claim[{index}].source_spans[{span_index}] invalid")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--annotator-a", type=Path, required=True)
    parser.add_argument("--annotator-b", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    left_rows, right_rows = read_jsonl(args.annotator_a), read_jsonl(args.annotator_b)
    left = {row["evidence_bundle"]["target"]["evidence_id"]: row for row in left_rows}
    right = {row["evidence_bundle"]["target"]["evidence_id"]: row for row in right_rows}
    errors = {
        "annotator_a": {eid: value for eid, row in left.items() if (value := validate_annotation(row))},
        "annotator_b": {eid: value for eid, row in right.items() if (value := validate_annotation(row))},
    }
    ids = sorted(set(left) | set(right))
    if len(ids) != REQUIRED_COUNT or set(left) != set(right):
        errors["packet"] = [f"Expected {REQUIRED_COUNT} matching IDs; A={len(left)}, B={len(right)}, union={len(ids)}"]

    span_tp = span_left = span_right = 0
    categorical: dict[str, list[tuple[str, str]]] = {field: [] for field in CATEGORY_FIELDS}
    aligned_count = 0
    for evidence_id in sorted(set(left) & set(right)):
        for a, b in align_claims(left[evidence_id].get("claims") or [], right[evidence_id].get("claims") or []):
            a_span, b_span = spans(a or {}), spans(b or {})
            span_tp += len(a_span & b_span)
            span_left += len(a_span)
            span_right += len(b_span)
            if a is not None and b is not None:
                aligned_count += 1
            for field in CATEGORY_FIELDS:
                categorical[field].append((str((a or {}).get(field, "<MISSING>")), str((b or {}).get(field, "<MISSING>"))))
    precision = span_tp / span_left if span_left else 0.0
    recall = span_tp / span_right if span_right else 0.0
    span_f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    metrics: dict[str, Any] = {
        "span_pairwise_precision": precision,
        "span_pairwise_recall": recall,
        "span_pairwise_f1": span_f1,
        "aligned_claims": aligned_count,
    }
    for field, pairs in categorical.items():
        metrics[f"{field}_alpha"] = alpha_nominal(pairs)
    checks = {name: metrics.get(name) is not None and metrics[name] >= threshold for name, threshold in THRESHOLDS.items()}
    complete = not any(errors.values())
    result = {
        "status": "PASS" if complete and all(checks.values()) else "FAIL",
        "annotation_complete": complete,
        "metrics": metrics,
        "thresholds": THRESHOLDS,
        "checks": checks,
        "validation_errors": errors,
        "note": "Canonicalization kappa and relation/rule alpha require completed ontology-layer fields and adjudication review; this script reports AWC-layer preliminary IAA.",
    }
    output = args.output or args.annotator_a.parent / "iaa_report.json"
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
