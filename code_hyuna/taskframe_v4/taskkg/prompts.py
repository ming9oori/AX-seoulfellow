from __future__ import annotations

import json
from typing import Any


def extraction_prompt(chunks: list[dict[str, Any]]) -> tuple[str, str]:
    system = """당신은 한국어 업무 문서에서 근거 기반 Open KG를 추출한다.
이 호출은 LLM 1이다. 최종 TaskFrame이나 고정 도메인 관계를 만들지 않는다.
반드시 (1) 모든 Evidence에서 의미 있는 자유형 Fact를 먼저 추출하고 문자 단위로 검증한 뒤,
(2) 로컬 TaskMention을 추출하고, (3) Fact와 TaskMention을 연결한다.
Task와 무관한 Fact도 삭제하지 말고 task_links=[]로 보존한다.
subject_raw, raw_predicate, object_raw, qualifier.text, surface_form,
action_raw, focal_object_raw는
해당 Evidence 원문에 실제 존재하는 연속 문자열만 사용한다.
조사·어미·인용부호·괄호·약어·특수문자를 제거·교체하거나 동사를 기본형으로 바꾸지 않는다.
raw_predicate는 관계를 나타내는 원문의 동사·형용사·서술 표현을 중심으로 잡고,
그 논항인 주체·목적어·수치·대상을 raw_predicate 안에 삼키지 않는다.
원문에 없는 사실·역할·목적·연결어·서술어를 만들지 않는다.
JSON object 하나만 출력한다."""
    payload = [
        {
            "chunk_id": chunk["chunk_id"],
            "document_id": chunk["document_id"],
            "section_path": chunk["section_path"],
            "sentences": chunk["sentences"],
        }
        for chunk in chunks
    ]
    few_shots = """[예시 1: fact · 병렬 술어 원자화]
원문: 수의계약(Handshake’ deals)은 기업경영의 투명성을 떨어뜨리고 기업의 구매비용을 높인다.
BAD: 목적어를 raw_predicate에 넣거나 `떨어뜨리고`를 `떨어뜨린다`로 바꾸지 않는다.
GOOD facts:
[
  {
    "fact_id": "T1",
    "subject_raw": "수의계약(Handshake’ deals)",
    "raw_predicate": "떨어뜨리고",
    "object_raw": "기업경영의 투명성을",
    "knowledge_function": "fact",
    "qualifiers": [],
    "task_links": [],
    "evidence": {
      "source_id": "EV1",
      "exact_quote": "수의계약(Handshake’ deals)은 기업경영의 투명성을 떨어뜨리고 기업의 구매비용을 높인다."
    }
  },
  {
    "fact_id": "T2",
    "subject_raw": "수의계약(Handshake’ deals)",
    "raw_predicate": "높인다",
    "object_raw": "기업의 구매비용을",
    "knowledge_function": "fact",
    "qualifiers": [],
    "task_links": [],
    "evidence": {
      "source_id": "EV1",
      "exact_quote": "수의계약(Handshake’ deals)은 기업경영의 투명성을 떨어뜨리고 기업의 구매비용을 높인다."
    }
  }
]

[예시 2: definition · 병렬 정의 대상]
원문: 경쟁력 있는 제안 역량이란 전문가 영업 역량, 전략 개발 역량, 제안서 역량을 의미한다.
GOOD: 세 대상을 별도 Fact로 만들고 각각
subject_raw="경쟁력 있는 제안 역량", raw_predicate="의미한다",
knowledge_function="definition"으로 둔다. object_raw에는 원문의 각 역량 표현만 복사한다.

[예시 3: procedure · 시간 qualifier와 Task 연결]
원문: 평가위원들은 10시에 제안 평가를 시작한다.
GOOD TaskMention:
{"task_mention_id":"M1","surface_form":"제안 평가를 시작한다","action_raw":"시작한다","focal_object_raw":"제안 평가를","intended_outcome_raw":"","evidence_ids":["EV3"],"confidence":1.0}
GOOD Fact:
{"fact_id":"T1","subject_raw":"평가위원들은","raw_predicate":"시작한다","object_raw":"제안 평가를","knowledge_function":"procedure","qualifiers":[{"type":"temporal","text":"10시에"}],"task_links":[{"task_mention_id":"M1","relevance":"core"}],"evidence":{"source_id":"EV3","exact_quote":"평가위원들은 10시에 제안 평가를 시작한다."}}

[예시 4: rule · 조건 qualifier]
원문: 제안금액이 기준을 넘으면 제안 PM은 법무 검토를 받아야 한다.
GOOD:
{"fact_id":"T1","subject_raw":"제안 PM은","raw_predicate":"받아야 한다","object_raw":"법무 검토를","knowledge_function":"rule","qualifiers":[{"type":"condition","text":"제안금액이 기준을 넘으면"}],"task_links":[],"evidence":{"source_id":"EV4","exact_quote":"제안금액이 기준을 넘으면 제안 PM은 법무 검토를 받아야 한다."}}

[예시 5: decision]
원문: 평가위원회는 A 업체를 우선협상대상자로 선정했다.
GOOD:
{"fact_id":"T1","subject_raw":"평가위원회는","raw_predicate":"선정했다","object_raw":"A 업체를 우선협상대상자로","knowledge_function":"decision","qualifiers":[],"task_links":[],"evidence":{"source_id":"EV5","exact_quote":"평가위원회는 A 업체를 우선협상대상자로 선정했다."}}

[예시 6: recommendation · 조건 qualifier]
원문: 수주 가능성이 낮은 경우 제안에 참여하지 않는 것이 좋다.
GOOD:
{"fact_id":"T1","subject_raw":"","raw_predicate":"참여하지 않는 것이 좋다","object_raw":"제안에","knowledge_function":"recommendation","qualifiers":[{"type":"condition","text":"수주 가능성이 낮은 경우"}],"task_links":[],"evidence":{"source_id":"EV6","exact_quote":"수주 가능성이 낮은 경우 제안에 참여하지 않는 것이 좋다."}}

[예시 7: exception qualifier]
원문: 긴급 사업을 제외하고 모든 구매는 경쟁입찰로 진행한다.
GOOD:
{"fact_id":"T1","subject_raw":"모든 구매는","raw_predicate":"진행한다","object_raw":"경쟁입찰로","knowledge_function":"procedure","qualifiers":[{"type":"exception","text":"긴급 사업을 제외하고"}],"task_links":[],"evidence":{"source_id":"EV7","exact_quote":"긴급 사업을 제외하고 모든 구매는 경쟁입찰로 진행한다."}}

[예시 8: 원문 문자 보존과 Task가 아닌 일정 공백]
원문 A: “제안서를 잘 써야 입찰에 성공한다”라는 말이 반드시 맞는 말은 아니다.
GOOD subject_raw: “제안서를 잘 써야 입찰에 성공한다”라는 말
BAD: 곡선 인용부호 `“ ”`를 ASCII 인용부호로 바꾸지 않는다.
원문 B: - 12~1시: 점심
GOOD Fact: subject_raw="12~1시", raw_predicate=":", object_raw="점심",
knowledge_function="fact", qualifiers=[{"type":"temporal","text":"12~1시"}], task_links=[]
중요: `점심`은 일정 Fact지만 수행·관리할 업무가 아니므로 TaskMention을 만들지 않는다.

[예시 9: 실제 명제가 없는 질문]
원문: 왜 그럴까?
GOOD: facts=[], sentence_audits.status="no_extractable_fact"
"""
    user = f"""다음 chunk들을 분석하라.

출력:
{{
  "chunks": [{{
    "chunk_id": "CH_...",
    "task_mentions": [{{
      "task_mention_id": "M1",
      "surface_form": "원문 업무 표현",
      "action_raw": "원문 행위",
      "focal_object_raw": "원문 중심 대상 또는 빈 문자열",
      "intended_outcome_raw": "청크에 명시된 목적/결과의 원문 표현 또는 빈 문자열",
      "evidence_ids": ["EV_..."],
      "confidence": 0.0
    }}],
    "facts": [{{
      "fact_id": "T1",
      "subject_raw": "exact_quote의 원문 연속 문자열 또는 빈 문자열",
      "raw_predicate": "exact_quote의 원문 관계 표현",
      "object_raw": "exact_quote의 원문 연속 문자열 또는 빈 문자열",
      "knowledge_function": "fact|definition|procedure|rule|decision|recommendation",
      "qualifiers": [{{
        "type": "condition|temporal|exception",
        "text": "exact_quote의 원문 연속 문자열"
      }}],
      "evidence": {{
        "source_id": "EV_...",
        "exact_quote": "해당 Fact를 직접 뒷받침하는 원문 연속 인용"
      }},
      "task_links": [{{
        "task_mention_id": "M1",
        "relevance": "core|supporting|context"
      }}],
      "confidence": 0.0
    }}],
    "sentence_audits": [{{
      "evidence_id": "EV_...",
      "fact_ids": ["T1"],
      "status": "facts_extracted|no_extractable_fact",
      "reason": "Fact가 없을 때만 이유"
    }}]
  }}]
}}

규칙:
- 먼저 모든 Evidence의 Fact를 추출하고 검증한 뒤 TaskMention과 task_links를 작성한다.
- 모든 Evidence를 sentence_audits에 정확히 한 번 기록하고, 실제 fact_id 전체를 기록한다.
- 정의, 속성, 상태, 비교, 수치, 인과, 조건, 정책, 일정, 사례도 의미 있는 Fact이면 추출한다.
- `no_extractable_fact`는 질문·제목·번호·불완전 조각처럼 실제 명제 관계가 없을 때만 사용한다.
- 한 Triple은 하나의 원자 관계만 담는다. 병렬 술어 또는 서로 다른 목적어 관계는
  같은 subject_raw를 반복하더라도 별도 Triple로 나눈다.
- 실제 독립 관계가 하나뿐이면 하나만 추출한다. 개수를 늘리기 위한 중복·의역은 금지한다.
- subject_raw는 관계의 주체·화제, raw_predicate는 관계를 나타내는 서술 표현,
  object_raw는 그 관계의 대상·값·보어가 되도록 경계를 정한다.
- 목적어가 있는 타동 관계에서 목적어를 raw_predicate에 포함하고 object_raw를 비우지 않는다.
- raw_predicate를 사전 관계명이나 동사 기본형으로 바꾸지 않는다.
- 일반 문장의 raw_predicate로 조사 `은`, `는`, `이`, `가`만 단독 사용하지 않는다.
- 원문상 주체 또는 목적어가 실제로 생략된 경우에만 빈 문자열로 나타낸다.
- knowledge_function은 하나의 primary 값만 사용한다.
  명시적 판단 결과=decision, 강제 의무·금지=rule, 비강제 권고=recommendation,
  수행 단계=procedure, 개념 정의=definition, 나머지 상태·수치·인과·사례=fact 순으로 판정한다.
- condition/temporal/exception이 원문에 명시되면 S–P–O에 삼키지 말고 qualifier로 분리한다.
- 출력 직전에 모든 non-empty raw 필드와 qualifier.text에 대해
  `value in evidence.exact_quote`를 문자 단위로 직접 확인한다.
- `evidence.exact_quote in source_id의 source_text`도 문자 단위로 확인한다.
- 위 검사가 거짓이면 따옴표나 어미를 바꾸지 말고 실제 원문 substring으로 수정한다.
- raw 필드끼리 의미를 중복하지 않는다. 특히 object_raw의 내용을 raw_predicate에 반복하지 않는다.
- TaskMention은 수행·관리·완료 여부를 판단할 수 있는 로컬 업무 표현이다.
- 단순 역량 설명, 제목, 일정 공백, 일회성 서사 사건은 TaskMention으로 만들지 않는다.
- intended_outcome_raw는 같은 청크에 명시된 경우만 원문에서 복사한다.
- core는 업무 수행 자체, supporting은 목적·조건·산출물·결과, context는 주변 설명이다.
- 하나의 Triple은 여러 TaskMention에 연결될 수 있다.
- 연결 판단이 어려우면 Triple을 버리지 말고 task_links=[]로 둔다.
- 표에서는 행명·열명·값을 각각 원문에 존재하는 문자열로 사용한다.
  행명과 열명을 합친 새 표현이나 원문에 없는 `이다`, `는`을 만들지 않는다.
- 목록의 `시간: 활동`처럼 원문에 명시된 구분 관계는 `:`를 raw_predicate로 사용할 수 있다.
- 입력 ID와 유니코드 문자를 정확히 복사한다.

필수 few-shot:
아래 예시를 그대로 기준으로 삼되, 실제 답변에서는 위의 전체 출력 스키마를 작성한다.
{few_shots}

입력:
{json.dumps(payload, ensure_ascii=False, indent=2)}"""
    return system, user


