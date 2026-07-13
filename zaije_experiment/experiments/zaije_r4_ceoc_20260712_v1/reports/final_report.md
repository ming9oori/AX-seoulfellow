# 자이제 R4-CEOC 최종 실험 보고서

## 1. 최종 결론

R4-CEOC의 최종 판정은 **`DETERMINISTIC_CORE_ONLY_PASS`**다.

문서 구조, exact-offset anchor와 mention, 명시적인 규범·조건·정의·예시·수량·절차 cue, 결정적 승격 정책만 사용한 `R4-B1`은 모든 안전성·근거·CQ·RDF·Neo4j Gate를 통과했다. 반면 선택적 LLM을 추가한 `R4-B2`는 안전성을 해치지는 않았지만 사전등록한 coverage 및 B3 대비 graph-yield 기준을 충족하지 못했다.

따라서 최종 canonical graph와 operational Neo4j graph는 **LLM 확장 결과를 제외한 B1 deterministic conservative core**로 고정한다.

## 2. 이번 실험에서 검증한 질문

R4는 R3에서 충돌했던 `IS_NORMATIVE`, `GENERALIZABLE_RULE` 같은 의미 field를 다시 LLM 정답으로 만들지 않았다. 대신 다음 질문을 검증했다.

> 암묵적 의미 판단 없이 문서 구조, 명시 cue, exact provenance, 결정적 policy만으로 실행 가능한 보수적 온톨로지 코어를 만들 수 있는가?

추가로 닫힌 선택형 LLM이 이 코어의 안전성을 유지하면서 적은 비용으로 coverage를 늘릴 수 있는지 비교했다.

## 3. R3 산출물의 사용 범위

### 사용한 것

- R3 atomic anchor segmenter와 source hash
- 64개 `BOUNDARY_HARD_KEEP`
- 6개 `BOUNDARY_HARD_DROP`
- exact offset과 context-span provenance
- 노출 Evidence 및 leakage-group registry

### 사용하지 않은 것

- `IS_NORMATIVE`
- `GENERALIZABLE_RULE`
- `SPECIFIC_EXAMPLE_INSTANCE`
- R3 semantic field envelope
- R3 falsifier를 정답으로 해석한 결과

R3의 50개 quarantined field는 `CROSS_MODEL_SEMANTIC_DISAGREEMENT`로 재명명했으며 DEV 진단 자료로만 보존했다. 온톨로지 사실이나 승격 근거로 사용하지 않았다.

## 4. 데이터와 누출 통제

| 항목 | 결과 |
|---|---:|
| DEV_EXPOSED Evidence | 120 |
| Confirmatory VALIDATION Evidence | 80 |
| Confirmatory leakage group | 28 |
| DEV Evidence overlap | 0 |
| DEV leakage-group overlap | 0 |
| TEST membership/access | 0 |

원래 표본 quota에서 VALIDATION의 정의와 표·템플릿 자료가 부족했다. API 호출 전에 가능한 정의 10건과 표 2건을 전수 포함하고 부족분을 조건 16건·절차 20건으로 재배분했다. 변경 내역과 membership hash는 confirmatory 실행 전에 잠갔다.

## 5. 방법론

### 5.1 R4-B0 Structure Only

B0는 다음 구조와 provenance만 생성했다.

- Document, Chapter, Section
- EvidenceBundle
- exact-offset Anchor와 ContextSpan
- 표·목록 구조
- 문서 및 anchor 순서
- ExtractionRun

B0는 의미 개념이나 규칙을 생성하지 않는 구조 기준선이다.

### 5.2 R4-B1 Deterministic Conservative Core

B1은 B0에 다음 결정적 추출만 추가했다.

- 한글명과 영문·약어의 명시적 괄호 병기
- 명시 정의 cue와 정의 assertion
- 명시 deontic cue와 같은 anchor의 action span
- 조건·예외 cue
- exact 수량·범위·단위
- 번호·순서 cue가 있는 절차 단계
- table cell 기반 TemplateField
- example marker 기반 ExampleInstance

명시 deontic cue가 있더라도 다음 조건을 모두 통과해야 RuleBox에 들어간다.

