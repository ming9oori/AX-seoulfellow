# CAPE-KG 교수님 보고용 핵심 브리프

Generated: 2026-06-28  
Related detailed slide draft: `experiments/cape_kg_eacl_20260627/07_reports/professor_report_slide_contents_current_20260628_ko.md`  
Traceability source: `experiments/cape_kg_eacl_20260627/06_release/prompt_node_edge_traceability.md`

이 문서는 상세 슬라이드 원고와 별개로, 교수님께 핵심만 빠르게 보고하기 위한 압축본입니다. 특히 다음 질문에 바로 답할 수 있도록 정리했습니다.

- 어떤 연구 방법론을 적용했는가?
- 어떤 prompt로 어떤 산출물을 만들었는가?
- CQ는 어떻게 만들었고 어떤 예시가 있는가?
- node와 edge는 각각 어떤 방식으로 산출했는가?
- 현재까지 어디까지 완료되었고, 무엇은 아직 claim하면 안 되는가?

---

## 1. 가장 중요한 결론

현재 연구는 한국어 수주/제안 업무 문서에서 **evidence-grounded procedural KG**를 구축하고, 이를 **NCS/PCF 표준 taxonomy**와 연결하는 CAPE-KG 방법론으로 정리되었습니다.

핵심은 다음입니다.

| 구분 | 현재 상태 |
|---|---|
| Layer 1 NCS/PCF KG | 구축 완료 |
| Layer 2 업무 KG | 구축 완료 |
| Evidence grounding | final node/edge 기준 완료 |
| LLM baseline/proposed/ablation | 120 evaluation chunks 기준 실행 완료 |
| NCS/PCF mapping 후보 | 생성 완료 |
| Neo4j/RDF/SHACL/HTML 시각화 산출물 | 생성 완료 |
| Human-gold annotation/IAA/adjudication | 미완료 |
| 최종 논문 main performance table | 아직 확정 불가 |

중요한 표현:

> 최종 Layer 2 KG는 LLM raw output을 그대로 저장한 결과가 아니라, OCR evidence anchor, task seed, 용어 사전, procedure template, schema validator를 결합해 만든 rule/schema/evidence 기반 graph입니다. LLM은 baseline/proposed/ablation 후보 생성 실험에 사용했습니다.

---

## 2. 현재 구축된 주요 수치

| 항목 | 값 | 의미 |
|---|---:|---|
| OCR clean sentences | 5,009 | 원문 업무 문서 sentence evidence |
| Layer 2 chunks | 214 | 전체 Layer 2 구축 단위 |
| Evaluation chunks | 120 | LLM 비교 실험 subset |
| Layer 1 NCS nodes | 4,109 | NCS taxonomy node |
| Layer 1 PCF nodes | 5,301 | PCF taxonomy node |
| Layer 2 final nodes | 179 | 최종 업무 KG node |
| Layer 2 final edges | 906 | 최종 업무 KG edge |
| NCS mapping candidates | 110 | Layer 2 task와 NCS 후보 |
| PCF mapping candidates | 110 | Layer 2 task와 PCF 후보 |

검증 상태:

| 검증 항목 | 결과 |
|---|---|
| Final nodes with evidence | 179 / 179 |
| Final edges with evidence | 906 / 906 |
| Final edges with source triples | 906 / 906 |
| Dangling edges | 0 |
| Prompt/CQ/node-edge traceability | PASS, 14 conditions / 12 CQs / 1,680 valid rows synchronized |
| Pre-human handoff validation | PASS; current check count: see `../06_release/pre_human_handoff_validation.md` |
| Claim gate | FAIL, human-gold/IAA/adjudication 미완료 때문 |

---

## 3. 전체 방법론 흐름

```text
OCR sentence
-> evidence anchor
-> task seed / keyword matching
-> procedural frame construction
-> node generation
-> edge/triple generation
-> schema/evidence validation
-> Layer 2 KG assembly
-> NCS/PCF standard bridge
-> LLM baseline/proposed/ablation comparison
-> human review handoff
```

방법론 구성 요소:

