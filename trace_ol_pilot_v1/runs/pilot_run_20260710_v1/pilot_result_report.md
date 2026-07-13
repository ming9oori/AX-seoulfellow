# TRACE-OL 자이제 파일럿 실험 결과

## 실행 개요

- 입력: `자이제_1.xlsx` (180건 표본 / 전체 1,366건)
- 분할: CAL 60 / B1 60 / B2_LOCKED 60
- Reference: Silver-A 69, Silver-B 39, Challenge 72
- API: 79회, input 247,006 tokens, output 183,601 tokens, 추정 $0.1544
- Reference 성격: 동일 low-cost model snapshot의 별도 prompt/call에 의한 pseudo-independent LLM-Silver; human gold가 아님

## 시스템 비교

| 시스템 | Claim F1 | Family macro-F1 | Graph F1 | Critical error rate |
|---|---:|---:|---:|---:|
| E0_direct_triple | 0.7843 | 0.2745 | 0.0000 | 0.9000 |
| E1_full_llm | 0.9310 | 0.4447 | 0.0000 | 0.4074 |
| E2_no_llm | 0.5902 | 0.2611 | 0.0000 | 0.5556 |
| E4_selective_distill | 0.5902 | 0.2611 | 0.0000 | 0.5556 |
| E2_flat_ablation_subset | 0.5217 | 0.1667 | 0.0000 | 0.6667 |

## 성공 게이트

- [ ] source_span_validity_ge_0_98
- [ ] silver_resolved_coverage_ge_0_80
- [ ] challenge_rate_le_0_20
- [x] claim_first_critical_error_reduction_ge_0_30
- [ ] e4_vs_e1_macro_f1_gap_le_0_05
- [x] e4_vs_e1_token_ratio_le_0_40
- [ ] distillation_call_reduction_ge_0_20
- [x] provenance_path_coverage_eq_1
- [x] competency_queries_ge_8_of_10

## Neo4j

- 노드/관계 내보내기: Claim 238, Concept 31, Assertion 52, Relationship 438
- 정적 무결성 검사: PASS; provenance coverage 1.0000
- Competency query: 8/10
- 실제 Neo4j DB 로드: NOT_RUN: Docker daemon socket permission denied

## 해석 제약

1. 성능 수치는 인간 gold가 아닌 TRACE-LLM-Silver 대비 일치도이다.
2. Challenge는 primary metric에서 제외했다.
3. Neo4j runtime이 없으면 CSV·Cypher·정적 무결성까지만 검증한 결과이다.
4. 최종 연구 보고 전에 blind human subset 검증이 필요하다.
