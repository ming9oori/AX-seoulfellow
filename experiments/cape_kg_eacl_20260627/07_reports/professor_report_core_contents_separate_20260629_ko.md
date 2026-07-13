# 교수님 보고용 별도 핵심 정리본

Generated: 2026-06-29  
Detailed slide draft: `experiments/cape_kg_eacl_20260627/07_reports/professor_report_slide_contents_current_20260628_ko.md`  
Experiment directory: `experiments/cape_kg_eacl_20260627`  
KG output directory: `outputs`

이 문서는 기존 슬라이드별 발표 원고와 별개로, 교수님께 먼저 설명해야 할 핵심만 정리한 보고용 파일입니다. 초점은 다음 네 가지입니다.

1. 저의 데이터에 어떤 방법론을 적용했는가
2. 실제 어떤 prompt 조건으로 어떤 JSON 산출물을 만들었는가
3. CQ를 어떻게 만들었고 node/edge schema와 어떻게 연결했는가
4. 최종 node와 edge를 각각 어떤 규칙으로 산출했는가

---

## 1. 한 문장 결론

이번 실험은 한국어 수주/제안 업무 문서에서 OCR sentence evidence를 기준으로 `DomainTask`, `ProcedureStep`, `Artifact`, `Role`, `DecisionGateway`, `GuardCondition`, `ReviewCheckpoint`, `Risk` 등을 추출해 Layer 2 procedural KG를 구축하고, 이를 NCS/PCF 표준 Layer 1 KG와 후보 매핑하는 CAPE-KG 방법론을 적용한 것입니다.

교수님께 가장 먼저 구분해서 설명해야 할 점은 다음입니다.

| 구분 | 현재 상태 | 보고 표현 |
| --- | --- | --- |
| KG 구축 | 완료 | Layer 1 표준 KG와 Layer 2 업무 KG 구축 완료 |
| Evidence grounding | 완료 | 최종 Layer 2 edge 947개 모두 evidence 보유 |
| LLM 조건별 실험 | 실행 완료 | baseline, proposed, ablation, model scaling 실행 |
| 최종 성능 claim | 아직 불가 | human-gold annotation, IAA, adjudication, expert review 이후 확정 |

즉, 현재 상태는 "KG 구축과 실험 인프라는 완료되었고, 논문용 최종 성능표는 사람 검수 후 확정해야 하는 단계"입니다.

---

## 2. 현재 핵심 결과

| 항목 | 결과 | 의미 |
| --- | ---: | --- |
| OCR clean sentences | 5,009 | sentence-level evidence의 원천 |
| Evidence anchors | 5,009 | node/edge가 참조하는 근거 ID |
| Layer 2 chunks | 214 | 전체 업무 문서 기반 KG 구축 단위 |
| LLM evaluation chunks | 120 | prompt 조건별 LLM 실험 단위 |
| Layer 1 NCS nodes | 4,109 | NCS 표준 taxonomy 축 |
| Layer 1 PCF nodes | 5,301 | PCF 표준 taxonomy 축 |
| Final Layer 2 nodes | 220 | 최종 업무 KG node |
| Final Layer 2 edges | 947 | 최종 업무 KG edge |
| Schema-valid triples | 947 | schema 검증을 통과한 SPO/evidence 중간 표현 |
| Node evidence coverage | 220 / 220 | 최종 node가 모두 evidence 보유 |
| Edge evidence coverage | 947 / 947 | 최종 edge가 모두 evidence 보유 |
| Dangling edges | 0 | source/target node 없는 edge 없음 |
| Type violations | 0 | domain/range/schema 위반 없음 |
| NCS mapping candidates | 110 | Layer 2 업무와 NCS 후보 연결 |
| PCF mapping candidates | 110 | Layer 2 업무와 PCF 후보 연결 |
| CQ answerability | 12 / 12 | 현재 KG로 12개 CQ 모두 구조적으로 질의 가능 |

핵심 파일은 다음입니다.

