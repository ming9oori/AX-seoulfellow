# EACL 제출 가능성 검토 및 수정된 연구·실험 계획서

**프로젝트명:** 업무 온톨로지 기반 기업용 멀티 AI 에이전트 자동 생성 및 운영을 위한 Agent Harness 기술 개발  
**검토 대상:** NCS/PCF 표준 레이어 + 수주·제안 업무 Layer2 KG 구축 방법론  
**작성일:** 2026-06-27  
**권장 논문명:** **CAPE-KG: Competency-Question Anchored Procedural Evidence Grounding for Domain Knowledge Graph Construction**

---

## 1. 결론 요약

현재 구축 방향은 **실무적으로 타당하고, 온톨로지 엔지니어링 관점에서도 안정적**이다. 발표 자료의 핵심인 “Layer1은 NCS/PCF 표준 기준축으로 얇게 구축하고, Layer2는 Task Frame과 Triple 중심으로 깊게 구축하며, 두 레이어를 직접 병합하지 않고 mapping edge로 느슨하게 연결한다”는 설계는 유지할 가치가 있다.

하지만 이를 **EACL main conference**에 그대로 제출하면, 리뷰어에게 다음과 같이 보일 위험이 크다.

> “한국어 수주·제안 문서를 대상으로 한 도메인 KG 구축 사례”

EACL은 NLP 학회이므로 단순 도메인 구축 결과보다 다음 요소가 필요하다.

1. **일반화 가능한 NLP 문제 정의**
2. **비교 가능한 baseline과 ablation**
3. **정량 평가 가능한 gold benchmark 또는 검증셋**
4. **기존 LLM-KG 연구 대비 명확한 차별점**
5. **재현 가능한 코드·스키마·프롬프트·평가 프로토콜**

따라서 본 연구는 다음과 같이 재정의하는 것이 좋다.

> **한국어 장문 업무 문서에서 절차형 업무 지식을 추출하고, 각 노드·엣지·슬롯을 원문 evidence span에 grounding하며, 표준 역량/프로세스 taxonomy에 연결하는 evidence-grounded procedural KG construction task**

이렇게 바꾸면 EACL의 **Information Extraction**, **Resources and Evaluation**, **NLP Applications**, **LLM Agents**, **NLP and Symbolic Reasoning** 영역에 걸친 연구로 포지셔닝할 수 있다.

---

## 2. EACL 제출 적합성 판단

### 2.1 Venue 적합성

EACL 2027 CFP는 substantial, original, unpublished NLP research를 받으며, 전통적인 연구 결과뿐 아니라 resource creation, negative findings, reproduction, novel linguistic insights도 허용한다. 또한 주제 영역에는 **Information Extraction**, **Information Retrieval and Text Mining**, **LLM Agents**, **NLP Applications**, **Resources and Evaluation**, **NLP and Symbolic Reasoning**이 포함되어 있다.  
Source: https://2027.eacl.org/calls/papers/

본 연구는 다음 조건을 만족하면 EACL에 충분히 의미가 있다.

| 항목 | 현재 상태 | EACL 제출 가능 상태로 만들기 위한 수정 |
|---|---|---|
| NLP task | 수주·제안 온톨로지 구축 | **Evidence-grounded procedural KG extraction**으로 정의 |
| 데이터 | 자이제 OCR + NCS/PCF | gold annotation subset + public benchmark 추가 |
| 방법론 | Task Frame LLM + Triple LLM | CQ-anchored schema retrieval + constrained generation + evidence verifier |
| 평가 | 품질 검수 중심 | F1, faithfulness, ontology conformance, procedural consistency, CQ answerability |
| novelty | 도메인 Layer2와 표준 Layer1 연결 | **evidence-span grounding + procedural KG + standard taxonomy bridge** |
| 재현성 | 내부 데이터 중심 | 공개 가능한 schema, prompt, code, derived annotations, visualization viewer 제공 |

### 2.2 일정 적합성

EACL 2027의 ARR submission deadline은 **2026년 8월 3일 AoE**이며, EACL commitment deadline은 **2026년 10월 11일**, acceptance notification은 **2026년 11월 12일**이다.  
Source: https://2027.eacl.org/calls/papers/

