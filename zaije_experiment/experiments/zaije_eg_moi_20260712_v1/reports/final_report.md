# 자이제 EG-MOI 최종 실험 보고서

실험 ID: `zaije_eg_moi_20260712_v1`  
최종 판정: **`EG_MOI_END_TO_END_PASS`**  
입력: `자이제_1.xlsx` 전체 `1,366`행  
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

- 지정 Excel을 직접 읽고 `1,366`개 원문 행을 생성했다.
- 문장·절, 목록 항목, 표 셀을 `2,308`개 Evidence Anchor로 분리했다.
- 표 header, row header, 목록 문맥을 `1,718`개 ContextSpan으로 보존했다.
- 모든 `start_char:end_char`를 원문과 왕복 비교했다: `1.00`.

### Stage 2. Open Candidate Discovery

- 고정 도메인 타입에 바로 넣지 않고 Mention `2,954`개를 먼저 발견했다.
- 표 구조, 한·영 병기, 명시적 정의, 조건, 수량과 한국어 논항 패턴을 사용했다.
- triple을 바로 만들지 않고 action·agent·object를 담은 SemanticFrame `177`개를 생성했다.

### Stage 3. Bottom-up Consolidation

- 문자열 NFKC 정규화와 완전 일치 병합을 적용했다.
- 한·영 병기와 약어 정의는 명시 Evidence로 병합했다.
- 문자 2·3-gram 희소 벡터를 만들고 cosine `0.90` 이상만 자동 병합했다.
- cosine `0.82~0.90`의 `46`건은 LLM이 없으므로 병합하지 않고 보류했다.
- 최종 ConceptCluster는 `2,188`개이며, `VALIDATED` `818`개, `UNRESOLVED` `1,370`개다.

### Stage 4. Middle-out Schema Induction

고정된 도메인 스키마를 먼저 채우지 않고 반복 군집의 프레임 역할과 문맥으로 다음 클래스를 귀납했다.

- `CustomerRequirement` → 상위 `Resource` (31개 군집)
- `EvaluationMeasure` → 상위 `Measure` (4개 군집)
- `ProposalArtifact` → 상위 `Resource` (47개 군집)
- `ProposalContext` → 상위 `Context` (243개 군집)
- `ProposalDomainConcept` → 상위 `DomainConcept` (212개 군집)
- `ProposalOrganization` → 상위 `Agent` (5개 군집)
- `ProposalRole` → 상위 `Agent` (47개 군집)
- `ProposalWorkUnit` → 상위 `WorkUnit` (229개 군집)

관계는 표 구조와 SemanticFrame에서 반복된 표현을 `PERFORMED_BY`, `HAS_INPUT`, `PRODUCES_OUTPUT`, `HAS_CONDITION`, `HAS_MEASURE`, `PRECEDES` 등으로 정리했다. `broader`, `partOf`, `precedes`를 혼동하지 않았으며, 명시 근거가 없는 도메인 taxonomy와 partonomy는 생성하지 않았다.

### Stage 5. Evidence-constrained Promotion

- 관계 후보 `VALIDATED`: `60`
- 관계 후보 `UNRESOLVED`: `179`
- 최종 Assertion: `261`
- Assertion Evidence coverage: `1.00`
- Assertion ExtractionActivity coverage: `1.00`
- domain/range 위반: `0`
- 잘못된 endpoint: `0`

중복, self-loop, 타입 충돌, 근거 부족 후보는 최종 그래프에 넣지 않고 `UNRESOLVED`에 보존했다.

## 3. 주요 결과

| 항목 | 결과 |
|---|---:|
| Evidence 원문 행 | 1,366 |
| Evidence Anchor | 2,308 |
| Mention 후보 | 2,954 |
| SemanticFrame | 177 |
| ConceptCluster | 2,188 |
| VALIDATED ConceptCluster | 818 |
| UNRESOLVED 전체 후보 | 1,549 |
| 최종 Assertion | 261 |
| 전체 그래프 노드 | 11,053 |
| 전체 그래프 관계 | 19,502 |

### Operational 관계

| 관계 | 수 |
|---|---:|
| PERFORMED_BY | 8 |
| HAS_INPUT | 13 |
| PRODUCES_OUTPUT | 3 |
| HAS_CONDITION | 35 |
| HAS_MEASURE | 1 |
| PRECEDES | 201 |

