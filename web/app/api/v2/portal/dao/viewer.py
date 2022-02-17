import json
import sqlalchemy
import uuid
from datetime import datetime
from flask import request
from sqlalchemy import cast, or_, Integer
from ..parsers import *
from app.models.domain.portal import *
from app.models.security import Role
from ...endpoints import check_user, get_user
from . import get_record_by_id
from sqlalchemy.exc import IntegrityError
from app.utils.constants import ROLE_ANONYMOUS, ROLE_AUTHENTICATED, ROLE_ADMIN, ROLE_MANAGER
from app.utils.security import is_admin_or_manager
from ..dao.app import get_viewer_record

viewer_fields = [
    'name',
    'title',
    'description',
    'keywords',
    'author',
    'lang',
    'slug',
    'bbox',
    'maxbbox',
    'config_version',
    'default_component',
    'show_help',
    'show_credits',
    'show_contact',
    'on_homepage',
    #'img_homepage',
    #'img_logo',
    'send_email_notifications_admin',
    'email_notifications_admin',
    'template',
    'is_active'
]

class TransCoordResult(db.Model):
    code = db.Column(db.String(50), primary_key=True)
    srid = db.Column(db.Integer())
    name = db.Column(db.String(255))
    x = db.Column(db.Float())
    y = db.Column(db.Float())
    z = db.Column(db.Float())

    def serialize(self):
        return dict(codigo=self.codigo,
                    srid=self.srid,
                    nome=self.nome,
                    x=self.x,
                    y=self.y,
                    z=self.z)

def get_by_filter(request):
    """
    Returns paged list of Planos
    """
    args = parser_records_with_page.parse_args(request)
    page = args.get('page', 1)
    per_page = args.get('per_page', 10)
    filter = json.loads(args.get('filter') or '{}')


    user = get_user(request)

    owner_id = None
    if user and not is_admin_or_manager(user):
        owner_id = user.id

    qy = Viewer.query
    # .outerjoin(Plano.tipo_plano).outerjoin(Plano.concelho).outerjoin(Plano.estado_plano) \
    #    .outerjoin(Plano.historico_plano).outerjoin(Plano.dinamica_plano).outerjoin(Plano.movimento_plano)

    if owner_id:
        qy = qy.filter(Viewer.owner_id == owner_id)

    for key in filter:
        field = getattr(Viewer, key)
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
            if sort[i] == 'tipo_plano':
                s = 1
                # order = getattr(getattr(EstadoPlano, 'designacao'), sort[i+1].lower())()
            elif sort[i]:
                order = getattr(getattr(Viewer, sort[i]), sort[i+1].lower())()

            if order is not None:
                qy = qy.order_by(order)

    page = qy.paginate(page, per_page, error_out=False)
    return page


def get_by_id(id):
    data = get_record_by_id(Viewer, id)
    return data


def create(data):
    user = get_user(request)

    record = Viewer()

    roles = db.session.query(Role).all()

    for field in viewer_fields:
        if hasattr(record, field):
            setattr(record, field, data.get(field))

    if 'config_json' in data:
        record.config_json = json.dumps(data['config_json'])

    # Roles
    if 'roles' in data:
        role_list = data['roles']
        for index in role_list:
            for role in roles:
                if role.id == index:
                    record.roles.append(role)
                    break
    # End Roles

    if not is_admin_or_manager(user):
        record.owner_id = user.id
    elif 'owner_id' in data:
        record.owner_id = data.get('owner_id')

    db.session.add(record)

    # Tipos Plantas (Child Groups)
    if 'print_groups' in data:
        order = 1
        for pgrp in data['print_groups']:
            rec = ViewerPrintGroup(order=order, viewer_id=record.id, print_group_id=pgrp.get('id'))
            db.session.add(rec)
            order += 1

    # Plantas (Child Prints)
    if 'prints' in data:
        order = 1
        for prt in data['prints']:
            rec = ViewerPrint(order=order, viewer_id=record.id, print_id=prt.get('id'))
            db.session.add(rec)
            order += 1

    db.session.commit()
    db.session.refresh(record)
    return record


