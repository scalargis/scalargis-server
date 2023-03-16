import logging
from flask import request
from flask_restx import Resource

from ..portal.parsers import *
from ..portal.serializers import *
from ..portal.dao import generic as dao_generic
from ..endpoints import check_user, ns_portal as ns

logger = logging.getLogger(__name__)


@ns.route('/lists/', defaults={'table': None})
@ns.route('/lists/<string:table>')
class GenericList(Resource):
    def __init__(self, api=None, entity_name=None, *args, **kwargs):
        #self.api = api
        super(GenericList, self).__init__(api, *args, **kwargs)
        self.entity_name = entity_name

    def options(self, table=None):
        return {'Allow': 'GET, POST, PUT, DELETE'}, 200, \
               {'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE',
                'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept, X-API-KEY'
                }

    @ns.expect(parser_records_with_page)
    @ns.marshal_with(page_generic)
    def get(self, table=None):
        """Returns Dominio"""
        if (check_user(request)):
            return dao_generic.get_generic(table or self.entity_name, request), 200, {'Access-Control-Allow-Origin': '*'}
        else:
            return None, 401, {'Access-Control-Allow-Origin': '*'}

    @ns.doc('create_generic')
    @ns.expect(generic_api_model)
    @ns.marshal_with(generic_api_model, code=201)
    def post(self, table=None):
        '''Create a new table record'''
        #if (check_user(request)):
        item = dao_generic.create_generic(table or self.entity_name, request.json)
        return item, 201, {'Access-Control-Allow-Origin': '*',
                           'Access-Control-Allow-Methods': 'POST',
                           'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
                           }
        #else:
        #    return None, 401, {'Access-Control-Allow-Origin': '*',
        #                       'Access-Control-Allow-Methods': 'POST',
        #                       'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
        #                       }

    @ns.doc('delete_generic values')
    @ns.response(204, 'Generic values deleted')
    def delete(self, table=None):
        '''Delete a record given its identifier'''
        #if (check_user(request)):
        data = request.args.get('filter')
        status = dao_generic.delete_generic_list(table or self.entity_name, data)
        return None, status, {'Access-Control-Allow-Origin': '*',
                              'Access-Control-Allow-Methods': 'GET, POST PUT, DELETE',
                              'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
                              }
        #else:
        #    return None, 401, {'Access-Control-Allow-Origin': '*',
        #                       'Access-Control-Allow-Methods': 'GET, POST PUT, DELETE',
        #                       'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
        #                       }


#@ns.route('/lists/', defaults={'table': None})
@ns.route('/lists/<string:table>/<int:id>')
@ns.response(404, 'Todo not found')
@ns.param('id', 'The record identifier')
class Generic(Resource):
    def __init__(self, api=None, entity_name=None, *args, **kwargs):
        super(Generic, self).__init__(api, *args, **kwargs)
        self.entity_name = entity_name

    def options(self, id, table=None):
        return {'Allow': 'GET, PUT, DELETE'}, 200, \
               {'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, PUT, DELETE',
                'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept, X-API-KEY'
                }

    '''Show a single todo item and lets you delete them'''

    @ns.doc('get_generic')
    @ns.marshal_with(generic_api_model)
    def get(self, id, table=None):
        '''Fetch a given resource'''
        if (check_user(request)):
            item = dao_generic.get_generic_by_id(table or self.entity_name, id)
            return item, 201, {'Access-Control-Allow-Origin': '*',
                               'Access-Control-Allow-Methods': 'GET, POST PUT, DELETE',
                               'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
                               }
        else:
            return None, 401, {'Access-Control-Allow-Origin': '*',
                               'Access-Control-Allow-Methods': 'GET, POST PUT, DELETE',
                               'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
                               }

    @ns.doc('delete_generic')
    @ns.response(204, 'Record deleted')
    def delete(self, id, table=None):
        '''Delete a record given its identifier'''
        #if (check_user(request)):
        status = dao_generic.delete_generic(table or self.entity_name, id)
        return None, status, {'Access-Control-Allow-Origin': '*',
                              'Access-Control-Allow-Methods': 'GET, POST PUT, DELETE',
                              'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
                              }
        #else:
        #    return None, 401, {'Access-Control-Allow-Origin': '*',
        #                       'Access-Control-Allow-Methods': 'GET, POST PUT, DELETE',
        #                       'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
        #                       }

    @ns.expect(generic_api_model)
    @ns.marshal_with(generic_api_model)
    def put(self, id, table=None):
        '''Update a record given its identifier'''
        item = dao_generic.update_generic(table or self.entity_name, id, request.json)
        return item, 200, {'Access-Control-Allow-Origin': '*',
                           'Access-Control-Allow-Methods': 'PUT',
                           'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
                           }
