# 교수님 보고용 발표자료 슬라이드 원고

Generated: 2026-06-29  
Experiment directory: `experiments/cape_kg_eacl_20260627`  
KG output directory: `outputs`

이 문서는 PPT 파일이 아니라, 교수님 보고 발표자료에 그대로 옮길 수 있도록 작성한 **슬라이드별 내용 원고**입니다. 각 슬라이드는 `핵심 메시지`, `슬라이드에 넣을 내용`, `발표 멘트`로 구성했습니다.

핵심 내용만 빠르게 보고하기 위한 별도 요약본은 다음 파일로 정리했습니다.

- `experiments/cape_kg_eacl_20260627/07_reports/professor_report_core_contents_separate_20260629_ko.md`
- `experiments/cape_kg_eacl_20260627/07_reports/professor_report_core_brief_prompt_cq_node_edge_current_20260629_ko.md`

가장 중요한 보고 원칙은 다음입니다.

> 현재까지는 한국어 수주/제안 업무 문서에 대해 Layer 1 표준 KG, Layer 2 업무 KG, evidence grounding, NCS/PCF mapping 후보, NCS-PCF crosswalk 후보, LLM baseline/ablation/model-scaling, public benchmark adapter, structural diagnostics, human-review handoff까지 구축 및 실행했습니다. 다만 논문에서 최종 성능 우수성을 주장하려면 human-gold annotation, IAA, adjudication, mapping expert review, NCS-PCF crosswalk expert review, active-review effort evidence가 아직 필요합니다.

따라서 발표에서는 **KG 구축 완료**와 **최종 성능 claim 미완료**를 분리해서 설명해야 합니다.

이번 업데이트에서는 특히 다음 세 가지를 별도로 설명할 수 있게 보강했습니다.

1. 어떤 프롬프트/실험 조건으로 어떤 JSON 산출물을 만들었는가
2. 최종 Layer 2 KG의 node는 어떤 규칙과 evidence로 생성되었는가
3. 최종 Layer 2 KG의 edge는 어떤 predicate, source/target node, evidence 조건으로 생성되었는가

---

## Slide 1. 제목

### 핵심 메시지
한국어 수주/제안 업무 문서에서 근거 기반 절차형 지식그래프를 구축하고, 이를 평가 가능한 NLP 연구 문제로 재정의했습니다.

### 슬라이드에 넣을 내용
- 제목: **CAPE-KG: 한국어 수주/제안 업무 문서 기반 Evidence-Grounded Procedural KG 구축**
- 부제:
  - OCR 기반 업무 문서에서 task, step, role, input/output, decision, risk를 구조화
  - 각 node/edge를 원문 sentence evidence에 연결
  - NCS/PCF 표준 taxonomy와 Layer 2 업무 KG를 연결
  - LLM baseline, ablation, model scaling, human-review handoff까지 실행

### 발표 멘트
이번 연구는 단순히 내부 업무 온톨로지를 만든 것이 아니라, 한국어 장문 업무 문서에서 절차형 업무 지식을 근거와 함께 추출하고 검증 가능한 KG로 구성하는 방법론입니다.

---

## Slide 2. 현재까지의 한 장 요약

### 핵심 메시지
자동 구축과 실험 인프라는 대부분 완료되었고, 최종 논문 성능표는 사람 검수 이후 확정해야 합니다.

### 슬라이드에 넣을 내용
| 항목 | 현재 상태 | 발표 가능 표현 |
| --- | --- | --- |
| Layer 1 NCS KG | 완료 | NCS taxonomy 기반 표준축 구축 |
| Layer 1 PCF KG | 완료 | PCF taxonomy 기반 표준축 구축 |
| Layer 2 업무 KG | 완료 | 수주/제안 업무 procedural KG 구축 |
| Evidence grounding | 완료 | accepted edge evidence 100% |
| NCS/PCF mapping 후보 | 완료 | Top-K 후보 생성, expert review 전 |
| LLM baseline/proposed/ablation | 실행 완료 | 120 evaluation chunks 기준 실행 |
| Model scaling | 실행 완료 | Qwen3-8B, Qwen3-14B, Qwen3-32B-AWQ |
| Public benchmark adapter | 실행 완료 | PAGED/Text2KG subset 진단 |
| Human review handoff | 준비 완료 | minimum paper-gate 반환 11개, optional/strong 반환 3개 추적 |
| Claim gate | FAIL | expected fail, human-gold 미완료 때문 |

### 발표 멘트
여기서 Claim gate FAIL은 실험 실패가 아닙니다. 아직 사람이 검수한 gold label이 없기 때문에 silver/proxy 결과를 최종 성능 claim으로 쓰지 못하게 막는 안전장치입니다.

---

## Slide 3. 연구 방향의 핵심 전환

### 핵심 메시지
연구를 "업무 KG 구축 사례"에서 "평가 가능한 evidence-grounded procedural KG construction task"로 전환했습니다.

### 슬라이드에 넣을 내용
| 기존 관점 | 수정된 연구 관점 |
| --- | --- |
| 수주/제안 업무 온톨로지 구축 | 한국어 업무 문서 기반 procedural KG construction |
| 내부 데이터 정리 | evidence-grounded KG extraction task |
| LLM으로 triple 생성 | CQ, schema, evidence, validator로 통제된 추출 |
| 후처리 mapping | NCS/PCF standard bridge |
| 결과물 중심 | baseline, ablation, model scaling, human-gold 평가 중심 |

### 발표 멘트
방법론의 핵심을 버린 것이 아니라, 학회 논문에서 평가 가능한 형태로 framing을 바꿨습니다. 핵심은 "업무 지식을 만들었다"가 아니라 "근거 기반 절차형 KG를 어떻게 안정적으로 구축하고 평가할 것인가"입니다.

---

## Slide 4. 연구 문제

### 핵심 메시지
한국어 장문 업무 문서에서 업무 절차 지식을 신뢰 가능한 KG로 만드는 문제입니다.

### 슬라이드에 넣을 내용
연구 질문:

1. 업무 task, step, role, artifact, decision, risk를 어떤 schema로 표현할 것인가?
2. 각 node와 edge가 원문 어느 sentence/page/chunk에 근거하는지 어떻게 추적할 것인가?
3. LLM 출력이 schema, predicate, domain/range, evidence 조건을 만족하는지 어떻게 검증할 것인가?
4. 구축된 업무 KG를 NCS/PCF 표준 taxonomy와 어떻게 연결할 것인가?
5. 사람이 검수한 human-gold 기준으로 어떤 성능 claim을 확정할 것인가?

### 발표 멘트
일반적인 entity extraction이 아니라 "업무가 어떤 순서로 수행되고, 무엇을 입력으로 쓰며, 누가 수행하고, 어떤 산출물을 내는가"를 그래프로 표현하는 문제입니다.

---

## Slide 5. 방법론 이름과 구성

### 핵심 메시지
CAPE-KG는 LLM 단독 추출이 아니라, CQ, schema, evidence, validator, standard bridge를 결합한 방법론입니다.

### 슬라이드에 넣을 내용
| 구성 요소 | 역할 |
| --- | --- |
| Competency Questions | KG가 답해야 할 업무 질문 정의 |
| Procedural Schema | DomainTask, ProcedureStep, Artifact, Role, DecisionGateway 등 구조화 |
| Evidence Grounding | node/edge를 OCR sentence evidence anchor에 연결 |
| Validator | predicate, domain/range, evidence, parse 오류 검증 |
| Standard Bridge | Layer 2 업무 KG를 NCS/PCF 표준 taxonomy와 연결 |
| Active Review | 사람이 먼저 봐야 할 오류 가능 항목 우선순위화 |

### 발표 멘트
차별점은 LLM을 사용했다는 점 자체가 아니라, LLM이 만든 결과를 schema와 evidence 조건 안에 넣고 검증 가능한 KG 산출물로 바꿨다는 점입니다.

---

## Slide 5-A. CQ는 어떻게 생성했는가

### 핵심 메시지
Competency Question(CQ)은 LLM이 자동 생성한 것이 아니라, "이 KG가 교수님/연구자/업무 사용자에게 답해야 하는 질문"을 먼저 정하고, 각 질문을 node type과 edge predicate로 연결한 설계 산출물입니다.

### 슬라이드에 넣을 내용
CQ 생성 방식:

1. 연구 문제를 먼저 정의
   - 한국어 수주/제안 업무 문서에서 절차형 업무 지식을 KG로 구축
   - 단순 entity 추출이 아니라 task, step, input/output, role, decision, risk, evidence, standard mapping을 표현
2. 업무 KG가 답해야 할 질문 범주를 설계
   - 업무 구성과 순서
   - 입력 자료와 산출물
   - 수행 역할
   - 의사결정 지점과 조건
   - 산출물 흐름
   - 원문 evidence grounding
   - NCS/PCF 표준 연결
3. 각 질문을 schema 요소에 연결
   - 예: "각 Task는 어떤 산출물을 생성하는가?" -> `PRODUCES`, `Artifact`
   - 예: "의사결정에는 어떤 조건이 필요한가?" -> `HAS_GUARD_CONDITION`, `GuardCondition`
4. 이 CQ 목록을 schema 파일과 LLM prompt, structural evaluation에서 재사용

관련 파일:

| 역할 | 파일 |
| --- | --- |
| 내부 KG build용 CQ | `outputs/03_schema/competency_questions.json` |
| EACL 실험용 CQ | `experiments/cape_kg_eacl_20260627/02_schema/competency_questions.json` |
| CQ 생성 코드 | `scripts/build_ax_epak_internal_kg.py`, `scripts/build_cape_kg_eacl_experiment.py` |
| LLM runtime prompt 내 CQ block | `scripts/run_cape_llm_condition_baselines.py` |

### 발표 멘트
CQ는 "무엇을 뽑을지"를 정하는 연구 설계 장치입니다. 즉, KG schema와 LLM extraction, evaluation이 서로 따로 놀지 않도록 묶어주는 anchor 역할을 합니다.

---

## Slide 5-B. CQ 실제 목록과 예시

### 핵심 메시지
현재 CQ는 12개이며, 절차형 업무 KG 구축과 표준 taxonomy bridge를 모두 커버하도록 설계했습니다.

### 슬라이드에 넣을 내용
EACL 실험에서 사용한 CQ 예시:

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

CQ가 실제로 쓰인 위치:

| 사용 위치 | 사용 방식 |
| --- | --- |
| Schema 설계 | node type과 predicate 목록을 정하는 기준 |
| LLM proposed prompt | `P_cape_kg_actual`에서 competency question block으로 제공 |
| Ablation | `P_minus_CQ`에서 CQ anchoring을 제거해 효과를 비교 |
| Structural evaluation | CQ answerability를 계산하는 기준 |
| 발표/논문 framing | 연구 문제를 "업무 KG 구축"이 아니라 "CQ-anchored procedural KG extraction"으로 설명 |

### 발표 멘트
예를 들어 CQ2와 CQ3이 있기 때문에 input/output artifact를 따로 추출하고, CQ5와 CQ6이 있기 때문에 의사결정 지점과 조건을 별도 node/edge로 표현합니다. CQ11과 CQ12는 Layer 2 업무 KG가 NCS/PCF 표준과 연결되는 이유입니다.

---

## Slide 6. 전체 실행 파이프라인

### 핵심 메시지
OCR 정제부터 KG 구축, LLM 실험, 구조 진단, human handoff까지 재현 가능한 파이프라인으로 실행했습니다.

### 슬라이드에 넣을 내용
1. OCR workbook 정제
2. sentence-level evidence anchor 생성
3. NCS/PCF Layer 1 KG 구축
4. Layer 2 chunk 생성
5. competency question 및 schema 정의
6. task frame 생성
7. procedure/triple 생성
8. Layer 2 graph 조립
9. NCS/PCF mapping 후보 생성
10. HTML/GraphML/Neo4j 시각화 산출물 생성
11. LLM baseline/proposed/ablation 실행
12. model scaling 실행
13. public benchmark adapter 실행
14. structural diagnostics 실행
15. human-gold/mapping/active-review handoff 생성
16. claim gate 및 release bundle 검증

### 발표 멘트
현재 파이프라인은 자동 산출물을 만드는 데서 끝나지 않고, 이후 사람이 검수한 데이터를 다시 import해서 final table을 갱신할 수 있도록 설계했습니다.

---

## Slide 7. 입력 데이터와 Evidence Anchor

### 핵심 메시지
원문 OCR sentence를 evidence anchor로 유지하여, KG의 각 edge가 원문 근거로 돌아갈 수 있게 했습니다.

### 슬라이드에 넣을 내용
| 항목 | 값 |
| --- | ---: |
| 입력 OCR workbook | `handoff-hanyang/자이제_ocr_preprocessed.xlsx` |
| OCR clean sentences | 5,009 |
| Evidence anchors | 5,009 |
| Layer 2 chunks | 214 |
| Evaluation chunks | 120 |
| Optional annotation chunks | 214 |
| Optional remaining chunks | 94 |

### 발표 멘트
평가 실험은 현재 120개 chunk를 기준으로 구성했고, 전체 corpus에서 가능한 human annotation 확장 범위는 214개 chunk입니다. 300개 이상 strong claim을 하려면 source 추가 또는 chunk 재분할이 필요합니다.

---

## Slide 8. Layer 1 표준 KG 구축 결과

### 핵심 메시지
NCS와 PCF를 Layer 1 표준축으로 구축하여, 업무 KG를 외부 표준 체계와 연결할 수 있게 했습니다.

### 슬라이드에 넣을 내용
| Layer 1 구성 | Nodes | Edges |
| --- | ---: | ---: |
| NCS taxonomy | 4,109 | 4,085 |
| PCF taxonomy | 5,301 | 2,004 |
| PCF metric edges | - | 3,284 |

### 발표 멘트
Layer 1은 새로 추출한 업무 지식이 아니라, Layer 2 업무 KG를 표준 taxonomy와 연결하기 위한 기준축입니다. 따라서 이후 mapping이나 standard bridge 평가에서 중요한 역할을 합니다.

---

## Slide 9. Layer 2 업무 KG 구축 결과

### 핵심 메시지
수주/제안 업무 문서에서 절차형 업무 KG를 구축했고, accepted edge는 모두 evidence를 갖습니다.

### 슬라이드에 넣을 내용
| 항목 | 값 |
| --- | ---: |
| Layer 2 nodes | 220 |
| Layer 2 edges | 947 |
| Clean triples | 947 |
| Canonical DomainTask | 22 |
| Evidence-missing edges | 0 |
| Dangling edges | 0 |
| Type violations | 0 |
| Orphan nodes | 9 |
| Alias collisions | 13 |

### 발표 멘트
Layer 2 KG 구축은 완료되었습니다. 다만 자동 구축 결과이기 때문에, 논문에서 precision/recall 성능으로 주장하려면 human-gold와 대조하는 단계가 필요합니다.

---

## Slide 10. Layer 2 Schema

### 핵심 메시지
업무 절차를 표현하기 위해 일반 entity가 아니라 procedural schema를 사용했습니다.

### 슬라이드에 넣을 내용
주요 node type:

| Node type | 의미 |
| --- | --- |
| DomainTask | 업무 단위 |
| ProcedureStep | 업무 수행 단계 |
| Artifact | 입력/산출 문서 또는 산출물 |
| Role | 수행자 또는 책임 주체 |
| DecisionGateway | 의사결정 지점 |
| GuardCondition | 분기 조건 |
| ReviewCheckpoint | 검토/리뷰/점검/승인/확인 지점 |
| Risk | 위험요소 |
| Metric | 평가/관리 지표 |

주요 edge type:

| Edge type | 의미 |
| --- | --- |
| HAS_STEP | task가 step을 포함 |
| PRECEDES | 절차 순서 |
| USES_INPUT | 입력 산출물 사용 |
| PRODUCES | 산출물 생성 |
| PERFORMED_BY | 역할 수행 |
| HAS_DECISION_GATEWAY | 의사결정 지점 보유 |
| HAS_REVIEW_CHECKPOINT | 검토/리뷰 checkpoint 연결 |
| HAS_RISK | 위험 연결 |

### 발표 멘트
이 schema가 있기 때문에 LLM 출력이 단순 triple list가 아니라 절차형 업무 구조로 정규화될 수 있습니다.

---

## Slide 10-A. 최종 KG Node 생성 방식

### 핵심 메시지
최종 `outputs/07_layer2_graph/layer2_nodes.jsonl`의 node는 LLM 출력물을 그대로 넣은 것이 아니라, OCR sentence evidence, task seed, 용어 사전, 절차 템플릿을 사용해 생성한 rule/schema 기반 KG node입니다.

