#!/usr/bin/env python3
"""Freeze R3 inputs, select confirmatory VALIDATION data, and preregister R4."""

from __future__ import annotations

import json
import shutil
from collections import Counter
from pathlib import Path

import r2_blre
import r3_apre
import r4_ceoc as r4


R3_ID = "zaije_ldr_r3_20260712_apre_v1"
SOURCE_HASH = "9246a6da6c7635b3f34ee55df75112eb38a2984ea06828be943dc196de5926eb"


def text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8")


def main() -> int:
    project = Path(__file__).resolve().parents[1]
    workspace = project.parent
    root = project / "experiments" / r4.EXPERIMENT_ID
    r3_root = project / "experiments" / R3_ID
    root.mkdir(parents=True, exist_ok=True)
    source = workspace / "legacy" / "자이제_1.xlsx"
    if r4.file_sha(source) != SOURCE_HASH:
        raise RuntimeError("Input binary hash mismatch")

    r3_status = json.loads((r3_root / "reference" / "status.json").read_text(encoding="utf-8"))
    if r3_status["overall_status"] != "BOUNDARY_REFERENCE_ONLY":
        raise RuntimeError("Unexpected R3 status")
    r3_gate1 = json.loads((r3_root / "reports" / "gate_r3_1.json").read_text(encoding="utf-8"))
    if r4.file_sha(project / "src" / "r3_apre.py") != r3_gate1["segmenter_source_sha256"]:
        raise RuntimeError("R3 segmenter changed after boundary lock")

    corpus = r4.read_jsonl(project / "data" / "canonical" / "corpus.jsonl")
    corpus_by_row = {row["excel_row"]: row for row in corpus}
    _, raw_records = r2_blre.read_xlsx_raw(source)
    enriched = []
    for raw in raw_records:
        base = corpus_by_row[raw["excel_row"]]
        enriched.append({**base, "raw_text": raw["text_for_llm_human"]})
    by_id = {row["evidence_id"]: row for row in enriched}

    r1_ids = set(json.loads((project / "annotation" / "pilot" / "pilot_lock.json").read_text(encoding="utf-8"))["evidence_ids"])
    r2_ids = set(json.loads((project / "annotation" / "llm_reference" / "repilot_v2" / "repilot_lock.json").read_text(encoding="utf-8"))["evidence_ids"])
    r3_ids = {row["evidence_id"] for row in r4.read_jsonl(r3_root / "data" / "r3_pilot_60_imported_unexposed.jsonl")}
    exposed_ids = r1_ids | r2_ids | r3_ids
    if len(exposed_ids) != 120:
        raise RuntimeError(f"Expected 120 exposed Evidence, got {len(exposed_ids)}")
    exposed_groups = {by_id[item]["leakage_group_id"] for item in exposed_ids}
    exposure_registry = {
        "experiment_id": r4.EXPERIMENT_ID, "evidence_count": len(exposed_ids),
        "leakage_group_count": len(exposed_groups), "evidence_ids": sorted(exposed_ids),
        "leakage_group_ids": sorted(exposed_groups),
        "sources": {"R1_PILOT": len(r1_ids), "R2_REPILOT": len(r2_ids), "R3_FRESH_NOW_DEV": len(r3_ids)},
        "r3_fresh_status": "DEV_EXPOSED_R3", "confirmatory_reuse": False,
    }
    r4.write_json(root / "locks" / "exposure_registry.json", exposure_registry)

    validation = [row for row in enriched if row["split"] == "VALIDATION" and row["evidence_id"] not in exposed_ids and row["leakage_group_id"] not in exposed_groups]
    selected, amendment = r4.select_confirmatory(validation)
    selected_ids = {row["evidence_id"] for row in selected}
    selected_groups = {row["leakage_group_id"] for row in selected}
    if len(selected) != 80 or selected_ids & exposed_ids or selected_groups & exposed_groups or any(row["split"] != "VALIDATION" for row in selected):
        raise RuntimeError("Confirmatory leakage or count error")
    confirm_path = root / "data" / "confirmatory" / "validation_80.jsonl"
    r4.write_jsonl(confirm_path, selected)
    r4.write_json(root / "locks" / "confirmatory_membership_lock.json", {
        "experiment_id": r4.EXPERIMENT_ID, "source_split": "VALIDATION", "count": 80,
        "membership_sha256": r4.file_sha(confirm_path), "evidence_ids": [row["evidence_id"] for row in selected],
        "leakage_group_ids": sorted(selected_groups), "dev_evidence_overlap": 0, "dev_group_overlap": 0,
        "test_membership_count": 0, "prior_api_exposure": 0, "membership_change_allowed": False,
        "strata": dict(Counter(r4.sample_stratum(row) for row in selected)),
    })
    r4.write_json(root / "data" / "manifests" / "confirmatory_sampling_amendment.json", amendment)

    dev_rows = [by_id[item] for item in sorted(exposed_ids)]
    dev_path = root / "data" / "dev_exposed" / "dev_120.jsonl"
    r4.write_jsonl(dev_path, dev_rows)
    dev_anchors = [r3_apre.build_atomic_anchors(row) for row in dev_rows]
    confirm_anchors = [r3_apre.build_atomic_anchors(row) for row in selected]
    r4.write_jsonl(root / "data" / "dev_exposed" / "anchors.jsonl", dev_anchors)
    r4.write_jsonl(root / "data" / "confirmatory" / "anchors.jsonl", confirm_anchors)

    boundary_path = r3_root / "reference" / "envelopes" / "claimhood_envelopes.jsonl"
    r4.write_json(root / "locks" / "r3_boundary_import_lock.json", {
        "source_experiment_id": R3_ID, "source_status_sha256": r4.file_sha(r3_root / "reference" / "status.json"),
        "boundary_file_sha256": r4.file_sha(boundary_path), "hard_keep": 64, "hard_drop": 6,
        "semantic_fields_status": "DIAGNOSTIC_ONLY", "argument_status": "NOT_BUILT",
        "segmenter_source_sha256": r3_gate1["segmenter_source_sha256"], "overwrite_parent": False,
    })
    disagreements = [row for row in r4.read_jsonl(r3_root / "reference" / "envelopes" / "field_envelopes.jsonl") if row["status"] == "QUARANTINED"]
    if len(disagreements) != 50:
        raise RuntimeError(f"Expected 50 R3 disagreements, got {len(disagreements)}")
    r4.write_jsonl(root / "data" / "dev_exposed" / "r3_cross_model_semantic_disagreements.jsonl", [
        {**row, "official_label": "CROSS_MODEL_SEMANTIC_DISAGREEMENT", "use_as_gold": False, "use_as_diagnostic_dev": True}
        for row in disagreements
    ])

    protocol = """# R4-CEOC preregistration

R4 builds an Evidence-grounded Conservative Work Ontology Core. R3 boundary outputs are fixed inputs; R3 semantic fields are diagnostic only. B0 contains structure and provenance. B1 adds deterministic explicit signals and policy-based promotion. B2 sends a locked information-value subset of gray-zone candidates to one closed-choice LLM. B3 sends every gray-zone candidate. TEST is prohibited. Confirmatory VALIDATION membership, relation registry, promotion thresholds, CQ split, model snapshot, schemas, prompts, and budget are immutable after system freeze.
"""
    text(root / "preregistration" / "r4_ceoc_protocol.md", protocol)
    text(root / "preregistration" / "relation_registry.yaml", """relations:
  - {id: REL_HAS_DEFINITION, domain: ConceptCandidate, range: DefinitionAssertion, promotion: explicit_only}
  - {id: REL_HAS_INPUT, domain: WorkUnitCandidate, range: ArtifactCandidate, promotion: explicit_or_structural}
  - {id: REL_PRODUCES_OUTPUT, domain: WorkUnitCandidate, range: ArtifactCandidate, promotion: explicit_or_structural}
  - {id: REL_PERFORMED_BY, domain: WorkUnitCandidate, range: ActorConceptCandidate, promotion: exact_argument_required}
  - {id: REL_PRECEDES, domain: WorkUnitCandidate, range: WorkUnitCandidate, promotion: explicit_sequence_only}
  - {id: REL_HAS_CONDITION, domain: AssertionCandidate, range: ConditionMention, promotion: cue_scope_required}
  - {id: REL_HAS_EXCEPTION, domain: AssertionCandidate, range: ExceptionMention, promotion: cue_scope_required}
  - {id: REL_ILLUSTRATES, domain: ExampleInstance, range: AssertionCandidate, promotion: safe}
  - {id: REL_HAS_QUANTITY_CONSTRAINT, domain: ConceptCandidate, range: QuantityMention, promotion: explicit_value_required}
  - {id: REL_ALIAS_OF, domain: ConceptCandidate, range: ConceptCandidate, promotion: exact_alias_or_closed_choice}
""")
    text(root / "preregistration" / "promotion_policy.yaml", """allow_implicit_normativity: false
allow_llm_direct_rule_promotion: false
allow_llm_generalizable_rule: false
generic_support_k: 2
explicit_deontic_requires: [cue, same_anchor_action, non_example, non_reported, non_hypothetical]
example_to_rule_direct_promotion: false
quarantined_in_operational_graph: false
statuses: [EVIDENCE_ONLY, CANDIDATE, SUPPORTED_CANDIDATE, EXPLICIT_ASSERTION, PROMOTED_TBOX, PROMOTED_ABOX, PROMOTED_RULEBOX, QUARANTINED, REJECTED]
""")
    text(root / "preregistration" / "shacl_policy.yaml", """critical_shapes:
  - promoted_assertion_requires_evidence
  - explicit_deontic_rule_requires_cue
  - cue_requires_exact_span
  - quantity_requires_value_or_range
  - promoted_relation_requires_subject_object
  - example_not_rulebox
  - reported_view_not_rulebox
  - quarantined_not_operational
  - neo4j_edge_references_rdf_assertion
critical_violation_max: 0
overall_violation_rate_max: 0.01
""")
    text(root / "preregistration" / "llm_selection_policy.yaml", """closed_choice_only: true
free_quote_generation: false
free_concept_generation: false
free_relation_generation: false
model_candidates: [gpt-4.1-2025-04-14]
budget_sweep: [0.0, 0.05, 0.10, 0.20, 0.40, 1.0]
provisional_b2_budget: 0.20
max_same_candidate_type: 0.35
deterministic_exploration: 0.05
dev_request_cap: 500
confirmatory_request_cap: 1200
""")
    cq = {
        "dev": [
            {"cq_id": "CQD1", "type": "EXPLICIT_DEFINITION", "question": "명시적으로 정의된 용어와 정의문은 무엇인가?"},
            {"cq_id": "CQD2", "type": "TEMPLATE_FIELD", "question": "명시된 표 또는 양식 필드는 무엇인가?"},
            {"cq_id": "CQD3", "type": "EXPLICIT_RULE", "question": "명시적 규범 cue를 가진 규칙은 무엇인가?"},
        ],
        "confirmatory": [
            {"cq_id": "CQT1", "type": "EXPLICIT_DEFINITION", "question": "명시적으로 정의된 용어와 정의문은 무엇인가?"},
            {"cq_id": "CQT2", "type": "TEMPLATE_FIELD", "question": "표와 양식에서 명시된 필드는 무엇인가?"},
            {"cq_id": "CQT3", "type": "EXPLICIT_SEQUENCE", "question": "번호 또는 순서 표현으로 연결된 단계는 무엇인가?"},
            {"cq_id": "CQT4", "type": "QUANTITY_CONSTRAINT", "question": "명시된 수량·범위 제약은 무엇인가?"},
            {"cq_id": "CQT5", "type": "EXPLICIT_RULE", "question": "명시 cue와 근거를 가진 규칙은 무엇인가?"},
        ],
        "locked_before_confirmatory": True,
    }
    r4.write_json(root / "preregistration" / "cq_split_lock.json", cq)
    text(root / "schema" / "core_schema.ttl", """@prefix ceoc: <https://example.org/ceoc/> .
@prefix prov: <http://www.w3.org/ns/prov#> .
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .
ceoc:Anchor a ceoc:Class .
ceoc:Assertion a ceoc:Class .
ceoc:ExplicitDeonticRule a ceoc:Class .
ceoc:TemplateField a ceoc:Class .
ceoc:ExampleInstance a ceoc:Class .
ceoc:Concept a ceoc:Class .
""")
    text(root / "schema" / "shapes.ttl", """@prefix ceoc: <https://example.org/ceoc/> .
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix prov: <http://www.w3.org/ns/prov#> .
ceoc:PromotedAssertionShape a sh:NodeShape ; sh:targetClass ceoc:Assertion ; sh:property [ sh:path prov:wasDerivedFrom ; sh:minCount 1 ] .
ceoc:ExplicitRuleShape a sh:NodeShape ; sh:targetClass ceoc:ExplicitDeonticRule ; sh:property [ sh:path ceoc:hasDeonticCue ; sh:minCount 1 ] .
""")
    text(root / "schema" / "neo4j_projection.yaml", """canonical_source: rdf
node_labels: [Document, Chapter, Section, EvidenceBundle, Anchor, Concept, Assertion, ExplicitDeonticRule, TemplateField, ExampleInstance, ExtractionRun]
required_edge_properties: [canonicalAssertionId, evidenceAnchorIds, extractionRunId]
exclude_statuses: [QUARANTINED, REJECTED, CANDIDATE, EVIDENCE_ONLY]
""")

    r4.write_json(root / "locks" / "input_lock.json", {"path": str(source), "binary_sha256": SOURCE_HASH, "sheet": "clean_sentences", "evidence_count": 1366})
    lock_paths = [
        root / "locks" / "input_lock.json", root / "locks" / "r3_boundary_import_lock.json",
        root / "locks" / "exposure_registry.json", root / "locks" / "confirmatory_membership_lock.json",
        root / "preregistration" / "relation_registry.yaml", root / "preregistration" / "promotion_policy.yaml",
        root / "preregistration" / "shacl_policy.yaml", root / "preregistration" / "llm_selection_policy.yaml",
        root / "preregistration" / "cq_split_lock.json", root / "schema" / "core_schema.ttl",
        root / "schema" / "shapes.ttl", root / "schema" / "neo4j_projection.yaml",
    ]
    r4.write_json(root / "locks" / "phase_r4_1_hashes.json", {str(path.relative_to(root)): r4.file_sha(path) for path in lock_paths})
    r4.write_json(root / "reports" / "gate_r4_0.json", {
        "status": "PASS", "hash_match": 1.0, "exposed_registry_completeness": 1.0,
        "test_access": 0, "parent_overwrite": 0, "confirmatory_count": 80,
        "confirmatory_prior_api_exposure": 0,
    })
    r4.write_json(root / "reports" / "gate_r4_1.json", {
        "status": "PASS", "relation_registry_locked": True, "promotion_policy_locked": True,
        "shacl_policy_locked": True, "cq_split_locked": True, "llm_budget_policy_locked": True,
        "test_access": 0,
    })
    text(root / "reports" / "r3_reinterpretation_report.md", """# R3 import and reinterpretation

- R3 boundary: 64 HARD_KEEP and 6 HARD_DROP, imported by hash.
- R3 semantic fields: DIAGNOSTIC_ONLY; never used as ontology facts.
- R3 quarantined fields: 50 CROSS_MODEL_SEMANTIC_DISAGREEMENT records, DEV diagnostic only.
- R3 fresh 60: DEV_EXPOSED_R3; confirmatory and TEST reuse prohibited.
- Parent artifacts overwritten: 0.
""")
    text(root / "reports" / "phase0_lock_report.md", f"""# R4-0/R4-1 Lock Report

- R4-0: **PASS**
- R4-1: **PASS**
- Exposed DEV Evidence: `{len(exposed_ids)}`
- Confirmatory VALIDATION Evidence: `80`
- Confirmatory strata: `{dict(Counter(r4.sample_stratum(row) for row in selected))}`
- Confirmatory membership SHA-256: `{r4.file_sha(confirm_path)}`
- DEV Evidence overlap: `0`
- DEV leakage-group overlap: `0`
- TEST membership/access: `0`
- Confirmatory API exposure: `0`
""")
    print(json.dumps({
        "experiment_id": r4.EXPERIMENT_ID, "gate_r4_0": "PASS", "gate_r4_1": "PASS",
        "dev_exposed": len(dev_rows), "confirmatory": len(selected),
        "confirmatory_strata": dict(Counter(r4.sample_stratum(row) for row in selected)),
        "dev_anchor_count": sum(len(item["anchors"]) for item in dev_anchors),
        "confirmatory_anchor_count": sum(len(item["anchors"]) for item in confirm_anchors),
        "confirmatory_api_exposure": 0, "test_access": 0,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
