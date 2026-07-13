# 자이제 LLM API 후속 실험 결과 보고서

## 1. 최종 판정

**`REVISE`**

Gate 0의 데이터·split 무결성은 유지됐지만, LLM-Derived Reference(LDR)의 품질을 검증하는 Gate 1L이 초기 PILOT과 1회 수정 후 fresh re-pilot에서 모두 실패했다.

따라서 현재 실험 ID에서는 다음을 진행하지 않았다.

- LDR-INDUCTION 100건과 LDR-VALIDATION 80건 생성
- E0∼E5 잠정 성능 비교
- TEST-NATURAL 140건과 TEST-CHALLENGE 60건 LDR 생성
- TEST 평가·온톨로지 귀납·Neo4j runtime 검증

이는 기술적 중단이 아니라, 후속 실험설계서가 정한 중단 규칙을 적용한 결과다.

---

## 2. 실험 목적

인간 Gold를 기다리지 않고 다중 LLM의 독립 주석·불일치 조정·근거 검증을 결합해 잠정 기준셋 LDR을 만들 수 있는지 검증했다.

이 단계의 수치는 실제 정확도가 아니다. 다음을 측정한다.

- 다른 LLM annotator가 같은 Claim을 만드는가?
- 같은 모델을 다시 호출했을 때 결과가 재현되는가?
- Claim과 argument가 원문 exact quote에 근거하는가?
- 양태·부정·조건·담화·승격 판정이 안정적인가?
- adjudicator가 후보 순서가 바뀌어도 같은 결론을 내는가?

---

## 3. 고정한 데이터

Phase 0 결과를 다시 만들지 않고 그대로 사용했다.

| 항목 | 값 |
|---|---:|
| Evidence | 1,366 |
| Leakage group | 168 |
| INDUCTION | 681 |
| VALIDATION | 272 |
| TEST_NATURAL | 275 |
| TEST_CHALLENGE_POOL | 138 |
| 기존 PILOT | 40 |
| fresh re-pilot | 20 |
| PILOT–re-pilot 중복 | 0 |
| TEST reference 생성·열람 | 0 |

주 입력은 설계서 binary hash와 일치하는 `legacy/자이제_1.xlsx`이다.

---

## 4. 사용한 LDR 방법

### 4.1 독립 Annotator

| 역할 | Model snapshot | 방법 |
|---|---|---|
| Annotator A | `gpt-4o-mini-2024-07-18` | domain-first, high-recall |
| Annotator B | `gpt-4.1-mini-2025-04-14` | ontology-first, conservative |
| Blind adjudicator | `gpt-4.1-2025-04-14` | A/B 익명화, 순서 무작위 |
| Grounding verifier | `gpt-4o-2024-08-06` | 최종 Claim을 반증 관점에서 검사 |

A와 B는 서로의 결과를 보지 않고 독립적으로 주석했다. 동일 모델·prompt의 반복 안정성을 계산하기 위해 역할별로 2회씩 호출했다.

### 4.2 Claim alignment

A/B Claim은 다음 가중치를 사용한 최대 가중 bipartite matching으로 정렬했다.

| 정렬 신호 | 가중치 |
|---|---:|
| Claim quote span overlap | 0.45 |
| family/type | 0.20 |
| predicate | 0.10 |
| argument span overlap | 0.10 |
| modality·polarity·condition·promotion | 0.15 |

매칭 threshold는 0.55로 잠권다.

### 4.3 Blind adjudication

A/B의 Claim 수, quote, argument, label 또는 핵심 필드 중 하나라도 다른 bundle을 adjudication했다.

- `ACCEPT_X`
- `ACCEPT_Y`
- `MERGE_SUPPORTED_FIELDS`
- `REJECT_BOTH`
- `UNDERDETERMINED`

후보 순서 편향을 검사하기 위해 불일치 중 10%를 X/Y 순서를 바꿔 다시 판정했다.

### 4.4 Grounding verification

최종 후보 Claim 전수에 대해 다음을 검사했다.

- exact quote
- Claim·argument support
- modality·polarity
- condition·exception
- scope overgeneralization
- example-to-rule contamination
- number·unit
- process direction

최종 상태는 `CONSENSUS_CORE`, `ADJUDICATED`, `UNDERDETERMINED`, `QUARANTINED`으로 분류했다.

---

## 5. 첫 번째 PILOT v1 결과

| 항목 | 결과 |
|---|---:|
| Evidence | 40 |
| A/B 불일치 bundle | 40 |
| `CONSENSUS_CORE` | 0 |
| `ADJUDICATED` | 21 |
| `QUARANTINED` | 19 |
| Gate PASS metric | 5/20 |
| Gate 1L | **FAIL** |

