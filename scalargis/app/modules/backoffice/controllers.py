import os
import logging

from flask import current_app, Response

from . import mod
from app.utils.http import get_script_root, get_base_url


@mod.route('/backoffice', defaults={'path': ''})
@mod.route('/backoffice/', defaults={'path': ''})
@mod.route('/backoffice/<path:path>')
def index(path):
    logger = logging.getLogger(__name__)
    logger.debug('Backoffice request')

    root_path = get_script_root()
    base_url = get_base_url()

    f = open(os.path.join(current_app.static_folder, 'backoffice', 'index.html'), "r", encoding='utf-8')
    in_html = f.read()
    out_html = in_html.replace("__SCALARGIS_ROOT_PATH__", root_path)
    out_html = out_html.replace("__SCALARGIS_ROOT_PATH_BASE_URL__", base_url)

    return Response(out_html, mimetype='text/html')
