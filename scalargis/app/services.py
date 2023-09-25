import os
import os.path
import importlib

from app import app, setup_security, setup_mail
from app.database import db


service_name = os.environ.get('SERVICE_NAME') or 'services'


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

    plugins = None

    plugin_service_name = 'SCALARGIS_PLUGINS_{0}'.format(service_name).upper()

    if 'SCALARGIS_PLUGINS' in app.config.keys():
        plugins = app.config['SCALARGIS_PLUGINS']

    if plugin_service_name in app.config.keys():
        plugins = app.config[plugin_service_name]

    if plugins:
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
            '''
            Deprecated: will be removed in next main version, use folder plugin instead
            '''
            name, ext = os.path.splitext(fname)
            if ext == '.py' and not name == '__init__':
                mods[name] = importlib.import_module('.' + name, 'app.plugins2')
                module = getattr(mods[name], 'module')
                app.register_blueprint(module)


def load_extensions():
    """
        This code looks for any modules or packages in the given directory, loads them
        and then registers a blueprint - blueprints must be created with the name 'module'
        Implemented directory scan
    """
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'extensions')
    if (os.path.basename(os.path.dirname(os.path.abspath(__file__)))).lower() == 'scalargis':
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app', 'extensions')

    dir_list = os.listdir(path)

    mods = {}

    extensions = None

    extension_service_name = 'SCALARGIS_EXTENSIONS_{0}'.format(service_name).upper()

    if 'SCALARGIS_EXTENSIONS' in app.config.keys():
        extensions = app.config['SCALARGIS_EXTENSIONS']

    if extension_service_name in app.config.keys():
        extensions = app.config[extension_service_name]

    if extensions:
        dir_list.clear()
        for extension in extensions:
            dir_list.append(extension)

    for fname in dir_list:
        if os.path.isdir(os.path.join(path, fname)) and os.path.exists(os.path.join(path, fname, '__init__.py')):
            mods[fname] = importlib.import_module('.' + fname, 'app.extensions')
            if hasattr(mods[fname], 'module_api'):
                module = getattr(mods[fname], 'module_api')
                app.register_blueprint(module)
            if hasattr(mods[fname], 'module'):
                module = getattr(mods[fname], 'module')
                app.register_blueprint(module)


def configure_app(flask_app):
    # Load the default configuration
    flask_app.config.from_object('instance.default')

    # Load the configuration from the instance folder
    flask_app.config.from_pyfile('config.py', silent=True)

    # Load the file specified by the APP_CONFIG_FILE environment variable
    if os.environ.get('APP_CONFIG_FILE') and os.path.exists(os.environ.get('APP_CONFIG_FILE')):
        flask_app.config.from_envvar('APP_CONFIG_FILE', silent=True)


def init_wsgi():
    db.init_app(app)

    setup_security(app)

    setup_mail(app)

    load_plugins()

    load_extensions()


def run(argv):
    if os.path.basename(os.getcwd()).lower() == 'app':
        os.chdir(os.path.join(os.getcwd(), '../'))

    db.init_app(app)

    setup_security(app)

    setup_mail(app)

    load_plugins()

    load_extensions()

    reloader = '--reloader' in argv
    threaded = '--threaded' in argv

    port = int(os.environ.get('PORT')) if os.environ.get('PORT') else 5000

    app.run(host="0.0.0.0", port=port, use_reloader=reloader, threaded=threaded)
