# TRACE-OL 파일럿 실험 설계서 v1.0

> **LLM-Silver Reference 기반, 비용 상한형 Claim-first 온톨로지 구축 파일럿**  
> 대상 데이터: `자이제_1 (2).xlsx`의 `clean_sentences` 1,366개 evidence unit  
> 작성 기준일: 2026-07-10  
> 목적: TRACE-OL을 실제로 실행하여 Claim Graph, Operational Graph, Neo4j 시각화 결과와 파일럿 비교 지표를 생성한다.

---

## 0. 이번 개정안에서 확정하는 핵심 결정

기존 설계는 사람 전문가가 만든 Gold standard를 전제로 했으나, 이번 파일럿에서는 비용과 착수 속도를 고려하여 **LLM이 만든 임시 기준 데이터**를 사용한다. 다만 연구 보고서에서는 이를 Gold라고 부르지 않고 다음과 같이 명명한다.

```text
TRACE LLM-Silver Reference v0.1
```

평가 코드 안에서는 일반적인 `gold_loader` 인터페이스로 읽어도 되지만, 파일명·리포트·그래프 속성에는 반드시 `silver` 또는 `provisional_reference`를 사용한다.

| 항목 | 확정안 |
|---|---|
| 파일럿 표본 | 180개 target evidence unit |
| 분할 | CAL 60 / B1 60 / B2 60 |
| 최종 잠금 평가 세트 | B2 60개 |
| 기준 주석 | 저비용 LLM A·B 독립 주석 → 불일치만 C → 고위험 잔여 충돌만 강한 adjudicator |
| 주석 명칭 | `LLM-Silver Reference v0.1` |
| 비교 시스템 | Direct Triple, Claim-first Full-LLM, TRACE No-LLM, TRACE Selective-LLM, Selective+Distillation |
| API 기본 상한 | 총 80회 호출, 입력 600k token, 출력 250k token |
| 강한 모델 상한 | 최대 8회 호출 또는 전체 비용의 15% 중 먼저 도달하는 값 |
| Neo4j 산출물 | Audit Graph와 Operational Projection을 모두 생성 |
| 파일럿 이후 | 50–100개 인간 검수로 `Gold-Core`를 별도 구축하는 것을 권고하되 이번 파일럿의 필수 조건은 아님 |

이번 설계의 목표는 “전문가 수준 정확도를 최종 입증”하는 것이 아니라 다음을 확인하는 것이다.

1. TRACE-OL 파이프라인이 처음부터 끝까지 실제로 작동하는가?
2. Claim-first가 직접 삼중항 생성보다 위험한 승격 오류를 줄이는가?
3. 선택적 LLM이 전면 LLM보다 적은 비용으로 유사한 결과를 내는가?
4. LLM 판정을 규칙으로 증류했을 때 다음 배치의 호출량이 감소하는가?
5. 결과를 Neo4j에 적재하여 원문 근거까지 추적 가능한 형태로 시각화할 수 있는가?

---

## 1. 연구 범위

### 1.1 포함 범위

- 문서 구조와 evidence ID 생성
- 표·목록·수식·문장 문맥 묶음 생성
- Atomic Work Claim 주석 및 추출
- claim type, modality, polarity, condition, promotion target 판정
- 용어·개념 후보와 제한적인 sense split/merge
- 사실 assertion, process edge, rule, evaluation observation으로 승격
- provenance를 포함한 Neo4j 그래프 생성
- 파일럿 기준 품질·비용·오류 분석

### 1.2 이번 파일럿에서 축소하거나 제외하는 범위

- 전체 1,366개 행의 최종 주석
- 10개 이상의 대규모 baseline
- 법인파산·투자·마케팅까지 포함한 cross-domain 검증
- 전문가 2명과 제3 adjudicator에 의한 완전한 Gold ontology
- 복잡한 OWL 추론 성능 평가
- 별도 소형 모델의 본격 학습과 hyperparameter 탐색
- 통계적 우월성을 확정하는 대규모 유의성 검정

이번 파일럿은 **실행 가능성, 오류 유형, 품질–비용 곡선과 Neo4j 결과 생성**을 검증한다. 논문 수준의 최종 성능 주장은 후속 인간 검수형 Gold-Core와 확대 실험에서 수행한다.

---

## 2. 연구 질문과 파일럿 성공 가설

### RQ-P1. LLM-Silver를 이용하여 실험 가능한 기준 데이터를 만들 수 있는가?

**파일럿 가설 H-P1**

- 자동 JSON schema 통과율이 98% 이상이다.
- 모든 accepted claim의 source span이 실제 원문에 존재한다.
- A·B 합의 또는 제한적 adjudication으로 전체 claim의 80% 이상을 `Silver-A` 또는 `Silver-B`로 확정할 수 있다.
- `MUST/MUST_NOT`, 부정, 예시 승격, 조건 범위와 같은 고위험 충돌의 미해결 비율이 15% 이하이다.

### RQ-P2. Claim-first가 직접 사실 삼중항 생성보다 안전한가?

**파일럿 가설 H-P2**

Claim-first 방식은 Direct Triple 방식에 비해 다음 치명적 오류의 합계를 상대적으로 30% 이상 줄인다.

- 의무·권고·금지를 일반 사실로 평탄화
- 부정 누락
- 조건부 규칙을 전역 사실로 승격
- 예시·반례·질문을 사실로 승격
- 원문에 없는 assertion 생성

### RQ-P3. 선택적 LLM이 전면 LLM에 근접한 품질을 유지하는가?

**파일럿 가설 H-P3**

B2에서 Selective-LLM은 Claim-first Full-LLM과 비교하여 다음을 만족한다.

- claim family Macro-F1 차이 0.05 이내
- critical error rate 차이 3%p 이내
- 추출 단계 LLM 입력·출력 token 합계가 Full-LLM의 40% 이하

원래 방법론의 80% 절감 목표보다 완화된 기준을 사용한다. 이번에는 규칙과 threshold가 아직 초기 버전이기 때문이다.

