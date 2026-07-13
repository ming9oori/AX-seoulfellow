# 교수님 보고용 핵심 요약: CAPE-KG 방법론, Prompt, CQ, Node/Edge 산출 방식

작성일: 2026-06-29  
대상 문서와의 관계: 이 파일은 `professor_report_slide_contents_current_20260628_ko.md`를 대체하지 않는 별도 핵심 요약본입니다.  
현재 상태: 자동 구축, 구조 검증, Neo4j/RDF/release bundle 갱신은 완료. Human-gold 기반 최종 성능 claim은 아직 보류.

## 1. 한 문장 요약

본 연구에서는 한국어 수주/제안 업무 문서에서 evidence-grounded procedural KG를 구축하고, 이를 NCS/PCF 표준 체계와 후보 연결한 뒤, LLM baseline/ablation/model-scaling 실험으로 방법론의 산출 구조를 진단했습니다. 최종 논문용 성능 claim은 사람 검수와 adjudication 후 계산해야 합니다.

## 2. 현재까지 실제로 완료된 것

| 구분 | 현재 상태 | 핵심 수치 |
|---|---|---:|
| OCR sentence 처리 | 완료 | 5,009 sentences |
| Layer 2 chunk 구성 | 완료 | 214 chunks |
| Layer 1 NCS KG | 완료 | 4,109 nodes |
| Layer 1 PCF KG | 완료 | 5,301 nodes |
| Layer 2 procedural KG | 완료 | 220 nodes / 947 edges |
| ReviewCheckpoint 반영 | 완료 | 41 nodes / 41 `HAS_REVIEW_CHECKPOINT` edges |
| NCS mapping 후보 | 완료 | 110 candidates |
| PCF mapping 후보 | 완료 | 110 candidates |
| CQ query pack | 완료 | 12/12 answerable |
| Neo4j export | 완료 | 11,028 nodes / 14,455 relationships |
| Pre-human handoff validation | 완료 | PASS, 87 PASS / 1 WARN |
| Human-gold annotation | 미완료 | 0 adjudicated chunks |
| 최종 F1 main result | 보류 | human-gold 필요 |

## 3. 전체 방법론 흐름

1. 입력 문서와 표준 데이터 준비
   - 업무 문서 OCR 결과를 sentence, page, chunk 단위로 정리했습니다.
   - NCS와 PCF 표준 데이터를 Layer 1 taxonomy KG로 변환했습니다.

2. CQ 기반 schema 설계
   - 수주/제안 업무를 설명하기 위해 12개 Competency Question을 정의했습니다.
   - 각 CQ를 KG predicate 또는 mapping task와 연결했습니다.

3. Layer 2 KG 자동 구축
   - LLM output을 그대로 final KG로 저장하지 않았습니다.
   - task seed, 용어 사전, procedure template, evidence anchor, schema validator를 이용해 rule/schema/evidence 기반으로 KG를 만들었습니다.

4. LLM 실험
   - LLM은 최종 KG를 무검증으로 만드는 도구가 아니라, 같은 120 evaluation chunks에서 baseline/proposed/ablation 조건이 어떤 후보 JSON을 생성하는지 비교하기 위해 사용했습니다.
   - Qwen3-8B, Qwen3-14B, Qwen3-32B-AWQ core diagnostic이 실행되었습니다.

5. Release와 검증
   - CQ query pack, structural evaluation, Neo4j export, RDF/SHACL, evidence projection, release bundle까지 갱신했습니다.
   - 단, 사람 검수 전이므로 성능 우수성 claim은 아직 하면 안 됩니다.

## 4. 실제 LLM 프롬프트 구조

프롬프트는 두 층으로 구성됩니다.

| 층 | 역할 |
|---|---|
| 조건별 prompt file | B0, B1, B2, B3, B4, B5, B6, P, ablation별 핵심 instruction |
| runtime prompt template | chunk metadata, sentence ids, chunk sentences, allowed node/edge schema, JSON shape, strict JSON contract를 결합 |

### 4.1 공통 runtime prompt 핵심

실제 LLM 호출 때 모든 조건에 공통으로 붙는 핵심 제약은 다음과 같습니다.

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

### 4.2 strict JSON contract

