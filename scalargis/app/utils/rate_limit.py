"""
Centralized rate limiting for ScalarGIS (core + extensions).

A single Flask-Limiter instance shared across the whole app. Endpoints opt in
with the ``rate_limit(...)`` decorator factory (or the ``limit_login`` /
``limit_email`` convenience wrappers); extensions consume the same limiter, so
there is exactly one set of counters, one error handler, and one place to
configure storage.

Complements the per-IP failed-login blocker in ``app/utils/login_blocking.py``:
that one counts *failed credentials*, this one caps *raw request rate* (email
flooding, token brute-forcing).

Storage is in-process (``memory://``). Production runs a single-process,
multi-threaded Waitress server (``scalargis/server.py``), so the counters are
shared across all worker threads — no external store is required.
"""
import json
import logging

from flask import current_app, request
from flask_limiter import Limiter, RateLimitExceeded
from flask_limiter.util import get_remote_address

logger = logging.getLogger(__name__)

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[],
    storage_uri="memory://",
    headers_enabled=True,
)

# Callables run on every 429 rejection (e.g. extension audit logging).
# Populated via register_rate_limit_hook, invoked by _run_hooks.
_hooks = []


def _user_key():
    """Per-authenticated-user key, falling back to the client IP for anonymous
    requests. Used by ``rate_limit(..., key='user')``."""
    try:
        from app.utils.security import get_api_user
        user = get_api_user(request)
        if user and getattr(user, 'id', None) is not None:
            return f"user:{user.id}"
    except Exception:
        pass
    return get_remote_address()


def rate_limit(config_key, default, key='ip'):
    """Generic rate-limit decorator for any Flask-RESTX Resource or view.

    The limit string is resolved lazily from app config at request time, so a
    deployment can override ``config_key`` without code changes::

        decorators = [rate_limit('SCALARGIS_RATELIMIT_LOGIN', '30/minute')]
        decorators = [rate_limit('SCALARGIS_CART_RATELIMIT_CART', '60/minute', key='user')]

    ``key='ip'``   -> per client IP (get_remote_address; proxy-aware via ProxyFix)
    ``key='user'`` -> per authenticated user, IP fallback (_user_key)
    """
    key_func = _user_key if key == 'user' else get_remote_address
    return limiter.limit(lambda: current_app.config.get(config_key, default),
                         key_func=key_func)


def limit_login():
    """Coarse per-IP cap for the login endpoint (defence-in-depth over the
    failed-login blocker in login_blocking.py)."""
    return rate_limit('SCALARGIS_RATELIMIT_LOGIN', '30/minute')


def limit_email():
    """Tight per-IP cap for endpoints that send mail or consume tokens."""
    return rate_limit('SCALARGIS_RATELIMIT_EMAIL', '5/minute;20/hour')


def register_rate_limit_hook(fn):
    """Register a callable ``fn(error)`` invoked on every rate-limit rejection.
    Lets extensions plug in audit logging without core depending on them."""
    _hooks.append(fn)


def _run_hooks(error):
    for fn in _hooks:
        try:
            fn(error)
        except Exception:
            logger.exception('rate-limit hook failed')


def rate_limit_exceeded_response(error):
    """Build the 429 response as JSON, consistent with the rest of the API."""
    response = error.get_response()
    response.status_code = 429
    response.set_data(json.dumps({
        'error': 'rate_limit_exceeded',
        'message': str(error.description),
    }))
    response.content_type = 'application/json'
    return response


def register_rate_limit_error_handler(target):
    """Attach the shared 429 handler to a Flask app *or* a Flask-RESTX ``Api``.

    Both run the hooks first. A Flask app handler returns the ``Response``; a
    Flask-RESTX ``Api`` handler must return ``(payload, status, headers)`` so
    RESTX serialises it correctly — a ``RateLimitExceeded`` raised inside a
    resource's ``decorators`` is caught by RESTX's error router, not the
    app-level handler."""
    from flask_restx import Api
    is_restx = isinstance(target, Api)

    def handler(error):
        _run_hooks(error)
        response = rate_limit_exceeded_response(error)
        if is_restx:
            return json.loads(response.get_data()), 429, dict(response.headers)
        return response

    target.errorhandler(RateLimitExceeded)(handler)


def init_rate_limiter(app):
    """Bind the shared limiter to the app. Call once, from the app factory,
    before the API namespaces are registered."""
    limiter.init_app(app)

    register_rate_limit_error_handler(app)

    # The auth endpoints are Flask-RESTX resources; a 429 raised inside their
    # ``decorators`` is handled by the RESTX Api error router, so register the
    # handler there too. Imported lazily to avoid a circular import at load.
    from app.api.restx import api
    register_rate_limit_error_handler(api)

    @limiter.request_filter
    def _exempt_options():
        # Never throttle CORS preflight.
        return request.method == 'OPTIONS'

    logger.info('Rate limiter initialized (storage=memory://)')
