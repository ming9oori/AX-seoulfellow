# 교수님 발표용 슬라이드 원고: CAPE-KG 수정 방향 반영본

Generated: 2026-06-28

> 최신 수정 방향과 active-review human-effort handoff를 반영해 다시 작성한 발표자료 원고는 `experiments/cape_kg_eacl_20260627/07_reports/professor_presentation_updated_direction_ko.md`입니다. 이 파일은 이전 초안으로 유지합니다.

이 문서는 교수님께 현재 연구 진행 상황을 발표하기 위한 PPT 슬라이드별 내용 초안입니다. 실제 PPT 파일이 아니라, 각 슬라이드에 들어갈 제목, 핵심 메시지, 본문, 발표자 설명을 바로 옮길 수 있도록 구성했습니다.

발표의 기본 톤은 다음과 같습니다.

- **KG 구축은 완료되었다고 말할 수 있습니다.**
- **LLM baseline/ablation/model scaling은 실행되었다고 말할 수 있습니다.**
- **그러나 성능이 최종적으로 우수하다는 주장은 아직 하지 않습니다.**
- **현재 main table은 final performance table이 아니라 claimability table입니다.**
- **다음 의사결정은 human annotation과 mapping expert review 진행입니다.**

---

## Slide 1. 제목

### 슬라이드 제목
한국어 수주/제안 업무 문서 기반 Evidence-Grounded Procedural KG 구축

### 핵심 메시지
실제 업무 문서에서 근거 문장에 연결된 절차 중심 지식그래프를 구축하고, NCS/PCF 표준 체계 및 LLM 비교 실험까지 연결했습니다.

### 슬라이드 본문
- 연구 대상: 한국어 수주/제안 업무 OCR 문서
- 방법론: CAPE-KG
- 현재 완료:
  - NCS/PCF Layer 1 KG 구축
  - 수주/제안 업무 Layer 2 KG 구축
  - NCS/PCF mapping candidate 생성
  - KG viewer 및 Neo4j import 산출물 생성
  - Qwen3-8B/14B/32B-AWQ 기반 LLM 실험 실행
- 현재 남은 핵심 작업:
  - human-gold annotation
  - IAA
  - adjudication
  - mapping expert review
  - human-gold 기반 final main table

### 발표자 설명
첫 슬라이드에서 현재 위치를 정확히 잡습니다. “구축과 실험 인프라는 완료되었고, 논문 성능 주장은 human-gold 이후 단계”라고 말합니다.

---

## Slide 2. 연구 배경

### 슬라이드 제목
왜 수주/제안 문서에는 절차 중심 KG가 필요한가?

### 핵심 메시지
수주/제안 문서는 단순 개체 목록보다 업무 흐름, 입력, 산출물, 책임자, 의사결정 조건이 중요합니다.

### 슬라이드 본문
- 일반 LLM 요약만으로는 업무 수행 구조를 검증하기 어렵습니다.
- 필요한 정보:
  - 어떤 업무가 존재하는가?
  - 각 업무는 어떤 입력을 사용하는가?
  - 어떤 산출물을 만드는가?
  - 누가 수행하거나 책임지는가?
  - 어떤 순서와 의사결정 조건이 있는가?
  - 각 지식은 원문 어느 문장에 근거하는가?
- 따라서 본 연구는 evidence-grounded procedural KG를 목표로 합니다.

### 발표자 설명
여기서는 “문서 이해”가 아니라 “업무 실행 지식 구조화”가 연구 문제라고 강조합니다.

---

## Slide 3. 수정된 연구 포지셔닝

### 슬라이드 제목
도메인 KG 구축 사례에서 NLP 연구 문제로 재정의

### 핵심 메시지
현재 연구는 단순한 업무 온톨로지 구축이 아니라, evidence-grounded procedural KG construction task로 재정의되었습니다.

### 슬라이드 본문
| 기존 설명 | 수정된 설명 |
| --- | --- |
| 수주/제안 업무 온톨로지 구축 | 한국어 장문 업무 문서의 절차형 KG 추출 |
| Layer 1/Layer 2 KG 구축 | evidence-grounded procedural KG construction |
| NCS/PCF 연결 | standard taxonomy bridge |
| 내부 검수 중심 | human-gold, IAA, ablation, public benchmark 평가 |

