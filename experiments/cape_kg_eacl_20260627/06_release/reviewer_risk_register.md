# CAPE-KG Reviewer Risk Register

Generated: 2026-06-29T18:56:35.552881+00:00
Experiment: `experiments/cape_kg_eacl_20260627`

이 문서는 EACL/ARR 리뷰어가 제기할 가능성이 큰 우려를 현재 산출물, claim 가능 범위, 남은 human/expert gate와 연결한 제출 준비용 risk register입니다.
최종 성능 claim은 human-gold annotation, IAA, adjudication, expert review가 끝난 뒤에만 가능합니다.

## Summary

- Claim status: `reviewer_risk_register_ready_with_open_human_gates`
- Risks: 13 total; critical=2, high=5, medium=6
- Open risks: 5 (R02_human_gold_missing, R07_mapping_downstream_labels, R08_crosswalk_downstream_utility, R09_active_review_effort, R13_submission_status_overclaim)
- Mitigated/partial risks: 7 mitigated, 1 partial
- Missing required evidence files: 0
- Paper-claim-allowed setup/auxiliary items now: 4

## Source Status

| item | value |
| --- | --- |
| claim_gate_overall_status | `FAIL` |
| claim_gate_required_failures | `4` |
| claim_gate_optional_failures | `2` |
| readiness_claim_status | `pending_human_gold_iaa_and_human_gold_scoring` |
| compliance_completion_status | `not_complete_pending_human_gold_iaa_adjudication_and_expert_review` |
| pre_human_validation_source_json | `experiments/cape_kg_eacl_20260627/06_release/pre_human_handoff_validation.json` |
| pre_human_validation_source_md | `experiments/cape_kg_eacl_20260627/06_release/pre_human_handoff_validation.md` |

## Risk Table

| id | severity | status | claim safety | reviewer concern | current evidence | remaining action |
| --- | --- | --- | --- | --- | --- | --- |
| R01_task_framing | high | `mitigated_as_pre_human_setup` | `claimable_setup_not_final_performance` | The work may look like a Korean domain KG construction case rather than a generalizable NLP task. | CAPE-KG is framed as evidence-grounded procedural KG extraction with RQ1-RQ4 and M1-M11 artifacts. | Use this framing consistently in the paper; final empirical claims still require human-gold scoring. |
| R02_human_gold_missing | critical | `open_human_required` | `not_claimable` | Main extraction quality cannot be trusted without adjudicated human-gold labels and IAA. | 0/100 adjudicated chunks, 0/500 gold items, required claim-gate failures=4. | Complete two-annotator labeling and adjudication for at least 100 chunks.; Adjudicate enough nodes, edges, and evidence anchors to reach 500 gold items.; Import completed annotator A/B files and recompute IAA.; Score P_cape_kg_actual against adjudicated human gold after gold completion. |
| R03_silver_proxy_overclaim | high | `mitigated_with_claim_gate` | `diagnostic_only_until_gold` | Silver/proxy diagnostics may be mistaken for final paper performance. | Claimable table status=pending_human_gold_and_or_expert_review; pre-human validation=PASS; see pre_human_handoff_validation.md for the current check count. | Keep all silver/proxy tables labeled as diagnostics until adjudicated human-gold metrics are recomputed. |
| R04_method_novelty | high | `partially_mitigated` | `method_artifacts_claimable_final_gain_pending` | The method may appear too close to existing ontology-guided or LLM-KG extraction pipelines. | M1-M11 coverage missing artifacts=0; B3/B4/B6-family baselines, six ablations, and novelty-positioning evidence are present. | After human-gold scoring, report whether CQ retrieval, evidence grounding, validators, and standard bridge improve metrics. |
| R05_public_reproducibility | high | `mitigated_with_public_safe_release_plan` | `claimable_setup_rights_review_still_required` | The private Korean source corpus may not be redistributable, weakening reproducibility. | External resources=6; public benchmarks=2; rights-review-required resources=3; public-safe reproducibility rows=67. | Do not release raw OCR/source-derived text unless rights are cleared; use public-safe skeleton, synthetic examples, prompts, schemas, and public benchmark adapters. |
| R06_public_benchmark_generalization | medium | `mitigated_as_auxiliary_evidence` | `auxiliary_claimable_not_main_result` | External generalization evidence may be too thin if only internal Korean documents are evaluated. | PAGED items=100; Text2KG items=200; strong_cross_run=True. | Present public benchmark results as auxiliary robustness evidence, not as a substitute for target-corpus human-gold results. |
| R07_mapping_downstream_labels | high | `open_expert_required` | `not_claimable_until_expert_review` | NCS/PCF downstream mapping utility is not claimable without expert-reviewed relevance labels. | complete source groups=0, pending rows=220, pending groups=44. | Complete Top-5 mapping expert review and recompute P@K, MRR, nDCG@10, accept rate, and explanation quality. |
| R08_crosswalk_downstream_utility | medium | `open_expert_required` | `not_claimable_until_crosswalk_expert_review` | Layer2-bridged NCS-PCF crosswalk utility is not claimable without expert-reviewed pair labels. | candidate rows=220, source tasks=22, completed rows=0, pending rows=220. | Complete NCS-PCF crosswalk expert review and recompute accept rate, Hit@K, P@10, MRR, nDCG@10, utility, and explanation quality. |
| R09_active_review_effort | medium | `open_human_required` | `not_claimable_until_effort_return` | Active-review efficiency claims need human timing and correction outcomes. | human effort status=ready_for_human_effort_collection; reviewed file present=False; pooled rows=204; briefing rows=204; briefing status=review_navigation_only_pending_human_effort. | Collect active_review_human_effort.reviewed.csv and refresh efficiency metrics against adjudicated outcomes. |
| R10_structural_validity | medium | `mitigated_with_structural_diagnostics` | `diagnostic_only_until_human_gold` | Procedural KG claims require evidence that schema, gateway, and artifact-flow constraints are valid. | review checkpoint candidates=45; gateway branch gaps=4; RDF/SHACL export exists=True. | Use structural review returns only after human confirmation; recompute structural metrics after final KG changes. |
| R11_llm_reproducibility | medium | `mitigated_with_strict_json_and_provenance` | `claimable_setup_not_quality_result` | LLM outputs may be brittle because of JSON parsing, prompt drift, or model-run provenance gaps. | strict JSON gate=PASS; revalidated recovery gate=PASS; warning conditions=0. | Keep prompts, model identifiers, raw/valid outputs, and provenance hashes synchronized after any new LLM run. |
| R12_release_bundle_safety | medium | `mitigated_with_bundle_scan` | `claimable_setup` | Release bundles may accidentally include source text, stale nested bundles, or unsafe review files. | release file count=1704; public-safe file count=383; public-safe risk issues=0. | Regenerate release bundle and checksums after any source artifact change. |
| R13_submission_status_overclaim | critical | `open_human_required` | `not_submission_ready` | The project may be presented as EACL-ready even though required human gates are still open. | claim gate=FAIL; minimum blockers=4; strong/optional blockers=4; RQ final claim ready count=0. | Do not mark the submission complete until all minimum human-gold gates and proposed-method human-gold scoring pass. |

