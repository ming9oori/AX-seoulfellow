# CAPE-KG Claim Language Guardrails

Generated: 2026-06-29T18:56:33.700948+00:00
Plan: `AX_EACL_submission_review_revised_plan.md`
Experiment: `experiments/cape_kg_eacl_20260627`

이 문서는 논문 초안, 발표자료, 교수님 보고에서 사용할 수 있는 표현과 아직 쓰면 안 되는 표현을 claim 단위로 고정한 guardrail입니다. 현재 상태는 pre-human handoff ready이며, 최종 제출 승인이나 최종 성능 claim이 아닙니다.

## Summary

| Item | Value |
| --- | --- |
| Overall status | PASS |
| Claim status | claim_language_guardrails_ready_not_submission_complete |
| Safe to use as submission | False |
| Submission ready | False |
| Claims | 10 |
| Claimable setup/diagnostic claims | 4 |
| Pending human/expert claims | 5 |
| Rights-review gated claims | 1 |
| Missing evidence files | 0 |
| Claim gate | FAIL |
| Pre-human validation | PASS |
| Pre-human checks | 92 |

## Claim Policy

- Use claimable_setup_or_diagnostic wording only for setup, construction, structural diagnostics, and reproducibility framing.
- Use diagnostic_only or pending wording for any silver/proxy metric.
- Do not state final extraction superiority until adjudicated human-gold scoring is complete.
- Do not state NCS/PCF mapping utility until expert review returns are imported.
- Do not state active-review efficiency until timing/correction evidence is returned.
- Do not state public release of source text until rights review is complete.

## Guardrail Table

| claim_id | area | current_status | safe_phrasing_ko | safe_phrasing_en | next_gate |
| --- | --- | --- | --- | --- | --- |
| C01_task_and_method_framing | Task framing and CAPE-KG contribution | claimable_setup_or_diagnostic | 본 연구는 CAPE-KG task framing과 pre-human 실험 인프라를 완성했으며, 최종 성능 claim은 human-gold 이후 확정한다. | We present the CAPE-KG framing and pre-human experimental infrastructure; final performance claims remain gated by human-gold evaluation. | minimum human-gold gates |
| C02_kg_construction_counts | KG construction counts and structural integrity | claimable_setup_or_diagnostic | Layer 2 KG construction is complete as an automatic build artifact: 220 nodes and 947 evidence-linked edges. | The Layer 2 KG is complete as an automatic build artifact: 220 nodes and 947 evidence-linked edges. | human correctness validation |
| C03_main_extraction_performance | Main extraction performance | pending_human_gold | Main extraction performance is not yet claimable; the scoring pipeline is ready and waiting for adjudicated human-gold returns. | Main extraction performance is not yet claimable; the scoring pipeline is ready pending adjudicated human-gold returns. | human-gold annotation, IAA, adjudication, and scoring |
| C04_evidence_faithfulness | Evidence grounding and faithfulness | pending_human_gold | Evidence diagnostics are available, but faithfulness claims remain diagnostic until adjudicated span evidence is imported. | Evidence diagnostics are available, but faithfulness claims remain diagnostic until adjudicated span evidence is imported. | adjudicated span and unsupported-edge evaluation |
| C05_baseline_ablation_superiority | Baseline, ablation, and model-scaling superiority | pending_human_gold | Baseline, ablation, and scaling runs are complete as silver/proxy diagnostics; final comparative claims require human-gold scoring. | Baseline, ablation, and scaling runs are complete as silver/proxy diagnostics; final comparative claims require human-gold scoring. | human-gold comparative scoring |
| C06_structural_diagnostics | Structural conformance, procedural consistency, and CQ answerability | claimable_setup_or_diagnostic | Structural diagnostics indicate schema and query coverage, not final semantic correctness. | Structural diagnostics indicate schema and query coverage, not final semantic correctness. | human semantic correctness review |
| C07_public_benchmark_adapter | Public benchmark adapter diagnostics | claimable_setup_or_diagnostic | Public benchmark runs are auxiliary adapter diagnostics, not official leaderboard or private-corpus main evidence. | Public benchmark runs are auxiliary adapter diagnostics, not official leaderboard or private-corpus main evidence. | scope-limited auxiliary reporting |
| C08_mapping_crosswalk | NCS/PCF mapping and NCS-PCF crosswalk | pending_expert_review | The standard bridge is candidate-generation evidence only until mapping and crosswalk expert review is complete. | The standard bridge is candidate-generation evidence only until mapping and crosswalk expert review is complete. | mapping and crosswalk expert review |
| C09_active_review_efficiency | Active-review efficiency | pending_human_effort | Active-review artifacts support review navigation only; efficiency claims require returned timing and correction evidence. | Active-review artifacts support review navigation only; efficiency claims require returned timing and correction evidence. | active-review effort return file |
| C10_reproducibility_release | Reproducibility, data release, and ethics | rights_review_required | Reproducibility is supported through public-safe artifacts; source-text release remains rights-gated. | Reproducibility is supported through public-safe artifacts; source-text release remains rights-gated. | rights review and public-safe audit |

