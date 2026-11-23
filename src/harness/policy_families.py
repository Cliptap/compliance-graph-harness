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

RUT_VALUE_RE = re.compile(r"\b\d{1,2}\.?\d{3}\.?\d{3}-?[\dkK]\b")
AMBIGUOUS_TEXT_SYNONYMS = {"run"}
PROSE_SYNONYMS = {"email", "phone", "address", "token", "secret", "password", "session", "cookie"}


def _constant_matches(text: str, synonyms: list[str]) -> bool:
    """``run`` is also English prose; only count it next to a RUT-shaped value."""
    lowered = text.lower()
    has_rut_value = bool(RUT_VALUE_RE.search(text))
    for synonym in synonyms:
        term = synonym.lower()
        if term in AMBIGUOUS_TEXT_SYNONYMS:
            if term in lowered and has_rut_value:
                return True
            continue
        if term in PROSE_SYNONYMS:
            pattern = (
                rf"\b{re.escape(term)}\b\s*[:=]\s*"
                r"(?:[\w.+-]+@[\w.-]+|[+]?\d[\d\s().-]{4,}|[A-Za-z][\w .-]*)"
            )
            if re.search(pattern, text, re.IGNORECASE):
                return True
            continue
        if re.search(rf"\b{re.escape(synonym)}\b", text, re.IGNORECASE):
            return True
    return False

LOG_PATTERNS = ("print", "logger.", "logging.", "console.log", "console.error",
                "sys.stdout", "sys.stderr", "stdout.write", "stderr.write")
RESPONSE_PATTERNS = ("JSONResponse", "JsonResponse", "Response", "jsonify", "PlainTextResponse",
                    "HTMLResponse", "HttpResponse", "StreamingResponse")
REDIRECT_PATTERNS = ("RedirectResponse", "redirect")
DELETE_RE = re.compile(r"\bdelete\s+from\s+[\"'`]?([a-z_][a-z0-9_]*)", re.IGNORECASE)
DJANGO_OBJECTS_RE = re.compile(r"\b([A-Z][A-Za-z0-9_]*)\.objects\b")
DERIVED_FIELD_SUFFIXES = ("_configured", "_suffix", "_last4", "_preview", "_enabled")
DERIVED_IDENTIFIER_PREFIXES = ("with_", "without_", "has_", "is_")
METADATA_FIELD_SUFFIXES = ("_ttl", "_minutes", "_updated_at", "_count", "_enabled", "_configured",
                           "_suffix", "_last4", "_preview", "_verified", "_confirmed", "_fp",
                           "_hash", "_id", "_at", "_algorithm", "_status", "_policy", "_ref",
                           "_version", "_masked")
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


MASK_NAME_HINTS = ("mask", "redact", "anonym", "obfuscat", "sanitiz", "hash", "fingerprint")
MASK_NAME_SUFFIXES = ("_masked", "_mask", "_suffix", "_last4", "_preview", "_fp", "_hash",
                      "_fingerprint", "_redacted")


def _exact_category(catalog: Catalog, field: str) -> str | None:
    lowered = field.lower()
    for category in catalog.data_categories:
        if lowered in catalog.synonyms(category):
            return category
    return None


def _field_category(catalog: Catalog, field: str) -> str | None:
    """Exact synonym first, then a guarded fuzzy match (``phone_number`` -> phone)."""
    lowered = field.lower()
    for category in catalog.data_categories:
        if lowered in catalog.synonyms(category):
            return category
    if lowered.startswith(DERIVED_IDENTIFIER_PREFIXES) or lowered.endswith(METADATA_FIELD_SUFFIXES):
        return None
    for category in catalog.data_categories:
        for synonym in catalog.synonyms(category):
            if len(synonym) > 3 and synonym in lowered:
                return category
    return None


def _is_masking_name(name: str) -> bool:
    lowered = name.lower()
    return any(hint in lowered for hint in MASK_NAME_HINTS) or lowered.endswith(MASK_NAME_SUFFIXES)


def _value_is_masked(catalog: Catalog, value: ast.AST) -> bool:
    """A per-field mask or a derived flag does not expose the underlying value."""
    if isinstance(value, ast.JoinedStr):
        return any(isinstance(part, ast.Constant) and isinstance(part.value, str)
                   and "*" in part.value for part in value.values)
    if isinstance(value, ast.Call):
        leaf = _call_name(value).rsplit(".", 1)[-1]
        if leaf in {"bool", "len", "any", "all"} or _is_masking_name(leaf):
            return True
        return catalog.is_sanitizer(ast.unparse(value))
    if isinstance(value, ast.Subscript):
        return not (isinstance(value.slice, ast.Constant) and isinstance(value.slice.value, str))
    if isinstance(value, ast.IfExp):
        return _value_is_masked(catalog, value.body) and _value_is_masked(catalog, value.orelse)
    if isinstance(value, ast.Constant) and value.value is None:
        return True
    if isinstance(value, (ast.Name, ast.Attribute)):
        token = _identifier(value)
        if not token or _exact_category(catalog, token):
            return False
        return _is_masking_name(token)
    if isinstance(value, ast.Compare):
        return True
    if isinstance(value, ast.UnaryOp) and isinstance(value.op, ast.Not):
        return True
    return False


def _has_credential_call(catalog: Catalog, node: ast.AST) -> bool:
    """A call that issues or retrieves a credential: ``tokens.create``, ``config.load_secret``.

    Only the call chain is followed: a credential-shaped call passed as an *argument*
    (``User.objects.create(password=make_password(...))``) does not make the result a secret.
    """
    current = node
    while current is not None:
        if isinstance(current, ast.Call):
            leaf = _call_name(current).rsplit(".", 1)[-1]
            if leaf.islower() and _field_category(catalog, leaf) == "CREDENTIAL":
                return True
            func = current.func
            current = func.value if isinstance(func, ast.Attribute) else None
            continue
        if isinstance(current, ast.Attribute):
            current = current.value
            continue
        if isinstance(current, ast.Name):
            return current.id.islower() and _field_category(catalog, current.id) == "CREDENTIAL"
        return False
    return False


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
    """Names assigned from vars(obj), obj.__dict__ or dict(obj.__dict__): they dump every attribute."""
    names: set[str] = set()
    for node in ast.walk(func):
        if not isinstance(node, ast.Assign):
            continue
        value = node.value
        is_dump = (
            (isinstance(value, ast.Call) and _call_name(value) == "vars")
            or (isinstance(value, ast.Attribute) and value.attr == "__dict__")
            or (isinstance(value, ast.Call) and _call_name(value) == "dict"
                and value.args and isinstance(value.args[0], ast.Attribute)
                and value.args[0].attr == "__dict__")
        )
        if is_dump:
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


VALUE_ACCESSORS = {"value", "raw"}
IMPORT_VERBS = {"format", "build", "render", "issue", "generate", "make", "compose", "get",
                "load", "fetch", "read", "describe", "export", "serialize", "summarize",
                "decrypt", "parse", "create"}
PASSTHROUGH_CALLS = {"dict", "list", "tuple", "set", "str", "jsonify", "JsonResponse",
                     "JSONResponse", "Response", "RedirectResponse", "execute", "executemany",
                     "fetchone", "fetchall", "fetchmany", "mappings", "scalars", "scalar",
                     "query", "filter", "filter_by", "where", "first", "one", "all", "get",
                     "count", "values", "zip", "enumerate", "sorted", "reversed", "next", "iter",
                     "join", "format", "replace", "strip", "lstrip", "rstrip", "lower", "upper",
                     "title", "split", "rsplit", "partition", "encode", "decode",
                     "dumps", "dump", "loads", "load"}


def _skip_nodes(node: ast.AST) -> set[int]:
    """Comprehension targets and iterables are not the value that reaches the sink."""
    skip: set[int] = set()
    for child in ast.walk(node):
        if isinstance(child, ast.comprehension):
            skip.add(id(child.iter))
            if isinstance(child.target, ast.Name):
                skip.add(id(child.target))
    return skip


def _projection_tokens(node: ast.AST) -> dict[int, str]:
    """Map a projected base node to the field it exposes (``row.email`` -> ``email``)."""
    tokens: dict[int, str] = {}
    for child in ast.walk(node):
        if isinstance(child, ast.Attribute):
            tokens[id(child.value)] = child.attr
        elif isinstance(child, ast.Subscript):
            token = _identifier(child)
            if token is not None:
                tokens[id(child.value)] = token
    return tokens


def _projects_value(catalog: Catalog, token: str | None) -> bool:
    """A whole-object base only carries its taint into ``.value`` or a field it names."""
    if token is None:
        return True
    return token in VALUE_ACCESSORS or _field_category(catalog, token) is not None


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


def _imported_names(tree: ast.AST) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            names.update(alias.asname or alias.name for alias in node.names)
        elif isinstance(node, ast.Import):
            names.update(alias.asname or alias.name.split(".")[0] for alias in node.names)
    return names


