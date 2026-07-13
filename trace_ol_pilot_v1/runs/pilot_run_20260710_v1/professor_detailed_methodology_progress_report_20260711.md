# TRACE-OL 자이제 지식그래프 파일럿

## 방법론·실험 절차·진행 현황·문제점 상세 보고서

- 보고 기준일: 2026-07-11
- 원본 데이터: `자이제_1.xlsx`
- 원본 행 수: 1,366 evidence units
- 최종 현황: 초기 파일럿 v1, LF v2, LF v2.1, modality-safe LF v2.2까지 실행 완료
- 현재 판정: **연구 가능성은 확인했지만 본 실험·운영 적용 전 방법 보완이 필요한 `REVISE` 단계**

---

## 1. 이 연구를 한 문장으로 설명하면

자이제 문서의 문장을 바로 subject-predicate-object 관계로 바꾸지 않고, **원문이 주장하는 의미를 구조화한 Atomic Work Claim으로 먼저 표현한 후 그래프로 전환**하면 의무, 금지, 부정, 조건, 예시 오승격 같은 오류를 줄이고 원문까지 추적 가능한 지식그래프를 만들 수 있는지 확인하는 연구이다.

또한 모든 문장을 LLM에 보내지 않고, 규칙으로 처리할 수 있는 문장은 labeling function, 즉 LF로 처리하고 어렵거나 위험한 경우만 LLM에 보내 비용을 줄일 수 있는지 검증했다.

---

## 2. 먼저 알아야 할 핵심 용어

| 용어 | 뜻 | 이 연구에서의 역할 |
|---|---|---|
| Evidence | 주장의 근거가 되는 원문 단위 | Excel의 각 문장·표 행 |
| Evidence bundle | target 원문과 앞뒤 context, 섹션, 표 header 등을 함께 묶은 입력 | 문장 하나만 보고 오해하는 문제 완화 |
| Source span | 주장의 근거가 된 정확한 문자열 위치 | `evidence_id`, `text`, `start`, `end`로 저장 |
| Claim | 원문이 주장하는 의미를 구조화한 중간 표현 | 의무·부정·조건·예시 여부 보존 |
| Triple | subject-predicate-object 관계 | 최종 지식그래프의 기본 관계 표현 |
| Assertion | Claim 중 그래프에 사용하도록 승인된 지식 | Claim과 operational relation 사이의 검증 단계 |
| Promotion | Claim을 실제 그래프 지식으로 승격하는 과정 | 예시·질문·NeedsReview의 잘못된 승격 차단 |
| Modality | 의무·금지·권고·가능·단순 서술 구분 | MUST, MUST_NOT, SHOULD, MAY, DESCRIPTIVE, NONE |
| Polarity | 긍정·부정 방향 | POSITIVE, NEGATIVE, NONE |
| Discourse claim | 예시, 질문, 인용, 반례 같은 담화적 표현 | 일반 사실로 승격하지 않음 |
| LLM-Silver | 여러 LLM 주석을 합의해 만든 임시 정답 | 인간 gold가 없어 실험 기준으로 사용 |
| Challenge | LLM 합의로도 안정적으로 해석하지 못한 사례 | 주요 성능 평가에서 제외 |
| LF | Labeling Function, 특정 패턴이 보이면 일부 label을 반환하는 재사용 규칙 | LLM 호출 전에 자동 판정 |
| Selective LLM | 전체가 아니라 어렵거나 위험한 후보만 LLM이 검토하는 방식 | 품질을 유지하며 비용 절감 시도 |
| Safe abstain | 규칙의 근거가 부족하거나 충돌하면 자동 판정을 포기하는 정책 | 오류가 큰 자동 교정 차단 |

---

## 3. 왜 바로 triple을 만들지 않고 Claim을 거치는가

예를 들어 원문이 다음과 같다고 가정한다.

> 계약 금액이 10억 원을 초과하는 경우, 제안팀은 반드시 법무 검토를 받아야 한다.

바로 triple을 만들면 다음정도로 축약될 수 있다.

```text
(제안팀) -[받는다]-> (법무 검토)
```

이 표현에서는 다음 정보가 빠질 수 있다.

- 10억 원을 초과할 때만 적용된다는 조건
- `반드시`라는 의무
- 단순 사실이 아니라 규칙이라는 점
- 정확한 원문 근거

Claim-first 방법은 다음과 같이 중간 표현을 먼저 만든다.

```text
claim_type: ConditionalRule
subject: 제안팀
action: 법무 검토를 받는다
condition: 계약 금액이 10억 원을 초과하는 경우
modality: MUST
polarity: POSITIVE
promotion_target: RULE_NODE
source_span: 원문의 정확한 evidence ID와 문자 위치
```

이 Claim을 확인한 뒤 그래프로 변환하면 조건과 의미를 잃어버릴 가능성을 줄일 수 있다. Claim은 그래프에 들어가기 전의 **의미 보존 및 감사 계층**이다.

---

## 4. 연구 질문

본 파일럿은 다음 네 가지를 확인하도록 설계했다.