## Claim Details

### C01_task_and_method_framing. Task framing and CAPE-KG contribution

- Current status: `claimable_setup_or_diagnostic`
- Paper sections: Introduction, Task Definition, Method
- Next gate: minimum human-gold gates

Allowed now:

- KO: CAPE-KG를 한국어 장문 업무 문서의 evidence-grounded procedural KG construction task로 정의했고, CQ/schema/evidence/validator/standard bridge를 결합한 pre-human 방법론 산출물을 구축했다고 말할 수 있다.
- EN: We can describe CAPE-KG as a pre-human, evidence-grounded procedural KG construction framework combining CQs, schema control, evidence grounding, validation, and standard-taxonomy bridging.

Forbidden now:

- KO: EACL 제출이 완료되었거나, 최종 성능 우수성이 입증되었다고 말하면 안 된다.
- EN: Do not say the EACL submission is complete or that final superiority has been proven.

Required before stronger claim:
- Adjudicated human-gold extraction metrics
- IAA and adjudication evidence
- Final paper tables refreshed after human returns

Unsafe phrasing examples:
- CAPE-KG is ready for EACL submission.
- CAPE-KG outperforms all baselines on the target corpus.

Evidence files:
- `AX_EACL_submission_review_revised_plan.md`
- `experiments/cape_kg_eacl_20260627/06_release/method_novelty_positioning.md`
- `experiments/cape_kg_eacl_20260627/06_release/rq_evidence_matrix.md`
- `experiments/cape_kg_eacl_20260627/06_release/prompt_node_edge_traceability.md`

### C02_kg_construction_counts. KG construction counts and structural integrity

- Current status: `claimable_setup_or_diagnostic`
- Paper sections: Dataset, KG Construction, Analysis
- Next gate: human correctness validation

Allowed now:

- KO: Layer 1 NCS/PCF와 Layer 2 업무 KG가 구축되었고, 현재 Layer 2는 220 nodes, 947 edges이며 accepted edge evidence 누락과 dangling edge가 없다고 말할 수 있다.
- EN: We can report constructed KG counts and structural checks: Layer 2 currently has 220 nodes and 947 edges with no missing accepted-edge evidence or dangling edges.

Forbidden now:

- KO: 이 count를 human-gold 정답 대비 정확도 또는 추출 성능으로 해석하면 안 된다.
- EN: Do not interpret construction counts as human-gold accuracy or extraction quality.

Required before stronger claim:
- Human verification of node/edge correctness
- Error analysis refreshed after adjudication

Unsafe phrasing examples:
- The constructed KG is correct with high precision.
- The KG has been fully validated by humans.

Evidence files:
- `outputs/10_evaluation/final_build_report.md`
- `outputs/07_layer2_graph/layer2_graph_quality_report.md`
- `outputs/12_rdf/cape_kg_shacl_validation_report.md`
- `outputs/09_visualization/kg_viewer.html`

