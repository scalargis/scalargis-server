import uuid

import pytest
from flask import Blueprint, Flask
from flask_restx import Api
from flask_security import Security, SQLAlchemyUserDatastore
from flask_security.utils import verify_password
from ldap3.core.exceptions import LDAPSocketOpenError

from app.database import db
from app.models.security import Role, User
from app.api.v1.endpoints import ns_authentication
import app.api.v1.endpoints.security
from app.utils import security as app_security, tokens
from app.utils.tests.test_ldap_auth import PASSWORDS, SEARCH_BIND, USER_DN, ldap
from tests.test_owner_gates import create_tables


@pytest.fixture
def client(tmp_path, monkeypatch, ldap):
    flask_app = Flask('ldap-login-test')
    flask_app.config.from_object('instance.default')
    flask_app.config.update(SQLALCHEMY_DATABASE_URI='sqlite:///:memory:', SQLALCHEMY_TRACK_MODIFICATIONS=False,
                            SQLALCHEMY_ENGINE_OPTIONS={}, SECURITY_PASSWORD_HASH='pbkdf2_sha512', TESTING=True,
                            SCALARGIS_LDAP_AUTHENTICATION=True, EMAIL_NOTIFICATIONS_FOLDER=str(tmp_path))
    flask_app.config['SECURITY_USER_IDENTITY_ATTRIBUTES'] = app_security.identity_attributes(
        flask_app.config.get('SECURITY_USER_IDENTITY_ATTRIBUTES'))
    db.init_app(flask_app)
    datastore = SQLAlchemyUserDatastore(db, User, Role)
    Security(flask_app, datastore)
    blueprint = Blueprint('api', 'ldap-login-api', url_prefix='/api')
    api = Api(blueprint)
    api.add_namespace(ns_authentication)
    flask_app.register_blueprint(blueprint)
    manager = app_security.LDAPLoginManager()
    manager.init_config(SEARCH_BIND)
    monkeypatch.setattr(app_security, 'ldap_managers', [manager])
    monkeypatch.setitem(PASSWORDS, USER_DN, 'secret')
    with flask_app.app_context():
        create_tables()
        db.session.add(Role(id=1, name='LDAP'))
        datastore.create_user(username='jdoe', email='jdoe@example.org', password='local-pw', active=True,
                              fs_uniquifier=uuid.uuid4().hex)
        db.session.commit()
        yield flask_app.test_client()
        db.session.remove()


def login(client, password):
    return client.post('/api/authentication/authenticate', json={'username': 'jdoe', 'password': password})


def local_hash_is(password):
    db.session.expire_all()
    return verify_password(password, User.query.filter_by(username='jdoe').one().password)


def mark_as_directory_account():
    user = User.query.filter_by(username='jdoe').one()
    user.roles.append(db.session.get(Role, 1))
    db.session.commit()


def test_directory_user_does_not_take_a_local_only_account(client, ldap):
    assert login(client, 'secret').status_code == 401
    assert ldap.binds == []
    assert local_hash_is('local-pw')
    assert login(client, 'local-pw').status_code == 200


def test_directory_account_follows_the_directory(client, ldap, monkeypatch):
    mark_as_directory_account()
    assert login(client, 'local-pw').status_code == 401
    token = login(client, 'secret').json['token']
    assert local_hash_is('secret')
    assert login(client, 'secret').status_code == 200
    assert tokens.user_from_auth_token(token) is not None

    monkeypatch.setitem(PASSWORDS, USER_DN, 'new-secret')
    assert login(client, 'secret').status_code == 401
    assert login(client, 'new-secret').status_code == 200

    monkeypatch.delitem(PASSWORDS, USER_DN)
    assert login(client, 'new-secret').status_code == 401

    def unreachable(*args, **kwargs):
        raise LDAPSocketOpenError('unreachable')

    monkeypatch.setattr(app_security, 'Connection', unreachable)
    assert login(client, 'new-secret').status_code == 200
    assert login(client, 'secret').status_code == 401