1. 직접 triple 추출보다 Claim-first 표현이 modality, 부정, 조건, discourse 오승격 오류를 줄이는가?
2. 규칙 기반 추출 E2에 선택적 LLM 판정을 추가한 E3가 비용 대비 품질을 개선하는가?
3. B1에서 유도·검증한 LF를 B2에 적용한 E4가 LLM 호출을 줄이면서 E1에 가까운 성능을 내는가?
4. 생성된 Claim과 operational Assertion이 원문 Evidence까지 추적 가능한 Neo4j 그래프로 안전하게 전환되는가?

---

## 5. 입력 데이터와 전처리

### 5.1 입력 고정

- 파일: `handoff-hanyang/.../자이제_1.xlsx`
- sheet: `clean_sentences`
- evidence units: 1,366개
- SHA-256: `e8c5f174b65eccd7a50dbd2e0e216ea870a6aedfd16b3e4538d6486aea15cf1f`

실행 시 파일 hash가 고정된 값과 다르면 실험이 중단되도록 했다. 이는 파일명이 같은 다른 버전이 결과에 혼입되는 것을 방지한다.

### 5.2 Evidence unit 생성

각 원문 행에 다음을 부여했다.

- 고유 `evidence_id`
- Excel row, page, chapter, section
- 원문 텍스트와 SHA-256
- block type: prose, question, figure caption, list, mixed, markdown table
- section ID, table ID, list ID
- duplicate cluster ID
- 실험용 stratum

### 5.3 Evidence bundle 생성

LLM이 target 문장 하나만 보고 주체나 대상을 임의로 만드는 것을 줄이기 위해 다음을 함께 제공했다.

- target evidence
- 직전·직후 evidence
- section metadata
- table header
- context 복원 여부

Context에서 주체를 복원한 경우에는 `restored_from_context=true`와 context evidence ID를 남기도록 했다.

### 5.4 층화 구성

다음 6개 유형을 파일럿의 주요 stratum으로 정했다.

1. definition/descriptive
2. normative
3. condition/exception
4. procedure/decision
5. table/formula/evaluation
6. discourse/ambiguous

단순 무작위 표본만 사용하면 수가 적은 금지·조건·표 문장이 빠질 수 있어, 층화 표적 표본과 무작위 표본을 함께 사용했다.

---

## 6. Atomic Work Claim schema

사용한 schema version은 `atomic-claim-v0.2`다. 각 Claim은 주요하게 다음을 포함한다.

| 필드 | 설명 |
|---|---|
| source_span | Claim의 정확한 원문 근거 |
| claim_family | FACTUAL, NORMATIVE, CONDITIONAL, PROCEDURAL, EVALUATIVE, DISCOURSE, UNCLEAR |
| claim_type | Definition, Obligation, Prohibition, ConditionalRule, ProcessOrder, Example, Question 등 |
| arguments | 주체, 객체, 행위, 도구 등의 역할과 span |
| predicate_normalized | 표현을 정규화한 predicate |
| modality | MUST, MUST_NOT, SHOULD, MAY, DESCRIPTIVE, NONE |
| polarity | POSITIVE, NEGATIVE, NONE |
| conditions | 이 Claim이 적용되는 조건 |
| exceptions | 예외 조건 |
| promotion_target | FACT_ASSERTION, RULE_NODE, PROCESS_EDGE, EVALUATION_NODE, NONE 등 |
| decision | ACCEPT, REJECT, ABSTAIN, NEEDS_REVIEW |
| uncertainty_code | 불확실성의 원인 |

설계상 중요한 안전 규칙은 다음과 같다.

- MUST_NOT은 NEGATIVE polarity와 함께 표현한다.
- ConditionalRule은 조건 span이 없으면 유효한 규칙으로 취급하지 않는다.
- Example, CounterExample, Question, Quotation은 기본적으로 operational graph에 승격하지 않는다.
- NEEDS_REVIEW는 audit에는 남지만 실제 operational relation으로 사용하지 않는다.
- 원문 span이 없거나 원문과 다르면 Claim을 제거하거나 검토 대상으로 남긴다.

---

## 7. 임시 정답 TRACE-LLM-Silver 생성 방법

### 7.1 왜 LLM-Silver를 사용했는가

이 데이터에는 인간 전문가가 만든 Atomic Claim gold label이 없었다. 따라서 하나의 LLM 결과를 바로 정답으로 사용하지 않고, 여러 번의 독립 주석과 합의 절차를 사용했다.

임시 정답의 이름은 `TRACE-LLM-Silver-v0.1`이다.

### 7.2 주석 모델

- A/B/C: `gpt-4o-mini-2024-07-18`
- D: `gpt-4o-2024-08-06`
- temperature: 0
- structured output: strict JSON schema

A와 B는 서로 다른 prompt와 별도 API call을 사용했지만 같은 model snapshot을 사용했다. 따라서 완전한 독립 주석자가 아닌 **pseudo-independent annotation**이다.

### 7.3 합의 절차

