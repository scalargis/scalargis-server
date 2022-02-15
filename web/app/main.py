import os
import sys
import importlib
import json
import logging.config

from flask import Flask, Blueprint, request, redirect, url_for, render_template
from flask_babel import Babel

from flask_security import Security, SQLAlchemyUserDatastore, forms
from flask_httpauth import HTTPBasicAuth

from flask_mail import Mail

from app import filters

from app.api.v1.endpoints.security import ns as v1_security_ns
from app.api.v2.endpoints import register_namespaces as v2_register_namespaces
from app.api.restx import api
from app.api.restx import api2

from app.models.security import User, Role
from app.models.securityForms import ExtendedLoginForm, ExtendedForgotPasswordForm, \
    ExtendedResetPasswordForm, ExtendedConfirmRegisterForm
from app.utils import security as app_security

from app import database
from app.database import db

base_path = os.path.join(os.path.dirname(os.path.abspath(__file__)))
instance_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'instance')
app = Flask(__name__, instance_path=instance_path, instance_relative_config=True)


def setup_logging(
        default_path=os.path.join(instance_path + os.sep + 'logging.json'),
        default_level=logging.INFO,
        env_key='LOG_CFG'
):
    """Setup logging configuration

    """
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


def setup_security(flask_app):
    # Setup Flask-Security
    user_datastore = SQLAlchemyUserDatastore(db, User, Role)
    security = Security(flask_app, user_datastore, login_form=ExtendedLoginForm,
                        forgot_password_form=ExtendedForgotPasswordForm,
                        reset_password_form=ExtendedResetPasswordForm,
                        confirm_register_form=ExtendedConfirmRegisterForm)
    database.user_datastore = user_datastore

    # Setup email security
    app_security.init_email(flask_app, security)

    # Setup a LDAP3 Login Manager.
    app_security.init_ldap(flask_app)

    # -- HTTPAUTH Setup --#
    auth = HTTPBasicAuth()
    # -- END HTTPAUTH Setup --#


def setup_mail(flask_app):
    mail = Mail()

    mail.init_app(flask_app)


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


def initialize_api(flask_app):
    # -- Restx -- #
    blueprint = Blueprint('api', __name__, url_prefix='/api/v1')
    api.init_app(blueprint)
    api.add_namespace(v1_security_ns)
    flask_app.register_blueprint(blueprint)

    blueprint2 = Blueprint('api2', __name__, url_prefix='/api/v2')
    api2.init_app(blueprint2)
    v2_register_namespaces()
    flask_app.register_blueprint(blueprint2)

    # -- Graphql -- #
    from app.api.graphql import bp_graph
    flask_app.register_blueprint(bp_graph)


def initialize_app(flask_app):
    configure_app(flask_app)

    babel = Babel(flask_app)

    db.init_app(flask_app)

    setup_security(flask_app)

    setup_mail(flask_app)

    flask_app.register_blueprint(filters.mod)

    initialize_api(flask_app)

    # -- Load Modules --#
    from app.modules.backoffice import mod as backoffice_bp
    from app.modules.map import mod as map_bp
    from app.modules.file.controllers import mod as file_bp
    from app.modules.profile.controllers import mod as profile_bp
    from app.modules.search.controllers import mod as search_bp
    from app.modules.print.controllers import mod as print_bp
    from app.modules.catalog.controllers import mod as catalog_bp
    from app.modules.ows.controllers import mod as ows_bp

    # -- Register blueprint(s) --#
    flask_app.register_blueprint(backoffice_bp)
    flask_app.register_blueprint(map_bp)
    flask_app.register_blueprint(file_bp)
    flask_app.register_blueprint(profile_bp)
    flask_app.register_blueprint(search_bp)
    flask_app.register_blueprint(print_bp)
    flask_app.register_blueprint(catalog_bp)
    flask_app.register_blueprint(ows_bp)


