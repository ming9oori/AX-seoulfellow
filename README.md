# AX Seoul Fellow: 자이제 EG-MOI 온톨로지·KG 실험

이 저장소는 `자이제_1.xlsx` 문서에서 온톨로지와 지식그래프(KG)를 생성하는 실험 코드와 결과를 보관한다.

여러 파일럿과 후속 실험 중 **현재의 최종 통합 방법론은 EG-MOI 1.0**이다.

> EG-MOI: **Evidence-Grounded Middle-Out Ontology Induction**  
> 실험 ID: `zaije_eg_moi_20260712_v1`  
> 최종 구조 검증: **`EG_MOI_END_TO_END_PASS`**

`EG_MOI_END_TO_END_PASS`는 원문 근거 보존, 스키마·그래프 생성, RDF/SHACL 검증, Neo4j 적재와 추적성 검사가 완주했다는 뜻이다. **생성된 개념과 관계의 의미 정확도가 모두 입증됐다는 뜻은 아니다.**

## 1. 최종 방법론 요약

EG-MOI는 완성된 도메인 스키마를 미리 고정하지 않는다. 다만 문서를 일관되게 읽기 위한 최소 상위 틀은 사전에 정의한다.

```text
최소 상위 유형
WorkUnit / Agent / Resource / Context / Measure / DomainConcept

표준 업무 관계
PERFORMED_BY / HAS_INPUT / PRODUCES_OUTPUT
HAS_CONDITION / HAS_MEASURE / PRECEDES
```

전체 실행 흐름은 다음과 같다.

```text
자이제_1.xlsx
  ↓
1. Evidence 구조화: 원문 행·Anchor·표 문맥 보존
  ↓
2. 후보 발견: Mention과 SemanticFrame 추출
  ↓
3. 개념 통합: 표기 변형·한영 병기·약어를 ConceptCluster로 통합
  ↓
4. 스키마 귀납: 반복 역할에서 자이제 도메인 Class를 구성
  ↓
5. 보수적 승격: Evidence·domain/range·중복·cycle 검사
  ↓
Assertion + RDF/SKOS/PROV-O/SHACL + Neo4j
```

예를 들어 원문이 다음과 같다고 하자.

```text
제안팀이 고객 요구사항을 바탕으로 제안서를 작성한다.
```

규칙은 다음 구조를 만든다.

```text
Mention: 제안팀 / 고객 요구사항 / 제안서 작성
SemanticFrame: agent=제안팀, action=작성, input=고객 요구사항, object=제안서

제안서 작성 --PERFORMED_BY----> 제안팀
제안서 작성 --HAS_INPUT-------> 고객 요구사항
제안서 작성 --PRODUCES_OUTPUT-> 제안서
```

최종 관계는 Assertion으로 표현하고, 어떤 원문과 추출 활동에서 나왔는지 함께 저장한다.

## 2. 중요 경로

| 용도 | 경로 |
|---|---|
| 최종 실험 설계서 | `자이제_최종방법론_EG-MOI.md` |
| 실행 코드 | `zaije_experiment/src/` |
| 최종 실험 폴더 | `zaije_experiment/experiments/zaije_eg_moi_20260712_v1/` |
| 상세 방법론 | `zaije_experiment/experiments/zaije_eg_moi_20260712_v1/reports/detailed_EG_MOI_full_methodology.md` |
| 10페이지 발표자료 | `zaije_experiment/experiments/zaije_eg_moi_20260712_v1/reports/presentation_EG_MOI_method_results_10slides.md` |
| Neo4j 노드 | `zaije_experiment/experiments/zaije_eg_moi_20260712_v1/neo4j/nodes.csv` |
| Neo4j 관계 | `zaije_experiment/experiments/zaije_eg_moi_20260712_v1/neo4j/edges.csv` |
| 최종 판정 | `zaije_experiment/experiments/zaije_eg_moi_20260712_v1/evaluation/gate_summary.json` |

## 3. 실행 환경

현재 실험에서 확인한 환경은 다음과 같다.

- Linux
- Python `3.13.13`
- `neo4j` Python driver `5.28.4`
- `pyshacl` `0.30.1`
- `rdflib` `7.6.0`
- Neo4j Community `4.4.43`
- Java는 사용하는 Neo4j 배포판의 요구 버전을 준비한다.