### 슬라이드에 넣을 내용
Node 생성 흐름:

1. OCR sentence를 `EA-JS-*` evidence anchor로 변환
2. `TASK_SEEDS`의 업무 seed label/alias/keyword로 관련 sentence 검색
3. 검색된 sentence에서 Artifact, Role, DecisionGateway, Principle, Risk 후보를 용어 사전으로 추출
4. 각 task frame을 `DomainTask` node로 생성
5. task별 절차 템플릿 또는 입력/산출물 기반 추론으로 `ProcedureStep` node 생성
6. 산출물이 다음 업무로 흘러가는 규칙으로 `ArtifactFlow` node 생성
7. `node_id` 기준으로 중복 제거하고, 모든 node에 evidence와 review status 부여

Node별 생성 방식:

| Node type | 생성 방식 | 현재 개수 |
| --- | --- | ---: |
| DomainTask | 업무 seed + evidence sentence 검색으로 생성 | 22 |
| ProcedureStep | task별 procedure template 또는 입력/산출물 기반 step 추론 | 99 |
| ReviewCheckpoint | 검토/리뷰/점검/승인/확인 신호가 있는 ProcedureStep에서 별도 checkpoint node로 투영 | 41 |
| Artifact | task evidence 안의 산출물/입력물 용어 매칭 | 14 |
| Role | 수행자/책임 주체 용어 매칭 | 10 |
| DecisionGateway | 의사결정 관련 용어 매칭 | 4 |
| GuardCondition | 의사결정 evidence에서 조건/가능성/경쟁/자원 등 조건 표현 추출 | 13 |
| Principle | 원칙/품질 기준 용어 매칭 | 5 |
| Risk | 위험/불리함/실패 가능성 용어 매칭 | 3 |
| ArtifactFlow | 특정 산출물이 다음 task 입력으로 쓰이는 규칙에서 생성 | 9 |

### 발표 멘트
여기서 중요한 점은 최종 KG node가 단순히 LLM에게 "node를 뽑아줘"라고 해서 나온 결과가 아니라는 점입니다. LLM 실험은 별도 prediction 실험이고, 현재 완성된 KG는 evidence anchor와 schema constraint를 만족하도록 조립된 자동 구축 결과입니다.

---

## Slide 10-B. 최종 KG Edge 생성 방식

### 핵심 메시지
Edge는 node 사이에 어떤 업무 관계가 있는지를 predicate별 규칙으로 생성하고, source/target node와 evidence가 모두 있는 경우에만 최종 graph에 남겼습니다.

### 슬라이드에 넣을 내용
Edge 생성 흐름:

1. task frame의 `inputs`, `outputs`, `roles`, `principles`, `risks` slot을 predicate로 변환
2. decision gateway와 guard condition을 별도 predicate로 연결
3. procedure step은 `HAS_STEP`, step 순서는 `PRECEDES`로 연결
4. artifact flow 규칙은 `FEEDS_INTO`, `USED_AS_INPUT_FOR`로 연결
5. 모든 edge를 triple record로 변환하고 `source_triple_ids`를 부여
6. allowed predicate, source/target node 존재, evidence 존재 조건을 통과한 edge만 최종 저장

Predicate별 생성 방식:

| Predicate | 생성 방식 | 현재 개수 |
| --- | --- | ---: |
| PRODUCES | task/step의 outputs slot을 Artifact node로 연결 | 220 |
| USES_INPUT | task/step의 inputs slot을 Artifact/Concept node로 연결 | 201 |
| PERFORMED_BY | task/step의 roles slot을 Role node로 연결 | 120 |
| HAS_STEP | DomainTask를 해당 ProcedureStep 목록에 연결 | 99 |
| PRECEDES | 같은 task 안에서 step order 기준으로 순서 연결 | 77 |
| HAS_PRINCIPLE | task/step의 principles slot 연결 | 64 |
| HAS_DECISION_GATEWAY | task/step에서 발견된 의사결정 node 연결 | 54 |
| HAS_REVIEW_CHECKPOINT | 검토/리뷰/점검/승인/확인 신호가 있는 step을 ReviewCheckpoint node로 연결 | 41 |
| HAS_RISK | task/step의 risks slot 연결 | 39 |
| HAS_GUARD_CONDITION | DecisionGateway에서 추출된 조건 node 연결 | 14 |
| FEEDS_INTO | Artifact가 다음 task로 흘러가는 규칙 연결 | 9 |
| USED_AS_INPUT_FOR | Artifact가 다음 task 입력으로 사용되는 규칙 연결 | 9 |

검증 결과:

| 검증 항목 | 결과 |
| --- | ---: |
| Final Layer 2 edges | 947 |
| Evidence가 있는 edges | 947 / 947 |
| `source_triple_ids`가 있는 edges | 947 / 947 |
| Dangling edges | 0 |
| Type violations | 0 |

### 발표 멘트
Edge는 "문장에 관계가 있어 보인다" 수준에서 끝나지 않습니다. 최종 graph에 들어가려면 source node와 target node가 실제로 존재해야 하고, predicate가 허용 목록에 있어야 하며, 원문 evidence anchor가 있어야 합니다.

---

## Slide 10-C. Triple, Node, Edge의 관계

### 핵심 메시지
최종 KG에서는 triple이 edge 검증과 evidence 추적을 위한 중간 표현으로 사용됩니다.

### 슬라이드에 넣을 내용
중간 산출물 관계:

| 단계 | 파일 | 의미 |
| --- | --- | --- |
| Task frame | `outputs/04_task_frames/canonical_task_catalog.json` | 22개 canonical 업무 단위 |
| Procedure structure | `outputs/05_procedure/procedure_structures_clean.jsonl` | task별 step, order, decision 구조 |
| Schema-valid triple | `outputs/06_triples/layer2_triples_schema_valid.jsonl` | edge를 SPO/evidence 형식으로 표현한 947개 triple |
| Final nodes | `outputs/07_layer2_graph/layer2_nodes.jsonl` | graph 시각화/Neo4j/RDF에 들어가는 220개 node |
| Final edges | `outputs/07_layer2_graph/layer2_edges.jsonl` | source/target/evidence 검증을 통과한 947개 edge |

구조:

| 개념 | 설명 |
| --- | --- |
| Node | 업무 개념 자체. 예: `기회분석`, `Capture Plan`, `고객 정보 수집` |
| Edge | node 사이 관계. 예: `기회분석 USES_INPUT Capture Plan` |
| Triple | edge를 subject-predicate-object와 evidence text로 평가하기 위한 중간 record |
| Evidence anchor | 해당 node/edge/triple이 근거로 삼은 OCR sentence |

### 발표 멘트
따라서 triple 수와 edge 수가 현재 947로 같습니다. edge를 만들고, 그것을 triple 형태로 evidence와 함께 검증한 뒤, 다시 최종 graph edge로 저장한 구조입니다.

---

## Slide 10-D. LLM 출력과 최종 KG의 관계

### 핵심 메시지
LLM은 최종 KG를 그대로 생성한 도구가 아니라, 동일 chunk에 대해 여러 방법론 조건이 어떤 node/edge/triple 후보를 생성하는지 비교하기 위한 prediction generator입니다.

### 슬라이드에 넣을 내용
구분해야 할 두 산출물:

| 구분 | 위치 | 의미 |
| --- | --- | --- |
| 최종 KG 구축 산출물 | `outputs/07_layer2_graph/` | 현재 연구 데이터에 대해 구축된 Layer 2 KG |
| LLM 실험 예측 산출물 | `experiments/cape_kg_eacl_20260627/48_*`, `49_*`, `50_*` | baseline/proposed/ablation 조건별 LLM prediction과 validation 결과 |

핵심 차이:

| 항목 | 최종 KG | LLM 실험 출력 |
| --- | --- | --- |
| 목적 | 실제 데이터에 대한 KG build | 방법론/프롬프트 조건 비교 |
| 입력 | 전체 OCR/evidence, schema, task seeds, rule dictionaries | 120개 evaluation chunk |
| 출력 | `node_id`, `edge_id`, source/target, evidence anchor가 있는 graph | 조건별 `triples`, `nodes`, `edges`, `mappings` |
| 검증 | dangling/type/evidence/RDF-SHACL-style structural validation | JSON parse, allowed type/predicate, evidence id validation |
| 현재 claim | KG 구축 완료 | silver/proxy diagnostic, human-gold 전 최종 성능 claim 아님 |

