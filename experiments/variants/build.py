"""Build the experiment A variants and verify them against the hidden manifest.

Each variant is a copy of the clean base with exactly one seeded defect (or none, for the clean
controls). The manifest stays in this directory and must never be copied into an audit workspace.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.harness.contracts import TaskSpec  # noqa: E402
from src.harness.policy_engine import PolicyEngine  # noqa: E402

HERE = Path(__file__).resolve().parent
BASE = ROOT / "experiments" / "supermercado"
MANIFEST = HERE / "manifest.json"
GENERATED = HERE / "generated"
EXTS = {".py", ".js", ".jsx", ".ts", ".tsx", ".sql", ".html"}
IGNORE = shutil.ignore_patterns("data", "__pycache__", ".pytest_cache", "*.pyc", "photos")
SPEC = TaskSpec(task_id="VARIANT", goal="variant", allowed_paths=["*"])


def load_manifest(path: Path = MANIFEST) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _apply(dest: Path, mutation: dict) -> None:
    target = dest / mutation["path"]
    op = mutation["op"]
    if op == "add_file":
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(mutation["content"], encoding="utf-8", newline="\n")
        return
    if op == "delete_file":
        if target.exists():
            target.unlink()
        return
    if op == "replace":
        text = target.read_text(encoding="utf-8")
        find = mutation["find"]
        count = text.count(find)
        if count != 1:
            raise ValueError(f"{mutation['path']}: expected one match, found {count}")
        target.write_text(text.replace(find, mutation["replace"], 1), encoding="utf-8", newline="\n")
        return
    raise ValueError(f"unknown mutation op {op!r}")


def build(variant: dict, dest: Path) -> Path:
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(BASE, dest, ignore=IGNORE)
    for mutation in variant["mutations"]:
        _apply(dest, mutation)
    return dest


def scan(dest: Path) -> set[tuple[str, str]]:
    files = {}
    for path in sorted(dest.rglob("*")):
        if not path.is_file() or path.suffix not in EXTS:
            continue
        if any(part in {"data", "__pycache__", ".pytest_cache"} for part in path.relative_to(dest).parts):
            continue
        files[path.relative_to(dest).as_posix()] = path.read_text(encoding="utf-8", errors="replace")
    findings = PolicyEngine().evaluate_changes(SPEC, files)
    return {(f.policy_id, f.status) for f in findings if f.status in ("VIOLATION", "WARNING")}


def expected(variant: dict) -> set[tuple[str, str]]:
    return {(item["policy"], item["detector_status"]) for item in variant["expected"]}


def main() -> int:
    parser = argparse.ArgumentParser(prog="python experiments/variants/build.py")
    parser.add_argument("--write", action="store_true", help="keep the variants under generated/")
    parser.add_argument("--only", help="build a single variant id")
    parser.add_argument("--list", action="store_true")
    args = parser.parse_args()

    manifest = load_manifest()
    variants = manifest["variants"]
    if args.list:
        for variant in variants:
            print(f"{variant['id']:34} {variant['kind']:7} {variant['description']}")
        return 0

    failures = 0
    for variant in variants:
        if args.only and variant["id"] != args.only:
            continue
        dest = (GENERATED / variant["id"]) if args.write else Path(tempfile.mkdtemp()) / variant["id"]
        build(variant, dest)
        actual = scan(dest)
        want = expected(variant)
        ok = actual == want
        print(f"{variant['id']:34} {'OK' if ok else 'FAIL':4} expected={sorted(want)}")
        if not ok:
            failures += 1
            if want - actual:
                print(f"{'':39}missing={sorted(want - actual)}")
            if actual - want:
                print(f"{'':39}extra={sorted(actual - want)}")
        if not args.write:
            shutil.rmtree(dest.parent, ignore_errors=True)

    print(f"variants={len(variants)} failures={failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
