# CAPE-KG 역할별 사람 검수 Quickstart

Generated: 2026-06-29T18:56:34.124054+00:00
Experiment: `experiments/cape_kg_eacl_20260627`

이 문서는 역할별로 지금 열 파일, 저장 파일, 반환 후 명령을 빠르게 확인하기 위한 내부 실행 카드입니다. 자세한 기준은 각 protocol/checklist를 따릅니다.

## 상태 요약

- Pre-human handoff: `PASS`
- Pre-human checks: 92
- Minimum return files: 0/11
- Required claim/human return files: 0/14
- Optional structural review files: 0/2
- All master return files: 0/16
- First batch: `full_120_priority_batch_001`
- Roles: 9

## 역할별 카드

### annotator_A

- Bundle: `experiments/cape_kg_eacl_20260627/06_release/human_review_handoff/cape_human_gold_annotator_A_priority100.tar.gz`
- Goal: priority 100 chunks 중 배정된 5개 batch를 독립 검수
- Start here: `experiments/cape_kg_eacl_20260627/05_review/human_review_first_batch_execution_card_ko.md`
- First required return: `experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_001/annotator_A_full_120_priority_batch_001.reviewed.jsonl`
- Claim note: A/B가 같은 100 chunks를 모두 완료하고 IAA/adjudication이 끝나기 전까지 human-gold claim 금지

Open files:
- `experiments/cape_kg_eacl_20260627/01_data/gold_annotation/annotation_workbench.html`
- `experiments/cape_kg_eacl_20260627/01_data/annotation_guideline_v1.md`
- `experiments/cape_kg_eacl_20260627/06_release/annotation_calibration_pack_ko.md`
- `experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_001/annotator_A_full_120_priority_batch_001.jsonl`

Save/return files:
- `experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_001/annotator_A_full_120_priority_batch_001.reviewed.jsonl`
- `experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_002/annotator_A_full_120_priority_batch_002.reviewed.jsonl`
- `experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_003/annotator_A_full_120_priority_batch_003.reviewed.jsonl`
- `experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_004/annotator_A_full_120_priority_batch_004.reviewed.jsonl`
- `experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_005/annotator_A_full_120_priority_batch_005.reviewed.jsonl`

Return rows:

| owner | task_type | batch_or_group | expected_rows | input_file | reviewed_file | present | status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| annotator_A | human_gold_annotation | full_120_priority_batch_001 | 20 | experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_001/annotator_A_full_120_priority_batch_001.jsonl | experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_001/annotator_A_full_120_priority_batch_001.reviewed.jsonl | no | missing_reviewed_file |
| annotator_A | human_gold_annotation | full_120_priority_batch_002 | 20 | experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_002/annotator_A_full_120_priority_batch_002.jsonl | experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_002/annotator_A_full_120_priority_batch_002.reviewed.jsonl | no | missing_reviewed_file |
| annotator_A | human_gold_annotation | full_120_priority_batch_003 | 20 | experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_003/annotator_A_full_120_priority_batch_003.jsonl | experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_003/annotator_A_full_120_priority_batch_003.reviewed.jsonl | no | missing_reviewed_file |
| annotator_A | human_gold_annotation | full_120_priority_batch_004 | 20 | experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_004/annotator_A_full_120_priority_batch_004.jsonl | experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_004/annotator_A_full_120_priority_batch_004.reviewed.jsonl | no | missing_reviewed_file |
| annotator_A | human_gold_annotation | full_120_priority_batch_005 | 20 | experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_005/annotator_A_full_120_priority_batch_005.jsonl | experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_005/annotator_A_full_120_priority_batch_005.reviewed.jsonl | no | missing_reviewed_file |

### annotator_B

- Bundle: `experiments/cape_kg_eacl_20260627/06_release/human_review_handoff/cape_human_gold_annotator_B_priority100.tar.gz`
- Goal: priority 100 chunks 중 배정된 5개 batch를 독립 검수
- Start here: `experiments/cape_kg_eacl_20260627/05_review/human_review_first_batch_execution_card_ko.md`
- First required return: `experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_001/annotator_B_full_120_priority_batch_001.reviewed.jsonl`
- Claim note: A/B가 같은 100 chunks를 모두 완료하고 IAA/adjudication이 끝나기 전까지 human-gold claim 금지

Open files:
- `experiments/cape_kg_eacl_20260627/01_data/gold_annotation/annotation_workbench.html`
- `experiments/cape_kg_eacl_20260627/01_data/annotation_guideline_v1.md`
- `experiments/cape_kg_eacl_20260627/06_release/annotation_calibration_pack_ko.md`
- `experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_001/annotator_B_full_120_priority_batch_001.jsonl`

