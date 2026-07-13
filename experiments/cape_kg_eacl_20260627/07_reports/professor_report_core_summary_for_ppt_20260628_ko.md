# 교수님 보고용 핵심 요약본

Generated: 2026-06-28  
Experiment directory: `experiments/cape_kg_eacl_20260627`  
Related detailed slide draft: `experiments/cape_kg_eacl_20260627/07_reports/professor_report_slide_contents_current_20260628_ko.md`

이 문서는 기존 상세 슬라이드 원고와 별개로, 교수님께 보고할 때 반드시 전달해야 하는 핵심 내용만 압축한 요약본입니다. 핵심은 다음 한 문장입니다.

> 본 연구는 한국어 수주·제안 업무 문서에서 원문 evidence에 근거한 procedural KG를 구축하고, 이를 NCS/PCF 표준 taxonomy와 연결하며, LLM baseline/proposed/ablation 실험과 human-review handoff까지 준비한 CAPE-KG 연구입니다. 단, 최종 성능 claim은 human-gold annotation, IAA, adjudication, mapping expert review, NCS-PCF crosswalk expert review, active-review effort evidence 이후에만 확정할 수 있습니다.

---

## 1. 현재 어디까지 완료되었는가

| 항목 | 현재 상태 | 핵심 수치 |
| --- | --- | ---: |
| OCR sentence/evidence anchor | 완료 | 5,009 sentences |
| Layer 1 NCS KG | 완료 | 4,109 nodes |
| Layer 1 PCF KG | 완료 | 5,301 nodes |
| Layer 2 업무 KG | 완료 | 179 nodes, 906 edges |
| Layer 2 clean triples | 완료 | 906 triples |
| NCS mapping candidates | 완료, expert review 전 | 110 candidates |
| PCF mapping candidates | 완료, expert review 전 | 110 candidates |
| LLM baseline/proposed/ablation | 실행 완료 | 120 chunks |
| Model scaling | 실행 완료 | Qwen3-8B, 14B, 32B-AWQ |
| Structural diagnostics | 실행 완료 | ontology 1.0000, CQ 0.9167 |
| Pre-human handoff validation | 준비 완료 | current check count: see `../06_release/pre_human_handoff_validation.md` |
| Final paper performance claim | 미완료 | human-gold 필요 |

발표 시 표현:

- “KG 구축은 완료되었습니다.”
- “다만 논문 성능표는 아직 최종본이 아닙니다.”
- “현재 남은 병목은 GPU가 아니라 사람 검수입니다.”

---

## 2. 연구 방법론의 핵심

방법론 이름은 CAPE-KG입니다.

**CAPE-KG = Competency-Question Anchored Procedural Evidence Grounding for Domain Knowledge Graph Construction**

핵심 구성은 다음입니다.

| 구성 요소 | 역할 |
| --- | --- |
| Competency Questions | KG가 답해야 할 질문을 먼저 정의 |
| Procedural Schema | task, step, artifact, role, decision, risk를 구분 |
| Evidence Grounding | 모든 node/edge를 OCR sentence evidence에 연결 |
| Constrained LLM Prompt | LLM 출력 형식을 `nodes`, `edges`, `mappings` JSON으로 제한 |
| Validator | allowed node type, predicate, evidence id, JSON parse를 검증 |
| Standard Bridge | Layer 2 업무 KG를 NCS/PCF 표준축에 연결 |
| Human-Gold Gate | 사람이 검수하기 전에는 최종 성능 claim을 막음 |

핵심 차별점:

- 단순 triple extraction이 아니라 업무 절차를 표현하는 procedural KG construction입니다.
- LLM에게 자유롭게 그래프를 만들게 하지 않고, CQ, schema, evidence, validator로 통제했습니다.
- 최종 KG와 LLM prediction을 구분했습니다.

---

## 3. CQ는 어떻게 만들었는가

CQ는 LLM이 자동 생성한 질문이 아니라, 연구자가 “이 KG가 답해야 하는 업무 질문”으로 설계한 요구사항입니다.

생성 방식:

1. 수주·제안 업무에서 필요한 지식 범주를 먼저 정함
2. 업무 절차를 task, step, input, output, role, decision, risk, evidence, standard mapping으로 분해함
3. 각 질문을 KG schema의 node type과 edge predicate에 연결함
4. 이 CQ를 prompt, schema, validation, structural evaluation에 재사용함

CQ source:

- `experiments/cape_kg_eacl_20260627/02_schema/competency_questions.json`
- `outputs/03_schema/competency_questions.json`

주요 CQ 예시:

