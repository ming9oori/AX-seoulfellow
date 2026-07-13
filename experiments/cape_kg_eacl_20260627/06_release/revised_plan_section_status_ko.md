# CAPE-KG Revised Plan Section Status

Generated: 2026-06-29T18:56:33.383241+00:00
Plan: `AX_EACL_submission_review_revised_plan.md`
Claim status: `revised_plan_section_status_ready_not_submission_complete`

이 문서는 `AX_EACL_submission_review_revised_plan.md`의 주요 장별 요구사항을 현재 산출물과 직접 연결한 한국어 운영표입니다.
제출 완료 선언이 아니라, revised plan을 어디까지 실행했고 어떤 evidence가 남았는지 확인하기 위한 상태표입니다.

## 핵심 판단

- Pre-human validation: `PASS` (91 PASS / 1 WARN / 0 FAIL)
- Claim gate: `FAIL`
- 계획서 13장 체크리스트: 20개 중 자동 완료 증거 11개, human-blocked 9개
- M1-M11 방법론 모듈: required artifact missing 0개
- Minimum paper-gate return files: 0/11
- Required claim/human return files: 0/14

현재 결론은 명확합니다. KG 구축, 실험 scaffold, release/reproducibility, prompt/schema/evaluation protocol은 준비되었지만, 최종 논문 성능 claim은 human-gold annotation, IAA, adjudication, proposed human-gold scoring, expert review 반환 전에는 열 수 없습니다.

## Revised Plan 장별 상태

| section_id | plan_section | current_status | key_numbers | claim_boundary | next_action | blocking_gate_ids |
| --- | --- | --- | --- | --- | --- | --- |
| S01 | 1. 결론 요약 | method_and_infrastructure_ready_claim_gated | pre-human checks=92; claim gate=FAIL; method modules=11/11 | 최종 성능 claim은 human-gold annotation, IAA, adjudication, P_cape_kg_actual human-gold scoring 이후에만 가능하다. | 사람 검수 반환 전까지는 KG 구축 완료와 최종 성능 claim 미완료를 분리해 보고한다. |  |
| S02 | 2. EACL 제출 적합성 판단 | submission_policy_scaffold_ready_not_submission_ready | submission_ready=False; minimum return files=0/11 | 제출 가능 판단은 최종 paper claim gate가 열린 뒤 다시 해야 한다. | human return 이후 policy checklist와 anonymization scan을 다시 실행한다. |  |
| S03 | 3. Accept 가능성 판단 | risk_register_ready_with_open_human_gates | required gate failures=4; optional gate failures=2 | 최종 성능 claim은 human-gold annotation, IAA, adjudication, P_cape_kg_actual human-gold scoring 이후에만 가능하다. | 교수님 보고에서는 accept 가능성을 현재 결과가 아니라 남은 gate 기준으로 설명한다. |  |
| S04 | 4. 관련 연구 대비 포지셔닝 | positioning_and_baseline_traceability_ready | baseline family coverage includes B0-B6 plus CAPE-KG and ablations. | 선행연구 대비 성능 우위는 human-gold score 이후에만 주장한다. | 논문 본문에는 차별점과 구현 범위를 분리해 쓴다. |  |
| S05 | 5. 수정된 핵심 연구 질문 | rq_evidence_matrix_ready | RQ count=4; final claim-ready RQ count remains gated by human/expert evidence. | RQ별 final answer는 adjudicated human-gold와 expert review 이후 확정한다. | 발표에서는 RQ를 task/evidence/mapping/review-efficiency 네 축으로 설명한다. |  |
| S06 | 6. 수정된 방법론: CAPE-KG | m1_m11_artifacts_present_human_claim_pending | modules=11/11; human-dependent=8 | 방법론 구성은 설명 가능하지만, 모듈별 성능 효과는 human-gold 비교 후 주장한다. | M3-M11의 human-dependent claim boundary를 논문 표와 본문에 유지한다. |  |
| S07 | 7. 온톨로지 스키마 수정안 | schema_rdf_shacl_and_evidence_projection_ready | Layer 2 nodes/edges and evidence anchors are structurally validated; SHACL-style validation is PASS. | schema conformance is structural evidence, not human correctness evidence. | schema terms should stay synchronized with CQ and prompt traceability. |  |
| S08 | 8. 데이터 및 annotation 계획 | annotation_packet_ready_pending_human_returns | minimum chunks=100; candidate edges=1371; required reviewed files=0/14 | annotation package readiness does not create gold labels. | A/B annotator files and adjudication file must be returned before scoring. | gold.completed_chunks;gold.item_count;gold.iaa |
| S09 | 9. 실험 설계 | baseline_ablation_public_benchmark_diagnostics_ready | actual LLM conditions cover the 120-row evaluation set; diagnostic tables are claim-safe until human-gold scoring. | silver/proxy diagnostics must not be reported as final F1/P@K evidence. | human-gold and expert-return refresh will populate final main result cells. | llm.proposed_human_gold_score;mapping.expert_review;crosswalk.expert_review |
| S10 | 10. 논문 contribution 문장 수정안 | contribution_traceability_ready_pending_final_scores | three contribution lines are supportable as task/method/resource framing, not final performance superiority. | 최종 성능 claim은 human-gold annotation, IAA, adjudication, P_cape_kg_actual human-gold scoring 이후에만 가능하다. | 논문 introduction에서는 contribution claim을 gate-safe wording으로 유지한다. |  |
| S11 | 11. EACL 제출용 논문 구조 | draft_and_section_source_map_ready_not_submission_ready | sections=16/16; missing evidence=0; human/expert blocked sections=6 | draft is claim-safe but safe_to_use_as_submission is false. | human returns 이후 Dataset/Experiments/Analysis/Conclusion sections를 final result로 갱신한다. |  |
| S12 | 12. Reviewer 관점의 예상 질문과 대응 | reviewer_response_pack_ready_with_open_risks | open risks include human gold, mapping review, crosswalk utility, active-review effort, and overclaiming. | reviewer 답변도 final scores가 아니라 current gate status에 맞춰야 한다. | human/expert returns 이후 open risk IDs를 닫고 reviewer response를 갱신한다. |  |
| S13 | 13. EACL 제출 전 필수 체크리스트 | automatic_items_pass_human_items_pending | checklist items=20; proven automatic=11; human blocked=9 | minimum accept checklist is not complete until gold chunks/items/IAA/proposed scoring are complete. | 11 minimum paper-gate return files must be completed before final main table. | gold.completed_chunks;gold.item_count;gold.iaa;llm.proposed_human_gold_score |
| S14 | 14. 수정된 일정안 | timeline_action_board_ready_human_execution_pending | required claim return files=0/14; master return files=0/16 | schedule risk remains dominated by human annotation/adjudication and expert reviews. | first priority is annotator A/B batch returns, then adjudication, then APPLY_IMPORTS=1 refresh. |  |

