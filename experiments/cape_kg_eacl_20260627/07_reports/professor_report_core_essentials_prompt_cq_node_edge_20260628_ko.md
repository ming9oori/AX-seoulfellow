# CAPE-KG 교수님 보고용 핵심 요약본

Generated: 2026-06-28  
Detailed slide draft: `experiments/cape_kg_eacl_20260627/07_reports/professor_report_slide_contents_current_20260628_ko.md`  
Traceability source: `experiments/cape_kg_eacl_20260627/06_release/prompt_node_edge_traceability.md`  
CQ query source: `experiments/cape_kg_eacl_20260627/06_release/cq_query_pack.md`

이 문서는 기존 상세 발표 원고와 별개로, 교수님께 핵심 내용만 빠르게 보고하기 위한 요약본입니다. 초점은 다음입니다.

1. 어떤 방법론으로 데이터를 KG로 만들었는가
2. 어떤 프롬프트 조건에서 어떤 산출물을 만들었는가
3. CQ를 어떻게 정의했고 KG 구축과 평가에 어떻게 썼는가
4. 최종 node와 edge가 각각 어떤 규칙으로 산출되었는가
5. 현재까지 무엇이 완료되었고 무엇이 human review 이후에 확정되는가

---

## 1. 한 문장 요약

본 연구는 한국어 수주/제안 업무 문서에서 **근거 문장에 연결된 절차형 지식그래프(evidence-grounded procedural KG)**를 구축하고, 이를 **NCS/PCF 표준 taxonomy**와 연결하는 CAPE-KG 방법론을 적용한 실험입니다.

핵심은 LLM 출력물을 그대로 KG로 저장한 것이 아니라는 점입니다.

> OCR sentence evidence, Competency Question, procedural schema, allowed predicate, validator, NCS/PCF bridge를 결합해 node와 edge를 통제된 방식으로 산출했습니다.

---

## 2. 현재까지의 산출물

| 항목 | 현재 상태 | 수치 |
|---|---|---:|
| OCR clean sentences | 완료 | 5,009 |
| Layer 2 chunks | 완료 | 214 |
| LLM evaluation chunks | 완료 | 120 |
| Layer 1 NCS KG | 완료 | 4,109 nodes |
| Layer 1 PCF KG | 완료 | 5,301 nodes |
| Layer 2 업무 KG | 완료 | 179 nodes / 906 edges |
| NCS mapping candidates | 완료 | 110 |
| PCF mapping candidates | 완료 | 110 |
| CQ query pack | 완료 | 12 CQ / 11 answerable |
| Pre-human handoff validation | 완료 | PASS; current check count: see `../06_release/pre_human_handoff_validation.md` |
| Human-gold annotation | 미완료 | pending |
| IAA/adjudication | 미완료 | pending |
| 최종 논문 성능표 | 미확정 | human-gold 이후 가능 |

중요한 해석:

- KG 구축 자체는 완료되었습니다.
- 자동 구조 진단과 release/handoff 검증도 완료되었습니다.
- 그러나 precision/recall/F1 중심의 최종 main table은 human-gold, IAA, adjudication 이후에 확정해야 합니다.

---

## 3. 전체 방법론

```text
OCR sentence 정제
-> evidence anchor 생성
-> task seed / keyword / procedure template 적용
-> Competency Question 정의
-> procedural schema 정의
-> node 후보 생성
-> edge/triple 후보 생성
-> schema/evidence/domain-range validation
-> final Layer 2 KG assembly
-> NCS/PCF standard bridge mapping
-> LLM baseline/proposed/ablation 비교
-> CQ answerability 및 structural diagnostic
-> human review handoff
```

방법론의 핵심 구성:

| 구성 | 역할 |
|---|---|
| CQ | KG가 답해야 할 질문을 먼저 정의 |
| Schema | 허용 node type과 predicate를 제한 |
| Evidence grounding | node/edge를 OCR sentence evidence에 연결 |
| Validator | evidence 누락, dangling edge, schema 위반을 제거 |
| Standard bridge | Layer 2 업무 KG를 NCS/PCF와 연결 |
| Human review | 최종 성능 claim을 위한 gold label 확보 |

---

## 4. 어떤 프롬프트로 무엇을 산출했는가

LLM 실험은 baseline, proposed, ablation 조건으로 나누어 실행했습니다. 모든 조건은 JSON-only 출력과 evidence sentence id 사용을 요구했습니다.

