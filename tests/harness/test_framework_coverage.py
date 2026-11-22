"""Framework coverage: Django, DRF, ORM and CLI shapes that round 3 exposed."""
from pathlib import Path

from src.harness.catalog import load_catalog
from src.harness.catalog_engine import CatalogEngine
from src.harness.contracts import TaskSpec

CATALOG = Path(__file__).resolve().parents[2] / ".harness" / "packs" / "catalog.v2.json"
ENGINE = CatalogEngine(load_catalog(CATALOG))
SPEC = TaskSpec(task_id="framework", goal="framework", allowed_paths=["*"], forbidden_paths=[])


def ids(code: str) -> set[str]:
    findings = ENGINE.evaluate(SPEC, {"app/framework.py": code})
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
