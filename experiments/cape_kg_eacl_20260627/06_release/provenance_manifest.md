# CAPE-KG Provenance Manifest

Generated: 2026-06-29T18:56:42.293489+00:00
Claim status: `provenance_manifest_ready_not_human_gold_evidence`

This manifest records file-level provenance for source artifacts, prompts, schemas, LLM runs, evaluation outputs, human-review handoffs, and release bundles. It is reproducibility evidence, not human-gold performance evidence.

## Summary

| Item | Value |
|---|---:|
| source_file_count | 8 |
| prompt_and_schema_file_count | 16 |
| evaluation_file_count | 112 |
| human_review_file_count | 75 |
| release_file_count | 36 |
| llm_run_count | 23 |
| llm_runs_with_raw | 23 |
| llm_runs_with_valid | 23 |
| missing_required_count | 0 |

## LLM Run Index

| logical_run | raw_rows | valid_rows | parse_errors | repaired | raw_file | valid_file |
|---|---:|---:|---:|---:|---|---|
| llama2_13b_chat_tool_extractions | 10 | 10 | 2 | 0 | `experiments/cape_kg_eacl_20260627/45_llama2_13b_chat_tool_extractions_raw.jsonl` | `experiments/cape_kg_eacl_20260627/46_llama2_13b_chat_tool_extractions_valid.jsonl` |
| llm_tool_extractions | 120 | 120 | 61 | 0 | `experiments/cape_kg_eacl_20260627/45_llm_tool_extractions_raw.jsonl` | `experiments/cape_kg_eacl_20260627/46_llm_tool_extractions_valid.jsonl` |
| qwen3_14b_core_conditions_120 | 480 | 480 | 358 | 358 | `experiments/cape_kg_eacl_20260627/48_qwen3_14b_core_conditions_120_raw.jsonl` | `experiments/cape_kg_eacl_20260627/49_qwen3_14b_core_conditions_120_valid.jsonl` |
| qwen3_14b_core_conditions_smoke | 16 | 16 | 6 | 6 | `experiments/cape_kg_eacl_20260627/48_qwen3_14b_core_conditions_smoke_raw.jsonl` | `experiments/cape_kg_eacl_20260627/49_qwen3_14b_core_conditions_smoke_valid.jsonl` |
| qwen3_32b_awq_core_120 | 480 | 480 | 335 | 335 | `experiments/cape_kg_eacl_20260627/48_qwen3_32b_awq_core_120_raw.jsonl` | `experiments/cape_kg_eacl_20260627/49_qwen3_32b_awq_core_120_valid.jsonl` |
| qwen3_32b_awq_smoke | 8 | 8 | 4 | 4 | `experiments/cape_kg_eacl_20260627/48_qwen3_32b_awq_smoke_raw.jsonl` | `experiments/cape_kg_eacl_20260627/49_qwen3_32b_awq_smoke_valid.jsonl` |
| qwen3_8b_b2_b4_condition_baselines_120 | 240 | 240 | 199 | 199 | `experiments/cape_kg_eacl_20260627/48_qwen3_8b_b2_b4_condition_baselines_120_raw.jsonl` | `experiments/cape_kg_eacl_20260627/49_qwen3_8b_b2_b4_condition_baselines_120_valid.jsonl` |
| qwen3_8b_b2_b4_condition_smoke | 10 | 10 | 4 | 0 | `experiments/cape_kg_eacl_20260627/48_qwen3_8b_b2_b4_condition_smoke_raw.jsonl` | `experiments/cape_kg_eacl_20260627/49_qwen3_8b_b2_b4_condition_smoke_valid.jsonl` |
| qwen3_8b_cape_ablation_120 | 720 | 720 | 609 | 609 | `experiments/cape_kg_eacl_20260627/48_qwen3_8b_cape_ablation_120_raw.jsonl` | `experiments/cape_kg_eacl_20260627/49_qwen3_8b_cape_ablation_120_valid.jsonl` |
| qwen3_8b_cape_ablation_smoke | 12 | 12 | 10 | 0 | `experiments/cape_kg_eacl_20260627/48_qwen3_8b_cape_ablation_smoke_raw.jsonl` | `experiments/cape_kg_eacl_20260627/49_qwen3_8b_cape_ablation_smoke_valid.jsonl` |
| qwen3_8b_cape_ablation_smoke_limited | 12 | 12 | 7 | 0 | `experiments/cape_kg_eacl_20260627/48_qwen3_8b_cape_ablation_smoke_limited_raw.jsonl` | `experiments/cape_kg_eacl_20260627/49_qwen3_8b_cape_ablation_smoke_limited_valid.jsonl` |
| qwen3_8b_condition_baselines | 30 | 30 | 8 | 0 | `experiments/cape_kg_eacl_20260627/48_qwen3_8b_condition_baselines_raw.jsonl` | `experiments/cape_kg_eacl_20260627/49_qwen3_8b_condition_baselines_valid.jsonl` |
| qwen3_8b_condition_baselines_120 | 360 | 360 | 222 | 222 | `experiments/cape_kg_eacl_20260627/48_qwen3_8b_condition_baselines_120_raw.jsonl` | `experiments/cape_kg_eacl_20260627/49_qwen3_8b_condition_baselines_120_valid.jsonl` |
| qwen3_8b_edc_schema_ablation | 240 | 240 | 208 | 207 | `experiments/cape_kg_eacl_20260627/48_qwen3_8b_edc_schema_ablation_raw.jsonl` | `experiments/cape_kg_eacl_20260627/49_qwen3_8b_edc_schema_ablation_valid.jsonl` |
| qwen3_8b_edc_schema_ablation_smoke | 4 | 4 | 2 | 2 | `experiments/cape_kg_eacl_20260627/48_qwen3_8b_edc_schema_ablation_smoke_raw.jsonl` | `experiments/cape_kg_eacl_20260627/49_qwen3_8b_edc_schema_ablation_smoke_valid.jsonl` |
| qwen3_8b_strict_json_1200_full | 1560 | 1560 | 569 | 569 | `experiments/cape_kg_eacl_20260627/48_qwen3_8b_strict_json_1200_full_raw.jsonl` | `experiments/cape_kg_eacl_20260627/49_qwen3_8b_strict_json_1200_full_valid.jsonl` |
| qwen3_8b_strict_json_contract_smoke | 16 | 16 | 15 | 15 | `experiments/cape_kg_eacl_20260627/48_qwen3_8b_strict_json_contract_smoke_raw.jsonl` | `experiments/cape_kg_eacl_20260627/49_qwen3_8b_strict_json_contract_smoke_valid.jsonl` |
| qwen3_8b_strict_json_nothink_1200_smoke | 8 | 8 | 0 | 0 | `experiments/cape_kg_eacl_20260627/48_qwen3_8b_strict_json_nothink_1200_smoke_raw.jsonl` | `experiments/cape_kg_eacl_20260627/49_qwen3_8b_strict_json_nothink_1200_smoke_valid.jsonl` |
| qwen3_8b_strict_json_nothink_smoke | 16 | 16 | 16 | 16 | `experiments/cape_kg_eacl_20260627/48_qwen3_8b_strict_json_nothink_smoke_raw.jsonl` | `experiments/cape_kg_eacl_20260627/49_qwen3_8b_strict_json_nothink_smoke_valid.jsonl` |
| qwen3_8b_strict_json_warn_top3_full_1200 | 360 | 360 | 215 | 215 | `experiments/cape_kg_eacl_20260627/48_qwen3_8b_strict_json_warn_top3_full_1200_raw.jsonl` | `experiments/cape_kg_eacl_20260627/49_qwen3_8b_strict_json_warn_top3_full_1200_valid.jsonl` |
| qwen3_8b_strict_json_warn_top3_full_2400 | 360 | 360 | 92 | 92 | `experiments/cape_kg_eacl_20260627/48_qwen3_8b_strict_json_warn_top3_full_2400_raw.jsonl` | `experiments/cape_kg_eacl_20260627/49_qwen3_8b_strict_json_warn_top3_full_2400_valid.jsonl` |
| qwen3_8b_strict_json_warn_top3_smoke_1200 | 12 | 12 | 0 | 0 | `experiments/cape_kg_eacl_20260627/48_qwen3_8b_strict_json_warn_top3_smoke_1200_raw.jsonl` | `experiments/cape_kg_eacl_20260627/49_qwen3_8b_strict_json_warn_top3_smoke_1200_valid.jsonl` |
| sac_kg_verifier_pruner_baseline | 120 | 120 | 0 | 0 | `experiments/cape_kg_eacl_20260627/48_sac_kg_verifier_pruner_baseline_raw.jsonl` | `experiments/cape_kg_eacl_20260627/49_sac_kg_verifier_pruner_baseline_valid.jsonl` |

## File Groups

### source_files

