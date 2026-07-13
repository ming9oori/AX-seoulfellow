# R2 Sampling Amendment Before API Calls

- Locked: 2026-07-12
- R2 API calls before amendment: 0
- R2_PILOT membership before amendment: not created
- TEST reference access: 0

## Infeasibility

원 설계의 다음 세 조건을 동시에 적용하면 fresh INDUCTION evidence가 46건만 남는다.

1. 기존 공개 PILOT/re-pilot 60건과 leakage group 중복 0
2. 기존 reference membership 420건과 leakage group 중복 0
3. fresh R2_PILOT 60건

잔여 46건의 `TABLE_TEMPLATE=0`, `NORMATIVE_DEONTIC=0`이므로 사전등록 quota도 실현할 수 없다. 이는 모델 결과가 아닌 기존 membership과 leakage group 구조로 인한 수학적 제약이다.

## Amendment

- 라벨·LLM 출력이 생성된 적 없는 기존 `INDUCTION_GOLD 100` membership은 R2에서 퇴역한다.
- 이미 공개된 PILOT/re-pilot 60건의 evidence ID와 leakage group은 계속 전부 제외한다.
- VALIDATION·TEST membership은 그대로 잠그고 열람하지 않는다. R2_PILOT은 INDUCTION split에서만 추출하므로 split group overlap은 0이다.
- 공개 60건의 group을 제외하면 table 1건, normative 5건만 남으므로 해당 strata는 잔여 전수를 사용한다.

## Amended Fresh Quotas

| Stratum | Count |
|---|---:|
| TABLE_TEMPLATE | 1 |
| LIST_MULTILINE | 8 |
| QUESTION_CAPTION_DISCOURSE | 4 |
| NORMATIVE_DEONTIC | 5 |
| CONDITIONAL_EXCEPTION | 10 |
| DEFINITION_CAUSAL_EVALUATIVE | 14 |
| NEGATION_QUANTITY_HIGH_RISK | 4 |
| SIMPLE_GENERAL_PROSE | 14 |
| **Total** | **60** |

이 amendment는 candidate lattice, model bake-off, R2_PILOT LLM 결과를 보기 전에 잠그며, fresh pilot 결과 후 추가 수정은 허용하지 않는다.
