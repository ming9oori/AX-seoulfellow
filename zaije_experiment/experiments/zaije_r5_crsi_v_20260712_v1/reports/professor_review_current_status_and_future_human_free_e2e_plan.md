# 자이제 온톨로지 파일럿 현재 진행 상황 및 향후 무인 End-to-End KG 구축 계획

작성일: 2026-07-12  
문서 용도: 교수님 검토 및 후속 진행 방향 확인  
공식 현재 실험: `zaije_r5_crsi_v_20260712_v1`  
공식 현재 판정: `DETERMINISTIC_CRSI_ONLY_PASS`  
후속 무인 End-to-End 단계: **교수님 검토 전, 공식 실행 보류**

---

# 1. 이 문서의 목적

이 문서는 다음 세 가지를 구분하여 설명하기 위해 작성했다.

1. 지금까지 실제로 무엇을 구현하고 실험했는가?
2. 현재 무엇이 구현되지 않았으며, 왜 구현되지 않았는가?
3. 앞으로 파일럿을 어떤 목표와 방법으로 끝까지 진행하려는가?

가장 중요한 점은 다음과 같다.

> 현재까지는 원문 추적, 일부 명시 표현 추출, 개념 alias 정리, RDF·Neo4j 변환까지 수행했다. 그러나 Actor·Artifact·입력·산출물 등 완전한 업무 의미 그래프는 아직 공식적으로 구현하지 않았다.

향후 목표는 다음과 같다.

> 사람의 판정이나 수작업 annotation 없이, 자이제_1 데이터만 입력하여 원문부터 KG·Neo4j까지 자동으로 생성되는 전체 파이프라인을 완성한다.

이 향후 목표는 정확도 평가보다 **자동 파이프라인의 처음부터 끝까지 완주**를 우선한다.

---

# 2. 최종적으로 만들고 싶은 것

최종 목표는 자이제 수주·제안 데이터에서 다음 구조를 자동으로 생성하는 것이다.

```text
누가 업무를 수행하는가?
어떤 업무를 수행하는가?
업무에 필요한 입력은 무엇인가?
업무의 산출물은 무엇인가?
업무는 어떤 순서로 진행되는가?
각 결과는 Excel 원문의 어느 부분에서 나왔는가?
```

예상하는 최종 KG의 기본 모습은 다음과 같다.

```text
제안서 작성          = WorkUnit
제안팀               = Actor 또는 Organization
고객 요구조건        = InformationObject
제안서 초안          = Artifact

제안서 작성 ──PERFORMED_BY─────> 제안팀
제안서 작성 ──HAS_INPUT────────> 고객 요구조건
제안서 작성 ──PRODUCES_OUTPUT──> 제안서 초안
```

그리고 모든 노드와 관계는 다음 경로로 원문까지 추적할 수 있어야 한다.

```text
Concept 또는 Relation
→ Mention
→ Anchor
→ EvidenceBundle
→ Excel 행과 원문
```

---

# 3. 현재까지 실제로 완료한 범위

## 3.1 원문 데이터 고정

- 사용 파일: `handoff-hanyang/수주제안/자이제_1.xlsx`
- 전체 레코드: 1,366개
- 기존 R4 입력 파일과 논리 텍스트가 동일한지 확인 완료
- Excel 행 번호, 원문, 해시를 EvidenceBundle로 보존

## 3.2 Anchor 분리

원문을 다음 기준으로 분리했다.

```text
일반 글 → 문장·절
표       → 표 셀
목록     → 목록 항목
```

전체 non-TEST 953개 Evidence에서 다음 Anchor를 생성했다.

| Anchor 종류 | 수 |
|---|---:|
| 일반 문장·절 | 907 |
| 표 셀 | 410 |
| 목록 항목 | 163 |
| 합계 | 1,480 |

각 Anchor에는 다음 정보가 저장돼 있다.

```text
Excel Evidence ID
원문 시작 위치
원문 종료 위치
정확한 원문 문자열
문장·표·목록 구조
표 header·row header 등의 Context
```

원문의 `start_char:end_char`와 Anchor 문자열이 정확히 일치하는지 검사했다.

