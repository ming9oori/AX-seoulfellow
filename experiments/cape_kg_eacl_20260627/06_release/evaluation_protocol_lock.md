# CAPE-KG Evaluation Protocol Lock

Generated: 2026-06-29T19:07:57.506678+00:00
Claim status: `evaluation_protocol_locked_pending_human_returns`
Protocol version: `cape-eacl-evaluation-protocol-v1`
Protocol content SHA256: `5109c0b85d791c93ec78cae1f02547b5622dfd7990c8e7ccd005d249ced5c51d`

This file freezes the evaluation protocol before human returns are imported. It is reproducibility evidence, not a final performance claim.

## Claim Gate Policy

- No-substitution policy: Silver/proxy diagnostics, smoke tests, and model-generated labels cannot substitute for adjudicated human-gold or expert-review evidence.
- Required gate IDs: `data.eval_chunks, gold.completed_chunks, gold.item_count, gold.iaa, llm.baselines, llm.proposed_generation, llm.proposed_human_gold_score, llm.ablations, external.public_subset, analysis.error_analysis, release.artifacts`

## Current Context Snapshot

These values document the current pre-human state and are intentionally outside the protocol content hash. The pre-human validation value is the previous on-disk validator result at lock-generation time, not an input to the current validation pass.

- Current claim gate: `FAIL`
- Current readiness: `pending_human_gold_iaa_and_human_gold_scoring`
- Current pre-human validation: `PASS`

## Human-Dependent Blockers

- `human_gold_chunks`
- `human_gold_items`
- `two annotator agreement`
- `human_gold_scoring_for_proposed_method`
- `mapping_expert_review_for_downstream_claims`
- `crosswalk_expert_review_for_bridge_utility_claims`
- `active_review_effort_timing_for_efficiency_claims`

## Frozen Condition Sets

| set | conditions |
|---|---|
| main | `B0_plain_llm, B1_predicate_constrained, B2_current_project, B3_edc_style, B4_taxonomy_rag, B5_procedural_prompt, B6_sac_kg_verifier_pruner, P_cape_kg_actual, P_minus_CQ, P_minus_Evidence, P_minus_Procedural_schema, P_minus_Schema_retrieval, P_minus_Standard_bridge, P_minus_Validator` |
| qwen3_14b | `B0_plain_llm, B1_predicate_constrained, B2_current_project, P_cape_kg_actual` |
| qwen3_32b_awq | `B0_plain_llm, B1_predicate_constrained, B2_current_project, P_cape_kg_actual` |

## Metric Definitions

### human_gold_core

| metric | unit | source |
|---|---|---|
| `node_label_f1` | condition | human-gold scored outputs |
| `edge_exact_f1` | condition | human-gold scored outputs |
| `predicate_f1` | condition | human-gold scored outputs |
| `evidence_exact_or_f1` | condition | human-gold evidence anchors |
| `component_span_exact_match` | subject/predicate/object component | adjudicated spans |
| `component_span_iou` | subject/predicate/object component | adjudicated spans |

### structural

| metric | unit | source |
|---|---|---|
| `ontology_conformance` | KG | domain/range/schema validation |
| `procedural_consistency` | KG | cycle, gateway, artifact-flow checks |
| `cq_answerability` | competency question | graph-query answerability |

### mapping_expert

| metric | unit | source |
|---|---|---|
| `expert_accept_rate` | standard |  |
| `hit_at_1` | standard |  |
| `hit_at_3` | standard |  |
| `hit_at_5` | standard |  |
| `precision_at_5` | standard |  |
| `mrr` | standard |  |
| `ndcg_at_10` | standard |  |
| `explanation_quality_score_mean` | standard |  |

### crosswalk_expert

| metric | unit | source |
|---|---|---|
| `expert_accept_rate` | NCS-PCF source-task group |  |
| `hit_at_1` | NCS-PCF source-task group |  |
| `hit_at_3` | NCS-PCF source-task group |  |
| `hit_at_5` | NCS-PCF source-task group |  |
| `precision_at_10` | NCS-PCF source-task group |  |
| `mrr` | NCS-PCF source-task group |  |
| `ndcg_at_10` | NCS-PCF source-task group |  |
| `utility_grade_mean` | candidate row |  |
| `explanation_quality_score_mean` | candidate row |  |

