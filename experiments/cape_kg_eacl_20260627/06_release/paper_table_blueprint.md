# CAPE-KG Paper Table Blueprint

Generated: 2026-06-29T18:55:33.552414+00:00
Plan: `AX_EACL_submission_review_revised_plan.md`
Experiment: `experiments/cape_kg_eacl_20260627`

이 문서는 revised EACL plan의 RQ/metric을 논문 표 배치로 고정한 blueprint입니다.
현재 `paper_tables.md`의 값을 대체하지 않으며, 어떤 표를 main result로 둘 수 있고 어떤 표는 diagnostic/appendix/pending으로 둬야 하는지 구분합니다.

## Summary

| Item | Value |
| --- | --- |
| Overall status | PASS |
| Claim status | paper_table_blueprint_ready_not_submission_complete |
| Safe to use as submission | False |
| Submission ready | False |
| Table count | 9 |
| Final-claim allowed now | 2 |
| Pending human/expert tables | 4 |
| Missing evidence files | 0 |
| Claim gate | FAIL |
| Pre-human validation | PASS |
| Pre-human checks | 92 |

## Table Blueprint

| table_id | paper_location | rq | current_status | current_use | promotion_gate |
| --- | --- | --- | --- | --- | --- |
| T01_dataset_annotation_status | main: Dataset and Annotation | Dataset | setup_claimable_human_gold_pending | main_table_setup_only | human-gold annotation and adjudication |
| T02_main_extraction_human_gold | main: Main Results | RQ1 | pending_human_gold | placeholder_only | gold.completed_chunks, gold.item_count, gold.iaa, llm.proposed_human_gold_score |
| T03_cq_schema_ablation | main: Ablation Studies | RQ2 | diagnostic_only_until_human_gold | diagnostic_or_appendix_until_gold | human-gold scoring for ablation conditions |
| T04_structural_cq_diagnostics | main or appendix: Structural Analysis | RQ2 | structural_diagnostic_ready | main_structural_diagnostic_with_claim_safety | human confirmation for semantic correctness claims |
| T05_public_benchmark_adapter | appendix or auxiliary main: Public Benchmark | External validity | auxiliary_claimable_not_main_private_result | auxiliary_or_appendix | none before human return; keep auxiliary scope |
| T06_mapping_downstream | main or appendix: Downstream Mapping | RQ3 | pending_expert_review | candidate_generation_only | mapping.expert_review |
| T07_crosswalk_downstream | appendix or downstream analysis | RQ3 | pending_expert_review | candidate_generation_only | crosswalk.expert_review |
| T08_active_review_efficiency | appendix or analysis: Human-in-the-loop | RQ4 | pending_human_effort | pool_design_only | active-review human effort return and adjudicated outcomes |
| T09_reproducibility_release | main: Reproducibility / appendix | Reproducibility | claimable_setup_rights_review_required | main_setup_or_appendix | rights review before source-text release |

## Detailed Table Specs

### T01_dataset_annotation_status. Dataset, annotation, and review-gate status

- Paper location: main: Dataset and Annotation
- RQ: `Dataset`
- Current status: `setup_claimable_human_gold_pending`
- Current use: `main_table_setup_only`
- Promotion gate: human-gold annotation and adjudication
- Final claim allowed now: `False`
- Caption stub: Dataset and annotation status for the Korean bid/proposal procedural KG extraction benchmark.
- Target metrics: evaluation chunks, priority gold subset, adjudicated chunks, gold items, return files

| path | exists | bytes |
| --- | --- | --- |
| experiments/cape_kg_eacl_20260627/06_release/paper_tables.md | True | 14924 |
| experiments/cape_kg_eacl_20260627/06_release/gold_sampling_coverage_report.md | True | 4889 |
| experiments/cape_kg_eacl_20260627/06_release/human_review_status_dashboard_ko.md | True | 12146 |
| experiments/cape_kg_eacl_20260627/04_evaluation/human_gold_validation_summary.json | True | 848 |

### T02_main_extraction_human_gold. Human-gold extraction performance

- Paper location: main: Main Results
- RQ: `RQ1`
- Current status: `pending_human_gold`
- Current use: `placeholder_only`
- Promotion gate: gold.completed_chunks, gold.item_count, gold.iaa, llm.proposed_human_gold_score
- Final claim allowed now: `False`
- Caption stub: Main extraction results against adjudicated human-gold nodes, edges, and evidence spans.
- Target metrics: Node F1, Edge F1, Evidence EM, Evidence IoU, Unsupported Edge Rate