주요 수치:

| Metric | v1 | 최소 기준 |
|---|---:|---:|
| Claim span F1 | 0.5212 | 0.80 |
| Argument span F1 | 0.0631 | 0.78 |
| Claim family alpha | -0.0007 | 0.67 |
| Claim type alpha | 0.0174 | 0.67 |
| Modality alpha | 0.0028 | 0.75 |
| Polarity alpha | -0.3308 | 0.80 |
| Promotion alpha | -0.0571 | 0.75 |
| Critical-field IMS | 0.7125 | 0.90 |
| Position-swap consistency | 0.5000 | 0.90 |
| High-risk verifier ENTAILED | 0.4898 | 0.95 |
| Quarantine rate | 0.4750 | 0.05 이하 |

v1 원본 metric의 `accepted_claim_exact_quote_validity=0.7143`은 Claim quote와 argument quote를 함께 검사한 구현이었다. 동일한 claim-only 정의로 산출한 값은 **0.7937**이다. 원본 metric은 덮어쓰지 않고 이 차이를 기록했다.

---

## 6. 1회 수정과 fresh re-pilot v2

PILOT v1 결과만 분석해 설계서가 허용한 유일한 prompt/schema 수정을 적용했다.

수정 내용:

1. 모든 quote를 하나의 연속 exact substring으로 제한
2. A/B에 공통 family 판정 순서 제공
3. argument role를 12개 허용 목록으로 제한
4. modality·polarity·discourse promotion 규칙 명시
5. adjudicator의 quote·field 재작성 금지
6. verifier에서 해당 없는 검사는 `true`로 판정하도록 명시
7. annotation role을 JSON schema의 단일 enum으로 고정

fresh re-pilot은 기존 PILOT과 겹치지 않는 INDUCTION 20건으로 실행했다.

| 항목 | 결과 |
|---|---:|
| Evidence | 20 |
| 기존 PILOT 중복 | 0 |
| A/B 불일치 bundle | 20 |
| `CONSENSUS_CORE` | 0 |
| `ADJUDICATED` | 14 |
| `QUARANTINED` | 6 |
| Gate PASS metric | 5/20 |
| Gate 1L | **FAIL** |

| Metric | v1 | v2 | v2 기준 |
|---|---:|---:|---:|
| Claim-only exact quote validity | 0.7937 | 0.8500 | 1.00 |
| Evidence/bundle consistency | 0.8313 | 0.8625 | 1.00 |
| Claim span F1 | 0.5212 | 0.6297 | 0.80 |
| Argument span F1 | 0.0631 | 0.3232 | 0.78 |
| Claim family alpha | -0.0007 | -0.0606 | 0.67 |
| Claim type alpha | 0.0174 | -0.0114 | 0.67 |
| Modality alpha | 0.0028 | -0.1872 | 0.75 |
| Polarity alpha | -0.3308 | -0.5318 | 0.80 |
| Promotion alpha | -0.0571 | -0.0658 | 0.75 |
| Critical-field IMS | 0.7125 | 0.6206 | 0.90 |
| Position-swap consistency | 0.5000 | 0.5000 | 0.90 |
| High-risk verifier ENTAILED | 0.4898 | 0.5833 | 0.95 |
| Quarantine rate | 0.4750 | 0.3000 | 0.05 이하 |

quote·span·quarantine은 개선됐지만 핵심 label 합의와 반복 안정성은 개선되지 않았다.

---

## 7. 실패 원인

### 7.1 Claim 후보 집합 자체가 다름

v2 1차 출력에서 A는 28개, B는 19개 Claim을 생성했다. 같은 라벨을 고르기 전에 무엇을 하나의 Claim으로 보는지부터 달랐다.

### 7.2 복합 작업을 한 번에 판정함

현재 prompt는 Claim boundary, family, type, modality, polarity, argument, promotion을 한 번에 생성하게 한다. 경계 판정 하나가 다르면 나머지 categorical agreement도 함께 붕괴한다.

### 7.3 Ontology-first B의 반복 안정성이 낮음

v2의 B critical-field exact agreement는 0.4458, Claim set F1은 0.6957이었다. 낮은 A/B 합의가 단순히 모델 계열 다양성 때문만은 아니며, B 자체의 반복 불안정성이 크게 기여했다.

### 7.4 Adjudicator position bias

v1·v2 모두 position-swap consistency가 0.50이었다. 후보 X/Y 순서를 바꿘을 때 절반에서 최종 Claim 집합이 바뀌었다. 현 adjudicator를 잠정 정답 조정자로 신뢰하기 어렵다.

### 7.5 근거 정확성은 개선됐지만 충분하지 않음

