# CAPE-KG 사람 검수 상태 대시보드

Generated: 2026-06-29T19:08:44.580373+00:00
Experiment: `experiments/cape_kg_eacl_20260627`

이 문서는 긴 체크리스트를 대체하지 않고, 현재 human gate 진행 상태와 다음에 열 파일만 빠르게 보기 위한 상태판입니다.

## 현재 결론

- Claim gate: `FAIL`
- Required claim-gate failures: 4
- Optional claim-gate failures: 2
- Pre-human validation source: `experiments/cape_kg_eacl_20260627/06_release/pre_human_handoff_validation.md`
- Latest release stamp: `return_preflight_sync02_20260629`
- Latest internal bundle: `experiments/cape_kg_eacl_20260627/06_release/bundles/cape_kg_eacl_internal_repro_return_preflight_sync02_20260629.tar.gz`
- Latest internal SHA256: `cfa7764221cbc9aae54c0833d0a74740f46b676bb86f5aa925ab8e533aa3c4b0`
- Latest public-safe bundle: `experiments/cape_kg_eacl_20260627/06_release/bundles/cape_kg_eacl_public_safe_skeleton_return_preflight_sync02_20260629.tar.gz`
- Latest public-safe SHA256: `92045dee721c3da3ce3caefa92a8b0c7aead9cbff86459ce3e2fc56d54b2df0a`
- Minimum paper-gate return files: 0/11
- Optional/strong claim return files: 0/3
- Required claim/human return files: 0/14
- Optional structural review files: 0/2
- All master return files: 0/16
- 현재 완료 판단: `not_complete_pending_human_gold_iaa_adjudication_and_expert_review`

## Priority-100 선정 근거

| item | value |
| --- | ---: |
| Selected chunks | 100/100 |
| Batch count / size | 5 / 20 |
| Candidate edges covered | 1371/1436 |
| Candidate-edge coverage | 0.954735 |
| Active-review chunk coverage | 0.967033 |
| High-impact chunk coverage | 1.000000 |
| Claim status | `gold_sampling_coverage_ready_pending_human_review` |
| Report | `experiments/cape_kg_eacl_20260627/06_release/gold_sampling_coverage_report.md` |

이 선정 근거는 사람 검수 우선순위와 coverage를 설명하는 운영 근거입니다. human-gold 결과나 성능 claim은 아닙니다.

## 진행 상태

| id | label | done | target | percent | status | next |
| --- | --- | --- | --- | --- | --- | --- |
| required_returns | Minimum paper-gate return files | 0 | 11 | 0.0% | pending_human_returns | annotation/adjudication reviewed file 11개를 정확한 filename으로 저장 |
| annotation_reviewed_files | A/B annotation reviewed files | 0 | 10 | 0.0% | pending_two_annotator_returns | priority batch 001-005를 annotator A/B가 독립 검수 |
| paired_iaa_chunks | IAA paired chunks | 0 | 100 | 0.0% | pending_iaa | A/B reviewed JSONL import 후 IAA 재계산 |
| adjudicated_chunks | Adjudicated gold chunks | 0 | 100 | 0.0% | pending_adjudication | adjudication_edited.jsonl 완료 및 import |
| gold_items | Gold node/edge/evidence items | 0 | 500 | 0.0% | pending_human_gold_items | adjudicated node/edge/evidence item 500개 이상 확보 |
| mapping_priority_groups | Mapping expert priority groups | 0 | 20 | 0.0% | pending_mapping_expert_review | top20 source-task-standard group의 Top-5 후보 검수 |
| crosswalk_source_groups | NCS-PCF crosswalk source groups | 0 | 22 | 0.0% | pending_crosswalk_expert_review | NCS-PCF crosswalk 후보 pair utility 검수 |
| active_review_effort_rows | Active-review effort rows | 0 | 204 | 0.0% | pending_human_effort_timing | review_seconds, decision, corrected_error 열 채우기 |

## 즉시 열 파일

- 첫 배치 간편 실행 카드: `experiments/cape_kg_eacl_20260627/05_review/human_review_first_batch_execution_card_ko.md`
- 역할별 quickstart: `experiments/cape_kg_eacl_20260627/05_review/human_review_role_quickstart_cards_ko.md`

가장 먼저 진행할 annotation batch는 `full_120_priority_batch_001`입니다.

