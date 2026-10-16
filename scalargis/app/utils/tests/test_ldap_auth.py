from types import SimpleNamespace

import pytest
from flask_ldap3_login import AuthenticationResponseStatus
from ldap3 import AUTO_BIND_TLS_BEFORE_BIND
from ldap3.core.exceptions import LDAPBindError

from app.utils import security

SVC_DN = 'cn=svc,dc=example,dc=com'
USER_DN = 'cn=John Doe,ou=Users,dc=example,dc=com'
PASSWORDS = {SVC_DN: 'svc-pw', USER_DN: 'secret', 'jdoe@example.com': 'secret'}

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
FAIL = AuthenticationResponseStatus.fail


@pytest.fixture
def ldap(monkeypatch):
    calls = SimpleNamespace(binds=[], searches=[])

    class FakeEntry:
        entry_dn = USER_DN

        def __contains__(self, attr):
            return False

    class FakeServer:
        def __init__(self, host, **kwargs):
            self.info = None

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


def test_search_bind_sends_an_escaped_filter(ldap):
    manager(SEARCH_BIND).authenticate('*', 'secret')
    assert ldap.searches == ['(&(objectclass=person)(sAMAccountName=\\2a))']
    assert [b[0] for b in ldap.binds] == [SVC_DN]


def test_direct_bind_escapes_the_dn(ldap):
    manager(DIRECT_BIND).authenticate('jdoe,ou=x', 'secret')
    assert ldap.binds[0][0] == 'uid=jdoe\\,ou\\=x,ou=people,dc=example,dc=com'


@pytest.mark.parametrize('config', [SEARCH_BIND, DIRECT_BIND, DIRECT_CREDENTIALS])
@pytest.mark.parametrize('password', ['', None])
def test_empty_password_fails_with_no_bind(ldap, config, password):
    assert manager(config).authenticate('jdoe', password).status == FAIL
    assert ldap.binds == []


def test_user_bind_does_not_use_the_service_password(ldap):
    with pytest.raises(LDAPBindError):
        manager(SEARCH_BIND)._direct_connection(USER_DN, '')
    assert ldap.binds[0][:2] == (USER_DN, '')


def test_starttls_runs_before_each_bind(ldap):
    manager({**SEARCH_BIND, 'LDAP_USE_TLS': True}).authenticate('jdoe', 'secret')
    assert [b[2] for b in ldap.binds] == [AUTO_BIND_TLS_BEFORE_BIND, AUTO_BIND_TLS_BEFORE_BIND]
