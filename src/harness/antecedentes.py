"""Accountability module — evidence the harness can produce for the data protection agency.

M1 implements the static data map: for every personal or sensitive field the scan finds in
the scanned code, it records where the datum lives (file, entity, line, persisted or not),
which catalog controls apply to its category and which law articles support them, plus the
sinks that can receive data. The map is rendered as a report and persisted to the harness
SQLite database (``evidence_fields`` / ``evidence_sinks``).

Usage:
    python -m src.harness.antecedentes map --root . --scan src/backend src/database \\
        experiments/supermercado/app

Later milestones add ``register`` (RoPA), ``subject`` (per-subject package), ``incident``.
"""
from __future__ import annotations

import argparse
import ast
import json
import sqlite3
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from src.harness.catalog import load_catalog
from src.harness.contracts import TaskSpec
from src.harness.data_lineage import ASTLineageScanner
from src.harness.db import DEFAULT_DB_PATH, get_db_connection
from src.harness.dimension_policy import (
    BLOCKED_FIELDS,
    CONSENT_FIELDS,
    CONSENT_RECORD_FIELDS,
    IGNORED_HOSTS,
    PersonalDataDimensionsPolicy,
    SQL_TABLE_RE,
    URL_RE,
    _sql_fields,
    extract_fields,
)
from src.harness.normative_pack import load_legacy_view

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
LEGACY_PACK = WORKSPACE_ROOT / ".harness" / "packs" / "cl-ley-21719.json"
CATALOG_PACK = WORKSPACE_ROOT / ".harness" / "packs" / "catalog.full.json"

DEFAULT_SCAN_DIRS = ("src/backend", "src/database", "experiments/supermercado/app")
PY_EXTENSIONS = (".py",)
TEMPLATE_EXTENSIONS = (".html", ".htm", ".jinja", ".jinja2", ".mjml", ".hbs", ".eta", ".ejs")
_REGISTER_SPEC = TaskSpec(task_id="REGISTER", goal="register", allowed_paths=["*"], forbidden_paths=[])


@dataclass
class EvidenceField:
    category: str
    field_name: str
    entity: str
    file_path: str
    line: int
    persisted: bool = False
    controls: list[str] = field(default_factory=list)
    articles: list[str] = field(default_factory=list)


@dataclass
class EvidenceSink:
    kind: str
    call: str
    file_path: str
    line: int


@dataclass
class DataMap:
    scan_root: str
    fields: list[EvidenceField] = field(default_factory=list)
    sinks: list[EvidenceSink] = field(default_factory=list)


def _category_controls() -> dict[str, set[str]]:
    catalog = load_catalog(CATALOG_PACK)
    mapping: dict[str, set[str]] = defaultdict(set)
    for control in catalog.controls:
        if not control.implemented:
            continue
        for category in control.data_categories:
            mapping[category].add(control.id)
    return mapping


def _match_category(name: str, categories: dict) -> str | None:
    lowered = name.lower()
    for cat_key, cat_data in categories.items():
        vocab = [f.lower() for f in cat_data.get("fields", [])]
        if any(term == lowered or (len(term) > 3 and term in lowered) for term in vocab):
            return cat_key
    if lowered in {"birth_date", "birthdate", "dob", "date_of_birth", "age"}:
        return "CHILDREN_DATA"
    return None


def _sql_evidence(rel: str, content: str, categories: dict) -> list[EvidenceField]:
    fields: list[EvidenceField] = []
    table_match = SQL_TABLE_RE.search(content)
    entity = table_match.group(1) if table_match else "schema"
    for name, line, _persisted in _sql_fields(content):
        category = _match_category(name, categories)
        if category is None:
            continue
        fields.append(EvidenceField(category=category, field_name=name, entity=entity,
                                    file_path=rel, line=line, persisted=True))
    return fields


def _scan_python_file(path: Path, rel: str, categories: dict) -> tuple[list, list]:
    content = path.read_text(encoding="utf-8", errors="replace")
    scanner = ASTLineageScanner(path, rel, categories)
    scanner.visit(ast.parse(content))
    return scanner.sources, scanner.sinks


