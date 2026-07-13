# CAPE-KG Mapping Review Group Briefing

Generated: 2026-06-29T18:55:24.456688+00:00

This briefing expands the next Top-20 source-task/standard groups into their Top-5 mapping candidates.
It is a reviewer navigation aid only. Candidate rows remain non-claimable until expert decisions are returned and imported.

## Summary

- groups: 20
- candidate rows: 100
- claim_status: `candidate_only_pending_expert_review`

## Review Rule

- Finish all Top-5 rows in a source-task/standard group before using that group for Hit@K, P@5, MRR, or accept-rate.
- Treat close-score groups as ambiguity checks; do not accept the top-ranked row only because it ranks first.
- Use `accepted/rejected/unsure`, `relevance_grade`, `explanation_quality_score`, and a short comment in `mapping_review_items.reviewed.jsonl`.

## 1. PCF / PT 전략 개발

- group_key: `PCF::L2_TASK_PT_STRATEGY`
- group_priority: 0.9564
- score_gap: 0.0109
- review_focus: high-score verification; complete Top-5 before metric use

| rank | score | target | score signals | review question |
|---:|---:|---|---|---|
| 1 | 0.2886 | `pcf:E:10952` 철수 전략 수립 | name=0.5; def=0.1526; verb=0.0; hier=0.5 | `PT 전략 개발` 업무가 PCF process context `철수 전략 수립`에 자연스럽게 위치하는가? |
| 2 | 0.2779 | `pcf:E:20092` 리콜 전략 수립 | name=0.5; def=0.1287; verb=0.0; hier=0.5 | `PT 전략 개발` 업무가 PCF process context `리콜 전략 수립`에 자연스럽게 위치하는가? |
| 3 | 0.2955 | `pcf:E:20873` 서비스 지원 전략 정의·개발 | name=0.5217; def=0.1261; verb=0.2; hier=0.3333 | `PT 전략 개발` 업무가 PCF process context `서비스 지원 전략 정의·개발`에 자연스럽게 위치하는가? |
| 4 | 0.311 | `pcf:E:20889` IT 서비스 전달 전략 개발 | name=0.6087; def=0.1178; verb=0.2; hier=0.3333 | `PT 전략 개발` 업무가 PCF process context `IT 서비스 전달 전략 개발`에 자연스럽게 위치하는가? |
| 5 | 0.3001 | `pcf:E:19220` 건설 전략 수립 | name=0.5; def=0.117; verb=0.2; hier=0.5 | `PT 전략 개발` 업무가 PCF process context `건설 전략 수립`에 자연스럽게 위치하는가? |

## 2. PCF / 경쟁사 분석

- group_key: `PCF::L2_TASK_COMPETITOR_ANALYSIS`
- group_priority: 0.9364
- score_gap: 0.0159
- review_focus: high-score verification; complete Top-5 before metric use

| rank | score | target | score signals | review question |
|---:|---:|---|---|---|
| 1 | 0.3706 | `pcf:E:10111` 경쟁사 및 경쟁·대체 제품·서비스 분석 | name=0.4444; def=0.2823; verb=0.3333; hier=0.4 | `경쟁사 분석` 업무가 PCF process context `경쟁사 및 경쟁·대체 제품·서비스 분석`에 자연스럽게 위치하는가? |
| 2 | 0.3732 | `pcf:E:10021` 경쟁 환경 분석·평가 | name=0.5882; def=0.2804; verb=0.25; hier=0.2 | `경쟁사 분석` 업무가 PCF process context `경쟁 환경 분석·평가`에 자연스럽게 위치하는가? |
| 3 | 0.4117 | `pcf:E:19945` 경쟁사 식별 | name=0.6667; def=0.2778; verb=0.25; hier=0.4 | `경쟁사 분석` 업무가 PCF process context `경쟁사 식별`에 자연스럽게 위치하는가? |
| 4 | 0.3958 | `pcf:E:11783` 경쟁 분석 수행 | name=0.7143; def=0.2732; verb=0.25; hier=0.1429 | `경쟁사 분석` 업무가 PCF process context `경쟁 분석 수행`에 자연스럽게 위치하는가? |
| 5 | 0.2909 | `pcf:E:13169` 가격 분석 수행 | name=0.4286; def=0.1936; verb=0.25; hier=0.1667 | `경쟁사 분석` 업무가 PCF process context `가격 분석 수행`에 자연스럽게 위치하는가? |

## 3. NCS / 목차 개발

- group_key: `NCS::L2_TASK_OUTLINE_DEVELOPMENT`
- group_priority: 0.9308
- score_gap: 0.0008
- review_focus: close-score disambiguation; complete Top-5 before metric use

