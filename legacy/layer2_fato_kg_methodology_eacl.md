# Layer2 업무 온톨로지/KG 구축 방법론  
## Frame-Anchored Task Ontology KG, FATO-KG

- 작성일: 2026-07-03
- 대상 데이터: `자이제_1.xlsx`의 `clean_sentences` 시트와 입력된 전체 방향 문서
- 목적: **수주·제안 도메인 Layer2 KG**를 우선 구축하되, 향후 법률·계약·컴플라이언스·영업·PM 등 유사 업무 에이전트로 확장 가능한 **범용 업무 온톨로지 방법론**으로 정리
- 연구 지향점: EACL 제출을 염두에 둔 **독창적 KG 구축 방법론**, 평가셋, 실험 설계, 논문 기여점 포함

---

## 0. 한 줄 요약

> **Layer1은 표준 분류 인덱스로 얇게 유지하고, Layer2는 “Task Frame을 먼저 만들고 Triple을 나중에 귀속시키는” 방식으로 깊게 구축한다.**  
> 이때 모든 triple은 원문 evidence와 Task Frame에 연결되며, NCS·PCF 같은 표준체계와는 노드를 병합하지 않고 `MAPS_TO`류의 느슨한 mapping edge로 연결한다.

본 문서에서는 이 접근을 **FATO-KG, Frame-Anchored Task Ontology KG**라고 부른다.

---

## 1. 현재 입력 방향의 핵심 재정의

입력된 전체 방향은 다음 원칙으로 요약된다.

```text
Layer1: NCS/PCF 등 표준 Reference Layer
- LLM 사용 최소화 또는 미사용
- 공식 구조를 계층 그래프로 보존
- 정의문은 1차적으로 속성으로 저장

Layer2: 실제 업무 수행 Ontology/KG
- Task Frame LLM 1종
- Triple LLM 1종
- Triple은 반드시 Task Frame에 귀속
- 업무 수행·계획·점검·설명에 쓸 수 있도록 깊게 구축

Layer2 → Layer1 Mapping
- Layer2 Task와 Layer1 능력단위/프로세스 표준 노드를 병합하지 않음
- 별도 mapping edge로 느슨하게 연결
```

핵심 설계 원칙은 다음이다.

```text
Layer1은 얇게,
Layer2는 깊게,
연결은 느슨하게.
```

이 원칙은 수주 에이전트뿐 아니라 법률 에이전트, 계약 검토 에이전트, 컴플라이언스 에이전트, PM 에이전트에도 동일하게 적용 가능하다.  
표준 분류체계는 안정적 기준축이고, 실제 에이전트가 수행하는 업무 지식은 Layer2에 담아야 하기 때문이다.

---

## 2. 입력 데이터 프로파일

`자이제_1.xlsx`는 `clean_sentences` 단일 시트로 구성되어 있으며, 확인된 컬럼은 다음과 같다.

| 컬럼 | 의미 |
|---|---|
| `page` | OCR 원문 페이지 |
| `chapter_no` | 장 번호 |
| `chapter_title` | 장 제목 |
| `section_no` | 절/소절 번호 |
| `section_title` | 절/소절 제목 |
| `text_for_llm_human` | LLM 입력과 사람이 함께 검토할 수 있는 정제 문장 |

확인된 데이터 규모는 다음과 같다.

| 항목 | 값 |
|---|---:|
| 유효 문장 행 | 1,366 |
| 장 수 | 3 |
| 절/소절 수 | 51 |
| 페이지 범위 | 19–178 |
| 구조 메타데이터 누락 문장 | 3 |

장별 구성은 다음과 같다.

| 장 | 제목 | 문장 행 | 절/소절 수 | 페이지 범위 |
|---:|---|---:|---:|---|
| 1 | 입찰과 제안 | 310 | 18 | 19–56 |
| 2 | 수주영업 | 486 | 18 | 57–118 |
| 3 | 제안서 전략 | 567 | 15 | 119–178 |

Layer2 구축 관점에서 현재 데이터는 다음 세 범주의 업무 지식을 포함한다.

1. **수주·제안 프로세스 개요**
   - 입찰과 제안의 중요성
   - 제안 프로세스
   - 제안서 작성, 제안 기획, 프레젠테이션의 관계

2. **수주영업·고객·평가자 이해**
   - 수주영업은 단순 세일즈가 아니라 비즈니스 개발
   - 영업 정보 관리
   - 고객 니즈, 공식 요구조건, 비공식 요구조건
   - 의사결정자, 영향자, 기술전문가, 사용자, 행정가 등 평가자 관점
   - 고객 구매단계, 신뢰도, 커뮤니케이션 스타일

3. **제안서 전략·경쟁·리스크 관리**
   - 전략은 고객에서 출발
   - 경쟁사 분석과 차별화 요소 규명
   - 전략기술서 작성
   - 전술개발, 솔루션 최적화, 커뮤니케이션 방법 개발
   - 1등/2등 전략, 정공법/역공법
   - 리스크 관리

따라서 현재 데이터는 단순 명사형 entity extraction보다는 **업무 수행 절차, 판단 기준, 입력/출력 산출물, 역할, 리스크, 전략 원칙**을 중심으로 KG를 구축하는 것이 적합하다.

---

## 3. 연구 문제 정의

### 3.1 기존 KG 구축의 한계

일반적인 KG 구축은 다음과 같이 진행된다.

```text
문서 → entity extraction → relation extraction → triple graph
```

그러나 업무 에이전트용 KG에서는 이 방식만으로 부족하다.

예를 들어 다음 triple이 추출되었다고 하자.

```text
수주영업 - ANALYZES - 고객 니즈
수주영업 - PRODUCES - Capture Plan
Capture Plan - USED_AS_INPUT_FOR - 제안서 기획
```

이 triple들은 유용하지만, 에이전트가 실제로 업무를 수행하려면 다음 질문에도 답해야 한다.

- 이 업무는 어느 상위 프로세스에 속하는가?
- 선행 업무와 후행 업무는 무엇인가?
- 어떤 입력자료가 없으면 업무를 시작하면 안 되는가?
- 산출물의 품질 기준은 무엇인가?
- 어떤 역할이 수행하고 누가 승인하는가?
- 의사결정 지점은 어디인가?
- 어떤 리스크가 발생할 수 있고 어떻게 완화하는가?
- 이 지식은 원문 어디에 근거하는가?
- 수주 도메인을 벗어나 법률 도메인에서도 같은 구조를 쓸 수 있는가?

따라서 Layer2 KG는 단순 triple graph가 아니라 **Task Frame을 중심으로 한 procedural knowledge graph**가 되어야 한다.

---

## 4. 제안 방법: FATO-KG

### 4.1 방법론 이름

**FATO-KG: Frame-Anchored Task Ontology Knowledge Graph**

의미는 다음과 같다.

| 요소 | 의미 |
|---|---|
| `Frame` | 업무 하나를 설명하는 구조화된 슬롯 묶음 |
| `Anchored` | 모든 triple과 claim을 특정 Task Frame 및 원문 evidence에 귀속 |
| `Task Ontology` | 도메인이 바뀌어도 유지되는 업무 수행 중심 상위 온톨로지 |
| `KG` | Task, Role, Artifact, Condition, Risk, Evidence, Standard Mapping을 포함하는 실행형 지식 그래프 |

### 4.2 핵심 아이디어

FATO-KG는 다음 순서로 구축한다.

```text
1. 문서를 Evidence Unit으로 안정적으로 분할
2. 장/절 구조를 이용해 Task Frame 후보를 먼저 생성
3. Task Frame을 canonical catalog로 정규화
4. Triple LLM은 자유롭게 triple을 만들지 않고, Task Frame catalog에 귀속하면서 추출
5. 모든 triple은 evidence span, confidence, modality, scope를 포함
6. 후처리에서 ontology constraint, evidence faithfulness, alias canonicalization을 검증
7. Layer1 표준체계와는 mapping edge로만 연결
8. 실행 시에는 TaskFrame → TaskInstance, Artifact → ArtifactInstance로 인스턴스화
```

핵심 차별점은 다음이다.

| 기존 접근 | FATO-KG |
|---|---|
| entity와 triple을 먼저 추출 | Task Frame을 먼저 유도 |
| relation schema를 프롬프트에 길게 넣음 | Task별 관련 schema snippet만 검색해 제공 |
| triple이 문서 전체에 떠 있음 | 모든 triple이 `frame_task_id`에 귀속 |
| evidence가 약하거나 없음 | 모든 claim/triple이 EvidenceSpan에 연결 |
| 도메인마다 ontology를 새로 만듦 | 상위 Task Ontology는 재사용, 도메인별 extension만 추가 |
| KG 품질을 triple F1로만 평가 | triple F1 + ontology conformance + agent utility 평가 |

---

## 5. 선행연구 기반 설계 근거와 연구 공백

