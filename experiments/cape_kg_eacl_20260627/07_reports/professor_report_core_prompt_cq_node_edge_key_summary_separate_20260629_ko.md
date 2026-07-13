# 교수님 보고용 핵심 요약: 프롬프트, CQ, Node/Edge 산출 방식

Generated: 2026-06-29

대상 문서와 별개로 작성한 핵심 요약본입니다.

- 기준 문서: `experiments/cape_kg_eacl_20260627/07_reports/professor_report_slide_contents_current_20260628_ko.md`
- 핵심 근거: `experiments/cape_kg_eacl_20260627/06_release/prompt_node_edge_traceability.md`
- CQ 근거: `experiments/cape_kg_eacl_20260627/06_release/cq_query_pack.md`
- 현재 상태 근거: `experiments/cape_kg_eacl_20260627/06_release/submission_completion_audit_ko.md`

## 1. 한 줄 요약

본 연구는 한국어 수주/제안 업무 문서에서 **CAPE-KG 방법론**을 적용하여, 원문 evidence에 근거한 절차형 업무 Knowledge Graph를 만들고, 이를 NCS/PCF 표준 taxonomy와 연결하는 실험입니다.

핵심은 단순히 LLM에게 "그래프를 만들어 달라"고 요청한 것이 아니라, 다음 네 가지를 결합했다는 점입니다.

| 구성 요소 | 역할 |
| --- | --- |
| CQ | KG가 답해야 할 질문을 먼저 정의 |
| Evidence anchor | 모든 node/edge/mapping을 원문 sentence id에 연결 |
| Procedural schema | 업무를 task, step, input, output, role, decision, guard, artifact flow로 구조화 |
| Validator/bridge | 허용 node type, edge predicate, NCS/PCF mapping 조건을 검사 |

## 2. 현재까지 실제로 산출된 것

| 항목 | 현재 산출 |
| --- | ---: |
| OCR source rows | 5,009 |
| Clean Layer 2 sentences | 4,257 |
| Layer 2 chunks | 214 |
| Evidence anchors | 5,009 |
| Layer 1 NCS nodes | 4,109 |
| Layer 1 PCF nodes | 5,301 |
| Layer 2 final nodes | 179 |
| Layer 2 final edges | 906 |
| NCS mapping candidates | 110 |
| PCF mapping candidates | 110 |
| Evaluation chunks for LLM conditions | 120 |
| Priority-100 human review chunks prepared | 100 |
| Human-gold adjudicated chunks | 0 |
| Human-gold items | 0 |

현재 KG 구축 자체는 완료되어 있습니다. 다만 논문에서 "성능이 우수하다"는 식의 최종 claim을 하려면 human-gold annotation, IAA, adjudication, expert review가 추가로 필요합니다.

## 3. 최종 KG와 LLM 실험의 관계

중요한 구분은 다음과 같습니다.

| 구분 | 설명 |
| --- | --- |
| 최종 Layer 2 KG | OCR evidence, task seed, 용어 사전, 절차 템플릿, schema validator를 사용해 조립한 rule/schema/evidence 기반 graph |
| LLM baseline/proposed/ablation | 동일 chunk에 대해 프롬프트 조건별로 어떤 node/edge/triple/mapping 후보가 나오는지 비교하기 위한 prediction 실험 |
| 성능 평가 | 현재 silver/proxy diagnostic은 있으나, 최종 precision/recall/F1 claim은 human-gold 이후 가능 |

따라서 현재 `outputs/07_layer2_graph/layer2_nodes.jsonl`과 `outputs/07_layer2_graph/layer2_edges.jsonl`은 LLM이 그대로 생성한 결과가 아니라, evidence와 schema 조건을 통과해 조립된 최종 KG입니다.

## 4. 어떤 프롬프트로 무엇을 산출했는가

실제 프롬프트 파일은 다음 위치에 있습니다.

`experiments/cape_kg_eacl_20260627/02_schema/prompts/`

각 조건별 핵심 프롬프트와 요구 산출물은 다음과 같습니다.

