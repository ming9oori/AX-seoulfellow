# CAPE-KG Contribution Claim Traceability

Generated: 2026-06-29T18:56:33.501369+00:00
Plan: `AX_EACL_submission_review_revised_plan.md`
Experiment: `experiments/cape_kg_eacl_20260627`

This artifact maps the three revised-plan contribution statements to current evidence, reviewer concerns, metrics, and claim gates.
It is claim-safe: it separates setup/method claims that are currently supported from final performance claims that remain gated by human or expert evidence.

## Summary

- claim_status: `contribution_claim_traceability_ready_pending_human_gold_and_expert_returns`
- contribution_count: `3`
- setup_claimable_count: `3`
- final_performance_claim_ready_count: `0`
- blocked_final_claim_count: `3`
- missing_evidence_file_count: `0`
- linked_rq_count: `4`
- known_rq_count: `4`
- known_metric_count: `10`
- linked_reviewer_question_count: `7`
- known_reviewer_question_count: `7`
- plan_completion_proven: `False`
- claim_gate_overall_status: `FAIL`

## Claim Boundary

- Safe to use pre-human: `True`
- Safe scope: Use for contribution framing, paper outline, reviewer-risk planning, and reproducibility description.
- Final performance claims remain pending: Final performance, benchmark reliability, taxonomy-alignment utility, and active-review efficiency remain pending human-gold, IAA, adjudication, mapping/crosswalk expert review, and human-effort returns.

## Contribution Rows

| id | title | setup claimable now | final performance ready | linked RQs | remaining gates |
| --- | --- | --- | --- | --- | --- |
| C1_task_definition_and_evidence_grounding | Evidence-grounded procedural KG construction task | True | False | RQ1<br>RQ2 | min.gold_chunks<br>min.gold_items<br>min.iaa<br>min.proposed |
| C2_cape_kg_framework | CAPE-KG framework | True | False | RQ1<br>RQ2<br>RQ4 | min.gold_chunks<br>min.gold_items<br>min.iaa<br>min.proposed<br>strong.active_review |
| C3_benchmark_and_standard_taxonomy_alignment | Korean bid/proposal benchmark and standard taxonomy alignment | True | False | RQ3 | min.gold_chunks<br>min.gold_items<br>min.iaa<br>min.proposed<br>strong.mapping_downstream<br>crosswalk.expert_review<br>external_rights_review_for_raw_source_text |

## C1_task_definition_and_evidence_grounding. Evidence-grounded procedural KG construction task

- Plan sentence EN: We formulate evidence-grounded procedural KG construction from long enterprise documents as a constrained information extraction task, requiring typed nodes, relations, and character-level evidence anchors.
- Plan sentence KO: 한국어 장문 업무 문서에서 절차형 KG 구축 문제를 typed node/relation과 evidence grounding이 필요한 constrained information extraction task로 정의한다.
- Current claim boundary: Task formulation, schema, KG artifacts, and automatic diagnostics are claimable; final extraction quality is not.
- Forbidden pre-human claim: CAPE-KG improves final node/edge/evidence F1 over baselines.

### Safe Pre-Human Wording

- KO: 현재는 장문 한국어 업무 문서를 evidence-grounded procedural IE task로 정의하고, 이를 위한 schema, KG 산출물, 자동 진단 지표를 준비했다고 말할 수 있다.
- EN: At the pre-human stage, it is safe to claim the task formulation, schema, KG artifacts, and automatic diagnostics.

### Links

- RQs: `RQ1, RQ2`
- Modules: `M1, M2, M4, M5, M6, M7, M8`
- Reviewer questions: `Q01_domain_application, Q04_why_korean_enterprise_documents, Q06_subjective_evaluation`
- Metrics: `Node F1, Edge F1, Evidence Exact Match, Evidence IoU, Unsupported Edge Rate, Ontology Conformance, Procedural Consistency, CQ Answerability`

### Evidence Files

