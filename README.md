# AX-seoulfellow: PARS-RF + Kiwi 및 KG 실험

## 최종 방법론: 터미널에서 질문하고 답변 받기

**최종 QA 방법론은 PARS-RF + Kiwi입니다.** 질문에서 Aspect를 추출하고, 그래프 보정을 적용한 검색 후보를 Cross-Encoder로 재정렬한 뒤, 원문 근거를 바탕으로 답변을 생성하고 검증합니다.

- [최종 패키지 안내](pars_rf_final/README.md)
- [상세 방법론](pars_rf_final/docs/methodology.md) · [4장 발표 자료](pars_rf_final/presentation/slides.md)
- [최종 메인 테이블: 11개 방법 비교](pars_rf_final/results/main_table.csv)

아래 명령은 **Bash 터미널** 기준입니다. 현재 `aigpu38` 서버에서는 기존 Python 환경과 그래프 snapshot을 그대로 사용할 수 있습니다. 새 질문 실행에는 OpenAI API 키와 API·모델 다운로드를 위한 네트워크가 필요합니다.

### 1. 현재 서버에서 실행 환경 준비

아래 두 줄을 복사해서 실행하세요. 실행 위치는 `pars_rf_final` 폴더입니다.

```bash
cd "/home/minjoo/AX_서울펠로우/AX-seoulfellow/pars_rf_final"
source ../../KG-RAG/.eval-venv/bin/activate
```

**다른 서버나 새 환경**에서는 저장소의 `pars_rf_final` 폴더로 이동한 다음, Python 3.11 이상으로 환경을 준비합니다. 현재 서버의 기존 환경을 사용하는 경우에는 이 설치 단계를 건너뜁니다.

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

### 2. API 키와 그래프 경로 설정

API 키가 이미 환경변수에 설정되어 있으면 그대로 사용합니다. 그렇지 않으면 아래 명령이 키를 입력받습니다. 입력 중에는 화면에 표시되지 않습니다.

```bash
if [ -z "${OPENAI_API_KEY:-}" ]; then
    read -r -s -p "OpenAI API Key: " OPENAI_API_KEY
    printf '\n'
fi
export OPENAI_API_KEY

export PARS_SNAPSHOT="../../KG-RAG/runs/p1p_profile_free_component_ablation_210_20260921/00_graph_snapshot.json"
test -f "$PARS_SNAPSHOT" && echo "그래프 snapshot 확인 완료"
```

`PARS_SNAPSHOT`은 현재 서버의 실제 그래프 경로입니다. **그래프 snapshot과 전체 원문은 GitHub 패키지에 포함되어 있지 않습니다.** 다른 서버에서는 별도로 전달받은 snapshot의 절대 경로로 바꾸세요. 확인 메시지가 나오지 않으면 경로를 먼저 확인합니다. API 키는 README나 코드에 적지 않습니다.

### 3. 질문을 입력하고 실행

```bash
read -r -p "질문을 입력하세요: " question_text
python scripts/answer_question.py \
  --snapshot "$PARS_SNAPSHOT" \
  --question "$question_text" \
  --device cuda \
  --allow-api
```

예시 질문: `제안은 어떤 방식으로 진행할 수 있으며, 갖춰야 할 두 가지 특성은 무엇인가요?`

GPU를 사용할 수 없으면 `--device cuda`를 `--device cpu`로 바꾸세요. 질문을 한 번 입력하면 답변 생성·검증 후 프로그램이 종료됩니다. **다음 질문은 3번 명령을 다시 실행**하면 됩니다. 이전 대화 내용을 이어받는 채팅 방식은 아닙니다.

### 4. 실행 결과 확인

터미널에는 다음 항목이 JSON으로 출력됩니다.

| 항목 | 의미 |
|---|---|
| `status` | `ANSWERED`: 답변·근거 검증 조건 충족, `INSUFFICIENT`: 조건을 충족하지 못함 |
| `answer` | 검증 단계가 반환한 답변. `status`와 함께 확인 |
| `citations` | 선택된 근거의 인용 ID. 실제 원문은 저장된 검색 결과에서 확인 |

`pars_rf_final` 기준으로 아래 파일도 저장됩니다.

