# 교수님 보고용 핵심 요약: Prompt, CQ, Node/Edge 생성 방식

Generated: 2026-06-28  
Related detailed slide draft: `experiments/cape_kg_eacl_20260627/07_reports/professor_report_slide_contents_current_20260628_ko.md`  
Main traceability artifact: `experiments/cape_kg_eacl_20260627/06_release/prompt_node_edge_traceability.md`  
KG output directory: `outputs`

이 문서는 기존 상세 발표자료와 별개로, 교수님께 핵심만 설명하기 위한 압축 보고서입니다. 특히 다음 질문에 답하도록 구성했습니다.

- 어떤 프롬프트로 어떤 산출물을 만들었는가?
- CQ는 어떻게 만들었고, 실제 예시는 무엇인가?
- 최종 node와 edge는 각각 어떤 방식으로 생성했는가?
- 현재까지 나온 결과 중 무엇은 말할 수 있고, 무엇은 아직 claim하면 안 되는가?

---

## 1. 한 문장 요약

이번 연구는 한국어 수주/제안 업무 문서에서 **CQ-anchored, evidence-grounded, procedural KG**를 구축하고, 이를 **NCS/PCF 표준 taxonomy**와 연결하는 CAPE-KG 방법론으로 정리되었습니다.

가장 중요한 구분은 다음입니다.

| 구분 | 설명 |
|---|---|
| 최종 Layer 2 KG | LLM raw output을 그대로 저장한 결과가 아니라, OCR evidence anchor, task seed, 용어 사전, procedure template, schema validator를 결합해 만든 rule/schema/evidence 기반 graph |
| LLM 실험 | baseline/proposed/ablation/model-scaling 조건에서 node/edge/mapping 후보를 생성하고 비교하기 위한 실험 |
| 최종 성능 claim | human-gold annotation, IAA, adjudication, mapping expert review, NCS-PCF crosswalk expert review, active-review effort evidence 이후에만 가능 |

교수님께 보고할 때는 다음처럼 표현하는 것이 안전합니다.

> KG 구축과 실험 인프라는 완료되었고, 현재는 최종 논문 성능 주장을 확정하기 위한 사람 검수 단계가 남아 있습니다.

---

## 2. 현재까지의 핵심 결과

| 항목 | 값 | 의미 |
|---|---:|---|
| OCR clean sentences | 5,009 | 원문 문장을 sentence-level evidence anchor로 분해 |
| Layer 2 chunks | 214 | 전체 업무 KG 구축 단위 |
| Evaluation chunks | 120 | LLM baseline/proposed/ablation 비교 실험 subset |
| Layer 1 NCS nodes | 4,109 | NCS taxonomy 기반 표준축 |
| Layer 1 NCS edges | 4,085 | NCS 계층/능력단위 연결 |
| Layer 1 PCF nodes | 5,301 | PCF taxonomy 기반 표준축 |
| Layer 1 PCF edges | 2,004 | PCF 계층 연결 |
| PCF metric edges | 3,284 | PCF metric 연결 |
| Final Layer 2 nodes | 179 | 수주/제안 업무 KG node |
| Final Layer 2 edges | 906 | 수주/제안 업무 KG edge |
| NCS mapping candidates | 110 | Layer 2 task -> NCS 후보 |
| PCF mapping candidates | 110 | Layer 2 task -> PCF 후보 |

검증 결과:

| 검증 항목 | 결과 |
|---|---|
| Final nodes with evidence | 179 / 179 |
| Final edges with evidence | 906 / 906 |
| Final edges with source triples | 906 / 906 |
| Dangling edges | 0 |
| Pre-human handoff validation | PASS; current check count: see `../06_release/pre_human_handoff_validation.md` |
| Claim gate | FAIL, human-gold/IAA/adjudication 미완료 때문 |

---

## 3. 전체 방법론 흐름

```text
OCR sentence
-> sentence-level evidence anchor
-> task seed / alias / keyword matching
-> task frame construction
-> procedure template or inferred step construction
-> node generation
-> edge/triple generation
-> schema and evidence validation
-> final Layer 2 KG assembly
-> NCS/PCF standard bridge
-> LLM baseline/proposed/ablation comparison
-> human review handoff
```

핵심 설계 요소:

| 요소 | 역할 |
|---|---|
| CQ | KG가 답해야 할 질문을 먼저 정의 |
| Procedural schema | `DomainTask`, `ProcedureStep`, `Artifact`, `Role`, `DecisionGateway`, `GuardCondition`, `Principle`, `Risk` 등으로 업무 지식을 구조화 |
| Evidence grounding | node/edge를 OCR sentence evidence anchor에 연결 |
| Validator | predicate, node type, domain/range, evidence id, JSON 형식 점검 |
| Standard bridge | Layer 2 업무 KG를 NCS/PCF taxonomy와 연결 |
| Human review handoff | 최종 논문 claim을 위한 annotation/expert-review 입력 패키지 |

---

## 4. LLM을 어디에 사용했는가

LLM은 사용했습니다. 다만 최종 KG를 LLM raw output 그대로 만든 것이 아니라, 비교 실험과 후보 생성에 사용했습니다.

주요 모델/조건:

| 구분 | 내용 |
|---|---|
| 기본 LLM 실험 | Qwen3-8B strict JSON full run |
| 현실적 확장 실험 | Qwen3-14B, Qwen3-32B-AWQ diagnostic/model-scaling |
| 실험 단위 | 120 evaluation chunks |
| 출력 형식 | JSON object only |
| 검증 방식 | parse, evidence id, schema term, predicate, node type, mapping field 검증 |

---

## 5. 어떤 프롬프트로 무엇을 산출했는가

프롬프트는 두 층으로 구성됩니다.

1. `experiments/cape_kg_eacl_20260627/02_schema/prompts/*.txt`에 저장된 조건별 prompt intent
2. `scripts/run_cape_llm_condition_baselines.py`에서 동적으로 붙는 runtime prompt template

즉, 실제 LLM 호출은 "prompt 파일의 짧은 조건 설명 + chunk sentence + allowed schema + JSON shape + evidence rule"의 결합입니다.

| condition | family | 목적 | 산출 key |
|---|---|---|---|
| `B0_plain_llm` | baseline | schema 없이 일반 subject-predicate-object triple 추출 | `triples` |
| `B1_predicate_constrained` | baseline | 허용 predicate만 사용해 edge 후보 추출 | `edges` |
| `B2_current_project` | baseline | task frame을 먼저 추론한 뒤 Layer 2 schema로 후처리 | `nodes`, `edges` |
| `B3_edc_style` | baseline | extract-define-canonicalize 방식으로 open-schema item을 CAPE-compatible하게 변환 | `nodes`, `edges` |
| `B4_taxonomy_rag` | baseline | NCS/PCF/task taxonomy snippet을 retrieval context로 제공 | `nodes`, `edges`, `mappings` |
| `B5_procedural_prompt` | baseline | action, actor, gateway, guard condition, artifact flow 중심 추출 | `nodes`, `edges` |
| `B6_sac_kg_verifier_pruner` | baseline | generator 후보에 schema/evidence verifier와 pruning 적용 | `nodes`, `edges` |
| `P_cape_kg_actual` | proposed | CQ, evidence grounding, procedural schema, validator, NCS/PCF bridge 결합 | `nodes`, `edges`, `mappings` |
| `P_minus_CQ` | ablation | proposed에서 CQ anchoring 제거 | `nodes`, `edges`, `mappings` |
| `P_minus_Evidence` | ablation | proposed에서 evidence anchor 요구 약화 | `nodes`, `edges`, `mappings` |
| `P_minus_Procedural_schema` | ablation | procedural schema 대신 flat schema 사용 | `nodes`, `edges`, `mappings` |
| `P_minus_Validator` | ablation | post-hoc validator rejection 제거 | `nodes`, `edges`, `mappings` |
| `P_minus_Standard_bridge` | ablation | NCS/PCF bridge 출력 제거 | `nodes`, `edges` |
| `P_minus_Schema_retrieval` | ablation | chunk-specific schema/taxonomy retrieval 제거 | `nodes`, `edges`, `mappings` |

---

## 6. 실제 저장된 prompt 파일 원문

아래 문장이 실제 prompt 파일에 저장되어 있습니다.

| condition | prompt file text |
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

`P_minus_CQ`, `P_minus_Evidence`, `P_minus_Procedural_schema`, `P_minus_Validator`, `P_minus_Standard_bridge`는 별도 prompt 파일이 아니라 runtime condition으로 구현했습니다. 즉 `P_cape_kg_actual`의 공통 template에서 특정 구성요소를 제거하거나 약화한 조건입니다.

---

