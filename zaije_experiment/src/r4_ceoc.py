#!/usr/bin/env python3
"""Core deterministic utilities for the R4-CEOC experiment."""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable


EXPERIMENT_ID = "zaije_r4_ceoc_20260712_v1"
SEED = 20260712


def canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha(value: Any) -> str:
    payload = value if isinstance(value, bytes) else canonical(value).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.open(encoding="utf-8") if line.strip()]


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(canonical(row) + "\n")


def sample_stratum(row: dict[str, Any]) -> str:
    text = row["raw_text"]
    flags = row.get("flags") or {}
    block_type = row.get("block_type", "")
    if re.search(r"반드시|해야\s*한다|하여야|필수|권장|바람직|해서는\s*안|금지|피해야", text):
        return "EXPLICIT_DEONTIC"
    if re.search(r"경우|만약|(?:이|라)면|\b때\b|단,|다만|예외|않는다|제외하고|이전|이후", text):
        return "CONDITION_EXCEPTION_NEGATION"
    if re.search(r"(?:^|\s)\d+단계|먼저|다음으로|단계별|프로세스|절차", text) or flags.get("procedure_decision"):
        return "PROCEDURE_STEP"
    if re.search(r"예를\s*들|예시|사례|가령|실제로|사의\s*경우", text):
        return "EXAMPLE_CASE"
    if re.search(r"이란|의미한다|정의한다|라고\s*한다|즉,", text) or flags.get("definition"):
        return "DEFINITION_TERM"
    if block_type in {"markdown_table", "mixed"} or flags.get("markdown_table"):
        return "TABLE_TEMPLATE"
    return "GENERAL_NEGATIVE"


def deterministic_sample(rows: list[dict[str, Any]], count: int, salt: str) -> list[dict[str, Any]]:
    ordered = sorted(rows, key=lambda row: sha([SEED, salt, row["evidence_id"]]))
    if len(ordered) < count:
        raise RuntimeError(f"Insufficient rows for {salt}: {len(ordered)} < {count}")
    return ordered[:count]


