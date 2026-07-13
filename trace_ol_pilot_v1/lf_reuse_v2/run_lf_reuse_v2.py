#!/usr/bin/env python3
"""Teacher-to-labeling-function distillation experiment with a fresh locked test."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Callable


HERE = Path(__file__).resolve().parent
PILOT_DIR = HERE.parent
sys.path.insert(0, str(PILOT_DIR))

import pilot_lib as lib  # noqa: E402
import run_pilot as base  # noqa: E402


SEED = 20260711
RUN_ID = "trace-ol-lf-reuse-v2-20260710"
DEFAULT_OUTPUT = HERE / "runs" / "lf_reuse_v2_20260710"
MODEL = base.MODEL_MINI
FAMILIES = ["normative", "conditional", "discourse", "definition", "procedure", "evaluation", "descriptive"]
QUOTAS = {
    "INDUCTION": {"normative": 12, "conditional": 12, "discourse": 12, "definition": 10, "procedure": 12, "evaluation": 12, "descriptive": 20},
    "VALIDATION": {"normative": 8, "conditional": 7, "discourse": 10, "definition": 8, "procedure": 8, "evaluation": 8, "descriptive": 11},
    "FRESH_TEST_LOCKED": {"normative": 7, "conditional": 8, "discourse": 10, "definition": 8, "procedure": 8, "evaluation": 8, "descriptive": 11},
}
SIGNATURE_FIELDS = ["claim_family", "claim_type", "modality", "polarity", "promotion_target"]
HIGH_RISK_TYPES = {"Obligation", "Prohibition", "NecessaryCondition", "ConditionalRule", "Exception", "Example", "CounterExample", "Question", "Quotation"}


FIXED_FEATURES: list[tuple[str, str]] = [
    ("cue:must_not", r"하지\s*말|금지|피해야|해서는\s*안"),
    ("cue:must", r"해야\s*한다|하여야|반드시|필수|해야\s*합니다"),
    ("cue:recommend", r"권장|바람직|하는\s*것이\s*좋|하는\s*것이\s*가장"),
    ("cue:condition", r"경우|만약|라면|때에는|시에는|일\s*때"),
    ("cue:example", r"예를\s*들어|예시|사례|Shipley\s*Tip"),
    ("cue:question", r"\?|？"),
    ("cue:definition", r"이란|정의|의미|말한다"),
    ("cue:process", r"단계|다음|이후|먼저|결과물|산출물|절차"),
    ("cue:evaluation", r"점수|평가|비중|BCM|V\s*>\s*C|Winner\s*\("),
    ("cue:negative", r"않|없|못|아니"),
]
STOP_TOKENS = {
    "그리고", "그러나", "따라서", "위하여", "대한", "통해", "위한", "있는", "있다", "한다", "하는",
    "것이다", "것을", "수", "및", "등", "이", "그", "때", "경우", "단계", "다음", "문서", "내용",
}


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def experiment_family(unit: dict[str, Any]) -> str:
    text = unit["text"]
    if unit["block_type"] == "question" or "?" in text or "？" in text or re.search(r"예를\s*들어|예시|사례|Shipley\s*Tip|인용", text, re.I):
        return "discourse"
    if re.search(r"하지\s*말|금지|피해야|해야\s*한다|하여야|반드시|필수|권장|바람직|하는\s*것이\s*좋", text):
        return "normative"
    if re.search(r"경우|만약|라면|때에는|시에는", text):
        return "conditional"
    if unit["block_type"] in {"markdown_table", "mixed"} or re.search(r"점수|평가|비중|BCM|V\s*>\s*C|Winner\s*\(", text, re.I):
        return "evaluation"
    if re.search(r"이란|정의|의미|말한다", text):
        return "definition"
    if re.search(r"단계|다음|이후|먼저|결과물|산출물|절차", text):
        return "procedure"
    return "descriptive"


def group_partition(group_id: str) -> str:
    value = int(lib.stable_hash([SEED, group_id], 8), 16) / 0xFFFFFFFF
    if value < 0.50:
        return "INDUCTION"
    if value < 0.75:
        return "VALIDATION"
    return "FRESH_TEST_LOCKED"


def make_fresh_splits(units: list[dict[str, Any]], old_ids: set[str]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    pools: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
    group_to_split: dict[str, str] = {}
    for unit in units:
        if unit["evidence_id"] in old_ids:
            continue
        split = group_partition(unit["bundle_group_id"])
        group_to_split[unit["bundle_group_id"]] = split
        pools[split][experiment_family(unit)].append(unit)
    selected: list[dict[str, Any]] = []
    for split, quotas in QUOTAS.items():
        for family, target in quotas.items():
            rows = sorted(pools[split][family], key=lambda row: lib.stable_hash([SEED, split, family, row["evidence_id"]], 16))
            if len(rows) < target:
                raise RuntimeError(f"Insufficient fresh rows for {split}/{family}: {len(rows)} < {target}")
            for row in rows[:target]:
                selected.append({**row, "v2_split": split, "v2_family": family})
    selected.sort(key=lambda row: (row["v2_split"], row["excel_row"]))
    splits_by_group: dict[str, set[str]] = defaultdict(set)
    for row in selected:
        splits_by_group[row["bundle_group_id"]].add(row["v2_split"])
    overlap = {key: sorted(value) for key, value in splits_by_group.items() if len(value) > 1}
    if overlap:
        raise AssertionError(f"Group leakage in v2: {overlap}")
    audit = {
        "seed": SEED,
        "counts": dict(Counter(row["v2_split"] for row in selected)),
        "family_counts": {split: dict(Counter(row["v2_family"] for row in selected if row["v2_split"] == split)) for split in QUOTAS},
        "excluded_v1_evidence": len(old_ids),
        "v1_overlap": len({row["evidence_id"] for row in selected} & old_ids),
        "group_overlap": overlap,
    }
    return selected, audit


def subset_bundles(bundles_by_id: dict[str, dict[str, Any]], rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [bundles_by_id[row["evidence_id"]] for row in rows]


def annotate(
    ledger: base.ApiLedger,
    *,
    phase: str,
    prompt_name: str,
    rows: list[dict[str, Any]],
    bundles_by_id: dict[str, dict[str, Any]],
    role: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    contract = "Return one JSON object with exactly one key `annotations`; include exactly one schema-valid annotation for every input evidence_id."
    prompt = base.prompt_file(prompt_name, contract)
    output, issues, skipped = base.annotate_batches(
        ledger,
        phase=phase,
        model=MODEL,
        prompt=prompt,
        bundles=subset_bundles(bundles_by_id, rows),
        sample_rows=rows,
        role=role,
        prompt_version=f"lf_reuse_v2_{role}",
    )
    if skipped:
        raise RuntimeError(f"Unexpected skipped annotations in {phase}: {len(skipped)}")
    return output, issues


def build_consensus_reference(
    ledger: base.ApiLedger,
    split_name: str,
    rows: list[dict[str, Any]],
    bundles_by_id: dict[str, dict[str, Any]],
    output_dir: Path,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    a, issues_a = annotate(ledger, phase=f"{split_name}_A", prompt_name="reference_A.txt", rows=rows, bundles_by_id=bundles_by_id, role=f"{split_name}_A")
    b, issues_b = annotate(ledger, phase=f"{split_name}_B", prompt_name="reference_B.txt", rows=rows, bundles_by_id=bundles_by_id, role=f"{split_name}_B")
    a_by = {row["evidence_id"]: row for row in a}
    b_by = {row["evidence_id"]: row for row in b}
    agreements: dict[str, dict[str, Any]] = {}
    disagreement_ids: list[str] = []
    for row in rows:
        eid = row["evidence_id"]
        complete, details = lib.annotation_agreement(a_by[eid], b_by[eid])
        agreements[eid] = {"agreed": complete, **details}
        if not complete:
            disagreement_ids.append(eid)
    disagreement_set = set(disagreement_ids)
    disagreement_rows = [row for row in rows if row["evidence_id"] in disagreement_set]
    c: list[dict[str, Any]] = []
    issues_c: list[dict[str, Any]] = []
    if disagreement_rows:
        c, issues_c = annotate(ledger, phase=f"{split_name}_C", prompt_name="reference_C_disagreement.txt", rows=disagreement_rows, bundles_by_id=bundles_by_id, role=f"{split_name}_C")
    c_by = {row["evidence_id"]: row for row in c}
    references: list[dict[str, Any]] = []
    for row in rows:
        eid = row["evidence_id"]
        if agreements[eid]["agreed"]:
            references.append({"evidence_id": eid, "agreement_tier": "Silver-A", "annotation": a_by[eid], "resolution": "A_B"})
            continue
        resolved, conflicts = lib.resolve_three_way(a_by[eid], b_by[eid], c_by[eid])
        if resolved is not None:
            references.append({"evidence_id": eid, "agreement_tier": "Silver-B", "annotation": resolved, "resolution": "A_B_C"})
        else:
            references.append({"evidence_id": eid, "agreement_tier": "Challenge", "annotation": a_by[eid], "resolution": "UNRESOLVED", "conflicts": conflicts})
    references.sort(key=lambda item: next(row["excel_row"] for row in rows if row["evidence_id"] == item["evidence_id"]))
    prefix = output_dir / "reference" / split_name.lower()
    write_jsonl(prefix / "annotator_A.jsonl", a)
    write_jsonl(prefix / "annotator_B.jsonl", b)
    write_jsonl(prefix / "annotator_C.jsonl", c)
    write_jsonl(prefix / "reference.jsonl", references)
    write_jsonl(prefix / "span_issues.jsonl", issues_a + issues_b + issues_c)
    summary = {
        "targets": len(rows),
        "tier_counts": dict(Counter(row["agreement_tier"] for row in references)),
        "resolved": sum(row["agreement_tier"] != "Challenge" for row in references),
        "resolved_rate": round(sum(row["agreement_tier"] != "Challenge" for row in references) / len(rows), 4),
        "ab_agreement_rate": round(sum(row["agreed"] for row in agreements.values()) / len(rows), 4),
        "span_issues": len(issues_a + issues_b + issues_c),
    }
    write_json(prefix / "summary.json", summary)
    return references, summary


def tokenize(text: str) -> list[str]:
    tokens = re.findall(r"[가-힣A-Za-z][가-힣A-Za-z0-9_-]*", text.casefold())
    return [token for token in tokens if len(token) >= 2 and token not in STOP_TOKENS]


def features_for(bundle: dict[str, Any], unit: dict[str, Any]) -> set[str]:
    text = bundle["target"]["text"]
    features = {f"block:{unit['block_type']}", f"family:{unit['v2_family']}"}
    for name, pattern in FIXED_FEATURES:
        if re.search(pattern, text, re.I):
            features.add(name)
    tokens = tokenize(text)
    for token in set(tokens):
        features.add(f"tok:{token}")
    for left, right in zip(tokens, tokens[1:]):
        features.add(f"bigram:{left}|{right}")
    return features


def signature(claim: dict[str, Any]) -> tuple[str, ...]:
    return tuple(str(claim.get(field) or "") for field in SIGNATURE_FIELDS)


def signature_dict(value: tuple[str, ...]) -> dict[str, str]:
    return dict(zip(SIGNATURE_FIELDS, value))


def primary_claim(annotation: dict[str, Any]) -> dict[str, Any] | None:
    claims = [claim for claim in annotation.get("claims") or [] if claim.get("decision") != "REJECT"]
    if not claims:
        return None
    claims.sort(key=lambda claim: (
        claim.get("claim_type") not in HIGH_RISK_TYPES,
        claim.get("decision") != "ACCEPT",
        claim.get("source_span", {}).get("start", 0),
    ))
    return claims[0]


def feature_matches(feature: str, bundle: dict[str, Any], unit: dict[str, Any]) -> bool:
    return feature in features_for(bundle, unit)


def induce_rules(
    teacher_annotations: list[dict[str, Any]],
    rows_by_id: dict[str, dict[str, Any]],
    bundles_by_id: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    label_counts: dict[str, Counter[tuple[str, ...]]] = defaultdict(Counter)
    support_ids: dict[tuple[str, tuple[str, ...]], list[str]] = defaultdict(list)
    total_feature_support: Counter[str] = Counter()
    for annotation in teacher_annotations:
        claim = primary_claim(annotation)
        if not claim:
            continue
        eid = annotation["evidence_id"]
        label = signature(claim)
        for feature in features_for(bundles_by_id[eid], rows_by_id[eid]):
            label_counts[feature][label] += 1
            total_feature_support[feature] += 1
            support_ids[(feature, label)].append(eid)
    candidates = []
    for feature, counts in label_counts.items():
        label, correct = counts.most_common(1)[0]
        support = total_feature_support[feature]
        precision = correct / support
        if correct < 3 or precision < 0.75:
            continue
        # Very broad metadata features are useful only when highly precise.
        if (feature.startswith("block:") or feature.startswith("family:")) and precision < 0.90:
            continue
        candidates.append({
            "rule_id": f"lf:v2:{lib.stable_hash([feature, label], 24)}",
            "feature": feature,
            "prediction": signature_dict(label),
            "induction_support": support,
            "induction_correct": correct,
            "induction_precision": round(precision, 4),
            "source_evidence_ids": support_ids[(feature, label)],
            "scope": "document_local",
            "status": "CANDIDATE",
        })
    candidates.sort(key=lambda row: (-row["induction_precision"], -row["induction_correct"], row["feature"]))
    return candidates[:300]


def claim_matches_prediction(claim: dict[str, Any], prediction: dict[str, str]) -> bool:
    return all(str(claim.get(field) or "") == value for field, value in prediction.items())


def validate_rules(
    candidates: list[dict[str, Any]],
    references: list[dict[str, Any]],
    rows_by_id: dict[str, dict[str, Any]],
    bundles_by_id: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    resolved = [row for row in references if row["agreement_tier"] != "Challenge"]
    output = []
    for candidate in candidates:
        fired = []
        correct = 0
        for reference in resolved:
            eid = reference["evidence_id"]
            if not feature_matches(candidate["feature"], bundles_by_id[eid], rows_by_id[eid]):
                continue
            fired.append(eid)
            if any(claim_matches_prediction(claim, candidate["prediction"]) for claim in reference["annotation"].get("claims") or []):
                correct += 1
        support = len(fired)
        precision = correct / support if support else 0.0
        claim_type = candidate["prediction"]["claim_type"]
        min_precision = 0.90 if claim_type in HIGH_RISK_TYPES else 0.85
        min_support = 3
        status = "ACTIVE" if support >= min_support and precision >= min_precision else "REJECTED_VALIDATION"
        output.append({
            **candidate,
            "validation_support": support,
            "validation_correct": correct,
            "validation_precision": round(precision, 4),
            "min_validation_precision": min_precision,
            "min_validation_support": min_support,
            "validation_evidence_ids": fired,
            "status": status,
        })
    output.sort(key=lambda row: (row["status"] != "ACTIVE", -row["validation_precision"], -row["validation_support"], row["feature"]))
    return output


def deduplicate_active_rules(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    active = [row for row in rows if row["status"] == "ACTIVE"]
    best: dict[tuple[str, tuple[str, ...]], dict[str, Any]] = {}
    for row in active:
        prediction = tuple(row["prediction"][field] for field in SIGNATURE_FIELDS)
        family = row["feature"].split(":", 1)[0]
        key = family, prediction
        current = best.get(key)
        score = (row["validation_precision"], row["validation_support"], row["induction_precision"], row["induction_support"])
        if current is None or score > (current["validation_precision"], current["validation_support"], current["induction_precision"], current["induction_support"]):
            best[key] = row
    return sorted(best.values(), key=lambda row: (-row["validation_precision"], -row["validation_support"], row["feature"]))


def apply_rules(
    base_annotations: list[dict[str, Any]],
    active_rules: list[dict[str, Any]],
    rows_by_id: dict[str, dict[str, Any]],
    bundles_by_id: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    output = json.loads(json.dumps(base_annotations, ensure_ascii=False))
    applications = []
    for annotation in output:
        eid = annotation["evidence_id"]
        matching = [rule for rule in active_rules if feature_matches(rule["feature"], bundles_by_id[eid], rows_by_id[eid])]
        if not matching or not annotation.get("claims"):
            continue
        votes: dict[tuple[str, ...], float] = defaultdict(float)
        rules_by_prediction: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)
        for rule in matching:
            predicted = tuple(rule["prediction"][field] for field in SIGNATURE_FIELDS)
            weight = max(0.01, rule["validation_precision"] - 0.5) * math.log1p(rule["validation_support"])
            votes[predicted] += weight
            rules_by_prediction[predicted].append(rule)
        ranked = sorted(votes.items(), key=lambda item: (-item[1], item[0]))
        winner, winner_score = ranked[0]
        runner_score = ranked[1][1] if len(ranked) > 1 else 0.0
        if len(ranked) > 1 and winner_score - runner_score < 0.20:
            applications.append({"evidence_id": eid, "status": "ABSTAIN_CONFLICT", "matching_rule_ids": [row["rule_id"] for row in matching]})
            continue
        prediction = signature_dict(winner)
        claim = annotation["claims"][0]
        if prediction["claim_type"] == "ConditionalRule" and not claim.get("conditions"):
            applications.append({"evidence_id": eid, "status": "ABSTAIN_MISSING_CONDITION", "matching_rule_ids": [row["rule_id"] for row in rules_by_prediction[winner]]})
            continue
        before = {field: claim.get(field) for field in SIGNATURE_FIELDS}
        claim.update(prediction)
        claim["decision"] = "ACCEPT" if prediction["promotion_target"] != "NEEDS_REVIEW" else "NEEDS_REVIEW"
        claim["uncertainty_code"] = "NONE" if claim["decision"] == "ACCEPT" else claim.get("uncertainty_code", "OTHER")
        claim["confidence"] = max(rule["validation_precision"] for rule in rules_by_prediction[winner])
        applications.append({
            "evidence_id": eid,
            "status": "APPLIED",
            "before": before,
            "after": prediction,
            "matching_rule_ids": [row["rule_id"] for row in rules_by_prediction[winner]],
            "vote_margin": round(winner_score - runner_score, 4),
        })
    return output, applications


def test_rule_precision(
    applications: list[dict[str, Any]],
    references: list[dict[str, Any]],
) -> dict[str, Any]:
    ref_by_id = {row["evidence_id"]: row for row in references if row["agreement_tier"] != "Challenge"}
    applied = [row for row in applications if row["status"] == "APPLIED" and row["evidence_id"] in ref_by_id]
    correct = 0
    for row in applied:
        ref = ref_by_id[row["evidence_id"]]
        if any(claim_matches_prediction(claim, row["after"]) for claim in ref["annotation"].get("claims") or []):
            correct += 1
    return {
        "resolved_test_units": len(ref_by_id),
        "applied_on_resolved": len(applied),
        "correct_on_resolved": correct,
        "test_rule_precision": round(correct / len(applied), 4) if applied else 0.0,
        "test_rule_coverage": round(len(applied) / len(ref_by_id), 4) if ref_by_id else 0.0,
    }


def full_gate_count(annotations: list[dict[str, Any]], bundles_by_id: dict[str, dict[str, Any]]) -> int:
    count = 0
    for annotation in annotations:
        for claim in annotation.get("claims") or []:
            bundle = bundles_by_id[annotation["evidence_id"]]
            priority = lib.priority_for_claim(claim, bundle)
            confidence = float(claim.get("confidence", 0.5))
            if priority >= 0.65 or (lib.risk_for_claim(claim) >= 0.85 and confidence < 0.90) or claim.get("decision") == "NEEDS_REVIEW":
                count += 1
    return count


def manifest_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    fields = ["evidence_id", "excel_row", "page", "section_id", "block_type", "stratum", "v2_family", "v2_split", "bundle_group_id", "text_hash"]
    return [{field: row.get(field, "") for field in fields} for row in rows]


def render_report(summary: dict[str, Any]) -> str:
    induction = summary["induction"]
    validation = summary["validation_reference"]
    test_ref = summary["test_reference"]
    rules = summary["rules"]
    metrics = summary["metrics"]
    savings = summary["llm_savings"]
    gates = summary["success_gates"]
    return f"""# TRACE-OL 재사용 규칙 실험 v2 결과

