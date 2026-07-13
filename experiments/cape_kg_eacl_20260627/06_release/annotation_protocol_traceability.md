# CAPE-KG Annotation Protocol Traceability

Generated: 2026-06-29T18:56:33.422620+00:00
Claim status: `annotation_protocol_traceability_ready_pending_human_returns`
Plan: `AX_EACL_submission_review_revised_plan.md`

This artifact maps the revised plan's annotation requirements to the prepared human-gold protocol, batch assignments, IAA/adjudication placeholders, validation summaries, and human-return gates.
It is a workflow traceability artifact, not human-gold performance evidence.

## Summary

- plan_target_count: `10`
- covered_plan_target_count: `10`
- minimum_chunk_target: `100`
- minimum_gold_item_target: `500`
- batch_count: `5`
- assigned_chunks: `100`
- candidate_edges_total: `1371`
- minimum_required_return_file_count: `11`
- minimum_required_return_file_present_count: `0`
- completed_pair_chunks: `0`
- pending_pair_chunks: `120`
- adjudicated_chunks: `0`
- gold_item_count: `0`
- packet_integrity_error_count: `0`
- handoff_bundle_count: `9`
- missing_handoff_bundle_count: `0`
- iaa_status: `pending_human_annotations`
- adjudication_claim_status: `draft_not_final_human_gold`
- human_gold_claim_status: `pending_human_adjudication`

## Plan Annotation Targets

| target_id | plan_requirement | protocol_coverage | evidence_artifacts | current_status |
| --- | --- | --- | --- | --- |
| T01_task_or_procedure_step | Task 또는 ProcedureStep 표시 | Guideline node type table and gold_node_fields cover DomainTask and ProcedureStep. | annotation_guideline_v1.md; annotation_schema.json | covered_by_protocol_pending_human_annotation |
| T02_artifact | Artifact 표시 | Guideline node type table and gold_node_fields cover Artifact. | annotation_guideline_v1.md; annotation_schema.json | covered_by_protocol_pending_human_annotation |
| T03_role | Role 표시 | Guideline node type table and gold_node_fields cover Role. | annotation_guideline_v1.md; annotation_schema.json | covered_by_protocol_pending_human_annotation |
| T04_decision_gateway | DecisionGateway 표시 | Guideline node type table and gold_node_fields cover DecisionGateway. | annotation_guideline_v1.md; annotation_schema.json | covered_by_protocol_pending_human_annotation |
| T05_guard_condition | GuardCondition 표시 | Guideline node type table and gold_node_fields cover GuardCondition. | annotation_guideline_v1.md; annotation_schema.json | covered_by_protocol_pending_human_annotation |
| T06_review_checkpoint | ReviewCheckpoint 표시 | Guideline node type table covers ReviewCheckpoint; current KG projects review/check/approval-signaled ProcedureStep nodes as ReviewCheckpoint. | annotation_guideline_v1.md; cq_query_pack.md; prompt_node_edge_traceability.md; structural_evaluation_metrics.json | covered_by_protocol_and_current_kg_projection_pending_human_annotation |
| T07_principle_or_risk | Principle/Risk 표시 | Guideline node type table and predicate table cover Principle and Risk. | annotation_guideline_v1.md; annotation_schema.json | covered_by_protocol_pending_human_annotation |
| T08_edge_type | Edge type 표시 | Guideline predicate table and gold_edge_fields require predicate, source, target, and decision. | annotation_guideline_v1.md; annotation_schema.json | covered_by_protocol_pending_human_annotation |
| T09_evidence_span | Evidence span 표시 | Guideline evidence section and gold_edge_fields require evidence_anchor_ids and evidence_spans. | annotation_guideline_v1.md; annotation_schema.json; human_gold_span_iou_report.md | covered_by_protocol_pending_human_annotation |
| T10_page_and_chunk_id | page/chunk ID 표시 | Batch/template records retain chunk_id and page metadata; annotators must not modify package identity. | annotation_guideline_v1.md; annotation_batch_assignment_summary.json; human_review_master_return_files.csv | covered_by_protocol_pending_human_annotation |

## Human-Gold Workflow Traceability

| workflow_id | stage | evidence | current_status | gate_effect |
| --- | --- | --- | --- | --- |
| W01_schema_and_guideline | Annotation schema and guideline | annotation_schema.json; annotation_guideline_v1.md | ready | Defines allowed node/edge/evidence fields before human annotation. |
| W02_batch_assignment | Priority-100 two-annotator batch assignment | annotation_batch_assignment_summary.json | 100/100 minimum chunks assigned | Prepares the minimum 100-chunk paper gate inputs. |
| W03_independent_annotation | Independent annotator A/B returns | human_gate_required_returns.csv | 0/11 minimum return files present | Unlocks IAA, adjudication, and human-gold scoring only after returns exist. |
| W04_iaa | Inter-annotator agreement | iaa_full_120/iaa_summary.json | 0/100 paired chunks completed | Blocks edge F1/type agreement/span IoU reporting until paired annotation exists. |
| W05_adjudication | Adjudication | full_120/adjudication_draft_summary.json | 0/100 adjudicated chunks | Blocks final gold labels and paper main table until adjudication is complete. |
| W06_human_gold_validation | Human-gold validation | human_gold_validation_summary.json | 0/500 adjudicated items | Requires 100+ chunks, 500+ items, and zero validation errors for minimum claim readiness. |
| W07_proposed_human_gold_scoring | P_cape_kg_actual human-gold scoring | human_gold_metrics.json | pending_human_adjudication | Final proposed-method F1 remains unavailable before adjudicated gold. |
| W08_mapping_expert_review | NCS/PCF mapping expert review | human_gate_required_returns.csv; mapping_expert_metrics.json | 0/1 expert return files present | Blocks mapping P@K/MRR/nDCG and accept-rate claims. |
| W09_crosswalk_expert_review | NCS-PCF crosswalk expert review | human_gate_required_returns.csv; crosswalk_expert_metrics.json | 0/1 expert return files present | Blocks crosswalk utility and ranking claims. |
| W10_active_review_effort | Active-review human-effort evidence | human_gate_required_returns.csv; active_review_human_effort_report.md | 0/1 effort return files present | Blocks active-review efficiency and human-effort reduction claims. |

