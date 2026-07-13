# CAPE-KG Claim Gate Report

Generated: 2026-06-29T18:55:32.465632+00:00

Overall status: **FAIL**

This gate is conservative. Silver/proxy diagnostics and actual LLM runs are not treated as final paper evidence unless they are scored against adjudicated human gold labels.

| gate | status | requirement | evidence |
|---|---|---|---|
| data.eval_chunks | PASS | Evaluation subset has at least 100 chunks | 120 chunks in experiments/cape_kg_eacl_20260627/01_data/evaluation_chunks.jsonl |
| gold.completed_chunks | FAIL | Adjudicated human-gold chunks >= 100 | 0 completed chunks, validation_errors=0, file=experiments/cape_kg_eacl_20260627/04_evaluation/human_gold_validation_summary.json |
| gold.item_count | FAIL | Human-gold node/edge/evidence items >= 500 | 0 items, validation_errors=0, file=experiments/cape_kg_eacl_20260627/04_evaluation/human_gold_validation_summary.json |
| gold.iaa | FAIL | Two-annotator agreement computed for >= 100 chunks | max_completed_pair_chunks=0, summaries=2 |
| llm.baselines | PASS | Actual full B0/B1/B2 LLM baseline generations exist | {'B0_plain_llm': 120, 'B1_predicate_constrained': 120, 'B2_current_project': 120} |
| llm.proposed_generation | PASS | Actual full CAPE-KG proposed generation exists | {'P_cape_kg_actual': 120} |
| llm.proposed_human_gold_score | FAIL | CAPE-KG proposed result is scored against adjudicated human gold | human_gold_scored_conditions=[] |
| llm.ablations | PASS | Actual full ablation runs >= 3 | 6 full ablations: ['P_minus_CQ', 'P_minus_Evidence', 'P_minus_Procedural_schema', 'P_minus_Schema_retrieval', 'P_minus_Standard_bridge', 'P_minus_Validator'] |
| llm.revalidated_output_recovery | PASS | Full actual LLM conditions have unrepaired parse/generation error rate <= 5% | all full conditions <= 5% unrepaired after conservative partial-JSON recovery |
| llm.strict_json_rate | PASS | Full actual LLM conditions have strict JSON parse/generation error rate <= 50% | all full conditions <= 50% strict parse/generation errors |
| external.public_subset | PASS | Public benchmark subset model evaluation exists | PAGED items=100, Text2KG items=200, summaries=4 |
| mapping.expert_review | FAIL | NCS/PCF mapping downstream metrics are expert-review claimable | complete_source_groups=0, pending_rows=220, file=experiments/cape_kg_eacl_20260627/04_evaluation/mapping_expert_metrics.json, progress_file=experiments/cape_kg_eacl_20260627/06_release/mapping_review_progress_summary.json, progress_pending_groups=44 |
| crosswalk.expert_review | FAIL | Layer2-bridged NCS-PCF crosswalk metrics are expert-review claimable | completed_rows=0, pending_rows=220, complete_source_groups=0, file=experiments/cape_kg_eacl_20260627/04_evaluation/crosswalk_expert_metrics.json, manifest_file=experiments/cape_kg_eacl_20260627/01_data/crosswalk_review/crosswalk_review_manifest.json, candidate_rows=220 |
| analysis.error_analysis | PASS | Structured error analysis includes claim scope, diagnostics, taxonomy, and human-gold follow-up | {'markdown': {'path': 'experiments/cape_kg_eacl_20260627/07_reports/error_analysis.md', 'exists': True, 'bytes': 12148}, 'json': {'path': 'experiments/cape_kg_eacl_20260627/07_reports/error_analysis.json', 'exists': True, 'bytes': 34951}, 'required_sections': ['## Claim Scope', '## Actual LLM Silver/Proxy Diagnostics', '## Proxy Scaffold Error Summary', '## Error Taxonomy', '## Human-Gold Follow-Up'], 'missing_sections': [], 'taxonomy_family_count': 8, 'ready_for_minimum_accept': True, 'claim_scope': 'silver_proxy_diagnostic_not_human_gold'} |
| release.artifacts | PASS | Schema, prompts, evaluation, error analysis, limitations, and reproducibility artifacts exist | all required release files exist |

## Blocking Items

- gold.completed_chunks: Adjudicated human-gold chunks >= 100 (0 completed chunks, validation_errors=0, file=experiments/cape_kg_eacl_20260627/04_evaluation/human_gold_validation_summary.json)
- gold.item_count: Human-gold node/edge/evidence items >= 500 (0 items, validation_errors=0, file=experiments/cape_kg_eacl_20260627/04_evaluation/human_gold_validation_summary.json)
- gold.iaa: Two-annotator agreement computed for >= 100 chunks (max_completed_pair_chunks=0, summaries=2)
- llm.proposed_human_gold_score: CAPE-KG proposed result is scored against adjudicated human gold (human_gold_scored_conditions=[])

## Warnings

- None
