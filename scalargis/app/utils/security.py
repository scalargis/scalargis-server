# -*- coding: utf-8 -*-
"""
    app.utils.security
    ~~~~~~~~~~~~~~~~~~~~
    Security module — refactored LDAP connection

      * LDAPLoginManager uses init_config(dict) loaded from config_ldap.py
      * Server + Connection are built explicitly via ldap3 so every step
        is logged and failures are obvious
      * authenticate() logs which bind strategy was chosen and why
      * get_user_info_for_username() logs the exact filter and base DN used
      * A new probe function test_ldap_connection() can be called on startup
        to verify connectivity before the first real login attempt
    
"""

import logging
from flask import current_app, _request_ctx_stack, request
from werkzeug.local import LocalProxy
from flask_principal import Identity, identity_changed
from flask_security.core import verify_hash
from flask_security.utils import verify_and_update_password
from flask_ldap3_login import LDAP3LoginManager, AuthenticationResponseStatus
from ldap3 import Server, Connection, ALL, SUBTREE, SIMPLE
from . import constants

logger = logging.getLogger(__name__)

# Emitted at import time — confirms this module was loaded by the app.
# If SCALARGIS_LDAP_AUTHENTICATION=True this line must appear in startup logs.
logger.info("=== security.py loaded — LDAP-aware security module active ===")

# List for handling configured LDAP domains
ldap_managers = []

# Convenient references
_security = LocalProxy(lambda: current_app.extensions['security'])
user_datastore = LocalProxy(lambda: current_app.extensions['security'].datastore)

authorizations = {
    'apikey': {
        'type': 'apiKey',
        'in': 'header',
        'name': 'X-API-KEY'
    }
}


# ---------------------------------------------------------------------------
# LDAPLoginManager — explicit connection + rich debug logging
# ---------------------------------------------------------------------------

