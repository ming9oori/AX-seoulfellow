# 실험 계획서 v2  
## CQ-Anchored Evidence-First Procedural Ontology Construction for Bid/Proposal Work

**작성일:** 2026-06-27  
**대상 데이터:** AX.zip의 NCS, PCF, PCF metrics, 산업별 PCF, 자이제 OCR sentence 데이터  
**연구 범위:** 데이터 전처리, 업무 온톨로지 스키마 설계, Layer1/Layer2 온톨로지 구축, 품질 평가  
**제외 범위:** 현 단계에서는 Agent Harness 성능평가와 운영 자동화 실험은 본 실험의 1차 평가 범위에서 제외하고, 후속 utility evaluation으로 둔다.

---

## 0. 핵심 결론

기존 발표안의 기본 방향인 **Layer1은 얇게, Layer2는 깊게, 연결은 느슨하게**라는 원칙은 유지할 가치가 있다. 다만 논문 novelty를 확보하려면 기존의 `Task Frame LLM + Triple LLM + 후처리`를 그대로 사용하는 것만으로는 부족하다. 이 구조는 최근 LLM 기반 KG construction 연구에서 이미 널리 쓰이는 **schema-guided extraction** 또는 **ontology-guided triplet extraction**의 변형으로 보일 가능성이 높다.

따라서 본 연구는 다음 방법론으로 확장한다.

> **CQ-Anchored Evidence-First Procedural Ontology Construction, 이하 CEP-Onto**  
> Competency Question으로 온톨로지 요구사항과 평가 질문을 먼저 생성하고, 문서의 모든 추출 단위를 page/sentence/character span에 anchor한 뒤, SHACL/JSON Schema 기반 executable constraint를 통해 LLM이 자유롭게 triple을 쓰지 못하게 하며, 최종적으로 수주·제안 업무를 “flat triple graph”가 아니라 **절차·의사결정·산출물·역할이 결합된 Evidence-backed Procedural Ontology**로 구축한다.

기존 발표안 대비 핵심 변화는 다음과 같다.

| 구분 | 기존 발표안 | 개선안: CEP-Onto |
|---|---|---|
| 구축 방식 | Task Frame 후 Triple 추출 | CQ → Anchor → Tool-constrained extraction → Verification → CQ 재평가 폐루프 |
| LLM 통제 | Prompt와 predicate 목록으로 통제 | SHACL/JSON Schema/Pydantic-style tool schema로 생성 시점부터 통제 |
| 근거 관리 | chunk/page/evidence sentence | subject, predicate, object, slot 값 각각에 page/sentence/character span anchor |
| 업무 표현 | Task Frame + Triple | Task Frame + Triple + Procedure Gateway + Guard Condition + Artifact Flow |
| 평가 | 추출 품질, 검수 | CQ answerability, ontology conformance, hallucination rate, process consistency, expert effort reduction |
| 사람 검수 | review sheet | uncertainty/centrality/conflict 기반 active review |
| 표준 연결 | Layer2 이후 NCS/PCF 후보 매핑 | NCS/PCF를 사후 매핑뿐 아니라 weak standard anchors와 mapping consistency check에 활용 |

---

## 1. 관련 연구 조사 요약

### 1.1 전통적 온톨로지 공학

고전적 온톨로지 개발 방법론은 도메인과 범위 정의, 기존 자원 재사용, 클래스·속성·인스턴스 정의, 평가 및 문서화를 강조한다. Ontology Development 101, METHONTOLOGY, NeOn Methodology는 여전히 논문 방법론의 기반으로 사용할 수 있다. 특히 본 연구는 NCS와 PCF라는 이미 구조화된 표준 자원을 재사용하므로 NeOn의 reuse/re-engineering 관점과 잘 맞는다.

그러나 전통적 방법론은 전문가 의존도가 높고, 비정형 문서에서 업무 절차 지식을 대량으로 추출하는 데 한계가 있다. 따라서 본 연구는 전통적 ontology engineering을 **요구사항·스키마·검증 프레임**으로 사용하고, 실제 instance/triple population은 LLM 기반으로 수행한다.

### 1.2 LLM 기반 Knowledge Graph Construction

최근 LLM 기반 KG construction 연구는 크게 다음 세 흐름으로 나뉜다.

1. **Schema-based / ontology-guided extraction**  
   사전에 정의된 entity type, relation type, domain/range constraints를 제공하고, LLM이 그 안에서 triple을 생성하도록 한다.

2. **Schema-free / open extraction**  
   문서에서 entity와 relation을 자유롭게 추출한 뒤, 후속 canonicalization과 schema induction으로 정리한다.

3. **Hybrid / iterative construction**  
   ontology engineering, extraction, fusion, validation을 반복하면서 그래프를 확장한다.

Text2KGBench는 ontology-driven KG generation을 평가할 때 ontology conformance, input faithfulness, hallucination을 함께 측정해야 한다는 점을 제시했다. 이는 본 연구의 평가 지표 설계에 직접 반영한다.

### 1.3 Ontology-guided triplet extraction과 few-shot/in-context learning

도메인별 KG construction에서는 대규모 labeled data가 부족한 경우가 많다. Maintenance Short Texts 대상 연구에서는 ontology-guided triplet extraction과 in-context learning을 결합하고, 20개의 의미적으로 유사한 예시만으로 fine-tuning 기반 방법과 비교 가능한 성능을 얻을 수 있음을 보였다.

본 연구는 이를 그대로 복제하지 않고, 자이제 수주·제안 문서에 대해 다음과 같이 확장한다.

- 단순 triple이 아니라 **업무 절차 단위**를 추출한다.
- 예시는 무작위 few-shot이 아니라 **active review에서 승인된 high-value examples**를 축적한다.
- 모든 추출 결과는 character-level anchor와 SHACL 검증을 통과해야 한다.

