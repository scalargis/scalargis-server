"""The viewer and backoffice index.html is read from disk once, and again only when its mtime changes."""
import builtins
import os

import pytest
from flask import Flask

from app.utils import http as http_utils

PAGE = '<script src="/static/{0}/main.js"></script><p>__SCALARGIS_ROOT_PATH__|__SCALARGIS_ROOT_PATH_BASE_URL__</p>'


@pytest.fixture
def app(tmp_path, monkeypatch):
    for name in ('viewer', 'backoffice'):
        (tmp_path / name).mkdir()
        (tmp_path / name / 'index.html').write_text(PAGE.format(name), encoding='utf-8')
    flask_app = Flask('app-index-test', static_folder=str(tmp_path))
    monkeypatch.setattr(http_utils, '_app_index', {})
    with flask_app.app_context():
        yield flask_app


@pytest.fixture
def opens(monkeypatch):
    seen = []
    real_open = builtins.open

    def counting_open(file, *args, **kwargs):
        if str(file).endswith('index.html'):
            seen.append(str(file))
        return real_open(file, *args, **kwargs)

    monkeypatch.setattr(builtins, 'open', counting_open)
    return seen


def _touch_later(path, text):
    stat = os.stat(path)
    path.write_text(text, encoding='utf-8')
    os.utime(path, ns=(stat.st_atime_ns, stat.st_mtime_ns + 1_000_000_000))


def test_reads_the_file_once(app, opens):
    for _ in range(5):
        assert http_utils.read_app_index('viewer') == PAGE.format('viewer')
    assert len(opens) == 1


def test_each_app_has_its_own_entry(app, opens):
    assert http_utils.read_app_index('viewer') == PAGE.format('viewer')
    assert http_utils.read_app_index('backoffice') == PAGE.format('backoffice')
    http_utils.read_app_index('viewer')
    http_utils.read_app_index('backoffice')
    assert len(opens) == 2


def test_reads_again_after_a_new_build(app, opens, tmp_path):
    http_utils.read_app_index('viewer')
    _touch_later(tmp_path / 'viewer' / 'index.html', 'new build')
    assert http_utils.read_app_index('viewer') == 'new build'
    http_utils.read_app_index('viewer')
    assert len(opens) == 2


def test_missing_file_raises(app, tmp_path):
    os.remove(tmp_path / 'viewer' / 'index.html')
    with pytest.raises(FileNotFoundError):
        http_utils.read_app_index('viewer')


def test_routes_replace_the_tokens_on_each_request(app, opens):
    from app.modules.backoffice import mod as backoffice_mod
    app.register_blueprint(backoffice_mod)
    client = app.test_client()
    first = client.get('/backoffice/users', environ_overrides={'SCRIPT_NAME': '/geo'}).get_data(as_text=True)
    second = client.get('/backoffice/').get_data(as_text=True)
    assert first == '<script src="/geo/static/backoffice/main.js"></script><p>/geo|/geo</p>'
    assert second == '<script src="/static/backoffice/main.js"></script><p>|</p>'
    assert len(opens) == 1
