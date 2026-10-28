from pathlib import Path

from harness.eval.corpus import TARGETS, load_cases, score
from src.harness.contracts import TaskSpec
from src.harness.normative_pack import load_legacy_view, load_pack
from src.harness.payment_policy import PaymentDataStoragePolicy
from src.harness.policy_engine import PolicyEngine
from src.harness.precommit import POLICY_CONTROLS, evaluate

ROOT = Path(__file__).resolve().parents[2]
PACK = ROOT / ".harness" / "packs" / "cl-ley-21719.json"
SPEC = TaskSpec(task_id="t", goal="t", allowed_paths=["*"])
ORM = "from sqlalchemy import Column\n\nclass P(Base):\n    __tablename__ = 'p'\n    {field}\n"


def run(code: str, path: str = "src/shop/models.py"):
    return PaymentDataStoragePolicy().evaluate(SPEC, {path: code})


def test_persisted_card_number_is_flagged_with_line_and_advice():
    [f] = run(ORM.format(field="card_number = Column(String(19))"))
    assert (f.policy_id, f.status, f.severity, f.file, f.line) == ("privacy.payment_data_storage", "VIOLATION", "HIGH", "src/shop/models.py", 5)
    assert "card_number" in f.message and f.remediation_advice


def test_cvv_is_flagged_even_when_encrypted():
    assert len(run(ORM.format(field="cvv = Column(EncryptedType(String, key))"))) == 1


def test_encrypted_card_number_and_tokens_pass():
    assert run(ORM.format(field="card_number = Column(EncryptedType(String, key))")) == []
    assert run(ORM.format(field="gateway_token = Column(String)\n    card_last4 = Column(String(4))")) == []


def test_request_schemas_and_non_python_files_are_not_storage():
    assert run("from pydantic import BaseModel\n\nclass In(BaseModel):\n    card_number: str\n") == []
    assert run("card_number = Column(String)", path="notes.md") == []


def test_syntax_errors_do_not_crash_the_policy():
    assert run("class (:\n") == []


def test_policy_is_in_the_default_engine_and_the_gate():
    code = ORM.format(field="card_number = Column(String(19))")
    assert {f.policy_id for f in PolicyEngine().evaluate_changes(SPEC, {"src/m.py": code})} >= {"privacy.payment_data_storage"}
    assert evaluate({"src/m.py": code}, PACK).blocked


def test_policy_maps_to_the_ecommerce_card_control():
    assert POLICY_CONTROLS["privacy.payment_data_storage"] == ("ECOM-CHECK-003",)
    assert "privacy.payment_data_storage" in TARGETS


def test_corpus_precision_and_recall_for_the_new_policy():
    stats = score(load_cases())["privacy.payment_data_storage"]
    assert stats["precision"] == 1.0 and stats["fp"] == 0
    assert 0 < stats["recall"] < 1


def test_status_is_no_longer_a_health_field():
    pack = load_pack(PACK)
    assert "status" not in pack["data_categories"]["SENSITIVE_HEALTH"]["fields"]
    assert "health_status" in pack["data_categories"]["SENSITIVE_HEALTH"]["fields"]
    assert "status" not in load_legacy_view(PACK)["data_categories"]["SENSITIVE_HEALTH"]["fields"]


def test_retention_messages_use_the_15_year_rule_not_decenal():
    from src.harness import agentic_audit, policy_engine

    for module in (agentic_audit, policy_engine):
        assert "decenal" not in Path(module.__file__).read_text(encoding="utf-8").lower()
