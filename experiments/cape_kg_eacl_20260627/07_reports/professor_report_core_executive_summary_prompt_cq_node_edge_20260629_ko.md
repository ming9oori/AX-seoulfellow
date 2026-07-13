# 교수님 보고용 핵심 요약본: Prompt, CQ, Node/Edge 산출 방식

Generated: 2026-06-29  
기준 문서: `experiments/cape_kg_eacl_20260627/07_reports/professor_report_slide_contents_current_20260628_ko.md`  
별도 요약 목적: 상세 슬라이드 원고와 분리하여, 교수님께 먼저 설명해야 할 핵심 방법론과 현재 결과만 압축 정리

이 문서는 PPT 원고가 아니라 **보고 전 핵심 브리핑용 문서**입니다. 특히 다음 질문에 바로 답하도록 구성했습니다.

1. 어떤 방법론으로 KG를 만들었는가?
2. 어떤 프롬프트를 사용했고, 무엇을 산출했는가?
3. CQ는 어떻게 만들었고, 예시는 무엇인가?
4. Node와 Edge는 각각 어떤 방식으로 생성되었는가?
5. 현재까지 무엇이 완료되었고, 무엇은 아직 claim하면 안 되는가?

---

## 1. 결론부터

본 연구는 한국어 수주/제안 업무 문서에서 **CAPE-KG 방법론**을 적용해, 원문 evidence에 근거한 절차형 업무 Knowledge Graph를 구축하고 이를 NCS/PCF 표준 taxonomy와 연결한 실험입니다.

가장 중요한 설명은 다음입니다.

> 최종 Layer 2 KG는 LLM raw output을 그대로 저장한 결과가 아닙니다. OCR sentence evidence, task seed, procedural schema, node/edge 생성 규칙, validator를 거쳐 구축한 evidence-grounded procedural KG입니다. LLM은 baseline/proposed/ablation 조건별 prediction을 비교하기 위해 사용했습니다.

따라서 현재 발표에서 안전하게 말할 수 있는 것과 아직 보류해야 하는 것은 분리해야 합니다.

| 구분 | 현재 상태 | 보고 표현 |
| --- | --- | --- |
| KG 구축 | 완료 | Layer 1 NCS/PCF KG와 Layer 2 업무 KG 구축 완료 |
| Evidence grounding | 완료 | 최종 Layer 2 node/edge가 evidence anchor와 연결됨 |
| LLM 실험 | 완료 | 14개 조건, 각 120 evaluation chunks 기준 실행 |
| Model scaling | 완료 | Qwen3-8B, Qwen3-14B, Qwen3-32B-AWQ 진단 완료 |
| Human-gold 성능 claim | 아직 불가 | annotation, IAA, adjudication 이후 확정 |
| Mapping 성능 claim | 아직 불가 | NCS/PCF expert review 이후 확정 |

---

## 2. 현재까지의 핵심 산출물

| 항목 | 값 |
| --- | ---: |
| OCR evidence anchors | 5,009 |
| Layer 1 NCS nodes | 4,109 |
| Layer 1 PCF nodes | 5,301 |
| Layer 2 final nodes | 179 |
| Layer 2 final edges | 906 |
| Canonical DomainTask | 22 |
| ProcedureStep | 99 |
| NCS mapping candidates | 110 |
| PCF mapping candidates | 110 |
| Evaluation chunks for LLM experiments | 120 |
| LLM experiment conditions | 14 |
| Human-gold adjudicated chunks | 0 |
| Human-gold items | 0 |

핵심 파일은 다음입니다.

| 목적 | 파일 |
| --- | --- |
| 최종 Layer 2 nodes | `outputs/07_layer2_graph/layer2_nodes.jsonl` |
| 최종 Layer 2 edges | `outputs/07_layer2_graph/layer2_edges.jsonl` |
| NCS mapping 후보 | `outputs/08_mapping/l2_ncs_mapping_candidates.jsonl` |
| PCF mapping 후보 | `outputs/08_mapping/l2_pcf_mapping_candidates.jsonl` |
| KG viewer | `outputs/09_visualization/kg_viewer.html` |
| Prompt-node-edge traceability | `experiments/cape_kg_eacl_20260627/06_release/prompt_node_edge_traceability.md` |
| CQ query pack | `experiments/cape_kg_eacl_20260627/06_release/cq_query_pack.md` |
| Claim 가능성 table | `experiments/cape_kg_eacl_20260627/06_release/claimable_main_table.md` |

