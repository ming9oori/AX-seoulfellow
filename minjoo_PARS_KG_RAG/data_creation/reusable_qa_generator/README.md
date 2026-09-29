# 범용 근거 추적형 QA 데이터셋 생성기

CSV, JSONL, JSON 또는 XLSX 원천 데이터에서 질문·기준답·근거 ID가 연결된 QA
데이터셋을 생성한다. 특정 문서의 열 이름, 장·절 구조, 온톨로지 또는 Neo4j에 의존하지
않도록 입력 스키마와 프롬프트를 설정 파일로 분리했다.

이 폴더는 새로운 source 데이터에 사용할 **권장 범용판**이다. 실제 자이제 150문항을
만들었던 원본 코드는 변경하지 않고 [`../source_qa/`](../source_qa/)에 계보 보존용으로
남겨 두었다.

## 1. 남긴 핵심 흐름

```text
source file
  -> 설정된 text/id/group/metadata 열 읽기
  -> 같은 group 안에서만 결정적 chunk 생성
  -> system prompt + 선택적 few-shot + SOURCE_RECORDS
  -> OpenAI Responses API Structured Outputs
  -> question/answer/source_ids/type/difficulty 수신
  -> source_ids로 원문 evidence와 metadata를 코드가 복원
  -> 형식·근거 범위·중복 검사
  -> JSONL + CSV + manifest + 재개 로그
```

범용화 과정에서 자이제 전용 Excel 헤더, 특정 장 순서, KG Gold 필드, Neo4j 정렬,
고정된 한국어 업무 유형은 핵심 생성기에서 제거했다. 그래프 Gold 연결은 QA 생성 후
별도 annotation 단계에서 수행해야 한다.

## 2. 파일 구성

```text
reusable_qa_generator/
├── generate.py                         # 단일 실행 파일
├── config.example.json                 # 모든 입력·생성 설정 예시
├── requirements.txt
├── .env.example
├── .gitignore                          # 키·가상환경·생성 결과 제외
├── prompts/
│   ├── system_prompt.txt               # 변수 치환형 범용 프롬프트
│   └── few_shot_examples.example.json  # 선택적 few-shot 형식 예시
└── examples/
    └── source.csv                       # API 없이 점검 가능한 최소 예제
```

실제 운영에 필요한 파일은 `generate.py`, 설정 JSON, 시스템 프롬프트, source 파일이다.
few-shot은 선택 사항이다.

## 3. 빠른 시작

Python 3.11 이상을 권장한다.

```bash
cd /path/to/minjoo_PARS_KG_RAG/data_creation/reusable_qa_generator

python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

먼저 API를 호출하지 않는 예제 점검을 실행한다.

```bash
python generate.py --config config.example.json --dry-run
```

예상 결과는 source 6행, group 3개, chunk 3개다. 이후 키를 환경변수로 주입한다.

```bash
export OPENAI_API_KEY="<YOUR_OPENAI_API_KEY>"
```

또는 `.env.example`을 `.env`로 복사한 뒤 실제 키를 넣을 수 있다. `.env`는 Git에
커밋하지 않는다.

실제 생성:

```bash
python generate.py \
  --config config.example.json \
  --output-dir outputs/example_run
```

중단된 실행 재개:

```bash
python generate.py \
  --config config.example.json \
  --output-dir outputs/example_run \
  --resume