Save/return files:
- `experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_001/annotator_B_full_120_priority_batch_001.reviewed.jsonl`
- `experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_002/annotator_B_full_120_priority_batch_002.reviewed.jsonl`
- `experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_003/annotator_B_full_120_priority_batch_003.reviewed.jsonl`
- `experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_004/annotator_B_full_120_priority_batch_004.reviewed.jsonl`
- `experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_005/annotator_B_full_120_priority_batch_005.reviewed.jsonl`

Return rows:

| owner | task_type | batch_or_group | expected_rows | input_file | reviewed_file | present | status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| annotator_B | human_gold_annotation | full_120_priority_batch_001 | 20 | experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_001/annotator_B_full_120_priority_batch_001.jsonl | experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_001/annotator_B_full_120_priority_batch_001.reviewed.jsonl | no | missing_reviewed_file |
| annotator_B | human_gold_annotation | full_120_priority_batch_002 | 20 | experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_002/annotator_B_full_120_priority_batch_002.jsonl | experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_002/annotator_B_full_120_priority_batch_002.reviewed.jsonl | no | missing_reviewed_file |
| annotator_B | human_gold_annotation | full_120_priority_batch_003 | 20 | experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_003/annotator_B_full_120_priority_batch_003.jsonl | experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_003/annotator_B_full_120_priority_batch_003.reviewed.jsonl | no | missing_reviewed_file |
| annotator_B | human_gold_annotation | full_120_priority_batch_004 | 20 | experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_004/annotator_B_full_120_priority_batch_004.jsonl | experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_004/annotator_B_full_120_priority_batch_004.reviewed.jsonl | no | missing_reviewed_file |
| annotator_B | human_gold_annotation | full_120_priority_batch_005 | 20 | experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_005/annotator_B_full_120_priority_batch_005.jsonl | experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_005/annotator_B_full_120_priority_batch_005.reviewed.jsonl | no | missing_reviewed_file |

### coordinator

- Bundle: `experiments/cape_kg_eacl_20260627/06_release/human_review_handoff/cape_human_gold_coordinator_priority100.tar.gz`
- Goal: 반환 파일 무결성 확인, preflight, dry-run/apply orchestration
- Start here: `experiments/cape_kg_eacl_20260627/06_release/human_review_start_here_ko.md`
- First required return: `experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_001/annotator_A_full_120_priority_batch_001.reviewed.jsonl`
- Claim note: checksum/preflight 통과는 claim evidence가 아니라 import safety evidence

Open files:
- `experiments/cape_kg_eacl_20260627/06_release/human_review_handoff/human_review_handoff_checksums.sha256`
- `experiments/cape_kg_eacl_20260627/06_release/human_review_status_dashboard_ko.md`
- `experiments/cape_kg_eacl_20260627/05_review/human_review_master_return_files.csv`
- `experiments/cape_kg_eacl_20260627/05_review/human_review_role_quickstart_cards_ko.md`

Save/return files:
- `experiments/cape_kg_eacl_20260627/06_release/human_review_return_preflight.md`
- `experiments/cape_kg_eacl_20260627/06_release/human_return_apply_last_run.md`
- `experiments/cape_kg_eacl_20260627/06_release/pre_human_handoff_validation.md`

### adjudicator

- Bundle: `experiments/cape_kg_eacl_20260627/06_release/human_review_handoff/cape_human_gold_adjudicator_full120.tar.gz`
- Goal: A/B disagreement를 adjudication하여 final human-gold 생성
- Start here: `experiments/cape_kg_eacl_20260627/01_data/gold_annotation/adjudication_protocol.md`
- First required return: `experiments/cape_kg_eacl_20260627/01_data/gold_annotation/full_120/adjudication_edited.jsonl`
- Claim note: adjudication_edited.jsonl import 전에는 proposed human-gold scoring claim 금지

Open files:
- `experiments/cape_kg_eacl_20260627/01_data/gold_annotation/full_120/adjudication_draft.jsonl`
- `experiments/cape_kg_eacl_20260627/01_data/gold_annotation/adjudication_protocol.md`

Save/return files:
- `experiments/cape_kg_eacl_20260627/01_data/gold_annotation/full_120/adjudication_edited.jsonl`

Return rows:

| owner | task_type | batch_or_group | expected_rows | input_file | reviewed_file | present | status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| adjudicator | human_gold_adjudication | full_120_adjudication | 120 | experiments/cape_kg_eacl_20260627/01_data/gold_annotation/full_120/adjudication_draft.jsonl | experiments/cape_kg_eacl_20260627/01_data/gold_annotation/full_120/adjudication_edited.jsonl | no | missing_reviewed_file |

