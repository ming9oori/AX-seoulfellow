# 교수님 보고용 핵심 요약본

Generated: 2026-06-29  
Experiment directory: `experiments/cape_kg_eacl_20260627`  
Full slide draft: `experiments/cape_kg_eacl_20260627/07_reports/professor_report_slide_contents_current_20260628_ko.md`

이 문서는 긴 발표 원고와 별개로, 교수님께 먼저 보고할 핵심 내용만 압축한 요약본입니다. 발표에서는 이 문서를 먼저 기준으로 설명하고, 세부 프롬프트/슬라이드별 멘트는 기존 full slide draft를 참조하면 됩니다.

---

## 1. 한 문장 요약

본 연구는 한국어 수주/제안 업무 문서에서 업무 절차, 입력/산출물, 역할, 의사결정, 위험, 원문 근거를 함께 추출해 **evidence-grounded procedural KG**를 구축하고, 이를 NCS/PCF 표준 taxonomy와 연결한 CAPE-KG 방법론 실험입니다.

핵심은 단순히 "LLM으로 triple을 뽑았다"가 아닙니다. 현재 최종 KG는 **OCR sentence evidence + CQ + procedural schema + rule-based assembly + validator**로 구축되었고, LLM은 동일 task에서 baseline/proposed/ablation 조건의 후보 생성 성능을 비교하기 위해 별도로 사용했습니다.

---

## 2. 현재 완료된 것과 아직 남은 것

| 구분 | 현재 상태 | 교수님께 보고할 표현 |
| --- | --- | --- |
| Layer 1 NCS KG | 완료 | NCS taxonomy를 표준 기준축으로 구축 |
| Layer 1 PCF KG | 완료 | PCF taxonomy를 표준 기준축으로 구축 |
| Layer 2 업무 KG | 완료 | 수주/제안 업무 procedural KG 구축 완료 |
| Evidence grounding | 완료 | 최종 accepted edge 906개 모두 evidence 보유 |
| NCS/PCF mapping 후보 | 완료 | 각 110개 후보 생성, expert review 전 |
| LLM baseline/ablation | 실행 완료 | Qwen3 계열 조건별 후보 생성 실험 수행 |
| Model scaling | 실행 완료 | Qwen3-8B, Qwen3-14B, Qwen3-32B-AWQ 실행 |
| Human review handoff | 준비 완료 | annotation, IAA, adjudication, expert review 반환 파일 추적 구조 마련 |
| 최종 성능 claim | 아직 불가 | human-gold, IAA, adjudication 이후 확정 |

현재 `claim gate`가 FAIL인 이유는 자동 실험 실패가 아니라, 논문 수준의 최종 성능 주장을 하려면 사람이 검수한 gold label이 아직 필요하기 때문입니다.

---

## 3. 연구 문제의 핵심 전환

초기에는 "내부 업무 온톨로지/KG 구축"처럼 보일 수 있었지만, 현재 연구는 다음 문제로 정리되었습니다.

| 기존 관점 | 현재 연구 관점 |
| --- | --- |
| 수주/제안 업무 지식 정리 | 한국어 업무 문서 기반 procedural KG construction |
| 단순 ontology build | evidence-grounded KG extraction and validation |
| LLM triple extraction | CQ/schema/evidence/validator로 통제된 후보 생성 |
| 내부 데이터 결과물 | human-gold 평가 가능한 NLP/KG construction task |
| 표준과 별도 관리 | NCS/PCF standard bridge로 외부 taxonomy와 연결 |

발표에서 가장 중요한 표현은 다음입니다.

> CAPE-KG는 한국어 장문 업무 문서에서 절차형 업무 지식을 추출하고, 각 node와 edge를 원문 sentence evidence에 연결하며, NCS/PCF 표준 taxonomy로 bridge하는 방법론이다.

---

## 4. 전체 파이프라인

| 단계 | 실행 내용 | 대표 산출물 |
| --- | --- | --- |
| 1 | OCR workbook 정제 | clean sentences, evidence anchors |
| 2 | Layer 1 표준 KG 구축 | NCS KG, PCF KG |
| 3 | Layer 2 chunk 생성 | evaluation chunks, annotation chunks |
| 4 | CQ/schema 정의 | `02_schema/competency_questions.json`, `cape_schema.json` |
| 5 | task frame 생성 | canonical task catalog |
| 6 | procedure/triple 생성 | procedure structures, schema-valid triples |
| 7 | Layer 2 graph 조립 | `layer2_nodes.jsonl`, `layer2_edges.jsonl` |
| 8 | NCS/PCF mapping 후보 생성 | NCS 110 rows, PCF 110 rows |
| 9 | LLM baseline/ablation/model scaling | Qwen3 output JSONL, quality reports |
| 10 | 평가/진단/handoff | main results, structural diagnostics, human review packages |

