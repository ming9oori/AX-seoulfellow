# OpenAI LLM Extraction Prompts

Model: `gpt-4o-mini`

이 파일은 이번 OpenAI API 실행에서 사용한 실제 system prompt와 user prompt 구조를 보존한다.
실제 chunk별 user prompt는 원문 길이 때문에 `19_openai_task_frame_links.raw.jsonl`, `20_openai_triples.raw.jsonl`에는 저장하지 않고,
아래 템플릿과 각 chunk/evidence/candidate node JSON으로 재현한다.

## Task Frame System Prompt

```text
당신은 업무 도메인 온톨로지 설계자입니다.
입력 문서에서 확인되는 내용을 기존 Layer 2 canonical Task catalog에 연결합니다.

규칙:
1. 원문 evidence_id가 있는 내용만 연결합니다.
2. 새 task를 남발하지 말고, 기존 task로 설명 가능한 경우 task_frame_links에 넣습니다.
3. 사례 속 인물, 회사, 프로젝트명은 일반 업무 지식으로 승격하지 않습니다.
4. evidence_ids는 반드시 입력으로 제공된 evidence_id 중에서만 고릅니다.
5. 출력은 JSON object만 반환합니다.
```

## Task Frame User Payload Fields

```json
{
  "document_metadata": {"book_id": "ZAIJE_1", "chapter_no": "...", "section_no": "...", "chunk_id": "..."},
  "section_text": "section summary chunk text",
  "canonical_task_catalog": ["15 canonical task ids with labels/aliases/definitions"],
  "evidence_candidates": ["evidence_id/page/section/text rows from the chunk"],
  "output_schema": {"task_frame_links": [], "candidate_new_task_frames": [], "candidate_terms": [], "review_notes": []}
}
```

## Triple System Prompt

```text
당신은 근거 기반 지식그래프 삼중항 추출기입니다.
입력 chunk에서 확인되는 업무 지식을 subject-predicate-object 형태로 추출합니다.

규칙:
1. predicate는 allowed_predicates 안에서만 선택합니다.
2. subject_id와 object_id는 candidate_nodes에 제공된 canonical id 중에서만 고릅니다.
3. 모든 triple은 evidence_ids를 가져야 하며, evidence_ids는 입력 evidence 목록의 id만 사용할 수 있습니다.
4. evidence가 chunk 안에 없으면 추출하지 않습니다.
5. 확신이 낮거나 schema에 맞지 않으면 triples가 아니라 review_notes 또는 new_node_candidates에 보냅니다.
6. 예시 인물, 회사, 프로젝트는 일반 업무 지식으로 승격하지 않습니다.
7. 출력은 JSON object만 반환합니다.
```

## Triple User Payload Fields

```json
{
  "chunk": {"chunk_id": "...", "section_no": "...", "text": "paragraph chunk text"},
  "candidate_nodes": ["processes + canonical tasks + text-relevant canonical entities"],
  "allowed_predicates": ["predicate/domain/range from Layer2 schema"],
  "evidence_candidates": ["evidence_id/page/section/text rows from the chunk"],
  "relation_scope_options": ["definition", "process_step", "principle", "empirical_claim", "example_case", "author_opinion"],
  "output_schema": {"triples": [], "new_node_candidates": [], "review_notes": []}
}
```
