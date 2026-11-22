"""M1 — Data map (evidence / antecedentes): static inventory of personal data locations.

Validates that the harness answers "where does each sensitive datum live, which controls
apply and which articles support them" from the code alone, and that the map persists to
the harness SQLite database.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from src.harness.antecedentes import (
    add_incident,
    build_map,
    build_register,
    build_subject,
    list_incidents,
    mark_notified,
    refresh_files,
    render_incidents,
    render_map,
    render_register,
    render_subject,
    scan_register,
)

ROOT = Path(__file__).resolve().parents[2]

CUSTOMER_MODEL = (
    "from sqlalchemy import Column, Integer, String\n"
    "from app.db import Base\n\n"
    "class Customer(Base):\n"
    "    __tablename__ = 'customers'\n"
    "    id = Column(Integer, primary_key=True)\n"
    "    rut = Column(String(12))\n"
    "    email = Column(String(255))\n"
)
LOG_SINK = (
    "import logging\n"
    "logger = logging.getLogger(__name__)\n\n"
    "def audit_order(customer):\n"
    "    logger.info('rut=%s', customer.rut)\n"
)


def _write(tmp_path: Path, rel: str, content: str) -> None:
    path = tmp_path / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def test_map_reports_sensitive_fields_with_controls_and_articles(tmp_path):
    _write(tmp_path, "app/models.py", CUSTOMER_MODEL)
    _write(tmp_path, "app/logging.py", LOG_SINK)

    report = render_map(build_map(tmp_path, ["app"]))
    assert "rut" in report and "email" in report
    assert "Customer" in report
    assert "IDENTIFIER_RUT" in report and "PERSONAL_CONTACT" in report
    assert "v2.log_pii" in report and "CORE-CHECK-002" in report
    assert "Art. 14 bis" in report
    assert "app/models.py" in report


def test_map_persists_fields_and_sinks_to_the_harness_db(tmp_path):
    db = tmp_path / "harness.db"
    _write(tmp_path, "app/models.py", CUSTOMER_MODEL)
    _write(tmp_path, "app/logging.py", LOG_SINK)

    build_map(tmp_path, ["app"], db_path=db)

    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    fields = {r["field_name"] for r in conn.execute("SELECT field_name FROM evidence_fields")}
    sinks = [dict(r) for r in conn.execute("SELECT * FROM evidence_sinks")]
    conn.close()

    assert {"rut", "email"} <= fields
    assert any("logger.info" in (s["call"] or "") for s in sinks)


def test_map_reports_sinks_with_location(tmp_path):
    _write(tmp_path, "app/logging.py", LOG_SINK)

    report = render_map(build_map(tmp_path, ["app"]))
    assert "app/logging.py" in report and "logger.info" in report


def test_map_is_empty_for_a_repo_without_personal_data(tmp_path):
    db = tmp_path / "harness.db"
    _write(tmp_path, "app/utils.py", "def helper(x):\n    return x + 1\n")

    report = render_map(build_map(tmp_path, ["app"], db_path=db))
    assert "no personal-data fields" in report.lower() or "0 fields" in report.lower()

    conn = sqlite3.connect(db)
    assert conn.execute("SELECT COUNT(*) FROM evidence_fields").fetchone()[0] == 0
    conn.close()


def test_map_refresh_removes_stale_entries(tmp_path):
    db = tmp_path / "harness.db"
    _write(tmp_path, "app/models.py", CUSTOMER_MODEL)
    build_map(tmp_path, ["app"], db_path=db)

    (tmp_path / "app" / "models.py").write_text(
        "from sqlalchemy import Column, Integer, String\n"
        "from app.db import Base\n\n"
        "class Customer(Base):\n"
        "    __tablename__ = 'customers'\n"
        "    id = Column(Integer, primary_key=True)\n",
        encoding="utf-8",
        newline="\n",
    )
    build_map(tmp_path, ["app"], db_path=db)

    conn = sqlite3.connect(db)
    assert conn.execute("SELECT COUNT(*) FROM evidence_fields").fetchone()[0] == 0
    conn.close()


REGISTER_MODEL = (
    "from sqlalchemy import Column, Integer, String, Boolean\n"
    "from app.db import Base\n\n"
    "class Customer(Base):\n"
    "    __tablename__ = 'customers'\n"
    "    id = Column(Integer, primary_key=True)\n"
    "    rut = Column(String(12))\n"
    "    email = Column(String(255))\n"
    "    marketing_consent = Column(Boolean, default=False)\n\n"
    "TRACKING_URL = 'https://metrics.acme.io/send'\n"
)


def test_register_lists_activities_with_declared_gaps(tmp_path):
    _write(tmp_path, "app/models.py", REGISTER_MODEL)

    report = render_register(build_register(tmp_path, ["app"]))
    assert "Customer" in report and "rut" in report and "email" in report
    assert "finalidad" in report.lower()
    assert "metrics.acme.io" in report
    assert "retención" in report.lower() or "retencion" in report.lower()


def test_register_persists_activities(tmp_path):
    db = tmp_path / "harness.db"
    _write(tmp_path, "app/models.py", REGISTER_MODEL)

    build_register(tmp_path, ["app"], db_path=db)

    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    rows = [dict(r) for r in conn.execute("SELECT * FROM processing_activities")]
    conn.close()
    assert rows
    assert any("rut" in row["data_fields_json"] for row in rows)


def test_register_is_empty_for_a_repo_without_personal_data(tmp_path):
    db = tmp_path / "harness.db"
    _write(tmp_path, "app/utils.py", "def helper(x):\n    return x + 1\n")

    report = render_register(build_register(tmp_path, ["app"], db_path=db))
    assert "no processing activities" in report.lower() or "0 processing" in report.lower()

    conn = sqlite3.connect(db)
    assert conn.execute("SELECT COUNT(*) FROM processing_activities").fetchone()[0] == 0
    conn.close()


AUDIT_SINK = (
    "def access_patient(p):\n"
    "    record_audit({'rut': p.rut, 'action': 'read'})\n"
)


def test_subject_package_reports_locations_flows_and_audit(tmp_path):
    _write(tmp_path, "app/models.py", CUSTOMER_MODEL)
    _write(tmp_path, "app/logging.py", LOG_SINK)
    _write(tmp_path, "app/audit.py", AUDIT_SINK)

    report = render_subject(build_subject(tmp_path, ["app"], category="IDENTIFIER_RUT"))
    assert "IDENTIFIER_RUT" in report
    assert "app/models.py" in report and "rut" in report
    assert "app/logging.py" in report
    assert "record_audit" in report or "store_audit_event" in report


def test_subject_package_accepts_a_field_name(tmp_path):
    _write(tmp_path, "app/models.py", CUSTOMER_MODEL)

    report = render_subject(build_subject(tmp_path, ["app"], field="rut"))
    assert "rut" in report and "Customer" in report


def test_subject_package_unknown_category_is_empty(tmp_path):
    _write(tmp_path, "app/models.py", CUSTOMER_MODEL)

    report = render_subject(build_subject(tmp_path, ["app"], category="SENSITIVE_BELIEFS"))
    assert "no personal-data fields" in report.lower() or "0 fields" in report.lower()


def test_incident_add_and_list_roundtrip(tmp_path):
    db = tmp_path / "harness.db"
    incident_id = add_incident(db, "Se detectó una fuga de RUT en bitácoras de pedidos.",
                               scope=["IDENTIFIER_RUT"], severity="HIGH")
    assert incident_id >= 1

    rows = list_incidents(db)
    assert len(rows) == 1
    assert rows[0]["description"].startswith("Se detectó")
    assert "IDENTIFIER_RUT" in rows[0]["scope_json"]

    report = render_incidents(rows)
    assert "IDENTIFIER_RUT" in report and "HIGH" in report and "Se detectó" in report


def test_incident_mark_notified_sets_status_and_timestamp(tmp_path):
    db = tmp_path / "harness.db"
    incident_id = add_incident(db, "Fuga de correos en respuestas admin.",
                               scope=["PERSONAL_CONTACT"])
    mark_notified(db, incident_id)

    rows = list_incidents(db)
    assert rows[0]["status"] == "NOTIFIED"
    assert rows[0]["notified_at"]


def test_incident_list_is_empty_on_a_fresh_db(tmp_path):
    db = tmp_path / "harness.db"
    assert list_incidents(db) == []
    assert "no incidents" in render_incidents(list_incidents(db)).lower()


def test_refresh_files_upserts_and_removes_map_entries(tmp_path):
    db = tmp_path / "harness.db"

    refresh_files(db, "scan", {"app/models.py": CUSTOMER_MODEL})
    conn = sqlite3.connect(db)
    fields = {r[0] for r in conn.execute("SELECT field_name FROM evidence_fields")}
    assert {"rut", "email"} <= fields
    conn.close()

    without_rut = CUSTOMER_MODEL.replace("    rut = Column(String(12))\n", "")
    refresh_files(db, "scan", {"app/models.py": without_rut})
    conn = sqlite3.connect(db)
    fields = {r[0] for r in conn.execute("SELECT field_name FROM evidence_fields")}
    conn.close()
    assert "rut" not in fields and "email" in fields


def test_refresh_files_records_sinks(tmp_path):
    db = tmp_path / "harness.db"

    refresh_files(db, "scan", {"app/logging.py": LOG_SINK})
    conn = sqlite3.connect(db)
    sinks = [r[0] for r in conn.execute("SELECT call FROM evidence_sinks")]
    conn.close()
    assert any("logger.info" in s for s in sinks)


def test_register_and_subject_share_recipients(tmp_path):
    (tmp_path / "app").mkdir()
    (tmp_path / "app" / "crm.py").write_text(
        'CRM = "https://crm.example-store.com/sync"\nNS = "https://www.w3.org/ns"\n',
        encoding="utf-8")
    (tmp_path / "schema.sql").write_text("CREATE TABLE customers (email TEXT);\n", encoding="utf-8")

    register = scan_register(tmp_path, ["app"])
    package = build_subject(tmp_path, ["app"], field="email")

    assert "crm.example-store.com" in register.recipients
    assert "www.w3.org" not in register.recipients
    assert package.recipients == register.recipients
    assert "crm.example-store.com" in render_register(register)
