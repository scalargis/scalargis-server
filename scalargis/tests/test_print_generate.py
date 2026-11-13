import json
import uuid

import pytest
from flask import Blueprint, Flask
from flask_restx import Api
from flask_security import Security, SQLAlchemyUserDatastore
from sqlalchemy import event

from app.database import db
from app.models.security import Role, User
from app.models.portal import Viewer, Print, PrintOutput, ViewerPrint
from app.models.runner import Job
from app.api.v1.endpoints import ns_app
from app.modules.print import jobs as print_jobs
from app.utils import security as app_security, tokens
from app.utils.constants import ROLE_ANONYMOUS, ROLE_AUTHENTICATED
from tests.test_owner_gates import create_tables, geometry_functions

REN = {'id': 'ren', 'type': 'CCDRAlg', 'target': 'mainmenu', 'config_json': {'print_code': 'ren_one_page'}}
FORM = {'scale': '1000', 'viewerId': '1', 'srid': '3763', 'layout': 'A4|Retrato', 'geomWKT': 'POINT (0 0)'}


@pytest.fixture
def client(tmp_path):
    flask_app = Flask('print-generate-test')
    flask_app.config.from_object('instance.default')
    flask_app.config.update(SQLALCHEMY_DATABASE_URI='sqlite:///:memory:', SQLALCHEMY_TRACK_MODIFICATIONS=False,
                            SQLALCHEMY_ENGINE_OPTIONS={}, SECURITY_PASSWORD_HASH='pbkdf2_sha512', TESTING=True,
                            APP_TMP_DIR=str(tmp_path))
    flask_app.config['SECURITY_USER_IDENTITY_ATTRIBUTES'] = app_security.identity_attributes(
        flask_app.config.get('SECURITY_USER_IDENTITY_ATTRIBUTES'))
    db.init_app(flask_app)
    datastore = SQLAlchemyUserDatastore(db, User, Role)
    Security(flask_app, datastore)
    blueprint = Blueprint('api', 'print-generate-api', url_prefix='/api')
    api = Api(blueprint)
    api.add_namespace(ns_app)
    flask_app.register_blueprint(blueprint)
    print_jobs.register()
    with flask_app.app_context():
        event.listen(db.engine, 'connect', geometry_functions)
        db.engine.dispose()
        create_tables()
        anonymous = datastore.create_role(name=ROLE_ANONYMOUS)
        datastore.create_role(name=ROLE_AUTHENTICATED)
        tecnico = datastore.create_role(name='tecnico')
        datastore.create_user(username='someone', email='someone@example.org', password='x-someone', active=True,
                              fs_uniquifier=uuid.uuid4().hex)
        viewer = Viewer(id=1, name='mapa', slug='mapa', uuid=uuid.uuid4().hex, title='Mapa', is_active=True,
                        config_json=json.dumps({'components': [REN], 'layers': []}))
        viewer.roles.append(anonymous)
        restricted = Print(id=1, code='restrita', name='restrita', is_active=True)
        restricted.roles.append(tecnico)
        db.session.add_all([viewer, restricted, Print(id=2, code='solta', name='solta', is_active=True),
                            Print(id=3, code='ren_one_page', name='ren_one_page', is_active=True),
                            Print(id=4, code='inativa', name='inativa', is_active=False)])
        db.session.flush()
        db.session.add_all([ViewerPrint(viewer_id=1, print_id=1, order=1), ViewerPrint(viewer_id=1, print_id=4, order=2)])
        db.session.commit()
        yield flask_app.test_client()
        db.session.remove()


def key():
    return {'X-API-KEY': tokens.auth_token(User.query.filter_by(username='someone').one())}


@pytest.mark.parametrize('route', ['generate', 'generate/job'])
def test_a_restricted_print_is_refused_and_takes_no_number(client, route):
    url = '/api/app/viewer/1/print/restrita/{0}'.format(route)
    assert client.post(url, data=FORM).status_code == 401
    assert client.post(url, data=FORM, headers=key()).status_code == 403
    assert PrintOutput.query.count() == 0
    assert Job.query.count() == 0


@pytest.mark.parametrize('code', ['solta', 'inativa'])
def test_a_print_that_the_viewer_does_not_reach_is_refused(client, code):
    assert client.post('/api/app/viewer/1/print/{0}/generate'.format(code), data=FORM).status_code == 404
    assert client.post('/api/app/viewer/1/print/{0}/generate/job'.format(code), data=FORM).status_code == 404
    assert PrintOutput.query.count() == 0
    assert Job.query.count() == 0


def test_a_print_that_a_component_names_still_issues(client):
    from app.api.v1.portal.dao.app import check_viewer_print
    assert check_viewer_print(1, 'ren_one_page', None) == (200, None)
    assert check_viewer_print(1, 'solta', None)[0] == 404
