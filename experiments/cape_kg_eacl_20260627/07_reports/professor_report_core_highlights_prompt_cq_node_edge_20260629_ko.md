# 교수님 보고용 핵심 브리핑: CAPE-KG 방법론, 프롬프트, CQ, Node/Edge 산출 방식

Generated: 2026-06-29  
Experiment directory: `experiments/cape_kg_eacl_20260627`  
KG output directory: `outputs`  
Related full slide draft: `experiments/cape_kg_eacl_20260627/07_reports/professor_report_slide_contents_current_20260628_ko.md`

이 문서는 기존 슬라이드 원고와 별개로, 교수님께 먼저 설명할 핵심 내용만 정리한 브리핑 파일입니다. 초점은 "무엇을 실행했고, 어떤 프롬프트와 CQ를 사용했으며, node와 edge를 어떤 방식으로 만들었는가"입니다.

---

## 1. 교수님께 먼저 말할 핵심 요약

1. 본 연구는 한국어 수주/제안 업무 문서에서 업무 절차, 입력/산출물, 역할, 의사결정, 위험, 원문 근거를 함께 추출해 evidence-grounded procedural KG를 구축하는 실험입니다.
2. 최종 KG는 LLM 출력물을 그대로 저장한 것이 아니라, OCR sentence evidence, CQ, procedural schema, rule/template assembly, validator를 거쳐 만든 Layer 2 업무 KG입니다.
3. Layer 1에는 NCS와 PCF 표준 taxonomy를 구축했고, Layer 2 업무 KG를 이 표준축과 mapping 후보로 연결했습니다.
4. LLM은 baseline/proposed/ablation/model-scaling 조건의 후보 생성 실험에 사용했습니다. 현재 사용한 주요 모델군은 Qwen3-8B, Qwen3-14B, Qwen3-32B-AWQ입니다.
5. 현재 KG 구축과 자동 진단은 완료되었지만, 최종 논문 성능 claim은 아직 하면 안 됩니다. human-gold annotation, IAA, adjudication, expert review가 아직 남아 있기 때문입니다.
6. 현재 claim gate가 FAIL인 것은 자동 실험 실패가 아니라, 사람 검수 전 성능 과장을 막기 위한 보수적 안전장치입니다.
7. 교수님께 보고할 핵심 표현은 "CAPE-KG는 한국어 업무 문서에서 evidence-grounded procedural KG를 구축하고 NCS/PCF 표준과 bridge하는 방법론"입니다.

---

## 2. 현재 완료된 핵심 산출물

| 항목 | 현재 값 | 해석 |
| --- | ---: | --- |
| OCR clean sentences / evidence anchors | 5,009 | 원문 sentence 단위 근거 |
| Layer 2 chunks | 214 | 전체 업무 문서 chunk |
| LLM evaluation chunks | 120 | baseline/proposed/ablation 평가용 chunk |
| Layer 1 NCS nodes | 4,109 | NCS 표준 KG |
| Layer 1 PCF nodes | 5,301 | PCF 표준 KG |
| Canonical DomainTask | 22 | 수주/제안 업무 task |
| Layer 2 KG nodes | 179 | 최종 업무 KG node |
| Layer 2 KG edges | 906 | 최종 업무 KG edge |
| Schema-valid triples | 906 | validator 통과 triple |
| NCS mapping candidates | 110 | Layer 2 to NCS 후보 |
| PCF mapping candidates | 110 | Layer 2 to PCF 후보 |
| NCS-PCF crosswalk candidates | 220 | Layer 2를 매개로 한 NCS-PCF 후보 |
| Evidence-missing edges | 0 | 모든 최종 edge가 evidence 보유 |
| Dangling edges | 0 | source/target 없는 edge 없음 |
| Domain/range violations | 0 | schema 위반 없음 |

핵심 파일:

| 목적 | 파일 |
| --- | --- |
| 최종 Layer 2 nodes | `outputs/07_layer2_graph/layer2_nodes.jsonl` |
| 최종 Layer 2 edges | `outputs/07_layer2_graph/layer2_edges.jsonl` |
| Schema-valid triples | `outputs/06_triples/layer2_triples_schema_valid.jsonl` |
| NCS mapping 후보 | `outputs/08_mapping/l2_ncs_mapping_candidates.jsonl` |
| PCF mapping 후보 | `outputs/08_mapping/l2_pcf_mapping_candidates.jsonl` |
| NCS-PCF crosswalk 후보 | `outputs/08_mapping/l2_ncs_pcf_crosswalk_candidates.jsonl` |
| KG viewer | `outputs/09_visualization/kg_viewer.html` |
| Prompt/node/edge traceability | `experiments/cape_kg_eacl_20260627/06_release/prompt_node_edge_traceability.md` |
| Paper table 초안 | `experiments/cape_kg_eacl_20260627/06_release/paper_tables.md` |
| Claim 가능 범위 정리 | `experiments/cape_kg_eacl_20260627/06_release/claimable_main_table.md` |

---

## 3. 방법론 전체 흐름

```text
OCR workbook
  -> sentence-level evidence anchors
  -> NCS/PCF Layer 1 KG
  -> Layer 2 chunks
  -> CQ + procedural schema
  -> task frame generation
  -> procedure structure + schema-valid triples
  -> Layer 2 node/edge graph
  -> NCS/PCF mapping candidates
  -> LLM baseline/proposed/ablation/model scaling
  -> structural diagnostics + human-review handoff + claim gate
```

중요한 구분:

| 구분 | 의미 |
| --- | --- |
| 최종 KG | rule/schema/evidence 기반으로 조립된 현재 Layer 2 업무 KG |
| LLM 실험 산출물 | 각 prompt condition이 생성한 prediction JSON |
| 최종 논문 성능 | human-gold 반환 후 계산해야 하는 precision/recall/F1 |

---

## 4. CAPE-KG 방법론의 구성 요소

| 구성 요소 | 역할 | 이번 실험에서의 구현 |
| --- | --- | --- |
| CQ | KG가 답해야 하는 질문 정의 | 12개 CQ를 schema, prompt, evaluation에 재사용 |
| Procedural schema | node type과 predicate 제한 | `DomainTask`, `ProcedureStep`, `Artifact`, `Role`, `DecisionGateway`, `GuardCondition` 등 |
| Evidence grounding | 모든 지식 항목을 원문 sentence에 연결 | `evidence_anchor_ids` 사용 |
| Runtime prompt | chunk별 sentence와 allowed schema를 LLM에 제공 | `scripts/run_cape_llm_condition_baselines.py` |
| Validator | JSON, evidence, type, predicate, domain/range 검증 | invalid schema/evidence 출력 reject |
| Standard bridge | Layer 2 task를 NCS/PCF 표준 후보와 연결 | NCS 110개, PCF 110개 |
| Human review gate | 최종 claim 전 사람 검수 강제 | human-gold, IAA, adjudication, expert review 대기 |

---

## 5. CQ는 어떻게 생성했는가

CQ는 LLM이 자동 생성한 질문이 아닙니다. 연구자가 먼저 "이 업무 KG가 답해야 하는 질문"을 정의했고, 이 질문을 node type과 edge predicate로 연결했습니다.

생성 절차:

1. 연구 문제를 "한국어 수주/제안 업무 문서에서 절차형 KG를 구축하는 문제"로 정의했습니다.
2. 업무자가 실제로 물을 질문 범주를 정했습니다.
3. 각 질문을 필요한 node type과 predicate에 연결했습니다.
4. 같은 CQ 목록을 schema 설계, LLM prompt, ablation, structural evaluation에서 재사용했습니다.

CQ가 필요한 이유:

| 역할 | 설명 |
| --- | --- |
| Schema 설계 기준 | 어떤 node type과 predicate가 필요한지 결정 |
| Prompt 제약 | LLM이 어떤 업무 질문에 답해야 하는지 명시 |
| Ablation 기준 | `P_minus_CQ`로 CQ anchoring 제거 효과 비교 |
| Evaluation 기준 | CQ answerability를 structural diagnostic으로 계산 |

---

## 6. 실제 CQ 목록과 현재 KG에서의 support

