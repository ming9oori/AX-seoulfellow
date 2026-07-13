# 자이제 온톨로지 파일럿 진행 현황 및 단순 End-to-End 후속 실행 지시서

작성일: 2026-07-12  
현재 실험: `zaije_r5_crsi_v_20260712_v1`  
현재 공식 판정: `DETERMINISTIC_CRSI_ONLY_PASS`  
문서 목적: **교수님께 현재까지 실제로 구현된 범위와 부족한 범위를 보고하고, 파일럿을 단순한 방법으로 끝까지 완주하기 위한 후속 실행 범위를 확인받기 위함**

---

# 0. 최종 목표와 최우선 실행 원칙

이 문서의 모든 후속 지시는 다음 목표를 최우선으로 해석한다.

> **사람의 판정이나 수작업 annotation 없이, 자이제_1 Excel 전체를 입력하면 원문 분리부터 Mention·타입·관계 생성, RDF, Neo4j CSV, 실제 Neo4j 적재와 시각화까지 자동으로 완료되는 KG 생성 파이프라인을 만든다.**

이번 파일럿의 성공 기준은 정답률이 아니다.

```text
입력: 자이제_1.xlsx
사람 개입: 0
중간 수작업 수정: 0
출력: 끝까지 생성된 KG와 Neo4j 입력 파일
```

정답 여부가 불확실해도 파이프라인을 중단하지 않는다. 대신 각 결과에 다음 정보를 붙인다.

```text
generation_method
rule_id
confidence
status = AUTOMATED_UNVERIFIED
evidence_anchor_ids
```

모호한 후보는 operational graph에서 삭제하는 대신 `LOW_CONFIDENCE` 또는 `UNDERDETERMINED` 상태로 그래프에 보존할 수 있다. 인간 검토와 전문가 Gold 평가는 **자동 KG 완성 이후의 별도 후속 평가**이며, 이번 파일럿의 완료 조건이 아니다.

방법론은 다음보다 복잡해지지 않도록 제한한다.

```text
표 header 규칙
+ 소수의 문장 정규식
+ 고정 타입·관계 schema
+ domain/range와 provenance 검사
```

embedding, 복잡한 clustering, 다중 agent, 인간-in-the-loop를 도입하지 않는다.

---

# 1. 교수님께 먼저 보고드릴 핵심 내용

## 1.1 현재까지 무엇을 만들었는가

현재까지 만든 것은 완성된 수주·제안 온톨로지가 아니라 다음 결과물이다.

> **Excel 원문을 문장·표 셀·목록 단위로 추적하고, 명시적인 규칙·조건·수량·동의어·일부 행동을 그래프로 표현한 뒤 RDF와 Neo4j까지 변환한 보수적 온톨로지 코어 v0.2**

현재 시스템은 다음을 수행할 수 있다.

1. Excel의 어느 행에서 지식이 나왔는지 추적한다.
2. 원문 안의 정확한 문자 위치를 Anchor로 보존한다.
3. `반드시`, `해야 한다`, `만약`, `경우`, `30점 이상` 같은 명시 표현을 찾는다.
4. `한글명(영문명)` 형태의 명시 alias를 하나의 개념으로 정리한다.
5. 일부 명시적 순서·정의·조건·템플릿 관계를 만든다.
6. RDF·SHACL·Neo4j로 변환하고 구조와 provenance를 검사한다.

## 1.2 아직 무엇을 만들지 못했는가

다음 기능은 아직 충분히 구현되지 않았다.

```text
제안팀         → Actor
제안서 초안    → Artifact
고객 요구조건  → InformationObject
제안서 작성    → WorkUnit
```

그리고 다음 관계도 아직 일반적으로 만들지 못한다.

```text
제안서 작성 ──PRODUCES_OUTPUT──> 제안서 초안
제안서 작성 ──HAS_INPUT────────> 고객 요구조건
제안서 작성 ──PERFORMED_BY─────> 제안팀
```

즉, 현재는 **근거 추적과 일부 명시 표현은 구현됐지만, 일반적인 업무 개념 유형화와 주체·입력·산출물 관계 추출은 미완성**이다.

## 1.3 왜 아직 구현하지 못했는가

앞선 실험은 다음 순서로 위험을 줄이는 데 초점을 두었다.

```text
원문 위치가 정확한가?
→ 규칙·조건·사례를 구별할 수 있는가?
→ 명시 alias를 안전하게 병합할 수 있는가?
→ 그래프가 원문까지 추적되는가?
```

