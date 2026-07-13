# CAPE-KG Mapping Roundtrip Smoke Test

Generated: 2026-06-29T18:55:24.500664+00:00
Overall status: `PASS`
Claim status: `mapping_roundtrip_smoke_not_paper_evidence`

This is an engineering smoke test only. It uses copied mapping rows to verify import and evaluation mechanics; it is not expert review and must not be used as paper evidence.

## Summary

- Reviewed rows: 10
- Import errors: 0
- Import warnings: 0
- Metric rows: 2

## Metrics

| standard | completed rows | pending rows | complete groups | Hit@1 | Hit@5 | P@5 | MRR | nDCG@10 | explanation quality | status |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| NCS | 5 | 0 | 1 | 1.0 | 1.0 | 0.2 | 1.0 | 1.0 | 3.4 | expert_review_evaluated |
| PCF | 5 | 0 | 1 | 1.0 | 1.0 | 0.2 | 1.0 | 1.0 | 3.4 | expert_review_evaluated |

## Files

- target: `experiments/cape_kg_eacl_20260627/06_release/mapping_roundtrip_smoke/mapping_target.jsonl`
- reviewed: `experiments/cape_kg_eacl_20260627/06_release/mapping_roundtrip_smoke/mapping_reviewed.jsonl`
- merged: `experiments/cape_kg_eacl_20260627/06_release/mapping_roundtrip_smoke/mapping_merged.jsonl`
- import_report: `experiments/cape_kg_eacl_20260627/06_release/mapping_roundtrip_smoke/mapping_import_report.json`
- metrics_csv: `experiments/cape_kg_eacl_20260627/06_release/mapping_roundtrip_smoke/mapping_metrics_smoke.csv`
- metrics_json: `experiments/cape_kg_eacl_20260627/06_release/mapping_roundtrip_smoke/mapping_metrics_smoke.json`
- summary: `experiments/cape_kg_eacl_20260627/06_release/mapping_roundtrip_smoke/mapping_roundtrip_smoke_summary.json`
- report: `experiments/cape_kg_eacl_20260627/06_release/mapping_roundtrip_smoke/mapping_roundtrip_smoke_report.md`
