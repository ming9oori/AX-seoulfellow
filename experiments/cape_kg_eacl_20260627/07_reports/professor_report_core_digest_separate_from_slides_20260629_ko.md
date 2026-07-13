# 교수님 보고용 핵심 요약본

Generated: 2026-06-29  
분리 대상 원고: `experiments/cape_kg_eacl_20260627/07_reports/professor_report_slide_contents_current_20260628_ko.md`  
Traceability source: `experiments/cape_kg_eacl_20260627/06_release/prompt_node_edge_traceability.md`  
Experiment directory: `experiments/cape_kg_eacl_20260627`  
KG output directory: `outputs`

이 문서는 긴 슬라이드별 원고와 별개로, 교수님께 먼저 보고해야 할 핵심만 압축한 별도 파일입니다. 초점은 다음 네 가지입니다.

1. 어떤 연구 방법론으로 저의 데이터에 KG를 구축했는가
2. 실제 어떤 프롬프트로 어떤 산출물을 만들었는가
3. CQ를 어떻게 만들었고 node/edge 설계에 어떻게 연결했는가
4. 현재까지 어떤 결과가 나왔고, 무엇은 아직 주장하면 안 되는가

---

## 1. 한 문장 결론

본 연구는 한국어 수주/제안 업무 문서에서 업무 절차, 입력/산출물, 수행 역할, 의사결정, 조건, 위험, 원문 근거를 함께 표현하는 **evidence-grounded procedural KG**를 구축하고, 이를 NCS/PCF 표준 taxonomy와 후보 매핑하는 CAPE-KG 실험입니다.

가장 중요한 구분은 다음입니다.

| 구분 | 의미 |
| --- | --- |
| 최종 KG 구축 | OCR evidence, CQ, schema, task seed, procedure template, validator로 rule/schema/evidence 기반 graph를 조립한 결과 |
| LLM 실험 | 동일 chunk에서 baseline/proposed/ablation/model-scaling 조건이 어떤 JSON 후보를 생성하는지 비교한 실험 |
| 최종 논문 성능 | human-gold annotation, IAA, adjudication, expert review 이후에만 claim 가능한 성능 |

따라서 현재 발표에서는 **KG 구축과 실험 인프라는 완료**, **human-gold 기반 최종 성능 우수성 claim은 아직 미완료**라고 분리해서 설명해야 합니다.

---

## 2. 현재까지의 핵심 수치

| 항목 | 값 | 의미 |
| --- | ---: | --- |
| OCR clean sentences / evidence anchors | 5,009 | node/edge 근거 문장 단위 |
| Layer 2 chunks | 214 | 현재 corpus 기반 업무 KG 구축 단위 |
| LLM evaluation chunks | 120 | baseline/proposed/ablation 비교 대상 |
| Layer 1 NCS nodes | 4,109 | NCS 표준 taxonomy 축 |
| Layer 1 PCF nodes | 5,301 | PCF 표준 taxonomy 축 |
| Final Layer 2 nodes | 179 | 최종 업무 KG node |
| Final Layer 2 edges | 906 | 최종 업무 KG edge |
| Canonical DomainTask | 22 | 수주/제안 업무 단위 |
| NCS mapping candidates | 110 | 22 tasks x Top-5 후보 |
| PCF mapping candidates | 110 | 22 tasks x Top-5 후보 |
| Evidence-missing Layer 2 edges | 0 | 최종 edge는 모두 evidence anchor 보유 |
| Dangling edges | 0 | 존재하지 않는 node를 가리키는 edge 없음 |
| Domain/range type violations | 0 | schema 구조 위반 없음 |
| CQ answerability | 11 / 12 | CQ8 review checkpoint는 구조적 gap으로 분리 관리 |
| Pre-human handoff validation | 76 PASS / 1 WARN / 0 FAIL | 사람 검수 전 handoff 인프라 준비 완료 |
| Claim gate | FAIL | human-gold와 expert review 미완료 때문에 의도적으로 final claim 차단 |

핵심 파일:

| 목적 | 파일 |
| --- | --- |
| 최종 Layer 2 nodes | `outputs/07_layer2_graph/layer2_nodes.jsonl` |
| 최종 Layer 2 edges | `outputs/07_layer2_graph/layer2_edges.jsonl` |
| Schema-valid triples | `outputs/06_triples/layer2_triples_schema_valid.jsonl` |
| Evidence index | `outputs/07_layer2_graph/layer2_evidence_index.jsonl` |
| NCS mapping 후보 | `outputs/08_mapping/l2_ncs_mapping_candidates.jsonl` |
| PCF mapping 후보 | `outputs/08_mapping/l2_pcf_mapping_candidates.jsonl` |
| KG viewer | `outputs/09_visualization/kg_viewer.html` |
| Build report | `outputs/10_evaluation/final_build_report.md` |
| Prompt/node/edge 추적 | `experiments/cape_kg_eacl_20260627/06_release/prompt_node_edge_traceability.md` |
| Claim 가능성 표 | `experiments/cape_kg_eacl_20260627/06_release/claimable_main_table.md` |

