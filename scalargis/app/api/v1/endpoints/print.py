import logging
from flask import request
from flask_restx import Resource

from ..portal.parsers import *
from ..portal.serializers import page_simple_viewer
from ..portal.serializers.print import page_print, print_api_model, print_with_viewers_api_model, \
    print_element_api_model, page_print_element, \
    print_group_api_model, print_group_with_viewers_api_model, page_print_group
from ..portal.dao import print as dao_print
from ..endpoints import check_user, ns_portal as ns
from app.utils.constants import ROLE_AUTHENTICATED, ROLE_ADMIN, ROLE_MANAGER


logger = logging.getLogger(__name__)


@ns.route('/prints')
class PrintList(Resource):
    def options(self):
        return {'Allow': 'GET, POST, DELETE'}, 200, \
               {'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, DELETE',
                'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept, X-API-KEY'
                }

    @ns.expect(parser_records_with_page)
    @ns.marshal_with(page_print)
    def get(self):
        """Returns Viewers """
        if (check_user(request, [ROLE_AUTHENTICATED])):
            data = dao_print.get_by_filter(request)
            return data, 200, {'Access-Control-Allow-Origin': '*',
                                'Access-Control-Allow-Headers': 'Content-Type,X-API-KEY'
                                }
        else:
            return 'Bad Credenciais', 401, {'Access-Control-Allow-Origin': '*'}

    @ns.doc('create_print')
    @ns.expect(print_api_model)
    @ns.marshal_with(print_api_model, code=201)
    def post(self):
        '''Create a new print'''
        if (check_user(request, [ROLE_AUTHENTICATED])):
            item = dao_print.create(request.json)
            return item, 201, {'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST',
                'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
                }
        else:
            return None, 401, {'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST',
                'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
                }

    @ns.doc('delete_print(s)')
    @ns.response(204, 'Print(s) deleted')
    def delete(self):
        '''Delete a viewer given its identifier'''
        if (check_user(request, [ROLE_AUTHENTICATED])):
            data = request.args.get('filter')
            status = dao_print.delete_list(data)
            return None, status, {'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST PUT, DELETE',
                'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
                }
        else:
            return None, 401, {'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST PUT, DELETE',
                'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
                }

