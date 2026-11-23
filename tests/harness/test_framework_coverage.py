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


def test_imported_producer_name_is_tainted():
    code = ("from app.identifiers import format_rut_and_email\n\n"
            "def rows(customers):\n"
            "    return [{'label': format_rut_and_email(c)} for c in customers]\n")
    assert "v2.admin_exposure" in ids(code, "app/views/admin_export.py")


def test_imported_masker_is_clean():
    code = ("from app.identifiers import mask_rut_and_email\n\n"
            "def rows(customers):\n"
            "    return [{'label': mask_rut_and_email(c)} for c in customers]\n")
    assert "v2.admin_exposure" not in ids(code, "app/views/admin_export.py")


def test_imported_sender_is_not_a_value():
    code = ("from app.mailer import send_email\n\n"
            "def notify(user):\n"
            "    return {'sent': send_email(user.email)}\n")
    assert "v2.admin_exposure" not in ids(code, "app/views/admin_export.py")


def test_parameter_reaches_response_inside_helper():
    code = ("from fastapi.responses import JSONResponse\n\n"
            "def render(customer, email):\n"
            "    return JSONResponse({'id': customer.id, 'email': email})\n\n"
            "def view(customer):\n"
            "    return render(customer=customer, email=customer.email)\n")
    assert "v2.admin_exposure" in ids(code, "app/api/admin_render.py")


def test_parameter_reaches_redirect_inside_helper():
    code = ("from fastapi.responses import RedirectResponse\n\n"
            "def go(token):\n"
            "    return RedirectResponse(f'/reset?token={token}')\n\n"
            "def start(repo, user_id):\n"
            "    token = repo.issue_reset(user_id)\n"
            "    return go(token)\n")
    assert "v2.reset_token" in ids(code)


def test_masked_parameter_in_helper_response_is_clean():
    code = ("from fastapi.responses import JSONResponse\n\n"
            "def render(customer, masked_email):\n"
            "    return JSONResponse({'id': customer.id, 'email': masked_email})\n\n"
            "def view(customer, mask_email):\n"
            "    return render(customer=customer, masked_email=mask_email(customer.email))\n")
    assert "v2.admin_exposure" not in ids(code, "app/api/admin_render.py")


def test_instance_payload_mutation_is_flagged():
    code = ("from fastapi.responses import JSONResponse\n\n"
            "class View:\n"
            "    def __init__(self, customer):\n"
            "        self.customer = customer\n"
            "        self._payload = {'id': customer.id}\n\n"
            "    def with_contact(self):\n"
            "        self._payload['email'] = self.customer.email\n"
            "        return self\n\n"
            "    def render(self):\n"
            "        return JSONResponse(self._payload)\n\n"
            "def admin_detail(customer):\n"
            "    return View(customer).with_contact().render()\n")
    assert "v2.admin_exposure" in ids(code, "app/admin/detail.py")


def test_imported_private_key_reader_is_flagged():
    code = ("from fastapi.responses import PlainTextResponse\n"
            "from app.vault import read_private_key_pem\n\n"
            "def signing_key():\n"
            "    pem = read_private_key_pem(key_id=load_active_key_id())\n"
            "    return PlainTextResponse(pem)\n")
    assert "v2.credential_response" in ids(code)


def test_masked_boolean_argument_is_clean():
    code = ("from fastapi.responses import JSONResponse\n\n"
            "def status(has_password):\n"
            "    return JSONResponse({'has_password': has_password})\n\n"
            "def view(record):\n"
            "    return status(has_password=record.password_hash is not None)\n")
    assert "v2.credential_response" not in ids(code)


def test_truncated_value_assignment_is_clean():
    code = ("from fastapi.responses import JSONResponse\n\n"
            "def response(api_key):\n"
            "    suffix = api_key[-4:]\n"
            "    return JSONResponse({'api_key_suffix': suffix})\n\n"
            "def view(integration):\n"
            "    return response(api_key=integration.api_key)\n")
    assert "v2.api_key" not in ids(code)


def test_keyword_only_retention_default_is_clean():
    code = ("from datetime import datetime, timedelta\n\n"
            "RETENTION_DAYS = 2190\n\n"
            "def purge(*, session, days: int = RETENTION_DAYS):\n"
            "    cutoff = datetime.utcnow() - timedelta(days=days)\n"
            "    return session.query(Order).filter(Order.created_at < cutoff).delete()\n")
    assert "v2.billing_retention" not in ids(code)


def test_session_id_log_label_is_clean():
    code = ("import logging\nlogger = logging.getLogger(__name__)\n\n"
            "class Telemetry:\n"
            "    def __init__(self, session_id):\n"
            "        self.session_id = session_id\n\n"
            "    def emit(self):\n"
            "        logger.info('session=%s', self.session_id)\n")
    assert "v2.log_pii" not in ids(code)


def test_false_module_flag_branch_is_not_logged():
    code = ("import logging\nlogger = logging.getLogger(__name__)\n\n"
            "LOG_RAW = False\n\n"
            "def emit(order_id, address):\n"
            "    fields = {'order_id': order_id}\n"
            "    if LOG_RAW:\n"
            "        fields['address'] = address\n"
            "    else:\n"
            "        fields['address_present'] = bool(address)\n"
            "    logger.info('checkout %s', fields)\n")
    assert "v2.log_pii" not in ids(code)


def test_false_class_flag_branch_is_not_rendered():
    code = ("from fastapi.responses import JSONResponse\n\n"
            "class UserView:\n"
            "    include_credentials = False\n\n"
            "    def __init__(self, user):\n"
            "        self.user = user\n\n"
            "    def render(self):\n"
            "        data = {'user_id': self.user.id}\n"
            "        if self.include_credentials:\n"
            "            data['password_hash'] = self.user.password_hash\n"
            "        else:\n"
            "            data['has_password'] = bool(self.user.password_hash)\n"
            "        return JSONResponse(data)\n\n"
            "def view(user):\n"
            "    return UserView(user).render()\n")
    assert "v2.credential_response" not in ids(code)


def test_true_class_flag_branch_is_rendered():
    code = ("from fastapi.responses import JSONResponse\n\n"
            "class DeviceView:\n"
            "    reveal_secret = True\n\n"
            "    def __init__(self, device):\n"
            "        self.device = device\n\n"
            "    def render(self):\n"
            "        data = {'device_id': self.device.id}\n"
            "        if self.reveal_secret:\n"
            "            data['api_secret'] = self.device.secret\n"
            "        return JSONResponse(data)\n\n"
            "def view(device):\n"
            "    return DeviceView(device).render()\n")
    assert "v2.credential_response" in ids(code)