| 목적 | 파일 |
| --- | --- |
| 최종 Layer 2 nodes | `outputs/07_layer2_graph/layer2_nodes.jsonl` |
| 최종 Layer 2 edges | `outputs/07_layer2_graph/layer2_edges.jsonl` |
| Schema-valid triples | `outputs/06_triples/layer2_triples_schema_valid.jsonl` |
| Evidence anchors | `outputs/06_triples/evidence_anchors.jsonl` |
| NCS mapping 후보 | `outputs/08_mapping/l2_ncs_mapping_candidates.jsonl` |
| PCF mapping 후보 | `outputs/08_mapping/l2_pcf_mapping_candidates.jsonl` |
| KG viewer | `outputs/09_visualization/kg_viewer.html` |
| Prompt-node-edge 추적 | `experiments/cape_kg_eacl_20260627/06_release/prompt_node_edge_traceability.md` |
| CQ query pack | `experiments/cape_kg_eacl_20260627/06_release/cq_query_pack.md` |
| Claim gate | `experiments/cape_kg_eacl_20260627/06_release/claim_gate_report.md` |

---

## 3. 방법론 핵심

CAPE-KG는 LLM에게 자유롭게 triple을 만들게 하는 방식이 아닙니다. CQ, schema, evidence, validator, standard bridge를 결합해 KG 생성을 통제했습니다.

| 구성 요소 | 역할 |
| --- | --- |
| Competency Questions | KG가 답해야 할 업무 질문을 먼저 정의 |
| Procedural schema | 업무 지식을 task, step, artifact, role, decision, risk 등으로 구조화 |
| Evidence grounding | node/edge/mapping이 원문 sentence evidence에 연결되도록 강제 |
| Allowed node/edge schema | 사용할 node type과 predicate를 제한 |
| Validator | JSON parse, evidence ID, predicate, type, domain/range 오류 점검 |
| Standard bridge | Layer 2 업무 KG를 NCS/PCF 표준 taxonomy와 연결 |
| Human-review gate | 사람 검수 전에는 최종 성능 claim을 막는 안전장치 |

실행 흐름은 다음입니다.

1. OCR workbook을 sentence 단위로 정제
2. 각 sentence에 evidence anchor ID 부여
3. NCS/PCF 표준 데이터를 Layer 1 KG로 구축
4. 한국어 업무 문서를 Layer 2 chunk로 분할
5. CQ와 procedural schema 정의
6. task seed, alias, keyword, evidence sentence로 DomainTask 생성
7. task별 template과 입력/산출물/역할/조건 단서로 node 생성
8. predicate별 규칙과 evidence 조건을 만족하는 edge만 생성
9. LLM baseline/proposed/ablation/model-scaling 조건 실행
10. human review handoff와 claim gate 생성

---

## 4. 최종 KG와 LLM output의 관계

교수님께 반드시 분리해서 설명해야 할 부분입니다.

| 구분 | 의미 | 위치 |
| --- | --- | --- |
| 최종 KG | 실제 데이터에 대해 구축된 Layer 2 업무 지식그래프 | `outputs/07_layer2_graph/` |
| LLM output | prompt 조건별 후보 JSON 생성 결과 | `experiments/cape_kg_eacl_20260627/49_*`, `50_*` |
| 평가/claim 관리 | silver diagnostic, claim gate, human review handoff | `experiments/cape_kg_eacl_20260627/04_evaluation/`, `06_release/` |

핵심 설명 문장:

> 최종 KG는 LLM raw output을 그대로 저장한 결과가 아닙니다. OCR evidence anchor, task seed, 용어 사전, procedure template, schema validator를 결합해 rule/schema/evidence 기반으로 조립한 graph입니다. LLM은 baseline, proposed, ablation 조건별 후보 생성 능력을 비교하기 위해 별도로 실행했습니다.

---

## 5. CQ는 어떻게 만들었는가

CQ, 즉 Competency Question은 LLM이 자동 생성한 질문이 아닙니다. 연구자가 먼저 "이 KG가 어떤 업무 질문에 답해야 하는가"를 정한 ontology requirement입니다.

생성 절차는 다음과 같습니다.

| 단계 | 내용 |
| --- | --- |
| 1 | 연구 문제를 "한국어 수주/제안 업무 문서에서 절차형 KG 구축"으로 정의 |
| 2 | 업무자가 실제로 물을 질문 범주를 task, step, input/output, role, decision, evidence, standard mapping으로 분해 |
| 3 | 각 질문을 node type과 predicate로 연결 |
| 4 | 같은 CQ를 schema, prompt, ablation, structural evaluation에서 재사용 |

관련 파일:

| 역할 | 파일 |
| --- | --- |
| EACL 실험용 CQ | `experiments/cape_kg_eacl_20260627/02_schema/competency_questions.json` |
| 내부 KG build용 CQ | `outputs/03_schema/competency_questions.json` |
| CQ query pack | `experiments/cape_kg_eacl_20260627/06_release/cq_query_pack.md` |
| CQ/schema 생성 코드 | `scripts/build_ax_epak_internal_kg.py`, `scripts/build_cape_kg_eacl_experiment.py` |
| runtime prompt 조립 코드 | `scripts/run_cape_llm_condition_baselines.py` |

