# 자이제_1 LLM API 기반 후속 실험 설계서

> **문서 유형:** 기존 「자이제_1 단일 도메인 온톨로지 자동 구축 실험 설계서」의 Gate 1 이후 수정·보완안  
> **대상 범위:** `자이제_1.xlsx` 단일 도메인, Transfer 직전까지  
> **기준일:** 2026-07-11  
> **입력 파일 SHA-256:** `9246a6da6c7635b3f34ee55df75112eb38a2984ea06828be943dc196de5926eb`  
> **권장 문서 상태:** `preregistration amendment v1`로 잠금  

---

## 0. 결론과 즉시 실행 원칙

현재 Gate 0은 통과했으므로 데이터와 split은 다시 만들지 않는다. 다음 단계에서는 인간 주석을 기다리지 않고 LLM API를 이용해 **LLM-Derived Reference, LDR**를 구축한 뒤 E0~E5와 온톨로지 평가를 진행한다.

다만 LDR은 인간 전문가 Gold와 동일한 지위를 갖지 않는다. 따라서 이번 단계에서 측정되는 값은 다음과 같이 해석한다.

> **시스템 정확도**가 아니라 **잠긴 다중-LLM 기준셋에 대한 일치도와 상대적 성능**을 측정한다.

이에 따라 기존 Gate 1~7의 구조를 유지하되, 인간 Gold가 없는 현재 단계의 최종 판정은 `PASS`가 아니라 다음 중 하나로 제한한다.

- `PROVISIONAL_PASS`: LDR 기준으로 방법론의 단일 도메인 타당성이 지지됨
- `ENGINEERING_PASS`: 파이프라인·비용·재현성은 통과했으나 LDR 신뢰도 또는 품질 게이트 일부가 약함
- `REVISE`: 기준셋 또는 시스템 설계를 수정해야 함
- `INVALID`: 누출·순환 평가·모델 잠금 위반으로 결과를 사용할 수 없음

원래 설계서의 인간 Gold 단계는 삭제하지 않고 **향후 confirmatory validation으로 연기**한다. 현재 LLM 실험은 그 이전의 연구개발·가설 선별 단계다.

### 지금 바로 수행할 순서

1. 기존 사전등록을 보존하고 `LLM reference amendment`를 추가한다.
2. 모델 역할·snapshot·prompt·schema·API 정책을 잠근다.
3. 준비된 PILOT 40건을 대상으로 독립 LLM 주석과 반복 안정성 실험을 수행한다.
4. Gate 1L을 통과하면 INDUCTION·VALIDATION용 LDR만 만든다.
5. E0~E5와 ontology induction을 개발·검증한다.
6. 모든 시스템과 threshold를 동결한다.
7. 동결 이후에만 TEST_NATURAL 140건과 TEST_CHALLENGE 60건의 LDR을 생성한다.
8. 잠긴 평가를 한 번 실행하고, 그 뒤에만 test 오류를 열람한다.
9. 선택된 시스템으로 전체 1,366건의 산출용 ontology를 만든다.

---

# 1. 현재 상태와 고정 사항

## 1.1 Phase 0 결과

본 설계서는 다음 보고 결과를 이미 통과한 사실로 간주한다.

| 항목 | 현재 상태 |
|---|---:|
| Gate 0 데이터·분할 무결성 | PASS |
| Evidence | 1,366 |
| Leakage group | 168 |
| split 간 leakage group 중복 | 0 |
| INDUCTION | 681 |
| VALIDATION | 272 |
| TEST_NATURAL | 275 |
| TEST_CHALLENGE_POOL | 138 |
| 잠금된 기준셋 표본 | 420 |
| PILOT 표본 | 40 |
| 표·템플릿 대상 | 56 |
| TEST 기준셋 사전 접근 | 0 |
| OpenAI API 호출 | 0 |
| 누적 API 토큰 | 0 |

이 수치와 split manifest는 본 수정 설계에서도 변경하지 않는다.

## 1.2 입력 파일 선택

주 실험 입력은 설계서의 binary hash와 일치하는 다음 파일이다.

```text
legacy/자이제_1.xlsx
```

497·916·1140행의 메타데이터가 보완된 handoff 수정본은 주 실험 입력으로 교체하지 않는다. 수정본은 다음 목적에만 사용한다.

- 누락 메타데이터에 대한 민감도 분석
- context repair가 추출 결과에 미치는 영향 분석
- 최종 산출물 생성 시 보조 view

주 실험에서는 세 행을 `metadata_missing=true`로 유지하고, 인접 Evidence bundle을 통해서만 문맥을 보완한다. 수정된 메타데이터를 원문 사실처럼 주입해서는 안 된다.

## 1.3 변경하면 안 되는 항목

- Evidence ID
- leakage group ID
- split 배정
- 420개 표본의 membership
- PILOT 40개 membership
- 표·템플릿 56개 membership
- input binary/content hash
- 기존 Gate 0 보고서

수정이 필요한 경우 기존 run을 폐기하지 말고 새로운 experiment ID를 만든다.

---

# 2. 실험의 지위와 용어

## 2.1 LDR의 정의

**LLM-Derived Reference, LDR**는 두 개 이상의 독립 LLM 주석 결과, 불일치 조정, 근거 검증, 제약 검사를 결합해 만든 잠정 기준셋이다.

LDR에는 다음 상태가 존재한다.

| 상태 | 의미 | 평가 사용 |
|---|---|---|
| `CONSENSUS_CORE` | 독립 annotator 합의 + 근거 검증 통과 | 주요 평가 |
| `ADJUDICATED` | 독립 결과 불일치를 adjudicator가 해소하고 검증 통과 | 주요 평가, 별도 표시 |
| `UNDERDETERMINED` | Evidence만으로 단일 정답을 확정하기 어려움 | abstention 평가 |
| `QUARANTINED` | 근거·형식·제약 문제가 해결되지 않음 | 주요 F1 제외, 실패율 보고 |
| `NEGATIVE_CONTROL` | 인위적 교란·반례 검사 항목 | LDR 품질 감사에만 사용 |

## 2.2 금지 용어

인간 전문가 검증 전에는 다음 표현을 사용하지 않는다.

- human gold
- ground truth
- 전문가 수준 정확도
- 실제 정확도 85% 달성
- 완전 자동 ontology 검증 완료

대신 다음처럼 표현한다.

- LDR-consistency F1
- model-reference agreement
- provisional ontology quality
- evidence-grounded consensus coverage
- human validation pending

## 2.3 현재 단계에서 가능한 주장

가능한 주장:

> 자이제 단일 도메인에서, 잠긴 다중-LLM 기준셋을 기준으로 Claim-first 방식과 선택적 LLM 방식의 상대적 품질·비용·근거 추적성 차이를 관찰했다.

현재 단계에서 불가능한 주장:

> 전문가가 구축한 정답 온톨로지 대비 정확도가 목표치를 달성했다.

---

# 3. 기존 설계서 변경표

| 기존 항목 | 수정 항목 | 처리 |
|---|---|---|
| Gate 1 인간 Gold 품질 | Gate 1L LLM Reference 품질 | 현재 단계에서 대체 |
| 인간 이중 주석 | 독립 LLM 2개 + 조건부 adjudicator + verifier | 적용 |
| IAA | Inter-Model Agreement, IMA + Intra-Model Stability, IMS | 명칭 변경 |
| Gold 420 | LDR 420 | membership 유지 |
| TEST Gold 사전 생성 | 시스템 freeze 후 TEST LDR 생성 | 누출 방지 강화 |
| PASS | PROVISIONAL_PASS | 인간 검증 전 주장 축소 |
| LLM-Silver 단일 모델 | 다중 역할·모델·블라인드 합의 | 순환성 완화 |
| E0~E5 비용 | 시스템 비용만 비교 | reference 비용은 별도 원장 |
| 인간 adjudicator | LLM adjudicator | 잠정 적용 |
| 최종 human confirmation | deferred phase | 현재 실험 비차단 |

