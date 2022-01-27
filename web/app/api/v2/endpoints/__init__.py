import logging
from app.api.restx import api2 as api
from app.api.utils.constants import ROLE_PORTAL_ADMIN


logger = logging.getLogger(__name__)


ns_portal = api.namespace('portal', description='Operations related with portal management')
ns_app = api.namespace('app', description='Operations related with client application')
ns_documents = api.namespace('documents', description='Operations related with folders and files')
ns_authentication = api.namespace('authentication', description='Operations related with authentication')
ns_security = api.namespace('security', description='Operations related with security')
ns_stats = api.namespace('stats', description='Operations related with statistics')

api_module_config = {}
api_module_config['APIisOpen'] = True  # for all GET requests
api_module_config['APIisOpenForEditing'] = False  # for all requests
api_module_config['viewRole'] = 'Authenticated'  # need it in portal.roles if not APIisOpen
api_module_config['editRole'] = ROLE_PORTAL_ADMIN  # need it in portal.roles for editing


def register_namespaces():
    api.add_namespace(ns_portal)
    api.add_namespace(ns_app)
    api.add_namespace(ns_authentication)
    api.add_namespace(ns_security)
    api.add_namespace(ns_stats)


def check_user(request, check_roles = None):

    if (api_module_config['APIisOpenForEditing']):
        return True

    if (request.method == 'GET' and api_module_config['APIisOpen']):
        return True

    if 'X-API-KEY' in request.headers:
        token = request.headers['X-API-KEY']
        user = get_user_from_token(token)

        if not user:
            return False

        user_roles = []
        for ru in user.roles:
            user_roles.append(ru.name)
        user_roles.append(constants.ROLE_AUTHENTICATED)

        if (request.method == 'GET' and api_module_config['viewRole'] in user_roles):
            return True

        if check_roles:
            edit_roles = [x.lower() for x in check_roles]
        else:
            edit_roles = api_module_config['editRole'].lower().split(';')

        for ur in user_roles:
            if ur.lower() in edit_roles:
                return True

    return False


def get_user(request):
    if 'X-API-KEY' in request.headers:
        token = request.headers['X-API-KEY']
        user = get_user_from_token(token)
        return user
    else:
        return None


from .portal import *
from .app import *
from .viewer import *
from .print import *
from .documents import *
from .security import *
from .settings import *
from .generic import *
from .stats import *