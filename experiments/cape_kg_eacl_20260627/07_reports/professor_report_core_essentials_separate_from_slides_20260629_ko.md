# 교수님 보고용 핵심 요약본

Generated: 2026-06-29  
Source slide draft: `experiments/cape_kg_eacl_20260627/07_reports/professor_report_slide_contents_current_20260628_ko.md`  
Experiment directory: `experiments/cape_kg_eacl_20260627`  
KG output directory: `outputs`

이 문서는 기존 슬라이드별 발표 원고와 별개의 핵심 요약본입니다. 목적은 교수님께 다음 네 가지를 짧고 명확하게 설명하는 것입니다.

1. 어떤 연구 방법론을 적용했는가?
2. 어떤 프롬프트와 CQ를 사용했는가?
3. node와 edge를 각각 어떤 방식으로 산출했는가?
4. 현재까지 어떤 결과는 말할 수 있고, 어떤 결과는 아직 말하면 안 되는가?

---

## 1. 한 문장 요약

본 연구는 한국어 수주/제안 업무 문서에서 `task`, `procedure step`, `input/output artifact`, `role`, `decision`, `risk`를 evidence와 함께 추출해 Layer 2 업무 KG를 만들고, 이를 Layer 1 NCS/PCF 표준 taxonomy와 연결하는 **CAPE-KG 방법론**을 실험한 것이다.

핵심은 LLM에게 그래프를 자유롭게 만들게 한 것이 아니라, `Competency Question(CQ)`, `procedural schema`, `evidence anchor`, `validator`, `NCS/PCF bridge`를 결합해 통제된 KG 구축 및 평가 파이프라인을 만든 점이다.

---

## 2. 현재까지의 핵심 결과

| 항목 | 현재 값 | 의미 |
| --- | ---: | --- |
| OCR sentences / evidence anchors | 5,009 | KG 근거로 연결되는 sentence 단위 anchor |
| Layer 2 chunks | 214 | 전체 문서에서 생성된 업무 문서 chunk |
| Evaluation chunks | 120 | LLM baseline/proposed/ablation 비교용 chunk |
| Layer 1 NCS nodes | 4,109 | NCS 표준 taxonomy KG |
| Layer 1 PCF nodes | 5,301 | PCF 표준 taxonomy KG |
| Layer 2 KG nodes | 179 | 최종 업무 KG node |
| Layer 2 KG edges | 906 | 최종 업무 KG edge |
| Schema-valid triples | 906 | 최종 edge와 1:1로 연결되는 검증된 중간 triple |
| Final edges with evidence | 906 / 906 | 모든 최종 edge가 evidence anchor 보유 |
| Dangling final edges | 0 | source/target이 없는 edge 없음 |
| NCS mapping candidates | 110 | Layer 2 task to NCS 후보, expert review 전 |
| PCF mapping candidates | 110 | Layer 2 task to PCF 후보, expert review 전 |
| Pre-human validation | 88 checks, 87 PASS / 1 WARN | 사람 검수 전 handoff/release 인프라 준비 완료 |

현재 말할 수 있는 결론은 다음과 같다.

- Layer 1 NCS/PCF KG 구축은 완료되었다.
- Layer 2 업무 KG 구축도 완료되었다.
- 최종 Layer 2 node/edge는 모두 evidence anchor와 연결되어 있다.
- LLM baseline/proposed/ablation/model-scaling 실험 산출물은 생성되어 있다.
- Human review handoff, annotation protocol, IAA/adjudication placeholder, release bundle 검증까지 준비되어 있다.
- 그러나 human-gold annotation, IAA, adjudication, mapping expert review가 끝나지 않았으므로 최종 precision/recall/F1 성능 우수성은 아직 claim하면 안 된다.

---

## 3. 방법론의 핵심 구조

| 구성 요소 | 역할 |
| --- | --- |
| CQ | KG가 답해야 할 업무 질문을 먼저 정의 |
| Procedural schema | `DomainTask`, `ProcedureStep`, `Artifact`, `Role`, `DecisionGateway`, `GuardCondition`, `Risk` 등 node type 정의 |
| Evidence grounding | node/edge를 OCR sentence evidence anchor에 연결 |
| LLM conditions | baseline, proposed, ablation 조건별 prediction 생성 |
| Validator | JSON parse, schema, predicate, domain/range, evidence 조건 검증 |
| Standard bridge | Layer 2 업무 KG를 NCS/PCF 표준 taxonomy와 연결 |
| Human review handoff | human-gold, mapping review, active-review 검수 패키지 생성 |

