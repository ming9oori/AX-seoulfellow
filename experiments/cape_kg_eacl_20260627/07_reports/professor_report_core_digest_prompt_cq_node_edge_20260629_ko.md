# 교수님 보고용 핵심 요약본: 프롬프트, CQ, Node/Edge 산출 방식

Generated: 2026-06-29  
Experiment directory: `experiments/cape_kg_eacl_20260627`  
KG output directory: `outputs`

이 문서는 `professor_report_slide_contents_current_20260628_ko.md`와 별개로 만든 **핵심 내용 중심 별도 요약본**입니다. 장문 슬라이드 원고가 아니라, 교수님께 먼저 설명해야 할 방법론의 뼈대만 빠르게 확인하기 위한 문서입니다.

핵심 질문은 네 가지입니다.

1. 어떤 방법론으로 연구를 진행했는가?
2. 어떤 프롬프트와 CQ를 사용했는가?
3. node와 edge는 각각 어떤 방식으로 산출했는가?
4. 현재까지 어떤 실험이 완료되었고, 무엇은 아직 claim하면 안 되는가?

---

## 1. 한 문장 요약

본 연구는 한국어 수주/제안 업무 문서에서 `DomainTask`, `ProcedureStep`, `Artifact`, `Role`, `DecisionGateway`, `GuardCondition`, `Risk` 등을 원문 sentence evidence에 연결한 **evidence-grounded procedural KG**를 구축하고, 이를 NCS/PCF 표준 taxonomy와 연결하는 CAPE-KG 방법론을 적용한 실험입니다.

가장 중요한 구분은 다음입니다.

| 구분 | 현재 상태 | 발표 시 표현 |
| --- | --- | --- |
| KG 구축 | 완료 | Layer 1 표준 KG와 Layer 2 업무 KG가 생성됨 |
| LLM 실험 | 실행 완료 | baseline/proposed/ablation/model scaling 산출물 준비 |
| 최종 성능 claim | 아직 불가 | human-gold, IAA, adjudication, expert review 전 |

즉, **KG 구축과 실험 인프라는 완료되었지만, 논문용 최종 F1 claim은 사람 검수 이후에만 가능**합니다.

---

## 2. 현재까지의 핵심 산출물

| 항목 | 현재 값 |
| --- | ---: |
| OCR evidence anchors | 5,009 |
| Layer 1 NCS nodes | 4,109 |
| Layer 1 PCF nodes | 5,301 |
| Layer 2 KG nodes | 220 |
| Layer 2 KG edges | 947 |
| Canonical DomainTask | 22 |
| ProcedureStep | 99 |
| NCS mapping candidates | 110 |
| PCF mapping candidates | 110 |
| NCS-PCF crosswalk candidates | 220 |
| Evaluation chunks for LLM experiments | 120 |
| LLM experiment conditions | 14 |

핵심 파일은 다음입니다.

| 목적 | 파일 |
| --- | --- |
| 최종 Layer 2 node | `outputs/07_layer2_graph/layer2_nodes.jsonl` |
| 최종 Layer 2 edge | `outputs/07_layer2_graph/layer2_edges.jsonl` |
| NCS mapping 후보 | `outputs/08_mapping/l2_ncs_mapping_candidates.jsonl` |
| PCF mapping 후보 | `outputs/08_mapping/l2_pcf_mapping_candidates.jsonl` |
| KG viewer | `outputs/09_visualization/kg_viewer.html` |
| 최종 build report | `outputs/10_evaluation/final_build_report.md` |
| 프롬프트/node/edge traceability | `experiments/cape_kg_eacl_20260627/06_release/prompt_node_edge_traceability.md` |
| 실험 재현 카드 | `experiments/cape_kg_eacl_20260627/06_release/experiment_reproduction_card.md` |
| claim 가능성 table | `experiments/cape_kg_eacl_20260627/06_release/claimable_main_table.md` |

---

## 3. 방법론 전체 흐름

이번 연구에서 최종 KG는 LLM 출력물을 그대로 저장한 결과가 아닙니다. 실제 흐름은 다음과 같습니다.

