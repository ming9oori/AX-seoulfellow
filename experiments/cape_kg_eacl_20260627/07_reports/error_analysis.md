# CAPE-KG Error Analysis

Generated: 2026-06-29T18:55:35.933275+00:00
Experiment: `experiments/cape_kg_eacl_20260627`

## Claim Scope

This report is a pre-human error analysis. It uses scaffold metrics, actual LLM silver/proxy diagnostics, strict JSON diagnostics, and workflow status. It is not a final paper performance table because adjudicated human-gold labels, IAA, mapping expert review, and NCS-PCF crosswalk expert review are still pending.

| claim-bearing question | current status | treatment |
|---|---|---|
| Core extraction quality | pending human-gold | Do not claim final F1 yet |
| Evidence exactness | pending human-gold | Use current values as diagnostics only |
| NCS/PCF mapping quality | pending expert review | Do not claim P@K/P@5/MRR yet |
| NCS-PCF crosswalk utility | pending expert review | Do not claim bridge utility or accept-rate yet |
| JSON/output reliability | diagnostic available | Report as engineering limitation and recovery gate |

## Actual LLM Silver/Proxy Diagnostics

| condition | rows | pred edges | pred nodes | edge F1 | predicate F1 | node F1 | evidence F1 | parse/repaired rows | claim status |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| B0_plain_llm | 120 | 0 | 1674 | 0.0000 | 0.0000 | 0.0350 | 0.0239 | 63/63 | silver_proxy_not_human_gold |
| B1_predicate_constrained | 120 | 663 | 0 | 0.0000 | 0.1416 | 0.0000 | 0.0291 | 63/63 | silver_proxy_not_human_gold |
| B5_procedural_prompt | 120 | 119 | 957 | 0.0010 | 0.0096 | 0.0274 | 0.0603 | 96/96 | silver_proxy_not_human_gold |
| B2_current_project | 120 | 82 | 712 | 0.0000 | 0.0068 | 0.0215 | 0.0503 | 97/97 | silver_proxy_not_human_gold |
| B4_taxonomy_rag | 120 | 128 | 674 | 0.0000 | 0.0105 | 0.0300 | 0.0641 | 102/102 | silver_proxy_not_human_gold |
| B3_edc_style | 120 | 53 | 566 | 0.0000 | 0.0119 | 0.0196 | 0.0311 | 99/98 | silver_proxy_not_human_gold |
| P_minus_Schema_retrieval | 120 | 308 | 566 | 0.0009 | 0.0730 | 0.0218 | 0.0598 | 109/109 | silver_proxy_not_human_gold |
| P_cape_kg_actual | 120 | 275 | 549 | 0.0018 | 0.0482 | 0.0326 | 0.0655 | 113/113 | silver_proxy_not_human_gold |
| P_minus_CQ | 120 | 284 | 554 | 0.0000 | 0.0338 | 0.0285 | 0.0682 | 117/117 | silver_proxy_not_human_gold |
| P_minus_Evidence | 120 | 259 | 514 | 0.0009 | 0.0549 | 0.0297 | 0.0666 | 103/103 | silver_proxy_not_human_gold |
| P_minus_Procedural_schema | 120 | 247 | 528 | 0.0036 | 0.0976 | 0.0301 | 0.0687 | 107/107 | silver_proxy_not_human_gold |
| P_minus_Standard_bridge | 120 | 338 | 572 | 0.0009 | 0.0712 | 0.0213 | 0.0590 | 59/59 | silver_proxy_not_human_gold |
| P_minus_Validator | 120 | 271 | 557 | 0.0018 | 0.0456 | 0.0299 | 0.0659 | 110/110 | silver_proxy_not_human_gold |
| B6_sac_kg_verifier_pruner | 120 | 361 | 2281 | 0.0017 | 0.0774 | 0.0564 | 0.1008 | 0/0 | silver_proxy_not_human_gold |

These rows show actual LLM generation coverage and silver-reference behavior. They must be replaced by human-gold scores for final paper claims.

## Proxy Scaffold Error Summary

| condition | TP | FP | FN | precision | recall | F1 | unsupported rate | ontology violations | procedural edges |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| B0_plain_llm_proxy | 135 | 366 | 765 | 0.2695 | 0.1500 | 0.1927 | 0.0000 | 540 | 42 |
| B1_predicate_constrained_proxy | 720 | 0 | 180 | 1.0000 | 0.8000 | 0.8889 | 0.0000 | 720 | 206 |
| B2_current_project_baseline | 900 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0 | 251 |
| B4_taxonomy_rag_proxy | 610 | 0 | 290 | 1.0000 | 0.6778 | 0.8079 | 0.0000 | 0 | 0 |
| B5_procedural_prompt_proxy | 251 | 0 | 649 | 1.0000 | 0.2789 | 0.4361 | 0.0000 | 0 | 251 |
| P_cape_kg_silver | 900 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0 | 251 |
| P_minus_CQ_proxy | 750 | 0 | 150 | 1.0000 | 0.8333 | 0.9091 | 0.0000 | 0 | 209 |
| P_minus_Evidence_proxy | 900 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0 | 251 |
| P_minus_Procedural_schema_proxy | 649 | 0 | 251 | 1.0000 | 0.7211 | 0.8380 | 0.0000 | 0 | 0 |
| P_minus_Validator_proxy | 900 | 26 | 0 | 0.9719 | 1.0000 | 0.9858 | 0.0000 | 45 | 251 |
| P_minus_Standard_bridge_proxy | 900 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0 | 251 |

