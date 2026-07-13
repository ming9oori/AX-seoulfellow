# 교수님 발표자료 원고: CAPE-KG 수정 방향 반영 최종본

Generated: 2026-06-28
Updated: 2026-06-28 13:10 UTC

이 문서는 교수님께 현재까지의 연구 진행 상황을 설명하기 위한 PPT 슬라이드별 원고입니다. 실제 PPT를 직접 만든 파일은 아니며, 각 슬라이드에 넣을 제목, 핵심 메시지, 표, 발표자 설명을 바로 옮길 수 있도록 작성했습니다.

현재 발표에서 가장 중요한 기준은 다음 한 문장입니다.

> **KG 구축과 실험 실행 인프라는 완료 단계에 도달했지만, 논문에서 주장 가능한 최종 성능은 human-gold annotation, IAA, adjudication, mapping expert review, NCS-PCF crosswalk expert review, active-review effort evidence 이후에만 확정한다.**

따라서 교수님께는 "실험을 하지 못했다"가 아니라, "자동 구축과 LLM 실행은 끝났고, 이제 논문 claim을 안전하게 만들기 위한 사람 검수 게이트가 남아 있다"라고 설명하는 것이 맞습니다.

이번 수정 반영점은 다음과 같습니다.

- 기존 minimum human gate는 120개 chunk, 11개 minimum 반환 파일 기준으로 유지합니다. 전체 workflow에서는 mapping, crosswalk, active-effort까지 포함해 14개 반환 파일을 추적합니다.
- 추가로 current corpus 전체 214개 chunk를 검수할 수 있는 optional expansion scaffold를 생성했습니다.
- 기존 120개에 포함되지 않은 remaining 94 chunk 검수 패키지도 별도로 만들었습니다.
- KG 구조 진단을 추가해 ontology conformance, procedural consistency, structural CQ answerability를 분리 평가했습니다.
- 구조 진단에서 발견된 미완성 표현은 자동 수정하지 않고, 45개 review checkpoint 후보와 4개 gateway branch gap worklist로 분리했습니다.
- 300-500 chunk 수준의 강한 full-paper claim은 현재 corpus만으로는 부족하며, 300개 기준으로 86개 chunk gap이 남아 있습니다.
- 따라서 교수님께는 "최소 제출 가능 경로: 120개 human-gold", "강화 경로: 214개 전체 검수", "더 강한 경로: source 추가 또는 chunk 재분할"의 세 선택지로 보고하는 것이 좋습니다.

---

## Slide 1. 제목

### 슬라이드 제목
CAPE-KG: 한국어 수주/제안 업무 문서 기반 Evidence-Grounded Procedural KG 구축

### 핵심 메시지
한국어 장문 업무 문서에서 업무 절차 지식을 추출하고, 각 노드와 엣지를 원문 근거에 연결하는 지식그래프 구축 방법론입니다.

### 슬라이드 본문
- 연구 대상: 한국어 수주/제안 업무 OCR 문서
- 연구 목표: evidence-grounded procedural KG construction
- 핵심 산출물:
  - Layer 1 NCS/PCF 표준 KG
  - Layer 2 수주/제안 업무 절차 KG
  - Layer 2와 NCS/PCF 간 mapping candidate
  - Layer 2 bridge 기반 NCS-PCF crosswalk candidate
  - KG viewer, GraphML, Neo4j import package
  - Qwen3-8B/14B/32B-AWQ 기반 baseline, ablation, model-scaling diagnostic
  - KG structural diagnostics 및 structural gap worklist
  - human-gold annotation/adjudication, mapping expert review, active-review effort handoff package
  - optional all-available 214-chunk annotation expansion scaffold

### 발표자 설명
첫 슬라이드에서 "KG 구축 자체는 완료되었지만, 성능 우수성 주장은 human-gold 이후로 분리했다"는 점을 먼저 말합니다.

---

## Slide 2. 현재 상태 요약

### 슬라이드 제목
자동 구축은 완료, 최종 논문 claim은 보류

### 핵심 메시지
현재 연구는 build와 실험 인프라가 갖춰진 상태이며, 사람 검수를 통해 최종 main table을 확정하는 단계입니다.

### 슬라이드 본문
| 구분 | 현재 상태 | 발표 시 표현 |
| --- | --- | --- |
| Layer 1 KG | 완료 | NCS/PCF 표준 기준축 구축 완료 |
| Layer 2 KG | 완료 | 수주/제안 업무 절차 KG 구축 완료 |
| Mapping candidate | 완료 | NCS/PCF 후보 생성 완료, expert review 대기 |
| NCS-PCF crosswalk candidate | 완료 | Layer2 bridge 기반 후보 220개 생성, expert review 대기 |
| LLM baseline/ablation | 실행 완료 | 120개 chunk 기준 실행 커버리지 확보 |
| Model scaling | 실행 완료 | Qwen3-8B/14B/32B-AWQ 진단 완료 |
| Public benchmark adapter | 실행 완료 | 보조 일반화 실험으로 사용 가능 |
| Human review handoff | 준비 완료 | annotator, adjudicator, mapping expert, active effort bundle 생성 |
| Optional annotation expansion | 준비 완료 | 전체 214개 current-corpus chunk 검수 scaffold 생성 |
| KG structural diagnostics | 생성 완료 | ontology=1.0000, procedural=0.9950, structural CQ=0.9167 |
| Structural gap worklist | 준비 완료 | review checkpoint 후보 45개, gateway branch gap 4개 |
| Pre-human validation | PASS | current check count: see `../06_release/pre_human_handoff_validation.md` |
| Claim gate | FAIL | human-gold 미완료로 인한 expected fail |

### 발표자 설명
여기서 FAIL은 실험 실패가 아니라 보수적 claim gate입니다. 아직 사람이 검수하지 않은 결과를 논문 성능으로 주장하지 않도록 막는 장치입니다.

