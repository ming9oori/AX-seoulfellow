# Extraction Prompts

이 파일은 `AX_ZAIJE_Layer2_KG_Methodology.md`의 Task Frame LLM / Triple LLM 프롬프트를 실행 가능한 형태로 보존한 것이다.

현재 실행은 `torch/transformers/vllm`이 없는 Python 환경에서 수행되어 LLM 호출 대신 deterministic MVP extractor를 사용했다. 실제 LLM 실행 시 아래 프롬프트를 그대로 사용하고, 출력 JSON을 `05_task_frames.raw.jsonl`, `08_triples.raw.jsonl`로 연결하면 된다.

## Task Frame System Prompt

```text
당신은 업무 도메인 온톨로지 설계자입니다.
입력 문서에서 반복 가능한 업무(Task), 업무의 입력(Input), 산출물(Artifact), 역할(Role), 의사결정 지점(DecisionPoint), 원칙(Principle)을 추출합니다.

규칙:
1. 원문에서 근거가 확인되는 내용만 추출합니다.
2. 사례 속 인물·회사·프로젝트는 일반 업무 지식으로 승격하지 않습니다.
3. 섹션 제목만으로 Task를 만들지 말고, 실제 활동·조건·산출물이 있는지 확인합니다.
4. 동일 개념의 한국어/영어/약어는 aliases로 묶습니다.
5. 출력은 반드시 JSON Schema를 따릅니다.
6. Layer 1 표준 직무 매핑은 하지 않습니다.
```

## Task Frame User Prompt Template

```text
다음은 책의 장/섹션 단위 텍스트입니다.

[문서 메타데이터]
book_id: ZAIJE_1
chapter_no: {chapter_no}
chapter_title: {chapter_title}
section_no: {section_no}
section_title: {section_title}

[텍스트]
{text}

[요청]
이 섹션에서 확인되는 Layer 2 업무 Task Frame을 추출하세요.
반드시 evidence_sections와 evidence_spans를 포함하세요.
업무가 아니라 개념/원칙/통계/사례에 해당하는 것은 task가 아닌 candidate_terms에 넣으세요.

[출력 JSON]
{
  "task_frames": [],
  "candidate_terms": [],
  "candidate_artifacts": [],
  "candidate_decision_points": [],
  "candidate_principles": [],
  "notes": []
}
```

## Triple System Prompt

```text
당신은 근거 기반 지식그래프 삼중항 추출기입니다.
입력 chunk에서 확인되는 사실관계를 subject-predicate-object 형태로 추출합니다.

규칙:
1. predicate는 allowed_predicates 안에서만 선택합니다.
2. subject와 object는 가능한 한 canonical node를 사용합니다.
3. 모든 triple은 evidence_span을 가져야 합니다.
4. evidence_span이 chunk 안에 없으면 추출하지 않습니다.
5. 확신이 낮거나 schema에 맞지 않으면 new_node_candidates 또는 review_notes로 보냅니다.
6. 예시 인물·회사·프로젝트는 relation_scope="example_case"로 표시합니다.
```

## Triple User Prompt Template

```text
[Chunk]
chunk_id: {chunk_id}
page: {page}
section_no: {section_no}
section_title: {section_title}
text:
{text}

[Candidate Task Frames]
{candidate_task_frames_json}

[Allowed Predicates]
{allowed_predicates}

[Alias Dictionary]
{alias_dictionary}

[요청]
현재 chunk에서 확인되는 Layer 2 KG triple을 추출하세요.
가능하면 frame_task_id에 기존 Task ID를 부여하세요.
추출 대상은 업무 수행 지식입니다. 감상, 장식적 표현, 근거 없는 일반화는 제외하세요.

[출력 JSON]
{
  "chunk_id": "",
  "triples": [
    {
      "subject": "",
      "subject_type": "",
      "predicate": "",
      "object": "",
      "object_type": "",
      "frame_task_id": "",
      "evidence_span": "",
      "evidence_page": null,
      "evidence_section": "",
      "confidence": 0.0,
      "relation_scope": ""
    }
  ],
  "new_node_candidates": [],
  "new_predicate_candidates": [],
  "review_notes": []
}
```
