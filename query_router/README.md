# Query Router 파일럿

`router.pdf`의 검색 필요/불필요 분류기를 구현한다. 기존 QA만 사용하며 새 QA를 생성하지 않는다.

```text
질문 ── 동일 Encoder ── 질문 벡터
                           │
저장된 TaskFrame / TaskMention / Relation 벡터와 코사인 유사도
                           │
        [TaskFrame max, TaskMention max, Relation max]
                           │
          train 통계로 표준화 → Linear 또는 MLP
                           │
               Sigmoid 점수 ≥ 임계값 → 검색 필요
```

Router는 검색 여부만 반환한다. 검색 깊이 조절, 실제 Neo4j 검색, 답변 생성은 구현 범위에 포함되지 않는다.

## 1. 코드 파일: 5개

| 파일 | 역할 |
|---|---|
| `generate_vectors.py` | 온톨로지 HTML 추출, QA 분할, Encoder 벡터와 유사도 3개 저장 |
| `train_linear.py` | Linear(3→1) 정의, 공통 학습·Loss·valid 선택·최종 test 평가 |
| `train_mlp.py` | MLP(3→16→ReLU→1) 정의 및 학습 실행 |
| `run_linear.py` | Linear 체크포인트·Encoder·온톨로지 벡터 로딩 및 질문 실행 |
| `run_mlp.py` | MLP 체크포인트 로딩 및 질문 실행 |

중복 코드를 늘리지 않도록 MLP는 `train_linear.py`의 학습 함수와 `run_linear.py`의 실행 함수를 재사용한다. 모델 클래스는 각 `train_*`에 분리되어 있다.

## 2. 설치

저장소 루트에서 실행한다. 현재 서버의 `router` 환경에는 필요한 패키지가 설치되어 있다.

```bash
cd /data1/home/jonghak/AX-seoulfellow
conda activate router
```

새 환경에서는 다음을 실행한다.

```bash
python -m pip install -r query_router/requirements.txt
```

기본 Encoder는 `BAAI/bge-m3`이며 최초 실행 시 모델 다운로드가 필요하다. 기본 실행은 CPU, 4 threads이다. CUDA 지원 PyTorch와 GPU가 있는 환경에서는 벡터 생성/실행에 `--device cuda`를 지정한다. 작은 분류기 학습은 CPU에서 수행한다.

## 3. 현재 입력과 라벨

- QA: `jaije_qa_dataset/qa_dataset.jsonl` — 기존 150개, 원본 파일은 변경하지 않음.
- 온톨로지: `code_hyuna/taskframe_v4/final_report/task_centric_open_kg_report_v2.html`.
- HTML에서 TaskFrame 12개, TaskMention 314개, Fact 1,936개에서 원문 Relation 1,165개를 추출한다.
- Relation 1,165개는 **고유한 원문 서술어 수**이다. 보고서의 정규화 관계 1,103개와는 다른 집계다.

| 입력 컬럼 | 검색 필요 라벨 |
|---|---|
| `needs_search`가 있으면 | `0/false` → 불필요, `1/true` → 필요 |
| 없으면 `expected_behavior=answer_with_evidence` | `1` |
| 없으면 `expected_behavior=answer_directly` | `0` |

다른 0/1 컬럼은 `--label-column 컬럼명`으로 지정한다. 알 수 없는 값이나 누락된 명시적 라벨은 오류로 처리한다. `answerable`, `source_answerable`, `ontology_answerable`을 검색 필요 라벨로 대신 사용하지 않는다.

**현재 150개는 모두 검색 필요(1)이고 검수 대기 상태이다.** 파일럿은 데이터 처리·학습·저장·재실행을 확인하는 용도이다. 검색 불필요 판별 성능을 평가할 수 없다. 한 클래스 valid에서는 임계값을 0.5로 유지하며, 음성 데이터가 없어 계산할 수 없는 false-positive rate는 `null`로 기록한다. Recall/F₂가 높아도 이진 분류 성능을 입증하지 않는다.

## 4. 데이터 분할과 벡터 생성

```bash
python query_router/generate_vectors.py
```

기본값은 `--ratios 0.7 0.15 0.15 --seed 42`이다. 같은 원본 파일·시트·장·절, 겹치는 원문 행, 동일한 질문을 하나의 그룹으로 묶는다. **비율은 그룹 기준**이므로 문항 수는 정확히 70:15:15가 아닐 수 있다.

현재 분할은 다음과 같다.

| 세트 | QA | 원문 그룹 | 검색 필요/불필요 |
|---|---:|---:|---:|
| train | 101 | 35 | 101 / 0 |
| valid | 21 | 8 | 21 / 0 |
| test | 28 | 8 | 28 / 0 |

분할된 JSONL은 기존 컬럼을 보존하고 `split`을 설정한다. `needs_search`, `router_label_source`, `router_group`을 추가해 학습 라벨과 분할 근거를 기록한다.