## 3.3 현재 Mention 추출

현재 Mention은 LLM이 아니라 사람이 작성한 정규식 규칙으로 추출한다.

| Mention 종류 | 대표 표현 |
|---|---|
| 의무·규칙 | 반드시, 해야 한다, 필수 |
| 권고 | 권장한다, 바람직하다 |
| 금지 | 해서는 안 된다, 금지한다 |
| 조건·예외 | 경우, 만약, 단, 다만 |
| 부정 | 아니다, 않는다, 없다 |
| 사례 | 예를 들어, 예시, 사례 |
| 수량 | 3명, 30점 이상, 3~6개월 |
| alias | 한글명(영문명) |
| 일부 행동 | 작성한다, 분석한다, 검토한다, 수립한다 |

예:

```text
원문: “제안서는 반드시 3명 이상이 검토해야 한다.”

반드시         → 의무 CueMention
3명 이상       → QuantityMention
검토해야 한다  → ActionMention
```

## 3.4 현재 개념 유형화

현재는 학습된 의미 분류기가 아니라 R4 타입을 R5 타입으로 바꾸는 고정 규칙을 사용한다.

```text
ActionMention       → WorkUnit
ExplicitProcessStep → WorkUnit
ExplicitDeonticRule → Rule
ExplicitCondition   → Condition
QuantityMention     → Metric
QuantityConstraint  → Metric
TemplateField       → TemplateField
Concept·Alias       → DomainConcept 또는 표면 Mention
```

현재 전체 non-TEST 그래프의 주요 타입은 다음과 같다.

| 타입 | 수 |
|---|---:|
| WorkUnit | 299 |
| Rule | 45 |
| Condition | 116 |
| Metric | 178 |
| TemplateField | 263 |
| DomainConcept | 139 |

## 3.5 현재 실제 생성 관계

현재 최종 B1에서 실제로 생성된 주요 의미 관계는 다음과 같다.

| 관계 | 수 | 근거 |
|---|---:|---|
| `HAS_ALIAS` | 166 | 명시적인 한글명(영문명) |
| `PRECEDES` | 55 | 명시적 단계·순서 표현 |
| `HAS_DEFINITION` | 17 | 정의 cue |
| `HAS_FIELD` | 7 | 템플릿 cue와 표 구조 |
| `HAS_CONDITION` | 4 | 같은 Anchor의 Rule·Condition |

## 3.6 개념 정규화

다음처럼 명시적인 alias를 하나의 canonical concept로 정리했다.

```text
제안 참여 의사 결정
Bid/No bid Decision
Bid / No Bid Decision
```

정리 후:

```text
Canonical Concept: 제안 참여 의사 결정
├── Mention: 제안 참여 의사 결정
├── Mention: Bid/No bid Decision
└── Mention: Bid / No Bid Decision
```

전체 시연 그래프에서 명시 alias 166/166을 연결했다.

## 3.7 RDF·Neo4j 변환과 검증

현재 공식 R5 B1 시연 그래프는 다음과 같다.

| 항목 | 값 |
|---|---:|
| nodes | 4,767 |
| relationships | 10,738 |
| canonical concepts | 139 |
| surface mentions | 302 |
| RDF triples | 87,023 |
| SHACL critical violation | 0 |

Neo4j Community 4.4.43에 실제로 적재하여 다음을 확인했다.

```text
node coverage = 1.00
relationship coverage = 1.00
Rule→Anchor = 45/45
Concept→Mention = 139/139
필수 query = 6/6 non-empty
```

---

# 4. 현재 결과를 어떻게 해석해야 하는가

현재 결과는 다음을 의미한다.

> 원문 위치, 명시 표현, alias, 일부 규칙·조건·순서 관계를 추적할 수 있는 보수적 온톨로지 코어를 만들었다.

현재 결과가 의미하지 않는 것은 다음이다.

> 모든 업무 개념과 관계가 정확하게 추출된 완성형 수주·제안 온톨로지를 만들었다.

현재 그래프의 4,767개 노드와 10,738개 관계에는 다음 구조 노드와 관계가 많이 포함돼 있다.

