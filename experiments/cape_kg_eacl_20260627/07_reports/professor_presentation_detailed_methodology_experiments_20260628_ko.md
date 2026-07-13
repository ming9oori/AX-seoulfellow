# 교수님 보고용 발표자료 원고: CAPE-KG 방법론, 실행 실험, 현재 결과

Generated: 2026-06-28 13:15 UTC

이 문서는 PPT 파일이 아니라, PPT 슬라이드에 바로 옮길 수 있는 **슬라이드별 발표 원고**입니다. 각 슬라이드는 `슬라이드 제목`, `핵심 메시지`, `슬라이드 본문`, `발표자 설명`으로 구성했습니다.

가장 중요한 보고 기준은 다음입니다.

> **현재 연구는 한국어 수주/제안 업무 문서에서 evidence-grounded procedural KG를 구축하고, NCS/PCF 표준 bridge, LLM baseline/ablation, model scaling, public benchmark adapter, human-review handoff까지 실행한 상태입니다. 다만 최종 성능 우수성 주장은 human-gold annotation, IAA, adjudication, mapping expert review, NCS-PCF crosswalk expert review, active-review effort evidence 이후에만 확정할 수 있습니다.**

따라서 발표에서는 다음 표현을 일관되게 사용합니다.

| 구분 | 발표 표현 |
| --- | --- |
| KG 구축 | 완료 |
| LLM 실행 | baseline/proposed/ablation/model-scaling 실행 완료 |
| 구조 진단 | ontology/procedural/CQ 구조 진단 완료 |
| Main table | final performance table이 아니라 claimability table 존재 |
| 최종 성능 claim | human-gold 이후 확정 |
| 현재 병목 | GPU가 아니라 사람 검수와 expert review |

---

## Slide 1. 제목

### 슬라이드 제목
CAPE-KG: 한국어 수주/제안 업무 문서 기반 Evidence-Grounded Procedural KG 구축

### 핵심 메시지
한국어 장문 업무 문서에서 업무 절차 지식을 추출하고, 각 노드와 엣지를 원문 evidence에 연결하는 지식그래프 구축 방법론입니다.

### 슬라이드 본문
- 연구 대상: 한국어 수주/제안 업무 OCR 문서
- 연구 목표: evidence-grounded procedural knowledge graph construction
- 방법론 이름: CAPE-KG
- 핵심 구성:
  - Competency Question
  - Procedural Schema
  - Evidence Grounding
  - Validator
  - NCS/PCF Standard Bridge
  - Active Review / Human Review Handoff

### 발표자 설명
첫 슬라이드에서는 "온톨로지를 단순히 만든 것"이 아니라, 한국어 장문 업무 문서에서 절차형 지식을 evidence와 함께 KG로 만드는 연구라고 설명합니다.

---

## Slide 2. 한 장 요약

### 슬라이드 제목
자동 구축과 실험 인프라는 완료, 최종 논문 claim은 human-gold 이후 확정

### 핵심 메시지
현재까지 KG 구축, LLM 실행, 구조 진단, public benchmark, human-review handoff는 준비되었지만, 논문 성능표는 아직 human-gold가 없어 확정 전입니다.

### 슬라이드 본문
| 항목 | 현재 상태 | 발표 가능 표현 |
| --- | --- | --- |
| Layer 1 NCS/PCF KG | 완료 | 표준 taxonomy 기준축 구축 완료 |
| Layer 2 업무 KG | 완료 | 수주/제안 업무 procedural KG 구축 완료 |
| Evidence grounding | 완료/진단 | accepted edge는 evidence anchor 보유 |
| NCS/PCF mapping candidate | 완료 | expert review 전 후보 생성 |
| NCS-PCF crosswalk candidate | 완료 | Layer2 bridge 기반 후보 220개 |
| LLM baseline/proposed/ablation | 실행 완료 | 120 chunk 기준 실행 커버리지 확보 |
| Model scaling | 실행 완료 | Qwen3-8B/14B/32B-AWQ 실행 |
| KG structural diagnostics | 완료 | ontology=1.0000, procedural=0.9950, CQ=0.9167 |
| Human review handoff | 준비 완료 | 반환 필요 파일 14개 |
| Claim gate | FAIL | expected fail, human-gold 미완료 때문 |

### 발표자 설명
여기서 FAIL은 실험 실패가 아닙니다. 아직 사람이 검수하지 않은 결과를 논문 성능으로 주장하지 않도록 막는 보수적 게이트입니다.

---

## Slide 3. 연구 방향 수정의 핵심

### 슬라이드 제목
도메인 KG 구축 사례에서 평가 가능한 NLP 연구로 전환

### 핵심 메시지
기존의 "수주/제안 업무 온톨로지 구축"을 "evidence-grounded procedural KG construction task"로 재정의했습니다.

### 슬라이드 본문
| 기존 표현 | 수정된 연구 표현 |
| --- | --- |
| 수주/제안 업무 온톨로지 구축 | evidence-grounded procedural KG construction |
| 내부 데이터 KG 사례 | 한국어 장문 업무 문서 기반 KG extraction task |
| LLM으로 triple 생성 | CQ/schema/evidence/validator로 통제된 추출 |
| 표준 연결 후처리 | NCS/PCF standard bridge |
| 결과물 중심 | 평가, ablation, reproducibility, human-gold 중심 |

