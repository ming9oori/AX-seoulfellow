# CAPE-KG EACL Experiment Report

Generated: 2026-06-29T18:55:35.935985+00:00

## Scope

This package follows `AX_EACL_submission_review_revised_plan.md` by reframing
the AX task as CAPE-KG: competency-question anchored procedural evidence
grounding for domain KG construction.

## Data

- Source KG directory: `outputs`
- OCR workbook: `handoff-hanyang/자이제_ocr_preprocessed.xlsx`
- Total chunks available: 214
- Evaluation chunks selected: 120
- Silver reference nodes: 208
- Silver reference edges: 900
- Silver evidence anchors: 293

## Main Silver/Proxy Results

These numbers validate the evaluation code path. They are not final paper
claims until the silver reference is replaced with human gold and the actual
LLM generations are scored against adjudicated labels.

- B0_plain_llm_proxy: Edge F1=0.1927, Evidence EM=0.0, Ontology=0.0, Procedural=0.9762
- B1_predicate_constrained_proxy: Edge F1=0.8889, Evidence EM=1.0, Ontology=0.0, Procedural=0.9175
- B2_current_project_baseline: Edge F1=1.0, Evidence EM=1.0, Ontology=1.0, Procedural=1.0
- B4_taxonomy_rag_proxy: Edge F1=0.8079, Evidence EM=1.0, Ontology=1.0, Procedural=1.0
- B5_procedural_prompt_proxy: Edge F1=0.4361, Evidence EM=1.0, Ontology=1.0, Procedural=1.0
- P_cape_kg_silver: Edge F1=1.0, Evidence EM=1.0, Ontology=1.0, Procedural=1.0
- P_minus_CQ_proxy: Edge F1=0.9091, Evidence EM=1.0, Ontology=1.0, Procedural=1.0
- P_minus_Evidence_proxy: Edge F1=1.0, Evidence EM=0.0, Ontology=1.0, Procedural=1.0
- P_minus_Procedural_schema_proxy: Edge F1=0.838, Evidence EM=1.0, Ontology=1.0, Procedural=1.0
- P_minus_Validator_proxy: Edge F1=0.9858, Evidence EM=0.9725, Ontology=0.9524, Procedural=1.0
- P_minus_Standard_bridge_proxy: Edge F1=1.0, Evidence EM=1.0, Ontology=1.0, Procedural=1.0

## CQ Answerability

- P_cape_kg_silver mean CQ score: 5.00/5

## Mapping Downstream

- NCS: coverage=1.0 top5_rows=110 reason_rate=1.0
- PCF: coverage=1.0 top5_rows=110 reason_rate=1.0

### Mapping Expert Review

- Review manifest: `experiments/cape_kg_eacl_20260627/01_data/mapping_review/mapping_review_manifest.json`
- Review workbench: `experiments/cape_kg_eacl_20260627/01_data/mapping_review/mapping_review_workbench.html`
- Safe import dry run: `python3 scripts/import_cape_mapping_review.py --experiment-dir experiments/cape_kg_eacl_20260627 --reviewed-file experiments/cape_kg_eacl_20260627/01_data/mapping_review/mapping_review_items.reviewed.jsonl`
- Candidate rows: 220
- Evaluation report: `experiments/cape_kg_eacl_20260627/04_evaluation/mapping_expert_evaluation_report.md`
- Progress report: `experiments/cape_kg_eacl_20260627/06_release/mapping_review_progress_report.md`
- Priority queue: `experiments/cape_kg_eacl_20260627/05_review/mapping_review_priority_queue.csv`
- Next 20 groups: `experiments/cape_kg_eacl_20260627/05_review/mapping_review_next_20_groups.csv`
- Next 60 rows: `experiments/cape_kg_eacl_20260627/05_review/mapping_review_next_60_rows.csv`
- Review progress: completed_rows=0, pending_rows=220, complete_source_groups=0, pending_source_groups=44, status=pending_or_partial_expert_review
- NCS: completed_rows=0, pending_rows=110, Hit@5=pending_expert_review, P@5=pending_expert_review, MRR=pending_expert_review, status=pending_expert_review
- PCF: completed_rows=0, pending_rows=110, Hit@5=pending_expert_review, P@5=pending_expert_review, MRR=pending_expert_review, status=pending_expert_review

## Active Review

- Silver/proxy review queue items: 900
- Highest priority: 0.317235

### Actual LLM Active-Review Diagnostic

- Report: `experiments/cape_kg_eacl_20260627/04_evaluation/active_review_efficiency_report.md`
- Metrics: `experiments/cape_kg_eacl_20260627/04_evaluation/active_review_efficiency_metrics.json`
- Queue JSONL: `experiments/cape_kg_eacl_20260627/05_review/actual_llm_active_review_queue_P_cape_kg_actual.jsonl`
- Candidate edges: 275
- Silver/proxy error rate: 0.992727
- High-impact silver/proxy error rate: 0.629091
- active_priority @ 10: precision=0.6, recall=0.034682, lift=0.953757
- active_priority @ 25: precision=0.64, recall=0.092486, lift=1.017341
- active_priority @ 55: precision=0.654545, recall=0.208092, lift=1.040462
- active_priority @ 100: precision=0.56, recall=0.323699, lift=0.890173
- uncertainty_only @ 10: precision=0.6, recall=0.034682, lift=0.953757
- uncertainty_only @ 25: precision=0.6, recall=0.086705, lift=0.953757
- uncertainty_only @ 55: precision=0.690909, recall=0.219653, lift=1.098266
- uncertainty_only @ 100: precision=0.72, recall=0.416185, lift=1.144509

This is a silver/proxy prioritization diagnostic, not a human review efficiency claim.

## Local LLM Extraction Run

- Raw chunk rows: 120
- Valid task frames: 59
- Valid procedural relations: 72
- Raw rows with parse/generation errors: 61
- Report: `experiments/cape_kg_eacl_20260627/47_llm_extraction_quality_report.md`

This validates the local Qwen3-8B extraction path over the selected chunks. It is still not a condition-specific B0/B1/B2/B4/B5 baseline matrix.

## Additional LLM Model Runs

- llama2_13b_chat_tool_extractions: raw_rows=10, task_frames=8, relations=2, rejections=8, parse_or_generation_error_rows=2, report=`experiments/cape_kg_eacl_20260627/47_llama2_13b_chat_tool_extractions_quality_report.md`

These are smoke/model-compatibility runs unless their chunk count and prompts match the full baseline matrix.

## Model Selection and Scaling

