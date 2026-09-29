# minjoo PARS-KG-RAG

`PARS-KG-RAG`(PCF-Anchored Property-Relation Subgraph KG-RAG)의 최종 재현 패키지다. 질문을 PCF에 먼저 정렬한 뒤, 비지도 Aspect와 지식 그래프의 노드·속성·관계를 함께 이용해 EvidenceSpan Top-5를 선택하고 답변을 생성한다. Query Profile과 LLM 기반 Aspect 추출은 최종 방법에서 사용하지 않는다.

이 디렉터리는 기존 `KG-RAG/`의 실험 이력을 변경하지 않고, 최종 코드·설정·데이터·테스트·핵심 문서·요약 결과만 `minjoo` 이름으로 모은 공개용 스냅샷이다.

## 최종 파이프라인

```text
질문
  -> Kiwi 후보구 생성
  -> 그래프 기반 5개 신호로 Aspect 최대 3개 선택
  -> PCF 경로 / Aspect 직접 검색 / 속성-관계 서브그래프 검색
  -> 세 검색 순위를 RRF로 결합
  -> BAAI/bge-reranker-v2-m3 Cross-Encoder 재정렬
  -> MMR로 중복을 줄여 EvidenceSpan Top-5 선택
  -> gpt-4o-mini-2024-07-18 답변 생성 및 근거 검증
```

핵심 모델과 고정값은 다음과 같다.

- 임베딩: `text-embedding-3-small`, 1,536차원, L2 정규화
- Aspect: Kiwi 후보 생성 + 학습 없는 P1-G 그래프 근거 순위 결합, 최대 3개
- 재정렬: `BAAI/bge-reranker-v2-m3` 고정 revision
- 답변 생성·검증: `gpt-4o-mini-2024-07-18`
- 최종 근거: EvidenceSpan Top-5
- 평가: BLEU-4, ROUGE-1/2/L, `FacebookAI/xlm-roberta-large` BERTScore

세부 수식과 검색 절차는 [방법론 문서](docs/methodology.md), Neo4j 구성은 [그래프 스키마](docs/graph_schema.md)에 정리되어 있다.

## 데이터와 결과

데이터셋은 총 210문항이다. 원문 기반 150문항과 일반 수주·제안 업무를 본뜬 합성 질문 60문항으로 구성되며, 32문항은 개발용, 178문항은 주 비교용이다. Gold Evidence 정렬이 된 주 비교 문항은 175개다. 데이터의 성격과 대표 문항은 [데이터셋 문서](docs/dataset.md), 실제 생성 코드·프롬프트·계보는 [데이터 생성 문서](data_creation/README.md)를 참고한다.

주 비교 178문항의 점수는 아래와 같다. 값은 백분율이며, 시간은 warm-cache 질문당 Top-5 검색 시간이다. 답변 생성 시간은 포함하지 않는다.

| 방법 | Hit@1 | Hit@5 | Recall@5 | Complete@5 | MRR | BLEU-4 | ROUGE-L | BERTScore | 검색 시간(초/질문) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Dense RAG | 47.43 | 77.14 | 60.95 | 46.86 | 58.27 | 24.6841 | 43.8100 | 92.3182 | 0.015 |
| PCF Path | 66.86 | 91.43 | 71.83 | 55.43 | 76.64 | 26.3053 | 45.3674 | 92.5728 | 0.263 |
| PCF+Aspect | 68.00 | 91.43 | 72.59 | 56.00 | 77.35 | 24.7597 | 44.7435 | 92.3902 | 1.020 |
| **PARS-KG-RAG** | **72.57** | 90.29 | **72.88** | **57.71** | **79.77** | 26.2105 | **46.4597** | 92.5215 | 2.225 |

PARS-KG-RAG는 Dense RAG보다 검색 지표가 높았고, Hit@1·MRR·ROUGE-L 등에서 ablation 구성요소의 기여가 관찰됐다. 다만 모든 분할을 개발 과정에서 확인했고 일반 질문 60개가 합성이므로, 결과는 탐색적 실험으로 해석해야 한다. 전체 신뢰구간과 제한사항은 [ablation 보고서](docs/component_ablation.md)에 있다.