The proxy scaffold rows are useful for debugging ablation behavior, but they include silver-derived references and synthetic condition transformations.

## Error Taxonomy

| family | observed signal | likely cause | affected conditions | paper treatment | next action |
|---|---|---|---|---|---|
| Missing extraction / coverage loss | High false-negative counts in proxy rows, e.g. B0_plain_llm_proxy, B4_taxonomy_rag_proxy, B5_procedural_prompt_proxy, and P_minus_CQ_proxy. | Prompt-only extraction or removed CQ context misses procedural elements that the silver scaffold contains. | B0_plain_llm_proxy, B4_taxonomy_rag_proxy, B5_procedural_prompt_proxy, P_minus_CQ_proxy | Use as error taxonomy and annotation priority signal only until human-gold confirms recall errors. | During adjudication, check whether omitted edges are true misses or silver-reference overgeneration. |
| Spurious extraction / overgeneration | B0_plain_llm_proxy has large FP count; P_minus_Validator_proxy keeps extra invalid edges. | Unconstrained generation and disabled validation allow unsupported or schema-incompatible edges to remain. | B0_plain_llm_proxy, P_minus_Validator_proxy | Report as validator motivation, not as final precision claim. | Inspect high-priority FP edges against source evidence in human review. |
| Ontology / domain-range violation | Proxy rows show ontology violations for B0/B1 and P_minus_Validator. | Predicate restriction alone does not enforce subject/object type compatibility. | B0_plain_llm_proxy, B1_predicate_constrained_proxy, P_minus_Validator_proxy | Use ontology conformance as a separate structural metric from extraction F1. | Keep domain/range validation in the proposed pipeline and rerun conformance on human-gold predictions. |
| Evidence grounding failure | P_minus_Evidence_proxy has unsupported_edge_rate=1.0 and zero grounding in the scaffold metrics. | Removing evidence constraints preserves graph shape but destroys source-text traceability. | P_minus_Evidence_proxy | Treat as direct support for evidence-grounded evaluation design. | Ask annotators to verify evidence exactness and evidence sufficiency for accepted edges. |
| Procedural schema loss | P_minus_Procedural_schema_proxy drops procedural edge count in the scaffold metrics. | Generic relation extraction does not preserve task-step-order and artifact-flow structure. | P_minus_Procedural_schema_proxy | Use as procedural KG motivation, not as final ablation conclusion until human-gold scoring. | Check PRECEDES, HAS_STEP, PRODUCES, USES_INPUT, and PERFORMED_BY during adjudication. |
| Strict JSON / parser recovery instability | Strict JSON warning threshold currently passes: all full conditions <= 50% strict parse/generation errors. | Long prompts and model reasoning text cause non-clean JSON outputs that require conservative partial-JSON recovery. | none_over_threshold | Report as engineering reliability limitation and keep unrepaired-rate gate separate from quality metrics. | Prefer strict contract plus no-think decoding for final reruns if time permits. |
| Standard taxonomy bridge uncertainty | Mapping expert review has complete_groups=0, pending_rows=220. | Automatic top-k mapping candidates are not equivalent to expert-confirmed standard alignment. | NCS mapping, PCF mapping | Do not claim NCS/PCF P@K, P@5, or MRR until expert review is complete. | Complete top-5 review for priority source-task groups and recompute mapping metrics. |
| Silver/proxy reference mismatch | Actual LLM silver edge-exact F1 values are low and should not be interpreted as final paper performance. | Silver labels were derived from the current KG and may not match human judgments or surface forms. | B0_plain_llm, B1_predicate_constrained, B2_current_project, B3_edc_style, B4_taxonomy_rag, B5_procedural_prompt, B6_sac_kg_verifier_pruner, P_cape_kg_actual, P_minus_CQ, P_minus_Evidence, P_minus_Procedural_schema, P_minus_Schema_retrieval, P_minus_Standard_bridge, P_minus_Validator | Use silver/proxy results for debugging, prompt comparison, and claim gating only. | Replace claim-bearing scores with adjudicated human-gold metrics. |

## Diagnostic Observations

