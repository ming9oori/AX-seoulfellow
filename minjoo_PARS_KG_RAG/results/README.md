# 검증 결과 요약

- `final_summary.json`: Dense RAG와 최종 PARS-KG-RAG 비교
- `ablation_summary.json`: Dense, PCF Path, PCF+Aspect, PARS-KG-RAG의 4-way ablation
- `latency_summary.json`: warm-cache 질문당 Top-5 검색 처리 시간

대용량 원시 실행 폴더는 Git에서 제외했다. 각 요약 JSON의 `artifact_checksums` 또는 `raw_artifact`에 원본 상대 경로와 SHA-256이 들어 있다.