| condition | 역할 | 산출 key |
|---|---|---|
| `B0_plain_llm` | schema 없는 일반 triple extraction | `triples` |
| `B1_predicate_constrained` | 허용 predicate만 사용하는 edge extraction | `edges` |
| `B2_current_project` | 기존 task frame 방식 baseline | `nodes`, `edges` |
| `B3_edc_style` | open-schema item 추출 후 CAPE-compatible 변환 | `nodes`, `edges` |
| `B4_taxonomy_rag` | NCS/PCF/task taxonomy retrieval baseline | `nodes`, `edges`, `mappings` |
| `B5_procedural_prompt` | action, actor, gateway, artifact flow 중심 추출 | `nodes`, `edges` |
| `B6_sac_kg_verifier_pruner` | verifier/pruner 스타일 deterministic approximation | `nodes`, `edges` |
| `P_cape_kg_actual` | 제안 방법론 | `nodes`, `edges`, `mappings` |
| `P_minus_CQ` | CQ anchoring 제거 ablation | `nodes`, `edges`, `mappings` |
| `P_minus_Evidence` | evidence 요구 약화 ablation | `nodes`, `edges`, `mappings` |
| `P_minus_Procedural_schema` | procedural schema 제거 ablation | `nodes`, `edges`, `mappings` |
| `P_minus_Validator` | validator rejection 제거 ablation | `nodes`, `edges`, `mappings` |
| `P_minus_Standard_bridge` | NCS/PCF bridge 제거 ablation | `nodes`, `edges` |
| `P_minus_Schema_retrieval` | chunk-specific schema retrieval 제거 ablation | `nodes`, `edges`, `mappings` |

---

## 5. 실제 프롬프트 원문

아래 문장은 실제 prompt file에 저장된 condition별 원문입니다. 실제 LLM 호출 때는 이 원문에 chunk sentence, sentence id, allowed node type, allowed predicate, output JSON shape가 결합됩니다.

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

공통 strict JSON contract:

```text
Return exactly one JSON object and nothing else.
Do not include markdown, code fences, comments, XML tags, <think> blocks, prose, or explanations.
Use empty arrays for absent nodes, edges, triples, or mappings fields required by the requested shape.
```

`P_minus_CQ`, `P_minus_Evidence`, `P_minus_Procedural_schema`, `P_minus_Validator`, `P_minus_Standard_bridge`는 별도 prompt file이 아니라 runtime condition으로 구현했습니다.

---

## 6. CQ는 어떻게 생성했는가

CQ(Competency Question)는 LLM이 만든 결과가 아니라, 연구자가 먼저 정의한 **KG 요구사항**입니다.

생성 방식:

1. 연구 문제를 "한국어 수주/제안 업무 문서에서 절차형 KG를 구축하는 문제"로 정의했습니다.
2. 업무 KG가 답해야 할 질문을 업무 구성, 순서, 입력, 산출물, 역할, 의사결정, evidence, 표준 taxonomy mapping으로 나누었습니다.
3. 각 질문을 필요한 node type과 edge predicate에 연결했습니다.
4. 이 CQ를 schema 설계, LLM prompt, ablation, structural evaluation, query pack에 재사용했습니다.

CQ가 쓰인 위치:

| 위치 | 사용 방식 |
|---|---|
| Schema 설계 | node type과 predicate를 정하는 기준 |
| LLM proposed prompt | `P_cape_kg_actual`에서 CQ-linked schema retrieval 기준 |
| Ablation | `P_minus_CQ`에서 CQ anchoring 제거 효과 비교 |
| Structural evaluation | CQ answerability 계산 |
| Query pack | 각 CQ를 Cypher/SPARQL-style query와 sample answer에 연결 |

---

## 7. CQ 실제 목록

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

현재 CQ query pack 결과:

| 항목 | 값 |
|---|---:|
| CQ 수 | 12 |
| 현재 KG로 구조적으로 답 가능한 CQ | 11 |
| answerability rate | 0.916667 |
| sample answer rows | 55 |
| 현재 KG에서 support가 없는 CQ | CQ8 |

CQ8은 실패라기보다 현재 schema/KG가 `HAS_REVIEW_CHECKPOINT` edge를 final graph에 포함하지 못한 구조적 gap으로 기록했습니다.

---

## 8. Node는 어떻게 산출했는가

Final Layer 2 nodes: **179개**

| node type | count | 산출 방식 |
|---|---:|---|
| `DomainTask` | 22 | task seed의 label, alias, keyword를 OCR sentence evidence에서 검색해 생성 |
| `ProcedureStep` | 99 | task별 procedure template 또는 입력/산출물 기반 step 추론으로 생성 |
| `Artifact` | 14 | task evidence 안의 입력물/산출물 용어 매칭으로 생성 |
| `Role` | 10 | 수행자/책임 주체 용어 매칭으로 생성 |
| `DecisionGateway` | 4 | 의사결정 관련 표현을 기준으로 생성 |
| `GuardCondition` | 13 | 조건, 가능성, 경쟁, 자원 등 조건 표현을 추출해 생성 |
| `Principle` | 5 | 원칙/품질 기준 표현으로 생성 |
| `Risk` | 3 | 위험, 불리함, 실패 가능성 표현으로 생성 |
| `ArtifactFlow` | 9 | 산출물이 다음 task 입력으로 쓰이는 규칙에서 생성 |

