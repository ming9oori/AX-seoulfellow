# CAPE-KG Human Review Coordinator Handoff

이 bundle은 annotator A/B 결과를 import하고 IAA/adjudication을 진행하기 위한 내부 coordinator용 자료다.

## Minimum Gate

- two annotators completed: 100 chunks
- adjudicated human-gold chunks: 100+
- adjudicated node/edge/evidence items: 500+
- IAA report computed
- `P_cape_kg_actual` scored against adjudicated gold

## Core Guidance Files

- Annotation guideline: `experiments/cape_kg_eacl_20260627/01_data/annotation_guideline_v1.md`
- Adjudication protocol: `experiments/cape_kg_eacl_20260627/01_data/gold_annotation/adjudication_protocol.md`
- Calibration pack: `experiments/cape_kg_eacl_20260627/06_release/annotation_calibration_pack_ko.md`
- Return field guide: `experiments/cape_kg_eacl_20260627/06_release/annotation_return_field_guide_ko.md`
- Validation error playbook: `experiments/cape_kg_eacl_20260627/06_release/human_return_validation_error_playbook_ko.md`
- Start-here guide: `experiments/cape_kg_eacl_20260627/06_release/human_review_start_here_ko.md`
- Master checklist: `experiments/cape_kg_eacl_20260627/06_release/human_review_master_checklist_ko.md`
- First batch execution card: `experiments/cape_kg_eacl_20260627/05_review/human_review_first_batch_execution_card_ko.md`
- Role quickstart: `experiments/cape_kg_eacl_20260627/05_review/human_review_role_quickstart_cards_ko.md`
- Status dashboard: `experiments/cape_kg_eacl_20260627/06_release/human_review_status_dashboard_ko.md`
- Launch checklist: `experiments/cape_kg_eacl_20260627/06_release/human_review_launch_checklist_ko.md`
- Batch review preview summary: `experiments/cape_kg_eacl_20260627/06_release/annotation_batch_review_preview_summary.md`

## Recommended Return Preflight and Wrapper

반환 파일을 받으면 먼저 전체 preflight를 실행한다:

```bash
python3 scripts/validate_cape_human_review_returns.py \
  --experiment-dir experiments/cape_kg_eacl_20260627
```

preflight에서 validation error가 없으면 안전 wrapper로 dry-run refresh를 먼저 실행한다:

```bash
PYTHON_BIN=python3 \
LLM_PYTHON=python3 \
APPLY_IMPORTS=0 \
bash scripts/run_cape_human_return_apply.sh
```

dry-run과 preflight가 모두 통과하면 반환 파일을 실제 반영한다:

```bash
PYTHON_BIN=python3 \
LLM_PYTHON=python3 \
APPLY_IMPORTS=1 \
bash scripts/run_cape_human_return_apply.sh
```

`APPLY_IMPORTS=1`은 reviewed return file이 없으면 기본적으로 거부된다.

## Low-Level Debug Batch Import Commands

아래 batch별 명령은 특정 reviewed file 문제를 디버깅할 때만 사용한다. 운영 반영은 위 wrapper를 기본 경로로 사용한다.

### full_120_priority_batch_001

Annotator A single-file dry run:

```bash
python3 scripts/import_cape_gold_annotation.py --experiment-dir experiments/cape_kg_eacl_20260627 --target-file experiments/cape_kg_eacl_20260627/01_data/gold_annotation/full_120/annotator_A.jsonl --reviewed-file experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_001/annotator_A_full_120_priority_batch_001.reviewed.jsonl --allow-partial
```

Annotator A single-file apply for debugging only:

```bash
python3 scripts/import_cape_gold_annotation.py --experiment-dir experiments/cape_kg_eacl_20260627 --target-file experiments/cape_kg_eacl_20260627/01_data/gold_annotation/full_120/annotator_A.jsonl --reviewed-file experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_001/annotator_A_full_120_priority_batch_001.reviewed.jsonl --allow-partial --apply
```

