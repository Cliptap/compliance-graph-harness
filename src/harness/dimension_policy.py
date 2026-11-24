"""Deterministic detectors for the Ley 21.719 dimensions where code gives evidence (T16-T20).

Layer A reads language-neutral artifacts (route declarations, SQL/Prisma models, templates,
configuration); layer B adds Python AST structure; layer C stays in the compliance skills and
never produces a ``confirmed_violation``.

The detectors are conservative. They return ``WARNING`` (potential risk, not counted by the
compliance score) unless the code contradicts an explicit safeguard that can be read from the
artifact, in which case they return ``VIOLATION``. Missing artifacts are reported per change
set, so a single-file change cannot claim a repo-wide gap on its own.
"""
from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field
from pathlib import PurePosixPath

from src.harness.contracts import Finding, TaskSpec
from src.harness.policy_engine import BasePolicy

POLICY_IDS = (
    "privacy.rights_reachability",
    "privacy.consent_transparency",
    "privacy.minors_and_sensitive",
    "privacy.retention_minimization",
    "privacy.third_party_transfers",
)

PERSONAL_FIELDS = {
    "rut", "run", "national_id", "dni", "email", "phone", "address", "full_name", "first_name",
    "last_name", "birth_date", "birthdate", "dob", "date_of_birth", "age", "gender", "identifier",
}
SENSITIVE_FIELDS = {
    "health", "health_status", "diagnosis", "diagnostico", "clinical_notes", "medical_record",
    "treatment", "religion", "religious_belief", "political_opinion", "union_membership",
    "sexual_orientation", "ethnic_origin", "socioeconomic_status", "socioeconomic_level",
    "genetic_data",
}
BIOMETRIC_FIELDS = {
    "fingerprint", "face_encoding", "face_id", "iris_scan", "biometric_template", "voiceprint",
    "retina", "facial_template",
}
GEOLOCATION_FIELDS = {"latitude", "longitude", "geolocation", "gps", "location", "coordinates"}
AGE_FIELDS = {"birth_date", "birthdate", "dob", "date_of_birth", "age"}
CONSENT_FIELDS = {
    "consent", "consent_granted", "marketing_consent", "subscribe", "subscribed", "newsletter",
    "opt_in", "marketing_opt_in",
}
RETENTION_FIELDS = {
    "retention", "retention_days", "retention_period", "ttl", "expires_at", "delete_after",
    "purge_at",
}
MASKERS = ("mask", "redact", "hash", "anon", "seudon", "encrypt", "tokeniz", "template_id")

RIGHT_ROUTES = {
    "access": ("access", "me", "my-data", "my_data", "personal-data", "profile", "datos", "account"),
    "rectification": ("rectif", "update", "edit", "modify", "modificar"),
    "erasure": ("delete", "erase", "cancel", "remove", "forget", "borrar", "eliminar"),
    "opposition": ("oppos", "opt-out", "optout", "oposicion"),
    "portability": ("export", "portab", "download", "descargar"),
    "block": ("block", "suspend", "freeze", "bloque"),
}
ROUTE_METHODS = {"get", "post", "put", "patch", "delete", "route", "api_route", "all"}
NEST_METHODS = {"Get", "Post", "Put", "Patch", "Delete"}
JS_ROUTE_RE = re.compile(
    r"(?:app|router|server|fastify|api)\s*\.\s*(get|post|put|patch|delete|route|all)\s*\(\s*[\"'`]([^\"'`]+)"
)
PRETICKED_RE = re.compile(
    r"(consent|subscribe|newsletter|marketing|opt[_-]?in)\w*\s*[:=][^\n]*?\bdefault\s*=\s*"
    r"(True|true|\"true\"|'true'|1)\b",
    re.IGNORECASE,
)
HTML_PRETICKED_RE = re.compile(
    r"<input[^>]*(consent|subscribe|accept|marketing)[^>]*\bchecked\b", re.IGNORECASE
)
MARKETING_WORDS = ("promo", "oferta", "descuento", "newsletter", "marketing", "cupon", "cupón")
MARKETING_PATH_HINTS = ("marketing", "newsletter", "promo", "campaign", "email", "mail")
UNSUBSCRIBE_WORDS = ("unsubscribe", "opt-out", "optout", "baja", "cancelar suscrip", "darse de baja")
TEMPLATE_EXTS = (".html", ".htm", ".jinja", ".jinja2", ".mjml", ".hbs", ".eta", ".ejs")
URL_RE = re.compile(r"https?://([a-zA-Z0-9.-]+)")
IGNORED_HOSTS = {
    "localhost", "127.0.0.1", "example.com", "www.example.com", "www.w3.org", "w3.org",
    "schema.org", "json-schema.org", "bcn.cl", "www.bcn.cl", "github.com", "www.github.com",
    "pypi.org", "npmjs.com", "www.npmjs.com",
}
SQL_TABLE_RE = re.compile(r"create\s+table\s+(?:if\s+not\s+exists\s+)?[\"`\[]?(\w+)", re.IGNORECASE)
SQL_SKIP = {
    "primary", "foreign", "constraint", "unique", "index", "key", "check", "create", "alter",
    "references", "on", "using", "comment",
}
PRISMA_MODEL_RE = re.compile(r"^\s*model\s+(\w+)\s*\{", re.IGNORECASE)
PRISMA_SKIP = {"id", "createdat", "updatedat", "created_at", "updated_at"}
CONSENT_RECORD_FIELDS = {"purpose", "version", "granted_at", "consented_at", "withdrawn_at", "revoked_at"}
BLOCKED_FIELDS = {"blocked", "blocked_at", "is_blocked", "blocked_reason", "suspended_at"}
REQUEST_FIELDS = {"requested_at", "request_date", "submitted_at", "created_at"}
RETENTION_ROUTINES = ("purge", "anonymiz", "anonimiz", "expire", "retention", "cleanup", "delete_expired")