---

## Slide 3. 왜 연구 방향을 수정했는가?

### 슬라이드 제목
도메인 KG 구축 사례에서 평가 가능한 NLP task로 전환

### 핵심 메시지
단순한 온톨로지 구축 사례가 아니라, 장문 업무 문서에서 근거 기반 procedural KG를 추출하는 평가 가능한 연구로 재정의했습니다.

### 슬라이드 본문
| 기존 표현 | 수정된 표현 |
| --- | --- |
| 수주/제안 업무 온톨로지 구축 | evidence-grounded procedural KG construction |
| 내부 도메인 KG 구축 | 장문 업무 문서 기반 node/edge/evidence extraction |
| NCS/PCF 연결 | standard taxonomy bridge |
| 내부 검수 중심 | human-gold, IAA, adjudication, expert review |
| 결과물 중심 | method, evaluation, ablation, reproducibility 중심 |

### 발표자 설명
방법론을 버린 것이 아니라, 학회 논문으로 설득 가능하도록 framing을 바꾼 것입니다. 핵심은 "업무 KG를 만들었다"에서 "근거 기반 절차형 KG 추출 과제를 정의하고 평가한다"로 바꾼 점입니다.

---

## Slide 4. 연구 문제

### 슬라이드 제목
한국어 장문 업무 문서에서 절차형 지식을 어떻게 신뢰성 있게 KG로 만들 것인가?

### 핵심 메시지
본 연구는 triple 수를 늘리는 문제가 아니라, 업무 실행 구조를 원문 evidence와 함께 구조화하고 검증하는 문제입니다.

### 슬라이드 본문
연구 질문:

1. 업무 task, step, input, output, role, decision, risk를 어떻게 구조화할 것인가?
2. 각 node와 edge가 원문 어느 sentence/page/chunk에 근거하는지 어떻게 추적할 것인가?
3. LLM 출력이 schema, predicate, domain/range, evidence 조건을 만족하는지 어떻게 검증할 것인가?
4. 구축된 업무 KG를 NCS/PCF 표준 taxonomy와 어떻게 연결할 것인가?
5. human-gold annotation으로 이 방법을 어떻게 정량 평가할 것인가?

### 발표자 설명
일반적인 문서 요약이나 entity extraction이 아니라, "업무가 어떤 순서로 진행되고 무엇을 입력/산출물로 사용하는가"를 구조화하는 것이 핵심입니다.

---

## Slide 5. CAPE-KG 방법론

### 슬라이드 제목
CAPE-KG: CQ, schema, evidence, validator, standard bridge의 결합

### 핵심 메시지
CAPE-KG는 LLM이 자유롭게 triple을 생성하는 방식이 아니라, 질문과 구조와 근거와 검증을 먼저 정의한 뒤 LLM을 그 안에서 사용합니다.

### 슬라이드 본문
| 구성 요소 | 역할 |
| --- | --- |
| Competency Question | KG가 답해야 할 업무 질문 정의 |
| Procedural Schema | DomainTask, ProcedureStep, Artifact, Role 등 구조화 |
| Evidence Grounding | node/edge를 OCR sentence, page, chunk와 연결 |
| Validator | schema, predicate, evidence, parse quality 검증 |
| Standard Bridge | Layer 2 업무 KG를 NCS/PCF 표준과 연결 |
| Active Review | 사람 검수가 필요한 항목을 우선순위화 |

### 발표자 설명
이 방법론의 차별점은 LLM output을 그대로 믿지 않고, evidence와 validator를 통해 claim 가능한 구조로 만드는 것입니다.

---

## Slide 6. 전체 파이프라인

### 슬라이드 제목
실제로 실행한 CAPE-KG 파이프라인

### 핵심 메시지
OCR 정제부터 KG 구축, LLM 실험, Neo4j/HTML 시각화, human-review handoff까지 재현 가능한 파이프라인으로 실행했습니다.

### 슬라이드 본문
1. OCR workbook 정제 및 sentence-level evidence anchor 생성
2. NCS/PCF Layer 1 표준 KG 구축
3. Layer 2 업무 chunk 생성 및 120개 evaluation chunk 선정
4. CQ, schema, prompt, validator 구성
5. DomainTask, ProcedureStep, Artifact, Role 등 task frame 구축
6. evidence-supported procedural triple 생성
7. Layer 2 업무 KG와 NCS/PCF mapping candidate 생성
8. Layer 2 bridge 기반 NCS-PCF crosswalk candidate 생성
9. HTML viewer, GraphML, Neo4j CSV/Cypher 생성
10. Qwen3-8B/14B/32B-AWQ baseline, ablation, model-scaling 실행
11. public benchmark adapter 실행
12. ontology/procedural/CQ 구조 진단 및 structural gap worklist 생성
13. human-gold annotation/adjudication/mapping/active-effort handoff 생성
14. claim gate, paper table, release bundle, checksum 검증

### 발표자 설명
자동 파이프라인과 산출물은 만들어졌고, 이제 사람 검수 결과를 넣으면 final paper table로 전환되는 구조입니다.

---

## Slide 7. 데이터와 Evidence Anchor

### 슬라이드 제목
입력 데이터와 evidence grounding

### 핵심 메시지
KG의 accepted edge가 원문 sentence로 돌아갈 수 있도록 OCR sentence를 evidence anchor로 유지했습니다.

### 슬라이드 본문
| 항목 | 값 |
| --- | ---: |
| OCR clean sentence / evidence anchor | 5,009 |
| Layer 2 chunks | 214 |
| Evaluation chunks | 120 |
| Silver reference nodes | 169 |
| Silver reference edges | 861 |
| Silver evidence anchors | 293 |

