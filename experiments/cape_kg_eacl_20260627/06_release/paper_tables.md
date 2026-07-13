# CAPE-KG Paper Tables



Generated: 2026-06-29T18:55:33.510006+00:00



Tables marked by pending human gold or expert review are diagnostic only and should not be used as final paper claims.



## Dataset and Annotation Status

| Item | Value | Note |
| --- | --- | --- |
| Evaluation chunks | 120 | selected Korean bid/proposal chunks |
| Optional all-available annotation chunks | 214 | optional_expansion_ready_pending_human_review |
| Optional remaining annotation chunks | 94 | not part of the 11-file minimum paper gate |
| Optional strong resegmented review units | 342 | max 18 source sentences/unit; ready_pending_human_review |
| Silver nodes | 208 | current KG-derived reference |
| Silver edges | 900 | current KG-derived reference |
| Silver evidence anchors | 293 | current KG-derived reference |
| Adjudicated human-gold chunks | 0 | pending_human_adjudication |
| Human-gold items | 0 | nodes + edges + evidence |
| Mapping review rows | 220 | pending_expert_review |

## Gold Subset Sampling Coverage

| Status | Selected | Selected edges | Full-120 edges | Candidate coverage | Active coverage | High-impact coverage |
| --- | --- | --- | --- | --- | --- | --- |
| gold_sampling_coverage_ready_pending_human_review | 100 | 1371 | 1436 | 0.9547 | 0.9670 | 1.0000 |

## Actual LLM Silver Diagnostics

| Condition | Edge F1 | Predicate F1 | Node F1 | Evidence F1 | Parse errors | Repairs |
| --- | --- | --- | --- | --- | --- | --- |
| B0_plain_llm | 0.0000 | 0.0000 | 0.0350 | 0.0239 | 63 | 63 |
| B1_predicate_constrained | 0.0000 | 0.1416 | 0.0000 | 0.0291 | 63 | 63 |
| B2_current_project | 0.0000 | 0.0068 | 0.0215 | 0.0503 | 97 | 97 |
| B3_edc_style | 0.0000 | 0.0119 | 0.0196 | 0.0311 | 99 | 98 |
| B4_taxonomy_rag | 0.0000 | 0.0105 | 0.0300 | 0.0641 | 102 | 102 |
| B5_procedural_prompt | 0.0010 | 0.0096 | 0.0274 | 0.0603 | 96 | 96 |
| B6_sac_kg_verifier_pruner | 0.0017 | 0.0774 | 0.0564 | 0.1008 | 0 | 0 |
| P_cape_kg_actual | 0.0018 | 0.0482 | 0.0326 | 0.0655 | 113 | 113 |
| P_minus_CQ | 0.0000 | 0.0338 | 0.0285 | 0.0682 | 117 | 117 |
| P_minus_Evidence | 0.0009 | 0.0549 | 0.0297 | 0.0666 | 103 | 103 |
| P_minus_Procedural_schema | 0.0036 | 0.0976 | 0.0301 | 0.0687 | 107 | 107 |
| P_minus_Schema_retrieval | 0.0009 | 0.0730 | 0.0218 | 0.0598 | 109 | 109 |
| P_minus_Standard_bridge | 0.0009 | 0.0712 | 0.0213 | 0.0590 | 59 | 59 |
| P_minus_Validator | 0.0018 | 0.0456 | 0.0299 | 0.0659 | 110 | 110 |

## Model Scaling Core Silver Diagnostics

