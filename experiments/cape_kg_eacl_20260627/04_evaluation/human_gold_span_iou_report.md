# CAPE-KG Human-Gold Component Span IoU

Generated: 2026-06-29T18:55:21.327174+00:00
Claim status: `pending_human_adjudication`

This report evaluates automatic component-level evidence span suggestions against adjudicated human gold.
It is paper-claimable only after completed adjudication rows contain component evidence spans.

## Summary

| Item | Value |
|---|---:|
| Candidate rows | 120 |
| Candidate edges | 1444 |
| Candidate component spans | 4332 |
| Completed adjudicated chunks | 0 |
| Gold edges | 0 |
| Gold component spans | 0 |
| Matched edges | 0 |
| Matched component spans | 0 |
| Span exact match rate | None |
| Mean span IoU | None |

## Component Metrics

| component | count | exact rate | mean IoU |
|---|---:|---:|---:|
| subject | 0 | None | None |
| predicate | 0 | None | None |
| object | 0 | None | None |

## Status Counts

- pending_two_annotator_input: 120

## Interpretation

- No component span metric rows were produced yet.
- This is expected before human adjudication or before gold component spans are returned.


## Output Files

- Metrics JSON: `experiments/cape_kg_eacl_20260627/04_evaluation/human_gold_span_iou_metrics.json`
- Component rows CSV: `experiments/cape_kg_eacl_20260627/04_evaluation/human_gold_span_iou_components.csv`
- Report MD: `experiments/cape_kg_eacl_20260627/04_evaluation/human_gold_span_iou_report.md`
