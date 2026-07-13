# Graph Query Demo

이 파일은 설계서 16.4의 5개 demo 질의와 CQ 평가 경로를 요약한다.

## Demo 1. 수주영업의 입력과 산출물은 무엇인가?

- `수주영업 / Capture Planning` -`USES_INPUT`-> `고객 정보`
- `수주영업 / Capture Planning` -`USES_INPUT`-> `경쟁사 정보`
- `수주영업 / Capture Planning` -`PRODUCES`-> `Capture Plan`
- `수주영업 / Capture Planning` -`PRODUCES`-> `제안서 초안·완성본`
- `수주영업 / Capture Planning` -`DISCOVERS`-> `고객 정보`
- `수주영업 / Capture Planning` -`TARGETS_STAKEHOLDER`-> `고객`
- `수주영업 / Capture Planning` -`HAS_PRINCIPLE`-> `고객 중심 원칙`
- `수주영업 / Capture Planning` -`DISCOVERS`-> `경쟁사 정보`
- `수주영업 / Capture Planning` -`USES_INPUT`-> `자사 솔루션`
- `수주영업 / Capture Planning` -`DISCOVERS`-> `기회 정보`
- `수주영업 / Capture Planning` -`DISCOVERS`-> `고객 이슈`
- `수주영업 / Capture Planning` -`HAS_SUBTASK`-> `경쟁사 분석 및 차별화 요소 규명`

## Demo 2. Capture Plan은 어디서 생성되고 어디에 쓰이는가?


## Demo 3. 제안전략 개발 전 필요한 정보는 무엇인가?

- `제안전략 개발` -`TARGETS_STAKEHOLDER`-> `고객`
- `제안전략 개발` -`USES_INPUT`-> `고객 니즈`
- `제안전략 개발` -`HAS_PRINCIPLE`-> `고객 중심 원칙`
- `제안전략 개발` -`USES_INPUT`-> `경쟁사 정보`
- `제안전략 개발` -`PRODUCES`-> `핵심 차별화 요소`
- `제안전략 개발` -`USES_INPUT`-> `고객 이슈`
- `제안전략 개발` -`HAS_PRINCIPLE`-> `차별화 원칙`
- `제안전략 개발` -`USES_INPUT`-> `고객 정보`
- `제안전략 개발` -`TARGETS_STAKEHOLDER`-> `사용자`

## Demo 4. 평가자 유형별로 어떤 분석이 필요한가?

- `평가자 분석` -`TARGETS_STAKEHOLDER`-> `영향자`
- `평가자 분석` -`TARGETS_STAKEHOLDER`-> `의사결정자`
- `평가자 분석` -`ANALYZES`-> `고객 평가 기준`
- `평가자 분석` -`TARGETS_STAKEHOLDER`-> `고객`
- `평가자 분석` -`DISCOVERS`-> `고객 니즈 구조`

## Demo 5. 리스크 관리는 어떤 차별화 포인트로 연결되는가?

- `리스크 관리` -`ANALYZES`-> `사업 리스크`

## Competency Questions

| CQ | passed | expected |
| --- | --- | --- |
| CQ1 | FAIL | 제안전략 개발 ← USES_INPUT ← Capture Plan/고객 이슈/경쟁사 정보/핵심 차별화 요소 |
| CQ2 | FAIL | 수주영업 → PRODUCES → Capture Plan → USED_AS_INPUT_FOR → 제안서 기획 |
| CQ3 | FAIL | 수주영업/제안참여 의사결정 → HAS_DECISION_POINT → Bid/No-Bid |
| CQ4 | FAIL | 평가자 분석 → ANALYZES → 평가자 유형 → USED_AS_INPUT_FOR → 설득 메시지 |
| CQ5 | FAIL | 리스크 관리 → MITIGATES → 리스크; 리스크 관리 → MAY_RESULT_IN → 차별화 포인트 |
| CQ6 | FAIL | 제안서 작성 → HAS_REVIEW → 전략 리뷰/초안 리뷰/최종 리뷰 |
| CQ7 | FAIL | RFP → CONTAINS → 공식 요구조건; 비공식 요구조건 → PART_OF → 고객 니즈 |
