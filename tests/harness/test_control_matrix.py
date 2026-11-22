"""Matrix de cobertura de los 37 controles del catálogo.

- Cada control implementado tiene al menos un caso positivo y uno negativo.
- Los gaps están declarados con motivo y no emiten hallazgos.
- La compuerta de pre-commit bloquea todos los casos positivos con severidad
  bloqueante (CRITICAL/HIGH con estado VIOLATION) y no bloquea los controles
  que sólo emiten riesgos (WARNING).
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.harness import precommit
from src.harness.catalog import load_catalog
from src.harness.catalog_engine import CatalogEngine
from src.harness.contracts import TaskSpec

ROOT = Path(__file__).resolve().parents[2]
PACK = ROOT / ".harness" / "packs" / "catalog.full.json"
CORPUS_PATH = ROOT / "harness" / "eval" / "catalog_corpus.json"
SPEC = TaskSpec(task_id="matrix", goal="matrix", allowed_paths=["*"], forbidden_paths=[])

DOMAIN_POS = "def purge():\n    session.delete(patient)\n"
DOMAIN_NEG = "def purge():\n    session.delete(order)\n"
LOG_POS = "import logging\nlogger = logging.getLogger(__name__)\n\ndef f(p):\n    logger.info(f'patient {p.rut} created')\n"
LOG_NEG = "import logging\nlogger = logging.getLogger(__name__)\n\ndef f(p):\n    logger.info('patient created')\n"
CONSENT_POS = "class Sub(Base):\n    __tablename__ = 'subs'\n    newsletter_consent = Column(Boolean, default=True)\n"
CONSENT_NEG = "class News(Base):\n    __tablename__ = 'news'\n    title = Column(String)\n"
RIGHTS_POS = "class Patient(Base):\n    __tablename__ = 'patients'\n    rut = Column(String(12))\n"
RIGHTS_NEG = "def helper():\n    return 1\n"
THIRD_PARTY_POS = (
    "class Customer(Base):\n    __tablename__ = 'customers'\n    email = Column(String)\n\n"
    "TRACKING = 'https://metrics.acme.io/send'\n"
)
THIRD_PARTY_NEG = "class Customer(Base):\n    __tablename__ = 'customers'\n    email = Column(String)\n"
SENSITIVE_POS = "class User(Base):\n    __tablename__ = 'users'\n    face_encoding = Column(LargeBinary)\n"
SENSITIVE_NEG = "class User(Base):\n    __tablename__ = 'users'\n    nickname = Column(String)\n"
RETENTION_POS = "class Customer(Base):\n    __tablename__ = 'customers'\n    email = Column(String)\n"
RETENTION_NEG = (
    "class Customer(Base):\n    __tablename__ = 'customers'\n"
    "    email = Column(String)\n    retention_days = Column(Integer)\n"
)
PAYMENT_POS = "from sqlalchemy import Column\n\nclass P(Base):\n    __tablename__ = 'p'\n    card_number = Column(String(19))\n"
PAYMENT_NEG = "from sqlalchemy import Column\n\nclass P(Base):\n    __tablename__ = 'p'\n    gateway_token = Column(String)\n"

LEGACY_CASES: dict[str, tuple[str, str, str]] = {
    "CL-DATAPROT-004": ("src/clinical.py", DOMAIN_POS, DOMAIN_NEG),
    "HEALTH-CHECK-001": ("src/clinical.py", DOMAIN_POS, DOMAIN_NEG),
    "CORE-CHECK-002": ("src/main.py", LOG_POS, LOG_NEG),
    "CORE-CHECK-005": ("src/consent.py", CONSENT_POS, CONSENT_NEG),
    "CORE-CHECK-006": ("src/rights.py", RIGHTS_POS, RIGHTS_NEG),
    "CORE-CHECK-007": ("src/consent.py", CONSENT_POS, CONSENT_NEG),
    "CORE-CHECK-010": ("src/transfers.py", THIRD_PARTY_POS, THIRD_PARTY_NEG),
    "CORE-CHECK-011": ("src/transfers.py", THIRD_PARTY_POS, THIRD_PARTY_NEG),
    "CORE-CHECK-012": ("src/sensitive.py", SENSITIVE_POS, SENSITIVE_NEG),
    "CORE-CHECK-013": ("src/retention.py", RETENTION_POS, RETENTION_NEG),
    "ECOM-CHECK-001": ("src/consent.py", CONSENT_POS, CONSENT_NEG),
    "ECOM-CHECK-003": ("src/pay.py", PAYMENT_POS, PAYMENT_NEG),
    "ECOM-CHECK-005": ("src/transfers.py", THIRD_PARTY_POS, THIRD_PARTY_NEG),
    "ECOM-CHECK-007": ("src/sensitive.py", SENSITIVE_POS, SENSITIVE_NEG),
}

BLOCKING_LEGACY = {
    "CL-DATAPROT-004", "HEALTH-CHECK-001", "CORE-CHECK-002", "CORE-CHECK-005",
    "CORE-CHECK-007", "ECOM-CHECK-001", "ECOM-CHECK-003", "CORE-CHECK-012", "ECOM-CHECK-007",
}
WARNING_ONLY_LEGACY = {"CORE-CHECK-006", "CORE-CHECK-010", "CORE-CHECK-011", "CORE-CHECK-013", "ECOM-CHECK-005"}


def _catalog():
    return load_catalog(PACK)


def _engine() -> CatalogEngine:
    return CatalogEngine(_catalog(), include_legacy=True)


def _ids(code: str, path: str = "src/m.py") -> set[str]:
    return {f.policy_id for f in _engine().evaluate(SPEC, {path: code})}


def _corpus_cases() -> list[dict]:
    return json.loads(CORPUS_PATH.read_text(encoding="utf-8"))["cases"]


def _corpus_positive_negative(control_id: str) -> tuple[str, str, str]:
    positives = [c for c in _corpus_cases() if c["control"] == control_id and c["expected"] == "violation"]
    negatives = [c for c in _corpus_cases() if c["control"] == control_id and c["expected"] == "clean"]
    assert positives, f"corpus: control {control_id} no tiene caso positivo"
    assert negatives, f"corpus: control {control_id} no tiene caso negativo"
    return positives[0]["path"], positives[0]["code"], negatives[0]["code"]


def _all_cases() -> dict[str, tuple[str, str, str]]:
    cases = dict(LEGACY_CASES)
    for control in _catalog().controls:
        if control.implemented and control.id.startswith("v2."):
            cases[control.id] = _corpus_positive_negative(control.id)
    return cases


ALL_CASES = _all_cases()


def test_every_implemented_control_has_positive_and_negative_cases():
    implemented = {c.id for c in _catalog().controls if c.implemented}
    assert set(ALL_CASES) == implemented, (
        f"faltan casos para {sorted(implemented - set(ALL_CASES))} "
        f"o sobran {sorted(set(ALL_CASES) - implemented)}")


@pytest.mark.parametrize("control_id", sorted(ALL_CASES))
def test_positive_case_fires_its_control(control_id):
    path, positive, _ = ALL_CASES[control_id]
    assert control_id in _ids(positive, path)


@pytest.mark.parametrize("control_id", sorted(ALL_CASES))
def test_negative_case_does_not_fire_its_control(control_id):
    path, _, negative = ALL_CASES[control_id]
    assert control_id not in _ids(negative, path)


def test_gap_controls_are_declared_with_reason():
    catalog = _catalog()
    gaps = [c for c in catalog.controls if not c.implemented]
    assert len(gaps) == 16
    assert all(c.gap_reason for c in gaps)
    assert set(_engine().gaps()) == {c.id for c in gaps}


def _gate_control_ids(findings) -> set[str]:
    ids: set[str] = set()
    for finding in findings:
        if finding.policy_id in precommit.LEGACY_CONTROLS:
            ids.update(precommit.LEGACY_CONTROLS[finding.policy_id])
        else:
            ids.add(finding.policy_id)
    return ids


@pytest.mark.parametrize("control_id", sorted(BLOCKING_LEGACY))
def test_gate_blocks_blocking_severity_positives(control_id):
    path, positive, _ = ALL_CASES[control_id]
    assert precommit.evaluate({path: positive}, PACK).blocked


@pytest.mark.parametrize("control_id", sorted(WARNING_ONLY_LEGACY))
def test_gate_does_not_block_warning_only_controls(control_id):
    path, positive, _ = ALL_CASES[control_id]
    result = precommit.evaluate({path: positive}, PACK)
    assert control_id in _gate_control_ids(result.findings)
    assert not result.blocked


def test_gate_report_cites_the_control_and_article():
    path, positive, _ = ALL_CASES["CORE-CHECK-005"]
    result = precommit.evaluate({path: positive}, PACK)
    report = precommit.format_report(result, PACK)
    assert "CORE-CHECK-005" in report and "Art. 12" in report


@pytest.mark.parametrize("control_id", [c.id for c in _catalog().controls
                                        if c.implemented and c.id.startswith("v2.")])
def test_gate_blocks_every_v2_corpus_positive(control_id):
    path, positive, _ = ALL_CASES[control_id]
    assert precommit.evaluate({path: positive}, PACK).blocked