따라서 일반 명사구, 행위의 주어·목적어, Artifact·Actor 유형화는 다음 단계로 남았다. 또한 다음 자원이 없었다.

- Actor·Artifact·InformationObject를 구분하는 확정된 annotation guideline
- 전문가가 판정한 타입 Gold
- 주어·목적어·입력·산출물을 찾는 parser 또는 labeling function
- 충분한 fresh VALIDATION 데이터

---

# 2. 현재 데이터와 실험 통제 상태

## 2.1 입력 데이터

- 사용자 지정 원본: `handoff-hanyang/수주제안/자이제_1.xlsx`
- 전체 레코드: 1,366개
- 전체 non-TEST 시연 그래프 입력: 953개
  - INDUCTION: 681개
  - VALIDATION: 272개
- TEST 접근: 0개

기존 R4 원본과 사용자 지정 Excel은 바이너리 해시는 달랐지만 워크시트, 행 번호, 1,366개 논리 텍스트가 모두 동일함을 확인했다.

## 2.2 현재 검증 데이터 한계

R1~R4에서 노출된 Evidence와 같은 leakage group을 제외한 결과 fresh VALIDATION은 8건·7개 그룹만 남았다.

따라서 다음은 가능하다.

- 코드가 같은 입력에서 같은 결과를 내는지 확인
- 원문 위치·provenance·domain/range 위반 검사
- 명시 alias와 명시 관계의 engineering 검증

다음은 아직 불가능하다.

- 모집단 수준 의미 정확도 추정
- 전문가 수준의 타입 정확도 주장
- 다른 문서·다른 산업으로의 일반화 주장

후속 파일럿에서도 이 한계를 숨기지 않는다. 다만 파일럿 단계이므로 데이터 부족이나 Gold 부재를 이유로 구현을 중단하지 않고, **자이제_1 전체 1,366행에 전체 파이프라인을 끝까지 실행한 뒤 결과를 `AUTOMATED_UNVERIFIED_PILOT`으로 분류**한다.

---

# 3. 현재 Anchor 분리 방법

## 3.1 Anchor의 목적

Anchor는 의미적으로 완전한 개념이 아니라, 나중에 원문을 정확히 다시 찾기 위한 최소 근거 구간이다.

## 3.2 일반 문장

다음 기준에서 문장을 나눈다.

```text
마침표, 물음표, 느낌표, 줄바꿈
```

긴 문장은 다음과 같은 강한 연결 표현에서만 추가로 나눈다.

```text
그러나, 하지만, 따라서, 또한, 그리고, 세미콜론
```

모든 쉼표에서 자르지 않는다. 한국어 술어 단위가 과도하게 분리되는 것을 막기 위해서다.

예:

```text
원문:
“제안서를 작성해야 한다. 그러나 제출 전에는 반드시 리뷰해야 한다.”

Anchor 1:
“제안서를 작성해야 한다.”

Anchor 2:
“그러나 제출 전에는 반드시 리뷰해야 한다.”
```

## 3.3 표

Markdown 표는 셀 단위로 분리한다.

예:

```text
| 활동 | 결과물 |
| 제안서 작성 | 제안서 초안 |
```

생성 결과:

```text
Anchor: 제안서 작성
Context: Column Header = 활동

Anchor: 제안서 초안
Context: Column Header = 결과물
Context: Row Header = 제안서 작성
```

셀 안의 `<br>`과 bullet은 추가로 분리한다. `-`, 숫자만 있는 셀, 표 구분선은 제외한다.

## 3.4 목록

다음 기호를 목록 항목으로 인식한다.

```text
-, *, •, ▪, 1., 2)
```

목록 제목과 이전 항목 설명은 ContextSpan으로 연결한다.

## 3.5 현재 Anchor 결과

전체 non-TEST 953개 Evidence에서 다음을 생성했다.

| 구조 | Anchor 수 |
|---|---:|
| 일반 문장·절 | 907 |
| 표 셀 | 410 |
| 목록 항목 | 163 |
| 합계 | 1,480 |

모든 Anchor는 원문의 `start_char:end_char`와 저장 문자열이 일치하는지 검사했다.

---

# 4. 현재 Mention 추출 방법

현재 Mention은 LLM이나 범용 NER가 아니라 사람이 작성한 정규식 규칙으로 찾는다.

## 4.1 CueMention

