import pytest
from flask import Flask

from app.utils.password_policy import validate_password


@pytest.fixture
def ctx():
    with Flask(__name__).app_context():
        yield


def test_short_password_fails(ctx):
    valid, msg, failed = validate_password('Ab1!')
    assert valid is False
    assert msg == 'password_policy_violation'
    assert failed == ['min_length']


@pytest.mark.parametrize('password, expected', [
    ('abcdefghijkl1!', ['uppercase']),
    ('ABCDEFGHIJKL1!', ['lowercase']),
    ('Abcdefghijkl!!', ['digit']),
    ('Abcdefghijkl12', ['special']),
])
def test_each_rule_fails_a_password(ctx, password, expected):
    valid, _msg, failed = validate_password(password)
    assert valid is False
    assert failed == expected


@pytest.mark.parametrize('password', ['', None])
def test_empty_password_fails_every_rule(ctx, password):
    valid, _msg, failed = validate_password(password)
    assert valid is False
    assert set(failed) == {'min_length', 'uppercase', 'lowercase', 'digit', 'special'}
