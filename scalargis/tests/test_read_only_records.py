import json
import uuid

import pytest
from flask import Blueprint, Flask
from flask_restx import Api
from flask_security import Security, SQLAlchemyUserDatastore
from sqlalchemy import event

from app.database import db
from app.models.security import Group, Role, User
from app.models.portal import CoordinateSystems, SiteSettings, ViewerContent
from app.api.v1.endpoints import ns_app, ns_portal, ns_security
import app.api.v1.endpoints.app
import app.api.v1.endpoints.generic
import app.api.v1.endpoints.security
import app.api.v1.endpoints.settings
from app.utils import security as app_security, tokens
from app.utils.constants import ROLE_ADMIN, ROLE_ANONYMOUS, ROLE_AUTHENTICATED, ROLE_MANAGER
from tests.test_owner_gates import create_tables, geometry_functions


@pytest.fixture
def client(tmp_path):
    flask_app = Flask('read-only-test')
    flask_app.config.from_object('instance.default')
    flask_app.config.update(SQLALCHEMY_DATABASE_URI='sqlite:///:memory:', SQLALCHEMY_TRACK_MODIFICATIONS=False,
                            SQLALCHEMY_ENGINE_OPTIONS={}, SECURITY_PASSWORD_HASH='pbkdf2_sha512', TESTING=True,
                            EMAIL_NOTIFICATIONS_FOLDER=str(tmp_path))
    flask_app.config['SECURITY_USER_IDENTITY_ATTRIBUTES'] = app_security.identity_attributes(
        flask_app.config.get('SECURITY_USER_IDENTITY_ATTRIBUTES'))
    db.init_app(flask_app)
    datastore = SQLAlchemyUserDatastore(db, User, Role)
    Security(flask_app, datastore)
    blueprint = Blueprint('api', 'read-only-api', url_prefix='/api')
    api = Api(blueprint)
    api.add_namespace(ns_app)
    api.add_namespace(ns_portal)
    api.add_namespace(ns_security)
    flask_app.register_blueprint(blueprint)
    with flask_app.app_context():
        event.listen(db.engine, 'connect', geometry_functions)
        db.engine.dispose()
        create_tables()
        db.session.add(Role(id=1, name=ROLE_ADMIN, read_only=True))
        manager = Role(id=2, name=ROLE_MANAGER, read_only=True)
        db.session.add_all([manager, Role(id=3, name=ROLE_ANONYMOUS, read_only=True),
                            Role(id=4, name=ROLE_AUTHENTICATED, read_only=True), Role(id=5, name='Editor')])
        db.session.add_all([Group(id=1, name='sistema', read_only=True), Group(id=2, name='equipa')])
        db.session.add_all([CoordinateSystems(id=1, code='EPSG:3763', srid=3763, read_only=True),
                            CoordinateSystems(id=2, code='EPSG:20790', srid=20790)])
        db.session.add(SiteSettings(id=1, code='SITE', setting_value='x', read_only=True))
        db.session.add_all([ViewerContent(id=1, name='on', content='{"a": 1}', active=True),
                            ViewerContent(id=2, name='off', content='{"a": 2}', active=False)])
        user = datastore.create_user(username='gestor', email='gestor@example.org', password='x-gestor',
                                     active=True, fs_uniquifier=uuid.uuid4().hex)
        user.roles.append(manager)
        db.session.commit()
        yield flask_app.test_client()
        db.session.remove()


def key():
    return {'X-API-KEY': tokens.auth_token(User.query.filter_by(username='gestor').one())}


def ids(*values):
    return {'filter': json.dumps({'id': list(values)})}


def test_read_only_role_cannot_be_renamed_or_deleted(client):
    assert client.put('/api/security/roles/1', json={'name': 'Outro'}, headers=key()).status_code == 403
    assert client.delete('/api/security/roles/1', headers=key()).status_code == 403
    assert client.delete('/api/security/roles', query_string=ids(5, 1), headers=key()).status_code == 403
    db.session.expire_all()
    assert {r.name for r in Role.query.all()} == {ROLE_ADMIN, ROLE_MANAGER, ROLE_ANONYMOUS, ROLE_AUTHENTICATED,
                                                  'Editor'}
    assert client.delete('/api/security/roles/5', headers=key()).status_code == 204


def test_read_only_group_crs_and_setting_cannot_be_changed(client):
    assert client.put('/api/security/groups/1', json={'name': 'x'}, headers=key()).status_code == 403
    assert client.delete('/api/security/groups', query_string=ids(2, 1), headers=key()).status_code == 403
    assert client.put('/api/portal/lists/coordinate_systems/1', json={'code': 'x'}, headers=key()).status_code == 403
    assert client.delete('/api/portal/lists/coordinate_systems/1', headers=key()).status_code == 403
    assert client.delete('/api/portal/settings/site/1', headers=key()).status_code == 403
    db.session.expire_all()
    assert Group.query.count() == 2
    assert db.session.get(CoordinateSystems, 1).code == 'EPSG:3763'
    assert db.session.get(SiteSettings, 1).setting_value == 'x'


def test_api_cannot_set_read_only_on_a_coordinate_system(client):
    client.put('/api/portal/lists/coordinate_systems/2', json={'code': 'EPSG:20790', 'read_only': True},
               headers=key())
    db.session.expire_all()
    assert not db.session.get(CoordinateSystems, 2).read_only
    assert client.delete('/api/portal/lists/coordinate_systems/2', headers=key()).status_code == 204


def test_inactive_content_answers_404(client):
    assert client.get('/api/app/content/1').status_code == 200
    assert client.get('/api/app/content/2').status_code == 404
