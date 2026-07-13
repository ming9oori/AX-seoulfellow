# 교수님 보고용 핵심 요약본: Prompt, CQ, Node/Edge 산출 방식

Generated: 2026-06-28  
Source detailed slide draft: `experiments/cape_kg_eacl_20260627/07_reports/professor_report_slide_contents_current_20260628_ko.md`  
Traceability source: `experiments/cape_kg_eacl_20260627/06_release/prompt_node_edge_traceability.md`  
Runtime prompt code: `scripts/run_cape_llm_condition_baselines.py`  
KG build code: `scripts/build_ax_epak_internal_kg.py`  
Experiment directory: `experiments/cape_kg_eacl_20260627`  
KG output directory: `outputs`

이 문서는 상세 슬라이드 원고와 별개로, 교수님께 핵심만 빠르게 설명하기 위한 별도 요약본입니다. 초점은 다음 네 가지입니다.

1. 어떤 방법론으로 KG를 만들었는가
2. 어떤 실제 prompt로 어떤 산출물을 만들었는가
3. CQ를 어떻게 정의했고, KG 구축과 평가에 어떻게 썼는가
4. 최종 node와 edge가 각각 어떤 방식으로 산출되었는가

---

## 1. 한 문장 요약

본 연구는 한국어 수주/제안 업무 문서에서 **CQ-anchored, evidence-grounded, procedural KG**를 구축하고, 이를 **NCS/PCF 표준 taxonomy**와 연결하는 CAPE-KG 방법론을 적용한 실험입니다.

가장 중요한 구분은 다음입니다.

| 구분 | 정확한 설명 |
|---|---|
| 최종 Layer 2 KG | LLM raw output을 그대로 저장한 것이 아니라, OCR evidence anchor, task seed, 용어 사전, procedure template, schema validator를 결합해 만든 rule/schema/evidence 기반 graph |
| LLM 실험 | baseline/proposed/ablation/model-scaling 조건에서 node, edge, mapping 후보를 생성하고 비교하기 위한 prediction experiment |
| 현재 claim 가능 | KG 구축 완료, evidence grounding 완료, 구조 진단 완료, LLM 조건별 실행 완료, NCS/PCF 후보 mapping 생성 완료 |
| 아직 claim 보류 | human-gold precision/recall/F1, IAA, adjudication 기반 main table, expert-reviewed mapping 성능 |

발표에서 사용할 안전한 표현:

> KG 구축과 실험 인프라는 완료되었고, 현재는 최종 논문 성능 주장을 확정하기 위한 사람 검수 단계가 남아 있습니다.

---

## 2. 현재까지의 핵심 산출물

| 항목 | 값 | 의미 |
|---|---:|---|
| OCR clean sentences | 5,009 | KG evidence의 원천 sentence |
| Evidence anchors | 5,009 | node/edge가 참조하는 sentence-level 근거 |
| Layer 2 chunks | 214 | 전체 업무 KG 구축 단위 |
| LLM evaluation chunks | 120 | baseline/proposed/ablation 비교 subset |
| Layer 1 NCS nodes | 4,109 | NCS 표준 taxonomy node |
| Layer 1 PCF nodes | 5,301 | PCF 표준 taxonomy node |
| Final Layer 2 nodes | 179 | 최종 업무 KG node |
| Final Layer 2 edges | 906 | 최종 업무 KG edge |
| Schema-valid triples | 906 | edge를 SPO/evidence 형식으로 표현한 중간 산출물 |
| NCS mapping candidates | 110 | Layer 2 task별 NCS 후보 |
| PCF mapping candidates | 110 | Layer 2 task별 PCF 후보 |

품질 진단:

| 검증 항목 | 결과 |
|---|---:|
| Final nodes with evidence | 179 / 179 |
| Final edges with evidence | 906 / 906 |
| Final edges with source triples | 906 / 906 |
| Dangling edges | 0 |
| Domain/range violations | 0 |
| Ontology conformance | 1.0000 |
| Procedural consistency | 0.9950 |
| CQ answerability | 0.9167, 12개 중 11개 answerable |

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

