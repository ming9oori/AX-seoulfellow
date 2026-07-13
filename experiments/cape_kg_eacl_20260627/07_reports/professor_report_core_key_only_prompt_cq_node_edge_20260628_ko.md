# 교수님 보고용 핵심 요약본: Prompt, CQ, Node/Edge 산출 방식

Generated: 2026-06-28  
Detailed slide draft: `experiments/cape_kg_eacl_20260627/07_reports/professor_report_slide_contents_current_20260628_ko.md`  
Traceability source: `experiments/cape_kg_eacl_20260627/06_release/prompt_node_edge_traceability.md`  
Runtime prompt code: `scripts/run_cape_llm_condition_baselines.py`

이 문서는 기존 상세 슬라이드 원고와 별개로, 교수님께 핵심만 빠르게 보고하기 위한 별도 요약본입니다. 초점은 다음 네 가지입니다.

1. 어떤 방법론으로 KG를 구축했는가
2. 어떤 실제 prompt로 어떤 산출물을 만들었는가
3. CQ를 어떻게 생성했고 어떻게 사용했는가
4. node와 edge를 각각 어떤 방식으로 산출했는가

---

## 1. 핵심 결론

본 연구는 한국어 수주/제안 업무 문서에서 **evidence-grounded procedural knowledge graph**를 구축하고, 이를 **NCS/PCF 표준 taxonomy**와 연결하는 CAPE-KG 방법론을 적용한 실험입니다.

가장 중요한 해석은 다음입니다.

> 최종 Layer 2 KG는 LLM 출력물을 그대로 저장한 결과가 아닙니다. OCR sentence evidence, task seed, 용어 사전, procedure template, schema validator를 결합해 rule/schema/evidence 기반으로 조립한 graph입니다. LLM은 baseline, proposed, ablation 조건에서 node/edge/mapping 후보를 생성하고 비교하는 실험에 사용했습니다.

현재까지 자동 구축은 완료되었지만, 논문에서 최종 성능 우수성을 주장하려면 human-gold annotation, IAA, adjudication, mapping expert review, NCS-PCF crosswalk expert review, active-review effort evidence가 필요합니다.

---

## 2. 현재 구축 결과

| 항목 | 결과 |
|---|---:|
| OCR clean sentences | 5,009 |
| Evidence anchors | 5,009 |
| Layer 2 chunks | 214 |
| LLM evaluation chunks | 120 |
| Layer 1 NCS nodes | 4,109 |
| Layer 1 PCF nodes | 5,301 |
| Final Layer 2 nodes | 179 |
| Final Layer 2 edges | 906 |
| NCS mapping candidates | 110 |
| PCF mapping candidates | 110 |
| Visualization/export | HTML, GraphML, Neo4j CSV, RDF/SHACL |

발표 시 표현:

- "KG 구축과 실험 인프라는 완료되었습니다."
- "현재 LLM 성능 수치는 human-gold 전 단계의 silver/proxy 또는 diagnostic 결과입니다."
- "최종 main table은 사람 검수 이후 확정해야 합니다."

---

## 3. 방법론 전체 흐름

```text
OCR sentence
-> evidence anchor 생성
-> task seed / keyword matching
-> procedure frame 구성
-> node 생성
-> edge/triple 생성
-> schema/evidence validation
-> Layer 2 KG assembly
-> NCS/PCF standard bridge
-> LLM baseline/proposed/ablation 비교
-> human review handoff
```

CAPE-KG의 핵심은 LLM 단독 추출이 아니라 **CQ, schema, evidence, validator, standard bridge**를 함께 사용해 KG 생성을 통제했다는 점입니다.

---

## 4. LLM 실험 조건과 산출물

LLM 실험은 baseline, proposed, ablation 조건으로 구성했습니다.

| condition | 목적 | 산출 key |
|---|---|---|
| `B0_plain_llm` | schema 없는 일반 subject-predicate-object triple extraction | `triples` |
| `B1_predicate_constrained` | 허용 predicate만 사용하는 edge extraction | `edges` |
| `B2_current_project` | task frame을 먼저 만들고 Layer 2 schema로 후처리 | `nodes`, `edges` |
| `B3_edc_style` | open-schema item을 extract/define/canonicalize 후 CAPE-compatible 구조로 변환 | `nodes`, `edges` |
| `B4_taxonomy_rag` | NCS/PCF/task taxonomy snippet을 retrieval context로 제공 | `nodes`, `edges`, `mappings` |
| `B5_procedural_prompt` | action, actor, gateway, guard, artifact flow 중심 절차형 추출 | `nodes`, `edges` |
| `B6_sac_kg_verifier_pruner` | generator 후보에 schema/evidence verifier와 pruning 적용 | `nodes`, `edges` |
| `P_cape_kg_actual` | 제안 방법론: CQ, evidence, procedural schema, validator, NCS/PCF bridge 결합 | `nodes`, `edges`, `mappings` |
| `P_minus_CQ` | 제안 방법론에서 CQ anchoring 제거 | `nodes`, `edges`, `mappings` |
| `P_minus_Evidence` | evidence anchor 요구 약화 | `nodes`, `edges`, `mappings` |
| `P_minus_Procedural_schema` | procedural schema 대신 flat schema 사용 | `nodes`, `edges`, `mappings` |
| `P_minus_Validator` | post-hoc validator rejection 제거 | `nodes`, `edges`, `mappings` |
| `P_minus_Standard_bridge` | NCS/PCF bridge 제거 | `nodes`, `edges` |
| `P_minus_Schema_retrieval` | chunk-specific schema/taxonomy retrieval 제거 | `nodes`, `edges`, `mappings` |