| rank | score | target | score signals | review question |
|---:|---:|---|---|---|
| 1 | 0.0729 | `ncs:CU:1508010104_23v4` 기본도면 작성 | name=0.1667; def=0.125; verb=0.2; hier=0.0 | `목차 개발` 수행에 필요한 직무 능력단위로 `기본도면 작성`가 방어 가능한가? |
| 2 | 0.2208 | `ncs:CU:2305060106_15v1` 제안서 작성 | name=0.1818; def=0.1247; verb=0.2727; hier=0.3333 | `목차 개발` 수행에 필요한 직무 능력단위로 `제안서 작성`가 방어 가능한가? |
| 3 | 0.0638 | `ncs:CU:1508040104_14v2` 선체 검사 준비 | name=0.1538; def=0.0952; verb=0.25; hier=0.0 | `목차 개발` 수행에 필요한 직무 능력단위로 `선체 검사 준비`가 방어 가능한가? |
| 4 | 0.22 | `ncs:CU:0302010109_14v1` 보험 상품 개발 제안서 작성 | name=0.3; def=0.0926; verb=0.1667; hier=0.3333 | `목차 개발` 수행에 필요한 직무 능력단위로 `보험 상품 개발 제안서 작성`가 방어 가능한가? |
| 5 | 0.172 | `ncs:CU:2001050106_25v5` 기술영업 제안 작업 | name=0.1333; def=0.0915; verb=0.1; hier=0.375 | `목차 개발` 수행에 필요한 직무 능력단위로 `기술영업 제안 작업`가 방어 가능한가? |

## 4. PCF / 제안서 작성

- group_key: `PCF::L2_TASK_PROPOSAL_WRITING`
- group_priority: 0.926467
- score_gap: 0.0103
- review_focus: complete Top-5 before metric use

| rank | score | target | score signals | review question |
|---:|---:|---|---|---|
| 1 | 0.2509 | `pcf:E:11790` 고객에 입찰·제안·견적 제출/제시 | name=0.25; def=0.1575; verb=0.0; hier=0.75 | `제안서 작성` 업무가 PCF process context `고객에 입찰·제안·견적 제출/제시`에 자연스럽게 위치하는가? |
| 2 | 0.2018 | `pcf:E:20663` 제안 IT 투자 프로젝트 평가 | name=0.2727; def=0.1469; verb=0.0; hier=0.25 | `제안서 작성` 업무가 PCF process context `제안 IT 투자 프로젝트 평가`에 자연스럽게 위치하는가? |
| 3 | 0.2319 | `pcf:E:18116` 기회 수주 계획 수립 | name=0.1176; def=0.1444; verb=0.5; hier=0.2 | `제안서 작성` 업무가 PCF process context `기회 수주 계획 수립`에 자연스럽게 위치하는가? |
| 4 | 0.2612 | `pcf:E:11779` 영업 제안서·견적서 개발·관리 | name=0.3636; def=0.1419; verb=0.1429; hier=0.4 | `제안서 작성` 업무가 PCF process context `영업 제안서·견적서 개발·관리`에 자연스럽게 위치하는가? |
| 5 | 0.2436 | `pcf:E:20018` 입찰·제안·견적 수정 | name=0.3529; def=0.1397; verb=0.0; hier=0.5 | `제안서 작성` 업무가 PCF process context `입찰·제안·견적 수정`에 자연스럽게 위치하는가? |

## 5. NCS / 제안전략 개발

- group_key: `NCS::L2_TASK_PROPOSAL_STRATEGY_DEVELOPMENT`
- group_priority: 0.91685
- score_gap: 0.0026
- review_focus: close-score disambiguation; complete Top-5 before metric use

| rank | score | target | score signals | review question |
|---:|---:|---|---|---|
| 1 | 0.2101 | `ncs:CU:0201020115_24v5` PR 전략 수립 | name=0.4; def=0.1002; verb=0.0; hier=0.2 | `제안전략 개발` 수행에 필요한 직무 능력단위로 `PR 전략 수립`가 방어 가능한가? |
| 2 | 0.2048 | `ncs:CU:1001010105_20v2` 영업 제안 | name=0.3333; def=0.0921; verb=0.0; hier=0.5 | `제안전략 개발` 수행에 필요한 직무 능력단위로 `영업 제안`가 방어 가능한가? |
| 3 | 0.1284 | `ncs:CU:1802030105_14v2` 의류유통 커뮤니케이션관리 | name=0.1; def=0.0853; verb=0.0; hier=0.2 | `제안전략 개발` 수행에 필요한 직무 능력단위로 `의류유통 커뮤니케이션관리`가 방어 가능한가? |
| 4 | 0.1204 | `ncs:CU:1903060114_23v2` 반도체 펌웨어 개발 | name=0.3529; def=0.0825; verb=0.3333; hier=0.0 | `제안전략 개발` 수행에 필요한 직무 능력단위로 `반도체 펌웨어 개발`가 방어 가능한가? |
| 5 | 0.2127 | `ncs:CU:2001050106_25v5` 기술영업 제안 작업 | name=0.3529; def=0.0813; verb=0.0; hier=0.4286 | `제안전략 개발` 수행에 필요한 직무 능력단위로 `기술영업 제안 작업`가 방어 가능한가? |

