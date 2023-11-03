import json
from datetime import datetime
import logging

from flask import request
import sqlalchemy
from sqlalchemy.orm import aliased
from sqlalchemy import cast, or_, Integer
from sqlalchemy.exc import IntegrityError
from shapely.wkt import loads
from geoalchemy2 import shape

from app.database import db
from ..parsers import *
from app.models.security import Role
from app.utils.security import is_admin_or_manager
from app.models.portal import Print, PrintGroup, PrintElement, PrintLayout, PrintGroupPrint, \
    PrintGroupChild, PrintGroupLayout, Viewer, ViewerPrint, ViewerPrintGroup
from ...endpoints import get_user
from . import get_record_by_id


logger = logging.getLogger(__name__)


print_fields = {
    "code": "code",
    "name": "name",
    "title": "title",
    "description": "description",
    "is_active": "is_active",

    "format": "format",
    "orientation": "orientation",
    "scale": "scale",
    "srid": "srid",

    "allow_drawing": "allow_drawing",
    "location_marking": "location_marking",
    "draw_location": "draw_location",
    "multi_geom": "multi_geom",
    "free_printing": "free_printing",
    "show_author": "show_author",
    "payment_reference": "payment_reference",
    "print_purpose": "print_purpose",
    "restrict_scales": "restrict_scales",
    "free_scale": "free_scale",
    "map_scale": "map_scale"
}

print_group_fields = {
    "code": "code",
    "name": "name",
    "title": "title",
    "description": "description",
    "is_active": "is_active",

    "allow_drawing": "allow_drawing",
    "location_marking": "location_marking",
    "draw_location": "draw_location",
    "multi_geom": "multi_geom",
    "free_printing": "free_printing",
    "show_author": "show_author",
    "payment_reference": "payment_reference",
    "print_purpose": "print_purpose",
    "restrict_scales": "restrict_scales",
    "free_scale": "free_scale",
    "map_scale": "map_scale",

    "select_prints": "select_prints",
    "group_prints": "group_prints",
    "show_all_prints": "show_all_prints",

    "tolerance_filter": "tolerance_filter"
}

print_element_fields = {
    "code": "code",
    "name": "name",
    "config": "config"
}


def get_by_filter(request):
    """
    Returns paged list of Prints
    """
    args = parser_records_with_page.parse_args(request)
    page = args.get('page', 1)
    per_page = args.get('per_page', 10)
    filter = json.loads(args.get('filter') or '{}')

    user = get_user(request)

    owner_id = None
    if user and not is_admin_or_manager(user):
        owner_id = user.id

    qy = Print.query

    if owner_id:
        qy = qy.filter(Print.owner_id == owner_id)

    for key in filter:
        kf = key
        if key in print_fields:
            kf = print_fields.get(key)
        if hasattr(Print, kf):
            field = getattr(Print, kf)
            if isinstance(filter[key], list):
                values = filter[key]
                conditions = []
                for val in values:
                    if isinstance(field.property.columns[0].type, Integer):
                        conditions.append(field == val)
                    else:
                        conditions.append(cast(field, sqlalchemy.String).ilike('%' + str(val) + '%'))
                qy = qy.filter(or_(*conditions))
            elif key not in ['groups', 'viewers']:
                if isinstance(field.property.columns[0].type, Integer):
                    qy = qy.filter(field == filter[key])
                else:
                    qy = qy.filter(cast(field, sqlalchemy.String).ilike('%' + str(filter[key]) + '%'))

    if 'groups' in filter:
        grps = filter['groups']
        qy = qy.join(PrintGroupPrint, Print.id == PrintGroupPrint.print_id)\
            .join(PrintGroup, PrintGroup.id == PrintGroupPrint.print_group_id)\
            .filter(PrintGroup.code.ilike('%' + str(grps) + '%'))

    if 'viewers' in filter:
        viewers = filter['viewers']
        qy = qy.join(ViewerPrint, Print.id == ViewerPrint.print_id).join(Viewer, Viewer.id == ViewerPrint.viewer_id).\
            filter(Viewer.name.ilike('%' + str(viewers) + '%'))

    sort = json.loads(args.get('sort') or '[]')
    if len(sort) > 0:
        for i in range(0, len(sort), 2):
            order = None
            if sort[i]:
                kf = sort[i]
                if sort[i] in print_fields:
                    kf = print_fields.get(sort[i])
                order = getattr(getattr(Print, kf), sort[i+1].lower())()

            if order is not None:
                qy = qy.order_by(order)

    page = qy.paginate(page=page, per_page=per_page, error_out=False)
    return page


