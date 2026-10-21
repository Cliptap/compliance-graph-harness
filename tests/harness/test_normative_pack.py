import copy
import json
from pathlib import Path

import pytest

from src.harness.normative_pack import PackError, load_pack, to_legacy_rules, validate_pack

ROOT = Path(__file__).resolve().parents[2]
PACK = ROOT / ".harness" / "packs" / "cl-ley-21719.json"
LEGACY = ROOT / ".harness" / "compliance_rules.json"


def test_shipped_pack_is_valid_and_complete():
    pack = load_pack(PACK)
    legacy = json.loads(LEGACY.read_text(encoding="utf-8"))
    expected = (len(legacy["rules"]) + len(legacy["core_checklist"])
                + sum(len(p["criteria"]) for p in legacy["sectorial_plugins"].values()))
    assert len(pack["controls"]) == expected == 14


def test_legacy_projection_matches_original_rules():
    pack = load_pack(PACK)
    legacy = json.loads(LEGACY.read_text(encoding="utf-8"))["rules"]
    projected = to_legacy_rules(pack)
    for old, new in zip(legacy, projected):
        assert new["rule_id"] == old["rule_id"]
        assert new["prohibited_sinks"] == old["prohibited_sinks"]
        assert new["required_mitigations"] == old["required_mitigations"]
        assert new["severity"] == old["severity"]
        assert new["sensitive_category"] == old["sensitive_category"]
        assert new["cwe"] == old["cwe"]
    assert len(projected) == len(legacy)


def test_every_control_cites_a_declared_law_and_article():
    pack = load_pack(PACK)
    for c in pack["controls"]:
        for s in c["sources"]:
            assert s["law"] in pack["laws"] and s["article"]


@pytest.mark.parametrize("mutate,msg", [
    (lambda c: c.update(severity="SEVERE"), "invalid severity"),
    (lambda c: c.update(sources=[]), "legal source"),
    (lambda c: c["sources"][0].update(law="L0"), "not declared"),
    (lambda c: c["detection"].update(type="magic"), "invalid detection type"),
    (lambda c: c.pop("evidence"), "missing 'evidence'"),
    (lambda c: c.update(id="bad id"), "invalid id format"),
])
def test_invalid_control_is_rejected(mutate, msg):
    pack = copy.deepcopy(load_pack(PACK))
    mutate(pack["controls"][0])
    with pytest.raises(PackError, match=msg):
        validate_pack(pack)


def test_duplicate_ids_rejected():
    pack = copy.deepcopy(load_pack(PACK))
    pack["controls"].append(copy.deepcopy(pack["controls"][0]))
    with pytest.raises(PackError, match="duplicate"):
        validate_pack(pack)