중요한 구분은 다음과 같다.

| 구분 | 설명 |
| --- | --- |
| 최종 KG | `outputs/07_layer2_graph`에 저장된 rule/schema/evidence 기반 KG |
| LLM prediction | 120개 evaluation chunk에서 baseline/proposed/ablation 조건별로 생성한 실험 산출물 |
| 논문 main result | human-gold annotation 이후 LLM prediction을 adjudicated gold와 비교해 확정해야 하는 결과 |

---

## 4. CQ는 어떻게 만들었는가?

CQ는 LLM이 자동으로 만든 것이 아니라, 연구자가 먼저 정의한 **KG 요구사항**이다. 즉, "이 KG가 어떤 질문에 답할 수 있어야 하는가?"를 먼저 정하고, 그 질문을 node type과 edge predicate로 연결했다.

생성 절차는 다음과 같다.

1. 연구 문제를 정의했다.
   - 한국어 수주/제안 업무 문서에서 절차형 업무 지식을 KG로 구축한다.
   - 단순 entity extraction이 아니라 업무 순서, 입력, 산출물, 역할, 의사결정, 위험, evidence, 표준 taxonomy mapping을 표현한다.
2. 업무 KG가 답해야 할 질문 범주를 정했다.
   - 주요 업무와 절차 단계
   - 입력 자료와 산출물
   - 수행 역할
   - 의사결정 지점과 조건
   - 산출물 흐름
   - 원문 evidence grounding
   - NCS/PCF 표준 연결
3. 각 질문을 target predicate에 연결했다.
   - "각 Task는 어떤 입력 자료를 사용하는가?" -> `USES_INPUT`
   - "각 Task는 어떤 산출물을 생성하는가?" -> `PRODUCES`
   - "업무는 어떤 순서로 수행되는가?" -> `HAS_STEP`, `PRECEDES`
   - "의사결정 조건은 무엇인가?" -> `HAS_GUARD_CONDITION`
4. 같은 CQ를 schema 설계, LLM prompt, structural evaluation, CQ answerability 계산에 재사용했다.

관련 파일은 다음과 같다.

| 역할 | 파일 |
| --- | --- |
| EACL 실험 CQ | `experiments/cape_kg_eacl_20260627/02_schema/competency_questions.json` |
| 내부 KG build CQ | `outputs/03_schema/competency_questions.json` |
| CQ query와 sample answer | `experiments/cape_kg_eacl_20260627/06_release/cq_query_pack.md` |
| prompt/node/edge 추적 문서 | `experiments/cape_kg_eacl_20260627/06_release/prompt_node_edge_traceability.md` |

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

현재 구조 진단 기준으로 12개 CQ 중 대부분은 KG에서 answerable하며, CQ8의 review checkpoint는 별도 structural gap으로 추적하고 있다.

---

## 6. 실제 사용한 프롬프트

프롬프트는 두 층으로 구성되었다.

1. 조건별 prompt file: baseline/proposed/ablation의 핵심 지시문
2. runtime prompt: chunk sentence, sentence id, allowed schema, allowed predicate, JSON output shape, evidence rule을 결합한 실제 호출 프롬프트

### 6.1 공통 runtime 제약

```text
Return ONLY one valid JSON object; no markdown and no explanation.
Each item must use evidence_anchor_ids from the current chunk sentence_ids.
Do not use outside knowledge.
Keep Korean labels when the source text is Korean.
Use only the listed node types and edge predicates.
```

### 6.2 Strict JSON contract

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

### 6.3 조건별 prompt file 원문