---

## 5. 실제 저장된 prompt 원문

아래는 `experiments/cape_kg_eacl_20260627/02_schema/prompts/`에 실제 저장된 prompt 파일 내용입니다. 실제 LLM 호출 시에는 이 문장에 runtime template, chunk sentence, sentence id, allowed schema, JSON output shape가 결합됩니다.

| condition | prompt file | 실제 prompt 원문 |
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

`P_minus_CQ`, `P_minus_Evidence`, `P_minus_Procedural_schema`, `P_minus_Validator`, `P_minus_Standard_bridge`는 별도 prompt 파일이 아니라 runtime condition으로 구현했습니다. 즉 `P_cape_kg_actual`의 공통 template에서 특정 구성요소를 제거하거나 약화한 조건입니다.

---

## 6. 실제 runtime prompt 공통 구조

실제 LLM 호출은 단순히 위 한 줄 prompt만 넣은 것이 아닙니다. `scripts/run_cape_llm_condition_baselines.py`가 아래 공통 구조를 붙여 runtime prompt를 구성했습니다.

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

schema-constrained 조건에서는 여기에 allowed node type, allowed edge predicate, JSON shape가 추가됩니다.

strict JSON 실행에서는 아래 조건도 system prompt에 추가했습니다.

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

## 7. `P_cape_kg_actual` runtime prompt 핵심

`P_cape_kg_actual`은 제안 방법론을 구현한 조건입니다. 실제 runtime prompt는 다음 정보를 포함합니다.

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

required JSON shape:

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

CQ는 LLM이 자동 생성한 결과가 아니라, 연구자가 먼저 정의한 **KG 요구사항**입니다.

생성 절차:

1. 연구 문제를 "한국어 수주/제안 업무 문서에서 절차형 KG를 구축하는 문제"로 정의했습니다.
2. KG가 답해야 할 질문을 업무 구성, 절차 순서, 입력, 산출물, 수행자, 의사결정, 조건, 원칙, risk, evidence, 표준 taxonomy 연결로 분해했습니다.
3. 각 질문을 필요한 node type과 edge predicate에 연결했습니다.
4. 이 CQ를 schema 설계, LLM prompt, validation, CQ answerability evaluation에 재사용했습니다.

관련 파일:

| 역할 | 파일 |
|---|---|
| EACL 실험용 CQ | `experiments/cape_kg_eacl_20260627/02_schema/competency_questions.json` |
| 내부 KG build용 CQ | `outputs/03_schema/competency_questions.json` |
| CQ/schema 생성 코드 | `scripts/build_ax_epak_internal_kg.py`, `scripts/build_cape_kg_eacl_experiment.py` |
| runtime prompt builder | `scripts/run_cape_llm_condition_baselines.py` |

---

## 9. CQ 실제 목록

| CQ | 질문 | 연결 predicate |
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

- CQ2/CQ3 때문에 input artifact와 output artifact를 분리했습니다.
- CQ5/CQ6 때문에 decision gateway와 guard condition을 별도 node/edge로 표현했습니다.
- CQ10 때문에 node/edge가 evidence anchor를 갖도록 설계했습니다.
- CQ11/CQ12 때문에 Layer 2 업무 KG를 NCS/PCF 표준 taxonomy와 연결했습니다.

---

## 10. Node는 어떻게 산출했는가

최종 node 파일: `outputs/07_layer2_graph/layer2_nodes.jsonl`  
최종 node 수: **179개**  
모든 final node는 evidence anchor를 갖습니다.

생성 흐름:

1. OCR sentence를 `EA-*` evidence anchor로 변환했습니다.
2. `TASK_SEEDS`의 label, alias, keyword로 관련 sentence를 찾았습니다.
3. task evidence 안에서 artifact, role, decision, principle, risk 후보를 용어 사전으로 추출했습니다.
4. 업무 단위를 `DomainTask` node로 만들었습니다.
5. task별 procedure template과 입력/산출물 구조를 이용해 `ProcedureStep` node를 만들었습니다.
6. 의사결정 문맥에서 `DecisionGateway`와 `GuardCondition`을 만들었습니다.
7. 산출물이 다음 업무 입력으로 쓰이는 경우 `ArtifactFlow`를 만들었습니다.
8. 모든 node에 `evidence_anchor_ids`, `source`, `review_status`를 붙였습니다.

| node type | count | 산출 방식 |
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

node 예시:

```json
{
  "node_id": "L2_TASK_OPPORTUNITY_ASSESSMENT",
  "label": "기회분석",
  "label_en": "Opportunity Assessment",
  "type": "DomainTask",
  "layer": "Layer2",
  "evidence_anchor_ids": ["EA-JS-00235", "EA-JS-00251", "EA-JS-00275"],
  "review_status": "accepted_by_rule_pending_human_review",
  "source": "jaije_ocr"
}
```

---

## 11. Edge는 어떻게 산출했는가

최종 edge 파일: `outputs/07_layer2_graph/layer2_edges.jsonl`  
최종 edge 수: **906개**  
모든 final edge는 evidence anchor와 source triple id를 갖습니다. dangling edge는 0개입니다.

생성 흐름:

1. task/procedure structure에서 subject node와 target node 후보를 만들었습니다.
2. 입력, 산출물, 수행자, 의사결정, 조건, 원칙, risk, 순서 정보를 predicate로 변환했습니다.
3. predicate는 allowed predicate 목록으로 제한했습니다.
4. edge마다 `source_id`, `target_id`, `predicate`, `evidence_anchor_ids`, `source_triple_ids`를 기록했습니다.
5. schema/domain/range/evidence validation을 통과한 edge만 final KG에 넣었습니다.

| predicate | count | 산출 방식 |
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

edge 예시:

```json
{
  "edge_id": "EDGE-257c3380629f4d96",
  "source_id": "L2_TASK_OPPORTUNITY_ASSESSMENT",
  "predicate": "USES_INPUT",
  "target_id": "L2_ARTIFACT_ARTIFACT_CAPTURE_PLAN",
  "evidence_anchor_ids": ["EA-JS-00235", "EA-JS-00251"],
  "source_triple_ids": ["TRI-172819a19da42b42"],
  "confidence": 0.785,
  "review_status": "accepted_by_rule"
}
```

---

## 12. 중간 산출물과 최종 산출물 연결

| 단계 | 파일 | 수량 |
|---|---|---:|
| Task catalog | `outputs/04_task_frames/canonical_task_catalog.json` | 22 tasks |
| Procedure structures | `outputs/05_procedure/procedure_structures_clean.jsonl` | 22 procedures / 99 steps |
| Schema-valid triples | `outputs/06_triples/layer2_triples_schema_valid.jsonl` | 906 |
| Final Layer 2 nodes | `outputs/07_layer2_graph/layer2_nodes.jsonl` | 179 |
| Final Layer 2 edges | `outputs/07_layer2_graph/layer2_edges.jsonl` | 906 |
| NCS mapping candidates | `outputs/08_mapping/l2_ncs_mapping_candidates.jsonl` | 110 |
| PCF mapping candidates | `outputs/08_mapping/l2_pcf_mapping_candidates.jsonl` | 110 |
| HTML viewer | `outputs/09_visualization/kg_viewer.html` | generated |
| Neo4j import | `outputs/11_neo4j_import_flat/` | generated |
| RDF/SHACL export | `outputs/12_rdf/` | generated |

---

## 13. LLM validated output 규모

아래 수치는 120개 evaluation chunks에 대한 LLM 조건별 validated output 규모입니다. 이 표는 "얼마나 생성했는가"를 보여주는 진단표이며, human-gold 기반 최종 성능표가 아닙니다.

| condition | valid rows | triples | nodes | edges | mappings |
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

---

## 14. 발표에서 강조할 핵심 문장

교수님께는 다음 순서로 설명하면 됩니다.

1. "제가 구축한 것은 단순 triple list가 아니라 원문 sentence evidence에 연결된 절차형 업무 KG입니다."
2. "CQ를 먼저 설계하고, CQ가 요구하는 task, step, input, output, role, decision, condition, evidence, NCS/PCF mapping을 schema로 만들었습니다."
3. "최종 KG의 node와 edge는 LLM raw output이 아니라 evidence, schema, validator를 거친 rule/schema/evidence 기반 graph입니다."
4. "LLM은 baseline/proposed/ablation 조건에서 후보를 생성하고 방법론을 비교하기 위해 사용했습니다."
5. "현재 자동 구축과 실험 인프라는 완료되었고, 최종 논문 성능 claim은 human-gold annotation과 adjudication 이후 확정해야 합니다."

---

## 15. 아직 남은 작업

| 작업 | 이유 |
|---|---|
| Human-gold annotation | 최종 precision/recall/F1 claim에 필요 |
| IAA 계산 | annotation 신뢰도 보고에 필요 |
| Adjudication | annotator disagreement 해소 |
| Mapping expert review | NCS/PCF mapping 후보의 최종 정답화 |
| Final main table 재계산 | 논문용 성능표 확정 |

현재 단계에서 가장 안전한 결론은 다음입니다.

> CAPE-KG의 구축 파이프라인, prompt 조건, CQ 설계, node/edge 산출 방식, LLM 비교 실험은 정리되어 있습니다. 다만 논문 최종 성능 주장은 사람 검수 이후로 보류해야 합니다.