1. OCR workbook을 sentence 단위로 정제
2. 각 sentence에 evidence anchor ID 부여
3. NCS/PCF taxonomy를 Layer 1 표준 KG로 구축
4. 업무 문서를 chunk 단위로 나누고 evaluation chunk 120개 구성
5. Competency Question(CQ)와 procedural schema 설계
6. task seed, alias, keyword, evidence sentence를 이용해 task frame 생성
7. task frame에서 step, artifact, role, decision, guard, risk 후보 생성
8. predicate별 규칙으로 triple과 edge 생성
9. source node, target node, predicate, evidence 조건을 검증
10. 통과한 node/edge만 최종 Layer 2 KG에 저장
11. NCS/PCF mapping 후보와 NCS-PCF crosswalk 후보 생성
12. LLM baseline/proposed/ablation/model scaling 실험 실행
13. structural diagnostics, claim gate, human-review handoff 생성

따라서 이 연구의 핵심은 **LLM으로 KG를 한 번에 만든 것**이 아니라, **CQ, schema, evidence, validator, standard bridge로 LLM 및 규칙 기반 산출물을 통제 가능한 KG construction task로 만든 것**입니다.

---

## 4. CQ는 어떻게 만들었는가

CQ는 LLM이 자동 생성한 것이 아니라, 연구자가 먼저 정의한 **KG 요구사항**입니다. 즉, "이 KG가 어떤 질문에 답할 수 있어야 하는가"를 정한 뒤, 그 질문을 node type과 edge predicate에 연결했습니다.

생성 절차는 다음과 같습니다.

| 단계 | 내용 |
| --- | --- |
| 연구 문제 정의 | 한국어 수주/제안 문서에서 절차형 업무 KG를 구축 |
| 질문 범주 설정 | 업무 구성, 절차 순서, 입력, 산출물, 역할, 의사결정, 조건, 위험, evidence, 표준 연결 |
| schema 연결 | 각 CQ를 `DomainTask`, `ProcedureStep`, `Artifact`, `Role`, `DecisionGateway` 등과 연결 |
| predicate 연결 | 각 CQ를 `HAS_STEP`, `USES_INPUT`, `PRODUCES`, `PERFORMED_BY` 등과 연결 |
| 실험 재사용 | schema, prompt, ablation, structural evaluation에서 같은 CQ 목록 사용 |

관련 파일:

| 역할 | 파일 |
| --- | --- |
| EACL 실험용 CQ | `experiments/cape_kg_eacl_20260627/02_schema/competency_questions.json` |
| 내부 KG build용 CQ | `outputs/03_schema/competency_questions.json` |
| LLM runtime prompt 코드 | `scripts/run_cape_llm_condition_baselines.py` |
| KG build 코드 | `scripts/build_ax_epak_internal_kg.py`, `scripts/build_cape_kg_eacl_experiment.py` |

---

## 5. CQ 실제 목록

| CQ | 질문 | 연결 predicate |
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

해석 예시는 다음입니다.

| CQ | 실제 설계 효과 |
| --- | --- |
| CQ2, CQ3 | input/output을 분리해야 하므로 `Artifact`, `USES_INPUT`, `PRODUCES`를 둠 |
| CQ5, CQ6 | 의사결정과 조건을 분리해야 하므로 `DecisionGateway`, `GuardCondition`을 둠 |
| CQ7 | 산출물이 다음 업무의 입력이 되는 흐름을 표현하기 위해 `FEEDS_INTO`, `USED_AS_INPUT_FOR`를 둠 |
| CQ11, CQ12 | Layer 2 업무 KG를 NCS/PCF 표준과 연결하는 bridge를 둠 |
| `P_minus_CQ` | CQ anchoring을 제거했을 때 제안 방법론의 효과가 어떻게 달라지는지 보기 위한 ablation |

---

## 6. 실제 프롬프트 파일 원문

프롬프트 파일 위치는 다음입니다.

`experiments/cape_kg_eacl_20260627/02_schema/prompts/`

저장된 프롬프트 원문은 다음과 같습니다.

