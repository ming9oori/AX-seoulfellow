# 교수님 보고용 핵심 요약본

Generated: 2026-06-28  
Experiment directory: `experiments/cape_kg_eacl_20260627`  
Related detailed slide document: `experiments/cape_kg_eacl_20260627/07_reports/professor_report_slide_contents_current_20260628_ko.md`

이 문서는 기존 긴 슬라이드 원고와 별개로, 교수님께 핵심만 설명하기 위한 별도 요약본입니다. 특히 다음 네 가지 질문에 답하도록 정리했습니다.

1. 어떤 연구 방법론을 적용했는가?
2. 어떤 CQ와 프롬프트로 무엇을 산출했는가?
3. node와 edge는 각각 어떤 방식으로 생성했는가?
4. 현재 결과 중 무엇을 주장할 수 있고, 무엇은 아직 보류해야 하는가?

---

## 1. 한 문장 요약

본 연구는 한국어 수주/제안 업무 문서에서 업무 절차, 입력/산출물, 역할, 의사결정, 위험요소를 evidence-grounded procedural KG로 구축하고, 이를 NCS/PCF 표준 taxonomy와 연결한 뒤, LLM baseline/ablation/model-scaling과 human-review handoff까지 실행한 연구입니다.

가장 중요한 구분은 다음입니다.

| 구분 | 현재 상태 | 발표 시 표현 |
| --- | --- | --- |
| KG 구축 | 완료 | Layer 1 표준 KG와 Layer 2 업무 KG 구축 완료 |
| LLM 실험 | 실행 완료 | 여러 프롬프트 조건과 모델 조건의 silver/proxy diagnostic 완료 |
| 최종 성능 claim | 보류 | human-gold annotation, IAA, adjudication 전이므로 최종 precision/recall 주장은 아직 불가 |

---

## 2. 연구 문제와 방법론

### 연구 문제

한국어 장문 업무 문서에서 단순 키워드나 entity list가 아니라, 다음과 같은 절차형 업무 지식을 KG로 구조화하는 것이 목표입니다.

| 추출 대상 | KG 표현 |
| --- | --- |
| 업무 단위 | `DomainTask` node |
| 업무 수행 단계 | `ProcedureStep` node |
| 입력/산출 문서 | `Artifact` node |
| 수행 주체 | `Role` node |
| 의사결정 지점 | `DecisionGateway` node |
| 의사결정 조건 | `GuardCondition` node |
| 원칙/위험 | `Principle`, `Risk` node |
| 업무 간 순서와 흐름 | `HAS_STEP`, `PRECEDES`, `USES_INPUT`, `PRODUCES`, `FEEDS_INTO` edge |

### 적용한 방법론

본 연구의 방법론은 LLM에게 "그래프를 만들어 달라"고 맡기는 방식이 아니라, 다음 요소를 결합한 통제된 KG construction 방식입니다.

| 구성 요소 | 역할 |
| --- | --- |
| Competency Questions | KG가 답해야 할 질문을 먼저 정의 |
| Procedural schema | 업무 절차를 표현할 node type과 edge predicate 정의 |
| Evidence grounding | 모든 지식 항목을 OCR sentence evidence anchor에 연결 |
| Validator | 허용되지 않은 node type, predicate, evidence id를 검증 |
| Standard bridge | Layer 2 업무 KG를 NCS/PCF taxonomy 후보와 연결 |
| Human-review handoff | 최종 claim을 위해 사람이 검수할 파일과 workflow 생성 |

---

## 3. 전체 파이프라인

| 단계 | 수행 내용 | 주요 산출물 |
| --- | --- | --- |
| 1 | OCR 문장 정제 | `outputs/02_ocr/ocr_sentences_clean.jsonl` |
| 2 | Evidence anchor 생성 | `outputs/06_triples/evidence_anchors.jsonl` |
| 3 | Layer 1 NCS/PCF KG 구축 | `outputs/01_layer1/` |
| 4 | Layer 2 chunk 구성 | `outputs/02_ocr/layer2_chunks.jsonl` |
| 5 | CQ 및 schema 정의 | `experiments/cape_kg_eacl_20260627/02_schema/` |
| 6 | Task frame 및 procedure 구조 생성 | `outputs/04_task_frames/`, `outputs/05_procedure/` |
| 7 | Triple 생성 및 검증 | `outputs/06_triples/layer2_triples_schema_valid.jsonl` |
| 8 | 최종 Layer 2 KG 조립 | `outputs/07_layer2_graph/layer2_nodes.jsonl`, `layer2_edges.jsonl` |
| 9 | NCS/PCF mapping 후보 생성 | `outputs/08_mapping/` |
| 10 | LLM baseline/proposed/ablation 실행 | `experiments/cape_kg_eacl_20260627/48_*`, `49_*`, `50_*` |
| 11 | 구조 진단 및 claim gate 실행 | `experiments/cape_kg_eacl_20260627/04_evaluation/`, `06_release/` |

