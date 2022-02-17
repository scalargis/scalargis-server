import os
import logging
import requests
from flask import Blueprint, render_template, request, abort, current_app, make_response, send_from_directory
from flask_security import current_user

from .. import mod

@mod.route('/v2/map', defaults={'path': ''})
@mod.route('/v2/map/', defaults={'path': ''})
@mod.route('/v2/map/<path:path>')
@mod.route('/v2/mapa', defaults={'path': ''})
@mod.route('/v2/mapa/', defaults={'path': ''})
@mod.route('/v2/mapa/<path:path>')
def index2(path):
    logger = logging.getLogger(__name__)
    logger.debug('This message should go to the log file - Map')

    return send_from_directory(os.path.join(current_app.static_folder, 'frontend'), 'index.html')