### 1.4 Competency Question 기반 온톨로지 개발과 평가

Competency Question, 이하 CQ는 온톨로지가 답할 수 있어야 하는 질문이다. 최근 연구는 RAG를 사용해 domain document에서 CQ를 생성하는 접근을 제안했으며, domain knowledge를 검색해 넣는 방식이 zero-shot CQ 생성보다 구체적인 온톨로지 과제에서 유리할 수 있음을 보였다.

본 연구의 novelty는 CQ를 단순 요구사항 문서로만 두지 않는다는 점이다. CQ를 다음 네 가지 기능으로 사용한다.

1. **Scope definition:** 어떤 업무 지식을 추출할지 결정한다.
2. **Extraction driver:** 답변 불가능한 CQ를 찾고, 해당 CQ를 해결할 수 있는 evidence를 다시 검색한다.
3. **Validation query:** 완성된 그래프가 질문에 답할 수 있는지 SPARQL/Graph query로 확인한다.
4. **Active review priority:** 답변 품질이 낮은 CQ와 관련된 triple을 우선 검수한다.

### 1.5 Grounded extraction과 provenance

최근 grounded KG extraction 연구는 hallucination을 줄이기 위해 triple의 각 요소가 원문 span으로 복원될 수 있어야 한다고 본다. AEVS는 anchor discovery, grounded extraction, restoration verification, coverage-aware supplement의 구조를 제안했다.

본 연구는 이를 한국어 OCR 기반 업무 문서에 맞게 변형한다.

- 문장 단위 row만 evidence로 쓰지 않고, row 내부의 **character span**까지 저장한다.
- `task_name`, `definition`, `inputs`, `outputs`, `roles`, `decision_points`, `principles` 등 Task Frame slot도 각각 anchor를 가진다.
- LLM이 만든 추론성 문장과 원문 직접 근거를 분리한다.
- 근거 없는 relation은 `unsupported_candidate`로 격리한다.

### 1.6 Production-grade KG extraction과 dynamic ontology prompting

ODKE+는 ontology-guided prompting, evidence retrieval, grounding verification, corroboration, normalization을 결합한 production-grade KG extraction pipeline을 제안했다. 이 흐름은 본 연구에서 다음 두 가지로 차용한다.

- relation extraction을 한 번에 끝내지 않고 **Evidence Retriever → Extractor → Grounder → Corroborator → Ingestor**로 나눈다.
- 전체 ontology를 매번 prompt에 넣지 않고, 현재 chunk와 관련된 **ontology snippet**만 동적으로 제공한다.

### 1.7 Semantic Web 표준

본 연구의 최종 산출물은 JSONL만으로 끝내지 않고 RDF/Turtle, OWL, SHACL, PROV-O를 함께 사용한다.

- RDF는 subject-predicate-object triple로 정보를 표현하는 그래프 데이터 모델이다.
- OWL은 class, property, individual, datatype value 및 추론 가능한 axioms를 표현할 수 있다.
- SHACL은 RDF graph가 지정된 shape 조건을 만족하는지 검증하는 데 사용한다.
- PROV-O는 누가, 어떤 활동으로, 어떤 근거에서 지식을 생성했는지를 표현하는 provenance 모델로 사용한다.

---

## 2. 연구 공백과 novelty 주장

### 2.1 연구 공백

기존 연구와 발표안을 함께 보면 다음 공백이 남아 있다.

1. **업무 절차성의 부족**  
   대부분의 LLM 기반 KG construction은 entity-relation-object triple에 집중한다. 그러나 수주·제안 업무는 “무엇이 무엇과 관련된다”보다 “어떤 조건에서 어떤 업무가 선행되고, 어떤 산출물을 만들고, 어떤 의사결정으로 분기되는가”가 더 중요하다.

2. **chunk-level evidence의 한계**  
   chunk 전체를 evidence로 저장하면 검수자는 실제 어떤 단어 또는 문장에 근거했는지 다시 찾아야 한다. OCR 문서에서는 이 문제가 더 크다.

3. **CQ와 extraction의 분리**  
   많은 온톨로지 연구에서 CQ는 요구사항 또는 평가용 질문으로만 사용된다. 하지만 실제 구축 과정에서는 CQ가 추출 대상과 검수 우선순위를 결정하는 폐루프 제어 변수로 쓰일 수 있다.

4. **post-hoc validation의 한계**  
   LLM이 잘못된 구조를 만든 뒤 SHACL로 걸러내는 방식은 오류를 줄일 수 있지만, 생성 자체를 막지는 못한다.

5. **표준 매핑의 사후 처리화**  
   NCS/PCF를 온톨로지 구축 뒤에만 붙이면, Layer2 업무 추출 자체에는 표준 지식의 구조가 거의 반영되지 않는다.

### 2.2 본 연구의 novelty

본 연구는 다음 5개를 novelty로 주장한다.

#### Novelty 1. CQ-driven closed-loop ontology construction

CQ를 단순 평가 문항이 아니라, 구축 루프의 제어 신호로 사용한다. 즉, 그래프가 특정 CQ에 답하지 못하면 관련 chunk를 다시 검색하고, 누락된 task/role/artifact/decision/triple을 추가 추출한다.

#### Novelty 2. Evidence-first procedural ontology

모든 업무 지식은 원문 근거를 먼저 anchor한 뒤 그래프에 편입한다. 특히 수주·제안 업무의 절차성을 표현하기 위해 다음 구조를 도입한다.

```text
TaskFrame
+ ProcedureStep
+ DecisionGateway
+ GuardCondition
+ ArtifactFlow
+ RoleAssignment
+ EvidenceAnchor
```