현재 발표 자료의 실행 계획은 2026년 10월까지 Layer2 graph, NCS/PCF mapping, crosswalk 검수를 진행하는 구조다. 즉, **현재 계획 그대로라면 EACL 2027 main submission에는 늦다.** EACL 2027을 목표로 한다면 8월 3일 전까지 최소한 다음이 필요하다.

1. gold annotation subset 완성
2. baseline 3개 이상 실험 완료
3. proposed method 실험 완료
4. ablation 일부 완료
5. error analysis 완료
6. 논문 초안 완성

따라서 일정 기준으로는 두 가지 전략이 있다.

### 전략 A: EACL 2027 단기 제출 전략

- 제출 형태: **short paper 또는 focused long paper**
- 데이터: 자이제 문서 전체가 아니라 100~150개 chunk gold subset
- 외부 검증: PAGED 또는 Text2KGBench 일부를 함께 사용
- 핵심 주장: “evidence-grounded procedural KG extraction에서 span grounding과 procedural validation이 hallucination을 줄인다”
- 위험: 실험 규모가 작으면 novelty가 약해질 수 있음

### 전략 B: 완성도 높은 full paper 전략

- 제출 시점: ACL/EMNLP 2027 또는 EACL 2028
- 데이터: 300~500개 chunk gold benchmark + 전체 KG 구축
- 외부 검증: PAGED + Text2KGBench + 한국어 업무 문서
- 핵심 주장: “long Korean enterprise procedural documents에서 표준 taxonomy alignment까지 포함한 end-to-end benchmark와 방법론”
- 추천: accept 가능성을 높이려면 전략 B가 더 안전함

---

## 3. Accept 가능성 판단

아래 평가는 실제 reviewer pool과 결과를 보장하는 것이 아니라, EACL/ARR 유형의 리뷰 기준을 기준으로 한 제출 준비도 평가다.

| 제출 버전 | 예상 판정 | 이유 |
|---|---|---|
| 현재 발표안 그대로 | **Reject 가능성 높음** | 도메인 구축 사례로 보일 위험, gold benchmark와 baseline 부족 |
| 현재안 + 방법론 설명만 강화 | **Borderline below** | novelty 주장 가능하지만 실험적 증거 부족 |
| 수정안 + gold subset + baselines + ablation | **Borderline to weak accept 가능권** | NLP task, 평가, 차별점이 생김 |
| 수정안 + 공개 가능한 benchmark + public benchmark 교차검증 + 강한 결과 | **Accept 가능권** | resource/evaluation + method contribution이 모두 성립 |

### 현재 상태의 가장 큰 약점

1. **Task novelty가 아직 명확하지 않다.**  
   Task Frame + Triple LLM은 이미 ontology-guided KG construction의 변형으로 보일 수 있다.

2. **데이터 공개 가능성이 불확실하다.**  
   원천 도서가 저작권 자료라면 raw text 공개가 어렵다. EACL resource/evaluation 논문은 재현성이 매우 중요하므로, 최소한 annotation schema, prompt, code, evaluation script, 비식별·파생 annotation, 공개 가능한 예시 subset이 필요하다.

3. **평가가 아직 검수 중심이다.**  
   EACL 논문은 “잘 만들었다”보다 “어떤 지표에서 기존 방법보다 낫다”를 보여줘야 한다.

4. **절차형 업무 지식이라는 장점이 아직 충분히 전면화되지 않았다.**  
   수주·제안은 단순 entity-relation 추출보다 절차, 의사결정, 조건, 산출물 흐름이 중요하다. 이 점을 논문의 핵심으로 삼아야 한다.

---

## 4. 관련 연구 대비 포지셔닝

### 4.1 LLM 기반 KG construction

SAC-KG는 LLM을 Generator, Verifier, Pruner로 구성해 대규모 domain KG를 구축하는 프레임워크를 제안했고, 기존 방법 대비 높은 precision을 보고했다.  
Source: https://aclanthology.org/2024.acl-long.238/

