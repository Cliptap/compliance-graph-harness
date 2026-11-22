"""Normative pack: law -> article -> control -> detection -> remediation -> evidence.

A pack is a single JSON document and the single source of normative truth. Every
control traces back to a legal source and declares:

* ``requirement_type``: legal_obligation | risk_based_measure | internal_standard
* ``applicability``: when the control applies
* ``validation_mode``: how it is verified
* ``legal_review``: pending | validated
* ``detection`` / ``remediation`` / ``evidence``

Every source carries a ``source_check`` (status, url, retrieved, note) recording whether a
public primary text supports the citation. It is separate from ``legal_review``: a verified
source does not validate the control's legal interpretation by itself.

``validated`` means self-validated against the primary legal text by the harness authors
(the pack's ``validation_method``): every source of the control is ``verified`` and a
``validation_note`` records the judgment of why the cited text supports exactly what the
control claims. It is never legal advice. The pack may be ``validated`` only when every
control is.

Each law declares a ``source_type`` (statute | guidance | contract, default statute). A
``legal_obligation`` needs at least one statute source; guidance or contracts alone never
make a control law.

``OUTCOMES`` are the allowed results of evaluating a control at runtime.
``to_legacy_document`` projects a pack onto the legacy ``compliance_rules.json``
shape so the DB loader, lineage scanner and auditor keep working unchanged.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

SEVERITIES = ("CRITICAL", "HIGH", "MEDIUM", "LOW")
DETECTION_TYPES = ("taint_sink", "pattern", "indicator", "manual")
REQUIREMENT_TYPES = ("legal_obligation", "risk_based_measure", "internal_standard")
VALIDATION_MODES = ("static_analysis", "integration_test", "document_review", "manual_assessment")
LEGAL_REVIEW = ("pending", "validated")
SOURCE_CHECK_STATUSES = ("verified", "partially_supported", "wrong_article", "not_found")
SOURCE_TYPES = ("statute", "guidance", "contract")
KNOWN_POLICY_IDS = frozenset({
    "privacy.cwe_532",
    "privacy.api_exposure",
    "privacy.payment_data_storage",
    "domain.prohibited_deletion",
    "privacy.rights_reachability",
    "privacy.consent_transparency",
    "privacy.minors_and_sensitive",
    "privacy.retention_minimization",
    "privacy.third_party_transfers",
})
ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
OUTCOMES = ("confirmed_violation", "potential_risk", "not_applicable", "insufficient_evidence")
CONTROL_ID = re.compile(r"^[A-Z]+(-[A-Z]+)*-\d{3}$")
REQUIRED_CONTROL_KEYS = (
    "id", "title", "description", "severity", "requirement_type", "applicability",
    "validation_mode", "legal_review", "sources", "detection", "remediation", "evidence",
)


class PackError(ValueError):
    """Raised when a pack violates the format."""


def load_pack(path: Path) -> dict:
    pack = json.loads(Path(path).read_text(encoding="utf-8"))
    validate_pack(pack)
    return pack


def _check_enum(errors: list[str], cid: str, control: dict, key: str, allowed: tuple[str, ...]) -> None:
    if key in control and control[key] not in allowed:
        errors.append(f"{cid}: invalid {key} {control[key]!r}")


def _check_source(errors: list[str], cid: str, src: dict) -> None:
    check = src.get("source_check")
    if not isinstance(check, dict):
        errors.append(f"{cid}: source without source_check")
        return
    if check.get("status") not in SOURCE_CHECK_STATUSES:
        errors.append(f"{cid}: invalid source_check status {check.get('status')!r}")
    if not str(check.get("url", "")).startswith("https://"):
        errors.append(f"{cid}: source_check.url must be an https URL")
    if not ISO_DATE.match(str(check.get("retrieved", ""))):
        errors.append(f"{cid}: source_check.retrieved must be an ISO date")
    if check.get("status") != "verified" and not str(check.get("note", "")).strip():
        errors.append(f"{cid}: source_check.note required unless verified")


def _check_self_validation(errors: list[str], cid: str, control: dict) -> None:
    if control.get("legal_review") != "validated":
        return
    if any(s.get("source_check", {}).get("status") != "verified" for s in control.get("sources", [])):
        errors.append(f"{cid}: validated control needs every source verified")
    if not str(control.get("validation_note", "")).strip():
        errors.append(f"{cid}: validated control needs a validation_note")


def _check_detector(errors: list[str], cid: str, det: dict) -> None:
    implemented = det.get("implemented")
    if not isinstance(implemented, bool):
        errors.append(f"{cid}: detection.implemented must be a boolean")
        return
    if implemented:
        if det.get("type") == "manual":
            errors.append(f"{cid}: manual control cannot declare a detector")
        if det.get("policy_id") not in KNOWN_POLICY_IDS:
            errors.append(f"{cid}: unknown detection.policy_id {det.get('policy_id')!r}")
    elif det.get("type") != "manual" and not str(det.get("gap_reason", "")).strip():
        errors.append(f"{cid}: non-manual control without a detector needs detection.gap_reason")


def _check_pack_review(errors: list[str], pack: dict) -> None:
    for key, law in pack.get("laws", {}).items():
        if law.get("source_type", "statute") not in SOURCE_TYPES:
            errors.append(f"law {key}: invalid source_type {law.get('source_type')!r}")
    if pack.get("legal_review") != "validated":
        return
    if any(c.get("legal_review") != "validated" for c in pack.get("controls", [])):
        errors.append("pack: pack legal_review validated requires every control validated")
    if not str(pack.get("validation_method", "")).strip():
        errors.append("pack: validated pack needs a validation_method")


def validate_pack(pack: dict) -> None:
    errors: list[str] = []
    for key in ("pack_id", "version", "jurisdiction", "laws", "controls"):
        if key not in pack:
            errors.append(f"pack: missing '{key}'")
    laws = pack.get("laws", {})
    _check_pack_review(errors, pack)
    seen: set[str] = set()
    for control in pack.get("controls", []):
        cid = control.get("id", "<no id>")
        for key in REQUIRED_CONTROL_KEYS:
            if key not in control:
                errors.append(f"{cid}: missing '{key}'")
        if cid in seen:
            errors.append(f"{cid}: duplicate id")
        seen.add(cid)
        if not CONTROL_ID.match(cid):
            errors.append(f"{cid}: invalid id format")
        _check_enum(errors, cid, control, "severity", SEVERITIES)
        _check_enum(errors, cid, control, "requirement_type", REQUIREMENT_TYPES)
        _check_enum(errors, cid, control, "validation_mode", VALIDATION_MODES)
        _check_enum(errors, cid, control, "legal_review", LEGAL_REVIEW)
        if control.get("requirement_type") == "legal_obligation" and not control.get("sources"):
            errors.append(f"{cid}: legal_obligation needs at least one legal source")
        elif control.get("requirement_type") == "legal_obligation" and not any(
                laws.get(s.get("law"), {}).get("source_type", "statute") == "statute"
                for s in control.get("sources", [])):
            errors.append(f"{cid}: legal_obligation needs a statute source")
        _check_self_validation(errors, cid, control)
        if not control.get("sources") and control.get("requirement_type") != "internal_standard":
            errors.append(f"{cid}: needs at least one legal source")
        for src in control.get("sources", []):
            if src.get("law") not in laws:
                errors.append(f"{cid}: source law {src.get('law')!r} not declared in 'laws'")
            if not src.get("article"):
                errors.append(f"{cid}: source without article")
            _check_source(errors, cid, src)
        det = control.get("detection", {})
        if det.get("type") not in DETECTION_TYPES:
            errors.append(f"{cid}: invalid detection type {det.get('type')!r}")
        _check_detector(errors, cid, det)
        if det.get("type") == "taint_sink" and not (det.get("sinks") and det.get("sensitive_category")):
            errors.append(f"{cid}: taint_sink needs sinks and sensitive_category")
        if det.get("type") == "pattern" and not det.get("patterns"):
            errors.append(f"{cid}: pattern detection needs patterns")
        if det.get("type") == "indicator" and not det.get("indicators"):
            errors.append(f"{cid}: indicator detection needs indicators")
        if not control.get("remediation", {}).get("mitigations") and det.get("type") != "manual":
            errors.append(f"{cid}: automated control needs remediation.mitigations")
        if not control.get("evidence", {}).get("kind"):
            errors.append(f"{cid}: evidence.kind required")
        if not str(control.get("applicability", {}).get("when", "")).strip():
            errors.append(f"{cid}: applicability.when required")
    if errors:
        raise PackError("; ".join(errors))


def _citation(control: dict) -> str:
    return "; ".join(s["citation"] for s in control["sources"])


def to_legacy_rules(pack: dict) -> list[dict]:
    """Project taint_sink controls onto the legacy ``rules`` list shape."""
    rules = []
    for c in pack["controls"]:
        det = c["detection"]
        if det["type"] != "taint_sink":
            continue
        rules.append({
            "rule_id": c["id"],
            "semgrep_id": det.get("semgrep_id", ""),
            "law_article": _citation(c),
            "title": c["title"],
            "description": c["description"],
            "cwe": det.get("cwe", ""),
            "sensitive_category": det["sensitive_category"],
            "prohibited_sinks": list(det["sinks"]),
            "required_mitigations": list(c["remediation"]["mitigations"]),
            "severity": c["severity"],
        })
    return rules


def _criterion(c: dict) -> dict:
    det = c["detection"]
    item = {"id": c["id"], "category": det.get("category", ""), "law_article": _citation(c),
            "title": c["title"], "description": c["description"], "severity": c["severity"],
            "detection_type": det["type"], "evidence_kind": c["evidence"]["kind"]}
    if det["type"] == "pattern":
        item["prohibited_patterns"] = list(det["patterns"])
    else:
        item["indicators"] = list(det.get("indicators", []))
    return item


def to_legacy_document(pack: dict) -> dict:
    """Legacy ``compliance_rules.json`` shape: rules, core_checklist, sectorial_plugins, data_categories."""
    core, plugins = [], {}
    for c in pack["controls"]:
        det = c["detection"]
        if det["type"] == "taint_sink":
            continue
        plugin = det.get("plugin", "core")
        if plugin == "core":
            core.append(_criterion(c))
        else:
            meta = pack.get("plugins", {}).get(plugin, {})
            entry = plugins.setdefault(plugin, {"name": meta.get("name", plugin),
                                                "description": meta.get("description", ""), "criteria": []})
            entry["criteria"].append(_criterion(c))
    return {
        "jurisdiction": pack["jurisdiction"], "version": pack["version"],
        "enforcement_date": pack.get("enforcement_date", ""),
        "data_categories": pack.get("data_categories", {}),
        "rules": to_legacy_rules(pack), "core_checklist": core, "sectorial_plugins": plugins,
    }


def load_legacy_view(path: Path) -> dict:
    """Load a pack (validated) and return the legacy-shaped document consumers expect."""
    return to_legacy_document(load_pack(path))
