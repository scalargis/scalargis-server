import json
import sqlalchemy
import uuid
from datetime import datetime
from flask import request
from sqlalchemy import cast, or_, Integer, Boolean
from flask_security.utils import encrypt_password
from ..parsers import *
from app.models.domain.portal import *
from ...endpoints import check_user, get_user
from . import get_record_by_id
from sqlalchemy.exc import IntegrityError
from app.utils.constants import ROLE_ANONYMOUS, ROLE_AUTHENTICATED
from app.models.security import Role, Group, User

def get_roles_by_filter(request):
    """
    Returns paged list of Roles
    """
    args = parser_records_with_page.parse_args(request)
    page = args.get('page', 1)
    per_page = args.get('per_page', 10)
    filter = json.loads(args.get('filter') or '{}')

    qy = Role.query
    # .outerjoin(Plano.tipo_plano).outerjoin(Plano.concelho).outerjoin(Plano.estado_plano) \
    #    .outerjoin(Plano.historico_plano).outerjoin(Plano.dinamica_plano).outerjoin(Plano.movimento_plano)

    for key in filter:
        field = getattr(Role, key)
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
                order = getattr(getattr(Role, sort[i]), sort[i+1].lower())()

            if order is not None:
                qy = qy.order_by(order)

    page = qy.paginate(page, per_page, error_out=False)
    return page


def get_role(request):
    """
    Returns list of roles
    """
    args = parser_records_with_page.parse_args(request)
    page = args.get('page', 1)
    per_page = args.get('per_page', 10)
    filter = json.loads(args.get('filter') or '{}')

    model = Role

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

    records_page = qy.paginate(page, per_page, error_out=False)

    return records_page


'''
def get_role_by_id(id):
    data = get_record_by_id(Role, id)
    return data
'''
def get_role_by_id(id):
    model = Role

    qy = Role.query.filter(model.id == id)
    return qy.one()


def create_role(data):
    user = get_role(request)

    model = Role

    record = model()

    #for key in data:
    #    print(key)
    record.name = data['name'] if 'name' in data else None
    record.description = data['description'] if 'description' in data else None

    db.session.add(record)
    db.session.commit()
    db.session.refresh(record)
    return record


def update_role(id, data):
    user = get_user(request)

    model = Role

    record = db.session.query(model).filter(model.id == id).one()

    #for key in data:
    #    print(key)
    record.name = data['name'] if 'name' in data else None
    record.description = data['description'] if 'description' in data else None

    db.session.add(record)
    db.session.commit()
    db.session.refresh(record)
    return record


def delete_role(id):
    user = get_user(request)

    model = Role

    record = db.session.query(model).filter(model.id == id).one()
    db.session.delete(record)
    try:
        db.session.commit()
        return 204
    except IntegrityError:
        return 500
    except:
        return 555


def delete_role_list(data):
    user = get_user(request)

    model = Role

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

#-----------------------------------------------------------------------------

def get_group(request):
    """
    Returns list of groups
    """
    args = parser_records_with_page.parse_args(request)
    page = args.get('page', 1)
    per_page = args.get('per_page', 10)
    filter = json.loads(args.get('filter') or '{}')

    model = Group

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

    records_page = qy.paginate(page, per_page, error_out=False)

    return records_page


'''
def get_group_by_id(id):
    data = get_record_by_id(Group, id)
    return data
'''
def get_group_by_id(id):
    model = Group

    qy = Group.query.filter(model.id == id)
    return qy.one()


def create_group(data):
    user = get_user(request)

    model = Group

    record = model()

    roles = db.session.query(Role).all()
    users = db.session.query(User).all()

    #for key in data:
    #    print(key)
    record.name = data['name'] if 'name' in data else None
    record.description = data['description'] if 'description' in data else None

    # Roles
    if 'roles' in data:
        role_list = data['roles']
        for index in role_list:
            for role in roles:
                if role.id == index:
                    record.roles.append(role)
                    break
    # End Roles

    # Users
    if 'users' in data:
        user_list = data['users']
        for index in user_list:
            for u in users:
                if u.id == index:
                    record.users.append(u)
                    break
    # End Users

    db.session.add(record)
    db.session.commit()
    db.session.refresh(record)
    return record


