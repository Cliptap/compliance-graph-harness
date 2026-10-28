"""Pre-commit gate: blocks privacy violations in the staged content.

It evaluates what is in the git index (what will be committed), never the working tree, with
the two deterministic privacy policies (CWE-532 logging and API personal-data exposure).
Scope and domain policies need a TaskSpec and are not part of the gate. Findings are mapped
to the pack controls so the report cites the law article. ``git commit --no-verify`` bypasses
any git hook; this gate is a safety net for honest mistakes, not an enforcement mechanism.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

from src.harness.contracts import Finding, TaskSpec
from src.harness.exposure_policy import ApiPersonalDataExposurePolicy
from src.harness.normative_pack import load_pack
from src.harness.payment_policy import PaymentDataStoragePolicy
from src.harness.policy_engine import PolicyEngine, SensitiveLoggingPolicy

DEFAULT_PACK = Path(__file__).resolve().parents[2] / ".harness" / "packs" / "cl-ley-21719.json"
EXTENSIONS = (".py", ".js", ".jsx", ".ts", ".tsx")
EXCLUDED_PREFIXES = ("tests/", "harness/eval/")
BLOCKING_SEVERITIES = ("CRITICAL", "HIGH")
HOOK_MARKER = "installed by the vibecoding harness (src.harness.precommit)"
HOOK_BODY = f"#!/bin/sh\n# {HOOK_MARKER}\nexec ${{HARNESS_PYTHON:-python}} -m src.harness.precommit --root .\n"

POLICY_CONTROLS = {
    "privacy.cwe_532": ("CORE-CHECK-002", "CL-DATAPROT-001"),
    "privacy.api_exposure": ("CORE-CHECK-002",),
    "privacy.payment_data_storage": ("ECOM-CHECK-003",),
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


def evaluate(files: dict[str, str], pack_path: Path = DEFAULT_PACK) -> GateResult:
    load_pack(pack_path)  # refuses to gate against an invalid pack
    selected = {p: c for p, c in files.items() if _eligible(p.replace("\\", "/"))}
    engine = PolicyEngine([SensitiveLoggingPolicy(), ApiPersonalDataExposurePolicy(), PaymentDataStoragePolicy()])
    return GateResult(engine.evaluate_changes(_TASK, selected), sorted(selected))


def format_report(result: GateResult, pack_path: Path = DEFAULT_PACK) -> str:
    if not result.findings:
        return ""
    controls = {c["id"]: c for c in load_pack(pack_path)["controls"]}
    lines = ["[harness] Commit blocked: privacy findings in staged changes." if result.blocked
             else "[harness] Privacy warnings in staged changes (commit allowed)."]
    for f in result.findings:
        lines.append(f"- {f.file}:{f.line} [{f.severity}] {f.policy_id}: {f.message}")
        if f.evidence:
            lines.append(f"    evidence: {f.evidence}")
        if f.remediation_advice:
            lines.append(f"    fix: {f.remediation_advice}")
        for cid in POLICY_CONTROLS.get(f.policy_id, ()):
            cites = "; ".join(s["citation"] for s in controls[cid]["sources"])
            lines.append(f"    control {cid}: {controls[cid]['title']} | {cites}")
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
    parser.add_argument("--install", action="store_true", help="install the git pre-commit hook")
    parser.add_argument("--force", action="store_true", help="overwrite an existing foreign hook")
    args = parser.parse_args(argv)
    if args.install:
        try:
            print(f"Installed {install_hook(args.root, args.force)}")
        except FileExistsError as exc:
            print(exc, file=sys.stderr)
            return 2
        return 0
    result = evaluate(collect_staged(args.root), args.pack)
    report = format_report(result, args.pack)
    if report:
        print(report, file=sys.stderr)
    return 1 if result.blocked else 0


if __name__ == "__main__":
    raise SystemExit(main())
