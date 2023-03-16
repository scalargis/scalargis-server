import os
import json
import logging.config

from flask import Flask, Blueprint, current_app, send_file, request, jsonify, render_template, url_for, Response
from flask_security import current_user
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import sql, text
from app.utils import http

instance_path=os.path.join(os.path.dirname(os.path.abspath(__file__)) + os.sep + '..' + os.sep + 'instance')
app = Flask(__name__, instance_path=instance_path, instance_relative_config=True)

db = SQLAlchemy()

db.init_app(app)

class SearchResult(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    designacao = db.Column(db.Text())
    origem = db.Column(db.Text())
    type = db.Column(db.Text())
    grupo = db.Column(db.Text())
    ilha = db.Column(db.Text())
    distrito = db.Column(db.Text())
    concelho = db.Column(db.Text())
    freguesia = db.Column(db.Text())
    dicofre = db.Column(db.Text())
    geom_wkt = db.Column(db.Text())
    similarity = db.Column(db.Float())
    search_func = db.Column(db.Text())

def setup_logging(
    default_path=os.path.join(instance_path + os.sep + 'logging_geographical_names.json'),
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


def load_app():
    setup_logging()
    configure_app(app)

    app.run(host="0.0.0.0", debug=True, use_reloader=True, threaded=True)


@app.route('/index', methods=['GET'])
def index():
    logger = logging.getLogger(__name__)
    logger.debug('Spatial Toolbox')

    return 'geographical_names'


@app.route('/search', methods=['GET', 'OPTIONS'])
@http.crossdomain(origin='*', methods=['GET', 'OPTIONS'], headers='Origin, Content-Type, X-API-KEY')
def search():
    logger = logging.getLogger(__name__)

    filter = request.args.get('_filter')
    min_similarity = 0.5 #request.args.get('_min_similarity')
    max_rows = 10 #request.args.get('_min_similarity')

    '''
    IN _filter text,
    IN _grupo text DEFAULT NULL::text,
    IN _ilha text DEFAULT NULL::text,
    IN _distrito text DEFAULT NULL::text,
    IN _concelho text DEFAULT NULL::text,
    IN _maxrows integer DEFAULT 18,
    IN _min_similarity real DEFAULT 0)
    '''
    data = db.session.query(SearchResult).from_statement(
        sql.text("select * from  geographical_names.search_geoname(:filter,:grupo,:ilha,:distrito,:concelho,:max_rows,:min_similarity)")). \
        params(filter=filter, grupo=None, ilha=None, distrito=None, concelho=None, max_rows=max_rows, min_similarity=min_similarity).all()

    '''
    result = [
        {"geom_wkt":"MULTIPOINT(-9.1686170000002 38.8258525000002)","designacao":"Loures","origem":"DGT","type":"populatedPlace","grupo":"CONTINENTE","ilha":"","distrito":"LISBOA","concelho":"LOURES","freguesia":"Loures","dicofre":"110707","similarity":1.86079,"search_func":"similarity"}
    ]
    '''
    result = [{"geom_wkt": d.geom_wkt, "designacao": d.designacao, "origem": d.origem, "type": d.type, "grupo": d.grupo,
               "ilha": d.ilha, "distrito": d.distrito, "concelho": d.concelho, "freguesia": d.freguesia,
               "dicofre": d.dicofre, "similarity": d.similarity, "search_func": d.search_func} for d in data]

    return Response(json.dumps(result), mimetype='application/json')


if __name__ == "__main__":
    load_app()