- Plan: `experiments/cape_kg_eacl_20260627/06_release/model_selection_and_scaling_plan.md`
- Current paper-package model: Qwen3-8B 4bit full 120-chunk condition runs.
- Stronger local diagnostic run: Qwen3-14B 4bit full 120-chunk B0/B1/B2/P core conditions.
  - Run report: `experiments/cape_kg_eacl_20260627/50_qwen3_14b_core_conditions_120_quality_report.md`
  - Silver proxy report: `experiments/cape_kg_eacl_20260627/04_evaluation/qwen3_14b_core_silver_evaluation_report.md`
- Stronger local diagnostic run: Qwen3-32B-AWQ full 120-chunk B0/B1/B2/P core conditions.
  - Run report: `experiments/cape_kg_eacl_20260627/50_qwen3_32b_awq_core_120_quality_report.md`
  - Silver proxy report: `experiments/cape_kg_eacl_20260627/04_evaluation/qwen3_32b_awq_core_silver_evaluation_report.md`
- Compatibility smoke run: Llama-2-13B-chat 4bit on 10 chunks.
- Remaining stronger local next-run candidate: standard Qwen3-32B after sufficient disk space is available.
- Current hardware assumption: 8 x RTX 3090 GPUs; Qwen3-32B template uses four shards with two GPUs per shard.
- Qwen3-32B-AWQ readiness: `core_run_complete`
  - Report: `experiments/cape_kg_eacl_20260627/06_release/qwen3_32b_awq_readiness.md`
  - Next action: Qwen3-32B-AWQ core 120-chunk run is complete; use human-gold scoring before paper claims.

Qwen3-14B/32B-AWQ improve the local model-strength evidence, but paper-level claims remain provisional until human-gold scoring is available.

## Strict JSON Diagnostics

- Report: `experiments/cape_kg_eacl_20260627/06_release/strict_json_diagnostics.md`
- Priority CSV: `experiments/cape_kg_eacl_20260627/05_review/strict_json_reprompt_priority.csv`
- Contract prompt: `experiments/cape_kg_eacl_20260627/02_schema/prompts/strict_json_contract.txt`
- Strict JSON gate: PASS
- Recovery gate: PASS
- Conditions over strict threshold: 0
- Conditions over unrepaired threshold: 0

This diagnostic does not change existing generated outputs; it documents parse recovery and provides a strict JSON contract for future smoke/full reruns.

## Plan Requirements Audit

- Report: `experiments/cape_kg_eacl_20260627/06_release/submission_readiness_audit.md`
- Metrics: `experiments/cape_kg_eacl_20260627/06_release/submission_readiness_audit.json`
- Claim status: pending_human_gold_iaa_and_human_gold_scoring
- Audited items: 20
- Status counts: `{'pending_human': 5, 'pass': 11, 'partial': 4}`
- Minimum-accept blocking items: 4
  - min.gold_chunks: 100+ adjudicated gold chunks -> Complete two-annotator labeling and adjudication for at least 100 chunks.
  - min.gold_items: 500+ adjudicated gold node/edge/evidence items -> Adjudicate enough nodes, edges, and evidence anchors to reach 500 gold items.
  - min.iaa: 2+ annotators and agreement for 100+ chunks -> Import completed annotator A/B files and recompute IAA.
  - min.proposed: CAPE-KG proposed result completed and scored -> Score P_cape_kg_actual against adjudicated human gold after gold completion.

## Method Module Coverage

- Report: `experiments/cape_kg_eacl_20260627/06_release/method_module_coverage.md`
- Metrics: `experiments/cape_kg_eacl_20260627/06_release/method_module_coverage.json`
- Modules with required artifacts: 11/11
- Missing required artifacts: 0
- Human-dependent modules for final claims: 8
- Claim status: all_m1_m11_artifacts_present_human_claims_pending
- M1 Document structure recovery: implemented_artifacts_present; remaining=No additional automatic step required; source-text release still requires rights review.
- M2 CQ generation and selection: implemented_artifacts_present; remaining=Human-gold CQ answerability must be recomputed after adjudication.
- M3 CQ-linked schema retrieval: implemented_artifacts_present_human_claim_pending; remaining=Final claim requires human-gold comparison of P vs. schema-retrieval ablation.
- M4 Procedural frame extraction: implemented_artifacts_present_human_claim_pending; remaining=Human review should verify task/step correctness before final claims.
- M5 Evidence-span constrained triple extraction: implemented_artifacts_present_human_claim_pending; remaining=Component-level span diagnostics are present; character/span exactness must still be validated against adjudicated human gold.
- M6 Span verifier: implemented_artifacts_present_human_claim_pending; remaining=Current verifier evidence is silver/proxy; human-gold evidence metrics are pending.
- M7 Ontology/SHACL validator: implemented_artifacts_present; remaining=No additional automatic step required; final conformance table should use human-gold predictions.
- M8 Procedural consistency validator: implemented_artifacts_present_human_claim_pending; remaining=Human-gold procedural consistency should be recomputed after adjudication.
- M9 Alias/canonicalization module: implemented_artifacts_present_human_claim_pending; remaining=Final node canonicalization quality requires human-gold node matching.
- M10 Active review queue: implemented_artifacts_present_human_claim_pending; remaining=Active-review ablation is represented with silver/proxy diagnostics; final efficiency claim requires human adjudication outcomes and reviewer effort/timing.
- M11 NCS/PCF mapping evaluator: implemented_artifacts_present_human_claim_pending; remaining=P@K/MRR/nDCG@10, explanation-quality, crosswalk accept-rate, and utility claims require completed expert review.

## Condition-Specific LLM Baseline Runs

- qwen3_14b_core_conditions_120: raw_rows=480, report=`experiments/cape_kg_eacl_20260627/50_qwen3_14b_core_conditions_120_quality_report.md`
  - B0_plain_llm: raw_rows=120, valid_triples=892, valid_nodes=0, valid_edges=0, valid_mappings=0, parse_or_generation_error_rows=68, partial_json_repaired_rows=68
  - B1_predicate_constrained: raw_rows=120, valid_triples=0, valid_nodes=0, valid_edges=641, valid_mappings=0, parse_or_generation_error_rows=75, partial_json_repaired_rows=75
  - B2_current_project: raw_rows=120, valid_triples=0, valid_nodes=723, valid_edges=60, valid_mappings=0, parse_or_generation_error_rows=102, partial_json_repaired_rows=102
  - P_cape_kg_actual: raw_rows=120, valid_triples=0, valid_nodes=574, valid_edges=332, valid_mappings=10, parse_or_generation_error_rows=113, partial_json_repaired_rows=113