#### Novelty 3. Ontology-to-tool constrained extraction

SHACL/JSON Schema/Pydantic-style schema에서 LLM tool interface를 생성한다. LLM은 자유 JSON을 생성하지 않고, `create_task_frame`, `add_relation`, `attach_evidence_anchor`, `reject_candidate` 같은 constrained tool만 호출하도록 한다. 이 방식은 post-hoc validation이 아니라 **generation-time constraint enforcement**를 목표로 한다.

#### Novelty 4. Standard-triangulated domain ontology

NCS와 PCF는 단순히 나중에 연결되는 표준 노드가 아니라, Layer2 task 추출과 검증에 활용되는 weak standard anchors가 된다. 예를 들어 어떤 task가 NCS의 “전략 수립”류 능력단위와 PCF의 “Develop strategy”류 process에 동시에 약하게 연결되면, 해당 task의 정의·입력·산출물 검증 우선순위가 올라간다.

#### Novelty 5. Active expert review with uncertainty, centrality, and conflict

모든 triple을 사람이 검수하지 않고, 다음 기준으로 검수 대상을 선택한다.

```text
review_priority =
  0.30 × extraction_uncertainty
+ 0.20 × evidence_anchor_risk
+ 0.20 × graph_centrality
+ 0.15 × mapping_disagreement
+ 0.15 × conflict_score
```

이를 통해 전문가 검수 비용 대비 그래프 품질 개선 폭을 실험적으로 검증한다.

---

## 3. 연구 질문과 가설

### RQ1. CQ 기반 폐루프가 온톨로지의 coverage와 answerability를 높이는가?

- **H1:** CQ-driven loop를 적용한 방법은 one-shot extraction 대비 CQ answerability와 graph coverage가 유의하게 높다.

### RQ2. Evidence-anchor-first extraction이 hallucination을 줄이는가?

- **H2:** character-level evidence anchor와 restoration verification을 적용한 방법은 chunk-level evidence 방식보다 unsupported triple rate가 낮다.

### RQ3. Ontology-to-tool constrained extraction이 ontology conformance를 높이는가?

- **H3:** SHACL/JSON Schema 기반 tool-constrained extraction은 prompt-only predicate restriction보다 SHACL violation rate와 invalid domain/range relation을 줄인다.

### RQ4. Procedural ontology schema가 수주·제안 업무의 실행 구조를 더 잘 표현하는가?

- **H4:** TaskFrame+Triple만 사용하는 baseline보다 ProcedureStep, DecisionGateway, GuardCondition, ArtifactFlow를 포함한 schema가 precedence, decision, artifact-flow relation F1에서 더 높다.

### RQ5. Active expert review가 동일 검수 시간에서 더 높은 품질 개선을 만드는가?

- **H5:** uncertainty/centrality/conflict 기반 active review는 random review보다 accepted-correct-triples per expert-minute가 높다.

---

## 4. 데이터셋과 전처리 계획

### 4.1 데이터 구성

AX.zip 기준 1차 실험 데이터는 다음과 같다.

| 데이터 | 파일 | 규모 | 역할 |
|---|---|---:|---|
| NCS 대분류 | `01_ncs/ncs_lclas.json` | 192 raw / 24 current-use | Layer1 NCS 계층 |
| NCS 중분류 | `01_ncs/ncs_mclas.json` | 665 raw / 84 current-use | Layer1 NCS 계층 |
| NCS 소분류 | `01_ncs/ncs_sclas.json` | 2,239 raw / 281 current-use | Layer1 NCS 계층 |
| NCS 세분류 | `01_ncs/ncs_dclas.json` | 2,165 raw / 269 current-use | Layer1 NCS 계층 |
| NCS 능력단위 | `01_ncs/ncs_unit.json` | 28,666 raw / 3,450 current-use | Layer1 capability axis |
| PCF element | `02_pcf/pcf_data.json` | 2,017 | Layer1 process axis |
| PCF metrics | `02_pcf/pcf_metrics.json` | 3,284 | optional metric nodes |
| Industry PCF | `02_pcf/industries/*.json` | 20 files | variant/robustness analysis |
| 자이제 OCR | `자이제_ocr_sentences.xlsx` | 5,009 rows | Layer2 업무 온톨로지 원천 |

### 4.2 NCS 전처리

NCS는 다음 조건을 기본 current-use filter로 사용한다.

```text
NCS_DEGR == 29 AND USG_YN == "Y"
```

노드 ID 설계는 다음과 같다.

```text
NCSLargeClass      ncs:L:{NCS_LCLAS_CD}
NCSMiddleClass     ncs:M:{NCS_LCLAS_CD}-{NCS_MCLAS_CD}
NCSSmallClass      ncs:S:{NCS_LCLAS_CD}-{NCS_MCLAS_CD}-{NCS_SCLAS_CD}
NCSSubDivision     ncs:D:{NCS_LCLAS_CD}-{NCS_MCLAS_CD}-{NCS_SCLAS_CD}-{NCS_SUBD_CD}
NCSCompetencyUnit  ncs:CU:{NCS_CL_CD}
```

전처리 품질 검사는 다음을 포함한다.

- 필수 코드 누락률
- 계층 경로 복원률
- 중복 label 비율
- 능력단위 정의 누락률
- level 값 분포
- 29차 사용본 필터 후 orphan node 수

### 4.3 PCF 전처리

PCF는 `pcf_data.json`을 기준으로 level 1~5 계층을 복원한다. parent는 `pcfId`가 아니라 상위 요소의 `hid`이므로, 다음 인덱스를 먼저 만든다.

```python
hid_to_pcf_id = {element["hid"]: element["pcfId"] for element in pcf_elements}
parent_id = hid_to_pcf_id[element["parent"]]
```