EDC는 Extract-Define-Canonicalize 구조로, 고정된 schema가 없거나 schema가 큰 상황에서 LLM 기반 KG construction을 수행하는 방법을 제안했다. 특히 schema를 prompt에 모두 넣기 어려운 문제와 canonicalization 문제를 다룬다.  
Source: https://aclanthology.org/2024.emnlp-main.548/

Taxonomy-driven KG construction은 curated taxonomy와 RAG를 결합하여 domain-specific KG extraction을 개선하는 방향을 보였다.  
Source: https://aclanthology.org/2025.findings-acl.223/

**본 연구의 차별점:**  
단순히 KG를 크게 만들거나 taxonomy를 참고하는 것이 아니라, **업무 절차의 실행 구조**와 **원문 evidence span grounding**을 동시에 요구한다. 또한 Layer2 업무 KG를 NCS/PCF라는 서로 다른 표준 기준축에 연결하여, 도메인 업무 지식이 역량·프로세스 표준을 매개하도록 설계한다.

### 4.2 Ontology-guided extraction과 faithfulness 평가

Text2KGBench는 ontology-driven KG generation에서 fact extraction performance, ontology conformance, hallucination을 평가하는 benchmark를 제안했다.  
Source: https://ar5iv.labs.arxiv.org/html/2308.02357

TextMineX는 ontology-guided LLM pipeline을 humanitarian mine action domain에 적용하면서 ontology conformance와 source-text faithfulness를 중요한 목표로 제시했다.  
Source: https://aclanthology.org/2026.findings-eacl.130.pdf

**본 연구의 차별점:**  
이미 ontology conformance와 faithfulness 자체는 novelty가 아니다. 본 연구는 이를 다음 단계로 강화해야 한다.

- triple 단위 evidence 문장 저장이 아니라 **subject/predicate/object/slot별 evidence span grounding**
- KG 전체가 아니라 **절차형 업무 흐름의 logical consistency** 평가
- 단순 ontology-guided extraction이 아니라 **CQ가 schema, extraction, evaluation을 동시에 통제**하는 구조

### 4.3 Procedural graph extraction

PAGED는 문서에서 procedural graph를 추출하는 benchmark를 제안했고, 절차형 그래프는 단순 순차 action뿐 아니라 non-sequential action과 constraints를 표현해야 한다고 강조한다.  
Source: https://aclanthology.org/2024.acl-long.583/

2026년 EACL Findings의 multi-agent procedural graph extraction 연구는 PAGED benchmark를 사용하며, 문장들이 actions, actors, gateways, constraints 같은 process elements와 정렬되고, flow edge가 temporal/logical dependencies를 포착한다고 설명한다.  
Source: https://aclanthology.org/2026.findings-eacl.158.pdf

**본 연구의 차별점:**  
기존 procedural graph extraction은 보통 process flow 자체에 집중한다. 본 연구는 여기에 다음을 추가한다.

1. 한국어 장문 업무 문서
2. 업무 ontology schema
3. evidence span grounding
4. NCS/PCF standard taxonomy bridge
5. Agent Harness 활용 가능성

---

## 5. 수정된 핵심 연구 질문

기존 연구 질문을 EACL형으로 다음과 같이 수정한다.

### RQ1. Evidence-grounded procedural KG extraction

한국어 장문 업무 문서에서 Task, ProcedureStep, DecisionGateway, GuardCondition, ArtifactFlow를 추출할 때, evidence-span grounding을 강제하면 unsupported triple과 hallucination을 줄일 수 있는가?

### RQ2. CQ-anchored schema control

Competency Question을 단순 요구사항 문서가 아니라 schema selection, LLM extraction, validation, evaluation의 anchor로 사용할 때, ontology conformance와 CQ answerability가 향상되는가?

### RQ3. Standard taxonomy bridge

Layer2 procedural KG가 NCS/PCF 표준 taxonomy mapping의 downstream 성능을 향상시키는가?

### RQ4. Human review efficiency

Evidence verifier와 active review queue가 전문가 검수 비용을 줄이면서 KG 품질을 높이는가?

---

## 6. 수정된 방법론: CAPE-KG

### 6.1 이름

**CAPE-KG: Competency-Question Anchored Procedural Evidence Grounding for Domain Knowledge Graph Construction**

### 6.2 핵심 아이디어

기존 방법은 다음과 같다.

