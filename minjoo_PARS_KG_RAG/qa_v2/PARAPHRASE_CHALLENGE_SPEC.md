# 패러프레이즈 강건성 진단 V1

## 1. 목적과 한계

기존 공식 148문항의 질문 표현만 바꾸고 정답과 Gold Evidence를 고정해 B0/P0/V2가 표현 변화에 얼마나 견디는지 진단한다. 이 데이터는 기존 원문 기반 질문에서 파생한 `synthetic development set`이며, 실무자 독립 질문이나 실제 사용 분포를 대신하지 않는다.

이 실험으로 말할 수 있는 것은 “같은 정보 요구를 다른 말로 물었을 때 어느 검색기가 덜 하락하는가”까지다. “일반 수주·제안 질문에서 V2가 더 우수하다”는 결론은 이후 독립 Operational Set과 KG Challenge Set에서만 검증한다.

## 2. 데이터 구성

개발 문항 `JAIJE1-QA-0001`, `JAIJE1-QA-0002`를 제외한 148문항 각각에 다음 네 행을 둔다.

| 유형 | 문항 수 | 의미 |
|---|---:|---|
| `original_control` | 148 | 기존 질문 원문 |
| `alias_synonym` | 148 | 별칭·동의어·다른 문장 구조 |
| `scenario_query` | 148 | 답 범위를 바꾸지 않는 일반 업무 상황형 표현 |
| `colloquial_query` | 148 | 범위를 누락하지 않은 짧은 구어체 표현 |
| 합계 | 592 | 검색기 내 paired 비교용 |

기존 자동 정렬에서 빠진 3문항은 `paraphrase_gold_overrides.json`에 별도로 기록했다. 이는 새 정답을 만든 것이 아니라, 한 원문 행이 여러 EvidenceSpan으로 분리되거나 표의 HTML 표기가 정규화되어 발생한 정렬 실패를 동결 스냅샷의 같은 페이지·텍스트로 복구한 것이다. 검색 결과나 방법별 점수는 ID 선택에 사용하지 않았다.

## 3. 누출 방지

생성 호출에는 다음 정보만 전달한다.

- 원 질문
- 요구한 세 가지 변형 유형
- 재시도 시 의미 변경 여부 등의 안전한 실패 코드

생성 호출에는 참조 정답, 원문/EvidenceSpan 텍스트, Gold ID, 검색 결과를 전달하지 않는다. 따라서 Evidence 문장을 다시 바꾸어 쓰도록 유도하지 않는다.

검증은 별도 구조화 출력 호출로 수행한다. 검증 호출은 원 질문, 후보 질문, 참조 정답만 보고 다음 네 항목을 판정한다.

- 동일한 정보 요구인가
- 조건·범위·행위자·시점·문항 양이 추가되거나 빠지지 않았는가
- 후보가 정답을 노출하지 않는가
- 자연스럽고 모호하지 않은 한국어인가

네 조건을 모두 통과하고 원 질문·다른 후보와 중복되지 않은 질문만 `challenge_eligible=true`가 된다. 검증 모델은 근거 텍스트나 검색 결과를 보지 않는다. 모델 검증은 사람 검수를 대신하지 않으므로 모든 행의 `review_status`는 `synthetic_not_human_reviewed`로 유지한다.

구조화 출력은 Pydantic 스키마와 Responses API `parse`를 사용하며 모든 요청은 `store=False`다.

## 4. 어휘 중첩 구간

Gold 원문에 포함된 내용 형태소 중 질문이 공유하는 비율을 다음처럼 계산한다.

```text
lexical_overlap = |질문 내용 토큰 ∩ Gold 원문 내용 토큰| / |질문 내용 토큰|
```

고정 임계값은 `low < 1/3`, `1/3 ≤ medium < 2/3`, `high ≥ 2/3`이다. 결과를 보고 임계값을 재조정하지 않는다. Kiwi를 사용할 수 없는 환경에서는 재현 가능한 정규식 토큰화로 대체하지만, 생성과 최종 검증은 같은 환경에서 실행해야 한다.

## 5. 실행 순서

### 5.1 오프라인 사전검증

API 호출 전에 148개 질문, Gold ID, 스냅샷 존재 여부, 체크섬, 예상 행 수를 검사한다.

```bash
python3 qa_v2/generate_paraphrase_challenge.py --prepare-only
```

산출물은 기본적으로 Git에서 제외된 `qa_v2/generated/paraphrase_v1_<UTC>/`에 기록된다.

### 5.2 생성·별도 검증

API 키는 파일이 아니라 현재 프로세스 환경변수로만 제공한다.

```bash
OPENAI_API_KEY=... python3 qa_v2/generate_paraphrase_challenge.py \
  --concurrency 4 \
  --max-rewrite-attempts 2
```

주요 산출물:

- `preflight_manifest.json`: 입력 체크섬과 데이터 고정 정보
- `paraphrase_candidates.jsonl`: 시도별 생성·검증 provenance
- `paraphrase_challenge_all.csv`: 실패 후보까지 포함한 감사용 파일
- `challenge_validation_summary.json`: 통과 상태
- `paraphrase_challenge_ready.csv`: 148×4행이 모두 통과한 경우에만 생성

부분 통과 파일을 실험 입력으로 사용하지 않는다.

### 5.3 CSV 독립 검사

```bash
python3 qa_v2/validate_paraphrase_challenge.py \
  qa_v2/generated/<RUN>/paraphrase_challenge_ready.csv
```

검사기는 원 질문·정답·Gold Evidence 불변성, 4행 구성, 의미 검증 플래그, 질문 중복, 어휘 중첩 점수 재계산을 확인한다.

### 5.4 검색 실험

답변 생성 전에 검색만 비교한다.

```bash
python run_experiment.py \
  --config config/experiment.yaml \
  --qa-csv qa_v2/generated/<RUN>/paraphrase_challenge_ready.csv \
  --stage retrieve \
  --run-id v2_paraphrase_<DATE>
```

### 5.5 paired 분석

```bash
python3 qa_v2/summarize_paraphrase_retrieval.py \
  --qa-csv qa_v2/generated/<RUN>/paraphrase_challenge_ready.csv \
  --metrics-jsonl runs/v2_paraphrase_<DATE>/03_retrieval_metrics_per_question.jsonl \
  --output-json runs/v2_paraphrase_<DATE>/paraphrase_analysis.json \
  --output-md runs/v2_paraphrase_<DATE>/PARAPHRASE_ANALYSIS.md
```

보고서는 다음을 계산한다.

- 전체·변형 유형·어휘 중첩 구간별 Hit@1/5, Recall@5, Complete@5, MRR
- 같은 질문에서 V2−B0, V2−P0, P0−B0 paired 차이와 bootstrap 95% CI
- 같은 Gold를 공유하는 원 질문 대비 각 패러프레이즈의 성능 하락량

## 6. 판정 원칙

- 낮은 어휘 중첩 구간에서 V2−B0의 Recall@5 CI가 0보다 높으면 graph late fusion의 패러프레이즈 보완 가능성을 확인한 것이다.
- V2가 원 질문에서는 B0를 유지하면서 패러프레이즈 하락폭이 더 작아야 실질적인 강건성 개선으로 본다.
- 이 개발셋으로 V2 가중치를 조정했다면 같은 데이터의 개선치를 최종 성능으로 보고하지 않는다.
- 이 결과가 긍정적이어도 실제 실무자 질문을 대신하지 않으며, 최종 결론은 독립 holdout 전까지 유보한다.
