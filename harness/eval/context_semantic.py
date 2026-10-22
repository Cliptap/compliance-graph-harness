"""Semantic context-retrieval benchmark: natural-language task -> files an agent should read.

Compares retrievers on the same scratch copy of the app (src/backend + src/database, as in
the pilot workspaces): CodeGraph (`context --format json`), graphify (`query`) and a
keyword-grep baseline. Gold sets are hand-labelled from grep + judgement and are part of the
benchmark; they are small, so results are indicative, not statistical.
Metrics are per task and per strategy; there is no composite score. Tools that are not
installed are reported as unavailable (None), never as zero.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

APP_PATHS = ("src/backend", "src/database")


@dataclass(frozen=True)
class Task:
    id: str
    query: str
    keywords: tuple[str, ...]
    gold: frozenset[str]


TASKS = (
    Task("impact_get_current_user", "who calls get_current_user and would be affected if its signature changes",
         ("get_current_user",),
         frozenset({"src/backend/security/dependencies.py", "src/backend/api/appointments.py",
                    "src/backend/api/audit.py", "src/backend/api/auth.py", "src/backend/api/patients.py",
                    "src/backend/api/practitioners.py", "src/backend/api/secure_example.py",
                    "src/database/events.py"})),
    Task("jwt_expiry", "change the JWT access token expiry time",
         ("expires_delta", "ACCESS_TOKEN_EXPIRE"),
         frozenset({"src/backend/api/auth.py", "src/backend/security/auth.py"})),
    Task("password_hashing", "where are passwords hashed and verified",
         ("verify_password", "get_password_hash"),
         frozenset({"src/backend/api/auth.py", "src/backend/security/auth.py",
                    "src/backend/services/user_service.py"})),
    Task("audit_logging", "how audit log entries are written and queried",
         ("AuditLog", "query_logs"),
         frozenset({"src/backend/api/audit.py", "src/backend/services/audit_service.py",
                    "src/database/models.py", "src/database/events.py"})),
    Task("soft_delete", "replace hard deletes of patients with soft delete",
         ("SoftDeleteMixin", "deleted_at"),
         frozenset({"src/database/models.py", "src/database/repository.py", "src/database/events.py",
                    "src/backend/api/patients.py"})),
    Task("appointment_response_field", "add a field to the appointment model and return it in the API response",
         ("AppointmentResponse", "class Appointment"),
         frozenset({"src/database/models.py", "src/backend/schemas.py", "src/backend/api/appointments.py"})),
)

_SRC = re.compile(r"src=([^\s\]]+)")


def make_workspace(repo_root: Path) -> Path:
    ws = Path(tempfile.mkdtemp(prefix="ctxsem_"))
    for rel in APP_PATHS:
        shutil.copytree(repo_root / rel, ws / rel, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.db"))
    subprocess.run(["git", "init", "-q"], cwd=ws, check=True)
    return ws


def codegraph_bin() -> str | None:
    explicit = os.environ.get("CODEGRAPH_BIN")
    if explicit and Path(explicit).exists():
        return explicit
    return shutil.which("codegraph")


def codegraph_retriever(ws: Path):
    binary = codegraph_bin()
    if not binary:
        return None
    env = {**os.environ, "CODEGRAPH_TELEMETRY": "0"}
    subprocess.run([binary, "init", str(ws)], check=True, capture_output=True, env=env)

    def retrieve(task: Task) -> set[str]:
        out = subprocess.run([binary, "context", task.query, "-p", str(ws), "--format", "json"],
                             check=True, capture_output=True, text=True, env=env).stdout
        return set(json.loads(out).get("relatedFiles", []))

    return retrieve


def graphify_retriever(ws: Path):
    binary = shutil.which("graphify")
    if not binary:
        return None
    subprocess.run([binary, "extract", str(ws), "--code-only"], cwd=ws, check=True, capture_output=True)

    def retrieve(task: Task) -> set[str]:
        out = subprocess.run([binary, "query", task.query, "--graph", "graphify-out/graph.json"],
                             cwd=ws, check=True, capture_output=True, text=True).stdout
        return {m.replace("\\", "/") for m in _SRC.findall(out) if m}

    return retrieve


def grep_retriever(ws: Path):
    def retrieve(task: Task) -> set[str]:
        hits = set()
        for path in ws.rglob("*.py"):
            text = path.read_text(encoding="utf-8", errors="replace")
            if any(k in text for k in task.keywords):
                hits.add(path.relative_to(ws).as_posix())
        return hits

    return retrieve


def score(task: Task, got: set[str], ws: Path) -> dict:
    hit = len(task.gold & got)
    tokens = sum(len((ws / f).read_text(encoding="utf-8", errors="replace")) for f in got if (ws / f).is_file()) // 4
    return {
        "task": task.id, "returned": len(got), "recall": hit / len(task.gold),
        "precision": hit / len(got) if got else None, "approx_tokens_if_read": tokens,
    }


def run(repo_root: Path, retrievers: dict | None = None) -> dict[str, list[dict] | None]:
    ws = make_workspace(repo_root)
    try:
        built = retrievers or {"codegraph": codegraph_retriever(ws), "graphify": graphify_retriever(ws),
                               "grep": grep_retriever(ws)}
        return {name: None if r is None else [score(t, r(t), ws) for t in TASKS] for name, r in built.items()}
    finally:
        shutil.rmtree(ws, ignore_errors=True)


def summarize(rows: list[dict] | None) -> dict | None:
    if rows is None:
        return None
    precisions = [r["precision"] for r in rows if r["precision"] is not None]
    return {
        "mean_recall": sum(r["recall"] for r in rows) / len(rows),
        "mean_precision": sum(precisions) / len(precisions) if precisions else None,
        "mean_returned": sum(r["returned"] for r in rows) / len(rows),
        "mean_tokens_if_read": sum(r["approx_tokens_if_read"] for r in rows) / len(rows),
    }


if __name__ == "__main__":
    results = run(Path(__file__).resolve().parents[2])
    for name, rows in results.items():
        print(name, summarize(rows))
        for r in rows or []:
            print("   ", r)
