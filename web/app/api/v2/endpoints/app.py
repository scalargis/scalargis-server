import logging
from flask import request
from flask_restx import Resource, inputs

from ..portal.parsers import *
from ..portal.serializers import *
from ..portal.dao import viewer as dao_viewer, component as dao_component, app as dao_app
from ..endpoints import check_user, ns_app as ns


logger = logging.getLogger(__name__)


@ns.route('/viewer')
@ns.response(404, 'Todo not found')
class AppDefaultViewer(Resource):
    def options(self):
        return {'Allow': 'GET'}, 200, \
               {'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST',
                'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept, X-API-KEY'
                }

    '''Get a viewer'''
    @ns.doc('get_viewer')
    def get(self):
        '''Fetch a given resource'''
        item, status = dao_app.get_app_default_viewer()
        return item, status, {'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST',
            'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
            }

    @ns.doc('create_viewer')
    @ns.expect(viewer_app_api_model)
    @ns.marshal_with(viewer_app_saved_api_model, code=201)
    def post(self):
        '''Create a new viewer'''
        item = dao_viewer.app_create(request.json)
        return item, 201, {'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST',
            'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
            }

@ns.route('/viewer/<path:viewer_id_or_slug>')
@ns.response(404, 'Todo not found')
@ns.param('viewer_id_or_slug', 'The viewer identifier')
class AppViewer(Resource):
    def options(self, viewer_id_or_slug):
        return {'Allow': 'GET'}, 200, \
               {'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, PUT',
                'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept, X-API-KEY'
                }

    '''Get a viewer'''
    @ns.doc('get_viewer')
    def get(self, viewer_id_or_slug):
        '''Fetch a given resource'''
        item, status = dao_app.get_app_viewer(viewer_id_or_slug)
        return item, status, {'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, PUT',
            'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
            }

    @ns.doc('save_viewer')
    @ns.expect(viewer_app_api_model)
    @ns.marshal_with(viewer_app_saved_api_model, code=201)
    def put(self, viewer_id_or_slug):
        '''Update viewer'''
        item, status = dao_viewer.app_update(viewer_id_or_slug, request.json)
        return item, status, {'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, PUT',
            'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
            }


@ns.route('/viewer/session/<path:viewer_id_or_slug>')
@ns.response(404, 'Todo not found')
@ns.param('viewer_id_or_slug', 'The viewer identifier')
class AppViewerSession(Resource):
    def options(self, viewer_id_or_slug):
        return {'Allow': 'GET'}, 200, \
               {'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, PUT',
                'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept, X-API-KEY'
                }

    '''Get a viewer'''
    @ns.doc('get_viewer')
    def get(self, viewer_id_or_slug):
        '''Fetch a given resource'''
        item, status = dao_app.get_app_viewer(viewer_id_or_slug, True)
        return item, status, {'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST',
            'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
            }

    @ns.doc('save_viewer_session')
    @ns.expect(viewer_app_api_model)
    def post(self, viewer_id_or_slug):
        '''Update viewer'''
        item, status = dao_app.save_viewer_session(viewer_id_or_slug, request.json)
        return item, status, {'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST',
            'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
            }


@ns.route('/viewer/<int:viewer_id>/print/group/<int:group_id>/details')
@ns.response(404, 'Todo not found')
@ns.param('viewer_id', 'The viewer identifier')
@ns.param('group_id', 'The print group identifier')
class AppPrintGroupDetails(Resource):
    def options(self, viewer_id, group_id):
        return {'Allow': 'POST'}, 200, \
               {'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST',
                'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept, X-API-KEY'
                }

    '''Get a print group details'''
    @ns.doc('get_print_group_details')
    @ns.doc(params={'geom_filter': {'description': 'Geometry filter (WKT)',
                                'type': 'str'}})
    @ns.doc(params={'geom_srid': {'description': 'Geometry filter SRID',
                                'type': 'int'}})
    def post(self, viewer_id, group_id):
        '''Fetch a given resource'''
        item, status = dao_app.get_app_viewer_print_group_details(viewer_id, group_id)
        return item, status, {'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST',
            'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
            }

@ns.route('/viewer/<int:viewer_id>/print/<string:print_code>/generate')
@ns.response(404, 'Todo not found')
@ns.param('viewer_id', 'The viewer identifier')
@ns.param('print_code', 'The print identifier')
class AppPrintGenerate(Resource):
    def options(self, viewer_id, print_code):
        return {'Allow': 'POST'}, 200, \
               {'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST',
                'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept, X-API-KEY'
                }

    '''Generate Print'''
    @ns.doc('do_print_generate')
    def post(self, viewer_id, print_code):
        '''Generate print'''
        item, status = dao_app.get_app_viewer_print_generate(viewer_id, print_code)
        return item, status, {'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST',
            'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
            }


@ns.route('/viewer/<int:viewer_id>/print/merge')
@ns.response(404, 'Todo not found')
@ns.param('viewer_id', 'The viewer identifier')
class AppPrintMerge(Resource):
    def options(self, viewer_id):
        return {'Allow': 'POST'}, 200, \
               {'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST',
                'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept, X-API-KEY'
                }

    '''Merge Print'''
    @ns.doc('do_print_merge')
    def post(self, viewer_id):
        '''Generate print'''
        item, status = dao_app.get_app_viewer_print_merge(viewer_id)
        return item, status, {'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST',
            'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
            }


@ns.route('/data/layer/<string:layer_id>')
@ns.response(404, 'Todo not found')
@ns.param('layer_id', 'The layer identifier (id or uuid)')
class AppDataLayer(Resource):
    def options(self, layer_id):
        return {'Allow': 'GET'}, 200, \
               {'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET',
                'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept, X-API-KEY'
                }

    '''Get a print group details'''
    @ns.doc('get_data_layer')
    def get(self, layer_id):
        '''Fetch a given resource'''
        item, status = dao_app.get_data_layer(layer_id)
        return item, status, {'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET',
            'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
            }


@ns.route('/utils/transcoord')
@ns.response(404, 'Todo not found')
class AppUtilsTransCoord(Resource):
    def options(self):
        return {'Allow': 'POST'}, 200, \
               {'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST',
                'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept, X-API-KEY'
                }

    '''Transform coordinates'''
    @ns.doc('get_trans_coord')
    def post(self):
        '''Fetch a given resource'''
        item, status = dao_viewer.app_transcoord(request.json)
        return item, status, {'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST',
            'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
            }

@ns.route('/viewer/<path:viewer_id>/contact_message')
@ns.response(404, 'Todo not found')
@ns.param('viewer_id', 'The viewer identifier')
class AppContactMessage(Resource):
    def options(self, viewer_id):
        return {'Allow': 'POST'}, 200, \
               {'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST',
                'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept, X-API-KEY'
                }

    '''Post viewer contact message'''
    @ns.doc('viewer_post_contact_message')
    @ns.expect(viewer_contact_message_app_api_model)
    def post(self, viewer_id):
        '''Post message viewer'''
        item, status = dao_app.send_viewer_contact_message(viewer_id, request.json)
        return item, status, {'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST',
            'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
            }


@ns.route('/backoffice')
@ns.response(404, 'Todo not found')
class AppBackoffice(Resource):
    def options(self):
        return {'Allow': 'GET'}, 200, \
               {'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET',
                'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept, X-API-KEY'
                }

    '''Get backoffice config'''
    @ns.doc('get_backoffice')
    def get(self):
        '''Fetch a given resource'''
        item, status = dao_app.get_app_backoffice()
        return item, status, {'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET',
            'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
            }