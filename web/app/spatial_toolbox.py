import os
import json
import requests
import logging.config
import os.path
import io
import uuid
from datetime import datetime
from PIL import Image
from osgeo import gdal
import fiona
from fiona import crs

from flask import Flask, Blueprint, current_app, send_file, request, jsonify, render_template, url_for, Response
from flask_security import current_user

from instance import settings
from app.utils import http

instance_path=os.path.join(os.path.dirname(os.path.abspath(__file__)) + os.sep + '..' + os.sep + 'instance')
app = Flask(__name__, instance_path=instance_path, instance_relative_config=True)

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

    if 'PROJ_LIB_PATH' in app.config.keys() and app.config['PROJ_LIB_PATH']:
        os.environ['PROJ_LIB'] = app.config['PROJ_LIB_PATH']
    if 'GDAL_DATA_PATH' in app.config.keys() and app.config['GDAL_DATA_PATH']:
        os.environ['GDAL_DATA'] = app.config['GDAL_DATA_PATH']

    app.run(host="0.0.0.0", debug=True, use_reloader=True, threaded=True)


@app.route('/index', methods=['GET'])
def index():
    logger = logging.getLogger(__name__)
    logger.debug('Spatial Toolbox')

    return '{0}; {1}'.format(os.environ['PROJ_LIB'], os.environ['GDAL_DATA'])


@app.route('/convert2geojson', methods=['POST', 'OPTIONS'])
@http.crossdomain(origin='*', methods=['POST', 'OPTIONS'], headers='Origin, Content-Type, X-API-KEY')
def convert_to_geojson_create_layer():
    logger = logging.getLogger(__name__)

    try:
        data = []

        fiona.drvsupport.supported_drivers['LIBKML'] = 'r'
        fiona.drvsupport.supported_drivers['kml'] = 'rw'  # enable KML support which is disabled by default
        fiona.drvsupport.supported_drivers['KML'] = 'rw'  # enable KML support which is disabled by default

        files = request.files.getlist("files")
        #Compatibility with legacy version
        if not files:
            files = request.files.getlist("files[]")

        metadata = {
            "filename": None,
            "size": None,
            "driver": None,
            "crs": None,
            "schema": None
        }

        if len(files) > 0:
            file = files[0]

            metadata['filename'] = file.filename

            filename = str(uuid.uuid4()) + os.path.splitext(file.filename)[1]
            filepath = os.path.join(settings.APP_TMP_DIR, filename)

            file.save(filepath)

            metadata['size'] = os.stat(filepath).st_size

            #dd = open(filepath, 'rb').read()

            if os.path.splitext(file.filename)[1].lower() == '.zip':
                filepath = 'zip://' + filepath

            file_uuid = str(uuid.uuid4().hex)

            with fiona.open(filepath, 'r') as source:
                metadata['driver'] = source.driver
                metadata['crs'] = source.meta.get('crs')
                metadata['extent'] = source.bounds
                metadata['schema'] = source.meta.get('schema')

                out_filepath = os.path.join(settings.APP_TMP_DIR, file_uuid + '.geojson')
                with fiona.open(
                        out_filepath,
                        'w',
                        encoding='utf-8',
                        driver='GeoJSON',
                        #crs=fiona.crs.from_epsg(4326),
                        #crs=fiona.crs.from_epsg(3763),
                        crs_wkt=source.crs_wkt,
                        schema={ 'geometry': 'Unknown', 'properties': source.schema['properties']}) as sink:
                    for rec in source:
                        sink.write(rec)

                #for feature in source:
                #    s = feature

            try:
                if os.path.exists(filepath.lstrip('zip://')):
                    os.remove(filepath.lstrip('zip://'))
            except Exception as e:
                logger.debug(e)

            metadata_out_filepath = os.path.join(settings.APP_TMP_DIR, file_uuid + '.metadata')
            if metadata :
                with open(metadata_out_filepath, 'w', encoding="utf8") as metadata_outfile:
                    json.dump(metadata, metadata_outfile)

            '''
            with open(out_filepath, encoding="utf8") as f:
                data = json.load(f)

                user = None
                if not current_user or not current_user.is_authenticated:
                    if 'X-API-KEY' in request.headers:
                        token = request.headers['X-API-KEY']
                        user = get_user_from_token(token)
                    else:
                        user = current_user

                record = UserDataLayer()
                record.uuid = layer_uuid
                record.data_geojson = json.dumps(data)
                if metadata:
                    record.metadata_geojson = json.dumps(metadata)
                record.is_private = False
                record.allow_anonymous = True
                record.is_active = True
                record.created_at = datetime.now()
                if (user and current_user.is_authenticated):
                    record.id_user_create = user.id
                    record.owner_id = user.id

                db.session.add(record)
                db.session.commit()
                db.session.refresh(record)
            '''

            #Build url for resource
            #url = url_for('api2.app_app_data_layer', layer_id=file_uuid)
            url = '/api/v2/app/data/layer/{0}'.format(file_uuid)

            return jsonify(Success=True, Message=None, Data={"uuid": file_uuid, "url": url, "metadata": metadata})
        else:
            return jsonify(Success=False, Message='Erro', Data=None)
    except fiona.errors.DriverError as e:
        logger.error(e)
        return jsonify(Success=False, Message='O ficheiro não é válido.', Data=None)
    except Exception as e:
        logger.error(e)
        return jsonify(Success=False, Message='Erro ao processar o ficheiro.', Data=None)


if __name__ == "__main__":
    load_app()