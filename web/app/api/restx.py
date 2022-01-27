import logging
import traceback

from flask_restx import Api
from sqlalchemy.orm.exc import NoResultFound
from app.utils.security import authorizations

log = logging.getLogger(__name__)

api = Api(version='1.0',
          title='Arade API',
          description='REST API to manage Arade plataform',
          authorizations=authorizations,
          security='apikey'
          # All API metadatas
          # All API metadatas
          )

api2 = Api(version='2.0',
          title='Arade API',
          description='REST API to manage Arade plataform',
          authorizations=authorizations,
          security='apikey'
          # All API metadatas
          # All API metadatas
          )

@api.errorhandler
def default_error_handler(e):
    message = 'An unhandled exception occurred.'
    log.exception(message)

    # if not settings.FLASK_DEBUG:
    if not True:
        return {'message': message}, 500


@api.errorhandler(NoResultFound)
def database_not_found_error_handler(e):
    log.warning(traceback.format_exc())
    return {'message': 'A database result was required but none was found.'}, 404