# 교수님 보고용 핵심 요약본

Generated: 2026-06-29  
Source long slide draft: `experiments/cape_kg_eacl_20260627/07_reports/professor_report_slide_contents_current_20260628_ko.md`  
Experiment directory: `experiments/cape_kg_eacl_20260627`  
KG output directory: `outputs`

이 문서는 긴 슬라이드 원고와 별개로, 교수님께 보고할 때 반드시 설명해야 하는 핵심만 압축한 요약본입니다. PPT를 직접 만드는 문서가 아니라, 발표 흐름과 핵심 표현을 빠르게 확인하기 위한 별도 파일입니다.

---

## 1. 한 문장 요약

한국어 수주/제안 업무 문서에서 업무 절차, 입력/산출물, 수행 역할, 의사결정, 위험, 근거 문장을 함께 표현하는 evidence-grounded procedural KG를 구축했고, 이를 NCS/PCF 표준 taxonomy와 연결한 뒤 LLM baseline, proposed prompt, ablation, model scaling, human-review handoff까지 실행했습니다.

---

## 2. 교수님께 먼저 말해야 할 핵심

| 구분 | 핵심 메시지 |
| --- | --- |
| 연구 문제 | 한국어 장문 업무 문서에서 절차형 업무 지식을 KG로 구조화하는 문제 |
| 핵심 방법론 | CQ, procedural schema, evidence grounding, validator, NCS/PCF bridge를 결합한 CAPE-KG |
| 최종 KG | Layer 1 표준 KG와 Layer 2 업무 KG 구축 완료 |
| LLM의 역할 | 최종 KG를 그대로 만든 도구가 아니라, 조건별 node/edge/mapping 후보 생성 성능을 비교하기 위한 prediction generator |
| 현재 결과 | 자동 구축, 구조 검증, LLM 진단, 모델 스케일링, human-review handoff 완료 |
| 아직 남은 것 | human-gold annotation, IAA, adjudication, mapping expert review, final performance table |

발표에서 가장 조심해야 할 표현은 다음입니다.

> KG 구축은 완료되었지만, 논문에서 최종 성능 우수성을 주장하려면 사람이 검수한 human-gold 기준의 평가가 아직 필요합니다.

---

## 3. 무엇을 만들었는가

### 3.1 Layer 1 표준 KG

| 구성 | 현재 결과 | 의미 |
| --- | ---: | --- |
| NCS taxonomy nodes | 4,109 | 국가직무능력표준 기반 표준축 |
| PCF taxonomy nodes | 5,301 | Process Classification Framework 기반 표준축 |
| NCS/PCF 역할 | 표준 taxonomy | Layer 2 업무 KG를 외부 표준 체계와 연결하기 위한 기준 |

### 3.2 Layer 2 업무 KG

| 항목 | 값 |
| --- | ---: |
| OCR clean sentences / evidence anchors | 5,009 |
| Layer 2 source chunks | 214 |
| Canonical DomainTask | 22 |
| Layer 2 nodes | 179 |
| Layer 2 edges | 906 |
| Schema-valid triples | 906 |
| NCS mapping candidates | 110 |
| PCF mapping candidates | 110 |
| Evidence-missing edges | 0 |
| Dangling edges | 0 |
| Type violations | 0 |

현재 KG는 단순 triple list가 아니라, 업무 절차를 표현하는 graph입니다. 주요 node type은 `DomainTask`, `ProcedureStep`, `Artifact`, `Role`, `DecisionGateway`, `GuardCondition`, `Principle`, `Risk`, `ArtifactFlow`입니다.

---

## 4. 방법론의 핵심 구조

CAPE-KG는 LLM에게 "그래프를 만들어줘"라고 요청하는 방식이 아닙니다. 전체 구조는 다음과 같습니다.

1. OCR sentence를 evidence anchor로 변환
2. 연구자가 정의한 Competency Question(CQ)로 KG가 답해야 할 질문을 고정
3. 업무 절차용 schema를 정의
4. task seed, 용어 사전, 절차 템플릿, evidence sentence를 이용해 Layer 2 KG node/edge를 구축
5. 모든 edge가 허용 predicate, source/target node 존재, evidence anchor 존재 조건을 만족하는지 검증
6. Layer 2 업무 KG를 NCS/PCF taxonomy 후보와 연결
7. LLM baseline/proposed/ablation/model-scaling은 동일 chunk에서 후보 생성 품질을 비교하기 위한 별도 prediction 실험으로 실행
8. 최종 성능 claim은 human-gold annotation 이후에만 확정

---

## 5. CQ는 어떻게 만들었는가