---

# 4. 연구 질문과 가설

## RQ-L1. LLM만으로 재현 가능한 잠정 기준셋을 만들 수 있는가?

- 독립 LLM annotator 간 핵심 필드 합의가 허용 기준을 넘는가?
- 동일 모델·설정 반복 시 출력이 안정적인가?
- consensus가 exact evidence span과 일치하는가?
- 고위험 Claim에서 합의와 검증을 동시에 만족하는가?

### H-L1

PILOT에서 정의한 Gate 1L 기준을 통과하면 LDR-DEV 생성으로 진행한다.

## RQ1. Claim-first 표현은 direct triple보다 의미를 잘 보존하는가?

### H1-P

E1이 E0보다 critical semantic error를 유의하게 줄이고 source grounding을 악화시키지 않는다.

## RQ2. 구조·규칙·제약 기반 비LLM 경로가 ontology induction에 기여하는가?

### H2-P

E2가 단순 규칙 기준선보다 concept typing, relation, RuleFrame, template 구조에서 우수하다.

## RQ3. 선택적 LLM은 전수 LLM과 유사한 품질을 더 적은 토큰으로 달성하는가?

### H3-P

E4가 E5에 대해 사전 정의된 비열등성 조건을 충족하면서 LLM 검토량과 토큰을 줄인다.

## RQ4. 위험·다양성·그래프 효용을 고려한 선택이 uncertainty-only보다 우수한가?

### H4-P

동일 budget에서 E4가 E3보다 CSER, contextualized assertion F1, CQ 기여도 중 두 개 이상에서 우세하고 나머지에서 실질적으로 열등하지 않다.

## RQ5. 생성 결과가 실행 가능한 ontology인가?

### H5-P

RDF/Property Graph 적재, SHACL 검사, provenance query, CQ-TEST가 잠정 기준을 통과한다.

---

# 5. LDR 구축 아키텍처

## 5.1 역할 구성

```text
Evidence Bundle
   ├─ Annotator A: Domain-first, high-recall annotation
   ├─ Annotator B: Ontology-first, high-precision annotation
   │
   └─ Alignment & Disagreement Detection
          ├─ 합의 → Grounding Verifier
          └─ 불일치 → Blind Adjudicator → Grounding Verifier

Grounding Verifier
   ├─ quote exactness
   ├─ entailment/support
   ├─ modality/polarity/condition preservation
   ├─ example-to-rule contamination
   └─ scope overreach

Deterministic Validator
   ├─ JSON Schema
   ├─ source substring
   ├─ stable IDs
   ├─ label registry
   ├─ graph constraints
   └─ provenance completeness

→ LDR status assignment
```

## 5.2 Annotator A — Domain-first

목표는 업무 지식의 누락을 줄이는 것이다.

- Evidence에 명시되거나 직접적으로 지지되는 Atomic Work Claim을 높은 recall로 추출
- 역할·행위·입력·산출물·조건·권고·금지·예외를 우선 식별
- 수주·제안 분야의 일반 지식을 추가하지 않음
- 모든 Claim에 exact quote 요구
- 불확실하면 추측하지 않고 field 단위 `UNDERDETERMINED`

## 5.3 Annotator B — Ontology-first

목표는 과잉 추출과 스키마 오염을 줄이는 것이다.

- A의 결과를 보지 않고 처음부터 독립 주석
- class/instance, general/example, task/artifact/rule/metric 구분을 엄격하게 적용
- relation domain/range와 promotion 가능성을 보수적으로 판단
- 질문·오해·반박·예시를 일반 규칙으로 승격하지 않음
- 명시적 source quote가 없는 argument는 생성하지 않음

## 5.4 Blind Adjudicator

A와 B가 불일치한 bundle만 처리한다.

- 두 결과를 `candidate_x`, `candidate_y`로 익명화
- 입력 순서를 무작위로 바꿈
- 모델명·역할명·가격·기존 점수 비공개
- 선택 가능한 결정:
  - `ACCEPT_X`
  - `ACCEPT_Y`
  - `MERGE_SUPPORTED_FIELDS`
  - `REJECT_BOTH`
  - `UNDERDETERMINED`
- 두 annotator가 모두 놓친 Claim 추가는 원칙적으로 금지
- 예외적으로 exact quote가 존재하고 누락이 명백하면 `ADJUDICATOR_ADDED`로 표시하며 별도 오류율에 포함

## 5.5 Grounding Verifier / Falsifier

Verifier는 consensus를 그대로 승인하는 모델이 아니라, 틀릴 이유를 찾는 역할이다.

검사 필드:

- `quote_is_exact_substring`
- `claim_is_supported`
- `argument_is_supported`
- `modality_preserved`
- `polarity_preserved`
- `condition_preserved`
- `exception_preserved`
- `scope_not_overgeneralized`
- `example_not_promoted_as_rule`
- `numeric_value_and_unit_preserved`

판정:

- `ENTAILED`
- `CONTRADICTED`
- `UNDERDETERMINED`

고위험 Claim은 `ENTAILED`가 아니면 `CONSENSUS_CORE`로 들어갈 수 없다.

## 5.6 결정론적 검증

LLM이 직접 문자 offset을 생성하게 하지 않는다. LLM은 exact quote를 반환하고, 프로그램이 원문에서 위치를 계산한다.

- quote가 원문에 1회 존재: 자동 offset 부여
- 여러 번 존재: 주변 context를 사용해 disambiguation
- 존재하지 않음: 해당 API 응답 전체 또는 Claim을 reject
- 정규화된 text가 필요해도 raw quote를 별도 보존
- 숫자·범위·단위는 문자열과 파싱값을 함께 저장

---

# 6. 모델 선택과 순환성 방지

## 6.1 우선 모델 정책

가장 바람직한 구성은 annotator A와 B가 서로 다른 모델 계열 또는 공급자에 속하는 것이다. 서로 다른 모델의 panel이 단일 judge의 고유 편향과 self-preference를 줄일 수 있다는 선행 결과가 있기 때문이다. 다만 현재 OpenAI API만 사용할 수 있다면 아래 fallback을 적용한다.

### 권장 모드: `MULTI_FAMILY`

- Annotator A: pinned model family 1
- Annotator B: pinned model family 2
- Adjudicator: A/B와 다른 강한 모델 또는 family 3
- Verifier: candidate 생성 모델과 다른 모델

### 허용 모드: `OPENAI_MULTI_SNAPSHOT`

- A와 B에 서로 다른 pinned snapshot 또는 서로 다른 모델 계층 사용
- adjudicator는 A/B와 다른 snapshot
- E0/E1 생성 모델은 reference annotator와 다른 snapshot을 우선 사용
- 모델 중복이 있으면 leave-overlap-out 점수를 추가 계산

### 최후 fallback: `SINGLE_SNAPSHOT_MULTI_ROLE`

하나의 snapshot만 쓸 수 있을 때:

- A와 B의 system prompt, 예시, 출력 순서, task framing 분리
- 각 PILOT 항목을 역할별 3회 독립 실행
- adjudicator 입력 순서 swap audit 수행
- 결과는 `ENGINEERING_ONLY`로 표시
- `PROVISIONAL_PASS` 판정 금지

## 6.2 모델 snapshot 잠금

모델 alias가 아니라 가능한 경우 날짜가 포함된 snapshot ID를 기록한다. 모델 변경은 새로운 experiment run으로 처리한다. OpenAI 공식 문서도 일관된 동작을 위해 production에서 특정 snapshot을 pin하고 eval suite로 변경을 감시할 것을 권고한다.

필수 manifest:

```yaml
reference_annotator_a:
  provider: openai
  model_snapshot: "<PINNED_MODEL_A>"
  prompt_hash: "..."
  schema_hash: "..."

reference_annotator_b:
  provider: openai
  model_snapshot: "<PINNED_MODEL_B>"
  prompt_hash: "..."
  schema_hash: "..."

reference_adjudicator:
  provider: openai
  model_snapshot: "<PINNED_MODEL_C>"

reference_verifier:
  provider: openai
  model_snapshot: "<PINNED_MODEL_D>"

candidate_full_llm:
  provider: openai
  model_snapshot: "<PINNED_MODEL_E>"

selective_arbiter:
  provider: openai
  model_snapshot: "<PINNED_MODEL_F>"
```

## 6.3 동일 모델 편향 통제

시스템과 reference에 동일 snapshot이 포함되면 다음 세 점수를 모두 보고한다.

1. `ALL_PANEL`: 전체 LDR 기준
2. `LEAVE_OVERLAP_OUT`: 해당 시스템과 같은 snapshot의 표결을 제외한 reference 기준
3. `CONSENSUS_CORE_ONLY`: 독립 모델이 동일하게 합의한 core만 기준

`ALL_PANEL`만 보고해서는 안 된다.

## 6.4 블라인드 원칙

- LDR annotator는 E0~E5 출력을 보지 않는다.
- E0~E5 prompt에는 LDR label이나 adjudication rationale가 들어가지 않는다.
- TEST LDR은 시스템 freeze 전에는 생성하지 않는다.
- adjudicator는 A/B의 모델 ID를 모른다.
- pairwise 비교가 필요하면 output order를 무작위화하고 swap consistency를 검사한다.

---

# 7. API 실행 규칙

## 7.1 API 기능

- 구조화 주석은 JSON Schema 기반 Structured Outputs를 사용한다.
- 대량 비동기 주석은 가능하면 Batch API를 사용한다.
- PILOT과 오류 디버깅은 동기 API를 사용한다.
- API key는 환경변수 또는 secret manager에서만 읽는다.
- API key, bearer header, 전체 secret를 로그·manifest·Git에 저장하지 않는다.

OpenAI Structured Outputs는 단순 JSON mode와 달리 schema adherence를 보장하도록 설계되어 있으므로, 주석 필드 누락과 파싱 실패를 줄이는 데 적합하다. Batch API는 동기 API 대비 비용 할인과 높은 rate limit을 제공하므로 잠긴 대량 주석에 유리하다.

## 7.2 재시도 정책

허용 재시도:

- transport error
- rate limit
- timeout
- schema parse failure
- incomplete response
- refusal

금지 재시도:

- 연구자가 마음에 들지 않는 label
- 예상보다 낮은 agreement
- 시스템 성능을 높이기 위한 test reference 재생성

최대 2회 자동 재시도를 권장한다. 모든 attempt를 저장한다. 최종 성공 응답만 남기는 방식은 금지한다.

## 7.3 요청 캐시

캐시 키:

```text
SHA256(
  model_snapshot
  + prompt_hash
  + schema_hash
  + evidence_bundle_hash
  + role
  + inference_config_hash
)
```

동일 캐시 키에 대해 API를 중복 호출하지 않는다. 안정성 audit용 반복 호출은 `replicate_id`를 캐시 키에 포함한다.

## 7.4 필수 API 원장

각 request마다 저장한다.

- experiment ID
- custom request ID
- evidence ID / bundle hash
- split
- role
- model snapshot
- prompt hash
- schema hash
- request time
- response ID
- finish status
- input/output/cached/reasoning token usage
- retry count
- latency
- parsed output hash
- raw response path
- estimated and actual cost

Reference 생성 비용, 시스템 생성 비용, 평가 비용을 분리한다.

```text
cost/reference/
cost/system/
cost/evaluation/
```

E4/E1 token ratio에는 reference 구축 토큰을 넣지 않는다. 대신 총 연구비 관점에서는 세 비용을 모두 별도 보고한다.

---

# 8. 주석 스키마

## 8.1 AWC 출력 최소 스키마

```json
{
  "evidence_id": "E000001",
  "bundle_hash": "sha256:...",
  "annotation_role": "DOMAIN_FIRST",
  "claims": [
    {
      "claim_local_id": "c1",
      "claim_quote": "원문에 정확히 존재하는 인용문",
      "claim_family": "NORMATIVE",
      "claim_type": "RECOMMENDATION",
      "arguments": [
        {
          "role": "subject",
          "quote": "핵심 이해관계자",
          "normalized_label": "핵심 이해관계자"
        },
        {
          "role": "cardinality",
          "quote": "3~6명",
          "normalized_label": "[3,6]"
        }
      ],
      "predicate": "hasRecommendedCardinality",
      "modality": "SHOULD",
      "polarity": "POSITIVE",
      "condition_quote": "Capture Planning을 수행할 때",
      "exception_quote": null,
      "scope_quote": null,
      "discourse_status": "GENERAL_GUIDANCE",
      "promotion_target": "RULE",
      "uncertain_fields": []
    }
  ],
  "no_claim_reason": null
}
```

## 8.2 허용 라벨

### Claim family

- `PROCEDURAL`
- `NORMATIVE`
- `DEFINITIONAL`
- `DESCRIPTIVE`
- `ASSESSMENT`
- `DECISIONAL`
- `TEMPLATE_INSTRUCTION`
- `DISCOURSE`

### Modality

- `MUST`
- `MUST_NOT`
- `SHOULD`
- `SHOULD_NOT`
- `MAY`
- `DESCRIPTIVE`
- `UNSPECIFIED`

### Discourse status

- `GENERAL_RULE`
- `GENERAL_GUIDANCE`
- `DEFINITION`
- `EXAMPLE`
- `QUESTION`
- `MISCONCEPTION`
- `REBUTTAL`
- `QUOTATION`
- `CASE_INSTANCE`
- `OTHER`

### Promotion target

- `ASSERTION`
- `RULE`
- `PROCEDURE_EDGE`
- `CONCEPT_ONLY`
- `TEMPLATE_SCHEMA`
- `DO_NOT_PROMOTE`
- `UNDERDETERMINED`

## 8.3 모델 자기확신 사용 금지

모델이 출력한 0~1 confidence는 primary confidence로 사용하지 않는다. Reference confidence는 다음 관찰값으로 계산한다.

```text
ReferenceConfidence =
  0.30 × inter_model_agreement
+ 0.20 × intra_model_stability
+ 0.25 × grounding_verifier_score
+ 0.15 × deterministic_constraint_score
+ 0.10 × discourse_and_scope_consistency
```

가중치는 PILOT 전 사전등록하고, TEST 결과를 본 뒤 바꾸지 않는다. 모델 자기확신은 진단 필드로만 저장할 수 있다.

---

# 9. Phase 1L — PILOT 40건

## 9.1 목적

- guideline이 LLM에 의해 일관되게 해석되는지 확인
- label set의 모호성을 식별
- exact quote와 structured output의 실행 가능성 확인
- 모델 간 편향과 반복 불안정성 측정
- prompt 수정 여부 결정

## 9.2 실행 횟수

PILOT 40건은 다음처럼 실행한다.

| 역할 | 기본 실행 | 반복 실행 |
|---|---:|---:|
| Annotator A | 40 | 동일 설정 1회 추가 |
| Annotator B | 40 | 동일 설정 1회 추가 |
| Adjudicator | A/B 불일치 bundle | 10%는 입력 순서 swap |
| Verifier | consensus/adjudicated claim | 고위험 전수, 나머지 최소 50% |

PILOT에서는 비용보다 신뢰도 진단을 우선한다. 본 주석 단계에서는 반복 비율을 줄인다.

## 9.3 Alignment 방법

A와 B의 Claim을 다음 순서로 정렬한다.

1. exact quote 또는 character span overlap
2. claim family/type
3. predicate
4. argument role 및 quote overlap
5. modality/polarity/condition

Claim matching은 greedy가 아니라 최대 가중 bipartite matching을 사용한다. 매칭 threshold와 weight는 PILOT 전에 기록한다.