| 조건 | 프롬프트 핵심 원문 | 요구 산출물 |
| --- | --- | --- |
| B0_plain_llm | `Extract subject-predicate-object triples from the chunk. Return JSON only.` | `triples` |
| B1_predicate_constrained | `Extract triples using only the allowed predicates. Return JSON only with evidence sentence ids.` | `edges` |
| B2_current_project | `Extract Task Frames, then triples, then post-process into the Layer2 schema.` | `nodes`, `edges` |
| B3_edc_style | `Extract, define, and canonicalize open-schema KG items, then emit CAPE-compatible nodes and edges for scoring.` | `nodes`, `edges` |
| B4_taxonomy_rag | `Retrieve NCS/PCF/task taxonomy snippets, then extract schema-constrained triples with evidence.` | `nodes`, `edges`, `mappings` |
| B5_procedural_prompt | `Extract actions, actors, gateways, guard conditions, artifact flows, and temporal/logical dependencies.` | `nodes`, `edges` |
| B6_sac_kg_verifier_pruner | `Use existing generator candidates, then apply schema/evidence verification and pruning in the style of SAC-KG. This is a deterministic approximation, not a full SAC-KG reproduction.` | `nodes`, `edges` |
| P_cape_kg_actual | `Use CQ-linked schema retrieval, procedural frame extraction, evidence-span constrained relation extraction, span verification, ontology validation, procedural consistency checks, and active review scoring.` | `nodes`, `edges`, `mappings` |
| P_minus_CQ | runtime condition only | `nodes`, `edges`, `mappings` |
| P_minus_Evidence | runtime condition only | `nodes`, `edges`, `mappings` |
| P_minus_Procedural_schema | runtime condition only | `nodes`, `edges`, `mappings` |
| P_minus_Validator | runtime condition only | `nodes`, `edges`, `mappings` |
| P_minus_Standard_bridge | runtime condition only | `nodes`, `edges` |
| P_minus_Schema_retrieval | `Run CAPE-KG without chunk-specific schema/taxonomy retrieval; keep CQ, evidence grounding, procedural schema, validation, and mapping output shape.` | `nodes`, `edges`, `mappings` |

## 5. 실제 제안 방법론 프롬프트

`P_cape_kg_actual` 조건은 제안 방법론을 대표하는 프롬프트입니다. 실제 실행 때는 아래 instruction에 chunk 문장, sentence id, taxonomy snippet, allowed schema, JSON contract가 결합되었습니다.

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

Allowed node types for this condition:
["Artifact", "ArtifactFlow", "DecisionGateway", "DomainTask", "GuardCondition",
 "Principle", "ProcedureStep", "ReviewCheckpoint", "Risk", "Role"]

Allowed edge predicates for this condition:
["BRANCHES_TO", "FEEDS_INTO", "HAS_DECISION_GATEWAY", "HAS_GUARD_CONDITION",
 "HAS_PRINCIPLE", "HAS_REVIEW_CHECKPOINT", "HAS_RISK", "HAS_STEP",
 "PERFORMED_BY", "PRECEDES", "PRODUCES", "USED_AS_INPUT_FOR", "USES_INPUT"]

JSON shape:
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

Strict JSON 실행에서는 위 user prompt 앞뒤에 다음 제약이 추가되었습니다.

```text
System:
You are a JSON-only evidence-grounded information extraction function.
Strict JSON contract:
- Return exactly one JSON object and nothing else.
- Do not include markdown, code fences, comments, XML tags, <think> blocks, prose, or explanations.
- For Qwen/Qwen-style chat models, obey /no_think; do not emit hidden or visible reasoning.

User prefix/suffix:
/no_think
...
/no_think
Return exactly one compact JSON object now.
```

이 프롬프트의 핵심은 CQ, evidence, procedural schema, validator, NCS/PCF bridge를 동시에 강제한다는 점입니다.

## 6. CQ는 어떻게 만들었는가

CQ는 LLM이 자동으로 만든 것이 아니라, 연구자가 "이 KG가 어떤 업무 질문에 답해야 하는가"를 기준으로 설계한 것입니다.

생성 흐름은 다음과 같습니다.

