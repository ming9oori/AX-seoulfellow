# AX 데이터 기반 Evidence-grounded Procedural KG 구축 실험 설계서

**프로젝트명:** 업무 온톨로지 기반 기업용 멀티 AI 에이전트 자동 생성 및 운영을 위한 Agent Harness 기술 개발  
**실험 범위:** 외부 benchmark 없이, 현재 보유한 AX 데이터만을 사용한 수주·제안 업무 KG 구축 및 내부 품질 검증  
**작성일:** 2026-06-27  
**권장 방법론명:** **AX-EPAK: Evidence-grounded Procedural Agent Knowledge Graph Construction**

---

## 0. 본 문서의 목적

이 문서는 기존의 EACL 제출용 확장 실험 설계에서 외부 benchmark 실험을 제외하고, **현재 보유한 AX 데이터 안에서 실제로 KG를 구축할 수 있는 실행형 실험 설계**만을 정리한다.

따라서 본 설계서의 목표는 다음 세 가지다.

1. `AX.zip`에 포함된 NCS, PCF, 자이제 OCR 데이터를 이용해 **Layer1 표준 온톨로지**와 **Layer2 수주·제안 업무 KG**를 구축한다.
2. Layer2는 단순 triple extraction이 아니라, **Task Frame + ProcedureStep + DecisionGateway + ArtifactFlow + EvidenceAnchor** 구조로 구축한다.
3. 외부 benchmark는 사용하지 않되, 내부 데이터 기반으로 **schema conformance, evidence support, procedural consistency, CQ answerability, mapping plausibility**를 평가한다.

본 실험은 “논문용 대규모 benchmark 성능 경쟁”이 아니라, **내 데이터에서 재현 가능한 KG 구축 파이프라인을 완성하고, 그 품질을 내부 검증하는 구축형 실험**이다.

---

## 1. 실험의 핵심 방향

기존 발표 방향의 핵심인 다음 원칙은 유지한다.

> **Layer1은 얇게, Layer2는 깊게, 연결은 느슨하게 구축한다.**

다만 실제 구축 실험에서는 Layer2를 다음처럼 강화한다.

```text
기존 Layer2:
Task Frame + Triple

수정 Layer2:
Task Frame
+ ProcedureStep
+ DecisionGateway
+ GuardCondition
+ ArtifactFlow
+ Triple
+ EvidenceAnchor
+ ReviewStatus
```

즉, 수주·제안 업무를 단순히 다음과 같은 사실 관계로만 표현하지 않는다.

```text
수주영업 -PRODUCES-> Capture Plan
제안서 기획 -DEVELOPS-> 제안전략
```

대신 실제 업무 실행에 필요한 절차 구조까지 표현한다.

```text
수주영업
  -HAS_STEP-> 고객 니즈 분석
  -HAS_STEP-> 경쟁사 분석
  -HAS_STEP-> 자사 솔루션 분석
  -HAS_DECISION_GATEWAY-> Bid/No Bid Decision
  -PRODUCES-> Capture Plan

Capture Plan
  -FEEDS_INTO-> 제안서 기획

제안서 기획
  -HAS_STEP-> 제안팀 구성
  -HAS_STEP-> 킥오프 미팅
  -HAS_STEP-> 목차 개발
  -PRODUCES-> Proposal Management Plan
```

이 구조는 향후 Agent Harness에서 다음 질문에 답하기 쉽다.

```text
이 업무를 수행하려면 어떤 순서로 진행해야 하는가?
각 단계의 입력과 산출물은 무엇인가?
어떤 시점에서 의사결정이 필요한가?
특정 산출물은 다음 업무의 어디에 쓰이는가?
각 지식은 원문 어디에 근거가 있는가?
```

---

## 2. 사용 데이터 및 1차 구축 범위

### 2.1 데이터 구성

`AX.zip` 기준 데이터 구성은 다음과 같다.

| 구분 | 파일 | 구축상 역할 |
|---|---|---|
| NCS 대분류 | `01_ncs/ncs_lclas.json` | Layer1 NCS 대분류 노드 |
| NCS 중분류 | `01_ncs/ncs_mclas.json` | Layer1 NCS 중분류 노드 |
| NCS 소분류 | `01_ncs/ncs_sclas.json` | Layer1 NCS 소분류 노드 |
| NCS 세분류 | `01_ncs/ncs_dclas.json` | Layer1 NCS 세분류 노드 |
| NCS 능력단위 | `01_ncs/ncs_unit.json` | Layer1 NCS 능력단위 노드 |
| PCF 공통 프로세스 | `02_pcf/pcf_data.json` | Layer1 PCF 프로세스 계층 |
| PCF 성과지표 | `02_pcf/pcf_metrics.json` | PCFElement와 연결되는 metric 노드 |
| PCF 산업별 변형 | `02_pcf/industries/*.json` | 1차 구축에서는 보조자료 및 manifest만 생성 |
| 수주·제안 OCR | `자이제_ocr_sentences.xlsx` | Layer2 업무 KG 원천 텍스트 |

### 2.2 1차 구축 데이터 규모

NCS는 29차 사용본을 기준으로 필터링한다.

```text
NCS_DEGR == 29
AND USG_YN == "Y"
```

1차 구축 기준 규모는 다음과 같다.

| 데이터 | 1차 구축 기준 | 사용 규모 |
|---|---:|---:|
| NCS 대분류 | 29차 사용본 | 24 |
| NCS 중분류 | 29차 사용본 | 84 |
| NCS 소분류 | 29차 사용본 | 281 |
| NCS 세분류 | 29차 사용본 | 269 |
| NCS 능력단위 | 29차 사용본 | 3,450 |
| PCF Element | 공통 PCF 전체 | 2,017 |
| PCF Metric | 전체 | 3,284 |
| PCF 산업별 파일 | manifest 생성 | 20 |
| 자이제 OCR | sentence row | 5,009 |

### 2.3 NCS 품질 주의점

NCS 29차 사용본 기준으로 일부 `ncs_unit.json` 능력단위가 `ncs_dclas.json`의 29차 세분류와 직접 연결되지 않는 경우가 존재한다. 따라서 Layer1 구축 시 다음 정책을 둔다.

```text
정책 A: 원본 세분류가 존재하면 정상 연결
정책 B: 능력단위에는 parent path가 있으나 dclas에 parent가 없으면
        NCSSubDivisionPlaceholder를 생성하고 review_status="needs_validation" 부여
정책 C: placeholder 여부는 quality report에 기록
```

이렇게 하면 능력단위를 유실하지 않으면서도 원본 기준축의 불일치를 투명하게 남길 수 있다.

### 2.4 PCF 품질 주의점

PCF는 `parent` 필드가 상위 요소의 `pcfId`가 아니라 `hid`를 가리키므로, 먼저 다음 인덱스를 만든다.

```python
hid_to_pcf_id = {element["hid"]: element["pcfId"] for element in pcf_data}
```

그 후 다음 관계를 생성한다.

```text
(:PCFElement {pcfId: child}) -[:HAS_CHILD_OF]-> (:PCFElement {pcfId: parent})
```