---

## 3. 방법론 핵심 구조

CAPE-KG는 LLM에게 자유롭게 graph를 만들게 하는 방식이 아닙니다. 다음 요소를 결합해서 KG 생성을 통제했습니다.

| 구성 요소 | 역할 |
| --- | --- |
| Competency Questions | KG가 답해야 할 업무 질문을 먼저 정의 |
| Procedural schema | `DomainTask`, `ProcedureStep`, `Artifact`, `Role`, `DecisionGateway`, `GuardCondition` 등으로 업무 구조화 |
| Evidence grounding | 모든 accepted node/edge/mapping을 원문 sentence evidence에 연결 |
| Allowed node/edge schema | 사용할 node type과 predicate를 제한 |
| Validator | JSON parse, evidence ID, predicate, domain/range, type 오류 점검 |
| Standard bridge | Layer 2 업무 KG를 NCS/PCF 표준 taxonomy와 연결 |
| Human-review gate | 사람 검수 전 최종 성능 claim을 막는 안전장치 |

전체 흐름:

1. OCR workbook을 sentence 단위로 정제
2. 각 sentence에 evidence anchor ID 부여
3. NCS/PCF 표준 데이터를 Layer 1 KG로 구축
4. 업무 문서를 Layer 2 chunk로 분할
5. CQ와 procedural schema 정의
6. task seed, alias, keyword, evidence sentence로 `DomainTask` 생성
7. procedure template과 입력/산출물/역할/조건 단서로 node 생성
8. predicate별 규칙과 evidence 조건을 만족하는 edge 생성
9. Layer 2 KG를 NCS/PCF Top-K 후보와 연결
10. LLM baseline/proposed/ablation/model-scaling 조건 실행
11. human review handoff, claim gate, release validation 생성

---

## 4. CQ는 어떻게 만들었는가

CQ, 즉 Competency Question은 LLM이 자동 생성한 질문이 아니라, 연구자가 먼저 정의한 **KG 요구사항**입니다.

CQ 생성 절차:

| 단계 | 내용 |
| --- | --- |
| 1 | 연구 문제를 "한국어 수주/제안 업무 문서 기반 procedural KG construction"으로 정의 |
| 2 | 업무 사용자가 실제로 물을 질문 범주를 정리 |
| 3 | 각 질문을 필요한 node type과 predicate에 연결 |
| 4 | 같은 CQ를 schema, prompt, ablation, structural evaluation에서 재사용 |

실제 CQ 목록:

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

CQ가 KG 설계에 미친 영향:

| CQ | 설계 영향 |
| --- | --- |
| CQ1 | `DomainTask`, `ProcedureStep`, `HAS_STEP`, `PRECEDES` 필요 |
| CQ2, CQ3 | `Artifact`, `USES_INPUT`, `PRODUCES` 필요 |
| CQ4 | `Role`, `PERFORMED_BY` 필요 |
| CQ5, CQ6 | `DecisionGateway`, `GuardCondition`, `HAS_DECISION_GATEWAY`, `HAS_GUARD_CONDITION` 필요 |
| CQ7 | 산출물 흐름을 표현하는 `FEEDS_INTO`, `USED_AS_INPUT_FOR` 필요 |
| CQ10 | 모든 accepted item에 evidence anchor 필요 |
| CQ11, CQ12 | NCS/PCF mapping 후보 생성 필요 |

주의: 현재 canonical Layer 2 graph에서는 CQ8의 `ReviewCheckpoint`/`HAS_REVIEW_CHECKPOINT`가 아직 구조적 gap입니다. 대신 review-checkpoint 후보 45개와 gateway branch gap 4개를 별도 worklist로 만들어 human structural review 대상으로 분리했습니다.

---

## 5. 실제 사용한 프롬프트와 산출물

프롬프트 파일 위치:

`experiments/cape_kg_eacl_20260627/02_schema/prompts/`

조건별 prompt 파일의 핵심 지시문:

| 조건 | 실제 prompt 원문 | 요구 산출물 |
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

Runtime에서 추가된 ablation 조건:

| 조건 | 제거하거나 약화한 요소 | 산출물 |
| --- | --- | --- |
| `P_minus_CQ` | CQ anchoring 제거 | `nodes`, `edges`, `mappings` |
| `P_minus_Evidence` | evidence anchor 요구 약화 | `nodes`, `edges`, `mappings` |
| `P_minus_Procedural_schema` | procedural schema 대신 flat schema 사용 | `nodes`, `edges`, `mappings` |
| `P_minus_Validator` | validator rejection 없이 모델의 schema 선택 허용 | `nodes`, `edges`, `mappings` |
| `P_minus_Standard_bridge` | NCS/PCF bridge 출력 제거 | `nodes`, `edges` |