| owner | batch_or_group | expected_rows | input_file | reviewed_file | present | status |
| --- | --- | --- | --- | --- | --- | --- |
| annotator_A | full_120_priority_batch_001 | 20 | experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_001/annotator_A_full_120_priority_batch_001.jsonl | experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_001/annotator_A_full_120_priority_batch_001.reviewed.jsonl | no | missing_reviewed_file |
| annotator_B | full_120_priority_batch_001 | 20 | experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_001/annotator_B_full_120_priority_batch_001.jsonl | experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_001/annotator_B_full_120_priority_batch_001.reviewed.jsonl | no | missing_reviewed_file |

Mapping expert는 아래 우선순위 group부터 검수합니다.

| priority_score | standard | source_label | pending_top5_rows | top_score | score_gap |
| --- | --- | --- | --- | --- | --- |
| 0.9564 | PCF | PT 전략 개발 | 5 | 0.311 | 0.0109 |
| 0.9364 | PCF | 경쟁사 분석 | 5 | 0.4117 | 0.0159 |
| 0.9308 | NCS | 목차 개발 | 5 | 0.2208 | 0.0008 |
| 0.926467 | PCF | 제안서 작성 | 5 | 0.2612 | 0.0103 |
| 0.91685 | NCS | 제안전략 개발 | 5 | 0.2127 | 0.0026 |

## 다음 행동 CSV

- CSV: `experiments/cape_kg_eacl_20260627/05_review/human_review_status_next_actions.csv`

| priority | actor | objective | open_file | save_as | unlocks |
| --- | --- | --- | --- | --- | --- |
| 1 | coordinator | handoff bundle이 손상되지 않았는지 확인 | experiments/cape_kg_eacl_20260627/06_release/human_review_handoff/human_review_handoff_checksums.sha256 |  | review package distribution |
| 2 | annotator_A | priority batch 001 독립 annotation | experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_001/annotator_A_full_120_priority_batch_001.jsonl | experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_001/annotator_A_full_120_priority_batch_001.reviewed.jsonl | first 20 paired chunks for IAA after both annotators return |
| 3 | annotator_B | priority batch 001 독립 annotation | experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_001/annotator_B_full_120_priority_batch_001.jsonl | experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_001/annotator_B_full_120_priority_batch_001.reviewed.jsonl | first 20 paired chunks for IAA after both annotators return |
| 4 | coordinator | 반환 파일 preflight | experiments/cape_kg_eacl_20260627/05_review/human_review_master_return_files.csv | experiments/cape_kg_eacl_20260627/06_release/human_review_return_preflight.md | safe dry-run/import decision |
| 5 | coordinator | 사람 반환 파일 dry-run 반영 |  | experiments/cape_kg_eacl_20260627/06_release/human_return_apply_last_run.md | apply readiness check |
| 6 | adjudicator | A/B disagreement adjudication | experiments/cape_kg_eacl_20260627/01_data/gold_annotation/full_120/adjudication_draft.jsonl | experiments/cape_kg_eacl_20260627/01_data/gold_annotation/full_120/adjudication_edited.jsonl | 100+ adjudicated chunks, 500+ gold items, proposed human-gold scoring |
| 7 | mapping_expert | NCS/PCF top20 priority group expert review | experiments/cape_kg_eacl_20260627/01_data/mapping_review/mapping_review_items.jsonl | experiments/cape_kg_eacl_20260627/01_data/mapping_review/mapping_review_items.reviewed.jsonl | mapping P@K/MRR/nDCG/expert accept-rate claim |
| 8 | crosswalk_expert | NCS-PCF crosswalk 후보 utility 검수 | experiments/cape_kg_eacl_20260627/01_data/crosswalk_review/crosswalk_review_items.jsonl | experiments/cape_kg_eacl_20260627/01_data/crosswalk_review/crosswalk_review_items.reviewed.jsonl | NCS-PCF crosswalk accept-rate/utility/ranking claim |
| 9 | active_reviewer | active-review effort/timing 기록 | experiments/cape_kg_eacl_20260627/05_review/active_review_human_effort_template.csv | experiments/cape_kg_eacl_20260627/05_review/active_review_human_effort.reviewed.csv | active review efficiency claim |

## 다음 명령

### verify_handoff_checksums

```bash
sha256sum -c experiments/cape_kg_eacl_20260627/06_release/human_review_handoff/human_review_handoff_checksums.sha256
```

### validate_required_returns

```bash
python3 scripts/validate_cape_human_review_returns.py --experiment-dir experiments/cape_kg_eacl_20260627
```

### dry_run_human_return_apply

