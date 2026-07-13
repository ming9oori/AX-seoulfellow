# CAPE-KG Prompt, Node, and Edge Traceability

Generated: 2026-06-29T18:55:34.133786+00:00
Experiment: `experiments/cape_kg_eacl_20260627`
Outputs: `outputs`

## 핵심 해석

- 최종 Layer 2 KG는 LLM 출력물을 그대로 저장한 결과가 아니라, OCR evidence anchor, task seed, 용어 사전, 절차 템플릿, schema validator로 조립한 rule/schema/evidence 기반 graph입니다.
- LLM 산출물은 baseline/proposed/ablation 조건별 prediction이며, 최종 성능 claim은 human-gold annotation 이후에만 가능합니다.
- 이 문서는 어떤 프롬프트/조건이 어떤 JSON key를 산출했고, 최종 node/edge가 어떤 규칙으로 생성되었는지를 추적하기 위한 release artifact입니다.

## Runtime Prompt 공통 제약

- Return ONLY one valid JSON object; no markdown and no explanation.
- Each item must use evidence_anchor_ids from the current chunk sentence_ids.
- Do not use outside knowledge.
- Keep Korean labels when the source text is Korean.
- Schema-constrained conditions receive allowed node types and allowed edge predicates.
- CAPE conditions impose hard limits of at most 5 nodes, 5 edges, and 3 mappings per chunk.
- Strict JSON runs prepend a JSON-only contract and /no_think instruction for Qwen-style chat models.

## 프롬프트/조건별 산출물 매핑

| condition | family | prompt_file | output | intent |
| --- | --- | --- | --- | --- |
| B0_plain_llm | baseline | `experiments/cape_kg_eacl_20260627/02_schema/prompts/B0_plain_llm_triple_extraction.txt` | `triples` | Schema 없이 subject-predicate-object triple을 직접 추출한다. |
| B1_predicate_constrained | baseline | `experiments/cape_kg_eacl_20260627/02_schema/prompts/B1_predicate_constrained_llm.txt` | `edges` | CAPE-KG 허용 predicate만 사용해 edge 후보를 추출한다. |
| B2_current_project | baseline | `experiments/cape_kg_eacl_20260627/02_schema/prompts/B2_current_project_baseline.txt` | `nodes`, `edges` | Task frame을 먼저 추론한 뒤 Layer 2 schema의 node/edge로 후처리한다. |
| B3_edc_style | baseline | `experiments/cape_kg_eacl_20260627/02_schema/prompts/B3_edc_style_baseline.txt` | `nodes`, `edges` | Open-schema item을 추출, 정의, canonicalize한 뒤 CAPE-compatible node/edge로 변환한다. |
| B4_taxonomy_rag | baseline | `experiments/cape_kg_eacl_20260627/02_schema/prompts/B4_taxonomy_rag_baseline.txt` | `nodes`, `edges`, `mappings` | NCS/PCF/task taxonomy snippet을 retrieval context로 제공하고 KG 후보와 mapping 후보를 추출한다. |
| B5_procedural_prompt | baseline | `experiments/cape_kg_eacl_20260627/02_schema/prompts/B5_procedural_prompt_baseline.txt` | `nodes`, `edges` | Action, actor, gateway, guard condition, artifact flow, dependency를 절차형으로 추출한다. |
| B6_sac_kg_verifier_pruner | baseline | `experiments/cape_kg_eacl_20260627/02_schema/prompts/B6_sac_kg_verifier_pruner_baseline.txt` | `nodes`, `edges` | 기존 generator 후보에 schema/evidence verifier와 pruning을 적용하는 SAC-KG-style approximation이다. |
| P_cape_kg_actual | proposed | `experiments/cape_kg_eacl_20260627/02_schema/prompts/P_cape_kg.txt` | `nodes`, `edges`, `mappings` | CQ anchoring, evidence grounding, procedural schema, validator, NCS/PCF bridge를 결합한다. |
| P_minus_CQ | ablation | runtime condition only | `nodes`, `edges`, `mappings` | 제안 방법론에서 competency-question anchoring을 제거한다. |
| P_minus_Evidence | ablation | runtime condition only | `nodes`, `edges`, `mappings` | 제안 방법론에서 evidence anchor 요구를 약화한다. |
| P_minus_Procedural_schema | ablation | runtime condition only | `nodes`, `edges`, `mappings` | 절차형 schema 대신 flat non-procedural schema를 사용한다. |
| P_minus_Validator | ablation | runtime condition only | `nodes`, `edges`, `mappings` | Post-hoc validator rejection 없이 모델의 schema 선택을 더 허용한다. |
| P_minus_Standard_bridge | ablation | runtime condition only | `nodes`, `edges` | NCS/PCF taxonomy bridge 출력을 제거한다. |
| P_minus_Schema_retrieval | ablation | `experiments/cape_kg_eacl_20260627/02_schema/prompts/P_minus_Schema_retrieval.txt` | `nodes`, `edges`, `mappings` | Chunk-specific CQ/schema/taxonomy retrieval을 제거하고 full schema 목록만 사용한다. |