1. A와 B가 전체 180건을 서로의 결과를 보지 않고 주석했다.
2. A/B Claim을 source span, argument, predicate, family 유사도로 정렬했다.
3. Claim 개수와 critical field가 모두 일치하면 Silver-A로 정했다.
4. A/B가 다른 evidence는 C가 A/B 결과를 보지 않고 다시 주석했다.
5. A/B/C 중 두 개 이상이 일치하면 Silver-B로 해소했다.
6. 남은 고위험 충돌 중 비용 기준을 만족한 1건에 D를 사용했다.
7. 끝까지 안정적으로 해소하지 못한 evidence는 Challenge로 남겼다.

### 7.4 Claim 정렬 점수

```text
alignment = 0.50 * source span overlap
          + 0.25 * argument overlap
          + 0.15 * normalized predicate similarity
          + 0.10 * claim family match
```

정렬 기준은 0.50이다. 정렬된 Claim에서 claim type, modality, polarity, promotion target, condition 유무를 critical signature로 비교했다.

### 7.5 v1 reference 결과

| 구분 | 건수 |
|---|---:|
| Silver-A | 69 |
| Silver-B | 39 |
| Challenge | 72 |
| 전체 | 180 |

- A/B critical agreement rate: 38.33%
- Silver resolved coverage: 60.00%
- Challenge rate: 40.00%
- reference 생성 단계 source span validity: 96.38%
- semantic-invalid claim 제거: 17개
- 제거 후 공개 reference에 남은 span substring 오류: 0개

이 결과는 reference 자체의 불확실성이 크다는 것을 보여준다. 특히 Challenge 40%는 최종 평가 표본이 크게 줄어드는 원인이 되었다.

---

## 8. v1 표본·분할·잠금 정책

### 8.1 표본

- 층화 표적 표본: 6개 stratum × 25 = 150건
- seed 기반 무작위 표본: 30건
- 총 180건
- seed: `20260710`

### 8.2 분할

| Split | 건수 | 용도 |
|---|---:|---|
| CAL | 60 | schema, 규칙, threshold 확인 |
| B1 | 60 | selective LLM과 LF 유도·검증 |
| B2_LOCKED | 60 | 최종 시스템 비교 |

B1은 다시 B1a induction 40건과 B1b validation 20건으로 나누었다.

### 8.3 누출 방지

다음을 group key로 사용했다.

- section ID
- table ID
- list ID
- duplicate cluster ID

동일 group이 두 split에 들어가지 않도록 분할했고, audit 결과 group overlap은 0건이었다.

### 8.4 B2 잠금

B2 evidence ID와 lock hash를 시스템 결과 전에 저장했다. B2 결과를 본 후 prompt, LF, threshold, schema를 바꾸지 않았다.

후속 실험에서 방법을 바꾸었기 때문에 기존 B2는 다시 최종 test로 사용하지 않았고, 매 version에서 이전 evidence와 겹치지 않는 fresh locked test를 만들었다.

---

## 9. 비교 시스템 E0∼E4

### 9.1 E0: Direct Triple Full-LLM

원문에서 subject-predicate-object triple을 바로 추출했다. Atomic Claim 중간 표현은 사용하지 않았다.

평가를 위해 source span이 유효한 triple을 최소 Claim 형태로 projection했지만, 추출 자체는 direct triple 방식으로 수행했다.

### 9.2 E1: Claim-first Full-LLM

B2 전체에 LLM을 사용해 Atomic Claim을 추출하고 promotion target까지 판정했다. 품질 상한선에 해당하지만 LLM 비용이 크다.

### 9.3 E2: TRACE No-LLM

LLM을 사용하지 않고 문장 cue와 block type을 사용해 Claim 후보를 만들었다.

예시 cue는 다음과 같다.

- `해야 한다`, `반드시`, `필수` → Obligation/MUST 후보
- `하지 말아야`, `금지` → Prohibition/MUST_NOT 후보
- `경우`, `만약` → ConditionalRule 후보
- `예를 들어`, `사례` → Example, 기본 비승격
- `?` → Question, 비승격
- table, BCM, 점수, 비중 → evaluation 후보

### 9.4 E3: TRACE Selective-LLM

E2가 만든 후보 전체를 LLM에 보내지 않고 위험과 불확실성이 높은 후보만 보냈다.

```text
priority = 0.45 * uncertainty
         + 0.30 * risk
         + 0.15 * novelty
         + 0.10 * graph impact
```

선택 조건은 다음과 같다.

- priority 0.65 이상
- 고위험 Claim이면 confidence 0.90 미만
- NEEDS_REVIEW
- 전체 candidate의 최대 15%, split당 최대 30개

### 9.5 E4: TRACE Selective + Distillation

E3의 검증된 교정에서 반복 패턴을 LF로 만들고, 별도 validation에서 precision과 support를 통과한 LF만 B2에 적용하는 방법이다.

기존 설계의 활성 기준은 유형별로 다음과 같다.

- Definition/DescriptiveFact: precision 0.85, support 4 이상
- ActivityOutput/ProcessOrder: precision 0.90, support 3 이상
- Obligation/Prohibition: precision 0.95, support 3 이상, critical error 0
- Discourse blocking: precision 0.95, support 3 이상, critical error 0