@dataclass
class FieldInfo:
    name: str
    path: str
    line: int
    persisted: bool


@dataclass
class RouteInfo:
    path: str
    method: str
    file: str
    line: int


@dataclass
class ChangeSet:
    files: dict[str, str] = field(default_factory=dict)
    fields: list[FieldInfo] = field(default_factory=list)
    routes: list[RouteInfo] = field(default_factory=list)
    # ``True`` when ``files`` is the whole project tree. Absence checks (a route
    # that does not exist) can only be stated as a violation on a complete set.
    complete: bool = False

    def field_names(self) -> set[str]:
        return {f.name for f in self.fields}

    def has_personal_data(self) -> bool:
        return any(f.name in PERSONAL_FIELDS or f.name in SENSITIVE_FIELDS for f in self.fields)

    def contains(self, *needles: str) -> bool:
        lowered = {p: c.lower() for p, c in self.files.items()}
        return any(n in content for content in lowered.values() for n in needles)

    def files_with(self, *needles: str) -> list[str]:
        return [p for p, c in self.files.items() if any(n in c.lower() for n in needles)]


def _python_fields(content: str) -> tuple[list[tuple[str, int, bool]], bool]:
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return [], False
    found: list[tuple[str, int, bool]] = []
    for cls in (n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)):
        persisted = False
        for stmt in cls.body:
            target = None
            value = None
            if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                target, value = stmt.target.id, stmt.value
            elif (isinstance(stmt, ast.Assign) and len(stmt.targets) == 1
                  and isinstance(stmt.targets[0], ast.Name)):
                target, value = stmt.targets[0].id, stmt.value
            if target is None:
                continue
            rendered = ast.unparse(value).lower() if value is not None else ""
            if target == "__tablename__" or any(m in rendered for m in ("column(", "mapped_column(", "models.")):
                persisted = True
            found.append((target.lower(), stmt.lineno, False))
        if persisted:
            found = [(name, line, True) for name, line, _ in found]
    return found, bool(found)


def _sql_fields(content: str) -> list[tuple[str, int, bool]]:
    found, in_table = [], False
    for line_no, line in enumerate(content.splitlines(), 1):
        if SQL_TABLE_RE.search(line):
            in_table = True
            continue
        if in_table:
            stripped = line.strip()
            if stripped.startswith(")"):
                in_table = False
                continue
            name = stripped.split()[0].strip('"`,[]') if stripped else ""
            if name and name.lower() not in SQL_SKIP and not stripped.startswith("--"):
                found.append((name.lower(), line_no, True))
    return found


