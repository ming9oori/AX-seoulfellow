# TRACE-OL LLM-Silver Pilot Result Report

- Run ID:
- Corpus hash:
- Pilot manifest hash:
- Schema version:
- Reference version:
- CAL/B1/B2 bundle counts:
- Model role and IDs:
- Prompt hashes:
- API hard cap:
- Actual calls/input tokens/output tokens/cost:

## 1. Reference quality

| Metric | CAL | B1 | B2 | Overall |
|---|---:|---:|---:|---:|
| JSON validity | | | | |
| Source-span validity | | | | |
| A–B claim existence F1 | | | | |
| Claim family agreement | | | | |
| Modality exact agreement | | | | |
| Polarity exact agreement | | | | |
| Condition span F1 | | | | |
| C adjudication rate | | | | |
| D adjudication rate | | | | |
| Silver-A coverage | | | | |
| Silver-B coverage | | | | |
| Challenge rate | | | | |

## 2. B2 main comparison

| System | Claim F1 | Family Macro-F1 | Fine Type Macro-F1 | Modality F1 | Promotion Macro-F1 | Graph F1 | Critical Error Rate | Calls | Tokens | Cost |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| E0 DirectTriple-LLM | N/A | N/A | N/A | N/A | N/A | | | | | |
| E1 ClaimFirst-FullLLM | | | | | | | | | | |
| E2 TRACE-NoLLM | | | | | | | | 0 | 0 | 0 |
| E4 Selective+Distill | | | | | | | | | | |
| E2-Flat ablation | | | | | | | | 0 | 0 | 0 |

## 3. Critical errors

| Error | E0 | E1 | E2 | E4 | Example evidence IDs |
|---|---:|---:|---:|---:|---|
| MUST/SHOULD/MAY confusion | | | | | |
| MUST_NOT or negation dropped | | | | | |
| Condition dropped | | | | | |
| Example/CounterExample/Question promoted | | | | | |
| Unsupported assertion | | | | | |
| False sense merge | | | | | |

## 4. Distillation

| Item | B1 before distill | B2 counterfactual before distill | B2 after distill |
|---|---:|---:|---:|
| Gate-selected candidates | | | |
| LLM-called candidates | | | |
| Auto-resolved by new LF | | | |
| LLM calls | | | |
| Critical errors from new LF | N/A | N/A | |

## 5. API ledger

| Role | Calls | Input tokens | Output tokens | Cache hits | Retries | Cost |
|---|---:|---:|---:|---:|---:|---:|
| Reference A | | | | | | |
| Reference B | | | | | | |
| Reference C | | | | | | |
| Adjudicator D | | | | | | |
| E0 | | | | | | |
| E1 | | | | | | |
| E3/E4 | | | | | | |
| Total | | | | | | |

## 6. Neo4j

| Item | Count/Rate | Pass criterion | Result |
|---|---:|---:|---|
| Documents | | | |
| Sections | | | |
| Evidence | | | |
| Claims | | | |
| Assertions | | | |
| Operational relationships | | | |
| Accepted assertions with evidence path | | 100% | |
| Orphan accepted claims | | 0 | |
| Constraint violations | | 0 | |
| CQ pass | | 8/10 | |

## 7. Competency queries

| CQ | Result summary | Evidence-linked | Pass/Fail |
|---|---|---|---|
| CQ1 단계별 산출물 | | | |
| CQ2 RFP와 의사결정 | | | |
| CQ3 MUST/MUST_NOT 규칙 | | | |
| CQ4 Capture Plan senses | | | |
| CQ5 경쟁자 분석 산출물 | | | |
| CQ6 BCM 평가 관측 | | | |
| CQ7 가치제안 수식 | | | |
| CQ8 discourse 비승격 | | | |
| CQ9 리스크와 완화 | | | |
| CQ10 NeedsReview | | | |

## 8. Error analysis

| Evidence ID | System | Silver | Prediction | Error cause | Proposed correction | Reusable LF candidate |
|---|---|---|---|---|---|---|
| | | | | | | |

## 9. Decision

- [ ] PROCEED — 전체 1,366개 확대
- [ ] REVISE — schema/prompt/LF 수정 및 새 locked test 필요
- [ ] NARROW — 지원 claim/promotion 범위 축소
- [ ] STOP — reference/provenance/cost 기준 미달

## 10. Interpretation limit

이 보고서의 성능은 전문가 Gold 정확도가 아니라 `TRACE-LLM-Silver-v0.1`과의 일치도다. 모든 Neo4j assertion은 human-reviewed=false로 표시한다.
