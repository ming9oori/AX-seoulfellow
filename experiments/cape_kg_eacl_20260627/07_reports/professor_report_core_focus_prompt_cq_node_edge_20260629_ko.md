# 교수님 보고용 별도 핵심 요약: Prompt, CQ, Node/Edge 산출 방식

Generated: 2026-06-29  
Related detailed slide draft: `experiments/cape_kg_eacl_20260627/07_reports/professor_report_slide_contents_current_20260628_ko.md`  
Traceability source: `experiments/cape_kg_eacl_20260627/06_release/prompt_node_edge_traceability.md`  
Experiment directory: `experiments/cape_kg_eacl_20260627`  
KG output directory: `outputs`

이 문서는 기존 슬라이드 원고와 별개로, 교수님께 핵심만 빠르게 보고하기 위한 별도 요약본입니다. 초점은 다음 네 가지입니다.

1. 어떤 prompt 조건을 사용했는가
2. CQ를 어떻게 만들었고 어떤 예시가 있는가
3. 최종 KG node를 어떻게 산출했는가
4. 최종 KG edge를 어떻게 산출했는가

---

## 1. 한 문장 결론

이번 실험은 한국어 수주/제안 업무 문서에서 task, step, input/output, role, decision, risk를 evidence-grounded procedural KG로 구축하고, 이를 NCS/PCF 표준 taxonomy와 연결하는 CAPE-KG 방법론을 적용한 것입니다.

가장 중요한 해석은 다음입니다.

> KG 구축 자체는 완료되었지만, 최종 성능 claim은 아직 human-gold annotation, IAA, adjudication, mapping expert review, NCS-PCF crosswalk expert review, active-review effort evidence 이후에만 가능합니다.

---

## 2. 현재까지 완성된 산출물

| 항목 | 현재 결과 | 해석 |
| --- | ---: | --- |
| OCR clean sentences | 5,009 | KG evidence anchor의 원천 문장 |
| Evidence anchors | 5,009 | node/edge가 참조하는 sentence-level 근거 |
| Layer 1 NCS nodes | 4,109 | 표준 능력단위 taxonomy 축 |
| Layer 1 PCF nodes | 5,301 | 표준 process classification 축 |
| Layer 2 chunks | 214 | 업무 문서를 KG 구축 단위로 분할 |
| Evaluation chunks | 120 | LLM 실험 및 평가용 chunk |
| Final Layer 2 nodes | 179 | 최종 업무 KG node |
| Final Layer 2 edges | 906 | 최종 업무 KG edge |
| Edge evidence coverage | 906 / 906 | 모든 edge가 evidence anchor 보유 |
| Dangling edges | 0 | source/target node가 없는 edge 없음 |
| NCS mapping candidates | 110 | Layer 2 업무와 NCS 후보 연결 |
| PCF mapping candidates | 110 | Layer 2 업무와 PCF 후보 연결 |

핵심 파일은 다음입니다.

| 목적 | 파일 |
| --- | --- |
| 최종 Layer 2 node | `outputs/07_layer2_graph/layer2_nodes.jsonl` |
| 최종 Layer 2 edge | `outputs/07_layer2_graph/layer2_edges.jsonl` |
| NCS mapping 후보 | `outputs/08_mapping/l2_ncs_mapping_candidates.jsonl` |
| PCF mapping 후보 | `outputs/08_mapping/l2_pcf_mapping_candidates.jsonl` |
| KG viewer | `outputs/09_visualization/kg_viewer.html` |
| prompt/node/edge 추적 문서 | `experiments/cape_kg_eacl_20260627/06_release/prompt_node_edge_traceability.md` |
| claim 가능성 표 | `experiments/cape_kg_eacl_20260627/06_release/claimable_main_table.md` |

---

## 3. 최종 KG와 LLM 실험의 관계

교수님께 설명할 때 가장 중요한 구분은 최종 KG와 LLM prediction을 분리하는 것입니다.