| CQ | 질문 | 연결 predicate | 현재 support |
| --- | --- | --- | ---: |
| CQ1 | 수주·제안 업무는 어떤 주요 Task와 절차 단계로 구성되는가? | `HAS_STEP`, `PRECEDES` | 176 |
| CQ2 | 각 Task는 어떤 입력 자료를 사용하는가? | `USES_INPUT` | 201 |
| CQ3 | 각 Task는 어떤 산출물을 생성하는가? | `PRODUCES` | 220 |
| CQ4 | 각 Task는 누가 수행하거나 책임지는가? | `PERFORMED_BY` | 120 |
| CQ5 | 어떤 의사결정 지점이 존재하는가? | `HAS_DECISION_GATEWAY` | 54 |
| CQ6 | 의사결정에는 어떤 조건이나 판단 기준이 필요한가? | `HAS_GUARD_CONDITION` | 14 |
| CQ7 | 산출물은 다음 업무에서 어떻게 사용되는가? | `FEEDS_INTO`, `USED_AS_INPUT_FOR` | 18 |
| CQ8 | 제안서 리뷰는 어떤 단계에서 어떻게 수행되는가? | `HAS_REVIEW_CHECKPOINT` | 0 |
| CQ9 | 각 업무에서 지켜야 할 원칙은 무엇인가? | `HAS_PRINCIPLE` | 64 |
| CQ10 | 각 지식 항목은 원문 어느 chunk/page/span에 근거가 있는가? | `EVIDENCED_BY` | 906 |
| CQ11 | 특정 업무는 어떤 NCS 능력단위와 관련되는가? | `REQUIRES_CAPABILITY`, `CANDIDATE_ALIGNS_WITH` | 110 |
| CQ12 | 특정 업무는 PCF 프로세스 체계상 어디에 위치하는가? | `PROCESS_CONTEXT`, `CANDIDATE_ALIGNS_WITH` | 110 |

현재 CQ answerability는 `11/12 = 0.916667`입니다. CQ8은 `HAS_REVIEW_CHECKPOINT` edge가 아직 최종 KG에 없어서 structural gap으로 남아 있습니다.

---

## 7. 실제 사용한 프롬프트 파일

프롬프트 파일 위치:

`experiments/cape_kg_eacl_20260627/02_schema/prompts/`

| 조건 | 실제 저장된 핵심 프롬프트 | 요구 산출물 |
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
| strict_json_contract | JSON object만 반환, markdown/설명/XML/`<think>` 금지, `/no_think`, compact JSON, 빈 배열 사용 | 모든 strict JSON 실행에 적용 |

---

## 8. 실제 runtime prompt 공통 구조

프롬프트 파일의 한 줄 지시문만 LLM에 들어간 것이 아닙니다. 실제 실행에서는 chunk sentence, sentence id, evidence 조건, allowed schema, JSON shape가 결합되었습니다.

공통 runtime template:

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

Qwen strict JSON contract:

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

`P_cape_kg_actual` 조건에는 다음 요소가 추가로 들어갑니다.

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

---

## 9. 조건별 LLM 산출물 수량

아래 수치는 LLM이 조건별로 생성하고 validator가 통과시킨 prediction JSON 수량입니다. 이는 human-gold 성능이 아니라 생성/진단 수량입니다.

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

발표 시 주의할 점:

- 이 표는 "어떤 조건에서 어떤 JSON 후보를 얼마나 생성했는가"를 보여줍니다.
- 이 표만으로 "어떤 방법이 더 정확하다"라고 말하면 안 됩니다.
- 정확도, 재현율, F1의 최종 주장은 human-gold annotation 후 계산해야 합니다.

---

## 10. Node는 어떻게 산출했는가

최종 node는 LLM 출력물을 그대로 복사한 것이 아니라, OCR evidence와 task/procedure 규칙을 사용해 생성했습니다.

Node 생성 흐름:

1. OCR sentence를 `EA-JS-*` evidence anchor로 변환했습니다.
2. 업무 seed label, alias, keyword로 관련 sentence를 검색했습니다.
3. sentence 안에서 artifact, role, decision, principle, risk 후보를 찾았습니다.
4. task frame을 `DomainTask` node로 만들었습니다.
5. task별 procedure template으로 `ProcedureStep` node를 만들었습니다.
6. 산출물이 다음 업무 입력으로 흘러가는 경우 `ArtifactFlow` node를 만들었습니다.
7. `node_id` 기준으로 중복 제거하고, evidence와 review status를 붙였습니다.

