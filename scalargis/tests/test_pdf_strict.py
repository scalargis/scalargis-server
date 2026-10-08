"""A strict Pdf stops on a failed map or legend fetch, and the default Pdf draws what it gets as before."""
import socket
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from io import BytesIO

import pytest
import requests
from flask import Flask
from PIL import Image
from reportlab.lib.utils import ImageReader

from app.utils import http as http_utils
from app.utils import pdf_layout
from app.utils.pdf_layout import Pdf, PrintServiceError


SERVICE_EXCEPTION = (b'<?xml version="1.0" encoding="UTF-8"?><ServiceExceptionReport version="1.1.1">'
                     b'<ServiceException code="LayerNotDefined">Could not find layer x</ServiceException>'
                     b'</ServiceExceptionReport>')


def image_bytes(fmt):
    out = BytesIO()
    mode = 'RGBA' if fmt == 'PNG' else 'RGB'
    Image.new(mode, (40, 30), (10, 120, 200, 255)[:len(mode)]).save(out, fmt)
    return out.getvalue()


PNG = image_bytes('PNG')
JPEG = image_bytes('JPEG')


class ServiceHandler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def log_message(self, *args):
        pass

    def do_GET(self):
        self.server.paths.append(self.path)
        if self.path.startswith('/png'):
            self._send(200, PNG, 'image/png')
        elif self.path.startswith('/jpeg'):
            self._send(200, JPEG, 'image/jpeg')
        elif self.path.startswith('/xml'):
            self._send(200, SERVICE_EXCEPTION, 'application/vnd.ogc.se_xml')
        elif self.path.startswith('/500'):
            self._send(500, b'Internal Server Error', 'text/html')
        elif self.path.startswith('/404'):
            self._send(404, b'Not Found', 'text/html')
        elif self.path.startswith('/hang'):
            time.sleep(3)
            self._send(200, PNG, 'image/png')
        else:
            self._send(400, b'unknown path')

    def _send(self, status, body, content_type='text/plain'):
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            pass


@pytest.fixture
def service():
    server = ThreadingHTTPServer(('127.0.0.1', 0), ServiceHandler)
    server.daemon_threads = True
    server.paths = []
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield 'http://127.0.0.1:{0}'.format(server.server_address[1])
    server.shutdown()
    server.server_close()


@pytest.fixture
def refused_url():
    s = socket.socket()
    s.bind(('127.0.0.1', 0))
    port = s.getsockname()[1]
    s.close()
    return 'http://127.0.0.1:{0}/wms'.format(port)


@pytest.fixture(autouse=True)
def app_context(monkeypatch):
    monkeypatch.delenv('HTTP_CONNECT_TIMEOUT', raising=False)
    monkeypatch.delenv('HTTP_READ_TIMEOUT', raising=False)
    monkeypatch.delenv('PDF_STRICT_READ_TIMEOUT', raising=False)
    monkeypatch.setattr(http_utils, '_session', None)
    monkeypatch.setattr(http_utils, '_session_pid', None)
    with Flask('pdf-strict-test').app_context():
        yield


def make_pdf(strict, monkeypatch):
    pdf = Pdf(strict=strict)
    draws = []
    real_draw = pdf.canvas.drawImage

    def draw(img, *args, **kwargs):
        draws.append(img)
        return real_draw(img, *args, **kwargs)

    monkeypatch.setattr(pdf.canvas, 'drawImage', draw)
    return pdf, draws


def add_map(pdf, url, serv_type='wms', img_format='image/png', opacity=1):
    pdf.insert_map(serv_type, 5000, 3763, -20000, -100000, 100, 80, img_format, 10, 10, url, 'ws:layer',
                   quality=1, opacity=opacity)


def add_legend(pdf, url, serv_type='wms'):
    pdf.insert_legend(serv_type, url, 'ws:layer', 10, 200, 40)


def finish(pdf):
    pdf.savepdf()
    out = pdf.getpdf()
    assert out.startswith(b'%PDF')
    return out


def test_strict_timeout_default():
    assert http_utils.strict_print_timeout() == (None, 30)


def test_strict_timeout_reads_env(monkeypatch):
    monkeypatch.setenv('HTTP_CONNECT_TIMEOUT', '5')
    monkeypatch.setenv('HTTP_READ_TIMEOUT', '290')
    monkeypatch.setenv('PDF_STRICT_READ_TIMEOUT', '12')
    assert http_utils.strict_print_timeout() == (5.0, 12.0)


def test_strict_timeout_ignores_bad_env(monkeypatch):
    monkeypatch.setenv('PDF_STRICT_READ_TIMEOUT', 'abc')
    assert http_utils.strict_print_timeout() == (None, 30)


def test_refused_connection_default_gives_pdf(monkeypatch, refused_url):
    pdf, draws = make_pdf(False, monkeypatch)
    add_map(pdf, refused_url)
    finish(pdf)
    assert draws == []


def test_refused_connection_strict_raises(monkeypatch, refused_url):
    pdf, draws = make_pdf(True, monkeypatch)
    with pytest.raises(PrintServiceError) as info:
        add_map(pdf, refused_url)
    assert info.value.url == refused_url
    assert isinstance(info.value.cause, requests.ConnectionError)
    assert draws == []