| 구분 | 의미 | 위치 |
| --- | --- | --- |
| 최종 KG | 실제 데이터에 대해 구축된 업무 지식그래프 | `outputs/07_layer2_graph/` |
| LLM 조건별 output | prompt 조건별 후보 산출물 | `experiments/cape_kg_eacl_20260627/49_*`, `50_*` |
| 평가/claim 문서 | silver diagnostic, claim gate, human review handoff | `experiments/cape_kg_eacl_20260627/04_evaluation/`, `06_release/` |

핵심 표현:

> 최종 KG는 LLM raw output을 그대로 저장한 것이 아닙니다. OCR evidence anchor, task seed, 용어 사전, procedure template, schema validator를 결합해 rule/schema/evidence 기반으로 조립한 graph입니다. LLM은 baseline, proposed, ablation 조건별 후보 생성 능력을 비교하기 위해 별도로 실행했습니다.

---

## 4. 사용한 실제 Prompt 조건

프롬프트 파일 위치:

`experiments/cape_kg_eacl_20260627/02_schema/prompts/`

아래 표는 파일에 실제 저장된 prompt 원문과 각 조건의 산출물 형태입니다. 실제 LLM 호출 때는 이 원문에 chunk sentence, sentence id, allowed schema, JSON shape, strict JSON contract가 runtime에서 결합됩니다.

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
| `P_minus_Schema_retrieval` | `Run CAPE-KG without chunk-specific schema/taxonomy retrieval; keep CQ, evidence grounding, procedural schema, validation, and mapping output shape.` | `nodes`, `edges`, `mappings` |
| `strict_json_contract` | JSON object만 반환, markdown/code fence/comment/XML/`<think>`/설명 금지, `/no_think`, compact JSON 사용 | 출력 형식 안정화 |

---

## 5. Runtime Prompt의 공통 구조

조건별 prompt만 단독으로 모델에 넣은 것이 아니라, 모든 실행에서 공통 제약을 함께 붙였습니다.

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

Strict JSON 실행에서는 system/user prompt에 다음 제약을 추가했습니다.

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

## 6. 제안 방법론 Prompt의 핵심

제안 방법론 조건인 `P_cape_kg_actual`은 단순 triple extraction이 아니라 CQ, schema, evidence, validator, NCS/PCF mapping을 함께 요구합니다.

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

요구한 JSON 형태는 다음입니다.

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

CQ, 즉 Competency Question은 LLM이 자동 생성한 것이 아니라 연구자가 정의한 KG 요구사항입니다.

생성 절차는 다음과 같습니다.

1. 연구 문제를 먼저 정했습니다.
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

## 8. CQ 실제 목록

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

교수님께 강조할 포인트:

> CQ는 "무엇을 추출할 것인가"와 "나중에 KG가 무엇을 답해야 하는가"를 동시에 정의합니다. 따라서 CQ가 schema, prompt, validation, evaluation을 묶는 anchor 역할을 합니다.

---

## 9. Node는 어떻게 산출했는가

최종 node 파일:

`outputs/07_layer2_graph/layer2_nodes.jsonl`

핵심 설명:

> 최종 node는 LLM에게 "node를 뽑아줘"라고 해서 나온 raw output이 아닙니다. OCR evidence, task seed, keyword/alias matching, 용어 사전, procedure template, schema 규칙으로 만든 KG node입니다.

생성 절차:

1. OCR workbook에서 sentence-level evidence anchor를 만들었습니다.
2. 수주/제안 업무와 관련된 task seed, alias, keyword를 정의했습니다.
3. 각 task seed가 실제 OCR sentence에서 지지되는지 검색했습니다.
4. evidence가 확인된 업무 단위를 `DomainTask` node로 만들었습니다.
5. task별 procedure template과 입력/산출물 구조를 이용해 `ProcedureStep` node를 만들었습니다.
6. 문서 안의 입력물, 산출물, 역할, 의사결정, 원칙, 위험 표현을 매칭해 `Artifact`, `Role`, `DecisionGateway`, `GuardCondition`, `Principle`, `Risk` node를 만들었습니다.
7. 특정 산출물이 다음 업무의 입력으로 쓰이는 경우 `ArtifactFlow` node를 만들었습니다.
8. 모든 node에 evidence anchor와 review status를 붙였습니다.

