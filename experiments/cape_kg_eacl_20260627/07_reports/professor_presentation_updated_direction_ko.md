# 교수님 발표자료 원고: CAPE-KG 최신 수정 방향 반영본

Generated: 2026-06-28

이 문서는 교수님께 현재까지의 연구 진행 상황을 설명하기 위한 PPT 슬라이드별 원고입니다. 실제 PPT 파일이 아니라, 각 슬라이드에 넣을 제목, 핵심 메시지, 본문, 발표자 설명을 바로 옮길 수 있도록 작성했습니다.

이번 버전의 핵심 수정 방향은 다음과 같습니다.

- KG 구축 결과와 논문 성능 주장을 분리합니다.
- 현재 KG 구축, LLM 실행, Neo4j/HTML 시각화, human-review handoff 인프라는 준비된 상태로 보고합니다.
- 그러나 "CAPE-KG가 baseline보다 우수하다"는 최종 성능 주장은 아직 하지 않습니다.
- Qwen3-8B/14B/32B-AWQ 결과는 현재 human-gold가 아닌 silver/proxy diagnostic입니다.
- 최신 추가 사항으로 adjudicator bundle, active-review human-effort 실험 템플릿, return preflight, human gate action plan이 준비되었습니다.
- 최종 main table은 human-gold annotation, IAA, adjudication, mapping expert review, NCS-PCF crosswalk expert review, active-review effort evidence 이후에 생성합니다.
- 현재 main table은 final performance table이 아니라 claimability table입니다.
- 최신 handoff 기준 required return file은 14개입니다.

---

## Slide 1. 제목

### 슬라이드 제목
CAPE-KG: 한국어 수주/제안 업무 문서 기반 Evidence-Grounded Procedural KG 구축

### 핵심 메시지
한국어 장문 업무 문서에서 원문 근거에 연결된 절차형 지식그래프를 구축하고, 이를 표준 taxonomy 및 LLM 평가 과제로 확장하는 연구입니다.

### 슬라이드 본문
- 연구 대상: 한국어 수주/제안 업무 OCR 문서
- 연구 방법론: CAPE-KG
- 주요 산출물:
  - Layer 1 NCS/PCF 표준 KG
  - Layer 2 수주/제안 업무 절차 KG
  - Layer 2와 NCS/PCF 간 mapping candidate
  - KG viewer, GraphML, Neo4j import package
  - Qwen3-8B/14B/32B-AWQ 기반 baseline, ablation, model-scaling 실행 결과
  - human-gold annotation/adjudication, mapping expert review, active-review human-effort handoff package

### 발표자 설명
첫 슬라이드에서 "KG 구축과 실험 인프라는 준비되었지만, 논문 성능 주장은 human-gold 검수 이후로 분리하고 있다"고 명확히 말합니다.

---

## Slide 2. 현재 상태 한 장 요약

### 슬라이드 제목
구축은 완료, 최종 성능 주장은 보류

### 핵심 메시지
자동 구축과 실험 인프라는 실행 완료 상태지만, 논문에서 주장 가능한 최종 성능은 사람 검수 이후에만 확정할 수 있습니다.

### 슬라이드 본문
| 구분 | 현재 상태 | 발표 시 표현 |
| --- | --- | --- |
| Layer 1 KG | 완료 | NCS/PCF 표준 기준축 구축 완료 |
| Layer 2 KG | 완료 | 수주/제안 업무 절차 KG 구축 완료 |
| NCS/PCF mapping | 후보 생성 완료 | expert review 전이므로 성능 주장은 보류 |
| LLM baseline/ablation | 실행 완료 | 14개 조건 120-row 실행 커버리지 확보 |
| Model scaling | 실행 완료 | Qwen3-8B/14B/32B-AWQ 진단 결과 확보 |
| Active review | 템플릿 준비 | human-effort 측정 시트와 평가기 준비 |
| Human review handoff | 준비 완료 | annotator, coordinator, adjudicator, mapping expert, crosswalk expert, active effort bundle 생성 |
| Required return files | 14개 대기 | annotation 10개, adjudication 1개, mapping 1개, crosswalk 1개, active effort 1개 |
| Pre-human validation | PASS | current check count: see `../06_release/pre_human_handoff_validation.md` |
| Final paper claim | 보류 | human-gold, IAA, adjudication 필요 |

### 발표자 설명
이 슬라이드는 발표 전체의 기준입니다. "무엇이 끝났고, 무엇은 아직 주장하면 안 되는지"를 먼저 구분합니다.