def _name_categories(catalog: Catalog, name: str) -> set[str]:
    """An imported producer whose name states its payload: ``format_rut_and_email``."""
    tokens = [token for token in re.split(r"[^a-z0-9]+", name.lower()) if token]
    if not tokens or tokens[0] not in IMPORT_VERBS:
        return set()
    found: set[str] = set()
    for category in catalog.data_categories:
        synonyms = catalog.synonyms(category)
        if any(token in synonyms for token in tokens):
            found.add(category)
            continue
        lowered = name.lower().replace("-", "_")
        if any(len(synonym) > 3 and synonym.replace("-", "_") in lowered for synonym in synonyms):
            found.add(category)
    return found


def _serializer_field_leak(catalog: Catalog, cls: ast.ClassDef,
                           categories: set[str]) -> str | None:
    """A DRF serializer field whose name or ``source`` exposes a sensitive category."""
    meta = next((item for item in cls.body
                 if isinstance(item, ast.ClassDef) and item.name == "Meta"), None)
    if meta is None:
        return None
    fields: list[str] = []
    for stmt in meta.body:
        if not isinstance(stmt, ast.Assign):
            continue
        if not any(isinstance(target, ast.Name) and target.id == "fields"
                   for target in stmt.targets):
            continue
        if isinstance(stmt.value, (ast.List, ast.Tuple)):
            fields = [element.value for element in stmt.value.elts
                      if isinstance(element, ast.Constant) and isinstance(element.value, str)]
    if not fields:
        return None
    write_only: set[str] = set()
    sources: dict[str, str] = {}
    masked: set[str] = set()
    for stmt in cls.body:
        if isinstance(stmt, ast.Assign):
            for target in stmt.targets:
                if not isinstance(target, ast.Name):
                    continue
                if isinstance(stmt.value, ast.Call):
                    keywords = {keyword.arg: keyword.value for keyword in stmt.value.keywords}
                    if isinstance(keywords.get("write_only"), ast.Constant) \
                            and keywords["write_only"].value is True:
                        write_only.add(target.id)
                    source = keywords.get("source")
                    if isinstance(source, ast.Constant) and isinstance(source.value, str):
                        sources[target.id] = source.value
        elif isinstance(stmt, ast.FunctionDef) and stmt.name.startswith("get_"):
            field = stmt.name[4:]
            for node in ast.walk(stmt):
                if isinstance(node, ast.Return) and node.value is not None \
                        and _value_is_masked(catalog, node.value):
                    masked.add(field)
    for field in fields:
        if field in write_only or field in masked:
            continue
        if field.lower().endswith(DERIVED_FIELD_SUFFIXES):
            continue
        category = _field_category(catalog, field)
        if category not in categories and field in sources:
            category = _field_category(catalog, sources[field])
        if category in categories:
            return field
    return None


def _serializer_scan(catalog: Catalog, tree: ast.AST, categories: set[str],
                     admin_only: bool, path: str) -> list[tuple[ast.ClassDef, str]]:
    found: list[tuple[ast.ClassDef, str]] = []
    for cls in (node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)):
        if admin_only and "admin" not in cls.name.lower() and "admin" not in path.lower():
            continue
        field = _serializer_field_leak(catalog, cls, categories)
        if field:
            found.append((cls, field))
    return found


ENDPOINT_MARKERS = ("router.", "app.", "shared_task", "api_view", "action(", ".get(",
                    ".post(", ".put(", ".delete(", ".patch(")


def _is_endpoint(func: ast.AST) -> bool:
    text = " ".join(ast.unparse(decorator)
                    for decorator in getattr(func, "decorator_list", [])).lower()
    return any(marker in text for marker in ENDPOINT_MARKERS)


def _field_lists(tree: ast.AST, catalog: Catalog, categories: set[str]) -> dict[str, set[str]]:
    """Literal field lists (``self.columns = ['id', 'rut', 'email']``) by name."""
    mapping: dict[str, set[str]] = {}
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Assign, ast.AnnAssign)) or node.value is None:
            continue
        if not isinstance(node.value, (ast.List, ast.Tuple)):
            continue
        found: set[str] = set()
        for element in node.value.elts:
            if isinstance(element, ast.Constant) and isinstance(element.value, str):
                category = _field_category(catalog, element.value)
                if category in categories:
                    found.add(category)
        if not found:
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        for target in targets:
            token = _identifier(target)
            if token:
                mapping[token] = mapping.get(token, set()) | found
    return mapping


def _sink_categories(catalog: Catalog, node: ast.AST, allowed: set[str],
                     env: dict[str, set[str]] | None = None,
                     summaries: dict[str, set[str]] | None = None,
                     param_returns: dict[str, set[int | str]] | None = None,
                     field_lists: dict[str, set[str]] | None = None,
                     attr_categories: dict[str, set[str]] | None = None) -> set[str]:
    """Categories that reach a sink, following local variables and helper summaries."""
    found: set[str] = set()
    comprehension_skip = _skip_nodes(node)
    projection = _projection_tokens(node)
    callees = {id(child.func) for child in ast.walk(node) if isinstance(child, ast.Call)}
    masked_calls: set[int] = set()
    for child in ast.walk(node):
        if isinstance(child, ast.Call) and _is_masking_name(_call_name(child).rsplit(".", 1)[-1]):
            for nested in ast.walk(child):
                masked_calls.add(id(nested))
    blocked_args: set[int] = set()
    for child in ast.walk(node):
        if not isinstance(child, ast.Call):
            continue
        leaf = _call_name(child).rsplit(".", 1)[-1]
        full = _call_name(child)
        if (leaf in PASSTHROUGH_CALLS or _is_masking_name(leaf)
                or (child is node and (full in RESPONSE_PATTERNS or full in REDIRECT_PATTERNS
                                       or _is_log_sink(full) or leaf in CSV_SINKS))):
            continue
        positions = (param_returns or {}).get(leaf, set())
        for index, arg in enumerate(child.args):
            if index in positions and not _value_is_masked(catalog, arg):
                continue
            for nested in ast.walk(arg):
                blocked_args.add(id(nested))
        for keyword in child.keywords:
            if keyword.arg in positions and not _value_is_masked(catalog, keyword.value):
                continue
            for nested in ast.walk(keyword.value):
                blocked_args.add(id(nested))
    blocked: set[int] = set()
    for child in ast.walk(node):
        if id(child) in blocked or id(child) in comprehension_skip or id(child) in masked_calls \
                or id(child) in blocked_args:
            continue
        if id(child) in projection and not (
                isinstance(child, ast.Name) and env and child.id in env
                and _projects_value(catalog, projection[id(child)])):
            continue
        if isinstance(child, ast.Name) and env and child.id in env:
            found |= env[child.id] & allowed
        elif isinstance(child, ast.Call):
            leaf = _call_name(child).rsplit(".", 1)[-1]
            if not _is_masking_name(leaf):
                found |= (summaries or {}).get(leaf, set()) & allowed
                if leaf == "get" and child.args and isinstance(child.args[0], ast.Constant) \
                        and isinstance(child.args[0].value, str):
                    category = _field_category(catalog, child.args[0].value)
                    if category in allowed:
                        found.add(category)
                positions = (param_returns or {}).get(leaf, set())
                for index, arg in enumerate(child.args):
                    if index in positions and not _value_is_masked(catalog, arg):
                        found |= _sink_categories(catalog, arg, allowed, env, summaries,
                                                  param_returns, field_lists)
                for keyword in child.keywords:
                    if keyword.arg in positions and not _value_is_masked(catalog, keyword.value):
                        found |= _sink_categories(catalog, keyword.value, allowed, env, summaries,
                                                  param_returns, field_lists)
        elif isinstance(child, ast.Dict):
            for key, value in zip(child.keys, child.values):
                if _value_is_masked(catalog, value):
                    for nested in ast.walk(value):
                        blocked.add(id(nested))
                    blocked.add(id(key))
                    continue
                if isinstance(key, ast.Constant) and isinstance(key.value, str):
                    category = _field_category(catalog, key.value)
                    if category in allowed:
                        found.add(category)
        elif isinstance(child, ast.DictComp) and field_lists:
            key = child.key
            for generator in child.generators:
                token = _identifier(generator.iter)
                if token in field_lists and isinstance(key, ast.Name) \
                        and isinstance(generator.target, ast.Name) \
                        and generator.target.id == key.id:
                    found |= field_lists[token] & allowed
        elif isinstance(child, (ast.Name, ast.Attribute, ast.Subscript)):
            if id(child) in callees:
                continue
            if isinstance(child, ast.Attribute) and attr_categories \
                    and isinstance(child.value, ast.Name) and child.value.id in {"self", "cls"}:
                found |= attr_categories.get(child.attr, set()) & allowed
            token = _identifier(child)
            category = _field_category(catalog, token) if token else None
            if category in allowed:
                found.add(category)
        elif isinstance(child, ast.Constant) and isinstance(child.value, str):
            for category in allowed:
                if _constant_matches(child.value, catalog.synonyms(category)):
                    found.add(category)
    return found