---

## 4. 현재 구축 결과

### 데이터와 evidence

| 항목 | 값 |
| --- | ---: |
| OCR clean sentences | 5,009 |
| Evidence anchors | 5,009 |
| Layer 2 chunks | 214 |
| Evaluation chunks | 120 |

### Layer 1 표준 KG

| 구성 | Nodes | Edges |
| --- | ---: | ---: |
| NCS taxonomy | 4,109 | 4,085 |
| PCF taxonomy | 5,301 | 2,004 |
| PCF metric edges | - | 3,284 |

### Layer 2 업무 KG

| 항목 | 값 |
| --- | ---: |
| Layer 2 nodes | 179 |
| Layer 2 edges | 906 |
| Schema-valid triples | 906 |
| NCS mapping candidates | 110 |
| PCF mapping candidates | 110 |
| Evidence-missing edges | 0 |
| Missing `source_triple_ids` edges | 0 |

해석: 현재 데이터에 대해 KG 구축 자체는 완료되었습니다. 다만 이 KG가 gold standard 대비 얼마나 정확한지는 사람 검수 이후에 최종 주장할 수 있습니다.

---

## 5. CQ는 어떻게 만들었는가

CQ는 LLM이 자동 생성한 것이 아니라, 이 KG가 답해야 하는 업무 질문을 연구자가 먼저 설계한 것입니다. 즉, CQ는 schema, prompt, evaluation을 연결하는 설계 기준입니다.

CQ 생성 방식은 다음과 같습니다.

1. 수주/제안 업무 문서에서 답해야 할 질문 범주를 정의했습니다.
2. 질문 범주를 업무 절차, 입력/산출물, 역할, 의사결정, 위험, evidence, 표준 taxonomy 연결로 나눴습니다.
3. 각 질문을 node type과 edge predicate에 연결했습니다.
4. 같은 CQ를 schema 설계, LLM prompt, structural evaluation에서 재사용했습니다.

### 실제 CQ 목록

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

관련 파일:

| 역할 | 파일 |
| --- | --- |
| EACL 실험용 CQ | `experiments/cape_kg_eacl_20260627/02_schema/competency_questions.json` |
| schema 파일 | `experiments/cape_kg_eacl_20260627/02_schema/cape_schema.json` |
| LLM prompt 구성 코드 | `scripts/run_cape_llm_condition_baselines.py` |

---

## 6. 실제 프롬프트로 무엇을 산출했는가

프롬프트 파일은 `experiments/cape_kg_eacl_20260627/02_schema/prompts/`에 저장되어 있습니다. 저장된 파일은 조건별 핵심 instruction이고, 실제 LLM 호출 때는 여기에 chunk 문장, sentence id, allowed node types, allowed edge predicates, JSON shape, strict JSON contract가 붙습니다.

### 프롬프트 파일 원문 요약

| 조건 | 실제 저장된 프롬프트 원문 | 산출물 |
| --- | --- | --- |
| `B0_plain_llm` | `Extract subject-predicate-object triples from the chunk. Return JSON only.` | 자유 `triples` |
| `B1_predicate_constrained` | `Extract triples using only the allowed predicates. Return JSON only with evidence sentence ids.` | predicate 제한 `edges` |
| `B2_current_project` | `Extract Task Frames, then triples, then post-process into the Layer2 schema.` | `nodes`, `edges` |
| `B3_edc_style` | `Extract, define, and canonicalize open-schema KG items, then emit CAPE-compatible nodes and edges for scoring.` | `nodes`, `edges` |
| `B4_taxonomy_rag` | `Retrieve NCS/PCF/task taxonomy snippets, then extract schema-constrained triples with evidence.` | `nodes`, `edges`, `mappings` |
| `B5_procedural_prompt` | `Extract actions, actors, gateways, guard conditions, artifact flows, and temporal/logical dependencies.` | `nodes`, `edges` |
| `B6_sac_kg_verifier_pruner` | `Use existing generator candidates, then apply schema/evidence verification and pruning in the style of SAC-KG. This is a deterministic approximation, not a full SAC-KG reproduction.` | verified/pruned `nodes`, `edges` |
| `P_cape_kg_actual` | `Use CQ-linked schema retrieval, procedural frame extraction, evidence-span constrained relation extraction, span verification, ontology validation, procedural consistency checks, and active review scoring.` | `nodes`, `edges`, `mappings` |
| `P_minus_Schema_retrieval` | `Run CAPE-KG without chunk-specific schema/taxonomy retrieval; keep CQ, evidence grounding, procedural schema, validation, and mapping output shape.` | ablation `nodes`, `edges`, `mappings` |

