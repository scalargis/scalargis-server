"""
Password complexity policy for ScalarGIS.

A single place that defines what a valid password is, and one helper to enforce
it at every password-setting choke point (self-service register/reset and admin
user create/update). Follows the same house style as ``rate_limit.py`` and
``security_headers.py``: a ``_DEFAULTS`` table, lazy reads from
``current_app.config`` so a deployment can re-tune any rule without code changes,
and no external dependencies.

``validate_password`` is a pure, testable function. ``enforce_password_policy``
wraps it with ``flask_restx.abort(400, ...)`` -- the raised ``HTTPException``
bypasses ``marshal_with`` and is rendered as JSON by Flask-RESTX, so the same
call works whether the surrounding endpoint marshals its response (admin
user CRUD) or not (self-service flows).
"""
import re

from flask import current_app
from flask_restx import abort

# Per-rule defaults. Each is overridable via ``SCALARGIS_PASSWORD_<KEY>`` config.
_DEFAULTS = {
    'MIN_LENGTH': 12,
    'REQUIRE_UPPERCASE': True,
    'REQUIRE_LOWERCASE': True,
    'REQUIRE_DIGIT': True,
    'REQUIRE_SPECIAL': True,
}


def _get(suffix):
    val = current_app.config.get('SCALARGIS_PASSWORD_{}'.format(suffix))
    return val if val is not None else _DEFAULTS.get(suffix)


def validate_password(password):
    """Check ``password`` against the configured policy.

    Returns ``(True, None, None)`` when it complies, otherwise
    ``(False, 'password_policy_violation', failed_rules)`` where
    ``failed_rules`` is a list of rule identifiers.
    """
    pw = password or ''
    failed_rules = []

    min_length = _get('MIN_LENGTH')
    if len(pw) < min_length:
        failed_rules.append('min_length')
    if _get('REQUIRE_UPPERCASE') and not re.search(r'[A-Z]', pw):
        failed_rules.append('uppercase')
    if _get('REQUIRE_LOWERCASE') and not re.search(r'[a-z]', pw):
        failed_rules.append('lowercase')
    if _get('REQUIRE_DIGIT') and not re.search(r'[0-9]', pw):
        failed_rules.append('digit')
    if _get('REQUIRE_SPECIAL') and not re.search(r'[^A-Za-z0-9]', pw):
        failed_rules.append('special')

    if failed_rules:
        return False, 'password_policy_violation', failed_rules
    return True, None, None


def enforce_password_policy(password):
    """Validate ``password``; on failure ``abort(400)`` with an i18n key.

    The error body matches the rest of these endpoints
    (``{status, error, message}``). Because ``abort`` raises an
    ``HTTPException``, it short-circuits before any ``marshal_with`` serialiser
    runs, so this is safe to call from both self-service and admin DAO paths.
    """
    valid, msg, failed_rules = validate_password(password)
    if not valid:
        abort(400, msg, status=400, error=True, failed_rules=failed_rules)