| 조건 | 프롬프트 파일 | 실제 저장된 prompt text |
| --- | --- | --- |
| B0_plain_llm | `B0_plain_llm_triple_extraction.txt` | `Extract subject-predicate-object triples from the chunk. Return JSON only.` |
| B1_predicate_constrained | `B1_predicate_constrained_llm.txt` | `Extract triples using only the allowed predicates. Return JSON only with evidence sentence ids.` |
| B2_current_project | `B2_current_project_baseline.txt` | `Extract Task Frames, then triples, then post-process into the Layer2 schema.` |
| B3_edc_style | `B3_edc_style_baseline.txt` | `Extract, define, and canonicalize open-schema KG items, then emit CAPE-compatible nodes and edges for scoring.` |
| B4_taxonomy_rag | `B4_taxonomy_rag_baseline.txt` | `Retrieve NCS/PCF/task taxonomy snippets, then extract schema-constrained triples with evidence.` |
| B5_procedural_prompt | `B5_procedural_prompt_baseline.txt` | `Extract actions, actors, gateways, guard conditions, artifact flows, and temporal/logical dependencies.` |
| B6_sac_kg_verifier_pruner | `B6_sac_kg_verifier_pruner_baseline.txt` | `Use existing generator candidates, then apply schema/evidence verification and pruning in the style of SAC-KG. This is a deterministic approximation, not a full SAC-KG reproduction.` |
| P_cape_kg_actual | `P_cape_kg.txt` | `Use CQ-linked schema retrieval, procedural frame extraction, evidence-span constrained relation extraction, span verification, ontology validation, procedural consistency checks, and active review scoring.` |
| P_minus_Schema_retrieval | `P_minus_Schema_retrieval.txt` | `Run CAPE-KG without chunk-specific schema/taxonomy retrieval; keep CQ, evidence grounding, procedural schema, validation, and mapping output shape.` |
| strict_json_contract | `strict_json_contract.txt` | JSON object만 반환, markdown/code fence/comment/XML/`<think>`/설명 금지, `/no_think`, compact JSON 사용 |

주의할 점은, 위 `.txt` 파일의 한 줄 지시문만 LLM에 들어간 것이 아니라는 점입니다. 실제 실행 시에는 `scripts/run_cape_llm_condition_baselines.py`의 `build_condition_prompt()`가 아래 정보를 함께 붙였습니다.

```text
Return ONLY one valid JSON object. No markdown. No explanation.
Every extracted item must include at least one evidence_anchor_ids value from the chunk.
Do not use outside knowledge. Keep Korean labels when the source text is Korean.

Chunk metadata:
chunk_id: {chunk_id}
pages: {page_start}..{page_end}
sentence_ids: {sentence_ids}

Chunk sentences:
{sentence_block}
```

strict JSON 실행에서는 system/user prompt에 다음 제약이 추가되었습니다.

```text
System:
You are a JSON-only evidence-grounded information extraction function.

Strict JSON contract:
- Return exactly one JSON object and nothing else.
- The first non-whitespace character must be `{` and the last non-whitespace character must be `}`.
- Do not include markdown, code fences, comments, XML tags, <think> blocks, prose, or explanations.
- For Qwen/Qwen-style chat models, obey `/no_think`; do not emit hidden or visible reasoning.

User:
/no_think
...
/no_think
Return exactly one compact JSON object now.
```

---

## 7. 제안 방법론 prompt의 핵심 구조

`P_cape_kg_actual` 조건은 CQ, evidence, procedural schema, validator, NCS/PCF bridge를 모두 결합한 제안 조건입니다.

실제 runtime prompt의 핵심 구조는 다음과 같습니다.

```text
You are running the P_cape_kg_actual CAPE-KG condition.
Extract a domain procedural knowledge graph from the chunk.

Competency questions:
- CQ1: Identify major bid/proposal tasks and procedural steps.
- CQ2: Identify input artifacts used by each task.
- CQ3: Identify output artifacts produced by each task.
- CQ4: Identify roles responsible for each task.
- CQ5: Identify decision gateways.
- CQ6: Identify guard conditions for decisions or branches.
- CQ7: Identify artifact flows between tasks.
- CQ8: Identify review checkpoints.
- CQ9: Identify principles and risks.
- CQ10: Attach every accepted item to evidence in the chunk.
- CQ11: Link task labels to NCS capability candidates when supported.
- CQ12: Link task labels to PCF process candidates when supported.

Taxonomy snippets:
{NCS/PCF/task taxonomy retrieval context}

Rules:
- Every node, edge, and mapping must include evidence_anchor_ids from the chunk.
- Use only the listed node types and edge predicates. Invalid schema terms will be rejected.
- Do not use outside knowledge.
- Keep Korean labels when the source text is Korean.
- Prefer concise, reusable labels.
- Hard limit: return at most 5 nodes, at most 5 edges, and at most 3 mappings.
- If the chunk does not support a field, return an empty array for that field.
```