코드는 Python 3.10 이상 문법을 사용한다. 아래 명령은 **저장소 루트**에서 실행한다.

### 3.1 저장소 받기

```bash
git clone --recurse-submodules https://github.com/ming9oori/AX-seoulfellow.git
cd AX-seoulfellow
```

이미 clone한 저장소라면 서브모듈만 초기화한다.

```bash
git submodule update --init --recursive
```

### 3.2 Python 가상환경

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r \
  zaije_experiment/experiments/zaije_eg_moi_20260712_v1/requirements-eg-moi.txt
```

API key는 필요하지 않다. 최종 EG-MOI 실험은 LLM 호출 없이 규칙 기반으로 실행됐다.

### 3.3 입력 파일 확인

코드는 다음 파일을 고정 입력으로 사용한다.

```text
handoff-hanyang/수주제안/자이제_1.xlsx
```

실행 전에 파일을 확인한다.

```bash
test -f 'handoff-hanyang/수주제안/자이제_1.xlsx'
```

종료 코드가 `0`이면 파일이 존재한다.

## 4. 빠른 실행: Neo4j 전까지

다음 두 명령이 Excel에서 그래프, RDF, SHACL, Neo4j CSV까지 생성한다.

```bash
python zaije_experiment/src/run_eg_moi.py
python zaije_experiment/src/export_eg_moi.py
```

첫 번째 명령의 성공 판정은 다음이다.

```text
"overall_status": "EG_MOI_PIPELINE_PASS"
```

두 번째 명령의 성공 판정은 다음이다.

```text
"pass": true
"shacl_conforms": true
```

이 두 명령은 아래 최종 실험 폴더의 동일 이름 산출물을 다시 쓴다.

```text
zaije_experiment/experiments/zaije_eg_moi_20260712_v1/
```

## 5. 단계별 실행 코드

### 5.1 Stage 1~5: Evidence에서 Assertion까지

```bash
python zaije_experiment/src/run_eg_moi.py
```

실행 코드: `zaije_experiment/src/run_eg_moi.py`

이 스크립트가 수행하는 작업은 다음과 같다.

1. Excel 1,366행을 읽고 stable ID를 부여한다.
2. 문장·목록·표 구조를 Anchor와 ContextSpan으로 나눈다.
3. 표 header, 한영 병기, 약어, 조건, 수량, 한국어 주체·목적어·행위 규칙으로 Mention과 SemanticFrame을 만든다.
4. 정규화 문자열과 2·3-gram cosine을 사용해 ConceptCluster를 만든다.
5. 반복 역할에서 구체적인 자이제 스키마 8개를 귀납한다.
6. Evidence와 domain/range를 통과한 관계를 Assertion으로 승격한다.
7. 불확실한 후보는 강제 확정하지 않고 `UNRESOLVED`에 남긴다.

주요 산출물:

```text
stage1_evidence/source_rows.jsonl
stage1_evidence/evidence_units.jsonl
stage2_discovery/mentions.jsonl
stage2_discovery/semantic_frames.jsonl
stage2_discovery/surface_relations.jsonl
stage3_consolidation/concept_clusters.jsonl
stage3_consolidation/merge_decisions.jsonl
stage4_schema/induced_schema.json
stage5_promotion/promotion_decisions.jsonl
stage5_promotion/unresolved.jsonl
graph/nodes.jsonl
graph/edges.jsonl
evaluation/structural_metrics.json
```

### 5.2 RDF·SHACL·Neo4j CSV export

```bash
python zaije_experiment/src/export_eg_moi.py
```

실행 코드: `zaije_experiment/src/export_eg_moi.py`

이 스크립트는 `graph/nodes.jsonl`과 `graph/edges.jsonl`을 읽어 다음을 생성한다.

```text
rdf/canonical.ttl             # 전체 RDF
rdf/concepts.skos.ttl         # SKOS 개념 체계
rdf/provenance.prov.ttl       # PROV-O 추적 정보
rdf/shapes.ttl                # SHACL 제약
rdf/validation_report.txt     # SHACL 검증 결과
neo4j/nodes.csv               # Neo4j 노드
neo4j/edges.csv               # Neo4j 관계
visualization/screenshots/    # 정적 SVG 그래프
evaluation/export_metrics.json
```

## 6. Neo4j 오프라인 적재

### 6.1 주의사항

`neo4j-admin import` 명령은 Neo4j가 중지된 상태에서 실행해야 한다.

> **주의:** 아래의 `--force=true`는 대상 Neo4j 데이터베이스를 삭제하고 다시 만든다. 기존 데이터가 있는 Neo4j에서 실행하지 말고, EG-MOI 전용 Neo4j 설치 폴더를 사용한다.

아래는 실험에서 검증한 Neo4j Community 4.4 명령 형식이다.

```bash
export REPO_ROOT="$(pwd)"
export EXP_ROOT="$REPO_ROOT/zaije_experiment/experiments/zaije_eg_moi_20260712_v1"
export NEO4J_HOME="/absolute/path/to/neo4j-community-4.4.43"

