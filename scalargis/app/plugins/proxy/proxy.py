import logging
import requests
from flask import Blueprint, request, make_response
from app.utils.http import replace_geoserver_url


''' Proxy service '''
module = Blueprint('proxy', __name__, template_folder='templates', static_folder='',
                   static_url_path='', url_prefix='/proxy')

module_code = 'proxy'

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
    if not ("getcapabilities" in url.lower()):
        url = replace_geoserver_url(url)

    s = requests.Session()

    r = None

    cookies = {}
    if 'session' in request.cookies:
        cookies['session'] = request.cookies.get('session')

    for h in request.headers.environ:
        if h.lower() == 'http_referer':
            s.headers.update({'referer': request.headers.environ.get(h)})

    if request.method == 'POST':
        r = s.post(url, data=request.data, cookies=cookies, verify=False)
    else:
        r = s.get(url, cookies=cookies, verify=False)

    resp = make_response(r.content, r.status_code)
    for h in r.headers:
        if h.lower() == 'content-type':
            resp.headers.set(h, r.headers.get(h))

    return resp
