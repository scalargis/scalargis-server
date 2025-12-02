import json
import sqlalchemy
import uuid
from datetime import datetime
from flask import current_app, request, render_template, url_for
from werkzeug.local import LocalProxy
from sqlalchemy import cast, or_, Integer, Boolean, func
from flask_security.utils import encrypt_password
from flask_security.confirmable import generate_confirmation_token, confirm_email_token_status
from flask_restx import marshal
from ..parsers import *
from app.models.portal import *
from ...endpoints import check_user, get_user
from ..serializers import account_api_model
from . import get_record_by_id
from sqlalchemy.exc import IntegrityError
from app.utils.constants import ROLE_ANONYMOUS, ROLE_AUTHENTICATED
from app.utils.mailing import send_mail
from app.models.security import Role, Group, User
from instance import settings
from app.utils import constants
from app.utils.security import get_token, get_user_token
from app.utils.http import get_host_url, get_script_root, get_base_url
# NIF Validation
import doctest
from app.extensions.authama.utils import validate_nif_ownership
import logging

DIGITOS_NIF = 9
DIGITOS_CONTROLO = 8

logger = logging.getLogger(__name__)

# Convenient references
_security = LocalProxy(lambda: current_app.extensions['security'])


def send_email_confirmation(user, subject=None, msg=None, template=None, redirect=None):
    #Avoid circular references. TODO: improve main_app reference
    from app.main import app as main_app

    token = generate_confirmation_token(user)

    msg_subject = subject if subject else "Registo de Utilizador"

    msg_text = msg if msg else render_template(template or '/v1/security/email/confirm_registration.html',
                                               APP_HOST_URL=get_host_url(),
                                               APP_SCRIPT_ROOT=get_script_root(),
                                               APP_BASE_URL=get_base_url(),
                                               security=_security,
                                               user=user, token=token, redirect=redirect)

    send_mail(main_app, [user.email], msg_subject, msg_text)


def send_email_password_reset(user, subject=None, msg=None, template=None, redirect=None):
    # Avoid circular references. TODO: improve main_app reference
    from app.main import app as main_app

    token = generate_confirmation_token(user)

    msg_subject = subject if subject else "Recuperação de Password"
    msg_text = msg if msg else render_template(template or '/v1/security/email/reset_instructions.html',
                                            APP_HOST_URL=get_host_url(),
                                            APP_SCRIPT_ROOT=get_script_root(),
                                            APP_BASE_URL=get_base_url(),
                                            security=_security,
                                            user=user, token=token, redirect=redirect)

    send_mail(main_app, [user.email], msg_subject, msg_text)


def send_email_user_registration(user, subject=None, msg=None, template=None, redirect=None):
    # Avoid circular references. TODO: improve main_app reference
    from app.main import app as main_app

    token = generate_confirmation_token(user)

    msg_subject = subject if subject else "Registo de utilizador"
    msg_text = msg if msg else render_template(template or '/v1/security/email/registration_instructions.html',
                                    APP_HOST_URL=get_host_url(),
                                    APP_SCRIPT_ROOT=get_script_root(),
                                    APP_BASE_URL=get_base_url(),
                                    security=_security,
                                    user=user, token=token, redirect=redirect)

    send_mail(main_app, [user.email], msg_subject, msg_text)

# calcular_digito_controlo e valida_nif retirados de: wikipedia, numero de identificação fiscal.
# utilizamos com valida_nif(nif) para validar o NIF fornecido no registo de utilizador.
def calcular_digito_controlo(digitos: str) -> str:
    """Calcula o digito de controle de um NIF Ex. 99999999[0]
    >>> calcular_digito_controlo('99999999')
    '0'
    >>> calcular_digito_controlo('74089837')
    '0'
    >>> calcular_digito_controlo('28702400')
    '8'
    """
    if not digitos.isdigit():
        raise ValueError("Nem todos os caracteres são digitos")
    if not len(digitos) == DIGITOS_CONTROLO:
        raise ValueError(f"Número de digitos diferente de {DIGITOS_CONTROLO}")

    soma = (
        int(digitos[0]) * 9
        + int(digitos[1]) * 8
        + int(digitos[2]) * 7
        + int(digitos[3]) * 6
        + int(digitos[4]) * 5
        + int(digitos[5]) * 4
        + int(digitos[6]) * 3
        + int(digitos[7]) * 2
    )
    resto = soma % 11
    if resto == 0 or resto == 1:
        return "0"
    return str(11 - resto)