Node 생성 조건:

- 모든 final node는 `evidence_anchor_ids`를 가져야 합니다.
- node type은 Layer 2 schema의 허용 type으로 제한했습니다.
- label은 가능한 한 원문 한국어 표현을 유지했습니다.
- 동일하거나 유사한 표현은 canonical task/artifact/role로 정규화했습니다.

---

## 9. Edge는 어떻게 산출했는가

Final Layer 2 edges: **906개**

| predicate | count | 산출 방식 |
|---|---:|---|
| `HAS_STEP` | 99 | DomainTask를 해당 ProcedureStep 목록에 연결 |
| `PRECEDES` | 77 | 같은 task 안에서 step order 기준으로 순서 연결 |
| `USES_INPUT` | 201 | task/step의 inputs slot을 Artifact 또는 Concept node로 연결 |
| `PRODUCES` | 220 | task/step의 outputs slot을 Artifact node로 연결 |
| `PERFORMED_BY` | 120 | task/step의 roles slot을 Role node로 연결 |
| `HAS_DECISION_GATEWAY` | 54 | task/step에서 발견된 의사결정 node를 연결 |
| `HAS_GUARD_CONDITION` | 14 | DecisionGateway에서 추출된 조건 node를 연결 |
| `HAS_PRINCIPLE` | 64 | task/step의 principles slot을 Principle node로 연결 |
| `HAS_RISK` | 39 | task/step의 risks slot을 Risk node로 연결 |
| `FEEDS_INTO` | 9 | Artifact가 다음 task로 흘러가는 규칙을 연결 |
| `USED_AS_INPUT_FOR` | 9 | Artifact가 다음 task 입력으로 사용되는 규칙을 연결 |

Edge 생성 조건:

- source node와 target node가 실제 존재해야 합니다.
- 모든 final edge는 `evidence_anchor_ids`를 가져야 합니다.
- 모든 final edge는 `source_triple_ids`로 중간 triple 산출물과 연결됩니다.
- predicate는 schema의 allowed predicate 목록으로 제한했습니다.
- dangling edge, evidence 누락, domain/range 위반은 validator에서 제거했습니다.

---

## 10. LLM 실험에서 나온 산출물 규모

LLM은 120개 evaluation chunk에 대해 조건별로 실행했습니다.

| condition | valid rows | triples | nodes | edges | mappings |
|---|---:|---:|---:|---:|---:|
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

주의:

- 이 표는 산출물 규모를 보여주는 diagnostic table입니다.
- 성능 우수성 claim은 아닙니다.
- precision/recall/F1 main table은 human-gold 이후 계산해야 합니다.

---

## 11. 발표에서 강조할 핵심 문장

발표에서는 다음 문장을 중심으로 설명하면 됩니다.

> 저의 방법론은 LLM에게 triple을 자유롭게 생성시키는 방식이 아니라, 먼저 CQ로 KG가 답해야 할 질문을 정의하고, 그 질문을 schema, predicate, evidence requirement에 연결한 뒤, OCR 문장 근거가 있는 node와 edge만 final KG에 반영하는 방식입니다.

> 따라서 최종 KG는 179개 node와 906개 edge로 구축되었고, 모든 node와 edge는 evidence anchor를 갖습니다.

> 현재 12개 CQ 중 11개는 final KG query로 구조적으로 답할 수 있으며, CQ8의 review checkpoint는 별도 structural gap으로 남겨 두었습니다.

> 자동 구축과 검증은 완료되었지만, 논문에서 최종 성능을 주장하려면 human-gold annotation, IAA, adjudication, mapping expert review가 추가로 필요합니다.

---

## 12. 현재 남은 일

| 남은 일 | 이유 |
|---|---|
| Human-gold annotation | precision/recall/F1 계산을 위한 정답 필요 |
| IAA 계산 | annotator 간 일치도 보고 필요 |
| Adjudication | 최종 gold label 확정 필요 |
| Mapping expert review | NCS/PCF 후보의 실제 정합성 검증 필요 |
| Active-review human effort 기록 | 검수 시간 절감 claim을 하려면 실제 시간 로그 필요 |

현재 상태는 **pre-human handoff ready**입니다. 즉, 사람이 검수하기 전 자동 산출물과 검증 인프라는 준비되었지만, 최종 논문 claim은 아직 보류 상태입니다.
