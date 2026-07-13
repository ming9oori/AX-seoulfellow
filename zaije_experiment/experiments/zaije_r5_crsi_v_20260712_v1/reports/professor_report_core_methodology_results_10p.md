# 자이제 수주·제안 온톨로지 R5-CRSI-V 실험 보고

**교수님 보고용 핵심 요약본, 약 10쪽**  
실험명: **R5-CRSI-V: Concept Resolution, Schema Induction, Neo4j Visualization**  
최종 판정: **`DETERMINISTIC_CRSI_ONLY_PASS`**  
채택 시스템: **R5-B1 Deterministic CRSI**  
작성일: 2026-07-12

## 1쪽. 핵심 결론

### 이번 실험에서 한 일

앞선 R4 실험에서 만든 **원문 근거 보존 그래프**를 입력으로 삼아 다음 세 작업을 수행했다.

1. 같은 개념을 가리키는 한글명·영문명·약어를 하나의 canonical concept로 정리했다.
2. 여러 형태로 흩어진 관계를 제한된 관계 schema로 정규화했다.
3. 모든 개념과 관계가 원문 Evidence까지 추적되는지 RDF·SHACL·Neo4j에서 검증했다.

핵심 방법론은 다음과 같다.

> LLM이 온톨로지를 처음부터 자유롭게 생성하도록 하지 않고, 원문에서 확인된 후보만 만든다. 명시적 alias, 문자열 정규화, 개념 타입, 그래프 제약으로 우선 판정하고, 정말 모호한 후보만 LLM이 닫힌 선택지로 판정하게 한다. 최종 반영 여부는 다시 결정적 constraint gate가 판단한다.

### 핵심 결과

| 항목 | 결과 |
|---|---:|
| 전체 시연 그래프 | 4,767 nodes / 10,738 relationships |
| canonical concepts | 139 |
| 정리된 표면 중복 | 204 |
| 명시 alias 회수 | 166/166 |
| 위험한 타입 충돌 병합 | 0 |
| 관계 domain/range 위반 | 0 |
| RDF triples | 87,023 |
| SHACL critical violation | 0 |
| Neo4j 필수 view | 6/6 non-empty |

선택적 LLM 방식 B2는 B1보다 safe yield를 **18.18%** 높였지만, B3 대비 토큰 사용량이 **55.27%**로 사전 기준 35%를 초과했다. 따라서 LLM 결과는 진단 자료로 보존하되 operational ontology에는 넣지 않았다.

### 정확한 주장 범위

현재 결과는 **provenance, 구조, 제약, CQ, 재현성을 검증한 engineering-validated ontology**이다. 아직 인간 전문가 Gold와 비교한 전체 의미 정확도는 검증하지 않았다.

<div style="page-break-after: always;"></div>

# 2쪽. 연구문제와 데이터 설계

## 1. 연구문제

이번 R5 실험은 다음 질문에 답하도록 설계했다.

| 연구질문 | 확인하려는 내용 |
|---|---|
| RQ1 | 명시적 alias·타입·문자열·그래프 제약으로 위험한 병합 없이 개념 중복을 줄일 수 있는가? |
| RQ2 | 다양한 표면 관계를 제한된 relation registry로 정리하면서 Evidence를 보존할 수 있는가? |
| RQ3 | 영향도가 큰 gray 후보만 LLM에 보내는 방식이 전수 LLM보다 비용 효율적인가? |
| RQ4 | 직접 LLM 생성보다 제안 방법이 provenance와 schema 안전성에서 우수한가? |
| RQ5 | 최종 그래프를 Neo4j로 손실 없이 옮기고 업무·규칙·개념·근거 관점에서 탐색할 수 있는가? |

## 2. 사용 데이터