### 발표자 설명
EACL 같은 NLP venue에서는 “도메인 시스템을 만들었다”보다 “일반화 가능한 task, method, evaluation을 제안했다”가 중요합니다. 그래서 연구를 CAPE-KG로 재정의했습니다.

---

## Slide 4. CAPE-KG 방법론

### 슬라이드 제목
CAPE-KG: Competency-Question Anchored Procedural Evidence Grounding

### 핵심 메시지
CAPE-KG는 competency question, procedural schema, evidence grounding, standard mapping을 결합합니다.

### 슬라이드 본문
| 구성 요소 | 역할 |
| --- | --- |
| Competency Question | KG가 답해야 하는 질문 정의 |
| Procedural Schema | Task, Step, Input, Output, Role, Decision 구조화 |
| Evidence Grounding | node/edge를 OCR sentence/page/chunk와 연결 |
| Validator | schema, predicate, evidence, parse quality 점검 |
| Standard Bridge | Layer 2 업무 KG를 NCS/PCF와 연결 |
| Active Review | 검수 우선순위가 높은 chunk/edge 식별 |

### 발표자 설명
핵심은 LLM이 임의로 triple을 만들게 하는 것이 아니라, 어떤 질문에 답하기 위해 어떤 구조와 근거가 필요한지를 먼저 정한 것입니다.

---

## Slide 5. 전체 실행 파이프라인

### 슬라이드 제목
실제로 실행한 KG 구축 및 평가 파이프라인

### 핵심 메시지
원문 OCR부터 표준 KG, 업무 KG, mapping, LLM 비교 실험, human handoff까지 하나의 파이프라인으로 실행했습니다.

### 슬라이드 본문
1. OCR workbook 정제 및 evidence anchor 생성
2. NCS/PCF Layer 1 KG 구축
3. 업무 task frame 생성
4. procedure KG 생성
5. evidence-supported triple 생성
6. Layer 2 graph 구축
7. NCS/PCF mapping candidate 생성
8. HTML/GraphML/Neo4j 시각화 산출물 생성
9. Qwen3-8B/14B/32B-AWQ LLM 비교 실험
10. public benchmark adapter 실행
11. human review package와 claim gate 생성

### 발표자 설명
이 슬라이드에서는 “어떤 것을 실제로 실행했는지”를 시간 순서로 보여줍니다.

---

## Slide 6. 입력 데이터와 OCR 처리

### 슬라이드 제목
입력 데이터: 한국어 OCR 업무 문서

### 핵심 메시지
5,009개 OCR sentence/evidence anchor를 기반으로 KG 구축과 평가 chunk를 만들었습니다.

### 슬라이드 본문
| 항목 | 값 |
| --- | ---: |
| OCR clean sentence/evidence anchors | 5,009 |
| Layer 2 chunks | 214 |
| Evaluation chunks | 120 |
| Silver reference nodes | 169 |
| Silver reference edges | 861 |
| Silver evidence anchors | 293 |

### 발표자 설명
OCR 문장 추적이 가능해야 KG edge가 원문 근거를 가질 수 있습니다. 이 점이 일반 LLM 추출과 다릅니다.

---

## Slide 7. Layer 1 표준 KG

### 슬라이드 제목
NCS/PCF 표준 체계 KG 구축

### 핵심 메시지
업무 KG를 외부 표준 체계에 연결하기 위해 NCS와 PCF를 Layer 1 KG로 구축했습니다.

### 슬라이드 본문
| 표준 | Nodes | Edges | 주요 구성 |
| --- | ---: | ---: | --- |
| NCS | 4,109 | 4,085 | 능력단위 3,450개 |
| PCF | 5,301 | 5,288 | PCFElement 2,017개, PCFMetric 3,284개 |
| 합계 | 9,410 | 9,373 | 표준 grounding layer |

품질 점검:

- endpoint missing count: 0
- duplicate node ID count: 0
- PCF metric orphan count: 0
- Layer 1 gate: PASS

### 발표자 설명
Layer 1은 이후 Layer 2 업무 task를 표준 직무/프로세스 체계와 연결하는 기준점입니다.

