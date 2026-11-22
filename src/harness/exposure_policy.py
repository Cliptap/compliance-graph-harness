"""AST detector for personal-data exposure in HTTP API responses (Ley 21.719 Art. 14 quinquies, CWE-200).

Flags, in Python route handlers (FastAPI/Flask style decorators):
  * a returned dict literal that carries a sensitive key with an unmasked value;
  * a list (or list comprehension) of dict literals with sensitive keys;
  * a ``JSONResponse``/``Response``/``jsonify`` payload that carries those keys;
  * a ``response_model`` class defined in the same file that declares a credential field;
  * an admin route that serialises raw rows (``dict(row)``, ``rows``) so masking cannot be seen.

Contact fields (email, phone, address) are only treated as sensitive in admin routes: a customer
reading their own profile may see them, an admin listing every customer must not.
"""
from __future__ import annotations

import ast

from src.harness.contracts import Finding, TaskSpec
from src.harness.policy_engine import BasePolicy

ROUTE_METHODS = {"get", "post", "put", "patch", "delete", "route", "api_route"}
CREDENTIAL_FIELDS = {"password", "hashed_password", "password_hash", "secret", "api_key", "private_key"}
PERSONAL_KEYS = {
    "rut", "run", "national_id", "dni", "diagnosis", "diagnostico", "clinical_notes",
    "medical_record", "treatment", "health_status",
}
CONTACT_KEYS = {
    "email", "correo", "e-mail", "phone", "telefono", "teléfono", "address", "direccion", "dirección",
}
MASKERS = ("mask", "redact", "hash", "anon", "seudon", "pseudon", "finger", "tokeniz",
           "enmascar", "encrypt")
RESPONSE_WRAPPERS = {"JSONResponse", "Response", "jsonify"}
RAW_COLLECTIONS = {"rows", "records", "results", "items", "customers", "accounts", "clientes", "cuentas"}


def _route_decorator(func: ast.FunctionDef | ast.AsyncFunctionDef) -> ast.Call | None:
    for dec in func.decorator_list:
        if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute) and dec.func.attr in ROUTE_METHODS:
            return dec
    return None


def _route_path(dec: ast.Call) -> str:
    for arg in dec.args:
        if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
            return arg.value
    return ""


def _is_admin(func: ast.FunctionDef | ast.AsyncFunctionDef, dec: ast.Call) -> bool:
    return "admin" in _route_path(dec).lower() or "admin" in func.name.lower()


def _call_name(node: ast.AST) -> str:
    if not isinstance(node, ast.Call):
        return ""
    func = node.func
    return func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", "")


def _is_masked(value: ast.AST) -> bool:
    if isinstance(value, ast.Call):
        name = ast.unparse(value.func).lower()
        return any(m in name for m in MASKERS)
    if isinstance(value, ast.JoinedStr):
        return any(isinstance(part, ast.Constant) and isinstance(part.value, str) and "*" in part.value
                   for part in value.values)
    return False


class ApiPersonalDataExposurePolicy(BasePolicy):
    def __init__(self) -> None:
        super().__init__(
            policy_id="privacy.api_exposure",
            description="API responses must not expose credentials or unmasked personal/health identifiers.",
            severity="HIGH",
        )

    def evaluate(self, task_spec: TaskSpec, modified_files: dict[str, str], diff: str | None = None) -> list[Finding]:
        findings: list[Finding] = []
        for path, content in modified_files.items():
            if not path.endswith(".py"):
                continue
            try:
                tree = ast.parse(content)
            except SyntaxError:
                continue
            findings.extend(self._scan(path.replace("\\", "/"), tree))
        return findings

    def _scan(self, path: str, tree: ast.Module) -> list[Finding]:
        classes = {n.name: n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)}
        out: list[Finding] = []
        for func in ast.walk(tree):
            if not isinstance(func, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            dec = _route_decorator(func)
            if dec is None:
                continue
            admin = _is_admin(func, dec)
            for kw in dec.keywords:
                if kw.arg == "response_model":
                    out.extend(self._check_model(path, kw.value, classes))
            for node in ast.walk(func):
                if isinstance(node, ast.Return):
                    out.extend(self._check_payload(path, node.value, admin))
        return out

    def _check_payload(self, path: str, expr: ast.AST | None, admin: bool) -> list[Finding]:
        if expr is None:
            return []
        if isinstance(expr, ast.Dict):
            return self._check_dict(path, expr, admin)
        if isinstance(expr, (ast.List, ast.Tuple, ast.Set)):
            found: list[Finding] = []
            for element in expr.elts:
                found.extend(self._check_payload(path, element, admin))
            return found
        if isinstance(expr, (ast.ListComp, ast.GeneratorExp, ast.SetComp)):
            return self._check_payload(path, expr.elt, admin)
        if isinstance(expr, ast.Call):
            name = _call_name(expr)
            if name in RESPONSE_WRAPPERS:
                for arg in expr.args:
                    found = self._check_payload(path, arg, admin)
                    if found:
                        return found
                for kw in expr.keywords:
                    if kw.arg in ("content", "body", "data"):
                        return self._check_payload(path, kw.value, admin)
                return []
            if admin and name in {"dict", "list"}:
                return [self._warning(
                    path, expr.lineno,
                    "Admin route serialises raw rows; masking cannot be verified from the code.",
                    ast.unparse(expr),
                    "Select and mask the fields explicitly instead of dumping the row.")]
            return []
        if admin and isinstance(expr, ast.Name) and expr.id.lower() in RAW_COLLECTIONS:
            return [self._warning(
                path, expr.lineno,
                f"Admin route returns the raw collection '{expr.id}'; masking cannot be verified.",
                ast.unparse(expr),
                "Project only the fields the admin list needs and mask RUT, email and phone.")]
        return []

    def _check_model(self, path: str, expr: ast.AST, classes: dict[str, ast.ClassDef]) -> list[Finding]:
        names = {n.id for n in ast.walk(expr) if isinstance(n, ast.Name)}
        found = []
        for name in names & classes.keys():
            for stmt in classes[name].body:
                if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name) \
                        and stmt.target.id.lower() in CREDENTIAL_FIELDS:
                    found.append(self._finding(
                        path, stmt.lineno, "HIGH",
                        f"Response model '{name}' exposes credential field '{stmt.target.id}'.",
                        ast.unparse(stmt), "Remove the field from the response schema."))
        return found

    def _check_dict(self, path: str, node: ast.Dict, admin: bool) -> list[Finding]:
        found = []
        for key, value in zip(node.keys, node.values):
            if not (isinstance(key, ast.Constant) and isinstance(key.value, str)):
                continue
            k = key.value.lower()
            sensitive = k in CREDENTIAL_FIELDS or k in PERSONAL_KEYS or (admin and k in CONTACT_KEYS)
            if sensitive and not _is_masked(value):
                found.append(self._finding(
                    path, key.lineno, "HIGH",
                    f"Returned payload exposes '{key.value}' without masking.",
                    f"{key.value}: {ast.unparse(value)}",
                    "Mask, hash or drop the field before returning it."))
        return found

    def _finding(self, path: str, line: int, severity: str, message: str, evidence: str, advice: str) -> Finding:
        return Finding(policy_id=self.policy_id, severity=severity, status="VIOLATION", file=path,
                       line=line, message=message, evidence=evidence, remediation_advice=advice)

    def _warning(self, path: str, line: int, message: str, evidence: str, advice: str) -> Finding:
        return Finding(policy_id=self.policy_id, severity="MEDIUM", status="WARNING", file=path,
                       line=line, message=message, evidence=evidence, remediation_advice=advice)
