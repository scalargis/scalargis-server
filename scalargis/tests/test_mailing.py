import inspect
import logging
import smtplib
from email import message_from_string
from types import SimpleNamespace

import pytest
from flask import Flask

from app.utils import mailing


class FakeSMTP:
    instances = []
    offer_starttls = True
    starttls_error = None
    refused = {}

    def __init__(self, host, port, timeout=None):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.calls = []
        self.sent = []
        self.tls_context = None
        FakeSMTP.instances.append(self)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def ehlo(self):
        self.calls.append('ehlo')

    def has_extn(self, name):
        return name.lower() == 'starttls' and self.offer_starttls

    def starttls(self, context=None):
        self.calls.append('starttls')
        self.tls_context = context
        if self.starttls_error:
            raise self.starttls_error

    def login(self, user, password):
        self.calls.append(('login', user, password))

    def send_message(self, msg, from_addr=None, to_addrs=None):
        self.calls.append('send')
        self.sent.append((msg, from_addr, list(to_addrs)))
        return dict(self.refused)


class FakeDb:
    def __init__(self, rows):
        self.session = SimpleNamespace(query=lambda model: SimpleNamespace(all=lambda: rows))


def row(code, value):
    return SimpleNamespace(code=code, setting_value=value)


BASE_CONFIG = {
    'SCALARGIS_SMTP_SERVER': 'mail.example.org',
    'SCALARGIS_SMTP_PORT': 587,
    'SCALARGIS_USE_SSL_EMAIL': False,
    'SCALARGIS_SENDER_EMAIL': 'no-reply@example.org',
}


@pytest.fixture(autouse=True)
def fake_smtp(monkeypatch):
    FakeSMTP.instances = []
    FakeSMTP.offer_starttls = True
    FakeSMTP.starttls_error = None
    FakeSMTP.refused = {}
    monkeypatch.setattr(mailing.smtplib, 'SMTP', FakeSMTP)
    monkeypatch.setattr(mailing, 'db', FakeDb([]))
    monkeypatch.setattr(mailing, '_deliver_async',
                        lambda app, message, recipients, conn: mailing.deliver(message, recipients, conn))
    return FakeSMTP


def make_app(**overrides):
    app = Flask('mailing-test')
    app.config.update(BASE_CONFIG)
    for key, value in overrides.items():
        if value is ...:
            app.config.pop(key, None)
        else:
            app.config[key] = value
    return app


def send(app, recipients=('a@example.org',), **kwargs):
    with app.app_context():
        return mailing.send_email(subject='testing scalargis mailing', html_body='<p>hi</p>',
                                  recipients=list(recipients), **kwargs)


def session():
    assert len(FakeSMTP.instances) == 1
    return FakeSMTP.instances[0]


def test_default_mode_is_never():
    assert send(make_app()) is True
    smtp = session()
    assert 'starttls' not in smtp.calls
    assert 'send' in smtp.calls
    assert smtp.timeout == 15


def test_never_skips_offered_starttls():
    assert send(make_app(SCALARGIS_SMTP_STARTTLS='never')) is True
    assert 'starttls' not in session().calls


def test_auto_offered_uses_starttls_with_verified_cert():
    send(make_app(SCALARGIS_SMTP_STARTTLS='auto'))
    smtp = session()
    assert smtp.calls[:3] == ['ehlo', 'starttls', 'ehlo']
    assert 'send' in smtp.calls
    assert smtp.tls_context.check_hostname is True


def test_auto_not_offered_sends_plaintext(caplog):
    FakeSMTP.offer_starttls = False
    with caplog.at_level(logging.INFO, logger=mailing.__name__):
        send(make_app(SCALARGIS_SMTP_STARTTLS='auto'))
    smtp = session()
    assert 'starttls' not in smtp.calls
    assert 'send' in smtp.calls
    assert 'no STARTTLS offered' in caplog.text