- qwen3_14b_core_conditions_smoke: raw_rows=16, report=`experiments/cape_kg_eacl_20260627/50_qwen3_14b_core_conditions_smoke_quality_report.md`
  - B0_plain_llm: raw_rows=4, valid_triples=13, valid_nodes=0, valid_edges=0, valid_mappings=0, parse_or_generation_error_rows=0, partial_json_repaired_rows=0
  - B1_predicate_constrained: raw_rows=4, valid_triples=0, valid_nodes=0, valid_edges=5, valid_mappings=0, parse_or_generation_error_rows=0, partial_json_repaired_rows=0
  - B2_current_project: raw_rows=4, valid_triples=0, valid_nodes=14, valid_edges=6, valid_mappings=0, parse_or_generation_error_rows=2, partial_json_repaired_rows=2
  - P_cape_kg_actual: raw_rows=4, valid_triples=0, valid_nodes=20, valid_edges=10, valid_mappings=0, parse_or_generation_error_rows=4, partial_json_repaired_rows=4
- qwen3_32b_awq_core_120: raw_rows=480, report=`experiments/cape_kg_eacl_20260627/50_qwen3_32b_awq_core_120_quality_report.md`
  - B0_plain_llm: raw_rows=120, valid_triples=897, valid_nodes=0, valid_edges=0, valid_mappings=0, parse_or_generation_error_rows=59, partial_json_repaired_rows=59
  - B1_predicate_constrained: raw_rows=120, valid_triples=0, valid_nodes=0, valid_edges=585, valid_mappings=0, parse_or_generation_error_rows=63, partial_json_repaired_rows=63
  - B2_current_project: raw_rows=120, valid_triples=0, valid_nodes=719, valid_edges=56, valid_mappings=0, parse_or_generation_error_rows=100, partial_json_repaired_rows=100
  - P_cape_kg_actual: raw_rows=120, valid_triples=0, valid_nodes=585, valid_edges=360, valid_mappings=5, parse_or_generation_error_rows=113, partial_json_repaired_rows=113
- qwen3_32b_awq_smoke: raw_rows=8, report=`experiments/cape_kg_eacl_20260627/50_qwen3_32b_awq_smoke_quality_report.md`
  - B0_plain_llm: raw_rows=4, valid_triples=8, valid_nodes=0, valid_edges=0, valid_mappings=0, parse_or_generation_error_rows=0, partial_json_repaired_rows=0
  - P_cape_kg_actual: raw_rows=4, valid_triples=0, valid_nodes=20, valid_edges=17, valid_mappings=0, parse_or_generation_error_rows=4, partial_json_repaired_rows=4
- qwen3_8b_b2_b4_condition_baselines_120: raw_rows=240, report=`experiments/cape_kg_eacl_20260627/50_qwen3_8b_b2_b4_condition_baselines_120_quality_report.md`
  - B2_current_project: raw_rows=120, valid_triples=0, valid_nodes=712, valid_edges=82, valid_mappings=0, parse_or_generation_error_rows=97, partial_json_repaired_rows=97
  - B4_taxonomy_rag: raw_rows=120, valid_triples=0, valid_nodes=674, valid_edges=128, valid_mappings=41, parse_or_generation_error_rows=102, partial_json_repaired_rows=102
- qwen3_8b_b2_b4_condition_smoke: raw_rows=10, report=`experiments/cape_kg_eacl_20260627/50_qwen3_8b_b2_b4_condition_smoke_quality_report.md`
  - B2_current_project: raw_rows=5, valid_triples=0, valid_nodes=9, valid_edges=6, valid_mappings=0, parse_or_generation_error_rows=2, partial_json_repaired_rows=0
  - B4_taxonomy_rag: raw_rows=5, valid_triples=0, valid_nodes=6, valid_edges=4, valid_mappings=5, parse_or_generation_error_rows=2, partial_json_repaired_rows=0
- qwen3_8b_cape_ablation_120: raw_rows=720, report=`experiments/cape_kg_eacl_20260627/50_qwen3_8b_cape_ablation_120_quality_report.md`
  - P_cape_kg_actual: raw_rows=120, valid_triples=0, valid_nodes=549, valid_edges=275, valid_mappings=52, parse_or_generation_error_rows=113, partial_json_repaired_rows=113
  - P_minus_CQ: raw_rows=120, valid_triples=0, valid_nodes=554, valid_edges=284, valid_mappings=35, parse_or_generation_error_rows=117, partial_json_repaired_rows=117
  - P_minus_Evidence: raw_rows=120, valid_triples=0, valid_nodes=514, valid_edges=259, valid_mappings=64, parse_or_generation_error_rows=103, partial_json_repaired_rows=103
  - P_minus_Procedural_schema: raw_rows=120, valid_triples=0, valid_nodes=528, valid_edges=247, valid_mappings=72, parse_or_generation_error_rows=107, partial_json_repaired_rows=107
  - P_minus_Standard_bridge: raw_rows=120, valid_triples=0, valid_nodes=572, valid_edges=338, valid_mappings=0, parse_or_generation_error_rows=59, partial_json_repaired_rows=59
  - P_minus_Validator: raw_rows=120, valid_triples=0, valid_nodes=557, valid_edges=271, valid_mappings=63, parse_or_generation_error_rows=110, partial_json_repaired_rows=110
- qwen3_8b_cape_ablation_smoke_limited: raw_rows=12, report=`experiments/cape_kg_eacl_20260627/50_qwen3_8b_cape_ablation_smoke_limited_quality_report.md`
  - P_cape_kg_actual: raw_rows=2, valid_triples=0, valid_nodes=4, valid_edges=3, valid_mappings=1, parse_or_generation_error_rows=1, partial_json_repaired_rows=0
  - P_minus_CQ: raw_rows=2, valid_triples=0, valid_nodes=0, valid_edges=0, valid_mappings=0, parse_or_generation_error_rows=2, partial_json_repaired_rows=0
  - P_minus_Evidence: raw_rows=2, valid_triples=0, valid_nodes=4, valid_edges=3, valid_mappings=1, parse_or_generation_error_rows=1, partial_json_repaired_rows=0
  - P_minus_Procedural_schema: raw_rows=2, valid_triples=0, valid_nodes=0, valid_edges=0, valid_mappings=0, parse_or_generation_error_rows=2, partial_json_repaired_rows=0
  - P_minus_Standard_bridge: raw_rows=2, valid_triples=0, valid_nodes=10, valid_edges=8, valid_mappings=0, parse_or_generation_error_rows=0, partial_json_repaired_rows=0
  - P_minus_Validator: raw_rows=2, valid_triples=0, valid_nodes=5, valid_edges=4, valid_mappings=1, parse_or_generation_error_rows=1, partial_json_repaired_rows=0
