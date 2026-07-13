# CAPE-KG Related Work to Baseline Traceability

Generated: 2026-06-29T18:56:33.540068+00:00
Claim status: `related_work_baseline_traceability_ready_not_official_reproduction`
Plan: `AX_EACL_submission_review_revised_plan.md`

This artifact maps the revised plan's related-work references to local baselines, public adapters, validators, provenance artifacts, and claim boundaries.
It is not an official reproduction report; it fixes what each reference supports in the paper narrative.

## Summary

- claim_status: `related_work_baseline_traceability_ready_not_official_reproduction`
- reference_count: `9`
- missing_evidence_file_count: `0`
- direct_llm_condition_count: `5`
- public_adapter_reference_count: `2`
- standard_reference_count: `2`
- official_reproduction_claim_count: `0`
- public_benchmark_claim_status: `public_adapter_model_runs_diagnostic_not_official_leaderboard`
- strong_public_cross_run_present: `True`
- max_single_run_paged_items: `100`
- max_single_run_text2kg_items: `200`

## Claim Boundary

- Safe scope: Use for Related Work, baseline motivation, public-adapter scope, validation standards, and reproducibility framing.
- Not claimable: This artifact does not prove official reproductions, benchmark leaderboard standing, target-corpus final performance, or human/expert-reviewed utility.
- Human/expert gated: `True`

## Related Work Matrix

| reference | coverage | local conditions | missing evidence | safe use |
| --- | --- | --- | --- | --- |
| RW01_sac_kg | deterministic_approximation_baseline | B6_sac_kg_verifier_pruner | 0 | Use as an approximate verifier/pruner baseline family in setup and ablation discussion. |
| RW02_edc | style_baseline | B3_edc_style | 0 | Use as an EDC-style baseline family for open-schema/canonicalization contrast. |
| RW03_taxonomy_driven_kg | style_baseline_and_downstream_bridge | B4_taxonomy_rag<br>P_minus_Standard_bridge | 0 | Use as taxonomy-retrieval and downstream bridge context. |
| RW04_text2kgbench | public_adapter_diagnostic | public_qwen3_8b_full_adapter_eval | 0 | Use as auxiliary public benchmark evidence: max Text2KG n=200; best relation F1=0.6015. |
| RW05_textminex | conceptual_positioning_with_local_validators | M5_evidence_grounding<br>M7_ontology_validation | 0 | Use as related-work motivation for faithfulness and ontology-guided extraction. |
| RW06_paged | public_adapter_and_procedural_prompt_baseline | B5_procedural_prompt<br>public_qwen3_8b_full_adapter_eval | 0 | Use as procedural graph extraction context: max PAGED n=100; best edge F1=0.4233. |
| RW07_multi_agent_procedural_feedback | conceptual_positioning_with_structural_feedback_artifacts | M8_procedural_consistency_validator<br>M10_active_review_queue | 0 | Use as motivation for structural feedback and active review scaffolding. |
| RW08_shacl | standard_validation_artifact | M7_ontology_shacl_validator | 0 | Use to document validation design and reproducibility. |
| RW09_prov_o | standard_provenance_artifact | provenance_manifest<br>provenance_prov_o_export | 0 | Use to document reproducibility and run provenance. |

## RW01_sac_kg. SAC-KG: generator / verifier / pruner style domain KG construction

- Source URL: https://aclanthology.org/2024.acl-long.238/
- Plan role: Motivates verifier/pruner-style KG construction baseline.
- Local coverage type: `deterministic_approximation_baseline`
- Local conditions/artifacts: `B6_sac_kg_verifier_pruner`
- Metric summary: rows=120; nodes=2281; edges=361; mappings=107; predicate_f1=0.0774; evidence_f1=0.1008
- Safe use: Use as an approximate verifier/pruner baseline family in setup and ablation discussion.
- Not claimable: Do not claim a full SAC-KG reproduction or direct leaderboard comparison.
- Paper sections: `Related Work, Experiments: Baselines, Limitations`

### Evidence Files

