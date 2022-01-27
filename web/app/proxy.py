import os
import json
import requests
import logging.config

from flask import Flask, request, make_response, current_app

instance_path=os.path.join(os.path.dirname(os.path.abspath(__file__)) + os.sep + '..' + os.sep + 'instance')
app = Flask(__name__, instance_path=instance_path, instance_relative_config=True)


def replace_geoserver_url(url):
    new_url = url

    try:
        if isinstance(current_app.config.get('ROUTE_GEOSERVER'), list):
            if isinstance(current_app.config.get('ROUTE_GEOSERVER')[0], list):
                for s in current_app.config.get('ROUTE_GEOSERVER'):
                    new_url = new_url.replace(s[0], s[1])
            else:
                new_url = new_url.replace(current_app.config.get('ROUTE_GEOSERVER')[0],
                                          current_app.config.get('ROUTE_GEOSERVER')[1])
        logging.info('WMS Url replace: ' + new_url)
    except AttributeError:
        logging.info('WMS Url replace: error')
        pass

    return new_url


def setup_logging(
    default_path=os.path.join(instance_path + os.sep + 'logging_proxy.json'),
    default_level=logging.INFO,
    env_key='LOG_CFG'
):
    """Setup logging configuration

    """
    path = default_path
    value = os.getenv(env_key, None)
    log_config = 'Not defined'
    if value:
        path = value
        log_config = value
    if os.path.exists(path):
        log_config = path
        with open(path, 'rt') as f:
            config = json.load(f)
        logging.config.dictConfig(config)
    else:
        logging.basicConfig(level=default_level)
        log_config = 'basicConfig'

    log = logging.getLogger(__name__)
    log.info('Setup logging: {}'.format(log_config))


def configure_app(flask_app):
    # Load the default configuration
    flask_app.config.from_object('instance.default')

    # Load the configuration from the instance folder
    flask_app.config.from_pyfile('config.py', silent=True)

    # Load the file specified by the APP_CONFIG_FILE environment variable
    if os.environ.get('APP_CONFIG_FILE') and os.path.exists(os.environ.get('APP_CONFIG_FILE')):
        flask_app.config.from_envvar('APP_CONFIG_FILE', silent=True)


def init_wsgi():
    setup_logging()
    configure_app(app)


def load_app():
    setup_logging()
    configure_app(app)

    app.run(host="0.0.0.0", debug=True, use_reloader=True, threaded=True)


@app.route('/proxy', methods=['GET', 'POST'])
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

if __name__ == "__main__":
    load_app()