def _evidence_for_file(rel: str, content: str, control_map: dict, label_map: dict,
                       categories: dict) -> tuple[list[EvidenceField], list[EvidenceSink]]:
    if rel.endswith(".sql"):
        fields: list[EvidenceField] = []
        for field in _sql_evidence(rel, content, categories):
            applicable = control_map.get(field.category, set()) | control_map.get("PERSONAL_DATA", set())
            field.controls = sorted(applicable)
            field.articles = sorted({cite for cid in applicable
                                     for cite in label_map[cid].framework_labels()})
            fields.append(field)
        return fields, []
    persisted = {name for name, _, is_persisted in extract_fields(rel, content) if is_persisted}
    scanner = ASTLineageScanner(Path(rel), rel, categories)
    try:
        scanner.visit(ast.parse(content))
    except SyntaxError:
        return [], []
    fields: list[EvidenceField] = []
    sinks: list[EvidenceSink] = []
    for source in scanner.sources:
        field = EvidenceField(
            category=source["category"],
            field_name=source["field_name"],
            entity=source["class_name"],
            file_path=source["file_path"],
            line=source["line"],
            persisted=source["field_name"] in persisted,
        )
        applicable = control_map.get(source["category"], set()) | control_map.get("PERSONAL_DATA", set())
        field.controls = sorted(applicable)
        field.articles = sorted({cite for cid in applicable
                                 for cite in label_map[cid].framework_labels()})
        fields.append(field)
    for sink in scanner.sinks:
        kind = "log" if "log" in sink["name"].lower() else "audit" if "audit" in sink["name"].lower() else "print"
        sinks.append(EvidenceSink(kind, sink["name"].split(" -> ")[-1], sink["file_path"], sink["line"]))
    return fields, sinks


def refresh_files(db_path: Path | str, scan_root: str, files: dict[str, str]) -> None:
    """Upsert the map entries for the given files (content in memory), removing stale rows."""
    categories = load_legacy_view(LEGACY_PACK)["data_categories"]
    control_map = _category_controls()
    label_map = {c.id: c for c in load_catalog(CATALOG_PACK).controls}
    conn = get_db_connection(db_path)
    try:
        conn.executescript((WORKSPACE_ROOT / ".harness" / "schema.sql").read_text(encoding="utf-8"))
        for rel, content in files.items():
            rel = rel.replace("\\", "/")
            conn.execute("DELETE FROM evidence_fields WHERE scan_root = ? AND file_path = ?",
                         (scan_root, rel))
            conn.execute("DELETE FROM evidence_sinks WHERE scan_root = ? AND file_path = ?",
                         (scan_root, rel))
            fields, sinks = _evidence_for_file(rel, content, control_map, label_map, categories)
            for item in fields:
                conn.execute(
                    """
                    INSERT INTO evidence_fields
                    (category, field_name, entity, file_path, line, persisted, controls_json, articles_json, scan_root)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (item.category, item.field_name, item.entity, item.file_path, item.line,
                     1 if item.persisted else 0, json.dumps(item.controls),
                     json.dumps(item.articles), scan_root),
                )
            for sink in sinks:
                conn.execute(
                    """
                    INSERT INTO evidence_sinks (sink_kind, call, file_path, line, scan_root)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (sink.kind, sink.call, sink.file_path, sink.line, scan_root),
                )
        conn.commit()
    finally:
        conn.close()