| 의미 | 대표 패턴 |
|---|---|
| 의무 | 반드시, 해야 한다, 필수, 요구된다 |
| 권고 | 권장한다, 바람직하다, 하는 것이 좋다 |
| 금지 | 해서는 안 된다, 금지한다, 피해야 한다 |
| 조건 | 경우, 때, 만약, 이전, 이후 |
| 예외 | 단, 다만, 예외적으로 |
| 부정 | 아니다, 않는다, 못한다, 없다 |
| 사례 | 예를 들어, 예시, 사례, 가령 |
| 정의 | 이란, 의미한다, 정의한다 |
| 템플릿 | 템플릿, 양식, 서식 |

예:

```text
“제안서는 반드시 제출 전에 검토해야 한다.”

반드시     → 의무 CueMention
제출 전    → 조건 CueMention
해야 한다  → 의무 CueMention
```

## 4.2 QuantityMention

다음 형태를 찾는다.

```text
최소 3명
30점 이상
3~6개월
20%
2년
```

숫자, 최소·최대, 범위, 단위, 이상·이하 정보를 저장한다.

## 4.3 AliasMention

다음 형태를 찾는다.

```text
한글 표현(영문 표현)
```

예:

```text
제안 요청서(Request for Proposal)
핵심 이슈(Hot Button)
```

## 4.4 ActionMention

다음 종결 표현을 가진 구간을 행동 후보로 찾는다.

```text
해야 한다, 한다, 된다, 수립한다, 작성한다,
분석한다, 평가한다, 선정한다, 도출한다
```

현재는 종결 표현 앞쪽의 긴 문자열이 함께 추출될 수 있다. 따라서 정확한 동사와 목적어 경계 추출은 아직 부족하다.

## 4.5 현재 Mention 추출의 한계

현재 시스템에는 모든 일반 명사구를 찾는 기능이 없다.

```text
제안팀
제안서 초안
고객 요구조건
평가위원
```

이 표현들은 alias, 수량, action 등의 기존 패턴에 걸리지 않으면 독립 Mention으로 안정적으로 추출되지 않는다.

---

# 5. 현재 개념 유형화 방법

현재 개념 유형화는 학습 모델이 아니라 R4 노드 타입을 R5 타입으로 바꾸는 고정표다.

```text
ExplicitProcessStep → WorkUnit
ActionMention       → WorkUnit
ExplicitDeonticRule → Rule
ExplicitCondition   → Condition
ExplicitException   → Condition
QuantityConstraint  → Metric
QuantityMention     → Metric
TemplateField       → TemplateField
ExampleInstance     → ExampleInstance
Concept             → DomainConcept 후보
Alias               → DomainConcept의 표면형
```

현재 전체 그래프의 WorkUnit 299개는 다음으로 구성된다.

```text
ActionMention 223개
ExplicitProcessStep 76개
```

Metric 178개는 다음으로 구성된다.

```text
QuantityMention 89개
QuantityConstraint 89개
```

## 5.1 중요한 현재 문제

Anchor 분리기는 표의 Column Header를 보존하지만, 현재 타입 부여기는 이를 사용하지 않는다.

따라서 현재는 다음 규칙이 없다.

```text
Activity 열 → WorkUnit
Output 열   → Artifact
Role 열     → Actor
Input 열    → InformationObject
```

일반 표 셀은 폭넓은 규칙 때문에 `TemplateField`가 될 수 있다. 기존 결과에서 일부 긴·부정확한 TemplateField label이 나타난 이유가 이것이다.

## 5.2 현재 만들어지지 않은 주요 타입

schema에는 다음 타입이 정의돼 있지만 최종 B1에서 일반적으로 추출되지 않았다.

```text
Actor
Organization
Artifact
InformationObject
Method
Strategy
DecisionCriterion
```

---

# 6. 현재 실제로 생성된 관계

전체 non-TEST B1 canonical graph의 주요 registry 관계는 다음과 같다.

| 관계 | 수 | 생성 근거 |
|---|---:|---|
| `HAS_ALIAS` | 166 | 명시 괄호 alias |
| `PRECEDES` | 55 | 명시 단계·순서 |
| `HAS_DEFINITION` | 17 | 명시 정의 cue |
| `HAS_FIELD` | 7 | 템플릿 cue와 같은 Evidence의 표 구조 |
| `HAS_CONDITION` | 4 | 같은 Anchor의 Rule·Condition |

현재 최종 B1에는 다음 일반 관계가 없다.

```text
PRODUCES_OUTPUT
HAS_INPUT
PERFORMED_BY
```

따라서 현재 Neo4j 그래프는 크기가 4,767 nodes / 10,738 relationships이지만, 이 중 상당수는 Evidence, Anchor, Context, Mention, provenance 관계다. 노드와 관계 수가 많다는 사실을 완성된 업무 의미 그래프로 해석해서는 안 된다.