| role | path | exists | bytes |
| --- | --- | --- | --- |
| B6 prompt | experiments/cape_kg_eacl_20260627/02_schema/prompts/B6_sac_kg_verifier_pruner_baseline.txt | True | 182 |
| B6 silver/proxy metric row | experiments/cape_kg_eacl_20260627/04_evaluation/actual_llm_silver_metrics.json | True | 15122 |
| novelty-positioning caveat | experiments/cape_kg_eacl_20260627/06_release/method_novelty_positioning.md | True | 10144 |

## RW02_edc. Extract, Define, Canonicalize (EDC)

- Source URL: https://aclanthology.org/2024.emnlp-main.548/
- Plan role: Motivates open-schema extraction and canonicalization comparison.
- Local coverage type: `style_baseline`
- Local conditions/artifacts: `B3_edc_style`
- Metric summary: rows=120; nodes=566; edges=53; mappings=0; predicate_f1=0.0119; evidence_f1=0.0311
- Safe use: Use as an EDC-style baseline family for open-schema/canonicalization contrast.
- Not claimable: Do not claim an exact implementation of the original EDC system.
- Paper sections: `Related Work, Experiments: Baselines, Analysis`

### Evidence Files

| role | path | exists | bytes |
| --- | --- | --- | --- |
| B3 prompt | experiments/cape_kg_eacl_20260627/02_schema/prompts/B3_edc_style_baseline.txt | True | 111 |
| B3 silver/proxy metric row | experiments/cape_kg_eacl_20260627/04_evaluation/actual_llm_silver_metrics.json | True | 15122 |
| canonicalization diagnostic | experiments/cape_kg_eacl_20260627/06_release/alias_canonicalization_report.md | True | 4439 |

## RW03_taxonomy_driven_kg. Taxonomy-driven KG construction / Taxonomy-RAG

- Source URL: https://aclanthology.org/2025.findings-acl.223/
- Plan role: Motivates taxonomy-retrieval baseline and standard-taxonomy bridge framing.
- Local coverage type: `style_baseline_and_downstream_bridge`
- Local conditions/artifacts: `B4_taxonomy_rag, P_minus_Standard_bridge`
- Metric summary: rows=120; nodes=674; edges=128; mappings=41; predicate_f1=0.0105; evidence_f1=0.0641
- Safe use: Use as taxonomy-retrieval and downstream bridge context.
- Not claimable: Do not claim mapping utility before expert labels are returned.
- Paper sections: `Related Work, Method: Standard bridge, Downstream Evaluation`

### Evidence Files

| role | path | exists | bytes |
| --- | --- | --- | --- |
| B4 prompt | experiments/cape_kg_eacl_20260627/02_schema/prompts/B4_taxonomy_rag_baseline.txt | True | 96 |
| B4 silver/proxy metric row | experiments/cape_kg_eacl_20260627/04_evaluation/actual_llm_silver_metrics.json | True | 15122 |
| Layer2-to-NCS candidates | outputs/08_mapping/l2_ncs_mapping_candidates.jsonl | True | 82404 |
| Layer2-to-PCF candidates | outputs/08_mapping/l2_pcf_mapping_candidates.jsonl | True | 81856 |
| mapping downstream diagnostic | experiments/cape_kg_eacl_20260627/04_evaluation/mapping_downstream_report.md | True | 2824 |

## RW04_text2kgbench. Text2KGBench ontology-driven KG generation benchmark

- Source URL: https://ar5iv.labs.arxiv.org/html/2308.02357
- Plan role: Motivates ontology-conformance and hallucination-oriented public sanity checks.
- Local coverage type: `public_adapter_diagnostic`
- Local conditions/artifacts: `public_qwen3_8b_full_adapter_eval`
- Metric summary: n/a
- Safe use: Use as auxiliary public benchmark evidence: max Text2KG n=200; best relation F1=0.6015.
- Not claimable: Do not treat adapter diagnostics as official Text2KGBench leaderboard results or target-corpus final evidence.
- Paper sections: `Related Work, Experiments: Public benchmark adapters, Limitations`