---

## 3. 방법론 핵심: CAPE-KG

CAPE-KG는 LLM 단독 추출 방식이 아니라, 아래 요소를 결합한 KG construction pipeline입니다.

| 구성 요소 | 역할 |
| --- | --- |
| CQ | KG가 답해야 할 업무 질문을 먼저 정의 |
| Procedural schema | task, step, artifact, role, decision, guard, risk를 구조화 |
| Evidence anchor | 모든 node/edge/mapping을 원문 sentence id에 연결 |
| Validator | 허용 node type, edge predicate, source/target 존재, evidence 존재를 검사 |
| Standard bridge | Layer 2 업무 KG를 NCS/PCF 표준 taxonomy와 연결 |
| Human-review handoff | 최종 논문 claim을 위해 사람이 검수할 batch와 gate를 준비 |

전체 흐름은 다음과 같습니다.

1. OCR workbook을 sentence 단위로 정제
2. sentence마다 evidence anchor ID 생성
3. NCS/PCF taxonomy를 Layer 1 KG로 구축
4. 업무 문서를 chunk로 나누고 evaluation chunks 구성
5. CQ와 procedural schema 설계
6. task seed, alias, keyword, evidence sentence로 task frame 생성
7. task frame에서 node 후보와 triple 후보 생성
8. predicate별 규칙으로 edge 생성
9. source/target/evidence/schema validation 수행
10. 통과한 node/edge만 최종 Layer 2 KG로 저장
11. NCS/PCF mapping 후보 생성
12. LLM baseline/proposed/ablation/model-scaling 실험 실행
13. human-gold, expert review, active-review handoff 준비

---

## 4. 실제 프롬프트로 무엇을 산출했는가

프롬프트 파일 위치:

`experiments/cape_kg_eacl_20260627/02_schema/prompts/`

조건별 실제 prompt text와 산출 key는 다음과 같습니다.

| 조건 | 실제 prompt text | 산출 key |
| --- | --- | --- |
| B0_plain_llm | `Extract subject-predicate-object triples from the chunk. Return JSON only.` | `triples` |
| B1_predicate_constrained | `Extract triples using only the allowed predicates. Return JSON only with evidence sentence ids.` | `edges` |
| B2_current_project | `Extract Task Frames, then triples, then post-process into the Layer2 schema.` | `nodes`, `edges` |
| B3_edc_style | `Extract, define, and canonicalize open-schema KG items, then emit CAPE-compatible nodes and edges for scoring.` | `nodes`, `edges` |
| B4_taxonomy_rag | `Retrieve NCS/PCF/task taxonomy snippets, then extract schema-constrained triples with evidence.` | `nodes`, `edges`, `mappings` |
| B5_procedural_prompt | `Extract actions, actors, gateways, guard conditions, artifact flows, and temporal/logical dependencies.` | `nodes`, `edges` |
| B6_sac_kg_verifier_pruner | `Use existing generator candidates, then apply schema/evidence verification and pruning in the style of SAC-KG. This is a deterministic approximation, not a full SAC-KG reproduction.` | `nodes`, `edges`, `mappings` |
| P_cape_kg_actual | `Use CQ-linked schema retrieval, procedural frame extraction, evidence-span constrained relation extraction, span verification, ontology validation, procedural consistency checks, and active review scoring.` | `nodes`, `edges`, `mappings` |
| P_minus_Schema_retrieval | `Run CAPE-KG without chunk-specific schema/taxonomy retrieval; keep CQ, evidence grounding, procedural schema, validation, and mapping output shape.` | `nodes`, `edges`, `mappings` |