Encoder 없이 추출/분할만 확인하려면:

```bash
python query_router/generate_vectors.py --prepare-only --output-dir query_router/artifacts/data_preview
```

온톨로지 전체는 사전에 고정된 검색 지식으로 사용하며 train/valid/test에서 공유한다. QA의 **질문만** Encoder에 입력하고 정답·근거 텍스트·Gold 컬럼은 특징에 넣지 않는다. 따라서 이번 분할은 고정된 지식에 대한 새 질문 평가이며, 보지 못한 온톨로지에 대한 일반화 평가는 아니다.

Encoder는 고정한다. TaskFrame은 업무명·정의·범위·별칭, TaskMention은 원문 표현·행위·대상, Relation은 원문 서술어를 임베딩한다. HTML의 Mention 카드에 없는 intended outcome은 만들어 넣지 않는다. 각 유형에서 최대 코사인 유사도 하나씩만 사용한다. 기본 입력 길이는 512 tokens이며 긴 항목은 모델 tokenizer 기준으로 잘린다. 필요하면 `--max-length`로 조정한다.

## 5. Linear와 MLP 학습

```bash
python query_router/train_linear.py
python query_router/train_mlp.py
```

기본 학습 설정: AdamW, learning rate 0.01, weight decay 0.0001, batch 32, 최대 200 epochs, early stopping patience 20, seed 42.

기본 Loss는 **weighted BCE**, 양성 가중치는 **2.0**이다. `train_linear.py`의 `router_loss()`에 수식과 의미를 주석으로 설명했다. MLP에도 동일한 Loss를 적용한다.

```text
weighted_BCE = -mean[w*y*log(p) + (1-y)*log(1-p)]

PDF 조합 Loss:
L = lambda * weighted_BCE + (1-lambda) * (1-soft_F_beta)
```

`w`가 커지면 필요한 검색을 생략하는 오류에 더 큰 비용을 준다. 실제 F-beta는 미분할 수 없으므로 조합 Loss에는 확률로 계산하는 soft-F-beta를 사용한다. `beta=2`는 Recall을 강조한다. **F-beta를 최소화하는 것이 아니라 `1-F-beta`를 최소화**한다.

조합 Loss 실험 예시:

```bash
python query_router/train_linear.py --loss weighted_bce_fbeta --pos-weight 2 --mix-lambda 0.8 --beta 2 --output-dir query_router/artifacts/bge_m3/linear_f2
python query_router/train_mlp.py --loss weighted_bce_fbeta --pos-weight 2 --mix-lambda 0.8 --beta 2 --output-dir query_router/artifacts/bge_m3/mlp_f2
```

특징 표준화는 train 통계만 사용한다. 최저 valid Loss의 모델을 선택하고, 양성·음성이 모두 있는 valid에서는 목표 Recall 0.95를 만족하며 불필요 검색률을 최소화하는 임계값을 선택한다. 이후 test를 평가한다. Recall 목표는 `--target-recall`로 바꾼다.

`metrics.json`에 confusion matrix, Recall, Precision, F-beta, 검색률, 불필요 검색률과 항상 검색/검색 없음 비교 결과를 저장한다. 모델·Loss 비교에는 valid를 사용하고 test 점수를 보고 설정을 반복 조정하지 않는다. Sigmoid 출력은 라우팅 점수이며 보정된 확률을 보장하지 않는다.

## 6. 저장한 모델 실행

노트북에서는 [router_test.ipynb](router_test.ipynb)를 열고 `router` Python 환경을 커널로 선택한다. 설정·모델 로딩 셀을 한 번 실행한 뒤, 마지막 셀의 `query = ''`에 질문을 입력한다. 질문을 바꿀 때는 마지막 셀만 실행하면 Linear/MLP 결과를 함께 확인할 수 있다. 새 환경에서 커널 실행 패키지가 없으면 `python -m pip install ipykernel`로 설치한다.

`run_mlp.py`는 `run_linear.py`에서 **공통 실행 함수만** 가져온다. `run_router(model_factory=MLPRouter, model_type="mlp")`로 호출하므로 실제 생성되는 모델은 MLP이고 기본 체크포인트는 `mlp/model.pt`이다. import만으로 Linear 모델을 로드하지 않는다.

모델 다운로드 완료 후에는 다음처럼 네트워크 없이 실행할 수 있다.

```bash
HF_HUB_OFFLINE=1 python query_router/run_linear.py --query "제안전략 개발의 평가 기준은 무엇인가?"
HF_HUB_OFFLINE=1 python query_router/run_mlp.py --query "제안전략 개발의 평가 기준은 무엇인가?"
```

다른 체크포인트 실행:

