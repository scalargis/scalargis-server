import logging
from flask import request
from flask_restx import Resource, fields, reqparse

from ..endpoints import ns
from app.plugins.spatial_toolbox.utils.analysis import get_intersect_results, export_intersect_results

logger = logging.getLogger(__name__)


intersect_parser = reqparse.RequestParser()
intersect_parser.add_argument('format', type=str, required=False, default='json', help='Output format')
intersect_parser.add_argument('code', type=str, required=True, help='Intersect config')
intersect_parser.add_argument('geom_wkt', type=str, required=True, help='Intersect geometry')
intersect_parser.add_argument('geom_srid', type=int, required=False, default=4326, help='SRID of Intersect geometry')
intersect_parser.add_argument('buffer', type=int, required=False, default=0, help='Intersect buffer')
intersect_parser.add_argument('buffer_srid', type=int, required=False, default=3857, help='SRID to calculate intersect buffer')
intersect_parser.add_argument('out_srid', type=int, required=False, default=4326, help='SRID of output geometries')


intersect_params = ns.model('Intersect parameters', {
    'format': fields.String(required=False, default='json'),
    'code':fields.String(required=True),
    'geom_wkt': fields.String(required=True),
    'geom_srid': fields.Integer(required=False, default=4326),
    'buffer': fields.Float(required=False, default=0),
    'buffer_srid': fields.Integer(required=False, default=3857),
    'out_srid': fields.Integer(required=False, default=4326)
})


@ns.route('/intersect')
class Intersect(Resource):
    def options(self):
        return {'Allow': 'OPTIONS, GET, POST'}, 200, \
               {'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS, GET, POST',
                'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept, X-API-KEY'
                }

    @ns.expect(intersect_parser, validate=False)
    def get(self):
        logger = logging.getLogger(__name__)

        try:
            format = request.args.get("format", "json")
            code = request.args.get("code", None)
            geom_wkt = request.args.get("geom_wkt", None)
            geom_srid = request.args.get("geom_srid", 4326)
            buffer = request.args.get("buffer", 0)
            buffer_srid = request.args.get("buffer_srid", 3857)
            out_srid = request.args.get("out_srid", 4326)

            data = get_intersect_results(config_code=code, geom_wkt=geom_wkt, geom_srid=geom_srid, buffer=buffer,
                                         buffer_srid=buffer_srid, out_srid=out_srid)

            if not code:
                return {"Success": False, "Message": "Parameter 'code' is required", "Data": None}, 400
            if not geom_wkt:
                return {"Success": False, "Message": "Parameter 'geom_wkt' is required", "Data": None}, 400

            if format != 'json':
                return export_intersect_results(data, format)

            return data, 200, {'Access-Control-Allow-Origin': '*',
                               'Access-Control-Allow-Methods': 'GET',
                               'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept, X-API-KEY'
                               }
        except Exception as e:
            logger.error(e)
            return {"Success": False, "Message": 'An error occurred while processing.', "Data": None}, 500

    @ns.expect(intersect_params, validate=False)
    def post(self):
        logger = logging.getLogger(__name__)

        try:
            # If JSON
            if request.is_json:
                data = request.get_json()
            else:
                # If form-data or x-www-form-urlencoded
                data = request.form.to_dict()

            format = data.get("format", "json")
            code = data.get("code", None)
            geom_wkt = data.get("geom_wkt", [])
            geom_srid = data.get("geom_srid", 4326)
            buffer = data.get("buffer", 0)
            buffer_srid = data.get("buffer_srid", 3857)
            out_srid = data.get("out_srid", 4326)

            if not code:
                return {"Success": False, "Message": "Parameter 'code' is required", "Data": None}, 400
            if not geom_wkt:
                return {"Success": False, "Message": "Parameter 'geom_wkt' is required", "Data": None}, 400

            data = get_intersect_results(config_code=code, geom_wkt=geom_wkt, geom_srid=geom_srid, buffer=buffer,
                                         buffer_srid=buffer_srid, out_srid=out_srid)

            if format != 'json':
                return export_intersect_results(data, format)

            return data, 200, {'Access-Control-Allow-Origin': '*',
                               'Access-Control-Allow-Methods': 'POST',
                               'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept, X-API-KEY'
                               }
        except Exception as e:
            logger.error(e)
            return {"Success": False, "Message": 'An error occurred while processing.', "Data": None}, 500