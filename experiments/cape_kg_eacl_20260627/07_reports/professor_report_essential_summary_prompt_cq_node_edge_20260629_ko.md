# 교수님 보고용 별도 핵심 요약본

Generated: 2026-06-29  
Detailed slide draft: `experiments/cape_kg_eacl_20260627/07_reports/professor_report_slide_contents_current_20260628_ko.md`  
Traceability source: `experiments/cape_kg_eacl_20260627/06_release/prompt_node_edge_traceability.md`  
Experiment directory: `experiments/cape_kg_eacl_20260627`  
KG output directory: `outputs`

이 문서는 기존 슬라이드 원고와 별개로, 교수님께 핵심만 빠르게 보고하기 위한 요약본입니다. 초점은 "어떤 프롬프트로 무엇을 산출했는가", "CQ를 어떻게 만들었는가", "최종 node와 edge는 어떤 방식으로 만들어졌는가"입니다.

---

## 1. 가장 중요한 결론

이번 연구는 한국어 수주/제안 업무 문서에서 업무 절차 지식을 `DomainTask`, `ProcedureStep`, `Artifact`, `Role`, `DecisionGateway`, `GuardCondition`, `Risk` 등으로 구조화하고, 각 node/edge를 원문 sentence evidence에 연결한 CAPE-KG 구축 실험입니다.

현재 말할 수 있는 결론은 다음과 같습니다.

| 구분 | 현재 상태 | 교수님께 보고할 표현 |
| --- | --- | --- |
| Layer 1 NCS/PCF KG | 완료 | 표준 taxonomy 축을 구축했다 |
| Layer 2 업무 KG | 완료 | 수주/제안 업무 procedural KG를 구축했다 |
| Evidence grounding | 완료 | 최종 accepted edge 906개가 모두 evidence anchor를 가진다 |
| LLM baseline/proposed/ablation | 실행 완료 | Qwen3 계열로 조건별 후보 생성 실험을 수행했다 |
| Human-gold 기반 최종 성능표 | 미완료 | 사람 검수 이후 precision/recall/F1을 확정해야 한다 |
| Claim gate | expected FAIL | 실험 실패가 아니라 human-gold 미완료를 막는 안전장치다 |

핵심적으로, **KG 구축 완료**와 **논문용 최종 성능 claim 미완료**를 분리해서 설명해야 합니다.

---

## 2. 현재까지의 핵심 수치

현재 EACL 실험 패키지 기준 핵심 수치는 다음과 같습니다.

| 항목 | 값 | 의미 |
| --- | ---: | --- |
| OCR clean sentences | 5,009 | sentence-level evidence anchor의 원천 |
| Evidence anchors | 5,009 | node/edge가 참조하는 원문 근거 |
| Layer 1 NCS nodes | 4,109 | NCS 표준 taxonomy node |
| Layer 1 PCF nodes | 5,301 | PCF 표준 taxonomy node |
| Layer 2 chunks | 214 | 현재 corpus 기반 업무 KG 구축 단위 |
| Evaluation chunks | 120 | LLM 조건별 평가 chunk |
| Final Layer 2 nodes | 179 | 최종 업무 KG node |
| Final Layer 2 edges | 906 | 최종 업무 KG edge |
| Evidence-covered edges | 906 / 906 | 모든 최종 edge에 evidence 존재 |
| Dangling edges | 0 | source/target node 없는 edge 없음 |
| Type violations | 0 | schema type 위반 없음 |
| NCS mapping candidates | 110 | Layer 2 업무와 NCS 후보 연결 |
| PCF mapping candidates | 110 | Layer 2 업무와 PCF 후보 연결 |
| CQ answerability | 11 / 12 | CQ8 review checkpoint만 구조적 gap |
| Pre-human handoff validation | PASS | 사람 검수 전 handoff 인프라 준비 완료 |

주요 산출물은 다음입니다.

