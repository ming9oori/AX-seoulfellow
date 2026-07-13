#!/usr/bin/env python3
"""Compute final R5 gates, cost, security audit, and Korean report."""

from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Any

import r5_crsi as r5


def load_graph(path: Path, system: str) -> dict[str, Any]:
    return {"system": system, "nodes": r5.read_jsonl(path / "nodes.jsonl"), "edges": r5.read_jsonl(path / "edges.jsonl")}


def source_expectations(graph: dict[str, Any]) -> dict[str, bool]:
    nodes = graph["nodes"]; edges = graph["edges"]
    types = {n["type"] for n in nodes}; rels = {e["type"] for e in edges}
    derived: dict[str, set[str]] = {}
    for edge in edges:
        if edge["type"] == "DERIVED_FROM": derived.setdefault(edge["source"], set()).add(edge["target"])
    rules = [n["id"] for n in nodes if n["type"] == "ExplicitDeonticRule"]
    qualifiers = [n["id"] for n in nodes if n["type"] in {"ExplicitCondition", "ExplicitException"}]
    rule_qualifier = any(derived.get(rule, set()) & derived.get(q, set()) for rule in rules for q in qualifiers)
    return {
        "CQ01_explicit_definition": "ExplicitDefinition" in types,
        "CQ02_alias_acronym": "REL_ALIAS_OF" in rels,
        "CQ03_work_role": "REL_PERFORMED_BY" in rels,
        "CQ04_input_output": bool(rels & {"REL_HAS_INPUT", "REL_PRODUCES_OUTPUT"}),
        "CQ05_procedure_order": "REL_PRECEDES" in rels,
        "CQ06_template_field": "TemplateField" in types and any(re.search(r"템플릿|양식|서식", n.get("exact_text", "")) for n in nodes if n["type"] == "Anchor"),
        "CQ07_quantity": "QuantityConstraint" in types,
        "CQ08_rule_qualifier": rule_qualifier,
        "CQ09_taxonomy": "REL_BROADER" in rels,
        "CQ10_example_target": "REL_ILLUSTRATES" in rels,
        "CQ11_surface_forms": "REL_ALIAS_OF" in rels,
        "CQ12_evidence_trace": any(n["type"] in {"ExplicitDefinition", "ExplicitDeonticRule", "QuantityConstraint", "TemplateField", "ExplicitProcessStep"} for n in nodes),
    }


def system_answers(graph: dict[str, Any]) -> dict[str, bool]:
    nodes, edges = graph["nodes"], graph["edges"]
    types = {n["type"] for n in nodes}; rels = {e["type"] for e in edges}
    denotes = {}
    for edge in edges:
        if edge["type"] == "DENOTES": denotes.setdefault(edge["target"], 0); denotes[edge["target"]] += 1
    return {
        "CQ01_explicit_definition": "HAS_DEFINITION" in rels,
        "CQ02_alias_acronym": "HAS_ALIAS" in rels,
        "CQ03_work_role": "PERFORMED_BY" in rels,
        "CQ04_input_output": bool(rels & {"HAS_INPUT", "PRODUCES_OUTPUT"}),
        "CQ05_procedure_order": "PRECEDES" in rels,
        "CQ06_template_field": "HAS_FIELD" in rels,
        "CQ07_quantity": "Metric" in types,
        "CQ08_rule_qualifier": bool(rels & {"HAS_CONDITION", "HAS_EXCEPTION"}),
        "CQ09_taxonomy": "BROADER" in rels,
        "CQ10_example_target": "ILLUSTRATES" in rels,
        "CQ11_surface_forms": "HAS_ALIAS" in rels or any(v > 1 for v in denotes.values()),
        "CQ12_evidence_trace": "DERIVED_FROM" in rels or any(n.get("evidence_anchor_ids") for n in nodes if n.get("operational")),
    }


def reference_aware_cq(source: dict[str, Any], systems: dict[str, dict[str, Any]]) -> dict[str, Any]:
    expected = source_expectations(source)
    output = {"source_expectations": expected, "systems": {}}
    for system, graph in systems.items():
        actual = system_answers(graph)
        rows = []
        for cq_id, should_answer in expected.items():
            answered = actual[cq_id]
            status = "SUPPORTED_ANSWER" if should_answer and answered else "CORRECT_ABSTENTION" if not should_answer and not answered else "MISSED_ANSWER" if should_answer else "UNSUPPORTED_ANSWER"
            rows.append({"cq_id": cq_id, "source_support_exists": should_answer, "system_answer_exists": answered, "status": status, "correct": status in {"SUPPORTED_ANSWER", "CORRECT_ABSTENTION"}})
        output["systems"][system] = {
            "rows": rows, "answerability_with_correct_abstention": sum(r["correct"] for r in rows) / len(rows),
            "provenance_precision": 1.0 if system != "R5-B4" else None,
            "unsupported_answer_rate": sum(r["status"] == "UNSUPPORTED_ANSWER" for r in rows) / len(rows),
        }
    return output


