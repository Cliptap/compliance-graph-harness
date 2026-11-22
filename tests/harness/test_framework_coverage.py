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


def test_helper_returned_log_line_is_pii():
    code = ("import logging\n\nlogger = logging.getLogger(__name__)\n\n\n"
            "def build_line(customer):\n"
            "    return f'notify {customer.email} rut={customer.rut}'\n\n\n"
            "def notify(customer):\n"
            "    line = build_line(customer)\n"
            "    logger.info(line)\n")
    assert "v2.log_pii" in ids(code)


def test_masked_helper_return_is_clean():
    code = ("import logging\n\nlogger = logging.getLogger(__name__)\n\n\n"
            "def mask_email(email):\n"
            "    local, _, domain = email.partition('@')\n"
            "    return f'{local[:1]}***@{domain}'\n\n\n"
            "def log_receipt(order, customer):\n"
            "    masked = mask_email(customer.email)\n"
            "    logger.info('sent %s to %s', order.id, masked)\n")
    assert "v2.log_pii" not in ids(code)


def test_admin_export_helper_column_is_flagged():
    code = ("def _contact(customer):\n"
            "    phone = customer.phone_e164\n"
            "    return f'+{phone[:2]} {phone[2:]}'\n\n\n"
            "def export_customers(repo):\n"
            "    payload = []\n"
            "    for customer in repo.all_active():\n"
            "        payload.append({'customer_id': customer.id, 'contact': _contact(customer)})\n"
            "    return {'rows': payload}\n")
    assert "v2.admin_exposure" in ids(code, "app/admin/export.py")


def test_reset_token_in_redirect_is_flagged():
    code = ("from fastapi import APIRouter\n"
            "from fastapi.responses import RedirectResponse\n\n"
            "router = APIRouter()\n\n\n"
            "@router.get('/reset')\n"
            "def reset_link(user, tokens):\n"
            "    token = tokens.create(user.id, ttl_minutes=30)\n"
            "    url = f'https://app.example.com/reset?token={token}'\n"
            "    return RedirectResponse(url, status_code=303)\n")
    assert "v2.reset_token" in ids(code)


def test_api_key_in_redirect_is_flagged():
    code = ("from fastapi import APIRouter\n"
            "from fastapi.responses import RedirectResponse\n\n"
            "router = APIRouter()\n\n\n"
            "@router.get('/connect')\n"
            "def connect(account, secrets):\n"
            "    key = secrets.get_active(account.id)\n"
            "    target = 'https://dashboard.example.com/connect?key=%s' % key.value\n"
            "    return RedirectResponse(target, status_code=302)\n")
    assert "v2.api_key" in ids(code)


def test_masked_key_suffix_is_clean():
    code = ("def describe(record):\n"
            "    return {'api_key_suffix': record.api_key[-4:],\n"
            "            'created_at': record.created_at}\n")
    assert "v2.api_key" not in ids(code)


def test_session_model_is_not_a_credential_source():
    code = ("def summary(self, account_id):\n"
            "    account = self.session.get(Account, account_id)\n"
            "    return {'id': account.id, 'email_verified': account.email_verified}\n")
    assert "v2.credential_response" not in ids(code)


def test_callee_name_is_not_a_value_identifier():
    code = ("def _has_password(user):\n"
            "    return bool(user.password_hash)\n\n"
            "def profile(user):\n"
            "    return {'id': user.id, 'has_password': _has_password(user)}\n")
    assert "v2.credential_response" not in ids(code)


def test_dynamic_column_list_is_flagged():
    code = ("class CustomerReportView:\n"
            "    def __init__(self):\n"
            "        self.columns = ['id', 'rut', 'email']\n\n"
            "    def _row(self, customer):\n"
            "        return {column: getattr(customer, column) for column in self.columns}\n\n"
            "    def render(self, queryset):\n"
            "        return {'rows': [self._row(c) for c in queryset]}\n")
    assert "v2.admin_exposure" in ids(code, "app/api/admin_reports.py")


def test_instance_delete_from_query_is_flagged():
    code = ("def _candidates(session):\n"
            "    return session.query(Customer).filter(Customer.updated_at < cutoff())\n\n"
            "def purge(session):\n"
            "    rows = _candidates(session).all()\n"
            "    for row in rows:\n"
            "        session.delete(row)\n"
            "    session.commit()\n")
    assert "v2.customer_hard_delete" in ids(code)