현재 Layer 2 node 구성:

| Node type | 생성 방식 | 개수 |
| --- | --- | ---: |
| `DomainTask` | 업무 seed, alias, keyword, evidence sentence 검색 | 22 |
| `ProcedureStep` | task별 procedure template 또는 입력/산출물 기반 step 추론 | 99 |
| `Artifact` | 입력물/산출물 용어 매칭 | 14 |
| `Role` | 수행자/책임 주체 용어 매칭 | 10 |
| `DecisionGateway` | 의사결정 관련 표현 매칭 | 4 |
| `GuardCondition` | 조건/판단 기준 표현 추출 | 13 |
| `Principle` | 원칙/품질 기준 용어 매칭 | 5 |
| `Risk` | 위험/불리함/실패 가능성 표현 매칭 | 3 |
| `ArtifactFlow` | 산출물이 다음 task 입력으로 쓰이는 흐름 규칙 | 9 |
| 합계 |  | 179 |

대표 예시:

| CQ | 필요한 node |
| --- | --- |
| CQ1 | `DomainTask`, `ProcedureStep` |
| CQ2, CQ3 | `Artifact` |
| CQ4 | `Role` |
| CQ5, CQ6 | `DecisionGateway`, `GuardCondition` |
| CQ9 | `Principle`, `Risk` |
| CQ11, CQ12 | Layer 2 task와 NCS/PCF mapping 후보 |

---

## 11. Edge는 어떻게 산출했는가

최종 edge는 predicate별 규칙으로 생성한 뒤, source node, target node, allowed predicate, evidence 조건을 통과한 것만 저장했습니다.

Edge 생성 흐름:

1. task frame의 `inputs`, `outputs`, `roles`, `principles`, `risks` slot을 predicate로 변환했습니다.
2. task와 step 관계는 `HAS_STEP`으로 연결했습니다.
3. 같은 task 안의 step 순서는 `PRECEDES`로 연결했습니다.
4. task/step이 사용하는 입력물은 `USES_INPUT`으로 연결했습니다.
5. task/step이 만드는 산출물은 `PRODUCES`로 연결했습니다.
6. 수행 주체는 `PERFORMED_BY`로 연결했습니다.
7. 의사결정 지점과 조건은 `HAS_DECISION_GATEWAY`, `HAS_GUARD_CONDITION`으로 연결했습니다.
8. 산출물이 다음 업무 입력으로 쓰이는 경우 `FEEDS_INTO`, `USED_AS_INPUT_FOR`로 연결했습니다.
9. 모든 edge에 `evidence_anchor_ids`와 `source_triple_ids`를 붙였습니다.
10. dangling edge, unknown predicate, domain/range violation, evidence missing 여부를 검증했습니다.

현재 Layer 2 edge 구성:

| Predicate | 의미 | 개수 |
| --- | --- | ---: |
| `PRODUCES` | 업무/단계가 산출물을 생성 | 220 |
| `USES_INPUT` | 업무/단계가 입력물을 사용 | 201 |
| `PERFORMED_BY` | 업무/단계의 수행 주체 | 120 |
| `HAS_STEP` | task와 procedure step 연결 | 99 |
| `PRECEDES` | 같은 task 안의 step 순서 | 77 |
| `HAS_PRINCIPLE` | 원칙/품질 기준 연결 | 64 |
| `HAS_DECISION_GATEWAY` | 의사결정 지점 연결 | 54 |
| `HAS_RISK` | 위험 요소 연결 | 39 |
| `HAS_GUARD_CONDITION` | 의사결정 조건 연결 | 14 |
| `FEEDS_INTO` | 산출물이 다음 업무로 흘러감 | 9 |
| `USED_AS_INPUT_FOR` | 산출물이 다음 task 입력으로 사용 | 9 |
| 합계 |  | 906 |

검증 결과:

| 검증 항목 | 결과 |
| --- | ---: |
| Final edges | 906 |
| Edges with evidence | 906 / 906 |
| Edges with `source_triple_ids` | 906 / 906 |
| Dangling edges | 0 |
| Unknown predicates | 0 |
| Domain/range violations | 0 |
| Evidence-missing edges | 0 |

---

## 12. 모델 스케일링 결과는 어떻게 해석해야 하는가

