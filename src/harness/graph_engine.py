import ast
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
from typing import Any

from src.harness.db import (
    DEFAULT_DB_PATH,
    WORKSPACE_ROOT,
    get_db_connection,
    init_harness_db,
    save_edge,
    save_node,
)


class CodeGraphBuilder(ast.NodeVisitor):
    """Analizador estático de código Python inspirado en la arquitectura de Graphify.
    
    Construye nodos (archivos, clases, funciones, llamadas, modelos) y aristas
    (DEFINES, IMPORTS, CALLS, FLOWS_TO) para habilitar Sub-graph Slicing.
    """

    def __init__(self, file_path: Path, relative_path: str, conn: sqlite3.Connection):
        self.file_path = file_path
        self.relative_path = relative_path.replace("\\", "/")
        self.conn = conn
        self.file_node_id = f"file::{self.relative_path}"
        self.current_class: str | None = None
        self.current_function: str | None = None

        # Guardar nodo de archivo
        save_node(
            self.conn,
            node_id=self.file_node_id,
            name=self.file_path.name,
            node_type="file",
            file_path=self.relative_path,
            line_start=1,
            line_end=None,
        )

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            target_id = f"module::{alias.name}"
            save_node(
                self.conn,
                node_id=target_id,
                name=alias.name,
                node_type="module",
                file_path=self.relative_path,
                line_start=node.lineno,
            )
            save_edge(self.conn, self.file_node_id, target_id, "IMPORTS")
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        mod = node.module or ""
        for alias in node.names:
            target_id = f"symbol::{mod}.{alias.name}"
            save_node(
                self.conn,
                node_id=target_id,
                name=f"{mod}.{alias.name}",
                node_type="import_symbol",
                file_path=self.relative_path,
                line_start=node.lineno,
            )
            save_edge(self.conn, self.file_node_id, target_id, "IMPORTS")
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        prev_class = self.current_class
        self.current_class = node.name
        class_id = f"{self.file_node_id}::{node.name}"

        # Clasificación base para clases de código (las fuentes sensibles se detectan en atributos via reglas)
        data_class = "PUBLIC"

        save_node(
            self.conn,
            node_id=class_id,
            name=node.name,
            node_type="class",
            file_path=self.relative_path,
            line_start=node.lineno,
            line_end=getattr(node, "end_lineno", node.lineno),
            data_classification=data_class,
            metadata={"bases": [ast.unparse(b) for b in node.bases]},
        )
        save_edge(self.conn, self.file_node_id, class_id, "DEFINES")

        self.generic_visit(node)
        self.current_class = prev_class

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        prev_func = self.current_function
        self.current_function = node.name

        parent_prefix = f"{self.file_node_id}::{self.current_class}" if self.current_class else self.file_node_id
        func_id = f"{parent_prefix}::{node.name}"

        # Detectar decoradores (ej. FastAPI endpoints)
        decorators = [ast.unparse(d) for d in node.decorator_list]
        is_endpoint = any("router" in d or "app." in d for d in decorators)

        save_node(
            self.conn,
            node_id=func_id,
            name=node.name,
            node_type="endpoint" if is_endpoint else "function",
            file_path=self.relative_path,
            line_start=node.lineno,
            line_end=getattr(node, "end_lineno", node.lineno),
            metadata={"decorators": decorators, "args": [a.arg for a in node.args.args]},
        )
        parent_id = f"{self.file_node_id}::{self.current_class}" if self.current_class else self.file_node_id
        save_edge(self.conn, parent_id, func_id, "DEFINES")

        self.generic_visit(node)
        self.current_function = prev_func

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        # Reutilizar lógica para funciones asíncronas
        prev_func = self.current_function
        self.current_function = node.name

        parent_prefix = f"{self.file_node_id}::{self.current_class}" if self.current_class else self.file_node_id
        func_id = f"{parent_prefix}::{node.name}"

        decorators = [ast.unparse(d) for d in node.decorator_list]
        is_endpoint = any("router" in d or "app." in d for d in decorators)

        save_node(
            self.conn,
            node_id=func_id,
            name=node.name,
            node_type="endpoint" if is_endpoint else "function",
            file_path=self.relative_path,
            line_start=node.lineno,
            line_end=getattr(node, "end_lineno", node.lineno),
            metadata={"decorators": decorators, "args": [a.arg for a in node.args.args], "async": True},
        )
        parent_id = f"{self.file_node_id}::{self.current_class}" if self.current_class else self.file_node_id
        save_edge(self.conn, parent_id, func_id, "DEFINES")

        self.generic_visit(node)
        self.current_function = prev_func

    def visit_Call(self, node: ast.Call) -> None:
        call_name = ast.unparse(node.func)
        if self.current_function:
            parent_prefix = f"{self.file_node_id}::{self.current_class}" if self.current_class else self.file_node_id
            caller_id = f"{parent_prefix}::{self.current_function}"
            target_id = f"call::{call_name}"

            # Detectar si es un sumidero conocido (Sink)
            node_type = "call"
            data_class = "PUBLIC"
            if any(sink in call_name for sink in ["logger", "print", "AuditLog"]):
                node_type = "sink"
                data_class = "CONFIDENTIAL"

            save_node(
                self.conn,
                node_id=target_id,
                name=call_name,
                node_type=node_type,
                file_path=self.relative_path,
                line_start=node.lineno,
                data_classification=data_class,
            )
            save_edge(self.conn, caller_id, target_id, "CALLS")

        self.generic_visit(node)