def test_key_assignment_taints_the_container():
    code = ("from fastapi.responses import JSONResponse\n\n"
            "def build(account_id, password_hash):\n"
            "    body = {'id': account_id}\n"
            "    body['password_hash'] = password_hash\n"
            "    return JSONResponse(body)\n\n"
            "def detail(account):\n"
            "    return build(account.id, account.password_hash)\n")
    assert "v2.credential_response" in ids(code, "app/admin/account.py")


def test_camel_case_constructor_is_not_a_source():
    code = ("from fastapi.responses import JSONResponse\n\n"
            "class SessionService:\n"
            "    def current(self, token):\n"
            "        return load_session(token)\n\n"
            "def read_session(token):\n"
            "    record = SessionService().current(token)\n"
            "    return JSONResponse({'username': record.username, 'roles': record.roles})\n")
    assert "v2.credential_response" not in ids(code)


def test_keyword_label_is_not_a_value():
    code = ("from fastapi.responses import JSONResponse\n\n"
            "def integration_response(*, slug, api_key):\n"
            "    suffix = api_key[-4:]\n"
            "    return JSONResponse({'slug': slug, 'api_key_suffix': suffix})\n\n"
            "def view(integration):\n"
            "    return integration_response(slug=integration.slug, api_key=integration.api_key)\n")
    assert "v2.api_key" not in ids(code)


def test_dict_get_projection_in_log_is_flagged():
    code = ("import logging\nlogger = logging.getLogger(__name__)\n\n"
            "def upsert(body):\n"
            "    logger.info('contact address=%s', body.get('address'))\n")
    assert "v2.log_pii" in ids(code)


def test_truncated_projection_in_list_is_clean():
    code = ("def rows(records):\n"
            "    return [{'id': r['id'], 'rut_last4': r['rut'][-4:]} for r in records]\n")
    assert "v2.admin_exposure" not in ids(code, "app/admin/masked.py")


def test_delete_method_with_short_cutoff_is_flagged():
    code = ("CUTOFF_DAYS = 365\n\n"
            "class OrderRepo:\n"
            "    def delete_older_than(self, days):\n"
            "        return days\n\n"
            "def purge():\n"
            "    return OrderRepo().delete_older_than(CUTOFF_DAYS)\n")
    assert "v2.billing_retention" in ids(code)


def test_delete_method_with_policy_cutoff_is_clean():
    code = ("RETENTION_DAYS = 2190\n\n"
            "class InvoiceRepo:\n"
            "    def delete_beyond_retention(self, days):\n"
            "        return days\n\n"
            "def purge():\n"
            "    return InvoiceRepo().delete_beyond_retention(RETENTION_DAYS)\n")
    assert "v2.billing_retention" not in ids(code)


def test_low_retention_field_in_sql_is_flagged():
    code = ("class BillingMixin:\n"
            "    retention_days = 730\n\n"
            "    def statement(self):\n"
            "        return f\"DELETE FROM invoices WHERE issued_at < now() - make_interval(days => {self.retention_days})\"\n\n"
            "class Job(BillingMixin):\n"
            "    def run(self, cursor):\n"
            "        cursor.execute(self.statement())\n")
    assert "v2.billing_retention" in ids(code)


def test_dto_keyword_cutoff_delete_is_flagged():
    code = ("class Plan:\n"
            "    def __init__(self, cutoff_days):\n"
            "        self.cutoff_days = cutoff_days\n\n"
            "class Repo:\n"
            "    def delete_old_orders(self, days):\n"
            "        return days\n\n"
            "def purge(repo):\n"
            "    plan = Plan(cutoff_days=365)\n"
            "    return repo.delete_old_orders(plan.cutoff_days)\n")
    assert "v2.billing_retention" in ids(code)


def test_masked_field_name_in_log_is_clean():
    code = ("import logging\nlogger = logging.getLogger(__name__)\n\n"
            "def log_sync(customer, payload):\n"
            "    logger.info('synced %s email=%s', customer.id, payload['email_masked'])\n")
    assert "v2.log_pii" not in ids(code)


def test_derived_counts_are_not_admin_exposure():
    code = ("from fastapi.responses import JSONResponse\n\n"
            "def coverage(customers):\n"
            "    with_email = sum(1 for c in customers if c.email)\n"
            "    without_email = len(customers) - with_email\n"
            "    return JSONResponse({'with_email': with_email, 'without_email': without_email})\n")
    assert "v2.admin_exposure" not in ids(code, "app/admin/coverage.py")


def test_serializer_write_only_password_is_clean():
    code = ("from rest_framework import serializers\n\n"
            "class UserSerializer(serializers.ModelSerializer):\n"
            "    password = serializers.CharField(write_only=True)\n"
            "    has_password = serializers.SerializerMethodField()\n\n"
            "    class Meta:\n"
            "        model = User\n"
            "        fields = ('id', 'email', 'password', 'has_password')\n\n"
            "    def get_has_password(self, obj):\n"
            "        return bool(obj.password_hash)\n")
    assert "v2.credential_response" not in ids(code)


def test_serializer_source_hash_is_flagged():
    code = ("from rest_framework import serializers\n\n"
            "class UserSerializer(serializers.ModelSerializer):\n"
            "    stored_hash = serializers.CharField(source='password_hash', read_only=True)\n\n"
            "    class Meta:\n"
            "        model = User\n"
            "        fields = ('id', 'stored_hash')\n")
    assert "v2.credential_response" in ids(code)


def test_serializer_token_field_is_flagged_for_reset():
    code = ("from rest_framework import serializers\n\n"
            "class ResetSerializer(serializers.ModelSerializer):\n"
            "    token = serializers.CharField(source='token_hash')\n\n"
            "    class Meta:\n"
            "        model = PasswordResetRequest\n"
            "        fields = ('id', 'token')\n")
    assert "v2.reset_token" in ids(code)


def test_prefixed_retention_constant_below_policy_is_flagged():
    code = ("ORDER_RETENTION_DAYS = 365\n\n"
            "def run(cursor):\n"
            "    sql = \"DELETE FROM orders WHERE created_at < NOW() - INTERVAL '%s days'\" % ORDER_RETENTION_DAYS\n"
            "    cursor.execute(sql)\n")
    assert "v2.billing_retention" in ids(code)