```text
Document chunks
→ Task Frame LLM
→ Triple LLM
→ 후처리
→ Layer2 KG
→ NCS/PCF mapping
```

수정 방법은 다음과 같다.

```text
Competency Questions
→ CQ-linked schema retrieval
→ Procedural frame extraction
→ Evidence-span constrained triple extraction
→ Span verifier
→ Ontology/SHACL validator
→ Procedural consistency validator
→ Active expert review
→ Layer2 KG
→ NCS/PCF downstream mapping evaluation
```

### 6.3 기존 발표안에서 유지할 부분

현재 발표 자료의 다음 구조는 유지한다.

1. Layer1은 NCS/PCF 표준 기준축으로 결정론적으로 구축
2. Layer2는 수주·제안 업무를 깊게 표현
3. Layer2와 Layer1은 직접 병합하지 않고 mapping edge로 연결
4. Layer2는 Task Frame을 중심으로 triple을 귀속
5. mapping은 BM25/embedding 후보 검색과 사람 검수 기반으로 확정

### 6.4 새로 추가해야 할 부분

| 추가 요소 | 목적 | EACL novelty 기여 |
|---|---|---|
| CQ-linked schema retrieval | chunk마다 필요한 schema subset만 제공 | large schema prompt 문제 완화 |
| Evidence span grounding | 추출된 요소의 원문 위치 복원 | hallucination/faithfulness 평가 가능 |
| Procedural ontology schema | 업무 순서, gateway, condition, artifact flow 표현 | procedural graph extraction과 연결 |
| SHACL/JSON Schema validation | 생성 시점 및 사후 제약 | ontology conformance 평가 |
| Procedural consistency validator | 순환, gateway 누락, artifact flow 오류 탐지 | task-specific structural evaluation |
| Active review queue | 전문가 검수 우선순위화 | human-in-the-loop 효율성 평가 |
| Public benchmark cross-check | EACL 일반화 요구 대응 | 도메인 사례 한계 완화 |

---

## 7. 온톨로지 스키마 수정안

### 7.1 Node types

```text
DomainTask
ProcedureStep
DecisionGateway
GuardCondition
Artifact
ArtifactFlow
Role
ReviewCheckpoint
Principle
Risk
EvidenceAnchor
NCSCompetencyUnit
PCFElement
MappingCandidate
```

### 7.2 Edge types

```text
HAS_STEP
PRECEDES
BRANCHES_TO
HAS_GUARD_CONDITION
USES_INPUT
PRODUCES
FEEDS_INTO
PERFORMED_BY
HAS_DECISION_GATEWAY
HAS_REVIEW_CHECKPOINT
HAS_PRINCIPLE
HAS_RISK
EVIDENCED_BY
REQUIRES_CAPABILITY
PROCESS_CONTEXT
CANDIDATE_ALIGNS_WITH
```

### 7.3 Evidence anchor schema

```json
{
  "triple_id": "TRI-C02-00012",
  "subject": {
    "id": "T:capture_planning",
    "label": "수주영업",
    "type": "DomainTask",
    "evidence_span": {
      "chunk_id": "C02-S01-003",
      "page": 73,
      "start_char": 15,
      "end_char": 19,
      "text": "수주영업"
    }
  },
  "predicate": {
    "label": "PRODUCES",
    "evidence_span": {
      "chunk_id": "C02-S01-003",
      "page": 73,
      "start_char": 34,
      "end_char": 42,
      "text": "작성한다"
    }
  },
  "object": {
    "id": "A:capture_plan",
    "label": "Capture Plan",
    "type": "Artifact",
    "evidence_span": {
      "chunk_id": "C02-S01-003",
      "page": 73,
      "start_char": 45,
      "end_char": 57,
      "text": "Capture Plan"
    }
  },
  "confidence": 0.86,
  "review_status": "pending"
}
```

### 7.4 Validation rules

SHACL은 RDF graph를 shapes graph 조건으로 검증하는 W3C recommendation이다. 본 연구에서는 RDF 변환 후 SHACL 또는 JSON Schema 기반 검증을 적용한다.  
Source: https://www.w3.org/TR/shacl/

예시 제약은 다음과 같다.