def scan_map(root: Path, scan_dirs: list[str]) -> DataMap:
    root = Path(root)
    categories = load_legacy_view(LEGACY_PACK)["data_categories"]
    control_map = _category_controls()
    catalog = load_catalog(CATALOG_PACK)
    label_map = {c.id: c for c in catalog.controls}

    result = DataMap(scan_root=str(root))
    persisted_by_file: dict[str, set[str]] = {}
    root_schema = root / "schema.sql"
    if root_schema.is_file():
        content = root_schema.read_text(encoding="utf-8", errors="replace")
        for field in _sql_evidence("schema.sql", content, categories):
            applicable = control_map.get(field.category, set()) | control_map.get("PERSONAL_DATA", set())
            field.controls = sorted(applicable)
            field.articles = sorted({cite for cid in applicable
                                     for cite in label_map[cid].framework_labels()})
            result.fields.append(field)
    for scan_dir in scan_dirs:
        base = root / scan_dir
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*")):
            if path.suffix not in PY_EXTENSIONS and path.suffix != ".sql":
                continue
            rel = path.relative_to(root).as_posix()
            content = path.read_text(encoding="utf-8", errors="replace")
            if path.suffix == ".sql":
                for field in _sql_evidence(rel, content, categories):
                    applicable = control_map.get(field.category, set()) | control_map.get("PERSONAL_DATA", set())
                    field.controls = sorted(applicable)
                    field.articles = sorted({cite for cid in applicable
                                             for cite in label_map[cid].framework_labels()})
                    result.fields.append(field)
                continue
            persisted_by_file[rel] = {
                name for name, _, persisted in extract_fields(rel, content)
                if persisted
            }
            sources, sinks = _scan_python_file(path, rel, categories)
            for source in sources:
                field = EvidenceField(
                    category=source["category"],
                    field_name=source["field_name"],
                    entity=source["class_name"],
                    file_path=source["file_path"],
                    line=source["line"],
                    persisted=source["field_name"] in persisted_by_file[rel],
                )
                applicable = control_map.get(source["category"], set()) | control_map.get("PERSONAL_DATA", set())
                field.controls = sorted(applicable)
                field.articles = sorted({cite for cid in applicable
                                         for cite in label_map[cid].framework_labels()})
                result.fields.append(field)
            for sink in sinks:
                kind = "log" if "log" in sink["name"].lower() else "audit" if "audit" in sink["name"].lower() else "print"
                result.sinks.append(EvidenceSink(kind, sink["name"].split(" -> ")[-1], sink["file_path"], sink["line"]))
    return result


def build_map(root: Path, scan_dirs: list[str], db_path: Path | str = DEFAULT_DB_PATH) -> DataMap:
    data_map = scan_map(root, scan_dirs)
    _persist(db_path, data_map)
    return data_map