def _self_attribute(target: ast.AST) -> str | None:
    if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) \
            and target.value.id in {"self", "cls"}:
        return target.attr
    if isinstance(target, ast.Subscript):
        base = target.value
        if isinstance(base, ast.Attribute) and isinstance(base.value, ast.Name) \
                and base.value.id in {"self", "cls"}:
            return base.attr
    return None


def _class_attr_categories(tree: ast.AST, catalog: Catalog, categories: set[str],
                           summaries: dict[str, set[str]],
                           param_returns: dict[str, set[int | str]] | None = None
                           ) -> dict[str, dict[str, set[str]]]:
    """Instance attributes mutated with sensitive values (``self._payload['email']``)."""
    result: dict[str, dict[str, set[str]]] = {}
    module_constants = _module_constants(tree)
    class_constants = _class_constants(tree)
    for cls in (node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)):
        attrs: dict[str, set[str]] = {}
        methods = [item for item in cls.body
                   if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))]
        for _ in range(2):
            changed = False
            for method in methods:
                env = _TaintTracker(catalog, categories, summaries, param_returns, attrs,
                                    module_constants, class_constants.get(cls.name, {})).scan(method)
                for node in ast.walk(method):
                    if not isinstance(node, (ast.Assign, ast.AnnAssign)) or node.value is None:
                        continue
                    if _value_is_masked(catalog, node.value):
                        continue
                    found = _sink_categories(catalog, node.value, categories, env, summaries,
                                             param_returns, None, attrs)
                    targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                    for target in targets:
                        attr = _self_attribute(target)
                        if attr is None:
                            continue
                        if isinstance(target, ast.Subscript) and isinstance(target.slice, ast.Constant) \
                                and isinstance(target.slice.value, str):
                            category = _field_category(catalog, target.slice.value)
                            if category in categories:
                                found = found | {category}
                        if found - attrs.get(attr, set()):
                            attrs[attr] = attrs.get(attr, set()) | found
                            changed = True
            if not changed:
                break
        if attrs:
            result[cls.name] = attrs
    return result


def _effect_matched(catalog: Catalog, node: ast.Call, positions: set[int | str],
                    allowed: set[str], env: dict[str, set[str]] | None,
                    summaries: dict[str, set[str]] | None,
                    param_returns: dict[str, set[int | str]] | None,
                    field_lists: dict[str, set[str]] | None,
                    attr_categories: dict[str, set[str]] | None = None) -> set[str]:
    """Categories carried by the arguments whose parameter positions reach a sink."""
    matched: set[str] = set()
    for index, arg in enumerate(node.args):
        if index in positions and not _value_is_masked(catalog, arg):
            matched |= _sink_categories(catalog, arg, allowed, env, summaries,
                                        param_returns, field_lists, attr_categories)
    for keyword in node.keywords:
        if keyword.arg in positions and not _value_is_masked(catalog, keyword.value):
            matched |= _sink_categories(catalog, keyword.value, allowed, env, summaries,
                                        param_returns, field_lists, attr_categories)
    return matched


def _module_constants(tree: ast.AST) -> dict[str, object]:
    constants: dict[str, object] = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    constants[target.id] = node.value.value
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) \
                and isinstance(node.value, ast.Constant):
            constants[node.target.id] = node.value.value
    return constants


def _class_constants(tree: ast.AST) -> dict[str, dict[str, object]]:
    result: dict[str, dict[str, object]] = {}
    for cls in (node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)):
        mutated: set[str] = set()
        for method in cls.body:
            if not isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for node in ast.walk(method):
                if isinstance(node, (ast.Assign, ast.AnnAssign)) and node.value is not None:
                    targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                    for target in targets:
                        attr = _self_attribute(target)
                        if attr:
                            mutated.add(attr)
        values: dict[str, object] = {}
        for stmt in cls.body:
            if isinstance(stmt, ast.Assign) and isinstance(stmt.value, ast.Constant):
                for target in stmt.targets:
                    if isinstance(target, ast.Name) and target.id not in mutated:
                        values[target.id] = stmt.value.value
            elif isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name) \
                    and isinstance(stmt.value, ast.Constant) and stmt.target.id not in mutated:
                values[stmt.target.id] = stmt.value.value
        if values:
            result[cls.name] = values
    return result


def _resolve_test(test: ast.AST, module_constants: dict[str, object],
                  self_constants: dict[str, object]) -> bool | None:
    if isinstance(test, ast.Constant) and isinstance(test.value, bool):
        return test.value
    if isinstance(test, ast.UnaryOp) and isinstance(test.op, ast.Not):
        inner = _resolve_test(test.operand, module_constants, self_constants)
        return None if inner is None else not inner
    if isinstance(test, ast.Name):
        value = module_constants.get(test.id)
        return value if isinstance(value, bool) else None
    if isinstance(test, ast.Attribute) and isinstance(test.value, ast.Name) \
            and test.value.id in {"self", "cls"}:
        value = self_constants.get(test.attr)
        return value if isinstance(value, bool) else None
    return None


