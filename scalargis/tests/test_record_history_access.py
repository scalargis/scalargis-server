import uuid

import pytest
from flask import Blueprint, Flask
from flask_restx import Api
from flask_security import Security, SQLAlchemyUserDatastore
from sqlalchemy import event

from app.database import db
from app.models.security import Role, User
from app.models.portal import Viewer
from app.api.v1.endpoints import ns_portal
from app.utils import security as app_security, tokens
from app.utils.constants import ROLE_AUTHENTICATED
from tests.test_owner_gates import create_tables, geometry_functions


@pytest.fixture
def client(tmp_path):
    flask_app = Flask('record-history-test')
    flask_app.config.from_object('instance.default')
    flask_app.config.update(SQLALCHEMY_DATABASE_URI='sqlite:///:memory:', SQLALCHEMY_TRACK_MODIFICATIONS=False,
                            SQLALCHEMY_ENGINE_OPTIONS={}, SECURITY_PASSWORD_HASH='pbkdf2_sha512', TESTING=True,
                            EMAIL_NOTIFICATIONS_FOLDER=str(tmp_path))
    flask_app.config['SECURITY_USER_IDENTITY_ATTRIBUTES'] = app_security.identity_attributes(
        flask_app.config.get('SECURITY_USER_IDENTITY_ATTRIBUTES'))
    db.init_app(flask_app)
    datastore = SQLAlchemyUserDatastore(db, User, Role)
    Security(flask_app, datastore)
    blueprint = Blueprint('api', 'record-history-api', url_prefix='/api')
    api = Api(blueprint)
    api.add_namespace(ns_portal)
    flask_app.register_blueprint(blueprint)
    with flask_app.app_context():
        event.listen(db.engine, 'connect', geometry_functions)
        db.engine.dispose()
        create_tables()
        datastore.create_role(name=ROLE_AUTHENTICATED)
        for name in ('owner', 'other'):
            datastore.create_user(username=name, email=name + '@example.org', password='x-' + name, active=True,
                                  fs_uniquifier=uuid.uuid4().hex)
        db.session.commit()
        owner = User.query.filter_by(username='owner').one()
        db.session.add(Viewer(id=1, name='v1', title='Old title', owner_id=owner.id, config_json='{}'))
        db.session.commit()
        yield flask_app.test_client()
        db.session.remove()


def key(username):
    return {'X-API-KEY': tokens.auth_token(User.query.filter_by(username=username).one())}


def test_history_routes_need_an_editor_of_the_viewer(client):
    assert client.put('/api/portal/viewers/1', json={'title': 'New title'}, headers=key('owner')).status_code == 200
    rows = client.get('/api/portal/viewers/1/history', headers=key('owner'))
    assert rows.status_code == 200
    hid = rows.get_json()[0]['id']
    one = client.get('/api/portal/viewers/1/history/%d' % hid, headers=key('owner'))
    assert one.status_code == 200
    assert one.get_json()['snapshot']['title'] == 'Old title'

    assert client.get('/api/portal/viewers/1/history', headers=key('other')).status_code == 403
    assert client.get('/api/portal/viewers/1/history/%d' % hid, headers=key('other')).status_code == 403