def _persist(db_path: Path | str, data_map: DataMap) -> None:
    conn = get_db_connection(db_path)
    try:
        conn.executescript(
            (WORKSPACE_ROOT / ".harness" / "schema.sql").read_text(encoding="utf-8")
        )
        conn.execute("DELETE FROM evidence_fields WHERE scan_root = ?", (data_map.scan_root,))
        conn.execute("DELETE FROM evidence_sinks WHERE scan_root = ?", (data_map.scan_root,))
        for field in data_map.fields:
            conn.execute(
                """
                INSERT INTO evidence_fields
                (category, field_name, entity, file_path, line, persisted, controls_json, articles_json, scan_root)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (field.category, field.field_name, field.entity, field.file_path, field.line,
                 1 if field.persisted else 0, json.dumps(field.controls), json.dumps(field.articles),
                 data_map.scan_root),
            )
        for sink in data_map.sinks:
            conn.execute(
                """
                INSERT INTO evidence_sinks (sink_kind, call, file_path, line, scan_root)
                VALUES (?, ?, ?, ?, ?)
                """,
                (sink.kind, sink.call, sink.file_path, sink.line, data_map.scan_root),
            )
        conn.commit()
    finally:
        conn.close()


@dataclass
class ProcessingActivity:
    activity: str
    data_fields: list[dict] = field(default_factory=list)
    file_path: str = ""
    persisted: bool = False
    retention: str = "no declarada"
    recipients: list[str] = field(default_factory=list)
    consent: str = "no declarado"
    gaps: list[str] = field(default_factory=list)


@dataclass
class Register:
    scan_root: str
    activities: list[ProcessingActivity] = field(default_factory=list)
    recipients: list[str] = field(default_factory=list)


def _gaps_for(findings: list, file_path: str) -> dict[str, list[str]]:
    gaps: dict[str, list[str]] = {}
    for finding in findings:
        if finding.file != file_path:
            continue
        if finding.policy_id == "privacy.retention_minimization":
            gaps.setdefault("retención", []).append(finding.message)
        elif finding.policy_id == "privacy.consent_transparency":
            gaps.setdefault("consentimiento", []).append(finding.message)
        elif finding.policy_id == "privacy.rights_reachability":
            gaps.setdefault("derechos del titular", []).append(finding.message)
        elif finding.policy_id == "privacy.third_party_transfers":
            gaps.setdefault("destinatarios", []).append(finding.message)
        elif finding.policy_id == "privacy.minors_and_sensitive":
            gaps.setdefault("datos sensibles/menores", []).append(finding.message)
    return gaps


def build_register(root: Path, scan_dirs: list[str], db_path: Path | str = DEFAULT_DB_PATH) -> Register:
    register = scan_register(root, scan_dirs)
    _persist_register(db_path, register)
    return register


def scan_register(root: Path, scan_dirs: list[str]) -> Register:
    data_map = scan_map(root, scan_dirs)
    files: dict[str, str] = {}
    for scan_dir in scan_dirs:
        base = Path(root) / scan_dir
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*")):
            if path.suffix in PY_EXTENSIONS or path.suffix in TEMPLATE_EXTENSIONS or path.suffix == ".sql":
                files[path.relative_to(root).as_posix()] = path.read_text(encoding="utf-8", errors="replace")
    root_schema = Path(root) / "schema.sql"
    if root_schema.is_file():
        files["schema.sql"] = root_schema.read_text(encoding="utf-8", errors="replace")
    findings = PersonalDataDimensionsPolicy(complete=True).evaluate(_REGISTER_SPEC, files)

    by_entity: dict[tuple[str, str], ProcessingActivity] = {}
    for field in data_map.fields:
        key = (field.file_path, field.entity)
        activity = by_entity.setdefault(
            key, ProcessingActivity(activity=field.entity, file_path=field.file_path))
        activity.data_fields.append({"field": field.field_name, "category": field.category})
        activity.persisted = activity.persisted or field.persisted

    for (file_path, entity), activity in by_entity.items():
        gaps = _gaps_for(findings, file_path)
        activity.gaps = ["finalidad no declarada en el código (documental)",
                         "base legal no declarada en el código (documental)"]
        if not activity.persisted:
            activity.retention = "no aplica (no persistido)"
        elif "retención" in gaps:
            activity.retention = "no declarada"
            activity.gaps.append("retención no declarada o sin rutina de purga")
        else:
            activity.retention = "declarada"
        activity.recipients = sorted({match for f in findings if f.file == file_path
                                      and f.policy_id == "privacy.third_party_transfers"
                                      for match in (f.evidence or "").replace("Hosts referenced: ", "").split(", ")})
        if "consentimiento" in gaps:
            activity.consent = "incompleto"
        all_names = {name for name, _, _ in extract_fields(file_path, files.get(file_path, ""))}
        consent_names = all_names & CONSENT_FIELDS
        has_record = any(any(record in name for record in CONSENT_RECORD_FIELDS) for name in all_names)
        if consent_names:
            activity.consent = "registrado" if has_record else "incompleto"
        if any(f["field"] in {"birth_date", "birthdate", "dob", "date_of_birth", "age"}
               for f in activity.data_fields):
            all_text = "\n".join(files.values()).lower()
            if not any(marker in all_text for marker in ("age_gate", "is_minor", "guardian", "parental", "tutor")):
                activity.gaps.append("age gate no declarado para datos de edad/menores")
        activity.gaps.extend(sorted(set(sum(gaps.values(), []))))

    recipients = sorted({host.lower() for content in files.values()
                         for host in URL_RE.findall(content)} - IGNORED_HOSTS)
    return Register(scan_root=str(root), recipients=recipients, activities=sorted(
        by_entity.values(), key=lambda a: (a.file_path, a.activity)))


def _persist_register(db_path: Path | str, register: Register) -> None:
    conn = get_db_connection(db_path)
    try:
        conn.executescript((WORKSPACE_ROOT / ".harness" / "schema.sql").read_text(encoding="utf-8"))
        conn.execute("DELETE FROM processing_activities WHERE scan_root = ?", (register.scan_root,))
        for activity in register.activities:
            conn.execute(
                """
                INSERT INTO processing_activities
                (activity, data_fields_json, file_path, retention, recipients_json, consent, gaps_json, scan_root)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (activity.activity, json.dumps(activity.data_fields), activity.file_path,
                 activity.retention, json.dumps(activity.recipients), activity.consent,
                 json.dumps(activity.gaps), register.scan_root),
            )
        conn.commit()
    finally:
        conn.close()