제안 조건에서 요구한 JSON shape는 다음입니다.

```json
{
  "nodes": [
    {
      "label": "string",
      "type": "node type",
      "evidence_anchor_ids": ["sentence ids"],
      "confidence": 0.0
    }
  ],
  "edges": [
    {
      "subject": "string",
      "subject_type": "node type",
      "predicate": "edge predicate",
      "object": "string",
      "object_type": "node type",
      "evidence_anchor_ids": ["sentence ids"],
      "confidence": 0.0
    }
  ],
  "mappings": [
    {
      "source_task": "text-supported task label",
      "standard": "NCS|PCF",
      "target_label": "taxonomy label from snippets",
      "evidence_anchor_ids": ["sentence ids"],
      "confidence": 0.0
    }
  ]
}
```

핵심은 LLM이 자유롭게 KG를 만들지 못하도록 했다는 점입니다. 반드시 chunk 안의 sentence ID를 evidence로 달고, 허용된 node type과 edge predicate 안에서 JSON을 반환하도록 제한했습니다.

---

## 8. 조건별 LLM 산출물

최신 재현 카드 기준으로 14개 조건이 실행 또는 재현 가능 상태입니다. 모든 조건은 120 evaluation chunks 기준입니다.

| 조건 | family | 출력 key | rows | nodes | edges | triples | mappings | claim status |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| B0_plain_llm | baseline | `triples` | 120 | 1,674 | 0 | 837 | 0 | silver/proxy only |
| B1_predicate_constrained | baseline | `edges` | 120 | 0 | 663 | 0 | 0 | silver/proxy only |
| B2_current_project | baseline | `nodes`, `edges` | 120 | 712 | 82 | 0 | 0 | silver/proxy only |
| B3_edc_style | baseline | `nodes`, `edges` | 120 | 566 | 53 | 0 | 0 | silver/proxy only |
| B4_taxonomy_rag | baseline | `nodes`, `edges`, `mappings` | 120 | 674 | 128 | 0 | 41 | silver/proxy only |
| B5_procedural_prompt | baseline | `nodes`, `edges` | 120 | 957 | 119 | 0 | 0 | silver/proxy only |
| B6_sac_kg_verifier_pruner | baseline | `nodes`, `edges`, `mappings` | 120 | 2,281 | 361 | 0 | 107 | silver/proxy only |
| P_cape_kg_actual | proposed | `nodes`, `edges`, `mappings` | 120 | 549 | 275 | 0 | 52 | silver/proxy only |
| P_minus_CQ | ablation | `nodes`, `edges`, `mappings` | 120 | 554 | 284 | 0 | 35 | silver/proxy only |
| P_minus_Evidence | ablation | `nodes`, `edges`, `mappings` | 120 | 514 | 259 | 0 | 64 | silver/proxy only |
| P_minus_Procedural_schema | ablation | `nodes`, `edges`, `mappings` | 120 | 528 | 247 | 0 | 72 | silver/proxy only |
| P_minus_Schema_retrieval | ablation | `nodes`, `edges`, `mappings` | 120 | 566 | 308 | 0 | 25 | silver/proxy only |
| P_minus_Standard_bridge | ablation | `nodes`, `edges` | 120 | 572 | 338 | 0 | 0 | silver/proxy only |
| P_minus_Validator | ablation | `nodes`, `edges`, `mappings` | 120 | 557 | 271 | 0 | 63 | silver/proxy only |

이 표는 **산출량과 재현 상태**를 설명하기 위한 표입니다. 많이 뽑았다고 성능이 좋다는 뜻은 아니며, human-gold 전까지는 최종 성능표로 쓰면 안 됩니다.

