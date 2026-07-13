# 입력 파일 확정 보고

- 실험 입력: `/home/minjoo/AX_서울펠로우/legacy/자이제_1.xlsx`
- binary SHA-256: `9246a6da6c7635b3f34ee55df75112eb38a2984ea06828be943dc196de5926eb`
- 설계서 binary hash 일치: `True`
- handoff 수정본 SHA-256: `e8c5f174b65eccd7a50dbd2e0e216ea870a6aedfd16b3e4538d6486aea15cf1f`
- 정규화 행 차이: `3`건

설계서의 binary hash와 일치하는 `legacy/자이제_1.xlsx`를 잠긴 입력으로 사용한다. handoff 파일은 동일 본문이지만 3개 행의 문서 메타데이터가 보완된 수정본이다.

## 차이 상세

```json
[
  {
    "excel_row": 497,
    "fields": {
      "chapter_no": {
        "design_locked": "",
        "handoff": "2.0"
      },
      "chapter_title": {
        "design_locked": "",
        "handoff": "수주영업"
      },
      "page": {
        "design_locked": "",
        "handoff": "89.0"
      },
      "section_no": {
        "design_locked": "",
        "handoff": "2.2.2"
      },
      "section_title": {
        "design_locked": "",
        "handoff": "가치제안을 하라"
      }
    }
  },
  {
    "excel_row": 916,
    "fields": {
      "chapter_no": {
        "design_locked": "",
        "handoff": "3.0"
      },
      "chapter_title": {
        "design_locked": "",
        "handoff": "제안서 전략"
      },
      "page": {
        "design_locked": "",
        "handoff": "132.0"
      },
      "section_no": {
        "design_locked": "",
        "handoff": "3.1.3"
      },
      "section_title": {
        "design_locked": "",
        "handoff": "전략은 고객에서 출발한다"
      }
    }
  },
  {
    "excel_row": 1140,
    "fields": {
      "chapter_no": {
        "design_locked": "",
        "handoff": "3.0"
      },
      "chapter_title": {
        "design_locked": "",
        "handoff": "제안서 전략"
      },
      "page": {
        "design_locked": "",
        "handoff": "155.0"
      },
      "section_no": {
        "design_locked": "",
        "handoff": "3.2.3"
      },
      "section_title": {
        "design_locked": "",
        "handoff": "전술개발의 효과성을 검증하라"
      }
    }
  }
]
```

## Canonical hash amendment

- 설계서 기재값: `de55c3184b7eba79db0694f1c89cd0a8f56dcb873d00c9f96df4e2deafc503d9`
- `canonical-jsonl-v1` 계산값: `84d45b50acc542497df2f19bf8c3ad395f2ed223e6cfeb02be467c9f80f54906`
- 알고리즘: 6개 원본 필드를 NFC·LF·trim 정규화한 후, key-sorted compact JSON 한 행으로 직렬화하고 마지막 LF를 포함해 SHA-256 계산
- 설계서 값은 설명된 방법으로 재현되지 않아, Gold 주석·TEST 열람 전에 실제 알고리즘과 계산값을 사전등록 amendment로 잠괄다.