| Model | Condition | Rows | Edge F1 | Predicate F1 | Node F1 | Evidence F1 | Parse errors | Repairs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Qwen3-8B | B0_plain_llm | 120 | 0.0000 | 0.0000 | 0.0350 | 0.0239 | 63 | 63 |
| Qwen3-8B | B1_predicate_constrained | 120 | 0.0000 | 0.1416 | 0.0000 | 0.0291 | 63 | 63 |
| Qwen3-8B | B2_current_project | 120 | 0.0000 | 0.0068 | 0.0215 | 0.0503 | 97 | 97 |
| Qwen3-8B | P_cape_kg_actual | 120 | 0.0018 | 0.0482 | 0.0326 | 0.0655 | 113 | 113 |
| Qwen3-14B | B0_plain_llm | 120 | 0.0000 | 0.0000 | 0.0329 | 0.0259 | 68 | 68 |
| Qwen3-14B | B1_predicate_constrained | 120 | 0.0008 | 0.1105 | 0.0000 | 0.0246 | 75 | 75 |
| Qwen3-14B | B2_current_project | 120 | 0.0000 | 0.0079 | 0.0198 | 0.0394 | 102 | 102 |
| Qwen3-14B | P_cape_kg_actual | 120 | 0.0017 | 0.0601 | 0.0298 | 0.0610 | 113 | 113 |
| Qwen3-32B-AWQ | B0_plain_llm | 120 | 0.0000 | 0.0000 | 0.0377 | 0.0273 | 59 | 59 |
| Qwen3-32B-AWQ | B1_predicate_constrained | 120 | 0.0016 | 0.1161 | 0.0000 | 0.0224 | 63 | 63 |
| Qwen3-32B-AWQ | B2_current_project | 120 | 0.0000 | 0.0099 | 0.0194 | 0.0387 | 100 | 100 |
| Qwen3-32B-AWQ | P_cape_kg_actual | 120 | 0.0034 | 0.0662 | 0.0284 | 0.0542 | 113 | 113 |

## Human-Gold Metrics

| Condition/status | Edge/chunks | Node/items | Evidence EM | Ontology | Procedural | CQ |
| --- | --- | --- | --- | --- | --- | --- |
| pending_human_adjudication | 0 | 0 | metrics pending |

## Evidence Span Granularity Diagnostic

| Triples | Components | Subject exact | Object exact | Predicate proxy | Status |
| --- | --- | --- | --- | --- | --- |
| 947 | 2841 | 0.2323 | 0.5512 | 1.0000 | automatic_component_span_diagnostic_not_human_gold |

## Predicate Cue Span Diagnostic

| Triples | Cue spans | Missing cues | Cue rate | Chunk spans | Source text included | Status |
| --- | --- | --- | --- | --- | --- | --- |
| 947 | 550 | 397 | 0.5808 | 550 | False | automatic_predicate_cue_span_diagnostic_not_human_gold |

## KG Structural Diagnostics

| Status | Ontology | Domain/range errors | Evidence missing | Procedural | Cycles | CQ answerability |
| --- | --- | --- | --- | --- | --- | --- |
| kg_structural_diagnostic_not_human_gold | 1.0000 | 0 | 0 | 0.9953 | 0 | 1.0000 |

## Structural Gap Worklist

| Status | Review checkpoint candidates | Gateway branch gaps | Structural CQ | Human gate effect |
| --- | --- | --- | --- | --- |
| structural_gap_worklist_pending_human_review | 45 | 4 | 1.0000 | does_not_change_minimum_11_file_paper_gate |

## Public Subset Diagnostics

| Run | PAGED n | PAGED node F1 | PAGED edge F1 | Text2KG n | Relation F1 | Triple F1 |
| --- | --- | --- | --- | --- | --- | --- |
| public_qwen3_14b_subset_eval_summary.json | 10 | 0.1733 | 0.1446 | 20 | 0.2817 | 0.0200 |
| public_qwen3_8b_full_adapter_eval_summary.json | 100 | 0.2472 | 0.4233 | 200 | 0.6015 | 0.1736 |
| public_qwen3_8b_subset_eval_summary.json | 10 | 0.1608 | 0.1794 | 20 | 0.4500 | 0.0500 |
| public_qwen3_8b_subset_smoke_summary.json | 3 | 0.0000 | 0.1333 | 5 | 0.4000 | 0.0000 |