CQ는 LLM이 자동으로 만든 것이 아니라, 연구자가 먼저 정의한 KG 요구사항입니다. 즉, 이 KG가 답해야 하는 업무 질문을 먼저 만들고, 각 질문을 node type과 edge predicate에 연결했습니다.

CQ 설계 원칙은 다음입니다.

| 설계 기준 | 설명 |
| --- | --- |
| 업무 절차 | 어떤 업무 task와 step이 있는가 |
| 입력/산출물 | 업무가 무엇을 사용하고 무엇을 만드는가 |
| 수행 주체 | 누가 수행하거나 책임지는가 |
| 의사결정 | 어떤 gateway와 guard condition이 있는가 |
| 산출물 흐름 | 어떤 artifact가 다음 업무로 이어지는가 |
| evidence | 각 지식 항목이 원문 어느 sentence에 근거하는가 |
| 표준 연결 | 업무가 NCS/PCF 체계와 어떻게 연결되는가 |

실제 CQ 목록은 다음과 같습니다.

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

관련 파일:

| 역할 | 파일 |
| --- | --- |
| CQ 정의 | `experiments/cape_kg_eacl_20260627/02_schema/competency_questions.json` |
| prompt/node/edge 추적 문서 | `experiments/cape_kg_eacl_20260627/06_release/prompt_node_edge_traceability.md` |
| CQ query pack | `experiments/cape_kg_eacl_20260627/06_release/cq_query_pack.md` |

---

## 6. 실제 프롬프트는 무엇이었는가

프롬프트 파일은 `experiments/cape_kg_eacl_20260627/02_schema/prompts/`에 있습니다. 실제 LLM 호출 시에는 이 파일의 조건별 지시문에 chunk 문장, sentence id, 허용 node type, 허용 edge predicate, JSON schema, strict JSON contract가 결합되었습니다.

### 6.1 제안 방법론 프롬프트 파일 원문

`P_cape_kg.txt`에 저장된 핵심 지시문은 다음입니다.

```text
Use CQ-linked schema retrieval, procedural frame extraction, evidence-span constrained relation extraction, span verification, ontology validation, procedural consistency checks, and active review scoring.
```

### 6.2 실제 runtime prompt의 핵심 구조

실제 실행 시에는 다음 요소가 함께 들어갔습니다.

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

`P_cape_kg_actual` 조건에는 추가로 다음이 포함되었습니다.

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

출력 JSON shape는 다음 세 배열입니다.

```json
{
  "nodes": [],
  "edges": [],
  "mappings": []
}
```

따라서 제안 방법론 프롬프트는 CQ, evidence, schema, validator, NCS/PCF mapping을 동시에 강제하는 조건입니다.

---

## 7. 프롬프트 조건별 산출물 차이

| 조건 | 목적 | 요구 산출물 |
| --- | --- | --- |
| `B0_plain_llm` | schema 없이 SPO triple 추출 | `triples` |
| `B1_predicate_constrained` | 허용 predicate만 사용 | `edges` |
| `B2_current_project` | task frame 후 Layer 2 schema 후처리 | `nodes`, `edges` |
| `B3_edc_style` | open-schema item 추출 후 CAPE 호환 변환 | `nodes`, `edges` |
| `B4_taxonomy_rag` | NCS/PCF/task taxonomy snippet 활용 | `nodes`, `edges`, `mappings` |
| `B5_procedural_prompt` | action, actor, gateway, artifact flow 추출 | `nodes`, `edges` |
| `B6_sac_kg_verifier_pruner` | schema/evidence verifier-pruner approximation | `nodes`, `edges` |
| `P_cape_kg_actual` | CQ + evidence + schema + validator + bridge | `nodes`, `edges`, `mappings` |
| `P_minus_CQ` | 제안 방법론에서 CQ anchoring 제거 | `nodes`, `edges`, `mappings` |
| `P_minus_Evidence` | evidence 요구 약화 | `nodes`, `edges`, `mappings` |
| `P_minus_Procedural_schema` | 절차형 schema 제거 | `nodes`, `edges`, `mappings` |
| `P_minus_Validator` | validator rejection 완화 | `nodes`, `edges`, `mappings` |
| `P_minus_Standard_bridge` | NCS/PCF bridge 제거 | `nodes`, `edges` |
| `P_minus_Schema_retrieval` | chunk-specific retrieval 제거 | `nodes`, `edges`, `mappings` |

핵심은 같은 LLM을 쓰더라도 프롬프트 조건이 다르면 산출물 구조가 다르다는 점입니다. B0는 graph node/edge가 아니라 자유 triple이고, 제안 방법론은 node, edge, mapping을 함께 요구합니다.