| 파일 | 내용 |
|---|---|
| `runs/live/answer.json` | 질문, 답변, 초안, 검증 결과, 검색 근거 등 상세 결과. 성공적으로 실행할 때마다 덮어씀 |
| `runs/live/api_usage.jsonl` | API 호출 이벤트와 사용량 기록. 실행할 때마다 이어서 기록 |
| `runs/live/embeddings.sqlite` | 다음 실행에서 재사용하는 임베딩 캐시 |

최초 실행에는 문서·그래프 임베딩 생성과 재정렬 모델 로딩 때문에 시간이 더 걸릴 수 있습니다. `--allow-api`는 유료 API 호출을 허용하는 옵션이며, 임베딩과 답변 생성·검증에 비용이 발생합니다. 사용량 로그를 남기지만 **이 CLI는 현재 요금에 따른 달러 비용이나 전체 처리 시간을 자동 집계하지 않습니다.** README의 과거 실험 시간·비용은 이번 질문의 측정값이 아닙니다.

질문별 결과를 보관하려면 실행 명령에 `--output runs/question_001`처럼 서로 다른 출력 폴더를 지정할 수 있습니다. 임베딩 캐시도 해당 폴더에 생성되므로 새 폴더의 첫 실행에는 임베딩 비용이 다시 발생할 수 있습니다.

### 자주 막히는 부분

| 상황 | 확인할 내용 |
|---|---|
| `Snapshot file does not exist` | `pars_rf_final`에서 실행 중인지, `PARS_SNAPSHOT`이 실제 파일을 가리키는지 확인 |
| `OPENAI_API_KEY is not set` | 같은 터미널에서 2번의 키 설정을 실행 |
| `ModuleNotFoundError` | 가상환경 활성화 여부 확인. 새 환경이면 `python -m pip install -e .` 실행 |
| CUDA 관련 오류 | CUDA를 지원하는 PyTorch·GPU 환경을 확인하거나 `--device cpu` 사용 |
| API 인증·연결 또는 모델 다운로드 오류 | 키의 유효성 및 실행 서버의 네트워크 접근 확인 |

API 없이 저장된 사례를 확인하려면 같은 폴더에서 `python scripts/replay_example.py`를 실행합니다. 이는 저장된 점수·답변을 사용하는 재현이며 새 질문에 대한 답변 생성은 아닙니다. 새 질문 CLI의 유료 종단 간 실행은 패키징·README 작성 과정에서 재검증하지 않았습니다.

---

## 기존 실험: 자이제 EG-MOI 온톨로지·KG 구축

아래는 기존 EG-MOI 구축 실험 안내입니다. 아래의 “LLM 호출 0”, “API key 불필요”는 해당 구축 실험의 조건이며, 위 PARS-RF 새 질문 실행에는 적용되지 않습니다.

QA 데이터셋: **[자이제 1·2·3 통합 450문항과 생성 프롬프트·five-shot](jaije_qa_dataset/README.md)**
([CSV](jaije_qa_dataset/final_450/qa_dataset.csv) · [JSONL](jaije_qa_dataset/final_450/qa_dataset.jsonl)).

`자이제_1.xlsx` 문서만 사용해 **원문 근거까지 추적할 수 있는 온톨로지와 Neo4j 지식그래프(KG)**를 자동 생성한 실험이다.

- 최종 방법론: **EG-MOI 1.0**
- 실험 ID: `zaije_eg_moi_20260712_v1`
- 최종 판정: **`EG_MOI_END_TO_END_PASS`**
- 사람 중간 개입: `0`
- LLM 호출: `0`

> 최종 판정은 파이프라인과 구조 검증이 성공했다는 뜻이다. 생성된 개념과 관계의 의미 정확도는 추가 전문가 검증이 필요하다.

## 추가 실험: minjoo PARS-KG-RAG

수주·제안 QA를 위한 PCF 앵커 기반 속성·관계 서브그래프 RAG 실험을
[`minjoo_PARS_KG_RAG`](minjoo_PARS_KG_RAG/README.md)에 추가했다. 해당 패키지에는 최종 코드,
재현 설정, 210문항 QA 데이터, 단위 테스트, 방법론·발표 문서와 검증된 결과 요약이 포함된다.

## 1. 전체 방법