```text
PRODUCES:
  subject ∈ {DomainTask, ProcedureStep}
  object ∈ {Artifact}
  evidence_anchor required

HAS_DECISION_GATEWAY:
  subject ∈ {DomainTask, ProcedureStep}
  object ∈ {DecisionGateway}
  outgoing BRANCHES_TO or ENABLES edge required

FEEDS_INTO:
  subject ∈ {Artifact}
  object ∈ {DomainTask, ProcedureStep}

PRECEDES:
  subject ∈ {DomainTask, ProcedureStep, ReviewCheckpoint}
  object ∈ {DomainTask, ProcedureStep, ReviewCheckpoint}
  no cycle within a same procedural flow
```

PROV-O는 provenance information을 표현하기 위한 W3C ontology이며, 본 연구에서는 LLM run, prompt version, chunk source, human reviewer를 provenance로 남기는 데 사용할 수 있다.  
Source: https://www.w3.org/TR/prov-o/

---

## 8. 데이터 및 annotation 계획

### 8.1 데이터 구성

| 데이터 | 역할 | 공개 가능성 |
|---|---|---|
| 자이제 OCR 5,009 sentences | 한국어 수주·제안 업무 문서 | 원문 공개는 저작권 검토 필요 |
| NCS JSON | 표준 역량 기준축 | 공개 표준 데이터 여부 확인 후 출처 명시 |
| PCF JSON | 표준 프로세스 기준축 | 라이선스 확인 필요 |
| PAGED benchmark | 외부 procedural graph benchmark | 공개 benchmark |
| Text2KGBench subset | ontology conformance 외부 검증 | 공개 benchmark |

### 8.2 Gold annotation subset

EACL 제출용 최소 annotation 계획은 다음과 같다.

| 항목 | 단기 제출 최소 | 강한 full paper 권장 |
|---|---:|---:|
| Annotated chunks | 100~150 | 300~500 |
| Gold triples/edges | 500~800 | 1,500~3,000 |
| Evidence spans | 모든 gold element | 모든 gold element |
| Annotators | 2명 + adjudicator | 2~3명 + adjudicator |
| IAA | edge F1, type agreement | edge F1, type agreement, span IoU |
| 공개 | schema/prompt/eval code + 예시 subset | 가능하면 derived benchmark 공개 |

### 8.3 Annotation guideline 핵심

각 chunk에 대해 다음을 표시한다.

1. Task 또는 ProcedureStep
2. Artifact
3. Role
4. DecisionGateway
5. GuardCondition
6. ReviewCheckpoint
7. Principle/Risk
8. Edge type
9. Evidence span
10. 원문 페이지와 chunk ID

---

## 9. 실험 설계

### 9.1 Baselines

| ID | 방법 | 설명 |
|---|---|---|
| B0 | Plain LLM Triple Extraction | schema 없이 subject-predicate-object 추출 |
| B1 | Predicate-constrained LLM | 허용 predicate만 제시 |
| B2 | Current Project Baseline | Task Frame LLM + Triple LLM + 후처리 |
| B3 | EDC-style Baseline | Extract → Define → Canonicalize 구조 구현 |
| B4 | Taxonomy-RAG Baseline | NCS/PCF/Task taxonomy retrieval 후 추출 |
| B5 | Procedural Prompt Baseline | action/gateway/condition/flow만 추출 |
| P | CAPE-KG | CQ retrieval + procedural schema + evidence grounding + validators |

### 9.2 Proposed method modules

```text
M1. Document structure recovery
M2. CQ generation and selection
M3. CQ-linked schema retrieval
M4. Procedural frame extraction
M5. Evidence-span constrained triple extraction
M6. Span verifier
M7. Ontology/SHACL validator
M8. Procedural consistency validator
M9. Alias/canonicalization module
M10. Active review queue
M11. NCS/PCF mapping evaluator
```

### 9.3 Main evaluation metrics