def update(id, data):
    user = get_user(request)

    record = Viewer.query.filter(Viewer.id == id).one_or_none()

    if record:
        if not is_admin_or_manager(user) and record.owner_id != user.id:
            return None

        roles = db.session.query(Role).all()

        for field in viewer_fields:
            if hasattr(record, field) and field in data:
                setattr(record, field, data.get(field))

        if 'config_json' in data:
            record.config_json = json.dumps(data['config_json'])

        # Tipos Plantas (Child Groups)
        if 'print_groups' in data:
            for print_group in record.print_groups:
                db.session.delete(print_group)
            order = 1
            for pgrp in data['print_groups']:
                rec = record.print_groups.append(ViewerPrintGroup(order=order, print_group_id=pgrp.get('id')))
                order += 1

        # Plantas (Child Prints)
        if 'prints' in data:
            for print in record.prints:
                db.session.delete(print)
            order = 1
            for prt in data['prints']:
                rec = record.prints.append(ViewerPrint(order=order, print_id=prt.get('id')))
                order += 1

        # Roles
        if 'roles' in data:
            for role in reversed(record.roles):
                record.roles.remove(role)

            role_list = data['roles']
            for index in role_list:
                for role in roles:
                    if role.id == index:
                        record.roles.append(role)
                        break
        # End Roles

        if 'owner_id' in data:
            record.owner_id = data.get('owner_id')

        db.session.add(record)
        db.session.commit()
        db.session.refresh(record)

    return record


def delete(id):
    user = get_user(request)

    record = Viewer.query.filter(Viewer.id == id).one_or_none()

    if record:
        if not is_admin_or_manager(user) and record.owner_id != user.id:
            return 403

        # Tipos Plantas (Child Groups)
        for print_group in record.print_groups:
            db.session.delete(print_group)

        # Plantas (Child Prints)
        for print in record.prints:
            db.session.delete(print)

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


def delete_list(data):
    user = get_user(request)

    model = Viewer

    if data is not None:
        filter = json.loads(data or '{}')
        if 'id' in filter:
            values = filter['id']
            for id in values:
                record = db.session.query(model).filter(model.id == id).one()

                if is_admin_or_manager(user) or record.owner_id == user.id:
                    # Tipos Plantas (Child Groups)
                    for print_group in record.print_groups:
                        db.session.delete(print_group)

                    # Plantas (Child Prints)
                    for print in record.prints:
                        db.session.delete(print)

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
'''
def delete_many(data):
    #args = parser_delete_records.parse_args(request)
    if data is not None:
        filter = json.loads(data or '{}')
        if 'id' in filter:
            values = filter['id']
            for id in values:
                record = db.session.query(Viewer).filter(Viewer.id == id).one()
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
'''

def app_create(data):
    response = {
        "id": None, "uuid": None, "name": None, "success": False
    }

    try:
        user = get_user(request)

        record = Viewer()

        record.uuid = uuid.uuid4().hex
        record.title = data.get('title')
        record.name = data.get('name') or record.uuid
        record.description = data.get('description')
        record.slug = data.get('slug') or record.uuid
        record.config_version = '1.0'
        record.allow_add_layers = data.get('allow_add_layers')
        record.allow_user_session = data.get('allow_user_session')

        config_json =  json.loads(data['config_json']) if isinstance(data['config_json'], str) else data['config_json']
        config_json['title'] = record.title
        config_json['name'] = record.name or record.uuid
        config_json['description'] = record.description

        #remove record level properties
        config_json.pop('id', None)
        config_json.pop('name', None)
        config_json.pop('title', None)
        config_json.pop('description', None)

        #remove ThemeWizard component if add layers not allowed
        if not record.allow_add_layers:
            components = config_json['components']
            components[:] = [c for c in components if c.get('type') != 'ThemeWizard']

        record.config_json = json.dumps(config_json)

        if user:
            record.id_user_create = user.id
            record.owner_id = user.id

        record.created_at = datetime.now()
        record.is_active = True

        db.session.add(record)

        # Add Roles
        role = Role.query.filter_by(name=ROLE_AUTHENTICATED).first()
        record.roles.append(role)
        if not user or data.get('allow_anonymous') is None or data.get('allow_anonymous') == True:
            role = Role.query.filter_by(name=ROLE_ANONYMOUS).first()
            record.roles.append(role)

        db.session.commit()
        db.session.refresh(record)

        response = {
            "id": record.id, "uuid": record.uuid, "name": record.name, "success": True
        }
    except:
        pass

    return response

