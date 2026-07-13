# CAPE-KG Method Novelty Positioning

Generated: 2026-06-29T18:56:35.483366+00:00
Experiment: `experiments/cape_kg_eacl_20260627`
Outputs: `outputs`

This artifact explains what the proposed CAPE-KG pipeline adds beyond common LLM-KG, ontology-guided, taxonomy-RAG, procedural-prompt, and verifier/pruner baselines.
It is a claim-safe positioning artifact: it supports method framing and reproducibility, but it does not replace human-gold evaluation.

## Summary

- Claim status: `method_novelty_positioning_ready_final_gain_pending_human_gold`
- Method modules tracked: 11
- Missing required method artifacts: 0
- LLM condition metric rows: 14
- CQs: 12/12 answerable by current graph-query diagnostics
- Current Layer 2 KG: 220 nodes, 947 edges

## Prior-Work Positioning Matrix

| prior-work family | representative condition | what it covers | what CAPE-KG adds | current evidence | claim boundary |
| --- | --- | --- | --- | --- | --- |
| Plain LLM triple extraction / Text2KG-style extraction | `B0_plain_llm` | Open subject-predicate-object extraction from each chunk. | Typed task/procedure nodes, allowed predicates, evidence anchors, CQ-linked schema, and validators. | valid rows=120; nodes=1674; edges=0; triples=837; mappings=0; predicate F1=0.0000; evidence F1=0.0239 | Current values are silver/proxy diagnostics; final quality gains need adjudicated human-gold scoring. |
| Predicate-constrained LLM KG extraction | `B1_predicate_constrained` | Relation extraction with an allowed predicate list. | Node typing, procedural task frames, evidence span tracking, CQ answerability, and standard-taxonomy mapping. | valid rows=120; nodes=0; edges=663; triples=0; mappings=0; predicate F1=0.1416; evidence F1=0.0291 | Predicate control alone is diagnostic, not a final proposed-method claim. |
| Current project baseline / task-frame post-processing | `B2_current_project` | Task-frame extraction followed by Layer 2 schema post-processing. | Full CAPE pipeline adds CQ retrieval, evidence grounding, validators, ablations, and NCS/PCF bridge. | valid rows=120; nodes=712; edges=82; triples=0; mappings=0; predicate F1=0.0068; evidence F1=0.0503 | Useful as an internal baseline; final comparison requires human-gold metrics. |
| EDC-style open-schema extraction and canonicalization | `B3_edc_style` | Extract, define, and canonicalize open-schema items before schema-compatible scoring. | Procedural KG schema, CQ-linked query needs, evidence span checks, and release-time claim gates. | valid rows=120; nodes=566; edges=53; triples=0; mappings=0; predicate F1=0.0119; evidence F1=0.0311 | Baseline approximation is available; do not claim superiority until human-gold scoring. |
| Taxonomy-RAG / ontology-guided KG extraction | `B4_taxonomy_rag` | Retrieval of taxonomy snippets before extracting schema-constrained nodes, edges, and mappings. | CAPE treats NCS/PCF as downstream bridge evidence, connects it to procedural KG nodes, and tracks expert-review readiness. | valid rows=120; nodes=674; edges=128; triples=0; mappings=41; predicate F1=0.0105; evidence F1=0.0641 | Mapping utility requires expert labels before paper claims. |
| Procedural prompt / workflow extraction | `B5_procedural_prompt` | Action, actor, gateway, guard condition, artifact flow, and dependency extraction. | CQ anchoring, schema validation, evidence anchoring, structural diagnostics, and KG query package. | valid rows=120; nodes=957; edges=119; triples=0; mappings=0; predicate F1=0.0096; evidence F1=0.0603 | Procedural structure is built and diagnosable; correctness still needs human adjudication. |
| SAC-KG-style verifier/pruner | `B6_sac_kg_verifier_pruner` | Generate candidate nodes/edges, then verify and prune using schema/evidence constraints. | End-to-end CQ/procedural/mapping/release-gate pipeline rather than verifier/pruner alone. | valid rows=120; nodes=2281; edges=361; triples=0; mappings=107; predicate F1=0.0774; evidence F1=0.1008 | This is a deterministic approximation baseline, not a full reproduction of an external system. |
| CAPE-KG proposed method | `P_cape_kg_actual` | CQ-linked schema retrieval, procedural extraction, evidence grounding, validation, and standard bridge. | This is the proposed integrated method rather than a single extraction component. | valid rows=120; nodes=549; edges=275; triples=0; mappings=52; predicate F1=0.0482; evidence F1=0.0655 | Implemented and traceable now; final performance claim remains pending human-gold scoring. |

## Module-to-Novelty Map