### 발표자 설명
방법론을 버린 것이 아니라, 학회 논문에서 평가 가능한 형태로 framing을 바꾼 것입니다. 핵심은 "업무 KG를 만들었다"에서 "근거 기반 절차형 KG 추출 방법론을 제안하고 평가한다"로 바꾼 점입니다.

---

## Slide 4. 연구 문제

### 슬라이드 제목
한국어 장문 업무 문서에서 절차형 업무 지식을 어떻게 신뢰성 있게 KG로 만들 것인가?

### 핵심 메시지
본 연구는 단순 triple extraction이 아니라, 업무 실행 구조와 evidence를 함께 모델링하는 문제입니다.

### 슬라이드 본문
연구 질문:

1. 업무 task, step, input, output, role, decision, risk를 어떻게 구조화할 것인가?
2. 각 node와 edge가 원문 어느 sentence/page/chunk에 근거하는지 어떻게 추적할 것인가?
3. LLM 출력이 schema, predicate, domain/range, evidence 조건을 만족하는지 어떻게 검증할 것인가?
4. 구축된 Layer 2 업무 KG를 NCS/PCF 표준 taxonomy와 어떻게 연결할 것인가?
5. human-gold annotation으로 어떤 결과를 논문 claim으로 확정할 것인가?

### 발표자 설명
일반적인 문서 요약이나 entity extraction이 아니라 "업무가 어떤 순서로 진행되고, 무엇을 입력으로 쓰고, 무엇을 산출하는가"를 구조화하는 것이 핵심입니다.

---

## Slide 5. CAPE-KG 방법론 개요

### 슬라이드 제목
CAPE-KG: CQ, Schema, Evidence, Validator, Standard Bridge의 결합

### 핵심 메시지
CAPE-KG는 LLM이 자유롭게 지식을 생성하게 두지 않고, 질문, 구조, 근거, 검증, 표준 연결을 함께 사용합니다.

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
차별점은 LLM output 자체가 아니라, LLM output을 KG schema와 evidence 조건 안에 넣고 검증 가능한 산출물로 바꾸는 것입니다.

---

## Slide 6. 전체 실행 파이프라인

### 슬라이드 제목
실제로 실행한 CAPE-KG 파이프라인

### 핵심 메시지
OCR 정제부터 KG 구축, LLM 실험, 구조 진단, Neo4j/HTML 시각화, human-review handoff까지 재현 가능한 파이프라인으로 실행했습니다.

### 슬라이드 본문
1. OCR workbook 정제 및 sentence-level evidence anchor 생성
2. NCS/PCF Layer 1 표준 KG 구축
3. Layer 2 업무 chunk 생성 및 120개 evaluation chunk 선정
4. CQ, schema, prompt, validator 구성
5. DomainTask, ProcedureStep, Artifact, Role 등 task frame 구축
6. evidence-supported procedural edge 생성
7. Layer 2 업무 KG와 NCS/PCF mapping candidate 생성
8. Layer 2 bridge 기반 NCS-PCF crosswalk candidate 생성
9. HTML viewer, GraphML, Neo4j CSV/Cypher 생성
10. Qwen3-8B/14B/32B-AWQ baseline, ablation, model-scaling 실행
11. PAGED/Text2KG public benchmark adapter 실행
12. ontology/procedural/CQ structural diagnostics 실행
13. structural gap worklist 생성
14. human-gold annotation/adjudication/mapping/active-effort handoff 생성
15. claim gate, paper table, release bundle, checksum 검증

### 발표자 설명
자동 구축과 실험 실행은 완료되었고, 이제 사람이 검수한 gold label이 들어오면 final paper table로 전환되는 구조입니다.

---

## Slide 7. 입력 데이터와 Evidence Anchor

### 슬라이드 제목
입력 데이터와 evidence grounding

### 핵심 메시지
KG의 accepted edge가 원문 sentence로 돌아갈 수 있도록 OCR sentence를 evidence anchor로 유지했습니다.

### 슬라이드 본문
입력 데이터:

- `handoff-hanyang/자이제_ocr_preprocessed.xlsx`

처리 결과:

| 항목 | 값 |
| --- | ---: |
| OCR clean sentence / evidence anchor | 5,009 |
| Layer 2 chunks | 214 |
| Evaluation chunks | 120 |
| Optional all-available annotation chunks | 214 |
| Optional remaining annotation chunks | 94 |
| Silver reference nodes | 169 |
| Silver reference edges | 861 |
| Silver evidence anchors | 293 |

### 발표자 설명
현재 reference는 KG-derived silver입니다. 최종 성능 주장은 silver가 아니라 adjudicated human-gold로 다시 계산해야 합니다.

---

## Slide 8. Evidence Span Granularity

### 슬라이드 제목
sentence-level evidence에서 component-level span 진단으로 확장

### 핵심 메시지
accepted triple은 sentence evidence anchor를 가지고 있으며, subject/object label이 sentence 안에서 발견되는 경우 character span을 자동 산출했습니다.