| 단계 | 내용 |
| --- | --- |
| 1 | 수주/제안 업무 문서에서 답해야 할 질문 범위를 정의 |
| 2 | 질문을 task, step, input, output, role, decision, guard, artifact flow, evidence, standard mapping으로 분해 |
| 3 | 각 CQ를 필요한 node type과 edge predicate에 연결 |
| 4 | CQ를 schema 설계, LLM prompt, structural evaluation, CQ answerability 평가에 재사용 |

CQ source files:

| 용도 | 파일 |
| --- | --- |
| EACL 실험용 CQ | `experiments/cape_kg_eacl_20260627/02_schema/competency_questions.json` |
| 내부 KG build용 CQ | `outputs/03_schema/competency_questions.json` |
| CQ/schema 생성 코드 | `scripts/build_ax_epak_internal_kg.py`, `scripts/build_cape_kg_eacl_experiment.py` |

## 7. CQ 목록과 연결되는 schema

| CQ | 질문 | 연결 predicate/schema |
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

현재 CQ query pack 기준으로 12개 CQ 중 11개는 현재 KG로 구조적 응답이 가능합니다. CQ8은 최종 KG에 `HAS_REVIEW_CHECKPOINT` edge가 없어 structural gap으로 남아 있고, review checkpoint 후보 45개를 사람 검수 대상으로 분리했습니다.

## 8. Node는 어떻게 산출했는가

최종 Layer 2 node는 LLM 출력물을 그대로 저장한 것이 아니라, OCR evidence와 schema 규칙을 통과한 자동 구축 결과입니다.

Node 생성 절차는 다음과 같습니다.

| 단계 | 내용 |
| --- | --- |
| 1 | OCR 문장을 sentence id와 evidence anchor로 정리 |
| 2 | 수주/제안 업무 task seed와 alias/keyword를 사용해 관련 sentence를 찾음 |
| 3 | 발견된 업무 단위를 `DomainTask` 후보로 정규화 |
| 4 | task별 절차 템플릿과 입력/산출물 정보를 사용해 `ProcedureStep` 생성 |
| 5 | 입력물/산출물 용어를 찾아 `Artifact` 생성 |
| 6 | 수행자/책임 주체를 찾아 `Role` 생성 |
| 7 | 의사결정 관련 표현을 찾아 `DecisionGateway` 생성 |
| 8 | 조건/가능성/경쟁/자원 같은 표현을 찾아 `GuardCondition` 생성 |
| 9 | 원칙/품질 기준을 찾아 `Principle`, 위험 표현을 찾아 `Risk` 생성 |
| 10 | 산출물이 다음 task 입력으로 사용되는 규칙을 찾아 `ArtifactFlow` 생성 |
| 11 | `node_id` 기준으로 중복 제거하고 evidence와 review status를 부여 |

현재 최종 node type별 수량은 다음과 같습니다.

| node type | count | 생성 규칙 |
| --- | ---: | --- |
| ProcedureStep | 99 | task별 procedure template 또는 입력/산출물 기반 step 추론 |
| DomainTask | 22 | TASK_SEEDS의 label/alias/keyword로 OCR sentence evidence 검색 |
| Artifact | 14 | task evidence 안의 입력물/산출물 용어 매칭 |
| GuardCondition | 13 | 의사결정 evidence에서 조건 표현 추출 |
| Role | 10 | 수행자/책임 주체 용어 매칭 |
| ArtifactFlow | 9 | 특정 산출물이 다음 task 입력으로 쓰이는 규칙 |
| Principle | 5 | 원칙/품질 기준 용어 매칭 |
| DecisionGateway | 4 | 의사결정 관련 용어 매칭 |
| Risk | 3 | 위험/불리함/실패 가능성 용어 매칭 |

요약하면, node는 "문서에서 업무 개념을 찾고, 그 개념을 정해진 절차형 schema에 넣은 것"입니다.

## 9. Edge는 어떻게 산출했는가

최종 Layer 2 edge는 node 사이의 업무 관계를 나타냅니다. edge가 최종 KG에 들어가려면 다음 조건을 만족해야 합니다.