---

## Slide 3. 왜 연구 방향을 수정했는가?

### 슬라이드 제목
도메인 KG 구축 사례에서 NLP 평가 가능한 연구로 전환

### 핵심 메시지
단순히 업무 온톨로지를 구축했다고 말하면 논문 contribution이 약할 수 있어, 평가 가능한 information extraction task로 재정의했습니다.

### 슬라이드 본문
| 기존 표현 | 수정된 표현 |
| --- | --- |
| 수주/제안 업무 온톨로지 구축 | evidence-grounded procedural KG construction |
| Layer 1/Layer 2 구축 사례 | 장문 업무 문서에서 node/edge/evidence 추출 |
| NCS/PCF 연결 | standard taxonomy bridge |
| 내부 검수 중심 | human-gold, IAA, ablation, public benchmark 평가 |
| 시스템 산출물 중심 | 논문에서 검증 가능한 task/method/evaluation 중심 |

### 발표자 설명
방법론을 버린 것이 아니라, 논문 venue에 맞게 framing을 바꾼 것입니다. 핵심은 "구축한 KG"를 "평가 가능한 추출 과제"로 다시 표현하는 것입니다.

---

## Slide 4. 연구 문제

### 슬라이드 제목
한국어 장문 업무 문서에서 절차형 KG를 어떻게 신뢰성 있게 구축할 것인가?

### 핵심 메시지
본 연구의 문제는 triple을 많이 만드는 것이 아니라, 업무 실행 구조를 원문 근거와 함께 구축하고 검증하는 것입니다.

### 슬라이드 본문
연구 질문:

1. 장문 OCR 업무 문서에서 업무 task, step, input, output, role, decision, risk를 어떻게 구조화할 것인가?
2. 각 node와 edge가 원문 어느 문장에 근거하는지 어떻게 추적할 것인가?
3. LLM output이 schema, predicate, domain/range, evidence 조건을 만족하는지 어떻게 검증할 것인가?
4. 구축된 업무 KG를 NCS/PCF 표준 taxonomy와 어떻게 연결할 것인가?
5. human-gold annotation으로 이 방법을 어떻게 정량 평가할 것인가?

### 발표자 설명
일반 문서 요약이나 entity extraction이 아니라 "업무 실행 지식의 구조화와 검증"이 핵심임을 강조합니다.

---

## Slide 5. 방법론 이름과 핵심 아이디어

### 슬라이드 제목
CAPE-KG: Competency-Question Anchored Procedural Evidence Grounding

### 핵심 메시지
CAPE-KG는 CQ, procedural schema, evidence grounding, validator, standard bridge를 결합한 KG construction framework입니다.

### 슬라이드 본문
| 구성 요소 | 역할 |
| --- | --- |
| Competency Question | KG가 답해야 하는 업무 질문 정의 |
| Procedural Schema | DomainTask, ProcedureStep, Artifact, Role 등 구조화 |
| Evidence Grounding | node/edge를 OCR sentence, page, chunk와 연결 |
| Validator | schema, predicate, evidence, parse quality 검증 |
| Standard Bridge | Layer 2 업무 KG를 NCS/PCF 표준 체계와 연결 |
| Active Review | 검수가 필요한 edge/chunk를 우선순위화 |

### 발표자 설명
LLM이 자유롭게 triple을 생성하는 방식이 아니라, "질문, 구조, 근거, 검증"을 먼저 정하고 LLM을 그 안에 넣는 방식입니다.

---

## Slide 6. 전체 실행 파이프라인

### 슬라이드 제목
실제로 실행한 CAPE-KG 파이프라인

### 핵심 메시지
OCR 문서 정제부터 KG 구축, LLM 실험, Neo4j/HTML 시각화, human-review handoff까지 하나의 재현 가능한 파이프라인으로 실행했습니다.

### 슬라이드 본문
1. OCR workbook 정제 및 evidence anchor 생성
2. NCS/PCF Layer 1 표준 KG 구축
3. 업무 chunk 생성 및 evaluation chunk 120개 선정
4. CQ, schema, prompt, validator 구성
5. Layer 2 task frame 및 procedural KG 구축
6. evidence-supported triple 생성 및 검증
7. Layer 2와 NCS/PCF mapping candidate 생성
8. HTML viewer, GraphML, Neo4j CSV/Cypher 생성
9. Qwen3-8B/14B/32B-AWQ baseline/ablation 실행
10. public benchmark adapter 실행
11. human-gold annotation/adjudication, mapping, active-review handoff 생성
12. claim gate, reproducibility bundle, public-safe bundle 생성

