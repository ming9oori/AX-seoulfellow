# CAPE-KG: Competency-Question Anchored Procedural Evidence Grounding for Domain Knowledge Graph Construction

Generated: 2026-06-29T18:56:33.576320+00:00

**Status:** internal claim-safe draft, not a submission-ready manuscript.

This draft intentionally separates completed engineering/evaluation artifacts from final paper claims. The current package is not EACL-ready because adjudicated human-gold labels, IAA, human-gold scoring, mapping expert review, NCS-PCF crosswalk expert review, and active-review effort evidence are still pending.

## Claim Safety Summary

- Current claim status: `pending_human_gold_iaa_and_human_gold_scoring`
- Required claim-gate failures: `4`
- Submission audit status counts: `{'pending_human': 5, 'pass': 11, 'partial': 4}`
- Evaluation chunks: `120`
- Silver reference edges: `900`
- Human return preflight: `pending_human_returns`
- Pre-human handoff validation: `PASS`
- Provenance manifest: `provenance_manifest_ready_not_human_gold_evidence`
- Minimum paper-gate human-return files: `0/11`
- Optional/strong claim human-return files: `0/3`
- Required claim/human-return files: `0/14`
- Optional structural review files: `0/2`
- All master return files: `0/16`

### Blocking Items

| ID | Requirement | Next step |
| --- | --- | --- |
| min.gold_chunks | 100+ adjudicated gold chunks | Complete two-annotator labeling and adjudication for at least 100 chunks. |
| min.gold_items | 500+ adjudicated gold node/edge/evidence items | Adjudicate enough nodes, edges, and evidence anchors to reach 500 gold items. |
| min.iaa | 2+ annotators and agreement for 100+ chunks | Import completed annotator A/B files and recompute IAA. |
| min.proposed | CAPE-KG proposed result completed and scored | Score P_cape_kg_actual against adjudicated human gold after gold completion. |

## Abstract Draft

We study evidence-grounded procedural knowledge graph construction for long, noisy Korean bid and proposal documents. The proposed CAPE-KG framework anchors extraction to competency questions, retrieves task-specific schema context, constrains generated nodes and edges to evidence spans, and routes uncertain outputs into active human review. The current experiment package implements the task definition, schema, prompts, actual LLM baselines, ablations, public benchmark adapters, provenance manifests, reviewer workbenches, adjudication handoff, mapping expert review handoff, and active-review effort collection. The package also includes a separate NCS-PCF crosswalk expert-review handoff for Layer2 bridge utility. Preliminary silver-reference diagnostics suggest that schema, evidence, and validator components materially change extraction behavior, but final effectiveness claims are deferred until adjudicated human-gold labels and inter-annotator agreement are complete.

## Introduction

Domain knowledge graph construction from enterprise procedure documents requires more than extracting generic triples. A useful graph must preserve procedural order, decision conditions, artifacts, responsible roles, evidence provenance, and downstream links to standard taxonomies. CAPE-KG frames this as an information extraction and resource/evaluation problem.

Current claimable contributions:

- A competency-question anchored task definition for evidence-grounded procedural KG construction.
- A CAPE schema covering tasks, procedure steps, gateways, guard conditions, artifacts, roles, principles, risks, and evidence anchors.
- Executable actual LLM baselines and ablations over 120 evaluation chunks.
- Layer 2 KG RDF/Turtle export and SHACL-style validation artifacts for ontology, predicate, domain/range, dangling-edge, and evidence-anchor checks.
- File-level provenance manifest and PROV-O Turtle export covering source files, prompts, schemas, LLM raw/valid outputs, evaluation artifacts, handoff files, and release artifacts.
- Public benchmark adapters and model diagnostics for PAGED and Text2KGBench subsets.
- Structured pre-human error analysis with claim scope, taxonomy, actual LLM diagnostics, and human-gold follow-up.
- Human annotation, adjudication, IAA, mapping review, crosswalk review, active-review, and optional structural-review workbenches with an 11-file minimum paper gate, 3 optional/strong claim returns, and 2 optional structural returns in the 16-file master manifest.

Claims that must remain pending:

- Superiority over baselines on human-gold edge, node, evidence, ontology, procedural, or CQ metrics.
- Expert-confirmed NCS/PCF mapping P@K, MRR, nDCG@10, accept-rate, and explanation-quality claims.
- Expert-confirmed NCS-PCF crosswalk accept-rate and utility claims.
- Human review efficiency claims based on adjudicated outcomes.

## Related Work

