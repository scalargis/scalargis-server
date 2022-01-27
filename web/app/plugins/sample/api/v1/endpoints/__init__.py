import logging
from app.utils import constants
from app.utils.security import get_user_from_token, get_api_user
from app.plugins.sample.api.restx import api as api_sample
from app.plugins.sample.utils.constants import ROLE_SAMPLE_VIEW, ROLE_SAMPLE_EDIT

logger = logging.getLogger(__name__)

ns = api_sample.namespace('sample', description='Plugin Sample', path='/v1')

api_module_config = {}
api_module_config['APIisOpen'] = False  # for all GET requests
api_module_config['APIisOpenForEditing'] = False  # for all requests
api_module_config['viewRole'] = ROLE_SAMPLE_VIEW  # need it in portal.roles if not APIisOpen
api_module_config['editRole'] = ROLE_SAMPLE_EDIT  # need it in portal.roles for editing


def check_user(request):

    if (api_module_config['APIisOpenForEditing']):
        return True

    if (request.method == 'GET' and api_module_config['APIisOpen']):
        return True

    user = get_api_user(request)

    if not user:
        return False

    user_roles = []
    for ru in user.roles:
        user_roles.append(ru.name)
    user_roles.append(constants.ROLE_AUTHENTICATED)

    if request.method == 'GET':
        view_roles = api_module_config['viewRole'].lower().split(';')
        for ur in user_roles:
            if ur.lower() in view_roles:
                return True

    edit_roles = api_module_config['editRole'].lower().split(';')
    for ur in user_roles:
        if ur.lower() in edit_roles:
            return True

    return False

    '''
    if 'X-API-KEY' in request.headers:
        token = request.headers['X-API-KEY']
        user = get_user_from_token(token)

        if not user:
            return False

        user_roles = []
        for ru in user.roles:
            user_roles.append(ru.name)
        user_roles.append(constants.ROLE_AUTHENTICATED)

        if request.method == 'GET':
            view_roles = api_module_config['viewRole'].lower().split(';')
            for ur in user_roles:
                if ur.lower() in view_roles:
                    return True

        edit_roles = api_module_config['editRole'].lower().split(';')
        for ur in user_roles:
            if ur.lower() in edit_roles:
                return True

    return False
    '''


from .data import *