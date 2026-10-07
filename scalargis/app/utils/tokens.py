"""API token and confirm token formats, independent of the Flask-Security version."""
from datetime import timedelta

from flask import current_app
from itsdangerous import BadData, SignatureExpired, URLSafeTimedSerializer
from passlib.context import CryptContext

REMEMBER_SALT = "remember-salt"
CONFIRM_SALT = "confirm-salt"
CONFIRM_WITHIN = timedelta(days=5)

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


def confirmation_token(user):
    """Builds the confirm and reset token: [id, sha256_crypt(email)] signed with confirm-salt."""
    return _serializer(CONFIRM_SALT).dumps([str(user.id), _hashing.hash(user.email or "")])


def confirmation_token_status(token, within=CONFIRM_WITHIN):
    """Returns (expired, invalid, user) for a confirm or reset token."""
    s = _serializer(CONFIRM_SALT)
    expired, invalid, data, user = False, False, None, None
    try:
        data = s.loads(token, max_age=int(within.total_seconds()))
    except SignatureExpired:
        _, data = s.loads_unsafe(token)
        expired = True
    except (BadData, TypeError, ValueError):
        invalid = True
    if data is not None and not (isinstance(data, list) and len(data) == 2):
        return False, True, None
    if data:
        user = _find(data[0])
    expired = expired and user is not None
    if not invalid and user:
        invalid = not _verify(data[1], user.email)
    return expired, invalid, user
