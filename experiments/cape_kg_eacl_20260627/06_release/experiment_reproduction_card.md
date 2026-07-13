# CAPE-KG Experiment Reproduction Card

Generated: 2026-06-29T18:56:41.753700+00:00
Experiment: `experiments/cape_kg_eacl_20260627`
Plan: `AX_EACL_submission_review_revised_plan.md`

This card connects the revised EACL plan's baselines, ablations, outputs, commands, and claim gates. It is a reproduction map, not a final performance claim.

## Summary

| Item | Value |
| --- | --- |
| Claim status | experiment_reproduction_card_ready_not_human_gold_claim |
| Safe to use as submission | False |
| Submission ready | False |
| Final performance claim ready | False |
| Conditions | 14 |
| Baselines | 7 |
| Proposed | 1 |
| Ablations | 6 |
| Conditions with 120 rows | 14 |
| Command groups | 12 |
| Missing source files | 0 |
| Missing condition outputs | 0 |

## Condition Matrix

| condition | family | rows | pred_nodes | pred_edges | pred_triples | pred_mappings | source_valid_file | metric_claim_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| B0_plain_llm | baseline | 120 | 1674 | 0 | 837 | 0 | experiments/cape_kg_eacl_20260627/49_qwen3_8b_condition_baselines_120_valid.jsonl | silver_proxy_not_human_gold |
| B1_predicate_constrained | baseline | 120 | 0 | 663 | 0 | 0 | experiments/cape_kg_eacl_20260627/49_qwen3_8b_condition_baselines_120_valid.jsonl | silver_proxy_not_human_gold |
| B2_current_project | baseline | 120 | 712 | 82 | 0 | 0 | experiments/cape_kg_eacl_20260627/49_qwen3_8b_b2_b4_condition_baselines_120_valid.jsonl | silver_proxy_not_human_gold |
| B3_edc_style | baseline | 120 | 566 | 53 | 0 | 0 | experiments/cape_kg_eacl_20260627/49_qwen3_8b_edc_schema_ablation_valid.jsonl | silver_proxy_not_human_gold |
| B4_taxonomy_rag | baseline | 120 | 674 | 128 | 0 | 41 | experiments/cape_kg_eacl_20260627/49_qwen3_8b_b2_b4_condition_baselines_120_valid.jsonl | silver_proxy_not_human_gold |
| B5_procedural_prompt | baseline | 120 | 957 | 119 | 0 | 0 | experiments/cape_kg_eacl_20260627/49_qwen3_8b_condition_baselines_120_valid.jsonl | silver_proxy_not_human_gold |
| B6_sac_kg_verifier_pruner | baseline | 120 | 2281 | 361 | 0 | 107 | experiments/cape_kg_eacl_20260627/49_sac_kg_verifier_pruner_baseline_valid.jsonl | silver_proxy_not_human_gold |
| P_cape_kg_actual | proposed | 120 | 549 | 275 | 0 | 52 | experiments/cape_kg_eacl_20260627/49_qwen3_8b_cape_ablation_120_valid.jsonl | silver_proxy_not_human_gold |
| P_minus_CQ | ablation | 120 | 554 | 284 | 0 | 35 | experiments/cape_kg_eacl_20260627/49_qwen3_8b_cape_ablation_120_valid.jsonl | silver_proxy_not_human_gold |
| P_minus_Evidence | ablation | 120 | 514 | 259 | 0 | 64 | experiments/cape_kg_eacl_20260627/49_qwen3_8b_cape_ablation_120_valid.jsonl | silver_proxy_not_human_gold |
| P_minus_Procedural_schema | ablation | 120 | 528 | 247 | 0 | 72 | experiments/cape_kg_eacl_20260627/49_qwen3_8b_cape_ablation_120_valid.jsonl | silver_proxy_not_human_gold |
| P_minus_Schema_retrieval | ablation | 120 | 566 | 308 | 0 | 25 | experiments/cape_kg_eacl_20260627/49_qwen3_8b_edc_schema_ablation_valid.jsonl | silver_proxy_not_human_gold |
| P_minus_Standard_bridge | ablation | 120 | 572 | 338 | 0 | 0 | experiments/cape_kg_eacl_20260627/49_qwen3_8b_cape_ablation_120_valid.jsonl | silver_proxy_not_human_gold |
| P_minus_Validator | ablation | 120 | 557 | 271 | 0 | 63 | experiments/cape_kg_eacl_20260627/49_qwen3_8b_cape_ablation_120_valid.jsonl | silver_proxy_not_human_gold |

