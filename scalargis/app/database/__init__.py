import logging
import sys

from flask_sqlalchemy import SQLAlchemy

log = logging.getLogger(__name__)

try:
    db = SQLAlchemy()
except SQLAlchemy.ConnectionError:
    log.error('Database connection error. Please check database...')
    sys.exit(1)
except SQLAlchemy.PermissionError:
    log.error('Database permission error. Please grant user credentials...')
    sys.exit(1)
except Exception as e:
    log.error("Generic exception: {}".format(e))
    sys.exit(1)