def get_by_id(id):
    data = get_record_by_id(Print, id)
    return data


def create(data):
    user = get_user(request)

    record = Print()

    roles = db.session.query(Role).all()

    for key in print_fields:
        if hasattr(record, print_fields.get(key)):
            if data.get(key) == '':
                setattr(record, print_fields.get(key), None)
            else:
                setattr(record, print_fields.get(key), data.get(key))

    if 'geom_filter' in data:
        geom = None
        geom_wkt = data.get('geom_filter')
        geom_srid = data.get('geom_filter_srid')
        tolerance_filter = data.get('tolerance_filter')

        if geom_wkt and len(geom_wkt) > 0:
            geom = shape.from_shape(loads(geom_wkt), srid=geom_srid if geom_srid else Print.__srid__)

        if geom:
            record.geometry = geom
            record.tolerance_filter = tolerance_filter
        else:
            record.geometry = None
            record.tolerance_filter = None

    if 'restrict_scales_list' in data:
        record.restrict_scales_list = ','.join([str(x) for x in data['restrict_scales_list']]) if data[
            'restrict_scales_list'] else None

    if 'config_json' in data:
        record.config_json = json.dumps(data['config_json']) if data['config_json'] else None

    if 'form_fields' in data:
        record.form_fields = json.dumps(data['form_fields']) if data['form_fields'] else None

    # Layouts
    if 'layouts' in data:
        for ld in data.get('layouts'):
            new_layout = PrintLayout()
            new_layout.format = ld.get('format')
            new_layout.orientation = ld.get('orientation')
            if 'config' in ld:
                new_layout.config = ld['config'] if ld['config'] else None

            record.layouts.append(new_layout)

    # Roles
    if 'roles' in data:
        for index in data['roles']:
            for role in roles:
                if role.id == index:
                    record.roles.append(role)
                    break

    record.owner_id = user.id
    if 'owner_id' in data:
        record.owner_id = data.get('owner_id')

    record.id_user_create= user.id
    record.created_at = datetime.now()

    db.session.add(record)
    db.session.commit()
    db.session.refresh(record)
    return record


def update(id, data):
    user = get_user(request)

    record = Print.query.filter(Print.id == id).one_or_none()

    if record:
        if not is_admin_or_manager(user) and record.owner_id != user.id:
            return None

        roles = db.session.query(Role).all()

        for key in print_fields:
            if hasattr(record, print_fields.get(key)):
                if data.get(key) == '':
                    setattr(record, print_fields.get(key), None)
                else:
                    setattr(record, print_fields.get(key), data.get(key))

        if 'geom_filter' in data:
            geom = None
            geom_wkt = data.get('geom_filter')
            geom_srid = data.get('geom_filter_srid')
            tolerance_filter = data.get('tolerance_filter')

            if geom_wkt and len(geom_wkt) > 0:
                geom = shape.from_shape(loads(geom_wkt), srid=geom_srid if geom_srid else Print.__srid__)

            if geom:
                record.geometry = geom
                record.tolerance_filter = tolerance_filter
            else:
                record.geometry = None
                record.tolerance_filter = None

        if 'restrict_scales_list' in data:
            record.restrict_scales_list = ','.join([str(x) for x in data['restrict_scales_list']]) if data['restrict_scales_list'] else None

        if 'config_json' in data:
            record.config_json = json.dumps(data['config_json']) if data['config_json'] else None

        if 'form_fields' in data:
            record.form_fields = json.dumps(data['form_fields']) if data['form_fields'] else None

        # Layouts
        if 'layouts' in data:
            for lt in reversed(record.layouts):
                db.session.delete(lt)
            record.layouts.clear()
            for lt in data['layouts']:
                new_layout = PrintLayout()
                new_layout.format = lt.get('format')
                new_layout.orientation = lt.get('orientation')
                if 'config' in lt:
                    new_layout.config = lt['config'] if lt['config'] else None

                record.layouts.append(new_layout)

        # Roles
        if 'roles' in data:
            for role in reversed(record.roles):
                record.roles.remove(role)
            record.roles.clear()
            for index in data['roles']:
                for role in roles:
                    if role.id == index:
                        record.roles.append(role)
                        break

        if 'owner_id' in data:
            record.owner_id = data.get('owner_id')

        record.id_user_update = user.id
        record.updated_at = datetime.now()

        db.session.add(record)
        db.session.commit()
        db.session.refresh(record)

    return record


