import uuid

import pytest
from flask import Blueprint, Flask
from flask_restx import Api
from flask_security import Security, SQLAlchemyUserDatastore
from sqlalchemy import event

from app.database import db
from app.models.security import Role, User
from app.models.portal import Viewer
from app.api.v1.endpoints import ns_app, ns_portal
from app.utils import security as app_security, tokens
from app.utils.constants import ROLE_ANONYMOUS, ROLE_AUTHENTICATED
from tests.test_owner_gates import create_tables, geometry_functions

CONFIG = {'components': [], 'layers': [], 'center': [0, 0], 'zoom': 1}


@pytest.fixture
def client(tmp_path):
    flask_app = Flask('viewer-slug-test')
    flask_app.config.from_object('instance.default')
    flask_app.config.update(SQLALCHEMY_DATABASE_URI='sqlite:///:memory:', SQLALCHEMY_TRACK_MODIFICATIONS=False,
                            SQLALCHEMY_ENGINE_OPTIONS={}, SECURITY_PASSWORD_HASH='pbkdf2_sha512', TESTING=True,
                            EMAIL_NOTIFICATIONS_FOLDER=str(tmp_path))
    flask_app.config['SECURITY_USER_IDENTITY_ATTRIBUTES'] = app_security.identity_attributes(
        flask_app.config.get('SECURITY_USER_IDENTITY_ATTRIBUTES'))
    db.init_app(flask_app)
    datastore = SQLAlchemyUserDatastore(db, User, Role)
    Security(flask_app, datastore)
    blueprint = Blueprint('api', 'viewer-slug-api', url_prefix='/api')
    api = Api(blueprint)
    api.add_namespace(ns_app)
    api.add_namespace(ns_portal)
    flask_app.register_blueprint(blueprint)
    with flask_app.app_context():
        event.listen(db.engine, 'connect', geometry_functions)
        db.engine.dispose()
        create_tables()
        anonymous = datastore.create_role(name=ROLE_ANONYMOUS)
        datastore.create_role(name=ROLE_AUTHENTICATED)
        datastore.create_user(username='owner', email='owner@example.org', password='x-owner', active=True,
                              fs_uniquifier=uuid.uuid4().hex)
        viewer = Viewer(id=1, name='mapa', slug='mapa', uuid=uuid.uuid4().hex, title='Mapa', is_active=True,
                        config_json='{"components": [], "layers": []}')
        viewer.roles.append(anonymous)
        db.session.add(viewer)
        db.session.commit()
        yield flask_app.test_client()
        db.session.remove()


def key():
    return {'X-API-KEY': tokens.auth_token(User.query.filter_by(username='owner').one())}


def test_anonymous_post_with_an_existing_slug_keeps_the_viewer(client):
    client.post('/api/app/viewer', json={'title': 'x', 'name': 'x', 'slug': 'mapa', 'config_json': CONFIG})
    assert Viewer.query.filter(Viewer.slug == 'mapa').count() == 1
    answer = client.get('/api/app/viewer/mapa')
    assert answer.status_code == 200
    assert answer.get_json()['id'] == 1


def test_duplicate_slug_in_the_database_takes_the_lowest_id(client):
    db.session.add(Viewer(id=2, name='copia', slug='MAPA', uuid=uuid.uuid4().hex, is_active=True,
                          config_json='{}'))
    db.session.commit()
    answer = client.get('/api/app/viewer/mapa')
    assert answer.status_code == 200
    assert answer.get_json()['id'] == 1


@pytest.mark.parametrize('slug', ['mapa', 'MAPA', '42'])
def test_logged_in_writes_refuse_a_taken_or_digit_slug(client, slug):
    body = {'title': 'x', 'name': 'x', 'slug': slug, 'config_json': CONFIG}
    assert client.post('/api/app/viewer', json=body, headers=key()).status_code == 409
    assert client.post('/api/portal/viewers', json=body, headers=key()).status_code == 409
    assert Viewer.query.count() == 1
