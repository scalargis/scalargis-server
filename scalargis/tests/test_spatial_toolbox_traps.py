"""The intersect check runs before the query, an unsaved upload leaves no tmp file, and an upload keeps its metadata."""
import io
import json

import pytest
from flask import Flask
from werkzeug.datastructures import FileStorage

from app.api.v1.portal.dao import viewer as viewer_dao
from app.api.v1.portal.dao import app as app_dao
from app.plugins.spatial_toolbox.api.v1.endpoints import analysis as analysis_endpoint
from app.plugins.spatial_toolbox.utils import vector

GEOJSON = {
    'type': 'FeatureCollection',
    'features': [{'type': 'Feature', 'properties': {'name': 'a'},
                  'geometry': {'type': 'Point', 'coordinates': [-8.0, 39.0]}}],
}


@pytest.fixture
def flask_app():
    return Flask('spatial-toolbox-test')


@pytest.fixture
def no_query(monkeypatch):
    calls = []
    monkeypatch.setattr(analysis_endpoint, 'get_intersect_results', lambda **kwargs: calls.append(kwargs))
    return calls


@pytest.mark.parametrize('query, field', [
    ('code=config_intersect', 'geom_wkt'),
    ('geom_wkt=POINT(-8 39)', 'code'),
])
def test_intersect_get_checks_the_parameters_first(flask_app, no_query, query, field):
    with flask_app.test_request_context('/intersect?' + query):
        body, status = analysis_endpoint.Intersect().get()
    assert status == 400
    assert body['Message'] == "Parameter '{0}' is required".format(field)
    assert no_query == []


def test_upload_with_no_persist_leaves_no_tmp_file(tmp_path, monkeypatch):
    monkeypatch.setattr(vector.settings, 'APP_TMP_DIR', str(tmp_path), raising=False)
    upload = FileStorage(io.BytesIO(json.dumps(GEOJSON).encode('utf-8')), filename='points.geojson')

    result = vector.convert_to_geojson_create_layer(upload, persist=False)

    assert result['metadata']['filename'] == 'points.geojson'
    assert result['data']['features'][0]['properties'] == {'name': 'a'}
    assert list(tmp_path.iterdir()) == []


class _Session:
    def __init__(self):
        self.added = []

    def add(self, record):
        self.added.append(record)

    def commit(self):
        pass

    def refresh(self, record):
        pass


class _Db:
    def __init__(self):
        self.session = _Session()


def test_first_read_of_an_upload_stores_its_metadata(flask_app, tmp_path, monkeypatch):
    metadata = {'filename': 'points.geojson', 'driver': 'GeoJSON'}
    (tmp_path / '123.geojson').write_text(json.dumps(GEOJSON), encoding='utf-8')
    (tmp_path / '123.metadata').write_text(json.dumps(metadata), encoding='utf-8')
    db = _Db()
    monkeypatch.setattr(app_dao.settings, 'APP_TMP_DIR', str(tmp_path), raising=False)
    monkeypatch.setattr(app_dao, 'get_user', lambda request: None)
    monkeypatch.setattr(app_dao, 'get_record_by_id', lambda model, record_id: None)
    monkeypatch.setattr(app_dao, 'UserDataLayer', type('UserDataLayer', (), {}))
    monkeypatch.setattr(app_dao, 'db', db)

    with flask_app.test_request_context('/api/app/data/layer/123'):
        data, status = app_dao.get_data_layer('123')

    assert status == 200
    assert data == GEOJSON
    record = db.session.added[0]
    assert json.loads(record.metadata_geojson) == metadata
    assert json.loads(record.data_geojson) == GEOJSON
