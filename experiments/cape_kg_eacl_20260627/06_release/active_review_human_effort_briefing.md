# CAPE-KG Active Review Human-Effort Briefing

Generated: 2026-06-29T18:55:22.746612+00:00

This briefing orders the pooled active-review effort sheet before human timing collection.
It is a navigation aid only; it does not create a human-effort efficiency claim until the reviewed CSV is returned with timing and decisions.

## Summary

- claim_status: `review_navigation_only_pending_human_effort`
- condition: `P_cape_kg_actual`
- pooled rows: 204
- expected reviewed CSV: `experiments/cape_kg_eacl_20260627/05_review/active_review_human_effort.reviewed.csv`
- briefing CSV: `experiments/cape_kg_eacl_20260627/05_review/active_review_human_effort_briefing.csv`

## Required Reviewer Fields

| field | rule |
|---|---|
| `reviewer_id` | same identifier across all reviewed rows |
| `review_seconds` | positive elapsed seconds for the row |
| `decision` | `correct`, `incorrect`, `partial`, `unsupported`, `invalid`, or `unsure` |
| `corrected_error` | `true` when the reviewer changed or rejected the candidate |
| `high_impact_correction` | `true` for evidence, schema, risk, gateway, or central task-flow corrections |

## Membership Buckets

| bucket | rows | silver error | high-impact | evidence focus |
|---|---:|---:|---:|---:|
| active_and_random_only | 17 | 17 | 8 | 8 |
| active_and_uncertainty_only | 35 | 35 | 24 | 23 |
| active_only | 35 | 35 | 18 | 18 |
| all_three | 13 | 13 | 8 | 7 |
| random_only | 52 | 51 | 32 | 32 |
| uncertainty_and_random_only | 18 | 18 | 15 | 15 |
| uncertainty_only | 34 | 34 | 25 | 24 |

## First 60 Review Rows

