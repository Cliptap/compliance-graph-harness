from __future__ import annotations

import ast
import json
import sqlite3
import uuid
from pathlib import Path
from typing import Any

from src.harness.db import DEFAULT_DB_PATH, RULES_PATH, WORKSPACE_ROOT, get_db_connection, save_edge, save_node


class ASTLineageScanner(ast.NodeVisitor):
    """Escáner estático transversal basado en AST de Python.
    
    Identifica de forma dinámica y agnóstica:
    1. Fuentes de datos sensibles (Sources) según la ontología legal (compliance_rules.json).
    2. Sumideros críticos (Sinks) como llamadas a logging, print, stdout o persistencia de auditoría.
    3. Mecanismos de sanitización y listas de campos enmascarados presentes en el código fuente.
    """

    def __init__(self, file_path: Path, rel_path: str, categories: dict[str, Any]):
        self.file_path = file_path
        self.rel_path = rel_path.replace("\\", "/")
        self.categories = categories  # Categorías legales cargadas dinámicamente desde compliance_rules.json
        self.sources: list[dict[str, Any]] = []
        self.sinks: list[dict[str, Any]] = []
        self.sanitizers: list[dict[str, Any]] = []
        self.sanitized_fields: set[str] = set()
        self.current_class: str | None = None
        self.current_function: str | None = None

    def visit_Assign(self, node: ast.Assign) -> None:
        # Detectar colecciones o sets de campos protegidos (ej: SENSITIVE_FIELDS = {"password", "identifier", ...})
        for target in node.targets:
            if isinstance(target, ast.Name) and any(term in target.id.lower() for term in ["sensitive", "redact", "mask", "protect"]):
                if isinstance(node.value, (ast.Set, ast.List, ast.Tuple)):
                    for elt in node.value.elts:
                        if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                            self.sanitized_fields.add(elt.value.lower())

        # Si estamos dentro de una clase, analizar posibles atributos/columnas del modelo
        if self.current_class:
            for target in node.targets:
                if isinstance(target, ast.Name):
                    self._check_and_register_field(target.id, node.lineno)

        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        # Detectar anotaciones de tipos en clases (ej: Pydantic o SQLAlchemy Mapped[str])
        if self.current_class and isinstance(node.target, ast.Name):
            self._check_and_register_field(node.target.id, node.lineno)
        self.generic_visit(node)

    def _check_and_register_field(self, field_name: str, lineno: int) -> None:
        field_lower = field_name.lower()
        for cat_key, cat_data in self.categories.items():
            fields_vocab = [f.lower() for f in cat_data.get("fields", [])]
            # Coincidencia semántica con el vocabulario de la categoría legal
            if any(term == field_lower or (len(term) > 3 and term in field_lower) for term in fields_vocab):
                source_id = f"source::{self.rel_path}::{self.current_class}.{field_name}"
                self.sources.append({
                    "id": source_id,
                    "name": f"{self.current_class}.{field_name}",
                    "file_path": self.rel_path,
                    "class_name": self.current_class,
                    "field_name": field_name,
                    "category": cat_key,
                    "line": lineno,
                })

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        prev_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = prev_class

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        prev_func = self.current_function
        self.current_function = node.name

        func_lower = node.name.lower()
        if any(san in func_lower for san in ["redact", "mask", "encrypt", "hash", "sanitize", "obfuscate"]):
            self.sanitizers.append({
                "id": f"sanitizer::{self.rel_path}::{node.name}",
                "name": node.name,
                "file_path": self.rel_path,
                "line": node.lineno,
            })

        self.generic_visit(node)
        self.current_function = prev_func

    def visit_Call(self, node: ast.Call) -> None:
        call_expr = ast.unparse(node.func)
        call_lower = call_expr.lower()

        is_sink = False
        sink_category = "CONFIDENTIAL"

        if any(call_lower.startswith(pfx) for pfx in ["print", "sys.stdout", "sys.stderr"]):
            is_sink = True
            sink_category = "PUBLIC"
        elif any(log_term in call_lower for log_term in ["logger.", "logging.", "log.info", "log.debug", "log.warning", "log.error"]):
            is_sink = True
            sink_category = "PUBLIC"
        elif any(audit_term in call_lower for audit_term in ["auditlog", "audit_log", "record_audit", "log_audit"]):
            # Excluir operadores de lectura/consulta SQLAlchemy y validación Pydantic
            is_query_op = any(op in call_lower for op in [".desc", ".asc", ".ilike", ".like", ".offset", ".limit", ".filter", "model_validate", "order_by"])
            if not is_query_op:
                is_sink = True
                sink_category = "CONFIDENTIAL"

        if is_sink:
            caller_name = self.current_function or "global"
            sink_id = f"sink::{self.rel_path}::{caller_name}::{call_expr}"
            self.sinks.append({
                "id": sink_id,
                "name": f"{caller_name} -> {call_expr}",
                "file_path": self.rel_path,
                "class": sink_category,
                "caller": caller_name,
                "expr": call_expr,
                "line": node.lineno,
            })

        self.generic_visit(node)