## 9.4 IMA와 IMS

### Inter-Model Agreement, IMA

- Claim span pairwise F1
- argument span pairwise F1
- claim family Krippendorff’s alpha
- claim type alpha
- modality alpha
- polarity alpha
- discourse status alpha
- promotion target alpha
- canonicalization agreement

### Intra-Model Stability, IMS

동일 snapshot·prompt·evidence를 반복 호출했을 때:

- Claim set F1
- critical field exact agreement
- normalized concept set agreement
- abstention consistency

낮은 온도 또는 deterministic 옵션을 사용해도 API 결과가 항상 동일하다고 가정하지 않는다.

## 9.5 Gate 1L 통과 기준

### 형식·근거 기준

| 지표 | 최소 기준 |
|---|---:|
| 최종 accepted response JSON schema validity | 1.00 |
| accepted Claim exact quote validity | 1.00 |
| evidence ID / bundle hash consistency | 1.00 |
| provenance 필수 필드 completeness | 1.00 |
| raw API failure rate | ≤ 0.02 |

### 합의 기준

| 지표 | 최소 | 목표 |
|---|---:|---:|
| Claim span pairwise F1 | 0.80 | 0.85 |
| Argument span pairwise F1 | 0.78 | 0.85 |
| Claim family alpha | 0.67 | 0.80 |
| Claim type alpha | 0.67 | 0.75 |
| Modality alpha | 0.75 | 0.80 |
| Polarity alpha | 0.80 | 0.90 |
| Promotion alpha | 0.75 | 0.80 |
| Critical-field IMS | 0.90 | 0.95 |
| Position-swap consistency | 0.90 | 0.95 |

`0.67~0.80` 구간은 잠정적 결론만 허용하고, 0.80 이상을 안정적 목표로 본다. 중요한 잘못이 규정 위반이나 규칙 오염을 유발하는 modality·polarity·promotion에는 더 높은 기준을 둔다.

### 위험·coverage 기준

| 지표 | 기준 |
|---|---:|
| 고위험 Claim verifier `ENTAILED` | ≥ 0.95 |
| example-to-rule contamination | ≤ 0.02 |
| adjudicator-added Claim 비율 | ≤ 0.05 |
| 전체 unresolved/underdetermined | ≤ 0.15 |
| high-risk unresolved | ≤ 0.10 |
| quarantine rate | ≤ 0.05 |

## 9.6 Gate 실패 시 처리

1. PILOT 결과만 보고 guideline/prompt를 최대 1회 수정한다.
2. 기존 PILOT과 겹치지 않는 INDUCTION 20건을 fresh re-pilot으로 사용한다.
3. 수정 prompt와 schema를 새 버전으로 잠근다.
4. 여전히 최소 기준 미달이면:
   - TEST LDR을 만들지 않음
   - E0~E5는 development-only로 제한
   - 최종 판정은 `REVISE`

PILOT 성능이 낮다는 이유로 TEST 표본을 보거나 TEST prompt를 반복 조정해서는 안 된다.

---

# 10. Phase 2L — LDR-DEV 구축

## 10.1 포함 범위

- PILOT 40: guideline 개발용, 최종 test 제외
- INDUCTION-GOLD membership 100: `LDR-INDUCTION`
- VALIDATION-GOLD membership 80: `LDR-VALIDATION`
- TEST_NATURAL 140: 이 단계에서 생성 금지
- TEST_CHALLENGE 60: 이 단계에서 생성 금지

## 10.2 주석 방식

- A/B 독립 annotation 전수
- agreement가 높은 저위험 Claim은 verifier 표본 검사 가능
- 다음은 verifier 전수:
  - MUST/MUST_NOT/SHOULD
  - condition/exception
  - negative claim
  - number/range/cardinality
  - process direction
  - example/general promotion
  - table/template instruction
- A/B 불일치 전수 adjudication
- 결과는 `CONSENSUS_CORE`, `ADJUDICATED`, `UNDERDETERMINED`, `QUARANTINED`로 구분

## 10.3 LDR를 training label로 사용할 때

LDR-INDUCTION은 LF, threshold, 소형 분류기, concept mapping 개발에 사용할 수 있다. 다만 LLM label noise를 증폭하지 않도록 다음을 지킨다.

- `CONSENSUS_CORE`만 supervised training의 기본 label로 사용
- `ADJUDICATED`는 낮은 sample weight
- `UNDERDETERMINED`는 abstention 학습에 사용
- `QUARANTINED`는 학습 제외
- reference annotator rationale를 candidate model prompt 예시로 사용 금지
- TEST reference는 어떤 학습에도 사용 금지

권장 sample weight:

| 상태 | weight |
|---|---:|
| CONSENSUS_CORE | 1.0 |
| ADJUDICATED | 0.6 |
| UNDERDETERMINED | abstention objective only |
| QUARANTINED | 0.0 |

## 10.4 표·템플릿 56개

56개 전수 대상이라는 원칙은 유지하되 split 누출을 막는다.

- INDUCTION/VALIDATION leakage group에 속한 표만 개발 시 공개
- TEST_NATURAL/CHALLENGE leakage group의 표 reference는 freeze 이후 생성
- 동일 table block의 caption/header/row/설명을 서로 다른 split으로 분리하지 않음
- instruction value와 example value를 분리
- scale, unit, range, cardinality를 구조화

## 10.5 Canonicalization pair 300개

추천 분할:

| 사용 | 수 |
|---|---:|
| INDUCTION | 180 |
| VALIDATION | 60 |
| LOCKED TEST | 60 |

기존 split과 충돌하면 수량보다 leakage group 일관성을 우선한다. locked pair는 freeze 전 열람하지 않는다.

## 10.6 Closed micrograph와 CQ

- Micrograph DEV 6개: ontology 설계에 사용
- Micrograph LOCK 6개: freeze 후 생성·평가
- CQ-DEV 20개: relation registry와 query shape 개발
- CQ-TEST 20개: freeze 전 접근 금지

LLM이 CQ를 생성하는 경우에도 CQ-TEST는 candidate system과 다른 model/prompt로 생성하고, answer set은 Evidence-grounded verifier를 통과해야 한다.

---

# 11. E0~E5 실행 설계

## 11.1 비교 시스템

| ID | 시스템 | LLM 사용 | 목적 |
|---|---|---|---|
| E0 | Direct Triple Full-LLM | 전수 | 평면 triple 기준선 |
| E1 | Full-LLM Atomic Work Claim | 전수 | Claim-first 고비용 기준선 |
| E2 | No-Generative-LLM SCALE-AWC | 없음 | 구조·규칙·소형모델 경로 |
| E3 | Uncertainty-only Selective LLM | 선택적 | 단순 선택 기준선 |
| E4 | Risk/Diversity/Graph-Utility Selective LLM | 선택적 | 최종 제안 시스템 |
| E5 | Exhaustive Gray-zone LLM | gray-zone 전수 | 선택정책 비교 기준선 |

## 11.2 LDR와 candidate 모델 분리

- E0/E1의 full-LLM 모델은 가능하면 Annotator A/B와 다른 snapshot 사용
- E3/E4/E5 arbiter도 reference adjudicator와 다른 snapshot을 우선
- 불가피한 overlap은 manifest에 기록
- overlap 시스템은 `LEAVE_OVERLAP_OUT` 결과를 primary sensitivity로 추가

## 11.3 공정 비교

E0과 E1:

- 동일 candidate model snapshot
- 동일 Evidence bundle
- 동일 context window
- 가능한 한 유사한 output budget
- E0는 direct triple, E1은 AWC schema만 다름

E3과 E4:

- 동일 candidate pool
- 동일 total candidate budget
- 동일 arbiter model
- selector만 다름

E4와 E5:

- 동일 base pipeline
- E4는 budgeted selection
- E5는 gray-zone 전수 검토