| 목적 | 파일 |
| --- | --- |
| 최종 Layer 2 nodes | `outputs/07_layer2_graph/layer2_nodes.jsonl` |
| 최종 Layer 2 edges | `outputs/07_layer2_graph/layer2_edges.jsonl` |
| Schema-valid triples | `outputs/06_triples/layer2_triples_schema_valid.jsonl` |
| NCS mapping 후보 | `outputs/08_mapping/l2_ncs_mapping_candidates.jsonl` |
| PCF mapping 후보 | `outputs/08_mapping/l2_pcf_mapping_candidates.jsonl` |
| KG viewer | `outputs/09_visualization/kg_viewer.html` |
| Prompt/node/edge 추적 | `experiments/cape_kg_eacl_20260627/06_release/prompt_node_edge_traceability.md` |
| Claim 가능성 표 | `experiments/cape_kg_eacl_20260627/06_release/claimable_main_table.md` |

---

## 3. 최종 KG와 LLM 산출물은 다르다

교수님께 가장 먼저 분명히 설명해야 하는 부분입니다.

| 구분 | 최종 KG | LLM 조건별 output |
| --- | --- | --- |
| 목적 | 실제 데이터에 대한 업무 KG 구축 | prompt/method 조건별 후보 생성 비교 |
| 위치 | `outputs/07_layer2_graph/` | `experiments/cape_kg_eacl_20260627/48_*`, `49_*`, `50_*` |
| 입력 | OCR evidence, task seeds, dictionaries, procedure templates, schema | 120개 evaluation chunk |
| 출력 | `node_id`, `edge_id`, source/target, evidence anchor가 있는 graph | 조건별 `triples`, `nodes`, `edges`, `mappings` |
| 검증 | dangling/type/evidence/procedural/CQ 구조 검증 | JSON parse, allowed type/predicate, evidence id 검증 |
| 현재 claim | KG 구축 완료 | silver/proxy diagnostic이며 최종 성능 claim 아님 |

보고용 핵심 문장:

> 최종 KG는 LLM raw output을 그대로 저장한 결과가 아닙니다. OCR evidence anchor, task seed, 용어 사전, procedure template, schema validator를 결합해 rule/schema/evidence 기반으로 조립한 graph입니다. LLM은 같은 데이터에서 baseline, proposed, ablation 조건별 후보 생성 능력을 비교하기 위해 별도로 실행했습니다.

---

## 4. 실제 사용한 프롬프트 조건

프롬프트 파일 위치는 `experiments/cape_kg_eacl_20260627/02_schema/prompts/`입니다. 파일에 저장된 조건별 prompt는 짧은 지시문이고, 실제 LLM 호출 때는 chunk sentence, sentence id, allowed schema, JSON shape, strict JSON contract가 runtime에서 결합됩니다.

| 조건 | 실제 prompt 원문 | 요구한 산출물 |
| --- | --- | --- |
| `B0_plain_llm` | `Extract subject-predicate-object triples from the chunk. Return JSON only.` | `triples` |
| `B1_predicate_constrained` | `Extract triples using only the allowed predicates. Return JSON only with evidence sentence ids.` | `edges` |
| `B2_current_project` | `Extract Task Frames, then triples, then post-process into the Layer2 schema.` | `nodes`, `edges` |
| `B3_edc_style` | `Extract, define, and canonicalize open-schema KG items, then emit CAPE-compatible nodes and edges for scoring.` | `nodes`, `edges` |
| `B4_taxonomy_rag` | `Retrieve NCS/PCF/task taxonomy snippets, then extract schema-constrained triples with evidence.` | `nodes`, `edges`, `mappings` |
| `B5_procedural_prompt` | `Extract actions, actors, gateways, guard conditions, artifact flows, and temporal/logical dependencies.` | `nodes`, `edges` |
| `B6_sac_kg_verifier_pruner` | `Use existing generator candidates, then apply schema/evidence verification and pruning in the style of SAC-KG. This is a deterministic approximation, not a full SAC-KG reproduction.` | `nodes`, `edges` |
| `P_cape_kg_actual` | `Use CQ-linked schema retrieval, procedural frame extraction, evidence-span constrained relation extraction, span verification, ontology validation, procedural consistency checks, and active review scoring.` | `nodes`, `edges`, `mappings` |
| `P_minus_CQ` | runtime condition only: 제안 방법론에서 CQ anchoring 제거 | `nodes`, `edges`, `mappings` |
| `P_minus_Evidence` | runtime condition only: evidence anchor 요구 약화 | `nodes`, `edges`, `mappings` |
| `P_minus_Procedural_schema` | runtime condition only: procedural schema 대신 flat schema 사용 | `nodes`, `edges`, `mappings` |
| `P_minus_Validator` | runtime condition only: validator rejection 없이 모델의 schema 선택 허용 | `nodes`, `edges`, `mappings` |
| `P_minus_Standard_bridge` | runtime condition only: NCS/PCF bridge 출력 제거 | `nodes`, `edges` |
| `P_minus_Schema_retrieval` | `Run CAPE-KG without chunk-specific schema/taxonomy retrieval; keep CQ, evidence grounding, procedural schema, validation, and mapping output shape.` | `nodes`, `edges`, `mappings` |