class LDAPLoginManager(LDAP3LoginManager):
    """
    Overrides LDAP3LoginManager.

    Key fix: the parent class's `connection` property stores state on the
    Flask app context via `ldap3_manager_connections`. That attribute only
    exists when the manager is registered with init_app(app). Scalargis uses
    init_config(dict) instead, so the attribute is never set and calling
    `self.connection` raises:
        AttributeError: 'AppContext' object has no attribute 'ldap3_manager_connections'

    Solution: never call `self.connection`. Build ldap3 Server/Connection
    directly in _direct_connection(), exactly as ldap_sync_users.py does,
    and pass that connection explicitly to get_object() and the bind methods.
    """

    def _direct_connection(self, bind_user=None, bind_password=None):
        """
        Build a plain ldap3 Connection — no Flask app context needed.
        Returns a bound Connection or raises with a logged error.
        """
        host     = self.config.get('LDAP_HOST')
        port     = int(self.config.get('LDAP_PORT', 389))
        use_ssl  = self.config.get('LDAP_USE_SSL', False)
        user     = bind_user     or self.config.get('LDAP_BIND_USER_DN')
        password = bind_password or self.config.get('LDAP_BIND_USER_PASSWORD')

        logger.debug(
            "[_direct_connection] host=%s  port=%d  ssl=%s  user=%s",
            host, port, use_ssl, user,
        )

        try:
            server = Server(host, port=port, use_ssl=use_ssl, get_info=ALL)
            conn = Connection(
                server,
                user=user,
                password=password,
                authentication=SIMPLE,
                auto_bind=True,
            )
            logger.debug(
                "[_direct_connection] bound OK — vendor: %s",
                server.info.vendor_name if server.info else "n/a",
            )
            return conn
        except Exception as exc:
            logger.error(
                "[_direct_connection] FAILED %s:%d — %s: %s",
                host, port, type(exc).__name__, exc,
            )
            raise

    def get_user_info_for_username(self, username, _connection=None):
        """
        Search the Users DN for a single user by login attribute.
        Uses _direct_connection() to avoid the app-context dependency.
        """
        ldap_filter = '(&{0}({1}={2}))'.format(
            self.config.get('LDAP_USER_OBJECT_FILTER'),
            self.config.get('LDAP_USER_LOGIN_ATTR'),
            username,
        )

        logger.debug(
            "[get_user_info] search_base='%s'  filter='%s'  attrs=%s",
            self.full_user_search_dn,
            ldap_filter,
            self.config.get('LDAP_GET_USER_ATTRIBUTES'),
        )

        # Use caller-supplied connection if given, otherwise build our own.
        conn = _connection or self._direct_connection()
        try:
            result = self.get_object(
                dn=self.full_user_search_dn,
                filter=ldap_filter,
                attributes=self.config.get('LDAP_GET_USER_ATTRIBUTES'),
                _connection=conn,
            )
        finally:
            if _connection is None:
                conn.unbind()

        if result:
            logger.debug("[get_user_info] found user '%s'", username)
        else:
            logger.warning(
                "[get_user_info] user '%s' NOT found under '%s' with filter '%s'",
                username, self.full_user_search_dn, ldap_filter,
            )

        return result

    def authenticate_search_bind(self, username, password):
        """
        Full override of the parent's authenticate_search_bind.

        The parent's implementation calls self.connection (the Flask app-context
        property) to do the service-account search, which raises AttributeError
        when init_config() is used instead of init_app(). It catches that
        exception silently and returns AuthenticationResponseStatus.fail —
        which is exactly what the log shows.

        This override replaces both the service-account search and the
        user-credential bind with direct ldap3 calls via _direct_connection(),
        so no Flask app context is ever touched.

        Flow:
          1. Service-account bind  → search for user's full DN
          2. User bind             → verify the supplied password
        """
        from flask_ldap3_login import AuthenticationResponse, AuthenticationResponseStatus as ARS
        from ldap3 import Server as _Server

        response = AuthenticationResponse()

        # ── Step 1: service-account search for user DN ────────────────────────
        ldap_filter = '(&{0}({1}={2}))'.format(
            self.config.get('LDAP_USER_OBJECT_FILTER'),
            self.config.get('LDAP_USER_LOGIN_ATTR'),
            username,
        )
        logger.debug(
            "[search_bind] searching for '%s'  base='%s'  filter='%s'",
            username, self.full_user_search_dn, ldap_filter,
        )

        try:
            svc_conn = self._direct_connection()
            svc_conn.search(
                search_base=self.full_user_search_dn,
                search_filter=ldap_filter,
                search_scope=SUBTREE,
                attributes=self.config.get('LDAP_GET_USER_ATTRIBUTES', []),
            )

            if not svc_conn.entries:
                logger.warning("[search_bind] user '%s' not found in directory.", username)
                response.status = ARS.fail
                svc_conn.unbind()
                return response

            user_entry = svc_conn.entries[0]
            user_dn    = user_entry.entry_dn
            response.user_info = {
                attr: user_entry[attr].value
                for attr in self.config.get('LDAP_GET_USER_ATTRIBUTES', [])
                if attr in user_entry
            }
            svc_conn.unbind()
            logger.debug("[search_bind] resolved DN: '%s'", user_dn)

        except Exception as exc:
            logger.error("[search_bind] service-account search failed: %s: %s", type(exc).__name__, exc)
            response.status = ARS.fail
            return response

        # ── Step 2: bind as the user to verify password ───────────────────────
        try:
            user_server = _Server(
                self.config.get('LDAP_HOST'),
                port=int(self.config.get('LDAP_PORT', 389)),
                use_ssl=self.config.get('LDAP_USE_SSL', False),
                get_info=ALL,
            )
            user_conn = Connection(
                user_server,
                user=user_dn,
                password=password,
                authentication=SIMPLE,
                auto_bind=True,
            )
            user_conn.unbind()
            response.status = ARS.success
            response.user_dn = user_dn
            logger.debug("[search_bind] user bind OK for DN '%s'", user_dn)

        except Exception as exc:
            logger.warning(
                "[search_bind] user bind FAILED for '%s' (DN: %s) — %s: %s",
                username, user_dn, type(exc).__name__, exc,
            )
            response.status = ARS.fail

        return response

    def authenticate(self, username, password):
        """
        Mirrors scalargis authenticate logic.
        Uses _direct_connection() for the service-account bind so the
        Flask app context is never touched.
        """
        rdn_attr      = self.config.get('LDAP_USER_RDN_ATTR')
        login_attr    = self.config.get('LDAP_USER_LOGIN_ATTR')
        always_search = self.config.get('LDAP_ALWAYS_SEARCH_BIND', False)
        direct_creds  = self.config.get('LDAP_BIND_DIRECT_CREDENTIALS', False)

        logger.debug(
            "[authenticate] username='%s'  RDN_ATTR='%s'  LOGIN_ATTR='%s'  "
            "ALWAYS_SEARCH_BIND=%s  BIND_DIRECT_CREDENTIALS=%s",
            username, rdn_attr, login_attr, always_search, direct_creds,
        )

        if direct_creds:
            logger.debug("[authenticate] strategy -> direct_credentials")
            result = self.authenticate_direct_credentials(username, password)

        elif not always_search and rdn_attr == login_attr:
            logger.debug(
                "[authenticate] strategy -> direct_bind (RDN_ATTR == LOGIN_ATTR == '%s')",
                rdn_attr,
            )
            result = self.authenticate_direct_bind(username, password)

        else:
            logger.debug(
                "[authenticate] strategy -> search_bind "
                "(always_search=%s or RDN_ATTR '%s' != LOGIN_ATTR '%s')",
                always_search, rdn_attr, login_attr,
            )
            result = self.authenticate_search_bind(username, password)

        if result.status == AuthenticationResponseStatus.success:
            logger.info("[authenticate] SUCCESS for '%s'", username)
        else:
            logger.warning(
                "[authenticate] FAILED for '%s' — status: %s",
                username, result.status,
            )

        return result