- 원본: `handoff-hanyang/수주제안/자이제_1.xlsx`
- 전체 레코드: **1,366개**
- 전체 non-TEST 시연 그래프 입력: **INDUCTION 681개 + VALIDATION 272개 = 953개**
- 기존 R4 입력 파일과 바이너리 해시는 달랐지만, 워크시트·행 번호·1,366개 논리 텍스트는 모두 동일함을 확인했다.

## 3. 데이터 누출 통제

방법 개발과 최종 확인을 분리했다.

| 구분 | 사용 목적 | 규모 |
|---|---|---:|
| DEV | 후보 생성, 규칙 점검, LLM 예산 선택 | 기존 노출 120건 |
| fresh VALIDATION | 시스템 동결 후 확인 실험 | 8건, 7 leakage groups |
| TEST | 이번 R5에서 사용 금지 | 접근 0건 |

원래 fresh VALIDATION 목표는 80건이었다. 그러나 R1~R4에서 노출된 Evidence와 동일 leakage group을 모두 제외한 결과 8건만 남았다. 설계서의 사전 부족 규칙에 따라 다음 원칙을 적용했다.

- API 실행 전에 8건 전수를 membership lock으로 고정했다.
- 부족분을 INDUCTION이나 TEST로 채우지 않았다.
- 결과를 확인한 뒤 threshold·prompt·relation registry를 변경하지 않았다.

따라서 **검증 독립성은 유지했지만 통계적 표본 크기는 부족하다.** 확인 표본의 alias 사건은 1건뿐이어서 recall 1/1의 Wilson 95% 신뢰구간은 약 0.21~1.00이다. 정밀한 모집단 성능으로 해석해서는 안 된다.

<div style="page-break-after: always;"></div>

# 3쪽. 전체 방법론: Evidence에서 canonical ontology까지

## 1. 기본 단위

R5는 원문을 바로 triple로 바꾸지 않고, 다음 계층을 순서대로 유지한다.

```text
Excel 원문
  → EvidenceBundle: 원문 행과 해시
  → Anchor: 문장·절·표 셀의 정확한 위치
  → Mention: 원문에 실제 등장한 표현
  → Candidate: 병합 또는 관계 판정 대상
  → Canonical Concept / Canonical Relation
  → RDF·Neo4j projection
```

용어의 의미는 다음과 같다.

| 용어 | 의미 |
|---|---|
| EvidenceBundle | Excel 한 행의 원문과 출처 정보 |
| Anchor | 원문 안에서 정확한 시작·종료 위치가 고정된 근거 단위 |
| Mention | 원문에 실제 등장한 용어·행위·수량·조건 표현 |
| Canonical Concept | 여러 표면형을 근거에 따라 하나로 정리한 개념 |
| MergeActivity | 어떤 Mention들을 어떤 규칙으로 병합했는지 나타내는 이력 |
| Canonical Relation | 고정 relation registry와 제약을 통과한 관계 |

## 2. 안전한 승격 원칙

후보가 operational ontology에 들어가기 위해서는 다음 조건을 모두 통과해야 한다.

1. 원문 Anchor가 존재해야 한다.
2. 생성된 인용문이 아니라 원문 문자열을 사용해야 한다.
3. 개념 타입이 서로 충돌하지 않아야 한다.
4. 관계의 domain과 range가 registry 정의에 맞아야 한다.
5. taxonomy·partonomy cycle이나 관계 혼동이 없어야 한다.
6. LLM 판정이라도 동일한 결정적 gate를 다시 통과해야 한다.

## 3. 이 방법이 필요한 이유

직접 triple 또는 직접 LLM 생성은 결과 수를 빠르게 늘릴 수 있지만 다음 문제가 있다.

- 같은 개념이 여러 노드로 분리될 수 있다.
- 관련 개념을 동일 개념으로 잘못 합칠 수 있다.
- 관계명이 매번 달라져 schema가 파편화될 수 있다.
- 원문에 없는 label이나 관계가 생성될 수 있다.
- 최종 결과가 어느 원문에서 왔는지 설명하기 어려울 수 있다.

