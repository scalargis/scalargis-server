"""Tests for the LDAP bind modes, the filter escape, and the TLS settings, on a fake ldap3."""
import ssl
from types import SimpleNamespace

import pytest
from flask import Flask
from flask_ldap3_login import AuthenticationResponseStatus
from ldap3 import Tls, AUTO_BIND_NO_TLS, AUTO_BIND_TLS_BEFORE_BIND
from ldap3.core.exceptions import LDAPBindError

from app.utils import security

SVC_DN = 'cn=svc,dc=example,dc=com'
USER_DN = 'cn=John Doe,ou=Users,dc=example,dc=com'
PASSWORDS = {
    SVC_DN: 'svc-pw',
    USER_DN: 'secret',
    'uid=jdoe,ou=people,dc=example,dc=com': 'secret',
    'jdoe@example.com': 'secret',
}

SEARCH_BIND = {
    'LDAP_HOST': 'ldap.example.com', 'LDAP_BASE_DN': 'dc=example,dc=com', 'LDAP_USER_DN': 'ou=Users',
    'LDAP_USER_RDN_ATTR': 'cn', 'LDAP_USER_LOGIN_ATTR': 'sAMAccountName',
    'LDAP_BIND_USER_DN': SVC_DN, 'LDAP_BIND_USER_PASSWORD': 'svc-pw',
}
DIRECT_BIND = {
    'LDAP_HOST': 'ldap.example.com', 'LDAP_BASE_DN': 'dc=example,dc=com', 'LDAP_USER_DN': 'ou=people',
    'LDAP_USER_RDN_ATTR': 'uid', 'LDAP_USER_LOGIN_ATTR': 'uid',
}
DIRECT_CREDENTIALS = {
    'LDAP_HOST': 'ldap.example.com', 'LDAP_BASE_DN': 'dc=example,dc=com',
    'LDAP_BIND_DIRECT_CREDENTIALS': True, 'LDAP_BIND_DIRECT_SUFFIX': '@example.com',
}
SUCCESS = AuthenticationResponseStatus.success
FAIL = AuthenticationResponseStatus.fail


@pytest.fixture
def ldap(monkeypatch):
    """Replaces ldap3 Server and Connection in the module and records each bind and search."""
    calls = SimpleNamespace(servers=[], binds=[], searches=[])

    class FakeEntry:
        entry_dn = USER_DN

        def __contains__(self, attr):
            return False

    class FakeServer:
        def __init__(self, host, **kwargs):
            self.host, self.kwargs, self.info = host, kwargs, None
            calls.servers.append(self)

    class FakeConnection:
        def __init__(self, server, user=None, password=None, authentication=None, auto_bind=None):
            calls.binds.append((user, password, auto_bind))
            if not password or PASSWORDS.get(user) != password:
                raise LDAPBindError('invalidCredentials')
            self.entries = []

        def search(self, search_base, search_filter, **kwargs):
            calls.searches.append(search_filter)
            if search_filter == '(&(objectclass=person)(sAMAccountName=jdoe))':
                self.entries = [FakeEntry()]

        def unbind(self):
            pass

    monkeypatch.setattr(security, 'Server', FakeServer)
    monkeypatch.setattr(security, 'Connection', FakeConnection)
    return calls


def manager(config):
    m = security.LDAPLoginManager()
    m.init_config(config)
    return m


def test_user_filter_escapes_the_username():
    assert manager(SEARCH_BIND)._user_filter('*)(cn=*') == \
        '(&(objectclass=person)(sAMAccountName=\\2a\\29\\28cn=\\2a))'


def test_search_bind_finds_the_dn_then_binds_as_the_user(ldap):
    result = manager(SEARCH_BIND).authenticate('jdoe', 'secret')
    assert result.status == SUCCESS
    assert result.user_dn == USER_DN
    assert [b[0] for b in ldap.binds] == [SVC_DN, USER_DN]


def test_search_bind_sends_an_escaped_filter(ldap):
    result = manager(SEARCH_BIND).authenticate('*', 'secret')
    assert result.status == FAIL
    assert ldap.searches == ['(&(objectclass=person)(sAMAccountName=\\2a))']
    assert [b[0] for b in ldap.binds] == [SVC_DN]