```bash
PYTHON_BIN=python3 LLM_PYTHON=python3 APPLY_IMPORTS=0 bash scripts/run_cape_human_return_apply.sh
```

### apply_human_returns

```bash
PYTHON_BIN=python3 LLM_PYTHON=python3 APPLY_IMPORTS=1 bash scripts/run_cape_human_return_apply.sh
```

### validate_pre_human_handoff

```bash
python3 scripts/validate_cape_pre_human_handoff.py --experiment-dir experiments/cape_kg_eacl_20260627 --outputs-dir outputs
```

### verify_release_checksums

```bash
sha256sum -c experiments/cape_kg_eacl_20260627/06_release/release_bundle_checksums.sha256
```

## 아직 claim하면 안 되는 것

- CAPE-KG가 baseline보다 human-gold 기준으로 우수하다는 최종 성능 claim
- NCS/PCF mapping P@K, MRR, nDCG, expert accept-rate claim
- NCS-PCF crosswalk accept-rate, utility, ranking claim
- active-review efficiency가 사람 검수 비용을 줄였다는 최종 claim
- strong_resegmented_342_max18이 342개 adjudicated gold chunk로 완료되었다는 claim

## Source Files

| path | exists | bytes |
| --- | --- | --- |
| experiments/cape_kg_eacl_20260627/06_release/claim_gate_report.json | True | 16096 |
| experiments/cape_kg_eacl_20260627/06_release/human_review_return_preflight.json | True | 11795 |
| experiments/cape_kg_eacl_20260627/06_release/human_review_master_checklist_ko.json | True | 38205 |
| experiments/cape_kg_eacl_20260627/06_release/human_gate_action_plan.json | True | 117002 |
| experiments/cape_kg_eacl_20260627/05_review/human_review_first_batch_execution_card_ko.md | True | 5593 |
| experiments/cape_kg_eacl_20260627/05_review/human_review_first_batch_execution_card.json | True | 10518 |
| experiments/cape_kg_eacl_20260627/05_review/human_review_role_quickstart_cards_ko.md | True | 19591 |
| experiments/cape_kg_eacl_20260627/05_review/human_review_role_quickstart_cards.json | True | 28002 |
| experiments/cape_kg_eacl_20260627/05_review/human_review_role_quickstart_cards.csv | True | 4609 |
| experiments/cape_kg_eacl_20260627/05_review/human_review_master_return_files.csv | True | 8192 |
| experiments/cape_kg_eacl_20260627/06_release/gold_sampling_coverage_report.json | True | 67903 |
| experiments/cape_kg_eacl_20260627/05_review/gold_sampling_priority100_selected_chunks.csv | True | 12535 |
| experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_batch_assignment_overview.csv | True | 4333 |
| experiments/cape_kg_eacl_20260627/05_review/mapping_review_next_20_groups.csv | True | 4320 |
| experiments/cape_kg_eacl_20260627/01_data/mapping_review/mapping_review_items.jsonl | True | 205773 |
| experiments/cape_kg_eacl_20260627/01_data/crosswalk_review/crosswalk_review_items.jsonl | True | 241950 |
| experiments/cape_kg_eacl_20260627/01_data/crosswalk_review/crosswalk_review_protocol.md | True | 1754 |
| experiments/cape_kg_eacl_20260627/05_review/active_review_human_effort_template.csv | True | 47175 |
| experiments/cape_kg_eacl_20260627/06_release/latest_release_bundle_index.json | True | 5107 |
| experiments/cape_kg_eacl_20260627/06_release/release_bundle_manifest.json | True | 37348 |

## Output Files

- JSON: `experiments/cape_kg_eacl_20260627/06_release/human_review_status_dashboard_ko.json`
- Markdown: `experiments/cape_kg_eacl_20260627/06_release/human_review_status_dashboard_ko.md`
- Next actions CSV: `experiments/cape_kg_eacl_20260627/05_review/human_review_status_next_actions.csv`
- First batch card: `experiments/cape_kg_eacl_20260627/05_review/human_review_first_batch_execution_card_ko.md`
- First batch card JSON: `experiments/cape_kg_eacl_20260627/05_review/human_review_first_batch_execution_card.json`
- Role quickstart: `experiments/cape_kg_eacl_20260627/05_review/human_review_role_quickstart_cards_ko.md`
- Role quickstart JSON: `experiments/cape_kg_eacl_20260627/05_review/human_review_role_quickstart_cards.json`
- Role quickstart CSV: `experiments/cape_kg_eacl_20260627/05_review/human_review_role_quickstart_cards.csv`