실제 LLM 호출 때는 위 prompt에 chunk sentence, sentence ID, allowed schema, JSON shape, strict JSON contract가 결합되었습니다.

공통 runtime prompt 제약:

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

---

## 6. 제안 방법론 `P_cape_kg_actual`

`P_cape_kg_actual`은 본 연구의 제안 조건입니다. 핵심은 하나의 좋은 prompt가 아니라, CQ, schema retrieval, procedural schema, evidence grounding, validator, NCS/PCF bridge를 함께 결합했다는 점입니다.

핵심 instruction:

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

요구 JSON shape:

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

## 7. Node는 어떻게 산출했는가

최종 node 파일:

`outputs/07_layer2_graph/layer2_nodes.jsonl`

최종 node는 LLM raw output을 그대로 저장한 것이 아닙니다. OCR sentence evidence, task seed, alias/keyword, 용어 사전, procedure template, schema constraint를 이용해 조립했습니다.

Node 생성 흐름:

1. OCR sentence를 `EA-*` evidence anchor로 변환
2. `TASK_SEEDS`의 label, alias, keyword로 관련 sentence 검색
3. sentence 안에서 artifact, role, decision, principle, risk 후보 추출
4. 관련 evidence가 있는 업무를 `DomainTask` node로 생성
5. task별 procedure template 또는 입력/산출물 단서로 `ProcedureStep` node 생성
6. decision keyword가 있으면 `DecisionGateway` 생성
7. 조건 표현이 있으면 `GuardCondition` 생성
8. 수행자 표현은 `Role`, 산출물/입력물 표현은 `Artifact`로 정규화
9. 산출물이 다음 task 입력으로 이어지는 경우 `ArtifactFlow` 생성
10. 각 node에 evidence anchor와 raw metadata를 부착

최종 node type 분포:

| node type | count | 생성 방식 |
| --- | ---: | --- |
| `ProcedureStep` | 99 | task별 procedure template 또는 입력/산출물 기반 step 추론 |
| `DomainTask` | 22 | task seed label/alias/keyword와 OCR evidence 매칭 |
| `Artifact` | 14 | task evidence 안의 입력물/산출물 용어 매칭 |
| `GuardCondition` | 13 | 의사결정 evidence에서 조건/가능성/경쟁/자원 표현 추출 |
| `Role` | 10 | 수행자/책임 주체 용어 매칭 |
| `ArtifactFlow` | 9 | 산출물이 다음 task 입력으로 이어지는 규칙 |
| `Principle` | 5 | 원칙/품질 기준 용어 매칭 |
| `DecisionGateway` | 4 | Bid/No Bid, pursuit, validation, approval 등 의사결정 단서 |
| `Risk` | 3 | 위험/불리함/실패 가능성 표현 매칭 |

---

## 8. Edge는 어떻게 산출했는가

최종 edge 파일:

`outputs/07_layer2_graph/layer2_edges.jsonl`

Edge 생성 원칙:

1. 모든 edge는 source node와 target node가 실제로 존재해야 함
2. predicate는 schema의 allowed predicate만 허용
3. predicate별 domain/range type을 만족해야 함
4. evidence anchor가 없는 edge는 accepted final graph에 넣지 않음
5. 중간 triple 또는 procedure structure와 연결되는 `source_triple_ids`를 유지
6. dangling edge, type violation, evidence missing edge를 validator에서 차단

최종 edge predicate 분포:

| predicate | count | 생성 방식 |
| --- | ---: | --- |
| `PRODUCES` | 220 | task/step의 outputs slot을 `Artifact` node로 연결 |
| `USES_INPUT` | 201 | task/step의 inputs slot을 `Artifact` 등으로 연결 |
| `PERFORMED_BY` | 120 | task/step의 roles slot을 `Role` node로 연결 |
| `HAS_STEP` | 99 | `DomainTask`를 해당 `ProcedureStep` 목록에 연결 |
| `PRECEDES` | 77 | 같은 task 안에서 step order 기준으로 순서 연결 |
| `HAS_PRINCIPLE` | 64 | task/step의 principles slot을 `Principle` node로 연결 |
| `HAS_DECISION_GATEWAY` | 54 | task/step에서 발견된 의사결정 node를 연결 |
| `HAS_RISK` | 39 | task/step의 risks slot을 `Risk` node로 연결 |
| `HAS_GUARD_CONDITION` | 14 | `DecisionGateway`에서 추출된 조건 node를 연결 |
| `FEEDS_INTO` | 9 | artifact가 다음 task로 흘러가는 규칙을 연결 |
| `USED_AS_INPUT_FOR` | 9 | artifact가 다음 task 입력으로 사용되는 규칙을 연결 |

