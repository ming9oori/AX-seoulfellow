# Source Profile

Generated: 2026-07-07T06:11:04+00:00
Input file: `자이제_1.xlsx`
Methodology: `AX_ZAIJE_Layer2_KG_Methodology.md`
Sheet: `clean_sentences`

## Counts

| item | value |
| --- | ---: |
| physical rows | 2366 |
| valid sentence rows | 1366 |
| evidence spans | 1366 |
| source chunks | 166 |
| chapters | 3 |
| sections | 51 |
| imputed section rows | 3 |

## Chunk Types

| chunk_type | count |
| --- | ---: |
| `paragraph_chunk` | 110 |
| `section_summary_chunk` | 51 |
| `definition_chunk` | 3 |
| `figure_chunk` | 1 |
| `table_chunk` | 1 |

## Chapter Profile

| chapter | title | pages | rows | sections |
| --- | --- | --- | ---: | ---: |
| 1 | 입찰과 제안 | 19-56 | 310 | 18 |
| 2 | 수주영업 | 57-118 | 487 | 18 |
| 3 | 제안서 전략 | 119-178 | 569 | 15 |

## Normalization Rule

- `chapter_no`/`section_no`가 누락된 행은 직전 유효 섹션에 귀속하고 `imputed_section=true`로 표시했다.
- 표/그림/정의성 문장은 chunk type으로 표시하되 원문 evidence span은 삭제하지 않았다.