def test_required_not_offered_aborts_before_login(caplog):
    FakeSMTP.offer_starttls = False
    app = make_app(SCALARGIS_SMTP_STARTTLS='required', SCALARGIS_SMTP_USERNAME='user',
                   SCALARGIS_SMTP_PASSWORD='secret')
    send(app)
    smtp = session()
    assert 'send' not in smtp.calls
    assert not any(isinstance(c, tuple) and c[0] == 'login' for c in smtp.calls)
    assert 'required but not offered' in caplog.text


@pytest.mark.parametrize('mode', ['auto', 'required'])
def test_tls_failure_aborts_send(mode, caplog):
    FakeSMTP.starttls_error = smtplib.SMTPException('handshake failed')
    send(make_app(SCALARGIS_SMTP_STARTTLS=mode, SCALARGIS_SMTP_USERNAME='user'))
    smtp = session()
    assert 'send' not in smtp.calls
    assert not any(isinstance(c, tuple) for c in smtp.calls)
    assert 'STARTTLS failed' in caplog.text


def test_login_without_tls_warns_but_sends(caplog):
    send(make_app(SCALARGIS_SMTP_USERNAME='user', SCALARGIS_SMTP_PASSWORD='secret'))
    smtp = session()
    assert ('login', 'user', 'secret') in smtp.calls
    assert 'send' in smtp.calls
    assert 'without TLS' in caplog.text


def test_login_after_tls_does_not_warn(caplog):
    send(make_app(SCALARGIS_SMTP_STARTTLS='auto', SCALARGIS_SMTP_USERNAME='user'))
    assert ('login', 'user', '') in session().calls
    assert 'without TLS' not in caplog.text


def test_empty_username_means_no_login():
    send(make_app(SCALARGIS_SMTP_USERNAME='', SCALARGIS_SMTP_PASSWORD=''))
    assert not any(isinstance(c, tuple) for c in session().calls)


def test_tls_verify_false_disables_cert_checks():
    send(make_app(SCALARGIS_SMTP_STARTTLS='auto', SCALARGIS_SMTP_TLS_VERIFY=False))
    context = session().tls_context
    assert context.check_hostname is False
    assert context.verify_mode == mailing.ssl.CERT_NONE


def test_use_ssl_email_maps_to_required_when_starttls_absent():
    FakeSMTP.offer_starttls = False
    send(make_app(SCALARGIS_USE_SSL_EMAIL=True))
    assert 'send' not in session().calls


def test_explicit_starttls_wins_over_use_ssl_email():
    FakeSMTP.offer_starttls = False
    send(make_app(SCALARGIS_USE_SSL_EMAIL=True, SCALARGIS_SMTP_STARTTLS='auto'))
    assert 'send' in session().calls


def test_invalid_starttls_mode_refuses(caplog):
    assert send(make_app(SCALARGIS_SMTP_STARTTLS='sometimes')) is False
    assert FakeSMTP.instances == []
    assert 'invalid SCALARGIS_SMTP_STARTTLS' in caplog.text


def test_custom_timeout():
    send(make_app(SCALARGIS_SMTP_TIMEOUT=30))
    assert session().timeout == 30


def test_string_port_and_display_sender(monkeypatch):
    app = make_app(SCALARGIS_SMTP_PORT='25', SCALARGIS_SENDER_EMAIL='no-reply <noreply@example.org>',
                   SCALARGIS_SENDER_USERNAME='')
    send(app)
    smtp = session()
    assert smtp.port == 25
    msg, from_addr, _ = smtp.sent[0]
    assert from_addr == 'noreply@example.org'
    assert msg['From'] == 'no-reply <noreply@example.org>'


def test_sender_username_is_display_name():
    send(make_app(SCALARGIS_SENDER_USERNAME='Sistema Nacional'))
    msg, from_addr, _ = session().sent[0]
    assert from_addr == 'no-reply@example.org'
    assert msg['From'] == 'Sistema Nacional <no-reply@example.org>'


def test_sender_username_as_address_fallback():
    send(make_app(SCALARGIS_SENDER_EMAIL=..., SCALARGIS_SENDER_USERNAME='info@example.org'))
    _, from_addr, _ = session().sent[0]
    assert from_addr == 'info@example.org'