### RQ-P4. Decision-to-Rule Distillation이 다음 배치의 호출량을 줄이는가?

**파일럿 가설 H-P4**

B1의 LLM 판정으로 만든 검증된 labeling function을 B2에 적용했을 때 다음을 만족한다.

- LLM 선택 대상 수가 증류 전 가상 게이트 대비 20% 이상 감소
- 최종 claim family Macro-F1 저하가 0.03 이하
- 새 규칙으로 인한 critical error가 0건 또는 전체의 2% 이하

### RQ-P5. 실제 Neo4j 결과물을 생성할 수 있는가?

**파일럿 가설 H-P5**

- accepted claim과 operational assertion의 Neo4j 적재 성공률 100%
- accepted assertion 중 evidence 경로가 없는 비율 0%
- 중복 ID constraint 위반 0건
- 사전 정의한 competency query 10개 중 8개 이상이 evidence-linked answer를 반환

---

## 3. 데이터 단위와 표본 설계

### 3.1 Target evidence unit과 evidence bundle

평가 단위는 원본의 한 행 또는 하나의 표 record가 되는 `target evidence unit`이다. API에는 target만 단독으로 보내지 않고 다음을 포함한 `evidence bundle`을 보낸다.

```text
bundle_id
문서·시트·행·페이지 ID
장·절 제목
target 원문
이전 evidence 1개
다음 evidence 1개
표인 경우 관련 header와 같은 행의 cell
목록인 경우 parent item
문맥 복원 여부와 원본/복원 구분
```

주석 대상은 target이며, context에서 복원한 정보는 반드시 `restored_from_context=true`와 근거 evidence ID를 기록한다.

### 3.2 파일럿 표본 수

권장 표본은 총 180개 target evidence unit이다. 전체 1,366개의 약 13%이므로 파일럿 수준의 폭넓은 오류 탐색이 가능하면서도 API 비용을 제한할 수 있다.

#### 표본 구성

- **목적 층화 표본 150개**: 희귀하지만 중요한 claim을 충분히 포함
- **단순 무작위 표본 30개**: 파일럿이 고위험 문장에만 과도하게 치우쳤는지 점검

목적 층화 표본은 아래 6개 strata에서 각 25개를 추출한다.

| Stratum | 목표 수 | 대표 내용 |
|---|---:|---|
| S1 정의·일반 설명 | 25 | `X란`, `말한다`, 일반적인 설명 |
| S2 의무·금지·권고 | 25 | `해야 한다`, `하지 말아야`, `권장` |
| S3 조건·예외·필요조건 | 25 | `경우`, `만약`, `있어야`, `단` |
| S4 절차·순서·의사결정 | 25 | 단계, 활동, trigger, decision |
| S5 표·수식·평가 관측 | 25 | 활동–산출물, BCM, 점수, `V > C` |
| S6 예시·반례·질문·인용·모호 문장 | 25 | 예, ×/○, 질문, 인용, 생략 |

하나의 unit이 여러 strata에 걸리면 우선순위는 `S5 → S2 → S3 → S4 → S6 → S1`로 둔다. 이는 구조 손실과 위험 규칙을 먼저 확보하기 위한 파일럿 정책이다.

### 3.3 분할

| Split | 수 | 사용 목적 | 수정 허용 여부 |
|---|---:|---|---|
| CAL | 60 | schema·prompt·LF·threshold 조정 | 허용 |
| B1 | 60 | 선택적 LLM 실행, 규칙 증류 | 제한적으로 허용 |
| B2 | 60 | 최종 파일럿 평가 | 결과 확인 전 동결 |

B1은 내부적으로 다음처럼 나눈다.

- `B1a` 40개: LLM 판정 수집과 LF 후보 생성
- `B1b` 20개: 새 LF의 검증과 activation 결정

B2는 표본 ID, 원문, reference annotation까지 생성한 후 접근 권한 또는 파일 경로를 분리해 잠근다. B2 결과를 본 뒤 prompt, 규칙, threshold를 변경한 경우 버전을 올리고 B2를 더 이상 최종 test로 부르지 않는다.

### 3.4 누수 방지

- 같은 표의 header·row·설명은 서로 다른 split으로 나누지 않는다.
- 같은 목록의 parent와 item을 분리하지 않는다.
- 같은 절의 강한 coreference chain은 가능한 한 같은 split에 둔다.
- near-duplicate 및 반복 `Shipley Tip`은 하나의 split에만 배치한다.
- `Capture Plan`처럼 다의어를 포함한 경우 각 sense가 CAL과 test에 모두 존재하도록 하되 동일 문장을 복제하지 않는다.
- split은 문장 무작위가 아니라 `bundle_group_id` 기준으로 수행한다.

---

## 4. LLM-Silver Reference 구축

### 4.1 명칭과 등급

| 등급 | 조건 | 최종 평가 포함 |
|---|---|---|
| Silver-A | A·B가 critical field에 합의하고 자동 검증 통과 | 포함 |
| Silver-B | C의 다수결 또는 adjudicator로 해결되고 자동 검증 통과 | 포함 |
| Challenge | 의미 충돌이 남거나 adjudicator가 abstain | headline F1에서 제외, 별도 분석 |
| Rejected | source span 위조, schema 실패, 원문 근거 없음 | 제외 및 오류 기록 |

모든 레코드에는 다음 메타데이터를 저장한다.

```text
reference_version
annotation_source=LLM
annotator_role
model_id
prompt_version
schema_version
created_at
agreement_tier
adjudication_status
human_reviewed=false
```

### 4.2 파일럿 주석 schema

API 비용과 주석 안정성을 위해, 이번 파일럿에서는 원래 Atomic Work Claim의 모든 필드를 한꺼번에 확정하지 않는다. 다음 핵심 필드를 필수로 한다.

```text
claim_id
source_span
claim_family
claim_type
subject span 또는 implicit 표시
predicate_normalized
object/event argument spans
modality
polarity
condition spans
exception spans
scope span 또는 context ID
promotion_target
kernel_type 후보
decision
uncertainty_code
```