### 슬라이드 본문
| 항목 | 값 |
| --- | ---: |
| Layer2 triples | 906 |
| Triple components | 2,718 |
| Exact component spans | 736 |
| Exact component span rate | 0.2708 |
| Subject exact span rate | 0.2395 |
| Object exact span rate | 0.5728 |
| Predicate full-sentence proxy rate | 1.0000 |

해석:

- sentence-level evidence grounding은 이미 KG에 포함되어 있음
- subject/object는 lexical exact match가 가능한 경우 character span을 추가 산출
- predicate는 아직 token-level span이 아니라 sentence-level proxy
- 최종 evidence exactness claim은 human-gold span annotation 이후 가능

### 발표자 설명
이 슬라이드는 evidence grounding을 과장하지 않기 위한 장치입니다. 현재는 "component-level span diagnostic"이며, 모든 항목이 완전한 character-level gold span이라고 말하면 안 됩니다.

---

## Slide 9. Layer 1 표준 KG 구축 결과

### 슬라이드 제목
NCS/PCF 표준 기준축 구축

### 핵심 메시지
Layer 1은 도메인 문서에서 추출한 것이 아니라, NCS와 PCF 표준 체계를 안정적인 기준축으로 KG화한 것입니다.

### 슬라이드 본문
| 표준 | Nodes | Edges | 주요 구성 |
| --- | ---: | ---: | --- |
| NCS | 4,109 | 4,085 | 능력단위 3,450개 포함 |
| PCF | 5,301 | 5,288 | PCFElement 2,017개, PCFMetric 3,284개 포함 |
| 합계 | 9,410 | 9,373 | Layer 1 standard grounding layer |

품질 점검:

- NCS endpoint missing count: 0
- NCS duplicate node ID count: 0
- PCF metric orphan count: 0
- Layer 1 gate: PASS

### 발표자 설명
Layer 1은 표준 taxonomy입니다. Layer 2 업무 KG와 직접 병합하지 않고, mapping candidate와 standard bridge를 통해 연결했습니다.

---

## Slide 10. Layer 2 업무 KG 구축 결과

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
| ArtifactFlow | 9 |
| Principle | 5 |
| DecisionGateway | 4 |
| Risk | 3 |

### 발표자 설명
이 결과는 "업무 절차 KG 구축 완료"로 말할 수 있습니다. 단, LLM이 baseline보다 좋다는 성능 주장은 별개의 human-gold evaluation 문제입니다.

---

## Slide 11. 절차형 Edge 구조

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
| HAS_GUARD_CONDITION | 14 | 판단 조건 |
| FEEDS_INTO / USED_AS_INPUT_FOR | 18 | 산출물 흐름 |

### 발표자 설명
일반 entity-relation KG가 아니라 업무 실행 구조를 담는 predicate를 사용한 것이 방법론적 차이입니다.

---

## Slide 12. KG 구조 진단

### 슬라이드 제목
KG structural diagnostics: 구조적으로 확인 가능한 품질

### 핵심 메시지
현재 KG는 ontology/domain-range/evidence 조건에서는 구조 오류가 없고, procedural consistency와 CQ answerability도 진단했습니다.

### 슬라이드 본문
| 진단 항목 | 값 | 해석 |
| --- | ---: | --- |
| Ontology conformance rate | 1.0000 | unknown type/predicate, dangling edge, domain-range violation 없음 |
| Domain/range violations | 0 | schema상 허용되지 않은 source-target 조합 없음 |
| Evidence-missing accepted edges | 0 | accepted edge는 evidence anchor 보유 |
| Procedural consistency rate | 0.9950 | precedence cycle 없음, gateway branch warning 중심 |
| Precedence cycles | 0 | 절차 순환 오류 없음 |
| Structural CQ answerability | 0.9167 | 12개 CQ 중 11개 구조적으로 answerable |

### 발표자 설명
이 표는 final performance table이 아닙니다. 사람이 만든 gold label과 비교한 성능이 아니라, 구축된 KG 자체의 구조적 진단입니다.

---

## Slide 13. Structural Gap Worklist

### 슬라이드 제목
구조 진단에서 보강할 항목을 human-review worklist로 분리

### 핵심 메시지
KG를 자동으로 수정하지 않고, 사람이 판단해야 할 구조 보강 후보를 별도 worklist로 만들었습니다.

### 슬라이드 본문
| Worklist | 값 | 의미 |
| --- | ---: | --- |
| Review checkpoint candidates | 45 | 리뷰/점검 성격의 task/step을 `ReviewCheckpoint`로 승격할지 검토 |
| Gateway branch gaps | 4 | guard condition은 있으나 explicit branch edge가 없는 decision gateway |
| Human gate effect | 변화 없음 | 현재 required 13 return file 구조는 그대로 유지 |

주요 gateway branch gap:

| Gateway | Guard 수 | Incoming task 수 |
| --- | ---: | ---: |
| `L2_DG_DG_APPROVAL` | 9 | 22 |
| `L2_DG_DG_BID_NO_BID` | 3 | 8 |
| `L2_DG_DG_BID_VALIDATION` | 1 | 17 |
| `L2_DG_DG_PURSUIT` | 1 | 7 |