## 실험 목적

기존 E3는 6개 조건문만 검토했고 모두 `needs_review`로 남아 재사용 규칙을 만들지 못했다. v2는 새로운 induction 표본 전체에서 teacher LLM의 판정 패턴을 찾고, 별도 validation에서 정확도를 통과한 규칙만 fresh test에 적용했다.

## 방법

1. v1의 180건을 제외한 원문에서 induction 90건, validation 60건, fresh test 60건을 새로 뽑았다.
2. 같은 section·table·list·duplicate group은 서로 다른 split에 들어가지 않게 했다.
3. induction 90건은 teacher LLM이 Claim으로 주석했다.
4. 주석 결과에서 문구, 연속 단어, block type, 문장 family와 Claim 유형의 반복 패턴을 LF 후보로 만들었다.
5. validation은 A/B 독립 주석과 C 다수결로 만든 임시 정답을 사용했다.
6. validation support 3건 이상, 일반 Claim precision 0.85 이상, 고위험 Claim precision 0.90 이상인 LF만 활성화했다.
7. 최종 규칙을 fresh locked test에 적용하고 E2 기본 규칙과 비교했다.

## 데이터와 임시 정답

- induction teacher 주석: {induction['targets']}건
- validation: {validation['targets']}건 중 {validation['resolved']}건 해결, 해소율 {validation['resolved_rate']:.2%}
- fresh test: {test_ref['targets']}건 중 {test_ref['resolved']}건 해결, 해소율 {test_ref['resolved_rate']:.2%}