| CQ | 질문 | 연결 predicate |
| --- | --- | --- |
| CQ1 | 수주·제안 업무는 어떤 주요 Task와 절차 단계로 구성되는가? | `HAS_STEP`, `PRECEDES` |
| CQ2 | 각 Task는 어떤 입력 자료를 사용하는가? | `USES_INPUT` |
| CQ3 | 각 Task는 어떤 산출물을 생성하는가? | `PRODUCES` |
| CQ4 | 각 Task는 누가 수행하거나 책임지는가? | `PERFORMED_BY` |
| CQ5 | 어떤 의사결정 지점이 존재하는가? | `HAS_DECISION_GATEWAY` |
| CQ6 | 의사결정에는 어떤 조건이나 판단 기준이 필요한가? | `HAS_GUARD_CONDITION` |
| CQ7 | 산출물은 다음 업무에서 어떻게 사용되는가? | `FEEDS_INTO`, `USED_AS_INPUT_FOR` |
| CQ10 | 각 지식 항목은 원문 어느 chunk/page/span에 근거가 있는가? | `EVIDENCED_BY` |
| CQ11 | 특정 업무는 어떤 NCS 능력단위와 관련되는가? | `REQUIRES_CAPABILITY`, `CANDIDATE_ALIGNS_WITH` |
| CQ12 | 특정 업무는 PCF 프로세스 체계상 어디에 위치하는가? | `PROCESS_CONTEXT`, `CANDIDATE_ALIGNS_WITH` |

발표 시 핵심 설명:

> CQ는 “어떤 정보를 추출할 것인가”를 정하는 설계 장치입니다. 예를 들어 CQ2와 CQ3이 있기 때문에 input/output artifact를 별도 node와 edge로 만들었고, CQ5와 CQ6이 있기 때문에 decision gateway와 guard condition을 별도로 추출했습니다.

---

## 4. 실제 프롬프트는 무엇이었는가

프롬프트 파일 위치:

`experiments/cape_kg_eacl_20260627/02_schema/prompts/`

프롬프트별 산출물:

| 조건 | 목적 | 출력 JSON |
| --- | --- | --- |
| `B0_plain_llm` | schema 없는 단순 SPO triple 추출 | `triples` |
| `B1_predicate_constrained` | 허용 predicate만 쓰는 edge 추출 | `edges` |
| `B2_current_project` | 기존 task-frame 방식 baseline | `nodes`, `edges` |
| `B3_edc_style` | EDC-style open-schema extraction | `nodes`, `edges` |
| `B4_taxonomy_rag` | NCS/PCF taxonomy context 사용 | `nodes`, `edges`, `mappings` |
| `B5_procedural_prompt` | procedural action/actor/gateway 추출 | `nodes`, `edges` |
| `B6_sac_kg_verifier_pruner` | verifier/pruner baseline | `nodes`, `edges`, `mappings` |
| `P_cape_kg_actual` | 제안 방법론 | `nodes`, `edges`, `mappings` |
| `P_minus_*` | ablation | 조건별 `nodes`, `edges`, `mappings` |

실제 prompt file 원문:

| 조건 | 저장된 핵심 프롬프트 |
| --- | --- |
| `B0_plain_llm` | `Extract subject-predicate-object triples from the chunk. Return JSON only.` |
| `B1_predicate_constrained` | `Extract triples using only the allowed predicates. Return JSON only with evidence sentence ids.` |
| `B2_current_project` | `Extract Task Frames, then triples, then post-process into the Layer2 schema.` |
| `B4_taxonomy_rag` | `Retrieve NCS/PCF/task taxonomy snippets, then extract schema-constrained triples with evidence.` |
| `B5_procedural_prompt` | `Extract actions, actors, gateways, guard conditions, artifact flows, and temporal/logical dependencies.` |
| `P_cape_kg_actual` | `Use CQ-linked schema retrieval, procedural frame extraction, evidence-span constrained relation extraction, span verification, ontology validation, procedural consistency checks, and active review scoring.` |

실제 runtime prompt에는 위 한 줄 지시문만 들어간 것이 아니라, chunk sentence, sentence id, allowed node type, allowed predicate, JSON shape, evidence requirement가 함께 붙었습니다.

공통 runtime prompt 핵심:

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

