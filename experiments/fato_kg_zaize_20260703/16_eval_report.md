# FATO-KG 자이제_1.xlsx 실험 리포트

Generated: 2026-07-03T06:14:56+00:00
Experiment dir: `experiments/fato_kg_zaize_20260703`
Input: `자이제_1.xlsx`
Methodology: `layer2_fato_kg_methodology_eacl.md`

이 리포트는 `자이제_1.xlsx`를 FATO-KG 방법론에 맞춰 처리한 1차 bootstrap 결과를 요약한다. 현재 결과는 자동 구축 결과이며, 사람 검수를 완료한 gold ontology/KG가 아니다.

## 1. 실행 요약

| 항목 | 값 |
| --- | ---: |
| 유효 evidence sentences | 1366 |
| 장 수 | 3 |
| section chunks | 52 |
| seed task frames | 26 |
| raw frame-anchored triples | 3064 |
| validated triples | 2988 |
| Layer2 nodes | 1446 |
| Layer2 edges | 3721 |
| Layer1 mapping candidates | 260 |
| human review sheet rows | 656 |

## 2. 입력 데이터 프로파일

| 항목 | 값 |
| --- | ---: |
| sheet | clean_sentences |
| 유효 문장 행 | 1366 |
| 장 수 | 3 |
| section chunk 수 | 52 |
| 구조 메타데이터 누락 문장 | 3 |

| chapter | sentence rows |
| --- | ---: |
| 1 입찰과 제안 | 310 |
| 2 수주영업 | 486 |
| 3 제안서 전략 | 567 |
| missing_metadata | 3 |

## 3. 적용한 처리 절차

1. `xlsx` 내부 XML을 직접 읽어 `page`, `chapter_no`, `section_no`, `section_title`, `text_for_llm_human` 컬럼을 추출했다.
2. 각 문장 행을 evidence unit으로 만들고, 원문 보존용 `evidence_id`, page, chapter, section, SHA1 fingerprint를 부여했다.
3. 장·절 구조를 기준으로 52개 section chunk를 구성했다. 구조 정보가 빠진 문장은 별도 `missing_structure` chunk로 분리했다.
4. 방법론 문서의 Layer2 FATO task frame 방향에 맞춰 26개 seed task frame을 만들었다.
5. task별 section hint와 키워드 매칭으로 관련 evidence를 연결하고, task frame candidate와 catalog를 산출했다.
6. evidence 문장에서 입력물, 산출물, 역할, 이해관계자, 원칙, 리스크, 의사결정점, 평가 기준 단서를 찾아 frame-anchored triple을 생성했다.
7. triple마다 allowed predicate, domain/range, evidence quote substring, confidence 기준을 적용해 자동 검증했다.
8. 검증된 triple을 Layer2 graph node/edge로 materialize하고, 모든 edge에 `frame_task_id`, `evidence_ids`, `confidence`, `validation_status`를 남겼다.
9. 기존 `outputs/01_layer1`의 NCS/PCF 노드와 lexical similarity 기반 top-k mapping candidate를 만들었다. 이 단계는 후보 생성이며 node merge가 아니다.
10. 자동 검증에서 검수 우선순위가 높은 triple 500개와 Layer1 매핑 후보 top-3를 사람 검수용 sheet로 내보냈다.

## 4. 검증 상태

| validation_status | count |
| --- | ---: |
| `verified` | 2334 |
| `needs_review_low_confidence` | 509 |
| `needs_review_example_scope` | 145 |

## 5. Node Type 분포

| node_type | nodes |
| --- | ---: |
| `EvidenceSpan` | 1366 |
| `Task` | 26 |
| `Artifact` | 8 |
| `Stakeholder` | 5 |
| `InformationItem` | 5 |
| `Principle` | 5 |
| `Role` | 5 |
| `Process` | 4 |
| `Risk` | 4 |
| `DecisionPoint` | 4 |
| `Concept` | 3 |
| `StrategyArtifact` | 3 |
| `Condition` | 2 |
| `StrategyElement` | 2 |
| `Constraint` | 2 |
| `EvaluationCriterion` | 1 |
| `Checklist` | 1 |

## 6. Predicate 분포

| predicate | edges |
| --- | ---: |
| `EVIDENCED_BY` | 3117 |
| `PRODUCES` | 106 |
| `USES_INPUT` | 90 |
| `ANALYZES` | 73 |
| `HAS_PRINCIPLE` | 62 |
| `ACCOUNTABLE_TO` | 60 |
| `HAS_RISK` | 59 |
| `PERFORMED_BY` | 34 |
| `HAS_TASK` | 26 |
| `TRIGGERED_BY` | 16 |
| `MITIGATES` | 16 |
| `HAS_DECISION_POINT` | 16 |
| `HAS_SUBTASK` | 14 |
| `EVALUATES` | 13 |
| `PRECEDES` | 11 |
| `HAS_CONSTRAINT` | 8 |

## 7. 가장 많은 evidence를 가진 Task Frame