핵심은 LLM 단독 추출이 아니라 **CQ, procedural schema, evidence grounding, validator, standard bridge**를 함께 사용했다는 점입니다.

---

## 4. CQ는 어떻게 생성했는가

CQ는 LLM이 자동 생성한 문장이 아니라, 연구자가 먼저 설계한 **"이 KG가 답해야 하는 질문 목록"**입니다.

생성 절차:

1. 한국어 수주/제안 업무 문서에서 필요한 업무 지식을 정의했습니다.
2. 질문 범주를 task, step, input, output, role, decision, guard, artifact flow, evidence, NCS/PCF mapping으로 나누었습니다.
3. 각 CQ를 target predicate 또는 KG element에 연결했습니다.
4. 동일한 CQ를 schema 설계, LLM prompt, ablation, CQ answerability 평가에 재사용했습니다.

CQ source:

| 역할 | 파일 |
|---|---|
| EACL 실험용 CQ | `experiments/cape_kg_eacl_20260627/02_schema/competency_questions.json` |
| 내부 KG build용 CQ | `outputs/03_schema/competency_questions.json` |
| CQ/schema 생성 코드 | `scripts/build_ax_epak_internal_kg.py`, `scripts/build_cape_kg_eacl_experiment.py` |

실제 CQ 목록:

| CQ | 질문 | 연결 predicate/schema |
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
| CQ10 | 각 지식 항목은 원문 어느 chunk/page/span에 근거가 있는가? | evidence anchor |
| CQ11 | 특정 업무는 어떤 NCS 능력단위와 관련되는가? | NCS candidate mapping |
| CQ12 | 특정 업무는 PCF 프로세스 체계상 어디에 위치하는가? | PCF candidate mapping |

발표용 핵심 문장:

> CQ는 "무엇을 추출할 것인가"를 미리 고정하는 연구 설계 장치입니다. 그래서 KG schema, LLM prompt, evaluation이 같은 질문 집합을 기준으로 연결됩니다.

---

## 5. 실제 프롬프트 파일 원문

프롬프트 파일 위치:

```text
experiments/cape_kg_eacl_20260627/02_schema/prompts/
```

실제 저장된 조건별 프롬프트 원문:

| 조건 | 파일 | 저장된 원문 | 요구 산출물 |
|---|---|---|---|
| `B0_plain_llm` | `B0_plain_llm_triple_extraction.txt` | `Extract subject-predicate-object triples from the chunk. Return JSON only.` | `triples` |
| `B1_predicate_constrained` | `B1_predicate_constrained_llm.txt` | `Extract triples using only the allowed predicates. Return JSON only with evidence sentence ids.` | `edges` |
| `B2_current_project` | `B2_current_project_baseline.txt` | `Extract Task Frames, then triples, then post-process into the Layer2 schema.` | `nodes`, `edges` |
| `B3_edc_style` | `B3_edc_style_baseline.txt` | `Extract, define, and canonicalize open-schema KG items, then emit CAPE-compatible nodes and edges for scoring.` | `nodes`, `edges` |
| `B4_taxonomy_rag` | `B4_taxonomy_rag_baseline.txt` | `Retrieve NCS/PCF/task taxonomy snippets, then extract schema-constrained triples with evidence.` | `nodes`, `edges`, `mappings` |
| `B5_procedural_prompt` | `B5_procedural_prompt_baseline.txt` | `Extract actions, actors, gateways, guard conditions, artifact flows, and temporal/logical dependencies.` | `nodes`, `edges` |
| `B6_sac_kg_verifier_pruner` | `B6_sac_kg_verifier_pruner_baseline.txt` | `Use existing generator candidates, then apply schema/evidence verification and pruning in the style of SAC-KG. This is a deterministic approximation, not a full SAC-KG reproduction.` | `nodes`, `edges` |
| `P_cape_kg_actual` | `P_cape_kg.txt` | `Use CQ-linked schema retrieval, procedural frame extraction, evidence-span constrained relation extraction, span verification, ontology validation, procedural consistency checks, and active review scoring.` | `nodes`, `edges`, `mappings` |
| `P_minus_Schema_retrieval` | `P_minus_Schema_retrieval.txt` | `Run CAPE-KG without chunk-specific schema/taxonomy retrieval; keep CQ, evidence grounding, procedural schema, validation, and mapping output shape.` | `nodes`, `edges`, `mappings` |
| strict JSON | `strict_json_contract.txt` | JSON object만 반환, markdown/설명/XML/`<think>` 금지, `/no_think`, compact JSON, empty arrays 사용 | JSON parse 안정화 |