`purpose`는 `PurposeCause` claim에서만, `formula/evaluation` 필드는 해당 claim에서만 출력한다. 글로벌 canonical concept ID는 이후 canonicalization 단계에서 생성하고, reference LLM이 자유롭게 ID를 만들지 못하게 한다.

### 4.3 Claim family와 fine-grained type

#### Claim family

```text
FACTUAL
NORMATIVE
CONDITIONAL
PROCEDURAL
EVALUATIVE
DISCOURSE
UNCLEAR
```

#### Claim type

```text
Definition
DescriptiveFact
Obligation
Prohibition
Recommendation
NecessaryCondition
ConditionalRule
Exception
ProcessOrder
ActivityOutput
DecisionTrigger
PurposeCause
ComparisonFormula
EvaluationObservation
Example
CounterExample
Question
Quotation
OtherUnclear
```

#### Modality

```text
MUST
MUST_NOT
SHOULD
MAY
DESCRIPTIVE
NONE
```

#### Promotion target

```text
FACT_ASSERTION
TBOX_AXIOM
PROCESS_EDGE
RULE_NODE
EVALUATION_NODE
LEXICAL_ONLY
NONE
NEEDS_REVIEW
```

### 4.4 핵심 label 결정 규칙

claim type은 조건, 양태, 극성을 모두 한 label에 중복 인코딩하지 않는다. 다음 우선순위를 고정한다.

| 원문 형태 | claim type | modality | polarity | condition |
|---|---|---|---|---|
| `X는 Y이다` | Definition 또는 DescriptiveFact | DESCRIPTIVE | POSITIVE | 없음 |
| `Y해야 한다` | Obligation | MUST | POSITIVE | 있을 수 있음 |
| `Y하지 말아야 한다` | Prohibition | MUST_NOT | NEGATIVE | 있을 수 있음 |
| `Y하는 것이 좋다/권장한다` | Recommendation | SHOULD | POSITIVE | 있을 수 있음 |
| `X인 경우 Y한다` | ConditionalRule 또는 해당 주행위 type | DESCRIPTIVE/MUST/SHOULD | 문장에 따름 | X |
| `Y하려면 X가 있어야 한다` | NecessaryCondition | DESCRIPTIVE 또는 MUST | 문장에 따름 | 적용 범위 별도 |
| `예를 들어 Y` | Example | NONE | 문장에 따름 | 없음 |
| `Y하지 않는 것은 잘못된 예다` | CounterExample | NONE | NEGATIVE | 없음 |

`if X, must Y`처럼 조건과 의무가 함께 있으면 `claim_type=Obligation`, `modality=MUST`, `conditions=[X]`로 주석한다. `ConditionalRule`은 별도의 의무·금지·권고가 없는 일반적인 if–then 규칙에 우선 사용한다.

파일럿의 canonical encoding에서는 `MUST_NOT`을 사용할 때 predicate는 가능한 한 긍정형 동사로 정규화하고 `polarity=NEGATIVE`로 둔다. 예를 들어 “리스크를 숨기지 말아야 한다”는 predicate=`숨기다`, modality=`MUST_NOT`, polarity=`NEGATIVE`다.

### 4.5 주석 모델 역할

#### Annotator A — 독립 추출자

- 저비용 모델 사용
- target에서 모든 Atomic Work Claim을 독립적으로 추출
- 허용 enum과 source span만 출력

#### Annotator B — 독립 추출자

- 가능하면 A와 다른 저비용 모델 사용
- A의 결과를 보지 않음
- 같은 schema를 사용하되 few-shot 예시 순서와 prompt 문구를 다르게 구성

같은 모델 하나만 사용할 수 있다면 독립 세션, 다른 prompt variant, 예시 순서 변경을 사용하되 이를 “독립 annotator”가 아니라 `pseudo-independent runs`로 기록한다.

#### Annotator C — 불일치 사례 전용

- A·B의 결과를 보지 않고 해당 target을 다시 독립 주석
- 전체 180개가 아니라 A·B 불일치 unit에만 호출
- 저비용 모델 사용

#### Adjudicator D — 고위험 잔여 충돌 전용

- A·B·C의 구조화 결과와 원문만 제공
- 강한 모델 사용 가능
- 다음 충돌에만 호출
  - MUST 대 SHOULD/MAY
  - MUST_NOT 또는 부정 범위
  - Example/CounterExample 대 Fact
  - 조건부 대 전역 assertion
  - promotion target이 RULE과 FACT로 갈림
  - sense merge/split이 많은 downstream edge에 영향
- `accept one`, `merge`, `split`, `abstain`, `needs_review`만 반환

### 4.6 자동 검증

LLM 판정 전에 다음 검사를 프로그램으로 수행한다.

1. JSON Schema validation
2. `source_span`이 target 또는 명시된 context 원문에 실제로 존재하는지 검사
3. start/end offset과 실제 문자열 일치 검사
4. 허용 enum 외 값 거절
5. `MUST_NOT`와 polarity의 모순 검사
6. `Example`, `CounterExample`, `Question`, `Quotation`의 기본 promotion이 `NONE`인지 검사
7. implicit subject에 가상의 원문 span이 들어가지 않았는지 검사
8. 조건 span이 없는 `ConditionalRule`은 review로 이동
9. 표 셀의 좌표와 source record ID 존재 여부 검사
10. 한 claim이 원문에 없는 개념을 object로 추가했는지 lexical entailment audit

공백·인용부호·문장부호 차이만 자동 정규화한다. 의미를 바꾸는 자동 수정은 하지 않는다.

### 4.7 합의와 claim 정렬

A와 B가 추출한 claim 수가 다를 수 있으므로 claim ID를 직접 비교하지 않는다. 같은 evidence 내에서 다음 점수로 최대 가중 이분 매칭을 수행한다.

```text
alignment_score =
  0.50 × source_span character IoU
+ 0.25 × subject/object span overlap
+ 0.15 × normalized predicate similarity
+ 0.10 × claim family agreement
```