def app_update(viewer_id_or_slug, data):

    response = {
        "id": None, "uuid": None, "name": None, "success": False
    }

    record = get_viewer_record(viewer_id_or_slug)

    if not record:
        return response, 404

    user = get_user(request)

    if not user or not user.is_authenticated or not user.is_active:
        return response, 401

    if user.id != record.owner_id:
        return response, 403

    record.title = data.get('title')
    record.name = data.get('name')
    record.description = data.get('description')
    record.config_version = '1.0'
    record.allow_add_layers = data.get('allow_add_layers')
    record.allow_user_session = data.get('allow_user_session')

    config_json = json.loads(data['config_json']) if isinstance(data['config_json'], str) else data['config_json']
    config_json['title'] = record.title
    config_json['name'] = record.name or record.uuid
    config_json['description'] = record.description

    # remove record level properties
    config_json.pop('id', None)
    config_json.pop('name', None)
    config_json.pop('title', None)
    config_json.pop('description', None)

    # remove ThemeWizard component if add layers not allowed
    if not record.allow_add_layers:
        components = config_json['components']
        components[:] = [c for c in components if c.get('type') != 'ThemeWizard']

    record.config_json = json.dumps(config_json)

    if 'is_active' in data:
        record.is_active = data['is_active']

    if 'allow_anonymous' in data:
        if data['allow_anonymous'] == False:
            for r in record.roles:
                if r.name == ROLE_ANONYMOUS:
                    record.roles.remove(r)
                    break
        elif data['allow_anonymous'] == True:
            has_anonymous = False
            for r in record.roles:
                if r.name == ROLE_ANONYMOUS:
                    has_anonymous = True
                    break
            # Add anonymous role to viewer
            if not has_anonymous:
                role = Role.query.filter_by(name='Anonymous').first()
                record.roles.append(role)

    record.id_user_update = user.id
    record.updated_at = datetime.now()

    db.session.add(record)
    db.session.commit()
    db.session.refresh(record)

    response = {
            "id": record.id, "uuid": record.uuid, "name": record.name, "success": True
        }

    return  response, 200


def app_transcoord(data):
    srid = data.get('srid')
    x = data.get('x')
    y = data.get('y')
    z = data.get('z')

    from app.models.mapas import SistemaCoordenadas
    from sqlalchemy import sql

    crs_list = db.session.query(SistemaCoordenadas).all()

    records = db.session.query(TransCoordResult).from_statement(
        sql.text("select srid, codigo as code, nome as name, x, y, z from  portal.transform_coordinates(:srid, :x, :y, 0)")). \
        params(srid=srid, x=x, y=y, z=z).all()

    results = {}
    for r in records:
        units = 'm'
        crs = next((x for x in crs_list if x.codigo == r.code), None)
        if "+proj=longlat" in crs.proj4text:
            units = 'degrees'
        results[r.code] = {"code": r.code, "srid": r.srid, "units": units,
                 "title": r.name, "x": r.x, "y": r.y, "z": z}

    rec = {
        "coordinates": [x, y],
        "srid": srid,
        "results": results
    }

    return rec, 200