def valida_nif(nif: str) -> bool:
    """Validação do número de identificação fiscal
    >>> valida_nif('999999990')
    True
    >>> valida_nif('999999999')
    False
    >>> valida_nif('501442600')
    True
    """
    if not nif.isdigit() or len(nif) != DIGITOS_NIF:
        return False
    return nif[-1] == calcular_digito_controlo(nif[:DIGITOS_CONTROLO])


def register_user(request):
    if request.is_json:
        name = request.json.get('name')
        email = request.json.get('email')
        username = request.json.get('username')
        password = request.json.get('password')
        redirect = request.json.get('redirect')
        nif = request.json.get('nif')
        oauth_token = request.json.get('oauth_token')
        oauth_context_id = request.json.get('oauth_context_id')
    else:
        cred = json.loads(request.data.decode('utf-8'))
        name = cred.get('name')
        email = cred.get('email')
        username = cred.get('username')
        password = cred.get('password')
        redirect = cred.get('redirect')
        nif = cred.get('nif')
        oauth_token = cred.get('oauth_token')
        oauth_context_id = cred.get('oauth_context_id')

    user = User.query.filter(or_(func.lower(User.username) == func.lower(username),
                                 func.lower(User.email) == func.lower(email))).first()

    if not user is None:
        return {'status': 409, 'error': True,
                'message': 'Já existe um utilizador com o username ou email indicado.'}, 409

    # Check for duplicate NIF if provided
    if nif is not None and nif != '':
        existing_nif_user = User.query.filter_by(nif=nif).first()
        if existing_nif_user is not None:
            return {'status': 409, 'error': True,
                    'message': 'Já existe um utilizador com o NIF indicado.'}, 409

    # ========================================
    # NIF OWNERSHIP VALIDATION
    # ========================================
    # If NIF is provided, OAuth credentials MUST be present and NIF ownership MUST be validated
    # If NIF is NOT provided, registration proceeds normally (admin use case)
    if nif is not None and nif != '':
        # Check OAuth credentials are provided
        if not oauth_token or not oauth_context_id:
            logger.warning(f'Registration attempted with NIF {nif} but missing OAuth credentials')
            return {'status': 400, 'error': True,
                    'message': 'Validação de NIF requerida. Por favor, registe-se através de Autenticação.Gov.'}, 400

        # Validate NIF ownership by calling FA API
        FA_API_URL = 'https://autenticacao.gov.pt/OAuthResourceServer/Api/AttributeManager'

        is_valid, error_msg = validate_nif_ownership(
            nif=nif,
            oauth_token=oauth_token,
            oauth_context_id=oauth_context_id,
            fa_api_url=FA_API_URL
        )

        if not is_valid:
            logger.warning(f'NIF ownership validation failed for NIF {nif}: {error_msg}')
            return {'status': 403, 'error': True,
                    'message': 'Falha na validação do NIF. O NIF fornecido não corresponde ao utilizado na autenticação.'}, 403

        logger.info(f'NIF {nif} ownership validated successfully for user registration')

    # NIF validation
    # Can be null/empty or valid NIF
    if nif is not None and nif != '':
        if not valida_nif(nif):
            return {'status': 400, 'error': True,
                    'message': 'NIF inválido.'}, 400

    user = User()

    user.name = name
    user.username = username
    user.email = email
    user.nif = nif if nif and nif != '' else None
    user.active = True
    user.password = encrypt_password(password)

    #Poderia nao ter try except, e apenas o scope do try. 
    # No entanto, a operacao na DB 'e o fiscalizador final de integridade.
    # Ou seja, poderia eventualmente dar se o caso de a verificacao de duplicados acima falhar.
    # E chegava aqui, sem except, e a excecao nao seria tratada.
    try:
        db.session.add(user)
        db.session.commit()
        db.session.refresh(user)
    except IntegrityError:
        db.session.rollback()
        return {'status': 409, 'error': True,
                'message': 'Já existe um utilizador com o username, email ou NIF indicado.'}, 409

    #send_email_user_registration(user, subject='Registo de utilizador', redirect=redirect)

    return {'success': True, 'message': 'Foi enviado um email para ' + email + ' com as instruções para confirmação e conclusão do registo.'}, 200