### 모든 LLM 조건에 공통으로 붙은 핵심 runtime prompt

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

### `P_cape_kg_actual`의 핵심 runtime instruction

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

### Strict JSON contract

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

핵심 해석: 같은 LLM을 쓰더라도 프롬프트 조건마다 요구 산출물이 다릅니다. `B0`는 자유 triple을 만들고, `B1`은 predicate만 제한하며, `P_cape_kg_actual`은 CQ, evidence, procedural schema, validator, NCS/PCF bridge를 모두 포함해 `nodes`, `edges`, `mappings`를 산출하게 했습니다.

---

## 7. Node는 어떻게 생성했는가

최종 KG의 node는 LLM 출력물을 그대로 넣은 것이 아닙니다. 최종 `outputs/07_layer2_graph/layer2_nodes.jsonl`은 OCR evidence, task seed, 용어 사전, 절차 template, schema rule을 조합해 만든 자동 구축 결과입니다.

### Node 생성 흐름

1. OCR sentence를 `EA-JS-*` evidence anchor로 변환했습니다.
2. 업무 seed와 alias/keyword로 관련 sentence를 검색했습니다.
3. sentence 안에서 artifact, role, decision, principle, risk 후보를 사전과 규칙으로 추출했습니다.
4. 업무 단위는 `DomainTask` node로 만들었습니다.
5. 업무별 절차 단계는 `ProcedureStep` node로 만들었습니다.
6. 산출물이 다음 업무의 입력으로 흐르는 경우 `ArtifactFlow` node를 만들었습니다.
7. 모든 node는 `node_id`, `type`, `label`, `evidence_anchor_ids`, `review_status`를 갖도록 정규화했습니다.

### 현재 node type별 개수

| Node type | 생성 방식 | 개수 |
| --- | --- | ---: |
| `ProcedureStep` | task별 절차 template 또는 입력/산출물 기반 step 추론 | 99 |
| `DomainTask` | 업무 seed와 evidence sentence 검색 | 22 |
| `Artifact` | 입력/산출물 용어 매칭 | 14 |
| `GuardCondition` | 의사결정 evidence에서 조건 표현 추출 | 13 |
| `Role` | 수행자/책임 주체 용어 매칭 | 10 |
| `ArtifactFlow` | 산출물이 다음 task 입력으로 쓰이는 흐름 규칙 | 9 |
| `Principle` | 원칙/품질 기준 용어 매칭 | 5 |
| `DecisionGateway` | 의사결정 관련 표현 매칭 | 4 |
| `Risk` | 위험/불리함/실패 가능성 표현 매칭 | 3 |

핵심 해석: node는 "LLM이 임의로 만든 entity"가 아니라, 업무 schema와 evidence anchor를 만족하도록 정규화된 KG 구성 요소입니다.

---

## 8. Edge는 어떻게 생성했는가

최종 KG의 edge는 node 사이의 업무 관계를 predicate별 규칙으로 생성하고, source node, target node, evidence가 모두 존재하는 경우에만 남겼습니다.

### Edge 생성 흐름

1. task frame의 `inputs`, `outputs`, `roles`, `principles`, `risks` slot을 predicate로 변환했습니다.
2. 의사결정 node와 조건 node는 `HAS_DECISION_GATEWAY`, `HAS_GUARD_CONDITION`으로 연결했습니다.
3. 업무와 step은 `HAS_STEP`, step 간 순서는 `PRECEDES`로 연결했습니다.
4. artifact flow는 `FEEDS_INTO`, `USED_AS_INPUT_FOR`로 연결했습니다.
5. 모든 edge는 triple record로 변환되어 `source_triple_ids`를 부여받았습니다.
6. allowed predicate, source/target node 존재, evidence 존재 조건을 통과한 edge만 최종 저장했습니다.

### 현재 predicate별 edge 개수

