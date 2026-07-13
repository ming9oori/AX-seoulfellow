# CAPE-KG Human Review Packet Integrity Report

Generated: 2026-06-29T06:55:45.936885+00:00
Experiment: `experiments/cape_kg_eacl_20260627`
Overall status: `PASS`
Claim status: `human_review_packet_integrity_ready_pending_human_returns`

이 보고서는 human-gold/IAA/전문가 검수 결과를 대체하지 않습니다.
목적은 사람이 검수하기 전에 배포된 입력 파일, return-file manifest, handoff bundle이 구조적으로 빠짐없이 준비되었는지 확인하는 것입니다.

## Summary

- Integrity errors: 0
- Integrity warnings: 0
- Minimum annotation chunks assigned: 100
- Minimum annotation candidate edges: 1371
- Mapping review rows: 220
- Crosswalk review rows: 220
- Active-review effort rows: 204
- Optional strong review units: 342
- Required human return files currently present: 0 / 14

## Component Readiness

| component | status | rows | key_count | human_state |
| --- | --- | --- | --- | --- |
| Minimum annotation batches | READY/PENDING | 10 | 100 chunks / 1371 candidate edges | 0 reviewed files present |
| Mapping expert review | READY/PENDING | 220 | 44 source-standard groups | 0 completed rows |
| NCS-PCF crosswalk review | READY/PENDING | 220 | 22 source tasks | 0 completed rows |
| Active-review effort | READY/PENDING | 204 | 204 review items | 0 human-filled rows |
| Optional strong package | READY/PENDING | 342 | 214 source chunks / 2048 candidate edges | pending_strong_human_returns |
| Return-file manifest | READY/PENDING | 16 | 14 required / 11 minimum | 0 returned files |
| Handoff bundles | READY | 9 | 100 chunks / 1371 candidate edges | handoff_ready_pending_human_review |

## Interpretation

- `READY/PENDING`은 입력 패킷은 준비되었지만 사람의 reviewed/adjudicated 파일이 아직 없다는 뜻입니다.
- 현재 단계에서 없는 reviewed 파일은 오류가 아닙니다. 오류는 입력 파일 누락, ID 불일치, 행 수 불일치, manifest 불일치입니다.
- 논문 claim으로 사용할 수 있는 human-gold 성능, IAA, expert mapping metric은 사람이 return 파일을 작성하고 import/preflight를 통과한 뒤에만 생성됩니다.

## Issues

No blocking integrity issues were found.

## Output Files

- JSON: `experiments/cape_kg_eacl_20260627/06_release/human_review_packet_integrity.json`
- Markdown: `experiments/cape_kg_eacl_20260627/06_release/human_review_packet_integrity.md`
- Issue CSV: `experiments/cape_kg_eacl_20260627/05_review/human_review_packet_integrity_issues.csv`