| innovation axis | modules | implementation | ablation/diagnostic | current status |
| --- | --- | --- | --- | --- |
| Competency-question anchored extraction | `M2, M3` | CQs define what the KG must answer, then guide schema/predicate retrieval and CQ query-pack evaluation. | P_minus_CQ and P_minus_Schema_retrieval isolate CQ anchoring and schema-retrieval effects. | 12/12 CQs answerable by current KG query diagnostics. |
| Evidence-grounded procedural KG construction | `M4, M5, M6` | Task/procedure frames are converted into typed nodes and edges with evidence anchors and component-span diagnostics. | P_minus_Evidence tests evidence grounding; evidence span granularity metrics diagnose span quality. | final nodes=220; final edges=947; component span exact rate=0.2612 |
| Ontology and procedural consistency validation | `M7, M8` | Domain/range, predicate, dangling-edge, precedence, gateway, and artifact-flow checks are explicit release artifacts. | P_minus_Validator and structural evaluation isolate validator/constraint contributions. | dangling edges=0; precedence cycles=0 |
| Standard taxonomy bridge | `M11` | Layer 2 procedural tasks are connected to NCS/PCF candidate mappings and NCS-PCF crosswalk candidates. | P_minus_Standard_bridge removes the standard bridge output for ablation. | Candidate mappings exist; downstream utility and accept-rate claims require expert review. |
| Active review and claim-safety gates | `M10` | Risky chunks and likely high-impact errors are queued for human review, while release gates prevent overclaiming. | Active-review ablation metrics and human-effort template separate automatic prioritization from human-time claims. | Automatic queue is ready; effort/time claims require returned human effort sheet. |

### Evidence Files by Innovation Axis

#### Competency-question anchored extraction
- `experiments/cape_kg_eacl_20260627/06_release/cq_query_pack.md`
- `experiments/cape_kg_eacl_20260627/06_release/prompt_node_edge_traceability.md`
- `outputs/03_schema/competency_questions.json`

#### Evidence-grounded procedural KG construction
- `experiments/cape_kg_eacl_20260627/06_release/prompt_node_edge_traceability.md`
- `experiments/cape_kg_eacl_20260627/04_evaluation/evidence_span_granularity_report.md`
- `outputs/06_triples/layer2_triples_component_spans.jsonl`

#### Ontology and procedural consistency validation
- `experiments/cape_kg_eacl_20260627/04_evaluation/structural_evaluation_report.md`
- `outputs/12_rdf/cape_kg_shacl_validation_report.md`
- `experiments/cape_kg_eacl_20260627/06_release/structural_review_action_plan.md`

#### Standard taxonomy bridge
- `outputs/08_mapping/l2_ncs_mapping_candidates.jsonl`
- `outputs/08_mapping/l2_pcf_mapping_candidates.jsonl`
- `experiments/cape_kg_eacl_20260627/04_evaluation/ncs_pcf_crosswalk_report.md`

#### Active review and claim-safety gates
- `experiments/cape_kg_eacl_20260627/04_evaluation/active_review_efficiency_report.md`
- `experiments/cape_kg_eacl_20260627/06_release/claimable_main_table.md`
- `experiments/cape_kg_eacl_20260627/06_release/pre_human_handoff_validation.md`

## What Can Be Claimed Now

| claim | evidence | safe scope |
| --- | --- | --- |
| The CAPE-KG pipeline has implemented artifacts for M1-M11. | modules=11; missing required artifacts=0 | Implementation and reproducibility setup claim. |
| The current corpus has a built Layer 2 procedural KG. | nodes=220; edges=947; edges with evidence=947 | Built KG artifact claim, not human-validated extraction-quality claim. |
| Baseline/proposed/ablation conditions are traceable. | condition metrics=14; prompt inventory=14 | Experimental setup and silver/proxy diagnostic claim. |
| CQs are connected to concrete graph queries. | CQs=12; answerable=12; rate=1.0000 | CQ query-package readiness, not final answer correctness. |

## What Cannot Be Claimed Yet

| claim to defer | required next evidence |
| --- | --- |
| CAPE-KG improves extraction quality over all baselines. | Adjudicated human-gold labels, IAA, and human-gold metrics for proposed and baseline conditions. |
| NCS/PCF mapping candidates are useful for downstream expert work. | Expert-reviewed mapping/crosswalk labels and recomputed P@K, MRR, nDCG, accept rate, and utility scores. |
| Active review reduces human effort in practice. | Returned human effort sheet with time/correction outcomes and refreshed active-effort metrics. |
| The package is submission complete. | All minimum human-gold gates and proposed-method human-gold scoring must pass the claim gate. |

## Source Files

| role | path | exists | bytes |
| --- | --- | ---: | ---: |
| M1-M11 module coverage | `experiments/cape_kg_eacl_20260627/06_release/method_module_coverage.json` | True | 46695 |
| M1-M11 module coverage report | `experiments/cape_kg_eacl_20260627/06_release/method_module_coverage.md` | True | 17555 |
| prompt/output traceability | `experiments/cape_kg_eacl_20260627/06_release/prompt_node_edge_traceability.json` | True | 24271 |
| prompt/output traceability report | `experiments/cape_kg_eacl_20260627/06_release/prompt_node_edge_traceability.md` | True | 13157 |
| CQ query pack | `experiments/cape_kg_eacl_20260627/06_release/cq_query_pack.json` | True | 53053 |
| silver/proxy baseline diagnostics | `experiments/cape_kg_eacl_20260627/04_evaluation/actual_llm_silver_metrics.json` | True | 15122 |
| structural diagnostics | `experiments/cape_kg_eacl_20260627/04_evaluation/structural_evaluation_metrics.json` | True | 22053 |
| evidence span diagnostics | `experiments/cape_kg_eacl_20260627/04_evaluation/evidence_span_granularity_metrics.json` | True | 1822 |
