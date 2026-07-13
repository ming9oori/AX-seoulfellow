# 교수님 보고용 핵심 요약본

Generated: 2026-06-29  
Source slide draft: `experiments/cape_kg_eacl_20260627/07_reports/professor_report_slide_contents_current_20260628_ko.md`  
Experiment directory: `experiments/cape_kg_eacl_20260627`  
KG output directory: `outputs`

이 문서는 기존 슬라이드별 발표 원고와 별개로, 교수님께 핵심만 설명하기 위한 요약본입니다. 특히 다음 질문에 바로 답할 수 있도록 정리했습니다.

1. 어떤 방법론으로 KG를 구축했는가?
2. 실제 어떤 프롬프트로 LLM 실험을 실행했는가?
3. CQ는 어떻게 만들었고 어디에 쓰였는가?
4. node와 edge는 각각 어떤 방식으로 산출되었는가?
5. 현재 어떤 결과까지 나왔고, 아직 무엇은 최종 주장하면 안 되는가?

---

## 1. 한 문장 요약

본 연구는 한국어 수주/제안 업무 문서에서 절차형 업무 지식을 추출하여, 각 node와 edge를 OCR sentence evidence에 연결한 evidence-grounded procedural KG를 구축하고, 이를 NCS/PCF 표준 taxonomy와 연결하는 방법론을 실험한 것이다.

핵심은 "LLM에게 그래프를 자유롭게 만들라고 한 것"이 아니라, CQ, schema, evidence anchor, validator, NCS/PCF bridge를 결합하여 통제된 KG 구축 및 평가 파이프라인을 만든 점이다.

---

## 2. 현재 결과 한 장 요약

현재 EACL 실험 디렉토리 기준 핵심 산출물은 다음과 같다.

| 구분 | 현재 결과 | 해석 |
| --- | ---: | --- |
| OCR evidence anchors | 5,009 | KG의 근거가 되는 sentence-level anchor |
| Layer 2 chunks | 214 | 전체 현재 corpus chunk |
| Evaluation chunks | 120 | LLM 조건 비교 및 silver diagnostic 실행 단위 |
| Layer 1 NCS nodes | 4,109 | NCS 표준 taxonomy KG |
| Layer 1 PCF nodes | 5,301 | PCF 표준 taxonomy KG |
| Layer 2 nodes | 179 | 최종 업무 KG node |
| Layer 2 edges | 906 | 최종 업무 KG edge |
| Schema-valid triples | 906 | edge 검증 및 evidence 추적용 중간 표현 |
| Evidence-missing final edges | 0 | accepted edge는 모두 evidence 보유 |
| Dangling final edges | 0 | source/target이 없는 edge 없음 |
| NCS mapping candidates | 110 | Layer 2 task to NCS 후보, expert review 전 |
| PCF mapping candidates | 110 | Layer 2 task to PCF 후보, expert review 전 |
| Qwen3-8B proposed rows | 120 | `P_cape_kg_actual` 조건 실행 완료 |
| Qwen3-8B proposed outputs | 576 nodes / 373 edges / 227 mappings | LLM prediction 산출물, 최종 KG 자체는 아님 |

중요한 해석은 다음이다.

- KG 구축 자체는 완료되었다.
- Layer 1 NCS/PCF KG와 Layer 2 업무 KG는 생성되어 시각화, Neo4j/RDF/GraphML 변환까지 가능하다.
- 다만 human-gold annotation, IAA, adjudication, mapping expert review가 끝나기 전에는 precision/recall/F1 기반 최종 성능 우수성 claim은 하면 안 된다.
- 현재 LLM 성능표는 silver/proxy diagnostic이며, 논문 최종 main table은 사람 검수 이후 확정해야 한다.

---

## 3. 방법론 핵심 구조

방법론은 CAPE-KG로 정리할 수 있다.

| 구성 요소 | 역할 |
| --- | --- |
| Competency Questions, CQ | KG가 답해야 할 업무 질문을 먼저 정의 |
| Procedural schema | task, step, artifact, role, decision, risk 등을 node/edge type으로 구조화 |
| Evidence grounding | 모든 accepted node/edge를 OCR sentence evidence에 연결 |
| LLM prompt conditions | baseline, proposed, ablation 조건별 prediction 생성 |
| Validator | JSON parse, schema, predicate, domain/range, evidence 조건 검증 |
| Standard bridge | Layer 2 업무 KG를 NCS/PCF 표준 taxonomy와 연결 |
| Human review handoff | human-gold, mapping review, active review를 위한 검수 패키지 생성 |