```text
EvidenceBundle
Anchor
ContextSpan
Mention
Document·Chapter·Section
provenance 관계
```

따라서 노드·관계 수가 많다는 사실을 업무 의미 그래프가 완성됐다는 뜻으로 해석하면 안 된다.

---

# 5. 현재 구현되지 않은 부분

## 5.1 일반 명사구 Mention 추출

현재 시스템은 다음 표현을 항상 독립 Mention으로 추출하지 못한다.

```text
제안팀
제안서 초안
고객 요구조건
평가위원
Capture Plan
```

현재 정규식은 cue, 수량, alias, 일부 행동에 집중돼 있다.

## 5.2 Actor·Artifact·InformationObject 유형화

다음 유형을 일반적으로 판단하는 규칙이 아직 없다.

```text
제안팀        → Actor 또는 Organization
제안서 초안   → Artifact
고객 요구조건 → InformationObject
```

schema에는 타입이 정의돼 있지만 실제 의미 분류기가 구현된 것은 아니다.

## 5.3 표 header를 이용한 유형화

Anchor 분리기는 다음 문맥을 보존한다.

```text
Anchor: 제안서 작성
Column Header: 활동(Activity)

Anchor: 제안서 초안
Column Header: 결과물(Output)
```

그러나 현재 공식 B1에서는 다음 규칙을 사용하지 않는다.

```text
Activity 열 → WorkUnit
Output 열   → Artifact
Role 열     → Actor 또는 Organization
Input 열    → InformationObject
```

## 5.4 주어·목적어·입력·산출물 추출

다음 문장을 의미 역할로 분리하는 기능이 아직 부족하다.

```text
“제안팀이 고객 요구조건을 바탕으로 제안서 초안을 작성한다.”
```

필요한 결과:

```text
Actor: 제안팀
InformationObject: 고객 요구조건
WorkUnit: 제안서 초안 작성
Artifact: 제안서 초안
```

## 5.5 핵심 업무 관계

현재 공식 B1에는 다음 일반 관계가 없다.

```text
PERFORMED_BY
HAS_INPUT
PRODUCES_OUTPUT
```

---

# 6. 왜 이 부분이 아직 구현되지 않았는가

## 6.1 앞선 실험의 우선순위

지금까지는 다음 위험을 먼저 해결했다.

```text
원문 위치가 정확한가?
규칙과 사례를 구분할 수 있는가?
명시 alias를 안전하게 정리할 수 있는가?
그래프에서 원문까지 추적할 수 있는가?
```

즉, 정확한 전체 의미 추출보다 **근거와 구조의 안전성**을 먼저 검증했다.

## 6.2 필요한 규칙과 기준이 없었음

다음 기준이 아직 확정되지 않았다.

- WorkUnit·Artifact·InformationObject의 구분 기준
- Actor·Organization의 구분 기준
- 표의 Activity·Output·Input·Role 처리 기준
- 일반 문장의 주어·목적어 경계
- `HAS_INPUT`과 `PRODUCES_OUTPUT`의 동사 기준

## 6.3 전문가 Gold와 충분한 검증 데이터가 없었음

의미 정확도를 측정할 전문가 Gold가 없으며 fresh VALIDATION도 8건뿐이다.

그러나 앞으로의 파일럿 목표는 정확도 평가가 아니라 자동 생성 완주이므로, 이 부족을 구현 중단 사유로 사용하지 않으려 한다.

---

# 7. 향후 파일럿의 최종 목표

향후 파일럿의 목표는 다음과 같다.

> **사람 개입 없이 자이제_1 데이터만 입력하여 처음부터 끝까지 KG를 생성한다. 생성 결과가 정답인지 여부와 관계없이 전체 파이프라인을 완주한다.**

구체적인 조건은 다음과 같다.

```text
입력 데이터: 자이제_1.xlsx만 사용
사람 annotation: 0
사람 중간 수정: 0
전문가 판정: 완료 조건에서 제외
출력: KG JSONL, RDF, Neo4j CSV, 실제 Neo4j graph
```