- LLM-based KG construction: EDC and SAC-KG motivate structured extraction, canonicalization, verifier, and pruner components.
- Ontology-guided information extraction: Text2KGBench provides ontology-conformance and hallucination-oriented evaluation context.
- Procedural graph extraction: PAGED motivates process element and flow extraction for procedural text.
- Evidence grounding: CAPE-KG treats source evidence anchors as first-class evaluation objects.

## Task Definition

Input: a document chunk with sentence/evidence IDs and optional schema/taxonomy context.

Output:

- nodes with type, label, confidence, and evidence anchors;
- edges with subject/object labels, predicate, type hints, confidence, and evidence anchors;
- optional NCS/PCF mapping candidates;
- optional Layer2-bridged NCS-PCF crosswalk candidates;
- validation metadata for ontology, procedural, and evidence constraints.

Core metrics planned for the final paper are edge exact F1, predicate F1, node label F1, evidence F1 or exact match, ontology conformance, procedural consistency, CQ answerability, and mapping P@K/MRR/nDCG@10 plus explanation quality after expert review.

## Dataset and Annotation

| Item | Current value | Status |
| --- | --- | --- |
| Evaluation chunks | 120 | available |
| Silver reference nodes | 208 | diagnostic only |
| Silver reference edges | 900 | diagnostic only |
| Adjudicated human-gold chunks | 0 | pending |
| Human-gold items | 0 | pending |
| Annotation reviewed files | 0/10 | pending return |
| Adjudication reviewed file | missing | pending return |
| Mapping review rows | 220 | pending expert review |
| Active-review effort rows | 204 | pending reviewer timing |
| Optional all-available annotation chunks | 214 | optional_expansion_ready_pending_human_review |
| Optional remaining annotation chunks | 94 | optional expansion, not current gate |
| Optional strong resegmented review units | 342 | max 18 source sentences/unit; ready_pending_human_review |

The annotation package and workbench are ready, but the paper must not claim human-gold results until two annotators and adjudication are complete.

### Human Review Return Manifest

| Return type | Required files | Present files | Purpose |
| --- | --- | --- | --- |
| Human-gold annotation | 10 | 0 | two-annotator labels for priority chunks |
| Human-gold adjudication | 1 | 0 | final adjudicated gold labels |
| Mapping expert review | 1 | 0 | expert-confirmed NCS/PCF mapping labels |
| NCS-PCF crosswalk expert review | 1 | 0 | expert-confirmed NCS-PCF crosswalk utility labels |
| Active-review human effort | 1 | 0 | review timing and correction-effort evidence |
| Total | 14 | 0 | all human-return files required before final claims |

The return preflight currently has no validation errors, but all paper-claimable human evidence remains pending until the 11 minimum files and 3 optional/strong claim files are returned and imported. The 2 optional structural-review files are tracked in the master manifest as procedural-structure follow-up and do not change the minimum paper gate.

### Handoff Bundles

| Bundle | File | Files inside | SHA256 |
| --- | --- | --- | --- |
| Annotator A | cape_human_gold_annotator_A_priority100.tar.gz | 88 | 61e9abb7f49ff145abd80eb66683753726c5e8f3a6af766d9dba3ec6282039e7 |
| Annotator B | cape_human_gold_annotator_B_priority100.tar.gz | 88 | f40bd182d67abda973d42b525d924101d12970b3054dfe1bcda2fabbb2c018a0 |
| Coordinator | cape_human_gold_coordinator_priority100.tar.gz | 96 | 7f72d5bae1d81c977d5c7f7d5ae981e2b722bc13723d8d29d5766a73bc32832d |
| Adjudicator | cape_human_gold_adjudicator_full120.tar.gz | 42 | 8753ea3ca38a1a156ff2ffbef25615976a517ca15a4d409420b8447fefaf2b22 |
| Mapping expert | cape_mapping_expert_review_top20_groups.tar.gz | 39 | 55084936ce2bba09fe2e6c005f3b47cfd844863114341f2b1e6e17a69ea3889c |
| NCS-PCF crosswalk expert | cape_crosswalk_expert_review_ncs_pcf.tar.gz | 37 | c9f0e233a048cbe74999d154c177e49e0f1ce4e5e40be7550f8dc31b821dd958 |
| Active-review effort | cape_active_review_human_effort.tar.gz | 40 | f49b428bf5dc6fb5ca52b43bf1d47a1999d7b126eb9e863f2ba3d0006345f5d3 |
| Structural reviewer | cape_structural_review_optional.tar.gz | 41 | 9d9ed2ecc451ac374c7be1d43e69b4012bd2ca8a9f46b6ad814fc80f50f17471 |
| Optional strong 300+ review | cape_human_gold_strong_resegmented_342.tar.gz | 57 | 406857a2485b819e1ad89f8fe2550a7838e0c76e3a73e8fb704d770158fd3719 |