| role | exists | records | bytes | sha256 | path |
|---|---:|---:|---:|---|---|
| data_manifest | True |  | 16391 | `11bf7594c0df6fa2d60f4201a3951f41fb3f4e7381a14fcfa54754c73bec2428` | `outputs/00_manifest/data_manifest.json` |
| ocr_structure | True |  | 161394 | `455c1c0c9376872643fc6d59ad972b04a9a0bce08577a5d476b823939ebd4f6a` | `outputs/02_ocr/document_structure_reviewed.json` |
| evidence_sentence_anchors | True | 5009 | 3198719 | `20911538dcbdad8e200d90fa72cadf9259670ed333b831d1a2c4aef3e4c4214d` | `outputs/02_ocr/ocr_sentences_clean.jsonl` |
| layer2_chunks | True | 214 | 1006690 | `5686d68a8ccf8dca4abc3b99b84de63716be96e8ec40927f9407a290f52fb968` | `outputs/02_ocr/layer2_chunks.jsonl` |
| layer1_ncs_nodes | True | 4109 | 2692452 | `bffe3bba938e54626b8eb715292f6ec85a78772667cdc20dc827ff9f45d8a3e3` | `outputs/01_layer1/layer1_ncs_nodes.jsonl` |
| layer1_pcf_nodes | True | 5301 | 3610251 | `b3b6f0c8528daa2b20980ed9756796a3a67e71c45ef6dc3340dd8b7c0a8777c8` | `outputs/01_layer1/layer1_pcf_nodes.jsonl` |
| evaluation_chunks | True | 120 | 495269 | `64d884bfaecea042b3aedd055a1ab3abc06bd7dd7ff3a0d60505f92164509fed` | `experiments/cape_kg_eacl_20260627/01_data/evaluation_chunks.jsonl` |
| public_benchmark_manifest | True |  | 17745 | `11cbc2bf1a70f87b4fe2c960fd331503a05dadc0e14c68ab4fd2ef87b5d7c2e0` | `experiments/cape_kg_eacl_20260627/08_public_benchmarks/public_benchmark_manifest.json` |

### prompt_and_schema_files

| role | exists | records | bytes | sha256 | path |
|---|---:|---:|---:|---|---|
| prompt | True |  | 75 | `ad219b0e42adf3e2ccfa342ae38dce49fb74dbd7ae0fbdf5a59598f4a24b031f` | `experiments/cape_kg_eacl_20260627/02_schema/prompts/B0_plain_llm_triple_extraction.txt` |
| prompt | True |  | 96 | `a453b6587e8b3e03e2839874cc1fff8f6e1a249a83ec59ede8453f3a16a41651` | `experiments/cape_kg_eacl_20260627/02_schema/prompts/B1_predicate_constrained_llm.txt` |
| prompt | True |  | 77 | `9a639be66c6b2a3727078108143f4e65ccb22ed69a2c5d29b891ac19a452cf4a` | `experiments/cape_kg_eacl_20260627/02_schema/prompts/B2_current_project_baseline.txt` |
| prompt | True |  | 111 | `d272d5d4a9463b5cbc8225a7f754e715675787a5e347d15903c9d5ad0b020ee2` | `experiments/cape_kg_eacl_20260627/02_schema/prompts/B3_edc_style_baseline.txt` |
| prompt | True |  | 96 | `158bb086cd403a70c995049d0dd43573f94dc904e63ff179c093c95a40cf30fd` | `experiments/cape_kg_eacl_20260627/02_schema/prompts/B4_taxonomy_rag_baseline.txt` |
| prompt | True |  | 104 | `7b435cf341de2b892b8221641ff14049d6d895d4d9b6303397805406f63c71b3` | `experiments/cape_kg_eacl_20260627/02_schema/prompts/B5_procedural_prompt_baseline.txt` |
| prompt | True |  | 182 | `8ae83e345b52d39328da78a6a7cfbf65d5945fe7a061daf6adedfa6a793ab88a` | `experiments/cape_kg_eacl_20260627/02_schema/prompts/B6_sac_kg_verifier_pruner_baseline.txt` |
| prompt | True |  | 206 | `55511f96c5c8440216baa973ff4b8fb80d5d952ec7f4d91bc91c75a9c6496e71` | `experiments/cape_kg_eacl_20260627/02_schema/prompts/P_cape_kg.txt` |
| prompt | True |  | 148 | `87f8d1d5403a9d32da879ea76f073fc066c13369e086f788428c3dafb2edfbf0` | `experiments/cape_kg_eacl_20260627/02_schema/prompts/P_minus_Schema_retrieval.txt` |
| prompt | True |  | 664 | `699c4aa6927dc3bccf72a9906e2aa8a40a7e5e2493d18ebcb4f000251bdfd783` | `experiments/cape_kg_eacl_20260627/02_schema/prompts/strict_json_contract.txt` |
| schema_or_cq | True |  | 3523 | `55ce9947e4240e781c52f25f0e6f6142aa7b1572eca9d4e50ae3c9cb7296b0d6` | `experiments/cape_kg_eacl_20260627/02_schema/cape_schema.json` |
| schema_or_cq | True |  | 340 | `155d51f83766139a766627418d17e65aad34e44073ddde3b3807e19767c5cac1` | `experiments/cape_kg_eacl_20260627/02_schema/cape_shapes.shacl.ttl` |
| schema_or_cq | True |  | 1164 | `4d222ece9cec3f3ccf1cb6eee352447153538fe7e0f17968a47df39e1de94863` | `outputs/03_schema/layer2_schema.json` |
| schema_or_cq | True |  | 2691 | `eb260124a4feebeff02aab4d381242161457ae9cf810c066af0a1bb08a201293` | `outputs/03_schema/domain_range_constraints.json` |
| schema_or_cq | True |  | 506 | `f1f89380f24c7cabb4546a74ed947fc849f5790f91cb043d87eb542d5d14f5e8` | `outputs/03_schema/allowed_predicates.json` |
| schema_or_cq | True |  | 2303 | `5d5ad4935c2c558adedb5629f2a5901553d2add58f139f3be1c04124e6be55c1` | `outputs/03_schema/competency_questions.json` |

### evaluation_files

