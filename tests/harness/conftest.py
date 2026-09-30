import pathlib
import tempfile
import pytest

from src.harness.db import init_harness_db, get_db_connection


@pytest.fixture
def tmp_harness_db(tmp_path):
    """Provee una base de datos SQLite efímera para pruebas de persistencia del harness."""
    db_file = tmp_path / "test_harness.db"
    init_harness_db(db_file)
    return db_file


@pytest.fixture
def sample_code_dir(tmp_path):
    """Provee un directorio temporal con archivos Python de muestra para análisis AST y lineage."""
    repo = tmp_path / "sample_project"
    repo.mkdir()
    
    # Archivo con función y llamada
    api_dir = repo / "api"
    api_dir.mkdir()
    (api_dir / "__init__.py").write_text("", encoding="utf-8")
    
    (api_dir / "service.py").write_text(
        'def process_patient_data(rut: str, diagnosis: str):\n'
        '    """Procesa datos sensibles"""\n'
        '    print(f"Audit log: {rut}")\n'
        '    return {"status": "ok", "rut": rut}\n',
        encoding="utf-8"
    )
    
    (api_dir / "controller.py").write_text(
        'from api.service import process_patient_data\n\n'
        'def handle_request(req_rut: str, req_diag: str):\n'
        '    result = process_patient_data(req_rut, req_diag)\n'
        '    return result\n',
        encoding="utf-8"
    )
    
    return repo
