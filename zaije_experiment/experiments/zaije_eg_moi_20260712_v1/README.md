# zaije_eg_moi_20260712_v1

Status: **EG_MOI_END_TO_END_PASS**

EG-MOI 5-stage pilot on the complete user-specified `자이제_1.xlsx` workbook.

- Final report: `reports/final_report.md`
- 10-slide presentation: `reports/presentation_EG_MOI_method_results_10slides.md`
- Detailed methodology: `reports/detailed_EG_MOI_full_methodology.md`
- Live Neo4j query visualizations: `visualization/live_query_results/`
- Live Neo4j visualization report: `reports/neo4j_representative_5_live_visualization_results.md`
- Gate summary: `evaluation/gate_summary.json`
- Canonical RDF: `rdf/canonical.ttl`
- SKOS: `rdf/concepts.skos.ttl`
- PROV-O: `rdf/provenance.prov.ttl`
- SHACL report: `rdf/validation_report.txt`
- Neo4j import: `neo4j/nodes.csv`, `neo4j/edges.csv`
- Neo4j 5.26+ Query UI import: `neo4j/load_csv_import_neo4j_5_26.cypher`
- Neo4j runtime validation: `neo4j/runtime_validation.json`

`EG_MOI_END_TO_END_PASS` means that the pipeline, provenance, constraints, serialization, and live Neo4j import passed. It does not claim semantic accuracy.
