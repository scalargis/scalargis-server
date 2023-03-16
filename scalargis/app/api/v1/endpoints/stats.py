import logging

from flask import request
from flask_restx import Resource

from ..portal.dao import stats as dao_stats
from ..endpoints import check_user, ns_portal as ns


logger = logging.getLogger(__name__)


@ns.route('/stats/viewer_owner_visits')
@ns.response(404, 'Todo not found')
class ViewerOwnerStats(Resource):
    def options(self):
        return {'Allow': 'GET, PUT, DELETE'}, 200, \
               {'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, PUT, DELETE',
                'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept, X-API-KEY'
                }

    '''Show a single todo item and lets you delete them'''

    def get(self):
        '''Fetch a given resource'''
        if (check_user(request)):
            item = dao_stats.get_viewer_owner_visits(request)

            return item, 201, {'Access-Control-Allow-Origin': '*',
                               'Access-Control-Allow-Methods': 'GET, POST PUT, DELETE',
                               'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
                               }
        else:
            return None, 401, {'Access-Control-Allow-Origin': '*',
                               'Access-Control-Allow-Methods': 'GET, POST PUT, DELETE',
                               'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
                               }
@ns.route('/stats/viewer_visits')
@ns.response(404, 'Todo not found')
class Stats(Resource):
    def options(self):
        return {'Allow': 'GET, PUT, DELETE'}, 200, \
               {'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, PUT, DELETE',
                'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept, X-API-KEY'
                }

    '''Show a single todo item and lets you delete them'''

    def get(self):
        '''Fetch a given resource'''
        if (check_user(request)):
            item = dao_stats.get_viewer_visits(request)

            return item, 201, {'Access-Control-Allow-Origin': '*',
                               'Access-Control-Allow-Methods': 'GET, POST PUT, DELETE',
                               'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
                               }
        else:
            return None, 401, {'Access-Control-Allow-Origin': '*',
                               'Access-Control-Allow-Methods': 'GET, POST PUT, DELETE',
                               'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
                               }
@ns.route('/stats/basicstats')
@ns.response(404, 'Todo not found')
class Stats(Resource):
    def options(self):
        return {'Allow': 'GET, PUT, DELETE'}, 200, \
               {'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, PUT, DELETE',
                'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept, X-API-KEY'
                }

    '''Show a single todo item and lets you delete them'''

    def get(self):
        '''Fetch a given resource'''
        if (check_user(request)):
            item = dao_stats.get_basic_stats(request)

            return item, 201, {'Access-Control-Allow-Origin': '*',
                               'Access-Control-Allow-Methods': 'GET, POST PUT, DELETE',
                               'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
                               }
        else:
            return None, 401, {'Access-Control-Allow-Origin': '*',
                               'Access-Control-Allow-Methods': 'GET, POST PUT, DELETE',
                               'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
                               }