| 지표 | 정의 |
|---|---|
| Node F1 | gold node type과 label canonicalization 기준 precision/recall/F1 |
| Edge F1 | gold edge type과 source-target match 기준 precision/recall/F1 |
| Evidence Exact Match | predicted span이 gold span과 정확히 일치하는 비율 |
| Evidence IoU | character span overlap / union |
| Unsupported Edge Rate | source text로 지지되지 않는 edge 비율 |
| Ontology Conformance | domain/range/schema 제약을 만족하는 edge 비율 |
| Procedural Consistency | cycle, gateway branch, artifact flow 제약 위반률 |
| CQ Answerability | competency question을 graph query로 답할 수 있는 비율 |
| NCS/PCF Mapping P@K | gold 또는 expert-confirmed mapping 후보가 top-k에 포함되는 비율 |
| Active Review Efficiency | 동일 검수 시간 대비 corrected high-impact errors 수 |

### 9.4 Ablation study

| Ablation | 제거 요소 | 예상 영향 |
|---|---|---|
| P - CQ | CQ anchor 제거 | CQ answerability 감소 |
| P - Evidence | evidence span 제거 | unsupported edge 증가 |
| P - Procedural schema | gateway/condition/artifact flow 제거 | procedural consistency 감소 |
| P - Schema retrieval | 전체 schema 또는 schema 없음 | schema conformance 감소 또는 context overflow |
| P - Validator | SHACL/JSON validation 제거 | invalid edge 증가 |
| P - Active review | 무작위 검수 | 검수 효율 감소 |
| P - Standard bridge | NCS/PCF mapping 제거 | downstream utility 평가 불가 |

### 9.5 Downstream task: NCS/PCF mapping

Layer2 KG가 정말 유용한지 보이려면 downstream task가 필요하다. 기존 발표 자료의 Layer2 bridge support 아이디어를 평가 태스크로 바꾼다.

```text
Input: Layer2 DomainTask representation
Output 1: Top-K NCSCompetencyUnit candidates
Output 2: Top-K PCFElement candidates
Output 3: NCS-PCF crosswalk candidates with Layer2 bridge support
```

비교한다.

```text
Text-only task description
vs.
Task Frame only
vs.
Flat triples
vs.
Procedural KG with evidence anchors
```

평가 지표는 다음이다.

```text
P@1, P@5, MRR, nDCG@10, expert accept rate, explanation quality score
```

---

## 10. 논문 contribution 문장 수정안

논문 introduction 마지막에는 다음처럼 contribution을 써야 한다.

```text
Our contributions are threefold.
First, we formulate evidence-grounded procedural KG construction from long enterprise documents as a constrained information extraction task, requiring not only typed nodes and relations but also character-level evidence anchors.
Second, we propose CAPE-KG, a competency-question anchored extraction framework that combines schema retrieval, constrained generation, evidence-span verification, ontology validation, and procedural consistency checking.
Third, we introduce a Korean bid/proposal work-domain benchmark and evaluate whether the resulting procedural KG improves standard taxonomy alignment to capability and process reference layers.
```

한국어 버전은 다음과 같다.

```text
본 연구의 기여는 세 가지다.
첫째, 한국어 장문 업무 문서에서 절차형 KG를 구축하는 문제를 character-level evidence grounding이 필요한 constrained information extraction task로 정의한다.
둘째, CQ 기반 schema retrieval, constrained generation, evidence-span verification, ontology validation, procedural consistency checking을 결합한 CAPE-KG 프레임워크를 제안한다.
셋째, 수주·제안 업무 benchmark를 구축하고, 추출된 절차형 KG가 NCS/PCF 표준 taxonomy alignment를 개선하는지 평가한다.
```

---

## 11. EACL 제출용 논문 구조

### Long paper 구조

```text
1. Introduction
2. Related Work
   2.1 LLM-based Knowledge Graph Construction
   2.2 Ontology-guided Information Extraction
   2.3 Procedural Graph Extraction
   2.4 Evidence Grounding and Faithfulness
3. Task Definition
   3.1 Evidence-grounded Procedural KG Construction
   3.2 CQ Answerability
   3.3 Standard Taxonomy Alignment
4. Dataset and Annotation
   4.1 Korean Bid/Proposal Corpus
   4.2 Annotation Schema
   4.3 Inter-annotator Agreement
   4.4 Public Release and Copyright Constraints
5. Method: CAPE-KG
   5.1 CQ-linked Schema Retrieval
   5.2 Procedural Frame Extraction
   5.3 Evidence-span Constrained Generation
   5.4 Validation and Active Review
6. Experiments
   6.1 Baselines
   6.2 Metrics
   6.3 Main Results
   6.4 Ablation Studies
   6.5 Downstream NCS/PCF Mapping
7. Analysis
   7.1 Error Types
   7.2 Evidence Failure Cases
   7.3 Procedural Consistency Cases
8. Conclusion
Limitations
Ethical Considerations
References
```