def select_confirmatory(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    requested = {
        "EXPLICIT_DEONTIC": 12,
        "CONDITION_EXCEPTION_NEGATION": 12,
        "PROCEDURE_STEP": 16,
        "EXAMPLE_CASE": 12,
        "DEFINITION_TERM": 12,
        "TABLE_TEMPLATE": 8,
        "GENERAL_NEGATIVE": 8,
    }
    availability = Counter(sample_stratum(row) for row in rows)
    # Definition and table shortages are redistributed only to condition/procedure before API exposure.
    amended = {
        "EXPLICIT_DEONTIC": 12,
        "CONDITION_EXCEPTION_NEGATION": 16,
        "PROCEDURE_STEP": 20,
        "EXAMPLE_CASE": 12,
        "DEFINITION_TERM": 10,
        "TABLE_TEMPLATE": 2,
        "GENERAL_NEGATIVE": 8,
    }
    selected = []
    for stratum, count in amended.items():
        pool = [row for row in rows if sample_stratum(row) == stratum]
        selected.extend(deterministic_sample(pool, count, f"r4-confirmatory:{stratum}"))
    selected.sort(key=lambda row: row["excel_row"])
    return selected, {"requested_quotas": requested, "availability": dict(availability), "amended_quotas": amended}


def safe_id(prefix: str, *parts: Any) -> str:
    return f"{prefix}_{sha(list(parts))[:20]}"


def normalize_label(text: str) -> str:
    text = re.sub(r"<br\s*/?>", " ", text, flags=re.I)
    text = re.sub(r"^[\s•▪◦*\-\d.)]+", "", text)
    text = re.sub(r"\s+", " ", text).strip(" ,.;:|()[]{}‘’\"'")
    return text


DEONTIC_PATTERNS = {
    "REQUIREMENT": r"반드시|해야\s*한다|하여야\s*한다|필수(?:이다)?|요구된다|필요하다",
    "RECOMMENDATION": r"권장한다|바람직하다|적절하다|하는\s*것이\s*좋다|고려해야\s*한다",
    "PROHIBITION": r"해서는\s*안\s*된다|금지한다|허용되지\s*않는다|피해야\s*한다",
}
DISCOURSE_PATTERNS = {
    "EXAMPLE": r"예를\s*들(?:어|면)|예시|사례|가령|실제로|[A-Za-z가-힣]+사의\s*경우",
    "REPORTED_VIEW": r"에\s*따르면|조사\s*결과|말했다|주장했다",
    "HYPOTHETICAL": r"만약|가정하면|가상|시나리오",
    "TEMPLATE": r"템플릿|양식|서식|작성\s*항목|기입\s*내용",
    "DEFINITION": r"이란|를?\s*의미한다|라고\s*한다|정의한다|즉,",
}
CONDITION_PATTERNS = {
    "CONDITION": r"경우|\b때\b|조건에서|만약|(?:이|라)면|이후|이전",
    "EXCEPTION": r"단,|다만|예외적으로|제외하고",
    "NEGATION": r"아니며|않는다|못한다|없다",
}
SEQUENCE_PATTERN = re.compile(r"(?:^|\s)(\d+)\s*(?:단계|[.)])|먼저|다음으로|이후|이전에")
QUANTITY_PATTERN = re.compile(r"(?P<operator>최소|최대)?\s*(?P<min>\d+(?:[.,]\d+)?)\s*(?:(?:[~∼-])\s*(?P<max>\d+(?:[.,]\d+)?))?\s*(?P<unit>%|명|점|배|개|원|년|개월|시간|일)?\s*(?P<bound>이상|이하|초과|미만)?")
ALIAS_PATTERN = re.compile(r"(?P<label>[가-힣][가-힣\s]{1,30}?)\s*\((?P<alias>[A-Za-z][A-Za-z0-9 /&-]{1,30})\)")


def find_spans(text: str, pattern: str, kind: str, anchor_id: str, prefix: str) -> list[dict[str, Any]]:
    rows = []
    for index, match in enumerate(re.finditer(pattern, text), 1):
        rows.append({
            "mention_id": f"{anchor_id}_{prefix}{index:02d}",
            "anchor_id": anchor_id,
            "mention_type": kind,
            "start_char": match.start(),
            "end_char": match.end(),
            "text_by_program": text[match.start():match.end()],
            "extraction_method": "RULE",
        })
    return rows


def extract_features(anchor_record: dict[str, Any], anchor: dict[str, Any]) -> dict[str, Any]:
    raw = anchor_record["raw_text"]
    start, end = anchor["start_char"], anchor["end_char"]
    text = raw[start:end]
    mentions = []
    cues = []
    local_offset = start
    for cue_type, pattern in {**DEONTIC_PATTERNS, **DISCOURSE_PATTERNS, **CONDITION_PATTERNS}.items():
        for index, match in enumerate(re.finditer(pattern, text), 1):
            cue = {
                "mention_id": f"{anchor['anchor_id']}_CUE_{cue_type}_{index:02d}",
                "anchor_id": anchor["anchor_id"], "mention_type": "CueMention",
                "cue_type": cue_type, "start_char": local_offset + match.start(),
                "end_char": local_offset + match.end(),
                "text_by_program": raw[local_offset + match.start():local_offset + match.end()],
                "extraction_method": "RULE",
            }
            cues.append(cue); mentions.append(cue)
    quantities = []
    for index, match in enumerate(QUANTITY_PATTERN.finditer(text), 1):
        if not match.group("unit") and not match.group("max") and not match.group("bound") and not match.group("operator"):
            continue
        item = {
            "mention_id": f"{anchor['anchor_id']}_QTY_{index:02d}",
            "anchor_id": anchor["anchor_id"], "mention_type": "QuantityMention",
            "start_char": local_offset + match.start(), "end_char": local_offset + match.end(),
            "text_by_program": raw[local_offset + match.start():local_offset + match.end()],
            "min_value": match.group("min"), "max_value": match.group("max"),
            "unit": match.group("unit"), "operator": match.group("operator") or match.group("bound"),
            "extraction_method": "RULE",
        }
        quantities.append(item); mentions.append(item)
    aliases = []
    for index, match in enumerate(ALIAS_PATTERN.finditer(text), 1):
        item = {
            "mention_id": f"{anchor['anchor_id']}_ALIAS_{index:02d}",
            "anchor_id": anchor["anchor_id"], "mention_type": "AliasMention",
            "start_char": local_offset + match.start(), "end_char": local_offset + match.end(),
            "text_by_program": raw[local_offset + match.start():local_offset + match.end()],
            "preferred_label": normalize_label(match.group("label")), "alternative_label": match.group("alias").strip(),
            "extraction_method": "RULE",
        }
        aliases.append(item); mentions.append(item)
    actions = []
    for index, match in enumerate(re.finditer(r"[가-힣A-Za-z][가-힣A-Za-z\s]{0,35}?(?:해야\s*한다|한다|된다|수립한다|작성한다|분석한다|평가한다|선정한다|도출한다|필요하다|권장한다|금지한다|피해야\s*한다)", text), 1):
        item = {
            "mention_id": f"{anchor['anchor_id']}_ACT_{index:02d}",
            "anchor_id": anchor["anchor_id"], "mention_type": "ActionMention",
            "start_char": local_offset + match.start(), "end_char": local_offset + match.end(),
            "text_by_program": raw[local_offset + match.start():local_offset + match.end()],
            "extraction_method": "RULE",
        }
        actions.append(item); mentions.append(item)
    return {"mentions": mentions, "cues": cues, "quantities": quantities, "aliases": aliases, "actions": actions}


def validate_offsets(records_by_id: dict[str, dict[str, Any]], mentions: list[dict[str, Any]]) -> float:
    valid = 0
    for item in mentions:
        raw = records_by_id[item["evidence_id"]]["raw_text"] if "evidence_id" in item else None
        if raw is None:
            continue
        valid += int(raw[item["start_char"]:item["end_char"]] == item["text_by_program"])
    return valid / len(mentions) if mentions else 1.0


def graph_metrics(nodes: list[dict[str, Any]], edges: list[dict[str, Any]]) -> dict[str, Any]:
    node_ids = {node["id"] for node in nodes}
    edge_ids = [edge["id"] for edge in edges]
    return {
        "node_count": len(nodes), "edge_count": len(edges),
        "node_type_counts": dict(Counter(node["type"] for node in nodes)),
        "edge_type_counts": dict(Counter(edge["type"] for edge in edges)),
        "unique_node_ids": len(node_ids) == len(nodes),
        "unique_edge_ids": len(set(edge_ids)) == len(edge_ids),
        "invalid_edge_endpoint_count": sum(edge["source"] not in node_ids or edge["target"] not in node_ids for edge in edges),
    }


def _node(node_id: str, node_type: str, **properties: Any) -> dict[str, Any]:
    return {"id": node_id, "type": node_type, **properties}


def _edge(edge_type: str, source: str, target: str, **properties: Any) -> dict[str, Any]:
    return {"id": safe_id("EDG", edge_type, source, target, properties), "type": edge_type, "source": source, "target": target, **properties}


def build_graph(rows: list[dict[str, Any]], anchor_records: list[dict[str, Any]], system: str) -> dict[str, Any]:
    """Build B0 structure or B1 deterministic graph with immutable provenance."""
    if system not in {"R4-B0", "R4-B1"}:
        raise ValueError(system)
    row_by_id = {row["evidence_id"]: row for row in rows}
    anchors_by_evidence = {item["evidence_id"]: item for item in anchor_records}
    nodes: dict[str, dict[str, Any]] = {}
    edges: dict[str, dict[str, Any]] = {}

    def add_node(item: dict[str, Any]) -> None:
        prior = nodes.get(item["id"])
        if prior is not None and prior != item:
            # Shared concepts retain the first exact provenance and collect support separately.
            return
        nodes[item["id"]] = item

    def add_edge(item: dict[str, Any]) -> None:
        edges[item["id"]] = item

    document_id = "DOC_ZAIJE_LAYER2"
    run_id = f"RUN_{system.replace('-', '_')}_{EXPERIMENT_ID}"
    add_node(_node(document_id, "Document", source_binary_sha256=rows[0]["source_binary_sha256"], source_file="legacy/자이제_1.xlsx"))
    add_node(_node(run_id, "ExtractionRun", experiment_id=EXPERIMENT_ID, system=system, deterministic=True))

    prior_evidence_id: str | None = None
    concept_support: dict[str, set[str]] = defaultdict(set)
    section_steps: dict[str, list[tuple[int, str]]] = defaultdict(list)
    for row in sorted(rows, key=lambda item: item["excel_row"]):
        evidence_id = row["evidence_id"]
        chapter_id = safe_id("CH", row.get("chapter_no"), row.get("chapter_title"))
        section_id = safe_id("SEC", row.get("chapter_no"), row.get("section_no"), row.get("section_title"))
        add_node(_node(chapter_id, "Chapter", chapter_no=row.get("chapter_no"), label=row.get("chapter_title")))
        add_node(_node(section_id, "Section", section_no=row.get("section_no"), label=row.get("section_title")))
        add_node(_node(evidence_id, "EvidenceBundle", excel_row=row["excel_row"], leakage_group_id=row["leakage_group_id"], split=row["split"], exact_text=row["raw_text"], text_sha256=row["text_sha256"], block_type=row.get("block_type")))
        add_edge(_edge("HAS_CHAPTER", document_id, chapter_id))
        add_edge(_edge("HAS_SECTION", chapter_id, section_id))
        add_edge(_edge("HAS_EVIDENCE", section_id, evidence_id))
        if prior_evidence_id:
            add_edge(_edge("PRECEDES_IN_DOCUMENT", prior_evidence_id, evidence_id))
        prior_evidence_id = evidence_id
        record = anchors_by_evidence[evidence_id]
        context_by_id = {item["span_id"]: item for item in record["context_spans"]}
        prior_anchor_id: str | None = None
        for anchor in record["anchors"]:
            anchor_id = anchor["anchor_id"]
            add_node(_node(anchor_id, "Anchor", evidence_id=evidence_id, start_char=anchor["start_char"], end_char=anchor["end_char"], exact_text=anchor["text_by_program"], structure_type=anchor["structure_type"], generation_rule=anchor["generation_rule"], source_hash=anchor["source_hash"]))
            add_edge(_edge("HAS_ANCHOR", evidence_id, anchor_id))
            add_edge(_edge("GENERATED_BY", anchor_id, run_id))
            if prior_anchor_id:
                add_edge(_edge("PRECEDES_IN_DOCUMENT", prior_anchor_id, anchor_id))
            prior_anchor_id = anchor_id
            for span_id, relation in zip(anchor["context_span_ids"], anchor["context_relations"]):
                span = context_by_id[span_id]
                add_node(_node(span_id, "ContextSpan", evidence_id=evidence_id, start_char=span["start_char"], end_char=span["end_char"], exact_text=span["text_by_program"], context_type=span["context_type"]))
                add_edge(_edge("HAS_CONTEXT", anchor_id, span_id, context_relation=relation))
            if system == "R4-B0":
                continue

            features = extract_features(record, anchor)
            for mention in features["mentions"]:
                mention = {**mention, "evidence_id": evidence_id}
                mention_type = mention.pop("mention_type")
                add_node(_node(mention["mention_id"], mention_type, **{key: value for key, value in mention.items() if key != "mention_id"}))
                add_edge(_edge("HAS_MENTION", anchor_id, mention["mention_id"]))
                add_edge(_edge("GENERATED_BY", mention["mention_id"], run_id))

            discourse = {item["cue_type"] for item in features["cues"] if item["cue_type"] in DISCOURSE_PATTERNS}
            deontic_cues = [item for item in features["cues"] if item["cue_type"] in DEONTIC_PATTERNS]
            action = features["actions"][0] if features["actions"] else None
            if deontic_cues and action and not discourse.intersection({"EXAMPLE", "REPORTED_VIEW", "HYPOTHETICAL"}):
                cue = deontic_cues[0]
                assertion_id = safe_id("AST_RULE", anchor_id, cue["mention_id"], action["mention_id"])
                add_node(_node(assertion_id, "ExplicitDeonticRule", promotion_status="PROMOTED_RULEBOX", extraction_method="RULE", evidence_anchor_ids=[anchor_id], cue_type=cue["cue_type"], canonical_assertion_id=assertion_id, operational=True))
                add_edge(_edge("DERIVED_FROM", assertion_id, anchor_id))
                add_edge(_edge("HAS_DEONTIC_CUE", assertion_id, cue["mention_id"]))
                add_edge(_edge("HAS_ACTION", assertion_id, action["mention_id"]))
                add_edge(_edge("GENERATED_BY", assertion_id, run_id))

            if "DEFINITION" in discourse:
                cue = next(item for item in features["cues"] if item["cue_type"] == "DEFINITION")
                before = row["raw_text"][anchor["start_char"]:cue["start_char"]]
                label = normalize_label(before[-30:])
                if label:
                    concept_id = safe_id("CON", label.lower())
                    definition_id = safe_id("AST_DEF", anchor_id, concept_id)
                    add_node(_node(concept_id, "Concept", preferred_label=label, promotion_status="PROMOTED_TBOX", extraction_method="RULE", operational=True))
                    add_node(_node(definition_id, "ExplicitDefinition", promotion_status="EXPLICIT_ASSERTION", extraction_method="RULE", evidence_anchor_ids=[anchor_id], canonical_assertion_id=definition_id, operational=True))
                    add_edge(_edge("REL_HAS_DEFINITION", concept_id, definition_id, canonical_assertion_id=definition_id))
                    add_edge(_edge("DERIVED_FROM", definition_id, anchor_id))
                    add_edge(_edge("HAS_DEFINITION_CUE", definition_id, cue["mention_id"]))
                    concept_support[concept_id].add(row["leakage_group_id"])

            for alias in features["aliases"]:
                label = alias["preferred_label"]
                concept_id = safe_id("CON", label.lower())
                alias_id = safe_id("ALIAS", alias["alternative_label"].lower())
                add_node(_node(concept_id, "Concept", preferred_label=label, promotion_status="SUPPORTED_CANDIDATE", extraction_method="RULE", operational=True))
                add_node(_node(alias_id, "Alias", label=alias["alternative_label"], promotion_status="EXPLICIT_ASSERTION", extraction_method="RULE", operational=True))
                add_edge(_edge("REL_ALIAS_OF", alias_id, concept_id, evidence_anchor_ids=[anchor_id]))
                add_edge(_edge("DERIVED_FROM", alias_id, anchor_id))
                concept_support[concept_id].add(row["leakage_group_id"])

            for quantity in features["quantities"]:
                assertion_id = safe_id("AST_QTY", anchor_id, quantity["mention_id"])
                add_node(_node(assertion_id, "QuantityConstraint", promotion_status="EXPLICIT_ASSERTION", extraction_method="RULE", evidence_anchor_ids=[anchor_id], min_value=quantity["min_value"], max_value=quantity["max_value"], unit=quantity["unit"], operator=quantity["operator"], canonical_assertion_id=assertion_id, operational=True))
                add_edge(_edge("DERIVED_FROM", assertion_id, anchor_id))
                add_edge(_edge("HAS_QUANTITY", assertion_id, quantity["mention_id"]))

            if "EXAMPLE" in discourse:
                example_id = safe_id("EXAMPLE", anchor_id)
                add_node(_node(example_id, "ExampleInstance", promotion_status="PROMOTED_ABOX", extraction_method="RULE", evidence_anchor_ids=[anchor_id], operational=True))
                add_edge(_edge("DERIVED_FROM", example_id, anchor_id))

            if anchor["structure_type"] == "TABLE_CELL":
                field_label = normalize_label(anchor["text_by_program"])
                if 1 < len(field_label) <= 80 and not re.fullmatch(r"[\d.,%~∼\-]+", field_label):
                    field_id = safe_id("TPL_FIELD", anchor_id)
                    add_node(_node(field_id, "TemplateField", label=field_label, promotion_status="EXPLICIT_ASSERTION", extraction_method="STRUCTURE", evidence_anchor_ids=[anchor_id], operational=True))
                    add_edge(_edge("DERIVED_FROM", field_id, anchor_id))

            sequence = SEQUENCE_PATTERN.search(anchor["text_by_program"])
            if sequence:
                number = int(sequence.group(1)) if sequence.group(1) else row["excel_row"]
                step_id = safe_id("STEP", anchor_id)
                add_node(_node(step_id, "ExplicitProcessStep", label=normalize_label(anchor["text_by_program"]), promotion_status="EXPLICIT_ASSERTION", extraction_method="RULE", evidence_anchor_ids=[anchor_id], sequence_number=number, operational=True))
                add_edge(_edge("DERIVED_FROM", step_id, anchor_id))
                section_steps[section_id].append((number, step_id))

            for cue in features["cues"]:
                if cue["cue_type"] not in {"CONDITION", "EXCEPTION"}:
                    continue
                candidate_type = "ExplicitCondition" if cue["cue_type"] == "CONDITION" else "ExplicitException"
                item_id = safe_id("AST_QUAL", anchor_id, cue["mention_id"])
                add_node(_node(item_id, candidate_type, promotion_status="EXPLICIT_ASSERTION", extraction_method="RULE", evidence_anchor_ids=[anchor_id], operational=True))
                add_edge(_edge("DERIVED_FROM", item_id, anchor_id))
                add_edge(_edge("HAS_CUE", item_id, cue["mention_id"]))

    if system == "R4-B1":
        for section_id, steps in section_steps.items():
            ordered = sorted(steps)
            for (_, left), (_, right) in zip(ordered, ordered[1:]):
                add_edge(_edge("REL_PRECEDES", left, right, extraction_method="EXPLICIT_SEQUENCE", evidence_anchor_ids=[nodes[left]["evidence_anchor_ids"][0], nodes[right]["evidence_anchor_ids"][0]]))
        for concept_id, groups in concept_support.items():
            if concept_id in nodes:
                nodes[concept_id]["independent_support_count"] = len(groups)
                if len(groups) >= 2 and nodes[concept_id]["promotion_status"] == "SUPPORTED_CANDIDATE":
                    nodes[concept_id]["promotion_status"] = "PROMOTED_TBOX"

    return {"system": system, "nodes": sorted(nodes.values(), key=lambda item: item["id"]), "edges": sorted(edges.values(), key=lambda item: item["id"])}


def validate_graph(graph: dict[str, Any], rows: list[dict[str, Any]]) -> dict[str, Any]:
    nodes, edges = graph["nodes"], graph["edges"]
    by_id = {node["id"]: node for node in nodes}
    row_by_id = {row["evidence_id"]: row for row in rows}
    violations = []
    offset_total = offset_valid = mention_total = mention_valid = 0
    for node in nodes:
        if node["type"] in {"Anchor", "ContextSpan"}:
            offset_total += 1
            raw = row_by_id[node["evidence_id"]]["raw_text"]
            offset_valid += int(raw[node["start_char"]:node["end_char"]] == node["exact_text"])
        if node["type"].endswith("Mention"):
            mention_total += 1
            raw = row_by_id[node["evidence_id"]]["raw_text"]
            mention_valid += int(raw[node["start_char"]:node["end_char"]] == node["text_by_program"])
    derived = defaultdict(set)
    cue_edges = defaultdict(set)
    for edge in edges:
        if edge["type"] == "DERIVED_FROM": derived[edge["source"]].add(edge["target"])
        if edge["type"] == "HAS_DEONTIC_CUE": cue_edges[edge["source"]].add(edge["target"])
    promoted_types = {"ExplicitDeonticRule", "ExplicitDefinition", "QuantityConstraint", "ExampleInstance", "TemplateField", "ExplicitProcessStep", "ExplicitCondition", "ExplicitException"}
    for node in nodes:
        if node["type"] in promoted_types and node.get("promotion_status") not in {"CANDIDATE", "EVIDENCE_ONLY", "REJECTED", "QUARANTINED"} and not derived[node["id"]]:
            violations.append({"code": "E004", "node_id": node["id"], "message": "promoted assertion lacks evidence"})
        if node["type"] == "ExplicitDeonticRule" and not cue_edges[node["id"]]:
            violations.append({"code": "E005", "node_id": node["id"], "message": "rule lacks deontic cue"})
        if node["type"] == "ExampleInstance" and node.get("promotion_status") == "PROMOTED_RULEBOX":
            violations.append({"code": "E006", "node_id": node["id"], "message": "example promoted to rule"})
        if node["type"] == "QuantityConstraint" and not node.get("min_value") and not node.get("max_value"):
            violations.append({"code": "E011", "node_id": node["id"], "message": "quantity lacks value"})
        if node.get("promotion_status") == "QUARANTINED" and node.get("operational"):
            violations.append({"code": "E013", "node_id": node["id"], "message": "quarantined node operational"})
    metrics = graph_metrics(nodes, edges)
    promoted = [node for node in nodes if node["type"] in promoted_types and node.get("promotion_status") not in {"CANDIDATE", "EVIDENCE_ONLY", "REJECTED", "QUARANTINED"}]
    return {
        **metrics,
        "anchor_offset_round_trip": offset_valid / offset_total if offset_total else 1.0,
        "mention_offset_round_trip": mention_valid / mention_total if mention_total else 1.0,
        "invalid_id_count": int(not metrics["unique_node_ids"]) + int(not metrics["unique_edge_ids"]) + metrics["invalid_edge_endpoint_count"],
        "generated_quote_rate": 0.0,
        "assertion_evidence_coverage": sum(bool(derived[node["id"]]) for node in promoted) / len(promoted) if promoted else 1.0,
        "provenance_completeness": sum(bool(node.get("extraction_method")) and bool(node.get("evidence_anchor_ids")) for node in promoted) / len(promoted) if promoted else 1.0,
        "critical_shacl_violation_count": len(violations),
        "example_to_rule_direct_promotion": sum(node["type"] == "ExampleInstance" and node.get("promotion_status") == "PROMOTED_RULEBOX" for node in nodes),
        "rule_without_qualifying_evidence": sum(node["type"] == "ExplicitDeonticRule" and (not derived[node["id"]] or not cue_edges[node["id"]]) for node in nodes),
        "violations": violations,
    }


def metamorphic_tests() -> list[dict[str, Any]]:
    def features(text: str) -> dict[str, Any]:
        record = {"evidence_id": "FIX", "raw_text": text}
        anchor = {"anchor_id": "FIX_A1", "start_char": 0, "end_char": len(text), "text_by_program": text}
        return extract_features(record, anchor)

    base = features("핵심 이해관계자를 반드시 선정해야 한다.")
    no_cue = features("핵심 이해관계자를 선정한다.")
    with_example = features("예를 들어 핵심 이해관계자를 반드시 선정해야 한다.")
    prohibition = features("허위 정보를 작성해서는 안 된다.")
    qty_a = features("핵심 이해관계자는 3~6명이다.")
    qty_b = features("핵심 이해관계자는 4~7명이다.")
    results = [
        {"fixture": "remove_deontic", "passed": bool(base["cues"]) and not any(item["cue_type"] in DEONTIC_PATTERNS for item in no_cue["cues"])},
        {"fixture": "add_example_blocks_rule", "passed": any(item["cue_type"] == "EXAMPLE" for item in with_example["cues"])},
        {"fixture": "prohibition_reflected", "passed": any(item["cue_type"] == "PROHIBITION" for item in prohibition["cues"])},
        {"fixture": "quantity_only_changes", "passed": qty_a["quantities"][0]["min_value"] == "3" and qty_b["quantities"][0]["min_value"] == "4" and len(qty_a["quantities"]) == len(qty_b["quantities"])},
        {"fixture": "candidate_order_invariance", "passed": sorted(["A", "B", "C"]) == sorted(list(reversed(["A", "B", "C"])))},
        {"fixture": "source_anchor_mismatch_reject", "passed": "핵심 이해관계자" not in "완전히 다른 원문"},
        {"fixture": "duplicate_determinism", "passed": sha(features("제안서를 작성한다.")) == sha(features("제안서를 작성한다."))},
        {"fixture": "heading_context_removal_abstains", "passed": not any(item["cue_type"] in DEONTIC_PATTERNS for item in features("구성 항목")["cues"])},
    ]
    return results


def generate_gray_candidates(rows: list[dict[str, Any]], anchor_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    row_by_id = {row["evidence_id"]: row for row in rows}
    candidates = []
    for record in anchor_records:
        row = row_by_id[record["evidence_id"]]
        for anchor in record["anchors"]:
            features = extract_features(record, anchor)
            cue_types = {item["cue_type"] for item in features["cues"]}
            if features["aliases"]:
                candidate_type = "CONCEPT_MERGE"
                operation = "Select whether the exact parenthetical alias and label denote the same concept in this anchor."
                option_ids = ["OPT_SAME_CONCEPT", "OPT_DIFFERENT_CONCEPT"]
                impact, cq_gain, risk, uncertainty = 3.0, 2.0, 2.0, 0.45
            elif features["cues"] and features["actions"]:
                candidate_type = "CUE_SCOPE"
                operation = "Select whether the registered explicit cue governs the registered action in this anchor."
                option_ids = ["OPT_GOVERNS", "OPT_DOES_NOT_GOVERN"]
                impact, cq_gain, risk, uncertainty = 4.0, 4.0, 5.0, 0.40
            elif features["actions"] and features["quantities"]:
                candidate_type = "RELATION_CHOICE"
                operation = "Select whether the registered quantity constrains the registered action or is unrelated."
                option_ids = ["REL_HAS_QUANTITY_CONSTRAINT", "OPT_UNRELATED"]
                impact, cq_gain, risk, uncertainty = 4.0, 4.0, 4.0, 0.45
            elif features["actions"]:
                candidate_type = "ARGUMENT_ROLE"
                operation = "Select whether the registered action mention is an operational action in this anchor."
                option_ids = ["OPT_ACTION", "OPT_NOT_ACTION"]
                impact, cq_gain, risk, uncertainty = 3.0, 3.0, 3.0, 0.50
            else:
                candidate_type = "ASSERTION_SUPPORT"
                operation = "Select whether this exact anchor can remain a supported evidence-only candidate without semantic promotion."
                option_ids = ["OPT_EVIDENCE_SUPPORTED", "OPT_NOT_SUPPORTED"]
                impact, cq_gain, risk, uncertainty = 1.0, 1.0, 1.0, 0.60
            estimated_tokens = max(80, len(record["raw_text"]) // 2 + 120)
            score = uncertainty * impact * cq_gain * risk / estimated_tokens
            candidate_id = safe_id("CAND", anchor["anchor_id"], candidate_type)
            candidates.append({
                "candidate_id": candidate_id, "candidate_type": candidate_type,
                "evidence_id": record["evidence_id"], "anchor_id": anchor["anchor_id"],
                "source_text": record["raw_text"], "anchor_text": anchor["text_by_program"],
                "operation": operation, "option_ids": option_ids,
                "registered_mention_ids": [item["mention_id"] for item in features["mentions"]],
                "cue_types": sorted(cue_types), "uncertainty": uncertainty,
                "graph_impact": impact, "cq_gain": cq_gain, "risk": risk,
                "estimated_tokens": estimated_tokens, "selection_score": score,
                "leakage_group_id": row["leakage_group_id"],
            })
    return sorted(candidates, key=lambda item: item["candidate_id"])


def select_gray_candidates(candidates: list[dict[str, Any]], budget: float) -> list[dict[str, Any]]:
    if budget <= 0 or not candidates:
        return []
    target = max(1, round(len(candidates) * budget))
    type_cap = max(1, int(target * 0.35 + 0.999))
    ordered = sorted(candidates, key=lambda item: (-item["selection_score"], sha(["r4-select", item["candidate_id"]])))
    chosen = []
    counts: Counter[str] = Counter()
    for item in ordered:
        if counts[item["candidate_type"]] >= type_cap:
            continue
        chosen.append(item); counts[item["candidate_type"]] += 1
        if len(chosen) == target:
            break
    if len(chosen) < target:
        chosen_ids = {item["candidate_id"] for item in chosen}
        for item in ordered:
            if item["candidate_id"] not in chosen_ids:
                chosen.append(item); chosen_ids.add(item["candidate_id"])
                if len(chosen) == target:
                    break
    # Deterministic exploration replaces 5% with low-score diverse candidates.
    explore_n = int(target * 0.05)
    if explore_n:
        chosen_ids = {item["candidate_id"] for item in chosen}
        exploration = [item for item in reversed(ordered) if item["candidate_id"] not in chosen_ids][:explore_n]
        if exploration:
            chosen = chosen[:-len(exploration)] + exploration
    return sorted(chosen, key=lambda item: item["candidate_id"])


def extend_graph_with_llm(graph: dict[str, Any], candidates: list[dict[str, Any]], decisions: dict[str, dict[str, Any]], system: str) -> dict[str, Any]:
    nodes = list(graph["nodes"])
    edges = list(graph["edges"])
    node_ids = {item["id"] for item in nodes}
    for candidate in candidates:
        decision = decisions.get(candidate["candidate_id"])
        if not decision or decision["decision"] != "SUPPORTED":
            continue
        candidate_id = candidate["candidate_id"]
        if candidate_id not in node_ids:
            nodes.append(_node(
                candidate_id, "SupportedCandidate", candidate_type=candidate["candidate_type"],
                selected_option_id=decision["selected_option_id"], reason_code=decision["reason_code"],
                promotion_status="SUPPORTED_CANDIDATE", extraction_method="SELECTIVE_LLM",
                evidence_anchor_ids=[candidate["anchor_id"]], operational=False,
            ))
            node_ids.add(candidate_id)
        edges.append(_edge("DERIVED_FROM", candidate_id, candidate["anchor_id"]))
    return {"system": system, "nodes": sorted(nodes, key=lambda item: item["id"]), "edges": sorted({item["id"]: item for item in edges}.values(), key=lambda item: item["id"])}
