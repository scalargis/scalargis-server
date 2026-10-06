"""The request values that pick a site setting or a print widget reach the SQL as bind parameters."""
import pytest
from flask import Flask
from sqlalchemy import text

from app.database import db
from app.plugins.spatial_toolbox.utils import analysis
from app.utils import pdf_layout

PAYLOAD = "x' or code='{0}"


class Stop(Exception):
    pass


@pytest.fixture
def app():
    flask_app = Flask('sql-binding-test')
    flask_app.config.update(SQLALCHEMY_DATABASE_URI='sqlite:///:memory:', SQLALCHEMY_TRACK_MODIFICATIONS=False)
    db.init_app(flask_app)
    with flask_app.app_context():
        db.session.execute(text("attach database ':memory:' as {0}".format(analysis.db_schema)))
        db.session.execute(text("create table {0}.site_settings (code text, setting_value text)".format(analysis.db_schema)))
        db.session.execute(text("insert into {0}.site_settings values ('cc_intersect', '{{\"layers\": []}}')".format(analysis.db_schema)))
        db.session.execute(text("create table {0}.widget (code text, config text)".format(analysis.db_schema)))
        db.session.execute(text("insert into {0}.widget values ('w1', '{{\"strings\": []}}')".format(analysis.db_schema)))
        yield flask_app
        db.session.remove()


@pytest.fixture
def executed(monkeypatch):
    calls = []
    real_execute = db.session.execute

    def execute(statement, params=None):
        rows = real_execute(statement, params).fetchall()
        calls.append((str(statement), params, rows))
        raise Stop

    monkeypatch.setattr(db.session, 'execute', execute)
    return calls


def test_intersect_config_code_is_bound(app, executed):
    with pytest.raises(Stop):
        analysis.get_intersect_results('cc_intersect', 'POINT(1 2)', 4326, 0, 3857, 4326)
    sql, params, rows = executed[0]
    assert params == {'code': 'cc_intersect'}
    assert len(rows) == 1


def test_intersect_payload_matches_no_setting(app, executed):
    payload = PAYLOAD.format('cc_intersect')
    with pytest.raises(Stop):
        analysis.get_intersect_results(payload, 'POINT(1 2)', 4326, 0, 3857, 4326)
    sql, params, rows = executed[0]
    assert payload not in sql
    assert params == {'code': payload}
    assert rows == []


def test_pdf_widget_code_is_bound(app, executed):
    pdf = pdf_layout.Pdf()
    pdf.add_widget_input({'codigo': 'w1', 'value': 1})
    with pytest.raises(Stop):
        pdf.generate([{}], srid=3763)
    sql, params, rows = executed[0]
    assert params == {'code': 'w1'}
    assert len(rows) == 1


def test_pdf_widget_payload_matches_no_widget(app, executed):
    payload = PAYLOAD.format('w1')
    pdf = pdf_layout.Pdf()
    pdf.add_widget_input({'codigo': payload, 'value': 1})
    with pytest.raises(Stop):
        pdf.generate([{}], srid=3763)
    sql, params, rows = executed[0]
    assert payload not in sql
    assert params == {'code': payload}
    assert rows == []