def run_graphify_extraction(root_dir: Path | str = WORKSPACE_ROOT) -> Path:
    """Ejecuta graphify extract en modo headless para generar graphify-out/graph.json."""
    root = Path(root_dir)
    out_json = root / "graphify-out" / "graph.json"

    # Buscar ejecutable de graphify
    graphify_bin = shutil.which("graphify")
    if not graphify_bin:
        local_bin = Path(os.path.expanduser("~/.local/bin/graphify.exe"))
        if local_bin.exists():
            graphify_bin = str(local_bin)

    if graphify_bin:
        cmd = [graphify_bin, "extract", str(root), "--code-only"]
        res = subprocess.run(cmd, cwd=str(root), capture_output=True, text=True)
        if res.returncode != 0 and not out_json.exists():
            print(f"[!] Advertencia al ejecutar graphify: {res.stderr}")

    return out_json


def ingest_graphify_graph(
    graph_json_path: Path | str,
    db_path: Path | str = DEFAULT_DB_PATH,
    allowed_prefixes: list[str] | None = None,
) -> int:
    """Ingesta el grafo estructurado de Graphify en SQLite, filtrando carpetas de tests y qa."""
    if allowed_prefixes is None:
        allowed_prefixes = ["src/backend", "src/database", "src/harness"]

    p = Path(graph_json_path)
    if not p.exists():
        return 0

    data = json.loads(p.read_text(encoding="utf-8"))
    nodes = data.get("nodes", [])
    links = data.get("links", data.get("edges", []))

    conn = get_db_connection(db_path)
    try:
        target_nodes = []
        target_node_ids = set()
        file_paths_seen = set()

        # Mapear los nodos de archivo/módulo existentes en Graphify
        file_to_node_id = {}
        for n in nodes:
            sfile = n.get("source_file", "").replace("\\", "/")
            if any(sfile.startswith(prefix) for prefix in allowed_prefixes):
                target_nodes.append(n)
                target_node_ids.add(n["id"])
                file_paths_seen.add(sfile)
                lbl = n.get("label", "")
                nlbl = n.get("norm_label", "")
                is_callable = n.get("_callable", False)
                is_class = n.get("_callable_class", False)
                if (lbl.endswith(".py") or nlbl.endswith(".py")) and not is_callable and not is_class:
                    file_to_node_id[sfile] = n["id"]

        # Asegurar que cada archivo tenga un nodo canónico único (solo si Graphify no lo generó)
        for fp in file_paths_seen:
            if fp not in file_to_node_id:
                synthesized_id = fp.replace("/", "_").replace(".", "_")
                file_to_node_id[fp] = synthesized_id
                target_node_ids.add(synthesized_id)
                save_node(
                    conn,
                    node_id=synthesized_id,
                    name=Path(fp).name,
                    node_type="file",
                    file_path=fp,
                    line_start=1,
                )

        # 1. Registrar TODOS los nodos en SQLite primero para satisfacer Foreign Keys
        for n in target_nodes:
            sfile = n.get("source_file", "").replace("\\", "/")
            loc = n.get("source_location", "")
            line_start = None
            if loc and loc.startswith("L"):
                try:
                    line_start = int(loc[1:].split("-")[0])
                except Exception:
                    pass

            is_file = (n["id"] == file_to_node_id.get(sfile))
            if is_file:
                ntype = "file"
                display_name = Path(sfile).name
            elif n.get("_callable_class"):
                ntype = "class"
                display_name = n.get("label", n["id"])
            elif n.get("_callable"):
                ntype = "callable"
                display_name = n.get("label", n["id"])
            else:
                ntype = "symbol"
                display_name = n.get("label", n["id"])

            save_node(
                conn,
                node_id=n["id"],
                name=display_name,
                node_type=ntype,
                file_path=sfile,
                line_start=line_start,
                community=n.get("community", 0),
                norm_label=n.get("norm_label"),
                metadata={
                    "origin": n.get("_origin"),
                    "callable": n.get("_callable"),
                    "callable_class": n.get("_callable_class"),
                    "full_path": sfile,
                },
            )

        # 2. Registrar aristas CONTAINS entre el archivo canónico y sus símbolos definidos
        for n in target_nodes:
            sfile = n.get("source_file", "").replace("\\", "/")
            canonical_file_id = file_to_node_id.get(sfile)
            if canonical_file_id and canonical_file_id != n["id"]:
                save_edge(conn, canonical_file_id, n["id"], "CONTAINS")

        # 3. Registrar aristas resueltas de Graphify
        for l in links:
            src = l.get("source")
            tgt = l.get("target")
            rel = l.get("relation", "CALLS").upper()

            if src in target_node_ids and tgt in target_node_ids:
                save_edge(
                    conn,
                    source_id=src,
                    target_id=tgt,
                    edge_type=rel,
                    metadata={"confidence": l.get("confidence", "EXTRACTED")},
                )

        conn.commit()
        return len(target_nodes)
    finally:
        conn.close()