## 11.4 Reference leakage 방지

- E2 LF는 LDR-INDUCTION만 사용
- threshold와 budget은 LDR-VALIDATION에서만 선택
- relation registry의 도메인 확장은 DEV evidence만 사용
- TEST LDR 생성 전 code·config·prompt hash를 freeze

---

# 12. 선택적 LLM 정책

## 12.1 E4 선택 점수

```text
Score(c) =
  Uncertainty(c)
  × Risk(c)
  × GraphImpact(c)
  × CQGain(c)
  × DiversityGain(c)
  × Novelty(c)
  / EstimatedTokenCost(c)
```

## 12.2 선택 제약

- 한 claim family가 선택의 35%를 넘지 않음
- normative/condition, discourse/promotion, table/template, canonicalization, procedure 각각 최소 quota
- 같은 semantic cluster 중복 억제
- high-risk minimum quota
- 5% deterministic exploration
- 긴 evidence만 과도하게 선택되지 않도록 length normalization

## 12.3 Budget sweep

- 0%
- 5%
- 10%
- 20%
- 40%
- 100% gray-zone

VALIDATION에서 primary budget 하나를 고정하고 TEST에는 그 budget만 confirmatory로 적용한다. 나머지 budget은 secondary curve로 보고한다.

---

# 13. 시스템 freeze

## 13.1 Freeze 조건

다음이 모두 완료된 시점을 `SYSTEM_FREEZE_TIMESTAMP`로 기록한다.

- annotation guideline version
- LDR schema
- candidate schemas
- relation registry
- LF 목록과 버전
- small model checkpoint
- concept normalization rules
- selector formula와 weights
- risk class
- budget
- E0~E5 prompt hash
- model snapshot
- SHACL shapes
- evaluation code hash
- statistical analysis script hash

## 13.2 Freeze 산출물

```text
freeze/
  system_freeze_manifest.json
  code_commit.txt
  environment.lock
  prompts.sha256
  schemas.sha256
  shacl.sha256
  evaluation_code.sha256
  selector_config.yaml
  model_policy.yaml
```

## 13.3 Freeze 이후 금지

- prompt 수정
- threshold 수정
- budget 변경
- LF 추가·삭제
- relation label 통합·분리
- TEST LDR 재생성
- 실패한 test만 선택적 재호출

오류 수정이 필요한 경우 현재 run은 종료하고 새로운 experiment ID로 재시작한다.

---

# 14. Phase 3L — Locked TEST LDR 생성

## 14.1 생성 시점

TEST LDR은 반드시 `SYSTEM_FREEZE_TIMESTAMP` 이후 생성한다.

```text
test_reference_created_at > system_frozen_at
```

이를 자동 assertion으로 검사한다.

## 14.2 대상

- TEST-NATURAL-GOLD membership 140 → `LDR-TEST-NATURAL`
- TEST-CHALLENGE-GOLD membership 60 → `LDR-TEST-CHALLENGE`
- locked canonicalization pair 60
- locked micrograph 6
- CQ-TEST 20
- TEST split 표·템플릿

## 14.3 잠금 방식

가장 좋은 방식은 별도 process 또는 별도 OS user가 TEST reference를 생성하고 평가 스크립트만 접근하도록 하는 것이다. 어렵다면 최소한 다음을 적용한다.

1. TEST LDR 생성 전 candidate outputs를 이미 read-only로 고정
2. LDR raw files를 `locked/reference/`에 저장
3. 파일 hash 생성
4. 권한을 read-only로 변경
5. 평가 스크립트는 aggregate metric을 먼저 생성
6. 연구자는 aggregate 결과 잠금 후에만 개별 TEST label 열람

필수 로그:

- test reference access before freeze: 0
- reference generation start/end time
- model/prompt/schema hash
- raw response count
- retry count
- file hash
- first researcher access time

## 14.4 TEST 재호출 규칙

허용:

- transport failure
- schema failure
- exact quote invalid로 자동 reject된 request의 사전 정의된 retry

금지:

- annotator disagreement이 높아서 다른 모델로 다시 생성
- E4 점수가 낮아서 reference 변경
- 특정 예시가 마음에 들지 않아 재-adjudication

---

# 15. LDR 품질 감사

## 15.1 Negative controls

LLM 간 합의만으로는 공통 오류를 발견하기 어렵다. 따라서 PILOT과 TEST에 직접 포함되지 않는 별도 감사 세트를 만든다.

권장 control:

- condition phrase 삭제
- MUST를 MAY로 교체
- 숫자 3~6을 6~9로 교체
- 사례 주체를 일반 class로 바꿈
- process 순서 반전
- unrelated evidence와 claim 조합
- 문장 일부를 인용처럼 삽입

Verifier가 이러한 교란을 `ENTAILED`로 통과시키면 reference 품질 문제다.

권장 최소 40개 control을 사용하고, false acceptance rate ≤ 0.05를 목표로 한다.

## 15.2 Duplicate consistency

정확 중복 text가 존재하는 경우:

- context가 같은 duplicate는 동일 Claim set 기대
- context가 다른 duplicate는 차이를 설명하는 context field 필요
- duplicate consistency를 별도 보고

## 15.3 Context ablation

20개 이상의 bundle에서 다음을 비교한다.

- target row만 제공
- 기존 evidence bundle 제공

이를 통해 인접 문맥이 modality, 생략 논항, 표 구조에 미치는 영향을 측정한다. 본 평가의 primary input은 기존 evidence bundle이다.

## 15.4 Position audit

adjudicator 입력의 A/B 위치를 뒤집은 10% 표본에서 판정이 유지되는지 확인한다. LLM judge는 position bias가 알려져 있으므로 위치 일관성을 필수 감사 항목으로 둔다.

---

# 16. 평가 지표

## 16.1 Reference 자체의 지표

- IMA
- IMS
- consensus coverage
- adjudication rate
- adjudicator-added rate
- underdetermined rate
- quarantine rate
- exact quote validity
- verifier entailment rate
- negative-control false acceptance
- duplicate consistency
- position-swap consistency
- model별 label prevalence

## 16.2 Claim 지표

- Claim span precision/recall/F1
- argument span F1
- claim family Macro-F1
- claim type Macro-F1
- modality F1
- polarity F1
- condition/exception slot F1
- discourse status F1
- promotion F1
- source span validity
- Critical Semantic Error Rate, CSER

### Critical Semantic Error

다음 중 하나면 critical error로 센다.

- MUST ↔ MAY/SHOULD 혼동
- MUST ↔ MUST_NOT 또는 polarity 반전
- condition/exception 누락으로 규칙 범위 확대
- 사례를 일반 규칙으로 승격
- process direction 반전
- 숫자·범위·단위 오류
- source에서 지지되지 않는 핵심 argument
- class/instance 오염으로 ontology assertion 왜곡

## 16.3 Concept·schema 지표

- Term span F1
- Concept type Macro-F1
- canonicalization pair F1
- B³ / CEAF 또는 pairwise cluster F1
- taxonomy edge F1
- relation label F1
- domain/range validity
- relation proliferation rate
- orphan concept rate

## 16.4 Operational ontology 지표

- Strict Contextualized Assertion F1
- Relaxed Contextualized Assertion F1
- RuleFrame slot F1
- procedure edge F1
- table/template field F1
- metric/range/cardinality F1
- evidence precision
- unsupported edge rate
- example contamination rate
- SHACL violation rate
- provenance path coverage

## 16.5 CQ 지표

- answer-set precision/recall/F1
- evidence precision
- no-answer accuracy
- hop correctness
- unsupported answer rate
- query execution success

## 16.6 비용 지표

### Reference 비용

- LDR bundle당 token/cost
- consensus bundle당 cost
- adjudicated bundle당 cost
- verified claim당 cost
- reference 전체 비용

### System 비용