### 발표자 설명
"실험 계획만 있는 상태"가 아니라, 자동 구축 및 실행 산출물은 실제로 생성된 상태임을 보여줍니다.

---

## Slide 7. 입력 데이터와 evidence anchor

### 슬라이드 제목
입력 데이터: 한국어 OCR 업무 문서와 evidence anchor

### 핵심 메시지
KG의 모든 accepted edge가 원문 근거로 돌아갈 수 있도록 OCR sentence를 evidence anchor로 관리했습니다.

### 슬라이드 본문
| 항목 | 값 |
| --- | ---: |
| OCR clean sentence / evidence anchor | 5,009 |
| Layer 2 chunks | 214 |
| Evaluation chunks | 120 |
| Silver reference nodes | 169 |
| Silver reference edges | 861 |
| Silver reference evidence anchors | 293 |

### 발표자 설명
OCR sentence는 단순 텍스트가 아니라 evidence anchor입니다. human-gold annotation에서도 이 anchor를 기준으로 평가합니다.

---

## Slide 8. Layer 1 표준 KG 구축 결과

### 슬라이드 제목
NCS/PCF 표준 기준축 구축

### 핵심 메시지
Layer 1은 도메인 문서에서 추출한 것이 아니라, NCS와 PCF 표준 체계를 안정적인 기준축으로 KG화한 것입니다.

### 슬라이드 본문
| 표준 | Nodes | Edges | 주요 구성 |
| --- | ---: | ---: | --- |
| NCS | 4,109 | 4,085 | 능력단위 중심 표준 구조 |
| PCF | 5,301 | 5,288 | PCFElement 및 PCFMetric 구조 |
| 합계 | 9,410 | 9,373 | Layer 1 standard grounding layer |

품질 점검:

- endpoint missing count: 0
- duplicate node ID count: 0
- PCF metric orphan count: 0
- Layer 1 gate: PASS

### 발표자 설명
Layer 1은 "표준 사전" 역할입니다. Layer 2와 직접 병합하지 않고 mapping candidate를 통해 연결합니다.

---

## Slide 9. Layer 2 업무 KG 구축 결과

### 슬라이드 제목
수주/제안 업무 절차 KG 구축 완료

### 핵심 메시지
한국어 수주/제안 문서에서 179개 node와 906개 edge의 Layer 2 procedural KG를 구축했습니다.

### 슬라이드 본문
| 항목 | 값 |
| --- | ---: |
| Layer 2 nodes | 179 |
| Layer 2 edges | 906 |
| Evidence anchors | 5,009 |
| Dangling edges | 0 |
| Evidence-missing accepted edges | 0 |
| Type violations | 0 |

### 발표자 설명
중요한 점은 규모뿐 아니라 evidence-missing accepted edge가 0이라는 점입니다. accepted edge는 원문 근거와 연결되어 있습니다.

---

## Slide 10. Layer 2 node schema

### 슬라이드 제목
업무 절차를 표현하는 node type 구성

### 핵심 메시지
Layer 2는 단순 entity KG가 아니라 업무, 단계, 산출물, 역할, 조건, 리스크를 함께 표현하는 procedural KG입니다.

### 슬라이드 본문
| Node type | Count |
| --- | ---: |
| ProcedureStep | 99 |
| DomainTask | 22 |
| Artifact | 14 |
| GuardCondition | 13 |
| Role | 10 |
| ArtifactFlow | 9 |
| Principle | 5 |
| DecisionGateway | 4 |
| Risk | 3 |

### 발표자 설명
ProcedureStep과 DomainTask가 중심이기 때문에, 업무 수행 흐름을 설명할 수 있는 구조입니다.

---

## Slide 11. Layer 2 edge schema

### 슬라이드 제목
업무 흐름을 구성하는 관계 type

### 핵심 메시지
Layer 2 edge는 산출물, 입력, 수행 주체, 선후행 관계, decision/risk 조건을 표현합니다.

### 슬라이드 본문
| Edge type | Count |
| --- | ---: |
| PRODUCES | 220 |
| USES_INPUT | 201 |
| PERFORMED_BY | 120 |
| HAS_STEP | 99 |
| PRECEDES | 77 |
| HAS_PRINCIPLE | 64 |
| HAS_DECISION_GATEWAY | 54 |
| HAS_RISK | 39 |
| HAS_GUARD_CONDITION | 14 |
| FEEDS_INTO / USED_AS_INPUT_FOR | 18 |

