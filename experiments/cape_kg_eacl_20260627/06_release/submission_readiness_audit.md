# CAPE-KG Submission Readiness Audit

Generated: 2026-06-29T18:55:31.977060+00:00
Source plan: `AX_EACL_submission_review_revised_plan.md`
Experiment: `experiments/cape_kg_eacl_20260627`

Claim status: **pending_human_gold_iaa_and_human_gold_scoring**

This audit maps the revised EACL plan to current files. It does not treat silver/proxy diagnostics as human-gold evidence.

## Summary

- Total audited items: 20
- Claimable items: 12
- Minimum-accept blocking items: 4
- Strong-accept human-blocking items: 4
- Status counts: `{'pending_human': 5, 'pass': 11, 'partial': 4}`

## Requirement Table

| id | category | status | claimable | requirement | next step |
|---|---|---:|---:|---|---|
| min.gold_chunks | minimum_accept | pending_human | no | 100+ adjudicated gold chunks | Complete two-annotator labeling and adjudication for at least 100 chunks. |
| min.gold_items | minimum_accept | pending_human | no | 500+ adjudicated gold node/edge/evidence items | Adjudicate enough nodes, edges, and evidence anchors to reach 500 gold items. |
| min.iaa | minimum_accept | pending_human | no | 2+ annotators and agreement for 100+ chunks | Import completed annotator A/B files and recompute IAA. |
| min.gold_sampling_ready | minimum_accept | pass | yes | Priority-100 gold subset sampling ready | No additional automatic step required; priority-100 sampling covers 1371/1436 full-120 candidate edges (0.9547), active-review coverage=0.9670, high-impact coverage=1.0000. Human annotation/adjudication still required. |
| min.baselines | minimum_accept | pass | yes | B0/B1/B2 actual LLM baselines completed | No additional automatic step required; keep baseline artifacts synchronized. |
| min.proposed | minimum_accept | partial | no | CAPE-KG proposed result completed and scored | Score P_cape_kg_actual against adjudicated human gold after gold completion. |
| min.ablations | minimum_accept | pass | yes | 3+ actual ablations completed | No additional automatic step required; ablation coverage satisfies the minimum gate. |
| min.error_analysis | minimum_accept | pass | yes | Structured error analysis table and taxonomy | No additional automatic step required; update only if new diagnostics change. |
| min.public_subset | minimum_accept | pass | yes | Public benchmark or public subset experiment | No additional automatic step required; public subset evidence is present. |
| min.release_plan | minimum_accept | pass | yes | Code, prompt, schema, and reproducibility release package | No additional automatic step required; regenerate only after source artifacts change. |
| min.limitations | minimum_accept | pass | yes | Limitations section | No additional automatic step required; keep limitations synchronized with future human results. |
| min.public_synthetic_examples | minimum_accept | pass | yes | Public-safe synthetic examples for reproducibility mitigation | No additional automatic step required; synthetic public-safe examples are ready. |
| strong.gold_chunks | strong_accept | pending_human | no | 300-500 adjudicated gold chunks | Use `strong_resegmented_342_max18` for optional 300+ two-annotator review and adjudication; do not claim 300+ adjudicated chunks until reviewed returns are imported. |
| strong.gold_items | strong_accept | pending_human | no | 1,500+ adjudicated gold edge/evidence items | Complete optional 300+ two-annotator review and adjudication until at least 1,500 gold edge/evidence items are available. |
| strong.public_cross | strong_accept | pass | yes | PAGED/Text2KGBench cross experiment | No additional automatic step required; cross-check includes PAGED >= 100 and Text2KG >= 200 in a single run. |
| strong.edc_taxonomy_baselines | strong_accept | pass | yes | EDC/SAC-KG/Taxonomy-RAG family baselines or reproductions | No additional automatic step required; B3/B4/B6 family baseline artifacts are present. |
| strong.mapping_downstream | strong_accept | partial | no | NCS/PCF mapping downstream evaluation | Complete expert review for mapping candidates and crosswalk candidates before making P@K/MRR/nDCG@10, explanation-quality, accept-rate, or utility claims. |
| strong.active_review | strong_accept | partial | no | Active review efficiency evaluation | Collect reviewed active-review human-effort CSV and validate efficiency against human adjudication outcomes. |
| strong.visualization | strong_accept | pass | yes | Visualization/demo provided | No additional automatic step required; keep the viewer synchronized with future graph updates. |
| method.m1_m11 | method_modules | partial | yes | CAPE-KG M1-M11 modules represented by executable artifacts | All executable module artifacts are present; human-review and human-gold scoring evidence remains required for final paper claims. |

## Blocking Minimum-Accept Items

- min.gold_chunks: 100+ adjudicated gold chunks -> Complete two-annotator labeling and adjudication for at least 100 chunks.
- min.gold_items: 500+ adjudicated gold node/edge/evidence items -> Adjudicate enough nodes, edges, and evidence anchors to reach 500 gold items.
- min.iaa: 2+ annotators and agreement for 100+ chunks -> Import completed annotator A/B files and recompute IAA.
- min.proposed: CAPE-KG proposed result completed and scored -> Score P_cape_kg_actual against adjudicated human gold after gold completion.

## Strong-Accept Human-Dependent Items

- strong.gold_chunks: 300-500 adjudicated gold chunks -> Use `strong_resegmented_342_max18` for optional 300+ two-annotator review and adjudication; do not claim 300+ adjudicated chunks until reviewed returns are imported.
- strong.gold_items: 1,500+ adjudicated gold edge/evidence items -> Complete optional 300+ two-annotator review and adjudication until at least 1,500 gold edge/evidence items are available.
- strong.mapping_downstream: NCS/PCF mapping downstream evaluation -> Complete expert review for mapping candidates and crosswalk candidates before making P@K/MRR/nDCG@10, explanation-quality, accept-rate, or utility claims.
- strong.active_review: Active review efficiency evaluation -> Collect reviewed active-review human-effort CSV and validate efficiency against human adjudication outcomes.