---

## 6. 실제 CQ 목록

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

CQ가 KG 설계에 미친 영향:

| CQ | 설계 영향 |
| --- | --- |
| CQ2, CQ3 | `Artifact`, `USES_INPUT`, `PRODUCES`가 필요해짐 |
| CQ5, CQ6 | `DecisionGateway`, `GuardCondition`을 별도 node로 둠 |
| CQ7 | `FEEDS_INTO`, `USED_AS_INPUT_FOR`로 산출물 흐름 표현 |
| CQ8 | `ReviewCheckpoint`, `HAS_REVIEW_CHECKPOINT`를 추가해 리뷰 절차 표현 |
| CQ10 | 모든 accepted item에 evidence anchor 요구 |
| CQ11, CQ12 | NCS/PCF mapping 후보를 산출하도록 설계 |

---

## 7. 실제 prompt 조건과 산출물

프롬프트 파일 위치:

`experiments/cape_kg_eacl_20260627/02_schema/prompts/`

아래 표는 파일에 저장된 실제 prompt 원문과 요구 산출물입니다. 실제 LLM 호출 때는 여기에 runtime template, chunk sentence, sentence id, allowed schema, JSON shape, strict JSON contract가 결합됩니다.

| 조건 | 실제 prompt text | 요구 산출물 |
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

추가 ablation 조건은 제안 방법론에서 특정 구성요소를 제거한 runtime condition입니다.

| 조건 | 제거한 요소 | 산출물 |
| --- | --- | --- |
| `P_minus_CQ` | CQ anchoring 제거 | `nodes`, `edges`, `mappings` |
| `P_minus_Evidence` | evidence anchor 요구 약화 | `nodes`, `edges`, `mappings` |
| `P_minus_Procedural_schema` | 절차형 schema 제거 | `nodes`, `edges`, `mappings` |
| `P_minus_Validator` | validator rejection 제거 | `nodes`, `edges`, `mappings` |
| `P_minus_Standard_bridge` | NCS/PCF bridge 제거 | `nodes`, `edges` |

---

## 8. Runtime prompt 공통 구조

프롬프트 파일의 한 줄 지시문만 모델에 넣은 것이 아닙니다. 실제 실행에서는 다음 공통 구조가 함께 붙었습니다.

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

Qwen strict JSON 실행에서는 다음 contract도 붙였습니다.

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

## 9. 제안 방법론 prompt의 핵심

`P_cape_kg_actual`은 본 연구의 제안 조건입니다. 핵심은 CQ, schema, evidence, validator, NCS/PCF bridge를 동시에 요구했다는 점입니다.

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

요구 JSON 형태:

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

## 10. LLM 조건별 valid output 수량

아래 수량은 human-gold 성능이 아니라, 각 prompt 조건이 120개 evaluation chunk에서 생성한 valid JSON output 규모입니다.

| condition | family | valid rows | triples | nodes | edges | mappings |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `B0_plain_llm` | baseline | 120 | 1,037 | 0 | 0 | 0 |
| `B1_predicate_constrained` | baseline | 120 | 0 | 0 | 805 | 0 |
| `B2_current_project` | baseline | 120 | 0 | 867 | 334 | 0 |
| `B3_edc_style` | baseline | 120 | 0 | 769 | 263 | 0 |
| `B4_taxonomy_rag` | baseline | 120 | 0 | 719 | 323 | 126 |
| `B5_procedural_prompt` | baseline | 120 | 0 | 1,307 | 302 | 0 |
| `B6_sac_kg_verifier_pruner` | baseline | 120 | 0 | 2,281 | 361 | 107 |
| `P_cape_kg_actual` | proposed | 120 | 0 | 576 | 373 | 227 |
| `P_minus_CQ` | ablation | 120 | 0 | 586 | 391 | 233 |
| `P_minus_Evidence` | ablation | 120 | 0 | 574 | 383 | 227 |
| `P_minus_Procedural_schema` | ablation | 120 | 0 | 558 | 353 | 212 |
| `P_minus_Schema_retrieval` | ablation | 120 | 0 | 568 | 417 | 216 |
| `P_minus_Standard_bridge` | ablation | 120 | 0 | 577 | 405 | 0 |
| `P_minus_Validator` | ablation | 120 | 0 | 570 | 375 | 229 |

