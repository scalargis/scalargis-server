# -*- coding: utf-8 -*-
"""
    app.utils.security
    ~~~~~~~~~~~~~~~~~~~~
    Security module
    :copyright: (c) 2017 by WKT-SI.
    :license: XXX see LICENSE for more details.
"""

import logging
from flask import current_app, _request_ctx_stack, request
from werkzeug.local import LocalProxy
from flask_principal import Identity, identity_changed
from flask_security.core import verify_hash
from flask_security.utils import verify_and_update_password
from flask_ldap3_login import LDAP3LoginManager, AuthenticationResponseStatus
from app.utils.decorators import async_task
from . import constants

# List for handling configured AD Domains
ldap_managers = []

# Convenient references
_security = LocalProxy(lambda: current_app.extensions['security'])

# Reference for flask-security datastore
user_datastore = LocalProxy(lambda: current_app.extensions['security'].datastore)

authorizations = {
    'apikey': {
        'type': 'apiKey',
        'in': 'header',
        'name': 'X-API-KEY'
    }
}


def init_ldap(app):
    """
    Performs ldap init.

    Args:
        app: flask application
    """

    if 'SCALARGIS_LDAP_AUTHENTICATION' in app.config and app.config.get('SCALARGIS_LDAP_AUTHENTICATION') is True:
        # Load the ldap configuration from config file
        app.config.from_pyfile('config_ldap.py')

        cfg = app.config.get('LDAP_CONFIG')

        if isinstance(cfg, list):
            for c in cfg:
                manager = LDAPLoginManager()
                manager.init_config(c)
                ldap_managers.append(manager)
        else:
            manager = LDAPLoginManager()
            manager.init_config(cfg)
            ldap_managers.append(manager)
    else:
        app.config['SCALARGIS_LDAP_AUTHENTICATION'] = False


def authenticate_ldap_user(username, password, domain):
    """
    Authenticates user on all configured ldap or just on the ldap from the specified domain.

    Args:
        username: Username.
        password: Password.
        domain: Domain.
    Returns:
        boolean: True if successfully authenticated
    """
    logger = logging.getLogger(__name__)

    if current_app.config.get('SCALARGIS_LDAP_AUTHENTICATION') is True:
        for ldap in ldap_managers:
            try:
                ldap_user = ldap.get_user_info_for_username(username)
                if ldap_user:
                    res = ldap.authenticate(username, password)
                    if res.status and res.status == AuthenticationResponseStatus.success:
                        return True
            except:
                logger.debug('Could not authenticate user {0} on Host: {1}, Base DN: {2}.'.
                             format(username, ldap.config.get('LDAP_HOST'), ldap.config.get('LDAP_BASE_DN')))

    return False


def get_user_token(username, password):
    """
    Authenticates user with the specified credentials and returns the authentication token.

    Args:
        username (str): Username.
        password (str): Password.
    Returns:
        string: Authentication token
    """

    authenticated = False
    token = None

    user = user_datastore.get_user(username)

    if user and user.is_active:
        if verify_and_update_password(password, user):
            authenticated = True
        else:
            if authenticate_ldap_user(username, password, None):
                authenticated = True

        if authenticated:
            token = user.get_auth_token()

    return token


def check_token(token):
    #header_key = _security.token_authentication_header
    #args_key = _security.token_authentication_key
    #header_token = request.headers.get(header_key, None)
    #token = request.args.get(args_key, header_token)
    #if request.get_json(silent=True):
    #    if not isinstance(request.json, list):
    #        token = request.json.get(args_key, token)

    #user = _security.login_manager.token_callback(token)
    data = _security.remember_token_serializer.loads(
        token, max_age=_security.token_max_age)
    user = _security.datastore.find_user(id=data[0])
    if not(user and verify_hash(data[1], user.password)):
        return user

    if user and user.is_active and user.is_authenticated:
        app = current_app._get_current_object()
        _request_ctx_stack.top.user = user
        identity_changed.send(app, identity=Identity(user.id))
        return True

    return False