### 발표자 설명
현재 reference는 KG-derived silver입니다. 최종 논문 성능은 이 silver가 아니라 adjudicated human-gold로 다시 계산해야 합니다.

---

## Slide 7A. Evidence Span Granularity

### 슬라이드 제목
sentence-level evidence에서 component-level span 진단으로 확장

### 핵심 메시지
accepted triple은 sentence evidence anchor를 가지고 있으며, 추가로 subject/object label이 원문 sentence 안에서 발견되는 경우 character span을 자동 산출했습니다.

### 슬라이드 본문
| 항목 | 값 |
| --- | ---: |
| Layer2 triples | 906 |
| Triple components | 2,718 |
| Exact component spans | 736 |
| Subject exact span rate | 0.2395 |
| Object exact span rate | 0.5728 |
| Predicate full-sentence proxy rate | 1.0000 |

해석:

- sentence-level evidence grounding은 이미 KG에 포함되어 있음
- subject/object는 label exact match가 가능한 경우 character span을 추가 산출
- predicate는 아직 token-level span이 아니라 sentence-level proxy
- 최종 evidence exactness claim은 human-gold span annotation 이후 가능

### 발표자 설명
이 슬라이드는 evidence grounding을 과장하지 않기 위한 장치입니다. "모든 것이 완전한 character-level gold span"이라고 말하지 않고, 현재 자동 진단 수준과 human-gold 필요성을 분리해서 설명합니다.

---

## Slide 8. Layer 1 표준 KG 구축 결과

### 슬라이드 제목
NCS/PCF 표준 기준축 구축

### 핵심 메시지
Layer 1은 도메인 문서에서 추출한 것이 아니라, NCS와 PCF 표준 체계를 안정적인 기준축으로 KG화한 것입니다.

### 슬라이드 본문
| 표준 | Nodes | Edges | 구성 |
| --- | ---: | ---: | --- |
| NCS | 4,109 | 4,085 | competency unit 3,450개 포함 |
| PCF | 5,301 | 5,288 | HAS_CHILD 2,004 + HAS_METRIC 3,284 |
| 합계 | 9,410 | 9,373 | Layer 1 standard grounding layer |

품질 점검:

- NCS endpoint missing count: 0
- NCS duplicate node ID count: 0
- PCF metric orphan count: 0
- Layer 1 gate: PASS

### 발표자 설명
PCF edge는 두 파일로 나뉘어 있습니다. `layer1_pcf_edges.jsonl`에는 HAS_CHILD 2,004개, `layer1_pcf_metric_edges.jsonl`에는 HAS_METRIC 3,284개가 있어 합계 5,288개입니다.

---

## Slide 9. Layer 2 업무 KG 구축 결과

### 슬라이드 제목
수주/제안 업무 절차 KG 구축 완료

### 핵심 메시지
Layer 2는 한국어 수주/제안 업무 문서에서 구축된 도메인 업무 절차 KG입니다.

### 슬라이드 본문
| 항목 | 값 |
| --- | ---: |
| Layer 2 nodes | 179 |
| Layer 2 edges | 906 |
| Evidence anchors | 5,009 |
| Dangling edges | 0 |
| Evidence-missing accepted edges | 0 |
| Type violations | 0 |

주요 node type:

| Node type | Count |
| --- | ---: |
| ProcedureStep | 99 |
| DomainTask | 22 |
| Artifact | 14 |
| GuardCondition | 13 |
| Role | 10 |

### 발표자 설명
이 결과는 "업무 절차 KG 구축 완료"로 말할 수 있습니다. 단, LLM이 더 잘한다는 성능 주장은 별도의 human-gold evaluation 문제입니다.

---

## Slide 10. 절차형 Edge 구조

### 슬라이드 제목
업무 흐름을 표현하는 predicate 체계

### 핵심 메시지
Layer 2 KG는 업무가 어떤 입력을 사용하고, 어떤 산출물을 만들며, 어떤 순서로 수행되는지 질의할 수 있는 구조입니다.

### 슬라이드 본문
| Predicate | Count | 의미 |
| --- | ---: | --- |
| PRODUCES | 220 | task/step이 생성하는 산출물 |
| USES_INPUT | 201 | task/step이 사용하는 입력 |
| PERFORMED_BY | 120 | 수행자/책임자 |
| HAS_STEP | 99 | task와 procedure step 연결 |
| PRECEDES | 77 | 절차 순서 |
| HAS_PRINCIPLE | 64 | 원칙/가이드라인 |
| HAS_DECISION_GATEWAY | 54 | 의사결정 지점 |
| HAS_RISK | 39 | 위험 요소 |

### 발표자 설명
일반 triple이 아니라 업무 실행 구조를 담는 predicate를 사용한 것이 방법론적 차이입니다.

---

## Slide 10A. KG 구조 진단과 Gap Worklist

### 슬라이드 제목
KG 구조 진단: 잘 된 부분과 검수할 부분을 분리

### 핵심 메시지
현재 KG는 ontology/domain-range/evidence 조건은 모두 통과했지만, 논문 claim을 안전하게 만들기 위해 구조적으로 보강할 항목을 별도 worklist로 분리했습니다.

### 슬라이드 본문
| 진단 항목 | 현재 값 | 해석 |
| --- | ---: | --- |
| Ontology conformance | 1.0000 | unknown type/predicate, dangling edge, domain-range violation 없음 |
| Evidence-missing accepted edges | 0 | accepted edge는 evidence anchor를 보유 |
| Procedural consistency | 0.9950 | precedence cycle 없음, warning 중심 |
| Structural CQ answerability | 0.9167 | 12개 CQ 중 11개 구조적으로 answerable |
| Review checkpoint candidates | 45 | 현재 task/step으로 표현된 리뷰/점검 후보 |
| Gateway branch gaps | 4 | guard는 있으나 explicit branch edge가 없는 gateway |

검수 대상:

- `structural_review_checkpoint_candidates.csv`: 리뷰/점검 개념을 `ReviewCheckpoint`로 승격할지 판단
- `structural_gateway_branch_gaps.csv`: decision gateway의 branch target을 명시할지 판단

### 발표자 설명
이 슬라이드의 핵심은 "자동으로 KG를 고쳐 성능을 올렸다"가 아닙니다. 구조 진단 결과를 사람 검수 가능한 worklist로 바꿨고, human review 전에는 KG를 임의로 수정하지 않았다는 점입니다.

---

## Slide 11. NCS/PCF Mapping Candidate

### 슬라이드 제목
업무 KG와 표준 taxonomy 연결 후보 생성

### 핵심 메시지
Layer 2 업무 task를 NCS/PCF 표준 체계와 연결하는 후보는 생성되었지만, 성능 지표는 expert review 이후에만 주장할 수 있습니다.

### 슬라이드 본문
| 항목 | 값 |
| --- | ---: |
| NCS mapping candidates | 110 |
| PCF mapping candidates | 110 |
| Total mapping review rows | 220 |
| Source task groups | 44 |
| Shared Layer2 tasks for crosswalk | 22 |
| NCS-PCF all crosswalk pairs | 550 |
| NCS-PCF top crosswalk candidates | 220 |
| Completed expert-review groups | 0 |
| Current claim status | pending expert review |

### 발표자 설명
이 단계는 후보 생성 완료입니다. Hit@K, P@5, MRR, nDCG@10, explanation quality, crosswalk accept-rate 같은 성능은 아직 말하면 안 됩니다.

---

## Slide 12. Mapping Downstream 비교 설계

### 슬라이드 제목
Text-only vs Task Frame vs Flat Triples vs Procedural KG 비교 준비

### 핵심 메시지
수정된 계획에 맞춰 mapping downstream 평가를 representation-arm 비교로 정리했습니다. 현재 값은 expert review 전 진단용 rerank입니다.

### 슬라이드 본문
| Arm | 의미 | 현재 해석 |
| --- | --- | --- |
| text_only_task_description | task label/definition만 사용 | lexical baseline |
| task_frame_only | task frame slot 사용 | 구조화된 task 정보 |
| flat_triples | typed triple 사용 | 절차 흐름은 약한 KG 표현 |
| procedural_kg_with_evidence | KG/evidence bridge feature 사용 | 현재 full scoring arm |

현재 diagnostic:

| Standard | Candidate groups | Candidate rows | 상태 |
| --- | ---: | ---: | --- |
| NCS | 22 | 110 | expert review 전 rerank diagnostic |
| PCF | 22 | 110 | expert review 전 rerank diagnostic |

### 발표자 설명
이 슬라이드에서는 성능 수치보다 "비교 설계가 마련되었다"는 점을 강조합니다. expert review가 들어오면 같은 source-task group에 대해 P@5, Hit@5, MRR, nDCG@10, explanation quality를 계산할 수 있습니다.

---

## Slide 13. Mapping Diagnostic 예시

### 슬라이드 제목
현재 mapping 비교표는 claim이 아니라 검증 scaffold

### 핵심 메시지
Top-5 후보 universe 안에서 arm별 proxy score로 rerank한 진단표를 만들었습니다. 이는 final mapping result가 아닙니다.

### 슬라이드 본문
| Standard | Arm | Top-1 agreement with full score | Mean top1 proxy | Claim status |
| --- | --- | ---: | ---: | --- |
| NCS | text_only_task_description | 0.3182 | 0.3098 | diagnostic only |
| NCS | task_frame_only | 0.2727 | 0.3395 | diagnostic only |
| NCS | flat_triples | 0.2273 | 0.3401 | diagnostic only |
| NCS | procedural_kg_with_evidence | 0.3182 | 0.2574 | diagnostic only |
| PCF | text_only_task_description | 0.4091 | 0.3249 | diagnostic only |
| PCF | task_frame_only | 0.3636 | 0.3602 | diagnostic only |
| PCF | flat_triples | 0.3636 | 0.3430 | diagnostic only |
| PCF | procedural_kg_with_evidence | 0.3182 | 0.2710 | diagnostic only |

### 발표자 설명
agreement는 full score의 Top-1과 얼마나 같은 후보를 고르는지 보는 내부 진단입니다. expert label이 없으므로 이 표를 "정확도"로 해석하면 안 됩니다.

---

## Slide 14. LLM 사용 범위

### 슬라이드 제목
LLM은 구축 방법론 평가와 비교 실험에 사용

### 핵심 메시지
현재 실험에서는 Qwen3 계열을 사용해 baseline, ablation, model scaling을 실행했습니다.

### 슬라이드 본문
사용한 모델:

- Qwen3-8B
- Qwen3-14B
- Qwen3-32B-AWQ
- Llama-2-13B-chat smoke/model-compatibility run

사용 목적:

- plain LLM baseline
- predicate-constrained baseline
- current project baseline
- CAPE-KG proposed condition
- CAPE-KG ablation
- model scaling diagnostic
- public benchmark adapter

### 발표자 설명
LLM은 필요 없었던 것이 아니라, KG 구축 후 방법론 비교와 평가를 위해 사용했습니다. 다만 현재 LLM 점수는 human-gold가 아니라 silver/proxy 기준입니다.

---

## Slide 15. LLM 실행 커버리지

### 슬라이드 제목
실제 LLM 실행은 완료되었고, human-gold scoring만 남음

### 핵심 메시지
120개 evaluation chunk 기준으로 baseline, proposed, ablation 실행 커버리지는 확보했습니다.