### 발표자 설명
이 구조 덕분에 "업무가 무엇을 만들고, 무엇을 입력으로 쓰고, 어떤 순서로 진행되는가"를 KG에서 질의할 수 있습니다.

---

## Slide 12. NCS/PCF mapping 결과

### 슬라이드 제목
Layer 2 업무 KG와 표준 taxonomy 연결 후보 생성

### 핵심 메시지
Layer 2 task를 NCS/PCF 표준 체계와 연결하는 mapping candidate는 생성되었지만, downstream 성능 주장은 expert review 이후에만 가능합니다.

### 슬라이드 본문
| 항목 | 값 |
| --- | ---: |
| NCS mapping candidates | 110 |
| PCF mapping candidates | 110 |
| Total mapping review rows | 220 |
| Pending source groups | 44 |
| Completed expert-review groups | 0 |
| Current claim status | pending expert review |

### 발표자 설명
이 단계는 "후보 생성 완료"까지는 말할 수 있습니다. 하지만 Hit@K, P@5, MRR 같은 mapping 성능은 expert review가 완료되어야 말할 수 있습니다.

---

## Slide 13. LLM은 어디에 사용했는가?

### 슬라이드 제목
LLM은 KG 구축 방법론 평가와 비교 실험에 사용

### 핵심 메시지
현재 실험에서는 Qwen3 계열 모델을 사용해 baseline, ablation, model scaling을 실행했습니다.

### 슬라이드 본문
사용한 LLM:

- Qwen3-8B
- Qwen3-14B
- Qwen3-32B-AWQ

사용 목적:

- plain LLM baseline
- predicate-constrained baseline
- current project baseline
- CAPE-KG proposed condition
- CAPE-KG ablation
- EDC-style / Taxonomy-RAG / SAC-KG-style 비교 조건
- model scaling diagnostic

### 발표자 설명
LLM이 필요 없었던 것이 아니라, KG 구축의 일부와 실험 비교 조건에 사용했습니다. 다만 현재 LLM 성능 수치는 human-gold가 아니라 silver/proxy 기준입니다.

---

## Slide 14. LLM 실행 커버리지

### 슬라이드 제목
14개 조건 120-row 실행 커버리지 확보

### 핵심 메시지
최소 제출 요건에서 요구한 baseline, proposed, ablation 실행 커버리지는 확보했습니다.

### 슬라이드 본문
| 구분 | 조건 | 상태 |
| --- | --- | --- |
| Baseline | B0 plain LLM | 120 rows |
| Baseline | B1 predicate constrained | 120 rows |
| Baseline | B2 current project | 120 rows |
| Proposed | P_cape_kg_actual | 120 rows |
| Ablation | P_minus_CQ | 120 rows |
| Ablation | P_minus_Evidence | 120 rows |
| Ablation | P_minus_Procedural_schema | 120 rows |
| Ablation | P_minus_Standard_bridge | 120 rows |
| Ablation | P_minus_Validator | 120 rows |
| Ablation | P_minus_Schema_retrieval | 120 rows |
| Additional baselines | B3/B4/B5/B6 | 각 120 rows |

### 발표자 설명
실행 커버리지는 강점입니다. 하지만 이 표는 "생성 완료"를 보여주는 표이지, 최종 성능 우위를 말하는 표가 아닙니다.

---

## Slide 15. 현재 LLM diagnostic 결과 해석

### 슬라이드 제목
Silver/proxy diagnostic은 참고용이며 최종 성능 주장은 아님

### 핵심 메시지
P_cape_kg_actual의 silver/proxy 결과는 존재하지만, human-gold가 아니므로 논문 main result로 사용하지 않습니다.

### 슬라이드 본문
| Model | Condition | Rows | Edge F1 | Predicate F1 | Node F1 | Evidence F1 |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Qwen3-8B | P_cape_kg_actual | 120 | 0.0018 | 0.0482 | 0.0326 | 0.0655 |
| Qwen3-14B | P_cape_kg_actual | 120 | 0.0017 | 0.0601 | 0.0298 | 0.0610 |
| Qwen3-32B-AWQ | P_cape_kg_actual | 120 | 0.0034 | 0.0662 | 0.0284 | 0.0542 |

주의:

- 위 수치는 silver/proxy reference 기준입니다.
- strict JSON warning gate는 2400-token strict/no-think 재실행 후 PASS 상태입니다.
- strict JSON 진단은 현재 claim gate가 선택한 full run 기준과 과거 디버깅 run을 분리해 보고합니다.
- 현재 선택된 strict JSON run의 parse/generation error rows는 661건이고, 모두 보수적 partial-JSON repair로 회수되어 unrepaired error는 0건입니다.
- 그래도 이 수치는 human-gold가 아니므로 최종 성능 주장에는 사용할 수 없습니다.
- 최종 논문 성능 table은 human-gold scoring 이후에 작성해야 합니다.

### 발표자 설명
수치가 낮아 보이는 이유를 방어적으로 설명하기보다, "이 수치는 최종 성능 수치가 아니다"라고 선을 긋는 것이 중요합니다.

---

## Slide 16. Public benchmark adapter

### 슬라이드 제목
외부 public benchmark와의 연결 실험

### 핵심 메시지
PAGED/Text2KG subset adapter를 통해 외부 benchmark 연결 가능성을 확인했습니다.

### 슬라이드 본문
| Run | PAGED items | PAGED edge F1 | Text2KG items | Text2KG relation F1 |
| --- | ---: | ---: | ---: | ---: |
| Qwen3-8B full adapter | 100 | 0.4233 | 200 | 0.6015 |
| Qwen3-14B subset | 10 | 0.1446 | 20 | 0.2817 |
| Qwen3-8B subset | 10 | 0.1794 | 20 | 0.4500 |

### 발표자 설명
이 결과는 한국어 수주/제안 문서 main result를 대체하지 않습니다. 다만 "외부 benchmark와 연결 가능한 평가 프레임이 있다"는 보조 근거로 사용할 수 있습니다.

---

## Slide 17. Active review 수정 방향

### 슬라이드 제목
Active review는 이제 human-effort 실험으로 정리

### 핵심 메시지
기존 active-review diagnostic은 silver/proxy였고, 최신 방향에서는 실제 reviewer effort를 측정할 수 있는 handoff package까지 준비했습니다.

### 슬라이드 본문
| 항목 | 값 |
| --- | ---: |
| Condition | P_cape_kg_actual |
| Candidate review queue | 275 |
| Human-effort pooled rows | 204 |
| Active-priority arm | 100 rows |
| Uncertainty-only arm | 100 rows |
| Random-control arm | 100 rows |
| Reviewed timing file | not returned yet |
| Current claim status | ready_for_human_effort_collection |

### 발표자 설명
여기서 말할 수 있는 것은 "active review 효율을 주장했다"가 아니라 "효율을 검증하기 위한 reviewer timing sheet와 평가기를 준비했다"입니다.

---

## Slide 18. Human review handoff

### 슬라이드 제목
논문 성능 주장을 위한 human review package 준비

### 핵심 메시지
100 chunk 최소 gate를 목표로 annotation, adjudication, mapping expert review, active-review effort까지 분리한 handoff package를 만들었습니다.

### 슬라이드 본문
| 항목 | 값 |
| --- | ---: |
| Priority batches | 5 |
| Assigned chunks | 100 |
| Candidate edges in handoff | 1,371 |
| Annotator bundles | A/B 각각 생성 |
| Coordinator bundle | 생성 |
| Adjudicator bundle | 생성 |
| Mapping expert bundle | 생성 |
| Active-review effort bundle | 생성 |
| Handoff bundles total | 6 |
| Required return files | 13 |
| Handoff status | handoff_ready_pending_human_review |

### 발표자 설명
사람 검수는 아직 완료되지 않았습니다. 하지만 annotator에게 넘길 파일, adjudicator가 수정해야 할 adjudication draft, mapping expert review 파일, active-review timing sheet, import script, IAA/adjudication/scoring refresh script는 준비되어 있습니다.

---

## Slide 19. Required return files

### 슬라이드 제목
남은 사람 검수 파일은 14개로 명확히 정의됨

### 핵심 메시지
이제 "무엇을 사람이 검수해서 돌려줘야 하는지"가 파일 단위로 고정되어 있습니다.

### 슬라이드 본문
| Return type | 파일 수 | 현재 상태 | 완료 후 역할 |
| --- | ---: | --- | --- |
| Human-gold annotation | 10 | missing reviewed file | A/B annotator label 수집 |
| Human-gold adjudication | 1 | missing reviewed file | 최종 gold label 확정 |
| Mapping expert review | 1 | missing reviewed file | NCS/PCF mapping 성능 평가 |
| Active-review human effort | 1 | missing reviewed file | 검수 시간/수정량 기반 효율 평가 |
| 합계 | 13 | pending human returns | final paper claim gate 해제 |