def _prisma_fields(content: str) -> list[tuple[str, int, bool]]:
    found, in_model = [], False
    for line_no, line in enumerate(content.splitlines(), 1):
        if PRISMA_MODEL_RE.match(line):
            in_model = True
            continue
        if in_model:
            if line.strip() == "}":
                in_model = False
                continue
            parts = line.strip().split()
            if len(parts) >= 2 and parts[0].lower() not in PRISMA_SKIP and not parts[0].startswith("@"):
                found.append((parts[0].lower(), line_no, True))
    return found


def extract_fields(path: str, content: str) -> list[tuple[str, int, bool]]:
    suffix = PurePosixPath(path).suffix.lower()
    if suffix == ".py":
        return _python_fields(content)[0]
    if suffix == ".sql":
        return _sql_fields(content)
    if suffix == ".prisma":
        return _prisma_fields(content)
    return []


def _python_routes(content: str) -> list[tuple[str, str, int]]:
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return []
    routes = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for dec in node.decorator_list:
            if not isinstance(dec, ast.Call):
                continue
            func = dec.func
            name = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", "")
            if name not in ROUTE_METHODS and name not in NEST_METHODS:
                continue
            if dec.args and isinstance(dec.args[0], ast.Constant) and isinstance(dec.args[0].value, str):
                routes.append((name.lower(), dec.args[0].value, node.lineno))
    return routes


def extract_routes(path: str, content: str) -> list[tuple[str, str, int]]:
    routes = _python_routes(content) if PurePosixPath(path).suffix.lower() == ".py" else []
    for match in JS_ROUTE_RE.finditer(content):
        routes.append((match.group(1).lower(), match.group(2), content[:match.start()].count("\n") + 1))
    return routes


def build_change_set(files: dict[str, str], complete: bool = False) -> ChangeSet:
    cs = ChangeSet(files={p.replace("\\", "/"): c for p, c in files.items()}, complete=complete)
    for path, content in cs.files.items():
        cs.fields.extend(FieldInfo(name, path, line, persisted) for name, line, persisted in extract_fields(path, content))
        cs.routes.extend(RouteInfo(route, method, path, line) for method, route, line in extract_routes(path, content))
    return cs


def _finding(policy_id: str, path: str, line: int, severity: str, status: str, message: str,
             evidence: str, advice: str) -> Finding:
    return Finding(policy_id=policy_id, severity=severity, status=status, file=path, line=line,
                   message=message, evidence=evidence, remediation_advice=advice)


def _first_file_with(cs: ChangeSet, names: set[str]) -> FieldInfo | None:
    return next((f for f in cs.fields if f.name in names), None)


