import os
import time
from datetime import timedelta

import pytest
from flask import Blueprint, Flask
from flask_restx import Api
from flask_security import Security, SQLAlchemyUserDatastore
from flask_security.utils import hash_password
from itsdangerous import TimestampSigner
from sqlalchemy import text

import app as app_package
from app.database import db
from app.models.security import Role, User, db_schema
from app.api.v1.endpoints import ns_authentication, ns_security
from app.api.v1.endpoints import security as _security_routes
from app.utils import security as app_security, tokens, utc_now

PASSWORD = 'Old-Passw0rd-1'
NEW_PASSWORD = 'New-Passw0rd-2'

USER_DDL = (
    'create table {0}."user" (id integer primary key, email text unique, username text unique, name text, '
    'first_name text, last_name text, password text, active boolean, confirmed_at datetime, '
    'last_login_at datetime, current_login_at datetime, last_login_ip text, current_login_ip text, '
    'login_count integer, auth_token text, auth_token_expire datetime, default_map text, default_viewer text, '
    'fs_uniquifier text not null unique)')
OTHER_DDL = [
    'create table {0}.role (id integer primary key, name text unique, description text, read_only boolean)',
    'create table {0}.permission (id integer primary key, name text unique, description text, read_only boolean)',
    'create table {0}."group" (id integer primary key, name text unique, description text, read_only boolean)',
    'create table {0}.roles_users (user_id integer, role_id integer)',
    'create table {0}.groups_users (user_id integer, group_id integer)',
    'create table {0}.roles_groups (group_id integer, role_id integer)',
    'create table {0}.roles_permissions (role_id integer, permission_id integer)',
]


@pytest.fixture
def flask_app():
    flask_app = Flask('api-token-test', template_folder=os.path.join(app_package.base_path, 'templates'))
    flask_app.config.from_object('instance.default')
    flask_app.config.update(SQLALCHEMY_DATABASE_URI='sqlite:///:memory:', SQLALCHEMY_TRACK_MODIFICATIONS=False,
                            SQLALCHEMY_ENGINE_OPTIONS={},
                            SECURITY_PASSWORD_HASH='pbkdf2_sha512', TESTING=True)
    flask_app.config['SECURITY_USER_IDENTITY_ATTRIBUTES'] = app_security.identity_attributes(
        flask_app.config.get('SECURITY_USER_IDENTITY_ATTRIBUTES'))
    db.init_app(flask_app)
    Security(flask_app, SQLAlchemyUserDatastore(db, User, Role))
    blueprint = Blueprint('api', 'api-token-api', url_prefix='/api')
    api = Api(blueprint)
    api.add_namespace(ns_authentication)
    api.add_namespace(ns_security)
    flask_app.register_blueprint(blueprint)
    with flask_app.app_context():
        db.session.execute(text("attach database ':memory:' as {0}".format(db_schema)))
        for ddl in [USER_DDL] + OTHER_DDL:
            db.session.execute(text(ddl.format(db_schema)))
        for i, name in [(1, 'ana'), (2, 'rui')]:
            db.session.add(User(id=i, username=name, email=name + '@example.org', name=name,
                                password=hash_password(PASSWORD), active=True, confirmed_at=utc_now()))
        db.session.commit()
        yield flask_app
        db.session.remove()


@pytest.fixture
def client(flask_app):
    return flask_app.test_client()


def login(client, username='ana', password=PASSWORD):
    return client.post('/api/authentication/authenticate',
                       json={'username': username, 'password': password}).get_json()['token']


def account(client, token):
    return client.get('/api/security/account', headers={'X-API-KEY': token})


def user(username='ana'):
    db.session.expire_all()
    return User.query.filter_by(username=username).one()


def old_token(monkeypatch, days):
    stamp = int(time.time()) - days * 86400
    with monkeypatch.context() as m:
        m.setattr(TimestampSigner, 'get_timestamp', lambda self: stamp)
        return tokens.auth_token(user())


def test_token_past_max_age_is_refused(client, monkeypatch):
    assert account(client, login(client)).status_code == 200
    assert account(client, old_token(monkeypatch, 149)).status_code == 200
    assert account(client, old_token(monkeypatch, 151)).status_code == 401


def test_password_change_needs_the_current_password(client):
    token = login(client)
    headers = {'X-API-KEY': token}

    missing = client.put('/api/security/update_password', json={'password': NEW_PASSWORD}, headers=headers)
    wrong = client.put('/api/security/update_password',
                       json={'password': NEW_PASSWORD, 'current_password': NEW_PASSWORD}, headers=headers)
    assert missing.status_code == 401
    assert wrong.status_code == 401
    assert login(client, password=PASSWORD)

    right = client.put('/api/security/update_password',
                       json={'password': NEW_PASSWORD, 'current_password': PASSWORD}, headers=headers)
    assert right.status_code == 200
    assert account(client, token).status_code == 401
    assert account(client, right.get_json()['data']['token']).status_code == 200


def test_auth_key_is_held_by_one_user(client):
    ana, rui = login(client), login(client, 'rui')
    key = 'shared-key'

    assert client.put('/api/security/account', json={'username': 'ana', 'email': 'ana@example.org',
                                                     'auth_token': key}, headers={'X-API-KEY': ana}).status_code == 200
    taken = client.put('/api/security/account', json={'username': 'rui', 'email': 'rui@example.org',
                                                      'auth_token': key}, headers={'X-API-KEY': rui})
    assert taken.status_code == 409
    assert user('rui').auth_token is None

    rui_row = user('rui')
    rui_row.auth_token = key
    db.session.commit()
    assert client.get('/api/authentication/authenticate', query_string={'authkey': key}).get_json() == {}
    assert app_security.get_user_from_auth_token(key) is None

    rui_row = user('rui')
    rui_row.auth_token = None
    db.session.commit()
    assert app_security.get_user_from_auth_token(key).username == 'ana'

    ana_row = user('ana')
    ana_row.auth_token_expire = utc_now() - timedelta(minutes=1)
    db.session.commit()
    assert app_security.get_user_from_auth_token(key) is None