## Reproduction Commands

| group | conditions | command | expected_valid_file | exists | paper_claim_scope |
| --- | --- | --- | --- | --- | --- |
| qwen3_8b_initial_baselines | B0_plain_llm,B1_predicate_constrained,B5_procedural_prompt | LLM_PYTHON=python3 CUDA_VISIBLE_DEVICES=0 python3 scripts/run_cape_llm_condition_baselines.py --output-dir experiments/cape_kg_eacl_20260627 --chunk-file 01_data/evaluation_chunks.jsonl --conditions B0_plain_llm,B1_predicate_constrained,B5_procedural_prompt --kg-dir outputs --output-prefix qwen3_8b_condition_baselines_120 --max-chunks 120 --strict-json-contract --resume | experiments/cape_kg_eacl_20260627/49_qwen3_8b_condition_baselines_120_valid.jsonl | True | reproduction or diagnostic only; not final human-gold performance |
| qwen3_8b_b2_b4_baselines | B2_current_project,B4_taxonomy_rag | LLM_PYTHON=python3 CUDA_VISIBLE_DEVICES=0 python3 scripts/run_cape_llm_condition_baselines.py --output-dir experiments/cape_kg_eacl_20260627 --chunk-file 01_data/evaluation_chunks.jsonl --conditions B2_current_project,B4_taxonomy_rag --kg-dir outputs --output-prefix qwen3_8b_b2_b4_condition_baselines --max-chunks 120 --strict-json-contract --resume | experiments/cape_kg_eacl_20260627/49_qwen3_8b_b2_b4_condition_baselines_120_valid.jsonl | True | reproduction or diagnostic only; not final human-gold performance |
| qwen3_8b_edc_schema_ablation | B3_edc_style,P_minus_Schema_retrieval | LLM_PYTHON=python3 CUDA_VISIBLE_DEVICES=0 python3 scripts/run_cape_llm_condition_baselines.py --output-dir experiments/cape_kg_eacl_20260627 --chunk-file 01_data/evaluation_chunks.jsonl --conditions B3_edc_style,P_minus_Schema_retrieval --kg-dir outputs --output-prefix qwen3_8b_edc_schema_ablation --max-chunks 120 --strict-json-contract --resume | experiments/cape_kg_eacl_20260627/49_qwen3_8b_edc_schema_ablation_valid.jsonl | True | reproduction or diagnostic only; not final human-gold performance |
| qwen3_8b_cape_ablation | P_cape_kg_actual,P_minus_CQ,P_minus_Evidence,P_minus_Procedural_schema,P_minus_Standard_bridge,P_minus_Validator | LLM_PYTHON=python3 CUDA_VISIBLE_DEVICES=0 python3 scripts/run_cape_llm_condition_baselines.py --output-dir experiments/cape_kg_eacl_20260627 --chunk-file 01_data/evaluation_chunks.jsonl --conditions P_cape_kg_actual,P_minus_CQ,P_minus_Evidence,P_minus_Procedural_schema,P_minus_Standard_bridge,P_minus_Validator --kg-dir outputs --output-prefix qwen3_8b_cape_ablation --max-chunks 120 --strict-json-contract --resume | experiments/cape_kg_eacl_20260627/49_qwen3_8b_cape_ablation_120_valid.jsonl | True | reproduction or diagnostic only; not final human-gold performance |
| sac_kg_verifier_pruner | B6_sac_kg_verifier_pruner | python3 scripts/build_sac_kg_verifier_pruner_baseline.py --experiment-dir experiments/cape_kg_eacl_20260627 --outputs-dir outputs | experiments/cape_kg_eacl_20260627/49_sac_kg_verifier_pruner_baseline_valid.jsonl | True | reproduction or diagnostic only; not final human-gold performance |
| silver_scoring | all conditions | python3 scripts/evaluate_actual_llm_silver.py --experiment-dir experiments/cape_kg_eacl_20260627 | experiments/cape_kg_eacl_20260627/04_evaluation/actual_llm_silver_metrics.json | True | reproduction or diagnostic only; not final human-gold performance |
| human_gold_refresh_after_returns | all conditions after human returns | PYTHON_BIN=python3 LLM_PYTHON=python3 APPLY_IMPORTS=1 bash scripts/run_cape_post_annotation_refresh.sh | experiments/cape_kg_eacl_20260627/04_evaluation/human_gold_metrics.json | True | reproduction or diagnostic only; not final human-gold performance |
| protocol_apply_human_returns | post-human or release protocol | PYTHON_BIN=python3 LLM_PYTHON=python3 APPLY_IMPORTS=1 bash scripts/run_cape_human_return_apply.sh |  | True | locked protocol command |
| protocol_dry_refresh | post-human or release protocol | PYTHON_BIN=python3 LLM_PYTHON=python3 APPLY_IMPORTS=0 bash scripts/run_cape_post_annotation_refresh.sh |  | True | locked protocol command |
| protocol_final_handoff_validation | post-human or release protocol | python3 scripts/validate_cape_pre_human_handoff.py --experiment-dir experiments/cape_kg_eacl_20260627 --outputs-dir outputs |  | True | locked protocol command |
| protocol_preflight_human_returns | post-human or release protocol | python3 scripts/validate_cape_human_review_returns.py --experiment-dir experiments/cape_kg_eacl_20260627 |  | True | locked protocol command |
| protocol_release_checksum | post-human or release protocol | sha256sum -c experiments/cape_kg_eacl_20260627/06_release/release_bundle_checksums.sha256 |  | True | locked protocol command |