| role | path | exists | bytes |
| --- | --- | --- | --- |
| revised plan contribution statement | AX_EACL_submission_review_revised_plan.md | True | 29461 |
| RQ-to-evidence matrix | experiments/cape_kg_eacl_20260627/06_release/rq_evidence_matrix.md | True | 14252 |
| metric traceability audit | experiments/cape_kg_eacl_20260627/06_release/metric_traceability_audit.md | True | 4507 |
| prompt/node/edge traceability | experiments/cape_kg_eacl_20260627/06_release/prompt_node_edge_traceability.md | True | 13157 |
| evidence span diagnostic | experiments/cape_kg_eacl_20260627/04_evaluation/evidence_span_granularity_report.md | True | 1580 |
| structural diagnostic report | experiments/cape_kg_eacl_20260627/04_evaluation/structural_evaluation_report.md | True | 2087 |
| final Layer 2 node artifacts | outputs/07_layer2_graph/layer2_nodes.jsonl | True | 94237 |
| final Layer 2 edge artifacts | outputs/07_layer2_graph/layer2_edges.jsonl | True | 331827 |

### Remaining Gates

- `min.gold_chunks`
- `min.gold_items`
- `min.iaa`
- `min.proposed`

## C2_cape_kg_framework. CAPE-KG framework

- Plan sentence EN: We propose CAPE-KG, a competency-question anchored extraction framework that combines schema retrieval, constrained generation, evidence-span verification, ontology validation, and procedural consistency checking.
- Plan sentence KO: CQ 기반 schema retrieval, constrained generation, evidence-span verification, ontology validation, procedural consistency checking을 결합한 CAPE-KG 프레임워크를 제안한다.
- Current claim boundary: Integrated framework implementation and diagnostic coverage are claimable; module-level improvements remain human-gold gated.
- Forbidden pre-human claim: Each CAPE-KG module independently improves final quality.

### Safe Pre-Human Wording

- KO: 현재는 CAPE-KG의 구성 모듈과 검증/진단 체계가 구현되어 있음을 claim할 수 있지만, 각 모듈이 최종 성능을 개선한다는 주장은 human-gold 이후로 보류해야 한다.
- EN: It is safe to claim that the integrated framework and diagnostic scaffolds are implemented; final module gains remain gated.

### Links

- RQs: `RQ1, RQ2, RQ4`
- Modules: `M2, M3, M4, M5, M6, M7, M8, M9, M10`
- Reviewer questions: `Q03_existing_ontology_guided_extraction, Q05_prompt_engineering, Q06_subjective_evaluation`
- Metrics: `Ontology Conformance, Procedural Consistency, CQ Answerability, Active Review Efficiency, Ablation: P - CQ, Ablation: P - Evidence, Ablation: P - Validator, Ablation: P - Active review`

### Evidence Files

| role | path | exists | bytes |
| --- | --- | --- | --- |
| M1-M11 module coverage | experiments/cape_kg_eacl_20260627/06_release/method_module_coverage.md | True | 17555 |
| method novelty positioning | experiments/cape_kg_eacl_20260627/06_release/method_novelty_positioning.md | True | 10144 |
| schema retrieval coverage | experiments/cape_kg_eacl_20260627/06_release/schema_retrieval_coverage_report.md | True | 5476 |
| strict JSON diagnostics | experiments/cape_kg_eacl_20260627/06_release/strict_json_diagnostics.md | True | 8741 |
| locked evaluation protocol | experiments/cape_kg_eacl_20260627/06_release/evaluation_protocol_lock.md | True | 19847 |
| claim language guardrails | experiments/cape_kg_eacl_20260627/06_release/claim_language_guardrails.md | True | 19281 |
| active-review diagnostic | experiments/cape_kg_eacl_20260627/04_evaluation/active_review_efficiency_report.md | True | 4055 |
| human-effort collection protocol | experiments/cape_kg_eacl_20260627/06_release/active_review_human_effort_plan.md | True | 2911 |