def build_repository_graph(
    root_dir: Path | str = WORKSPACE_ROOT,
    db_path: Path | str = DEFAULT_DB_PATH,
    use_graphify: bool = True,
    target_dirs: list[Path] | None = None,
) -> int:
    """Escanea el repositorio y construye el Grafo de Contexto de Código en SQLite.
    
    Por defecto utiliza Graphify para resolución de símbolos y deduplicación a nivel de compilador,
    con fallback al motor AST nativo en caso de indisponibilidad.
    """
    root = Path(root_dir)
    init_harness_db(db_path)
    conn = get_db_connection(db_path)

    # Limpiar tablas previas respetando claves foráneas
    conn.execute("DELETE FROM compliance_findings;")
    conn.execute("DELETE FROM graph_edges;")
    conn.execute("DELETE FROM graph_nodes;")
    conn.commit()
    conn.close()

    if use_graphify:
        try:
            graph_json_path = run_graphify_extraction(root)
            if graph_json_path.exists():
                count = ingest_graphify_graph(graph_json_path, db_path=db_path)
                if count > 0:
                    return count
        except Exception as ex:
            print(f"[!] Fallback a motor AST nativo tras error en Graphify: {ex}")

    # Fallback al motor AST nativo si Graphify no está disponible
    conn = get_db_connection(db_path)
    if target_dirs is None:
        target_dirs = [root / "src" / "backend", root / "src" / "database"]
    nodes_count = 0

    try:
        for tdir in target_dirs:
            if not tdir.exists():
                continue
            for py_file in tdir.rglob("*.py"):
                rel_path = py_file.relative_to(root).as_posix()
                try:
                    content = py_file.read_text(encoding="utf-8")
                    tree = ast.parse(content, filename=str(py_file))
                    builder = CodeGraphBuilder(py_file, rel_path, conn)
                    builder.visit(tree)
                except Exception as ex:
                    print(f"Error procesando {rel_path}: {ex}")
        conn.commit()
        nodes_count = conn.execute("SELECT COUNT(*) FROM graph_nodes").fetchone()[0]
    finally:
        conn.close()

    return nodes_count