class _TaintTracker(ast.NodeVisitor):
    """Propagate sensitive categories through simple assignments and SQL reads."""

    def __init__(self, catalog: Catalog, categories: set[str],
                 summaries: dict[str, set[str]] | None = None,
                 param_returns: dict[str, set[int | str]] | None = None,
                 attr_categories: dict[str, set[str]] | None = None,
                 module_constants: dict[str, object] | None = None,
                 self_constants: dict[str, object] | None = None):
        self.catalog = catalog
        self.categories = set(categories)
        self.summaries = summaries or {}
        self.param_returns = param_returns or {}
        self.attr_categories = attr_categories or {}
        self.module_constants = module_constants or {}
        self.self_constants = self_constants or {}
        self.env: dict[str, set[str]] = {}

    def scan(self, node: ast.AST) -> dict[str, set[str]]:
        self.visit(node)
        return self.env

    def visit_Assign(self, node: ast.Assign) -> None:
        categories = self._categories(node.value) | self._source_categories(node.targets, node.value)
        masked = _value_is_masked(self.catalog, node.value)
        if masked:
            categories = set()
        for target in node.targets:
            extra = set() if masked else self._target_key_categories(target)
            self._taint(target, categories | extra)
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        if node.value is not None:
            categories = self._categories(node.value) | self._source_categories([node.target], node.value)
            masked = _value_is_masked(self.catalog, node.value)
            if masked:
                categories = set()
            extra = set() if masked else self._target_key_categories(node.target)
            self._taint(node.target, categories | extra)
        self.generic_visit(node)

    def _target_key_categories(self, target: ast.AST) -> set[str]:
        """``body['api_key'] = value`` taints the container from the key itself."""
        if isinstance(target, ast.Subscript) and isinstance(target.slice, ast.Constant) \
                and isinstance(target.slice.value, str):
            category = _field_category(self.catalog, target.slice.value)
            if category in self.categories:
                return {category}
        return set()

    def visit_Call(self, node: ast.Call) -> None:
        """``rows.append(value)`` carries the value's categories into the container."""
        func = node.func
        if isinstance(func, ast.Attribute) and func.attr in {"append", "extend", "update"} \
                and isinstance(func.value, ast.Name):
            categories: set[str] = set()
            for arg in list(node.args) + [kw.value for kw in node.keywords]:
                categories |= self._categories(arg)
            if categories:
                self.env[func.value.id] = self.env.get(func.value.id, set()) | categories
        self.generic_visit(node)

    def visit_If(self, node: ast.If) -> None:
        """Only walk the branch taken by a constant test (``if DEBUG:``)."""
        value = _resolve_test(node.test, self.module_constants, self.self_constants)
        if value is True:
            for stmt in node.body:
                self.visit(stmt)
            return
        if value is False:
            for stmt in node.orelse:
                self.visit(stmt)
            return
        self.generic_visit(node)

    def _source_categories(self, targets: list[ast.AST], value: ast.AST) -> set[str]:
        """A variable that holds a credential stays tainted downstream.

        ``tokens.create(...)``, ``secrets.get_active(...)`` and ``load_secret(...)``
        are sources; a derived name (``token_ttl``) is not.
        """
        if "CREDENTIAL" not in self.categories:
            return set()
        names = [target.id for target in targets if isinstance(target, ast.Name)]
        for name in names:
            if name.startswith(DERIVED_IDENTIFIER_PREFIXES) or name.endswith(METADATA_FIELD_SUFFIXES):
                continue
            if _field_category(self.catalog, name) == "CREDENTIAL":
                return {"CREDENTIAL"}
        if names and _has_credential_call(self.catalog, value):
            return {"CREDENTIAL"}
        return set()

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
            if isinstance(child, ast.Call):
                leaf = _call_name(child).rsplit(".", 1)[-1]
                if (self.catalog.is_sanitizer(ast.unparse(child)) or _is_masking_name(leaf)
                        or leaf in {"sum", "len", "count", "bool", "any", "all"}):
                    for nested in ast.walk(child):
                        sanitized.add(id(nested))
        blocked_args: set[int] = set()
        for child in ast.walk(node):
            if not isinstance(child, ast.Call):
                continue
            leaf = _call_name(child).rsplit(".", 1)[-1]
            if leaf in PASSTHROUGH_CALLS or _is_masking_name(leaf):
                continue
            positions = self.param_returns.get(leaf, set())
            for index, arg in enumerate(child.args):
                if index in positions and not _value_is_masked(self.catalog, arg):
                    continue
                for nested in ast.walk(arg):
                    blocked_args.add(id(nested))
            for keyword in child.keywords:
                if keyword.arg in positions and not _value_is_masked(self.catalog, keyword.value):
                    continue
                for nested in ast.walk(keyword.value):
                    blocked_args.add(id(nested))
        dict_keys: set[int] = set()
        dict_blocked: set[int] = set()
        skip = _skip_nodes(node)
        projection = _projection_tokens(node)
        callees = {id(child.func) for child in ast.walk(node) if isinstance(child, ast.Call)}
        for child in ast.walk(node):
            if id(child) in sanitized or id(child) in blocked_args or id(child) in dict_blocked:
                continue
            if isinstance(child, ast.Dict):
                for key, value in zip(child.keys, child.values):
                    if _value_is_masked(self.catalog, value):
                        for nested in ast.walk(value):
                            dict_blocked.add(id(nested))
                        dict_blocked.add(id(key))
                        continue
                    if isinstance(key, ast.Constant) and isinstance(key.value, str):
                        dict_keys.add(id(key))
                        category = _field_category(self.catalog, key.value)
                        if category in self.categories and not self.catalog.is_sanitizer(ast.unparse(value)):
                            found.add(category)
            elif isinstance(child, ast.Name) and child.id in self.env and id(child) not in skip:
                if id(child) in callees or (
                        id(child) in projection
                        and not _projects_value(self.catalog, projection[id(child)])):
                    continue
                found |= self.env[child.id]
            elif isinstance(child, ast.Call):
                leaf = _call_name(child).rsplit(".", 1)[-1]
                found |= self.summaries.get(leaf, set())
                if leaf == "get" and child.args and isinstance(child.args[0], ast.Constant) \
                        and isinstance(child.args[0].value, str):
                    category = _field_category(self.catalog, child.args[0].value)
                    if category in self.categories:
                        found.add(category)
                positions = self.param_returns.get(leaf, set())
                for index, arg in enumerate(child.args):
                    if index in positions and not _value_is_masked(self.catalog, arg):
                        found |= self._categories(arg)
                for keyword in child.keywords:
                    if keyword.arg in positions and not _value_is_masked(self.catalog, keyword.value):
                        found |= self._categories(keyword.value)
            elif isinstance(child, ast.Constant) and isinstance(child.value, str) and id(child) not in dict_keys:
                for table in TABLE_RE.findall(child.value.lower()):
                    found |= set(self.catalog.tables.get(table, ()))
                for category in self.categories:
                    if _constant_matches(child.value, self.catalog.synonyms(category)):
                        found.add(category)
            elif isinstance(child, (ast.Attribute, ast.Subscript)):
                if id(child) in callees:
                    continue
                if isinstance(child, ast.Attribute) and self.attr_categories \
                        and isinstance(child.value, ast.Name) \
                        and child.value.id in {"self", "cls"}:
                    found |= self.attr_categories.get(child.attr, set())
                token = _identifier(child)
                if token:
                    category = _field_category(self.catalog, token)
                    if category:
                        found.add(category)
        return found & self.categories


