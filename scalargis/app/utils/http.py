from datetime import timedelta
from flask import make_response, request, current_app
from functools import update_wrapper
import logging


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
    return (current_app.config.get('SCALARGIS_BASE_URL') or '').rstrip('\/')