### C03_main_extraction_performance. Main extraction performance

- Current status: `pending_human_gold`
- Paper sections: Experiments, Main Results, Conclusion
- Next gate: human-gold annotation, IAA, adjudication, and scoring

Allowed now:

- KO: 현재는 main extraction result가 pending human-gold라고만 말할 수 있다.
- EN: At present, main extraction performance must be described as pending human-gold evaluation.

Forbidden now:

- KO: silver/proxy F1을 final main table 또는 논문 성능 우수성으로 제시하면 안 된다.
- EN: Do not present silver/proxy F1 as the final main-result table or as superiority evidence.

Required before stronger claim:
- 100+ adjudicated chunks
- 500+ gold node/edge/evidence items
- 2+ annotator IAA
- P_cape_kg_actual scored against adjudicated human gold

Unsafe phrasing examples:
- CAPE-KG achieves the best extraction F1.
- The main table proves the proposed method is superior.

Evidence files:
- `experiments/cape_kg_eacl_20260627/04_evaluation/human_gold_metrics.json`
- `experiments/cape_kg_eacl_20260627/04_evaluation/human_gold_validation_summary.json`
- `experiments/cape_kg_eacl_20260627/06_release/claimable_main_table.md`
- `experiments/cape_kg_eacl_20260627/06_release/post_human_scoring_readiness.md`
- `experiments/cape_kg_eacl_20260627/06_release/claim_gate_report.md`

### C04_evidence_faithfulness. Evidence grounding and faithfulness

- Current status: `pending_human_gold`
- Paper sections: Method, Faithfulness Evaluation, Error Analysis
- Next gate: adjudicated span and unsupported-edge evaluation

Allowed now:

- KO: 자동 구축 edge의 evidence attachment와 component span diagnostic은 보고할 수 있지만, human-gold faithfulness claim은 보류해야 한다.
- EN: We can report automatic evidence attachment and component-span diagnostics, while holding human-gold faithfulness claims.

Forbidden now:

- KO: evidence span 정확도 또는 unsupported edge 감소를 human-gold로 입증했다고 말하면 안 된다.
- EN: Do not say evidence-span correctness or unsupported-edge reduction is proven against human gold.

Required before stronger claim:
- Adjudicated component span returns
- Human-gold exact/IoU evidence metrics
- Unsupported-edge adjudication

Unsafe phrasing examples:
- CAPE-KG eliminates hallucination.
- Evidence spans are human-validated.

Evidence files:
- `experiments/cape_kg_eacl_20260627/04_evaluation/evidence_grounding_report.md`
- `experiments/cape_kg_eacl_20260627/04_evaluation/evidence_span_granularity_report.md`
- `experiments/cape_kg_eacl_20260627/04_evaluation/human_gold_span_iou_report.md`
- `experiments/cape_kg_eacl_20260627/06_release/post_human_scoring_readiness.md`

### C05_baseline_ablation_superiority. Baseline, ablation, and model-scaling superiority

- Current status: `pending_human_gold`
- Paper sections: Experiments, Ablation, Model Scaling
- Next gate: human-gold comparative scoring

Allowed now:

- KO: B0-B6, P_cape_kg_actual, P_minus_* 조건과 Qwen3 scaling을 실행했고, 현재 수치는 silver/proxy diagnostic이라고 말할 수 있다.
- EN: We can report that B0-B6, P_cape_kg_actual, P_minus_* ablations, and Qwen3 scaling diagnostics were run.

Forbidden now:

- KO: P_cape_kg_actual이 baseline보다 최종적으로 우수하다고 말하면 안 된다.
- EN: Do not claim final superiority of P_cape_kg_actual over baselines yet.

Required before stronger claim:
- Same frozen metric definitions applied to adjudicated human gold
- Final statistical tests after human-gold scoring

Unsafe phrasing examples:
- Qwen3-32B-AWQ proves monotonic model scaling.
- The ablation proves CQ improves final F1.