def _function_summaries(tree: ast.AST, catalog: Catalog,
                        categories: set[str]) -> dict[str, set[str]]:
    """Return-value summaries for local helpers, computed to a fixpoint.

    Pattern matching sees the sink in the caller but the sensitive value is built
    inside the helper. A summary says which categories a function's return value
    can carry, following other local helpers and variables.
    """
    functions = {node.name: node for node in ast.walk(tree)
                 if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
    if not functions:
        return {}
    module_constants = _module_constants(tree)
    class_constants = _class_constants(tree)
    enclosing = _enclosing_classes(tree)
    field_lists = _field_lists(tree, catalog, categories)
    summaries: dict[str, set[str]] = {}
    for imported in _imported_names(tree):
        imported_categories = _name_categories(catalog, imported) & categories
        if imported_categories and not _is_masking_name(imported):
            summaries[imported] = imported_categories
    for _ in range(len(functions) + 1):
        changed = False
        for name, func in functions.items():
            found: set[str] = set()
            if not _is_masking_name(name):
                env = _TaintTracker(catalog, categories, summaries,
                                    module_constants=module_constants,
                                    self_constants=class_constants.get(
                                        enclosing.get(id(func), ""), {})).scan(func)
                for node in ast.walk(func):
                    if isinstance(node, ast.Return) and node.value is not None \
                            and not _value_is_masked(catalog, node.value):
                        if isinstance(node.value, ast.Call) and _call_name(node.value) in (
                                set(RESPONSE_PATTERNS) | set(REDIRECT_PATTERNS) | set(CSV_SINKS)):
                            continue
                        found |= _sink_categories(catalog, node.value, categories, env, summaries,
                                                  field_lists=field_lists)
            found &= categories
            merged = summaries.get(name, set()) | found
            if merged != summaries.get(name, set()):
                summaries[name] = merged
                changed = True
        if not changed:
            break
    return {name: values for name, values in summaries.items() if values}


def _call_effects(tree: ast.AST, catalog: Catalog, categories: set[str],
                  summaries: dict[str, set[str]]) -> tuple[dict[str, set[int | str]],
                                                           dict[str, set[int | str]],
                                                           dict[str, set[int | str]],
                                                           dict[str, set[int | str]]]:
    """Parameter positions that reach a return value, a log, a response or a redirect.

    ``_auth_header(key)`` returns its first parameter; a caller that passes a
    credential inherits it. ``_audit(org, key)`` logs its second parameter; a
    caller with a tainted key must be flagged without inlining the helper.
    """
    functions = {node.name: node for node in ast.walk(tree)
                 if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
    params = {name: [arg.arg for arg in list(func.args.args) + list(func.args.kwonlyargs)
                     if arg.arg not in {"self", "cls"}]
              for name, func in functions.items()}
    field_lists = _field_lists(tree, catalog, categories)
    module_constants = _module_constants(tree)
    class_constants = _class_constants(tree)
    enclosing = _enclosing_classes(tree)
    param_returns: dict[str, set[int | str]] = {name: set() for name in functions}
    for _ in range(len(functions) + 1):
        changed = False
        for name, func in functions.items():
            for index, param in enumerate(params[name]):
                others = {key: value for key, value in param_returns.items() if key != name}
                tracker = _TaintTracker(catalog, categories, summaries, others,
                                        module_constants=module_constants,
                                        self_constants=class_constants.get(
                                            enclosing.get(id(func), ""), {}))
                tracker.env[param] = set(categories)
                env = tracker.scan(func)
                hit = False
                for node in ast.walk(func):
                    if not isinstance(node, ast.Return) or node.value is None:
                        continue
                    if _value_is_masked(catalog, node.value):
                        continue
                    if _sink_categories(catalog, node.value, categories, env, summaries,
                                        param_returns, field_lists):
                        hit = True
                        break
                if hit:
                    param_returns[name].update({index, param})
                    changed = True
        if not changed:
            break
    param_logs: dict[str, set[int | str]] = {name: set() for name in functions}
    for name, func in functions.items():
        for index, param in enumerate(params[name]):
            others = {key: value for key, value in param_returns.items() if key != name}
            tracker = _TaintTracker(catalog, categories, summaries, others,
                                    module_constants=module_constants,
                                    self_constants=class_constants.get(
                                        enclosing.get(id(func), ""), {}))
            tracker.env[param] = set(categories)
            env = tracker.scan(func)
            for node in ast.walk(func):
                if not isinstance(node, ast.Call) or not _is_log_sink(_call_name(node)):
                    continue
                if _sink_categories(catalog, node, categories, env, summaries,
                                    param_returns, field_lists):
                    param_logs[name].update({index, param})
                    break
    param_responses: dict[str, set[int | str]] = {name: set() for name in functions}
    param_redirects: dict[str, set[int | str]] = {name: set() for name in functions}
    for name, func in functions.items():
        for index, param in enumerate(params[name]):
            others = {key: value for key, value in param_returns.items() if key != name}
            tracker = _TaintTracker(catalog, categories, summaries, others,
                                    module_constants=module_constants,
                                    self_constants=class_constants.get(
                                        enclosing.get(id(func), ""), {}))
            tracker.env[param] = set(categories)
            env = tracker.scan(func)
            for node in ast.walk(func):
                if isinstance(node, ast.Call) and _call_name(node) in REDIRECT_PATTERNS:
                    if _sink_categories(catalog, node, categories, env, summaries,
                                        param_returns, field_lists):
                        param_redirects[name].update({index, param})
                        break
                if isinstance(node, ast.Call) and _call_name(node) in RESPONSE_PATTERNS:
                    if _sink_categories(catalog, node, categories, env, summaries,
                                        param_returns, field_lists):
                        param_responses[name].update({index, param})
                        break
                if isinstance(node, ast.Return) and isinstance(
                        node.value, (ast.Dict, ast.List, ast.Tuple)):
                    if _sink_categories(catalog, node.value, categories, env, summaries,
                                        param_returns, field_lists):
                        param_responses[name].update({index, param})
                        break
    return param_returns, param_logs, param_responses, param_redirects


class PolicyFamily:
    def __init__(self, catalog: Catalog):
        self.catalog = catalog

    def evaluate(self, control: Control, task: TaskSpec, files: dict[str, str]) -> list[Finding]:
        raise NotImplementedError

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
            summaries = _function_summaries(tree, self.catalog, categories)
            field_lists = _field_lists(tree, self.catalog, categories)
            self._module_constants = _module_constants(tree)
            self._class_constants = _class_constants(tree)
            (param_returns, param_logs,
             param_responses, param_redirects) = _call_effects(tree, self.catalog, categories,
                                                               summaries)
            attr_map = _class_attr_categories(tree, self.catalog, categories, summaries,
                                              param_returns)
            if "log" in sinks:
                findings.extend(self._scan_logs(control, path, tree, categories, summaries,
                                                param_returns, param_logs, field_lists, attr_map))
            if "response" in sinks:
                findings.extend(self._scan_responses(control, path, tree, categories, summaries,
                                                     param_returns, field_lists, param_responses,
                                                     attr_map))
                findings.extend(self._scan_serializers(control, path, tree, categories))
                findings.extend(self._scan_graphql_types(control, path, tree, categories))
                if control.detection.context.get("route") == "admin":
                    findings.extend(self._scan_admin_classes(control, path, tree, categories))
            if "redirect" in sinks:
                findings.extend(self._scan_redirects(control, path, tree, categories, summaries,
                                                     param_returns, field_lists, param_redirects,
                                                     attr_map))
            if "csv" in sinks:
                findings.extend(self._scan_csv(control, path, tree, categories, summaries,
                                               param_returns, field_lists, attr_map))
        return self._dedupe(findings)

    def _scan_logs(self, control, path, tree, categories, summaries,
                   param_returns, param_logs, field_lists, attr_map) -> list[Finding]:
        out = []
        enclosing = _enclosing_classes(tree)
        for func in _leaf_functions(tree):
            class_name = enclosing.get(id(func), "")
            attrs = attr_map.get(class_name, {})
            env = _TaintTracker(self.catalog, categories, summaries, param_returns, attrs,
                                self._module_constants,
                                self._class_constants.get(class_name, {})).scan(func)
            for node in ast.walk(func):
                if not isinstance(node, ast.Call):
                    continue
                name = _call_name(node)
                if _is_log_sink(name):
                    text = ast.unparse(node)
                    if self.catalog.is_sanitizer(text):
                        continue
                    matched = self._categories(node, categories, env, summaries,
                                               param_returns, field_lists, attrs)
                    if matched:
                        out.append(_finding(control, path, node.lineno,
                                            f"Log call exposes {sorted(matched)} without masking.", text))
                    continue
                positions = param_logs.get(name.rsplit(".", 1)[-1])
                if not positions:
                    continue
                matched: set[str] = set()
                for index, arg in enumerate(node.args):
                    if index in positions and not _value_is_masked(self.catalog, arg):
                        matched |= self._categories(arg, categories, env, summaries,
                                                    param_returns, field_lists, attrs)
                for keyword in node.keywords:
                    if keyword.arg in positions and not _value_is_masked(self.catalog, keyword.value):
                        matched |= self._categories(keyword.value, categories, env, summaries,
                                                    param_returns, field_lists, attrs)
                if matched:
                    out.append(_finding(
                        control, path, node.lineno,
                        f"Log call inside '{_call_name(node)}' exposes {sorted(matched)} without masking.",
                        ast.unparse(node)))
        return out

    def _scan_responses(self, control, path, tree, categories, summaries,
                        param_returns, field_lists, param_responses, attr_map) -> list[Finding]:
        out = []
        admin_only = control.detection.context.get("route") == "admin"
        enclosing = _enclosing_classes(tree)
        for func in _leaf_functions(tree):
            class_name = enclosing.get(id(func), "")
            if (admin_only and "admin" not in func.name.lower()
                    and "admin" not in self._decorators(func).lower()
                    and "admin" not in class_name.lower()
                    and "admin" not in path.lower()):
                continue
            env = _TaintTracker(self.catalog, categories, summaries, param_returns,
                                attr_map.get(class_name, {}), self._module_constants,
                                self._class_constants.get(class_name, {})).scan(func)
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
                            _call_name(value) in RESPONSE_PATTERNS or _call_name(value) == "dict"
                            or _call_name(value).rsplit(".", 1)[-1] in summaries
                            or _call_name(value).rsplit(".", 1)[-1] in param_returns):
                        payload = value
                elif isinstance(node, ast.Call) and _call_name(node) in RESPONSE_PATTERNS:
                    payload = node
                if payload is None:
                    continue
                text = ast.unparse(payload)
                if self.catalog.is_sanitizer(text):
                    continue
                matched = self._categories(payload, categories, env, summaries,
                                           param_returns, field_lists,
                                           attr_map.get(class_name, {}))
                if matched:
                    out.append(_finding(control, path, payload.lineno,
                                        f"Response exposes {sorted(matched)} without masking.", text))
            for node in ast.walk(func):
                if not isinstance(node, ast.Call):
                    continue
                positions = param_responses.get(_call_name(node).rsplit(".", 1)[-1])
                if not positions:
                    continue
                matched = _effect_matched(self.catalog, node, positions, categories, env,
                                          summaries, param_returns, field_lists,
                                          attr_map.get(class_name, {}))
                if matched:
                    out.append(_finding(control, path, node.lineno,
                                        f"Response inside '{_call_name(node)}' exposes "
                                        f"{sorted(matched)} without masking.",
                                        ast.unparse(node)))
        return out

    def _field_category(self, field: str) -> str | None:
        return _field_category(self.catalog, field)

    def _masked_serializer_fields(self, cls: ast.ClassDef) -> set[str]:
        masked: set[str] = set()
        for method in cls.body:
            if not isinstance(method, ast.FunctionDef) or not method.name.startswith("get_"):
                continue
            field = method.name[4:]
            for node in ast.walk(method):
                if isinstance(node, ast.Return) and node.value is not None \
                        and self._value_is_masked(node.value):
                    masked.add(field)
        return masked

    def _scan_serializers(self, control, path, tree, categories) -> list[Finding]:
        out: list[Finding] = []
        admin_only = control.detection.context.get("route") == "admin"
        for cls, field in _serializer_scan(self.catalog, tree, categories, admin_only, path):
            out.append(_finding(control, path, cls.lineno,
                                f"Serializer '{cls.name}' exposes '{field}' without masking.",
                                field))
        return out

    def _scan_admin_classes(self, control, path, tree, categories) -> list[Finding]:
        out: list[Finding] = []
        for cls in (node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)):
            bases = " ".join(ast.unparse(base) for base in cls.bases)
            if "admin" not in cls.name.lower() and "admin.ModelAdmin" not in bases:
                continue
            for stmt in cls.body:
                if not isinstance(stmt, ast.Assign):
                    continue
                names = {target.id for target in stmt.targets if isinstance(target, ast.Name)}
                if not names & {"list_display", "search_fields", "list_filter"}:
                    continue
                if not isinstance(stmt.value, (ast.List, ast.Tuple)):
                    continue
                for element in stmt.value.elts:
                    if not isinstance(element, ast.Constant) or not isinstance(element.value, str):
                        continue
                    if self._field_category(element.value) in categories:
                        out.append(_finding(control, path, stmt.lineno,
                                            f"Admin class '{cls.name}' exposes '{element.value}' "
                                            "without masking.", element.value))
                        break
        return out

    def _scan_graphql_types(self, control, path, tree, categories) -> list[Finding]:
        out: list[Finding] = []
        admin_only = control.detection.context.get("route") == "admin"
        for cls in (node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)):
            decorators = " ".join(ast.unparse(decorator) for decorator in cls.decorator_list).lower()
            if "strawberry" not in decorators:
                continue
            if admin_only and "admin" not in cls.name.lower() and "admin" not in path.lower():
                continue
            for stmt in cls.body:
                if not isinstance(stmt, ast.AnnAssign) or not isinstance(stmt.target, ast.Name):
                    continue
                field = stmt.target.id
                if self._field_category(field) in categories:
                    out.append(_finding(control, path, stmt.lineno,
                                        f"GraphQL type '{cls.name}' exposes '{field}' without masking.",
                                        field))
                    break
        return out

    def _scan_redirects(self, control, path, tree, categories, summaries,
                        param_returns, field_lists, param_redirects, attr_map) -> list[Finding]:
        out = []
        enclosing = _enclosing_classes(tree)
        for func in _leaf_functions(tree):
            class_name = enclosing.get(id(func), "")
            attrs = attr_map.get(class_name, {})
            env = _TaintTracker(self.catalog, categories, summaries, param_returns, attrs,
                                self._module_constants,
                                self._class_constants.get(class_name, {})).scan(func)
            for node in ast.walk(func):
                if not isinstance(node, ast.Call) or _call_name(node) not in REDIRECT_PATTERNS:
                    continue
                text = ast.unparse(node)
                if self.catalog.is_sanitizer(text):
                    continue
                matched = self._categories(node, categories, env, summaries,
                                           param_returns, field_lists)
                if matched:
                    out.append(_finding(control, path, node.lineno,
                                        f"Redirect exposes {sorted(matched)}.", text))
            for node in ast.walk(func):
                if not isinstance(node, ast.Call):
                    continue
                positions = param_redirects.get(_call_name(node).rsplit(".", 1)[-1])
                if not positions:
                    continue
                matched = _effect_matched(self.catalog, node, positions, categories, env,
                                          summaries, param_returns, field_lists, attrs)
                if matched:
                    out.append(_finding(control, path, node.lineno,
                                        f"Redirect inside '{_call_name(node)}' exposes "
                                        f"{sorted(matched)}.", ast.unparse(node)))
        return out

    def _scan_csv(self, control, path, tree, categories, summaries,
                  param_returns, field_lists, attr_map) -> list[Finding]:
        out = []
        enclosing = _enclosing_classes(tree)
        for func in _leaf_functions(tree):
            class_name = enclosing.get(id(func), "")
            attrs = attr_map.get(class_name, {})
            env = _TaintTracker(self.catalog, categories, summaries, param_returns, attrs,
                                self._module_constants,
                                self._class_constants.get(class_name, {})).scan(func)
            for node in ast.walk(func):
                if not isinstance(node, ast.Call) or _call_name(node) not in CSV_SINKS:
                    continue
                text = ast.unparse(node)
                if self.catalog.is_sanitizer(text):
                    continue
                matched = self._categories(node, categories, env, summaries,
                                           param_returns, field_lists, attrs)
                if matched:
                    out.append(_finding(control, path, node.lineno,
                                        f"CSV row exposes {sorted(matched)} without masking.", text))
        return out

    def _value_is_masked(self, value: ast.AST) -> bool:
        return _value_is_masked(self.catalog, value)

    def _categories(self, node: ast.AST, allowed: set[str],
                    env: dict[str, set[str]] | None = None,
                    summaries: dict[str, set[str]] | None = None,
                    param_returns: dict[str, set[int | str]] | None = None,
                    field_lists: dict[str, set[str]] | None = None,
                    attr_categories: dict[str, set[str]] | None = None) -> set[str]:
        return _sink_categories(self.catalog, node, allowed, env, summaries,
                                param_returns, field_lists, attr_categories)

    @staticmethod
    def _decorators(func: ast.AST) -> str:
        return " ".join(ast.unparse(decorator) for decorator in getattr(func, "decorator_list", []))


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
        enclosing = _enclosing_classes(tree)
        functions = {node.name: node for node in ast.walk(tree)
                     if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
        function_tables = _function_query_tables(tree)
        model_params = _model_param_tables(tree)
        decorator_ids = {id(decorator)
                         for item in ast.walk(tree)
                         if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
                         for decorator in item.decorator_list}
        out: list[Finding] = []
        for func in _leaf_functions(tree):
            cutoff = _max_cutoff(func, constants)
            if cutoff is not None and cutoff >= retention_days:
                continue
            if cutoff is None and _retention_field_gate(func, retention_field, constants,
                                                        retention_days):
                continue
            if cutoff is None and _helper_retention_aware(func, functions, constants, retention_days):
                continue
            out.extend(self._deletes_in(control, path, func, tables, enclosing.get(id(func), ""),
                                        _name_tables(func, function_tables), function_tables,
                                        model_params, decorator_ids))
            if cutoff is None:
                out.extend(_short_cutoff_delete_calls(control, path, func, tables, constants,
                                                      retention_days))
        for stmt in tree.body:
            if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                continue
            cutoff = _max_cutoff(stmt, constants)
            if cutoff is not None and cutoff >= retention_days:
                continue
            if cutoff is None and _mentions_retention_field(stmt, retention_field):
                continue
            out.extend(self._deletes_in(control, path, stmt, tables, "",
                                        _name_tables(stmt, function_tables), function_tables,
                                        None, decorator_ids))
        return out

    @staticmethod
    def _deletes_in(control, path, node, tables, class_name="", name_tables=None,
                    function_tables=None, model_params=None, decorator_ids=frozenset()):
        out: list[Finding] = []
        for child in ast.walk(node):
            matched = _delete_tables(child, class_name) & tables
            if not matched and model_params:
                for candidate in _delete_tables(child, class_name):
                    matched |= model_params.get(candidate, set()) & tables
            if not matched:
                matched = _resolved_delete_tables(child, name_tables or {},
                                                  function_tables or {}) & tables
            if not matched and isinstance(child, ast.Call) \
                    and _call_name(child).endswith(".delete") and not child.args \
                    and id(child) not in decorator_ids:
                text = ast.unparse(child).lower() + " " + getattr(node, "name", "").lower() \
                    + " " + path.lower()
                matched = {table for table in tables if table.rstrip("s") in text}
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
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        args = list(node.args.args)
        defaults = list(node.args.defaults)
        for arg, default in zip(args[-len(defaults):] if defaults else [], defaults):
            if isinstance(default, ast.Constant) and isinstance(default.value, int):
                constants[arg.arg] = default.value
            elif isinstance(default, ast.Name) and default.id in constants:
                constants[arg.arg] = constants[default.id]
        for arg, default in zip(node.args.kwonlyargs, node.args.kw_defaults):
            if isinstance(default, ast.Constant) and isinstance(default.value, int):
                constants[arg.arg] = default.value
            elif isinstance(default, ast.Name) and default.id in constants:
                constants[arg.arg] = constants[default.id]
    call_values: dict[str, set[int]] = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        for keyword in node.keywords:
            if not keyword.arg:
                continue
            value = _int_value(keyword.value, constants)
            if value is not None:
                call_values.setdefault(keyword.arg, set()).add(value)
    for name, values in call_values.items():
        if len(values) == 1 and name not in constants:
            constants[name] = next(iter(values))
    method_returns: dict[str, set[int]] = {}
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for child in ast.walk(node):
            if isinstance(child, ast.Return) and isinstance(child.value, ast.Constant) \
                    and isinstance(child.value.value, int):
                method_returns.setdefault(node.name, set()).add(child.value.value)
    for name, values in method_returns.items():
        if name not in constants:
            constants[name] = min(values)
    return constants


def _int_value(node: ast.AST, constants: dict[str, int]) -> int | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, int):
        return node.value
    if isinstance(node, ast.Name):
        return constants.get(node.id)
    if isinstance(node, ast.Attribute):
        return constants.get(node.attr)
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and not node.args:
        return constants.get(node.func.attr)
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