## Public Benchmark Cross-Check

| Runs | Strong run | Max PAGED n | Max Text2KG n | Best PAGED edge F1 | Best Text2KG relation F1 | Status |
| --- | --- | --- | --- | --- | --- | --- |
| 4 | True | 100 | 200 | 0.4233 | 0.6015 | public_adapter_model_runs_diagnostic_not_official_leaderboard |

## Mapping Expert Review

| Standard | Completed | Pending | Groups | Hit@5 | P@5 | MRR | nDCG@10 | Explanation | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| NCS | 0 | 110 | 0 | pending_expert_review | pending_expert_review | pending_expert_review | pending_expert_review | pending_expert_review | pending_expert_review |
| PCF | 0 | 110 | 0 | pending_expert_review | pending_expert_review | pending_expert_review | pending_expert_review | pending_expert_review | pending_expert_review |

## Layer2-bridged NCS-PCF Crosswalk Candidates

| Shared Layer2 tasks | All pairs | Candidate rows | Top-K per standard | Status |
| --- | --- | --- | --- | --- |
| 22 | 550 | 220 | 5 | candidate_only_pending_expert_review |

## Crosswalk Expert Review

| Candidates | Source tasks | Completed | Pending | Hit@5 | P@10 | MRR | Utility | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 220 | 22 | 0 | 220 | pending_crosswalk_expert_review | pending_crosswalk_expert_review | pending_crosswalk_expert_review | pending_crosswalk_expert_review | pending_crosswalk_expert_review |

## Active Review Prioritization Diagnostic

| Condition | Strategy | Budget | Errors | Precision@k | Recall@k | Lift | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| P_cape_kg_actual | active_priority | 10 | 6 | 0.6000 | 0.0347 | 0.9538 | silver_proxy_not_human_review_efficiency |
| P_cape_kg_actual | active_priority | 25 | 16 | 0.6400 | 0.0925 | 1.0173 | silver_proxy_not_human_review_efficiency |
| P_cape_kg_actual | active_priority | 55 | 36 | 0.6545 | 0.2081 | 1.0405 | silver_proxy_not_human_review_efficiency |
| P_cape_kg_actual | active_priority | 100 | 56 | 0.5600 | 0.3237 | 0.8902 | silver_proxy_not_human_review_efficiency |
| P_cape_kg_actual | uncertainty_only | 10 | 6 | 0.6000 | 0.0347 | 0.9538 | silver_proxy_not_human_review_efficiency |
| P_cape_kg_actual | uncertainty_only | 25 | 15 | 0.6000 | 0.0867 | 0.9538 | silver_proxy_not_human_review_efficiency |
| P_cape_kg_actual | uncertainty_only | 55 | 38 | 0.6909 | 0.2197 | 1.0983 | silver_proxy_not_human_review_efficiency |
| P_cape_kg_actual | uncertainty_only | 100 | 72 | 0.7200 | 0.4162 | 1.1445 | silver_proxy_not_human_review_efficiency |

## P minus Active Review Ablation Diagnostic