## 실제 프롬프트 파일 원문

아래 원문은 `experiments/cape_kg_eacl_20260627/02_schema/prompts/`에 저장된 프롬프트 파일 내용입니다. 실제 LLM 호출 때는 이 조건별 원문에 runtime template, chunk sentence, sentence id, allowed schema, JSON shape가 결합됩니다.

| condition | prompt_file | prompt_text |
| --- | --- | --- |
| B0_plain_llm | `experiments/cape_kg_eacl_20260627/02_schema/prompts/B0_plain_llm_triple_extraction.txt` | `Extract subject-predicate-object triples from the chunk. Return JSON only.` |
| B1_predicate_constrained | `experiments/cape_kg_eacl_20260627/02_schema/prompts/B1_predicate_constrained_llm.txt` | `Extract triples using only the allowed predicates. Return JSON only with evidence sentence ids.` |
| B2_current_project | `experiments/cape_kg_eacl_20260627/02_schema/prompts/B2_current_project_baseline.txt` | `Extract Task Frames, then triples, then post-process into the Layer2 schema.` |
| B3_edc_style | `experiments/cape_kg_eacl_20260627/02_schema/prompts/B3_edc_style_baseline.txt` | `Extract, define, and canonicalize open-schema KG items, then emit CAPE-compatible nodes and edges for scoring.` |
| B4_taxonomy_rag | `experiments/cape_kg_eacl_20260627/02_schema/prompts/B4_taxonomy_rag_baseline.txt` | `Retrieve NCS/PCF/task taxonomy snippets, then extract schema-constrained triples with evidence.` |
| B5_procedural_prompt | `experiments/cape_kg_eacl_20260627/02_schema/prompts/B5_procedural_prompt_baseline.txt` | `Extract actions, actors, gateways, guard conditions, artifact flows, and temporal/logical dependencies.` |
| B6_sac_kg_verifier_pruner | `experiments/cape_kg_eacl_20260627/02_schema/prompts/B6_sac_kg_verifier_pruner_baseline.txt` | `Use existing generator candidates, then apply schema/evidence verification and pruning in the style of SAC-KG. This is a deterministic approximation, not a full SAC-KG reproduction.` |
| P_cape_kg_actual | `experiments/cape_kg_eacl_20260627/02_schema/prompts/P_cape_kg.txt` | `Use CQ-linked schema retrieval, procedural frame extraction, evidence-span constrained relation extraction, span verification, ontology validation, procedural consistency checks, and active review scoring.` |
| P_minus_CQ | runtime condition only |  |
| P_minus_Evidence | runtime condition only |  |
| P_minus_Procedural_schema | runtime condition only |  |
| P_minus_Validator | runtime condition only |  |
| P_minus_Standard_bridge | runtime condition only |  |
| P_minus_Schema_retrieval | `experiments/cape_kg_eacl_20260627/02_schema/prompts/P_minus_Schema_retrieval.txt` | `Run CAPE-KG without chunk-specific schema/taxonomy retrieval; keep CQ, evidence grounding, procedural schema, validation, and mapping output shape.` |