def _retention_field_gate(node: ast.AST, field: str, constants: dict[str, int],
                          retention_days: int) -> bool:
    """Skip a delete that refers to a retention field only when its value is adequate."""
    if not field or field not in ast.unparse(node).lower():
        return False
    values = {name.lower(): value for name, value in constants.items() if isinstance(value, int)}
    value = values.get(field)
    if value is None:
        suffix_values = [candidate for name, candidate in values.items()
                         if name.endswith(field)]
        value = min(suffix_values) if suffix_values else None
    if value is None:
        return True
    return value >= retention_days


def _short_cutoff_delete_calls(control, path, func, tables, constants, retention_days):
    """``repo.delete_older_than(365)`` deletes a table without a visible statement."""
    out: list[Finding] = []
    for child in ast.walk(func):
        if not isinstance(child, ast.Call):
            continue
        leaf = _call_name(child).rsplit(".", 1)[-1].lower()
        if leaf == "delete" or not (leaf.startswith("delete") or leaf.startswith("purge")):
            continue
        values = [value for value in (_int_value(arg, constants) for arg in child.args)
                  if value is not None]
        if not values or max(values) >= retention_days:
            continue
        text = ast.unparse(child).lower() + " " + func.name.lower() + " " + path.lower()
        for table in tables:
            if table.rstrip("s") in text:
                out.append(_finding(control, path, child.lineno,
                                    f"{table} is deleted before its retention period ends.",
                                    ast.unparse(child)[:200]))
                break
    return out