## Evidence Files

### R01_task_framing. The work may look like a Korean domain KG construction case rather than a generalizable NLP task.

- Status: `mitigated_as_pre_human_setup`
- Claim safety: `claimable_setup_not_final_performance`
- Evidence coverage: 3/3

| role | path | exists | bytes |
| --- | --- | ---: | ---: |
| RQ-to-evidence mapping | `experiments/cape_kg_eacl_20260627/06_release/rq_evidence_matrix.md` | True | 14252 |
| M1-M11 method coverage | `experiments/cape_kg_eacl_20260627/06_release/method_module_coverage.md` | True | 17555 |
| paper draft with conservative claim scope | `experiments/cape_kg_eacl_20260627/07_reports/eacl_paper_draft.md` | True | 21410 |

### R02_human_gold_missing. Main extraction quality cannot be trusted without adjudicated human-gold labels and IAA.

- Status: `open_human_required`
- Claim safety: `not_claimable`
- Evidence coverage: 3/3

| role | path | exists | bytes |
| --- | --- | ---: | ---: |
| human-gold completion state | `experiments/cape_kg_eacl_20260627/04_evaluation/human_gold_validation_summary.json` | True | 848 |
| human-gold metric placeholder | `experiments/cape_kg_eacl_20260627/04_evaluation/human_gold_metrics.json` | True | 1509 |
| human gate action plan | `experiments/cape_kg_eacl_20260627/06_release/human_gate_action_plan.md` | True | 18799 |

### R03_silver_proxy_overclaim. Silver/proxy diagnostics may be mistaken for final paper performance.

- Status: `mitigated_with_claim_gate`
- Claim safety: `diagnostic_only_until_gold`
- Evidence coverage: 3/3