이 방법론에서 LLM은 최종 KG를 그대로 만드는 단일 도구가 아니다. LLM은 동일한 chunk에 대해 여러 조건이 어떤 node/edge/mapping 후보를 만드는지 비교하기 위한 prediction generator로 사용되었다. 최종 KG는 별도의 rule/schema/evidence 기반 build pipeline에서 생성되었다.

---

## 4. CQ는 어떻게 생성했는가?

CQ는 LLM이 자동 생성한 결과가 아니다. 연구자가 "이 KG가 답해야 하는 업무 질문"을 먼저 정의하고, 각 질문을 schema node type 및 edge predicate에 연결한 설계 산출물이다.

생성 절차는 다음과 같다.

1. 연구 문제를 정의했다.
   - 한국어 수주/제안 업무 문서에서 절차형 업무 지식을 KG로 구축한다.
   - 단순 entity extraction이 아니라 업무 순서, 입력, 산출물, 역할, 의사결정, 위험, evidence, 표준 mapping을 표현한다.
2. 업무 KG가 답해야 할 질문 범주를 설계했다.
   - 주요 업무와 절차 단계
   - 입력 자료와 산출물
   - 수행 역할
   - 의사결정 지점과 조건
   - 산출물 흐름
   - 원문 evidence grounding
   - NCS/PCF 표준 연결
3. 각 질문을 target predicate에 연결했다.
   - 예: "각 Task는 어떤 산출물을 생성하는가?" -> `PRODUCES`
   - 예: "각 Task는 어떤 입력 자료를 사용하는가?" -> `USES_INPUT`
   - 예: "의사결정 조건은 무엇인가?" -> `HAS_GUARD_CONDITION`
4. 이 CQ를 schema 설계, LLM prompt, structural evaluation, CQ answerability 계산에 재사용했다.

관련 파일은 다음과 같다.

| 역할 | 파일 |
| --- | --- |
| EACL 실험 CQ | `experiments/cape_kg_eacl_20260627/02_schema/competency_questions.json` |
| 내부 KG build CQ | `outputs/03_schema/competency_questions.json` |
| CQ/schema 생성 코드 | `scripts/build_ax_epak_internal_kg.py`, `scripts/build_cape_kg_eacl_experiment.py` |
| CQ traceability 문서 | `experiments/cape_kg_eacl_20260627/06_release/prompt_node_edge_traceability.md` |

---

## 5. CQ 실제 목록

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

발표에서 강조할 점은 CQ가 단순한 설명 문장이 아니라, node/edge 설계와 LLM extraction output shape를 결정하는 기준이라는 점이다.

---

## 6. 실제 프롬프트는 무엇이었는가?

프롬프트는 두 층으로 구성되었다.

1. 조건별 prompt file
   - 각 baseline/proposed/ablation의 핵심 지시문
2. runtime prompt template
   - 실제 chunk sentence, sentence id, allowed node types, allowed edge predicates, JSON output shape, evidence rule을 결합

즉, 저장된 프롬프트 한 줄만 LLM에 들어간 것이 아니라, 아래 요소들이 실제 호출 시 함께 결합되었다.

```text
Return ONLY one valid JSON object; no markdown and no explanation.
Each item must use evidence_anchor_ids from the current chunk sentence_ids.
Do not use outside knowledge.
Keep Korean labels when the source text is Korean.
Use only the listed node types and edge predicates.
Hard limit: return at most 5 nodes, at most 5 edges, and at most 3 mappings.
```

제안 방법론 조건인 `P_cape_kg_actual`의 저장 프롬프트 원문은 다음이다.

```text
Use CQ-linked schema retrieval, procedural frame extraction, evidence-span constrained relation extraction, span verification, ontology validation, procedural consistency checks, and active review scoring.
```

