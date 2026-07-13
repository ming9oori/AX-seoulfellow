# 교수님 보고용 핵심 요약본: Prompt, CQ, Node/Edge 산출 방식

Generated: 2026-06-29  
Detailed slide draft: `experiments/cape_kg_eacl_20260627/07_reports/professor_report_slide_contents_current_20260628_ko.md`  
Traceability source: `experiments/cape_kg_eacl_20260627/06_release/prompt_node_edge_traceability.md`  
Experiment directory: `experiments/cape_kg_eacl_20260627`  
KG output directory: `outputs`

이 문서는 기존 교수님 보고용 슬라이드 원고와 별개로, 핵심만 빠르게 설명하기 위한 별도 요약본입니다. 초점은 다음 네 가지입니다.

1. 어떤 프롬프트 조건으로 무엇을 산출했는가
2. CQ를 어떻게 설계했고, 어떤 예시가 있는가
3. 최종 KG node를 어떤 방식으로 만들었는가
4. 최종 KG edge를 어떤 방식으로 만들었는가

---

## 1. 한 문장 결론

이번 연구는 한국어 수주/제안 업무 문서에서 task, step, input/output, role, decision, risk를 원문 evidence와 연결된 procedural KG로 구축하고, 이를 NCS/PCF 표준 taxonomy와 연결하는 CAPE-KG 방법론을 적용한 것입니다.

교수님께 가장 먼저 구분해서 말씀드려야 할 점은 다음입니다.

> KG 구축 자체는 완료되었습니다. 다만 논문에서 최종 성능 우수성을 주장하려면 human-gold annotation, IAA, adjudication, mapping expert review, NCS-PCF crosswalk expert review, active-review effort evidence가 아직 필요합니다.

---

## 2. 현재까지의 핵심 결과

| 항목 | 현재 결과 | 의미 |
| --- | ---: | --- |
| OCR clean sentences | 5,009 | KG evidence anchor의 원천 문장 |
| Evidence anchors | 5,009 | node/edge가 참조하는 sentence-level 근거 |
| Layer 1 NCS nodes | 4,109 | 표준 능력단위 taxonomy 축 |
| Layer 1 PCF nodes | 5,301 | 표준 process taxonomy 축 |
| Layer 2 chunks | 214 | 업무 문서 기반 KG 구축 단위 |
| Evaluation chunks | 120 | LLM 조건별 실험 단위 |
| Final Layer 2 nodes | 179 | 최종 업무 KG node |
| Final Layer 2 edges | 906 | 최종 업무 KG edge |
| Edge evidence coverage | 906 / 906 | 모든 edge가 원문 evidence 보유 |
| Dangling edges | 0 | source/target node 없는 edge 없음 |
| NCS mapping candidates | 110 | Layer 2 업무와 NCS 후보 연결 |
| PCF mapping candidates | 110 | Layer 2 업무와 PCF 후보 연결 |

핵심 산출물:

| 목적 | 파일 |
| --- | --- |
| 최종 Layer 2 nodes | `outputs/07_layer2_graph/layer2_nodes.jsonl` |
| 최종 Layer 2 edges | `outputs/07_layer2_graph/layer2_edges.jsonl` |
| Schema-valid triples | `outputs/06_triples/layer2_triples_schema_valid.jsonl` |
| NCS mapping 후보 | `outputs/08_mapping/l2_ncs_mapping_candidates.jsonl` |
| PCF mapping 후보 | `outputs/08_mapping/l2_pcf_mapping_candidates.jsonl` |
| KG viewer | `outputs/09_visualization/kg_viewer.html` |
| Prompt-node-edge 추적 문서 | `experiments/cape_kg_eacl_20260627/06_release/prompt_node_edge_traceability.md` |

---

## 3. 최종 KG와 LLM output의 관계

교수님께 설명할 때 가장 중요한 구분은 "최종 KG"와 "LLM prediction 실험"이 다르다는 점입니다.