"$NEO4J_HOME/bin/neo4j" stop

"$NEO4J_HOME/bin/neo4j-admin" import \
  --database=neo4j \
  --id-type=STRING \
  --nodes="$EXP_ROOT/neo4j/nodes.csv" \
  --relationships="$EXP_ROOT/neo4j/edges.csv" \
  --multiline-fields=true \
  --force=true \
  --report-file="$EXP_ROOT/neo4j/import.report"
```

Neo4j 5.x는 `neo4j-admin database import full` 형식을 사용하므로, 사용 버전의 `neo4j-admin ... --help`를 확인한다.

### 6.2 로컬 검증용 서버 설정

기본 Neo4j와 포트가 겹치지 않게 `NEO4J_HOME/conf/neo4j.conf`에 다음을 설정할 수 있다.

```properties
dbms.default_listen_address=127.0.0.1
dbms.connector.bolt.listen_address=:7689
dbms.connector.http.listen_address=:7476
dbms.security.auth_enabled=false
```

`auth_enabled=false`는 **로컬 파일럿 검증 전용**이다. 공유 서버나 외부에 열린 환경에서는 사용하지 않는다. 현재 검증 스크립트는 인증이 비활성화된 로컬 Neo4j를 기준으로 한다.

서버를 시작한다.

```bash
"$NEO4J_HOME/bin/neo4j" start
```

실험에서 사용한 접속 주소:

```text
Neo4j Browser: http://127.0.0.1:7476
Bolt:          bolt://127.0.0.1:7689
Database:      neo4j
```

## 7. Neo4j 적재 검증과 시각화

### 7.1 적재 수량·추적성 검증

```bash
NEO4J_URI=bolt://127.0.0.1:7689 \
python zaije_experiment/src/validate_eg_moi_neo4j.py
```

실행 코드: `zaije_experiment/src/validate_eg_moi_neo4j.py`

다음을 검사한다.

- 노드 `11,053 / 11,053`
- 관계 `19,502 / 19,502`
- Assertion의 Evidence 추적 비율 `1.0`
- Assertion의 ExtractionActivity 추적 비율 `1.0`
- 잘못된 관계 endpoint `0`
- 스키마·업무·개념 통합·근거·생성 이력 view가 모두 비어 있지 않음

성공하면 `neo4j/runtime_validation.json`의 `pass`가 `true`가 된다.

### 7.2 대표 Cypher 5개 실행과 SVG 생성

```bash
NEO4J_URI=bolt://127.0.0.1:7689 \
python zaije_experiment/src/render_eg_moi_live_query_results.py
```

실행 코드: `zaije_experiment/src/render_eg_moi_live_query_results.py`

이 스크립트는 **실제 Neo4j에 접속해 Cypher를 실행한 후** 원형 노드 그래프 SVG 5개와 합본 1개를 만든다.

```text
visualization/live_query_results/00_representative_5_live_results.svg
visualization/live_query_results/01_schema.svg
visualization/live_query_results/02_input_output.svg
visualization/live_query_results/03_performer.svg
visualization/live_query_results/04_sequence.svg
visualization/live_query_results/05_evidence.svg
```

예상되는 전체 결과는 다음과 같다.

```text
귀납 스키마:      8
입력·산출물:       16
업무 수행자:        8
업무 순서:        201
Assertion 원문: 445
```

## 8. 최종 판정과 해시 검증

Neo4j 검증과 시각화까지 끝난 후 최종 보고서, gate, 보안 검사, 산출물 SHA-256 목록을 다시 만든다.

```bash
python zaije_experiment/src/finalize_eg_moi.py
```

실행 코드: `zaije_experiment/src/finalize_eg_moi.py`

성공 출력:

```text
"overall_status": "EG_MOI_END_TO_END_PASS"
```

해시를 검증한다.

```bash
cd zaije_experiment/experiments/zaije_eg_moi_20260712_v1
sha256sum -c reports/artifact_sha256.txt
cd ../../../..
```

모든 항목이 `OK`로 나와야 한다.

## 9. 처음부터 끝까지 실행하는 순서

아래가 최종 전체 실행 순서다. `neo4j-admin import`만 Neo4j가 중지된 상태에서 실행한다.

```bash
# 1. Python 결과 생성
python zaije_experiment/src/run_eg_moi.py
python zaije_experiment/src/export_eg_moi.py