## 7. 실제 runtime 공통 프롬프트

아래는 모든 조건에 공통으로 붙는 runtime prompt의 핵심 원문입니다.

```text
Return ONLY one valid JSON object. No markdown. No explanation.
Every extracted item must include at least one evidence_anchor_ids value from the chunk.
Do not use outside knowledge. Keep Korean labels when the source text is Korean.

Chunk metadata:
chunk_id: {chunk_id}
pages: {page_start}..{page_end}
sentence_ids: {sentence_ids}

Chunk sentences:
{sentence_id}: {sentence_text}
...
```

Strict JSON 실행에서는 다음 계약을 system prompt에 추가했습니다.

```text
Strict JSON contract:
- Return exactly one JSON object and nothing else.
- The first non-whitespace character must be `{` and the last non-whitespace character must be `}`.
- Do not include markdown, code fences, comments, XML tags, `<think>` blocks, prose, or explanations.
- For Qwen/Qwen-style chat models, obey `/no_think`; do not emit hidden or visible reasoning.
- Output the JSON object immediately without a preamble.
- Use compact JSON without indentation or extra whitespace to reduce truncation risk.
- Use double-quoted JSON strings only.
- Use empty arrays for absent `nodes`, `edges`, `triples`, or `mappings` fields required by the requested shape.
```

---

## 8. `P_cape_kg_actual` 실제 runtime 프롬프트 핵심

`P_cape_kg_actual`의 실제 runtime instruction은 다음 구조입니다.

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
{retrieved NCS/PCF candidate snippets}

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

해석:

- `nodes`는 업무 개념 후보입니다.
- `edges`는 업무 개념 사이의 절차/입출력/역할/의사결정 관계 후보입니다.
- `mappings`는 Layer 2 업무 task를 NCS/PCF 후보와 연결하는 후보입니다.
- 모든 항목은 현재 chunk의 sentence id를 evidence로 가져야 합니다.

---

## 9. CQ는 어떻게 생성했는가

CQ는 LLM이 자동 생성한 것이 아니라, 연구자가 먼저 정의한 **KG 요구사항**입니다.

생성 절차:

| 단계 | 설명 |
|---|---|
| 1. 연구 문제 정의 | 한국어 수주/제안 업무 문서에서 절차형 업무 지식을 KG로 구축하는 문제로 정의 |
| 2. KG가 답해야 할 질문 범주 설정 | 업무 구성, 절차 순서, 입력 자료, 산출물, 수행 역할, 의사결정, 조건, 산출물 흐름, evidence, NCS/PCF mapping |
| 3. 질문을 schema에 연결 | 각 CQ를 node type 또는 predicate에 연결 |
| 4. 재사용 | schema 설계, LLM prompt, validator, CQ answerability evaluation에서 동일 CQ 사용 |

CQ 원본 파일:

| 역할 | 파일 |
|---|---|
| EACL 실험용 CQ | `experiments/cape_kg_eacl_20260627/02_schema/competency_questions.json` |
| 내부 KG build용 CQ | `outputs/03_schema/competency_questions.json` |
| traceability 문서 | `experiments/cape_kg_eacl_20260627/06_release/prompt_node_edge_traceability.md` |

---

## 10. CQ 실제 목록

| CQ | 질문 | 연결 predicate |
|---|---|---|
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

발표용 해석:

- CQ2와 CQ3 때문에 input artifact와 output artifact를 분리했습니다.
- CQ5와 CQ6 때문에 decision gateway와 guard condition을 별도 node/edge로 표현했습니다.
- CQ7 때문에 산출물이 다음 업무로 흐르는 `FEEDS_INTO`, `USED_AS_INPUT_FOR` 관계를 만들었습니다.
- CQ11과 CQ12 때문에 Layer 2 업무 KG를 NCS/PCF 표준 taxonomy와 연결했습니다.

---

## 11. Node는 어떻게 생성했는가

최종 Layer 2 node는 총 179개입니다.

기본 생성 방식:

| 단계 | 설명 |
|---|---|
| 1. Task seed 정의 | `TASK_SEEDS`에 수주/제안 업무 task의 label, alias, keyword를 정의 |
| 2. Evidence 검색 | OCR sentence에서 task keyword/alias/label이 등장하는 sentence를 찾음 |
| 3. Term matching | artifact, role, decision, principle, risk 용어 목록을 evidence sentence에서 매칭 |
| 4. Input/output 판정 | `작성`, `수립`, `개발`, `도출`, `생성`, `산출`, `제출` 등은 output signal, `기반`, `활용`, `검토`, `정보`, `요구조건`, `수집` 등은 input signal로 사용 |
| 5. Procedure step 생성 | task별 procedure template이 있으면 사용하고, 없으면 frame의 입력/산출물에서 step label을 추론 |
| 6. Evidence anchor 부착 | 모든 node에 `evidence_anchor_ids`를 연결 |

Node type별 수량과 생성 규칙:

| node type | count | generation rule |
|---|---:|---|
| `ProcedureStep` | 99 | task별 procedure template 또는 입력/산출물 기반 step 추론으로 생성 |
| `DomainTask` | 22 | `TASK_SEEDS`의 label/alias/keyword로 OCR sentence evidence를 검색해 생성 |
| `Artifact` | 14 | task evidence 안의 입력물/산출물 용어 매칭으로 생성 |
| `GuardCondition` | 13 | 의사결정 evidence에서 조건/가능성/경쟁/자원 등 조건 표현을 정규식으로 추출 |
| `Role` | 10 | 수행자/책임 주체 용어 매칭으로 생성 |
| `ArtifactFlow` | 9 | 특정 산출물이 다음 task 입력으로 쓰이는 규칙에서 생성 |
| `Principle` | 5 | 원칙/품질 기준 용어 매칭으로 생성 |
| `DecisionGateway` | 4 | 의사결정 관련 용어 매칭으로 생성 |
| `Risk` | 3 | 위험/불리함/실패 가능성 용어 매칭으로 생성 |

실제 node 예시:

```json
{
  "node_id": "L2_TASK_OPPORTUNITY_ASSESSMENT",
  "label": "기회분석",
  "type": "DomainTask",
  "label_en": "Opportunity Assessment",
  "evidence_anchor_ids": ["EA-JS-00235", "EA-JS-00251", "EA-JS-00275"],
  "review_status": "accepted_by_rule_pending_human_review"
}
```

이 예시는 `기회분석`이라는 업무 task를 OCR sentence evidence에 근거해 `DomainTask` node로 만든 것입니다.

---

## 12. Edge는 어떻게 생성했는가

최종 Layer 2 edge는 총 906개입니다.

기본 생성 방식:

| 단계 | 설명 |
|---|---|
| 1. Task frame slot 연결 | task/step의 inputs, outputs, roles, principles, risks slot을 각각 정해진 predicate로 연결 |
| 2. Procedure relation 생성 | `DomainTask -> ProcedureStep`은 `HAS_STEP`, step 순서는 `PRECEDES`로 연결 |
| 3. Decision relation 생성 | task/step에서 발견된 decision node는 `HAS_DECISION_GATEWAY`, 조건은 `HAS_GUARD_CONDITION`으로 연결 |
| 4. Artifact flow 생성 | 특정 산출물이 다음 task 입력으로 사용되면 `FEEDS_INTO`, `USED_AS_INPUT_FOR` 생성 |
| 5. Schema-valid triple화 | edge를 triple로 변환하고 `source_triple_ids`를 부착 |
| 6. Final validation | dangling edge, missing evidence, domain/range 위반을 점검 |

Predicate별 수량과 생성 규칙:

| predicate | count | generation rule |
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
| `FEEDS_INTO` | 9 | Artifact가 다음 task로 흘러가는 규칙을 연결 |
| `USED_AS_INPUT_FOR` | 9 | Artifact가 다음 task 입력으로 사용되는 규칙을 연결 |

실제 edge 예시:

```json
{
  "source_id": "L2_TASK_OPPORTUNITY_ASSESSMENT",
  "predicate": "USES_INPUT",
  "target_id": "L2_ARTIFACT_ARTIFACT_CAPTURE_PLAN",
  "evidence_anchor_ids": ["EA-JS-00235", "EA-JS-00251"],
  "source_triple_ids": ["TRI-172819a19da42b42"],
  "review_status": "accepted_by_rule"
}
```

이 예시는 `기회분석` task가 `Capture Plan` artifact를 입력으로 사용한다는 관계입니다.

---

## 13. LLM 조건별 출력 수량

아래 표는 120 evaluation chunks 기준 valid JSON output 수량입니다. 이 수량은 성능이 아니라 산출 coverage입니다.