## Method: CAPE-KG

CAPE-KG consists of the following modules:

1. CQ-linked schema retrieval.
2. Procedural frame extraction.
3. Evidence-span constrained generation.
4. Ontology and procedural validation.
5. NCS/PCF mapping candidate generation.
6. Layer2-bridged NCS-PCF crosswalk candidate generation.
7. Active review prioritization.

The current experiment also includes B6, a deterministic SAC-KG-style verifier/pruner approximation. It uses existing generator candidates and applies schema/evidence/domain-range checks. This should be described as an approximation, not a full SAC-KG reproduction.

## Experiments

### Baselines and Ablations

| Condition | Rows | Edge F1 | Predicate F1 | Node F1 | Evidence F1 | Parse/error rows |
| --- | --- | --- | --- | --- | --- | --- |
| B0_plain_llm | 120 | 0.0000 | 0.0000 | 0.0350 | 0.0239 | 63 |
| B1_predicate_constrained | 120 | 0.0000 | 0.1416 | 0.0000 | 0.0291 | 63 |
| B2_current_project | 120 | 0.0000 | 0.0068 | 0.0215 | 0.0503 | 97 |
| B3_edc_style | 120 | 0.0000 | 0.0119 | 0.0196 | 0.0311 | 99 |
| B4_taxonomy_rag | 120 | 0.0000 | 0.0105 | 0.0300 | 0.0641 | 102 |
| B5_procedural_prompt | 120 | 0.0010 | 0.0096 | 0.0274 | 0.0603 | 96 |
| B6_sac_kg_verifier_pruner | 120 | 0.0017 | 0.0774 | 0.0564 | 0.1008 | 0 |
| P_cape_kg_actual | 120 | 0.0018 | 0.0482 | 0.0326 | 0.0655 | 113 |

These are silver-reference diagnostics only. Final tables must be regenerated after human-gold annotation and scoring.

### Evidence Span Granularity

| Triples | Components | Subject exact | Object exact | Predicate proxy | Status |
| --- | --- | --- | --- | --- | --- |
| 947 | 2841 | 0.2323 | 0.5512 | 1.0000 | automatic_component_span_diagnostic_not_human_gold |

This diagnostic separates sentence-level evidence support from component-level lexical spans. Predicate evidence remains a sentence-level proxy until human-gold span annotation is available.

### KG Structural Diagnostics

| Status | Ontology | Domain/range errors | Evidence missing | Procedural | Cycles | CQ answerability |
| --- | --- | --- | --- | --- | --- | --- |
| kg_structural_diagnostic_not_human_gold | 1.0000 | 0 | 0 | 0.9953 | 0 | 1.0000 |

This diagnostic checks ontology/domain-range conformance, procedural constraints, and structural CQ answerability on the built KG. It is not a human-gold performance result.

### Structural Gap Worklist

| Status | Review checkpoint candidates | Gateway branch gaps | Structural CQ | Human gate effect |
| --- | --- | --- | --- | --- |
| structural_gap_worklist_pending_human_review | 45 | 4 | 1.0000 | does_not_change_minimum_11_file_paper_gate |

This worklist turns structural diagnostics into reviewable follow-up items. It does not automatically modify the KG and does not change the 11-file minimum paper gate.

### Public Benchmark Adapters

| Run | PAGED n | PAGED node F1 | PAGED edge F1 | Text2KG n | Relation F1 | Triple F1 |
| --- | --- | --- | --- | --- | --- | --- |
| public_qwen3_14b_subset_eval_summary.json | 10 | 0.1733 | 0.1446 | 20 | 0.2817 | 0.0200 |
| public_qwen3_8b_full_adapter_eval_summary.json | 100 | 0.2472 | 0.4233 | 200 | 0.6015 | 0.1736 |
| public_qwen3_8b_subset_eval_summary.json | 10 | 0.1608 | 0.1794 | 20 | 0.4500 | 0.0500 |
| public_qwen3_8b_subset_smoke_summary.json | 3 | 0.0000 | 0.1333 | 5 | 0.4000 | 0.0000 |

The public benchmark adapter results are useful external diagnostics, not official leaderboard claims.

### Layer2-Bridged NCS-PCF Crosswalk Candidates

| Shared Layer2 tasks | All pairs | Candidate rows | Top-K per standard | Status |
| --- | --- | --- | --- | --- |
| 22 | 550 | 220 | 5 | candidate_only_pending_expert_review |