### mapping_expert

- Bundle: `experiments/cape_kg_eacl_20260627/06_release/human_review_handoff/cape_mapping_expert_review_top20_groups.tar.gz`
- Goal: NCS/PCF mapping top20 priority groups의 top-5 후보 검수
- Start here: `experiments/cape_kg_eacl_20260627/01_data/mapping_review/mapping_review_protocol.md`
- First required return: `experiments/cape_kg_eacl_20260627/01_data/mapping_review/mapping_review_items.reviewed.jsonl`
- Claim note: expert-reviewed file import 전에는 mapping P@K/MRR/nDCG claim 금지

Open files:
- `experiments/cape_kg_eacl_20260627/01_data/mapping_review/mapping_review_items.jsonl`
- `experiments/cape_kg_eacl_20260627/05_review/mapping_review_next_20_groups.csv`

Save/return files:
- `experiments/cape_kg_eacl_20260627/01_data/mapping_review/mapping_review_items.reviewed.jsonl`

Return rows:

| owner | task_type | batch_or_group | expected_rows | input_file | reviewed_file | present | status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| mapping_expert | mapping_expert_review | top20_groups_top5_rows | 100 | experiments/cape_kg_eacl_20260627/01_data/mapping_review/mapping_review_items.jsonl | experiments/cape_kg_eacl_20260627/01_data/mapping_review/mapping_review_items.reviewed.jsonl | no | missing_reviewed_file |

### crosswalk_expert

- Bundle: `experiments/cape_kg_eacl_20260627/06_release/human_review_handoff/cape_crosswalk_expert_review_ncs_pcf.tar.gz`
- Goal: NCS-PCF crosswalk 후보 220 rows의 utility/ranking 검수
- Start here: `experiments/cape_kg_eacl_20260627/01_data/crosswalk_review/crosswalk_review_protocol.md`
- First required return: `experiments/cape_kg_eacl_20260627/01_data/crosswalk_review/crosswalk_review_items.reviewed.jsonl`
- Claim note: expert-reviewed file import 전에는 crosswalk accept-rate/utility claim 금지

Open files:
- `experiments/cape_kg_eacl_20260627/01_data/crosswalk_review/crosswalk_review_items.jsonl`
- `experiments/cape_kg_eacl_20260627/01_data/crosswalk_review/crosswalk_review_sheet.csv`

Save/return files:
- `experiments/cape_kg_eacl_20260627/01_data/crosswalk_review/crosswalk_review_items.reviewed.jsonl`

Return rows:

| owner | task_type | batch_or_group | expected_rows | input_file | reviewed_file | present | status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| crosswalk_expert | crosswalk_expert_review | ncs_pcf_crosswalk_candidates | 220 | experiments/cape_kg_eacl_20260627/01_data/crosswalk_review/crosswalk_review_items.jsonl | experiments/cape_kg_eacl_20260627/01_data/crosswalk_review/crosswalk_review_items.reviewed.jsonl | no | missing_reviewed_file |

### active_reviewer

- Bundle: `experiments/cape_kg_eacl_20260627/06_release/human_review_handoff/cape_active_review_human_effort.tar.gz`
- Goal: active/random review effort와 timing 기록
- Start here: `experiments/cape_kg_eacl_20260627/06_release/active_review_human_effort_briefing.md`
- First required return: `experiments/cape_kg_eacl_20260627/05_review/active_review_human_effort.reviewed.csv`
- Claim note: review_seconds/corrected_error 없는 상태에서는 active-review efficiency claim 금지

Open files:
- `experiments/cape_kg_eacl_20260627/05_review/active_review_human_effort_template.csv`
- `experiments/cape_kg_eacl_20260627/05_review/actual_llm_active_review_queue_P_cape_kg_actual.csv`

Save/return files:
- `experiments/cape_kg_eacl_20260627/05_review/active_review_human_effort.reviewed.csv`

Return rows:

| owner | task_type | batch_or_group | expected_rows | input_file | reviewed_file | present | status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| active_reviewer | active_review_human_effort | pooled_active_uncertainty_random | 204 | experiments/cape_kg_eacl_20260627/05_review/active_review_human_effort_template.csv | experiments/cape_kg_eacl_20260627/05_review/active_review_human_effort.reviewed.csv | no | missing_reviewed_file |

### structural_reviewer

