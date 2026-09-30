"""Request capture and replay for jobs, and the print.planta job."""
from types import SimpleNamespace

import pytest
from flask import Flask, jsonify, request, url_for

from app.database import db
from app.database.schema import create_runner_tables
from app.models.runner import Job
from app.runner import runner as core
from app.runner import requests as job_requests
from app.modules.print import jobs as print_jobs


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.setattr(core, 'job_files_root', lambda: str(tmp_path / 'jobs'))
    monkeypatch.setattr(core, '_job_types', {})
    flask_app = Flask('request-jobs-test')
    flask_app.config.update(SQLALCHEMY_DATABASE_URI='sqlite:///:memory:', SQLALCHEMY_TRACK_MODIFICATIONS=False,
                            SQLALCHEMY_ENGINE_OPTIONS={'execution_options': {'schema_translate_map': {'scalargis': None}}})
    flask_app.add_url_rule('/file/<filename>', 'file.get', lambda filename: filename)
    db.init_app(flask_app)
    with flask_app.app_context():
        create_runner_tables()
        yield flask_app
        db.session.remove()


FORM = 'viewerId=3&scale=1000&layers[]=a;b&layers[]=c;d&geomWKT[]=POINT(1 2)&title=Planta%20%C3%A1rea'


def _form_request(app):
    return app.test_request_context('/api/app/viewer/3/print/p1/generate/job?x=1', base_url='https://box.pt/dev/',
                                    method='POST', data=FORM, content_type='application/x-www-form-urlencoded',
                                    headers={'User-Agent': 'probe/1'}, environ_base={'REMOTE_ADDR': '10.0.0.9'})


def test_capture_and_replay_keep_form_lists_args_and_the_url_root(app):
    with _form_request(app):
        captured = job_requests.capture_request(request)
    assert captured['url_root'] == 'https://box.pt/dev/'
    assert 'json' not in captured

    with job_requests.replay_request(captured):
        assert request.values['viewerId'] == '3'
        assert request.values['title'] == 'Planta área'
        assert request.form.getlist('layers[]') == ['a;b', 'c;d']
        assert request.form.getlist('geomWKT[]') == ['POINT(1 2)']
        assert request.args['x'] == '1'
        assert request.script_root == '/dev'
        assert request.remote_addr == '10.0.0.9'
        assert request.headers['User-Agent'] == 'probe/1'
        assert url_for('file.get', filename='f.pdf') == '/dev/file/f.pdf'


def test_capture_and_replay_keep_a_json_body(app):
    body = {'group_name': 'CRUS', 'record': {'concelho': 'ODEMIRA'}, 'simplification': True}
    with app.test_request_context('/mapaspt/api/app/inteligt/query/job', method='POST', json=body):
        captured = job_requests.capture_request(request)
    with job_requests.replay_request(captured):
        assert request.json == body


def test_replay_sets_current_user_only_when_given(app):
    from flask_login import LoginManager, current_user
    LoginManager(app).user_loader(lambda user_id: None)
    with _form_request(app):
        captured = job_requests.capture_request(request)
    someone = SimpleNamespace(id=5, is_authenticated=True)
    with job_requests.replay_request(captured, someone):
        assert current_user.id == 5
        with job_requests.replay_request(captured):
            assert not current_user.is_authenticated
        assert current_user.id == 5
    with job_requests.replay_request(captured):
        assert not current_user.is_authenticated


def test_plain_result_reads_a_json_response(app):
    with app.test_request_context('/'):
        assert job_requests.plain_result(jsonify(Success=False, Message='m')) == {'Success': False, 'Message': 'm'}
    assert job_requests.plain_result({'a': 1}) == {'a': 1}


def test_print_planta_job_runs_the_print_with_the_captured_request(app, monkeypatch):
    from app.modules.print import controllers
    seen = {}

    def fake_print(code, user, request=request):
        seen.update(code=code, user=user, layers=request.form.getlist('layers[]'), scale=request.values['scale'])
        return {'Success': True, 'Message': None,
                'Data': {'filename': 'f.pdf', 'url': url_for('file.get', filename='f.pdf'), 'planta_id': 9}}

    monkeypatch.setattr(controllers, 'viewer_generate_pdf', fake_print)
    print_jobs.register()
    assert core.job_types() == [print_jobs.JOB_TYPE]

    with _form_request(app):
        job_id = print_jobs.start_print_planta(request, 'p1', None)
    assert core.claim_job('box/pid1') == job_id
    assert core.run_job(job_id) == core.STATUS_DONE

    job = db.session.get(Job, job_id)
    assert job.created_by is None
    assert job.result['Data']['url'] == '/dev/file/f.pdf'
    assert seen == {'code': 'p1', 'user': None, 'layers': ['a;b', 'c;d'], 'scale': '1000'}


def test_print_planta_job_stores_a_not_configured_answer_as_its_result(app, monkeypatch):
    from app.modules.print import controllers
    monkeypatch.setattr(controllers, 'viewer_generate_pdf',
                        lambda code, user: jsonify(Success=False, Message='nao configurada', Data=None))
    print_jobs.register()
    with _form_request(app):
        job_id = print_jobs.start_print_planta(request, 'nope', None)
    core.claim_job('box/pid1')
    assert core.run_job(job_id) == core.STATUS_DONE
    assert db.session.get(Job, job_id).result == {'Success': False, 'Message': 'nao configurada', 'Data': None}