### 5.1 Relation extraction과 triple generation

REBEL은 relation extraction을 seq2seq 문제로 단순화하여 text에서 triplet sequence를 생성하는 접근을 보였다. 이는 LLM 기반 triple extraction의 선행적 흐름과 연결된다. 그러나 업무 문서에서는 triple 자체보다 **그 triple이 어떤 업무 맥락에 속하는지**가 중요하다.

### 5.2 Ontology-driven KG generation

Text2KGBench는 ontology가 주어졌을 때 자연어 문장에서 ontology의 class, relation, domain/range constraint를 준수하면서 fact를 추출하는 문제를 평가한다. 이 방향은 FATO-KG의 `ontology-constrained extraction`과 직접 연결된다. 다만 Text2KG류의 일반 benchmark는 주로 factual extraction에 초점이 있고, 업무 수행 절차·조건·의사결정·산출물 생애주기까지 평가하는 데는 한계가 있다.

### 5.3 Schema induction과 canonicalization

EDC, Extract-Define-Canonicalize는 open extraction 이후 schema definition과 canonicalization을 수행하여, 사전에 고정 schema가 없거나 schema가 너무 큰 상황에서도 KG를 만들 수 있게 한다. FATO-KG는 이 아이디어를 수용하되, schema를 entity 중심으로만 유도하지 않고 **Task Frame 단위의 업무 schema**로 유도한다.

### 5.4 Schema-guided multi-agent extraction

OneKE는 schema agent, extraction agent, reflection agent, configurable knowledge base를 사용하여 다양한 data format과 domain에 대응하는 schema-guided extraction 시스템을 제안한다. FATO-KG도 multi-stage pipeline을 사용하지만, 시스템적 agent 조합 자체보다 **Task Frame anchoring, evidence-bound procedural KG, cross-domain 업무 온톨로지 재사용**을 연구 기여점으로 삼는다.

### 5.5 Provenance와 validation

PROV-O는 provenance 정보를 표현·교환하기 위한 OWL2 ontology이며, SHACL은 RDF graph를 shape constraint로 검증하는 W3C 표준이다. FATO-KG에서는 이를 응용하여 다음을 강제한다.

- 모든 triple은 `EVIDENCED_BY`를 가져야 한다.
- every evidence span은 원문 위치와 extraction run을 가져야 한다.
- relation별 domain/range constraint를 검증한다.
- 업무 순서, 입력/출력, decision gate의 필수 슬롯을 검증한다.

### 5.6 Business process와 temporal ontology

BPMN은 업무 프로세스를 stakeholder가 이해할 수 있으면서도 실행 semantics로 번역 가능하도록 표현하는 표준 notation이다. APQC PCF는 조직의 핵심 프로세스를 계층적으로 정리한 process taxonomy이다. OWL-Time은 시간·순서·기간 표현을 위한 ontology이다.  
FATO-KG는 이 세 흐름에서 다음만 선택적으로 가져온다.

- BPMN: task, gateway, event, artifact 관점
- PCF: Layer1 표준 process reference
- OWL-Time: `PRECEDES`, `DURING`, `HAS_DURATION`, milestone 등 temporal relation 표현

단, Layer2는 BPMN diagram 자체가 아니다. Layer2는 에이전트가 질의·추론·실행점검에 사용할 수 있는 **property graph/RDF hybrid 업무 지식층**이다.

---

## 6. FATO-KG의 Ontology 설계

### 6.1 전체 구조

```text
FATO Core Ontology
├─ Work Structure
│  ├─ Domain
│  ├─ Process
│  ├─ TaskFrame
│  ├─ Task
│  ├─ Subtask
│  ├─ Step
│  └─ Gate
│
├─ Execution Context
│  ├─ Role
│  ├─ Agent
│  ├─ Stakeholder
│  ├─ Condition
│  ├─ Constraint
│  ├─ DecisionPoint
│  ├─ Risk
│  └─ EvaluationCriterion
│
├─ Artifact Layer
│  ├─ Artifact
│  ├─ InputArtifact
│  ├─ OutputArtifact
│  ├─ Template
│  ├─ Checklist
│  └─ ArtifactInstance
│
├─ Evidence Layer
│  ├─ SourceDocument
│  ├─ DocumentSection
│  ├─ Chunk
│  ├─ EvidenceSpan
│  └─ ExtractedClaim
│
├─ Runtime Layer
│  ├─ TaskInstance
│  ├─ AgentAction
│  ├─ ArtifactVersion
│  └─ ExecutionLog
│
└─ Mapping Layer
   ├─ StandardScheme
   ├─ StandardNode
   ├─ NCSCompetencyUnit
   ├─ PCFElement
   └─ MappingCandidate
```

### 6.2 Core class 정의

| Class | 설명 | 수주·제안 예시 | 법률 도메인 예시 |
|---|---|---|---|
| `Domain` | 업무 도메인 | 수주·제안 | 법률·계약 |
| `Process` | 여러 Task의 상위 흐름 | 제안 프로세스 | 계약 검토 프로세스 |
| `TaskFrame` | 업무를 설명하는 슬롯 구조 | 수주전략 수립 frame | 계약 리스크 검토 frame |
| `Task` | 실제 업무 단위 | 고객 니즈 분석 | 조항별 위험 분석 |
| `Step` | Task 내부 실행 단계 | 평가자 유형 분류 | 문제 조항 표시 |
| `Gate` | 진행 여부 판단 지점 | Bid/No Bid | 소송/합의 판단 |
| `Role` | 수행자·책임자 역할 | 영업대표, 제안PM | 변호사, 파트너 |
| `Stakeholder` | 영향을 받거나 평가하는 주체 | 고객, 평가자 | 의뢰인, 상대방 |
| `Artifact` | 산출물·입력물 | Capture Plan, 제안서 | 계약서, 법률의견서 |
| `Condition` | 업무 수행 조건 | RFP 수신, 예산 범위 확인 | 관할법, 계약유형 |
| `Constraint` | 지켜야 할 제약 | 평가 기준, 제출기한 | 법령, 판례, 계약상 의무 |
| `Risk` | 위험요소 | 경쟁사 우위, 가격 불리 | 손해배상, 해지권 |
| `Principle` | 일반 원칙 | 전략은 고객에서 출발 | 법령 우선 검토 |
| `EvaluationCriterion` | 평가 기준 | 기술점수, 가격점수 | 쟁점 중요도, 승소가능성 |
| `EvidenceSpan` | 원문 근거 | page/section/sentence | 법령 조문, 판례 문단 |
| `ExtractedClaim` | 추출된 지식 주장 | “수주영업은 고객 니즈를 분석한다” | “면책조항은 책임 범위를 제한한다” |
| `TaskInstance` | 특정 실행 건 | A사업 제안서 기획 | B계약 검토 건 |
| `ArtifactInstance` | 특정 산출물 버전 | A사업 제안서 v3 | B계약 수정본 v2 |
| `MappingCandidate` | 표준체계 연결 후보 | NCS 수주전략수립 | 법률 직무표준 또는 내부 taxonomy |

### 6.3 주요 relation 정의

| Relation | Domain → Range | 의미 |
|---|---|---|
| `HAS_TASK` | `Process → Task` | 프로세스가 task를 포함 |
| `HAS_SUBTASK` | `Task → Task` | task의 하위 task |
| `HAS_STEP` | `Task → Step` | task 내부 실행 단계 |
| `PRECEDES` | `Task/Step → Task/Step` | 선후행 관계 |
| `TRIGGERED_BY` | `Task → Event/Condition` | task를 시작시키는 조건 |
| `USES_INPUT` | `Task → Artifact/InformationItem` | task가 사용하는 입력 |
| `PRODUCES` | `Task → Artifact` | task의 산출물 |
| `PERFORMED_BY` | `Task → Role` | 수행 역할 |
| `ACCOUNTABLE_TO` | `Task → Role/Stakeholder` | 책임·승인 대상 |
| `ANALYZES` | `Task → Concept/Artifact/Stakeholder` | 분석 대상 |
| `DEVELOPS` | `Task → Artifact/Strategy/Concept` | 개발·수립 대상 |
| `EVALUATES` | `Task → EvaluationCriterion/Artifact` | 평가 대상 |
| `DECIDES` | `Task/Gate → DecisionPoint` | 의사결정 |
| `HAS_DECISION_POINT` | `Task → DecisionPoint` | task 내 decision point |
| `HAS_CONDITION` | `Task/Rule → Condition` | 조건 |
| `HAS_CONSTRAINT` | `Task/Artifact → Constraint` | 제약조건 |
| `HAS_RISK` | `Task/Artifact → Risk` | 관련 위험 |
| `MITIGATES` | `Task/Control → Risk` | 위험 완화 |
| `HAS_PRINCIPLE` | `Task → Principle` | 적용 원칙 |
| `EVIDENCED_BY` | `Claim/Triple/Node/Edge → EvidenceSpan` | 원문 근거 |
| `MENTIONED_IN` | `Entity → EvidenceSpan` | 언급 위치 |
| `INSTANCE_OF` | `TaskInstance → TaskFrame/Task` | 실행 인스턴스와 정의 연결 |
| `REALIZES` | `ArtifactInstance → Artifact` | 산출물 인스턴스와 산출물 유형 연결 |
| `MAPS_TO` | `Layer2 Node → Layer1 Node` | 표준체계 연결 |
| `REQUIRES_CAPABILITY` | `Task → NCSCompetencyUnit` | 수행에 필요한 역량 |
| `PROCESS_CONTEXT` | `Task → PCFElement` | 표준 프로세스 맥락 |