또는 그래프 방향을 상위에서 하위로 통일하려면 다음처럼 저장한다.

```text
(:PCFElement {pcfId: parent}) -[:HAS_CHILD]-> (:PCFElement {pcfId: child})
```

본 실험에서는 모든 계층 관계 방향을 **상위 → 하위**로 통일한다.

---

## 3. 실험 목표와 연구 질문

### 3.1 실험 목표

본 실험의 목표는 다음과 같다.

```text
AX 데이터만을 이용하여
1. NCS/PCF 표준 기준축을 결정론적으로 구축하고,
2. 자이제 OCR 문서에서 수주·제안 업무 지식을 evidence-grounded procedural KG로 추출하며,
3. Layer2 업무 KG를 NCS/PCF 표준축에 후보 매핑하고,
4. 내부 검증 기준으로 KG 품질을 평가한다.
```

### 3.2 연구 질문

외부 benchmark를 사용하지 않는 대신, 내부 구축 실험의 연구 질문은 다음과 같이 설정한다.

**RQ1. 데이터 구축 가능성**  
현재 보유한 NCS, PCF, OCR 데이터만으로 Layer1/Layer2 구조를 갖춘 수주·제안 업무 KG를 구축할 수 있는가?

**RQ2. Evidence grounding 품질**  
Layer2에서 추출된 Task Frame, ProcedureStep, Triple은 원문 chunk 및 sentence evidence로 복원 가능한가?

**RQ3. 절차형 표현의 유용성**  
단순 triple보다 ProcedureStep, DecisionGateway, ArtifactFlow를 포함한 구조가 수주·제안 업무의 실행 순서와 산출물 흐름을 더 잘 설명하는가?

**RQ4. 내부 질의 응답 가능성**  
구축된 KG는 사전에 정의한 Competency Question에 대해 evidence가 있는 답변을 제공할 수 있는가?

**RQ5. 표준축 연결 가능성**  
Layer2 업무 Task는 NCS 능력단위 및 PCF 프로세스 요소와 설명 가능한 후보 매핑을 생성할 수 있는가?

---

## 4. 전체 실험 파이프라인

전체 실험은 다음 9단계로 구성한다.

```text
[0] 데이터 적재 및 manifest 생성
    ↓
[1] Layer1 NCS/PCF 표준 온톨로지 구축
    ↓
[2] OCR 문서 정제 및 문서 구조 복원
    ↓
[3] CQ 및 Layer2 schema 확정
    ↓
[4] Task Frame 추출 및 검수
    ↓
[5] ProcedureStep / DecisionGateway / ArtifactFlow 추출
    ↓
[6] Evidence-grounded Triple 추출 및 검증
    ↓
[7] Layer2 Graph 통합 및 품질 검증
    ↓
[8] Layer2 → Layer1 후보 매핑
    ↓
[9] KG 시각화 및 내부 평가 보고서 생성
```

각 단계는 독립적으로 산출물을 남긴다. 중간 산출물을 버리지 않고 모두 저장해야 재현성과 오류 추적이 가능하다.

---

## 5. Phase 0: 데이터 적재 및 manifest 생성

### 5.1 목적

모든 원본 파일의 위치, 크기, 해시, 레코드 수, 스키마 필드를 기록하여 재현 가능한 실험 환경을 만든다.

### 5.2 입력

```text
AX.zip
```

### 5.3 처리 절차

1. `AX.zip` 압축 해제
2. 파일별 SHA-256 해시 계산
3. JSON 파일 레코드 수 계산
4. Excel 파일 sheet명, row 수, column명 확인
5. 산업별 PCF 파일 목록화
6. 데이터 manifest 생성

### 5.4 출력

```text
outputs/00_manifest/data_manifest.csv
outputs/00_manifest/data_manifest.json
outputs/00_manifest/raw_schema_profile.md
```

### 5.5 품질 기준

| 항목 | 기준 |
|---|---|
| 모든 원본 파일 해시 | 기록되어야 함 |
| 모든 JSON 파일 | parse 가능해야 함 |
| OCR Excel | `문장`, `페이지` 컬럼 확인 |
| record_count | manifest에 기록 |
| 오류 파일 | `status=error` 및 error message 기록 |

---

## 6. Phase 1: Layer1 NCS/PCF 표준 온톨로지 구축

### 6.1 목적

NCS와 PCF를 LLM 없이 결정론적으로 그래프화한다. Layer1은 지식 추출 대상이 아니라 **표준 기준축**이다.

### 6.2 NCS 구축 방식

#### 6.2.1 노드 타입

```text
NCSLargeClass
NCSMiddleClass
NCSSmallClass
NCSSubDivision
NCSSubDivisionPlaceholder
NCSCompetencyUnit
```

#### 6.2.2 노드 ID 규칙

```text
ncs:L:{NCS_LCLAS_CD}
ncs:M:{NCS_LCLAS_CD}.{NCS_MCLAS_CD}
ncs:S:{NCS_LCLAS_CD}.{NCS_MCLAS_CD}.{NCS_SCLAS_CD}
ncs:D:{NCS_LCLAS_CD}.{NCS_MCLAS_CD}.{NCS_SCLAS_CD}.{NCS_SUBD_CD}
ncs:CU:{NCS_CL_CD}
```

#### 6.2.3 관계

```text
NCSLargeClass -[:HAS_CHILD]-> NCSMiddleClass
NCSMiddleClass -[:HAS_CHILD]-> NCSSmallClass
NCSSmallClass -[:HAS_CHILD]-> NCSSubDivision
NCSSubDivision -[:HAS_COMPETENCY_UNIT]-> NCSCompetencyUnit
```

#### 6.2.4 속성 보존

`COMPE_UNIT_DEF`는 triple로 쪼개지 않고 다음 속성으로 저장한다.

```json
{
  "definition_ko": "...",
  "competency_level": "...",
  "ncs_degr": 29,
  "usage": "Y",
  "source_file": "ncs_unit.json"
}
```

### 6.3 PCF 구축 방식

#### 6.3.1 노드 타입

```text
PCFElement
PCFMetric
PCFIndustryVariantManifest
```

#### 6.3.2 노드 ID 규칙

```text
pcf:E:{pcfId}
pcf:M:{metricId}
pcf:IND:{industry_file}:{pcfId}
```

#### 6.3.3 관계

```text
PCFElement(level=n) -[:HAS_CHILD]-> PCFElement(level=n+1)
PCFElement -[:HAS_METRIC]-> PCFMetric
```

산업별 PCF는 1차 구축에서 그래프에 병합하지 않고 manifest만 생성한다.

```text
outputs/01_layer1/pcf_industry_manifest.jsonl
```

### 6.4 출력

```text
outputs/01_layer1/layer1_ncs_nodes.jsonl
outputs/01_layer1/layer1_ncs_edges.jsonl
outputs/01_layer1/layer1_pcf_nodes.jsonl
outputs/01_layer1/layer1_pcf_edges.jsonl
outputs/01_layer1/layer1_pcf_metric_edges.jsonl
outputs/01_layer1/layer1_quality_report.md
```

### 6.5 내부 품질 기준