```text
자이제_1.xlsx
  ↓
1. Evidence: 원문과 표 문맥 보존
  ↓
2. Mention·SemanticFrame: 중요 표현과 문장 역할 추출
  ↓
3. ConceptCluster: 같은 개념을 하나로 통합
  ↓
4. 귀납 스키마: 데이터에서 구체적인 분류 구성
  ↓
5. Assertion: 근거와 타입 검증을 통과한 관계 저장
  ↓
RDF·SKOS·PROV-O·SHACL·Neo4j
```

### 핵심 개념

| 개념 | 쉽게 설명 |
|---|---|
| Evidence | 결과가 나온 Excel 원문 |
| Mention | 원문에서 찾은 개별 표현 |
| SemanticFrame | `누가·무엇을·어떻게 한다`는 문장 구조 |
| ConceptCluster | 같은 개념의 여러 표기를 통합한 결과 |
| Class | 개념을 담는 분류 |
| Assertion | `업무-관계-대상`으로 표현한 하나의 사실 주장 |

### 스키마는 어디서 오는가?

처음에는 일관된 분류를 위한 **최소 틀**만 두었다.

```text
WorkUnit / Agent / Resource / Context / Measure / DomainConcept
```

그런 다음 자이제 데이터에서 8개의 구체적인 Class를 귀납했다.

```text
ProposalWorkUnit / ProposalRole / ProposalOrganization
ProposalArtifact / CustomerRequirement / ProposalContext
EvaluationMeasure / ProposalDomainConcept
```

즉, **상위 분류 틀은 사전 정의하고 구체적인 도메인 스키마는 데이터에서 만들었다.**

## 2. 관계 생성 예시

원문:

```text
제안팀이 고객 요구사항을 바탕으로 제안서를 작성한다.
```

추출 결과:

```text
제안서 작성 --PERFORMED_BY----> 제안팀
제안서 작성 --HAS_INPUT-------> 고객 요구사항
제안서 작성 --PRODUCES_OUTPUT-> 제안서
```

사용한 표준 관계:

| 관계 | 의미 |
|---|---|
| `PERFORMED_BY` | 누가 수행하는가 |
| `HAS_INPUT` | 무엇을 입력으로 사용하는가 |
| `PRODUCES_OUTPUT` | 무엇을 산출하는가 |
| `HAS_CONDITION` | 어떤 조건에서 수행하는가 |
| `HAS_MEASURE` | 어떤 수치와 연결되는가 |
| `PRECEDES` | 어떤 업무가 먼저 나오는가 |

관계 이름은 미리 정의했지만, **실제 연결 대상은 표 구조와 한국어 문장 패턴에서 자동 추출**했다.

## 3. 빠른 실행

모든 명령은 저장소 루트에서 실행한다.

```bash
git clone --recurse-submodules https://github.com/ming9oori/AX-seoulfellow.git
cd AX-seoulfellow

python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r \
  zaije_experiment/experiments/zaije_eg_moi_20260712_v1/requirements-eg-moi.txt

# Excel → Evidence → 개념·스키마·Assertion
python zaije_experiment/src/run_eg_moi.py

# RDF·SHACL·Neo4j CSV 생성
python zaije_experiment/src/export_eg_moi.py
```

성공 기준:

```text
run_eg_moi.py    → EG_MOI_PIPELINE_PASS
export_eg_moi.py → pass=true, shacl_conforms=true
```

API key는 필요하지 않다. 입력 파일은 다음이다.

```text
handoff-hanyang/수주제안/자이제_1.xlsx
```

## 4. Neo4j 적재와 검증

최종 적재 파일:

- [nodes.csv](zaije_experiment/experiments/zaije_eg_moi_20260712_v1/neo4j/nodes.csv)
- [edges.csv](zaije_experiment/experiments/zaije_eg_moi_20260712_v1/neo4j/edges.csv)

### 방법 A: Neo4j Desktop Query UI

Neo4j `5.26+`에서는 동적 라벨과 관계 타입을 사용해 UI만으로 적재할 수 있다.

1. `nodes.csv`, `edges.csv`를 Desktop instance의 `import` 폴더에 넣는다.
2. **Tools → Query**를 연다.
3. [UI LOAD CSV 스크립트](zaije_experiment/experiments/zaije_eg_moi_20260712_v1/neo4j/load_csv_import_neo4j_5_26.cypher)를 위에서부터 한 문장씩 실행한다.

핵심 문법은 `SET n:$(split(row[':LABEL'], ';'))`과 `MERGE (source)-[r:$(row[':TYPE'])]->(target)`이다. Aura에서는 로컬 `file:///` 대신 Aura가 접근할 수 있는 HTTPS URL 또는 Data Importer를 사용한다.