R5는 **먼저 근거와 후보 공간을 제한하고, 마지막에만 의미 판단을 허용하는 보수적 ontology consolidation 방법**이다.

<div style="page-break-after: always;"></div>

# 4쪽. 핵심 방법론 1: Concept Resolution

## 1. 문자열 정규화

표면형 비교 전에 다음 정규화를 결정적으로 수행했다.

- Unicode NFKC 정규화
- 영문 casefold
- 연속 공백 정리
- 따옴표·일부 구두점 제거
- `/`, `_`, `-` 주변 공백 통일
- 약어와 수량 단위는 보수적으로 유지

예를 들어 `Bid/No bid Decision`과 `Bid / No Bid Decision`은 비교 가능한 정규형으로 바꾸되, 단어가 비슷하다는 이유만으로 바로 병합하지 않는다.

## 2. 후보를 세 종류로 분리

### Hard-positive

다음처럼 동일 개념이라는 근거가 명시적인 경우다.

- 원문의 괄호형 한·영 alias
- `이하 ○○라 한다`와 같은 명시 정의
- 같은 타입에서 완전히 같은 정규형
- 한 Anchor에서 정의된 약어
- 동일한 명시 alias가 두 concept를 연결하는 경우

### Hard-negative

다음처럼 병합하면 안 되는 경우다.

- `WorkUnit`과 `Metric`
- `Template`과 `TemplateField`
- `Actor`와 `Artifact`
- `ExampleInstance`와 일반 `DomainConcept`
- 이미 `PART_OF` 또는 `BROADER`로 구별된 두 개념

### Gray-zone

문자열이나 문맥은 유사하지만 동일 개념인지 확정할 수 없는 경우다. 이 후보만 LLM 판정 대상이 될 수 있다.

## 3. 후보 점수와 병합

초기 pair score는 다음 정보를 결합했다.

```text
0.30 lexical similarity
+ 0.25 graph-context similarity
+ 0.20 definition similarity
+ 0.15 role compatibility
+ 0.10 bilingual evidence
```

점수는 **후보의 우선순위를 정하는 용도**이지 자동 병합 근거가 아니다. hard-negative는 점수보다 우선하며, 결정적 B1에서는 hard-positive만 union-find로 병합했다.

## 4. 병합 후 provenance

병합 결과는 단순히 원 노드를 삭제하지 않는다.

```text
Mention ──DENOTES──> CanonicalConcept
MergeActivity ──USED──> Mention
MergeActivity ──GENERATED──> CanonicalConcept
Mention / Concept ──DERIVED_FROM──> Anchor
```

따라서 canonical concept에서 원래 표면형과 Excel 원문까지 역추적할 수 있다.

<div style="page-break-after: always;"></div>

# 5쪽. 핵심 방법론 2: Relation Schema Induction

## 1. 관계를 자유 생성하지 않는 이유

LLM이나 규칙이 관계명을 자유롭게 만들면 `produces`, `creates`, `hasOutput`, `outputOf`처럼 같은 의미의 관계가 여러 종류로 생길 수 있다. R5에서는 실험 전에 relation registry를 고정했다.

## 2. 고정 관계 체계

| 영역 | 관계 |
|---|---|
| 정의·명칭 | `HAS_DEFINITION`, `HAS_ALIAS` |
| 업무 구조 | `HAS_INPUT`, `PRODUCES_OUTPUT`, `PERFORMED_BY`, `PRECEDES` |
| 규칙·제약 | `HAS_CONDITION`, `HAS_EXCEPTION`, `HAS_QUANTITY_CONSTRAINT` |
| 템플릿 | `USES_TEMPLATE`, `HAS_FIELD` |
| 설명·의사결정 | `ILLUSTRATES`, `ADDRESSES_ISSUE`, `SUPPORTS_DECISION` |
| 개념 체계 | `PART_OF`, `BROADER` |

registry에 없는 신규 관계는 자동 승격하지 않고 quarantine 대상으로 남겼다.