def test_search_bind_wrong_password(ldap):
    assert manager(SEARCH_BIND).authenticate('jdoe', 'wrong').status == FAIL


def test_direct_bind_needs_no_service_account(ldap):
    result = manager(DIRECT_BIND).authenticate('jdoe', 'secret')
    assert result.status == SUCCESS
    assert ldap.binds == [('uid=jdoe,ou=people,dc=example,dc=com', 'secret', AUTO_BIND_NO_TLS)]
    assert ldap.searches == []


def test_direct_bind_escapes_the_dn(ldap):
    assert manager(DIRECT_BIND).authenticate('jdoe,ou=x', 'secret').status == FAIL
    assert ldap.binds[0][0] == 'uid=jdoe\\,ou\\=x,ou=people,dc=example,dc=com'


def test_direct_credentials_binds_with_prefix_and_suffix(ldap):
    result = manager(DIRECT_CREDENTIALS).authenticate('jdoe', 'secret')
    assert result.status == SUCCESS
    assert [b[0] for b in ldap.binds] == ['jdoe@example.com']


@pytest.mark.parametrize('config', [SEARCH_BIND, DIRECT_BIND, DIRECT_CREDENTIALS])
@pytest.mark.parametrize('password', ['', None])
def test_empty_password_fails_with_no_bind(ldap, config, password):
    assert manager(config).authenticate('jdoe', password).status == FAIL
    assert ldap.binds == []


def test_user_bind_does_not_use_the_service_password(ldap):
    with pytest.raises(LDAPBindError):
        manager(SEARCH_BIND)._direct_connection(USER_DN, '')
    assert ldap.binds == [(USER_DN, '', AUTO_BIND_NO_TLS)]


def test_starttls_runs_before_each_bind(ldap):
    assert manager({**SEARCH_BIND, 'LDAP_USE_TLS': True}).authenticate('jdoe', 'secret').status == SUCCESS
    assert [b[2] for b in ldap.binds] == [AUTO_BIND_TLS_BEFORE_BIND, AUTO_BIND_TLS_BEFORE_BIND]


def test_ldap_tls_dict_builds_a_tls(ldap):
    manager({**DIRECT_BIND, 'LDAP_TLS': {'validate': ssl.CERT_REQUIRED}}).authenticate('jdoe', 'secret')
    tls = ldap.servers[0].kwargs['tls']
    assert isinstance(tls, Tls)
    assert tls.validate == ssl.CERT_REQUIRED


def test_ldap_tls_object_and_none():
    tls = Tls(validate=ssl.CERT_REQUIRED)
    assert security.ldap_tls({'LDAP_TLS': tls}) is tls
    assert security.ldap_tls({}) is None


@pytest.fixture
def ldap_app(monkeypatch):
    app = Flask(__name__)
    app.config['SCALARGIS_LDAP_AUTHENTICATION'] = True
    monkeypatch.setattr(security, 'ldap_managers', [])
    with app.app_context():
        yield security.ldap_managers


def test_authenticate_ldap_user_direct_bind_with_no_service_account(ldap, ldap_app):
    ldap_app.append(manager(DIRECT_BIND))
    assert security.authenticate_ldap_user('jdoe', 'secret', None) is True
    assert ldap.searches == []


def test_authenticate_ldap_user_tries_the_next_manager(ldap, ldap_app):
    ldap_app.extend([manager({**SEARCH_BIND, 'LDAP_BIND_USER_PASSWORD': 'bad'}), manager(DIRECT_BIND)])
    assert security.authenticate_ldap_user('jdoe', 'secret', None) is True
    assert [b[0] for b in ldap.binds] == [SVC_DN, 'uid=jdoe,ou=people,dc=example,dc=com']


def test_authenticate_ldap_user_fails_on_every_manager(ldap, ldap_app):
    ldap_app.append(manager(SEARCH_BIND))
    assert security.authenticate_ldap_user('jdoe', 'wrong', None) is False