Evidence files:
- `experiments/cape_kg_eacl_20260627/04_evaluation/actual_llm_silver_metrics.json`
- `experiments/cape_kg_eacl_20260627/06_release/qwen3_model_scaling_report.md`
- `experiments/cape_kg_eacl_20260627/06_release/paper_tables.md`
- `experiments/cape_kg_eacl_20260627/06_release/evaluation_protocol_lock.md`

### C06_structural_diagnostics. Structural conformance, procedural consistency, and CQ answerability

- Current status: `claimable_setup_or_diagnostic`
- Paper sections: Evaluation, Analysis
- Next gate: human semantic correctness review

Allowed now:

- KO: ontology conformance, procedural consistency, CQ answerability 같은 자동 구조 진단은 보고할 수 있다.
- EN: We can report automatic structural diagnostics such as ontology conformance, procedural consistency, and CQ answerability.

Forbidden now:

- KO: 구조적으로 answerable하다는 사실을 답변의 human-gold correctness로 해석하면 안 된다.
- EN: Do not treat structural answerability as human-gold answer correctness.

Required before stronger claim:
- Human-gold correctness check for extracted items
- Human review of structural gap worklist

Unsafe phrasing examples:
- All competency questions are correctly answered.
- The KG is semantically complete.

Evidence files:
- `experiments/cape_kg_eacl_20260627/04_evaluation/structural_evaluation_report.md`
- `experiments/cape_kg_eacl_20260627/06_release/cq_query_pack.md`
- `experiments/cape_kg_eacl_20260627/04_evaluation/structural_gap_worklist_report.md`
- `outputs/12_rdf/cape_kg_shacl_validation_report.md`

### C07_public_benchmark_adapter. Public benchmark adapter diagnostics

- Current status: `claimable_setup_or_diagnostic`
- Paper sections: Experiments, Generalization Check, Reproducibility
- Next gate: scope-limited auxiliary reporting

Allowed now:

- KO: PAGED/Text2KG adapter 기반 public cross-check를 auxiliary diagnostic으로 실행했다고 말할 수 있다.
- EN: We can report the PAGED/Text2KG adapter runs as auxiliary diagnostics.

Forbidden now:

- KO: public benchmark 결과를 private Korean enterprise corpus의 main result로 대체하면 안 된다.
- EN: Do not replace the private Korean enterprise main result with public-adapter diagnostics.

Required before stronger claim:
- Final private-corpus human-gold scoring
- Explicit benchmark scope and adapter limitations

Unsafe phrasing examples:
- The public benchmark proves generalization of the private-corpus method.
- These are official benchmark leaderboard results.

Evidence files:
- `experiments/cape_kg_eacl_20260627/08_public_benchmarks/public_benchmark_crosscheck_summary.json`
- `experiments/cape_kg_eacl_20260627/08_public_benchmarks/public_benchmark_crosscheck_report.md`
- `experiments/cape_kg_eacl_20260627/06_release/public_reproducibility_manifest.md`

### C08_mapping_crosswalk. NCS/PCF mapping and NCS-PCF crosswalk

- Current status: `pending_expert_review`
- Paper sections: Downstream Evaluation, Standard Taxonomy Bridge
- Next gate: mapping and crosswalk expert review

Allowed now:

- KO: NCS/PCF Top-K mapping 후보와 Layer2-bridged NCS-PCF crosswalk 후보를 생성했다고 말할 수 있다.
- EN: We can report that NCS/PCF Top-K mapping candidates and Layer2-bridged NCS-PCF crosswalk candidates were generated.

Forbidden now:

- KO: expert review 없이 P@K, MRR, nDCG@10, utility, accept-rate를 주장하면 안 된다.
- EN: Do not claim P@K, MRR, nDCG@10, utility, or accept-rate without expert review.

Required before stronger claim:
- Mapping expert review returns
- Crosswalk expert review returns
- Refreshed downstream metrics