- source span IoU가 0.80 이상이면 label이 달라도 우선 같은 claim 후보로 정렬한다.
- 그 외에는 `alignment_score >= 0.50`이면 같은 claim 후보로 본다.
- claim type, modality, polarity와 condition은 claim 정렬 후 합의 여부를 판정하는 필드이며, 정렬 자체를 과도하게 막지 않도록 낮은 비중 또는 0으로 둔다.
- 한쪽에만 있는 claim은 “claim existence disagreement”로 C에게 보낸다.
- critical field는 `claim_type`, `modality`, `polarity`, `promotion_target`, 조건의 존재 여부다.
- A·B가 critical field에 모두 합의하고 span 검증을 통과하면 Silver-A다.
- 불일치는 C를 호출하고 다수결 가능한 categorical field는 2/3로 결정한다.
- span 충돌은 가장 긴 span을 자동 선택하지 않고, 다수 일치 span 또는 D의 판정을 사용한다.

### 4.8 Reference 구축 중 비용 절감 정책

- prose는 최대 10 target을 한 call에 batch
- 표·수식은 최대 4–6 target을 한 call에 batch
- A·B는 전체 표본, C는 불일치만, D는 고위험 잔여 충돌만 호출
- 긴 설명과 chain-of-thought 출력 금지
- `uncertainty_code`는 짧은 enum으로 제한
- JSON invalid일 때만 최대 1회 retry
- 불확실하다는 이유만으로 retry하지 않고 Challenge로 보냄
- 동일 prompt hash와 evidence hash는 cache 재사용

---

## 5. 비교 시스템

파일럿에서는 원래 B0–B10 전체를 실행하지 않고 핵심 가설을 구분할 수 있는 다섯 조건만 사용한다.

### E0. DirectTriple-LLM

```text
Evidence bundle
→ LLM이 바로 entity/relation triple 생성
→ 간단 canonicalization
→ Neo4j fact edge
```

- B2에서만 실행
- claim type, modality, condition 노드를 먼저 만들지 않음
- 흔한 “문장→삼중항” 방식의 파일럿 baseline

### E1. ClaimFirst-FullLLM

```text
Evidence bundle
→ 모든 target을 LLM이 Atomic Work Claim으로 주석
→ promotion policy
→ fact/process/rule/evaluation graph
```

- B2에서만 실행
- Claim-first가 적용된 전면 LLM 상한선
- Reference 생성 prompt와 다른 extraction prompt 사용
- 가능하면 reference annotator와 다른 모델 사용

### E2. TRACE-NoLLM

```text
문서 구조·표 파서
+ 한국어 언어 규칙
+ labeling functions
+ 단순 weighted vote
→ claim 후보·승격
```

- CAL에서 LF weight와 threshold를 조정
- B1과 B2에 적용
- API 호출 0회
- 이번 파일럿에서는 별도의 대형 label model 학습보다 해석 가능한 weighted vote를 우선 사용

### E3. TRACE-SelectiveLLM

```text
E2 결과
→ uncertainty × risk × novelty × graph impact
→ 상위 후보만 저비용 LLM 판정
→ promotion
```

- B1a에서 실행하여 LLM 판정과 오류 패턴 수집
- B1b에서 threshold 검증
- B2에서는 distillation을 적용한 E4와 연결

### E4. TRACE-Selective+Distillation

```text
B1a의 LLM 판정
→ LF 후보 생성
→ B1b에서 검증
→ 통과 LF만 B2에 적용
→ 남은 고우선순위 후보만 LLM 호출
```

- B2의 제안 방법
- headline 결과에서 TRACE-OL 파일럿 대표 시스템으로 사용

### 비용 없는 구조 ablation

E2를 다음 두 버전으로 실행한다.

- `E2-Structure`: 장·절·표 header·cell·목록 순서 사용
- `E2-Flat`: 동일 원문을 평문으로만 사용

표·수식·절차 subset에서만 비교하여 구조 신호의 유효성을 탐색한다. 추가 API 호출은 없다.

---

## 6. No-LLM 후보 생성과 약한 감독

### 6.1 최소 labeling function 묶음

파일럿에서 처음부터 지나치게 많은 규칙을 만들지 않는다. 다음 12–20개 핵심 LF로 시작한다.

| LF 군 | 예 |
|---|---|
| 정의 | `X란`, `X는 …을 말한다`, `X라고 부른다` |
| 의무 | `해야 한다`, `필수`, `반드시` |
| 금지·부정 | `하지 말아야`, `피해야`, `금지` |
| 권고 | `권장`, `가장 좋은`, `바람직` |
| 조건 | `경우`, `만약`, `때`, `~라면` |
| 필요조건 | `있어야 한다`, `필요하다` |
| 절차 | `단계`, `이후`, `끝나면`, 순번·목록 |
| 활동–산출물 | 표 header가 활동/결과물인 record |
| 목적·인과 | `목적은`, `위해서`, `때문이다` |
| 예시·반례 | `예를 들어`, `사례`, `(×)`, `(○)` |
| 질문·인용 | 물음표, 인용 표지 |
| 수식·평가 | 비교 연산자, 점수·가중치 header |

### 6.2 Weighted vote

각 LF는 다음을 반환한다.

```text
(label, confidence, scope, evidence)
또는 abstain
```

CAL에서 Silver와 비교하여 LF별 precision을 추정하고 초기 weight를 정한다.

```text
weight = logit(clipped_precision)
```

지원 수가 3 미만인 LF는 weight를 학습하지 않고 기본 저가중치 또는 abstain 처리한다. 상관이 높은 중복 LF는 하나의 family로 묶어 과대 투표를 방지한다.

### 6.3 후보 confidence

```text
posterior(label) = softmax(가중 LF vote 합)
confidence = max posterior
uncertainty = 1 - confidence
```

이번 파일럿에서 confidence는 확률의 엄밀한 calibration이라기보다 **게이트의 우선순위 점수**로 사용한다. B2에서 calibration curve를 해석할 때 이 한계를 명시한다.

---

## 7. 선택적 LLM 게이트

### 7.1 우선순위 공식