## 3. 관계 승격 규칙

- 문서에서 명시된 순서만 `PRECEDES`로 승격한다.
- 같은 Anchor에서 명시적으로 연결된 규칙·조건·수량만 해당 관계로 연결한다.
- 템플릿 cue와 같은 Evidence의 표 구조가 함께 있을 때만 `HAS_FIELD`를 만든다.
- domain/range가 맞지 않으면 LLM이 관계를 선택했더라도 반영하지 않는다.
- 모든 canonical relation은 하나 이상의 Evidence Anchor를 가져야 한다.

## 4. Taxonomy·Partonomy·Procedure 분리

다음 세 관계는 의미가 다르므로 혼합하지 않았다.

| 구조 | 질문 | 예시 |
|---|---|---|
| Taxonomy | “A는 B의 종류인가?” | `BROADER` |
| Partonomy | “A는 B의 구성요소인가?” | `PART_OF`, `HAS_FIELD` |
| Procedure | “A 다음에 B가 수행되는가?” | `PRECEDES` |

표의 상하 위치, 문서 장·절 구조, 문자열 포함 관계만으로 `BROADER`를 만들지 않았다. cycle, self-loop, 같은 pair에 `BROADER`와 `PART_OF`가 동시에 붙는 경우도 금지했다.

## 5. 해석상 중요한 점

최종 그래프에서 역할·입출력·taxonomy 관계가 적거나 없는 것은 실패한 자유 추출 결과가 아니다. **명시 근거가 충분하지 않을 때 관계를 만들지 않은 보수적 abstention 결과**다. 그래프의 안전성과 업무 schema의 완전성은 구분해야 한다.

<div style="page-break-after: always;"></div>

# 6쪽. 핵심 방법론 3: LLM을 제한된 판정기로 사용

## 1. 비교 시스템

| 시스템 | 방식 | 목적 |
|---|---|---|
| B0 Raw Surface | 표면형을 모두 분리 | 중복이 정리되지 않은 baseline |
| B1 Deterministic CRSI | hard-positive, 타입, registry, constraint | 제안한 결정적 시스템 |
| B2 Selective LLM | B1 + 영향도 상위 gray 후보 | 비용 효율 hybrid 검증 |
| B3 Exhaustive LLM | B1 + gray 후보 전수 판정 | B2의 도달 가능 품질 기준 |
| B4 Direct-LLM | 같은 Evidence에서 개념·관계 직접 생성 | 자유 생성 baseline |

## 2. B2/B3의 LLM 제약

LLM은 한 요청에서 후보 하나만 판정했다.

개념 pair 선택지는 다음 네 가지뿐이다.

```text
SAME_CONCEPT
RELATED_NOT_SAME
DIFFERENT_CONCEPT
UNDERDETERMINED
```

관계 후보도 사전에 잠긴 registry 중 하나, `NONE`, `UNDERDETERMINED`만 선택할 수 있다.

LLM에는 다음 행위를 허용하지 않았다.

- 새로운 원문 인용 생성
- 새로운 concept label 생성
- 새로운 relation name 생성
- 자유로운 synonym·taxonomy 생성
- LLM 판정의 직접 operational 승격

## 3. 선택적 LLM 예산 정책

gray 후보를 graph impact, Evidence support, CQ 기여, 위험도, 다양성 기준으로 정렬하고 DEV에서 10%, 20%, 40% 예산을 비교했다.

동일 후보를 20% 반복 판정하여 안정성도 측정했다. 반복 일치도가 0.90 미만이면 결과를 `UNDERDETERMINED`로 처리하도록 설계했다.

## 4. 최종 안전 gate

LLM이 `SAME_CONCEPT` 또는 특정 관계를 선택해도 다음을 다시 검사했다.

1. 타입 호환성
2. Evidence 존재
3. domain/range
4. hard-negative 위반
5. taxonomy cycle
6. provenance completeness

