# Gate 1L PILOT 결과

- Run: `ldr_pilot_20260711_v1`
- Gate 1L: **FAIL**
- API real calls: 49
- Input/output tokens: 196,186 / 58,552
- Estimated reference cost: $0.448288

이 수치는 시스템 실제 정확도가 아니라 다중 LLM 기준셋의 형식·합의·안정성·근거 품질 검사다.

## Reference status

| Status | Bundles |
|---|---:|
| CONSENSUS_CORE | 0 |
| ADJUDICATED | 21 |
| UNDERDETERMINED | 0 |
| QUARANTINED | 19 |

## Gate metrics

| Metric | Value | Threshold | PASS |
|---|---:|---:|---|
| accepted_json_schema_validity | 1.0000 | >= 1.00 | PASS |
| accepted_claim_exact_quote_validity | 0.7143 | >= 1.00 | FAIL |
| evidence_bundle_consistency | 0.8313 | >= 1.00 | FAIL |
| provenance_completeness | 1.0000 | >= 1.00 | PASS |
| raw_api_failure_rate | 0.0000 | <= 0.02 | PASS |
| claim_span_pairwise_f1 | 0.5212 | >= 0.80 | FAIL |
| argument_span_pairwise_f1 | 0.0631 | >= 0.78 | FAIL |
| claim_family_alpha | -0.0007 | >= 0.67 | FAIL |
| claim_type_alpha | 0.0174 | >= 0.67 | FAIL |
| modality_alpha | 0.0028 | >= 0.75 | FAIL |
| polarity_alpha | -0.3308 | >= 0.80 | FAIL |
| promotion_alpha | -0.0571 | >= 0.75 | FAIL |
| critical_field_ims | 0.7125 | >= 0.90 | FAIL |
| position_swap_consistency | 0.5000 | >= 0.90 | FAIL |
| high_risk_verifier_entailed | 0.4898 | >= 0.95 | FAIL |
| example_to_rule_contamination | 0.0000 | <= 0.02 | PASS |
| adjudicator_added_claim_ratio | 0.0000 | <= 0.05 | PASS |
| unresolved_underdetermined | 0.4750 | <= 0.15 | FAIL |
| high_risk_unresolved | 0.5102 | <= 0.10 | FAIL |
| quarantine_rate | 0.4750 | <= 0.05 | FAIL |

## Decision

Gate 1L 최소 기준을 모두 만족하지 못했다. TEST LDR은 생성하지 않고, PILOT 결과만 보고 prompt/guideline을 최대 1회 수정한 후 fresh INDUCTION 20건으로 re-pilot해야 한다.