## Competency Question 생성 방식과 예시

- CQ는 LLM이 자동 생성한 것이 아니라 연구자가 정의한 KG 요구사항입니다.
- 수주/제안 업무 절차를 task, step, input, output, role, decision, guard, artifact flow, evidence, NCS/PCF mapping 질문으로 분해했습니다.
- 각 CQ를 target predicate 또는 required KG element에 연결해 schema, LLM prompt, validation, CQ answerability evaluation에 재사용했습니다.

CQ source files:

- Experiment CQ: `experiments/cape_kg_eacl_20260627/02_schema/competency_questions.json`
- Internal build CQ: `outputs/03_schema/competency_questions.json`
- CQ/schema generation code: `scripts/build_ax_epak_internal_kg.py`, `scripts/build_cape_kg_eacl_experiment.py`

| cq_id | question | target_predicates |
| --- | --- | --- |
| CQ1 | 수주·제안 업무는 어떤 주요 Task와 절차 단계로 구성되는가? | `HAS_STEP`, `PRECEDES` |
| CQ2 | 각 Task는 어떤 입력 자료를 사용하는가? | `USES_INPUT` |
| CQ3 | 각 Task는 어떤 산출물을 생성하는가? | `PRODUCES` |
| CQ4 | 각 Task는 누가 수행하거나 책임지는가? | `PERFORMED_BY` |
| CQ5 | 어떤 의사결정 지점이 존재하는가? | `HAS_DECISION_GATEWAY` |
| CQ6 | 의사결정에는 어떤 조건이나 판단 기준이 필요한가? | `HAS_GUARD_CONDITION` |
| CQ7 | 산출물은 다음 업무에서 어떻게 사용되는가? | `FEEDS_INTO`, `USED_AS_INPUT_FOR` |
| CQ8 | 제안서 리뷰는 어떤 단계에서 어떻게 수행되는가? | `HAS_REVIEW_CHECKPOINT` |
| CQ9 | 각 업무에서 지켜야 할 원칙은 무엇인가? | `HAS_PRINCIPLE` |
| CQ10 | 각 지식 항목은 원문 어느 chunk/page/span에 근거가 있는가? | `EVIDENCED_BY` |
| CQ11 | 특정 업무는 어떤 NCS 능력단위와 관련되는가? | `REQUIRES_CAPABILITY`, `CANDIDATE_ALIGNS_WITH` |
| CQ12 | 특정 업무는 PCF 프로세스 체계상 어디에 위치하는가? | `PROCESS_CONTEXT`, `CANDIDATE_ALIGNS_WITH` |

## LLM Validated Output 수량

Source valid files:

- `experiments/cape_kg_eacl_20260627/49_qwen3_8b_strict_json_1200_full_valid.jsonl`
- `experiments/cape_kg_eacl_20260627/49_sac_kg_verifier_pruner_baseline_valid.jsonl`

| condition | valid_rows | triples | nodes | edges | mappings |
| --- | --- | --- | --- | --- | --- |
| B0_plain_llm | 120 | 1037 | 0 | 0 | 0 |
| B1_predicate_constrained | 120 | 0 | 0 | 805 | 0 |
| B2_current_project | 120 | 0 | 867 | 334 | 0 |
| B3_edc_style | 120 | 0 | 769 | 263 | 0 |
| B4_taxonomy_rag | 120 | 0 | 719 | 323 | 126 |
| B5_procedural_prompt | 120 | 0 | 1307 | 302 | 0 |
| B6_sac_kg_verifier_pruner | 120 | 0 | 2281 | 361 | 107 |
| P_cape_kg_actual | 120 | 0 | 576 | 373 | 227 |
| P_minus_CQ | 120 | 0 | 586 | 391 | 233 |
| P_minus_Evidence | 120 | 0 | 574 | 383 | 227 |
| P_minus_Procedural_schema | 120 | 0 | 558 | 353 | 212 |
| P_minus_Schema_retrieval | 120 | 0 | 568 | 417 | 216 |
| P_minus_Standard_bridge | 120 | 0 | 577 | 405 | 0 |
| P_minus_Validator | 120 | 0 | 570 | 375 | 229 |