### active_review_effort

| metric | unit | source |
|---|---|---|
| `review_seconds` | review row |  |
| `corrections_per_hour` | review arm |  |
| `high_impact_corrections_per_hour` | review arm |  |

## Locked Public Files

These files define the protocol, prompts, evaluators, wrappers, and validators included in the protocol hash.

| role | exists | bytes | sha256 | path |
|---|---:|---:|---|---|
| revised_plan | True | 29461 | `1e7c38dd29317524f2570b86f21cc6e5c659817c71fd160ab6dcd008e4324ccc` | `AX_EACL_submission_review_revised_plan.md` |
| cape_schema | True | 3523 | `55ce9947e4240e781c52f25f0e6f6142aa7b1572eca9d4e50ae3c9cb7296b0d6` | `experiments/cape_kg_eacl_20260627/02_schema/cape_schema.json` |
| prompt_contract | True | 664 | `699c4aa6927dc3bccf72a9906e2aa8a40a7e5e2493d18ebcb4f000251bdfd783` | `experiments/cape_kg_eacl_20260627/02_schema/prompts/strict_json_contract.txt` |
| baseline_prompt_b0 | True | 75 | `ad219b0e42adf3e2ccfa342ae38dce49fb74dbd7ae0fbdf5a59598f4a24b031f` | `experiments/cape_kg_eacl_20260627/02_schema/prompts/B0_plain_llm_triple_extraction.txt` |
| baseline_prompt_b1 | True | 96 | `a453b6587e8b3e03e2839874cc1fff8f6e1a249a83ec59ede8453f3a16a41651` | `experiments/cape_kg_eacl_20260627/02_schema/prompts/B1_predicate_constrained_llm.txt` |
| baseline_prompt_b2 | True | 77 | `9a639be66c6b2a3727078108143f4e65ccb22ed69a2c5d29b891ac19a452cf4a` | `experiments/cape_kg_eacl_20260627/02_schema/prompts/B2_current_project_baseline.txt` |
| baseline_prompt_b3 | True | 111 | `d272d5d4a9463b5cbc8225a7f754e715675787a5e347d15903c9d5ad0b020ee2` | `experiments/cape_kg_eacl_20260627/02_schema/prompts/B3_edc_style_baseline.txt` |
| baseline_prompt_b4 | True | 96 | `158bb086cd403a70c995049d0dd43573f94dc904e63ff179c093c95a40cf30fd` | `experiments/cape_kg_eacl_20260627/02_schema/prompts/B4_taxonomy_rag_baseline.txt` |
| baseline_prompt_b5 | True | 104 | `7b435cf341de2b892b8221641ff14049d6d895d4d9b6303397805406f63c71b3` | `experiments/cape_kg_eacl_20260627/02_schema/prompts/B5_procedural_prompt_baseline.txt` |
| baseline_prompt_b6 | True | 182 | `8ae83e345b52d39328da78a6a7cfbf65d5945fe7a061daf6adedfa6a793ab88a` | `experiments/cape_kg_eacl_20260627/02_schema/prompts/B6_sac_kg_verifier_pruner_baseline.txt` |
| proposed_prompt | True | 206 | `55511f96c5c8440216baa973ff4b8fb80d5d952ec7f4d91bc91c75a9c6496e71` | `experiments/cape_kg_eacl_20260627/02_schema/prompts/P_cape_kg.txt` |
| ablation_prompt_minus_schema_retrieval | True | 148 | `87f8d1d5403a9d32da879ea76f073fc066c13369e086f788428c3dafb2edfbf0` | `experiments/cape_kg_eacl_20260627/02_schema/prompts/P_minus_Schema_retrieval.txt` |
| human_gold_evaluator | True | 57230 | `8ab22558c09d36880430347a3706a24faec5a05af016cb8bb3ed0359a807a573` | `scripts/evaluate_cape_human_gold.py` |
| span_iou_evaluator | True | 17134 | `c1c1e8a838a80bd8e579689c83b683d0906a1ee95372f34be35fe0bdceb90aa7` | `scripts/evaluate_cape_human_gold_span_iou.py` |
| mapping_review_evaluator | True | 11251 | `33c5467fd0e3204ad70595af1f3f6d516b8d3562864bedfd476b1de877b8b367` | `scripts/evaluate_cape_mapping_review.py` |
| crosswalk_review_evaluator | True | 10995 | `0c4e2df5a1858a655bab15b507e29dbc4463cf504fc284c2e5df94f6e09611da` | `scripts/evaluate_cape_crosswalk_review.py` |
| active_effort_evaluator | True | 29575 | `e4c291b5507b976842a6b963b1b1e181e55025ff2e91ade4e87269b13af73fad` | `scripts/build_cape_active_review_human_effort.py` |
| ablation_coverage_builder | True | 22327 | `02b531584f8386c16ed36645f7817b89c41acdb50244d5df03d961a075b71615` | `scripts/build_cape_ablation_coverage_report.py` |
| alias_canonicalization_builder | True | 23558 | `dd583b5114e4ccc738e65a5785148035f557808ff0d88b8138e48c0accf63961` | `scripts/build_cape_alias_canonicalization_report.py` |
| annotation_calibration_builder | True | 11773 | `173e7e1d44553f9b5d109579a6b79ccc21ef6def3644bd7c8b9386dac2a825ee` | `scripts/build_cape_annotation_calibration_pack.py` |
| statistical_analysis | True | 15939 | `fa0e378e77955556b60449b4a8ebdd9665d4c53e42e5f1ddb5316fea48fc0f8d` | `scripts/compute_cape_statistical_analysis.py` |
| return_preflight | True | 47143 | `0202a83a929c09cf0fede0011381b9f96567443c7d2edcdc8a660ab20880c3f1` | `scripts/validate_cape_human_review_returns.py` |
| human_return_wrapper | True | 18531 | `3a82c23f550bdcd5949b430dfb682508d6ce27be2a5c9512e37889958bcac165` | `scripts/run_cape_human_return_apply.sh` |
| post_annotation_refresh_wrapper | True | 49877 | `918cf3a428916e20d7b2ef3fd0d59c976a2e547dc338cd5f486e13f573f10e7a` | `scripts/run_cape_post_annotation_refresh.sh` |
| pre_human_handoff_validator | True | 693231 | `0d96d8a53e80b457367c78fbc4edf04a3882090195566b8dc059fea9822c31ef` | `scripts/validate_cape_pre_human_handoff.py` |
| release_bundle_builder | True | 34786 | `3a3241aa13d5fb88487178a18a158c7ed00a146f3a3fc90be1491c4b2b752f16` | `scripts/build_cape_release_bundle.py` |
| provenance_manifest_builder | True | 31158 | `d623c5f1c7e53042ec30909c42f2708ab4d7455de2f7c3d75c468dab642d96f9` | `scripts/build_cape_provenance_manifest.py` |
| schema_retrieval_coverage_builder | True | 25263 | `172ce4748b6910ebfab11de329a10387aa824ddc03c53650fd415a7b17fc2d20` | `scripts/build_cape_schema_retrieval_coverage_report.py` |
| arr_submission_policy_checklist_builder | True | 19062 | `83f684e532ed963e0367406b03f450551d4d59679b218111b73da4c7b69af854` | `scripts/build_cape_arr_submission_policy_checklist.py` |
| anonymized_submission_prep_builder | True | 15057 | `6b390b2606e5bc4bb9914e27ec1f957fdab45261a0d4d9c1e792b0f3d0edc44a` | `scripts/build_cape_anonymized_submission_prep.py` |
| responsible_nlp_checklist_prep_builder | True | 22962 | `40bdf4a8cdb95b86f737e9d11188a8a932d0497a66f9a49da0cd9fe4148bc18e` | `scripts/build_cape_responsible_nlp_checklist_prep.py` |
| experiment_reproduction_card_builder | True | 23330 | `e0396cedea1e572f1ee18d3a61ab37ba64af72a621bec61067fdef8c4d003292` | `scripts/build_cape_experiment_reproduction_card.py` |
| evidence_graph_projection_builder | True | 12065 | `2ea0e45b51612e0bf1fc5b3da8821f5fbe716c4e9a67e8c4e4aba480df592884` | `scripts/build_cape_evidence_graph_projection.py` |
| neo4j_evidence_query_pack_builder | True | 17764 | `919f4b267f16b8fb7547bd6de90808a52d67440064463c17db8d857182274ddf` | `scripts/build_cape_neo4j_evidence_query_pack.py` |
| paper_table_blueprint_builder | True | 18240 | `80d2571f0079ddd54ebe87ec4e174e1b7e181a445114e08f27374290a836921b` | `scripts/build_cape_paper_table_blueprint.py` |
| method_novelty_positioning_builder | True | 23362 | `cacb9a173801f7b74bea6cb8b2eafd3481a81946ed89e95b17e49b7334a44827` | `scripts/build_cape_method_novelty_positioning.py` |
| qwen3_model_scaling_report_builder | True | 12740 | `fb391eef450b5d1161dd4d4bab3bb564cc47b749b0a6582592a1d913fb97085c` | `scripts/build_cape_qwen3_model_scaling_report.py` |
| metric_traceability_audit_builder | True | 20234 | `8192bc4500332666bc2db10973aefff986d427433f04c92274cf2646b247dc71` | `scripts/build_cape_metric_traceability_audit.py` |
| contribution_claim_traceability_builder | True | 21088 | `863a7a08006bf8f3bafd018795aea445189772dac4135e3f0374b81ac2494654` | `scripts/build_cape_contribution_claim_traceability.py` |
| related_work_baseline_traceability_builder | True | 21542 | `5ea60fa714612186ab783f7c79e00b113644a24d1b3cda8bec6b05a2f5a9b0ba` | `scripts/build_cape_related_work_baseline_traceability.py` |
| annotation_protocol_traceability_builder | True | 25420 | `24e562119985af01040b7d969041978446dfe509a8e593d691314643b7b7c912` | `scripts/build_cape_annotation_protocol_traceability.py` |
| claim_language_guardrails_builder | True | 29784 | `520f662d7fd3b6d063e6592e6b02496142dd813e09d2ac10bd6f5b17d64f7d3c` | `scripts/build_cape_claim_language_guardrails.py` |
| reviewer_response_prep_builder | True | 20475 | `25c25620b9db30cbf575e6d7f3355c8a8a2b63245ac3fb383d3f8799be04fb2d` | `scripts/build_cape_reviewer_response_prep.py` |
| submission_timeline_action_board_builder | True | 24375 | `68e364f7c610ccff6586be7f24ad5f9a49a88426916036a34a74ae251adae66e` | `scripts/build_cape_submission_timeline_action_board.py` |
| revised_plan_completion_audit_builder | True | 25714 | `c8f2081aa10e45fa94599e4eeeefb1f2acf2c5dd9ba9080a299c84ea1eeadf5c` | `scripts/build_cape_revised_plan_completion_audit.py` |
| pre_human_status_helper | True | 1610 | `3579f25316b70d40d583cd73c6907a419aaa6906328378c8c587f02511238e10` | `scripts/cape_pre_human_status.py` |