```bash
HF_HUB_OFFLINE=1 python query_router/run_linear.py --checkpoint query_router/artifacts/bge_m3/linear_f2/model.pt --query "고객의 핵심 이슈는 어떻게 분석하는가?"
```

출력 JSON에는 `needs_search`, `search_score`, `threshold`, 유사도 3개, `single_class_pilot`이 포함된다. 현재 모델에는 한 클래스 파일럿이라는 설명도 출력된다.

실행은 학습 때의 Encoder ID/revision, 입력 길이, prefix, 온톨로지 벡터, 표준화 통계, 임계값을 그대로 사용한다. 체크포인트와 다른 벡터 파일은 해시 검사로 거부한다. 벡터 폴더를 옮겼다면 `--vectors-dir`, 모델 캐시 위치를 옮겼다면 `--cache-dir`를 지정한다.

## 7. Encoder 교체 / QA 업데이트

SentenceTransformer로 로드 가능한 임베딩 모델의 Hub ID 또는 로컬 경로를 `--model-name`에 지정한다. 벡터 차원은 자동으로 처리되며 분류기 입력은 항상 유사도 3개이다. 모델의 권장 prefix는 옵션으로 명시한다.

E5로 교체하는 예시:

```bash
python query_router/generate_vectors.py --model-name intfloat/multilingual-e5-base --query-prefix "query: " --ontology-prefix "passage: " --output-dir query_router/artifacts/e5_base
python query_router/train_linear.py --vectors-dir query_router/artifacts/e5_base
python query_router/train_mlp.py --vectors-dir query_router/artifacts/e5_base
HF_HUB_OFFLINE=1 python query_router/run_mlp.py --checkpoint query_router/artifacts/e5_base/mlp/model.pt --query "제안전략 개발의 평가 기준은 무엇인가?"
```

새 QA가 같은 컬럼 구조로 준비되면 `--qa`만 변경해 새 실험 폴더에서 실행한다.

```bash
python query_router/generate_vectors.py --qa jaije_qa_dataset/qa_dataset.jsonl --output-dir query_router/artifacts/updated_qa
python query_router/train_linear.py --vectors-dir query_router/artifacts/updated_qa
python query_router/train_mlp.py --vectors-dir query_router/artifacts/updated_qa
```

추가 데이터의 검색 불필요 사례는 위 라벨 규칙을 따라야 한다. 동일 seed와 동일 입력에서는 분할이 재현되지만 데이터가 추가되면 그룹 배정이 바뀔 수 있다. 기존 test와 직접 비교하려면 기존 실험 폴더를 보존한다.

Encoder·QA·온톨로지가 바뀌면 새 폴더에서 벡터 생성과 분류기 학습을 다시 수행한다. 완료된 벡터/체크포인트의 덮어쓰기는 거부한다.

## 8. 생성 파일

```text
artifacts/
  model_cache/              # 다운로드한 Encoder
  bge_m3/
    ontology.jsonl          # ID/유형/임베딩 텍스트, 원문 Relation의 Fact ID
    train.jsonl
    valid.jsonl
    test.jsonl
    data_summary.json       # 데이터 해시, 분할 수, 클래스 수
    vectors.npz             # 온톨로지/질문 벡터, 3차원 특징, 라벨, QA ID, split
    manifest.json           # Encoder 설정/revision, 특징 순서, 벡터 해시
    linear/                 # mlp/, linear_f2/, mlp_f2/도 동일 구조
      model.pt
      training_config.json
      history.jsonl         # epoch별 train/valid Loss
      metrics.json
      train_predictions.jsonl
      valid_predictions.jsonl
      test_predictions.jsonl
```

`artifacts/`는 로컬 실행 산출물이며 Git에서 제외한다. 실행 코드는 `.py` 5개만 유지한다.

## 9. 현재 실행 확인 결과

2026-09-14, 서버의 `router` 환경(CPU)에서 다음을 확인했다.

- BGE-M3 실제 다운로드와 1,024차원 벡터 생성 완료.
- 원본 QA 150개 보존, 동일 seed 분할 재현, 세트 사이 절·근거 행 중복 없음.
- Linear/MLP × weighted BCE/F₂ 조합의 네 학습 실행과 체크포인트 저장 완료.
- 두 Loss의 단일/양쪽 클래스 입력에서 유한한 Loss·gradient 확인.
- 네 체크포인트를 다시 로딩한 test 점수가 저장된 예측과 일치.
- `run_linear.py`, `run_mlp.py`를 오프라인으로 실행해 실제 질문 처리 완료.

기본 모델은 이미 `artifacts/bge_m3/linear/model.pt`, `artifacts/bge_m3/mlp/model.pt`에 있다. 즉시 사용하려면 **6절의 실행 명령부터** 시작한다. 벡터 생성과 학습을 다시 확인하려면 새 `--output-dir`를 사용한다. 추가 QA나 음성 파일럿 데이터는 만들지 않았다.
