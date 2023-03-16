import logging
from flask import request
from flask_restx import Resource

from ..portal.parsers import *
from ..portal.serializers.notification import notification_api_model, page_notification
from ..portal.dao import notification as dao_notification
from ..endpoints import check_user, ns_portal as ns
from app.utils.constants import ROLE_AUTHENTICATED


logger = logging.getLogger(__name__)


@ns.route('/notifications')
class NotificationList(Resource):
    def options(self):
        return {'Allow': 'GET, POST, DELETE'}, 200, \
               {'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, DELETE',
                'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept, X-API-KEY'
                }

    @ns.expect(parser_records_with_page)
    @ns.marshal_with(page_notification)
    def get(self):
        """Returns Notifications """
        if (check_user(request, [ROLE_AUTHENTICATED])):
            data = dao_notification.get_by_filter(request)
            return data, 200, {'Access-Control-Allow-Origin': '*',
                                'Access-Control-Allow-Headers': 'Content-Type,X-API-KEY'
                                }
        else:
            return 'Bad Credenciais', 401, {'Access-Control-Allow-Origin': '*'}


@ns.route('/notifications/<int:id>')
@ns.response(404, 'Todo not found')
@ns.param('id', 'The notification identifier')
class Notification(Resource):
    def options(self, id):
        return {'Allow': 'GET, PUT, DELETE'}, 200, \
               {'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, PUT, DELETE',
                'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept, X-API-KEY'
                }

    '''Show a notification'''
    @ns.doc('get_notification')
    @ns.marshal_with(notification_api_model)
    def get(self, id):
        '''Fetch a given resource'''
        if check_user(request):
            item = dao_notification.get_by_id(id)
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

    '''Update a notification'''
    @ns.expect(notification_api_model)
    @ns.marshal_with(notification_api_model)
    def put(self, id):
        '''Update a notification given its identifier'''
        if check_user(request, [ROLE_AUTHENTICATED]):
            item = dao_notification.update(id, request.json)
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


@ns.route('/notifications/<int:id>/file/<string:filename>')
@ns.response(404, 'Todo not found')
@ns.param('filename', 'The notification filename')
class NotificationFile(Resource):
    def options(self, id, filename):
        return {'Allow': 'GET, PUT, DELETE'}, 200, \
               {'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET',
                'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept, X-API-KEY'
                }

    '''Show a notification file'''
    @ns.doc('get_notification_file')
    def get(self, id, filename):
        '''Fetch a given resource'''
        if check_user(request):
            response, code = dao_notification.get_file(id, filename)
            if response:
                if code:
                    return response, code
                else:
                    return response
            else:
                return None, 404, {'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'GET',
                    'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
                    }
        else:
            return None, 401, {'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET',
                'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept'
                }


@ns.route('/notifications/viewers/list')
class NotificationViewersList(Resource):
    def options(self):
        return {'Allow': 'GET, POST, DELETE'}, 200, \
               {'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, DELETE',
                'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept, X-API-KEY'
                }

    def get(self):
        """Returns Notifications Viewers list """
        if (check_user(request, [ROLE_AUTHENTICATED])):
            data = dao_notification.get_viewers_list(request)
            return data, 200, {'Access-Control-Allow-Origin': '*',
                                'Access-Control-Allow-Headers': 'Content-Type,X-API-KEY'
                                }
        else:
            return 'Bad Credenciais', 401, {'Access-Control-Allow-Origin': '*'}