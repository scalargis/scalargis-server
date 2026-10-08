"""get_config_value reads only the site_settings row of its key."""
import pytest
from flask import Flask
from sqlalchemy import event, text

from app.database import db
from app.database.schema import db_schema
from app.models.portal import SiteSettings
from app.utils import settings as settings_utils


@pytest.fixture
def app():
    flask_app = Flask('site-settings-test')
    flask_app.config.update(SQLALCHEMY_DATABASE_URI='sqlite:///:memory:', SQLALCHEMY_TRACK_MODIFICATIONS=False,
                            SCALARGIS_PROXY_CORS=['http://localhost:3000'], CAPTCHA_URL='http://config')
    db.init_app(flask_app)
    with flask_app.app_context():
        db.session.execute(text("attach database ':memory:' as {0}".format(db_schema)))
        SiteSettings.__table__.create(db.session.connection())
        db.session.execute(text("insert into {0}.site_settings (code, setting_value) values "
                                "('SITE_CONFIG', '{{}}'), ('scalargis_proxy_cors', '*'), "
                                "('CAPTCHA_URL', ''), ('SCALARGISXPROXY_CORS', 'wrong')".format(db_schema)))
        yield flask_app
        db.session.remove()


@pytest.fixture
def statements(app):
    seen = []

    def before(conn, cursor, statement, parameters, context, executemany):
        seen.append(statement)

    engine = db.engine
    event.listen(engine, 'before_cursor_execute', before)
    yield seen
    event.remove(engine, 'before_cursor_execute', before)


def test_row_overrides_config_with_case_ignored(app):
    assert settings_utils.get_config_value('SCALARGIS_PROXY_CORS') == '*'


def test_empty_row_keeps_config_value(app):
    assert settings_utils.get_config_value('CAPTCHA_URL') == 'http://config'


def test_no_row_keeps_config_value(app):
    db.session.execute(text("delete from {0}.site_settings where lower(code) = 'scalargis_proxy_cors'".format(db_schema)))
    assert settings_utils.get_config_value('SCALARGIS_PROXY_CORS') == ['http://localhost:3000']


def test_unknown_key_is_none(app):
    assert settings_utils.get_config_value('NO_SUCH_KEY') is None


def test_lookup_filters_on_the_code(app, statements):
    settings_utils.get_config_value('SCALARGIS_PROXY_CORS')
    selects = [s for s in statements if 'site_settings' in s]
    assert len(selects) == 1
    assert 'WHERE lower(' in selects[0]
    assert ' LIKE ' not in selects[0].upper()