def get_user_from_token(token):
    #user = _security.login_manager.token_callback(token)
    user = None

    data = _security.remember_token_serializer.loads(
        token, max_age=_security.token_max_age)
    user = _security.datastore.find_user(id=data[0])
    if not (user and verify_hash(data[1], user.password)):
        user = None

    if user and user.is_active and user.is_authenticated:
        return user

    return None


def get_user_from_auth_token(token):
    user = _security.datastore.find_user(auth_token=token)

    if user and user.is_active and user.is_authenticated:
        return user

    return None


def get_api_user(request):
    if 'X-API-KEY' in request.headers:
        token = request.headers['X-API-KEY']
        user = get_user_from_token(token)
        return user
    else:
        return None


def auth_required(api):
    """
    Decorator - requires authentication token.
    """
    def real_decorator(function):
        func = api.doc(security='apikey')(function)

        def check_auth(*args, **kwargs):
            if 'X-API-KEY' not in request.headers:
                api.abort(401, 'API key required')
            key = request.headers['X-API-KEY']
            if not check_token(key):
                api.abort(401, 'Bad credentials')
            return func(*args, **kwargs)
        return check_auth

    return real_decorator


def get_user_roles(user):
    roles = [constants.ROLE_ANONYMOUS]

    if user and user.is_authenticated:
        for ru in user.roles:
            roles.append(ru.name)
        roles.append(constants.ROLE_AUTHENTICATED)

    return roles


def get_roles_names(roles, add_anonymous=False):
    roles_names = []

    if add_anonymous:
        roles_names = [constants.ROLE_ANONYMOUS]

    for r in roles:
        if r.name not in roles_names:
            roles_names.append(r.name)

    return roles_names


def is_admin_or_manager(user):
    is_admin_manager = False

    if user and user.id > 0:
        for ru in user.roles:
            if ru.name == constants.ROLE_ADMIN or ru.name == constants.ROLE_MANAGER:
                is_admin_manager = True
                break

    return is_admin_manager


class LDAPLoginManager(LDAP3LoginManager):
    """
        Overrides several methods of LDAP3LoginManager Class
    """

    def get_user_info_for_username(self, username, _connection=None):
        """
        Gets info about a user at a specified username by searching the
        Users DN. Username attribute is the same as specified as
        LDAP_USER_LOGIN_ATTR.

        Args:
            username (str): Username of the user to search for.
            _connection (ldap3.Connection): A connection object to use when
                searching. If not given, a temporary connection will be
                created, and destroyed after use.
        Returns:
            dict: A dictionary of the user info from LDAP
        """
        ldap_filter = '(&{0}({1}={2}))'.format(
            self.config.get('LDAP_USER_OBJECT_FILTER'),
            self.config.get('LDAP_USER_LOGIN_ATTR'),
            username
        )

        return self.get_object(
            dn=self.full_user_search_dn,
            filter=ldap_filter,
            attributes=self.config.get("LDAP_GET_USER_ATTRIBUTES"),
            _connection=_connection,
        )

    def authenticate(self, username, password):
        """
        An abstracted authentication method. Decides whether to perform a
        direct bind or a search bind based upon the login attribute configured
        in the config.

        Args:
            username (str): Username of the user to bind
            password (str): User's password to bind with.

        Returns:
            AuthenticationResponse

        """
        if self.config.get('LDAP_BIND_DIRECT_CREDENTIALS'):
            result = self.authenticate_direct_credentials(username, password)

        elif not self.config.get('LDAP_ALWAYS_SEARCH_BIND') and \
                        self.config.get('LDAP_USER_RDN_ATTR') == \
                        self.config.get('LDAP_USER_LOGIN_ATTR'):
            # Since the user's RDN is the same as the login field,
            # we can do a direct bind.
            result = self.authenticate_direct_bind(username, password)
        else:
            # We need to search the User's DN to find who the user is (and
            # their DN) so we can try bind with their password.
            result = self.authenticate_search_bind(username, password)

        return result
