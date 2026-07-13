# TRACE-OL LLM-Silver 파일럿 실행 번들 v1.0

이 번들은 자이제 Layer 2 전문가 자료에서 TRACE-OL 파일럿을 다시 실행하기 위한 설계·설정·주석 schema·prompt·Neo4j 검증 자료를 포함한다.

## 핵심 설정

- 표본: 180개 target evidence unit
- 분할: CAL 60 / B1 60 / B2 Locked Test 60
- 기준 데이터: `TRACE-LLM-Silver-v0.1`
- 기준 주석: 저비용 LLM A·B 전체 독립 주석, 불일치만 C, 고위험 잔여 충돌만 D
- API 상한: 총 80회, 입력 600k token, 출력 250k token
- 최종 시스템: `E4 TRACE-Selective+Distillation`
- 필수 결과: Neo4j Audit Graph와 Operational Projection

## 파일

- `TRACE-OL_파일럿_실험설계서_v1.0.md`: 전체 설계서
- `config/pilot_experiment_config_v1.yaml`: 실행 파라미터
- `schemas/atomic_work_claim_schema_v0.2.json`: 구조화 주석 JSON Schema
- `prompts/reference_*.txt`: LLM-Silver 생성용 prompt
- `prompts/system_*.txt`: 비교 시스템용 prompt
- `neo4j/constraints_and_checks.cypher`: constraint·감사·시각화 query
- `templates/pilot_result_report_template.md`: 결과 보고서 양식

## 실행 전에 반드시 바꿀 값

1. `config/pilot_experiment_config_v1.yaml`의 모든 `SET_ME` model ID
2. 실제 API 단가와 사용 한도
3. 입력 파일 경로
4. CAL에서 정한 LF weight와 gate threshold
5. B2 locked manifest의 접근·버전 정책

## 권장 실행 순서

```text
구조 전처리
→ 180개 표본 및 split 동결
→ A/B 주석
→ 불일치 C/D 판정
→ Silver-A/B/Challenge 생성
→ CAL 규칙 보정
→ B1 선택적 LLM과 증류
→ B2 E0/E1/E2/E4 실행
→ Neo4j 적재
→ 품질·비용·critical error·CQ 보고
```

보고되는 정확도는 전문가 Gold가 아니라 **LLM-Silver와의 일치도**다.