| role | path | exists | bytes |
| --- | --- | ---: | ---: |
| claimable vs diagnostic result table | `experiments/cape_kg_eacl_20260627/06_release/claimable_main_table.md` | True | 6429 |
| pre-human validation | `experiments/cape_kg_eacl_20260627/06_release/pre_human_handoff_validation.md` | True | 14535 |
| pre-human error analysis with claim scope | `experiments/cape_kg_eacl_20260627/07_reports/error_analysis.md` | True | 12148 |

### R04_method_novelty. The method may appear too close to existing ontology-guided or LLM-KG extraction pipelines.

- Status: `partially_mitigated`
- Claim safety: `method_artifacts_claimable_final_gain_pending`
- Evidence coverage: 4/4

| role | path | exists | bytes |
| --- | --- | ---: | ---: |
| method module artifact coverage | `experiments/cape_kg_eacl_20260627/06_release/method_module_coverage.json` | True | 46695 |
| method novelty positioning matrix | `experiments/cape_kg_eacl_20260627/06_release/method_novelty_positioning.md` | True | 10144 |
| actual LLM silver diagnostics | `experiments/cape_kg_eacl_20260627/04_evaluation/actual_llm_silver_metrics.json` | True | 15122 |
| SAC-KG-style baseline diagnostics | `experiments/cape_kg_eacl_20260627/50_sac_kg_verifier_pruner_baseline_quality_report.md` | True | 827 |

### R05_public_reproducibility. The private Korean source corpus may not be redistributable, weakening reproducibility.

- Status: `mitigated_with_public_safe_release_plan`
- Claim safety: `claimable_setup_rights_review_still_required`
- Evidence coverage: 5/5

| role | path | exists | bytes |
| --- | --- | ---: | ---: |
| data release and ethics statement | `experiments/cape_kg_eacl_20260627/06_release/data_release_ethics_statement.md` | True | 6315 |
| external resource/license report | `experiments/cape_kg_eacl_20260627/06_release/external_resource_license_report.md` | True | 2807 |
| public-safe reproducibility manifest | `experiments/cape_kg_eacl_20260627/06_release/public_reproducibility_manifest.md` | True | 19910 |
| public-safe reproducibility manifest JSON | `experiments/cape_kg_eacl_20260627/06_release/public_reproducibility_manifest.json` | True | 36569 |
| public-safe synthetic examples | `experiments/cape_kg_eacl_20260627/06_release/public_synthetic_examples/README.md` | True | 969 |

### R06_public_benchmark_generalization. External generalization evidence may be too thin if only internal Korean documents are evaluated.

- Status: `mitigated_as_auxiliary_evidence`
- Claim safety: `auxiliary_claimable_not_main_result`
- Evidence coverage: 3/3

| role | path | exists | bytes |
| --- | --- | ---: | ---: |
| public benchmark cross-check summary | `experiments/cape_kg_eacl_20260627/08_public_benchmarks/public_benchmark_crosscheck_summary.json` | True | 3839 |
| public benchmark report | `experiments/cape_kg_eacl_20260627/08_public_benchmarks/public_benchmark_crosscheck_report.md` | True | 1379 |
| public benchmark manifest | `experiments/cape_kg_eacl_20260627/08_public_benchmarks/public_benchmark_manifest.json` | True | 17745 |

### R07_mapping_downstream_labels. NCS/PCF downstream mapping utility is not claimable without expert-reviewed relevance labels.

- Status: `open_expert_required`
- Claim safety: `not_claimable_until_expert_review`
- Evidence coverage: 3/3

| role | path | exists | bytes |
| --- | --- | ---: | ---: |
| mapping review progress report | `experiments/cape_kg_eacl_20260627/06_release/mapping_review_progress_report.md` | True | 4317 |
| mapping expert metric placeholder | `experiments/cape_kg_eacl_20260627/04_evaluation/mapping_expert_metrics.json` | True | 1675 |
| priority mapping groups | `experiments/cape_kg_eacl_20260627/05_review/mapping_review_next_20_groups.csv` | True | 4320 |

### R08_crosswalk_downstream_utility. Layer2-bridged NCS-PCF crosswalk utility is not claimable without expert-reviewed pair labels.

- Status: `open_expert_required`
- Claim safety: `not_claimable_until_crosswalk_expert_review`
- Evidence coverage: 3/3

| role | path | exists | bytes |
| --- | --- | ---: | ---: |
| crosswalk expert metric placeholder | `experiments/cape_kg_eacl_20260627/04_evaluation/crosswalk_expert_metrics.json` | True | 1115 |
| crosswalk review manifest | `experiments/cape_kg_eacl_20260627/01_data/crosswalk_review/crosswalk_review_manifest.json` | True | 1538 |
| crosswalk review sheet | `experiments/cape_kg_eacl_20260627/01_data/crosswalk_review/crosswalk_review_sheet.csv` | True | 130781 |