| path | exists | bytes |
| --- | --- | --- |
| experiments/cape_kg_eacl_20260627/06_release/post_human_scoring_readiness.md | True | 7034 |
| experiments/cape_kg_eacl_20260627/04_evaluation/human_gold_metrics.json | True | 1509 |
| experiments/cape_kg_eacl_20260627/04_evaluation/human_gold_span_iou_metrics.json | True | 1405 |
| experiments/cape_kg_eacl_20260627/06_release/claim_gate_report.md | True | 4370 |

### T03_cq_schema_ablation. CAPE-KG module ablations

- Paper location: main: Ablation Studies
- RQ: `RQ2`
- Current status: `diagnostic_only_until_human_gold`
- Current use: `diagnostic_or_appendix_until_gold`
- Promotion gate: human-gold scoring for ablation conditions
- Final claim allowed now: `False`
- Caption stub: Ablation results for CQ anchoring, schema retrieval, procedural schema constraints, and validators.
- Target metrics: P - CQ, P - Schema retrieval, P - Procedural schema, P - Validator, Ontology conformance, CQ answerability

| path | exists | bytes |
| --- | --- | --- |
| experiments/cape_kg_eacl_20260627/06_release/paper_tables.md | True | 14924 |
| experiments/cape_kg_eacl_20260627/04_evaluation/actual_llm_silver_metrics.json | True | 15122 |
| experiments/cape_kg_eacl_20260627/04_evaluation/cq_answerability_by_condition.csv | True | 12836 |
| experiments/cape_kg_eacl_20260627/04_evaluation/structural_evaluation_metrics.json | True | 22053 |
| experiments/cape_kg_eacl_20260627/06_release/rq_evidence_matrix.md | True | 14252 |

### T04_structural_cq_diagnostics. Ontology, procedural consistency, and CQ answerability diagnostics

- Paper location: main or appendix: Structural Analysis
- RQ: `RQ2`
- Current status: `structural_diagnostic_ready`
- Current use: `main_structural_diagnostic_with_claim_safety`
- Promotion gate: human confirmation for semantic correctness claims
- Final claim allowed now: `False`
- Caption stub: Automatic structural diagnostics for the constructed Layer 2 procedural KG.
- Target metrics: Ontology conformance, Procedural consistency, Cycle count, Gateway branch gaps, CQ answerability

| path | exists | bytes |
| --- | --- | --- |
| experiments/cape_kg_eacl_20260627/04_evaluation/structural_evaluation_report.md | True | 2087 |
| experiments/cape_kg_eacl_20260627/04_evaluation/ontology_conformance_metrics.json | True | 983 |
| experiments/cape_kg_eacl_20260627/04_evaluation/procedural_consistency_metrics.json | True | 15185 |
| experiments/cape_kg_eacl_20260627/04_evaluation/cq_answerability_structural_metrics.json | True | 3876 |
| experiments/cape_kg_eacl_20260627/06_release/cq_query_pack.md | True | 29675 |

### T05_public_benchmark_adapter. Public benchmark adapter diagnostics

- Paper location: appendix or auxiliary main: Public Benchmark
- RQ: `External validity`
- Current status: `auxiliary_claimable_not_main_private_result`
- Current use: `auxiliary_or_appendix`
- Promotion gate: none before human return; keep auxiliary scope
- Final claim allowed now: `True`
- Caption stub: Auxiliary public-benchmark adapter diagnostics; not a substitute for target-corpus human-gold results.
- Target metrics: PAGED node/edge F1, Text2KG relation/triple F1, run size

| path | exists | bytes |
| --- | --- | --- |
| experiments/cape_kg_eacl_20260627/08_public_benchmarks/public_benchmark_crosscheck_report.md | True | 1379 |
| experiments/cape_kg_eacl_20260627/08_public_benchmarks/public_benchmark_crosscheck_summary.json | True | 3839 |
| experiments/cape_kg_eacl_20260627/06_release/public_reproducibility_manifest.md | True | 19910 |

### T06_mapping_downstream. Layer2-to-NCS/PCF mapping utility

- Paper location: main or appendix: Downstream Mapping
- RQ: `RQ3`
- Current status: `pending_expert_review`
- Current use: `candidate_generation_only`
- Promotion gate: mapping.expert_review
- Final claim allowed now: `False`
- Caption stub: Expert-reviewed downstream standard-taxonomy alignment performance.
- Target metrics: P@1, P@5, MRR, nDCG@10, expert accept rate, explanation quality

