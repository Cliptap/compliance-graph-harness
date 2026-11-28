"""Pre-commit gate: blocks privacy violations in the staged content.

It evaluates what is in the git index (what will be committed), never the working tree, with the
same engine validated in the dose experiment: the pack-driven ``CatalogEngine`` (v2 families:
sink_exposure, retention_deletion, credential_exposure) plus the legacy privacy policies
(CWE-532 logging, API personal-data exposure, payment data storage, Ley 21.719 dimension
checks and clinical retention invariants). Retention and credential checks also rely on the
AST-based v2 families; the line-based legacy customer-deletion policy is excluded from the gate
to avoid comment/docstring false positives, and the remaining line-based policies skip lines
that are only comments or strings. Scope and dependency policies need a TaskSpec and are not
part of the gate. Findings are mapped to the pack controls so the report cites the law article.
``git commit --no-verify`` bypasses any git hook; this gate is a safety net for honest mistakes,
not an enforcement mechanism.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

from src.harness.catalog import CatalogError, load_catalog
from src.harness.catalog_engine import CatalogEngine
from src.harness.contracts import Finding, TaskSpec
from src.harness.dimension_policy import PersonalDataDimensionsPolicy
from src.harness.exposure_policy import ApiPersonalDataExposurePolicy
from src.harness.payment_policy import PaymentDataStoragePolicy
from src.harness.policy_engine import DomainInvariantPolicy, PolicyEngine, SensitiveLoggingPolicy

DEFAULT_PACK = Path(__file__).resolve().parents[2] / ".harness" / "packs" / "catalog.full.json"
EXTENSIONS = (".py", ".js", ".jsx", ".ts", ".tsx")
# tests/ and harness/eval/ are test and evaluation code; experiments/ holds deliberately
# vulnerable fixtures (seeded defects, RUTs in logs, credentials in responses) that the
# gate must not block on.
EXCLUDED_PREFIXES = ("tests/", "harness/eval/", "experiments/")
BLOCKING_SEVERITIES = ("CRITICAL", "HIGH")
HOOK_MARKER = "installed by the vibecoding harness (src.harness.precommit)"
HOOK_BODY = (
    "#!/bin/sh\n"
    f"# {HOOK_MARKER}\n"
    "if [ -n \"$VIBECODING_HARNESS_ROOT\" ]; then\n"
    "  export PYTHONPATH=\"$VIBECODING_HARNESS_ROOT${PYTHONPATH:+:$PYTHONPATH}\"\n"
    "fi\n"
    "exec ${HARNESS_PYTHON:-python} -m src.harness.precommit --root .\n"
)

LEGACY_CONTROLS = {
    "privacy.cwe_532": ("CORE-CHECK-002",),
    "privacy.api_exposure": ("CORE-CHECK-002",),
    "privacy.payment_data_storage": ("ECOM-CHECK-003",),
    "privacy.consent_transparency": ("CORE-CHECK-005", "CORE-CHECK-007", "ECOM-CHECK-001"),
    "privacy.rights_reachability": ("CORE-CHECK-006",),
    "privacy.minors_and_sensitive": ("CORE-CHECK-012", "ECOM-CHECK-007"),
    "privacy.retention_minimization": ("CORE-CHECK-013",),
    "privacy.third_party_transfers": ("CORE-CHECK-010", "CORE-CHECK-011", "ECOM-CHECK-005"),
    "domain.prohibited_deletion": ("CL-DATAPROT-004", "HEALTH-CHECK-001"),
}
DISCLAIMER = ("Validated against the primary legal text by the harness authors; this report is "
              "not legal advice (no es asesoría legal).")
_TASK = TaskSpec(task_id="PRECOMMIT", goal="Pre-commit privacy gate", category="compliance")


@dataclass
class GateResult:
    findings: list[Finding] = field(default_factory=list)
    files: list[str] = field(default_factory=list)

    @property
    def blocked(self) -> bool:
        return any(f.status == "VIOLATION" and f.severity in BLOCKING_SEVERITIES for f in self.findings)


def _git(root: Path, *args: str) -> str:
    proc = subprocess.run(["git", "-C", str(root), "-c", "core.quotepath=off", *args],
                          capture_output=True, check=True)
    return proc.stdout.decode("utf-8", errors="replace")


def _eligible(path: str) -> bool:
    return path.endswith(EXTENSIONS) and not path.startswith(EXCLUDED_PREFIXES)


def collect_staged(root: Path) -> dict[str, str]:
    names = _git(root, "diff", "--cached", "--name-only", "--diff-filter=ACM").splitlines()
    return {n: _git(root, "show", f":{n}") for n in names if n.endswith(EXTENSIONS)}


def _read_files(root: Path, rel_paths: list[str]) -> dict[str, str]:
    files: dict[str, str] = {}
    for rel in rel_paths:
        rel = rel.replace("\\", "/")
        target = root / rel
        if target.is_file():
            files[rel] = target.read_text(encoding="utf-8", errors="replace")
    return files


def _merge(left: list[Finding], right: list[Finding]) -> list[Finding]:
    seen = {(f.policy_id, f.file, f.line, f.message) for f in left}
    for finding in right:
        key = (finding.policy_id, finding.file, finding.line, finding.message)
        if key not in seen:
            seen.add(key)
            left.append(finding)
    return left


def evaluate(files: dict[str, str], pack_path: Path = DEFAULT_PACK) -> GateResult:
    load_catalog(pack_path)  # refuses to gate against an invalid pack
    selected = {p: c for p, c in files.items() if _eligible(p.replace("\\", "/"))}
    legacy = PolicyEngine(
        [
            SensitiveLoggingPolicy(),
            ApiPersonalDataExposurePolicy(),
            PaymentDataStoragePolicy(),
            PersonalDataDimensionsPolicy(),
            DomainInvariantPolicy(),
        ]
    ).evaluate_changes(_TASK, selected)
    v2 = CatalogEngine(load_catalog(pack_path), include_legacy=False).evaluate(_TASK, selected)
    return GateResult(_merge(legacy, v2), sorted(selected))


def _control_ids(policy_id: str) -> tuple[str, ...]:
    if policy_id in LEGACY_CONTROLS:
        return LEGACY_CONTROLS[policy_id]
    if policy_id.startswith(("v2.", "CORE-", "CL-", "HEALTH-", "ECOM-")):
        return (policy_id,)
    return ()


def format_report(result: GateResult, pack_path: Path = DEFAULT_PACK) -> str:
    if not result.findings:
        return ""
    catalog = load_catalog(pack_path)
    lines = ["[harness] Commit blocked: privacy findings." if result.blocked
             else "[harness] Privacy warnings (commit allowed)."]
    for f in result.findings:
        lines.append(f"- {f.file}:{f.line} [{f.severity}] {f.policy_id}: {f.message}")
        if f.evidence:
            lines.append(f"    evidence: {f.evidence}")
        if f.remediation_advice:
            lines.append(f"    fix: {f.remediation_advice}")
        for cid in _control_ids(f.policy_id):
            try:
                control = catalog.control(cid)
                cites = "; ".join(control.framework_labels())
                lines.append(f"    control {cid}: {control.title} | {cites}")
            except CatalogError:
                continue
    lines.append(DISCLAIMER)
    return "\n".join(lines)


def install_hook(root: Path, force: bool = False) -> Path:
    hook = Path(_git(root, "rev-parse", "--git-path", "hooks/pre-commit").strip())
    if not hook.is_absolute():
        hook = Path(root) / hook
    if hook.exists() and not force and HOOK_MARKER not in hook.read_text(encoding="utf-8", errors="replace"):
        raise FileExistsError(f"{hook} already exists and was not installed by the harness; use --force")
    hook.parent.mkdir(parents=True, exist_ok=True)
    hook.write_text(HOOK_BODY, encoding="utf-8", newline="\n")
    hook.chmod(0o755)
    return hook


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m src.harness.precommit", description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--pack", type=Path, default=DEFAULT_PACK)
    parser.add_argument("--files", nargs="*", default=None,
                        help="check these working-tree files instead of the staged content")
    parser.add_argument("--install", action="store_true", help="install the git pre-commit hook")
    parser.add_argument("--force", action="store_true", help="overwrite an existing foreign hook")
    parser.add_argument("--refresh-map", action="store_true",
                        help="refresh the evidence map entries for the evaluated files (M5)")
    parser.add_argument("--evidence-db", type=Path,
                        default=Path(__file__).resolve().parents[2] / ".harness" / "harness.db",
                        help="harness database for the evidence map")
    args = parser.parse_args(argv)
    if args.install:
        try:
            print(f"Installed {install_hook(args.root, args.force)}")
        except FileExistsError as exc:
            print(exc, file=sys.stderr)
            return 2
        return 0
    if args.files is not None:
        files = _read_files(args.root, args.files)
    else:
        files = collect_staged(args.root)
    result = evaluate(files, args.pack)
    report = format_report(result, args.pack)
    if report:
        print(report, file=sys.stderr)
    harness_root = Path(__file__).resolve().parents[2]
    if args.refresh_map or args.root.resolve() == harness_root.resolve():
        try:
            from src.harness.antecedentes import refresh_files

            refresh_files(args.evidence_db, str(args.root.resolve()), files)
        except Exception:  # the map must never break the gate
            pass
    return 1 if result.blocked else 0


if __name__ == "__main__":
    raise SystemExit(main())
