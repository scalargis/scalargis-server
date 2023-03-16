import logging
import json
from flask import Blueprint, request, Response
from sqlalchemy import sql

from app.utils import http
from app.database import db

from .api.v1.endpoints import ns as v1_geonames_ns
from .api.restx import api
from .models.geonames import GeonamesSearchResultLegacy


''' Legacy service '''
module = Blueprint('geographical_names', __name__, template_folder='templates', static_folder='',
                   static_url_path='', url_prefix='/geographical_names')

module_api = Blueprint('geonames_api', __name__, template_folder='templates', static_folder='',
                   static_url_path='', url_prefix='/geonames/api')

module_code = 'geonames'

api.init_app(module_api)
api.add_namespace(v1_geonames_ns)


@module.route('/index', methods=['GET'])
def index():
    logger = logging.getLogger(__name__)
    logger.debug('Geographical Names')

    return module_code


''' Legacy route '''
@module.route('/search', methods=['GET', 'OPTIONS'])
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
    data = db.session.query(GeonamesSearchResultLegacy).from_statement(
        sql.text("select * from  geographical_names.search_geoname(:filter,:grupo,:ilha,:distrito,:concelho,:max_rows,:min_similarity)")). \
        params(filter=filter, grupo=None, ilha=None, distrito=None, concelho=None, max_rows=max_rows, min_similarity=min_similarity).all()

    '''
    result = [
        {"geom_wkt":"MULTIPOINT(-9.1686170000002 38.8258525000002)","designacao":"Loures","origem":"DGT",
        "type":"populatedPlace","grupo":"CONTINENTE","ilha":"","distrito":"LISBOA","concelho":"LOURES",
        "freguesia":"Loures","dicofre":"110707","similarity":1.86079,"search_func":"similarity"}
    ]
    '''
    result = [{"geom_wkt": d.geom_wkt, "designacao": d.designacao, "origem": d.origem, "type": d.type, "grupo": d.grupo,
               "ilha": d.ilha, "distrito": d.distrito, "concelho": d.concelho, "freguesia": d.freguesia,
               "dicofre": d.dicofre, "similarity": d.similarity, "search_func": d.search_func} for d in data]

    return Response(json.dumps(result), mimetype='application/json')