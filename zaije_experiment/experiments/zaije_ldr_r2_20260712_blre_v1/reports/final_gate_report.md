# LDR-R2 BLRE 실험 현황 보고서

## 1. 최종 판정

**`REVISE_BEFORE_R2_PILOT`**

실험은 Phase D 모델·configuration bake-off까지 진행했다. fresh `R2_PILOT 60`은 실행하지 않았다.

중단 이유는 사전 기준을 모두 만족한 configuration이 1개뿐이어서, 필수 panel 3개를 잠그지 못했기 때문이다.

---

## 2. 시작 전 고정한 항목

- Experiment ID: `zaije_ldr_r2_20260712_blre_v1`
- 입력: `legacy/자이제_1.xlsx`
- Evidence: 1,366
- Gate 0 split: 기존 PASS 결과 유지
- DEV_EXPOSED: 기존 PILOT 40 + re-pilot 20 = 60
- Model bake-off: DEV_EXPOSED 내 24
- Fresh R2_PILOT: INDUCTION 60, membership/hash 잠금
- Fresh R2_PILOT API exposure: 0
- TEST reference 생성·열람: 0

---

## 3. 표본 설계 충돌과 API 전 amendment

원 설계의 `기존 420 membership group 전부 제외` 조건을 적용하면 INDUCTION에 46건만 남아 fresh 60건을 뽑을 수 없었다. 또한 table과 normative 잔여가 각각 0건이었다.

R2 API 호출 전에 다음을 amendment로 잠권다.

- 라벨이 생성된 적 없는 기존 `INDUCTION_GOLD 100` membership 퇴역
- 이미 공개된 60건의 evidence·leakage group 전부 제외
- VALIDATION·TEST membership 유지
- 잔여 table 1건, normative 5건 전수 사용
- 부족 quota를 conditional·definition strata로 재배분

수정된 fresh 60건은 기존 공개 60건과 evidence·leakage group 중복이 0이다.

---

## 4. 구현한 BLRE 구성

### 4.1 Deterministic Candidate Lattice

- 원문 character offset 보존
- prose 문장·절·인접 절 병합 후보
- list header·item·header+item 후보
- table row 후보
- question·caption 후보
- candidate ID·generation rule·member segment 기록

### 4.2 Boundary selection

LLM은 quote를 작성하지 않고 candidate ID만 `KEEP/DROP/UNDERDETERMINED/MISSING_CANDIDATE`로 판정했다.

### 4.3 Field decomposition

하나의 Claim JSON을 한 번에 생성하지 않고 다음으로 분리했다.

- F1: semantic mode
- F2: deontic force + polarity
- F3: conditionality + epistemic status
- F4: promotion

### 4.4 Configuration policy

| ID | Snapshot |
|---|---|
| C01 | `gpt-4o-mini-2024-07-18` |
| C02 | `gpt-4.1-mini-2025-04-14` |
| C03 | `gpt-4o-2024-08-06` |
| C04 | `gpt-4.1-2025-04-14` |
| C05 | `gpt-4.1-nano-2025-04-14` |

각 configuration을 같은 24건에 2회 실행했다. Primary repeat은 동일 candidate 순서를 사용했고, 역순 order audit은 별도로 실행했다.

---

## 5. DEV 실행 중 발견한 구현 문제

### 5.1 Batch cardinality

첫 field prompt가 단수형으로 적혀 있어 C02∼C04가 batch item을 누락했다. Structured Outputs는 반환된 item의 형식을 보장하지만 배열 길이는 보장하지 않는다.

fresh data를 보기 전 DEV prompt에 `입력 item별 정확히 1개 반환`을 명시했다.

### 5.2 Repeat·order audit 혼입

첫 구현은 repeat 2에 candidate 순서를 뒤집어 model IMS와 order bias를 섞었다. 교정 구현에서는:

- primary repeat: 동일 순서
- order audit: 별도 역순 호출

로 분리했다.

### 5.3 Field task 미분리

첫 구현은 6개 field를 한 응답에서 판정했다. 교정 구현은 설계서대로 F1∼F4를 별도 Structured Output task로 실행했다.

위 교정은 모두 DEV_EXPOSED 24건 내에서만 이루어졌고 fresh 60건은 열람하지 않았다.

---

## 6. 교정된 bake-off 결과

