import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from io import BytesIO
from urllib.parse import parse_qs, urlsplit

from flask import Flask
from PIL import Image

from app.utils.pdf_layout import Pdf
from app.utils.print_layers import client_layer_url_params


def test_print_keeps_time_and_auth_values_without_query_injection():
    stream = BytesIO()
    Image.new('RGB', (2, 2), 'white').save(stream, format='PNG')
    body = stream.getvalue()
    seen = []

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            seen.append(parse_qs(urlsplit(self.path).query))
            self.send_response(200)
            self.send_header('Content-Type', 'image/png')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        time = '2024-01-01T12:00:00+01:00&layers=private'
        descriptor = ';'.join(['wms', 'url', 'public', '1', '0', '0', '', '', 'image/png', 'a+b&x=y', time])
        with Flask('timeline-print-test').app_context():
            image = Pdf.wms_getmap(
                f'http://127.0.0.1:{server.server_port}/wms', 'public', [0, 0, 1, 1], 2, 2, 3857, 'image/png',
                url_params=client_layer_url_params(descriptor), timeout=5, strict=True,
            )
        assert image.getSize() == (2, 2)
        assert seen[0]['TIME'] == [time]
        assert seen[0]['layers'] == ['public']
        assert seen[0]['authkey'] == ['a+b&x=y']
        assert 'x' not in seen[0]
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def test_legacy_layer_without_time_keeps_authentication():
    assert client_layer_url_params('wms;url;layer;1;0;0;;;image/png;token') == [['authkey', 'token']]
    assert client_layer_url_params('wms;url;layer;1;0;0;;;image/png') == []
