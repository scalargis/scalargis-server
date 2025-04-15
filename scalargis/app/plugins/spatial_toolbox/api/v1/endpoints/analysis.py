import logging
from flask import request
from flask_restx import Resource

from ..endpoints import ns
from app.plugins.spatial_toolbox.utils.analysis import get_intersect_results, export_intersect_results

logger = logging.getLogger(__name__)


@ns.route('/intersect')
class Intersect(Resource):
    def options(self):
        return {'Allow': 'POST'}, 200, \
               {'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET',
                'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept, X-API-KEY'
                }

    def get(self):
        logger = logging.getLogger(__name__)

        try:
            format = request.args.get("format", "json")
            code = request.args.get("code", None)
            geom_wkt = request.args.get("geom_wkt", [])
            geom_srid = request.args.get("geom_srid", 4326)
            buffer = request.args.get("buffer", 0)
            buffer_srid = request.args.get("buffer_srid", 3857)
            out_srid = request.args.get("out_srid", 4326)

            data = get_intersect_results(config_code=code, geom_wkt=geom_wkt, geom_srid=geom_srid, buffer=buffer,
                                         buffer_srid=buffer_srid, out_srid=out_srid)

            if (format != 'json'):
                return export_intersect_results(data, format)

            return data, 200, {'Access-Control-Allow-Origin': '*',
                               'Access-Control-Allow-Methods': 'POST',
                               'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept, X-API-KEY'
                               }
        except Exception as e:
            logger.error(e)
            return {"Success": False, "Message": 'Erro ao processar.', "Data": None}, 500