| 조건 | 설명 |
| --- | --- |
| source node 존재 | edge의 출발 node가 최종 node 목록에 있어야 함 |
| target node 존재 | edge의 도착 node가 최종 node 목록에 있어야 함 |
| allowed predicate | predicate가 schema 허용 목록에 있어야 함 |
| evidence anchor | 원문 sentence evidence가 있어야 함 |
| source_triple_ids | 중간 triple record와 연결되어야 함 |

Edge 생성 절차는 다음과 같습니다.

| 단계 | 내용 |
| --- | --- |
| 1 | task와 step 사이를 `HAS_STEP`으로 연결 |
| 2 | 같은 task 안의 step order를 기준으로 `PRECEDES` 생성 |
| 3 | task/step의 input slot을 `USES_INPUT`으로 연결 |
| 4 | task/step의 output slot을 `PRODUCES`로 연결 |
| 5 | task/step의 role slot을 `PERFORMED_BY`로 연결 |
| 6 | decision node가 있으면 `HAS_DECISION_GATEWAY`로 연결 |
| 7 | decision condition이 있으면 `HAS_GUARD_CONDITION`으로 연결 |
| 8 | principle/risk slot을 `HAS_PRINCIPLE`, `HAS_RISK`로 연결 |
| 9 | artifact가 다음 업무로 흐르면 `FEEDS_INTO`, `USED_AS_INPUT_FOR`로 연결 |
| 10 | 모든 edge를 triple record로 만들고 schema/evidence validator를 통과한 것만 저장 |

현재 최종 edge predicate별 수량은 다음과 같습니다.

| predicate | count | 생성 규칙 |
| --- | ---: | --- |
| PRODUCES | 220 | task/step의 outputs slot을 Artifact node로 연결 |
| USES_INPUT | 201 | task/step의 inputs slot을 Artifact 또는 Concept node로 연결 |
| PERFORMED_BY | 120 | task/step의 roles slot을 Role node로 연결 |
| HAS_STEP | 99 | DomainTask를 해당 ProcedureStep 목록에 연결 |
| PRECEDES | 77 | 같은 task 안에서 step order 기준으로 순서 연결 |
| HAS_PRINCIPLE | 64 | task/step의 principles slot을 Principle node로 연결 |
| HAS_DECISION_GATEWAY | 54 | task/step에서 발견된 의사결정 node 연결 |
| HAS_RISK | 39 | task/step의 risks slot을 Risk node로 연결 |
| HAS_GUARD_CONDITION | 14 | DecisionGateway에서 추출된 조건 node 연결 |
| FEEDS_INTO | 9 | Artifact가 다음 task로 흘러가는 규칙 연결 |
| USED_AS_INPUT_FOR | 9 | Artifact가 다음 task 입력으로 사용되는 규칙 연결 |

현재 final edge는 906개이며, 906개 모두 evidence anchor와 `source_triple_ids`를 갖습니다. Dangling edge는 0개입니다.

## 10. Triple은 왜 있는가

Triple은 최종 graph edge를 만들기 전의 중간 표현입니다.

| 개념 | 의미 |
| --- | --- |
| Node | KG의 개체 또는 업무 개념. 예: `기회분석`, `제안서`, `제안 PM` |
| Edge | node 사이 관계. 예: `기회분석 USES_INPUT Capture Plan` |
| Triple | edge를 subject-predicate-object와 evidence text로 검증하기 위한 중간 record |
| Evidence anchor | 해당 node/edge/triple의 근거가 되는 OCR sentence id |

현재 구조에서는 schema-valid triple 906개가 만들어졌고, 이것이 최종 edge 906개로 연결됩니다.

## 11. LLM 조건별 실제 산출량

120 evaluation chunks 기준으로 조건별 valid output 수량은 다음과 같습니다.

