# TRACE-OL 자이제 Neo4j 실험 결과

- Run ID: `run:20260710T000000Z:P2_OFFLINE:a9482ce`
- 입력: `/home/minjoo/AX_서울펠로우/handoff-hanyang/수주제안/자이제_1.xlsx`
- 입력 SHA-256: `e8c5f174b65eccd7a50dbd2e0e216ea870a6aedfd16b3e4538d6486aea15cf1f`
- 정적 파이프라인 상태: **PASS**
- 설계 기준 비교 가능성: **BASELINE_DRIFT**
- 전체 DoD 상태: **BLOCKED_EXTERNAL_AND_BASELINE_DRIFT**

## 핵심 결과

| 항목 | 결과 |
|---|---:|
| source_blocks | 1366 |
| missing_context_original | 0 |
| evidence_spans | 1552 |
| tables | 56 |
| table_cells | 892 |
| formulas | 1 |
| term_mentions | 117 |
| claim_candidates | 609 |
| accepted_claims | 43 |
| needs_review_claims | 526 |
| rejected_claims | 40 |
| llm_gate_queue | 30 |
| actual_llm_calls | 0 |
| distilled_rules | 0 |
| graph_nodes | 4975 |
| graph_relationships | 7283 |
| accepted_direct_relations | 38 |
| cq_passed | 12 |
| cq_total | 12 |
| regression_passed | 6 |
| regression_total | 6 |

## 데이터 기준 차이

설계서 기준 입력 해시는 `9246a6da6c7635b3f34ee55df75112eb38a2984ea06828be943dc196de5926eb`이지만 실제 파일은 `e8c5f174b65eccd7a50dbd2e0e216ea870a6aedfd16b3e4538d6486aea15cf1f`이다. 
설계서가 예상한 원문 문맥 누락은 3건이나 현재 파일은 0건이다. 현재 파일의 값을 원문으로 보존했으며 누락을 인위적으로 재현하지 않았다.

## 실험 매트릭스

| 실험 | 상태 | 비고 |
|---|---|---|
| B0_RULE_ONLY | EXECUTED | 전량 규칙 후보 생성·자동 승인/기각 완료 |
| B1_LOCAL_EMBEDDING | NOT_EXECUTED | 설계 설정에서 local embedding 비활성 |
| B2_FULL_ADJ | BLOCKED | OPENAI_API_KEY와 human gold 없음 |
| P1_SELECTIVE | ROUTING_ONLY | 30건 요청 동결; 실제 API 호출 없음 |
| P2_DISTILLED | PARTIAL | teacher 판정이 없어 증류 규칙 0건; B0 승인 결과만 projection |

## 검증

| 검사 | 심각도 | 기대 | 실제 | 결과 |
|---|---|---:|---:|---|
| VAL_SOURCE_BLOCK_COUNT | critical | 1366 | 1366 | PASS |
| VAL_DUPLICATE_SOURCE_ID | critical | 0 | 0 | PASS |
| VAL_OFFSET_ROUNDTRIP | critical | 0 | 0 | PASS |
| VAL_GLOBAL_ID_UNIQUENESS | critical | 0 | 0 | PASS |
| VAL_DANGLING_RELATIONSHIP_ENDPOINT | critical | 0 | 0 | PASS |
| VAL_ACCEPTED_WITHOUT_EVIDENCE | critical | 0 | 0 | PASS |
| VAL_DIRECT_EDGE_CLAIM_CONSISTENCY | critical | 0 | 0 | PASS |
| VAL_CQ_PASS | critical | 12 | 12 | PASS |
| VAL_REGRESSION_PASS | critical | 6 | 6 | PASS |
| VAL_CURRENT_INPUT_MISSING_CONTEXT | critical | 0 | 0 | PASS |
| VAL_DESIGN_INPUT_HASH_MATCH | comparability | 9246a6da6c7635b3f34ee55df75112eb38a2984ea06828be943dc196de5926eb | e8c5f174b65eccd7a50dbd2e0e216ea870a6aedfd16b3e4538d6486aea15cf1f | FAIL |
| VAL_DESIGN_MISSING_CONTEXT_BASELINE | comparability | 3 | 0 | FAIL |

## 해석 한계

- Accepted는 규칙·구조·근거 계약을 통과했다는 뜻이며 human gold 정확도를 뜻하지 않는다.
- OpenAI 키가 없어 선택 게이트의 요청 목록만 동결했고 실제 모델 판정·규칙 증류·3회 반복은 수행하지 않았다.
- Docker 데몬 권한이 없어 Neo4j 실적재는 수행하지 않았다. CSV/Cypher와 인메모리 등가 검증은 생성·통과했다.
- 실행 Python은 3.13.13으로, 설계서가 고정한 3.11/3.12 범위 밖이다. 본 실행기는 표준 라이브러리만 사용해 동작했지만 공식 재현 환경과는 다르다.
- 사람 주석 gold가 없어 precision/recall/F1과 bootstrap CI는 산출하지 않았다.