PCF metrics는 `pcfId` 또는 `hid`를 기준으로 연결한다.

```text
(:PCFElement)-[:HAS_METRIC]->(:PCFMetric)
```

산업별 PCF는 1차 실험에서 Layer1에 병합하지 않는다. 단, robustness analysis에서 cross-industry PCF와 산업별 PCF 간 label/definition 변화가 Layer2 매핑에 미치는 영향을 측정한다.

### 4.4 OCR 전처리

OCR Excel은 문장과 페이지 컬럼만 있으므로 다음 단계가 필요하다.

#### Step 1. Row cleaning

- 빈 행 제거
- page number-only row 제거
- 헤더/푸터/판권/목차/색인 구간 표시
- 표 fragment 탐지
- OCR 이상 token 탐지
- 한영 혼합어와 약어 보존

#### Step 2. Document structure reconstruction

```text
Document
→ Chapter
→ Section
→ Subsection
→ Chunk
→ Sentence
→ EvidenceAnchor
```

#### Step 3. EvidenceAnchor 생성

각 문장은 다음 metadata를 가진다.

```json
{
  "sentence_id": "SENT-P073-0004",
  "page": 73,
  "text": "...",
  "char_start": 0,
  "char_end": 128,
  "section_id": "CH02-SEC03",
  "is_body": true,
  "is_index": false,
  "ocr_risk": 0.12
}
```

#### Step 4. Chunking variants

실험을 위해 chunking 방법을 3개로 비교한다.

| 조건 | 설명 | 예상 장점 | 예상 위험 |
|---|---|---|---|
| C1 sentence-window | 5~8 sentence sliding window | 근거 정밀도 높음 | 절차 문맥 손실 |
| C2 section-based | 절/소절 단위 chunk | 업무 흐름 보존 | chunk가 길어질 수 있음 |
| C3 hybrid semantic | section 기반 + 길이 초과 시 semantic split | 균형 | 구현 복잡도 |

---

## 5. 제안 방법론: CEP-Onto Pipeline

### 5.1 전체 파이프라인

```text
AX.zip
  ↓
Data Manifest & Integrity Check
  ↓
NCS/PCF deterministic preprocessing
  ↓
OCR cleaning & EvidenceAnchor generation
  ↓
RAG-based CQ generation
  ↓
Initial TBox / SHACL / tool schema generation
  ↓
Ontology snippet retrieval per chunk
  ↓
Anchor-first extraction
  ↓
Tool-constrained task/procedure/triple generation
  ↓
Grounding & restoration verification
  ↓
CQ answerability test
  ↓
Active expert review
  ↓
Canonicalization & graph fusion
  ↓
RDF/OWL/SHACL/PROV-O serialization
  ↓
Evaluation report
```

### 5.2 CQ generation module

CQ는 RAG 기반으로 생성한다. 입력은 OCR chunk, 목차 구조, 색인, NCS/PCF 상위 label이다.

CQ 유형은 다음과 같이 나눈다.

| CQ type | 예시 |
|---|---|
| Task decomposition | 제안서 기획은 어떤 하위 업무로 구성되는가? |
| Precedence | Bid/No Bid Decision은 어느 업무 전후에 위치하는가? |
| Input-output | Capture Plan은 어떤 업무의 산출물이며 어떤 업무의 입력인가? |
| Role responsibility | 제안 PM은 어떤 업무를 책임지는가? |
| Decision/gateway | 입찰타당성 결정은 어떤 조건에서 수행되는가? |
| Principle | 제안서 리뷰에서 지켜야 할 원칙은 무엇인가? |
| Artifact transformation | 고객 정보는 어떤 분석을 거쳐 제안전략으로 변환되는가? |
| Standard alignment | 이 업무는 어떤 NCS 능력단위 또는 PCF process와 관련되는가? |
| Negative/guard | 어떤 경우에 제안 참여를 중단해야 하는가? |

초기 목표는 80~120개 CQ를 생성하고, domain expert가 40~60개를 core CQ로 승인한다.

### 5.3 Ontology-to-tool constrained extraction

스키마를 단순 문서로만 두지 않고, LLM 호출 시 사용할 tool interface로 변환한다.

예시 tool schema:

```json
{
  "tool_name": "add_procedural_relation",
  "arguments": {
    "subject_id": "string",
    "predicate": {
      "enum": ["PRECEDES", "USES_INPUT", "PRODUCES", "HAS_DECISION_GATEWAY", "PERFORMED_BY"]
    },
    "object_id": "string",
    "modality": {"enum": ["must", "should", "may", "example"]},
    "condition_id": "string|null",
    "evidence_anchor_ids": {"type": "array", "minItems": 1},
    "confidence": {"type": "number", "minimum": 0, "maximum": 1}
  }
}
```

LLM은 이 tool schema에 없는 relation이나 type을 생성할 수 없다. 새로운 개념이 필요하면 `propose_new_schema_term` tool을 호출하고, 해당 term은 바로 그래프에 들어가지 않고 review queue로 이동한다.

### 5.4 Anchor-first extraction

기존 방식은 chunk를 넣고 바로 triple을 뽑는다. 개선안은 반대로 한다.

```text
1. chunk에서 의미 anchor 후보 추출
2. anchor를 entity/relation/action/modality/condition/artifact 후보로 분류
3. anchor 간 가능한 relation 후보 생성
4. tool schema로 constrained extraction
5. 모든 slot과 triple element가 anchor에 연결되는지 복원 검증
```

Anchor type은 다음과 같다.

