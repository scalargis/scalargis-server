import logging
from flask import request
from flask_restx import Namespace, Resource, fields
from app.plugins.sample.api.v1.sample.parsers import *
from app.plugins.sample.api.v1.sample.serializers import *

from ..endpoints import ns, check_user


@ns.route('/data')
class DataList(Resource):
    def options(self):
        return {'Allow': 'GET'}, 200, \
               {'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET',
                'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept, X-API-KEY'
                }

    #@ns.marshal_with(concelho_api_model)
    def get(self):
        """Returns Data"""

        data = [
            {'id': 1, 'name': 'teste1'},
            {'id': 2, 'name': 'teste2'}
        ]
        return data, 200, {'Access-Control-Allow-Origin': '*'}


@ns.route('/protected_data')
class ProtectedDataList(Resource):
    def options(self):
        return {'Allow': 'GET'}, 200, \
               {'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET',
                'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept, X-API-KEY'
                }

    def get(self):
        """Returns Data """

        if check_user(request):
            data = [
                {'id': 1, 'name': 'teste1'},
                {'id': 2, 'name': 'teste2'}
            ]

            return data, 200, {'Access-Control-Allow-Origin': '*',
                                'Access-Control-Allow-Headers': 'Content-Type,X-API-KEY'
                                }
        else:
            return 'Bad Credenciais', 401, {'Access-Control-Allow-Origin': '*'}