---

## 10. 평가 방법

### 10.1 주요 참조 범위

- Primary evaluation: Silver-A + Silver-B
- Challenge: primary metric에서 제외
- Sensitivity evaluation: Silver-A만 별도 확인 가능

### 10.2 성능 지표

| 지표 | 의미 |
|---|---|
| Claim precision | 시스템이 만든 Claim 중 임시 정답과 정렬된 비율 |
| Claim recall | 임시 정답 Claim 중 시스템이 찾은 비율 |
| Claim F1 | precision과 recall의 조화평균 |
| Family macro-F1 | Claim family별 성능을 같은 비중으로 평균 |
| Type macro-F1 | 세부 Claim type 분류 성능 |
| Modality macro-F1 | MUST, MUST_NOT, SHOULD 등 양태 분류 성능 |
| Promotion macro-F1 | 그래프 승격 대상 분류 성능 |
| Graph F1 | evidence, predicate, promotion target 기반 graph signature 일치 |
| Critical error rate | modality, 부정, 조건, discourse 오승격 오류 비율 |

### 10.3 Critical error

다음을 중요 오류로 계산했다.

- modality confusion
- negation/polarity drop
- condition drop
- discourse promotion
- source evidence가 없는 assertion

### 10.4 Bootstrap

Evidence unit을 단위로 2,000회 복원 추출해 Claim F1의 percentile 95% confidence interval을 계산했다. 표본이 작으므로 단일 F1 값만으로 결론내지 않기 위한 절차다.

### 10.5 성공 게이트

실험 전에 다음 기준을 고정했다.

- source span validity 0.98 이상
- Silver resolved coverage 0.80 이상
- Challenge rate 0.20 이하
- E1 critical error relative reduction 0.30 이상
- E4가 E1 family macro-F1의 0.05 이내
- E4/E1 token ratio 0.40 이하
- distillation으로 LLM call 0.20 이상 감소
- provenance path coverage 1.0
- competency query 10개 중 8개 이상 통과

---

## 11. v1 실험 결과

### 11.1 성능

B2 60건 중 Silver-A/B로 해소된 30건만 primary metric에 포함되었다.

| 시스템 | Claim F1 | Family macro-F1 | Critical error rate |
|---|---:|---:|---:|
| E0 Direct Triple | 0.7843 | 0.2745 | 0.9000 |
| E1 Claim-first Full-LLM | **0.9310** | **0.4447** | **0.4074** |
| E2 No-LLM | 0.5902 | 0.2611 | 0.5556 |
| E4 Selective + Distill | 0.5902 | 0.2611 | 0.5556 |
| E2-flat subset | 0.5217 | 0.1667 | 0.6667 |

### 11.2 핵심 해석

- E1의 Claim F1이 E0보다 0.1467 높았다.
- E1의 critical error rate는 E0 대비 약 54.7% 감소했다.
- Claim-first 표현이 의미 보존에 유리할 가능성을 확인했다.
- 하지만 B2에서 안정적으로 해소된 평가 evidence가 30건에 불과하여 잠정적 결론이다.

### 11.3 E3·E4 실패

B1a 40건의 E2 Claim 중 6개가 Selective-LLM 후보로 선정되었다. 6개 모두 ConditionalRule이었고 LLM은 전부 `needs_review`로 판정했다.

그 결과:

- accepted correction: 0개
- LF candidate: 0개
- active LF: 0개
- E4가 E2와 동일한 Claim F1을 보임

즉, E4 가설을 충분히 실험하지 못했다.

### 11.4 v1 성공 게이트

| 게이트 | 결과 |
|---|---|
| source span validity | FAIL |
| Silver resolved coverage | FAIL |
| Challenge rate | FAIL |
| E1 critical error reduction | PASS |
| E4-E1 performance gap | FAIL |
| E4/E1 token ratio | PASS |
| distillation call reduction | FAIL |
| provenance coverage | PASS |
| competency query | PASS |

최종 4/9 PASS로 `STOP_OR_REVISE`를 반환했다.

---

## 12. Neo4j 변환 방법과 결과

### 12.1 그래프 계층

```text
Document
  ↓ HAS_SECTION
Section
  ↓ HAS_EVIDENCE
Evidence
  ↓ SUPPORTS
Claim
  ↓ PROMOTED_TO
Assertion / Rule
  ↓
Operational relation
```

사용자가 최종 operational relation을 보더라도 Claim과 Evidence를 거쳐 원문까지 돌아갈 수 있게 했다.

### 12.2 내보내기 결과

| 항목 | 개수 |
|---|---:|
| Document | 1 |
| Section | 36 |
| Evidence | 180 |
| Claim | 238 |
| Concept | 31 |
| Assertion | 52 |
| Rule | 5 |
| Condition | 8 |
| Relationship | 438 |
| Operational relationship | 11 |

### 12.3 정적 무결성

다음 오류는 모두 0건이었다.

- Evidence가 없는 accepted Claim
- source Claim이 없는 accepted Assertion
- discourse의 operational promotion
- NeedsReview의 operational promotion
- MUST_NOT/polarity 충돌
- lineage가 없는 operational relation
- orphan Concept