| path | exists | bytes |
| --- | --- | --- |
| experiments/cape_kg_eacl_20260627/04_evaluation/mapping_downstream_report.md | True | 2824 |
| experiments/cape_kg_eacl_20260627/06_release/mapping_review_progress_report.md | True | 4317 |
| experiments/cape_kg_eacl_20260627/04_evaluation/mapping_expert_metrics.json | True | 1675 |
| experiments/cape_kg_eacl_20260627/06_release/rq_evidence_matrix.md | True | 14252 |

### T07_crosswalk_downstream. Layer2-bridged NCS-PCF crosswalk utility

- Paper location: appendix or downstream analysis
- RQ: `RQ3`
- Current status: `pending_expert_review`
- Current use: `candidate_generation_only`
- Promotion gate: crosswalk.expert_review
- Final claim allowed now: `False`
- Caption stub: Expert-reviewed utility of Layer2-bridged NCS-PCF crosswalk candidates.
- Target metrics: accept rate, Hit@K, P@10, MRR, nDCG@10, utility, explanation quality

| path | exists | bytes |
| --- | --- | --- |
| experiments/cape_kg_eacl_20260627/04_evaluation/ncs_pcf_crosswalk_report.md | True | 4308 |
| experiments/cape_kg_eacl_20260627/04_evaluation/ncs_pcf_crosswalk_summary.json | True | 893 |
| experiments/cape_kg_eacl_20260627/04_evaluation/crosswalk_expert_metrics.json | True | 1115 |

### T08_active_review_efficiency. Active-review efficiency

- Paper location: appendix or analysis: Human-in-the-loop
- RQ: `RQ4`
- Current status: `pending_human_effort`
- Current use: `pool_design_only`
- Promotion gate: active-review human effort return and adjudicated outcomes
- Final claim allowed now: `False`
- Caption stub: Human-effort efficiency of active-review prioritization compared with control queues.
- Target metrics: review seconds, corrections, high-impact corrections, precision@k, lift vs random

| path | exists | bytes |
| --- | --- | --- |
| experiments/cape_kg_eacl_20260627/06_release/active_review_human_effort_plan.md | True | 2911 |
| experiments/cape_kg_eacl_20260627/04_evaluation/active_review_human_effort_metrics.json | True | 6348 |
| experiments/cape_kg_eacl_20260627/04_evaluation/active_review_ablation_metrics.json | True | 11236 |
| experiments/cape_kg_eacl_20260627/04_evaluation/active_review_pool_overlap_summary.json | True | 1861 |

### T09_reproducibility_release. Reproducibility and release artifacts

- Paper location: main: Reproducibility / appendix
- RQ: `Reproducibility`
- Current status: `claimable_setup_rights_review_required`
- Current use: `main_setup_or_appendix`
- Promotion gate: rights review before source-text release
- Final claim allowed now: `True`
- Caption stub: Release and reproducibility artifacts supporting a public-safe replication path.
- Target metrics: schema, prompts, code, public-safe bundle, PROV-O, RDF/SHACL, synthetic examples

| path | exists | bytes |
| --- | --- | --- |
| experiments/cape_kg_eacl_20260627/06_release/public_reproducibility_manifest.md | True | 19910 |
| experiments/cape_kg_eacl_20260627/06_release/release_bundle_safety_report.md | True | 2110 |
| experiments/cape_kg_eacl_20260627/06_release/provenance_manifest.md | True | 55803 |
| experiments/cape_kg_eacl_20260627/06_release/provenance_prov_o_report.md | True | 1486 |
| outputs/12_rdf/cape_kg_shacl_validation_report.md | True | 1327 |
| experiments/cape_kg_eacl_20260627/06_release/public_synthetic_examples/README.md | True | 969 |

## Claim Policy

- `placeholder_only`, `candidate_generation_only`, `pool_design_only`, and `diagnostic_or_appendix_until_gold` rows must not be promoted to final main results before their promotion gates pass.
- Public benchmark and reproducibility tables can be used only with their auxiliary/setup scope.
- Main extraction and ablation superiority claims require adjudicated human-gold scoring.
- Mapping/crosswalk tables require expert-reviewed labels.
- This artifact intentionally keeps `safe_to_use_as_submission=false` and `submission_ready=false`.