실제 runtime instruction의 핵심은 다음과 같다.

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
- Use only the listed node types and edge predicates.
- Invalid schema terms will be rejected.
- Do not use outside knowledge.
- Return JSON only.
```

---

## 7. 프롬프트 조건별 산출물 차이

| 조건 | 프롬프트 의도 | 요구한 출력 |
| --- | --- | --- |
| `B0_plain_llm` | schema 없이 자유 subject-predicate-object triple 추출 | `triples` |
| `B1_predicate_constrained` | 허용 predicate만 사용해 edge 후보 추출 | `edges` |
| `B2_current_project` | task frame 추론 후 Layer 2 schema로 후처리 | `nodes`, `edges` |
| `B3_edc_style` | open-schema item 추출, 정의, canonicalization 후 CAPE 호환 변환 | `nodes`, `edges` |
| `B4_taxonomy_rag` | NCS/PCF/task taxonomy snippet을 retrieval context로 사용 | `nodes`, `edges`, `mappings` |
| `B5_procedural_prompt` | action, actor, gateway, artifact flow, dependency 추출 | `nodes`, `edges` |
| `B6_sac_kg_verifier_pruner` | 기존 후보를 schema/evidence verifier로 pruning | `nodes`, `edges` |
| `P_cape_kg_actual` | CQ, evidence, procedural schema, validator, NCS/PCF bridge 결합 | `nodes`, `edges`, `mappings` |
| `P_minus_CQ` | 제안 방법론에서 CQ anchoring 제거 | `nodes`, `edges`, `mappings` |
| `P_minus_Evidence` | evidence anchor 요구 약화 | `nodes`, `edges`, `mappings` |
| `P_minus_Procedural_schema` | 절차형 schema 대신 flat schema 사용 | `nodes`, `edges`, `mappings` |
| `P_minus_Validator` | validator rejection 없이 모델 schema 선택 허용 | `nodes`, `edges`, `mappings` |
| `P_minus_Standard_bridge` | NCS/PCF bridge 출력 제거 | `nodes`, `edges` |
| `P_minus_Schema_retrieval` | chunk-specific schema/taxonomy retrieval 제거 | `nodes`, `edges`, `mappings` |

이 표가 중요한 이유는, 같은 LLM을 사용해도 prompt condition에 따라 산출물의 구조가 달라진다는 점을 보여주기 때문이다. 예를 들어 B0는 graph node/edge가 아니라 자유 triple을 만들고, 제안 방법론은 node, edge, mapping을 모두 만들도록 설계했다.

---

## 8. 최종 KG node는 어떻게 생성했는가?

최종 `outputs/07_layer2_graph/layer2_nodes.jsonl`의 node는 LLM 출력물을 그대로 저장한 것이 아니다. OCR sentence evidence, task seed, 용어 사전, 절차 템플릿, schema constraint를 사용해 rule/schema/evidence 기반으로 생성한 graph node이다.

Node 생성 흐름은 다음과 같다.

1. OCR sentence를 evidence anchor로 만든다.
2. task seed의 label, alias, keyword를 사용해 관련 sentence를 찾는다.
3. 관련 evidence가 있는 task만 `DomainTask` 후보로 만든다.
4. task별 procedure template 또는 입력/산출물 기반 규칙으로 `ProcedureStep`을 만든다.
5. 입력물/산출물 용어 매칭으로 `Artifact`를 만든다.
6. 수행 주체 용어 매칭으로 `Role`을 만든다.
7. decision 관련 표현으로 `DecisionGateway`와 `GuardCondition`을 만든다.
8. 위험/원칙 표현으로 `Risk`, `Principle`을 만든다.
9. 산출물이 다음 업무 입력으로 쓰이는 규칙으로 `ArtifactFlow`를 만든다.
10. `node_id` 기준으로 중복 제거하고 evidence와 review status를 붙인다.

현재 node type별 개수는 다음과 같다.

| Node type | 개수 | 생성 방식 |
| --- | ---: | --- |
| `ProcedureStep` | 99 | task별 procedure template 또는 입력/산출물 기반 step 추론 |
| `DomainTask` | 22 | task seed label/alias/keyword로 OCR evidence 검색 |
| `Artifact` | 14 | task evidence 안의 입력물/산출물 용어 매칭 |
| `GuardCondition` | 13 | 의사결정 evidence에서 조건 표현 추출 |
| `Role` | 10 | 수행자/책임 주체 용어 매칭 |
| `ArtifactFlow` | 9 | 특정 산출물이 다음 task 입력으로 쓰이는 규칙 |
| `Principle` | 5 | 원칙/품질 기준 용어 매칭 |
| `DecisionGateway` | 4 | 의사결정 관련 용어 매칭 |
| `Risk` | 3 | 위험/불리함/실패 가능성 용어 매칭 |

핵심 설명은 다음과 같다.

> 최종 KG node는 LLM이 자유롭게 만든 node가 아니라, evidence anchor와 schema constraint를 만족하도록 조립된 node이다.

---

## 9. 최종 KG edge는 어떻게 생성했는가?

최종 `outputs/07_layer2_graph/layer2_edges.jsonl`의 edge는 node 사이의 업무 관계를 predicate별 규칙으로 생성한 뒤, source node와 target node가 실제로 존재하고 evidence가 있는 경우에만 저장한 것이다.

Edge 생성 흐름은 다음과 같다.

1. task frame과 procedure structure에서 입력, 산출물, 역할, 위험, 원칙, 의사결정 slot을 읽는다.
2. 각 slot을 허용 predicate에 매핑한다.
3. source node와 target node가 graph 안에 실제로 존재하는지 확인한다.
4. edge에 evidence anchor를 연결한다.
5. edge를 triple record로 변환해 `source_triple_ids`를 부여한다.
6. allowed predicate, domain/range, evidence 존재 조건을 검증한다.
7. 검증을 통과한 edge만 최종 graph에 저장한다.

현재 edge predicate별 개수는 다음과 같다.

| Edge predicate | 개수 | 생성 방식 |
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

검증 결과는 다음과 같다.

| 항목 | 값 |
| --- | ---: |
| Final Layer 2 edges | 906 |
| Evidence가 있는 edges | 906 / 906 |
| `source_triple_ids`가 있는 edges | 906 / 906 |
| Dangling edges | 0 |

핵심 설명은 다음과 같다.

> 최종 edge는 "문장에 관계가 있어 보인다"는 수준의 후보가 아니라, 허용 predicate, source/target node 존재, evidence anchor 조건을 통과한 관계이다.

---

## 10. Triple, node, edge의 관계

본 실험에서는 triple을 최종 graph 자체라기보다 edge 검증과 evidence 추적을 위한 중간 표현으로 사용했다.

| 단계 | 파일 | 현재 수량 |
| --- | --- | ---: |
| Task frame | `outputs/04_task_frames/canonical_task_catalog.json` | 22 tasks |
| Procedure structure | `outputs/05_procedure/procedure_structures_clean.jsonl` | 22 procedures / 99 steps |
| Schema-valid triple | `outputs/06_triples/layer2_triples_schema_valid.jsonl` | 906 |
| Final nodes | `outputs/07_layer2_graph/layer2_nodes.jsonl` | 179 |
| Final edges | `outputs/07_layer2_graph/layer2_edges.jsonl` | 906 |

정리하면 다음과 같다.

- Node: 업무 개념 자체이다. 예: task, step, artifact, role.
- Edge: node 사이의 관계이다. 예: `DomainTask PRODUCES Artifact`.
- Triple: edge를 subject-predicate-object와 evidence로 검증하기 위한 중간 record이다.
- Evidence anchor: 해당 node/edge/triple이 근거로 삼은 OCR sentence이다.

---

## 11. LLM 실험은 무엇을 실행했는가?

LLM 실험은 120개 evaluation chunk에 대해 Qwen3-8B strict JSON 조건으로 baseline, proposed, ablation을 실행한 것이다. 추가로 Qwen3-14B, Qwen3-32B-AWQ model scaling diagnostic도 수행했다.

Qwen3-8B strict JSON 120 chunk full run의 주요 산출물은 다음과 같다.

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

주의할 점은 출력 개수가 많다고 성능이 좋다는 뜻은 아니라는 점이다. 이 표는 어떤 조건이 어떤 종류의 후보를 얼마나 생성했는지 보여주는 coverage/behavior 표이다.

---

## 12. 현재 claim 가능한 것과 아닌 것

| 구분 | 현재 상태 | 발표 가능 표현 |
| --- | --- | --- |
| KG 구축 | 완료 | Layer 1 NCS/PCF KG와 Layer 2 업무 KG를 구축했다 |
| Evidence grounding | 완료 | accepted Layer 2 edge 906개는 모두 evidence anchor를 가진다 |
| LLM 조건 실행 | 완료 | baseline/proposed/ablation 120 chunk run을 수행했다 |
| Qwen3 model scaling | 완료 | 8B, 14B, 32B-AWQ diagnostic을 실행했다 |
| NCS/PCF mapping 후보 | 완료 | NCS 110개, PCF 110개 후보를 생성했다 |
| Structural diagnostics | 완료 | ontology conformance, procedural consistency, CQ answerability를 계산했다 |
| Human-gold 성능 | 미완료 | 사람 검수 전이므로 최종 precision/recall/F1 claim은 불가 |
| Mapping 성능 | 미완료 | expert review 전이므로 Hit@K, MRR 등 최종 claim 불가 |
| Active-review 효율 | 미완료 | human timing/correction evidence 전이므로 효율 claim 불가 |

교수님께 보고할 때는 다음과 같이 말하는 것이 안전하다.

> 현재까지는 KG 구축과 실험 실행, 진단, 검수 패키지 준비까지 완료했습니다. 다만 논문에서 최종 성능 우수성을 주장하려면 human-gold annotation과 expert review가 필요합니다.

---

## 13. 발표에서 가장 강조할 핵심 문장

1. 이 연구는 단순한 LLM triple extraction이 아니라, CQ-anchored procedural KG construction 방법론이다.
2. CQ는 KG가 답해야 할 업무 질문을 먼저 정의하고, 이를 schema와 prompt와 evaluation에 연결한 설계 장치이다.
3. 최종 KG node/edge는 LLM raw output이 아니라, OCR evidence, task seed, schema, predicate rule, validator를 통과해 조립된 graph이다.
4. LLM은 baseline/proposed/ablation 조건을 비교하기 위한 prediction generator로 사용되었다.
5. 현재 Layer 2 KG는 179 nodes, 906 edges이며 모든 accepted edge는 evidence anchor를 가진다.
6. NCS/PCF bridge 후보는 생성되었지만, mapping 성능 claim은 expert review 이후 가능하다.
7. 현재 silver/proxy metric은 진단용이며, 논문 main performance table은 human-gold annotation 이후 확정해야 한다.

---

## 14. 교수님 질문 대비 답변

### Q1. LLM을 썼는가?

썼다. 다만 최종 KG 전체를 LLM raw output으로 만든 것이 아니라, LLM은 조건별 candidate prediction 실험에 사용했다. 최종 KG는 evidence 기반 build pipeline에서 생성되었고, LLM 실험은 proposed method와 baseline/ablation 비교를 위한 별도 산출물이다.

### Q2. 어떤 LLM을 썼는가?

주요 full run은 Qwen3-8B 4bit strict JSON 조건으로 실행했다. 추가 diagnostic으로 Qwen3-14B와 Qwen3-32B-AWQ도 core 120 chunk 조건에서 실행했다.

### Q3. 프롬프트 차별점은 무엇인가?

제안 조건인 `P_cape_kg_actual`은 CQ, evidence grounding, procedural schema, validator, NCS/PCF bridge를 모두 결합했다. baseline들은 자유 triple, predicate 제한, taxonomy RAG, procedural prompt 등 일부 요소만 가진다. ablation은 CQ, evidence, schema, validator, standard bridge를 하나씩 제거해 비교한다.

### Q4. node는 어떻게 만든 것인가?

OCR sentence evidence에서 task seed, alias, keyword, 절차 템플릿, 입력/산출물/역할/위험/원칙 용어 매칭을 사용해 만들었다. 모든 최종 node는 `node_id`, `type`, `label`, evidence, review status를 가진다.

### Q5. edge는 어떻게 만든 것인가?

task/step의 입력, 산출물, 역할, 위험, 원칙, 의사결정 slot을 허용 predicate에 매핑하고, source/target node가 존재하며 evidence가 있는 경우에만 저장했다.

### Q6. 지금 main table이 나왔는가?

현재 main table 후보와 claimable table은 있다. 하지만 human-gold annotation 전이므로 최종 성능 main table은 아직 아니다. 지금 표는 setup/diagnostic/result status를 구분하기 위한 중간 보고용 표이다.

### Q7. 지금 논문 claim에서 조심해야 할 점은 무엇인가?

silver/proxy F1을 최종 성능으로 주장하면 안 된다. 사람 검수 전에는 "diagnostic" 또는 "setup completed"로 표현해야 한다.

---

## 15. 핵심 산출물 경로

| 산출물 | 경로 |
| --- | --- |
| 전체 발표 원고 | `experiments/cape_kg_eacl_20260627/07_reports/professor_report_slide_contents_current_20260628_ko.md` |
| Prompt/node/edge traceability | `experiments/cape_kg_eacl_20260627/06_release/prompt_node_edge_traceability.md` |
| CQ file | `experiments/cape_kg_eacl_20260627/02_schema/competency_questions.json` |
| Prompt files | `experiments/cape_kg_eacl_20260627/02_schema/prompts/` |
| Final Layer 2 nodes | `outputs/07_layer2_graph/layer2_nodes.jsonl` |
| Final Layer 2 edges | `outputs/07_layer2_graph/layer2_edges.jsonl` |
| Schema-valid triples | `outputs/06_triples/layer2_triples_schema_valid.jsonl` |
| Final build report | `outputs/10_evaluation/final_build_report.md` |
| Claimable main table | `experiments/cape_kg_eacl_20260627/06_release/claimable_main_table.md` |
| Human review start guide | `experiments/cape_kg_eacl_20260627/06_release/human_review_start_here_ko.md` |