def test_no_sender_refuses():
    assert send(make_app(SCALARGIS_SENDER_EMAIL=...)) is False
    assert FakeSMTP.instances == []


def test_smtp_not_configured_skips():
    assert send(make_app(SCALARGIS_SMTP_SERVER=...)) is False
    assert FakeSMTP.instances == []


def test_one_session_one_message_for_many_recipients():
    send(make_app(), recipients=['a@example.org', 'b@example.org'])
    smtp = session()
    assert len(smtp.sent) == 1
    msg, _, to_addrs = smtp.sent[0]
    assert to_addrs == ['a@example.org', 'b@example.org']
    assert msg['To'] == 'a@example.org, b@example.org'


def test_partial_refusal_is_logged(caplog):
    FakeSMTP.refused = {'b@example.org': (550, b'no such user')}
    send(make_app(), recipients=['a@example.org', 'b@example.org'])
    assert 'recipient refused to=b@example.org code=550' in caplog.text


def test_no_recipients_refuses():
    assert send(make_app(), recipients=[]) is False
    assert FakeSMTP.instances == []


def test_db_rows_override_config_and_parse_bool(monkeypatch):
    monkeypatch.setattr(mailing, 'db', FakeDb([
        row('smtp_server', 'db-relay.example.org'),
        row('smtp_port', '2525'),
        row('use_ssl_email', 'True'),
    ]))
    with make_app().app_context():
        settings = mailing.get_mail_settings()
    assert settings['smtp_server'] == 'db-relay.example.org'
    assert settings['smtp_port'] == '2525'
    assert settings['use_ssl_email'] is True


@pytest.mark.parametrize('value, expected', [('false', False), ('FALSE', False), ('true', True), ('bogus', False)])
def test_db_use_ssl_email_values(monkeypatch, value, expected):
    monkeypatch.setattr(mailing, 'db', FakeDb([row('use_ssl_email', value)]))
    with make_app().app_context():
        settings = mailing.get_mail_settings()
    assert settings['use_ssl_email'] is expected


def test_db_empty_value_keeps_config(monkeypatch):
    monkeypatch.setattr(mailing, 'db', FakeDb([row('smtp_server', '')]))
    with make_app().app_context():
        assert mailing.get_mail_settings()['smtp_server'] == 'mail.example.org'


def test_send_mail_signature_unchanged():
    params = list(inspect.signature(mailing.send_mail).parameters)
    assert params == ['app', 'receiver_email', 'subject', 'message_html', 'message_text', 'attachments']


def test_send_mail_wrapper_sends(tmp_path):
    attachment = tmp_path / 'report.txt'
    attachment.write_text('data')
    app = make_app()
    with app.test_request_context():
        mailing.send_mail(app, ['a@example.org'], 'Confirmação de envio', '<p>Olá</p>', 'Olá',
                          attachments=[{'filepath': str(attachment), 'filename': 'report.txt'}])
    msg, _, to_addrs = session().sent[0]
    assert to_addrs == ['a@example.org']
    parsed = message_from_string(msg.as_string())
    assert parsed['Subject'].startswith('=?utf-8?')
    types = [p.get_content_type() for p in parsed.walk()]
    assert types == ['multipart/alternative', 'text/plain', 'text/html', 'application/octet-stream']


def test_send_mail_without_app_context():
    mailing.send_mail(make_app(), ['a@example.org'], 'subject', '<p>x</p>')
    assert 'send' in session().calls


def test_inline_images_build_related_tree(tmp_path):
    logo = tmp_path / 'logo.png'
    logo.write_bytes(b'\x89PNG\r\n\x1a\n')
    send(make_app(), inline_images=[{'cid': 'logo', 'filepath': str(logo), 'mimetype': 'image/png'}])
    msg, _, _ = session().sent[0]
    types = [p.get_content_type() for p in msg.walk()]
    assert types == ['multipart/related', 'multipart/alternative', 'text/html', 'image/png']
    assert msg.get_payload()[1]['Content-ID'] == '<logo>'
