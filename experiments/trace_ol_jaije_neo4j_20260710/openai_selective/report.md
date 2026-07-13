# TRACE-OL OpenAI 선택 판정 결과

- Run ID: `run:20260710T010000Z:P1_OPENAI:a9482ce`
- Model: `gpt-4o-mini-2024-07-18`
- 상태: **PASS_WITH_GUARDRAIL_REJECTIONS**
- API key 저장: **아니오**

## 수량

| 항목 | 값 |
|---|---:|
| selected_candidates | 30 |
| repeats | 3 |
| api_calls | 90 |
| completed_responses | 90 |
| schema_parsed_responses | 90 |
| valid_structured_responses | 75 |
| local_contract_guardrail_rejections | 15 |
| api_errors | 0 |
| unanimous_promotions | 23 |
| majority_rejections | 1 |
| remaining_needs_review | 6 |
| accepted_claims_total | 66 |
| distilled_rule_candidates | 13 |
| adopted_distilled_rules | 0 |
| graph_nodes | 5065 |
| graph_relationships | 7373 |
| cq_passed | 12 |
| cq_total | 12 |
| regression_passed | 6 |
| regression_total | 6 |

## 반복 합의

| 결과 | 후보 수 |
|---|---:|
| llm_repeat_incomplete_or_disagreed | 5 |
| openai_majority_reject | 1 |
| openai_unanimous_accept_but_semantic_revision_disagreed | 1 |
| openai_unanimous_accept_or_revise | 23 |

## 승격 정책

- 3회 모두 유효하고 accept/revise이며 의미 필드가 동일한 경우만 Accepted로 승격했다.
- 과반 reject는 Rejected, 나머지는 NeedsReview로 보존했다.
- 증류 규칙은 별도 validation split 정밀도를 측정할 수 없어 후보만 만들고 채택하지 않았다.
- human gold가 없으므로 precision/recall/F1은 여전히 산출하지 않았다.
