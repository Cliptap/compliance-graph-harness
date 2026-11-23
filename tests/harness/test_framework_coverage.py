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
