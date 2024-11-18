import logging
from datetime import datetime
from flask import request
from flask_restx import Resource
from app.utils.security import get_user_token
from app.utils.security import get_user_from_token, get_user_from_auth_token
from app.utils import constants
from ..portal.parsers import *
from ..portal.serializers import *
from ..portal.dao import security as dao_security
from ..endpoints import check_user, ns_authentication, ns_security


logger = logging.getLogger(__name__)


class AuthenticationDAO(object):
    def __init__(self, authenticated, token):
        self.authenticated = authenticated
        self.token = token


authentication_model = ns_authentication.model('Authentication Model', {
    'username': fields.String,
    'password': fields.String
})


@ns_authentication.route('/authenticate')
class SecurityToken(Resource):
    """Get User Token"""
    def options(self):
        return {'Allow': 'GET, POST'}, 200, \
               {'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, GET',
                'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
                }

    def get(self):
        """Gets user associated with given token"""

        data = {}

        if not 'authkey' in request.args or not request.args.get('authkey'):
            return data

        authkey = request.args.get('authkey')

        user = get_user_from_auth_token(authkey)

        if user and user.is_active and (not user.auth_token_expire or user.auth_token_expire >= datetime.now()):
            data = {
                'user': user.username
            }

        return data

    @ns_authentication.expect(authentication_model)
    def post(self):
        """Authenticates user and returns authentication token"""

        authenticated = False

        if request.is_json:
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
            #ns_authentication.abort(401, 'Bad credencials')
            return 'Bad credentials', 401, {'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST',
                'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
                }

        data = {
            'authenticated': authenticated,
            'token': token or '',
            'username': username,
            'name': user.name,
            'userroles': user_roles,
            'auth_token': user.auth_token if user.auth_token and
                            (not user.auth_token_expire or user.auth_token_expire >= datetime.now()) else ''
        }

        return data, {'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST',
                'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
                }

# --------------------------------------------------------------------

@ns_security.route('/account')
class Account(Resource):
    """Account"""
    def options(self):
        return {'Allow': 'GET, PUT'}, 200, \
               {'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'PUT, GET',
                'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
                }

    @ns_security.doc('get_account_info')
    @ns_security.marshal_with(account_api_model)
    def get(self):
        item, status = dao_security.get_account(request)
        return item, status, {'Access-Control-Allow-Origin': '*',
                              'Access-Control-Allow-Methods': 'GET',
                              'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
                              }

    @ns_security.expect(account_api_model)
    def put(self):
        '''Update account'''
        item, status = dao_security.update_account(request)
        return item, status, {'Access-Control-Allow-Origin': '*',
                           'Access-Control-Allow-Methods': 'PUT',
                           'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
                           }

#---------------------------------------------------------------------

@ns_security.route('/reset_password')
class ResetPassword(Resource):
    """Password Reset"""
    def options(self):
        return {'Allow': 'POST'}, 200, \
               {'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST',
                'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
                }

    def post(self):
        """Send email for password reset"""

        data, status = dao_security.send_password_reset(request)

        return data, status, {'Access-Control-Allow-Origin': '*',
                              'Access-Control-Allow-Methods': 'POST',
                              'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
                              }


@ns_security.route('/reset_password_validation')
class PageValidationPassword(Resource):
    """Password Reset"""
    def options(self):
        return {'Allow': 'POST'}, 200, \
               {'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST',
                'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
                }

    def post(self):
        """Send email for password reset"""

        data, status = dao_security.password_reset_validation(request)

        return data, status, {'Access-Control-Allow-Origin': '*',
                              'Access-Control-Allow-Methods': 'POST, GET',
                              'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
                              }


@ns_security.route('/set_password')
class SetPassword(Resource):
    """Reset password"""
    def options(self):
        return {'Allow': 'POST'}, 200, \
               {'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST',
                'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
                }

    def post(self):
        """Reset password"""

        data, status = dao_security.set_password(request)

        return data, status, {'Access-Control-Allow-Origin': '*',
                              'Access-Control-Allow-Methods': 'POST, GET',
                              'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
                              }


@ns_security.route('/update_password')
class UpdatePassword(Resource):
    """Reset password"""
    def options(self):
        return {'Allow': 'POST'}, 200, \
               {'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST',
                'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
                }

    def put(self):
        """Change password"""

        data, status = dao_security.update_password(request)

        return data, status, {'Access-Control-Allow-Origin': '*',
                              'Access-Control-Allow-Methods': 'POST, GET',
                              'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
                              }