class PersonalDataDimensionsPolicy(BasePolicy):
    """Aggregates the deterministic checks of T16-T20 into one pass over the change set."""

    def __init__(self, complete: bool = False) -> None:
        super().__init__(
            policy_id="privacy.dimensions",
            description="Rights, consent, sensitive data, retention and third-party transfer checks.",
            severity="HIGH",
        )
        self.complete = complete

    def evaluate(self, task_spec: TaskSpec, modified_files: dict[str, str], diff: str | None = None) -> list[Finding]:
        cs = build_change_set(modified_files, complete=self.complete)
        findings = [
            *self._rights(cs),
            *self._consent(cs),
            *self._sensitive(cs),
            *self._retention(cs),
            *self._third_parties(cs),
        ]
        seen, unique = set(), []
        for f in findings:
            key = (f.policy_id, f.file, f.message)
            if key not in seen:
                seen.add(key)
                unique.append(f)
        return unique

    def _rights(self, cs: ChangeSet) -> list[Finding]:
        if not cs.has_personal_data():
            return []
        anchor = _first_file_with(cs, set(PERSONAL_FIELDS) | set(SENSITIVE_FIELDS))
        routes = " ".join(r.path.lower().replace("/", " ").replace("_", "-") for r in cs.routes)
        out = []
        severity, status = ("HIGH", "VIOLATION") if cs.complete else ("MEDIUM", "WARNING")
        for right, keywords in RIGHT_ROUTES.items():
            if any(k in routes for k in keywords):
                continue
            out.append(_finding(
                "privacy.rights_reachability", anchor.path, anchor.line, severity, status,
                f"No route exposes the data-subject right of {right} (Ley 21.719 Art. 4-11, 10).",
                f"Personal data model '{anchor.name}' in {anchor.path}",
                f"Expose a reachable endpoint for {right}; Art. 10 requires it to be expeditious and effective.",
            ))
        if out and not any(f.name in BLOCKED_FIELDS for f in cs.fields) and not cs.contains("blocked"):
            out.append(_finding(
                "privacy.rights_reachability", anchor.path, anchor.line, severity, status,
                "No blocked state is modelled for personal data (Ley 21.719 Art. 8, block right).",
                f"Model '{anchor.name}' has no blocked/blocked_at field",
                "Model a blocked state that processing paths must honour.",
            ))
        if cs.routes and not any(f.name in REQUEST_FIELDS for f in cs.fields):
            out.append(_finding(
                "privacy.rights_reachability", anchor.path, anchor.line, "LOW", "WARNING",
                "Rights requests have no timestamp field for the 30/30/2-business-day deadlines (Art. 10).",
                "No requested_at/created_at field found in the change set",
                "Record request and response timestamps to evidence the legal deadlines.",
            ))
        return out

    def _consent(self, cs: ChangeSet) -> list[Finding]:
        out = []
        for path, content in cs.files.items():
            for match in PRETICKED_RE.finditer(content):
                line = content[:match.start()].count("\n") + 1
                out.append(_finding(
                    "privacy.consent_transparency", path, line, "HIGH", "VIOLATION",
                    "Consent is pre-ticked by default (Ley 21.719 Arts. 12, 14 ter; Ley 19.496 Art. 28 B).",
                    match.group(0).strip(), "Default consent to false and require an explicit action.",
                ))
            for match in HTML_PRETICKED_RE.finditer(content):
                line = content[:match.start()].count("\n") + 1
                out.append(_finding(
                    "privacy.consent_transparency", path, line, "HIGH", "VIOLATION",
                    "Consent checkbox is pre-checked in a template (Ley 21.719 Arts. 12, 14 ter).",
                    match.group(0).strip(), "Remove the checked attribute; require an explicit opt-in.",
                ))
            if PurePosixPath(path).suffix.lower() in TEMPLATE_EXTS:
                lowered = content.lower()
                stem = PurePosixPath(path).stem.lower()
                is_campaign = any(hint in stem for hint in MARKETING_PATH_HINTS)
                if is_campaign and any(w in lowered for w in MARKETING_WORDS) and not any(
                        u in lowered for u in UNSUBSCRIBE_WORDS):
                    out.append(_finding(
                        "privacy.consent_transparency", path, 1, "MEDIUM", "WARNING",
                        "Marketing template without a visible unsubscribe/opt-out (Ley 19.496 Art. 28 B).",
                        "No unsubscribe/baja link found in the template",
                        "Add an unsubscribe link, the sender identity and a subject line.",
                    ))
        consent_fields = [f for f in cs.fields if f.name in CONSENT_FIELDS]
        if consent_fields:
            names = cs.field_names()
            if not names & CONSENT_RECORD_FIELDS:
                out.append(_finding(
                    "privacy.consent_transparency", consent_fields[0].path, consent_fields[0].line,
                    "MEDIUM", "WARNING",
                    "Consent is stored without timestamp, purpose or policy version (Art. 12).",
                    f"Fields: {sorted(names & CONSENT_FIELDS)}",
                    "Record consent with granted_at, purpose and policy version.",
                ))
            routes = " ".join(r.path.lower() for r in cs.routes)
            grants = any(r.method in ("post", "put", "patch") and "consent" in r.path.lower() for r in cs.routes)
            revokes = any(w in routes for w in ("revoke", "withdraw", "unsubscribe", "baja"))
            if grants and not revokes:
                out.append(_finding(
                    "privacy.consent_transparency", consent_fields[0].path, consent_fields[0].line,
                    "MEDIUM", "WARNING",
                    "Consent can be granted but no revocation route exists (Art. 12).",
                    "Grant route without revoke/withdraw/unsubscribe route",
                    "Make withdrawal as reachable as the grant.",
                ))
        if cs.has_personal_data():
            routes = " ".join(r.path.lower() for r in cs.routes)
            if not any(w in routes for w in ("privacy", "privacidad", "politica")):
                anchor = _first_file_with(cs, set(PERSONAL_FIELDS) | set(SENSITIVE_FIELDS))
                out.append(_finding(
                    "privacy.consent_transparency", anchor.path, anchor.line, "MEDIUM", "WARNING",
                    "No privacy-policy route found (Ley 21.719 Arts. 14 ter, 14 quater).",
                    "Personal data is processed but no /privacy or /privacidad route is declared",
                    "Publish the privacy policy with version, date and a contact channel.",
                ))
        return out

    def _sensitive(self, cs: ChangeSet) -> list[Finding]:
        out = []
        for f in cs.fields:
            if f.name in BIOMETRIC_FIELDS and not any(m in f.name for m in MASKERS):
                out.append(_finding(
                    "privacy.minors_and_sensitive", f.path, f.line, "CRITICAL", "VIOLATION",
                    f"Raw biometric template field '{f.name}' is stored (Art. 16 sexies).",
                    f"{f.name} in {f.path}",
                    "Store a template identifier or an irreversible hash, never the raw template.",
                ))
            if f.name in SENSITIVE_FIELDS and not (cs.contains(*MASKERS) or cs.contains("explicit_consent", "sensitive_consent")):
                out.append(_finding(
                    "privacy.minors_and_sensitive", f.path, f.line, "MEDIUM", "WARNING",
                    f"Sensitive field '{f.name}' has no explicit consent or protection marker (Art. 2 g, 16).",
                    f"{f.name} in {f.path}",
                    "Require explicit consent and document the sensitive-data classification.",
                ))
        age_field = _first_file_with(cs, AGE_FIELDS)
        if age_field:
            age_gate = cs.contains("age_gate", "is_minor", "guardian", "parental", "tutor") or any(
                num in "".join(cs.files.values()) for num in ("14", "16")
            )
            if not age_gate:
                out.append(_finding(
                    "privacy.minors_and_sensitive", age_field.path, age_field.line, "MEDIUM", "WARNING",
                    "Age data is collected without an age gate at 14/16 (Art. 16 quater).",
                    f"{age_field.name} in {age_field.path}",
                    "Gate processing for children under 14 and adolescents 14-17; record parental consent.",
                ))
        geo = _first_file_with(cs, GEOLOCATION_FIELDS)
        if geo and not cs.contains("consent", "notice", "privacy", "geolocation_notice"):
            out.append(_finding(
                "privacy.minors_and_sensitive", geo.path, geo.line, "MEDIUM", "WARNING",
                "Geolocation is collected without consent or notice (Art. 16 ter).",
                f"{geo.name} in {geo.path}",
                "Collect geolocation only behind consent and a specific notice.",
            ))
        return out

    def _retention(self, cs: ChangeSet) -> list[Finding]:
        out = []
        routines = cs.contains(*RETENTION_ROUTINES)
        names = cs.field_names()
        for f in cs.fields:
            if not f.persisted or f.name not in PERSONAL_FIELDS | SENSITIVE_FIELDS:
                continue
            if names & RETENTION_FIELDS or routines:
                continue
            out.append(_finding(
                "privacy.retention_minimization", f.path, f.line, "MEDIUM", "WARNING",
                f"Personal field '{f.name}' has no retention field or purge routine (Arts. 3 c, 17-18).",
                f"{f.name} in persisted model {f.path}",
                "Declare a retention period per entity and purge or anonymise when it expires.",
            ))
        soft_deleted = [f for f in cs.fields if f.name in ("deleted_at", "is_deleted", "deleted")]
        if soft_deleted and cs.has_personal_data():
            out.append(_finding(
                "privacy.retention_minimization", soft_deleted[0].path, soft_deleted[0].line,
                "LOW", "WARNING",
                "Soft delete keeps personal data without an anonymisation or purge path (Art. 3 c).",
                f"{soft_deleted[0].name} in {soft_deleted[0].path}",
                "Anonymise or purge personal fields after the retention period; deleting the flag is not enough.",
            ))
        return out

    def _third_parties(self, cs: ChangeSet) -> list[Finding]:
        if not cs.has_personal_data():
            return []
        out = []
        for path, content in cs.files.items():
            hosts = sorted({h.lower() for h in URL_RE.findall(content)} - IGNORED_HOSTS)
            if not hosts:
                continue
            out.append(_finding(
                "privacy.third_party_transfers", path, 1, "LOW", "WARNING",
                "Third parties that may receive personal data need a contract and a transfer basis (Arts. 15 bis, 27).",
                f"Hosts referenced: {', '.join(hosts)}",
                "Inventory each processor/SDK, its region and the transfer basis; contracts stay documentary evidence.",
            ))
        return out