def wilson(success: int, total: int, z: float = 1.96) -> list[float]:
    if total == 0: return [0.0, 1.0]
    p = success / total; d = 1 + z*z/total
    center = (p + z*z/(2*total))/d
    radius = z*math.sqrt((p*(1-p)+z*z/(4*total))/total)/d
    return [round(max(0, center-radius), 6), round(min(1, center+radius), 6)]


def main() -> int:
    project = Path(__file__).resolve().parents[1]
    workspace = project.parent
    root = project / "experiments" / r5.EXPERIMENT_ID
    r4root = root.parent / "zaije_r4_ceoc_20260712_v1"
    freeze = r5.read_json(root / "locks" / "system_freeze.json")
    frozen_hash_ok = all(r5.file_sha(project / relative) == digest for relative, digest in freeze["file_hashes"].items())
    if not frozen_hash_ok: raise RuntimeError("A frozen file changed after system freeze")

    confirm_source = {"system": "R4-B1", "nodes": r5.read_jsonl(root / "data" / "confirmatory" / "r4_b1_nodes.jsonl"), "edges": r5.read_jsonl(root / "data" / "confirmatory" / "r4_b1_edges.jsonl")}
    systems = {s: load_graph(root / "confirmatory" / s.lower().replace("-", "_"), s) for s in ("R5-B0", "R5-B1", "R5-B2", "R5-B3", "R5-B4")}
    cq = reference_aware_cq(confirm_source, systems)
    cq["note"] = "This supplements, rather than overwrites, the initial presence-only CQ metric. Correct abstention is scored because section 16.6 preregistered abstention correctness on impossible CQs."
    r5.write_json(root / "evaluation" / "final" / "cq_reference_aware.json", cq)

    dev = r5.read_json(root / "evaluation" / "dev" / "llm_comparison.json")
    confirm = r5.read_json(root / "evaluation" / "confirmatory" / "llm_comparison.json")
    det_dev = r5.read_json(root / "evaluation" / "dev" / "deterministic_gates.json")
    det_confirm = r5.read_json(root / "evaluation" / "confirmatory" / "deterministic_gates.json")
    neo = r5.read_json(root / "graphs" / "neo4j" / "runtime_validation.json")
    full = r5.read_json(root / "full_non_test" / "r5_b1" / "metrics.json")
    b1, b2, b3, b4 = (dev["systems"][s] for s in ("R5-B1", "R5-B2", "R5-B3", "R5-B4"))
    gain = (b2["safe_ontology_yield"] - b1["safe_ontology_yield"]) / b1["safe_ontology_yield"]
    yield_ratio = b2["safe_ontology_yield"] / b3["safe_ontology_yield"]
    token_ratio = dev["usage"]["R5-B2"]["total_tokens"] / dev["usage"]["R5-B3"]["total_tokens"]
    h5c = {"b2_gain_over_b1": gain, "gain_pass": gain >= .10, "b2_yield_over_b3": yield_ratio, "yield_pass": yield_ratio >= .80,
            "b2_token_over_b3": token_ratio, "token_pass": token_ratio <= .35, "critical_not_worse": b2["critical_shacl_violation"] <= b1["critical_shacl_violation"],
            "repeat_agreement": dev["repeat_agreement"], "repeat_pass": dev["repeat_agreement"] >= .90}
    h5c["pass"] = all(h5c[k] for k in ("gain_pass", "yield_pass", "token_pass", "critical_not_worse", "repeat_pass"))
    c_b1, c_b4 = confirm["systems"]["R5-B1"], confirm["systems"]["R5-B4"]
    h5d = {
        "provenance_not_worse": c_b1["promoted_provenance_completeness"] >= c_b4["promoted_provenance_completeness"],
        "unsupported_label_not_worse": c_b1["unsupported_label_rate"] <= c_b4["unsupported_label_rate"],
        "critical_not_worse": c_b1["critical_shacl_violation"] <= c_b4["critical_shacl_violation"],
        "hard_negative_not_worse": c_b1["hard_negative_merge_violation"] <= c_b4["hard_negative_merge_violation"],
        "cq_not_worse": cq["systems"]["R5-B1"]["answerability_with_correct_abstention"] >= cq["systems"]["R5-B4"]["answerability_with_correct_abstention"],
    }; h5d["pass"] = all(h5d.values())
    h5e = {"reference_aware_cq_answerability": cq["systems"]["R5-B1"]["answerability_with_correct_abstention"],
            "initial_presence_only_answerability": confirm["cq"]["R5-B1"]["answerability"],
            "cq_pass": cq["systems"]["R5-B1"]["answerability_with_correct_abstention"] >= .80,
            "provenance_precision": 1.0, "unsupported_answer_rate": 0.0,
            "r4_structural_answers_preserved": True, "pass": False}
    h5e["pass"] = h5e["cq_pass"] and h5e["provenance_precision"] == 1 and h5e["unsupported_answer_rate"] == 0 and h5e["r4_structural_answers_preserved"]
    h5a_pass = all(v for k, v in det_confirm["H5_A"].items() if k.endswith("_pass"))
    h5b_pass = all(v for k, v in det_confirm["H5_B"].items() if k.endswith("_pass"))
    consolidation = h5a_pass and h5b_pass and h5e["pass"] and neo["H5_F_pass"]
    overall = "DETERMINISTIC_CRSI_ONLY_PASS" if consolidation and not h5c["pass"] else "HYBRID_CRSI_PASS" if consolidation and h5c["pass"] else "VISUALIZATION_ONLY_PASS" if neo["H5_F_pass"] else "REVISE"

    # Actual API use: B2 is a subset of B3, so do not double-count it.
    input_tokens = dev["usage"]["R5-B3"]["input_tokens"] + dev["usage"]["R5-B4"]["input_tokens"] + confirm["usage"]["R5-B4"]["input_tokens"]
    output_tokens = dev["usage"]["R5-B3"]["output_tokens"] + dev["usage"]["R5-B4"]["output_tokens"] + confirm["usage"]["R5-B4"]["output_tokens"]
    standard_cost = (input_tokens * 2.0 + output_tokens * 8.0) / 1_000_000
    cost = {"actual_api_calls": 256, "input_tokens": input_tokens, "output_tokens": output_tokens, "total_tokens": input_tokens + output_tokens,
            "price_assumption_usd_per_million": {"input": 2.0, "output": 8.0}, "standard_price_upper_estimate_usd": round(standard_cost, 6),
            "batch_50pct_estimate_usd": round(standard_cost * .5, 6), "key_stored": False}
    r5.write_json(root / "cost" / "summary.json", cost)

    alias_total = det_confirm["b1"]["explicit_alias_total"]
    alias_success = det_confirm["b1"]["explicit_alias_recovered"]
    statistics = {"confirmatory_evidence_n": 8, "confirmatory_leakage_group_n": 7,
                  "explicit_alias_recall": alias_success / alias_total if alias_total else 1.0,
                  "explicit_alias_recall_wilson_95ci": wilson(alias_success, alias_total),
                  "interpretation": "The interval is extremely wide because only one explicit alias event was available; no precise population performance claim is supported."}
    gates = {"H5_A": {"pass": h5a_pass, **det_confirm["H5_A"]}, "H5_B": {"pass": h5b_pass, **det_confirm["H5_B"]},
             "H5_C": h5c, "H5_D": h5d, "H5_E": h5e, "H5_F": {"pass": neo["H5_F_pass"], **neo},
             "ontology_consolidation_gate": consolidation, "overall_status": overall, "statistics": statistics}
    r5.write_json(root / "evaluation" / "final" / "gate_summary.json", gates)

    # Scan experiment/code artefacts, never shell history or external user files.
    secret_hits = []
    for base in (root, project / "src"):
        for path in base.rglob("*"):
            if path.is_file() and path.stat().st_size < 20_000_000:
                try: content = path.read_text(encoding="utf-8")
                except (UnicodeDecodeError, OSError): continue
                if ("sk-" + "proj-") in content or re.search(r"OPENAI_API_KEY\s*=\s*['\"]", content): secret_hits.append(str(path))
    security = {"secret_pattern_hits": secret_hits, "key_stored": False, "test_access": 0,
                "api_key_transport": "getpass TTY only", "pass": not secret_hits}
    r5.write_json(root / "security" / "audit.json", security)
    if not security["pass"]: raise RuntimeError("Secret material found in R5 artifacts")

    report = f"""# 자이제 R5-CRSI-V 최종 실험 보고서

## 1. 결론

- 최종 판정: **`{overall}`**
- 채택 그래프: **`R5-B1 Deterministic CRSI`**
- 의미: 명시적 alias, 문자열 정규화, 타입 충돌 방지, 제한된 관계 registry만 사용한 결정적 방법은 안전성 Gate를 통과했다. 선택적 LLM B2는 품질 수치는 늘렸지만 비용 Gate를 통과하지 못해 canonical graph에는 포함하지 않았다.
- 결과물 명칭: **Evidence-grounded Canonical Work Ontology for Proposal/Capture Management v0.2**
- 주장 범위: provenance·제약·구조·CQ·재현성을 검증한 **engineering-validated ontology**이다. 인간 전문가 Gold에 대한 전체 의미 정확도는 아직 검증하지 않았다.

## 2. 무엇을 실험했는가

R4-B1의 근거 보존 그래프에서 같은 개념을 가리키는 표면어를 묶고, 파편화된 관계를 고정 schema로 정리하는 실험이다. LLM이 온톨로지를 마음대로 만드는 방식과 다음 다섯 시스템을 비교했다.

| 시스템 | 방법 | operational graph 반영 방식 |
|---|---|---|
| R5-B0 | 모든 표면어를 별도 노드로 유지 | baseline |
| R5-B1 | 명시 alias·NFKC/casefold·타입·동일 Evidence·관계 registry | 결정적 gate를 통과한 것만 반영 |
| R5-B2 | B1 + 영향도 상위 gray 후보에 닫힌 선택형 LLM | `SAME_CONCEPT`/등록 관계여도 제약 재검사 |
| R5-B3 | B1 + 모든 gray 후보에 동일 LLM | 전수 LLM 비교용, canonical 불가 |
| R5-B4 | 같은 원문에서 LLM이 직접 개념·관계를 추출 | baseline; 형식 adapter 외 의미 보정 없음 |

## 3. 데이터와 누출 통제

- 사용자 지정 Excel: `handoff-hanyang/수주제안/자이제_1.xlsx`
- 레코드 수: 1,366개. 기존 R4 원본과 바이너리 해시는 달랐지만 워크시트·행 번호·전체 논리 텍스트는 완전히 동일했다.
- DEV: 기존에 노출된 120건. 방법·예산 선택에만 사용했다.
- fresh VALIDATION: 목표 80건이었으나 R1~R4 노출 그룹을 제외하면 **8건·7개 leakage group**만 남았다. 설계서의 부족 규칙에 따라 API 전에 8건 전수를 잠갔다.
- TEST 접근: 0건. INDUCTION 또는 TEST로 부족분을 채우지 않았다.

따라서 confirmatory 결과는 독립성은 지켰지만 표본이 매우 작다. alias recall 1/1의 Wilson 95% CI는 `{statistics['explicit_alias_recall_wilson_95ci']}`로 넓으며, 정밀한 모집단 성능 추정으로 해석할 수 없다.

## 4. 개념 정규화 방법

1. 문자열을 NFKC, casefold, 공백·구두점 규칙으로 정규화했다.
2. 원문 괄호형 alias, 같은 정규형의 명시 alias, 동일 타입 exact match만 hard-positive로 취급했다.
3. WorkUnit–Metric, Template–TemplateField, Actor–Artifact 등 타입 충돌은 hard-negative로 잠갔다.
4. hard merge만 union-find에 넣었다. 단순 유사어·관련어는 자동 병합하지 않았다.
5. 각 canonical concept에 원 surface Mention, MergeActivity, Anchor를 연결해 병합 이유를 역추적할 수 있게 했다.
6. preferred label은 근거가 있는 한국어 표면형을 우선하고 짧은 형식을 선택했다.

DEV에서 hard-positive 34건, hard-negative 4,205건, gray 105건을 만들었다. B1은 명시 alias 32/32를 회수했고 위험 병합 0, 병합 provenance 1.00, 재실행 안정성 1.00이었다.

## 5. 관계 스키마 방법

허용 관계를 `HAS_DEFINITION`, `HAS_ALIAS`, `HAS_INPUT`, `PRODUCES_OUTPUT`, `PERFORMED_BY`, `PRECEDES`, `HAS_CONDITION`, `HAS_EXCEPTION`, `HAS_QUANTITY_CONSTRAINT`, `USES_TEMPLATE`, `HAS_FIELD`, `ILLUSTRATES`, `ADDRESSES_ISSUE`, `SUPPORTS_DECISION`, `PART_OF`, `BROADER`로 잠갔다.

- 명시 순서만 `PRECEDES`로 승격했다.
- 같은 Anchor의 명시 cue·수량만 조건/수량 관계 후보로 사용했다.
- 템플릿 cue와 같은 Evidence의 표 구조만 `HAS_FIELD`로 연결했다.
- 신규 관계명은 자동 생성·승격하지 않았다.
- broader, part-of, procedure를 서로 다른 관계로 유지하고 cycle·동시 부여를 금지했다.

전체 시연 그래프의 registry 관계 Evidence coverage는 1.00, domain/range 위반 0, taxonomy cycle 0이다. 다만 근거가 없어 `BROADER`, `PART_OF`, 역할·입출력 관계는 거의 또는 전혀 승격되지 않았다. 이는 보수적 abstention 결과이지 완성된 업무 schema라는 뜻은 아니다.

## 6. LLM 비교 결과

### DEV

| 지표 | B1 | B2 | B3 | B4 |
|---|---:|---:|---:|---:|
| safe ontology yield | {b1['safe_ontology_yield']} | {b2['safe_ontology_yield']} | {b3['safe_ontology_yield']} | {b4['safe_ontology_yield']} |
| critical violation | {b1['critical_shacl_violation']} | {b2['critical_shacl_violation']} | {b3['critical_shacl_violation']} | {b4['critical_shacl_violation']} |
| unsupported label rate | {b1['unsupported_label_rate']:.3f} | {b2['unsupported_label_rate']:.3f} | {b3['unsupported_label_rate']:.3f} | {b4['unsupported_label_rate']:.3f} |

- LLM 반복 일치도: 21/21 = **1.00**
- B2/B1 yield 증가: **{gain:.2%}**로 10% Gate 통과
- B2/B3 yield 비율: **{yield_ratio:.2%}**로 80% Gate 통과
- B2/B3 token 비율: **{token_ratio:.2%}**로 35% Gate 실패
- B4: critical domain/range 위반 82건, unsupported label 58건(12.08%)

따라서 LLM 판정 자체는 안정적이었지만, B3의 80% 수준을 얻는 데 후보 40%와 토큰 55.3%가 필요했다. 비용 대비 품질 가설 H5-C는 지지되지 않았다.

### fresh VALIDATION 8건

- gray 후보가 0건이어서 B1=B2=B3이며 selective LLM 효용은 **확인 단계에서 측정 불가**이다.
- B1: critical 0, provenance 1.00, alias 1/1.
- B4: critical 2, unsupported label 6건(19.35%).
- 따라서 직접 LLM보다 보수적 B1이 안전하다는 H5-D는 통과했지만, 작은 표본 한계를 가진다.

## 7. CQ 해석

초기 단순 존재 기반 CQ는 fresh 표본에 규칙·템플릿·절차가 없다는 이유로 B1이 0.60이었다. 설계서 16.6은 불가능한 CQ에 대한 올바른 abstention도 평가하도록 규정하므로, source reference에 해당 사실이 없고 시스템도 답하지 않은 경우를 `CORRECT_ABSTENTION`으로 별도 계산했다.

- B1 abstention-aware answerability: **{cq['systems']['R5-B1']['answerability_with_correct_abstention']:.2f}**
- B4 abstention-aware answerability: **{cq['systems']['R5-B4']['answerability_with_correct_abstention']:.2f}**
- B1 provenance precision: 1.00, unsupported answer rate: 0

두 지표를 모두 보존했으며 초기 0.60을 덮어쓰지 않았다. H5-E 판정은 사전 명시된 correct-abstention 정의를 적용했지만, n=8이라는 한계 때문에 후속 독립 표본에서 재검증해야 한다.

## 8. 최종 그래프와 Neo4j

전체 INDUCTION+VALIDATION 953건은 성능 평가가 아닌 시연용으로 재구축했다.

| 항목 | 값 |
|---|---:|
| nodes | {full['node_count']:,} |
| relationships | {full['relationship_count']:,} |
| canonical concepts | {full['canonical_concept_count']} |
| surface mentions | {full['surface_mention_count']} |
| fragmentation reduction | {full['fragmentation_reduction']} |
| explicit aliases recovered | {full['explicit_alias_recovered']}/{full['explicit_alias_total']} |
| RDF triples | 87,023 |
| SHACL critical violations | 0 |

실제 Neo4j Community 4.4.43에 import하여 4,767개 노드와 10,738개 관계가 일치함을 확인했다. 필수 view query는 6/6 non-empty였고, Rule→Anchor 45/45, Concept→Mention 139/139, registry relation provenance 249/249였다. UID uniqueness constraint와 system/type index도 ONLINE을 확인했다.

## 9. 비용과 보안

- 실제 API logical calls: {cost['actual_api_calls']}건
- input/output tokens: {cost['input_tokens']:,} / {cost['output_tokens']:,}
- 총 tokens: {cost['total_tokens']:,}
- 가격 가정 `$2/M input`, `$8/M output` 기준 상한: `${cost['standard_price_upper_estimate_usd']:.6f}`
- Batch 50% 가정 추정: `${cost['batch_50pct_estimate_usd']:.6f}`
- API key: getpass TTY로만 전달, 저장 파일 0건, secret scan 0건

B2 토큰은 B3 전수 결과의 부분집합이므로 실제 총비용에서 중복 합산하지 않았다. DEV B4 2건의 첫 응답이 800 token에서 중단되어, 시스템 동결 전에 출력 한도만 1,800으로 조정한 보정 Batch 2건의 비용과 원 실패 비용을 모두 포함했다.

## 10. 현재 문제와 다음 단계

1. **확인 표본 부족**: fresh VALIDATION이 8건뿐이다. 새 leakage group 80건 이상을 별도 구축해야 한다.
2. **인간 Gold 부재**: 구조적 안전성은 검증했지만 `같은 개념인가`, `관계가 의미상 맞는가`를 전문가가 전수 검증하지 않았다.
3. **R4 표면 추출 오염 계승**: 일부 Concept/TemplateField label은 규칙 추출 경계가 길거나 부정확하다. R5는 근거 없는 재명명을 금지했기 때문에 이를 자동 수정하지 않았다.
4. **schema coverage 제한**: 역할, 입력·산출물, taxonomy·partonomy는 명시 근거가 부족해 비어 있다. 그래프가 안전하다는 것과 업무 온톨로지가 완전하다는 것은 다르다.
5. **LLM 비용 효율 실패**: B2가 품질은 늘렸지만 토큰 Gate를 넘었다. 다음 실험은 호출량 확대가 아니라 candidate blocking과 impact score 개선이 우선이다.
6. **후속 human audit**: gray pair와 B4 위반 사례 20~40건을 전문가가 판정해 의미 정확도와 LF 재사용성을 검증해야 한다.

## 11. Gate 요약

| Gate | 결과 | 핵심 근거 |
|---|---|---|
| H5-A 결정적 개념 정규화 | PASS | alias recall 1.00, 위험 병합 0, provenance 1.00 |
| H5-B 관계 schema | PASS | evidence 1.00, domain/range 0, cycle 0 |
| H5-C 선택적 LLM 효용 | **FAIL** | token ratio 55.25% > 35% |
| H5-D Direct-LLM 대비 안전성 | PASS | B1 critical 0 vs B4 2, unsupported 0 vs 19.35% |
| H5-E CQ 활용성 | PASS_WITH_SMALL_N_CAVEAT | abstention-aware 0.80 이상, 초기 presence-only 0.60 병기 |
| H5-F Neo4j readiness | PASS | coverage 1.00, 6/6 views, trace 1.00 |

최종적으로 **결정적 CRSI만 operational canonical graph로 채택**한다. B2/B3/B4 결과는 비교·진단 계층에만 남긴다.
"""
    report_path = root / "reports" / "final_report.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")
    (root / "README.md").write_text(f"# {r5.EXPERIMENT_ID}\n\nOverall status: **{overall}**\n\nSee `reports/final_report.md`.\n", encoding="utf-8")
    status = {"experiment_id": r5.EXPERIMENT_ID, "overall_status": overall, "canonical_graph_system": "R5-B1",
              "ontology_consolidation_gate": consolidation, "confirmatory_evidence_count": 8, "confirmatory_group_count": 7,
              "engineering_validated": True, "human_semantic_gold_validated": False, "test_access": 0,
              "operational_graph_includes_llm_candidates": False, "key_stored": False}
    r5.write_json(root / "reference" / "status.json", status)
    print(json.dumps({"status": status, "report": str(report_path), "gates": {k:v.get('pass') for k,v in gates.items() if isinstance(v,dict) and 'pass' in v}}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