ARR/EACL 제출에서는 Limitations 섹션이 요구되며, official ACL template과 ARR submission requirements를 따라야 한다.  
Source: https://aclrollingreview.org/cfp

---

## 12. Reviewer 관점의 예상 질문과 대응

| 예상 reviewer 질문 | 대응 전략 |
|---|---|
| 단순 domain application 아닌가? | public benchmark와 일반 task definition을 포함 |
| 데이터가 공개되지 않으면 재현성이 낮지 않은가? | schema, prompts, code, eval script, derived annotations, synthetic examples 공개 |
| ontology-guided extraction은 이미 많지 않은가? | evidence span + procedural consistency + standard taxonomy bridge를 차별점으로 제시 |
| 왜 Korean enterprise document인가? | 저자원 업무 도메인, OCR noise, long document, mixed Korean-English aliases를 challenge로 정의 |
| LLM prompt engineering 아닌가? | constrained decoding/schema validation/quantitative ablation을 포함 |
| 평가가 subjective하지 않은가? | gold span, gold edge, SHACL validation, mapping P@K로 정량화 |
| NCS/PCF mapping이 NLP contribution인가? | downstream evaluation으로 제한하고 core는 information extraction에 둠 |

---

## 13. EACL 제출 전 필수 체크리스트

### 최소 accept 가능권 체크리스트

- [ ] 100개 이상 chunk gold annotation
- [ ] 최소 500개 이상 gold node/edge/evidence item
- [ ] 2명 이상 annotation 및 agreement 보고
- [ ] B0/B1/B2 baseline 완료
- [ ] CAPE-KG proposed result 완료
- [ ] ablation 3개 이상 완료
- [ ] error analysis 표 1개 이상
- [ ] public benchmark 또는 public subset 실험 포함
- [ ] 코드/프롬프트/스키마 공개 계획 명시
- [ ] Limitations 섹션 포함

### 강한 accept 가능권 체크리스트

- [ ] 300~500개 chunk gold annotation
- [ ] 1,500개 이상 gold edge/evidence item
- [ ] PAGED 또는 Text2KGBench와 교차 실험
- [ ] EDC/SAC-KG/Taxonomy-RAG 계열 baseline 구현 또는 합리적 재현
- [ ] NCS/PCF mapping downstream 평가 포함
- [ ] active review efficiency 평가 포함
- [ ] visualization/demo 제공
- [ ] raw text 공개 불가 시 reproducibility mitigation 명확화

---

## 14. 수정된 일정안

### EACL 2027 제출을 강행하는 경우

```text
2026.06.27~07.03
- 논문 title, task definition, related work 확정
- annotation guideline v1 작성
- 30 chunk pilot annotation

2026.07.04~07.12
- 100~150 chunk gold annotation
- B0/B1/B2 baseline 구현
- CAPE-KG minimal implementation

2026.07.13~07.20
- main experiments
- evidence span evaluation
- ontology conformance evaluation
- procedural consistency evaluation

2026.07.21~07.27
- ablation
- error analysis
- paper writing

2026.07.28~08.02
- internal review
- reproducibility package
- final submission

2026.08.03
- ARR submission
```

이 일정은 매우 공격적이다. 논문 품질을 위해서는 submission scope를 줄여야 한다.

### 더 안전한 full paper 일정

```text
2026.07~08
- full annotation guideline
- 300~500 chunk gold benchmark
- public benchmark adaptation

2026.09
- full CAPE-KG pipeline
- baseline and ablation
- NCS/PCF downstream mapping evaluation

2026.10
- full KG construction
- expert review
- visualization/demo

2026.11~12
- 논문 작성 및 외부 피드백

2027년 이후 적절한 *CL venue 제출
```