Provenance path coverage는 1.0이었고, competency query는 8/10을 통과했다.

### 12.4 남은 한계

Docker daemon socket 권한이 없어 실제 Neo4j 인스턴스에 CSV를 로드하고 Cypher를 실행하지는 못했다.

따라서 정확한 표현은 다음과 같다.

- CSV·Cypher 산출물 생성: 완료
- endpoint·ID·lineage 정적 검증: 완료
- 실제 Neo4j runtime 검증: 미완료

---

## 13. 재사용 규칙 실험이 v2∼v2.2로 변경된 과정

### 13.1 v1 LF 실패의 원인

v1의 E3는 B1a 40건 중 6개만 선정했고, 6개 모두 `경우`를 포함한 ConditionalRule 후보였다.

즉, 교정 사례의 다양성이 없었다. 또한 LF 생성기는 `하지 말아야`, `해야 한다`, `경우`, `단계`, `이란`, `예를 들어`, `점수`, `결과물` 등 일부 고정 cue만 찾았다.

그 결과 accepted correction이 없었고 LF를 하나도 만들지 못했다.

### 13.2 LF v2: Teacher-to-LF 재설계

새 실험에서는 v1 표본 180건을 제외한 원문에서 다음을 새로 뽑았다.

- induction 90건
- validation 60건
- retired fresh test 60건

Induction 전체를 teacher LLM으로 주석한 후 다음 feature를 채굴했다.

- 사전 cue 정규식
- token
- token bigram
- block type
- 문장 family

하지만 v2는 하나의 LF가 다음 5개를 모두 동시에 맞혀야 하도록 설계했다.

- claim family
- claim type
- modality
- polarity
- promotion target

Teacher 주석의 표현 차이 때문에 완전한 5-field signature가 반복되지 않아 LF 후보가 1개만 생성되었고, validation을 통과한 LF는 0개였다.

Fresh test A 두 배치가 시작되었지만 test label과 metric을 조립·분석하기 전에 실험을 중단했다. 해당 test는 폐기하고 다시 사용하지 않았다.

### 13.3 LF v2.1: Field-level LF

v2의 문제를 해결하기 위해 Claim 전체를 하나의 LF로 예측하지 않고 다음을 별도 LF로 나누었다.

- claim family LF
- claim type LF
- modality LF
- polarity LF
- promotion target LF

사전 선언 LF와 induction에서 자동 채굴한 field LF를 함께 사용했다.

#### 데이터

- 새 validation: 60건
- 새 fresh locked test: 60건
- v1·v2 이전 evidence와 중복: 0건
- validation/test group overlap: 0건
- validation resolved: 42/60
- test resolved: 30/60

#### 규칙 생성 결과

- LF candidate: 74개
- validation 통과: 9개
- 상관·중복 정리 후 active LF: 6개

최종 active LF의 예는 다음과 같다.

| 패턴 | 예측 | Validation support | Validation precision |
|---|---|---:|---:|
| descriptive family | POSITIVE polarity | 6 | 1.0000 |
| procedure family | FACTUAL family | 4 | 1.0000 |
| explicit obligation | POSITIVE polarity | 4 | 1.0000 |
| observational `경우가/경우에는` | FACTUAL family | 3 | 1.0000 |
| observational `경우가/경우에는` | DescriptiveFact type | 3 | 1.0000 |
| process cue | FACTUAL family | 7 | 0.8571 |

#### Fresh test 결과

- resolved test: 30건
- LF 적용: 16건
- 적용 정답: 14건
- LF precision: 87.50%
- LF coverage: 53.33%
- Claim F1: 0.8571 → 0.9286
- LLM 검토 후보: 16 → 13
- LLM 후보 감소: 18.75%
- critical error rate: 0.7083 → 0.7308

#### 해석

재사용 규칙을 실제로 만드는 것에는 성공했고 Claim F1도 상승했다. 하지만 추가로 정렬된 Claim에서 modality mismatch 2건이 더 드러나 critical error rate가 악화되었다. LLM 절감도 20% 목표에 1.25%p 부족했다.

따라서 6/8 게이트를 통과했지만 최종 판정은 `REVISE`였다.

### 13.4 LF v2.2: Modality-aware package + Safe abstain

v2.1에서 family나 polarity 하나만 맞힌 LF가 Claim을 정렬시키면서 modality 오류가 드러난 문제를 보완했다.

v2.2에서는 다음을 함께 검증한 패키지만 자동 적용했다.

- claim type
- modality
- polarity
- promotion target
- 필요한 경우 claim family

Modality 해석이 두 개로 경쟁하거나 support가 부족하면 자동 적용하지 않는 safe-abstain 정책을 사용했다.

#### 데이터

- 새 validation: 50건
- 새 fresh locked test: 50건
- 이전 v1·v2·v2.1 510건과 evidence 중복: 0건
- validation/test group overlap: 0건
- validation resolved: 26/50
- test resolved: 33/50

#### Package 결과

