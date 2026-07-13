# 자이제 LDR-R3 APRE 실험 최종 상태 보고서

## 1. 한 문장 결론

R3는 **원문을 원자적인 anchor로 나누고 Claim 여부를 안정적으로 판정하는 단계까지는 성공**했지만, Claim의 규범성·일반 규칙성·예시성 같은 의미 field를 독립 모델이 다시 확인했을 때 모순이 너무 많이 발견되어 **`BOUNDARY_REFERENCE_ONLY`에서 중단**했다.

즉, 이번 실험에서 신뢰할 수 있다고 인정한 것은 “원문의 어느 부분이 Claim 단위인가”까지다. 그 Claim이 일반 규칙인지, 의무인지, 예시인지와 같은 상세 의미 reference, argument, E0-E5 비교, 온톨로지 및 Neo4j 그래프는 아직 신뢰할 수 있는 결과로 만들지 않았다.

## 2. 왜 R3를 다시 했는가

선행 R2는 여러 후보를 한 요청에 배열로 제시했을 때 후보 순서에 따라 답이 달라졌고, 사전등록에 필요한 3개 모델 패널을 구성하지 못해 fresh pilot 전에 중단됐다. R3는 신뢰 근거를 “모델 3개의 다수결”에서 다음 네 요소로 바꿨다.

1. 프로그램이 원문에서 exact-offset atomic anchor를 만든다.
2. LLM에는 한 번에 anchor 또는 field proposal 하나만 보여 준다.
3. 한 primary snapshot의 동일 측정을 3회 반복해 재현성을 확인한다.
4. 다른 snapshot의 falsifier가 고위험 결과를 반증 관점에서 검사한다.

이 방법을 **APRE(Anchor-Pointwise Reference Envelope)**라고 사전등록했다. 결과물은 인간 Gold가 아니라 잠정 engineering reference를 목표로 한다.

## 3. 사용 데이터와 누출 통제

- 원본: `legacy/자이제_1.xlsx`
- 원본 binary SHA-256: `9246a6da6c7635b3f34ee55df75112eb38a2984ea06828be943dc196de5926eb`
- 기존 R2의 미노출 fresh 60을 membership 변경 없이 import했다.
- imported JSONL SHA-256: `3e499252899e964b7363310e5733961fc3e6aa65aa4d0d382537839173003b17`
- DEV_EXPOSED와 fresh의 Evidence 및 leakage group 중복: 0
- TEST 원문·reference·API 호출: 0
- fresh 60은 R3-0~R3-2 통과 후에만 처음 API에 노출했다.

## 4. 실제 실행 방법

### 4.1 Gate R3-0: 데이터와 잠금

fresh 60의 membership, 원본 hash, DEV 중복, TEST 미접근, 모델·prompt·schema 정책을 검사했다. **PASS**였다.

### 4.2 Gate R3-1: deterministic atomic anchor

프로그램이 prose clause, list item, table cell을 exact character offset으로 분리했다. 목록 header, 표 caption, 행·열 header는 anchor 본문과 합치지 않고 context span으로 연결했다.

DEV_EXPOSED_60에서만 free-span 진단을 사용해 분절기를 개발했다. 세 번의 DEV 진단 revision을 모두 보존했고 fresh에는 이 과정에서 API를 호출하지 않았다. 최종 분절기는 DEV 60건에서 243개 anchor를 만들었다.

| 지표 | 결과 | 기준 |
|---|---:|---:|
| Offset round-trip | 1.0000 | 1.00 |
| Anchor ID uniqueness | 1.0000 | 1.00 |
| Context span existence | 1.0000 | 1.00 |
| Deterministic rerun identity | 1.0000 | 1.00 |
| Missing anchor | 0.0000 | 0.05 이하 |
| Over-merged anchor | 0.0453 | 0.05 이하 |
| 정의상 structural-context 누락 | 0.0000 | 0.02 이하 |

결과는 **PASS**였다. 최종 fresh 60에서는 70개 anchor가 생성됐다.

### 4.3 Gate R3-2: primary와 falsifier 자격시험

