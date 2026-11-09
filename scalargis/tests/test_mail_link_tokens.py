import os
import re
from datetime import timedelta

import pytest
from flask import Blueprint, Flask
from flask_restx import Api
from flask_security import Security, SQLAlchemyUserDatastore
from sqlalchemy import text

import app as app_package
from app.database import db
from app.models.security import Role, User, db_schema
from app.api.v1.endpoints import ns_authentication, ns_security
from app.api.v1.endpoints import security as _security_routes
from app.api.v1.portal.dao import security as dao_security
from app.utils import security as app_security

PASSWORD = 'Old-Passw0rd-1'
NEW_PASSWORD = 'New-Passw0rd-2'
OTHER_PASSWORD = 'Other-Passw0rd-3'

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
def mails(monkeypatch):
    sent = []
    monkeypatch.setattr(dao_security, 'send_mail', lambda app, to, subject, html: sent.append(html))
    return sent


@pytest.fixture
def flask_app(mails):
    flask_app = Flask('mail-link-tokens-test', template_folder=os.path.join(app_package.base_path, 'templates'))
    flask_app.config.from_object('instance.default')
    flask_app.config.update(SQLALCHEMY_DATABASE_URI='sqlite:///:memory:', SQLALCHEMY_TRACK_MODIFICATIONS=False,
                            SQLALCHEMY_ENGINE_OPTIONS={},
                            SECURITY_PASSWORD_HASH='pbkdf2_sha512', TESTING=True)
    flask_app.config['SECURITY_USER_IDENTITY_ATTRIBUTES'] = app_security.identity_attributes(
        flask_app.config.get('SECURITY_USER_IDENTITY_ATTRIBUTES'))
    db.init_app(flask_app)
    Security(flask_app, SQLAlchemyUserDatastore(db, User, Role))
    blueprint = Blueprint('api', 'mail-link-tokens-api', url_prefix='/api')
    api = Api(blueprint)
    api.add_namespace(ns_authentication)
    api.add_namespace(ns_security)
    flask_app.register_blueprint(blueprint)
    with flask_app.app_context():
        db.session.execute(text("attach database ':memory:' as {0}".format(db_schema)))
        for ddl in [USER_DDL] + OTHER_DDL:
            db.session.execute(text(ddl.format(db_schema)))
        db.session.commit()
        yield flask_app
        db.session.remove()


@pytest.fixture
def client(flask_app):
    return flask_app.test_client()


def last_token(mails):
    return re.search(r'token=([^&"\s]+)', mails[-1]).group(1)


def register(client, mails, username='ana', email='ana@example.org'):
    answer = client.post('/api/security/register_user',
                         json={'name': username, 'username': username, 'email': email, 'password': PASSWORD})
    assert answer.status_code == 200
    return answer, last_token(mails)


def confirm(client, token):
    return client.post('/api/security/registration/confirmation', json={'token': token})


def request_reset(client, mails, username='ana'):
    count = len(mails)
    client.post('/api/security/reset_password', json={'username': username})
    return last_token(mails) if len(mails) > count else None


def set_password(client, token, password):
    return client.post('/api/security/set_password', json={'token': token, 'password': password})


def logged_in(client, password, username='ana'):
    body = client.post('/api/authentication/authenticate',
                       json={'username': username, 'password': password}).get_json()
    return isinstance(body, dict) and body.get('authenticated') is True


def user(username='ana'):
    db.session.expire_all()
    return User.query.filter_by(username=username).one()


def test_activation_answers_no_token_and_works_once(client, mails):
    answer, token = register(client, mails)
    assert answer.get_json()['confirm_within_hours'] == 24

    first = confirm(client, token)
    assert first.status_code == 200
    body = first.get_json()
    assert body['confirmed'] is True
    assert 'token' not in body and 'auth_token' not in body and 'authenticated' not in body
    assert user().active and user().confirmed_at is not None

    again = confirm(client, token)
    assert again.status_code == 401
    assert 'token' not in again.get_json()


def test_old_activation_link_of_a_confirmed_account_gives_no_login(client, mails):
    _, old = register(client, mails)
    assert register(client, mails)[1] != old
    assert confirm(client, old).status_code == 401
    assert confirm(client, last_token(mails)).status_code == 200

    reset = request_reset(client, mails)
    for token in (old, reset):
        answer = confirm(client, token)
        assert answer.status_code == 401
        assert 'token' not in answer.get_json()


def test_activation_link_expires(client, mails, flask_app):
    _, token = register(client, mails)
    flask_app.config['SECURITY_CONFIRM_EMAIL_WITHIN'] = timedelta(seconds=-1)
    answer = confirm(client, token)
    assert answer.status_code == 401
    assert answer.get_json()['message'] == 'registration_confirmation_expired'
    assert not user().active


def test_activation_takes_no_get(client, mails):
    _, token = register(client, mails)
    assert client.get('/api/security/registration/confirmation?token=' + token).status_code == 405
    assert not user().active


def test_reset_link_works_once_and_only_the_newest(client, mails):
    _, token = register(client, mails)
    confirm(client, token)

    first = request_reset(client, mails)
    second = request_reset(client, mails)
    assert set_password(client, first, OTHER_PASSWORD).status_code == 401

    done = set_password(client, second, NEW_PASSWORD)
    assert done.status_code == 200 and done.get_json()['authenticated'] is True

    reused = set_password(client, second, OTHER_PASSWORD)
    assert reused.status_code == 401
    assert 'token' not in reused.get_json()
    assert client.post('/api/security/reset_password_validation', json={'token': second}).status_code == 401
    assert logged_in(client, NEW_PASSWORD)
    assert not logged_in(client, OTHER_PASSWORD)


def test_activation_link_does_not_set_a_password(client, mails):
    _, token = register(client, mails)
    assert set_password(client, token, OTHER_PASSWORD).status_code == 401
    assert client.post('/api/security/reset_password_validation', json={'token': token}).status_code == 401
    assert not user().active
    assert confirm(client, token).status_code == 200
    assert logged_in(client, PASSWORD)


def test_disabled_account_gets_no_reset(client, mails):
    _, token = register(client, mails)
    confirm(client, token)
    reset = request_reset(client, mails)
    account = user()
    account.active = False
    db.session.commit()

    assert request_reset(client, mails) is None
    answer = set_password(client, reset, OTHER_PASSWORD)
    assert answer.status_code == 401
    assert 'token' not in answer.get_json()