- qwen3_8b_cape_ablation_smoke: raw_rows=12, report=`experiments/cape_kg_eacl_20260627/50_qwen3_8b_cape_ablation_smoke_quality_report.md`
  - P_cape_kg_actual: raw_rows=2, valid_triples=0, valid_nodes=0, valid_edges=0, valid_mappings=0, parse_or_generation_error_rows=2, partial_json_repaired_rows=0
  - P_minus_CQ: raw_rows=2, valid_triples=0, valid_nodes=0, valid_edges=0, valid_mappings=0, parse_or_generation_error_rows=2, partial_json_repaired_rows=0
  - P_minus_Evidence: raw_rows=2, valid_triples=0, valid_nodes=0, valid_edges=0, valid_mappings=0, parse_or_generation_error_rows=2, partial_json_repaired_rows=0
  - P_minus_Procedural_schema: raw_rows=2, valid_triples=0, valid_nodes=0, valid_edges=0, valid_mappings=0, parse_or_generation_error_rows=2, partial_json_repaired_rows=0
  - P_minus_Standard_bridge: raw_rows=2, valid_triples=0, valid_nodes=10, valid_edges=8, valid_mappings=0, parse_or_generation_error_rows=0, partial_json_repaired_rows=0
  - P_minus_Validator: raw_rows=2, valid_triples=0, valid_nodes=0, valid_edges=0, valid_mappings=0, parse_or_generation_error_rows=2, partial_json_repaired_rows=0
- qwen3_8b_condition_baselines_120: raw_rows=360, report=`experiments/cape_kg_eacl_20260627/50_qwen3_8b_condition_baselines_120_quality_report.md`
  - B0_plain_llm: raw_rows=120, valid_triples=837, valid_nodes=0, valid_edges=0, valid_mappings=0, parse_or_generation_error_rows=63, partial_json_repaired_rows=63
  - B1_predicate_constrained: raw_rows=120, valid_triples=0, valid_nodes=0, valid_edges=663, valid_mappings=0, parse_or_generation_error_rows=63, partial_json_repaired_rows=63
  - B5_procedural_prompt: raw_rows=120, valid_triples=0, valid_nodes=957, valid_edges=119, valid_mappings=0, parse_or_generation_error_rows=96, partial_json_repaired_rows=96
- qwen3_8b_condition_baselines: raw_rows=30, report=`experiments/cape_kg_eacl_20260627/50_qwen3_8b_condition_baselines_quality_report.md`
  - B0_plain_llm: raw_rows=10, valid_triples=24, valid_nodes=0, valid_edges=0, valid_mappings=0, parse_or_generation_error_rows=1, partial_json_repaired_rows=0
  - B1_predicate_constrained: raw_rows=10, valid_triples=0, valid_nodes=0, valid_edges=20, valid_mappings=0, parse_or_generation_error_rows=2, partial_json_repaired_rows=0
  - B5_procedural_prompt: raw_rows=10, valid_triples=0, valid_nodes=20, valid_edges=14, valid_mappings=0, parse_or_generation_error_rows=5, partial_json_repaired_rows=0
- qwen3_8b_edc_schema_ablation: raw_rows=240, report=`experiments/cape_kg_eacl_20260627/50_qwen3_8b_edc_schema_ablation_quality_report.md`
  - B3_edc_style: raw_rows=120, valid_triples=0, valid_nodes=566, valid_edges=53, valid_mappings=0, parse_or_generation_error_rows=99, partial_json_repaired_rows=98
  - P_minus_Schema_retrieval: raw_rows=120, valid_triples=0, valid_nodes=566, valid_edges=308, valid_mappings=25, parse_or_generation_error_rows=109, partial_json_repaired_rows=109
- qwen3_8b_edc_schema_ablation_smoke: raw_rows=4, report=`experiments/cape_kg_eacl_20260627/50_qwen3_8b_edc_schema_ablation_smoke_quality_report.md`
  - B3_edc_style: raw_rows=2, valid_triples=0, valid_nodes=3, valid_edges=4, valid_mappings=0, parse_or_generation_error_rows=0, partial_json_repaired_rows=0
  - P_minus_Schema_retrieval: raw_rows=2, valid_triples=0, valid_nodes=10, valid_edges=5, valid_mappings=0, parse_or_generation_error_rows=2, partial_json_repaired_rows=2
- qwen3_8b_strict_json_1200_full: raw_rows=1560, report=`experiments/cape_kg_eacl_20260627/50_qwen3_8b_strict_json_1200_full_quality_report.md`
  - B0_plain_llm: raw_rows=120, valid_triples=1037, valid_nodes=0, valid_edges=0, valid_mappings=0, parse_or_generation_error_rows=16, partial_json_repaired_rows=16
  - B1_predicate_constrained: raw_rows=120, valid_triples=0, valid_nodes=0, valid_edges=805, valid_mappings=0, parse_or_generation_error_rows=17, partial_json_repaired_rows=17
  - B2_current_project: raw_rows=120, valid_triples=0, valid_nodes=867, valid_edges=334, valid_mappings=0, parse_or_generation_error_rows=63, partial_json_repaired_rows=63
  - B3_edc_style: raw_rows=120, valid_triples=0, valid_nodes=769, valid_edges=263, valid_mappings=0, parse_or_generation_error_rows=59, partial_json_repaired_rows=59
  - B4_taxonomy_rag: raw_rows=120, valid_triples=0, valid_nodes=719, valid_edges=323, valid_mappings=126, parse_or_generation_error_rows=76, partial_json_repaired_rows=76
  - B5_procedural_prompt: raw_rows=120, valid_triples=0, valid_nodes=1307, valid_edges=302, valid_mappings=0, parse_or_generation_error_rows=76, partial_json_repaired_rows=76
  - P_cape_kg_actual: raw_rows=120, valid_triples=0, valid_nodes=576, valid_edges=373, valid_mappings=227, parse_or_generation_error_rows=43, partial_json_repaired_rows=43
  - P_minus_CQ: raw_rows=120, valid_triples=0, valid_nodes=586, valid_edges=391, valid_mappings=233, parse_or_generation_error_rows=48, partial_json_repaired_rows=48
  - P_minus_Evidence: raw_rows=120, valid_triples=0, valid_nodes=574, valid_edges=383, valid_mappings=227, parse_or_generation_error_rows=39, partial_json_repaired_rows=39
  - P_minus_Procedural_schema: raw_rows=120, valid_triples=0, valid_nodes=558, valid_edges=353, valid_mappings=212, parse_or_generation_error_rows=42, partial_json_repaired_rows=42
  - P_minus_Schema_retrieval: raw_rows=120, valid_triples=0, valid_nodes=568, valid_edges=417, valid_mappings=216, parse_or_generation_error_rows=31, partial_json_repaired_rows=31
  - P_minus_Standard_bridge: raw_rows=120, valid_triples=0, valid_nodes=577, valid_edges=405, valid_mappings=0, parse_or_generation_error_rows=16, partial_json_repaired_rows=16
  - P_minus_Validator: raw_rows=120, valid_triples=0, valid_nodes=570, valid_edges=375, valid_mappings=229, parse_or_generation_error_rows=43, partial_json_repaired_rows=43