---

# 7. 현재 개념 정규화 방법

현재 잘 구현된 의미 정리 기능은 명시 alias 통합이다.

## 7.1 문자열 정규화

다음을 적용한다.

```text
Unicode NFKC
영문 casefold
공백 정리
일부 구두점 통일
/, -, _ 주변 표기 통일
```

## 7.2 Hard-positive

다음만 결정적으로 병합한다.

```text
원문의 명시 괄호 alias
같은 정규형의 명시 alias
동일 타입의 확실한 exact match
```

## 7.3 Hard-negative

다음 타입은 병합하지 않는다.

```text
WorkUnit–Metric
Template–TemplateField
Actor–Artifact
ExampleInstance–DomainConcept
```

## 7.4 Gray-zone

관련성은 있지만 동일 개념인지 불명확한 후보는 자동 병합하지 않는다.

```text
SAME_CONCEPT
RELATED_NOT_SAME
DIFFERENT_CONCEPT
UNDERDETERMINED
```

선택적 LLM도 이 선택지 안에서만 판정하고 최종 타입·Evidence gate를 다시 통과해야 한다.

---

# 8. 현재 비교 실험 결과

## 8.1 비교 시스템

| 시스템 | 방법 |
|---|---|
| B0 | 표면형을 분리한 baseline |
| B1 | 명시 규칙·타입·제약만 사용 |
| B2 | B1 + 일부 gray 후보 LLM 판정 |
| B3 | B1 + gray 후보 전수 LLM 판정 |
| B4 | LLM 직접 개념·관계 생성 baseline |

## 8.2 DEV 결과

| 지표 | B1 | B2 | B3 | B4 |
|---|---:|---:|---:|---:|
| safe ontology yield | 88 | 104 | 128 | 140 |
| critical violation | 0 | 0 | 0 | 82 |
| unsupported label rate | 0% | 0% | 0% | 12.08% |

- B2/B1 yield 증가: 18.18%
- B2/B3 yield 비율: 81.25%
- B2/B3 token 비율: 55.27%
- 사전 token 기준: 35% 이하
- LLM 반복 일치도: 21/21 = 1.00

B2는 품질 수치는 증가했지만 비용 기준을 통과하지 못했다. 따라서 B1을 canonical system으로 선택했다.

## 8.3 Fresh VALIDATION 결과

- Evidence: 8건
- leakage groups: 7개
- gray 후보: 0개
- B1 critical violation: 0
- B4 critical violation: 2
- B4 unsupported label rate: 19.35%

표본이 너무 작으므로 독립성은 유지했지만 모집단 성능 주장은 불가능하다.

---

# 9. 현재 RDF·Neo4j 결과

전체 INDUCTION+VALIDATION 953건을 B1으로 재구축한 시연 그래프는 다음과 같다.

| 항목 | 값 |
|---|---:|
| nodes | 4,767 |
| relationships | 10,738 |
| canonical concepts | 139 |
| surface mentions | 302 |
| 정리된 표면 중복 | 204 |
| 명시 alias 회수 | 166/166 |
| RDF triples | 87,023 |
| SHACL critical violation | 0 |

실제 Neo4j Community 4.4.43에 적재해 다음을 확인했다.

- node coverage: 1.00
- relationship coverage: 1.00
- registry relation provenance: 249/249
- Rule→Anchor: 45/45
- Concept→Mention: 139/139
- 필수 visualization query: 6/6 non-empty

이 결과는 **구조와 추적 가능성의 검증 결과**다. 전체 업무 개념과 관계의 의미 정확도를 검증한 결과는 아니다.

---

# 10. 후속 파일럿의 목적

다음 파일럿은 지금까지 비어 있던 최소 업무 의미 구조를 끝까지 구현한다.

## 10.1 한 문장 목표

> 표와 명시적인 일반 문장에서 WorkUnit, Actor, Artifact, InformationObject를 찾고, `PERFORMED_BY`, `HAS_INPUT`, `PRODUCES_OUTPUT`, `PRECEDES`를 Evidence와 함께 생성하여 Neo4j까지 검증한다.

## 10.2 이번 후속 파일럿에서만 다룰 타입

방법론 복잡도를 막기 위해 다음 5개로 제한한다.

```text
WorkUnit
Actor
Organization
Artifact
InformationObject
```

기존 Rule·Condition·Metric은 입력으로 보존하지만 신규 유형화 실험의 목표로 확장하지 않는다.