### R09_active_review_effort. Active-review efficiency claims need human timing and correction outcomes.

- Status: `open_human_required`
- Claim safety: `not_claimable_until_effort_return`
- Evidence coverage: 6/6

| role | path | exists | bytes |
| --- | --- | ---: | ---: |
| active-review human effort report | `experiments/cape_kg_eacl_20260627/04_evaluation/active_review_human_effort_report.md` | True | 2911 |
| active-review effort briefing | `experiments/cape_kg_eacl_20260627/06_release/active_review_human_effort_briefing.md` | True | 15523 |
| active-review effort briefing CSV | `experiments/cape_kg_eacl_20260627/05_review/active_review_human_effort_briefing.csv` | True | 98684 |
| active-review effort briefing summary | `experiments/cape_kg_eacl_20260627/06_release/active_review_human_effort_briefing.json` | True | 1880 |
| human effort template | `experiments/cape_kg_eacl_20260627/05_review/active_review_human_effort_template.csv` | True | 47175 |
| human effort protocol | `experiments/cape_kg_eacl_20260627/06_release/active_review_human_effort_plan.md` | True | 2911 |

### R10_structural_validity. Procedural KG claims require evidence that schema, gateway, and artifact-flow constraints are valid.

- Status: `mitigated_with_structural_diagnostics`
- Claim safety: `diagnostic_only_until_human_gold`
- Evidence coverage: 3/3

| role | path | exists | bytes |
| --- | --- | ---: | ---: |
| structural evaluation report | `experiments/cape_kg_eacl_20260627/04_evaluation/structural_evaluation_report.md` | True | 2087 |
| structural gap worklist | `experiments/cape_kg_eacl_20260627/04_evaluation/structural_gap_worklist_report.md` | True | 8155 |
| RDF/SHACL validation report | `outputs/12_rdf/cape_kg_shacl_validation_report.md` | True | 1327 |

### R11_llm_reproducibility. LLM outputs may be brittle because of JSON parsing, prompt drift, or model-run provenance gaps.

- Status: `mitigated_with_strict_json_and_provenance`
- Claim safety: `claimable_setup_not_quality_result`
- Evidence coverage: 3/3

| role | path | exists | bytes |
| --- | --- | ---: | ---: |
| strict JSON diagnostics | `experiments/cape_kg_eacl_20260627/06_release/strict_json_diagnostics.md` | True | 8741 |
| provenance manifest | `experiments/cape_kg_eacl_20260627/06_release/provenance_manifest.md` | True | 55803 |
| LLM run index | `experiments/cape_kg_eacl_20260627/04_evaluation/provenance_llm_run_index.csv` | True | 16241 |

### R12_release_bundle_safety. Release bundles may accidentally include source text, stale nested bundles, or unsafe review files.

- Status: `mitigated_with_bundle_scan`
- Claim safety: `claimable_setup`
- Evidence coverage: 4/4

| role | path | exists | bytes |
| --- | --- | ---: | ---: |
| release bundle manifest | `experiments/cape_kg_eacl_20260627/06_release/release_bundle_manifest.json` | True | 37341 |
| release bundle safety report | `experiments/cape_kg_eacl_20260627/06_release/release_bundle_safety_report.md` | True | 2110 |
| release checksum file | `experiments/cape_kg_eacl_20260627/06_release/release_bundle_checksums.sha256` | True | 378 |
| public reproducibility manifest included in public-safe skeleton | `experiments/cape_kg_eacl_20260627/06_release/public_reproducibility_manifest.md` | True | 19910 |

### R13_submission_status_overclaim. The project may be presented as EACL-ready even though required human gates are still open.

- Status: `open_human_required`
- Claim safety: `not_submission_ready`
- Evidence coverage: 3/3

| role | path | exists | bytes |
| --- | --- | ---: | ---: |
| completion audit | `experiments/cape_kg_eacl_20260627/06_release/submission_completion_audit_ko.md` | True | 25787 |
| plan compliance matrix | `experiments/cape_kg_eacl_20260627/06_release/eacl_plan_compliance_matrix.md` | True | 34933 |
| claim gate report | `experiments/cape_kg_eacl_20260627/06_release/claim_gate_report.md` | True | 4370 |

## Interpretation

- `open_human_required` and `open_expert_required` are expected blockers, not script failures.
- `diagnostic_only_until_gold` means the value can guide debugging or slides, but not final performance claims.
- `claimable_setup` means the artifact supports reproducibility or experimental setup, not method quality.