- qwen3_8b_strict_json_contract_smoke: raw_rows=16, report=`experiments/cape_kg_eacl_20260627/50_qwen3_8b_strict_json_contract_smoke_quality_report.md`
  - P_cape_kg_actual: raw_rows=4, valid_triples=0, valid_nodes=20, valid_edges=15, valid_mappings=1, parse_or_generation_error_rows=4, partial_json_repaired_rows=4
  - P_minus_CQ: raw_rows=4, valid_triples=0, valid_nodes=20, valid_edges=15, valid_mappings=1, parse_or_generation_error_rows=4, partial_json_repaired_rows=4
  - P_minus_Schema_retrieval: raw_rows=4, valid_triples=0, valid_nodes=20, valid_edges=15, valid_mappings=4, parse_or_generation_error_rows=3, partial_json_repaired_rows=3
  - P_minus_Validator: raw_rows=4, valid_triples=0, valid_nodes=20, valid_edges=15, valid_mappings=3, parse_or_generation_error_rows=4, partial_json_repaired_rows=4
- qwen3_8b_strict_json_nothink_1200_smoke: raw_rows=8, report=`experiments/cape_kg_eacl_20260627/50_qwen3_8b_strict_json_nothink_1200_smoke_quality_report.md`
  - P_cape_kg_actual: raw_rows=2, valid_triples=0, valid_nodes=10, valid_edges=8, valid_mappings=6, parse_or_generation_error_rows=0, partial_json_repaired_rows=0
  - P_minus_CQ: raw_rows=2, valid_triples=0, valid_nodes=10, valid_edges=8, valid_mappings=6, parse_or_generation_error_rows=0, partial_json_repaired_rows=0
  - P_minus_Schema_retrieval: raw_rows=2, valid_triples=0, valid_nodes=10, valid_edges=7, valid_mappings=4, parse_or_generation_error_rows=0, partial_json_repaired_rows=0
  - P_minus_Validator: raw_rows=2, valid_triples=0, valid_nodes=10, valid_edges=8, valid_mappings=4, parse_or_generation_error_rows=0, partial_json_repaired_rows=0
- qwen3_8b_strict_json_nothink_smoke: raw_rows=16, report=`experiments/cape_kg_eacl_20260627/50_qwen3_8b_strict_json_nothink_smoke_quality_report.md`
  - P_cape_kg_actual: raw_rows=4, valid_triples=0, valid_nodes=20, valid_edges=15, valid_mappings=1, parse_or_generation_error_rows=4, partial_json_repaired_rows=4
  - P_minus_CQ: raw_rows=4, valid_triples=0, valid_nodes=20, valid_edges=15, valid_mappings=0, parse_or_generation_error_rows=4, partial_json_repaired_rows=4
  - P_minus_Schema_retrieval: raw_rows=4, valid_triples=0, valid_nodes=20, valid_edges=16, valid_mappings=2, parse_or_generation_error_rows=4, partial_json_repaired_rows=4
  - P_minus_Validator: raw_rows=4, valid_triples=0, valid_nodes=20, valid_edges=15, valid_mappings=1, parse_or_generation_error_rows=4, partial_json_repaired_rows=4
- qwen3_8b_strict_json_warn_top3_full_1200: raw_rows=360, report=`experiments/cape_kg_eacl_20260627/50_qwen3_8b_strict_json_warn_top3_full_1200_quality_report.md`
  - B2_current_project: raw_rows=120, valid_triples=0, valid_nodes=867, valid_edges=334, valid_mappings=0, parse_or_generation_error_rows=63, partial_json_repaired_rows=63
  - B4_taxonomy_rag: raw_rows=120, valid_triples=0, valid_nodes=719, valid_edges=323, valid_mappings=126, parse_or_generation_error_rows=76, partial_json_repaired_rows=76
  - B5_procedural_prompt: raw_rows=120, valid_triples=0, valid_nodes=1307, valid_edges=302, valid_mappings=0, parse_or_generation_error_rows=76, partial_json_repaired_rows=76
- qwen3_8b_strict_json_warn_top3_full_2400: raw_rows=360, report=`experiments/cape_kg_eacl_20260627/50_qwen3_8b_strict_json_warn_top3_full_2400_quality_report.md`
  - B2_current_project: raw_rows=120, valid_triples=0, valid_nodes=980, valid_edges=619, valid_mappings=0, parse_or_generation_error_rows=18, partial_json_repaired_rows=18
  - B4_taxonomy_rag: raw_rows=120, valid_triples=0, valid_nodes=830, valid_edges=499, valid_mappings=333, parse_or_generation_error_rows=35, partial_json_repaired_rows=35
  - B5_procedural_prompt: raw_rows=120, valid_triples=0, valid_nodes=1705, valid_edges=706, valid_mappings=0, parse_or_generation_error_rows=39, partial_json_repaired_rows=39
- qwen3_8b_strict_json_warn_top3_smoke_1200: raw_rows=12, report=`experiments/cape_kg_eacl_20260627/50_qwen3_8b_strict_json_warn_top3_smoke_1200_quality_report.md`
  - B2_current_project: raw_rows=4, valid_triples=0, valid_nodes=14, valid_edges=11, valid_mappings=0, parse_or_generation_error_rows=0, partial_json_repaired_rows=0
  - B4_taxonomy_rag: raw_rows=4, valid_triples=0, valid_nodes=14, valid_edges=10, valid_mappings=8, parse_or_generation_error_rows=0, partial_json_repaired_rows=0
  - B5_procedural_prompt: raw_rows=4, valid_triples=0, valid_nodes=20, valid_edges=16, valid_mappings=0, parse_or_generation_error_rows=0, partial_json_repaired_rows=0
- sac_kg_verifier_pruner_baseline: raw_rows=120, report=`experiments/cape_kg_eacl_20260627/50_sac_kg_verifier_pruner_baseline_quality_report.md`
  - B6_sac_kg_verifier_pruner: raw_rows=120, valid_triples=0, valid_nodes=2281, valid_edges=361, valid_mappings=107, parse_or_generation_error_rows=0, partial_json_repaired_rows=0

These are actual condition-specific LLM generations, but currently smoke-scale unless raw_rows match the full evaluation set for each condition.

## Actual LLM Silver-Proxy Evaluation

