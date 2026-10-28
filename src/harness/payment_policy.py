"""AST detector for payment card data persisted in ORM models (Ley 21.719 Arts. 14 bis and 14 quinquies).

Flags, in Python files, a persisted model (a class with ``__tablename__`` or SQLAlchemy ``Column`` /
``mapped_column`` fields) that stores:
  * a card security code (CVV/CVC), which is flagged even when encrypted;
  * a primary account number (PAN) that is not wrapped in an encrypted column type.

Request schemas (e.g. pydantic models) are not storage and are ignored. PCI DSS is a contractual
standard, not law: the legal basis is the risk-based security duty, so the finding says "risk".
Known miss: card data placed in a free-form JSON column.
"""
from __future__ import annotations

import ast

from src.harness.contracts import Finding, TaskSpec
from src.harness.policy_engine import BasePolicy

SECURITY_CODE_FIELDS = {"cvv", "cvv2", "cvc", "cvc2", "card_cvv", "security_code"}
PAN_FIELDS = {"card_number", "card_pan", "pan", "credit_card_number", "card_no"}
COLUMN_CALLS = {"Column", "mapped_column"}


def _call_name(node: ast.AST) -> str:
    if isinstance(node, ast.Call):
        func = node.func
        return func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", "")
    return ""


def _field_target(stmt: ast.stmt) -> tuple[str, ast.AST | None] | None:
    if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
        return stmt.target.id, stmt.value
    if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 and isinstance(stmt.targets[0], ast.Name):
        return stmt.targets[0].id, stmt.value
    return None


def _is_persisted(cls: ast.ClassDef) -> bool:
    for stmt in cls.body:
        target = _field_target(stmt)
        if target and (target[0] == "__tablename__" or _call_name(target[1]) in COLUMN_CALLS):
            return True
    return False


class PaymentDataStoragePolicy(BasePolicy):
    def __init__(self) -> None:
        super().__init__(
            policy_id="privacy.payment_data_storage",
            description="Persisted models must not store card security codes or unencrypted card numbers.",
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
            for cls in (n for n in ast.walk(tree) if isinstance(n, ast.ClassDef) and _is_persisted(n)):
                for stmt in cls.body:
                    target = _field_target(stmt)
                    if target:
                        findings.extend(self._check(path.replace("\\", "/"), cls.name, stmt, *target))
        return findings

    def _check(self, path: str, cls: str, stmt: ast.stmt, name: str, value: ast.AST | None) -> list[Finding]:
        field = name.lower()
        encrypted = value is not None and "encrypt" in ast.unparse(value).lower()
        if field in SECURITY_CODE_FIELDS:
            reason = "stores a card security code, which must not be persisted"
        elif field in PAN_FIELDS and not encrypted:
            reason = "stores a card number without an encrypted column type"
        else:
            return []
        return [Finding(
            policy_id=self.policy_id, severity="HIGH", status="VIOLATION", file=path, line=stmt.lineno,
            message=f"Model '{cls}' field '{name}' {reason} (security risk, Ley 21.719 Arts. 14 bis and 14 quinquies).",
            evidence=ast.unparse(stmt),
            remediation_advice="Store only the gateway token and the last four digits; never persist the security code.",
        )]