---

## 9. 최종 KG node는 어떻게 산출했는가

최종 `outputs/07_layer2_graph/layer2_nodes.jsonl`의 node는 LLM output을 그대로 저장한 것이 아닙니다. OCR evidence, task seed, alias/keyword, 용어 사전, procedure template을 결합해 생성했습니다.

Node 생성 흐름은 다음과 같습니다.

1. OCR sentence를 evidence anchor로 변환
2. `TASK_SEEDS`의 업무 seed label, alias, keyword로 관련 sentence 검색
3. 검색된 sentence에서 artifact, role, decision, principle, risk 후보 추출
4. task frame을 `DomainTask` node로 생성
5. task별 procedure template 또는 입력/산출물 기반 추론으로 `ProcedureStep` node 생성
6. 의사결정 표현에서 `DecisionGateway`와 `GuardCondition` 생성
7. 특정 산출물이 다음 task 입력으로 쓰이는 경우 `ArtifactFlow` 생성
8. `node_id` 기준으로 중복 제거
9. 모든 node에 evidence와 review status 부여

현재 node type별 개수는 다음입니다.

| Node type | 생성 방식 | 개수 |
| --- | --- | ---: |
| `DomainTask` | 업무 seed + evidence sentence 검색 | 22 |
| `ProcedureStep` | task별 procedure template 또는 입력/산출물 기반 step 추론 | 99 |
| `Artifact` | task evidence 안의 입력물/산출물 용어 매칭 | 14 |
| `Role` | 수행자/책임 주체 용어 매칭 | 10 |
| `DecisionGateway` | 의사결정 관련 용어 매칭 | 4 |
| `GuardCondition` | decision evidence에서 조건/가능성/경쟁/자원 표현 추출 | 13 |
| `Principle` | 원칙/품질 기준 용어 매칭 | 5 |
| `Risk` | 위험/불리함/실패 가능성 용어 매칭 | 3 |
| `ArtifactFlow` | 특정 산출물이 다음 task 입력으로 쓰이는 규칙 | 9 |

요약하면 node는 "업무 개념 자체"입니다. 예를 들면 `기회분석`, `Capture Plan`, `고객 정보 수집`, `제안서 리뷰`, `Bid/No-Bid 판단 조건` 같은 항목이 node가 됩니다.

---

## 10. 최종 KG edge는 어떻게 산출했는가

최종 `outputs/07_layer2_graph/layer2_edges.jsonl`의 edge는 node 사이 업무 관계를 predicate별 규칙으로 만든 뒤, source/target/evidence 검증을 통과한 것만 저장한 결과입니다.

Edge 생성 흐름은 다음과 같습니다.

1. task frame의 `inputs`, `outputs`, `roles`, `principles`, `risks` slot을 predicate로 변환
2. procedure step은 `HAS_STEP`, step 순서는 `PRECEDES`로 연결
3. task/step과 artifact는 `USES_INPUT`, `PRODUCES`로 연결
4. task/step과 role은 `PERFORMED_BY`로 연결
5. decision gateway와 guard condition은 `HAS_DECISION_GATEWAY`, `HAS_GUARD_CONDITION`으로 연결
6. artifact flow는 `FEEDS_INTO`, `USED_AS_INPUT_FOR`로 연결
7. 모든 edge에 `source_triple_ids`와 evidence anchor 부여
8. allowed predicate, source node 존재, target node 존재, evidence 존재 여부 검증
9. 검증을 통과한 edge만 final graph에 저장

현재 predicate별 edge 수는 다음입니다.