---

## 8. Node는 어떻게 산출했는가

최종 `outputs/07_layer2_graph/layer2_nodes.jsonl`의 node는 LLM raw output을 그대로 저장한 것이 아닙니다. OCR evidence anchor, task seed, 용어 사전, 절차 템플릿, schema constraint를 이용해 조립한 rule/schema/evidence 기반 node입니다.

Node 생성 흐름:

1. OCR sentence를 evidence anchor로 변환
2. `TASK_SEEDS`의 label, alias, keyword로 관련 sentence 검색
3. 관련 sentence에서 artifact, role, decision, principle, risk 후보를 용어 사전으로 추출
4. 각 task frame을 `DomainTask` node로 생성
5. task별 절차 템플릿 또는 입력/산출물 기반 추론으로 `ProcedureStep` node 생성
6. 산출물이 다음 업무로 이어지는 경우 `ArtifactFlow` node 생성
7. `node_id` 기준으로 중복 제거
8. 모든 node에 evidence와 review status 부여

Node type별 결과:

| Node type | 개수 | 생성 방식 |
| --- | ---: | --- |
| `ProcedureStep` | 99 | task별 절차 템플릿 또는 입력/산출물 기반 step 추론 |
| `DomainTask` | 22 | task seed label/alias/keyword와 evidence sentence 매칭 |
| `Artifact` | 14 | 입력물/산출물 용어 매칭 |
| `GuardCondition` | 13 | 의사결정 evidence에서 조건 표현 추출 |
| `Role` | 10 | 수행자/책임 주체 용어 매칭 |
| `ArtifactFlow` | 9 | 산출물이 다음 task 입력으로 쓰이는 규칙 |
| `Principle` | 5 | 원칙/품질 기준 용어 매칭 |
| `DecisionGateway` | 4 | 의사결정 관련 용어 매칭 |
| `Risk` | 3 | 위험/실패 가능성 용어 매칭 |

---

## 9. Edge는 어떻게 산출했는가

최종 `outputs/07_layer2_graph/layer2_edges.jsonl`의 edge는 source node, target node, predicate, evidence가 모두 검증된 관계만 남긴 것입니다.

Edge 생성 흐름:

1. task frame의 `inputs`, `outputs`, `roles`, `principles`, `risks` slot을 predicate로 변환
2. decision gateway와 guard condition을 별도 predicate로 연결
3. task와 step은 `HAS_STEP`으로 연결
4. step 순서는 `PRECEDES`로 연결
5. artifact flow는 `FEEDS_INTO`, `USED_AS_INPUT_FOR`로 연결
6. 모든 edge를 schema-valid triple record로 변환하고 `source_triple_ids`를 부여
7. allowed predicate, source/target node 존재, evidence 존재 조건을 통과한 edge만 최종 저장

Predicate별 결과:

| Predicate | 개수 | 생성 방식 |
| --- | ---: | --- |
| `PRODUCES` | 220 | task/step의 outputs slot을 Artifact node로 연결 |
| `USES_INPUT` | 201 | task/step의 inputs slot을 Artifact 또는 Concept node로 연결 |
| `PERFORMED_BY` | 120 | task/step의 roles slot을 Role node로 연결 |
| `HAS_STEP` | 99 | DomainTask를 ProcedureStep 목록에 연결 |
| `PRECEDES` | 77 | 같은 task 안에서 step order 기준 순서 연결 |
| `HAS_PRINCIPLE` | 64 | task/step의 principle slot 연결 |
| `HAS_DECISION_GATEWAY` | 54 | task/step에서 발견된 decision node 연결 |
| `HAS_RISK` | 39 | task/step의 risk slot 연결 |
| `HAS_GUARD_CONDITION` | 14 | DecisionGateway와 GuardCondition 연결 |
| `FEEDS_INTO` | 9 | Artifact가 다음 task로 흘러가는 규칙 |
| `USED_AS_INPUT_FOR` | 9 | Artifact가 다음 task 입력으로 쓰이는 규칙 |

검증 결과:

| 검증 항목 | 결과 |
| --- | ---: |
| Final Layer 2 edges | 906 |
| Evidence가 있는 edges | 906 / 906 |
| `source_triple_ids`가 있는 edges | 906 / 906 |
| Dangling edges | 0 |
| Type violations | 0 |

---

## 10. LLM은 어디에 사용했는가

LLM은 사용했습니다. 다만 최종 KG를 그대로 생성하는 단일 도구로 쓴 것이 아니라, 여러 prompt/method 조건에서 후보 생성 결과를 비교하는 실험용 generator로 사용했습니다.