- evidence 1,000건당 token/cost
- accepted assertion당 token/cost
- E4/E1 token ratio
- E4/E5 token ratio
- LLM-reviewed candidate ratio
- cache hit rate

### Evaluation 비용

- judge/verifier 비용
- CQ 평가 비용
- repeated stability audit 비용

---

# 17. LDR 불확실성을 반영한 점수

## 17.1 Core score

`CONSENSUS_CORE`와 검증된 `ADJUDICATED`만 사용한다.

장점: reference noise가 낮다.  
한계: 어려운 예시를 제외해 성능이 높아질 수 있다.

## 17.2 All-case score

`UNDERDETERMINED`를 포함한다.

- 시스템이 적절히 `ABSTAIN`하면 정답 처리
- 단정적인 출력은 오류 처리
- quarantined reference는 denominator에 넣지 않고 quarantine rate를 별도 보고

## 17.3 Confidence-weighted score

각 reference assertion의 `ReferenceConfidence`를 weight로 사용한다. 이 점수는 secondary다. Primary는 해석이 명확한 unweighted core/all-case 지표다.

## 17.4 난이도 분리

반드시 따로 보고한다.

- TEST_NATURAL
- TEST_CHALLENGE
- high-risk subset
- table/template subset
- underdetermined subset

자연분포와 challenge를 단순 평균해 하나의 대표 점수로 만들지 않는다.

---

# 18. 통계 분석

## 18.1 재표본화 단위

Evidence row를 독립 표본으로 보지 않고 leakage group을 cluster로 사용한다.

- paired cluster bootstrap 5,000회
- 95% confidence interval
- 동일 group에서 시스템 결과를 paired 비교

## 18.2 Primary 비교

1. E1 vs E0: CSER 차이
2. E4 vs E5: 비열등성
3. E4 vs E3: 동일 budget 성능
4. E4 vs E2: 선택적 LLM의 증분 효과

## 18.3 비열등성

E4가 E5보다 현저히 싸면서 품질이 유사한지 검정한다.

권장 margin:

- Claim/Assertion F1: `-0.05`
- Evidence precision: `-0.02`
- CSER: E4가 E5보다 절대 `+0.03` 이상 악화되지 않음

margin은 TEST를 보기 전에 확정한다.

## 18.4 Reference 민감도 분석

각 시스템에 대해 다음 reference variant를 사용한다.

- ALL_PANEL
- LEAVE_OVERLAP_OUT
- CONSENSUS_CORE_ONLY
- ADJUDICATED_INCLUDED
- HIGH_CONFIDENCE_ONLY

시스템 순위가 reference variant에 따라 크게 바뀌면 `reference-sensitive`로 판정한다.

## 18.5 LLM 반복성

E0/E1/E4의 10% 표본을 동일 설정으로 한 번 더 실행한다.

- metric variation
- graph edge overlap
- claim set F1
- cost variation

동일 snapshot과 낮은 temperature에서도 비결정성이 있을 수 있으므로 결과 hash 동일을 LLM 경로의 필수 조건으로 두지 않는다. 대신 raw response와 cache replay 재현성을 보장한다.

---

# 19. 수정된 성공 게이트

## Gate 0 — 데이터·분할 무결성

현재 `PASS`. 재실행하지 않는다.

## Gate 1L — LLM Reference 품질

PILOT의 형식·합의·안정성·근거·위험 기준을 모두 충족해야 한다.

- 통과: LDR-DEV 진행
- 조건부: 1회 수정 후 fresh re-pilot
- 실패: TEST LDR 금지, `REVISE`

## P-Gate 2 — Claim-first 표현 효과

E1 대 E0:

- CSER 상대 감소 ≥ 30%
- paired 95% CI의 중심이 감소 방향
- source span validity 악화 없음
- ALL_PANEL과 LEAVE_OVERLAP_OUT에서 방향 일치

통과 시 가능한 표현:

> LDR 기준으로 Claim-first 표현이 direct triple보다 의미 보존에 유리했다.

## P-Gate 3 — Ontology 품질

E4, TEST_NATURAL LDR 기준:

| 지표 | 잠정 기준 |
|---|---:|
| Term span F1 | ≥ 0.85 |
| Concept type Macro-F1 | ≥ 0.80 |
| Canonicalization F1 | ≥ 0.85 |
| Taxonomy edge F1 | ≥ 0.75 |
| Core non-tax relation F1 | ≥ 0.75 |
| RuleFrame slot F1 | ≥ 0.80 |
| Table/template F1 | ≥ 0.85 |

이 수치는 인간 Gold 정확도가 아니라 LDR agreement 기준이다.

## P-Gate 4 — 신뢰성과 안전성

| 지표 | 기준 |
|---|---:|
| Evidence precision | ≥ 0.95 |
| Unsupported edge rate | ≤ 0.03 |
| Example contamination | ≤ 0.02 |
| 중대 SHACL violation | ≤ 0.01 |
| Provenance path coverage | 1.00 |
| Process direction critical error | ≤ 0.02 |

## P-Gate 5 — 저비용 LLM 효과

- E4가 E5에 대해 비열등
- E4/E1 token ratio ≤ 0.35
- E4/E5 token ratio ≤ 0.50
- LLM-reviewed candidate ratio ≤ 0.20
- 동일 budget에서 E4가 E3보다 주요 지표 2개 이상 우세
- reference cost는 별도 보고

## P-Gate 6 — 질의 가능성과 runtime

- CQ-TEST answer-set F1 ≥ 0.80
- CQ-TEST evidence precision ≥ 0.90
- no-answer accuracy ≥ 0.85
- provenance query 성공률 1.00
- idempotent import 후 node/edge hash 동일
- duplicate stable ID 0

## P-Gate 7 — 재현성

- 비LLM 경로 결과 hash 동일
- 모든 LLM raw response 보존
- prompt/schema/model snapshot hash 보존
- cache replay 결과 동일
- TEST reference 생성 시점이 freeze 이후
- TEST 사전 접근 0
- API secret 미저장

---

# 20. 최종 판정 규칙

## `PROVISIONAL_PASS`

조건:

- Gate 0, Gate 1L, P-Gate 2~7 통과
- reference-sensitive 분석에서 시스템 순위가 안정적
- multi-family 또는 multi-snapshot 구성
- critical negative control 통과

허용 주장:

> 자이제 단일 도메인에서 LDR 기준으로 저비용·근거 기반 ontology 구축 방법의 잠정 타당성이 지지되었다.

## `ENGINEERING_PASS`

조건 예:

- pipeline·runtime·provenance 통과
- 시스템 간 상대 순위는 안정적
- 단일 snapshot fallback 또는 LDR 합의 일부가 목표 미달

허용 주장:

> 기술 파이프라인은 실행 가능하며 후속 인간 검증 후보 시스템을 선별했다.

## `REVISE`

다음 중 하나:

- Gate 1L 실패
- reference variant에 따라 시스템 순위 역전
- negative-control false acceptance 초과
- E4 비용 절감 미달
- ontology 품질 핵심 지표 미달

## `INVALID`

다음 중 하나:

- TEST LDR을 freeze 전에 생성·열람
- TEST 결과 후 prompt/threshold 변경
- 동일 모델이 reference와 candidate를 만들고 overlap 통제를 하지 않음
- API raw response 또는 manifest 소실
- split leakage 발견

---

# 21. 실행 단계와 산출물

## Phase A — 사전등록 수정

작업:

- 기존 preregistration 보존
- 인간 Gold 미사용 사유 기록
- LDR 지위와 주장 한계 기록
- 모델 정책과 gate 잠금

산출물:

```text
preregistration/amendment_llm_reference_v1.md
preregistration/model_policy_v1.yaml
preregistration/api_policy_v1.yaml
preregistration/gate1l_thresholds.yaml
```

## Phase B — PILOT 40 LLM 주석

작업:

- A/B 독립 주석
- 역할별 반복 실행
- A/B alignment
- blind adjudication
- verifier
- IMA/IMS 계산

