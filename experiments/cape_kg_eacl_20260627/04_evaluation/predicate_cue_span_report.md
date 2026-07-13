# CAPE-KG Predicate Cue Span Diagnostic

Generated: 2026-06-29T18:55:36.212286+00:00
Claim status: `automatic_predicate_cue_span_diagnostic_not_human_gold`

This report adds an automatic lexical predicate-cue diagnostic on top of the existing sentence-level predicate evidence proxy.
It is not a human-gold predicate-span evaluation. Source text is omitted from JSONL/CSV rows.

## Summary

| Item | Value |
|---|---:|
| Triples | 947 |
| Predicate cue spans found | 550 |
| Predicate cue spans missing | 397 |
| Predicate cue span rate | 0.580781 |
| Chunk-local cue spans | 550 |
| Chunk-local cue span rate | 0.580781 |

## Method Counts

| Method | Count |
|---|---:|
| `predicate_cue_lexical_match` | 550 |
| `predicate_cue_not_found` | 397 |

## Predicate Coverage

| Predicate | Triples | Cue spans | Rate |
|---|---:|---:|---:|
| `FEEDS_INTO` | 9 | 3 | 0.333333 |
| `HAS_DECISION_GATEWAY` | 54 | 54 | 1.0 |
| `HAS_GUARD_CONDITION` | 14 | 9 | 0.642857 |
| `HAS_PRINCIPLE` | 64 | 1 | 0.015625 |
| `HAS_REVIEW_CHECKPOINT` | 41 | 20 | 0.487805 |
| `HAS_RISK` | 39 | 8 | 0.205128 |
| `HAS_STEP` | 99 | 51 | 0.515152 |
| `PERFORMED_BY` | 120 | 83 | 0.691667 |
| `PRECEDES` | 77 | 11 | 0.142857 |
| `PRODUCES` | 220 | 202 | 0.918182 |
| `USED_AS_INPUT_FOR` | 9 | 3 | 0.333333 |
| `USES_INPUT` | 201 | 105 | 0.522388 |

## Interpretation

- Existing component span diagnostics still treat predicate evidence as full-sentence proxy evidence.
- This file adds a separate lexical cue diagnostic for predicates when configured surface cues are present.
- Cue span presence is useful for review prioritization and later human-gold predicate span comparison.
- Cue span absence must not be interpreted as unsupported evidence.