현재 return preflight:

- overall_status: pending_human_returns
- validation errors: 0
- annotator reviewed files present: 0/10
- adjudication reviewed file present: false
- mapping reviewed rows: 0
- active-review effort reviewed file present: false

### 발표자 설명
이 슬라이드는 교수님께 다음 실행 단계를 아주 구체적으로 보여줍니다. 현재 문제는 자동 파이프라인이 빠진 것이 아니라, 사람이 반환해야 할 14개 파일이 아직 비어 있다는 것입니다.

---

## Slide 20. 현재 main table의 성격

### 슬라이드 제목
현재 main table은 final performance table이 아니라 claimability table

### 핵심 메시지
현재 table은 어떤 결과가 주장 가능한지, 어떤 결과가 pending인지 구분하기 위한 표입니다.

### 슬라이드 본문
| Result | Claimability | Current value | Blocker |
| --- | --- | --- | --- |
| Core extraction main result | pending_human | not claimable yet | 0/100 adjudicated chunks |
| Actual LLM run coverage | claimable_setup | B0/B1/B2/P=120 rows; 6 ablations | quality claim은 human-gold 필요 |
| CAPE-KG silver diagnostic | diagnostic_only | silver/proxy metrics exist | human-gold 아님 |
| Public benchmark adapter | auxiliary_claimable | PAGED/Text2KG subset metrics | main result 대체 불가 |
| NCS/PCF mapping downstream | pending_expert_review | pending_rows=220 | expert review 필요 |
| Release package | claimable_setup | PASS | source text 제외 public-safe |
| Submission claim gate | not_ready | FAIL | required failures=4 |

### 발표자 설명
교수님께 "아직 main table이 없다"가 아니라 "현재는 claimability main table이 있고, final performance main table은 human-gold 이후 생성한다"고 설명합니다.

---

## Slide 21. Conservative claim gate

### 슬라이드 제목
현재 claim gate가 FAIL인 이유

### 핵심 메시지
FAIL은 실험 실패가 아니라, 아직 사람 검수 기반 최종 논문 주장을 하지 말라는 보수적 안전장치입니다.

### 슬라이드 본문
현재 claim gate:

- Overall status: FAIL
- Required failures: 4
- Optional failures: 1
- Warnings: 0

자동 실행 측면에서 개선된 항목:

- llm.strict_json_rate: PASS
- B2/B4/B5 top warning conditions를 2400-token strict/no-think 설정으로 재실행
- Strict JSON diagnostics는 현재 선택 run 기준과 historical debugging run 기준을 분리
- 선택된 full 120-row run의 parse/generation error rows:
  - B2_current_project: 18/120
  - B4_taxonomy_rag: 35/120
  - B5_procedural_prompt: 39/120

Blocking required gates:

1. gold.completed_chunks: adjudicated human-gold chunks 100개 필요
2. gold.item_count: human-gold node/edge/evidence item 500개 필요
3. gold.iaa: 2인 annotator agreement 필요
4. llm.proposed_human_gold_score: P_cape_kg_actual human-gold scoring 필요

Optional blocking gate:

- mapping.expert_review: NCS/PCF expert review 완료 필요

### 발표자 설명
이 슬라이드는 연구의 약점이 아니라 엄격성을 보여주는 장치입니다. 현재 가능한 주장과 불가능한 주장을 자동 gate로 분리했습니다.

---

## Slide 22. KG 시각화 및 Neo4j

### 슬라이드 제목
KG를 직접 탐색할 수 있는 시각화 산출물

### 핵심 메시지
구축된 KG는 HTML viewer와 Neo4j import package로 확인할 수 있습니다.

### 슬라이드 본문
| 산출물 | 상태 |
| --- | --- |
| HTML KG viewer | 생성 완료 |
| Neo4j flat import CSV | 생성 완료 |
| Neo4j Cypher | 생성 완료 |
| CSV validation | PASS |
| CSV files | 17 |
| Validated import rows | 20,088 |
| Neo4j nodes by CSV parser | 9,589 |
| Neo4j relationships | 10,499 |

### 발표자 설명
시각화는 논문 성능 claim과 별개로, 구축 결과를 교수님께 직접 보여줄 수 있는 demo evidence입니다.

---

## Slide 23. Reproducibility package

### 슬라이드 제목
재현성과 공개 가능성을 분리한 release package

