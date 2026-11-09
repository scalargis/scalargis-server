"""API token and mail link token formats, independent of the Flask-Security version."""
import uuid
from datetime import timedelta

from flask import current_app
from itsdangerous import BadData, SignatureExpired, URLSafeTimedSerializer
from passlib.context import CryptContext

REMEMBER_SALT = "remember-salt"
ACTIVATION_SALT = "confirm-salt"
RESET_SALT = "reset-salt"
ACTIVATION_WITHIN_KEY = "SECURITY_CONFIRM_EMAIL_WITHIN"
RESET_WITHIN_KEY = "SECURITY_RESET_PASSWORD_WITHIN"
_DEFAULT_WITHIN = {ACTIVATION_WITHIN_KEY: timedelta(hours=24), RESET_WITHIN_KEY: timedelta(hours=2)}

_hashing = CryptContext(schemes=["sha256_crypt", "hex_md5"], deprecated=["hex_md5"])


def _serializer(salt):
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"], salt=salt)


def _find(user_id):
    from app.database import db
    from app.models.security import User
    try:
        return db.session.get(User, int(user_id))
    except (TypeError, ValueError):
        return None


def _verify(hashed, value):
    try:
        return _hashing.verify(value or "", hashed)
    except (TypeError, ValueError):
        return False


def auth_token(user):
    """Builds the API token: [id, sha256_crypt(password)] signed with remember-salt."""
    return _serializer(REMEMBER_SALT).dumps([str(user.id), _hashing.hash(user.password or "")])


def user_from_auth_token(token, max_age=None):
    """Returns the active user for an API token, or None."""
    try:
        data = _serializer(REMEMBER_SALT).loads(token, max_age=max_age)
    except (BadData, TypeError, ValueError):
        return None
    if not (isinstance(data, list) and len(data) == 2):
        return None
    user = _find(data[0])
    if user and _verify(data[1], user.password) and user.is_active:
        return user
    return None


def within(key):
    """Returns the lifetime of a mail link from a timedelta or a "<n> <unit>" config value."""
    value = current_app.config.get(key)
    if isinstance(value, timedelta):
        return value
    if isinstance(value, str):
        parts = value.split()
        if len(parts) == 2:
            unit = parts[1] if parts[1].endswith("s") else parts[1] + "s"
            try:
                return timedelta(**{unit: int(parts[0])})
            except (TypeError, ValueError):
                pass
    return _DEFAULT_WITHIN[key]


def within_hours(key):
    """Returns the lifetime of a mail link in whole hours, rounded up."""
    return -(-int(within(key).total_seconds()) // 3600)


def new_stamp(user):
    """Gives the user a new fs_uniquifier, which cancels each open mail link of the account."""
    user.fs_uniquifier = uuid.uuid4().hex


def _activation_secret(user):
    return "{}|{}".format(user.email or "", user.fs_uniquifier or "")


def _reset_secret(user):
    return "{}|{}".format(user.password or "", user.fs_uniquifier or "")


def activation_token(user):
    """Builds the activation link token, bound to the email and the stamp."""
    return _serializer(ACTIVATION_SALT).dumps([str(user.id), _hashing.hash(_activation_secret(user))])


def reset_token(user):
    """Builds the reset link token, bound to the password and the stamp."""
    return _serializer(RESET_SALT).dumps([str(user.id), _hashing.hash(_reset_secret(user))])


def _token_status(token, salt, key, secret):
    s = _serializer(salt)
    expired = False
    try:
        data = s.loads(token, max_age=int(within(key).total_seconds()))
    except SignatureExpired:
        _, data = s.loads_unsafe(token)
        expired = True
    except (BadData, TypeError, ValueError):
        return False, True, None
    if not (isinstance(data, list) and len(data) == 2):
        return False, True, None
    user = _find(data[0])
    if user is None or not _verify(data[1], secret(user)):
        return False, True, None
    return expired, False, user


def activation_token_status(token):
    """Returns (expired, invalid, user) for an activation link token."""
    return _token_status(token, ACTIVATION_SALT, ACTIVATION_WITHIN_KEY, _activation_secret)


def reset_token_status(token):
    """Returns (expired, invalid, user) for a reset link token."""
    return _token_status(token, RESET_SALT, RESET_WITHIN_KEY, _reset_secret)