| 평가 항목 | 통과 기준 |
|---|---|
| NCS 필터링 | `NCS_DEGR=29`, `USG_YN=Y`만 기본 사용 |
| NCS 능력단위 유실 | 0건. parent 누락 시 placeholder로 보존 |
| PCF parent 복원 | parent hid가 모두 pcfId로 매핑되어야 함 |
| PCF metric 연결 | 모든 metric이 PCFElement에 연결되어야 함 |
| 노드 ID 중복 | 0건 |
| edge endpoint 누락 | 0건 |

---

## 7. Phase 2: OCR 문서 정제 및 문서 구조 복원

### 7.1 목적

`자이제_ocr_sentences.xlsx`의 5,009개 sentence row를 문서 구조에 맞게 복원하고, Layer2 추출에 사용할 chunk를 생성한다.

### 7.2 입력

```text
자이제_ocr_sentences.xlsx
```

### 7.3 OCR row 스키마

원본 Excel은 다음 두 컬럼으로 구성된다.

```text
문장
페이지
```

이를 다음 구조로 변환한다.

```json
{
  "sentence_id": "SENT-000001",
  "text_raw": "...",
  "text_clean": "...",
  "page": 5,
  "zone": "front_matter|toc|body|index|copyright|unknown",
  "chapter_id": null,
  "section_id": null,
  "subsection_id": null,
  "ocr_flags": []
}
```

### 7.4 문서 zone 분류

초기 zone 정책은 다음과 같다.

| 구간 | 페이지 범위 | 처리 |
|---|---:|---|
| 표지/제목 | 3–4 | metadata로만 사용 |
| 프롤로그 | 5–7 | 본문 추출 제외, 배경 정보로만 보관 |
| 목차 | 8–13 | 문서 구조 복원에 사용 |
| 본문 | 19–470 | Layer2 추출 대상 |
| 찾아보기 | 471–473 | alias dictionary 구축에 활용 |
| 판권 | 474 이후 | 제외 |

페이지 범위는 OCR 결과를 기준으로 검수하면서 조정할 수 있다.

### 7.5 텍스트 정제 규칙

| 정제 항목 | 처리 방식 |
|---|---|
| 연속 공백 | 단일 공백으로 정규화 |
| 줄바꿈 fragment | 문장 단위로 병합 또는 유지 여부 표시 |
| OCR 오탈자 | 원문은 `text_raw`, 수정본은 `text_clean`에 저장 |
| 영어 약어 띄어쓰기 오류 | alias 후보로 저장. 예: `T ransaparency` |
| 페이지 번호성 문장 | `ocr_flags=["page_number_candidate"]` |
| 표 fragment | `ocr_flags=["table_fragment"]` |
| 제목 후보 | `ocr_flags=["heading_candidate"]` |

### 7.6 문서 구조 복원

복원할 문서 구조는 다음과 같다.

```text
Document
  → Chapter
    → Section
      → Subsection
        → Chunk
          → Sentence
```

TOC와 본문 heading 후보를 함께 사용한다. 문서 구조는 완전 자동 확정보다는 다음 절차를 권장한다.

```text
1차 자동 복원
→ chapter/section/subsection 후보 생성
→ 사람 검수
→ 확정 structure 저장
→ chunk 생성
```

### 7.7 Chunk 생성 기준

Chunk는 LLM 추출 단위이므로 너무 작거나 너무 크면 안 된다.

| 항목 | 기준 |
|---|---|
| 기본 단위 | subsection 또는 heading 단위 |
| 권장 길이 | 800–1,800자 |
| 최대 길이 | 2,500자 초과 시 분할 |
| 최소 길이 | 250자 미만이면 인접 chunk와 병합 검토 |
| page span | `page_start`, `page_end` 저장 |
| sentence span | 포함 sentence_id 목록 저장 |
| evidence offset | chunk 내 character offset 계산 |

### 7.8 출력

```text
outputs/02_ocr/ocr_sentences_clean.jsonl
outputs/02_ocr/document_structure_raw.json
outputs/02_ocr/document_structure_reviewed.json
outputs/02_ocr/layer2_chunks.jsonl
outputs/02_ocr/ocr_quality_report.md
```

### 7.9 내부 품질 기준

| 평가 항목 | 통과 기준 |
|---|---|
| sentence row 보존 | 5,009개 row가 모두 추적 가능해야 함 |
| 본문 zone 분류 | 본문 추출 대상 chunk가 명확해야 함 |
| chunk source | 모든 chunk가 sentence_id 목록을 가져야 함 |
| chunk page range | 모든 chunk에 page_start/page_end 존재 |
| heading 검수 | chapter/section 구조는 수동 검수 완료 |

---

## 8. Phase 3: Competency Question 및 Layer2 Schema 확정

### 8.1 목적

Layer2 추출을 시작하기 전에, KG가 답해야 하는 질문과 스키마를 확정한다. 본 실험에서는 CQ가 단순 요구사항이 아니라 **추출·검증·시각화의 기준**이다.

### 8.2 내부 Competency Questions

| CQ ID | 질문 | 필요한 KG 요소 |
|---|---|---|
| CQ1 | 수주·제안 업무는 어떤 주요 Task로 구성되는가? | `DomainTask`, `HAS_SUBTASK`, `PRECEDES` |
| CQ2 | 각 Task는 어떤 입력 자료를 사용하는가? | `USES_INPUT`, `Artifact`, `Concept` |
| CQ3 | 각 Task는 어떤 산출물을 생성하는가? | `PRODUCES`, `Artifact` |
| CQ4 | 각 Task는 누가 수행하거나 책임지는가? | `PERFORMED_BY`, `Role` |
| CQ5 | 어떤 의사결정 지점이 존재하는가? | `DecisionGateway`, `HAS_DECISION_GATEWAY` |
| CQ6 | 의사결정에는 어떤 조건이나 판단 기준이 필요한가? | `GuardCondition`, `HAS_GUARD_CONDITION` |
| CQ7 | 산출물은 다음 업무에서 어떻게 사용되는가? | `ArtifactFlow`, `FEEDS_INTO`, `USED_AS_INPUT_FOR` |
| CQ8 | 제안서 리뷰는 어떤 단계에서 어떻게 수행되는가? | `ReviewCheckpoint`, `HAS_REVIEW` |
| CQ9 | 각 업무에서 지켜야 할 원칙은 무엇인가? | `Principle`, `HAS_PRINCIPLE` |
| CQ10 | 각 지식 항목은 원문 어느 chunk/page에 근거가 있는가? | `EvidenceAnchor`, `EVIDENCED_BY` |
| CQ11 | 특정 업무는 어떤 NCS 능력단위와 관련되는가? | `CANDIDATE_REQUIRES_CAPABILITY` |
| CQ12 | 특정 업무는 PCF 프로세스 체계상 어디에 위치하는가? | `CANDIDATE_PROCESS_CONTEXT` |

### 8.3 Layer2 노드 타입

```text
DomainTask
ProcedureStep
DecisionGateway
GuardCondition
Artifact
ArtifactFlow
Role
Principle
ReviewCheckpoint
Risk
Concept
EvidenceAnchor
Chunk
Sentence
```

### 8.4 Layer2 관계 타입