- 사전 package candidate: 7개
- active package: explicit question 1개
- validation에서 차단된 package: 6개
- fresh test에서 차단 package가 발화했지만 자동 교정을 보류한 행: 6건

#### Fresh test 결과

- explicit question package: 5/5 정답
- package precision: 100%
- package coverage: 15.15%
- Claim F1: 0.8788 → 0.8788
- critical error rate: 0.2759 → 0.2759
- LLM 검토 후보: 7 → 7
- LLM 감소: 0%
- gate: 6/7 PASS, `REVISE`

#### 해석

Safe policy는 v2.1의 critical error 악화를 막았다. 하지만 유일하게 통과한 질문 package는 E2가 이미 잘 처리하는 유형이었다. 따라서 안전성은 회복했지만 추가 성능 향상과 LLM 절감은 없었다.

---

## 14. 현재까지 어디까지 진행되었는가

| 항목 | 상태 | 설명 |
|---|---|---|
| Excel evidence 정규화 | 완료 | 1,366 evidence unit 및 bundle 생성 |
| Atomic Claim schema | 완료 | v0.2 schema·span·enum 검증 |
| v1 층화 표본 | 완료 | 180건, CAL/B1/B2 각 60 |
| LLM-Silver reference | 완료 | Silver-A 69, Silver-B 39, Challenge 72 |
| E0∼E4 비교 | 완료 | v1 success gate 4/9 |
| Claim-first 가설 | 잠정 지지 | E1이 E0보다 높은 F1, 낮은 critical error |
| Selective-LLM 효과 | 미입증 | v1 E3 교정이 모두 NeedsReview |
| LF 생성 가능성 | 확인 | v2.1에서 active LF 6개 |
| LF 운영 효용 | 미확보 | v2.1은 error 악화, v2.2는 효용 0 |
| Modality safe policy | 일부 확인 | 위험 package 차단으로 error 악화 방지 |
| Neo4j CSV·Cypher 생성 | 완료 | 정적 validation PASS |
| Neo4j runtime 적재 | 미완료 | Docker socket 권한 부족 |
| 인간 gold 평가 | 미수행 | 현재 가장 큰 연구 제약 |

요약하면 연구 코드, 실험 산출물, 재현 절차, 가설별 파일럿은 완료했다. 하지만 인간 gold와 새 normative/conditional 데이터가 없어 최종 방법론으로 확정할 수는 없다.

---

## 15. 현재 가장 중요한 문제

### 15.1 인간 gold가 없다

현재 모든 정확도는 LLM-Silver와의 일치도다. LLM-Silver 자체가 틀린 경우 시스템이 올바른 해석을 해도 오답으로 평가될 수 있다.

따라서 현재 결과로 다음을 주장하면 안 된다.

- 인간 전문가 기준 절대 정확도가 0.93이다.
- E1이 실제로 93.1% 정확하다.

정확한 표현은 다음이다.

- E1의 Claim F1이 LLM-Silver 기준 0.9310이었다.

### 15.2 Reference 합의율이 낮다

- A/B agreement 38.33%
- 최종 resolved coverage 60%
- Challenge 40%

즉, 평가 대상이 크게 줄어들었고 평가 편향이 생길 수 있다.

### 15.3 같은 model family의 오류 상관

A/B/C가 모두 같은 low-cost model snapshot을 사용했다. Prompt와 call이 달라도 모델 자체의 편향은 공유할 수 있다.

### 15.4 Modality label의 비일관성

같은 descriptive 문장을 어떤 주석은 `NONE`, 다른 주석은 `DESCRIPTIVE`로 표시했다. `경우가/경우에는`과 같은 표현은 DescriptiveFact type에서 비교적 일치했지만 modality는 두 값으로 나뉘었다.

이 문제는 LF 정확도가 아니라 annotation guideline 문제일 수 있다. `NONE`과 `DESCRIPTIVE`의 경계를 먼저 명확히 정의해야 한다.

### 15.5 재사용 규칙이 일부 쉬운 필드에 치우쳐져 있다

v2.1의 활성 LF에는 `POSITIVE polarity`, `FACTUAL family` 같이 비교적 쉬운 필드가 포함되었다. 이런 LF는 test precision을 높일 수 있지만 운영상 가장 필요한 MUST/MUST_NOT, 조건 범위, negation을 해결하지 못할 수 있다.

### 15.6 데이터 고갈과 adaptive reuse

현재까지 서로 겹치지 않게 선정한 evidence는 다음과 같다.

| 실험 | 선정 evidence | 이전 실험과 중복 |
|---|---:|---:|
| v1 | 180 | 0 |
| LF v2 | 210 | 0 |
| LF v2.1 | 120 | 0 |
| LF v2.2 | 100 | 0 |
| 총 unique selected | 610 | 0 |

원문 1,366건 중 756건이 evidence ID 기준으로 남아 있다. 하지만 현재 family heuristic 기준 남은 분포는 다음과 같다.

- descriptive: 665
- evaluation: 59
- discourse: 30
- procedure: 2
- normative: 0
- conditional: 0
- definition: 0