### 핵심 메시지
내부 재현 bundle과 public-safe skeleton bundle을 분리해, 원문/내부 검수 자료 노출 위험을 줄였습니다.

### 슬라이드 본문
| 항목 | 값 |
| --- | --- |
| Internal repro bundle | 생성 완료 |
| Public-safe skeleton bundle | 생성 완료 |
| Internal file count | 1,340 |
| Public-safe file count | 215 |
| Public-safe risky paths | 0 |
| Checksum validation | OK |
| Internal SHA256 | c8872391aff46f00fb00ea04575aa7a7b28805305bd093a1c1e6fcc8e9631dc5 |
| Public-safe SHA256 | f3484c55d19b91ec70d5b91aaa54ad2350f05b63f90af9fca2fe354788659f59 |

### 발표자 설명
논문 제출 시 public release는 source text와 내부 검수 파일을 제외한 형태로 공개하고, 내부 재현 package는 별도로 유지하는 방향입니다.

---

## Slide 24. 현재까지 주장 가능한 것과 아닌 것

### 슬라이드 제목
발표에서 안전하게 말할 수 있는 주장 범위

### 핵심 메시지
구축, 실행, 인프라 준비는 주장 가능하지만, 성능 우위는 아직 주장하지 않습니다.

### 슬라이드 본문
말할 수 있는 것:

- NCS/PCF Layer 1 KG 구축 완료
- 수주/제안 업무 Layer 2 KG 구축 완료
- node/edge/evidence 기반 procedural schema 구현
- 14개 LLM 조건 실행 커버리지 확보
- Qwen3-8B/14B/32B-AWQ model-scaling diagnostic 확보
- public benchmark adapter 실행
- Neo4j/HTML viewer/release bundle 준비
- human-gold annotation/adjudication, mapping, active-review handoff 준비
- pre-human handoff validation PASS

아직 말하면 안 되는 것:

- CAPE-KG가 baseline보다 최종적으로 우수하다
- P_cape_kg_actual의 human-gold F1이 얼마다
- NCS/PCF mapping Hit@K/P@5/MRR이 얼마다
- active review가 실제 사람 검수 시간을 얼마나 줄였다

### 발표자 설명
이 슬라이드는 교수님과 연구 방향을 조율할 때 가장 중요합니다. 논문 claim을 섣불리 만들지 않는다는 점을 분명히 합니다.

---

## Slide 25. 남은 실험 계획

### 슬라이드 제목
다음 단계: human-gold와 expert review로 final table 완성

### 핵심 메시지
이제 남은 핵심은 자동 실행이 아니라 사람 검수 기반 gold evidence를 채우는 것입니다.

### 슬라이드 본문
우선순위:

1. Annotator A/B가 100 chunk priority batch 검수
2. IAA 계산
3. Adjudicator가 `adjudication_edited.jsonl` 반환
4. Adjudication으로 final human-gold 생성
5. P_cape_kg_actual 및 baseline을 human-gold로 scoring
6. NCS/PCF Top-5 mapping expert review
7. Active-review human-effort reviewed CSV 수집
8. Final performance main table 생성
9. EACL paper draft에서 claim wording 업데이트

### 발표자 설명
교수님께는 "현재는 pre-human handoff ready 상태이고, 이제 실제 사람 검수만 들어가면 final table로 전환할 수 있다"고 설명합니다.

---

## Slide 26. 예상 contribution 정리

### 슬라이드 제목
논문 contribution으로 정리할 수 있는 항목

### 핵심 메시지
최종 논문은 업무 KG 구축 자체보다, evidence-grounded procedural KG construction task와 평가 체계가 contribution이 되어야 합니다.

### 슬라이드 본문
예상 contribution:

1. 한국어 수주/제안 문서 기반 evidence-grounded procedural KG construction task 정의
2. CQ-anchored schema, evidence grounding, validator, standard bridge를 결합한 CAPE-KG 방법론
3. NCS/PCF 표준 체계와 업무 KG를 연결하는 taxonomy bridge
4. baseline, ablation, model scaling, public benchmark adapter를 포함한 평가 프레임
5. human-gold annotation, IAA, adjudication, active-review effort까지 포함한 검증 프로토콜

### 발표자 설명
"온톨로지 만들었습니다"가 아니라 "장문 업무 문서에서 근거 기반 procedural KG를 만드는 task와 방법론을 제안한다"로 정리해야 합니다.

---

## Slide 27. 교수님께 논의드릴 의사결정