---

## 5. Competency Question은 어떻게 만들었는가

CQ는 LLM이 자동 생성한 질문이 아니라, KG가 답해야 하는 업무 질문을 연구 설계 단계에서 먼저 정리한 것입니다. 즉, "어떤 node와 edge가 필요해야 이 업무 KG가 의미 있는가"를 정의하는 장치입니다.

CQ 생성 방식은 다음과 같습니다.

1. 수주/제안 업무 문서에서 답해야 하는 질문 범주를 먼저 정의했습니다.
2. 각 질문을 node type과 edge predicate에 연결했습니다.
3. 이 CQ를 schema 설계, LLM prompt, ablation, structural evaluation에 반복 사용했습니다.

대표 CQ는 다음과 같습니다.

| CQ | 질문 | 연결 predicate |
| --- | --- | --- |
| CQ1 | 수주·제안 업무는 어떤 주요 Task와 절차 단계로 구성되는가? | `HAS_STEP`, `PRECEDES` |
| CQ2 | 각 Task는 어떤 입력 자료를 사용하는가? | `USES_INPUT` |
| CQ3 | 각 Task는 어떤 산출물을 생성하는가? | `PRODUCES` |
| CQ4 | 각 Task는 누가 수행하거나 책임지는가? | `PERFORMED_BY` |
| CQ5 | 어떤 의사결정 지점이 존재하는가? | `HAS_DECISION_GATEWAY` |
| CQ6 | 의사결정에는 어떤 조건이나 판단 기준이 필요한가? | `HAS_GUARD_CONDITION` |
| CQ7 | 산출물은 다음 업무에서 어떻게 사용되는가? | `FEEDS_INTO`, `USED_AS_INPUT_FOR` |
| CQ11 | 특정 업무는 어떤 NCS 능력단위와 관련되는가? | `REQUIRES_CAPABILITY`, `CANDIDATE_ALIGNS_WITH` |
| CQ12 | 특정 업무는 PCF 프로세스 체계상 어디에 위치하는가? | `PROCESS_CONTEXT`, `CANDIDATE_ALIGNS_WITH` |

전체 CQ 12개는 `experiments/cape_kg_eacl_20260627/02_schema/competency_questions.json`에 저장되어 있습니다.

---

## 6. 실제 사용한 프롬프트 조건

프롬프트는 두 층으로 구성됩니다.

1. 조건별 핵심 지시문: `experiments/cape_kg_eacl_20260627/02_schema/prompts/`
2. runtime prompt: chunk sentence, sentence id, allowed node/edge type, evidence rule, JSON shape가 자동으로 결합됨

조건별 핵심 지시문은 다음과 같습니다.

| 조건 | 실제 저장된 핵심 프롬프트 | 주요 출력 |
| --- | --- | --- |
| B0_plain_llm | `Extract subject-predicate-object triples from the chunk. Return JSON only.` | `triples` |
| B1_predicate_constrained | `Extract triples using only the allowed predicates. Return JSON only with evidence sentence ids.` | `edges` |
| B2_current_project | `Extract Task Frames, then triples, then post-process into the Layer2 schema.` | `nodes`, `edges` |
| B3_edc_style | `Extract, define, and canonicalize open-schema KG items, then emit CAPE-compatible nodes and edges for scoring.` | `nodes`, `edges` |
| B4_taxonomy_rag | `Retrieve NCS/PCF/task taxonomy snippets, then extract schema-constrained triples with evidence.` | `nodes`, `edges`, `mappings` |
| B5_procedural_prompt | `Extract actions, actors, gateways, guard conditions, artifact flows, and temporal/logical dependencies.` | `nodes`, `edges` |
| P_cape_kg_actual | `Use CQ-linked schema retrieval, procedural frame extraction, evidence-span constrained relation extraction, span verification, ontology validation, procedural consistency checks, and active review scoring.` | `nodes`, `edges`, `mappings` |
| P_minus_CQ | 제안 방법론에서 CQ anchoring 제거 | `nodes`, `edges`, `mappings` |
| P_minus_Evidence | 제안 방법론에서 evidence 요구 약화 | `nodes`, `edges`, `mappings` |
| P_minus_Procedural_schema | procedural schema 대신 flat schema 사용 | `nodes`, `edges`, `mappings` |
| P_minus_Validator | validator rejection 제거 | `nodes`, `edges`, `mappings` |
| P_minus_Standard_bridge | NCS/PCF bridge 제거 | `nodes`, `edges` |

