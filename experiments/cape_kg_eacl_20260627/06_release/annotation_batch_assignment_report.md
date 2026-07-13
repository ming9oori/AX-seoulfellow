# CAPE-KG Human Annotation Batch Assignments

Generated: 2026-06-29T18:44:25.141580+00:00

These batches are workflow artifacts for human annotation. They do not satisfy the gold-label gate until edited, imported, and adjudicated.

- Package: `full_120`
- Batch size: 20
- Batches: 5
- Assigned chunks: 100
- Candidate edges in assigned chunks: 1371
- Output directory: `experiments/cape_kg_eacl_20260627/05_review/human_gold_batches`

## Batches

| batch | chunks | rank range | candidate edges | high-impact chunks | files |
|---|---:|---:|---:|---:|---|
| full_120_priority_batch_001 | 20 | 1-20 | 811 | 7 | [README](experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_001/README.md) / [tracking](experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_001/batch_tracking_sheet.csv) |
| full_120_priority_batch_002 | 20 | 21-40 | 180 | 16 | [README](experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_002/README.md) / [tracking](experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_002/batch_tracking_sheet.csv) |
| full_120_priority_batch_003 | 20 | 41-60 | 152 | 15 | [README](experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_003/README.md) / [tracking](experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_003/batch_tracking_sheet.csv) |
| full_120_priority_batch_004 | 20 | 61-80 | 91 | 18 | [README](experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_004/README.md) / [tracking](experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_004/batch_tracking_sheet.csv) |
| full_120_priority_batch_005 | 20 | 81-100 | 137 | 8 | [README](experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_005/README.md) / [tracking](experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_priority_batch_005/batch_tracking_sheet.csv) |

## Preferred Wrapper Commands

Use these commands for normal operation after reviewed files are returned:

```bash
python3 scripts/validate_cape_human_review_returns.py --experiment-dir experiments/cape_kg_eacl_20260627
```

```bash
PYTHON_BIN=python3 LLM_PYTHON=python3 APPLY_IMPORTS=0 bash scripts/run_cape_human_return_apply.sh
```

```bash
PYTHON_BIN=python3 LLM_PYTHON=python3 APPLY_IMPORTS=1 bash scripts/run_cape_human_return_apply.sh
```

## Generated Files

- Summary JSON: `experiments/cape_kg_eacl_20260627/06_release/annotation_batch_assignment_summary.json`
- Overview CSV: `experiments/cape_kg_eacl_20260627/05_review/human_gold_batches/full_120_batch_assignment_overview.csv`
- Report: `experiments/cape_kg_eacl_20260627/06_release/annotation_batch_assignment_report.md`