def test_dynamic_model_delete_is_flagged():
    code = ("class Service:\n"
            "    def __init__(self, customer_model):\n"
            "        self.customer_model = customer_model\n\n"
            "    def purge(self, ids):\n"
            "        self.customer_model.objects.filter(id__in=ids).delete()\n")
    assert "v2.customer_hard_delete" in ids(code)


def test_endpoint_returning_tainted_name_is_flagged():
    code = ("from celery import shared_task\n\n"
            "@shared_task\ndef rotate(batch):\n"
            "    results = []\n"
            "    for client in batch:\n"
            "        results.append({'client_id': client.id, 'signing_secret': client.signing_secret})\n"
            "    return results\n")
    assert "v2.api_key" in ids(code)


def test_delete_route_decorator_is_not_a_hard_delete():
    code = ("from fastapi import APIRouter\nrouter = APIRouter()\n\n"
            "def mark_deleted(session, customer_id):\n"
            "    customer = session.get(Customer, customer_id)\n"
            "    customer.deleted_at = now()\n"
            "    session.commit()\n\n"
            "@router.delete('/customers/{customer_id}')\n"
            "def delete_customer(customer_id, session):\n"
            "    mark_deleted(session, customer_id)\n"
            "    return {'deleted': customer_id}\n")
    assert "v2.customer_hard_delete" not in ids(code, "app/api/customers.py")


def test_email_domain_is_not_admin_exposure():
    code = ("from django.contrib import admin\n\n"
            "class StaffUserAdmin(admin.ModelAdmin):\n"
            "    list_display = ('id', 'username', 'email_domain')\n\n"
            "    def email_domain(self, obj):\n"
            "        return obj.email.partition('@')[2]\n")
    assert "v2.admin_exposure" not in ids(code, "app/accounts/admin.py")


def test_nested_serializer_in_admin_file_is_flagged():
    code = ("from rest_framework import serializers\n\n"
            "class CustomerProfileSerializer(serializers.ModelSerializer):\n"
            "    class Meta:\n"
            "        model = Customer\n"
            "        fields = ('id', 'email', 'phone')\n\n"
            "class AdminAccountSerializer(serializers.ModelSerializer):\n"
            "    customer = CustomerProfileSerializer(read_only=True)\n\n"
            "    class Meta:\n"
            "        model = Account\n"
            "        fields = ('id', 'customer')\n")
    assert "v2.admin_exposure" in ids(code, "app/accounts/serializers.py")


def test_serializer_declared_api_key_is_flagged():
    code = ("from rest_framework import serializers\n\n"
            "class BaseClientSerializer(serializers.ModelSerializer):\n"
            "    class Meta:\n"
            "        model = ApiClient\n"
            "        fields = ('id', 'name')\n\n"
            "class ApiClientCredentialsSerializer(BaseClientSerializer):\n"
            "    api_key = serializers.CharField(read_only=True)\n\n"
            "    class Meta(BaseClientSerializer.Meta):\n"
            "        fields = BaseClientSerializer.Meta.fields + ('api_key',)\n")
    assert "v2.api_key" in ids(code)


def test_response_data_secret_fields_are_flagged():
    code = ("from django.conf import settings\n"
            "from rest_framework.views import exception_handler\n\n"
            "class Handler:\n"
            "    secret_fields = ('SECRET_KEY', 'DATABASE_PASSWORD')\n\n"
            "    def __call__(self, exc, context):\n"
            "        response = exception_handler(exc, context)\n"
            "        response.data = {'debug': {name: getattr(settings, name, None) for name in self.secret_fields}}\n"
            "        return response\n")
    assert "v2.credential_response" in ids(code)


def test_django_redirect_with_urlencoded_token_is_flagged():
    code = ("from urllib.parse import urlencode\n"
            "from django.http import HttpResponseRedirect\n\n"
            "def go(token, prefix='/reset'):\n"
            "    params = urlencode({'token': token, 'next': '/'})\n"
            "    return HttpResponseRedirect(f'{prefix}?{params}')\n")
    assert "v2.reset_token" in ids(code)


def test_class_alias_retention_is_clean():
    code = ("from datetime import timedelta\n"
            "from django.utils import timezone\n\n"
            "TAX_RETENTION_DAYS = 2190\n\n"
            "class PurgeView:\n"
            "    required_days = TAX_RETENTION_DAYS\n\n"
            "    def post(self, queryset):\n"
            "        cutoff = timezone.now() - timedelta(days=self.required_days)\n"
            "        return queryset.filter(issued_at__lte=cutoff).delete()\n")
    assert "v2.billing_retention" not in ids(code)


def test_meta_less_serializer_secret_is_flagged():
    code = ("from rest_framework import serializers\n\n"
            "class SecretValueSerializer(serializers.Serializer):\n"
            "    value = serializers.CharField()\n"
            "    secret = serializers.CharField()\n")
    assert "v2.credential_response" in ids(code)


def test_serializer_method_nested_secret_is_flagged():
    code = ("from rest_framework import serializers\n\n"
            "class CredentialSerializer(serializers.Serializer):\n"
            "    value = serializers.CharField()\n\n"
            "class SnapshotSerializer(serializers.ModelSerializer):\n"
            "    credential = serializers.SerializerMethodField()\n\n"
            "    class Meta:\n"
            "        model = User\n"
            "        fields = ('id', 'credential')\n\n"
            "    def get_credential(self, obj):\n"
            "        return CredentialSerializer({'value': obj.secret}).data\n")
    assert "v2.credential_response" in ids(code)


def test_get_fields_exclusion_is_clean():
    code = ("from rest_framework import serializers\n\n"
            "class CredentialSafeMixin:\n"
            "    excluded_fields = ('password', 'password_hash')\n\n"
            "    def get_fields(self):\n"
            "        fields = super().get_fields()\n"
            "        for name in self.excluded_fields:\n"
            "            fields.pop(name, None)\n"
            "        return fields\n\n"
            "class ProfileSerializer(CredentialSafeMixin, serializers.ModelSerializer):\n"
            "    class Meta:\n"
            "        model = User\n"
            "        fields = ('id', 'username', 'password', 'password_hash')\n")
    assert "v2.credential_response" not in ids(code)


