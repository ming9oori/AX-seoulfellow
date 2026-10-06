# 재현 범위와 최종 실행 계약

최종 방법은 `PARS_REFINED / CE_TOP5`입니다. 이 폴더는 최종 알고리즘 코드·설정, 발표 자료, 완료된 집계 결과와 실제 한 문항의 오프라인 재현 자료를 묶었습니다.

## 재현 가능한 범위

| 작업 | 포함된 입력 | 추가 조건 |
|---|---|---|
| 후보 합집합·CE 순위 재현 | 전체 1,525개 ID의 R·M, 70개 CE 로짓 | NumPy |
| 실제 질문 Aspect 재추출 | 원 질문·규칙·기대 Aspect | Kiwi 0.23.2 |
| 단위·계약 테스트 | 합성 fixture·mock API | 프로젝트 의존 패키지 |
| 새로운 질문의 전체 실행 | 코드·프롬프트·JSON schema | 별도 snapshot·모델 가중치·API |
| 전체 178문항 품질 재평가 | 집계 결과만 포함 | 전체 QA·Gold·참조답·snapshot·모델 환경 필요 |

저장된 답변을 출력하는 것은 새 답변 생성 실험이 아닙니다. 한 문항 재현 성공은 전체 평가를 새로 수행했다는 뜻이 아닙니다. 원문 자료는 사용 권한을 확인한 뒤 로컬 `assets/`에 준비합니다.

## 그래프 snapshot 형식

`--snapshot`에는 JSON 객체를 전달합니다. 기존 `src/kg_rag/snapshot.py`의 export 구조와 `cover_index.py`·`retrieval.py`의 읽기 계약을 따릅니다.

- `evidence_spans`: `properties.id`, `properties.name` 원문, 출처 메타데이터와 `sections`.
- `pcf_processes`, `pcf_child_of`: PCF 노드 및 `child_id`·`parent_id` 계층.
- `taskframes`, `pcf_mappings`: TaskFrame 노드와 업무 분류 매핑.
- `facts`, `taskmentions`: 속성, 직접 `evidence_ids`, TaskFrame 연결.

최종 방법은 원문 1,525개·직접 뷰 5,968개를 사용한 기록입니다. 다른 snapshot에 실행하면 별도 실험이며 기존 성능과 동일하다고 보장하지 않습니다. 불완전한 최소 JSON을 원래 실험 데이터로 취급하지 않습니다.

## 설정 구분

`config/final_method.json`이 새 질문 진입점의 설정입니다. `final_method`는 질문 후보 40개, Aspect별 후보 20개, 최종 Top5, 상한 없는 Aspect, 원문 7,000자, `CE_TOP5`를 명시합니다. 설정을 바꾸어 다른 방법이 되면 별도 실험으로 기록해야 합니다.

`experiment_ablation.yaml`과 `experiment_pars_cover_v1.yaml`은 원본 코드·계약 테스트 호환과 연구 계보를 위해 보존했습니다. 그 안의 `legacy_run` 등 외부 경로는 이 패키지의 실행 입력으로 사용하지 않습니다. 이전 Cover의 lambda 0.5나 예전 Aspect 상한을 최종 PARS-RF 설정으로 읽지 마세요.

## 측정 및 출판 자료

- `results/main_table.csv`: 요청한 메인 11조건.
- `results/method_catalog_20261002.json`: 전체 20조건, 조건 의미, 시간·비용.
- `results/gap_completion_20261002.json`: 집계 원본.
- `examples/real_question.json`: 10월 1일의 실제 검색·생성·검증 기록.
- `examples/real_question_scores.npz`: 당시 후보 선택 점수. `allow_pickle=False`로 읽습니다.

사례의 context에서 호스트의 절대 경로만 파일명으로 줄였습니다. 사례에 보존한 과거 `context_sha256`은 원래 context에 대한 해시이며 경로를 줄인 현재 문자열의 해시가 아닙니다. 원래 소스 파일 해시는 `release_manifest.json`에 별도로 기록했습니다.

## 검증과 제한

오프라인 재현과 포함된 테스트는 패키지 안의 코드만 로드하여 실행합니다. GPU 모델 재추론·새 유료 API 실행·전체 데이터셋 재평가는 이 릴리스 제작 범위에 포함되지 않습니다. 새 질문 CLI는 기존 런타임을 연결한 진입점이며 API usage를 기록하고 인용을 검증합니다.

API 키, `.env`, SQLite 캐시, 모델 가중치, 원본 전체 자료, 관련 없는 실험 변경은 업로드 대상에서 제외했습니다. 사용한 모델·원문·분류 체계의 이용 조건은 각각 적용됩니다. 이 패키지의 배포가 원문 전체의 재배포 권한을 부여하지는 않습니다.
