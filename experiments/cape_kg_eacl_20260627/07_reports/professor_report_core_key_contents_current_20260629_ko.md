# 교수님 보고용 핵심 내용 별도 요약본

Generated: 2026-06-29  
Detailed slide draft: `experiments/cape_kg_eacl_20260627/07_reports/professor_report_slide_contents_current_20260628_ko.md`  
Experiment directory: `experiments/cape_kg_eacl_20260627`  
KG output directory: `outputs`

이 문서는 기존 슬라이드별 발표 원고와 별개로, 교수님께 가장 먼저 설명해야 할 핵심만 압축한 별도 파일입니다. 초점은 네 가지입니다.

1. 어떤 방법론을 적용했는가
2. 어떤 프롬프트로 어떤 산출물을 만들었는가
3. CQ를 어떻게 정의했고 node/edge 설계와 어떻게 연결했는가
4. 최종 node와 edge를 각각 어떤 규칙으로 산출했는가

---

## 1. 한 문장 결론

이번 실험은 한국어 수주/제안 업무 OCR 문서를 sentence evidence 단위로 정리한 뒤, `DomainTask`, `ProcedureStep`, `Artifact`, `Role`, `DecisionGateway`, `GuardCondition`, `ReviewCheckpoint`, `Risk` 등을 포함하는 Layer 2 절차형 KG를 구축하고, 이를 NCS/PCF 표준 Layer 1 KG와 후보 매핑한 CAPE-KG 실험입니다.

핵심은 LLM에게 자유롭게 triple을 만들게 한 것이 아니라, **CQ, procedural schema, allowed predicate, evidence anchor, validator, NCS/PCF bridge**로 KG 산출을 통제했다는 점입니다.

---

## 2. 현재 결과 숫자

현재 로컬 산출물 기준 핵심 수량은 다음입니다.

| 항목 | 수량 | 기준 파일 |
| --- | ---: | --- |
| OCR evidence anchors | 5,009 | `outputs/06_triples/evidence_anchors.jsonl` |
| Layer 2 chunks | 214 | `outputs/02_ocr/layer2_chunks.jsonl` |
| LLM evaluation chunks | 120 | `experiments/cape_kg_eacl_20260627/01_data/evaluation_chunks.jsonl` |
| Layer 1 NCS nodes | 4,109 | `outputs/01_layer1/layer1_ncs_nodes.jsonl` |
| Layer 1 PCF nodes | 5,301 | `outputs/01_layer1/layer1_pcf_nodes.jsonl` |
| Canonical DomainTask | 22 | `outputs/04_task_frames/canonical_task_catalog.json` |
| Procedure structures | 22 | `outputs/05_procedure/procedure_structures_clean.jsonl` |
| Procedure steps | 99 | `experiments/cape_kg_eacl_20260627/06_release/prompt_node_edge_traceability.json` |
| Final Layer 2 nodes | 220 | `outputs/07_layer2_graph/layer2_nodes.jsonl` |
| Final Layer 2 edges | 947 | `outputs/07_layer2_graph/layer2_edges.jsonl` |
| Schema-valid triples | 947 | `outputs/06_triples/layer2_triples_schema_valid.jsonl` |
| NCS mapping candidates | 110 | `outputs/08_mapping/l2_ncs_mapping_candidates.jsonl` |
| PCF mapping candidates | 110 | `outputs/08_mapping/l2_pcf_mapping_candidates.jsonl` |
| CQ answerability | 12 / 12 | `experiments/cape_kg_eacl_20260627/04_evaluation/cq_answerability_structural_metrics.json` |

주의할 점은 이 숫자가 **자동 구축 및 구조 진단 결과**라는 점입니다. 최종 논문 성능표의 precision/recall/F1은 human-gold annotation, IAA, adjudication 이후 다시 계산해야 합니다.

---

## 3. 방법론 핵심

CAPE-KG의 처리 흐름은 다음과 같습니다.

