import json
import sqlalchemy
import uuid
from datetime import datetime
from flask import request
from sqlalchemy import cast, or_, Integer
from shapely.wkt import loads
from geoalchemy2 import shape
import geoalchemy2.functions as geo_funcs
from geoalchemy2.elements import WKTElement
from ..parsers import *
from app.models.mapas import Planta, PlantaLayout, TipoPlanta, SubPlanta,  TipoPlantaChild, PlantaTipoPlanta, \
    TipoPlantaLayout
from app.models.domain.portal import *
from ...endpoints import check_user, get_user
from . import get_record_by_id
from sqlalchemy.exc import IntegrityError
from app.utils import geo
from app.utils.constants import ROLE_ANONYMOUS, ROLE_AUTHENTICATED, ROLE_ADMIN, ROLE_MANAGER
from app.utils.security import is_admin_or_manager
from ..dao.app import get_viewer_record


print_fields = {
    "code": "codigo",
    "name": "nome",
    "title": "titulo",
    "description": "descricao",
    "is_active": "activo",

    "format": "formato",
    "orientation": "orientacao",
    "scale": "escala",
    "srid": "srid",
    #"configuracao": "config_json",

    "template": "template",
    "location_marking": "marcacaoLocal",
    "draw_location": "desenharLocal",
    "multi_geom": "multiGeom",
    "free_printing": "emissaoLivre",
    "add_title": "tituloEmissao",
    "show_author": "autorEmissao",
    "payment_reference": "guiaPagamento",
    "print_purpose": "finalidadeEmissao",
    "restrict_scales": "escalasRestritas",
    "free_scale": "escalaLivre",
    "map_scale": "escalaMapa",
    "identification": "identificacao",
    #"identification_fields": "identificacaoCampos",
    #"form_fields": "formFields"
}

print_group_fields = {
    "code": "codigo",
    "name": "nome",
    "title": "titulo",
    "description": "descricao",
    "is_active": "activo",

    "location_marking": "marcacaoLocal",
    "draw_location": "desenharLocal",
    "multi_geom": "multiGeom",
    "free_printing": "emissaoLivre",
    "add_title": "tituloEmissao",
    "show_author": "autorEmissao",
    "payment_reference": "guiaPagamento",
    "print_purpose": "finalidadeEmissao",
    "restrict_scales": "escalasRestritas",
    "free_scale": "escalaLivre",
    "map_scale": "escalaMapa",
    "identification": "identificacaoRequerente",
    #"identification_fields": "identificacaoCampos",
    #"form_fields": "formFields"

    "select_prints": "seleccaoPlantas",
    "group_prints": "agruparPlantas",
    "show_all_prints": "showAll",
    #"geom_filter": "geometry_wkt",
    #"geom_filter_srid": "geometry_srid",
    "tolerance_filter": "tolerancia"
}

