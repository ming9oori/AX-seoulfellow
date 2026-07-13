# CAPE-KG Active Review Human-Effort Handoff

이 bundle은 active-review efficiency claim을 검증하기 위한 reviewer effort/timing 수집 자료다.

## 열 파일

- Plan: `experiments/cape_kg_eacl_20260627/06_release/active_review_human_effort_plan.md`
- Briefing: `experiments/cape_kg_eacl_20260627/06_release/active_review_human_effort_briefing.md`
- Briefing CSV: `experiments/cape_kg_eacl_20260627/05_review/active_review_human_effort_briefing.csv`
- Template CSV: `experiments/cape_kg_eacl_20260627/05_review/active_review_human_effort_template.csv`
- Expected reviewed CSV: `experiments/cape_kg_eacl_20260627/05_review/active_review_human_effort.reviewed.csv`
- Active-review queue: `experiments/cape_kg_eacl_20260627/05_review/actual_llm_active_review_queue_P_cape_kg_actual.csv`
- Silver diagnostic report: `experiments/cape_kg_eacl_20260627/04_evaluation/active_review_efficiency_report.md`
- Validation error playbook: `experiments/cape_kg_eacl_20260627/06_release/human_return_validation_error_playbook_ko.md`
- Master checklist: `experiments/cape_kg_eacl_20260627/06_release/human_review_master_checklist_ko.md`
- Status dashboard: `experiments/cape_kg_eacl_20260627/06_release/human_review_status_dashboard_ko.md`
- Launch checklist: `experiments/cape_kg_eacl_20260627/06_release/human_review_launch_checklist_ko.md`

## Review 규칙

- `active_review_human_effort_template.csv`를 열고 각 row를 한 번씩 검토한다.
- `active_review_human_effort_briefing.md`와 `active_review_human_effort_briefing.csv`를 먼저 확인해 high-impact/evidence/schema 항목 순서로 검토한다.
- `reviewer_id`, `review_seconds`, `decision`, `corrected_error`, `high_impact_correction`을 반드시 채운다.
- `decision`은 `correct`, `incorrect`, `partial`, `unsupported`, `invalid`, `unsure` 중 하나를 사용한다.
- `corrected_error=true`는 reviewer가 후보를 수정/거절/부분수정한 경우에 사용한다.
- `high_impact_correction=true`는 evidence, schema, risk, gateway, central task-flow에 영향을 주는 수정에 사용한다.
- 완료 파일은 정확히 `experiments/cape_kg_eacl_20260627/05_review/active_review_human_effort.reviewed.csv` 경로명으로 저장한다.

## Preflight

```bash
python3 scripts/validate_cape_human_review_returns.py \
  --experiment-dir experiments/cape_kg_eacl_20260627
```

## Metrics Refresh

preflight 통과 후 안전 wrapper dry-run을 실행하면 `04_evaluation/active_review_human_effort_metrics.json`과 paper tables 갱신 가능 여부를 확인한다.

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

이 파일은 human-gold annotation을 대체하지 않는다. Active-review efficiency claim은 reviewer effort/timing과 adjudicated gold outcome alignment가 모두 있어야 논문 주장으로 사용할 수 있다.