즉, 전체 행은 남아 있지만 modality LF 실험에 필요한 의무·금지·조건 표본은 사실상 소진되었다. 같은 파일을 계속 재분할하면 엄격한 fresh test를 만들 수 없다.

### 15.7 Graph F1 0의 문제

모든 시스템의 graph F1이 0으로 나왔다. 이는 모든 graph가 완전히 틀렸다는 뜻이 아니다.

현 지표는 다음이 정확히 같아야 match로 계산했다.

- evidence ID
- normalized predicate string
- promotion target

의미가 같아도 predicate 문자열이 다르면 오답이 되어 지표가 과도하게 엄격했다. 다음 실험에서는 ontology-aware relation mapping을 사전 고정해야 한다.

### 15.8 Neo4j runtime이 검증되지 않았다

파일과 정적 연결 구조는 검증했지만 실제 Neo4j 서버에서 constraint, import, query를 실행하지 못했다. 최종 보고에서 `Neo4j 적재 완료`라고 표현하면 안 된다.

---

## 16. 현재 결과로 주장할 수 있는 것과 없는 것

### 16.1 주장할 수 있는 것

1. 이 데이터와 LLM-Silver 기준에서 E1 Claim-first가 E0 direct triple보다 높은 Claim F1과 낮은 critical error rate를 보였다.
2. Source span, Claim, Assertion, operational relation을 연결하는 provenance 구조를 구현했다.
3. Field-level LF를 induction·validation·fresh test로 나누어 생성·검증할 수 있다는 가능성을 확인했다.
4. Safe-abstain 정책으로 검증되지 않은 modality package의 자동 적용을 막을 수 있다.

### 16.2 아직 주장할 수 없는 것

1. E1의 인간 전문가 기준 정확도가 93.1%라고 주장할 수 없다.
2. LF가 일반적으로 Full-LLM을 대체할 수 있다고 주장할 수 없다.
3. 다른 문서·도메인에도 LF가 재사용된다고 주장할 수 없다.
4. Neo4j 실제 적재와 query 성능이 검증되었다고 주장할 수 없다.
5. 18.75% LLM 후보 감소가 자연 문서 분포에서도 재현된다고 주장할 수 없다.

---

## 17. 다음 정식 실험에 필요한 방법

### 17.1 새 데이터

현 자이제 문서만으로는 새 normative/conditional test를 만들 수 없다. 다음을 포함한 별도 문서가 필요하다.

- 명시적 의무
- 금지·부정
- 조건·예외
- 권고
- 예시·질문·인용
- 표·수식·평가

### 17.2 인간 gold 주석

최소한 작은 blind human subset을 만들어야 한다.

권장 절차는 다음과 같다.

1. 두 명 이상의 주석자가 LLM 결과를 보지 않고 독립 주석한다.
2. Disagreement을 인간 adjudicator가 해소한다.
3. Modality guideline에 `NONE` vs `DESCRIPTIVE`, MUST vs SHOULD, descriptive conditional vs rule conditional의 경계를 예시와 함께 적는다.
4. 인간 gold로 LLM-Silver의 정확도와 편향을 먼저 검증한다.

### 17.3 사전 등록할 사항

새 test를 보기 전에 다음을 고정해야 한다.

- schema
- Claim alignment 방법
- LF candidate pattern
- validation precision/support threshold
- safe-abstain 기준
- promotion policy
- success gate
- model ID·prompt version
- token/cost cap

### 17.4 권장 분할

예시로 다음과 같은 독립 분할이 필요하다.

| Split | 용도 |
|---|---|
| Induction | LF 후보 생성 |
| Validation | LF precision/support·threshold 판정 |
| Fresh locked test | 최종 효과 측정 |
| Human audit subset | LLM-Silver 유효성 검증 |

섹션, 표, 목록, 중복 cluster 단위로 누출을 차단해야 한다.

### 17.5 다음 시스템 비교

1. E0 Direct Triple
2. E1 Full-LLM Claim-first
3. E2 No-LLM
4. E4 Field LF
5. E4-safe Modality package + abstain

다음 실험에서는 단순 F1뿐 아니라 다음을 함께 비교해야 한다.

- critical errors·absolute count
- LLM call·token·cost
- LF coverage·precision·conflict rate
- abstain rate
- human gold 기준 성능
- Neo4j provenance·query 정답률

### 17.6 Neo4j runtime

- 실제 Neo4j 인스턴스 준비
- constraints 적용
- idempotent import 2회 실행
- duplicate 노드·관계 검사
- provenance query
- competency query 10개 실행
- query 결과와 원문 evidence 연결 검증

---

## 18. API 사용과 비용

| 실험 | Calls | Input tokens | Output tokens | 추정 비용 USD |
|---|---:|---:|---:|---:|
| v1 파일럿 | 79 | 247,006 | 183,601 | 0.154424 |
| LF v2 중단 실험 | 35 | 102,424 | 65,491 | 0.054658 |
| LF v2.1 | 43 | 124,026 | 77,566 | 0.065144 |
| LF v2.2 | 37 | 106,662 | 61,722 | 0.053033 |
| **전체** | **194** | **580,118** | **388,380** | **0.327259** |