### Evidence Files

| role | path | exists | bytes |
| --- | --- | --- | --- |
| Text2KGBench CAPE adapter subset | experiments/cape_kg_eacl_20260627/08_public_benchmarks/text2kgbench_cape_adapter_subset.jsonl | True | 244992 |
| Text2KGBench local profile | experiments/cape_kg_eacl_20260627/08_public_benchmarks/text2kgbench_profile.json | True | 10712 |
| public cross-check summary | experiments/cape_kg_eacl_20260627/08_public_benchmarks/public_benchmark_crosscheck_summary.json | True | 3839 |
| public cross-check report | experiments/cape_kg_eacl_20260627/08_public_benchmarks/public_benchmark_crosscheck_report.md | True | 1379 |

## RW05_textminex. TextMineX ontology-guided LLM pipeline

- Source URL: https://aclanthology.org/2026.findings-eacl.130.pdf
- Plan role: Motivates ontology conformance and source-text faithfulness positioning.
- Local coverage type: `conceptual_positioning_with_local_validators`
- Local conditions/artifacts: `M5_evidence_grounding, M7_ontology_validation`
- Metric summary: n/a
- Safe use: Use as related-work motivation for faithfulness and ontology-guided extraction.
- Not claimable: Do not claim TextMineX reproduction or direct comparison.
- Paper sections: `Related Work, Method: Validation, Faithfulness Evaluation`

### Evidence Files

| role | path | exists | bytes |
| --- | --- | --- | --- |
| evidence-span diagnostic | experiments/cape_kg_eacl_20260627/04_evaluation/evidence_span_granularity_report.md | True | 1580 |
| ontology/procedural structural diagnostic | experiments/cape_kg_eacl_20260627/04_evaluation/structural_evaluation_report.md | True | 2087 |
| SHACL-style validation report | outputs/12_rdf/cape_kg_shacl_validation_report.md | True | 1327 |
| metric-to-output traceability | experiments/cape_kg_eacl_20260627/06_release/metric_traceability_audit.md | True | 4507 |

## RW06_paged. PAGED procedural graph extraction benchmark

- Source URL: https://aclanthology.org/2024.acl-long.583/
- Plan role: Motivates procedural graph extraction and public procedural sanity checks.
- Local coverage type: `public_adapter_and_procedural_prompt_baseline`
- Local conditions/artifacts: `B5_procedural_prompt, public_qwen3_8b_full_adapter_eval`
- Metric summary: rows=120; nodes=957; edges=119; mappings=0; predicate_f1=0.0096; evidence_f1=0.0603
- Safe use: Use as procedural graph extraction context: max PAGED n=100; best edge F1=0.4233.
- Not claimable: Do not treat adapter diagnostics as official PAGED leaderboard results or target-corpus final evidence.
- Paper sections: `Related Work, Experiments: Public benchmark adapters, Analysis`

### Evidence Files

| role | path | exists | bytes |
| --- | --- | --- | --- |
| B5 prompt | experiments/cape_kg_eacl_20260627/02_schema/prompts/B5_procedural_prompt_baseline.txt | True | 104 |
| B5 silver/proxy metric row | experiments/cape_kg_eacl_20260627/04_evaluation/actual_llm_silver_metrics.json | True | 15122 |
| PAGED CAPE adapter subset | experiments/cape_kg_eacl_20260627/08_public_benchmarks/paged_cape_adapter_subset.jsonl | True | 608999 |
| PAGED local profile | experiments/cape_kg_eacl_20260627/08_public_benchmarks/paged_profile.json | True | 1648 |
| public cross-check summary | experiments/cape_kg_eacl_20260627/08_public_benchmarks/public_benchmark_crosscheck_summary.json | True | 3839 |

## RW07_multi_agent_procedural_feedback. Multi-agent procedural graph extraction with structural feedback