### 발표자 설명
이 슬라이드의 핵심은 "자동으로 KG를 고쳐 성능을 올렸다"가 아닙니다. 구조 진단 결과를 숨기지 않고, 사람 검수 가능한 보강 후보로 분리했다는 점입니다.

---

## Slide 14. NCS/PCF Mapping Candidate

### 슬라이드 제목
업무 KG와 표준 taxonomy 연결 후보 생성

### 핵심 메시지
Layer 2 업무 task를 NCS/PCF 표준 체계와 연결하는 후보는 생성되었지만, mapping 성능 지표는 expert review 이후에만 주장할 수 있습니다.

### 슬라이드 본문
| 항목 | 값 |
| --- | ---: |
| NCS mapping candidates | 110 |
| PCF mapping candidates | 110 |
| Total mapping review rows | 220 |
| NCS source task groups | 22 |
| PCF source task groups | 22 |
| Completed expert-review groups | 0 |
| Pending rows | 220 |
| Current claim status | pending expert review |

### 발표자 설명
Hit@K, P@5, MRR, nDCG@10, explanation quality 같은 mapping 성능은 아직 말하면 안 됩니다. 현재는 후보 생성과 review scaffold가 준비된 상태입니다.

---

## Slide 15. Layer2-Bridged NCS-PCF Crosswalk

### 슬라이드 제목
Layer 2 업무 task를 매개로 NCS-PCF 연결 후보 생성

### 핵심 메시지
같은 Layer 2 업무 task에 연결된 NCS 후보와 PCF 후보를 이용해 NCS-PCF crosswalk 후보를 만들었습니다.

### 슬라이드 본문
| 항목 | 값 |
| --- | ---: |
| Shared Layer2 tasks | 22 |
| NCS candidate rows | 110 |
| PCF candidate rows | 110 |
| All NCS-PCF candidate pairs | 550 |
| Top crosswalk candidates | 220 |
| Claim status | candidate only, pending expert review |

### 발표자 설명
이 결과는 표준 간 연결을 자동 확정한 것이 아니라, expert가 검토할 수 있는 candidate를 만든 것입니다. 논문에서는 "standard bridge candidate generation"으로 표현해야 합니다.

---

## Slide 16. 시각화와 Neo4j Import

### 슬라이드 제목
KG를 직접 확인할 수 있는 시각화 산출물

### 핵심 메시지
HTML viewer, GraphML/JSON, Neo4j flat CSV/Cypher를 생성했고 CSV validation을 통과했습니다.

### 슬라이드 본문
| 항목 | 값 |
| --- | ---: |
| Neo4j import nodes | 9,589 |
| Neo4j import relationships | 10,499 |
| CSV files | 17 |
| CSV total rows | 20,088 |
| Missing endpoint count | 0 |
| CSV validation status | PASS |

주요 파일:

- `outputs/09_visualization/kg_viewer.html`
- `outputs/11_neo4j_import_flat/nodes.csv`
- `outputs/11_neo4j_import_flat/neo4j_import_http_8765.cypher`
- `outputs/11_neo4j_import_flat/neo4j_csv_validation_report.json`

### 발표자 설명
교수님께 실제 KG를 볼 수 있는 viewer와 Neo4j import 경로가 준비되어 있다고 설명할 수 있습니다.

---

## Slide 17. LLM 사용 범위

### 슬라이드 제목
LLM은 baseline, proposed, ablation, scaling diagnostic에 사용

### 핵심 메시지
LLM은 사용했습니다. 다만 현재 LLM 점수는 human-gold가 아니라 silver/proxy 기준이므로 최종 성능 claim이 아닙니다.

### 슬라이드 본문
사용한 모델:

| 모델 | 사용 목적 | 현재 해석 |
| --- | --- | --- |
| Qwen3-8B | baseline, ablation, strict JSON diagnostics | full 120 chunk 조건 다수 실행 |
| Qwen3-14B | stronger local diagnostic core run | B0/B1/B2/P 120 chunk 실행 |
| Qwen3-32B-AWQ | 더 큰 local open-weight model scaling | B0/B1/B2/P 120 chunk 실행 |
| Llama-2-13B-chat | compatibility smoke run | 10 chunk smoke 성격 |

### 발표자 설명
"LLM이 필요 없었다"가 아니라, KG 구축 방법론 평가와 비교 실험을 위해 사용했습니다. 단, 사람이 검수한 gold와 비교하기 전에는 최종 성능표가 아닙니다.

---

## Slide 18. 실제 LLM 실행 커버리지

### 슬라이드 제목
120개 evaluation chunk 기준 LLM 실행 완료

### 핵심 메시지
baseline, proposed, ablation generation은 claim gate에서 PASS이며, proposed human-gold score만 사람이 아직 없어서 FAIL입니다.

### 슬라이드 본문
| Gate | 상태 | 내용 |
| --- | --- | --- |
| B0/B1/B2 baseline generation | PASS | 각 120 rows |
| P_cape_kg_actual generation | PASS | 120 rows |
| Ablation generation | PASS | 6개 full ablations |
| Output recovery gate | PASS | unrepaired error <= 5% |
| Strict JSON gate | PASS | strict parse/generation error <= 50% |
| Proposed human-gold score | FAIL | adjudicated human-gold 미완료 |

주요 조건:

| 구분 | 조건 |
| --- | --- |
| Baseline | B0_plain_llm, B1_predicate_constrained, B2_current_project |
| 추가 baseline | B3_edc_style, B4_taxonomy_rag, B5_procedural_prompt, B6_sac_kg_verifier_pruner |
| Proposed | P_cape_kg_actual |
| Ablation | P_minus_CQ, P_minus_Evidence, P_minus_Procedural_schema, P_minus_Schema_retrieval, P_minus_Standard_bridge, P_minus_Validator |

### 발표자 설명
생성 자체는 끝났지만, 사람이 확정한 gold label과 비교하지 않았으므로 "성능이 좋다"는 말은 보류합니다.

---

## Slide 19. Actual LLM Silver Diagnostic

### 슬라이드 제목
Silver 기준 진단 결과는 debugging과 sanity check 용도

### 핵심 메시지
현재 LLM 수치는 KG-derived silver reference와 비교한 값이므로 최종 성능표가 아닙니다.

### 슬라이드 본문
| Condition | Edge F1 | Predicate F1 | Node F1 | Evidence F1 | 상태 |
| --- | ---: | ---: | ---: | ---: | --- |
| B0_plain_llm | 0.0000 | 0.0000 | 0.0350 | 0.0239 | silver diagnostic |
| B1_predicate_constrained | 0.0000 | 0.1416 | 0.0000 | 0.0291 | silver diagnostic |
| B2_current_project | 0.0000 | 0.0068 | 0.0215 | 0.0503 | silver diagnostic |
| B6_sac_kg_verifier_pruner | 0.0017 | 0.0774 | 0.0564 | 0.1008 | deterministic approximation |
| P_cape_kg_actual | 0.0018 | 0.0482 | 0.0326 | 0.0655 | silver diagnostic |

### 발표자 설명
이 표는 성능 우수성 주장이 아니라, 어떤 조건이 어떤 유형의 output을 내는지 확인하는 diagnostic입니다.

---

## Slide 20. Model Scaling 결과

### 슬라이드 제목
Qwen3-8B, 14B, 32B-AWQ까지 실행 완료

### 핵심 메시지
현재 서버에서 현실적으로 실행 가능한 local open-weight scaling으로 Qwen3-32B-AWQ까지 실행했습니다.

### 슬라이드 본문
| Model | Condition | Rows | Edge F1 | Predicate F1 | Node F1 | Evidence F1 | 상태 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| Qwen3-8B | P_cape_kg_actual | 120 | 0.0018 | 0.0482 | 0.0326 | 0.0655 | silver diagnostic |
| Qwen3-14B | P_cape_kg_actual | 120 | 0.0017 | 0.0601 | 0.0298 | 0.0610 | silver diagnostic |
| Qwen3-32B-AWQ | P_cape_kg_actual | 120 | 0.0034 | 0.0662 | 0.0284 | 0.0542 | silver diagnostic |

추가 실행 산출:

| Model | B0 rows | B1 rows | B2 rows | P rows |
| --- | ---: | ---: | ---: | ---: |
| Qwen3-8B | 120 | 120 | 120 | 120 |
| Qwen3-14B | 120 | 120 | 120 | 120 |
| Qwen3-32B-AWQ | 120 | 120 | 120 | 120 |

### 발표자 설명
32B-AWQ가 현재 가장 큰 local open-weight diagnostic입니다. 하지만 이 역시 human-gold 전에는 최종 성능 주장이 아닙니다.

---

## Slide 21. Public Benchmark Adapter

### 슬라이드 제목
외부 benchmark는 보조 일반화 근거로 사용

### 핵심 메시지
public benchmark adapter를 통해 내부 한국어 문서 외의 KG extraction benchmark에도 실행 경로를 만들었습니다.

### 슬라이드 본문
| Run | PAGED n | PAGED edge F1 | Text2KG n | Relation F1 | Triple F1 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Qwen3-8B full adapter | 100 | 0.4233 | 200 | 0.6015 | 0.1736 |
| Qwen3-14B subset | 10 | 0.1446 | 20 | 0.2817 | 0.0200 |
| Qwen3-8B subset | 10 | 0.1794 | 20 | 0.4500 | 0.0500 |

### 발표자 설명
이 결과는 auxiliary claim으로 사용할 수 있지만, 논문의 main result는 한국어 수주/제안 데이터의 human-gold 평가가 되어야 합니다.

---

## Slide 22. Active Review Ablation Diagnostic

### 슬라이드 제목
Active review 우선순위화 scaffold 구축

### 핵심 메시지
계획서의 `P - Active review` 항목을 추적하기 위해 active-priority queue와 active review 제거 조건을 비교하는 silver/proxy 진단표를 만들었습니다.

### 슬라이드 본문
| Condition | Strategy | Budget | High-impact errors | Precision@k | Lift | 상태 |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| P_cape_kg_actual_with_active_review | active_priority | 25 | 16 | 0.6400 | 1.0173 | silver diagnostic |
| P_minus_Active_review_random_expected | random_expected | 25 | 15.7273 | 0.6291 | 1.0000 | silver diagnostic |
| P_minus_Active_review_uncertainty_only | uncertainty_only | 25 | 15 | 0.6000 | 0.9538 | silver diagnostic |
| P_cape_kg_actual_with_active_review | active_priority | 55 | 36 | 0.6545 | 1.0405 | silver diagnostic |
| P_minus_Active_review_random_expected | random_expected | 55 | 34.6000 | 0.6291 | 1.0000 | silver diagnostic |

