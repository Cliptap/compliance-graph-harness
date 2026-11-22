"""Environment checks for the compliance graph harness.

Run ``harness-doctor`` or ``python -m src.harness.doctor`` after installing. Required checks
(python, dependencies, packs, gate smoke) fail the command; optional checks (git, pre-commit hook,
.env) are reported but do not block.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


@dataclass
class Check:
    name: str
    ok: bool
    detail: str = ""
    required: bool = True


def _check_python() -> Check:
    ok = sys.version_info >= (3, 12)
    return Check("python>=3.12", ok, sys.version.split()[0])


def _check_dependencies() -> Check:
    missing = [name for name in ("pydantic",) if importlib.util.find_spec(name) is None]
    return Check("dependencies", not missing, "missing: " + ", ".join(missing) if missing else "pydantic")


def _check_packs(root: Path) -> Check:
    from src.harness.catalog import load_catalog
    from src.harness.normative_pack import load_legacy_view

    catalog_path = root / ".harness" / "packs" / "catalog.full.json"
    legacy_path = root / ".harness" / "packs" / "cl-ley-21719.json"
    if not catalog_path.is_file() or not legacy_path.is_file():
        return Check("packs", False, "missing .harness/packs/*.json")
    try:
        catalog = load_catalog(catalog_path)
        load_legacy_view(legacy_path)
    except Exception as exc:  # noqa: BLE001 - the doctor reports any load failure
        return Check("packs", False, str(exc))
    return Check("packs", True, f"{len(catalog.controls)} controls")


def _check_gate() -> Check:
    from src.harness.precommit import DEFAULT_PACK, evaluate

    code = "def f(customer):\n    logger.info('rut=%s', customer['rut'])\n"
    result = evaluate({"app/x.py": code}, DEFAULT_PACK)
    hit = any(f.policy_id in {"v2.log_pii", "privacy.cwe_532"} for f in result.findings)
    return Check("gate smoke", hit, "raw RUT detected" if hit else "raw RUT not detected")


def _check_git(root: Path) -> Check:
    return Check("git repository", (root / ".git").exists(), str(root), required=False)


def _check_hook(root: Path) -> Check:
    hook = root / ".git" / "hooks" / "pre-commit"
    if hook.is_file():
        return Check("pre-commit hook", True, str(hook), required=False)
    return Check("pre-commit hook", False, "not installed (optional)", required=False)


def _check_env(root: Path) -> Check:
    env_file = root / ".env"
    if env_file.is_file():
        return Check(".env", True, "present", required=False)
    return Check(".env", False, "missing (optional; copy .env.example)", required=False)


def run_checks(root: Path = ROOT) -> list[Check]:
    return [
        _check_python(),
        _check_dependencies(),
        _check_packs(root),
        _check_gate(),
        _check_git(root),
        _check_hook(root),
        _check_env(root),
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="harness-doctor", description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    checks = run_checks(args.root)
    if args.json:
        print(json.dumps([asdict(check) for check in checks], ensure_ascii=False, indent=2))
    else:
        for check in checks:
            if check.ok:
                status = "PASS"
            elif check.required:
                status = "FAIL"
            else:
                status = "WARN"
            print(f"[{status}] {check.name}: {check.detail}")
    failed = [check for check in checks if check.required and not check.ok]
    if failed:
        print(f"\n{len(failed)} required check(s) failed", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