### 발표 멘트
교수님께 설명할 때 "LLM이 만든 KG"라고 말하면 오해가 생길 수 있습니다. 정확한 표현은 "최종 KG는 rule/schema/evidence 기반으로 구축했고, LLM은 같은 task에서 baseline/proposed/ablation 조건의 후보 생성 성능을 비교하기 위해 별도로 실행했다"입니다.

---

## Slide 11. NCS/PCF Standard Bridge

### 핵심 메시지
Layer 2 업무 task를 NCS/PCF와 연결하여, 내부 업무 지식을 외부 표준 체계와 비교 가능하게 했습니다.

### 슬라이드에 넣을 내용
| 항목 | 값 |
| --- | ---: |
| Canonical tasks | 22 |
| NCS mapping candidates | 110 |
| PCF mapping candidates | 110 |
| NCS Top-K coverage | 1.000 |
| PCF Top-K coverage | 1.000 |
| NCS-PCF crosswalk candidates | 220 |
| Shared Layer 2 tasks | 22 |

### 발표 멘트
현재 mapping은 후보 생성 단계입니다. 자동으로 정답이라고 merge하지 않았고, Top-K 후보의 acceptability는 expert review 후에 주장해야 합니다.

---

## Slide 12. LLM을 왜 사용했는가

### 핵심 메시지
LLM은 schema-constrained extraction 후보를 만들기 위해 사용했고, 최종 신뢰성은 evidence와 validator, human-gold로 확보하는 구조입니다.

### 슬라이드에 넣을 내용
LLM 사용 목적:

- 한국어 장문 업무 문서에서 후보 node/edge 추출
- 절차 관계와 역할/산출물/위험 관계 후보 생성
- baseline, ablation, model scaling 비교
- strict JSON contract와 validator로 출력 안정성 진단

LLM을 사용하지 않은 부분:

- NCS/PCF Layer 1 taxonomy 구축
- deterministic KG build의 일부 rule/template 기반 처리
- Neo4j/HTML export
- claim gate, checksum, release validation

### 발표 멘트
LLM이 정답을 생성한다고 가정하지 않았습니다. LLM은 후보 생성기이고, evidence grounding과 validator, 그리고 최종 human-gold 평가가 신뢰성을 담당합니다.

---

## Slide 13. 실행한 LLM 모델과 조건

### 핵심 메시지
Qwen3 계열 모델을 중심으로 baseline, proposed, ablation, scaling을 실행했습니다.

### 슬라이드에 넣을 내용
실행 모델:

| 모델 | 사용 목적 | 상태 |
| --- | --- | --- |
| Qwen3-8B | 기본 baseline/proposed/ablation | 실행 완료 |
| Qwen3-14B | model scaling core conditions | 실행 완료 |
| Qwen3-32B-AWQ | 더 큰 모델의 현실적 scaling | 120 chunk core run 완료 |

핵심 조건:

| 조건 | 의미 |
| --- | --- |
| B0_plain_llm | 가장 단순한 LLM baseline |
| B1_predicate_constrained | predicate 제한 baseline |
| B2_current_project | 기존 프로젝트 방식 baseline |
| B3_edc_style | EDC-style baseline |
| B4_taxonomy_rag | taxonomy retrieval baseline |
| B5_procedural_prompt | procedural prompt baseline |
| B6_sac_kg_verifier_pruner | SAC-KG-style verifier/pruner approximation |
| P_cape_kg_actual | 제안 방법론 조건 |
| P_minus_* | CQ/evidence/schema/bridge/validator ablation |

### 발표 멘트
모델을 키우는 실험도 했지만, 현재 결과는 silver/proxy diagnostic입니다. 최종 성능 비교는 human-gold가 들어온 뒤 같은 조건으로 재계산해야 합니다.

---

## Slide 13-A. 프롬프트별 산출물 매핑

### 핵심 메시지
프롬프트마다 요구한 출력 구조가 다릅니다. B0는 자유 triple, B1은 predicate-constrained edge, B2 이후는 CAPE-compatible node/edge, 제안 방법론과 taxonomy 조건은 mapping까지 산출하도록 설계했습니다.

### 슬라이드에 넣을 내용
프롬프트 파일 위치:

- `experiments/cape_kg_eacl_20260627/02_schema/prompts/`
- 실제 실행 시에는 `scripts/run_cape_llm_condition_baselines.py`가 chunk metadata, sentence ids, allowed node/edge types, JSON schema, strict JSON contract를 합쳐 runtime prompt를 구성

조건별 산출물:

| 조건 | 프롬프트 의도 | 요구한 주요 출력 |
| --- | --- | --- |
| B0_plain_llm | schema 없이 SPO triple 추출 | `triples` |
| B1_predicate_constrained | 허용 predicate만 사용해 관계 추출 | `edges` |
| B2_current_project | task frame 추출 후 Layer 2 schema로 후처리 | `nodes`, `edges` |
| B3_edc_style | open-schema item 추출, 정의, canonicalization 후 CAPE 호환 변환 | `nodes`, `edges` |
| B4_taxonomy_rag | NCS/PCF/task taxonomy snippet을 retrieval context로 사용 | `nodes`, `edges`, `mappings` |
| B5_procedural_prompt | action, actor, gateway, guard, artifact flow, dependency 추출 | `nodes`, `edges` |
| B6_sac_kg_verifier_pruner | 기존 후보를 schema/evidence verifier로 pruning하는 deterministic approximation | `nodes`, `edges` |
| P_cape_kg_actual | CQ, evidence, procedural schema, validator, NCS/PCF bridge를 결합한 제안 조건 | `nodes`, `edges`, `mappings` |
| P_minus_CQ | 제안 방법론에서 competency question anchoring 제거 | `nodes`, `edges`, `mappings` |
| P_minus_Evidence | evidence anchor 요구를 약화 | `nodes`, `edges`, `mappings` |
| P_minus_Procedural_schema | 절차형 schema 대신 flat schema 사용 | `nodes`, `edges`, `mappings` |
| P_minus_Validator | validator rejection 없이 모델 schema 선택 허용 | `nodes`, `edges`, `mappings` |
| P_minus_Standard_bridge | NCS/PCF bridge 출력 제거 | `nodes`, `edges` |
| P_minus_Schema_retrieval | chunk-specific schema/taxonomy retrieval 제거 | `nodes`, `edges`, `mappings` |

### 발표 멘트
같은 LLM을 쓰더라도 프롬프트 조건이 다르면 산출물이 다릅니다. 예를 들어 B0는 node/edge graph가 아니라 자유 triple을 내고, 제안 방법론은 node, edge, standard mapping까지 내도록 설계되어 있습니다.

---

## Slide 13-B. 실제 프롬프트 파일 원문

### 핵심 메시지
프롬프트 파일에 저장된 원문은 조건별 핵심 지시문이며, 실제 LLM 호출 때는 여기에 chunk 문장, sentence id, allowed schema, JSON 출력 형식이 자동으로 붙습니다.

### 슬라이드에 넣을 내용
프롬프트 파일 원문:

| 조건 | 파일 | 실제 저장된 프롬프트 원문 |
| --- | --- | --- |
| B0_plain_llm | `B0_plain_llm_triple_extraction.txt` | `Extract subject-predicate-object triples from the chunk. Return JSON only.` |
| B1_predicate_constrained | `B1_predicate_constrained_llm.txt` | `Extract triples using only the allowed predicates. Return JSON only with evidence sentence ids.` |
| B2_current_project | `B2_current_project_baseline.txt` | `Extract Task Frames, then triples, then post-process into the Layer2 schema.` |
| B3_edc_style | `B3_edc_style_baseline.txt` | `Extract, define, and canonicalize open-schema KG items, then emit CAPE-compatible nodes and edges for scoring.` |
| B4_taxonomy_rag | `B4_taxonomy_rag_baseline.txt` | `Retrieve NCS/PCF/task taxonomy snippets, then extract schema-constrained triples with evidence.` |
| B5_procedural_prompt | `B5_procedural_prompt_baseline.txt` | `Extract actions, actors, gateways, guard conditions, artifact flows, and temporal/logical dependencies.` |
| B6_sac_kg_verifier_pruner | `B6_sac_kg_verifier_pruner_baseline.txt` | `Use existing generator candidates, then apply schema/evidence verification and pruning in the style of SAC-KG. This is a deterministic approximation, not a full SAC-KG reproduction.` |
| P_cape_kg_actual | `P_cape_kg.txt` | `Use CQ-linked schema retrieval, procedural frame extraction, evidence-span constrained relation extraction, span verification, ontology validation, procedural consistency checks, and active review scoring.` |
| P_minus_Schema_retrieval | `P_minus_Schema_retrieval.txt` | `Run CAPE-KG without chunk-specific schema/taxonomy retrieval; keep CQ, evidence grounding, procedural schema, validation, and mapping output shape.` |
| strict_json_contract | `strict_json_contract.txt` | JSON object만 반환, markdown/설명/XML/`<think>` 금지, `/no_think`, compact JSON, 빈 배열 사용 |