Qwen 계열 모델을 안정적으로 쓰기 위해 strict JSON 조건에서는 다음 contract를 추가했습니다.

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

### 4.3 proposed condition의 실제 핵심 instruction

`P_cape_kg_actual` 조건의 핵심 instruction은 다음 방향입니다.

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

JSON output shape는 다음과 같습니다.

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

### 4.4 조건별 prompt file 원문

| 조건 | 실제 prompt text |
|---|---|
| B0 plain LLM | `Extract subject-predicate-object triples from the chunk. Return JSON only.` |
| B1 predicate constrained | `Extract triples using only the allowed predicates. Return JSON only with evidence sentence ids.` |
| B2 current project baseline | `Extract Task Frames, then triples, then post-process into the Layer2 schema.` |
| B3 EDC-style baseline | `Extract, define, and canonicalize open-schema KG items, then emit CAPE-compatible nodes and edges for scoring.` |
| B4 taxonomy-RAG baseline | `Retrieve NCS/PCF/task taxonomy snippets, then extract schema-constrained triples with evidence.` |
| B5 procedural prompt baseline | `Extract actions, actors, gateways, guard conditions, artifact flows, and temporal/logical dependencies.` |
| B6 SAC-KG verifier-pruner baseline | `Use existing generator candidates, then apply schema/evidence verification and pruning in the style of SAC-KG. This is a deterministic approximation, not a full SAC-KG reproduction.` |
| P CAPE-KG | `Use CQ-linked schema retrieval, procedural frame extraction, evidence-span constrained relation extraction, span verification, ontology validation, procedural consistency checks, and active review scoring.` |
| P minus schema retrieval | `Run CAPE-KG without chunk-specific schema/taxonomy retrieval; keep CQ, evidence grounding, procedural schema, validation, and mapping output shape.` |

## 5. CQ는 어떻게 만들었는가

CQ는 LLM이 임의로 생성한 것이 아닙니다. 연구자가 수주/제안 업무 KG가 답해야 하는 질문을 먼저 정하고, 그 질문을 node type, edge predicate, evidence, mapping 요구사항으로 연결했습니다.

CQ 설계 기준은 다음과 같습니다.

1. 업무 구조를 물어보는가: task, step, order
2. 업무 입출력을 물어보는가: input artifact, output artifact
3. 책임 주체를 물어보는가: role
4. 절차적 판단을 물어보는가: decision gateway, guard condition
5. 산출물 흐름을 물어보는가: artifact flow
6. 리뷰와 품질관문을 물어보는가: review checkpoint
7. 원문 evidence를 추적할 수 있는가
8. 표준 직무/프로세스 체계와 연결할 수 있는가: NCS, PCF

| CQ | 질문 | 연결 predicate/source | 현재 support |
|---|---|---|---:|
| CQ1 | 수주·제안 업무는 어떤 주요 Task와 절차 단계로 구성되는가? | `HAS_STEP`, `PRECEDES` | 176 |
| CQ2 | 각 Task는 어떤 입력 자료를 사용하는가? | `USES_INPUT` | 201 |
| CQ3 | 각 Task는 어떤 산출물을 생성하는가? | `PRODUCES` | 220 |
| CQ4 | 각 Task는 누가 수행하거나 책임지는가? | `PERFORMED_BY` | 120 |
| CQ5 | 어떤 의사결정 지점이 존재하는가? | `HAS_DECISION_GATEWAY` | 54 |
| CQ6 | 의사결정에는 어떤 조건이나 판단 기준이 필요한가? | `HAS_GUARD_CONDITION` | 14 |
| CQ7 | 산출물은 다음 업무에서 어떻게 사용되는가? | `FEEDS_INTO`, `USED_AS_INPUT_FOR` | 18 |
| CQ8 | 제안서 리뷰는 어떤 단계에서 어떻게 수행되는가? | `HAS_REVIEW_CHECKPOINT` | 41 |
| CQ9 | 각 업무에서 지켜야 할 원칙은 무엇인가? | `HAS_PRINCIPLE` | 64 |
| CQ10 | 각 지식 항목은 원문 어느 chunk/page/span에 근거가 있는가? | `EVIDENCED_BY` | 947 |
| CQ11 | 특정 업무는 어떤 NCS 능력단위와 관련되는가? | NCS mapping candidates | 110 |
| CQ12 | 특정 업무는 PCF 프로세스 체계상 어디에 위치하는가? | PCF mapping candidates | 110 |

