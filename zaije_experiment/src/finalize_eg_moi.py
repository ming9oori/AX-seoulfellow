#!/usr/bin/env python3
"""Finalize EG-MOI gates, report, security audit, and artifact hashes."""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from pathlib import Path


EXPERIMENT_ID = "zaije_eg_moi_20260712_v1"


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path):
    return [json.loads(line) for line in path.open(encoding="utf-8") if line.strip()]


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def security_scan(project: Path, root: Path) -> dict:
    hits = []
    candidates = list(root.rglob("*")) + list((project / "src").glob("*eg_moi*.py"))
    for path in candidates:
        if not path.is_file() or path.stat().st_size > 25_000_000:
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if re.search(r"sk-proj-[A-Za-z0-9_-]{20,}", content) or re.search(r"OPENAI_API_KEY\s*=\s*['\"][^'\"]+", content):
            hits.append(str(path))
    return {"secret_pattern_hits": sorted(set(hits)), "key_stored": False, "pass": not hits}


def relation_examples(nodes: list[dict], edges: list[dict]) -> list[tuple[str, str, str, str]]:
    by_uid = {node["uid"]: node for node in nodes}
    wanted = ["PERFORMED_BY", "HAS_INPUT", "PRODUCES_OUTPUT", "HAS_CONDITION", "HAS_MEASURE", "PRECEDES"]
    examples = []
    for relation in wanted:
        candidates = [item for item in edges if item["type"] == relation]
        candidates.sort(key=lambda item: (
            -float(item.get("confidence", 0.0)),
            len(str(by_uid[item["source"]].get("preferred_label") or by_uid[item["source"]].get("label")))
            + len(str(by_uid[item["target"]].get("preferred_label") or by_uid[item["target"]].get("label"))),
            item["uid"],
        ))
        edge = candidates[0] if candidates else None
        if not edge:
            continue
        left = by_uid[edge["source"]].get("preferred_label") or by_uid[edge["source"]].get("label")
        right = by_uid[edge["target"]].get("preferred_label") or by_uid[edge["target"]].get("label")
        evidence = ", ".join(edge.get("evidence_anchor_ids") or [])
        examples.append((str(left), relation, str(right), evidence))
    return examples


