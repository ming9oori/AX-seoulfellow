# CAPE-KG 핵심 요약본: Prompt, CQ, Node/Edge 산출 방식

Generated: 2026-06-28  
Related detailed slide draft: `experiments/cape_kg_eacl_20260627/07_reports/professor_report_slide_contents_current_20260628_ko.md`  
Experiment directory: `experiments/cape_kg_eacl_20260627`  
KG output directory: `outputs`

이 문서는 기존 교수님 보고용 상세 슬라이드 원고와 별개로, 발표 준비 시 핵심만 빠르게 확인하기 위한 별도 요약본입니다. 특히 다음 질문에 바로 답할 수 있도록 구성했습니다.

- 어떤 방법론으로 KG를 만들었는가?
- 어떤 prompt로 어떤 산출물을 만들었는가?
- CQ는 어떻게 만들었고, 실제 예시는 무엇인가?
- node와 edge는 각각 어떤 방식으로 산출했는가?
- 현재까지 무엇은 완료되었고, 무엇은 아직 사람 검수 이후에 확정해야 하는가?

---

## 1. 가장 중요한 한 문장

본 연구는 한국어 수주/제안 업무 문서에서 **원문 sentence evidence에 연결된 절차형 지식그래프(evidence-grounded procedural KG)**를 구축하고, 이를 **NCS/PCF 표준 taxonomy**와 연결하는 CAPE-KG 방법론을 적용한 실험입니다.

발표에서 가장 조심해야 할 구분은 다음입니다.

| 구분 | 정확한 설명 |
|---|---|
| 최종 KG | LLM raw output을 그대로 저장한 것이 아니라, OCR evidence anchor, task seed, 용어 사전, 절차 템플릿, schema validator를 결합해 만든 rule/schema/evidence 기반 graph |
| LLM 실험 | 같은 evaluation chunk에 대해 baseline/proposed/ablation 조건이 어떤 node/edge/triple 후보를 만드는지 비교한 prediction experiment |
| 현재 claim 가능 | KG 구축 완료, evidence grounding, 구조 진단, LLM 조건별 실행, NCS/PCF 후보 mapping, human review handoff 준비 |
| 아직 claim 보류 | human-gold precision/recall/F1, IAA, adjudication, expert-reviewed mapping 성능, 최종 논문 main performance table |

---

## 2. 현재까지 나온 핵심 결과

| 항목 | 값 | 의미 |
|---|---:|---|
| OCR clean sentences | 5,009 | KG evidence의 원천 sentence |
| Layer 2 chunks | 214 | 전체 업무 KG 구축 단위 |
| LLM evaluation chunks | 120 | baseline/proposed/ablation 비교 subset |
| Layer 1 NCS nodes | 4,109 | NCS 표준 taxonomy node |
| Layer 1 PCF nodes | 5,301 | PCF 표준 taxonomy node |
| Final Layer 2 KG nodes | 179 | 최종 업무 KG node |
| Final Layer 2 KG edges | 906 | 최종 업무 KG edge |
| Schema-valid triples | 906 | edge를 SPO/evidence 형태로 표현한 중간 산출물 |
| NCS mapping candidates | 110 | Layer 2 task별 NCS 후보 |
| PCF mapping candidates | 110 | Layer 2 task별 PCF 후보 |

품질/상태 요약:

| 검증 항목 | 결과 |
|---|---|
| Nodes with evidence | 179 / 179 |
| Edges with evidence | 906 / 906 |
| Edges with source triples | 906 / 906 |
| Dangling edges | 0 |
| Type/domain-range violations | 0 |
| Ontology conformance | 1.0000 |
| Procedural consistency | 0.9950 |
| CQ answerability | 0.9167, 12개 중 11개 answerable |
| Pre-human handoff validation | PASS; current check count: see `../06_release/pre_human_handoff_validation.md` |

여기서 1 WARN은 실험 실패가 아니라, human-gold annotation, IAA, adjudication, human-gold scoring이 아직 끝나지 않았다는 claim gate입니다.

---

## 3. 전체 방법론 흐름