def render_register(register: Register) -> str:
    lines = [f"# Processing register (RoPA draft) — {register.scan_root}", ""]
    lines.append(f"**{len(register.activities)} processing activities** derived from the code. "
                 "Purpose and legal basis cannot be read from code: they are declared as pending gaps "
                 "to be completed with documentary evidence.")
    lines.append("")
    if not register.activities:
        lines.append("No processing activities found: no personal data detected in the scanned directories.")
    lines.append("| Activity | Data | Retention | Recipients | Consent | Pending gaps |")
    lines.append("| --- | --- | --- | --- | --- | --- |")
    for activity in register.activities:
        data = ", ".join(f"`{f['field']}` ({f['category']})" for f in activity.data_fields)
        recipients = ", ".join(activity.recipients) or "—"
        gaps = "<br>".join(activity.gaps) or "—"
        lines.append(f"| {activity.activity} | {data} | {activity.retention} | "
                     f"{recipients} | {activity.consent} | {gaps} |")
        lines.append("")
    if register.recipients:
        lines.append("**Third-party recipients referenced by the scanned code "
                     "(static, may over-approximate):** " + ", ".join(register.recipients))
        lines.append("")
    lines.append("Static code-derived draft: not a legal register, not legal advice.")
    return "\n".join(lines)


@dataclass
class SubjectPackage:
    category: str = ""
    field_name: str = ""
    locations: list[EvidenceField] = field(default_factory=list)
    sinks: list[EvidenceSink] = field(default_factory=list)
    audit_entries: list[dict] = field(default_factory=list)
    audit_tables: list[dict] = field(default_factory=list)
    consent_fields: list[dict] = field(default_factory=list)
    entities: list[ProcessingActivity] = field(default_factory=list)
    recipients: list[str] = field(default_factory=list)


def _consent_fields(files: dict[str, str]) -> list[dict]:
    out: list[dict] = []
    for rel, content in files.items():
        for name, line, _persisted in extract_fields(rel, content):
            if name in CONSENT_FIELDS | CONSENT_RECORD_FIELDS | BLOCKED_FIELDS:
                out.append({"field": name, "file": rel, "line": line})
    return out


def _audit_tables(root: Path, scan_dirs: list[str]) -> list[dict]:
    out: list[dict] = []
    for scan_dir in scan_dirs:
        base = root / scan_dir
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*.sql")):
            for idx, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
                if "audit" in line.lower():
                    out.append({"file": path.relative_to(root).as_posix(), "line": idx, "text": line.strip()})
    return out


def build_subject(root: Path, scan_dirs: list[str], category: str | None = None,
                  field: str | None = None) -> SubjectPackage:
    data_map = scan_map(root, scan_dirs)
    register = scan_register(root, scan_dirs)
    files: dict[str, str] = {}
    for scan_dir in scan_dirs:
        base = Path(root) / scan_dir
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*")):
            if path.suffix in PY_EXTENSIONS or path.suffix == ".sql":
                files[path.relative_to(root).as_posix()] = path.read_text(encoding="utf-8", errors="replace")
    root_schema = Path(root) / "schema.sql"
    if root_schema.is_file():
        files["schema.sql"] = root_schema.read_text(encoding="utf-8", errors="replace")

    locations = [
        f for f in data_map.fields
        if (category and f.category == category) or (field and f.field_name.lower() == field.lower())
    ]
    field_names = {f.field_name.lower() for f in locations}
    referencing_files = {
        rel for rel, content in files.items()
        if any(name in content.lower() for name in field_names)
    }
    related_sinks = [s for s in data_map.sinks if s.file_path in referencing_files]
    audit_entries = [
        {"file": s.file_path, "line": s.line, "call": s.call}
        for s in data_map.sinks if s.kind == "audit" and s.file_path in referencing_files
    ]
    subject_entities = [a for a in register.activities
                        if any(entry["field"] in {f.field_name for f in locations} for entry in a.data_fields)]
    recipients = list(register.recipients)
    return SubjectPackage(
        category=category or "", field_name=field or "",
        locations=locations, sinks=related_sinks,
        audit_entries=audit_entries, audit_tables=_audit_tables(root, scan_dirs),
        consent_fields=_consent_fields(files), entities=subject_entities, recipients=recipients,
    )


