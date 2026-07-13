# CAPE-KG Post-Human Scoring Readiness

Generated: 2026-06-29T18:56:33.656720+00:00
Claim status: `post_human_scoring_readiness_ready_pending_human_returns`
Overall status: `PASS`
Safe to use as submission: `False`
Submission ready: `False`

이 파일은 사람 검수 결과가 돌아온 뒤 어떤 지표를 어떤 명령으로 갱신해야 하는지 고정한 readiness map입니다. 현재 human-gold evidence 자체가 아니며, 최종 논문 성능 claim을 대체하지 않습니다.

## Summary

| item | value |
| --- | --- |
| metric_count | 10 |
| claimable_metric_count | 0 |
| pending_metric_count | 10 |
| tracked_return_files | 14 |
| present_return_files | 0 |
| minimum_return_files | 11 |
| minimum_present_return_files | 0 |
| readiness_claim_status | pending_human_gold_iaa_and_human_gold_scoring |
| claim_gate_overall_status | FAIL |
| pre_human_validation_status | PASS |
| pre_human_validation_counts | {'PASS': 91, 'WARN': 1} |
| pre_human_validation_check_count | 92 |
| pre_human_validation_claim_status | pre_human_handoff_ready_not_submission_complete |
| primary_command_style | portable_python3 |
| pinned_python_exists | True |

## Metric Readiness

| metric | claim_status | returns | gate_ids | main_outputs |
| --- | --- | --- | --- | --- |
| Node F1 | pending_human_returns | 0/11 | gold.completed_chunks, gold.item_count, gold.iaa, llm.proposed_human_gold_score | experiments/cape_kg_eacl_20260627/04_evaluation/human_gold_metrics.json<br>experiments/cape_kg_eacl_20260627/04_evaluation/human_gold_metrics.csv<br>experiments/cape_kg_eacl_20260627/04_evaluation/human_gold_evaluation_report.md |
| Edge F1 | pending_human_returns | 0/11 | gold.completed_chunks, gold.item_count, gold.iaa, llm.proposed_human_gold_score | experiments/cape_kg_eacl_20260627/04_evaluation/human_gold_metrics.json<br>experiments/cape_kg_eacl_20260627/04_evaluation/human_gold_metrics.csv<br>experiments/cape_kg_eacl_20260627/04_evaluation/human_gold_evaluation_report.md |
| Evidence Exact Match / IoU | pending_human_returns | 0/11 | gold.completed_chunks, gold.item_count, gold.iaa, llm.proposed_human_gold_score | experiments/cape_kg_eacl_20260627/04_evaluation/human_gold_span_iou_metrics.json<br>experiments/cape_kg_eacl_20260627/04_evaluation/human_gold_span_iou_components.csv<br>experiments/cape_kg_eacl_20260627/04_evaluation/human_gold_span_iou_report.md |
| Unsupported Edge Rate | pending_human_returns | 0/11 | gold.completed_chunks, gold.item_count, gold.iaa, llm.proposed_human_gold_score | experiments/cape_kg_eacl_20260627/04_evaluation/human_gold_metrics.json<br>experiments/cape_kg_eacl_20260627/04_evaluation/human_gold_metrics.csv<br>experiments/cape_kg_eacl_20260627/04_evaluation/human_gold_evaluation_report.md |
| Ontology Conformance | pending_human_returns | 0/11 | gold.completed_chunks, gold.item_count, llm.proposed_human_gold_score | experiments/cape_kg_eacl_20260627/04_evaluation/structural_evaluation_metrics.json<br>experiments/cape_kg_eacl_20260627/04_evaluation/structural_evaluation_report.md<br>experiments/cape_kg_eacl_20260627/06_release/cq_query_pack.md |
| Procedural Consistency | pending_human_returns | 0/11 | gold.completed_chunks, gold.item_count, llm.proposed_human_gold_score | experiments/cape_kg_eacl_20260627/04_evaluation/structural_evaluation_metrics.json<br>experiments/cape_kg_eacl_20260627/04_evaluation/structural_evaluation_report.md<br>experiments/cape_kg_eacl_20260627/06_release/cq_query_pack.md |
| CQ Answerability | pending_human_returns | 0/11 | gold.completed_chunks, gold.item_count, llm.proposed_human_gold_score | experiments/cape_kg_eacl_20260627/04_evaluation/structural_evaluation_metrics.json<br>experiments/cape_kg_eacl_20260627/04_evaluation/structural_evaluation_report.md<br>experiments/cape_kg_eacl_20260627/06_release/cq_query_pack.md |
| NCS/PCF Mapping P@K / MRR / nDCG | pending_human_returns | 0/1 | mapping.expert_review | experiments/cape_kg_eacl_20260627/04_evaluation/mapping_expert_metrics.json<br>experiments/cape_kg_eacl_20260627/04_evaluation/mapping_expert_evaluation_report.md<br>experiments/cape_kg_eacl_20260627/06_release/mapping_review_progress_report.md |
| NCS-PCF Crosswalk Accept Rate / Utility | pending_human_returns | 0/1 | crosswalk.expert_review | experiments/cape_kg_eacl_20260627/04_evaluation/crosswalk_expert_metrics.json<br>experiments/cape_kg_eacl_20260627/04_evaluation/crosswalk_expert_evaluation_report.md<br>experiments/cape_kg_eacl_20260627/04_evaluation/ncs_pcf_crosswalk_summary.json |
| Active Review Efficiency | pending_human_returns | 0/1 | strong.active_review | experiments/cape_kg_eacl_20260627/04_evaluation/active_review_human_effort_metrics.json<br>experiments/cape_kg_eacl_20260627/04_evaluation/active_review_human_effort_report.md<br>experiments/cape_kg_eacl_20260627/04_evaluation/active_review_efficiency_metrics.json |