def delete(id):
    user = get_user(request)

    record = Print.query.filter(Print.id == id).one_or_none()

    if record:
        if not is_admin_or_manager(user) and record.owner_id != user.id:
            return 403

        db.session.delete(record)

        try:
            db.session.commit()
            return 204
        except IntegrityError as e:
            logger.exception(str(e))
            return 500
        except Exception as e:
            logger.exception(str(e))
            return 555
    else:
        return 404


def delete_list(data):
    user = get_user(request)

    model = Print

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
            except IntegrityError as e:
                logger.exception(str(e))
                db.session.rollback()
                return 500
            except Exception as e:
                logger.exception(str(e))
                db.session.rollback()
                return 555
        return 204
    else:
        return 555


def get_print_viewers_by_filter(print_id, request):
    """
    Returns paged list of Prints Viewers
    """
    args = parser_records_with_page.parse_args(request)
    page = args.get('page', 1)
    per_page = args.get('per_page', 10)
    filter = json.loads(args.get('filter') or '{}')

    qy = db.session.query(Viewer.id, Viewer.name, Viewer.title, Viewer.is_active, Viewer.is_shared).\
        join(ViewerPrint, Viewer.id == ViewerPrint.viewer_id)
    qy = qy.filter(ViewerPrint.print_id == print_id)

    for key in filter:
        kf = key
        '''
        if key in print_fields:
            kf = print_fields.get(key)
        '''
        if hasattr(Viewer, kf):
            field = getattr(Viewer, kf)
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
            order = None

            if sort[i] == 'xxxxx':
                s = 1
            elif sort[i]:
                kf = sort[i]
                '''
                if sort[i] in print_fields:
                    kf = print_fields.get(sort[i])
                '''
                order = getattr(getattr(Viewer, kf), sort[i+1].lower())()

            if order is not None:
                qy = qy.order_by(order)

    page = qy.paginate(page=page, per_page=per_page, error_out=False)

    return page

# ---------------------------------------