## 6. NCS / 레드팀 리뷰

- group_key: `NCS::L2_TASK_RED_TEAM_REVIEW`
- group_priority: 0.910483
- score_gap: 0.0014
- review_focus: close-score disambiguation; complete Top-5 before metric use

| rank | score | target | score signals | review question |
|---:|---:|---|---|---|
| 1 | 0.1979 | `ncs:CU:2305060106_15v1` 제안서 작성 | name=0.1667; def=0.0884; verb=0.1429; hier=0.5 | `레드팀 리뷰` 수행에 필요한 직무 능력단위로 `제안서 작성`가 방어 가능한가? |
| 2 | 0.0097 | `ncs:CU:1508060110_14v2` 비상·소화 장치 시운전 | name=0.1111; def=0.0821; verb=0.0; hier=0.0 | `레드팀 리뷰` 수행에 필요한 직무 능력단위로 `비상·소화 장치 시운전`가 방어 가능한가? |
| 3 | 0.0193 | `ncs:CU:1508060104_15v3` 보일러 시운전 | name=0.1538; def=0.0795; verb=0.0; hier=0.0 | `레드팀 리뷰` 수행에 필요한 직무 능력단위로 `보일러 시운전`가 방어 가능한가? |
| 4 | 0.1993 | `ncs:CU:0302010109_14v1` 보험 상품 개발 제안서 작성 | name=0.0952; def=0.0677; verb=0.3333; hier=0.5 | `레드팀 리뷰` 수행에 필요한 직무 능력단위로 `보험 상품 개발 제안서 작성`가 방어 가능한가? |
| 5 | 0.0045 | `ncs:CU:1508060102_15v3` 주기관 해상 시운전 | name=0.125; def=0.0627; verb=0.0; hier=0.0 | `레드팀 리뷰` 수행에 필요한 직무 능력단위로 `주기관 해상 시운전`가 방어 가능한가? |

## 7. PCF / 제안계획 수립

- group_key: `PCF::L2_TASK_PMP_DEVELOPMENT`
- group_priority: 0.91025
- score_gap: 0.0105
- review_focus: complete Top-5 before metric use

| rank | score | target | score signals | review question |
|---:|---:|---|---|---|
| 1 | 0.048 | `pcf:E:10516` 전직 지원(Outplacement) 개발·시행 | name=0.0625; def=0.139; verb=0.1818; hier=0.0 | `제안계획 수립` 업무가 PCF process context `전직 지원(Outplacement) 개발·시행`에 자연스럽게 위치하는가? |
| 2 | 0.2427 | `pcf:E:11779` 영업 제안서·견적서 개발·관리 | name=0.2609; def=0.137; verb=0.25; hier=0.3333 | `제안계획 수립` 업무가 PCF process context `영업 제안서·견적서 개발·관리`에 자연스럽게 위치하는가? |
| 3 | 0.2322 | `pcf:E:10191` 사전 영업 활동 수행 | name=0.2222; def=0.1369; verb=0.3; hier=0.375 | `제안계획 수립` 업무가 PCF process context `사전 영업 활동 수행`에 자연스럽게 위치하는가? |
| 4 | 0.058 | `pcf:E:16448` 리스크 경감·관리 전략 수립 및 기존 성과관리 프로세스와 통합 | name=0.1463; def=0.1087; verb=0.2; hier=0.0 | `제안계획 수립` 업무가 PCF process context `리스크 경감·관리 전략 수립 및 기존 성과관리 프로세스와 통합`에 자연스럽게 위치하는가? |
| 5 | 0.1276 | `pcf:E:16824` 신제품·서비스 개발 및 출시 계획 수립 | name=0.4286; def=0.1066; verb=0.2; hier=0.0 | `제안계획 수립` 업무가 PCF process context `신제품·서비스 개발 및 출시 계획 수립`에 자연스럽게 위치하는가? |

## 8. PCF / 킥오프 미팅

- group_key: `PCF::L2_TASK_KICKOFF_MEETING`
- group_priority: 0.90485
- score_gap: 0.0026
- review_focus: close-score disambiguation; complete Top-5 before metric use

