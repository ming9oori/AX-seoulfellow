# CAPE-KG Public Reproducibility Manifest

Generated: 2026-06-29T19:06:39.525462+00:00
Experiment: `experiments/cape_kg_eacl_20260627`

This manifest maps the reproducibility material promised in the EACL plan to public-safe artifacts. It is not a performance-result claim.

## Claim Status

- Claim status: `public_reproducibility_manifest_ready_not_submission_complete`
- Public-safe rows: 67
- Internal-only rows: 22
- Missing rows: 0
- Text-risk hits in manifest payload: 0

## Requirement Coverage

| requirement | status | evidence |
| --- | --- | --- |
| schema | covered | CAPE schema, SHACL-style shapes, competency questions |
| prompts | covered | condition prompts plus strict JSON contract |
| code | covered | runners, builders, exporters, release validator |
| evaluation protocol | covered | locked metrics, condition sets, claim policy |
| derived public examples | covered | synthetic chunks, gold, predictions, summary |
| public benchmark cross-check | covered | adapter, cross-check, Qwen3 public benchmark summaries |
| release safety | covered | ethics, license, safety, latest bundle index |

## Category Summary

| category | total | present | public_safe | internal_only |
| --- | --- | --- | --- | --- |
| evaluation_protocol | 29 | 29 | 15 | 3 |
| internal_only | 8 | 8 | 0 | 8 |
| prompts | 10 | 10 | 10 | 0 |
| public_benchmarks | 8 | 8 | 8 | 0 |
| release_safety | 5 | 5 | 3 | 0 |
| runtime_code | 24 | 24 | 21 | 3 |
| schema_and_cq | 3 | 3 | 3 | 0 |
| synthetic_public_examples | 5 | 5 | 5 | 0 |
| traceability | 10 | 10 | 2 | 8 |

## Artifact Rows

