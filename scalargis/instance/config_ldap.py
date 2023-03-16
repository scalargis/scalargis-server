ldap_cfg = [{
        # Hostname of your LDAP Server
        'LDAP_HOST': '127.0.0.1',
        # Base DN of your directory
        'LDAP_BASE_DN': 'dc=domain_name,dc=pt',
        # Users DN to be prepended to the Base DN
        'LDAP_USER_DN': '',
        # Groups DN to be prepended to the Base DN
        'LDAP_GROUP_DN': '',
        # The RDN attribute for your user schema on LDAP
        'LDAP_USER_RDN_ATTR': 'cn',
        # The Attribute you want users to authenticate to LDAP with.
        'LDAP_USER_LOGIN_ATTR': 'sAMAccountName',
        # The Username to bind to LDAP with
        'LDAP_BIND_USER_DN': 'mail@domain_name.pt',
        # The Password to bind to LDAP with
        'LDAP_BIND_USER_PASSWORD': 'password',
        'LDAP_USER_SEARCH_SCOPE': 'SUBTREE'
        # ldap_config['LDAP_USER_OBJECT_FILTER'] = '(objectClass=user)'
    }]

LDAP_CONFIG = ldap_cfg


