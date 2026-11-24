"""Evidence gate: a documentary control blocks until its artifact is valid."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest

from src.harness import evidence

ROOT = Path(__file__).resolve().parents[2]
PACK = ROOT / ".harness" / "packs" / "catalog.full.json"
TODAY = date(2026, 11, 24)


def _manifest(root: Path, entries: list[dict]) -> None:
    target = root / ".harness" / "evidence.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps({"version": 1, "evidence": entries}), encoding="utf-8")


def _artifact(root: Path, name: str = "docs/eipd.md") -> str:
    target = root / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("artifact\n", encoding="utf-8")
    return name


def _entry(control: str, artifact: str, **overrides) -> dict:
    base = {"control": control, "artifact": artifact, "owner": "DPO",
            "granted_at": "2026-01-01", "expires_at": "2027-01-01"}
    base.update(overrides)
    return base


def _controls() -> list[str]:
    return [c.id for c in evidence.required_controls(
        evidence.load_catalog(PACK))]


def test_the_pack_declares_six_documentary_controls():
    assert len(_controls()) == 6
    assert "CORE-CHECK-009" in _controls()
    assert "ECOM-CHECK-004" in _controls()


def test_a_missing_manifest_reports_every_required_control(tmp_path):
    gaps = evidence.check(tmp_path, PACK, today=TODAY)
    assert {gap.control for gap in gaps} == set(_controls())
    assert all(gap.reason == "missing" for gap in gaps)


def test_a_complete_manifest_has_no_gaps(tmp_path):
    entries = [_entry(control, _artifact(tmp_path, f"docs/{control}.md"))
               for control in _controls()]
    _manifest(tmp_path, entries)
    assert evidence.check(tmp_path, PACK, today=TODAY) == []


def test_a_missing_artifact_file_is_a_gap(tmp_path):
    entries = [_entry(control, _artifact(tmp_path, f"docs/{control}.md"))
               for control in _controls()]
    entries[0]["artifact"] = "docs/absent.md"
    _manifest(tmp_path, entries)
    gaps = evidence.check(tmp_path, PACK, today=TODAY)
    assert [(gap.control, gap.reason) for gap in gaps] == [
        (entries[0]["control"], "artifact not found")]


def test_an_expired_artifact_is_a_gap(tmp_path):
    entries = [_entry(control, _artifact(tmp_path, f"docs/{control}.md"))
               for control in _controls()]
    entries[1]["expires_at"] = "2026-11-23"
    _manifest(tmp_path, entries)
    gaps = evidence.check(tmp_path, PACK, today=TODAY)
    assert [(gap.control, gap.reason) for gap in gaps] == [
        (entries[1]["control"], "expired")]


def test_an_artifact_without_an_owner_is_a_gap(tmp_path):
    entries = [_entry(control, _artifact(tmp_path, f"docs/{control}.md"))
               for control in _controls()]
    entries[2]["owner"] = "  "
    _manifest(tmp_path, entries)
    gaps = evidence.check(tmp_path, PACK, today=TODAY)
    assert [(gap.control, gap.reason) for gap in gaps] == [
        (entries[2]["control"], "missing owner")]


def test_an_artifact_without_an_expiry_is_a_gap(tmp_path):
    entries = [_entry(control, _artifact(tmp_path, f"docs/{control}.md"))
               for control in _controls()]
    entries[3].pop("expires_at")
    _manifest(tmp_path, entries)
    gaps = evidence.check(tmp_path, PACK, today=TODAY)
    assert [(gap.control, gap.reason) for gap in gaps] == [
        (entries[3]["control"], "missing expiry")]


def test_the_cli_fails_when_evidence_is_missing(tmp_path, capsys):
    assert evidence.main(["--root", str(tmp_path), "--pack", str(PACK)]) == 1
    output = capsys.readouterr().out
    assert "merge blocked" in output
    assert "CORE-CHECK-009" in output


def test_the_cli_passes_with_a_complete_manifest(tmp_path, capsys):
    entries = [_entry(control, _artifact(tmp_path, f"docs/{control}.md"))
               for control in _controls()]
    _manifest(tmp_path, entries)
    assert evidence.main(["--root", str(tmp_path), "--pack", str(PACK)]) == 0
    assert "every required artifact" in capsys.readouterr().out


def test_an_implemented_control_cannot_also_be_documentary(tmp_path):
    """The pack invariant: evidence is for controls no detector can decide."""
    raw = json.loads(PACK.read_text(encoding="utf-8"))
    documentary = next(c for c in raw["controls"] if c.get("evidence"))
    documentary["implemented"] = True
    pack = tmp_path / "pack.json"
    pack.write_text(json.dumps(raw), encoding="utf-8")
    with pytest.raises(evidence.CatalogError):
        evidence.load_catalog(pack)


def test_a_malformed_manifest_is_a_catalog_error(tmp_path):
    target = tmp_path / ".harness" / "evidence.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("{not json", encoding="utf-8")
    with pytest.raises(evidence.CatalogError):
        evidence.check(tmp_path, PACK, today=TODAY)