즉, R5에서 LLM은 **온톨로지 생성기**가 아니라 **제한된 후보 판정기**다.

<div style="page-break-after: always;"></div>

# 7쪽. DEV 실험 결과: B1~B4 비교

## 1. 후보 규모

DEV 120건에서 다음 reference와 후보를 생성했다.

| 후보 종류 | 건수 |
|---|---:|
| hard-positive | 34 |
| hard-negative | 4,205 |
| gray-zone | 105 |

B1은 명시 alias **32/32**를 회수했고, 위험 병합 0, merge provenance 1.00, 재실행 안정성 1.00을 기록했다.

## 2. 시스템 비교

| 지표 | B1 | B2 | B3 | B4 |
|---|---:|---:|---:|---:|
| safe ontology yield | 88 | 104 | 128 | 140 |
| critical violation | 0 | 0 | 0 | 82 |
| provenance completeness | 1.00 | 1.00 | 1.00 | 1.00 |
| unsupported label rate | 0.00% | 0.00% | 0.00% | 12.08% |

`safe ontology yield`는 안전하게 줄인 개념 파편 수와 Evidence를 보존한 정규화 관계 수를 합친 engineering 지표다. 인간 Gold 기준 의미 정확도와 동일한 지표는 아니다.

B4는 yield 수치만 보면 가장 높지만 domain/range 위반이 82건이었다. 따라서 **많이 생성했다는 사실만으로 더 좋은 온톨로지라고 판단할 수 없다.**

## 3. B2 예산 sweep

| 예산 | 선택 후보 | safe yield | 사용 tokens |
|---|---:|---:|---:|
| 10% | 11 | 91 | 12,412 |
| 20% | 21 | 93 | 23,758 |
| 40% | 42 | 104 | 34,707 |
| B3 전수 | 105 | 128 | 62,801 |

40%가 B3 yield의 80% 이상에 도달한 최소 예산이었다.

- B2의 B1 대비 yield 증가: **18.18%**, 기준 10% 통과
- B2/B3 yield 비율: **81.25%**, 기준 80% 통과
- B2/B3 token 비율: **55.27%**, 기준 35% 실패
- 반복 판정 일치도: **21/21 = 1.00**

### DEV 결론

LLM 판정은 안정적이었고 품질 수치도 증가했다. 그러나 B3와 가까운 결과를 얻는 데 예상보다 많은 후보와 토큰이 필요했다. 따라서 **선택적 LLM의 비용 효율 가설 H5-C는 지지되지 않았다.**

<div style="page-break-after: always;"></div>

# 8쪽. 확인 실험과 최종 Neo4j 결과

## 1. Fresh VALIDATION 결과

fresh VALIDATION 8건에서는 hard-positive alias 1건만 발견됐고 gray 후보는 0건이었다.

| 항목 | B1 | B2 | B3 | B4 |
|---|---:|---:|---:|---:|
| safe ontology yield | 2 | 2 | 2 | 5 |
| critical violation | 0 | 0 | 0 | 2 |
| provenance completeness | 1.00 | 1.00 | 1.00 | 1.00 |
| unsupported label rate | 0.00% | 0.00% | 0.00% | 19.35% |

gray 후보가 없으므로 B1=B2=B3이었다. 따라서 확인 표본에서는 B2의 추가 효용을 다시 측정할 수 없었다. 다만 B1은 위반 0, B4는 위반 2건과 unsupported label 6건을 보여 직접 LLM 대비 안전성 방향은 DEV와 일치했다.

## 2. Competency Question

단순히 “답 노드가 존재하는가”만 측정하면 fresh 표본에 규칙·템플릿·절차 사례가 없어서 B1 answerability는 0.60이었다.

설계서에 따라 원문에 답이 존재하지 않고 시스템도 답하지 않은 경우를 `CORRECT_ABSTENTION`으로 계산한 결과는 다음과 같다.

