from __future__ import annotations

import json
import os
import sqlite3
import sys
import webbrowser
from pathlib import Path
from typing import Any

from src.harness.db import DEFAULT_DB_PATH, get_db_connection

HTML_OUTPUT_PATH = Path(__file__).resolve().parent.parent.parent / ".harness" / "graph.html"


def export_graph_data(db_path: Path | str = DEFAULT_DB_PATH) -> dict[str, Any]:
    """Extrae todos los nodos, aristas, reglas y hallazgos desde SQLite para el visualizador."""
    conn = get_db_connection(db_path)
    try:
        nodes_rows = conn.execute("SELECT * FROM graph_nodes").fetchall()
        edges_rows = conn.execute("SELECT * FROM graph_edges").fetchall()
        findings_rows = conn.execute("SELECT * FROM compliance_findings").fetchall()
        rules_rows = conn.execute("SELECT * FROM compliance_rules").fetchall()

        nodes = []
        for r in nodes_rows:
            r_keys = r.keys()
            nodes.append({
                "id": r["id"],
                "name": r["name"],
                "node_type": r["node_type"],
                "file_path": r["file_path"],
                "line_start": r["line_start"],
                "line_end": r["line_end"],
                "data_classification": r["data_classification"],
                "community": r["community"] if "community" in r_keys else 0,
                "norm_label": r["norm_label"] if "norm_label" in r_keys else None,
                "metadata": json.loads(r["metadata_json"] or "{}"),
            })

        edges = []
        for r in edges_rows:
            edges.append({
                "source": r["source_id"],
                "target": r["target_id"],
                "type": r["edge_type"],
                "metadata": json.loads(r["metadata_json"] or "{}"),
            })

        findings = []
        for r in findings_rows:
            findings.append({
                "id": r["id"],
                "rule_id": r["rule_id"],
                "source": r["source_node_id"],
                "sink": r["sink_node_id"],
                "taint_path": json.loads(r["taint_path_json"] or "[]"),
                "status": r["status"],
            })

        rules = {r["rule_id"]: dict(r) for r in rules_rows}

        # Cargar auditorías periciales de checklist por archivo
        file_audits: dict[str, list[dict[str, Any]]] = {}
        try:
            chk_rows = conn.execute("SELECT * FROM file_checklist_audits ORDER BY evaluated_at DESC").fetchall()
            for cr in chk_rows:
                fp = cr["file_path"]
                if fp not in file_audits:
                    file_audits[fp] = []
                file_audits[fp].append(dict(cr))
        except sqlite3.OperationalError:
            pass

        return {
            "nodes": nodes,
            "edges": edges,
            "findings": findings,
            "rules": rules,
            "file_audits": file_audits,
            "stats": {
                "total_nodes": len(nodes),
                "total_edges": len(edges),
                "total_findings": len(findings),
            },
        }
    finally:
        conn.close()