| 요소 | 역할 |
|---|---|
| CQ | KG가 답해야 할 질문을 먼저 정의 |
| Procedural schema | task, step, artifact, role, decision, risk 구조화 |
| Evidence grounding | node/edge를 OCR sentence evidence에 연결 |
| Validator | predicate, domain/range, evidence, JSON 형식 점검 |
| Standard bridge | Layer 2 업무 KG를 NCS/PCF와 연결 |
| Human review handoff | 최종 논문 claim을 위한 사람 검수 패키지 |

---

## 4. 어떤 prompt로 무엇을 산출했는가

LLM 실험은 baseline, proposed, ablation으로 구성했습니다. Prompt 파일은 `experiments/cape_kg_eacl_20260627/02_schema/prompts/`에 있습니다.

| condition | 목적 | 산출 key |
|---|---|---|
| `B0_plain_llm` | schema 없는 일반 triple extraction | `triples` |
| `B1_predicate_constrained` | 허용 predicate만 사용하는 extraction | `edges` |
| `B2_current_project` | 기존 task frame/triple 방식 baseline | `nodes`, `edges` |
| `B3_edc_style` | extract-define-canonicalize 스타일 baseline | `nodes`, `edges` |
| `B4_taxonomy_rag` | NCS/PCF/task taxonomy retrieval baseline | `nodes`, `edges`, `mappings` |
| `B5_procedural_prompt` | action/actor/gateway/artifact flow 중심 baseline | `nodes`, `edges` |
| `B6_sac_kg_verifier_pruner` | SAC-KG-style verifier/pruner approximation | `nodes`, `edges` |
| `P_cape_kg_actual` | 제안 방법론 | `nodes`, `edges`, `mappings` |
| `P_minus_CQ` | CQ anchoring 제거 ablation | `nodes`, `edges`, `mappings` |
| `P_minus_Evidence` | evidence anchor 요구 약화 ablation | `nodes`, `edges`, `mappings` |
| `P_minus_Procedural_schema` | procedural schema 제거 ablation | `nodes`, `edges`, `mappings` |
| `P_minus_Validator` | post-hoc validator rejection 제거 ablation | `nodes`, `edges`, `mappings` |
| `P_minus_Standard_bridge` | NCS/PCF bridge 제거 ablation | `nodes`, `edges` |
| `P_minus_Schema_retrieval` | chunk-specific schema/taxonomy retrieval 제거 ablation | `nodes`, `edges`, `mappings` |

---

## 5. 실제 저장된 prompt 원문

아래는 실제 prompt 파일의 원문입니다. 실제 LLM 호출 때는 이 문장에 chunk metadata, sentence ids, chunk sentences, allowed node types, allowed predicates, output JSON shape가 결합됩니다.

| condition | 실제 prompt 원문 |
|---|---|
| `B0_plain_llm` | `Extract subject-predicate-object triples from the chunk. Return JSON only.` |
| `B1_predicate_constrained` | `Extract triples using only the allowed predicates. Return JSON only with evidence sentence ids.` |
| `B2_current_project` | `Extract Task Frames, then triples, then post-process into the Layer2 schema.` |
| `B3_edc_style` | `Extract, define, and canonicalize open-schema KG items, then emit CAPE-compatible nodes and edges for scoring.` |
| `B4_taxonomy_rag` | `Retrieve NCS/PCF/task taxonomy snippets, then extract schema-constrained triples with evidence.` |
| `B5_procedural_prompt` | `Extract actions, actors, gateways, guard conditions, artifact flows, and temporal/logical dependencies.` |
| `B6_sac_kg_verifier_pruner` | `Use existing generator candidates, then apply schema/evidence verification and pruning in the style of SAC-KG. This is a deterministic approximation, not a full SAC-KG reproduction.` |
| `P_cape_kg_actual` | `Use CQ-linked schema retrieval, procedural frame extraction, evidence-span constrained relation extraction, span verification, ontology validation, procedural consistency checks, and active review scoring.` |
| `P_minus_Schema_retrieval` | `Run CAPE-KG without chunk-specific schema/taxonomy retrieval; keep CQ, evidence grounding, procedural schema, validation, and mapping output shape.` |

Strict JSON 조건에는 다음 계약을 추가했습니다.

```text
Return exactly one JSON object and nothing else.
Do not include markdown, code fences, comments, XML tags, <think> blocks, prose, or explanations.
Use empty arrays for absent nodes, edges, triples, or mappings fields required by the requested shape.
```