def test_global_directory_from_signal_is_flagged():
    code = ("from django.db.models.signals import post_save\n"
            "from django.dispatch import receiver\n"
            "from rest_framework.response import Response\n"
            "from rest_framework.views import APIView\n\n"
            "DIRECTORY = {}\n\n"
            "@receiver(post_save, sender=Customer)\n"
            "def index_customer(sender, instance, **kwargs):\n"
            "    DIRECTORY[str(instance.pk)] = {'email': instance.email, 'phone': instance.phone}\n\n"
            "class AdminDirectoryView(APIView):\n"
            "    def get(self, request):\n"
            "        return Response({'items': list(DIRECTORY.values())})\n")
    assert "v2.admin_exposure" in ids(code, "app/customers/directory.py")


def test_async_adelete_is_flagged():
    code = ("async def purge(user_id):\n"
            "    from app.customers.models import Customer\n"
            "    queryset = Customer.objects.filter(user_id=user_id)\n"
            "    deleted, _detail = await queryset.adelete()\n"
            "    return deleted\n")
    assert "v2.customer_hard_delete" in ids(code)


def test_custom_hard_delete_method_is_flagged():
    code = ("from django.core.management.base import BaseCommand\n\n"
            "class Command(BaseCommand):\n"
            "    def handle(self, *args, **options):\n"
            "        Customer.objects.inactive_since(365).hard_delete()\n")
    assert "v2.customer_hard_delete" in ids(code)


def test_password_set_boolean_field_is_clean():
    code = ("from rest_framework import serializers\n\n"
            "class SecurityFlagsSerializer(serializers.Serializer):\n"
            "    password_set = serializers.BooleanField()\n"
            "    mfa_enabled = serializers.BooleanField()\n")
    assert "v2.credential_response" not in ids(code)


def test_formview_rendered_pii_is_flagged():
    code = ("from django.views.generic import FormView\n\n"
            "class AdminSearchView(FormView):\n"
            "    def form_valid(self, form):\n"
            "        self.results = [{'email': c.email, 'phone': c.phone} for c in Customer.objects.all()]\n"
            "        return self.render_to_response(self.get_context_data(form=form))\n")
    assert "v2.admin_exposure" in ids(code, "app/crm/admin_views.py")


def test_graphql_reset_token_type_is_flagged():
    code = ("import strawberry\n\n"
            "@strawberry.type\n"
            "class ResetResult:\n"
            "    requested: bool\n"
            "    reset_token: str\n")
    assert "v2.reset_token" in ids(code)




def test_purge_service_with_policy_retention_is_clean():
    code = ("from datetime import timedelta\nfrom django.utils import timezone\n\n"
            "RETENTION_DAYS = 730\n\n"
            "class Service:\n"
            "    def cutoff(self):\n"
            "        return timezone.now() - timedelta(days=RETENTION_DAYS)\n\n"
            "    def purge(self, customers):\n"
            "        customers.hard_delete_before(self.cutoff())\n\n"
            "def run(customers):\n"
            "    Service().purge(customers)\n")
    assert "v2.customer_hard_delete" not in ids(code)


def test_async_adelete_with_short_cutoff_is_flagged():
    code = ("from datetime import timedelta\nfrom django.utils import timezone\n\n"
            "def purge():\n"
            "    cutoff = timezone.now() - timedelta(days=365)\n"
            "    Invoice.objects.filter(issued_at__lt=cutoff).adelete()\n")
    assert "v2.billing_retention" in ids(code)


def test_async_purge_with_repository_alias_is_flagged():
    code = ("from datetime import timedelta\nfrom django.utils import timezone\n\n"
            "PURGE_AFTER_DAYS = 180\n\n"
            "async def purge(session):\n"
            "    repo = OrderRepository(session)\n"
            "    cutoff = timezone.now() - timedelta(days=PURGE_AFTER_DAYS)\n"
            "    await repo.delete_before(cutoff)\n")
    assert "v2.billing_retention" in ids(code)


def test_pydantic_model_dump_with_pii_is_logged():
    code = ("import logging\n"
            "from pydantic import BaseModel\n\n"
            "logger = logging.getLogger(__name__)\n\n\n"
            "class CustomerProfile(BaseModel):\n"
            "    id: int\n"
            "    email: str\n"
            "    rut: str\n\n\n"
            "def record(customer):\n"
            "    profile = CustomerProfile(id=customer.id, email=customer.email, rut=customer.rut)\n"
            "    logger.info('profile=%s', profile.model_dump())\n")
    assert "v2.log_pii" in ids(code)


def test_pydantic_admin_response_model_exposes_contact():
    code = ("from fastapi import APIRouter\n"
            "from pydantic import BaseModel\n\n"
            "router = APIRouter(prefix='/admin')\n\n\n"
            "class AdminCustomerOut(BaseModel):\n"
            "    id: int\n"
            "    email: str\n"
            "    phone: str\n\n\n"
            "@router.get('/customers/{customer_id}', response_model=AdminCustomerOut)\n"
            "def admin_customer_detail(customer_id: int):\n"
            "    customer = Customer.objects.get(pk=customer_id)\n"
            "    return AdminCustomerOut(id=customer.id, email=customer.email, phone=customer.phone)\n")
    assert "v2.admin_exposure" in ids(code, "app/admin/customers.py")


def test_cached_admin_export_is_exposed():
    code = ("from fastapi import APIRouter\n"
            "from django.core.cache import cache\n\n"
            "router = APIRouter(prefix='/admin')\n\n\n"
            "def build_export(customer_id):\n"
            "    customer = Customer.objects.get(pk=customer_id)\n"
            "    cache.set(f'admin:export:{customer_id}', {'email': customer.email})\n\n\n"
            "@router.get('/customers/{customer_id}/export')\n"
            "def download_export(customer_id):\n"
            "    payload = cache.get(f'admin:export:{customer_id}')\n"
            "    return {'customer': payload}\n")
    assert "v2.admin_exposure" in ids(code, "app/admin/export_api.py")


def test_dataclass_secret_in_cache_is_exposed():
    code = ("from dataclasses import dataclass, asdict\n"
            "from fastapi import APIRouter\n\n"
            "router = APIRouter(prefix='/services')\n\n\n"
            "@dataclass\n"
            "class ServiceCredential:\n"
            "    service: str\n"
            "    api_key: str\n\n\n"
            "def provision(service):\n"
            "    credential = ServiceCredential(service=service, api_key=issue_api_key(service))\n"
            "    cache.set(f'service:credential:{service}', asdict(credential))\n\n\n"
            "@router.get('/{service}/credentials')\n"
            "def read_credentials(service):\n"
            "    return {'credential': cache.get(f'service:credential:{service}')}\n")
    assert "v2.api_key" in ids(code, "app/services/credential_api.py")