### 발표 멘트
여기서 보이는 한 줄 프롬프트는 "조건명과 방법론의 핵심 지시"입니다. 실제 모델 입력에는 다음 슬라이드의 runtime prompt template이 결합됩니다.

---

## Slide 13-C. 실제 Runtime Prompt 공통 Template

### 핵심 메시지
프롬프트 파일은 조건의 핵심 아이디어를 담고 있고, 실제 LLM 호출 prompt에는 chunk 문장, sentence id, JSON shape, evidence requirement, allowed schema가 함께 들어갑니다.

### 슬라이드에 넣을 내용
모든 조건에 실제로 붙은 공통 prompt template:

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

모든 조건에 공통으로 들어간 제약:

| 제약 | 의미 |
| --- | --- |
| JSON only | markdown, 설명문 없이 하나의 JSON object만 반환 |
| Chunk metadata | `chunk_id`, page range, sentence id 목록 제공 |
| Sentence evidence | 추출 항목은 chunk 안의 sentence id를 evidence로 달아야 함 |
| No outside knowledge | chunk에 직접 근거가 없는 내용 금지 |
| Korean label retention | 원문이 한국어이면 label도 한국어 유지 |

Schema-constrained 조건에 추가된 제약:

| 제약 | 의미 |
| --- | --- |
| Allowed node types | DomainTask, ProcedureStep, Artifact, Role, DecisionGateway 등 |
| Allowed edge predicates | HAS_STEP, PRECEDES, USES_INPUT, PRODUCES, PERFORMED_BY 등 |
| Evidence validation | 출력의 `evidence_anchor_ids`가 해당 chunk sentence id 안에 있어야 valid |
| Validator | 알 수 없는 node type/predicate는 rejection 또는 ablation별 허용 |
| Hard limit | 제안/ablation 조건은 chunk당 최대 5 nodes, 5 edges, 3 mappings |

Strict JSON contract:

| 항목 | 의미 |
| --- | --- |
| `/no_think` | Qwen 계열에서 reasoning text 출력 억제 |
| compact JSON | truncation과 parse error 감소 |
| empty arrays | 없는 `nodes`, `edges`, `triples`, `mappings`는 빈 배열로 반환 |

### 발표 멘트
즉 프롬프트는 단순히 "그래프를 만들어줘"가 아니라, 어떤 JSON key를 만들어야 하는지, 어떤 node/edge type만 허용되는지, 어떤 sentence id를 evidence로 달아야 하는지를 명시했습니다.

---

## Slide 13-D. 실제 P_cape_kg_actual Runtime Prompt

### 핵심 메시지
제안 방법론 조건인 `P_cape_kg_actual`은 CQ, taxonomy snippet, evidence requirement, validator rule, allowed schema, JSON shape를 모두 포함한 prompt로 실행했습니다.

### 슬라이드에 넣을 내용
`P_cape_kg_actual` runtime instruction 핵심 원문:

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

Taxonomy snippets:
{NCS/PCF/task taxonomy retrieval context}

Rules:
- Every node, edge, and mapping must include evidence_anchor_ids from the chunk.
- Use only the listed node types and edge predicates. Invalid schema terms will be rejected.
- Do not use outside knowledge.
- Keep Korean labels when the source text is Korean.
- Prefer concise, reusable labels.
- Hard limit: return at most 5 nodes, at most 5 edges, and at most 3 mappings.
- If the chunk does not support a field, return an empty array for that field.

Allowed node types for this condition:
["Artifact", "ArtifactFlow", "DecisionGateway", "DomainTask", "GuardCondition",
 "Principle", "ProcedureStep", "ReviewCheckpoint", "Risk", "Role"]

Allowed edge predicates for this condition:
["BRANCHES_TO", "FEEDS_INTO", "HAS_DECISION_GATEWAY", "HAS_GUARD_CONDITION",
 "HAS_PRINCIPLE", "HAS_REVIEW_CHECKPOINT", "HAS_RISK", "HAS_STEP",
 "PERFORMED_BY", "PRECEDES", "PRODUCES", "USED_AS_INPUT_FOR", "USES_INPUT"]

JSON shape:
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

Strict JSON run에서는 위 user prompt 앞뒤에 다음이 추가되었습니다.

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

### 발표 멘트
이 prompt가 제안 방법론의 실제 실행 조건입니다. CQ와 taxonomy bridge가 들어가고, evidence anchor와 schema validator가 강제되며, 출력은 `nodes`, `edges`, `mappings` 세 배열로 제한됩니다.

---

## Slide 13-E. Baseline Runtime Prompt 예시

### 핵심 메시지
Baseline은 제안 방법론보다 제약을 일부 제거하거나 단순화하여 비교군으로 사용했습니다.

### 슬라이드에 넣을 내용
B0 실제 instruction:

```text
You are the B0 baseline: plain LLM triple extraction.
Extract only directly supported subject-predicate-object triples.
Use any short predicate label that appears appropriate from the text.

JSON shape:
{
  "triples": [
    {
      "subject": "string",
      "predicate": "string",
      "object": "string",
      "evidence_anchor_ids": ["sentence ids"],
      "confidence": 0.0
    }
  ]
}
```

B1 실제 instruction:

```text
You are the B1 baseline: predicate-constrained LLM extraction.
Use only these predicates:
{allowed CAPE-KG edge predicates}

Extract edges as directly supported triples. Include node types if inferable.

JSON shape:
{
  "edges": [
    {
      "subject": "string",
      "subject_type": "DomainTask|ProcedureStep|DecisionGateway|GuardCondition|Artifact|ArtifactFlow|Role|ReviewCheckpoint|Principle|Risk",
      "predicate": "one allowed predicate",
      "object": "string",
      "object_type": "DomainTask|ProcedureStep|DecisionGateway|GuardCondition|Artifact|ArtifactFlow|Role|ReviewCheckpoint|Principle|Risk",
      "evidence_anchor_ids": ["sentence ids"],
      "confidence": 0.0
    }
  ]
}
```

B4 실제 instruction의 핵심:

```text
You are the B4 baseline: taxonomy-RAG extraction.
Use the NCS/PCF/task taxonomy hints only as retrieval context.
Extract only what is directly supported by the chunk.
Do not force a taxonomy mapping when the chunk does not support it.

Taxonomy snippets:
{taxonomy_context}

JSON shape includes:
- nodes
- edges
- mappings
```

### 발표 멘트
B0는 schema 제약이 거의 없고, B1은 predicate만 제한하며, B4는 taxonomy context를 넣지만 CQ/validator/procedural control 전체를 결합하지는 않습니다. 따라서 P_cape_kg_actual과 비교할 수 있습니다.

---

## Slide 13-F. LLM 산출물 예시 요약

### 핵심 메시지
120개 chunk에 대해 조건별 validated JSON 산출물을 만들었고, 이 산출물은 최종 KG가 아니라 조건 비교용 prediction입니다.

### 슬라이드에 넣을 내용
Qwen3-8B strict JSON full run 기준 validated object 수:

| 조건 | Valid rows | Triples | Nodes | Edges | Mappings |
| --- | ---: | ---: | ---: | ---: | ---: |
| B0_plain_llm | 120 | 1,037 | 0 | 0 | 0 |
| B1_predicate_constrained | 120 | 0 | 0 | 805 | 0 |
| B2_current_project | 120 | 0 | 867 | 334 | 0 |
| B3_edc_style | 120 | 0 | 769 | 263 | 0 |
| B4_taxonomy_rag | 120 | 0 | 719 | 323 | 126 |
| B5_procedural_prompt | 120 | 0 | 1,307 | 302 | 0 |
| P_cape_kg_actual | 120 | 0 | 576 | 373 | 227 |
| P_minus_* ablations | 각 120 | 0 | 558-586 | 353-417 | 0-233 |

