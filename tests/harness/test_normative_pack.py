import copy
import hashlib
import json
import re
from pathlib import Path

import pytest

from src.harness.normative_pack import (
    LEGAL_REVIEW, OUTCOMES, SOURCE_CHECK_STATUSES, PackError, load_legacy_view, load_pack,
    to_legacy_rules, validate_pack,
)

ROOT = Path(__file__).resolve().parents[2]
PACK = ROOT / ".harness" / "packs" / "cl-ley-21719.json"
VALIDATION_METHOD = ("Self-validation against primary legal texts (BCN LeyChile, Diario Oficial) "
                     "by the harness authors; not legal advice.")
ORIGINAL_IDS = (
    "CL-DATAPROT-001", "CL-DATAPROT-002", "CL-DATAPROT-003", "CL-DATAPROT-004", "CL-DATAPROT-005",
    "CL-DATAPROT-006", "CL-DATAPROT-007", "CORE-CHECK-001", "CORE-CHECK-002", "CORE-CHECK-003",
    "CORE-CHECK-004", "HEALTH-CHECK-001", "HEALTH-CHECK-002", "HEALTH-CHECK-003",
)
NEW_CORE_IDS = tuple(f"CORE-CHECK-{n:03d}" for n in range(5, 14))
ECOM_IDS = tuple(f"ECOM-CHECK-{n:03d}" for n in range(1, 8))


def _controls() -> dict[str, dict]:
    return {c["id"]: c for c in load_pack(PACK)["controls"]}


def _articles(control: dict) -> set[str]:
    return {f"{s['law']}:{s['article']}" for s in control["sources"]}


def _validated_copy() -> dict:
    return copy.deepcopy(load_pack(PACK))


def test_shipped_pack_is_valid_and_complete():
    ids = [c["id"] for c in load_pack(PACK)["controls"]]
    assert len(ids) == 30
    assert set(ORIGINAL_IDS) | set(NEW_CORE_IDS) | set(ECOM_IDS) == set(ids)


def test_every_control_is_self_validated():
    pack = load_pack(PACK)
    assert pack["legal_review"] == "validated"
    assert pack["validation_method"] == VALIDATION_METHOD
    for c in pack["controls"]:
        assert c["legal_review"] == "validated", c["id"]
        assert c["validation_note"].strip(), c["id"]
        assert all(s["source_check"]["status"] == "verified" for s in c["sources"]), c["id"]


def test_validated_control_needs_every_source_verified():
    pack = _validated_copy()
    pack["controls"][0]["sources"][0]["source_check"].update(status="partially_supported", note="overstated")
    with pytest.raises(PackError, match="validated control needs every source verified"):
        validate_pack(pack)


def test_validated_control_needs_validation_note():
    pack = _validated_copy()
    pack["controls"][0]["validation_note"] = "  "
    with pytest.raises(PackError, match="validated control needs a validation_note"):
        validate_pack(pack)


def test_pack_is_validated_only_when_every_control_is():
    pack = _validated_copy()
    pack["controls"][0]["legal_review"] = "pending"
    with pytest.raises(PackError, match="pack legal_review validated requires every control validated"):
        validate_pack(pack)


def test_validated_pack_declares_validation_method():
    pack = _validated_copy()
    pack.pop("validation_method")
    with pytest.raises(PackError, match="validation_method"):
        validate_pack(pack)


def test_pending_control_may_keep_partial_sources():
    pack = _validated_copy()
    pack["legal_review"] = "pending"
    control = pack["controls"][0]
    control["legal_review"] = "pending"
    control.pop("validation_note")
    control["sources"][0]["source_check"].update(status="partially_supported", note="overstated")
    validate_pack(pack)