## 디렉터리 구조

```text
minjoo_PARS_KG_RAG/
├── config/                  # 최종 비교 및 4-way ablation 설정
├── data_creation/           # 범용 QA 생성기 + 150문항 원본 코드·프롬프트·계보
├── docs/                    # 방법론·데이터·그래프·발표·시각화 문서
├── qa_v2/                   # 최종 210문항 데이터와 생성 명세
├── results/                 # 검증된 기계 판독 요약 JSON
├── scripts/                 # 검색 시간 벤치마크
├── src/kg_rag/              # 검색·Aspect·재정렬·평가 구현
├── tests/                   # 단위 테스트 41개
├── run_experiment.py        # 단계별 실험 실행기
└── requirements.txt
```

`runs/`, `cache/`, 모델 캐시, 가상환경과 비밀정보는 의도적으로 포함하지 않았다. 검증된 원시 실행물의 체크섬은 `results/*.json`에 남겨 두었다.

## 설치

Python 3.11을 기준으로 검증했다.

```bash
cd minjoo_PARS_KG_RAG
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
cp .env.example .env
```

`.env`에는 본인의 Neo4j 접속 정보만 입력하고 OpenAI 키는 셸 환경변수나 비밀관리 도구로 주입한다. `.env`와 키는 Git에 커밋하지 않는다.

```bash
export OPENAI_API_KEY="<YOUR_OPENAI_API_KEY>"
```

CUDA가 없으면 두 설정 파일의 `device: cuda`와 `bertscore_device: cuda`를 `cpu`로 바꿀 수 있다. 결과와 처리 시간은 하드웨어에 따라 달라진다.

## 실행

최종 Dense RAG 대 PARS-KG-RAG 비교:

```bash
python run_experiment.py \
  --config config/experiment.yaml \
  --stage snapshot --run-id <RUN_ID>

python run_experiment.py \
  --config config/experiment.yaml \
  --stage retrieve --run-id <RUN_ID> --reuse-snapshot

python run_experiment.py \
  --config config/experiment.yaml \
  --stage generate --run-id <RUN_ID> --reuse-snapshot

python run_experiment.py \
  --config config/experiment.yaml \
  --stage evaluate --run-id <RUN_ID> --reuse-snapshot
```

Dense → PCF Path → PCF+Aspect → PARS-KG-RAG의 최소 ablation은 `config/experiment_ablation.yaml`로 같은 순서로 실행한다.

검색 시간은 ablation 실행이 끝난 후 측정한다.

```bash
python scripts/benchmark_retrieval_latency.py \
  --config config/experiment_ablation.yaml \
  --source-run runs/<RUN_ID>
```

OpenAI 임베딩·생성 호출과 Neo4j 조회에는 비용이 발생할 수 있다. 먼저 `--limit`으로 소규모 점검을 권장한다.

## 검증

```bash
python -m unittest discover -s tests -v
python -m compileall -q run_experiment.py src scripts qa_v2
```

## 핵심 문서와 산출물

- [최종 방법론](docs/methodology.md)
- [구성요소 ablation 및 전체 성능표](docs/component_ablation.md)
- [10장 이내 발표 슬라이드 초안](docs/presentation.md)
- [210문항 데이터셋 설명](docs/dataset.md)
- [210문항 생성 코드·프롬프트·계보](data_creation/README.md)
- [다른 source용 범용 QA 생성기](data_creation/reusable_qa_generator/README.md)
- [Neo4j 노드·관계·속성](docs/graph_schema.md)
- [실제 성공 사례 HTML](docs/success_case.html)
- [검색 처리 시간](docs/latency.md)
- [최종 결과 JSON](results/final_summary.json)
- [ablation 결과 JSON](results/ablation_summary.json)
- [처리 시간 JSON](results/latency_summary.json)

보안 및 공개 전 점검 사항은 [SECURITY.md](SECURITY.md), 포함·제외 범위는 [RELEASE_MANIFEST.md](RELEASE_MANIFEST.md)에 기록했다.