각 후보에 대해 0–1로 정규화한 다음 값을 계산한다.

```text
priority =
  0.45 × uncertainty
+ 0.30 × risk
+ 0.15 × novelty
+ 0.10 × graph_impact
```

#### Risk 기본값

| 후보 | risk |
|---|---:|
| Prohibition, negation scope | 1.00 |
| Obligation | 0.90 |
| Condition/Exception | 0.85 |
| Example/CounterExample promotion | 0.85 |
| sense split/merge | 0.75 |
| Process/Decision | 0.60 |
| Definition | 0.45 |
| DescriptiveFact | 0.30 |

#### Novelty

- CAL과 B1에서 보지 못한 predicate pattern
- 기존 relation cluster에 낮은 유사도
- 새로운 표 header 조합
- 새로운 claim type 조합

#### Graph impact

- 여러 claim이 참조하는 concept
- 많은 process edge에 연결되는 stage/task
- merge 오류 시 다수 assertion에 영향을 미치는 sense
- competency query에 직접 사용되는 노드

### 7.2 호출 조건

다음 중 하나를 만족할 때 LLM queue 후보가 된다.

1. `priority >= 0.65`
2. 고위험 claim이고 confidence < 0.90
3. LF가 modality 또는 polarity에서 충돌
4. sense merge/split이 graph impact 상위 20%
5. promotion validation이 실패했지만 원문 근거는 존재

다만 한 split에서 LLM으로 보내는 후보는 다음 상한을 적용한다.

```text
min(전체 후보의 15%, 30개 후보)
```

낮은 confidence라도 영향도와 위험이 낮으면 LLM을 호출하지 않고 `NeedsReview`로 남긴다.

### 7.3 LLM 판정 출력

```text
accept
reject
abstain
needs_review
```

필수 출력은 candidate ID, 결정, claim type, modality, polarity, conditions, source span IDs다. 자유 relation 이름 생성과 원문 밖 지식 보완은 금지한다.

---

## 8. Decision-to-Rule Distillation

### 8.1 생성 대상

B1a에서 반복적으로 accept/reject된 판정으로부터 다음 feature를 추출한다.

- lexical cue
- 조사·어미·부정 범위
- dependency path 또는 간단 chunk pattern
- block type
- 표 header 조합
- subject/object Kernel type
- 장·절 문맥
- 기존 LF 충돌 형태

### 8.2 LF 후보 예

```text
패턴: “X의 작성 목적은 Y하는 것이다”
조건: block_type=prose, 질문/인용 아님
출력: claim_type=PurposeCause, subject=X, purpose=Y
scope: document-local에서 시작
```

### 8.3 검증과 승격 기준

B1a에서 만든 LF를 B1b에 적용하여 다음을 확인한다.

| LF 종류 | 최소 precision | 최소 support | 추가 조건 |
|---|---:|---:|---|
| 일반 fact/definition | 0.85 | 4 | critical error 없음 |
| process/activity-output | 0.90 | 3 | 표 구조 일치 |
| obligation/prohibition/negation | 0.95 | 3 | modality/polarity 오류 0건 |
| example/counterexample 차단 | 0.95 | 3 | fact 오승격 0건 |

통과 LF도 기본적으로 `document-local` 또는 `section-family` 범위로 등록한다. 다른 도메인에 바로 일반화하지 않는다.

### 8.4 B2 평가

B2에서 다음을 기록한다.

- distillation 적용 전 gate가 선택했을 후보 수
- distillation 후 자동 처리된 후보 수
- 실제 LLM에 보낸 후보 수
- 새 LF별 정답 일치와 오류
- 호출 감소율

증류로 자동 처리된 후보가 critical error를 만들면 해당 LF를 즉시 비활성화하고 `SoftDeprecated`로 기록한다.

---

## 9. API 비용 상한과 호출 계획

### 9.1 모델 역할

특정 공급자나 모델 이름에 고정하지 않고 다음 역할로 구성한다.

```text
M-A: 저비용 reference annotator A
M-B: 저비용 reference annotator B
M-C: 저비용 disagreement annotator
M-D: 강한 adjudicator
M-E: 시스템 extraction/adjudication용 저비용 모델
```

가능하면 `M-E`는 reference를 만든 A·B와 다른 모델을 사용한다. 불가능하면 prompt, few-shot 예시, 세션과 cache namespace를 분리하고 결과를 “외부 정확도”가 아니라 “LLM-Silver와의 일치도”라고 보고한다.

### 9.2 권장 호출 예산

| 용도 | 예상 호출 | 상한 |
|---|---:|---:|
| Annotator A, 180개 batch | 18–22 | 22 |
| Annotator B, 180개 batch | 18–22 | 22 |
| Annotator C, 불일치만 | 4–8 | 8 |
| Adjudicator D | 2–5 | 8 |
| E0 Direct Triple, B2 | 6–8 | 8 |
| E1 Claim-first Full-LLM, B2 | 6–8 | 8 |
| E3/E4 Selective LLM | 3–6 | 6 |
| invalid JSON retry·예비 | 0–4 | 4 |
| **총계** | **61–80** | **80** |

### 9.3 Token 상한

```text
max_total_calls        = 80
max_input_tokens       = 600,000
max_output_tokens      = 250,000
max_strong_model_calls = 8
```

실제 비용은 공급자의 단가로 다음과 같이 계산한다.

```text
cost = Σ[(input_tokens / 1,000,000) × input_price
       + (output_tokens / 1,000,000) × output_price]
```

각 call마다 `cost_ledger.csv`에 model ID, prompt hash, evidence IDs, token, cache 여부, retry 여부를 기록한다.

### 9.4 비용 보호 규칙

- 총 예산 70%에 도달했는데 reference adjudication이 남아 있으면 저위험 불일치는 Challenge로 남긴다.
- 총 예산 80%에 도달하면 optional structure 분석과 추가 verifier를 중단한다.
- 총 예산 90%에 도달하면 B2의 E0, E1, E4와 Neo4j export만 수행한다.
- 강한 모델은 reference의 고위험 잔여 충돌에만 사용한다.
- 모델의 장문 설명과 chain-of-thought를 요청하지 않는다.
- JSON이 유효하면 재질문하지 않는다.
- 동일 evidence bundle, prompt, model 조합은 content hash cache를 사용한다.