산출물:

```text
annotation/llm_reference/pilot/annotator_A.jsonl
annotation/llm_reference/pilot/annotator_B.jsonl
annotation/llm_reference/pilot/replicates/
annotation/llm_reference/pilot/adjudication.jsonl
annotation/llm_reference/pilot/verifier.jsonl
reports/gate1l_pilot_report.md
reports/gate1l_metrics.json
```

## Phase C — LDR-DEV

작업:

- INDUCTION 100
- VALIDATION 80
- DEV table/canonicalization/micrograph/CQ
- LDR status와 confidence 부여

산출물:

```text
reference/llm/dev/ldr_induction_awc.jsonl
reference/llm/dev/ldr_validation_awc.jsonl
reference/llm/dev/ldr_terms_concepts.jsonl
reference/llm/dev/ldr_canonical_pairs.csv
reference/llm/dev/ldr_tables.jsonl
reference/llm/dev/ldr_micrographs.ttl
reference/llm/dev/cq_dev.json
reports/ldr_dev_quality_report.md
```

## Phase D — E0/E1/E2

작업:

- full-LLM 기준선
- no-generative path
- neutral semantic mapper
- cost/provenance ledger

## Phase E — Ontology induction

작업:

- concept extraction/typing
- canonicalization
- taxonomy
- non-tax relation
- procedure
- RuleFrame
- template schema
- SHACL/provenance

## Phase F — E3/E4/E5와 budget sweep

작업:

- VALIDATION에서 selector와 budget 선택
- ablation
- Pareto curve
- primary config 잠금

## Phase G — System freeze

작업:

- code/config/model/prompt/schema/threshold hash
- candidate TEST outputs 생성·잠금
- TEST reference가 아직 존재하지 않음을 확인

## Phase H — Locked TEST LDR와 평가

작업:

- 140 natural + 60 challenge LDR 생성
- locked table/pairs/micrograph/CQ 생성
- aggregate evaluation
- cluster bootstrap
- 비열등성
- sensitivity analysis

## Phase I — 전체 1,366건 ontology

작업:

- 최종 frozen 시스템 실행
- RDF/OWL/SHACL 및 Neo4j export
- full-corpus graph는 독립 test가 아니라 산출물로 표시

## Deferred Phase J — 인간 확인

현재 실험의 비차단 단계다. 향후 논문·대외 성과 주장 전에 수행한다.

권장 최소 감사:

- TEST_NATURAL 층화 80건
- TEST_CHALLENGE 40건
- high-risk Claim 전수 또는 층화 표본
- locked micrograph 6개
- CQ-TEST 20개

이 단계 이후에만 기존 설계의 최종 `PASS`와 “정확도” 표현을 사용할 수 있다.

---

# 22. 권장 디렉터리 구조

```text
zaije_experiment/
├── legacy/
│   └── 자이제_1.xlsx
├── reports/
│   ├── phase0_status_report.md
│   ├── input_resolution.md
│   ├── gate1l_pilot_report.md
│   ├── ldr_dev_quality_report.md
│   ├── locked_evaluation_report.md
│   └── final_provisional_report.md
├── preregistration/
│   ├── original_experiment_design.md
│   ├── amendment_llm_reference_v1.md
│   ├── model_policy_v1.yaml
│   ├── api_policy_v1.yaml
│   └── gate1l_thresholds.yaml
├── annotation/
│   ├── guideline.md
│   ├── human_deferred/
│   │   ├── annotator_A.jsonl
│   │   └── annotator_B.jsonl
│   └── llm_reference/
│       ├── schemas/
│       ├── prompts/
│       ├── pilot/
│       ├── dev/
│       ├── adjudication/
│       └── verifier/
├── reference/
│   └── llm/
│       ├── dev/
│       └── locked/
├── systems/
│   ├── E0/
│   ├── E1/
│   ├── E2/
│   ├── E3/
│   ├── E4/
│   └── E5/
├── freeze/
├── evaluation/
│   ├── metrics/
│   ├── bootstrap/
│   ├── sensitivity/
│   └── negative_controls/
├── graph/
│   ├── rdf/
│   ├── shacl/
│   └── neo4j/
├── logs/
│   ├── api/
│   ├── access/
│   └── pipeline/
└── cost/
    ├── reference/
    ├── system/
    └── evaluation/
```

---

# 23. 설정 파일 예시

## 23.1 `model_policy_v1.yaml`

```yaml
experiment_id: zaije_ldr_v1
mode: OPENAI_MULTI_SNAPSHOT  # MULTI_FAMILY | OPENAI_MULTI_SNAPSHOT | SINGLE_SNAPSHOT_MULTI_ROLE

reference:
  annotator_a:
    model: "<PINNED_MODEL_A>"
    role: domain_first
    temperature: 0
  annotator_b:
    model: "<PINNED_MODEL_B>"
    role: ontology_first
    temperature: 0
  adjudicator:
    model: "<PINNED_MODEL_C>"
    temperature: 0
    blind_candidate_order: true
  verifier:
    model: "<PINNED_MODEL_D>"
    temperature: 0

candidate:
  full_llm:
    model: "<PINNED_MODEL_E>"
  selective_arbiter:
    model: "<PINNED_MODEL_F>"

constraints:
  disallow_reference_candidate_same_snapshot: true
  allow_overlap_with_leave_out_analysis: true
  test_reference_after_system_freeze: true
```

## 23.2 `api_policy_v1.yaml`

```yaml
secret_source: environment
store_api_key: false
store_raw_responses: true
use_structured_outputs: true
use_batch_for_bulk: true
max_transport_retries: 2
retry_on_label_disagreement: false
cache_enabled: true

logging:
  request_id: true
  response_id: true
  model_snapshot: true
  prompt_hash: true
  schema_hash: true
  token_usage: true
  retry_history: true
  raw_response_path: true
```

## 23.3 `reference_status.json` 예시

```json
{
  "evidence_id": "E000001",
  "reference_status": "CONSENSUS_CORE",
  "annotator_agreement": 0.92,
  "intra_model_stability": 0.96,
  "verifier_status": "ENTAILED",
  "constraint_status": "PASS",
  "reference_confidence": 0.94,
  "model_overlap_flags": [],
  "provenance": {
    "annotator_a_response_id": "...",
    "annotator_b_response_id": "...",
    "adjudicator_response_id": null,
    "verifier_response_id": "..."
  }
}
```

---

# 24. Prompt 설계 원칙

## 24.1 공통 system instruction

- Evidence bundle 외 지식을 사용하지 않음
- 문서가 말하는 것과 모델이 알고 있는 것을 분리
- exact quote 없는 핵심 필드 생성 금지
- 문서에 없는 주체·산출물·조건을 보충하지 않음
- 불확실하면 `UNDERDETERMINED`
- 질문·예시·오해·반박을 일반 규칙으로 자동 승격하지 않음
- 원문에 여러 Claim이 있으면 atomic하게 분리
- 짧은 판정 사유만 출력하고 자유 서술을 최소화

## 24.2 Prompt 예시 사용

- 예시는 PILOT/INDUCTION에서만 선택
- TEST와 같은 leakage group의 예시 금지
- 한 label만 과대표집하지 않음
- positive와 hard negative를 함께 포함
- prompt example hash를 기록

## 24.3 Adjudicator prompt

- 두 candidate 순서를 무작위화
- “더 자세한 답”을 선호하지 않도록 길이를 판단 기준에서 제외
- evidence support를 최우선 기준으로 명시
- merge 시 field별 source quote 요구
- 결정 불가를 허용

## 24.4 Verifier prompt

Verifier에게 “맞는지 확인하라”보다 다음처럼 반증을 요구한다.

> 이 Claim이 틀리거나 과도하게 일반화되었다고 판단할 수 있는 근거를 먼저 찾고, Evidence가 모든 핵심 필드를 직접 지지할 때만 ENTAILED로 판정하라.