### 6.4 Relation vocabulary 통제 원칙

LLM에게 relation을 자유 생성하게 하면 ontology drift가 빠르게 발생한다. 따라서 relation은 세 단계로 관리한다.

```text
Level A: Core relation
- 모든 도메인에서 재사용
- HAS_TASK, HAS_SUBTASK, PRECEDES, USES_INPUT, PRODUCES, PERFORMED_BY, EVIDENCED_BY 등

Level B: Domain relation
- 수주·제안 도메인에서 자주 쓰임
- ANALYZES_EVALUATOR, DEVELOPS_WIN_STRATEGY처럼 처음에는 후보로 두고 Core relation으로 환원 가능하면 환원

Level C: Candidate relation
- LLM이 제안했지만 아직 승인되지 않음
- review queue로 이동
```

초기에는 relation을 과도하게 늘리지 않는다.  
대부분의 업무 지식은 다음 20개 안팎의 relation으로 충분히 표현 가능하다.

```text
HAS_TASK
HAS_SUBTASK
HAS_STEP
PRECEDES
TRIGGERED_BY
USES_INPUT
PRODUCES
PERFORMED_BY
ANALYZES
DEVELOPS
EVALUATES
DECIDES
HAS_DECISION_POINT
HAS_CONDITION
HAS_CONSTRAINT
HAS_RISK
MITIGATES
HAS_PRINCIPLE
MAY_RESULT_IN
EVIDENCED_BY
MAPS_TO
REQUIRES_CAPABILITY
PROCESS_CONTEXT
```

---

## 7. Task Frame 설계

### 7.1 Task Frame이 필요한 이유

Task Frame은 “업무 하나를 실제 수행 가능한 단위로 설명하는 슬롯 구조”다.  
Layer2 KG에서 Task Frame은 다음 역할을 한다.

1. triple이 어느 업무에 속하는지 결정하는 anchor
2. entity type을 별도 LLM으로 추출하지 않아도 되는 슬롯 구조
3. 업무 에이전트가 계획, 점검, 실행, 설명에 사용할 수 있는 template
4. 향후 법률·계약 도메인으로 확장할 때 재사용 가능한 상위 pattern

### 7.2 Task Frame 기본 스키마

```json
{
  "frame_id": "L2_TASK_CAPTURE_STRATEGY",
  "domain": "bid_proposal",
  "canonical_task_name": "수주전략 수립",
  "aliases": ["Capture Strategy", "Win Strategy", "수주 전략 개발"],
  "task_type": "StrategyDevelopmentTask",
  "definition": "고객 니즈, 경쟁사, 평가 기준, 자사 역량을 분석하여 사업 수주 가능성을 높이는 전략을 수립하는 업무",
  "parent_process": "제안 프로세스",
  "preconditions": [
    "사업 기회가 식별됨",
    "고객 요구 또는 RFP 정보가 존재함"
  ],
  "inputs": [
    {"name": "고객 니즈", "type": "InformationItem"},
    {"name": "경쟁사 정보", "type": "InformationItem"},
    {"name": "평가 기준", "type": "EvaluationCriterion"}
  ],
  "outputs": [
    {"name": "수주전략", "type": "StrategyArtifact"},
    {"name": "차별화 포인트", "type": "StrategyElement"}
  ],
  "roles": [
    {"name": "영업대표", "responsibility": "고객 정보 수집"},
    {"name": "제안PM", "responsibility": "전략 구조화"}
  ],
  "subtasks": [
    "고객 니즈 분석",
    "경쟁사 분석",
    "평가 기준 분석",
    "차별화 요소 도출"
  ],
  "decision_points": [
    "Bid/No Bid Decision",
    "1등 전략 또는 2등 전략 선택"
  ],
  "risks": [
    "고객 비공식 요구조건 미파악",
    "경쟁사 강점 과소평가"
  ],
  "success_criteria": [
    "고객 이슈와 제안전략이 연결됨",
    "경쟁자가 동일하게 주장하기 어려운 차별화 요소가 정의됨"
  ],
  "principles": [
    "전략은 고객에서 출발해야 한다",
    "차별화 요소는 경쟁자와 비교 가능해야 한다"
  ],
  "evidence_sections": [
    {"chapter": 3, "section_no": "3.1.3", "section_title": "전략은 고객에서 출발한다"},
    {"chapter": 3, "section_no": "3.1.4", "section_title": "경쟁사 분석을 통해 핵심 차별화요소를 규명하라"}
  ],
  "cross_domain_pattern": "StrategyDevelopment"
}
```

### 7.3 Task type taxonomy

수주·제안 도메인과 법률 도메인 모두에 재사용 가능한 task type은 다음과 같다.

| Task Type | 설명 | 수주·제안 예시 | 법률 예시 |
|---|---|---|---|
| `OpportunityAssessmentTask` | 기회·안건의 가치와 가능성 판단 | 사업 기회 분석 | 사건 수임 가능성 검토 |
| `InformationGatheringTask` | 필요한 정보 수집 | 영업 정보 관리 | 사실관계 수집 |
| `RequirementAnalysisTask` | 요구조건 분석 | RFP 요구조건 분석 | 계약 요구사항 분석 |
| `StakeholderAnalysisTask` | 이해관계자 분석 | 평가자 분석 | 의뢰인/상대방/재판부 분석 |
| `StrategyDevelopmentTask` | 전략 수립 | 수주전략 수립 | 소송전략 수립 |
| `RiskAssessmentTask` | 리스크 식별·평가 | 리스크 관리 | 법률 리스크 검토 |
| `ArtifactAuthoringTask` | 산출물 작성 | 제안서 작성 | 계약서/의견서 작성 |
| `ReviewTask` | 검토·품질관리 | 제안서 리뷰 | 파트너 리뷰 |
| `DecisionTask` | 판단·승인 | Bid/No Bid | 소송/합의 결정 |
| `CommunicationTask` | 전달·설득 | 프레젠테이션 | 의뢰인 보고 |
| `MappingTask` | 표준체계와 연결 | NCS/PCF 매핑 | 법률 taxonomy 매핑 |

---

## 8. 현재 수주·제안 데이터의 Seed Task Catalog

다음은 현재 데이터에서 바로 시작할 수 있는 Layer2 seed task catalog이다.  
초기 구축에서는 너무 세밀한 task를 모두 만들지 말고, **15–25개 canonical task**로 시작한 뒤 evidence가 누적되면 확장한다.