def load_plugins():
    """
        This code looks for any modules or packages in the given directory, loads them
        and then registers a blueprint - blueprints must be created with the name 'module'
        Implemented directory scan
    """
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'plugins')
    if (os.path.basename(os.path.dirname(os.path.abspath(__file__)))).lower() == 'web':
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app', 'plugins')

    dir_list = os.listdir(path)

    mods = {}

    if 'PLUGINS' in app.config.keys():
        plugins = app.config['PLUGINS']
        dir_list.clear()
        for plugin in plugins:
            dir_list.append(plugin)

    for fname in dir_list:
        if os.path.isdir(os.path.join(path, fname)) and os.path.exists(os.path.join(path, fname, '__init__.py')):
            mods[fname] = importlib.import_module('.' + fname, 'app.plugins')
            if hasattr(mods[fname], 'module_api'):
                module = getattr(mods[fname], 'module_api')
                app.register_blueprint(module)
            if hasattr(mods[fname], 'module'):
                module = getattr(mods[fname], 'module')
                app.register_blueprint(module)
        elif os.path.isfile(os.path.join(path, fname)):
            name, ext = os.path.splitext(fname)
            if ext == '.py' and not name == '__init__':
                mods[name] = importlib.import_module('.' + name, 'app.plugins2')
                module = getattr(mods[name], 'module')
                app.register_blueprint(module)


def main(argv):
    if os.path.basename(os.getcwd()).lower() == 'app':
        os.chdir(os.path.join(os.getcwd(), '../'))

    setup_logging()
    initialize_app(app)
    load_plugins()

    reloader = '--reloader' in argv
    threaded = '--threaded' in argv

    app.run(host="0.0.0.0", use_reloader=reloader, threaded=threaded)


def init_wsgi():
    setup_logging()
    initialize_app(app)
    load_plugins()


@app.route("/")
def home():
    if 'DEFAULT_APP_PAGE' in app.config and app.config['DEFAULT_APP_PAGE']:
        action = app.config['DEFAULT_APP_PAGE'].lower()

        if '.' in action:
            return redirect(url_for(action), 302)
        elif '/' in action:
            return redirect(action, 302)
        elif action == 'home':
            return redirect(url_for('map.home'), 302)
        else:
            return redirect(url_for('map.index'), 302)
    else:
        return redirect(url_for('map.index'), 302)


@app.route("/check_path")
def check_path():
    return '<div>' + base_path + '</div><div>' + os.path.abspath(__file__) + '</div>'


@app.route("/setup", methods=['GET', 'POST'])
def setup():
    from sqlalchemy import MetaData

    try:
        metadata_obj = MetaData(schema="portal")
        metadata_obj.reflect(bind=db.engine)

        if metadata_obj.tables is not None and len(metadata_obj.tables) > 0:
            msg = '<div class="alert alert-warning" role="alert">' \
                  '<p>A <i>"portal"</i> schema already exists in the database, the configuration may have already ' \
                  'been executed.</p><p>Delete the <i>"portal"</i> schema if you want to have a new configuration, ' \
                  'then run setup again.</p>' \
                  '</div>'

            return render_template('setup/setup.html', db_exists=True, message=msg)
    except Exception as e:
        msg = '<div class="alert alert-alert-danger" role="alert">' + str(e) + '</div>'
        return render_template('setup/setup.html', message=msg)

    if request.method == 'POST':
        try:
            from app.database.schema import setup

            load_sample_data = 'load_sample_data' in request.form and request.form['load_sample_data']

            setup(load_sample_data)

            msg = '<div class="alert alert-success" role="alert">' \
                  '<div>The database has been successfully configured!</div>' \
                  '</div>'
            return render_template('setup/setup.html', success=True, message=msg)
        except Exception as e:
            msg = '<div class="alert alert-alert-danger" role="alert">' + str(e) + '</div>'
            return render_template('setup/setup.html', message=msg)
    else:
        msg = '<p>Click the <i>Setup</i> button to create the ScalarGIS schema in the database.</p>' \
              '<p>The schema will be created with the name <i>"portal"</i>.</p>'

        return render_template('setup/setup.html', message=msg)


@app.cli.command()
def init_db():
    configure_app(app)

    db.init_app(app)
    setup_security(app)

    from app.database.schema import create_schema
    create_schema(True)

    print('Successful Database Initialization!')


@app.cli.command()
def load_sample_data():
    configure_app(app)

    db.init_app(app)
    setup_security(app)

    from app.database.schema import load_sample_data
    load_sample_data(True)

    print('Sample data successfully loaded!')


if __name__ == "__main__":
    main(sys.argv)
