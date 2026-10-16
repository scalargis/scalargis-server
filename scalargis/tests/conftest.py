import pytest

from app.runner import runner as core


@pytest.fixture(autouse=True)
def declared_runner_queue(monkeypatch):
    monkeypatch.setenv('RUNNER_QUEUE', '')
    monkeypatch.delenv('RUNNER_PERIODIC', raising=False)
    monkeypatch.setattr(core, '_config', {})