| Task ID | Canonical Task | Task Type | 주요 근거 섹션 |
|---|---|---|---|
| `L2_TASK_BID_CONTEXT_UNDERSTANDING` | 입찰·제안 환경 이해 | `OpportunityAssessmentTask` | 1.1, 1.1.1–1.1.4 |
| `L2_TASK_PROPOSAL_PROCESS_MANAGEMENT` | 제안 프로세스 관리 | `ProcessManagementTask` | 1.3, 1.3.1 |
| `L2_TASK_CAPTURE_PLANNING` | 수주영업 | `InformationGatheringTask` | 1.3.2, 2.1 |
| `L2_TASK_CAPTURE_INFORMATION_MANAGEMENT` | 영업 정보 관리 | `InformationGatheringTask` | 2.1.3, 2.2.1 |
| `L2_TASK_CUSTOMER_NEEDS_ANALYSIS` | 고객 니즈 분석 | `RequirementAnalysisTask` | 1.1.1, 2.4.4, 3.1.3 |
| `L2_TASK_UNSTATED_REQUIREMENT_DISCOVERY` | 비공식 요구조건 발굴 | `RequirementAnalysisTask` | 1.1.1 |
| `L2_TASK_VALUE_PROPOSITION` | 가치제안 개발 | `StrategyDevelopmentTask` | 2.2.2 |
| `L2_TASK_EVALUATOR_ANALYSIS` | 평가자 분석 | `StakeholderAnalysisTask` | 2.3.1–2.3.4 |
| `L2_TASK_PURCHASE_STAGE_DIAGNOSIS` | 고객 구매단계 진단 | `StakeholderAnalysisTask` | 2.4.1 |
| `L2_TASK_TRUST_BUILDING` | 신뢰도 관리 | `CommunicationTask` | 2.4.2 |
| `L2_TASK_PERSUASIVE_COMMUNICATION` | 설득 커뮤니케이션 설계 | `CommunicationTask` | 2.4.3–2.4.5 |
| `L2_TASK_PROPOSAL_STRATEGY_MANAGEMENT` | 제안전략 관리 | `StrategyDevelopmentTask` | 3.1 |
| `L2_TASK_CUSTOMER_ISSUE_ANALYSIS` | 고객 이슈 분석 | `RequirementAnalysisTask` | 3.1.3 |
| `L2_TASK_COMPETITOR_ANALYSIS` | 경쟁사 분석 | `StrategyDevelopmentTask` | 3.1.4 |
| `L2_TASK_DIFFERENTIATOR_IDENTIFICATION` | 차별화 요소 규명 | `StrategyDevelopmentTask` | 3.1.4 |
| `L2_TASK_STRATEGY_STATEMENT_WRITING` | 전략기술서 작성 | `ArtifactAuthoringTask` | 3.2.2 |
| `L2_TASK_TACTIC_DEVELOPMENT` | 전술개발 | `StrategyDevelopmentTask` | 3.2.3–3.2.4 |
| `L2_TASK_SOLUTION_OPTIMIZATION` | 솔루션 최적화 | `StrategyDevelopmentTask` | 3.2.4 |
| `L2_TASK_COMMUNICATION_METHOD_DEVELOPMENT` | 커뮤니케이션 방법 개발 | `CommunicationTask` | 3.2.4 |
| `L2_TASK_STRATEGY_VALIDATION` | 전략 효과성 검증 | `ReviewTask` | 3.2.3, 3.2.5 |
| `L2_TASK_POSITION_STRATEGY_SELECTION` | 1등·2등 전략 선택 | `DecisionTask` | 3.3.1 |
| `L2_TASK_DIRECT_INDIRECT_STRATEGY_SELECTION` | 정공법·역공법 선택 | `DecisionTask` | 3.3.2 |
| `L2_TASK_RISK_MANAGEMENT` | 리스크 관리 | `RiskAssessmentTask` | 3.3.3 |
| `L2_TASK_PROPOSAL_PLANNING` | 제안서 기획 | `ArtifactAuthoringTask` | 1.3.3 |
| `L2_TASK_PROPOSAL_WRITING_MILESTONE` | 제안서 작성 단계 관리 | `ArtifactAuthoringTask` | 1.3.4 |
| `L2_TASK_PRESENTATION_PREPARATION` | 프레젠테이션 준비 | `CommunicationTask` | 1.3.5 |

---

## 9. 구축 파이프라인

### 9.1 전체 파이프라인

```text
자이제_1.xlsx
  ↓
01. Evidence Unit 생성
  ↓
02. 문서 구조 기반 Chunk 생성
  ↓
03. Task Frame 후보 추출
  ↓
04. Task Frame canonicalization
  ↓
05. Task Catalog 확정
  ↓
06. Frame-anchored Triple 추출
  ↓
07. Evidence faithfulness 검증
  ↓
08. Ontology constraint 검증
  ↓
09. Node/Edge 병합 및 alias 정규화
  ↓
10. Layer2 KG 생성
  ↓
11. Layer2 → Layer1 mapping 후보 생성
  ↓
12. Human review 및 benchmark 구축
```

### 9.2 Step 1: Evidence Unit 생성

각 문장 행을 안정적인 Evidence Unit으로 만든다.

```json
{
  "evidence_id": "EV_ZAIZE_P021_S1_1_1_0007",
  "source_document_id": "DOC_ZAIZE_001",
  "page": 21,
  "chapter_no": 1,
  "chapter_title": "입찰과 제안",
  "section_no": "1.1.1",
  "section_title": "제안서를 잘 써야 입찰에 성공한다",
  "text": "고객의 니즈는 제안 요청서에 공개된 공식적인 요구조건뿐만 아니라 비공식적인 요구조건까지 포함한다.",
  "char_start": null,
  "char_end": null,
  "source_type": "ocr_clean_sentence"
}
```

중요한 원칙은 다음이다.

- evidence text는 요약하지 않는다.
- page, chapter, section 정보를 반드시 보존한다.
- 구조 메타데이터 누락 문장은 버리지 않고 `needs_context_imputation` 큐로 보낸다.
- 그림·표·예시 문장은 `evidence_modality`를 추가한다.

```text
evidence_modality:
- prose
- list
- figure_caption
- table
- example
- formula
```

### 9.3 Step 2: Chunk 생성

문장 단위로 바로 triple extraction을 하면 context가 부족하다.  
따라서 chunk는 다음 우선순위로 만든다.

```text
기본: section/subsection 단위
예외: section이 너무 길면 800–1,200 Korean characters 기준으로 sliding chunk
중첩: chunk는 EvidenceSpan 목록을 참조
```

Chunk schema:

```json
{
  "chunk_id": "CH_ZAIZE_3_1_4_002",
  "source_document_id": "DOC_ZAIZE_001",
  "chapter_no": 3,
  "section_no": "3.1.4",
  "section_title": "경쟁사 분석을 통해 핵심 차별화요소를 규명하라",
  "evidence_ids": [
    "EV_ZAIZE_P145_S3_1_4_001",
    "EV_ZAIZE_P145_S3_1_4_002"
  ],
  "chunk_text": "...",
  "chunk_type": "section_window"
}
```

### 9.4 Step 3: Task Frame 후보 추출

Task Frame LLM은 chunk마다 호출하지 않는다.  
처음에는 다음 두 수준에서만 실행한다.

```text
A. Chapter-level Task Frame extraction
B. Corpus-level Task Frame consolidation
```

입력에는 다음을 제공한다.

- chapter title
- section title list
- 각 section의 대표 문장 5–10개
- 이미 확정된 core task ontology
- 출력 스키마

Task Frame LLM prompt의 핵심 지시문은 다음과 같다.

```text
너는 업무 온톨로지 설계자다.
입력 문서에서 반복적으로 등장하고 실제 에이전트가 수행·점검할 수 있는 업무 단위를 식별하라.
단순 개념, 설명, 예시 회사명, 인물명은 Task로 만들지 마라.
각 Task는 입력, 산출물, 수행자, 판단 지점, 리스크, 원칙, 선후행 관계를 가질 수 있어야 한다.
수주·제안 도메인에 특화된 이름을 쓰되, cross_domain_pattern도 함께 부여하라.
```

### 9.5 Step 4: Task Frame canonicalization

후보 Task Frame은 다음 기준으로 병합한다.

| 병합 기준 | 설명 |
|---|---|
| 이름 유사도 | 수주전략 수립, Win Strategy 개발 등 |
| 정의 유사도 | 업무 목적과 수행 내용 |
| 입력/출력 유사도 | 사용하는 자료와 생성 산출물 |
| 선후행 위치 | 같은 process 위치인지 |
| evidence overlap | 같은 section에서 반복되는지 |
| cross-domain pattern | 같은 상위 업무 pattern인지 |

예시 alias 병합:

```json
{
  "canonical": "수주영업",
  "aliases": ["Capture Planning", "영업 정보 관리", "비즈니스 개발"],
  "note": "영업 정보 관리가 독립 task로 충분한 evidence를 가지면 하위 task로 분리"
}
```

```json
{
  "canonical": "제안서 기획",
  "aliases": ["Proposal Planning", "제안 기획", "제안관리계획 수립"],
  "note": "제안서 작성과 분리. 기획은 전략·구조·일정·역할분담 중심."
}
```

### 9.6 Step 5: Frame-anchored Triple 추출

Triple LLM은 section/chunk마다 실행한다.  
단, 자유 추출이 아니라 다음을 함께 제공한다.

- 현재 chunk text
- 관련 Task Frame Top-k
- relation vocabulary
- entity type list
- 금지 규칙
- evidence span id list

출력 schema:

```json
{
  "chunk_id": "CH_ZAIZE_3_1_4_002",
  "triples": [
    {
      "subject": "경쟁사 분석",
      "subject_type": "Task",
      "predicate": "PRODUCES",
      "object": "차별화 요소",
      "object_type": "StrategyElement",
      "frame_task_id": "L2_TASK_COMPETITOR_ANALYSIS",
      "evidence_ids": ["EV_ZAIZE_P145_S3_1_4_004"],
      "evidence_quote": "경쟁사 분석을 통해 핵심 차별화요소를 규명하라",
      "modality": "normative",
      "polarity": "positive",
      "scope": "domain_principle",
      "confidence": 0.91
    }
  ],
  "new_task_candidates": [
    {
      "task_name": "경쟁자의 강점 최소화",
      "reason": "리스크 관리 섹션에서 반복적으로 등장하는 전술적 업무 후보",
      "evidence_ids": ["EV_ZAIZE_P178_S3_3_3_003"]
    }
  ]
}
```