### 발표자 설명
이 표는 active review 효율이 입증되었다는 뜻이 아닙니다. 최종 효율 주장은 human-effort reviewed CSV와 adjudicated label이 들어온 뒤 다시 계산해야 합니다.

---

## Slide 23. Human Review Handoff

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

| 유형 | 파일 수 | 현재 상태 |
| --- | ---: | --- |
| Annotation reviewed JSONL | 10 | pending |
| Adjudication edited JSONL | 1 | pending |
| Mapping expert reviewed JSONL | 1 | pending |
| Active-review effort reviewed CSV | 1 | pending |
| 합계 | 13 | pending |

### 발표자 설명
현재 사람이 검수해서 돌려줘야 할 파일은 14개입니다. 반환되면 import script와 validation script로 전체 리포트를 갱신합니다.

---

## Slide 24. Optional Annotation Expansion

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

### 발표자 설명
교수님께는 "최소 제출 가능 경로는 120개 검수이고, 더 강한 claim을 원하면 214개 전체 검수까지 확장할 수 있다. 300-500 chunk claim은 source 추가 또는 chunk 재분할이 필요하다"라고 설명합니다.

---

## Slide 25. Pre-Human Validation

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
WARN 1개는 human-gold가 아직 없다는 알려진 blocker입니다. 인프라 문제가 아니라, 최종 논문 claim을 보류해야 한다는 표시입니다.

---

## Slide 26. Claim Gate 상태

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
claim gate FAIL은 좋은 안전장치입니다. 아직 검수되지 않은 결과를 논문 주장으로 쓰지 않도록 막고 있기 때문입니다.

---

## Slide 27. 현재 Main Table의 의미

### 슬라이드 제목
현재 table은 final performance table이 아니라 claimability table

### 핵심 메시지
지금 있는 main table은 어떤 결과를 논문 claim으로 쓸 수 있는지 구분하는 보수적 표입니다.

### 슬라이드 본문
| Result | 현재 claimability | 현재 값 |
| --- | --- | --- |
| Core extraction main result | pending_human | human-gold F1 not claimable |
| Actual LLM run coverage | claimable_setup | B0/B1/B2/P=120 rows, 6 ablations |
| Optional annotation expansion | claimable_setup | all_available=214, remaining_optional=94, strong_300_gap=86 |
| CAPE-KG silver diagnostic | diagnostic_only | edge=0.001786, predicate=0.048214, evidence=0.065527 |
| Evidence span granularity | diagnostic_only | subject_exact=0.239514, object_exact=0.572848 |
| KG structural diagnostics | diagnostic_only | ontology=1.0, procedural=0.995043, CQ=0.916667 |
| Structural gap worklist | claimable_setup | review_checkpoint_candidates=45, gateway_branch_gaps=4 |
| Public benchmark adapter | auxiliary_claimable | PAGED 100, Text2KG 200 |
| NCS/PCF mapping downstream | pending_expert_review | pending_rows=220, crosswalk_candidates=220 |
| Release/reproducibility package | claimable_setup | PASS |
| Submission claim gate | not_ready | FAIL |

### 발표자 설명
"현재 main table이 있느냐"라는 질문에는 "있지만 final performance table이 아니라 claimability table"이라고 답해야 합니다.

---

## Slide 28. 현재까지 진행한 실험 목록

### 슬라이드 제목
현재까지 실제로 실행한 실험과 산출물

### 핵심 메시지
KG build, LLM baseline/ablation, model scaling, public benchmark, structural evaluation, human-review handoff, release validation까지 실행했습니다.

### 슬라이드 본문
| 단계 | 실행 내용 | 결과 |
| --- | --- | --- |
| KG build | Layer 1 NCS/PCF, OCR, Layer 2 KG, mapping candidate 생성 | PASS |
| Visualization | HTML viewer, GraphML, JSON, Neo4j CSV 생성 | PASS |
| Neo4j validation | flat CSV parser/endpoint/JSON carrier 점검 | PASS |
| CAPE experiment package | 120 evaluation chunks, silver reference, schema, prompts 생성 | PASS |
| LLM baselines | Qwen3-8B baseline/ablation, Qwen3-14B core, Qwen3-32B-AWQ core | 실행 완료 |
| Public benchmark | PAGED/Text2KG adapter 평가 | 실행 완료 |
| Structural diagnostics | ontology/procedural/CQ 구조 진단 및 structural gap worklist 생성 | 생성 완료 |
| Paper tables | paper table, claimable main table 생성 | 생성 완료 |
| Submission completion audit | 계획서 요구사항별 완료 여부와 다음 명령 정리 | 생성 완료 |
| Claim gate | 제출 주장 가능성 점검 | FAIL, human-gold 미완료 때문 |
| Human handoff | annotator/coordinator/adjudicator/mapping/active-effort bundle 생성 | 준비 완료 |
| Optional annotation expansion | all-available 214, remaining 94 scaffold 생성 | 준비 완료 |
| Pre-human validation | handoff/release/Neo4j/action plan 통합 검증 | PASS; current check count: see `../06_release/pre_human_handoff_validation.md` |