| 구분 | 의미 | 위치 |
| --- | --- | --- |
| 최종 KG | 실제 데이터에 대해 구축된 Layer 2 업무 지식그래프 | `outputs/07_layer2_graph/` |
| LLM 조건별 output | prompt 조건별 후보 생성 결과 | `experiments/cape_kg_eacl_20260627/49_*`, `50_*` |
| 평가/claim 관리 | silver diagnostic, claim gate, human review handoff | `experiments/cape_kg_eacl_20260627/04_evaluation/`, `06_release/` |

핵심 설명 문장:

> 최종 KG는 LLM raw output을 그대로 저장한 것이 아닙니다. OCR evidence anchor, task seed, 용어 사전, procedure template, schema validator를 결합해 rule/schema/evidence 기반으로 조립한 graph입니다. LLM은 baseline, proposed, ablation 조건별 후보 생성 능력을 비교하기 위해 별도로 실행했습니다.

---

## 4. 실제 사용한 Prompt 조건

프롬프트 파일 위치:

`experiments/cape_kg_eacl_20260627/02_schema/prompts/`

아래 표는 파일에 실제 저장된 prompt 원문과 각 조건이 요구한 산출물 형태입니다. 실제 LLM 호출 때는 여기에 chunk sentence, sentence id, allowed schema, JSON shape, strict JSON contract가 runtime에서 결합됩니다.

| 조건 | 실제 prompt 원문 | 산출물 |
| --- | --- | --- |
| `B0_plain_llm` | `Extract subject-predicate-object triples from the chunk. Return JSON only.` | `triples` |
| `B1_predicate_constrained` | `Extract triples using only the allowed predicates. Return JSON only with evidence sentence ids.` | `edges` |
| `B2_current_project` | `Extract Task Frames, then triples, then post-process into the Layer2 schema.` | `nodes`, `edges` |
| `B3_edc_style` | `Extract, define, and canonicalize open-schema KG items, then emit CAPE-compatible nodes and edges for scoring.` | `nodes`, `edges` |
| `B4_taxonomy_rag` | `Retrieve NCS/PCF/task taxonomy snippets, then extract schema-constrained triples with evidence.` | `nodes`, `edges`, `mappings` |
| `B5_procedural_prompt` | `Extract actions, actors, gateways, guard conditions, artifact flows, and temporal/logical dependencies.` | `nodes`, `edges` |
| `B6_sac_kg_verifier_pruner` | `Use existing generator candidates, then apply schema/evidence verification and pruning in the style of SAC-KG. This is a deterministic approximation, not a full SAC-KG reproduction.` | `nodes`, `edges` |
| `P_cape_kg_actual` | `Use CQ-linked schema retrieval, procedural frame extraction, evidence-span constrained relation extraction, span verification, ontology validation, procedural consistency checks, and active review scoring.` | `nodes`, `edges`, `mappings` |
| `P_minus_CQ` | runtime condition only: proposed method에서 CQ anchoring 제거 | `nodes`, `edges`, `mappings` |
| `P_minus_Evidence` | runtime condition only: evidence anchor 요구 약화 | `nodes`, `edges`, `mappings` |
| `P_minus_Procedural_schema` | runtime condition only: procedural schema 대신 flat schema 사용 | `nodes`, `edges`, `mappings` |
| `P_minus_Validator` | runtime condition only: validator rejection 없이 모델 선택 허용 | `nodes`, `edges`, `mappings` |
| `P_minus_Standard_bridge` | runtime condition only: NCS/PCF bridge 출력 제거 | `nodes`, `edges` |
| `P_minus_Schema_retrieval` | `Run CAPE-KG without chunk-specific schema/taxonomy retrieval; keep CQ, evidence grounding, procedural schema, validation, and mapping output shape.` | `nodes`, `edges`, `mappings` |

Strict JSON contract:

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

---

## 5. Runtime Prompt의 공통 구조

파일에 저장된 조건별 prompt만 단독으로 모델에 넣은 것이 아니라, 실제 실행에서는 다음 제약을 함께 붙였습니다.

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

이 공통 구조 때문에 LLM은 다음 조건을 만족해야 했습니다.