| rank | score | target | score signals | review question |
|---:|---:|---|---|---|
| 1 | 0.1983 | `pcf:E:10464` 오퍼 협상 | name=0.3636; def=0.0999; verb=0.0; hier=0.2 | `킥오프 미팅` 업무가 PCF process context `오퍼 협상`에 자연스럽게 위치하는가? |
| 2 | 0.1693 | `pcf:E:10191` 사전 영업 활동 수행 | name=0.1176; def=0.0997; verb=0.25; hier=0.25 | `킥오프 미팅` 업무가 PCF process context `사전 영업 활동 수행`에 자연스럽게 위치하는가? |
| 3 | 0.0585 | `pcf:E:20012` 고객 미팅·워크숍 관리 | name=0.3333; def=0.0947; verb=0.0; hier=0.0 | `킥오프 미팅` 업무가 PCF process context `고객 미팅·워크숍 관리`에 자연스럽게 위치하는가? |
| 4 | 0.1957 | `pcf:E:11779` 영업 제안서·견적서 개발·관리 | name=0.0909; def=0.0924; verb=0.3333; hier=0.3636 | `킥오프 미팅` 업무가 PCF process context `영업 제안서·견적서 개발·관리`에 자연스럽게 위치하는가? |
| 5 | 0.1753 | `pcf:E:11168` 오퍼링·고객 가치 제안 정의 | name=0.1905; def=0.0911; verb=0.1667; hier=0.1667 | `킥오프 미팅` 업무가 PCF process context `오퍼링·고객 가치 제안 정의`에 자연스럽게 위치하는가? |

## 9. PCF / 제안서 리뷰

- group_key: `PCF::L2_TASK_PROPOSAL_REVIEW`
- group_priority: 0.8667
- score_gap: 0.0287
- review_focus: complete Top-5 before metric use

| rank | score | target | score signals | review question |
|---:|---:|---|---|---|
| 1 | 0.2491 | `pcf:E:20018` 입찰·제안·견적 수정 | name=0.3529; def=0.1519; verb=0.0; hier=0.5 | `제안서 리뷰` 업무가 PCF process context `입찰·제안·견적 수정`에 자연스럽게 위치하는가? |
| 2 | 0.2066 | `pcf:E:11790` 고객에 입찰·제안·견적 제출/제시 | name=0.25; def=0.137; verb=0.0; hier=0.4 | `제안서 리뷰` 업무가 PCF process context `고객에 입찰·제안·견적 제출/제시`에 자연스럽게 위치하는가? |
| 3 | 0.2778 | `pcf:E:11779` 영업 제안서·견적서 개발·관리 | name=0.4545; def=0.13; verb=0.2222; hier=0.2727 | `제안서 리뷰` 업무가 PCF process context `영업 제안서·견적서 개발·관리`에 자연스럽게 위치하는가? |
| 4 | 0.1473 | `pcf:E:11781` RFP/RFQ 접수 | name=0.125; def=0.1191; verb=0.0; hier=0.2 | `제안서 리뷰` 업무가 PCF process context `RFP/RFQ 접수`에 자연스럽게 위치하는가? |
| 5 | 0.1825 | `pcf:E:20663` 제안 IT 투자 프로젝트 평가 | name=0.2727; def=0.1039; verb=0.0; hier=0.25 | `제안서 리뷰` 업무가 PCF process context `제안 IT 투자 프로젝트 평가`에 자연스럽게 위치하는가? |

## 10. PCF / 수주전략 수립

- group_key: `PCF::L2_TASK_WIN_STRATEGY_DEVELOPMENT`
- group_priority: 0.8516
- score_gap: 0.0371
- review_focus: high-score verification; complete Top-5 before metric use

| rank | score | target | score signals | review question |
|---:|---:|---|---|---|
| 1 | 0.4016 | `pcf:E:10952` 철수 전략 수립 | name=0.8; def=0.2329; verb=0.25; hier=0.1429 | `수주전략 수립` 업무가 PCF process context `철수 전략 수립`에 자연스럽게 위치하는가? |
| 2 | 0.3645 | `pcf:E:20092` 리콜 전략 수립 | name=0.6667; def=0.1968; verb=0.3333; hier=0.1429 | `수주전략 수립` 업무가 PCF process context `리콜 전략 수립`에 자연스럽게 위치하는가? |
| 3 | 0.2785 | `pcf:E:20873` 서비스 지원 전략 정의·개발 | name=0.2727; def=0.173; verb=0.5; hier=0.125 | `수주전략 수립` 업무가 PCF process context `서비스 지원 전략 정의·개발`에 자연스럽게 위치하는가? |
| 4 | 0.1085 | `pcf:E:21700` 직원 경력 개발 관리 | name=0.1111; def=0.1682; verb=0.4; hier=0.0 | `수주전략 수립` 업무가 PCF process context `직원 경력 개발 관리`에 자연스럽게 위치하는가? |
| 5 | 0.2731 | `pcf:E:20889` IT 서비스 전달 전략 개발 | name=0.2727; def=0.1666; verb=0.5; hier=0.125 | `수주전략 수립` 업무가 PCF process context `IT 서비스 전달 전략 개발`에 자연스럽게 위치하는가? |

