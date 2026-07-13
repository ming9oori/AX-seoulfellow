# SCALE-AWC 자이제 단일 도메인 실험

이 디렉터리는 `자이제_1_온톨로지_구축_실험설계서.md` v1.0을 실행하기 위한 별도 실험 공간이다. 기존 `trace_ol_pilot_v1` 결과는 수정하지 않는다.

## 현재 실행 범위

- Phase 0: 원본 hash, stable ID, leakage group, 50/20/20/10 split, manifest 잠금
- Phase 1 준비: blind PILOT 40건, 2인 주석 template, adjudication template
- Phase 1 후속: 인간 주석 반환 후 IAA 계산과 guideline lock
- Phase 2∼7: 인간 Gold 잠금 후에만 실행

LLM-Silver는 이 실험의 최종 정답으로 사용하지 않는다. TEST Gold를 모델 선정·프롬프트·threshold 조정에 사용하지 않는다.

## 실행

```bash
python3 zaije_experiment/src/prepare_phase0.py
python3 zaije_experiment/src/evaluation/compute_pilot_iaa.py \
  --annotator-a zaije_experiment/annotation/pilot/annotator_A.jsonl \
  --annotator-b zaije_experiment/annotation/pilot/annotator_B.jsonl
```

Phase 0의 기본 입력은 실험설계서의 binary hash와 일치하는 `legacy/자이제_1.xlsx`이다. handoff 수정본과의 차이는 `reports/input_resolution.md`에 기록한다.

## 중단 조건

Phase 1 PILOT의 인간 이중 주석과 adjudication이 없으면 E0∼E5의 잠긴 성능 수치를 계산하지 않는다. 이는 구현 미완이 아니라 실험설계서 Gate 1의 필수 조건이다.
