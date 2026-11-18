import json
import logging
import re

import sqlalchemy
from flask import request
from flask_restx import abort
from sqlalchemy import cast, or_
from sqlalchemy.exc import IntegrityError

from app.database import db
from app.models.portal import SharedLayer, Viewer
from app.utils import utc_now, iso_utc
from ..parsers import parser_records_with_page
from ...endpoints import get_user
from . import history


logger = logging.getLogger(__name__)

ENTITY = 'shared_layer'

CODE_PATTERN = re.compile(r'^[a-z0-9-]+$')

SORT_FIELDS = ('id', 'code', 'title', 'updated_at')


def _layer(value):
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except ValueError:
            abort(400, 'layer_json is not valid JSON', error='invalid_layer')
    if not isinstance(value, dict):
        abort(400, 'layer_json must be an object', error='invalid_layer')
    layer_type = value.get('type')
    if not isinstance(layer_type, str) or not layer_type.strip():
        abort(400, 'layer_json must have a type', error='invalid_layer')
    if 'id' in value:
        abort(400, 'layer_json must not have an id', error='invalid_layer')
    if layer_type.strip().upper() == 'GROUP':
        abort(400, 'A shared layer cannot be a GROUP', error='group_layer')
    return value


def _code(value):
    if not isinstance(value, str) or not CODE_PATTERN.match(value):
        abort(400, 'code must match ^[a-z0-9-]+$', error='invalid_code')
    return value


def _code_free(code, record_id=None):
    qy = SharedLayer.query.filter(SharedLayer.code == code)
    if record_id is not None:
        qy = qy.filter(SharedLayer.id != record_id)
    if qy.first() is not None:
        abort(409, 'A shared layer with this code exists', error='duplicate_code')


def _loads(text):
    try:
        return json.loads(text) if text else None
    except ValueError:
        return None


def _pointer_codes(config_text):
    config = _loads(config_text)
    layers = config.get('layers') if isinstance(config, dict) else None
    if not isinstance(layers, list):
        return set()
    return {lyr['shared'] for lyr in layers
            if isinstance(lyr, dict) and isinstance(lyr.get('shared'), str) and lyr['shared']}


def _viewers_with_pointers():
    return db.session.query(Viewer.id, Viewer.name, Viewer.title, Viewer.config_json) \
        .filter(Viewer.config_json.contains('"shared"')).order_by(Viewer.id).all()


def usage(code):
    """Returns the viewers whose config_json.layers hold a layer with shared equal to code."""
    return [{'id': v.id, 'name': v.name, 'title': v.title}
            for v in _viewers_with_pointers() if code in _pointer_codes(v.config_json)]


def usage_counts():
    """Returns a map of each code to the number of viewers that name it."""
    counts = {}
    for v in _viewers_with_pointers():
        for code in _pointer_codes(v.config_json):
            counts[code] = counts.get(code, 0) + 1
    return counts


def _type_of(record):
    layer = _loads(record.layer_json)
    return layer.get('type') if isinstance(layer, dict) else None


def to_dict(record, with_layer=True):
    """Returns the API form of a library row."""
    data = {'id': record.id, 'code': record.code, 'title': record.title, 'type': _type_of(record),
            'updated_at': iso_utc(record.updated_at)}
    if with_layer:
        data['layer_json'] = _loads(record.layer_json)
    return data


def get_by_filter(req):
    """Returns a page of library rows with the type and the usage count of each row."""
    args = parser_records_with_page.parse_args(req)
    page = args.get('page') or 1
    per_page = args.get('per_page') or 10
    try:
        filters = json.loads(args.get('filter') or '{}')
        sort = json.loads(args.get('sort') or '[]')
    except ValueError:
        abort(400, 'filter and sort must be JSON', error='invalid_filter')

    qy = SharedLayer.query
    for key, value in (filters.items() if isinstance(filters, dict) else []):
        if key == 'id':
            ids = value if isinstance(value, list) else [value]
            qy = qy.filter(SharedLayer.id.in_([int(i) for i in ids]))
        elif key in ('code', 'title'):
            qy = qy.filter(cast(getattr(SharedLayer, key), sqlalchemy.String).ilike('%' + str(value) + '%'))
        elif key == 'q':
            text = '%' + str(value) + '%'
            qy = qy.filter(or_(SharedLayer.code.ilike(text), SharedLayer.title.ilike(text)))

    ordered = False
    if isinstance(sort, list):
        for i in range(0, len(sort) - 1, 2):
            if sort[i] in SORT_FIELDS and str(sort[i + 1]).lower() in ('asc', 'desc'):
                qy = qy.order_by(getattr(getattr(SharedLayer, sort[i]), str(sort[i + 1]).lower())())
                ordered = True
    if not ordered:
        qy = qy.order_by(SharedLayer.code.asc())

    result = qy.paginate(page=page, per_page=per_page, error_out=False)
    counts = usage_counts()
    items = []
    for record in result.items:
        item = to_dict(record, with_layer=False)
        item['usage_count'] = counts.get(record.code, 0)
        items.append(item)
    return {'page': result.page, 'pages': result.pages, 'per_page': result.per_page, 'total': result.total,
            'items': items}


def get_by_id(record_id):
    return SharedLayer.query.filter(SharedLayer.id == record_id).one_or_none()


def _commit():
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        abort(409, 'A shared layer with this code exists', error='duplicate_code')


def create(data):
    """Creates a library row after the code and layer checks."""
    if not isinstance(data, dict):
        abort(400, 'The body must be an object')
    user = get_user(request)
    code = _code(data.get('code'))
    layer = _layer(data.get('layer_json'))
    _code_free(code)
    record = SharedLayer(code=code, title=data.get('title') or layer.get('title'),
                         layer_json=json.dumps(layer, ensure_ascii=False),
                         id_user_create=user.id if user else None, created_at=utc_now())
    db.session.add(record)
    _commit()
    db.session.refresh(record)
    return record


def update(record_id, data):
    """Updates a library row and keeps a history row of the state before. None when the row does not exist."""
    if not isinstance(data, dict):
        abort(400, 'The body must be an object')
    record = get_by_id(record_id)
    if record is None:
        return None
    user = get_user(request)
    history.check_stale(record, data)
    before = history.snapshot(ENTITY, record)

    if 'code' in data:
        code = _code(data.get('code'))
        if code != record.code:
            _code_free(code, record.id)
            used = usage(record.code)
            if used:
                abort(409, 'The code is in use by viewers', error='in_use', viewers=used)
            record.code = code
    if 'layer_json' in data:
        record.layer_json = json.dumps(_layer(data.get('layer_json')), ensure_ascii=False)
    if 'title' in data:
        record.title = data.get('title') or None

    record.id_user_update = user.id if user else None
    record.updated_at = utc_now()
    history.keep(ENTITY, record, before, history.ORIGIN_BACKOFFICE, user)
    _commit()
    db.session.refresh(record)
    return record


def delete(record_id):
    """Deletes a library row and its history rows. Aborts with 409 when a viewer names it."""
    record = get_by_id(record_id)
    if record is None:
        return False
    used = usage(record.code)
    if used:
        abort(409, 'The shared layer is in use by viewers', error='in_use', viewers=used)
    history.forget(ENTITY, [record.id])
    db.session.delete(record)
    db.session.commit()
    return True