### 슬라이드 본문
| Gate | 상태 | 내용 |
| --- | --- | --- |
| B0/B1/B2 baseline generation | PASS | 각 120 rows |
| P_cape_kg_actual generation | PASS | 120 rows |
| Ablation generation | PASS | 6개 extraction ablations + active-review ablation diagnostic |
| Output recovery gate | PASS | unrepaired error <= 5% |
| Strict JSON gate | PASS | strict parse/generation error <= 50% |
| Proposed human-gold score | FAIL | adjudicated human-gold 미완료 |

### 발표자 설명
생성 자체는 끝났지만, 사람이 확정한 gold label과 비교하지 않았으므로 "성능이 좋다"는 말은 보류합니다.

---

## Slide 16. Actual LLM Silver Diagnostic

### 슬라이드 제목
Silver 기준 진단 결과는 debugging 용도

### 핵심 메시지
현재 LLM 수치는 KG-derived silver reference와 비교한 값이므로 최종 성능표가 아니라 모델 동작 진단표입니다.

### 슬라이드 본문
| Condition | Edge F1 | Predicate F1 | Node F1 | Evidence F1 | 상태 |
| --- | ---: | ---: | ---: | ---: | --- |
| B0_plain_llm | 0.0000 | 0.0000 | 0.0350 | 0.0239 | silver diagnostic |
| B1_predicate_constrained | 0.0000 | 0.1416 | 0.0000 | 0.0291 | silver diagnostic |
| B2_current_project | 0.0000 | 0.0068 | 0.0215 | 0.0503 | silver diagnostic |
| B6_sac_kg_verifier_pruner | 0.0017 | 0.0774 | 0.0564 | 0.1008 | deterministic approximation |
| P_cape_kg_actual | 0.0018 | 0.0482 | 0.0326 | 0.0655 | silver diagnostic |

### 발표자 설명
이 표는 성능 우수성 주장이 아니라, 어떤 조건이 어떤 유형의 output을 내는지 확인하는 sanity check입니다.

---

## Slide 17. Model Scaling

### 슬라이드 제목
Qwen3-8B, 14B, 32B-AWQ까지 실행 완료

### 핵심 메시지
현재 서버의 8개 GPU를 활용해 32B-AWQ까지 현실적인 범위의 local open-weight 모델을 실행했습니다.

### 슬라이드 본문
| Model | Condition | Rows | Edge F1 | Predicate F1 | Evidence F1 | 상태 |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| Qwen3-8B | P_cape_kg_actual | 120 | 0.0018 | 0.0482 | 0.0655 | silver diagnostic |
| Qwen3-14B | P_cape_kg_actual | 120 | 0.0017 | 0.0601 | 0.0610 | silver diagnostic |
| Qwen3-32B-AWQ | P_cape_kg_actual | 120 | 0.0034 | 0.0662 | 0.0542 | silver diagnostic |

실행 환경:

- GPUs 0-7 사용 가능
- 8 x RTX 3090, 24GB
- Qwen3-32B-AWQ cached and run complete
- Standard Qwen3-32B는 디스크 여유 공간 부족으로 현재 비권장

### 발표자 설명
32B-AWQ가 현재 가장 큰 local open-weight diagnostic입니다. 하지만 이 역시 human-gold 전에는 최종 성능 주장이 아닙니다.

---

## Slide 18. Public Benchmark Adapter

### 슬라이드 제목
외부 benchmark는 보조 일반화 근거로 사용

### 핵심 메시지
public benchmark adapter를 통해 한국어 내부 문서 외의 KG extraction benchmark에도 실행 경로를 만들었습니다.

### 슬라이드 본문
| Run | PAGED n | PAGED edge F1 | Text2KG n | Relation F1 | Triple F1 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Qwen3-8B full adapter | 100 | 0.4233 | 200 | 0.6015 | 0.1736 |
| Qwen3-14B subset | 10 | 0.1446 | 20 | 0.2817 | 0.0200 |
| Qwen3-8B subset | 10 | 0.1794 | 20 | 0.4500 | 0.0500 |

### 발표자 설명
이 결과는 auxiliary claim으로 사용할 수 있지만, 논문의 main result는 한국어 수주/제안 데이터의 human-gold 평가가 되어야 합니다.

---

## Slide 18A. Active Review Ablation Diagnostic

### 슬라이드 제목
P - Active Review ablation scaffold 추가

### 핵심 메시지
계획서의 `P - Active review` 항목을 명시적으로 추적하기 위해 active-priority queue와 active review 제거 조건을 비교하는 silver/proxy 진단표를 추가했습니다.

### 슬라이드 본문
| Condition | Strategy | Budget | High-impact errors | Precision@k | Lift | 상태 |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| P_cape_kg_actual_with_active_review | active_priority | 25 | 16 | 0.6400 | 1.0173 | silver diagnostic |
| P_minus_Active_review_random_expected | random_expected | 25 | 15.7273 | 0.6291 | 1.0000 | silver diagnostic |
| P_minus_Active_review_uncertainty_only | uncertainty_only | 25 | 15 | 0.6000 | 0.9538 | silver diagnostic |
| P_cape_kg_actual_with_active_review | active_priority | 55 | 36 | 0.6545 | 1.0405 | silver diagnostic |
| P_minus_Active_review_random_expected | random_expected | 55 | 34.6000 | 0.6291 | 1.0000 | silver diagnostic |

### 발표자 설명
이 표는 active review 효율이 입증되었다는 뜻이 아닙니다. 계획서의 ablation scaffold가 준비되었고, 최종 효율 주장은 human-effort reviewed CSV와 adjudicated label이 들어온 뒤 다시 계산해야 합니다.

---

## Slide 19. Human Review Handoff

### 슬라이드 제목
사람 검수 패키지는 준비 완료

### 핵심 메시지
annotator, coordinator, adjudicator, mapping expert, active-review effort bundle을 모두 생성했습니다.

### 슬라이드 본문
생성된 bundle:

- Annotator A priority100 bundle
- Annotator B priority100 bundle
- Coordinator priority100 bundle
- Adjudicator full120 bundle
- Mapping expert top20 groups bundle
- Active-review human-effort bundle
- Handoff checksums
- Korean start-here guide

Required return files:

| 유형 | 파일 수 | 상태 |
| --- | ---: | --- |
| Annotation reviewed JSONL | 10 | pending |
| Adjudication edited JSONL | 1 | pending |
| Mapping expert reviewed JSONL | 1 | pending |
| Active-review effort reviewed CSV | 1 | pending |
| 합계 | 13 | pending |

### 발표자 설명
현재 사람이 검수해서 돌려줘야 할 파일은 14개입니다. 반환되면 import script와 validation script로 다시 전체 리포트를 갱신합니다.

---

## Slide 19A. Optional Annotation Expansion

### 슬라이드 제목
검수 범위 확장안: 120개 필수 gate와 214개 전체 corpus scaffold 분리

### 핵심 메시지
현재 minimum paper-gate에 필요한 필수 반환 파일은 11개이며, mapping/crosswalk/active-effort까지 포함한 전체 추적 반환 파일은 14개입니다. 추가로 current corpus 전체 214개 chunk를 검수할 수 있는 선택적 확장 패키지를 준비했습니다.

### 슬라이드 본문
| 항목 | 값 | 해석 |
| --- | ---: | --- |
| 현재 Layer2 chunk 전체 | 214 | 현재 OCR corpus에서 사용 가능한 전체 chunk |
| 필수 full package | 120 | 현 claim gate와 human-gold scoring의 중심 |
| 선택적 추가 chunk | 94 | 기존 120개에 포함되지 않은 나머지 chunk |
| all-available package | 214 | 전체 corpus 검수를 위한 선택 scaffold |
| 300 chunk strong target gap | 86 | 현재 corpus만으로는 300개 목표 도달 불가 |
| required return file 변화 | 0 | minimum paper-gate 11개는 유지, 전체 추적 반환은 14개로 관리 |

생성 파일:

- `experiments/cape_kg_eacl_20260627/01_data/gold_annotation/all_available_214/`
- `experiments/cape_kg_eacl_20260627/01_data/gold_annotation/remaining_94_text_only/`
- `experiments/cape_kg_eacl_20260627/01_data/gold_annotation/annotation_expansion_report.md`

### 발표자 설명
교수님께는 "최소 제출 가능 경로는 120개 검수이고, 더 강한 full-paper claim을 원하면 214개 전체 검수까지 확장할 수 있다. 다만 300-500 chunk claim은 현재 source를 추가하거나 chunk를 더 세분화해야 한다"라고 설명하면 됩니다.

---

## Slide 20. Pre-Human Validation

### 슬라이드 제목
검수 시작 전 handoff validation은 PASS

### 핵심 메시지
사람 검수를 시작하기 위한 파일, bundle, checksum, safety scan은 통과했습니다.

### 슬라이드 본문
| 항목 | 값 |
| --- | ---: |
| Total checks | 21 |
| PASS | 20 |
| WARN | 1 |
| FAIL | 0 |
| Claim status | pre_human_handoff_ready_not_submission_complete |

대표 PASS 항목:

- required files present
- handoff bundle checksum
- annotation roundtrip smoke
- mapping roundtrip smoke
- claimable main table safety
- EACL paper draft claim safety
- Neo4j CSV validation
- public-safe bundle risk scan
- release bundle checksum

### 발표자 설명
WARN은 human-gold가 아직 없다는 알려진 blocker를 표시하기 위한 것입니다. 인프라 문제는 아닙니다.

---

## Slide 21. Claim Gate

### 슬라이드 제목
현재 claim gate는 의도적으로 FAIL

### 핵심 메시지
성능 주장을 막는 4개 required failure와 1개 optional failure가 남아 있습니다.

### 슬라이드 본문
Required failures:

| Gate | 현재 상태 | 필요한 것 |
| --- | --- | --- |
| gold.completed_chunks | 0 completed | 100+ adjudicated chunks |
| gold.item_count | 0 items | 500+ gold node/edge/evidence items |
| gold.iaa | 0 paired chunks | 100+ paired IAA chunks |
| llm.proposed_human_gold_score | none | P_cape_kg_actual human-gold scoring |

Optional failure:

| Gate | 현재 상태 | 필요한 것 |
| --- | --- | --- |
| mapping.expert_review | 0 complete groups, 220 pending rows | Top-5 mapping expert review |

### 발표자 설명
claim gate FAIL은 좋은 상태입니다. 아직 검수되지 않은 결과를 논문 주장으로 쓰지 않도록 막고 있기 때문입니다.

---

## Slide 22. 현재 Main Table의 의미

### 슬라이드 제목
현재 table은 final performance table이 아니라 claimability table

### 핵심 메시지
지금 있는 main table은 어떤 결과를 논문 claim으로 쓸 수 있는지 구분하는 보수적 표입니다.

### 슬라이드 본문
| Result | 현재 claimability | 현재 값 |
| --- | --- | --- |
| Core extraction main result | pending_human | human-gold F1 not claimable |
| Actual LLM run coverage | claimable_setup | B0/B1/B2/P 120 rows |
| Optional annotation expansion | claimable_setup | all_available=214, remaining_optional=94, strong_300_gap=86 |
| CAPE-KG silver diagnostic | diagnostic_only | edge=0.0018, predicate=0.0482, evidence=0.0655 |
| KG structural diagnostics | diagnostic_only | ontology/procedural/CQ answerability, human-gold 전 구조 진단 |
| Structural gap worklist | claimable_setup | review_checkpoint_candidates=45, gateway_branch_gaps=4 |
| Public benchmark adapter | auxiliary_claimable | PAGED 100, Text2KG 200 |
| NCS/PCF mapping downstream | pending_expert_review | pending_rows=220, crosswalk_candidates=220 |
| Active-review ablation | diagnostic_only | ablation_rows=24 |
| Release/reproducibility package | claimable_setup | PASS |
| Submission claim gate | not_ready | FAIL, required_failures=4 |