## 11. PCF / 기회분석

- group_key: `PCF::L2_TASK_OPPORTUNITY_ASSESSMENT`
- group_priority: 0.8492
- score_gap: 0.0327
- review_focus: complete Top-5 before metric use

| rank | score | target | score signals | review question |
|---:|---:|---|---|---|
| 1 | 0.276 | `pcf:E:18116` 기회 수주 계획 수립 | name=0.2667; def=0.2597; verb=0.0; hier=0.5 | `기회분석` 업무가 PCF process context `기회 수주 계획 수립`에 자연스럽게 위치하는가? |
| 2 | 0.2433 | `pcf:E:20011` 기회 파이프라인 관리 | name=0.2667; def=0.2425; verb=0.0; hier=0.25 | `기회분석` 업무가 PCF process context `기회 파이프라인 관리`에 자연스럽게 위치하는가? |
| 3 | 0.2177 | `pcf:E:11773` 기회를 사업전략에 매칭 | name=0.25; def=0.2059; verb=0.0; hier=0.2 | `기회분석` 업무가 PCF process context `기회를 사업전략에 매칭`에 자연스럽게 위치하는가? |
| 4 | 0.2277 | `pcf:E:16937` 영업팀에 기회 전달 | name=0.2857; def=0.1972; verb=0.0; hier=0.25 | `기회분석` 업무가 PCF process context `영업팀에 기회 전달`에 자연스럽게 위치하는가? |
| 5 | 0.1118 | `pcf:E:20119` 개선 기회 식별 | name=0.3333; def=0.191; verb=0.0; hier=0.0 | `기회분석` 업무가 PCF process context `개선 기회 식별`에 자연스럽게 위치하는가? |

## 12. NCS / 킥오프 미팅

- group_key: `NCS::L2_TASK_KICKOFF_MEETING`
- group_priority: 0.834
- score_gap: 0.0185
- review_focus: complete Top-5 before metric use

| rank | score | target | score signals | review question |
|---:|---:|---|---|---|
| 1 | 0.0794 | `ncs:CU:1508050103_17v2` 선행도장 계획 작성 | name=0.125; def=0.118; verb=0.3333; hier=0.0 | `킥오프 미팅` 수행에 필요한 직무 능력단위로 `선행도장 계획 작성`가 방어 가능한가? |
| 2 | 0.1896 | `ncs:CU:2305060106_15v1` 제안서 작성 | name=0.1667; def=0.1029; verb=0.1111; hier=0.4 | `킥오프 미팅` 수행에 필요한 직무 능력단위로 `제안서 작성`가 방어 가능한가? |
| 3 | 0.1711 | `ncs:CU:2001050106_25v5` 기술영업 제안 작업 | name=0.125; def=0.0997; verb=0.1667; hier=0.25 | `킥오프 미팅` 수행에 필요한 직무 능력단위로 `기술영업 제안 작업`가 방어 가능한가? |
| 4 | 0.0124 | `ncs:CU:1508040112_14v2` 정도(Dimension) 검사 | name=0.0909; def=0.0992; verb=0.0; hier=0.0 | `킥오프 미팅` 수행에 필요한 직무 능력단위로 `정도(Dimension) 검사`가 방어 가능한가? |
| 5 | 0.0386 | `ncs:CU:1508010102_23v4` 건조사양서 작성 | name=0.1429; def=0.087; verb=0.125; hier=0.0 | `킥오프 미팅` 수행에 필요한 직무 능력단위로 `건조사양서 작성`가 방어 가능한가? |

## 13. PCF / 솔루션 결정

- group_key: `PCF::L2_TASK_SOLUTION_DEFINITION`
- group_priority: 0.8112
- score_gap: 0.0472
- review_focus: high-score verification; complete Top-5 before metric use

