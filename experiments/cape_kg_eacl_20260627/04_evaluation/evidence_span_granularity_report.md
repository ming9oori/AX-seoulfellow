# CAPE-KG Component Evidence Span Granularity Report

Generated: 2026-06-29T18:55:36.060929+00:00

This report audits how far the current evidence grounding goes beyond sentence anchors.
It derives subject/object lexical character spans when labels appear in the evidence sentence and marks predicate support as a full-sentence proxy.
It is not a human-gold span evaluation.

## Summary

- Triples: 947
- Components: 2841
- Exact component spans: 742 (0.261176)
- Components with chunk-local spans: 1683 (0.592397)
- Subject exact spans: 220 (0.232313)
- Object exact spans: 522 (0.551214)
- Predicate full-sentence proxies: 947 (1.0)
- Claim status: `automatic_component_span_diagnostic_not_human_gold`

## Method Counts

| key | count |
|---|---:|
| object.case_insensitive_label_match | 2 |
| object.chunk_span | 519 |
| object.exact | 522 |
| object.exact_label_match | 520 |
| object.label_not_found_in_sentence | 425 |
| predicate.chunk_span | 944 |
| predicate.full_sentence_proxy | 947 |
| subject.case_insensitive_label_match | 2 |
| subject.chunk_span | 220 |
| subject.exact | 220 |
| subject.exact_label_match | 218 |
| subject.label_not_found_in_sentence | 727 |

## Interpretation

- Sentence-level evidence coverage is already present in the KG.
- This diagnostic adds component-level lexical spans for subject/object labels where possible.
- Predicate evidence is still sentence-level proxy evidence; human annotation is needed for predicate-token evidence spans.
- Use this file to document evidence-grounding granularity honestly before human-gold span scoring.