---

## 5. 실제 runtime prompt의 공통 구조

모든 조건에서 모델에는 다음 공통 제약이 함께 들어갔습니다.

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

Strict JSON 실행에서는 다음 계약을 추가했습니다.

```text
Strict JSON contract:
- Return exactly one JSON object and nothing else.
- The first non-whitespace character must be { and the last non-whitespace character must be }.
- Do not include markdown, code fences, comments, XML tags, <think> blocks, prose, or explanations.
- For Qwen/Qwen-style chat models, obey /no_think; do not emit hidden or visible reasoning.
- Output the JSON object immediately without a preamble.
- Use compact JSON without indentation or extra whitespace to reduce truncation risk.
- Use double-quoted JSON strings only.
- Use empty arrays for absent nodes, edges, triples, or mappings fields required by the requested shape.
```

이 구조 때문에 LLM은 원문 chunk 안의 sentence id를 evidence로 붙이고, schema 조건에 맞는 JSON만 반환해야 했습니다.

---

## 6. 제안 방법론 `P_cape_kg_actual`의 핵심

제안 방법론 prompt는 단순 triple extraction이 아니라 CQ, procedural schema, evidence grounding, validator, NCS/PCF mapping을 함께 요구했습니다.

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

요구한 JSON shape는 다음입니다.

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

## 7. CQ는 어떻게 생성했는가

CQ, 즉 Competency Question은 LLM이 자동 생성한 질문이 아니라, 연구자가 먼저 정의한 KG 요구사항입니다.

생성 절차는 다음과 같습니다.

1. 연구 문제를 먼저 정했습니다.
   - 한국어 수주/제안 업무 문서에서 절차형 업무 KG를 구축한다.
   - 단순 entity extraction이 아니라 task, step, input/output, role, decision, guard condition, risk, evidence, standard mapping을 표현한다.
2. KG가 답해야 할 질문 범주를 나누었습니다.
   - 업무 구성과 순서
   - 입력 자료와 산출물
   - 수행 역할
   - 의사결정과 조건
   - 산출물 흐름
   - 원문 evidence
   - NCS/PCF 표준 연결
3. 각 질문을 schema predicate와 연결했습니다.
   - "각 Task는 어떤 산출물을 생성하는가?" -> `PRODUCES`
   - "각 Task는 누가 수행하는가?" -> `PERFORMED_BY`
   - "의사결정 조건은 무엇인가?" -> `HAS_GUARD_CONDITION`
4. 동일 CQ를 schema, prompt, validation, CQ answerability evaluation에 재사용했습니다.

관련 파일:

| 역할 | 파일 |
| --- | --- |
| EACL 실험용 CQ | `experiments/cape_kg_eacl_20260627/02_schema/competency_questions.json` |
| 내부 KG build용 CQ | `outputs/03_schema/competency_questions.json` |
| CQ/schema 생성 코드 | `scripts/build_cape_kg_eacl_experiment.py`, `scripts/build_ax_epak_internal_kg.py` |
| runtime prompt 조립 코드 | `scripts/run_cape_llm_condition_baselines.py` |
| CQ query pack | `experiments/cape_kg_eacl_20260627/06_release/cq_query_pack.md` |

---

## 8. CQ 실제 목록과 현재 answerability

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