## Current Context Files

These files summarize the current run state. They are hash-checked for freshness but excluded from the protocol content hash.

| role | exists | bytes | sha256 | path |
|---|---:|---:|---|---|
| claim_gate_report | True | 16096 | `3235308a11ef4581ddc12715eaf96c0d8154a3f417f923cefd2683cdf4a1bc8f` | `experiments/cape_kg_eacl_20260627/06_release/claim_gate_report.json` |
| arr_submission_policy_checklist | True | 13239 | `e272fd2b3890703630c2e00d3ad32c553e8070c11a02f15ed6a046c4ff743bc6` | `experiments/cape_kg_eacl_20260627/06_release/arr_submission_policy_checklist.json` |
| anonymized_submission_prep | True | 85802 | `e60522e1dd6453ac9f96900d265f6585980865f8192078f25a6730de21681e66` | `experiments/cape_kg_eacl_20260627/06_release/anonymized_submission_prep.json` |
| responsible_nlp_checklist_prep | True | 17320 | `5a5cc928fed2961bbfa94f756088147bc4b2ca12a27e61395bc179bcbb6ca254` | `experiments/cape_kg_eacl_20260627/06_release/responsible_nlp_checklist_prep.json` |
| experiment_reproduction_card | True | 25386 | `5ecec8fb6c90e324d71f8e5602f6b19705f230bbe8a330a4e312361827095542` | `experiments/cape_kg_eacl_20260627/06_release/experiment_reproduction_card.json` |
| paper_tables | True | 14924 | `c6574059d5f4f492a4fc0c3a1e9121255b8445e34477c6b96d04823d099b9b1d` | `experiments/cape_kg_eacl_20260627/06_release/paper_tables.md` |
| paper_table_blueprint | True | 14900 | `8b36482f74381a4ba95002b0020601008fa13600965ae08e7c6b4e5cce49b52e` | `experiments/cape_kg_eacl_20260627/06_release/paper_table_blueprint.json` |
| claimable_main_table | True | 8484 | `005f17132e2ea81a48be93da5af34dfa47a6c038ae84bbdc8d6d8b85711a6480` | `experiments/cape_kg_eacl_20260627/06_release/claimable_main_table.json` |
| ablation_coverage_report | True | 42424 | `2bda4057cc74f003d3e1cc9bd442e8720a5c9103635c2f6e6866b674e487a199` | `experiments/cape_kg_eacl_20260627/06_release/ablation_coverage_report.json` |
| alias_canonicalization_report | True | 25200 | `f114573b66b22d5d2e50e13da756a3df56a79945b7e8342dbf33358ca7658f92` | `experiments/cape_kg_eacl_20260627/06_release/alias_canonicalization_report.json` |
| claim_language_guardrails | True | 24674 | `0057536408fcce5f75ecfd47db9a099e1cd9b239d612a403d9dc646d6571f4a6` | `experiments/cape_kg_eacl_20260627/06_release/claim_language_guardrails.json` |
| reviewer_response_prep | True | 16864 | `acb2c81fd51d0a3acf55c5d1947689da1b453f5409d19340c69db50c7d1aac4c` | `experiments/cape_kg_eacl_20260627/06_release/reviewer_response_prep.json` |
| submission_timeline_action_board | True | 20171 | `0c3e6c5d503cd2bcdb5a4b82ac11c7717633c9d44ec6e1ff47f952671507e4b8` | `experiments/cape_kg_eacl_20260627/06_release/submission_timeline_action_board.json` |
| revised_plan_completion_audit | True | 27725 | `56cd4fe7e0dd5e65d6790fe0cc90cbb320001e8851ff1332b9a25648e5bcac91` | `experiments/cape_kg_eacl_20260627/06_release/revised_plan_completion_audit.json` |
| revised_plan_completion_audit_public_safe | True | 11683 | `a401a18532bfb908621d8783569f529f57f39d8dfb75fd8c9aac7d761bf78815` | `experiments/cape_kg_eacl_20260627/06_release/revised_plan_completion_audit_public_safe.json` |
| method_module_coverage | True | 46695 | `95e37567ede4edebb0fb30a6a88f69999fd8f756ad57a2e2da65472e100fa154` | `experiments/cape_kg_eacl_20260627/06_release/method_module_coverage.json` |
| schema_retrieval_coverage_report | True | 29213 | `f61c1b4cf958bded060a67b9ee1bb23e1f2889c524af4014c8ebdd3467b1c82c` | `experiments/cape_kg_eacl_20260627/06_release/schema_retrieval_coverage_report.json` |
| method_novelty_positioning | True | 12832 | `0c45a6e355b613ae0363ab1c1a8f4e99f5b3ba2a29842bf678ee83d42792ad1c` | `experiments/cape_kg_eacl_20260627/06_release/method_novelty_positioning.json` |
| qwen3_model_scaling_report | True | 11209 | `4d154fbf91984b1ab665091de9ccc08775151337b7d31ba54f822c16f4e2d149` | `experiments/cape_kg_eacl_20260627/06_release/qwen3_model_scaling_report.json` |
| metric_traceability_audit | True | 31872 | `a88129a4c5645d3fb33d2c13ae6511c842bf91d0531474798db744ab33583594` | `experiments/cape_kg_eacl_20260627/06_release/metric_traceability_audit.json` |
| contribution_claim_traceability | True | 13648 | `eff305723aa5a80336d05dee2df7f73f62ea6ee596f761f7668da8c0eaac15e6` | `experiments/cape_kg_eacl_20260627/06_release/contribution_claim_traceability.json` |
| related_work_baseline_traceability | True | 17584 | `f8d822c4c9416c298aaf395a77aabdfa311270eda14bb3a1710122870e9431ee` | `experiments/cape_kg_eacl_20260627/06_release/related_work_baseline_traceability.json` |
| annotation_protocol_traceability | True | 16477 | `e35dd7d99e02f905fe9d084e0fe212fad1a90b4922f7a0c2aac84c9f8431f248` | `experiments/cape_kg_eacl_20260627/06_release/annotation_protocol_traceability.json` |
| rq_evidence_matrix | True | 15840 | `448492bbd2543ab4f6b55b6f9beb1d64780c0cbc92884f1a8947acdebd6b5b27` | `experiments/cape_kg_eacl_20260627/06_release/rq_evidence_matrix.json` |
| evidence_graph_projection | True | 1603 | `861843745a481b47c8cf3a3dc71acbfb78fe0dad393a6e1ee743f88ecaee2e4a` | `outputs/13_evidence_graph/evidence_graph_projection_summary.json` |
| neo4j_evidence_query_pack | True | 10917 | `5d637e5f4fa307ce7b0281536726254b5e2c5e43d9e763a5f0c593f3c1f8e54c` | `experiments/cape_kg_eacl_20260627/06_release/neo4j_evidence_query_pack.json` |