### 발표자 설명
이 슬라이드는 교수님께 "지금 main table이 있느냐"라는 질문에 답하는 용도입니다. 있습니다. 하지만 final performance table은 아닙니다.

---

## Slide 23. 시각화와 재현성 산출물

### 슬라이드 제목
KG를 확인하고 재현할 수 있는 산출물 준비

### 핵심 메시지
HTML viewer, Neo4j import, release bundle, paper draft, checksum까지 준비되어 있습니다.

### 슬라이드 본문
| 목적 | 파일 |
| --- | --- |
| HTML KG viewer | `outputs/09_visualization/kg_viewer.html` |
| Neo4j flat import | `outputs/11_neo4j_import_flat/` |
| Neo4j validation | `outputs/11_neo4j_import_flat/neo4j_csv_validation_report.json` |
| Final build report | `outputs/10_evaluation/final_build_report.md` |
| Claim gate | `experiments/cape_kg_eacl_20260627/06_release/claim_gate_report.md` |
| Submission completion audit | `experiments/cape_kg_eacl_20260627/06_release/submission_completion_audit_ko.md` |
| Paper tables | `experiments/cape_kg_eacl_20260627/06_release/paper_tables.md` |
| Evidence span granularity report | `experiments/cape_kg_eacl_20260627/04_evaluation/evidence_span_granularity_report.md` |
| Structural evaluation report | `experiments/cape_kg_eacl_20260627/04_evaluation/structural_evaluation_report.md` |
| Structural gap worklist report | `experiments/cape_kg_eacl_20260627/04_evaluation/structural_gap_worklist_report.md` |
| NCS-PCF crosswalk report | `experiments/cape_kg_eacl_20260627/04_evaluation/ncs_pcf_crosswalk_report.md` |
| Active-review ablation report | `experiments/cape_kg_eacl_20260627/04_evaluation/active_review_ablation_report.md` |
| Optional annotation expansion report | `experiments/cape_kg_eacl_20260627/01_data/gold_annotation/annotation_expansion_report.md` |
| EACL draft | `experiments/cape_kg_eacl_20260627/07_reports/eacl_paper_draft.md` |
| Release bundle | `experiments/cape_kg_eacl_20260627/06_release/release_bundle_manifest.json` |

### 발표자 설명
교수님께 실제 산출물이 파일 단위로 정리되어 있고, Neo4j와 HTML viewer로 볼 수 있다고 설명합니다.

---

## Slide 24. 선행 연구와의 연결

### 슬라이드 제목
기존 KG extraction 연구와 비교 가능한 평가축 확보

### 핵심 메시지
Paged, Text2KGBench, EDC, SAC-KG 등 선행 연구와 연결되는 baseline과 비교축을 마련했습니다.

### 슬라이드 본문
| 선행 연구 축 | 현재 반영 방식 |
| --- | --- |
| PAGED | public procedural graph benchmark adapter |
| Text2KGBench | ontology-guided KG generation adapter |
| EDC | Extract-Define-Canonicalize style baseline 및 schema retrieval ablation |
| SAC-KG | generator/verifier/pruner approximation baseline |
| Llama/Vicuna/ChatGPT 계열 | prior-work context로 정리, local run은 Qwen3 중심 |
| Qwen3-8B/14B/32B-AWQ | 현재 서버에서 실행 가능한 local open-weight scaling |

### 발표자 설명
선행 연구와 완전히 동일한 reproduction은 아니지만, 논문에서 요구되는 비교 가능성은 baseline, ablation, public adapter로 확보했습니다.

---

## Slide 25. 남은 작업

### 슬라이드 제목
다음 단계는 사람 검수 결과를 넣어 final table로 전환하는 것

### 핵심 메시지
자동 실험을 더 많이 돌리는 것보다, 이제는 human-gold와 expert review를 완료하는 것이 핵심입니다.

### 슬라이드 본문
우선순위:

1. Annotator A/B가 priority100 batch 5개씩 검수
2. IAA 계산
3. Adjudicator가 full120 adjudication file 편집
4. Adjudicated human-gold 생성
5. P_cape_kg_actual과 baselines를 human-gold로 scoring
6. NCS/PCF Top-5 mapping expert review
7. Active-review human-effort reviewed CSV 수집
8. Structural gap worklist에서 review checkpoint 후보와 gateway branch gap 검수
9. 선택적으로 remaining 94 chunk 또는 all-available 214 chunk 검수 확장
10. Final performance main table 생성
11. EACL paper draft claim wording 업데이트

### 발표자 설명
교수님께 "다음 병목은 GPU가 아니라 사람 검수"라고 말하면 됩니다. GPU 실험은 32B-AWQ까지 충분히 진행했습니다.

---

## Slide 26. 예상 Contribution

### 슬라이드 제목
논문 contribution 정리

### 핵심 메시지
최종 논문은 단순 KG 구축보다, evidence-grounded procedural KG construction task와 평가 체계를 contribution으로 제시해야 합니다.

### 슬라이드 본문
예상 contribution:

1. 한국어 수주/제안 문서 기반 evidence-grounded procedural KG construction task 정의
2. CQ-anchored schema, evidence grounding, validator, standard bridge를 결합한 CAPE-KG 방법론
3. NCS/PCF 표준 체계와 업무 KG를 연결하는 taxonomy bridge
4. baseline, ablation, model scaling, public benchmark adapter를 포함한 평가 프레임
5. human-gold annotation, IAA, adjudication, mapping expert review, active-review effort까지 포함한 검증 프로토콜

