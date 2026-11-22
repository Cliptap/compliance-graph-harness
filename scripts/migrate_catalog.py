"""Migrate the law-specific pack into the multi-framework catalog v2.

Implemented controls keep their coverage through a legacy adapter during the
migration. Controls without a v2 family are copied as declared gaps, so the
catalog never hides what it cannot detect.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

OLD = Path(".harness/packs/cl-ley-21719.json")
V2 = Path(".harness/packs/catalog.v2.json")
OUT = Path(".harness/packs/catalog.full.json")

LAW_NAMES = {
    "L19628": "Ley 19.628",
    "L20584": "Ley 20.584",
    "L21668": "Ley 21.668",
    "L19496": "Ley 19.496",
    "DL825": "DL 825",
    "DL830": "DL 830",
    "TBK_AFILIACION": "Código Tributario",
}

CWE_ISO = {
    "CWE-532": ("A.8.12", "Data leakage prevention"),
    "CWE-200": ("A.8.12", "Data leakage prevention"),
    "CWE-311": ("A.8.24", "Use of cryptography"),
    "CWE-312": ("A.8.24", "Use of cryptography"),
    "CWE-522": ("A.8.24", "Use of cryptography"),
    "CWE-798": ("A.8.24", "Use of cryptography"),
    "CWE-404": ("A.8.10", "Information deletion"),
    "CWE-285": ("A.8.3", "Information access restriction"),
    "CWE-693": ("A.8.28", "Secure coding"),
    "CWE-20": ("A.8.28", "Secure coding"),
}

CATEGORY_SYNONYMS = {
    "SENSITIVE_HEALTH": ["diagnosis", "diagnostico", "clinical_notes", "medical_record"],
    "SENSITIVE_BIOMETRIC": ["biometric", "fingerprint", "huella", "iris", "face"],
    "IDENTIFIER_RUT": ["rut", "run", "national_id", "dni"],
    "PERSONAL_CONTACT": ["email", "correo", "phone", "telefono", "address", "direccion"],
    "SECURITY_METADATA": ["ip", "user_agent", "metadata", "log"],
    "SENSITIVE_ETHNIC_RACIAL_ORIGIN": ["ethnic", "racial", "etnia", "raza"],
    "SENSITIVE_POLITICAL_UNION_AFFILIATION": ["political", "union", "sindicato", "partido"],
    "SENSITIVE_BELIEFS": ["belief", "religion", "creencia"],
    "SENSITIVE_SOCIOECONOMIC": ["income", "socioeconomic", "ingreso"],
    "SENSITIVE_SEXUAL_LIFE_ORIENTATION": ["sexual", "orientation"],
    "SENSITIVE_GENDER_IDENTITY": ["gender", "identidad_genero"],
    "SENSITIVE_BIOLOGICAL_PROFILE": ["biological", "genetic", "genetico"],
    "CHILDREN_DATA": ["minor", "children", "menor", "birth_date"],
    "PERSONAL_DATA": ["personal_data", "customer", "user", "client"],
}

CATEGORY_INFER = {
    "ECOM-CHECK-003": "PAYMENT",
    "CORE-CHECK-012": "CHILDREN_DATA",
    "ECOM-CHECK-007": "CHILDREN_DATA",
    "HEALTH-CHECK-001": "SENSITIVE_HEALTH",
    "HEALTH-CHECK-002": "SENSITIVE_HEALTH",
    "HEALTH-CHECK-003": "SENSITIVE_HEALTH",
}


def _frameworks(control: dict, cwe: str | None) -> list[dict]:
    refs: list[dict] = []
    seen: set[tuple[str, str]] = set()
    for source in control.get("sources", []):
        framework = LAW_NAMES.get(source.get("law", ""), source.get("law", ""))
        ref = source.get("article", "")
        if framework and (framework, ref) not in seen:
            seen.add((framework, ref))
            refs.append({"framework": framework, "ref": ref})
    if cwe:
        refs.append({"framework": "CWE", "ref": cwe})
        iso = CWE_ISO.get(cwe)
        if iso:
            refs.append({"framework": "ISO/IEC 27001:2022", "ref": iso[0], "title": iso[1]})
    if not refs:
        refs.append({"framework": "ISO/IEC 27001:2022", "ref": "A.5.34", "title": "Privacy and protection of PII"})
    return refs


def _category(control: dict) -> str:
    detection = control.get("detection", {})
    category = detection.get("sensitive_category")
    if category and category in CATEGORY_SYNONYMS:
        return category
    return CATEGORY_INFER.get(control["id"], "PERSONAL_DATA")


def _remediation(control: dict) -> str:
    value = control.get("remediation", "")
    if isinstance(value, str) and value.strip():
        return value.strip()
    if isinstance(value, dict):
        return value.get("summary") or value.get("description") or "Remediate the finding."
    return "Remediate the finding according to the mapped control."


def _cwe(control: dict) -> str | None:
    match = re.search(r"CWE-\d+", str(control.get("detection", {}).get("cwe", "")))
    return match.group(0) if match else None


def main() -> int:
    old = json.loads(OLD.read_text(encoding="utf-8"))
    v2 = json.loads(V2.read_text(encoding="utf-8"))
    frameworks = dict(v2["frameworks"])
    for code in old.get("laws", {}):
        frameworks.setdefault(LAW_NAMES.get(code, code), {"kind": "law"})
    data_categories = dict(v2["data_categories"])
    for name in CATEGORY_SYNONYMS:
        data_categories.setdefault(name, {"sensitivity": "medium", "synonyms": CATEGORY_SYNONYMS[name]})

    controls: list[dict] = []
    for control in old["controls"]:
        detection = control.get("detection", {})
        cwe = _cwe(control)
        replaced = control["id"] == "CL-DATAPROT-001"
        implemented = bool(detection.get("implemented")) and not replaced
        entry = {
            "id": control["id"],
            "pack_control": control["id"],
            "title": control.get("title", control["id"]),
            "frameworks": _frameworks(control, cwe),
            "data_categories": [_category(control)],
            "detection": {
                "policy": "legacy",
                "params": {"legacy_policy": detection.get("policy_id") or ""},
            },
            "severity": control.get("severity", "MEDIUM"),
            "remediation": _remediation(control),
            "implemented": implemented,
        }
        if not implemented:
            entry["gap_reason"] = (
                "replaced by v2.log_pii" if replaced
                else detection.get("gap_reason") or "manual or indicator control without a v2 family"
            )
        controls.append(entry)

    controls.extend(v2["controls"])
    out = {
        **v2,
        "generated_by": "scripts/migrate_catalog.py",
        "frameworks": frameworks,
        "data_categories": data_categories,
        "controls": controls,
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    implemented = sum(1 for control in controls if control["implemented"])
    print(f"wrote {OUT}: {len(controls)} controls ({implemented} implemented, {len(controls)-implemented} gaps)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
