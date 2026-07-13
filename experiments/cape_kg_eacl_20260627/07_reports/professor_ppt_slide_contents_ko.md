# 교수님 발표용 PPT 슬라이드 내용 초안

Generated: 2026-06-28

이 파일은 기존 발표자료 초안 파일명과의 호환을 위해 유지합니다.

최신 실험 상태와 수정 방향을 반영해 다시 작성한 발표 슬라이드 원고는 아래 파일에 정리했습니다.

- `experiments/cape_kg_eacl_20260627/07_reports/professor_report_slide_contents_current_20260628_ko.md`

최신 발표 원고의 핵심 방향:

- KG 구축 결과와 논문 성능 주장을 분리합니다.
- 프롬프트별 산출물 구조와 최종 KG node/edge 생성 방식을 별도 슬라이드로 설명합니다.
- 실제 저장된 프롬프트 원문, runtime prompt template, `P_cape_kg_actual` prompt, baseline prompt 예시를 포함합니다.
- Competency Question(CQ)의 생성 방식과 CQ1-CQ12 실제 예시를 포함합니다.
- Qwen3-8B/14B/32B-AWQ 실행 결과는 silver/proxy diagnostic으로만 설명합니다.
- 현재 main table은 final performance table이 아니라 claimability table이라고 설명합니다.
- active-review는 효율 주장이 아니라 human-effort 템플릿과 평가기가 준비된 상태로 설명합니다.
- strict JSON warning gate는 PASS이며, 현재 선택 run과 과거 디버깅 run을 분리해 보고합니다.
- 다음 단계는 100 chunk human-gold annotation, IAA, adjudication, mapping expert review, active-review timing return입니다.
- 자동 산출물과 handoff infrastructure는 pre-human validation 기준 PASS 상태입니다.
- 최신 pre-human validation 수치는 24 checks, 23 PASS, 1 WARN, 0 FAIL입니다.
- KG 시각화/재현성 산출물에는 HTML/Neo4j뿐 아니라 RDF/Turtle export와 SHACL-style validation report도 포함됩니다.