```text
OCR sentence 정제
-> sentence-level evidence anchor 생성
-> task seed / alias / keyword matching
-> procedural frame construction
-> node 후보 생성
-> edge/triple 후보 생성
-> schema/evidence/domain-range validation
-> final Layer 2 KG assembly
-> NCS/PCF standard bridge candidate mapping
-> LLM baseline/proposed/ablation 비교
-> structural diagnostics / CQ answerability
-> human review handoff
```

방법론의 핵심 구성 요소는 다음입니다.

| 구성 요소 | 역할 |
|---|---|
| Competency Questions | KG가 답해야 하는 업무 질문을 먼저 정의 |
| Procedural schema | `DomainTask`, `ProcedureStep`, `Artifact`, `Role`, `DecisionGateway`, `GuardCondition`, `Risk` 등으로 업무 구조화 |
| Evidence grounding | node/edge/triple이 원문 sentence evidence anchor로 돌아가도록 설계 |
| Validator | node type, predicate, domain/range, evidence id, JSON shape를 점검 |
| Standard bridge | Layer 2 업무 task를 NCS/PCF 표준 taxonomy 후보와 연결 |
| Human review handoff | 최종 논문 claim을 위해 사람이 검수할 파일과 검증 루틴 제공 |

---

## 4. 어떤 prompt로 무엇을 산출했는가

프롬프트 파일 위치:

- `experiments/cape_kg_eacl_20260627/02_schema/prompts/`
- 실행 스크립트: `scripts/run_cape_llm_condition_baselines.py`

실제 LLM 호출에서는 아래 prompt file의 핵심 지시문에 `chunk_id`, page range, sentence ids, chunk sentences, allowed node types, allowed predicates, JSON output shape, strict JSON contract가 자동으로 결합되었습니다.

| condition | 목적 | 주요 산출 key |
|---|---|---|
| `B0_plain_llm` | schema 없는 일반 SPO triple extraction | `triples` |
| `B1_predicate_constrained` | 허용 predicate만 쓰는 relation extraction | `edges` |
| `B2_current_project` | 기존 task frame/triple 방식 baseline | `nodes`, `edges` |
| `B3_edc_style` | extract-define-canonicalize 스타일 baseline | `nodes`, `edges` |
| `B4_taxonomy_rag` | NCS/PCF/task taxonomy retrieval baseline | `nodes`, `edges`, `mappings` |
| `B5_procedural_prompt` | action, actor, gateway, artifact flow 중심 baseline | `nodes`, `edges` |
| `B6_sac_kg_verifier_pruner` | SAC-KG-style verifier/pruner approximation | `nodes`, `edges` |
| `P_cape_kg_actual` | 제안 방법론 | `nodes`, `edges`, `mappings` |
| `P_minus_CQ` | CQ anchoring 제거 ablation | `nodes`, `edges`, `mappings` |
| `P_minus_Evidence` | evidence anchor 요구 약화 ablation | `nodes`, `edges`, `mappings` |
| `P_minus_Procedural_schema` | procedural schema 제거 ablation | `nodes`, `edges`, `mappings` |
| `P_minus_Validator` | validator rejection 제거 ablation | `nodes`, `edges`, `mappings` |
| `P_minus_Standard_bridge` | NCS/PCF bridge 제거 ablation | `nodes`, `edges` |
| `P_minus_Schema_retrieval` | chunk-specific schema/taxonomy retrieval 제거 ablation | `nodes`, `edges`, `mappings` |

---

## 5. 실제 prompt file 원문

아래 문장은 실제 prompt 파일에 저장된 핵심 지시문입니다.