```text
HAS_SUBTASK
HAS_STEP
PRECEDES
USES_INPUT
PRODUCES
PERFORMED_BY
ANALYZES
DEVELOPS
DECIDES
EVALUATES
TRIGGERED_BY
HAS_DECISION_GATEWAY
HAS_GUARD_CONDITION
HAS_REVIEW
HAS_PRINCIPLE
HAS_RISK
FEEDS_INTO
USED_AS_INPUT_FOR
ALIAS_OF
EVIDENCED_BY
RELATED_TO
```

### 8.5 관계별 domain/range 제약

| 관계 | Subject type | Object type |
|---|---|---|
| `HAS_SUBTASK` | DomainTask | DomainTask |
| `HAS_STEP` | DomainTask | ProcedureStep |
| `PRECEDES` | DomainTask / ProcedureStep | DomainTask / ProcedureStep |
| `USES_INPUT` | DomainTask / ProcedureStep | Artifact / Concept |
| `PRODUCES` | DomainTask / ProcedureStep | Artifact |
| `PERFORMED_BY` | DomainTask / ProcedureStep | Role |
| `HAS_DECISION_GATEWAY` | DomainTask / ProcedureStep | DecisionGateway |
| `HAS_GUARD_CONDITION` | DecisionGateway | GuardCondition |
| `HAS_REVIEW` | DomainTask / ProcedureStep | ReviewCheckpoint |
| `HAS_PRINCIPLE` | DomainTask / ProcedureStep | Principle |
| `FEEDS_INTO` | Artifact | DomainTask / ProcedureStep |
| `EVIDENCED_BY` | Any Layer2 node/edge | EvidenceAnchor |

### 8.6 출력

```text
outputs/03_schema/competency_questions.json
outputs/03_schema/layer2_schema.json
outputs/03_schema/allowed_predicates.json
outputs/03_schema/domain_range_constraints.json
outputs/03_schema/ontology_schema.md
```

---

## 9. Phase 4: Task Frame 추출 및 검수

### 9.1 목적

자이제 문서 전체의 핵심 업무 지도를 만든다. Task Frame은 이후 triple과 procedure extraction의 기준 catalog 역할을 한다.

### 9.2 추출 단위

Task Frame은 chunk마다 매번 새로 만들지 않는다. 다음 단위로 추출한다.

```text
1차: Chapter 단위 Task 후보 추출
2차: 전체 문서 통합 및 중복 병합
3차: 사람 검수로 Canonical Task Catalog 확정
```

### 9.3 Task Frame 스키마

```json
{
  "task_id": "L2_TASK_CAPTURE_PLANNING",
  "task_name_ko": "수주영업",
  "task_name_en": "Capture Planning",
  "aliases": ["Capture Planning", "캡처 플래닝"],
  "definition": "...",
  "chapter_scope": ["CH02"],
  "inputs": [
    {"label": "고객 정보", "type": "Concept", "evidence_anchor_ids": ["EA-..."]}
  ],
  "outputs": [
    {"label": "Capture Plan", "type": "Artifact", "evidence_anchor_ids": ["EA-..."]}
  ],
  "roles": [],
  "decision_gateways": [],
  "procedure_steps": [],
  "next_tasks": [],
  "principles": [],
  "evidence_anchor_ids": [],
  "confidence": 0.0,
  "review_status": "pending"
}
```

### 9.4 Task Frame 추출 프롬프트 골격

```text
당신은 수주·제안 업무 온톨로지 구축을 위한 정보 추출기입니다.
아래 chunk들은 같은 chapter에 속합니다.
목표는 이 chapter에서 등장하는 핵심 업무 Task Frame을 추출하는 것입니다.

규칙:
1. 업무 수행 단위만 DomainTask로 추출하세요.
2. 일반 개념, 산출물, 사람 역할은 Task로 만들지 마세요.
3. 각 슬롯은 반드시 원문 근거를 가져야 합니다.
4. 원문에 없는 내용을 추론으로 보강하지 마세요.
5. 기존 canonical task와 같은 개념이면 새 task를 만들지 말고 alias로 연결하세요.
6. 출력은 제공된 JSON schema만 따르세요.

입력:
- chapter_id
- chapter_title
- chunk list
- existing canonical task candidates
- allowed node types

출력:
- task_frame_candidates JSON array
```

### 9.5 검수 방식

Task Frame은 최종 graph의 중심이므로 전량 검수한다.

검수 항목은 다음과 같다.

| 항목 | 검수 기준 |
|---|---|
| Task 적합성 | 실제 업무 수행 단위인가? |
| 중복 여부 | 기존 task와 같은 개념인가? |
| alias 적절성 | 한국어/영어/약어 병합이 맞는가? |
| definition 근거 | 원문 근거가 있는가? |
| input/output 적합성 | 입력과 산출물이 뒤바뀌지 않았는가? |
| procedure 확장 가능성 | 하위 step으로 나눌 수 있는가? |

### 9.6 출력

```text
outputs/04_task_frames/task_frame_candidates_raw.jsonl
outputs/04_task_frames/task_frame_review_sheet.csv
outputs/04_task_frames/canonical_task_catalog.json
outputs/04_task_frames/task_frame_quality_report.md
```

### 9.7 내부 품질 기준

| 평가 항목 | 통과 기준 |
|---|---|
| canonical task 중복 | 중복률 5% 이하 |
| task evidence | 모든 task에 evidence anchor 1개 이상 |
| chapter coverage | 본문 chapter별 핵심 task 1개 이상 |
| review_status | canonical catalog는 모두 reviewed 또는 accepted |

---

## 10. Phase 5: ProcedureStep / DecisionGateway / ArtifactFlow 추출

### 10.1 목적

Task Frame을 실제 실행 가능한 업무 절차 구조로 확장한다. 이 단계가 기존 단순 triple 방식과 가장 크게 달라지는 지점이다.

### 10.2 추출 대상

| 추출 요소 | 설명 | 예시 |
|---|---|---|
| ProcedureStep | 업무 내부의 수행 단계 | 고객 니즈 분석, 경쟁사 분석 |
| DecisionGateway | 판단·선택이 필요한 지점 | Bid/No Bid Decision |
| GuardCondition | 의사결정 조건 | 수익성, 경쟁 가능성, 자원 가용성 |
| ArtifactFlow | 산출물이 다음 업무로 흐르는 관계 | Capture Plan → Proposal Planning |
| ReviewCheckpoint | 검토 활동 | Blue Team Review, Red Team Review |

### 10.3 Procedure 추출 스키마

```json
{
  "procedure_id": "PROC-L2_TASK_CAPTURE_PLANNING-001",
  "parent_task_id": "L2_TASK_CAPTURE_PLANNING",
  "steps": [
    {
      "step_id": "STEP-...",
      "label": "고객 니즈 분석",
      "order": 1,
      "inputs": ["고객 정보"],
      "outputs": ["고객 니즈 분석 결과"],
      "roles": [],
      "evidence_anchor_ids": ["EA-..."]
    }
  ],
  "decision_gateways": [
    {
      "gateway_id": "DG-...",
      "label": "Bid/No Bid Decision",
      "guard_conditions": [],
      "evidence_anchor_ids": ["EA-..."]
    }
  ],
  "artifact_flows": [
    {
      "source_artifact": "Capture Plan",
      "target_task_id": "L2_TASK_PROPOSAL_PLANNING",
      "relation": "FEEDS_INTO",
      "evidence_anchor_ids": ["EA-..."]
    }
  ]
}
```

