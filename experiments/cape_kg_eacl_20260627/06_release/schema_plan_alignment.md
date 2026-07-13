# CAPE-KG Schema Plan Alignment

Generated: 2026-06-29T18:55:34.527583+00:00
Claim status: `schema_plan_alignment_ready_with_known_structural_gaps`

This report aligns the schema terms in `AX_EACL_submission_review_revised_plan.md` sections 7.1 and 7.2 with the current artifacts. It deliberately separates canonical Layer 2 graph terms from projection, mapping-candidate, and human-review worklist terms.

## Summary

| Item | Value |
|---|---:|
| Plan node types | 14 |
| Plan edge types | 16 |
| Canonical Layer 2 present terms | 21 |
| Projection or mapping represented terms | 8 |
| Pending structural review terms | 1 |
| Missing unclassified terms | 0 |

## Interpretation

- `canonical_layer2_present`: present directly in `layer2_nodes.jsonl` or `layer2_edges.jsonl`.
- `projection_present`: materialized in evidence projection, RDF/SHACL, or Neo4j export rather than canonical Layer 2 JSONL.
- `mapping_projection_present` / `represented_as_candidate_rows`: standard-bridge candidates exist but remain pending expert review.
- `pending_structural_review`: known noncanonical gap prepared as a human structural review worklist.
- `missing_unclassified`: unexpected gap; validator should fail if this is nonzero.

## Alignment Rows

| kind | term | canonical_count | represented_count | status | represented_in | claim_scope |
|---|---|---:|---:|---|---|---|
| node_type | `DomainTask` | 22 | 22 | `canonical_layer2_present` | canonical_layer2_graph | canonical Layer 2 KG term |
| node_type | `ProcedureStep` | 99 | 99 | `canonical_layer2_present` | canonical_layer2_graph | canonical Layer 2 KG term |
| node_type | `DecisionGateway` | 4 | 4 | `canonical_layer2_present` | canonical_layer2_graph | canonical Layer 2 KG term |
| node_type | `GuardCondition` | 13 | 13 | `canonical_layer2_present` | canonical_layer2_graph | canonical Layer 2 KG term |
| node_type | `Artifact` | 14 | 14 | `canonical_layer2_present` | canonical_layer2_graph | canonical Layer 2 KG term |
| node_type | `ArtifactFlow` | 9 | 9 | `canonical_layer2_present` | canonical_layer2_graph | canonical Layer 2 KG term |
| node_type | `Role` | 10 | 10 | `canonical_layer2_present` | canonical_layer2_graph | canonical Layer 2 KG term |
| node_type | `ReviewCheckpoint` | 41 | 41 | `canonical_layer2_present` | canonical_layer2_graph | canonical Layer 2 KG term |
| node_type | `Principle` | 5 | 5 | `canonical_layer2_present` | canonical_layer2_graph | canonical Layer 2 KG term |
| node_type | `Risk` | 3 | 3 | `canonical_layer2_present` | canonical_layer2_graph | canonical Layer 2 KG term |
| node_type | `EvidenceAnchor` | 0 | 451 | `projection_present` | evidence_projection | noncanonical EvidenceAnchor projection; final span correctness remains human-gold pending |
| node_type | `NCSCompetencyUnit` | 0 | 3450 | `layer1_standard_present` | layer1_ncs_graph_and_mapping_targets | Layer 1 standard taxonomy node type |
| node_type | `PCFElement` | 0 | 2017 | `layer1_standard_present` | layer1_pcf_graph_and_mapping_targets | Layer 1 standard taxonomy node type |
| node_type | `MappingCandidate` | 0 | 220 | `represented_as_candidate_rows` | mapping_candidate_rows | candidate-only standard bridge pending expert review |
| edge_type | `HAS_STEP` | 99 | 99 | `canonical_layer2_present` | canonical_layer2_graph | canonical Layer 2 KG predicate |
| edge_type | `PRECEDES` | 77 | 77 | `canonical_layer2_present` | canonical_layer2_graph | canonical Layer 2 KG predicate |
| edge_type | `BRANCHES_TO` | 0 | 4 | `pending_structural_review` | structural_review_worklist | known schema gap tracked for human structural review |
| edge_type | `HAS_GUARD_CONDITION` | 14 | 14 | `canonical_layer2_present` | canonical_layer2_graph | canonical Layer 2 KG predicate |
| edge_type | `USES_INPUT` | 201 | 201 | `canonical_layer2_present` | canonical_layer2_graph | canonical Layer 2 KG predicate |
| edge_type | `PRODUCES` | 220 | 220 | `canonical_layer2_present` | canonical_layer2_graph | canonical Layer 2 KG predicate |
| edge_type | `FEEDS_INTO` | 9 | 9 | `canonical_layer2_present` | canonical_layer2_graph | canonical Layer 2 KG predicate |
| edge_type | `PERFORMED_BY` | 120 | 120 | `canonical_layer2_present` | canonical_layer2_graph | canonical Layer 2 KG predicate |
| edge_type | `HAS_DECISION_GATEWAY` | 54 | 54 | `canonical_layer2_present` | canonical_layer2_graph | canonical Layer 2 KG predicate |
| edge_type | `HAS_REVIEW_CHECKPOINT` | 41 | 41 | `canonical_layer2_present` | canonical_layer2_graph | canonical Layer 2 KG predicate |
| edge_type | `HAS_PRINCIPLE` | 64 | 64 | `canonical_layer2_present` | canonical_layer2_graph | canonical Layer 2 KG predicate |
| edge_type | `HAS_RISK` | 39 | 39 | `canonical_layer2_present` | canonical_layer2_graph | canonical Layer 2 KG predicate |
| edge_type | `EVIDENCED_BY` | 0 | 3915 | `projection_present` | evidence_projection_and_neo4j_export | noncanonical evidence projection; final span correctness remains human-gold pending |
| edge_type | `REQUIRES_CAPABILITY` | 0 | 110 | `mapping_projection_present` | mapping_projection_and_neo4j_export | candidate-only NCS mapping pending expert review |
| edge_type | `PROCESS_CONTEXT` | 0 | 110 | `mapping_projection_present` | mapping_projection_and_neo4j_export | candidate-only PCF mapping pending expert review |
| edge_type | `CANDIDATE_ALIGNS_WITH` | 0 | 440 | `represented_as_candidate_rows` | mapping_candidate_rows_and_crosswalk_candidates | generic plan relation represented by standard-specific mapping rows pending expert review |

## Known Structural Review Terms

| term | evidence | note |
|---|---|---|
| `BRANCHES_TO` | `experiments/cape_kg_eacl_20260627/04_evaluation/structural_gap_worklist_summary.json`, `experiments/cape_kg_eacl_20260627/05_review/structural_gateway_branch_gaps.csv` | Decision gateways are present, but explicit branch outcomes are pending structural review. |

## Claim Safety

- This report does not change the canonical KG.
- It prevents overclaiming that every plan schema term is already present as a canonical Layer 2 node or edge.
- Mapping and crosswalk rows remain candidate-only until expert review returns are imported.
- Review checkpoint terms are canonical when present, but their correctness remains pending human-gold review.
- Branch terms remain structural-review worklist items until human review confirms source-supported branch outcomes.