제안 방법론 `P_cape_kg_actual`의 핵심 runtime instruction:

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
- Prefer concise, reusable labels.
- Hard limit: return at most 5 nodes, at most 5 edges, and at most 3 mappings.
- If the chunk does not support a field, return an empty array for that field.
```

출력 JSON shape:

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

## 5. 최종 KG node는 어떻게 산출했는가

중요한 점:

> 최종 `outputs/07_layer2_graph/layer2_nodes.jsonl`은 LLM 출력물을 그대로 저장한 것이 아닙니다. OCR evidence anchor, task seed, 용어 사전, 절차 템플릿, schema constraint를 이용해 rule/schema/evidence 기반으로 조립한 KG node입니다.

Node 생성 흐름:

1. OCR sentence를 `EA-JS-*` evidence anchor로 변환
2. `TASK_SEEDS`의 label, alias, keyword로 관련 sentence 검색
3. 검색된 sentence에서 artifact, role, decision, principle, risk 후보를 용어 사전으로 추출
4. 업무 seed를 `DomainTask` node로 생성
5. task별 procedure template과 입력/산출물 규칙으로 `ProcedureStep` node 생성
6. 산출물 흐름 규칙으로 `ArtifactFlow` node 생성
7. `node_id` 기준 중복 제거
8. 모든 node에 evidence와 review status 부여

Node type별 결과:

| Node type | 생성 방식 | 개수 |
| --- | --- | ---: |
| `DomainTask` | 업무 seed + evidence sentence 검색 | 22 |
| `ProcedureStep` | task별 procedure template 또는 입력/산출물 기반 step 추론 | 99 |
| `Artifact` | 입력물/산출물 용어 매칭 | 14 |
| `Role` | 수행자/책임 주체 용어 매칭 | 10 |
| `DecisionGateway` | 의사결정 관련 용어 매칭 | 4 |
| `GuardCondition` | 조건/가능성/경쟁/자원 표현 추출 | 13 |
| `Principle` | 원칙/품질 기준 용어 매칭 | 5 |
| `Risk` | 위험/불리함/실패 가능성 용어 매칭 | 3 |
| `ArtifactFlow` | 산출물이 다음 task 입력으로 쓰이는 규칙 | 9 |

총계:

- Final Layer 2 nodes: 179
- Nodes with evidence: 179 / 179

---

## 6. 최종 KG edge는 어떻게 산출했는가

중요한 점:

> Edge는 “문장에 관계가 있어 보이는 것”을 저장한 것이 아니라, source node와 target node가 실제로 존재하고, predicate가 허용 목록에 있으며, evidence anchor가 있는 경우에만 최종 graph에 남겼습니다.

Edge 생성 흐름:

1. task frame의 `inputs`, `outputs`, `roles`, `principles`, `risks` slot을 predicate로 변환
2. decision gateway와 guard condition을 별도 predicate로 연결
3. procedure step은 `HAS_STEP`, step 순서는 `PRECEDES`로 연결
4. artifact flow는 `FEEDS_INTO`, `USED_AS_INPUT_FOR`로 연결
5. 모든 edge를 triple record로 변환하고 `source_triple_ids` 부여
6. allowed predicate, source/target node 존재, evidence 존재 조건을 통과한 edge만 저장

Predicate별 결과:

| Predicate | 생성 방식 | 개수 |
| --- | --- | ---: |
| `PRODUCES` | task/step의 outputs slot을 Artifact node로 연결 | 220 |
| `USES_INPUT` | task/step의 inputs slot을 Artifact/Concept node로 연결 | 201 |
| `PERFORMED_BY` | task/step의 roles slot을 Role node로 연결 | 120 |
| `HAS_STEP` | DomainTask를 ProcedureStep 목록에 연결 | 99 |
| `PRECEDES` | 같은 task 안에서 step order 기준으로 순서 연결 | 77 |
| `HAS_PRINCIPLE` | task/step의 principles slot 연결 | 64 |
| `HAS_DECISION_GATEWAY` | task/step에서 발견된 의사결정 node 연결 | 54 |
| `HAS_RISK` | task/step의 risks slot 연결 | 39 |
| `HAS_GUARD_CONDITION` | DecisionGateway와 조건 node 연결 | 14 |
| `FEEDS_INTO` | Artifact가 다음 task로 흐르는 규칙 연결 | 9 |
| `USED_AS_INPUT_FOR` | Artifact가 다음 task 입력으로 사용되는 규칙 연결 | 9 |

검증 결과:

- Final Layer 2 edges: 906
- Evidence가 있는 edges: 906 / 906
- `source_triple_ids`가 있는 edges: 906 / 906
- Dangling edges: 0
- Type violations: 0

---

## 7. Triple, node, edge의 관계

중간 산출물 관계:

| 단계 | 파일 | 의미 |
| --- | --- | --- |
| Task frame | `outputs/04_task_frames/canonical_task_catalog.json` | 22개 canonical 업무 단위 |
| Procedure structure | `outputs/05_procedure/procedure_structures_clean.jsonl` | task별 step, order, decision 구조 |
| Schema-valid triple | `outputs/06_triples/layer2_triples_schema_valid.jsonl` | edge를 SPO/evidence 형식으로 표현한 906개 triple |
| Final nodes | `outputs/07_layer2_graph/layer2_nodes.jsonl` | 최종 KG node |
| Final edges | `outputs/07_layer2_graph/layer2_edges.jsonl` | 검증 통과 edge |

해석:

- Node는 업무 개념입니다.
- Edge는 node 사이 관계입니다.
- Triple은 edge를 subject-predicate-object와 evidence로 검증하기 위한 중간 표현입니다.
- 현재 triple 수와 edge 수가 모두 906인 이유는 schema-valid triple이 최종 edge로 변환되었기 때문입니다.

---

## 8. LLM은 어떻게 사용했는가

LLM 사용 목적:

- 동일 120개 evaluation chunk에 대해 baseline/proposed/ablation 조건별 후보 생성
- prompt 조건이 산출물 구조와 evidence grounding에 미치는 영향 진단
- Qwen3-8B, 14B, 32B-AWQ model scaling 확인

사용 모델:

| 모델 | 실행 범위 | 상태 |
| --- | --- | --- |
| Qwen3-8B | baseline/proposed/ablation full 120 chunks | 완료 |
| Qwen3-14B | core conditions 120 chunks | 완료 |
| Qwen3-32B-AWQ | core conditions 120 chunks | 완료 |

Qwen3-8B validated output 수량 예시:

| 조건 | Valid rows | Triples | Nodes | Edges | Mappings |
| --- | ---: | ---: | ---: | ---: | ---: |
| `B0_plain_llm` | 120 | 1,037 | 0 | 0 | 0 |
| `B1_predicate_constrained` | 120 | 0 | 0 | 805 | 0 |
| `B2_current_project` | 120 | 0 | 867 | 334 | 0 |
| `B4_taxonomy_rag` | 120 | 0 | 719 | 323 | 126 |
| `B5_procedural_prompt` | 120 | 0 | 1,307 | 302 | 0 |
| `P_cape_kg_actual` | 120 | 0 | 576 | 373 | 227 |

주의:

- 이 수량표는 “얼마나 많이 추출했는가”를 보여주는 diagnostic입니다.
- 많이 추출했다고 성능이 높은 것은 아닙니다.
- 최종 precision/recall/F1은 human-gold 이후에 계산해야 합니다.

---

## 9. 현재 결과를 어떻게 해석해야 하는가

현재 말할 수 있는 것:

- Layer 1 NCS/PCF KG 구축 완료
- Layer 2 procedural KG 구축 완료
- 모든 accepted Layer 2 edge에 evidence 있음
- NCS/PCF mapping 후보 생성 완료
- LLM baseline/proposed/ablation/model-scaling 실행 완료
- public benchmark adapter 실행 완료
- structural diagnostics와 pre-human handoff 준비 완료

아직 말하면 안 되는 것:

- “우리 방법이 최종적으로 더 정확하다”
- “P_cape_kg_actual이 human-gold 기준으로 우수하다”
- “NCS/PCF mapping 성능이 검증됐다”
- “active review가 사람 검수 비용을 줄였다”

이유:

- human-gold annotation 반환 파일: 0 / 11
- adjudicated chunks: 0
- gold item count: 0
- IAA 미계산
- mapping expert review, NCS-PCF crosswalk expert review, active-review effort evidence 미완료
- active-review timing/correction 미반환

---

## 10. 발표용 핵심 메시지

교수님께 보고할 때 가장 안전한 표현:

1. “이번 연구는 한국어 수주·제안 업무 문서에서 evidence-grounded procedural KG를 구축하는 방법론입니다.”
2. “단순 LLM triple extraction이 아니라 CQ, schema, evidence, validator로 통제된 KG construction입니다.”
3. “최종 Layer 2 KG는 179 nodes, 906 edges로 구축되었고, accepted edge는 모두 evidence를 갖습니다.”
4. “NCS/PCF Layer 1 표준 KG와 Layer 2 업무 KG는 직접 병합하지 않고 mapping candidate로 느슨하게 연결했습니다.”
5. “LLM은 최종 KG를 그대로 만든 도구가 아니라, baseline/proposed/ablation 조건의 prediction generator로 사용했습니다.”
6. “현재 자동 실험과 handoff는 완료되었지만, 최종 논문 성능표는 human-gold, IAA, adjudication, expert review 이후 확정해야 합니다.”

---

## 11. 다음 단계

| 우선순위 | 해야 할 일 | 목적 |
| --- | --- | --- |
| 1 | Annotator A/B 100 chunk 검수 완료 | human-gold 생성 |
| 2 | IAA 계산 | annotation 신뢰도 확인 |
| 3 | adjudication 완료 | 최종 gold label 확정 |
| 4 | P/Baseline/Ablation을 human-gold로 재평가 | final main table 생성 |
| 5 | NCS/PCF mapping expert review | mapping downstream claim 가능화 |
| 6 | active-review timing/correction 반환 | 검수 비용 절감 claim 가능화 |

최종 결론:

> 현재는 “자동 KG 구축 및 실험 인프라 완성 단계”입니다. 논문에서 주장 가능한 최종 성능 결과는 사람 검수 데이터가 들어온 뒤 생성해야 합니다.