- Report: `experiments/cape_kg_eacl_20260627/04_evaluation/actual_llm_silver_evaluation_report.md`
- Metrics: `experiments/cape_kg_eacl_20260627/04_evaluation/actual_llm_silver_metrics.json`
- B0_plain_llm: edge_exact_F1=0.0, predicate_F1=0.0, node_F1=0.034975, evidence_F1=0.023925, parse_or_generation_error_rows=63, partial_json_repaired_rows=63
- B1_predicate_constrained: edge_exact_F1=0.0, predicate_F1=0.141553, node_F1=0.0, evidence_F1=0.029059, parse_or_generation_error_rows=63, partial_json_repaired_rows=63
- B5_procedural_prompt: edge_exact_F1=0.00096, predicate_F1=0.009597, node_F1=0.02742, evidence_F1=0.060257, parse_or_generation_error_rows=96, partial_json_repaired_rows=96
- B2_current_project: edge_exact_F1=0.0, predicate_F1=0.006839, node_F1=0.021542, evidence_F1=0.050274, parse_or_generation_error_rows=97, partial_json_repaired_rows=97
- B4_taxonomy_rag: edge_exact_F1=0.0, predicate_F1=0.010511, node_F1=0.029974, evidence_F1=0.064055, parse_or_generation_error_rows=102, partial_json_repaired_rows=102
- B3_edc_style: edge_exact_F1=0.0, predicate_F1=0.011893, node_F1=0.019573, evidence_F1=0.031098, parse_or_generation_error_rows=99, partial_json_repaired_rows=98
- P_minus_Schema_retrieval: edge_exact_F1=0.00088, predicate_F1=0.073031, node_F1=0.021797, evidence_F1=0.059804, parse_or_generation_error_rows=109, partial_json_repaired_rows=109
- P_cape_kg_actual: edge_exact_F1=0.001786, predicate_F1=0.048214, node_F1=0.032597, evidence_F1=0.065527, parse_or_generation_error_rows=113, partial_json_repaired_rows=113
- P_minus_CQ: edge_exact_F1=0.0, predicate_F1=0.033793, node_F1=0.028546, evidence_F1=0.068178, parse_or_generation_error_rows=117, partial_json_repaired_rows=117
- P_minus_Evidence: edge_exact_F1=0.000899, predicate_F1=0.054856, node_F1=0.029703, evidence_F1=0.066594, parse_or_generation_error_rows=103, partial_json_repaired_rows=103
- P_minus_Procedural_schema: edge_exact_F1=0.003617, predicate_F1=0.097649, node_F1=0.030058, evidence_F1=0.068724, parse_or_generation_error_rows=107, partial_json_repaired_rows=107
- P_minus_Standard_bridge: edge_exact_F1=0.000868, predicate_F1=0.071211, node_F1=0.021324, evidence_F1=0.059004, parse_or_generation_error_rows=59, partial_json_repaired_rows=59
- P_minus_Validator: edge_exact_F1=0.001789, predicate_F1=0.045617, node_F1=0.029864, evidence_F1=0.065932, parse_or_generation_error_rows=110, partial_json_repaired_rows=110
- B6_sac_kg_verifier_pruner: edge_exact_F1=0.00172, predicate_F1=0.077386, node_F1=0.056352, evidence_F1=0.100771, parse_or_generation_error_rows=0, partial_json_repaired_rows=0

These are silver-reference diagnostics, not final human-gold paper scores.

## Model Scaling Silver-Proxy Diagnostics

- Source metrics: `experiments/cape_kg_eacl_20260627/04_evaluation/actual_llm_silver_metrics.json`, `experiments/cape_kg_eacl_20260627/04_evaluation/qwen3_14b_core_silver_metrics.json`, `experiments/cape_kg_eacl_20260627/04_evaluation/qwen3_32b_awq_core_silver_metrics.json`
- Qwen3-8B / B0_plain_llm: rows=120, edge_exact_F1=0.0, predicate_F1=0.0, node_F1=0.034975, evidence_F1=0.023925, parse_or_generation_error_rows=63, partial_json_repaired_rows=63
- Qwen3-8B / B1_predicate_constrained: rows=120, edge_exact_F1=0.0, predicate_F1=0.141553, node_F1=0.0, evidence_F1=0.029059, parse_or_generation_error_rows=63, partial_json_repaired_rows=63
- Qwen3-8B / B2_current_project: rows=120, edge_exact_F1=0.0, predicate_F1=0.006839, node_F1=0.021542, evidence_F1=0.050274, parse_or_generation_error_rows=97, partial_json_repaired_rows=97
- Qwen3-8B / P_cape_kg_actual: rows=120, edge_exact_F1=0.001786, predicate_F1=0.048214, node_F1=0.032597, evidence_F1=0.065527, parse_or_generation_error_rows=113, partial_json_repaired_rows=113
- Qwen3-14B / B0_plain_llm: rows=120, edge_exact_F1=0.0, predicate_F1=0.0, node_F1=0.032902, evidence_F1=0.025904, parse_or_generation_error_rows=68, partial_json_repaired_rows=68
- Qwen3-14B / B1_predicate_constrained: rows=120, edge_exact_F1=0.000767, predicate_F1=0.110514, node_F1=0.0, evidence_F1=0.024581, parse_or_generation_error_rows=75, partial_json_repaired_rows=75
- Qwen3-14B / B2_current_project: rows=120, edge_exact_F1=0.0, predicate_F1=0.007901, node_F1=0.019772, evidence_F1=0.039356, parse_or_generation_error_rows=102, partial_json_repaired_rows=102
- Qwen3-14B / P_cape_kg_actual: rows=120, edge_exact_F1=0.001741, predicate_F1=0.060078, node_F1=0.029751, evidence_F1=0.060955, parse_or_generation_error_rows=113, partial_json_repaired_rows=113
- Qwen3-32B-AWQ / B0_plain_llm: rows=120, edge_exact_F1=0.0, predicate_F1=0.0, node_F1=0.037736, evidence_F1=0.027304, parse_or_generation_error_rows=59, partial_json_repaired_rows=59
- Qwen3-32B-AWQ / B1_predicate_constrained: rows=120, edge_exact_F1=0.001569, predicate_F1=0.116078, node_F1=0.0, evidence_F1=0.022435, parse_or_generation_error_rows=63, partial_json_repaired_rows=63
- Qwen3-32B-AWQ / B2_current_project: rows=120, edge_exact_F1=0.0, predicate_F1=0.009896, node_F1=0.019359, evidence_F1=0.03871, parse_or_generation_error_rows=100, partial_json_repaired_rows=100
- Qwen3-32B-AWQ / P_cape_kg_actual: rows=120, edge_exact_F1=0.003441, predicate_F1=0.066237, node_F1=0.02835, evidence_F1=0.054153, parse_or_generation_error_rows=113, partial_json_repaired_rows=113