---

## Slide 8. Layer 2 업무 KG

### 슬라이드 제목
Layer 2 수주/제안 업무 절차 KG 구축 결과

### 핵심 메시지
한국어 수주/제안 문서에서 179개 node와 906개 edge의 업무 절차 KG를 구축했습니다.

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
가장 중요한 수치는 edge 수보다 evidence-missing edge가 0이라는 점입니다. 즉, accepted edge는 모두 원문 근거를 갖습니다.

---

## Slide 9. Layer 2 node type

### 슬라이드 제목
업무 절차 KG의 node 구성

### 핵심 메시지
Layer 2는 업무, 단계, 산출물, 역할, 조건, 리스크를 함께 표현합니다.

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
이 구조는 단순 개체 KG가 아니라 업무 수행 프로세스를 표현하는 구조입니다.

---

## Slide 10. Layer 2 edge type

### 슬라이드 제목
업무 흐름을 구성하는 관계

### 핵심 메시지
주요 edge는 입력, 산출물, 수행자, 절차 순서, 의사결정 조건을 표현합니다.

### 슬라이드 본문
| Predicate | Count | 의미 |
| --- | ---: | --- |
| PRODUCES | 220 | 산출물 생성 |
| USES_INPUT | 201 | 입력 사용 |
| PERFORMED_BY | 120 | 수행자/책임자 |
| HAS_STEP | 99 | 세부 절차 |
| PRECEDES | 77 | 절차 순서 |
| HAS_PRINCIPLE | 64 | 업무 원칙 |
| HAS_DECISION_GATEWAY | 54 | 의사결정 지점 |
| HAS_RISK | 39 | 리스크 |
| HAS_GUARD_CONDITION | 14 | 판단 조건 |

### 발표자 설명
`PRODUCES`, `USES_INPUT`, `PRECEDES`가 많다는 것은 업무 수행 흐름을 실제로 KG가 담고 있다는 의미입니다.

---

## Slide 11. NCS/PCF mapping candidate

### 슬라이드 제목
Layer 2 업무 KG와 표준 체계 연결

### 핵심 메시지
Layer 2 업무 task를 NCS/PCF 표준 후보에 연결했지만, 확정은 expert review 이후입니다.

### 슬라이드 본문
| 항목 | 값 |
| --- | ---: |
| NCS mapping candidates | 110 |
| PCF mapping candidates | 110 |
| 전체 review rows | 220 |
| NCS source task groups | 22 |
| PCF source task groups | 22 |
| Expert-reviewed rows | 0 |
| Pending rows | 220 |

### 발표자 설명
여기서 중요한 점은 “자동으로 mapping이 맞다고 확정했다”가 아닙니다. 현재는 표준 연결 후보를 만들었고, expert review로 Hit@K, P@5, MRR을 확정해야 합니다.

---

## Slide 12. 시각화와 Neo4j 산출물

### 슬라이드 제목
KG를 실제로 조회하고 검증할 수 있는 산출물

### 핵심 메시지
HTML viewer와 Neo4j import 파일을 생성했고, CSV validation을 통과했습니다.

### 슬라이드 본문
| 항목 | 값 |
| --- | ---: |
| Neo4j import nodes | 9,589 |
| Neo4j import relationships | 10,499 |
| CSV files | 17 |
| CSV total rows | 20,088 |
| Missing endpoint count | 0 |
| CSV validation | PASS |

주요 산출물:

- `outputs/09_visualization/kg_viewer.html`
- `outputs/11_neo4j_import_flat/nodes.csv`
- `outputs/11_neo4j_import_flat/neo4j_import_http_8765.cypher`

### 발표자 설명
KG는 결과 파일로만 존재하는 것이 아니라, viewer와 Neo4j에서 실제로 탐색할 수 있는 상태입니다.

---

## Slide 13. LLM은 어떻게 사용했는가?

### 슬라이드 제목
LLM 사용 범위와 역할

### 핵심 메시지
LLM을 사용했지만, 현재 LLM 결과는 final claim이 아니라 human-gold 전 진단 결과로 다룹니다.