## Locked Private Inputs

Private inputs are represented by source IDs and hashes only so this protocol lock can remain public-safe. Their source IDs are in the protocol hash; their current hashes are tracked separately for handoff freshness.

| source_id | exists | bytes | sha256 |
|---|---:|---:|---|
| `evaluation_chunk_selection_120` | True | 495269 | `64d884bfaecea042b3aedd055a1ab3abc06bd7dd7ff3a0d60505f92164509fed` |
| `gold_candidate_template_120` | True | 11066628 | `cec1a17ea77826a7de0bf1403bdd56014176341238d6575335771866f71cf636` |
| `minimum_gold_package_a` | True | 3898829 | `6bff12957aa968df9313a463afd20f99d62eeb59ac6d487a0dfcc8d4909aa33e` |
| `minimum_gold_package_b` | True | 3898829 | `142924e746ed74fa2d8cd0bb14e0c674cdca8623e7b6b511fcb95d4dd96bc9d7` |
| `minimum_gold_resolution_template` | True | 324026 | `5f342e8671a4823df84a30e3b6c83901a27e6cd8831e3e5a24f52e791e00fcae` |
| `mapping_review_candidate_pool` | True | 205773 | `213e182506be10fb4d85b83cc9b57b699fdbfb47f2ecb27b79aba2da43e4a947` |
| `crosswalk_review_candidate_pool` | True | 241950 | `ee7bd10be0b93396062423eb1d3b8aa5c7772d22ab25fcf65d31caf9f6f1cf97` |

