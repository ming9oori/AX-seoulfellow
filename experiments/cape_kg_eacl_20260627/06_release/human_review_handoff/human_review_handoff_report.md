# CAPE-KG Human Review Handoff Report

Generated: 2026-06-29T18:56:34.243929+00:00
Claim status: `handoff_ready_pending_human_review`

## Annotation Handoff

### Annotator A

- Rows: 100
- Unique chunks: 100
- Candidate edges: 1371
- Ready for minimum gate: True
- Status counts: `{'pending_human_annotation': 100}`

### Annotator B

- Rows: 100
- Unique chunks: 100
- Candidate edges: 1371
- Ready for minimum gate: True
- Status counts: `{'pending_human_annotation': 100}`

## Optional Strong 300+ Review Handoff

- Package: `strong_resegmented_342_max18`
- Review units: 342
- Source chunks represented: 214
- Max source sentences per unit: 18
- Candidate edges: 2087
- Status: optional handoff ready; not a completed 300+ adjudicated-gold claim.

## Bundles

| bundle | path | sha256 | bytes | files |
|---|---|---|---:|---:|
| annotator_A | `experiments/cape_kg_eacl_20260627/06_release/human_review_handoff/cape_human_gold_annotator_A_priority100.tar.gz` | `28d47a6f9b479c054ddbc886fe15f365b8389f6183a34ce7a2170d894704c87e` | 431579 | 88 |
| annotator_B | `experiments/cape_kg_eacl_20260627/06_release/human_review_handoff/cape_human_gold_annotator_B_priority100.tar.gz` | `8ddd97bd64f4d2e0e381abb09ebd0cd46bfa3430a77a8dcc382a9001bb43da85` | 431580 | 88 |
| coordinator | `experiments/cape_kg_eacl_20260627/06_release/human_review_handoff/cape_human_gold_coordinator_priority100.tar.gz` | `26d98f4b8f1a663d940a9287ec4cb17c50004b5cb6b547054c6e522d219b9eca` | 679139 | 96 |
| adjudicator | `experiments/cape_kg_eacl_20260627/06_release/human_review_handoff/cape_human_gold_adjudicator_full120.tar.gz` | `718e5dfb9954cfa0b510d318f64a976ecda027d14f190bb0e7f22b21fffd3be6` | 284553 | 42 |
| mapping_expert | `experiments/cape_kg_eacl_20260627/06_release/human_review_handoff/cape_mapping_expert_review_top20_groups.tar.gz` | `838ace64502a71c04b4e9866230d1ab455307aefdd23a7a5b7fc5e0ea96a4329` | 148030 | 39 |
| crosswalk_expert | `experiments/cape_kg_eacl_20260627/06_release/human_review_handoff/cape_crosswalk_expert_review_ncs_pcf.tar.gz` | `36296fd089d95cab4ad3d6e4ecc1a514d2aeb2e31313b9e61a04d4854eade749` | 120421 | 37 |
| active_review_effort | `experiments/cape_kg_eacl_20260627/06_release/human_review_handoff/cape_active_review_human_effort.tar.gz` | `179c683580de5cd72acaeddd68c5fc882e6609bf3c1a8568c5474007da4bf5f1` | 136671 | 40 |
| structural_reviewer | `experiments/cape_kg_eacl_20260627/06_release/human_review_handoff/cape_structural_review_optional.tar.gz` | `6018d90a8ed5f5a9384cfc9a335553d79000e0512b8edbe45006da15878ab3d3` | 87208 | 41 |
| strong_resegmented_review | `experiments/cape_kg_eacl_20260627/06_release/human_review_handoff/cape_human_gold_strong_resegmented_342.tar.gz` | `7f5449d1df34fc4ac8c58eb058c4f5b52bcaaab5215cc98dba160841585446e0` | 1155271 | 57 |

## Notes

- These bundles are internal review handoffs and may contain source-derived chunk text.
- They do not satisfy human-gold, IAA, or adjudication gates by themselves.
- The structural reviewer bundle is optional and does not change the 11-file minimum paper gate.
- The strong resegmented review bundle is optional and does not change the 11-file minimum paper gate.
- After minimum review, validate returned files and run `scripts/run_cape_human_return_apply.sh`.
- After optional strong 300+ review, validate returned files and run `scripts/run_cape_strong_return_apply.sh`.
