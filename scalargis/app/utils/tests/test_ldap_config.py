"""Tests for the LDAP manager config and the identity setting conversion."""
import pytest

from app.utils import security

SEARCH_BIND = {
    'LDAP_HOST': 'ldap.example.com', 'LDAP_BASE_DN': 'dc=example,dc=com', 'LDAP_USER_DN': 'ou=Users',
    'LDAP_USER_RDN_ATTR': 'cn', 'LDAP_USER_LOGIN_ATTR': 'sAMAccountName',
    'LDAP_BIND_USER_DN': 'cn=svc,dc=example,dc=com', 'LDAP_BIND_USER_PASSWORD': 'pw',
}


def manager(config):
    m = security.LDAPLoginManager()
    m.init_config(config)
    return m


def test_init_config_keeps_values_over_defaults():
    m = manager(SEARCH_BIND)
    assert m.config['LDAP_USER_LOGIN_ATTR'] == 'sAMAccountName'
    assert m.config['LDAP_PORT'] == 389
    assert m.config['LDAP_USER_OBJECT_FILTER'] == '(objectclass=person)'


def test_init_config_does_not_change_the_given_dict():
    config = dict(SEARCH_BIND)
    manager(config)
    assert config == SEARCH_BIND


def test_full_user_search_dn():
    assert manager(SEARCH_BIND).full_user_search_dn == 'ou=Users,dc=example,dc=com'
    assert manager({**SEARCH_BIND, 'LDAP_USER_DN': ' '}).full_user_search_dn == 'dc=example,dc=com'


def test_managers_keep_their_own_config():
    a = manager(SEARCH_BIND)
    b = manager({**SEARCH_BIND, 'LDAP_BASE_DN': 'dc=other,dc=com'})
    assert a.full_user_search_dn == 'ou=Users,dc=example,dc=com'
    assert b.full_user_search_dn == 'ou=Users,dc=other,dc=com'


def test_always_search_bind_is_accepted():
    m = manager({**SEARCH_BIND, 'LDAP_USER_LOGIN_ATTR': 'cn', 'LDAP_ALWAYS_SEARCH_BIND': True})
    assert security.ldap_bind_mode(m.config) == 'search_bind'


@pytest.mark.parametrize('config, mode', [
    ({**SEARCH_BIND, 'LDAP_USER_LOGIN_ATTR': 'cn'}, 'direct_bind'),
    ({k: v for k, v in SEARCH_BIND.items() if k not in ('LDAP_USER_RDN_ATTR', 'LDAP_USER_LOGIN_ATTR')}, 'direct_bind'),
    ({**SEARCH_BIND, 'LDAP_BIND_DIRECT_CREDENTIALS': True}, 'direct_credentials'),
])
def test_init_config_refuses_direct_modes(config, mode):
    with pytest.raises(ValueError, match=mode):
        manager(config)


def test_identity_attributes_converts_the_old_form():
    value = security.identity_attributes(('username', 'email'))
    assert [list(v) for v in value] == [['username'], ['email']]
    for v in value:
        opts = next(iter(v.values()))
        assert opts['case_insensitive'] is True
        assert opts['mapper'] is security.uia_plain_mapper


def test_identity_attributes_keeps_the_new_form():
    value = [{'email': {'case_insensitive': True}}]
    assert security.identity_attributes(value) is value


def test_uia_plain_mapper():
    assert security.uia_plain_mapper('Admin') == 'Admin'
    assert security.uia_plain_mapper('') is None
