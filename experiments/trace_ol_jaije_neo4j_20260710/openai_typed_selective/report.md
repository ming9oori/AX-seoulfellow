# TRACE-OL OpenAI 선택 판정 결과

- Run ID: `run:20260710T020000Z:P1_TYPED_OPENAI:a9482ce`
- Model: `gpt-4o-mini-2024-07-18`
- 상태: **FAILED**
- API key 저장: **아니오**
- 반복 판정 완전 일치율: **93.33%**
- 실패 CQ: **CQ-07**

## 수량

| 항목 | 값 |
|---|---:|
| queue_source | typed_audit |
| selected_candidates | 30 |
| repeats | 3 |
| api_calls | 90 |
| completed_responses | 90 |
| schema_parsed_responses | 90 |
| valid_structured_responses | 90 |
| local_contract_guardrail_rejections | 0 |
| api_errors | 0 |
| unanimous_promotions | 26 |
| majority_rejections | 2 |
| remaining_needs_review | 2 |
| unanimous_candidate_decisions | 28 |
| accepted_claims_total | 39 |
| distilled_rule_candidates | 10 |
| adopted_distilled_rules | 0 |
| graph_nodes | 5065 |
| graph_relationships | 7369 |
| cq_passed | 11 |
| cq_total | 12 |
| regression_passed | 6 |
| regression_total | 6 |

## 반복 합의

| 결과 | 후보 수 |
|---|---:|
| llm_repeat_incomplete_or_disagreed | 2 |
| openai_majority_reject | 2 |
| openai_unanimous_accept_or_revise | 26 |

## 승격 정책

- 3회 모두 유효하고 accept/revise이며 의미 필드가 동일한 경우만 Accepted로 승격했다.
- 과반 reject는 Rejected, 나머지는 NeedsReview로 보존했다.
- 증류 규칙은 별도 validation split 정밀도를 측정할 수 없어 후보만 만들고 채택하지 않았다.
- human gold가 없으므로 precision/recall/F1은 여전히 산출하지 않았다.
