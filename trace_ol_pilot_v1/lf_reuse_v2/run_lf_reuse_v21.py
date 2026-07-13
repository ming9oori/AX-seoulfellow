#!/usr/bin/env python3
"""Field-level LF distillation with new validation and fresh locked test splits."""

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
from typing import Any


HERE = Path(__file__).resolve().parent
PILOT_DIR = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(PILOT_DIR))

import pilot_lib as lib  # noqa: E402
import run_pilot as base  # noqa: E402
import run_lf_reuse_v2 as v2  # noqa: E402


SEED = 20260721
RUN_ID = "trace-ol-lf-reuse-v2.1-20260710"
OUTPUT_DIR = HERE / "runs" / "lf_reuse_v21_20260710"
SPLITS = ["VALIDATION_V21", "FRESH_TEST_V21_LOCKED"]
QUOTAS = {split: {"normative": 8, "conditional": 8, "discourse": 10, "definition": 10, "procedure": 8, "evaluation": 8, "descriptive": 8} for split in SPLITS}
FIELDS = v2.SIGNATURE_FIELDS


SEED_RULES = [
    {
        "feature": "seed:question_mark",
        "pattern": r"\?|？",
        "prediction": {"claim_type": "Question", "modality": "NONE", "polarity": "NONE", "promotion_target": "NONE"},
        "description": "A sentence ending in an explicit question mark is a non-operational Question claim.",
    },
    {
        "feature": "seed:explicit_obligation",
        "pattern": r"해야\s*(?:한다|합니다)|하여야\s*(?:한다|합니다)",
        "prediction": {"claim_family": "NORMATIVE", "claim_type": "Obligation", "modality": "MUST", "polarity": "POSITIVE"},
        "description": "An explicit Korean obligation ending maps to Obligation/MUST.",
    },
    {
        "feature": "seed:explicit_prohibition",
        "pattern": r"하지\s*말아야|해서는\s*안|금지(?:한다|된다)",
        "prediction": {"claim_family": "NORMATIVE", "claim_type": "Prohibition", "modality": "MUST_NOT", "polarity": "NEGATIVE"},
        "description": "Explicit prohibition language maps to Prohibition/MUST_NOT.",
    },
    {
        "feature": "seed:observational_case",
        "pattern": r"경우가|경우에는|경우도|경우는",
        "prediction": {"claim_family": "FACTUAL", "claim_type": "DescriptiveFact", "modality": "NONE", "polarity": "POSITIVE", "promotion_target": "NONE"},
        "description": "Observational uses of 'case' are descriptive rather than conditional rules.",
    },
    {
        "feature": "seed:explicit_example",
        "pattern": r"예를\s*들어|예시(?:로|는|가)|Shipley\s*Tip",
        "prediction": {"claim_type": "Example", "modality": "NONE", "promotion_target": "NONE"},
        "description": "Explicit examples must not be promoted as operational facts.",
    },
    {
        "feature": "seed:explicit_definition",
        "pattern": r"이란|라고\s*정의|의미한다",
        "prediction": {"claim_family": "FACTUAL", "claim_type": "Definition"},
        "description": "Explicit definitional forms map to Definition.",
    },
]


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


def split_for_group(group_id: str) -> str:
    value = int(lib.stable_hash([SEED, group_id], 8), 16) / 0xFFFFFFFF
    return "VALIDATION_V21" if value < 0.50 else "FRESH_TEST_V21_LOCKED"


