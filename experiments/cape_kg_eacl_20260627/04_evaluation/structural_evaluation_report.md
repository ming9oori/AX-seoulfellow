# CAPE-KG Structural Evaluation

Generated: 2026-06-29T18:55:36.830809+00:00
Claim status: `kg_structural_diagnostic_not_human_gold`

This report evaluates the current built KG structure. It is not a replacement for human-gold scoring.

## Summary

| Metric | Value |
|---|---:|
| Nodes | 220 |
| Edges | 947 |
| Ontology conformance rate | 1.0 |
| Domain/range violations | 0 |
| Dangling edges | 0 |
| Evidence-missing edges | 0 |
| Procedural consistency rate | 0.995283 |
| Procedural edges | 844 |
| PRECEDES cycle count | 0 |
| Gateway without branch | 4 |
| Gateway without guard | 0 |
| Artifact-flow direction violations | 0 |
| CQ answerability rate | 1.0 |
| Answerable CQs | 12 / 12 |

## CQ Answerability

| CQ | support count | answerable | support source | predicates |
|---|---:|---:|---|---|
| CQ1 | 176 | yes | `layer2_edges` | `HAS_STEP,PRECEDES` |
| CQ2 | 201 | yes | `layer2_edges` | `USES_INPUT` |
| CQ3 | 220 | yes | `layer2_edges` | `PRODUCES` |
| CQ4 | 120 | yes | `layer2_edges` | `PERFORMED_BY` |
| CQ5 | 54 | yes | `layer2_edges` | `HAS_DECISION_GATEWAY` |
| CQ6 | 14 | yes | `layer2_edges` | `HAS_GUARD_CONDITION` |
| CQ7 | 18 | yes | `layer2_edges` | `FEEDS_INTO,USED_AS_INPUT_FOR` |
| CQ8 | 41 | yes | `layer2_edges` | `HAS_REVIEW_CHECKPOINT` |
| CQ9 | 64 | yes | `layer2_edges` | `HAS_PRINCIPLE` |
| CQ10 | 947 | yes | `edge.evidence_anchor_ids` | `EVIDENCED_BY` |
| CQ11 | 110 | yes | `l2_ncs_mapping_candidates.jsonl` | `REQUIRES_CAPABILITY,CANDIDATE_ALIGNS_WITH` |
| CQ12 | 110 | yes | `l2_pcf_mapping_candidates.jsonl` | `PROCESS_CONTEXT,CANDIDATE_ALIGNS_WITH` |

## Interpretation

- Ontology conformance checks node types, predicates, dangling edges, domain/range constraints, and evidence-anchor presence.
- Procedural consistency checks PRECEDES cycles, gateway branch/guard availability, and artifact-flow direction.
- CQ answerability is structural: a CQ is answerable if at least one supporting predicate exists in the current KG.
- Human-gold evaluation must still recompute these metrics against adjudicated labels before final paper claims.
