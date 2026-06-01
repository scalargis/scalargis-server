"""
Security response headers for ScalarGIS.

Adds standard security headers to every HTTP response via a Flask
after_request hook.  All values are configurable via
``SCALARGIS_SECURITY_HEADERS_*`` config keys; set any key to ``''``
(empty string) to suppress that header entirely.
"""
import logging
import re

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
    # Cross-origin framing opt-in (embedded map). EMBED_PATHS is a list of path
    # prefixes allowed to be iframed by other sites; empty = no embedding (the
    # default). EMBED_FRAME_ANCESTORS is the frame-ancestors value applied to
    # those paths (e.g. '*' for any site, or "'self' https://parent.example").
    'EMBED_PATHS': [],
    'EMBED_FRAME_ANCESTORS': '*',
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

        # Is this request path opted-in for cross-origin framing (embedded map)?
        # Match is aligned on a '/' boundary so '/sso' matches '/sso' and
        # '/sso/callback' but not '/ssomething'.
        embed_paths = _get(cfg, 'EMBED_PATHS') or []
        path = request.path or ''
        is_embed = any(path == p or path.startswith(p + '/') for p in embed_paths)

        val = _get(cfg, 'X_FRAME_OPTIONS')
        if val and not is_embed:
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
            if is_embed:
                # Relax only the framing directive for opted-in (embeddable)
                # routes; every other CSP protection stays intact.
                embed_fa = _get(cfg, 'EMBED_FRAME_ANCESTORS') or '*'
                csp = re.sub(r"frame-ancestors[^;]*",
                             "frame-ancestors " + embed_fa, csp)
            header = ('Content-Security-Policy-Report-Only'
                      if _get(cfg, 'CSP_REPORT_ONLY')
                      else 'Content-Security-Policy')
            response.headers.setdefault(header, csp)

        if _get(cfg, 'HSTS_FORCE') or request.scheme == 'https':
            response.headers.setdefault('Strict-Transport-Security',
                                        _build_hsts(cfg))

        return response

    logger.info('Security headers hook registered')
