# 교수님 보고용 핵심 요약본

Generated: 2026-06-29  
Related full slide draft: `experiments/cape_kg_eacl_20260627/07_reports/professor_report_slide_contents_current_20260628_ko.md`  
Related detailed summary: `experiments/cape_kg_eacl_20260627/07_reports/professor_report_core_summary_separate_from_slides_latest_20260629_ko.md`  
Experiment directory: `experiments/cape_kg_eacl_20260627`  
KG output directory: `outputs`

이 문서는 기존 장문 슬라이드 원고와 별개로, 교수님께 **핵심 내용만 빠르게 보고**하기 위한 압축본입니다.

---

## 1. 한 문장 결론

본 연구는 한국어 수주/제안 업무 문서에서 업무 절차, 입력/산출물, 수행 역할, 의사결정 조건, 위험, 원문 근거를 함께 표현하는 **evidence-grounded procedural KG**를 구축하고, 이를 LLM baseline, ablation, model scaling, human-review gate로 평가 가능한 연구 문제로 정리한 실험입니다.

핵심 주의점:

> KG 구축과 자동 진단 인프라는 완료되었지만, 논문에서 최종 성능 우수성을 주장하려면 human-gold annotation, IAA, adjudication, expert review가 아직 필요합니다.

---

## 2. 현재까지 나온 주요 결과

| 항목 | 현재 결과 | 의미 |
| --- | ---: | --- |
| OCR clean sentences | 5,009 | 원문 근거 sentence anchor |
| Layer 2 source chunks | 214 | 업무 문서 chunk |
| LLM evaluation chunks | 120 | baseline/proposed/ablation 비교 대상 |
| Layer 1 NCS nodes | 4,109 | NCS 표준 taxonomy 축 |
| Layer 1 PCF nodes | 5,301 | PCF 표준 taxonomy 축 |
| Canonical DomainTask | 22 | 수주/제안 업무 단위 |
| Layer 2 nodes | 179 | 최종 업무 KG node |
| Layer 2 edges | 906 | 최종 업무 KG edge |
| Schema-valid triples | 906 | edge 검증용 SPO/evidence 중간 표현 |
| NCS mapping candidates | 110 | 22 tasks x Top-5 |
| PCF mapping candidates | 110 | 22 tasks x Top-5 |
| Evidence-missing accepted edges | 0 | 최종 edge evidence 누락 없음 |
| Dangling edges / type violations | 0 / 0 | 구조 검증 통과 |

핵심 파일:

| 목적 | 파일 |
| --- | --- |
| 최종 Layer 2 nodes | `outputs/07_layer2_graph/layer2_nodes.jsonl` |
| 최종 Layer 2 edges | `outputs/07_layer2_graph/layer2_edges.jsonl` |
| NCS mapping 후보 | `outputs/08_mapping/l2_ncs_mapping_candidates.jsonl` |
| PCF mapping 후보 | `outputs/08_mapping/l2_pcf_mapping_candidates.jsonl` |
| KG 시각화 | `outputs/09_visualization/kg_viewer.html` |
| 최종 build report | `outputs/10_evaluation/final_build_report.md` |
| prompt/node/edge traceability | `experiments/cape_kg_eacl_20260627/06_release/prompt_node_edge_traceability.md` |

---

## 3. 방법론 핵심

CAPE-KG는 LLM에게 자유롭게 triple을 만들게 한 방식이 아니라, 다음 제약을 결합한 구축 방법론입니다.

| 구성 요소 | 역할 |
| --- | --- |
| Competency Questions | KG가 답해야 하는 업무 질문을 먼저 정의 |
| Procedural schema | `DomainTask`, `ProcedureStep`, `Artifact`, `Role`, `DecisionGateway`, `GuardCondition` 등으로 업무 구조화 |
| Evidence grounding | 모든 accepted node/edge/mapping을 원문 sentence evidence에 연결 |
| Schema/validator | 허용 node type, predicate, domain/range, evidence 조건 검증 |
| Standard bridge | Layer 2 업무 KG를 NCS/PCF 표준 taxonomy와 연결 |
| Human-review gate | 사람 검수 전 최종 성능 claim을 막는 안전장치 |

실행 흐름:

1. OCR workbook을 sentence 단위로 정제하고 evidence anchor 부여
2. NCS/PCF 표준 데이터를 Layer 1 KG로 구축
3. 수주/제안 업무 문서를 Layer 2 chunk로 분할
4. CQ와 procedural schema 정의
5. task seed, alias, keyword, evidence sentence로 `DomainTask` 생성
6. procedure template, 입력/산출물/역할/조건 단서로 node 생성
7. predicate별 규칙과 evidence 조건으로 edge 생성
8. Layer 2 KG를 NCS/PCF Top-K 후보와 연결
9. LLM baseline/proposed/ablation/model scaling 실행
10. human review handoff와 claim gate 생성

---

## 4. 어떤 프롬프트로 무엇을 산출했는가

프롬프트 파일 위치:

`experiments/cape_kg_eacl_20260627/02_schema/prompts/`

실제 LLM 호출은 조건별 prompt 원문에 runtime template, chunk sentence, sentence ID, allowed schema, JSON output shape, strict JSON contract를 결합해서 실행했습니다.

공통 runtime 제약:

```text
Return ONLY one valid JSON object. No markdown. No explanation.
Every extracted item must include at least one evidence_anchor_ids value from the chunk.
Do not use outside knowledge. Keep Korean labels when the source text is Korean.
```

Qwen strict JSON 실행 제약:

```text
Strict JSON contract:
- Return exactly one JSON object and nothing else.
- Do not include markdown, code fences, comments, XML tags, <think> blocks, prose, or explanations.
- For Qwen/Qwen-style chat models, obey /no_think; do not emit hidden or visible reasoning.
```

조건별 핵심 prompt와 산출물:

| 조건 | 실제 prompt 핵심 문장 | 요구 산출물 |
| --- | --- | --- |
| `B0_plain_llm` | `Extract subject-predicate-object triples from the chunk. Return JSON only.` | `triples` |
| `B1_predicate_constrained` | `Extract triples using only the allowed predicates. Return JSON only with evidence sentence ids.` | `edges` |
| `B2_current_project` | `Extract Task Frames, then triples, then post-process into the Layer2 schema.` | `nodes`, `edges` |
| `B3_edc_style` | `Extract, define, and canonicalize open-schema KG items, then emit CAPE-compatible nodes and edges for scoring.` | `nodes`, `edges` |
| `B4_taxonomy_rag` | `Retrieve NCS/PCF/task taxonomy snippets, then extract schema-constrained triples with evidence.` | `nodes`, `edges`, `mappings` |
| `B5_procedural_prompt` | `Extract actions, actors, gateways, guard conditions, artifact flows, and temporal/logical dependencies.` | `nodes`, `edges` |
| `B6_sac_kg_verifier_pruner` | `Use existing generator candidates, then apply schema/evidence verification and pruning in the style of SAC-KG.` | `nodes`, `edges` |
| `P_cape_kg_actual` | `Use CQ-linked schema retrieval, procedural frame extraction, evidence-span constrained relation extraction, span verification, ontology validation, procedural consistency checks, and active review scoring.` | `nodes`, `edges`, `mappings` |

`P_cape_kg_actual`은 CQ anchoring, evidence grounding, procedural schema, validator, NCS/PCF bridge를 동시에 반영한 제안 방법론 조건입니다.

---

## 5. CQ는 어떻게 생성했고, 무엇을 의미하는가

CQ는 LLM이 자동 생성한 질문이 아니라, 연구자가 먼저 정의한 **KG 요구사항**입니다. 즉, "이 KG가 어떤 업무 질문에 답할 수 있어야 하는가"를 정하고, 각 질문을 필요한 node type과 edge predicate에 연결했습니다.

CQ 생성 방식:

| 단계 | 내용 |
| --- | --- |
| 1 | 연구 문제를 "한국어 수주/제안 업무 문서 기반 procedural KG construction"으로 정의 |
| 2 | 업무 사용자가 실제로 물을 질문 범주를 정리 |
| 3 | 질문을 node type과 predicate에 연결 |
| 4 | 같은 CQ를 schema, prompt, ablation, structural evaluation에서 재사용 |

대표 CQ:

| CQ | 질문 | 연결 predicate/schema |
| --- | --- | --- |
| CQ1 | 수주·제안 업무는 어떤 주요 Task와 절차 단계로 구성되는가? | `HAS_STEP`, `PRECEDES` |
| CQ2 | 각 Task는 어떤 입력 자료를 사용하는가? | `USES_INPUT`, `Artifact` |
| CQ3 | 각 Task는 어떤 산출물을 생성하는가? | `PRODUCES`, `Artifact` |
| CQ4 | 각 Task는 누가 수행하거나 책임지는가? | `PERFORMED_BY`, `Role` |
| CQ5 | 어떤 의사결정 지점이 존재하는가? | `HAS_DECISION_GATEWAY`, `DecisionGateway` |
| CQ6 | 의사결정에는 어떤 조건이나 판단 기준이 필요한가? | `HAS_GUARD_CONDITION`, `GuardCondition` |
| CQ7 | 산출물은 다음 업무에서 어떻게 사용되는가? | `FEEDS_INTO`, `USED_AS_INPUT_FOR` |
| CQ10 | 각 지식 항목은 원문 어느 chunk/page/span에 근거가 있는가? | evidence anchor |
| CQ11 | 특정 업무는 어떤 NCS 능력단위와 관련되는가? | NCS mapping candidates |
| CQ12 | 특정 업무는 PCF 프로세스 체계상 어디에 위치하는가? | PCF mapping candidates |

요약하면 CQ가 있었기 때문에 task, step, input, output, role, decision, risk, evidence, NCS/PCF mapping을 모두 graph schema 안에 넣을 수 있었습니다.

---

## 6. Node는 어떻게 산출했는가

최종 node 파일:

`outputs/07_layer2_graph/layer2_nodes.jsonl`

최종 node는 LLM raw output을 그대로 저장한 것이 아니라, OCR evidence, task seed, alias/keyword, 용어 사전, procedure template, schema constraint를 이용해 조립했습니다.

Node 생성 흐름:

1. OCR sentence를 `EA-*` evidence anchor로 변환
2. `TASK_SEEDS`의 업무 label, alias, keyword로 관련 sentence 검색
3. sentence 안에서 artifact, role, decision, principle, risk 후보 추출
4. 관련 evidence가 있는 업무를 `DomainTask` node로 생성
5. task별 procedure template 또는 입력/산출물 단서로 `ProcedureStep` node 생성
6. 산출물이 다음 업무 입력으로 흐르는 경우 `ArtifactFlow` node 생성
7. `node_id` 기준으로 중복 제거
8. 모든 node에 evidence와 review status 부여

Node type별 결과:

| Node type | 개수 | 생성 방식 |
| --- | ---: | --- |
| `ProcedureStep` | 99 | task별 procedure template 또는 입력/산출물 기반 step 추론 |
| `DomainTask` | 22 | task seed label/alias/keyword와 evidence sentence 매칭 |
| `Artifact` | 14 | 입력물/산출물 용어 매칭 |
| `GuardCondition` | 13 | 의사결정 evidence에서 조건 표현 추출 |
| `Role` | 10 | 수행자/책임 주체 용어 매칭 |
| `ArtifactFlow` | 9 | 산출물이 다음 업무 입력으로 쓰이는 흐름 규칙 |
| `Principle` | 5 | 원칙/품질 기준 용어 매칭 |
| `DecisionGateway` | 4 | 의사결정 관련 표현 매칭 |
| `Risk` | 3 | 위험/실패 가능성 표현 매칭 |
| 합계 | 179 |  |

---

## 7. Edge는 어떻게 산출했는가

최종 edge 파일:

`outputs/07_layer2_graph/layer2_edges.jsonl`

Edge는 node 사이 업무 관계를 나타냅니다. 최종 graph에 들어가려면 source node와 target node가 실제로 존재해야 하고, predicate가 허용 목록에 있어야 하며, evidence anchor가 있어야 합니다.

Edge 생성 흐름:

1. task frame의 `inputs`, `outputs`, `roles`, `principles`, `risks` slot을 predicate로 변환
2. decision gateway와 guard condition을 별도 edge로 연결
3. procedure step은 `HAS_STEP`, step 순서는 `PRECEDES`로 연결
4. artifact flow는 `FEEDS_INTO`, `USED_AS_INPUT_FOR`로 연결
5. edge를 triple record로 변환하고 `source_triple_ids` 부여
6. source/target 존재, allowed predicate, evidence 존재 여부 검증
7. 검증을 통과한 edge만 최종 `layer2_edges.jsonl`에 저장