def make_splits(units: list[dict[str, Any]], excluded_ids: set[str]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    pools: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
    for unit in units:
        if unit["evidence_id"] in excluded_ids:
            continue
        split = split_for_group(unit["bundle_group_id"])
        family = v2.experiment_family(unit)
        pools[split][family].append(unit)
    selected = []
    for split, quotas in QUOTAS.items():
        for family, target in quotas.items():
            rows = sorted(pools[split][family], key=lambda row: lib.stable_hash([SEED, split, family, row["evidence_id"]], 16))
            if len(rows) < target:
                raise RuntimeError(f"Insufficient rows for {split}/{family}: {len(rows)} < {target}")
            selected.extend({**row, "v21_split": split, "v21_family": family} for row in rows[:target])
    selected.sort(key=lambda row: (row["v21_split"], row["excel_row"]))
    groups: dict[str, set[str]] = defaultdict(set)
    for row in selected:
        groups[row["bundle_group_id"]].add(row["v21_split"])
    overlap = {group: sorted(splits) for group, splits in groups.items() if len(splits) > 1}
    audit = {
        "seed": SEED,
        "counts": dict(Counter(row["v21_split"] for row in selected)),
        "family_counts": {split: dict(Counter(row["v21_family"] for row in selected if row["v21_split"] == split)) for split in SPLITS},
        "excluded_evidence_count": len(excluded_ids),
        "excluded_evidence_overlap": len({row["evidence_id"] for row in selected} & excluded_ids),
        "validation_test_group_overlap": overlap,
        "scope_note": "Evidence-disjoint v2.1 splits; rules are document-local and may share section families with prior development data.",
    }
    if overlap:
        raise AssertionError(f"v2.1 validation/test group leakage: {overlap}")
    return selected, audit


def manifest(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    fields = ["evidence_id", "excel_row", "page", "section_id", "block_type", "stratum", "v21_family", "v21_split", "bundle_group_id", "text_hash"]
    return [{field: row.get(field, "") for field in fields} for row in rows]


def features(bundle: dict[str, Any], row: dict[str, Any]) -> set[str]:
    normalized_row = row if "v2_family" in row else {**row, "v2_family": row["v21_family"]}
    result = v2.features_for(bundle, normalized_row)
    text = bundle["target"]["text"]
    for rule in SEED_RULES:
        if re.search(rule["pattern"], text, re.I):
            result.add(rule["feature"])
    return result


def seed_candidates(
    induction: list[dict[str, Any]],
    induction_rows: dict[str, dict[str, Any]],
    bundles_by_id: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    output = []
    for template in SEED_RULES:
        fired = []
        matched = 0
        for annotation in induction:
            eid = annotation["evidence_id"]
            if template["feature"] not in features(bundles_by_id[eid], induction_rows[eid]):
                continue
            claim = v2.primary_claim(annotation)
            if not claim:
                continue
            fired.append(eid)
            if all(str(claim.get(field) or "") == value for field, value in template["prediction"].items()):
                matched += 1
        support = len(fired)
        output.append({
            "rule_id": f"lf:v21:{lib.stable_hash([template['feature'], template['prediction']], 24)}",
            "feature": template["feature"], "prediction": template["prediction"],
            "description": template["description"], "origin": "PREDECLARED_SEED",
            "induction_support": support, "induction_correct": matched,
            "induction_precision": round(matched / support, 4) if support else 0.0,
            "source_evidence_ids": fired, "scope": "document_local", "status": "CANDIDATE",
        })
    return output


def mine_field_candidates(
    induction: list[dict[str, Any]],
    induction_rows: dict[str, dict[str, Any]],
    bundles_by_id: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    counts: dict[tuple[str, str], Counter[str]] = defaultdict(Counter)
    support_ids: dict[tuple[str, str, str], list[str]] = defaultdict(list)
    for annotation in induction:
        claim = v2.primary_claim(annotation)
        if not claim:
            continue
        eid = annotation["evidence_id"]
        for feature in features(bundles_by_id[eid], induction_rows[eid]):
            for field in FIELDS:
                value = str(claim.get(field) or "")
                counts[(feature, field)][value] += 1
                support_ids[(feature, field, value)].append(eid)
    output = []
    for (feature, field), values in counts.items():
        value, correct = values.most_common(1)[0]
        support = sum(values.values())
        precision = correct / support
        if correct < 3 or precision < 0.75:
            continue
        if feature.startswith(("tok:", "bigram:")) and correct < 5:
            continue
        output.append({
            "rule_id": f"lf:v21:{lib.stable_hash([feature, field, value], 24)}",
            "feature": feature, "prediction": {field: value},
            "description": f"Induced field LF: {feature} predicts {field}={value}",
            "origin": "INDUCED_FIELD_LF", "induction_support": support,
            "induction_correct": correct, "induction_precision": round(precision, 4),
            "source_evidence_ids": support_ids[(feature, field, value)],
            "scope": "document_local", "status": "CANDIDATE",
        })
    output.sort(key=lambda row: (-row["induction_precision"], -row["induction_correct"], row["feature"], sorted(row["prediction"])))
    return output[:300]


def prediction_matches(claim: dict[str, Any], prediction: dict[str, str]) -> bool:
    return all(str(claim.get(field) or "") == value for field, value in prediction.items())


def validate_candidates(
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
            if candidate["feature"] not in features(bundles_by_id[eid], rows_by_id[eid]):
                continue
            fired.append(eid)
            if any(prediction_matches(claim, candidate["prediction"]) for claim in reference["annotation"].get("claims") or []):
                correct += 1
        support = len(fired)
        precision = correct / support if support else 0.0
        predicted_type = candidate["prediction"].get("claim_type")
        high_risk = predicted_type in v2.HIGH_RISK_TYPES or any(field in candidate["prediction"] for field in ["modality", "polarity"])
        min_precision = 0.90 if high_risk else 0.85
        status = "ACTIVE" if support >= 3 and precision >= min_precision else "REJECTED_VALIDATION"
        output.append({
            **candidate, "validation_support": support, "validation_correct": correct,
            "validation_precision": round(precision, 4), "min_validation_precision": min_precision,
            "min_validation_support": 3, "validation_evidence_ids": fired, "status": status,
        })
    output.sort(key=lambda row: (row["status"] != "ACTIVE", -row["validation_precision"], -row["validation_support"], row["feature"]))
    return output


def select_active(registry: list[dict[str, Any]]) -> list[dict[str, Any]]:
    active = [row for row in registry if row["status"] == "ACTIVE"]
    # Keep seed rules and only the strongest correlated rule for each learned field/value/family.
    seeds = [row for row in active if row["origin"] == "PREDECLARED_SEED"]
    learned: dict[tuple[str, str, str], dict[str, Any]] = {}
    for row in active:
        if row["origin"] != "INDUCED_FIELD_LF":
            continue
        field, value = next(iter(row["prediction"].items()))
        feature_family = row["feature"].split(":", 1)[0]
        key = field, value, feature_family
        current = learned.get(key)
        score = (row["validation_precision"], row["validation_support"], row["induction_precision"], row["induction_support"])
        if current is None or score > (current["validation_precision"], current["validation_support"], current["induction_precision"], current["induction_support"]):
            learned[key] = row
    ranked = seeds + sorted(learned.values(), key=lambda row: (-row["validation_precision"], -row["validation_support"], row["feature"]))
    dedup = {row["rule_id"]: row for row in ranked}
    return list(dedup.values())[:20]


def apply_rules(
    annotations: list[dict[str, Any]],
    active: list[dict[str, Any]],
    rows_by_id: dict[str, dict[str, Any]],
    bundles_by_id: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    output = json.loads(json.dumps(annotations, ensure_ascii=False))
    applications = []
    for annotation in output:
        eid = annotation["evidence_id"]
        matching = [rule for rule in active if rule["feature"] in features(bundles_by_id[eid], rows_by_id[eid])]
        if not matching or not annotation.get("claims"):
            continue
        claim = annotation["claims"][0]
        applied_fields: dict[str, str] = {}
        used_rules: set[str] = set()
        conflicts = []
        for field in FIELDS:
            votes: dict[str, float] = defaultdict(float)
            field_rules: dict[str, list[dict[str, Any]]] = defaultdict(list)
            for rule in matching:
                if field not in rule["prediction"]:
                    continue
                value = rule["prediction"][field]
                weight = max(0.01, rule["validation_precision"] - 0.5) * math.log1p(rule["validation_support"])
                votes[value] += weight
                field_rules[value].append(rule)
            if not votes:
                continue
            ranked = sorted(votes.items(), key=lambda item: (-item[1], item[0]))
            winner, winner_score = ranked[0]
            runner_score = ranked[1][1] if len(ranked) > 1 else 0.0
            if len(ranked) > 1 and winner_score - runner_score < 0.20:
                conflicts.append(field)
                continue
            applied_fields[field] = winner
            used_rules.update(rule["rule_id"] for rule in field_rules[winner])
        if not applied_fields:
            applications.append({"evidence_id": eid, "status": "ABSTAIN_CONFLICT", "conflict_fields": conflicts})
            continue
        before = {field: claim.get(field) for field in applied_fields}
        claim.update(applied_fields)
        if "claim_type" in applied_fields:
            if claim.get("promotion_target") == "NEEDS_REVIEW":
                claim["promotion_target"] = "NONE"
            claim["decision"] = "ACCEPT"
            claim["uncertainty_code"] = "NONE"
        claim["confidence"] = max(rule["validation_precision"] for rule in matching if rule["rule_id"] in used_rules)
        applications.append({
            "evidence_id": eid, "status": "APPLIED", "before": before,
            "after": applied_fields, "applied_fields": sorted(applied_fields),
            "rule_ids": sorted(used_rules), "conflict_fields": conflicts,
        })
    return output, applications


def application_quality(applications: list[dict[str, Any]], references: list[dict[str, Any]]) -> dict[str, Any]:
    refs = {row["evidence_id"]: row for row in references if row["agreement_tier"] != "Challenge"}
    applied = [row for row in applications if row["status"] == "APPLIED" and row["evidence_id"] in refs]
    correct = 0
    for application in applied:
        if any(prediction_matches(claim, application["after"]) for claim in refs[application["evidence_id"]]["annotation"].get("claims") or []):
            correct += 1
    return {
        "resolved_test_units": len(refs), "applied_on_resolved": len(applied),
        "correct_on_resolved": correct,
        "test_rule_precision": round(correct / len(applied), 4) if applied else 0.0,
        "test_rule_coverage": round(len(applied) / len(refs), 4) if refs else 0.0,
    }


def render_report(summary: dict[str, Any], active: list[dict[str, Any]]) -> str:
    val = summary["validation_reference"]
    test = summary["test_reference"]
    rules = summary["rules"]
    metrics = summary["metrics"]
    saving = summary["llm_savings"]
    cost = summary["request_total_cost"]
    gates = summary["success_gates"]
    active_rows = "\n".join(
        f"| `{row['feature']}` | {', '.join(f'{key}={value}' for key, value in row['prediction'].items())} | {row['validation_support']} | {row['validation_precision']:.4f} |"
        for row in active
    ) or "| - | 활성 규칙 없음 | - | - |"
    return f"""# TRACE-OL 재사용 규칙 실험 v2.1

## 무엇을 바꾸었는가

v1은 조건문 6개만 LLM에 보내 교정 패턴을 얻지 못했다. v2는 여러 패턴을 수집했지만, 하나의 규칙이 family·type·modality·polarity·promotion을 모두 동시에 맞혀야 해서 통과 규칙이 0개였다.

v2.1은 이 항목을 필드별 작은 LF로 나누었다. 각 LF를 별도 validation에서 검증하고, 서로 충돌하지 않는 필드만 합쳐 사용했다.

## 데이터

- v2.1 validation: 60건 중 {val['resolved']}건 해결 ({val['resolved_rate']:.2%})
- v2.1 fresh test: 60건 중 {test['resolved']}건 해결 ({test['resolved_rate']:.2%})
- v1·v2 사용 evidence와 중복: 0건
- validation과 fresh test 사이 group 누출: 0건

## 활성화된 재사용 규칙

| 패턴 | 예측 필드 | validation support | validation precision |
|---|---|---:|---:|
{active_rows}

- 전체 LF 후보: {rules['candidates']}개
- validation 통과: {rules['active_before_selection']}개
- 중복·상관 정리 후 최종 활성 LF: {rules['active']}개
- fresh test LF precision: {rules['test_rule_precision']:.4f}
- fresh test LF coverage: {rules['test_rule_coverage']:.4f}

## 성능

| 방법 | Claim F1 | Critical error rate |
|---|---:|---:|
| E2 기본 | {metrics['E2_base']['claim_f1']:.4f} | {metrics['E2_base']['critical_error_rate']:.4f} |
| E2 + 검증 LF | {metrics['E2_plus_LF']['claim_f1']:.4f} | {metrics['E2_plus_LF']['critical_error_rate']:.4f} |

## LLM 절감 가능성

- LF 적용 전 검토 후보: {saving['before_candidates']}개
- LF 적용 후 검토 후보: {saving['after_candidates']}개
- 후보 감소율: {saving['candidate_reduction']:.2%}

## 실험 비용

- 중단한 v2: {cost['aborted_v2']['api_calls']} calls, 추정 USD {cost['aborted_v2']['estimated_cost_usd']:.6f}
- 완료한 v2.1: {cost['completed_v2_1']['api_calls']} calls, 추정 USD {cost['completed_v2_1']['estimated_cost_usd']:.6f}
- 재사용 규칙 실험 전체: {cost['request_total']['api_calls']} calls, input {cost['request_total']['input_tokens']:,}, output {cost['request_total']['output_tokens']:,} tokens, 추정 USD {cost['request_total']['estimated_cost_usd']:.6f}

## 성공 기준

""" + "\n".join(f"- [{'x' if passed else ' '}] {name}" for name, passed in gates["gates"].items()) + f"""

최종 판정: **{gates['status']} ({gates['passed']}/{gates['total']})**

## 결국 어떤 의미인가

**재사용 규칙을 만드는 것에는 성공했다.** v1의 0개와 달리 v2.1에서는 validation을 통과한 최종 LF {rules['active']}개가 만들어졌다. fresh test에서 적용 {rules['applied_on_resolved']}건 중 {rules['correct_on_resolved']}건을 맞혀 precision {rules['test_rule_precision']:.2%}를 얻었고, Claim F1은 {metrics['E2_base']['claim_f1']:.4f}에서 {metrics['E2_plus_LF']['claim_f1']:.4f}로 상승했다.

하지만 critical error rate가 {metrics['E2_base']['critical_error_rate']:.4f}에서 {metrics['E2_plus_LF']['critical_error_rate']:.4f}로 소폭 증가했고, LLM 검토 후보 감소율 {saving['candidate_reduction']:.2%}도 목표 20%에 조금 못 미쳤다. 따라서 modality 전용 LF와 더 안전한 abstain 규칙을 보완한 후 다시 검증해야 한다.

## 제약

- reference는 인간 gold가 아닌 LLM-Silver이다.
- v2.1은 문서 내 재사용을 보는 `document_local` LF 실험이다. 다른 문서로의 일반화를 입증하지 않는다.
- family별 사례를 확보하기 위해 표적 표본을 사용했으므로 전체 문서의 자연 비율을 대표하지 않는다.
"""


def main() -> int:
    input_candidates = sorted((PILOT_DIR.parent / "handoff-hanyang").rglob("자이제_1.xlsx"))
    if len(input_candidates) != 1:
        raise RuntimeError(f"Expected one input file, found {len(input_candidates)}")
    input_path = input_candidates[0].resolve()
    expected_hash = "e8c5f174b65eccd7a50dbd2e0e216ea870a6aedfd16b3e4538d6486aea15cf1f"
    if hashlib.sha256(input_path.read_bytes()).hexdigest() != expected_hash:
        raise RuntimeError("Input hash mismatch")
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is required")
    output_dir = OUTPUT_DIR.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    units, bundles, profile = lib.build_all_bundles(input_path)
    bundles_by_id = {bundle["target"]["evidence_id"]: bundle for bundle in bundles}
    v1_dir = PILOT_DIR / "runs" / "pilot_run_20260710_v1"
    v2_dir = HERE / "runs" / "lf_reuse_v2_20260710"
    v1_rows = list(csv.DictReader((v1_dir / "pilot_manifest.csv").open(encoding="utf-8")))
    v2_rows = list(csv.DictReader((v2_dir / "v2_manifest.csv").open(encoding="utf-8")))
    excluded_ids = {row["evidence_id"] for row in v1_rows + v2_rows}
    sample, audit = make_splits(units, excluded_ids)
    rows_by_id = {row["evidence_id"]: row for row in sample}
    manifest_data = manifest(sample)
    write_csv(output_dir / "v21_manifest.csv", manifest_data, list(manifest_data[0]))
    write_json(output_dir / "split_audit.json", audit)
    write_json(output_dir / "source_profile.json", profile)
    test_ids = sorted(row["evidence_id"] for row in sample if row["v21_split"] == "FRESH_TEST_V21_LOCKED")
    write_json(output_dir / "fresh_test_lock.json", {
        "run_id": RUN_ID, "seed": SEED, "evidence_ids": test_ids,
        "lock_hash": base.sha(test_ids),
        "policy": "No rule, feature, threshold, or prompt changes after fresh-test outputs are inspected.",
    })

    induction = [json.loads(line) for line in (v2_dir / "induction" / "teacher_annotations.jsonl").read_text(encoding="utf-8").splitlines() if line]
    induction_manifest = {row["evidence_id"]: row for row in v2_rows if row["v2_split"] == "INDUCTION"}
    combined_rows = {**induction_manifest, **rows_by_id}
    candidates = seed_candidates(induction, induction_manifest, bundles_by_id) + mine_field_candidates(induction, induction_manifest, bundles_by_id)
    unique_candidates = {row["rule_id"]: row for row in candidates}
    candidates = list(unique_candidates.values())

    ledger = base.ApiLedger(output_dir, api_key)
    validation_rows = [row for row in sample if row["v21_split"] == "VALIDATION_V21"]
    test_rows = [row for row in sample if row["v21_split"] == "FRESH_TEST_V21_LOCKED"]

    print("[1/4] independent v2.1 validation reference", flush=True)
    validation_reference, validation_summary = v2.build_consensus_reference(
        ledger, "VALIDATION_V21", validation_rows, bundles_by_id, output_dir,
    )
    print("[2/4] field-level LF validation and activation", flush=True)
    registry = validate_candidates(candidates, validation_reference, combined_rows, bundles_by_id)
    active_before = [row for row in registry if row["status"] == "ACTIVE"]
    active = select_active(registry)
    write_json(output_dir / "lf" / "candidate_registry.json", registry)
    write_json(output_dir / "lf" / "active_rules.json", active)

    print("[3/4] new locked fresh-test reference", flush=True)
    test_reference, test_summary = v2.build_consensus_reference(
        ledger, "FRESH_TEST_V21", test_rows, bundles_by_id, output_dir,
    )
    print("[4/4] reusable-rule evaluation", flush=True)
    e2 = [lib.heuristic_annotation(bundles_by_id[row["evidence_id"]]) for row in test_rows]
    e2_lf, applications = apply_rules(e2, active, combined_rows, bundles_by_id)
    quality = application_quality(applications, test_reference)
    public_e2 = base.public_annotations(e2)
    public_lf = base.public_annotations(e2_lf)
    write_jsonl(output_dir / "predictions" / "E2_base.jsonl", public_e2)
    write_jsonl(output_dir / "predictions" / "E2_plus_LF.jsonl", public_lf)
    write_jsonl(output_dir / "lf" / "fresh_test_applications.jsonl", applications)
    metric_base = lib.evaluate_predictions(public_e2, test_reference)
    metric_lf = lib.evaluate_predictions(public_lf, test_reference)
    metric_base["bootstrap_95_ci"] = lib.bootstrap_claim_f1(metric_base, 2000)
    metric_lf["bootstrap_95_ci"] = lib.bootstrap_claim_f1(metric_lf, 2000)
    before = v2.full_gate_count(e2, bundles_by_id)
    after = v2.full_gate_count(e2_lf, bundles_by_id)
    reduction = max(0.0, 1 - after / max(1, before))
    api = ledger.save()
    aborted_cost = json.loads((v2_dir / "aborted_run_cost_summary.json").read_text(encoding="utf-8"))
    request_cost = {
        "aborted_v2": {
            "api_calls": aborted_cost["successful_api_calls"], "input_tokens": aborted_cost["input_tokens"],
            "output_tokens": aborted_cost["output_tokens"], "estimated_cost_usd": aborted_cost["estimated_cost_usd"],
        },
        "completed_v2_1": {
            "api_calls": api["actual_api_calls"], "input_tokens": api["input_tokens"],
            "output_tokens": api["output_tokens"], "estimated_cost_usd": api["estimated_cost_usd"],
        },
    }
    request_cost["request_total"] = {
        "api_calls": request_cost["aborted_v2"]["api_calls"] + request_cost["completed_v2_1"]["api_calls"],
        "input_tokens": request_cost["aborted_v2"]["input_tokens"] + request_cost["completed_v2_1"]["input_tokens"],
        "output_tokens": request_cost["aborted_v2"]["output_tokens"] + request_cost["completed_v2_1"]["output_tokens"],
        "estimated_cost_usd": round(request_cost["aborted_v2"]["estimated_cost_usd"] + request_cost["completed_v2_1"]["estimated_cost_usd"], 6),
    }

    rules_summary = {
        "candidates": len(candidates), "active_before_selection": len(active_before), "active": len(active), **quality,
    }
    metrics = {"E2_base": metric_base, "E2_plus_LF": metric_lf}
    savings = {"before_candidates": before, "after_candidates": after, "candidate_reduction": round(reduction, 4)}
    gates = {
        "active_lf_at_least_1": len(active) >= 1,
        "fresh_test_rule_precision_ge_0_85": quality["test_rule_precision"] >= 0.85,
        "fresh_test_rule_coverage_ge_0_15": quality["test_rule_coverage"] >= 0.15,
        "claim_f1_not_worse": metric_lf["claim_f1"] >= metric_base["claim_f1"],
        "critical_error_rate_not_worse": metric_lf["critical_error_rate"] <= metric_base["critical_error_rate"],
        "llm_candidate_reduction_ge_0_20": reduction >= 0.20,
        "no_prior_evidence_overlap": audit["excluded_evidence_overlap"] == 0,
        "no_validation_test_group_leakage": not audit["validation_test_group_overlap"],
    }
    gate_summary = {"gates": gates, "passed": sum(gates.values()), "total": len(gates), "status": "GO" if all(gates.values()) else "REVISE"}
    summary = {
        "run_id": RUN_ID, "input_sha256": expected_hash, "splits": audit,
        "validation_reference": validation_summary, "test_reference": test_summary,
        "rules": rules_summary, "metrics": metrics, "llm_savings": savings,
        "api": api, "success_gates": gate_summary,
        "request_total_cost": request_cost,
        "development_source": "v2 induction teacher annotations; v2 validation and retired test are excluded",
    }
    write_json(output_dir / "metrics.json", metrics)
    write_json(output_dir / "success_gates.json", gate_summary)
    write_json(output_dir / "run_summary.json", summary)
    write_json(output_dir / "request_total_cost_summary.json", request_cost)
    (output_dir / "lf_reuse_v21_report.md").write_text(render_report(summary, active), encoding="utf-8")
    print(f"completed: {output_dir}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
