from pathlib import Path


def test_crm_sync_code_references_the_crm_host():
    text = "\n".join(
        path.read_text(encoding="utf-8", errors="replace")
        for path in Path("app").rglob("*.py")
    )
    assert "crm.example-store.com" in text, "no code references the CRM host"