| order | item | chunk | triple | bucket | focus |
|---:|---|---|---|---|---|
| 1 | `ARQ-ACT-12cc121dd3131869` | `JZ-CHUNK-0188` | PT 전략 개발 / FEEDS_INTO / 문화콘텐츠 기획서 발표 | active_and_uncertainty_only | high-impact correction check; candidate correctness check; evidence grounding check; low-confidence check |
| 2 | `ARQ-ACT-7e9789b6b2a1bcc0` | `JZ-CHUNK-0196` | 제안서 작성 / USES_INPUT / 감성 슬라이드 준비 | active_and_uncertainty_only | high-impact correction check; candidate correctness check; evidence grounding check; low-confidence check |
| 3 | `ARQ-ACT-383b21b71c5d6127` | `JZ-CHUNK-0196` | 감성 슬라이드 준비 / FEEDS_INTO / 스토리텔링 | all_three | high-impact correction check; candidate correctness check; evidence grounding check; low-confidence check |
| 4 | `ARQ-ACT-047c5e4917b3743e` | `JZ-CHUNK-0188` | PT 전략 개발 / FEEDS_INTO / 제안서 작성 | active_and_uncertainty_only | high-impact correction check; candidate correctness check; evidence grounding check |
| 5 | `ARQ-ACT-e67c90e4bfa15d48` | `JZ-CHUNK-0196` | 전략 수립 / FEEDS_INTO / 제안서 작성 | active_and_uncertainty_only | high-impact correction check; candidate correctness check; evidence grounding check |
| 6 | `ARQ-ACT-c8c96a3908d70dce` | `JZ-CHUNK-0107` | 제안서 페이지 확정 / USES_INPUT / 페이지 할당 기준 | random_only | high-impact correction check; candidate correctness check; evidence grounding check; random-control baseline timing |
| 7 | `ARQ-ACT-ee5f01d3307b79b4` | `JZ-CHUNK-0069` | 경쟁사 약점 극대화 / FEEDS_INTO / 제안서 작성 | all_three | high-impact correction check; candidate correctness check |
| 8 | `ARQ-ACT-d53733e2c507c09c` | `JZ-CHUNK-0014` | 제안서 작성 / HAS_RISK / 영어 제안서 검증 시스템 부재 | active_and_uncertainty_only | high-impact correction check; candidate correctness check |
| 9 | `ARQ-ACT-3cc436b52ec213ed` | `JZ-CHUNK-0188` | PT 전략 개발 / FEEDS_INTO / PR 전략 수립 | active_and_uncertainty_only | high-impact correction check; candidate correctness check; evidence grounding check; low-confidence check |
| 10 | `ARQ-ACT-26d890d9e00cdb81` | `JZ-CHUNK-0037` | 제안 전략 수립 / PRODUCES / 성공 사례 제시 | random_only | high-impact correction check; candidate correctness check; evidence grounding check; random-control baseline timing |
| 11 | `ARQ-ACT-51bead69724a8880` | `JZ-CHUNK-0186` | 발표 전달력에서 졌다 / FEEDS_INTO / 수주 PT에서 졌다는 말 | random_only | high-impact correction check; candidate correctness check; evidence grounding check; random-control baseline timing |
| 12 | `ARQ-ACT-c833229f026eeff1` | `JZ-CHUNK-0130` | 레드팀 리뷰 / BRANCHES_TO / 제안서 작성 | all_three | high-impact correction check; candidate correctness check; evidence grounding check |
| 13 | `ARQ-ACT-58883774b32313bc` | `JZ-CHUNK-0140` | 제안서 작성 / HAS_STEP / 피라미드식 논리구조 | active_and_random_only | high-impact correction check; candidate correctness check; evidence grounding check |
| 14 | `ARQ-ACT-50723925f5fee304` | `JZ-CHUNK-0065` | 경쟁사 비교표(BCM) 사례 1 / PRODUCES / 신규시스템 오픈 지원 필요 | random_only | high-impact correction check; candidate correctness check; evidence grounding check; random-control baseline timing |
| 15 | `ARQ-ACT-2a241e8eee548f65` | `JZ-CHUNK-0054` | 제안서 작성 / USES_INPUT / 기본도면 작성 | active_and_uncertainty_only | high-impact correction check; candidate correctness check; evidence grounding check |
| 16 | `ARQ-ACT-a3acf06cfe268785` | `JZ-CHUNK-0054` | 제안서 전략 개발 / FEEDS_INTO / PR 전략 수립 | uncertainty_and_random_only | high-impact correction check; candidate correctness check; evidence grounding check |
| 17 | `ARQ-ACT-f47a46fa79cd250f` | `JZ-CHUNK-0092` | 제안서 작성 / PRECEDES / 제안서 검토 | active_and_uncertainty_only | high-impact correction check; candidate correctness check; evidence grounding check |
| 18 | `ARQ-ACT-8da97640dc68cecf` | `JZ-CHUNK-0034` | 핵심 관련자 결정 / FEEDS_INTO / 평가위원회 정보 | uncertainty_only | high-impact correction check; candidate correctness check; evidence grounding check |
| 19 | `ARQ-ACT-d3dc4b992bf46b2f` | `JZ-CHUNK-0137` | 서술의 품질 검토 / PRODUCES / 논리적 구조 및 문장 전달성 보고서 | random_only | high-impact correction check; candidate correctness check; evidence grounding check; random-control baseline timing |
| 20 | `ARQ-ACT-ba0d7f980b23996a` | `JZ-CHUNK-0008` | 가격 전략 수립 / FEEDS_INTO / 제안서 작성 | active_and_uncertainty_only | high-impact correction check; candidate correctness check; evidence grounding check |
| 21 | `ARQ-ACT-2009c7f3b72abd48` | `JZ-CHUNK-0061` | 차별화 전략 수립 / PRECEDES / 디지털 전장환경 검토 | uncertainty_and_random_only | high-impact correction check; candidate correctness check; evidence grounding check |
| 22 | `ARQ-ACT-23b94116de48c6b5` | `JZ-CHUNK-0199` | 솔루션 제안 / PRODUCES / 제안서 작성 | all_three | high-impact correction check; candidate correctness check; evidence grounding check |
| 23 | `ARQ-ACT-d633859180b0a174` | `JZ-CHUNK-0091` | RFP 분석 / USED_AS_INPUT_FOR / 목차 개발 | random_only | high-impact correction check; candidate correctness check; evidence grounding check; random-control baseline timing |
| 24 | `ARQ-ACT-1a1cc66e6c255120` | `JZ-CHUNK-0205` | 제안서 작성 / FEEDS_INTO / 리뷰 체크포인트 | active_and_uncertainty_only | high-impact correction check; candidate correctness check; evidence grounding check |
| 25 | `ARQ-ACT-99dead66f848174e` | `JZ-CHUNK-0198` | 기술적 전문성 설명 / FEEDS_INTO / 평가자 이해 | uncertainty_only | high-impact correction check; candidate correctness check; evidence grounding check |
| 26 | `ARQ-ACT-dc336e7f37951cbc` | `JZ-CHUNK-0013` | 제안서 작성 / USES_INPUT / 그림설명문 작성 | active_and_uncertainty_only | high-impact correction check; candidate correctness check; evidence grounding check |
| 27 | `ARQ-ACT-7965bec63c56f79a` | `JZ-CHUNK-0054` | 제안서 전략 개발 / FEEDS_INTO / 수주전략수립 | uncertainty_only | high-impact correction check; candidate correctness check; evidence grounding check |
| 28 | `ARQ-ACT-305ede520fc6e485` | `JZ-CHUNK-0193` | 제안서 / FEEDS_INTO / 솔루션 결정 | uncertainty_and_random_only | high-impact correction check; candidate correctness check; evidence grounding check |
| 29 | `ARQ-ACT-b018815d8584158c` | `JZ-CHUNK-0008` | 수주전략수립 / FEEDS_INTO / 제안서 작성 | active_and_uncertainty_only | high-impact correction check; candidate correctness check; evidence grounding check |
| 30 | `ARQ-ACT-3895bbadfbb0b006` | `JZ-CHUNK-0193` | 솔루션 결정 / PRODUCES / 제안서 | uncertainty_and_random_only | high-impact correction check; candidate correctness check; evidence grounding check |
| 31 | `ARQ-ACT-42bb393b75222b99` | `JZ-CHUNK-0144` | 경쟁사 분석 / FEEDS_INTO / PR 전략 수립 | uncertainty_only | high-impact correction check; candidate correctness check; evidence grounding check |
| 32 | `ARQ-ACT-c879964869814010` | `JZ-CHUNK-0038` | 가치제안 / PRODUCES / 비용 절감 효과 | uncertainty_and_random_only | high-impact correction check; candidate correctness check; evidence grounding check |
| 33 | `ARQ-ACT-9eaf9ed455af06b3` | `JZ-CHUNK-0132` | 제안서 작성 / PERFORMED_BY / 디자이너 | active_and_uncertainty_only | high-impact correction check; candidate correctness check; evidence grounding check |
| 34 | `ARQ-ACT-7a9e3267073572ce` | `JZ-CHUNK-0010` | 제안서 작성 / PRODUCES / 제안서 | active_and_random_only | high-impact correction check; candidate correctness check; evidence grounding check |
| 35 | `ARQ-ACT-1add340096e3edd5` | `JZ-CHUNK-0199` | 가격 전략 수립 / USED_AS_INPUT_FOR / 솔루션 제안 | uncertainty_only | high-impact correction check; candidate correctness check; evidence grounding check |
| 36 | `ARQ-ACT-8b9586c9d1885b21` | `JZ-CHUNK-0132` | 제안서 내용 전달 / FEEDS_INTO / 제안서 작성 | active_and_uncertainty_only | high-impact correction check; candidate correctness check; evidence grounding check |
| 37 | `ARQ-ACT-f13446e2eaf45f79` | `JZ-CHUNK-0193` | 제안서 / HAS_RISK / 선입견 형성 | uncertainty_only | high-impact correction check; candidate correctness check; evidence grounding check |
| 38 | `ARQ-ACT-560376e8e64b0af1` | `JZ-CHUNK-0061` | 기관총 무게 분석 / PRODUCES / 차별화 전략 수립 | random_only | high-impact correction check; candidate correctness check; evidence grounding check; random-control baseline timing |
| 39 | `ARQ-ACT-70283ef009e8b65b` | `JZ-CHUNK-0130` | 제안서 작성 / HAS_PRINCIPLE / 핵심 원리 | active_and_uncertainty_only | high-impact correction check; candidate correctness check; evidence grounding check |
| 40 | `ARQ-ACT-c4aa557a036fb5a7` | `JZ-CHUNK-0053` | 제안 전략 수립 / HAS_STEP / 경쟁사 약점 극대화 | random_only | high-impact correction check; candidate correctness check; evidence grounding check; random-control baseline timing |
| 41 | `ARQ-ACT-bb598167378c2a4b` | `JZ-CHUNK-0012` | 솔루션 결정 / PRECEDES / 경쟁력 분석 | uncertainty_only | high-impact correction check; candidate correctness check; evidence grounding check |
| 42 | `ARQ-ACT-44ce34d01b33227b` | `JZ-CHUNK-0026` | 고객 니즈 파악 / FEEDS_INTO / 제안서 작성 | active_and_uncertainty_only | high-impact correction check; candidate correctness check; evidence grounding check |
| 43 | `ARQ-ACT-3962153ed816aca9` | `JZ-CHUNK-0054` | 제안서 전략 개발 / FEEDS_INTO / 제안서 작성 | active_and_uncertainty_only | high-impact correction check; candidate correctness check; evidence grounding check |
| 44 | `ARQ-ACT-24d0e37804d47709` | `JZ-CHUNK-0092` | 제안서 작성 / USES_INPUT / 논리적 구조 | active_and_uncertainty_only | high-impact correction check; candidate correctness check; evidence grounding check |
| 45 | `ARQ-ACT-7ab6997946c3859c` | `JZ-CHUNK-0031` | SBS 전문가 영업 전략 수립 / PRECEDES / 차별화 전략 | uncertainty_and_random_only | high-impact correction check; candidate correctness check; evidence grounding check |
| 46 | `ARQ-ACT-15b72c71f0288f7e` | `JZ-CHUNK-0026` | 고객 상담 / FEEDS_INTO / 제안서 작성 | all_three | high-impact correction check; candidate correctness check; evidence grounding check |
| 47 | `ARQ-ACT-4f83a523179c14af` | `JZ-CHUNK-0010` | 첨부문서 / USED_AS_INPUT_FOR / 제안서 평가 | uncertainty_only | high-impact correction check; candidate correctness check; evidence grounding check |
| 48 | `ARQ-ACT-d94f8f7ae187b2fd` | `JZ-CHUNK-0023` | 최적화된 솔루션 개발 / FEEDS_INTO / 솔루션 제공 | random_only | high-impact correction check; candidate correctness check; evidence grounding check; random-control baseline timing |
| 49 | `ARQ-ACT-9ac6fc8184f43f8d` | `JZ-CHUNK-0205` | 고객 니즈 파악 / PRODUCES / 제안서 작성 | active_and_uncertainty_only | high-impact correction check; candidate correctness check; evidence grounding check |
| 50 | `ARQ-ACT-4a92fc951bdb4b41` | `JZ-CHUNK-0038` | 가치제안 / PRODUCES / 비용 추적 메커니즘 | uncertainty_only | high-impact correction check; candidate correctness check; evidence grounding check |
| 51 | `ARQ-ACT-9facce77430ed348` | `JZ-CHUNK-0025` | 평가자 이해 / PRECEDES / 전략적 대응 | random_only | high-impact correction check; candidate correctness check; evidence grounding check; random-control baseline timing |
| 52 | `ARQ-ACT-1989d4f20d80bec0` | `JZ-CHUNK-0013` | 그래픽 제작 / PRODUCES / 그래픽 | random_only | high-impact correction check; candidate correctness check; evidence grounding check; random-control baseline timing |
| 53 | `ARQ-ACT-dd577a50cc1d9443` | `JZ-CHUNK-0010` | 근거 제시 / USED_AS_INPUT_FOR / 제안서 작성 | active_and_uncertainty_only | high-impact correction check; candidate correctness check; evidence grounding check |
| 54 | `ARQ-ACT-2b3246889dd1c4f0` | `JZ-CHUNK-0138` | 제안서 평가 / USES_INPUT / 서술의 품질 | uncertainty_only | high-impact correction check; candidate correctness check; evidence grounding check |
| 55 | `ARQ-ACT-2550d586ad181130` | `JZ-CHUNK-0065` | 경쟁사 비교표(BCM) 사례 2 / PRODUCES / 고객의 TCO 고려 | random_only | high-impact correction check; candidate correctness check; evidence grounding check; random-control baseline timing |
| 56 | `ARQ-ACT-ce3d5f74b504c6b2` | `JZ-CHUNK-0145` | 정보 표제 / FEEDS_INTO / 제안서 작성 | all_three | high-impact correction check; candidate correctness check; evidence grounding check |
| 57 | `ARQ-ACT-fbbe736c6eff3bae` | `JZ-CHUNK-0143` | 제안서 작성 / USES_INPUT / 근거 제시 | active_and_random_only | high-impact correction check; candidate correctness check; evidence grounding check |
| 58 | `ARQ-ACT-10dd6bd329b11ed5` | `JZ-CHUNK-0031` | 제약회사 분석 / PRECEDES / SBS 전문가 영업 전략 수립 | uncertainty_only | high-impact correction check; candidate correctness check; evidence grounding check |
| 59 | `ARQ-ACT-be5d932fd2c9ee9f` | `JZ-CHUNK-0190` | PT 슬라이드 개발 / FEEDS_INTO / 제안서 작성 | active_and_uncertainty_only | high-impact correction check; candidate correctness check; evidence grounding check |
| 60 | `ARQ-ACT-edfc05d758ffa2dc` | `JZ-CHUNK-0108` | 충실도 체크리스트 작성 / PRODUCES / 충실도 | random_only | high-impact correction check; candidate correctness check; evidence grounding check; random-control baseline timing |

## Claim Scope

- This briefing uses silver/proxy labels only for review navigation.
- Corrections/hour and high-impact/hour require `active_review_human_effort.reviewed.csv` with timing.
- Paper-level active-review claims still require alignment to adjudicated human-gold outcomes.