### 슬라이드 본문
| 모델 | 역할 | 현재 상태 |
| --- | --- | --- |
| Qwen3-8B | baseline, ablation, strict JSON diagnostics | full 120 chunk 다수 실행 |
| Qwen3-14B | stronger local diagnostic | B0/B1/B2/P 120 chunk 실행 |
| Qwen3-32B-AWQ | 더 큰 모델의 현실적 core run | B0/B1/B2/P 120 chunk 실행 완료 |
| Llama-2-13B-chat | compatibility smoke | 10 chunk smoke |

### 발표자 설명
LLM은 쓰지 않은 것이 아닙니다. 다만 성능을 주장하려면 LLM output을 human-gold label과 비교해야 하므로, 현재는 진단 결과로 표현합니다.

---

## Slide 14. Qwen3 model scaling 결과

### 슬라이드 제목
Qwen3-8B/14B/32B-AWQ core run

### 핵심 메시지
더 큰 모델까지 실행했으며, 모든 core condition에서 120 chunk 단위 결과를 확보했습니다.

### 슬라이드 본문
| 모델 | 조건 | Rows | 생성 결과 요약 |
| --- | --- | ---: | --- |
| Qwen3-8B | P_cape_kg_actual | 120 | nodes 549, edges 275, mappings 52 |
| Qwen3-14B | P_cape_kg_actual | 120 | nodes 574, edges 332, mappings 10 |
| Qwen3-32B-AWQ | P_cape_kg_actual | 120 | nodes 585, edges 360, mappings 5 |

Core baselines:

- B0_plain_llm: 일반 triple 추출
- B1_predicate_constrained: predicate 제한
- B2_current_project: 기존 프로젝트 방식
- P_cape_kg_actual: CAPE-KG proposed condition

### 발표자 설명
여기서는 “더 큰 모델을 돌렸다”는 실행 커버리지를 말합니다. 아직 “더 큰 모델이 더 좋다”는 결론은 human-gold scoring 전이라 보류합니다.

---

## Slide 15. Silver/proxy 진단 결과

### 슬라이드 제목
현재 LLM 성능표는 final main table이 아님

### 핵심 메시지
현재 silver/proxy 점수는 디버깅과 방향성 확인용이며, 논문 성능 주장으로 사용하지 않습니다.

### 슬라이드 본문
Qwen3-32B-AWQ core silver/proxy diagnostic:

| 조건 | Edge F1 | Predicate F1 | Node F1 | Evidence F1 |
| --- | ---: | ---: | ---: | ---: |
| B0_plain_llm | 0.0000 | 0.0000 | 0.0377 | 0.0273 |
| B1_predicate_constrained | 0.0016 | 0.1161 | 0.0000 | 0.0224 |
| B2_current_project | 0.0000 | 0.0099 | 0.0194 | 0.0387 |
| P_cape_kg_actual | 0.0034 | 0.0662 | 0.0284 | 0.0542 |

주의:

- silver/proxy reference 기준입니다.
- human-gold label이 아닙니다.
- final paper claim으로 사용하지 않습니다.

### 발표자 설명
이 슬라이드에서는 오히려 엄격함을 보여주는 것이 좋습니다. “낮은 진단 점수 때문에 실패”가 아니라, “현재 reference가 silver라서 성능 주장에 쓰지 않는다”는 점을 설명합니다.

---

## Slide 16. Public benchmark adapter

### 슬라이드 제목
외부 benchmark를 통한 보조 일반화 확인

### 핵심 메시지
내부 데이터만의 사례라는 약점을 줄이기 위해 PAGED/Text2KG 계열 public subset 평가도 실행했습니다.

### 슬라이드 본문
| Run | PAGED n | PAGED edge F1 | Text2KG n | Relation F1 | Triple F1 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Qwen3-8B full adapter | 100 | 0.4233 | 200 | 0.6015 | 0.1736 |
| Qwen3-14B subset | 10 | 0.1446 | 20 | 0.2817 | 0.0200 |
| Qwen3-8B subset | 10 | 0.1794 | 20 | 0.4500 | 0.0500 |

### 발표자 설명
이 결과는 내부 수주/제안 KG의 main result가 아니라 auxiliary evidence입니다. 논문에서는 일반화 가능성 보조 자료로 사용할 수 있습니다.

---