DEV_EXPOSED_24에서 각 primary 후보를 claimhood와 네 binary facet에 대해 2회씩 pointwise 측정했다. 또한 source-anchor 일치와 의도적인 mismatch를 균형 control로 넣었다. 총 936개의 DEV 요청을 사용했다.

| Primary | Claim 반복 일치 | Positive-set F1 | 최저 facet 일치 | Control BA | 자격 |
|---|---:|---:|---:|---:|---|
| C02 / gpt-4.1-mini | 1.0000 | 1.0000 | 0.8750 | 0.9583 | 실패 |
| C03 / gpt-4o | 0.9583 | 0.9744 | 0.8750 | 0.9167 | 실패 |
| C04 / gpt-4.1 | 0.9583 | 0.9756 | 1.0000 | 0.9583 | **통과** |

falsifier 후보는 supported/contradicted proposal을 2회 판정했다. C01은 supported recall, contradicted recall, 반복 일치가 모두 1.00이었다.

- Primary lock: `C04 / gpt-4.1-2025-04-14`
- Independent falsifier lock: `C01 / gpt-4o-mini-2024-07-18`
- 두 역할의 snapshot 중복: 없음
- Gate 결과: **PASS**

### 4.4 Gate R3-3: fresh pointwise Claimhood

fresh 60에서 생성한 70개 anchor 각각을 primary가 3회 독립 판정했다. 한 요청에는 anchor 하나만 넣었고 Batch API의 응답은 `custom_id`로 결합했다. 별도로 20개 source-anchor mismatch control을 넣었다.

| 지표 | 결과 | 기준 |
|---|---:|---:|
| 3-repeat exact agreement | 1.0000 | 0.90 이상 |
| Positive-set pairwise F1 median | 1.0000 | 0.90 이상 |
| HARD+SOFT coverage | 1.0000 | 0.90 이상 |
| BOUNDARY_UNSTABLE | 0.0000 | 0.10 이하 |
| Mismatch false KEEP | 0.0000 | 0.05 이하 |
| Duplicate consistency | 1.0000 | 0.95 이상 |

결과는 `BOUNDARY_HARD_KEEP 64`, `BOUNDARY_HARD_DROP 6`이며 Gate는 **PASS**였다. 따라서 64개 anchor는 APRE boundary/claimhood 연구의 잠정 reference로 사용할 수 있다.

### 4.5 Gate R3-4: cue-first field와 독립 반증

64개 KEEP Claim에서 프로그램이 의무·권고·금지·부정·조건·예외·예시·정의·수량 cue를 exact offset으로 추출했다. 명시 cue로 확정되는 field는 `RULE_HARD`로 처리하고, 나머지 핵심 facet과 cue scope 294개만 primary가 각각 3회 판정했다. primary 요청은 총 882건이었다.

반복 안정성은 높았다.

| Field | 3회 exact agreement | Gwet AC1 |
|---|---:|---:|
| GENERALIZABLE_RULE | 0.9844 | 0.9849 |
| IS_NORMATIVE | 0.9630 | 0.9676 |
| IS_PROCEDURAL | 0.9531 | 0.9388 |
| SPECIFIC_EXAMPLE_INSTANCE | 0.9833 | 0.9854 |
| DEONTIC_SCOPE | 0.9000 | 0.9287 |
| NEGATION/CONDITION/EXCEPTION_SCOPE | 1.0000 | 1.0000 |

그러나 안정성만으로 정확성을 주장하지 않기 위해, 고위험 `SUPPORTED` 151건을 C01 falsifier에 보냈다. 이 단계에서 다음 문제가 드러났다.

| 핵심 문제 | 결과 | 허용 기준 |
|---|---:|---:|
| Falsifier contradiction rate | **0.3311** | 0.02 이하 |
| Falsifier accepted/soft | **0.6689** | 0.90 이상 |
| General rule + specific example 동시 승격 | **0.2656** | 0.05 이하 |

특히 falsifier contradiction은 `IS_NORMATIVE 28건`, `GENERALIZABLE_RULE 17건`, 조건·예외·부정 scope 4건, example 1건이었다. 최종 field envelope에는 50건이 `QUARANTINED`됐다.