| condition | prompt file | 저장된 프롬프트 원문 | 산출물 |
| --- | --- | --- | --- |
| B0_plain_llm | `B0_plain_llm_triple_extraction.txt` | `Extract subject-predicate-object triples from the chunk. Return JSON only.` | `triples` |
| B1_predicate_constrained | `B1_predicate_constrained_llm.txt` | `Extract triples using only the allowed predicates. Return JSON only with evidence sentence ids.` | `edges` |
| B2_current_project | `B2_current_project_baseline.txt` | `Extract Task Frames, then triples, then post-process into the Layer2 schema.` | `nodes`, `edges` |
| B3_edc_style | `B3_edc_style_baseline.txt` | `Extract, define, and canonicalize open-schema KG items, then emit CAPE-compatible nodes and edges for scoring.` | `nodes`, `edges` |
| B4_taxonomy_rag | `B4_taxonomy_rag_baseline.txt` | `Retrieve NCS/PCF/task taxonomy snippets, then extract schema-constrained triples with evidence.` | `nodes`, `edges`, `mappings` |
| B5_procedural_prompt | `B5_procedural_prompt_baseline.txt` | `Extract actions, actors, gateways, guard conditions, artifact flows, and temporal/logical dependencies.` | `nodes`, `edges` |
| B6_sac_kg_verifier_pruner | `B6_sac_kg_verifier_pruner_baseline.txt` | `Use existing generator candidates, then apply schema/evidence verification and pruning in the style of SAC-KG. This is a deterministic approximation, not a full SAC-KG reproduction.` | `nodes`, `edges` |
| P_cape_kg_actual | `P_cape_kg.txt` | `Use CQ-linked schema retrieval, procedural frame extraction, evidence-span constrained relation extraction, span verification, ontology validation, procedural consistency checks, and active review scoring.` | `nodes`, `edges`, `mappings` |
| P_minus_Schema_retrieval | `P_minus_Schema_retrieval.txt` | `Run CAPE-KG without chunk-specific schema/taxonomy retrieval; keep CQ, evidence grounding, procedural schema, validation, and mapping output shape.` | `nodes`, `edges`, `mappings` |

### 6.4 Proposed condition의 실제 runtime prompt 구조

아래는 `P_cape_kg_actual`에서 실제 호출 때 사용한 구조이다. `{taxonomy_context}`와 chunk 문장은 각 chunk마다 동적으로 채워졌다.

```text
/no_think

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
{taxonomy_context}

Rules:
- Every node, edge, and mapping must include evidence_anchor_ids from the chunk.
- Use only the listed node types and edge predicates. Invalid schema terms will be rejected.
- Do not use outside knowledge.
- Keep Korean labels when the source text is Korean.
- Prefer concise, reusable labels.
- Hard limit: return at most 5 nodes, at most 5 edges, and at most 3 mappings.
- If the chunk does not support a field, return an empty array for that field.

Allowed node types:
["Artifact", "ArtifactFlow", "DecisionGateway", "DomainTask", "GuardCondition", "Principle", "ProcedureStep", "ReviewCheckpoint", "Risk", "Role"]

Allowed edge predicates:
["BRANCHES_TO", "FEEDS_INTO", "HAS_DECISION_GATEWAY", "HAS_GUARD_CONDITION", "HAS_PRINCIPLE", "HAS_REVIEW_CHECKPOINT", "HAS_RISK", "HAS_STEP", "PERFORMED_BY", "PRECEDES", "PRODUCES", "USED_AS_INPUT_FOR", "USES_INPUT"]

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
      "source_label": "string",
      "target": "NCS or PCF candidate label/code",
      "target_system": "NCS or PCF",
      "evidence_anchor_ids": ["sentence ids"],
      "confidence": 0.0
    }
  ]
}
```

---

## 7. LLM 실험에서 생성된 산출물 수량

아래 수량은 human-gold 성능이 아니라, 120개 evaluation chunk에서 조건별 valid JSON 산출물이 얼마나 생성되었는지를 보여주는 실행 결과이다.

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

주의: 이 표는 "많이 뽑았다"는 실행 진단일 뿐이며, 품질 성능표는 아니다. 최종 precision/recall/F1은 사람 검수 gold가 들어온 뒤 계산해야 한다.

---

## 8. Node는 어떻게 산출했는가?

최종 Layer 2 KG node는 총 179개이다. 모든 node는 evidence anchor를 가진다.

| node type | count | 생성 방식 |
| --- | ---: | --- |
| DomainTask | 22 | TASK_SEEDS의 label/alias/keyword로 OCR sentence evidence를 검색해 생성 |
| ProcedureStep | 99 | task별 procedure template 또는 입력/산출물 기반 step 추론으로 생성 |
| Artifact | 14 | task evidence 안의 입력물/산출물 용어 매칭으로 생성 |
| Role | 10 | 수행자/책임 주체 용어 매칭으로 생성 |
| DecisionGateway | 4 | 의사결정 관련 용어 매칭으로 생성 |
| GuardCondition | 13 | 의사결정 evidence에서 조건/가능성/경쟁/자원 등 조건 표현을 추출 |
| Principle | 5 | 원칙/품질 기준 용어 매칭으로 생성 |
| Risk | 3 | 위험/불리함/실패 가능성 용어 매칭으로 생성 |
| ArtifactFlow | 9 | 특정 산출물이 다음 task 입력으로 쓰이는 규칙에서 생성 |

요약하면 node는 임의 생성이 아니라 `task seed`, `용어 사전`, `procedure template`, `evidence sentence`, `schema type`을 결합해 생성했다.