`P_minus_CQ`, `P_minus_Evidence`, `P_minus_Procedural_schema`, `P_minus_Validator`, `P_minus_Standard_bridge`는 별도 파일이 아니라 runtime condition으로 구현했습니다. 즉 `P_cape_kg_actual`의 공통 template에서 특정 구성요소를 제거하거나 약화한 조건입니다.

---

## 6. `P_cape_kg_actual`의 핵심

`P_cape_kg_actual`은 단순 prompt engineering이 아니라, 다음 요소를 결합한 proposed method입니다.

```text
CQ anchoring
-> schema/taxonomy retrieval
-> procedural frame extraction
-> evidence-constrained node/edge extraction
-> span/evidence verification
-> ontology validation
-> procedural consistency checks
-> active review scoring
-> NCS/PCF standard bridge
```

주요 제약:

| 제약 | 내용 |
|---|---|
| CQ anchoring | CQ1-CQ12를 기준으로 추출 대상 고정 |
| Evidence grounding | 각 item은 현재 chunk sentence id를 evidence로 가져야 함 |
| Allowed node types | `DomainTask`, `ProcedureStep`, `Artifact`, `Role`, `DecisionGateway`, `GuardCondition`, `Principle`, `Risk`, `ArtifactFlow` 등 |
| Allowed predicates | `HAS_STEP`, `PRECEDES`, `USES_INPUT`, `PRODUCES`, `PERFORMED_BY`, `HAS_DECISION_GATEWAY`, `HAS_GUARD_CONDITION`, `HAS_PRINCIPLE`, `HAS_RISK`, `FEEDS_INTO`, `USED_AS_INPUT_FOR` 등 |
| Output shape | `nodes`, `edges`, `mappings` |
| Hard limit | chunk당 최대 5 nodes, 5 edges, 3 mappings |
| Standard bridge | NCS/PCF 후보 mapping 출력 |

---

## 7. CQ는 어떻게 만들었는가

CQ는 LLM이 자동 생성한 것이 아니라, 연구자가 먼저 정의한 **KG 요구사항**입니다.

생성 방식:

1. 연구 문제를 "한국어 수주/제안 업무 문서에서 절차형 KG를 구축하는 문제"로 정의했습니다.
2. KG가 답해야 할 질문을 업무 구성, 순서, 입력, 산출물, 역할, 의사결정, evidence, NCS/PCF mapping으로 나누었습니다.
3. 각 질문을 필요한 node type과 edge predicate로 연결했습니다.
4. 이 CQ를 schema 설계, LLM prompt, validator, CQ answerability evaluation에서 재사용했습니다.

CQ 원본:

| 목적 | 파일 |
|---|---|
| EACL 실험용 CQ | `experiments/cape_kg_eacl_20260627/02_schema/competency_questions.json` |
| 내부 KG build용 CQ | `outputs/03_schema/competency_questions.json` |
| traceability 문서 | `experiments/cape_kg_eacl_20260627/06_release/prompt_node_edge_traceability.md` |

---

## 8. CQ 실제 예시

| CQ | 질문 | 연결 predicate |
|---|---|---|
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

예시 해석:

- CQ2와 CQ3이 있기 때문에 input artifact와 output artifact를 분리해 추출했습니다.
- CQ5와 CQ6이 있기 때문에 decision gateway와 guard condition을 별도 node/edge로 표현했습니다.
- CQ11과 CQ12가 있기 때문에 Layer 2 업무 KG를 NCS/PCF 표준 taxonomy와 연결했습니다.

---

## 9. Node는 어떻게 산출했는가

최종 node 파일: `outputs/07_layer2_graph/layer2_nodes.jsonl`

생성 흐름:

1. OCR sentence를 `EA-*` evidence anchor로 변환했습니다.
2. `TASK_SEEDS`의 label, alias, keyword로 관련 sentence를 찾았습니다.
3. task evidence 안에서 artifact, role, decision, principle, risk 후보를 용어 사전으로 추출했습니다.
4. 업무 단위를 `DomainTask` node로 만들었습니다.
5. task별 procedure template과 입력/산출물 구조를 이용해 `ProcedureStep` node를 만들었습니다.
6. 의사결정 문맥에서 `DecisionGateway`와 `GuardCondition`을 만들었습니다.
7. 산출물이 다음 업무 입력으로 쓰이는 경우 `ArtifactFlow`를 만들었습니다.
8. 모든 node에 evidence anchor와 review status를 붙였습니다.

