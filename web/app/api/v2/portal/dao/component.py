import json
import sqlalchemy
from datetime import datetime
from flask import request
from sqlalchemy import cast, or_, Integer
from ..parsers import *
from app.models.domain.portal import *
from ...endpoints import check_user, get_user
from . import get_record_by_id
from sqlalchemy.exc import IntegrityError


component_fields = ['name', 'title', 'description', 'type', 'plugin', 'target', 'scripts', 'is_active', 'config_version',
                    'config_json', 'config_version', 'action', 'template', 'html_content',
                    'icon_css_class']

def get_by_filter(request):
    """
    Returns paged list of Components
    """
    args = parser_records_with_page.parse_args(request)
    page = args.get('page', 1)
    per_page = args.get('per_page', 10)
    filter = json.loads(args.get('filter') or '{}')

    qy = Component.query
    # .outerjoin(Plano.tipo_plano).outerjoin(Plano.concelho).outerjoin(Plano.estado_plano) \
    #    .outerjoin(Plano.historico_plano).outerjoin(Plano.dinamica_plano).outerjoin(Plano.movimento_plano)

    for key in filter:
        field = getattr(Component, key)
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
            if isinstance(field.property.columns[0].type, Integer):
                qy = qy.filter(field == filter[key])
            else:
                qy = qy.filter(cast(field, sqlalchemy.String).ilike('%' + str(filter[key]) + '%'))

    sort = json.loads(args.get('sort') or '[]')
    if len(sort) > 0:
        for i in range(0, len(sort), 2):
            order = getattr(getattr(Component, sort[i]), sort[i+1].lower())()

            qy = qy.order_by(order)

    page = qy.paginate(page, per_page, error_out=False)
    return page


def get_by_id(id):
    data = get_record_by_id(Component, id)
    return data


def create(data):
    user = get_user(request)

    record = Component()

    for field in component_fields:
        if hasattr(record, field):
            setattr(record, field, data.get(field))

    record.config_json = json.dumps(data['config_json'])

    db.session.add(record)
    db.session.commit()
    db.session.refresh(record)
    return record


def update(id, data):
    user = get_user(request)

    record = db.session.query(Component).filter(Component.id == id).one()

    if record:
        for field in component_fields:
            if hasattr(record, field):
                setattr(record, field, data.get(field))

        record.config_json = json.dumps(data['config_json'])

        db.session.add(record)
        db.session.commit()
        db.session.refresh(record)

    return record

def delete(id):
    record = db.session.query(Component).filter(Component.id == id).one_or_none()

    if record:
        db.session.delete(record)
        try:
            db.session.commit()
            return 204
        except IntegrityError:
            return 500
        except:
            return 555
    else:
        return 404

def delete_many(data):
    #args = parser_delete_records.parse_args(request)
    if data is not None:
        filter = json.loads(data or '{}')
        if 'id' in filter:
            values = filter['id']
            for id in values:
                record = db.session.query(Component).filter(Component.id == id).one()
                db.session.delete(record)

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


def get_viewer_components_by_filter(viewer_id, request):
    """
    Returns paged list of Viewer Components
    """
    args = parser_records_with_page.parse_args(request)
    page = args.get('page', 1)
    per_page = args.get('per_page', 10)
    filter = json.loads(args.get('filter') or '{}')

    qy = ViewerComponent.query.filter(ViewerComponent.viewer_id==viewer_id)

    for key in filter:
        field = getattr(Component, key)
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
            if isinstance(field.property.columns[0].type, Integer):
                qy = qy.filter(field == filter[key])
            else:
                qy = qy.filter(cast(field, sqlalchemy.String).ilike('%' + str(filter[key]) + '%'))

    sort = json.loads(args.get('sort') or '[]')
    if len(sort) > 0:
        for i in range(0, len(sort), 2):
            order = getattr(getattr(Component, sort[i]), sort[i+1].lower())()

            qy = qy.order_by(order)

    page = qy.paginate(page, per_page, error_out=False)
    return page


def create_viewer_component(viewer_id, data):
    user = get_user(request)

    record = ViewerComponent()

    for field in component_fields:
        if hasattr(record, field):
            setattr(record, field, data.get(field))

    record.viewer_id = viewer_id
    record.component_id = data.get('id')

    record.config_json = json.dumps(data['config_json'])

    db.session.add(record)
    db.session.commit()
    db.session.refresh(record)
    return record


def get_viewer_component_by_id(viewer_id, id):
    data = db.session.query(ViewerComponent).filter(ViewerComponent.viewer_id==viewer_id). \
        filter(ViewerComponent.component_id==id).one_or_none()

    return data


def delete_viewer_component(viewer_id, id):
    record = db.session.query(ViewerComponent).filter(ViewerComponent.viewer_id==viewer_id). \
        filter(ViewerComponent.component_id==id).one_or_none()

    if record:
        db.session.delete(record)
        try:
            db.session.commit()
            return 204
        except IntegrityError:
            return 500
        except:
            return 555
    else:
        return 404

def update_viewer_component(viewer_id, id, data):
    user = get_user(request)

    record = db.session.query(ViewerComponent).filter(ViewerComponent.viewer_id==viewer_id). \
        filter(ViewerComponent.component_id==id).one_or_none()

    if record:
        for field in component_fields:
            if hasattr(record, field):
                setattr(record, field, data.get(field))

        record.config_json = json.dumps(data['config_json'])

        db.session.add(record)
        db.session.commit()
        db.session.refresh(record)

    return record