중요한 최신 변경점은 CQ8입니다. 이전에는 CQ8이 구조적 gap으로 남아 있었지만, 현재는 검토/리뷰/점검/승인/확인 신호가 있는 procedure step을 `ReviewCheckpoint`로 투영하고 `HAS_REVIEW_CHECKPOINT` edge를 생성하여 41개 support가 생겼습니다.

## 6. Node는 어떻게 산출했는가

최종 Layer 2 node는 LLM 후보를 그대로 채택한 것이 아니라, rule/schema/evidence 기반 생성 결과입니다.

| node type | count | 산출 방식 |
|---|---:|---|
| `DomainTask` | 22 | task seed의 label, alias, keyword를 OCR sentence evidence에 매칭 |
| `ProcedureStep` | 99 | task별 procedure template 또는 입력/산출물 기반 step 추론 |
| `ReviewCheckpoint` | 41 | `검토`, `리뷰`, `점검`, `승인`, `확인`, `review`, `checkpoint` 신호가 있는 step에서 투영 |
| `Artifact` | 14 | RFP, Capture Plan, 제안전략, 제안서, 발표자료 등 artifact 사전 매칭 |
| `Role` | 10 | 제안 PM, 영업, 리뷰팀 등 수행자/책임 주체 용어 매칭 |
| `DecisionGateway` | 4 | Bid/No-Bid, Bid Validation 등 의사결정 용어 매칭 |
| `GuardCondition` | 13 | 의사결정 주변 문장에서 조건/판단 기준 표현 추출 |
| `ArtifactFlow` | 9 | 산출물이 후속 task의 입력으로 흘러가는 규칙에서 생성 |
| `Principle` | 5 | 원칙/품질 기준 용어 매칭 |
| `Risk` | 3 | 위험/실패 가능성/불리함 표현 매칭 |

모든 final Layer 2 node는 evidence anchor를 갖습니다.

## 7. Edge는 어떻게 산출했는가

최종 Layer 2 edge 역시 schema validator를 통과한 edge만 남겼습니다.

| predicate | count | 산출 방식 |
|---|---:|---|
| `HAS_STEP` | 99 | DomainTask를 해당 ProcedureStep 목록에 연결 |
| `PRECEDES` | 77 | 같은 task 안의 step order를 기준으로 순서 연결 |
| `USES_INPUT` | 201 | task/step의 input slot을 Artifact node에 연결 |
| `PRODUCES` | 220 | task/step의 output slot을 Artifact node에 연결 |
| `PERFORMED_BY` | 120 | task/step을 Role node에 연결 |
| `HAS_DECISION_GATEWAY` | 54 | task/step에서 발견된 의사결정 node 연결 |
| `HAS_GUARD_CONDITION` | 14 | DecisionGateway를 GuardCondition에 연결 |
| `HAS_REVIEW_CHECKPOINT` | 41 | review-signaled ProcedureStep을 ReviewCheckpoint에 연결 |
| `HAS_PRINCIPLE` | 64 | task/step을 Principle에 연결 |
| `HAS_RISK` | 39 | task/step을 Risk에 연결 |
| `FEEDS_INTO` | 9 | Artifact가 다음 task로 흘러가는 방향 연결 |
| `USED_AS_INPUT_FOR` | 9 | Artifact가 후속 task 입력으로 쓰임을 연결 |

현재 final Layer 2 edge 947개는 모두 evidence anchor와 source triple id를 갖고, dangling edge는 0개입니다.

## 8. LLM 실험은 무엇을 했는가

LLM 실험의 목적은 final KG 자체를 만드는 것이 아니라, proposed prompt와 baseline/ablation이 같은 120 evaluation chunks에서 어떤 후보 JSON을 생성하는지 비교하는 것입니다.