---

## 10. 평가 기준

### 10.1 Reference 품질

| 지표 | 계산 |
|---|---|
| JSON validity | schema 통과 call / 전체 call |
| Source-span validity | 실제 원문 substring인 span / 전체 span |
| A–B claim existence agreement | 정렬된 claim 수 기반 F1 |
| Claim family agreement | Cohen's kappa 또는 raw agreement |
| Fine claim type agreement | Macro agreement |
| Modality/polarity agreement | exact match |
| Condition span agreement | token overlap F1 |
| Adjudication rate | C 또는 D가 필요한 unit / 전체 unit |
| Silver-A coverage | Silver-A claim / 전체 확정 claim |
| Challenge rate | 미해결 claim / 전체 후보 claim |

### 10.2 Claim 추출 품질

Primary reference는 Silver-A+Silver-B다. Silver-A만 사용한 민감도 분석을 함께 보고한다.

| 평가 대상 | 지표 |
|---|---|
| Claim 존재 | Precision, Recall, F1 |
| Claim family | Macro-F1 |
| Fine claim type | Macro-F1, support와 함께 보고 |
| Subject/object/event argument | exact·partial span F1 |
| Modality | Macro-F1, critical confusion matrix |
| Polarity | F1 |
| Condition/exception | exact·partial span F1 |
| Promotion target | Macro-F1 |

### 10.3 Graph assertion 품질

- factual assertion Precision/Recall/F1
- process directed edge F1
- activity–output relation F1
- rule antecedent/consequent F1
- full-rule exact match
- evaluation observation field accuracy
- unsupported assertion rate
- source-link exact match
- duplicate relation rate
- false concept merge rate

### 10.4 Critical error rate

다음은 일반 오류와 별도로 합산한다.

```text
MUST ↔ SHOULD/MAY 혼동
MUST_NOT 또는 부정 누락
조건 제거 후 전역 assertion 생성
Example/CounterExample/Question을 fact로 승격
원문 밖 assertion
잘못된 sense merge로 여러 edge 오염
```

```text
critical_error_rate = critical_error_count / 평가 대상 claim 수
```

Claim-first와 Direct Triple의 핵심 비교는 일반 triple F1보다 이 지표를 우선한다.

### 10.5 비용 효율

- API call 수
- input/output token
- 실제 비용
- accepted claim당 token과 비용
- LLM으로 보낸 후보 비율
- cache hit rate
- distillation 전후 call 감소율
- Full-LLM 대비 Selective-LLM token 비율

### 10.6 Neo4j·감사 가능성

- node/relationship import 성공 수
- constraint violation 수
- accepted claim의 evidence path coverage
- orphan Claim/Assertion 수
- `NeedsReview`와 operational graph 분리 여부
- competency query pass rate
- graph에서 source row까지 이동 가능한 비율

### 10.7 통계 처리

파일럿 표본이 작고 reference가 LLM-Silver이므로 p-value 중심의 강한 결론을 피한다.

- B2 evidence bundle 단위 paired bootstrap 2,000회
- F1 차이와 critical error 차이의 95% confidence interval
- 같은 unit에서의 success/failure는 McNemar 결과를 참고값으로 제시
- effect size와 raw count를 반드시 함께 보고
- Challenge set은 별도 표로 정성 분석

---

## 11. Neo4j 그래프 설계와 필수 산출물

### 11.1 두 개의 뷰

#### A. Audit Graph

LLM-Silver와 시스템 판단을 포함하여 근거와 상태를 추적한다.

```text
(Document)-[:CONTAINS]->(Section)
(Section)-[:CONTAINS]->(Evidence)
(Evidence)-[:SUPPORTS]->(Claim)
(Claim)-[:PROMOTED_TO]->(Assertion)
(Claim)-[:REFERS_TO]->(Concept)
(Claim)-[:HAS_CONDITION]->(Condition)
```

#### B. Operational Projection

accepted claim만 업무용 edge로 materialize한다.

```text
(Task)-[:PRODUCES]->(Artifact)
(Event)-[:TRIGGERS]->(Decision)
(Stage)-[:PRECEDES]->(Stage)
(Rule)-[:HAS_ANTECEDENT]->(Condition)
(Rule)-[:HAS_CONSEQUENT]->(Action)
(EvaluationObservation)-[:EVALUATES]->(Entity)
```

### 11.2 Assertion 노드의 사용

Neo4j 관계만으로 provenance와 claim ID를 일관되게 연결하기 어려운 경우 `Assertion`을 1급 노드로 둔다.

```text
(Claim)-[:PROMOTED_TO]->(Assertion)
(Assertion)-[:SUBJECT]->(EntityA)
(Assertion)-[:OBJECT]->(EntityB)
Assertion.predicate = "PRODUCES"
```

Operational Projection에서는 다음 직접 edge를 추가한다.

```text
(EntityA)-[:PRODUCES {
  assertion_id,
  claim_id,
  evidence_id,
  confidence,
  reference_tier
}]->(EntityB)
```

### 11.3 필수 속성

#### Claim

```text
id
claim_family
claim_type
modality
polarity
status
confidence
reference_tier
annotation_source
human_reviewed
prompt_version
model_id
```

#### Evidence

```text
id
source_file
sheet
excel_row
page
chapter
section
text_hash
context_recovered
```

#### Assertion

```text
id
predicate
promotion_target
status
confidence
source_claim_id
source_evidence_id
system_version
```

### 11.4 Export 파일

```text
neo4j_documents.csv
neo4j_sections.csv
neo4j_evidence.csv
neo4j_claims.csv
neo4j_concepts.csv
neo4j_assertions.csv
neo4j_rules.csv
neo4j_nodes.csv              # 선택적 통합본
neo4j_relationships.csv      # 선택적 통합본
neo4j_constraints.cypher
neo4j_import.cypher
neo4j_validation_queries.cypher
```

