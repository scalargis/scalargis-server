import logging

from flask import Response

from . import mod
from app.utils.settings import get_default_locale
from app.utils.http import get_script_root, get_base_url, read_app_index


@mod.route('/<path:path>')
@mod.route('/map', defaults={'path': ''})
@mod.route('/map/', defaults={'path': ''})
@mod.route('/map/<path:path>')
@mod.route('/mapa', defaults={'path': ''})
@mod.route('/mapa/', defaults={'path': ''})
@mod.route('/mapa/<path:path>')
def index(path):
    logger = logging.getLogger(__name__)
    logger.debug('Map request')

    root_path = get_script_root()
    base_url = get_base_url()
    default_locale = get_default_locale()

    in_html = read_app_index('viewer')
    out_html = in_html.replace("__SCALARGIS_ROOT_PATH__", root_path)
    out_html = out_html.replace("__SCALARGIS_ROOT_PATH_BASE_URL__", base_url)
    out_html = out_html.replace("__SCALARGIS_DEFAULT_LOCALE__", default_locale)
    out_html = out_html.replace('="/static/viewer/', '="' + root_path + '/static/viewer/')

    return Response(out_html, mimetype='text/html')
