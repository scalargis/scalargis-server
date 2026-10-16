import uuid
from types import SimpleNamespace

import pytest
from flask import Flask
from werkzeug.exceptions import HTTPException

from app.database import db
from app.database.schema import create_runner_tables
from app.models.runner import Job
from app.runner import runner as core
from app.utils import utc_now


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.setattr(core, 'job_files_root', lambda: str(tmp_path / 'jobs'))
    monkeypatch.setattr(core, '_job_types', {})
    flask_app = Flask('runner-test')
    flask_app.config.update(SQLALCHEMY_DATABASE_URI='sqlite:///:memory:', SQLALCHEMY_TRACK_MODIFICATIONS=False,
                            SQLALCHEMY_ENGINE_OPTIONS={'execution_options': {'schema_translate_map': {'scalargis': None}}},
                            RESTX_MASK_HEADER='X-Fields', RESTX_MASK_SWAGGER=False)
    db.init_app(flask_app)
    with flask_app.app_context():
        create_runner_tables()
        yield flask_app
        db.session.remove()


def _user(user_id, role):
    return SimpleNamespace(id=user_id, roles=[SimpleNamespace(name=role)])


def test_status_is_readable_by_its_owner_and_an_admin(app, monkeypatch):
    from app.api.v1.endpoints import jobs
    state = {'user': None}
    monkeypatch.setattr(jobs.dao_job, 'get_user', lambda request: state['user'])
    monkeypatch.setattr(jobs.dao_job, 'current_user', SimpleNamespace(is_authenticated=False))
    job = Job(id=uuid.uuid4(), type='t', payload={}, status=core.STATUS_QUEUED, attempts=0, created_at=utc_now(),
              created_by=5)
    db.session.add(job)
    db.session.commit()

    def status():
        try:
            response = jobs.JobStatus().get(str(job.id))
        except HTTPException as err:
            return err.code
        return response[1] if isinstance(response, tuple) else response.status_code

    with app.test_request_context('/'):
        assert status() == 404
        state['user'] = _user(6, 'Authenticated')
        assert status() == 404
        state['user'] = _user(5, 'Authenticated')
        assert status() == 200
        state['user'] = _user(1, 'Admin')
        assert status() == 200