파일럿 규모에서는 Neo4j `LOAD CSV` 또는 공식 driver를 사용한다. 대규모 bulk import 전용 도구는 전체 corpus가 훨씬 커진 이후 검토한다.

### 11.5 필수 검증 query

1. accepted claim 중 evidence가 없는 것
2. accepted assertion 중 source claim이 없는 것
3. 중복 ID
4. operational edge 중 claim/evidence 속성이 없는 것
5. Example/CounterExample인데 operational graph에 들어간 것
6. MUST_NOT인데 polarity 또는 rule 구조가 모순인 것
7. NeedsReview가 operational projection에 포함된 것
8. 같은 surface label에 여러 sense가 있는데 강제 병합된 것
9. 고아 Concept
10. competency query 10개

### 11.6 파일럿 competency query 예시

1. 각 수주 단계가 생성하는 산출물은 무엇인가?
2. RFP Available이 촉발하는 의사결정은 무엇인가?
3. MUST 또는 MUST_NOT인 규칙과 그 원문 근거는 무엇인가?
4. Capture Plan의 서로 다른 sense와 각 근거는 무엇인가?
5. 경쟁자 분석이 생성하는 산출물은 무엇인가?
6. BCM 평가 관측의 대상·기준·가중치·점수는 무엇인가?
7. 가치제안 수식의 operand와 해석은 무엇인가?
8. 예시와 반례로 분류되어 승격되지 않은 claim은 무엇인가?
9. 리스크와 권장 완화 행동은 무엇인가?
10. 현재 NeedsReview인 고위험 claim은 무엇인가?

---

## 12. 실행 순서

### Step 0. 실험 계약 동결

- `atomic_claim_schema_v0.2.json` 동결
- claim type과 promotion target enum 동결
- API 상한 동결
- 모델 역할과 model ID 기록
- prompt version과 hash 생성
- 10개 competency query 동결

### Step 1. 구조 전처리

- 1,366개 evidence ID 생성
- 장·절·페이지·행 정보 연결
- 표·목록·수식 block type 판정
- context bundle 생성
- near-duplicate cluster 생성

산출물:

```text
document_graph.jsonl
evidence_bundles_all.jsonl
duplicate_clusters.json
```

### Step 2. 180개 표본 추출과 split 잠금

- 150개 층화 + 30개 무작위
- group split으로 CAL/B1/B2 배정
- B2 manifest 별도 잠금

산출물:

```text
pilot_manifest.csv
cal_ids.txt
b1_ids.txt
b2_locked_ids.txt
```

### Step 3. LLM-Silver 생성

1. A 전체 주석
2. B 전체 독립 주석
3. 자동 schema/span validation
4. claim alignment
5. 불일치만 C
6. 고위험 잔여 충돌만 D
7. Silver-A/B/Challenge 확정

산출물:

```text
silver_raw_A.jsonl
silver_raw_B.jsonl
silver_raw_C.jsonl
silver_adjudication_D.jsonl
silver_reference_v0.1.jsonl
challenge_set_v0.1.jsonl
reference_quality_report.json
```

### Step 4. CAL에서 No-LLM 파이프라인 조정

- LF precision과 coverage 계산
- weight와 threshold 고정
- promotion policy와 high-risk threshold 고정
- B2를 보지 않음

산출물:

```text
lf_registry_v0.1.yaml
calibration_report.json
promotion_policy_v0.1.yaml
```

### Step 5. B1a에서 Selective-LLM 실행

- E2 후보와 confidence 생성
- gate 상위 후보만 M-E 호출
- LLM 판정과 비용 저장
- LF 후보 생성

### Step 6. B1b에서 LF 검증

- LF precision/support 측정
- 통과 LF만 활성화
- 실패 LF는 보존하되 disabled 상태
- B2용 E4 파이프라인 동결

산출물:

```text
lf_registry_v0.2_frozen.yaml
b1_metrics.json
b1_cost_ledger.csv
```

### Step 7. B2 최종 실행

동결된 B2에 다음을 실행한다.

```text
E0 DirectTriple-LLM
E1 ClaimFirst-FullLLM
E2 TRACE-NoLLM
E4 TRACE-Selective+Distillation
E2-Flat structure ablation
```

B2 실행 후에는 어떤 시스템 출력도 수동 수정하지 않는다.

### Step 8. Graph compile과 Neo4j 적재

- Audit Graph 생성
- Silver-A/B와 E4 accepted claim을 구분하여 적재
- Operational Projection 생성
- constraint와 validation query 실행
- Browser/Bloom 시각화 query 저장

### Step 9. 평가와 오류 분석

- reference quality
- claim/graph 품질
- critical error
- token/cost
- distillation call 감소
- Neo4j CQ 결과
- Challenge set 사례 분석

### Step 10. 버전 결정

파일럿 결과에 따라 다음 중 하나를 선택한다.

```text
PROCEED: 전체 1,366개로 확대
REVISE: schema/prompt/LF 수정 후 새 B2 필요
NARROW: claim type 또는 promotion 범위를 축소
STOP: Silver 신뢰도나 provenance 구조가 파일럿 기준 미달
```

---

## 13. Go / Revise / Stop 기준

### Proceed

다음을 모두 충족하면 전체 corpus 확대를 진행한다.

- source-span validity 98% 이상
- Silver-A+B coverage 80% 이상
- Challenge rate 20% 이하
- Claim-first critical error가 Direct Triple보다 상대적으로 30% 이상 낮음
- E4의 claim family Macro-F1이 E1보다 0.05 이상 낮지 않음
- E4 token이 E1의 40% 이하
- accepted assertion evidence path coverage 100%
- competency query 8/10 이상 통과
- API 상한 내 완료

### Revise

다음 중 하나면 schema, prompt 또는 LF를 수정하고 새로운 locked test를 만든다.

