from src.harness.doctor import run_checks


def test_doctor_required_checks_pass():
    checks = run_checks()
    required = [check for check in checks if check.required]
    assert all(check.ok for check in required), [
        (check.name, check.detail) for check in required if not check.ok
    ]
