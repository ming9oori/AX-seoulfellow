# CAPE-KG Reviewer Response Prep

Generated: 2026-06-29T18:56:33.737369+00:00
Plan: `AX_EACL_submission_review_revised_plan.md`
Experiment: `experiments/cape_kg_eacl_20260627`

이 문서는 revised EACL plan 12장의 예상 reviewer 질문을 현재 evidence, 안전한 답변 문구, 금지 claim, 남은 gate로 연결한 준비 문서입니다.
최종 rebuttal 문서가 아니라 pre-human 상태에서 논문 초안과 발표 문구가 reviewer 우려에 어떻게 대응해야 하는지 고정하는 guardrail입니다.

## Summary

| Item | Value |
| --- | --- |
| Overall status | PASS |
| Claim status | reviewer_response_prep_ready_not_submission_complete |
| Safe to use as submission | False |
| Submission ready | False |
| Reviewer questions | 7 |
| Missing evidence files | 0 |
| Claim gate | FAIL |
| Pre-human validation | PASS |
| Pre-human checks | 92 |

## Response Table

| id | reviewer_question | status | safe_claim_boundary | remaining_gate |
| --- | --- | --- | --- | --- |
| Q01_domain_application | 단순 domain application 아닌가? | mitigated_setup_final_performance_pending | Task definition, method modules, and structural diagnostics are safe to discuss now. | human-gold annotation, IAA, adjudication, and proposed-method scoring |
| Q02_reproducibility_private_data | 데이터가 공개되지 않으면 재현성이 낮지 않은가? | mitigated_public_safe_release_rights_review_required | Public-safe reproducibility scaffolding is claimable as setup evidence. | external rights review before public source-text release |
| Q03_existing_ontology_guided_extraction | ontology-guided extraction은 이미 많지 않은가? | partially_mitigated_final_gain_pending | Method composition and artifact coverage are safe to claim. | human-gold ablation scoring |
| Q04_why_korean_enterprise_documents | 왜 Korean enterprise document인가? | claimable_setup_human_quality_pending | Dataset challenge and sampling setup are safe to describe. | two-annotator labels, adjudication, and IAA |
| Q05_prompt_engineering | LLM prompt engineering 아닌가? | mitigated_with_constraints_and_diagnostics | Engineering controls, validators, and provenance are safe setup claims. | human-gold semantic correctness evaluation |
| Q06_subjective_evaluation | 평가가 subjective하지 않은가? | scaffold_ready_human_metrics_pending | Metric definitions and scorer readiness are safe to describe. | completed human-gold labels and scorer refresh |
| Q07_ncs_pcf_nlp_contribution | NCS/PCF mapping이 NLP contribution인가? | candidate_pipeline_ready_expert_review_pending | Candidate generation and downstream task framing are safe to discuss. | mapping and crosswalk expert review |

## Detailed Responses

### Q01_domain_application. 단순 domain application 아닌가?

- Concern class: `task_framing`
- Status: `mitigated_setup_final_performance_pending`
- Paper sections: Introduction, Task Definition, Method
- Remaining gate: human-gold annotation, IAA, adjudication, and proposed-method scoring

**Short answer, Korean**

논문은 수주·제안 KG 구축 사례가 아니라, 장문 한국어 업무 문서에서 evidence-grounded procedural KG를 추출하는 constrained IE task로 정의한다. 현재 RQ1-RQ4, M1-M11, CQ/query pack, paper section source map이 이 framing을 뒷받침한다.

**Short answer, English**

The paper should be framed as constrained evidence-grounded procedural KG extraction from long Korean enterprise documents, not as a one-off bid/proposal KG case. RQ1-RQ4, M1-M11, the CQ/query pack, and the section source map currently support that framing.

**Safe claim boundary**

Task definition, method modules, and structural diagnostics are safe to discuss now.

**Must not claim yet**

