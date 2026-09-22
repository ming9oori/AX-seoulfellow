from __future__ import annotations

import csv
import hashlib
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


VARIANT_TYPES = ("alias_synonym", "scenario_query", "colloquial_query")
ALL_ROW_TYPES = ("original_control", *VARIANT_TYPES)
VARIANT_SUFFIX = {
    "alias_synonym": "P_ALIAS",
    "scenario_query": "P_SCENARIO",
    "colloquial_query": "P_COLLOQUIAL",
}
VALIDATION_FLAGS = (
    "same_information_need",
    "no_added_or_removed_constraints",
    "no_answer_leakage",
    "natural_korean",
)
GOLD_LIST_FIELDS = (
    "gold_evidence_span_ids",
    "gold_taskframe_ids",
    "gold_fact_ids",
    "gold_pcf_ids",
    "gold_relation_types",
)
OUTPUT_COLUMNS = (
    "qa_id",
    "parent_qa_id",
    "variant_type",
    "question",
    "original_question",
    "answer",
    "evidence_text",
    *GOLD_LIST_FIELDS,
    "gold_path",
    "min_hops",
    "source_answerable",
    "ontology_answerable",
    "graph_structure_required",
    "expected_behavior",
    "question_origin",
    "query_stratum",
    "split",
    "review_status",
    "challenge_eligible",
    "semantic_equivalent",
    "no_added_or_removed_constraints",
    "no_answer_leakage",
    "natural_korean",
    "validation_notes",
    "lexical_overlap_score",
    "lexical_overlap_band",
    "generation_model",
    "generation_response_id",
    "validation_model",
    "validation_response_id",
    "prompt_version",
    "generated_at",
)


def normalize_text(value: Any) -> str:
    text = unicodedata.normalize("NFC", str(value or ""))
    return re.sub(r"\s+", " ", text).strip()


def normalize_match_text(value: Any) -> str:
    text = unicodedata.normalize("NFKC", str(value or "")).lower()
    text = re.sub(r"\s+", "", text)
    return re.sub(r"[^0-9a-z가-힣]", "", text)


def parse_jsonish(value: Any, default: Any) -> Any:
    if value is None or value == "":
        return default
    if isinstance(value, (dict, list, int, float, bool)):
        return value
    try:
        return json.loads(str(value))
    except (TypeError, ValueError, json.JSONDecodeError):
        return default


