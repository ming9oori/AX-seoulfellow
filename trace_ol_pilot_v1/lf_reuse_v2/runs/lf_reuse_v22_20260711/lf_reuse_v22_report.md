# TRACE-OL modality-aware 재사용 규칙 실험 v2.2

## 실험 목적

v2.1은 LF로 Claim F1을 높였지만 modality 오류가 증가했다. v2.2는 claim family나 polarity 하나만 맞히는 규칙을 자동 적용하지 않고, claim type·modality·polarity·promotion이 함께 검증된 패키지만 적용했다. modality 패키지가 충돌하면 자동 교정을 포기하고 LLM 검토 대상으로 남겼다.

## 데이터

- 새 validation: 50건 중 26건 해결 (52.00%)
- 새 fresh test: 50건 중 33건 해결 (66.00%)
- 이전 v1·v2·v2.1 510건과 evidence 중복: 0건
- validation/test group 누출: 0건

이전 실험이 규칙 중심 문장을 대부분 사용해, 남은 미사용 데이터에는 명시적 의무 1건과 조건 cue 4건만 남았다. 따라서 이 실험은 안전 정책을 검증하지만 modality 일반화를 입증하기에는 표본이 부족하다.

## 활성 패키지

| 패키지 | type / modality / polarity | validation support | validation precision |
|---|---|---:|---:|
| `explicit_question` | Question / NONE / NONE | 5 | 1.0000 |

## fresh test 결과

- 패키지 precision: 1.0000
- 패키지 coverage: 0.1515

| 방법 | Claim F1 | Critical error rate |
|---|---:|---:|
| E2 기본 | 0.8788 | 0.2759 |
| E2 + safe LF package | 0.8788 | 0.2759 |

- LLM 검토 후보: 7개 → 7개
- 후보 감소율: 0.00%
- validation에서 차단한 패키지: 6개
- fresh test에서 차단 패키지가 발화했지만 자동 교정을 보류한 행: 6건
- 활성 패키지 간 runtime 충돌 abstain: 0건

## 성공 기준

- [x] active_safe_package_at_least_1
- [x] test_package_precision_ge_0_90
- [x] critical_error_rate_not_worse
- [x] claim_f1_not_worse
- [ ] llm_candidate_reduction_ge_0_20
- [x] no_prior_evidence_overlap
- [x] no_validation_test_group_leakage

최종 판정: **REVISE (6/7)**

## 해석

v2.2의 목적은 규칙 개수를 늘리는 것이 아니라, modality 근거가 부족한 규칙을 자동 적용하지 않아 critical error를 막는 것이다. 이 목표는 달성했지만, 통과한 질문 패키지는 E2가 이미 잘 처리하던 유형이어서 F1과 LLM 절감을 개선하지 못했다. 즉 **안전성은 회복했지만 추가 효용은 없었다.**