공식 문서: [동적 MERGE](https://neo4j.com/docs/cypher-manual/current/clauses/merge/), [LOAD CSV 파일 위치](https://neo4j.com/docs/getting-started/data-import/csv-files/)

### 방법 B: 터미널 일괄 적재

Neo4j Community 4.4 기준 적재 예시:

```bash
export EXP_ROOT="$(pwd)/zaije_experiment/experiments/zaije_eg_moi_20260712_v1"
export NEO4J_HOME="/path/to/neo4j-community-4.4.43"

"$NEO4J_HOME/bin/neo4j" stop
"$NEO4J_HOME/bin/neo4j-admin" import \
  --database=neo4j \
  --id-type=STRING \
  --nodes="$EXP_ROOT/neo4j/nodes.csv" \
  --relationships="$EXP_ROOT/neo4j/edges.csv" \
  --multiline-fields=true \
  --force=true
"$NEO4J_HOME/bin/neo4j" start
```

> `--force=true`는 기존 database를 덮어쓴다. 반드시 실험 전용 Neo4j에서만 사용한다.

적재 후 검증과 시각화:

```bash
NEO4J_URI=bolt://127.0.0.1:7689 \
python zaije_experiment/src/validate_eg_moi_neo4j.py

NEO4J_URI=bolt://127.0.0.1:7689 \
python zaije_experiment/src/render_eg_moi_live_query_results.py

python zaije_experiment/src/finalize_eg_moi.py
```

최종 성공 기준은 `EG_MOI_END_TO_END_PASS`이다.

## 5. 최종 결과

| 항목 | 결과 |
|---|---:|
| Excel 원문 행 | 1,366 |
| Anchor | 2,308 |
| Mention | 2,954 |
| SemanticFrame | 177 |
| ConceptCluster | 2,188 |
| Assertion | 261 |
| Neo4j 노드 | 11,053 |
| Neo4j 관계 | 19,502 |
| RDF triple | 157,272 |
| SHACL | PASS |

주요 업무 관계:

```text
PERFORMED_BY 8 / HAS_INPUT 13 / PRODUCES_OUTPUT 3
HAS_CONDITION 35 / HAS_MEASURE 1 / PRECEDES 201
```

## 6. 주요 코드와 문서

| 파일 | 용도 |
|---|---|
| [run_eg_moi.py](zaije_experiment/src/run_eg_moi.py) | Excel에서 Assertion까지 생성 |
| [export_eg_moi.py](zaije_experiment/src/export_eg_moi.py) | RDF·SHACL·Neo4j CSV export |
| [validate_eg_moi_neo4j.py](zaije_experiment/src/validate_eg_moi_neo4j.py) | Neo4j 적재량과 추적성 검증 |
| [render_eg_moi_live_query_results.py](zaije_experiment/src/render_eg_moi_live_query_results.py) | 대표 Cypher 실행과 SVG 생성 |
| [상세 방법론](zaije_experiment/experiments/zaije_eg_moi_20260712_v1/reports/detailed_EG_MOI_full_methodology.md) | 단계별 규칙과 설계 근거 |
| [10페이지 발표자료](zaije_experiment/experiments/zaije_eg_moi_20260712_v1/reports/presentation_EG_MOI_method_results_10slides.md) | 방법론과 결과 요약 |
| [최종 보고서](zaije_experiment/experiments/zaije_eg_moi_20260712_v1/reports/final_report.md) | 실험 결과와 한계 |
| [PARS-KG-RAG 실험 패키지](minjoo_PARS_KG_RAG/README.md) | 최종 방법론·실험 결과·재현 코드 |
| [범용 QA 생성기](minjoo_PARS_KG_RAG/data_creation/reusable_qa_generator/README.md) | 다른 원천 데이터에서 근거 기반 QA를 생성하는 코드와 프롬프트 |

## 7. 해석할 때 주의할 점

- `PRECEDES`는 같은 절에 등장한 문서 순서를 업무 순서로 근사했다.
- `UNRESOLVED`는 오류가 아니라 근거가 부족해 자동 확정하지 않은 후보다.
- 현재 결과는 **구조적으로는 검증됐지만 의미론적으로는 미검증**이다.