Node type별 결과:

| node type | count | 생성 방식 |
|---|---:|---|
| `ProcedureStep` | 99 | task별 procedure template 또는 입력/산출물 기반 step 추론 |
| `DomainTask` | 22 | task seed label/alias/keyword와 OCR sentence evidence 매칭 |
| `Artifact` | 14 | task evidence 안의 입력물/산출물 용어 매칭 |
| `GuardCondition` | 13 | 의사결정 evidence에서 조건/가능성/경쟁/자원 표현 추출 |
| `Role` | 10 | 수행자/책임 주체 용어 매칭 |
| `ArtifactFlow` | 9 | 특정 산출물이 다음 task 입력으로 쓰이는 규칙 |
| `Principle` | 5 | 원칙/품질 기준 표현 매칭 |
| `DecisionGateway` | 4 | 의사결정 관련 표현 매칭 |
| `Risk` | 3 | 위험/불리함/실패 가능성 표현 매칭 |

---

## 10. Edge는 어떻게 산출했는가

최종 edge 파일: `outputs/07_layer2_graph/layer2_edges.jsonl`

생성 흐름:

1. task frame의 `inputs`, `outputs`, `roles`, `principles`, `risks` slot을 edge predicate로 변환했습니다.
2. `DomainTask`와 `ProcedureStep`은 `HAS_STEP`으로 연결했습니다.
3. 같은 task 안의 step 순서는 `PRECEDES`로 연결했습니다.
4. 입력은 `USES_INPUT`, 산출물은 `PRODUCES`로 연결했습니다.
5. 수행자/책임 주체는 `PERFORMED_BY`로 연결했습니다.
6. 의사결정 지점과 조건은 `HAS_DECISION_GATEWAY`, `HAS_GUARD_CONDITION`으로 연결했습니다.
7. 산출물이 다음 업무로 흐르면 `FEEDS_INTO`, `USED_AS_INPUT_FOR`로 연결했습니다.
8. source node, target node, allowed predicate, evidence가 모두 확인된 edge만 최종 graph에 남겼습니다.

Predicate별 결과:

| predicate | count | 생성 방식 |
|---|---:|---|
| `PRODUCES` | 220 | task/step의 output slot을 Artifact node로 연결 |
| `USES_INPUT` | 201 | task/step의 input slot을 Artifact 또는 Concept로 연결 |
| `PERFORMED_BY` | 120 | task/step의 role slot을 Role node로 연결 |
| `HAS_STEP` | 99 | DomainTask를 ProcedureStep 목록에 연결 |
| `PRECEDES` | 77 | 같은 task 안에서 step order 기준으로 연결 |
| `HAS_PRINCIPLE` | 64 | task/step의 principle slot을 Principle node로 연결 |
| `HAS_DECISION_GATEWAY` | 54 | task/step에서 발견된 decision node 연결 |
| `HAS_RISK` | 39 | task/step의 risk slot을 Risk node로 연결 |
| `HAS_GUARD_CONDITION` | 14 | DecisionGateway와 조건 node 연결 |
| `FEEDS_INTO` | 9 | Artifact가 다음 task로 흘러가는 규칙 연결 |
| `USED_AS_INPUT_FOR` | 9 | Artifact가 다음 task 입력으로 쓰이는 규칙 연결 |

---

## 11. 현재 실행한 실험

| 실험 | 현재 상태 |
|---|---|
| Qwen3-8B baseline/proposed/ablation | 실행 완료 |
| Qwen3-14B core condition scaling | 실행 완료 |
| Qwen3-32B-AWQ core condition scaling | 실행 완료 |
| B0/B1/B2 baseline | 각 120 rows 실행 완료 |
| B3/B4/B5/B6 baseline family | 실행 완료 |
| `P_cape_kg_actual` | 120 rows 실행 완료 |
| `P_minus_*` ablation | 6개 조건 실행 완료 |
| Public benchmark adapter | PAGED/Text2KG subset 실행 완료 |
| Active review pool design | 300 arm assignments -> 204 unique rows |
| Human review handoff | 준비 완료 |

