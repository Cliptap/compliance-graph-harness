"""Deterministic checks for the Ley 21.719 controls that do not fit a sink family."""
from pathlib import Path

from src.harness.catalog import load_catalog
from src.harness.catalog_engine import CatalogEngine
from src.harness.contracts import TaskSpec

FULL_CATALOG = Path(__file__).resolve().parents[2] / ".harness" / "packs" / "catalog.full.json"
ENGINE = CatalogEngine(load_catalog(FULL_CATALOG), include_legacy=False)
SPEC = TaskSpec(task_id="hygiene", goal="hygiene", allowed_paths=["*"], forbidden_paths=[])


def ids(code: str, path: str = "app/framework.py") -> set[str]:
    return {finding.policy_id for finding in ENGINE.evaluate(SPEC, {path: code})}


def test_health_cache_without_encryption_is_flagged():
    code = ("from app.cache import cache\n\n\n"
            "def prime(patient):\n"
            "    cache.set(f'patient:{patient.id}', {\n"
            "        'full_name': patient.full_name,\n"
            "        'diagnosis': patient.diagnosis,\n"
            "    })\n")
    assert "CL-DATAPROT-002" in ids(code)


def test_encrypted_cache_payload_is_clean():
    code = ("from app.cache import cache\n"
            "from app.crypto import encrypt\n\n\n"
            "def prime(patient):\n"
            "    cache.set(f'patient:{patient.id}', encrypt({'diagnosis': patient.diagnosis}))\n")
    assert "CL-DATAPROT-002" not in ids(code)


def test_health_orm_field_without_encryption_is_flagged():
    code = ("from sqlalchemy import Column, String\n"
            "from sqlalchemy.orm import declarative_base\n\n"
            "Base = declarative_base()\n\n\n"
            "class Patient(Base):\n"
            "    __tablename__ = 'patients'\n"
            "    id = Column(String, primary_key=True)\n"
            "    diagnosis = Column(String)\n")
    assert "CL-DATAPROT-003" in ids(code)


def test_encrypted_orm_field_is_clean():
    code = ("from sqlalchemy import Column, String\n"
            "from sqlalchemy_utils import EncryptedType\n\n"
            "Base = declarative_base()\n\n\n"
            "class Patient(Base):\n"
            "    __tablename__ = 'patients'\n"
            "    diagnosis = Column(EncryptedType(String, 'key'))\n")
    assert "CL-DATAPROT-003" not in ids(code)


def test_clinical_route_without_auth_is_flagged():
    code = ("from fastapi import APIRouter\n\n"
            "router = APIRouter()\n\n\n"
            "@router.get('/patients/{patient_id}')\n"
            "def get_patient(patient_id: int):\n"
            "    patient = load_patient(patient_id)\n"
            "    return {'id': patient.id, 'full_name': patient.full_name}\n")
    assert "CL-DATAPROT-005" in ids(code)


def test_clinical_route_with_auth_dependency_is_clean():
    code = ("from fastapi import APIRouter, Depends\n\n"
            "router = APIRouter()\n\n\n"
            "@router.get('/patients/{patient_id}')\n"
            "def get_patient(patient_id: int, user=Depends(require_clinical_role)):\n"
            "    patient = load_patient(patient_id)\n"
            "    return {'id': patient.id, 'full_name': patient.full_name}\n")
    assert "CL-DATAPROT-005" not in ids(code)


def test_clinical_export_as_csv_is_flagged():
    code = ("from fastapi import APIRouter\n"
            "from fastapi.responses import PlainTextResponse\n\n"
            "router = APIRouter()\n\n\n"
            "@router.get('/patients/export')\n"
            "def export_patients():\n"
            "    rows = load_patients()\n"
            "    body = '\\n'.join(','.join([row.id, row.full_name]) for row in rows)\n"
            "    return PlainTextResponse(body, media_type='text/csv')\n")
    assert "CL-DATAPROT-007" in ids(code)


def test_clinical_export_as_fhir_json_is_clean():
    code = ("from fastapi import APIRouter\n"
            "from fastapi.responses import JSONResponse\n\n"
            "router = APIRouter()\n\n\n"
            "@router.get('/patients/export')\n"
            "def export_patients():\n"
            "    rows = load_patients()\n"
            "    bundle = {'resourceType': 'Bundle', 'entry': [row.to_fhir() for row in rows]}\n"
            "    return JSONResponse(bundle, media_type='application/fhir+json')\n")
    assert "CL-DATAPROT-007" not in ids(code)


def test_personal_route_without_auth_is_flagged():
    code = ("from fastapi import APIRouter\n\n"
            "router = APIRouter()\n\n\n"
            "@router.get('/customers/{customer_id}')\n"
            "def get_customer(customer_id: int):\n"
            "    customer = load_customer(customer_id)\n"
            "    return {'email': customer.email, 'phone': customer.phone}\n")
    assert "CORE-CHECK-003" in ids(code)


def test_personal_route_with_auth_is_clean():
    code = ("from fastapi import APIRouter, Depends\n\n"
            "router = APIRouter()\n\n\n"
            "@router.get('/customers/{customer_id}')\n"
            "def get_customer(customer_id: int, user=Depends(current_customer)):\n"
            "    customer = load_customer(customer_id)\n"
            "    return {'email': customer.email, 'phone': customer.phone}\n")
    assert "CORE-CHECK-003" not in ids(code)
