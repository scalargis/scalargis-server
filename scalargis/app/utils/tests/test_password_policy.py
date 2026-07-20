"""Tests for the password policy module and the policy it publishes.

Run with the venv interpreter from ``scalargis-server/scalargis``::

    ../venv/Scripts/python.exe -m pytest app/utils/tests/test_password_policy.py

These use a bare ``Flask`` app rather than the real app factory: the module only
ever touches ``current_app.config``, so a minimal app context is enough and the
tests stay free of the database.
"""
import pytest
from flask import Flask

from app.utils.password_policy import (
    _CHARACTER_RULES,
    _DEFAULTS,
    describe_policy,
    validate_password,
)


@pytest.fixture
def app():
    return Flask(__name__)


def _ctx(app, **config):
    app.config.update(config)
    return app.app_context()


# --- describe_policy -------------------------------------------------

def test_describe_policy_returns_the_defaults(app):
    with _ctx(app):
        assert describe_policy() == {
            'min_length': 12,
            'require_uppercase': True,
            'require_lowercase': True,
            'require_digit': True,
            'require_special': True,
        }


def test_describe_policy_follows_config_overrides(app):
    with _ctx(app, SCALARGIS_PASSWORD_MIN_LENGTH=8,
              SCALARGIS_PASSWORD_REQUIRE_SPECIAL=False):
        policy = describe_policy()
    assert policy['min_length'] == 8
    assert policy['require_special'] is False
    # untouched rules keep their defaults
    assert policy['require_uppercase'] is True


def test_describe_policy_is_json_safe(app):
    """Only plain scalars -- the endpoint returns this straight to an anonymous
    caller, so it must never carry an object or a secret."""
    with _ctx(app):
        policy = describe_policy()
    assert set(policy) == {'min_length', 'require_uppercase', 'require_lowercase',
                           'require_digit', 'require_special'}
    assert isinstance(policy['min_length'], int)
    for key in policy:
        if key != 'min_length':
            assert isinstance(policy[key], bool)


def test_describe_policy_flags_are_real_bools_not_truthy_config(app):
    """A deployment writing 1/0 (or "yes") must still publish JSON booleans."""
    with _ctx(app, SCALARGIS_PASSWORD_REQUIRE_DIGIT=1,
              SCALARGIS_PASSWORD_REQUIRE_UPPERCASE=0):
        policy = describe_policy()
    assert policy['require_digit'] is True
    assert policy['require_uppercase'] is False


# --- the anti-drift property -----------------------------------------

def test_every_character_rule_is_published(app):
    """The point of the endpoint: a rule that is enforced must be advertised.

    Both functions walk ``_CHARACTER_RULES``, so this holds by construction --
    the test guards the construction.
    """
    with _ctx(app):
        policy = describe_policy()
    for rule_id, _suffix, _pattern in _CHARACTER_RULES:
        assert 'require_{}'.format(rule_id) in policy


def test_published_rules_match_what_validate_password_enforces(app):
    """Turn every rule off; the published policy must go all-False and a weak
    password must then pass. Proves the two read the same config."""
    with _ctx(app, SCALARGIS_PASSWORD_MIN_LENGTH=1,
              SCALARGIS_PASSWORD_REQUIRE_UPPERCASE=False,
              SCALARGIS_PASSWORD_REQUIRE_LOWERCASE=False,
              SCALARGIS_PASSWORD_REQUIRE_DIGIT=False,
              SCALARGIS_PASSWORD_REQUIRE_SPECIAL=False):
        policy = describe_policy()
        valid, _msg, failed = validate_password('a')

    assert policy == {'min_length': 1, 'require_uppercase': False,
                      'require_lowercase': False, 'require_digit': False,
                      'require_special': False}
    assert valid is True
    assert failed is None


def test_failed_rules_are_a_subset_of_the_published_rule_ids(app):
    """``failed_rules`` reaches the client, which maps it onto the published
    policy -- so every id it can emit must be one the client knows."""
    published = {'min_length'} | {rule_id for rule_id, _s, _p in _CHARACTER_RULES}
    with _ctx(app):
        _valid, _msg, partial = validate_password('a')
        _valid, _msg, everything = validate_password('')
    assert set(partial) <= published
    # the empty password trips every rule there is, so this pins the whole set
    assert set(everything) == published


def test_defaults_table_and_character_rules_agree(app):
    """Each character rule's config suffix must exist in ``_DEFAULTS``."""
    for _rule_id, suffix, _pattern in _CHARACTER_RULES:
        assert suffix in _DEFAULTS


# --- validate_password (regression cover for the refactor) -----------

def test_valid_password_passes(app):
    with _ctx(app):
        assert validate_password('Abcdefgh1234!') == (True, None, None)


def test_short_password_fails_on_min_length_only(app):
    with _ctx(app):
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
def test_each_rule_is_reported_by_id(app, password, expected):
    with _ctx(app):
        valid, _msg, failed = validate_password(password)
    assert valid is False
    assert failed == expected


def test_empty_and_none_passwords_fail_every_rule(app):
    with _ctx(app):
        for pw in ('', None):
            valid, _msg, failed = validate_password(pw)
            assert valid is False
            assert set(failed) == {'min_length', 'uppercase', 'lowercase',
                                   'digit', 'special'}
