import logging
from app.utils import constants
from app.utils.security import get_api_user
from app.plugins.spatial_toolbox.api.restx import api as api_spatial_toolbox

logger = logging.getLogger(__name__)

#ns = api_spatial_toolbox.namespace('spatial_toolbox', description='Plugin Spatial Toolbox', path='/v1')
ns = api_spatial_toolbox.namespace('spatial_toolbox', description='Plugin Spatial Toolbox', path='/')

api_module_config = {}
api_module_config['APIisOpen'] = True  # for all GET requests
api_module_config['viewRole'] = 'anonymous;authenticated'


def check_user(request):
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

    return False


from .data import *
from .analysis import *
