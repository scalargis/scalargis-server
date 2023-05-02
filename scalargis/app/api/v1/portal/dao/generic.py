import json
from datetime import datetime

from flask import request
import sqlalchemy
from sqlalchemy import Integer, cast, inspect, or_
from sqlalchemy.exc import IntegrityError

from app.database import db
from ..parsers import *
from app.models.portal import CoordinateSystems
from app.api.v1.endpoints import get_user


generic_models = {
    "coordinatesystems": CoordinateSystems,
    "coordinate_systems": CoordinateSystems,
    }

generic_fields = [
    "code",
    "name",
    "description",
    "config_json"
]


def get_generic(entity_name, request):
    """
    Returns list of domain
    """
    args = parser_records_with_page.parse_args(request)
    page = args.get('page', 1)
    per_page = args.get('per_page', 10)
    filter = json.loads(args.get('filter') or '{}')

    model = generic_models[entity_name.lower()]

    qy = model.query

    if filter:
        for key in filter:
            field = getattr(model, key)
            if isinstance(filter[key], list):
                values = filter[key]
                conditions = []
                for val in values:
                    if isinstance(field.property.columns[0].type, Integer):
                        conditions.append(field == val)
                    else:
                        conditions.append(cast(field, sqlalchemy.String).ilike('%' + str(val) + '%'))
                qy = qy.filter(or_(*conditions))
            else:
                qy = qy.filter(cast(field, sqlalchemy.String).ilike('%' + str(filter[key]) + '%'))

    sort = json.loads(args.get('sort') or '[]')
    if len(sort) > 0 and sort[0] is not None:
        for i in range(0, len(sort), 2):
            if isinstance(sort[i], list):
                for j in range(0, len(sort[i])):
                    order = getattr(getattr(model, sort[i][j]), sort[i+1][j].lower())()
                    qy = qy.order_by(order)
            else:
                order = getattr(getattr(model, sort[i]), sort[i+1].lower())()
                qy = qy.order_by(order)

    records_page = qy.paginate(page=page, per_page=per_page, error_out=False)

    return records_page


def get_generic_by_id(entity_name, id):
    model = generic_models[entity_name.lower()]

    qy = model.query.filter(model.id == id)
    return qy.one()


def create_generic(entity_name, data):
    user = get_user(request)

    model = generic_models[entity_name.lower()]

    record = model()

    record.code = data['code'] if 'code' in data else None
    record.name = data['name'] if 'name' in data else None
    record.description = data['description'] if 'description' in data else None
    record.config_json = json.dumps(data['config_json']) if 'config_json' in data  else None

    # Update custom model fields
    mapper = inspect(model)
    for column in mapper.attrs:
        if column.key not in generic_fields:
            if column.key in data:
                setattr(record, column.key, data[column.key])

    record.created_at = datetime.now()
    if user and user.id:
        record.id_user_create = user.id

    db.session.add(record)
    db.session.commit()
    db.session.refresh(record)
    return record


def update_generic(entity_name, id, data):
    user = get_user(request)

    model = generic_models[entity_name.lower()]

    record = db.session.query(model).filter(model.id == id).one()

    record.code = data['code'] if 'code' in data else None
    record.name = data['name'] if 'name' in data else None
    record.description = data['description'] if 'description' in data else None
    record.config_json = json.dumps(data['config_json']) if 'config_json' in data else None

    # Update custom model fields
    mapper = inspect(model)
    for column in mapper.attrs:
        if column.key not in generic_fields:
            if column.key in data:
                setattr(record, column.key, data[column.key])

    record.updated_at = datetime.now()
    if user and user.id:
        record.id_user_update = user.id
    else:
        record.id_user_update = None

    db.session.add(record)
    db.session.commit()
    db.session.refresh(record)
    return record


def delete_generic(entity_name, id):
    user = get_user(request)

    model = generic_models[entity_name.lower()]

    record = db.session.query(model).filter(model.id == id).one()
    db.session.delete(record)
    try:
        db.session.commit()
        return 204
    except IntegrityError:
        return 500
    except:
        return 555


def delete_generic_list(entity_name, data):
    user = get_user(request)

    model = generic_models[entity_name.lower()]

    #args = parser_delete_records.parse_args(request)
    if data is not None:
        filter = json.loads(data or '{}')
        if 'id' in filter:
            values = filter['id']
            for id in values:
                rec = db.session.query(model).filter(model.id == id).one()
                db.session.delete(rec)

            try:
                db.session.commit()
                return 204
            except IntegrityError:
                db.session.rollback()
                return 500
            except:
                db.session.rollback()
                return 555
        return 204
    else:
        return 555