사용한 주요 LLM 실행:

| 범주 | 실행 내용 |
| --- | --- |
| 기본 조건 | Qwen3-8B strict JSON 조건에서 120 evaluation chunks 실행 |
| 더 큰 모델 | Qwen3-14B core conditions, Qwen3-32B-AWQ core conditions 실행 |
| public adapter | PAGED/Text2KG subset 및 full adapter 진단 실행 |

---

## 11. 최종 node는 어떻게 산출했는가

최종 Layer 2 node 수는 220개입니다.

| node type | count | 생성 규칙 |
| --- | ---: | --- |
| `ProcedureStep` | 99 | task별 procedure template 또는 입력/산출물 기반 step 추론으로 생성 |
| `ReviewCheckpoint` | 41 | 검토/리뷰/점검/승인/확인 신호가 있는 ProcedureStep에서 별도 checkpoint node로 투영 |
| `DomainTask` | 22 | `TASK_SEEDS`의 label/alias/keyword로 OCR sentence evidence를 검색해 생성 |
| `Artifact` | 14 | task evidence 안의 입력물/산출물 용어 매칭으로 생성 |
| `GuardCondition` | 13 | 의사결정 evidence에서 조건/가능성/경쟁/자원 등 조건 표현을 정규식으로 추출 |
| `Role` | 10 | 수행자/책임 주체 용어 매칭으로 생성 |
| `ArtifactFlow` | 9 | 특정 산출물이 다음 task 입력으로 쓰이는 규칙에서 생성 |
| `Principle` | 5 | 원칙/품질 기준 용어 매칭으로 생성 |
| `DecisionGateway` | 4 | 의사결정 관련 용어 매칭으로 생성 |
| `Risk` | 3 | 위험/불리함/실패 가능성 용어 매칭으로 생성 |

중요한 점:

| 항목 | 설명 |
| --- | --- |
| node label | 한국어 업무 용어를 중심으로 canonical label 생성 |
| node type | procedural schema의 허용 type 중 하나로 제한 |
| evidence | 모든 최종 node가 evidence anchor를 보유 |
| review status | 자동 생성/검증 상태를 기록하고, 최종 claim은 human review 이후 확정 |

---

## 12. 최종 edge는 어떻게 산출했는가

최종 Layer 2 edge 수는 947개입니다.

| predicate | count | 생성 규칙 |
| --- | ---: | --- |
| `PRODUCES` | 220 | task/step의 outputs slot을 Artifact node로 연결 |
| `USES_INPUT` | 201 | task/step의 inputs slot을 Artifact 또는 Concept node로 연결 |
| `PERFORMED_BY` | 120 | task/step의 roles slot을 Role node로 연결 |
| `HAS_STEP` | 99 | DomainTask를 해당 ProcedureStep 목록에 연결 |
| `PRECEDES` | 77 | 같은 task 안에서 step order 기준으로 순서 연결 |
| `HAS_PRINCIPLE` | 64 | task/step의 principles slot을 Principle node로 연결 |
| `HAS_DECISION_GATEWAY` | 54 | task/step에서 발견된 의사결정 node를 연결 |
| `HAS_REVIEW_CHECKPOINT` | 41 | 검토/리뷰/점검/승인/확인 신호가 있는 ProcedureStep을 ReviewCheckpoint node로 연결 |
| `HAS_RISK` | 39 | task/step의 risks slot을 Risk node로 연결 |
| `HAS_GUARD_CONDITION` | 14 | DecisionGateway에서 추출된 조건 node를 연결 |
| `FEEDS_INTO` | 9 | Artifact가 다음 task로 흘러가는 규칙을 연결 |
| `USED_AS_INPUT_FOR` | 9 | Artifact가 다음 task 입력으로 사용되는 규칙을 연결 |

edge acceptance 조건:

| 조건 | 의미 | 현재 결과 |
| --- | --- | --- |
| source node 존재 | edge의 출발 node가 최종 node 목록에 있어야 함 | dangling edges 0 |
| target node 존재 | edge의 도착 node가 최종 node 목록에 있어야 함 | dangling edges 0 |
| predicate 허용 | schema에 정의된 predicate만 사용 | type violations 0 |
| domain/range 부합 | predicate별 source/target type 제약 만족 | type violations 0 |
| evidence 보유 | edge마다 evidence anchor 필요 | 947 / 947 |
| source triple 연결 | 최종 edge가 중간 triple provenance를 가짐 | 947 / 947 |