해석:

- 이 표는 "얼마나 많이 뽑았는가"에 대한 출력량 진단입니다.
- 정확도/성능 우수성 표가 아닙니다.
- 최종 성능 평가는 human-gold annotation 이후 같은 outputs를 gold와 비교해 계산해야 합니다.

### 발표 멘트
이 표를 보여주면 프롬프트별로 산출물 성격이 실제로 달랐다는 점을 설명할 수 있습니다. 다만 많이 뽑았다고 좋은 것이 아니며, human-gold 전에는 precision/recall claim으로 해석하면 안 됩니다.

---

## Slide 14. 실험 1: Deterministic KG Build

### 핵심 메시지
원문 데이터에서 Layer 1, Layer 2, mapping, visualization까지 자동 구축이 성공했습니다.

### 슬라이드에 넣을 내용
실행 결과:

| 산출물 | 상태 | 경로 |
| --- | --- | --- |
| Layer 1 NCS/PCF | PASS | `outputs/01_layer1/` |
| OCR/evidence anchors | PASS | `outputs/02_ocr/`, `outputs/06_triples/` |
| Layer 2 KG | PASS | `outputs/07_layer2_graph/` |
| NCS/PCF mapping | PASS | `outputs/08_mapping/` |
| HTML/GraphML/JSON viewer | PASS | `outputs/09_visualization/` |
| Final build report | PASS | `outputs/10_evaluation/final_build_report.md` |

### 발표 멘트
이 단계는 연구 데이터에 대한 KG 구축 자체를 완료한 단계입니다. 발표에서는 "KG 구축은 완료, 성능 평가는 pending"이라고 분리해서 말하는 것이 중요합니다.

---

## Slide 15. 실험 2: Actual LLM Silver Diagnostics

### 핵심 메시지
실제 LLM을 여러 조건으로 실행했지만, 현재 metric은 human-gold가 아니라 silver reference 기준 diagnostic입니다.

### 슬라이드에 넣을 내용
| Condition | Edge F1 | Predicate F1 | Node F1 | Evidence F1 | Parse errors |
| --- | ---: | ---: | ---: | ---: | ---: |
| B0_plain_llm | 0.0000 | 0.0000 | 0.0350 | 0.0239 | 63 |
| B1_predicate_constrained | 0.0000 | 0.1416 | 0.0000 | 0.0291 | 63 |
| B2_current_project | 0.0000 | 0.0068 | 0.0215 | 0.0503 | 97 |
| B6_sac_kg_verifier_pruner | 0.0017 | 0.0774 | 0.0564 | 0.1008 | 0 |
| P_cape_kg_actual | 0.0018 | 0.0482 | 0.0326 | 0.0655 | 113 |

주의:

- 이 표는 final performance table이 아닙니다.
- KG-derived silver reference와의 비교입니다.
- 낮은 edge F1은 strict exact-match 기준과 silver proxy의 한계를 반영합니다.

### 발표 멘트
이 결과는 성능 우수성 주장이 아니라 진단표입니다. 특히 edge exact match는 label, predicate, evidence가 동시에 맞아야 해서 매우 엄격합니다.

---

## Slide 16. 실험 3: Ablation Study

### 핵심 메시지
CAPE-KG의 구성 요소를 하나씩 제거한 조건을 실행하여, 어떤 구성 요소가 결과에 영향을 주는지 확인할 수 있게 했습니다.

### 슬라이드에 넣을 내용
실행된 ablation:

| Ablation | 제거한 구성 요소 |
| --- | --- |
| P_minus_CQ | Competency Question |
| P_minus_Evidence | Evidence instruction |
| P_minus_Procedural_schema | Procedural schema |
| P_minus_Schema_retrieval | Schema retrieval |
| P_minus_Standard_bridge | NCS/PCF bridge |
| P_minus_Validator | Validator feedback |

대표 silver diagnostic:

| Condition | Edge F1 | Predicate F1 | Node F1 | Evidence F1 |
| --- | ---: | ---: | ---: | ---: |
| P_cape_kg_actual | 0.0018 | 0.0482 | 0.0326 | 0.0655 |
| P_minus_CQ | 0.0000 | 0.0338 | 0.0285 | 0.0682 |
| P_minus_Evidence | 0.0009 | 0.0549 | 0.0297 | 0.0666 |
| P_minus_Procedural_schema | 0.0036 | 0.0976 | 0.0301 | 0.0687 |
| P_minus_Validator | 0.0018 | 0.0456 | 0.0299 | 0.0659 |

### 발표 멘트
현재 ablation은 silver/proxy 기준이므로 방향성 진단으로만 사용합니다. 최종적으로는 human-gold 기준으로 같은 ablation을 재계산해야 논문 claim이 됩니다.

---

## Slide 17. 실험 4: Model Scaling

### 핵심 메시지
Qwen3-8B, 14B, 32B-AWQ를 같은 120 chunk core condition에서 비교했습니다.

### 슬라이드에 넣을 내용
| Model | Condition | Rows | Edge F1 | Predicate F1 | Node F1 | Evidence F1 |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Qwen3-8B | P_cape_kg_actual | 120 | 0.0018 | 0.0482 | 0.0326 | 0.0655 |
| Qwen3-14B | P_cape_kg_actual | 120 | 0.0017 | 0.0601 | 0.0298 | 0.0610 |
| Qwen3-32B-AWQ | P_cape_kg_actual | 120 | 0.0034 | 0.0662 | 0.0284 | 0.0542 |

### 발표 멘트
32B-AWQ는 core 120 chunk run이 완료되었습니다. 현재 기준으로는 predicate/edge silver diagnostic 일부가 좋아졌지만, 이것도 human-gold 전에는 최종 claim이 아닙니다.

---

## Slide 18. 실험 5: Public Benchmark Adapter

### 핵심 메시지
내부 한국어 업무 데이터만이 아니라, PAGED/Text2KG public benchmark adapter도 실행해 보조적인 일반화 진단을 확보했습니다.

### 슬라이드에 넣을 내용
| Run | PAGED n | PAGED node F1 | PAGED edge F1 | Text2KG n | Relation F1 | Triple F1 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Qwen3-8B full adapter | 100 | 0.2472 | 0.4233 | 200 | 0.6015 | 0.1736 |
| Qwen3-8B subset | 10 | 0.1608 | 0.1794 | 20 | 0.4500 | 0.0500 |
| Qwen3-14B subset | 10 | 0.1733 | 0.1446 | 20 | 0.2817 | 0.0200 |

### 발표 멘트
이 결과는 public benchmark에서 adapter가 동작한다는 보조 증거입니다. 다만 본 연구의 main result는 한국어 수주/제안 업무 데이터 human-gold 기준으로 확정해야 합니다.

---

## Slide 19. 실험 6: Structural Diagnostics

### 핵심 메시지
KG 구조 자체의 schema conformance, procedural consistency, CQ answerability를 자동 진단했습니다.

### 슬라이드에 넣을 내용
| 진단 항목 | 값 | 해석 |
| --- | ---: | --- |
| Ontology conformance | 1.0000 | schema/domain-range 위반 없음 |
| Procedural consistency | 0.9950 | 절차 구조 대부분 일관 |
| CQ answerability | 1.0000 | 정의한 CQ 12개 모두 구조적으로 응답 가능 |
| Domain/range errors | 0 | edge type 제약 위반 없음 |
| Evidence missing | 0 | accepted edge evidence 누락 없음 |
| Cycles | 0 | 절차 순환 오류 없음 |

### 발표 멘트
이 표는 KG의 구조적 품질 진단입니다. 논문에서 human-gold 성능과는 별개로, 구축된 KG가 schema와 절차 제약을 잘 만족한다는 진단 근거로 사용할 수 있습니다.

---

## Slide 20. Structural Gap Worklist

### 핵심 메시지
구조 진단에서 발견된 개선 후보를 사람이 검토할 수 있는 worklist로 만들었습니다.

### 슬라이드에 넣을 내용
| 항목 | 값 |
| --- | ---: |
| Review checkpoint candidates | 45 |
| Gateway branch gaps | 4 |
| Structural CQ answerability | 1.0000 |
| Procedural consistency | 0.9950 |

대표 개선 후보:

- review 관련 task/step을 `ReviewCheckpoint`로 재분류하거나 link 추가할지 검토
- decision gateway에서 branch target을 추가할지 검토
- 자동으로 KG를 수정하지 않고 human structural review 대상으로 분리

### 발표 멘트
자동 시스템이 임의로 branch edge를 추가하면 hallucination 위험이 있습니다. 그래서 구조 gap은 자동 수정하지 않고 optional human review 대상으로 넘겼습니다.

---

## Slide 21. Evidence Span Granularity

### 핵심 메시지
sentence-level evidence를 유지하고, subject/object label의 exact character span coverage도 진단했습니다.

### 슬라이드에 넣을 내용
| 항목 | 값 |
| --- | ---: |
| Layer 2 triples | 947 |
| Triple components | 2,841 |
| Exact component spans | 742 |
| Exact component span rate | 0.2612 |
| Subject exact span rate | 0.2323 |
| Object exact span rate | 0.5512 |
| Predicate sentence proxy rate | 1.0000 |

### 발표 멘트
현재는 sentence-level evidence가 기본입니다. component-level span은 자동 진단이며, 최종 span exactness claim은 human-gold span 검수 이후에 해야 합니다.

---

## Slide 22. Active Review 설계

### 핵심 메시지
사람 검수 비용을 줄이기 위해 오류 가능성이 높은 항목을 우선 검토하는 active-review queue를 만들었습니다.

### 슬라이드에 넣을 내용
| 항목 | 값 |
| --- | ---: |
| Candidate count | 275 |
| Silver-proxy error count | 273 |
| High-impact error count | 173 |
| Human-effort pooled rows | 204 |
| Active-priority assigned | 100 |
| Uncertainty-only assigned | 100 |
| Random-control assigned | 100 |

주의:

- 현재 active-review 결과는 human timing/correction 데이터가 없는 상태
- 효율성 claim은 `active_review_human_effort.reviewed.csv` 반환 후 가능

### 발표 멘트
active review는 이미 queue와 template이 준비되어 있지만, 아직 사람이 실제로 검수한 시간과 correction 결과가 없기 때문에 효율성 주장은 보류해야 합니다.

---

## Slide 23. Human-Gold Annotation 설계

### 핵심 메시지
최종 성능 claim을 위해 100 chunk 이상의 two-annotator annotation과 adjudication을 준비했습니다.

### 슬라이드에 넣을 내용
| 항목 | 현재 값 |
| --- | ---: |
| Minimum paper-gate return files | 11 |
| Optional/strong claim return files | 3 |
| Required claim/human return files | 14 |
| Optional structural review files | 2 |
| All master return files | 16 |
| Present human return files | 0 |
| Required adjudicated chunks | 100+ |
| Current adjudicated chunks | 0 |
| Required gold items | 500+ |
| Current gold items | 0 |
| Annotator A/B manifests | 각 100 unique chunks |
| Batch assignment | 5 batches x 20 chunks |

필요한 사람 검수:

- Annotator A/B full 120 package
- IAA 계산
- adjudication
- mapping expert review
- NCS-PCF crosswalk expert review
- active-review human effort timing/correction

### 발표 멘트
현재 병목은 GPU나 자동화가 아니라 사람 검수입니다. minimum 11개와 optional/strong claim 3개가 돌아오면 논문 claim용 post-annotation refresh를 실행할 수 있고, 선택 structural review 2개까지 포함한 master 반환 manifest는 16개로 관리합니다.

---

## Slide 24. Claimable Main Table 해석

### 핵심 메시지
현재 main table은 final performance table이 아니라, 어떤 결과를 주장할 수 있고 어떤 결과를 보류해야 하는지 정리한 claimability table입니다.

### 슬라이드에 넣을 내용
| Result | 현재 상태 | 이유 |
| --- | --- | --- |
| Core extraction main result | pending_human | human-gold 미완료 |
| Actual LLM run coverage | claimable_setup | 조건별 120 rows 생성 완료 |
| CAPE-KG silver diagnostic | diagnostic_only | silver proxy 기준 |
| KG structural diagnostics | diagnostic_only | human-gold 성능이 아닌 구조 진단 |
| Public benchmark adapter | auxiliary_claimable | 보조 일반화 증거 |
| NCS/PCF mapping downstream | pending_expert_review | expert review 필요 |
| Active-review ablation | diagnostic_only | human effort 데이터 필요 |
| Release/reproducibility package | claimable_setup | bundle/checksum 검증 완료 |
| Submission claim gate | not_ready | required failures 4개 |

### 발표 멘트
교수님께는 "현재 main table이 없느냐"가 아니라 "final performance table은 아직 없고, claimability table은 있다"고 설명하는 것이 정확합니다.

---

## Slide 25. Claim Gate 결과

### 핵심 메시지
Claim gate는 보수적으로 FAIL이며, 실패 원인은 모두 사람이 필요한 평가 단계입니다.

### 슬라이드에 넣을 내용
| Gate | Status | 의미 |
| --- | --- | --- |
| data.eval_chunks | PASS | 120 chunks 준비 |
| llm.baselines | PASS | B0/B1/B2 120 rows 완료 |
| llm.proposed_generation | PASS | P_cape_kg_actual 120 rows 완료 |
| llm.ablations | PASS | 6개 ablation 완료 |
| external.public_subset | PASS | public subset 실행 |
| release.artifacts | PASS | release artifact 준비 |
| gold.completed_chunks | FAIL | human-gold chunk 0 |
| gold.item_count | FAIL | gold item 0 |
| gold.iaa | FAIL | IAA 미계산 |
| llm.proposed_human_gold_score | FAIL | human-gold scoring 미완료 |

### 발표 멘트
FAIL은 자동 실험이 잘못됐다는 뜻이 아닙니다. 사람이 검수하지 않은 수치를 논문 성능으로 주장하지 않기 위한 conservative gate입니다.

---

## Slide 26. 현재 완료된 실험 목록

### 핵심 메시지
현재까지 실행한 실험은 KG 구축, LLM 조건 비교, 모델 확장, public benchmark, 구조 진단, handoff 검증까지 포함합니다.

### 슬라이드에 넣을 내용
| 실험/작업 | 완료 여부 | 산출물 |
| --- | --- | --- |
| Layer 1 NCS/PCF KG build | 완료 | `outputs/01_layer1/` |
| OCR evidence anchor build | 완료 | `outputs/02_ocr/`, `outputs/06_triples/` |
| Layer 2 procedural KG build | 완료 | `outputs/07_layer2_graph/` |
| NCS/PCF mapping candidate build | 완료 | `outputs/08_mapping/` |
| KG visualization/Neo4j export | 완료 | `outputs/09_visualization/`, `outputs/11_neo4j_import_flat/` |
| Qwen3-8B baseline/proposed | 완료 | `45_*`, `46_*`, `47_*` files |
| Qwen3-8B ablations | 완료 | `48_*`, `49_*`, `50_*` files |
| Qwen3-14B core run | 완료 | `qwen3_14b_core_*` files |
| Qwen3-32B-AWQ core run | 완료 | `qwen3_32b_awq_core_*` files |
| Public benchmark adapter | 완료 | `08_public_benchmarks/` |
| Structural diagnostics | 완료 | `04_evaluation/structural_*` |
| Human-review handoff | 완료 | `06_release/human_review_handoff/` |
| Claim gate/release bundle | 완료 | `06_release/claim_gate_report.*`, checksums |

### 발표 멘트
실험 실행 자체는 상당히 넓게 진행되었습니다. 다만 최종 논문 주장을 위해 남은 것은 사람이 검수한 gold label을 넣고 같은 평가기를 다시 돌리는 것입니다.

---

## Slide 27. Pre-Human Handoff Validation

### 핵심 메시지
사람 검수를 시작하기 전 필요한 산출물과 bundle은 validation 기준 PASS 상태입니다.

### 슬라이드에 넣을 내용
| 항목 | 값 |
| --- | ---: |
| Overall status | PASS |
| Checks | 75 |
| PASS | 74 |
| WARN | 1 |
| FAIL | 0 |

WARN 내용:

- submission claim은 아직 human-gold, IAA, adjudication, human-gold scoring 전이므로 보류

### 발표 멘트
검수 인프라는 준비되어 있고, WARN은 의도된 경고입니다. 실제 사람이 annotation을 완료하면 claim gate를 다시 통과시킬 수 있습니다.

---

## Slide 28. 시각화와 재현성 산출물