## Prompt and Output Mapping

| condition | output_keys | prompt_file | reproduction_group | paper_claim_scope |
| --- | --- | --- | --- | --- |
| B0_plain_llm | triples | experiments/cape_kg_eacl_20260627/02_schema/prompts/B0_plain_llm_triple_extraction.txt | qwen3_8b_initial_baselines | diagnostic/silver only until adjudicated human-gold scoring |
| B1_predicate_constrained | edges | experiments/cape_kg_eacl_20260627/02_schema/prompts/B1_predicate_constrained_llm.txt | qwen3_8b_initial_baselines | diagnostic/silver only until adjudicated human-gold scoring |
| B2_current_project | nodes, edges | experiments/cape_kg_eacl_20260627/02_schema/prompts/B2_current_project_baseline.txt | qwen3_8b_b2_b4_baselines | diagnostic/silver only until adjudicated human-gold scoring |
| B3_edc_style | nodes, edges | experiments/cape_kg_eacl_20260627/02_schema/prompts/B3_edc_style_baseline.txt | qwen3_8b_edc_schema_ablation | diagnostic/silver only until adjudicated human-gold scoring |
| B4_taxonomy_rag | nodes, edges, mappings | experiments/cape_kg_eacl_20260627/02_schema/prompts/B4_taxonomy_rag_baseline.txt | qwen3_8b_b2_b4_baselines | diagnostic/silver only until adjudicated human-gold scoring |
| B5_procedural_prompt | nodes, edges | experiments/cape_kg_eacl_20260627/02_schema/prompts/B5_procedural_prompt_baseline.txt | qwen3_8b_initial_baselines | diagnostic/silver only until adjudicated human-gold scoring |
| B6_sac_kg_verifier_pruner | nodes, edges, mappings | experiments/cape_kg_eacl_20260627/02_schema/prompts/B6_sac_kg_verifier_pruner_baseline.txt | sac_kg_verifier_pruner | diagnostic/silver only until adjudicated human-gold scoring |
| P_cape_kg_actual | nodes, edges, mappings | experiments/cape_kg_eacl_20260627/02_schema/prompts/P_cape_kg.txt | qwen3_8b_cape_ablation | diagnostic/silver only until adjudicated human-gold scoring |
| P_minus_CQ | nodes, edges, mappings | runtime condition only | qwen3_8b_cape_ablation | diagnostic/silver only until adjudicated human-gold scoring |
| P_minus_Evidence | nodes, edges, mappings | runtime condition only | qwen3_8b_cape_ablation | diagnostic/silver only until adjudicated human-gold scoring |
| P_minus_Procedural_schema | nodes, edges, mappings | runtime condition only | qwen3_8b_cape_ablation | diagnostic/silver only until adjudicated human-gold scoring |
| P_minus_Schema_retrieval | nodes, edges, mappings | experiments/cape_kg_eacl_20260627/02_schema/prompts/P_minus_Schema_retrieval.txt | qwen3_8b_edc_schema_ablation | diagnostic/silver only until adjudicated human-gold scoring |
| P_minus_Standard_bridge | nodes, edges | runtime condition only | qwen3_8b_cape_ablation | diagnostic/silver only until adjudicated human-gold scoring |
| P_minus_Validator | nodes, edges, mappings | runtime condition only | qwen3_8b_cape_ablation | diagnostic/silver only until adjudicated human-gold scoring |