| Anchor type | 예시 |
|---|---|
| TaskActionAnchor | 분석한다, 수립한다, 작성한다, 검토한다 |
| ArtifactAnchor | Capture Plan, 제안서, PMP |
| RoleAnchor | 제안 PM, 영업대표, 리뷰팀 |
| DecisionAnchor | Bid/No Bid Decision, 입찰타당성 결정 |
| ConditionAnchor | 고객 요구가 불명확한 경우, 경쟁우위가 없을 때 |
| PrincipleAnchor | 고객 중심, 일관성, 충실도 |
| MetricAnchor | 일정, 비용, 승률, 리스크 |

### 5.5 Procedural ontology schema

Layer2는 다음 핵심 class를 사용한다.

| Class | 설명 |
|---|---|
| `DomainTask` | 수주·제안의 중심 업무 |
| `ProcedureStep` | 수행 순서를 갖는 구체 단계 |
| `DecisionGateway` | 업무 흐름이 분기되는 의사결정 지점 |
| `GuardCondition` | decision 또는 task 수행 조건 |
| `Artifact` | 산출물, 입력자료, 문서, 도구 |
| `Role` | 수행자, 책임자, 참여자 |
| `Principle` | 업무 수행 원칙 |
| `ReviewEvent` | 리뷰 활동과 그 목적 |
| `Risk` | 업무 리스크 |
| `EvidenceAnchor` | 원문 근거 단위 |
| `StandardAnchor` | NCS/PCF weak anchor |
| `ExtractionActivity` | LLM/규칙/사람 검수 활동 |

핵심 relation은 다음과 같다.

```text
HAS_SUBTASK
PRECEDES
USES_INPUT
PRODUCES
PERFORMED_BY
RESPONSIBLE_FOR
HAS_DECISION_GATEWAY
HAS_GUARD_CONDITION
BRANCHES_TO
HAS_REVIEW
HAS_PRINCIPLE
HAS_RISK
TRANSFORMS_INTO
EVIDENCED_BY
ANCHOR_OF
ALIAS_OF
CANDIDATE_ALIGNS_WITH
REQUIRES_CAPABILITY
PROCESS_CONTEXT
CONFLICTS_WITH
```

### 5.6 Standard-triangulated extraction

NCS/PCF는 다음 세 방식으로 활용한다.

1. **Reference layer:** 기존 발표안처럼 Layer1 그래프를 구성한다.
2. **Weak standard anchor:** Layer2 task 후보가 NCS/PCF label/definition과 약하게 연결될 경우 standard hint로 저장한다.
3. **Mapping consistency check:** Layer2 task가 NCS와 PCF 양쪽에서 전혀 후보를 찾지 못하거나, 너무 동떨어진 표준과 연결되면 검토 대상으로 올린다.

중요한 점은, 표준 anchor는 원문 evidence를 대체하지 않는다. Layer2 업무 지식의 1차 근거는 자이제 문서이고, NCS/PCF는 보조적 해석과 매핑 검증에 사용된다.

---

## 6. Baseline 및 Ablation 설계

### 6.1 Baselines

| ID | 방법 | 설명 |
|---|---|---|
| B0 | Presentation baseline | 기존 발표안: Task Frame LLM + Triple LLM + 후처리 |
| B1 | Plain LLM triple extraction | 스키마 없이 자유 triple 추출 |
| B2 | Predicate-constrained extraction | predicate 목록만 제한 |
| B3 | Ontology-guided extraction | entity/relation/domain/range schema 제공 |
| B4 | Ontology-guided + few-shot | 검수 예시 20개를 in-context examples로 제공 |

### 6.2 Proposed method and ablations

| ID | 방법 | 목적 |
|---|---|---|
| P | Full CEP-Onto | 전체 제안 방법 |
| P-1 | w/o CQ loop | CQ 폐루프의 효과 제거 |
| P-2 | w/o anchor verification | anchor-first 및 restoration verification 제거 |
| P-3 | w/o tool constraint | tool-constrained generation 제거, prompt-only schema로 대체 |
| P-4 | w/o procedural schema | ProcedureGateway/GuardCondition 제거, flat triple로 대체 |
| P-5 | w/o standard triangulation | NCS/PCF weak anchor 제거 |
| P-6 | random review | active review 대신 무작위 검수 |

---

## 7. Gold Standard 구축 계획

### 7.1 Annotation unit

기본 annotation unit은 chunk이며, evidence는 sentence/character span 단위로 표시한다.

Gold annotation 항목:

- DomainTask
- Subtask/ProcedureStep
- Role
- Artifact
- DecisionGateway
- GuardCondition
- Principle
- Risk
- Relation
- EvidenceAnchor span
- Alias/canonical label
- Unsupported or example-only 여부

### 7.2 샘플링 전략

자이제 문서는 chapter별 업무 성격이 다르므로, random split만 쓰면 특정 업무가 누락될 수 있다. 따라서 stratified chapter sampling을 사용한다.

| 집합 | 비율 | 용도 |
|---|---:|---|
| Pilot annotation | 5% chunks | annotation guideline 정교화 |
| Development | 15% chunks | prompt/tool/schema tuning |
| Blind test | 20% chunks | 최종 성능평가 |
| Unlabeled pool | 60% chunks | active extraction 및 ontology population |

Blind test는 실험 종료 전까지 prompt 개선과 example selection에 사용하지 않는다.

### 7.3 Annotator 구성

- 최소 2인의 annotator가 동일 subset을 독립 라벨링한다.
- 불일치 항목은 adjudication으로 gold를 확정한다.
- inter-annotator agreement는 entity type, relation type, evidence span, procedural relation별로 별도 보고한다.

---

## 8. 평가 지표

### 8.1 Extraction quality

| 지표 | 설명 |
|---|---|
| Entity Precision / Recall / F1 | canonical entity 기준 |
| Relation Precision / Recall / F1 | relation type 기준 |
| Exact Triple F1 | subject-predicate-object 완전 일치 |
| Relaxed Triple F1 | alias/canonical normalization 반영 |
| Slot F1 | Task Frame slot별 F1 |