주의:

> 위 파일의 한 줄 문장은 조건별 핵심 지시문입니다. 실제 LLM 호출 때는 여기에 chunk sentence, sentence id, allowed node/edge schema, JSON shape, strict JSON contract가 결합됩니다.

---

## 6. 실제 Runtime Prompt 공통 Template

모든 LLM 조건에 공통으로 들어간 runtime prompt 핵심:

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

strict JSON 실행에서는 system/user prompt 앞뒤에 다음 제약이 추가되었습니다.

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

## 7. 실제 `P_cape_kg_actual` Prompt 핵심

제안 방법론 조건은 CQ, taxonomy snippet, evidence requirement, validator rule, allowed schema, JSON shape를 모두 포함합니다.

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

요구 JSON shape:

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

발표용 핵심 문장:

> 제안 프롬프트는 "그래프를 만들어줘"가 아니라, CQ, schema, evidence, standard mapping, JSON key까지 제한한 extraction contract입니다.

---

## 8. LLM 조건별 산출물 수량

Qwen3-8B strict JSON full run과 SAC-KG-style deterministic approximation 기준 validated output 요약입니다. 이 표는 출력량 진단이며, 최종 성능표가 아닙니다.

| 조건 | valid rows | triples | nodes | edges | mappings |
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

- B0는 자유 SPO triple만 산출합니다.
- B1은 predicate-constrained edge만 산출합니다.
- B2~B5는 node/edge 중심 후보를 산출합니다.
- B4와 P 계열은 NCS/PCF mapping 후보까지 산출할 수 있습니다.
- P_minus 조건들은 제안 방법론의 구성 요소를 하나씩 제거한 ablation입니다.

---

## 9. 최종 KG Node는 어떻게 산출했는가

최종 node 파일:

```text
outputs/07_layer2_graph/layer2_nodes.jsonl
```

생성 흐름:

1. OCR sentence를 `EA-JS-*` evidence anchor로 변환했습니다.
2. `TASK_SEEDS`의 업무 seed label, alias, keyword로 관련 sentence를 검색했습니다.
3. 검색된 sentence에서 Artifact, Role, DecisionGateway, Principle, Risk 후보를 용어 사전과 규칙으로 추출했습니다.
4. 각 task frame을 `DomainTask` node로 생성했습니다.
5. task별 procedure template 또는 입력/산출물 기반 추론으로 `ProcedureStep` node를 생성했습니다.
6. 산출물이 다음 업무 입력으로 쓰이는 규칙에서 `ArtifactFlow` node를 생성했습니다.
7. `node_id` 기준으로 중복 제거하고, 모든 node에 evidence와 review status를 부여했습니다.

Node type별 결과:

| Node type | 생성 방식 | 개수 |
|---|---|---:|
| `DomainTask` | 업무 seed와 evidence sentence 검색 | 22 |
| `ProcedureStep` | task별 procedure template 또는 입력/산출물 기반 step 추론 | 99 |
| `Artifact` | 입력/산출물 용어 매칭 | 14 |
| `Role` | 수행자/책임 주체 용어 매칭 | 10 |
| `DecisionGateway` | 의사결정 관련 표현 추출 | 4 |
| `GuardCondition` | 조건/가능성/경쟁/자원 등 조건 표현 추출 | 13 |
| `Principle` | 원칙/품질 기준 용어 매칭 | 5 |
| `Risk` | 위험/불리함/실패 가능성 용어 매칭 | 3 |
| `ArtifactFlow` | 산출물이 다음 task 입력으로 쓰이는 규칙 | 9 |