def get_print_group_by_filter(request):
    """
    Returns paged list of Print Groups
    """
    args = parser_records_with_page.parse_args(request)
    page = args.get('page', 1)
    per_page = args.get('per_page', 10)
    filter = json.loads(args.get('filter') or '{}')

    user = get_user(request)

    owner_id = None
    if user and not is_admin_or_manager(user):
        owner_id = user.id

    qy = PrintGroup.query

    if owner_id:
        qy = qy.filter(PrintGroup.owner_id == owner_id)

    for key in filter:
        kf = key
        if key in print_group_fields:
            kf = print_group_fields.get(key)
        if hasattr(PrintGroup, kf):
            field = getattr(PrintGroup, kf)
            if isinstance(filter[key], list):
                values = filter[key]
                conditions = []
                for val in values:
                    if isinstance(field.property.columns[0].type, Integer):
                        conditions.append(field == val)
                    else:
                        conditions.append(cast(field, sqlalchemy.String).ilike('%' + str(val) + '%'))
                qy = qy.filter(or_(*conditions))
            elif key not in ['groups', 'prints', 'viewers']:
                if isinstance(field.property.columns[0].type, Integer):
                    qy = qy.filter(field == filter[key])
                else:
                    qy = qy.filter(cast(field, sqlalchemy.String).ilike('%' + str(filter[key]) + '%'))

    if 'groups' in filter:
        grps = filter['groups']
        child = aliased(PrintGroup)
        qy = qy.join(PrintGroupChild, PrintGroup.id == PrintGroupChild.print_group_id).filter().\
            join(child, child.id == PrintGroupChild.print_group_child_id).filter(child.code.ilike('%' + str(grps) + '%'))

    if 'prints' in filter:
        prts = filter['prints']
        qy = qy.join(PrintGroupPrint, PrintGroup.id == PrintGroupPrint.print_group_id).\
            join(Print, Print.id == PrintGroupPrint.print_id).filter(Print.code.ilike('%' + str(prts) + '%'))

    if 'viewers' in filter:
        viewers = filter['viewers']
        qy = qy.join(ViewerPrintGroup, PrintGroup.id == ViewerPrintGroup.print_group_id).\
            join(Viewer, Viewer.id == ViewerPrintGroup.viewer_id).filter(Viewer.name.ilike('%' + str(viewers) + '%'))

    sort = json.loads(args.get('sort') or '[]')
    if len(sort) > 0:
        for i in range(0, len(sort), 2):
            order = None
            if sort[i]:
                kf = sort[i]
                if sort[i] in print_group_fields:
                    kf = print_group_fields.get(sort[i])
                order = getattr(getattr(PrintGroup, kf), sort[i+1].lower())()

            if order is not None:
                qy = qy.order_by(order)

    page = qy.paginate(page=page, per_page=per_page, error_out=False)
    return page


def get_print_group_by_id(id):
    data = get_record_by_id(PrintGroup, id)
    return data


def create_print_group(data):
    user = get_user(request)

    record = PrintGroup()

    roles = db.session.query(Role).all()

    for key in print_group_fields:
        if hasattr(record, print_group_fields.get(key)):
            if data.get(key) == '':
                setattr(record, print_group_fields.get(key), None)
            else:
                setattr(record, print_group_fields.get(key), data.get(key))

    if 'geom_filter' in data:
        geom = None
        geom_wkt = data.get('geom_filter')
        geom_srid = data.get('geom_filter_srid')
        tolerance_filter = data.get('tolerance_filter')

        if geom_wkt and len(geom_wkt) > 0:
            geom = shape.from_shape(loads(geom_wkt), srid=geom_srid if geom_srid else PrintGroup.__srid__)

        if geom:
            record.geometry = geom
            record.tolerance_filter = tolerance_filter
        else:
            record.geometry = None
            record.tolerance_filter = None

    if 'form_fields' in data:
        record.form_fields = json.dumps(data['form_fields']) if data['form_fields'] else None

    if 'layouts' in data:
        # Insert
        for ld in data.get('layouts'):
            new_layout = PrintGroupLayout()
            new_layout.format = ld.get('format')
            new_layout.orientation = ld.get('orientation')
            if 'config' in ld:
                new_layout.config = ld['config'] if ld['config'] else None

            record.layouts.append(new_layout)

    # Print groups (Child Groups)
    if 'groups' in data:
        order = 1
        for grp in data['groups']:
            new_childgroup = PrintGroupChild()
            new_childgroup.order = order
            new_childgroup.print_group_child_id = grp.get('id')
            record.print_group_child_assoc.append(new_childgroup)
            order += 1

    # Prints (Child Prints)
    if 'prints' in data:
        order = 1
        for plt in data['prints']:
            new_childprint = PrintGroupPrint()
            new_childprint.order = order,
            new_childprint.print_id = plt.get('id')
            record.print_assoc.append(new_childprint)
            order += 1

    # Roles
    if 'roles' in data:
        for index in data['roles']:
            for role in roles:
                if role.id == index:
                    record.roles.append(role)
                    break

    record.owner_id = user.id
    if 'owner_id' in data:
        record.owner_id = data.get('owner_id')

    record.id_user_create = user.id
    record.created_at = datetime.now()

    db.session.add(record)
    db.session.commit()
    db.session.refresh(record)
    return record