Public benchmark cross-check:

| 항목 | 값 |
|---|---:|
| model run count | 4 |
| strong cross-check run present | true |
| max single-run PAGED items | 100 |
| max single-run Text2KG items | 200 |
| best PAGED edge F1 | 0.4233 |
| best Text2KG relation F1 | 0.6015 |

---

## 12. 현재 claim 가능/불가능 구분

| 구분 | 말할 수 있는 것 | 아직 말하면 안 되는 것 |
|---|---|---|
| KG 구축 | Layer 2 KG 179 nodes / 906 edges 구축 완료 | 이것만으로 baseline보다 우수하다는 성능 주장 |
| LLM 실험 | baseline/proposed/ablation/model scaling 실행 완료 | human-gold 기반 F1 우수성 claim |
| Evidence | final node/edge가 evidence anchor를 갖도록 구성 | evidence exact match 최종 우수성 claim |
| Mapping | NCS/PCF 후보 110개씩 생성 | expert-confirmed P@K, MRR, nDCG claim |
| Active review | review queue와 effort template 준비 | 실제 사람 검수 시간 절감 claim |
| Release | pre-human validation PASS, release bundle 준비 | 최종 논문 제출 ready claim |

현재 claim gate가 FAIL인 이유는 실험 실패가 아니라, 다음 사람이 해야 할 검수 단계가 아직 없기 때문입니다.

| 남은 항목 | 필요 이유 |
|---|---|
| human-gold annotation | 최종 node/edge/evidence 정답 확정 |
| IAA | annotator agreement 보고 |
| adjudication | 최종 gold label 확정 |
| `P_cape_kg_actual` human-gold scoring | proposed method main result 확정 |
| mapping expert review | NCS/PCF bridge 성능 claim 확정 |

---

## 13. 교수님께 말할 핵심 문장

1. "연구를 단순 업무 온톨로지 구축이 아니라, 한국어 업무 문서 기반 evidence-grounded procedural KG construction task로 재정의했습니다."
2. "CAPE-KG의 핵심은 CQ, procedural schema, evidence grounding, validator, NCS/PCF bridge를 결합한 것입니다."
3. "최종 Layer 2 KG는 179 nodes, 906 edges이며, LLM raw output이 아니라 evidence/schema/rule 기반으로 조립한 graph입니다."
4. "LLM은 사용했지만, 최종 KG 자체를 그대로 생성한 것이 아니라 baseline/proposed/ablation 후보 생성 실험에 사용했습니다."
5. "실제 prompt는 조건별로 다르게 설계했고, `P_cape_kg_actual`은 CQ, schema retrieval, evidence constraint, validator, standard bridge를 결합합니다."
6. "자동 구축과 실험 실행은 완료되었지만, 논문 main performance table은 human-gold annotation, IAA, adjudication 이후 확정해야 합니다."

---

## 14. 같이 열어볼 파일

| 목적 | 파일 |
|---|---|
| 상세 발표자료 슬라이드 원고 | `experiments/cape_kg_eacl_20260627/07_reports/professor_report_slide_contents_current_20260628_ko.md` |
| 이 핵심 브리프 | `experiments/cape_kg_eacl_20260627/07_reports/professor_report_core_brief_prompt_cq_node_edge_20260628_ko.md` |
| prompt/node/edge 추적 | `experiments/cape_kg_eacl_20260627/06_release/prompt_node_edge_traceability.md` |
| CQ 원본 | `experiments/cape_kg_eacl_20260627/02_schema/competency_questions.json` |
| prompt 파일 | `experiments/cape_kg_eacl_20260627/02_schema/prompts/` |
| 최종 node | `outputs/07_layer2_graph/layer2_nodes.jsonl` |
| 최종 edge | `outputs/07_layer2_graph/layer2_edges.jsonl` |
| claimable main table | `experiments/cape_kg_eacl_20260627/06_release/claimable_main_table.md` |
| pre-human validation | `experiments/cape_kg_eacl_20260627/06_release/pre_human_handoff_validation.md` |