### 8.2 Grounding and hallucination

| 지표 | 설명 |
|---|---|
| Element grounding rate | subject, predicate, object 각각 anchor가 있는 비율 |
| Evidence restoration success | 추출 요소가 원문 span으로 복원되는 비율 |
| Unsupported triple rate | 근거 없는 triple 비율 |
| Evidence mismatch rate | evidence span이 실제 주장과 맞지 않는 비율 |
| Inference-only ratio | 원문 직접근거가 아니라 추론으로만 생성된 항목 비율 |

### 8.3 Ontology conformance

| 지표 | 설명 |
|---|---|
| SHACL violation rate | shape 위반 triple/노드 비율 |
| Domain/range violation | relation별 domain/range 위반 |
| Required property completeness | 필수 속성 누락률 |
| Unknown predicate rate | 허용되지 않은 relation 발생률 |
| Duplicate canonical entity rate | canonicalization 실패율 |

### 8.4 Procedural consistency

| 지표 | 설명 |
|---|---|
| Precedence F1 | 업무 선후행 relation 정확도 |
| Gateway F1 | DecisionGateway 추출 정확도 |
| Guard condition F1 | 조건/분기 조건 추출 정확도 |
| Artifact flow F1 | 산출물 → 후속 업무 입력 연결 정확도 |
| Cycle violation count | 순환 선후행 오류 수 |
| Orphan procedure step rate | 상위 task나 evidence 없는 step 비율 |

### 8.5 CQ answerability

| 지표 | 설명 |
|---|---|
| CQ answerability | graph query로 답 가능한 CQ 비율 |
| CQ answer accuracy | 사람이 평가한 답변 정확도 |
| CQ evidence support | 답변에 연결된 evidence가 충분한 비율 |
| Query path length | 답변에 필요한 평균 graph hop 수 |
| Unanswered CQ category | 어떤 유형의 CQ가 실패하는지 분포 |

### 8.6 Human review efficiency

| 지표 | 설명 |
|---|---|
| Accepted correct triples per expert-minute | 검수 시간 대비 정답 triple 수 |
| Error found per expert-minute | 검수 시간 대비 오류 발견 수 |
| Review reduction rate | random review 대비 필요한 검수량 감소 |
| High-impact correction rate | 중심 노드/핵심 CQ에 영향을 준 수정 비율 |

### 8.7 Layer1/Layer2 mapping evaluation

| 지표 | 설명 |
|---|---|
| Precision@k | Top-k 매핑 후보 중 적절한 후보 비율 |
| MRR | 첫 적절 후보의 평균 역순위 |
| nDCG@k | relevance grade를 반영한 ranking 품질 |
| Mapping explanation adequacy | 사람이 평가한 mapping reason 충분성 |
| Bridge support accuracy | Layer2 bridge가 실제로 표준 간 대응 근거가 되는 비율 |

---

## 9. 실험별 세부 계획

### Experiment 1. OCR chunking strategy 비교

**목적:** sentence-window, section-based, hybrid semantic chunking 중 어떤 방식이 업무 온톨로지 추출에 가장 적합한지 확인한다.

**조건:**

- C1: sentence-window chunk
- C2: section-based chunk
- C3: hybrid semantic chunk

**평가:**

- entity/relation F1
- evidence restoration success
- CQ answerability
- unsupported triple rate
- average tokens per chunk
- expert review time per accepted triple

**예상:** hybrid semantic chunking이 문맥과 근거 정밀도의 균형이 가장 좋을 가능성이 높다.

### Experiment 2. Extraction method 비교

**목적:** 기존 발표안 대비 CEP-Onto가 extraction quality와 ontology conformance를 높이는지 검증한다.

**조건:**

- B0 Presentation baseline
- B1 Plain LLM triple extraction
- B2 Predicate-constrained extraction
- B3 Ontology-guided extraction
- B4 Ontology-guided + few-shot
- P Full CEP-Onto

**평가:**

- exact/relaxed triple F1
- slot F1
- SHACL violation rate
- unsupported triple rate
- evidence mismatch rate

### Experiment 3. CQ-driven closed loop 효과

**목적:** CQ를 구축 루프에 넣는 것이 graph coverage와 answerability를 개선하는지 검증한다.

**조건:**

- P-1: no CQ loop
- P: full CQ loop

**절차:**

1. core CQ 40~60개 확정
2. 1차 그래프 생성
3. CQ answerability test 실행
4. 실패한 CQ를 유형별로 분류
5. 관련 chunk 재검색 및 추가 extraction
6. 2~3회 반복

**평가:**

- iteration별 CQ answerability 증가율
- 새로 추가된 correct triple 수
- 반복에 따른 hallucination 증가 여부
- unanswered CQ 유형 변화

### Experiment 4. Anchor verification 효과

**목적:** character-level anchor와 restoration verification이 hallucination을 줄이는지 검증한다.

**조건:**

- chunk-level evidence only
- sentence-level evidence
- character-span anchor + restoration verification

**평가:**

- unsupported triple rate
- evidence mismatch rate
- element grounding rate
- annotator verification time

### Experiment 5. Procedural schema 효과

**목적:** flat triple graph와 procedural ontology graph의 차이를 검증한다.

**조건:**

- flat task-triple graph
- task-triple + artifact flow
- full procedural ontology with decision gateway and guard condition

**평가:**

- precedence F1
- gateway F1
- guard condition F1
- artifact flow F1
- cycle violation count
- process query answerability

**대표 process CQ:**

