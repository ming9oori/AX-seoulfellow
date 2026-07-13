# CAPE-KG Pre-Human Handoff Validation

Generated: 2026-06-29T18:57:01.337759+00:00
Overall status: `PASS`
Claim status: `pre_human_handoff_ready_not_submission_complete`

## Summary

- Checks: 92
- PASS: 91
- WARN: 1
- FAIL: 0

## Checks

| id | status | detail |
|---|---|---|
| `required_files_present` | `PASS` | All required files are present. |
| `claim_gate_known_human_blockers` | `WARN` | Submission claims are still pending human gold, IAA, adjudication, and human-gold scoring. |
| `readiness_status_expected` | `PASS` | Readiness audit is in the expected pre-human pending state. |
| `claim_gate_blocker_alignment` | `PASS` | Claim gate FAIL/PASS states are aligned with readiness blockers, human-gold pending state, and mapping expert pending state. |
| `requirements_matrix_traceability` | `PASS` | Requirements matrix traceability is synchronized with the submission readiness audit. |
| `eacl_plan_compliance_matrix` | `PASS` | EACL plan compliance matrix is synchronized with readiness audit item IDs/statuses and current source artifacts. |
| `revised_plan_completion_audit` | `PASS` | Revised plan completion audit proves automatic-stage readiness while keeping human-gated completion unclaimed. |
| `public_revised_plan_completion_audit` | `PASS` | Public-safe revised plan completion audit mirrors completion status without private paths or source text. |
| `revised_plan_section_status` | `PASS` | Korean section-by-section revised-plan status table is synchronized with current gates and audits. |
| `metric_traceability_audit` | `PASS` | Revised-plan metrics are linked to evaluator scripts, outputs, protocol definitions, paper tables, and human/expert gates. |
| `contribution_claim_traceability` | `PASS` | Revised-plan contribution statements are linked to current evidence, metrics, reviewer concerns, and human/expert claim gates. |
| `related_work_baseline_traceability` | `PASS` | Plan related-work references are linked to local baselines, public adapters, validation standards, provenance artifacts, and claim boundaries. |
| `annotation_protocol_traceability` | `PASS` | Plan annotation requirements are linked to protocol, schema, batch, IAA/adjudication, return-file, and gate evidence. |
| `method_module_coverage_claim_safety` | `PASS` | CAPE-KG M1-M11 executable artifacts are covered while human-dependent final claims remain pending. |
| `paper_readiness_checklist` | `PASS` | Paper readiness checklist separates minimum and strong-accept gates and tracks the 1,500+ gold item requirement. |
| `rq_evidence_matrix` | `PASS` | RQ-to-evidence matrix covers RQ1-RQ4, all required evidence files exist, and final claims remain gated by human/expert review. |
| `evaluation_protocol_lock` | `PASS` | Evaluation protocol lock freezes metrics, condition sets, commands, claim policy, and file hashes before human returns. |
| `reviewer_risk_register` | `PASS` | Reviewer risk register covers 13 likely reviewer concerns, has complete evidence coverage, and keeps human/expert blockers open. |
| `cq_query_pack` | `PASS` | CQ query pack links all 12 competency questions to KG queries and sample answers. |
| `human_gold_span_iou_evaluator` | `PASS` | Human-gold component span exact/IoU evaluator is ready and conservatively pending adjudicated span returns. |
| `evidence_grounding_report_claim_safety` | `PASS` | Evidence grounding report is explicitly scoped as silver/proxy and not human-gold evidence. |
| `evidence_span_granularity_claim_safety` | `PASS` | Component span granularity diagnostic is internally consistent and scoped as non-human-gold evidence. |
| `predicate_cue_span_diagnostic` | `PASS` | Automatic predicate cue span diagnostic is internally consistent and source-text safe. |
| `edge_component_span_traceability` | `PASS` | Final KG edges trace to source triples and automatic component spans without including source text. |
| `active_review_diagnostics_claim_safety` | `PASS` | Active-review ablation and human-effort artifacts are explicitly scoped as silver/proxy or pending human timing. |
| `mapping_downstream_claim_safety` | `PASS` | Mapping downstream, expert-review, and NCS-PCF crosswalk artifacts are candidate-only or pending expert review. |
| `llm_diagnostics_public_benchmark_claim_safety` | `PASS` | LLM diagnostics, statistical tests, model scaling, strict-JSON diagnostics, and public benchmark cross-checks are scoped as silver/proxy or auxiliary diagnostics. |
| `ablation_coverage_report` | `PASS` | Planned baseline, LLM ablation, and active-review ablation diagnostics are covered while final performance claims remain human-gold gated. |
| `alias_canonicalization_report` | `PASS` | M9 alias/canonicalization coverage, collision queue, and human-gold node matching boundary are synchronized. |
| `handoff_claim_status` | `PASS` | Human review handoff status is ready for review. |
| `handoff_batch_coverage` | `PASS` | Handoff covers the minimum priority-100 human review set. |
| `handoff_annotator_manifests` | `PASS` | Annotator A/B manifests each cover 100 unique chunks. |
| `handoff_bundle_manifest_hashes` | `PASS` | Handoff bundle files match manifest hashes. |
| `handoff_bundle_contents` | `PASS` | Human review handoff tarballs contain the expected role-specific review inputs, guidance, and import/validation scripts. |
| `component_span_handoff_coverage` | `PASS` | Human-review candidate edges include conservative subject/predicate/object component span suggestions. |
| `prompt_node_edge_traceability` | `PASS` | Prompt files, CQ definitions, LLM output summaries, and final KG node/edge counts are traceable and synchronized. |
| `schema_retrieval_coverage_report` | `PASS` | CQ-linked schema retrieval is represented by proposed, ablation, and taxonomy baseline conditions with claim-safe silver diagnostics. |
| `schema_plan_alignment` | `PASS` | Plan schema terms are classified across canonical Layer 2, evidence/mapping projections, and known structural-review gaps. |
| `llm_condition_output_integrity` | `PASS` | LLM baseline, proposed, and ablation valid outputs cover all expected chunks with valid JSON shape and chunk-local evidence anchors. |
| `human_return_field_error_guidance` | `PASS` | Human-return field guide and validation error playbook are ready for annotators, adjudicators, experts, and coordinators. |
| `human_review_guidance_ready` | `PASS` | Detailed annotation, adjudication, and mapping review guidance is present and included in handoff bundles. |
| `annotation_batch_review_preview` | `PASS` | Annotation candidate/span preview artifacts cover priority-100 chunks and the optional strong 342-unit package, and are included in handoff bundles. |
| `gold_sampling_coverage_report` | `PASS` | Gold subset sampling coverage report explains the priority-100 minimum annotation subset while keeping human-gold claims pending. |
| `gold_item_feasibility_report` | `PASS` | Gold item feasibility report shows the priority-100 candidate pool can cover the 500-item target while keeping human-gold claims pending. |
| `handoff_bundle_checksums` | `PASS` | Checksum verification passed. |
| `annotation_roundtrip_smoke` | `PASS` | Annotation import, IAA, adjudication, validation, and scoring smoke test passed without using real gold claims. |
| `active_review_effort_roundtrip_smoke` | `PASS` | Active-review effort CSV validation and human-effort metric smoke test passed without using real human-effort claims. |
| `mapping_roundtrip_smoke` | `PASS` | Mapping import and expert-metric smoke test passed without using real expert-review claims. |
| `crosswalk_roundtrip_smoke` | `PASS` | NCS-PCF crosswalk import and utility/ranking metric smoke test passed without using real expert-review claims. |
| `claimable_main_table` | `PASS` | Claimable main table separates pending human-gold results from diagnostic-only metrics. |
| `claim_language_guardrails` | `PASS` | Claim-language guardrails define safe and unsafe paper/presentation wording for all current claim classes. |
| `reviewer_response_prep` | `PASS` | Reviewer response prep maps the revised-plan reviewer questions to evidence, safe answers, and remaining gates. |
| `submission_timeline_action_board` | `PASS` | Submission timeline action board maps the revised-plan schedule to current gates and critical-path actions. |
| `paper_table_blueprint` | `PASS` | Paper table blueprint separates final main tables from diagnostics, appendix material, and pending human/expert gates. |
| `arr_submission_policy_checklist` | `PASS` | ARR/EACL submission policy checklist maps official policy items to draft sections, release artifacts, and manual gates. |
| `anonymized_submission_prep` | `PASS` | Anonymized submission prep scans manuscript/supplement risks while keeping upload-ready status false. |
| `responsible_nlp_checklist_prep` | `PASS` | Responsible NLP checklist prep maps ethics, societal-impact, data, LLM-use, reproducibility, and author-confirmation answers to evidence while keeping final answers pending. |
| `experiment_reproduction_card` | `PASS` | Experiment reproduction card maps all baselines, ablations, proposed outputs, commands, and claim gates without promoting silver metrics to final claims. |
| `paper_tables_claim_safety` | `PASS` | Paper tables separate pending human-gold/expert-review results from silver/proxy diagnostics in both Markdown and LaTeX. |
| `paper_section_source_map` | `PASS` | Paper section source map covers the planned long-paper sections and preserves human-gold/expert-review claim boundaries. |
| `post_human_scoring_readiness` | `PASS` | Post-human scoring readiness map links plan metrics to human/expert return files, refresh commands, and output tables. |
| `eacl_submission_package_manifest` | `PASS` | EACL submission package manifest separates ready diagnostic/release components from human-gold and expert-review blockers. |
| `data_release_ethics_statement` | `PASS` | Data release and ethics statement plus external resource license report document public-safe release boundaries, benchmark licenses/citations, reproducibility mitigation, human-review privacy, LLM risk, and pending claim status. |
| `provenance_manifest` | `PASS` | Provenance manifest indexes source files, prompts, schemas, LLM runs, evaluation files, human-review handoffs, and release artifacts. |
| `layer2_evidence_triple_integrity` | `PASS` | Final Layer 2 nodes/edges, source triples, and evidence anchors are internally consistent. |
| `evidence_graph_projection_integrity` | `PASS` | EvidenceAnchor nodes and EVIDENCED_BY edges match Layer 2 evidence_anchor_ids; source text is omitted. |
| `rdf_shacl_export` | `PASS` | Layer 2 KG RDF export and SHACL-style validation artifacts are present and pass structural checks. |
| `human_review_return_preflight` | `PASS` | Human review return preflight is configured and currently has no validation errors. |
| `strong_review_return_preflight` | `PASS` | Optional strong 300+ return preflight is configured and currently has no validation errors. |
| `human_gate_action_plan` | `PASS` | Human gate action plan is synchronized with return preflight and split human-return files. |
| `human_review_status_dashboard` | `PASS` | Human review status dashboard is synchronized with return preflight and next-action CSV. |
| `human_review_first_batch_execution_card` | `PASS` | Human review first-batch execution card is synchronized with A/B batch files, dashboard links, guardrails, and safe commands. |
| `human_review_role_quickstart_cards` | `PASS` | Human review role quickstart cards are synchronized with role bundles, dashboard links, return files, and safe commands. |
| `human_review_launch_checklist` | `PASS` | Human review launch checklist maps the minimum paper-gate return files to day-1 tasks and safe commands. |
| `human_review_packet_integrity` | `PASS` | Human-review packet integrity is ready and still correctly marked pending human returns. |
| `human_return_apply_wrapper_safety` | `PASS` | Human-return apply wrapper records dry-run success and empty-apply refusal evidence. |
| `strong_return_apply_wrapper_safety` | `PASS` | Strong-return apply wrapper records dry-run success and empty-apply refusal evidence. |
| `eacl_paper_draft_claim_safety` | `PASS` | EACL paper draft is synchronized with the conservative claim gate, split human-return plan, and standard paper section skeleton. |
| `current_reports_index` | `PASS` | Current report index points users to the canonical professor-report, paper-draft, release-gate, and post-annotation refresh artifacts. |
| `neo4j_csv_validation` | `PASS` | Neo4j CSV validation reports passed and include the EvidenceAnchor/EVIDENCED_BY projection. |
| `neo4j_evidence_query_pack` | `PASS` | Neo4j evidence query pack is synchronized with the current EvidenceAnchor/EVIDENCED_BY import package. |
| `kg_visualization_demo` | `PASS` | KG visualization/demo artifacts are present and synchronized with current Layer 2 graph counts. |
| `public_reproducibility_manifest` | `PASS` | Public reproducibility manifest maps plan requirements to public-safe artifacts and is included in the public-safe bundle. |
| `public_synthetic_examples_claim_safety` | `PASS` | Public synthetic examples are schema-shaped, source-text safe, and explicitly not paper-result evidence. |
| `public_safe_manifest_risk_scan` | `PASS` | Public-safe manifest risk scan is empty. |
| `public_safe_text_reference_scan` | `PASS` | Public-safe text files do not mention conservative internal path/name patterns. |
| `public_external_release_review_queue` | `PASS` | Public external release review queue is synchronized with the public-safe text reference scan. |
| `release_bundle_manifest_hashes` | `PASS` | Release bundle files match manifest hashes. |
| `release_bundle_no_stale_nested_artifacts` | `PASS` | Release bundles exclude stale nested bundle metadata/checksum artifacts. |
| `public_safe_tar_content_scan` | `PASS` | Public-safe bundle excludes internal-review and source-text paths. |
| `report_validation_summary_freshness` | `PASS` | Report and release markdown files do not contain known stale pre-human validation count patterns. |
| `release_bundle_checksums` | `PASS` | Checksum verification passed. |

## Interpretation

- `PASS` means the pre-human handoff infrastructure is ready.
- `WARN` keeps the known paper-claim blocker visible: human gold, IAA, adjudication, and human-gold scoring are not complete.
- Any `FAIL` means the handoff/release artifacts should be fixed before asking annotators to start.