Qwen3-8B, Qwen3-14B, Qwen3-32B-AWQ를 120 evaluation chunks의 핵심 조건에 대해 실행했습니다. 아래 값은 silver/proxy diagnostic입니다.

| Model | Condition | Rows | Predicted edges | Exact edge F1 | Predicate F1 | Node F1 | Evidence F1 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Qwen3-8B | `P_cape_kg_actual` | 120 | 275 | 0.0018 | 0.0482 | 0.0326 | 0.0655 |
| Qwen3-14B | `P_cape_kg_actual` | 120 | 332 | 0.0017 | 0.0601 | 0.0298 | 0.0610 |
| Qwen3-32B-AWQ | `P_cape_kg_actual` | 120 | 360 | 0.0034 | 0.0662 | 0.0284 | 0.0542 |

해석:

- 32B-AWQ는 현재 완료된 가장 큰 local core diagnostic입니다.
- 32B-AWQ에서 exact edge F1과 predicate F1은 8B보다 높지만, evidence F1은 낮습니다.
- 따라서 "모델이 커질수록 모든 지표가 좋아진다"라고 말하면 안 됩니다.
- 이 표는 최종 성능표가 아니라 human-gold 전의 진단표입니다.

---

## 13. 현재 claim 가능 범위와 불가능 범위

| 항목 | 현재 상태 | 발표 가능 여부 |
| --- | --- | --- |
| KG 구축 완료 | 가능 | Layer 1 NCS/PCF KG와 Layer 2 업무 KG 구축 완료라고 말할 수 있음 |
| Evidence grounding | 가능 | 최종 Layer 2 edge 906개가 모두 evidence를 가진다고 말할 수 있음 |
| LLM 조건별 실행 | 가능 | B0/B1/B2/P, ablation, Qwen3 scaling을 실행했다고 말할 수 있음 |
| Public benchmark adapter | 가능하되 보조 근거 | PAGED/Text2KG subset diagnostic으로만 설명 |
| Human-gold 성능 우수성 | 불가 | 아직 annotation/adjudication 전 |
| Mapping 성능 | 불가 | NCS/PCF expert review 전 |
| Active-review 효율성 | 불가 | human effort/timing evidence 전 |

가장 안전한 발표 표현:

> 현재까지는 KG 구축, LLM 조건별 실행, structural diagnostics, release/human-review handoff까지 완료했습니다. 다만 최종 성능 superiority claim은 human-gold annotation, IAA, adjudication, expert review가 끝난 뒤에만 제시하겠습니다.

---

## 14. 현재 남은 필수 단계

| 남은 단계 | 왜 필요한가 | 현재 상태 |
| --- | --- | --- |
| 100+ chunks human-gold annotation | 최종 extraction 성능 계산 | 0 completed chunks |
| 500+ node/edge/evidence items | 최소 논문 성능표의 gold item 확보 | 0 items |
| 2 annotator IAA | annotation 신뢰도 제시 | pending |
| Adjudication | 최종 gold label 확정 | pending |
| `P_cape_kg_actual` human-gold scoring | 제안 방법론 최종 F1 계산 | pending |
| NCS/PCF mapping expert review | mapping Hit@K, P@K, MRR, nDCG 계산 | 220 rows pending |
| NCS-PCF crosswalk expert review | crosswalk utility/accept-rate claim | 220 rows pending |
| Active-review effort evidence | review 효율성 claim | 204 rows pending |

---

## 15. 발표용 결론 문장

교수님께 보고할 때는 다음 문장으로 정리할 수 있습니다.

> 이번 실험에서는 한국어 수주/제안 업무 문서를 sentence evidence 단위로 정제한 뒤, CQ와 procedural schema를 기준으로 Layer 2 업무 KG를 구축했습니다. 최종 KG는 179개 node와 906개 edge로 구성되며, 모든 edge가 원문 evidence에 연결되어 있습니다. 또한 NCS/PCF 표준 taxonomy와의 mapping 후보, LLM baseline/proposed/ablation/model-scaling 결과, structural diagnostics, human-review handoff까지 준비했습니다. 다만 현재 결과는 pre-human stage이므로, 최종 논문 성능 주장은 human-gold annotation, IAA, adjudication, expert review 이후에 확정해야 합니다.