def render_subject(package: SubjectPackage) -> str:
    label = package.category or f"field `{package.field_name}`"
    lines = [f"# Subject evidence — {label}", ""]
    lines.append("Static package: code-derived locations and flows; access log entries are "
                 "pointed to their tables, not queried live. Not legal advice.")
    lines.append("")
    if not package.locations:
        lines.append("No personal-data fields match this subject in the scanned directories.")
        return "\n".join(lines)
    lines.append("## 1. Where the datum lives")
    lines.append("")
    lines.append("| Field | Entity | Location | Persisted | Controls |")
    lines.append("| --- | --- | --- | :-: | --- |")
    for f in sorted(package.locations, key=lambda x: (x.file_path, x.line or 0)):
        lines.append(f"| `{f.field_name}` | {f.entity} | {f.file_path}:{f.line} | "
                     f"{'yes' if f.persisted else 'no'} | {', '.join(f'`{c}`' for c in f.controls)} |")
    lines.append("")
    if package.sinks:
        lines.append("## 2. Flows (sinks in files that reference the subject fields)")
        lines.append("")
        for s in sorted(package.sinks, key=lambda x: (x.file_path, x.line or 0)):
            lines.append(f"- `{s.call}` — {s.file_path}:{s.line} ({s.kind})")
        lines.append("")
    if package.audit_entries or package.audit_tables:
        lines.append("## 3. Access trail")
        lines.append("")
        for entry in package.audit_entries:
            lines.append(f"- audit call `{entry['call']}` — {entry['file']}:{entry['line']}")
        for table in package.audit_tables:
            lines.append(f"- audit table reference — {table['file']}:{table['line']}: `{table['text']}`")
        lines.append("")
    if package.consent_fields:
        lines.append("## 4. Consent and rights records")
        lines.append("")
        for c in package.consent_fields:
            lines.append(f"- `{c['field']}` — {c['file']}:{c['line']}")
        lines.append("")
    if package.entities:
        lines.append("## 5. Processing state")
        lines.append("")
    if package.recipients:
        lines.append("## 6. Third-party recipients")
        lines.append("")
        lines.extend(f"- `{recipient}`" for recipient in package.recipients)
        lines.append("")
        lines.append("| Entity | Retention | Consent | Recipients |")
        lines.append("| --- | --- | --- | --- |")
        for entity in package.entities:
            lines.append(f"| {entity.activity} | {entity.retention} | {entity.consent} | "
                         f"{', '.join(entity.recipients) or '—'} |")
        lines.append("")
    return "\n".join(lines)


def add_incident(db_path: Path | str, description: str, scope: list[str] | None = None,
                 severity: str = "MEDIUM") -> int:
    conn = get_db_connection(db_path)
    try:
        conn.executescript((WORKSPACE_ROOT / ".harness" / "schema.sql").read_text(encoding="utf-8"))
        cursor = conn.execute(
            "INSERT INTO incident_records (description, scope_json, severity) VALUES (?, ?, ?)",
            (description, json.dumps(scope or []), severity),
        )
        conn.commit()
        return int(cursor.lastrowid)
    finally:
        conn.close()


def list_incidents(db_path: Path | str) -> list[dict]:
    conn = get_db_connection(db_path)
    try:
        conn.executescript((WORKSPACE_ROOT / ".harness" / "schema.sql").read_text(encoding="utf-8"))
        rows = conn.execute(
            "SELECT * FROM incident_records ORDER BY id DESC").fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def mark_notified(db_path: Path | str, incident_id: int) -> None:
    conn = get_db_connection(db_path)
    try:
        conn.execute(
            "UPDATE incident_records SET status = 'NOTIFIED', notified_at = CURRENT_TIMESTAMP, "
            "updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (incident_id,),
        )
        conn.commit()
    finally:
        conn.close()


def render_incidents(rows: list[dict]) -> str:
    lines = ["# Incident register", ""]
    if not rows:
        lines.append("No incidents recorded.")
        return "\n".join(lines)
    lines.append("| ID | Date | Description | Scope | Severity | Status | Notified |")
    lines.append("| --- | --- | --- | --- | --- | --- | --- |")
    for row in rows:
        scope = ", ".join(json.loads(row.get("scope_json") or "[]")) or "—"
        lines.append(f"| {row['id']} | {row['created_at']} | {row['description']} | "
                     f"{scope} | {row['severity']} | {row['status']} | {row.get('notified_at') or '—'} |")
    return "\n".join(lines)


