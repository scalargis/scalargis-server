import os
import socket
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest
import requests
from flask import Flask

from app.utils import http as http_utils
from app.plugins.proxy import proxy as proxy_plugin


LARGE_BODY = bytes(range(256)) * 20000


class UpstreamHandler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def log_message(self, *args):
        pass

    def do_GET(self):
        self.server.connections.add(self.client_address)
        self.server.seen.append(self.headers)
        if self.path.startswith('/slow'):
            time.sleep(2)
            self._send(200, b'late')
        elif self.path.startswith('/large'):
            self._send(200, LARGE_BODY, 'application/octet-stream')
        elif self.path.startswith('/range'):
            first, last = self.headers['Range'].split('=')[1].split('-')
            part = LARGE_BODY[int(first):int(last) + 1]
            self._send(206, part, 'image/tiff', {
                'Content-Range': 'bytes {0}-{1}/{2}'.format(first, last, len(LARGE_BODY)),
                'Accept-Ranges': 'bytes'})
        elif self.path.startswith('/cookie'):
            self._send(200, b'ok', extra={'Set-Cookie': 'JSESSIONID=abc; Path=/'})
        else:
            self._send(200, b'ok')

    def do_POST(self):
        body = self.rfile.read(int(self.headers['Content-Length']))
        self._send(200, body, 'text/xml')

    def _send(self, status, body, content_type='text/plain', extra=None):
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(body)))
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass


@pytest.fixture
def upstream():
    server = ThreadingHTTPServer(('127.0.0.1', 0), UpstreamHandler)
    server.daemon_threads = True
    server.connections = set()
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


def test_timeout_is_off_without_env():
    assert http_utils.http_timeout() is None
    assert http_utils.http_session().default_timeout is None


def test_timeout_reads_env(monkeypatch):
    monkeypatch.setenv('HTTP_CONNECT_TIMEOUT', '5')
    monkeypatch.setenv('HTTP_READ_TIMEOUT', '290')
    assert http_utils.http_session().default_timeout == (5.0, 290.0)


def test_bad_env_value_is_ignored(monkeypatch):
    monkeypatch.setenv('HTTP_CONNECT_TIMEOUT', 'five')
    assert http_utils.http_timeout() is None


def test_one_session_per_process(monkeypatch):
    first = http_utils.http_session()
    assert http_utils.http_session() is first
    monkeypatch.setattr(http_utils, '_session_pid', os.getpid() + 1)
    assert http_utils.http_session() is not first


def test_read_timeout_raises(monkeypatch, upstream):
    _, base = upstream
    monkeypatch.setenv('HTTP_READ_TIMEOUT', '0.5')
    with pytest.raises(requests.Timeout):
        http_utils.http_session().get(base + '/slow')


def test_connect_timeout_raises(monkeypatch):
    listener = socket.socket()
    listener.bind(('127.0.0.1', 0))
    listener.listen(0)
    port = listener.getsockname()[1]
    fillers = []
    try:
        for _ in range(8):
            s = socket.socket()
            s.setblocking(False)
            s.connect_ex(('127.0.0.1', port))
            fillers.append(s)
        monkeypatch.setenv('HTTP_CONNECT_TIMEOUT', '0.5')
        monkeypatch.setenv('HTTP_READ_TIMEOUT', '0.5')
        with pytest.raises(requests.Timeout):
            http_utils.http_session().get('http://127.0.0.1:{0}/'.format(port))
    finally:
        for s in fillers:
            s.close()
        listener.close()


def test_explicit_timeout_wins(monkeypatch, upstream):
    _, base = upstream
    monkeypatch.setenv('HTTP_READ_TIMEOUT', '0.5')
    assert http_utils.http_session().get(base + '/slow', timeout=5).text == 'late'


def test_two_calls_reuse_one_connection(upstream):
    server, base = upstream
    session = http_utils.http_session()
    assert session.get(base + '/a').text == 'ok'
    assert session.get(base + '/b').text == 'ok'
    assert len(server.connections) == 1


def test_session_keeps_no_cookies(upstream):
    server, base = upstream
    session = http_utils.http_session()
    session.get(base + '/cookie')
    session.get(base + '/a')
    assert len(session.cookies) == 0
    assert server.seen[-1].get('Cookie') is None


def test_proxy_streams_large_answer(proxy_client, upstream):
    _, base = upstream
    resp = proxy_client.get('/proxy/', query_string={'url': base + '/large'})
    assert resp.status_code == 200
    assert resp.is_streamed
    assert resp.headers['Content-Type'] == 'application/octet-stream'
    assert resp.headers['Content-Length'] == str(len(LARGE_BODY))
    assert resp.headers['Access-Control-Allow-Origin'] == '*'
    assert resp.get_data() == LARGE_BODY


def test_proxy_passes_range_answer(proxy_client, upstream):
    server, base = upstream
    resp = proxy_client.get('/proxy/', query_string={'url': base + '/range'},
                            headers={'Range': 'bytes=100-199', 'Referer': 'http://viewer/'})
    assert resp.status_code == 206
    assert resp.headers['Content-Range'] == 'bytes 100-199/{0}'.format(len(LARGE_BODY))
    assert resp.get_data() == LARGE_BODY[100:200]
    assert server.seen[-1].get('Referer') == 'http://viewer/'


def test_proxy_answers_504_on_slow_upstream(monkeypatch, proxy_client, upstream):
    _, base = upstream
    monkeypatch.setenv('HTTP_READ_TIMEOUT', '0.5')
    resp = proxy_client.get('/proxy/', query_string={'url': base + '/slow'})
    assert resp.status_code == 504
    assert resp.headers['Access-Control-Allow-Origin'] == '*'


def test_proxy_posts_body(proxy_client, upstream):
    _, base = upstream
    resp = proxy_client.post('/proxy/', query_string={'url': base + '/wfs'}, data=b'<GetFeature/>',
                             content_type='text/xml')
    assert resp.status_code == 200
    assert resp.get_data() == b'<GetFeature/>'
    assert resp.headers['Content-Type'] == 'text/xml'
