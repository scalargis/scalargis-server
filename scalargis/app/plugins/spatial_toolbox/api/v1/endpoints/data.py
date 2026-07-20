import io
import json
import logging
import os

from flask import request, send_file
from flask_restx import Resource

from ..endpoints import ns
from ....utils.vector import convert_to_geojson_create_layer, export_geojson_to_format

logger = logging.getLogger(__name__)


@ns.route('/convert2geojson')
class convert2geojson(Resource):
    def options(self):
        return {'Allow': 'POST'}, 200, \
               {'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST',
                'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept, X-API-KEY'
                }

    def post(self):
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

                return data, 200, {'Access-Control-Allow-Origin': '*',
                                    'Access-Control-Allow-Methods': 'POST',
                                    'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept, X-API-KEY'
                                    }
        except Exception as e:
            logger.error(e)
            return {"Success": False, "Message": 'Erro ao processar o ficheiro.', "Data": None}, 500


@ns.route('/export')
class export(Resource):
    def options(self):
        return {'Allow': 'POST'}, 200, \
               {'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST',
                'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept, X-API-KEY'
                }

    def post(self):
        logger = logging.getLogger(__name__)

        try:
            payload = request.get_json(silent=True) or {}
            geojson_data = payload.get('geojson')
            out_format = payload.get('format')
            epsg = payload.get('crs', 4326)

            if isinstance(geojson_data, str):
                geojson_data = json.loads(geojson_data)

            if not geojson_data or not out_format:
                return {"Success": False, "Message": 'Parâmetros em falta (geojson, format).', "Data": None}, 400

            filepath, download_name, mimetype = export_geojson_to_format(geojson_data, out_format, epsg)

            # Read into memory so the temp file can be removed right away
            # (send_file streams the path lazily, after this returns).
            with open(filepath, 'rb') as f:
                buffer = io.BytesIO(f.read())
            try:
                os.remove(filepath)
            except Exception as e:
                logger.debug(e)

            return send_file(buffer, mimetype=mimetype, as_attachment=True,
                             download_name=download_name)
        except ValueError as e:
            logger.error(e)
            return {"Success": False, "Message": str(e), "Data": None}, 400
        except Exception as e:
            logger.error(e)
            return {"Success": False, "Message": 'Erro ao exportar os elementos.', "Data": None}, 500