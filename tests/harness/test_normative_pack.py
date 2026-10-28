import copy
import re
from pathlib import Path

import pytest

from src.harness.normative_pack import (
    LEGAL_REVIEW, OUTCOMES, SOURCE_CHECK_STATUSES, PackError, load_legacy_view, load_pack,
    to_legacy_rules, validate_pack,
)

ROOT = Path(__file__).resolve().parents[2]
PACK = ROOT / ".harness" / "packs" / "cl-ley-21719.json"


def test_shipped_pack_is_valid_and_complete():
    assert len(load_pack(PACK)["controls"]) == 14


def test_every_control_is_pending_legal_review():
    pack = load_pack(PACK)
    assert pack["legal_review"] == "pending"
    assert all(c["legal_review"] == "pending" for c in pack["controls"])


def test_internal_standards_are_not_presented_as_law():
    by_id = {c["id"]: c for c in load_pack(PACK)["controls"]}
    for cid in ("HEALTH-CHECK-002", "CL-DATAPROT-007", "CL-DATAPROT-002"):
        assert by_id[cid]["requirement_type"] == "internal_standard"
    assert by_id["HEALTH-CHECK-001"]["requirement_type"] == "legal_obligation"
    assert "15" in by_id["HEALTH-CHECK-001"]["applicability"]["when"]


def test_retention_category_is_not_decenal():
    categories = {c["detection"].get("category") for c in load_pack(PACK)["controls"]}
    assert "RETENTION_15_YEAR_CLINICAL_RECORD" in categories
    assert not any("DECENAL" in (c or "") for c in categories)


def test_sanctions_use_legal_terminology():
    sanctions = load_pack(PACK)["sanctions"]
    assert {"leve", "grave", "gravisima"} <= set(sanctions)
    assert not {"minor", "serious", "critical"} & set(sanctions)


def test_outcomes_and_review_states_are_closed_sets():
    assert OUTCOMES == ("confirmed_violation", "potential_risk", "not_applicable", "insufficient_evidence")
    assert LEGAL_REVIEW == ("pending", "validated")


def test_legacy_view_feeds_existing_consumers():
    view = load_legacy_view(PACK)
    assert len(view["rules"]) == 7 and len(view["core_checklist"]) == 4
    assert len(view["sectorial_plugins"]["health_clinical"]["criteria"]) == 3
    assert "SENSITIVE_HEALTH" in view["data_categories"]
    assert view["rules"] == to_legacy_rules(load_pack(PACK))


def test_every_control_cites_a_declared_law_and_article():
    pack = load_pack(PACK)
    for c in pack["controls"]:
        for s in c["sources"]:
            assert s["law"] in pack["laws"] and s["article"]


def _all_sources(pack: dict) -> list[dict]:
    return [s for c in pack["controls"] for s in c["sources"]]


def test_every_source_has_a_public_source_check():
    for s in _all_sources(load_pack(PACK)):
        check = s["source_check"]
        assert check["status"] in SOURCE_CHECK_STATUSES
        assert check["url"].startswith("https://")
        assert check["retrieved"] == "2026-10-28"
        if check["status"] != "verified":
            assert check["note"].strip()


def test_source_check_is_separate_from_legal_review():
    assert SOURCE_CHECK_STATUSES == ("verified", "partially_supported", "wrong_article", "not_found")
    pack = load_pack(PACK)
    assert all(c["legal_review"] == "pending" for c in pack["controls"])


def test_no_shipped_citation_is_wrong_or_not_found():
    statuses = {s["source_check"]["status"] for s in _all_sources(load_pack(PACK))}
    assert statuses <= {"verified", "partially_supported"}


def test_known_citation_defects_are_fixed():
    text = PACK.read_text(encoding="utf-8")
    pack = load_pack(PACK)
    by_id = {c["id"]: c for c in pack["controls"]}
    assert "Art. 127" not in text
    assert "\u00c3" not in text
    assert all(s["article"] == "Artículo único" for s in _all_sources(pack) if s["law"] == "L21668")
    assert not any(re.search(r"Art\. 14°(?! (bis|ter|quáter|quinquies|sexies))", s["article"])
                   for s in _all_sources(pack) if s["law"] == "L19628")
    assert ("L20584", "Art. 13") in {(s["law"], s["article"]) for s in by_id["HEALTH-CHECK-001"]["sources"]}
    for cid in ("CL-DATAPROT-001", "CORE-CHECK-002"):
        assert any("34° ter let. i)" in s["article"] for s in by_id[cid]["sources"])
    assert "Art. 2° let. f)" in pack["data_categories"]["IDENTIFIER_RUT"]["legal_basis"]


@pytest.mark.parametrize("mutate,msg", [
    (lambda c: c["sources"][0].pop("source_check"), "source without source_check"),
    (lambda c: c["sources"][0]["source_check"].update(status="maybe"), "invalid source_check status"),
    (lambda c: c["sources"][0]["source_check"].update(url="bcn.cl"), "source_check.url"),
    (lambda c: c["sources"][0]["source_check"].update(retrieved="ayer"), "source_check.retrieved"),
    (lambda c: c["sources"][0]["source_check"].update(status="partially_supported", note=""),
     "source_check.note"),
    (lambda c: c.update(severity="SEVERE"), "invalid severity"),
    (lambda c: c.update(sources=[]), "legal source"),
    (lambda c: c["sources"][0].update(law="L0"), "not declared"),
    (lambda c: c["detection"].update(type="magic"), "invalid detection type"),
    (lambda c: c.pop("evidence"), "missing 'evidence'"),
    (lambda c: c.update(id="bad id"), "invalid id format"),
    (lambda c: c.update(requirement_type="law_of_nature"), "invalid requirement_type"),
    (lambda c: c.pop("applicability"), "missing 'applicability'"),
    (lambda c: c.update(legal_review="maybe"), "invalid legal_review"),
    (lambda c: c.update(validation_mode="vibes"), "invalid validation_mode"),
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