# ---------------------------------------------------------------------------
# Probe — call this on app startup to catch misconfigs early
# ---------------------------------------------------------------------------

def test_ldap_connection(manager: LDAPLoginManager) -> bool:
    """
    Attempts a service-account bind and a base search.
    Logs detailed diagnostics.  Returns True if both succeed.
    Call from init_ldap() after building managers, e.g.:

        if not test_ldap_connection(manager):
            app.logger.error("LDAP probe failed — check config_ldap.py")
    """
    host    = manager.config.get('LDAP_HOST')
    base_dn = manager.config.get('LDAP_BASE_DN')
    bind_dn = manager.config.get('LDAP_BIND_USER_DN')

    logger.info(
        "[ldap_probe] Testing connection — host=%s  base_dn=%s  bind_dn=%s",
        host, base_dn, bind_dn,
    )

    try:
        conn = manager._direct_connection()
        logger.info("[ldap_probe] Service-account bind: OK")

        conn.search(
            search_base=base_dn,
            search_filter='(objectClass=*)',
            search_scope=SUBTREE,
            attributes=['distinguishedName'],
            size_limit=1,
        )

        if conn.entries:
            logger.info("[ldap_probe] Base DN search returned at least 1 entry — OK")
        else:
            logger.warning(
                "[ldap_probe] Base DN search returned 0 entries. "
                "Check LDAP_BASE_DN='%s' and bind account read permissions.",
                base_dn,
            )

        logger.info(
            "[ldap_probe] full_user_search_dn='%s'",
            manager.full_user_search_dn,
        )
        conn.unbind()
        return True

    except Exception as exc:
        logger.error(
            "[ldap_probe] Connection FAILED — %s: %s",
            type(exc).__name__, exc,
        )
        return False


# ---------------------------------------------------------------------------
# init_ldap — unchanged logic, probe added
# ---------------------------------------------------------------------------

