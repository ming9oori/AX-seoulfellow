# CAPE-KG Annotator B Handoff

이 bundle은 내부 human-gold annotation 작업용이다. 원문 기반 chunk text가 들어 있으므로 외부 공개용이 아니다.

## 목표

- annotator `B`가 priority batch 001-005, 총 100 chunks를 독립적으로 검수한다.
- chunk text만 근거로 candidate edge를 accept/reject한다.
- 빠진 node/edge가 명시적으로 지지되면 추가한다.
- 모든 accepted edge에는 evidence anchor 또는 exact span을 남긴다.
- 완료한 chunk는 `annotation_status`를 `completed`로 둔다. 불확실하면 `needs_adjudication`을 사용한다.

## 열 파일

- Workbench: `experiments/cape_kg_eacl_20260627/01_data/gold_annotation/annotation_workbench.html`
- Schema: `experiments/cape_kg_eacl_20260627/01_data/gold_annotation/annotation_schema.json`
- Annotation guideline: `experiments/cape_kg_eacl_20260627/01_data/annotation_guideline_v1.md`
- Protocol: `experiments/cape_kg_eacl_20260627/01_data/gold_annotation/adjudication_protocol.md`
- Calibration pack: `experiments/cape_kg_eacl_20260627/06_release/annotation_calibration_pack_ko.md`
- Return field guide: `experiments/cape_kg_eacl_20260627/06_release/annotation_return_field_guide_ko.md`
- Validation error playbook: `experiments/cape_kg_eacl_20260627/06_release/human_return_validation_error_playbook_ko.md`
- Master checklist: `experiments/cape_kg_eacl_20260627/06_release/human_review_master_checklist_ko.md`
- First batch execution card: `experiments/cape_kg_eacl_20260627/05_review/human_review_first_batch_execution_card_ko.md`
- Role quickstart: `experiments/cape_kg_eacl_20260627/05_review/human_review_role_quickstart_cards_ko.md`
- Status dashboard: `experiments/cape_kg_eacl_20260627/06_release/human_review_status_dashboard_ko.md`
- Launch checklist: `experiments/cape_kg_eacl_20260627/06_release/human_review_launch_checklist_ko.md`
- Batch review preview summary: `experiments/cape_kg_eacl_20260627/06_release/annotation_batch_review_preview_summary.md`

## Batch Files

### full_120_priority_batch_001

- Input JSONL: `experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_001/annotator_B_full_120_priority_batch_001.jsonl`
- Save reviewed JSONL as: `experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_001/annotator_B_full_120_priority_batch_001.reviewed.jsonl`
- Tracking sheet: `experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_001/batch_tracking_sheet.csv`
- Review preview: `experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_001/batch_review_preview.md`

### full_120_priority_batch_002

- Input JSONL: `experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_002/annotator_B_full_120_priority_batch_002.jsonl`
- Save reviewed JSONL as: `experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_002/annotator_B_full_120_priority_batch_002.reviewed.jsonl`
- Tracking sheet: `experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_002/batch_tracking_sheet.csv`
- Review preview: `experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_002/batch_review_preview.md`

### full_120_priority_batch_003

- Input JSONL: `experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_003/annotator_B_full_120_priority_batch_003.jsonl`
- Save reviewed JSONL as: `experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_003/annotator_B_full_120_priority_batch_003.reviewed.jsonl`
- Tracking sheet: `experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_003/batch_tracking_sheet.csv`
- Review preview: `experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_003/batch_review_preview.md`

### full_120_priority_batch_004

- Input JSONL: `experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_004/annotator_B_full_120_priority_batch_004.jsonl`
- Save reviewed JSONL as: `experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_004/annotator_B_full_120_priority_batch_004.reviewed.jsonl`
- Tracking sheet: `experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_004/batch_tracking_sheet.csv`
- Review preview: `experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_004/batch_review_preview.md`

### full_120_priority_batch_005

- Input JSONL: `experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_005/annotator_B_full_120_priority_batch_005.jsonl`
- Save reviewed JSONL as: `experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_005/annotator_B_full_120_priority_batch_005.reviewed.jsonl`
- Tracking sheet: `experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_005/batch_tracking_sheet.csv`
- Review preview: `experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_005/batch_review_preview.md`

## Return and Apply Flow

각 batch를 검수한 뒤에는 reviewed filename 그대로 저장하고 coordinator에게 전달한다.
Coordinator는 개별 파일을 바로 apply하지 않고, 전체 반환 파일 preflight와 안전 wrapper를 먼저 실행한다.

전체 반환 파일 preflight:

```bash
python3 scripts/validate_cape_human_review_returns.py --experiment-dir experiments/cape_kg_eacl_20260627
```

전체 dry-run refresh:

```bash
PYTHON_BIN=python3 \
LLM_PYTHON=python3 \
APPLY_IMPORTS=0 \
bash scripts/run_cape_human_return_apply.sh
```

preflight와 dry-run이 통과하고 필요한 reviewed file이 모두 있으면 실제 반영:

```bash
PYTHON_BIN=python3 \
LLM_PYTHON=python3 \
APPLY_IMPORTS=1 \
bash scripts/run_cape_human_return_apply.sh
```

## Low-Level Debug Import

아래 단일 파일 import는 특정 batch file을 디버깅할 때만 사용한다. 운영 반영은 위 wrapper를 기본 경로로 사용한다.

```bash
python3 scripts/import_cape_gold_annotation.py \
  --experiment-dir experiments/cape_kg_eacl_20260627 \
  --target-file experiments/cape_kg_eacl_20260627/01_data/gold_annotation/full_120/annotator_B.jsonl \
  --reviewed-file <reviewed_jsonl_from_batch> \
  --allow-partial
```

논문용 gold로 인정되려면 annotator A/B import, IAA 계산, adjudication, human-gold scoring까지 완료되어야 한다.
