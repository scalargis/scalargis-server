from datetime import timedelta
from http.cookiejar import DefaultCookiePolicy
from flask import make_response, request, current_app
from functools import update_wrapper
import logging
import os
import threading

import requests
from requests.adapters import HTTPAdapter


HTTP_POOL_SIZE = 32

_session = None
_session_pid = None
_session_lock = threading.Lock()

_app_index = {}
_app_index_lock = threading.Lock()


def crossdomain(origin=None, methods=None, headers=None,
                max_age=21600, attach_to_all=True,
                automatic_options=True):
    if methods is not None:
        methods = ', '.join(sorted(x.upper() for x in methods))
    if headers is not None and not isinstance(headers, str):
        headers = ', '.join(x.upper() for x in headers)
    if not isinstance(origin, str):
        origin = ', '.join(origin)
    if isinstance(max_age, timedelta):
        max_age = max_age.total_seconds()

    def get_methods():
        if methods is not None:
            return methods

        options_resp = current_app.make_default_options_response()
        return options_resp.headers['allow']

    def decorator(f):
        def wrapped_function(*args, **kwargs):
            if automatic_options and request.method == 'OPTIONS':
                resp = current_app.make_default_options_response()
            else:
                resp = make_response(f(*args, **kwargs))
            if not attach_to_all and request.method != 'OPTIONS':
                return resp

            h = resp.headers

            h['Access-Control-Allow-Origin'] = origin
            h['Access-Control-Allow-Methods'] = get_methods()
            h['Access-Control-Max-Age'] = str(max_age)
            if headers is not None:
                h['Access-Control-Allow-Headers'] = headers
            return resp

        f.provide_automatic_options = False
        return update_wrapper(wrapped_function, f)

    return decorator


def replace_geoserver_url(url):
    new_url = url

    try:
        if isinstance(current_app.config.get('SCALARGIS_ROUTE_GEOSERVER'), list) \
                and len(current_app.config.get('SCALARGIS_ROUTE_GEOSERVER')) > 0:
            if isinstance(current_app.config.get('SCALARGIS_ROUTE_GEOSERVER')[0], list):
                for s in current_app.config.get('SCALARGIS_ROUTE_GEOSERVER'):
                    if len(s) > 2:
                        if s[2] == 'start':
                            if new_url.startswith(s[0]):
                                new_url = new_url.replace(s[0], s[1])
                        else:
                            new_url = new_url.replace(s[0], s[1])
                    else:
                        new_url = new_url.replace(s[0], s[1])
            else:
                s = current_app.config.get('SCALARGIS_ROUTE_GEOSERVER')
                if len(s) > 2:
                    if s[2] == 'start':
                        if new_url.startswith(s[0]):
                            new_url = new_url.replace(s[0], s[1])
                        else:
                            new_url = new_url.replace(s[0], s[1])
                else:
                    new_url = new_url.replace(s[0], s[1])
        logging.info('WMS Url replace: ' + new_url)
    except AttributeError:
        logging.info('WMS Url replace: error')
        pass

    return new_url


def get_host_url():
    if 'SCALARGIS_HOST_URL' in current_app.config and current_app.config.get('SCALARGIS_HOST_URL'):
        return current_app.config.get('SCALARGIS_HOST_URL').rstrip('\/')

    if request.headers.environ.get('HTTP_X_FORWARDED_HOST'):
        host = request.headers.environ.get('HTTP_X_FORWARDED_HOST').rstrip('\/')
        proto = 'http'
        if request.headers.environ.get('HTTP_X_FORWARDED_PROTO'):
            proto = request.headers.environ.get('HTTP_X_FORWARDED_PROTO').rstrip(':\/\/')
        return '{0}://{1}'.format(proto, host)

    return request.host_url.rstrip('\/')


def get_script_root():
    return request.script_root or ''


def get_base_url():
    return (current_app.config.get('SCALARGIS_BASE_URL') or request.script_root or '').rstrip('\/')


def read_app_index(app_name):
    """The index.html of static/<app_name>, read again only when its mtime changes."""
    path = os.path.join(current_app.static_folder, app_name, 'index.html')
    mtime = os.stat(path).st_mtime_ns
    cached = _app_index.get(path)
    if cached and cached[0] == mtime:
        return cached[1]
    with _app_index_lock:
        cached = _app_index.get(path)
        if cached and cached[0] == mtime:
            return cached[1]
        with open(path, 'r', encoding='utf-8') as f:
            html = f.read()
        _app_index[path] = (mtime, html)
        return html


def _env_seconds(name):
    value = os.environ.get(name)
    if not value:
        return None
    try:
        seconds = float(value)
    except ValueError:
        logging.warning('%s is not a number: %s', name, value)
        return None
    return seconds if seconds > 0 else None


def http_timeout():
    """Returns the (connect, read) timeout from HTTP_CONNECT_TIMEOUT and HTTP_READ_TIMEOUT, or None."""
    connect = _env_seconds('HTTP_CONNECT_TIMEOUT')
    read = _env_seconds('HTTP_READ_TIMEOUT')
    if connect is None and read is None:
        return None
    return connect, read


class TimeoutSession(requests.Session):
    """Session that applies a default timeout and keeps no cookies between requests."""

    def __init__(self, timeout=None):
        super().__init__()
        self.default_timeout = timeout
        self.cookies.set_policy(DefaultCookiePolicy(allowed_domains=[]))
        adapter = HTTPAdapter(pool_connections=HTTP_POOL_SIZE, pool_maxsize=HTTP_POOL_SIZE)
        self.mount('http://', adapter)
        self.mount('https://', adapter)

    def request(self, method, url, **kwargs):
        if kwargs.get('timeout') is None:
            kwargs['timeout'] = self.default_timeout
        return super().request(method, url, **kwargs)


def http_session():
    """Returns the shared outbound HTTP session of this process."""
    global _session, _session_pid
    pid = os.getpid()
    if _session is None or _session_pid != pid:
        with _session_lock:
            if _session is None or _session_pid != pid:
                _session = TimeoutSession(http_timeout())
                _session_pid = pid
    return _session