- B0_plain_llm_proxy is a broad recall/precision stress case: FP=366, FN=765, ontology_violations=540.
- P_minus_Evidence_proxy isolates evidence grounding: unsupported_edge_rate=1.0, evidence_exact_match=0.0.
- P_minus_Validator_proxy shows the value of validation: FP=26 and ontology_violations=45 remain when pruning is removed.
- P_minus_Procedural_schema_proxy has procedural_edge_count=0, highlighting procedural schema dependence.
- P_cape_kg_actual actual LLM run is complete for 120 rows, but current scores remain silver/proxy: edge_F1=0.0018, predicate_F1=0.0482, evidence_F1=0.0655.
- Strict JSON diagnostics now pass the configured warning gate: all full conditions <= 50% strict parse/generation errors.
- Active-review diagnostics are high-risk by design and silver/proxy only; current candidate error_rate=0.9927.
- Paired bootstrap and McNemar diagnostics exist, but all current significance statements are silver/proxy and must be rerun on human-gold labels.

## Model-Scaling Diagnostic Slice

| model | condition | rows | edge F1 | predicate F1 | node F1 | evidence F1 | parse/repaired rows |
|---|---|---:|---:|---:|---:|---:|---:|
| Qwen3-8B | B0_plain_llm | 120 | 0.0000 | 0.0000 | 0.0350 | 0.0239 | 63/63 |
| Qwen3-8B | B1_predicate_constrained | 120 | 0.0000 | 0.1416 | 0.0000 | 0.0291 | 63/63 |
| Qwen3-8B | B2_current_project | 120 | 0.0000 | 0.0068 | 0.0215 | 0.0503 | 97/97 |
| Qwen3-8B | P_cape_kg_actual | 120 | 0.0018 | 0.0482 | 0.0326 | 0.0655 | 113/113 |
| Qwen3-14B | B0_plain_llm | 120 | 0.0000 | 0.0000 | 0.0329 | 0.0259 | 68/68 |
| Qwen3-14B | B1_predicate_constrained | 120 | 0.0008 | 0.1105 | 0.0000 | 0.0246 | 75/75 |
| Qwen3-14B | B2_current_project | 120 | 0.0000 | 0.0079 | 0.0198 | 0.0394 | 102/102 |
| Qwen3-14B | P_cape_kg_actual | 120 | 0.0017 | 0.0601 | 0.0298 | 0.0610 | 113/113 |
| Qwen3-32B-AWQ | B0_plain_llm | 120 | 0.0000 | 0.0000 | 0.0377 | 0.0273 | 59/59 |
| Qwen3-32B-AWQ | B1_predicate_constrained | 120 | 0.0016 | 0.1161 | 0.0000 | 0.0224 | 63/63 |
| Qwen3-32B-AWQ | B2_current_project | 120 | 0.0000 | 0.0099 | 0.0194 | 0.0387 | 100/100 |
| Qwen3-32B-AWQ | P_cape_kg_actual | 120 | 0.0034 | 0.0662 | 0.0284 | 0.0542 | 113/113 |

## Strict JSON and Recovery Notes

- Strict JSON gate status: `PASS`
- Revalidated output recovery status: `PASS`
- Top strict-error conditions: none

## Human-Gold Follow-Up

- Adjudicate at least 100 chunks and at least 500 node/edge/evidence items.
- Compute IAA on paired A/B annotations before adjudication-derived claims.
- Recompute node, edge, predicate, evidence, ontology, procedural, and CQ metrics against adjudicated human gold.
- Manually categorize false positives and false negatives into the taxonomy families above.
- Complete NCS/PCF expert mapping review before reporting Hit@K, P@5, or MRR.
- Keep silver/proxy diagnostic tables out of the final claim-bearing main table.

## Source Files

- proxy_main_results: `experiments/cape_kg_eacl_20260627/04_evaluation/main_results.csv`
- actual_llm_silver_metrics: `experiments/cape_kg_eacl_20260627/04_evaluation/actual_llm_silver_metrics.json`
- model_scaling_source_files: `experiments/cape_kg_eacl_20260627/04_evaluation/actual_llm_silver_metrics.json`, `experiments/cape_kg_eacl_20260627/04_evaluation/qwen3_14b_core_silver_metrics.json`, `experiments/cape_kg_eacl_20260627/04_evaluation/qwen3_32b_awq_core_silver_metrics.json`
- strict_json_diagnostics: `experiments/cape_kg_eacl_20260627/06_release/strict_json_diagnostics.json`
- active_review_efficiency: `experiments/cape_kg_eacl_20260627/04_evaluation/active_review_efficiency_metrics.json`
- statistical_analysis: `experiments/cape_kg_eacl_20260627/04_evaluation/statistical_analysis_metrics.json`
- mapping_expert_metrics: `experiments/cape_kg_eacl_20260627/04_evaluation/mapping_expert_metrics.json`
