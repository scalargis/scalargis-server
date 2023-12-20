import logging

from flask import request
from flask_restx import Resource

from ..portal.parsers import *
from ..portal.serializers import *
from ..portal.dao import viewer as dao_viewer
from ..endpoints import check_user, ns_portal as ns
from app.utils.constants import ROLE_AUTHENTICATED, ROLE_ADMIN, ROLE_MANAGER

logger = logging.getLogger(__name__)


@ns.route('/viewers')
class ViewerList(Resource):
    def options(self):
        return {'Allow': 'GET, POST, DELETE'}, 200, \
               {'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, DELETE',
                'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept, X-API-KEY'
                }

    @ns.expect(parser_records_with_page)
    @ns.marshal_with(page_viewer)
    def get(self):
        """Returns Viewers """
        if (check_user(request, [ROLE_AUTHENTICATED])):
            data = dao_viewer.get_by_filter(request)
            return data, 200, {'Access-Control-Allow-Origin': '*',
                                'Access-Control-Allow-Headers': 'Content-Type,X-API-KEY'
                                }
        else:
            return 'Bad Credenciais', 401, {'Access-Control-Allow-Origin': '*'}

    @ns.doc('create_viewer')
    @ns.expect(viewer_api_model)
    @ns.marshal_with(viewer_api_model, code=201)
    def post(self):
        '''Create a new viewer'''
        if (check_user(request, [ROLE_AUTHENTICATED])):
            item = dao_viewer.create(request.json)
            return item, 201, {'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST',
                'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
                }
        else:
            return None, 401, {'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST',
                'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
                }

    @ns.doc('delete_viewer(s)')
    @ns.response(204, 'Viewer(s) deleted')
    def delete(self):
        '''Delete a viewer given its identifier'''
        if (check_user(request, [ROLE_AUTHENTICATED])):
            data = request.args.get('filter')
            status = dao_viewer.delete_list(data)
            return None, status, {'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST PUT, DELETE',
                'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
                }
        else:
            return None, 401, {'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST PUT, DELETE',
                'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
                }


@ns.route('/viewers/list')
class ViewerListAll(Resource):
    def options(self):
        return {'Allow': 'GET, POST, DELETE'}, 200, \
               {'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, DELETE',
                'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept, X-API-KEY'
                }

    def get(self):
        """Returns Viewers List """
        if (check_user(request, [ROLE_AUTHENTICATED])):
            data = dao_viewer.get_list(request)
            return data, 200, {'Access-Control-Allow-Origin': '*',
                                'Access-Control-Allow-Headers': 'Content-Type,X-API-KEY'
                                }
        else:
            return 'Bad Credenciais', 401, {'Access-Control-Allow-Origin': '*'}

    @ns.doc('get index page viewers')
    def post(self):
        """Returns Index page Viewers List """
        if (check_user(request, [ROLE_AUTHENTICATED])):
            data = dao_viewer.get_list(request, is_index=True)
            return data, 201, {'Access-Control-Allow-Origin': '*',
                                'Access-Control-Allow-Headers': 'Content-Type,X-API-KEY'
                                }
        else:
            return 'Bad Credenciais', 401, {'Access-Control-Allow-Origin': '*'}


@ns.route('/viewers/<int:id>')
@ns.response(404, 'Todo not found')
@ns.param('id', 'The viewer identifier')
class Viewer(Resource):
    def options(self, id):
        return {'Allow': 'GET, PUT, DELETE'}, 200, \
               {'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, PUT, DELETE',
                'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept, X-API-KEY'
                }

    '''Show a single todo item and lets you delete them'''
    @ns.doc('get_viewer')
    @ns.marshal_with(viewer_api_model)
    def get(self, id):
        '''Fetch a given resource'''
        if check_user(request):
            item = dao_viewer.get_by_id(id)
            if item:
                return item, 201, {'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'GET, POST PUT, DELETE',
                    'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
                    }
            else:
                return item, 404, {'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'GET, POST PUT, DELETE',
                    'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
                    }
        else:
            return None, 401, {'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST PUT, DELETE',
                'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
                }

    @ns.doc('delete_viewer')
    @ns.response(204, 'Viewer deleted')
    def delete(self, id):
        '''Delete a viewer given its identifier'''
        if (check_user(request, [ROLE_AUTHENTICATED])):
            status = dao_viewer.delete(id)
            return None, status, {'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST PUT, DELETE',
                'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
                }
        else:
            return None, 401, {'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST PUT, DELETE',
                'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
                }

    @ns.expect(viewer_api_model)
    @ns.marshal_with(viewer_api_model)
    def put(self, id):
        '''Update a viewer given its identifier'''
        if check_user(request, [ROLE_AUTHENTICATED]):
            item = dao_viewer.update(id, request.json)
            if item:
                return item, 200, {'Access-Control-Allow-Origin': '*',
                        'Access-Control-Allow-Methods': 'PUT',
                        'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
                        }
            else:
                return item, 404, {'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'GET, POST PUT, DELETE',
                    'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
                    }
        else:
            return None, 401, {'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST PUT, DELETE',
                'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
                }
