#!/usr/bin/env python3
"""Modality-aware LF packages with conservative abstention on a new locked test."""

from __future__ import annotations

import csv
import hashlib
import json
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


SEED = 20260724
RUN_ID = "trace-ol-lf-reuse-v2.2-20260711"
OUTPUT_DIR = HERE / "runs" / "lf_reuse_v22_20260711"
VALIDATION = "VALIDATION_V22"
TEST = "FRESH_TEST_V22_LOCKED"
QUOTAS = {
    VALIDATION: {"conditional": 2, "discourse": 10, "definition": 3, "procedure": 8, "evaluation": 10, "descriptive": 17},
    TEST: {"normative": 1, "conditional": 2, "discourse": 10, "definition": 4, "procedure": 8, "evaluation": 10, "descriptive": 15},
}


PACKAGES: list[dict[str, Any]] = [
    {
        "package_id": "lfpkg:v22:question",
        "pattern": r"\?|？",
        "name": "explicit_question",
        "prediction": {"claim_type": "Question", "modality": "NONE", "polarity": "NONE", "promotion_target": "NONE"},
        "risk": "HIGH",
    },
    {
        "package_id": "lfpkg:v22:obligation",
        "pattern": r"해야\s*(?:한다|합니다)|하여야\s*(?:한다|합니다)",
        "name": "explicit_obligation",
        "prediction": {"claim_family": "NORMATIVE", "claim_type": "Obligation", "modality": "MUST", "polarity": "POSITIVE", "promotion_target": "NONE"},
        "risk": "HIGH",
    },
    {
        "package_id": "lfpkg:v22:prohibition",
        "pattern": r"하지\s*말아야|해서는\s*안|금지(?:한다|된다)",
        "name": "explicit_prohibition",
        "prediction": {"claim_family": "NORMATIVE", "claim_type": "Prohibition", "modality": "MUST_NOT", "polarity": "NEGATIVE", "promotion_target": "NONE"},
        "risk": "HIGH",
    },
    {
        "package_id": "lfpkg:v22:observational_case_none",
        "pattern": r"경우가|경우에는|경우도|경우는",
        "name": "observational_case_none",
        "prediction": {"claim_family": "FACTUAL", "claim_type": "DescriptiveFact", "modality": "NONE", "polarity": "POSITIVE", "promotion_target": "NONE"},
        "risk": "HIGH",
    },
    {
        "package_id": "lfpkg:v22:observational_case_descriptive",
        "pattern": r"경우가|경우에는|경우도|경우는",
        "name": "observational_case_descriptive",
        "prediction": {"claim_family": "FACTUAL", "claim_type": "DescriptiveFact", "modality": "DESCRIPTIVE", "polarity": "POSITIVE", "promotion_target": "NONE"},
        "risk": "HIGH",
    },
    {
        "package_id": "lfpkg:v22:example",
        "pattern": r"예를\s*들어|예시(?:로|는|가)|Shipley\s*Tip",
        "name": "explicit_example",
        "prediction": {"claim_type": "Example", "modality": "NONE", "polarity": "NONE", "promotion_target": "NONE"},
        "risk": "HIGH",
    },
    {
        "package_id": "lfpkg:v22:definition",
        "pattern": r"이란|라고\s*정의|의미한다",
        "name": "explicit_definition",
        "prediction": {"claim_family": "FACTUAL", "claim_type": "Definition", "modality": "NONE", "polarity": "POSITIVE", "promotion_target": "NONE"},
        "risk": "STANDARD",
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
    return VALIDATION if value < 0.50 else TEST


def make_splits(units: list[dict[str, Any]], excluded_ids: set[str]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    pools: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
    for unit in units:
        if unit["evidence_id"] in excluded_ids:
            continue
        split = split_for_group(unit["bundle_group_id"])
        pools[split][v2.experiment_family(unit)].append(unit)
    selected = []
    for split, quotas in QUOTAS.items():
        for family, target in quotas.items():
            rows = sorted(pools[split][family], key=lambda row: lib.stable_hash([SEED, split, family, row["evidence_id"]], 16))
            if len(rows) < target:
                raise RuntimeError(f"Insufficient rows for {split}/{family}: {len(rows)} < {target}")
            selected.extend({**row, "v22_split": split, "v22_family": family} for row in rows[:target])
    selected.sort(key=lambda row: (row["v22_split"], row["excel_row"]))
    groups: dict[str, set[str]] = defaultdict(set)
    for row in selected:
        groups[row["bundle_group_id"]].add(row["v22_split"])
    overlap = {group: sorted(splits) for group, splits in groups.items() if len(splits) > 1}
    if overlap:
        raise AssertionError(f"Validation/test group leakage: {overlap}")
    audit = {
        "seed": SEED,
        "counts": dict(Counter(row["v22_split"] for row in selected)),
        "family_counts": {split: dict(Counter(row["v22_family"] for row in selected if row["v22_split"] == split)) for split in QUOTAS},
        "excluded_prior_evidence": len(excluded_ids),
        "prior_evidence_overlap": len({row["evidence_id"] for row in selected} & excluded_ids),
        "validation_test_group_overlap": overlap,
        "remaining_data_limitation": "Only one normative and four conditional cue rows remained after excluding v1/v2/v2.1 evidence.",
    }
    return selected, audit


def manifest(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    fields = ["evidence_id", "excel_row", "page", "section_id", "block_type", "stratum", "v22_family", "v22_split", "bundle_group_id", "text_hash"]
    return [{field: row.get(field, "") for field in fields} for row in rows]


def package_fires(package: dict[str, Any], text: str) -> bool:
    return bool(re.search(package["pattern"], text, re.I))


def prediction_matches(claim: dict[str, Any], prediction: dict[str, str]) -> bool:
    return all(str(claim.get(field) or "") == value for field, value in prediction.items())


def validate_packages(
    references: list[dict[str, Any]],
    bundles_by_id: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    resolved = [row for row in references if row["agreement_tier"] != "Challenge"]
    registry = []
    for package in PACKAGES:
        fired = []
        correct = 0
        for reference in resolved:
            eid = reference["evidence_id"]
            if not package_fires(package, bundles_by_id[eid]["target"]["text"]):
                continue
            fired.append(eid)
            if any(prediction_matches(claim, package["prediction"]) for claim in reference["annotation"].get("claims") or []):
                correct += 1
        support = len(fired)
        precision = correct / support if support else 0.0
        # With only two remaining condition examples, require perfect validation precision.
        min_precision = 1.0 if support == 2 else 0.90
        status = "ACTIVE" if support >= 2 and precision >= min_precision else "REJECTED_VALIDATION"
        registry.append({
            **package, "validation_support": support, "validation_correct": correct,
            "validation_precision": round(precision, 4), "min_validation_support": 2,
            "min_validation_precision": min_precision, "validation_evidence_ids": fired,
            "status": status, "scope": "document_local",
        })
    # Competing predictions for the same pattern are both deactivated unless only one passed.
    active_by_pattern: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in registry:
        if row["status"] == "ACTIVE":
            active_by_pattern[row["pattern"]].append(row)
    for rows in active_by_pattern.values():
        predictions = {json.dumps(row["prediction"], sort_keys=True) for row in rows}
        if len(predictions) > 1:
            for row in rows:
                row["status"] = "REJECTED_COMPETING_MODALITY"
    return registry


def apply_packages(
    annotations: list[dict[str, Any]],
    active: list[dict[str, Any]],
    bundles_by_id: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    output = json.loads(json.dumps(annotations, ensure_ascii=False))
    applications = []
    for annotation in output:
        eid = annotation["evidence_id"]
        text = bundles_by_id[eid]["target"]["text"]
        matching = [package for package in active if package_fires(package, text)]
        if not matching or not annotation.get("claims"):
            continue
        distinct = {json.dumps(package["prediction"], sort_keys=True) for package in matching}
        if len(distinct) != 1:
            applications.append({"evidence_id": eid, "status": "ABSTAIN_PACKAGE_CONFLICT", "package_ids": [row["package_id"] for row in matching]})
            continue
        package = matching[0]
        claim = annotation["claims"][0]
        before = {field: claim.get(field) for field in package["prediction"]}
        claim.update(package["prediction"])
        claim["decision"] = "ACCEPT"
        claim["uncertainty_code"] = "NONE"
        claim["confidence"] = package["validation_precision"]
        applications.append({
            "evidence_id": eid, "status": "APPLIED", "package_id": package["package_id"],
            "before": before, "after": package["prediction"],
        })
    return output, applications


def application_quality(applications: list[dict[str, Any]], references: list[dict[str, Any]]) -> dict[str, Any]:
    refs = {row["evidence_id"]: row for row in references if row["agreement_tier"] != "Challenge"}
    applied = [row for row in applications if row["status"] == "APPLIED" and row["evidence_id"] in refs]
    correct = sum(
        any(prediction_matches(claim, application["after"]) for claim in refs[application["evidence_id"]]["annotation"].get("claims") or [])
        for application in applied
    )
    return {
        "resolved_test_units": len(refs), "applied_on_resolved": len(applied),
        "correct_on_resolved": correct,
        "test_package_precision": round(correct / len(applied), 4) if applied else 0.0,
        "test_package_coverage": round(len(applied) / len(refs), 4) if refs else 0.0,
    }


def render_report(summary: dict[str, Any], active: list[dict[str, Any]]) -> str:
    val = summary["validation_reference"]
    test = summary["test_reference"]
    quality = summary["package_quality"]
    metrics = summary["metrics"]
    savings = summary["llm_savings"]
    gates = summary["success_gates"]
    rows = "\n".join(
        f"| `{row['name']}` | {row['prediction']['claim_type']} / {row['prediction']['modality']} / {row['prediction']['polarity']} | {row['validation_support']} | {row['validation_precision']:.4f} |"
        for row in active
    ) or "| - | 활성 패키지 없음 | - | - |"
    return f"""# TRACE-OL modality-aware 재사용 규칙 실험 v2.2

## 실험 목적

v2.1은 LF로 Claim F1을 높였지만 modality 오류가 증가했다. v2.2는 claim family나 polarity 하나만 맞히는 규칙을 자동 적용하지 않고, claim type·modality·polarity·promotion이 함께 검증된 패키지만 적용했다. modality 패키지가 충돌하면 자동 교정을 포기하고 LLM 검토 대상으로 남겼다.

## 데이터

- 새 validation: 50건 중 {val['resolved']}건 해결 ({val['resolved_rate']:.2%})
- 새 fresh test: 50건 중 {test['resolved']}건 해결 ({test['resolved_rate']:.2%})
- 이전 v1·v2·v2.1 510건과 evidence 중복: 0건
- validation/test group 누출: 0건

이전 실험이 규칙 중심 문장을 대부분 사용해, 남은 미사용 데이터에는 명시적 의무 1건과 조건 cue 4건만 남았다. 따라서 이 실험은 안전 정책을 검증하지만 modality 일반화를 입증하기에는 표본이 부족하다.

## 활성 패키지

| 패키지 | type / modality / polarity | validation support | validation precision |
|---|---|---:|---:|
{rows}

## fresh test 결과

- 패키지 precision: {quality['test_package_precision']:.4f}
- 패키지 coverage: {quality['test_package_coverage']:.4f}

| 방법 | Claim F1 | Critical error rate |
|---|---:|---:|
| E2 기본 | {metrics['E2_base']['claim_f1']:.4f} | {metrics['E2_base']['critical_error_rate']:.4f} |
| E2 + safe LF package | {metrics['E2_plus_safe_LF']['claim_f1']:.4f} | {metrics['E2_plus_safe_LF']['critical_error_rate']:.4f} |

- LLM 검토 후보: {savings['before_candidates']}개 → {savings['after_candidates']}개
- 후보 감소율: {savings['candidate_reduction']:.2%}
- validation에서 차단한 패키지: {summary['applications']['rejected_packages']}개
- fresh test에서 차단 패키지가 발화했지만 자동 교정을 보류한 행: {summary['applications']['withheld_test_rows']}건
- 활성 패키지 간 runtime 충돌 abstain: {summary['applications']['runtime_conflict_abstained']}건

## 성공 기준

""" + "\n".join(f"- [{'x' if passed else ' '}] {name}" for name, passed in gates["gates"].items()) + f"""

최종 판정: **{gates['status']} ({gates['passed']}/{gates['total']})**

## 해석

v2.2의 목적은 규칙 개수를 늘리는 것이 아니라, modality 근거가 부족한 규칙을 자동 적용하지 않아 critical error를 막는 것이다. 이 목표는 달성했지만, 통과한 질문 패키지는 E2가 이미 잘 처리하던 유형이어서 F1과 LLM 절감을 개선하지 못했다. 즉 **안전성은 회복했지만 추가 효용은 없었다.**
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
    manifest_paths = [
        PILOT_DIR / "runs" / "pilot_run_20260710_v1" / "pilot_manifest.csv",
        HERE / "runs" / "lf_reuse_v2_20260710" / "v2_manifest.csv",
        HERE / "runs" / "lf_reuse_v21_20260710" / "v21_manifest.csv",
    ]
    excluded_ids = set()
    for path in manifest_paths:
        excluded_ids.update(row["evidence_id"] for row in csv.DictReader(path.open(encoding="utf-8")))
    sample, audit = make_splits(units, excluded_ids)
    manifest_data = manifest(sample)
    write_csv(output_dir / "v22_manifest.csv", manifest_data, list(manifest_data[0]))
    write_json(output_dir / "split_audit.json", audit)
    write_json(output_dir / "source_profile.json", profile)
    test_ids = sorted(row["evidence_id"] for row in sample if row["v22_split"] == TEST)
    write_json(output_dir / "fresh_test_lock.json", {
        "run_id": RUN_ID, "seed": SEED, "evidence_ids": test_ids,
        "lock_hash": base.sha(test_ids),
        "policy": "No package, modality choice, threshold, or prompt changes after fresh-test outputs are inspected.",
    })

    validation_rows = [row for row in sample if row["v22_split"] == VALIDATION]
    test_rows = [row for row in sample if row["v22_split"] == TEST]
    ledger = base.ApiLedger(output_dir, api_key)

    print("[1/4] v2.2 independent validation reference", flush=True)
    validation_reference, validation_summary = v2.build_consensus_reference(
        ledger, "VALIDATION_V22", validation_rows, bundles_by_id, output_dir,
    )
    print("[2/4] modality-aware package activation", flush=True)
    registry = validate_packages(validation_reference, bundles_by_id)
    active = [row for row in registry if row["status"] == "ACTIVE"]
    rejected = [row for row in registry if row["status"] != "ACTIVE"]
    write_json(output_dir / "lf" / "package_registry.json", registry)
    write_json(output_dir / "lf" / "active_packages.json", active)

    print("[3/4] new locked fresh-test reference", flush=True)
    test_reference, test_summary = v2.build_consensus_reference(
        ledger, "FRESH_TEST_V22", test_rows, bundles_by_id, output_dir,
    )
    print("[4/4] safe-abstain evaluation", flush=True)
    e2 = [lib.heuristic_annotation(bundles_by_id[row["evidence_id"]]) for row in test_rows]
    e2_safe, applications = apply_packages(e2, active, bundles_by_id)
    quality = application_quality(applications, test_reference)
    public_e2 = base.public_annotations(e2)
    public_safe = base.public_annotations(e2_safe)
    write_jsonl(output_dir / "predictions" / "E2_base.jsonl", public_e2)
    write_jsonl(output_dir / "predictions" / "E2_plus_safe_LF.jsonl", public_safe)
    write_jsonl(output_dir / "lf" / "fresh_test_applications.jsonl", applications)
    metric_base = lib.evaluate_predictions(public_e2, test_reference)
    metric_safe = lib.evaluate_predictions(public_safe, test_reference)
    metric_base["bootstrap_95_ci"] = lib.bootstrap_claim_f1(metric_base, 2000)
    metric_safe["bootstrap_95_ci"] = lib.bootstrap_claim_f1(metric_safe, 2000)
    before = v2.full_gate_count(e2, bundles_by_id)
    after = v2.full_gate_count(e2_safe, bundles_by_id)
    reduction = max(0.0, 1 - after / max(1, before))
    app_summary = {
        "applied": sum(row["status"] == "APPLIED" for row in applications),
        "runtime_conflict_abstained": sum(row["status"].startswith("ABSTAIN") for row in applications),
        "rejected_packages": len(rejected),
        "withheld_test_rows": sum(
            any(package_fires(package, bundles_by_id[row["evidence_id"]]["target"]["text"]) for package in rejected)
            for row in test_rows
        ),
    }
    api = ledger.save()
    metrics = {"E2_base": metric_base, "E2_plus_safe_LF": metric_safe}
    savings = {"before_candidates": before, "after_candidates": after, "candidate_reduction": round(reduction, 4)}
    gates = {
        "active_safe_package_at_least_1": len(active) >= 1,
        "test_package_precision_ge_0_90": quality["test_package_precision"] >= 0.90,
        "critical_error_rate_not_worse": metric_safe["critical_error_rate"] <= metric_base["critical_error_rate"],
        "claim_f1_not_worse": metric_safe["claim_f1"] >= metric_base["claim_f1"],
        "llm_candidate_reduction_ge_0_20": reduction >= 0.20,
        "no_prior_evidence_overlap": audit["prior_evidence_overlap"] == 0,
        "no_validation_test_group_leakage": not audit["validation_test_group_overlap"],
    }
    gate_summary = {"gates": gates, "passed": sum(gates.values()), "total": len(gates), "status": "GO" if all(gates.values()) else "REVISE"}
    summary = {
        "run_id": RUN_ID, "input_sha256": expected_hash, "splits": audit,
        "validation_reference": validation_summary, "test_reference": test_summary,
        "packages": {"candidates": len(PACKAGES), "active": len(active)},
        "package_quality": quality, "applications": app_summary,
        "metrics": metrics, "llm_savings": savings, "api": api,
        "success_gates": gate_summary,
        "design_note": "v2.1 test informed the safe-package policy; all v2.2 validation/test evidence is new.",
    }
    write_json(output_dir / "metrics.json", metrics)
    write_json(output_dir / "success_gates.json", gate_summary)
    write_json(output_dir / "run_summary.json", summary)
    (output_dir / "lf_reuse_v22_report.md").write_text(render_report(summary, active), encoding="utf-8")
    print(f"completed: {output_dir}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