정확도와 관계없이 생성하되 결과에는 다음 정보를 남긴다.

```text
generation_method
rule_id
confidence
status = AUTOMATED_UNVERIFIED
evidence_anchor_ids
```

따라서 잘못됐을 가능성이 있는 결과도 삭제하지 않고 confidence와 생성 규칙을 붙여 보존한다.

---

# 8. 향후 파일럿 방법론의 단순화 원칙

방법론이 지나치게 복잡해지는 것을 방지하기 위해 다음만 사용한다.

```text
기존 Anchor
+ 표 header 규칙
+ 소수의 문장 정규식
+ 고정 타입·관계 schema
+ domain/range와 provenance 검사
```

사용하지 않을 것은 다음과 같다.

- 복잡한 embedding clustering
- 여러 모델을 조합한 ensemble
- 다중 agent
- 반복적인 threshold 최적화
- 자유 생성형 LLM ontology extraction
- 사람-in-the-loop
- 근거 없는 taxonomy 생성

LLM 사용 여부는 선택 사항이다. 사용하더라도 새로운 개념·관계를 만들게 하지 않고 고정 선택지만 판정하게 한다.

---

# 9. 향후 파일럿의 최소 타입과 관계

## 9.1 타입

방법론을 단순하게 유지하기 위해 다음 5개 타입에 집중한다.

```text
WorkUnit
Actor
Organization
Artifact
InformationObject
```

## 9.2 관계

다음 4개 관계만 우선 생성한다.

```text
PERFORMED_BY
HAS_INPUT
PRODUCES_OUTPUT
PRECEDES
```

새로운 관계명은 자동 생성하지 않는다.

---

# 10. 향후 파일럿의 단순 자동 규칙

## 10.1 표 구조 우선

| 표 header | 자동 타입 |
|---|---|
| 활동, Activity, 단계, Step | WorkUnit |
| 결과물, Output, Deliverable | Artifact |
| 입력, Input, 참고자료 | InformationObject 또는 Artifact |
| 담당, Role, 수행자, 책임자 | Actor 또는 Organization |

같은 행에서는 다음 관계를 자동 생성한다.

```text
Activity → Output = PRODUCES_OUTPUT
Activity → Input  = HAS_INPUT
Activity → Role   = PERFORMED_BY
```

예:

| 활동 | 담당 | 입력 | 결과물 |
|---|---|---|---|
| 제안서 작성 | 제안팀 | 고객 요구조건 | 제안서 초안 |

자동 후보:

```text
제안서 작성       → WorkUnit
제안팀            → Actor 또는 Organization
고객 요구조건     → InformationObject
제안서 초안       → Artifact
```

자동 관계:

```text
제안서 작성 ──PERFORMED_BY─────> 제안팀
제안서 작성 ──HAS_INPUT────────> 고객 요구조건
제안서 작성 ──PRODUCES_OUTPUT──> 제안서 초안
```

## 10.2 일반 문장

다음처럼 단순하고 명확한 패턴만 우선 처리한다.

```text
X가 Y를 작성한다
X가 Y를 분석한다
X가 Y를 검토한다
X가 Y를 제출한다
```

예:

```text
“제안팀이 제안서 초안을 작성한다.”
```

자동 후보:

```text
제안팀             → Actor 또는 Organization
제안서 초안 작성   → WorkUnit
제안서 초안        → Artifact
```

문장 경계가 불명확해도 파이프라인은 중단하지 않는다. 낮은 confidence로 보존한다.

---

# 11. 향후 End-to-End 실행 단계

교수님 검토 후 다음 순서로 진행하고자 한다.

## Phase 1. 입력

- 자이제_1 전체 데이터 로드
- source hash 기록
- 기존 Anchor 규칙 재사용

## Phase 2. Mention 후보

- 표 header 기반 후보 생성
- 소수 문장 정규식 기반 후보 생성
- 모든 후보에 원문 위치 저장

## Phase 3. 타입

- 5개 타입 중 하나 자동 부여
- 명확한 표 구조: HIGH confidence
- 일반 문장 규칙: MEDIUM 또는 LOW confidence