def test_pydantic_reset_response_exposes_token():
    code = ("from fastapi import APIRouter\n"
            "from pydantic import BaseModel\n\n"
            "router = APIRouter(prefix='/auth')\n\n\n"
            "class PasswordResetOut(BaseModel):\n"
            "    email: str\n"
            "    reset_token: str\n\n\n"
            "@router.post('/password-reset', response_model=PasswordResetOut)\n"
            "def request_password_reset(payload):\n"
            "    token = issue_reset_token(payload.email)\n"
            "    return PasswordResetOut(email=payload.email, reset_token=token)\n")
    assert "v2.reset_token" in ids(code)


def test_database_session_receiver_is_not_a_credential():
    code = ("class AccountRepository:\n"
            "    def __init__(self, session):\n"
            "        self.session = session\n\n"
            "    def get_public(self, account_id):\n"
            "        row = self.session.execute('SELECT id, email FROM accounts').one()\n"
            "        return {'id': row.id, 'email': row.email}\n")
    assert "v2.credential_response" not in ids(code)


def test_masked_pydantic_model_is_not_flagged():
    code = ("from pydantic import BaseModel\n\n\n"
            "class AdminCustomerSummary(BaseModel):\n"
            "    id: int\n"
            "    email_masked: str\n"
            "    api_key_configured: bool\n\n\n"
            "def present(customer):\n"
            "    return AdminCustomerSummary(\n"
            "        id=customer.id,\n"
            "        email_masked=mask_email(customer.email),\n"
            "        api_key_configured=bool(customer.api_key),\n"
            "    )\n")
    assert "v2.admin_exposure" not in ids(code, "app/admin/presenters.py")
    assert "v2.api_key" not in ids(code, "app/admin/presenters.py")


def test_cache_key_written_and_read_with_different_expressions():
    code = ("from fastapi import APIRouter\n"
            "from app.cache import cache\n\n"
            "router = APIRouter()\n\n\n"
            "def refresh(tenant_id):\n"
            "    cache.set(f'admin:directory:{tenant_id}', [{'email': u.email}], ttl=300)\n\n\n"
            "@router.get('/admin/tenants/{tenant_id}/directory')\n"
            "def directory(tenant_id: int):\n"
            "    key = 'admin:directory:' + str(tenant_id)\n"
            "    rows = cache.get(key)\n"
            "    return {'users': rows}\n")
    assert "v2.admin_exposure" in ids(code, "app/api/admin_directory.py")


def test_model_inherits_sensitive_field_from_base():
    code = ("from fastapi import APIRouter\n"
            "from pydantic import BaseModel\n\n"
            "router = APIRouter()\n\n\n"
            "class BaseUserCard(BaseModel):\n"
            "    id: int\n"
            "    email: str\n\n\n"
            "class AdminUserCard(BaseUserCard):\n"
            "    status: str = 'active'\n\n\n"
            "@router.get('/admin/users', response_model=list[AdminUserCard])\n"
            "def admin_users():\n"
            "    users = User.objects.all()\n"
            "    return [AdminUserCard(id=u.id, email=u.email) for u in users]\n")
    assert "v2.admin_exposure" in ids(code, "app/api/admin_users.py")


def test_envelope_model_annotated_with_credential_model():
    code = ("from fastapi import APIRouter\n"
            "from pydantic import BaseModel\n\n"
            "router = APIRouter()\n\n\n"
            "class BaseAccountRecord(BaseModel):\n"
            "    id: int\n"
            "    password_hash: str\n\n\n"
            "class AccountRecord(BaseAccountRecord):\n"
            "    last_login: str | None = None\n\n\n"
            "class ProfileEnvelope(BaseModel):\n"
            "    account: AccountRecord\n\n\n"
            "@router.get('/account/{user_id}', response_model=ProfileEnvelope)\n"
            "def get_account(user_id: int):\n"
            "    user = User.objects.get(pk=user_id)\n"
            "    record = AccountRecord(id=user.id, password_hash=user.password_hash)\n"
            "    return ProfileEnvelope(account=record)\n")
    assert "v2.credential_response" in ids(code)


def test_masked_serialized_dict_subscript_is_clean():
    code = ("import logging\n"
            "from dataclasses import dataclass\n\n"
            "logger = logging.getLogger(__name__)\n\n\n"
            "@dataclass\n"
            "class ContactRecord:\n"
            "    id: int\n"
            "    email: str\n\n"
            "    def to_dict(self) -> dict:\n"
            "        local, _, domain = self.email.partition('@')\n"
            "        return {'id': self.id, 'email': f'{local[:1]}***@{domain}'}\n\n\n"
            "def log_contact(contact: ContactRecord) -> None:\n"
            "    safe = contact.to_dict()\n"
            "    logger.info('contact %s', safe['email'])\n")
    assert "v2.log_pii" not in ids(code)


def test_purge_helper_with_keyword_cutoff_is_flagged():
    code = ("GRACE_DAYS = 400\n\n\n"
            "def nightly_cleanup(tenant_id):\n"
            "    with session_scope() as session:\n"
            "        removed = delete_orders_older_than(session, tenant_id, days=GRACE_DAYS)\n"
            "        session.commit()\n"
            "    return removed\n")
    assert "v2.billing_retention" in ids(code, "app/tasks/billing_cleanup.py")


def test_cached_retention_window_gates_the_delete():
    clean = ("from datetime import datetime, timedelta\n"
             "from sqlalchemy import delete\n\n"
             "TAX_RETENTION_DAYS = 2190\n\n\n"
             "def refresh_window(tenant_id):\n"
             "    cache.set(f'tax:window:{tenant_id}', {'days': TAX_RETENTION_DAYS}, ttl=600)\n\n\n"
             "def purge(tenant_id):\n"
             "    window = cache.get('tax:window:' + str(tenant_id))\n"
             "    cutoff = datetime.utcnow() - timedelta(days=window['days'])\n"
             "    session.execute(delete(Invoice).where(Invoice.issued_at < cutoff))\n")
    assert "v2.billing_retention" not in ids(clean)
    short = clean.replace("TAX_RETENTION_DAYS = 2190", "TAX_RETENTION_DAYS = 365")
    assert "v2.billing_retention" in ids(short)