- Bundle: `experiments/cape_kg_eacl_20260627/06_release/human_review_handoff/cape_structural_review_optional.tar.gz`
- Goal: optional structural gap/checkpoint 후보 검수
- Start here: `experiments/cape_kg_eacl_20260627/06_release/structural_review_action_plan.md`
- First required return: `experiments/cape_kg_eacl_20260627/05_review/structural_review_checkpoint_candidates.reviewed.csv`
- Claim note: 선택 구조 검수이며 minimum paper gate의 대체 evidence가 아님

Open files:
- `experiments/cape_kg_eacl_20260627/05_review/structural_review_checkpoint_candidates.csv`
- `experiments/cape_kg_eacl_20260627/05_review/structural_gateway_branch_gaps.csv`

Save/return files:
- `experiments/cape_kg_eacl_20260627/05_review/structural_review_checkpoint_candidates.reviewed.csv`
- `experiments/cape_kg_eacl_20260627/05_review/structural_gateway_branch_gaps.reviewed.csv`

Return rows:

| owner | task_type | batch_or_group | expected_rows | input_file | reviewed_file | present | status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| structural_reviewer | structural_review_checkpoint_candidates |  | 45 | experiments/cape_kg_eacl_20260627/05_review/structural_review_checkpoint_candidates.csv | experiments/cape_kg_eacl_20260627/05_review/structural_review_checkpoint_candidates.reviewed.csv | no | ready_for_optional_review |
| structural_reviewer | structural_gateway_branch_gaps |  | 4 | experiments/cape_kg_eacl_20260627/05_review/structural_gateway_branch_gaps.csv | experiments/cape_kg_eacl_20260627/05_review/structural_gateway_branch_gaps.reviewed.csv | no | ready_for_optional_review |

### strong_resegmented_review

- Bundle: `experiments/cape_kg_eacl_20260627/06_release/human_review_handoff/cape_human_gold_strong_resegmented_342.tar.gz`
- Goal: optional 342 resegmented review units의 strong setting 검수
- Start here: `experiments/cape_kg_eacl_20260627/06_release/human_review_handoff/README_strong_resegmented_review_ko.md`
- First required return: `experiments/cape_kg_eacl_20260627/01_data/gold_annotation/strong_resegmented_342_max18/annotator_A_edited.jsonl`
- Claim note: strong 300+ claim은 optional이며 A/B/adjudication 완료 후에만 가능

Open files:
- `experiments/cape_kg_eacl_20260627/01_data/gold_annotation/strong_resegmented_342_max18/annotator_A.jsonl`
- `experiments/cape_kg_eacl_20260627/01_data/gold_annotation/strong_resegmented_342_max18/annotator_B.jsonl`
- `experiments/cape_kg_eacl_20260627/01_data/gold_annotation/strong_resegmented_342_max18/tracking_sheet.csv`

Save/return files:
- `experiments/cape_kg_eacl_20260627/01_data/gold_annotation/strong_resegmented_342_max18/annotator_A_edited.jsonl`
- `experiments/cape_kg_eacl_20260627/01_data/gold_annotation/strong_resegmented_342_max18/annotator_B_edited.jsonl`
- `experiments/cape_kg_eacl_20260627/01_data/gold_annotation/strong_resegmented_342_max18/adjudication_edited.jsonl`

## 공통 명령

### verify_handoff_checksums

```bash
sha256sum -c experiments/cape_kg_eacl_20260627/06_release/human_review_handoff/human_review_handoff_checksums.sha256
```

### validate_required_returns

```bash
python3 scripts/validate_cape_human_review_returns.py --experiment-dir experiments/cape_kg_eacl_20260627
```

### validate_strong_returns

```bash
python3 scripts/validate_cape_strong_review_returns.py --experiment-dir experiments/cape_kg_eacl_20260627
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

## Source Files

| path | exists | bytes |
| --- | --- | --- |
| experiments/cape_kg_eacl_20260627/06_release/human_review_handoff/human_review_handoff_manifest.json | True | 16713 |
| experiments/cape_kg_eacl_20260627/05_review/human_review_master_return_files.csv | True | 8192 |
| experiments/cape_kg_eacl_20260627/06_release/human_review_status_dashboard_ko.json | True | 36382 |
| experiments/cape_kg_eacl_20260627/05_review/human_review_first_batch_execution_card.json | True | 10518 |
| experiments/cape_kg_eacl_20260627/05_review/structural_review_optional_returns.csv | True | 1019 |

## Output Files

- Markdown: `experiments/cape_kg_eacl_20260627/05_review/human_review_role_quickstart_cards_ko.md`
- JSON: `experiments/cape_kg_eacl_20260627/05_review/human_review_role_quickstart_cards.json`
- CSV: `experiments/cape_kg_eacl_20260627/05_review/human_review_role_quickstart_cards.csv`