| role | exists | records | bytes | sha256 | path |
|---|---:|---:|---:|---|---|
| evaluation_or_gate | True |  | 15122 | `cca895a4eca0ac1228519a6bbb43ff0afab0652fc94d3d57fac2c80d4e798e17` | `experiments/cape_kg_eacl_20260627/04_evaluation/actual_llm_silver_metrics.json` |
| evaluation_or_gate | True |  | 4435 | `c0bff27fa96037195fe56b50ee0da74eb74af86633aaa10e0c87a6577df91c5f` | `experiments/cape_kg_eacl_20260627/04_evaluation/qwen3_14b_core_silver_metrics.json` |
| evaluation_or_gate | True |  | 4398 | `a9d4545a9235e3b6b6c7110229a8903d041683d23eefcfa529ed595f45a901e7` | `experiments/cape_kg_eacl_20260627/04_evaluation/qwen3_32b_awq_core_silver_metrics.json` |
| evaluation_or_gate | True |  | 11209 | `4d154fbf91984b1ab665091de9ccc08775151337b7d31ba54f822c16f4e2d149` | `experiments/cape_kg_eacl_20260627/06_release/qwen3_model_scaling_report.json` |
| evaluation_or_gate | True |  | 4752 | `a0659a6269d112c6085674bcd7efcc5f812d244413efd046bde0ee7d1505e9a8` | `experiments/cape_kg_eacl_20260627/06_release/qwen3_model_scaling_report.md` |
| evaluation_or_gate | True |  | 22053 | `108afa8861661de058bbe013879143773d19f9695a5ef4dccdeb7b81050fc14d` | `experiments/cape_kg_eacl_20260627/04_evaluation/structural_evaluation_metrics.json` |
| evaluation_or_gate | True |  | 1822 | `2e854b162a5b1209e1b552b0357e08a6a51e801e846647242eb66bd635bbc841` | `experiments/cape_kg_eacl_20260627/04_evaluation/evidence_span_granularity_metrics.json` |
| evaluation_or_gate | True |  | 1603 | `861843745a481b47c8cf3a3dc71acbfb78fe0dad393a6e1ee743f88ecaee2e4a` | `outputs/13_evidence_graph/evidence_graph_projection_summary.json` |
| evaluation_or_gate | True |  | 1638 | `e7dbc0835a8c7505a249be614dfc9b983c14982dcb3405f815bd4877e4841115` | `outputs/13_evidence_graph/evidence_graph_projection_report.md` |
| evaluation_or_gate | True | 451 | 225323 | `fcceee05ca64281027c0d4c691b6b62af86a88061ee2a17260b4b1e0656401d6` | `outputs/13_evidence_graph/evidence_anchor_nodes.jsonl` |
| evaluation_or_gate | True | 3915 | 2227213 | `bf6102dce0b95c0ffdb4c11b369c49ef96e7e47307338ae3b334a5a3a21f5888` | `outputs/13_evidence_graph/evidenced_by_edges.jsonl` |
| evaluation_or_gate | True |  | 1475 | `6ad94a04ddb2928cd96b479c826506a4d76797e07b2c0663c347e56af536b405` | `outputs/11_neo4j_import/manifest.json` |
| evaluation_or_gate | True |  | 15647 | `2ca33d5033a262565d1f1db70bd932f8c0b4205cfa117e4e611e359db106e256` | `outputs/11_neo4j_import/neo4j_csv_validation_report.json` |
| evaluation_or_gate | True |  | 1479 | `845ed71bdce549f040e0a95607b0d7c9e7e1bea9c8159f816f6fc21037f9f4da` | `outputs/11_neo4j_import_flat/manifest.json` |
| evaluation_or_gate | True |  | 15499 | `0031af04ce44c640294497b437bee8219ce280843f11c7c25e15c4a406c7bab8` | `outputs/11_neo4j_import_flat/neo4j_csv_validation_report.json` |
| evaluation_or_gate | True |  | 4954 | `26c2c4dd0eba2e3d852207fd6855f6791981cee38cfd875c818085759d387895` | `outputs/11_neo4j_import_flat/neo4j_evidence_queries.cypher` |
| evaluation_or_gate | True |  | 10917 | `5d637e5f4fa307ce7b0281536726254b5e2c5e43d9e763a5f0c593f3c1f8e54c` | `experiments/cape_kg_eacl_20260627/06_release/neo4j_evidence_query_pack.json` |
| evaluation_or_gate | True |  | 8410 | `3d38ba2840047667e1bb32cbb7d2ad0ec6f7324ae991e3b9457f6504a9536faf` | `experiments/cape_kg_eacl_20260627/06_release/neo4j_evidence_query_pack.md` |
| evaluation_or_gate | True |  | 12827 | `2fdd5afdd7de3f8a04163789e694f6e4fcd5a5e1bf4581f1fa71f767fc7b06b6` | `experiments/cape_kg_eacl_20260627/04_evaluation/active_review_efficiency_metrics.json` |
| evaluation_or_gate | True |  | 11236 | `8724e0346622a5190c111f4228c4fe496d0c559def3207f2c6d9e9191158458b` | `experiments/cape_kg_eacl_20260627/04_evaluation/active_review_ablation_metrics.json` |
| evaluation_or_gate | True |  | 6348 | `f59b516797ccd39e14750d90a72ae7778f0bb295147cd9c1f7ffc1198b5c629c` | `experiments/cape_kg_eacl_20260627/04_evaluation/active_review_human_effort_metrics.json` |
| evaluation_or_gate | True |  | 1861 | `71f89ea3925dfa2a7134b6e0ddbe6e29f73cef132fb5d34901c97bc7290fee84` | `experiments/cape_kg_eacl_20260627/04_evaluation/active_review_pool_overlap_summary.json` |
| evaluation_or_gate | True |  | 1650 | `e2bb1224e40eb442013719549350854a65f59020ab295582ff36690c9c80984d` | `experiments/cape_kg_eacl_20260627/04_evaluation/active_review_pool_overlap_report.md` |
| evaluation_or_gate | True |  | 1880 | `2260a071c5744088e83c8d064d077aae738c15cf524b66745c33645b243bbb89` | `experiments/cape_kg_eacl_20260627/06_release/active_review_human_effort_briefing.json` |
| evaluation_or_gate | True |  | 15523 | `87b884c8bb3e24ff53244cae1e72c277e55b810b3fc6276bd0d713838dcf2d8f` | `experiments/cape_kg_eacl_20260627/06_release/active_review_human_effort_briefing.md` |
| evaluation_or_gate | True | 204 | 98684 | `70fdd580c16a171e2a245d0b0c1fbebb470a0414fa6def4e3cb2dcc0de0c78f8` | `experiments/cape_kg_eacl_20260627/05_review/active_review_human_effort_briefing.csv` |
| evaluation_or_gate | True |  | 17745 | `11cbc2bf1a70f87b4fe2c960fd331503a05dadc0e14c68ab4fd2ef87b5d7c2e0` | `experiments/cape_kg_eacl_20260627/08_public_benchmarks/public_benchmark_manifest.json` |
| evaluation_or_gate | True |  | 1857 | `2aa5dea3308838f0d82f6e99838f599a137f0203af1d563809fd33dabf8bab55` | `experiments/cape_kg_eacl_20260627/08_public_benchmarks/public_benchmark_adapter_report.md` |
| evaluation_or_gate | True |  | 3839 | `de5b64ae0cb6ca0b9783ba1ba53fcc4015d6ddb0781952664fb73931a79288eb` | `experiments/cape_kg_eacl_20260627/08_public_benchmarks/public_benchmark_crosscheck_summary.json` |
| evaluation_or_gate | True |  | 1379 | `534fec4e256509b8490df4b12877c24b553d5c66607fc261760dd166d2284541` | `experiments/cape_kg_eacl_20260627/08_public_benchmarks/public_benchmark_crosscheck_report.md` |
| evaluation_or_gate | True |  | 893 | `e825d1374d51aaf28676f68da6a8aa11bf46955f924ad4f4d14af3c7f85c6c9a` | `experiments/cape_kg_eacl_20260627/04_evaluation/ncs_pcf_crosswalk_summary.json` |
| evaluation_or_gate | True | 2 | 300 | `c48a1d282a02256ba41b81277db57ee5ff71df4353a0f603664ccb414f8e9de8` | `experiments/cape_kg_eacl_20260627/04_evaluation/mapping_downstream_results.csv` |
| evaluation_or_gate | True | 8 | 2135 | `81b48990c6917789c367bf7c346b54d7a2fb8a0bc4bd817c637ffc4845c0d67c` | `experiments/cape_kg_eacl_20260627/04_evaluation/mapping_downstream_arm_diagnostics.csv` |
| evaluation_or_gate | True | 176 | 73343 | `5345d2dab3d4b9a782dad421030b626590cd0504185a4dad54e62e8c31fb2a13` | `experiments/cape_kg_eacl_20260627/04_evaluation/mapping_downstream_arm_rerank_details.csv` |
| evaluation_or_gate | True |  | 1744 | `05ac6560264fc76ca1187fc6806f5d7900e86bc18f659c8296e75c3e562acb06` | `experiments/cape_kg_eacl_20260627/04_evaluation/mapping_downstream_arm_rerank_summary.json` |
| evaluation_or_gate | True |  | 2824 | `170cce208ddb5c3fb90c01f594680325f2e8d821d93494357205fd232edc0675` | `experiments/cape_kg_eacl_20260627/04_evaluation/mapping_downstream_report.md` |
| evaluation_or_gate | True |  | 1675 | `6a9ccffe47e2fbc7b487a9e953f7047bcb9498a972003df0ed9ec2a31d4d711f` | `experiments/cape_kg_eacl_20260627/04_evaluation/mapping_expert_metrics.json` |
| evaluation_or_gate | True |  | 119714 | `2a416554886de80e01b82b7bfc1658cb3f2e2181e85da2bd0577ddd88eef764b` | `experiments/cape_kg_eacl_20260627/06_release/mapping_review_group_briefing.json` |
| evaluation_or_gate | True |  | 29653 | `bd33d8c3f776cab1bb315b3f8f079c56d53ce504f6e5ef2cc2ba54a2140954df` | `experiments/cape_kg_eacl_20260627/06_release/mapping_review_group_briefing.md` |
| evaluation_or_gate | True | 100 | 56828 | `50507d5e9c1518e24e273e4f195a475aa7683423ea8430d7d939f292ff661e5b` | `experiments/cape_kg_eacl_20260627/05_review/mapping_review_group_briefing_top20.csv` |
| evaluation_or_gate | True | 60 | 13328 | `cbbd214f2c7e949dc4385d72a9c0c29dd54a7c08ac62b733b4d5c097f4db99f5` | `experiments/cape_kg_eacl_20260627/04_evaluation/cq_query_sample_answers.csv` |
| evaluation_or_gate | True |  | 1509 | `31129f425670a3765fb454c69168b60f6bb56c1dd0c37cd4fa2f94bae7f4b843` | `experiments/cape_kg_eacl_20260627/04_evaluation/human_gold_metrics.json` |
| evaluation_or_gate | True |  | 1405 | `667e354614b77b2b1e5a04b78e6581d60e4204598641a98e23887c1a0f2943cb` | `experiments/cape_kg_eacl_20260627/04_evaluation/human_gold_span_iou_metrics.json` |
| evaluation_or_gate | True | 0 | 162 | `c3b89a2e8acdf01971e920b6aa89d8dfd0d979743dadb89872a465d2be3f93ae` | `experiments/cape_kg_eacl_20260627/04_evaluation/human_gold_span_iou_components.csv` |
| evaluation_or_gate | True |  | 1371 | `999e58808c777c1516ce6791ad7a1b2874cc61341d1f7329264f39f6dc928ec0` | `experiments/cape_kg_eacl_20260627/04_evaluation/human_gold_span_iou_report.md` |
| evaluation_or_gate | True |  | 16096 | `3235308a11ef4581ddc12715eaf96c0d8154a3f417f923cefd2683cdf4a1bc8f` | `experiments/cape_kg_eacl_20260627/06_release/claim_gate_report.json` |
| evaluation_or_gate | True |  | 13239 | `e272fd2b3890703630c2e00d3ad32c553e8070c11a02f15ed6a046c4ff743bc6` | `experiments/cape_kg_eacl_20260627/06_release/arr_submission_policy_checklist.json` |
| evaluation_or_gate | True |  | 12933 | `569b07617cc6d866403bb9ba5790474319dba44044f8d879839defb823a6fca2` | `experiments/cape_kg_eacl_20260627/06_release/arr_submission_policy_checklist.md` |
| evaluation_or_gate | True |  | 85790 | `4d071c39568cd9b3cedb66ea7bda52dffaa14520f75e0156a174115c499a6870` | `experiments/cape_kg_eacl_20260627/06_release/anonymized_submission_prep.json` |
| evaluation_or_gate | True |  | 17046 | `5139227f553a9ddeed9a21b9e01ef3f4ad02d5263e43320887ae870963364d5e` | `experiments/cape_kg_eacl_20260627/06_release/anonymized_submission_prep.md` |
| evaluation_or_gate | True | 200 | 57075 | `f30387c79748adb3610148c468d95c77a3bfb7609fd29d761ee89d052c8a888c` | `experiments/cape_kg_eacl_20260627/06_release/anonymized_submission_risk_scan.csv` |
| evaluation_or_gate | True |  | 17320 | `5a5cc928fed2961bbfa94f756088147bc4b2ca12a27e61395bc179bcbb6ca254` | `experiments/cape_kg_eacl_20260627/06_release/responsible_nlp_checklist_prep.json` |
| evaluation_or_gate | True |  | 14584 | `011812f14a9f0a3ce4992c4bdb094383d219ccbd2689cb0e56d8cafed096d4e6` | `experiments/cape_kg_eacl_20260627/06_release/responsible_nlp_checklist_prep.md` |
| evaluation_or_gate | True | 10 | 8934 | `bd40871ee013d8eb243621de3016351e5c10782853cfad00f0e18129fc20b43c` | `experiments/cape_kg_eacl_20260627/06_release/responsible_nlp_checklist_items.csv` |
| evaluation_or_gate | True |  | 25386 | `5ecec8fb6c90e324d71f8e5602f6b19705f230bbe8a330a4e312361827095542` | `experiments/cape_kg_eacl_20260627/06_release/experiment_reproduction_card.json` |
| evaluation_or_gate | True |  | 13855 | `aeef4e27c54994085265554fbeded68cb733d4ee7147fb2491b7d3ee60613cc8` | `experiments/cape_kg_eacl_20260627/06_release/experiment_reproduction_card.md` |
| evaluation_or_gate | True | 14 | 6136 | `a7b960ef88f2fa95e6e153b513bdae503364c6d3dce3ea315a67dcb008128f52` | `experiments/cape_kg_eacl_20260627/06_release/experiment_reproduction_conditions.csv` |
| evaluation_or_gate | True |  | 24674 | `0057536408fcce5f75ecfd47db9a099e1cd9b239d612a403d9dc646d6571f4a6` | `experiments/cape_kg_eacl_20260627/06_release/claim_language_guardrails.json` |
| evaluation_or_gate | True |  | 19281 | `14ab147ab22300ab1c61308a8304d2e48d6709ae6b3b68d6fc28b640b60c44d4` | `experiments/cape_kg_eacl_20260627/06_release/claim_language_guardrails.md` |
| evaluation_or_gate | True |  | 16864 | `acb2c81fd51d0a3acf55c5d1947689da1b453f5409d19340c69db50c7d1aac4c` | `experiments/cape_kg_eacl_20260627/06_release/reviewer_response_prep.json` |
| evaluation_or_gate | True |  | 14814 | `59ca1834b986ba6c1f531afec8979220443b7b226622443e5981000266833c26` | `experiments/cape_kg_eacl_20260627/06_release/reviewer_response_prep.md` |
| evaluation_or_gate | True |  | 20171 | `0c3e6c5d503cd2bcdb5a4b82ac11c7717633c9d44ec6e1ff47f952671507e4b8` | `experiments/cape_kg_eacl_20260627/06_release/submission_timeline_action_board.json` |
| evaluation_or_gate | True |  | 6133 | `5b6f1ee217f5dbf76cdc3b5557f16deda1528e3872f1c2c79b589cb31762a571` | `experiments/cape_kg_eacl_20260627/06_release/submission_timeline_action_board.md` |
| evaluation_or_gate | True |  | 8484 | `005f17132e2ea81a48be93da5af34dfa47a6c038ae84bbdc8d6d8b85711a6480` | `experiments/cape_kg_eacl_20260627/06_release/claimable_main_table.json` |
| evaluation_or_gate | True |  | 44897 | `650cb93e9a0e86eb8d75ed5fd2dcdf1c92dadbcb228fd3602fdb427a3bfad282` | `experiments/cape_kg_eacl_20260627/06_release/submission_readiness_audit.json` |
| evaluation_or_gate | True |  | 6172 | `73e86e7b544861343752bcdf7431ccf7a001e632e75f494e87c16b08c236d1b2` | `experiments/cape_kg_eacl_20260627/06_release/submission_readiness_audit.md` |
| evaluation_or_gate | True |  | 58018 | `31ee4a6416fb8cf0b91ec0c378fddef36fe08cc6aa281b83bb8e152e6fc3ef3d` | `experiments/cape_kg_eacl_20260627/06_release/eacl_plan_compliance_matrix.json` |
| evaluation_or_gate | True |  | 34933 | `3ea4df34bf5fa194afc6cdd634047e5c220f4826241c3324746afa3ac08886ef` | `experiments/cape_kg_eacl_20260627/06_release/eacl_plan_compliance_matrix.md` |
| evaluation_or_gate | True |  | 3104 | `ba82c7a2aac3f761225d5d13b1afbb23f8d3c7d877e9105479b7a7b2eb0a60a0` | `experiments/cape_kg_eacl_20260627/06_release/paper_readiness_checklist.json` |
| evaluation_or_gate | True |  | 3974 | `3f78e4a5615f950418834e1b93573f6a9b1b682829ae632a27654c33de1b26f8` | `experiments/cape_kg_eacl_20260627/06_release/paper_readiness_checklist.md` |
| evaluation_or_gate | True |  | 15840 | `448492bbd2543ab4f6b55b6f9beb1d64780c0cbc92884f1a8947acdebd6b5b27` | `experiments/cape_kg_eacl_20260627/06_release/rq_evidence_matrix.json` |
| evaluation_or_gate | True |  | 14252 | `6db2ca0b9dd31a3aa6a459e5c49ce81b39a7b69fd83f355541e1dc931cf79144` | `experiments/cape_kg_eacl_20260627/06_release/rq_evidence_matrix.md` |
| evaluation_or_gate | True |  | 23051 | `b5bdf22b085c418283397c3a09d3e60e33956a022557ef50c367e2563efa85dc` | `experiments/cape_kg_eacl_20260627/06_release/reviewer_risk_register.json` |
| evaluation_or_gate | True | 13 | 5689 | `03e4756533aa3a7fbd963da297c493a030f11d2aba589f2752f3f574970425df` | `experiments/cape_kg_eacl_20260627/06_release/reviewer_risk_register.csv` |
| evaluation_or_gate | True |  | 17456 | `ce789584bafd3f8706c0e02f9a812bd47914f11f9d2ab115251fddcfc094bdec` | `experiments/cape_kg_eacl_20260627/06_release/reviewer_risk_register.md` |
| evaluation_or_gate | True |  | 12832 | `0c45a6e355b613ae0363ab1c1a8f4e99f5b3ba2a29842bf678ee83d42792ad1c` | `experiments/cape_kg_eacl_20260627/06_release/method_novelty_positioning.json` |
| evaluation_or_gate | True |  | 10144 | `081913cbee628a3840db92b803aece687eaf06dfc9a524dae8fc55d2a0a21888` | `experiments/cape_kg_eacl_20260627/06_release/method_novelty_positioning.md` |
| evaluation_or_gate | True |  | 53053 | `09d1505bcfaeb4c8a7f9f1fd52277f9d6c90415cfdc2819b747a3b182ba3c22b` | `experiments/cape_kg_eacl_20260627/06_release/cq_query_pack.json` |
| evaluation_or_gate | True |  | 29675 | `689fe8135194c4093d436f398fdf681d8c4868eb6b0e4a40e95879d23c877518` | `experiments/cape_kg_eacl_20260627/06_release/cq_query_pack.md` |
| evaluation_or_gate | True |  | 14924 | `c6574059d5f4f492a4fc0c3a1e9121255b8445e34477c6b96d04823d099b9b1d` | `experiments/cape_kg_eacl_20260627/06_release/paper_tables.md` |
| evaluation_or_gate | True |  | 14900 | `8b36482f74381a4ba95002b0020601008fa13600965ae08e7c6b4e5cce49b52e` | `experiments/cape_kg_eacl_20260627/06_release/paper_table_blueprint.json` |
| evaluation_or_gate | True |  | 12030 | `84185da33879db815699066f819ff5f72ef5b107f0a372d26e9808c24940faa7` | `experiments/cape_kg_eacl_20260627/06_release/paper_table_blueprint.md` |
| evaluation_or_gate | True |  | 20915 | `d55f7832be8c9ca2f78a6176de62531ab7567f5d82652ad8a504e9270ff0e004` | `experiments/cape_kg_eacl_20260627/06_release/paper_section_source_map.json` |
| evaluation_or_gate | True |  | 9141 | `8cc9c9e325d44358d76c7cef7880011797ef4d3e392aba4c07c3f1d4a4da859f` | `experiments/cape_kg_eacl_20260627/06_release/paper_section_source_map.md` |
| evaluation_or_gate | True |  | 27348 | `a377356905b86e14f691191c87c143c9aaec5506e49fd30bbb833d2c57f0aceb` | `experiments/cape_kg_eacl_20260627/06_release/eacl_submission_package_manifest.json` |
| evaluation_or_gate | True |  | 14120 | `c0e8fec276c6a96c19b3dd81c9bfd174ba71ccf5898ac04b7973d54d47f8fb73` | `experiments/cape_kg_eacl_20260627/06_release/eacl_submission_package_manifest.md` |
| evaluation_or_gate | True |  | 41215 | `4e34cb0af389697bc1f3421416e33d298b60ceb48e9946888c13e76740226020` | `experiments/cape_kg_eacl_20260627/06_release/post_human_scoring_readiness.json` |
| evaluation_or_gate | True |  | 7034 | `a8a492a18583b24fde1c576b0cf2f0070856c450778b26adf927b2b45b229dc7` | `experiments/cape_kg_eacl_20260627/06_release/post_human_scoring_readiness.md` |
| evaluation_or_gate | True |  | 38758 | `f4bd7dd4346fde404f1fd8793e0747e7d5e233eae5cc360e9af12fdb6b1ab886` | `experiments/cape_kg_eacl_20260627/06_release/submission_completion_audit_ko.json` |
| evaluation_or_gate | True |  | 25787 | `5728bb200061b41ed9234ac4ff9781e7691b986dcbf6aff03daae135b25e18c4` | `experiments/cape_kg_eacl_20260627/06_release/submission_completion_audit_ko.md` |
| evaluation_or_gate | True |  | 79600 | `0d58dda654e32bac9caa4bfed615dfb4c2340bd1faca536470836e1ad6732eda` | `experiments/cape_kg_eacl_20260627/06_release/pre_human_handoff_validation.json` |
| evaluation_or_gate | True |  | 24271 | `1737fed8390648670ba3327b4194679d6c397a82f77d40561101908ee1637ca6` | `experiments/cape_kg_eacl_20260627/06_release/prompt_node_edge_traceability.json` |
| evaluation_or_gate | True |  | 13157 | `c50cc61a6878e69da790753b7063fb69a3bef325ecb63ac09a12257a39309b0a` | `experiments/cape_kg_eacl_20260627/06_release/prompt_node_edge_traceability.md` |
| evaluation_or_gate | True |  | 36569 | `59251605fedcc76b9d2405d670260f2c1acba0125a99733fd4d9baabb2647db8` | `experiments/cape_kg_eacl_20260627/06_release/public_reproducibility_manifest.json` |
| evaluation_or_gate | True |  | 19910 | `02477a7fe458cd5d00761cde9aa6599f54deaa2bc54dbbc0576fc20097a18b57` | `experiments/cape_kg_eacl_20260627/06_release/public_reproducibility_manifest.md` |
| evaluation_or_gate | True | 102 | 17173 | `2da1e869f1c2d4e71e1a797505b55785bf0065ebfa63b4672b89b17489888b5e` | `experiments/cape_kg_eacl_20260627/06_release/public_reproducibility_manifest.csv` |
| evaluation_or_gate | True |  | 13075 | `ec6b2523d8c54298375cc06cf829b4c0b2e1b77dd97f0c5c2203b11d377bc84b` | `experiments/cape_kg_eacl_20260627/07_reports/README_current_reports_ko.md` |
| evaluation_or_gate | True |  | 23487 | `32b93fba808c3461b410004baeed9236ba65b1d6b356ea87125ed3f0c1502acf` | `experiments/cape_kg_eacl_20260627/07_reports/professor_report_core_essentials_prompt_cq_node_edge_separate_20260629_ko.md` |
| evaluation_or_gate | True |  | 20370 | `38a338530e635d462dd8834dcd8799ddcd2f256aaa5303af187cc3fadef61ef9` | `experiments/cape_kg_eacl_20260627/07_reports/professor_report_core_essentials_separate_from_slides_20260629_ko.md` |
| evaluation_or_gate | True |  | 16905 | `d3698730dece1ed8136e6cbb2baf0714a79d20b2463285e9c2f0597d19fb6916` | `experiments/cape_kg_eacl_20260627/07_reports/professor_report_core_summary_separate_from_slides_sync4_20260629_ko.md` |
| evaluation_or_gate | True |  | 22425 | `7dd77f1a73e0e3b7842c4cb54a025c7c8014f1a3e96fd1445de8716ac3da7fed` | `experiments/cape_kg_eacl_20260627/07_reports/professor_report_core_summary_separate_from_slides_latest_20260629_ko.md` |
| evaluation_or_gate | True |  | 21842 | `48ee170aae930dacd5a684c814b20a66917e9e9bcc8f80ccefee49cf96782d13` | `experiments/cape_kg_eacl_20260627/07_reports/professor_report_key_summary_separate_from_slides_20260629_ko.md` |
| evaluation_or_gate | True |  | 23857 | `fa44b4604753b88f532d684dab268b95d1144e8deed22b824a7db5a4e2c25a38` | `experiments/cape_kg_eacl_20260627/07_reports/professor_report_core_contents_separate_20260629_ko.md` |
| evaluation_or_gate | True |  | 19149 | `009b332e9a26ae1e0ba0d9148faf8b1f89d38c9b697f8589fcfa9503385c5f92` | `experiments/cape_kg_eacl_20260627/07_reports/professor_report_key_content_only_prompt_cq_node_edge_20260629_ko.md` |
| evaluation_or_gate | True |  | 17526 | `d68b4ec3f573e0b09f3633ed2307990c271e1c04937cdac70cb9cdb6c7f5dec0` | `experiments/cape_kg_eacl_20260627/07_reports/professor_report_core_summary_current_20260629_ko.md` |
| evaluation_or_gate | True |  | 61204 | `26a10ec851ebba108576682318d92a205715a4234af4b7afb3a3fcbb2ab485d2` | `experiments/cape_kg_eacl_20260627/07_reports/professor_report_slide_contents_current_20260628_ko.md` |
| evaluation_or_gate | True |  | 15244 | `7c1ae403e697a634623174a3df0df047b9835ca4fb1226bab8c039bb7fe351a6` | `experiments/cape_kg_eacl_20260627/07_reports/professor_report_core_essentials_prompt_cq_node_edge_20260628_ko.md` |
| evaluation_or_gate | True |  | 24350 | `840d018f8d7fb69e164445ead7ad6e0ebc2ce9fc00d6258185e6c84954145af5` | `experiments/cape_kg_eacl_20260627/07_reports/professor_report_core_separate_summary_prompt_cq_node_edge_20260628_ko.md` |
| evaluation_or_gate | True |  | 18761 | `fb3143466ba8e7595bd2023a2f28b15a597733736a0b0c64067624385fdcc7f1` | `experiments/cape_kg_eacl_20260627/07_reports/professor_report_core_brief_prompt_cq_node_edge_20260628_ko.md` |
| evaluation_or_gate | True |  | 22956 | `c072178f55bf771e15212ab19be36863b7fa3d4a569efac791b5d582eb3846ee` | `experiments/cape_kg_eacl_20260627/07_reports/professor_report_core_briefing_prompt_cq_node_edge_current_20260628_ko.md` |
| evaluation_or_gate | True |  | 20172 | `ac7b1a63eee2f27016e3e79f0bc8ef79767466ece5aac12190b217ae1777b9c2` | `experiments/cape_kg_eacl_20260627/07_reports/professor_report_core_summary_current_20260628_ko.md` |
| evaluation_or_gate | True |  | 21410 | `79a365bfe2cfee372f1fda4504c6f8872d4b87545b609dc8b08149ba066d34e2` | `experiments/cape_kg_eacl_20260627/07_reports/eacl_paper_draft.md` |