def test_hard_delete_helper_with_table_name_and_no_guard_is_flagged():
    code = ("from celery import shared_task\n\n\n"
            "@shared_task\n"
            "def erase_customer(customer_id: int) -> dict:\n"
            "    with session_scope() as session:\n"
            "        hard_delete_customer(session, customer_id)\n"
            "        session.commit()\n"
            "    return {'customer_id': customer_id, 'erased': True}\n")
    assert "v2.customer_hard_delete" in ids(code, "app/tasks/erase_customer.py")


def test_instance_delete_through_mixin_resolves_the_model():
    code = ("from app.db import session_scope, BaseCustomer\n\n\n"
            "class PurgeMixin:\n"
            "    def hard_delete(self, session) -> None:\n"
            "        session.delete(self)\n\n\n"
            "class ArchivedCustomer(BaseCustomer, PurgeMixin):\n"
            "    archived_at = None\n\n\n"
            "def purge_archived(customer_id: int) -> str:\n"
            "    with session_scope() as session:\n"
            "        record = session.get(ArchivedCustomer, customer_id)\n"
            "        record.hard_delete(session)\n"
            "    return 'deleted'\n")
    assert "v2.customer_hard_delete" in ids(code)


def test_tablename_inheritance_maps_subclass_to_policy_table():
    code = ("from sqlalchemy import delete\n\n\n"
            "class Invoice(BaseInvoice):\n"
            "    __tablename__ = 'invoices'\n\n\n"
            "class CreditNote(Invoice):\n"
            "    __tablename__ = 'credit_notes'\n\n\n"
            "def purge_credit_notes(cutoff):\n"
            "    session.execute(delete(CreditNote).where(CreditNote.issued_at < cutoff))\n"
            "    session.commit()\n")
    assert "v2.billing_retention" in ids(code)


def test_model_dump_exclude_removes_the_logged_field():
    code = ("import logging\n"
            "from pydantic import BaseModel\n\n"
            "logger = logging.getLogger(__name__)\n\n\n"
            "class OrderEvent(BaseModel):\n"
            "    order_id: str\n"
            "    email: str\n"
            "    phone: str\n\n\n"
            "def record(order):\n"
            "    event = OrderEvent(order_id=order.order_id, email=order.email, phone=order.phone)\n"
            "    payload = event.model_dump(exclude={'email', 'phone'})\n"
            "    logger.info('order audit %s', payload)\n")
    assert "v2.log_pii" not in ids(code)


def test_field_exclude_true_is_a_safe_projection():
    code = ("from fastapi import APIRouter\n"
            "from pydantic import BaseModel, Field\n\n"
            "router = APIRouter(prefix='/admin')\n\n\n"
            "class AdminCustomerOut(BaseModel):\n"
            "    id: int\n"
            "    email: str = Field(exclude=True)\n"
            "    phone: str = Field(exclude=True)\n"
            "    email_masked: str\n\n\n"
            "@router.get('/customers/{customer_id}')\n"
            "def get_customer(customer_id: int):\n"
            "    row = load_customer(customer_id)\n"
            "    model = AdminCustomerOut(id=row.id, email=row.email, phone=row.phone, email_masked='a***@b')\n"
            "    return model.model_dump()\n")
    assert "v2.admin_exposure" not in ids(code, "app/admin/customer_out.py")


def test_model_dump_exclude_partial_still_exposes_credentials():
    code = ("from fastapi import APIRouter\n"
            "from pydantic import BaseModel\n\n"
            "router = APIRouter(prefix='/accounts')\n\n\n"
            "class UserOut(BaseModel):\n"
            "    id: int\n"
            "    email: str\n"
            "    password_hash: str\n"
            "    api_secret: str\n\n\n"
            "@router.get('/users/{user_id}')\n"
            "def get_user(user_id: int):\n"
            "    row = load_user(user_id)\n"
            "    model = UserOut(id=row.id, email=row.email, password_hash=row.password_hash, api_secret=row.api_secret)\n"
            "    return model.model_dump(exclude={'email'})\n")
    assert "v2.credential_response" in ids(code)


def test_filtered_dict_comprehension_is_clean():
    code = ("from fastapi import APIRouter\n\n"
            "router = APIRouter()\n\n\n"
            "class CredentialStrippingMixin:\n"
            "    hidden_fields = ('password_hash', 'api_secret')\n\n"
            "    def strip(self, payload):\n"
            "        return {k: v for k, v in payload.items() if k not in self.hidden_fields}\n\n\n"
            "class UserPresenter(CredentialStrippingMixin):\n"
            "    def present(self, row):\n"
            "        raw = {'id': row.id, 'password_hash': row.password_hash, 'api_secret': row.api_secret}\n"
            "        return self.strip(raw)\n\n\n"
            "@router.get('/users/{user_id}')\n"
            "def get_user(user_id: int):\n"
            "    row = load_user(user_id)\n"
            "    return UserPresenter().present(row)\n")
    assert "v2.credential_response" not in ids(code)


def test_record_named_like_a_secret_is_not_a_credential():
    code = ("from rest_framework import serializers\n"
            "from rest_framework.response import Response\n"
            "from rest_framework.views import APIView\n\n\n"
            "class ApiKeySerializer(serializers.ModelSerializer):\n"
            "    key_suffix = serializers.SerializerMethodField()\n"
            "    secret = serializers.CharField(write_only=True, required=False)\n\n"
            "    class Meta:\n"
            "        model = ApiKey\n"
            "        fields = ('id', 'label', 'key_suffix', 'secret')\n\n"
            "    def get_key_suffix(self, obj):\n"
            "        return obj.key[-4:]\n\n\n"
            "class ApiKeyDetailView(APIView):\n"
            "    def get(self, request, key_id):\n"
            "        api_key = ApiKey.objects.get(pk=key_id)\n"
            "        return Response(ApiKeySerializer(api_key).data)\n")
    assert "v2.api_key" not in ids(code)


def test_orjson_response_is_a_response_sink():
    code = ("from fastapi import APIRouter\n"
            "from fastapi.responses import ORJSONResponse\n\n"
            "router = APIRouter(prefix='/keys')\n\n\n"
            "@router.post('/rotate')\n"
            "def rotate_key(owner_id: int):\n"
            "    new_key = generate_api_key(owner_id)\n"
            "    return ORJSONResponse({'id': owner_id, 'api_key': new_key})\n")
    assert "v2.api_key" in ids(code)


