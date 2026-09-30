import ast
import pathlib
import pytest

pytestmark = [pytest.mark.harness, pytest.mark.ast]

from src.harness.db import get_db_connection
from src.harness.graph_engine import (
    CodeGraphBuilder,
    build_repository_graph,
    subgraph_slice,
    render_slice_context,
)


def test_code_graph_builder_extracts_ast_nodes(tmp_harness_db, sample_code_dir):
    """Verifica que CodeGraphBuilder procesa el AST y registra nodos de archivo, función y llamadas."""
    service_file = sample_code_dir / "api" / "service.py"
    rel_path = "api/service.py"
    
    conn = get_db_connection(tmp_harness_db)
    try:
        builder = CodeGraphBuilder(service_file, rel_path, conn)
        content = service_file.read_text(encoding="utf-8")
        tree = ast.parse(content, filename=str(service_file))
        builder.visit(tree)
        conn.commit()

        # Validar nodo de archivo
        file_row = conn.execute("SELECT * FROM graph_nodes WHERE node_type = 'file'").fetchone()
        assert file_row is not None
        assert file_row["name"] == "service.py"

        # Validar nodo de función
        fn_row = conn.execute("SELECT * FROM graph_nodes WHERE node_type = 'function'").fetchone()
        assert fn_row is not None
        assert fn_row["name"] == "process_patient_data"
    finally:
        conn.close()


def test_subgraph_slice_extracts_neighborhood(tmp_harness_db):
    """Verifica que subgraph_slice extrae correctamente la vecindad de 1 salto de un nodo."""
    conn = get_db_connection(tmp_harness_db)
    try:
        # Insertar nodos y aristas de prueba usando columnas source_id, target_id, edge_type
        conn.execute("INSERT INTO graph_nodes (id, name, node_type, file_path) VALUES ('node_a', 'FuncA', 'function', 'a.py')")
        conn.execute("INSERT INTO graph_nodes (id, name, node_type, file_path) VALUES ('node_b', 'FuncB', 'function', 'b.py')")
        conn.execute("INSERT INTO graph_nodes (id, name, node_type, file_path) VALUES ('node_c', 'FuncC', 'function', 'c.py')")
        conn.execute("INSERT INTO graph_edges (source_id, target_id, edge_type) VALUES ('node_a', 'node_b', 'calls')")
        conn.commit()

        # Slice desde node_a con depth=1
        slice_data = subgraph_slice("node_a", depth=1, db_path=tmp_harness_db)
        
        node_ids = [n["id"] for n in slice_data["nodes"]]
        assert "node_a" in node_ids
        assert "node_b" in node_ids
        assert "node_c" not in node_ids  # No está conectado
        assert len(slice_data["edges"]) == 1
        assert slice_data["edges"][0]["type"] == "calls"
    finally:
        conn.close()


def test_render_slice_context_generates_markdown(sample_code_dir):
    """Verifica que render_slice_context produce el markdown estructurado de contexto de podado."""
    slice_data = {
        "root_node": "api_service_py",
        "involved_files": ["api/service.py"],
        "nodes": [
            {"id": "api_service_py", "name": "service.py", "node_type": "file", "file_path": "api/service.py"}
        ],
        "edges": []
    }
    
    context_str = render_slice_context(slice_data, root_dir=sample_code_dir)
    assert "Sub-graph Slice" in context_str
    assert "api/service.py" in context_str
    assert "def process_patient_data" in context_str


def test_build_repository_graph_with_custom_target(tmp_harness_db, sample_code_dir):
    """Verifica que build_repository_graph indexa archivos usando el fallback AST."""
    count = build_repository_graph(
        root_dir=sample_code_dir,
        db_path=tmp_harness_db,
        use_graphify=False,
        target_dirs=[sample_code_dir / "api"]
    )
    assert count > 0

    conn = get_db_connection(tmp_harness_db)
    try:
        nodes = conn.execute("SELECT COUNT(*) as cnt FROM graph_nodes").fetchone()["cnt"]
        assert nodes > 0
    finally:
        conn.close()


def test_python_symbol_extractor_and_symbol_level_slicing(sample_code_dir):
    """Verifica que PythonSymbolExtractor extrae la función exacta y render_slice_context aplica symbol-level slicing."""
    from src.harness.graph_engine import PythonSymbolExtractor

    extractor = PythonSymbolExtractor()
    service_file = sample_code_dir / "api" / "service.py"

    code = extractor.extract_symbol_code(service_file, "process_patient_data")
    assert code is not None
    assert "def process_patient_data" in code
    assert 'print(f"Audit log: {rut}")' in code

    # Evaluar render_slice_context en modo symbol_level
    slice_data = {
        "root_node": "api_service_py_process_patient_data",
        "involved_files": ["api/service.py"],
        "nodes": [
            {
                "id": "node_fn",
                "name": "process_patient_data",
                "node_type": "function",
                "file_path": "api/service.py",
            }
        ],
        "edges": [],
    }

    symbol_ctx = render_slice_context(slice_data, root_dir=sample_code_dir, symbol_level=True)
    assert "Symbol-Level Slicing" in symbol_ctx
    assert "Símbolo (function):" in symbol_ctx
    assert "process_patient_data" in symbol_ctx