| condition | prompt file | 실제 저장된 prompt text |
|---|---|---|
| `B0_plain_llm` | `B0_plain_llm_triple_extraction.txt` | `Extract subject-predicate-object triples from the chunk. Return JSON only.` |
| `B1_predicate_constrained` | `B1_predicate_constrained_llm.txt` | `Extract triples using only the allowed predicates. Return JSON only with evidence sentence ids.` |
| `B2_current_project` | `B2_current_project_baseline.txt` | `Extract Task Frames, then triples, then post-process into the Layer2 schema.` |
| `B3_edc_style` | `B3_edc_style_baseline.txt` | `Extract, define, and canonicalize open-schema KG items, then emit CAPE-compatible nodes and edges for scoring.` |
| `B4_taxonomy_rag` | `B4_taxonomy_rag_baseline.txt` | `Retrieve NCS/PCF/task taxonomy snippets, then extract schema-constrained triples with evidence.` |
| `B5_procedural_prompt` | `B5_procedural_prompt_baseline.txt` | `Extract actions, actors, gateways, guard conditions, artifact flows, and temporal/logical dependencies.` |
| `B6_sac_kg_verifier_pruner` | `B6_sac_kg_verifier_pruner_baseline.txt` | `Use existing generator candidates, then apply schema/evidence verification and pruning in the style of SAC-KG. This is a deterministic approximation, not a full SAC-KG reproduction.` |
| `P_cape_kg_actual` | `P_cape_kg.txt` | `Use CQ-linked schema retrieval, procedural frame extraction, evidence-span constrained relation extraction, span verification, ontology validation, procedural consistency checks, and active review scoring.` |
| `P_minus_Schema_retrieval` | `P_minus_Schema_retrieval.txt` | `Run CAPE-KG without chunk-specific schema/taxonomy retrieval; keep CQ, evidence grounding, procedural schema, validation, and mapping output shape.` |
| `strict_json_contract` | `strict_json_contract.txt` | JSON object만 반환, markdown/설명/code fence/XML/`<think>` block 금지, Qwen 계열 `/no_think`, compact JSON, 빈 배열 사용 |

`P_minus_CQ`, `P_minus_Evidence`, `P_minus_Procedural_schema`, `P_minus_Validator`, `P_minus_Standard_bridge`는 별도 prompt file이 아니라 runtime condition으로 구현했습니다. 즉 `P_cape_kg_actual`의 공통 template에서 CQ, evidence, procedural schema, validator, standard bridge 중 특정 구성요소를 제거하거나 약화한 조건입니다.

---

## 6. 실제 runtime prompt 공통 구조

프롬프트 파일의 한 줄 지시문만 LLM에 넣은 것이 아닙니다. 실행 스크립트가 아래 공통 template을 결합했습니다.

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

schema-constrained 조건에는 다음도 추가되었습니다.

```text
Allowed node types:
{allowed_node_types}

Allowed edge predicates:
{allowed_edge_predicates}

Required output JSON shape:
{
  "nodes": [...],
  "edges": [...],
  "mappings": [...]
}
```

strict JSON run에서는 system/user prompt에 다음 제약이 추가되었습니다.

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

---

## 7. 제안 방법론 `P_cape_kg_actual`의 실제 prompt 구조

`P_cape_kg_actual`은 단순한 "KG를 만들어라" prompt가 아니라, CQ, taxonomy snippet, evidence requirement, schema restriction, validator rule, output JSON shape를 결합한 조건입니다.

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

## 8. CQ는 어떻게 생성했는가

CQ(Competency Question)는 LLM이 자동 생성한 것이 아니라, 연구자가 먼저 정의한 **KG 요구사항**입니다.

생성 방식:

1. 연구 문제를 "한국어 수주/제안 업무 문서에서 절차형 업무 KG를 구축하는 문제"로 정의했습니다.
2. KG가 답해야 할 질문을 업무 구성, 순서, 입력, 산출물, 역할, 의사결정, 조건, 산출물 흐름, 원문 evidence, 표준 taxonomy mapping으로 나누었습니다.
3. 각 질문을 필요한 node type과 edge predicate에 연결했습니다.
4. 이 CQ를 schema 설계, LLM prompt, ablation, structural evaluation, CQ query pack에 재사용했습니다.

CQ가 쓰인 위치:

| 위치 | 사용 방식 |
|---|---|
| Schema 설계 | node type과 predicate를 정하는 기준 |
| `P_cape_kg_actual` prompt | CQ block으로 추출 목표를 고정 |
| `P_minus_CQ` ablation | CQ anchoring을 제거했을 때의 차이를 비교 |
| Structural evaluation | 12개 CQ 중 몇 개를 현재 KG가 답할 수 있는지 계산 |
| CQ query pack | CQ별 Cypher/SPARQL-style query와 sample answer 생성 |

---

## 9. CQ 실제 목록과 현재 support

