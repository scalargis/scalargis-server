ldap_cfg = [{
        # Hostname of your LDAP Server
        'LDAP_HOST': 'apa.local:389',
        # Base DN of your directory
        'LDAP_BASE_DN': 'ou=APA,ou=Grupos,dc=apa,dc=local',
        # Users DN to be prepended to the Base DN
        'LDAP_USER_DN': '',
        # Groups DN to be prepended to the Base DN
        'LDAP_GROUP_DN': '',
        # The RDN attribute for your user schema on LDAP
        'LDAP_USER_RDN_ATTR': 'cn',
        # The Attribute you want users to authenticate to LDAP with.
        'LDAP_USER_LOGIN_ATTR': 'sAMAccountName',
        # The Username to bind to LDAP with
        'LDAP_BIND_USER_DN': 'cn=ldap,ou=Especiais,dc=apa,dc=local',
        # The Password to bind to LDAP with
        'LDAP_BIND_USER_PASSWORD': 'CrsLHEp2M7NByZpL',
        'LDAP_USER_SEARCH_SCOPE': 'SUBTREE'
        # ldap_config['LDAP_USER_OBJECT_FILTER'] = '(objectClass=user)'
    }]

LDAP_CONFIG = ldap_cfg


