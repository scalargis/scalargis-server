import uuid

import pytest
from flask import Blueprint, Flask
from flask_restx import Api
from flask_security import Security, SQLAlchemyUserDatastore
from sqlalchemy import event

from app.database import db
from app.models.security import Role, User
from app.models.portal import SharedLayer
from app.api.v1.endpoints import ns_portal
from app.utils import security as app_security, tokens
from app.utils.constants import ROLE_MANAGER
from tests.test_owner_gates import create_tables, geometry_functions


LAYER = '{"type": "WMS", "title": "Base", "url": "https://example.org/wms", "layers": "base"}'


@pytest.fixture
def client(tmp_path):
    flask_app = Flask('shared-layer-test')
    flask_app.config.from_object('instance.default')
    flask_app.config.update(SQLALCHEMY_DATABASE_URI='sqlite:///:memory:', SQLALCHEMY_TRACK_MODIFICATIONS=False,
                            SQLALCHEMY_ENGINE_OPTIONS={}, SECURITY_PASSWORD_HASH='pbkdf2_sha512', TESTING=True,
                            EMAIL_NOTIFICATIONS_FOLDER=str(tmp_path))
    flask_app.config['SECURITY_USER_IDENTITY_ATTRIBUTES'] = app_security.identity_attributes(
        flask_app.config.get('SECURITY_USER_IDENTITY_ATTRIBUTES'))
    db.init_app(flask_app)
    datastore = SQLAlchemyUserDatastore(db, User, Role)
    Security(flask_app, datastore)
    blueprint = Blueprint('api', 'shared-layer-api', url_prefix='/api')
    api = Api(blueprint)
    api.add_namespace(ns_portal)
    flask_app.register_blueprint(blueprint)
    with flask_app.app_context():
        event.listen(db.engine, 'connect', geometry_functions)
        db.engine.dispose()
        create_tables()
        manager_role = datastore.create_role(name=ROLE_MANAGER)
        for name in ('plain', 'boss'):
            datastore.create_user(username=name, email=name + '@example.org', password='x-' + name, active=True,
                                  fs_uniquifier=uuid.uuid4().hex)
        db.session.commit()
        datastore.add_role_to_user(User.query.filter_by(username='boss').one(), manager_role)
        db.session.add(SharedLayer(id=1, code='base', title='Base', layer_json=LAYER))
        db.session.commit()
        yield flask_app.test_client()
        db.session.remove()


def key(username):
    return {'X-API-KEY': tokens.auth_token(User.query.filter_by(username=username).one())}


@pytest.mark.parametrize('username', ['plain', 'boss'])
def test_library_writes_need_an_admin(client, username):
    body = {'code': 'other', 'title': 'Other', 'layer_json': {'type': 'WMS', 'url': 'https://example.org/wms'}}
    assert client.post('/api/portal/shared-layers', json=body, headers=key(username)).status_code == 403
    assert client.put('/api/portal/shared-layers/1', json={'title': 'Changed'},
                      headers=key(username)).status_code == 403
    assert client.delete('/api/portal/shared-layers/1', headers=key(username)).status_code == 403

    rows = SharedLayer.query.all()
    assert [(r.code, r.title) for r in rows] == [('base', 'Base')]
