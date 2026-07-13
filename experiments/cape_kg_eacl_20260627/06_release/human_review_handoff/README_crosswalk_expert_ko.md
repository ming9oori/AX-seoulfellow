# CAPE-KG NCS-PCF Crosswalk Expert Review Handoff

이 bundle은 Layer2 task를 매개로 생성된 NCS-PCF crosswalk 후보를 검수하기 위한 내부 expert review 자료다.

## 열 파일

- Protocol: `experiments/cape_kg_eacl_20260627/01_data/crosswalk_review/crosswalk_review_protocol.md`
- Review JSONL: `experiments/cape_kg_eacl_20260627/01_data/crosswalk_review/crosswalk_review_items.jsonl`
- Review CSV sheet: `experiments/cape_kg_eacl_20260627/01_data/crosswalk_review/crosswalk_review_sheet.csv`
- Manifest: `experiments/cape_kg_eacl_20260627/01_data/crosswalk_review/crosswalk_review_manifest.json`
- Candidate report: `experiments/cape_kg_eacl_20260627/04_evaluation/ncs_pcf_crosswalk_report.md`
- Candidate CSV: `experiments/cape_kg_eacl_20260627/04_evaluation/ncs_pcf_crosswalk_candidates.csv`
- Expert metrics report: `experiments/cape_kg_eacl_20260627/04_evaluation/crosswalk_expert_evaluation_report.md`
- Validation error playbook: `experiments/cape_kg_eacl_20260627/06_release/human_return_validation_error_playbook_ko.md`
- Master checklist: `experiments/cape_kg_eacl_20260627/06_release/human_review_master_checklist_ko.md`
- Status dashboard: `experiments/cape_kg_eacl_20260627/06_release/human_review_status_dashboard_ko.md`
- Launch checklist: `experiments/cape_kg_eacl_20260627/06_release/human_review_launch_checklist_ko.md`

## Review 규칙

- 각 row는 하나의 Layer2 업무를 공유하는 NCS 후보와 PCF 후보의 pair다.
- `expert_decision`은 `accepted`, `rejected`, `unsure` 중 하나를 사용한다.
- `utility_grade`는 0, 1, 2, 3 중 하나를 사용한다.
- `explanation_quality_score`는 1, 2, 3, 4, 5 중 하나를 사용한다.
- 완료 row는 `review_status=completed`, `reviewer_id`, `comment`를 포함해야 한다.
- 완료 파일은 정확히 `experiments/cape_kg_eacl_20260627/01_data/crosswalk_review/crosswalk_review_items.reviewed.jsonl` 경로명으로 저장한다.

## Apply Flow

```bash
python3 scripts/validate_cape_human_review_returns.py \
  --experiment-dir experiments/cape_kg_eacl_20260627
```

통과하면 안전 wrapper로 dry-run refresh를 먼저 실행한다.

```bash
PYTHON_BIN=python3 \
LLM_PYTHON=python3 \
APPLY_IMPORTS=0 \
bash scripts/run_cape_human_return_apply.sh
```

dry-run과 preflight가 모두 통과하면 `APPLY_IMPORTS=1`로 실제 반영한다.

```bash
PYTHON_BIN=python3 \
LLM_PYTHON=python3 \
APPLY_IMPORTS=1 \
bash scripts/run_cape_human_return_apply.sh
```

## Low-Level Debug Import

```bash
python3 scripts/import_cape_crosswalk_review.py \
  --experiment-dir experiments/cape_kg_eacl_20260627 \
  --reviewed-file experiments/cape_kg_eacl_20260627/01_data/crosswalk_review/crosswalk_review_items.reviewed.jsonl
```

이 crosswalk review는 mapping expert review와 별개다. NCS/PCF 개별 Top-K mapping claim은 mapping expert review가, NCS-PCF pair utility claim은 이 crosswalk review가 필요하다.
