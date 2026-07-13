# CAPE-KG Alias/Canonicalization Diagnostic Report

Generated: 2026-06-29T18:55:40.449314+00:00

This report documents the current M9 alias/canonicalization artifacts. It is a diagnostic artifact, not human-gold node matching evidence.

## Claim Boundary

- Claim status: `alias_canonicalization_diagnostic_ready_pending_human_gold_node_matching`
- Diagnostic only: automatic alias coverage and collision queue.
- Pending human-gold node matching: final canonicalization precision, recall, and merge/split correctness are not yet claimable.
- Collision review required: alias collisions are preserved as a review queue, not silently resolved.

## Summary

| metric | value |
| --- | --- |
| Layer 2 nodes | 220 |
| Layer 2 edges | 947 |
| Canonical task catalog entries | 22 |
| Alias dictionary entries | 122 |
| Alias collision groups | 13 |
| Ambiguous multi-node collision groups | 6 |
| Duplicate-reference-only groups | 7 |
| Graph quality collision count | 13 |
| Duplicate alias references | 8 |
| Nodes with aliases | 44 |
| Node alias coverage rate | 0.200000 |

## Node Alias Coverage

| metric | value |
| --- | --- |
| nodes_with_aliases | 44 |
| nodes_without_aliases | 176 |
| raw_node_alias_total | 136 |
| unique_node_alias_total | 128 |
| duplicate_alias_within_node_total | 8 |
| duplicate_label_group_count | 21 |

## Canonical Task Catalog

| metric | value |
| --- | --- |
| catalog_review_status | auto_catalog_pending_human_review |
| canonical_task_count | 22 |
| canonical_tasks_with_aliases | 22 |
| canonical_task_alias_coverage_rate | 1.000000 |
| raw_canonical_task_alias_total | 51 |
| unique_canonical_task_alias_total | 51 |
| missing_task_ids_from_layer2_nodes | 0 |

## Alias Dictionary Diagnostics

| metric | value |
| --- | --- |
| alias_entry_count | 122 |
| raw_alias_reference_count | 136 |
| unique_alias_reference_count | 128 |
| duplicate_alias_reference_count | 8 |
| collision_alias_count | 13 |
| ambiguous_collision_alias_count | 6 |
| duplicate_reference_only_group_count | 7 |
| missing_node_reference_count | 0 |

## Collision Review Queue

Full CSV: `experiments/cape_kg_eacl_20260627/04_evaluation/alias_canonicalization_collision_groups.csv`

| alias | collision_kind | target_count | node_types | review_status |
| --- | --- | --- | --- | --- |
| bid validation decision | cross_type_collision | 2 | DecisionGateway,DomainTask | pending_human_node_matching_review |
| bid/no bid decision | duplicate_reference_only | 1 | DomainTask | pending_human_node_matching_review |
| capture planning | duplicate_reference_only | 1 | DomainTask | pending_human_node_matching_review |
| kickoff meeting | duplicate_reference_only | 1 | DomainTask | pending_human_node_matching_review |
| opportunity assessment | duplicate_reference_only | 1 | DomainTask | pending_human_node_matching_review |
| proposal planning | duplicate_reference_only | 1 | DomainTask | pending_human_node_matching_review |
| proposal writing | duplicate_reference_only | 1 | DomainTask | pending_human_node_matching_review |
| red team review | duplicate_reference_only | 1 | DomainTask | pending_human_node_matching_review |
| 영업참여 결정 | cross_type_collision | 2 | DecisionGateway,DomainTask | pending_human_node_matching_review |
| 요구조건 | cross_type_collision | 2 | Principle,Risk | pending_human_node_matching_review |
| 입찰타당성 결정 | cross_type_collision | 2 | DecisionGateway,DomainTask | pending_human_node_matching_review |
| 참여결정 | cross_type_collision | 2 | DecisionGateway,DomainTask | pending_human_node_matching_review |
| 참여타당성 검증 | cross_type_collision | 2 | DecisionGateway,DomainTask | pending_human_node_matching_review |

## B3 EDC-Style Baseline Footprint

| condition | rows | nodes | edges | mappings | triples |
| --- | --- | --- | --- | --- | --- |
| B3_edc_style | 120 | 566 | 53 | 0 | 0 |
| P_minus_Schema_retrieval | 120 | 566 | 308 | 25 | 0 |

## Inputs

- `layer2_nodes`: `outputs/07_layer2_graph/layer2_nodes.jsonl`
- `layer2_edges`: `outputs/07_layer2_graph/layer2_edges.jsonl`
- `alias_dictionary`: `outputs/07_layer2_graph/layer2_alias_dictionary.json`
- `layer2_graph_quality_report`: `outputs/07_layer2_graph/layer2_graph_quality_report.md`
- `canonical_task_catalog`: `outputs/04_task_frames/canonical_task_catalog.json`
- `b3_edc_schema_ablation_valid`: `experiments/cape_kg_eacl_20260627/49_qwen3_8b_edc_schema_ablation_valid.jsonl`
