import logging

from flask import Blueprint, request, render_template, jsonify
from flask_security import current_user

from app.plugins.sample.api.v1.endpoints import ns as v1_sample_ns
from app.plugins.sample.api.restx import api

module = Blueprint('sample', __name__, template_folder='templates', static_folder='static',
                   static_url_path='/plugins/sample/static', url_prefix='/sample')

module_api = Blueprint('sample_api', __name__, template_folder='templates', static_folder='static',
                   static_url_path='/plugins/sample/static', url_prefix='/sample/api')

modulo_codigo = 'sample'

api.init_app(module_api)
api.add_namespace(v1_sample_ns)


@module.route('/index', methods=['GET'])
def sample_index():
    logger = logging.getLogger(__name__)
    logger.debug('This message should go to the log file - map')

    return render_template("sample_index.html")