| rank | score | target | score signals | review question |
|---:|---:|---|---|---|
| 1 | 0.3409 | `pcf:E:20627` 솔루션 설계 활동 촉진 | name=0.4444; def=0.2124; verb=0.4444; hier=0.25 | `솔루션 결정` 업무가 PCF process context `솔루션 설계 활동 촉진`에 자연스럽게 위치하는가? |
| 2 | 0.3881 | `pcf:E:20071` 솔루션 정의 | name=0.8333; def=0.1754; verb=0.2222; hier=0.25 | `솔루션 결정` 업무가 PCF process context `솔루션 정의`에 자연스럽게 위치하는가? |
| 3 | 0.3106 | `pcf:E:20076` 솔루션 배포 | name=0.6667; def=0.1698; verb=0.0; hier=0.25 | `솔루션 결정` 업무가 PCF process context `솔루션 배포`에 자연스럽게 위치하는가? |
| 4 | 0.2567 | `pcf:E:20797` IT 솔루션 라이프사이클 정의 | name=0.4545; def=0.1586; verb=0.1111; hier=0.125 | `솔루션 결정` 업무가 PCF process context `IT 솔루션 라이프사이클 정의`에 자연스럽게 위치하는가? |
| 5 | 0.3117 | `pcf:E:20072` 솔루션 검증 | name=0.6667; def=0.1446; verb=0.0; hier=0.375 | `솔루션 결정` 업무가 PCF process context `솔루션 검증`에 자연스럽게 위치하는가? |

## 14. PCF / 제안팀 구성

- group_key: `PCF::L2_TASK_PROPOSAL_TEAM_FORMATION`
- group_priority: 0.809883
- score_gap: 0.0293
- review_focus: complete Top-5 before metric use

| rank | score | target | score signals | review question |
|---:|---:|---|---|---|
| 1 | 0.1832 | `pcf:E:11142` 설계 팀 구성 | name=0.6154; def=0.156; verb=0.1111; hier=0.0 | `제안팀 구성` 업무가 PCF process context `설계 팀 구성`에 자연스럽게 위치하는가? |
| 2 | 0.1456 | `pcf:E:20062` 프로젝트 계획 수정·승인 | name=0.1053; def=0.1212; verb=0.0; hier=0.2222 | `제안팀 구성` 업무가 PCF process context `프로젝트 계획 수정·승인`에 자연스럽게 위치하는가? |
| 3 | 0.0439 | `pcf:E:10051` 인수인계 활동 평가를 위한 역할 활동도 작성 | name=0.1333; def=0.1209; verb=0.0909; hier=0.0 | `제안팀 구성` 업무가 PCF process context `인수인계 활동 평가를 위한 역할 활동도 작성`에 자연스럽게 위치하는가? |
| 4 | 0.2125 | `pcf:E:20627` 솔루션 설계 활동 촉진 | name=0.1111; def=0.1185; verb=0.4444; hier=0.2222 | `제안팀 구성` 업무가 PCF process context `솔루션 설계 활동 촉진`에 자연스럽게 위치하는가? |
| 5 | 0.1573 | `pcf:E:11468` 고객팀에 기획 정보 전파 | name=0.2105; def=0.1135; verb=0.0; hier=0.1111 | `제안팀 구성` 업무가 PCF process context `고객팀에 기획 정보 전파`에 자연스럽게 위치하는가? |

## 15. NCS / 가격 전략 수립

- group_key: `NCS::L2_TASK_PRICE_STRATEGY`
- group_priority: 0.8
- score_gap: 0.0534
- review_focus: high-score verification; complete Top-5 before metric use

| rank | score | target | score signals | review question |
|---:|---:|---|---|---|
| 1 | 0.3835 | `ncs:CU:0201020115_24v5` PR 전략 수립 | name=0.75; def=0.1411; verb=0.25; hier=0.5 | `가격 전략 수립` 수행에 필요한 직무 능력단위로 `PR 전략 수립`가 방어 가능한가? |
| 2 | 0.4369 | `ncs:CU:1802030104_14v2` 의류 가격전략수립 | name=0.7059; def=0.1232; verb=0.4; hier=1.0 | `가격 전략 수립` 수행에 필요한 직무 능력단위로 `의류 가격전략수립`가 방어 가능한가? |
| 3 | 0.2274 | `ncs:CU:0201020111_24v4` PR 환경분석 | name=0.1333; def=0.1202; verb=0.4; hier=0.5 | `가격 전략 수립` 수행에 필요한 직무 능력단위로 `PR 환경분석`가 방어 가능한가? |
| 4 | 0.0479 | `ncs:CU:1506030118_20v1` 자동차 고전압전기장치 정비 | name=0.2727; def=0.1105; verb=0.0; hier=0.0 | `가격 전략 수립` 수행에 필요한 직무 능력단위로 `자동차 고전압전기장치 정비`가 방어 가능한가? |
| 5 | 0.0379 | `ncs:CU:1508060105_15v3` 보조기계 시운전 | name=0.25; def=0.1008; verb=0.0; hier=0.0 | `가격 전략 수립` 수행에 필요한 직무 능력단위로 `보조기계 시운전`가 방어 가능한가? |

## 16. NCS / 경쟁사 분석