- B0: 0.83
- B1/B2/B3: **1.00**
- B4: 0.67
- B1 provenance precision: 1.00
- B1 unsupported answer rate: 0

초기 0.60 결과도 삭제하지 않고 함께 보존했다. n=8이므로 CQ 통과 역시 후속 표본에서 재검증해야 한다.

## 3. 전체 non-TEST 시연 그래프

최종 시스템 B1을 INDUCTION+VALIDATION 953건에 적용했다. 이 그래프는 시각화용이며 confirmatory 성능 표본으로 재사용하지 않았다.

| 항목 | 값 |
|---|---:|
| nodes / relationships | 4,767 / 10,738 |
| canonical concepts / surface mentions | 139 / 302 |
| fragmentation reduction | 204 |
| explicit aliases | 166/166 |
| registry relations with provenance | 249/249 |
| RDF triples / SHACL violations | 87,023 / 0 |

실제 Neo4j Community 4.4.43에 적재해 다음을 확인했다.

- RDF→Neo4j node·relationship coverage 1.00
- Rule→Anchor 45/45
- Concept→Mention 139/139
- 필수 query 6종 모두 non-empty
- UID uniqueness constraint와 system/type index ONLINE

<div style="page-break-after: always;"></div>

# 9쪽. 연구질문에 대한 답과 최종 판정

## 1. 연구질문별 답

### RQ1. 결정적 규칙으로 안전하게 중복을 줄일 수 있는가?

**현재 범위에서는 그렇다.** DEV에서 alias 32/32, 전체 시연 그래프에서 166/166을 회수했다. hard-negative 충돌, provenance 누락, 재실행 불일치는 모두 0이었다. 다만 fresh VALIDATION의 alias 사건이 1건뿐이므로 일반화 주장은 제한한다.

### RQ2. 관계를 고정 schema로 정리하면서 Evidence를 보존할 수 있는가?

**그렇다.** relation evidence coverage 1.00, domain/range 위반 0, orphan 관계 0, taxonomy cycle 0을 기록했다. 단, 명시 근거가 부족한 역할·입출력·taxonomy 관계는 생성하지 않아 coverage가 제한적이다.

### RQ3. 선택적 LLM이 비용 효율적인가?

**이번 설정에서는 아니다.** B2는 B1보다 yield를 18.18% 높이고 B3의 81.25%에 도달했지만 토큰 비율이 55.27%로 기준 35%를 넘었다.

### RQ4. 직접 LLM 생성보다 안전한가?

**구조적·공학적 안전성에서는 그렇다.** DEV B4는 critical 위반 82건과 unsupported label 12.08%, fresh VALIDATION B4는 위반 2건과 unsupported label 19.35%였다. B1은 두 단계 모두 0이었다.

### RQ5. Neo4j에서 근거 추적과 시각화가 가능한가?

**가능하다.** 적재 coverage 1.00, 필수 view 6/6, Rule→Anchor와 Concept→Mention coverage 1.00을 실제 Neo4j runtime에서 확인했다.

## 2. Gate 요약

| Gate | 결과 | 판단 |
|---|---|---|
| H5-A 개념 정규화 | PASS | alias·충돌·provenance·안정성 통과 |
| H5-B 관계 schema | PASS | Evidence·domain/range·cycle 통과 |
| H5-C 선택적 LLM 효용 | **FAIL** | token ratio 55.27% > 35% |
| H5-D Direct-LLM 대비 안전성 | PASS | B1 위반·unsupported가 더 적음 |
| H5-E CQ 활용성 | PASS, small-n caveat | abstention-aware 1.00 |
| H5-F Neo4j readiness | PASS | projection·query·trace 통과 |

## 3. 최종 의사결정

최종 판정은 **`DETERMINISTIC_CRSI_ONLY_PASS`**다.

- operational canonical graph: **B1만 채택**
- B2/B3: 후보 판정 실험 및 진단 자료로만 보존
- B4: 직접 생성 baseline으로만 보존
- 결과물: **Evidence-grounded Canonical Work Ontology for Proposal/Capture Management v0.2**