```text
deontic cue 존재
+ 같은 atomic anchor의 action span
+ example/reported/hypothetical 아님
+ exact evidence anchor
+ SHACL policy 통과
```

명시 cue가 없는 암묵적 규범성, LLM의 일반 규칙 판정, 사례에서의 일반화는 사용하지 않았다.

### 5.3 R4-B2 Selective LLM

LLM에는 다음 닫힌 선택만 허용했다.

- cue와 action의 scope
- parenthetical alias 병합
- 등록된 action mention의 역할
- 등록된 quantity relation
- evidence-only candidate support

새 quote, concept, mention, relation 이름은 생성할 수 없다. LLM이 승인해도 결과는 operational assertion이 아니라 `SUPPORTED_CANDIDATE`에만 머문다.

DEV revision 1에서 source mismatch rejection이 0.60으로 실패했다. confirmatory는 노출하지 않은 상태에서 exact-substring 선검사를 prompt에 명시한 revision 2를 실행했다.

| 자격 지표 | Revision 2 |
|---|---:|
| Structured Output validity | 1.0000 |
| Candidate ID validity | 1.0000 |
| Source mismatch rejection | 1.0000 |
| Supported control recall | 1.0000 |
| Repeat agreement | 0.9750 |
| Control accuracy | 1.0000 |
| Unsupported free generation | 0 |

모델과 20% B2 budget을 이 결과로 잠갔다.

### 5.4 R4-B3 Exhaustive Gray-zone LLM

B3는 동일 prompt·schema·snapshot으로 confirmatory gray-zone 후보 146개를 모두 판정했다. B3는 정확도 상한이 아니라 비용과 coverage를 비교하기 위한 exhaustive 조건이다.

## 6. DEV 결정적 Gate

DEV B1 결과는 다음과 같다.

| 지표 | 결과 | Gate |
|---|---:|---:|
| Nodes / Edges | 1,014 / 2,313 | 보고 |
| Anchor offset round-trip | 1.0000 | 1.00 |
| Mention offset round-trip | 1.0000 | 1.00 |
| Assertion evidence coverage | 1.0000 | 1.00 |
| Provenance completeness | 1.0000 | 1.00 |
| Critical SHACL violation | 0 | 0 |
| Example→RuleBox | 0 | 0 |
| Rule without qualifying evidence | 0 | 0 |
| Deterministic metamorphic accuracy | 1.0000 | 1.00 |

따라서 R4-2는 PASS였다.

## 7. Confirmatory B0-B3 결과

| Metric | B0 | B1 | B2 | B3 |
|---|---:|---:|---:|---:|
| Nodes | 298 | 566 | 588 | 705 |
| Edges | 708 | 1,155 | 1,177 | 1,294 |
| Accepted concepts | 0 | 20 | 20 | 20 |
| Accepted aliases | 0 | 15 | 15 | 15 |
| Accepted assertions | 0 | 93 | 93 | 93 |
| Accepted explicit rules | 0 | 10 | 10 | 10 |
| Accepted LLM candidates | 0 | 0 | 22 | 139 |
| Policy-compliant graph yield | 0 | 153 | 175 | 292 |
| Critical violations | 0 | 0 | 0 | 0 |
| Provenance completeness | 1.00 | 1.00 | 1.00 | 1.00 |
| CQ answerability | 0.00 | 1.00 | 1.00 | 1.00 |
| API calls | 0 | 0 | 29 | 146 |

### B2 coverage

```text
B2 gain over B1 = 14.38%    기준 15% 이상 → 실패
B2 yield / B3 yield = 59.93% 기준 85% 이상 → 실패
B2 token / B3 token = 19.09% 기준 35% 이하 → 통과
```

leakage-group 5,000회 cluster bootstrap에서도 B2가 B3보다 승인한 후보 수는 평균 116.64개 적었으며 95% 구간은 `[-166, -73]`이었다.

B2는 비용은 줄였지만 정보가치 scoring이 B3에서 승인될 후보를 충분히 집중시키지 못했다. 따라서 H4-B와 H4-C는 지지되지 않았다.

## 8. 구조적 CQ

