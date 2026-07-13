# CAPE-KG 교수님 보고용 핵심 요약

Generated: 2026-06-28  
Detailed source document: `experiments/cape_kg_eacl_20260627/07_reports/professor_report_slide_contents_current_20260628_ko.md`  
Traceability source: `experiments/cape_kg_eacl_20260627/06_release/prompt_node_edge_traceability.md`

이 문서는 상세 슬라이드 원고와 별개로, 교수님께 핵심만 설명하기 위한 압축본입니다. 중심 질문은 다음 다섯 가지입니다.

1. 이 연구에서 실제로 무엇을 했는가?
2. 어떤 프롬프트로 어떤 산출물을 만들었는가?
3. CQ는 어떻게 만들었고 어떤 예시가 있는가?
4. 최종 KG의 node와 edge는 각각 어떻게 산출했는가?
5. 현재 무엇은 완료되었고, 무엇은 아직 최종 claim하면 안 되는가?

---

## 1. 한 문장 요약

본 연구는 한국어 수주/제안 업무 문서에서 OCR sentence evidence에 근거한 절차형 지식그래프를 구축하고, 이를 NCS/PCF 표준 taxonomy와 연결한 뒤, LLM baseline/proposed/ablation/model-scaling 실험과 human-review handoff까지 준비한 CAPE-KG 실험입니다.

가장 중요한 구분은 다음입니다.

| 구분 | 설명 |
|---|---|
| 최종 Layer 2 KG | rule/schema/evidence 기반으로 구축한 실제 업무 KG |
| LLM 산출물 | baseline/proposed/ablation 조건 비교를 위한 prediction 후보 |
| 현재 claim 가능 | KG 구축 완료, 실험 coverage, 구조 진단, 재현 패키지 |
| 아직 claim 보류 | human-gold precision/recall/F1, IAA, adjudicated main performance table, mapping expert-review 성능 |

발표에서 사용할 정확한 표현:

> 최종 KG는 LLM raw output을 그대로 저장한 것이 아니라, OCR evidence anchor, task seed, 용어 사전, 절차 템플릿, schema validator를 결합해 만든 graph입니다. LLM은 같은 데이터에서 여러 추출 조건의 후보 생성 성능을 비교하기 위해 별도로 실행했습니다.

---

## 2. 현재까지 구축된 결과

| 항목 | 값 | 의미 |
|---|---:|---|
| OCR clean sentences | 5,009 | 원문 업무 문서 sentence evidence |
| Layer 2 chunks | 214 | 전체 KG 구축 단위 |
| Evaluation chunks | 120 | LLM 비교 실험 subset |
| Layer 1 NCS nodes | 4,109 | NCS taxonomy node |
| Layer 1 PCF nodes | 5,301 | PCF taxonomy node |
| Layer 2 final nodes | 179 | 최종 업무 KG node |
| Layer 2 final edges | 906 | 최종 업무 KG edge |
| NCS mapping candidates | 110 | Layer 2 task와 NCS 후보 |
| PCF mapping candidates | 110 | Layer 2 task와 PCF 후보 |

품질 점검 결과:

| 검증 항목 | 결과 |
|---|---|
| Final nodes with evidence | 179 / 179 |
| Final edges with evidence | 906 / 906 |
| Final edges with source triples | 906 / 906 |
| Dangling edges | 0 |
| Ontology conformance | 1.0000 |
| Procedural consistency | 0.9950 |
| CQ answerability | 0.9167 |
| Claim gate | FAIL, human-gold/IAA/adjudication 미완료 때문 |

---

## 3. 전체 방법론 흐름

```text
OCR sentence 정제
-> sentence-level evidence anchor 생성
-> task seed / keyword / alias matching
-> procedural frame 구성
-> node 후보 생성
-> edge/triple 후보 생성
-> schema/evidence/domain-range validation
-> Layer 2 KG assembly
-> NCS/PCF standard bridge
-> LLM baseline/proposed/ablation 비교
-> human-gold / mapping expert review handoff
```

방법론 구성:

| 구성 요소 | 역할 |
|---|---|
| Competency Questions | KG가 답해야 할 업무 질문을 먼저 정의 |
| Procedural Schema | task, step, artifact, role, decision, risk 구조화 |
| Evidence Grounding | node/edge를 OCR sentence evidence에 연결 |
| Validator | JSON, predicate, node type, domain/range, evidence 조건 점검 |
| Standard Bridge | Layer 2 업무 KG를 NCS/PCF와 연결 |
| Human Review Handoff | 논문용 최종 claim을 위한 사람 검수 패키지 |

---