## 계획서 13장 체크리스트 상태

| scope | id | status | completion_proven | human_blocked | proof_state | next_step |
| --- | --- | --- | --- | --- | --- | --- |
| minimum_accept | min.gold_chunks | pending_human | no | yes | human_required_not_complete | Complete two-annotator labeling and adjudication for at least 100 chunks. |
| minimum_accept | min.gold_items | pending_human | no | yes | human_required_not_complete | Adjudicate enough nodes, edges, and evidence anchors to reach 500 gold items. |
| minimum_accept | min.iaa | pending_human | no | yes | human_required_not_complete | Import completed annotator A/B files and recompute IAA. |
| minimum_accept | min.gold_sampling_ready | pass | yes | no | proven_for_current_automatic_stage | No additional automatic step required; priority-100 sampling covers 1371/1436 full-120 candidate edges (0.9547), active-review coverage=0.9670, high-impact coverage=1.0000. Human annotation/adjudication still required. |
| minimum_accept | min.baselines | pass | yes | no | proven_for_current_automatic_stage | No additional automatic step required; keep baseline artifacts synchronized. |
| minimum_accept | min.proposed | partial | no | yes | scaffold_ready_human_evidence_pending | Score P_cape_kg_actual against adjudicated human gold after gold completion. |
| minimum_accept | min.ablations | pass | yes | no | proven_for_current_automatic_stage | No additional automatic step required; ablation coverage satisfies the minimum gate. |
| minimum_accept | min.error_analysis | pass | yes | no | proven_for_current_automatic_stage | No additional automatic step required; update only if new diagnostics change. |
| minimum_accept | min.public_subset | pass | yes | no | proven_for_current_automatic_stage | No additional automatic step required; public subset evidence is present. |
| minimum_accept | min.release_plan | pass | yes | no | proven_for_current_automatic_stage | No additional automatic step required; regenerate only after source artifacts change. |
| minimum_accept | min.limitations | pass | yes | no | proven_for_current_automatic_stage | No additional automatic step required; keep limitations synchronized with future human results. |
| minimum_accept | min.public_synthetic_examples | pass | yes | no | proven_for_current_automatic_stage | No additional automatic step required; synthetic public-safe examples are ready. |
| strong_accept | strong.gold_chunks | pending_human | no | yes | human_required_not_complete | Use `strong_resegmented_342_max18` for optional 300+ two-annotator review and adjudication; do not claim 300+ adjudicated chunks until reviewed returns are imported. |
| strong_accept | strong.gold_items | pending_human | no | yes | human_required_not_complete | Complete optional 300+ two-annotator review and adjudication until at least 1,500 gold edge/evidence items are available. |
| strong_accept | strong.public_cross | pass | yes | no | proven_for_current_automatic_stage | No additional automatic step required; cross-check includes PAGED >= 100 and Text2KG >= 200 in a single run. |
| strong_accept | strong.edc_taxonomy_baselines | pass | yes | no | proven_for_current_automatic_stage | No additional automatic step required; B3/B4/B6 family baseline artifacts are present. |
| strong_accept | strong.mapping_downstream | partial | no | yes | scaffold_ready_human_evidence_pending | Complete expert review for mapping candidates and crosswalk candidates before making P@K/MRR/nDCG@10, explanation-quality, accept-rate, or utility claims. |
| strong_accept | strong.active_review | partial | no | yes | scaffold_ready_human_evidence_pending | Collect reviewed active-review human-effort CSV and validate efficiency against human adjudication outcomes. |
| strong_accept | strong.visualization | pass | yes | no | proven_for_current_automatic_stage | No additional automatic step required; keep the viewer synchronized with future graph updates. |
| method_modules | method.m1_m11 | partial | no | yes | scaffold_ready_human_evidence_pending | All executable module artifacts are present; human-review and human-gold scoring evidence remains required for final paper claims. |

