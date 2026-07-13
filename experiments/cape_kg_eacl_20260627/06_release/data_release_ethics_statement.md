# CAPE-KG Data Release and Ethics Statement

Generated for the CAPE-KG EACL pre-human handoff package.

This document is a release and ethics planning artifact. It is not human-gold performance evidence and must not be used as a final result table.

## Claim Status

- Current claim status: pending human-gold annotation, inter-annotator agreement, adjudication, and proposed-method human-gold scoring.
- Current release status: internal reproducibility package and public-safe skeleton are prepared, but external publication still requires final rights review.
- Current human evidence status: no adjudicated human-gold chunks or gold items are available yet.

## Data Sources

The experiment combines four classes of material:

| Source class | Role in the experiment | Release treatment |
| --- | --- | --- |
| Korean bid/proposal source text | Domain corpus for procedural KG construction | Restricted unless rights are cleared |
| NCS/PCF standard taxonomy data | Standard competency and process reference layers | Cite source and verify redistribution terms before publication |
| Public benchmark data | External procedural and ontology-driven KG checks | Follow original benchmark licenses and citation requirements |
| Synthetic examples | Format and reproducibility demonstration | Public-safe by design |

## Release Partition

The release is intentionally split into two tracks.

| Track | Intended audience | Contents | Exclusions |
| --- | --- | --- | --- |
| Internal reproducibility package | Project team and authorized reviewers | Full experiment artifacts, hashes, validation reports, review handoff materials, and source-derived intermediate outputs | Not for external publication without rights review |
| Public-safe skeleton | External paper reviewers and future reproducers | Schema, prompts, evaluation scripts, public benchmark adapters, aggregate diagnostics, synthetic examples, RDF/SHACL shapes, and visualization scaffolds | Raw source text, source-derived review workbooks, and private human-review return files |

This split is required because the core domain corpus may contain copyrighted or restricted text. The public-safe skeleton therefore prioritizes inspectable methodology over raw-text redistribution.

## Reproducibility Mitigation

If the raw source corpus cannot be released, the paper should still provide the following reproducibility path:

| Reproducibility object | Purpose |
| --- | --- |
| CAPE schema and competency questions | Defines the extraction target and evaluation concepts |
| Prompt files | Makes baseline, ablation, and proposed-method instructions inspectable |
| Evaluation scripts | Allows rerunning metrics on returned or substitute data |
| Public benchmark adapters | Allows external sanity checks on open data |
| Synthetic examples | Shows expected JSONL structure, evidence anchors, and schema-conformant outputs |
| External resource license report | Records public benchmark licenses, citation URLs, and rights-review boundaries |
| Provenance manifest and checksums | Makes file lineage and bundle integrity auditable |
| RDF/SHACL export | Makes KG structure and validation constraints inspectable |

The paper should explicitly state that synthetic examples and public benchmark diagnostics are reproducibility aids, not substitutes for human-gold evaluation on the target corpus.

## Copyright and Licensing

- Do not publish raw domain text unless redistribution rights are explicitly cleared.
- Do not publish source-derived review packages as public artifacts.
- Cite NCS, PCF, PAGED, and Text2KGBench according to their source terms.
- Keep public examples synthetic or otherwise rights-cleared.
- Keep checksum and provenance records for any artifact used in a claim.

## Privacy and Sensitive Information

The current corpus is treated as potentially sensitive enterprise procedural material. Before any external release, inspect for:

- personal names, contact details, or organization-specific identifiers;
- confidential business procedures or proposal strategy details;
- source text copied from copyrighted documents;
- reviewer comments or private human-review decisions.

Any such material should be removed, anonymized, or withheld from the public-safe release.

## Human Review Ethics

The annotation and mapping review process should follow these rules:

- Reviewers should receive only the minimum necessary text and metadata for the assigned task.
- Reviewer identities should not be exposed in public artifacts.
- Human-review timing and correction logs should be reported only in aggregate.
- Disagreements should be adjudicated through the documented protocol before being used as gold evidence.
- IAA should be reported as a reliability measure, not as a personal reviewer evaluation.

## LLM Use and Risk Disclosure

The paper should disclose that LLMs are used for extraction, baseline generation, ablation generation, and diagnostic scoring support. It should also state that:

- LLM outputs may hallucinate nodes, edges, or evidence support;
- evidence anchoring and schema validation reduce but do not eliminate this risk;
- all final performance claims require adjudicated human-gold comparison;
- silver/proxy diagnostics are engineering evidence only.

## Public Statement for the Paper

A concise paper-ready statement can be:

> The target domain corpus contains source-derived bid/proposal text whose redistribution requires rights review. We therefore separate an internal reproducibility package from a public-safe skeleton containing schema, prompts, evaluation scripts, public benchmark adapters, synthetic examples, provenance records, and validation reports. All final extraction and mapping performance claims are reserved for adjudicated human-gold evaluation; synthetic and silver/proxy diagnostics are not treated as final evidence.

## Status Summary

| Item | Status |
| --- | --- |
| Raw source text public release | Restricted pending rights review |
| Public-safe schema/prompt/script release | Prepared |
| Synthetic examples | Prepared |
| Public benchmark adapters | Prepared |
| External resource license report | Prepared |
| Human-gold labels | Pending |
| IAA and adjudication | Pending |
| Expert mapping review | Pending |
| Final paper performance claims | Not yet claimable |