| frame_task_id | task name | evidence/edge count |
| --- | --- | ---: |
| `L2_TASK_BID_CONTEXT_UNDERSTANDING` | 입찰·제안 환경 이해 | 358 |
| `L2_TASK_CAPTURE_PLANNING` | 수주영업 | 301 |
| `L2_TASK_CUSTOMER_NEEDS_ANALYSIS` | 고객 니즈 분석 | 253 |
| `L2_TASK_COMPETITOR_ANALYSIS` | 경쟁사 분석 | 252 |
| `L2_TASK_PROPOSAL_PROCESS_MANAGEMENT` | 제안 프로세스 관리 | 234 |
| `L2_TASK_CAPTURE_INFORMATION_MANAGEMENT` | 영업 정보 관리 | 218 |
| `L2_TASK_EVALUATOR_ANALYSIS` | 평가자 분석 | 200 |
| `L2_TASK_DIFFERENTIATOR_IDENTIFICATION` | 차별화 요소 규명 | 197 |
| `L2_TASK_CUSTOMER_ISSUE_ANALYSIS` | 고객 이슈 분석 | 193 |
| `L2_TASK_PROPOSAL_STRATEGY_MANAGEMENT` | 제안전략 관리 | 187 |
| `L2_TASK_PERSUASIVE_COMMUNICATION` | 설득 커뮤니케이션 설계 | 161 |
| `L2_TASK_RISK_MANAGEMENT` | 리스크 관리 | 127 |
| `L2_TASK_SOLUTION_OPTIMIZATION` | 솔루션 최적화 | 123 |
| `L2_TASK_STRATEGY_VALIDATION` | 전략 효과성 검증 | 117 |
| `L2_TASK_STRATEGY_STATEMENT_WRITING` | 전략기술서 작성 | 102 |

## 8. Layer1 Mapping 후보

| target scheme | candidates |
| --- | ---: |
| `NCS` | 130 |
| `PCF` | 130 |

mapping score는 task name similarity, alias similarity, token overlap, definition similarity, graph-neighbor support를 합산한 heuristic score이다. 이 값은 사람 검수 우선순위용이며 정답 매핑을 의미하지 않는다.

## 9. 산출물

| file | meaning |
| --- | --- |
| `00_source_profile.json` | 입력 엑셀의 장/절/문장 수와 누락 메타데이터 요약 |
| `01_evidence_units.jsonl` | 원문 문장 단위 evidence unit |
| `02_chunks.jsonl` | 장·절 기준 section chunk |
| `03_task_frame_candidates.jsonl` | evidence 기반 task frame 후보 |
| `04_task_frame_catalog.jsonl` | 26개 FATO task frame catalog |
| `05_alias_dictionary.json` | task frame alias 사전 |
| `06_relation_schema.json` | 허용 predicate와 domain/range 제약 |
| `07_frame_anchored_triples_raw.jsonl` | 자동 추출 raw triple |
| `08_frame_anchored_triples_validated.jsonl` | schema/evidence 검증 후 triple |
| `09_layer2_nodes.jsonl` | Layer2 graph node |
| `10_layer2_edges.jsonl` | Layer2 graph edge |
| `11_layer2_graph_schema.md` | Layer2 graph schema 설명 |
| `12_l2_l1_mapping_candidates.jsonl` | NCS/PCF 매핑 후보 |
| `13_human_review_sheet.xlsx` | 사람 검수용 triple/mapping sheet |
| `13_human_review_sheet.csv` | 같은 내용을 CSV로 내보낸 파일 |
| `14_benchmark_gold_frames.jsonl` | human annotation starter template |
| `15_benchmark_gold_triples.jsonl` | human annotation starter template |
| `layer2_neo4j_import.cypher` | Neo4j import 보조 스크립트 초안 |
| `agent_query_templates.md` | agent query pattern 초안 |
| `graph_api_spec.yaml` | graph API spec 초안 |

## 10. 재실행 명령

```bash
cd /home/minjoo/AX_서울펠로우
python3 scripts/build_fato_kg_zaize.py \
  --input-xlsx 자이제_1.xlsx \
  --methodology layer2_fato_kg_methodology_eacl.md \
  --output-dir experiments/fato_kg_zaize_20260703 \
  --layer1-dir outputs/01_layer1
```

## 11. Claim Boundary

- 이 결과는 FATO-KG 방법론의 deterministic bootstrap 실험이다.
- 이번 실행은 외부 LLM/GPU를 사용하지 않았다. 현재 서버의 GPU는 이후 LLM 기반 extraction/verification을 붙일 때 사용할 수 있다.
- `verified`는 evidence quote substring, allowed predicate, domain/range 같은 자동 검증을 통과했다는 뜻이다.
- human-gold 성능, task attribution accuracy, evidence faithfulness F1은 아직 주장할 수 없다.
- `14_benchmark_gold_frames.jsonl`, `15_benchmark_gold_triples.jsonl`은 human annotation starter template이며 gold 완료 파일이 아니다.
