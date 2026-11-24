import pytest

from src.harness.contracts import TaskSpec
from src.harness.dimension_policy import POLICY_IDS, PersonalDataDimensionsPolicy

SPEC = TaskSpec(task_id="T", goal="dimension detectors")


def _ids(files: dict[str, str]) -> list[str]:
    return [f.policy_id for f in PersonalDataDimensionsPolicy().evaluate(SPEC, files)]


CUSTOMER = """
class Customer(Base):
    __tablename__ = "customers"
    email = Column(String)
    rut = Column(String)
"""

RIGHTS = """
@router.get("/me/data")
def read_me(): ...

@router.patch("/me/update")
def update_me(): ...

@router.delete("/me/delete")
def delete_me(): ...

@router.post("/me/opposition")
def oppose(): ...

@router.get("/me/export")
def export_me(): ...

@router.post("/me/block")
def block_me(): ...

class RightsRequest(Base):
    __tablename__ = "rights_requests"
    blocked = Column(Boolean, default=False)
    requested_at = Column(DateTime)
"""


def test_missing_rights_are_reported_as_potential_risk():
    findings = PersonalDataDimensionsPolicy().evaluate(SPEC, {"src/models.py": CUSTOMER})
    rights = [f for f in findings if f.policy_id == "privacy.rights_reachability"]
    assert rights
    assert all(f.status == "WARNING" for f in rights)
    assert any("access" in f.message or "erasure" in f.message for f in rights)


def test_all_rights_routes_and_blocked_state_clear_the_rights_check():
    files = {"src/models.py": CUSTOMER, "src/api.py": RIGHTS}
    rights = [f for f in PersonalDataDimensionsPolicy().evaluate(SPEC, files)
              if f.policy_id == "privacy.rights_reachability"]
    assert rights == []


def test_missing_rights_route_blocks_on_a_complete_scan():
    findings = PersonalDataDimensionsPolicy(complete=True).evaluate(SPEC, {"src/models.py": CUSTOMER})
    rights = [f for f in findings if f.policy_id == "privacy.rights_reachability"]
    assert rights
    assert all(f.status == "VIOLATION" and f.severity == "HIGH" for f in rights)


def test_missing_rights_route_stays_a_warning_on_a_diff():
    findings = PersonalDataDimensionsPolicy().evaluate(SPEC, {"src/models.py": CUSTOMER})
    rights = [f for f in findings if f.policy_id == "privacy.rights_reachability"]
    assert rights
    assert all(f.status == "WARNING" for f in rights)


def test_complete_scan_with_every_rights_route_reports_no_rights_finding():
    files = {"src/models.py": CUSTOMER, "src/api.py": RIGHTS}
    rights = [f for f in PersonalDataDimensionsPolicy(complete=True).evaluate(SPEC, files)
              if f.policy_id == "privacy.rights_reachability"]
    assert rights == []


def test_pre_ticked_consent_is_a_violation():
    code = CUSTOMER + "\n    marketing_consent = Column(Boolean, default=True)\n"
    findings = PersonalDataDimensionsPolicy().evaluate(SPEC, {"src/models.py": code})
    assert any(f.policy_id == "privacy.consent_transparency" and f.status == "VIOLATION" for f in findings)


def test_opt_in_default_false_is_clean():
    code = CUSTOMER + "\n    marketing_consent = Column(Boolean, default=False)\n"
    findings = PersonalDataDimensionsPolicy().evaluate(SPEC, {"src/models.py": code})
    assert not [f for f in findings if f.status == "VIOLATION"]


def test_pre_checked_template_checkbox_is_a_violation():
    html = '<form><input type="checkbox" name="marketing_consent" checked> Acepto</form>'
    findings = PersonalDataDimensionsPolicy().evaluate(SPEC, {"templates/signup.html": html})
    assert any(f.policy_id == "privacy.consent_transparency" and f.status == "VIOLATION" for f in findings)


def test_marketing_template_without_unsubscribe_warns():
    html = "<p>Oferta exclusiva</p>"
    findings = PersonalDataDimensionsPolicy().evaluate(SPEC, {"templates/promo.html": html})
    assert any(f.policy_id == "privacy.consent_transparency" and f.status == "WARNING" for f in findings)


def test_marketing_template_with_unsubscribe_is_clean():
    html = "<p>Oferta exclusiva</p><a href='/unsubscribe'>Darse de baja</a>"
    findings = PersonalDataDimensionsPolicy().evaluate(SPEC, {"templates/promo.html": html})
    assert not [f for f in findings if f.policy_id == "privacy.consent_transparency"]