| CQ | 질문 | 연결 predicate | 현재 support |
|---|---|---|---:|
| CQ1 | 수주/제안 업무는 어떤 주요 Task와 절차 단계로 구성되는가? | `HAS_STEP`, `PRECEDES` | 176 |
| CQ2 | 각 Task는 어떤 입력 자료를 사용하는가? | `USES_INPUT` | 201 |
| CQ3 | 각 Task는 어떤 산출물을 생성하는가? | `PRODUCES` | 220 |
| CQ4 | 각 Task는 누가 수행하거나 책임지는가? | `PERFORMED_BY` | 120 |
| CQ5 | 어떤 의사결정 지점이 존재하는가? | `HAS_DECISION_GATEWAY` | 54 |
| CQ6 | 의사결정에는 어떤 조건이나 판단 기준이 필요한가? | `HAS_GUARD_CONDITION` | 14 |
| CQ7 | 산출물은 다음 업무에서 어떻게 사용되는가? | `FEEDS_INTO`, `USED_AS_INPUT_FOR` | 18 |
| CQ8 | 제안서 리뷰는 어떤 단계에서 어떻게 수행되는가? | `HAS_REVIEW_CHECKPOINT` | 0 |
| CQ9 | 각 업무에서 지켜야 할 원칙은 무엇인가? | `HAS_PRINCIPLE` | 64 |
| CQ10 | 각 지식 항목은 원문 어느 chunk/page/span에 근거가 있는가? | evidence anchor | 906 |
| CQ11 | 특정 업무는 어떤 NCS 능력단위와 관련되는가? | NCS mapping candidates | 110 |
| CQ12 | 특정 업무는 PCF 프로세스 체계상 어디에 위치하는가? | PCF mapping candidates | 110 |

현재 CQ8은 final KG에 `HAS_REVIEW_CHECKPOINT` edge가 없어 answerable이 아닙니다. 이 항목은 자동으로 보완하지 않고 structural gap 및 human/schema follow-up 대상으로 남겨두었습니다.

---

## 10. CQ 예시 답변

CQ query pack에서 확인한 실제 KG 예시는 다음과 같습니다.

| CQ | 예시 답변 | 해석 |
|---|---|---|
| CQ1 | `기회분석` - `HAS_STEP` -> `Capture Plan 검토` | task가 어떤 절차 단계로 구성되는지 답변 |
| CQ1 | `Capture Plan 검토` - `PRECEDES` -> `제안전략 검토` | 같은 task 안의 단계 순서 답변 |
| CQ2 | `기회분석` - `USES_INPUT` -> `Capture Plan` | task가 사용하는 입력 자료 답변 |
| CQ3 | `기회분석` - `PRODUCES` -> `제안 요청서` | task가 생성하는 산출물 답변 |
| CQ4 | `DomainTask/ProcedureStep` - `PERFORMED_BY` -> `Role` | 수행자 또는 책임 주체 답변 |
| CQ5 | `DomainTask/ProcedureStep` - `HAS_DECISION_GATEWAY` -> `DecisionGateway` | 의사결정 지점 답변 |
| CQ6 | `DecisionGateway` - `HAS_GUARD_CONDITION` -> `GuardCondition` | 의사결정 조건 답변 |
| CQ7 | `Artifact` - `FEEDS_INTO` 또는 `USED_AS_INPUT_FOR` -> 다음 task/step | 산출물 흐름 답변 |
| CQ11 | Layer 2 task -> NCS candidate | 표준 능력단위 후보 답변 |
| CQ12 | Layer 2 task -> PCF candidate | 표준 프로세스 후보 답변 |

이 예시는 성능 정답이 아니라, 현재 KG가 CQ에 대해 어떤 구조적 답을 제공할 수 있는지를 보여주는 query-level sample입니다.

---

## 11. Node는 어떻게 산출했는가

최종 node 파일:

- `outputs/07_layer2_graph/layer2_nodes.jsonl`

Node 생성 흐름:

