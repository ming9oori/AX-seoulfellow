# CAPE-KG NCS-PCF Crosswalk Roundtrip Smoke Test

Generated: 2026-06-29T18:55:36.781900+00:00
Overall status: `PASS`
Claim status: `crosswalk_roundtrip_smoke_not_paper_evidence`

This is an engineering smoke test only. It uses copied crosswalk rows to verify import and evaluation mechanics; it is not expert review and must not be used as paper evidence.

## Summary

- Source groups: 2
- Reviewed rows: 20
- Import errors: 0
- Import warnings: 0
- Metric rows: 1

## Metrics

| candidates | source tasks | completed | pending | complete groups | Hit@1 | Hit@3 | Hit@5 | P@10 | MRR | nDCG@10 | utility | explanation quality | status |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 20 | 2 | 20 | 0 | 2 | 1.0 | 1.0 | 1.0 | 0.1 | 1.0 | 1.0 | 0.3 | 3.2 | crosswalk_expert_review_evaluated |

## Files

- target: `experiments/cape_kg_eacl_20260627/06_release/crosswalk_roundtrip_smoke/crosswalk_target.jsonl`
- reviewed: `experiments/cape_kg_eacl_20260627/06_release/crosswalk_roundtrip_smoke/crosswalk_reviewed.jsonl`
- merged: `experiments/cape_kg_eacl_20260627/06_release/crosswalk_roundtrip_smoke/crosswalk_merged.jsonl`
- import_report: `experiments/cape_kg_eacl_20260627/06_release/crosswalk_roundtrip_smoke/crosswalk_import_report.json`
- metrics_csv: `experiments/cape_kg_eacl_20260627/06_release/crosswalk_roundtrip_smoke/crosswalk_metrics_smoke.csv`
- metrics_json: `experiments/cape_kg_eacl_20260627/06_release/crosswalk_roundtrip_smoke/crosswalk_metrics_smoke.json`
- summary: `experiments/cape_kg_eacl_20260627/06_release/crosswalk_roundtrip_smoke/crosswalk_roundtrip_smoke_summary.json`
- report: `experiments/cape_kg_eacl_20260627/06_release/crosswalk_roundtrip_smoke/crosswalk_roundtrip_smoke_report.md`
