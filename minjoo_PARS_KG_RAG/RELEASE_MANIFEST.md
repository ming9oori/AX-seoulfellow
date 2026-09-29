# 공개 패키지 구성

이 폴더는 2026-09-22 기준 PARS-KG-RAG 최종 실험을 재현·검토하기 위한 정리본이다. 작성자 표기는 `minjoo`, 패키지 이름은 `minjoo_PARS_KG_RAG`로 고정했다.

## 포함

- 최종 실행기와 `src/kg_rag` 구현
- 최종 비교 및 최소 구성요소 ablation 설정
- 210문항 QA 데이터, 분할 정보, manifest
- 원문 기반 150문항을 만든 원본 생성기·시스템 프롬프트·five-shot·실행 통계 사본
- 150문항 Gold 정렬 및 60문항 수작업 확장의 코드·명세·통합 계보 문서
- CSV·JSONL·JSON·XLSX를 지원하는 설정 기반 범용 QA 생성기와 예제
- 단위 테스트
- 검색 처리 시간 측정 스크립트
- 방법론·데이터·Neo4j·발표·시각화 문서
- 검증된 최종·ablation·latency 요약 JSON

## 제외

- 약 2 GB의 `cache/`, `runs/`, 가상환경과 모델 다운로드 캐시
- API 키, Neo4j 자격 증명, `.env`
- 원문 `자이제_1.xlsx`와 중복되는 원본 150문항 API 생성 로그
- 중간 탐색 실험의 중복 설정과 임시 산출물

제외된 원시 실행 산출물의 경로와 SHA-256은 `results/final_summary.json`, `results/ablation_summary.json`, `results/latency_summary.json`에 기록되어 있다. 원시 실행물까지 장기 보관하려면 `runs/`를 Git 외부의 접근 통제된 저장소에 별도 아카이브해야 한다.
