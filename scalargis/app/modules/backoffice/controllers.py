import logging

from flask import Response

from . import mod
from app.utils.http import get_script_root, get_base_url, read_app_index


@mod.route('/backoffice', defaults={'path': ''})
@mod.route('/backoffice/', defaults={'path': ''})
@mod.route('/backoffice/<path:path>')
def index(path):
    logger = logging.getLogger(__name__)
    logger.debug('Backoffice request')

    root_path = get_script_root()
    base_url = get_base_url()

    in_html = read_app_index('backoffice')
    out_html = in_html.replace("__SCALARGIS_ROOT_PATH__", root_path)
    out_html = out_html.replace("__SCALARGIS_ROOT_PATH_BASE_URL__", base_url)
    out_html = out_html.replace('="/static/backoffice/', '="' + root_path + '/static/backoffice/')

    return Response(out_html, mimetype='text/html')