따라서 Gate R3-4는 **REVISE**이며, 전체 실험 판정은 설계서의 시나리오 B에 따라 **`BOUNDARY_REFERENCE_ONLY`**다.

## 5. 현재 확보한 것과 확보하지 못한 것

### 확보한 것

- 입력·split·fresh membership 무결성
- exact-offset atomic anchor segmenter
- 64개 `BOUNDARY_HARD_KEEP` Claim anchor
- 6개 `BOUNDARY_HARD_DROP` anchor
- 점단위 claimhood protocol의 fresh 반복 안정성
- primary/falsifier 역할 분리와 모든 raw API provenance
- field 실패의 구체적 오류 분포

### 확보하지 못한 것

- 신뢰 가능한 semantic field APRE-LDR
- argument role reference와 mention 평가
- Gate R3-5 argument 성능
- Gate R3-6 전체 reference viability
- APRE-LDR-INDUCTION/VALIDATION 확장
- E0~E5 상대 성능 비교
- 온톨로지 귀납·SHACL·CQ 평가
- Neo4j 그래프 변환과 evidence path 검증
- 인간 전문가 정확도 또는 Gold 동등성

이 항목들은 “성능이 낮았다”가 아니라 **선행 Gate 실패 때문에 실행하지 않은 것**이다.

## 6. 무엇이 문제였는가

R3는 R2의 후보 순서 문제를 해결했다. Claimhood도 매우 안정적이었다. 현재 병목은 boundary가 아니라 **field의 의미 과잉 승격**이다.

1. 동일 primary는 같은 답을 반복했지만, 독립 falsifier는 그 답의 상당수를 원문이 지지하지 않는다고 판단했다.
2. 특히 설명적·절차적 문장을 암묵적 규범으로 해석하는 경향이 강했다.
3. 구체적 사례에서도 재사용 가능한 일반 규칙을 동시에 인정하는 비율이 높았다.
4. 따라서 “반복 일치가 높다 = 정확하다”는 결론은 기각됐다.

이 중단은 실패를 숨긴 것이 아니라, 안정적으로 틀릴 수 있는 field를 온톨로지와 Neo4j 그래프에 넣지 않기 위한 안전 조치다.

## 7. 비용과 재현성

| 구간 | 고유 API 요청 |
|---|---:|
| DEV segmenter diagnostic 3 revisions | 180 |
| DEV model role qualification | 936 |
| Fresh claimhood | 230 |
| Fresh semantic fields | 882 |
| Fresh high-risk falsifier | 151 |
| 합계 | **2,379** |

- Input tokens: `931,324`
- Output tokens: `75,594`
- 표준 가격 기준 상한 추정: `$1.896916`
- Batch 할인은 비용 추정에 반영하지 않았다.
- API key 저장 파일: 0
- TEST API 요청: 0

모든 prompt, schema, model snapshot, batch input, logical request manifest, raw response, output, token usage, lock hash를 experiment 폴더에 보존했다.

## 8. 다음 실험에 대한 권고

같은 experiment ID에서 prompt나 threshold를 수정해 다시 실행하면 안 된다. 후속 run은 새 ID로 등록해야 한다.

가장 우선할 변경은 다음과 같다.

1. `IS_NORMATIVE`는 암묵 판정을 당분간 금지하고 명시 deontic cue + scope가 있는 경우만 reference에 포함한다.
2. `GENERALIZABLE_RULE`은 모델 단독 승격을 금지하고 example/template/reported cue가 있으면 기본 `DO_NOT_PROMOTE`로 둔다.
3. primary와 falsifier가 충돌한 50건을 대상으로 사람 20~40건 calibration을 도입해 어느 쪽이 과잉/과소 판정인지 확인한다.
4. 인간 calibration 없이 계속하려면 field reference를 포기하고, 이번에 통과한 boundary reference와 결정적 cue·구조·CQ 지표만으로 연구 질문을 축소한다.

현재 데이터 상태에서는 fresh 60이 이미 R3 API에 노출됐으므로, 이 60건을 다시 “미노출 confirmatory sample”이라고 부를 수 없다.