def subgraph_slice(target_node_id: str, depth: int = 1, db_path: Path | str = DEFAULT_DB_PATH) -> dict[str, Any]:
    """Extrae el subgrafo relevante (Sub-graph Slicing estilo Graphify) a k-saltos del nodo objetivo.
    
    Permite generar un prompt ultracompacto con solo los archivos y símbolos físicos implicados.
    """
    conn = get_db_connection(db_path)
    try:
        visited_nodes: set[str] = {target_node_id}
        current_frontier: set[str] = {target_node_id}

        collected_edges: list[dict] = []

        for _ in range(depth):
            if not current_frontier:
                break
            placeholders = ",".join("?" for _ in current_frontier)
            query = f"""
                SELECT source_id, target_id, edge_type, metadata_json 
                FROM graph_edges 
                WHERE source_id IN ({placeholders}) OR target_id IN ({placeholders})
            """
            params = list(current_frontier) + list(current_frontier)
            rows = conn.execute(query, params).fetchall()

            next_frontier: set[str] = set()
            for r in rows:
                src, tgt, etype, meta = r["source_id"], r["target_id"], r["edge_type"], r["metadata_json"]
                collected_edges.append({
                    "source": src,
                    "target": tgt,
                    "type": etype,
                    "metadata": json.loads(meta or "{}"),
                })
                if src not in visited_nodes:
                    visited_nodes.add(src)
                    next_frontier.add(src)
                if tgt not in visited_nodes:
                    visited_nodes.add(tgt)
                    next_frontier.add(tgt)
            current_frontier = next_frontier

        # Recuperar datos completos de los nodos involucrados
        nodes_data = []
        if visited_nodes:
            placeholders = ",".join("?" for _ in visited_nodes)
            rows = conn.execute(
                f"SELECT * FROM graph_nodes WHERE id IN ({placeholders})",
                list(visited_nodes),
            ).fetchall()
            for r in rows:
                nodes_data.append({
                    "id": r["id"],
                    "name": r["name"],
                    "node_type": r["node_type"],
                    "file_path": r["file_path"],
                    "line_start": r["line_start"],
                    "line_end": r["line_end"],
                    "data_classification": r["data_classification"],
                })

        # Extraer lista única de archivos físicos involucrados para el prompt ultracompacto
        involved_files = sorted(list({n["file_path"] for n in nodes_data if n["file_path"]}))

        return {
            "root_node": target_node_id,
            "depth": depth,
            "involved_files": involved_files,
            "nodes": nodes_data,
            "edges": collected_edges,
        }
    finally:
        conn.close()


from abc import ABC, abstractmethod


class SymbolExtractor(ABC):
    """Contrato base para extractores de símbolos de código independientes del lenguaje."""

    @abstractmethod
    def extract_symbol_code(self, file_path: Path, symbol_name: str) -> str | None:
        """Extrae el fragmento de código correspondiente a un símbolo específico."""
        pass


class PythonSymbolExtractor(SymbolExtractor):
    """Extractor quirúrgico de símbolos para código Python basado en rangos AST preservando formato."""

    def extract_symbol_code(self, file_path: Path, symbol_name: str) -> str | None:
        if not file_path.exists() or file_path.suffix != ".py":
            return None
        try:
            content = file_path.read_text(encoding="utf-8")
            tree = ast.parse(content, filename=str(file_path))
            lines = content.splitlines()

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    if node.name == symbol_name:
                        start = max(0, node.lineno - 1)
                        end = getattr(node, "end_lineno", len(lines))
                        return "\n".join(lines[start:end])
        except Exception:
            return None
        return None


