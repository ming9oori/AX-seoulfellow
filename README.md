# 자이제 EG-MOI 온톨로지·KG 실험

`자이제_1.xlsx` 문서만 사용해 **원문 근거까지 추적할 수 있는 온톨로지와 Neo4j 지식그래프(KG)**를 자동 생성한 실험이다.

- 최종 방법론: **EG-MOI 1.0**
- 실험 ID: `zaije_eg_moi_20260712_v1`
- 최종 판정: **`EG_MOI_END_TO_END_PASS`**
- 사람 중간 개입: `0`
- LLM 호출: `0`

> 최종 판정은 파이프라인과 구조 검증이 성공했다는 뜻이다. 생성된 개념과 관계의 의미 정확도는 추가 전문가 검증이 필요하다.

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

## 7. 해석할 때 주의할 점

- `PRECEDES`는 같은 절에 등장한 문서 순서를 업무 순서로 근사했다.
- `UNRESOLVED`는 오류가 아니라 근거가 부족해 자동 확정하지 않은 후보다.
- 현재 결과는 **구조적으로는 검증됐지만 의미론적으로는 미검증**이다.