현재 CQ answerability는 11/12입니다. CQ8은 `HAS_REVIEW_CHECKPOINT` edge가 아직 없어서 structural gap으로 추적 중입니다.

---

## 9. 최종 KG node 산출 방식

최종 `outputs/07_layer2_graph/layer2_nodes.jsonl`의 node는 LLM 출력물을 그대로 넣은 것이 아니라, evidence anchor, task seed, 용어 사전, procedure template, schema validator를 결합해 만들었습니다.

Node 생성 흐름:

1. OCR sentence를 `EA-JS-*` evidence anchor로 변환
2. `TASK_SEEDS`의 label, alias, keyword로 관련 sentence 검색
3. 검색된 sentence에서 artifact, role, decision, principle, risk 후보를 용어 사전으로 추출
4. 각 task frame을 `DomainTask` node로 생성
5. task별 procedure template 또는 입력/산출물 기반 추론으로 `ProcedureStep` node 생성
6. 산출물이 다음 업무로 흘러가는 규칙으로 `ArtifactFlow` node 생성
7. `node_id` 기준 중복 제거 후 모든 node에 evidence와 review status 부여

Node type별 결과:

| Node type | 개수 | 생성 방식 |
| --- | ---: | --- |
| `ProcedureStep` | 99 | task별 procedure template 또는 입력/산출물 기반 step 추론 |
| `DomainTask` | 22 | `TASK_SEEDS`의 label/alias/keyword로 OCR sentence evidence 검색 |
| `Artifact` | 14 | task evidence 안의 입력물/산출물 용어 매칭 |
| `GuardCondition` | 13 | 의사결정 evidence에서 조건/가능성/경쟁/자원 표현 추출 |
| `Role` | 10 | 수행자/책임 주체 용어 매칭 |
| `ArtifactFlow` | 9 | 특정 산출물이 다음 task 입력으로 쓰이는 규칙 |
| `Principle` | 5 | 원칙/품질 기준 용어 매칭 |
| `DecisionGateway` | 4 | 의사결정 관련 용어 매칭 |
| `Risk` | 3 | 위험/불리함/실패 가능성 용어 매칭 |

요약하면, node는 "LLM에게 node를 뽑아 달라고 요청한 결과"가 아니라, 업무 seed와 evidence 기반 규칙을 통해 schema type별로 정규화한 결과입니다.

---

## 10. 최종 KG edge 산출 방식

최종 `outputs/07_layer2_graph/layer2_edges.jsonl`의 edge는 source node, target node, predicate, evidence anchor가 모두 유효한 경우에만 남겼습니다.

Edge 생성 흐름:

1. task frame의 `inputs`, `outputs`, `roles`, `principles`, `risks` slot을 predicate로 변환
2. decision gateway와 guard condition을 별도 predicate로 연결
3. procedure step은 `HAS_STEP`, step 순서는 `PRECEDES`로 연결
4. artifact flow 규칙은 `FEEDS_INTO`, `USED_AS_INPUT_FOR`로 연결
5. 모든 edge를 triple record로 변환하고 `source_triple_ids` 부여
6. allowed predicate, source/target node 존재, evidence 존재 조건을 통과한 edge만 최종 저장

Predicate별 결과:

| Predicate | 개수 | 생성 방식 |
| --- | ---: | --- |
| `PRODUCES` | 220 | task/step의 outputs slot을 Artifact node로 연결 |
| `USES_INPUT` | 201 | task/step의 inputs slot을 Artifact 또는 Concept node로 연결 |
| `PERFORMED_BY` | 120 | task/step의 roles slot을 Role node로 연결 |
| `HAS_STEP` | 99 | DomainTask를 해당 ProcedureStep 목록에 연결 |
| `PRECEDES` | 77 | 같은 task 안에서 step order 기준 순서 연결 |
| `HAS_PRINCIPLE` | 64 | task/step의 principles slot을 Principle node로 연결 |
| `HAS_DECISION_GATEWAY` | 54 | task/step에서 발견된 의사결정 node 연결 |
| `HAS_RISK` | 39 | task/step의 risks slot을 Risk node로 연결 |
| `HAS_GUARD_CONDITION` | 14 | DecisionGateway에서 추출된 조건 node 연결 |
| `FEEDS_INTO` | 9 | Artifact가 다음 task로 흘러가는 규칙 연결 |
| `USED_AS_INPUT_FOR` | 9 | Artifact가 다음 task 입력으로 사용되는 규칙 연결 |

