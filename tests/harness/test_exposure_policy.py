from src.harness.contracts import TaskSpec
from src.harness.exposure_policy import ApiPersonalDataExposurePolicy
from src.harness.policy_engine import PolicyEngine

SPEC = TaskSpec(task_id="t", goal="g", allowed_paths=["*"], forbidden_paths=[])


def run(code: str, path: str = "src/backend/api/x.py"):
    return ApiPersonalDataExposurePolicy().evaluate(SPEC, {path: code})


def test_dict_with_raw_rut_is_flagged():
    code = "@router.get('/p')\ndef p():\n    return {'rut': patient.rut, 'name': 'x'}\n"
    f = run(code)
    assert [x.policy_id for x in f] == ["privacy.api_exposure"]
    assert f[0].line == 3 and f[0].status == "VIOLATION"


def test_masked_value_is_clean():
    code = "@router.get('/p')\ndef p():\n    return {'rut': mask_rut(patient.rut)}\n"
    assert run(code) == []


def test_response_model_with_credential_field_is_flagged():
    code = (
        "class UserOut(BaseModel):\n    username: str\n    hashed_password: str\n\n"
        "@router.get('/u', response_model=list[UserOut])\ndef u():\n    return []\n"
    )
    f = run(code)
    assert len(f) == 1 and "hashed_password" in f[0].message


def test_access_token_response_is_not_flagged():
    code = "@router.post('/token')\ndef t():\n    return {'access_token': tok, 'token_type': 'bearer'}\n"
    assert run(code) == []


def test_non_route_function_and_non_python_are_ignored():
    assert run("def helper():\n    return {'rut': r}\n") == []
    assert run("return {'rut': r}", path="notes.md") == []


def test_syntax_error_is_ignored():
    assert run("def broken(:\n") == []


def test_json_response_with_raw_rut_is_flagged():
    code = (
        "@router.get('/admin/x')\ndef list_x():\n"
        "    return JSONResponse({'rut': row['rut'], 'email': row['email']})\n"
    )
    f = run(code)
    assert {x.status for x in f} == {"VIOLATION"}
    assert any("rut" in x.message for x in f)


def test_list_of_dicts_with_raw_rut_is_flagged():
    code = (
        "@router.get('/admin/customers')\ndef customers():\n"
        "    return [{'rut': row['rut'], 'name': row['name']} for row in rows]\n"
    )
    f = run(code)
    assert len(f) == 1 and f[0].line == 3


def test_admin_contact_fields_are_flagged_but_own_profile_is_clean():
    admin = (
        "@router.get('/admin/customers')\ndef customers():\n"
        "    return [{'email': row['email'], 'phone': row['phone']}]\n"
    )
    own = (
        "@router.get('/profile')\ndef profile():\n"
        "    return {'email': customer.email, 'phone': customer.phone}\n"
    )
    assert len(run(admin)) == 2
    assert run(own) == []


def test_admin_raw_row_serialisation_is_a_warning():
    code = (
        "@router.get('/admin/customers')\ndef customers(rows):\n"
        "    return [dict(row) for row in rows]\n"
    )
    f = run(code)
    assert [x.status for x in f] == ["WARNING"]


def test_masked_list_payload_is_clean():
    code = (
        "@router.get('/admin/customers')\ndef customers():\n"
        "    return [{'rut': mask_rut(row['rut']), 'email': redact(row['email'])}]\n"
    )
    assert run(code) == []


def test_registered_in_default_engine():
    ids = [type(p).__name__ for p in PolicyEngine().policies]
    assert "ApiPersonalDataExposurePolicy" in ids
