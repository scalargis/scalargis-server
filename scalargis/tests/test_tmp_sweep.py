import os
import time
import uuid

import pytest
from flask import Flask

from app.database import db
from app.models.portal import UserDataLayer
from app.runner import tmp_sweep


@pytest.fixture
def app():
    flask_app = Flask('tmp-sweep-test')
    flask_app.config.update(SQLALCHEMY_DATABASE_URI='sqlite:///:memory:', SQLALCHEMY_TRACK_MODIFICATIONS=False,
                            SQLALCHEMY_ENGINE_OPTIONS={'execution_options': {'schema_translate_map': {'scalargis': None}}})
    db.init_app(flask_app)
    with flask_app.app_context():
        UserDataLayer.__table__.create(db.engine)
        yield flask_app
        db.session.remove()


def _file(folder, name, days_old):
    path = folder / name
    path.write_bytes(b'x' * 10)
    stamp = time.time() - days_old * 86400
    os.utime(path, (stamp, stamp))
    return path


def test_the_sweep_deletes_only_expired_files_of_its_kinds(app, tmp_path):
    saved, unsaved = uuid.uuid4().hex, uuid.uuid4().hex
    db.session.add(UserDataLayer(uuid=saved.upper(), title='kept in the database'))
    db.session.commit()
    old_print = _file(tmp_path, str(uuid.uuid4()) + '.pdf', 8)
    new_print = _file(tmp_path, str(uuid.uuid4()) + '.pdf', 6)
    old_intersect = _file(tmp_path, 'intersect_layers-{0}.pdf'.format(uuid.uuid4()), 2)
    old_upload = _file(tmp_path, str(uuid.uuid4()) + '.KML', 2)
    old_export = _file(tmp_path, uuid.uuid4().hex + '.zip', 2)
    new_upload = _file(tmp_path, str(uuid.uuid4()) + '.kml', 0)
    saved_files = [_file(tmp_path, saved + ext, 2) for ext in ('.geojson', '.metadata')]
    unsaved_files = [_file(tmp_path, unsaved + ext, 2) for ext in ('.geojson', '.metadata')]
    keep = [_file(tmp_path, '.gitignore', 400), _file(tmp_path, 'convert-apply.txt', 400),
            _file(tmp_path, 'report.pdf', 400)]
    (tmp_path / 'jobs').mkdir()
    (tmp_path / 'notifications').mkdir()
    old_dir_file = _file(tmp_path / 'notifications', str(uuid.uuid4()) + '.pdf', 400)

    removed = tmp_sweep.sweep_folder(str(tmp_path), tmp_sweep.tmp_hours())

    assert not any(p.exists() for p in [old_print, old_intersect, old_upload, old_export, *saved_files])
    assert all(p.exists() for p in [new_print, new_upload, *unsaved_files, *keep, old_dir_file])
    assert (tmp_path / 'jobs').is_dir()
    assert removed[tmp_sweep.KIND_PRINT][0] == 1
    assert removed[tmp_sweep.KIND_LAYER][0] == 2


def test_an_age_of_zero_turns_a_kind_off(app, tmp_path, monkeypatch):
    monkeypatch.setenv('RUNNER_TMP_PRINT_HOURS', '0')
    old_print = _file(tmp_path, str(uuid.uuid4()) + '.pdf', 400)
    tmp_sweep.sweep_folder(str(tmp_path), tmp_sweep.tmp_hours())
    assert old_print.exists()
