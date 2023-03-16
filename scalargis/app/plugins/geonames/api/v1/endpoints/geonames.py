import logging
from flask_restx import Resource

from app.plugins.geonames.api.v1.geonames import geonames_func
from ..endpoints import ns

logger = logging.getLogger(__name__)


@ns.route('/search')
class search(Resource):
    def options(self):
        return {'Allow': 'GET, POST, DELETE'}, 200, \
               {'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET',
                'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept, X-API-KEY'
                }

    def get(self):
        """Returns geonames search results"""
        data, code = geonames_func.search()
        return data, code, {'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET',
        'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept, X-API-KEY'
        }