def generate_graph_html(
    db_path: Path | str = DEFAULT_DB_PATH,
    output_path: Path | str = HTML_OUTPUT_PATH,
    open_browser: bool = False,
) -> Path:
    """Genera el archivo HTML interactivo con D3.js (v7) estilo Graphify."""
    data = export_graph_data(db_path)
    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)

    json_payload = json.dumps(data, ensure_ascii=False)

    html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>VibeCoding Harness — Visualizador de Subgrafos (Graphify Architecture)</title>
  <script src="https://d3js.org/d3.v7.min.js"></script>
  <style>
    :root {{
      --bg-color: #0b0f19;
      --card-bg: rgba(17, 24, 39, 0.85);
      --border-color: #1f2937;
      --text-main: #f3f4f6;
      --text-muted: #9ca3af;
      --accent-health: #FFFF00;
      --accent-contact: #F0A825;
      --accent-rut: #7c3aed;
      --accent-sink: #ef4444;
      --accent-source: #f59e0b;
      --accent-class: #10b981;
      --accent-func: #0ea5e9;
      --accent-file: #f8fafc;
    }}

    * {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
    }}

    body {{
      background-color: var(--bg-color);
      color: var(--text-main);
      overflow: hidden;
      display: flex;
      height: 100vh;
      width: 100vw;
    }}

    #canvas-container {{
      flex: 1;
      height: 100%;
      position: relative;
      background: radial-gradient(circle at center, #111827 0%, #030712 100%);
    }}

    svg {{
      width: 100%;
      height: 100%;
    }}

    /* Panel Lateral de Sub-graph Slicing & Auditoría */
    #sidebar {{
      width: 450px;
      height: 100%;
      background: var(--card-bg);
      backdrop-filter: blur(12px);
      border-left: 1px solid var(--border-color);
      display: flex;
      flex-direction: column;
      z-index: 10;
      box-shadow: -4px 0 25px rgba(0, 0, 0, 0.5);
      transition: margin-right 0.3s cubic-bezier(0.4, 0, 0.2, 1);
      flex-shrink: 0;
    }}

    #sidebar.collapsed {{
      margin-right: -450px;
    }}

    .floating-toggle-btn {{
      position: absolute;
      top: 18px;
      right: 18px;
      background: #0284c7;
      color: white;
      border: 1px solid #38bdf8;
      border-radius: 8px;
      padding: 9px 15px;
      font-size: 0.85rem;
      font-weight: 600;
      cursor: pointer;
      z-index: 50;
      display: flex;
      align-items: center;
      gap: 6px;
      box-shadow: 0 4px 15px rgba(0,0,0,0.5);
      transition: all 0.2s;
    }}

    .floating-toggle-btn:hover {{
      background: #0369a1;
      transform: translateY(-1px);
    }}

    .icon-toggle-btn {{
      background: transparent;
      border: 1px solid #374151;
      color: var(--text-muted);
      border-radius: 6px;
      width: 30px;
      height: 30px;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      padding: 0;
      font-size: 1rem;
      transition: all 0.2s;
    }}

    .icon-toggle-btn:hover {{
      background: #1f2937;
      color: var(--text-main);
      border-color: #38bdf8;
    }}

    .sidebar-header {{
      padding: 18px 20px;
      border-bottom: 1px solid var(--border-color);
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}

    .sidebar-header h2 {{
      font-size: 1.15rem;
      font-weight: 700;
      color: #38bdf8;
      display: flex;
      align-items: center;
      gap: 8px;
    }}

    .sidebar-header p {{
      font-size: 0.8rem;
      color: var(--text-muted);
      margin-top: 4px;
    }}

    .sidebar-content {{
      flex: 1;
      overflow-y: auto;
      padding: 20px;
      display: flex;
      flex-direction: column;
      gap: 16px;
    }}

    .control-group {{
      display: flex;
      flex-direction: column;
      gap: 8px;
    }}

    label {{
      font-size: 0.8rem;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: var(--text-muted);
    }}

    select, input {{
      background: #1f2937;
      border: 1px solid #374151;
      color: var(--text-main);
      padding: 10px 12px;
      border-radius: 8px;
      font-size: 0.88rem;
      outline: none;
      transition: all 0.2s;
    }}

    select:focus, input:focus {{
      border-color: #38bdf8;
      box-shadow: 0 0 0 2px rgba(56, 189, 248, 0.2);
    }}

    .btn-row {{
      display: flex;
      gap: 10px;
    }}

    button {{
      background: #0284c7;
      color: white;
      border: none;
      padding: 10px 16px;
      border-radius: 8px;
      font-size: 0.88rem;
      font-weight: 600;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
      transition: all 0.2s;
      flex: 1;
    }}

    button:hover {{
      background: #0369a1;
      transform: translateY(-1px);
    }}

    button.secondary {{
      background: #374151;
      color: var(--text-main);
    }}

    button.secondary:hover {{
      background: #4b5563;
    }}

    /* Tarjeta de Auditoría del Nodo */
    .audit-card {{
      background: rgba(31, 41, 55, 0.7);
      border: 1px solid #374151;
      border-radius: 10px;
      padding: 14px;
      display: flex;
      flex-direction: column;
      gap: 12px;
    }}

    .audit-section-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 6px;
    }}

    .audit-section-title {{
      font-size: 0.8rem;
      font-weight: 700;
      color: #38bdf8;
      display: flex;
      align-items: center;
      gap: 6px;
    }}

    .copy-btn {{
      background: #1f2937;
      border: 1px solid #374151;
      color: #38bdf8;
      font-size: 0.72rem;
      padding: 3px 8px;
      border-radius: 4px;
      cursor: pointer;
      font-weight: 500;
      display: inline-flex;
      align-items: center;
      gap: 4px;
      transition: all 0.2s;
      flex: none;
    }}

    .copy-btn:hover {{
      background: #374151;
      color: #7dd3fc;
      border-color: #38bdf8;
    }}

    .copy-btn.copied {{
      background: rgba(16, 185, 129, 0.2);
      color: #34d399;
      border-color: #10b981;
    }}

    .audit-text-box {{
      background: rgba(17, 24, 39, 0.7);
      border: 1px solid #1f2937;
      border-radius: 6px;
      padding: 10px;
      font-size: 0.78rem;
      line-height: 1.45;
      color: #e5e7eb;
      white-space: pre-line;
    }}

    /* Tarjeta de Métricas de Sub-graph Slicing */
    .slice-card {{
      background: rgba(31, 41, 55, 0.7);
      border: 1px solid #374151;
      border-radius: 10px;
      padding: 14px;
      display: flex;
      flex-direction: column;
      gap: 10px;
    }}

    .metric-badge {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 3px 8px;
      border-radius: 9999px;
      font-size: 0.72rem;
      font-weight: 700;
      width: fit-content;
    }}

    .stat-row {{
      display: flex;
      justify-content: space-between;
      font-size: 0.82rem;
    }}

    .stat-label {{
      color: var(--text-muted);
    }}

    .stat-val {{
      font-weight: 600;
      color: var(--text-main);
    }}

    .file-tag {{
      display: block;
      background: #111827;
      padding: 6px 10px;
      border-radius: 6px;
      font-family: monospace;
      font-size: 0.78rem;
      color: #38bdf8;
      word-break: break-all;
      border: 1px solid #1f2937;
      margin-top: 4px;
    }}

    /* Leyenda flotante */
    #legend {{
      position: absolute;
      bottom: 20px;
      left: 20px;
      background: var(--card-bg);
      backdrop-filter: blur(8px);
      border: 1px solid var(--border-color);
      border-radius: 10px;
      padding: 14px 16px;
      font-size: 0.75rem;
      display: flex;
      flex-direction: column;
      gap: 6px;
      pointer-events: none;
      box-shadow: 0 4px 15px rgba(0, 0, 0, 0.4);
    }}

    .legend-item {{
      display: flex;
      align-items: center;
      gap: 8px;
    }}

    .legend-dot {{
      width: 10px;
      height: 10px;
      border-radius: 50%;
    }}

    /* Tooltip de nodo */
    #tooltip {{
      position: absolute;
      display: none;
      background: rgba(17, 24, 39, 0.95);
      border: 1px solid #38bdf8;
      border-radius: 8px;
      padding: 10px 12px;
      font-size: 0.8rem;
      color: #f3f4f6;
      pointer-events: none;
      z-index: 100;
      box-shadow: 0 8px 20px rgba(0,0,0,0.6);
      max-width: 320px;
    }}
  </style>