---

# 25. 예상 위험과 대응

## 위험 1. 여러 LLM이 같은 오류에 합의

대응:

- 모델 다양성
- verifier/falsifier
- negative controls
- leave-overlap-out
- 인간 Gold와 동일시 금지

## 위험 2. 동일 공급자 모델 간 상관 오류

대응:

- pinned multi-snapshot
- 역할·prompt 분리
- 반복 안정성
- `ENGINEERING_ONLY` downgrade 조건
- 향후 인간 감사 필수

## 위험 3. E1이 reference schema와 유사해 유리

대응:

- neutral semantic slot 평가
- E0 projection 외 독립 slot scoring
- candidate model과 reference model 분리
- LDR raw rationale 미노출

## 위험 4. 합의가 높은 쉬운 사례만 core로 남음

대응:

- core와 all-case 모두 보고
- underdetermined/challenge 별도 보고
- quarantine·adjudication rate 공개
- hard subset을 제거하지 않음

## 위험 5. adjudicator의 position·verbosity bias

대응:

- 익명화
- 순서 무작위화
- 10% swap audit
- evidence-based rubric
- free-form preference 대신 field-level decision

## 위험 6. API 모델 업데이트

대응:

- snapshot pinning
- model ID와 response ID 저장
- 변경 시 새 run
- cached response replay

## 위험 7. 비용이 과도해짐

대응:

- PILOT 동기, 본 주석 Batch
- A/B 합의 항목은 adjudicator 생략
- verifier는 고위험 전수, 저위험 층화 표본
- cache
- reference/system/evaluation 비용 분리

## 위험 8. TEST reference를 보고 시스템을 수정

대응:

- freeze 후 reference 생성
- 접근 로그
- aggregate 평가 먼저 생성
- 수정 시 새 experiment ID

---

# 26. 다음 단계 완료 조건

다음 단계인 E0~E5 본 실험으로 넘어가기 위한 최소 조건은 다음이다.

```text
[ ] amendment_llm_reference_v1.md 잠금
[ ] model_policy_v1.yaml 잠금
[ ] API secret 비저장 검사 통과
[ ] PILOT A/B 독립 호출 완료
[ ] PILOT 반복 안정성 호출 완료
[ ] blind adjudication 완료
[ ] grounding verifier 완료
[ ] IMA/IMS 산출
[ ] Gate 1L 최소 기준 충족
[ ] prompt/schema 변경 종료 및 hash 잠금
[ ] LDR-INDUCTION 100 생성
[ ] LDR-VALIDATION 80 생성
[ ] TEST LDR 미생성 상태 확인
[ ] reference/system/evaluation cost ledger 분리
```

이 목록이 충족되면 E0~E5와 ontology induction을 시작한다.

---

# 27. 최종 보고서 문장 템플릿

## Gate 1L 통과 시

> 두 개의 독립 LLM 주석자, 불일치 조정자, 근거 검증자를 이용해 자이제 문서의 잠정 기준셋을 구축하였다. 기준셋은 exact evidence span, modality, condition, discourse status, promotion 상태를 포함하며, 모델 간 합의·반복 안정성·반례 통제를 통과한 항목과 불확정 항목을 구분한다.

## E4가 우세할 때

> 잠긴 LDR 기준에서 위험·다양성·그래프 효용 기반 선택적 LLM 방식은 uncertainty-only 방식보다 동일 예산에서 더 높은 의미 보존 및 ontology 품질을 보였고, gray-zone 전수 LLM 방식에 대해 사전 정의한 비열등성 조건을 충족했다.

## 결과가 약할 때

> LDR 기준에서 Claim-first 또는 ontology induction의 일부 효과는 관찰되었으나, 모델 간 합의·비용 절감·관계 귀납 중 하나 이상의 게이트를 충족하지 못했으므로 방법론 가설은 수정이 필요하다.

## 반드시 붙일 한계 문장

> 본 결과의 기준셋은 인간 전문가 Gold가 아니라 다중 LLM 합의와 근거 검증으로 구성된 잠정 reference이므로, 절대 정확도와 전문가 수준 성능에 대한 결론은 후속 인간 검증이 필요하다.

---

# 28. 선행연구와 설계 근거

LLM이 일부 텍스트 분류 주석에서 crowd worker보다 높은 성능과 일치도를 보인 연구가 있어 LLM annotation의 실용 가능성은 존재한다. 그러나 그 결과가 복합 span·관계·규칙·ontology 주석으로 자동 일반화되는 것은 아니다. 후속 연구들은 모델·과업별 신뢰도 변동과 LLM judge의 position, verbosity, self-enhancement bias를 보고했다. 따라서 본 설계는 단일 LLM label을 Gold로 취급하지 않고, 독립 panel, blind adjudication, source-grounded verification, 반복 안정성, negative control을 결합한다.

또한 단일 대형 judge보다 서로 다른 모델의 panel이 bias와 비용 측면에서 유리할 수 있다는 연구를 반영한다. 다만 panel 합의 역시 인간 truth를 보장하지 않으므로 LDR이라는 제한된 지위를 유지한다. 범주형 label 합의의 보조 분석에는 annotator별 오류율을 추정하는 Dawid–Skene 계열 모델을 적용할 수 있지만, span·open relation에는 직접 적용하지 않고 majority/adjudication 결과와 비교하는 sensitivity analysis로만 사용한다.

OpenAI API 구현에서는 Structured Outputs로 schema adherence를 강제하고, bulk annotation에는 Batch API를 사용하며, 모델 snapshot을 pin하고 prompt/eval 변경을 추적한다.

---

# 참고문헌

1. Gilardi, F., Alizadeh, M., & Kubli, M. (2023). *ChatGPT outperforms crowd workers for text-annotation tasks*. Proceedings of the National Academy of Sciences, 120(30), e2305016120. https://doi.org/10.1073/pnas.2305016120
2. Zheng, L. et al. (2023). *Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena*. arXiv:2306.05685. https://arxiv.org/abs/2306.05685
3. Verga, P. et al. (2024). *Replacing Judges with Juries: Evaluating LLM Generations with a Panel of Diverse Models*. arXiv:2404.18796. https://arxiv.org/abs/2404.18796
4. Tan, S. et al. (2024). *JudgeBench: A Benchmark for Evaluating LLM-based Judges*. arXiv:2410.12784. https://arxiv.org/abs/2410.12784
5. Shi, L. et al. (2024). *Judging the Judges: A Systematic Study of Position Bias in LLM-as-a-Judge*. arXiv:2406.07791. https://arxiv.org/abs/2406.07791
6. Tan, Z. et al. (2024). *Large Language Models for Data Annotation and Synthesis: A Survey*. EMNLP 2024. https://aclanthology.org/2024.emnlp-main.54/
7. Dawid, A. P., & Skene, A. M. (1979). *Maximum Likelihood Estimation of Observer Error-Rates Using the EM Algorithm*. Journal of the Royal Statistical Society: Series C, 28(1), 20–28. https://doi.org/10.2307/2346806
8. OpenAI. *Structured model outputs*. https://developers.openai.com/api/docs/guides/structured-outputs
9. OpenAI. *Batch API*. https://developers.openai.com/api/docs/guides/batch
10. OpenAI. *Text generation: model snapshot pinning and eval guidance*. https://developers.openai.com/api/docs/guides/text

---

# 최종 원칙

> **LLM 합의를 정답으로 가장하지 않는다.**  
> **근거와 제약으로 검증된 LDR를 잠그고, 시스템과 reference의 모델·시간·정보 경계를 분리한 뒤 상대 실험을 수행한다.**  
> **현재 단계의 목적은 최종 정확도 선언이 아니라, 인간 검증에 올릴 가장 유망한 ontology 구축 방법을 비용·품질·재현성 기준으로 선별하는 것이다.**
