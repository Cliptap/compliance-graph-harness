"""Reusable detection families driven by the control catalog.

A family is not a control: it is the implementation of a detection strategy
(sink exposure, retention-aware deletion, credential exposure). The catalog
selects the family and passes the parameters, so adding a control does not
require a new policy class.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

from src.harness.catalog import Catalog, Control
from src.harness.contracts import Finding, TaskSpec

LOG_PATTERNS = ("print", "logger.", "logging.", "console.log", "console.error",
                "sys.stdout", "sys.stderr")
RESPONSE_PATTERNS = ("JSONResponse", "Response", "jsonify")
REDIRECT_PATTERNS = ("RedirectResponse", "redirect")
DELETE_RE = re.compile(r"\bdelete\s+from\s+[\"'`]?([a-z_][a-z0-9_]*)", re.IGNORECASE)
TIMEDELTA_RE = re.compile(r"timedelta\s*\(\s*days\s*=\s*(\d+)", re.IGNORECASE)
INTERVAL_RE = re.compile(r"interval\s+'(\d+)\s+days?'", re.IGNORECASE)
MAKE_INTERVAL_RE = re.compile(r"make_interval\s*\(\s*days\s*=>\s*(\d+)", re.IGNORECASE)
TABLE_RE = re.compile(r"\bfrom\s+([a-z_][a-z0-9_]*)", re.IGNORECASE)
CSV_SINKS = ("writerow", "writer.writerow", "DictWriter.writerow")
HEADER_SECRET_RE = re.compile(
    r"headers?\s*(?:\.\s*get\(\s*|\[\s*)['\"]authorization['\"]|http_authorization",
    re.IGNORECASE,
)


def _call_name(node: ast.Call) -> str:
    func = node.func
    if isinstance(func, ast.Attribute):
        return f"{ast.unparse(func.value)}.{func.attr}"
    return getattr(func, "id", "")


def _is_log_sink(name: str) -> bool:
    """`log.info` is as common as `logger.info`; a bare substring match would catch `catalog.`."""
    if name.startswith("log."):
        return True
    return any(name.startswith(pattern) or pattern in name for pattern in LOG_PATTERNS)


def _enclosing_classes(tree: ast.AST) -> dict[int, str]:
    """Map each method node to the class that declares it, for context heuristics."""
    mapping: dict[int, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    mapping[id(child)] = node.name
    return mapping


def _dump_names(func: ast.AST) -> set[str]:
    """Names assigned from vars(obj) or obj.__dict__: returning them dumps every attribute."""
    names: set[str] = set()
    for node in ast.walk(func):
        if not isinstance(node, ast.Assign):
            continue
        value = node.value
        if (isinstance(value, ast.Call) and _call_name(value) == "vars") or (
                isinstance(value, ast.Attribute) and value.attr == "__dict__"):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    names.add(target.id)
    return names


def _finding(control: Control, path: str, line: int, message: str, evidence: str) -> Finding:
    return Finding(
        policy_id=control.id,
        severity=control.severity,
        status="VIOLATION",
        file=path,
        line=line,
        message=message,
        evidence=evidence,
        remediation_advice=control.remediation,
    )


def _skip_nodes(node: ast.AST) -> set[int]:
    """Names whose table taint must not be applied blindly.

    A subscript or attribute projects one field, and a comprehension target or
    iterable is not the value that reaches the sink. The whole-row cases
    (``dict(row)``) keep the table taint.
    """
    skip: set[int] = set()
    for child in ast.walk(node):
        if isinstance(child, (ast.Subscript, ast.Attribute)):
            skip.add(id(child.value))
        if isinstance(child, ast.comprehension):
            skip.add(id(child.iter))
            if isinstance(child.target, ast.Name):
                skip.add(id(child.target))
    return skip


def _leaf_functions(tree: ast.AST):
    for func in ast.walk(tree):
        if isinstance(func, (ast.FunctionDef, ast.AsyncFunctionDef)):
            nested = any(isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
                         for child in ast.walk(func) if child is not func)
            if not nested:
                yield func


def _identifier(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Constant):
        return node.slice.value if isinstance(node.slice.value, str) else None
    return None


class _TaintTracker(ast.NodeVisitor):
    """Propagate sensitive categories through simple assignments and SQL reads."""

    def __init__(self, catalog: Catalog, categories: set[str]):
        self.catalog = catalog
        self.categories = set(categories)
        self.env: dict[str, set[str]] = {}

    def scan(self, node: ast.AST) -> dict[str, set[str]]:
        self.visit(node)
        return self.env

    def visit_Assign(self, node: ast.Assign) -> None:
        categories = self._categories(node.value)
        for target in node.targets:
            self._taint(target, categories)
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        if node.value is not None:
            self._taint(node.target, self._categories(node.value))
        self.generic_visit(node)

    def visit_ListComp(self, node: ast.ListComp) -> None:
        self._taint_comprehension(node.generators)
        self.generic_visit(node)

    def visit_GeneratorExp(self, node: ast.GeneratorExp) -> None:
        self._taint_comprehension(node.generators)
        self.generic_visit(node)

    def visit_DictComp(self, node: ast.DictComp) -> None:
        self._taint_comprehension(node.generators)
        self.generic_visit(node)

    def _taint_comprehension(self, generators: list[ast.comprehension]) -> None:
        for generator in generators:
            categories = self._categories(generator.iter)
            if categories and isinstance(generator.target, ast.Name):
                self.env[generator.target.id] = self.env.get(generator.target.id, set()) | categories

    def _taint(self, target: ast.AST, categories: set[str]) -> None:
        if not categories:
            return
        if isinstance(target, ast.Name):
            self.env[target.id] = self.env.get(target.id, set()) | categories
        elif isinstance(target, ast.Subscript) and isinstance(target.value, ast.Name):
            self.env[target.value.id] = self.env.get(target.value.id, set()) | categories
        elif isinstance(target, (ast.Tuple, ast.List)):
            for element in target.elts:
                self._taint(element, categories)

    def _categories(self, node: ast.AST) -> set[str]:
        found: set[str] = set()
        sanitized: set[int] = set()
        for child in ast.walk(node):
            if isinstance(child, ast.Call) and self.catalog.is_sanitizer(ast.unparse(child)):
                for nested in ast.walk(child):
                    sanitized.add(id(nested))
        skip = _skip_nodes(node)
        dict_keys: set[int] = set()
        for child in ast.walk(node):
            if id(child) in sanitized:
                continue
            if isinstance(child, ast.Dict):
                for key, value in zip(child.keys, child.values):
                    if isinstance(key, ast.Constant) and isinstance(key.value, str):
                        dict_keys.add(id(key))
                        category = self.catalog.category_for(key.value)
                        if category in self.categories and not self.catalog.is_sanitizer(ast.unparse(value)):
                            found.add(category)
            elif isinstance(child, ast.Name) and child.id in self.env and id(child) not in skip:
                found |= self.env[child.id]
            elif isinstance(child, ast.Constant) and isinstance(child.value, str) and id(child) not in dict_keys:
                for table in TABLE_RE.findall(child.value.lower()):
                    found |= set(self.catalog.tables.get(table, ()))
                for category in self.categories:
                    if any(re.search(rf"\b{re.escape(synonym)}\b", child.value, re.IGNORECASE)
                           for synonym in self.catalog.synonyms(category)):
                        found.add(category)
            elif isinstance(child, (ast.Attribute, ast.Subscript)):
                token = _identifier(child)
                if token:
                    category = self.catalog.category_for(token)
                    if category:
                        found.add(category)
        return found & self.categories


class PolicyFamily:
    def __init__(self, catalog: Catalog):
        self.catalog = catalog

    def evaluate(self, control: Control, task: TaskSpec, files: dict[str, str]) -> list[Finding]:
        raise NotImplementedError


class SinkExposureFamily(PolicyFamily):
    """Sensitive data reaches a sink (log, response, redirect) without a sanitizer."""

    def evaluate(self, control: Control, task: TaskSpec, files: dict[str, str]) -> list[Finding]:
        findings: list[Finding] = []
        sinks = set(control.detection.sinks)
        categories = set(control.data_categories)
        for path, content in files.items():
            if not path.endswith(".py"):
                continue
            try:
                tree = ast.parse(content)
            except SyntaxError:
                continue
            if "log" in sinks:
                findings.extend(self._scan_logs(control, path, tree, categories))
            if "response" in sinks:
                findings.extend(self._scan_responses(control, path, tree, categories))
            if "redirect" in sinks:
                findings.extend(self._scan_redirects(control, path, tree, categories))
            if "csv" in sinks:
                findings.extend(self._scan_csv(control, path, tree, categories))
        return self._dedupe(findings)

    def _scan_logs(self, control, path, tree, categories) -> list[Finding]:
        out = []
        for func in _leaf_functions(tree):
            env = _TaintTracker(self.catalog, categories).scan(func)
            for node in ast.walk(func):
                if not isinstance(node, ast.Call):
                    continue
                name = _call_name(node)
                if not _is_log_sink(name):
                    continue
                text = ast.unparse(node)
                if self.catalog.is_sanitizer(text):
                    continue
                matched = self._categories(node, categories, env)
                if matched:
                    out.append(_finding(control, path, node.lineno,
                                        f"Log call exposes {sorted(matched)} without masking.", text))
        return out

    def _scan_responses(self, control, path, tree, categories) -> list[Finding]:
        out = []
        admin_only = control.detection.context.get("route") == "admin"
        enclosing = _enclosing_classes(tree)
        for func in _leaf_functions(tree):
            class_name = enclosing.get(id(func), "")
            if (admin_only and "admin" not in func.name.lower()
                    and "admin" not in self._decorators(func).lower()
                    and "admin" not in class_name.lower()):
                continue
            env = _TaintTracker(self.catalog, categories).scan(func)
            dumps = _dump_names(func)
            for node in ast.walk(func):
                payload = None
                if isinstance(node, ast.Return):
                    value = node.value
                    if isinstance(value, ast.Name) and value.id in dumps \
                            and categories & {"CREDENTIAL", "PERSONAL_CONTACT"}:
                        out.append(_finding(control, path, node.lineno,
                                            f"Response returns '{value.id}', a dump of all object attributes.",
                                            ast.unparse(node)))
                        continue
                    if isinstance(value, (ast.Dict, ast.List, ast.Tuple, ast.ListComp, ast.SetComp)):
                        payload = value
                    elif isinstance(value, ast.Call) and (
                            _call_name(value) in RESPONSE_PATTERNS or _call_name(value) == "dict"):
                        payload = value
                elif isinstance(node, ast.Call) and _call_name(node) in RESPONSE_PATTERNS:
                    payload = node
                if payload is None:
                    continue
                text = ast.unparse(payload)
                if self.catalog.is_sanitizer(text):
                    continue
                matched = self._categories(payload, categories, env)
                if matched:
                    out.append(_finding(control, path, payload.lineno,
                                        f"Response exposes {sorted(matched)} without masking.", text))
        return out

    def _scan_redirects(self, control, path, tree, categories) -> list[Finding]:
        out = []
        for func in _leaf_functions(tree):
            env = _TaintTracker(self.catalog, categories).scan(func)
            for node in ast.walk(func):
                if not isinstance(node, ast.Call) or _call_name(node) not in REDIRECT_PATTERNS:
                    continue
                text = ast.unparse(node)
                if self.catalog.is_sanitizer(text):
                    continue
                matched = self._categories(node, categories, env)
                if matched:
                    out.append(_finding(control, path, node.lineno,
                                        f"Redirect exposes {sorted(matched)}.", text))
        return out

    def _scan_csv(self, control, path, tree, categories) -> list[Finding]:
        out = []
        for func in _leaf_functions(tree):
            env = _TaintTracker(self.catalog, categories).scan(func)
            for node in ast.walk(func):
                if not isinstance(node, ast.Call) or _call_name(node) not in CSV_SINKS:
                    continue
                text = ast.unparse(node)
                if self.catalog.is_sanitizer(text):
                    continue
                matched = self._categories(node, categories, env)
                if matched:
                    out.append(_finding(control, path, node.lineno,
                                        f"CSV row exposes {sorted(matched)} without masking.", text))
        return out

    def _value_is_masked(self, value: ast.AST) -> bool:
        """A per-field mask or a derived flag does not expose the underlying value."""
        if isinstance(value, ast.JoinedStr):
            return any(isinstance(part, ast.Constant) and isinstance(part.value, str)
                       and "*" in part.value for part in value.values)
        if isinstance(value, ast.Call):
            leaf = _call_name(value).rsplit(".", 1)[-1]
            if leaf in {"bool", "len", "any", "all"}:
                return True
            return self.catalog.is_sanitizer(ast.unparse(value))
        if isinstance(value, ast.Compare):
            return True
        if isinstance(value, ast.UnaryOp) and isinstance(value.op, ast.Not):
            return True
        return False

    def _categories(self, node: ast.AST, allowed: set[str],
                    env: dict[str, set[str]] | None = None) -> set[str]:
        found: set[str] = set()
        skip = _skip_nodes(node)
        for child in ast.walk(node):
            if id(child) in skip:
                continue
            if isinstance(child, ast.Name) and env and child.id in env:
                found |= env[child.id] & allowed
            elif isinstance(child, ast.Dict):
                for key, value in zip(child.keys, child.values):
                    if self._value_is_masked(value):
                        for nested in ast.walk(value):
                            skip.add(id(nested))
                        skip.add(id(key))
                        continue
                    if isinstance(key, ast.Constant) and isinstance(key.value, str):
                        category = self.catalog.category_for(key.value)
                        if category in allowed:
                            found.add(category)
            elif isinstance(child, (ast.Name, ast.Attribute, ast.Subscript)):
                token = _identifier(child)
                category = self.catalog.category_for(token) if token else None
                if category in allowed:
                    found.add(category)
            elif isinstance(child, ast.Constant) and isinstance(child.value, str):
                for category in allowed:
                    if any(re.search(rf"\b{re.escape(s)}\b", child.value, re.IGNORECASE)
                           for s in self.catalog.synonyms(category)):
                        found.add(category)
        return found

    @staticmethod
    def _decorators(func: ast.AST) -> str:
        return " ".join(ast.unparse(decorator) for decorator in getattr(func, "decorator_list", []))

    @staticmethod
    def _dedupe(findings: list[Finding]) -> list[Finding]:
        seen = set()
        out = []
        for finding in findings:
            key = (finding.policy_id, finding.file, finding.line, finding.message)
            if key not in seen:
                seen.add(key)
                out.append(finding)
        return out


class RetentionDeletionFamily(PolicyFamily):
    """A destructive operation removes records before their retention period ends."""

    def evaluate(self, control: Control, task: TaskSpec, files: dict[str, str]) -> list[Finding]:
        params = control.detection.params
        tables = {table.lower() for table in params.get("tables", ())}
        retention_days = int(params.get("retention_days", 0))
        retention_field = str(params.get("retention_field", "retention_days")).lower()
        out: list[Finding] = []
        for path, content in files.items():
            if path.endswith(".py"):
                try:
                    tree = ast.parse(content)
                except SyntaxError:
                    continue
                out.extend(self._scan_tree(control, path, tree, tables, retention_days, retention_field))
            elif path.endswith(".sql"):
                out.extend(self._scan_sql(control, path, content, tables, retention_days, retention_field))
        seen: set[tuple[str, int]] = set()
        unique: list[Finding] = []
        for finding in out:
            key = (finding.file, finding.line)
            if key not in seen:
                seen.add(key)
                unique.append(finding)
        return unique

    def _scan_tree(self, control, path, tree, tables, retention_days, retention_field):
        constants = _int_constants(tree)
        out: list[Finding] = []
        for func in _leaf_functions(tree):
            cutoff = _max_cutoff(func, constants)
            if cutoff is not None and cutoff >= retention_days:
                continue
            if cutoff is None and _mentions_retention_field(func, retention_field):
                continue
            out.extend(self._deletes_in(control, path, func, tables))
        for stmt in tree.body:
            if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                continue
            cutoff = _max_cutoff(stmt, constants)
            if cutoff is not None and cutoff >= retention_days:
                continue
            if cutoff is None and _mentions_retention_field(stmt, retention_field):
                continue
            out.extend(self._deletes_in(control, path, stmt, tables))
        return out

    @staticmethod
    def _deletes_in(control, path, node, tables):
        out: list[Finding] = []
        for child in ast.walk(node):
            matched = _delete_tables(child) & tables
            if not matched:
                continue
            table = sorted(matched)[0]
            out.append(_finding(control, path, getattr(child, "lineno", 1),
                                f"{table} is deleted before its retention period ends.",
                                ast.unparse(child)[:200]))
        return out

    @staticmethod
    def _scan_sql(control, path, content, tables, retention_days, retention_field):
        lowered = content.lower()
        if retention_field and retention_field in lowered:
            return []
        cutoffs = [int(value) for value in TIMEDELTA_RE.findall(content)]
        cutoffs += [int(value) for value in INTERVAL_RE.findall(content)]
        cutoffs += [int(value) for value in MAKE_INTERVAL_RE.findall(content)]
        if cutoffs and max(cutoffs) >= retention_days:
            return []
        out: list[Finding] = []
        for line_no, line in enumerate(content.splitlines(), 1):
            match = DELETE_RE.search(line.lower())
            if match and match.group(1) in tables:
                out.append(_finding(control, path, line_no,
                                    f"{match.group(1)} is deleted before its retention period ends.",
                                    line.strip()))
        return out


def _int_constants(tree: ast.AST) -> dict[str, int]:
    constants: dict[str, int] = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            args = node.args.args[-len(node.args.defaults):] if node.args.defaults else []
            for arg, default in zip(args, node.args.defaults):
                if isinstance(default, ast.Constant) and isinstance(default.value, int):
                    constants[arg.arg] = default.value
            continue
        targets: list[ast.AST] = []
        value = None
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant) \
                and isinstance(node.value.value, int):
            targets, value = node.targets, node.value.value
        elif isinstance(node, ast.AnnAssign) and isinstance(node.value, ast.Constant) \
                and isinstance(node.value.value, int):
            targets, value = [node.target], node.value.value
        if value is None:
            continue
        for target in targets:
            if isinstance(target, ast.Name):
                constants[target.id] = value
            elif isinstance(target, ast.Attribute):
                constants[target.attr] = value
    return constants


def _int_value(node: ast.AST, constants: dict[str, int]) -> int | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, int):
        return node.value
    if isinstance(node, ast.Name):
        return constants.get(node.id)
    if isinstance(node, ast.Attribute):
        return constants.get(node.attr)
    return None


def _max_cutoff(node: ast.AST, constants: dict[str, int]) -> int | None:
    values = []
    for child in ast.walk(node):
        if isinstance(child, ast.Call) and _call_name(child).endswith("timedelta"):
            for kw in child.keywords:
                if kw.arg == "days":
                    value = _int_value(kw.value, constants)
                    if value is not None:
                        values.append(value)
        elif isinstance(child, ast.Constant) and isinstance(child.value, str):
            values.extend(int(value) for value in INTERVAL_RE.findall(child.value))
            values.extend(int(value) for value in MAKE_INTERVAL_RE.findall(child.value))
    return max(values) if values else None


def _mentions_retention_field(node: ast.AST, field: str) -> bool:
    if not field:
        return False
    return field in ast.unparse(node).lower()


def _table_candidates(name: str) -> set[str]:
    base = name.lower()
    return {base, base + "s", base.rstrip("s")}


def _query_model(func: ast.AST) -> str | None:
    value = getattr(func, "value", None)
    while isinstance(value, ast.Call):
        name = _call_name(value)
        if name == "query" or name.endswith(".query"):
            if value.args and isinstance(value.args[0], (ast.Name, ast.Attribute)):
                return _identifier(value.args[0])
            return None
        value = getattr(value.func, "value", None)
    return None


def _delete_tables(node: ast.AST) -> set[str]:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        match = DELETE_RE.search(node.value.lower())
        return {match.group(1)} if match else set()
    if not isinstance(node, ast.Call):
        return set()
    name = _call_name(node)
    if name == "delete" or name.endswith(".delete"):
        if node.args:
            arg = node.args[0]
            if isinstance(arg, (ast.Name, ast.Attribute)):
                token = _identifier(arg)
                return _table_candidates(token) if token else set()
        model = _query_model(node.func)
        return _table_candidates(model) if model else set()
    return set()


class CredentialExposureFamily(PolicyFamily):
    """A credential (reset token, API key, session token) reaches a response, redirect or log."""

    def evaluate(self, control: Control, task: TaskSpec, files: dict[str, str]) -> list[Finding]:
        params = control.detection.params
        keys = tuple(params.get("keys", ()))
        value_pattern = params.get("value_pattern")
        sinks = set(control.detection.sinks)
        out: list[Finding] = []
        for path, content in files.items():
            if not path.endswith(".py"):
                continue
            try:
                tree = ast.parse(content)
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                if not self._is_sink(node, sinks):
                    continue
                text = ast.unparse(node)
                if self.catalog.is_sanitizer(text):
                    continue
                if (self._matches(text, keys, value_pattern)
                        or self._logs_token(node, sinks, keys)
                        or self._returns_secret_attribute(node, sinks, keys)):
                    out.append(_finding(control, path, getattr(node, "lineno", 1),
                                        "A credential reaches a response, redirect or log.", text))
        return out

    @staticmethod
    def _logs_token(node: ast.AST, sinks: set[str], keys: tuple[str, ...]) -> bool:
        if "log" not in sinks or not isinstance(node, ast.Call):
            return False
        if not any(key in {"token", "reset_token"} for key in keys):
            return False
        arguments = " ".join(ast.unparse(arg) for arg in node.args[1:])
        arguments += " " + " ".join(ast.unparse(kw.value) for kw in node.keywords)
        return bool(re.search(r"\btoken\b", arguments, re.IGNORECASE))

    def _returns_secret_attribute(self, node: ast.AST, sinks: set[str],
                                  keys: tuple[str, ...]) -> bool:
        if "response" not in sinks or not isinstance(node, ast.Return):
            return False
        if not any(key in {"api_key", "api-key", "secret"} for key in keys):
            return False
        values = node.value.values if isinstance(node.value, ast.Dict) else []
        return any(
            isinstance(item, ast.Attribute)
            and any(term in item.attr.lower() for term in ("secret", "api_key"))
            and not self.catalog.is_sanitizer(ast.unparse(item))
            for item in values
        )

    @staticmethod
    def _is_sink(node: ast.AST, sinks: set[str]) -> bool:
        if "response" in sinks and isinstance(node, ast.Return):
            value = node.value
            return (isinstance(value, (ast.Dict, ast.List, ast.Tuple))
                    or (isinstance(value, ast.Call) and _call_name(value) in RESPONSE_PATTERNS))
        if isinstance(node, ast.Call):
            name = _call_name(node)
            if "response" in sinks and name in RESPONSE_PATTERNS:
                return True
            if "redirect" in sinks and name in REDIRECT_PATTERNS:
                return True
            if "log" in sinks and _is_log_sink(name):
                return True
        return False

    @staticmethod
    def _matches(text: str, keys: tuple[str, ...], value_pattern: str | None) -> bool:
        if HEADER_SECRET_RE.search(text) and any(
                "key" in key.lower() or key.lower() == "secret" for key in keys):
            return True
        for key in keys:
            if re.search(rf'["\']{re.escape(key)}["\']\s*:', text, re.IGNORECASE):
                return True
            if re.search(rf"\b{re.escape(key)}\b\s*=", text, re.IGNORECASE):
                return True
        if value_pattern and re.search(value_pattern, text, re.IGNORECASE):
            return True
        return False
