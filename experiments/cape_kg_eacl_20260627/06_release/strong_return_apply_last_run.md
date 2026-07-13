# CAPE-KG Strong 300+ Return Apply Last Run

Started: `2026-06-29T19:01:25Z`
Ended: `2026-06-29T19:01:25Z`
Experiment: `experiments/cape_kg_eacl_20260627`
APPLY_IMPORTS: `0`

## Status

- Wrapper status: `completed`
- Exit code: 0
- Strong return preflight: `pending_strong_human_returns`
- Package: `strong_resegmented_342_max18`
- Present strong return files: 0
- Apply scope: `no_strong_return_files`
- Expected review units: 342
- Paired completed chunks: 0
- Ready for strong IAA: False
- Ready for strong claim after import: False
- Error count: 0
- Warning count: 0

## Import Reports

- `experiments/cape_kg_eacl_20260627/01_data/gold_annotation/strong_resegmented_342_max18/annotator_A_import_report.json`: exists=False
- `experiments/cape_kg_eacl_20260627/01_data/gold_annotation/strong_resegmented_342_max18/annotator_B_import_report.json`: exists=False
- `experiments/cape_kg_eacl_20260627/01_data/gold_annotation/strong_resegmented_342_max18/adjudication_import_report.json`: exists=False

## Interpretation

- This wrapper only handles the optional strong 300+ resegmented package.
- `APPLY_IMPORTS=0` validates and dry-runs any present import files without mutating the package targets.
- `APPLY_IMPORTS=1` is refused when no reviewed strong return files are present unless `ALLOW_EMPTY_APPLY=1` is set.
- Strong 300+ paper claims still require imported A/B annotations, IAA, adjudication, and human-gold scoring.