1. OCR sentence를 evidence anchor로 변환했습니다.
2. `TASK_SEEDS`의 업무 seed label, alias, keyword로 관련 sentence를 찾았습니다.
3. 관련 sentence에서 Artifact, Role, DecisionGateway, Principle, Risk 후보를 용어 사전/규칙으로 추출했습니다.
4. 각 task frame을 `DomainTask` node로 생성했습니다.
5. task별 procedure template 또는 입력/산출물 기반 추론으로 `ProcedureStep` node를 생성했습니다.
6. 특정 산출물이 다음 업무 입력으로 쓰이는 경우 `ArtifactFlow` node를 생성했습니다.
7. `node_id` 기준으로 중복을 제거하고, 모든 node에 evidence와 review status를 부여했습니다.

Node type별 결과:

| Node type | 개수 | 생성 방식 |
|---|---:|---|
| `ProcedureStep` | 99 | task별 procedure template 또는 입력/산출물 기반 step 추론 |
| `DomainTask` | 22 | task seed label/alias/keyword로 evidence sentence 검색 |
| `Artifact` | 14 | task evidence 안의 입력물/산출물 용어 매칭 |
| `GuardCondition` | 13 | decision evidence에서 조건/가능성/경쟁/자원 등 조건 표현 추출 |
| `Role` | 10 | 수행자/책임 주체 용어 매칭 |
| `ArtifactFlow` | 9 | 특정 산출물이 다음 task 입력으로 쓰이는 규칙 |
| `Principle` | 5 | 원칙/품질 기준 용어 매칭 |
| `DecisionGateway` | 4 | 의사결정 관련 용어 매칭 |
| `Risk` | 3 | 위험/불리함/실패 가능성 용어 매칭 |

핵심 해석:

> 최종 KG node는 LLM에게 "node를 뽑아줘"라고 해서 그대로 받은 결과가 아닙니다. OCR evidence, task seed, dictionary, procedure template, schema rule을 결합해 정규화한 graph node입니다.

---

## 12. Edge는 어떻게 산출했는가

최종 edge 파일:

- `outputs/07_layer2_graph/layer2_edges.jsonl`

Edge 생성 흐름:

1. task frame의 `inputs`, `outputs`, `roles`, `principles`, `risks` slot을 predicate로 변환했습니다.
2. decision gateway와 guard condition을 별도 predicate로 연결했습니다.
3. task와 step은 `HAS_STEP`, step 순서는 `PRECEDES`로 연결했습니다.
4. artifact flow 규칙은 `FEEDS_INTO`, `USED_AS_INPUT_FOR`로 연결했습니다.
5. 모든 edge를 triple record로 변환하고 `source_triple_ids`를 부여했습니다.
6. allowed predicate, source/target node 존재, domain/range, evidence 존재 조건을 통과한 edge만 final graph에 저장했습니다.

Predicate별 결과:

| Predicate | 개수 | 생성 방식 |
|---|---:|---|
| `PRODUCES` | 220 | task/step의 outputs slot을 Artifact node로 연결 |
| `USES_INPUT` | 201 | task/step의 inputs slot을 Artifact 또는 Concept node로 연결 |
| `PERFORMED_BY` | 120 | task/step의 roles slot을 Role node로 연결 |
| `HAS_STEP` | 99 | DomainTask를 해당 ProcedureStep 목록에 연결 |
| `PRECEDES` | 77 | 같은 task 안에서 step order 기준으로 순서 연결 |
| `HAS_PRINCIPLE` | 64 | task/step의 principles slot을 Principle node로 연결 |
| `HAS_DECISION_GATEWAY` | 54 | task/step에서 발견된 의사결정 node를 연결 |
| `HAS_RISK` | 39 | task/step의 risks slot을 Risk node로 연결 |
| `HAS_GUARD_CONDITION` | 14 | DecisionGateway에서 추출된 조건 node를 연결 |
| `FEEDS_INTO` | 9 | Artifact가 다음 task로 흘러가는 규칙 연결 |
| `USED_AS_INPUT_FOR` | 9 | Artifact가 다음 task 입력으로 사용되는 규칙 연결 |

검증 결과:

| 검증 항목 | 결과 |
|---|---:|
| Final edges | 906 |
| Edges with evidence | 906 / 906 |
| Edges with `source_triple_ids` | 906 / 906 |
| Dangling edges | 0 |
| Domain/range violations | 0 |

핵심 해석:

> Edge는 "문장에 관계가 있어 보인다" 수준에서 끝나지 않습니다. 최종 graph에 들어가려면 source node와 target node가 실제로 존재해야 하고, predicate가 허용 목록에 있어야 하며, 원문 evidence anchor가 있어야 합니다.