### 핵심 메시지
KG를 HTML viewer, GraphML, Neo4j import 형식으로 확인할 수 있게 만들었고, release bundle과 checksum도 생성했습니다.

### 슬라이드에 넣을 내용
시각화:

- HTML viewer: `outputs/09_visualization/kg_viewer.html`
- GraphML: `outputs/09_visualization/kg_full.graphml`
- JSON graph: `outputs/09_visualization/kg_full.json`
- Neo4j flat import: `outputs/11_neo4j_import_flat/`
- RDF/Turtle export: `outputs/12_rdf/cape_kg_layer2.ttl`
- SHACL-style validation report: `outputs/12_rdf/cape_kg_shacl_validation_report.md`

재현성:

- Release bundle manifest: `06_release/release_bundle_manifest.json`
- Release checksum: `06_release/release_bundle_checksums.sha256`
- Human review handoff checksum: `06_release/human_review_handoff/human_review_handoff_checksums.sha256`
- Provenance manifest: `06_release/provenance_manifest.md`
- PROV-O Turtle export: `06_release/provenance_prov_o.ttl`

### 발표 멘트
교수님께 보여드릴 때는 HTML viewer나 Neo4j Browser에서 KG를 직접 시각화해 설명할 수 있습니다. public-safe bundle은 원문 텍스트 유출을 막도록 별도로 관리했습니다.

---

## Slide 29. 현재 한계

### 핵심 메시지
현재 한계는 자동화 실패가 아니라, 논문 claim을 확정하기 위한 human-gold와 expert review가 아직 없다는 점입니다.

### 슬라이드에 넣을 내용
| 한계 | 현재 영향 | 해결 방법 |
| --- | --- | --- |
| Human-gold 없음 | final F1/precision/recall claim 불가 | 100 chunk two-annotator annotation |
| IAA 없음 | annotation 신뢰도 claim 불가 | annotator A/B 완료 후 IAA 계산 |
| Adjudication 없음 | gold label 확정 불가 | adjudication file 작성 |
| Mapping expert review 없음 | NCS/PCF mapping 성능 claim 불가 | Top-K mapping group 검수 |
| Active effort 없음 | active review 효율 claim 불가 | timing/correction CSV 반환 |
| Current corpus 214 chunks | 300+ strong claim 부족 | source 추가 또는 chunk 재분할 |

### 발표 멘트
즉, 현재의 작업은 "논문 제출 직전"이 아니라 "사람 평가만 들어오면 final result table로 전환 가능한 pre-human complete 상태"입니다.

---

## Slide 30. 다음 단계

### 핵심 메시지
다음 단계는 GPU 실험이 아니라 사람 검수와 post-annotation refresh입니다.

### 슬라이드에 넣을 내용
우선순위:

1. 100 chunk annotator A/B 검수 완료
2. IAA 계산
3. disagreement adjudication
4. human-gold metrics 재계산
5. NCS/PCF mapping expert review
6. NCS-PCF crosswalk expert review
7. active-review human effort CSV 작성
8. claim gate 재실행
9. final performance table 생성
10. 논문 결과/한계/오류분석 업데이트

핵심 명령:

```bash
PYTHON_BIN=/home/minjoo/tdpo2_aaai2027/.venv_tdpo2/bin/python \
LLM_PYTHON=/home/minjoo/tdpo2_aaai2027/.venv_tdpo2/bin/python \
APPLY_IMPORTS=1 \
bash scripts/run_cape_post_annotation_refresh.sh
```

### 발표 멘트
사람 검수 파일이 준비되면 이 refresh script가 import, IAA, adjudication, scoring, claim gate, release table 갱신까지 이어서 실행합니다.

---

## Slide 31. 교수님께 보고할 결론

### 핵심 메시지
현재 연구는 방법론과 인프라가 상당히 구축되었고, 논문 claim 확정을 위한 마지막 단계는 human evaluation입니다.

### 슬라이드에 넣을 내용
보고 결론:

- 한국어 수주/제안 업무 문서에서 evidence-grounded procedural KG를 구축했다.
- Layer 1 표준 KG와 Layer 2 업무 KG를 분리해 구축했다.
- Layer 2 업무 KG는 220 nodes, 947 edges이며 accepted edge evidence 누락은 없다.
- NCS/PCF mapping 후보와 NCS-PCF crosswalk 후보를 생성했다.
- Qwen3-8B/14B/32B-AWQ 기반 LLM baseline, proposed, ablation, scaling 실험을 실행했다.
- Public benchmark adapter와 structural diagnostics도 실행했다.
- 현재 main table은 final performance table이 아니라 claimability table이다.
- 최종 성능 주장은 human-gold, IAA, adjudication, expert review 이후 확정한다.

### 발표 멘트
현재 교수님께 가장 명확하게 드릴 메시지는 "연구 방법론과 자동 실험 체계는 준비되었고, 이제 사람이 만든 gold evaluation으로 논문 claim을 확정하는 단계"라는 점입니다.

---

## Slide 32. 발표 시 피해야 할 표현

### 핵심 메시지
아직 human-gold가 없기 때문에 final 성능처럼 들리는 표현은 피해야 합니다.

### 슬라이드에 넣을 내용
| 피해야 할 표현 | 안전한 표현 |
| --- | --- |
| 제안 방법론이 baseline보다 우수하다 | silver/proxy 기준 diagnostic을 수행했다 |
| main table 결과가 나왔다 | claimability table은 있고 final performance table은 pending이다 |
| mapping 성능이 검증되었다 | mapping 후보가 생성되었고 expert review가 필요하다 |
| active review가 효율적이다 | active review queue와 human-effort template이 준비되었다 |
| 32B 모델이 성능을 개선했다 | 32B-AWQ core run이 완료되었고 silver diagnostic에서 일부 차이가 관찰되었다 |

### 발표 멘트
이 구분을 지키면 교수님께 현재 성과와 남은 일을 모두 정직하게 보고할 수 있습니다.

---

# Appendix A. 주요 산출물 경로

| 목적 | 경로 |
| --- | --- |
| 최종 KG build report | `outputs/10_evaluation/final_build_report.md` |
| Layer 2 nodes | `outputs/07_layer2_graph/layer2_nodes.jsonl` |
| Layer 2 edges | `outputs/07_layer2_graph/layer2_edges.jsonl` |
| NCS mapping candidates | `outputs/08_mapping/l2_ncs_mapping_candidates.jsonl` |
| PCF mapping candidates | `outputs/08_mapping/l2_pcf_mapping_candidates.jsonl` |
| HTML KG viewer | `outputs/09_visualization/kg_viewer.html` |
| Neo4j import flat | `outputs/11_neo4j_import_flat/` |
| RDF/Turtle export | `outputs/12_rdf/cape_kg_layer2.ttl` |
| SHACL-style validation | `outputs/12_rdf/cape_kg_shacl_validation_report.md` |
| Prompt files | `experiments/cape_kg_eacl_20260627/02_schema/prompts/` |
| LLM run provenance | `experiments/cape_kg_eacl_20260627/04_evaluation/provenance_llm_run_index.csv` |
| LLM raw/valid outputs | `experiments/cape_kg_eacl_20260627/48_*`, `49_*`, `50_*` |
| Paper tables | `experiments/cape_kg_eacl_20260627/06_release/paper_tables.md` |
| Claimable main table | `experiments/cape_kg_eacl_20260627/06_release/claimable_main_table.md` |
| Claim gate | `experiments/cape_kg_eacl_20260627/06_release/claim_gate_report.md` |
| Completion audit | `experiments/cape_kg_eacl_20260627/06_release/submission_completion_audit_ko.md` |
| Human review checklist | `experiments/cape_kg_eacl_20260627/06_release/human_review_master_checklist_ko.md` |
| Pre-human validation | `experiments/cape_kg_eacl_20260627/06_release/pre_human_handoff_validation.md` |

---

# Appendix B. 한 문장 요약

> 본 연구는 한국어 수주/제안 업무 문서에서 evidence-grounded procedural KG를 구축하는 CAPE-KG 방법론을 적용하여 Layer 1 표준 KG, Layer 2 업무 KG, NCS/PCF bridge, LLM baseline/ablation/model-scaling, structural diagnostics, human-review handoff까지 완료했으며, 최종 논문 성능 claim은 100 chunk 이상 human-gold annotation, IAA, adjudication, expert review 이후 확정할 계획입니다.