### 10.4 절차 일관성 검증

자동 검증 규칙은 다음과 같다.

| 규칙 | 설명 |
|---|---|
| 순환 금지 | 같은 procedure 안에서 `PRECEDES` cycle이 없어야 함 |
| 산출물 흐름 | `FEEDS_INTO`의 source는 Artifact여야 함 |
| 의사결정 조건 | DecisionGateway가 있으면 GuardCondition 후보를 검토 |
| 단계 번호 | 같은 task 안에서 order 중복 여부 확인 |
| evidence 필수 | step/gateway/flow는 evidence anchor를 가져야 함 |

### 10.5 출력

```text
outputs/05_procedure/procedure_structures_raw.jsonl
outputs/05_procedure/procedure_structures_clean.jsonl
outputs/05_procedure/procedure_edges.jsonl
outputs/05_procedure/procedure_quality_report.md
```

---

## 11. Phase 6: Evidence-grounded Triple 추출 및 검증

### 11.1 목적

chunk 단위로 사실 관계를 추출하되, 모든 triple이 canonical task와 evidence anchor에 연결되도록 한다.

### 11.2 Triple 추출 입력

각 chunk에 대해 LLM 또는 정보추출기를 호출할 때 다음 정보를 함께 제공한다.

```text
1. chunk_text
2. chunk_id, page_start, page_end, sentence_ids
3. canonical_task_catalog
4. allowed_node_types
5. allowed_predicates
6. domain/range constraints
7. output JSON schema
```

### 11.3 Triple 출력 스키마

```json
{
  "triple_id": "TRI-CH02-S03-C004-0001",
  "frame_task_id": "L2_TASK_CAPTURE_PLANNING",
  "subject": {
    "label": "수주영업",
    "type": "DomainTask",
    "canonical_id": "L2_TASK_CAPTURE_PLANNING",
    "evidence_anchor_id": "EA-..."
  },
  "predicate": "PRODUCES",
  "object": {
    "label": "Capture Plan",
    "type": "Artifact",
    "canonical_id": null,
    "evidence_anchor_id": "EA-..."
  },
  "evidence": {
    "chunk_id": "CH02-S03-C004",
    "sentence_ids": ["SENT-000812", "SENT-000813"],
    "evidence_text": "...",
    "span_start": 125,
    "span_end": 173,
    "anchor_exact": true
  },
  "confidence": 0.82,
  "review_status": "pending"
}
```

### 11.4 EvidenceAnchor 정책

EvidenceAnchor는 세 수준으로 둔다.

| 수준 | 설명 | 사용 조건 |
|---|---|---|
| `exact_span` | chunk 내 start/end char offset이 정확히 잡힘 | 가장 권장 |
| `sentence_anchor` | sentence_id까지는 정확하지만 char offset 불확실 | OCR/띄어쓰기 오류가 있을 때 |
| `chunk_anchor` | chunk 전체가 근거이나 특정 span 불확실 | 추론적 관계 또는 문맥 기반 관계 |

Graph에 확정 반영할 때는 다음 기준을 적용한다.

```text
accepted edge:
  exact_span 또는 sentence_anchor 필수

review_required edge:
  chunk_anchor만 있는 경우
  confidence < 0.65인 경우
  predicate가 other인 경우
  domain/range 위반이 있는 경우
```

### 11.5 Triple 추출 프롬프트 골격

```text
당신은 수주·제안 업무 KG를 구축하기 위한 evidence-grounded relation extractor입니다.
아래 chunk에서 확인 가능한 사실 관계만 추출하세요.

규칙:
1. 원문에 없는 관계를 만들지 마세요.
2. subject, object는 가능한 canonical task catalog의 항목에 연결하세요.
3. predicate는 allowed_predicates 중 하나만 사용하세요.
4. 각 triple은 evidence_text와 sentence_id 또는 span offset을 가져야 합니다.
5. 업무 절차, 의사결정, 산출물 흐름이 보이면 반드시 추출하세요.
6. 사례 회사명/인물명은 표준 업무지식으로 일반화하지 말고 example_entity로 분리하세요.
7. 확신이 낮으면 confidence를 낮추고 review_status="needs_review"로 표시하세요.

출력은 JSON array만 반환하세요.
```

### 11.6 자동 검증

추출 후 다음 검증을 수행한다.

| 검증 | 방식 |
|---|---|
| JSON schema 검증 | 필수 필드 누락 확인 |
| predicate 검증 | allowed list 외 predicate 분리 |
| domain/range 검증 | 관계별 subject/object type 확인 |
| evidence 검증 | evidence_text가 chunk에 존재하는지 확인 |
| canonical ID 검증 | frame_task_id가 catalog에 존재하는지 확인 |
| 중복 제거 | 동일 subject-predicate-object 병합 |
| 방향 검증 | `USES_INPUT`, `PRODUCES`, `FEEDS_INTO` 방향 오류 탐지 |
| 사례 분리 | Microsoft 등 예시 entity를 일반 업무노드와 분리 |

### 11.7 출력

```text
outputs/06_triples/layer2_triples_raw.jsonl
outputs/06_triples/layer2_triples_schema_valid.jsonl
outputs/06_triples/layer2_triples_clean.jsonl
outputs/06_triples/evidence_anchors.jsonl
outputs/06_triples/new_node_candidates.jsonl
outputs/06_triples/new_predicate_candidates.jsonl
outputs/06_triples/triple_quality_report.md
```

### 11.8 내부 품질 기준

| 평가 항목 | 통과 기준 |
|---|---|
| schema violation | clean set 기준 0건 |
| allowed predicate violation | clean set 기준 0건 |
| evidence anchor 존재 | accepted triple 100% |
| exact/sentence anchor 비율 | accepted triple의 90% 이상 |
| unsupported triple rate | 검수 표본 기준 15% 이하 |
| direction error rate | 검수 표본 기준 10% 이하 |
| duplicate triple rate | clean 이후 5% 이하 |

---

## 12. Phase 7: Layer2 Graph 통합 및 품질 검증

### 12.1 목적

Task Frame, Procedure, Triple, EvidenceAnchor를 통합하여 최종 Layer2 KG를 생성한다.

### 12.2 통합 규칙

1. canonical task는 `DomainTask` 노드로 생성한다.
2. procedure step은 `ProcedureStep` 노드로 생성하고 parent task에 연결한다.
3. outputs는 `Artifact` 노드로 생성한다.
4. roles는 `Role` 노드로 생성한다.
5. decision point는 `DecisionGateway` 노드로 생성한다.
6. guard condition은 `GuardCondition` 노드로 생성한다.
7. 동일 label이라도 type이 다르면 별도 노드로 유지한다.
8. alias는 노드를 병합하지 않고 `ALIAS_OF` 또는 `aliases` 속성으로 관리한다.
9. 모든 Layer2 edge는 evidence anchor를 최소 1개 이상 가져야 한다.