@ns.route('/prints/<int:id>')
@ns.response(404, 'Todo not found')
@ns.param('id', 'The print identifier')
class Print(Resource):
    def options(self, id):
        return {'Allow': 'GET, PUT, DELETE'}, 200, \
               {'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, PUT, DELETE',
                'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept, X-API-KEY'
                }

    '''Show a single todo item and lets you delete them'''
    @ns.doc('get_print')
    @ns.marshal_with(print_api_model)
    def get(self, id):
        '''Fetch a given resource'''
        if check_user(request):
            item = dao_print.get_by_id(id)
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

    @ns.doc('delete_print')
    @ns.response(204, 'Print deleted')
    def delete(self, id):
        '''Delete a viewer given its identifier'''
        if (check_user(request, [ROLE_AUTHENTICATED])):
            status = dao_print.delete(id)
            return None, status, {'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST PUT, DELETE',
                'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
                }
        else:
            return None, 401, {'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST PUT, DELETE',
                'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
                }

    @ns.expect(print_api_model)
    @ns.marshal_with(print_api_model)
    def put(self, id):
        '''Update a print given its identifier'''
        if check_user(request, [ROLE_AUTHENTICATED]):
            item = dao_print.update(id, request.json)
            if item:
                return item, 201, {'Access-Control-Allow-Origin': '*',
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


@ns.route('/prints/<int:id>/viewers')
@ns.response(404, 'Todo not found')
@ns.param('id', 'The print identifier')
class PrintViewers(Resource):
    def options(self, id):
        return {'Allow': 'GET'}, 200, \
               {'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET',
                'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept, X-API-KEY'
                }

    '''Show print viewers'''

    @ns.doc('get_print_viewers')
    @ns.expect(parser_records_with_page)
    @ns.marshal_with(page_simple_viewer)
    def get(self, id):
        """Returns Print Viewers """
        if (check_user(request, [ROLE_AUTHENTICATED])):
            data = dao_print.get_print_viewers_by_filter(id, request)
            return data, 200, {'Access-Control-Allow-Origin': '*',
                               'Access-Control-Allow-Methods': 'GET',
                               'Access-Control-Allow-Headers': 'Content-Type,X-API-KEY'
                               }
        else:
            return 'Bad Credenciais', 401, {'Access-Control-Allow-Origin': '*'}

# ------------------------------------------

@ns.route('/prints/groups')
class PrintGroupList(Resource):
    def options(self):
        return {'Allow': 'GET, POST, DELETE'}, 200, \
               {'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, DELETE',
                'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept, X-API-KEY'
                }

    @ns.expect(parser_records_with_page)
    @ns.marshal_with(page_print_group)
    def get(self):
        """Returns Print groups """
        if (check_user(request, [ROLE_AUTHENTICATED])):
            data = dao_print.get_print_group_by_filter(request)
            return data, 200, {'Access-Control-Allow-Origin': '*',
                                'Access-Control-Allow-Headers': 'Content-Type,X-API-KEY'
                                }
        else:
            return 'Bad Credenciais', 401, {'Access-Control-Allow-Origin': '*'}

    @ns.doc('create_print_group')
    @ns.expect(print_group_api_model)
    @ns.marshal_with(print_group_api_model, code=201)
    def post(self):
        '''Create a new print group'''
        if (check_user(request, [ROLE_AUTHENTICATED])):
            item = dao_print.create_print_group(request.json)
            return item, 201, {'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST',
                'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
                }
        else:
            return None, 401, {'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST',
                'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
                }

    @ns.doc('delete_print_groups(s)')
    @ns.response(204, 'Print group(s) deleted')
    def delete(self):
        '''Delete a viewer given its identifier'''
        if (check_user(request, [ROLE_AUTHENTICATED])):
            data = request.args.get('filter')
            status = dao_print.delete_print_group_list(data)
            return None, status, {'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST PUT, DELETE',
                'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
                }
        else:
            return None, 401, {'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST PUT, DELETE',
                'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
                }


@ns.route('/prints/groups/<int:id>')
@ns.response(404, 'Todo not found')
@ns.param('id', 'The print group identifier')
class PrintGroup(Resource):
    def options(self, id):
        return {'Allow': 'GET, PUT, DELETE'}, 200, \
               {'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, PUT, DELETE',
                'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept, X-API-KEY'
                }

    '''Show a single todo item and lets you delete them'''
    @ns.doc('get_print_group')
    @ns.marshal_with(print_group_api_model)
    def get(self, id):
        '''Fetch a given resource'''
        if check_user(request):
            item = dao_print.get_print_group_by_id(id)
            if item:
                return item, 200, {'Access-Control-Allow-Origin': '*',
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

    @ns.doc('delete_print_group')
    @ns.response(204, 'Print group deleted')
    def delete(self, id):
        '''Delete a print group given its identifier'''
        if (check_user(request, [ROLE_AUTHENTICATED])):
            status = dao_print.delete_print_group(id)
            return None, status, {'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST PUT, DELETE',
                'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
                }
        else:
            return None, 401, {'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST PUT, DELETE',
                'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
                }

    @ns.expect(print_group_api_model)
    @ns.marshal_with(print_group_api_model)
    def put(self, id):
        '''Update a print group given its identifier'''
        if check_user(request, [ROLE_AUTHENTICATED]):
            item = dao_print.update_print_group(id, request.json)
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


@ns.route('/groups/<int:id>/viewers')
@ns.response(404, 'Todo not found')
@ns.param('id', 'The print identifier')
class PrintGroupViewers(Resource):
    def options(self, id):
        return {'Allow': 'GET'}, 200, \
               {'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET',
                'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept, X-API-KEY'
                }

    '''Show print group viewers'''

    @ns.doc('get_print_group_viewers')
    @ns.expect(parser_records_with_page)
    @ns.marshal_with(page_simple_viewer)
    def get(self, id):
        """Returns Print Viewers """
        if (check_user(request, [ROLE_AUTHENTICATED])):
            data = dao_print.get_print_group_viewers_by_filter(id, request)
            return data, 200, {'Access-Control-Allow-Origin': '*',
                               'Access-Control-Allow-Methods': 'GET',
                               'Access-Control-Allow-Headers': 'Content-Type,X-API-KEY'
                               }
        else:
            return 'Bad Credenciais', 401, {'Access-Control-Allow-Origin': '*'}

# -------------------------------------------

@ns.route('/prints/elements')
class PrintElementsList(Resource):
    def options(self):
        return {'Allow': 'GET, POST, DELETE'}, 200, \
               {'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, DELETE',
                'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept, X-API-KEY'
                }

    @ns.expect(parser_records_with_page)
    @ns.marshal_with(page_print_element)
    def get(self):
        """Returns Print elements """
        if check_user(request):
            data = dao_print.get_print_element_by_filter(request)
            return data, 200, {'Access-Control-Allow-Origin': '*',
                                'Access-Control-Allow-Headers': 'Content-Type,X-API-KEY'
                                }
        else:
            return 'Bad Credenciais', 401, {'Access-Control-Allow-Origin': '*'}

    @ns.doc('create_print_element')
    @ns.expect(print_element_api_model)
    @ns.marshal_with(print_element_api_model, code=201)
    def post(self):
        '''Create a new print'''
        if check_user(request, [ROLE_ADMIN, ROLE_MANAGER]):
            item = dao_print.create_print_element(request.json)
            return item, 201, {'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST',
                'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
                }
        else:
            return None, 401, {'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST',
                'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
                }

    @ns.doc('delete_print_element(s)')
    @ns.response(204, 'Print element(s) deleted')
    def delete(self):
        '''Delete a print element given its identifier'''
        if check_user(request, [ROLE_ADMIN, ROLE_MANAGER]):
            data = request.args.get('filter')
            status = dao_print.delete_print_element_list(data)
            return None, status, {'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST PUT, DELETE',
                'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
                }
        else:
            return None, 401, {'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST PUT, DELETE',
                'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
                }

@ns.route('/prints/elements/<int:id>')
@ns.response(404, 'Todo not found')
@ns.param('id', 'The print element identifier')
class PrintElement(Resource):
    def options(self, id):
        return {'Allow': 'GET, PUT, DELETE'}, 200, \
               {'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, PUT, DELETE',
                'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept, X-API-KEY'
                }

    '''Show a single todo item and lets you delete them'''
    @ns.doc('get_print')
    @ns.marshal_with(print_element_api_model)
    def get(self, id):
        '''Fetch a given resource'''
        if check_user(request):
            item = dao_print.get_print_element_by_id(id)
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

    @ns.doc('delete_print_element')
    @ns.response(204, 'Print element deleted')
    def delete(self, id):
        '''Delete a viewer given its identifier'''
        if check_user(request, [ROLE_ADMIN, ROLE_MANAGER]):
            status = dao_print.delete_print_element(id)
            return None, status, {'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST PUT, DELETE',
                'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
                }
        else:
            return None, 401, {'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST PUT, DELETE',
                'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
                }

    @ns.expect(print_element_api_model)
    @ns.marshal_with(print_element_api_model)
    def put(self, id):
        '''Update a print given its identifier'''
        if check_user(request, [ROLE_ADMIN, ROLE_MANAGER]):
            item = dao_print.update_print_element(id, request.json)
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