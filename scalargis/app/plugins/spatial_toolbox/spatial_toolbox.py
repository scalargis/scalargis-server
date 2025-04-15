import logging
import os
import os.path
import site

import fiona

from flask import Blueprint, request

from app.main import app
from app.utils import http

from .database.schema import setup_db

from .api.v1.endpoints import ns as v1_spatial_toolbox_ns
from .api.restx import api
from .utils.vector import convert_to_geojson_create_layer

logger = logging.getLogger(__name__)

''' Legacy service '''
module = Blueprint('spatial_toolbox', __name__, template_folder='templates', static_folder='',
                   static_url_path='', url_prefix='/spatial_toolbox')

module_api = Blueprint('spatial_toolbox_api', __name__, template_folder='templates', static_folder='',
                   static_url_path='', url_prefix='/spatial_toolbox/api')

module_code = 'spatial_toolbox'

api.init_app(module_api)
api.add_namespace(v1_spatial_toolbox_ns)

# Set PROJ and GDAL paths
venv_folder = site.getsitepackages()[1]
if 'PROJ_LIB_PATH' in app.config.keys() and app.config['PROJ_LIB_PATH']:
    if os.path.isdir(app.config['PROJ_LIB_PATH']):
        os.environ['PROJ_LIB'] = app.config['PROJ_LIB_PATH']
else:
    if os.path.isdir(os.path.join(venv_folder, 'osgeo/data/proj')):
        os.environ['PROJ_LIB'] = os.path.join(venv_folder, 'osgeo/data/proj')

if 'GDAL_DATA_PATH' in app.config.keys() and app.config['GDAL_DATA_PATH']:
    if os.path.isdir(app.config['GDAL_DATA_PATH']):
        os.environ['GDAL_DATA'] = app.config['GDAL_DATA_PATH']
else:
    if os.path.isdir(os.path.join(venv_folder, 'osgeo/data/gdal')):
        os.environ['GDAL_DATA'] = os.path.join(venv_folder, 'osgeo/data/gdal')

try:
    created = setup_db()
    if created:
        logger.info('SpatialToolbox API: schema created!')
except Exception as e:
    logger.error('SpatialToolbox API - Database Initialization error: {}'.format(str(e)))

@module.route('/index', methods=['GET'])
def index():
    logger = logging.getLogger(__name__)
    logger.debug('Spatial Toolbox')

    return module_code


''' Legacy route '''
@module.route('/convert2geojson', methods=['POST'])
@module.route('/convert2geojson/layer/create', methods=['POST', 'OPTIONS'])
@http.crossdomain(origin='*', methods=['POST', 'OPTIONS'], headers='Origin, Content-Type, X-API-KEY')
def convert_file_to_geojson():
    logger = logging.getLogger(__name__)

    try:
        persist = True

        if 'persist' in request.form and (request.form.get('persist') == 'false' or
                                 request.form and request.form.get('persist') == False):
            persist = False

        files = request.files.getlist("files")
        #Compatibility with legacy version
        if not files:
            files = request.files.getlist("files[]")

        if len(files) > 0:
            file = files[0]

            data = convert_to_geojson_create_layer(file, persist)

            return {"Success": True, "Message": None, "Data": data}, 200
        else:
            return {"Success": False, "Message": None, "Data": None}, 200

    except fiona.errors.DriverError as e:
        logger.error(e)
        return {"success": False, "message": 'O ficheiro não é válido.', "data": None}, 500
    except Exception as e:
        logger.error(e)
        return {"success": False, "Message": 'Erro ao processar o ficheiro.', "data": None}, 500

