# CAPE-KG Paper Readiness Checklist

Generated: 2026-06-29T18:56:33.257649+00:00
Plan: `AX_EACL_submission_review_revised_plan.md`
Experiment: `experiments/cape_kg_eacl_20260627`

이 문서는 `paper_readiness_checklist.json`을 사람이 검토하기 쉬운 Markdown 표로 렌더링한 것입니다.
PASS는 자동 산출물이 존재하거나 실행이 끝났다는 뜻이며, PENDING은 human-gold 또는 human review 완료 전에는 논문 claim으로 사용할 수 없다는 뜻입니다.

## Summary

- Items: 18
- PASS: 10
- PENDING: 8
- Minimum-accept items: 11 / pending 4
- Strong-accept items: 7 / pending 4

## Minimum-Accept Checklist

| requirement | status | evidence |
| --- | --- | --- |
| 100+ chunk gold annotation | PENDING | human-gold validation: 0/120 completed chunks, 0 node/edge/evidence items, validation_errors=0 |
| 500+ gold node/edge/evidence item | PENDING | human-gold validation: 0 items; silver reference edges=900 |
| 2+ annotators and agreement | PENDING | two-annotator assignment package generated; human completion/adjudication pending |
| Priority-100 gold subset sampling ready | PASS | priority-100 sampling selected 100 chunks; candidate_edge_coverage=0.954735 (1371/1436), active_review_coverage=0.967033, high_impact_coverage=1.000000; not gold until two annotators, IAA, and adjudication are complete |
| B0/B1/B2 baseline completed | PASS | condition-specific actual B0/B1/B2/B4/B5 full runs exist; human-gold scoring pending |
| CAPE-KG proposed result completed | PENDING | actual proposed generation and silver-proxy scoring exist; human-gold evaluation pending |
| 3+ ablations completed | PASS | actual LLM ablations completed for 6 conditions: P_minus_CQ, P_minus_Evidence, P_minus_Procedural_schema, P_minus_Schema_retrieval, P_minus_Standard_bridge, P_minus_Validator |
| error analysis table | PASS | structured error analysis generated with claim scope, taxonomy, diagnostics, and human-gold follow-up |
| public benchmark/subset experiment | PASS | PAGED/Text2KGBench acquired, profiled, adapter subsets generated, and model subset evaluation generated |
| code/prompt/schema release plan | PASS | prompt/schema/reproducibility package generated |
| limitations section | PASS | limitations generated |

## Strong-Accept Checklist

| requirement | status | evidence |
| --- | --- | --- |
| 300-500 chunk gold annotation | PENDING | human-gold validation: 0/300 adjudicated chunks; optional package strong_resegmented_342_max18 has 342 review units |
| 1,500+ gold edge/evidence item | PENDING | human-gold validation: 0/1500 items; validation_errors=0 |
| PAGED/Text2KGBench cross experiment | PASS | PAGED/Text2KGBench acquired, profiled, adapter subsets generated, and model subset evaluation generated |
| EDC/SAC-KG/Taxonomy-RAG family baseline | PASS | B3/B4/B6-family artifacts are generated; SAC-KG is represented by a deterministic verifier/pruner approximation |
| NCS/PCF mapping downstream evaluation | PENDING | candidate/rerank diagnostics exist; expert-reviewed P@K/MRR/nDCG claims pending |
| active review efficiency evaluation | PENDING | silver/proxy active-review diagnostics exist; human effort timing and adjudicated outcome alignment pending |
| visualization/demo | PASS | KG viewer generated from current Layer 2 graph artifacts |

## Interpretation

- `B0/B1/B2 baseline`, `ablation`, `error analysis`, `public benchmark`, `release plan`, `limitations`는 자동 산출물 기준으로 준비되었습니다.
- `gold annotation`, `gold item count`, `IAA`, `CAPE-KG proposed human-gold evaluation`은 사람 검수와 adjudication 이후에만 완료로 바뀝니다.
- strong-accept 항목의 `1,500+ gold edge/evidence item`, mapping downstream, active-review efficiency 역시 사람 검수 전에는 논문 claim으로 사용할 수 없습니다.
- 이 체크리스트는 제출 가능성 감사용이며, silver/proxy diagnostic을 human-gold 성능으로 대체하지 않습니다.