def render_slice_context(
    slice_data: dict[str, Any],
    root_dir: Path | str = WORKSPACE_ROOT,
    symbol_level: bool = False,
) -> str:
    """Genera el bloque de contexto en Markdown para el agente.
    
    Si symbol_level es True, realiza un recorte quirúrgico (symbol-level slicing)
    extrayendo solo las funciones, clases o endpoints involucrados, minimizando el consumo de tokens.
    """
    root = Path(root_dir)
    files = slice_data.get("involved_files", [])
    nodes = slice_data.get("nodes", [])
    parts = [
        f"### Sub-graph Slice de Contexto (Objetivo: `{slice_data.get('root_node')}`)",
        f"- **Archivos físicos aislados:** {len(files)}",
        f"- **Nodos en vecindad:** {len(nodes)}",
        f"- **Aristas conectadas:** {len(slice_data.get('edges', []))}",
        f"- **Modo de extracción:** {'Symbol-Level Slicing' if symbol_level else 'File-Level Bundling'}",
        "\n#### Fragmentos Críticos de Código:\n",
    ]

    extractor = PythonSymbolExtractor()

    if symbol_level and nodes:
        # Agrupar nodos por archivo
        rendered_symbols = set()
        for n in nodes:
            fpath = n.get("file_path")
            ntype = n.get("node_type")
            name = n.get("name")
            if not fpath or ntype not in ("function", "class", "endpoint"):
                continue

            full_p = root / fpath
            sym_key = f"{fpath}::{name}"
            if sym_key in rendered_symbols:
                continue

            code_slice = extractor.extract_symbol_code(full_p, name)
            if code_slice:
                parts.append(
                    f"**Símbolo ({ntype}):** `{name}` (`{fpath}`)\n```python\n{code_slice}\n```\n"
                )
                rendered_symbols.add(sym_key)

        # Si ningún símbolo específico pudo extraerse, recurrir a los archivos
        if not rendered_symbols:
            for fpath in files:
                full_p = root / fpath
                if full_p.exists():
                    content = full_p.read_text(encoding="utf-8")
                    parts.append(f"**Archivo:** `{fpath}`\n```python\n{content}\n```\n")
    else:
        for fpath in files:
            full_p = root / fpath
            if full_p.exists():
                content = full_p.read_text(encoding="utf-8")
                parts.append(f"**Archivo:** `{fpath}`\n```python\n{content}\n```\n")

    return "\n".join(parts)


if __name__ == "__main__":
    import sys
    args = sys.argv[1:]

    if not args or args[0] == "--help" or args[0] == "-h":
        print("Uso del CLI de Graph Engine (VibeCoding Harness):")
        print("  python -m src.harness.graph_engine build                  - Escanea y construye el grafo de contexto")
        print("  python -m src.harness.graph_engine slice <simbolo> [depth]- Extrae el subgrafo aislado de un simbolo")
        sys.exit(0)

    command = args[0]

    if command == "build":
        print("[*] Escaneando repositorio y construyendo grafo de contexto...")
        cnt = build_repository_graph()
        print(f"[OK] Grafo construido exitosamente con {cnt} nodos indexados.")

    elif command == "slice":
        if len(args) < 2:
            print("[ERROR] Debes especificar el identificador o nombre del simbolo a aislar.")
            sys.exit(1)

        symbol_query = args[1]
        depth = int(args[2]) if len(args) > 2 else 1

        conn = get_db_connection()
        # Buscar coincidencia exacta o mas cercana (insensible a mayusculas/minusculas)
        pattern = f"%{symbol_query}%"
        row = conn.execute(
            "SELECT id, name, file_path FROM graph_nodes WHERE id LIKE ? OR name LIKE ? OR file_path LIKE ? ORDER BY LENGTH(id) ASC LIMIT 1",
            (pattern, pattern, pattern),
        ).fetchone()
        conn.close()

        if not row:
            print(f"[ERROR] No se encontro el nodo o simbolo '{symbol_query}' en el grafo.")
            sys.exit(1)

        target_id = row["id"]
        slice_res = subgraph_slice(target_id, depth=depth)

        total_nodes = 434
        conn = get_db_connection()
        total_nodes = conn.execute("SELECT COUNT(*) FROM graph_nodes").fetchone()[0]
        conn.close()

        sliced_nodes_count = len(slice_res["nodes"])
        savings = (100.0 - (sliced_nodes_count / total_nodes * 100.0)) if total_nodes else 0.0

        print("\n" + "=" * 65)
        print("REPORTE DE SUB-GRAPH SLICING (ESTILO GRAPHIFY)")
        print("=" * 65)
        print(f"Nodo Raiz Aislado:      {target_id}")
        print(f"Profundidad (k-hops):   {depth}")
        print(f"Nodos en el Subgrafo:   {sliced_nodes_count} / {total_nodes}")
        print(f"Aristas Conectadas:     {len(slice_res['edges'])}")
        print(f"Economia de Contexto:   {savings:.1f}% de ahorro en tokens")
        print("-" * 65)
        print("Archivos Fisicos Aislados para el Subagente:")
        for f in slice_res["involved_files"]:
            print(f"  -> {f}")
        print("=" * 65 + "\n")