def test_location_header_assignment_is_a_redirect_sink():
    code = ("from fastapi import APIRouter\n"
            "from fastapi.responses import RedirectResponse\n\n"
            "router = APIRouter(prefix='/auth')\n\n\n"
            "@router.get('/password-reset/start')\n"
            "def start_reset(email: str):\n"
            "    account = find_account(email)\n"
            "    token = issue_reset_token(account)\n"
            "    target = '/reset/confirm?token=' + token\n"
            "    response = RedirectResponse(url='/login?reset=pending', status_code=303)\n"
            "    response.headers['Location'] = target\n"
            "    return response\n")
    assert "v2.reset_token" in ids(code)


def test_csv_export_with_pii_is_an_admin_response():
    code = ("import csv\n"
            "import io\n"
            "from django.http import HttpResponse\n"
            "from django.contrib.admin.views.decorators import staff_member_required\n\n\n"
            "@staff_member_required\n"
            "def export_customers(request):\n"
            "    buffer = io.StringIO()\n"
            "    writer = csv.writer(buffer)\n"
            "    writer.writerow(['id', 'email', 'phone'])\n"
            "    for customer in Customer.objects.all():\n"
            "        writer.writerow([customer.id, customer.email, customer.phone])\n"
            "    return HttpResponse(buffer.getvalue(), content_type='text/csv')\n")
    assert "v2.admin_exposure" in ids(code, "app/admin/export_views.py")


def test_prefixed_sql_table_name_matches_the_policy_table():
    code = ("import logging\n"
            "from django.db import connection\n\n"
            "logger = logging.getLogger(__name__)\n\n\n"
            "def purge_old_invoices():\n"
            "    sql = 'DELETE FROM billing_invoice WHERE paid = %s AND issued_at < now() - interval %s'\n"
            "    with connection.cursor() as cursor:\n"
            "        cursor.execute(sql, [True, '180 days'])\n"
            "        removed = cursor.rowcount\n"
            "    return removed\n")
    assert "v2.billing_retention" in ids(code)


def test_named_audit_logger_is_a_log_sink():
    code = ("import logging\n\n"
            "audit = logging.getLogger('accounts.audit')\n\n\n"
            "def account_page(account):\n"
            "    audit.warning('account page opened phone=%s id=%s', account.phone, account.id)\n")
    assert "v2.log_pii" in ids(code)


def test_render_context_with_pii_is_an_admin_response():
    code = ("from django.shortcuts import render\n\n"
            "from app.customers.models import Customer\n\n\n"
            "def customer_admin_detail(request, customer_id):\n"
            "    customer = Customer.objects.get(pk=customer_id)\n"
            "    context = {\n"
            "        'customer_id': customer.id,\n"
            "        'email': customer.email,\n"
            "        'phone': customer.phone,\n"
            "    }\n"
            "    return render(request, 'admin/customers/detail.html', context)\n")
    assert "v2.admin_exposure" in ids(code, "app/admin/customer_views.py")


def test_render_context_with_masked_values_is_clean():
    code = ("from django.shortcuts import render\n\n"
            "from app.privacy.masking import mask_email\n\n\n"
            "def customer_admin_detail(request, customer):\n"
            "    context = {\n"
            "        'customer_id': customer.id,\n"
            "        'email': mask_email(customer.email),\n"
            "        'phone': mask_email(customer.phone),\n"
            "    }\n"
            "    return render(request, 'admin/customers/detail.html', context)\n")
    assert "v2.admin_exposure" not in ids(code, "app/admin/customer_views.py")


def test_streamed_column_tuple_exports_credentials():
    code = ("from collections.abc import AsyncIterator\n\n"
            "from fastapi import APIRouter\n"
            "from fastapi.responses import StreamingResponse\n\n"
            "from app.users.models import User\n\n"
            "router = APIRouter(prefix='/internal/users')\n"
            "EXPORT_COLUMNS = ('id', 'username', 'password_hash', 'api_secret')\n\n\n"
            "async def _user_rows() -> AsyncIterator[str]:\n"
            "    yield ','.join(EXPORT_COLUMNS) + '\\n'\n"
            "    async for user in User.objects.all().aiterator():\n"
            "        values = [str(getattr(user, column)) for column in EXPORT_COLUMNS]\n"
            "        yield ','.join(values) + '\\n'\n\n\n"
            "@router.get('/export')\n"
            "async def export_users() -> StreamingResponse:\n"
            "    return StreamingResponse(_user_rows(), media_type='text/csv')\n")
    assert "v2.credential_response" in ids(code)


def test_streamed_reset_token_is_exposed():
    code = ("from collections.abc import AsyncIterator\n\n"
            "from fastapi import APIRouter\n"
            "from fastapi.responses import StreamingResponse\n\n"
            "from app.accounts.models import PasswordReset\n\n"
            "router = APIRouter(prefix='/api/password')\n\n\n"
            "async def _reset_events(reset_id: int) -> AsyncIterator[str]:\n"
            "    reset = PasswordReset.objects.get(pk=reset_id)\n"
            "    yield 'event: ready\\n'\n"
            "    yield f'data: {reset.token}\\n\\n'\n\n\n"
            "@router.get('/{reset_id}/stream')\n"
            "async def stream_reset(reset_id: int) -> StreamingResponse:\n"
            "    return StreamingResponse(_reset_events(reset_id), media_type='text/event-stream')\n")
    assert "v2.reset_token" in ids(code)


def test_dependency_generator_yield_is_not_a_stream():
    code = ("from fastapi import Depends\n"
            "from sqlalchemy.ext.asyncio import AsyncSession\n\n"
            "from app.db import get_session\n\n\n"
            "async def admin_session(session: AsyncSession = Depends(get_session)):\n"
            "    yield session\n")
    assert "v2.credential_response" not in ids(code)


def test_decoded_private_key_in_response_is_a_credential():
    code = ("from fastapi import APIRouter\n\n"
            "from app.security.keys import load_private_key\n\n"
            "router = APIRouter()\n\n\n"
            "@router.get('/internal/jwt/signing-material')\n"
            "def signing_material():\n"
            "    pem = load_private_key('jwt-signing-2026')\n"
            "    return {'algorithm': 'RS256', 'private_key_pem': pem.decode('utf-8')}\n")
    assert "v2.credential_response" in ids(code)


