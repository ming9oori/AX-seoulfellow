# PARS-KG-RAG 문항당 검색 처리 시간

측정일: 2026-09-22

기준 실행: `p1p_profile_free_component_ablation_210_20260921`

## 보고용 결과

주 비교 178문항에서 측정한 질문당 평균 검색 처리 시간은 다음과 같다.

| 방법 | 검색 본체 평균 | P1-G Aspect 평균 | **보고용 합계 평균** |
|---|---:|---:|---:|
| Dense RAG | 0.015초 | - | **0.015초/query** |
| PCF Path | 0.263초 | - | **0.263초/query** |
| PCF+Aspect | 0.306초 | 0.714초 | **1.020초/query** |
| **PARS-KG-RAG** | 1.511초 | 0.714초 | **2.225초/query** |

보고용 합계는 독립적으로 각 방법을 운영할 때 질문 입력부터 Top-5 Evidence를
반환할 때까지 필요한 warm-cache 계산 시간이다. PCF+Aspect와 PARS-KG-RAG에는
두 방법이 공통으로 사용하는 P1-G Aspect 추출의 배치 평균 0.714초/query를 한 번
합산했다.

## 검색 본체 분포

| 방법 | N | 평균 | 중앙값 | P95 | 표준편차 |
|---|---:|---:|---:|---:|---:|
| Dense RAG | 178 | 0.0147 | 0.0140 | 0.0243 | 0.0063 |
| PCF Path | 178 | 0.2630 | 0.2549 | 0.3521 | 0.0539 |
| PCF+Aspect | 178 | 0.3063 | 0.2933 | 0.4215 | 0.0651 |
| **PARS-KG-RAG** | 178 | 1.5109 | 1.5298 | 1.7824 | 0.2042 |

위 분포는 검색 본체만의 wall-clock 초이며 Aspect 추출 시간은 포함하지 않는다.
Aspect 추출은 전체 127.1000초, 178문항 평균 0.7140초였다.

## 측정 조건

- 동일한 주 비교 178문항, `D0_ORIGINAL`, Top-5를 사용했다.
- NVIDIA GeForce RTX 3090 1개, PyTorch 2.8.0+cu128, Python 3.11.13에서 측정했다.
- 각 방법을 3문항씩 warm-up한 뒤 1회 측정했다.
- 문항 순서와 문항 내 방법 순서를 고정 seed로 무작위화했다.
- 방법 사이의 Cross-Encoder 점수 캐시는 매 케이스마다 제거했다.
- `time.perf_counter()`로 각 질문의 검색 호출을 개별 계측했다.
- OpenAI 임베딩은 기존 SQLite cache에서 읽었다.

다음 시간은 제외했다.

- 일회성 그래프 인덱스 구성 4.899초
- 일회성 Cross-Encoder 로딩 6.299초
- cache miss 시 OpenAI 임베딩 네트워크 지연
- GPT 답변 생성과 인용 검증 API 지연
- BLEU·ROUGE·BERTScore 등 오프라인 평가 시간

따라서 이 수치는 **방법 간 warm-cache 검색 계산비용 비교**이며 실제 서비스의
end-to-end SLA로 해석하면 안 된다. 답변 API 지연을 포함한 전체 응답시간은 별도
uncached 온라인 반복 측정이 필요하다.

## 재현

```bash
CUDA_VISIBLE_DEVICES=<GPU_ID> \
  python scripts/benchmark_retrieval_latency.py \
  --config config/experiment_ablation.yaml \
  --source-run \
  runs/p1p_profile_free_component_ablation_210_20260921 \
  --warmup 3
```

스크립트는 OpenAI 네트워크 호출을 비활성화하며 임베딩 cache miss가
발생하면 즉시 실패한다. 따라서 실제 API key가 필요하지 않다.
스크립트 SHA-256: `23a1e325916afc09d0116572d5106c099aae75805245d0bb2d86e7a7e91e22f2`

원시 문항별 측정값:
`runs/p1p_profile_free_component_ablation_210_20260921/metrics/retrieval_latency_benchmark.json`

원시 파일 SHA-256:
`7a9f0b06734e3f78e617a10a6696c2069a53839a5db5e3c67a8d744980ec6a62`