## 10.3 이번 후속 파일럿에서만 다룰 관계

다음 4개로 제한한다.

```text
PERFORMED_BY
HAS_INPUT
PRODUCES_OUTPUT
PRECEDES
```

새로운 관계명은 만들지 않는다.

---

# 11. 후속 파일럿의 단순 방법론

## 11.1 최우선 근거: 표의 열 제목

복잡한 의미 모델보다 명시적인 표 구조를 우선한다.

| 열 제목 | 타입 또는 관계 |
|---|---|
| 활동, Activity, 단계, Step | 셀 값을 `WorkUnit` 후보로 생성 |
| 결과물, Output, Deliverable | 셀 값을 `Artifact` 후보로 생성 |
| 입력, Input, 참고자료 | 셀 값을 `InformationObject` 후보로 생성 |
| 담당, Role, 수행자, 책임자 | 셀 값을 `Actor/Organization` 후보로 생성 |

같은 표 행에서 다음 관계를 만든다.

```text
Activity → Output  = PRODUCES_OUTPUT
Activity → Input   = HAS_INPUT
Activity → Role    = PERFORMED_BY
```

예:

| 활동 | 담당 | 입력 | 결과물 |
|---|---|---|---|
| 제안서 작성 | 제안팀 | 고객 요구조건 | 제안서 초안 |

생성 후보:

```text
제안서 작성       = WorkUnit
제안팀            = Actor
고객 요구조건     = InformationObject
제안서 초안       = Artifact

제안서 작성 ──PERFORMED_BY─────> 제안팀
제안서 작성 ──HAS_INPUT────────> 고객 요구조건
제안서 작성 ──PRODUCES_OUTPUT──> 제안서 초안
```

## 11.2 일반 문장: 소수의 명시 패턴만 허용

다음처럼 주어·목적어·행동이 명확한 문장만 처리한다.

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

후보:

```text
Actor: 제안팀
WorkUnit: 제안서 초안 작성
Artifact: 제안서 초안
PERFORMED_BY: 제안서 초안 작성 → 제안팀
PRODUCES_OUTPUT: 제안서 초안 작성 → 제안서 초안
```

문장 구조가 명확하지 않으면 추출하지 않는다.

## 11.3 Artifact·InformationObject의 단순 구분

```text
문서·초안·계획서·보고서·표·템플릿·체크리스트
→ Artifact

요구조건·핵심 이슈·평가 기준·분석 정보·고객 정보
→ InformationObject
```

둘이 충돌하면 `UNDERDETERMINED`로 남긴다. 복잡한 다중 상속을 도입하지 않는다.

## 11.4 Actor·Organization의 단순 구분

```text
팀·부서·회사·기관·위원회
→ Organization

대표·담당자·평가위원·PM·작성자
→ Actor
```

모호하면 두 타입을 억지로 선택하지 않고 보류한다.

---

# 12. 방법론 복잡도 제한 지시

후속 파일럿은 다음 원칙을 반드시 지킨다.

## 12.1 도입하지 않을 것

- embedding 기반 대규모 clustering
- 복잡한 가중치 조합과 반복 threshold 튜닝
- 자유 생성형 LLM ontology extraction
- 새로운 관계명 자동 생성
- 다단계 agent orchestration
- 근거 없는 상위·하위 taxonomy 생성
- 여러 parser·모델의 복잡한 ensemble

## 12.2 사용할 것

- 기존 Anchor와 ContextSpan
- 표의 명시적 열 구조
- 소수의 해석 가능한 정규식
- 5개 핵심 타입
- 4개 핵심 관계
- domain/range 검사
- Evidence Anchor 필수 조건
- 모호할 때 abstain

## 12.3 LLM 사용 원칙

LLM은 필수 요소가 아니다. 결정적 규칙으로 처리할 수 없는 후보가 있을 때만 다음 고정 선택지를 사용한다.

```text
WORK_UNIT
ACTOR
ORGANIZATION
ARTIFACT
INFORMATION_OBJECT
UNDERDETERMINED
```

관계 선택지도 다음으로 제한한다.

```text
PERFORMED_BY
HAS_INPUT
PRODUCES_OUTPUT
PRECEDES
NONE
UNDERDETERMINED
```

LLM은 새로운 label, quote, type, relation을 생성하지 않는다. 파일럿 API 상한을 사전에 고정하고 결과를 본 뒤 늘리지 않는다.

## 12.4 단순성 판단 기준

다음 질문에 한 문장으로 답할 수 없는 규칙은 도입하지 않는다.