@ns_security.route('/register_user')
class RegistrationUser(Resource):
    """User Registration"""
    def options(self):
        return {'Allow': 'POST'}, 200, \
               {'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST',
                'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept, X-API-KEY'
                }

    def post(self):
        """User registration and validation code"""
        resp, code = dao_security.register_user(request)
        return resp, code, {'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'POST',
        'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept, X-API-KEY'
        }


@ns_security.route('/registration/send_confirmation')
class RegistrationSendEmail(Resource):
    """Send register confirmation"""
    def options(self):
        return {'Allow': 'POST'}, 200, \
               {'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST',
                'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
                }

    def post(self):
        """Send email with register confirmation"""

        data, status = dao_security.send_confirmation(request)

        return data, status, {'Access-Control-Allow-Origin': '*',
                  'Access-Control-Allow-Methods': 'POST',
                  'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
                  }


    @ns_security.route('/registration/confirmation')
    class RegistrationConfirmation(Resource):
        """Register confirmation"""

        def options(self):
            return {'Allow': 'GET, POST'}, 200, \
                   {'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'POST, GET',
                    'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
                    }

        def get(self):
            """Confirm user registration with given token"""

            data, status = dao_security.confirm_email(request)

            return data, status, {'Access-Control-Allow-Origin': '*',
                                  'Access-Control-Allow-Methods': 'POST, GET',
                                  'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
                                  }

        def post(self):
            """Confirm user registration with given token and returns authentication token"""

            data, status = dao_security.confirm_email(request)

            return data, status, {'Access-Control-Allow-Origin': '*',
                                  'Access-Control-Allow-Methods': 'POST, GET',
                                  'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
                                  }

#---------------------------------------------------------------------

@ns_security.route('/roles')
class RolesList(Resource):
    def options(self):
        return {'Allow': 'GET, POST, PUT, DELETE'}, 200, \
               {'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE',
                'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept, X-API-KEY'
                }

    @ns_security.expect(parser_records_with_page)
    @ns_security.marshal_with(page_roles)
    def get(self):
        """Returns Roles"""
        if (check_user(request)):
            return dao_security.get_role(request), 200, {'Access-Control-Allow-Origin': '*'}
        else:
            return None, 401, {'Access-Control-Allow-Origin': '*'}

    @ns_security.doc('create_role')
    @ns_security.expect(role_api_model)
    @ns_security.marshal_with(role_api_model, code=201)
    def post(self):
        '''Create a new table record'''
        # if (check_user(request)):
        item = dao_security.create_role(request.json)
        return item, 201, {'Access-Control-Allow-Origin': '*',
                           'Access-Control-Allow-Methods': 'POST',
                           'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
                           }
        # else:
        #    return None, 401, {'Access-Control-Allow-Origin': '*',
        #                       'Access-Control-Allow-Methods': 'POST',
        #                       'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
        #                       }

    @ns_security.doc('delete_role values')
    @ns_security.response(204, 'Generic values deleted')
    def delete(self):
        '''Delete a record given its identifier'''
        # if (check_user(request)):
        data = request.args.get('filter')
        status = dao_security.delete_role_list(data)
        return None, status, {'Access-Control-Allow-Origin': '*',
                              'Access-Control-Allow-Methods': 'GET, POST PUT, DELETE',
                              'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
                              }
        # else:
        #    return None, 401, {'Access-Control-Allow-Origin': '*',
        #                       'Access-Control-Allow-Methods': 'GET, POST PUT, DELETE',
        #                       'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
        #                       }

