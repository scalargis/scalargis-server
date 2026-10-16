from types import SimpleNamespace

from flask import Flask, request
from flask_login import LoginManager, current_user

from app.runner import requests as job_requests


def test_replay_sets_current_user_only_when_given():
    app = Flask('request-jobs-test')
    LoginManager(app).user_loader(lambda user_id: None)
    with app.app_context():
        with app.test_request_context('/print/job', method='POST', data={'viewerId': '3'}):
            captured = job_requests.capture_request(request)
        someone = SimpleNamespace(id=5, is_authenticated=True)
        with job_requests.replay_request(captured, someone):
            assert current_user.id == 5
            with job_requests.replay_request(captured):
                assert not current_user.is_authenticated
            assert current_user.id == 5
        with job_requests.replay_request(captured):
            assert not current_user.is_authenticated