| Config | Boundary repeat F1 | ID validity | Order consistency | Critical-field IMS | Eligible |
|---|---:|---:|---:|---:|---|
| C01 | 0.9306 | 0.9583 | 0.7083 | 0.1667 | FAIL |
| **C02** | **0.9222** | **1.0000** | 0.5000 | **0.8750** | **PASS** |
| C03 | 1.0000 | 1.0000 | 0.5000 | 0.6250 | FAIL |
| C04 | 0.9722 | 1.0000 | 0.5000 | 0.7083 | FAIL |
| C05 | 0.8488 | 0.7917 | 0.4583 | 0.5000 | FAIL |

configuration 자격 기준은 boundary repeat F1 0.85, candidate ID validity 1.00, critical-field IMS 0.85, deterministic control 0.95, API failure 0.01 이하였다.

`C02`만 자격을 통과했다. panel 크기 3을 충족하지 못했으므로 `model_panel_lock.json` 상태는 `REVISE`다.

Order consistency는 모든 configuration에서 낮았다. C02가 bake-off 자격은 통과했지만 fresh Gate R1의 order consistency 0.95 기준을 충족했다는 뜻은 아니다.

---

## 7. 실행하지 않은 단계

panel 3개를 잠그지 못했기 때문에 다음은 실행하지 않았다.

- fresh R2_PILOT 60 boundary 3×2 voting
- deterministic boundary envelope
- fresh field F1∼F4 voting
- mention lattice·argument ID selection
- reference envelope HARD/SOFT/UNSTABLE 집계
- high-risk pointwise verifier
- Gate R0∼R4 최종 판정
- LDR-INDUCTION·VALIDATION
- E0∼E5
- TEST reference

---

## 8. API 사용량

| Run | Calls | Input | Output | Estimated cost |
|---|---:|---:|---:|---:|
| 초기 bake-off + field cardinality DEV 재실행 | 72 | 135,688 | 55,849 | $0.448074 |
| 교정된 decomposed bake-off | 115 | 231,880 | 86,588 | $0.589519 |
| **합계** | **187** | **367,568** | **142,437** | **$1.037593** |

- API failed attempt: 0
- fresh R2_PILOT call: 0
- TEST call: 0
- API key 저장: 0

비용은 raw response usage와 사전 단가로 재계산한 추정치다.

---

## 9. 해석

### 확인한 것

1. 자유 quote 생성을 제거한 exact-offset candidate lattice는 기술적으로 작동했다.
2. 경계·field를 분리하면 C02처럼 반복 안정성이 높은 configuration을 식별할 수 있다.
3. promotion, polarity, semantic mode는 경계를 잠그어도 모델·configuration에 따라 반복 불안정성이 남았다.
4. candidate 순서 편향은 비교형 adjudicator를 제거한 후에도 boundary selection에 남아 있었다.

### 아직 검증하지 못한 것

- BLRE reference envelope가 HARD+SOFT coverage 0.85를 달성하는지
- argument mention ID 선택이 안정적인지
- high-risk verifier가 0.90 기준을 통과하는지
- BLRE 기준 E0∼E5 상대 성능
- 온톨로지·Neo4j 품질

---

## 10. 다음 조치

현 experiment ID에서 fresh pilot을 강행하면 사전등록을 위반한다. 새 experiment ID에서 다음 중 하나가 필요하다.

1. candidate order를 아예 모델에 노출하지 않는 candidate-by-candidate pointwise 호출
2. promotion·polarity를 cue 후보 구조와 함께 별도 이진 판정으로 분해
3. OpenAI 공급자 내 configuration 3개 조건을 완화하지 않으려면 다른 model family/provider 추가
4. panel 3개 요구를 단일 안정 configuration + bootstrap/replicate envelope로 바꾸려면 새 연구 가설로 사전등록

현 run의 fresh 60 membership은 출력에 노출되지 않았으므로, 새 실험에서 정책을 명시하면 재사용 가능하다.

---

## 11. 결론

> **LDR-R2는 exact-offset candidate lattice와 field decomposition을 구현하고 DEV bake-off까지 실행했다. 그러나 사전 기준을 만족한 configuration이 C02 하나뿐이어서 3-model panel을 구성하지 못했다. 따라서 fresh R2_PILOT을 실행하지 않고 `REVISE_BEFORE_R2_PILOT`로 종료한다.**