## 최종 KG Node 생성 방식

- Final nodes: 220
- Nodes with evidence: 220 / 220

| node_type | count | generation_rule |
| --- | --- | --- |
| ProcedureStep | 99 | task별 procedure template 또는 입력/산출물 기반 step 추론으로 생성 |
| ReviewCheckpoint | 41 | 검토/리뷰/점검/승인/확인 신호가 있는 ProcedureStep에서 별도 checkpoint node로 투영 |
| DomainTask | 22 | TASK_SEEDS의 label/alias/keyword로 OCR sentence evidence를 검색해 생성 |
| Artifact | 14 | task evidence 안의 입력물/산출물 용어 매칭으로 생성 |
| GuardCondition | 13 | 의사결정 evidence에서 조건/가능성/경쟁/자원 등 조건 표현을 정규식으로 추출 |
| Role | 10 | 수행자/책임 주체 용어 매칭으로 생성 |
| ArtifactFlow | 9 | 특정 산출물이 다음 task 입력으로 쓰이는 규칙에서 생성 |
| Principle | 5 | 원칙/품질 기준 용어 매칭으로 생성 |
| DecisionGateway | 4 | 의사결정 관련 용어 매칭으로 생성 |
| Risk | 3 | 위험/불리함/실패 가능성 용어 매칭으로 생성 |

## 최종 KG Edge 생성 방식

- Final edges: 947
- Edges with evidence: 947 / 947
- Edges with `source_triple_ids`: 947 / 947
- Dangling edges: 0

| predicate | count | generation_rule |
| --- | --- | --- |
| PRODUCES | 220 | task/step의 outputs slot을 Artifact node로 연결 |
| USES_INPUT | 201 | task/step의 inputs slot을 Artifact 또는 Concept node로 연결 |
| PERFORMED_BY | 120 | task/step의 roles slot을 Role node로 연결 |
| HAS_STEP | 99 | DomainTask를 해당 ProcedureStep 목록에 연결 |
| PRECEDES | 77 | 같은 task 안에서 step order 기준으로 순서 연결 |
| HAS_PRINCIPLE | 64 | task/step의 principles slot을 Principle node로 연결 |
| HAS_DECISION_GATEWAY | 54 | task/step에서 발견된 의사결정 node를 연결 |
| HAS_REVIEW_CHECKPOINT | 41 | 검토/리뷰/점검/승인/확인 신호가 있는 ProcedureStep을 ReviewCheckpoint node로 연결 |
| HAS_RISK | 39 | task/step의 risks slot을 Risk node로 연결 |
| HAS_GUARD_CONDITION | 14 | DecisionGateway에서 추출된 조건 node를 연결 |
| FEEDS_INTO | 9 | Artifact가 다음 task로 흘러가는 규칙을 연결 |
| USED_AS_INPUT_FOR | 9 | Artifact가 다음 task 입력으로 사용되는 규칙을 연결 |

## 중간 산출물 연결

| 단계 | 파일 | 현재 수량 |
|---|---|---:|
| Task frame | `outputs/04_task_frames/canonical_task_catalog.json` | 22 |
| Procedure structure | `outputs/05_procedure/procedure_structures_clean.jsonl` | 22 procedures / 99 steps |
| Schema-valid triple | `outputs/06_triples/layer2_triples_schema_valid.jsonl` | 947 |
| Final nodes | `outputs/07_layer2_graph/layer2_nodes.jsonl` | 220 |
| Final edges | `outputs/07_layer2_graph/layer2_edges.jsonl` | 947 |

## 주의

- 이 산출물은 재현성과 설명 가능성을 위한 traceability 문서입니다.
- LLM output quantity는 성능 우수성을 뜻하지 않습니다.
- Precision/recall/F1 main table은 adjudicated human-gold가 들어온 뒤 다시 계산해야 합니다.