Node type별 결과:

| node type | count | 생성 방식 |
| --- | ---: | --- |
| `ProcedureStep` | 99 | task별 procedure template 또는 입력/산출물 기반 step 추론 |
| `DomainTask` | 22 | task seed의 label/alias/keyword가 OCR evidence에서 확인될 때 생성 |
| `Artifact` | 14 | 입력물/산출물 용어 매칭 |
| `GuardCondition` | 13 | 의사결정 evidence에서 조건/가능성/경쟁/자원 표현 추출 |
| `Role` | 10 | 수행자/책임 주체 용어 매칭 |
| `ArtifactFlow` | 9 | 산출물이 다음 task 입력으로 쓰이는 규칙 |
| `Principle` | 5 | 원칙/품질 기준 용어 매칭 |
| `DecisionGateway` | 4 | 의사결정 관련 용어 매칭 |
| `Risk` | 3 | 위험/불리함/실패 가능성 용어 매칭 |

검증 결과:

| 항목 | 값 |
| --- | ---: |
| Final Layer 2 nodes | 179 |
| Evidence가 있는 nodes | 179 / 179 |

---

## 10. Edge는 어떻게 산출했는가

최종 edge 파일:

`outputs/07_layer2_graph/layer2_edges.jsonl`

핵심 설명:

> Edge는 node 사이의 업무 관계입니다. 최종 graph에 들어가려면 source node와 target node가 실제로 존재해야 하고, predicate가 허용 목록에 있어야 하며, 원문 evidence anchor가 있어야 합니다.

생성 절차:

1. task frame의 `inputs`, `outputs`, `roles`, `principles`, `risks` slot을 edge predicate로 변환했습니다.
2. DomainTask와 ProcedureStep을 `HAS_STEP`으로 연결했습니다.
3. 같은 task 안의 step 순서를 `PRECEDES`로 연결했습니다.
4. task/step과 decision node를 `HAS_DECISION_GATEWAY`로 연결했습니다.
5. decision node와 조건 node를 `HAS_GUARD_CONDITION`으로 연결했습니다.
6. 산출물이 다음 task의 입력으로 쓰이는 경우 `FEEDS_INTO`, `USED_AS_INPUT_FOR`로 연결했습니다.
7. 모든 edge를 triple record로 변환하고 `source_triple_ids`를 부여했습니다.
8. predicate 허용 목록, source/target node 존재, evidence 존재 조건을 통과한 edge만 저장했습니다.

Predicate별 결과:

| predicate | count | 생성 방식 |
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

| 항목 | 값 |
| --- | ---: |
| Final Layer 2 edges | 906 |
| Evidence가 있는 edges | 906 / 906 |
| `source_triple_ids`가 있는 edges | 906 / 906 |
| Dangling edges | 0 |

---

## 11. LLM 조건별 산출물 수량

아래 표는 성능 우수성 표가 아니라, prompt 조건별로 어떤 형태의 JSON 산출물이 생성되었는지를 보여주는 산출량 진단표입니다.

| 조건 | valid rows | triples | nodes | edges | mappings |
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

- `B0`는 schema 없이 triple만 생성합니다.
- `B1`은 predicate만 제한했기 때문에 edge는 나오지만 node schema 구조가 약합니다.
- `B4`와 `P_cape_kg_actual`은 NCS/PCF mapping까지 생성합니다.
- `P_minus_Standard_bridge`에서 mapping이 0인 것은 의도된 ablation입니다.
- 이 수량표는 final performance table이 아닙니다. 최종 precision/recall/F1은 human-gold 이후 확정해야 합니다.

