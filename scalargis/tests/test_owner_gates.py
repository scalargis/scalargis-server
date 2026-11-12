import json
import uuid

import pytest
from flask import Blueprint, Flask
from flask_restx import Api
from flask_security import Security, SQLAlchemyUserDatastore
from sqlalchemy import event, text

from app.database import db
from app.models.security import Role, User
from app.models.portal import ContactMessage, Print, PrintGroup, Viewer
from app.api.v1.endpoints import ns_portal
from app.utils import security as app_security, tokens
from app.utils.constants import ROLE_MANAGER


def geometry_functions(conn, record):
    for name in ('AsEWKB', 'GeomFromEWKT', 'AsText', 'Transform', 'ST_AsText', 'ST_Transform', 'ST_AsEWKB'):
        conn.create_function(name, -1, lambda *args: args[0] if args else None)


def create_tables():
    schemas = {t.schema for t in db.metadata.tables.values() if t.schema}
    for schema in schemas:
        db.session.execute(text("attach database ':memory:' as {0}".format(schema)))
    for table in db.metadata.tables.values():
        pk = [c.name for c in table.primary_key.columns]
        cols = []
        for c in table.columns:
            if pk == [c.name]:
                cols.append('"{0}" integer primary key'.format(c.name))
            else:
                cols.append('"{0}"'.format(c.name))
        name = '{0}."{1}"'.format(table.schema, table.name) if table.schema else '"{0}"'.format(table.name)
        db.session.execute(text('create table {0} ({1})'.format(name, ', '.join(cols))))
    db.session.commit()


@pytest.fixture
def flask_app(tmp_path):
    flask_app = Flask('owner-gates-test')
    flask_app.config.from_object('instance.default')
    flask_app.config.update(SQLALCHEMY_DATABASE_URI='sqlite:///:memory:', SQLALCHEMY_TRACK_MODIFICATIONS=False,
                            SQLALCHEMY_ENGINE_OPTIONS={}, SECURITY_PASSWORD_HASH='pbkdf2_sha512', TESTING=True,
                            EMAIL_NOTIFICATIONS_FOLDER=str(tmp_path))
    flask_app.config['SECURITY_USER_IDENTITY_ATTRIBUTES'] = app_security.identity_attributes(
        flask_app.config.get('SECURITY_USER_IDENTITY_ATTRIBUTES'))
    db.init_app(flask_app)
    datastore = SQLAlchemyUserDatastore(db, User, Role)
    Security(flask_app, datastore)
    blueprint = Blueprint('api', 'owner-gates-api', url_prefix='/api')
    api = Api(blueprint)
    api.add_namespace(ns_portal)
    flask_app.register_blueprint(blueprint)
    with flask_app.app_context():
        event.listen(db.engine, 'connect', geometry_functions)
        db.engine.dispose()
        create_tables()
        manager_role = datastore.create_role(name=ROLE_MANAGER)
        for name in ('owner', 'other', 'boss'):
            datastore.create_user(username=name, email=name + '@example.org', password='x-' + name, active=True,
                                  fs_uniquifier=uuid.uuid4().hex)
        db.session.commit()
        boss = User.query.filter_by(username='boss').one()
        datastore.add_role_to_user(boss, manager_role)
        owner = User.query.filter_by(username='owner').one()
        db.session.add(Viewer(id=1, name='v1', owner_id=owner.id))
        for i in (1, 2):
            db.session.add(Print(id=i, code='p%d' % i, name='p%d' % i, owner_id=owner.id))
            db.session.add(PrintGroup(id=i, code='g%d' % i, title='g%d' % i))
        message_uuid = uuid.uuid4().hex
        db.session.add(ContactMessage(id=1, viewer_id=1, message_uuid=message_uuid, name='n', email='e@example.org'))
        db.session.commit()
        (tmp_path / message_uuid).mkdir()
        (tmp_path / message_uuid / 'plan.txt').write_text('private plan')
        yield flask_app
        db.session.remove()


@pytest.fixture
def client(flask_app):
    return flask_app.test_client()


def key(username):
    user = User.query.filter_by(username=username).one()
    return {'X-API-KEY': tokens.auth_token(user)}


def remaining(model):
    db.session.expire_all()
    return sorted(r.id for r in model.query.all())


@pytest.mark.parametrize('url,model,refused,allowed', [('/api/portal/prints', Print, 'other', 'owner'),
                                                        ('/api/portal/prints/groups', PrintGroup, 'owner', 'boss')])
def test_bulk_delete_needs_the_owner(client, url, model, refused, allowed):
    query = {'filter': json.dumps({'id': [1, 2]})}
    assert client.delete(url, query_string=query, headers=key(refused)).status_code == 403
    assert remaining(model) == [1, 2]
    assert client.delete(url, query_string=query, headers=key(allowed)).status_code == 204
    assert remaining(model) == []


def test_owner_id_from_the_body_needs_a_manager(client):
    other_id = User.query.filter_by(username='other').one().id
    answer = client.put('/api/portal/prints/1', json={'owner_id': other_id}, headers=key('other'))
    assert answer.status_code == 403
    client.put('/api/portal/prints/1', json={'name': 'p1', 'owner_id': other_id}, headers=key('owner'))
    db.session.expire_all()
    assert db.session.get(Print, 1).owner_id != other_id


def test_attachment_needs_a_reader_of_the_message(client):
    url = '/api/portal/notifications/1/file/plan.txt'
    assert client.get(url).status_code == 404
    assert client.get(url, headers=key('other')).status_code == 404
    for name in ('owner', 'boss'):
        answer = client.get(url, headers=key(name))
        assert answer.status_code == 200
        assert answer.data == b'private plan'
