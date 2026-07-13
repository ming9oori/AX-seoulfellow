# 자이제_1 무인 End-to-End KG 파일럿 최종 보고서

## 1. 목표

이 파일럿의 목표는 정확도 평가가 아니다.

> **사람 개입 없이 자이제_1 Excel 전체를 입력하여 Anchor 분리, Mention·개념 타입·관계 생성, RDF, Neo4j CSV, 실제 Neo4j 적재와 시각화까지 끝까지 자동 실행하는 것**

- 최종 상태: **`AUTOMATED_E2E_PASS`**
- 사람 판정·수작업 annotation: `0`
- LLM 호출: `0`
- 입력: 자이제_1 전체 `1,366`행
- 결과 상태: `AUTOMATED_UNVERIFIED`
- 의미 정확도 평가·주장: 하지 않음

`AUTOMATED_E2E_PASS`는 생성 결과가 모두 정답이라는 뜻이 아니다. 입력에서 Neo4j까지 무인 파이프라인이 중단 없이 완료됐다는 뜻이다.

## 2. 사용한 단순 방법론

복잡한 embedding, clustering, agent, LLM을 사용하지 않았다.

```text
Excel 전체 1,366행
→ 문장·표 셀·목록 Anchor
→ 표 header와 소수 정규식으로 Mention 후보
→ 5개 타입으로 자동 분류
→ 4개 관계 자동 생성
→ domain/range·Evidence 검사
→ RDF·SHACL
→ Neo4j CSV
→ 실제 Neo4j import·query
```

### 2.1 타입

```text
WorkUnit
Actor
Organization
Artifact
InformationObject
```

### 2.2 관계

```text
PERFORMED_BY
HAS_INPUT
PRODUCES_OUTPUT
PRECEDES
```

### 2.3 가장 강한 규칙: 표 구조

| 표 header | 자동 타입 |
|---|---|
| Activity·활동·단계 | WorkUnit |
| Output·결과물·산출물 | Artifact |
| Input·입력·참고자료 | Artifact 또는 InformationObject |
| Role·담당·수행자·책임자 | Actor 또는 Organization |

같은 행에서 Activity와 Output·Input·Role을 연결한다.

```text
Activity → Output = PRODUCES_OUTPUT
Activity → Input  = HAS_INPUT
Activity → Role   = PERFORMED_BY
```

### 2.4 일반 문장 규칙

다음과 같은 단순 패턴만 사용했다.

```text
X가 Y를 작성한다
X가 Y를 분석한다
X가 Y를 검토한다
X가 Y를 제출한다
```

작성·수립·개발·도출·준비의 목적어는 산출물 후보로, 분석·검토·평가·확인의 목적어는 입력 정보 후보로 연결했다.

## 3. 자동 생성 결과

### 3.1 전체 그래프

| 항목 | 결과 |
|---|---:|
| Evidence | 1,366 |
| Anchor | 2,308 |
| nodes | 6,258 |
| relationships | 9,249 |
| typed Mention 후보 | 460 |
| 의미 관계 | 374 |

### 3.2 타입

| 타입 | 수 |
|---|---:|
| WorkUnit | 192 |
| Actor | 80 |
| Organization | 2 |
| Artifact | 38 |
| InformationObject | 93 |

### 3.3 관계

| 관계 | 수 |
|---|---:|
| PERFORMED_BY | 73 |
| HAS_INPUT | 65 |
| PRODUCES_OUTPUT | 79 |
| PRECEDES | 157 |

## 4. 생성 예시

### HIGH confidence 표 구조 예시

원문 표의 `활동(Activity)`·`결과물(Output)` 열에서 다음이 자동 생성됐다.

```text
WorkUnit: 수주전략 초안 개발 / 리뷰
Artifact: Capture Plan 초안
Relation: PRODUCES_OUTPUT
Evidence: Excel row 243의 표 셀 Anchor
Rule: LF_SAME_TABLE_ROW_ACTIVITY_OUTPUT
Confidence: HIGH
```

다른 자동 Artifact 예시는 다음과 같다.

```text
프로젝트 조직도
고객미팅 플래너
Capture Plan 초안
Executive Summary
```

### LOW confidence 문장 정규식 예시

단순 정규식은 다음과 같이 경계를 길거나 부정확하게 잡은 결과도 만들었다.

```text
Actor 후보: “그 핵심”
Actor 후보: “최근 기업”
WorkUnit 후보: “제안 요청서가 발행되면 늘 허겁지겁 제안서 작성”
```

이 결과도 삭제하지 않고 다음처럼 표시했다.

```text
status = AUTOMATED_UNVERIFIED
confidence = LOW 또는 MEDIUM
rule_id = 사용한 규칙
evidence_anchor_ids = 원문 근거
```

따라서 사용자는 HIGH 결과를 우선 조회하거나 전체 자동 결과를 그대로 사용할 수 있다.

## 5. 구조 검증

| 검사 | 결과 |
|---|---:|
| Anchor offset round-trip | 1.00 |
| invalid edge endpoint | 0 |
| domain/range violation | 0 |
| 의미 관계 provenance coverage | 1.00 |
| RDF triples | 88,003 |
| SHACL critical violation | 0 |

이 검사는 그래프 구조와 원문 연결이 올바른 형식인지 확인한다. Actor·Artifact 등의 의미가 실제 정답인지는 평가하지 않는다.

## 6. Neo4j 검증

Neo4j Community 4.4.43에 실제 import했다.

| 검사 | 결과 |
|---|---:|
| Neo4j nodes | 6,258 |
| Neo4j relationships | 9,249 |
| node coverage | 1.00 |
| relationship coverage | 1.00 |
| 의미 관계 provenance | 1.00 |

런타임 query 결과:

```text
WorkUnit–Actor: 73
WorkUnit–Input/Output: 144
Process sequence: 157
Mention–Evidence trace: 460
```

## 7. 이번 파일럿에서 완료된 것

- [x] 자이제_1 전체 1,366행 자동 입력
- [x] Anchor 2,308개 자동 생성
- [x] 5개 핵심 타입 자동 생성
- [x] 4개 핵심 관계 자동 생성
- [x] 모든 의미 관계에 Evidence 연결
- [x] RDF 생성·재파싱
- [x] SHACL 검사
- [x] Neo4j nodes.csv·edges.csv 생성
- [x] 실제 Neo4j import
- [x] 네 시각화 query와 SVG 생성
- [x] 사람 개입 0
- [x] LLM 호출 0

## 8. 아직 검증하지 않은 것

- Actor·Organization 구분의 의미 정확도
- Artifact·InformationObject 구분의 의미 정확도
- 문장 정규식이 잡은 주어·목적어 경계 정확도
- PRECEDES가 실제 업무 순서를 의미하는지 여부
- 전문가 Gold 기준 precision·recall

이 항목들은 자동 KG 생성의 완료 조건이 아니며 후속 평가 대상이다.

## 9. 최종 결론

> **자이제_1 전체 데이터를 입력으로 사용해 사람 개입 없이 원문부터 Neo4j KG까지 생성하는 파일럿 파이프라인을 끝까지 완성했다.**

현재 그래프는 정답 그래프가 아니라 `AUTOMATED_UNVERIFIED KG`다. 표 구조에서 나온 HIGH 결과는 상대적으로 명확하고, 일반 문장 정규식에서 나온 LOW 결과는 오류 가능성이 높다. 그러나 모든 결과가 규칙 ID와 원문 Anchor를 가지므로 이후 필요한 경우 confidence 기반 필터링이나 별도 정확도 평가를 수행할 수 있다.
