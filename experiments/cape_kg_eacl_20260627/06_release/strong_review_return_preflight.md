# CAPE-KG Optional Strong 300+ Return Preflight

Generated: 2026-06-29T19:01:25.573311+00:00
Overall status: `pending_strong_human_returns`
Package: `strong_resegmented_342_max18`

This preflight checks optional strong-paper-scale reviewed files before any manual import. It does not change the 11-file minimum paper gate and is not paper-claimable human-gold evidence until reviewed files are actually imported, IAA is recomputed, and adjudication/scoring are completed.

## Validation Policy

- Annotator file identity check: `True`
- Completed candidate coverage check: `True`
- Needs-adjudication comments required: `True`
- Completed adjudication adjudicator id required: `True`

## Summary

| Item | Value |
|---|---:|
| Expected review units | 342 |
| Annotator A present | False |
| Annotator B present | False |
| A completed chunks | 0 |
| B completed chunks | 0 |
| Paired completed chunks | 0 |
| Adjudication present | False |
| Completed adjudicated chunks | 0 |
| Ready for strong IAA | False |
| Ready for strong adjudication import | False |
| Error count | 0 |
| Warning count | 0 |

## Expected Reviewed Files

- Annotator A: `experiments/cape_kg_eacl_20260627/01_data/gold_annotation/strong_resegmented_342_max18/annotator_A_edited.jsonl`
- Annotator B: `experiments/cape_kg_eacl_20260627/01_data/gold_annotation/strong_resegmented_342_max18/annotator_B_edited.jsonl`
- Adjudication: `experiments/cape_kg_eacl_20260627/01_data/gold_annotation/strong_resegmented_342_max18/adjudication_edited.jsonl`

## Next Commands After Returns Arrive

```bash
python3 scripts/validate_cape_strong_review_returns.py \
  --experiment-dir experiments/cape_kg_eacl_20260627

python3 scripts/compute_cape_annotation_iaa.py \
  --annotator-a experiments/cape_kg_eacl_20260627/01_data/gold_annotation/strong_resegmented_342_max18/annotator_A_edited.jsonl \
  --annotator-b experiments/cape_kg_eacl_20260627/01_data/gold_annotation/strong_resegmented_342_max18/annotator_B_edited.jsonl \
  --output-dir experiments/cape_kg_eacl_20260627/01_data/gold_annotation/strong_resegmented_342_max18/iaa_strong_resegmented
```