## Return File Summary

| task_type | rows | present | missing |
| --- | --- | --- | --- |
| active_review_human_effort | 1 | 0 | 1 |
| crosswalk_expert_review | 1 | 0 | 1 |
| human_gold_adjudication | 1 | 0 | 1 |
| human_gold_annotation | 10 | 0 | 10 |
| mapping_expert_review | 1 | 0 | 1 |

## Human-Gold Gate Boundary

- Safe scope: Use as an internal traceability map from revised-plan annotation requirements to prepared annotation protocol, batches, IAA/adjudication placeholders, and claim gates.
- Not claimable: This artifact does not satisfy human-gold annotation, IAA, adjudication, final extraction F1, mapping expert review, crosswalk utility, or active-review efficiency claims.
- Human/expert gated: `True`
- Current gate status: `pending_human_annotations`

## Gate Dependency Snapshot

| gate_id | gate_type | required_for_minimum | claim_status | current_progress | blocking_return_file_count |
| --- | --- | --- | --- | --- | --- |
| min.iaa | minimum_accept | yes | pending_human | 0/10 annotation reviewed files present; 0/100 paired completed chunks. | 10 |
| min.gold_chunks | minimum_accept | yes | pending_human | 0/100 adjudicated chunks. | 11 |
| min.gold_items | minimum_accept | yes | pending_human | 0/500 adjudicated node/edge/evidence items in current validation summary. | 11 |
| min.proposed | minimum_accept | yes | partial | P_cape_kg_actual generated for 120 rows; human-gold scored conditions=[] until adjudication exists. | 1 |
| mapping.expert_review | optional_strong | no | pending_expert_review | 0/44 source-task-standard groups complete; 0/20 priority Top-5 groups complete; 220 candidate rows pending. | 1 |
| crosswalk.expert_review | optional_strong | no | pending_crosswalk_expert_review | 0/22 source-task groups complete; 0/220 rows complete. | 1 |
| strong.active_review_effort | strong_or_auxiliary | no | pending_human_effort_timing | 0/204 reviewed rows; 0 timed rows. | 1 |

## Source Artifacts

| role | path | exists | bytes |
| --- | --- | --- | --- |
| revised EACL plan | AX_EACL_submission_review_revised_plan.md | True | 29461 |
| human-gold annotation guideline | experiments/cape_kg_eacl_20260627/01_data/annotation_guideline_v1.md | True | 12652 |
| human-gold schema | experiments/cape_kg_eacl_20260627/01_data/gold_annotation/annotation_schema.json | True | 741 |
| priority-100 batch assignment summary | experiments/cape_kg_eacl_20260627/06_release/annotation_batch_assignment_summary.json | True | 21447 |
| handoff bundle integrity summary | experiments/cape_kg_eacl_20260627/06_release/human_review_packet_integrity.json | True | 14261 |
| IAA summary | experiments/cape_kg_eacl_20260627/01_data/gold_annotation/iaa_full_120/iaa_summary.json | True | 444 |
| adjudication draft summary | experiments/cape_kg_eacl_20260627/01_data/gold_annotation/full_120/adjudication_draft_summary.json | True | 1113 |
| human-gold validation summary | experiments/cape_kg_eacl_20260627/04_evaluation/human_gold_validation_summary.json | True | 848 |
| human-gold metric output | experiments/cape_kg_eacl_20260627/04_evaluation/human_gold_metrics.json | True | 1509 |
| required human-return manifest | experiments/cape_kg_eacl_20260627/05_review/human_gate_required_returns.csv | True | 7485 |
| claim gate dependency matrix | experiments/cape_kg_eacl_20260627/05_review/human_review_gate_dependency_matrix.csv | True | 13358 |
| claim gate report | experiments/cape_kg_eacl_20260627/06_release/claim_gate_report.json | True | 16096 |
| final Layer 2 edge output | outputs/07_layer2_graph/layer2_edges.jsonl | True | 331827 |

## Interpretation

- The plan target coverage is complete at the protocol/workflow level: all ten annotation target categories are represented in guideline/schema/gate artifacts.
- The paper minimum is not yet satisfied because human annotator returns, IAA, adjudication, and human-gold scoring are still pending.
- Mapping, crosswalk, and active-review efficiency claims remain expert/human-return gated.
