import logging

from flask_restx import Api
from app.utils.security import authorizations

log = logging.getLogger(__name__)

api = Api(version='1.0',
          title='ScalarGIS API',
          description='REST API to manage ScalarGIS plataform',
          authorizations=authorizations,
          security='apikey',
          doc='/docs'
          # All API metadata
          )


@api.errorhandler
def default_error_handler(e):
    message = 'An unhandled exception occurred.'
    log.exception(message)

    # if not settings.FLASK_DEBUG:
    if not True:
        return {'message': message}, 500