### 12.3 최종 Layer2 노드 스키마

```json
{
  "node_id": "L2_ARTIFACT_CAPTURE_PLAN",
  "label": "Capture Plan",
  "label_ko": "수주계획서",
  "label_en": "Capture Plan",
  "type": "Artifact",
  "aliases": [],
  "definition": null,
  "source": "jaije_ocr",
  "evidence_anchor_ids": ["EA-..."],
  "review_status": "accepted"
}
```

### 12.4 최종 Layer2 edge 스키마

```json
{
  "edge_id": "EDGE-L2-000001",
  "source_id": "L2_TASK_CAPTURE_PLANNING",
  "predicate": "PRODUCES",
  "target_id": "L2_ARTIFACT_CAPTURE_PLAN",
  "evidence_anchor_ids": ["EA-..."],
  "confidence": 0.86,
  "source_triple_ids": ["TRI-..."],
  "review_status": "accepted"
}
```

### 12.5 Graph 품질 검증

| 검증 항목 | 설명 |
|---|---|
| orphan node | edge가 없는 고립 노드 확인 |
| dangling edge | source/target node가 없는 edge 확인 |
| evidence missing | evidence 없는 Layer2 edge 확인 |
| type violation | domain/range 제약 위반 확인 |
| cycle check | `PRECEDES` 관계 cycle 확인 |
| hub analysis | 과도하게 많은 edge를 가진 node 검토 |
| alias collision | 동일 alias가 여러 canonical node에 연결되는지 확인 |
| chapter coverage | chapter별 task/triple 분포 확인 |

### 12.6 출력

```text
outputs/07_layer2_graph/layer2_nodes.jsonl
outputs/07_layer2_graph/layer2_edges.jsonl
outputs/07_layer2_graph/layer2_alias_dictionary.json
outputs/07_layer2_graph/layer2_evidence_index.jsonl
outputs/07_layer2_graph/layer2_graph_quality_report.md
```

---

## 13. Phase 8: Layer2 → Layer1 후보 매핑

### 13.1 목적

Layer2 업무 Task가 NCS 표준 역량축과 PCF 표준 프로세스축 중 어디와 관련되는지 후보 매핑을 생성한다.

이 단계에서도 자동 확정은 하지 않는다.

```text
자동화 목표: 후보 추천
최종 확정: 사람 검수
```

### 13.2 매핑 대상

```text
Layer2 DomainTask → NCSCompetencyUnit
Layer2 DomainTask → PCFElement
```

### 13.3 매핑용 텍스트 구성

#### Layer2 Task 텍스트

```text
task_name_ko
+ task_name_en
+ aliases
+ definition
+ inputs
+ outputs
+ procedure_steps
+ decision_gateways
+ principles
+ evidence-supported keywords
```

#### NCS 텍스트

```text
NCS_LCLAS_CDNM
+ NCS_MCLAS_CDNM
+ NCS_SCLAS_CDNM
+ NCS_SUBD_CDNM
+ COMPE_UNIT_NAME
+ COMPE_UNIT_DEF
```

#### PCF 텍스트

```text
hid
+ nameKo
+ nameEn
+ descKo
+ descEn
+ parent path
```

### 13.4 후보 생성 방식

외부 benchmark 없이 내부 후보 추천만 수행한다.

```text
1. BM25 후보 Top-50
2. Embedding similarity 후보 Top-50
3. 후보 union
4. 계층 context 보정
5. action verb 유사도 보정
6. domain gap penalty 적용
7. Top-K 후보 저장
```

### 13.5 점수식

초기 점수식은 다음과 같이 둔다.

```text
final_score =
  0.25 × name_similarity
+ 0.30 × definition_description_similarity
+ 0.15 × action_verb_similarity
+ 0.10 × hierarchy_context_similarity
+ 0.15 × embedding_similarity
+ 0.05 × level_compatibility
- domain_gap_penalty
```

기존 발표안보다 embedding 비중을 조금 높이고, definition/description 비중은 유지한다. 이유는 Layer2 task가 짧은 label만으로는 NCS/PCF와 직접 이름이 맞지 않을 가능성이 크기 때문이다.

### 13.6 매핑 타입

| mapping_type | 의미 |
|---|---|
| `exactMatch` | 거의 동일한 업무/능력 |
| `broadMatch` | 상위 개념으로 포괄 |
| `relatedTo` | 의미적으로 관련 |
| `requiresCapability` | 해당 업무 수행에 필요한 역량 |
| `processContext` | PCF상 업무 위치 설명 |
| `noMatch` | 연결하지 않음 |

### 13.7 매핑 결과 스키마

```json
{
  "mapping_id": "MAP-L2-NCS-000001",
  "source_id": "L2_TASK_CAPTURE_PLANNING",
  "source_type": "DomainTask",
  "target_id": "ncs:CU:...",
  "target_type": "NCSCompetencyUnit",
  "mapping_type": "requiresCapability",
  "score": 0.72,
  "score_breakdown": {
    "name_similarity": 0.31,
    "definition_description_similarity": 0.75,
    "action_verb_similarity": 0.80,
    "hierarchy_context_similarity": 0.52,
    "embedding_similarity": 0.78,
    "level_compatibility": 0.60,
    "domain_gap_penalty": 0.10
  },
  "reason": "고객/경쟁사 분석 및 전략 수립 행위가 유사함",
  "review_status": "pending"
}
```

### 13.8 내부 품질 기준

| 평가 항목 | 통과 기준 |
|---|---|
| task coverage | canonical task의 80% 이상에 후보 1개 이상 생성 |
| top-k 검수 적합률 | 검수 표본 기준 Top-5 내 acceptable 후보 60% 이상 |
| reason 존재 | 모든 후보에 reason 포함 |
| no auto-merge | Layer1/Layer2 node 직접 병합 0건 |

### 13.9 출력

```text
outputs/08_mapping/l2_ncs_mapping_candidates.jsonl
outputs/08_mapping/l2_pcf_mapping_candidates.jsonl
outputs/08_mapping/mapping_review_sheet.csv
outputs/08_mapping/mapping_quality_report.md
```

---

## 14. Phase 9: KG 시각화 및 내부 평가 보고서 생성

### 14.1 목적

구축된 KG를 연구자와 도메인 전문가가 직접 탐색할 수 있도록 시각화한다. 시각화는 단순 presentation용이 아니라, 품질 검수 도구로도 사용한다.

### 14.2 시각화 산출물

| 산출물 | 용도 |
|---|---|
| `kg_viewer.html` | 브라우저에서 인터랙티브 탐색 |
| `kg_full.graphml` | Gephi, yEd, Cytoscape 등에서 분석 |
| `kg_full.json` | 웹 시각화 및 API 연계 |
| `neo4j_nodes.csv` | Neo4j import |
| `neo4j_edges.csv` | Neo4j import |
| `kg_static_overview.svg` | 보고서 삽입용 정적 그래프 |

### 14.3 시각화 기능 요구사항

인터랙티브 HTML viewer는 다음 기능을 포함한다.