```

재개 시 source, prompt, few-shot, 모델 또는 생성 설정이 달라지면 fingerprint 검사가
실행을 중단한다. 설정을 바꾼 실험은 새 출력 디렉터리를 사용한다.
새 실행의 출력 디렉터리는 비어 있어야 하며, 기존 결과를 자동으로 덮어쓰지 않는다.

## 4. 새로운 source 데이터 준비

### 4.1 권장 단위

한 행은 답의 근거로 인용할 수 있는 최소 단위여야 한다. 보통 한 문장, 표의 한 행,
짧은 문단이 적합하다. 문서 전체를 한 행에 넣지 않는다.

권장 열은 다음과 같다.

| 역할 | 예시 | 필수 여부 |
|---|---|---|
| 안정적인 근거 ID | `source_id` | 권장 |
| 모델에 전달할 원문 | `text` | 필수 |
| 문맥 혼합을 막는 묶음 | `document_id`, `section` | 권장 |
| 추적용 정보 | `page`, `title`, `url`, `date` | 선택 |

예시 CSV:

```csv
source_id,document_id,section,page,text
DOC1-001,manual-v1,계정 관리,1,신규 계정은 책임자 승인 후 생성한다.
DOC1-002,manual-v1,계정 관리,1,미사용 계정은 확인 후 비활성화한다.
```

### 4.2 지원 형식

- CSV: 첫 행을 헤더로 사용하며 UTF-8 또는 UTF-8-SIG를 권장한다.
- XLSX: 첫 행을 헤더로 사용한다. `sheet`가 `null`이면 활성 시트를 읽는다.
- JSON: 최상위 값이 객체 배열이어야 한다.
- JSONL: 한 줄에 객체 하나를 둔다.

중첩 JSON metadata는 문자열화해 보존한다. `text`가 빈 행은 제외한다. 설정된 group 열이
비어 있거나 ID가 중복되면 즉시 실패한다.

### 4.3 group 열이 중요한 이유

`group_columns`가 같은 행끼리만 한 chunk에 들어간다. 서로 다른 문서나 절의 문장이
우연히 결합돼 잘못된 답을 만드는 것을 막으려면 보통 다음처럼 설정한다.

```json
"group_columns": ["document_id", "section"]
```

문서에 절 구분이 없으면 `document_id`만 사용한다. 모든 행을 함께 묶으려는 경우에만 빈
배열 `[]`을 사용한다.

## 5. 설정 파일

모든 상대경로는 설정 JSON이 위치한 디렉터리를 기준으로 해석한다.

### 5.1 `dataset`

```json
"dataset": {
  "name": "my_manual_qa",
  "language": "Korean",
  "domain": "장비 운영 매뉴얼",
  "qa_id_prefix": "MANUAL-QA"
}
```

- `name`: manifest와 기본 출력 경로에 쓰는 데이터셋 이름
- `language`: 질문·답변 출력 언어
- `domain`: 프롬프트에 제공할 분야 설명
- `qa_id_prefix`: 최종 ID 접두사. 예: `MANUAL-QA-0001`

### 5.2 `input`

```json
"input": {
  "path": "data/manual.csv",
  "format": "auto",
  "sheet": null,
  "id_column": "source_id",
  "text_column": "text",
  "group_columns": ["document_id", "section"],
  "metadata_columns": ["document_id", "section", "page"]
}
```

- `format`: `auto`, `csv`, `jsonl`, `json`, `xlsx`
- `id_column`: `null`이면 `ROW-000001` 형식의 ID를 만들지만, 원본 수정 후에도 안정적인
  추적을 위해 실제 ID 열을 두는 것이 좋다.
- `text_column`: 모델과 최종 Evidence에 전달할 원문 열
- `group_columns`: chunk 경계를 결정하는 열
- `metadata_columns`: 결과의 `evidence_metadata`에 복사할 열

group 열은 metadata에 자동 포함되므로 중복 지정해도 한 번만 저장된다.

### 5.3 `prompt`

```json
"prompt": {
  "system_prompt_path": "prompts/system_prompt.txt",
  "few_shots_path": null,
  "version": "my-manual-qa-v1"
}
```

처음에는 `few_shots_path: null`로 소규모 파일럿을 실행한다. 품질 문제가 반복될 때만
source와 정답이 정확히 대응되는 도메인별 예시를 추가한다.

### 5.4 `generation`

```json
"generation": {
  "model": "gpt-4o-mini-2024-07-18",
  "target_size": 100,
  "qas_per_chunk": 3,
  "max_source_rows": 18,
  "max_source_chars": 5000,
  "max_source_ids_per_qa": 4,
  "max_answer_sentences": 2,
  "duplicate_threshold": 0.92,
  "max_output_tokens": 1600,
  "max_retries": 2,
  "retry_base_seconds": 2.0,
  "timeout_seconds": 120.0,
  "question_types": ["fact", "definition", "reason", "method"],
  "difficulties": ["easy", "medium", "hard"]
}
```

`question_types`와 `difficulties`는 source 특성에 맞게 바꿀 수 있으며 Structured Outputs
스키마의 enum에도 그대로 반영된다. `model`은 Structured Outputs를 지원하는 모델을
사용해야 한다. 명령행의 `--model`과 `--target-size`로 두 값만 임시 재정의할 수 있다.

```bash
python generate.py --config my_config.json \
  --model gpt-4o-mini-2024-07-18 \
  --target-size 20 \
  --output-dir outputs/pilot
