# SCALE-AWC 인간 Gold 주석 가이드라인 v1

## 1. 주석 원칙

1. 모델 출력을 보지 않고 원문과 주어진 문맥만 사용한다.
2. target 원문이 주요 평가 단위이며, context는 생략 논항·범위만 복원한다.
3. 원문이 지지하지 않는 상식을 추가하지 않는다.
4. 결정할 근거가 부족하면 추측하지 말고 `UNDERDETERMINED`를 선택한다.
5. 하나의 문장이 독립 명제를 여러 개 포함하면 Claim을 나눈다. 단, 조건과 결과를 서로 다른 Claim으로 분리하지 않고 하나의 RuleFrame으로 보존한다.

## 2. Claim boundary와 span

- `source_spans`는 Claim을 지지하는 최소 연속 문자 범위다.
- `start`는 0부터 시작하는 문자 offset, `end`는 끝 문자 다음 offset이다.
- `text == evidence_text[start:end]`가 반드시 성립해야 한다.
- context를 사용하면 해당 context `evidence_id`를 기록하고 `restored_from_context=true`로 표시한다.
- 제목이나 표 header를 논항 복원에 쓴 경우도 근거 ID를 남긴다.

## 3. Claim family

| Label | 의미 | 주요 예 |
|---|---|---|
| `FACTUAL` | 정의·사실·구성 설명 | "Capture Plan은 ...로 구성된다" |
| `NORMATIVE` | 의무·금지·권고 | "반드시 ...해야 한다" |
| `CONDITIONAL` | 조건·예외·필요조건 | "...인 경우 ...한다" |
| `PROCEDURAL` | 단계·순서·입출력·의사결정 | "검토 후 승인한다" |
| `EVALUATIVE` | 점수·비교·측정·조사 결과 | "영향력을 5점 척도로..." |
| `DISCOURSE` | 질문·예시·인용·오해·반박 | "예를 들어..." |
| `UNCLEAR` | 근거만으로 유형 판정 불가 | 불완전 조각 |

가장 핵심적인 의미 기능을 family로 선택하되, 조건이 있는 의무는 `claim_family=CONDITIONAL`, `claim_type=ConditionalRule`, `modality=MUST`처럼 세부 필드에 모두 보존한다.

## 4. Claim type

- 정의·사실: `Definition`, `DescriptiveFact`
- 규범: `Obligation`, `Prohibition`, `Recommendation`
- 조건: `NecessaryCondition`, `ConditionalRule`, `Exception`
- 절차: `ProcessOrder`, `ActivityOutput`, `DecisionTrigger`
- 목적·인과: `PurposeCause`
- 평가: `ComparisonFormula`, `EvaluationObservation`
- 담화: `Example`, `CounterExample`, `Question`, `Quotation`
- 판정 불가: `OtherUnclear`

## 5. Modality와 polarity

| Modality | 판정 기준 |
|---|---|
| `MUST` | 의무, 반드시, 필수 수행 |
| `MUST_NOT` | 금지, 하지 말아야 함 |
| `SHOULD` | 권고, 바람직함, 일반적 필요성 |
| `MAY` | 허용, 가능, 선택 |
| `DESCRIPTIVE` | 규범이 아닌 사실 설명 |
| `NONE` | 질문·제목·불완전 조각 등 양태 미판정 |

- `MUST_NOT`은 modality에 금지를 보존하고 polarity도 `NEGATIVE`로 기록한다.
- 단순히 "필요하다"가 등장했다고 항상 `MUST`로 분류하지 않고, 누가 무엇을 의무적으로 해야 하는지를 확인한다.
- 반박 문장의 부정된 명제와 저자가 실제로 주장하는 명제를 구분한다.

## 6. Condition, exception, scope

- 조건은 규칙이 발화하는 전제다.
- 예외는 일반 규칙이 적용되지 않거나 다른 결과가 적용되는 상황이다.
- 시간 표현이 단순 절차 순서인지 규칙 조건인지 구분한다.
- condition/exception은 원문 span을 반드시 기록한다. span이 없으면 `ConditionalRule`로 승격하지 않는다.

## 7. Discourse와 promotion

| 현상 | discourse_status | 기본 promotion |
|---|---|---|
| 저자의 명시적 주장 | `ASSERTED` | 의미에 따라 선택 |
| 설명용 사례 | `EXAMPLE` | `NONE` |
| 질문 | `QUESTION` | `NONE` |
| 외부 인용 | `QUOTATION` | `EVALUATION_NODE` 또는 `NONE` |
| 오해·잘못된 믿음 | `MYTH` | `NONE` |
| 반례 | `COUNTEREXAMPLE` | `NONE` |

`Example`, `Question`, `Quotation`, `Myth`는 별도 검수 없이 operational relation이나 TBox 규칙으로 승격하지 않는다.

## 8. Promotion target

- `FACT_ASSERTION`: 개별 사실·상태·관찰
- `TBOX_AXIOM`: 클래스·계층·도메인/레인지 정의
- `PROCESS_EDGE`: 절차 순서·입출력·역할
- `RULE_NODE`: 조건·의무·금지·권고·예외
- `EVALUATION_NODE`: 측정·조사·출처·비교
- `LEXICAL_ONLY`: 용어·별칭 정보만 보존
- `NONE`: 승격 대상 아님
- `NEEDS_REVIEW`: 고위험 또는 근거 부족

## 9. 온톨로지 주석

- `term_mentions`: 용어 span, canonical concept ID, 상위 concept type, instance/class를 기록한다.
- 같은 문장·표에서 대비되거나 다른 역할을 가지면 문자열이 비슷해도 병합하지 않는다.
- `Capture Plan` 문서와 `Capture Planning` 활동은 다른 ontological category다.
- `relations`: relation registry ID, subject/object concept ID, evidence span, domain/range 판정을 기록한다.
- 규칙은 평면 edge로 압축하지 말고 RuleFrame으로 기록한다.

## 10. 완료 점검

- 모든 span이 원문 substring인가?
- 의무·금지·권고·가능을 구분했는가?
- 부정과 반박 범위를 보존했는가?
- 조건과 예외 span을 남겼는가?
- 사례·질문·인용을 사실·규칙로 승격하지 않았는가?
- instance/class와 process direction을 확인했는가?
- 수치 범위·단위·척도를 그대로 보존했는가?
- 알 수 없는 것을 추측하지 않고 `UNDERDETERMINED`로 남겼는가?

## 11. PILOT 잠금 기준

| 항목 | 기준 |
|---|---:|
| Term/argument span pairwise F1 | ≥ 0.85 |
| Claim family Krippendorff's alpha | ≥ 0.80 |
| Claim type/modality/promotion alpha | ≥ 0.75 |
| Canonicalization Cohen's kappa | ≥ 0.80 |
| Relation/Rule label alpha | ≥ 0.75 |

미달 시 가이드라인을 한 차례만 수정하고, 기존 PILOT과 겹치지 않는 20건으로 재확인한다.