- Silver-A+B coverage 60–79%
- Challenge rate 20–30%
- fine claim type은 불안정하나 family 수준은 안정적
- 조건·예외 span 오류가 집중됨
- 선택적 LLM 호출률이 15%를 지속적으로 초과
- distillation LF가 일반화되지 않음
- Neo4j import는 성공하지만 relation fragmentation이 큼

### Stop 또는 범위 축소

- source-span validity 95% 미만
- 원문 밖 assertion이 반복됨
- high-risk conflict 미해결이 30% 초과
- Claim-first도 예시·금지·조건 오류를 충분히 줄이지 못함
- accepted assertion의 evidence path coverage가 100%가 아님
- API 비용이 상한을 크게 초과하고 cache/batching 개선 여지가 없음

범위 축소 시에는 우선 `Definition`, `ActivityOutput`, `ProcessOrder`, `Obligation/Prohibition`, `Example blocking`만 남기고 복잡한 sense induction과 수식 해석을 후속 단계로 미룬다.

---

## 14. 전체 corpus 확대 시 비용 절감형 후속안

파일럿이 Proceed 기준을 통과한 뒤 남은 약 1,186개 unit에 대해서는 A·B 이중 주석을 그대로 반복하지 않는다.

### 확대 주석 정책

```text
1차: 저비용 모델 1회 주석
2차: 다음 사례에만 추가 주석
     - high-risk modality/negation
     - gate uncertainty 상위 20%
     - 새 relation/sense 후보
     - schema/validation 오류
3차: 잔여 고위험 충돌만 strong adjudicator
```

이 방식은 파일럿에서 검증된 LF와 promotion policy를 재사용하기 때문에 전체 corpus에 대한 API 사용량을 줄일 수 있다.

### 후속 인간 Gold-Core

논문·대외 성능 주장을 위해서는 이후 다음을 권고한다.

- 50–100개 층화 표본
- 최소 3명의 인간 주석 또는 2명+adjudicator
- 일부는 LLM 결과를 보지 않는 blind annotation
- LLM-Silver와 인간 간 agreement 및 bias 점검
- `TRACE-Gold-Core-v1.0` 생성

LLM이 annotation을 대체할 수 있는지는 과제별로 달라질 수 있으므로, 작은 인간 검증 subset을 사용해 정당화하는 절차가 최근 제안되어 있다. 또한 다수의 저비용 모델 주석을 결합하는 방식은 비용 절감 가능성이 있지만, 과제별 aggregation 검증이 필요하다.

---

## 15. 결과 보고 문구

### 사용 가능한 표현

> TRACE-OL 파일럿은 180개 evidence unit에 대해 LLM-Silver Reference v0.1을 구축하고, 잠금된 60개 test unit에서 Direct Triple, Full-LLM Claim-first, No-LLM 및 Selective-LLM 조건을 비교하였다.

> 보고된 F1은 전문가 Gold가 아니라 LLM-Silver와의 일치도이다.

> Neo4j 그래프는 LLM-Silver 또는 TRACE-OL 예측에 기반한 provisional graph이며, human-reviewed 속성은 false다.

### 피해야 할 표현

```text
전문가 Gold 기준 정확도
사람 전문가 수준을 달성
최종 온톨로지 완성
실제 업무 수행에 안전함이 입증
전체 1,366개 데이터에서 검증 완료
```

---

## 16. 최종 산출물 체크리스트

### Reference

- [ ] `pilot_manifest.csv`
- [ ] `evidence_bundles.jsonl`
- [ ] `silver_raw_A/B/C.jsonl`
- [ ] `silver_adjudication_D.jsonl`
- [ ] `silver_reference_v0.1.jsonl`
- [ ] `challenge_set_v0.1.jsonl`
- [ ] `reference_quality_report.json`

### Systems

- [ ] `pred_E0_direct_triple.jsonl`
- [ ] `pred_E1_full_claim.jsonl`
- [ ] `pred_E2_no_llm.jsonl`
- [ ] `pred_E4_selective_distill.jsonl`
- [ ] `lf_registry_v0.2_frozen.yaml`
- [ ] `llm_decisions.jsonl`
- [ ] `cost_ledger.csv`

### Evaluation

- [ ] `metrics_reference.json`
- [ ] `metrics_claim.json`
- [ ] `metrics_graph.json`
- [ ] `critical_errors.csv`
- [ ] `bootstrap_intervals.json`
- [ ] `pilot_report.md`

### Neo4j

- [ ] node/relationship CSV
- [ ] constraints/import/validation Cypher
- [ ] node·relationship count report
- [ ] competency query result
- [ ] Audit Graph screenshot 또는 export
- [ ] Operational Graph screenshot 또는 export

---

## 17. 참고 근거

- Calderon, Reichart, and Dror (2025), *The Alternative Annotator Test for LLM-as-a-Judge*. 적은 인간 주석 subset으로 LLM annotator 사용을 정당화하는 통계 절차를 제안한다.
- Bavaresco et al. (2025), *LLMs instead of Human Judges? A Large Scale Empirical Study across 20 NLP Evaluation Tasks*. LLM judge의 유효성이 과제와 설정에 따라 달라지고 재현성 문제가 있음을 대규모로 비교한다.
- Liu and Hou (2026), *Aggregating Crowd of LLMs for Cost-Effective Data Annotation*. 여러 소형 LLM의 주석을 결합하는 비용 효율적 접근을 평가한다.
- Ratner et al. (2017/2020), *Snorkel: Rapid Training Data Creation with Weak Supervision*. 충돌하고 abstain하는 labeling function을 결합하는 약한 감독의 기본 틀을 제공한다.
- Neo4j Cypher Manual, current documentation. 파일럿 규모의 CSV 적재와 uniqueness constraint 설정에 사용한다.

---

## 18. 한 문장 요약

> **180개 표본에서 두 저비용 LLM의 독립 주석으로 provisional Silver를 만들고, 불일치에만 추가 비용을 쓰며, 잠근 60개 test에서 Claim-first·선택적 LLM·규칙 증류를 비교한 뒤, 모든 accepted assertion을 원문 근거와 함께 Neo4j Audit Graph와 Operational Graph로 실제 적재한다.**
