# SCALE-AWC 자이제 실험 재실행 현황

## 판정

- Phase 0: **PASS**
- Phase 1: **BLOCKED — 인간 독립 이중 주석 필요**
- Phase 2∼7: **NOT RUN**

새 설계서는 LLM-Silver를 최종 정답으로 금지한다. 따라서 인간 Gold 없이 E0∼E5 성능을 다시 계산하는 것은 설계서 위반이며, 이번 실행은 Gold 직전 단계에서 정상 중단했다.

## 완료한 작업

- 설계서 binary hash와 일치하는 원본 확정
- 1,366 evidence의 stable ID와 canonical corpus 생성
- 168 leakage group 생성
- 그룹 간 겹침 0인 50/20/20/10 split 잠금
- AWC Gold 420건의 표본 ID 잠금
- PILOT 40건의 blind A/B 주석 템플릿 생성
- 표 조각 56건의 전수 Gold 범위 잠금
- API 호출 0건, TEST Gold 열람 0건

## Split

| Split | Evidence | 비율 |
|---|---:|---:|
| INDUCTION | 681 | 0.4985 |
| VALIDATION | 272 | 0.1991 |
| TEST_NATURAL | 275 | 0.2013 |
| TEST_CHALLENGE_POOL | 138 | 0.1010 |


## 재개 조건

1. `annotation/pilot/annotator_A.jsonl`과 `annotator_B.jsonl`을 서로 독립적으로 완료한다.
2. 수주·제안 도메인 전문가와 온톨로지·정보추출 연구자가 최소 1명씩 포함되어야 한다.
3. IAA 기준을 계산하고 불일치를 adjudication한다.
4. 기준을 통과하면 guideline·schema·label set을 잠그고 Phase 2 Gold 주석으로 넘어간다.

상세한 입력 버전 차이와 canonical hash amendment는 `reports/input_resolution.md`를 본다.