class DataLineageEngine:
    """Motor Transversal de Grafo de Flujo de Datos (Data Lineage & Taint Analysis)
    agnóstico al repositorio, gobernado por las reglas de la Nueva Ley de Protección de Datos Personales.
    """

    def __init__(self, db_path: Path | str = DEFAULT_DB_PATH, rules_path: Path | str = RULES_PATH):
        self.db_path = Path(db_path)
        self.rules_path = Path(rules_path)
        self.categories: dict[str, Any] = {}
        self._load_compliance_ontology()

    def _load_compliance_ontology(self) -> None:
        """Carga el vocabulario y ontología de datos protegidos desde compliance_rules.json."""
        if self.rules_path.exists():
            data = json.loads(self.rules_path.read_text(encoding="utf-8"))
            self.categories = data.get("data_categories", {})
        else:
            self.categories = {
                "SENSITIVE_HEALTH": {
                    "fields": ["diagnosis", "clinical_notes", "medical_record", "treatment", "health_status", "status"]
                },
                "IDENTIFIER_RUT": {
                    "fields": ["identifier", "rut", "run", "dni", "national_id"]
                },
                "PERSONAL_CONTACT": {
                    "fields": ["telecom", "email", "phone", "address", "telefono"]
                },
            }

    def scan_and_build_lineage(
        self,
        root_dir: Path | str = WORKSPACE_ROOT,
        scan_dirs: list[Path] | None = None,
    ) -> int:
        """Escanea transversalmente el código fuente de la aplicación mediante AST,
        identificando fuentes, sumideros y trazando flujos de datos y mitigaciones de forma dinámica.
        """
        root = Path(root_dir)
        conn = get_db_connection(self.db_path)

        all_sources: list[dict[str, Any]] = []
        all_sinks: list[dict[str, Any]] = []
        file_scanners: dict[str, ASTLineageScanner] = {}

        # Escanear módulos de aplicación excluyendo harness, tests y entornos virtuales
        if scan_dirs is None:
            scan_dirs = [root / "src" / "database", root / "src" / "backend"]
        try:
            for sdir in scan_dirs:
                if not sdir.exists():
                    continue
                for py_file in sdir.rglob("*.py"):
                    rel_path = py_file.relative_to(root).as_posix()
                    # Reutilizar el nodo de archivo canónico de Graphify
                    file_row = conn.execute(
                        "SELECT id FROM graph_nodes WHERE file_path = ? AND node_type = 'file'",
                        (rel_path,),
                    ).fetchone()
                    if file_row:
                        file_node_id = file_row["id"]
                    else:
                        file_node_id = rel_path.replace("/", "_").replace(".", "_")
                        save_node(
                            conn,
                            node_id=file_node_id,
                            name=py_file.name,
                            node_type="file",
                            file_path=rel_path,
                            line_start=1,
                        )

                    try:
                        content = py_file.read_text(encoding="utf-8")
                        tree = ast.parse(content, filename=str(py_file))
                        scanner = ASTLineageScanner(py_file, rel_path, self.categories)
                        scanner.visit(tree)
                        file_scanners[rel_path] = scanner

                        # 1. Registrar Fuentes Sensibles (Sources)
                        for src in scanner.sources:
                            save_node(
                                conn,
                                node_id=src["id"],
                                name=src["name"],
                                node_type="source",
                                file_path=src["file_path"],
                                line_start=src["line"],
                                data_classification=src["category"],
                            )
                            save_edge(conn, file_node_id, src["id"], "CONTAINS")

                            # Vincular con la clase canónica de Graphify correspondiente si existe
                            class_row = conn.execute(
                                "SELECT id FROM graph_nodes WHERE file_path = ? AND name = ? AND node_type = 'class'",
                                (src["file_path"], src["class_name"]),
                            ).fetchone()
                            if class_row:
                                save_edge(conn, class_row["id"], src["id"], "CONTAINS")

                            all_sources.append(src)

                        # 2. Registrar Sumideros (Sinks)
                        for sk in scanner.sinks:
                            save_node(
                                conn,
                                node_id=sk["id"],
                                name=sk["name"],
                                node_type="sink",
                                file_path=sk["file_path"],
                                line_start=sk["line"],
                                data_classification=sk["class"],
                            )
                            save_edge(conn, file_node_id, sk["id"], "CALLS")
                            all_sinks.append(sk)

                        # 3. Registrar Sanitizadores
                        for san in scanner.sanitizers:
                            save_node(
                                conn,
                                node_id=san["id"],
                                name=san["name"],
                                node_type="sanitizer",
                                file_path=san["file_path"],
                                line_start=san["line"],
                            )

                    except Exception as ex:
                        print(f"Error procesando linaje en {rel_path}: {ex}")

            # 4. Trazabilidad Dinámica de Flujos (Taint Propagation)
            for rel_path, scanner in file_scanners.items():
                file_row = conn.execute(
                    "SELECT id FROM graph_nodes WHERE file_path = ? AND node_type = 'file'",
                    (rel_path,),
                ).fetchone()
                file_node_id = file_row["id"] if file_row else rel_path.replace("/", "_").replace(".", "_")
                has_audit_or_print = any("audit" in sk["expr"].lower() or "print" in sk["expr"].lower() or "logger" in sk["expr"].lower() for sk in scanner.sinks)

                if has_audit_or_print:
                    for src in all_sources:
                        field_lower = src["field_name"].lower()
                        is_sanitized = field_lower in scanner.sanitized_fields

                        if is_sanitized:
                            for sk in scanner.sinks:
                                save_edge(conn, src["id"], sk["id"], "SANITIZED_BY")
                        else:
                            save_edge(conn, src["id"], file_node_id, "FLOWS_TO")
                            for sk in scanner.sinks:
                                save_edge(conn, file_node_id, sk["id"], "FLOWS_TO")

            conn.commit()
            return len(all_sources) + len(all_sinks)
        finally:
            conn.close()

    def detect_violations(self) -> list[dict[str, Any]]:
        """Cruza el Grafo de Flujo de Datos con la Matriz de Cumplimiento Legal (compliance_rules).
        
        Detecta si un dato clasificado llega a un sumidero prohibido sin pasar por una arista SANITIZED_BY.
        """
        conn = get_db_connection(self.db_path)
        violations = []
        seen_violations: set[tuple[str, str, str]] = set()

        try:
            rules = conn.execute("SELECT * FROM compliance_rules").fetchall()

            for rule in rules:
                rule_id = rule["rule_id"]
                sens_cat = rule["sensitive_category"]
                prohibited_sinks = json.loads(rule["prohibited_sinks"])

                # Buscar fuentes clasificadas dinámicamente bajo esa categoría
                sources = conn.execute(
                    "SELECT id, name, file_path FROM graph_nodes WHERE data_classification = ? AND node_type = 'source'",
                    (sens_cat,),
                ).fetchall()

                for src in sources:
                    src_id = src["id"]
                    paths = self._find_paths_to_sinks(conn, src_id)

                    for path in paths:
                        sink_id = path[-1]
                        viol_key = (rule_id, src_id, sink_id)
                        if viol_key in seen_violations:
                            continue

                        # Comprobar si el sumidero coincide con la lista de prohibidos en la regla
                        is_prohibited = any(
                            psink.lower() in sink_id.lower() or (len(psink.split(".")[0]) > 3 and psink.split(".")[0].lower() in sink_id.lower())
                            for psink in prohibited_sinks
                        )

                        if is_prohibited:
                            has_mitigation = self._path_has_mitigation(conn, path, src_id)

                            if not has_mitigation:
                                seen_violations.add(viol_key)
                                finding_id = f"VULN-{uuid.uuid4().hex[:8].upper()}"
                                violation = {
                                    "finding_id": finding_id,
                                    "rule_id": rule_id,
                                    "title": rule["title"],
                                    "law_article": rule["law_article"],
                                    "severity": rule["severity"],
                                    "source": src_id,
                                    "sink": sink_id,
                                    "taint_path": path,
                                    "required_mitigations": json.loads(rule["required_mitigations"]),
                                }
                                violations.append(violation)

                                conn.execute(
                                    """
                                    INSERT OR REPLACE INTO compliance_findings 
                                    (id, rule_id, source_node_id, sink_node_id, taint_path_json, status)
                                    VALUES (?, ?, ?, ?, ?, 'OPEN')
                                    """,
                                    (finding_id, rule_id, src_id, sink_id, json.dumps(path)),
                                )
            conn.commit()
            return violations
        finally:
            conn.close()

    def _find_paths_to_sinks(self, conn: sqlite3.Connection, start_node: str, max_depth: int = 5) -> list[list[str]]:
        """Recorrido BFS determinista de caminos de contaminación (Source -> Sink)."""
        all_paths: list[list[str]] = []
        queue: list[list[str]] = [[start_node]]

        while queue:
            current_path = queue.pop(0)
            current_node = current_path[-1]

            if len(current_path) > max_depth:
                continue

            node_row = conn.execute(
                "SELECT node_type FROM graph_nodes WHERE id = ?", (current_node,)
            ).fetchone()
            if node_row and node_row["node_type"] == "sink" and len(current_path) > 1:
                all_paths.append(current_path)
                continue

            edges = conn.execute(
                "SELECT target_id FROM graph_edges WHERE source_id = ? AND edge_type = 'FLOWS_TO'",
                (current_node,),
            ).fetchall()

            for edge in edges:
                tgt = edge["target_id"]
                if tgt not in current_path:
                    queue.append(current_path + [tgt])

        return all_paths

    def _path_has_mitigation(self, conn: sqlite3.Connection, path: list[str], source_id: str) -> bool:
        """Determina si la fuente o alguno de los nodos del camino fue sanitizado o cifrado."""
        for node in path:
            sanitized = conn.execute(
                "SELECT id FROM graph_edges WHERE (source_id = ? OR target_id = ?) AND edge_type = 'SANITIZED_BY'",
                (node, node),
            ).fetchone()
            if sanitized:
                return True
        # También verificar si la fuente directamente tiene mitigación con el sumidero final
        sink_node = path[-1]
        direct_san = conn.execute(
            "SELECT id FROM graph_edges WHERE source_id = ? AND target_id = ? AND edge_type = 'SANITIZED_BY'",
            (source_id, sink_node),
        ).fetchone()
        return direct_san is not None
