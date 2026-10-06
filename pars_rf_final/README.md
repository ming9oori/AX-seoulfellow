# PARS-RF + Kiwi

질문의 세부 요구인 **Aspect로 근거 후보를 확장하고, 원 질문과 원문의 직접 관련성으로 최종 근거를 선택하는 KG-RAG 방법**입니다. 최종 실행 식별자는 `PARS_REFINED`, 선택 방식은 `CE_TOP5`입니다.

```text
질문 → Kiwi Aspect 추출
     → 의미·BM25 관련성 및 PCF·TaskFrame 그래프 보정
     → 질문 후보 Top40 ∪ 각 Aspect 후보 Top20
     → 원 질문–원문 Cross-Encoder Top5
     → 원문 기반 답변 생성 → 근거·인용 검증
```

Aspect 개수의 고정 상한은 없습니다. 그래프에 연결되지 않은 원문도 검색하며, 최종 선택에 coverage 보너스·RRF·MMR을 사용하지 않습니다. 답변의 사실 근거는 선택된 원문입니다.

## 먼저 읽을 자료

| 자료 | 파일 |
|---|---|
| 상세 방법론·수식·실제 사례·결과·한계 | [Markdown](docs/methodology.md) · [PDF](docs/methodology.pdf) · [Word](docs/methodology.docx) |
| 4장 발표 자료와 발표 대본 | [Markdown](presentation/slides.md) · [PowerPoint](presentation/slides.pptx) · [PDF](presentation/slides.pdf) |
| 실제 문장으로 그린 방법론 그림 | [그림 설명과 Mermaid](docs/methodology_figure.md) |
| 최종 메인 테이블 11개 방법 | [CSV](results/main_table.csv) · [발표 자료의 표](presentation/slides.md#슬라이드-3-최종-메인-테이블--11개-방법-비교) |
| 전체 20조건과 구성요소 비교 | [설명 포함 CSV](results/all_methods_explained_20261002.csv) · [JSON](results/method_catalog_20261002.json) |
| 재현 범위·입력·실행 계약 | [재현 안내](docs/reproducibility.md) |

## 핵심 결과

결과 기준은 **2026-10-02**이며 답변 178문항, 검색 Gold 175문항입니다. 시간·비용은 동일 30문항의 별도 온라인 측정입니다.

| 방법 | Recall@5 | BLEU-4 | ROUGE-L | BERTScore | warm 검색 ms | 응답 평균 초 | API USD/30문항 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Dense + CE | 73.78 | 27.24 | 47.08 | 92.72 | 156.48 | 4.77 | 0.010611 |
| **PARS-RF + Kiwi** | **76.90** | **27.63** | **47.51** | **92.80** | **243.26** | **4.56** | **0.010801** |
| PARS-RF + LLM | 77.18 | 27.69 | 47.55 | 92.80 | 249.95 | 6.01 | 0.012486 |

성능은 0–100 척도이며 답변 유사도는 사실 정확도가 아닙니다. 비용은 GPT·임베딩 usage 기반 추정이고 구축·GPU 비용은 제외합니다. 상세 측정 조건과 11개 방법 전체는 메인 테이블을 참고하세요.

**Aspect를 포함한다는 연구 설계에 따라 Kiwi 구성을 채택했습니다. 모든 조건에서 최고라는 의미는 아닙니다.** Aspect 후보 확장 제거 조건의 Recall@5는 77.95로 더 높았으며, Aspect 자체의 이득은 현재 평가에서 확정되지 않았습니다. 기존에 관측한 데이터의 탐색적 평가입니다.

## API 없이 실제 사례 재현

Python 3.11 이상을 사용합니다. 아래 명령은 이 폴더에서 실행합니다.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-replay.txt
python scripts/replay_example.py
```

실제 질문 `JAIJE1-QA-0102`의 Kiwi Aspect, 저장된 점수에서 만든 후보 70개, CE Top5가 원래 실행과 일치하는지 검사합니다. **모델 API나 CE 모델 다운로드는 필요하지 않습니다.** R·M과 CE 로짓은 저장값을 사용하며, 표시하는 답변은 저장된 답변입니다. 임베딩·CE 추론·답변 생성 전체를 새로 수행한 재평가가 아닙니다.

NumPy만으로 후보 통합·선택을 확인하려면 `python scripts/replay_example.py --scores-only`를 사용합니다.

## 새 질문 실행

전체 실행에는 사용할 권한이 있는 원문·그래프 snapshot, 모델 다운로드 환경, OpenAI API 자격증명이 필요합니다. 원문 전체·그래프 원본·모델 가중치·캐시는 이 폴더에 포함하지 않습니다.

```bash
python -m pip install -e .
# OPENAI_API_KEY는 환경변수로 설정합니다. 파일이나 Git에 키를 저장하지 마세요.
python scripts/answer_question.py \
  --snapshot assets/graph_snapshot.json \
  --question "제안은 어떤 방식으로 진행할 수 있으며, 갖춰야 할 두 가지 특성은 무엇인가요?" \
  --device cuda --allow-api
```

기본은 API 호출 비활성 상태입니다. `--allow-api` 실행 시 최초 인덱스·질문 임베딩과 답변·검증에 비용이 발생합니다. usage는 무시된 `runs/live/api_usage.jsonl`에 기록됩니다. 과거 가격을 새 실행에 자동 적용하지 않으며 이번 패키징 작업에서는 새 API 호출을 하지 않았습니다. CUDA가 없으면 `--device cpu`로 실행할 수 있지만 기존 GPU 시간과 비교해서는 안 됩니다.

## 테스트

```bash
python -m pip install -e .
python -m unittest discover -s tests -v
python scripts/replay_example.py
```

원본 전체 실행물이 필요한 이력 회귀 테스트는 해당 실행물이 없으면 명시적으로 skip됩니다. 포함된 테스트 결과와 재현 결과는 [검증 기록](release_validation.json)을 참고하세요. 새 CLI의 유료 종단 간 실행은 패키징 중 재실행하지 않았습니다.

## 폴더 구성

```text
pars_rf_final/
├── src/kg_rag/       # 기존 검증 코드와 내부 의존 모듈
├── config/          # 최종 진입점 설정·Aspect 규칙·이전 프로토콜
├── prompts/         # 고정 생성·검증 프롬프트
├── schemas/         # 출력 JSON 계약
├── examples/        # 실제 한 문항의 추적 기록·저장 점수
├── scripts/         # 오프라인 재현·새 질문 실행
├── tests/           # 추출·선택·뷰·API 계약 테스트
├── docs/            # 상세 방법론·그림·재현 안내
├── presentation/    # 4장 발표 자료
└── results/         # 최종 11조건 및 전체 20조건 결과
```

공통 런타임과의 호환을 위해 이전 방법의 내부 클래스도 포함하지만 최종 진입점은 `CE_TOP5`로 고정합니다. 원본 코드의 계보는 [release_manifest.json](release_manifest.json)에 기록했습니다. 문서 안의 이전 실험 파일 경로는 연구 계보를 나타내며, 이 패키지에서 전체 과거 실험을 다시 실행하는 명령은 아닙니다.