- group_key: `NCS::L2_TASK_COMPETITOR_ANALYSIS`
- group_priority: 0.8
- score_gap: 0.0911
- review_focus: high-score verification; complete Top-5 before metric use

| rank | score | target | score signals | review question |
|---:|---:|---|---|---|
| 1 | 0.2075 | `ncs:CU:2001050105_25v5` 수주전략수립 | name=0.0; def=0.1093; verb=0.2; hier=0.8333 | `경쟁사 분석` 수행에 필요한 직무 능력단위로 `수주전략수립`가 방어 가능한가? |
| 2 | 0.2739 | `ncs:CU:1902020104_16v2` 전자부품 적용제품분석 | name=0.3529; def=0.1016; verb=0.5; hier=0.2 | `경쟁사 분석` 수행에 필요한 직무 능력단위로 `전자부품 적용제품분석`가 방어 가능한가? |
| 3 | 0.365 | `ncs:CU:1001010111_20v2` 영업 환경분석 | name=0.4615; def=0.0991; verb=0.6667; hier=0.6 | `경쟁사 분석` 수행에 필요한 직무 능력단위로 `영업 환경분석`가 방어 가능한가? |
| 4 | 0.2349 | `ncs:CU:1002010104_20v2` 개발도입용도분석 | name=0.2857; def=0.091; verb=0.25; hier=0.4 | `경쟁사 분석` 수행에 필요한 직무 능력단위로 `개발도입용도분석`가 방어 가능한가? |
| 5 | 0.0454 | `ncs:CU:1705030101_21v1` 분석 준비·데이터 품질 관리 | name=0.1905; def=0.084; verb=0.2; hier=0.0 | `경쟁사 분석` 수행에 필요한 직무 능력단위로 `분석 준비·데이터 품질 관리`가 방어 가능한가? |

## 17. NCS / 고객 니즈 분석

- group_key: `NCS::L2_TASK_CUSTOMER_NEEDS_ANALYSIS`
- group_priority: 0.8
- score_gap: 0.0735
- review_focus: high-score verification; complete Top-5 before metric use

| rank | score | target | score signals | review question |
|---:|---:|---|---|---|
| 1 | 0.3761 | `ncs:CU:1506050103_18v2` 고객 니즈 파악 | name=0.75; def=0.2041; verb=0.25; hier=0.1429 | `고객 니즈 분석` 수행에 필요한 직무 능력단위로 `고객 니즈 파악`가 방어 가능한가? |
| 2 | 0.3026 | `ncs:CU:0302020106_16v2` 고객 상담 | name=0.4615; def=0.1876; verb=0.2; hier=0.4286 | `고객 니즈 분석` 수행에 필요한 직무 능력단위로 `고객 상담`가 방어 가능한가? |
| 3 | 0.2293 | `ncs:CU:1601030101_16v4` 고객 요구사항 파악 | name=0.4444; def=0.1255; verb=0.0; hier=0.1667 | `고객 니즈 분석` 수행에 필요한 직무 능력단위로 `고객 요구사항 파악`가 방어 가능한가? |
| 4 | 0.1957 | `ncs:CU:1003020115_16v2` 고객요구 관리 | name=0.4; def=0.1089; verb=0.0; hier=0.1667 | `고객 니즈 분석` 수행에 필요한 직무 능력단위로 `고객요구 관리`가 방어 가능한가? |
| 5 | 0.1995 | `ncs:CU:1301020109_22v3` 식음료 고객 관리 | name=0.3529; def=0.1028; verb=0.0; hier=0.2 | `고객 니즈 분석` 수행에 필요한 직무 능력단위로 `식음료 고객 관리`가 방어 가능한가? |

## 18. NCS / 수주전략 수립

- group_key: `NCS::L2_TASK_WIN_STRATEGY_DEVELOPMENT`
- group_priority: 0.8
- score_gap: 0.1681
- review_focus: high-score verification; complete Top-5 before metric use

| rank | score | target | score signals | review question |
|---:|---:|---|---|---|
| 1 | 0.4713 | `ncs:CU:2001050105_25v5` 수주전략수립 | name=0.9231; def=0.1885; verb=0.1667; hier=0.8571 | `수주전략 수립` 수행에 필요한 직무 능력단위로 `수주전략수립`가 방어 가능한가? |
| 2 | 0.0163 | `ncs:CU:2002040114_22v2` CG 소스 후반 작업 | name=0.1111; def=0.1301; verb=0.0; hier=0.0 | `수주전략 수립` 수행에 필요한 직무 능력단위로 `CG 소스 후반 작업`가 방어 가능한가? |
| 3 | 0.2285 | `ncs:CU:2001010101_19v4` 정보기술 전략 기획 | name=0.3529; def=0.1133; verb=0.2; hier=0.1429 | `수주전략 수립` 수행에 필요한 직무 능력단위로 `정보기술 전략 기획`가 방어 가능한가? |
| 4 | 0.2865 | `ncs:CU:2001010104_19v4` 정보기술 프로세스관리 전략 수립 | name=0.4167; def=0.1083; verb=0.4; hier=0.2857 | `수주전략 수립` 수행에 필요한 직무 능력단위로 `정보기술 프로세스관리 전략 수립`가 방어 가능한가? |
| 5 | 0.3032 | `ncs:CU:0201030116_21v4` STP 전략 수립 | name=0.625; def=0.0963; verb=0.2; hier=0.2857 | `수주전략 수립` 수행에 필요한 직무 능력단위로 `STP 전략 수립`가 방어 가능한가? |