### human_review_files

| role | exists | records | bytes | sha256 | path |
|---|---:|---:|---:|---|---|
| human_review_handoff | True |  | 3677 | `907f0f706c30bc334d87052a54799cd01c51acc89fc491ecaea9c1ba2e3968ad` | `experiments/cape_kg_eacl_20260627/01_data/gold_annotation/annotation_package_manifest.json` |
| human_review_handoff | True |  | 645 | `2b4d501e5933e558f6157b60eb616a209242fb576980c404faf49cd10e2cdd3e` | `experiments/cape_kg_eacl_20260627/01_data/gold_annotation/annotation_manifest_sync_report.json` |
| human_review_handoff | True |  | 3903 | `b37670deaa78485006ed426093904b4c9395274e78974499d105fb5f3390f8ef` | `experiments/cape_kg_eacl_20260627/01_data/gold_annotation/annotation_expansion_manifest.json` |
| human_review_handoff | True |  | 2513 | `f22b3e7659c3c2a368022f245ac0c8d0caf1771df54443d7ac5844b21e0ace5d` | `experiments/cape_kg_eacl_20260627/01_data/gold_annotation/annotation_expansion_report.md` |
| human_review_handoff | True |  | 4684 | `c7ceef1a68d0df28910fae64552626b89dc9b2f870286407f73147bd8fc2c9e5` | `experiments/cape_kg_eacl_20260627/06_release/annotation_batch_review_preview_summary.json` |
| human_review_handoff | True |  | 2121 | `17a90830fd6e93c47f8b1242e5422101e6189ad42b8c2c8303d155c190481675` | `experiments/cape_kg_eacl_20260627/06_release/annotation_batch_review_preview_summary.md` |
| human_review_handoff | True | 5 | 1817 | `eed0f6bb2bae6a8e8d37776c5be9f91dae7843fae44e533298200924d9d2a95b` | `experiments/cape_kg_eacl_20260627/05_review/annotation_batch_review_preview_summary.csv` |
| human_review_handoff | True |  | 67903 | `1488ac713aa247007f12efda9e5a0017dbcc1bd0477f6aae655229bf6f3639ab` | `experiments/cape_kg_eacl_20260627/06_release/gold_sampling_coverage_report.json` |
| human_review_handoff | True |  | 4889 | `5ecb9186f3545c37de4aa24a10063185355699f9e9d88d383486c723f6f94b4e` | `experiments/cape_kg_eacl_20260627/06_release/gold_sampling_coverage_report.md` |
| human_review_handoff | True | 6 | 357 | `0ac26ad9bdfc13abd5f387c797e8cc442409d751113a970ee9e75535a4336b84` | `experiments/cape_kg_eacl_20260627/05_review/gold_sampling_coverage_by_chapter.csv` |
| human_review_handoff | True | 100 | 12535 | `eea150440fbcb890e9fac0860a25616873fe014aeb8ff66556dc76541fc6b4e7` | `experiments/cape_kg_eacl_20260627/05_review/gold_sampling_priority100_selected_chunks.csv` |
| human_review_handoff | True |  | 2043 | `ca46f617ace5397065184880523a279bd68634bfd5319ec34c7b73ec821f9ada` | `experiments/cape_kg_eacl_20260627/06_release/strong_resegmented_review_preview_summary.json` |
| human_review_handoff | True |  | 1370 | `7ba613e106ff044e00aaa21e6aa60780ffe6fe34bd41817f948fa6b5d7c643f2` | `experiments/cape_kg_eacl_20260627/06_release/strong_resegmented_review_preview_summary.md` |
| human_review_handoff | True | 1 | 623 | `12f895f7adc572a78b64c9042b030d830abffd467df101e911b0cd349a2600f6` | `experiments/cape_kg_eacl_20260627/05_review/strong_resegmented_review_preview_summary.csv` |
| human_review_handoff | True | 342 | 39502 | `9f4afbb42aab61b59848785ca583a8fe7fc7d2c54a2a07f3d44ef5c171db3b66` | `experiments/cape_kg_eacl_20260627/01_data/gold_annotation/strong_resegmented_342_max18/strong_review_preview.csv` |
| human_review_handoff | True |  | 9536 | `c9dd603c693e091f7362121f367fec17cfd05dc63379e04edca620e670914cc3` | `experiments/cape_kg_eacl_20260627/01_data/gold_annotation/strong_resegmented_342_max18/strong_review_preview.md` |
| human_review_handoff | True |  | 11795 | `e2f072df41a0c54834d90f42e5ab927559c4dc5033ca4719edc8150a14009e2f` | `experiments/cape_kg_eacl_20260627/06_release/human_review_return_preflight.json` |
| human_review_handoff | True |  | 3102 | `ef1cf1864b7b0cdb95445d08caa38c1c0380495db67ae11f370536f322156dd8` | `experiments/cape_kg_eacl_20260627/06_release/strong_review_return_preflight.json` |
| human_review_handoff | True |  | 2116 | `1ed1726b2196e18776cbffcb884a30990eb3a89de7f6e3d692814a6a18a90664` | `experiments/cape_kg_eacl_20260627/06_release/strong_review_return_preflight.md` |
| human_review_handoff | True |  | 1539 | `9531b67a024c052b694d4add9a3cb3d9cf71a40575f0bb7b7e51cda0204d9c34` | `experiments/cape_kg_eacl_20260627/06_release/strong_return_apply_last_run.json` |
| human_review_handoff | True |  | 1429 | `f675661ce2587a4d0625b664a6fc629893fc15fd0e09b2f2cc507a3ffa0c4494` | `experiments/cape_kg_eacl_20260627/06_release/strong_return_apply_last_run.md` |
| human_review_handoff | True |  | 891 | `af249055a99a9a7274f44fb8738b20206985c68334638489e11a30072e256dcc` | `experiments/cape_kg_eacl_20260627/06_release/strong_return_apply_refusal_last_run.json` |
| human_review_handoff | True |  | 877 | `b70696b38cbf6c94770a8c6d6407a143f9726586675ce7b8fc707a2c5c7b8ca0` | `experiments/cape_kg_eacl_20260627/06_release/strong_return_apply_refusal_last_run.md` |
| human_review_handoff | True |  | 1417 | `2d58bd21606df677f577f96c8ec0a75b7b8acb8fa7816dcb624b2de856a19d13` | `experiments/cape_kg_eacl_20260627/06_release/human_return_apply_last_run.json` |
| human_review_handoff | True |  | 1721 | `ee1820c7d53e6c59f63b937408250b1a1b3a75b7a84dc5db3fd83e97b8a6174c` | `experiments/cape_kg_eacl_20260627/06_release/human_return_apply_last_run.md` |
| human_review_handoff | True |  | 1227 | `07c3c8a18cf5712ec95092e14167f030ae79c6be213d71280b9e025090a7e9f6` | `experiments/cape_kg_eacl_20260627/06_release/human_return_apply_refusal_last_run.json` |
| human_review_handoff | True |  | 1146 | `b67aa0a366246c9200457183542f5bde00b62b2028ce1859f1e1b0fc1e143c04` | `experiments/cape_kg_eacl_20260627/06_release/human_return_apply_refusal_last_run.md` |
| human_review_handoff | True |  | 1670 | `9849e0da76559c067ae7b356f1d71bbc3813cd15aeee70577993bc962554582f` | `experiments/cape_kg_eacl_20260627/06_release/post_annotation_refresh_last_run.json` |
| human_review_handoff | True |  | 117002 | `27b18e20dfb144415322715a22329193e728d6f2bdc93e43daaaed4f727a846b` | `experiments/cape_kg_eacl_20260627/06_release/human_gate_action_plan.json` |
| human_review_handoff | True |  | 18799 | `52ab0fa8be977a6914e015fdf768544e336e5a273dcedac7c7d4ba1396d460d7` | `experiments/cape_kg_eacl_20260627/06_release/human_gate_action_plan.md` |
| human_review_handoff | True |  | 38205 | `928244780a5e513981c5012861c7d33662dd6b3dba52f13263836caad9b177c7` | `experiments/cape_kg_eacl_20260627/06_release/human_review_master_checklist_ko.json` |
| human_review_handoff | True |  | 15446 | `f333cbc4c9c62b759739c9902d89cd1777596129723a73ba4f4c291284174e1d` | `experiments/cape_kg_eacl_20260627/06_release/human_review_master_checklist_ko.md` |
| human_review_handoff | True |  | 10518 | `4ad1d0d81e48747db680e0752285dafa2662a4b30e7472c21745ce169d9a6d70` | `experiments/cape_kg_eacl_20260627/05_review/human_review_first_batch_execution_card.json` |
| human_review_handoff | True |  | 5593 | `3e3368b49319b8e927414b772bcb98a8908eea719d01d99a8cccc0dfd1c30b9a` | `experiments/cape_kg_eacl_20260627/05_review/human_review_first_batch_execution_card_ko.md` |
| human_review_handoff | True |  | 28002 | `996684bd5ca2096b0a6af6cdb51358ec8c5a766d2d4d6f9dbefc09248983eaeb` | `experiments/cape_kg_eacl_20260627/05_review/human_review_role_quickstart_cards.json` |
| human_review_handoff | True |  | 19591 | `7a9b942fb762bd70ed17301209e574d133f803f20e57800b9e1c94e602493091` | `experiments/cape_kg_eacl_20260627/05_review/human_review_role_quickstart_cards_ko.md` |
| human_review_handoff | True | 9 | 4609 | `1f62291f0f031ef36f255d6d758b102c816566921bda692aeb2948e61132f062` | `experiments/cape_kg_eacl_20260627/05_review/human_review_role_quickstart_cards.csv` |
| human_review_handoff | True |  | 36382 | `932f484c4ed8812f826bd4ae756bcb8708fc0d308b50787e05b39dc1445780e2` | `experiments/cape_kg_eacl_20260627/06_release/human_review_status_dashboard_ko.json` |
| human_review_handoff | True |  | 12146 | `dabc3c39c6fe7347853c89a9948694d402d6c626e31ae985ac61e8660a99115b` | `experiments/cape_kg_eacl_20260627/06_release/human_review_status_dashboard_ko.md` |
| human_review_handoff | True |  | 26208 | `bbfddba80cfaaf012f4387b6bd1b5f2f8640767261edb098c1c081f2db33fad9` | `experiments/cape_kg_eacl_20260627/06_release/human_review_launch_checklist_ko.json` |
| human_review_handoff | True |  | 12049 | `7307cda43cdb7bd53060a37dc9f1d7049d934d0f428342adcc8dfdde35f12e1f` | `experiments/cape_kg_eacl_20260627/06_release/human_review_launch_checklist_ko.md` |
| human_review_handoff | True |  | 14261 | `af5ebe34e75434d9615be4acbda8e83390e6572fb82bb769fd8cfa2f8f5e69f5` | `experiments/cape_kg_eacl_20260627/06_release/human_review_packet_integrity.json` |
| human_review_handoff | True |  | 2505 | `73b9747b9cdfb3163ff7563287b84f1203e60f6930a00522f996ba223a29c014` | `experiments/cape_kg_eacl_20260627/06_release/human_review_packet_integrity.md` |
| human_review_handoff | True |  | 1880 | `2260a071c5744088e83c8d064d077aae738c15cf524b66745c33645b243bbb89` | `experiments/cape_kg_eacl_20260627/06_release/active_review_human_effort_briefing.json` |
| human_review_handoff | True |  | 15523 | `87b884c8bb3e24ff53244cae1e72c277e55b810b3fc6276bd0d713838dcf2d8f` | `experiments/cape_kg_eacl_20260627/06_release/active_review_human_effort_briefing.md` |
| human_review_handoff | True | 14 | 7485 | `a4f43d62e763076e3bb38d56e0107f42ad5b16e812dba6a8ffb6cfd256294671` | `experiments/cape_kg_eacl_20260627/05_review/human_gate_required_returns.csv` |
| human_review_handoff | True | 7 | 13358 | `2cd042ebdd177d73043d68e2013337736461ec278aeddcadf0b9ee30be962266` | `experiments/cape_kg_eacl_20260627/05_review/human_review_gate_dependency_matrix.csv` |
| human_review_handoff | True | 16 | 8192 | `6a39e87aaba4d95a2c9789042cda56835e71ae3a70b887954abcabe5cd018d71` | `experiments/cape_kg_eacl_20260627/05_review/human_review_master_return_files.csv` |
| human_review_handoff | True | 0 | 53 | `8341fb3e032e5c01a7b796fcbba212c2eb733082b29ee49673cfac60ceab145e` | `experiments/cape_kg_eacl_20260627/05_review/human_review_packet_integrity_issues.csv` |
| human_review_handoff | True | 9 | 3578 | `b77bbbd3a90950bcfcf343802fa5d86c2df385ce5d8727610dbc97342acbd7b9` | `experiments/cape_kg_eacl_20260627/05_review/human_review_status_next_actions.csv` |
| human_review_handoff | True | 18 | 8698 | `7f93e4dd1d6fd600d6bdb86755f6c3dbc93d6bb825aa3f51ffd86e207f813cd2` | `experiments/cape_kg_eacl_20260627/05_review/human_review_minimum_gate_launch_tasks.csv` |
| human_review_handoff | True | 204 | 98684 | `70fdd580c16a171e2a245d0b0c1fbebb470a0414fa6def4e3cb2dcc0de0c78f8` | `experiments/cape_kg_eacl_20260627/05_review/active_review_human_effort_briefing.csv` |
| human_review_handoff | True |  | 1619 | `14747fa1007491668b4906ccf53399b428c436561e0d9b5e1db5493f58e653bb` | `experiments/cape_kg_eacl_20260627/01_data/mapping_review/mapping_review_manifest.json` |
| human_review_handoff | True |  | 119714 | `2a416554886de80e01b82b7bfc1658cb3f2e2181e85da2bd0577ddd88eef764b` | `experiments/cape_kg_eacl_20260627/06_release/mapping_review_group_briefing.json` |
| human_review_handoff | True |  | 29653 | `bd33d8c3f776cab1bb315b3f8f079c56d53ce504f6e5ef2cc2ba54a2140954df` | `experiments/cape_kg_eacl_20260627/06_release/mapping_review_group_briefing.md` |
| human_review_handoff | True | 100 | 56828 | `50507d5e9c1518e24e273e4f195a475aa7683423ea8430d7d939f292ff661e5b` | `experiments/cape_kg_eacl_20260627/05_review/mapping_review_group_briefing_top20.csv` |
| human_review_handoff | True |  | 16713 | `614c91d01d0fb4bb86c99ff245a22c07603767af6a70fddc94bcb5502f6c8959` | `experiments/cape_kg_eacl_20260627/06_release/human_review_handoff/human_review_handoff_manifest.json` |
| human_review_handoff | True |  | 3374 | `af63954463605603905be87a450135e48d825623451944b205fac139bd8b2f04` | `experiments/cape_kg_eacl_20260627/06_release/human_review_handoff/human_review_handoff_report.md` |
| human_review_handoff | True |  | 1587 | `4f479bdfd74b3d31feeaefb833d2c47f85625b8979f9f5c3d7c9f046c508aef4` | `experiments/cape_kg_eacl_20260627/06_release/human_review_handoff/human_review_handoff_checksums.sha256` |
| human_review_handoff | True |  | 7314 | `c3f760ce4bf9f68d07f6e21979448313e251f75993238d5ddbe5aa00ec25f452` | `experiments/cape_kg_eacl_20260627/06_release/human_review_handoff/README_strong_resegmented_review_ko.md` |
| human_review_handoff | True |  | 2070 | `57b59461cc48862fe750804c0fd3beb83dd81b9751a6317a847babad14b0a406` | `experiments/cape_kg_eacl_20260627/06_release/human_review_handoff/strong_resegmented_review_manifest.json` |
| human_review_handoff | True | 342 | 3886436 | `1069470ba4f6bfab96afdff40f0fb72097020a108e34c1ee70a53ebc23e2db81` | `experiments/cape_kg_eacl_20260627/01_data/gold_annotation/strong_resegmented_342_max18/annotator_A.jsonl` |
| human_review_handoff | True | 342 | 3886436 | `5086bbfaac7282cdbbceb45e45638476495b5baea6e5775f77abec78132e5de2` | `experiments/cape_kg_eacl_20260627/01_data/gold_annotation/strong_resegmented_342_max18/annotator_B.jsonl` |
| human_review_handoff | True | 342 | 716895 | `a47fea5d2a279bccfe032baefe27a7b9f99264d23b474d44f9de7ea849cd70c5` | `experiments/cape_kg_eacl_20260627/01_data/gold_annotation/strong_resegmented_342_max18/adjudication.jsonl` |
| human_review_handoff | True | 342 | 718605 | `3a8853539b762e303902352729222ceb9e979892784e7e43ce532c9e6d85cb6b` | `experiments/cape_kg_eacl_20260627/01_data/gold_annotation/strong_resegmented_342_max18/adjudication_draft.jsonl` |
| human_review_handoff | True | 342 | 83783 | `c405e132a6fe2ac0ce495bfa00739409ee51e0314fc507aebd0404c4de50e124` | `experiments/cape_kg_eacl_20260627/01_data/gold_annotation/strong_resegmented_342_max18/tracking_sheet.csv` |
| human_review_bundle:active_review_effort | True |  | 136671 | `179c683580de5cd72acaeddd68c5fc882e6609bf3c1a8568c5474007da4bf5f1` | `experiments/cape_kg_eacl_20260627/06_release/human_review_handoff/cape_active_review_human_effort.tar.gz` |
| human_review_bundle:adjudicator | True |  | 284553 | `718e5dfb9954cfa0b510d318f64a976ecda027d14f190bb0e7f22b21fffd3be6` | `experiments/cape_kg_eacl_20260627/06_release/human_review_handoff/cape_human_gold_adjudicator_full120.tar.gz` |
| human_review_bundle:annotator_A | True |  | 431579 | `28d47a6f9b479c054ddbc886fe15f365b8389f6183a34ce7a2170d894704c87e` | `experiments/cape_kg_eacl_20260627/06_release/human_review_handoff/cape_human_gold_annotator_A_priority100.tar.gz` |
| human_review_bundle:annotator_B | True |  | 431580 | `8ddd97bd64f4d2e0e381abb09ebd0cd46bfa3430a77a8dcc382a9001bb43da85` | `experiments/cape_kg_eacl_20260627/06_release/human_review_handoff/cape_human_gold_annotator_B_priority100.tar.gz` |
| human_review_bundle:coordinator | True |  | 679139 | `26d98f4b8f1a663d940a9287ec4cb17c50004b5cb6b547054c6e522d219b9eca` | `experiments/cape_kg_eacl_20260627/06_release/human_review_handoff/cape_human_gold_coordinator_priority100.tar.gz` |
| human_review_bundle:crosswalk_expert | True |  | 120421 | `36296fd089d95cab4ad3d6e4ecc1a514d2aeb2e31313b9e61a04d4854eade749` | `experiments/cape_kg_eacl_20260627/06_release/human_review_handoff/cape_crosswalk_expert_review_ncs_pcf.tar.gz` |
| human_review_bundle:mapping_expert | True |  | 148030 | `838ace64502a71c04b4e9866230d1ab455307aefdd23a7a5b7fc5e0ea96a4329` | `experiments/cape_kg_eacl_20260627/06_release/human_review_handoff/cape_mapping_expert_review_top20_groups.tar.gz` |
| human_review_bundle:strong_resegmented_review | True |  | 1155271 | `7f5449d1df34fc4ac8c58eb058c4f5b52bcaaab5215cc98dba160841585446e0` | `experiments/cape_kg_eacl_20260627/06_release/human_review_handoff/cape_human_gold_strong_resegmented_342.tar.gz` |
| human_review_bundle:structural_reviewer | True |  | 87208 | `6018d90a8ed5f5a9384cfc9a335553d79000e0512b8edbe45006da15878ab3d3` | `experiments/cape_kg_eacl_20260627/06_release/human_review_handoff/cape_structural_review_optional.tar.gz` |