These are bridge-supported candidate pairs only. Expert review is required before reporting crosswalk precision, accept-rate, or downstream utility.

### NCS-PCF Crosswalk Expert Review Status

| Candidates | Source tasks | Completed | Pending | Hit@5 | Utility | Status |
| --- | --- | --- | --- | --- | --- | --- |
| 220 | 22 | 0 | 220 | pending_crosswalk_expert_review | pending_crosswalk_expert_review | pending_crosswalk_expert_review |

This status table separates candidate generation from expert-confirmed crosswalk utility claims.

### P minus Active Review Ablation

| Condition | Strategy | Budget | Errors | Precision@k | Lift | Status |
| --- | --- | --- | --- | --- | --- | --- |
| P_cape_kg_actual_with_active_review | active_priority | 25 | 16 | 0.6400 | 1.0173 | silver_proxy_ablation_not_human_efficiency |
| P_minus_Active_review_random_expected | random_expected | 25 | 15.7273 | 0.6291 | 1.0000 | silver_proxy_ablation_not_human_efficiency |
| P_minus_Active_review_uncertainty_only | uncertainty_only | 25 | 15 | 0.6000 | 0.9538 | silver_proxy_ablation_not_human_efficiency |
| P_cape_kg_actual_with_active_review | active_priority | 55 | 36 | 0.6545 | 1.0405 | silver_proxy_ablation_not_human_efficiency |
| P_minus_Active_review_random_expected | random_expected | 55 | 34.6000 | 0.6291 | 1.0000 | silver_proxy_ablation_not_human_efficiency |
| P_minus_Active_review_uncertainty_only | uncertainty_only | 55 | 38 | 0.6909 | 1.0983 | silver_proxy_ablation_not_human_efficiency |
| P_cape_kg_actual_with_active_review | active_priority | 100 | 56 | 0.5600 | 0.8902 | silver_proxy_ablation_not_human_efficiency |
| P_minus_Active_review_random_expected | random_expected | 100 | 62.9091 | 0.6291 | 1.0000 | silver_proxy_ablation_not_human_efficiency |
| P_minus_Active_review_uncertainty_only | uncertainty_only | 100 | 72 | 0.7200 | 1.1445 | silver_proxy_ablation_not_human_efficiency |

This is a silver/proxy scaffold for the active-review ablation in the revised plan. It must be rerun against adjudicated human labels and reviewer effort files before any efficiency claim.

## Analysis

- Structured error analysis artifact: `07_reports/error_analysis.md` and `07_reports/error_analysis.json`.
- Error types: unsupported edges, invalid evidence, ontology violations, procedural flow errors, mapping misses, strict JSON recovery issues, and silver/reference mismatch.
- Evidence failure cases: missing anchors, overly broad anchors, and hallucinated support.
- Procedural consistency cases: missing gateways, invalid guard conditions, and artifact-flow direction errors.
- Active review: compare active priority, uncertainty-only, and random review after adjudicated outcomes exist.

## Required Work Before Submission

| ID | Category | Status | Claimable | Requirement |
| --- | --- | --- | --- | --- |
| min.gold_chunks | minimum_accept | pending_human | no | 100+ adjudicated gold chunks |
| min.gold_items | minimum_accept | pending_human | no | 500+ adjudicated gold node/edge/evidence items |
| min.iaa | minimum_accept | pending_human | no | 2+ annotators and agreement for 100+ chunks |
| min.gold_sampling_ready | minimum_accept | pass | yes | Priority-100 gold subset sampling ready |
| min.baselines | minimum_accept | pass | yes | B0/B1/B2 actual LLM baselines completed |
| min.proposed | minimum_accept | partial | no | CAPE-KG proposed result completed and scored |
| min.ablations | minimum_accept | pass | yes | 3+ actual ablations completed |
| min.error_analysis | minimum_accept | pass | yes | Structured error analysis table and taxonomy |
| min.public_subset | minimum_accept | pass | yes | Public benchmark or public subset experiment |
| min.release_plan | minimum_accept | pass | yes | Code, prompt, schema, and reproducibility release package |
| min.limitations | minimum_accept | pass | yes | Limitations section |
| min.public_synthetic_examples | minimum_accept | pass | yes | Public-safe synthetic examples for reproducibility mitigation |
| strong.gold_chunks | strong_accept | pending_human | no | 300-500 adjudicated gold chunks |
| strong.gold_items | strong_accept | pending_human | no | 1,500+ adjudicated gold edge/evidence items |
| strong.public_cross | strong_accept | pass | yes | PAGED/Text2KGBench cross experiment |
| strong.edc_taxonomy_baselines | strong_accept | pass | yes | EDC/SAC-KG/Taxonomy-RAG family baselines or reproductions |
| strong.mapping_downstream | strong_accept | partial | no | NCS/PCF mapping downstream evaluation |
| strong.active_review | strong_accept | partial | no | Active review efficiency evaluation |
| strong.visualization | strong_accept | pass | yes | Visualization/demo provided |
| method.m1_m11 | method_modules | partial | yes | CAPE-KG M1-M11 modules represented by executable artifacts |

