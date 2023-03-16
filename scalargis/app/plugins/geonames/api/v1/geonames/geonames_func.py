import logging
from flask import request
from sqlalchemy import sql

from app.plugins.geonames.models.geonames import *

# ---------------------------------------------------- Get info
def search():

    logger = logging.getLogger(__name__)

    filter = request.args.get('_filter')
    min_similarity = request.args.get('_min_similarity') or 0.5
    max_rows = request.args.get('_max_rows') or 10

    if filter is None:
        return [], 500

    '''
    IN _filter text,
    IN _group text DEFAULT NULL::text,
    IN _admin_level1 text DEFAULT NULL::text,
    IN _admin_level2 text DEFAULT NULL::text,
    IN _admin_level3 text DEFAULT NULL::text,
    IN _maxrows integer DEFAULT 18,
    IN _min_similarity real DEFAULT 0)
    '''
    data = db.session.query(GeonamesSearchResult).from_statement(
        sql.text
            ("select * from  geonames.search_geonames(:filter,:group,:admin_level1,:admin_level2,:admin_level3,:max_rows,:min_similarity)")). \
        params(filter=filter, group=None, admin_level1=None, admin_level2=None, admin_level3=None, max_rows=max_rows, min_similarity=min_similarity).all()

    '''
    result = [
        {"geom_wkt":"MULTIPOINT(-9.1686170000002 38.8258525000002)","designacao":"Loures","origem":"DGT","type":"populatedPlace","grupo":"CONTINENTE","ilha":"","distrito":"LISBOA","concelho":"LOURES","freguesia":"Loures","dicofre":"110707","similarity":1.86079,"search_func":"similarity"}
    ]
    '''
    result = [{"geom_wkt": d.geom_wkt, "name": d.name, "source": d.source, "type": d.type, "group": d.group,
               "admin_level1": d.admin_level1, "admin_level2": d.admin_level2, "admin_level3": d.admin_level3,
               "admin_level4": d.admin_level4, "admin_code": d.admin_code, "similarity": d.similarity,
               "search_func": d.search_func} for d in data]

    return result, 200