Do not claim final target-corpus superiority until human-gold scoring is complete.

**Evidence files**

| path | exists | bytes |
| --- | --- | --- |
| AX_EACL_submission_review_revised_plan.md | True | 29461 |
| experiments/cape_kg_eacl_20260627/06_release/rq_evidence_matrix.md | True | 14252 |
| experiments/cape_kg_eacl_20260627/06_release/method_module_coverage.md | True | 17555 |
| experiments/cape_kg_eacl_20260627/06_release/cq_query_pack.md | True | 29675 |
| experiments/cape_kg_eacl_20260627/06_release/paper_section_source_map.md | True | 9141 |

### Q02_reproducibility_private_data. 데이터가 공개되지 않으면 재현성이 낮지 않은가?

- Concern class: `reproducibility`
- Status: `mitigated_public_safe_release_rights_review_required`
- Paper sections: Dataset and Annotation, Release and Reproducibility, Ethics
- Remaining gate: external rights review before public source-text release

**Short answer, Korean**

raw OCR/source text는 권리 검토 전 공개하지 않는다. 대신 schema, prompts, evaluation scripts, provenance, public-safe synthetic examples, public benchmark adapters, release bundle manifest를 공개 가능한 재현성 package로 제시한다.

**Short answer, English**

Raw OCR/source text should not be released before rights clearance. Reproducibility is mitigated through schemas, prompts, evaluation scripts, provenance, public-safe synthetic examples, public benchmark adapters, and release-bundle manifests.

**Safe claim boundary**

Public-safe reproducibility scaffolding is claimable as setup evidence.

**Must not claim yet**

Do not state that private source text can be redistributed or that rights review is complete.

**Evidence files**

| path | exists | bytes |
| --- | --- | --- |
| experiments/cape_kg_eacl_20260627/06_release/public_reproducibility_manifest.md | True | 19910 |
| experiments/cape_kg_eacl_20260627/06_release/public_synthetic_examples/README.md | True | 969 |
| experiments/cape_kg_eacl_20260627/06_release/external_resource_license_report.md | True | 2807 |
| experiments/cape_kg_eacl_20260627/06_release/data_release_ethics_statement.md | True | 6315 |
| experiments/cape_kg_eacl_20260627/06_release/provenance_manifest.md | True | 55803 |
| experiments/cape_kg_eacl_20260627/06_release/release_bundle_safety_report.md | True | 2110 |

### Q03_existing_ontology_guided_extraction. ontology-guided extraction은 이미 많지 않은가?

- Concern class: `novelty`
- Status: `partially_mitigated_final_gain_pending`
- Paper sections: Related Work, Method, Ablation
- Remaining gate: human-gold ablation scoring

**Short answer, Korean**

차별점은 ontology guidance 자체가 아니라 CQ-anchored schema retrieval, procedural node/edge schema, component evidence spans, validators, active-review queue, NCS/PCF standard bridge를 하나의 평가 가능한 pipeline으로 묶는 데 있다.

**Short answer, English**

The novelty claim should not be generic ontology guidance. It should focus on combining CQ-anchored schema retrieval, procedural node/edge schemas, component evidence spans, validators, active-review queues, and NCS/PCF standard bridging in an evaluable pipeline.

**Safe claim boundary**

Method composition and artifact coverage are safe to claim.

**Must not claim yet**

Do not claim that each module independently improves final quality until ablations are scored against human gold.

**Evidence files**

| path | exists | bytes |
| --- | --- | --- |
| experiments/cape_kg_eacl_20260627/06_release/method_novelty_positioning.md | True | 10144 |
| experiments/cape_kg_eacl_20260627/06_release/method_module_coverage.md | True | 17555 |
| experiments/cape_kg_eacl_20260627/06_release/prompt_node_edge_traceability.md | True | 13157 |
| experiments/cape_kg_eacl_20260627/04_evaluation/evidence_span_granularity_report.md | True | 1580 |
| experiments/cape_kg_eacl_20260627/04_evaluation/structural_evaluation_report.md | True | 2087 |
| experiments/cape_kg_eacl_20260627/06_release/reviewer_risk_register.md | True | 17456 |

