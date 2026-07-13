# CAPE-KG Optional Annotation Expansion Package

Generated: 2026-06-29T18:55:22.016581+00:00

This package is an optional strong-paper scale scaffold. It does not change the 11-file minimum paper gate and is tracked separately for optional/strong claims.
The original current source has 214 Layer2 chunks. A sentence-preserving resegmentation scaffold is provided for a 300+ chunk human-review target.

## Summary

- All available Layer2 chunks: 214
- Current required full package chunks: 120
- Remaining optional chunks: 94
- Maximum current-corpus adjudicated chunks if fully reviewed: 214
- Strong 300 chunk target gap without resegmentation: 86
- Strong resegmented package: `strong_resegmented_342_max18`
- Strong resegmented max sentences per unit: 18
- Strong resegmented review units: 342
- Strong 300 chunk target gap after resegmentation: 0
- Claim status: `optional_expansion_ready_pending_human_review`

## Packages

| package | chunks | chunks with silver candidates | candidate edges | path |
|---|---:|---:|---:|---|
| all_available_214 | 214 | 72 | 2004 | `experiments/cape_kg_eacl_20260627/01_data/gold_annotation/all_available_214` |
| remaining_94_text_only | 94 | 0 | 0 | `experiments/cape_kg_eacl_20260627/01_data/gold_annotation/remaining_94_text_only` |
| strong_resegmented_342_max18 | 342 | 93 | 2087 | `experiments/cape_kg_eacl_20260627/01_data/gold_annotation/strong_resegmented_342_max18` |

## Interpretation

- `all_available_214` is useful if the project wants to review every current chunk.
- `remaining_94_text_only` contains chunks not included in the current 120-chunk evaluation package.
- `strong_resegmented_342_max18` splits the same source chunks into at most 18 source sentences per review unit, yielding 342 pending human-review units.
- The resegmented package keeps `source_chunk_id` and `split_sentence_ids`, so every review unit remains traceable to the original Layer2 chunk and source sentences.
- Many remaining chunks have zero silver candidates; annotators can still add directly supported nodes/edges from text.
- This is optional expansion evidence, not completed human gold. It must not be reported as adjudicated 300+ chunks until two-annotator review and adjudication are returned.

## Strong resegmented package detail

- Package path: `experiments/cape_kg_eacl_20260627/01_data/gold_annotation/strong_resegmented_342_max18`
- Review units: 342
- Units with silver candidates: 93
- Candidate edges total: 2087
- Claim status: `ready_pending_human_review`
