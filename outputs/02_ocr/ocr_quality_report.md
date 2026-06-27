# OCR Quality Report

Generated: 2026-06-27

- OCR source file: `handoff-hanyang/자이제_ocr_preprocessed.xlsx`
- OCR workbook type: preprocessed
- Total source rows preserved: 5009
- Clean Layer2 sentences: 4257
- Excluded rows: 752
- Preprocessed LLM chunks imported: 214
- Chunk mean char length: 1154.2
- Chunk max char length: 1800
- Body kept rows: 4257

## Zone Counts

{
  "title_page": 1,
  "prologue": 36,
  "table_of_contents": 144,
  "revision_note": 50,
  "chapter_cover": 4,
  "body": 4769,
  "index": 3,
  "copyright": 2
}

## OCR Flag Counts

{
  "excluded_from_layer2": 752,
  "title_page": 1,
  "prologue": 36,
  "prologue_text": 36,
  "english_spacing_check": 226,
  "table_of_contents": 144,
  "toc_title": 1,
  "toc_other": 2,
  "toc_chapter": 6,
  "toc_section": 133,
  "duplicate_clean_text": 493,
  "toc_page_number_fragment": 2,
  "revision_note": 50,
  "chapter_cover": 4,
  "header_footer": 196,
  "page_header": 196,
  "heading_body_split": 29,
  "section_heading_with_body": 29,
  "regular_text": 3733,
  "section_heading": 124,
  "visual_or_table_ocr": 94,
  "figure_caption_marker": 28,
  "visual_caption_marker": 39,
  "punctuation_only": 8,
  "list_marker_only": 217,
  "bullet_item": 300,
  "shipley_tip_marker": 45,
  "table_caption_marker": 11,
  "very_short_text": 19,
  "long_ocr_line": 46,
  "bibliographic_or_url": 4,
  "section_heading_fragment": 3,
  "split_heading_prefix": 3,
  "split_heading_suffix_stripped": 3,
  "numbered_example_or_table": 49,
  "numbered_example_text": 71,
  "section_number_not_in_toc": 22,
  "number_only": 4,
  "marker_after_heading_split": 3,
  "index": 3,
  "index_entry": 3,
  "copyright": 2,
  "copyright_notice": 2
}

## Gate G3

- Every chunk has sentence ids: True
- Every chunk has page range: True
- Result: PASS

The build used the workbook's reviewed preprocessing artifacts instead of
reconstructing chunks from the raw two-column OCR file.