---

## 13. NCS/PCF mapping은 무엇을 산출했는가

Layer 2 업무 KG를 외부 표준 taxonomy와 연결하기 위해 후보 매핑을 만들었습니다.

| mapping | 수량 | 의미 |
| --- | ---: | --- |
| Layer 2 to NCS candidates | 110 | 22개 canonical task 각각에 NCS Top-K 후보 제공 |
| Layer 2 to PCF candidates | 110 | 22개 canonical task 각각에 PCF Top-K 후보 제공 |
| NCS-PCF crosswalk candidates | 220 | 동일 Layer 2 task를 매개로 NCS와 PCF 연결 후보 생성 |

주의할 점:

| 항목 | 설명 |
| --- | --- |
| 현재 상태 | 후보 추천까지 완료 |
| 아직 필요한 것 | domain expert review |
| 논문 표현 | "candidate mapping generated"는 가능하지만, "mapping 정확도 검증 완료"는 아직 불가 |

---

## 14. 현재 claim gate 상태

Claim gate는 FAIL입니다. 이는 실험 실패가 아니라, 사람 검수 전에는 최종 성능 claim을 못 하게 막는 보수적 장치입니다.

| gate | 상태 | 설명 |
| --- | --- | --- |
| evaluation chunks >= 100 | PASS | 120 chunks |
| actual LLM baselines | PASS | B0/B1/B2 full generation 존재 |
| proposed generation | PASS | `P_cape_kg_actual` 120 rows 존재 |
| ablations | PASS | 6개 full ablation 존재 |
| public subset | PASS | PAGED/Text2KG adapter 진단 존재 |
| release artifacts | PASS | schema, prompts, evaluation, reproducibility artifact 존재 |
| human-gold completed chunks | FAIL | 현재 0 completed chunks |
| human-gold item count | FAIL | 현재 0 human-gold items |
| IAA | FAIL | two-annotator agreement 미계산 |
| proposed human-gold score | FAIL | adjudicated human gold 기준 scoring 전 |
| mapping expert review | FAIL | NCS/PCF mapping expert review 전 |
| crosswalk expert review | FAIL | NCS-PCF crosswalk expert review 전 |

교수님께 보고할 표현:

> 자동 KG 구축, prompt 조건별 LLM 실험, 구조 검증, release/handoff 준비는 완료되었습니다. 다만 논문에서 성능 우수성을 주장하려면 human-gold annotation, IAA, adjudication, mapping expert review가 필요합니다.

---

## 15. 발표에서 강조할 핵심 메시지

| 메시지 | 설명 |
| --- | --- |
| 연구 문제 | 한국어 장문 업무 문서에서 evidence-grounded procedural KG를 구축하는 문제 |
| 방법론 차별점 | CQ anchoring, procedural schema, evidence grounding, validator, NCS/PCF bridge 결합 |
| LLM의 역할 | 최종 KG를 그대로 만든 것이 아니라, prompt 조건별 후보 생성과 비교 실험에 사용 |
| 현재 성과 | Layer 1 KG, Layer 2 KG, mapping 후보, LLM baselines/ablations/model scaling, CQ query pack, Neo4j/HTML viewer 완료 |
| 남은 일 | human-gold annotation, IAA, adjudication, expert review 후 final main table 확정 |

---

## 16. 한 장 보고용 요약

| 질문 | 답 |
| --- | --- |
| 무엇을 만들었나? | 한국어 수주/제안 업무 문서 기반 evidence-grounded procedural KG |
| 어떤 방법론인가? | CQ, schema, evidence, validator, standard bridge를 결합한 CAPE-KG |
| node는 어떻게 만들었나? | task seed, procedure template, 용어/조건/역할/산출물 evidence 매칭으로 생성 |
| edge는 어떻게 만들었나? | predicate별 source/target type, evidence, provenance 조건을 만족하는 관계만 채택 |
| LLM은 썼나? | 썼음. baseline/proposed/ablation/model-scaling 조건에서 후보 JSON 생성 실험 수행 |
| 최종 KG는 LLM raw output인가? | 아님. rule/schema/evidence 기반 조립 graph이며 LLM output은 별도 실험 결과 |
| 현재 main table은 완성됐나? | 자동/silver diagnostic table은 있으나 논문용 final main table은 human-gold 후 확정 |
| 다음 단계는? | 사람 검수, IAA, adjudication, expert review, final metric recomputation |

