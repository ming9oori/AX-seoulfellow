# 자이제 2·3 문서 기반 QA — 각 150문항

2026-09-30에 실제 `gpt-5.6-terra` 호출로 생성한 300문항이다.
자이제 1의 시스템 프롬프트(`jaije-qa-v1`), five-shot 5개, 청크 생성,
응답 스키마, 근거 복원, 중복 검사 규칙을 그대로 사용했다.

| 데이터셋 | 입력 시트 | 본문 열 | 검수 원문 행 | QA | 포함 절 | CSV | JSONL |
|---|---|---|---:|---:|---:|---|---|
| 자이제 2 | `종학 파트` | `사람 검수` | 1,375 | 150 | 37 | [CSV](outputs/jaije2_terra_v1/qa_dataset.csv) | [JSONL](outputs/jaije2_terra_v1/qa_dataset.jsonl) |
| 자이제 3 | `clean_sentences` | `사람 검수` | 1,254 | 150 | 47 | [CSV](outputs/jaije3_terra_v1/qa_dataset.csv) | [JSONL](outputs/jaije3_terra_v1/qa_dataset.jsonl) |

CSV는 UTF-8 BOM 형식이다. 질문, 기준답변, 근거 원문, 페이지, 장·절,
Excel 행 번호 및 생성 이력을 포함한다. 기존 자이제 1의 39개 컬럼을 유지한다.
기존 PARS-KG-RAG 210문항 실험에는 이번 300문항이 포함되지 않았다.

## 생성 및 출처 규칙

- 같은 절에서 최대 18행·5,000자를 묶고, 호출당 최대 3문항을 요청한다.
- 장·절을 순환하는 기존 청크 순서로 진행하며 150개를 채우면 중단한다.
  전체 원문이나 모든 절을 빠짐없이 평가한다는 의미는 아니다.
- 답변은 1~2문장, 근거는 1~4행이다. 페이지·장·절·근거 문장은 Excel에서 복원한다.
- `사람 검수` 셀이 비어 있으면 제외한다. `text_for_llm`로 대체하지 않는다.
  자이제 2에서 제외한 빈 검수 셀 164개는 모두 `수정 여부=1`이었다.
- 자이제 1의 five-shot은 원래 자이제 1 파일과 대조한다. 예시 행 번호를
  자이제 2·3의 행 번호로 오인해 제외하지 않으며, 예시와 같은 본문만 제외한다.
- `source_row_ids`는 `source_file`의 `sheet_name`에 있는 **물리적 Excel 행 번호**다.
  Excel의 별도 `source_row` 열 값과 구분한다.
- 질문 ID는 `JAIJE2-QA-0001` 또는 `JAIJE3-QA-0001`로 시작한다.

## 검증 결과와 검수 상태

원본 Excel을 다시 읽어 300문항의 근거 셀·메타데이터 일치, CSV/JSONL 동등성,
ID 고유성, 답변 길이와 문장 수, 같은 절 근거 사용을 검증했다.
데이터셋 내부 및 자이제 2·3 사이에 정규화 질문의 `SequenceMatcher` 유사도
0.92 이상인 쌍은 없다. 교차 중복 검사는 자이제 1을 포함하지 않는다.
자이제 2 생성 후보 중 근접 중복 1개를 제외했으며, 성공 API 호출은 각각 60회와 54회다.

모든 문항은 `review_status=pending`인 **사람 검수 전 초안**이다.
`ontology_answerable=null`이며 그래프 Gold는 아직 라벨링하지 않았다.
표본 점검에서 자이제 2의 문항 2개에 맥락·답변 범위 검토가 필요하여
[검수 메모](outputs/jaije2_terra_v1/spot_check_notes.json)를 남겼다.
자동 검증과 표본 점검은 전체 답변의 의미 정확성에 대한 전문가 승인이 아니다.

- [통합 검증 요약](outputs/jaije2_3_validation_summary.json)
- [자이제 2 생성 통계](outputs/jaije2_terra_v1/qa_dataset_report.json)
- [자이제 3 생성 통계](outputs/jaije3_terra_v1/qa_dataset_report.json)

## 보존 범위

이 폴더의 생성기 2개, 검증기, 프롬프트, few-shot은 실제 실행본을 내용 변경 없이
복사했다. `generation_manifest.json`의 코드·입력·프롬프트 해시와 데이터 체크섬을
보존했다. manifest의 절대 경로는 원래 실행 환경의 기록이며 이 저장소의 경로가 아니다.

원문 Excel, API 키, 가상환경, 원 요청/응답 로그, 전체 원문 행 사본은 포함하지 않았다.
실제 작업공간의 `AX/qa_dataset/outputs/jaije*_terra_v1/`에는 전체 감사 로그가 남아 있다.

## 새 실행 재현

Python 3.11 이상에서 다음과 같이 설치한다.

```bash
cd dataset/jaije2_3
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

원본 `자이제_1.xlsx`, `자이제_2.xlsx`, `자이제_3.xlsx`를 이 폴더의 부모인
`dataset/`에 별도로 준비한다. 자이제 1은 기존 few-shot 검증에 필요하다.
아래 명령은 `dataset/jaije2_3/`에서 실행한다.

```bash
python generate_document_qa.py \
  --input ../자이제_2.xlsx --sheet '종학 파트' --text-column '사람 검수' \
  --id-prefix JAIJE2 --output-dir reproduction/jaije2 --dry-run

python generate_document_qa.py \
  --input ../자이제_3.xlsx --sheet clean_sentences --text-column '사람 검수' \
  --id-prefix JAIJE3 --output-dir reproduction/jaije3 --dry-run
```

실제 생성은 실행 환경에 `OPENAI_API_KEY`를 설정한 뒤 `--dry-run`을 제거한다.
기본 모델은 `gpt-5.6-terra`이며 해당 계정의 모델 접근 권한이 필요하다.
다른 키 파일은 `--env-file /path/to/.env`로 지정할 수 있다.
`--resume`은 동일 입력·설정·코드의 성공 로그에서 이어서 생성한다.
이미 자료가 있는 출력 디렉터리에 새 실행을 덮어쓰지 않는다.

`validate_document_outputs.py`는 원본 Excel 2개와 전체 실행 로그가 있는
`outputs/jaije2_terra_v1/`, `outputs/jaije3_terra_v1/`를 대상으로 하는 당시 검증기다.
공개 결과만으로는 이 검증기를 완전히 실행할 수 없다.
공개 파일의 무결성은 각 `independent_validation_report.json`에 있는
CSV/JSONL SHA-256으로 확인할 수 있다.

LLM 재호출은 비결정적이므로 문항 내용의 byte-level 재생산은 보장하지 않는다.