| condition | rows | triples | nodes | edges | mappings |
|---|---:|---:|---:|---:|---:|
| `B0_plain_llm` | 120 | 1,037 | 0 | 0 | 0 |
| `B1_predicate_constrained` | 120 | 0 | 0 | 805 | 0 |
| `B2_current_project` | 120 | 0 | 867 | 334 | 0 |
| `B3_edc_style` | 120 | 0 | 769 | 263 | 0 |
| `B4_taxonomy_rag` | 120 | 0 | 719 | 323 | 126 |
| `B5_procedural_prompt` | 120 | 0 | 1,307 | 302 | 0 |
| `B6_sac_kg_verifier_pruner` | 120 | 0 | 2,281 | 361 | 107 |
| `P_cape_kg_actual` | 120 | 0 | 576 | 373 | 227 |
| `P_minus_CQ` | 120 | 0 | 586 | 391 | 233 |
| `P_minus_Evidence` | 120 | 0 | 574 | 383 | 227 |
| `P_minus_Procedural_schema` | 120 | 0 | 558 | 353 | 212 |
| `P_minus_Schema_retrieval` | 120 | 0 | 568 | 417 | 216 |
| `P_minus_Standard_bridge` | 120 | 0 | 577 | 405 | 0 |
| `P_minus_Validator` | 120 | 0 | 570 | 375 | 229 |

해석:

- `B0_plain_llm`은 schema가 없어서 `triples`만 산출합니다.
- schema-aware 조건은 `nodes`와 `edges`를 산출합니다.
- taxonomy bridge 조건은 `mappings`도 산출합니다.
- `P_cape_kg_actual`은 node/edge/mapping을 모두 산출하지만, 최종 성능 우수성은 human-gold scoring 후에만 주장할 수 있습니다.

---

## 14. NCS/PCF mapping 후보는 어떻게 만들었는가

Mapping은 Layer 2 task를 외부 표준 taxonomy와 연결하기 위한 후보 생성 단계입니다.

| mapping | count | 의미 |
|---|---:|---|
| NCS mapping candidates | 110 | Layer 2 task -> NCS competency unit 후보 |
| PCF mapping candidates | 110 | Layer 2 task -> PCF process element 후보 |

후보 생성 기준:

| score signal | 설명 |
|---|---|
| name similarity | task label과 target label의 명칭 유사도 |
| definition/description similarity | task definition과 taxonomy description의 유사도 |
| hierarchy context similarity | taxonomy 계층 맥락 유사도 |
| action verb similarity | 업무 동사 유사도 |
| level compatibility | task와 taxonomy level의 호환성 |
| domain gap penalty | 도메인 차이가 클 때 penalty |

실제 mapping 후보 예시:

| source task | standard | candidate | rank | score | status |
|---|---|---|---:|---:|---|
| 기회분석 | PCF | 기회 수주 계획 수립 | 1 | 0.2760 | pending_review |
| 기회분석 | NCS | 배관 및 Unit 설치(기장) | 1 | 0.0257 | pending_review |

주의:

- mapping 후보는 생성되었지만 expert review 전입니다.
- 위 NCS 예시는 확정 mapping이 아니라 낮은 점수의 자동 후보입니다. 이 때문에 expert review가 필요합니다.
- 따라서 Hit@K, MRR, nDCG, explanation quality 같은 downstream mapping 성능 claim은 아직 하면 안 됩니다.

---

## 15. 현재 말할 수 있는 것과 아직 말하면 안 되는 것

| 구분 | 말할 수 있는 표현 | 아직 말하면 안 되는 표현 |
|---|---|---|
| KG 구축 | Layer 1 NCS/PCF KG와 Layer 2 procedural KG 구축 완료 | 사람 검수까지 끝난 gold KG라고 표현 |
| Evidence | final node/edge가 evidence anchor를 가진다 | evidence correctness가 human-gold로 입증되었다고 표현 |
| LLM 실험 | 120 chunks에서 baseline/proposed/ablation 생성 완료 | CAPE-KG가 human-gold 기준으로 baseline보다 우수하다고 단정 |
| 구조 진단 | ontology conformance, procedural consistency, CQ answerability는 자동 진단 완료 | 구조 진단을 최종 품질 성능으로 과장 |
| mapping | NCS/PCF 후보 생성 완료 | expert-reviewed mapping 성능 완료 |
| main table | claimability table은 있음 | final human-gold performance main table 완성 |

현재 claim gate가 FAIL인 이유:

| blocker | 현재 상태 |
|---|---|
| adjudicated human-gold chunks | 0 / 100 |
| human-gold node/edge/evidence items | 0 / 500 |
| IAA | 미계산 |
| proposed human-gold scoring | 미완료 |
| mapping expert review | 미완료 |

이 FAIL은 실험 실패가 아니라, human-gold 없이 과도한 논문 주장을 하지 않도록 막는 보수적 안전장치입니다.

---

## 16. 교수님께 보고할 때의 핵심 메시지

발표에서 가장 먼저 말할 내용:

> 저는 한국어 수주/제안 업무 문서에서 절차형 업무 지식을 추출하기 위해 CAPE-KG 방법론을 적용했습니다. 이 방법론은 CQ로 추출 목표를 정의하고, evidence anchor로 원문 근거를 연결하며, procedural schema와 validator를 통해 node/edge를 통제하고, 최종적으로 NCS/PCF 표준 taxonomy와 연결합니다.

방법론 차별점:

| 차별점 | 설명 |
|---|---|
| CQ-anchored | KG가 답해야 할 질문을 먼저 정의하고 schema/prompt/evaluation에 연결 |
| Evidence-grounded | 모든 최종 node/edge가 원문 sentence evidence로 돌아갈 수 있음 |
| Procedural KG | 단순 entity graph가 아니라 task, step, input, output, role, decision, condition, risk를 표현 |
| Standard bridge | 내부 업무 KG를 NCS/PCF 외부 표준과 연결 |
| Claim-safe evaluation | human-gold 전에는 silver/proxy diagnostic과 최종 성능 claim을 분리 |

현재 상태:

> 자동 구축과 실험 실행은 완료되었고, 이제 남은 핵심은 human-gold annotation, IAA, adjudication, mapping expert review를 완료해 final performance table을 확정하는 것입니다.

---

## 17. 발표 슬라이드로 옮길 때 추천 구성

핵심 슬라이드는 다음 8장으로 충분합니다.

| slide | 제목 | 핵심 내용 |
|---|---|---|
| 1 | 연구 목표 | 한국어 수주/제안 문서에서 evidence-grounded procedural KG 구축 |
| 2 | 방법론 개요 | CQ, schema, evidence, validator, standard bridge |
| 3 | 실제 prompt 설계 | baseline/proposed/ablation 조건과 output key |
| 4 | CQ 설계 | 12개 CQ와 predicate 연결 |
| 5 | Node 생성 방식 | task seed, term matching, procedure step, evidence anchor |
| 6 | Edge 생성 방식 | slot-to-predicate, procedure relation, decision relation, artifact flow |
| 7 | 현재 결과 | Layer 1/2 수량, LLM output 수량, mapping 후보 |
| 8 | 남은 단계 | human-gold, IAA, adjudication, expert review, final main table |

---

## 18. 핵심 파일 위치

| 목적 | 파일 |
|---|---|
| 상세 발표자료 원고 | `experiments/cape_kg_eacl_20260627/07_reports/professor_report_slide_contents_current_20260628_ko.md` |
| 이 핵심 요약 파일 | `experiments/cape_kg_eacl_20260627/07_reports/professor_report_final_core_prompt_cq_node_edge_20260628_ko.md` |
| prompt/node/edge traceability | `experiments/cape_kg_eacl_20260627/06_release/prompt_node_edge_traceability.md` |
| CQ 원본 | `experiments/cape_kg_eacl_20260627/02_schema/competency_questions.json` |
| prompt 파일 | `experiments/cape_kg_eacl_20260627/02_schema/prompts/` |
| runtime prompt builder | `scripts/run_cape_llm_condition_baselines.py` |
| final node 파일 | `outputs/07_layer2_graph/layer2_nodes.jsonl` |
| final edge 파일 | `outputs/07_layer2_graph/layer2_edges.jsonl` |
| NCS mapping 후보 | `outputs/08_mapping/l2_ncs_mapping_candidates.jsonl` |
| PCF mapping 후보 | `outputs/08_mapping/l2_pcf_mapping_candidates.jsonl` |
| claimable main table | `experiments/cape_kg_eacl_20260627/06_release/claimable_main_table.md` |
| claim gate | `experiments/cape_kg_eacl_20260627/06_release/claim_gate_report.md` |
| pre-human validation | `experiments/cape_kg_eacl_20260627/06_release/pre_human_handoff_validation.md` |
