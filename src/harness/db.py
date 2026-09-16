from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
HARNESS_DIR = WORKSPACE_ROOT / ".harness"
DEFAULT_DB_PATH = HARNESS_DIR / "harness.db"
SCHEMA_PATH = HARNESS_DIR / "schema.sql"
RULES_PATH = HARNESS_DIR / "compliance_rules.json"


def get_db_connection(db_path: Path | str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Obtiene una conexión a la base de datos embebida SQLite del harness."""
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_harness_db(db_path: Path | str = DEFAULT_DB_PATH) -> None:
    """Inicializa el esquema y carga las reglas de la ley chilena en la base de datos."""
    conn = get_db_connection(db_path)
    try:
        # Migración previa de columnas si la tabla ya existía
        cols = {row["name"] for row in conn.execute("PRAGMA table_info(graph_nodes)").fetchall()}
        if cols:
            if "community" not in cols:
                conn.execute("ALTER TABLE graph_nodes ADD COLUMN community INTEGER DEFAULT 0;")
            if "norm_label" not in cols:
                conn.execute("ALTER TABLE graph_nodes ADD COLUMN norm_label TEXT;")

        # 1. Crear tablas e índices desde schema.sql
        if SCHEMA_PATH.exists():
            schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
            conn.executescript(schema_sql)

        # 2. Cargar reglas desde compliance_rules.json
        if RULES_PATH.exists():
            conn.execute("DELETE FROM compliance_rules;")
            data = json.loads(RULES_PATH.read_text(encoding="utf-8"))
            rules = data.get("rules", [])
            for r in rules:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO compliance_rules 
                    (rule_id, law_article, title, description, sensitive_category, prohibited_sinks, required_mitigations, severity)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        r["rule_id"],
                        r["law_article"],
                        r["title"],
                        r["description"],
                        r["sensitive_category"],
                        json.dumps(r["prohibited_sinks"]),
                        json.dumps(r["required_mitigations"]),
                        r.get("severity", "CRITICAL"),
                    ),
                )
        conn.commit()
    finally:
        conn.close()


def save_node(
    conn: sqlite3.Connection,
    node_id: str,
    name: str,
    node_type: str,
    file_path: str,
    line_start: int | None = None,
    line_end: int | None = None,
    data_classification: str = "PUBLIC",
    community: int = 0,
    norm_label: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    """Inserta o actualiza un nodo del grafo mediante ON CONFLICT DO UPDATE evitando el borrado en cascada."""
    conn.execute(
        """
        INSERT INTO graph_nodes 
        (id, name, node_type, file_path, line_start, line_end, data_classification, community, norm_label, metadata_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            name = excluded.name,
            node_type = excluded.node_type,
            file_path = excluded.file_path,
            line_start = COALESCE(excluded.line_start, graph_nodes.line_start),
            line_end = COALESCE(excluded.line_end, graph_nodes.line_end),
            data_classification = CASE 
                WHEN excluded.data_classification != 'PUBLIC' THEN excluded.data_classification
                ELSE graph_nodes.data_classification
            END,
            community = CASE WHEN excluded.community != 0 THEN excluded.community ELSE graph_nodes.community END,
            norm_label = COALESCE(excluded.norm_label, graph_nodes.norm_label),
            metadata_json = excluded.metadata_json
        """,
        (
            node_id,
            name,
            node_type,
            file_path,
            line_start,
            line_end,
            data_classification,
            community,
            norm_label,
            json.dumps(metadata or {}),
        ),
    )


def save_edge(
    conn: sqlite3.Connection,
    source_id: str,
    target_id: str,
    edge_type: str,
    metadata: dict[str, Any] | None = None,
) -> None:
    """Inserta una arista de relación entre dos nodos del grafo evitando duplicados."""
    exists = conn.execute(
        "SELECT 1 FROM graph_edges WHERE source_id = ? AND target_id = ? AND edge_type = ?",
        (source_id, target_id, edge_type),
    ).fetchone()
    if not exists:
        conn.execute(
            """
            INSERT INTO graph_edges (source_id, target_id, edge_type, metadata_json)
            VALUES (?, ?, ?, ?)
            """,
            (source_id, target_id, edge_type, json.dumps(metadata or {})),
        )


def log_agent_reasoning(
    session_id: str,
    agent_name: str,
    step_name: str,
    input_payload: str | dict,
    reasoning_trace: str,
    output_result: str | dict | None = None,
    tokens_used: int = 0,
    db_path: Path | str = DEFAULT_DB_PATH,
) -> int:
    """Registra de forma exhaustiva el razonamiento y las decisiones de un subagente para observabilidad local."""
    conn = get_db_connection(db_path)
    try:
        in_str = json.dumps(input_payload) if isinstance(input_payload, dict) else str(input_payload)
        out_str = json.dumps(output_result) if isinstance(output_result, dict) else str(output_result or "")
        cursor = conn.execute(
            """
            INSERT INTO agent_audit_logs 
            (session_id, agent_name, step_name, input_payload, reasoning_trace, output_result, tokens_used)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (session_id, agent_name, step_name, in_str, reasoning_trace, out_str, tokens_used),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()