def induction_prompt(
    mention_cards: list[dict[str, Any]],
    candidate_blocks: list[dict[str, Any]],
    ambiguous_facts: list[dict[str, Any]],
    chunk_contexts: list[dict[str, Any]],
) -> tuple[str, str]:
    system = """당신은 LLM 2로서 문서 전역의 TaskMention을 TaskFrame으로 병합·분리한다.
새 Triple이나 새 TaskMention을 추출하지 않는다. 후보 block은 비교 범위를 넓히는 참고값이며
최종 경계를 강제하지 않는다. 업무 목적, 핵심 행위, 중심 대상, 프로세스 단계, 범위,
추상화 수준, 연결 Fact를 종합한다. Actor/Input/Output 차이만으로 업무를 분리하지 않는다.
모든 입력 TaskMention을 정확히 하나의 TaskFrame에 넣는다.
경계가 애매한 입력 Fact에 대해서만 TaskMention 연결을 재판정한다.
JSON object 하나만 출력한다."""
    user = f"""TaskFrame을 구성하라.

출력:
{{
  "taskframes": [{{
    "frame_key": "F1",
    "canonical_name": "한국어 명사형 업무명",
    "definition": "근거에 충실한 정의",
    "scope": "프로세스 범위 또는 빈 문자열",
    "aliases": ["문서의 업무 표현"],
    "member_task_mentions": ["TM_..."],
    "status": "canonical|provisional"
  }}],
  "task_relations": [{{
    "source_frame_key": "F1",
    "relation": "sameTask|subTaskOf|relatedTask|precedes|follows|supports|distinctTask",
    "target_frame_key": "F2",
    "confidence": 0.0,
    "reason": "근거"
  }}],
  "triple_link_decisions": [{{
    "triple_id": "TR_...",
    "task_links": [{{
      "task_mention_id": "TM_...",
      "relevance": "core|supporting|context"
    }}],
    "reason": "재판정 근거"
  }}]
}}

규칙:
- 모든 mention ID를 정확히 한 Frame에 한 번만 배정한다.
- 목적·단계·범위·추상화 수준이 다르면 표현이 비슷해도 분리한다.
- 같은 업무의 다양한 표현이면 Actor나 산출물이 달라도 병합할 수 있다.
- 불확실한 Mention도 삭제하지 말고 provisional Frame으로 보존한다.
- canonical_name, definition, scope는 입력 근거를 일반화하되 새 사실을 만들지 않는다.
- aliases는 실제 member surface_form을 중심으로 작성한다.
- 관계는 근거가 있을 때만 만들고 같은/반대 방향 중복을 피한다.
- triple_link_decisions에는 제공된 ambiguous_facts만 정확한 입력 ID로 기록한다.
- `coverage_required=true`인 모든 Fact는 최소 하나 이상의 TaskMention에 연결한다.
- 업무 수행을 직접 나타내지 않는 정의·통계·배경·조건 Fact도 가장 관련 있는
  TaskMention에 relevance=context로 연결한다. task_links=[]로 남기지 않는다.
- knowledge_function은 Fact 자체의 문서 기능이다. procedure/rule/decision/recommendation은
  core 또는 supporting 후보이고 definition/fact는 대체로 context 후보이지만,
  이 힌트만으로 relevance를 강제하지 말고 실제 S–P–O와 Evidence 의미를 우선한다.
- qualifier의 condition/temporal/exception은 업무 범위와 단계 경계를 판단하는 근거로 사용한다.
- 하나의 Fact가 여러 업무에 관련되면 여러 TaskMention 연결을 허용한다.
- 애매한 Fact는 `현재 Evidence → 현재 chunk → 앞·뒤 chunk → section_path` 순으로 판단한다.
- 주변 chunk의 TaskMention은 연결 후보이며, 장·절 전환이나 주제 전환이 있으면
  현재 Fact와 가장 의미적으로 가까운 다른 후보를 선택한다. 근거가 약한 일반 Fact는
  가장 가까운 업무에 context로 연결하고 reason에 불확실성을 기록한다.
- 현재 Fact의 명시적 의미와 충돌하는 주변 문맥으로 연결을 덮어쓰지 않는다.

TaskMention:
{json.dumps(mention_cards, ensure_ascii=False, indent=2)}

알고리즘 후보 block:
{json.dumps(candidate_blocks, ensure_ascii=False, indent=2)}

경계 재판정 Fact:
{json.dumps(ambiguous_facts, ensure_ascii=False, indent=2)}

참조 chunk 문맥(각 Fact의 context_chunk_ids로 참조):
{json.dumps(chunk_contexts, ensure_ascii=False, indent=2)}"""
    return system, user


