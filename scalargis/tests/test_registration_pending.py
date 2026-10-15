"""A pending account gets a new activation mail, every other account keeps the 409, and an admin save confirms the email."""
from datetime import datetime

import pytest
from flask import Flask

from app.api.v1.portal.dao import security as dao
from app.models.security import User, Role, Group

CONFIRMED = datetime(2026, 1, 1)


def _user(username, email, active, confirmed_at=None):
    return User(username=username, email=email, name=username, active=active, confirmed_at=confirmed_at)


class _Query:
    def __init__(self, rows):
        self.rows = rows

    def all(self):
        return self.rows

    def filter(self, *args):
        return self

    def one(self):
        return self.rows[0]


class _Session:
    def __init__(self, record=None):
        self.record = record
        self.added = []

    def query(self, model):
        if model in (Role, Group):
            return _Query([])
        return _Query([self.record])

    def add(self, record):
        self.added.append(record)

    def commit(self):
        pass

    def refresh(self, record):
        pass


class _Db:
    def __init__(self, record=None):
        self.session = _Session(record)


@pytest.fixture
def flask_app():
    return Flask('registration-test')


@pytest.fixture
def mails(monkeypatch):
    sent = []
    monkeypatch.setattr(dao, 'send_email_user_registration',
                        lambda user, redirect=None, locale=None: sent.append((user, redirect)))
    return sent


@pytest.fixture
def users(monkeypatch):
    rows = []

    def by_email(email):
        return next((u for u in rows if email and u.email.lower() == email.lower()), None)

    def by_username_or_email(username, email):
        return next((u for u in rows if u.username.lower() == (username or '').lower()
                     or u.email.lower() == (email or '').lower()), None)

    monkeypatch.setattr(dao, '_find_user_by_email', by_email)
    monkeypatch.setattr(dao, '_find_user_by_username_or_email', by_username_or_email)
    monkeypatch.setattr(dao, 'enforce_password_policy', lambda password: None)
    monkeypatch.setattr(dao, 'hash_password', lambda password: 'hashed:' + password)
    return rows


@pytest.fixture
def db(monkeypatch):
    fake = _Db()
    monkeypatch.setattr(dao, 'db', fake)
    return fake


def _register(flask_app, username, email):
    body = {'name': 'Ana', 'username': username, 'email': email, 'password': 'Secret#123',
            'redirect': 'viewer', 'locale': 'pt'}
    with flask_app.test_request_context('/register_user', method='POST', json=body):
        return dao.register_user(dao.request)


def _send_confirmation(flask_app, email):
    with flask_app.test_request_context('/send_confirmation', method='POST', json={'email': email}):
        return dao.send_confirmation(dao.request)


def test_is_pending():
    assert dao.is_pending(_user('a', 'a@x.pt', active=False))
    assert not dao.is_pending(_user('a', 'a@x.pt', active=True))
    assert not dao.is_pending(_user('a', 'a@x.pt', active=False, confirmed_at=CONFIRMED))
    assert not dao.is_pending(None)


def test_a_new_registration_adds_an_inactive_user(flask_app, users, mails, db):
    body, status = _register(flask_app, 'ana', 'ana@x.pt')

    assert status == 200
    assert body == {'success': True, 'message': 'registration_email_sent', 'email': 'ana@x.pt'}
    [user] = db.session.added
    assert (user.username, user.active, user.password) == ('ana', False, 'hashed:Secret#123')
    assert mails == [(user, 'viewer')]


@pytest.mark.parametrize('username', ['ana', 'other'])
def test_register_again_over_a_pending_account_sends_a_new_mail(flask_app, users, mails, db, username):
    pending = _user('ana', 'Ana@X.pt', active=False)
    users.append(pending)

    body, status = _register(flask_app, username, 'ana@x.pt')

    assert status == 200
    assert body == {'success': True, 'message': 'registration_email_sent', 'email': 'Ana@X.pt'}
    assert mails == [(pending, 'viewer')]
    assert db.session.added == []
    assert pending.username == 'ana'
    assert pending.password is None


@pytest.mark.parametrize('existing', [
    _user('ana', 'ana@x.pt', active=True, confirmed_at=CONFIRMED),
    _user('ana', 'ana@x.pt', active=False, confirmed_at=CONFIRMED),
    _user('ana', 'ana@x.pt', active=True),
], ids=['active', 'admin-saved-inactive', 'active-unconfirmed'])
def test_register_again_over_any_other_account_gets_409(flask_app, users, mails, db, existing):
    users.append(existing)

    body, status = _register(flask_app, 'other', 'ana@x.pt')

    assert status == 409
    assert body['message'] == 'registration_user_exists'
    assert mails == []
    assert db.session.added == []


def test_a_taken_username_with_a_new_email_gets_409(flask_app, users, mails, db):
    users.append(_user('ana', 'ana@x.pt', active=False))

    body, status = _register(flask_app, 'ana', 'new@x.pt')

    assert status == 409
    assert mails == []


def test_send_confirmation_mails_a_pending_account(flask_app, users, mails):
    pending = _user('ana', 'ana@x.pt', active=False)
    users.append(pending)

    body, status = _send_confirmation(flask_app, 'ANA@x.pt')

    assert (status, body['message']) == (200, 'registration_confirmation_sent_if_exists')
    assert [user for user, _ in mails] == [pending]


@pytest.mark.parametrize('rows, email', [
    ([_user('ana', 'ana@x.pt', active=True, confirmed_at=CONFIRMED)], 'ana@x.pt'),
    ([_user('ana', 'ana@x.pt', active=False, confirmed_at=CONFIRMED)], 'ana@x.pt'),
    ([], 'nobody@x.pt'),
    ([], None),
], ids=['active', 'admin-saved-inactive', 'unknown', 'no-email'])
def test_send_confirmation_mails_no_other_account(flask_app, users, mails, rows, email):
    users.extend(rows)

    body, status = _send_confirmation(flask_app, email)

    assert (status, body['message']) == (200, 'registration_confirmation_sent_if_exists')
    assert mails == []


@pytest.fixture
def admin(monkeypatch):
    monkeypatch.setattr(dao, 'get_user', lambda request: None)


def test_create_user_fills_confirmed_at(flask_app, admin, db):
    with flask_app.test_request_context('/users', method='POST'):
        record = dao.create_user({'username': 'ana', 'email': 'ana@x.pt', 'active': False})

    assert record.confirmed_at is not None
    assert not dao.is_pending(record)


def test_update_user_fills_an_empty_confirmed_at(flask_app, admin, monkeypatch):
    record = _user('ana', 'ana@x.pt', active=False)
    monkeypatch.setattr(dao, 'db', _Db(record))

    with flask_app.test_request_context('/users/1', method='PUT'):
        dao.update_user(1, {'username': 'ana', 'email': 'ana@x.pt', 'active': False})

    assert record.confirmed_at is not None
    assert not dao.is_pending(record)


def test_update_user_keeps_a_set_confirmed_at(flask_app, admin, monkeypatch):
    record = _user('ana', 'ana@x.pt', active=True, confirmed_at=CONFIRMED)
    monkeypatch.setattr(dao, 'db', _Db(record))

    with flask_app.test_request_context('/users/1', method='PUT'):
        dao.update_user(1, {'username': 'ana', 'email': 'ana@x.pt', 'active': True})

    assert record.confirmed_at == CONFIRMED
