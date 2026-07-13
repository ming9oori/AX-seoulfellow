#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build a static HTML workbench for CAPE-KG NCS/PCF mapping review."""

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_EXP_DIR = Path("experiments/cape_kg_eacl_20260627")


def read_json(path, default=None):
    path = Path(path)
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path):
    rows = []
    with Path(path).open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_json(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def html_json(data):
    return json.dumps(data, ensure_ascii=False).replace("</", "<\\/")


def build_html(rows, generated_at):
    payload = {
        "generated_at_utc": generated_at,
        "items": rows,
        "decision_values": ["accepted", "rejected", "unsure"],
        "grade_values": ["0", "1", "2", "3"],
        "quality_values": ["1", "2", "3", "4", "5"],
    }
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>CAPE-KG Mapping Review</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #f6f7f9;
      --panel: #ffffff;
      --line: #d9dee7;
      --text: #1d2433;
      --muted: #687386;
      --blue: #2563eb;
      --green: #15803d;
      --red: #b91c1c;
      --amber: #b45309;
      --shadow: 0 1px 2px rgba(15, 23, 42, 0.08);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      color: var(--text);
      background: var(--bg);
      font-size: 14px;
    }}
    button, input, select, textarea {{
      font: inherit;
    }}
    .app {{
      min-height: 100vh;
      display: grid;
      grid-template-rows: auto 1fr;
    }}
    header {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      padding: 12px 16px;
      border-bottom: 1px solid var(--line);
      background: var(--panel);
      position: sticky;
      top: 0;
      z-index: 10;
    }}
    .brand {{
      display: flex;
      align-items: baseline;
      gap: 12px;
      min-width: 240px;
    }}
    h1 {{
      font-size: 18px;
      line-height: 1.2;
      margin: 0;
      letter-spacing: 0;
    }}
    .meta {{
      color: var(--muted);
      font-size: 12px;
      white-space: nowrap;
    }}
    .toolbar {{
      display: flex;
      align-items: center;
      gap: 8px;
      flex-wrap: wrap;
      justify-content: flex-end;
    }}
    .toolbar input[type="search"], .toolbar input[type="text"], .toolbar select {{
      height: 34px;
      border: 1px solid var(--line);
      background: #fff;
      color: var(--text);
      padding: 0 10px;
      border-radius: 6px;
      min-width: 150px;
    }}
    .btn {{
      height: 34px;
      border: 1px solid var(--line);
      background: #fff;
      color: var(--text);
      border-radius: 6px;
      padding: 0 10px;
      cursor: pointer;
      box-shadow: var(--shadow);
    }}
    .btn:hover {{ border-color: #9aa7bb; }}
    .btn.primary {{
      background: var(--blue);
      border-color: var(--blue);
      color: #fff;
    }}
    main {{
      display: grid;
      grid-template-columns: 320px minmax(0, 1fr);
      min-height: 0;
    }}
    aside {{
      border-right: 1px solid var(--line);
      background: #fbfcfe;
      overflow: auto;
      padding: 10px;
    }}
    .group {{
      width: 100%;
      display: grid;
      gap: 4px;
      text-align: left;
      border: 1px solid transparent;
      border-radius: 6px;
      background: transparent;
      padding: 9px;
      cursor: pointer;
    }}
    .group:hover {{ background: #eef2f7; }}
    .group.active {{
      background: #eaf1ff;
      border-color: #b8cdfd;
    }}
    .group-top {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
    }}
    .source {{
      font-weight: 650;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }}
    .pill {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-width: 42px;
      height: 22px;
      padding: 0 7px;
      border-radius: 999px;
      background: #e5e7eb;
      color: #334155;
      font-size: 12px;
      font-weight: 650;
    }}
    .pill.ncs {{ background: #dbeafe; color: #1d4ed8; }}
    .pill.pcf {{ background: #dcfce7; color: #166534; }}
    .progress {{
      color: var(--muted);
      font-size: 12px;
    }}
    .content {{
      min-width: 0;
      overflow: auto;
      padding: 16px;
    }}
    .summary {{
      display: grid;
      grid-template-columns: repeat(4, minmax(110px, 1fr));
      gap: 10px;
      margin-bottom: 14px;
    }}
    .stat {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 10px;
      box-shadow: var(--shadow);
    }}
    .stat-value {{
      font-size: 22px;
      line-height: 1.1;
      font-weight: 750;
    }}
    .stat-label {{
      color: var(--muted);
      font-size: 12px;
      margin-top: 4px;
    }}
    .source-head {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 14px;
      margin-bottom: 12px;
      box-shadow: var(--shadow);
    }}
    .source-title {{
      display: flex;
      align-items: center;
      gap: 10px;
      margin-bottom: 6px;
    }}
    .source-title h2 {{
      margin: 0;
      font-size: 20px;
      line-height: 1.25;
      letter-spacing: 0;
    }}
    .source-id {{
      color: var(--muted);
      font-size: 12px;
      overflow-wrap: anywhere;
    }}
    .candidate-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(340px, 1fr));
      gap: 12px;
    }}
    .card {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      box-shadow: var(--shadow);
      display: grid;
      grid-template-rows: auto 1fr auto;
      min-height: 330px;
    }}
    .card.accepted {{ border-color: rgba(21, 128, 61, 0.55); }}
    .card.rejected {{ border-color: rgba(185, 28, 28, 0.45); }}
    .card.unsure {{ border-color: rgba(180, 83, 9, 0.55); }}
    .card-head {{
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 10px;
      padding: 12px;
      border-bottom: 1px solid var(--line);
    }}
    .target {{
      min-width: 0;
    }}
    .target h3 {{
      margin: 0 0 5px;
      font-size: 16px;
      line-height: 1.3;
      letter-spacing: 0;
    }}
    .target-meta {{
      color: var(--muted);
      font-size: 12px;
      overflow-wrap: anywhere;
    }}
    .rank {{
      width: 42px;
      height: 42px;
      border-radius: 8px;
      background: #eef2ff;
      color: #3730a3;
      display: grid;
      place-items: center;
      font-size: 18px;
      font-weight: 800;
      flex: 0 0 auto;
    }}
    .card-body {{
      padding: 12px;
      display: grid;
      gap: 10px;
      align-content: start;
    }}
    .reason {{
      line-height: 1.45;
      color: #334155;
      min-height: 42px;
    }}
    .score-row {{
      display: grid;
      grid-template-columns: 76px 1fr 54px;
      gap: 8px;
      align-items: center;
      font-size: 12px;
      color: var(--muted);
    }}
    .bar {{
      height: 7px;
      border-radius: 999px;
      overflow: hidden;
      background: #e5e7eb;
    }}
    .bar > span {{
      display: block;
      height: 100%;
      background: #64748b;
    }}
    .card-actions {{
      border-top: 1px solid var(--line);
      padding: 12px;
      display: grid;
      gap: 10px;
    }}
    .segments, .grades {{
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
    }}
    .seg {{
      min-width: 74px;
      height: 32px;
      border: 1px solid var(--line);
      background: #fff;
      border-radius: 6px;
      cursor: pointer;
    }}
    .seg.active.accepted {{ background: #dcfce7; border-color: #86efac; color: var(--green); }}
    .seg.active.rejected {{ background: #fee2e2; border-color: #fecaca; color: var(--red); }}
    .seg.active.unsure {{ background: #fef3c7; border-color: #fde68a; color: var(--amber); }}
    .seg.grade.active {{ background: #e0f2fe; border-color: #7dd3fc; color: #075985; }}
    textarea {{
      width: 100%;
      min-height: 70px;
      resize: vertical;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 8px;
      color: var(--text);
      background: #fff;
    }}
    .empty {{
      padding: 48px;
      color: var(--muted);
      text-align: center;
    }}
    @media (max-width: 900px) {{
      header {{
        align-items: flex-start;
        flex-direction: column;
      }}
      .toolbar {{
        justify-content: flex-start;
      }}
      main {{
        grid-template-columns: 1fr;
      }}
      aside {{
        max-height: 260px;
        border-right: 0;
        border-bottom: 1px solid var(--line);
      }}
      .summary {{
        grid-template-columns: repeat(2, minmax(110px, 1fr));
      }}
      .candidate-grid {{
        grid-template-columns: 1fr;
      }}
    }}
  </style>
</head>
<body>
<div class="app">
  <header>
    <div class="brand">
      <h1>CAPE-KG Mapping Review</h1>
      <div class="meta" id="generatedAt"></div>
    </div>
    <div class="toolbar">
      <input id="reviewer" type="text" placeholder="reviewer_id">
      <select id="standardFilter" aria-label="standard filter">
        <option value="all">All standards</option>
        <option value="NCS">NCS</option>
        <option value="PCF">PCF</option>
      </select>
      <select id="statusFilter" aria-label="status filter">
        <option value="all">All rows</option>
        <option value="pending">Pending</option>
        <option value="completed">Completed</option>
      </select>
      <input id="search" type="search" placeholder="search task or target">
      <input id="importFile" type="file" accept=".jsonl,.json" hidden>
      <button class="btn" id="importBtn" type="button">Import</button>
      <button class="btn" id="saveBtn" type="button">Save Draft</button>
      <button class="btn primary" id="exportBtn" type="button">Export JSONL</button>
    </div>
  </header>
  <main>
    <aside id="groupList"></aside>
    <section class="content">
      <div class="summary" id="summary"></div>
      <div id="reviewPanel"></div>
    </section>
  </main>
</div>
<script id="mapping-data" type="application/json">{html_json(payload)}</script>
<script>
const payload = JSON.parse(document.getElementById("mapping-data").textContent);
const storageKey = "cape_mapping_review_v1";
let items = structuredClone(payload.items);
let activeGroupKey = "";

function norm(value) {{
  return String(value || "").trim().toLowerCase();
}}

function isCompleted(row) {{
  const status = norm(row.review_status);
  const decision = norm(row.expert_decision);
  return ["completed", "reviewed", "adjudicated", "final"].includes(status) ||
    ["accepted", "accept", "rejected", "reject", "unsure"].includes(decision);
}}

function groupKey(row) {{
  return `${{row.standard}}::${{row.source_id}}`;
}}

function groupedItems() {{
  const standard = document.getElementById("standardFilter").value;
  const status = document.getElementById("statusFilter").value;
  const search = norm(document.getElementById("search").value);
  const groups = new Map();
  for (const row of items) {{
    if (standard !== "all" && row.standard !== standard) continue;
    if (status === "pending" && isCompleted(row)) continue;
    if (status === "completed" && !isCompleted(row)) continue;
    const haystack = norm([row.source_label, row.source_id, row.target_label, row.target_id, row.reason].join(" "));
    if (search && !haystack.includes(search)) continue;
    const key = groupKey(row);
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(row);
  }}
  return Array.from(groups.entries()).map(([key, rows]) => {{
    rows.sort((a, b) => Number(a.rank || 999) - Number(b.rank || 999));
    return {{ key, rows }};
  }}).sort((a, b) => {{
    const ar = a.rows[0];
    const br = b.rows[0];
    return (ar.standard + ar.source_label).localeCompare(br.standard + br.source_label);
  }});
}}

function computeStats() {{
  const total = items.length;
  const completed = items.filter(isCompleted).length;
  const accepted = items.filter(row => norm(row.expert_decision) === "accepted" || ["2", "3"].includes(String(row.relevance_grade || ""))).length;
  const qualityScored = items.filter(row => ["1", "2", "3", "4", "5"].includes(String(row.explanation_quality_score || ""))).length;
  const groups = new Set(items.map(groupKey)).size;
  return {{ total, completed, accepted, qualityScored, groups }};
}}

function renderSummary() {{
  const stats = computeStats();
  const cells = [
    ["Rows", stats.total],
    ["Completed", stats.completed],
    ["Positive", stats.accepted],
    ["Explanation scores", stats.qualityScored],
    ["Task groups", stats.groups],
  ];
  document.getElementById("summary").innerHTML = cells.map(([label, value]) => `
    <div class="stat"><div class="stat-value">${{value}}</div><div class="stat-label">${{label}}</div></div>
  `).join("");
}}

function renderGroups() {{
  const groups = groupedItems();
  const list = document.getElementById("groupList");
  if (!groups.length) {{
    list.innerHTML = '<div class="empty">No rows</div>';
    document.getElementById("reviewPanel").innerHTML = '<div class="empty">No selected group</div>';
    return;
  }}
  if (!groups.some(group => group.key === activeGroupKey)) activeGroupKey = groups[0].key;
  list.innerHTML = groups.map(group => {{
    const row = group.rows[0];
    const done = group.rows.filter(isCompleted).length;
    const cls = row.standard === "NCS" ? "ncs" : "pcf";
    return `
      <button class="group ${{group.key === activeGroupKey ? "active" : ""}}" data-group="${{escapeAttr(group.key)}}">
        <div class="group-top">
          <span class="source">${{escapeHtml(row.source_label)}}</span>
          <span class="pill ${{cls}}">${{row.standard}}</span>
        </div>
        <div class="progress">${{done}}/${{group.rows.length}} reviewed</div>
      </button>
    `;
  }}).join("");
  list.querySelectorAll(".group").forEach(btn => {{
    btn.addEventListener("click", () => {{
      activeGroupKey = btn.dataset.group;
      render();
    }});
  }});
  renderPanel(groups.find(group => group.key === activeGroupKey));
}}

function renderPanel(group) {{
  const panel = document.getElementById("reviewPanel");
  if (!group) {{
    panel.innerHTML = '<div class="empty">No selected group</div>';
    return;
  }}
  const source = group.rows[0];
  const cls = source.standard === "NCS" ? "ncs" : "pcf";
  panel.innerHTML = `
    <div class="source-head">
      <div class="source-title">
        <span class="pill ${{cls}}">${{source.standard}}</span>
        <h2>${{escapeHtml(source.source_label)}}</h2>
      </div>
      <div class="source-id">${{escapeHtml(source.source_id)}} · ${{escapeHtml(source.source_type || "")}}</div>
    </div>
    <div class="candidate-grid">
      ${{group.rows.map(renderCard).join("")}}
    </div>
  `;
  panel.querySelectorAll("[data-decision]").forEach(btn => {{
    btn.addEventListener("click", () => setDecision(btn.dataset.mapping, btn.dataset.decision));
  }});
  panel.querySelectorAll("[data-grade]").forEach(btn => {{
    btn.addEventListener("click", () => setGrade(btn.dataset.mapping, btn.dataset.grade));
  }});
  panel.querySelectorAll("[data-quality]").forEach(btn => {{
    btn.addEventListener("click", () => setQuality(btn.dataset.mapping, btn.dataset.quality));
  }});
  panel.querySelectorAll("textarea[data-comment]").forEach(area => {{
    area.addEventListener("input", () => updateField(area.dataset.comment, "comment", area.value));
  }});
}}

function renderCard(row) {{
  const decision = norm(row.expert_decision);
  const cardClass = ["accepted", "rejected", "unsure"].includes(decision) ? decision : "";
  const breakdown = row.score_breakdown || {{}};
  const scoreRows = Object.entries(breakdown).map(([key, value]) => {{
    const num = Number(value || 0);
    const pct = Math.max(0, Math.min(100, num * 100));
    return `
      <div class="score-row">
        <span>${{escapeHtml(key)}}</span>
        <span class="bar"><span style="width:${{pct}}%"></span></span>
        <span>${{Number.isFinite(num) ? num.toFixed(3) : "0.000"}}</span>
      </div>
    `;
  }}).join("");
  return `
    <article class="card ${{cardClass}}">
      <div class="card-head">
        <div class="target">
          <h3>${{escapeHtml(row.target_label)}}</h3>
          <div class="target-meta">${{escapeHtml(row.target_type || "")}} · ${{escapeHtml(row.target_id || "")}}</div>
        </div>
        <div class="rank">${{escapeHtml(row.rank)}}</div>
      </div>
      <div class="card-body">
        <div class="target-meta">score ${{Number(row.score || 0).toFixed(4)}} · ${{escapeHtml(row.mapping_type || "")}}</div>
        <div class="reason">${{escapeHtml(row.reason || "")}}</div>
        <div>${{scoreRows}}</div>
      </div>
      <div class="card-actions">
        <div class="segments">
          ${{decisionButton(row, "accepted", "Accept")}}
          ${{decisionButton(row, "rejected", "Reject")}}
          ${{decisionButton(row, "unsure", "Unsure")}}
          ${{decisionButton(row, "", "Clear")}}
        </div>
        <div class="grades">
          ${{["0", "1", "2", "3"].map(grade => gradeButton(row, grade)).join("")}}
        </div>
        <div class="grades">
          ${{["1", "2", "3", "4", "5"].map(score => qualityButton(row, score)).join("")}}
        </div>
        <textarea data-comment="${{escapeAttr(row.mapping_id)}}" placeholder="comment">${{escapeHtml(row.comment || "")}}</textarea>
      </div>
    </article>
  `;
}}

function decisionButton(row, value, label) {{
  const active = norm(row.expert_decision) === value ? "active" : "";
  const cls = value || "clear";
  return `<button class="seg ${{cls}} ${{active}}" data-mapping="${{escapeAttr(row.mapping_id)}}" data-decision="${{escapeAttr(value)}}" type="button">${{label}}</button>`;
}}

function gradeButton(row, value) {{
  const active = String(row.relevance_grade || "") === value ? "active" : "";
  return `<button class="seg grade ${{active}}" data-mapping="${{escapeAttr(row.mapping_id)}}" data-grade="${{value}}" type="button">Grade ${{value}}</button>`;
}}

function qualityButton(row, value) {{
  const active = String(row.explanation_quality_score || "") === value ? "active" : "";
  return `<button class="seg grade ${{active}}" data-mapping="${{escapeAttr(row.mapping_id)}}" data-quality="${{value}}" type="button">Reason ${{value}}</button>`;
}}

function findItem(mappingId) {{
  return items.find(row => row.mapping_id === mappingId);
}}

function setDecision(mappingId, decision) {{
  const row = findItem(mappingId);
  if (!row) return;
  row.expert_decision = decision;
  row.review_status = row.relevance_grade || row.expert_decision || row.explanation_quality_score ? "completed" : "pending_expert_review";
  row.reviewer_id = document.getElementById("reviewer").value || row.reviewer_id || "";
  row.claim_status = row.review_status === "completed" ? "expert_reviewed_pending_evaluation" : "not_gold_until_expert_reviewed";
  saveDraft(false);
  render();
}}

function setGrade(mappingId, grade) {{
  const row = findItem(mappingId);
  if (!row) return;
  row.relevance_grade = String(row.relevance_grade || "") === grade ? "" : grade;
  row.review_status = row.relevance_grade || row.expert_decision || row.explanation_quality_score ? "completed" : "pending_expert_review";
  row.reviewer_id = document.getElementById("reviewer").value || row.reviewer_id || "";
  row.claim_status = row.review_status === "completed" ? "expert_reviewed_pending_evaluation" : "not_gold_until_expert_reviewed";
  saveDraft(false);
  render();
}}

function setQuality(mappingId, score) {{
  const row = findItem(mappingId);
  if (!row) return;
  row.explanation_quality_score = String(row.explanation_quality_score || "") === score ? "" : score;
  row.review_status = row.relevance_grade || row.expert_decision || row.explanation_quality_score ? "completed" : "pending_expert_review";
  row.reviewer_id = document.getElementById("reviewer").value || row.reviewer_id || "";
  row.claim_status = row.review_status === "completed" ? "expert_reviewed_pending_evaluation" : "not_gold_until_expert_reviewed";
  saveDraft(false);
  render();
}}

function updateField(mappingId, field, value) {{
  const row = findItem(mappingId);
  if (!row) return;
  row[field] = value;
  row.reviewer_id = document.getElementById("reviewer").value || row.reviewer_id || "";
  saveDraft(false);
}}

function saveDraft(showMessage = true) {{
  localStorage.setItem(storageKey, JSON.stringify({{ items, reviewer: document.getElementById("reviewer").value || "" }}));
  if (showMessage) document.getElementById("saveBtn").textContent = "Saved";
  if (showMessage) setTimeout(() => document.getElementById("saveBtn").textContent = "Save Draft", 900);
}}

function loadDraft() {{
  const raw = localStorage.getItem(storageKey);
  if (!raw) return;
  try {{
    const draft = JSON.parse(raw);
    if (Array.isArray(draft.items) && draft.items.length === items.length) items = draft.items;
    if (draft.reviewer) document.getElementById("reviewer").value = draft.reviewer;
  }} catch (err) {{
    console.warn(err);
  }}
}}

function exportJsonl() {{
  const text = items.map(row => JSON.stringify(row)).join("\\n") + "\\n";
  const blob = new Blob([text], {{ type: "application/jsonl;charset=utf-8" }});
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "mapping_review_items.reviewed.jsonl";
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}}

function importRows(file) {{
  const reader = new FileReader();
  reader.onload = () => {{
    const text = String(reader.result || "");
    let incoming = [];
    try {{
      if (file.name.endsWith(".json")) {{
        const parsed = JSON.parse(text);
        incoming = Array.isArray(parsed) ? parsed : parsed.items || [];
      }} else {{
        incoming = text.split(/\\r?\\n/).filter(Boolean).map(line => JSON.parse(line));
      }}
    }} catch (err) {{
      alert("Import failed: " + err.message);
      return;
    }}
    const byId = new Map(items.map(row => [row.mapping_id, row]));
    let merged = 0;
    for (const row of incoming) {{
      if (!row.mapping_id || !byId.has(row.mapping_id)) continue;
      Object.assign(byId.get(row.mapping_id), row);
      merged += 1;
    }}
    saveDraft(false);
    render();
    alert(`Imported ${{merged}} rows`);
  }};
  reader.readAsText(file);
}}

function escapeHtml(value) {{
  return String(value ?? "").replace(/[&<>"']/g, ch => ({{ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }}[ch]));
}}

function escapeAttr(value) {{
  return escapeHtml(value).replace(/`/g, "&#96;");
}}

function render() {{
  renderSummary();
  renderGroups();
}}

document.getElementById("generatedAt").textContent = payload.generated_at_utc;
document.getElementById("standardFilter").addEventListener("change", () => {{ activeGroupKey = ""; render(); }});
document.getElementById("statusFilter").addEventListener("change", () => {{ activeGroupKey = ""; render(); }});
document.getElementById("search").addEventListener("input", () => {{ activeGroupKey = ""; render(); }});
document.getElementById("reviewer").addEventListener("input", () => saveDraft(false));
document.getElementById("saveBtn").addEventListener("click", () => saveDraft(true));
document.getElementById("exportBtn").addEventListener("click", exportJsonl);
document.getElementById("importBtn").addEventListener("click", () => document.getElementById("importFile").click());
document.getElementById("importFile").addEventListener("change", event => {{
  const file = event.target.files && event.target.files[0];
  if (file) importRows(file);
  event.target.value = "";
}});
loadDraft();
render();
</script>
</body>
</html>
"""


def run(args):
    exp_dir = Path(args.experiment_dir)
    review_dir = exp_dir / "01_data/mapping_review"
    review_file = review_dir / "mapping_review_items.jsonl"
    rows = read_jsonl(review_file)
    generated_at = datetime.now(timezone.utc).isoformat()
    html_path = review_dir / "mapping_review_workbench.html"
    write_text(html_path, build_html(rows, generated_at))

    manifest_path = review_dir / "mapping_review_manifest.json"
    manifest = read_json(manifest_path, {}) or {}
    by_standard = Counter(row.get("standard") for row in rows)
    manifest.update(
        {
            "mapping_review_workbench": str(html_path),
            "workbench_generated_at_utc": generated_at,
            "candidate_rows": len(rows),
            "candidate_rows_by_standard": dict(sorted(by_standard.items())),
        }
    )
    write_json(manifest_path, manifest)
    payload = {
        "mapping_review_workbench": str(html_path),
        "review_items": str(review_file),
        "candidate_rows": len(rows),
        "candidate_rows_by_standard": dict(sorted(by_standard.items())),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-dir", default=str(DEFAULT_EXP_DIR))
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
