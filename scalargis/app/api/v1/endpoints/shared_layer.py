import logging

from flask import request
from flask_restx import Resource

from ..portal.dao import shared_layer as dao_shared_layer
from ..portal.dao import history as dao_history
from ..endpoints import get_user, ns_portal as ns
from app.utils.constants import ROLE_ADMIN


logger = logging.getLogger(__name__)

CORS = {'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept, X-API-KEY'}


def refusal(req):
    """Returns the body and status of a refusal for a caller that is not an admin, or None for an admin."""
    user = get_user(req)
    if user is None:
        return {'message': 'Authentication required'}, 401
    if not any(role.name == ROLE_ADMIN for role in user.roles):
        return {'message': 'Forbidden'}, 403
    return None


@ns.route('/shared-layers')
class SharedLayerList(Resource):
    def options(self):
        return {'Allow': 'GET, POST'}, 200, dict(CORS, **{'Access-Control-Allow-Methods': 'GET, POST'})

    def get(self):
        '''Returns a page of shared layers with the type and the usage count of each one'''
        refused = refusal(request)
        if refused:
            return refused[0], refused[1], CORS
        return dao_shared_layer.get_by_filter(request), 200, CORS

    def post(self):
        '''Creates a shared layer'''
        refused = refusal(request)
        if refused:
            return refused[0], refused[1], CORS
        record = dao_shared_layer.create(request.get_json(silent=True))
        return dao_shared_layer.to_dict(record), 201, CORS


@ns.route('/shared-layers/<int:id>')
@ns.param('id', 'The shared layer identifier')
class SharedLayerItem(Resource):
    def options(self, id):
        return {'Allow': 'GET, PUT, DELETE'}, 200, dict(CORS, **{'Access-Control-Allow-Methods': 'GET, PUT, DELETE'})

    def get(self, id):
        '''Returns a shared layer'''
        refused = refusal(request)
        if refused:
            return refused[0], refused[1], CORS
        record = dao_shared_layer.get_by_id(id)
        if record is None:
            return {'message': 'Shared layer not found'}, 404, CORS
        return dao_shared_layer.to_dict(record), 200, CORS

    def put(self, id):
        '''Updates a shared layer'''
        refused = refusal(request)
        if refused:
            return refused[0], refused[1], CORS
        record = dao_shared_layer.update(id, request.get_json(silent=True))
        if record is None:
            return {'message': 'Shared layer not found'}, 404, CORS
        return dao_shared_layer.to_dict(record), 200, CORS

    def delete(self, id):
        '''Deletes a shared layer that no viewer names'''
        refused = refusal(request)
        if refused:
            return refused[0], refused[1], CORS
        if not dao_shared_layer.delete(id):
            return {'message': 'Shared layer not found'}, 404, CORS
        return {'id': id}, 200, CORS


@ns.route('/shared-layers/<int:id>/usage')
@ns.param('id', 'The shared layer identifier')
class SharedLayerUsage(Resource):
    def get(self, id):
        '''Returns the viewers that name a shared layer'''
        refused = refusal(request)
        if refused:
            return refused[0], refused[1], CORS
        record = dao_shared_layer.get_by_id(id)
        if record is None:
            return {'message': 'Shared layer not found'}, 404, CORS
        return dao_shared_layer.usage(record.code), 200, CORS


@ns.route('/shared-layers/<int:id>/history', defaults={'hid': None})
@ns.route('/shared-layers/<int:id>/history/<int:hid>')
@ns.param('id', 'The shared layer identifier')
class SharedLayerHistory(Resource):
    def get(self, id, hid):
        '''Returns the saved states of a shared layer, or one state with its snapshot'''
        refused = refusal(request)
        if refused:
            return refused[0], refused[1], CORS
        record = dao_shared_layer.get_by_id(id)
        return dao_history.respond('shared_layer', record, hid, True)