def test_existing_detection_and_remediation_are_unchanged():
    by_id = _controls()
    fingerprint = {cid: [by_id[cid]["severity"], by_id[cid]["detection"], by_id[cid]["remediation"]]
                   for cid in ORIGINAL_IDS}
    digest = hashlib.sha256(json.dumps(fingerprint, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    assert digest == "e4a247ce7497264291483e5289b8bf7e7f2b2c3b988023fb29cd86ceb29a59ab"


@pytest.mark.parametrize("cid,absent,present", [
    ("CL-DATAPROT-001", ["Prohibición absoluta"], ["según el riesgo", "dato sensible"]),
    ("CORE-CHECK-002", ["Prohibición perentoria"], ["secreto", "según el riesgo"]),
    ("CORE-CHECK-001", ["Obligación"], ["en su caso", "riesgo"]),
    ("CL-DATAPROT-004", ["Prohibición perentoria"], ["15 años", "no afectará el almacenamiento"]),
    ("HEALTH-CHECK-001", ["Legal Hold", "Prohibición absoluta"], ["15 años", "no afectará el almacenamiento"]),
    ("CL-DATAPROT-006", ["no pueden ser resolutivos"], ["oponerse", "intervención humana", "revisión"]),
    ("CORE-CHECK-004", ["no pueden ser exclusivamente automatizados"],
     ["oponerse", "intervención humana", "revisión"]),
    ("CL-DATAPROT-007", ["debe exportar"], ["decisión del proyecto", "automatizada", "consentimiento"]),
    ("HEALTH-CHECK-002", ["obligatoriamente", "Universal"], ["decisión del proyecto", "no fija un estándar"]),
    ("CORE-CHECK-003", ["Cancelación"], ["portabilidad", "bloqueo", "según el riesgo"]),
])
def test_overstated_claims_match_the_text(cid, absent, present):
    control = _controls()[cid]
    text = f"{control['title']} {control['description']}"
    for phrase in absent:
        assert phrase not in text, (cid, phrase)
    for phrase in present:
        assert phrase in text, (cid, phrase)


def test_internal_standards_say_they_are_a_project_choice():
    for c in _controls().values():
        if c["requirement_type"] == "internal_standard":
            assert "decisión del proyecto" in c["description"], c["id"]


@pytest.mark.parametrize("cid,articles,phrases,validation_mode", [
    ("CORE-CHECK-005", ["L19628:Art. 12°", "L19628:Art. 13°", "L19628:Art. 2° let. p)"],
     ["libre, informado y específico", "medios similares o equivalentes", "no ha sido libremente otorgado"],
     "manual_assessment"),
    ("CORE-CHECK-006", ["L19628:Arts. 4° al 11°"],
     ["treinta días corridos", "por una sola vez", "dos días hábiles"], "manual_assessment"),
    ("CORE-CHECK-007", ["L19628:Art. 14° ter", "L19628:Art. 3° let. g)"],
     ["base de legitimidad", "decisiones automatizadas"], "document_review"),
    ("CORE-CHECK-008", ["L19628:Art. 14° sexies"],
     ["sin dilaciones indebidas", "registrar", "menores de catorce años",
      "económico, financiero, bancario o comercial"], "document_review"),
    ("CORE-CHECK-009", ["L19628:Art. 15° ter"], ["alto riesgo", "previo al inicio", "elaboración de perfiles"],
     "document_review"),
    ("CORE-CHECK-010", ["L19628:Art. 15° bis", "L19628:Art. 15°"],
     ["objeto del encargo", "autorización específica y por escrito", "suprimidos o devueltos"],
     "document_review"),
    ("CORE-CHECK-011", ["L19628:Art. 27°", "L19628:Art. 28°"],
     ["cláusulas contractuales", "países adecuados"], "document_review"),
    ("CORE-CHECK-012", ["L19628:Art. 16° quáter"],
     ["interés superior", "menores de catorce años", "menores de dieciséis años"], "manual_assessment"),
    ("CORE-CHECK-013", ["L19628:Art. 3° let. b)", "L19628:Art. 3° let. c)", "L19628:Art. 14° let. d)",
                        "L19628:Art. 7° inc. 2° N° ii"],
     ["necesario para cumplir con los fines", "suprimidos o anonimizados"], "document_review"),
])
def test_core_dimension_control(cid, articles, phrases, validation_mode):
    control = _controls()[cid]
    assert control["detection"] == {"type": "manual", "category": control["detection"]["category"],
                                    "plugin": "core"}
    assert control["validation_mode"] == validation_mode
    assert control["evidence"]["kind"] in ("document_present", "procedure_documented")
    assert control["requirement_type"] == "legal_obligation"
    cited = _articles(control)
    for article in articles:
        assert article in cited, (cid, article)
    for phrase in phrases:
        assert phrase in control["description"], (cid, phrase)


def test_breach_control_sets_no_fixed_hour_deadline():
    text = json.dumps(_controls()["CORE-CHECK-008"], ensure_ascii=False)
    assert not re.search(r"\b\d+\s*(h|horas|hours)\b", text)


LEGAL_SENSITIVE_CATEGORIES = (
    "SENSITIVE_ETHNIC_RACIAL_ORIGIN", "SENSITIVE_POLITICAL_UNION_AFFILIATION", "SENSITIVE_BELIEFS",
    "SENSITIVE_SOCIOECONOMIC", "SENSITIVE_SEXUAL_LIFE_ORIENTATION", "SENSITIVE_GENDER_IDENTITY",
    "SENSITIVE_BIOLOGICAL_PROFILE",
)
GENERIC_FIELD_NAMES = {"status", "gender", "sex", "race", "age", "birth_date", "birthdate", "ingreso",
                       "type", "state", "name", "income_type", "score"}


def test_legal_sensitive_categories_are_declared():
    categories = load_pack(PACK)["data_categories"]
    for key in LEGAL_SENSITIVE_CATEGORIES:
        assert "Art. 2° let. g)" in categories[key]["legal_basis"], key
        assert categories[key]["fields"], key
    assert "Art. 16° quáter" in categories["CHILDREN_DATA"]["legal_basis"]
    new_fields = {f for key in (*LEGAL_SENSITIVE_CATEGORIES, "CHILDREN_DATA") for f in categories[key]["fields"]}
    assert not new_fields & GENERIC_FIELD_NAMES


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
    assert len(view["rules"]) == 7 and len(view["core_checklist"]) == 13
    assert len(view["sectorial_plugins"]["health_clinical"]["criteria"]) == 3
    assert [c["id"] for c in view["sectorial_plugins"]["ecommerce_retail"]["criteria"]] == list(ECOM_IDS)
    manual = {c["id"]: c for c in view["core_checklist"] if c["detection_type"] == "manual"}
    assert set(manual) == set(NEW_CORE_IDS)
    assert manual["CORE-CHECK-008"]["evidence_kind"] in ("document_present", "procedure_documented")
    assert all(c["detection_type"] in ("pattern", "indicator") for c in view["core_checklist"]
               if c["id"] not in NEW_CORE_IDS)
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
    pack = _validated_copy()
    pack["legal_review"] = "pending"
    control = pack["controls"][0]
    control["legal_review"] = "pending"
    control.pop("validation_note")
    assert all(s["source_check"]["status"] == "verified" for s in control["sources"])
    validate_pack(pack)


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
    assert not any(re.search(r"Art\. 14°(?! (bis|ter|quáter|quinquies|sexies|let\. d\)))", s["article"])
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


@pytest.mark.parametrize("cid,articles,phrases,requirement_type,validation_mode", [
    ("ECOM-CHECK-001", ["L19496:Art. 28 B", "L19628:Art. 12°", "L19628:Art. 13°", "L19628:Art. 8° let. b)"],
     ["la identidad del remitente", "suspensión de los envíos", "oponerse"],
     "legal_obligation", "manual_assessment"),
    ("ECOM-CHECK-002", ["L19628:Art. 8° bis", "L19628:Art. 8° let. b)", "L19628:Art. 15° ter",
                        "L19628:Art. 2° let. w)", "L19628:Art. 14° ter let. l)"],
     ["elaboración de perfiles", "intervención humana", "evaluación de impacto"],
     "legal_obligation", "manual_assessment"),
    ("ECOM-CHECK-003", ["L19628:Art. 14° bis", "L19628:Art. 14° quinquies", "L19628:Art. 14° sexies"],
     ["secreto", "adecuado al riesgo", "económico, financiero, bancario o comercial"],
     "legal_obligation", "manual_assessment"),
    ("ECOM-CHECK-004", ["TBK_AFILIACION:Cláusula 10.9", "L19628:Art. 14° quinquies"],
     ["PCI DSS", "contrato de afiliación", "no es una obligación legal"],
     "internal_standard", "document_review"),
    ("ECOM-CHECK-005", ["L19628:Art. 15° bis", "L19628:Art. 15°"],
     ["pasarelas de pago", "objeto del encargo", "cesión"],
     "legal_obligation", "document_review"),
    ("ECOM-CHECK-006", ["DL825:Art. 58", "DL830:Art. 17", "DL830:Art. 200", "L19628:Art. 7° inc. 2° N° ii",
                        "L19628:Art. 3° let. c)"],
     ["seis años", "obligación legal", "suprimidos o anonimizados"],
     "legal_obligation", "document_review"),
    ("ECOM-CHECK-007", ["L19628:Art. 2° let. g)", "L19628:Art. 16°"],
     ["la situación socioeconómica", "en forma expresa"],
     "legal_obligation", "manual_assessment"),
])
def test_ecommerce_control(cid, articles, phrases, requirement_type, validation_mode):
    control = _controls()[cid]
    assert control["detection"]["type"] == "manual"
    assert control["detection"]["plugin"] == "ecommerce_retail"
    assert control["requirement_type"] == requirement_type
    assert control["validation_mode"] == validation_mode
    assert control["evidence"]["kind"] in ("document_present", "procedure_documented")
    assert articles and set(articles) <= _articles(control), (cid, _articles(control))
    for phrase in phrases:
        assert phrase in control["description"], (cid, phrase)


def test_ecommerce_plugin_and_laws_are_declared():
    pack = load_pack(PACK)
    assert set(pack["plugins"]) == {"health_clinical", "ecommerce_retail"}
    laws = pack["laws"]
    expected = {"L19496": "statute", "DL825": "statute", "DL830": "statute", "TBK_AFILIACION": "contract"}
    for key, source_type in expected.items():
        assert laws[key]["url"].startswith("https://"), key
        assert laws[key]["source_type"] == source_type, key
    assert all(law.get("source_type", "statute") == "statute"
               for key, law in laws.items() if key in ("L19628", "L20584", "L21668"))


def test_pci_dss_is_never_presented_as_law():
    for c in _controls().values():
        if c["requirement_type"] != "internal_standard":
            assert "PCI" not in f"{c['title']} {c['description']}", c["id"]
    assert _controls()["ECOM-CHECK-004"]["requirement_type"] == "internal_standard"


def test_legal_obligation_needs_a_statute_source():
    pack = _validated_copy()
    control = next(c for c in pack["controls"] if c["id"] == "ECOM-CHECK-001")
    for src in control["sources"]:
        src["law"] = "TBK_AFILIACION"
    with pytest.raises(PackError, match="legal_obligation needs a statute source"):
        validate_pack(pack)


def test_invalid_law_source_type_is_rejected():
    pack = _validated_copy()
    pack["laws"]["L19496"]["source_type"] = "rumour"
    with pytest.raises(PackError, match="invalid source_type"):
        validate_pack(pack)