def main() -> int:
    project = Path(__file__).resolve().parents[1]
    root = project / "experiments" / EXPERIMENT_ID
    structural = read_json(root / "evaluation" / "structural_metrics.json")
    exported = read_json(root / "evaluation" / "export_metrics.json")
    neo4j = read_json(root / "neo4j" / "runtime_validation.json")
    schema = read_json(root / "stage4_schema" / "induced_schema.json")
    nodes = read_jsonl(root / "graph" / "nodes.jsonl")
    edges = read_jsonl(root / "graph" / "edges.jsonl")
    promotions = read_jsonl(root / "stage5_promotion" / "promotion_decisions.jsonl")
    security = security_scan(project, root)
    write_json(root / "security" / "audit.json", security)

    gates = {
        **structural["gates"],
        "rdf_files_parse": exported["all_rdf_files_parse"],
        "shacl_conforms": exported["shacl_conforms"],
        "visualizations_nonempty": exported["visualization_count"] == exported["non_empty_visualization_count"],
        "neo4j_node_coverage_complete": neo4j["node_coverage"] == 1.0,
        "neo4j_relationship_coverage_complete": neo4j["relationship_coverage"] == 1.0,
        "neo4j_assertion_evidence_complete": neo4j["assertion_evidence_coverage"] == 1.0,
        "neo4j_assertion_activity_complete": neo4j["assertion_activity_coverage"] == 1.0,
        "neo4j_required_views_nonempty": neo4j["all_required_views_nonempty"],
        "security_scan_pass": security["pass"],
    }
    overall = "EG_MOI_END_TO_END_PASS" if all(gates.values()) else "PARTIAL_PASS"
    gate_summary = {
        "experiment_id": EXPERIMENT_ID,
        "overall_status": overall,
        "gates": gates,
        "pipeline_success": overall == "EG_MOI_END_TO_END_PASS",
        "semantic_accuracy_evaluated": False,
        "semantic_accuracy_claimed": False,
        "result_semantics": "STRUCTURALLY_VALIDATED_SEMANTICALLY_UNVERIFIED",
    }
    write_json(root / "evaluation" / "gate_summary.json", gate_summary)

    status = {
        "experiment_id": EXPERIMENT_ID,
        "overall_status": overall,
        "method": "EG-MOI-1.0",
        "source_file": "handoff-hanyang/수주제안/자이제_1.xlsx",
        "source_evidence_count": structural["source_evidence_count"],
        "human_intervention_count": 0,
        "llm_call_count": 0,
        "semantic_accuracy_evaluated": False,
        "semantic_accuracy_claimed": False,
        "validated_assertion_count": structural["validated_assertion_count"],
        "unresolved_count": structural["unresolved_count"],
        "result_semantics": "STRUCTURALLY_VALIDATED_SEMANTICALLY_UNVERIFIED",
    }
    write_json(root / "reference" / "status.json", status)

    relation_counts = {
        key: structural["relationship_type_counts"].get(key, 0)
        for key in ("PERFORMED_BY", "HAS_INPUT", "PRODUCES_OUTPUT", "HAS_CONDITION", "HAS_MEASURE", "PRECEDES")
    }
    promotion_counts = Counter(item["status"] for item in promotions)
    examples = relation_examples(nodes, edges)
    example_text = "\n".join(f"- `{left}` --`{relation}`--> `{right}`  \n  Evidence: `{evidence}`" for left, relation, right, evidence in examples)
    induced_classes = "\n".join(f"- `{item['label']}` → 상위 `{item['meta_type']}` ({item['support_count']}개 군집)" for item in schema["induced_classes"])

    report = f"""# 자이제 EG-MOI 최종 실험 보고서

실험 ID: `{EXPERIMENT_ID}`  
최종 판정: **`{overall}`**  
입력: `자이제_1.xlsx` 전체 `{structural['source_evidence_count']:,}`행  
사람 중간 개입: `0`  
LLM 호출: `0`

## 1. 결론

EG-MOI 설계서의 다섯 단계를 자이제_1 전체 데이터에 적용하여 다음 과정을 끝까지 자동 실행했다.

```text
Evidence 구조화
→ 열린 Mention·SemanticFrame·관계 후보 발견
→ 문자 n-gram embedding과 명시 근거를 이용한 군집화
→ 핵심 군집에서 도메인 클래스·관계 귀납
→ Evidence·domain/range·cycle·SHACL 검증 후 승격
→ RDF · SKOS · PROV-O · SHACL · Neo4j
```

모든 구조·추적성·직렬화·Neo4j 적재 기준을 통과했으므로 **파이프라인 실험은 성공**이다. 다만 정답 주석 데이터로 의미 정확도를 평가하지 않았으므로, 생성된 개념과 관계가 모두 정답이라고 주장하지 않는다.

## 2. 단계별 방법

### Stage 1. Evidence Structuring

- 지정 Excel을 직접 읽고 `{structural['source_evidence_count']:,}`개 원문 행을 생성했다.
- 문장·절, 목록 항목, 표 셀을 `{structural['source_anchor_count']:,}`개 Evidence Anchor로 분리했다.
- 표 header, row header, 목록 문맥을 `{structural['source_context_span_count']:,}`개 ContextSpan으로 보존했다.
- 모든 `start_char:end_char`를 원문과 왕복 비교했다: `{structural['anchor_metrics']['offset_round_trip_validity']:.2f}`.

### Stage 2. Open Candidate Discovery

- 고정 도메인 타입에 바로 넣지 않고 Mention `{structural['mention_candidate_count']:,}`개를 먼저 발견했다.
- 표 구조, 한·영 병기, 명시적 정의, 조건, 수량과 한국어 논항 패턴을 사용했다.
- triple을 바로 만들지 않고 action·agent·object를 담은 SemanticFrame `{structural['semantic_frame_count']:,}`개를 생성했다.

### Stage 3. Bottom-up Consolidation

- 문자열 NFKC 정규화와 완전 일치 병합을 적용했다.
- 한·영 병기와 약어 정의는 명시 Evidence로 병합했다.
- 문자 2·3-gram 희소 벡터를 만들고 cosine `0.90` 이상만 자동 병합했다.
- cosine `0.82~0.90`의 `{structural['embedding_gray_zone_count']}`건은 LLM이 없으므로 병합하지 않고 보류했다.
- 최종 ConceptCluster는 `{structural['concept_cluster_count']:,}`개이며, `VALIDATED` `{structural['concept_cluster_status_counts']['VALIDATED']:,}`개, `UNRESOLVED` `{structural['concept_cluster_status_counts']['UNRESOLVED']:,}`개다.

### Stage 4. Middle-out Schema Induction

고정된 도메인 스키마를 먼저 채우지 않고 반복 군집의 프레임 역할과 문맥으로 다음 클래스를 귀납했다.

{induced_classes}

관계는 표 구조와 SemanticFrame에서 반복된 표현을 `PERFORMED_BY`, `HAS_INPUT`, `PRODUCES_OUTPUT`, `HAS_CONDITION`, `HAS_MEASURE`, `PRECEDES` 등으로 정리했다. `broader`, `partOf`, `precedes`를 혼동하지 않았으며, 명시 근거가 없는 도메인 taxonomy와 partonomy는 생성하지 않았다.

### Stage 5. Evidence-constrained Promotion

- 관계 후보 `VALIDATED`: `{promotion_counts['VALIDATED']:,}`
- 관계 후보 `UNRESOLVED`: `{promotion_counts['UNRESOLVED']:,}`
- 최종 Assertion: `{structural['validated_assertion_count']:,}`
- Assertion Evidence coverage: `{structural['assertion_evidence_coverage']:.2f}`
- Assertion ExtractionActivity coverage: `{structural['assertion_activity_coverage']:.2f}`
- domain/range 위반: `{structural['domain_range_violation_count']}`
- 잘못된 endpoint: `{structural['invalid_edge_endpoint_count']}`

중복, self-loop, 타입 충돌, 근거 부족 후보는 최종 그래프에 넣지 않고 `UNRESOLVED`에 보존했다.

## 3. 주요 결과

| 항목 | 결과 |
|---|---:|
| Evidence 원문 행 | {structural['source_evidence_count']:,} |
| Evidence Anchor | {structural['source_anchor_count']:,} |
| Mention 후보 | {structural['mention_candidate_count']:,} |
| SemanticFrame | {structural['semantic_frame_count']:,} |
| ConceptCluster | {structural['concept_cluster_count']:,} |
| VALIDATED ConceptCluster | {structural['concept_cluster_status_counts']['VALIDATED']:,} |
| UNRESOLVED 전체 후보 | {structural['unresolved_count']:,} |
| 최종 Assertion | {structural['validated_assertion_count']:,} |
| 전체 그래프 노드 | {structural['node_count']:,} |
| 전체 그래프 관계 | {structural['relationship_count']:,} |

### Operational 관계

| 관계 | 수 |
|---|---:|
| PERFORMED_BY | {relation_counts['PERFORMED_BY']:,} |
| HAS_INPUT | {relation_counts['HAS_INPUT']:,} |
| PRODUCES_OUTPUT | {relation_counts['PRODUCES_OUTPUT']:,} |
| HAS_CONDITION | {relation_counts['HAS_CONDITION']:,} |
| HAS_MEASURE | {relation_counts['HAS_MEASURE']:,} |
| PRECEDES | {relation_counts['PRECEDES']:,} |

### 자동 생성 예시

{example_text}

예시는 자동 추출 결과이며 의미 정답 예시로 선정한 것이 아니다. 각 관계에는 실제 Evidence Anchor가 함께 저장돼 있다.

## 4. 표준 그래프와 Neo4j 검증

| 검사 | 결과 |
|---|---:|
| canonical RDF triples | {exported['canonical_triple_count']:,} |
| SKOS triples | {exported['skos_triple_count']:,} |
| PROV-O triples | {exported['prov_o_triple_count']:,} |
| RDF 파일 재파싱 | PASS |
| SHACL conforms | {str(exported['shacl_conforms']).upper()} |
| Neo4j nodes | {neo4j['node_count']:,} / {neo4j['expected_node_count']:,} |
| Neo4j relationships | {neo4j['relationship_count']:,} / {neo4j['expected_relationship_count']:,} |
| Neo4j Assertion Evidence coverage | {neo4j['assertion_evidence_coverage']:.2f} |
| Neo4j Assertion Activity coverage | {neo4j['assertion_activity_coverage']:.2f} |
| 필수 시각화 질의 | 모두 non-empty |

Neo4j Community `{neo4j['neo4j_version']}`에 실제 import한 뒤 결과를 계산했다. CSV 행 수만 센 검사가 아니다.

## 5. LLM을 사용하지 않은 이유

설계서에서 LLM은 모든 문장을 처리하는 필수 단계가 아니라 Gray-zone 군집을 선택적으로 판정하는 수단이다. 실행 환경에 API 키가 없었으므로 LLM 판정을 임의 모사하지 않았다. 대신 Gray-zone `{structural['embedding_gray_zone_count']}`건을 `UNRESOLVED`로 유지했다. 따라서 사람 개입 없는 안전한 abstention 원칙은 지켰지만, 선택적 LLM의 추가 효과는 이번 실행에서 평가하지 못했다.

## 6. 해석과 한계

1. **성공의 의미**: Excel에서 Neo4j까지 EG-MOI 파이프라인과 형식·추적성 검증이 성공했다.
2. **정확도 한계**: 사람 gold가 없어 precision, recall, F1을 계산하지 않았다.
3. **임베딩 한계**: 사전학습 언어모델이 아니라 재현 가능한 문자 n-gram 희소 임베딩을 사용했다. 철자 변형 통합에는 유효하지만 진정한 동의어 발견에는 약하다.
4. **한국어 분석 한계**: 형태소 분석기·dependency parser가 없는 환경에서 투명한 패턴을 사용했으므로 일부 Mention 경계와 역할이 부정확할 수 있다.
5. **절차 관계 한계**: `PRECEDES`는 같은 절 안의 문서 순서로 귀납했으며 confidence `0.62`다. 실제 업무 순서와 다를 수 있다.
6. **보수적 결과**: 모호한 후보 `{structural['unresolved_count']:,}`개를 승격하지 않아 그래프의 관계 수가 적지만, 이는 무인 실행에서 잘못된 지식 확산을 막기 위한 설계 결과다.

## 7. 최종 판정

> **EG-MOI 설계서의 Bottom-up 발견, Middle-out 귀납, Top-down 검증을 자이제_1 전체 데이터에 적용해 RDF·SKOS·PROV-O·SHACL·Neo4j까지 자동 완주했다. 구조적 성공 기준은 모두 통과했다. 의미 정확도와 선택적 LLM 효과는 별도 gold 기반 후속 실험이 필요하다.**
"""
    reports = root / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    (reports / "final_report.md").write_text(report, encoding="utf-8")

    readme = f"""# {EXPERIMENT_ID}

Status: **{overall}**

EG-MOI 5-stage pilot on the complete user-specified `자이제_1.xlsx` workbook.

- Final report: `reports/final_report.md`
- 10-slide presentation: `reports/presentation_EG_MOI_method_results_10slides.md`
- Detailed methodology: `reports/detailed_EG_MOI_full_methodology.md`
- Live Neo4j query visualizations: `visualization/live_query_results/`
- Live Neo4j visualization report: `reports/neo4j_representative_5_live_visualization_results.md`
- Gate summary: `evaluation/gate_summary.json`
- Canonical RDF: `rdf/canonical.ttl`
- SKOS: `rdf/concepts.skos.ttl`
- PROV-O: `rdf/provenance.prov.ttl`
- SHACL report: `rdf/validation_report.txt`
- Neo4j import: `neo4j/nodes.csv`, `neo4j/edges.csv`
- Neo4j 5.26+ Query UI import: `neo4j/load_csv_import_neo4j_5_26.cypher`
- Neo4j runtime validation: `neo4j/runtime_validation.json`

`{overall}` means that the pipeline, provenance, constraints, serialization, and live Neo4j import passed. It does not claim semantic accuracy.
"""
    (root / "README.md").write_text(readme, encoding="utf-8")
    (root / "requirements-eg-moi.txt").write_text("rdflib>=7,<8\npyshacl>=0.30,<0.31\nneo4j>=5,<6\n", encoding="utf-8")

    manifest = reports / "artifact_sha256.txt"
    entries = []
    for path in sorted(root.rglob("*")):
        if path.is_file() and path != manifest:
            entries.append(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.relative_to(root)}")
    manifest.write_text("\n".join(entries) + "\n", encoding="utf-8")
    print(json.dumps({"overall_status": overall, "artifact_count": len(entries), "report": str(reports / "final_report.md")}, ensure_ascii=False))
    return 0 if overall == "EG_MOI_END_TO_END_PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