## Source Artifacts

- `06_release/submission_readiness_audit.md`
- `06_release/claim_gate_report.md`
- `06_release/paper_tables.md` and `paper_tables.tex`
- `04_evaluation/actual_llm_silver_evaluation_report.md`
- `06_release/provenance_manifest.md`, `06_release/provenance_prov_o.ttl`, and `04_evaluation/provenance_llm_run_index.csv`
- `04_evaluation/structural_evaluation_report.md`
- `outputs/12_rdf/cape_kg_layer2.ttl` and `outputs/12_rdf/cape_kg_shacl_validation_report.md`
- `04_evaluation/structural_gap_worklist_report.md`
- `06_release/human_gate_action_plan.md` and `05_review/human_gate_required_returns.csv`
- `06_release/human_review_return_preflight.md`
- `06_release/human_review_handoff/human_review_handoff_report.md`
- `07_reports/error_analysis.md` and `07_reports/error_analysis.json`
- `07_reports/final_eacl_experiment_report.md`

## Conclusion

The current CAPE-KG package is ready for pre-human handoff and internal paper drafting: the schema, prompts, actual LLM runs, ablations, structural diagnostics, public benchmark adapters, provenance records, reviewer workbenches, and release manifests are available. The final paper conclusion must be rewritten after adjudicated human-gold labels, IAA, expert mapping review, crosswalk review, and active-review effort evidence are returned.

## Limitations

- Human-gold annotation, adjudication, and IAA are not complete.
- Silver diagnostics are useful for debugging but cannot support final paper claims.
- Mapping downstream metrics require expert-reviewed NCS/PCF candidate groups.
- Active-review efficiency requires returned reviewer timing/correction files and adjudicated outcomes.
- Raw copyrighted text may not be releasable; release must emphasize schema, prompts, code, derived annotations, and public adapters.
- The SAC-KG-style B6 baseline is an approximation, not a faithful full reproduction.
- Qwen3-32B-AWQ core B0/B1/B2/P diagnostic runs are complete, but all model-scaling scores remain silver/proxy until human-gold scoring.
- Standard Qwen3-32B weights are not currently cached; the current disk state is not suitable for a standard-weight 32B run without freeing additional space.

## Ethical Considerations

The release package should avoid exposing copyrighted or sensitive raw source text unless rights are cleared. The reproducibility path should prioritize schema, prompts, evaluation code, public benchmark adapters, derived annotations, and visualization artifacts.

## References

1. EACL 2027 Call for Papers. https://2027.eacl.org/calls/papers/
2. ACL Rolling Review CFP. https://aclrollingreview.org/cfp
3. Chen et al. 2024. SAC-KG: Exploiting Large Language Models as Skilled Automatic Constructors for Domain Knowledge Graph. https://aclanthology.org/2024.acl-long.238/
4. Zhang and Soh. 2024. Extract, Define, Canonicalize: An LLM-based Framework for Knowledge Graph Construction. https://aclanthology.org/2024.emnlp-main.548/
5. Pan et al. 2025. Taxonomy-Driven Knowledge Graph Construction for Domain-Specific Scientific Applications. https://aclanthology.org/2025.findings-acl.223/
6. Mihindukulasooriya et al. 2023. Text2KGBench: A Benchmark for Ontology-Driven Knowledge Graph Generation from Text. https://ar5iv.labs.arxiv.org/html/2308.02357
7. Zhou et al. 2026. TextMineX: Data, Evaluation Framework and Ontology-guided LLM Pipeline for Humanitarian Mine Action. https://aclanthology.org/2026.findings-eacl.130.pdf
8. Du et al. 2024. PAGED: A Benchmark for Procedural Graphs Extraction from Documents. https://aclanthology.org/2024.acl-long.583/
9. Ying et al. 2026. Multi-Agent Procedural Graph Extraction with Structural Feedback. https://aclanthology.org/2026.findings-eacl.158.pdf
10. W3C SHACL. https://www.w3.org/TR/shacl/
11. W3C PROV-O. https://www.w3.org/TR/prov-o/