## Evaluation Commands

| step | command |
|---|---|
| `preflight_human_returns` | `python3 scripts/validate_cape_human_review_returns.py --experiment-dir experiments/cape_kg_eacl_20260627` |
| `apply_human_returns` | `PYTHON_BIN=python3 LLM_PYTHON=python3 APPLY_IMPORTS=1 bash scripts/run_cape_human_return_apply.sh` |
| `dry_refresh` | `PYTHON_BIN=python3 LLM_PYTHON=python3 APPLY_IMPORTS=0 bash scripts/run_cape_post_annotation_refresh.sh` |
| `final_handoff_validation` | `python3 scripts/validate_cape_pre_human_handoff.py --experiment-dir experiments/cape_kg_eacl_20260627 --outputs-dir outputs` |
| `release_checksum` | `sha256sum -c experiments/cape_kg_eacl_20260627/06_release/release_bundle_checksums.sha256` |

## Interpretation

- Human returns may update metric values, but metric definitions, condition sets, and claim-gate policy should remain stable unless this lock is intentionally regenerated.
- The protocol content hash changes whenever locked protocol files, metric definitions, condition sets, private input IDs, or commands change.
- Current context files may change after regeneration without redefining the protocol itself.
- Final paper claims still require adjudicated human-gold and expert-review evidence.