실제 LLM 실행 시에는 위 조건별 prompt text에 chunk 정보와 JSON contract가 결합되었습니다.

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

Strict JSON 실행에서는 다음 제약을 추가했습니다.

```text
System:
You are a JSON-only evidence-grounded information extraction function.

Strict JSON contract:
- Return exactly one JSON object and nothing else.
- The first non-whitespace character must be `{` and the last non-whitespace character must be `}`.
- Do not include markdown, code fences, comments, XML tags, <think> blocks, prose, or explanations.
- For Qwen/Qwen-style chat models, obey /no_think; do not emit hidden or visible reasoning.

User:
/no_think
...
/no_think
Return exactly one compact JSON object now.
```

제안 방법론인 `P_cape_kg_actual`의 핵심 runtime prompt 구조는 다음과 같습니다.

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

핵심은 LLM이 자유롭게 그래프를 만들지 못하게 하고, **CQ, evidence, schema, validator, NCS/PCF bridge**를 모두 조건으로 걸었다는 점입니다.

---

## 5. CQ는 어떻게 생성했는가

CQ는 LLM이 자동 생성한 것이 아니라, 연구자가 먼저 정의한 **KG 요구사항**입니다. 즉, "이 KG가 어떤 업무 질문에 답해야 하는가"를 정하고, 그 질문을 node type과 edge predicate에 연결했습니다.

생성 방식은 다음과 같습니다.

| 단계 | 내용 |
| --- | --- |
| 1 | 수주/제안 업무 문서에서 답해야 할 질문 범위를 정의 |
| 2 | 질문을 업무 구성, 절차 순서, 입력, 산출물, 역할, 의사결정, 조건, 위험, evidence, 표준 연결로 분해 |
| 3 | 각 질문을 `DomainTask`, `ProcedureStep`, `Artifact`, `Role`, `DecisionGateway`, `GuardCondition` 등 node type과 연결 |
| 4 | 각 질문을 `HAS_STEP`, `USES_INPUT`, `PRODUCES`, `PERFORMED_BY`, `HAS_DECISION_GATEWAY` 등 predicate와 연결 |
| 5 | 같은 CQ를 schema 설계, LLM prompt, ablation, structural evaluation에 재사용 |

CQ source files:

| 용도 | 파일 |
| --- | --- |
| EACL 실험용 CQ | `experiments/cape_kg_eacl_20260627/02_schema/competency_questions.json` |
| 내부 KG build용 CQ | `outputs/03_schema/competency_questions.json` |
| CQ query pack | `experiments/cape_kg_eacl_20260627/06_release/cq_query_pack.md` |

현재 CQ는 12개이며, 11개는 현재 KG로 구조적으로 answerable합니다. CQ8은 `HAS_REVIEW_CHECKPOINT` edge가 최종 KG에 없어서 structural gap으로 남아 있고, review checkpoint 후보를 사람 검수 대상으로 분리했습니다.

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

---

## 6. Node는 어떻게 산출했는가

최종 node는 `outputs/07_layer2_graph/layer2_nodes.jsonl`에 저장되어 있습니다. 이 node들은 LLM raw output이 아니라, OCR evidence와 schema 규칙을 통과한 자동 구축 결과입니다.

Node 생성 절차는 다음과 같습니다.

1. OCR 문장을 evidence anchor로 정리
2. `TASK_SEEDS`의 업무 seed label, alias, keyword로 관련 sentence 검색
3. 발견된 업무 단위를 `DomainTask` 후보로 정규화
4. task별 procedure template 또는 입력/산출물 기반 추론으로 `ProcedureStep` 생성
5. 입력물/산출물 용어를 찾아 `Artifact` 생성
6. 수행자/책임 주체를 찾아 `Role` 생성
7. 의사결정 관련 표현을 찾아 `DecisionGateway` 생성
8. 조건/가능성/경쟁/자원 표현을 찾아 `GuardCondition` 생성
9. 원칙/품질 기준은 `Principle`, 위험 표현은 `Risk`로 생성
10. 산출물이 다음 task 입력으로 사용되는 규칙에서 `ArtifactFlow` 생성
11. `node_id` 기준으로 중복 제거하고 evidence와 review status 부여

