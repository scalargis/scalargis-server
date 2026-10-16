import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest
from flask import Flask

from app.utils import http as http_utils
from app.plugins.proxy import proxy as proxy_plugin


class UpstreamHandler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def log_message(self, *args):
        pass

    def do_GET(self):
        self.server.seen.append(self.headers)
        extra = {'Set-Cookie': 'JSESSIONID=abc; Path=/'} if self.path.startswith('/cookie') else {}
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain')
        self.send_header('Content-Length', '2')
        for k, v in extra.items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(b'ok')


@pytest.fixture
def upstream():
    server = ThreadingHTTPServer(('127.0.0.1', 0), UpstreamHandler)
    server.daemon_threads = True
    server.seen = []
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield server, 'http://127.0.0.1:{0}'.format(server.server_address[1])
    server.shutdown()
    server.server_close()


@pytest.fixture(autouse=True)
def fresh_session(monkeypatch):
    monkeypatch.delenv('HTTP_CONNECT_TIMEOUT', raising=False)
    monkeypatch.delenv('HTTP_READ_TIMEOUT', raising=False)
    monkeypatch.setattr(http_utils, '_session', None)
    monkeypatch.setattr(http_utils, '_session_pid', None)


@pytest.fixture
def proxy_client(monkeypatch):
    monkeypatch.setattr(proxy_plugin, 'get_config_value', lambda key: '*')
    app = Flask('proxy-test')
    app.register_blueprint(proxy_plugin.module)
    return app.test_client()


def test_session_keeps_no_cookies(upstream):
    server, base = upstream
    session = http_utils.http_session()
    session.get(base + '/cookie')
    session.get(base + '/a')
    assert len(session.cookies) == 0
    assert server.seen[-1].get('Cookie') is None


@pytest.mark.parametrize('url', ['file:///etc/passwd', 'gopher://127.0.0.1/', 'ftp://host/x', 'no-scheme'])
def test_proxy_answers_400_on_bad_scheme(proxy_client, url):
    assert proxy_client.get('/proxy/', query_string={'url': url}).status_code == 400


def test_proxy_sends_no_cookie_upstream(proxy_client, upstream):
    server, base = upstream
    proxy_client.set_cookie('session', 'secret')
    assert proxy_client.get('/proxy/', query_string={'url': base + '/ok'}).status_code == 200
    assert server.seen[-1].get('Cookie') is None


def test_proxy_answer_is_sandboxed(proxy_client, upstream):
    _, base = upstream
    resp = proxy_client.get('/proxy/', query_string={'url': base + '/ok'})
    assert resp.headers['Content-Security-Policy'] == 'sandbox'