## Claim Gate Policy

- The condition matrix documents executed or reproducible diagnostic runs, not final paper performance.
- Silver/proxy F1 values are allowed only for debugging and setup discussion.
- Main result tables require adjudicated human-gold labels, IAA, adjudication, and post-human scoring.
- Downstream mapping utility requires expert-reviewed NCS/PCF and crosswalk returns.

## Source Files

| role | exists | bytes | path |
| --- | --- | --- | --- |
| revised_plan | True | 29461 | AX_EACL_submission_review_revised_plan.md |
| evaluation_chunks_private | True | 495269 | experiments/cape_kg_eacl_20260627/01_data/evaluation_chunks.jsonl |
| silver_metrics | True | 15122 | experiments/cape_kg_eacl_20260627/04_evaluation/actual_llm_silver_metrics.json |
| evaluation_protocol_lock | True | 27469 | experiments/cape_kg_eacl_20260627/06_release/evaluation_protocol_lock.json |
| prompt_node_edge_traceability | True | 24271 | experiments/cape_kg_eacl_20260627/06_release/prompt_node_edge_traceability.json |
| qwen3_model_scaling | True | 11209 | experiments/cape_kg_eacl_20260627/06_release/qwen3_model_scaling_report.json |
| public_benchmark_crosscheck | True | 3839 | experiments/cape_kg_eacl_20260627/08_public_benchmarks/public_benchmark_crosscheck_summary.json |
| final_layer2_nodes | True | 94237 | outputs/07_layer2_graph/layer2_nodes.jsonl |
| final_layer2_edges | True | 331827 | outputs/07_layer2_graph/layer2_edges.jsonl |
| reproduction_output:qwen3_8b_initial_baselines | True | 481286 | experiments/cape_kg_eacl_20260627/49_qwen3_8b_condition_baselines_120_valid.jsonl |
| reproduction_output:qwen3_8b_b2_b4_baselines | True | 275348 | experiments/cape_kg_eacl_20260627/49_qwen3_8b_b2_b4_condition_baselines_120_valid.jsonl |
| reproduction_output:qwen3_8b_edc_schema_ablation | True | 261060 | experiments/cape_kg_eacl_20260627/49_qwen3_8b_edc_schema_ablation_valid.jsonl |
| reproduction_output:qwen3_8b_cape_ablation | True | 1021348 | experiments/cape_kg_eacl_20260627/49_qwen3_8b_cape_ablation_120_valid.jsonl |
| reproduction_output:sac_kg_verifier_pruner | True | 425795 | experiments/cape_kg_eacl_20260627/49_sac_kg_verifier_pruner_baseline_valid.jsonl |
| reproduction_output:silver_scoring | True | 15122 | experiments/cape_kg_eacl_20260627/04_evaluation/actual_llm_silver_metrics.json |
| reproduction_output:human_gold_refresh_after_returns | True | 1509 | experiments/cape_kg_eacl_20260627/04_evaluation/human_gold_metrics.json |

## Interpretation

- Use this file to explain exactly what was run for each baseline, proposed condition, and ablation.
- Use the command groups as reproduction entry points; some commands require the project LLM environment and GPU access.
- Do not use the silver/proxy metric values as final EACL main results.
- After human returns are imported, run the post-annotation refresh wrapper and regenerate this card if condition outputs or claim gates change.
