"""AST detector for personal-data exposure in HTTP API responses (Ley 21.719 Art. 14 quinquies, CWE-200).

Flags, in Python route handlers (FastAPI/Flask style decorators):
  * a returned dict literal that carries a sensitive key with an unmasked value;
  * a ``response_model`` class defined in the same file that declares a credential field.
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
MASKERS = ("mask", "redact", "hash", "anon", "seudon", "encrypt")


def _route_decorator(func: ast.FunctionDef | ast.AsyncFunctionDef) -> ast.Call | None:
    for dec in func.decorator_list:
        if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute) and dec.func.attr in ROUTE_METHODS:
            return dec
    return None


def _is_masked(value: ast.AST) -> bool:
    if isinstance(value, ast.Call):
        name = ast.unparse(value.func).lower()
        return any(m in name for m in MASKERS)
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
            for kw in dec.keywords:
                if kw.arg == "response_model":
                    out.extend(self._check_model(path, kw.value, classes))
            for node in ast.walk(func):
                if isinstance(node, ast.Return) and isinstance(node.value, ast.Dict):
                    out.extend(self._check_dict(path, node.value))
        return out

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

    def _check_dict(self, path: str, node: ast.Dict) -> list[Finding]:
        found = []
        for key, value in zip(node.keys, node.values):
            if not (isinstance(key, ast.Constant) and isinstance(key.value, str)):
                continue
            k = key.value.lower()
            if (k in CREDENTIAL_FIELDS or k in PERSONAL_KEYS) and not _is_masked(value):
                found.append(self._finding(
                    path, key.lineno, "HIGH",
                    f"Returned dict exposes '{key.value}' without masking.",
                    f"{key.value}: {ast.unparse(value)}",
                    "Mask, hash or drop the field before returning it."))
        return found

    def _finding(self, path: str, line: int, severity: str, message: str, evidence: str, advice: str) -> Finding:
        return Finding(policy_id=self.policy_id, severity=severity, status="VIOLATION", file=path,
                       line=line, message=message, evidence=evidence, remediation_advice=advice)
