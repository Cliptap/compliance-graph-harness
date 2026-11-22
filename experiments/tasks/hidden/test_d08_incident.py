from pathlib import Path


def test_incident_document_exists_and_names_the_leak():
    path = Path("INCIDENT.md")
    assert path.is_file(), "INCIDENT.md does not exist"
    text = path.read_text(encoding="utf-8", errors="replace")
    assert "RUT" in text, "the incident does not name the leaked data"