---

## 12. 교수님께 바로 설명할 핵심 답변

| 예상 질문 | 답변 |
| --- | --- |
| KG 구축은 완료되었는가? | 네. Layer 1 NCS/PCF KG와 Layer 2 업무 KG는 구축 완료입니다. |
| Layer 2 KG는 LLM raw output인가? | 아닙니다. evidence, task seed, schema, procedure template, validator 기반으로 조립한 최종 graph입니다. |
| LLM은 사용했는가? | 네. Qwen3 계열 모델로 baseline/proposed/ablation/model-scaling 실험을 수행했습니다. |
| 어떤 prompt를 사용했는가? | B0-B6 baseline, `P_cape_kg_actual`, `P_minus_*` ablation 조건을 사용했습니다. |
| CQ는 누가 만들었는가? | LLM 생성이 아니라 연구자가 설계한 KG 요구 질문입니다. |
| node는 어떻게 만들었는가? | task seed, evidence matching, 용어 사전, procedure template으로 만들고 evidence를 붙였습니다. |
| edge는 어떻게 만들었는가? | task frame slot과 procedure order를 predicate로 변환하고 source/target/evidence 검증을 통과시켰습니다. |
| main table은 나왔는가? | claimability table과 diagnostic table은 있습니다. 최종 performance main table은 human-gold 이후 확정합니다. |

---

## 13. 현재 claim 가능한 것과 아직 claim하면 안 되는 것

| 구분 | 현재 상태 |
| --- | --- |
| Claim 가능 | KG 구축 완료, evidence coverage, ontology/procedural structural diagnostics, prompt/ablation/model-scaling 실행, human-review handoff 준비 |
| Diagnostic으로만 사용 | silver/proxy F1, actual LLM silver evaluation, public benchmark adapter 결과 |
| 아직 claim 불가 | final human-gold precision/recall/F1, IAA, adjudicated gold 기반 proposed 성능, mapping expert review 기반 downstream 성능, NCS-PCF crosswalk utility/accept-rate, active-review human-effort 절감 효과 |

현재 claim gate가 FAIL인 이유:

> 자동 실험이 실패해서가 아니라, 사람이 검수한 gold annotation과 expert review가 아직 들어오지 않았기 때문입니다. 따라서 현재 FAIL은 expected fail입니다.

---

## 14. 다음 작업

최종 논문 성능표를 만들려면 다음 순서가 필요합니다.

1. annotator A/B가 full 120 priority batch를 검수합니다.
2. annotator 간 IAA를 계산합니다.
3. disagreement를 adjudication합니다.
4. adjudicated human-gold 기준으로 node/edge/evidence F1을 재계산합니다.
5. mapping expert review를 반영합니다.
6. NCS-PCF crosswalk expert review를 반영합니다.
7. active-review human effort sheet를 반환받아 검수 효율 claim을 계산합니다.
8. final performance main table을 확정합니다.

반환 파일이 준비되면 다음 wrapper로 refresh합니다.

```bash
PYTHON_BIN=/home/minjoo/tdpo2_aaai2027/.venv_tdpo2/bin/python \
LLM_PYTHON=/home/minjoo/tdpo2_aaai2027/.venv_tdpo2/bin/python \
APPLY_IMPORTS=1 \
bash scripts/run_cape_human_return_apply.sh
```

---

## 15. 발표용 최종 요약 문장

> 본 연구는 한국어 수주/제안 업무 문서에서 업무 절차, 입력/산출물, 역할, 의사결정, 위험을 sentence-level evidence에 grounding하여 Layer 2 procedural KG로 구축하고, 이를 NCS/PCF 표준 taxonomy와 연결하는 CAPE-KG 방법론을 적용한 것입니다. 현재 KG 구축과 LLM baseline/ablation/model-scaling, structural diagnostics, human-review handoff는 완료되었으며, 최종 성능 claim은 human-gold annotation과 expert review 이후 확정할 예정입니다.