<div style="page-break-after: always;"></div>

# 10쪽. 현재 한계와 후속 연구 계획

## 1. 현재 확정할 수 있는 것

- 원문 근거와 구조를 보존한 개념 정규화 파이프라인을 구현했다.
- 명시 alias를 결정적으로 정리하고 원 표면형까지 역추적할 수 있다.
- registry 관계의 provenance·domain/range·cycle을 자동 검사할 수 있다.
- RDF와 Neo4j 사이의 projection을 실제 서버에서 검증했다.
- 현재 데이터에서는 selective LLM보다 B1이 operational 기준에 적합하다.

## 2. 아직 확정할 수 없는 것

- 전체 canonical concept의 의미가 전문가 관점에서 모두 정확한가
- 관련 개념과 동일 개념을 실제 업무 전문가가 같은 기준으로 구분하는가
- 새 문서·새 산업에도 동일 규칙이 재사용되는가
- 역할·입력·산출물·taxonomy까지 포함한 업무 온톨로지가 완성됐는가
- n=8 결과가 더 큰 독립 표본에서도 반복되는가

## 3. 현재 발견된 핵심 문제

1. **Fresh VALIDATION 부족**  
   기존 노출 그룹을 제거한 뒤 8건만 남았다. 독립적인 80건 이상의 신규 leakage group이 필요하다.

2. **인간 전문가 Gold 부재**  
   구조적 안전성은 검증했지만 의미 정확도는 아직 engineering proxy에 기반한다.

3. **R4 label 경계 오류 계승**  
   일부 Concept·TemplateField label이 길거나 불완전하다. R5는 근거 없는 재명명을 금지했으므로 자동 수정하지 않았다.

4. **Schema coverage 제한**  
   역할, 입력·산출물, taxonomy·partonomy는 명시 Evidence가 부족해 대부분 abstain했다.

5. **LLM 선택 효율 부족**  
   현재 impact score와 blocking으로는 B3의 80% 결과를 얻는 데 후보 40%, 토큰 55.27%가 필요했다.

## 4. 권고 후속 실험

| 우선순위 | 후속 작업 | 목적 |
|---:|---|---|
| 1 | 신규 독립 VALIDATION 80건 이상 구축 | 통계적 확인력 확보 |
| 2 | gray pair와 B4 위반 사례 20~40건 전문가 판정 | 의미 Gold와 오류 유형 확보 |
| 3 | label span 정제 규칙 개발 | R4에서 계승된 긴·불완전 label 개선 |
| 4 | candidate blocking·impact score 개선 | B2 토큰 비율 35% 이하 달성 시도 |
| 5 | 역할·입력·산출물 reference 구축 | 업무 ontology schema coverage 확대 |
| 6 | 별도 도메인 transfer | 규칙 재사용성 검증 |

## 5. 교수님께 확인받고 싶은 사항

1. 다음 단계의 우선순위를 **신규 검증셋 구축**과 **전문가 semantic audit**에 두는 것이 적절한가?
2. 현재 결과를 “완성된 도메인 온톨로지”가 아니라 **근거 추적 가능하고 제약 검증된 보수적 ontology core v0.2**로 보고하는 것이 적절한가?
3. 후속 실험에서 전문가에게 우선 제시할 대상은 gray concept pair, B4 위반 관계, 긴 label 오류 중 무엇이어야 하는가?

---

**최종 한 문장**  
이번 R5 실험은 LLM이 자유롭게 온톨로지를 생성하는 것보다, 원문 근거가 있는 후보를 결정적 규칙과 제약으로 먼저 정리하는 방식이 현재 자이제 데이터에서 더 안전하고 재현 가능함을 보여주었으며, LLM은 아직 operational 생성기가 아니라 제한된 후보 판정 보조도구로 유지하는 것이 타당하다는 결과를 얻었다.
