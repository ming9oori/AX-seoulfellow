# TRACE-OL 자이제 전체 실험 최종 보고서

## 최종 상태

- 연구 실행: **COMPLETE**
- 정적 그래프 무결성: **PASS**
- 선택적 OpenAI 판정: **COMPLETE**
- Production 승격: **NOT READY**
- 전체 설계 DoD: **BLOCKED_CQ_GOLD_LIVE_NEO4J_AND_BASELINE_DRIFT**

Production 승격을 보류한 직접 원인은 CQ-07 실패다. BCM의 `자사 - 예산` 점수 Claim이 3회 판정에서 `accept, reject, accept`로 갈려 3/3 승격 기준을 통과하지 못했다.

## 입력 기준

| 항목 | 값 |
|---|---|
| 실제 입력 SHA-256 | `e8c5f174b65eccd7a50dbd2e0e216ea870a6aedfd16b3e4538d6486aea15cf1f` |
| 설계서 기준 SHA-256 | `9246a6da6c7635b3f34ee55df75112eb38a2984ea06828be943dc196de5926eb` |
| 실제 SourceBlock | 1,366 |
| 실제 문맥 누락 | 0 |
| 설계서 예상 문맥 누락 | 3 |

현재 파일의 메타데이터를 원문으로 보존했다. 설계서의 누락 3건을 인위적으로 재현하지 않았으므로 원래 설계 기준 실험과 직접 비교할 수 없다.

## 오프라인 파이프라인

| 항목 | 결과 |
|---|---:|
| EvidenceSpan | 1,552 |
| Table / Cell | 56 / 892 |
| Formula | 1 |
| Claim 후보 | 609 |
| 규칙 기반 Accepted | 43 |
| Neo4j 노드 / 관계 | 4,975 / 7,283 |
| CQ | 12/12 |
| 고정 회귀 | 6/6 |

원문 offset round-trip, 전역 ID 유일성, 관계 끝점, Accepted Claim evidence coverage, direct edge-Claim 일치 검사는 모두 통과했다.

## OpenAI 선택 판정

선택된 최종 run은 `run:20260710T020000Z:P1_TYPED_OPENAI:a9482ce`다.

| 항목 | 결과 |
|---|---:|
| 모델 | `gpt-4o-mini-2024-07-18` |
| typed 후보 | 30 |
| 반복 | 3 |
| API 호출 / 완료 응답 | 90 / 90 |
| schema·ID·근거·domain/range 통과 | 90/90 |
| 3/3 Accepted 승격 | 26 |
| 3/3 Rejected | 2 |
| 2:1 불일치 NeedsReview | 2 |
| 반복 완전 일치율 | 93.33% |
| 최종 Accepted Claim | 39 |
| 최종 Neo4j 노드 / 관계 | 5,065 / 7,369 |
| CQ | 11/12 |
| 고정 회귀 | 6/6 |
| 최종 run 추정 비용 | $0.0225042 |

두 개의 NeedsReview는 다음과 같다.

1. Row 236: `Capture Planning HAS_OUTCOME Bid/No-Bid` — accept 2, reject 1
2. Row 983: `자사 MEASURED_BY 예산` — accept 2, reject 1

두 개의 3/3 Rejected 후보는 Row 236의 `Process HAS_STAGE Capture Planning`, Row 243의 `Stage HAS_TASK 수주전략 초안 개발`이다. 모델 결정을 규칙 결과로 덮어쓰지 않고 Claim Graph에 판정 상태를 보존했다.

## 진단 Run

첫 selective run은 Section placeholder를 subject로 둔 불확실 후보를 사용했다. 이 구조에서는 `Section -[:MITIGATES]-> literal`처럼 predicate domain/range가 불완전해질 수 있음이 확인됐다. 해당 run은 진단용으로 보존했으며 최종 그래프에는 채택하지 않았다.

이후 typed audit queue와 로컬 domain/range 검증을 추가했고, 최종 run에서는 90개 응답 모두 계약을 통과했다.

## 비용과 보안

| 실행 | 호출 | 추정 비용 |
|---|---:|---:|
| 최초 smoke | 1 | $0.0002490 |
| untyped 진단 | 90 | $0.0232116 |
| typed smoke | 1 | $0.0002418 |
| typed 최종 | 90 | $0.0225042 |
| 합계 | 182 | **$0.0462066** |

API 키는 명령행 인자나 파일에 저장하지 않았고, 산출물 검색에서도 키 문자열은 발견되지 않았다. ModelCall 원장에는 모델, prompt/input hash, response ID, 토큰, 지연, 비용 및 판정만 저장했다.

## Neo4j와 평가 한계

- 최종 Neo4j CSV 12,434행의 파서 위험 검사는 오류 0건으로 통과했다.
- Docker 소켓 권한이 없어 live Neo4j 적재·멱등성 재적재·실제 Cypher 실행은 수행하지 못했다.
- Human gold가 없어 precision/recall/F1, bootstrap CI, 규칙 validation precision은 산출하지 않았다.
- 증류 규칙 후보 10개를 생성했지만 별도 validation split과 반례 검증이 없어 채택 규칙은 0개다.
- Python 3.13.13을 사용했으며 설계서의 공식 범위인 Python 3.11/3.12와 다르다.

## 남은 승인 조건

1. Human reviewer가 `human_review_queue.jsonl`의 4개 항목, 특히 두 NeedsReview를 판정한다.
2. CQ-07을 다시 채점하고 12/12를 확인한다.
3. Human gold와 adjudication log를 확보해 B0/B2/P1/P2 및 ablation 성능을 계산한다.
4. Neo4j 5.26.28 Community에 fresh volume으로 적재하고 멱등성·검증 Cypher를 실제 실행한다.
5. 증류 규칙을 별도 rule-validation set에서 검증한 뒤 P2 production run을 생성한다.