### 9.7 Step 6: Scope와 modality 분류

업무 문서에는 원칙, 예시, 일반 설명, 경고, 금지, 사례가 섞여 있다.  
따라서 triple마다 `scope`와 `modality`를 부여한다.

| 필드 | 값 | 의미 |
|---|---|---|
| `modality` | `descriptive` | 사실 설명 |
|  | `normative` | 해야 한다, 중요하다 등 지침 |
|  | `warning` | 위험·주의 |
|  | `example` | 사례 |
|  | `definition` | 정의 |
|  | `heuristic` | 경험칙 |
| `scope` | `domain_principle` | 도메인 일반 원칙 |
|  | `task_specific` | 특정 task에만 적용 |
|  | `example_only` | 사례로만 유지, 일반 지식으로 승격 금지 |
|  | `source_claim` | 저자의 주장, 검증 필요 |
|  | `mapping_hint` | 표준 mapping에 도움되는 보조 정보 |

이 필드가 있어야 “책의 예시”와 “업무 원칙”을 분리할 수 있다.

---

## 10. Hallucination 방지와 검증

### 10.1 Evidence faithfulness 검증

모든 triple은 evidence에 근거해야 한다.

검증 규칙:

```text
1. evidence_quote가 원문 evidence text에 부분 문자열로 존재하는가?
2. subject/object가 evidence에 명시되었거나 명확히 coreference 가능한가?
3. predicate가 evidence 문장의 의미와 일치하는가?
4. 예시 문장을 일반 원칙으로 승격하지 않았는가?
5. LLM이 문서에 없는 표준 용어를 추가하지 않았는가?
```

결과 상태:

```text
verified
needs_review
rejected_no_evidence
rejected_overgeneralized
rejected_wrong_direction
```

### 10.2 Ontology constraint 검증

초기에는 SHACL과 유사한 rule을 JSON으로 정의해도 충분하다.

```json
{
  "shape": "TaskProducesArtifactShape",
  "target_relation": "PRODUCES",
  "subject_allowed_types": ["Task", "Step"],
  "object_allowed_types": ["Artifact", "StrategyArtifact", "Checklist", "Report"],
  "required_edge_properties": ["evidence_ids", "frame_task_id", "confidence"],
  "min_confidence_for_auto_accept": 0.80
}
```

예시 검증:

| Triple | 결과 | 이유 |
|---|---|---|
| `수주영업 - PRODUCES - Capture Plan` | pass | Task → Artifact |
| `고객 니즈 - PRODUCES - 수주영업` | fail | 방향 오류 |
| `제안서 - PERFORMED_BY - 영업대표` | fail | Artifact는 수행자가 아님 |
| `리스크 관리 - MITIGATES - 경쟁사 강점` | needs_review | 경쟁사 강점이 Risk인지 StrategyFactor인지 검토 필요 |

### 10.3 Process consistency 검증

업무 KG에서는 순서 관계가 중요하다.

검증 항목:

```text
- PRECEDES cycle이 존재하는가?
- Task와 Subtask 사이에 모순된 parent가 있는가?
- 필수 입력이 없는 Task가 PRODUCES를 갖는가?
- Gate 이후 가능한 next_task가 정의되어 있는가?
- ReviewTask가 Artifact를 EVALUATES하지 않고 떠 있는가?
```

---

## 11. 최종 Layer2 그래프 예시

### 11.1 Property graph 예시

```cypher
(:Task {
  id: "L2_TASK_CAPTURE_INFORMATION_MANAGEMENT",
  name: "영업 정보 관리",
  task_type: "InformationGatheringTask",
  domain: "bid_proposal"
})
-[:USES_INPUT {
  evidence_ids: ["EV_ZAIZE_P070_S2_2_1_003"],
  confidence: 0.89
}]->
(:InformationItem {name: "고객 정보"})

(:Task {id: "L2_TASK_CAPTURE_INFORMATION_MANAGEMENT"})
-[:PRODUCES {
  evidence_ids: ["EV_ZAIZE_P071_S2_2_1_005"],
  confidence: 0.86
}]->
(:Artifact {name: "Capture Plan"})

(:Task {id: "L2_TASK_CAPTURE_INFORMATION_MANAGEMENT"})
-[:PRECEDES {
  evidence_ids: ["EV_ZAIZE_P050_S1_3_2_002"],
  confidence: 0.83
}]->
(:Task {id: "L2_TASK_PROPOSAL_PLANNING"})
```

### 11.2 RDF/Turtle 스타일 예시

```turtle
l2:L2_TASK_COMPETITOR_ANALYSIS a fato:Task ;
    rdfs:label "경쟁사 분석"@ko ;
    fato:taskType fato:StrategyDevelopmentTask ;
    fato:hasSubtask l2:L2_TASK_DIFFERENTIATOR_IDENTIFICATION ;
    fato:evidencedBy ev:EV_ZAIZE_P145_S3_1_4_004 .

l2:L2_TASK_COMPETITOR_ANALYSIS fato:produces l2:DIFFERENTIATOR .
l2:DIFFERENTIATOR a fato:StrategyElement ;
    rdfs:label "차별화 요소"@ko .
```

---

## 12. Layer2 → Layer1 Mapping

### 12.1 원칙

Layer2 Task와 Layer1 표준 노드는 병합하지 않는다.

```text
나쁜 방식:
수주전략 수립 = NCS 수주전략수립

좋은 방식:
수주전략 수립 -REQUIRES_CAPABILITY→ NCS 수주전략수립
수주전략 수립 -PROCESS_CONTEXT→ PCF 영업 제안서·견적서 개발·관리
```

### 12.2 Mapping edge type

| Edge | 의미 | 사용 예 |
|---|---|---|
| `EXACT_MATCH_CANDIDATE` | 거의 동일해 보이나 사람 검토 필요 | 드묾 |
| `BROAD_MATCH` | Layer1이 더 넓음 | NCS 사업기획 ↔ 고객 니즈 분석 |
| `RELATED_TO` | 의미 관련 | 리스크 관리 ↔ 사업 위험관리 |
| `REQUIRES_CAPABILITY` | 수행 역량 | 수주전략 수립 ↔ 수주전략수립 능력단위 |
| `PROCESS_CONTEXT` | 프로세스 위치 | 제안서 기획 ↔ PCF proposal process |
| `NO_MATCH` | 매핑하지 않음 | 억지 연결 방지 |

### 12.3 Mapping candidate scoring

```text
mapping_score =
  0.25 × task_name_similarity
+ 0.25 × task_definition_similarity
+ 0.15 × input_output_similarity
+ 0.15 × action_verb_similarity
+ 0.10 × hierarchy_context_similarity
+ 0.05 × graph_neighbor_support
+ 0.05 × level_compatibility
- domain_gap_penalty
```

`graph_neighbor_support`는 FATO-KG의 독자적 요소다.  
예를 들어 `수주전략 수립`이 `경쟁사 분석`, `고객 니즈 분석`, `평가 기준 분석`, `차별화 요소`와 강하게 연결되어 있고, 특정 NCS 능력단위 정의에도 같은 주변 개념이 있으면 mapping score를 올린다.

### 12.4 Mapping result schema

```json
{
  "mapping_id": "MAP_L2_TASK_CAPTURE_STRATEGY_NCS_2001050105_25v5",
  "source_layer": "Layer2",
  "source_id": "L2_TASK_CAPTURE_STRATEGY",
  "source_name": "수주전략 수립",
  "target_layer": "Layer1",
  "target_scheme": "NCS",
  "target_id": "2001050105_25v5",
  "target_name": "수주전략수립",
  "mapping_type": "REQUIRES_CAPABILITY",
  "score": 0.92,
  "evidence": {
    "layer2_evidence_ids": ["EV_ZAIZE_P050_S1_3_2_002"],
    "layer1_text_fields": ["COMPE_UNIT_NAME", "COMPE_UNIT_DEF"]
  },
  "reason": "Layer2 수주전략 수립은 고객 니즈와 경쟁사 정보를 분석하여 수주전략을 결정하는 업무이고, NCS 수주전략수립은 고객 요구, 경쟁사 분석, 제안 평가 우위 요소 도출과 의미가 강하게 연결된다.",
  "review_status": "needs_review"
}
```

---

## 13. 법률 에이전트로 확장할 때의 재사용 방식

FATO-KG의 핵심은 **업무 수행 ontology는 재사용하고, 도메인 개념만 extension으로 추가**하는 것이다.

### 13.1 Core ontology 재사용

