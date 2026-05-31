"""
Security response headers for ScalarGIS.

Adds standard security headers to every HTTP response via a Flask
after_request hook.  All values are configurable via
``SCALARGIS_SECURITY_HEADERS_*`` config keys; set any key to ``''``
(empty string) to suppress that header entirely.
"""
import logging

from flask import request

logger = logging.getLogger(__name__)

_DEFAULTS = {
    'X_FRAME_OPTIONS': 'SAMEORIGIN',
    'X_CONTENT_TYPE_OPTIONS': 'nosniff',
    'X_XSS_PROTECTION': '0',
    'REFERRER_POLICY': 'strict-origin-when-cross-origin',
    'CSP': (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval' https: http:; "
        "style-src 'self' 'unsafe-inline' https: http:; "
        "img-src 'self' data: blob: https: http:; "
        "font-src 'self' data:; "
        "connect-src 'self' blob: https: http:; "
        "frame-src 'self' https: http:; "
        "frame-ancestors 'self'; "
        "object-src 'none'; "
        "base-uri 'self'; "
        "form-action 'self'"
    ),
    'HSTS_MAX_AGE': 31536000,
    'HSTS_INCLUDE_SUBDOMAINS': False,
    'HSTS_PRELOAD': False,
    'HSTS_FORCE': False,
    'CSP_REPORT_ONLY': False,
}


def _get(cfg, suffix):
    key = 'SCALARGIS_SECURITY_HEADERS_{}'.format(suffix)
    val = cfg.get(key)
    return val if val is not None else _DEFAULTS.get(suffix, '')


def _build_hsts(cfg):
    max_age = _get(cfg, 'HSTS_MAX_AGE')
    value = 'max-age={}'.format(max_age)
    if _get(cfg, 'HSTS_INCLUDE_SUBDOMAINS'):
        value += '; includeSubDomains'
    if _get(cfg, 'HSTS_PRELOAD'):
        value += '; preload'
    return value


def init_security_headers(app):
    """Register the after_request hook that sets security headers."""

    @app.after_request
    def _add_security_headers(response):
        cfg = app.config

        val = _get(cfg, 'X_FRAME_OPTIONS')
        if val:
            response.headers.setdefault('X-Frame-Options', val)

        val = _get(cfg, 'X_CONTENT_TYPE_OPTIONS')
        if val:
            response.headers.setdefault('X-Content-Type-Options', val)

        val = _get(cfg, 'X_XSS_PROTECTION')
        if val is not None and val != '':
            response.headers.setdefault('X-XSS-Protection', str(val))

        val = _get(cfg, 'REFERRER_POLICY')
        if val:
            response.headers.setdefault('Referrer-Policy', val)

        csp = _get(cfg, 'CSP')
        if csp:
            header = ('Content-Security-Policy-Report-Only'
                      if _get(cfg, 'CSP_REPORT_ONLY')
                      else 'Content-Security-Policy')
            response.headers.setdefault(header, csp)

        if _get(cfg, 'HSTS_FORCE') or request.scheme == 'https':
            response.headers.setdefault('Strict-Transport-Security',
                                        _build_hsts(cfg))

        return response

    logger.info('Security headers hook registered')