| 기능 | 설명 |
|---|---|
| Layer 필터 | Layer1 NCS, Layer1 PCF, Layer2, Mapping 구분 |
| Node type 필터 | DomainTask, Artifact, Role, PCFElement 등 |
| Predicate 필터 | PRODUCES, PRECEDES, HAS_STEP 등 |
| Chapter 필터 | 특정 chapter에서 추출된 노드/엣지만 보기 |
| Evidence 보기 | edge 클릭 시 page, chunk, evidence text 표시 |
| Mapping 보기 | Layer2 task와 NCS/PCF 후보 연결 확인 |
| Review status 필터 | accepted, pending, needs_review 구분 |
| 검색 | label, alias, id 기반 검색 |

### 14.4 시각화 색상 정책

| 유형 | 시각화 원칙 |
|---|---|
| Layer1 NCS | 표준 역량축 색상 |
| Layer1 PCF | 표준 프로세스축 색상 |
| Layer2 Task | 가장 강조 |
| Artifact | Task보다 작은 노드 |
| DecisionGateway | 다이아몬드 또는 별도 shape |
| Mapping edge | 점선 또는 옅은 선 |
| Evidence edge | viewer에서는 상세 패널로 표시, 그래프에는 기본 숨김 |

### 14.5 시각화를 통한 품질 검수

시각화에서 다음 오류를 육안으로 확인한다.

```text
1. 특정 노드가 지나치게 많은 edge를 갖는지
2. 제안서 작성, 제안서 기획, 수주영업 같은 핵심 task가 분리되어 있는지
3. Artifact 흐름이 업무 순서와 맞는지
4. NCS/PCF mapping edge가 과도하게 많은지
5. evidence가 없는 edge가 남아 있는지
6. 동일 개념이 alias 병합되지 않고 중복 노드로 보이는지
```

### 14.6 출력

```text
outputs/09_visualization/kg_viewer.html
outputs/09_visualization/kg_full.json
outputs/09_visualization/kg_full.graphml
outputs/09_visualization/kg_static_overview.svg
outputs/09_visualization/neo4j_nodes.csv
outputs/09_visualization/neo4j_edges.csv
outputs/09_visualization/visualization_readme.md
```

---

## 15. 내부 평가 설계

외부 benchmark를 사용하지 않으므로, 평가는 **내부 구축 품질 평가**로 설계한다.

### 15.1 평가 단위

| 평가 단위 | 설명 |
|---|---|
| Sentence | OCR 문장 단위 |
| Chunk | LLM 추출 입력 단위 |
| Task Frame | 업무 지도 단위 |
| Procedure | Task 내부 절차 구조 |
| Triple | 관계 추출 단위 |
| Edge | 최종 graph relation |
| Mapping Candidate | Layer2→Layer1 후보 |
| CQ Answer | KG 질의 결과 |

### 15.2 평가 지표

#### 15.2.1 Schema Conformance

```text
Schema Conformance =
1 - (schema violation 수 / 전체 검증 대상 수)
```

목표:

```text
clean graph 기준 100%
```

#### 15.2.2 Evidence Support Rate

```text
Evidence Support Rate =
근거가 확인된 triple 수 / 검수한 triple 수
```

판정 기준:

| 라벨 | 의미 |
|---|---|
| `supported_exact` | 원문에 명시적으로 있음 |
| `supported_paraphrase` | 원문 표현을 합리적으로 바꾼 수준 |
| `weakly_supported` | 문맥상 가능하나 명시성 약함 |
| `unsupported` | 원문 근거 없음 |
| `wrong` | 원문과 반대이거나 오류 |

목표:

```text
supported_exact + supported_paraphrase ≥ 85%
unsupported + wrong ≤ 15%
```

#### 15.2.3 Evidence Restoration Success

```text
Evidence Restoration Success =
exact_span 또는 sentence_anchor를 가진 accepted edge 수 / accepted edge 수
```

목표:

```text
90% 이상
```

#### 15.2.4 Procedural Consistency

검증 항목:

```text
PRECEDES cycle 없음
ProcedureStep order 충돌 없음
DecisionGateway는 GuardCondition 또는 evidence를 가짐
ArtifactFlow source는 Artifact
ArtifactFlow target은 Task 또는 Step
```

목표:

```text
자동 검증 오류 0건
```

#### 15.2.5 CQ Answerability

각 CQ에 대해 KG query를 작성하고, 답변 가능 여부를 평가한다.

| 점수 | 기준 |
|---:|---|
| 0 | 답변 불가 |
| 1 | 일부 노드만 검색됨 |
| 2 | 답변은 가능하나 evidence 부족 |
| 3 | 답변 가능, evidence 있음, 구조 일부 부족 |
| 4 | 답변 가능, evidence 있음, 구조 적절 |
| 5 | 답변 가능, evidence 있음, 절차/표준 매핑까지 연결됨 |

목표:

```text
핵심 CQ 10개 평균 4.0 이상
```

#### 15.2.6 Mapping Plausibility

Layer2→NCS/PCF 후보 매핑은 Top-K 검수로 평가한다.

```text
Top-K Acceptable Rate =
Top-K 후보 중 1개 이상 acceptable인 task 수 / 검수 task 수
```

목표:

```text
Top-5 기준 60% 이상
```

### 15.3 검수 표본 설계

전체를 모두 사람 검수하면 비용이 크므로, 다음과 같이 나눈다.

| 대상 | 검수 방식 | 권장 표본 |
|---|---|---:|
| Task Frame | 전량 검수 | 전체 task |
| Procedure | 핵심 task 전량 + 나머지 표본 | 핵심 task 100% |
| Triple | chapter stratified sampling | 120 chunks |
| Evidence Anchor | triple 검수 표본과 동일 | 120 chunks |
| Mapping Candidate | canonical task 기준 표본 | 30–50 task |
| CQ Answer | 전량 검수 | 10–12 CQ |

### 15.4 검수자 운영

권장 방식은 다음과 같다.

```text
1차 검수자: 추출 결과의 correctness/evidence 확인
2차 검수자: 애매한 항목 adjudication
30개 chunk는 두 명이 중복 검수하여 agreement 확인
```

외부 benchmark는 사용하지 않지만, 내부 검수 신뢰도를 위해 최소한의 중복 검수는 필요하다.

### 15.5 Review Sheet 필드

```text
item_id
item_type
task_id
chunk_id
page_start
page_end
subject
predicate
object
node_or_edge_type
evidence_text
evidence_anchor_type
confidence
system_decision
reviewer_decision
support_label
type_correct
predicate_correct
direction_correct
canonicalization_correct
comment
final_status
```

---

## 16. 실험 산출물 전체 목록

최종 폴더 구조는 다음과 같이 둔다.