```text
제안참여 의사결정 이후 제안서 기획으로 넘어가기 위해 필요한 산출물과 조건은 무엇인가?
Capture Plan은 어떤 업무에서 만들어지고 어떤 후속 업무에 입력으로 쓰이는가?
제안서 리뷰는 어떤 단계에서 어떤 목적으로 수행되는가?
```

### Experiment 6. Active expert review 효과

**목적:** active review가 random review 대비 검수 효율을 개선하는지 확인한다.

**조건:**

- random sampling
- confidence-based sampling
- uncertainty + centrality + conflict sampling
- full active review priority score

**평가:**

- accepted correct triples per expert-minute
- error found per expert-minute
- final graph F1 after fixed review budget
- CQ answerability after fixed review budget

### Experiment 7. Standard triangulation 효과

**목적:** NCS/PCF weak standard anchor가 Layer2 task 정규화와 mapping quality에 기여하는지 검증한다.

**조건:**

- L2→NCS/PCF post-hoc mapping only
- weak standard anchor during canonicalization
- weak standard anchor + mapping consistency check

**평가:**

- Precision@5
- MRR
- nDCG@10
- mapping explanation adequacy
- noMatch false positive rate

---

## 10. 통계 분석 계획

### 10.1 반복 실행

LLM 출력 변동을 고려해 각 extraction condition은 최소 3회 반복 실행한다.

- temperature: 0 또는 0.1을 기본값으로 고정
- 동일 prompt, 동일 chunk, 동일 model version 기록
- output hash와 manifest 저장

### 10.2 유의성 검정

| 비교 | 권장 검정 |
|---|---|
| relation F1 paired comparison | paired bootstrap confidence interval |
| CQ answerability 비율 차이 | McNemar test 또는 bootstrap |
| review efficiency | Wilcoxon signed-rank test |
| ranking metric | paired randomization test |

### 10.3 Effect size

p-value만 보고하지 않고 다음 효과크기를 함께 보고한다.

- F1 absolute improvement
- hallucination rate reduction
- SHACL violation reduction
- expert time reduction percentage
- CQ answerability gain

---

## 11. 산출물 설계

### 11.1 전처리 산출물

```text
00_data_manifest.csv
01_clean_ncs_classes.jsonl
02_clean_ncs_competency_units.jsonl
03_clean_pcf_elements.jsonl
04_clean_pcf_metrics.jsonl
05_ocr_clean_sentences.jsonl
06_document_structure.json
07_evidence_anchors.jsonl
08_chunks_sentence_window.jsonl
09_chunks_section_based.jsonl
10_chunks_hybrid_semantic.jsonl
```

### 11.2 CQ 및 스키마 산출물

```text
11_cq_candidates_raw.jsonl
12_cq_core_reviewed.jsonl
13_cq_to_sparql_templates.jsonl
14_ontology_tbox.ttl
15_ontology_shapes.shacl.ttl
16_tool_schemas.json
17_predicate_registry.json
```

### 11.3 Layer1 산출물

```text
18_layer1_ncs_nodes.jsonl
19_layer1_ncs_edges.jsonl
20_layer1_pcf_nodes.jsonl
21_layer1_pcf_edges.jsonl
22_layer1_pcf_metric_edges.jsonl
23_layer1_quality_report.md
```

### 11.4 Layer2 산출물

```text
24_anchor_candidates.jsonl
25_task_frames_raw.jsonl
26_task_frames_verified.jsonl
27_procedural_relations_raw.jsonl
28_procedural_relations_verified.jsonl
29_layer2_nodes.jsonl
30_layer2_edges.jsonl
31_layer2_evidence_index.jsonl
32_alias_dictionary.json
33_conflict_review_queue.jsonl
34_unsupported_candidates.jsonl
```

### 11.5 실험 산출물

```text
35_gold_annotations.jsonl
36_experiment_config.yaml
37_experiment_results.csv
38_ablation_results.csv
39_cq_answerability_report.md
40_hallucination_audit_report.md
41_human_review_efficiency_report.md
42_mapping_evaluation_report.md
43_final_ontology_build_report.md
```

---

## 12. 논문 방법론 구성안

```text
3. Methodology

3.1 Research Design
- Design science research
- Evidence-first procedural ontology construction
- Hybrid structured standards + unstructured OCR corpus

3.2 Data Sources and Preprocessing
- NCS current-use filtering
- PCF hierarchy reconstruction
- OCR cleaning and evidence anchor generation
- Document structure reconstruction

3.3 Related Work-Derived Design Requirements
- Ontology engineering requirements
- Ontology-guided extraction requirements
- Grounded extraction requirements
- CQ-based evaluation requirements

3.4 CEP-Onto Framework
- CQ generation
- Ontology-to-tool constraint generation
- Anchor-first extraction
- Procedural ontology modeling
- Grounding verification
- Active expert review
- Standard triangulation

3.5 Ontology Schema
- Layer1 standard reference ontology
- Layer2 procedural domain ontology
- Evidence and provenance model

3.6 Experimental Setup
- Gold annotation protocol
- Baselines and ablations
- Metrics
- Statistical tests

3.7 Results
- Extraction quality
- Grounding/hallucination
- Ontology conformance
- Procedural consistency
- CQ answerability
- Expert review efficiency
- Standard mapping quality

3.8 Discussion
- Novelty and implications
- Error analysis
- Limitations
- Extension to Agent Harness
```

---

## 13. 예상 논문 기여문

본 연구는 다음과 같이 contribution을 주장할 수 있다.

1. **Methodological contribution**  
   비정형 한국어 업무 문서와 구조화된 표준 직무/프로세스 데이터를 결합하여 업무 온톨로지를 구축하는 CQ-driven, evidence-first, tool-constrained 방법론을 제안한다.