| category | description | path | exists | release_status | reviewer_value |
| --- | --- | --- | --- | --- | --- |
| schema_and_cq | CAPE node/edge schema | experiments/cape_kg_eacl_20260627/02_schema/cape_schema.json | yes | public_safe | reproducibility |
| schema_and_cq | SHACL-style shapes | experiments/cape_kg_eacl_20260627/02_schema/cape_shapes.shacl.ttl | yes | public_safe | reproducibility |
| schema_and_cq | Competency questions | experiments/cape_kg_eacl_20260627/02_schema/competency_questions.json | yes | public_safe | reproducibility |
| prompts | LLM condition prompt: B0_plain_llm_triple_extraction.txt | experiments/cape_kg_eacl_20260627/02_schema/prompts/B0_plain_llm_triple_extraction.txt | yes | public_safe | reproducibility |
| prompts | LLM condition prompt: B1_predicate_constrained_llm.txt | experiments/cape_kg_eacl_20260627/02_schema/prompts/B1_predicate_constrained_llm.txt | yes | public_safe | reproducibility |
| prompts | LLM condition prompt: B2_current_project_baseline.txt | experiments/cape_kg_eacl_20260627/02_schema/prompts/B2_current_project_baseline.txt | yes | public_safe | reproducibility |
| prompts | LLM condition prompt: B3_edc_style_baseline.txt | experiments/cape_kg_eacl_20260627/02_schema/prompts/B3_edc_style_baseline.txt | yes | public_safe | reproducibility |
| prompts | LLM condition prompt: B4_taxonomy_rag_baseline.txt | experiments/cape_kg_eacl_20260627/02_schema/prompts/B4_taxonomy_rag_baseline.txt | yes | public_safe | reproducibility |
| prompts | LLM condition prompt: B5_procedural_prompt_baseline.txt | experiments/cape_kg_eacl_20260627/02_schema/prompts/B5_procedural_prompt_baseline.txt | yes | public_safe | reproducibility |
| prompts | LLM condition prompt: B6_sac_kg_verifier_pruner_baseline.txt | experiments/cape_kg_eacl_20260627/02_schema/prompts/B6_sac_kg_verifier_pruner_baseline.txt | yes | public_safe | reproducibility |
| prompts | LLM condition prompt: P_cape_kg.txt | experiments/cape_kg_eacl_20260627/02_schema/prompts/P_cape_kg.txt | yes | public_safe | reproducibility |
| prompts | LLM condition prompt: P_minus_Schema_retrieval.txt | experiments/cape_kg_eacl_20260627/02_schema/prompts/P_minus_Schema_retrieval.txt | yes | public_safe | reproducibility |
| prompts | LLM condition prompt: strict_json_contract.txt | experiments/cape_kg_eacl_20260627/02_schema/prompts/strict_json_contract.txt | yes | public_safe | reproducibility |
| runtime_code | LLM condition runner | scripts/run_cape_llm_condition_baselines.py | yes | public_safe | reproducibility |
| runtime_code | KG experiment builder | scripts/build_cape_kg_eacl_experiment.py | yes | public_safe | reproducibility |
| runtime_code | RDF and SHACL-style exporter | scripts/export_cape_kg_rdf_shacl.py | yes | public_safe | reproducibility |
| runtime_code | CQ query pack builder | scripts/build_cape_cq_query_pack.py | yes | public_safe | reproducibility |
| runtime_code | Neo4j evidence query pack builder | scripts/build_cape_neo4j_evidence_query_pack.py | yes | internal_only | Neo4j evidence inspection helper |
| runtime_code | Prompt-node-edge traceability builder | scripts/build_cape_prompt_node_edge_traceability.py | yes | public_safe | reproducibility |
| runtime_code | Experiment reproduction card builder | scripts/build_cape_experiment_reproduction_card.py | yes | public_safe | reproducibility |
| runtime_code | Evidence graph projection builder | scripts/build_cape_evidence_graph_projection.py | yes | public_safe | reproducibility |
| runtime_code | Predicate cue span diagnostic builder | scripts/build_cape_predicate_cue_spans.py | yes | public_safe | reproducibility |
| runtime_code | Method novelty positioning builder | scripts/build_cape_method_novelty_positioning.py | yes | public_safe | reproducibility |
| runtime_code | Qwen3 model-scaling report builder | scripts/build_cape_qwen3_model_scaling_report.py | yes | public_safe | reproducibility |
| runtime_code | Gold sampling coverage report builder | scripts/build_cape_gold_sampling_coverage_report.py | yes | public_safe | reproducibility |
| runtime_code | Public synthetic example builder | scripts/build_cape_public_synthetic_examples.py | yes | public_safe | reproducibility |
| runtime_code | Anonymized submission prep builder | scripts/build_cape_anonymized_submission_prep.py | yes | public_safe | reproducibility |
| runtime_code | Responsible NLP checklist prep builder | scripts/build_cape_responsible_nlp_checklist_prep.py | yes | public_safe | reproducibility |
| runtime_code | Release bundle builder | scripts/build_cape_release_bundle.py | yes | public_safe | reproducibility |
| runtime_code | Pre-human release validator | scripts/validate_cape_pre_human_handoff.py | yes | public_safe | reproducibility |
| runtime_code | Pre-human status helper | scripts/cape_pre_human_status.py | yes | public_safe | reproducibility |
| runtime_code | Revised plan completion audit builder | scripts/build_cape_revised_plan_completion_audit.py | yes | public_safe | reproducibility |
| runtime_code | Annotation protocol traceability builder | scripts/build_cape_annotation_protocol_traceability.py | yes | internal_only | human annotation protocol traceability; internal review path references |
| runtime_code | Metric traceability audit builder | scripts/build_cape_metric_traceability_audit.py | yes | public_safe | reproducibility |
| runtime_code | Contribution claim traceability builder | scripts/build_cape_contribution_claim_traceability.py | yes | public_safe | reproducibility |
| runtime_code | Related-work baseline traceability builder | scripts/build_cape_related_work_baseline_traceability.py | yes | public_safe | reproducibility |
| runtime_code | Human-review packet integrity builder | scripts/build_cape_human_review_packet_integrity_report.py | yes | internal_only | human-review packet integrity; internal path references |
| evaluation_protocol | Locked evaluation protocol | experiments/cape_kg_eacl_20260627/06_release/evaluation_protocol_lock.md | yes | public_safe | reproducibility |
| evaluation_protocol | Locked evaluation protocol JSON | experiments/cape_kg_eacl_20260627/06_release/evaluation_protocol_lock.json | yes | public_safe | reproducibility |
| evaluation_protocol | Claim-safe paper tables | experiments/cape_kg_eacl_20260627/06_release/paper_tables.md | yes | live_release_status | reproducibility |
| evaluation_protocol | Claim-safe paper tables LaTeX | experiments/cape_kg_eacl_20260627/06_release/paper_tables.tex | yes | live_release_status | reproducibility |
| evaluation_protocol | Claimability table | experiments/cape_kg_eacl_20260627/06_release/claimable_main_table.md | yes | live_release_status | reproducibility |
| evaluation_protocol | Experiment reproduction card | experiments/cape_kg_eacl_20260627/06_release/experiment_reproduction_card.md | yes | live_release_status | reproducibility |
| evaluation_protocol | Experiment reproduction card JSON | experiments/cape_kg_eacl_20260627/06_release/experiment_reproduction_card.json | yes | live_release_status | reproducibility |
| evaluation_protocol | Experiment reproduction condition CSV | experiments/cape_kg_eacl_20260627/06_release/experiment_reproduction_conditions.csv | yes | live_release_status | reproducibility |
| evaluation_protocol | RQ evidence matrix | experiments/cape_kg_eacl_20260627/06_release/rq_evidence_matrix.md | yes | live_release_status | reproducibility |
| evaluation_protocol | Public-safe revised plan completion audit | experiments/cape_kg_eacl_20260627/06_release/revised_plan_completion_audit_public_safe.md | yes | public_safe | reproducibility |
| evaluation_protocol | Public-safe revised plan completion audit JSON | experiments/cape_kg_eacl_20260627/06_release/revised_plan_completion_audit_public_safe.json | yes | public_safe | reproducibility |
| evaluation_protocol | Public-safe revised plan completion audit CSV | experiments/cape_kg_eacl_20260627/06_release/revised_plan_completion_audit_public_safe_items.csv | yes | public_safe | reproducibility |
| evaluation_protocol | Metric traceability audit | experiments/cape_kg_eacl_20260627/06_release/metric_traceability_audit.md | yes | public_safe | reproducibility |
| evaluation_protocol | Metric traceability audit JSON | experiments/cape_kg_eacl_20260627/06_release/metric_traceability_audit.json | yes | public_safe | reproducibility |
| evaluation_protocol | Metric traceability audit CSV | experiments/cape_kg_eacl_20260627/06_release/metric_traceability_audit.csv | yes | public_safe | reproducibility |
| evaluation_protocol | Contribution claim traceability | experiments/cape_kg_eacl_20260627/06_release/contribution_claim_traceability.md | yes | public_safe | reproducibility |
| evaluation_protocol | Contribution claim traceability JSON | experiments/cape_kg_eacl_20260627/06_release/contribution_claim_traceability.json | yes | public_safe | reproducibility |
| evaluation_protocol | Contribution claim traceability CSV | experiments/cape_kg_eacl_20260627/06_release/contribution_claim_traceability.csv | yes | public_safe | reproducibility |
| evaluation_protocol | Related-work baseline traceability | experiments/cape_kg_eacl_20260627/06_release/related_work_baseline_traceability.md | yes | public_safe | reproducibility |
| evaluation_protocol | Related-work baseline traceability JSON | experiments/cape_kg_eacl_20260627/06_release/related_work_baseline_traceability.json | yes | public_safe | reproducibility |
| evaluation_protocol | Related-work baseline traceability CSV | experiments/cape_kg_eacl_20260627/06_release/related_work_baseline_traceability.csv | yes | public_safe | reproducibility |
| evaluation_protocol | Annotation protocol traceability | experiments/cape_kg_eacl_20260627/06_release/annotation_protocol_traceability.md | yes | internal_only | human annotation protocol traceability; internal review path references |
| evaluation_protocol | Annotation protocol traceability JSON | experiments/cape_kg_eacl_20260627/06_release/annotation_protocol_traceability.json | yes | internal_only | human annotation protocol traceability; internal review path references |
| evaluation_protocol | Annotation protocol traceability CSV | experiments/cape_kg_eacl_20260627/06_release/annotation_protocol_traceability.csv | yes | internal_only | human annotation protocol traceability; internal review path references |
| evaluation_protocol | Method novelty positioning | experiments/cape_kg_eacl_20260627/06_release/method_novelty_positioning.md | yes | live_release_status | reproducibility |
| evaluation_protocol | Method novelty positioning JSON | experiments/cape_kg_eacl_20260627/06_release/method_novelty_positioning.json | yes | live_release_status | reproducibility |
| evaluation_protocol | Qwen3 model-scaling report | experiments/cape_kg_eacl_20260627/06_release/qwen3_model_scaling_report.md | yes | live_release_status | reproducibility |
| evaluation_protocol | Qwen3 model-scaling report JSON | experiments/cape_kg_eacl_20260627/06_release/qwen3_model_scaling_report.json | yes | live_release_status | reproducibility |
| evaluation_protocol | CQ query pack | experiments/cape_kg_eacl_20260627/06_release/cq_query_pack.md | yes | public_safe | reproducibility |
| traceability | Prompt to node/edge traceability | experiments/cape_kg_eacl_20260627/06_release/prompt_node_edge_traceability.md | yes | public_safe | reproducibility |
| traceability | Prompt to node/edge traceability JSON | experiments/cape_kg_eacl_20260627/06_release/prompt_node_edge_traceability.json | yes | public_safe | reproducibility |
| traceability | Evidence graph projection report | outputs/13_evidence_graph/evidence_graph_projection_report.md | yes | internal_only | source-grounded graph projection; source text omitted |
| traceability | Evidence graph projection summary | outputs/13_evidence_graph/evidence_graph_projection_summary.json | yes | internal_only | source-grounded graph projection; source text omitted |
| traceability | Predicate cue span diagnostic report | experiments/cape_kg_eacl_20260627/04_evaluation/predicate_cue_span_report.md | yes | internal_only | automatic predicate cue diagnostic; source text omitted |
| traceability | Predicate cue span diagnostic metrics | experiments/cape_kg_eacl_20260627/04_evaluation/predicate_cue_span_metrics.json | yes | internal_only | automatic predicate cue diagnostic; source text omitted |
| traceability | Predicate cue span diagnostic rows | experiments/cape_kg_eacl_20260627/04_evaluation/predicate_cue_span_rows.csv | yes | internal_only | automatic predicate cue diagnostic; source text omitted |
| traceability | Predicate cue span JSONL | outputs/06_triples/layer2_predicate_cue_spans.jsonl | yes | internal_only | automatic predicate cue diagnostic; source text omitted |
| traceability | Neo4j evidence query pack | experiments/cape_kg_eacl_20260627/06_release/neo4j_evidence_query_pack.md | yes | internal_only | Neo4j Browser queries for EvidenceAnchor/EVIDENCED_BY inspection |
| traceability | Neo4j evidence query pack JSON | experiments/cape_kg_eacl_20260627/06_release/neo4j_evidence_query_pack.json | yes | internal_only | Neo4j Browser queries for EvidenceAnchor/EVIDENCED_BY inspection |
| synthetic_public_examples | Synthetic example README | experiments/cape_kg_eacl_20260627/06_release/public_synthetic_examples/README.md | yes | public_safe | reproducibility |
| synthetic_public_examples | Synthetic chunks | experiments/cape_kg_eacl_20260627/06_release/public_synthetic_examples/synthetic_chunks.jsonl | yes | public_safe | reproducibility |
| synthetic_public_examples | Synthetic gold labels | experiments/cape_kg_eacl_20260627/06_release/public_synthetic_examples/synthetic_gold.jsonl | yes | public_safe | reproducibility |
| synthetic_public_examples | Synthetic predictions | experiments/cape_kg_eacl_20260627/06_release/public_synthetic_examples/synthetic_predictions.jsonl | yes | public_safe | reproducibility |
| synthetic_public_examples | Synthetic evaluation summary | experiments/cape_kg_eacl_20260627/06_release/public_synthetic_examples/synthetic_evaluation_summary.json | yes | public_safe | reproducibility |
| public_benchmarks | Public benchmark manifest | experiments/cape_kg_eacl_20260627/08_public_benchmarks/public_benchmark_manifest.json | yes | public_safe | reproducibility |
| public_benchmarks | Public benchmark adapter report | experiments/cape_kg_eacl_20260627/08_public_benchmarks/public_benchmark_adapter_report.md | yes | public_safe | reproducibility |
| public_benchmarks | Public benchmark cross-check report | experiments/cape_kg_eacl_20260627/08_public_benchmarks/public_benchmark_crosscheck_report.md | yes | public_safe | reproducibility |
| public_benchmarks | Public benchmark cross-check summary | experiments/cape_kg_eacl_20260627/08_public_benchmarks/public_benchmark_crosscheck_summary.json | yes | public_safe | reproducibility |
| public_benchmarks | Qwen3 8B subset report | experiments/cape_kg_eacl_20260627/08_public_benchmarks/public_qwen3_8b_subset_eval_report.md | yes | public_safe | reproducibility |
| public_benchmarks | Qwen3 8B subset summary | experiments/cape_kg_eacl_20260627/08_public_benchmarks/public_qwen3_8b_subset_eval_summary.json | yes | public_safe | reproducibility |
| public_benchmarks | Qwen3 14B subset report | experiments/cape_kg_eacl_20260627/08_public_benchmarks/public_qwen3_14b_subset_eval_report.md | yes | public_safe | reproducibility |
| public_benchmarks | Qwen3 14B subset summary | experiments/cape_kg_eacl_20260627/08_public_benchmarks/public_qwen3_14b_subset_eval_summary.json | yes | public_safe | reproducibility |
| release_safety | Data release and ethics statement | experiments/cape_kg_eacl_20260627/06_release/data_release_ethics_statement.md | yes | public_safe | reproducibility |
| release_safety | External resource license report | experiments/cape_kg_eacl_20260627/06_release/external_resource_license_report.md | yes | public_safe | reproducibility |
| release_safety | External resource license report JSON | experiments/cape_kg_eacl_20260627/06_release/external_resource_license_report.json | yes | public_safe | reproducibility |
| release_safety | Release bundle safety report | experiments/cape_kg_eacl_20260627/06_release/release_bundle_safety_report.md | yes | live_release_status | reproducibility |
| release_safety | Latest release bundle index | experiments/cape_kg_eacl_20260627/06_release/latest_release_bundle_index.md | yes | live_release_status | reproducibility |
| internal_only | Full graph visualization and source-grounded graph files | outputs/09_visualization/kg_viewer.html | yes | internal_only | demo; inspect before public release |
| internal_only | Full graph RDF export | outputs/12_rdf/cape_kg_layer2.ttl | yes | internal_only | derived graph; inspect before public release |
| internal_only | Neo4j source-grounded import package | outputs/11_neo4j_import_flat/README.md | yes | internal_only | derived graph; includes EvidenceAnchor projection without source text |
| internal_only | Neo4j source-grounded import validation | outputs/11_neo4j_import_flat/neo4j_csv_validation_report.md | yes | internal_only | parser and evidence-projection validation |
| internal_only | Neo4j source-grounded evidence Cypher queries | outputs/11_neo4j_import_flat/neo4j_evidence_queries.cypher | yes | internal_only | Neo4j Browser query helper; source text omitted |
| internal_only | EvidenceAnchor node projection | outputs/13_evidence_graph/evidence_anchor_nodes.jsonl | yes | internal_only | derived graph; source text omitted |
| internal_only | EVIDENCED_BY edge projection | outputs/13_evidence_graph/evidenced_by_edges.jsonl | yes | internal_only | derived graph; source text omitted |
| internal_only | Gold subset sampling coverage report | experiments/cape_kg_eacl_20260627/06_release/gold_sampling_coverage_report.md | yes | internal_only | private review selection evidence |

## Notes

- The source corpus itself is not part of the public-safe skeleton.
- Synthetic examples are only format and release-safety artifacts.
- Public benchmark rows are auxiliary generalization evidence, not the main private-domain human-gold result.
- Final submission-level claims still require human-gold and expert-review returns.