This compares completed local open-weight model scales on the shared B0/B1/B2/P core conditions. It is still silver/proxy evidence only.

## Statistical Silver-Proxy Diagnostics

- Report: `experiments/cape_kg_eacl_20260627/04_evaluation/statistical_analysis_report.md`
- Metrics: `experiments/cape_kg_eacl_20260627/04_evaluation/statistical_analysis_metrics.json`
- Bootstrap CSV: `experiments/cape_kg_eacl_20260627/04_evaluation/statistical_analysis_bootstrap.csv`
- McNemar CSV: `experiments/cape_kg_eacl_20260627/04_evaluation/statistical_analysis_mcnemar.csv`
- Per-chunk scores: `experiments/cape_kg_eacl_20260627/04_evaluation/statistical_analysis_chunk_scores.csv`
- Bootstrap iterations: 2000
- P vs B0_plain_llm (predicate_f1): delta=0.065814, 95% CI=[0.041384, 0.094497], p_approx=0.0
- P vs B0_plain_llm (node_label_f1): delta=0.001558, 95% CI=[-0.012699, 0.016308], p_approx=0.829
- P vs B0_plain_llm (evidence_f1): delta=0.031118, 95% CI=[0.022698, 0.040338], p_approx=0.0
- P vs B2_current_project (predicate_f1): delta=0.052411, 95% CI=[0.028477, 0.079871], p_approx=0.0
- P vs B2_current_project (node_label_f1): delta=0.013369, 95% CI=[0.002472, 0.025422], p_approx=0.018
- P vs B2_current_project (evidence_f1): delta=0.008677, 95% CI=[0.004498, 0.01324], p_approx=0.0
- P vs B3_edc_style (predicate_f1): delta=0.040066, 95% CI=[0.014748, 0.067981], p_approx=0.002
- P vs B3_edc_style (node_label_f1): delta=0.016398, 95% CI=[0.003792, 0.0306], p_approx=0.009
- P vs B3_edc_style (evidence_f1): delta=0.023881, 95% CI=[0.017186, 0.030731], p_approx=0.0
- P vs B4_taxonomy_rag (predicate_f1): delta=0.043845, 95% CI=[0.022175, 0.067886], p_approx=0.0
- P vs B4_taxonomy_rag (node_label_f1): delta=0.006646, 95% CI=[-0.0026, 0.0176], p_approx=0.191
- P vs B4_taxonomy_rag (evidence_f1): delta=0.000854, 95% CI=[-0.002604, 0.003991], p_approx=0.597
- P vs B5_procedural_prompt (predicate_f1): delta=0.048001, 95% CI=[0.018717, 0.079442], p_approx=0.004
- P vs B5_procedural_prompt (node_label_f1): delta=0.008757, 95% CI=[-0.002724, 0.020937], p_approx=0.156
- P vs B5_procedural_prompt (evidence_f1): delta=0.002572, 95% CI=[-0.001688, 0.007266], p_approx=0.234

These paired tests use silver/proxy labels only and must be rerun on adjudicated human gold before final claims.

## Human Gold Validation and Evaluation

- Validation report: `experiments/cape_kg_eacl_20260627/04_evaluation/human_gold_validation_report.md`
- Evaluation report: `experiments/cape_kg_eacl_20260627/04_evaluation/human_gold_evaluation_report.md`
- Metrics: `experiments/cape_kg_eacl_20260627/04_evaluation/human_gold_metrics.json`
- Completed/adjudicated chunks: 0
- Gold node/edge/evidence items: 0
- Validation errors: 0
- Claim status: pending_human_adjudication

No human-gold metrics are claimable yet because adjudication is still pending.

## Public Benchmark Adapters

- Manifest: `experiments/cape_kg_eacl_20260627/08_public_benchmarks/public_benchmark_manifest.json`
- PAGED: adapter_subset_items=100, status=gold_graph_reformatted_for_cape_external_subset_no_model_run
- Text2KGBench: adapter_subset_items=200, status=gold_triples_reformatted_for_cape_external_subset_no_model_run

### Public Subset Model Evaluations

- `experiments/cape_kg_eacl_20260627/08_public_benchmarks/public_qwen3_14b_subset_eval_summary.json`: PAGED items=10, Text2KG items=20, PAGED node F1=0.1733, PAGED edge-predicate F1=0.1446, Text2KG relation F1=0.2817, Text2KG triple exact F1=0.02
- `experiments/cape_kg_eacl_20260627/08_public_benchmarks/public_qwen3_8b_full_adapter_eval_summary.json`: PAGED items=100, Text2KG items=200, PAGED node F1=0.2472, PAGED edge-predicate F1=0.4233, Text2KG relation F1=0.6015, Text2KG triple exact F1=0.1736
- `experiments/cape_kg_eacl_20260627/08_public_benchmarks/public_qwen3_8b_subset_eval_summary.json`: PAGED items=10, Text2KG items=20, PAGED node F1=0.1608, PAGED edge-predicate F1=0.1794, Text2KG relation F1=0.45, Text2KG triple exact F1=0.05
- `experiments/cape_kg_eacl_20260627/08_public_benchmarks/public_qwen3_8b_subset_smoke_summary.json`: PAGED items=3, Text2KG items=5, PAGED node F1=0.0, PAGED edge-predicate F1=0.1333, Text2KG relation F1=0.4, Text2KG triple exact F1=0.0

These are public benchmark adapter runs, not official public leaderboard results.

## Public Synthetic Examples

- README: `experiments/cape_kg_eacl_20260627/06_release/public_synthetic_examples/README.md`
- Summary: `experiments/cape_kg_eacl_20260627/06_release/public_synthetic_examples/synthetic_evaluation_summary.json`
- Chunks: 2
- Nodes: 8
- Edges: 6
- Validation errors: 0
- Source-text policy: synthetic_only_no_source_corpus_text

These examples are format and release-safety artifacts only; they are not paper results.

## Human Gold Annotation Package

- Manifest: `experiments/cape_kg_eacl_20260627/01_data/gold_annotation/annotation_package_manifest.json`
- Status: ready_for_two_human_annotators_pending_labels
- Annotation workbench: `experiments/cape_kg_eacl_20260627/01_data/gold_annotation/annotation_workbench.html`
- Annotator safe import template: `python3 scripts/import_cape_gold_annotation.py --experiment-dir experiments/cape_kg_eacl_20260627 --target-file {target_annotator_jsonl} --reviewed-file {exported_annotator_jsonl}`
- Adjudication safe import template: `python3 scripts/import_cape_gold_annotation.py --experiment-dir experiments/cape_kg_eacl_20260627 --target-file {target_adjudication_jsonl} --reviewed-file {exported_adjudication_jsonl}`
- full_120: chunks=120, candidate_edges=1436, tracking=`experiments/cape_kg_eacl_20260627/01_data/gold_annotation/full_120/tracking_sheet.csv`
- pilot_30: chunks=30, candidate_edges=1121, tracking=`experiments/cape_kg_eacl_20260627/01_data/gold_annotation/pilot_30/tracking_sheet.csv`