```text
이 타입은 어떤 원문 근거 때문에 붙었는가?
이 관계는 어떤 표 열 또는 문장 패턴 때문에 생성됐는가?
왜 이 후보는 보류됐는가?
```

---

# 13. 후속 파일럿의 실행 단계

이 문서는 제안서로 끝나는 문서가 아니라 실제 구현·실행 지시서다. 다음 단계를 중간에 멈추지 않고 끝까지 수행한다.

## Phase 1. 입력 감사

- 현재 R5 B1 graph와 source hash 고정
- 기존 결과를 덮어쓰지 않는 새 experiment ID 생성
- TEST 접근 0 확인
- Activity·Output·Input·Role header 사전 고정
- 타입·관계 registry 고정

권장 experiment ID:

```text
zaije_simple_e2e_pilot_20260712_v1
```

## Phase 2. 구조 기반 Mention 생성

- 표의 header와 각 cell을 연결
- Activity cell → WorkUnit candidate
- Output cell → Artifact candidate
- Input cell → InformationObject candidate
- Role cell → Actor/Organization candidate
- 각 후보에 Evidence·Anchor·header 근거 저장

## Phase 3. 단순 문장 패턴 적용

- `X가 Y를 작성/분석/검토/제출한다` 패턴만 우선 적용
- 주어, 목적어, 행동 span을 각각 저장
- 조사·동사 경계가 불명확하면 보류

## Phase 4. 타입 판정

- 구조 규칙과 소형 lexicon이 일치하면 hard type
- 한 규칙만 지지하면 candidate
- 충돌하면 underdetermined
- 타입별 생성 이유를 `typing_rule_id`로 저장

## Phase 5. 관계 생성

- 같은 표 행의 Activity–Output/Input/Role을 연결
- 일반 문장은 같은 Anchor 안에서만 연결
- domain/range와 Evidence를 검사
- 위반 관계는 operational graph에 넣지 않음

## Phase 6. 자동 파일럿 평가

- 표 기반 explicit reference를 자동 생성
- 유형별 사례를 나중에 확인할 수 있는 audit queue로 자동 출력하되 이번 실행에서는 사람이 판정하지 않음
- `AUTOMATED_UNVERIFIED_PILOT`과 `NO_HUMAN_GOLD`를 명시
- 오류 예시와 보류 예시를 함께 보고

## Phase 7. 전체 non-TEST 실행

- INDUCTION+VALIDATION 전체 적용
- 타입·관계·abstention 수 집계
- 기존 R5 provenance backbone과 결합
- 이전 그래프를 덮어쓰지 않음

## Phase 8. RDF·Neo4j

- RDF 재파싱
- SHACL 검사
- Neo4j nodes/edges CSV 생성
- 실제 Neo4j import
- WorkUnit→Actor/Input/Output view 생성
- 원문 Evidence trace 확인

## Phase 9. 최종 보고

- 방법론
- 정확한 규칙 목록
- 추출 예시
- 오류 예시
- 타입·관계 수
- abstention 수
- Neo4j 검증
- 한계
- 다음 실험 권고

구현이 끝나지 않았다는 이유로 분석 문서만 남기고 중단하지 않는다. 오류가 있더라도 파일럿 결과와 실패 원인을 보존하고 최종 상태를 `PASS`, `PARTIAL_PASS`, `REVISE` 중 하나로 판정한다.

---

# 14. 후속 파일럿 성공 기준

파일럿은 통계적 논문 성능이 아니라 전체 파이프라인 동작 여부를 확인한다.

## 14.1 필수 Gate

```text
Anchor offset round-trip = 1.00
모든 promoted type에 Evidence Anchor 존재
모든 promoted relation에 Evidence Anchor 존재
domain/range violation = 0
orphan node·relation = 0
TEST 접근 = 0
재실행 hash stability = 1.00
RDF parse = PASS
Neo4j node coverage = 1.00
Neo4j relationship coverage = 1.00
```

## 14.2 최소 기능 Gate

다음이 각각 1개 이상 실제로 생성돼야 한다.

```text
WorkUnit
Actor 또는 Organization
Artifact
InformationObject
PERFORMED_BY
HAS_INPUT
PRODUCES_OUTPUT
PRECEDES
```

해당 관계의 명시 근거가 데이터에 전혀 없으면 0개를 실패로 숨기지 않고 `SOURCE_SUPPORT_NOT_FOUND`로 보고한다.

## 14.3 의미 평가 표기

전문가 Gold가 없으면 다음 용어를 사용하지 않는다.

```text
전문가 수준 정확도
완성된 온톨로지
검증된 의미 정답
```