| condition | valid rows | triples | nodes | edges | mappings |
| --- | ---: | ---: | ---: | ---: | ---: |
| B0_plain_llm | 120 | 1,037 | 0 | 0 | 0 |
| B1_predicate_constrained | 120 | 0 | 0 | 805 | 0 |
| B2_current_project | 120 | 0 | 867 | 334 | 0 |
| B3_edc_style | 120 | 0 | 769 | 263 | 0 |
| B4_taxonomy_rag | 120 | 0 | 719 | 323 | 126 |
| B5_procedural_prompt | 120 | 0 | 1,307 | 302 | 0 |
| B6_sac_kg_verifier_pruner | 120 | 0 | 2,281 | 361 | 107 |
| P_cape_kg_actual | 120 | 0 | 576 | 373 | 227 |
| P_minus_CQ | 120 | 0 | 586 | 391 | 233 |
| P_minus_Evidence | 120 | 0 | 574 | 383 | 227 |
| P_minus_Procedural_schema | 120 | 0 | 558 | 353 | 212 |
| P_minus_Schema_retrieval | 120 | 0 | 568 | 417 | 216 |
| P_minus_Standard_bridge | 120 | 0 | 577 | 405 | 0 |
| P_minus_Validator | 120 | 0 | 570 | 375 | 229 |

이 표는 "어떤 프롬프트 조건이 어떤 형태의 JSON을 산출했는가"를 보여주는 표입니다. 많이 뽑은 조건이 더 좋은 조건이라는 의미는 아닙니다. 품질 평가는 human-gold 기준으로 다시 해야 합니다.

## 12. 현재 structural diagnostic

| 진단 항목 | 현재 값 | 해석 |
| --- | ---: | --- |
| Ontology conformance | 1.0000 | 허용 node/edge schema 위반 없음 |
| Procedural consistency | 0.9950 | 절차 구조가 대부분 일관됨 |
| CQ answerability | 0.9167 | 12개 CQ 중 11개가 현재 KG로 구조적 응답 가능 |
| Evidence missing edges | 0 | accepted edge evidence 누락 없음 |
| Dangling edges | 0 | source/target 없는 edge 없음 |

남아 있는 structural gap은 `ReviewCheckpoint`, `HAS_REVIEW_CHECKPOINT`, `BRANCHES_TO`입니다. 이들은 자동으로 hallucination을 추가하지 않고 사람 검수 대상으로 분리했습니다.

## 13. 교수님께 설명할 때의 핵심 문장

발표에서 다음과 같이 설명할 수 있습니다.

> 본 연구에서는 한국어 수주/제안 업무 문서를 대상으로, CQ로 KG가 답해야 할 질문을 먼저 정의하고, 그 질문을 node type과 edge predicate로 연결했습니다. 이후 OCR sentence를 evidence anchor로 유지한 상태에서 업무 task, 절차 step, 입력물, 산출물, 수행자, 의사결정, 조건, 원칙, 위험을 구조화하여 Layer 2 업무 KG를 구축했습니다. 최종 KG는 179개 node와 906개 edge로 구성되며, 모든 accepted edge는 원문 evidence를 갖습니다. LLM은 최종 KG를 그대로 생성한 도구라기보다, 여러 프롬프트 조건에서 후보 node/edge/triple/mapping을 생성하고 비교하기 위한 prediction generator로 사용했습니다. 최종 성능 claim은 현재 준비된 100 chunk human-gold annotation, IAA, adjudication 이후 확정할 예정입니다.

## 14. 현재 남은 일

| 남은 작업 | 이유 |
| --- | --- |
| 100개 chunk 이상 human annotation | 최종 precision/recall/F1 claim 필요 |
| 2명 이상 annotator와 IAA 계산 | annotation 신뢰도 보고 필요 |
| adjudication 완료 | 최종 human-gold 기준 확정 필요 |
| NCS/PCF mapping expert review | 표준 bridge 품질 claim 필요 |
| NCS-PCF crosswalk expert review | 표준 간 연결 utility claim 필요 |
| active-review human effort 기록 | active-review 효율 claim 필요 |

현재까지의 자동 구축, 프롬프트 실행, 구조 진단, human-review handoff는 완료되어 있습니다. 남은 부분은 논문 성능 주장에 필요한 사람 검수와 전문가 검수입니다.

