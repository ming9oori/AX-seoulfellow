# LLM Reference Amendment v1

- Experiment: `zaije_ldr_v1`
- Locked date: 2026-07-11
- Parent experiment: `zaije-scale-awc-v1`
- Parent Gate 0: `PASS`
- Status: `LOCKED_BEFORE_LLM_CALL`

## Purpose

인간 Gold 구축을 후속 confirmatory validation으로 연기하고, 잠긴 다중 LLM 기준셋 `LLM-Derived Reference(LDR)`로 단일 도메인 가설을 잠정 검증한다.

LDR은 human gold, ground truth, 실제 정확도로 표현하지 않는다. 최종 판정은 `PROVISIONAL_PASS`, `ENGINEERING_PASS`, `REVISE`, `INVALID`로 제한한다.

## Preserved Locks

- Evidence 1,366
- Leakage groups 168
- `INDUCTION=681`, `VALIDATION=272`, `TEST_NATURAL=275`, `TEST_CHALLENGE_POOL=138`
- Gold/LDR membership 420
- PILOT membership 40
- Table/template membership 56
- TEST LDR creation before system freeze: forbidden

## Phase 1L

PILOT 40건에 대해 Domain-first A와 Ontology-first B를 서로 독립적으로 각 2회 실행한다. A/B 불일치만 blind adjudication하고, 최종 Claim을 grounding verifier와 결정론적 검증기로 검사한다.

Gate 1L 미달 시 PILOT 결과만 사용해 prompt/guideline을 최대 1회 수정할 수 있다. 이후 기존 PILOT과 겹치지 않는 INDUCTION 20건으로 fresh re-pilot한다.

## Cost Separation

Reference 생성 비용은 E0∼E5 system 비용에 포함하지 않는다. API 원장은 `reference`, `system`, `evaluation`으로 분리한다.
