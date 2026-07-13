# CAPE-KG Claimable Main Table

Generated: 2026-06-29T18:55:33.389234+00:00
Overall claim status: `pending_human_gold_and_or_expert_review`

This table is intentionally conservative. Silver/proxy diagnostics are separated from claimable human-gold results.

| Result | Claimability | Primary metric | Current value | Evidence file | Blocker / note |
| --- | --- | --- | --- | --- | --- |
| Core extraction main result | pending_human | Human-gold edge/node/evidence F1 | not claimable yet | 04_evaluation/human_gold_metrics.json | 0/100 adjudicated chunks, 0/500 items, validation_errors=0 |
| Actual LLM run coverage | claimable_setup | Full conditions generated | B0/B1/B2/P=120 rows; 6 ablations | 06_release/claim_gate_report.json | generation coverage only; not final quality without human-gold scoring |
| Optional annotation expansion | claimable_setup | All available current-corpus chunks prepared for optional review | all_available=214, remaining_optional=94, strong_300_gap_without_split=86, resegmented=342, strong_300_gap_after_split=0 | 01_data/gold_annotation/annotation_expansion_manifest.json | optional package does not change the 11-file minimum paper gate; it is tracked separately for strong/optional claims |
| Priority-100 gold subset sampling | claimable_setup | Coverage of full-120 candidate edges, active-review chunks, and high-impact chunks | selected=100, candidate_edge_coverage=0.954735, active_review_coverage=0.967033, high_impact_coverage=1.0 | 06_release/gold_sampling_coverage_report.json | gold_sampling_coverage_ready_pending_human_review |
| CAPE-KG silver diagnostic | diagnostic_only | Silver edge/predicate/node/evidence F1 | edge=0.001786, predicate=0.048214, node=0.032597, evidence=0.065527 | 04_evaluation/actual_llm_silver_metrics.json | silver_proxy_not_human_gold |
| Qwen3 model scaling diagnostic | diagnostic_only | Proposed-method silver exact/predicate/evidence F1 across Qwen3-8B/14B/32B-AWQ | Qwen3-8B: exact=0.001786, predicate=0.048214, evidence=0.065527; Qwen3-14B: exact=0.001741, predicate=0.060078, evidence=0.060955; Qwen3-32B-AWQ: exact=0.003441, predicate=0.066237, evidence=0.054153 | 06_release/qwen3_model_scaling_report.json | qwen3_model_scaling_diagnostic_ready_not_human_gold; 32B-AWQ rows=480/480; not human-gold performance evidence |
| Evidence span granularity | diagnostic_only | Subject/object lexical char-span coverage; predicate sentence proxy coverage | subject_exact=0.232313, object_exact=0.551214, predicate_proxy=1.0 | 04_evaluation/evidence_span_granularity_metrics.json | predicate-token and final exactness claims require adjudicated human-gold spans |
| Predicate cue span diagnostic | diagnostic_only | Lexical predicate-cue span coverage | cue_spans=550/947, rate=0.580781, source_text_included=False | 04_evaluation/predicate_cue_span_metrics.json; outputs/06_triples/layer2_predicate_cue_spans.jsonl | automatic lexical diagnostic only; predicate-token correctness requires adjudicated human-gold spans |
| KG structural diagnostics | diagnostic_only | Ontology conformance, procedural consistency, CQ answerability | ontology=1.0, procedural=0.995283, cq=1.0 | 04_evaluation/structural_evaluation_metrics.json | kg_structural_diagnostic_not_human_gold |
| Structural gap worklist | claimable_setup | Review-checkpoint candidates and gateway branch gaps prepared for review | review_checkpoint_candidates=45, gateway_branch_gaps=4 | 04_evaluation/structural_gap_worklist_summary.json | does_not_change_minimum_11_file_paper_gate |
| Public benchmark adapter | auxiliary_claimable | PAGED/Text2KG subset metrics | PAGED n=100, best edge F1=0.4233; Text2KG n=200, best relation F1=0.6015; strong_cross_run=True | 08_public_benchmarks/public_benchmark_crosscheck_summary.json | auxiliary generalization evidence, not the Korean enterprise human-gold main result |
| NCS/PCF mapping downstream | pending_expert_review | Hit@5/P@5/MRR/nDCG@10/explanation quality for Layer2-to-NCS and Layer2-to-PCF candidates | complete_groups=0, pending_rows=220 | 04_evaluation/mapping_expert_metrics.json | expert review must complete Top-5 NCS/PCF candidate groups before downstream mapping claims |
| NCS-PCF crosswalk downstream | pending_expert_review | Expert accept rate, Hit@K, P@10, MRR, nDCG@10, utility, explanation quality for Layer2-bridged crosswalk candidates | candidates=220, source_tasks=22, completed_rows=0, pending_rows=220 | 04_evaluation/crosswalk_expert_metrics.json; 04_evaluation/ncs_pcf_crosswalk_summary.json | expert review must validate NCS-PCF crosswalk utility before bridge-support claims |
| Active-review pool design | claimable_setup | Three-arm review pool coverage and duplicate reduction | arm_assignments=300, unique_rows=204, duplicate_removed=96, reduction=0.32 | 04_evaluation/active_review_pool_overlap_summary.json | pool design only; efficiency claims require human timing/correction evidence |
| Active-review human-effort briefing | claimable_setup | Ordered review-navigation sheet for pooled active/uncertainty/random rows | briefing_rows=204, pooled_rows=204, claim_status=review_navigation_only_pending_human_effort | 06_release/active_review_human_effort_briefing.json; 05_review/active_review_human_effort_briefing.csv | review navigation only; efficiency claims require returned timing/correction evidence |
| Active-review ablation | diagnostic_only | P vs P-minus-active-review silver/proxy review-priority lift | ablation_rows=24 | 04_evaluation/active_review_ablation_metrics.json | human timing/correction evidence and adjudicated labels required before efficiency claims |
| Release/reproducibility package | claimable_setup | Release artifacts and public-safe bundle | PASS | 06_release/release_bundle_manifest.json | public-safe bundle excludes source text and internal review handoff files |
| Submission claim gate | not_ready | Conservative gate status | FAIL | 06_release/claim_gate_report.json | required_failures=4, warnings=0 |

## Interpretation

- `claimable`: can be used as a paper claim with the listed evidence.
- `claimable_setup`: supports reproducibility or experiment coverage, but is not a quality result.
- `auxiliary_claimable`: can support an auxiliary/public-benchmark claim, not the main Korean enterprise result.
- `diagnostic_only`: useful for debugging or motivation only.
- `pending_human` / `pending_expert_review`: blocked on human review before paper claims.