def send_confirmation(request):

    if request.is_json:
        email = request.json.get('email')
        redirect = request.json.get('redirect') or ''
    else:
        data = json.loads(request.data.decode('utf-8'))
        email = data.get('email')
        redirect = data.get('redirect') or ''

    user = User.query.filter(func.lower(User.email) == func.lower(email)).first() if email else None

    if user is not None:
        redirect = redirect if redirect else user.default_viewer or ''
        send_email_user_registration(user, subject="Registo de utilizador", redirect=redirect)
    else:
        return {'status': 401, 'error': True, 'message': 'Não existe nenhum registo de utilizador com o email indicado.'}, 401

    return {'message': 'A confirmação de registo de utilizador foi enviada para o email {}'.format(email), 'email': email}, 200


def confirm_email(request):
    token = None

    authenticated = False
    user_token = None

    from app.database import db

    if request.method == 'POST':
        if request.is_json:
            token = request.json.get('token')
        else:
            cred = json.loads(request.data.decode('utf-8'))
            token = cred.get('token')
    else:
        if 'token' in request.args:
            token = request.args.get('token')

    if token:
        expired, invalid, user = confirm_email_token_status(token)
    else:
        return { 'status': 401, 'error': True, 'message': 'Confirmação de registo inválida.'}, 401

    already_confirmed = user is not None and user.confirmed_at is not None

    if expired and not already_confirmed:
        return { 'status': 401, 'error': True, 'message': 'Confirmação de registo expirada.'}, 401
    if invalid or (expired and not already_confirmed):
        return { 'status': 401, 'error': True, 'message': 'Confirmação de registo inválida.'}, 401

    if user:
        user_token = user.get_auth_token()

        authenticated = True

        user_roles = []
        for ru in user.roles:
            user_roles.append(ru.name)
        user_roles.append(constants.ROLE_AUTHENTICATED)

        if not already_confirmed:
            user.active = True
            user.confirmed_at = datetime.utcnow()

            db.session.add(user)
            db.session.commit()

        data = {
            'authenticated': authenticated,
            'token': user_token or '',
            'username': user.username,
            'name': user.name,
            'userroles': user_roles,
            'auth_token': user.auth_token if user.auth_token and
                                             (
                                             not user.auth_token_expire or user.auth_token_expire >= datetime.now()) else ''
        }
    else:
        return {'status': 401, 'error': True, 'message': 'Confirmação de registo inválida.'}, 401

    return data, 200


def send_password_reset(request):

    if request.is_json:
        username = request.json.get('username')
        redirect = request.json.get('redirect')
    else:
        data = json.loads(request.data.decode('utf-8'))
        username = data.get('username')
        redirect = data.get('redirect') if 'redirect' in data else None

    user = User.query.filter(func.lower(User.email) == func.lower(username)).first() if username else None

    if user is None:
        user = User.query.filter(func.lower(User.username) == func.lower(username)).first() if username else None

    if user is not None:
        redirect = redirect if redirect else user.default_viewer or ''
        send_email_password_reset(user, subject="Recuperação de Password", redirect=redirect)
    else:
        return {'status': 401, 'error': True, 'message': 'Não existe nenhum utilizador com o username ou email indicado.'}, 401

    return { 'message': 'Foi enviado um email para ' + user.email + ' com as instruções para recuperação da palavra-passe.'}, 200


def password_reset_validation(request):
    token = None

    if request.method == 'POST':
        if request.is_json:
            token = request.json.get('token')
        else:
            cred = json.loads(request.data.decode('utf-8'))
            token = cred.get('token')

    if token:
        expired, invalid, user = confirm_email_token_status(token)
    else:
        return {'status': 401, 'error': True, 'message': 'Confirmação de alteração de palavra-passe inválida.'}, 401

    if expired:
        return {'status': 401, 'error': True, 'message': 'Confirmação de alteração de password expirada.'}, 401

    if invalid:
        return {'status': 401, 'error': True, 'message': 'Confirmação de alteração de password inválida.'}, 401

    if user:
        if not user.is_active:
            return {'status': 401, 'error': True, 'message': 'Confirmação de alteração de palavra-passe inválida.'}, 401

        data = {
            'username': user.username,
            'name': user.name,
        }
    else:
        return {'status': 401, 'error': True, 'message': 'Confirmação de alteração de password inválida.'}, 401

    return data, 200