### 발표자 설명
실험이 멈춘 것이 아니라, 자동 실행 가능한 부분은 대부분 끝났고 지금은 human validation 단계로 넘어간 상태입니다.

---

## Slide 29. 주요 산출물 위치

### 슬라이드 제목
교수님께 보여드릴 수 있는 핵심 파일

### 핵심 메시지
KG, 실험표, claim gate, review handoff, release bundle이 모두 파일 단위로 정리되어 있습니다.

### 슬라이드 본문
| 목적 | 파일 |
| --- | --- |
| Layer 2 nodes | `outputs/07_layer2_graph/layer2_nodes.jsonl` |
| Layer 2 edges | `outputs/07_layer2_graph/layer2_edges.jsonl` |
| KG viewer | `outputs/09_visualization/kg_viewer.html` |
| Neo4j flat import | `outputs/11_neo4j_import_flat/` |
| Final build report | `outputs/10_evaluation/final_build_report.md` |
| Paper tables | `experiments/cape_kg_eacl_20260627/06_release/paper_tables.md` |
| Claimable main table | `experiments/cape_kg_eacl_20260627/06_release/claimable_main_table.md` |
| Claim gate report | `experiments/cape_kg_eacl_20260627/06_release/claim_gate_report.md` |
| Structural evaluation report | `experiments/cape_kg_eacl_20260627/04_evaluation/structural_evaluation_report.md` |
| Structural gap worklist | `experiments/cape_kg_eacl_20260627/04_evaluation/structural_gap_worklist_report.md` |
| Human gate action plan | `experiments/cape_kg_eacl_20260627/06_release/human_gate_action_plan.md` |
| Submission completion audit | `experiments/cape_kg_eacl_20260627/06_release/submission_completion_audit_ko.md` |
| 현재 발표 원고 | `experiments/cape_kg_eacl_20260627/07_reports/professor_presentation_detailed_methodology_experiments_20260628_ko.md` |

### 발표자 설명
필요하면 발표 중에는 HTML viewer나 Neo4j import 결과를 보조 화면으로 보여줄 수 있습니다.

---

## Slide 30. 논문 Contribution 후보

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

## Slide 31. 남은 작업

### 슬라이드 제목
다음 단계는 사람 검수 결과를 넣어 final table로 전환하는 것

### 핵심 메시지
자동 실험을 더 많이 돌리는 것보다, 이제는 human-gold와 expert review를 완료하는 것이 핵심입니다.

### 슬라이드 본문
우선순위:

1. Annotator A/B가 priority100 batch 5개씩 검수
2. A/B `.reviewed.jsonl` 10개 반환
3. IAA 계산
4. Adjudicator가 full120 adjudication file 편집
5. Adjudicated human-gold 생성
6. P_cape_kg_actual과 baselines를 human-gold로 scoring
7. NCS/PCF Top-5 mapping expert review
8. Active-review human-effort reviewed CSV 수집
9. Structural gap worklist에서 review checkpoint 후보와 gateway branch gap 검토
10. 선택적으로 remaining 94 chunk 또는 all-available 214 chunk 검수 확장
11. Final performance main table 생성
12. EACL paper draft claim wording 업데이트

### 발표자 설명
교수님께 "다음 병목은 GPU가 아니라 사람 검수"라고 말하면 됩니다. GPU 실험은 32B-AWQ까지 진행했습니다.

---

## Slide 32. 교수님께 논의드릴 의사결정

### 슬라이드 제목
다음 연구 실행 방향 결정 필요

### 핵심 메시지
현재 자동 구축과 실험 실행은 충분히 정리되었으므로, 다음 결정은 annotation 범위와 논문 claim 범위입니다.

### 슬라이드 본문
논의 요청:

1. 최소 100 chunk human-gold로 EACL submission을 목표로 할지
2. 214 chunk 전체 current-corpus 검수까지 확장할지
3. 300-500 chunk까지 확장하려면 source 추가 또는 chunk 재분할을 진행할지
4. NCS/PCF expert review를 priority top20 groups까지만 할지, 전체 44 groups로 확장할지
5. Structural gap worklist의 review checkpoint/gateway branch 검수를 human-gold 단계에 포함할지
6. Active-review human-effort 실험을 본문에 넣을지 appendix로 둘지
7. Qwen3-32B-AWQ 이후 closed API upper-bound baseline을 추가할지
8. public benchmark adapter를 auxiliary evaluation으로 얼마나 강조할지

### 발표자 설명
마지막에는 교수님이 다음 실행 방향을 쉽게 결정할 수 있도록 선택지를 제시합니다.

---

## Slide 33. 발표 시 피해야 할 표현

### 슬라이드 제목
현재 결과를 과장하지 않기 위한 표현 가이드

### 핵심 메시지
현재 결과는 충분히 의미 있지만, human-gold 전에는 final 성능 claim을 하면 안 됩니다.