```

## 6. 프롬프트 수정

기본 `system_prompt.txt`는 다음 placeholder를 지원한다.

- `{{DATASET_NAME}}`
- `{{LANGUAGE}}`
- `{{DOMAIN}}`
- `{{MAX_SOURCE_IDS}}`
- `{{MAX_ANSWER_SENTENCES}}`
- `{{QUESTION_TYPES}}`
- `{{DIFFICULTIES}}`

미해결 placeholder가 남으면 API 호출 전에 실패한다. source 본문에 포함된 지시문을 모델이
따르지 않도록 기본 프롬프트에는 prompt-injection 방어 문구가 들어 있다.

모델에게 생성하도록 맡기는 필드는 다음 다섯 개뿐이다.

```text
question
answer
source_ids
question_type
difficulty
```

Evidence 원문, metadata, chunk ID, 모델, 응답 ID와 생성 시각은 모델 출력이 아니라
코드가 원본과 실행 기록에서 채운다.

## 7. 선택적 few-shot

`few_shot_examples.example.json`을 복사해 실제 도메인에 맞는 파일을 만들고 설정에 연결한다.

```json
"few_shots_path": "prompts/my_few_shots.json"
```

각 예시는 다음 구조를 사용한다.

```json
{
  "name": "single-source fact",
  "source_records": [
    {
      "source_id": "EX-001",
      "text": "근거 문장",
      "metadata": {"section": "예시 절"}
    }
  ],
  "expected": {
    "question": "질문?",
    "answer": "근거에 따른 답변입니다.",
    "source_ids": ["EX-001"],
    "question_type": "fact",
    "difficulty": "easy"
  }
}
```

few-shot은 실제 평가 source와 분리하는 편이 안전하다. 질문 유형과 난이도는 설정의 허용
목록 안에 있어야 하며, 선택한 source ID는 예시 안의 source record를 가리켜야 한다.

## 8. 자동 검증

생성 후보는 다음을 모두 통과해야 한다.

- 질문 길이가 5~500자이고 `?` 또는 `？`로 끝남
- 답변이 비어 있지 않고 설정한 최대 문장 수 이하
- `source_ids`가 1개 이상이고 설정된 최대 개수 이하
- 모든 source ID가 현재 chunk 안에 존재
- 질문 유형과 난이도가 설정의 허용 목록에 속함
- normalized exact duplicate가 아님
- 기존 질문과 `SequenceMatcher` 유사도가 임계값 이상이 아님

source 행이 `max_source_chars`보다 길면 자동 절단하지 않고 실패한다. 근거를 조용히
손실시키지 않기 위한 정책이므로, 원천 단위를 나누거나 명시적으로 한도를 높인다.

## 9. 출력

| 파일 | 내용 |
|---|---|
| `qa_dataset.jsonl` | 배열·객체 타입이 보존된 기준 데이터 |
| `qa_dataset.csv` | 검수용 CSV; 배열·객체는 JSON 문자열 |
| `manifest.json` | 입력·프롬프트·few-shot 해시, 설정, 분포, 상태, fingerprint |
| `generation_log.jsonl` | chunk별 source ID, 응답 ID, 채택·탈락·오류와 재개 상태 |

주요 QA 필드는 다음과 같다.

| 필드 | 생성 주체 |
|---|---|
| `question`, `answer`, `source_ids`, `question_type`, `difficulty` | LLM + 코드 검증 |
| `evidence_text`, `evidence_metadata`, `group_key` | source에서 코드로 복원 |
| `qa_id` | 채택 순서에 따라 코드가 안정적으로 부여 |
| `generation_model`, `generation_response_id`, `prompt_version` | 실행 계보 |
| `review_status` | 항상 `pending`으로 시작 |

API 오류가 난 chunk는 로그에 `error`로 남고 다음 chunk로 진행한다. `--resume`을 사용하면
성공한 chunk는 건너뛰고 실패한 chunk를 다시 시도한다.

## 10. 다른 source에 적용하는 권장 절차

1. 원문을 최소 근거 단위로 정리하고 안정적인 source ID를 부여한다.
2. 서로 섞이면 안 되는 문서·절을 group 열로 정한다.
3. `config.example.json`을 복사해 열 이름, 언어, 도메인, 모델을 바꾼다.
4. `--dry-run`으로 행·group·chunk 수를 확인한다.
5. `--target-size 10` 정도의 별도 출력 폴더에서 파일럿을 생성한다.
6. 질문 자연스러움, 답변의 원문 지지, source ID 최소성을 사람이 검수한다.
7. 필요할 때만 프롬프트나 few-shot을 수정하고 `prompt.version`을 올린다.
8. 설정을 동결한 후 새 출력 폴더에서 본 생성을 수행한다.
9. 최종 CSV/JSONL과 manifest를 함께 보존한다.

## 11. 사용 범위와 한계

- 이 생성기는 source에 직접 답이 있는 positive QA를 만든다. 답변 불가 질문이나 hard
  negative는 별도 설계·사람 검수가 필요하다.
- 자동 검증은 형식과 근거 ID 범위를 확인할 뿐, 답변의 의미적 정확성을 보증하지 않는다.
- `review_status=pending`을 사람 승인 없이 `approved`로 바꾸지 않는다.
- LLM 호출은 비결정적일 수 있으므로 같은 설정으로도 byte-level 동일 결과가 보장되지 않는다.
- 출력 데이터셋을 모델·검색기 튜닝에 사용했다면 같은 문항을 독립 test로 주장하지 않는다.
- 개인정보·기밀 source를 외부 API에 보내기 전에 조직 정책과 데이터 처리 조건을 확인한다.

## 12. API 구현 기준

코드는 OpenAI Responses API의 `responses.parse()`와 Pydantic 모델을 사용한다. JSON mode가
아니라 schema adherence를 제공하는 Structured Outputs 방식이다. 관련 최신 지원 모델과
제약은 [OpenAI Structured Outputs 공식 문서](https://developers.openai.com/api/docs/guides/structured-outputs)를 확인한다.
