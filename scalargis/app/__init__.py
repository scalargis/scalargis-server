import os
import json
import logging.config

from flask import Flask
from flask_mail import Mail

__version__ = '0.1.0'

base_path = os.path.join(os.path.dirname(os.path.abspath(__file__)))
instance_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'instance')
app = Flask(__name__, instance_path=instance_path, instance_relative_config=True)


def get_db_schema():
    db_schema = app.config.get('SCALARGIS_DB_SCHEMA') or 'scalargis'
    return db_schema


def setup_logging(
        default_path=os.path.join(instance_path + os.sep + 'logging.json'),
        default_level=logging.INFO,
        env_key='LOG_CFG'
):
    """Setup logging configuration

    """

    if os.path.basename(os.getcwd()).lower() == 'app':
        os.chdir(os.path.join(os.getcwd(), '../'))

    path = default_path
    value = os.getenv(env_key, None)
    log_config = 'Not defined'
    if value:
        path = value
        log_config = value
    if os.path.exists(path):
        log_config = path
        with open(path, 'rt') as f:
            config = json.load(f)
        logging.config.dictConfig(config)
    else:
        logging.basicConfig(level=default_level)
        log_config = 'basicConfig'

    log = logging.getLogger(__name__)
    log.info('Setup logging: {}'.format(log_config))


def configure_app(flask_app):
    # Load the default configuration
    flask_app.config.from_object('instance.default')

    # Load the configuration from the instance folder
    flask_app.config.from_pyfile('config.py', silent=True)

    # Load the file specified by the APP_CONFIG_FILE environment variable
    if os.environ.get('APP_CONFIG_FILE') and os.path.exists(os.environ.get('APP_CONFIG_FILE')):
        flask_app.config.from_envvar('APP_CONFIG_FILE', silent=True)
    elif os.environ.get('APP_CONFIG_FILE') and os.path.exists(
            os.path.join(instance_path, os.environ.get('APP_CONFIG_FILE'))):
        flask_app.config.from_pyfile(os.path.join(instance_path, os.environ.get('APP_CONFIG_FILE')), silent=True)

    # Load backoffice configuration
    flask_app.config.from_pyfile('config_backoffice.py')


def setup_security(flask_app):
    """Setup Flask-Security and LDAP3 Login Manager

    """
    from app import database
    from flask_security import Security, SQLAlchemyUserDatastore

    from app.models.security import User, Role
    from app.database import db
    from app.utils import security as app_security

    # Setup Flask-Security
    user_datastore = SQLAlchemyUserDatastore(db, User, Role)
    security = Security(flask_app, user_datastore)
    database.user_datastore = user_datastore

    # Setup a LDAP3 Login Manager.
    app_security.init_ldap(flask_app)


def setup_mail(flask_app):
    """Setup Flask-Mail

    """
    mail = Mail()

    mail.init_app(flask_app)


setup_logging()
configure_app(app)
