# CAPE-KG Submission Timeline Action Board

Generated: 2026-06-29T18:56:33.772865+00:00
As-of date: `2026-06-29`
Plan: `AX_EACL_submission_review_revised_plan.md`

이 문서는 revised EACL plan 14장의 공격적 EACL/ARR 제출 일정과 현재 gate 상태를 연결한 action board입니다.
제출 완료 선언이 아니라, 남은 minimum/strong gate와 날짜별 critical path를 추적하기 위한 release artifact입니다.

## Summary

| Item | Value |
| --- | --- |
| Overall status | PASS |
| Claim status | submission_timeline_action_board_ready_not_submission_complete |
| Safe to use as submission | False |
| Submission ready | False |
| ARR target date | 2026-08-03 |
| Days to ARR target | 35 |
| Pre-human validation | PASS |
| Pre-human checks | 92 |
| Claim gate | FAIL |
| Minimum return files | 0/11 |
| Optional/strong claim return files | 0/3 |
| Optional structural review files | 0/2 |
| All master return files | 0/16 |
| Human blockers | 8 |

## Strategy A Schedule Status

| phase | dates | status | blocking_gates | action_now |
| --- | --- | --- | --- | --- |
| A01_foundation_week | 2026-06-27~2026-07-03 | automatic_foundation_ready_pilot_human_pending | gold.completed_chunks<br>gold.iaa | Pilot/foundation 문서는 준비됨. 실제 pilot 또는 priority batch annotation 반환이 필요함. |
| A02_minimum_gold_and_core_runs | 2026-07-04~2026-07-12 | automatic_llm_runs_ready_minimum_gold_pending | gold.completed_chunks<br>gold.item_count<br>gold.iaa | Baseline/proposed generation은 준비됨. 11개 minimum human-return file이 critical path. |
| A03_main_scoring_and_metrics | 2026-07-13~2026-07-20 | scorers_ready_human_gold_refresh_pending | llm.proposed_human_gold_score | Human-gold import 후 scoring wrapper와 post-annotation refresh를 실행해야 main metric이 채워짐. |
| A04_ablation_analysis_writing | 2026-07-21~2026-07-27 | diagnostic_tables_ready_final_claim_refresh_pending | gold.completed_chunks<br>llm.proposed_human_gold_score | 현재 paper draft와 diagnostic tables는 준비됨. human-gold 결과가 들어오면 final result language로 갱신해야 함. |
| A05_internal_review_and_submission_package | 2026-07-28~2026-08-02 | release_package_ready_not_submission_complete | gold.completed_chunks<br>gold.item_count<br>gold.iaa<br>llm.proposed_human_gold_score | Release bundle은 준비되어 있으나 submission-ready gate는 human-gold 완료 전까지 false. |
| A06_arr_submission_target | 2026-08-03~2026-08-03 | not_submission_ready_until_minimum_gates_pass | gold.completed_chunks<br>gold.item_count<br>gold.iaa<br>llm.proposed_human_gold_score | 최소 human-gold gates와 proposed human-gold scoring이 PASS가 되기 전에는 제출 완료로 표시하지 않음. |

## Critical Path Actions

| id | workstream | due | D-day | priority | status | owner | next_action |
| --- | --- | --- | --- | --- | --- | --- | --- |
| CP01_minimum_annotation_returns | human_gold_annotation | 2026-07-12 | 13 | critical | pending_human | annotator_A_and_B | 10개 priority batch A/B reviewed JSONL을 exact filename으로 반환한다. |
| CP02_adjudication_return | human_gold_adjudication | 2026-07-13 | 14 | critical | pending_human | adjudicator | A/B annotation 반환 후 adjudication_edited.jsonl을 작성하고 import한다. |
| CP03_iaa_and_human_gold_scoring | human_gold_metrics | 2026-07-20 | 21 | critical | pending_human_returns | pipeline_after_returns | 검수 반환 import 후 IAA, node/edge/evidence/span metrics, P_cape_kg_actual scoring을 재계산한다. |
| CP04_claim_safe_main_tables | paper_tables | 2026-07-27 | 28 | critical | automatic_scaffold_ready_human_values_pending | paper_author | Human-gold metric이 채워진 뒤 silver/proxy diagnostic language를 final result language와 분리해 업데이트한다. |
| CP05_release_and_validation_freeze | submission_package | 2026-08-02 | 34 | critical | release_ready_not_submission_complete | pipeline | 최종 결과 반영 후 release bundle, checksum, protocol lock, pre-human/final validation을 다시 실행한다. |
| OP01_mapping_expert_review | mapping_downstream | 2026-07-27 | 28 | strong_optional | pending_expert_review | mapping_expert | Top-K NCS/PCF 후보를 expert review하고 P@K/MRR/nDCG/explanation quality를 재계산한다. |
| OP02_crosswalk_expert_review | ncs_pcf_crosswalk | 2026-07-27 | 28 | strong_optional | pending_expert_review | crosswalk_expert | Layer2-bridged NCS-PCF crosswalk 후보를 expert review하고 utility metrics를 재계산한다. |
| OP03_active_review_effort | active_review_efficiency | 2026-07-27 | 28 | strong_optional | pending_human_effort | active_review_effort_reviewer | active/uncertainty/random control effort sheet를 채워 review-efficiency claim을 검증한다. |
| OP04_structural_checkpoint_review | structural_review_checkpoint_candidates | 2026-07-27 | 28 | strong_optional | pending_structural_reviewer | structural_reviewer | ReviewCheckpoint 후보를 구조 검수자가 확인하고 structural review returns를 반영한다. |
| OP05_structural_gateway_branch_review | structural_gateway_branch_gaps | 2026-07-27 | 28 | strong_optional | pending_structural_reviewer | structural_reviewer | Gateway branch gap 후보를 확인해 procedural consistency 보강 여부를 결정한다. |

## Interpretation

- 자동 실험, baseline/ablation scaffolding, paper draft, release bundle은 pre-human 기준으로 준비되었습니다.
- ARR 2026-08-03 목표의 critical path는 2026-07-12까지 minimum annotation returns를 확보하고, 2026-07-20까지 human-gold scoring을 채우는 것입니다.
- Mapping/crosswalk expert review와 active-review human effort는 strong-accept claim을 위한 optional/strong path입니다.
- Optional structural review 2개 파일은 procedural structure 보강용이며, minimum human-gold gate나 strong mapping/active-review claim gate를 대체하지 않습니다.
- `safe_to_use_as_submission=false`와 `submission_ready=false`는 의도된 상태입니다. 최소 human-gold gate가 PASS가 되기 전에는 제출 완료로 표시하지 않습니다.