## Phase 4. 관계

- `PERFORMED_BY`
- `HAS_INPUT`
- `PRODUCES_OUTPUT`
- `PRECEDES`

## Phase 5. 구조 검사

- edge endpoint 존재
- domain/range
- Evidence Anchor 존재
- 원문 offset 일치

## Phase 6. 전체 KG

- 전체 데이터 적용
- 정확도와 관계없이 모든 자동 결과 보존
- `AUTOMATED_UNVERIFIED` 표시

## Phase 7. RDF·Neo4j

- RDF 생성·재파싱
- SHACL 검사
- `nodes.csv`, `edges.csv` 생성
- 실제 Neo4j import
- 핵심 query와 시각화 생성

## Phase 8. 최종 보고

- 자동 생성 수
- HIGH·MEDIUM·LOW 결과 수
- 대표적인 정상·오류 가능 사례
- 구조 검증 결과
- 의미 정확도 미검증 명시

---

# 12. 향후 파일럿 완료 기준

이번 파일럿은 정확도 기준이 아니라 다음 End-to-End 기준으로 완료 여부를 판단한다.

- [ ] 자이제_1 전체 데이터 자동 입력
- [ ] 사람 annotation 0
- [ ] 사람 중간 수정 0
- [ ] Mention 자동 생성
- [ ] 5개 타입 자동 생성
- [ ] 4개 관계 자동 생성
- [ ] 모든 결과에 rule ID와 confidence 저장
- [ ] 모든 관계에 Evidence Anchor 저장
- [ ] RDF 생성
- [ ] Neo4j nodes.csv·edges.csv 생성
- [ ] 실제 Neo4j import
- [ ] query와 시각화 생성
- [ ] 최종 보고서 생성

정확도가 낮거나 일부 결과가 잘못됐더라도 전체 파이프라인이 끝까지 실행되면 파일럿 목표를 달성한 것으로 본다.

이 경우 최종 상태는 다음처럼 표기한다.

```text
AUTOMATED_E2E_PASS
AUTOMATED_UNVERIFIED
NO_HUMAN_GOLD
ACCURACY_NOT_CLAIMED
```

---

# 13. 교수님께 확인받고 싶은 사항

## 질문 1

파일럿의 우선 목표를 의미 정확도보다 **사람 개입 없는 전체 KG 생성 파이프라인 완주**로 설정해도 되는가?

## 질문 2

파일럿 단계에서는 결과가 틀릴 가능성이 있더라도 삭제하지 않고 다음 정보와 함께 보존해도 되는가?

```text
confidence
rule_id
AUTOMATED_UNVERIFIED
원문 Evidence
```

## 질문 3

방법론을 다음 수준으로 제한해도 되는가?

```text
표 구조
소수 정규식
5개 타입
4개 관계
구조·provenance 검사
```

## 질문 4

자동 KG가 완성된 이후에 의미 정확도 평가와 전문가 검토를 별도 후속 연구로 분리해도 되는가?

---

# 14. 최종 요약

## 현재까지 완료

```text
Excel 원문 보존
→ Anchor 분리
→ 규칙·조건·수량·alias·일부 행동 추출
→ 명시 alias 정규화
→ 일부 정의·조건·순서 관계
→ RDF·Neo4j 변환과 원문 추적 검증
```

## 현재 미구현

```text
일반 명사구 Mention
→ Actor·Artifact·InformationObject 유형화
→ 주어·입력·산출물 관계
→ 완전 자동 업무 의미 KG
```

## 교수님 검토 후 진행하려는 목표

```text
자이제_1 전체 데이터
→ 사람 개입 0
→ 단순 규칙 기반 자동 타입·관계 생성
→ 정확도와 관계없이 전체 KG 보존
→ RDF
→ Neo4j
→ 시각화와 최종 보고
```

> **파일럿에서는 방법을 복잡하게 만들지 않고, 자이제_1 데이터만으로 사람 개입 없이 처음부터 끝까지 KG를 생성하는 것을 우선 목표로 한다. 의미 정확도 평가는 자동 KG 완성 이후의 별도 단계로 둔다.**

