# PARS-KG-RAG 최소 구성요소 Ablation

기준일: 2026-09-21

run ID: `p1p_profile_free_component_ablation_210_20260921`

상태: 검색·답변 생성·BLEU·ROUGE·BERTScore·paired bootstrap 완료

## 1. 무엇을 확인했는가

최종 방법의 복잡도를 과도하게 늘리지 않고, 다음 네 단계만 비교했다.

| 약칭 | 방법 | 추가된 구성요소 |
|---|---|---|
| Dense | 일반 Dense RAG | EvidenceSpan 문장 임베딩 검색 |
| PCF Path | PCF-first | PCF → TaskFrame → Fact/TaskMention → Evidence |
| PCF+Aspect | PCF Path + Direct Aspect | 비-LLM P1-G Aspect가 Evidence를 직접 보조 검색 |
| **PARS-KG-RAG** | PCF+Aspect + Property–Relation Subgraph | 노드 속성·관계·실제 연결 서브그래프 검색 |

세 KG 방법은 모두 Query Profile을 사용하지 않는다. 모델, 데이터, Top-5,
후보 수, RRF, MMR, 답변 프롬프트와 평가 코드는 고정했다. 따라서 단계별 차이는
Aspect와 PARS 구성요소의 추가 효과를 보는 nested ablation이다.

## 2. 데이터와 그래프

- 전체 210문항: 원문 기반 150 + 일반 업무형 합성 60
- 일반 업무형 합성 60: 직접형·시나리오·복수 의도·프로세스·조건 관계·구어체 각 10
- 개발·진단 32문항 제외 후 주 비교 178문항
- 주 비교 구성: 원문 기반 148 + 합성 holdout 30
- Gold Evidence 정렬: 전체 207/210, 주 비교 175/178
- Neo4j: 고유 노드 6,280, 관계 11,325
- 주의: 일반 업무형은 현업자 독립 작성본이 아니며, 모든 분할을 개발 중 관찰했다.

## 3. 고정 모델과 설정

| 역할 | 설정 |
|---|---|
| 임베딩 | `text-embedding-3-small`, 1,536차원, L2 정규화 |
| Aspect | Kiwi 후보 + P1-G 5-signal graph-grounded RRF, 최대 3개, LLM 없음 |
| Cross-Encoder | `BAAI/bge-reranker-v2-m3`, revision `953dc6f...` |
| 답변·인용 검증 | `gpt-4o-mini-2024-07-18` |
| BERTScore | `FacebookAI/xlm-roberta-large`, layer 17 |
| 검색 | PCF 3, TaskFrame 3, branch 후보 20, 재정렬 후보 40, Evidence 5 |
| 융합 | RRF `k=60`, MMR `lambda=0.90` |
| 통계 | paired bootstrap 10,000회; 검색 qid, 답변 section cluster |

## 4. 검색 결과

주 비교 178문항이며 Evidence 지표의 실제 분모는 175문항이다.

| 방법 | Hit@1 | Hit@5 | Recall@5 | Complete@5 | MRR | 평균 검색† (s/query) |
|---|---:|---:|---:|---:|---:|---:|
| Dense | 47.43 | 77.14 | 60.95 | 46.86 | 58.27 | **0.015** |
| PCF Path | 66.86 | **91.43** | 71.83 | 55.43 | 76.64 | 0.263 |
| PCF+Aspect | 68.00 | **91.43** | 72.59 | 56.00 | 77.35 | 1.020 |
| **PARS-KG-RAG** | **72.57** | 90.29 | **72.88** | **57.71** | **79.77** | 2.225 |

† 주 비교 178문항 warm-cache 질문→Top-5 검색 시간이다. Aspect 방법은
P1-G 추출 평균 0.714초/query를 포함한다. 일회성 인덱스·모델 로딩,
uncached OpenAI 임베딩, GPT 답변·검증은 제외했다. 상세 측정 정의와
중앙값·P95는 [처리 시간 보고서](latency.md)에 있다.

PARS-KG-RAG − PCF+Aspect:

| 지표 | 차이(%p) | paired 95% CI | 판정 |
|---|---:|---:|---|
| Hit@1 | +4.57 | [1.14, 8.00] | 유의한 상승 |
| Hit@5 | -1.14 | [-4.00, 1.71] | 차이 불확실 |
| Recall@5 | +0.29 | [-2.19, 2.86] | 차이 불확실 |
| Complete@5 | +1.71 | [-1.14, 4.57] | 차이 불확실 |
| MRR | +2.42 | [0.26, 4.79] | 유의한 상승 |

PARS-KG-RAG − PCF Path에서 Hit@1은 +5.71%p, 95% CI [0.57, 10.86]로 상승했다.
MRR은 +3.13%p였지만 CI [-0.14, 6.56]가 0을 조금 포함했다. PCF+Aspect − PCF Path의
모든 검색 지표 CI는 0을 포함해, Direct Aspect만의 평균 효과는 이 실행에서
확정되지 않았다.

PARS-KG-RAG − Dense는 다섯 검색 지표 모두 CI가 0보다 컸다. Hit@1 +25.14%p
[18.29, 32.00], MRR +21.50%p [16.26, 26.78]였다.

