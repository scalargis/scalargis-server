import logging
from flask import request
from flask_restx import Resource

from ..endpoints import ns
from ....utils.vector import convert_to_geojson_create_layer

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