### Remaining Gates

- `min.gold_chunks`
- `min.gold_items`
- `min.iaa`
- `min.proposed`
- `strong.active_review`

## C3_benchmark_and_standard_taxonomy_alignment. Korean bid/proposal benchmark and standard taxonomy alignment

- Plan sentence EN: We introduce a Korean bid/proposal work-domain benchmark and evaluate whether the resulting procedural KG improves standard taxonomy alignment to capability and process reference layers.
- Plan sentence KO: 수주·제안 업무 benchmark를 구축하고, 추출된 절차형 KG가 NCS/PCF 표준 taxonomy alignment를 개선하는지 평가한다.
- Current claim boundary: Benchmark/release scaffolds and mapping candidates are claimable; benchmark reliability and taxonomy utility require human/expert returns.
- Forbidden pre-human claim: The benchmark is fully validated or the KG improves NCS/PCF alignment.

### Safe Pre-Human Wording

- KO: 현재는 benchmark 구축 및 공개 가능 재현 패키지, NCS/PCF 후보 생성까지 준비되었다고 말할 수 있다. benchmark 신뢰도와 taxonomy alignment 개선 주장은 사람 검수와 expert review 이후에만 가능하다.
- EN: It is safe to claim benchmark/release scaffolds and mapping candidates; reliability and alignment utility remain expert/human gated.

### Links

- RQs: `RQ3`
- Modules: `M1, M5, M9, M11`
- Reviewer questions: `Q02_reproducibility_private_data, Q04_why_korean_enterprise_documents, Q07_ncs_pcf_nlp_contribution`
- Metrics: `NCS/PCF Mapping P@K, P@1, P@5, MRR, nDCG@10, Expert accept rate, Explanation quality score`

### Evidence Files

| role | path | exists | bytes |
| --- | --- | --- | --- |
| gold sampling coverage report | experiments/cape_kg_eacl_20260627/06_release/gold_sampling_coverage_report.md | True | 4889 |
| public-safe reproducibility manifest | experiments/cape_kg_eacl_20260627/06_release/public_reproducibility_manifest.md | True | 19910 |
| public-safe synthetic examples | experiments/cape_kg_eacl_20260627/06_release/public_synthetic_examples/README.md | True | 969 |
| public benchmark cross-check | experiments/cape_kg_eacl_20260627/08_public_benchmarks/public_benchmark_crosscheck_report.md | True | 1379 |
| Layer2-to-NCS mapping candidates | outputs/08_mapping/l2_ncs_mapping_candidates.jsonl | True | 82404 |
| Layer2-to-PCF mapping candidates | outputs/08_mapping/l2_pcf_mapping_candidates.jsonl | True | 81856 |
| NCS-PCF crosswalk candidates | experiments/cape_kg_eacl_20260627/04_evaluation/ncs_pcf_crosswalk_report.md | True | 4308 |
| mapping review progress | experiments/cape_kg_eacl_20260627/06_release/mapping_review_progress_report.md | True | 4317 |

### Remaining Gates

- `min.gold_chunks`
- `min.gold_items`
- `min.iaa`
- `min.proposed`
- `strong.mapping_downstream`
- `crosswalk.expert_review`
- `external_rights_review_for_raw_source_text`

## Source Artifacts

- `revised_plan`: `AX_EACL_submission_review_revised_plan.md`
- `revised_plan_completion_audit`: `experiments/cape_kg_eacl_20260627/06_release/revised_plan_completion_audit.json`
- `claim_gate_report`: `experiments/cape_kg_eacl_20260627/06_release/claim_gate_report.json`
- `rq_evidence_matrix`: `experiments/cape_kg_eacl_20260627/06_release/rq_evidence_matrix.json`
- `metric_traceability_audit`: `experiments/cape_kg_eacl_20260627/06_release/metric_traceability_audit.json`
- `reviewer_response_prep`: `experiments/cape_kg_eacl_20260627/06_release/reviewer_response_prep.json`