핵심 설명:

> 최종 node는 LLM이 임의로 만든 label 목록이 아니라, evidence anchor와 schema constraint를 만족하도록 조립된 업무 개념입니다.

---

## 10. 최종 KG Edge는 어떻게 산출했는가

최종 edge 파일:

```text
outputs/07_layer2_graph/layer2_edges.jsonl
```

생성 흐름:

1. task frame의 `inputs`, `outputs`, `roles`, `principles`, `risks` slot을 predicate로 변환했습니다.
2. decision gateway와 guard condition을 별도 predicate로 연결했습니다.
3. procedure step은 `HAS_STEP`, step 순서는 `PRECEDES`로 연결했습니다.
4. artifact flow 규칙은 `FEEDS_INTO`, `USED_AS_INPUT_FOR`로 연결했습니다.
5. 모든 edge를 triple record로 변환하고 `source_triple_ids`를 부여했습니다.
6. allowed predicate, source/target node 존재, evidence 존재 조건을 통과한 edge만 최종 graph에 남겼습니다.

Predicate별 결과:

| Predicate | 생성 방식 | 개수 |
|---|---|---:|
| `PRODUCES` | task/step의 outputs slot을 Artifact node로 연결 | 220 |
| `USES_INPUT` | task/step의 inputs slot을 Artifact 또는 Concept node로 연결 | 201 |
| `PERFORMED_BY` | task/step의 roles slot을 Role node로 연결 | 120 |
| `HAS_STEP` | DomainTask를 해당 ProcedureStep 목록에 연결 | 99 |
| `PRECEDES` | 같은 task 안에서 step order 기준으로 순서 연결 | 77 |
| `HAS_PRINCIPLE` | task/step의 principles slot을 Principle node로 연결 | 64 |
| `HAS_DECISION_GATEWAY` | task/step에서 발견된 의사결정 node 연결 | 54 |
| `HAS_RISK` | task/step의 risks slot 연결 | 39 |
| `HAS_GUARD_CONDITION` | DecisionGateway에서 추출된 조건 node 연결 | 14 |
| `FEEDS_INTO` | Artifact가 다음 task로 흘러가는 규칙 연결 | 9 |
| `USED_AS_INPUT_FOR` | Artifact가 다음 task 입력으로 사용되는 규칙 연결 | 9 |

검증 결과:

| 검증 항목 | 결과 |
|---|---:|
| Final Layer 2 edges | 906 |
| Evidence가 있는 edges | 906 / 906 |
| `source_triple_ids`가 있는 edges | 906 / 906 |
| Dangling edges | 0 |
| Type/domain-range violations | 0 |

핵심 설명:

> edge는 source node, target node, 허용 predicate, evidence anchor가 모두 유효한 경우에만 최종 graph에 포함되었습니다.

---

## 11. Triple, Node, Edge의 관계

| 단계 | 파일 | 현재 수량 | 의미 |
|---|---|---:|---|
| Task frame | `outputs/04_task_frames/canonical_task_catalog.json` | 22 | canonical 업무 단위 |
| Procedure structure | `outputs/05_procedure/procedure_structures_clean.jsonl` | 22 procedures / 99 steps | task별 step, order, decision 구조 |
| Schema-valid triple | `outputs/06_triples/layer2_triples_schema_valid.jsonl` | 906 | edge를 SPO/evidence 형태로 표현한 중간 산출물 |
| Final nodes | `outputs/07_layer2_graph/layer2_nodes.jsonl` | 179 | graph에 들어가는 node |
| Final edges | `outputs/07_layer2_graph/layer2_edges.jsonl` | 906 | 검증을 통과한 edge |

