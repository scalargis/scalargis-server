import io
import zipfile

import pytest
from flask import Blueprint, Flask
from flask_restx import Api

from instance import settings
from app.modules.file import controllers as file_controllers
from app.api.v1.endpoints import ns_documents
from app.plugins.spatial_toolbox.api.v1.endpoints import ns


def export_body(secret):
    return {'format': 'csv', 'data': {'layers': [{
        'title': 'Layer', 'group': 'g', 'fields': [{'field': 'owner', 'alias': 'Owner'}],
        'results': [{'area': 1, 'length': 0, 'percent': 10, 'owner': secret}]}]}}


def csv_text(response):
    with zipfile.ZipFile(io.BytesIO(response.get_data())) as archive:
        return ''.join(archive.read(name).decode('utf-8') for name in archive.namelist())


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, 'APP_TMP_DIR', str(tmp_path))
    flask_app = Flask('intersect-export-test')
    flask_app.register_blueprint(file_controllers.mod)
    blueprint = Blueprint('spatial_toolbox_api', 'intersect-export-api', url_prefix='/spatial_toolbox/api')
    api = Api(blueprint)
    api.add_namespace(ns)
    flask_app.register_blueprint(blueprint)
    core_blueprint = Blueprint('api', 'intersect-export-core-api', url_prefix='/api')
    core_api = Api(core_blueprint)
    core_api.add_namespace(ns_documents)
    flask_app.register_blueprint(core_blueprint)
    return flask_app.test_client()


def test_csv_exports_get_their_own_file_and_leave_nothing_public(client, tmp_path):
    first = client.post('/spatial_toolbox/api/intersect/export', json=export_body('owner-a'), buffered=False)
    second = client.post('/spatial_toolbox/api/intersect/export', json=export_body('owner-b'), buffered=False)
    assert first.status_code == 200 and second.status_code == 200
    assert len(list(tmp_path.iterdir())) == 2
    assert 'owner-a' in csv_text(first)
    assert 'owner-b' in csv_text(second)
    first.close()
    second.close()

    assert list(tmp_path.iterdir()) == []
    for url in ['/file/intersect_layers.csvz', '/file/intersect_layers.zip',
                '/api/documents/temporary/intersect_layers.csvz']:
        assert client.get(url).status_code == 404
