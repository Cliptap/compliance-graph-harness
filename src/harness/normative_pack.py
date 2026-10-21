"""Normative pack: law -> article -> control -> detection -> remediation -> evidence.

A pack is a single JSON document. Every control traces back to a legal source
and declares how it is detected, how it is remediated and what evidence proves
compliance. `to_legacy_rules` projects a pack onto the legacy
``compliance_rules.json`` rule shape so existing consumers keep working.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

SEVERITIES = ("CRITICAL", "HIGH", "MEDIUM", "LOW")
DETECTION_TYPES = ("taint_sink", "pattern", "indicator", "manual")
CONTROL_ID = re.compile(r"^[A-Z]+(-[A-Z]+)*-\d{3}$")
REQUIRED_CONTROL_KEYS = ("id", "title", "description", "severity", "sources", "detection", "remediation", "evidence")


class PackError(ValueError):
    """Raised when a pack violates the format."""


def load_pack(path: Path) -> dict:
    pack = json.loads(Path(path).read_text(encoding="utf-8"))
    validate_pack(pack)
    return pack


def validate_pack(pack: dict) -> None:
    errors: list[str] = []
    for key in ("pack_id", "version", "jurisdiction", "laws", "controls"):
        if key not in pack:
            errors.append(f"pack: missing '{key}'")
    laws = pack.get("laws", {})
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
        if control.get("severity") not in SEVERITIES:
            errors.append(f"{cid}: invalid severity {control.get('severity')!r}")
        if not control.get("sources"):
            errors.append(f"{cid}: needs at least one legal source")
        for src in control.get("sources", []):
            if src.get("law") not in laws:
                errors.append(f"{cid}: source law {src.get('law')!r} not declared in 'laws'")
            if not src.get("article"):
                errors.append(f"{cid}: source without article")
        det = control.get("detection", {})
        if det.get("type") not in DETECTION_TYPES:
            errors.append(f"{cid}: invalid detection type {det.get('type')!r}")
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
    if errors:
        raise PackError("; ".join(errors))


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
            "law_article": "; ".join(s["citation"] for s in c["sources"]),
            "title": c["title"],
            "description": c["description"],
            "cwe": det.get("cwe", ""),
            "sensitive_category": det["sensitive_category"],
            "prohibited_sinks": list(det["sinks"]),
            "required_mitigations": list(c["remediation"]["mitigations"]),
            "severity": c["severity"],
        })
    return rules
