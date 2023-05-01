import os
import importlib
import logging.config

from flask import Blueprint, redirect, url_for

from app import app, base_path, configure_app, setup_logging, setup_security, setup_mail
from app.database import db

from app import filters
from app.api.v1.endpoints import register_namespaces as api_register_namespaces
from app.api.restx import api


def initialize_api(flask_app):
    # -- Restx -- #
    blueprint = Blueprint('api', __name__, url_prefix='/api')
    api.init_app(blueprint)
    api_register_namespaces()
    flask_app.register_blueprint(blueprint)


def initialize_app(flask_app):
    db.init_app(flask_app)

    setup_security(flask_app)
    setup_mail(flask_app)

    flask_app.register_blueprint(filters.mod)

    initialize_api(flask_app)

    # -- Load Modules --#
    from app.modules.backoffice import mod as backoffice_bp
    from app.modules.map import mod as map_bp
    from app.modules.file.controllers import mod as file_bp

    # -- Register blueprint(s) --#
    flask_app.register_blueprint(backoffice_bp)
    flask_app.register_blueprint(map_bp)
    flask_app.register_blueprint(file_bp)

    from app.database.schema import create_schema

    # -- Create database schema
    with app.app_context():
        log = logging.getLogger(__name__)
        try:
            created = create_schema()
            if created:
                log.info('Database schema created!')
        except Exception as e:
            log.error('Database Initialization error: {}'.format(str(e)))


def load_plugins():
    """
        This code looks for any modules or packages in the given directory, loads them
        and then registers a blueprint - blueprints must be created with the name 'module'
        Implemented directory scan
    """
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'plugins')
    if (os.path.basename(os.path.dirname(os.path.abspath(__file__)))).lower() == 'scalargis':
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app', 'plugins')

    dir_list = os.listdir(path)

    mods = {}

    if 'SCALARGIS_PLUGINS' in app.config.keys():
        plugins = app.config['SCALARGIS_PLUGINS']
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


def run(argv):
    if os.path.basename(os.getcwd()).lower() == 'app':
        os.chdir(os.path.join(os.getcwd(), '../'))

    initialize_app(app)
    load_plugins()

    reloader = '--reloader' in argv
    threaded = '--threaded' in argv

    port = int(os.environ.get('PORT')) if os.environ.get('PORT') else 5000

    app.run(host="0.0.0.0", port=port, use_reloader=reloader, threaded=threaded)


def init_wsgi():
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


@app.cli.command()
def init_db():
    db.init_app(app)
    setup_security(app)

    from app.database.schema import create_schema
    create_schema()

    print('Successful Database Initialization!')


@app.cli.command()
def load_sample_data():
    configure_app(app)

    db.init_app(app)
    setup_security(app)

    from app.database.schema import load_sample_data
    load_sample_data()

    print('Sample data successfully loaded!')