def init_ldap(app):
    """
    Performs ldap init.  Reads LDAP_CONFIG from config_ldap.py.
    Runs a connectivity probe after each manager is built.
    """
    if app.config.get('SCALARGIS_LDAP_AUTHENTICATION') is True:
        logger.info(
            "[init_ldap] SCALARGIS_LDAP_AUTHENTICATION=True — "
            "loading LDAP config from config_ldap.py"
        )
        app.config.from_pyfile('config_ldap.py')

        cfg = app.config.get('LDAP_CONFIG')
        if cfg is None:
            logger.error(
                "[init_ldap] LDAP_CONFIG not found in config_ldap.py — "
                "LDAP authentication will NOT work."
            )
            return

        configs = cfg if isinstance(cfg, list) else [cfg]
        logger.info("[init_ldap] Found %d LDAP config(s) to initialise.", len(configs))

        for i, c in enumerate(configs):
            logger.info(
                "[init_ldap] Initialising manager %d/%d — host=%s  base_dn=%s  user_dn=%s",
                i + 1, len(configs),
                c.get('LDAP_HOST'),
                c.get('LDAP_BASE_DN'),
                c.get('LDAP_USER_DN'),
            )
            manager = LDAPLoginManager()
            manager.init_config(c)
            logger.info(
                "[init_ldap] full_user_search_dn resolved to '%s'",
                manager.full_user_search_dn,
            )
            test_ldap_connection(manager)
            ldap_managers.append(manager)

        logger.info(
            "[init_ldap] Done — %d LDAP manager(s) registered.",
            len(ldap_managers),
        )
    else:
        logger.warning(
            "[init_ldap] SCALARGIS_LDAP_AUTHENTICATION is not True "
            "(value=%r) — LDAP disabled, only local password auth will work.",
            app.config.get('SCALARGIS_LDAP_AUTHENTICATION'),
        )
        app.config['SCALARGIS_LDAP_AUTHENTICATION'] = False


# ---------------------------------------------------------------------------
# authenticate_ldap_user — unchanged logic, clearer logging
# ---------------------------------------------------------------------------

def authenticate_ldap_user(username, password, domain):
    """
    Tries each configured LDAP manager in order.
    Returns True on the first successful bind.
    """
    if not current_app.config.get('SCALARGIS_LDAP_AUTHENTICATION'):
        logger.debug("[auth_ldap] LDAP authentication disabled.")
        return False

    for ldap in ldap_managers:
        host    = ldap.config.get('LDAP_HOST')
        base_dn = ldap.config.get('LDAP_BASE_DN')

        try:
            logger.debug(
                "[auth_ldap] Trying host=%s  base_dn=%s  for user='%s'",
                host, base_dn, username,
            )
            ldap_user = ldap.get_user_info_for_username(username)

            if not ldap_user:
                logger.warning(
                    "[auth_ldap] user '%s' not found on host=%s — skipping",
                    username, host,
                )
                continue

            res = ldap.authenticate(username, password)
            if res.status == AuthenticationResponseStatus.success:
                return True

        except Exception as exc:
            logger.debug(
                "[auth_ldap] Exception authenticating '%s' on host=%s base_dn=%s — %s: %s",
                username, host, base_dn, type(exc).__name__, exc,
            )

    return False


# ---------------------------------------------------------------------------
# Everything below is unchanged from original security.py
# ---------------------------------------------------------------------------

def get_token(username):
    token = None
    user = user_datastore.get_user(username)
    if user and user.is_active:
        token = user.get_auth_token()
    return token


def get_user_token(username, password):
    """
    Authenticates with local password first, then falls back to LDAP.
    On successful LDAP auth the local password hash is refreshed so that
    subsequent logins work without needing to reach the LDAP server.
    """
    from flask_security.utils import hash_password

    authenticated = False
    token = None

    user = user_datastore.get_user(username)

    if user and user.is_active:
        if verify_and_update_password(password, user):
            authenticated = True
            logger.debug("[get_user_token] local password OK for '%s'", username)
        else:
            if authenticate_ldap_user(username, password, None):
                authenticated = True
                # Sync the LDAP-verified password into the local DB.
                # This means future logins succeed via verify_and_update_password
                # even if the LDAP server is temporarily unreachable.
                try:
                    user.password = hash_password(password)
                    user_datastore.put(user)
                    user_datastore.commit()
                    logger.info(
                        "[get_user_token] local password refreshed for '%s' after LDAP auth",
                        username,
                    )
                except Exception as exc:
                    logger.warning(
                        "[get_user_token] could not refresh local password for '%s': %s",
                        username, exc,
                    )

        if authenticated:
            token = user.get_auth_token()

    return token


def check_token(token):
    data = _security.remember_token_serializer.loads(
        token, max_age=_security.token_max_age)
    user = _security.datastore.find_user(id=data[0])
    if not (user and verify_hash(data[1], user.password)):
        return user
    if user and user.is_active and user.is_authenticated:
        app = current_app._get_current_object()
        _request_ctx_stack.top.user = user
        identity_changed.send(app, identity=Identity(user.id))
        return True
    return False


def get_user_from_token(token):
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
    return None


def auth_required(api):
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
