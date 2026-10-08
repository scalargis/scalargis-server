import logging
from urllib.parse import urlparse
import requests
from flask import Blueprint, Response, request, make_response
from app.utils.http import replace_geoserver_url, http_session
from app.utils.settings import get_config_value


''' Proxy service '''
module = Blueprint('proxy', __name__, template_folder='templates', static_folder='',
                   static_url_path='', url_prefix='/proxy')

module_code = 'proxy'

CHUNK_SIZE = 64 * 1024

PASSED_HEADERS = ('content-type', 'content-range', 'accept-ranges')

requests.packages.urllib3.disable_warnings()


@module.route('/index', methods=['GET'])
def index():
    logger = logging.getLogger(__name__)
    logger.debug('Proxy')

    return module_code


''' Proxy route '''
@module.route('/', methods=['GET', 'POST'])
def proxy():
    url = request.args.get('url')
    if not url:
        return _cors(make_response('Missing url parameter', 400))
    if not ("getcapabilities" in url.lower()):
        url = replace_geoserver_url(url)
    if urlparse(url).scheme.lower() not in ('http', 'https'):
        return _cors(make_response('Invalid url parameter', 400))

    headers = {}
    for h in request.headers.environ:
        if h.lower() == 'http_referer':
            headers['referer'] = request.headers.environ.get(h)

    if request.range:
        headers['range'] = request.range.to_header()

    data = request.data if request.method == 'POST' else None

    try:
        r = http_session().request(request.method, url, data=data, headers=headers, verify=False,
                                   stream=True)
    except requests.Timeout:
        logging.getLogger(__name__).warning('Proxy timeout: %s', url)
        resp = make_response('Gateway Timeout', 504)
        return _cors(resp)

    resp = Response(_stream(r), status=r.status_code, direct_passthrough=True)
    resp.headers['Content-Security-Policy'] = 'sandbox'
    for h in r.headers:
        if h.lower() in PASSED_HEADERS:
            resp.headers.set(h, r.headers.get(h))
    if 'content-length' in r.headers and 'content-encoding' not in r.headers:
        resp.headers.set('Content-Length', r.headers.get('content-length'))

    return _cors(resp)


def _stream(r):
    """Yields the upstream body in chunks and closes the upstream connection."""
    try:
        for chunk in r.iter_content(chunk_size=CHUNK_SIZE):
            yield chunk
    except requests.RequestException as err:
        logging.getLogger(__name__).warning('Proxy stream stopped: %s', err)
    finally:
        r.close()


def _cors(resp):
    """Adds the SCALARGIS_PROXY_CORS headers to a proxy response."""
    origins = get_config_value('SCALARGIS_PROXY_CORS')
    if origins == '*':
        resp.headers['Access-Control-Allow-Origin'] = '*'
        resp.headers['Access-Control-Allow-Methods'] = 'PUT,GET,POST,DELETE'
        resp.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
    elif isinstance(origins, list) and 'Origin' in request.headers and request.headers['Origin'] in origins:
        resp.headers['Access-Control-Allow-Origin'] = request.headers['Origin']
        resp.headers['Access-Control-Allow-Methods'] = 'PUT,GET,POST,DELETE'
        resp.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'

    return resp