### Q04_why_korean_enterprise_documents. 왜 Korean enterprise document인가?

- Concern class: `dataset_motivation`
- Status: `claimable_setup_human_quality_pending`
- Paper sections: Dataset and Annotation, Analysis
- Remaining gate: two-annotator labels, adjudication, and IAA

**Short answer, Korean**

이 데이터는 OCR noise, 장문 절차, 한국어/영어 alias 혼합, task-artifact-role-flow가 얽힌 업무 문서라는 IE challenge를 제공한다. 현재 5,009 sentence OCR evidence index와 120 evaluation chunks, 100 priority review chunks가 준비되어 있다.

**Short answer, English**

The corpus is motivated as an IE challenge with OCR noise, long procedural context, mixed Korean/English aliases, and intertwined task-artifact-role-flow structures. The current setup includes 5,009 OCR evidence sentences, 120 evaluation chunks, and 100 priority review chunks.

**Safe claim boundary**

Dataset challenge and sampling setup are safe to describe.

**Must not claim yet**

Do not claim benchmark quality or annotation reliability until annotation and IAA are complete.

**Evidence files**

| path | exists | bytes |
| --- | --- | --- |
| outputs/06_triples/evidence_anchors.jsonl | True | 1676699 |
| experiments/cape_kg_eacl_20260627/01_data/evaluation_chunks.jsonl | True | 495269 |
| experiments/cape_kg_eacl_20260627/06_release/gold_sampling_coverage_report.md | True | 4889 |
| experiments/cape_kg_eacl_20260627/06_release/annotation_qc_report.md | True | 1384 |
| experiments/cape_kg_eacl_20260627/06_release/human_review_packet_integrity.md | True | 2505 |

### Q05_prompt_engineering. LLM prompt engineering 아닌가?

- Concern class: `method_rigor`
- Status: `mitigated_with_constraints_and_diagnostics`
- Paper sections: Method, Experiments, Reproducibility
- Remaining gate: human-gold semantic correctness evaluation

**Short answer, Korean**

CAPE-KG는 prompt만이 아니라 strict JSON contract, schema retrieval, constrained predicate set, component evidence spans, ontology/SHACL validation, procedural diagnostics, provenance lock으로 통제된다.

**Short answer, English**

CAPE-KG is controlled by more than prompts: strict JSON contracts, schema retrieval, constrained predicates, component evidence spans, ontology/SHACL validation, procedural diagnostics, and provenance locks constrain the pipeline.

**Safe claim boundary**

Engineering controls, validators, and provenance are safe setup claims.

**Must not claim yet**

Do not equate strict JSON or SHACL pass rates with final semantic correctness.

**Evidence files**

| path | exists | bytes |
| --- | --- | --- |
| experiments/cape_kg_eacl_20260627/02_schema/prompts/strict_json_contract.txt | True | 664 |
| experiments/cape_kg_eacl_20260627/06_release/strict_json_diagnostics.md | True | 8741 |
| experiments/cape_kg_eacl_20260627/06_release/evaluation_protocol_lock.md | True | 19847 |
| outputs/12_rdf/cape_kg_shacl_validation_report.md | True | 1327 |
| experiments/cape_kg_eacl_20260627/06_release/provenance_manifest.md | True | 55803 |
| experiments/cape_kg_eacl_20260627/06_release/prompt_node_edge_traceability.md | True | 13157 |

### Q06_subjective_evaluation. 평가가 subjective하지 않은가?

- Concern class: `evaluation_rigor`
- Status: `scaffold_ready_human_metrics_pending`
- Paper sections: Experiments, Main Results, Analysis
- Remaining gate: completed human-gold labels and scorer refresh