| Condition | Strategy | Budget | Errors | Precision@k | Recall@k | Lift | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| P_cape_kg_actual_with_active_review | active_priority | 25 | 16 | 0.6400 | 0.0925 | 1.0173 | silver_proxy_ablation_not_human_efficiency |
| P_minus_Active_review_random_expected | random_expected | 25 | 15.7273 | 0.6291 | 0.0909 | 1.0000 | silver_proxy_ablation_not_human_efficiency |
| P_minus_Active_review_uncertainty_only | uncertainty_only | 25 | 15 | 0.6000 | 0.0867 | 0.9538 | silver_proxy_ablation_not_human_efficiency |
| P_cape_kg_actual_with_active_review | active_priority | 55 | 36 | 0.6545 | 0.2081 | 1.0405 | silver_proxy_ablation_not_human_efficiency |
| P_minus_Active_review_random_expected | random_expected | 55 | 34.6000 | 0.6291 | 0.2000 | 1.0000 | silver_proxy_ablation_not_human_efficiency |
| P_minus_Active_review_uncertainty_only | uncertainty_only | 55 | 38 | 0.6909 | 0.2197 | 1.0983 | silver_proxy_ablation_not_human_efficiency |
| P_cape_kg_actual_with_active_review | active_priority | 100 | 56 | 0.5600 | 0.3237 | 0.8902 | silver_proxy_ablation_not_human_efficiency |
| P_minus_Active_review_random_expected | random_expected | 100 | 62.9091 | 0.6291 | 0.3636 | 1.0000 | silver_proxy_ablation_not_human_efficiency |
| P_minus_Active_review_uncertainty_only | uncertainty_only | 100 | 72 | 0.7200 | 0.4162 | 1.1445 | silver_proxy_ablation_not_human_efficiency |

## Active Review Human-Effort Handoff

| Arm | Budget | Assigned | Reviewed | Seconds | Corrections | High-impact | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| active_priority | 100 | 100 | 0 | 0 | 0 | 0 | pending_human_effort_timing |
| uncertainty_only | 100 | 100 | 0 | 0 | 0 | 0 | pending_human_effort_timing |
| random_control | 100 | 100 | 0 | 0 | 0 | 0 | pending_human_effort_timing |

## Active Review Pool Design

| Arm assignments | Unique rows | Duplicate removed | Reduction | Active rows | Uncertainty rows | Random rows | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 300 | 204 | 96 | 0.3200 | 100 | 100 | 100 | pool_design_diagnostic_not_human_effort_claim |

## Paired Bootstrap Silver Diagnostics

| Baseline | Metric | P mean | Base mean | Delta | 95% CI | p approx | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| B0_plain_llm | predicate_f1 | 0.0658 | 0.0000 | 0.0658 | [0.041384, 0.094497] | 0.0000 | silver_proxy_not_human_gold |
| B0_plain_llm | node_label_f1 | 0.0383 | 0.0367 | 0.0016 | [-0.012699, 0.016308] | 0.8290 | silver_proxy_not_human_gold |
| B0_plain_llm | evidence_f1 | 0.0516 | 0.0205 | 0.0311 | [0.022698, 0.040338] | 0.0000 | silver_proxy_not_human_gold |
| B2_current_project | predicate_f1 | 0.0658 | 0.0134 | 0.0524 | [0.028477, 0.079871] | 0.0000 | silver_proxy_not_human_gold |
| B2_current_project | node_label_f1 | 0.0383 | 0.0249 | 0.0134 | [0.002472, 0.025422] | 0.0180 | silver_proxy_not_human_gold |
| B2_current_project | evidence_f1 | 0.0516 | 0.0430 | 0.0087 | [0.004498, 0.01324] | 0.0000 | silver_proxy_not_human_gold |
| B3_edc_style | predicate_f1 | 0.0658 | 0.0257 | 0.0401 | [0.014748, 0.067981] | 0.0020 | silver_proxy_not_human_gold |
| B3_edc_style | node_label_f1 | 0.0383 | 0.0219 | 0.0164 | [0.003792, 0.0306] | 0.0090 | silver_proxy_not_human_gold |
| B3_edc_style | evidence_f1 | 0.0516 | 0.0278 | 0.0239 | [0.017186, 0.030731] | 0.0000 | silver_proxy_not_human_gold |
| B4_taxonomy_rag | predicate_f1 | 0.0658 | 0.0220 | 0.0438 | [0.022175, 0.067886] | 0.0000 | silver_proxy_not_human_gold |
| B4_taxonomy_rag | node_label_f1 | 0.0383 | 0.0316 | 0.0066 | [-0.0026, 0.0176] | 0.1910 | silver_proxy_not_human_gold |
| B4_taxonomy_rag | evidence_f1 | 0.0516 | 0.0508 | 0.0009 | [-0.002604, 0.003991] | 0.5970 | silver_proxy_not_human_gold |
| B5_procedural_prompt | predicate_f1 | 0.0658 | 0.0178 | 0.0480 | [0.018717, 0.079442] | 0.0040 | silver_proxy_not_human_gold |
| B5_procedural_prompt | node_label_f1 | 0.0383 | 0.0295 | 0.0088 | [-0.002724, 0.020937] | 0.1560 | silver_proxy_not_human_gold |
| B5_procedural_prompt | evidence_f1 | 0.0516 | 0.0491 | 0.0026 | [-0.001688, 0.007266] | 0.2340 | silver_proxy_not_human_gold |