| FATO Core | 수주·제안 도메인 | 법률 도메인 |
|---|---|---|
| `Task` | 수주전략 수립 | 계약 리스크 검토 |
| `InputArtifact` | RFP, 고객 정보 | 계약서, 사실관계 메모 |
| `OutputArtifact` | 제안서, 전략기술서 | 법률의견서, 수정계약서 |
| `Role` | 영업대표, 제안PM | 담당 변호사, 파트너 |
| `Stakeholder` | 고객, 평가자 | 의뢰인, 상대방, 법원 |
| `DecisionPoint` | Bid/No Bid | 소송/합의/수정요청 결정 |
| `Risk` | 경쟁사 우위, 가격 불리 | 손해배상, 해지, 규제 위반 |
| `Constraint` | 평가 기준, 제출기한 | 법령, 판례, 계약 조항 |
| `EvidenceSpan` | OCR 문장 | 법령 조문, 판례 문단 |
| `TaskInstance` | A사업 제안 건 | B계약 검토 건 |

### 13.2 법률 도메인 extension 예시

```text
LegalTask
├─ LegalIssueIdentification
├─ ContractClauseAnalysis
├─ LegalRiskAssessment
├─ PrecedentSearch
├─ StatuteInterpretation
├─ LegalOpinionDrafting
├─ PartnerReview
└─ ClientCommunication
```

법률 도메인에서도 triple extraction은 다음처럼 동일하게 작동한다.

```json
{
  "subject": "계약 리스크 검토",
  "predicate": "USES_INPUT",
  "object": "계약서 초안",
  "frame_task_id": "LEGAL_TASK_CONTRACT_RISK_REVIEW",
  "evidence_ids": ["EV_CONTRACT_001_CLAUSE_12"],
  "confidence": 0.94
}
```

즉 수주·제안 도메인의 `RFP 분석 → 제안전략 → 제안서 작성` 흐름은 법률 도메인의 `계약서 분석 → 법률 리스크 평가 → 의견서 작성` 흐름으로 같은 ontology pattern을 통해 확장된다.

---

## 14. EACL 제출용 연구 설계

### 14.1 가능한 논문 제목

1. **Frame-Anchored Task Ontology Induction for Agentic Knowledge Graph Construction**
2. **Beyond Triples: Evidence-Grounded Procedural Knowledge Graphs for Business Agents**
3. **FATO-KG: Task-Frame Anchored Knowledge Graph Construction from Procedural Domain Documents**
4. **From Manuals to Agentic Workflows: Evidence-Constrained Task Ontology Induction with LLMs**

### 14.2 핵심 연구 질문

```text
RQ1. Task Frame을 먼저 유도하고 triple을 귀속시키면 flat triple extraction보다 ontology conformance와 faithfulness가 향상되는가?

RQ2. FATO-KG는 수주·제안 도메인에서 구축한 core ontology를 법률 도메인으로 재사용할 때 annotation cost를 줄이는가?

RQ3. evidence-bound extraction과 validation rule은 hallucination 및 overgeneralization을 줄이는가?

RQ4. FATO-KG는 단순 KG 품질뿐 아니라 agent의 업무 계획, 점검, 설명 성능을 향상시키는가?
```

### 14.3 논문 기여점

EACL 논문으로 제시할 수 있는 기여는 다음 네 가지다.

#### Contribution 1: New task formulation

기존 KG construction을 `text → triples`로 보지 않고, 다음 문제로 재정의한다.

```text
Given procedural domain documents,
construct an evidence-grounded task ontology KG
that supports agent planning, checking, and explanation,
while remaining mappable to external standards without node merging.
```

#### Contribution 2: Method

**Task Frame-first, Triple-second** 방식의 FATO-KG pipeline을 제안한다.

```text
Task Frame induction
→ Frame canonicalization
→ Frame-anchored triple extraction
→ Evidence/ontology validation
→ Loose standard mapping
```

#### Contribution 3: Dataset

현재 `자이제_1.xlsx`를 기반으로 다음 benchmark를 만들 수 있다.

```text
Korean Bid-Proposal Procedural KG Benchmark
- OCR-cleaned evidence sentences
- Section-level chunks
- Gold Task Frames
- Gold frame-anchored triples
- Evidence span links
- Mapping candidates to NCS/PCF
```

향후 법률 문서 1종을 추가하면 cross-domain benchmark가 된다.

```text
Korean Agentic Work Ontology Benchmark
├─ Bid-Proposal split
└─ Legal-Contract split
```

#### Contribution 4: Evaluation

일반 triple F1뿐 아니라 다음을 함께 평가한다.

- ontology conformance
- evidence faithfulness
- task attribution accuracy
- hallucination rate
- process consistency
- downstream agent utility
- cross-domain schema reuse

### 14.4 Baseline

| Baseline | 설명 |
|---|---|
| `Flat Triple Prompting` | Task Frame 없이 chunk에서 triple만 추출 |
| `Ontology-only Prompting` | ontology schema만 주고 triple 추출 |
| `EDC-style Pipeline` | extract → define → canonicalize |
| `OneKE-style Schema Agent Pipeline` | schema-guided extraction + reflection |
| `FATO-KG w/o Evidence Validation` | ablation |
| `FATO-KG w/o Task Frame` | ablation |
| `FATO-KG Full` | 제안 방법 |

### 14.5 평가 지표

#### KG extraction metrics

| Metric | 설명 |
|---|---|
| Entity F1 | node label/type 정확도 |
| Relation F1 | edge predicate 정확도 |
| Triple F1 | subject-predicate-object 정확도 |
| Task Attribution Accuracy | triple의 `frame_task_id`가 맞는지 |
| Evidence Accuracy | evidence span이 맞는지 |
| Ontology Conformance | domain/range/required property 충족률 |
| Hallucination Rate | 원문 근거 없는 triple 비율 |
| Overgeneralization Rate | example을 일반 원칙으로 잘못 승격한 비율 |
| Direction Error Rate | 관계 방향 오류 비율 |

#### Procedural KG metrics

| Metric | 설명 |
|---|---|
| Process Edge Accuracy | `PRECEDES`, `HAS_SUBTASK` 정확도 |
| Gate Coverage | decision point 포착률 |
| Artifact Flow Accuracy | input/output 산출물 흐름 정확도 |
| Risk-Control Coverage | risk와 mitigation 연결 포착률 |
| Role Assignment Accuracy | 수행자/책임자 연결 정확도 |

#### Agent utility metrics

| Task | 평가 방식 |
|---|---|
| 업무 계획 생성 | 주어진 목표에서 누락 없는 task sequence 생성 |
| 체크리스트 생성 | evidence 기반 수행 체크리스트 생성 |
| 리스크 점검 | task별 risk와 mitigation 제시 |
| 설명 가능성 | 답변에 source evidence를 제시 |
| 표준 매핑 설명 | Layer2 task가 왜 NCS/PCF와 연결되는지 설명 |
| 법률 도메인 전이 | core ontology 재사용 후 추가 annotation 절감률 |

### 14.6 Annotation protocol

Gold data는 전체를 다 만들 필요가 없다.  
처음에는 stratified sample을 만든다.

```text
Train/dev/test split:
- chapter 1: process overview
- chapter 2: capture/sales intelligence
- chapter 3: strategy/risk

Annotation unit:
- Task Frame
- Frame slot
- Triple
- Evidence span
- Modality/scope
- Mapping candidate
```

권장 규모:

| 항목 | 1차 목표 |
|---|---:|
| Gold Task Frame | 25–40개 |
| Gold triples | 800–1,200개 |
| Annotated chunks | 150–250개 |
| Expert annotator | 2명 이상 |
| Adjudication | 1명 |
| Agreement | Cohen’s κ 또는 Krippendorff’s α |

---

## 15. 실제 구현 산출물

### 15.1 파일 산출물

```text
00_source_profile.json
01_evidence_units.jsonl
02_chunks.jsonl
03_task_frame_candidates.jsonl
04_task_frame_catalog.jsonl
05_alias_dictionary.json
06_relation_schema.json
07_frame_anchored_triples_raw.jsonl
08_frame_anchored_triples_validated.jsonl
09_layer2_nodes.jsonl
10_layer2_edges.jsonl
11_layer2_graph_schema.md
12_l2_l1_mapping_candidates.jsonl
13_human_review_sheet.xlsx
14_benchmark_gold_frames.jsonl
15_benchmark_gold_triples.jsonl
16_eval_report.md
```

### 15.2 Node schema

```json
{
  "node_id": "L2_TASK_COMPETITOR_ANALYSIS",
  "node_type": "Task",
  "name": "경쟁사 분석",
  "canonical_name": "경쟁사 분석",
  "aliases": ["Competitor Analysis"],
  "domain": "bid_proposal",
  "task_type": "StrategyDevelopmentTask",
  "definition": "경쟁사의 강점, 약점, 전략, 고객 인식을 분석하여 차별화 요소와 대응 전략을 도출하는 업무",
  "source": "task_frame_llm",
  "evidence_ids": ["EV_ZAIZE_P145_S3_1_4_004"],
  "confidence": 0.90,
  "review_status": "needs_review",
  "version": "v0.1"
}
```

