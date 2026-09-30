import json
import sqlite3
import pytest

pytestmark = [pytest.mark.harness, pytest.mark.db, pytest.mark.fast]

from src.harness.db import (
    get_db_connection,
    init_harness_db,
    save_node,
    save_edge,
    log_agent_reasoning,
)


def test_init_harness_db_creates_tables_and_rules(tmp_harness_db):
    """Verifica que init_harness_db crea las tablas del esquema y precarga las reglas legales."""
    conn = get_db_connection(tmp_harness_db)
    try:
        tables = {row["name"] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
        assert "graph_nodes" in tables
        assert "graph_edges" in tables
        assert "compliance_rules" in tables
        assert "agent_audit_logs" in tables
        
        # Validar que las reglas de cumplimiento fueron insertadas
        rules_count = conn.execute("SELECT COUNT(*) as cnt FROM compliance_rules").fetchone()["cnt"]
        assert rules_count > 0
    finally:
        conn.close()


def test_save_node_and_edge(tmp_harness_db):
    """Verifica la persistencia de nodos y aristas con sus atributos."""
    conn = get_db_connection(tmp_harness_db)
    try:
        save_node(conn, "n1", "ClassA", "class", "app/models.py", line_start=10, metadata={"community": 1})
        save_node(conn, "n2", "ClassB", "class", "app/models.py", line_start=30, metadata={"community": 1})
        save_edge(conn, "n1", "n2", "INHERITS")
        conn.commit()

        node_row = conn.execute("SELECT * FROM graph_nodes WHERE id = 'n1'").fetchone()
        assert node_row["name"] == "ClassA"
        assert node_row["node_type"] == "class"

        edge_row = conn.execute("SELECT * FROM graph_edges WHERE source_id = 'n1' AND target_id = 'n2'").fetchone()
        assert edge_row is not None
        assert edge_row["edge_type"] == "INHERITS"
    finally:
        conn.close()


def test_log_agent_reasoning(tmp_harness_db):
    """Verifica el registro trazable de razonamiento agéntico en SQLite."""
    log_agent_reasoning(
        session_id="test-session-001",
        agent_name="compliance_auditor_agent",
        step_name="audit_evaluation",
        input_payload={"test": "input"},
        reasoning_trace="Evaluación preliminar de no contaminación",
        output_result={"status": "PASSED"},
        db_path=tmp_harness_db,
    )

    conn = get_db_connection(tmp_harness_db)
    try:
        row = conn.execute("SELECT * FROM agent_audit_logs WHERE session_id = 'test-session-001'").fetchone()
        assert row is not None
        assert row["agent_name"] == "compliance_auditor_agent"
        assert "no contaminación" in row["reasoning_trace"]
        assert json.loads(row["output_result"])["status"] == "PASSED"
    finally:
        conn.close()