## 4. 어떤 프롬프트로 무엇을 산출했는가

프롬프트 파일 위치:

- `experiments/cape_kg_eacl_20260627/02_schema/prompts/`

실제 LLM 호출에서는 아래 프롬프트 파일의 핵심 지시문에 chunk metadata, sentence ids, chunk sentences, allowed node types, allowed predicates, JSON output shape가 자동으로 결합되었습니다.

| condition | 목적 | 산출 key |
|---|---|---|
| `B0_plain_llm` | schema 없는 일반 SPO triple extraction | `triples` |
| `B1_predicate_constrained` | 허용 predicate만 사용하는 edge extraction | `edges` |
| `B2_current_project` | task frame/triple 기반 기존 방식 baseline | `nodes`, `edges` |
| `B3_edc_style` | extract-define-canonicalize 스타일 baseline | `nodes`, `edges` |
| `B4_taxonomy_rag` | NCS/PCF/task taxonomy retrieval baseline | `nodes`, `edges`, `mappings` |
| `B5_procedural_prompt` | action/actor/gateway/artifact flow 중심 baseline | `nodes`, `edges` |
| `B6_sac_kg_verifier_pruner` | verifier/pruner approximation baseline | `nodes`, `edges` |
| `P_cape_kg_actual` | 제안 방법론 | `nodes`, `edges`, `mappings` |
| `P_minus_CQ` | CQ anchoring 제거 ablation | `nodes`, `edges`, `mappings` |
| `P_minus_Evidence` | evidence 요구 약화 ablation | `nodes`, `edges`, `mappings` |
| `P_minus_Procedural_schema` | 절차형 schema 제거 ablation | `nodes`, `edges`, `mappings` |
| `P_minus_Validator` | validator rejection 제거 ablation | `nodes`, `edges`, `mappings` |
| `P_minus_Standard_bridge` | NCS/PCF bridge 제거 ablation | `nodes`, `edges` |
| `P_minus_Schema_retrieval` | chunk-specific schema/taxonomy retrieval 제거 ablation | `nodes`, `edges`, `mappings` |

---

## 5. 실제 프롬프트 핵심 원문

아래 문장은 실제 프롬프트 파일에 저장된 핵심 지시문입니다.

| condition | 실제 저장된 prompt text |
|---|---|
| `B0_plain_llm` | `Extract subject-predicate-object triples from the chunk. Return JSON only.` |
| `B1_predicate_constrained` | `Extract triples using only the allowed predicates. Return JSON only with evidence sentence ids.` |
| `B2_current_project` | `Extract Task Frames, then triples, then post-process into the Layer2 schema.` |
| `B3_edc_style` | `Extract, define, and canonicalize open-schema KG items, then emit CAPE-compatible nodes and edges for scoring.` |
| `B4_taxonomy_rag` | `Retrieve NCS/PCF/task taxonomy snippets, then extract schema-constrained triples with evidence.` |
| `B5_procedural_prompt` | `Extract actions, actors, gateways, guard conditions, artifact flows, and temporal/logical dependencies.` |
| `B6_sac_kg_verifier_pruner` | `Use existing generator candidates, then apply schema/evidence verification and pruning in the style of SAC-KG. This is a deterministic approximation, not a full SAC-KG reproduction.` |
| `P_cape_kg_actual` | `Use CQ-linked schema retrieval, procedural frame extraction, evidence-span constrained relation extraction, span verification, ontology validation, procedural consistency checks, and active review scoring.` |
| `P_minus_Schema_retrieval` | `Run CAPE-KG without chunk-specific schema/taxonomy retrieval; keep CQ, evidence grounding, procedural schema, validation, and mapping output shape.` |

Strict JSON 조건에는 공통으로 다음 계약을 붙였습니다.

```text
Return exactly one JSON object and nothing else.
Do not include markdown, code fences, comments, XML tags, <think> blocks, prose, or explanations.
For Qwen/Qwen-style chat models, obey /no_think; do not emit hidden or visible reasoning.
Use empty arrays for absent nodes, edges, triples, or mappings fields required by the requested shape.
```

---

## 6. 제안 방법론 `P_cape_kg_actual`의 실제 runtime prompt 구조

`P_cape_kg_actual`은 단순히 "KG를 추출하라"가 아니라, CQ, taxonomy snippet, evidence requirement, schema restriction, validator rule, output JSON shape를 함께 넣은 조건입니다.

핵심 runtime instruction:

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