## M1-M11 방법론 모듈 상태

| module | name | status | required_artifacts | missing_required | human_dependent | remaining_for_claim |
| --- | --- | --- | --- | --- | --- | --- |
| M1 | Document structure recovery | implemented_artifacts_present | 5 | 0 | False | No additional automatic step required; source-text release still requires rights review. |
| M2 | CQ generation and selection | implemented_artifacts_present | 7 | 0 | False | Human-gold CQ answerability must be recomputed after adjudication. |
| M3 | CQ-linked schema retrieval | implemented_artifacts_present_human_claim_pending | 8 | 0 | True | Final claim requires human-gold comparison of P vs. schema-retrieval ablation. |
| M4 | Procedural frame extraction | implemented_artifacts_present_human_claim_pending | 6 | 0 | True | Human review should verify task/step correctness before final claims. |
| M5 | Evidence-span constrained triple extraction | implemented_artifacts_present_human_claim_pending | 28 | 0 | True | Component-level span diagnostics are present; character/span exactness must still be validated against adjudicated human gold. |
| M6 | Span verifier | implemented_artifacts_present_human_claim_pending | 15 | 0 | True | Current verifier evidence is silver/proxy; human-gold evidence metrics are pending. |
| M7 | Ontology/SHACL validator | implemented_artifacts_present | 10 | 0 | False | No additional automatic step required; final conformance table should use human-gold predictions. |
| M8 | Procedural consistency validator | implemented_artifacts_present_human_claim_pending | 19 | 0 | True | Human-gold procedural consistency should be recomputed after adjudication. |
| M9 | Alias/canonicalization module | implemented_artifacts_present_human_claim_pending | 7 | 0 | True | Final node canonicalization quality requires human-gold node matching. |
| M10 | Active review queue | implemented_artifacts_present_human_claim_pending | 18 | 0 | True | Active-review ablation is represented with silver/proxy diagnostics; final efficiency claim requires human adjudication outcomes and reviewer effort/timing. |
| M11 | NCS/PCF mapping evaluator | implemented_artifacts_present_human_claim_pending | 13 | 0 | True | P@K/MRR/nDCG@10, explanation-quality, crosswalk accept-rate, and utility claims require completed expert review. |

## 아직 필요한 반환 파일

아래 파일이 들어와야 final main table과 human-gold/expert-review claim을 갱신할 수 있습니다.

