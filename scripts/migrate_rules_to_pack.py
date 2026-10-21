"""One-off migration: .harness/compliance_rules.json -> .harness/packs/cl-ley-21719.json."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.harness.normative_pack import validate_pack  # noqa: E402

LAWS = {
    "L19628": {"name": "Ley 19.628 (reformada por Ley 21.719)", "short": "Ley 21.719"},
    "L20584": {"name": "Ley 20.584 (derechos y deberes del paciente)", "short": "Ley 20.584"},
    "L21668": {"name": "Ley 21.668 (interoperabilidad de fichas clÃ­nicas)", "short": "Ley 21.668"},
}


def sources_from(text: str) -> list[dict]:
    """Best-effort split of a free-text citation into (law, article) pairs."""
    out = []
    for part in re.split(r";", text):
        part = part.strip()
        if not part:
            continue
        if "20.584" in part and "21.719" not in part:
            law = "L20584"
        elif "21.668" in part and "21.719" not in part and "19.628" not in part:
            law = "L21668"
        else:
            law = "L19628"
        art = re.findall(r"Art\.?\s*\d+[Â°Âº]?(?:\s*(?:bis|ter|quÃ¡ter|quinquies))?(?:\s*(?:let\.|inc\.|NÂ°)\s*[\w)]+)?", part)
        out.append({"law": law, "article": ", ".join(a.strip() for a in art) or part, "citation": part})
    return out


def criterion_to_control(c: dict, plugin: str) -> dict:
    base = {"category": c["category"], "plugin": plugin}
    if "prohibited_patterns" in c:
        detection = {"type": "pattern", **base, "patterns": c["prohibited_patterns"]}
        evidence = {"kind": "pattern_absent", "note": "Prohibited patterns absent from the changed code."}
        mitigations = (["soft_delete_filter", "status = BLOCKED_LEGAL_HOLD"]
                       if "RETENTION" in c["category"] else ["review:" + c["category"]])
    else:
        detection = {"type": "indicator", **base, "indicators": c["indicators"]}
        evidence = {"kind": "code_indicator_present", "note": "Indicators found in the changed code."}
        mitigations = [f"apply:{i}" for i in c["indicators"]]
    return {
        "id": c["id"], "title": c["title"], "description": c["description"],
        "severity": c["severity"], "sources": sources_from(c["law_article"]),
        "detection": detection, "remediation": {"mitigations": mitigations}, "evidence": evidence,
    }


def main() -> None:
    d = json.loads((ROOT / ".harness" / "compliance_rules.json").read_text(encoding="utf-8"))
    controls = []
    for r in d["rules"]:
        controls.append({
            "id": r["rule_id"], "title": r["title"], "description": r["description"],
            "severity": r["severity"], "sources": sources_from(r["law_article"]),
            "detection": {"type": "taint_sink", "semgrep_id": r["semgrep_id"], "cwe": r["cwe"],
                          "sensitive_category": r["sensitive_category"], "sinks": r["prohibited_sinks"]},
            "remediation": {"mitigations": r["required_mitigations"]},
            "evidence": {"kind": "scan_finding_absent", "note": "No open finding for this control in the compliance scan."},
        })
    for plugin_id, items in [("core", d["core_checklist"])] + [
        (pid, p["criteria"]) for pid, p in d["sectorial_plugins"].items()
    ]:
        for c in items:
            controls.append(criterion_to_control(c, plugin_id))
    pack = {
        "pack_id": "cl-ley-21719", "version": d["version"], "jurisdiction": d["jurisdiction"],
        "enforcement_date": d["enforcement_date"], "laws": LAWS,
        "sanctions": d["sanctions"], "data_categories": d["data_categories"], "controls": controls,
    }
    validate_pack(pack)
    out = ROOT / ".harness" / "packs" / "cl-ley-21719.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(pack, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{len(controls)} controls -> {out}")


if __name__ == "__main__":
    main()