---

## 15. KG 시각화 계획

본 답변과 함께 다음 파일을 생성했다.

```text
AX_KG_visualization.html
AX_KG_visualization.svg
AX_KG_pilot_graph.json
AX_KG_pilot_graph.graphml
```

현재 시각화는 다음을 포함한다.

1. 발표 자료 기반 Layer2 representative procedural KG
2. 실제 AX.zip에서 확인한 일부 NCSCompetencyUnit
3. 실제 AX.zip에서 확인한 일부 PCFElement
4. Layer2→NCS, Layer2→PCF, NCS↔PCF candidate mapping edge
5. 검색, mapping edge 토글, 노드 클릭 상세보기
6. 추후 실제 `layer2_nodes.jsonl`, `layer2_edges.jsonl` 또는 JSON 그래프를 불러올 수 있는 viewer 구조

주의할 점은, 이 파일은 **완성 KG가 아니라 pilot visualization**이다. 실제 LLM 추출과 검수 후 생성되는 `layer2_nodes.jsonl`, `layer2_edges.jsonl`, `l2_ncs_mapping_candidates.jsonl`, `l2_pcf_mapping_candidates.jsonl`로 대체해야 최종 KG visualization이 된다.

---

## 16. 최종 권고

### 현재 방향을 버릴 필요는 없다

기존의 Layer1/Layer2 분리, NCS/PCF 표준축, Layer2 Task Frame, Triple LLM, mapping edge 구조는 유지해야 한다. 이 구조는 실무적으로 좋고, Agent Harness 연계에도 적합하다.

### 다만 EACL 논문으로는 연구 질문을 바꿔야 한다

기존 질문:

```text
수주·제안 업무 온톨로지를 어떻게 구축할 것인가?
```

수정 질문:

```text
LLM이 장문 한국어 업무 문서에서 절차형 KG를 추출할 때,
원문 evidence span, procedural constraints, CQ-based schema control이
faithfulness와 ontology conformance를 얼마나 개선하는가?
```

### Accept 가능성을 높이는 최종 포지션

가장 강한 포지션은 다음이다.

> **CAPE-KG is not merely a domain ontology construction pipeline; it is an evidence-grounded procedural information extraction framework for long enterprise documents, evaluated by span-level grounding, ontology conformance, procedural consistency, CQ answerability, and standard taxonomy alignment.**

이렇게 수정하면 EACL 제출 의미가 있다. 단, **gold annotation과 baseline 실험 없이 방법론만 제출하면 accept 가능성은 낮다.**

---

## References

1. EACL 2027 Call for Papers. https://2027.eacl.org/calls/papers/
2. ACL Rolling Review CFP. https://aclrollingreview.org/cfp
3. Chen et al. 2024. SAC-KG: Exploiting Large Language Models as Skilled Automatic Constructors for Domain Knowledge Graph. https://aclanthology.org/2024.acl-long.238/
4. Zhang and Soh. 2024. Extract, Define, Canonicalize: An LLM-based Framework for Knowledge Graph Construction. https://aclanthology.org/2024.emnlp-main.548/
5. Pan et al. 2025. Taxonomy-Driven Knowledge Graph Construction for Domain-Specific Scientific Applications. https://aclanthology.org/2025.findings-acl.223/
6. Mihindukulasooriya et al. 2023. Text2KGBench: A Benchmark for Ontology-Driven Knowledge Graph Generation from Text. https://ar5iv.labs.arxiv.org/html/2308.02357
7. Zhou et al. 2026. TextMineX: Data, Evaluation Framework and Ontology-guided LLM Pipeline for Humanitarian Mine Action. https://aclanthology.org/2026.findings-eacl.130.pdf
8. Du et al. 2024. PAGED: A Benchmark for Procedural Graphs Extraction from Documents. https://aclanthology.org/2024.acl-long.583/
9. Ying et al. 2026. Multi-Agent Procedural Graph Extraction with Structural Feedback. https://aclanthology.org/2026.findings-eacl.158.pdf
10. W3C SHACL. https://www.w3.org/TR/shacl/
11. W3C PROV-O. https://www.w3.org/TR/prov-o/