@ns_security.route('/roles/<int:id>')
@ns_security.response(404, 'Todo not found')
@ns_security.param('id', 'The record identifier')
class Roles(Resource):
    def options(self, id):
        return {'Allow': 'GET, PUT, DELETE'}, 200, \
               {'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, PUT, DELETE',
                'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept, X-API-KEY'
                }

    '''Show a single todo item and lets you delete them'''

    @ns_security.doc('get_role')
    @ns_security.marshal_with(role_api_model)
    def get(self, id):
        '''Fetch a given resource'''
        if (check_user(request)):
            item = dao_security.get_role_by_id(id)
            return item, 201, {'Access-Control-Allow-Origin': '*',
                               'Access-Control-Allow-Methods': 'GET, POST PUT, DELETE',
                               'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
                               }
        else:
            return None, 401, {'Access-Control-Allow-Origin': '*',
                               'Access-Control-Allow-Methods': 'GET, POST PUT, DELETE',
                               'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
                               }

    @ns_security.doc('delete_role')
    @ns_security.response(204, 'Record deleted')
    def delete(self, id):
        '''Delete a record given its identifier'''
        # if (check_user(request)):
        status = dao_security.delete_role(id)
        return None, status, {'Access-Control-Allow-Origin': '*',
                              'Access-Control-Allow-Methods': 'GET, POST PUT, DELETE',
                              'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
                              }
        # else:
        #    return None, 401, {'Access-Control-Allow-Origin': '*',
        #                       'Access-Control-Allow-Methods': 'GET, POST PUT, DELETE',
        #                       'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
        #                       }

    @ns_security.expect(role_api_model)
    @ns_security.marshal_with(role_api_model)
    def put(self, id):
        '''Update a record given its identifier'''
        item = dao_security.update_role(id, request.json)
        return item, 200, {'Access-Control-Allow-Origin': '*',
                           'Access-Control-Allow-Methods': 'PUT',
                           'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
                           }

#--------------------------------------------------------------------

@ns_security.route('/groups')
class GroupsList(Resource):
    def options(self):
        return {'Allow': 'GET, POST, PUT, DELETE'}, 200, \
               {'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE',
                'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept, X-API-KEY'
                }

    @ns_security.expect(parser_records_with_page)
    @ns_security.marshal_with(page_groups)
    def get(self):
        """Returns Groups"""
        if (check_user(request)):
            return dao_security.get_group(request), 200, {'Access-Control-Allow-Origin': '*'}
        else:
            return None, 401, {'Access-Control-Allow-Origin': '*'}

    @ns_security.doc('create_group')
    @ns_security.expect(group_api_model)
    @ns_security.marshal_with(group_api_model, code=201)
    def post(self):
        '''Create a new table record'''
        # if (check_user(request)):
        item = dao_security.create_group(request.json)
        return item, 201, {'Access-Control-Allow-Origin': '*',
                           'Access-Control-Allow-Methods': 'POST',
                           'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
                           }
        # else:
        #    return None, 401, {'Access-Control-Allow-Origin': '*',
        #                       'Access-Control-Allow-Methods': 'POST',
        #                       'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
        #                       }

    @ns_security.doc('delete_group values')
    @ns_security.response(204, 'Generic values deleted')
    def delete(self):
        '''Delete a record given its identifier'''
        # if (check_user(request)):
        data = request.args.get('filter')
        status = dao_security.delete_group_list(data)
        return None, status, {'Access-Control-Allow-Origin': '*',
                              'Access-Control-Allow-Methods': 'GET, POST PUT, DELETE',
                              'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
                              }
        # else:
        #    return None, 401, {'Access-Control-Allow-Origin': '*',
        #                       'Access-Control-Allow-Methods': 'GET, POST PUT, DELETE',
        #                       'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
        #                       }

@ns_security.route('/groups/<int:id>')
@ns_security.response(404, 'Todo not found')
@ns_security.param('id', 'The record identifier')
class Groups(Resource):
    def options(self, id):
        return {'Allow': 'GET, PUT, DELETE'}, 200, \
               {'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, PUT, DELETE',
                'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept, X-API-KEY'
                }

    '''Show a single todo item and lets you delete them'''

    @ns_security.doc('get_group')
    @ns_security.marshal_with(group_api_model)
    def get(self, id):
        '''Fetch a given resource'''
        if (check_user(request)):
            item = dao_security.get_group_by_id(id)
            return item, 201, {'Access-Control-Allow-Origin': '*',
                               'Access-Control-Allow-Methods': 'GET, POST PUT, DELETE',
                               'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
                               }
        else:
            return None, 401, {'Access-Control-Allow-Origin': '*',
                               'Access-Control-Allow-Methods': 'GET, POST PUT, DELETE',
                               'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
                               }

    @ns_security.doc('delete_group')
    @ns_security.response(204, 'Record deleted')
    def delete(self, id):
        '''Delete a record given its identifier'''
        # if (check_user(request)):
        status = dao_security.delete_group(id)
        return None, status, {'Access-Control-Allow-Origin': '*',
                              'Access-Control-Allow-Methods': 'GET, POST PUT, DELETE',
                              'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
                              }
        # else:
        #    return None, 401, {'Access-Control-Allow-Origin': '*',
        #                       'Access-Control-Allow-Methods': 'GET, POST PUT, DELETE',
        #                       'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
        #                       }

    @ns_security.expect(group_api_model)
    @ns_security.marshal_with(group_api_model)
    def put(self, id):
        '''Update a record given its identifier'''
        item = dao_security.update_group(id, request.json)
        return item, 200, {'Access-Control-Allow-Origin': '*',
                           'Access-Control-Allow-Methods': 'PUT',
                           'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
                           }