대신 다음처럼 표기한다.

```text
PRELIMINARY PILOT
engineering-validated
explicit-structure reference
human semantic audit pending
```

---

# 15. 후속 파일럿 필수 산출물

```text
experiment_root/
├── data/
│   ├── membership.jsonl
│   ├── anchors.jsonl
│   └── explicit_structure_reference.jsonl
├── candidates/
│   ├── mentions.jsonl
│   ├── typed_candidates.jsonl
│   └── relation_candidates.jsonl
├── reference/
│   ├── typing_rules.yaml
│   ├── relation_rules.yaml
│   ├── audit_queue.jsonl
│   └── status.json
├── runs/
│   ├── deterministic/
│   └── optional_closed_choice_llm/
├── graphs/
│   ├── rdf/canonical.ttl
│   ├── shacl/
│   └── neo4j/nodes.csv, edges.csv
├── visualization/
│   ├── workunit_actor.svg
│   ├── workunit_input_output.svg
│   └── evidence_trace.svg
├── evaluation/
│   ├── type_metrics.json
│   ├── relation_metrics.json
│   └── gate_summary.json
└── reports/
    ├── methodology.md
    ├── results.md
    └── final_report.md
```

모든 파일에는 experiment ID와 source hash를 기록한다.

---

# 16. 파일럿 Definition of Done

다음 항목이 모두 완료돼야 파일럿을 끝낸 것으로 본다.

- [ ] 기존 R5 결과를 변경하지 않는 새 experiment 생성
- [ ] 5개 타입과 4개 관계 schema 잠금
- [ ] 표 header 기반 Mention·타입 규칙 구현
- [ ] 최소 일반 문장 패턴 구현
- [ ] 타입 후보와 관계 후보 전체 생성
- [ ] 모든 후보에 Anchor와 rule ID 저장
- [ ] domain/range·orphan·offset 검사
- [ ] 오류·보류 사례 audit queue 자동 생성, 사람 판정 0
- [ ] 자이제_1 전체 1,366행 적용
- [ ] RDF·SHACL 생성 및 검증
- [ ] Neo4j CSV 생성
- [ ] 실제 Neo4j import와 coverage 검사
- [ ] 세 가지 필수 시각화 생성
- [ ] 방법론·결과·한계 최종 보고서 작성
- [ ] `PASS`, `PARTIAL_PASS`, `REVISE` 최종 판정
- [ ] API key 저장 0 및 secret scan
- [ ] TEST 접근 0 확인

데이터 부족, Gold 부재, 낮은 confidence는 파일럿을 중단하는 이유가 아니다. 그 경우에도 전체 단계는 실행하고 결과를 `AUTOMATED_E2E_PASS`, `PARTIAL_PASS`, `REVISE` 중 하나로 기록한다. `AUTOMATED_E2E_PASS`는 정확도가 맞다는 뜻이 아니라 무인 파이프라인이 끝까지 완료됐다는 뜻이다.

---

# 17. 교수님께 확인받고 싶은 사항

## 질문 1

다음 파일럿의 목표를 **완성된 전체 온톨로지**가 아니라, 아래 최소 구조의 End-to-End 구현으로 두어도 되는가?

```text
WorkUnit
Actor/Organization
Artifact
InformationObject
PERFORMED_BY
HAS_INPUT
PRODUCES_OUTPUT
PRECEDES
```

## 질문 2

방법론 복잡도를 억제하기 위해 다음 원칙을 적용해도 되는가?

```text
표 구조 우선
소수의 정규식
모호하면 abstain
LLM은 선택형 보조 판정만 수행
embedding·agent·복잡한 ensemble은 사용하지 않음
```

## 질문 3

전문가 Gold가 없는 상태에서는 명시적인 표 구조를 임시 reference로 사용하고 결과를 `PRELIMINARY PILOT`로 보고해도 되는가?

## 질문 4

파일럿 완료 후 교수님 또는 업무 전문가가 우선 검토할 audit 대상을 다음 순서로 두어도 되는가?

```text
1. WorkUnit–Artifact 구분
2. Artifact–InformationObject 구분
3. Actor–Organization 구분
4. PRODUCES_OUTPUT·HAS_INPUT·PERFORMED_BY 관계
```

---

# 18. 최종 요약

## 지금까지 한 일

```text
원문 근거 추적
→ Anchor 분리
→ 명시 cue·수량·alias·일부 Action 추출
→ 제한적 Rule·Condition·Definition·Sequence 생성
→ alias 정규화
→ RDF·Neo4j 변환과 구조 검증
```