def _mentions_retention_field(node: ast.AST, field: str) -> bool:
    if not field:
        return False
    return field in ast.unparse(node).lower()


def _helper_retention_aware(func: ast.AST, functions: dict[str, ast.AST],
                            constants: dict[str, int], retention_days: int) -> bool:
    """A delete is gated only if the helper-derived cutoff feeds the delete itself."""
    delete_exprs = _delete_expressions(func)
    if not delete_exprs:
        return False
    adequate = {name for name, helper in functions.items()
                if (_max_cutoff(helper, constants) or 0) >= retention_days}
    if not adequate:
        return False
    names: set[str] = set()
    for node in ast.walk(func):
        if not isinstance(node, (ast.Assign, ast.AnnAssign)) or node.value is None:
            continue
        if not any(isinstance(child, ast.Call)
                   and _call_name(child).rsplit(".", 1)[-1] in adequate
                   for child in ast.walk(node.value)):
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        names.update(target.id for target in targets if isinstance(target, ast.Name))
    for expr in delete_exprs:
        if any(re.search(rf"\b{re.escape(name)}\b", expr) for name in names):
            return True
        if any(re.search(rf"\b{re.escape(name)}\s*\(", expr) for name in adequate):
            return True
    if _deleted_rows_are_gated(func, adequate):
        return True
    return False


def _deleted_rows_are_gated(func: ast.AST, adequate: set[str]) -> bool:
    """``for row in rows: session.delete(row)`` is gated if ``rows`` came from a safe helper."""
    sources: dict[str, ast.AST] = {}
    for node in ast.walk(func):
        if isinstance(node, (ast.Assign, ast.AnnAssign)) and node.value is not None:
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for target in targets:
                if isinstance(target, ast.Name):
                    sources[target.id] = node.value
        elif isinstance(node, (ast.For, ast.AsyncFor)) and isinstance(node.target, ast.Name):
            sources[node.target.id] = node.iter
    deleted: set[str] = set()
    for node in ast.walk(func):
        if isinstance(node, ast.Call) and _call_name(node).rsplit(".", 1)[-1] == "delete":
            deleted.update(arg.id for arg in node.args if isinstance(arg, ast.Name))
    for name in deleted:
        expression = sources.get(name)
        seen: set[str] = set()
        while expression is not None and name not in seen:
            seen.add(name)
            if any(isinstance(child, ast.Call)
                   and _call_name(child).rsplit(".", 1)[-1] in adequate
                   for child in ast.walk(expression)):
                return True
            if not isinstance(expression, ast.Name):
                break
            name = expression.id
            expression = sources.get(name)
    return False


def _delete_expressions(func: ast.AST) -> list[str]:
    exprs: list[str] = []
    for node in ast.walk(func):
        if isinstance(node, ast.Call) and _call_name(node).rsplit(".", 1)[-1].lower() in {
                "delete", "execute", "filter", "where"}:
            exprs.append(ast.unparse(node))
    return exprs