---

## 9. Edge는 어떻게 산출했는가?

최종 Layer 2 KG edge는 총 906개이다. 모든 edge는 evidence anchor와 `source_triple_ids`를 가진다.

| predicate | count | 생성 방식 |
| --- | ---: | --- |
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

edge 생성의 핵심 조건은 다음과 같다.

- source node와 target node가 모두 존재해야 한다.
- predicate가 schema에서 허용된 관계여야 한다.
- edge마다 evidence anchor가 있어야 한다.
- 최종 dangling edge는 0개여야 한다.

---

## 10. 주요 산출 파일

| 목적 | 파일 |
| --- | --- |
| 최종 Layer 2 nodes | `outputs/07_layer2_graph/layer2_nodes.jsonl` |
| 최종 Layer 2 edges | `outputs/07_layer2_graph/layer2_edges.jsonl` |
| schema-valid triples | `outputs/06_triples/layer2_triples_schema_valid.jsonl` |
| 프롬프트/node/edge 추적 | `experiments/cape_kg_eacl_20260627/06_release/prompt_node_edge_traceability.md` |
| annotation protocol 추적 | `experiments/cape_kg_eacl_20260627/06_release/annotation_protocol_traceability.md` |
| claim 가능한 결과 표 | `experiments/cape_kg_eacl_20260627/06_release/claimable_main_table.md` |
| pre-human validation | `experiments/cape_kg_eacl_20260627/06_release/pre_human_handoff_validation.md` |
| KG viewer | `outputs/09_visualization/kg_viewer.html` |
| Neo4j import CSV | `outputs/11_neo4j_import_flat/` |

---

## 11. 발표에서 안전하게 말할 수 있는 것

다음 표현은 현재 산출물 기준으로 안전하다.

- "Layer 1 NCS/PCF KG와 Layer 2 업무 KG 구축은 완료했습니다."
- "최종 Layer 2 KG는 179 nodes, 906 edges이며, 모든 edge가 evidence anchor에 연결되어 있습니다."
- "LLM baseline/proposed/ablation 조건을 120개 evaluation chunk에 대해 실행했고, valid JSON 산출물을 확보했습니다."
- "CAPE-KG는 CQ, procedural schema, evidence grounding, validator, NCS/PCF bridge를 결합한 방법론입니다."
- "사람 검수 전 handoff/release 검증은 PASS 상태입니다."

---

## 12. 아직 말하면 안 되는 것

다음 표현은 아직 하면 안 된다.

- "CAPE-KG가 baseline보다 최종 F1이 높다."
- "NCS/PCF mapping이 정확하다고 검증되었다."
- "Active review가 실제 사람 검수 시간을 줄였다."
- "Human-gold 기준으로 성능이 확정되었다."

이유는 human-gold annotation, IAA, adjudication, mapping expert review, crosswalk expert review, active-review effort evidence가 아직 반환되지 않았기 때문이다.

---

## 13. 다음 단계

| 단계 | 필요 작업 | 완료 후 가능해지는 것 |
| --- | --- | --- |
| Human-gold annotation | annotator A/B가 priority-100 chunk 검수 파일 반환 | IAA 계산 |
| Adjudication | adjudicator가 최종 gold 확정 | 최종 human-gold dataset 생성 |
| Human-gold scoring | proposed/baseline prediction과 gold 비교 | 논문 main table의 precision/recall/F1 확정 |
| Mapping expert review | NCS/PCF 후보 검수 | mapping P@K, MRR, nDCG claim 가능 |
| Crosswalk expert review | NCS-PCF 연결 후보 검수 | bridge utility claim 가능 |
| Active-review effort 기록 | 검수 시간/수정량 반환 | active review 효율 claim 가능 |

---

## 14. 교수님께 보고할 핵심 결론

현재 연구는 **KG 구축 단계와 실험 인프라 구축 단계는 완료**되었다고 말할 수 있다. 특히 CAPE-KG의 핵심 구성인 CQ 기반 schema 설계, evidence-grounded node/edge 생성, NCS/PCF bridge, LLM 조건별 실험, 검수 handoff가 모두 연결되어 있다.

다만 논문에서 가장 중요한 최종 성능표는 아직 사람 검수 gold가 없기 때문에 확정하지 않았다. 따라서 현재 발표에서는 **"방법론과 자동 구축 결과는 준비되었고, 최종 claim은 human-gold 검수 후 확정한다"**는 점을 명확히 구분해서 설명하는 것이 가장 안전하다.