confirmatory 전에 다음 5종 CQ를 잠갔다.

1. 명시 정의
2. 표·양식 필드
3. 명시 순서 단계
4. 수량·범위 제약
5. 명시 규범 규칙

B1은 5종 모두에서 evidence path를 가진 답을 반환했다.

| 지표 | 결과 | Gate |
|---|---:|---:|
| CQ evidence answerability | 1.0000 | 0.80 이상 |
| Answer provenance precision | 1.0000 | 1.00 |
| Unsupported answer rate | 0.0000 | 0 |

이는 구조적 CQ가 동작한다는 의미이며, 인간 Gold에 대한 의미 정확도를 뜻하지 않는다.

## 9. RDF·SHACL·Neo4j

최종 canonical graph는 B1이다.

| 지표 | 결과 |
|---|---:|
| RDF triples | 11,402 |
| RDF serialization·재파싱 | PASS |
| pySHACL conforms | PASS |
| Custom critical SHACL violation | 0 |
| RDF node coverage | 1.0000 |
| RDF edge coverage | 1.0000 |
| Neo4j nodes | 566 |
| Neo4j relationships | 1,155 |
| Neo4j node projection coverage | 1.0000 |
| Neo4j edge projection coverage | 1.0000 |
| Neo4j provenance property coverage | 1.0000 |
| Rule→Anchor runtime paths | 10/10 |
| ExampleInstance in RuleBox | 0 |

실제 Neo4j Community 4.4.43 로컬 프로세스에 import하고 Cypher로 검증했다. 검증 후 임시 서버는 종료했으며 재사용 가능한 JSONL·CSV projection을 보존했다.

## 10. 가설 판정

| 가설 | 결과 | 해석 |
|---|---|---|
| H4-A 보수 코어 안전성 | **지지** | B1 grounding·SHACL·promotion Gate 통과 |
| H4-B 선택적 LLM coverage | **지지되지 않음** | B1 대비 14.38%로 15% 미달 |
| H4-C 선택적 LLM 비용 효율 | **지지되지 않음** | token은 절약했지만 B3 yield의 59.93% |
| H4-D 구조적 활용성 | **지지** | CQ answerability 1.00, provenance 1.00 |
| H4-E Neo4j projection | **지지** | node·edge·provenance coverage 1.00 |

## 11. 비용

| 구간 | API calls |
|---|---:|
| DEV qualification revision 1 | 393 |
| DEV qualification revision 2 | 393 |
| Confirmatory B2 | 29 |
| Confirmatory B3 | 146 |
| 합계 | **961** |

- Input tokens: `495,051`
- Output tokens: `45,357`
- Batch 할인 미반영 표준 가격 상한: `$1.352958`
- B0/B1 API 비용: 0
- TEST API 호출: 0
- API key 저장 파일: 0

## 12. 현재 만들어진 결과물

- Evidence Graph와 exact-offset provenance
- deterministic concept·alias·definition·quantity·procedure·template·rule core
- canonical RDF Turtle
- pySHACL validation report
- Neo4j node·relationship JSONL 및 CSV
- 실제 Neo4j runtime query 검증 결과
- B0~B3 비교 지표와 비용 원장
- 구조적 CQ 답과 evidence path

결과물의 올바른 명칭은 **Evidence-grounded Conservative Work Ontology Core**다. 인간 전문가 Gold나 완성된 전체 직무 온톨로지로 부르지 않는다.

## 13. 다음 단계

현재 operational core는 B1을 유지하는 것이 타당하다. 후속 실험은 새 ID에서 다음 중 하나로 진행해야 한다.

1. B2 scoring을 재설계해 B3가 승인한 후보를 상위 20%에 집중시키는 ranking 연구
2. 현재 `SUPPORTED_CANDIDATE` 139건에 대한 사람 calibration으로 실제 승격 precision 측정
3. B1 concept의 SKOS canonicalization과 relation refinement
4. B1 코어를 기준으로 제한적인 E0~E5 engineering 비교

같은 R4 experiment ID에서 scoring·threshold·prompt를 수정해 confirmatory를 다시 실행하면 안 된다.