| 제약 | 의미 |
| --- | --- |
| JSON only | markdown/설명문 없이 하나의 JSON object만 반환 |
| Evidence required | chunk sentence id 중 하나 이상을 evidence로 첨부 |
| No outside knowledge | 원문에 없는 업무 지식 추가 금지 |
| Korean labels | 원문이 한국어이면 label도 한국어 유지 |
| Schema constrained | 허용 node type과 predicate만 사용 |
| Hard limit | proposed/ablation 조건은 chunk당 최대 5 nodes, 5 edges, 3 mappings |

---

## 6. 제안 방법론 Prompt의 핵심

제안 방법론 조건인 `P_cape_kg_actual`은 단순 triple extraction이 아니라 CQ, schema, evidence, validator, NCS/PCF mapping을 모두 결합한 prompt입니다.

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

요구한 JSON 형태:

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

CQ, 즉 Competency Question은 LLM이 자동으로 만든 질문이 아니라, 연구자가 먼저 정의한 KG 요구사항입니다.

생성 절차:

1. 연구 문제를 정의했습니다.
   - 한국어 수주/제안 업무 문서에서 procedural KG를 구축한다.
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

---

## 8. CQ 실제 목록과 schema 연결

| CQ | 질문 | 연결 predicate/schema |
| --- | --- | --- |
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

교수님께 강조할 문장:

> CQ는 "무엇을 추출할 것인가"와 "나중에 KG가 무엇을 답해야 하는가"를 동시에 정의합니다. 따라서 CQ가 schema, prompt, validation, evaluation을 묶는 anchor 역할을 합니다.

---

## 9. 최종 KG Node 산출 방식

최종 `outputs/07_layer2_graph/layer2_nodes.jsonl`의 node는 LLM이 한 번에 생성한 것이 아니라, evidence와 schema 규칙을 통과한 node입니다.

전체 흐름:

1. OCR sentence를 evidence anchor로 정리
2. task seed, alias, keyword로 업무 단위 후보를 찾음
3. task별 evidence sentence를 모아 canonical task catalog 생성
4. 각 task를 `DomainTask` node로 생성
5. task별 procedure template과 입력/산출물 기반 규칙으로 `ProcedureStep` node 생성
6. artifact, role, decision, guard condition, principle, risk를 용어 매칭/규칙으로 생성
7. node id 기준으로 중복 제거
8. evidence anchor와 review status를 부여

Node type별 생성 규칙:

| Node type | 현재 개수 | 생성 방식 |
| --- | ---: | --- |
| `ProcedureStep` | 99 | task별 procedure template 또는 입력/산출물 기반 step 추론 |
| `DomainTask` | 22 | task seed의 label/alias/keyword로 OCR sentence evidence 검색 |
| `Artifact` | 14 | task evidence 안의 입력물/산출물 용어 매칭 |
| `GuardCondition` | 13 | 의사결정 evidence에서 조건/가능성/경쟁/자원 표현 추출 |
| `Role` | 10 | 수행자/책임 주체 용어 매칭 |
| `ArtifactFlow` | 9 | 특정 산출물이 다음 task 입력으로 쓰이는 규칙에서 생성 |
| `Principle` | 5 | 원칙/품질 기준 용어 매칭 |
| `DecisionGateway` | 4 | 의사결정 관련 용어 매칭 |
| `Risk` | 3 | 위험/불리함/실패 가능성 용어 매칭 |

핵심 설명 문장:

> Node는 "문서에서 등장한 업무 개념"을 KG의 정점으로 만든 것입니다. 각 node는 type을 가지며, 가능한 경우 원문 evidence anchor에 연결됩니다.

---

## 10. 최종 KG Edge 산출 방식

최종 `outputs/07_layer2_graph/layer2_edges.jsonl`의 edge는 node 사이 관계를 predicate별 규칙으로 생성한 뒤 검증을 통과한 결과입니다.

전체 흐름:

1. task frame의 inputs, outputs, roles, principles, risks slot을 확인
2. procedure step의 순서와 소속 task를 확인
3. decision gateway와 guard condition을 연결
4. artifact flow 규칙으로 산출물의 다음 업무 사용 관계를 연결
5. 모든 edge를 triple record로 변환하고 `source_triple_ids` 부여
6. allowed predicate, source/target node 존재, evidence 존재 조건을 검증
7. 통과한 edge만 최종 graph에 저장

Edge predicate별 생성 규칙:

| Predicate | 현재 개수 | 생성 방식 |
| --- | ---: | --- |
| `PRODUCES` | 220 | task/step의 outputs slot을 Artifact node로 연결 |
| `USES_INPUT` | 201 | task/step의 inputs slot을 Artifact 또는 Concept node로 연결 |
| `PERFORMED_BY` | 120 | task/step의 roles slot을 Role node로 연결 |
| `HAS_STEP` | 99 | DomainTask를 해당 ProcedureStep 목록에 연결 |
| `PRECEDES` | 77 | 같은 task 안에서 step order 기준으로 순서 연결 |
| `HAS_PRINCIPLE` | 64 | task/step의 principles slot을 Principle node로 연결 |
| `HAS_DECISION_GATEWAY` | 54 | task/step에서 발견된 의사결정 node 연결 |
| `HAS_RISK` | 39 | task/step의 risks slot을 Risk node로 연결 |
| `HAS_GUARD_CONDITION` | 14 | DecisionGateway에서 추출된 조건 node 연결 |
| `FEEDS_INTO` | 9 | Artifact가 다음 task로 흘러가는 규칙 연결 |
| `USED_AS_INPUT_FOR` | 9 | Artifact가 다음 task 입력으로 사용되는 규칙 연결 |

검증 결과:

| 항목 | 결과 |
| --- | ---: |
| Final Layer 2 edges | 906 |
| Evidence가 있는 edges | 906 / 906 |
| `source_triple_ids`가 있는 edges | 906 / 906 |
| Dangling edges | 0 |

핵심 설명 문장:

> Edge는 "어떤 업무가 어떤 산출물을 만들고, 어떤 입력을 사용하며, 누가 수행하고, 어떤 순서로 이어지는가"를 나타냅니다. 최종 edge가 되려면 source node, target node, 허용 predicate, evidence anchor가 모두 필요합니다.

---

## 11. Triple, Node, Edge의 관계

| 개념 | 의미 | 예시 |
| --- | --- | --- |
| Node | 업무 개념 자체 | `기회분석`, `Capture Plan`, `고객 정보 수집` |
| Edge | node 사이 관계 | `기회분석 USES_INPUT Capture Plan` |
| Triple | edge를 subject-predicate-object와 evidence로 검증하기 위한 중간 표현 | `(subject, predicate, object, evidence_anchor_ids)` |
| Evidence anchor | 해당 node/edge/triple이 근거로 삼은 OCR sentence | sentence id |

중간 산출물 연결:

| 단계 | 파일 | 현재 수량 |
| --- | --- | ---: |
| Task frame | `outputs/04_task_frames/canonical_task_catalog.json` | 22 |
| Procedure structure | `outputs/05_procedure/procedure_structures_clean.jsonl` | 22 procedures / 99 steps |
| Schema-valid triple | `outputs/06_triples/layer2_triples_schema_valid.jsonl` | 906 |
| Final nodes | `outputs/07_layer2_graph/layer2_nodes.jsonl` | 179 |
| Final edges | `outputs/07_layer2_graph/layer2_edges.jsonl` | 906 |

현재 triple 수와 final edge 수가 모두 906인 이유는, edge를 SPO/evidence 형태로 검증한 뒤 최종 graph edge로 저장했기 때문입니다.

---

## 12. LLM 조건별 산출물 수량

Qwen3-8B strict JSON full run 기준 validated output 수량입니다. 이 표는 조건별 prompt가 실제로 어떤 종류의 output을 만들었는지 보여주는 진단표입니다.

| 조건 | Valid rows | Triples | Nodes | Edges | Mappings |
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

해석:

- B0는 schema 없이 자유 triple만 생성합니다.
- B1은 predicate만 제한한 edge 후보를 생성합니다.
- B2-B5는 서로 다른 baseline 방식으로 node/edge 후보를 생성합니다.
- `P_cape_kg_actual`은 CQ, evidence, procedural schema, validator, NCS/PCF bridge를 결합하여 nodes, edges, mappings를 함께 생성합니다.
- 이 수량은 "많이 뽑았다"는 의미이지 성능이 좋다는 의미는 아닙니다.

---

## 13. 지금까지 실행한 실험