- Source URL: https://aclanthology.org/2026.findings-eacl.158.pdf
- Plan role: Motivates procedural feedback, structural constraints, and review queues.
- Local coverage type: `conceptual_positioning_with_structural_feedback_artifacts`
- Local conditions/artifacts: `M8_procedural_consistency_validator, M10_active_review_queue`
- Metric summary: n/a
- Safe use: Use as motivation for structural feedback and active review scaffolding.
- Not claimable: Do not claim a multi-agent reproduction or human-effort gains before returned timing/correction data.
- Paper sections: `Related Work, Method: Active review, Analysis`

### Evidence Files

| role | path | exists | bytes |
| --- | --- | --- | --- |
| procedural consistency report | experiments/cape_kg_eacl_20260627/04_evaluation/procedural_consistency_report.md | True | 2087 |
| structural-review action plan | experiments/cape_kg_eacl_20260627/06_release/structural_review_action_plan.md | True | 3565 |
| active-review diagnostic | experiments/cape_kg_eacl_20260627/04_evaluation/active_review_efficiency_report.md | True | 4055 |
| human-effort protocol | experiments/cape_kg_eacl_20260627/06_release/active_review_human_effort_plan.md | True | 2911 |

## RW08_shacl. W3C SHACL

- Source URL: https://www.w3.org/TR/shacl/
- Plan role: Provides standards context for shape/domain-range validation.
- Local coverage type: `standard_validation_artifact`
- Local conditions/artifacts: `M7_ontology_shacl_validator`
- Metric summary: n/a
- Safe use: Use to document validation design and reproducibility.
- Not claimable: Do not equate SHACL pass rates with final semantic correctness.
- Paper sections: `Method: Validation, Reproducibility, Limitations`

### Evidence Files

| role | path | exists | bytes |
| --- | --- | --- | --- |
| schema SHACL-style shapes | experiments/cape_kg_eacl_20260627/02_schema/cape_shapes.shacl.ttl | True | 340 |
| runtime shapes | outputs/12_rdf/cape_kg_runtime_shapes.shacl.ttl | True | 6142 |
| validation summary | outputs/12_rdf/cape_kg_shacl_validation_summary.json | True | 1561 |
| validation report | outputs/12_rdf/cape_kg_shacl_validation_report.md | True | 1327 |

## RW09_prov_o. W3C PROV-O

- Source URL: https://www.w3.org/TR/prov-o/
- Plan role: Provides standards context for provenance of prompts, runs, chunks, and outputs.
- Local coverage type: `standard_provenance_artifact`
- Local conditions/artifacts: `provenance_manifest, provenance_prov_o_export`
- Metric summary: n/a
- Safe use: Use to document reproducibility and run provenance.
- Not claimable: Do not claim that provenance alone resolves private-corpus release rights.
- Paper sections: `Reproducibility, Ethics, Limitations`

### Evidence Files

| role | path | exists | bytes |
| --- | --- | --- | --- |
| provenance manifest | experiments/cape_kg_eacl_20260627/06_release/provenance_manifest.md | True | 55803 |
| provenance manifest JSON | experiments/cape_kg_eacl_20260627/06_release/provenance_manifest.json | True | 100278 |
| PROV-O TTL export | experiments/cape_kg_eacl_20260627/06_release/provenance_prov_o.ttl | True | 183362 |
| PROV-O export report | experiments/cape_kg_eacl_20260627/06_release/provenance_prov_o_report.md | True | 1486 |

## Source Artifacts

- `revised_plan`: `AX_EACL_submission_review_revised_plan.md`
- `method_novelty_positioning`: `experiments/cape_kg_eacl_20260627/06_release/method_novelty_positioning.json`
- `public_benchmark_crosscheck`: `experiments/cape_kg_eacl_20260627/08_public_benchmarks/public_benchmark_crosscheck_summary.json`
- `actual_llm_silver_metrics`: `experiments/cape_kg_eacl_20260627/04_evaluation/actual_llm_silver_metrics.json`
- `external_resource_license_report`: `experiments/cape_kg_eacl_20260627/06_release/external_resource_license_report.json`