정리:

- node는 업무 개념입니다.
- edge는 node 사이의 관계입니다.
- triple은 edge를 subject-predicate-object와 evidence로 검증하기 위한 중간 표현입니다.
- 현재 triple 수와 edge 수는 906으로 같습니다.

---

## 12. NCS/PCF Standard Bridge

Layer 2 업무 KG를 외부 표준 체계와 연결하기 위해 NCS/PCF 후보 mapping을 생성했습니다.

| 항목 | 값 |
|---|---:|
| Canonical DomainTask | 22 |
| NCS mapping candidates | 110 |
| PCF mapping candidates | 110 |
| NCS Top-K coverage | 1.000 |
| PCF Top-K coverage | 1.000 |
| NCS-PCF crosswalk candidates | 220 |

주의:

> 현재 mapping은 후보 생성 단계입니다. 자동 후보를 정답으로 claim하지 않았고, expert review 후 acceptability를 주장해야 합니다.

---

## 13. 현재 claim 가능/불가능 범위

| 구분 | 현재 상태 | 발표 가능 표현 |
|---|---|---|
| KG 구축 | 완료 | Layer 1 표준 KG와 Layer 2 업무 KG 구축 완료 |
| Evidence grounding | 완료 | final node/edge가 sentence-level evidence에 연결됨 |
| 구조 진단 | 완료 | ontology conformance 1.0000, procedural consistency 0.9950 |
| LLM 조건 실행 | 완료 | 120 evaluation chunks 기준 baseline/proposed/ablation/model scaling 실행 |
| CQ answerability | 완료 | 12개 중 11개 CQ answerable |
| Human-gold annotation | 미완료 | 사람 검수 진행 후 최종 성능표 확정 |
| IAA/adjudication | 미완료 | annotator A/B 검수와 adjudication 필요 |
| Mapping expert review | 미완료 | NCS/PCF 후보의 expert-reviewed 성능은 아직 claim 보류 |

Claim gate가 막고 있는 필수 항목:

| gate | 의미 | 현재 상태 |
|---|---|---|
| `gold.completed_chunks` | adjudicated human-gold chunks >= 100 | 0 completed |
| `gold.item_count` | human-gold node/edge/evidence items >= 500 | 0 items |
| `gold.iaa` | two-annotator agreement computed | pending |
| `llm.proposed_human_gold_score` | `P_cape_kg_actual`을 adjudicated gold와 비교 | pending |

사람 검수 반환 파일 기준:

| 구분 | 파일 수 | 의미 |
|---|---:|---|
| Minimum paper-gate 반환 | 11 | annotation A/B 10개 JSONL + adjudication 1개 JSONL |
| Optional/strong 반환 | 3 | mapping expert review + NCS-PCF crosswalk expert review + active-review effort |
| 전체 추적 human-return 파일 | 14 | minimum 11개와 optional/strong 3개를 합친 workflow 추적 대상 |

---

## 14. 교수님께 설명할 때의 핵심 문장

1. "최종 KG는 LLM raw output이 아니라 evidence와 schema로 검증된 rule/schema/evidence 기반 graph입니다."
2. "LLM은 최종 KG를 그대로 만든 도구가 아니라, baseline/proposed/ablation 조건에서 후보 node/edge/mapping을 생성하고 비교하기 위해 사용했습니다."
3. "CQ는 추출 대상을 고정하는 연구 설계 장치이며, schema, prompt, evaluation을 연결합니다."
4. "Node는 task seed, evidence sentence, 용어 사전, procedure template으로 생성했고, edge는 predicate별 규칙과 evidence validation을 통과한 것만 저장했습니다."
5. "KG 구축과 실험 인프라는 완료되었지만, human-gold/IAA/adjudication 전에는 최종 precision/recall/F1 우수성을 주장하지 않습니다."