### 자동 생성 예시

- `구매와 솔루션을 실행` --`PERFORMED_BY`--> `고객`  
  Evidence: `egmoi:evidence/xlsx-row-659_A02`
- `제안서 작성` --`HAS_INPUT`--> `수주계획`  
  Evidence: `egmoi:evidence/xlsx-row-237_A01`
- `제안서를 작성` --`PRODUCES_OUTPUT`--> `제안서`  
  Evidence: `egmoi:evidence/xlsx-row-310_A01`
- `우리가 솔루션을 제공` --`HAS_CONDITION`--> `이 경우`  
  Evidence: `egmoi:evidence/xlsx-row-747_A01`
- `한편으로 제안서를 작성` --`HAS_MEASURE`--> `~20%`  
  Evidence: `egmoi:evidence/xlsx-row-1056_A01`
- `대안을 검토` --`PRECEDES`--> `리스크를 관리`  
  Evidence: `egmoi:evidence/xlsx-row-1333_A11, egmoi:evidence/xlsx-row-1334_A01`

예시는 자동 추출 결과이며 의미 정답 예시로 선정한 것이 아니다. 각 관계에는 실제 Evidence Anchor가 함께 저장돼 있다.

## 4. 표준 그래프와 Neo4j 검증

| 검사 | 결과 |
|---|---:|
| canonical RDF triples | 157,272 |
| SKOS triples | 4,354 |
| PROV-O triples | 19,892 |
| RDF 파일 재파싱 | PASS |
| SHACL conforms | TRUE |
| Neo4j nodes | 11,053 / 11,053 |
| Neo4j relationships | 19,502 / 19,502 |
| Neo4j Assertion Evidence coverage | 1.00 |
| Neo4j Assertion Activity coverage | 1.00 |
| 필수 시각화 질의 | 모두 non-empty |

Neo4j Community `4.4.43`에 실제 import한 뒤 결과를 계산했다. CSV 행 수만 센 검사가 아니다.

## 5. LLM을 사용하지 않은 이유

설계서에서 LLM은 모든 문장을 처리하는 필수 단계가 아니라 Gray-zone 군집을 선택적으로 판정하는 수단이다. 실행 환경에 API 키가 없었으므로 LLM 판정을 임의 모사하지 않았다. 대신 Gray-zone `46`건을 `UNRESOLVED`로 유지했다. 따라서 사람 개입 없는 안전한 abstention 원칙은 지켰지만, 선택적 LLM의 추가 효과는 이번 실행에서 평가하지 못했다.

## 6. 해석과 한계

1. **성공의 의미**: Excel에서 Neo4j까지 EG-MOI 파이프라인과 형식·추적성 검증이 성공했다.
2. **정확도 한계**: 사람 gold가 없어 precision, recall, F1을 계산하지 않았다.
3. **임베딩 한계**: 사전학습 언어모델이 아니라 재현 가능한 문자 n-gram 희소 임베딩을 사용했다. 철자 변형 통합에는 유효하지만 진정한 동의어 발견에는 약하다.
4. **한국어 분석 한계**: 형태소 분석기·dependency parser가 없는 환경에서 투명한 패턴을 사용했으므로 일부 Mention 경계와 역할이 부정확할 수 있다.
5. **절차 관계 한계**: `PRECEDES`는 같은 절 안의 문서 순서로 귀납했으며 confidence `0.62`다. 실제 업무 순서와 다를 수 있다.
6. **보수적 결과**: 모호한 후보 `1,549`개를 승격하지 않아 그래프의 관계 수가 적지만, 이는 무인 실행에서 잘못된 지식 확산을 막기 위한 설계 결과다.

## 7. 최종 판정

> **EG-MOI 설계서의 Bottom-up 발견, Middle-out 귀납, Top-down 검증을 자이제_1 전체 데이터에 적용해 RDF·SKOS·PROV-O·SHACL·Neo4j까지 자동 완주했다. 구조적 성공 기준은 모두 통과했다. 의미 정확도와 선택적 LLM 효과는 별도 gold 기반 후속 실험이 필요하다.**
