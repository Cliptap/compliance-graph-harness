"""Evidence gate for the controls a detector cannot decide.

Some Ley 21.719 edges are documentary: an impact assessment, an incident register,
a PCI attestation. No AST proves them, and pretending otherwise produces findings
that a developer learns to ignore. This gate blocks the merge until the artifact
exists, has an owner and is inside its validity window.

The manifest is ``.harness/evidence.json``::

    {
      "version": 1,
      "evidence": [
        {
          "control": "CORE-CHECK-009",
          "artifact": "docs/eipd.md",
          "owner": "DPO",
          "granted_at": "2026-03-01",
          "expires_at": "2027-03-01"
        }
      ]
    }

Run it in CI, not in the pre-commit hook: a missing impact assessment is a
repository-level state, not a property of the commit under review.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from src.harness.catalog import Catalog, CatalogError, Control, load_catalog

MANIFEST = Path(".harness") / "evidence.json"
DEFAULT_PACK = Path(".harness") / "packs" / "catalog.full.json"


@dataclass(frozen=True)
class EvidenceGap:
    control: str
    title: str
    reason: str
    detail: str


def required_controls(catalog: Catalog) -> list[Control]:
    """Controls the pack declares as documentary evidence."""
    return [control for control in catalog.controls if control.evidence]


def _parse_date(value: object) -> date | None:
    if not isinstance(value, str):
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _load_entries(manifest: Path) -> dict[str, dict]:
    if not manifest.is_file():
        return {}
    try:
        raw = json.loads(manifest.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise CatalogError(f"{manifest.as_posix()}: invalid JSON: {exc}") from exc
    if not isinstance(raw, dict) or not isinstance(raw.get("evidence", []), list):
        raise CatalogError(f"{manifest.as_posix()}: expected an 'evidence' list")
    entries: dict[str, dict] = {}
    for entry in raw.get("evidence", []):
        if isinstance(entry, dict) and isinstance(entry.get("control"), str):
            entries[entry["control"]] = entry
    return entries


def check(root: Path | str, pack_path: Path | str | None = None,
          today: date | None = None) -> list[EvidenceGap]:
    """Every required control that has no valid artifact, in pack order."""
    root = Path(root)
    pack = Path(pack_path) if pack_path is not None else root / DEFAULT_PACK
    catalog = load_catalog(pack)
    entries = _load_entries(root / MANIFEST)
    today = today or date.today()
    gaps: list[EvidenceGap] = []
    for control in required_controls(catalog):
        title = control.title or control.id
        entry = entries.get(control.id)
        if entry is None:
            gaps.append(EvidenceGap(control.id, title, "missing",
                                    f"no entry in {MANIFEST.as_posix()}"))
            continue
        artifact = entry.get("artifact")
        if not isinstance(artifact, str) or not artifact.strip():
            gaps.append(EvidenceGap(control.id, title, "missing artifact",
                                    "the entry needs an 'artifact' path"))
            continue
        if not (root / artifact).is_file():
            gaps.append(EvidenceGap(control.id, title, "artifact not found", artifact))
            continue
        if not str(entry.get("owner") or "").strip():
            gaps.append(EvidenceGap(control.id, title, "missing owner", artifact))
        expires = _parse_date(entry.get("expires_at"))
        if expires is None:
            gaps.append(EvidenceGap(control.id, title, "missing expiry",
                                    f"{artifact} needs an ISO 'expires_at' date"))
        elif expires < today:
            gaps.append(EvidenceGap(control.id, title, "expired",
                                    f"{artifact} expired on {expires.isoformat()}"))
    return gaps


def format_report(gaps: list[EvidenceGap]) -> str:
    if not gaps:
        return "[evidence] every required artifact is present, owned and current."
    lines = [f"[evidence] merge blocked: {len(gaps)} evidence gap(s)."]
    for gap in gaps:
        lines.append(f"- {gap.control} [{gap.reason}]: {gap.title}")
        lines.append(f"  {gap.detail}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Evidence gate for the documentary controls of the pack.")
    parser.add_argument("--root", default=".", help="project root (default: .)")
    parser.add_argument("--pack", default=None,
                        help=f"pack path (default: <root>/{DEFAULT_PACK.as_posix()})")
    args = parser.parse_args(argv)
    gaps = check(args.root, args.pack)
    print(format_report(gaps))
    return 1 if gaps else 0


if __name__ == "__main__":
    raise SystemExit(main())