## Slide 17. Claimable main table

### 슬라이드 제목
현재 main table의 정확한 의미

### 핵심 메시지
현재 main table은 final performance table이 아니라 claimability table입니다.

### 슬라이드 본문
| 결과 | 현재 상태 | 해석 |
| --- | --- | --- |
| Core extraction main result | pending_human | human-gold F1 미계산 |
| Actual LLM run coverage | claimable_setup | 실행 커버리지는 주장 가능 |
| CAPE-KG silver diagnostic | diagnostic_only | 디버깅/동기 부여용 |
| Public benchmark adapter | auxiliary_claimable | 보조 주장 가능 |
| NCS/PCF mapping downstream | pending_expert_review | expert review 필요 |
| Release/reproducibility package | claimable_setup | 재현 패키지 준비 |
| Submission claim gate | not_ready | required failures 4, warnings 0 |

### 발표자 설명
교수님께 “main table이 나왔냐”는 질문을 받으면, “최종 성능표는 아직 아니고, 현재는 어떤 결과를 주장할 수 있는지 구분하는 claimability table이 나왔습니다”라고 답하면 됩니다.

---

## Slide 18. Human gate 현황

### 슬라이드 제목
논문 성능 주장을 막고 있는 human gate

### 핵심 메시지
자동 산출물은 준비되었지만, 논문 성능 주장은 human-gold annotation과 expert review가 끝나야 가능합니다.

### 슬라이드 본문
| Blocking item | 요구사항 | 현재 |
| --- | --- | --- |
| min.gold_chunks | 100+ adjudicated chunks | 0 |
| min.gold_items | 500+ gold node/edge/evidence items | 0 |
| min.iaa | 100+ paired chunks로 IAA 계산 | 0 |
| min.proposed | P_cape_kg_actual human-gold scoring | 미완료 |
| mapping.expert_review | NCS/PCF mapping expert review | pending rows 220 |

### 발표자 설명
이 슬라이드가 현재 발표에서 가장 중요합니다. “왜 아직 논문 성능표가 없는가?”에 대한 정직한 답입니다.

---

## Slide 19. Human review handoff 준비 상태

### 슬라이드 제목
사람 검수를 바로 시작할 수 있는 산출물

### 핵심 메시지
Annotator와 mapping expert에게 전달할 bundle과 반환 파일 목록이 준비되었습니다.

### 슬라이드 본문
| 항목 | 값 |
| --- | ---: |
| Full annotation package chunks | 120 |
| Priority handoff chunks | 100 |
| Annotation batches | 5 |
| Annotator reviewed files required | 10 |
| Mapping expert reviewed files required | 1 |
| Required return files total | 11 |
| Present reviewed files | 0 |

주요 파일:

- `06_release/human_gate_action_plan.md`
- `05_review/human_gate_required_returns.csv`
- `06_release/human_review_handoff/human_review_handoff_report.md`

### 발표자 설명
이제 남은 것은 추가 자동 개발보다 실제 annotation과 expert review입니다. 반환 파일이 들어오면 import와 scoring pipeline은 준비되어 있습니다.

---

## Slide 20. Pre-human validation 결과

### 슬라이드 제목
검수 전 handoff 인프라 검증

### 핵심 메시지
Human review를 시작하기 위한 파일, bundle, CSV, release artifact 검증은 통과했습니다.

### 슬라이드 본문
| 항목 | 값 |
| --- | --- |
| Overall status | PASS |
| Claim status | pre_human_handoff_ready_not_submission_complete |
| Check count | 20 |
| PASS | 19 |
| WARN | 1 |
| FAIL | 0 |

WARN 의미:

- human gold, IAA, adjudication, human-gold scoring이 아직 없다는 예상 경고
- 자동 산출물 오류가 아니라 final paper claim을 보류해야 한다는 표시

### 발표자 설명
이 슬라이드는 “사람 검수 전 준비 상태는 안정적”이라는 근거입니다. 동시에 아직 submission complete가 아니라는 점도 명확히 합니다.

---

## Slide 21. 재현성과 release package

### 슬라이드 제목
재현 가능한 산출물 패키지

### 핵심 메시지
내부 재현 bundle과 public-safe skeleton bundle을 생성했고 checksum 검증을 통과했습니다.