def update_print_group(id, data):
    user = get_user(request)

    record = PrintGroup.query.filter(PrintGroup.id == id).one_or_none()

    if record:
        if not is_admin_or_manager(user) and record.owner_id != user.id:
            return None

        roles = db.session.query(Role).all()

        for key in print_group_fields:
            if hasattr(record,  print_group_fields.get(key)):
                if data.get(key) == '':
                    setattr(record,  print_group_fields.get(key), None)
                else:
                    setattr(record,  print_group_fields.get(key), data.get(key))

        if 'geom_filter' in data:
            geom = None
            geom_wkt = data.get('geom_filter')
            geom_srid = data.get('geom_filter_srid')
            tolerance_filter = data.get('tolerance_filter')

            if geom_wkt and len(geom_wkt) > 0:
                geom = shape.from_shape(loads(geom_wkt), srid=geom_srid if geom_srid else PrintGroup.__srid__)

            if geom:
                record.geometry = geom
                record.tolerance_filter = tolerance_filter
            else:
                record.geometry = None
                record.tolerance_filter = None

        if 'form_fields' in data:
            record.form_fields = json.dumps(data['form_fields']) if data['form_fields'] else None

        # Layouts
        if 'layouts' in data:
            for lt in reversed(record.layouts):
                db.session.delete(lt)
            record.layouts.clear()
            for lt in data['layouts']:
                new_layout = PrintGroupLayout()
                new_layout.format = lt.get('format')
                new_layout.orientation = lt.get('orientation')
                if 'config' in lt:
                    new_layout.config = lt['config'] if lt['config'] else None

                record.layouts.append(new_layout)

        # Print Groups (Child Groups)
        if 'groups' in data:
            for prg in reversed(record.print_group_child_assoc):
                db.session.delete(prg)
            record.print_group_child_assoc.clear()
            order = 1
            for grp in data['groups']:
                rec = PrintGroupChild(order=order, print_group_id=record.id, print_group_child_id=grp.get('id'))
                db.session.add(rec)
                order += 1

        # Prints
        if 'prints' in data:
            for prt in reversed(record.print_assoc):
                db.session.delete(prt)
            record.print_assoc.clear()
            order = 1
            for prtn in data['prints']:
                rec = PrintGroupPrint(order=order, print_group_id=record.id, print_id=prtn.get('id'))
                db.session.add(rec)
                order += 1

        # Roles
        if 'roles' in data:
            for role in reversed(record.roles):
                record.roles.remove(role)
            record.roles.clear()
            for index in data['roles']:
                for role in roles:
                    if role.id == index:
                        record.roles.append(role)
                        break

        if 'owner_id' in data:
            record.owner_id = data.get('owner_id')

        record.id_user_update = user.id
        record.updated_at = datetime.now()

        db.session.add(record)
        db.session.commit()
        db.session.refresh(record)

    return record


def delete_print_group(id):
    user = get_user(request)

    record = PrintGroup.query.filter(PrintGroup.id == id).one_or_none()

    if record:
        if not is_admin_or_manager(user) and record.owner_id != user.id:
            return 403

        db.session.delete(record)

        try:
            db.session.commit()
            return 204
        except IntegrityError as e:
            logger.exception(str(e))
            return 500
        except Exception as e:
            logger.exception(str(e))
            return 555
    else:
        return 404


def delete_print_group_list(data):
    user = get_user(request)

    model = PrintGroup

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
            except IntegrityError as e:
                logger.exception(str(e))
                db.session.rollback()
                return 500
            except Exception as e:
                logger.exception(str(e))
                db.session.rollback()
                return 555
        return 204
    else:
        return 555