| Predicate | 생성 방식 | 개수 |
| --- | --- | ---: |
| `PRODUCES` | task/step의 outputs slot을 Artifact node로 연결 | 220 |
| `USES_INPUT` | task/step의 inputs slot을 Artifact node로 연결 | 201 |
| `PERFORMED_BY` | task/step의 roles slot을 Role node로 연결 | 120 |
| `HAS_STEP` | DomainTask를 해당 ProcedureStep 목록에 연결 | 99 |
| `PRECEDES` | 같은 task 안에서 step order 기준으로 순서 연결 | 77 |
| `HAS_PRINCIPLE` | task/step의 principles slot을 Principle node로 연결 | 64 |
| `HAS_DECISION_GATEWAY` | task/step에서 발견된 의사결정 node 연결 | 54 |
| `HAS_RISK` | task/step의 risks slot을 Risk node로 연결 | 39 |
| `HAS_GUARD_CONDITION` | DecisionGateway에서 추출된 조건 node 연결 | 14 |
| `FEEDS_INTO` | Artifact가 다음 task로 흘러가는 규칙 연결 | 9 |
| `USED_AS_INPUT_FOR` | Artifact가 다음 task 입력으로 사용되는 규칙 연결 | 9 |

검증 결과는 다음입니다.

| 검증 항목 | 결과 |
| --- | ---: |
| Final Layer 2 edges | 947 |
| Evidence가 있는 edges | 947 / 947 |
| `source_triple_ids`가 있는 edges | 947 / 947 |
| Dangling edges | 0 |
| Domain/range violations | 0 |
| Ontology conformance | 1.0000 |

요약하면 edge는 "업무 개념 사이의 관계"입니다. 예를 들면 `기회분석 USES_INPUT 시장 정보`, `제안서 작성 PRODUCES 제안서`, `검토 단계 PRECEDES 승인 단계` 같은 구조가 edge입니다.

---

## 11. Triple, node, edge의 관계

| 개념 | 의미 |
| --- | --- |
| Node | 업무 개념 자체 |
| Edge | node 사이 관계 |
| Triple | edge를 subject-predicate-object와 evidence로 평가하기 위한 중간 record |
| Evidence anchor | node/edge/triple이 근거로 삼은 OCR sentence |

중간 산출물의 연결은 다음과 같습니다.

| 단계 | 파일 | 현재 수량 |
| --- | --- | ---: |
| Task frame | `outputs/04_task_frames/canonical_task_catalog.json` | 22 |
| Procedure structure | `outputs/05_procedure/procedure_structures_clean.jsonl` | 22 procedures / 99 steps |
| Schema-valid triple | `outputs/06_triples/layer2_triples_schema_valid.jsonl` | 947 |
| Final nodes | `outputs/07_layer2_graph/layer2_nodes.jsonl` | 220 |
| Final edges | `outputs/07_layer2_graph/layer2_edges.jsonl` | 947 |

현재 triple 수와 edge 수가 947로 같은 이유는, 업무 관계를 SPO/evidence 형식으로 검증한 뒤 최종 graph edge로 저장했기 때문입니다.

---

## 12. 어떤 LLM을 사용했는가

현재 LLM은 주로 조건별 prediction generator로 사용했습니다.

| 모델 | 목적 | 상태 |
| --- | --- | --- |
| Qwen3-8B | 기본 baseline/proposed/ablation | 14개 조건 120 chunks 기준 실행 |
| Qwen3-14B | model scaling core conditions | 실행 완료 |
| Qwen3-32B-AWQ | 더 큰 모델의 현실적 scaling | core 4조건 x 120 chunks = 480 rows 완료 |

핵심 해석:

- Qwen3-8B는 기본 실험 조건 전체를 돌리는 기준 모델입니다.
- Qwen3-14B와 Qwen3-32B-AWQ는 모델 크기 변화에 따른 진단용 scaling입니다.
- 현재 scaling 결과도 human-gold 전이므로 **성능 우수성 claim이 아니라 diagnostic**입니다.

---

## 13. 현재 실험은 어디까지 완료되었는가

| 항목 | 상태 |
| --- | --- |
| Layer 1 NCS/PCF KG | 완료 |
| Layer 2 업무 KG | 완료 |
| Evidence grounding | 완료 |
| Neo4j/HTML/GraphML 시각화 산출물 | 준비됨 |
| NCS/PCF mapping 후보 | 완료, expert review 전 |
| NCS-PCF crosswalk 후보 | 완료, expert review 전 |
| LLM baseline/proposed/ablation | 완료 |
| Qwen3 model scaling | 완료 |
| Public benchmark adapter | 완료 |
| Human-review handoff | 준비 완료 |
| Pre-human validation | PASS, 92 checks 중 91 PASS / 1 WARN |
| Release bundle | 최신 index/checksum 기준 생성 및 검증 완료 |
| 최종 논문 성능표 | 아직 불가 |

