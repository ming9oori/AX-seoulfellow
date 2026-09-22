# QA 데이터

최종 실험 입력은 다음 파일이다.

```text
generated/general_extension_20260920/qa_dataset_expanded_210_split.csv
```

구성은 원문 기반 150문항과 합성 일반 업무형 60문항이며, `evaluation_split` 열로 개발 32문항과 주 비교 178문항을 구분한다. 같은 디렉터리의 manifest에 행 수, 분할, SHA-256이 기록되어 있다.

이 폴더의 Python 파일은 QA 검증, 일반 질문 확장, 패러프레이즈 진단과 검색 분석에 사용한 연구 도구다. 일부 중간 분석 도구의 기본 입력은 공개 패키지에서 제외한 과거 `runs/` 또는 원문 QA를 가리키므로, 재사용할 때는 해당 명령의 `--help`를 확인하고 입력 경로를 명시해야 한다. 최종 210문항 실험 자체는 프로젝트 루트의 `run_experiment.py`와 `config/experiment*.yaml`만으로 실행한다.