검증 결과:

| 검증 항목 | 결과 |
| --- | ---: |
| Final Layer 2 edges | 906 |
| Evidence가 있는 edges | 906 / 906 |
| `source_triple_ids`가 있는 edges | 906 / 906 |
| Dangling edges | 0 |
| Type violations | 0 |

---

## 11. Triple, node, edge의 관계

현재 pipeline에서는 triple이 edge 생성과 evidence 검증을 위한 중간 표현입니다.

| 단계 | 파일 | 현재 수량 |
| --- | --- | ---: |
| Task frame | `outputs/04_task_frames/canonical_task_catalog.json` | 22 tasks |
| Procedure structure | `outputs/05_procedure/procedure_structures_clean.jsonl` | 22 procedures / 99 steps |
| Schema-valid triple | `outputs/06_triples/layer2_triples_schema_valid.jsonl` | 906 triples |
| Final nodes | `outputs/07_layer2_graph/layer2_nodes.jsonl` | 179 nodes |
| Final edges | `outputs/07_layer2_graph/layer2_edges.jsonl` | 906 edges |

정리하면, edge를 subject-predicate-object와 evidence로 검증하기 위해 triple 형태를 사용했고, 최종 graph에는 검증된 node와 edge가 저장됩니다.

---

## 12. LLM 조건별 validated output 수량

아래 수치는 human-gold 성능이 아니라, 각 조건이 유효 JSON으로 산출한 후보 수량입니다.

| condition | valid rows | triples | nodes | edges | mappings |
| --- | ---: | ---: | ---: | ---: | ---: |
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

주의할 점은 수량이 많다고 성능이 높다는 뜻은 아니라는 것입니다. precision/recall/F1은 adjudicated human-gold가 들어온 뒤 계산해야 합니다.

---

## 13. 실행한 LLM 모델과 실험 조건

현재 LLM 실험은 Qwen3 계열을 중심으로 진행했습니다.

| 모델 | 목적 | 현재 상태 |
| --- | --- | --- |
| Qwen3-8B | 기본 baseline/proposed/ablation | 120 chunk 조건별 실행 완료 |
| Qwen3-14B | 현실적인 model scaling | core condition 실행 완료 |
| Qwen3-32B-AWQ | 더 큰 모델의 quantized scaling | 120 chunk core run 완료 |

실험 조건은 크게 네 그룹입니다.

| 그룹 | 조건 | 의미 |
| --- | --- | --- |
| 단순 baseline | `B0_plain_llm`, `B1_predicate_constrained` | schema가 약하거나 predicate만 제한한 기준선 |
| 기존/문헌식 baseline | `B2_current_project`, `B3_edc_style`, `B4_taxonomy_rag`, `B5_procedural_prompt`, `B6_sac_kg_verifier_pruner` | task frame, EDC, taxonomy RAG, procedural prompt, verifier/pruner 계열 비교 |
| Proposed | `P_cape_kg_actual` | CQ, schema, evidence, validator, NCS/PCF bridge를 결합 |
| Ablation | `P_minus_*` | CQ/evidence/procedural schema/validator/standard bridge/schema retrieval의 효과 분리 |

---

## 14. 현재 claim 상태

현재 pre-human handoff validation은 PASS입니다.

| 항목 | 상태 | 의미 |
| --- | --- | --- |
| Pre-human handoff validation | PASS | 사람 검수 시작 전 파일/검증/번들 준비가 되어 있음 |
| Checks | 57 | 자동 점검 항목 수 |
| PASS | 56 | 통과 항목 |
| WARN | 1 | human-gold 미완료 경고 |
| FAIL | 0 | handoff 인프라 실패 없음 |

하지만 submission claim gate는 expected FAIL입니다.