def test_non_campaign_templates_mentioning_marketing_are_not_flagged():
    html = "<h1>Mi cuenta</h1><p>Marketing: inactivo</p>"
    for path in ("templates/account.html", "templates/privacy.html"):
        findings = PersonalDataDimensionsPolicy().evaluate(SPEC, {path: html})
        assert not [f for f in findings if f.policy_id == "privacy.consent_transparency"], path


def test_raw_biometric_template_is_a_violation():
    code = """
class BiometricProfile(Base):
    __tablename__ = "biometric_profiles"
    face_encoding = Column(LargeBinary)
"""
    findings = PersonalDataDimensionsPolicy().evaluate(SPEC, {"src/models.py": code})
    assert any(f.policy_id == "privacy.minors_and_sensitive" and f.status == "VIOLATION" for f in findings)


def test_biometric_template_identifier_is_clean():
    code = """
class BiometricProfile(Base):
    __tablename__ = "biometric_profiles"
    face_template_id = Column(String)
"""
    findings = PersonalDataDimensionsPolicy().evaluate(SPEC, {"src/models.py": code})
    assert not [f for f in findings if f.status == "VIOLATION"]


def test_sensitive_field_without_explicit_consent_warns():
    code = """
class Patient(Base):
    __tablename__ = "patients"
    diagnosis = Column(String)
"""
    findings = PersonalDataDimensionsPolicy().evaluate(SPEC, {"src/models.py": code})
    assert any(f.policy_id == "privacy.minors_and_sensitive" and "diagnosis" in f.message for f in findings)


def test_sensitive_field_with_explicit_consent_is_clean():
    code = """
class Patient(Base):
    __tablename__ = "patients"
    diagnosis = Column(String, encrypted=True)
    explicit_consent = Column(Boolean, default=False)
"""
    findings = PersonalDataDimensionsPolicy().evaluate(SPEC, {"src/models.py": code})
    assert not [f for f in findings
                if f.policy_id == "privacy.minors_and_sensitive" and "diagnosis" in f.message]


def test_age_without_gate_warns():
    code = """
class Shopper(Base):
    __tablename__ = "shoppers"
    birth_date = Column(Date)
"""
    findings = PersonalDataDimensionsPolicy().evaluate(SPEC, {"src/models.py": code})
    assert any("age gate" in f.message for f in findings if f.policy_id == "privacy.minors_and_sensitive")


def test_geolocation_without_consent_warns():
    code = """
class Delivery(Base):
    __tablename__ = "deliveries"
    latitude = Column(Float)
"""
    findings = PersonalDataDimensionsPolicy().evaluate(SPEC, {"src/models.py": code})
    assert any("Geolocation" in f.message for f in findings)


def test_personal_field_without_retention_warns():
    code = """
class Customer(Base):
    __tablename__ = "customers"
    email = Column(String)
"""
    findings = PersonalDataDimensionsPolicy().evaluate(SPEC, {"src/models.py": code})
    assert any(f.policy_id == "privacy.retention_minimization" for f in findings)


def test_retention_field_clears_the_retention_check():
    code = """
class Customer(Base):
    __tablename__ = "customers"
    email = Column(String)
    retention_days = Column(Integer)
"""
    findings = PersonalDataDimensionsPolicy().evaluate(SPEC, {"src/models.py": code})
    assert not [f for f in findings if f.policy_id == "privacy.retention_minimization"]


def test_third_party_hosts_are_inventoried_as_partial_evidence():
    files = {"src/models.py": CUSTOMER, "src/sync.py": "URL = 'https://api.stripe.com/v1/charges'"}
    findings = [f for f in PersonalDataDimensionsPolicy().evaluate(SPEC, files)
                if f.policy_id == "privacy.third_party_transfers"]
    assert findings and "api.stripe.com" in findings[0].evidence


def test_local_hosts_are_not_reported():
    files = {"src/models.py": CUSTOMER, "src/sync.py": "URL = 'http://localhost:8000/health'"}
    assert not [f for f in PersonalDataDimensionsPolicy().evaluate(SPEC, files)
                if f.policy_id == "privacy.third_party_transfers"]


def test_policy_ids_are_unique_and_prefixed():
    assert len(POLICY_IDS) == len(set(POLICY_IDS))
    assert all(p.startswith("privacy.") for p in POLICY_IDS)


def test_pathological_input_does_not_raise():
    code = "def broken(:\n  pass"
    assert isinstance(PersonalDataDimensionsPolicy().evaluate(SPEC, {"src/broken.py": code}), list)