v1은 B 주석 출력 절단 2회의 추정 사용량을 포함한다. LF v2는 중단되었지만 성공한 API response cache 35개의 usage를 합산했다.

최종 산출물 재생성은 response cache를 사용했으므로 재실행 시 추가 model call이 없었다. Cache replay는 최초 실험 사용량을 교체하지 않으며, 최초 호출 usage를 보고한다.

API key는 환경변수에서만 읽었고 코드·로그·실험 산출물에 저장하지 않았다.

---

## 19. 재현성 및 주요 산출물

### 19.1 실행 코드

- `trace_ol_pilot_v1/run_pilot.py`
- `trace_ol_pilot_v1/pilot_lib.py`
- `trace_ol_pilot_v1/lf_reuse_v2/run_lf_reuse_v2.py`
- `trace_ol_pilot_v1/lf_reuse_v2/run_lf_reuse_v21.py`
- `trace_ol_pilot_v1/lf_reuse_v2/run_lf_reuse_v22.py`

### 19.2 v1 주요 파일

- `run_summary.json`
- `pilot_manifest.csv`
- `sampling_audit.json`
- `b2_lock_manifest.json`
- `reference/reference_annotations.jsonl`
- `reference/challenge_set.jsonl`
- `metrics_reference.json`
- `metrics_claim.json`
- `critical_errors.csv`
- `success_gates.json`
- `cost_ledger.csv`
- `neo4j/`

### 19.3 LF v2.1 주요 파일

- `lf_reuse_v2/runs/lf_reuse_v21_20260710/run_summary.json`
- `lf_reuse_v2/runs/lf_reuse_v21_20260710/lf/active_rules.json`
- `lf_reuse_v2/runs/lf_reuse_v21_20260710/lf/fresh_test_applications.jsonl`
- `lf_reuse_v2/runs/lf_reuse_v21_20260710/lf_reuse_v21_report.md`

### 19.4 LF v2.2 주요 파일

- `lf_reuse_v2/runs/lf_reuse_v22_20260711/run_summary.json`
- `lf_reuse_v2/runs/lf_reuse_v22_20260711/lf/package_registry.json`
- `lf_reuse_v2/runs/lf_reuse_v22_20260711/lf/active_packages.json`
- `lf_reuse_v2/runs/lf_reuse_v22_20260711/lf_reuse_v22_report.md`

### 19.5 검증한 항목

- JSON·JSONL parsing
- manifest cardinality·ID uniqueness
- split count
- prior evidence overlap
- validation/test group overlap
- lock hash
- source span exact match
- Atomic Claim 허용 필드
- Neo4j CSV endpoint·ID uniqueness
- token·call·cost ledger
- API key 문자열 미저장

---

## 20. 교수님께 보고할 때의 핵심 순서

### 20.1 1단계: 문제

> 문장에서 바로 triple을 만들면 의무, 부정, 조건, 예시 여부가 손실될 수 있습니다.

### 20.2 2단계: 제안 방법

> 그래서 원문 근거와 modality, polarity, condition, promotion decision을 포함한 Atomic Claim을 먼저 만든 뒤 그래프로 전환했습니다.

### 20.3 3단계: 실험

> Direct Triple E0, Full-LLM Claim-first E1, No-LLM E2, Selective-LLM E3, LF 재사용 E4를 locked test에서 비교했습니다.

### 20.4 4단계: 주요 결과

> LLM-Silver 기준으로 E1은 E0보다 Claim F1이 높고 critical error가 낮았습니다. LF는 v2.1에서 6개를 만들어 F1을 높였지만 modality 오류가 소폭 늘었습니다. v2.2에서 위험한 패키지를 차단해 오류 악화는 막았지만 추가 효용은 없었습니다.

### 20.5 5단계: 현재 문제

> 인간 gold가 없고, LLM reference의 Challenge가 많으며, 현 문서의 미사용 의무·조건 표본이 소진되었습니다. 따라서 새 문서와 인간 주석으로 다시 검증해야 합니다.

---

## 21. 최종 결론

본 파일럿은 Claim-first 방법의 연구 가능성과 provenance 기반 Neo4j 변환 구조를 확인했다. 또한 LF를 생성·검증·재사용하는 파이프라인을 구현하고 fresh test에서 일부 효과를 확인했다.

하지만 현재 결과는 인간 gold가 아닌 LLM-Silver 기준이며, reference 해소율과 modality 일관성이 부족하다. v2.1의 LF는 성능을 높였지만 critical error를 소폭 악화시켰고, v2.2의 safe policy는 안전성을 복구했지만 성능과 LLM 비용을 개선하지 못했다.

따라서 현재 단계의 정확한 결론은 다음과 같다.

> **Claim-first와 원문 추적 그래프의 가능성은 확인했고, 재사용 LF를 만드는 것에도 성공했다. 그러나 인간 gold, 새 normative/conditional 데이터, modality guideline, ontology-aware graph metric, Neo4j runtime 검증을 보완하기 전에는 최종 방법론이나 운영 시스템으로 확정할 수 없다.**
