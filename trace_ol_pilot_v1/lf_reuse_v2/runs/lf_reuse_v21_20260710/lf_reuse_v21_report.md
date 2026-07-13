# TRACE-OL 재사용 규칙 실험 v2.1

## 무엇을 바꾸었는가

v1은 조건문 6개만 LLM에 보내 교정 패턴을 얻지 못했다. v2는 여러 패턴을 수집했지만, 하나의 규칙이 family·type·modality·polarity·promotion을 모두 동시에 맞혀야 해서 통과 규칙이 0개였다.

v2.1은 이 항목을 필드별 작은 LF로 나누었다. 각 LF를 별도 validation에서 검증하고, 서로 충돌하지 않는 필드만 합쳐 사용했다.

## 데이터

- v2.1 validation: 60건 중 42건 해결 (70.00%)
- v2.1 fresh test: 60건 중 30건 해결 (50.00%)
- v1·v2 사용 evidence와 중복: 0건
- validation과 fresh test 사이 group 누출: 0건

## 활성화된 재사용 규칙

| 패턴 | 예측 필드 | validation support | validation precision |
|---|---|---:|---:|
| `family:descriptive` | polarity=POSITIVE | 6 | 1.0000 |
| `family:procedure` | claim_family=FACTUAL | 4 | 1.0000 |
| `seed:explicit_obligation` | polarity=POSITIVE | 4 | 1.0000 |
| `seed:observational_case` | claim_family=FACTUAL | 3 | 1.0000 |
| `seed:observational_case` | claim_type=DescriptiveFact | 3 | 1.0000 |
| `cue:process` | claim_family=FACTUAL | 7 | 0.8571 |

- 전체 LF 후보: 74개
- validation 통과: 9개
- 중복·상관 정리 후 최종 활성 LF: 6개
- fresh test LF precision: 0.8750
- fresh test LF coverage: 0.5333

## 성능

| 방법 | Claim F1 | Critical error rate |
|---|---:|---:|
| E2 기본 | 0.8571 | 0.7083 |
| E2 + 검증 LF | 0.9286 | 0.7308 |

## LLM 절감 가능성

- LF 적용 전 검토 후보: 16개
- LF 적용 후 검토 후보: 13개
- 후보 감소율: 18.75%

## 실험 비용

- 중단한 v2: 35 calls, 추정 USD 0.054658
- 완료한 v2.1: 43 calls, 추정 USD 0.065144
- 재사용 규칙 실험 전체: 78 calls, input 226,450, output 143,057 tokens, 추정 USD 0.119802

## 성공 기준

- [x] active_lf_at_least_1
- [x] fresh_test_rule_precision_ge_0_85
- [x] fresh_test_rule_coverage_ge_0_15
- [x] claim_f1_not_worse
- [ ] critical_error_rate_not_worse
- [ ] llm_candidate_reduction_ge_0_20
- [x] no_prior_evidence_overlap
- [x] no_validation_test_group_leakage

최종 판정: **REVISE (6/8)**

## 결국 어떤 의미인가

**재사용 규칙을 만드는 것에는 성공했다.** v1의 0개와 달리 v2.1에서는 validation을 통과한 최종 LF 6개가 만들어졌다. fresh test에서도 적용 16건 중 14건을 맞혀 precision 87.5%를 얻었고, Claim F1은 0.8571에서 0.9286으로 상승했다.

하지만 바로 운영에 적용할 단계는 아니다. LF 적용 후 추가로 정렬된 Claim에서 modality 불일치 2건이 더 드러나 critical error rate가 0.7083에서 0.7308로 소폭 증가했다. LLM 검토 후보도 16개에서 13개로 줄었지만 감소율 18.75%로 목표 20%에 조금 못 미쳤다.

따라서 현재 결론은 **"LF 생성과 재사용 가능성은 확인했지만, modality 전용 LF와 더 안전한 abstain 규칙을 보완한 후 다시 검증해야 한다"이다.**

## 제약

- reference는 인간 gold가 아닌 LLM-Silver이다.
- v2.1은 문서 내 재사용을 보는 `document_local` LF 실험이다. 다른 문서로의 일반화를 입증하지 않는다.
- family별 사례를 확보하기 위해 표적 표본을 사용했으므로 전체 문서의 자연 비율을 대표하지 않는다.
