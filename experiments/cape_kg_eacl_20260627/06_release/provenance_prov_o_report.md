# CAPE-KG PROV-O Export Report

Generated: 2026-06-29T18:56:42.347549+00:00
Claim status: `prov_o_export_ready_not_human_gold_evidence`

This report accompanies the W3C PROV-O Turtle export for the CAPE-KG experiment package. It records provenance for source files, prompt/schema files, LLM raw and validated outputs, evaluation files, human-review handoff files, and release artifacts.

## Outputs

- Turtle: `experiments/cape_kg_eacl_20260627/06_release/provenance_prov_o.ttl`
- Summary JSON: `experiments/cape_kg_eacl_20260627/06_release/provenance_prov_o_summary.json`
- Report: `experiments/cape_kg_eacl_20260627/06_release/provenance_prov_o_report.md`

## Counts

| Item | Value |
|---|---:|
| Entities | 287 |
| Activities | 26 |
| Agents | 6 |
| File entities | 286 |
| LLM runs | 23 |
| Turtle predicate statements | 3502 |

## Interpretation

- `prov:Entity` nodes represent files and derived artifacts, identified by path and SHA-256 when available.
- `prov:Activity` nodes represent the experiment package, LLM extraction runs, human-review handoff preparation, and release-bundle preparation.
- `prov:SoftwareAgent` nodes represent the executable CAPE-KG pipeline and indexed model paths.
- This is reproducibility and lineage evidence. It is not human-gold performance evidence.

## Source Manifest

- Manifest status: `provenance_manifest_ready_not_human_gold_evidence`
- Manifest generated at: `2026-06-29T18:56:42.293489+00:00`
- Missing required provenance files: `0`