def json_compact(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def write_jsonl(path: Path, rows: Iterable[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False))
            handle.write("\n")


def write_csv(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _unique_rows(rows: Sequence[Mapping[str, Any]], key: str, label: str) -> dict[str, Mapping[str, Any]]:
    output: dict[str, Mapping[str, Any]] = {}
    duplicates: list[str] = []
    for row in rows:
        value = normalize_text(row.get(key))
        if not value:
            raise ValueError(f"{label} row has an empty {key}")
        if value in output:
            duplicates.append(value)
        output[value] = row
    if duplicates:
        raise ValueError(f"Duplicate {label} IDs: {sorted(set(duplicates))[:10]}")
    return output


def _string_list(value: Any) -> list[str]:
    parsed = parse_jsonish(value, [])
    if isinstance(parsed, str):
        parsed = [parsed]
    if not isinstance(parsed, list):
        return []
    return list(dict.fromkeys(normalize_text(item) for item in parsed if normalize_text(item)))


def load_gold_overrides(path: Path | None) -> dict[str, dict[str, Any]]:
    if path is None:
        return {}
    value = json.loads(path.read_text(encoding="utf-8"))
    rows = value.get("overrides", value) if isinstance(value, dict) else value
    if not isinstance(rows, list):
        raise ValueError("Gold override file must contain an overrides array")
    output: dict[str, dict[str, Any]] = {}
    for row in rows:
        qid = normalize_text(row.get("qid"))
        evidence_ids = _string_list(row.get("gold_evidence_ids"))
        if not qid or not evidence_ids:
            raise ValueError("Each Gold override needs qid and gold_evidence_ids")
        if qid in output:
            raise ValueError(f"Duplicate Gold override: {qid}")
        output[qid] = {**row, "qid": qid, "gold_evidence_ids": evidence_ids}
    return output


def build_parent_records(
    source_rows: Sequence[Mapping[str, Any]],
    aligned_rows: Sequence[Mapping[str, Any]],
    *,
    excluded_qids: set[str] | None = None,
    gold_overrides: Mapping[str, Mapping[str, Any]] | None = None,
    limit: int = 0,
) -> list[dict[str, Any]]:
    """Freeze source questions and Gold labels before any paraphrase is generated."""
    excluded_qids = excluded_qids or set()
    gold_overrides = gold_overrides or {}
    source_by_qid = _unique_rows(source_rows, "qa_id", "source QA")
    aligned_by_qid = _unique_rows(aligned_rows, "qid", "aligned Gold")
    missing = sorted((set(source_by_qid) - excluded_qids) - set(aligned_by_qid))
    if missing:
        raise ValueError(f"Source QA missing from aligned Gold: {missing[:10]}")
    unknown_overrides = sorted(set(gold_overrides) - set(source_by_qid))
    if unknown_overrides:
        raise ValueError(f"Gold overrides reference unknown QA IDs: {unknown_overrides}")

    parents: list[dict[str, Any]] = []
    for qid, source in source_by_qid.items():
        if qid in excluded_qids:
            continue
        question = normalize_text(source.get("question"))
        answer = normalize_text(source.get("answer"))
        if not question or not answer:
            raise ValueError(f"{qid} needs both question and reference answer")
        aligned = dict(aligned_by_qid[qid])
        override = gold_overrides.get(qid)
        if override:
            aligned["gold_evidence_ids"] = list(override["gold_evidence_ids"])
            # The old TaskFrame/PCF values were inferred from an empty evidence match.
            # Leave them empty so the experiment runner re-infers them from the repaired IDs.
            aligned["gold_taskframe_ids"] = []
            aligned["gold_pcf_ids"] = []
            aligned["gold_fact_ids"] = []
        evidence_ids = _string_list(aligned.get("gold_evidence_ids"))
        if not evidence_ids:
            raise ValueError(
                f"{qid} has no aligned Gold EvidenceSpan; add a reviewed override or exclude it"
            )
        evidence_text = parse_jsonish(source.get("evidence_text"), [])
        if isinstance(evidence_text, str):
            evidence_text = [evidence_text]
        parents.append(
            {
                "qid": qid,
                "question": question,
                "answer": answer,
                "evidence_texts": [normalize_text(item) for item in evidence_text if normalize_text(item)],
                "gold_evidence_span_ids": evidence_ids,
                "gold_taskframe_ids": _string_list(aligned.get("gold_taskframe_ids")),
                "gold_fact_ids": _string_list(aligned.get("gold_fact_ids")),
                "gold_pcf_ids": _string_list(aligned.get("gold_pcf_ids")),
                "gold_relation_types": _string_list(aligned.get("gold_relation_types")),
                "gold_path": aligned.get("gold_path", []),
                "min_hops": aligned.get("min_hops"),
                "source_answerable": normalize_text(source.get("source_answerable") or "true").lower(),
                "ontology_answerable": normalize_text(source.get("ontology_answerable")).lower(),
                "graph_structure_required": normalize_text(source.get("graph_structure_required")).lower(),
                "expected_behavior": normalize_text(source.get("expected_behavior") or "answer_with_evidence"),
                "override_applied": bool(override),
                "override_reason": normalize_text(override.get("reason")) if override else "",
            }
        )
    if limit:
        parents = parents[:limit]
    return parents


class LexicalOverlapScorer:
    """Query-token coverage by Gold source text, with a deterministic fallback."""

    def __init__(self) -> None:
        self._kiwi = None
        try:
            from kiwipiepy import Kiwi

            self._kiwi = Kiwi()
        except ImportError:
            self._kiwi = None

    def tokens(self, value: Any) -> set[str]:
        text = normalize_text(value).lower()
        if self._kiwi is None:
            return {
                token
                for token in re.findall(r"[0-9a-z가-힣]+", text)
                if len(token) > 1 or token.isdigit()
            }
        output: set[str] = set()
        for token in self._kiwi.tokenize(text):
            if token.tag.startswith(("N", "V", "MA", "SL", "SN", "XR")):
                form = normalize_text(token.form).lower()
                if len(form) > 1 or form.isdigit():
                    output.add(form)
        return output

    def score(self, question: str, evidence_texts: Sequence[str]) -> float:
        query_tokens = self.tokens(question)
        if not query_tokens:
            return 0.0
        evidence_tokens = self.tokens(" ".join(evidence_texts))
        return len(query_tokens & evidence_tokens) / len(query_tokens)

    @staticmethod
    def band(score: float) -> str:
        if score < 1 / 3:
            return "low"
        if score < 2 / 3:
            return "medium"
        return "high"


def variant_qid(parent_qid: str, variant_type: str) -> str:
    if variant_type not in VARIANT_SUFFIX:
        raise ValueError(f"Unknown variant type: {variant_type}")
    return f"{parent_qid}__{VARIANT_SUFFIX[variant_type]}"


def validate_generated_record(parent: Mapping[str, Any], record: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    variants = record.get("variants", [])
    validations = record.get("validations", [])
    by_type = {normalize_text(item.get("variant_type")): item for item in variants}
    validation_by_type = {
        normalize_text(item.get("variant_type")): item for item in validations
    }
    if len(variants) != len(by_type) or set(by_type) != set(VARIANT_TYPES):
        errors.append("variant_types_must_be_exactly_once_each")
    if len(validations) != len(validation_by_type) or set(validation_by_type) != set(VARIANT_TYPES):
        errors.append("validation_types_must_be_exactly_once_each")
    normalized_questions: list[str] = []
    original = normalize_match_text(parent["question"])
    answer = normalize_match_text(parent["answer"])
    for variant_type in VARIANT_TYPES:
        item = by_type.get(variant_type, {})
        validation = validation_by_type.get(variant_type, {})
        question = normalize_text(item.get("question"))
        normalized = normalize_match_text(question)
        if not question:
            errors.append(f"{variant_type}:empty_question")
        if normalized and normalized == original:
            errors.append(f"{variant_type}:same_as_original")
        if normalized:
            normalized_questions.append(normalized)
        if answer and len(answer) >= 8 and answer in normalized:
            errors.append(f"{variant_type}:full_answer_leakage")
        for flag in VALIDATION_FLAGS:
            if validation.get(flag) is not True:
                errors.append(f"{variant_type}:{flag}=false")
    if len(normalized_questions) != len(set(normalized_questions)):
        errors.append("duplicate_candidate_questions")
    return errors


def _base_row(parent: Mapping[str, Any], scorer: LexicalOverlapScorer) -> dict[str, Any]:
    score = scorer.score(parent["question"], parent["evidence_texts"])
    return {
        "qa_id": parent["qid"],
        "parent_qa_id": parent["qid"],
        "variant_type": "original_control",
        "question": parent["question"],
        "original_question": parent["question"],
        "answer": parent["answer"],
        "evidence_text": "[]",
        **{field: json_compact(parent[field]) for field in GOLD_LIST_FIELDS},
        "gold_path": json_compact(parent["gold_path"]),
        "min_hops": "" if parent["min_hops"] is None else str(parent["min_hops"]),
        "source_answerable": parent["source_answerable"],
        "ontology_answerable": parent["ontology_answerable"],
        "graph_structure_required": parent["graph_structure_required"],
        "expected_behavior": parent["expected_behavior"],
        "question_origin": "source_derived_control",
        "query_stratum": "paraphrase_stress_control",
        "split": "development",
        "review_status": "synthetic_not_human_reviewed",
        "challenge_eligible": "true",
        "semantic_equivalent": "true",
        "no_added_or_removed_constraints": "true",
        "no_answer_leakage": "true",
        "natural_korean": "true",
        "validation_notes": "original control; validation not applicable",
        "lexical_overlap_score": f"{score:.6f}",
        "lexical_overlap_band": scorer.band(score),
        "generation_model": "",
        "generation_response_id": "",
        "validation_model": "",
        "validation_response_id": "",
        "prompt_version": "paraphrase-stress-v1",
        "generated_at": "",
    }


def build_challenge_rows(
    parents: Sequence[Mapping[str, Any]],
    records: Mapping[str, Mapping[str, Any]],
    *,
    scorer: LexicalOverlapScorer | None = None,
) -> list[dict[str, Any]]:
    scorer = scorer or LexicalOverlapScorer()
    rows: list[dict[str, Any]] = []
    for parent in parents:
        base = _base_row(parent, scorer)
        rows.append(base)
        record = records.get(parent["qid"])
        if record is None:
            continue
        errors = validate_generated_record(parent, record)
        variants = {
            normalize_text(item.get("variant_type")): item
            for item in record.get("variants", [])
        }
        validations = {
            normalize_text(item.get("variant_type")): item
            for item in record.get("validations", [])
        }
        for variant_type in VARIANT_TYPES:
            variant = variants.get(variant_type, {})
            validation = validations.get(variant_type, {})
            question = normalize_text(variant.get("question"))
            score = scorer.score(question, parent["evidence_texts"])
            local_errors = [
                error
                for error in errors
                if error.startswith(f"{variant_type}:")
                or error in {"duplicate_candidate_questions", "variant_types_must_be_exactly_once_each", "validation_types_must_be_exactly_once_each"}
            ]
            rows.append(
                {
                    **base,
                    "qa_id": variant_qid(parent["qid"], variant_type),
                    "variant_type": variant_type,
                    "question": question,
                    "question_origin": "synthetic_paraphrase_from_source_derived_control",
                    "challenge_eligible": str(not local_errors).lower(),
                    "semantic_equivalent": str(validation.get("same_information_need") is True).lower(),
                    "no_added_or_removed_constraints": str(
                        validation.get("no_added_or_removed_constraints") is True
                    ).lower(),
                    "no_answer_leakage": str(validation.get("no_answer_leakage") is True).lower(),
                    "natural_korean": str(validation.get("natural_korean") is True).lower(),
                    "validation_notes": normalize_text(validation.get("rationale")),
                    "lexical_overlap_score": f"{score:.6f}",
                    "lexical_overlap_band": scorer.band(score),
                    "generation_model": normalize_text(record.get("generation_model")),
                    "generation_response_id": normalize_text(record.get("generation_response_id")),
                    "validation_model": normalize_text(record.get("validation_model")),
                    "validation_response_id": normalize_text(record.get("validation_response_id")),
                    "generated_at": normalize_text(record.get("generated_at")),
                }
            )
    return rows


def validate_challenge_rows(
    rows: Sequence[Mapping[str, Any]],
    parents: Sequence[Mapping[str, Any]],
    *,
    allow_incomplete: bool = False,
) -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    parent_by_qid = {parent["qid"]: parent for parent in parents}
    qids = [normalize_text(row.get("qa_id")) for row in rows]
    duplicate_qids = sorted(qid for qid, count in Counter(qids).items() if qid and count > 1)
    if duplicate_qids:
        errors.append(f"duplicate qa_id: {duplicate_qids[:10]}")
    grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[normalize_text(row.get("parent_qa_id"))].append(row)
    unknown_parents = sorted(set(grouped) - set(parent_by_qid))
    if unknown_parents:
        errors.append(f"unknown parent_qa_id: {unknown_parents[:10]}")
    if not allow_incomplete:
        missing_parents = sorted(set(parent_by_qid) - set(grouped))
        if missing_parents:
            errors.append(f"missing parent groups: {missing_parents[:10]}")

    for parent_qid, parent in parent_by_qid.items():
        group = grouped.get(parent_qid, [])
        row_types = Counter(normalize_text(row.get("variant_type")) for row in group)
        if not allow_incomplete and row_types != Counter(ALL_ROW_TYPES):
            errors.append(f"{parent_qid}: expected one row for each type, got {dict(row_types)}")
        for row in group:
            prefix = normalize_text(row.get("qa_id")) or parent_qid
            variant_type = normalize_text(row.get("variant_type"))
            if variant_type not in ALL_ROW_TYPES:
                errors.append(f"{prefix}: unknown variant_type={variant_type!r}")
            if normalize_text(row.get("answer")) != parent["answer"]:
                errors.append(f"{prefix}: reference answer changed")
            if parse_jsonish(row.get("evidence_text"), None) != []:
                errors.append(f"{prefix}: evidence_text must be [] so explicit Gold is used")
            for field in GOLD_LIST_FIELDS:
                if _string_list(row.get(field)) != list(parent[field]):
                    errors.append(f"{prefix}: frozen {field} changed")
            if parse_jsonish(row.get("gold_path"), None) != parent["gold_path"]:
                errors.append(f"{prefix}: frozen gold_path changed")
            if normalize_text(row.get("split")) != "development":
                errors.append(f"{prefix}: split must be development")
            eligible = normalize_text(row.get("challenge_eligible")).lower() == "true"
            if not allow_incomplete and not eligible:
                errors.append(f"{prefix}: challenge_eligible is not true")
            if variant_type != "original_control" and eligible:
                for field in (
                    "semantic_equivalent",
                    "no_added_or_removed_constraints",
                    "no_answer_leakage",
                    "natural_korean",
                ):
                    if normalize_text(row.get(field)).lower() != "true":
                        errors.append(f"{prefix}: eligible row has {field} != true")
                if normalize_match_text(row.get("question")) == normalize_match_text(parent["question"]):
                    errors.append(f"{prefix}: paraphrase equals original question")

    summary = {
        "parent_count": len(parent_by_qid),
        "row_count": len(rows),
        "expected_complete_row_count": len(parent_by_qid) * len(ALL_ROW_TYPES),
        "variant_type_counts": dict(sorted(Counter(normalize_text(row.get("variant_type")) for row in rows).items())),
        "lexical_overlap_band_counts": dict(sorted(Counter(normalize_text(row.get("lexical_overlap_band")) for row in rows).items())),
        "eligible_counts": dict(sorted(Counter(normalize_text(row.get("challenge_eligible")).lower() for row in rows).items())),
        "error_count": len(errors),
    }
    return errors, summary
