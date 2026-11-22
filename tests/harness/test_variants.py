import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "experiments" / "variants" / "manifest.json"


def test_variant_manifest_self_check():
    result = subprocess.run([sys.executable, "experiments/variants/build.py"], cwd=ROOT,
                            capture_output=True, text=True, timeout=300)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "failures=0" in result.stdout


def test_manifest_has_seeded_and_clean_variants():
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    kinds = {variant["kind"] for variant in data["variants"]}
    assert kinds == {"seeded", "clean"}
    assert len(data["variants"]) >= 12
    ids = [variant["id"] for variant in data["variants"]]
    assert len(ids) == len(set(ids))
    for variant in data["variants"]:
        if variant["kind"] == "clean":
            assert variant["expected"] == [], variant["id"]
        else:
            assert variant["expected"], variant["id"]