1. OCR workbook을 sentence 단위로 정제
2. 각 sentence에 evidence anchor ID 부여
3. NCS/PCF 표준 데이터를 Layer 1 KG로 구축
4. 한국어 업무 문서를 Layer 2 chunk로 분할
5. CQ와 procedural schema 정의
6. task seed, alias, keyword, evidence sentence로 `DomainTask` 생성
7. task별 procedure template과 입력/산출물/역할/조건 단서로 node 생성
8. predicate별 domain/range와 evidence 조건을 만족하는 edge만 생성
9. 동일 120개 evaluation chunk에 대해 LLM baseline/proposed/ablation 조건 실행
10. human review handoff와 claim gate로 최종 claim 가능 범위 통제

교수님께 설명할 때 가장 중요한 구분은 다음입니다.

| 구분 | 의미 | 현재 상태 |
| --- | --- | --- |
| 최종 KG | 실제 데이터에 대해 구축된 Layer 2 업무 KG | 구축 완료 |
| LLM output | prompt 조건별 후보 JSON prediction | 실행 완료 |
| 최종 성능 claim | human-gold 기준 성능표 | 아직 불가 |

즉, **KG 구축과 LLM 진단 실험은 완료되었지만, CAPE-KG가 baseline보다 최종적으로 우수하다는 논문 claim은 아직 하면 안 됩니다.**

---

## 4. 실제 프롬프트 조건과 산출물

실제 프롬프트 파일 위치는 다음입니다.

`experiments/cape_kg_eacl_20260627/02_schema/prompts/`

아래 표는 저장된 실제 prompt text와 요구 산출물입니다. 실제 LLM 호출 시에는 여기에 chunk sentence, sentence ID, allowed node type, allowed predicate, JSON shape, strict JSON contract가 결합됩니다.

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

추가 ablation은 파일이 아니라 runtime condition으로 만들어졌습니다.

| 조건 | 제거한 요소 | 산출물 |
| --- | --- | --- |
| `P_minus_CQ` | CQ anchoring 제거 | `nodes`, `edges`, `mappings` |
| `P_minus_Evidence` | evidence anchor 요구 약화 | `nodes`, `edges`, `mappings` |
| `P_minus_Procedural_schema` | 절차형 schema 제거 | `nodes`, `edges`, `mappings` |
| `P_minus_Validator` | validator rejection 제거 | `nodes`, `edges`, `mappings` |
| `P_minus_Standard_bridge` | NCS/PCF bridge 제거 | `nodes`, `edges` |

---

## 5. Runtime prompt의 공통 제약

프롬프트 파일의 한 줄 문장만 모델에 넣은 것이 아닙니다. 실제 실행에서는 모든 조건에 다음 제약이 결합되었습니다.

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

Qwen 계열 strict JSON 실행에서는 다음 contract도 추가했습니다.

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

## 6. 제안 방법론 prompt의 핵심

`P_cape_kg_actual`은 본 연구의 proposed condition입니다. 실제 runtime prompt의 핵심 구조는 다음과 같습니다.

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

이 prompt가 요구하는 JSON shape는 다음입니다.

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

## 7. CQ는 어떻게 만들었는가

CQ는 LLM이 자동 생성한 질문이 아닙니다. 연구자가 먼저 "이 KG가 답해야 하는 업무 질문"을 정하고, 각 질문을 schema node type과 edge predicate에 연결했습니다.

CQ 생성 방식은 다음입니다.

1. 연구 문제를 "한국어 수주/제안 업무 문서에서 절차형 KG 구축"으로 정의
2. 업무자가 실제로 물을 질문 범주를 task, step, input/output, role, decision, guard, artifact flow, evidence, NCS/PCF mapping으로 분해
3. 각 질문을 필요한 node type과 predicate에 연결
4. 같은 CQ 목록을 schema, prompt, ablation, structural evaluation에서 재사용

CQ source files:

| 역할 | 파일 |
| --- | --- |
| EACL 실험용 CQ | `experiments/cape_kg_eacl_20260627/02_schema/competency_questions.json` |
| 내부 KG build용 CQ | `outputs/03_schema/competency_questions.json` |
| CQ query pack | `experiments/cape_kg_eacl_20260627/06_release/cq_query_pack.md` |
| runtime prompt builder | `scripts/run_cape_llm_condition_baselines.py` |

---

## 8. 실제 CQ 목록과 설계 영향

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

CQ가 node/edge 설계에 미친 영향은 다음과 같습니다.

| CQ | 설계 영향 |
| --- | --- |
| CQ1 | `DomainTask`, `ProcedureStep`, `HAS_STEP`, `PRECEDES`가 필요해짐 |
| CQ2, CQ3 | `Artifact`, `USES_INPUT`, `PRODUCES`가 필요해짐 |
| CQ4 | `Role`, `PERFORMED_BY`가 필요해짐 |
| CQ5, CQ6 | `DecisionGateway`, `GuardCondition`을 별도 node로 둠 |
| CQ7 | `ArtifactFlow`, `FEEDS_INTO`, `USED_AS_INPUT_FOR`로 산출물 흐름 표현 |
| CQ8 | `ReviewCheckpoint`, `HAS_REVIEW_CHECKPOINT`로 리뷰 절차 표현 |
| CQ10 | 모든 accepted node/edge에 evidence anchor 요구 |
| CQ11, CQ12 | NCS/PCF mapping 후보를 별도 산출 |

---

## 9. 최종 KG node는 어떻게 산출했는가

최종 Layer 2 node는 220개이며, 모두 evidence anchor를 보유합니다.

| node type | count | 생성 방식 |
| --- | ---: | --- |
| `ProcedureStep` | 99 | task별 procedure template 또는 입력/산출물 기반 step 추론으로 생성 |
| `ReviewCheckpoint` | 41 | 검토/리뷰/점검/승인/확인 신호가 있는 step에서 별도 checkpoint node로 투영 |
| `DomainTask` | 22 | task seed의 label/alias/keyword로 OCR sentence evidence를 검색해 생성 |
| `Artifact` | 14 | task evidence 안의 입력물/산출물 용어 매칭으로 생성 |
| `GuardCondition` | 13 | 의사결정 evidence에서 조건/가능성/경쟁/자원 표현을 추출 |
| `Role` | 10 | 수행자/책임 주체 용어 매칭으로 생성 |
| `ArtifactFlow` | 9 | 특정 산출물이 다음 task 입력으로 쓰이는 규칙에서 생성 |
| `Principle` | 5 | 원칙/품질 기준 용어 매칭으로 생성 |
| `DecisionGateway` | 4 | 의사결정 관련 용어 매칭으로 생성 |
| `Risk` | 3 | 위험/불리함/실패 가능성 용어 매칭으로 생성 |

핵심 설명 문장:

> Node는 LLM raw output을 그대로 채택한 것이 아니라, task seed, keyword/alias, procedure template, evidence sentence, schema type을 조합해 canonical node로 만든 것입니다.

---

## 10. 최종 KG edge는 어떻게 산출했는가

최종 Layer 2 edge는 947개이며, 모두 evidence anchor와 source triple ID를 보유합니다. dangling edge는 0개입니다.

| predicate | count | 생성 방식 |
| --- | ---: | --- |
| `PRODUCES` | 220 | task/step의 outputs slot을 `Artifact` node로 연결 |
| `USES_INPUT` | 201 | task/step의 inputs slot을 `Artifact` 또는 관련 node로 연결 |
| `PERFORMED_BY` | 120 | task/step의 roles slot을 `Role` node로 연결 |
| `HAS_STEP` | 99 | `DomainTask`를 해당 `ProcedureStep` 목록에 연결 |
| `PRECEDES` | 77 | 같은 task 안에서 step order 기준으로 순서 연결 |
| `HAS_PRINCIPLE` | 64 | task/step의 principles slot을 `Principle` node로 연결 |
| `HAS_DECISION_GATEWAY` | 54 | task/step에서 발견된 의사결정 node를 연결 |
| `HAS_REVIEW_CHECKPOINT` | 41 | 검토/리뷰/점검/승인/확인 신호가 있는 step을 checkpoint node로 연결 |
| `HAS_RISK` | 39 | task/step의 risks slot을 `Risk` node로 연결 |
| `HAS_GUARD_CONDITION` | 14 | `DecisionGateway`에서 추출된 조건 node를 연결 |
| `FEEDS_INTO` | 9 | 산출물이 다음 task로 흘러가는 규칙을 연결 |
| `USED_AS_INPUT_FOR` | 9 | 산출물이 다음 task 입력으로 사용되는 규칙을 연결 |

