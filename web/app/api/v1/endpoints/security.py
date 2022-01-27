import logging
import json
from flask import request
import flask_restx
from flask_restx import Namespace, Resource, fields, reqparse
from app.utils.security import get_user_token
from app.utils.security import get_user_from_token
from app.utils import constants
from app.api.v1.security.parsers import parser
from app.api.v1.security.serializers import model

logger = logging.getLogger(__name__)

ns = Namespace('authentication', description='Operations related with authentication')


class AuthenticationDAO(object):
    def __init__(self, authenticated, token):
        self.authenticated = authenticated
        self.token = token

'''
@ns.route('/authenticate')
class SecurityToken(Resource):
'''
    #'''Get User Token'''
'''
    @ns.expect(parser)
    @ns.marshal_with(model)
    def post(self, **kwargs):
'''
        #'''Authenticates user and returns authentication token'''
'''
        authenticated = False
        token = None
        username = None
        password = None

        try:
            args = parser.parse_args()
            username = args.get('username')
            password = args.get('password')
        except Exception as exp:
            if 'username' in request.form and 'password' in request.form:
                username = request.form.get('username')
                password = request.form.get('password')

        if username:
            token = get_user_token(username, password)

        if token:
            authenticated = True

        data = {
            'authenticated': authenticated,
            'token': token or ''
        }

        return AuthenticationDAO(authenticated=authenticated, token=token)
'''


input_model = ns.model('Model', {
    'username': fields.String,
    'password': fields.String
})


@ns.route('/authenticate')
class SecurityToken(Resource):
    """Get User Token"""
    def options(self):
        return {'Allow': 'POST'}, 200, \
               {'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST',
                'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
                }

    @ns.expect(input_model)
    def post(self):
        """Authenticates user and returns authentication token"""

        authenticated = False

        if request.json:
            username = request.json.get('username')
            password = request.json.get('password')
        else:
            cred = json.loads(request.data.decode('utf-8'))
            username = cred.get('username')
            password = cred.get('password')

        token = get_user_token(username, password)

        if token:
            authenticated = True
            user = get_user_from_token(token)

            user_roles = []
            for ru in user.roles:
                user_roles.append(ru.name)
            user_roles.append(constants.ROLE_AUTHENTICATED)

        else:
            ns.abort(401, 'Bad credencials')

        data = {
            'authenticated': authenticated,
            'token': token or '',
            'username': username,
            'userroles': user_roles
        }

        return data, {'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST',
                'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
                }
