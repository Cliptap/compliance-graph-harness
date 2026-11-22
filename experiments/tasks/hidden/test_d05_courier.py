from pathlib import Path


def test_courier_code_references_the_courier_host():
    text = "\n".join(
        path.read_text(encoding="utf-8", errors="replace")
        for path in Path("app").rglob("*.py")
    )
    assert "courier.example-store.com" in text, "no code references the courier host"