### 15.3 Edge schema

```json
{
  "edge_id": "EDGE_L2_000123",
  "source_id": "L2_TASK_COMPETITOR_ANALYSIS",
  "predicate": "PRODUCES",
  "target_id": "L2_CONCEPT_DIFFERENTIATOR",
  "frame_task_id": "L2_TASK_COMPETITOR_ANALYSIS",
  "evidence_ids": ["EV_ZAIZE_P145_S3_1_4_004"],
  "evidence_quote": "경쟁사 분석을 통해 핵심 차별화요소를 규명하라",
  "modality": "normative",
  "scope": "task_specific",
  "confidence": 0.91,
  "extraction_model": "triple_llm_v1",
  "validation_status": "verified",
  "created_at": "2026-07-03"
}
```

---

## 16. Prompt 설계

### 16.1 Task Frame LLM prompt template

```text
[System]
너는 업무 온톨로지와 지식그래프를 설계하는 연구자다.
목표는 문서에서 에이전트가 실제로 수행·점검·설명할 수 있는 업무 단위(Task Frame)를 추출하는 것이다.
단순 개념, 사람 이름, 회사명, 예시는 Task로 만들지 않는다.

[Input]
도메인: {domain}
문서 범위: {chapter_or_corpus}
섹션 목록:
{section_list}

대표 문장:
{representative_sentences}

기존 Core Task Ontology:
{core_task_type_list}

[Output JSON]
{
  "task_frames": [
    {
      "frame_id": "",
      "canonical_task_name": "",
      "aliases": [],
      "task_type": "",
      "definition": "",
      "parent_process": "",
      "preconditions": [],
      "inputs": [],
      "outputs": [],
      "roles": [],
      "subtasks": [],
      "next_tasks": [],
      "decision_points": [],
      "risks": [],
      "principles": [],
      "success_criteria": [],
      "evidence_sections": [],
      "cross_domain_pattern": "",
      "confidence": 0.0
    }
  ],
  "rejected_candidates": [
    {
      "name": "",
      "reason": ""
    }
  ]
}

[Rules]
1. 업무는 동사적 행위 또는 수행 가능한 명사구여야 한다.
2. 최소 2개 이상의 슬롯을 채울 수 없으면 Task로 만들지 마라.
3. evidence section을 반드시 포함하라.
4. 도메인 특화 이름과 cross-domain pattern을 함께 부여하라.
5. 중복 Task는 alias로 병합하라.
```

### 16.2 Triple LLM prompt template

```text
[System]
너는 ontology-constrained KG extractor다.
현재 chunk에서 확인되는 사실관계만 추출한다.
모든 triple은 반드시 evidence span과 Task Frame에 연결해야 한다.
원문에 없는 지식은 추가하지 않는다.

[Allowed Node Types]
{node_type_list}

[Allowed Relations]
{relation_schema}

[Relevant Task Frames]
{top_k_task_frames}

[Chunk Evidence]
{evidence_id_text_pairs}

[Output JSON]
{
  "chunk_id": "",
  "triples": [
    {
      "subject": "",
      "subject_type": "",
      "predicate": "",
      "object": "",
      "object_type": "",
      "frame_task_id": "",
      "evidence_ids": [],
      "evidence_quote": "",
      "modality": "descriptive|normative|warning|example|definition|heuristic",
      "scope": "domain_principle|task_specific|example_only|source_claim|mapping_hint",
      "polarity": "positive|negative",
      "confidence": 0.0
    }
  ],
  "new_task_candidates": []
}

[Hard Constraints]
1. predicate는 allowed relations 안에서만 선택한다.
2. frame_task_id는 Relevant Task Frames 중 하나를 사용한다. 없으면 "UNASSIGNED"로 둔다.
3. evidence_quote는 evidence text의 부분 문자열이어야 한다.
4. 예시 인물·회사·사건은 일반 원칙으로 만들지 않는다.
5. 추론으로 보완한 내용은 triple로 쓰지 말고 new_task_candidates 또는 note에 넣는다.
```

---

## 17. Graph 저장 방식

### 17.1 Property graph 우선

초기 구현은 Neo4j 또는 compatible property graph가 적합하다.

이유:

- 업무 에이전트 질의는 multi-hop traversal이 많다.
- Task → Input → Artifact → Next Task 흐름 탐색이 중요하다.
- edge property에 evidence, confidence, validation_status를 넣기 쉽다.
- human review 상태 관리가 쉽다.

### 17.2 RDF/OWL export 병행

연구와 표준 validation을 위해 RDF export도 유지한다.

```text
Property Graph
- 운영/서비스/에이전트 질의용

RDF/OWL
- ontology 문서화
- SHACL validation
- 논문 재현성
- 표준 vocabulary 연결
```

### 17.3 Named graph 권장

RDF export 시 named graph를 분리한다.

```text
graph:fato-core
graph:bid-proposal-domain
graph:evidence
graph:runtime
graph:mapping
graph:review
```

---

## 18. 에이전트 활용 시나리오

### 18.1 업무 계획

질문:

```text
A사업 제안서 기획을 시작하려면 어떤 선행 업무와 입력 산출물이 필요한가?
```

KG 탐색:

```text
제안서 기획
← PRECEDES
수주영업
← PRODUCES
Capture Plan

제안서 기획
← USES_INPUT
수주전략, 고객 니즈, 평가 기준, 경쟁사 정보
```

### 18.2 체크리스트 생성

질문:

```text
제안전략을 수립할 때 점검해야 할 항목을 만들어줘.
```

KG 탐색:

```text
Task: 제안전략 관리
- HAS_SUBTASK: 고객 이슈 분석
- HAS_SUBTASK: 경쟁사 분석
- HAS_SUBTASK: 차별화 요소 규명
- HAS_RISK: 고객 비공식 요구조건 미파악
- HAS_PRINCIPLE: 전략은 고객에서 출발
- PRODUCES: 전략기술서
```

### 18.3 리스크 경고

질문:

```text
경쟁사 분석 없이 제안서를 작성하면 어떤 문제가 생길 수 있어?
```

KG 탐색:

```text
경쟁사 분석 - PRODUCES - 차별화 요소
차별화 요소 - USED_AS_INPUT_FOR - 제안전략 관리
제안전략 관리 - HAS_RISK - 경쟁자 대비 차별성 부족
```

### 18.4 표준 매핑 설명

질문:

```text
수주전략 수립은 NCS의 어떤 능력단위와 연결될 수 있고, 왜?
```

KG 탐색:

```text
Layer2 Task: 수주전략 수립
- ANALYZES: 고객 니즈
- ANALYZES: 경쟁사 정보
- PRODUCES: 수주전략
- HAS_DECISION_POINT: Bid/No Bid

Mapping Candidate:
- NCS 수주전략수립
- mapping_type: REQUIRES_CAPABILITY
- reason: 고객 요구, 경쟁사 분석, 평가 우위 요소 도출과 연결
```

---

## 19. Human-in-the-loop 설계

완전 자동 구축보다 더 중요한 것은 **검토 가능한 자동화**다.

### 19.1 Review queue

다음 경우는 자동 승인하지 않는다.

| 조건 | 처리 |
|---|---|
| confidence < 0.80 | review |
| evidence quote 불일치 | reject 또는 review |
| 신규 relation 후보 | ontology review |
| 신규 task 후보 | task catalog review |
| example을 일반 원칙으로 승격 | reject |
| Layer1 mapping score 0.50–0.84 | human review |
| Task merge 충돌 | ontology curator review |
| PRECEDES cycle 발생 | process review |

### 19.2 Review sheet 컬럼

```text
item_id
item_type
source_text
extracted_subject
predicate
object
frame_task_id
evidence_quote
confidence
validation_status
review_decision
reviewer_comment
canonical_fix
```

---

## 20. 단계별 실행 계획

### Phase 0: 데이터 안정화

- `clean_sentences`에서 Evidence Unit 생성
- 구조 메타데이터 누락 3개 문장 처리
- section-level chunk 생성
- figure/table/example 분류

산출물:

```text
01_evidence_units.jsonl
02_chunks.jsonl
00_source_profile.json
```

### Phase 1: Seed Task Ontology 구축

- 25개 내외 seed task catalog 생성
- alias dictionary 구축
- core relation schema 확정
- Task Frame LLM prompt 고정

산출물:

```text
03_task_frame_candidates.jsonl
04_task_frame_catalog.jsonl
05_alias_dictionary.json
06_relation_schema.json
```

### Phase 2: Frame-anchored Triple 추출

- section/chunk별 Triple LLM 실행
- evidence quote 검증
- ontology constraint 검증
- 중복 edge 병합

산출물:

```text
07_frame_anchored_triples_raw.jsonl
08_frame_anchored_triples_validated.jsonl
09_layer2_nodes.jsonl
10_layer2_edges.jsonl
```