def update_group(id, data):
    user = get_user(request)

    model = Group

    record = db.session.query(model).filter(model.id == id).one()

    roles = db.session.query(Role).all()
    users = db.session.query(User).all()

    #for key in data:
    #    print(key)
    record.name = data['name'] if 'name' in data else None
    record.description = data['description'] if 'description' in data else None

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

    # Users
    if 'users' in data:
        for u in reversed(record.users.all()):
           record.users.remove(u)

        user_list = data['users']
        for index in user_list:
            for u in users:
                if u.id == index:
                    record.users.append(u)
                    break
    # End Users

    db.session.add(record)
    db.session.commit()
    db.session.refresh(record)
    return record


def delete_group(id):
    user = get_user(request)

    model = Group

    record = db.session.query(model).filter(model.id == id).one()
    db.session.delete(record)
    try:
        db.session.commit()
        return 204
    except IntegrityError:
        return 500
    except:
        return 555


def delete_group_list(data):
    user = get_user(request)

    model = Group

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


#-----------------------------------------------------------------------------

def get_users(request):
    """
    Returns list of users
    """
    args = parser_records_with_page.parse_args(request)
    page = args.get('page', 1)
    per_page = args.get('per_page', 10)
    filter = json.loads(args.get('filter') or '{}')

    model = User

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
                if isinstance(field.property.columns[0].type, Boolean):
                    if filter[key]:
                        qy = qy.filter(field == True)
                    else:
                        qy = qy.filter(or_(field == False, field == None))
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

    records_page = qy.paginate(page, per_page, error_out=False)

    return records_page


def get_user_by_id(id):
    model = User

    qy = User.query.filter(model.id == id)
    return qy.one()


def create_user(data):
    user = get_user(request)

    model = User

    record = model()

    roles = db.session.query(Role).all()
    groups = db.session.query(Group).all()

    #for key in data:
    #    print(key)
    record.first_name = data['first_name'] if 'first_name' in data else None
    record.last_name = data['last_name'] if 'last_name' in data else None
    record.name = data['name'] if 'name' in data  else None
    record.username = data['username'] if 'username' in data else None
    record.email = data['email'] if 'email' in data else None
    record.active = data['active'] if 'active' in data else False
    if 'password' in data and data['password'] is not None:
        record.password = encrypt_password(data['password'])
    if 'auth_token' in data and data['auth_token'] is not None:
        record.auth_token = data['auth_token']
        record.auth_token_expire = data['auth_token_expire'] if 'auth_token_expire' in data else None

    # Roles
    if 'roles' in data:
        role_list = data['roles']
        for index in role_list:
            for role in roles:
                if role.id == index:
                    record.roles.append(role)
                    break
    # End Roles

    # Groups
    if 'groups' in data:
        group_list = data['groups']
        for index in group_list:
            for group in groups:
                if group.id == index:
                    record.groups.append(group)
                    break
    # End Groups

    db.session.add(record)
    db.session.commit()
    db.session.refresh(record)
    return record


def update_user(id, data):
    user = get_user(request)

    model = User

    record = db.session.query(model).filter(model.id == id).one()

    roles = db.session.query(Role).all()
    groups = db.session.query(Group).all()

    #for key in data:
    #    print(key)
    record.first_name = data['first_name'] if 'first_name' in data  else None
    record.last_name = data['last_name'] if 'last_name' in data else None
    record.name = data['name'] if 'name' in data else None
    record.username = data['username'] if 'username' in data else None
    record.email = data['email'] if 'email' in data else None
    record.active = data['active'] if 'active' in data else False
    if 'password' in data and data['password'] is not None:
        record.password = encrypt_password(data['password'])
    if 'auth_token' in data and data['auth_token'] is not None:
        record.auth_token = data['auth_token']
        record.auth_token_expire = data['auth_token_expire'] if 'auth_token_expire' in data else None
    else:
        record.auth_token = None
        record.auth_token_expire = None

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

    # Groups
    if 'groups' in data:
        for group in reversed(record.groups):
            record.groups.remove(group)

        group_list = data['groups']
        for index in group_list:
            for group in groups:
                if group.id == index:
                    record.groups.append(group)
                    break
    # End Groups

    db.session.add(record)
    db.session.commit()
    db.session.refresh(record)
    return record


def delete_user(id):
    user = get_user(request)

    model = User

    record = db.session.query(model).filter(model.id == id).one()
    db.session.delete(record)
    try:
        db.session.commit()
        return 204
    except IntegrityError:
        return 500
    except:
        return 555


def delete_user_list(data):
    user = get_user(request)

    model = User

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