# CAPE-KG RDF/SHACL-Style Validation Report

Generated: 2026-06-29T18:55:39.744689+00:00
Overall status: `PASS`
Claim status: `rdf_shacl_style_validation_pass_not_human_gold`

This report exports the Layer 2 CAPE-KG graph to Turtle and validates the current JSONL graph against the same predicate, evidence, and domain/range constraints used by the pipeline. It is structural validation evidence, not human-gold performance evidence.

## Outputs

- RDF/Turtle: `outputs/12_rdf/cape_kg_layer2.ttl`
- Runtime shapes: `outputs/12_rdf/cape_kg_runtime_shapes.shacl.ttl`
- Summary JSON: `outputs/12_rdf/cape_kg_shacl_validation_summary.json`
- Report: `outputs/12_rdf/cape_kg_shacl_validation_report.md`

## Summary

| Item | Value |
|---|---:|
| node_count | 220 |
| edge_count | 947 |
| node_type_count | 10 |
| predicate_type_count | 12 |
| allowed_predicate_count | 27 |
| domain_range_rule_count | 17 |
| evidence_anchor_catalog_count | 5009 |
| used_evidence_anchor_count | 451 |
| rdf_statement_count | 19690 |
| error_count | 0 |
| warning_count | 0 |

## Issue Counts

- No validation issues.

## Public Release Note

The RDF export is placed under `outputs/12_rdf` rather than `06_release` because KG labels and definitions are source-derived internal artifacts. The export intentionally omits full evidence sentence text.