## 19. NCS / 제안서 기획

- group_key: `NCS::L2_TASK_PROPOSAL_PLANNING`
- group_priority: 0.8
- score_gap: 0.2687
- review_focus: high-score verification; complete Top-5 before metric use

| rank | score | target | score signals | review question |
|---:|---:|---|---|---|
| 1 | 0.0756 | `ncs:CU:1508010104_23v4` 기본도면 작성 | name=0.1538; def=0.2047; verb=0.0; hier=0.0 | `제안서 기획` 수행에 필요한 직무 능력단위로 `기본도면 작성`가 방어 가능한가? |
| 2 | 0.3751 | `ncs:CU:2305060106_15v1` 제안서 작성 | name=0.6667; def=0.141; verb=0.0; hier=1.0 | `제안서 기획` 수행에 필요한 직무 능력단위로 `제안서 작성`가 방어 가능한가? |
| 3 | 0.1064 | `ncs:CU:0201020115_24v5` PR 전략 수립 | name=0.1429; def=0.1126; verb=0.5; hier=0.0 | `제안서 기획` 수행에 필요한 직무 능력단위로 `PR 전략 수립`가 방어 가능한가? |
| 4 | 0.067 | `ncs:CU:0201020114_24v4` PR 환경조사 | name=0.1538; def=0.1078; verb=0.3333; hier=0.0 | `제안서 기획` 수행에 필요한 직무 능력단위로 `PR 환경조사`가 방어 가능한가? |
| 5 | 0.0537 | `ncs:CU:0201020111_24v4` PR 환경분석 | name=0.1538; def=0.106; verb=0.25; hier=0.0 | `제안서 기획` 수행에 필요한 직무 능력단위로 `PR 환경분석`가 방어 가능한가? |

## 20. NCS / 제안서 리뷰

- group_key: `NCS::L2_TASK_PROPOSAL_REVIEW`
- group_priority: 0.8
- score_gap: 0.0671
- review_focus: high-score verification; complete Top-5 before metric use

| rank | score | target | score signals | review question |
|---:|---:|---|---|---|
| 1 | 0.3646 | `ncs:CU:2305060106_15v1` 제안서 작성 | name=0.6667; def=0.187; verb=0.125; hier=0.5 | `제안서 리뷰` 수행에 필요한 직무 능력단위로 `제안서 작성`가 방어 가능한가? |
| 2 | 0.2975 | `ncs:CU:0302010109_14v1` 보험 상품 개발 제안서 작성 | name=0.381; def=0.1431; verb=0.2857; hier=0.5 | `제안서 리뷰` 수행에 필요한 직무 능력단위로 `보험 상품 개발 제안서 작성`가 방어 가능한가? |
| 3 | 0.2179 | `ncs:CU:2001050106_25v5` 기술영업 제안 작업 | name=0.375; def=0.1124; verb=0.0; hier=0.2857 | `제안서 리뷰` 수행에 필요한 직무 능력단위로 `기술영업 제안 작업`가 방어 가능한가? |
| 4 | 0.1695 | `ncs:CU:0201020115_24v5` PR 전략 수립 | name=0.1429; def=0.0861; verb=0.1667; hier=0.25 | `제안서 리뷰` 수행에 필요한 직무 능력단위로 `PR 전략 수립`가 방어 가능한가? |
| 5 | 0.1688 | `ncs:CU:1001010105_20v2` 영업 제안 | name=0.3636; def=0.0747; verb=0.0; hier=0.1429 | `제안서 리뷰` 수행에 필요한 직무 능력단위로 `영업 제안`가 방어 가능한가? |

## Output Files

- JSON: `experiments/cape_kg_eacl_20260627/06_release/mapping_review_group_briefing.json`
- Markdown: `experiments/cape_kg_eacl_20260627/06_release/mapping_review_group_briefing.md`
- CSV: `experiments/cape_kg_eacl_20260627/05_review/mapping_review_group_briefing_top20.csv`
