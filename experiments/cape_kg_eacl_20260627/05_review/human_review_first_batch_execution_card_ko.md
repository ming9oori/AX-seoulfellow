# CAPE-KG 첫 배치 검수 실행 카드

Generated: 2026-06-29T18:56:34.087406+00:00
Experiment: `experiments/cape_kg_eacl_20260627`
Batch: `full_120_priority_batch_001`

이 문서는 전체 체크리스트가 아니라, human-gold 검수를 실제로 시작할 때 첫 20개 chunk 배치에서 열 파일과 저장 파일을 바로 확인하기 위한 내부 실행 카드입니다.

## 현재 상태

- Claim gate: `FAIL`
- Required claim-gate failures: 4
- Human-return preflight: `pending_human_returns`
- Minimum paper gate ready after preflight: False
- Apply scope: `no_return_files`

## 첫 배치 규모

- Chunk count: 20
- Candidate edges: 811
- Active-review items: 41
- High-impact chunks: 7

## Priority-100 안에서 첫 배치의 의미

| item | value |
|---|---:|
| Priority-100 selected chunks | 100/100 |
| Priority-100 candidate edges | 1371 |
| First-batch candidate edges | 811 |
| First-batch share of priority candidate edges | 0.591539 |
| Full-120 candidate-edge coverage | 0.954735 |
| Active-review coverage | 0.967033 |
| High-impact coverage | 1.000000 |
| Claim status | `gold_sampling_coverage_ready_pending_human_review` |

첫 배치는 priority-100 중에서도 candidate edge가 가장 많은 구간입니다. 이 수치는 검수 우선순위 설명용이며 human-gold 성능 증거가 아닙니다.

## Annotator별 입력/저장 파일

| owner | batch_or_group | expected_rows | input_file | reviewed_file | present | status |
| --- | --- | --- | --- | --- | --- | --- |
| annotator_A | full_120_priority_batch_001 | 20 | experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_001/annotator_A_full_120_priority_batch_001.jsonl | experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_001/annotator_A_full_120_priority_batch_001.reviewed.jsonl | no | missing_reviewed_file |
| annotator_B | full_120_priority_batch_001 | 20 | experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_001/annotator_B_full_120_priority_batch_001.jsonl | experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_001/annotator_B_full_120_priority_batch_001.reviewed.jsonl | no | missing_reviewed_file |

## 공통으로 열 파일

| 역할 | 존재 | bytes | 경로 |
|---|---:|---:|---|
| workbench | True | 28252 | `experiments/cape_kg_eacl_20260627/01_data/gold_annotation/annotation_workbench.html` |
| annotation_guideline | True | 12652 | `experiments/cape_kg_eacl_20260627/01_data/annotation_guideline_v1.md` |
| annotation_schema | True | 741 | `experiments/cape_kg_eacl_20260627/01_data/gold_annotation/annotation_schema.json` |
| adjudication_protocol | True | 10196 | `experiments/cape_kg_eacl_20260627/01_data/gold_annotation/adjudication_protocol.md` |
| calibration_pack | True | 7970 | `experiments/cape_kg_eacl_20260627/06_release/annotation_calibration_pack_ko.md` |
| batch_readme | True | 4242 | `experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_001/README.md` |
| batch_preview_md | True | 4287 | `experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_001/batch_review_preview.md` |
| batch_preview_csv | True | 4065 | `experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_001/batch_review_preview.csv` |
| batch_tracking_sheet | True | 4628 | `experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_001/batch_tracking_sheet.csv` |
| master_return_files | True | 8192 | `experiments/cape_kg_eacl_20260627/05_review/human_review_master_return_files.csv` |
| status_dashboard | True | 12146 | `experiments/cape_kg_eacl_20260627/06_release/human_review_status_dashboard_ko.md` |
| launch_checklist | True | 12049 | `experiments/cape_kg_eacl_20260627/06_release/human_review_launch_checklist_ko.md` |

## 검수 규칙

- Input JSONL은 덮어쓰지 않고 reviewed_file 경로에 새로 저장합니다.
- A/B annotator는 서로 결과를 보지 않고 독립적으로 검수합니다.
- 각 JSONL row는 한 줄에 하나의 JSON object 형식을 유지합니다.
- accepted edge에는 evidence anchor 또는 exact span을 남깁니다.
- 첫 배치 20 chunks만으로 human-gold 최종 성능 claim을 하지 않습니다.
- 최소 논문 gate는 5개 batch A/B 10개 reviewed 파일과 adjudication reviewed 파일까지 필요합니다.

## 반환 후 확인 명령

반환 파일을 받으면 아래 순서로 확인합니다. `APPLY_IMPORTS=1`은 reviewed 파일들이 실제로 준비된 뒤에만 실행합니다.

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

## 논문 claim 주의

- 첫 배치 `full_120_priority_batch_001`은 20 chunks만 다룹니다.
- A/B 둘 다 반환되어도 이 배치 하나만으로는 100 chunk IAA, adjudication, proposed human-gold scoring이 완료되지 않습니다.
- 교수님께 보고할 때는 현재 상태를 `검수 시작 준비 완료, 사람 검수 반환 대기`로 표현해야 합니다.