## 5. 최종 답변 결과

| 방법 | BLEU-4 | R-1 | R-2 | R-L | BERTScore | 보류율 |
|---|---:|---:|---:|---:|---:|---:|
| Dense | 24.68 | 52.43 | 32.14 | 43.81 | 92.32 | 1.69 |
| PCF Path | **26.31** | 54.61 | 34.45 | 45.37 | **92.57** | 2.25 |
| PCF+Aspect | 24.76 | 53.69 | 33.19 | 44.74 | 92.39 | 2.81 |
| **PARS-KG-RAG** | 26.21 | **55.06** | **34.87** | **46.46** | 92.52 | 2.25 |

PARS-KG-RAG는 ROUGE-1/2/L 점추정치가 가장 높았다. PCF+Aspect 대비 ROUGE-L 차이
+1.72점의 95% CI [0.07, 3.40]만 0보다 컸고, 나머지 답변 지표 CI는 0을
포함했다. PCF Path 대비 답변 지표는 모두 통계적으로 구분되지 않았다.

Dense 대비 PARS-KG-RAG는 ROUGE-1 +2.64 [1.11, 4.18], ROUGE-2 +2.74
[1.02, 4.51], ROUGE-L +2.65 [0.90, 4.32]로 상승했다. BLEU와 BERTScore
CI는 0을 포함했다.

## 6. 구조적 기여가 선명한 실제 사례

source-derived 문항 `JAIJE1-QA-0101`:

> 기회분석이 끝난 뒤 제안참여 의사결정 전에는 어떤 결정이 이루어집니까?

P1-G가 선택한 검색 Aspect:

1. `기회 분석 끝나 뒤 제안 참여 의사 결정 전 이루어지`
2. `끝나 뒤 제안 참여`
3. `참여 의사 결정 전`

초기 PCF Top-3에는 일반적인 승인·통지 프로세스가 섞였다. PCF를 hard gate로
사용하지 않았기 때문에 PARS가 Evidence-rooted closure에서 다음 저장 구조를 다시 찾았다.

```text
PCFProcess(기회 수주 계획 수립)
  ← MAPS_TO_PCF — TaskFrame(입찰 의사결정 및 기회 관리)
  ← HAS_SUPPORTING_FACT — Fact(기회분석 후 영업참여 결정)
  → RELATED_TO_TASK_MENTION → TaskMention
  → SUPPORTED_BY → EvidenceSpan
```

첫 번째 최종 Evidence의 다섯 PARS 신호 순위는 question-property 1위,
Aspect coverage 3위, edge support 3위, PCF anchor 1위, Evidence relevance
1위였다. 두 Gold Evidence의 검색 결과는 다음과 같다.

| 방법 | MRR | Recall@5 | Complete@5 |
|---|---:|---:|---:|
| Dense | 0.20 | 0.50 | 0 |
| PCF Path | 0.50 | 0.50 | 0 |
| PCF+Aspect | 0.50 | 0.50 | 0 |
| **PARS-KG-RAG** | **1.00** | **1.00** | **1** |

PARS-KG-RAG Top-2에는 두 Gold 원문이 모두 포함됐다.

1. “정보수집을 위한 영업활동이 끝나면 … 제안참여 의사결정을 하게 된다.”
2. “기회분석이 끝나고 나면 … 영업활동을 할 것인가를 결정하는 것이
   영업참여 결정(Pursuit Decision)이다.”

이는 한 문항의 성공 사례이며 전체 성능의 대체 증거는 아니다. 다만 Direct Aspect만으로
놓친 복수 근거를 속성·관계 서브그래프가 보완하는 과정을 설명하기에 적합하다.

## 7. 결론

- PARS-KG-RAG는 Hit@1·Recall@5·Complete@5·MRR과 ROUGE-1/2/L 점추정치가 가장 높다.
- PARS 추가 효과는 Hit@1과 MRR에서 통계적으로 확인됐다.
- Direct Aspect만 추가한 효과는 이번 평균 결과에서 유의하지 않았다.
- PARS-KG-RAG의 Hit@5는 PCF Path/PCF+Aspect보다 1.14%p 낮지만 차이는 유의하지 않았다.
- 답변 수준에서 KG ablation 간 차이는 아직 대부분 불확실하다.
- 따라서 현재 주장은 “PARS가 상위 근거의 순위를 개선한다”까지이며,
  독립 현업 질문·반복 생성·blind human evaluation이 필요하다.

## 8. 재실행과 산출물

```bash
OPENAI_API_KEY=<환경변수로만 설정> \
CUDA_VISIBLE_DEVICES=<GPU_ID> \
python run_experiment.py \
  --config config/experiment_ablation.yaml \
  --stage all --run-id <NEW_RUN_ID>
```

- 기계 요약: `../results/ablation_summary.json`
- 원시 실행: `runs/p1p_profile_free_component_ablation_210_20260921/`
- 검색 bootstrap: `metrics/component_ablation_retrieval_analysis.json`
- 답변 요약·bootstrap: `metrics/answer_metric_summary.json`
- 원시 `runs/`는 Git ignore 대상이므로 장기 보존 시 별도 아카이브가 필요하다.