def test_hanging_service_strict_raises_after_strict_timeout(monkeypatch, service):
    monkeypatch.setenv('HTTP_READ_TIMEOUT', '290')
    monkeypatch.setenv('PDF_STRICT_READ_TIMEOUT', '0.5')
    pdf, _ = make_pdf(True, monkeypatch)
    start = time.monotonic()
    with pytest.raises(PrintServiceError) as info:
        add_map(pdf, service + '/hang')
    assert time.monotonic() - start < 2.5
    assert isinstance(info.value.cause, requests.ReadTimeout)


@pytest.mark.parametrize('path', ['/500', '/404', '/xml'])
def test_failed_answer_strict_raises(monkeypatch, service, path):
    pdf, _ = make_pdf(True, monkeypatch)
    with pytest.raises(PrintServiceError) as info:
        add_map(pdf, service + path)
    assert info.value.url == service + path


@pytest.mark.parametrize('path', ['/500', '/404', '/xml'])
def test_failed_answer_default_gives_pdf(monkeypatch, service, path):
    pdf, draws = make_pdf(False, monkeypatch)
    add_map(pdf, service + path)
    finish(pdf)
    assert draws == []


def test_esri_rest_failed_fetch_strict_raises(monkeypatch, service, refused_url):
    pdf, _ = make_pdf(True, monkeypatch)
    with pytest.raises(PrintServiceError):
        add_map(pdf, service + '/500', serv_type='esri_rest')
    with pytest.raises(PrintServiceError):
        add_map(pdf, refused_url, serv_type='esri_rest')


def test_opacity_failed_fetch_strict_raises(monkeypatch, service, refused_url):
    pdf, _ = make_pdf(True, monkeypatch)
    with pytest.raises(PrintServiceError):
        add_map(pdf, service + '/500', opacity=0.5)
    with pytest.raises(PrintServiceError):
        add_map(pdf, service + '/xml', opacity=0.5)
    with pytest.raises(PrintServiceError):
        add_map(pdf, refused_url, opacity=0.5)


def test_legend_failed_fetch_strict_raises(monkeypatch, service, refused_url):
    pdf, _ = make_pdf(True, monkeypatch)
    with pytest.raises(PrintServiceError):
        add_legend(pdf, service + '/500')
    with pytest.raises(PrintServiceError):
        add_legend(pdf, refused_url)


def test_legend_failed_fetch_default_gives_pdf(monkeypatch, service):
    pdf, draws = make_pdf(False, monkeypatch)
    add_legend(pdf, service + '/500')
    finish(pdf)
    assert draws == []


def test_good_answers_strict_draw_images(monkeypatch, service):
    pdf, draws = make_pdf(True, monkeypatch)
    add_map(pdf, service + '/png')
    add_map(pdf, service + '/jpeg', img_format='image/jpeg')
    add_map(pdf, service + '/png', serv_type='esri_rest')
    add_map(pdf, service + '/png', opacity=0.5)
    add_legend(pdf, service + '/png')
    out = finish(pdf)
    assert len(draws) == 5
    assert out.count(b'/Subtype /Image') >= 4


def test_unknown_service_type_strict_raises_value_error(monkeypatch, service):
    pdf, _ = make_pdf(True, monkeypatch)
    with pytest.raises(ValueError):
        add_map(pdf, service + '/png', serv_type='wmts')
    with pytest.raises(ValueError):
        add_legend(pdf, service + '/png', serv_type='esri_rest')


def test_unknown_service_type_default_is_skipped(monkeypatch, service):
    pdf, draws = make_pdf(False, monkeypatch)
    add_map(pdf, service + '/png', serv_type='wmts')
    add_legend(pdf, service + '/png', serv_type='esri_rest')
    finish(pdf)
    assert draws == []


@pytest.fixture
def mocked_fetch(monkeypatch):
    calls = []

    def fetch(url, timeout=None):
        calls.append(('plain', timeout))
        return ImageReader(BytesIO(PNG))

    def fetch_with_opacity(url, opacity, timeout=None):
        calls.append(('opacity', timeout))
        return ImageReader(Image.open(BytesIO(PNG)))

    monkeypatch.setattr(pdf_layout, 'get_image', fetch)
    monkeypatch.setattr(pdf_layout, 'get_image_with_opacity', fetch_with_opacity)
    return calls


def draw_all(pdf):
    add_map(pdf, 'http://maps.test/wms')
    add_map(pdf, 'http://maps.test/wms', opacity=0.5)
    add_map(pdf, 'http://maps.test/arcgis/rest/services/x/MapServer', serv_type='esri_rest')
    add_legend(pdf, 'http://maps.test/wms')


def test_default_path_draws_same_images_with_session_timeout(monkeypatch, mocked_fetch):
    monkeypatch.setenv('HTTP_READ_TIMEOUT', '290')
    pdf, draws = make_pdf(False, monkeypatch)
    draw_all(pdf)
    finish(pdf)
    assert len(draws) == 4
    assert mocked_fetch == [('plain', None), ('opacity', None), ('plain', None), ('plain', None)]


def test_strict_path_passes_strict_timeout(monkeypatch, mocked_fetch):
    monkeypatch.setenv('HTTP_CONNECT_TIMEOUT', '5')
    monkeypatch.setenv('PDF_STRICT_READ_TIMEOUT', '20')
    pdf, draws = make_pdf(True, monkeypatch)
    draw_all(pdf)
    finish(pdf)
    assert len(draws) == 4
    assert [t for _, t in mocked_fetch] == [(5.0, 20.0)] * 4