v2 exact quote validity는 0.85였다. 이 실험은 승인 Claim의 exact quote 1.00을 필수로 하므로 0.85는 운영 기준으로는 부족하다.

---

## 8. API 사용량과 비용

Reference 생성 비용만 포함한다. E0∼E5 system 비용은 발생하지 않았다.

| Run | Calls | Input tokens | Output tokens | 추정 비용 |
|---|---:|---:|---:|---:|
| PILOT v1 | 49 | 196,186 | 58,552 | $0.448288 |
| fresh re-pilot v2 | 25 | 115,951 | 30,931 | $0.235937 |
| **합계** | **74** | **312,137** | **89,483** | **$0.684225** |

- API failed attempt: 0
- Cache replay: 0
- TEST reference call: 0
- API key 저장: 0

비용은 사전등록 단가로 계산한 추정치이며 실제 청구액과 차이가 있을 수 있다.

---

## 9. 현재 주장할 수 있는 것

1. Phase 0 split·membership 잠금을 깨지 않고 다중 snapshot LDR PILOT을 재현 가능한 형태로 실행했다.
2. Structured Outputs, raw response, token usage, prompt/schema hash, model snapshot, exact quote 재검증 파이프라인이 작동했다.
3. quote 제약 강화로 span·argument·quarantine 지표는 일부 개선됐다.
4. 현 A/B/adjudicator 구성은 LDR 기준셋으로 사용하기에 합의·안정성·순서 독립성이 부족하다.

현재 주장할 수 없는 것:

- E1 Claim-first가 E0 direct triple보다 우수하다.
- E4가 E5에 비열등하면서 토큰을 줄인다.
- 온톨로지 품질·CQ·Neo4j runtime 기준을 통과했다.
- 실제 정확도 또는 전문가 수준의 품질을 달성했다.

---

## 10. 다음 실험은 새 ID로 시작해야 한다

현 설계서의 1회 수정 횟수를 모두 사용했다. 추가 수정은 현 run에 덧붙이지 말고 새 experiment ID와 새 induction sample로 시작해야 한다.

권장 변경:

1. **2단계 reference**: 먼저 Claim quote/boundary 후보만 독립 확정하고, 잠긴 경계에 family·type·modality를 별도 판정한다.
2. **자유 quote 생성 금지**: 프로그램이 문장·절 후보 ID를 먼저 만들고 LLM은 ID만 선택한다.
3. **Field-level adjudication**: Claim 전체를 다시 작성하지 말고 불일치 필드만 선택한다.
4. **Swap audit 확대**: 10% 표본이 아니라 PILOT 불일치 전수에 순서 swap을 적용한다.
5. **다른 공급자 또는 인간 소규모 감사**: high-risk Claim 20∼40건을 외부 기준으로 확인한다.
6. **간단한 라벨 체계**: 필드별 `UNDERDETERMINED`를 허용하고 family/type 경계 예시를 추가한다.

---

## 11. 주요 산출물

### 사전등록

- `preregistration/amendment_llm_reference_v1.md`
- `preregistration/model_policy_v1.yaml`
- `preregistration/api_policy_v1.yaml`
- `preregistration/gate1l_thresholds.yaml`
- `preregistration/prompt_revision_v2.md`

### v1

- `runs/ldr_pilot_20260711_v1/reports/gate1l_metrics.json`
- `runs/ldr_pilot_20260711_v1/reports/gate1l_gate.json`
- `runs/ldr_pilot_20260711_v1/reference/llm/pilot_ldr.jsonl`
- `runs/ldr_pilot_20260711_v1/cost/reference/summary.json`

### v2

- `annotation/llm_reference/repilot_v2/repilot_lock.json`
- `runs/ldr_repilot_20260711_v2/reports/gate1l_metrics.json`
- `runs/ldr_repilot_20260711_v2/reports/gate1l_gate.json`
- `runs/ldr_repilot_20260711_v2/reference/llm/pilot_ldr.jsonl`
- `runs/ldr_repilot_20260711_v2/cost/reference/summary.json`

---

## 12. 결론

LLM API를 이용한 다중 역할 주석·adjudication·grounding verification 파이프라인은 기술적으로 실행됐다. 그러나 잠정 기준셋이 되기 위한 모델 간 합의, 반복 안정성, exact grounding, 순서 독립성 기준을 만족하지 못했다.

> **따라서 현 LDR로 E0∼E5를 평가하면 시스템 품질보다 불안정한 reference와의 일치도를 측정하게 된다. 현 실험은 `REVISE`로 종료하고, Claim boundary 확정과 field 판정을 분리한 새 실험으로 재설계해야 한다.**