현재 구조 검증 결과:

| 검증 항목 | 결과 |
| --- | ---: |
| Final Layer 2 edges | 906 |
| Evidence-covered edges | 906 / 906 |
| Dangling edges | 0 |
| Domain/range violations | 0 |
| Unknown predicates | 0 |
| Ontology conformance rate | 1.0 |
| Procedural consistency rate | 0.995043 |

---

## 9. LLM 조건별 validated output 수량

아래 표는 성능표가 아니라, 조건별 LLM output이 정상 JSON으로 생성되어 어떤 key를 얼마나 산출했는지 보여주는 traceability 표입니다.

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

추가 model scaling diagnostic도 실행했습니다.

| 모델 | 현재 해석 |
| --- | --- |
| Qwen3-8B | 주된 full condition 비교 기준 |
| Qwen3-14B | proposed-method silver diagnostic 실행 |
| Qwen3-32B-AWQ | proposed-method silver diagnostic 실행 |

단, 이 model scaling 결과도 human-gold 성능이 아니라 silver/proxy diagnostic입니다.

---

## 10. 현재까지 실행한 실험과 산출물

| 실험/산출물 | 현재 상태 | claim scope |
| --- | --- | --- |
| Layer 1 NCS KG 구축 | 완료 | 구축 결과로 보고 가능 |
| Layer 1 PCF KG 구축 | 완료 | 구축 결과로 보고 가능 |
| Layer 2 procedural KG 구축 | 완료 | 구축 결과로 보고 가능 |
| Evidence grounding | 완료 | 구조 검증 결과로 보고 가능 |
| NCS/PCF mapping 후보 | 완료 | 후보 생성까지만 보고 가능, expert review 전 |
| NCS-PCF crosswalk 후보 | 완료 | 후보 생성까지만 보고 가능, expert review 전 |
| LLM baseline/proposed/ablation | 완료 | generation coverage와 diagnostic으로 보고 가능 |
| Qwen3 model scaling | 완료 | silver/proxy diagnostic으로만 보고 가능 |
| Public benchmark adapter | 완료 | 보조 일반화 evidence로 보고 가능 |
| Structural diagnostics | 완료 | CQ8 gap과 review worklist 포함 |
| Human review handoff | 준비 완료 | 사람 검수 시작 가능 |
| Human-gold final scoring | 미완료 | final performance claim 불가 |

---

## 11. 교수님께 설명할 때의 안전한 표현

사용 가능한 표현:

- "저의 데이터에 대해 NCS/PCF Layer 1 KG와 수주/제안 업무 Layer 2 KG 구축은 완료했습니다."
- "최종 Layer 2 KG는 179개 node와 906개 edge로 구성되며, 모든 accepted edge는 sentence-level evidence anchor를 가집니다."
- "LLM은 최종 KG를 그대로 생성한 것이 아니라, baseline/proposed/ablation 조건의 후보 생성 실험에 사용했습니다."
- "제안 방법론은 CQ, procedural schema, evidence grounding, validator, NCS/PCF bridge를 결합한 방식입니다."
- "현재 main result table은 claimable/pending/diagnostic을 구분해 만들었고, human-gold final 성능표는 사람 검수 후 확정해야 합니다."

피해야 할 표현:

- "CAPE-KG가 기존 방법보다 성능이 높다는 최종 결론이 나왔다."
- "human-gold 기준 F1이 확정되었다."
- "NCS/PCF mapping이 정답으로 확정되었다."
- "active review가 실제 사람 검수 시간을 줄였다고 입증되었다."
- "CQ8 review checkpoint 구조가 완전히 해결되었다."

---

## 12. 앞으로 바로 해야 할 일

| 우선순위 | 작업 | 이유 |
| --- | --- | --- |
| 1 | human-gold annotation A/B 반환 | final precision/recall/F1 계산의 필수 조건 |
| 2 | IAA 계산 및 adjudication | 논문용 gold label 확정 |
| 3 | NCS/PCF mapping expert review | 표준 taxonomy 연결 claim 확정 |
| 4 | NCS-PCF crosswalk expert review | crosswalk utility/ranking claim 확정 |
| 5 | active-review human effort return | active review 효율성 claim 확정 |
| 6 | CQ8 structural review | review checkpoint/gateway branch gap 보완 |
| 7 | post-annotation refresh 실행 | final main table, paper table, release bundle 갱신 |

핵심 결론:

> 지금까지의 연구는 KG 구축, LLM 조건별 실험, 구조 검증, human-review handoff까지 완료된 상태입니다. 다만 논문에서 최종 성능 우수성을 주장하려면 사람 검수 기반 gold label과 expert review가 반드시 들어와야 합니다.