## 재사용 규칙 결과

- induction LF 후보: {rules['candidates']}개
- validation 통과 LF: {rules['active_before_dedup']}개
- 중복 family 정리 후 최종 LF: {rules['active']}개
- fresh test rule precision: {rules['test_rule_precision']:.4f}
- fresh test rule coverage: {rules['test_rule_coverage']:.4f}

## 성능 비교

| 방법 | Claim F1 | Critical error rate |
|---|---:|---:|
| E2 기본 | {metrics['E2_base']['claim_f1']:.4f} | {metrics['E2_base']['critical_error_rate']:.4f} |
| E2 + 검증된 LF | {metrics['E2_plus_LF']['claim_f1']:.4f} | {metrics['E2_plus_LF']['critical_error_rate']:.4f} |

## LLM 절감 가능성

- LF 적용 전 LLM 검토 후보: {savings['before_candidates']}개
- LF 적용 후 LLM 검토 후보: {savings['after_candidates']}개
- 예상 후보 감소율: {savings['candidate_reduction']:.2%}

## 성공 기준

""" + "\n".join(f"- [{'x' if passed else ' '}] {name}" for name, passed in gates["gates"].items()) + f"""

최종 판정: **{gates['status']} ({gates['passed']}/{gates['total']})**

## 해석 제약

