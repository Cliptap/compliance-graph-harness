import json
from pathlib import Path

import pytest

from src.harness.catalog import CatalogError, load_catalog

PACKS = Path(__file__).resolve().parents[2] / ".harness" / "packs"
CATALOG = PACKS / "catalog.v2.json"
FULL = PACKS / "catalog.full.json"


def test_catalog_loads_and_maps_frameworks():
    catalog = load_catalog(CATALOG)
    assert catalog.pack_id == "cl-ley-21719"
    control = catalog.control("v2.log_pii")
    labels = control.framework_labels()
    assert any("Ley 21.719" in label for label in labels)
    assert any("ISO/IEC 27001:2022 A.8.12" in label for label in labels)
    assert any("CWE CWE-532" in label for label in labels)


def test_is_sanitizer_requires_a_call():
    catalog = load_catalog(FULL)
    assert catalog.is_sanitizer("mask_rut(customer['rut'])")
    assert catalog.is_sanitizer("_fingerprint(secret, customer['rut'])")
    assert catalog.is_sanitizer("bcrypt.hashpw(value, salt)")
    assert not catalog.is_sanitizer("{'password_hash': customer.password_hash}")
    assert not catalog.is_sanitizer("{'anonymous': 1}")


def test_catalog_rejects_unknown_policy(tmp_path):
    data = json.loads(CATALOG.read_text(encoding="utf-8"))
    data["controls"][0]["detection"]["policy"] = "does_not_exist"
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(CatalogError):
        load_catalog(path)


def test_full_catalog_migrates_all_controls_and_declares_gaps():
    catalog = load_catalog(FULL)
    assert len(catalog.controls) >= 30
    assert catalog.control("v2.log_pii")
    gaps = [control for control in catalog.controls if not control.implemented]
    assert gaps and all(control.gap_reason for control in gaps)


def test_legacy_adapter_maps_old_policy_findings():
    from src.harness.catalog_engine import CatalogEngine
    from src.harness.contracts import TaskSpec

    engine = CatalogEngine(load_catalog(FULL))
    findings = engine.evaluate(
        TaskSpec(task_id="t", goal="g", allowed_paths=["*"], forbidden_paths=[]),
        {"app/main.py": "def f(rut):\n    logger.info('rut=%s', rut)\n"},
    )
    ids = {finding.policy_id for finding in findings}
    assert "v2.log_pii" in ids
    assert "CORE-CHECK-002" in ids


def test_catalog_rejects_unknown_framework(tmp_path):
    data = json.loads(CATALOG.read_text(encoding="utf-8"))
    data["controls"][0]["frameworks"][0]["framework"] = "NOPE"
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(CatalogError):
        load_catalog(path)