### 슬라이드 본문
| 피해야 할 표현 | 대체 표현 |
| --- | --- |
| CAPE-KG가 baseline보다 성능이 좋다 | 현재는 silver/proxy diagnostic이며 human-gold 이후 확정한다 |
| main table이 완성됐다 | claimability table은 있고 final performance table은 pending이다 |
| mapping 평가가 끝났다 | mapping candidate와 diagnostic scaffold는 있고 expert review가 필요하다 |
| active review가 효율적이다 | active-review effort 템플릿과 silver diagnostic은 준비됐다 |
| Qwen3-32B-AWQ 결과가 최종 성능이다 | Qwen3-32B-AWQ는 가장 큰 local diagnostic run이다 |
| claim gate FAIL이 실험 실패다 | human-gold 미완료를 감지한 expected conservative gate다 |
| 구조 gap을 자동으로 수정했다 | 구조 gap을 human-review worklist로 분리했고 KG는 임의 수정하지 않았다 |

### 발표자 설명
교수님께 보고할 때도, 나중에 논문에 쓸 때도 claim scope를 명확히 분리하는 것이 중요합니다.

---

## Slide 34. 마무리

### 슬라이드 제목
정리: 구축은 완료, 최종 주장은 human-gold 이후 확정

### 핵심 메시지
CAPE-KG는 자동 구축과 평가 인프라를 완성했고, 이제 남은 핵심은 사람 검수 기반 evidence를 채워 최종 성능 주장을 claimable하게 만드는 것입니다.

### 슬라이드 본문
한 문장 요약:

> CAPE-KG는 한국어 장문 업무 문서에서 evidence-grounded procedural KG를 구축하는 자동 파이프라인과 평가 인프라를 완성했으며, 현재는 14개 human return file을 통해 human-gold, adjudication, mapping expert review, NCS-PCF crosswalk expert review, active-review effort를 수집하는 단계입니다.

현재 상태:

- Automatic KG build: complete
- LLM runs: complete for current diagnostic scope
- Structural diagnostics: complete
- Structural gap worklist: prepared for human review
- Pre-human handoff: PASS
- Claim gate: FAIL, expected
- Final performance claim: pending human-gold
- Next execution: human review return import and final table regeneration

### 발표자 설명
마지막에는 "실험이 실패하거나 멈춘 것이 아니라, 논문 주장을 안전하게 만들기 위해 human gate를 기다리는 상태"라고 정리합니다.

---

## Appendix A. 보고용 숫자 요약

| 구분 | 값 |
| --- | ---: |
| OCR clean sentence/evidence anchors | 5,009 |
| Layer 2 chunks | 214 |
| Evaluation chunks | 120 |
| Layer 1 NCS nodes | 4,109 |
| Layer 1 PCF nodes | 5,301 |
| Layer 2 nodes | 179 |
| Layer 2 edges | 906 |
| NCS mapping candidates | 110 |
| PCF mapping candidates | 110 |
| NCS-PCF crosswalk candidates | 220 |
| Neo4j import nodes | 9,589 |
| Neo4j import relationships | 10,499 |
| Review checkpoint candidates | 45 |
| Gateway branch gaps | 4 |
| Required human return files | 14 |
| Present human return files | 0 |
| Pre-human validation | current check count: see `../06_release/pre_human_handoff_validation.md` |
| Claim gate | FAIL, required failures 4 |

---

## Appendix B. 검증 상태

| 검증 항목 | 결과 |
| --- | --- |
| Post-annotation refresh | 완료 |
| Pre-human handoff validation | PASS |
| Release bundle checksums | OK |
| Neo4j CSV validation | PASS |
| Public-safe tar content scan | PASS |
| Method module coverage | M1-M11 all artifacts present |
| Submission completion audit | not complete, pending human-gold/IAA/adjudication/expert review |

---

## Appendix C. 핵심 파일 경로

| 목적 | 파일 |
| --- | --- |
| 현재 상세 발표 원고 | `experiments/cape_kg_eacl_20260627/07_reports/professor_presentation_detailed_methodology_experiments_20260628_ko.md` |
| 현재 실험 방법론/결과 정리 | `experiments/cape_kg_eacl_20260627/07_reports/current_experiment_methodology_and_results_ko.md` |
| 기존 발표 요약본 | `experiments/cape_kg_eacl_20260627/07_reports/professor_presentation_revised_current_20260628_ko.md` |
| final build report | `outputs/10_evaluation/final_build_report.md` |
| paper tables | `experiments/cape_kg_eacl_20260627/06_release/paper_tables.md` |
| claimable main table | `experiments/cape_kg_eacl_20260627/06_release/claimable_main_table.md` |
| claim gate report | `experiments/cape_kg_eacl_20260627/06_release/claim_gate_report.md` |
| submission completion audit | `experiments/cape_kg_eacl_20260627/06_release/submission_completion_audit_ko.md` |
| structural evaluation report | `experiments/cape_kg_eacl_20260627/04_evaluation/structural_evaluation_report.md` |
| structural gap worklist report | `experiments/cape_kg_eacl_20260627/04_evaluation/structural_gap_worklist_report.md` |
| human gate action plan | `experiments/cape_kg_eacl_20260627/06_release/human_gate_action_plan.md` |
| KG viewer | `outputs/09_visualization/kg_viewer.html` |
| Neo4j flat import | `outputs/11_neo4j_import_flat/` |
