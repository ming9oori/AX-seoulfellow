# CAPE-KG Edge Component Span Traceability

Generated: 2026-06-29T18:56:35.821642+00:00
Claim status: `edge_component_span_traceability_ready_not_human_gold_span_claim`

This artifact links final Layer 2 KG edges to source triples and automatic subject/predicate/object evidence-span diagnostics.
It is a traceability artifact, not a human-gold span-quality result.
Source text is omitted; rows contain offsets, hashes, and metadata only.

## Summary

| Item | Value |
|---|---:|
| Final Layer 2 edges | 947 |
| Edges with source triple IDs | 947 |
| Edges with component span links | 947 |
| Edge-component span links | 2841 |
| Linked source triples | 947 |
| Exact component spans | 742 |
| Exact component span rate | 0.261176 |
| Chunk-local spans | 1683 |
| Chunk-local span rate | 0.592397 |
| Predicate full-sentence proxies | 947 |
| Missing edge source triples | 0 |
| Missing component span triples | 0 |

## Component Roles

| Component | Links |
|---|---:|
| `object` | 947 |
| `predicate` | 947 |
| `subject` | 947 |

## Span Methods

| Method | Links |
|---|---:|
| `object.case_insensitive_label_match` | 2 |
| `object.exact_label_match` | 520 |
| `object.label_not_found_in_sentence` | 425 |
| `predicate.full_sentence_proxy` | 947 |
| `subject.case_insensitive_label_match` | 2 |
| `subject.exact_label_match` | 218 |
| `subject.label_not_found_in_sentence` | 727 |

## Interpretation

- Final KG edges can now be traced to source triples and automatic component-level evidence spans.
- The file is useful for reviewer explanation and later human span adjudication.
- Predicate rows remain sentence-level proxy support until human-gold predicate spans are returned.
- Source text is intentionally omitted from JSONL/CSV rows.