# 2. Neo4j 중지 후 CSV 적재
export REPO_ROOT="$(pwd)"
export EXP_ROOT="$REPO_ROOT/zaije_experiment/experiments/zaije_eg_moi_20260712_v1"
export NEO4J_HOME="/absolute/path/to/neo4j-community-4.4.43"
"$NEO4J_HOME/bin/neo4j" stop
"$NEO4J_HOME/bin/neo4j-admin" import \
  --database=neo4j \
  --id-type=STRING \
  --nodes="$EXP_ROOT/neo4j/nodes.csv" \
  --relationships="$EXP_ROOT/neo4j/edges.csv" \
  --multiline-fields=true \
  --force=true \
  --report-file="$EXP_ROOT/neo4j/import.report"

# 3. Neo4j 시작 후 검증·시각화
"$NEO4J_HOME/bin/neo4j" start
NEO4J_URI=bolt://127.0.0.1:7689 python zaije_experiment/src/validate_eg_moi_neo4j.py
NEO4J_URI=bolt://127.0.0.1:7689 python zaije_experiment/src/render_eg_moi_live_query_results.py

# 4. 최종 gate·보고서·해시 생성
python zaije_experiment/src/finalize_eg_moi.py

# 5. 산출물 무결성 확인
(cd "$EXP_ROOT" && sha256sum -c reports/artifact_sha256.txt)
```

## 10. 실행 코드와 역할

| 순서 | 코드 | 역할 |
|---:|---|---|
| 1 | `zaije_experiment/src/run_eg_moi.py` | Excel → Evidence → Mention/Frame → Cluster → 스키마 → Assertion |
| 2 | `zaije_experiment/src/export_eg_moi.py` | graph JSONL → RDF·SKOS·PROV-O·SHACL·Neo4j CSV·정적 SVG |
| 3 | `zaije_experiment/src/validate_eg_moi_neo4j.py` | Neo4j 적재량·제약·근거 추적성 검사 |
| 4 | `zaije_experiment/src/render_eg_moi_live_query_results.py` | Neo4j 대표 Cypher 5개 실행·SVG 생성 |
| 5 | `zaije_experiment/src/finalize_eg_moi.py` | 최종 gate·보안 검사·보고서·SHA-256 manifest 생성 |

보조 모듈:

- `zaije_experiment/src/r2_blre.py`: Excel OOXML 구조 읽기와 기초 전처리
- `zaije_experiment/src/r3_apre.py`: Anchor·ContextSpan 분리와 offset 검증

## 11. 정상 재실행 기준값

| 항목 | 기준값 |
|---|---:|
| Excel 원문 행 | 1,366 |
| Anchor | 2,308 |
| ContextSpan | 1,718 |
| Mention | 2,954 |
| SemanticFrame | 177 |
| ConceptCluster | 2,188 |
| VALIDATED Cluster | 818 |
| UNRESOLVED Cluster | 1,370 |
| Assertion | 261 |
| Neo4j 노드 | 11,053 |
| Neo4j 관계 | 19,502 |
| RDF triple | 157,272 |
| SHACL | PASS |

Operational 관계는 다음과 같다.

| 관계 | 수 |
|---|---:|
| `PERFORMED_BY` | 8 |
| `HAS_INPUT` | 13 |
| `PRODUCES_OUTPUT` | 3 |
| `HAS_CONDITION` | 35 |
| `HAS_MEASURE` | 1 |
| `PRECEDES` | 201 |

## 12. 대표 Neo4j 확인 질의

### 12.1 귀납 스키마 8개

```cypher
MATCH p=(:SchemaClass)-[:SUBCLASS_OF]->(:MetaClass)
RETURN p
LIMIT 50;
```

### 12.2 업무의 입력·산출물 16개

```cypher
MATCH p=(:ConceptCluster)-[r]->(:ConceptCluster)
WHERE type(r) IN ['HAS_INPUT', 'PRODUCES_OUTPUT']
RETURN p
LIMIT 50;
```

### 12.3 업무 수행자 8개

```cypher
MATCH p=(:ConceptCluster)-[:PERFORMED_BY]->(:ConceptCluster)
RETURN p
LIMIT 30;
```

### 12.4 문서 순서 기반 업무 순서 201개

```cypher
MATCH p=(:ConceptCluster)-[:PRECEDES]->(:ConceptCluster)
RETURN p
LIMIT 50;
```

### 12.5 Assertion의 원문 Evidence 445개

```cypher
MATCH p=(:Assertion)-[:DERIVED_FROM]->(:EvidenceUnit)
RETURN p
LIMIT 50;
```

대표 질의 파일:

```text
zaije_experiment/experiments/zaije_eg_moi_20260712_v1/
visualization/queries/representative_5_queries.cypher
```

## 13. 자주 발생하는 문제

### `FileNotFoundError: .../자이제_1.xlsx`

- 저장소 루트에서 실행했는지 확인한다.
- `handoff-hanyang/수주제안/자이제_1.xlsx`가 존재하는지 확인한다.
- 파일명이 같아 보여도 Unicode 조합 형식이 다를 수 있으므로 저장소에 포함된 원본 경로를 사용한다.

### `ModuleNotFoundError: pyshacl` 또는 `neo4j`

```bash
source .venv/bin/activate
python -m pip install -r \
  zaije_experiment/experiments/zaije_eg_moi_20260712_v1/requirements-eg-moi.txt
