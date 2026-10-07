"""Tests for the API token and confirm token formats."""
from datetime import timedelta
from types import SimpleNamespace

import pytest
from flask import Flask
from itsdangerous import URLSafeTimedSerializer

from app.utils import tokens


@pytest.fixture
def user(monkeypatch):
    found = SimpleNamespace(id=7, password='$2b$12$hash', email='user@example.com', is_active=True)
    monkeypatch.setattr(tokens, '_find', lambda user_id: found if str(user_id) == '7' else None)
    return found


@pytest.fixture
def ctx():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'test-secret'
    with app.app_context():
        yield app


def test_auth_token_round_trip(ctx, user):
    assert tokens.user_from_auth_token(tokens.auth_token(user)) is user


def test_auth_token_is_a_signed_two_item_list(ctx, user):
    data = URLSafeTimedSerializer('test-secret', salt='remember-salt').loads(tokens.auth_token(user))
    assert isinstance(data, list) and data[0] == '7' and data[1].startswith('$5$')


def test_password_change_voids_auth_token(ctx, user):
    token = tokens.auth_token(user)
    user.password = '$2b$12$other'
    assert tokens.user_from_auth_token(token) is None


def test_inactive_user_gets_no_user_from_auth_token(ctx, user):
    token = tokens.auth_token(user)
    user.is_active = False
    assert tokens.user_from_auth_token(token) is None


def test_dict_payload_is_rejected(ctx, user):
    token = URLSafeTimedSerializer('test-secret', salt='remember-salt').dumps({'ver': '5', 'uid': '7'})
    assert tokens.user_from_auth_token(token) is None


@pytest.mark.parametrize('token', ['', 'garbage', None])
def test_bad_auth_token_gives_none(ctx, user, token):
    assert tokens.user_from_auth_token(token) is None


def test_confirmation_token_round_trip(ctx, user):
    assert tokens.confirmation_token_status(tokens.confirmation_token(user)) == (False, False, user)


def test_email_change_voids_confirmation_token(ctx, user):
    token = tokens.confirmation_token(user)
    user.email = 'other@example.com'
    assert tokens.confirmation_token_status(token) == (False, True, user)


def test_expired_confirmation_token(ctx, user):
    token = tokens.confirmation_token(user)
    assert tokens.confirmation_token_status(token, within=timedelta(seconds=-1)) == (True, False, user)


def test_confirmation_token_of_unknown_user(ctx, user):
    token = URLSafeTimedSerializer('test-secret', salt='confirm-salt').dumps(['8', 'x'])
    assert tokens.confirmation_token_status(token) == (False, False, None)


def test_bad_confirmation_token_is_invalid(ctx, user):
    assert tokens.confirmation_token_status('garbage') == (False, True, None)


def test_confirmation_token_with_dict_payload_is_invalid(ctx, user):
    token = URLSafeTimedSerializer('test-secret', salt='confirm-salt').dumps({'uid': '7'})
    assert tokens.confirmation_token_status(token) == (False, True, None)
