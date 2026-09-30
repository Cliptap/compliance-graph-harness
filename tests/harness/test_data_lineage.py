import ast
from pathlib import Path
import pytest

pytestmark = [pytest.mark.harness, pytest.mark.lineage]

from src.harness.data_lineage import ASTLineageScanner, DataLineageEngine
from src.harness.db import get_db_connection


def test_ast_lineage_scanner_detects_sensitive_sources_and_sinks():
    """Verifica que ASTLineageScanner detecta atributos sensibles y sumideros como print/logging."""
    code = (
        'class PatientRecord:\n'
        '    rut: str\n'
        '    diagnosis: str\n'
        '\n'
        'def export_record(p: PatientRecord):\n'
        '    print(f"Exporting: {p.rut}")\n'
    )
    categories = {
        "IDENTIFIER_RUT": {"fields": ["rut", "identifier"]},
        "SENSITIVE_HEALTH": {"fields": ["diagnosis", "notes"]},
    }
    
    scanner = ASTLineageScanner(Path("mock.py"), "mock.py", categories)
    tree = ast.parse(code)
    scanner.visit(tree)
    
    # Fuentes detectadas
    source_fields = [s["field_name"] for s in scanner.sources]
    assert "rut" in source_fields
    assert "diagnosis" in source_fields
    
    # Sumidero detectado (print)
    assert len(scanner.sinks) >= 1
    assert any("print" in sink["expr"] for sink in scanner.sinks)


def test_ast_lineage_scanner_detects_sensitive_fields_set():
    """Verifica que se detectan los sets de enmascaramiento o campos sanitizados."""
    code = 'SENSITIVE_FIELDS = {"password", "secret_token", "rut", "diagnosis"}\n'
    categories = {}
    
    scanner = ASTLineageScanner(Path("events.py"), "events.py", categories)
    tree = ast.parse(code)
    scanner.visit(tree)
    
    assert "password" in scanner.sanitized_fields
    assert "rut" in scanner.sanitized_fields
    assert "diagnosis" in scanner.sanitized_fields


def test_data_lineage_engine_scans_sample_project(tmp_harness_db, sample_code_dir):
    """Verifica que DataLineageEngine analiza un proyecto y registra fuentes y sumideros en la base de datos."""
    # Añadir clase con campo sensible para que genere fuentes y sumideros
    model_file = sample_code_dir / "api" / "models.py"
    model_file.write_text(
        'class Patient:\n'
        '    rut: str\n'
        '    diagnosis: str\n'
        '\n'
        'def log_patient(p: Patient):\n'
        '    print(p.rut)\n',
        encoding="utf-8"
    )

    engine = DataLineageEngine(db_path=tmp_harness_db)
    
    # Crear nodo archivo en SQLite primero
    conn = get_db_connection(tmp_harness_db)
    conn.execute(
        "INSERT INTO graph_nodes (id, name, node_type, file_path) "
        "VALUES ('api_models_py', 'models.py', 'file', 'api/models.py')"
    )
    conn.commit()
    conn.close()

    count = engine.scan_and_build_lineage(
        root_dir=sample_code_dir,
        scan_dirs=[sample_code_dir / "api"]
    )
    
    # Validar que se crearon nodos o aristas de lineage
    conn = get_db_connection(tmp_harness_db)
    try:
        nodes = conn.execute("SELECT * FROM graph_nodes WHERE node_type IN ('source', 'sink', 'sanitizer')").fetchall()
        assert len(nodes) >= 1
    finally:
        conn.close()
