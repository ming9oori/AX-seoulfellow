# CAPE-KG Mapping Expert Review Handoff

이 bundle은 NCS/PCF mapping downstream claim을 위한 내부 expert review 자료다.

## 열 파일

- Workbench: `experiments/cape_kg_eacl_20260627/01_data/mapping_review/mapping_review_workbench.html`
- Protocol: `experiments/cape_kg_eacl_20260627/01_data/mapping_review/mapping_review_protocol.md`
- Review JSONL: `experiments/cape_kg_eacl_20260627/01_data/mapping_review/mapping_review_items.jsonl`
- Group briefing: `experiments/cape_kg_eacl_20260627/06_release/mapping_review_group_briefing.md`
- Group briefing CSV: `experiments/cape_kg_eacl_20260627/05_review/mapping_review_group_briefing_top20.csv`
- Next 20 groups: `experiments/cape_kg_eacl_20260627/05_review/mapping_review_next_20_groups.csv`
- Next 60 rows: `experiments/cape_kg_eacl_20260627/05_review/mapping_review_next_60_rows.csv`
- Validation error playbook: `experiments/cape_kg_eacl_20260627/06_release/human_return_validation_error_playbook_ko.md`
- Master checklist: `experiments/cape_kg_eacl_20260627/06_release/human_review_master_checklist_ko.md`
- Status dashboard: `experiments/cape_kg_eacl_20260627/06_release/human_review_status_dashboard_ko.md`
- Launch checklist: `experiments/cape_kg_eacl_20260627/06_release/human_review_launch_checklist_ko.md`

## Review 규칙

- source task + standard별 Top-5 후보 5개를 하나의 group으로 본다.
- `mapping_review_group_briefing.md`에서 Top-20 group의 Top-5 후보를 먼저 비교한다.
- group 5개 row가 모두 `review_status=completed`가 되어야 P@K/MRR 계산에 들어간다.
- decision은 `accepted`, `rejected`, `unsure` 중 하나를 사용한다.
- `relevance_grade`는 0, 1, 2, 3 중 하나를 사용한다.

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

아래 단일 파일 import는 mapping reviewed file 문제를 디버깅할 때만 사용한다.

```bash
python3 scripts/import_cape_mapping_review.py \
  --experiment-dir experiments/cape_kg_eacl_20260627 \
  --reviewed-file experiments/cape_kg_eacl_20260627/01_data/mapping_review/mapping_review_items.reviewed.jsonl
```