2. **Modeling contribution**  
   수주·제안 업무를 단순 triple이 아니라 Task, ProcedureStep, DecisionGateway, GuardCondition, ArtifactFlow로 표현하는 procedural ontology schema를 제안한다.

3. **Evaluation contribution**  
   ontology conformance, hallucination, evidence grounding, CQ answerability, procedural consistency, human review efficiency를 함께 측정하는 평가 체계를 제안한다.

4. **Practical contribution**  
   NCS/PCF 표준 기준축과 도메인 업무 그래프를 느슨하게 연결하면서도, 표준 지식을 extraction/canonicalization/mapping quality control에 활용하는 재현 가능한 파이프라인을 제시한다.

---

## 14. 리스크와 대응 방안

| 리스크 | 영향 | 대응 |
|---|---|---|
| OCR 오류 | 잘못된 evidence anchor | OCR risk score와 human correction queue 운영 |
| 업무명 alias 폭증 | canonicalization 실패 | 색인, 약어 사전, NCS/PCF label, 전문가 검수 반영 |
| LLM hallucination | unsupported triple 증가 | anchor-first, restoration verification, SHACL/tool constraint 적용 |
| CQ가 너무 추상적 | 평가 불가능 | CQ를 graph query 가능 형태로 정규화 |
| 절차 relation 주관성 | annotator disagreement | precedence/condition annotation guideline 구체화 |
| NCS/PCF domain mismatch | 무리한 mapping | exactMatch보다 relatedTo/requiresCapability/processContext 중심으로 평가 |
| 검수 비용 증가 | 일정 지연 | active review로 고위험/고중심 항목 우선 검수 |

---

## 15. 실행 일정

| 기간 | 작업 | 산출물 |
|---|---|---|
| Week 1 | 데이터 manifest, NCS/PCF/OCR 프로파일링 | manifest, quality report |
| Week 2 | OCR cleaning, document structure, evidence anchor 생성 | clean sentences, chunks, anchors |
| Week 3 | CQ 후보 생성 및 core CQ 검수 | CQ catalog |
| Week 4 | TBox/SHACL/tool schema 설계 | ontology schema, tool schemas |
| Week 5 | Layer1 NCS/PCF 그래프 구축 | Layer1 nodes/edges |
| Week 6 | Pilot annotation 및 guideline 확정 | pilot gold, guideline |
| Week 7 | Baseline B0~B4 실행 | baseline outputs |
| Week 8 | CEP-Onto full 및 ablation 실행 | proposed outputs |
| Week 9 | Active review 실험 | review logs |
| Week 10 | Mapping 및 standard triangulation 실험 | mapping candidates, mapping eval |
| Week 11 | 통계 분석 및 error analysis | result tables |
| Week 12 | 논문 방법론/실험 장 초안 작성 | manuscript draft |

---

## 16. 최종 선택 권고

가장 논문성이 높은 최종 방법론은 다음이다.

```text
CEP-Onto =
  NCS/PCF deterministic Layer1
+ OCR evidence-anchor preprocessing
+ RAG-based CQ generation
+ SHACL/JSON Schema-derived tool-constrained extraction
+ anchor-first Task/Procedure/Triple extraction
+ restoration verification
+ CQ answerability loop
+ active expert review
+ standard-triangulated mapping quality control
```

이 방법론은 기존 발표안의 안정적인 레이어 구조를 유지하면서도, 다음 점에서 명확한 novelty를 가진다.

- 기존의 one-shot extraction이 아니라 CQ 기반 폐루프다.
- chunk evidence가 아니라 element-level evidence anchor를 사용한다.
- 사후 검증이 아니라 생성 시점 constraint enforcement를 시도한다.
- 수주·제안 업무의 절차성과 의사결정 구조를 formal schema로 표현한다.
- 사람 검수를 단순 review sheet가 아니라 active review 실험으로 평가한다.
- NCS/PCF를 단순 사후 매핑 대상이 아니라 표준 triangulation 장치로 사용한다.

따라서 본 연구는 단순한 “LLM 기반 업무 온톨로지 구축 사례”가 아니라, **표준 기준축과 OCR 문헌을 결합한 evidence-first procedural ontology construction 방법론**으로 포지셔닝하는 것이 가장 적절하다.

---

## 참고 연구 및 표준

- Noy & McGuinness, *Ontology Development 101: A Guide to Creating Your First Ontology*, Stanford KSL Technical Report, 2001.
- Fernández-López et al., *METHONTOLOGY: From Ontological Art Towards Ontological Engineering*, 1997.
- Gómez-Pérez et al., *NeOn Methodology for Building Ontology Networks*, 2009.
- Mihindukulasooriya et al., *Text2KGBench: A Benchmark for Ontology-Driven Knowledge Graph Generation from Text*, ISWC 2023.
- van Cauter & Yakovets, *Ontology-guided Knowledge Graph Construction from Maintenance Short Texts*, KaLLM 2024.
- Alharbi et al., *A RAG Approach for Generating Competency Questions in Ontology Engineering*, 2024.
- Yang et al., *Grounded Knowledge Graph Extraction via LLMs: An Anchor-Constrained Framework with Provenance Tracking*, 2026.
- Khorshidi et al., *ODKE+: Ontology-Guided Open-Domain Knowledge Extraction with LLMs*, 2025.
- Zhou et al., *Ontology-to-tools compilation for executable semantic constraint enforcement in LLM agents*, 2026.
- W3C, *RDF 1.1 Concepts and Abstract Syntax*, 2014.
- W3C, *OWL 2 Web Ontology Language Primer*, 2012.
- W3C, *Shapes Constraint Language SHACL*, 2017.
- W3C, *PROV-O: The PROV Ontology*, 2013.
- NCS 공식 사이트, *국가직무능력표준 개념 설명*.
- APQC, *Process Classification Framework PCF*.