**Short answer, Korean**

평가는 node/edge F1, evidence EM/IoU, unsupported edge rate, ontology conformance, procedural consistency, CQ answerability, mapping P@K/MRR/nDCG로 정량화되도록 준비되어 있다. 현재 final human-gold 값은 pending이다.

**Short answer, English**

The evaluation is designed around quantitative metrics: node/edge F1, evidence EM/IoU, unsupported edge rate, ontology conformance, procedural consistency, CQ answerability, and mapping P@K/MRR/nDCG. Final human-gold values remain pending.

**Safe claim boundary**

Metric definitions and scorer readiness are safe to describe.

**Must not claim yet**

Do not report silver/proxy diagnostics as main human-gold performance.

**Evidence files**

| path | exists | bytes |
| --- | --- | --- |
| experiments/cape_kg_eacl_20260627/06_release/paper_tables.md | True | 14924 |
| experiments/cape_kg_eacl_20260627/06_release/post_human_scoring_readiness.md | True | 7034 |
| experiments/cape_kg_eacl_20260627/04_evaluation/human_gold_metrics.json | True | 1509 |
| experiments/cape_kg_eacl_20260627/04_evaluation/human_gold_span_iou_report.md | True | 1371 |
| experiments/cape_kg_eacl_20260627/04_evaluation/structural_evaluation_report.md | True | 2087 |
| experiments/cape_kg_eacl_20260627/06_release/claim_gate_report.md | True | 4370 |

### Q07_ncs_pcf_nlp_contribution. NCS/PCF mapping이 NLP contribution인가?

- Concern class: `downstream_scope`
- Status: `candidate_pipeline_ready_expert_review_pending`
- Paper sections: Downstream Evaluation, Analysis
- Remaining gate: mapping and crosswalk expert review

**Short answer, Korean**

NCS/PCF는 핵심 NLP contribution이 아니라 downstream standard-taxonomy alignment task로 제한한다. core contribution은 evidence-grounded procedural IE이고, NCS/PCF mapping은 KG가 표준 taxonomy alignment에 유용한지 검증하는 후속 평가다.

**Short answer, English**

NCS/PCF mapping should be scoped as a downstream standard-taxonomy alignment task, not the core NLP contribution. The core contribution is evidence-grounded procedural IE; mapping evaluates whether the resulting KG helps standard-taxonomy alignment.

**Safe claim boundary**

Candidate generation and downstream task framing are safe to discuss.

**Must not claim yet**

Do not claim P@K, MRR, nDCG, accept-rate, or utility until expert review is complete.

**Evidence files**

| path | exists | bytes |
| --- | --- | --- |
| experiments/cape_kg_eacl_20260627/04_evaluation/mapping_downstream_report.md | True | 2824 |
| experiments/cape_kg_eacl_20260627/06_release/mapping_review_progress_report.md | True | 4317 |
| experiments/cape_kg_eacl_20260627/04_evaluation/ncs_pcf_crosswalk_report.md | True | 4308 |
| experiments/cape_kg_eacl_20260627/04_evaluation/mapping_expert_metrics.json | True | 1675 |
| experiments/cape_kg_eacl_20260627/04_evaluation/crosswalk_expert_metrics.json | True | 1115 |
| experiments/cape_kg_eacl_20260627/06_release/rq_evidence_matrix.md | True | 14252 |

## Claim Policy

- `mitigated_*` and `*_ready_*` statuses mean paper sections can describe setup, design, diagnostics, or candidate generation.
- Human-gold extraction quality, IAA, adjudicated correctness, mapping utility, and active-review efficiency remain unclaimable until the relevant returns are imported and scoring is refreshed.
- Silver/proxy diagnostics may support debugging and reviewer-risk planning, but must not be reported as final main results.
- This artifact intentionally keeps `safe_to_use_as_submission=false` and `submission_ready=false`.