#--------------------------------------------------------------------

@ns_security.route('/users')
class UsersList(Resource):
    def options(self):
        return {'Allow': 'GET, POST, PUT, DELETE'}, 200, \
               {'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE',
                'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept, X-API-KEY'
                }

    @ns_security.expect(parser_records_with_page)
    @ns_security.marshal_with(page_users)
    def get(self):
        """Returns Users"""
        if (check_user(request)):
            return dao_security.get_users(request), 200, {'Access-Control-Allow-Origin': '*'}
        else:
            return None, 401, {'Access-Control-Allow-Origin': '*'}

    @ns_security.doc('create_user')
    @ns_security.expect(user_api_model)
    @ns_security.marshal_with(user_api_model, code=201)
    def post(self):
        '''Create a new table record'''
        #if (check_user(request)):
        item = dao_security.create_user(request.json)
        return item, 201, {'Access-Control-Allow-Origin': '*',
                           'Access-Control-Allow-Methods': 'POST',
                           'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
                           }
        #else:
        #    return None, 401, {'Access-Control-Allow-Origin': '*',
        #                       'Access-Control-Allow-Methods': 'POST',
        #                       'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
        #                       }

    @ns_security.doc('delete_user values')
    @ns_security.response(204, 'Generic values deleted')
    def delete(self):
        '''Delete a record given its identifier'''
        #if (check_user(request)):
        data = request.args.get('filter')
        status = dao_security.delete_user_list(data)
        return None, status, {'Access-Control-Allow-Origin': '*',
                              'Access-Control-Allow-Methods': 'GET, POST PUT, DELETE',
                              'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
                              }
        #else:
        #    return None, 401, {'Access-Control-Allow-Origin': '*',
        #                       'Access-Control-Allow-Methods': 'GET, POST PUT, DELETE',
        #                       'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
        #                       }


@ns_security.route('/users/<int:id>')
@ns_security.response(404, 'Todo not found')
@ns_security.param('id', 'The record identifier')
class Users(Resource):
    def options(self, id):
        return {'Allow': 'GET, PUT, DELETE'}, 200, \
               {'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, PUT, DELETE',
                'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept, X-API-KEY'
                }

    '''Show a single todo item and lets you delete them'''

    @ns_security.doc('get_user')
    @ns_security.marshal_with(user_api_model)
    def get(self, id):
        '''Fetch a given resource'''
        if (check_user(request)):
            item = dao_security.get_user_by_id(id)
            return item, 201, {'Access-Control-Allow-Origin': '*',
                               'Access-Control-Allow-Methods': 'GET, POST PUT, DELETE',
                               'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
                               }
        else:
            return None, 401, {'Access-Control-Allow-Origin': '*',
                               'Access-Control-Allow-Methods': 'GET, POST PUT, DELETE',
                               'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
                               }

    @ns_security.doc('delete_user')
    @ns_security.response(204, 'Record deleted')
    def delete(self, id):
        '''Delete a record given its identifier'''
        #if (check_user(request)):
        status = dao_security.delete_user(id)
        return None, status, {'Access-Control-Allow-Origin': '*',
                              'Access-Control-Allow-Methods': 'GET, POST PUT, DELETE',
                              'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
                              }
        #else:
        #    return None, 401, {'Access-Control-Allow-Origin': '*',
        #                       'Access-Control-Allow-Methods': 'GET, POST PUT, DELETE',
        #                       'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
        #                       }

    @ns_security.expect(user_api_model)
    @ns_security.marshal_with(user_api_model)
    def put(self, id):
        '''Update a record given its identifier'''
        item = dao_security.update_user(id, request.json)
        return item, 200, {'Access-Control-Allow-Origin': '*',
                           'Access-Control-Allow-Methods': 'PUT',
                           'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
                           }