def render_map(data_map: DataMap) -> str:
    lines = [f"# Data map — {data_map.scan_root}", ""]
    lines.append(f"**{len(data_map.fields)} personal-data fields** across "
                 f"{len({f.file_path for f in data_map.fields})} files · "
                 f"**{len(data_map.sinks)} sinks**.")
    lines.append("")
    if not data_map.fields:
        lines.append("No personal-data fields found in the scanned directories.")
    by_category: dict[str, list[EvidenceField]] = defaultdict(list)
    for field in data_map.fields:
        by_category[field.category].append(field)
    for category in sorted(by_category):
        lines.append(f"## {category}")
        lines.append("")
        lines.append("| Field | Entity | Location | Persisted | Controls | Articles |")
        lines.append("| --- | --- | --- | :-: | --- | --- |")
        for field in sorted(by_category[category], key=lambda f: (f.file_path, f.line or 0)):
            articles = "; ".join(field.articles) or "—"
            controls = ", ".join(f"`{c}`" for c in field.controls) or "—"
            persisted = "yes" if field.persisted else "no"
            lines.append(f"| `{field.field_name}` | {field.entity} | "
                         f"{field.file_path}:{field.line} | {persisted} | {controls} | {articles} |")
        lines.append("")
    if data_map.sinks:
        lines.append("## Sinks")
        lines.append("")
        lines.append("| Kind | Call | Location |")
        lines.append("| --- | --- | --- |")
        for sink in sorted(data_map.sinks, key=lambda s: (s.file_path, s.line or 0)):
            lines.append(f"| {sink.kind} | `{sink.call}` | {sink.file_path}:{sink.line} |")
        lines.append("")
    lines.append("Static code-derived map: flows are co-occurrence, not runtime tracing. "
                 "Not legal advice.")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m src.harness.antecedentes", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    map_parser = sub.add_parser("map", help="static data map of the scanned code")
    map_parser.add_argument("--root", type=Path, default=Path("."))
    map_parser.add_argument("--scan", nargs="*", default=list(DEFAULT_SCAN_DIRS))
    map_parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH)

    register_parser = sub.add_parser("register", help="RoPA-style processing register draft")
    register_parser.add_argument("--root", type=Path, default=Path("."))
    register_parser.add_argument("--scan", nargs="*", default=list(DEFAULT_SCAN_DIRS))
    register_parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH)

    subject_parser = sub.add_parser("subject", help="per-subject/per-category evidence package")
    subject_parser.add_argument("--root", type=Path, default=Path("."))
    subject_parser.add_argument("--scan", nargs="*", default=list(DEFAULT_SCAN_DIRS))
    subject_parser.add_argument("--category", default=None, help="catalog category key (e.g. IDENTIFIER_RUT)")
    subject_parser.add_argument("--field", default=None, help="field name (e.g. rut)")

    incident_parser = sub.add_parser("incident", help="breach/incident register")
    incident_parser.add_argument("--add", default=None, help="register an incident with this description")
    incident_parser.add_argument("--scope", default="", help="comma-separated affected categories")
    incident_parser.add_argument("--severity", default="MEDIUM")
    incident_parser.add_argument("--list", action="store_true", help="list the incident register")
    incident_parser.add_argument("--notify", type=int, default=None, help="mark an incident as notified")
    incident_parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH)

    args = parser.parse_args(argv)
    if args.command == "map":
        data_map = build_map(args.root, args.scan, args.db)
        print(render_map(data_map))
        print(f"\npersisted: {args.db}")
        return 0
    if args.command == "register":
        register = build_register(args.root, args.scan, args.db)
        print(render_register(register))
        print(f"\npersisted: {args.db}")
        return 0
    if args.command == "subject":
        if not args.category and not args.field:
            print("subject requires --category or --field", file=sys.stderr)
            return 2
        package = build_subject(args.root, args.scan, args.category, args.field)
        print(render_subject(package))
        return 0
    if args.command == "incident":
        if args.add:
            scope = [s.strip() for s in args.scope.split(",") if s.strip()]
            incident_id = add_incident(args.db, args.add, scope, args.severity)
            print(f"incident {incident_id} registered")
        if args.notify is not None:
            mark_notified(args.db, args.notify)
            print(f"incident {args.notify} marked as NOTIFIED")
        if args.list or not args.add and args.notify is None:
            print(render_incidents(list_incidents(args.db)))
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