## Refresh Commands

아래 명령은 현재 repository checkout에서 바로 실행하기 위한 portable `python3` 기준 명령입니다.

| step | command |
| --- | --- |
| validate_returns | python3 scripts/validate_cape_human_review_returns.py --experiment-dir experiments/cape_kg_eacl_20260627 |
| dry_run_apply_returns | PYTHON_BIN=python3 LLM_PYTHON=python3 APPLY_IMPORTS=0 bash scripts/run_cape_human_return_apply.sh |
| apply_returns_and_refresh | PYTHON_BIN=python3 LLM_PYTHON=python3 APPLY_IMPORTS=1 bash scripts/run_cape_human_return_apply.sh |
| validate_pre_human_or_post_refresh | python3 scripts/validate_cape_pre_human_handoff.py --experiment-dir experiments/cape_kg_eacl_20260627 --outputs-dir outputs |

## Pinned Environment Commands

아래 명령은 현재 서버에서 확인된 pinned Python 경로 `/home/minjoo/tdpo2_aaai2027/.venv_tdpo2/bin/python`를 사용하는 참고 명령입니다.

| step | command |
| --- | --- |
| validate_returns | /home/minjoo/tdpo2_aaai2027/.venv_tdpo2/bin/python scripts/validate_cape_human_review_returns.py --experiment-dir experiments/cape_kg_eacl_20260627 |
| dry_run_apply_returns | PYTHON_BIN=/home/minjoo/tdpo2_aaai2027/.venv_tdpo2/bin/python LLM_PYTHON=/home/minjoo/tdpo2_aaai2027/.venv_tdpo2/bin/python APPLY_IMPORTS=0 bash scripts/run_cape_human_return_apply.sh |
| apply_returns_and_refresh | PYTHON_BIN=/home/minjoo/tdpo2_aaai2027/.venv_tdpo2/bin/python LLM_PYTHON=/home/minjoo/tdpo2_aaai2027/.venv_tdpo2/bin/python APPLY_IMPORTS=1 bash scripts/run_cape_human_return_apply.sh |
| validate_pre_human_or_post_refresh | /home/minjoo/tdpo2_aaai2027/.venv_tdpo2/bin/python scripts/validate_cape_pre_human_handoff.py --experiment-dir experiments/cape_kg_eacl_20260627 --outputs-dir outputs |

## Claim Policy

- This artifact is a scoring readiness map, not human-gold evidence.
- Metrics with pending_human_returns must not be used as final paper performance claims.
- Run dry-run validation before APPLY_IMPORTS=1 whenever reviewed return files are added.
- Regenerate paper tables, claim gate, provenance, and release bundles after applying returns.

## Missing Outputs Or Evidence

- none