| minimum | task | owner | batch_or_group | expected_rows | present | status | reviewed_file |
| --- | --- | --- | --- | --- | --- | --- | --- |
| yes | human_gold_annotation | annotator_A | full_120_priority_batch_001 | 20 | no | missing_reviewed_file | experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_001/annotator_A_full_120_priority_batch_001.reviewed.jsonl |
| yes | human_gold_annotation | annotator_B | full_120_priority_batch_001 | 20 | no | missing_reviewed_file | experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_001/annotator_B_full_120_priority_batch_001.reviewed.jsonl |
| yes | human_gold_annotation | annotator_A | full_120_priority_batch_002 | 20 | no | missing_reviewed_file | experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_002/annotator_A_full_120_priority_batch_002.reviewed.jsonl |
| yes | human_gold_annotation | annotator_B | full_120_priority_batch_002 | 20 | no | missing_reviewed_file | experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_002/annotator_B_full_120_priority_batch_002.reviewed.jsonl |
| yes | human_gold_annotation | annotator_A | full_120_priority_batch_003 | 20 | no | missing_reviewed_file | experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_003/annotator_A_full_120_priority_batch_003.reviewed.jsonl |
| yes | human_gold_annotation | annotator_B | full_120_priority_batch_003 | 20 | no | missing_reviewed_file | experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_003/annotator_B_full_120_priority_batch_003.reviewed.jsonl |
| yes | human_gold_annotation | annotator_A | full_120_priority_batch_004 | 20 | no | missing_reviewed_file | experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_004/annotator_A_full_120_priority_batch_004.reviewed.jsonl |
| yes | human_gold_annotation | annotator_B | full_120_priority_batch_004 | 20 | no | missing_reviewed_file | experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_004/annotator_B_full_120_priority_batch_004.reviewed.jsonl |
| yes | human_gold_annotation | annotator_A | full_120_priority_batch_005 | 20 | no | missing_reviewed_file | experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_005/annotator_A_full_120_priority_batch_005.reviewed.jsonl |
| yes | human_gold_annotation | annotator_B | full_120_priority_batch_005 | 20 | no | missing_reviewed_file | experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_005/annotator_B_full_120_priority_batch_005.reviewed.jsonl |
| yes | human_gold_adjudication | adjudicator | full_120_adjudication | 120 | no | missing_reviewed_file | experiments/cape_kg_eacl_20260627/01_data/gold_annotation/full_120/adjudication_edited.jsonl |
| no | mapping_expert_review | mapping_expert | top20_groups_top5_rows | 100 | no | missing_reviewed_file | experiments/cape_kg_eacl_20260627/01_data/mapping_review/mapping_review_items.reviewed.jsonl |
| no | crosswalk_expert_review | crosswalk_expert | ncs_pcf_crosswalk_candidates | 220 | no | missing_reviewed_file | experiments/cape_kg_eacl_20260627/01_data/crosswalk_review/crosswalk_review_items.reviewed.jsonl |
| no | active_review_human_effort | active_reviewer | pooled_active_uncertainty_random | 204 | no | missing_reviewed_file | experiments/cape_kg_eacl_20260627/05_review/active_review_human_effort.reviewed.csv |

## 사용 명령

사람 검수 반환 전 dry-run:

```bash
PYTHON_BIN=python3 LLM_PYTHON=python3 APPLY_IMPORTS=0 bash scripts/run_cape_human_return_apply.sh
```

사람 검수 반환 후 적용:

```bash
PYTHON_BIN=python3 LLM_PYTHON=python3 APPLY_IMPORTS=1 bash scripts/run_cape_human_return_apply.sh
```

최종 검증:

```bash
python3 scripts/validate_cape_pre_human_handoff.py --experiment-dir experiments/cape_kg_eacl_20260627 --outputs-dir outputs
sha256sum -c experiments/cape_kg_eacl_20260627/06_release/release_bundle_checksums.sha256
sha256sum -c experiments/cape_kg_eacl_20260627/06_release/human_review_handoff/human_review_handoff_checksums.sha256
```

## 산출 파일

- JSON: `experiments/cape_kg_eacl_20260627/06_release/revised_plan_section_status_ko.json`
- CSV: `experiments/cape_kg_eacl_20260627/06_release/revised_plan_section_status_ko.csv`
- Markdown: `experiments/cape_kg_eacl_20260627/06_release/revised_plan_section_status_ko.md`