Annotator B single-file dry run:

```bash
python3 scripts/import_cape_gold_annotation.py --experiment-dir experiments/cape_kg_eacl_20260627 --target-file experiments/cape_kg_eacl_20260627/01_data/gold_annotation/full_120/annotator_B.jsonl --reviewed-file experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_001/annotator_B_full_120_priority_batch_001.reviewed.jsonl --allow-partial
```

Annotator B single-file apply for debugging only:

```bash
python3 scripts/import_cape_gold_annotation.py --experiment-dir experiments/cape_kg_eacl_20260627 --target-file experiments/cape_kg_eacl_20260627/01_data/gold_annotation/full_120/annotator_B.jsonl --reviewed-file experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_001/annotator_B_full_120_priority_batch_001.reviewed.jsonl --allow-partial --apply
```

### full_120_priority_batch_002

Annotator A single-file dry run:

```bash
python3 scripts/import_cape_gold_annotation.py --experiment-dir experiments/cape_kg_eacl_20260627 --target-file experiments/cape_kg_eacl_20260627/01_data/gold_annotation/full_120/annotator_A.jsonl --reviewed-file experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_002/annotator_A_full_120_priority_batch_002.reviewed.jsonl --allow-partial
```

Annotator A single-file apply for debugging only:

```bash
python3 scripts/import_cape_gold_annotation.py --experiment-dir experiments/cape_kg_eacl_20260627 --target-file experiments/cape_kg_eacl_20260627/01_data/gold_annotation/full_120/annotator_A.jsonl --reviewed-file experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_002/annotator_A_full_120_priority_batch_002.reviewed.jsonl --allow-partial --apply
```

Annotator B single-file dry run:

```bash
python3 scripts/import_cape_gold_annotation.py --experiment-dir experiments/cape_kg_eacl_20260627 --target-file experiments/cape_kg_eacl_20260627/01_data/gold_annotation/full_120/annotator_B.jsonl --reviewed-file experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_002/annotator_B_full_120_priority_batch_002.reviewed.jsonl --allow-partial
```

Annotator B single-file apply for debugging only:

```bash
python3 scripts/import_cape_gold_annotation.py --experiment-dir experiments/cape_kg_eacl_20260627 --target-file experiments/cape_kg_eacl_20260627/01_data/gold_annotation/full_120/annotator_B.jsonl --reviewed-file experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_002/annotator_B_full_120_priority_batch_002.reviewed.jsonl --allow-partial --apply
```

### full_120_priority_batch_003

Annotator A single-file dry run:

```bash
python3 scripts/import_cape_gold_annotation.py --experiment-dir experiments/cape_kg_eacl_20260627 --target-file experiments/cape_kg_eacl_20260627/01_data/gold_annotation/full_120/annotator_A.jsonl --reviewed-file experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_003/annotator_A_full_120_priority_batch_003.reviewed.jsonl --allow-partial
```

Annotator A single-file apply for debugging only:

```bash
python3 scripts/import_cape_gold_annotation.py --experiment-dir experiments/cape_kg_eacl_20260627 --target-file experiments/cape_kg_eacl_20260627/01_data/gold_annotation/full_120/annotator_A.jsonl --reviewed-file experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_003/annotator_A_full_120_priority_batch_003.reviewed.jsonl --allow-partial --apply
```

Annotator B single-file dry run:

```bash
python3 scripts/import_cape_gold_annotation.py --experiment-dir experiments/cape_kg_eacl_20260627 --target-file experiments/cape_kg_eacl_20260627/01_data/gold_annotation/full_120/annotator_B.jsonl --reviewed-file experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_003/annotator_B_full_120_priority_batch_003.reviewed.jsonl --allow-partial
```

Annotator B single-file apply for debugging only:

```bash
python3 scripts/import_cape_gold_annotation.py --experiment-dir experiments/cape_kg_eacl_20260627 --target-file experiments/cape_kg_eacl_20260627/01_data/gold_annotation/full_120/annotator_B.jsonl --reviewed-file experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_003/annotator_B_full_120_priority_batch_003.reviewed.jsonl --allow-partial --apply
```

