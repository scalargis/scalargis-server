import os
import json
import logging.config
import os.path
import importlib

from flask import Flask


instance_path=os.path.join(os.path.dirname(os.path.abspath(__file__)) + os.sep + '..' + os.sep + 'instance')
app = Flask(__name__, instance_path=instance_path, instance_relative_config=True)


def setup_logging(
    default_path=os.path.join(instance_path + os.sep + 'logging_spatial_toolbox.json'),
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

    if 'SCALARGIS_PLUGINS' in app.config.keys():
        plugins = app.config['PLUGINS']

    if 'SCALARGIS_PLUGINS_SPATIAL_TOOLBOX' in app.config.keys():
        plugins = app.config['SCALARGIS_PLUGINS_SPATIAL_TOOLBOX']

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
            name, ext = os.path.splitext(fname)
            if ext == '.py' and not name == '__init__':
                mods[name] = importlib.import_module('.' + name, 'app.plugins2')
                module = getattr(mods[name], 'module')
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
    setup_logging()
    configure_app(app)
    load_plugins()


def load_app():
    setup_logging()
    configure_app(app)
    load_plugins()

    app.run(host="0.0.0.0", debug=True, use_reloader=True, threaded=True)


if __name__ == "__main__":
    load_app()