### 발표자 설명
"온톨로지를 만들었다"가 아니라 "장문 업무 문서에서 근거 기반 procedural KG를 만드는 task와 방법론을 제안한다"로 정리해야 합니다.

---

## Slide 27. 교수님께 논의드릴 사항

### 슬라이드 제목
교수님께 확인받을 의사결정

### 핵심 메시지
현재 자동 구축과 실험 실행은 충분히 정리되었으므로, 다음 결정은 annotation 범위와 논문 claim 범위입니다.

### 슬라이드 본문
논의 요청:

1. 최소 100 chunk human-gold로 EACL submission을 목표로 할지
2. 214 chunk 전체 current-corpus 검수까지 확장할지
3. 300-500 chunk까지 확장하려면 source 추가 또는 chunk 재분할을 진행할지
4. NCS/PCF expert review를 priority top20 groups까지만 할지, 전체 44 groups로 확장할지
5. Active-review human-effort 실험을 본문에 넣을지 appendix로 둘지
6. Qwen3-32B-AWQ 이후 closed API upper-bound baseline을 추가할지
7. public benchmark adapter를 auxiliary evaluation으로 얼마나 강조할지

### 발표자 설명
마지막에는 교수님이 다음 실행 방향을 쉽게 결정할 수 있도록 선택지를 제시합니다.

---

## Slide 28. 마무리

### 슬라이드 제목
정리: 구축은 완료, 주장은 human-gold 이후 확정

### 핵심 메시지
CAPE-KG는 자동 구축과 평가 인프라를 완성했고, 이제 남은 핵심은 사람 검수 기반 evidence를 채워 최종 성능 주장을 claimable하게 만드는 것입니다.

### 슬라이드 본문
한 문장 요약:

> CAPE-KG는 한국어 장문 업무 문서에서 evidence-grounded procedural KG를 구축하는 자동 파이프라인과 평가 인프라를 완성했으며, 현재는 14개 human return file을 통해 human-gold, adjudication, mapping expert review, NCS-PCF crosswalk expert review, active-review effort를 수집하는 단계입니다.

현재 상태:

- Automatic KG build: complete
- LLM runs: complete for current diagnostic scope
- Pre-human handoff: PASS
- Claim gate: FAIL, expected
- Final performance claim: pending human-gold
- Next execution: human review return import and final table regeneration

### 발표자 설명
마지막에는 "실험이 멈춘 것이 아니라, 논문 주장을 안전하게 만들기 위해 human gate를 기다리는 상태"라고 정리합니다.

---

## Appendix A. 핵심 파일 경로

| 목적 | 파일 |
| --- | --- |
| 현재 발표자료 | `experiments/cape_kg_eacl_20260627/07_reports/professor_presentation_revised_current_20260628_ko.md` |
| 현재 실험 방법론/결과 정리 | `experiments/cape_kg_eacl_20260627/07_reports/current_experiment_methodology_and_results_ko.md` |
| 최종 실험 리포트 | `experiments/cape_kg_eacl_20260627/07_reports/final_eacl_experiment_report.md` |
| claimability table | `experiments/cape_kg_eacl_20260627/06_release/claimable_main_table.md` |
| claim gate | `experiments/cape_kg_eacl_20260627/06_release/claim_gate_report.md` |
| submission completion audit | `experiments/cape_kg_eacl_20260627/06_release/submission_completion_audit_ko.md` |
| paper tables | `experiments/cape_kg_eacl_20260627/06_release/paper_tables.md` |
| mapping downstream report | `experiments/cape_kg_eacl_20260627/04_evaluation/mapping_downstream_report.md` |
| mapping arm diagnostic CSV | `experiments/cape_kg_eacl_20260627/04_evaluation/mapping_downstream_arm_diagnostics.csv` |
| structural evaluation report | `experiments/cape_kg_eacl_20260627/04_evaluation/structural_evaluation_report.md` |
| structural gap worklist report | `experiments/cape_kg_eacl_20260627/04_evaluation/structural_gap_worklist_report.md` |
| pre-human validation | `experiments/cape_kg_eacl_20260627/06_release/pre_human_handoff_validation.md` |
| human gate action plan | `experiments/cape_kg_eacl_20260627/06_release/human_gate_action_plan.md` |
| required return files | `experiments/cape_kg_eacl_20260627/05_review/human_gate_required_returns.csv` |
| optional 214-chunk annotation expansion | `experiments/cape_kg_eacl_20260627/01_data/gold_annotation/annotation_expansion_report.md` |
| KG viewer | `outputs/09_visualization/kg_viewer.html` |
| Neo4j flat import | `outputs/11_neo4j_import_flat/` |

---

## Appendix B. 발표 시 피해야 할 표현

| 피해야 할 표현 | 대체 표현 |
| --- | --- |
| CAPE-KG가 baseline보다 성능이 좋다 | 현재는 silver/proxy diagnostic이며 human-gold 이후 확정한다 |
| main table이 완성됐다 | claimability table은 있고 final performance table은 pending이다 |
| mapping 평가가 끝났다 | mapping candidate와 diagnostic scaffold는 있고 expert review가 필요하다 |
| active review가 효율적이다 | active-review effort 템플릿과 silver diagnostic은 준비됐다 |
| Qwen3-32B-AWQ 결과가 최종 성능이다 | Qwen3-32B-AWQ는 가장 큰 local diagnostic run이다 |
| claim gate FAIL이 실험 실패다 | human-gold 미완료를 감지한 expected conservative gate다 |
| 300 chunk 검수 패키지가 완성됐다 | 현재 corpus 기준 최대 214 chunk이며, 300개 이상은 source 추가 또는 chunk 재분할이 필요하다 |
| 구조 gap을 자동으로 수정했다 | 구조 gap을 human-review worklist로 분리했고 KG는 임의 수정하지 않았다 |