### 슬라이드 본문
| Bundle | SHA256 |
| --- | --- |
| Internal repro | `250a70c7ddb003cf16adeb7b55ecdca722b38b9024d07c42add96b6ea00d9e3f` |
| Public-safe skeleton | `ec76c3a4d1a20bd7d8539eb980ef23467f92e91717ef9014ec2ae7bf90f270b9` |

검증 결과:

- release bundle checksum: OK
- public-safe tar content scan: PASS
- source text와 internal review handoff 파일은 public-safe bundle에서 제외

### 발표자 설명
논문 제출 관점에서 재현성과 데이터 공개 제약을 분리했습니다. 원문 데이터 공개가 어려워도 schema, prompt, code, derived artifacts 중심의 public-safe package를 준비했습니다.

---

## Slide 22. 현재 결론과 교수님께 논의드릴 사항

### 슬라이드 제목
현재 결론 및 다음 의사결정

### 핵심 메시지
KG 구축과 실험 프레임은 준비되었고, 다음 단계는 human-gold 검수와 expert review입니다.

### 슬라이드 본문
현재 결론:

- Layer 1 NCS/PCF KG 구축 완료
- Layer 2 업무 절차 KG 구축 완료
- NCS/PCF mapping candidate 생성 완료
- LLM baseline/ablation/model scaling 실행 완료
- public benchmark adapter 실행 완료
- human review handoff 준비 완료
- final performance claim은 human-gold 이후로 보류

교수님께 논의드릴 사항:

- 100 chunk human-gold annotation을 우선 진행할지
- annotator 2인을 어떻게 배정할지
- mapping expert review를 누가 수행할지
- EACL short paper 전략으로 갈지, 더 큰 gold set을 만든 뒤 full paper 전략으로 갈지
- 내부 원문 데이터 공개 제한을 어떻게 논문에 설명할지

### 발표자 설명
마지막 슬라이드에서는 “무엇을 해달라”가 분명해야 합니다. 자동 실험은 준비되었고, 이제 연구 주장의 신뢰도를 결정하는 병목은 사람 검수입니다.

---

## 발표 중 사용할 수 있는 핵심 문장

발표 중 다음 표현을 그대로 사용해도 됩니다.

- “현재 KG 구축은 완료되었지만, 논문 성능 주장은 human-gold 이후로 보류하고 있습니다.”
- “Layer 2 KG의 accepted edge는 모두 evidence anchor를 가지고 있습니다.”
- “Qwen3-8B, 14B, 32B-AWQ까지 실행했지만, 이 결과는 아직 silver/proxy diagnostic입니다.”
- “현재 main table은 final performance table이 아니라 claimability table입니다.”
- “다음 단계는 100 chunk human-gold annotation, IAA, adjudication, mapping expert review입니다.”

피해야 할 표현:

- “CAPE-KG가 baseline보다 우수하다는 것이 입증되었습니다.”
- “최종 main table이 완성되었습니다.”
- “NCS/PCF mapping 정확도가 검증되었습니다.”
- “LLM 실험 결과가 논문 성능 결과입니다.”

---

## 부록. 발표자료에 넣을 파일 경로

| 용도 | 경로 |
| --- | --- |
| 실험 방법론/결과 한국어 보고서 | `experiments/cape_kg_eacl_20260627/07_reports/current_experiment_methodology_and_results_ko.md` |
| 최종 EACL 실험 보고서 | `experiments/cape_kg_eacl_20260627/07_reports/final_eacl_experiment_report.md` |
| Claimable main table | `experiments/cape_kg_eacl_20260627/06_release/claimable_main_table.md` |
| Paper tables | `experiments/cape_kg_eacl_20260627/06_release/paper_tables.md` |
| Human gate action plan | `experiments/cape_kg_eacl_20260627/06_release/human_gate_action_plan.md` |
| Pre-human validation | `experiments/cape_kg_eacl_20260627/06_release/pre_human_handoff_validation.md` |
| KG viewer | `outputs/09_visualization/kg_viewer.html` |
| Neo4j import Cypher | `outputs/11_neo4j_import_flat/neo4j_import_http_8765.cypher` |
