# Visualization Readme

Open `kg_viewer.html` in a browser. Use filters and search to inspect Layer1, Layer2, mapping, and evidence-linked edges.

Mapping edges use the CAPE/EACL predicate names `REQUIRES_CAPABILITY` and `PROCESS_CONTEXT`.

## VS Code Remote SSH

From the repository root:

```bash
bash scripts/serve_kg_viewer.sh
```

Forward port `8765` in the VS Code Ports panel, then open:

```text
http://localhost:8765/outputs/09_visualization/kg_viewer.html
```

You can also use Command Palette -> `Simple Browser: Show` and enter the same URL.

## Other Visualization Files

- `kg_full.json`: full graph data for custom tools
- `kg_full.graphml`: importable into Gephi, yEd, Cytoscape, and other graph tools
- `kg_static_overview.svg`: static count overview