| 항목 | 상태 | 이유 |
| --- | --- | --- |
| Claim gate | FAIL | human-gold, IAA, adjudication, human-gold scoring, mapping expert review, NCS-PCF crosswalk expert review, active-review effort evidence 미완료 |
| Core extraction main result | pending human | 0/100 adjudicated chunks |
| NCS/PCF mapping downstream | pending expert review | expert review 반환 전 |
| Active-review efficiency | pending human effort | timing/correction evidence 반환 전 |

보고용 표현:

> Claim gate FAIL은 자동 실험 실패가 아니라, 아직 사람이 검수한 gold label이 없는 상태에서 성능 우수성을 주장하지 못하도록 막는 보수적 gate입니다.

---

## 15. 교수님께 바로 설명할 수 있는 핵심 문장

1. "최종 KG는 LLM raw output이 아니라, OCR sentence evidence, task seed, dictionary, procedure template, schema validator를 결합해 구축한 evidence-grounded procedural KG입니다."
2. "LLM은 최종 KG를 그대로 생성한 도구라기보다, baseline/proposed/ablation 조건에서 후보 node/edge/mapping을 얼마나 안정적으로 생성하는지 비교하기 위해 사용했습니다."
3. "CQ는 LLM이 만든 것이 아니라 연구자가 먼저 정의한 KG 요구사항이며, schema, prompt, validation, evaluation을 묶는 anchor 역할을 합니다."
4. "현재 Layer 2 KG는 179 nodes, 906 edges이고, 모든 final edge가 evidence anchor를 갖습니다."
5. "논문에서 최종 성능표를 주장하려면 human-gold annotation, IAA, adjudication, mapping expert review, NCS-PCF crosswalk expert review, active-review effort evidence를 완료해야 합니다."

---

## 16. 발표에서 조심해야 할 표현

| 피해야 할 표현 | 더 정확한 표현 |
| --- | --- |
| "LLM이 KG를 만들었다" | "최종 KG는 rule/schema/evidence 기반으로 구축했고, LLM은 조건별 후보 생성 실험에 사용했다" |
| "성능이 좋다" | "현재는 silver/proxy diagnostic이며, human-gold 이후 최종 성능 claim이 가능하다" |
| "mapping이 완료되었다" | "NCS/PCF mapping 후보는 생성되었고, expert review 전이다" |
| "main table이 완성되었다" | "claimability table과 diagnostic table은 있으며, human-gold main performance table은 아직 미완료다" |
| "claim gate FAIL이라 실패했다" | "human-gold 미완료를 표시하는 expected FAIL이다" |

---

## 17. 가장 중요한 후속 작업

최종 논문 claim을 위해 남은 작업은 사람 검수 기반입니다.

| 작업 | 현재 상태 | 완료 후 가능해지는 것 |
| --- | --- | --- |
| Human-gold annotation | 미완료 | node/edge/evidence precision/recall/F1 계산 |
| IAA 계산 | 미완료 | annotation 신뢰도 보고 |
| Adjudication | 미완료 | 최종 gold 기준 확정 |
| Mapping expert review | 미완료 | NCS/PCF mapping Hit@K, P@K, MRR, nDCG claim |
| Active-review human effort | 미완료 | active-review efficiency claim |

---

## 18. 이 요약본의 기준 파일

이 문서의 수치와 해석은 다음 파일을 기준으로 정리했습니다.

| 목적 | 기준 파일 |
| --- | --- |
| Prompt/CQ/node/edge traceability | `experiments/cape_kg_eacl_20260627/06_release/prompt_node_edge_traceability.md` |
| CQ query/sample answer | `experiments/cape_kg_eacl_20260627/06_release/cq_query_pack.md` |
| Structural diagnostics | `experiments/cape_kg_eacl_20260627/04_evaluation/structural_evaluation_report.md` |
| Claimable main table | `experiments/cape_kg_eacl_20260627/06_release/claimable_main_table.md` |
| Pre-human handoff validation | `experiments/cape_kg_eacl_20260627/06_release/pre_human_handoff_validation.md` |
| Detailed professor slide draft | `experiments/cape_kg_eacl_20260627/07_reports/professor_report_slide_contents_current_20260628_ko.md` |