def set_password(request):
    password = None

    authenticated = False
    user_token = None

    from app.database import db

    if request.method == 'POST':
        if request.is_json:
            token = request.json.get('token')
            password = request.json.get('password')
        else:
            cred = json.loads(request.data.decode('utf-8'))
            token = cred.get('token')
            password = cred.get('password')

    if token:
        expired, invalid, user = confirm_email_token_status(token)
    else:
        return { 'status': 401, 'error': True, 'message': 'Confirmação de alteração de password inválida.'}, 401

    if expired or invalid:
        return { 'status': 401, 'error': True, 'message': 'Confirmação de alteração de password expirada.'}, 401

    if user:
        user.password = encrypt_password(password)
        db.session.add(user)
        db.session.commit()

        authenticated = True
        user_token = user.get_auth_token()

        user_roles = []
        for ru in user.roles:
            user_roles.append(ru.name)
        user_roles.append(constants.ROLE_AUTHENTICATED)

        data = {
            'authenticated': authenticated,
            'token': user_token or '',
            'username': user.username,
            'name': user.name,
            'userroles': user_roles,
            'auth_token': user.auth_token if user.auth_token and
                                             (
                                             not user.auth_token_expire or user.auth_token_expire >= datetime.now()) else ''
        }
    else:
        return {'status': 401, 'error': True, 'message': 'Confirmação de alteração de password inválida.'}, 401

    return data, 200


def update_password(request):

    password = request.json.get("password", None)

    if not password:
        return {}, 400

    user = get_user(request)

    if not user or not user.is_authenticated or not user.is_active:
        return {}, 401

    user.password = encrypt_password(password)
    db.session.add(user)
    db.session.commit()

    token = get_user_token(user.username, password)

    data = {'data': {'token': token}, 'status': 200, 'success': True, 'message': 'Password alterada com sucesso.'}

    return data, 200


def get_account(request):

    user = get_user(request)

    if not user or not user.is_authenticated or not user.is_active:
        return {}, 401

    return user, 200


def update_account(request):

    user = get_user(request)

    if not user or not user.is_authenticated or not user.is_active:
        return {}, 401


    try:
        data = request.json

        '''
        model = User
    
        record = db.session.query(model).filter(model.id == id).one()
        '''

        user.first_name = data['first_name'] if 'first_name' in data  else None
        user.last_name = data['last_name'] if 'last_name' in data else None
        user.name = data['name'] if 'name' in data else None
        user.username = data['username'] if 'username' in data else None
        user.email = data['email'] if 'email' in data else None
        if 'auth_token' in data and data['auth_token'] is not None:
            user.auth_token = data['auth_token']
            user.auth_token_expire = data['auth_token_expire'] if 'auth_token_expire' in data else None
        else:
            user.auth_token = None
            user.auth_token_expire = None

        db.session.add(user)
        db.session.commit()
        db.session.refresh(user)

        token = get_token(user.username)

        item = marshal(user, account_api_model)
        item['token'] = token

        return item, 200
    except IntegrityError as e:
        return {'status': 409, 'error': True,
                'message': 'Já existe um utilizador com o username ou email indicado.'}, 409
    except Exception as e:
        return {'status': 422, 'error': True,
                'message': 'Ocorreu um erro ao alterar o registo.'}, 422


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

    page = qy.paginate(page=page, per_page=per_page, error_out=False)
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

    records_page = qy.paginate(page=page, per_page=per_page, error_out=False)

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

    records_page = qy.paginate(page=page, per_page=per_page, error_out=False)

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
                    if filter[key] is True:
                        qy = qy.filter(field == True) # noqa
                    elif filter[key] is False:
                        qy = qy.filter(or_(field == False, field == None)) # noqa
                elif isinstance(field.property.columns[0].type, Integer):
                    qy = qy.filter(field == filter[key])
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