### 슬라이드 제목
교수님께 확인받고 싶은 결정 사항

### 핵심 메시지
현재 자동 실험은 충분히 정리되었으므로, 다음 결정은 annotation 범위와 논문 claim 범위입니다.

### 슬라이드 본문
논의 요청:

1. 최소 100 chunk human-gold로 EACL submission을 목표로 할지
2. 300-500 chunk까지 확장해 strong full-paper claim을 노릴지
3. NCS/PCF expert review를 어느 범위까지 진행할지
4. Active-review human-effort 실험을 논문 본문에 넣을지 appendix로 둘지
5. Qwen3-32B-AWQ 결과를 model-scaling diagnostic으로만 둘지 추가 모델을 더 돌릴지
6. public benchmark adapter를 auxiliary evaluation으로 얼마나 강조할지

### 발표자 설명
마지막은 "제가 다음에 무엇을 실행하면 되는지"를 교수님께서 결정하기 쉽게 만든 슬라이드입니다.

---

## Slide 28. 발표 마무리 문장

### 슬라이드 제목
정리: 자동 구축은 완료, 논문 주장은 human-gold 이후 확정

### 핵심 메시지
현재 연구는 KG 구축과 실험 인프라를 끝낸 상태이며, 남은 핵심은 사람 검수 기반 evidence를 채워 최종 성능 주장을 claimable하게 만드는 것입니다.

### 슬라이드 본문
한 문장 요약:

> CAPE-KG는 한국어 장문 업무 문서에서 evidence-grounded procedural KG를 구축하는 자동 파이프라인과 평가 인프라를 완성했으며, 현재는 14개 human return file을 통해 human-gold, adjudication, mapping expert review, NCS-PCF crosswalk expert review, active-review effort를 수집하는 단계입니다.

현재 상태:

- Automatic artifacts: ready
- Pre-human handoff: PASS
- Claim gate: FAIL, but expected
- Final performance claim: pending human-gold
- Next execution: annotation/adjudication/expert review return import

### 발표자 설명
마지막에는 "실험이 안 된 것이 아니라, 논문에서 주장 가능한 수준으로 끌어올리기 위해 사람 검수 게이트를 남겨둔 상태"라고 정리합니다.

---

## Appendix A. 주요 파일 경로

| 목적 | 파일 |
| --- | --- |
| 최종 실험 리포트 | `experiments/cape_kg_eacl_20260627/07_reports/final_eacl_experiment_report.md` |
| 현재 claimability table | `experiments/cape_kg_eacl_20260627/06_release/claimable_main_table.md` |
| claim gate | `experiments/cape_kg_eacl_20260627/06_release/claim_gate_report.md` |
| pre-human validation | `experiments/cape_kg_eacl_20260627/06_release/pre_human_handoff_validation.md` |
| active-review human-effort plan | `experiments/cape_kg_eacl_20260627/06_release/active_review_human_effort_plan.md` |
| human review handoff | `experiments/cape_kg_eacl_20260627/06_release/human_review_handoff/` |
| human gate action plan | `experiments/cape_kg_eacl_20260627/06_release/human_gate_action_plan.md` |
| required return files | `experiments/cape_kg_eacl_20260627/05_review/human_gate_required_returns.csv` |
| adjudicator README | `experiments/cape_kg_eacl_20260627/06_release/human_review_handoff/README_adjudicator_ko.md` |
| Layer 2 nodes | `outputs/07_layer2_graph/layer2_nodes.jsonl` |
| Layer 2 edges | `outputs/07_layer2_graph/layer2_edges.jsonl` |
| KG viewer | `outputs/09_visualization/kg_viewer.html` |
| Neo4j flat import | `outputs/11_neo4j_import_flat/` |
| release bundle manifest | `experiments/cape_kg_eacl_20260627/06_release/release_bundle_manifest.json` |

---

## Appendix B. 발표 시 피해야 할 표현

| 피해야 할 표현 | 대체 표현 |
| --- | --- |
| 성능이 baseline보다 좋다 | 현재는 human-gold 전 silver/proxy diagnostic이다 |
| main table이 완성됐다 | claimability table은 있고 final performance table은 pending이다 |
| mapping 평가가 끝났다 | mapping candidate 생성은 끝났고 expert review가 필요하다 |
| active review가 효율적이다 | active-review human-effort 평가 템플릿이 준비됐다 |
| Qwen3-32B 결과가 최종 성능이다 | Qwen3-32B-AWQ model-scaling diagnostic이다 |
