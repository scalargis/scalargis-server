"""gunicorn runtime: Waitress environ parity, gunicorn settings and the DB pool options."""
import importlib
import os
import runpy

import pytest

from app.utils.wsgi import with_waitress_environ

SCALARGIS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _call(app, path, scheme='http'):
    seen = {}

    def inner(environ, start_response):
        seen.update(environ)
        start_response('200 OK', [])
        return [b'ok']

    status = []
    body = with_waitress_environ(inner, *app)(
        {'PATH_INFO': path, 'SCRIPT_NAME': '', 'wsgi.url_scheme': scheme},
        lambda s, h: status.append(s),
    )
    return status[0], b''.join(body), seen


def test_no_prefix_and_no_scheme_leave_environ_alone():
    status, _, seen = _call((None, None), '/api/app/site/config')
    assert status == '200 OK'
    assert seen['PATH_INFO'] == '/api/app/site/config'
    assert seen['SCRIPT_NAME'] == ''
    assert seen['wsgi.url_scheme'] == 'http'


def test_url_scheme_sets_the_wsgi_scheme():
    _, _, seen = _call(('', 'https'), '/x')
    assert seen['wsgi.url_scheme'] == 'https'


def test_url_prefix_moves_to_script_name():
    _, _, seen = _call(('/scalargis/', None), '/scalargis/api/app')
    assert seen['SCRIPT_NAME'] == '/scalargis'
    assert seen['PATH_INFO'] == '/api/app'


def test_path_outside_the_prefix_gives_404():
    status, body, seen = _call(('/scalargis', None), '/other/api')
    assert status.startswith('404')
    assert body == b'Not Found'
    assert seen == {}


def _gunicorn_conf(monkeypatch, **env):
    for key in ('PORT', 'WORKERS', 'THREADS', 'CONNECTION_LIMIT', 'WORKER_TIMEOUT', 'MAX_REQUESTS',
                'MAX_REQUESTS_JITTER', 'TRUSTED_PROXY'):
        monkeypatch.delenv(key, raising=False)
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    return runpy.run_path(os.path.join(SCALARGIS_DIR, 'gunicorn.conf.py'))


def test_gunicorn_conf_defaults(monkeypatch):
    conf = _gunicorn_conf(monkeypatch)
    assert conf['wsgi_app'] == 'wsgi:app'
    assert conf['bind'] == '0.0.0.0:5000'
    assert conf['worker_class'] == 'gthread'
    assert (conf['workers'], conf['threads']) == (2, 6)
    assert conf['preload_app'] is False
    assert conf['max_requests'] == 0
    assert conf['forwarded_allow_ips'] == '127.0.0.1'


def test_gunicorn_conf_reads_the_stack_env(monkeypatch):
    conf = _gunicorn_conf(monkeypatch, PORT='5001', WORKERS='4', THREADS='4', MAX_REQUESTS='5000',
                          MAX_REQUESTS_JITTER='500', TRUSTED_PROXY='*', CONNECTION_LIMIT='')
    assert conf['bind'] == '0.0.0.0:5001'
    assert (conf['workers'], conf['threads']) == (4, 4)
    assert (conf['max_requests'], conf['max_requests_jitter']) == (5000, 500)
    assert conf['forwarded_allow_ips'] == '*'
    assert conf['worker_connections'] == 100


@pytest.mark.parametrize('env, expected', [
    ({}, {}),
    ({'DB_POOL_SIZE': '6'}, {'pool_size': 6}),
    ({'DB_POOL_SIZE': '6', 'DB_MAX_OVERFLOW': '2'}, {'pool_size': 6, 'max_overflow': 2}),
])
def test_pool_options_come_from_env(monkeypatch, env, expected):
    monkeypatch.delenv('DB_POOL_SIZE', raising=False)
    monkeypatch.delenv('DB_MAX_OVERFLOW', raising=False)
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    import instance.default as default
    assert importlib.reload(default).SQLALCHEMY_ENGINE_OPTIONS == expected