### release_files

| role | exists | records | bytes | sha256 | path |
|---|---:|---:|---:|---|---|
| release_or_reproducibility | True |  | 400028 | `4b5c0925536c2887da09c50ec956e983d9d0a1470feb89a61097d1d1138a649f` | `experiments/cape_kg_eacl_20260627/06_release/reproducibility_manifest.json` |
| release_or_reproducibility | True |  | 36569 | `59251605fedcc76b9d2405d670260f2c1acba0125a99733fd4d9baabb2647db8` | `experiments/cape_kg_eacl_20260627/06_release/public_reproducibility_manifest.json` |
| release_or_reproducibility | True |  | 19910 | `02477a7fe458cd5d00761cde9aa6599f54deaa2bc54dbbc0576fc20097a18b57` | `experiments/cape_kg_eacl_20260627/06_release/public_reproducibility_manifest.md` |
| release_or_reproducibility | True | 102 | 17173 | `2da1e869f1c2d4e71e1a797505b55785bf0065ebfa63b4672b89b17489888b5e` | `experiments/cape_kg_eacl_20260627/06_release/public_reproducibility_manifest.csv` |
| release_or_reproducibility | True |  | 85790 | `4d071c39568cd9b3cedb66ea7bda52dffaa14520f75e0156a174115c499a6870` | `experiments/cape_kg_eacl_20260627/06_release/anonymized_submission_prep.json` |
| release_or_reproducibility | True |  | 17046 | `5139227f553a9ddeed9a21b9e01ef3f4ad02d5263e43320887ae870963364d5e` | `experiments/cape_kg_eacl_20260627/06_release/anonymized_submission_prep.md` |
| release_or_reproducibility | True | 200 | 57075 | `f30387c79748adb3610148c468d95c77a3bfb7609fd29d761ee89d052c8a888c` | `experiments/cape_kg_eacl_20260627/06_release/anonymized_submission_risk_scan.csv` |
| release_or_reproducibility | True |  | 17320 | `5a5cc928fed2961bbfa94f756088147bc4b2ca12a27e61395bc179bcbb6ca254` | `experiments/cape_kg_eacl_20260627/06_release/responsible_nlp_checklist_prep.json` |
| release_or_reproducibility | True |  | 14584 | `011812f14a9f0a3ce4992c4bdb094383d219ccbd2689cb0e56d8cafed096d4e6` | `experiments/cape_kg_eacl_20260627/06_release/responsible_nlp_checklist_prep.md` |
| release_or_reproducibility | True | 10 | 8934 | `bd40871ee013d8eb243621de3016351e5c10782853cfad00f0e18129fc20b43c` | `experiments/cape_kg_eacl_20260627/06_release/responsible_nlp_checklist_items.csv` |
| release_or_reproducibility | True |  | 25386 | `5ecec8fb6c90e324d71f8e5602f6b19705f230bbe8a330a4e312361827095542` | `experiments/cape_kg_eacl_20260627/06_release/experiment_reproduction_card.json` |
| release_or_reproducibility | True |  | 13855 | `aeef4e27c54994085265554fbeded68cb733d4ee7147fb2491b7d3ee60613cc8` | `experiments/cape_kg_eacl_20260627/06_release/experiment_reproduction_card.md` |
| release_or_reproducibility | True | 14 | 6136 | `a7b960ef88f2fa95e6e153b513bdae503364c6d3dce3ea315a67dcb008128f52` | `experiments/cape_kg_eacl_20260627/06_release/experiment_reproduction_conditions.csv` |
| release_or_reproducibility | True |  | 6315 | `67f9a35aff5c1da5d7a0adde3da01dc002df6343157c7ed2aa9b0bdddac39788` | `experiments/cape_kg_eacl_20260627/06_release/data_release_ethics_statement.md` |
| release_or_reproducibility | True |  | 6818 | `4f8ee8f339ab869fbb817e7006ba7d81be2d25652c9e698e49dbb28d5a4311a7` | `experiments/cape_kg_eacl_20260627/06_release/external_resource_license_report.json` |
| release_or_reproducibility | True | 6 | 3710 | `a84177fb479d33459377209aa2891f1dd7a63102ac3376a7a4b34ec1d98f82e4` | `experiments/cape_kg_eacl_20260627/06_release/external_resource_license_report.csv` |
| release_or_reproducibility | True |  | 2807 | `45631c20380f7a6a1c3c86265f346c6186c022a813294326d137c845e1c435dd` | `experiments/cape_kg_eacl_20260627/06_release/external_resource_license_report.md` |
| release_or_reproducibility | True |  | 27469 | `34bf7f8304cc435ec72d8df96b5a05c8ee037dae2a1a6deb6708a52e3f359852` | `experiments/cape_kg_eacl_20260627/06_release/evaluation_protocol_lock.json` |
| release_or_reproducibility | True |  | 19847 | `4ef3b2166e4e7ae303c9d858fcef6169b010c20a6a1ee0f2ed14aa3fae77391e` | `experiments/cape_kg_eacl_20260627/06_release/evaluation_protocol_lock.md` |
| release_or_reproducibility | True |  | 5114 | `b77341f5ae984238b43d3c056a1fb1f265d78046def3443469832d2f5dc1a020` | `experiments/cape_kg_eacl_20260627/06_release/latest_release_bundle_index.json` |
| release_or_reproducibility | True |  | 2061 | `bf678ea7de283f052e50d0bd96592287165ef879d9e6bd96d6cc5efab7814f2a` | `experiments/cape_kg_eacl_20260627/06_release/latest_release_bundle_index.md` |
| release_or_reproducibility | True |  | 4684 | `c7ceef1a68d0df28910fae64552626b89dc9b2f870286407f73147bd8fc2c9e5` | `experiments/cape_kg_eacl_20260627/06_release/annotation_batch_review_preview_summary.json` |
| release_or_reproducibility | True |  | 2121 | `17a90830fd6e93c47f8b1242e5422101e6189ad42b8c2c8303d155c190481675` | `experiments/cape_kg_eacl_20260627/06_release/annotation_batch_review_preview_summary.md` |
| release_or_reproducibility | True |  | 67903 | `1488ac713aa247007f12efda9e5a0017dbcc1bd0477f6aae655229bf6f3639ab` | `experiments/cape_kg_eacl_20260627/06_release/gold_sampling_coverage_report.json` |
| release_or_reproducibility | True |  | 4889 | `5ecb9186f3545c37de4aa24a10063185355699f9e9d88d383486c723f6f94b4e` | `experiments/cape_kg_eacl_20260627/06_release/gold_sampling_coverage_report.md` |
| release_or_reproducibility | True |  | 2043 | `ca46f617ace5397065184880523a279bd68634bfd5319ec34c7b73ec821f9ada` | `experiments/cape_kg_eacl_20260627/06_release/strong_resegmented_review_preview_summary.json` |
| release_or_reproducibility | True |  | 1370 | `7ba613e106ff044e00aaa21e6aa60780ffe6fe34bd41817f948fa6b5d7c643f2` | `experiments/cape_kg_eacl_20260627/06_release/strong_resegmented_review_preview_summary.md` |
| release_or_reproducibility | True |  | 36382 | `932f484c4ed8812f826bd4ae756bcb8708fc0d308b50787e05b39dc1445780e2` | `experiments/cape_kg_eacl_20260627/06_release/human_review_status_dashboard_ko.json` |
| release_or_reproducibility | True |  | 12146 | `dabc3c39c6fe7347853c89a9948694d402d6c626e31ae985ac61e8660a99115b` | `experiments/cape_kg_eacl_20260627/06_release/human_review_status_dashboard_ko.md` |
| release_or_reproducibility | True |  | 26208 | `bbfddba80cfaaf012f4387b6bd1b5f2f8640767261edb098c1c081f2db33fad9` | `experiments/cape_kg_eacl_20260627/06_release/human_review_launch_checklist_ko.json` |
| release_or_reproducibility | True |  | 12049 | `7307cda43cdb7bd53060a37dc9f1d7049d934d0f428342adcc8dfdde35f12e1f` | `experiments/cape_kg_eacl_20260627/06_release/human_review_launch_checklist_ko.md` |
| release_or_reproducibility | True |  | 2110 | `3aa50a1f3ac6efb29b42463f4948c759f4b93e8a458194c7277a424751b9f974` | `experiments/cape_kg_eacl_20260627/06_release/release_bundle_safety_report.md` |
| release_or_reproducibility | True | 0 | 36 | `73c63625458ed28a6bf27a71548deb1d7b6abb64b5c76bed20e8b22448b482ce` | `experiments/cape_kg_eacl_20260627/06_release/public_external_release_review_queue.csv` |
| release_or_reproducibility | True |  | 1112 | `dae577a6200841bc61846c30108f94767b26bf678348c9c008cbfefe2fa414f2` | `experiments/cape_kg_eacl_20260627/06_release/public_external_release_review_queue.md` |
| release_or_reproducibility | True |  | 969 | `da67b80596de9bc272df8bfcae2b020d43622c5b7c5ecb36483e4f842f751c1a` | `experiments/cape_kg_eacl_20260627/06_release/public_synthetic_examples/README.md` |
| release_or_reproducibility | True |  | 1126 | `b6bb240cdd930626333a90be4a5d6ac72eadf1b503deee23671cbaa23651e829` | `experiments/cape_kg_eacl_20260627/06_release/public_synthetic_examples/synthetic_evaluation_summary.json` |

## Interpretation

- Use `provenance_llm_run_index.csv` to trace LLM raw outputs, validated outputs, quality reports, models, conditions, and parse-repair counts.
- Use this manifest with release checksums to reproduce the exact pre-human experiment package.
- Human-gold labels, IAA, adjudication, expert mapping decisions, and active-review effort remain external human-return evidence until reviewed files are imported.