| 모델/조건 | 실행 상태 | 해석 |
|---|---|---|
| Qwen3-8B | 120 chunks, baseline/proposed/ablation 실행 | 주된 local diagnostic |
| Qwen3-14B | core 4조건 실행 | 더 큰 모델 diagnostic |
| Qwen3-32B-AWQ | core 4조건, 480 rows 완료 | 현재 실행된 가장 큰 local model diagnostic |
| B0-B6 baselines | 실행 | plain triple, predicate-constrained, current baseline, EDC-style, taxonomy-RAG, procedural, SAC-KG-style |
| P ablations | 실행 | CQ, evidence, procedural schema, validator, standard bridge, schema retrieval 제거 조건 |

Qwen3-32B-AWQ는 silver/proxy 기준에서 proposed predicate F1과 exact edge F1이 8B보다 높게 나왔지만, evidence F1은 8B보다 낮았습니다. 따라서 “큰 모델이면 항상 좋아진다”라고 말하면 안 됩니다.

## 9. 현재 main table로 말할 수 있는 것과 없는 것

| 항목 | 현재 말할 수 있는가 | 이유 |
|---|---|---|
| KG 구축 완료 | 가능 | Layer 1, Layer 2, mapping candidates, evidence projection, Neo4j export 완료 |
| CQ 구조적 answerability | 가능 | 12/12 CQ가 현재 KG query support를 가짐 |
| Neo4j 시각화/탐색 가능 | 가능 | CSV validation PASS, flat import package 있음 |
| LLM 조건별 산출 coverage | 가능 | 120 chunks 기준 condition별 output 존재 |
| Human-gold F1 최종 성능 | 불가 | adjudicated human-gold chunks가 0개 |
| 방법론이 baseline보다 최종적으로 우수하다는 claim | 불가 | 사람 검수 후 precision/recall/F1 계산 필요 |
| NCS/PCF mapping 품질 claim | 불가 | expert review pending |
| Active-review 효율 claim | 불가 | 사람 correction/time evidence pending |

## 10. 교수님께 보고할 때의 핵심 메시지

1. “현재까지는 KG 구축과 자동 구조 검증은 완료했습니다.”
2. “최신 KG는 Layer 2 기준 220 nodes, 947 edges이고, 모든 edge가 evidence anchor를 갖습니다.”
3. “이전 구조적 공백이던 ReviewCheckpoint/CQ8도 현재는 41개 checkpoint edge로 지원됩니다.”
4. “LLM은 final KG를 무비판적으로 생성한 것이 아니라, baseline/proposed/ablation 비교용 후보 생성기로 사용했습니다.”
5. “논문용 최종 성능표는 아직 나오지 않았습니다. 사람 검수와 adjudication 후에만 Human-gold F1 main table을 만들 수 있습니다.”

## 11. 바로 이어서 해야 할 일

| 우선순위 | 해야 할 일 | 산출물 |
|---|---|---|
| 1 | Annotator A/B가 priority 100 chunks 검수 | reviewed JSONL |
| 2 | IAA 계산 | agreement report |
| 3 | adjudicator가 최종 gold 확정 | adjudication JSONL |
| 4 | human-gold scoring 재실행 | final precision/recall/F1 table |
| 5 | NCS/PCF mapping expert review | mapping downstream metrics |
| 6 | active-review human effort 기록 | review-effort efficiency metrics |

## 12. 핵심 파일 위치

| 역할 | 파일 |
|---|---|
| 최종 Layer 2 nodes | `outputs/07_layer2_graph/layer2_nodes.jsonl` |
| 최종 Layer 2 edges | `outputs/07_layer2_graph/layer2_edges.jsonl` |
| CQ query pack | `experiments/cape_kg_eacl_20260627/06_release/cq_query_pack.md` |
| Prompt/node/edge traceability | `experiments/cape_kg_eacl_20260627/06_release/prompt_node_edge_traceability.md` |
| Structural evaluation | `experiments/cape_kg_eacl_20260627/04_evaluation/structural_evaluation_report.md` |
| Claimable main table | `experiments/cape_kg_eacl_20260627/06_release/claimable_main_table.md` |
| Neo4j flat import | `outputs/11_neo4j_import_flat/` |
| Pre-human validation | `experiments/cape_kg_eacl_20260627/06_release/pre_human_handoff_validation.md` |
| 최신 release bundle index | `experiments/cape_kg_eacl_20260627/06_release/latest_release_bundle_index.md` |