print_element_fields = {
    "code": "codigo",
    "name": "nome",
    "config": "configuracao"
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

    qy = Planta.query

    if owner_id:
        qy = qy.filter(Planta.owner_id == owner_id)

    for key in filter:
        kf = key
        if key in print_fields:
            kf = print_fields.get(key)
        field = getattr(Planta, kf)
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
                # order = getattr(getattr(EstadoPlano, 'designacao'), sort[i+1].lower())()
            elif sort[i]:
                kf = sort[i]
                if sort[i] in print_fields:
                    kf = print_fields.get(sort[i])
                order = getattr(getattr(Planta, kf), sort[i+1].lower())()

            if order is not None:
                qy = qy.order_by(order)

    page = qy.paginate(page, per_page, error_out=False)
    return page


def get_by_id(id):
    data = get_record_by_id(Planta, id)
    return data


def create(data):
    user = get_user(request)

    record = Planta()

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
            #ss = geo.transformGeom(loads(geom_wkt), 'epsg:{0}'.format(geom_srid),
            #                       'epsg:{0}'.format(table_geom_srid))
            geom = shape.from_shape(loads(geom_wkt), srid=geom_srid if geom_srid else 3763)

        if geom:
            record.geometry = geom
            record.tolerancia = tolerance_filter
        else:
            record.geometry = None
            record.tolerancia = None

    if 'restrict_scales_list' in data:
        record.escalasRestritasLista = ','.join([str(x) for x in data['restrict_scales_list']]) if data[
            'restrict_scales_list'] else None

    if 'config_json' in data:
        record.configuracao = json.dumps(data['config_json']) if data['config_json'] else None

    if 'form_fields' in data:
        record.formFields = json.dumps(data['form_fields']) if data['form_fields'] else None

    if 'identification_fields' in data:
        record.identificacaoCampos = json.dumps(data['identification_fields']) if data[
            'identification_fields'] else None

    if 'layouts' in data:
        for ld in data.get('layouts'):
            new_layout = PlantaLayout()
            new_layout.formato = ld.get('format')
            new_layout.orientacao = ld.get('orientation')
            if 'config' in ld:
                new_layout.configuracao = ld['config'] if ld['config'] else None

            record.layouts.append(new_layout)

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

    record.owner_id = user.id
    if 'owner_id' in data:
        record.owner_id = data.get('owner_id')

    db.session.add(record)
    db.session.commit()
    db.session.refresh(record)
    return record


def update(id, data):
    user = get_user(request)

    record = Planta.query.filter(Planta.id == id).one_or_none()

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
                #ss = geo.transformGeom(loads(geom_wkt), 'epsg:{0}'.format(geom_srid),
                #                       'epsg:{0}'.format(table_geom_srid))
                geom = shape.from_shape(loads(geom_wkt), srid=geom_srid if geom_srid else 3763)

            if geom:
                record.geometry = geom
                record.tolerancia = tolerance_filter
            else:
                record.geometry = None
                record.tolerancia = None

        if 'restrict_scales_list' in data:
            record.escalasRestritasLista = ','.join([str(x) for x in data['restrict_scales_list']]) if data['restrict_scales_list'] else None

        if 'config_json' in data:
            record.configuracao = json.dumps(data['config_json']) if data['config_json'] else None

        if 'form_fields' in data:
            record.formFields = json.dumps(data['form_fields']) if data['form_fields'] else None

        if 'identification_fields' in data:
            record.identificacaoCampos = json.dumps(data['identification_fields']) if data['identification_fields'] else None

        if 'layouts' in data:
            layout_ids = [l.get('id') for l in data.get('layouts') if l.get('id')]
            #Remove deleted
            for layout in reversed(record.layouts):
                if not (layout.id in layout_ids):
                    record.layouts.remove(layout)
            #Update
            for layout in record.layouts:
                for ld in data.get('layouts'):
                    if layout.id == ld.get('id'):
                        layout.formato = ld.get('format')
                        layout.orientacao = ld.get('orientation')
                        if 'config' in ld:
                            layout.configuracao = ld['config'] if ld['config'] else None
                            break
            #Insert
            for ld in data.get('layouts'):
                if not 'id' in ld or not ld.get('id'):
                    new_layout = PlantaLayout()
                    new_layout.formato = ld.get('format')
                    new_layout.orientacao = ld.get('orientation')
                    if 'config' in ld:
                        new_layout.configuracao = ld['config'] if ld['config'] else None

                    record.layouts.append(new_layout)

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

    record = Planta.query.filter(Planta.id == id).one_or_none()

    if record:
        if not is_admin_or_manager(user) and record.owner_id != user.id:
            return 403

        for layout in reversed(record.layouts):
            #record.layouts.remove(layout)
            db.session.delete(layout)

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

    model = Planta

    #args = parser_delete_records.parse_args(request)
    if data is not None:
        filter = json.loads(data or '{}')
        if 'id' in filter:
            values = filter['id']
            for id in values:
                rec = db.session.query(model).filter(model.id == id).one()

                # Remove print layouts
                for layout in reversed(rec.layouts):
                    # rec.layouts.remove(layout)
                    db.session.delete(layout)

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

#---------------------------------------

def get_print_group_by_filter(request):
    """
    Returns paged list of Prints groups
    """
    args = parser_records_with_page.parse_args(request)
    page = args.get('page', 1)
    per_page = args.get('per_page', 10)
    filter = json.loads(args.get('filter') or '{}')


    user = get_user(request)

    owner_id = None
    if user and not is_admin_or_manager(user):
        owner_id = user.id

    qy = TipoPlanta.query

    if owner_id:
        qy = qy.filter(TipoPlanta.owner_id == owner_id)

    for key in filter:
        kf = key
        if key in print_group_fields:
            kf = print_group_fields.get(key)
        field = getattr(TipoPlanta, kf)
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
                # order = getattr(getattr(EstadoPlano, 'designacao'), sort[i+1].lower())()
            elif sort[i]:
                kf = sort[i]
                if sort[i] in print_fields:
                    kf = print_fields.get(sort[i])
                order = getattr(getattr(TipoPlanta, kf), sort[i+1].lower())()

            if order is not None:
                qy = qy.order_by(order)

    page = qy.paginate(page, per_page, error_out=False)
    return page


def get_print_group_by_id(id):
    data = get_record_by_id(TipoPlanta, id)
    return data


def create_print_group(data):
    user = get_user(request)

    record = TipoPlanta()

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
            #ss = geo.transformGeom(loads(geom_wkt), 'epsg:{0}'.format(geom_srid),
            #                       'epsg:{0}'.format(table_geom_srid))
            geom = shape.from_shape(loads(geom_wkt), srid=geom_srid if geom_srid else 3763)

        if geom:
            record.geometry = geom
            record.tolerancia = tolerance_filter
        else:
            record.geometry = None
            record.tolerancia = None

    if 'config_json' in data:
        record.configuracao = json.dumps(data['config_json']) if data['config_json'] else None

    if 'form_fields' in data:
        record.formFields = json.dumps(data['form_fields']) if data['form_fields'] else None

    if 'identification_fields' in data:
        record.identificacaoCampos = json.dumps(data['identification_fields']) if data[
            'identification_fields'] else None

    if 'layouts' in data:
        # Insert
        for ld in data.get('layouts'):
            new_layout = TipoPlantaLayout()
            new_layout.formato = ld.get('format')
            new_layout.orientacao = ld.get('orientation')
            if 'config' in ld:
                new_layout.configuracao = ld['config'] if ld['config'] else None

            record.layouts.append(new_layout)

    # Tipos Plantas (Child Groups)
    if 'groups' in data:
        ordem = 1
        for grp in data['groups']:
            new_childgroup = TipoPlantaChild()
            new_childgroup.ordem = ordem
            new_childgroup.tipo_planta_child_id = grp.get('id')
            record.tipo_planta_child_assoc.append(new_childgroup)
            ordem += 1

    # Plantas (Child Prints)
    if 'prints' in data:
        ordem = 1
        for plt in data['prints']:
            new_childprint = PlantaTipoPlanta()
            new_childprint.ordem = ordem,
            new_childprint.planta_id = plt.get('id')
            record.planta_assoc.append(new_childprint)
            ordem += 1

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

    record.owner_id = user.id
    if 'owner_id' in data:
        record.owner_id = data.get('owner_id')

    db.session.add(record)
    db.session.commit()
    db.session.refresh(record)
    return record


def update_print_group(id, data):
    user = get_user(request)

    record = TipoPlanta.query.filter(TipoPlanta.id == id).one_or_none()

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
                #ss = geo.transformGeom(loads(geom_wkt), 'epsg:{0}'.format(geom_srid),
                #                       'epsg:{0}'.format(table_geom_srid))
                geom = shape.from_shape(loads(geom_wkt), srid=geom_srid if geom_srid else 3763)

            if geom:
                record.geometry = geom
                record.tolerancia = tolerance_filter
            else:
                record.geometry = None
                record.tolerancia = None

        if 'config_json' in data:
            record.configuracao = json.dumps(data['config_json']) if data['config_json'] else None

        if 'form_fields' in data:
            record.formFields = json.dumps(data['form_fields']) if data['form_fields'] else None

        if 'identification_fields' in data:
            record.identificacaoCampos = json.dumps(data['identification_fields']) if data['identification_fields'] else None

        if 'layouts' in data:
            layout_ids = [l.get('id') for l in data.get('layouts') if l.get('id')]
            #Remove deleted
            for layout in reversed(record.layouts):
                if not (layout.id in layout_ids):
                    record.layouts.remove(layout)
            #Update
            for layout in record.layouts:
                for ld in data.get('layouts'):
                    if layout.id == ld.get('id'):
                        layout.formato = ld.get('format')
                        layout.orientacao = ld.get('orientation')
                        if 'config' in ld:
                            layout.configuracao = ld['config'] if ld['config'] else None
                            break
            #Insert
            for ld in data.get('layouts'):
                if not 'id' in ld or not ld.get('id'):
                    new_layout = TipoPlantaLayout()
                    new_layout.formato = ld.get('format')
                    new_layout.orientacao = ld.get('orientation')
                    if 'config' in ld:
                        new_layout.configuracao = ld['config'] if ld['config'] else None

                    record.layouts.append(new_layout)

        # Tipos Plantas (Child Groups)
        if 'groups' in data:
            record.tipo_planta_child_assoc.clear()
            ordem = 1
            for grp in data['groups']:
                rec = TipoPlantaChild(ordem=ordem, tipo_planta_id=record.id, tipo_planta_child_id=grp.get('id'))
                db.session.add(rec)
                ordem += 1

        # Plantas (Child Prints)
        if 'prints' in data:
            for planta in reversed(record.plantas):
                db.session.delete(planta)
            ordem = 1
            for plt in data['prints']:
                record.plantas.append(PlantaTipoPlanta(ordem=ordem, planta_id=plt.get('id')))
                ordem += 1

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


def delete_print_group(id):
    user = get_user(request)

    record = TipoPlanta.query.filter(TipoPlanta.id == id).one_or_none()

    if record:
        if not is_admin_or_manager(user) and record.owner_id != user.id:
            return 403

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


def delete_print_group_list(data):
    user = get_user(request)

    model = TipoPlanta

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


#---------------------------------------

def get_print_element_by_filter(request):
    """
    Returns paged list of Prints elements
    """
    args = parser_records_with_page.parse_args(request)
    page = args.get('page', 1)
    per_page = args.get('per_page', 10)
    filter = json.loads(args.get('filter') or '{}')


    user = get_user(request)

    #owner_id = None
    #if user and not is_admin_or_manager(user):
    #    owner_id = user.id

    qy = SubPlanta.query

    #if owner_id:
    #    qy = qy.filter(SubPlanta.owner_id == owner_id)

    for key in filter:
        kf = key
        if key in print_element_fields:
            kf = print_element_fields.get(key)
        field = getattr(SubPlanta, kf)
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
                # order = getattr(getattr(EstadoPlano, 'designacao'), sort[i+1].lower())()
            elif sort[i]:
                kf = sort[i]
                if sort[i] in print_element_fields:
                    kf = print_element_fields.get(sort[i])
                order = getattr(getattr(SubPlanta, kf), sort[i+1].lower())()

            if order is not None:
                qy = qy.order_by(order)

    page = qy.paginate(page, per_page, error_out=False)
    return page


def get_print_element_by_id(id):
    data = get_record_by_id(SubPlanta, id)
    return data


def create_print_element(data):
    user = get_user(request)

    record = SubPlanta()

    for key in print_element_fields:
        if hasattr(record, print_element_fields.get(key)):
            if data.get(key) == '':
                setattr(record, print_element_fields.get(key), None)
            else:
                setattr(record, print_element_fields.get(key), data.get(key))

    #record.owner_id = user.id
    #if 'owner_id' in data:
    #    record.owner_id = data.get('owner_id')

    db.session.add(record)
    db.session.commit()
    db.session.refresh(record)
    return record


def update_print_element(id, data):
    user = get_user(request)

    record = SubPlanta.query.filter(SubPlanta.id == id).one_or_none()

    if record:
        #if not is_admin_or_manager(user) and record.owner_id != user.id:
        #    return None

        #roles = db.session.query(Role).all()

        for key in print_element_fields:
            if hasattr(record, print_element_fields.get(key)):
                if data.get(key) == '':
                    setattr(record, print_element_fields.get(key), None)
                else:
                    setattr(record, print_element_fields.get(key), data.get(key))

        #if 'owner_id' in data:
        #    record.owner_id = data.get('owner_id')

        db.session.add(record)
        db.session.commit()
        db.session.refresh(record)

    return record


def delete_print_element(id):
    user = get_user(request)

    record = SubPlanta.query.filter(SubPlanta.id == id).one_or_none()

    if record:
        #if not is_admin_or_manager(user) and record.owner_id != user.id:
        #    return 403

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


def delete_print_element_list(data):
    user = get_user(request)

    model = SubPlanta

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