| Predicate | 생성 방식 | 개수 |
| --- | --- | ---: |
| `PRODUCES` | task/step의 output slot을 Artifact node로 연결 | 220 |
| `USES_INPUT` | task/step의 input slot을 Artifact/Concept node로 연결 | 201 |
| `PERFORMED_BY` | task/step의 role slot을 Role node로 연결 | 120 |
| `HAS_STEP` | DomainTask를 ProcedureStep 목록에 연결 | 99 |
| `PRECEDES` | 같은 task 안에서 step order 기준으로 순서 연결 | 77 |
| `HAS_PRINCIPLE` | task/step의 principle slot 연결 | 64 |
| `HAS_DECISION_GATEWAY` | task/step에서 발견된 의사결정 node 연결 | 54 |
| `HAS_RISK` | task/step의 risk slot 연결 | 39 |
| `HAS_GUARD_CONDITION` | DecisionGateway와 조건 node 연결 | 14 |
| `FEEDS_INTO` | artifact가 다음 task로 흘러가는 규칙 연결 | 9 |
| `USED_AS_INPUT_FOR` | artifact가 다음 task 입력으로 사용되는 규칙 연결 | 9 |

### Edge 검증 결과

| 검증 항목 | 결과 |
| --- | ---: |
| Final Layer 2 edges | 906 |
| Evidence가 있는 edges | 906 / 906 |
| `source_triple_ids`가 있는 edges | 906 / 906 |
| Evidence-missing edges | 0 |
| Domain/range violations | 0 |

핵심 해석: edge는 단순 관계 후보가 아니라, 실제 source/target node가 존재하고, 허용된 predicate이며, evidence anchor를 가진 경우에만 최종 KG에 들어갔습니다.

---

## 9. LLM은 어디에 사용했는가

LLM은 최종 KG를 그대로 생성한 도구가 아니라, 같은 chunk에 대해 baseline/proposed/ablation 조건별 후보 생성 성능을 비교하기 위한 prediction generator로 사용했습니다.

| 구분 | 최종 KG 구축 | LLM 실험 |
| --- | --- | --- |
| 목적 | 실제 데이터에 대한 KG build | 방법론 조건 비교 |
| 입력 | 전체 OCR/evidence, schema, task seed, rule dictionary | 120개 evaluation chunks |
| 출력 | node_id/edge_id/evidence가 있는 graph | 조건별 `triples`, `nodes`, `edges`, `mappings` |
| 검증 | dangling/type/evidence/structural validation | JSON parse, schema, predicate, evidence id validation |
| 현재 claim | KG 구축 완료 | silver/proxy diagnostic, human-gold 전 최종 성능 아님 |

사용 모델:

| 모델 | 사용 목적 | 상태 |
| --- | --- | --- |
| Qwen3-8B | 기본 baseline/proposed/ablation | 실행 완료 |
| Qwen3-14B | model scaling core conditions | 실행 완료 |
| Qwen3-32B-AWQ | 더 큰 모델의 현실적 scaling | 120 chunk core run 완료 |

---

## 10. 현재 실험 결과

### LLM 조건별 silver/proxy diagnostic

이 표는 human-gold 결과가 아니라, KG-derived silver reference 기준 진단 결과입니다.

| Condition | Edge F1 | Predicate F1 | Node F1 | Evidence F1 |
| --- | ---: | ---: | ---: | ---: |
| `B0_plain_llm` | 0.0000 | 0.0000 | 0.0350 | 0.0239 |
| `B1_predicate_constrained` | 0.0000 | 0.1416 | 0.0000 | 0.0291 |
| `B2_current_project` | 0.0000 | 0.0068 | 0.0215 | 0.0503 |
| `B6_sac_kg_verifier_pruner` | 0.0017 | 0.0774 | 0.0564 | 0.1008 |
| `P_cape_kg_actual` | 0.0018 | 0.0482 | 0.0326 | 0.0655 |

해석: 현재 값은 최종 성능이 아니라 진단값입니다. strict edge exact match가 매우 엄격하고, gold가 아닌 silver reference와 비교했기 때문에 교수님께는 "성능 우수성"이 아니라 "실험 파이프라인 및 진단 결과"로 설명하는 것이 안전합니다.

### Model scaling

| Model | Condition | Rows | Edge F1 | Predicate F1 | Node F1 | Evidence F1 |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Qwen3-8B | `P_cape_kg_actual` | 120 | 0.0018 | 0.0482 | 0.0326 | 0.0655 |
| Qwen3-14B | `P_cape_kg_actual` | 120 | 0.0017 | 0.0601 | 0.0298 | 0.0610 |
| Qwen3-32B-AWQ | `P_cape_kg_actual` | 120 | 0.0034 | 0.0662 | 0.0284 | 0.0542 |