def get_print_group_viewers_by_filter(print_group_id, request):
    """
    Returns paged list of Prints groups Viewers
    """
    args = parser_records_with_page.parse_args(request)
    page = args.get('page', 1)
    per_page = args.get('per_page', 10)
    filter = json.loads(args.get('filter') or '{}')

    qy = db.session.query(Viewer.id, Viewer.name, Viewer.title, Viewer.is_active, Viewer.is_shared). \
        join(ViewerPrintGroup, Viewer.id == ViewerPrintGroup.viewer_id)
    qy = qy.filter(ViewerPrintGroup.print_group_id == print_group_id)

    for key in filter:
        kf = key
        '''
        if key in print_fields:
            kf = print_fields.get(key)
        '''
        if hasattr(Viewer, kf):
            field = getattr(Viewer, kf)
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
            order = None

            if sort[i] == 'xxxxx':
                s = 1
            elif sort[i]:
                kf = sort[i]
                '''
                if sort[i] in print_fields:
                    kf = print_fields.get(sort[i])
                '''
                order = getattr(getattr(Viewer, kf), sort[i + 1].lower())()

            if order is not None:
                qy = qy.order_by(order)

    page = qy.paginate(page=page, per_page=per_page, error_out=False)

    return page

# ---------------------------------------

def get_print_element_by_filter(request):
    """
    Returns paged list of Prints Elements
    """
    args = parser_records_with_page.parse_args(request)
    page = args.get('page', 1)
    per_page = args.get('per_page', 10)
    filter = json.loads(args.get('filter') or '{}')


    user = get_user(request)

    #owner_id = None
    #if user and not is_admin_or_manager(user):
    #    owner_id = user.id

    qy = PrintElement.query

    #if owner_id:
    #    qy = qy.filter(PrintElement.owner_id == owner_id)

    for key in filter:
        kf = key
        if key in print_element_fields:
            kf = print_element_fields.get(key)
        field = getattr(PrintElement, kf)
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
            order = None
            if sort[i]:
                kf = sort[i]
                if sort[i] in print_element_fields:
                    kf = print_element_fields.get(sort[i])
                order = getattr(getattr(PrintElement, kf), sort[i+1].lower())()

            if order is not None:
                qy = qy.order_by(order)

    page = qy.paginate(page=page, per_page=per_page, error_out=False)
    return page


def get_print_element_by_id(id):
    data = get_record_by_id(PrintElement, id)
    return data


def create_print_element(data):
    user = get_user(request)

    record = PrintElement()

    for key in print_element_fields:
        if hasattr(record, print_element_fields.get(key)):
            if data.get(key) == '':
                setattr(record, print_element_fields.get(key), None)
            else:
                setattr(record, print_element_fields.get(key), data.get(key))

    #record.owner_id = user.id
    #if 'owner_id' in data:
    #    record.owner_id = data.get('owner_id')

    record.id_user_create = user.id
    record.created_at = datetime.now()

    db.session.add(record)
    db.session.commit()
    db.session.refresh(record)
    return record


def update_print_element(id, data):
    user = get_user(request)

    record = PrintElement.query.filter(PrintElement.id == id).one_or_none()

    if record:
        #if not is_admin_or_manager(user) and record.owner_id != user.id:
        #    return None

        for key in print_element_fields:
            if hasattr(record, print_element_fields.get(key)):
                if data.get(key) == '':
                    setattr(record, print_element_fields.get(key), None)
                else:
                    setattr(record, print_element_fields.get(key), data.get(key))

        #if 'owner_id' in data:
        #    record.owner_id = data.get('owner_id')

        record.id_user_update = user.id
        record.updated_at = datetime.now()

        db.session.add(record)
        db.session.commit()
        db.session.refresh(record)

    return record


def delete_print_element(id):
    user = get_user(request)

    record = PrintElement.query.filter(PrintElement.id == id).one_or_none()

    if record:
        #if not is_admin_or_manager(user) and record.owner_id != user.id:
        #    return 403

        db.session.delete(record)

        try:
            db.session.commit()
            return 204
        except IntegrityError as e:
            logger.exception(str(e))
            return 500
        except Exception as e:
            logger.exception(str(e))
            return 555
    else:
        return 404


def delete_print_element_list(data):
    user = get_user(request)

    model = PrintElement

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
            except IntegrityError as e:
                logger.exception(str(e))
                db.session.rollback()
                return 500
            except Exception as e:
                logger.exception(str(e))
                db.session.rollback()
                return 555
        return 204
    else:
        return 555