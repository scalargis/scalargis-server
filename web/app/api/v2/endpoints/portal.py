import logging
from flask import request
from flask_restx import Resource

from ..portal.parsers import *
from ..portal.serializers import *
from ..portal.dao import component as dao_component, security as dao_security
from ..endpoints import check_user, ns_portal as ns
from app.utils.constants import ROLE_AUTHENTICATED


logger = logging.getLogger(__name__)


@ns.route('/components')
class ComponentsList(Resource):
    def options(self):
        return {'Allow': 'GET, POST, DELETE'}, 200, \
               {'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, DELETE',
                'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept, X-API-KEY'
                }

    @ns.expect(parser_records_with_page)
    @ns.marshal_with(page_viewer)
    def get(self):
        """Returns Components """
        if (check_user(request)):
            data = dao_component.get_by_filter(request)
            return data, 200, {'Access-Control-Allow-Origin': '*',
                                'Access-Control-Allow-Headers': 'Content-Type,X-API-KEY'
                                }
        else:
            return 'Bad Credenciais', 401, {'Access-Control-Allow-Origin': '*'}

    @ns.doc('create_component')
    @ns.expect(component_api_model)
    @ns.marshal_with(component_api_model, code=201)
    def post(self):
        '''Create a new component'''
        if (check_user(request)):
            item = dao_component.create(request.json)
            return item, 201, {'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST',
                'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
                }
        else:
            return None, 401, {'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST',
                'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
                }

    @ns.doc('delete_components(s)')
    @ns.response(204, 'Components(s) deleted')
    def delete(self):
        '''Delete a camponent given its identifier'''
        if (check_user(request)):
            data = request.args.get('filter')
            status = None #portal_func.delete_planos(data)
            return None, status, {'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST PUT, DELETE',
                'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
                }
        else:
            return None, 401, {'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST PUT, DELETE',
                'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
                }


@ns.route('/components/<int:id>')
@ns.response(404, 'Todo not found')
@ns.param('id', 'The component identifier')
class Component(Resource):
    def options(self, id):
        return {'Allow': 'GET, PUT, DELETE'}, 200, \
               {'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, PUT, DELETE',
                'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept, X-API-KEY'
                }

    '''Show a single todo item and lets you delete them'''
    @ns.doc('get_component')
    @ns.marshal_with(component_api_model)
    def get(self, id):
        '''Fetch a given resource'''
        if check_user(request):
            item = dao_component.get_by_id(id)
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

    @ns.doc('delete_component')
    @ns.response(204, 'Component deleted')
    def delete(self, id):
        '''Delete a component given its identifier'''
        if (check_user(request)):
            status = dao_component.delete(id)
            return None, status, {'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST PUT, DELETE',
                'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
                }
        else:
            return None, 401, {'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST PUT, DELETE',
                'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
                }

    @ns.expect(component_api_model)
    @ns.marshal_with(component_api_model)
    def put(self, id):
        '''Update a component given its identifier'''
        if (check_user(request)):
            item = dao_component.update(id, request.json)
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

#------------------------------------------------------------

@ns.route('/viewers/<int:viewer_id>/components')
class ViewerComponentList(Resource):
    def options(self, viewer_id):
        return {'Allow': 'GET, POST, DELETE'}, 200, \
               {'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, DELETE',
                'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept, X-API-KEY'
                }

    @ns.doc('get_viewer_component')
    @ns.expect(parser_records_with_page)
    @ns.marshal_with(page_viewer_component)
    def get(self, viewer_id):
        """Returns Viewer Components """
        if check_user(request):
            data = dao_component.get_viewer_components_by_filter(viewer_id, request)
            return data, 200, {'Access-Control-Allow-Origin': '*',
                                'Access-Control-Allow-Headers': 'Content-Type,X-API-KEY'
                                }
        else:
            return 'Bad Credenciais', 401, {'Access-Control-Allow-Origin': '*'}

    @ns.doc('create_viewer_component')
    @ns.expect(viewer_component_api_model)
    @ns.marshal_with(viewer_component_api_model, code=201)
    def post(self, viewer_id):
        '''Create a new viewer_component'''
        if check_user(request):
            item = dao_component.create_viewer_component(viewer_id, request.json)
            return item, 201, {'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST',
                'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
                }
        else:
            return None, 401, {'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST',
                'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
                }

    @ns.doc('delete_viewer_components(s)')
    @ns.response(204, 'Viewer Component(s) deleted')
    def delete(self):
        '''Delete viewer camponent given its identifiers'''
        if (check_user(request)):
            data = request.args.get('filter')
            status = None #portal_func.delete_planos(data)
            return None, status, {'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST PUT, DELETE',
                'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
                }
        else:
            return None, 401, {'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST PUT, DELETE',
                'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
                }

@ns.route('/viewers/<int:viewer_id>/components/<int:id>')
@ns.response(404, 'Todo not found')
@ns.param('viewer_id', 'The viewer identifier')
@ns.param('id', 'The component identifier')
class ViewerComponent(Resource):
    def options(self, viewer_id, id):
        return {'Allow': 'GET, PUT, DELETE'}, 200, \
               {'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, PUT, DELETE',
                'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept, X-API-KEY'
                }

    '''Show a single todo item and lets you delete them'''
    @ns.doc('get_viewer_component')
    @ns.marshal_with(viewer_component_api_model)
    def get(self, viewer_id, id):
        '''Fetch a given resource'''
        if check_user(request):
            item = dao_component.get_viewer_component_by_id(viewer_id, id)
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

    @ns.doc('delete_viewer_component')
    @ns.response(204, 'Viewer Component deleted')
    def delete(self, viewer_id, id):
        '''Delete a viewer component given its identifier'''
        if (check_user(request)):
            status = dao_component.delete_viewer_component(viewer_id, id)
            return None, status, {'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST PUT, DELETE',
                'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
                }
        else:
            return None, 401, {'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST PUT, DELETE',
                'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
                }

    @ns.expect(viewer_component_api_model)
    @ns.marshal_with(viewer_component_api_model)
    def put(self, viewer_id, id):
        '''Update a viewer_ component given its identifier'''
        if (check_user(request)):
            item = dao_component.update_viewer_component(viewer_id, id, request.json)
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

#------------------------------------------------------

@ns.route('/roles')
class RolesList(Resource):
    def options(self):
        return {'Allow': 'GET, POST, DELETE'}, 200, \
               {'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, DELETE',
                'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept, X-API-KEY'
                }

    @ns.expect(parser_records_with_page)
    @ns.marshal_with(page_roles)
    def get(self):
        """Returns Roles """
        if (check_user(request)):
            data = dao_security.get_roles_by_filter(request)
            return data, 200, {'Access-Control-Allow-Origin': '*',
                                'Access-Control-Allow-Headers': 'Content-Type,X-API-KEY'
                                }
        else:
            return 'Bad Credenciais', 401, {'Access-Control-Allow-Origin': '*'}