Rules:
- Every node, edge, and mapping must include evidence_anchor_ids from the chunk.
- Use only the listed node types and edge predicates. Invalid schema terms will be rejected.
- Do not use outside knowledge.
- Keep Korean labels when the source text is Korean.
- Hard limit: return at most 5 nodes, at most 5 edges, and at most 3 mappings.
```

허용 node type:

```text
Artifact, ArtifactFlow, DecisionGateway, DomainTask, GuardCondition,
Principle, ProcedureStep, ReviewCheckpoint, Risk, Role
```

허용 edge predicate:

```text
BRANCHES_TO, FEEDS_INTO, HAS_DECISION_GATEWAY, HAS_GUARD_CONDITION,
HAS_PRINCIPLE, HAS_REVIEW_CHECKPOINT, HAS_RISK, HAS_STEP,
PERFORMED_BY, PRECEDES, PRODUCES, USED_AS_INPUT_FOR, USES_INPUT
```

요구 output shape:

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

---

## 7. CQ는 어떻게 생성했는가

CQ는 LLM이 자동 생성한 것이 아니라, 연구자가 먼저 정의한 KG 요구사항입니다.

생성 방식:

1. 연구 문제를 "한국어 수주/제안 업무 문서에서 절차형 업무 KG를 구축하는 문제"로 정의했습니다.
2. KG가 답해야 할 질문을 업무 구성, 순서, 입력, 산출물, 역할, 의사결정, 조건, 원칙, 위험, evidence, 표준 mapping으로 나눴습니다.
3. 각 질문을 필요한 node type과 edge predicate에 연결했습니다.
4. 동일 CQ를 schema 설계, LLM prompt, structural evaluation, CQ answerability 계산에서 재사용했습니다.

CQ 관련 파일:

| 역할 | 파일 |
|---|---|
| EACL 실험용 CQ | `experiments/cape_kg_eacl_20260627/02_schema/competency_questions.json` |
| 내부 KG build용 CQ | `outputs/03_schema/competency_questions.json` |
| traceability 문서 | `experiments/cape_kg_eacl_20260627/06_release/prompt_node_edge_traceability.md` |

---

## 8. CQ 실제 예시

| CQ | 질문 | 연결 predicate/schema |
|---|---|---|
| CQ1 | 수주/제안 업무는 어떤 주요 Task와 절차 단계로 구성되는가? | `HAS_STEP`, `PRECEDES` |
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

해석:

- CQ2, CQ3 때문에 input artifact와 output artifact를 분리했습니다.
- CQ5, CQ6 때문에 decision gateway와 guard condition을 별도 node/edge로 만들었습니다.
- CQ11, CQ12 때문에 Layer 2 업무 KG를 NCS/PCF 표준 taxonomy와 연결했습니다.

---

## 9. 최종 KG node는 어떻게 산출했는가

최종 node 파일:

- `outputs/07_layer2_graph/layer2_nodes.jsonl`

핵심:

> 최종 node는 LLM이 "node를 뽑아줘"라고 해서 나온 raw output이 아니라, OCR evidence, task seed, keyword/alias matching, 용어 사전, 절차 템플릿, schema 규칙으로 만든 KG node입니다.

생성 흐름:

1. OCR sentence를 `EA-*` evidence anchor로 변환했습니다.
2. `TASK_SEEDS`의 label, alias, keyword로 관련 sentence를 찾았습니다.
3. task evidence 안에서 artifact, role, decision, principle, risk 후보를 용어 사전으로 추출했습니다.
4. 업무 단위를 `DomainTask` node로 만들었습니다.
5. task별 procedure template과 입력/산출물 구조를 이용해 `ProcedureStep` node를 만들었습니다.
6. 의사결정 문맥에서 `DecisionGateway`와 `GuardCondition`을 만들었습니다.
7. 산출물이 다음 업무 입력으로 쓰이는 경우 `ArtifactFlow`를 만들었습니다.
8. 모든 node에 evidence anchor와 review status를 붙였습니다.

Node type별 결과:

| node type | count | 생성 방식 |
|---|---:|---|
| `ProcedureStep` | 99 | task별 procedure template 또는 입력/산출물 기반 step 추론 |
| `DomainTask` | 22 | task seed label/alias/keyword와 OCR sentence evidence 매칭 |
| `Artifact` | 14 | task evidence 안의 입력물/산출물 용어 매칭 |
| `GuardCondition` | 13 | 의사결정 evidence에서 조건/가능성/경쟁/자원 표현 추출 |
| `Role` | 10 | 수행자/책임 주체 용어 매칭 |
| `ArtifactFlow` | 9 | 특정 산출물이 다음 task 입력으로 쓰이는 규칙 |
| `Principle` | 5 | 원칙/품질 기준 표현 매칭 |
| `DecisionGateway` | 4 | 의사결정 관련 표현 매칭 |
| `Risk` | 3 | 위험/불리함/실패 가능성 표현 매칭 |

---

## 10. 최종 KG edge는 어떻게 산출했는가

최종 edge 파일:

- `outputs/07_layer2_graph/layer2_edges.jsonl`

핵심:

> Edge는 node 사이의 업무 관계입니다. 최종 graph에 들어가려면 source node와 target node가 실제로 존재해야 하고, predicate가 허용 목록에 있어야 하며, 원문 evidence anchor가 있어야 합니다.

생성 흐름:

1. task frame의 `inputs`, `outputs`, `roles`, `principles`, `risks` slot을 edge predicate로 변환했습니다.
2. `DomainTask`와 `ProcedureStep` 사이를 `HAS_STEP`으로 연결했습니다.
3. 같은 task 안의 step order를 `PRECEDES`로 연결했습니다.
4. task/step과 decision node를 `HAS_DECISION_GATEWAY`로 연결했습니다.
5. decision node와 조건 node를 `HAS_GUARD_CONDITION`으로 연결했습니다.
6. artifact가 다음 task 입력으로 쓰이면 `FEEDS_INTO`, `USED_AS_INPUT_FOR`를 생성했습니다.
7. 모든 edge를 triple record로 변환하고 `source_triple_ids`를 부여했습니다.
8. predicate, source/target node 존재, evidence 존재 조건을 통과한 edge만 저장했습니다.

Predicate별 결과:

| predicate | count | 생성 방식 |
|---|---:|---|
| `PRODUCES` | 220 | task/step의 outputs slot을 Artifact node로 연결 |
| `USES_INPUT` | 201 | task/step의 inputs slot을 Artifact/Concept node로 연결 |
| `PERFORMED_BY` | 120 | task/step의 roles slot을 Role node로 연결 |
| `HAS_STEP` | 99 | DomainTask를 해당 ProcedureStep 목록에 연결 |
| `PRECEDES` | 77 | 같은 task 안에서 step order 기준으로 순서 연결 |
| `HAS_PRINCIPLE` | 64 | task/step의 principles slot을 Principle node로 연결 |
| `HAS_DECISION_GATEWAY` | 54 | task/step에서 발견된 의사결정 node 연결 |
| `HAS_RISK` | 39 | task/step의 risks slot을 Risk node로 연결 |
| `HAS_GUARD_CONDITION` | 14 | DecisionGateway에서 추출된 조건 node 연결 |
| `FEEDS_INTO` | 9 | Artifact가 다음 task로 흘러가는 규칙 연결 |
| `USED_AS_INPUT_FOR` | 9 | Artifact가 다음 task 입력으로 사용되는 규칙 연결 |

검증 결과:

| 항목 | 값 |
|---|---:|
| Final Layer 2 edges | 906 |
| Evidence가 있는 edges | 906 / 906 |
| `source_triple_ids`가 있는 edges | 906 / 906 |
| Dangling edges | 0 |

---

## 11. Triple, edge, node의 관계

| 용어 | 의미 |
|---|---|
| Node | graph의 entity 또는 절차 단위. 예: `기회분석`, `제안서`, `Capture Plan` |
| Edge | node 사이 관계. 예: `기회분석 USES_INPUT Capture Plan` |
| Triple | edge를 subject-predicate-object와 evidence text로 평가하기 위한 중간 record |
| Evidence anchor | 해당 node/edge/triple이 근거로 삼은 OCR sentence |

현재 구조:

| 단계 | 파일 | 수량 |
|---|---|---:|
| Task frame | `outputs/04_task_frames/canonical_task_catalog.json` | 22 |
| Procedure structure | `outputs/05_procedure/procedure_structures_clean.jsonl` | 22 procedures / 99 steps |
| Schema-valid triple | `outputs/06_triples/layer2_triples_schema_valid.jsonl` | 906 |
| Final nodes | `outputs/07_layer2_graph/layer2_nodes.jsonl` | 179 |
| Final edges | `outputs/07_layer2_graph/layer2_edges.jsonl` | 906 |

---

## 12. LLM 실험 결과는 어떻게 해석해야 하는가

Qwen3-8B strict JSON full run 기준 validated object 수:

| 조건 | Valid rows | Triples | Nodes | Edges | Mappings |
|---|---:|---:|---:|---:|---:|
| `B0_plain_llm` | 120 | 1,037 | 0 | 0 | 0 |
| `B1_predicate_constrained` | 120 | 0 | 0 | 805 | 0 |
| `B2_current_project` | 120 | 0 | 867 | 334 | 0 |
| `B3_edc_style` | 120 | 0 | 769 | 263 | 0 |
| `B4_taxonomy_rag` | 120 | 0 | 719 | 323 | 126 |
| `B5_procedural_prompt` | 120 | 0 | 1,307 | 302 | 0 |
| `P_cape_kg_actual` | 120 | 0 | 576 | 373 | 227 |
| `P_minus_*` ablations | 각 120 | 0 | 558-586 | 353-417 | 0-233 |

해석:

- 이 표는 각 프롬프트 조건이 어떤 종류의 JSON 산출물을 얼마나 만들었는지 보여주는 산출량 진단입니다.
- 많이 뽑았다고 좋은 모델이라는 뜻은 아닙니다.
- precision/recall/F1 claim은 human-gold annotation 이후에만 가능합니다.

Model scaling도 실행했습니다.

| Model | Condition | Rows | Edge F1 | Predicate F1 | Node F1 | Evidence F1 |
|---|---|---:|---:|---:|---:|---:|
| Qwen3-8B | `P_cape_kg_actual` | 120 | 0.0018 | 0.0482 | 0.0326 | 0.0655 |
| Qwen3-14B | `P_cape_kg_actual` | 120 | 0.0017 | 0.0601 | 0.0298 | 0.0610 |
| Qwen3-32B-AWQ | `P_cape_kg_actual` | 120 | 0.0034 | 0.0662 | 0.0284 | 0.0542 |

주의:

> 위 F1은 human-gold가 아니라 silver reference 기준 diagnostic입니다. 최종 성능 우수성 주장으로 사용하면 안 됩니다.

---

## 13. 현재까지 실행한 실험

| 실험 | 상태 | 산출물 |
|---|---|---|
| Deterministic KG build | 완료 | Layer 1, Layer 2, mapping, visualization |
| Evidence grounding check | 완료 | node/edge evidence coverage |
| LLM baseline/proposed | 완료 | B0-B6, P_cape_kg_actual |
| Ablation study | 완료 | P_minus_CQ, Evidence, Schema, Validator, Bridge 등 |
| Model scaling | 완료 | Qwen3-8B, Qwen3-14B, Qwen3-32B-AWQ |
| Public benchmark adapter | 완료 | PAGED/Text2KG auxiliary diagnostic |
| Structural diagnostics | 완료 | ontology, procedural, CQ answerability |
| Human review handoff | 준비 완료 | annotation/mapping/active-review return files |
| Final human-gold main table | 미완료 | 사람 검수 이후 계산 필요 |

---

## 14. 교수님께 말해야 할 핵심 메시지

| 질문 | 답변 |
|---|---|
| KG 구축은 완료되었는가? | 네. Layer 1 NCS/PCF와 Layer 2 업무 KG는 구축 완료입니다. |
| 최종 KG는 LLM이 만든 것인가? | 아닙니다. 최종 KG는 rule/schema/evidence 기반이며, LLM은 비교 실험용 prediction generator로 사용했습니다. |
| 어떤 프롬프트를 썼는가? | B0-B6 baseline, P_cape_kg_actual proposed, P_minus_* ablation 조건을 사용했습니다. |
| CQ는 어디서 왔는가? | LLM 생성이 아니라 연구자가 설계한 KG 요구 질문이며 schema/prompt/evaluation에 재사용했습니다. |
| node는 어떻게 만들었는가? | task seed, evidence matching, 용어 사전, procedure template으로 만들고 evidence를 붙였습니다. |
| edge는 어떻게 만들었는가? | task frame slot과 procedure order를 predicate로 변환하고 source/target/evidence 검증을 통과시켰습니다. |
| main table은 나왔는가? | claimability table은 있습니다. 최종 performance main table은 human-gold 이후 확정합니다. |
| 왜 Claim gate가 FAIL인가? | 시스템 실패가 아니라 human-gold/IAA/adjudication이 아직 없어서 최종 claim을 막는 정상적인 안전장치입니다. |

---

## 15. 다음 단계

최종 논문 claim을 위해 필요한 단계:

1. 100개 priority chunk에 대해 annotator A/B 검수 완료
2. IAA 계산
3. adjudication 완료
4. human-gold 기준 node/edge/evidence F1 재계산
5. NCS/PCF mapping expert review 완료
6. claim gate 재실행
7. final performance main table 확정

현재 발표에서의 안전한 결론:

> CAPE-KG 방법론으로 한국어 수주/제안 업무 문서의 evidence-grounded procedural KG 구축과 LLM 조건 비교 실험은 완료했으며, 최종 논문 성능 claim은 human-gold annotation과 expert review 이후 확정할 계획입니다.