Predicate별 edge 수:

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

검증 결과:

| 검증 항목 | 결과 |
| --- | ---: |
| Evidence가 있는 edges | 906 / 906 |
| `source_triple_ids`가 있는 edges | 906 / 906 |
| Dangling edges | 0 |
| Type violations | 0 |

---

## 8. LLM은 무엇에 사용했는가

LLM은 최종 KG를 무검증으로 직접 만든 도구가 아니라, 같은 120개 evaluation chunks에서 baseline/proposed/ablation 조건이 어떤 후보 JSON을 생성하는지 비교하기 위해 사용했습니다.

실행 모델:

| 모델 | 사용 목적 | 상태 |
| --- | --- | --- |
| Qwen3-8B | 기본 baseline/proposed/ablation | 실행 완료 |
| Qwen3-14B | model scaling core conditions | 실행 완료 |
| Qwen3-32B-AWQ | 현실적인 대형 모델 scaling | 120 chunk core run 완료 |

실험 조건:

| 범주 | 조건 |
| --- | --- |
| Baseline | `B0_plain_llm`, `B1_predicate_constrained`, `B2_current_project`, `B3_edc_style`, `B4_taxonomy_rag`, `B5_procedural_prompt`, `B6_sac_kg_verifier_pruner` |
| Proposed | `P_cape_kg_actual` |
| Ablation | `P_minus_CQ`, `P_minus_Evidence`, `P_minus_Procedural_schema`, `P_minus_Validator`, `P_minus_Standard_bridge`, `P_minus_Schema_retrieval` |
| Scaling | Qwen3-8B, Qwen3-14B, Qwen3-32B-AWQ |

중요한 해석:

- LLM output 수량은 성능 우수성을 뜻하지 않습니다.
- 현재 LLM 평가는 human-gold 전 silver/proxy diagnostic입니다.
- final main performance table은 사람이 검수한 gold label 이후에만 확정할 수 있습니다.

---

## 9. 현재 주장 가능한 것과 아직 주장하면 안 되는 것

| 구분 | 현재 말할 수 있는 것 | 아직 말하면 안 되는 것 |
| --- | --- | --- |
| KG 구축 | Layer 1 NCS/PCF와 Layer 2 업무 KG 구축 완료 | human-gold 대비 최종 성능 우수성 |
| Evidence | 최종 accepted edge 906개 모두 evidence 보유 | evidence span 정확도가 human-gold에서 높다는 claim |
| LLM 실험 | baseline/proposed/ablation/model scaling 실행 완료 | proposed method가 최종적으로 baseline보다 우수하다는 claim |
| Mapping | NCS/PCF Top-K 후보 생성 완료 | expert review 기준 P@K/MRR/nDCG 우수성 |
| Active review | queue와 template 준비 완료 | 실제 사람 검수 시간이 줄었다는 efficiency claim |
| 논문 준비 | claim gate와 release validation 준비 | EACL 제출용 final main table 완료 |

발표에서 안전한 표현:

> 현재까지는 KG 구축과 실험 인프라 구축이 완료되었고, 최종 성능 claim을 위해 human-gold annotation과 expert review를 진행해야 하는 단계입니다.

피해야 할 표현:

> CAPE-KG가 baseline보다 최종적으로 성능이 높다.

이 표현은 human-gold scoring 이후에만 가능합니다.

---

## 10. 다음 단계

| 우선순위 | 작업 | 산출물 |
| --- | --- | --- |
| 1 | Annotator A/B가 priority 100 chunks 검수 | reviewed JSONL |
| 2 | IAA 계산 | agreement report |
| 3 | adjudication 수행 | adjudicated gold JSONL |
| 4 | proposed/baseline human-gold scoring | final main table |
| 5 | NCS/PCF mapping expert review | P@K, MRR, nDCG |
| 6 | active-review effort 기록 | active review efficiency table |

교수님께 보고할 때의 마지막 문장:

> 지금 단계의 핵심 성과는 "한국어 수주/제안 업무 문서를 evidence-grounded procedural KG로 재현 가능하게 구축했다"는 점이고, 논문 성능 주장은 사람 검수 이후 final main table로 확정하겠습니다.