def test_delete_on_helper_query_is_flagged():
    code = ("from datetime import datetime, timedelta\n\n"
            "def _expired(session, cutoff):\n"
            "    return session.query(Order).filter(Order.created_at < cutoff)\n\n"
            "def purge(session, days=365):\n"
            "    cutoff = datetime.utcnow() - timedelta(days=days)\n"
            "    return _expired(session, cutoff).delete(synchronize_session=False)\n")
    assert "v2.billing_retention" in ids(code)


def test_credential_param_logged_inside_helper_is_flagged():
    code = ("import logging\n\nlogger = logging.getLogger(__name__)\n\n"
            "def _header(key):\n"
            "    return f'Bearer {key}'\n\n"
            "def _audit(org_id, key):\n"
            "    header = _header(key)\n"
            "    logger.info('org=%s auth=%s', org_id, header)\n\n"
            "def ping(repo, org_id):\n"
            "    key = repo.get_api_key(org_id)\n"
            "    _audit(org_id, key)\n")
    assert "v2.api_key" in ids(code)


def test_instance_delete_with_retention_helper_is_clean():
    code = ("from datetime import datetime, timedelta\n\n"
            "RETENTION_DAYS = 730\n\n"
            "def _expired(session):\n"
            "    cutoff = datetime.utcnow() - timedelta(days=RETENTION_DAYS)\n"
            "    return session.query(Customer).filter(Customer.created_at < cutoff)\n\n"
            "def purge(session):\n"
            "    rows = _expired(session).all()\n"
            "    for row in rows:\n"
            "        session.delete(row)\n"
            "    session.commit()\n")
    assert "v2.customer_hard_delete" not in ids(code)


def test_masked_argument_placeholder_is_not_pii():
    code = ("import logging\nlogger = logging.getLogger(__name__)\n\n"
            "def mask(value):\n"
            "    return f'***{value[-2:]}'\n\n"
            "def show(user):\n"
            "    masked = mask(user['email'])\n"
            "    logger.info('email=%s', masked)\n")
    assert "v2.log_pii" not in ids(code)


def test_masked_value_name_is_not_exposed():
    code = "def row(customer, masked_email):\n    return {'email': masked_email}\n"
    assert "v2.admin_exposure" not in ids(code, "app/admin/rows.py")


def test_suffix_helper_is_masked():
    code = ("def _phone_suffix(phone):\n"
            "    digits = ''.join(ch for ch in phone if ch.isdigit())\n"
            "    return digits[-4:]\n\n"
            "def row(customer):\n"
            "    return {'phone_suffix': _phone_suffix(phone=customer.phone)}\n")
    assert "v2.admin_exposure" not in ids(code, "app/admin/rows.py")


def test_password_metadata_is_not_a_credential():
    code = ("def status(user):\n"
            "    return {'user_id': user.id,\n"
            "            'password_algorithm': user.password_algorithm,\n"
            "            'password_changed_at': user.password_changed_at}\n")
    assert "v2.credential_response" not in ids(code)


def test_nested_credential_call_is_not_a_source():
    code = ("def create(username, raw):\n"
            "    user = User.objects.create(username=username, password=make_password(raw))\n"
            "    return {'id': user.id, 'username': user.username}\n")
    assert "v2.credential_response" not in ids(code)


def test_keyword_parameter_reaches_response():
    code = ("from rest_framework.response import Response\n\n"
            "class Serializer:\n"
            "    def render(self, customer, email):\n"
            "        data = {'id': customer.id}\n"
            "        data['email'] = email\n"
            "        return data\n\n"
            "def list_customers(customers):\n"
            "    serializer = Serializer()\n"
            "    rows = [serializer.render(customer=c, email=c.email) for c in customers]\n"
            "    return Response({'rows': rows})\n")
    assert "v2.admin_exposure" in ids(code, "app/api/admin_list.py")


def test_keyword_parameter_logged_inside_helper():
    code = ("import logging\nlogger = logging.getLogger(__name__)\n\n"
            "def audit(event, email):\n"
            "    logger.info('event=%s email=%s', event, email)\n\n"
            "def handle(payload):\n"
            "    audit(event='signup', email=payload['email'])\n")
    assert "v2.log_pii" in ids(code)


def test_constructor_keyword_cutoff_is_clean():
    code = ("from datetime import datetime, timedelta\n\n"
            "LEGAL_HOLD_DAYS = 2190\n\n"
            "class Job:\n"
            "    def __init__(self, days):\n"
            "        self.days = days\n\n"
            "    def run(self, session):\n"
            "        cutoff = datetime.utcnow() - timedelta(days=self.days)\n"
            "        return session.query(Order).filter(Order.created_at < cutoff).delete()\n\n"
            "def trigger(session):\n"
            "    Job(days=LEGAL_HOLD_DAYS).run(session)\n")
    assert "v2.billing_retention" not in ids(code)