해석: 32B-AWQ가 일부 silver diagnostic에서 개선을 보였지만, 이 역시 human-gold 전에는 최종 성능 주장으로 쓰면 안 됩니다.

### 구조 진단

| 항목 | 값 | 해석 |
| --- | ---: | --- |
| Ontology conformance | 1.0000 | schema/domain-range 위반 없음 |
| Procedural consistency | 0.9950 | 절차 구조 대부분 일관 |
| CQ answerability | 0.9167 | 12개 CQ 중 11개 구조적으로 응답 가능 |
| Domain/range errors | 0 | edge type 제약 위반 없음 |
| Evidence missing | 0 | accepted edge evidence 누락 없음 |
| Precedence cycles | 0 | 절차 순환 없음 |

---

## 11. 발표에서 강조할 핵심 메시지

### 강조해도 되는 것

| 주장 | 근거 |
| --- | --- |
| Layer 1 NCS/PCF KG 구축 완료 | NCS 4,109 nodes, PCF 5,301 nodes |
| Layer 2 업무 KG 구축 완료 | 179 nodes, 906 edges |
| Evidence-grounded KG 구조 확보 | edge evidence missing 0 |
| CQ 기반 procedural schema 설계 | 12개 CQ와 node/edge schema 연결 |
| LLM baseline/proposed/ablation/model scaling 실행 | Qwen3-8B, 14B, 32B-AWQ 실행 |
| Human review handoff 준비 | annotation, adjudication, mapping review 파일 준비 |

### 아직 보류해야 하는 것

| 보류할 주장 | 이유 |
| --- | --- |
| 최종 precision/recall/F1 성능 우수성 | human-gold annotation 미완료 |
| annotator agreement | IAA 미완료 |
| NCS/PCF mapping 정답성 | expert review 미완료 |
| active review 효율성 | 실제 사람 검수 시간/수정량 미수집 |
| 최종 논문 main table claim | claim gate가 human-gold 부족으로 FAIL |

---

## 12. 교수님께 보고할 때 사용할 수 있는 짧은 설명

이번 연구에서는 한국어 수주/제안 업무 문서에서 절차형 업무 지식을 KG로 구축했습니다. 먼저 OCR 문장을 sentence-level evidence anchor로 만들고, 12개 Competency Question을 기준으로 업무 task, step, input/output artifact, role, decision, risk를 표현하는 procedural schema를 설계했습니다. 최종 Layer 2 KG는 179개 node와 906개 edge로 구축되었고, 모든 edge는 원문 evidence anchor와 연결되어 있습니다.

LLM은 최종 KG를 직접 생성하는 도구라기보다, 같은 chunk에 대해 여러 방법론 조건의 후보 생성 결과를 비교하기 위한 실험 도구로 사용했습니다. 실제 프롬프트는 단순 triple extraction baseline부터 CQ, evidence, schema, validator, NCS/PCF bridge를 모두 포함한 `P_cape_kg_actual`까지 구성했습니다. Qwen3-8B, 14B, 32B-AWQ를 실행했고, 현재 결과는 silver/proxy diagnostic으로 정리되어 있습니다.

현재 발표에서 가장 안전한 결론은 "KG 구축과 실험 인프라는 완료되었고, 최종 성능 claim은 human-gold annotation, IAA, adjudication, mapping expert review, NCS-PCF crosswalk expert review, active-review effort evidence 이후 확정해야 한다"입니다.

---

## 13. 바로 보여줄 핵심 표

| 구분 | 핵심 결과 | 상태 |
| --- | ---: | --- |
| OCR clean sentences | 5,009 | 완료 |
| Evidence anchors | 5,009 | 완료 |
| Layer 2 chunks | 214 | 완료 |
| Evaluation chunks | 120 | 완료 |
| NCS Layer 1 nodes | 4,109 | 완료 |
| PCF Layer 1 nodes | 5,301 | 완료 |
| Layer 2 nodes | 179 | 완료 |
| Layer 2 edges | 906 | 완료 |
| Schema-valid triples | 906 | 완료 |
| NCS mapping candidates | 110 | expert review 전 |
| PCF mapping candidates | 110 | expert review 전 |
| Ontology conformance | 1.0000 | 구조 진단 완료 |
| Procedural consistency | 0.9950 | 구조 진단 완료 |
| CQ answerability | 0.9167 | 구조 진단 완료 |
| Human-gold chunks | 0 | 사람 검수 필요 |
| Claim gate | FAIL | expected fail, human-gold 부족 |