### full_120_priority_batch_004

Annotator A single-file dry run:

```bash
python3 scripts/import_cape_gold_annotation.py --experiment-dir experiments/cape_kg_eacl_20260627 --target-file experiments/cape_kg_eacl_20260627/01_data/gold_annotation/full_120/annotator_A.jsonl --reviewed-file experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_004/annotator_A_full_120_priority_batch_004.reviewed.jsonl --allow-partial
```

Annotator A single-file apply for debugging only:

```bash
python3 scripts/import_cape_gold_annotation.py --experiment-dir experiments/cape_kg_eacl_20260627 --target-file experiments/cape_kg_eacl_20260627/01_data/gold_annotation/full_120/annotator_A.jsonl --reviewed-file experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_004/annotator_A_full_120_priority_batch_004.reviewed.jsonl --allow-partial --apply
```

Annotator B single-file dry run:

```bash
python3 scripts/import_cape_gold_annotation.py --experiment-dir experiments/cape_kg_eacl_20260627 --target-file experiments/cape_kg_eacl_20260627/01_data/gold_annotation/full_120/annotator_B.jsonl --reviewed-file experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_004/annotator_B_full_120_priority_batch_004.reviewed.jsonl --allow-partial
```

Annotator B single-file apply for debugging only:

```bash
python3 scripts/import_cape_gold_annotation.py --experiment-dir experiments/cape_kg_eacl_20260627 --target-file experiments/cape_kg_eacl_20260627/01_data/gold_annotation/full_120/annotator_B.jsonl --reviewed-file experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_004/annotator_B_full_120_priority_batch_004.reviewed.jsonl --allow-partial --apply
```

### full_120_priority_batch_005

Annotator A single-file dry run:

```bash
python3 scripts/import_cape_gold_annotation.py --experiment-dir experiments/cape_kg_eacl_20260627 --target-file experiments/cape_kg_eacl_20260627/01_data/gold_annotation/full_120/annotator_A.jsonl --reviewed-file experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_005/annotator_A_full_120_priority_batch_005.reviewed.jsonl --allow-partial
```

Annotator A single-file apply for debugging only:

```bash
python3 scripts/import_cape_gold_annotation.py --experiment-dir experiments/cape_kg_eacl_20260627 --target-file experiments/cape_kg_eacl_20260627/01_data/gold_annotation/full_120/annotator_A.jsonl --reviewed-file experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_005/annotator_A_full_120_priority_batch_005.reviewed.jsonl --allow-partial --apply
```

Annotator B single-file dry run:

```bash
python3 scripts/import_cape_gold_annotation.py --experiment-dir experiments/cape_kg_eacl_20260627 --target-file experiments/cape_kg_eacl_20260627/01_data/gold_annotation/full_120/annotator_B.jsonl --reviewed-file experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_005/annotator_B_full_120_priority_batch_005.reviewed.jsonl --allow-partial
```

Annotator B single-file apply for debugging only:

```bash
python3 scripts/import_cape_gold_annotation.py --experiment-dir experiments/cape_kg_eacl_20260627 --target-file experiments/cape_kg_eacl_20260627/01_data/gold_annotation/full_120/annotator_B.jsonl --reviewed-file experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_005/annotator_B_full_120_priority_batch_005.reviewed.jsonl --allow-partial --apply
```

## Expected Refreshed Files

확인 파일:

- `experiments/cape_kg_eacl_20260627/01_data/gold_annotation/iaa_full_120/iaa_summary.json`
- `experiments/cape_kg_eacl_20260627/01_data/gold_annotation/full_120/adjudication_draft.jsonl`
- `experiments/cape_kg_eacl_20260627/04_evaluation/human_gold_validation_summary.json`
- `experiments/cape_kg_eacl_20260627/06_release/claim_gate_report.md`