def _model_param_tables(tree: ast.AST) -> dict[str, set[str]]:
    """Models passed to a helper whose own parameter is used in ``delete(param)``."""
    functions = {node.name: node for node in ast.walk(tree)
                 if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
    params = {name: [arg.arg for arg in list(func.args.args) + list(func.args.kwonlyargs)
                     if arg.arg not in {"self", "cls"}]
              for name, func in functions.items()}
    used: dict[str, set[str]] = {}
    for name, func in functions.items():
        for node in ast.walk(func):
            if not isinstance(node, ast.Call):
                continue
            call = _call_name(node)
            if not (call == "delete" or call.endswith(".delete") or call == "query"
                    or call.endswith(".query") or call == "select"):
                continue
            for arg in node.args:
                if isinstance(arg, ast.Name):
                    used.setdefault(name, set()).add(arg.id)
    resolved: dict[str, set[str]] = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        callee = _call_name(node).rsplit(".", 1)[-1]
        if callee not in functions:
            continue
        for index, arg in enumerate(node.args):
            if index >= len(params[callee]) or params[callee][index] not in used.get(callee, set()):
                continue
            token = _identifier(arg)
            if token:
                resolved.setdefault(params[callee][index], set()).update(_table_candidates(token))
    return resolved


def _table_candidates(name: str) -> set[str]:
    base = name.lower()
    return {base, base + "s", base.rstrip("s")}


def _direct_query_tables(node: ast.AST) -> set[str]:
    """Tables read or deleted by one statement: ``query(X)``, ``select(X)``, ``X.objects``."""
    tables: set[str] = set()
    if not isinstance(node, ast.Call):
        return tables
    name = _call_name(node)
    leaf = name.rsplit(".", 1)[-1]
    if (name == "query" or name.endswith(".query")) and node.args \
            and isinstance(node.args[0], (ast.Name, ast.Attribute)):
        token = _identifier(node.args[0])
        if token:
            tables |= _table_candidates(token)
    if leaf in {"select", "delete"} and node.args \
            and isinstance(node.args[0], (ast.Name, ast.Attribute)):
        token = _identifier(node.args[0])
        if token:
            tables |= _table_candidates(token)
    if ".objects" in name:
        match = DJANGO_OBJECTS_RE.search(ast.unparse(node))
        if match:
            tables |= _table_candidates(match.group(1))
    return tables


def _function_query_tables(tree: ast.AST) -> dict[str, set[str]]:
    """Tables each local function reads or deletes, following calls to other functions."""
    functions = {node.name: node for node in ast.walk(tree)
                 if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
    tables: dict[str, set[str]] = {}
    for _ in range(len(functions) + 1):
        changed = False
        for name, func in functions.items():
            found: set[str] = set()
            for node in ast.walk(func):
                found |= _direct_query_tables(node)
                if isinstance(node, ast.Call):
                    leaf = _call_name(node).rsplit(".", 1)[-1]
                    found |= tables.get(leaf, set())
            if found != tables.get(name, set()):
                tables[name] = found
                changed = True
        if not changed:
            break
    return tables


def _tables_of_expr(expr: ast.AST, function_tables: dict[str, set[str]],
                    env: dict[str, set[str]]) -> set[str]:
    found: set[str] = set()
    for child in ast.walk(expr):
        found |= _direct_query_tables(child)
        if isinstance(child, ast.Call):
            found |= function_tables.get(_call_name(child).rsplit(".", 1)[-1], set())
        if isinstance(child, ast.Name):
            found |= env.get(child.id, set())
    return found


def _name_tables(func: ast.AST, function_tables: dict[str, set[str]]) -> dict[str, set[str]]:
    """Names that hold a query result, so ``session.delete(row)`` resolves to a table."""
    env: dict[str, set[str]] = {}
    for _ in range(3):
        changed = False
        for node in ast.walk(func):
            if isinstance(node, (ast.Assign, ast.AnnAssign)) and node.value is not None:
                found = _tables_of_expr(node.value, function_tables, env)
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                for target in targets:
                    if isinstance(target, ast.Name) and found - env.get(target.id, set()):
                        env[target.id] = env.get(target.id, set()) | found
                        changed = True
            elif isinstance(node, (ast.For, ast.AsyncFor)) and isinstance(node.target, ast.Name):
                found = _tables_of_expr(node.iter, function_tables, env)
                if found - env.get(node.target.id, set()):
                    env[node.target.id] = env.get(node.target.id, set()) | found
                    changed = True
            elif isinstance(node, (ast.ListComp, ast.SetComp, ast.GeneratorExp, ast.DictComp)):
                for generator in node.generators:
                    if not isinstance(generator.target, ast.Name):
                        continue
                    found = _tables_of_expr(generator.iter, function_tables, env)
                    if found - env.get(generator.target.id, set()):
                        env[generator.target.id] = env.get(generator.target.id, set()) | found
                        changed = True
        if not changed:
            break
    return env


def _resolved_delete_tables(node: ast.AST, name_tables: dict[str, set[str]],
                            function_tables: dict[str, set[str]]) -> set[str]:
    """Instance deletes and deletes on a helper-built query."""
    if not isinstance(node, ast.Call):
        return set()
    if not _call_name(node).endswith(".delete"):
        return set()
    if node.args and isinstance(node.args[0], ast.Name):
        return name_tables.get(node.args[0].id, set())
    if isinstance(node.func, ast.Attribute):
        return _tables_of_expr(node.func.value, function_tables, name_tables)
    return set()



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


def _delete_tables(node: ast.AST, class_name: str = "") -> set[str]:
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
        if model:
            return _table_candidates(model)
        model = _django_model(node, class_name)
        return _table_candidates(model) if model else set()
    return set()


def _django_model(node: ast.AST, class_name: str = "") -> str | None:
    match = DJANGO_OBJECTS_RE.search(ast.unparse(node))
    if match:
        return match.group(1)
    if class_name.endswith("Manager"):
        return class_name[: -len("Manager")]
    return None


def _secret_header_bindings(tree: ast.AST) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign) or not isinstance(node.value, ast.Dict):
            continue
        for key in node.value.keys:
            if not isinstance(key, ast.Constant) or not isinstance(key.value, str):
                continue
            lowered = key.value.lower()
            if "api-key" in lowered or "api_key" in lowered or "authorization" in lowered:
                names.update(target.id for target in node.targets if isinstance(target, ast.Name))
    return names


class CredentialExposureFamily(PolicyFamily):
    """A credential (reset token, API key, session token) reaches a response, redirect or log."""

    def evaluate(self, control: Control, task: TaskSpec, files: dict[str, str]) -> list[Finding]:
        params = control.detection.params
        keys = tuple(params.get("keys", ()))
        value_pattern = params.get("value_pattern")
        sinks = set(control.detection.sinks)
        categories = set(control.data_categories)
        out: list[Finding] = []
        for path, content in files.items():
            if not path.endswith(".py"):
                continue
            try:
                tree = ast.parse(content)
            except SyntaxError:
                continue
            header_bindings = _secret_header_bindings(tree)
            summaries = _function_summaries(tree, self.catalog, categories)
            field_lists = _field_lists(tree, self.catalog, categories)
            self._module_constants = _module_constants(tree)
            self._class_constants = _class_constants(tree)
            (param_returns, param_logs,
             param_responses, param_redirects) = _call_effects(tree, self.catalog, categories,
                                                               summaries)
            attr_map = _class_attr_categories(tree, self.catalog, categories, summaries,
                                              param_returns)
            enclosing = _enclosing_classes(tree)
            env_by_node: dict[int, dict[str, set[str]]] = {}
            attrs_by_node: dict[int, dict[str, set[str]]] = {}
            endpoint_by_node: dict[int, bool] = {}
            for func in _leaf_functions(tree):
                class_name = enclosing.get(id(func), "")
                attrs = attr_map.get(class_name, {})
                env = _TaintTracker(self.catalog, categories, summaries, param_returns,
                                    attrs, self._module_constants,
                                    self._class_constants.get(class_name, {})).scan(func)
                endpoint = _is_endpoint(func)
                for child in ast.walk(func):
                    env_by_node[id(child)] = env
                    attrs_by_node[id(child)] = attrs
                    endpoint_by_node[id(child)] = endpoint
            for node in ast.walk(tree):
                is_sink = self._is_sink(node, sinks)
                endpoint = endpoint_by_node.get(id(node), False)
                return_call = (endpoint and isinstance(node, ast.Return)
                               and isinstance(node.value, ast.Call)
                               and (_call_name(node.value).rsplit(".", 1)[-1] in summaries
                                    or _call_name(node.value).rsplit(".", 1)[-1] in param_returns))
                return_name = (endpoint and isinstance(node, ast.Return)
                               and isinstance(node.value, ast.Name)
                               and bool(env_by_node.get(id(node), {}).get(node.value.id)))
                if not (is_sink or return_call or return_name):
                    continue
                target = node.value if (return_call or return_name) else node
                text = ast.unparse(target)
                if self.catalog.is_sanitizer(text):
                    continue
                tainted = _sink_categories(self.catalog, target, categories,
                                           env_by_node.get(id(node)), summaries,
                                           param_returns, field_lists,
                                           attrs_by_node.get(id(node)))
                if (tainted
                        or self._matches(text, keys, value_pattern)
                        or self._constant_key_match(target, keys)
                        or self._logs_token(node, sinks, keys)
                        or self._logs_secret_name(node, sinks, keys)
                        or self._returns_secret_attribute(node, sinks, keys)
                        or self._logs_secret_header(node, header_bindings, keys)):
                    out.append(_finding(control, path, getattr(node, "lineno", 1),
                                        "A credential reaches a response, redirect or log.", text))
            if "log" in sinks:
                for node in ast.walk(tree):
                    if not isinstance(node, ast.Call):
                        continue
                    positions = param_logs.get(_call_name(node).rsplit(".", 1)[-1])
                    if not positions or not isinstance(node, ast.Call):
                        continue
                    env = env_by_node.get(id(node))
                    attrs = attrs_by_node.get(id(node))
                    matched: set[str] = set()
                    for index, arg in enumerate(node.args):
                        if index in positions and not _value_is_masked(self.catalog, arg):
                            matched |= _sink_categories(self.catalog, arg, categories, env,
                                                        summaries, param_returns, field_lists, attrs)
                    for keyword in node.keywords:
                        if keyword.arg in positions and not _value_is_masked(self.catalog, keyword.value):
                            matched |= _sink_categories(self.catalog, keyword.value, categories, env,
                                                        summaries, param_returns, field_lists, attrs)
                    if matched:
                        out.append(_finding(control, path, node.lineno,
                                            "A credential reaches a log inside a helper.",
                                            ast.unparse(node)))
            for sink_name, positions_by_func, enabled, message in (
                    ("response", param_responses, "response" in sinks,
                     "A credential reaches a response inside a helper."),
                    ("redirect", param_redirects, "redirect" in sinks,
                     "A credential reaches a redirect inside a helper.")):
                if not enabled:
                    continue
                for node in ast.walk(tree):
                    if not isinstance(node, ast.Call):
                        continue
                    positions = positions_by_func.get(_call_name(node).rsplit(".", 1)[-1])
                    if not positions:
                        continue
                    matched = _effect_matched(self.catalog, node, positions, categories,
                                              env_by_node.get(id(node)), summaries,
                                              param_returns, field_lists,
                                              attrs_by_node.get(id(node)))
                    if matched:
                        out.append(_finding(control, path, node.lineno, message,
                                            ast.unparse(node)))
            if "response" in sinks:
                for cls, field in _serializer_scan(self.catalog, tree, categories, False, path):
                    out.append(_finding(control, path, cls.lineno,
                                        f"Serializer '{cls.name}' exposes '{field}'.",
                                        field))
        return self._dedupe(out)

    @staticmethod
    def _logs_token(node: ast.AST, sinks: set[str], keys: tuple[str, ...]) -> bool:
        if "log" not in sinks or not isinstance(node, ast.Call) \
                or not _is_log_sink(_call_name(node)):
            return False
        if not any(key in {"token", "reset_token"} for key in keys):
            return False
        for arg in list(node.args) + [kw.value for kw in node.keywords]:
            for child in ast.walk(arg):
                if isinstance(child, ast.Name) and "token" in child.id.lower():
                    return True
                if isinstance(child, ast.Attribute) and "token" in child.attr.lower():
                    return True
        return False

    @staticmethod
    def _logs_secret_name(node: ast.AST, sinks: set[str],
                          keys: tuple[str, ...]) -> bool:
        if "log" not in sinks or not isinstance(node, ast.Call) \
                or not _is_log_sink(_call_name(node)):
            return False
        if not any(key in {"api_key", "api-key", "secret"} for key in keys):
            return False
        for arg in list(node.args) + [kw.value for kw in node.keywords]:
            for child in ast.walk(arg):
                if isinstance(child, ast.Name) and any(
                        term in child.id.lower() for term in ("secret", "api_key")):
                    return True
                if isinstance(child, ast.Attribute) and any(
                        term in child.attr.lower() for term in ("secret", "api_key")):
                    return True
        return False

    @staticmethod
    def _logs_secret_header(node: ast.AST, bindings: set[str],
                            keys: tuple[str, ...]) -> bool:
        if not bindings or not isinstance(node, ast.Call) \
                or not _is_log_sink(_call_name(node)):
            return False
        if not any(key in {"api_key", "api-key", "secret"} for key in keys):
            return False
        arguments = " ".join(ast.unparse(arg) for arg in node.args)
        arguments += " " + " ".join(ast.unparse(kw.value) for kw in node.keywords)
        return any(re.search(rf"\b{re.escape(name)}\b", arguments) for name in bindings)

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
        if value_pattern and re.search(value_pattern, text, re.IGNORECASE):
            return True
        return False

    @staticmethod
    def _constant_key_match(node: ast.AST, keys: tuple[str, ...]) -> bool:
        """``f'/sent?token={...}'``: the key label is inside a literal string."""
        for child in ast.walk(node):
            if not isinstance(child, ast.Constant) or not isinstance(child.value, str):
                continue
            for key in keys:
                if re.search(rf"\b{re.escape(key)}\b\s*=", child.value, re.IGNORECASE):
                    return True
        return False