핵심 설명 문장:

> Edge는 subject-predicate-object만 있는 단순 triple이 아니라, predicate별 domain/range, evidence anchor, source triple ID, review status를 함께 가진 검증 가능한 KG relation입니다.

---

## 11. LLM 조건별 산출량

아래 표는 Qwen3-8B strict JSON full run 및 SAC-KG-style baseline valid output 기준입니다. 이는 성능표가 아니라, 조건별 JSON 산출량과 traceability를 보여주는 표입니다.

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

해석:

- `B0`은 일반 triple만 산출합니다.
- `B1`은 predicate만 제한하므로 edge는 많지만 node 구조가 약합니다.
- `B2-B5`는 baseline 계열입니다.
- `P_cape_kg_actual`은 CQ, evidence, schema, validator, NCS/PCF bridge를 모두 포함한 제안 조건입니다.
- `P_minus_*`는 제안 조건에서 특정 구성요소를 제거한 ablation입니다.

---

## 12. 발표에서 안전하게 말할 수 있는 것과 아직 말하면 안 되는 것

| 구분 | 말해도 되는 표현 | 아직 말하면 안 되는 표현 |
| --- | --- | --- |
| KG 구축 | Layer 1/Layer 2 KG와 evidence-grounded relation을 구축했다 | 사람이 검수한 정답 KG가 완성됐다 |
| CQ | 12개 CQ가 현재 KG에서 구조적으로 answerable하다 | CQ 답변의 의미적 정답성이 human-gold로 증명됐다 |
| LLM 실험 | B0-B6, proposed, ablation, Qwen3 계열 진단을 실행했다 | proposed가 human-gold 기준으로 baseline보다 최종 우수하다 |
| mapping | NCS/PCF 후보 110개씩 생성했다 | expert review 기준 최종 mapping 성능이 확정됐다 |
| paper table | claim-safe traceability 및 structural table은 있다 | 최종 main performance table이 확정됐다 |

교수님 보고용 한 문장:

> 현재까지는 한국어 수주/제안 업무 문서에 대해 evidence-grounded procedural KG 구축, CQ 기반 schema 설계, LLM 조건별 진단, NCS/PCF 후보 매핑, human-review handoff까지 완료했고, 최종 성능 claim은 human-gold annotation과 expert review 이후 확정하는 단계입니다.

---

## 13. 바로 확인할 핵심 파일

| 목적 | 파일 |
| --- | --- |
| 상세 슬라이드 원고 | `experiments/cape_kg_eacl_20260627/07_reports/professor_report_slide_contents_current_20260628_ko.md` |
| prompt/node/edge traceability | `experiments/cape_kg_eacl_20260627/06_release/prompt_node_edge_traceability.md` |
| CQ query pack | `experiments/cape_kg_eacl_20260627/06_release/cq_query_pack.md` |
| final build report | `outputs/10_evaluation/final_build_report.md` |
| Layer 2 nodes | `outputs/07_layer2_graph/layer2_nodes.jsonl` |
| Layer 2 edges | `outputs/07_layer2_graph/layer2_edges.jsonl` |
| NCS mapping candidates | `outputs/08_mapping/l2_ncs_mapping_candidates.jsonl` |
| PCF mapping candidates | `outputs/08_mapping/l2_pcf_mapping_candidates.jsonl` |
| KG viewer | `outputs/09_visualization/kg_viewer.html` |