- 임시 정답은 인간 gold가 아니므로 성능은 LLM-Silver 대비 일치도다.
- 표본은 LF family를 검증하기 위해 표적 선정했으므로 전체 문서의 자연 비율을 대표하지 않는다.
- 현 fresh test를 본 후 LF를 수정하면 이 test는 더 이상 최종 평가용으로 사용할 수 없다.
"""


def main() -> int:
    input_candidates = sorted((PILOT_DIR.parent / "handoff-hanyang").rglob("자이제_1.xlsx"))
    if len(input_candidates) != 1:
        raise RuntimeError(f"Expected one input file, found {len(input_candidates)}")
    input_path = input_candidates[0].resolve()
    expected_hash = "e8c5f174b65eccd7a50dbd2e0e216ea870a6aedfd16b3e4538d6486aea15cf1f"
    actual_hash = hashlib.sha256(input_path.read_bytes()).hexdigest()
    if actual_hash != expected_hash:
        raise RuntimeError(f"Input hash mismatch: {actual_hash}")
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is required")
    output_dir = DEFAULT_OUTPUT.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    print("[1/6] fresh group-safe induction/validation/test split", flush=True)
    units, bundles, source_profile = lib.build_all_bundles(input_path)
    bundles_by_id = {bundle["target"]["evidence_id"]: bundle for bundle in bundles}
    v1_manifest = list(csv.DictReader((PILOT_DIR / "runs" / "pilot_run_20260710_v1" / "pilot_manifest.csv").open(encoding="utf-8")))
    old_ids = {row["evidence_id"] for row in v1_manifest}
    sample, split_audit = make_fresh_splits(units, old_ids)
    rows_by_id = {row["evidence_id"]: row for row in sample}
    fields = list(manifest_rows(sample)[0])
    write_csv(output_dir / "v2_manifest.csv", manifest_rows(sample), fields)
    write_json(output_dir / "split_audit.json", split_audit)
    write_json(output_dir / "source_profile.json", source_profile)
    test_ids = sorted(row["evidence_id"] for row in sample if row["v2_split"] == "FRESH_TEST_LOCKED")
    write_json(output_dir / "fresh_test_lock.json", {
        "run_id": RUN_ID, "seed": SEED, "input_sha256": actual_hash,
        "evidence_ids": test_ids, "lock_hash": base.sha(test_ids),
        "policy": "No LF, feature, threshold, or prompt changes after fresh test labels and outputs are inspected.",
    })

    ledger = base.ApiLedger(output_dir, api_key)
    induction_rows = [row for row in sample if row["v2_split"] == "INDUCTION"]
    validation_rows = [row for row in sample if row["v2_split"] == "VALIDATION"]
    test_rows = [row for row in sample if row["v2_split"] == "FRESH_TEST_LOCKED"]

    print("[2/6] teacher annotation on induction split", flush=True)
    induction_annotations, induction_issues = annotate(
        ledger, phase="INDUCTION_TEACHER", prompt_name="system_E1_full_claim.txt",
        rows=induction_rows, bundles_by_id=bundles_by_id, role="LF_V2_TEACHER",
    )
    write_jsonl(output_dir / "induction" / "teacher_annotations.jsonl", induction_annotations)
    write_jsonl(output_dir / "induction" / "span_issues.jsonl", induction_issues)

    print("[3/6] independent validation reference", flush=True)
    validation_reference, validation_summary = build_consensus_reference(
        ledger, "VALIDATION", validation_rows, bundles_by_id, output_dir,
    )

    print("[4/6] LF induction and held-out activation", flush=True)
    candidates = induce_rules(induction_annotations, rows_by_id, bundles_by_id)
    registry = validate_rules(candidates, validation_reference, rows_by_id, bundles_by_id)
    active_before_dedup = [row for row in registry if row["status"] == "ACTIVE"]
    active_rules = deduplicate_active_rules(registry)
    write_json(output_dir / "lf" / "candidate_registry.json", registry)
    write_json(output_dir / "lf" / "active_rules.json", active_rules)

    print("[5/6] locked fresh-test reference and LF evaluation", flush=True)
    test_reference, test_reference_summary = build_consensus_reference(
        ledger, "FRESH_TEST", test_rows, bundles_by_id, output_dir,
    )
    e2_test = [lib.heuristic_annotation(bundles_by_id[row["evidence_id"]]) for row in test_rows]
    e2_lf, applications = apply_rules(e2_test, active_rules, rows_by_id, bundles_by_id)
    rule_test = test_rule_precision(applications, test_reference)
    public_e2 = base.public_annotations(e2_test)
    public_e2_lf = base.public_annotations(e2_lf)
    write_jsonl(output_dir / "predictions" / "E2_base.jsonl", public_e2)
    write_jsonl(output_dir / "predictions" / "E2_plus_LF.jsonl", public_e2_lf)
    write_jsonl(output_dir / "lf" / "fresh_test_applications.jsonl", applications)
    metric_base = lib.evaluate_predictions(public_e2, test_reference)
    metric_lf = lib.evaluate_predictions(public_e2_lf, test_reference)
    metric_base["bootstrap_95_ci"] = lib.bootstrap_claim_f1(metric_base, 2000)
    metric_lf["bootstrap_95_ci"] = lib.bootstrap_claim_f1(metric_lf, 2000)
    before_candidates = full_gate_count(e2_test, bundles_by_id)
    after_candidates = full_gate_count(e2_lf, bundles_by_id)
    candidate_reduction = max(0.0, 1 - after_candidates / max(1, before_candidates))

    print("[6/6] metrics, gates, and report", flush=True)
    api_summary = ledger.save()
    rules_summary = {
        "candidates": len(candidates), "active_before_dedup": len(active_before_dedup), "active": len(active_rules),
        **rule_test,
    }
    metrics = {"E2_base": metric_base, "E2_plus_LF": metric_lf}
    llm_savings = {
        "before_candidates": before_candidates, "after_candidates": after_candidates,
        "candidate_reduction": round(candidate_reduction, 4),
    }
    gates = {
        "active_lf_at_least_1": len(active_rules) >= 1,
        "validation_active_lf_at_least_1": len(active_before_dedup) >= 1,
        "fresh_test_rule_precision_ge_0_85": rule_test["test_rule_precision"] >= 0.85,
        "fresh_test_rule_coverage_ge_0_15": rule_test["test_rule_coverage"] >= 0.15,
        "claim_f1_not_worse": metric_lf["claim_f1"] >= metric_base["claim_f1"],
        "critical_error_rate_not_worse": metric_lf["critical_error_rate"] <= metric_base["critical_error_rate"],
        "llm_candidate_reduction_ge_0_20": candidate_reduction >= 0.20,
        "no_v1_evidence_overlap": split_audit["v1_overlap"] == 0,
        "no_group_leakage": not split_audit["group_overlap"],
    }
    gate_summary = {"gates": gates, "passed": sum(gates.values()), "total": len(gates), "status": "GO" if all(gates.values()) else "REVISE"}
    summary = {
        "run_id": RUN_ID,
        "input_sha256": actual_hash,
        "splits": split_audit,
        "induction": {"targets": len(induction_rows), "span_issues": len(induction_issues)},
        "validation_reference": validation_summary,
        "test_reference": test_reference_summary,
        "rules": rules_summary,
        "metrics": metrics,
        "llm_savings": llm_savings,
        "api": api_summary,
        "success_gates": gate_summary,
    }
    write_json(output_dir / "metrics.json", metrics)
    write_json(output_dir / "success_gates.json", gate_summary)
    write_json(output_dir / "run_summary.json", summary)
    (output_dir / "lf_reuse_v2_report.md").write_text(render_report(summary), encoding="utf-8")
    print(f"completed: {output_dir}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