최신 release bundle 확인 위치:

| 항목 | 파일 |
| --- | --- |
| 최신 bundle index | `experiments/cape_kg_eacl_20260627/06_release/latest_release_bundle_index.md` |
| release checksum | `experiments/cape_kg_eacl_20260627/06_release/release_bundle_checksums.sha256` |
| handoff checksum | `experiments/cape_kg_eacl_20260627/06_release/human_review_handoff/human_review_handoff_checksums.sha256` |

---

## 14. 현재 main table을 어떻게 봐야 하는가

현재 `claimable_main_table.md`는 있습니다. 다만 이것은 최종 논문 성능 main table이 아니라, **무엇을 claim할 수 있고 무엇을 아직 claim하면 안 되는지 구분하는 table**입니다.

현재 claim 가능한 것과 불가능한 것은 다음처럼 나뉩니다.

| 범주 | 현재 표현 가능 여부 | 이유 |
| --- | --- | --- |
| KG 구축 완료 | 가능 | node/edge/evidence/schema validation 완료 |
| 실험 조건 실행 완료 | 가능 | 14개 조건, 각 120 chunks 재현 카드 있음 |
| 구조 진단 | 가능하나 diagnostic으로만 | ontology conformance, CQ answerability 등 자동 진단 |
| silver/proxy metric | 가능하나 diagnostic으로만 | human-gold가 아니라 KG-derived silver reference 기준 |
| 최종 extraction F1 | 불가 | adjudicated human-gold 미완료 |
| mapping 정확도 | 불가 | expert review 미완료 |
| active review 효율 claim | 불가 | 사람 검수 시간/수정량 evidence 미반환 |

발표에서는 다음 문장을 쓰는 것이 안전합니다.

> 현재까지는 KG 구축, LLM 조건별 실행, structural diagnostics, release/reproducibility package까지 완료했습니다. 다만 최종 논문 성능 claim은 human-gold annotation, IAA, adjudication, mapping expert review 이후 확정할 예정입니다.

---

## 15. 교수님께 설명할 때의 핵심 문장

1. "이 연구는 LLM에게 단순히 triple을 뽑게 한 것이 아니라, CQ와 schema로 KG가 답해야 할 질문을 먼저 정의했습니다."
2. "각 node와 edge는 원문 OCR sentence evidence anchor에 연결되도록 만들었습니다."
3. "최종 KG는 LLM raw output이 아니라 task seed, procedure template, evidence, schema validator를 거친 graph입니다."
4. "LLM은 baseline/proposed/ablation 조건의 prediction generator로 사용했고, 제안 방법론은 CQ, evidence, procedural schema, validator, standard bridge를 결합한 조건입니다."
5. "현재 KG 구축과 실험 실행은 완료되었지만, 논문 성능 claim은 human-gold와 expert review가 들어와야 확정됩니다."

---

## 16. 다음 단계

최종 논문 claim을 위해 남은 일은 사람 검수입니다.

| 남은 작업 | 필요한 이유 |
| --- | --- |
| Human-gold annotation | 최종 precision/recall/F1 계산 |
| IAA 계산 | annotation 신뢰도 제시 |
| Adjudication | 최종 gold label 확정 |
| Proposed human-gold scoring | 제안 방법론의 최종 성능표 생성 |
| Mapping expert review | NCS/PCF mapping 성능 검증 |
| NCS-PCF crosswalk expert review | 표준 간 bridge utility 검증 |
| Active-review effort evidence | active review 효율 claim 검증 |

현재 단계의 결론은 다음입니다.

> CAPE-KG 방법론을 적용해 한국어 수주/제안 업무 문서 기반 Layer 2 procedural KG와 NCS/PCF standard bridge 후보를 구축했고, 14개 LLM 조건과 Qwen3 모델 scaling 실험까지 재현 가능한 형태로 준비했다. 단, 최종 성능 우수성 claim은 사람 검수 이후로 보류한다.