```

### Neo4j `Connection refused`

- Neo4j가 실행 중인지 확인한다.
- `NEO4J_URI`의 Bolt 포트와 `neo4j.conf`의 Bolt 포트가 같은지 확인한다.
- `http://127.0.0.1:7476`은 Browser 주소이고, Python driver는 `bolt://127.0.0.1:7689`를 사용한다.

### `Label does not exist` 또는 `Relationship type does not exist`

대부분 다른 Neo4j 서버나 빈 데이터베이스에 접속한 경우다.

```cypher
MATCH (n) RETURN count(n);
MATCH ()-[r]->() RETURN count(r);
```

적재가 정상이라면 각각 `11053`, `19502`가 나와야 한다. Neo4j Browser를 기본 `7687`이 아닌 실험 서버 `7689`에 다시 연결한다.

### Neo4j import가 기존 database 오류로 중단됨

- Neo4j를 먼저 중지한다.
- 기존 DB 삭제가 허용되는 EG-MOI 전용 설치인지 확인한다.
- 전용 설치에서만 `--force=true`로 다시 실행한다.

### `sha256sum -c` 실패

산출물이 최종 판정 이후 변경됐다는 뜻이다. Neo4j 검증과 시각화까지 완료한 뒤 다시 실행한다.

```bash
python zaije_experiment/src/finalize_eg_moi.py
```

## 14. 결과 해석 주의

1. `EG_MOI_END_TO_END_PASS`는 파이프라인과 구조 검증의 성공이다.
2. 정답 Gold와 전문가 평가를 사용한 의미 정확도는 아직 측정하지 않았다.
3. `PRECEDES`는 같은 절 안의 문서 등장 순서를 업무 순서의 근사치로 사용하므로 후속 검증이 필요하다.
4. `UNRESOLVED`는 오류로 판단한 것이 아니라, 근거가 부족해 자동 확정하지 않은 후보다.
5. 현재 결과는 **구조적으로 검증됐지만 의미론적으로는 미검증**인 파일럿 결과다.

## 15. 최종 문서

- 상세 방법론: `zaije_experiment/experiments/zaije_eg_moi_20260712_v1/reports/detailed_EG_MOI_full_methodology.md`
- 최종 보고서: `zaije_experiment/experiments/zaije_eg_moi_20260712_v1/reports/final_report.md`
- 10페이지 발표자료: `zaije_experiment/experiments/zaije_eg_moi_20260712_v1/reports/presentation_EG_MOI_method_results_10slides.md`
- Neo4j 실행 시각화 보고서: `zaije_experiment/experiments/zaije_eg_moi_20260712_v1/reports/neo4j_representative_5_live_visualization_results.md`