---

## 13. Triple, Node, Edge의 관계

| 개념 | 역할 | 대표 파일 |
|---|---|---|
| Task frame | 업무 단위와 slot의 중간 구조 | `outputs/04_task_frames/canonical_task_catalog.json` |
| Procedure structure | task별 step/order/decision 구조 | `outputs/05_procedure/procedure_structures_clean.jsonl` |
| Triple | edge를 subject-predicate-object와 evidence로 평가하기 위한 중간 record | `outputs/06_triples/layer2_triples_schema_valid.jsonl` |
| Node | graph 시각화/Neo4j/RDF에 들어가는 최종 node | `outputs/07_layer2_graph/layer2_nodes.jsonl` |
| Edge | source/target/evidence 검증을 통과한 최종 graph edge | `outputs/07_layer2_graph/layer2_edges.jsonl` |

현재 triple 수와 final edge 수는 모두 906입니다. 즉 edge를 만들고, 그것을 SPO/evidence triple 형태로 검증한 뒤, 다시 final graph edge로 저장한 구조입니다.

---

## 14. NCS/PCF bridge는 무엇을 했는가

Layer 2 업무 KG를 외부 표준 체계와 연결하기 위해 NCS/PCF 후보 mapping을 생성했습니다.

| 항목 | 값 |
|---|---:|
| Canonical tasks | 22 |
| NCS mapping candidates | 110 |
| PCF mapping candidates | 110 |
| NCS Top-K coverage | 1.000 |
| PCF Top-K coverage | 1.000 |

중요한 해석:

> 현재 NCS/PCF mapping은 후보 생성 단계입니다. 자동 후보를 정답으로 주장하면 안 되고, expert review 이후 acceptability 또는 accuracy를 claim해야 합니다.

---

## 15. 현재 발표에서 말할 수 있는 것과 말하면 안 되는 것

말할 수 있는 것:

- 한국어 수주/제안 업무 문서에서 Layer 2 procedural KG를 구축했다.
- 최종 KG는 179 nodes, 906 edges로 구성된다.
- final node/edge는 evidence anchor에 연결되어 있다.
- 12개 CQ 중 11개는 현재 KG query로 structural answer를 제공한다.
- LLM baseline/proposed/ablation/model scaling 실험은 120 evaluation chunks 기준으로 실행했다.
- NCS/PCF 후보 mapping은 각각 110개씩 생성했다.
- Neo4j/HTML/RDF/SHACL/export와 human review handoff까지 준비했다.

아직 말하면 안 되는 것:

- proposed method가 human-gold 기준으로 baseline보다 최종 성능이 우수하다는 주장
- precision/recall/F1 main table을 최종 논문 결과로 확정하는 것
- NCS/PCF mapping 후보가 expert-reviewed 정답이라는 주장
- CQ sample answer가 의미적으로 모두 정답이라는 주장

정확한 발표 표현:

> 현재까지는 KG 구축과 실험/검증 인프라가 완료되었고, 최종 성능 claim은 human-gold annotation, IAA, adjudication, expert review 이후 확정할 예정입니다.

---

## 16. 교수님께 짧게 설명할 때의 핵심 멘트

1. "저희 방법론은 LLM이 만든 결과를 그대로 KG로 저장하는 방식이 아니라, CQ, schema, evidence, validator를 결합해 절차형 KG를 구축하는 방식입니다."
2. "CQ는 LLM이 만든 것이 아니라 연구자가 먼저 정의한 KG 요구사항이며, task/step/input/output/role/decision/risk/evidence/NCS-PCF 연결을 커버합니다."
3. "최종 Layer 2 KG는 179 nodes와 906 edges이고, 모든 final edge는 evidence anchor와 source triple을 갖습니다."
4. "LLM은 별도 실험에서 baseline, proposed, ablation 후보 생성기로 사용했고, Qwen3 계열 모델로 120개 evaluation chunk 실험을 수행했습니다."
5. "현재 수치는 구조 진단과 silver/proxy 진단이며, 논문용 최종 성능표는 human-gold 검수 이후 확정해야 합니다."