</head>
<body>
  <div id="canvas-container">
    <button id="btn-open-sidebar" class="floating-toggle-btn" style="display: none;" title="Desplegar panel lateral">
      <span>📋 Ficha de Auditoría ◀</span>
    </button>
    <svg id="graph-svg"></svg>
    <div id="legend">
      <div style="font-weight: 700; margin-bottom: 4px; color: #9ca3af;">Categorías del Grafo</div>
      <div class="legend-item"><div class="legend-dot" style="background: var(--accent-health); border: 1px solid #ca8a04;"></div> Dato Salud (Art. 16 Ley)</div>
      <div class="legend-item"><div class="legend-dot" style="background: var(--accent-contact);"></div> Dato Contacto (Art. 2 Ley)</div>
      <div class="legend-item"><div class="legend-dot" style="background: var(--accent-rut);"></div> Identificador Civil (RUT/RUN)</div>
      <div class="legend-item"><div class="legend-dot" style="background: var(--accent-sink);"></div> Sumidero Crítico (Sink)</div>
      <div class="legend-item"><div class="legend-dot" style="background: var(--accent-source);"></div> Fuente General (Source)</div>
      <div class="legend-item"><div class="legend-dot" style="background: var(--accent-class);"></div> Clase / Modelo</div>
      <div class="legend-item"><div class="legend-dot" style="background: var(--accent-func);"></div> Función / Endpoint / Callable</div>
      <div class="legend-item"><div class="legend-dot" style="background: var(--accent-file); border: 1px solid #94a3b8;"></div> Archivo / Módulo</div>
    </div>
    <div id="tooltip"></div>
  </div>

  <div id="sidebar">
    <div class="sidebar-header">
      <div>
        <h2>🕸️ Sub-graph Slicer</h2>
        <p>Auditoría de Contexto & Cumplimiento Normativo</p>
      </div>
      <button id="btn-collapse-sidebar" class="icon-toggle-btn" title="Plegar panel lateral">⏵</button>
    </div>

    <div class="sidebar-content">
      <div class="control-group">
        <label for="symbol-search">Buscar o Seleccionar Símbolo</label>
        <input type="text" id="symbol-search" placeholder="Escribe para filtrar símbolos..." autocomplete="off">
        <select id="node-selector" size="5" style="margin-top: 4px;"></select>
      </div>

      <div class="control-group">
        <label for="depth-selector">Profundidad de Salto (k-hops)</label>
        <select id="depth-selector">
          <option value="1" selected>k = 1 (Vecinos inmediatos)</option>
          <option value="2">k = 2 (Flujo extendido)</option>
          <option value="3">k = 3 (Contexto profundo)</option>
        </select>
      </div>

      <div class="btn-row">
        <button id="btn-slice">✂️ Aislar Subgrafo</button>
        <button id="btn-reset" class="secondary">🔄 Reset</button>
      </div>

      <!-- Ficha de Auditoría y Remediación del Nodo Seleccionado -->
      <div id="node-audit-card" class="audit-card" style="display: none;">
        <div style="border-bottom: 1px solid #374151; padding-bottom: 8px;">
          <div style="display: flex; justify-content: space-between; align-items: center; gap: 8px;">
            <span id="audit-node-name" style="font-weight: 700; font-size: 0.92rem; color: #f3f4f6; word-break: break-all;"></span>
            <span id="audit-node-badge" class="metric-badge"></span>
          </div>
          <div id="audit-node-meta" style="font-size: 0.74rem; color: #9ca3af; margin-top: 4px;"></div>
        </div>

        <div>
          <div class="audit-section-header">
            <span class="audit-section-title">⚖️ Diagnóstico & Vector de Exposición</span>
            <button id="btn-copy-diag" class="copy-btn" title="Copiar diagnóstico y artículos legales al portapapeles">📋 Copiar Diagnóstico</button>
          </div>
          <div id="audit-diag-content" class="audit-text-box"></div>
        </div>

        <div>
          <div class="audit-section-header">
            <span class="audit-section-title">🛡️ Propuesta de Protección Óptima</span>
            <button id="btn-copy-prop" class="copy-btn" title="Copiar propuesta técnica de protección al portapapeles">📋 Copiar Propuesta</button>
          </div>
          <div id="audit-prop-content" class="audit-text-box"></div>
        </div>

        <!-- Checklist Pericial Normativo (Core Ley 21.719 + Plugin Sectorial) -->
        <div id="audit-checklist-container" style="display: none; border-top: 1px solid #374151; padding-top: 10px;">
          <div class="audit-section-header">
            <span class="audit-section-title">📜 Checklist Normativo del Archivo</span>
            <span id="checklist-summary-badge" class="metric-badge" style="background: rgba(16, 185, 129, 0.2); color: #34d399; font-size: 0.7rem;"></span>
          </div>
          <div id="checklist-items-list" style="display: flex; flex-direction: column; gap: 6px; margin-top: 6px;"></div>
        </div>
      </div>

      <!-- Resumen del Subgrafo Aislado -->
      <div id="slice-results" style="display: none;" class="slice-card">
        <div style="font-weight: 700; font-size: 0.85rem; color: #38bdf8;">Resumen del Subgrafo Aislado</div>

        <div class="stat-row">
          <span class="stat-label">Nodos en el Subgrafo:</span>
          <span id="stat-slice-nodes" class="stat-val">0 / 0</span>
        </div>
        <div class="stat-row">
          <span class="stat-label">Aristas Conectadas:</span>
          <span id="stat-slice-edges" class="stat-val">0</span>
        </div>

        <div style="margin-top: 6px;">
          <span class="stat-label" style="font-size: 0.78rem; font-weight: 600;">Archivos Físicos Involucrados:</span>
          <div id="isolated-files-container"></div>
        </div>

        <div id="breach-alert-box" style="display: none; margin-top: 8px; padding: 10px; background: rgba(239, 68, 68, 0.15); border: 1px solid rgba(239, 68, 68, 0.4); border-radius: 8px;">
          <div style="font-size: 0.78rem; font-weight: 700; color: #f87171; display: flex; align-items: center; gap: 6px;">
            ⚠️ Infracción Normativa Detectada
          </div>
          <div id="breach-desc" style="font-size: 0.74rem; color: #fca5a5; margin-top: 4px;"></div>
        </div>
      </div>
    </div>
  </div>

  <script>
    const graphData = {json_payload};

    const svg = d3.select("#graph-svg");
    const container = document.getElementById("canvas-container");
    const tooltip = document.getElementById("tooltip");

    let width = container.clientWidth;
    let height = container.clientHeight;

    const g = svg.append("g");

    // Zoom & Pan
    const zoom = d3.zoom()
      .scaleExtent([0.1, 8])
      .on("zoom", (event) => g.attr("transform", event.transform));

    svg.call(zoom);

    // Posicionamiento direccional según la estructura de carpetas del repositorio
    function getFolderTarget(d, w, h) {{
      const fp = (d.file_path || "").toLowerCase();
      const cx = w / 2;
      const cy = h / 2;
      const r = Math.min(w, h) * 0.28; // Radio acotado: mantiene todo visible sin alejarse

      if (fp.includes("backend/api")) {{
        // Norte / Superior: Endpoints y controladores HTTP
        return {{ x: cx, y: cy - r * 0.9 }};
      }} else if (fp.includes("backend/security")) {{
        // Oeste / Izquierda: Seguridad, Autenticación y Contexto
        return {{ x: cx - r * 1.05, y: cy - r * 0.15 }};
      }} else if (fp.includes("backend/services") || fp.includes("backend/schemas")) {{
        // Noreste: Servicios de Negocio y Esquemas DTO
        return {{ x: cx + r * 0.9, y: cy - r * 0.45 }};
      }} else if (fp.includes("database")) {{
        // Sur / Inferior: Modelos, ORM y Persistencia
        return {{ x: cx - r * 0.15, y: cy + r * 0.95 }};
      }} else if (fp.includes("harness")) {{
        // Sureste: Compliance, Taint Analysis y Harness
        return {{ x: cx + r * 0.95, y: cy + r * 0.7 }};
      }} else if (fp.includes("backend")) {{
        // Noroeste: Raíz backend (main.py, etc.)
        return {{ x: cx - r * 0.55, y: cy - r * 0.65 }};
      }}
      return {{ x: cx, y: cy }};
    }}

    window.addEventListener("resize", () => {{
      width = container.clientWidth;
      height = container.clientHeight;
      simulation.force("x", d3.forceX(d => getFolderTarget(d, width, height).x).strength(0.07));
      simulation.force("y", d3.forceY(d => getFolderTarget(d, width, height).y).strength(0.07));
      simulation.alpha(0.15).restart();
    }});

    function getNodeColor(d) {{
      if (d.data_classification === "SENSITIVE_HEALTH") return "#FFFF00";
      if (d.data_classification === "PERSONAL_CONTACT") return "#F0A825";
      if (d.data_classification === "IDENTIFIER_RUT") return "#7c3aed";
      if (d.node_type === "sink") return "#ef4444";
      if (d.node_type === "source") return "#f59e0b";
      if (d.node_type === "class") return "#10b981";
      if (d.node_type === "endpoint" || d.node_type === "function" || d.node_type === "callable") return "#0ea5e9";
      if (d.node_type === "file") return "#f8fafc";
      return "#64748b";
    }}

    function getNodeSize(d) {{
      if (d.node_type === "source" || d.node_type === "sink") return 11;
      if (d.node_type === "file") return 10;
      if (d.node_type === "class") return 8.5;
      if (d.node_type === "endpoint") return 8;
      if (d.node_type === "function" || d.node_type === "callable") return 6;
      return 5;
    }}

    // Mapeo de enlaces para D3
    const links = graphData.edges.map(e => ({{
      source: e.source,
      target: e.target,
      type: e.type,
      metadata: e.metadata
    }}));

    // Nodos inicializados cerca de sus clústeres direccionales para estabilidad
    const nodes = graphData.nodes.map(n => {{
      const target = getFolderTarget(n, width, height);
      return {{
        ...n,
        x: target.x + (Math.random() - 0.5) * 40,
        y: target.y + (Math.random() - 0.5) * 40,
      }};
    }});

    // Simulación de Fuerzas D3 con Ordenamiento Arquitectónico y Espaciado Amplio
    const simulation = d3.forceSimulation(nodes)
      .alphaDecay(0.03)
      .force("link", d3.forceLink(links).id(d => d.id).distance(d => d.type === "FLOWS_TO" ? 90 : (d.type === "CONTAINS" ? 45 : 60)))
      .force("charge", d3.forceManyBody().strength(-95).distanceMax(280))
      .force("x", d3.forceX(d => getFolderTarget(d, width, height).x).strength(0.07))
      .force("y", d3.forceY(d => getFolderTarget(d, width, height).y).strength(0.07))
      .force("collision", d3.forceCollide().radius(d => getNodeSize(d) + 9).iterations(2));

    // Aristas
    const link = g.append("g")
      .attr("class", "links")
      .selectAll("line")
      .data(links)
      .enter().append("line")
      .attr("stroke", d => d.type === "FLOWS_TO" ? "#ef4444" : (d.type === "CONTAINS" ? "#475569" : "#374151"))
      .attr("stroke-width", d => d.type === "FLOWS_TO" ? 2.5 : 1)
      .attr("stroke-dasharray", d => d.type === "FLOWS_TO" ? "4,3" : "none")
      .attr("stroke-opacity", 0.6);

    // Nodos
    const node = g.append("g")
      .attr("class", "nodes")
      .selectAll("circle")
      .data(nodes)
      .enter().append("circle")
      .attr("r", d => getNodeSize(d))
      .attr("fill", d => getNodeColor(d))
      .attr("stroke", d => d.node_type === "file" ? "#94a3b8" : "#111827")
      .attr("stroke-width", 1.5)
      .call(d3.drag()
        .on("start", dragstarted)
        .on("drag", dragged)
        .on("end", dragended))
      .on("mouseover", (event, d) => {{
        tooltip.style.display = "block";
        tooltip.innerHTML = `<strong>${{d.name}}</strong><br>
          <span style="color: #9ca3af;">Tipo:</span> ${{d.node_type}}<br>
          <span style="color: #9ca3af;">Clasificación:</span> <strong style="color: ${{getNodeColor(d)}};">${{d.data_classification}}</strong><br>
          <span style="color: #9ca3af;">Archivo:</span> ${{d.file_path || 'N/A'}}`;
        tooltip.style.left = (event.pageX + 12) + "px";
        tooltip.style.top = (event.pageY + 12) + "px";
      }})
      .on("mouseout", () => {{
        tooltip.style.display = "none";
      }})
      .on("click", (event, d) => {{
        sidebar.classList.remove("collapsed");
        btnExpand.style.display = "none";
        document.getElementById("node-selector").value = d.id;
        renderNodeAudit(d);
        executeSlice(d.id, parseInt(document.getElementById("depth-selector").value));
      }});

    // Etiquetas de texto para nodos de tipo archivo (para identificar clústeres visualmente)
    const fileLabel = g.append("g")
      .attr("class", "file-labels")
      .selectAll("text")
      .data(nodes.filter(n => n.node_type === "file"))
      .enter().append("text")
      .attr("font-size", "10px")
      .attr("fill", "#c7d2fe")
      .attr("font-weight", "600")
      .attr("dx", 12)
      .attr("dy", 4)
      .attr("pointer-events", "none")
      .style("text-shadow", "0 1px 3px rgba(0,0,0,0.9)")
      .text(d => d.name);

    simulation.on("tick", () => {{
      link
        .attr("x1", d => d.source.x)
        .attr("y1", d => d.source.y)
        .attr("x2", d => d.target.x)
        .attr("y2", d => d.target.y);

      node
        .attr("cx", d => d.x)
        .attr("cy", d => d.y);

      fileLabel
        .attr("x", d => d.x)
        .attr("y", d => d.y);
    }});

    function dragstarted(event, d) {{
      if (!event.active) simulation.alphaTarget(0.04).restart();
      d.fx = d.x;
      d.fy = d.y;
    }}

    function dragged(event, d) {{
      d.fx = event.x;
      d.fy = event.y;
    }}

    function dragended(event, d) {{
      if (!event.active) simulation.alphaTarget(0);
      d.fx = null;
      d.fy = null;
    }}

    // Poblar Selector de Símbolos
    const nodeSelector = document.getElementById("node-selector");
    const searchInput = document.getElementById("symbol-search");

    function populateSelector(filter = "") {{
      nodeSelector.innerHTML = "";
      const filtered = nodes.filter(n => n.name.toLowerCase().includes(filter.toLowerCase()) || n.id.toLowerCase().includes(filter.toLowerCase()));
      filtered.slice(0, 100).forEach(n => {{
        const opt = document.createElement("option");
        opt.value = n.id;
        opt.textContent = `${{n.name}} (${{n.node_type}})`;
        nodeSelector.appendChild(opt);
      }});
      if (filtered.length > 0) {{
        nodeSelector.value = filtered[0].id;
      }}
    }}
    populateSelector();

    searchInput.addEventListener("input", (e) => populateSelector(e.target.value));

    // Lógica de Plegado/Desplegado de Barra Lateral
    const sidebar = document.getElementById("sidebar");
    const btnCollapse = document.getElementById("btn-collapse-sidebar");
    const btnExpand = document.getElementById("btn-open-sidebar");

    btnCollapse.addEventListener("click", () => {{
      sidebar.classList.add("collapsed");
      btnExpand.style.display = "flex";
    }});

    btnExpand.addEventListener("click", () => {{
      sidebar.classList.remove("collapsed");
      btnExpand.style.display = "none";
    }});

    // Función de Copiado al Portapapeles con Retroalimentación Visual
    function copyToClipboard(text, btnElement, originalText) {{
      if (!text) return;
      if (navigator.clipboard && navigator.clipboard.writeText) {{
        navigator.clipboard.writeText(text).then(() => {{
          btnElement.textContent = "✓ Copiado!";
          btnElement.classList.add("copied");
          setTimeout(() => {{
            btnElement.textContent = originalText;
            btnElement.classList.remove("copied");
          }}, 2000);
        }}).catch(() => fallbackCopy(text, btnElement, originalText));
      }} else {{
        fallbackCopy(text, btnElement, originalText);
      }}
    }}

    function fallbackCopy(text, btnElement, originalText) {{
      const textArea = document.createElement("textarea");
      textArea.value = text;
      document.body.appendChild(textArea);
      textArea.select();
      try {{
        document.execCommand('copy');
        btnElement.textContent = "✓ Copiado!";
        btnElement.classList.add("copied");
        setTimeout(() => {{
          btnElement.textContent = originalText;
          btnElement.classList.remove("copied");
        }}, 2000);
      }} catch (err) {{
        console.error("Error al copiar:", err);
      }}
      document.body.removeChild(textArea);
    }}

    document.getElementById("btn-copy-diag").addEventListener("click", () => {{
      const text = document.getElementById("audit-diag-content").innerText;
      copyToClipboard(text, document.getElementById("btn-copy-diag"), "📋 Copiar Diagnóstico");
    }});

    document.getElementById("btn-copy-prop").addEventListener("click", () => {{
      const text = document.getElementById("audit-prop-content").innerText;
      copyToClipboard(text, document.getElementById("btn-copy-prop"), "📋 Copiar Propuesta");
    }});

    // Renderizado de Ficha de Auditoría y Propuesta de Protección Óptima
    function renderNodeAudit(d) {{
      if (!d) return;
      const auditCard = document.getElementById("node-audit-card");
      auditCard.style.display = "flex";

      document.getElementById("audit-node-name").textContent = d.name;
      
      const badge = document.getElementById("audit-node-badge");
      const isClassified = d.data_classification && d.data_classification !== "PUBLIC";
      badge.textContent = isClassified ? d.data_classification : d.node_type.toUpperCase();
      badge.style.background = getNodeColor(d) + "25";
      badge.style.color = getNodeColor(d);
      badge.style.border = "1px solid " + getNodeColor(d) + "50";

      const lineInfo = d.line_start ? ` (L${{d.line_start}})` : "";
      document.getElementById("audit-node-meta").textContent = `${{d.file_path || 'N/A'}}${{lineInfo}} • Tipo: ${{d.node_type}}`;

      let diagText = "";
      let propText = "";

      const cls = d.data_classification || "PUBLIC";
      const ntype = d.node_type || "symbol";

      if (cls === "SENSITIVE_HEALTH") {{
        diagText = "DATO SENSIBLE DE SALUD (Categoría Especial)\\n" +
          "• Vector de Exposición: Atributo clínico o diagnóstico de paciente. Su inclusión en logs, telemetría o interfaces sin RBAC provoca una fuga perimetral de fichas clínicas.\\n" +
          "• Normativa Aplicable: Ley 21.719 Art. 2° let. g) y Art. 16° bis (Datos relativos a la salud; prohibición de tratamiento salvo mandato legal expreso) en armonía con Ley 20.584 Art. 12° y 13° (Reserva y deber de confidencialidad de la ficha clínica; deber de custodia de 15 años). Infracción gravísima bajo el Art. 34° ter let. j) con multas de hasta 20.000 UTM o 4% de ingresos anuales.";
        
        propText = "PROPUESTA DE PROTECCIÓN ÓPTIMA (CERO DISRUPCIÓN)\\n" +
          "• Implementar Cifrado en Reposo a nivel de campo (Field-Level Encryption con AES-256-GCM) y excluir este campo de la serialización automática en auditoría y telemetría.\\n" +
          "• Viabilidad Operativa: CERO DISRUPCIÓN. La API y servicios médicos operan normalmente, descifrando en memoria únicamente para el profesional de salud tratante autenticado bajo RBAC (Ley 20.584). Los respaldos, logs y operadores de infraestructura quedan completamente ciegos al dato clínico crudo.";
      }} else if (cls === "IDENTIFIER_RUT") {{
        diagText = "IDENTIFICADOR CIVIL DIRECTO (RUT / RUN)\\n" +
          "• Vector de Exposición: Rol Único Tributario o Nacional. Al circular en texto plano en trazas de depuración o payloads de eventos, permite la reidentificación unívoca del paciente y correlación no autorizada de datos personales.\\n" +
          "• Normativa Aplicable: Ley 21.719 Art. 2° let. a) y Art. 14° bis (Principio de Seguridad y Confidencialidad; protección mandatoria de identificadores civiles directos frente a revelación no autorizada).";
        
        propText = "PROPUESTA DE PROTECCIÓN ÓPTIMA (CERO DISRUPCIÓN)\\n" +
          "• Aplicar seudonimización o enmascaramiento dinámico (ej. formato '12.345.xxx-x') para salidas a logs, auditoría y vistas externas.\\n" +
          "• Viabilidad Operativa: CERO DISRUPCIÓN. Las relaciones relacionales y consultas internas siguen operando sobre el identificador primario del paciente ('patient_id'), manteniendo intacta la integridad referencial y las búsquedas del backend sin exponer la identidad civil en trazas de auditoría.";
      }} else if (ntype === "sink") {{
        diagText = "SUMIDERO CRÍTICO (Sink de Persistencia / Logging)\\n" +
          "• Vector de Exposición: Punto de consumo o salida que persiste payloads en tablas de auditoría ('AuditLog') o flujos de logs. Si recibe entidades sin filtro previo, vuelca datos sensibles en texto plano sin cifrar.\\n" +
          "• Normativa Aplicable: CWE-532 (Insertion of Sensitive Information into Log File), Ley 21.719 Art. 14° quinquies (Falta de medidas técnicas de seguridad apropiadas) y Art. 14° sexies (Riesgo de brecha de seguridad notificable ante la APDP).";
        
        propText = "PROPUESTA DE PROTECCIÓN ÓPTIMA (CERO DISRUPCIÓN)\\n" +
          "• Interceptar en la capa de auditoría/logging aplicando una función sanitizadora ('mask_sensitive_payload') previo al INSERT en base de datos.\\n" +
          "• Viabilidad Operativa: CERO DISRUPCIÓN. Se preserva el 100% de la trazabilidad obligatoria que exige el Art. 14° sexies de la Ley 21.719 (auditoría forense de operaciones) sin violar el principio de confidencialidad al impedir que los valores sensibles queden en crudo.";
      }} else if (cls === "PERSONAL_CONTACT") {{
        diagText = "DATO PERSONAL DE CONTACTO / LOCALIZACIÓN\\n" +
          "• Vector de Exposición: Información de telecomunicaciones o dirección del titular expuesta en interfaces o registros generales.\\n" +
          "• Normativa Aplicable: Ley 21.719 Art. 3° let. c) y Art. 14° quáter (Principio de Proporcionalidad y Minimización de Datos).";
        
        propText = "PROPUESTA DE PROTECCIÓN ÓPTIMA (CERO DISRUPCIÓN)\\n" +
          "• Excluir campos de contacto de esquemas de respuesta pública mediante esquemas DTO restringidos.\\n" +
          "• Viabilidad Operativa: CERO DISRUPCIÓN. Solo los módulos de notificación y contacto acceden a estos campos bajo demanda.";
      }} else if (ntype === "endpoint" || ntype === "callable" || ntype === "function") {{
        diagText = "FUNCIÓN / ENDPOINT OPERATIVO\\n" +
          "• Vector de Exposición: Interfaz de procesamiento que canaliza solicitudes del usuario o del sistema. Transporta parámetros de entrada y salida.\\n" +
          "• Normativa Aplicable: Ley 21.719 Art. 14° quáter (Privacidad desde el Diseño y por Defecto).";
        
        propText = "PROPUESTA DE PROTECCIÓN ÓPTIMA (CERO DISRUPCIÓN)\\n" +
          "• Aplicar control de acceso RBAC granular y esquemas de salida tipificados para evitar fuga de campos excedentes.\\n" +
          "• Viabilidad Operativa: CERO DISRUPCIÓN. El contrato de la API se mantiene íntegro para usuarios legítimos.";
      }} else {{
        diagText = "COMPONENTE ESTRUCTURAL / DE SOPORTE\\n" +
          "• Estado Normativo: Conforme. No almacena ni procesa directamente fuentes de datos personales clasificadas bajo la Ley 21.719.\\n" +
          "• Normativa Aplicable: Ley 21.719 Art. 14° quinquies (Gobernanza y seguridad técnica general).";
        
        propText = "PROPUESTA DE PROTECCIÓN ÓPTIMA (CERO DISRUPCIÓN)\\n" +
          "• Mantener el principio de privilegio mínimo y no incorporar atributos clasificados sin transformadores de cifrado previo.";
      }}

      document.getElementById("audit-diag-content").innerText = diagText;
      document.getElementById("audit-prop-content").innerText = propText;

      // Renderizado del Checklist Normativo Asociado al Archivo
      const chkContainer = document.getElementById("audit-checklist-container");
      const chkList = document.getElementById("checklist-items-list");
      const chkBadge = document.getElementById("checklist-summary-badge");
      chkList.innerHTML = "";

      const fileAudits = (graphData.file_audits && d.file_path && graphData.file_audits[d.file_path]) || [];
      if (fileAudits.length > 0) {{
        chkContainer.style.display = "block";
        const passed = fileAudits.filter(a => a.status === "PASSED").length;
        const violations = fileAudits.filter(a => a.status === "VIOLATION").length;
        const total = fileAudits.length;

        if (violations > 0) {{
          chkBadge.textContent = `${{violations}} Infracción${{violations > 1 ? 'es' : ''}} / ${{total}} Criterios`;
          chkBadge.style.background = "rgba(239, 68, 68, 0.2)";
          chkBadge.style.color = "#f87171";
          chkBadge.style.border = "1px solid rgba(239, 68, 68, 0.4)";
        }} else {{
          chkBadge.textContent = `${{passed}}/${{total}} Aprobados (Conforme)`;
          chkBadge.style.background = "rgba(16, 185, 129, 0.2)";
          chkBadge.style.color = "#34d399";
          chkBadge.style.border = "1px solid rgba(16, 185, 129, 0.4)";
        }}

        fileAudits.forEach(item => {{
          const itemEl = document.createElement("div");
          itemEl.style.cssText = "background: rgba(17, 24, 39, 0.8); border: 1px solid #1f2937; border-radius: 6px; padding: 8px; font-size: 0.76rem;";
          
          let statusBadge = "";
          if (item.status === "PASSED") {{
            statusBadge = `<span style="color: #34d399; font-weight: 700;">✓ CONFORME</span>`;
          }} else if (item.status === "VIOLATION") {{
            statusBadge = `<span style="color: #f87171; font-weight: 700;">⚠ INFRACCIÓN [${{item.severity}}]</span>`;
          }} else {{
            statusBadge = `<span style="color: #9ca3af; font-weight: 600;">— N/A</span>`;
          }}

          const pluginLabel = item.plugin_name === "health_clinical" ? "🏥 Salud (Ley 20.584/21.668)" : "⚖️ Core (Ley 21.719)";

          let extraInfo = "";
          if (item.status === "VIOLATION" && item.evidence_snippet) {{
            extraInfo = `<div style="margin-top: 4px; padding: 4px 6px; background: rgba(239,68,68,0.1); border-left: 2px solid #ef4444; color: #fca5a5; font-family: monospace; font-size: 0.72rem;">Evidencia: ${{item.evidence_snippet}}</div>`;
          }}
          if (item.status === "VIOLATION" && item.remediation_advice) {{
            extraInfo += `<div style="margin-top: 4px; color: #38bdf8; font-size: 0.72rem;">Mitigación: ${{item.remediation_advice}}</div>`;
          }}

          itemEl.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 3px;">
              <span style="font-weight: 600; color: #e5e7eb;">${{item.criterion_id}}</span>
              ${{statusBadge}}
            </div>
            <div style="color: #9ca3af; font-size: 0.7rem; margin-bottom: 2px;">${{pluginLabel}} • ${{item.law_article}}</div>
            <div style="color: #d1d5db; line-height: 1.35;">${{item.details || ''}}</div>
            ${{extraInfo}}
          `;
          chkList.appendChild(itemEl);
        }});
      }} else {{
        chkContainer.style.display = "none";
      }}
    }}

    // Lógica de Sub-graph Slicing Interactivo
    function executeSlice(rootId, depth = 1) {{
      if (!rootId) return;

      const rootNode = nodes.find(n => n.id === rootId);
      if (rootNode) {{
        renderNodeAudit(rootNode);
      }}

      const visitedNodes = new Set([rootId]);
      let currentFrontier = new Set([rootId]);
      const matchedEdges = new Set();

      for (let i = 0; i < depth; i++) {{
        const nextFrontier = new Set();
        links.forEach(l => {{
          const srcId = typeof l.source === 'object' ? l.source.id : l.source;
          const tgtId = typeof l.target === 'object' ? l.target.id : l.target;

          if (currentFrontier.has(srcId)) {{
            matchedEdges.add(l);
            visitedNodes.add(tgtId);
            nextFrontier.add(tgtId);
          }}
          if (currentFrontier.has(tgtId)) {{
            matchedEdges.add(l);
            visitedNodes.add(srcId);
            nextFrontier.add(srcId);
          }}
        }});
        currentFrontier = nextFrontier;
      }}

      // Atenuar / Resaltar nodos y aristas
      node.transition().duration(400)
        .attr("opacity", d => visitedNodes.has(d.id) ? 1 : 0.08)
        .attr("r", d => visitedNodes.has(d.id) ? getNodeSize(d) * 1.5 : getNodeSize(d));

      link.transition().duration(400)
        .attr("opacity", l => matchedEdges.has(l) ? 1 : 0.05)
        .attr("stroke-width", l => matchedEdges.has(l) ? 3 : 1);

      // Centrar cámara en el subgrafo
      const matchedNodes = nodes.filter(n => visitedNodes.has(n.id));
      if (matchedNodes.length > 0) {{
        const xMin = d3.min(matchedNodes, d => d.x);
        const xMax = d3.max(matchedNodes, d => d.x);
        const yMin = d3.min(matchedNodes, d => d.y);
        const yMax = d3.max(matchedNodes, d => d.y);

        const midX = (xMin + xMax) / 2;
        const midY = (yMin + yMax) / 2;
        const dx = Math.max(xMax - xMin, 100);
        const dy = Math.max(yMax - yMin, 100);

        const scale = Math.min(width / (dx * 1.8), height / (dy * 1.8), 2.5);
        const transform = d3.zoomIdentity
          .translate(width / 2, height / 2)
          .scale(scale)
          .translate(-midX, -midY);

        svg.transition().duration(750).call(zoom.transform, transform);
      }}

      // Actualizar Panel de Métricas
      const involvedFiles = Array.from(new Set(matchedNodes.map(n => n.file_path).filter(Boolean)));

      document.getElementById("slice-results").style.display = "flex";
      document.getElementById("stat-slice-nodes").textContent = `${{matchedNodes.length}} / ${{nodes.length}}`;
      document.getElementById("stat-slice-edges").textContent = matchedEdges.size;

      // Comprobar si hay brecha legal en el slice
      const breach = graphData.findings.find(f => visitedNodes.has(f.source) || visitedNodes.has(f.sink));
      const alertBox = document.getElementById("breach-alert-box");

      if (breach) {{
        alertBox.style.display = "block";
        document.getElementById("breach-desc").textContent = `Flujo prohibido detectado en este slice: ${{breach.source}} -> ${{breach.sink}} (Ley 21.719 / Ley 20.584).`;
      }} else {{
        alertBox.style.display = "none";
      }}

      const filesCont = document.getElementById("isolated-files-container");
      filesCont.innerHTML = "";
      involvedFiles.forEach(f => {{
        const span = document.createElement("span");
        span.className = "file-tag";
        span.textContent = f;
        filesCont.appendChild(span);
      }});
    }}

    document.getElementById("btn-slice").addEventListener("click", () => {{
      const rootId = nodeSelector.value;
      const depth = parseInt(document.getElementById("depth-selector").value);
      executeSlice(rootId, depth);
    }});

    document.getElementById("btn-reset").addEventListener("click", () => {{
      node.transition().duration(400).attr("opacity", 1).attr("r", d => getNodeSize(d));
      link.transition().duration(400).attr("opacity", 0.6).attr("stroke-width", d => d.type === "FLOWS_TO" ? 2.5 : 1);
      document.getElementById("slice-results").style.display = "none";
      document.getElementById("node-audit-card").style.display = "none";
      svg.transition().duration(600).call(zoom.transform, d3.zoomIdentity);
    }});
  </script>
</body>
</html>
"""

    out_file.write_text(html_content, encoding="utf-8")

    if open_browser:
        try:
            # En Windows abre directamente con la app predeterminada
            if os.name == "nt":
                os.startfile(str(out_file))
            else:
                webbrowser.open(out_file.as_uri())
        except Exception as e:
            print(f"Aviso: no se pudo abrir automáticamente el navegador ({e}). Puedes abrir {out_file} manualmente.")

    return out_file


if __name__ == "__main__":
    should_open = "--open" in sys.argv or "-o" in sys.argv
    path = generate_graph_html(open_browser=should_open)
    print(f"Visualizador interactivo generado exitosamente en: {path}")