| 구분 | 최종 KG 구축 | LLM 실험 |
| --- | --- | --- |
| 목적 | 현재 데이터에 대한 evidence-grounded KG build | 조건별 후보 생성 성능 비교 |
| 입력 | 전체 OCR/evidence, schema, task seeds, rules | 120개 evaluation chunks |
| 출력 | 179 nodes, 906 edges | 조건별 triples/nodes/edges/mappings |
| 검증 | structural validation, evidence validation | JSON parse, schema, evidence id validation |
| claim 상태 | KG 구축 완료 | silver/proxy diagnostic |

사용한 주요 모델:

| 모델 | 역할 | 현재 상태 |
| --- | --- | --- |
| Qwen3-8B | 기본 local baseline/proposed/ablation | 실행 완료 |
| Qwen3-14B | 더 강한 local core diagnostic | 실행 완료 |
| Qwen3-32B-AWQ | 가장 큰 현실적 local core diagnostic | 120 chunk core run 완료 |

---

## 11. 현재 LLM 진단 결과

이 표는 human-gold final performance가 아니라 silver/proxy diagnostic입니다.

| 모델 | 조건 | Rows | Exact edge F1 | Predicate F1 | Node F1 | Evidence F1 |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Qwen3-8B | `P_cape_kg_actual` | 120 | 0.0018 | 0.0482 | 0.0326 | 0.0655 |
| Qwen3-14B | `P_cape_kg_actual` | 120 | 0.0017 | 0.0601 | 0.0298 | 0.0610 |
| Qwen3-32B-AWQ | `P_cape_kg_actual` | 120 | 0.0034 | 0.0662 | 0.0284 | 0.0542 |

해석:

- 32B-AWQ는 8B보다 silver predicate F1과 exact edge F1이 일부 개선되었습니다.
- 그러나 evidence F1은 8B보다 낮습니다.
- 따라서 "큰 모델일수록 항상 좋다"는 식의 claim은 하면 안 됩니다.
- 현재 필요한 다음 단계는 추가 GPU 실험보다 human-gold 평가입니다.

---

## 12. 구조 진단 결과

| 항목 | 값 |
| --- | ---: |
| Ontology conformance rate | 1.0000 |
| Domain/range violations | 0 |
| Dangling edges | 0 |
| Evidence-missing edges | 0 |
| Procedural consistency rate | 0.9950 |
| PRECEDES cycle count | 0 |
| Artifact-flow direction violations | 0 |
| CQ answerability rate | 0.9167 |
| Answerable CQs | 11 / 12 |

주의할 점:

- CQ8, 즉 `HAS_REVIEW_CHECKPOINT`는 현재 structural support count가 0입니다.
- 이것은 자동으로 임의 edge를 추가하지 않고, structural gap으로 남겨 human review 대상으로 넘긴 상태입니다.

---

## 13. 현재까지 실행한 실험/산출물

| 범주 | 실행 상태 | 대표 파일 |
| --- | --- | --- |
| OCR evidence anchor 생성 | 완료 | `outputs/02_evidence/evidence_anchors.jsonl` |
| CQ/schema 정의 | 완료 | `experiments/cape_kg_eacl_20260627/02_schema/competency_questions.json` |
| Layer 1 NCS/PCF KG | 완료 | `outputs/01_layer1_*` |
| Layer 2 업무 KG | 완료 | `outputs/07_layer2_graph/layer2_nodes.jsonl`, `outputs/07_layer2_graph/layer2_edges.jsonl` |
| NCS/PCF mapping 후보 | 완료 | `outputs/08_mapping/l2_ncs_mapping_candidates.jsonl`, `outputs/08_mapping/l2_pcf_mapping_candidates.jsonl` |
| KG 시각화 | 완료 | `outputs/09_visualization/kg_viewer.html` |
| Neo4j import CSV | 완료 | `outputs/11_neo4j_import/` |
| LLM baseline/proposed | 완료 | `experiments/cape_kg_eacl_20260627/49_qwen3_8b_strict_json_1200_full_valid.jsonl` |
| Ablation | 완료 | `experiments/cape_kg_eacl_20260627/49_qwen3_8b_cape_ablation_120_valid.jsonl` |
| Model scaling | 완료 | `experiments/cape_kg_eacl_20260627/06_release/qwen3_model_scaling_report.md` |
| Public benchmark adapter | 완료 | `experiments/cape_kg_eacl_20260627/08_public_benchmarks/public_benchmark_adapter_report.md` |
| Structural diagnostics | 완료 | `experiments/cape_kg_eacl_20260627/04_evaluation/structural_evaluation_report.md` |
| Human-review handoff | 준비 완료 | `experiments/cape_kg_eacl_20260627/06_release/human_review_handoff/` |
| Pre-human validation | PASS | `experiments/cape_kg_eacl_20260627/06_release/pre_human_handoff_validation.md` |