### IAA Runs

- `experiments/cape_kg_eacl_20260627/01_data/gold_annotation/iaa_full_120/iaa_report.md`: completed_pair_chunks=0, pending_pair_chunks=120, status=pending_human_annotations
- `experiments/cape_kg_eacl_20260627/01_data/gold_annotation/iaa_pilot_30/iaa_report.md`: completed_pair_chunks=0, pending_pair_chunks=30, status=pending_human_annotations

### Adjudication Drafts

- `experiments/cape_kg_eacl_20260627/01_data/gold_annotation/full_120/adjudication_draft_report.md`: completed_pair_chunks=0, pending_pair_chunks=120, auto_adjudicated_chunks=0, needs_adjudication_chunks=0, status=draft_not_final_human_gold
- `experiments/cape_kg_eacl_20260627/01_data/gold_annotation/pilot_30/adjudication_draft_report.md`: completed_pair_chunks=0, pending_pair_chunks=30, auto_adjudicated_chunks=0, needs_adjudication_chunks=0, status=draft_not_final_human_gold
- `experiments/cape_kg_eacl_20260627/01_data/gold_annotation/strong_resegmented_342_max18/adjudication_draft_report.md`: completed_pair_chunks=0, pending_pair_chunks=342, auto_adjudicated_chunks=0, needs_adjudication_chunks=0, status=draft_not_final_human_gold

This package is ready for human labeling, but it is not a substitute for completed gold annotation.

## Human Annotation Progress

- Report: `experiments/cape_kg_eacl_20260627/06_release/annotation_progress_report.md`
- Summary: `experiments/cape_kg_eacl_20260627/06_release/annotation_progress_summary.json`
- Full worklist CSV: `experiments/cape_kg_eacl_20260627/05_review/human_gold_annotation_priority_queue.csv`
- Next 100 worklist CSV: `experiments/cape_kg_eacl_20260627/05_review/human_gold_next_100_worklist.csv`
- Batch assignment report: `experiments/cape_kg_eacl_20260627/06_release/annotation_batch_assignment_report.md`
- Batch assignments: batches=5, assigned_chunks=100, candidate_edges=1371, status=assignment_batches_ready_pending_human_annotation
- Gate status: pending_human_adjudication
- full_120 progress: A_done=0, B_done=0, paired_done=0, adjudicated=0, active_review_chunks=91, high_impact_chunks=64

This is a workflow tracker for human annotation, not a substitute for completed gold labels.

## Annotation QC

- Report: `experiments/cape_kg_eacl_20260627/06_release/annotation_qc_report.md`
- Summary: `experiments/cape_kg_eacl_20260627/06_release/annotation_qc_summary.json`
- Issue CSV: `experiments/cape_kg_eacl_20260627/05_review/annotation_qc_issues.csv`
- Gate worklist: `experiments/cape_kg_eacl_20260627/05_review/annotation_completion_gate_worklist.csv`
- Overall QC status: pending_human_annotation
- Full_120 minimum gate: pending_human_annotation
- Errors: 0; warnings: 0
  - pilot_30: paired=0, ready_for_adjudication=0, adjudicated=0, gold_items=0
  - full_120: paired=0, ready_for_adjudication=0, adjudicated=0, gold_items=0

The QC report checks workflow/import safety; it does not convert pending rows into claimable gold labels.

## Human Gate Action Plan

- Report: `experiments/cape_kg_eacl_20260627/06_release/human_gate_action_plan.md`
- JSON: `experiments/cape_kg_eacl_20260627/06_release/human_gate_action_plan.json`
- Required returns CSV: `experiments/cape_kg_eacl_20260627/05_review/human_gate_required_returns.csv`
- Claim status: human_gate_action_plan_ready_pending_returns
- Return preflight status: pending_human_returns
- Annotation reviewed files present: 0/10
- Required return file entries: 14

This is the single operational checklist for resolving the remaining human-gold, IAA, and expert-review gates.

## Claim Gate and Paper Tables

- Claim gate report: `experiments/cape_kg_eacl_20260627/06_release/claim_gate_report.md`
- Claim gate status: FAIL
- Required failures: 4
- Optional failures: 2
- Warnings: 0
- Claim gate JSON: `experiments/cape_kg_eacl_20260627/06_release/claim_gate_report.json`
- Paper tables Markdown: `experiments/cape_kg_eacl_20260627/06_release/paper_tables.md`
- Paper tables LaTeX: `experiments/cape_kg_eacl_20260627/06_release/paper_tables.tex`
- EACL plan compliance matrix: `experiments/cape_kg_eacl_20260627/06_release/eacl_plan_compliance_matrix.md`
- EACL plan compliance JSON: `experiments/cape_kg_eacl_20260627/06_release/eacl_plan_compliance_matrix.json`
- Claim-safe paper draft: `experiments/cape_kg_eacl_20260627/07_reports/eacl_paper_draft.md`
- Paper draft status: `experiments/cape_kg_eacl_20260627/06_release/eacl_paper_draft_status.json`

The claim gate is expected to fail until human adjudication and IAA are complete.

## Release Bundles

- Bundle manifest: `experiments/cape_kg_eacl_20260627/06_release/release_bundle_manifest.json`
- Bundle checksums: `experiments/cape_kg_eacl_20260627/06_release/release_bundle_checksums.sha256`
- Safety report: `experiments/cape_kg_eacl_20260627/06_release/release_bundle_safety_report.md`
- Latest release bundle index: `experiments/cape_kg_eacl_20260627/06_release/latest_release_bundle_index.md`
- Latest release bundle index JSON: `experiments/cape_kg_eacl_20260627/06_release/latest_release_bundle_index.json`
- Current bundle filenames and SHA256 values are intentionally read from the latest release bundle index to avoid stale exact-path claims after refresh.
- Bundle creation does not change the human-gold claim gate status.

## Required Next Step

Human annotation remains the gating step for EACL-ready evidence.
- Recommended human-return apply wrapper: `scripts/run_cape_human_return_apply.sh`
- Run it with `APPLY_IMPORTS=0` for dry-run validation and `APPLY_IMPORTS=1` only after reviewed return files are present.
- The wrapper validates returned files before refreshing IAA, adjudication drafts, evaluation, audit, tables, reports, and release bundles.
- Low-level post-annotation refresh script: `scripts/run_cape_post_annotation_refresh.sh`
- Use this directly only for debugging; the wrapper is the safer operational entry point.