```text
outputs/
  00_manifest/
    data_manifest.csv
    data_manifest.json
    raw_schema_profile.md

  01_layer1/
    layer1_ncs_nodes.jsonl
    layer1_ncs_edges.jsonl
    layer1_pcf_nodes.jsonl
    layer1_pcf_edges.jsonl
    layer1_pcf_metric_edges.jsonl
    pcf_industry_manifest.jsonl
    layer1_quality_report.md

  02_ocr/
    ocr_sentences_clean.jsonl
    document_structure_raw.json
    document_structure_reviewed.json
    layer2_chunks.jsonl
    ocr_quality_report.md

  03_schema/
    competency_questions.json
    layer2_schema.json
    allowed_predicates.json
    domain_range_constraints.json
    ontology_schema.md

  04_task_frames/
    task_frame_candidates_raw.jsonl
    task_frame_review_sheet.csv
    canonical_task_catalog.json
    task_frame_quality_report.md

  05_procedure/
    procedure_structures_raw.jsonl
    procedure_structures_clean.jsonl
    procedure_edges.jsonl
    procedure_quality_report.md

  06_triples/
    layer2_triples_raw.jsonl
    layer2_triples_schema_valid.jsonl
    layer2_triples_clean.jsonl
    evidence_anchors.jsonl
    new_node_candidates.jsonl
    new_predicate_candidates.jsonl
    triple_quality_report.md

  07_layer2_graph/
    layer2_nodes.jsonl
    layer2_edges.jsonl
    layer2_alias_dictionary.json
    layer2_evidence_index.jsonl
    layer2_graph_quality_report.md

  08_mapping/
    l2_ncs_mapping_candidates.jsonl
    l2_pcf_mapping_candidates.jsonl
    mapping_review_sheet.csv
    mapping_quality_report.md

  09_visualization/
    kg_viewer.html
    kg_full.json
    kg_full.graphml
    kg_static_overview.svg
    neo4j_nodes.csv
    neo4j_edges.csv
    visualization_readme.md

  10_evaluation/
    internal_review_sample.jsonl
    internal_review_results.csv
    cq_queries.json
    cq_answerability_report.md
    final_build_report.md
```

---

## 17. 실행 일정안

외부 benchmark가 제외되었으므로, 일정은 구축 중심으로 압축할 수 있다.

| 기간 | 주요 작업 | 핵심 산출물 |
|---|---|---|
| Week 1 | 데이터 manifest, Layer1 NCS/PCF 구축 | manifest, layer1 nodes/edges |
| Week 2 | OCR 정제, 문서 구조 복원, chunk 생성 | clean sentences, chunks |
| Week 3 | CQ/schema 확정, Task Frame 추출 | schema, task candidates |
| Week 4 | Task Frame 검수, canonical catalog 확정 | canonical_task_catalog |
| Week 5 | Procedure/Decision/ArtifactFlow 추출 | procedure structures |
| Week 6 | Triple 추출 및 evidence 검증 | clean triples, evidence anchors |
| Week 7 | Layer2 graph 통합, alias 정규화 | layer2 nodes/edges |
| Week 8 | Layer2→NCS/PCF 후보 매핑 | mapping candidates |
| Week 9 | KG 시각화, 내부 평가 표본 검수 | kg_viewer, review results |
| Week 10 | 최종 build report 작성 | final_build_report |

---

## 18. Go/No-Go 품질 게이트

각 단계는 다음 조건을 만족해야 다음 단계로 넘어간다.

| Gate | 조건 | 미달 시 조치 |
|---|---|---|
| G1: Manifest | 모든 파일 parse 및 해시 기록 | 원본 재확인 |
| G2: Layer1 | dangling edge 0건 | placeholder 또는 parent 복원 |
| G3: Chunk | 모든 chunk가 sentence_id/page 보유 | chunking 재수행 |
| G4: Task Catalog | task evidence 100% | task 후보 재추출/병합 |
| G5: Procedure | cycle 및 type violation 0건 | procedure edge 수정 |
| G6: Triple | schema violation 0건 | prompt/schema 수정 후 재추출 |
| G7: Evidence | accepted edge evidence 100% | unsupported edge review queue 이동 |
| G8: Mapping | 후보 reason 100% | mapping scorer 수정 |
| G9: Visualization | 모든 accepted node/edge 로딩 | viewer input 변환 수정 |

---

## 19. 본 실험에서 제외하는 것

이번 실험에서는 다음을 제외한다.

```text
1. 외부 KG construction benchmark 실험
2. EACL 제출용 public benchmark 비교
3. 여러 LLM 모델 간 대규모 성능 비교
4. 외부 데이터셋을 이용한 generalization 검증
5. 산업별 PCF 전체 병합
6. Agent Harness 실제 자동 실행 성능평가
```

다만 추후 논문 확장 시에는 다음을 추가할 수 있다.

```text
1. public benchmark와 비교
2. 모델별 ablation
3. gold annotation 확대
4. Agent task execution 평가
5. NCS/PCF crosswalk의 downstream utility 평가
```

---

## 20. 최종 성공 기준

이번 내부 구축 실험의 성공 기준은 다음과 같다.

| 구분 | 성공 기준 |
|---|---|
| Layer1 구축 | NCS/PCF 표준 계층과 metric 연결 완료 |
| OCR 구조화 | 자이제 OCR sentence가 chunk와 page로 추적 가능 |
| Task Catalog | 수주·제안 주요 업무 task catalog 확정 |
| Procedure KG | 주요 task에 step, decision, artifact flow 연결 |
| Triple KG | evidence-supported triple clean set 생성 |
| Evidence | 모든 accepted Layer2 edge가 evidence anchor 보유 |
| Mapping | Layer2→NCS/PCF Top-K 후보 생성 및 검수 가능 |
| Visualization | HTML/GraphML/JSON 형태로 KG 탐색 가능 |
| Internal Evaluation | CQ answerability, evidence support, schema conformance 보고서 생성 |

최종적으로 다음 파일이 존재하면 본 실험은 완료로 본다.

```text
outputs/07_layer2_graph/layer2_nodes.jsonl
outputs/07_layer2_graph/layer2_edges.jsonl
outputs/08_mapping/l2_ncs_mapping_candidates.jsonl
outputs/08_mapping/l2_pcf_mapping_candidates.jsonl
outputs/09_visualization/kg_viewer.html
outputs/10_evaluation/final_build_report.md
```

---

## 21. 최종 요약

이번 실험은 benchmark 성능 경쟁을 하지 않는다. 대신 다음을 목표로 한다.

> **AX가 보유한 NCS, PCF, 자이제 OCR 데이터를 이용해, 수주·제안 업무를 evidence-grounded procedural KG로 실제 구축하고, 그 결과를 내부 품질 기준으로 검증한다.**

기존 발표안의 안정적인 구조는 유지한다.

```text
Layer1 = NCS/PCF 표준 기준축
Layer2 = 수주·제안 업무 KG
Mapping = Layer2와 Layer1의 느슨한 연결
```

여기에 다음을 추가하여 실제 구축성과 검증성을 높인다.

```text
1. EvidenceAnchor 기반 근거 추적
2. ProcedureStep/DecisionGateway/ArtifactFlow 기반 절차형 표현
3. CQ 기반 내부 answerability 평가
4. schema/domain-range 기반 자동 검증
5. HTML/GraphML 기반 KG 시각화
```

따라서 본 설계서는 EACL 제출용 benchmark 실험이 아니라, **현재 데이터로 KG를 완성하기 위한 실험 운영 문서**로 사용한다.