---

## 14. 현재 claim 가능/불가능한 것

| 주장 | 현재 가능 여부 | 이유 |
| --- | --- | --- |
| Layer 1 NCS/PCF KG를 구축했다 | 가능 | 자동 구축 산출물 존재 |
| Layer 2 업무 KG를 구축했다 | 가능 | 179 nodes, 906 edges, evidence/dangling/type 검증 완료 |
| 모든 accepted Layer 2 edge에 evidence가 있다 | 가능 | evidence-missing edges 0 |
| KG가 12개 CQ 중 11개를 구조적으로 답할 수 있다 | 가능하되 structural diagnostic으로 표현 | human-gold 성능 claim은 아님 |
| LLM baseline/proposed/ablation/model scaling을 실행했다 | 가능 | valid output 및 report 존재 |
| Qwen3-32B-AWQ가 최종적으로 가장 좋다 | 불가능 | silver/proxy 기준 일부 개선일 뿐 human-gold 아님 |
| CAPE-KG가 기존 방법보다 성능이 우수하다 | 아직 불가능 | human-gold final F1/precision/recall 필요 |
| NCS/PCF mapping이 정확하다 | 아직 불가능 | expert review 미완료 |
| active review가 annotation 비용을 줄인다 | 아직 불가능 | 실제 human timing/correction evidence 필요 |

---

## 15. 남은 작업

논문 main table을 확정하려면 다음이 필요합니다.

| 남은 작업 | 목적 |
| --- | --- |
| 100 chunk two-annotator annotation | human-gold 생성 |
| IAA 계산 | annotator 간 일치도 확인 |
| adjudication | 최종 gold node/edge/evidence 확정 |
| 500+ gold item 확보 | minimum paper gate 충족 |
| NCS/PCF mapping expert review | standard bridge 평가 |
| NCS-PCF crosswalk expert review | crosswalk utility 평가 |
| active-review effort 기록 | active review 효율성 claim |
| final human-gold scoring | 최종 main table 생성 |

현재 pre-human handoff validation은 `PASS`입니다. 다만 claim gate는 human-gold가 없기 때문에 의도적으로 `FAIL` 상태입니다. 이것은 실험 실패가 아니라, 아직 주장하면 안 되는 결과를 막기 위한 보수적 gate입니다.

---

## 16. 발표 때 사용할 수 있는 최종 정리 멘트

> 현재까지는 한국어 수주/제안 업무 문서에서 evidence-grounded procedural KG를 구축하는 전체 파이프라인을 만들었고, Layer 1 NCS/PCF KG와 Layer 2 업무 KG 구축, NCS/PCF mapping 후보, LLM baseline/proposed/ablation/model-scaling, 구조 진단, human-review handoff까지 완료했습니다. 핵심 방법론은 CQ로 KG가 답해야 할 질문을 고정하고, procedural schema와 evidence anchor, validator를 통해 node와 edge를 통제된 방식으로 생성하는 것입니다. 다만 논문에서 성능 우수성을 주장하려면 human-gold annotation과 expert review가 아직 필요하므로, 현재 결과는 구축 완료 및 진단 결과로 보고하고 final main table은 사람 검수 이후 확정하는 것이 맞습니다.

---

## 17. 가장 중요한 파일

| 용도 | 파일 |
| --- | --- |
| 긴 발표 원고 | `experiments/cape_kg_eacl_20260627/07_reports/professor_report_slide_contents_current_20260628_ko.md` |
| 이 핵심 요약본 | `experiments/cape_kg_eacl_20260627/07_reports/professor_report_key_summary_separate_from_slides_20260629_ko.md` |
| prompt/node/edge traceability | `experiments/cape_kg_eacl_20260627/06_release/prompt_node_edge_traceability.md` |
| claimable main table | `experiments/cape_kg_eacl_20260627/06_release/claimable_main_table.md` |
| pre-human validation | `experiments/cape_kg_eacl_20260627/06_release/pre_human_handoff_validation.md` |
| Qwen3 model scaling | `experiments/cape_kg_eacl_20260627/06_release/qwen3_model_scaling_report.md` |
| structural evaluation | `experiments/cape_kg_eacl_20260627/04_evaluation/structural_evaluation_report.md` |
| final KG nodes | `outputs/07_layer2_graph/layer2_nodes.jsonl` |
| final KG edges | `outputs/07_layer2_graph/layer2_edges.jsonl` |