## 아직 필요한 일

```text
일반 업무 Mention 추출
→ WorkUnit·Actor·Artifact·InformationObject 유형화
→ PERFORMED_BY·HAS_INPUT·PRODUCES_OUTPUT 생성
→ 전체 non-TEST 실행
→ RDF·Neo4j 재구축
→ 파일럿 최종 보고
```

## 후속 파일럿의 핵심 지시

> **방법을 더 복잡하게 만들지 않는다. 표의 명시 구조, 소수의 규칙, 타입·관계 제약만으로 최소 업무 의미 그래프를 끝까지 구현한다. 성능이 낮거나 데이터가 부족해도 중간에 멈추지 않고 전체 파이프라인과 실패 원인을 최종 산출물로 남긴다.**

---

# 19. 실제 후속 파일럿 실행 완료 결과

위 지시에 따라 새 실험을 실제로 끝까지 실행했다.

```text
experiment_id: zaije_simple_e2e_pilot_20260712_v1
overall_status: AUTOMATED_E2E_PASS
source: 자이제_1.xlsx 전체 1,366행
human intervention: 0
human Gold: 0
LLM calls: 0
accuracy evaluated: false
result semantics: AUTOMATED_UNVERIFIED
```

`AUTOMATED_E2E_PASS`는 정답률 통과가 아니다. 사람 개입 없이 source부터 실제 Neo4j까지 자동 실행이 완료됐다는 뜻이다.

## 19.1 자동 생성 결과

| 항목 | 수 |
|---|---:|
| Evidence | 1,366 |
| Anchor | 2,308 |
| 전체 nodes | 6,258 |
| 전체 relationships | 9,249 |
| typed Mention 후보 | 460 |
| 핵심 의미 관계 | 374 |

타입:

| 타입 | 수 |
|---|---:|
| WorkUnit | 192 |
| Actor | 80 |
| Organization | 2 |
| Artifact | 38 |
| InformationObject | 93 |

관계:

| 관계 | 수 |
|---|---:|
| PERFORMED_BY | 73 |
| HAS_INPUT | 65 |
| PRODUCES_OUTPUT | 79 |
| PRECEDES | 157 |

## 19.2 구조 검증

```text
Anchor offset round-trip: 1.00
invalid edge endpoint: 0
domain/range violation: 0
semantic relation provenance coverage: 1.00
RDF triples: 88,003
SHACL critical violation: 0
```

## 19.3 실제 Neo4j 검증

Neo4j Community 4.4.43에 실제 import했다.

```text
Neo4j nodes: 6,258
Neo4j relationships: 9,249
node coverage: 1.00
relationship coverage: 1.00
WorkUnit–Actor paths: 73
WorkUnit–Input/Output paths: 144
Process sequence paths: 157
Mention–Evidence trace paths: 460
```

## 19.4 결과 해석

표의 Activity·Output 구조에서 생성한 결과는 상대적으로 명확하다.

예:

```text
WorkUnit: 수주전략 초안 개발 / 리뷰
Artifact: Capture Plan 초안
Relation: PRODUCES_OUTPUT
Confidence: HIGH
```

일반 문장 정규식에서는 잘못된 경계도 발생했다.

예:

```text
Actor 후보: “그 핵심”
Actor 후보: “최근 기업”
```

이러한 결과도 삭제하지 않고 `LOW` confidence와 `AUTOMATED_UNVERIFIED` 상태로 저장했다. 이번 목표는 정답 판정이 아니라 무인 KG 생성 완주이기 때문이다.

## 19.5 최종 산출물 위치

```text
zaije_experiment/experiments/zaije_simple_e2e_pilot_20260712_v1/
```

핵심 파일:

```text
reports/final_report.md
graphs/neo4j/nodes.csv
graphs/neo4j/edges.csv
graphs/neo4j/runtime_validation.json
graphs/rdf/r5_canonical.ttl
evaluation/structural_metrics.json
evaluation/gate_summary.json
reference/status.json
visualization/screenshots/
```

## 19.6 현재 최종 위치

```text
자이제_1 전체 입력
→ 사람 개입 없는 Anchor·Mention·타입·관계 생성
→ RDF·SHACL
→ Neo4j CSV
→ 실제 Neo4j import
→ query·시각화
```

위 End-to-End 경로는 완료됐다. 다음 선택지는 그래프를 다시 만드는 것이 아니라, 현재 자동 그래프의 confidence 규칙을 개선하거나 정확도를 별도 평가하는 것이다.
