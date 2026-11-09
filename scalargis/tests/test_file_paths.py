import io
import os

import pytest
from flask import Blueprint, Flask
from flask_login import LoginManager
from flask_restx import Api
from sqlalchemy import text

from app.database import db
from app.models.files import db_schema
from app.modules.file import controllers as file_controllers
from app.api.v1.endpoints import ns_documents
from app.utils.files import bare_filename, contained_path

ESCAPES = ['..%2foutside.txt', '..%2f..%2foutside.txt', 'sub%2f..%2f..%2foutside.txt']


@pytest.fixture
def tree(tmp_path):
    docs = tmp_path / 'docs'
    (docs / 'sub').mkdir(parents=True)
    (tmp_path / 'locked').mkdir()
    (tmp_path / 'locked' / 'keep.txt').write_text('keep')
    (docs / 'inside.txt').write_text('inside')
    (tmp_path / 'outside.txt').write_text('outside')
    return tmp_path


@pytest.fixture
def client(tree):
    flask_app = Flask('file-paths-test')
    flask_app.config.update(SQLALCHEMY_DATABASE_URI='sqlite:///:memory:', SQLALCHEMY_TRACK_MODIFICATIONS=False,
                            SECRET_KEY='test')
    db.init_app(flask_app)
    login_manager = LoginManager(flask_app)
    login_manager.user_loader(lambda user_id: None)
    flask_app.register_blueprint(file_controllers.mod)
    blueprint = Blueprint('api', 'file-paths-api', url_prefix='/api')
    api = Api(blueprint)
    api.add_namespace(ns_documents)
    flask_app.register_blueprint(blueprint)
    with flask_app.app_context():
        db.session.execute(text("attach database ':memory:' as {0}".format(db_schema)))
        db.session.execute(text(
            "create table {0}.document_directory (id integer primary key, codigo text, path text, titulo text, "
            "descricao text, allow_upload boolean, upload_anonymous boolean, upload_overwrite boolean, "
            "upload_generate_filename boolean, allow_delete boolean, delete_anonymous boolean)".format(db_schema)))
        db.session.execute(text(
            "create table {0}.document_directory_rules (id integer primary key, doc_dir_id integer, "
            "viewer_id integer, filtro text, excluir text, excluir_dir text, descricao text)".format(db_schema)))
        db.session.execute(text(
            "insert into {0}.document_directory values (1, 'docs', :path, 't', null, 1, 1, 0, 0, 1, 1)".format(
                db_schema)), {'path': str(tree / 'docs')})
        db.session.execute(text(
            "insert into {0}.document_directory values (2, 'locked', :path, 't', null, 1, 0, 0, 0, 1, 0)".format(
                db_schema)), {'path': str(tree / 'locked')})
        db.session.execute(text(
            "insert into {0}.document_directory_rules values (1, 1, null, null, '.bak', null, null)".format(db_schema)))
        db.session.commit()
        yield flask_app.test_client()
        db.session.remove()


def test_contained_path_refuses_names_outside_the_base(tmp_path):
    base = str(tmp_path)
    assert os.path.normpath(contained_path(base, 'a', 'b.txt')) == os.path.join(base, 'a', 'b.txt')
    for name in ['../x', 'a/../../x', '/etc/passwd', str(tmp_path.parent / 'x'), '..']:
        assert contained_path(base, name) is None
    assert contained_path(None, 'x') is None


def test_bare_filename_keeps_only_the_last_part():
    assert bare_filename('../../etc/cron.d/x') == 'x'
    assert bare_filename('C:\\temp\\relatório ação.pdf') == 'relatório ação.pdf'
    for name in ['', '..', 'a/..', '.', None]:
        assert bare_filename(name) is None


@pytest.mark.parametrize('escape', ESCAPES)
def test_reads_stay_inside_the_folder(client, escape):
    for url in ['/file/docs/' + escape, '/api/documents/docs/' + escape]:
        response = client.get(url)
        assert response.status_code == 404
        assert b'outside' not in response.data
    assert client.get('/file/docs/inside.txt').data == b'inside'
    assert client.get('/api/documents/docs/inside.txt').data == b'inside'


def test_lists_stay_inside_the_folder(client):
    assert client.get('/api/documents/list/docs/..%2f').status_code == 404
    listing = client.get('/api/documents/list/docs')
    assert listing.status_code == 200
    assert 'inside.txt' in listing.get_data(as_text=True)


@pytest.mark.parametrize('escape', ESCAPES)
def test_deletes_stay_inside_the_folder(client, tree, escape):
    assert client.delete('/file/docs/' + escape).status_code == 404
    assert client.delete('/api/documents/docs/' + escape).status_code == 404
    assert (tree / 'outside.txt').exists()


@pytest.mark.parametrize('name', ['../escape.txt', '../../escape.txt', 'sub/../../escape.txt'])
def test_upload_names_stay_inside_the_folder(client, tree, name):
    client.post('/file/docs/upload', data={'files': (io.BytesIO(b'x'), name)}, content_type='multipart/form-data')
    client.post('/api/documents/docs/sub', data={'files': (io.BytesIO(b'x'), name)},
                content_type='multipart/form-data')
    assert not (tree / 'escape.txt').exists()
    assert not (tree / 'docs' / 'escape.txt').exists()
    assert not (tree.parent / 'escape.txt').exists()


def test_upload_paths_stay_inside_the_folder(client, tree):
    response = client.post('/file/docs/..%2fpathdir/upload', data={'files': (io.BytesIO(b'x'), 'p.txt')},
                           content_type='multipart/form-data')
    assert response.status_code == 404
    response = client.post('/api/documents/docs/..%2fpathdir', data={'files': (io.BytesIO(b'x'), 'p.txt')},
                           content_type='multipart/form-data')
    assert response.status_code == 404
    assert not (tree / 'pathdir').exists()
    client.post('/file/docs/upload', data={'files': (io.BytesIO(b'ok'), 'normal.txt')},
                content_type='multipart/form-data')
    assert (tree / 'docs' / 'normal.txt').read_bytes() == b'ok'


def test_upload_and_delete_need_a_user_when_the_folder_is_not_anonymous(client, tree):
    for url in ['/file/locked/upload', '/api/documents/locked/sub']:
        response = client.post(url, data={'files': (io.BytesIO(b'x'), 'new.txt')},
                               content_type='multipart/form-data')
        assert response.status_code == 401
        response = client.post(url, data={'files': (io.BytesIO(b'x'), 'new.txt')},
                               content_type='multipart/form-data', headers={'X-API-KEY': 'not-a-token'})
        assert response.status_code == 401
    assert not (tree / 'locked' / 'new.txt').exists()
    assert not (tree / 'locked' / 'sub').exists()
    for url in ['/file/locked/keep.txt', '/api/documents/locked/keep.txt']:
        assert client.delete(url).status_code == 401
        assert client.delete(url, headers={'X-API-KEY': 'not-a-token'}).status_code == 401
    assert (tree / 'locked' / 'keep.txt').read_text() == 'keep'