def reconciliation_prompt(
    provisional_frames: list[dict[str, Any]],
) -> tuple[str, str]:
    system = """당신은 LLM 2의 전역 reconciliation 단계이다.
앞선 로컬 induction이 만든 provisional TaskFrame을 문서 전역에서 비교하여 병합하거나
분리 상태를 유지한다. 새 TaskMention이나 Fact를 만들지 않는다.
모든 입력 provisional_taskframe_id를 정확히 하나의 최종 TaskFrame에 배정한다.
로컬 배치 경계 때문에 갈라진 동일 업무는 병합하되, 목적·프로세스 단계·대상·범위·
추상화 수준이 다른 업무는 분리한다. JSON object 하나만 출력한다."""
    user = f"""다음 provisional TaskFrame을 전역 조정하라.

출력:
{{
  "taskframes": [{{
    "frame_key": "GF1",
    "provisional_taskframe_ids": ["TF_..."],
    "canonical_name": "한국어 명사형 업무명",
    "definition": "공통 근거에 충실한 정의",
    "scope": "업무 범위 또는 빈 문자열",
    "aliases": ["검색용 업무 표현"],
    "status": "canonical|provisional",
    "merge_reason": "병합 또는 분리 유지 근거"
  }}],
  "task_relations": [{{
    "source_frame_key": "GF1",
    "relation": "sameTask|subTaskOf|relatedTask|precedes|follows|supports|distinctTask",
    "target_frame_key": "GF2",
    "confidence": 0.0,
    "reason": "관계 근거"
  }}]
}}

규칙:
- 모든 provisional_taskframe_id를 정확히 한 번 사용한다.
- 같은 이름만 보고 병합하지 말고 definition, scope, aliases, action, focal object,
  member Fact 요약을 함께 비교한다.
- Actor/Input/Output 차이만으로 분리하지 않는다.
- 불확실하면 과병합하지 말고 provisional 상태를 유지한다.
- 입력에 없는 ID나 업무 사실을 만들지 않는다.
- 관계는 근거가 있을 때만 생성하고 자기 관계는 만들지 않는다.

입력 provisional TaskFrame:
{json.dumps(provisional_frames, ensure_ascii=False, indent=2)}"""
    return system, user
