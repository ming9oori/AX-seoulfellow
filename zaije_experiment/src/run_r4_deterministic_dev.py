#!/usr/bin/env python3
"""Build DEV B0/B1 and evaluate grounding, policy, SHACL, and metamorphic gates."""

from __future__ import annotations

import json
from pathlib import Path

import r4_ceoc as r4


def main() -> int:
    project = Path(__file__).resolve().parents[1]
    root = project / "experiments" / r4.EXPERIMENT_ID
    if json.loads((root / "reports" / "gate_r4_1.json").read_text(encoding="utf-8"))["status"] != "PASS":
        raise RuntimeError("R4-1 must pass")
    rows = r4.read_jsonl(root / "data" / "dev_exposed" / "dev_120.jsonl")
    anchors = r4.read_jsonl(root / "data" / "dev_exposed" / "anchors.jsonl")
    b0 = r4.build_graph(rows, anchors, "R4-B0")
    b1 = r4.build_graph(rows, anchors, "R4-B1")
    for name, graph in [("dev_b0", b0), ("dev_b1", b1)]:
        r4.write_jsonl(root / "runs" / name / "nodes.jsonl", graph["nodes"])
        r4.write_jsonl(root / "runs" / name / "edges.jsonl", graph["edges"])
        r4.write_json(root / "runs" / name / "metrics.json", r4.validate_graph(graph, rows))
    metrics = r4.validate_graph(b1, rows)
    fixtures = r4.metamorphic_tests()
    r4.write_jsonl(root / "fixtures" / "metamorphic" / "deterministic_results.jsonl", fixtures)
    metamorphic_accuracy = sum(item["passed"] for item in fixtures) / len(fixtures)
    passed = (
        metrics["anchor_offset_round_trip"] == 1.0
        and metrics["mention_offset_round_trip"] == 1.0
        and metrics["invalid_id_count"] == 0
        and metrics["generated_quote_rate"] == 0
        and metrics["assertion_evidence_coverage"] == 1.0
        and metrics["provenance_completeness"] == 1.0
        and metrics["critical_shacl_violation_count"] == 0
        and metrics["example_to_rule_direct_promotion"] == 0
        and metrics["rule_without_qualifying_evidence"] == 0
        and metamorphic_accuracy == 1.0
    )
    result = {
        "status": "PASS" if passed else "CONSERVATIVE_CORE_REVISE",
        "metrics": metrics, "deterministic_metamorphic_accuracy": metamorphic_accuracy,
        "fixture_count": len(fixtures), "confirmatory_api_exposure": 0, "test_access": 0,
    }
    r4.write_json(root / "reports" / "gate_r4_2.json", result)
    lines = [
        "# R4 Deterministic Core DEV Report", "", f"- Gate R4-2: **{result['status']}**",
        f"- B0 nodes/edges: `{len(b0['nodes'])}` / `{len(b0['edges'])}`",
        f"- B1 nodes/edges: `{len(b1['nodes'])}` / `{len(b1['edges'])}`",
        "- Confirmatory API exposure: `0`", "- TEST access: `0`", "",
        "| Metric | Value | Gate |", "|---|---:|---:|",
        f"| Anchor offset round-trip | {metrics['anchor_offset_round_trip']:.4f} | 1.00 |",
        f"| Mention offset round-trip | {metrics['mention_offset_round_trip']:.4f} | 1.00 |",
        f"| Assertion evidence coverage | {metrics['assertion_evidence_coverage']:.4f} | 1.00 |",
        f"| Provenance completeness | {metrics['provenance_completeness']:.4f} | 1.00 |",
        f"| Critical SHACL violations | {metrics['critical_shacl_violation_count']} | 0 |",
        f"| Example to RuleBox | {metrics['example_to_rule_direct_promotion']} | 0 |",
        f"| Rule without qualifying evidence | {metrics['rule_without_qualifying_evidence']} | 0 |",
        f"| Metamorphic accuracy | {metamorphic_accuracy:.4f} | 1.00 |",
    ]
    (root / "reports" / "deterministic_core_dev_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if passed else 4


if __name__ == "__main__":
    raise SystemExit(main())