Unsafe phrasing examples:
- CAPE-KG improves NCS/PCF mapping accuracy.
- The crosswalk utility is expert-validated.

Evidence files:
- `experiments/cape_kg_eacl_20260627/04_evaluation/mapping_downstream_report.md`
- `experiments/cape_kg_eacl_20260627/04_evaluation/mapping_expert_metrics.json`
- `experiments/cape_kg_eacl_20260627/04_evaluation/ncs_pcf_crosswalk_report.md`
- `experiments/cape_kg_eacl_20260627/04_evaluation/crosswalk_expert_metrics.json`
- `experiments/cape_kg_eacl_20260627/06_release/mapping_review_progress_report.md`

### C09_active_review_efficiency. Active-review efficiency

- Current status: `pending_human_effort`
- Paper sections: Human-in-the-loop Evaluation, Active Review
- Next gate: active-review effort return file

Allowed now:

- KO: active/uncertainty/random review queue와 human-effort 입력 양식이 준비되었다고 말할 수 있다.
- EN: We can report that active/uncertainty/random review queues and human-effort templates are ready.

Forbidden now:

- KO: 사람 검수 시간이 절감되었거나 active review가 더 효율적이었다고 말하면 안 된다.
- EN: Do not claim reduced review time or active-review efficiency yet.

Required before stronger claim:
- Returned active-review human-effort CSV
- Timing/correction evidence
- Efficiency metrics refreshed after returns

Unsafe phrasing examples:
- Active review reduces annotation cost.
- The queue is proven more efficient than random review.

Evidence files:
- `experiments/cape_kg_eacl_20260627/06_release/active_review_human_effort_plan.md`
- `experiments/cape_kg_eacl_20260627/06_release/active_review_human_effort_briefing.md`
- `experiments/cape_kg_eacl_20260627/04_evaluation/active_review_human_effort_report.md`
- `experiments/cape_kg_eacl_20260627/04_evaluation/active_review_efficiency_report.md`

### C10_reproducibility_release. Reproducibility, data release, and ethics

- Current status: `rights_review_required`
- Paper sections: Limitations, Ethics, Reproducibility, Artifact Appendix
- Next gate: rights review and public-safe audit

Allowed now:

- KO: code, prompt, schema, synthetic public-safe examples, public-safe bundle 경계를 설명할 수 있다.
- EN: We can describe code, prompts, schema, synthetic public-safe examples, and public-safe bundle boundaries.

Forbidden now:

- KO: 원문 corpus 또는 내부 검수 파일을 공개할 수 있다고 말하면 안 된다.
- EN: Do not claim raw source corpus or internal review files can be released publicly.

Required before stronger claim:
- Rights review for any source-text release
- Final public artifact audit after paper claims are fixed

Unsafe phrasing examples:
- All data will be publicly released.
- The public bundle contains the full private corpus.

Evidence files:
- `experiments/cape_kg_eacl_20260627/06_release/release_bundle_manifest.json`
- `experiments/cape_kg_eacl_20260627/06_release/latest_release_bundle_index.md`
- `experiments/cape_kg_eacl_20260627/06_release/data_release_ethics_statement.md`
- `experiments/cape_kg_eacl_20260627/06_release/external_resource_license_report.md`
- `experiments/cape_kg_eacl_20260627/06_release/public_reproducibility_manifest.md`
- `experiments/cape_kg_eacl_20260627/06_release/public_synthetic_examples/README.md`

## Missing Evidence

- No missing evidence files.

## Use Guidance

- 이 파일의 safe phrasing은 현재 pre-human 발표/보고/초안에 사용할 수 있는 보수적 표현입니다.
- `pending_human_gold`, `pending_expert_review`, `pending_human_effort` claim은 final main table이나 conclusion에 성능 claim으로 쓰지 않습니다.
- `rights_review_required` claim은 public-safe artifact 범위까지만 설명하고, 원문 corpus 공개 가능성은 별도 권리 검토 전까지 주장하지 않습니다.