| 실험/작업 | 현재 상태 | 설명 |
| --- | --- | --- |
| Layer 1 NCS KG 구축 | 완료 | NCS taxonomy 기반 표준축 구축 |
| Layer 1 PCF KG 구축 | 완료 | PCF taxonomy 기반 표준축 구축 |
| Layer 2 업무 KG 구축 | 완료 | 179 nodes, 906 edges |
| Evidence grounding | 완료 | accepted edge evidence coverage 100% |
| NCS/PCF mapping 후보 생성 | 완료 | 각각 110개 후보 |
| LLM baseline 실행 | 완료 | B0-B6 조건 |
| Proposed CAPE-KG 조건 실행 | 완료 | `P_cape_kg_actual` |
| Ablation 실행 | 완료 | CQ/evidence/schema/validator/bridge/retrieval 제거 조건 |
| Model scaling | 완료 | Qwen3-8B, Qwen3-14B, Qwen3-32B-AWQ |
| Public benchmark adapter | 완료 | PAGED/Text2KG subset 진단 |
| Structural diagnostics | 완료 | ontology conformance, procedural consistency, CQ answerability |
| Human review handoff | 준비 완료 | human-gold/mapping/active-review 반환 대기 |
| Claim gate | expected FAIL | human-gold 미완료로 최종 claim 차단 |

---

## 14. 발표에서 조심해야 할 표현

사용해도 되는 표현:

- "Layer 1 NCS/PCF KG와 Layer 2 업무 KG 구축은 완료했다."
- "Layer 2 업무 KG는 179 nodes, 906 edges이며, accepted edge evidence coverage는 100%이다."
- "제안 방법론은 CQ, schema, evidence, validator, NCS/PCF bridge를 결합한다."
- "LLM 조건별 baseline/proposed/ablation/model-scaling 실험은 실행했다."
- "현재 silver/proxy diagnostic은 완료되었고, 최종 성능 claim은 human-gold 이후 확정한다."

피해야 할 표현:

- "제안 방법론이 최종적으로 baseline보다 우수하다."
- "현재 F1이 논문 main result이다."
- "LLM이 최종 KG를 직접 생성했다."
- "사람 검수 없이 gold evaluation이 끝났다."

정확한 표현:

> 현재 결과는 KG 구축 및 실험 인프라 완료 상태입니다. 최종 논문용 성능표는 human-gold annotation, IAA, adjudication, mapping expert review가 끝난 뒤 확정해야 합니다.

---

## 15. 교수님 보고용 1분 설명문

이번 연구에서는 한국어 수주/제안 업무 문서를 OCR sentence 단위 evidence anchor로 정리한 뒤, task, step, input/output, role, decision, risk를 표현하는 procedural KG를 구축했습니다. Layer 1에는 NCS와 PCF 표준 taxonomy를 두고, Layer 2에는 실제 업무 문서에서 추출한 업무 KG를 구축했습니다. 현재 Layer 2 KG는 179개 node와 906개 edge로 구성되어 있고, 최종 edge는 모두 source/target node와 evidence anchor를 갖습니다.

방법론적으로는 먼저 KG가 답해야 할 12개의 Competency Question을 정의했고, 이를 node type과 predicate schema로 연결했습니다. 이후 LLM 실험에서는 B0-B6 baseline, 제안 방법론 `P_cape_kg_actual`, 그리고 CQ/evidence/schema/validator/standard bridge/retrieval ablation을 실행했습니다. 실제 prompt는 단순히 "그래프를 만들어라"가 아니라, JSON only, evidence required, no outside knowledge, allowed schema, hard limit 조건을 포함했습니다.

다만 최종 KG는 LLM raw output을 그대로 넣은 것이 아니라, OCR evidence anchor, task seed, 용어 사전, procedure template, schema validator를 결합해 조립한 graph입니다. LLM output은 조건별 후보 생성 능력을 비교하는 별도 실험 산출물입니다. 따라서 현재 발표에서는 KG 구축 완료와 실험 인프라 완료를 주장할 수 있지만, 최종 성능 우수성 claim은 human-gold annotation과 adjudication이 끝난 뒤 확정해야 합니다.