### Phase 3: Graph DB 적재와 질의 템플릿

- property graph 적재
- 주요 질의 템플릿 작성
- agent tool API 설계

산출물:

```text
layer2_neo4j_import.cypher
agent_query_templates.md
graph_api_spec.yaml
```

### Phase 4: Layer1 Mapping

- NCS/PCF text representation 생성
- BM25 + embedding top-k 검색
- graph-neighbor support scoring
- mapping review sheet 생성

산출물:

```text
12_l2_l1_mapping_candidates.jsonl
13_human_review_sheet.xlsx
```

### Phase 5: EACL 실험 패키지

- gold annotation subset 구축
- baseline 구현
- ablation 실험
- agent utility task 정의
- 논문 draft 작성

산출물:

```text
14_benchmark_gold_frames.jsonl
15_benchmark_gold_triples.jsonl
16_eval_report.md
paper_draft_eacl.md
```

---

## 21. 예상 오류와 대응

| 오류 | 원인 | 대응 |
|---|---|---|
| 너무 많은 Task 생성 | LLM이 section title을 모두 task로 승격 | “2개 이상 슬롯을 채울 수 없는 후보 reject” 규칙 |
| triple 파편화 | frame 없이 문장별 추출 | Task Frame Top-k를 항상 제공 |
| 예시 일반화 | 사례 문장을 domain principle로 변환 | `scope=example_only` 강제 |
| relation drift | LLM 자유 relation 생성 | allowed relation 폐쇄집합 |
| evidence 없는 지식 추가 | LLM의 배경지식 개입 | evidence quote substring 검증 |
| NCS와 무리한 exact match | 표준 능력단위와 실제 업무의 granularity 차이 | `REQUIRES_CAPABILITY`, `RELATED_TO` 중심 |
| 법률 도메인 전이 실패 | 도메인 개념을 core ontology에 넣음 | core/domain extension 엄격 분리 |
| 순서 관계 충돌 | section 순서와 업무 순서 혼동 | PRECEDES는 explicit evidence 또는 expert review 필요 |

---

## 22. EACL용 독창성 강조 포인트

FATO-KG의 EACL 논문 기여를 강하게 만들려면 “LLM으로 KG를 만들었다”가 아니라 다음 메시지를 전면에 내세워야 한다.

### 22.1 Procedural KG construction as a distinct NLP problem

일반 KG는 factual triple 중심이지만, 업무 에이전트는 다음 지식이 필요하다.

```text
Task
Input
Output
Role
Decision
Risk
Condition
Principle
Evidence
Runtime Instance
```

따라서 FATO-KG는 **procedural and agentic knowledge graph construction**이라는 문제를 제안한다.

### 22.2 Frame anchoring reduces fragmentation

업무 문서에서 같은 개념은 여러 절에 흩어져 있다.  
Task Frame을 먼저 만들면 triple이 하나의 업무 맥락으로 모인다.

```text
고객 니즈 분석
경쟁사 분석
차별화 요소 규명
전략기술서 작성
```

이들이 각각 독립 triple로 떠 있지 않고 `제안전략 관리` 또는 `수주전략 수립` frame 아래 정렬된다.

### 22.3 Evidence-bound graph supports trustworthy agents

모든 node/edge/claim이 evidence와 연결되므로 에이전트 답변에서 출처를 제시할 수 있다.

```text
Answer
→ supporting task
→ supporting triple
→ evidence span
→ page/section/source
```

### 22.4 Loose standard mapping prevents ontology contamination

NCS/PCF 같은 표준체계와 업무 ontology를 병합하면 도메인 지식과 표준 분류가 섞인다.  
FATO-KG는 mapping edge로만 연결하여 다음을 동시에 달성한다.

- 표준 정렬
- 설명 가능성
- 도메인 ontology 독립성
- 향후 다른 표준 추가 가능성

### 22.5 Cross-domain reuse is built into the ontology

수주·제안에서 만든 ontology가 법률 도메인으로 확장될 때, core class와 relation은 유지되고 domain extension만 바뀐다.  
이 점은 단일 도메인 KG 구축 논문보다 연구적 가치가 크다.

---

## 23. 논문 abstract 초안

> We propose FATO-KG, a frame-anchored methodology for constructing evidence-grounded procedural knowledge graphs from domain documents for agentic workflows. Unlike conventional text-to-KG pipelines that extract flat triples, FATO-KG first induces canonical task frames and then routes all extracted triples to task-level anchors with evidence spans, modality, and ontology constraints. The resulting graph represents tasks, inputs, outputs, roles, decision points, risks, conditions, artifacts, and provenance, while maintaining loose mappings to external standard taxonomies such as occupational or process frameworks. We instantiate the method on a Korean bid-proposal corpus and evaluate it against flat triple extraction, ontology-only prompting, and schema-induction baselines. We further test cross-domain reuse on a legal workflow setting. Experiments measure not only triple-level F1, but also task attribution, evidence faithfulness, ontology conformance, process consistency, and downstream agent utility. The proposed formulation highlights procedural KG construction as a distinct NLP problem for trustworthy business agents.

---

## 24. 최종 권장안

현재 프로젝트에서는 다음처럼 진행하는 것이 가장 좋다.

```text
1. Layer2부터 FATO-KG 방식으로 구축한다.
2. Task Frame Catalog를 먼저 만든다.
3. Triple LLM은 반드시 Task Frame과 EvidenceSpan에 귀속시킨다.
4. Core ontology와 수주·제안 domain extension을 분리한다.
5. Layer1 NCS/PCF와는 절대 node merge하지 않고 mapping edge만 만든다.
6. Human review queue를 전제로 자동화한다.
7. EACL 제출용으로는 benchmark와 agent utility 평가까지 설계한다.
```

초기 최소 구현 범위는 다음이다.

```text
- Evidence Unit 1,366개
- Section Chunk 51개
- Seed Task Frame 25개 내외
- Validated Triple 800–1,200개
- Relation vocabulary 20개 내외
- Layer1 mapping candidate Top-5/task
- Human review sheet 1개
```

---

## 25. 참고문헌 및 표준 자료

아래 자료는 방법론 설계의 배경으로 사용하기 적합하다.

1. Huguet Cabot, P.-L., & Navigli, R. (2021). **REBEL: Relation Extraction By End-to-end Language generation**. Findings of EMNLP 2021.  
   https://aclanthology.org/2021.findings-emnlp.204/

2. Mihindukulasooriya, N., Tiwari, S., Enguix, C. F., & Lata, K. (2023). **Text2KGBench: A Benchmark for Ontology-Driven Knowledge Graph Generation from Text**. ISWC 2023 Resource Track.  
   https://arxiv.org/abs/2308.02357

3. Zhang, B., & Soh, H. (2024). **Extract, Define, Canonicalize: An LLM-based Framework for Knowledge Graph Construction**. EMNLP 2024.  
   https://aclanthology.org/2024.emnlp-main.548/

4. Luo, Y. et al. (2024/2025). **OneKE: A Dockerized Schema-Guided LLM Agent-based Knowledge Extraction System**.  
   https://arxiv.org/html/2412.20005v1

5. W3C. **PROV-O: The PROV Ontology**.  
   https://www.w3.org/TR/prov-o/

6. W3C. **Shapes Constraint Language, SHACL**.  
   https://www.w3.org/TR/shacl/

7. W3C/OGC. **Time Ontology in OWL, OWL-Time**.  
   https://www.w3.org/TR/owl-time/

8. Object Management Group. **Business Process Model and Notation, BPMN 2.0.2**.  
   https://www.omg.org/spec/BPMN/2.0.2/About-BPMN

9. APQC. **Process Classification Framework, PCF**.  
   https://www.apqc.org/process-frameworks

10. Schema.org. **Schema.org Vocabulary**.  
    https://schema.org/

---

## 26. 부록: FATO-KG와 입력 방향의 대응

| 입력 방향 | FATO-KG 반영 |
|---|---|
| Layer1은 얇게 | NCS/PCF를 Standard Reference Layer로만 유지 |
| Layer2는 깊게 | Task, Step, Role, Artifact, Condition, Risk, Evidence까지 표현 |
| Task Frame LLM 1종 | Chapter/corpus 수준에서 Task Frame 유도 |
| Triple LLM 1종 | Chunk 수준에서 frame-anchored triple 추출 |
| Task Frame 기준 삼중항 귀속 | 모든 triple에 `frame_task_id` 필수 |
| Layer2와 Layer1 직접 병합 금지 | `MAPS_TO`, `REQUIRES_CAPABILITY`, `PROCESS_CONTEXT` edge만 사용 |
| Evidence 보존 | 모든 claim/triple에 `EVIDENCED_BY` 연결 |
| 향후 에이전트 실행 | `TaskFrame → TaskInstance`, `Artifact → ArtifactInstance`로 runtime layer 확장 |
