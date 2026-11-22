import re
from pathlib import Path

import pytest
import yaml

from src.harness.normative_pack import load_pack

ROOT = Path(__file__).resolve().parents[2]
SKILLS = ("compliance-dev", "compliance-audit", "compliance-patch")
PACK = load_pack(ROOT / ".harness" / "packs" / "cl-ley-21719.json")
CONTROL_IDS = {c["id"] for c in PACK["controls"]}


def text(skill: str) -> str:
    return (ROOT / ".agents" / "skills" / skill / "SKILL.md").read_text(encoding="utf-8")


@pytest.mark.parametrize("skill", SKILLS)
def test_frontmatter_is_valid(skill):
    _, fm, _ = text(skill).split("---", 2)
    meta = yaml.safe_load(fm)
    assert meta["name"] == skill and len(meta["description"]) > 40


@pytest.mark.parametrize("skill", SKILLS)
def test_every_control_id_mentioned_exists_in_the_pack(skill):
    mentioned = set(re.findall(r"\b(?:CORE|ECOM|HEALTH|CL)-[A-Z]*-?\w*?-\d{3}\b", text(skill)))
    assert mentioned <= CONTROL_IDS, mentioned - CONTROL_IDS


@pytest.mark.parametrize("skill", SKILLS)
def test_validation_state_is_described_as_self_validation_not_legal_advice(skill):
    body = text(skill).lower()
    assert "autovalid" in body and "asesoria legal" in body
    assert "legal_review: pending" not in body


def test_audit_covers_documentary_dimensions_and_ecommerce_plugin():
    body = text("compliance-audit")
    for cid in ("CORE-CHECK-005", "CORE-CHECK-008", "CORE-CHECK-012", "ECOM-CHECK-003"):
        assert cid in body
    assert "ecommerce_retail" in body and "insufficient_evidence" in body


def test_dev_and_patch_know_the_commit_gate_and_the_card_detector():
    for skill in ("compliance-dev", "compliance-patch"):
        assert "src.harness.precommit" in text(skill)
    assert "privacy.payment_data_storage" in text("compliance-dev")


def test_every_manual_control_family_has_an_evidence_hint_in_the_audit_skill():
    manual = sorted(c["id"] for c in PACK["controls"] if c["detection"]["type"] == "manual")
    body = text("compliance-audit")
    assert manual and all(cid in body for cid in manual)