`P_cape_kg_actual` runtime prompt에는 다음 요소가 들어갔습니다.

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
- Hard limit: return at most 5 nodes, at most 5 edges, and at most 3 mappings.
```

따라서 LLM에게 단순히 "그래프를 만들어라"라고 요청한 것이 아니라, 어떤 CQ에 답해야 하는지, 어떤 node/edge type만 허용되는지, 어떤 sentence id를 evidence로 붙여야 하는지를 명시했습니다.

---

## 7. Node는 어떻게 산출했는가

최종 `outputs/07_layer2_graph/layer2_nodes.jsonl`의 node는 LLM 출력물을 그대로 넣은 것이 아닙니다. OCR sentence evidence, task seed, 용어 사전, procedure template을 사용해 rule/schema 기반으로 조립했습니다.

Node 생성 흐름은 다음과 같습니다.

1. OCR sentence를 `EA-JS-*` evidence anchor로 변환
2. 업무 seed label/alias/keyword로 관련 sentence 검색
3. sentence 안에서 artifact, role, decision, principle, risk 후보 추출
4. task frame을 `DomainTask` node로 생성
5. task별 procedure template으로 `ProcedureStep` 생성
6. 산출물이 다음 업무 입력으로 흐르는 경우 `ArtifactFlow` 생성
7. `node_id` 기준 중복 제거, evidence와 review status 부여

현재 Layer 2 node 구성은 다음과 같습니다.

| Node type | 생성 방식 | 개수 |
| --- | --- | ---: |
| DomainTask | 업무 seed + evidence sentence 검색 | 22 |
| ProcedureStep | procedure template 또는 입력/산출물 기반 step 추론 | 99 |
| Artifact | 입력/산출물 용어 매칭 | 14 |
| Role | 수행자/책임 주체 용어 매칭 | 10 |
| DecisionGateway | 의사결정 관련 표현 매칭 | 4 |
| GuardCondition | 의사결정 조건 표현 추출 | 13 |
| Principle | 원칙/품질 기준 용어 매칭 | 5 |
| Risk | 위험/불리함/실패 가능성 표현 매칭 | 3 |
| ArtifactFlow | 산출물의 다음 task 입력 흐름 규칙 | 9 |
| 합계 |  | 179 |

---

## 8. Edge는 어떻게 산출했는가

최종 `outputs/07_layer2_graph/layer2_edges.jsonl`의 edge는 predicate별 규칙으로 생성한 뒤, source node, target node, allowed predicate, evidence 조건을 통과한 것만 저장했습니다.

Edge 생성 흐름은 다음과 같습니다.

1. task frame의 `inputs`, `outputs`, `roles`, `principles`, `risks` slot을 predicate로 변환
2. decision gateway와 guard condition을 별도 edge로 연결
3. procedure step은 `HAS_STEP`, step 순서는 `PRECEDES`로 연결
4. artifact flow는 `FEEDS_INTO`, `USED_AS_INPUT_FOR`로 연결
5. edge를 triple record로 변환하고 `source_triple_ids` 부여
6. source/target 존재, allowed predicate, evidence 존재 여부 검증

Predicate별 edge 수는 다음과 같습니다.

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
| `FEEDS_INTO` | 산출물이 다음 업무로 흐름 | 9 |
| `USED_AS_INPUT_FOR` | 산출물이 다음 task 입력으로 사용 | 9 |
| 합계 |  | 906 |

검증 결과는 다음과 같습니다.

| 검증 항목 | 결과 |
| --- | ---: |
| Final Layer 2 nodes | 179 |
| Final Layer 2 edges | 906 |
| Schema-valid triples | 906 |
| Evidence가 있는 edges | 906 / 906 |
| Dangling edges | 0 |
| Type violations | 0 |

---

## 9. 현재 주요 수치

| 항목 | 결과 |
| --- | ---: |
| OCR clean sentences / evidence anchors | 5,009 |
| Total chunks available | 214 |
| Evaluation chunks | 120 |
| Layer 1 NCS nodes | 4,109 |
| Layer 1 NCS edges | 4,085 |
| Layer 1 PCF nodes | 5,301 |
| Layer 1 PCF taxonomy edges | 2,004 |
| Layer 1 PCF metric edges | 3,284 |
| Layer 2 nodes | 179 |
| Layer 2 edges | 906 |
| Silver reference nodes | 169 |
| Silver reference edges | 861 |
| Silver evidence anchors | 293 |
| NCS mapping candidates | 110 |
| PCF mapping candidates | 110 |

---

## 10. LLM은 어떻게 사용했는가

LLM은 최종 KG를 그대로 생성한 도구가 아니라, 같은 chunk에 대해 여러 조건이 어떤 후보 node/edge/triple/mapping을 만드는지 비교하기 위한 candidate generator로 사용했습니다.

실행한 주요 모델은 다음과 같습니다.

| 모델/run | 범위 | 역할 |
| --- | --- | --- |
| Qwen3-8B 4bit | 120 chunks, 여러 baseline/ablation | 기본 조건별 LLM 실험 |
| Qwen3-14B 4bit | 120 chunks, B0/B1/B2/P core conditions | 더 큰 모델 diagnostic |
| Qwen3-32B-AWQ | 120 chunks, B0/B1/B2/P core conditions | 현실적으로 실행 가능한 큰 모델 diagnostic |
| Llama-2-13B-chat | 10 chunks smoke | compatibility smoke run |

Qwen3-32B-AWQ까지 실행했지만, 현재 수치는 human-gold가 아니라 silver/proxy 기준입니다. 따라서 발표에서는 "model scaling diagnostic은 완료했지만, 최종 성능 claim은 human-gold 이후"라고 말해야 합니다.

---

## 11. 지금 주장할 수 있는 것과 아직 주장하면 안 되는 것

| 주장 유형 | 현재 가능 여부 | 이유 |
| --- | --- | --- |
| Layer 1 NCS/PCF KG 구축 완료 | 가능 | 산출물과 count 존재 |
| Layer 2 업무 KG 구축 완료 | 가능 | 179 nodes, 906 edges 생성 |
| Evidence-grounded graph 구축 | 가능 | accepted edge evidence missing 0 |
| LLM 조건별 후보 생성 실험 실행 | 가능 | Qwen3 계열 JSONL/report 존재 |
| CQ/schema/evidence/validator 기반 방법론 설계 | 가능 | schema, prompts, validation artifacts 존재 |
| CAPE-KG가 baseline보다 성능이 우수하다 | 아직 불가 | human-gold precision/recall/F1 미완료 |
| mapping 후보가 정답이다 | 아직 불가 | expert review 미완료 |
| active review가 실제 시간을 절감했다 | 아직 불가 | human correction/time evidence 미완료 |

---

## 12. 교수님께 보고할 핵심 메시지

발표에서 다음 순서로 말하면 됩니다.

1. 저는 수주/제안 업무 문서를 단순히 정리한 것이 아니라, evidence-grounded procedural KG construction 문제로 재정의했습니다.
2. CQ 12개를 먼저 설계하고, 이 CQ를 node/edge schema와 LLM prompt, evaluation에 연결했습니다.
3. 최종 KG는 LLM raw output이 아니라 OCR evidence, rule/schema 기반 task frame, procedure template, validator를 거쳐 구축했습니다.
4. 현재 Layer 2 KG는 179 nodes, 906 edges이고, 최종 edge는 모두 evidence를 갖습니다.
5. LLM은 별도로 baseline/proposed/ablation/model-scaling 후보 생성 실험에 사용했습니다.
6. Qwen3-8B, Qwen3-14B, Qwen3-32B-AWQ까지 실행했고, prompt 조건별 산출물도 정리되어 있습니다.
7. 다만 논문 수준의 최종 성능 우수성 claim은 human-gold annotation, IAA, adjudication, expert review 이후에만 확정하겠습니다.

---

## 13. 바로 보여줄 핵심 파일

| 목적 | 파일 |
| --- | --- |
| 긴 발표 원고 | `experiments/cape_kg_eacl_20260627/07_reports/professor_report_slide_contents_current_20260628_ko.md` |
| 최종 KG nodes | `outputs/07_layer2_graph/layer2_nodes.jsonl` |
| 최종 KG edges | `outputs/07_layer2_graph/layer2_edges.jsonl` |
| schema-valid triples | `outputs/06_triples/layer2_triples_schema_valid.jsonl` |
| CQ 목록 | `experiments/cape_kg_eacl_20260627/02_schema/competency_questions.json` |
| prompt 파일들 | `experiments/cape_kg_eacl_20260627/02_schema/prompts/` |
| 최종 실험 report | `experiments/cape_kg_eacl_20260627/07_reports/final_eacl_experiment_report.md` |
| main result table | `experiments/cape_kg_eacl_20260627/04_evaluation/main_results.csv` |
| human handoff plan | `experiments/cape_kg_eacl_20260627/06_release/human_gate_action_plan.md` |

---

## 14. 결론

현재까지는 자동 KG 구축, evidence grounding, NCS/PCF mapping 후보 생성, LLM baseline/ablation/model-scaling, public benchmark adapter, structural diagnostics, human-review handoff까지 완료되었습니다.

다만 최종 논문 표에서 "제안 방법론이 더 좋다"고 주장하려면 사람 검수 기반 gold label이 필요합니다. 따라서 현재 발표의 결론은 다음과 같이 잡는 것이 안전합니다.

> CAPE-KG 방법론을 적용해 한국어 수주/제안 업무 문서의 evidence-grounded procedural KG 구축과 LLM 조건별 실험 인프라는 완성했다. 다음 단계는 human-gold annotation, IAA, adjudication, expert review를 통해 최종 성능 claim을 확정하는 것이다.
