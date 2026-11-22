"""Framework coverage: Django, DRF, ORM and CLI shapes that round 3 exposed."""
from pathlib import Path

from src.harness.catalog import load_catalog
from src.harness.catalog_engine import CatalogEngine
from src.harness.contracts import TaskSpec

CATALOG = Path(__file__).resolve().parents[2] / ".harness" / "packs" / "catalog.v2.json"
ENGINE = CatalogEngine(load_catalog(CATALOG))
SPEC = TaskSpec(task_id="framework", goal="framework", allowed_paths=["*"], forbidden_paths=[])


def ids(code: str, path: str = "app/framework.py") -> set[str]:
    findings = ENGINE.evaluate(SPEC, {path: code})
    return {finding.policy_id for finding in findings}


def test_django_json_response_in_admin_route():
    code = (
        "def admin_customer(customer):\n"
        "    return JsonResponse({'email': customer.email, 'phone': customer.phone})\n"
    )
    assert "v2.admin_exposure" in ids(code)


def test_django_json_response_reset_token():
    code = "def reset(token):\n    return JsonResponse({'token': token})\n"
    assert "v2.reset_token" in ids(code)


def test_drf_admin_serializer_fields():
    code = (
        "class AdminCustomerSerializer(serializers.ModelSerializer):\n"
        "    class Meta:\n"
        "        model = Customer\n"
        "        fields = ['id', 'rut', 'email', 'phone']\n"
    )
    assert "v2.admin_exposure" in ids(code)


def test_drf_credential_serializer_fields():
    code = (
        "class IntegrationSerializer(serializers.ModelSerializer):\n"
        "    class Meta:\n"
        "        model = Integration\n"
        "        fields = ['id', 'name', 'api_secret']\n"
    )
    assert "v2.credential_response" in ids(code)


def test_django_admin_list_display():
    code = (
        "@admin.register(Customer)\n"
        "class CustomerAdmin(admin.ModelAdmin):\n"
        "    list_display = ('id', 'email', 'phone')\n"
    )
    assert "v2.admin_exposure" in ids(code)


def test_django_orm_manager_delete():
    code = (
        "def purge():\n"
        "    cutoff = timezone.now() - timedelta(days=90)\n"
        "    Customer.objects.filter(last_login__lt=cutoff).delete()\n"
    )
    assert "v2.customer_hard_delete" in ids(code)


def test_cli_stdout_is_a_log_sink():
    code = (
        "def handle(self):\n"
        "    token = default_token_generator.make_token(user)\n"
        "    self.stdout.write('reset token: %s' % token)\n"
    )
    assert "v2.reset_token" in ids(code)


def test_api_key_header_dict_log():
    code = (
        "def deliver(event, integration, logger):\n"
        "    headers = {'X-Api-Key': integration.api_key}\n"
        "    logger.info('delivering %s', headers)\n"
    )
    assert "v2.api_key" in ids(code)


def test_fuzzy_personal_identifier_in_log():
    code = 'def f(phone_number):\n    log.info("sms %s", phone_number)\n'
    assert "v2.log_pii" in ids(code)


def test_strawberry_admin_type_field():
    code = "@strawberry.type\nclass AdminCustomer:\n    id: int\n    rut: str\n"
    assert "v2.admin_exposure" in ids(code)


def test_strawberry_credential_type_field():
    code = "@strawberry.type\nclass TenantSettings:\n    tenant_id: str\n    api_secret: str\n"
    assert "v2.credential_response" in ids(code)


def test_api_key_secret_name_in_log():
    code = 'def f(secret, log):\n    log.info("key %s", secret)\n'
    assert "v2.api_key" in ids(code)


def test_prose_email_is_not_logged_pii():
    code = 'def f(order, log):\n    log.info("invoice email dispatched for %s", order.id)\n'
    assert "v2.log_pii" not in ids(code)


def test_email_with_value_is_logged_pii():
    code = 'def f(email, log):\n    log.info("email=%s", email)\n'
    assert "v2.log_pii" in ids(code)


def test_email_count_is_not_logged_pii():
    code = ("def f(customers, log):\n"
            "    with_email = sum(1 for c in customers if c.email)\n"
            "    log.info('with_email=%d', with_email)\n")
    assert "v2.log_pii" not in ids(code)


def test_admin_route_path_is_context():
    code = "def list_customers(rows):\n    return [{'email': c.email} for c in rows]\n"
    assert "v2.admin_exposure" in ids(code, "app/admin/customers.py")


def test_admin_shipping_address_key():
    code = "def admin_order(order):\n    return {'shipping_address': order.address}\n"
    assert "v2.admin_exposure" in ids(code)


def test_dict_dunder_dump_is_flagged():
    code = "def user_record(user):\n    data = dict(user.__dict__)\n    return data\n"
    assert "v2.credential_response" in ids(code)


def test_helper_retention_cutoff_is_clean():
    code = ("RETENTION_DAYS = 730\n\n"
            "def _cutoff(days=RETENTION_DAYS):\n    return now() - timedelta(days=days)\n\n"
            "def purge(session):\n    cutoff = _cutoff()\n"
            "    session.execute(delete(Customer).where(Customer.created_at < cutoff))\n")
    assert "v2.customer_hard_delete" not in ids(code)


def test_helper_cutoff_not_feeding_delete_is_still_flagged():
    code = ("RETENTION_DAYS = 730\n\n"
            "def _cutoff(days=RETENTION_DAYS):\n    return now() - timedelta(days=days)\n\n"
            "def purge(session, customer_id):\n"
            "    window = _cutoff()\n"
            "    audit_log.info('retention window %s', window)\n"
            "    session.execute(delete(Customer).where(Customer.id == customer_id))\n")
    assert "v2.customer_hard_delete" in ids(code)


def test_direct_helper_cutoff_in_delete_is_clean():
    code = ("RETENTION_DAYS = 730\n\n"
            "def _cutoff(days=RETENTION_DAYS):\n    return now() - timedelta(days=days)\n\n"
            "def purge(session):\n"
            "    session.execute(delete(Customer).where(Customer.created_at < _cutoff()))\n")
    assert "v2.customer_hard_delete" not in ids(code)