def test_metadata_key_with_password_prefix_is_clean():
    code = ("from django.shortcuts import render\n\n"
            "from app.accounts.models import User\n\n\n"
            "def security_page(request, user_id):\n"
            "    user = User.objects.get(pk=user_id)\n"
            "    return render(\n"
            "        request,\n"
            "        'accounts/security.html',\n"
            "        {\n"
            "            'mfa_enabled': user.mfa_enabled,\n"
            "            'last_password_change': user.password_changed_at,\n"
            "            'token_source': 'email_link',\n"
            "        },\n"
            "    )\n")
    assert "v2.credential_response" not in ids(code)


def test_property_returning_contact_is_logged():
    code = ("import logging\n\n"
            "logger = logging.getLogger(__name__)\n\n\n"
            "class Customer:\n"
            "    def __init__(self, email):\n"
            "        self.email = email\n\n"
            "    @property\n"
            "    def contact_line(self):\n"
            "        return f'contact <{self.email}>'\n\n\n"
            "def record_seen(customer):\n"
            "    logger.info('customer seen: %s', customer.contact_line)\n")
    assert "v2.log_pii" in ids(code)


def test_format_map_body_is_logged():
    code = ("import logging\n\n"
            "logger = logging.getLogger('notifications')\n"
            "RECEIPT_BODY = 'Hola {name}, enviamos tu comprobante a {email}.'\n\n\n"
            "def build_receipt(customer):\n"
            "    body = RECEIPT_BODY.format_map({'name': customer.first_name, 'email': customer.email})\n"
            "    logger.info('rendered receipt: %s', body)\n"
            "    return body\n")
    assert "v2.log_pii" in ids(code)


def test_template_substitute_with_signing_key_is_a_credential():
    code = ("from string import Template\n\n"
            "from fastapi import APIRouter\n\n"
            "router = APIRouter()\n"
            "CONFIG_REPORT = Template('service=$service signing_key=$signing_key')\n\n\n"
            "@router.get('/internal/config-report')\n"
            "def config_report():\n"
            "    body = CONFIG_REPORT.substitute(service='billing', signing_key=current_app.config['SIGNING_KEY'])\n"
            "    return body\n")
    assert "v2.credential_response" in ids(code)


def test_response_model_exclude_removes_the_sensitive_field():
    code = ("from fastapi import APIRouter\n"
            "from pydantic import BaseModel\n\n"
            "router = APIRouter(prefix='/admin-api')\n\n\n"
            "class AdminCustomerRow(BaseModel):\n"
            "    id: int\n"
            "    email: str\n"
            "    plan: str\n\n\n"
            "@router.get('/customers', response_model=list[AdminCustomerRow],\n"
            "            response_model_exclude={'email'})\n"
            "def list_customers():\n"
            "    return [{'id': 1, 'email': 'ana@example.com', 'plan': 'pro'}]\n")
    assert "v2.admin_exposure" not in ids(code)


def test_response_model_with_nested_credential_model_is_flagged():
    code = ("from fastapi import APIRouter\n"
            "from pydantic import BaseModel\n\n"
            "router = APIRouter()\n\n\n"
            "class BaseAccountRecord(BaseModel):\n"
            "    id: int\n"
            "    password_hash: str\n\n\n"
            "class AccountRecord(BaseAccountRecord):\n"
            "    last_login: str | None = None\n\n\n"
            "class ProfileEnvelope(BaseModel):\n"
            "    account: AccountRecord\n\n\n"
            "@router.get('/account/{user_id}', response_model=ProfileEnvelope)\n"
            "def get_account(user_id: int):\n"
            "    record = AccountRecord(id=user_id, password_hash='pbkdf2')\n"
            "    return ProfileEnvelope(account=record)\n")
    assert "v2.credential_response" in ids(code)


def test_payload_key_outside_the_response_model_is_dropped():
    code = ("import jwt\n\n"
            "from fastapi import APIRouter\n"
            "from pydantic import BaseModel\n\n"
            "router = APIRouter(prefix='/settings')\n\n\n"
            "class IntegrationOut(BaseModel):\n"
            "    account_id: int\n"
            "    api_key_configured: bool\n"
            "    api_key_last4: str | None = None\n\n\n"
            "@router.get('/{account_id}', response_model=IntegrationOut,\n"
            "            response_model_exclude_none=True)\n"
            "def read_integration(account_id: int):\n"
            "    token = jwt.encode({'sub': str(account_id), 'scope': 'read'}, 'k', algorithm='HS256')\n"
            "    return {'account_id': account_id, 'api_key_configured': True, 'session_token': token}\n")
    assert "v2.credential_response" not in ids(code)


def test_fingerprint_metadata_field_is_not_pii():
    code = ("import hashlib\n"
            "import logging\n"
            "from dataclasses import dataclass\n\n"
            "logger = logging.getLogger('growth')\n\n\n"
            "@dataclass\n"
            "class SignupEvent:\n"
            "    email: str\n"
            "    email_fingerprint: str = ''\n\n"
            "    def __post_init__(self):\n"
            "        self.email_fingerprint = hashlib.sha256(self.email.encode()).hexdigest()[:16]\n\n\n"
            "def track(email):\n"
            "    event = SignupEvent(email=email)\n"
            "    logger.info('signup fingerprint=%s', event.email_fingerprint)\n")
    assert "v2.log_pii" not in ids(code)


def test_serializer_method_field_with_masked_branch_is_clean():
    code = ("from rest_framework import serializers\n\n\n"
            "class CustomerSerializer(serializers.ModelSerializer):\n"
            "    phone = serializers.SerializerMethodField()\n\n"
            "    class Meta:\n"
            "        model = Customer\n"
            "        fields = ['id', 'full_name', 'phone']\n\n"
            "    def get_phone(self, obj):\n"
            "        digits = ''.join(ch for ch in (obj.phone or '') if ch.isdigit())\n"
            "        return f'***{digits[-4:]}' if digits else '***'\n")
    assert "v2.admin_exposure" not in ids(code, "app/admin/serializers.py")


def test_password_change_timestamp_is_not_a_credential():
    code = ("from fastapi import APIRouter\n\n"
            "router = APIRouter()\n\n\n"
            "@router.get('/accounts/{account_id}/security')\n"
            "def account_security(account_id: int):\n"
            "    account = load_account(account_id)\n"
            "    return {\n"
            "        'id': account.id,\n"
            "        'has_password': bool(account.password_hash),\n"
            "        'mfa_enabled': account.mfa_enabled,\n"
            "        'last_password_change': account.last_password_change,\n"
            "    }\n")
    assert "v2.credential_response" not in ids(code)