## Claim Gate

| Gate | Status | Required | Evidence |
| --- | --- | --- | --- |
| data.eval_chunks | PASS | True | 120 chunks in experiments/cape_kg_eacl_20260627/01_data/evaluation_chunks.jsonl |
| gold.completed_chunks | FAIL | True | 0 completed chunks, validation_errors=0, file=experiments/cape_kg_eacl_20260627/04_evaluation/human_gold_validation_summary.json |
| gold.item_count | FAIL | True | 0 items, validation_errors=0, file=experiments/cape_kg_eacl_20260627/04_evaluation/human_gold_validation_summary.json |
| gold.iaa | FAIL | True | max_completed_pair_chunks=0, summaries=2 |
| llm.baselines | PASS | True | {'B0_plain_llm': 120, 'B1_predicate_constrained': 120, 'B2_current_project': 120} |
| llm.proposed_generation | PASS | True | {'P_cape_kg_actual': 120} |
| llm.proposed_human_gold_score | FAIL | True | human_gold_scored_conditions=[] |
| llm.ablations | PASS | True | 6 full ablations: ['P_minus_CQ', 'P_minus_Evidence', 'P_minus_Procedural_schema', 'P_minus_Schema_retrieval', 'P_minus_Standard_bridge', 'P_minus_Validator'] |
| llm.revalidated_output_recovery | PASS | False | all full conditions <= 5% unrepaired after conservative partial-JSON recovery |
| llm.strict_json_rate | PASS | False | all full conditions <= 50% strict parse/generation errors |
| external.public_subset | PASS | True | PAGED items=100, Text2KG items=200, summaries=4 |
| mapping.expert_review | FAIL | False | complete_source_groups=0, pending_rows=220, file=experiments/cape_kg_eacl_20260627/04_evaluation/mapping_expert_metrics.json, progress_file=experiments/cape_kg_eacl_20260627/06_release/mapping_review_progress_summary.json, progress_pending_groups=44 |
| crosswalk.expert_review | FAIL | False | completed_rows=0, pending_rows=220, complete_source_groups=0, file=experiments/cape_kg_eacl_20260627/04_evaluation/crosswalk_expert_metrics.json, manifest_file=experiments/cape_kg_eacl_20260627/01_data/crosswalk_review/crosswalk_review_manifest.json, candidate_rows=220 |
| analysis.error_analysis | PASS | True | {'markdown': {'path': 'experiments/cape_kg_eacl_20260627/07_reports/error_analysis.md', 'exists': True, 'bytes': 12148}, 'json': {'path': 'experiments/cape_kg_eacl_20260627/07_reports/error_analysis.json', 'exists': True, 'bytes': 34951}, 'required_sections': ['## Claim Scope', '## Actual LLM Silver/Proxy Diagnostics', '## Proxy Scaffold Error Summary', '## Error Taxonomy', '## Human-Gold Follow-Up'], 'missing_sections': [], 'taxonomy_family_count': 8, 'ready_for_minimum_accept': True, 'claim_scope': 'silver_proxy_diagnostic_not_human_gold'} |
| release.artifacts | PASS | True | all required release files exist |