현재 node type별 개수는 다음입니다.

| Node type | 생성 방식 | 개수 |
| --- | --- | ---: |
| `ProcedureStep` | task별 procedure template 또는 입력/산출물 기반 step 추론 | 99 |
| `DomainTask` | task seed label/alias/keyword로 OCR sentence evidence 검색 | 22 |
| `Artifact` | task evidence 안의 입력물/산출물 용어 매칭 | 14 |
| `GuardCondition` | 의사결정 evidence에서 조건/가능성/경쟁/자원 표현 추출 | 13 |
| `Role` | 수행자/책임 주체 용어 매칭 | 10 |
| `ArtifactFlow` | 특정 산출물이 다음 task 입력으로 쓰이는 규칙 | 9 |
| `Principle` | 원칙/품질 기준 용어 매칭 | 5 |
| `DecisionGateway` | 의사결정 관련 용어 매칭 | 4 |
| `Risk` | 위험/불리함/실패 가능성 용어 매칭 | 3 |

요약하면, node는 `기회분석`, `Capture Plan`, `제안전략`, `제안 PM`, `Bid/No-Bid 판단 조건`처럼 **업무 개념 자체**입니다.

---

## 7. Edge는 어떻게 산출했는가

최종 edge는 `outputs/07_layer2_graph/layer2_edges.jsonl`에 저장되어 있습니다. Edge는 node 사이의 업무 관계를 predicate별 규칙으로 만든 뒤, source/target/evidence 검증을 통과한 것만 저장했습니다.

Edge 생성 절차는 다음과 같습니다.

1. task frame의 `inputs`, `outputs`, `roles`, `principles`, `risks` slot을 predicate로 변환
2. DomainTask와 ProcedureStep은 `HAS_STEP`으로 연결
3. 같은 task 안의 step 순서는 `PRECEDES`로 연결
4. task/step과 artifact는 `USES_INPUT`, `PRODUCES`로 연결
5. task/step과 role은 `PERFORMED_BY`로 연결
6. 의사결정과 조건은 `HAS_DECISION_GATEWAY`, `HAS_GUARD_CONDITION`으로 연결
7. 산출물이 다음 task 입력으로 쓰이면 `FEEDS_INTO`, `USED_AS_INPUT_FOR`로 연결
8. 모든 edge에 `source_triple_ids`와 evidence anchor 부여
9. allowed predicate, source node 존재, target node 존재, evidence 존재 여부 검증
10. 검증 통과 edge만 final graph에 저장

현재 predicate별 edge 수는 다음입니다.

| Predicate | 생성 방식 | 개수 |
| --- | --- | ---: |
| `PRODUCES` | task/step의 outputs slot을 Artifact node로 연결 | 220 |
| `USES_INPUT` | task/step의 inputs slot을 Artifact 또는 Concept node로 연결 | 201 |
| `PERFORMED_BY` | task/step의 roles slot을 Role node로 연결 | 120 |
| `HAS_STEP` | DomainTask를 해당 ProcedureStep 목록에 연결 | 99 |
| `PRECEDES` | 같은 task 안에서 step order 기준으로 순서 연결 | 77 |
| `HAS_PRINCIPLE` | task/step의 principles slot을 Principle node로 연결 | 64 |
| `HAS_DECISION_GATEWAY` | task/step에서 발견된 의사결정 node 연결 | 54 |
| `HAS_RISK` | task/step의 risks slot을 Risk node로 연결 | 39 |
| `HAS_GUARD_CONDITION` | DecisionGateway에서 추출된 조건 node 연결 | 14 |
| `FEEDS_INTO` | Artifact가 다음 task로 흘러가는 규칙 연결 | 9 |
| `USED_AS_INPUT_FOR` | Artifact가 다음 task 입력으로 사용되는 규칙 연결 | 9 |

검증 결과:

| 항목 | 결과 |
| --- | ---: |
| Final Layer 2 edges | 906 |
| Evidence가 있는 edges | 906 / 906 |
| `source_triple_ids`가 있는 edges | 906 / 906 |
| Dangling edges | 0 |
| Ontology conformance | 1.0000 |

요약하면, edge는 `기회분석 USES_INPUT Capture Plan`, `제안서 작성 PRODUCES 제안서`, `검토 단계 PRECEDES 승인 단계`처럼 **업무 개념 사이의 관계**입니다.

---

## 8. LLM 실험은 무엇을 했는가

LLM은 최종 KG를 그대로 생성하는 단일 도구가 아니라, 조건별 prediction을 비교하기 위한 실험 모듈로 사용했습니다.

| 조건 범주 | 조건 수 | 설명 |
| --- | ---: | --- |
| Baseline | 7 | plain triple, predicate-constrained, task-frame, EDC-style, taxonomy-RAG, procedural prompt, SAC-KG-style verifier/pruner |
| Proposed | 1 | `P_cape_kg_actual`: CQ + evidence + procedural schema + validator + NCS/PCF bridge |
| Ablation | 6 | CQ, evidence, procedural schema, validator, standard bridge, schema retrieval 제거 조건 |
| 전체 | 14 | 각 조건 120 evaluation chunks 기준 실행 |

Qwen3 model scaling도 진행했습니다.

| 모델 | 목적 | 상태 |
| --- | --- | --- |
| Qwen3-8B | 기본 baseline/proposed/ablation 전체 조건 | 완료 |
| Qwen3-14B | core condition scaling | 완료 |
| Qwen3-32B-AWQ | 현실적으로 실행 가능한 대형 모델 scaling | 480 valid rows 완료 |

주의할 점:

- 현재 LLM 결과는 human-gold 전이므로 **silver/proxy diagnostic**입니다.
- 산출량이 많다고 성능이 좋다는 뜻은 아닙니다.
- 최종 precision/recall/F1 main table은 adjudicated human-gold 이후 다시 계산해야 합니다.

---

## 9. 교수님께 설명할 핵심 문장

발표에서 가장 안전한 핵심 문장은 다음입니다.

1. "이 연구는 LLM에게 단순히 triple을 뽑게 한 것이 아니라, CQ와 schema로 KG가 답해야 할 질문을 먼저 정의했습니다."
2. "각 node와 edge는 원문 OCR sentence evidence anchor에 연결되도록 만들었습니다."
3. "최종 KG는 LLM raw output이 아니라 task seed, procedure template, evidence, schema validator를 거친 graph입니다."
4. "LLM은 baseline/proposed/ablation 조건의 prediction generator로 사용했고, 제안 방법론은 CQ, evidence, procedural schema, validator, standard bridge를 결합한 조건입니다."
5. "현재 KG 구축과 실험 실행은 완료되었지만, 논문 성능 claim은 human-gold와 expert review가 들어와야 확정됩니다."

---

## 10. 아직 남은 작업

최종 논문 claim을 위해 남은 작업은 사람 검수와 expert review입니다.

| 남은 작업 | 필요한 이유 |
| --- | --- |
| Human-gold annotation | 최종 node/edge/evidence precision, recall, F1 계산 |
| IAA 계산 | annotator 간 일치도 제시 |
| Adjudication | 최종 gold label 확정 |
| Proposed human-gold scoring | 제안 방법론의 최종 main table 생성 |
| Mapping expert review | NCS/PCF mapping 성능 검증 |
| NCS-PCF crosswalk expert review | 표준 간 bridge utility 검증 |
| Active-review effort evidence | active review 효율 claim 검증 |

현재 결론:

> CAPE-KG 방법론을 적용해 한국어 수주/제안 업무 문서 기반 Layer 2 procedural KG와 NCS/PCF standard bridge 후보를 구축했고, 14개 LLM 조건과 Qwen3 model scaling 실험까지 재현 가능한 형태로 준비했다. 단, 최종 성능 우수성 claim은 사람 검수 이후로 보류한다.
