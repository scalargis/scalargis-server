"""Core runner: job table, claim, run, reaper, cleanup, wakes and the job endpoints."""
import os
import threading
import time
import uuid
from datetime import timedelta
from types import SimpleNamespace

import pytest
from flask import Flask
from werkzeug.exceptions import HTTPException

from app.database import db
from app.runner import runner as core
from app.database.schema import create_runner_tables
from app.models.runner import Job, RunnerHeartbeat
from app.utils import utc_now

PG_URL = os.environ.get('RUNNER_TEST_DATABASE_URL')


def _make_app(url='sqlite:///:memory:', schema_map=True):
    app = Flask('runner-test')
    options = {'execution_options': {'schema_translate_map': {'scalargis': None}}} if schema_map else {}
    app.config.update(SQLALCHEMY_DATABASE_URI=url, SQLALCHEMY_TRACK_MODIFICATIONS=False,
                      SQLALCHEMY_ENGINE_OPTIONS=options)
    db.init_app(app)
    return app


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.setattr(core, 'job_files_root', lambda: str(tmp_path / 'jobs'))
    monkeypatch.setattr(core, '_job_types', {})
    core._job_event.clear()
    flask_app = _make_app()
    with flask_app.app_context():
        create_runner_tables()
        yield flask_app
        db.session.remove()


def _job(**fields):
    values = dict(id=uuid.uuid4(), type='t', payload={}, status=core.STATUS_QUEUED, attempts=0,
                  created_at=utc_now())
    values.update(fields)
    job = Job(**values)
    db.session.add(job)
    db.session.commit()
    return job.id


def test_enqueue_claim_and_run_store_the_result(app):
    core.register_job_type('t', lambda ctx: {'double': ctx.payload['n'] * 2, 'by': ctx.created_by})

    job_id = core.enqueue('t', {'n': 21}, created_by=7)
    assert core._job_event.is_set()
    assert db.session.get(Job, job_id).status == core.STATUS_QUEUED

    assert core.claim_job('box/pid1') == job_id
    job = db.session.get(Job, job_id)
    assert (job.status, job.attempts, job.runner) == (core.STATUS_RUNNING, 1, 'box/pid1')
    assert core.claim_job('box/pid1') is None

    assert core.run_job(job_id) == core.STATUS_DONE
    db.session.expire_all()
    job = db.session.get(Job, job_id)
    assert job.result == {'double': 42, 'by': 7}
    assert job.finished_at is not None


def test_enqueue_rejects_an_unknown_type(app):
    with pytest.raises(ValueError):
        core.enqueue('nope')


def test_claim_skips_types_this_runner_does_not_know(app):
    core.register_job_type('t', lambda ctx: None)
    _job(type='other')
    assert core.claim_job('box/pid1') is None


def test_queue_keeps_the_jobs_of_one_line_apart(app, monkeypatch):
    core.register_job_type('t', lambda ctx: {'type': ctx.type})
    monkeypatch.setenv('RUNNER_QUEUE', 'dev')
    dev_job = core.enqueue('t')
    assert db.session.get(Job, dev_job).type == 'dev/t'

    monkeypatch.delenv('RUNNER_QUEUE')
    prod_job = core.enqueue('t')
    assert db.session.get(Job, prod_job).type == 't'
    assert core.claim_job('prod/pid1') == prod_job
    assert core.claim_job('prod/pid1') is None

    monkeypatch.setenv('RUNNER_QUEUE', 'dev')
    assert core.claim_job('dev/pid1') == dev_job
    assert core.run_job(dev_job) == core.STATUS_DONE
    assert db.session.get(Job, dev_job).result == {'type': 't'}


def test_failed_handler_marks_the_job_failed(app):
    def boom(ctx):
        raise RuntimeError('no map')

    core.register_job_type('t', boom)
    job_id = core.enqueue('t')
    core.claim_job('h')

    assert core.run_job(job_id) == core.STATUS_FAILED
    db.session.expire_all()
    job = db.session.get(Job, job_id)
    assert job.error == 'no map'
    assert job.result is None


def test_handler_file_goes_to_the_work_dir(app):
    def write(ctx):
        path = os.path.join(ctx.work_dir(), 'out.pdf')
        with open(path, 'wb') as f:
            f.write(b'%PDF')
        ctx.result_path = path
        return {'pages': 1}

    core.register_job_type('t', write)
    job_id = core.enqueue('t')
    core.claim_job('h')
    core.run_job(job_id)

    db.session.expire_all()
    job = db.session.get(Job, job_id)
    assert job.result_path.endswith(os.path.join(str(job_id), 'out.pdf'))
    assert os.path.isfile(job.result_path)


def test_result_that_is_not_json_fails_the_job(app):
    core.register_job_type('t', lambda ctx: {'when': object()})
    job_id = core.enqueue('t')
    core.claim_job('h')

    assert core.run_job(job_id) == core.STATUS_FAILED
    db.session.expire_all()
    assert db.session.get(Job, job_id).error.startswith('result not saved')


def test_reaper_requeues_then_fails_jobs_of_a_dead_runner(app):
    now = utc_now()
    db.session.add(RunnerHeartbeat(key='runner:live/pid1', host='live/pid1', last_beat_at=now, beat_count=1))
    db.session.add(RunnerHeartbeat(key='runner:dead/pid2', host='dead/pid2',
                                   last_beat_at=now - timedelta(hours=1), beat_count=1))
    db.session.commit()
    live = _job(status=core.STATUS_RUNNING, runner='live/pid1', attempts=1)
    retry = _job(status=core.STATUS_RUNNING, runner='dead/pid2', attempts=1)
    last = _job(status=core.STATUS_RUNNING, runner='dead/pid2', attempts=2)

    assert core.reap_lost_jobs() == 1

    db.session.expire_all()
    assert db.session.get(Job, live).status == core.STATUS_RUNNING
    assert db.session.get(Job, retry).status == core.STATUS_QUEUED
    assert db.session.get(Job, retry).runner is None
    assert db.session.get(Job, last).status == core.STATUS_FAILED


def test_cleanup_deletes_old_finished_jobs_and_their_files(app):
    old = utc_now() - timedelta(days=3)
    gone = _job(status=core.STATUS_DONE, finished_at=old)
    kept_recent = _job(status=core.STATUS_DONE, finished_at=utc_now())
    kept_queued = _job(created_at=old)
    folder = os.path.join(core.job_files_root(), str(gone))
    os.makedirs(folder)
    db.session.add(RunnerHeartbeat(key='runner:old/pid1', host='old/pid1', updated_at=old, beat_count=0))
    db.session.add(RunnerHeartbeat(key='periodic:x', host='old/pid1', updated_at=old, beat_count=0))
    db.session.commit()

    assert core.cleanup_jobs() == 1

    db.session.expire_all()
    assert db.session.get(Job, gone) is None
    assert db.session.get(Job, kept_recent) is not None
    assert db.session.get(Job, kept_queued) is not None
    assert not os.path.exists(folder)
    assert db.session.get(RunnerHeartbeat, 'runner:old/pid1') is None
    assert db.session.get(RunnerHeartbeat, 'periodic:x') is not None


def test_periodic_heartbeat_moves_only_on_success(app, monkeypatch):
    state = {'fail': False, 'wakes': []}

    def task(wakes):
        state['wakes'].append(wakes)
        if state['fail']:
            raise RuntimeError('down')

    monkeypatch.setattr(core, '_periodics', {})
    core.register_periodic('t.task', task, 10)
    key = core.periodic_key('t.task')

    assert core.run_periodic('t.task', host='h')
    row = db.session.get(RunnerHeartbeat, key)
    assert (row.beat_count, row.last_error) == (1, None)
    first_beat = row.last_beat_at

    state['fail'] = True
    assert not core.run_periodic('t.task', ['64'], host='h')
    db.session.expire_all()
    row = db.session.get(RunnerHeartbeat, key)
    assert (row.beat_count, row.last_error, row.last_beat_at) == (1, 'down', first_beat)
    assert state['wakes'] == [[], ['64']]


def test_notify_messages_turn_into_wakes(monkeypatch):
    monkeypatch.setattr(core, '_wakes', {})
    core._job_event.clear()
    event = core._wake_event('t.msg')
    event.clear()

    core.handle_message('{"job": "abc"}')
    core.handle_message('{"wake": "t.msg", "p": "64"}')
    core.handle_message('not json')
    core.handle_message('[1]')

    assert core._job_event.is_set()
    assert event.is_set()
    assert core.pop_wakes('t.msg') == ['64']
    assert core.pop_wakes('t.msg') == []


def test_wake_without_postgres_stays_in_process(app, monkeypatch):
    monkeypatch.setattr(core, '_wakes', {})

    assert core.wake('t.local', '7') is False
    assert core.pop_wakes('t.local') == ['7']


def test_leader_is_always_true_off_postgres(app):
    assert core._Leader(app).hold() is True


def test_host_id_differs_after_a_restart_with_the_same_pid(monkeypatch):
    monkeypatch.setattr(core, '_process_ids', {})
    first = core.host_id()
    assert core.host_id() == first
    monkeypatch.setattr(core, '_process_ids', {})
    assert core.host_id() != first
    assert first.split('/')[1] == 'pid{0}'.format(os.getpid())


def test_runner_mode(monkeypatch):
    monkeypatch.setenv('RUNNER_MODE', ' External ')
    assert core.runner_mode() == core.MODE_EXTERNAL
    monkeypatch.delenv('RUNNER_MODE')
    assert core.runner_mode() == ''


def test_in_process_runner_runs_a_job_and_a_periodic(tmp_path, monkeypatch):
    monkeypatch.setattr(core, 'job_files_root', lambda: str(tmp_path / 'jobs'))
    monkeypatch.setattr(core, '_job_types', {})
    monkeypatch.setattr(core, '_periodics', {})
    monkeypatch.setenv('RUNNER_POLL_SECONDS', '1')
    flask_app = _make_app('sqlite:///' + str(tmp_path / 'r.db').replace('\\', '/'))
    ticks = []
    core.register_job_type('t', lambda ctx: {'ok': ctx.payload['n']})
    core.register_periodic('t.tick', ticks.append, 3600)

    with flask_app.app_context():
        create_runner_tables()
    runner = core.Runner(flask_app).start()
    try:
        with flask_app.app_context():
            job_id = core.enqueue('t', {'n': 5})
            core.wake('t.tick', '9')
        deadline = time.monotonic() + 10
        status = None
        while time.monotonic() < deadline:
            with flask_app.app_context():
                status = db.session.get(Job, job_id).status
            if status == core.STATUS_DONE and ['9'] in ticks:
                break
            time.sleep(0.05)
    finally:
        runner.stop(wait=True)
    assert status == core.STATUS_DONE
    assert [] in ticks and ['9'] in ticks


def test_runner_beat_touches_the_beat_file_only_after_a_row_write(app, tmp_path, monkeypatch):
    beat_file = tmp_path / 'beat'
    monkeypatch.setenv('RUNNER_BEAT_FILE', str(beat_file))
    runner = core.Runner(app)
    monkeypatch.setattr(core, '_write_beat', lambda *a, **k: False)
    runner._beat_runner()
    assert not beat_file.exists()
    monkeypatch.setattr(core, '_write_beat', lambda *a, **k: True)
    runner.last_runner_beat = 0.0
    runner._beat_runner()
    assert beat_file.exists()
    os.utime(str(beat_file), (0, 0))
    runner.last_runner_beat = 0.0
    runner._beat_runner()
    assert os.path.getmtime(str(beat_file)) > time.time() - 60


def test_beat_file_is_off_without_the_env_var(tmp_path, monkeypatch):
    monkeypatch.delenv('RUNNER_BEAT_FILE', raising=False)
    monkeypatch.chdir(tmp_path)
    core.touch_beat_file()
    assert os.listdir(str(tmp_path)) == []


class _User(SimpleNamespace):
    pass


def _admin():
    return _User(id=1, roles=[SimpleNamespace(name='Admin')])


def _someone(user_id):
    return _User(id=user_id, roles=[SimpleNamespace(name='Authenticated')])


@pytest.fixture
def jobs_api(app, monkeypatch):
    from app.api.v1.endpoints import jobs
    app.config.update(RESTX_MASK_HEADER='X-Fields', RESTX_MASK_SWAGGER=False)
    state = {'user': None}
    monkeypatch.setattr(jobs.dao_job, 'get_user', lambda request: state['user'])
    monkeypatch.setattr(jobs.dao_job, 'current_user', SimpleNamespace(is_authenticated=False))
    return jobs, state


def _code(call):
    try:
        response = call()
    except HTTPException as err:
        return err.code, None
    if isinstance(response, tuple):
        return response[1], response[0]
    return response.status_code, response


def test_status_is_readable_by_its_owner_and_an_admin(app, jobs_api):
    jobs, state = jobs_api
    job_id = str(_job(created_by=5))
    status = lambda i=job_id: _code(lambda: jobs.JobStatus().get(i))

    with app.test_request_context('/'):
        assert status()[0] == 404
        state['user'] = _someone(6)
        assert status()[0] == 404
        state['user'] = _someone(5)
        code, body = status()
        assert code == 200 and body['status'] == core.STATUS_QUEUED and body['has_file'] is False
        state['user'] = _admin()
        assert status()[0] == 200
        assert status('not-a-uuid')[0] == 404


def test_anonymous_job_is_readable_by_its_id(app, jobs_api):
    jobs, _ = jobs_api
    job_id = str(_job())
    with app.test_request_context('/'):
        assert _code(lambda: jobs.JobStatus().get(job_id))[0] == 200


def test_result_waits_for_done_then_gives_json_or_file(app, jobs_api, tmp_path):
    jobs, _ = jobs_api
    pending = str(_job())
    done = str(_job(status=core.STATUS_DONE, result={'url': '/x.pdf'}))
    path = tmp_path / 'r.pdf'
    path.write_bytes(b'%PDF-1')
    with_file = str(_job(status=core.STATUS_DONE, result_path=str(path)))
    lost_file = str(_job(status=core.STATUS_DONE, result_path=str(tmp_path / 'gone.pdf')))
    result = lambda i: _code(lambda: jobs.JobResult().get(i))

    with app.test_request_context('/'):
        code, body = result(pending)
        assert code == 409 and body['status'] == core.STATUS_QUEUED
        code, body = result(done)
        assert code == 200 and body['result'] == {'url': '/x.pdf'}
        code, response = result(with_file)
        response.direct_passthrough = False
        assert code == 200 and response.get_data() == b'%PDF-1'
        assert 'r.pdf' in response.headers['Content-Disposition']
        assert result(lost_file)[0] == 410


pg = pytest.mark.skipif(not PG_URL, reason='RUNNER_TEST_DATABASE_URL is not set')


@pytest.fixture
def pg_app(tmp_path, monkeypatch):
    monkeypatch.setattr(core, 'job_files_root', lambda: str(tmp_path / 'jobs'))
    monkeypatch.setattr(core, '_job_types', {})
    flask_app = _make_app(PG_URL, schema_map=False)
    with flask_app.app_context():
        db.session.execute(db.text('CREATE SCHEMA IF NOT EXISTS scalargis'))
        db.session.commit()
        create_runner_tables()
        db.session.execute(db.text('DELETE FROM scalargis.job'))
        db.session.commit()
    yield flask_app
    with flask_app.app_context():
        db.session.execute(db.text('DELETE FROM scalargis.job'))
        db.session.commit()


@pg
def test_pg_parallel_claims_never_take_the_same_job(pg_app):
    core.register_job_type('t', lambda ctx: None)
    with pg_app.app_context():
        ids = {core.enqueue('t', {'n': n}) for n in range(40)}

    claimed = []
    lock = threading.Lock()

    def claimer():
        while True:
            with pg_app.app_context():
                job_id = core.claim_job(threading.current_thread().name)
            if job_id is None:
                return
            with lock:
                claimed.append(job_id)

    threads = [threading.Thread(target=claimer, name='c{0}'.format(i)) for i in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert sorted(claimed, key=str) == sorted(ids, key=str)


@pg
def test_pg_one_leader_at_a_time(pg_app):
    first, second = core._Leader(pg_app), core._Leader(pg_app)
    with pg_app.app_context():
        holders = db.session.execute(db.text(
            "SELECT a.pid, a.application_name, a.backend_start FROM pg_locks l JOIN pg_stat_activity a USING (pid) "
            "WHERE l.locktype = 'advisory' AND l.objid = :k"), {'k': core.LEADER_LOCK_KEY & 0xFFFFFFFF}).all()
    try:
        assert first.hold() is True, 'leader lock held by {0}'.format(holders)
        assert second.hold() is False
        assert first.hold() is True
        first.release()
        assert second.hold() is True
    finally:
        first.release()
        second.release()


@pg
def test_pg_notify_wakes_the_listener(pg_app, monkeypatch):
    monkeypatch.setattr(core, '_wakes', {})
    core.register_job_type('t', lambda ctx: None)
    runner = core.Runner(pg_app)
    listener = threading.Thread(target=runner._listen_loop, daemon=True)
    listener.start()
    try:
        event = core._wake_event('t.pg')
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            event.clear()
            with pg_app.app_context():
                assert core.wake('t.pg', '64') is True
            if event.wait(0.5):
                break
        assert '64' in core.pop_wakes('t.pg')
    finally:
        runner.stop_event.set()
        runner.leader.release()


@pg
def test_pg_parallel_starts_create_the_tables_once(pg_app):
    with pg_app.app_context():
        db.session.execute(db.text('DROP TABLE IF EXISTS scalargis.job, scalargis.runner_heartbeat'))
        db.session.commit()
    errors = []
    barrier = threading.Barrier(8)

    def start():
        try:
            with pg_app.app_context():
                barrier.wait()
                create_runner_tables()
                db.session.remove()
        except Exception as err:
            errors.append(err)

    threads = [threading.Thread(target=start) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert errors == []
    with pg_app.app_context():
        assert db.session.execute(db.text('SELECT count(*) FROM scalargis.job')).scalar() == 0


def _kill_backends():
    """Terminate every other backend of the test database, as a Postgres restart does."""
    from sqlalchemy import create_engine
    from sqlalchemy.pool import NullPool
    engine = create_engine(PG_URL, poolclass=NullPool)
    with engine.begin() as conn:
        killed = conn.execute(db.text(
            'SELECT count(pg_terminate_backend(pid)) FROM pg_stat_activity '
            'WHERE datname = current_database() AND pid <> pg_backend_pid()')).scalar()
    engine.dispose()
    return killed


def _pooled_app(pre_ping):
    app = Flask('runner-pool-test')
    app.config.update(SQLALCHEMY_DATABASE_URI=PG_URL, SQLALCHEMY_TRACK_MODIFICATIONS=False,
                      SQLALCHEMY_ENGINE_OPTIONS={'pool_pre_ping': True} if pre_ping else {})
    db.init_app(app)
    return app


@pg
@pytest.mark.parametrize('pre_ping', [False, True])
def test_pg_pool_after_a_db_restart(pre_ping):
    from sqlalchemy.exc import OperationalError
    app = _pooled_app(pre_ping)
    with app.app_context():
        assert db.session.execute(db.text('SELECT 1')).scalar() == 1
        db.session.remove()
        assert _kill_backends() >= 1
        if pre_ping:
            assert db.session.execute(db.text('SELECT 1')).scalar() == 1
        else:
            with pytest.raises(OperationalError):
                db.session.execute(db.text('SELECT 1'))
        db.session.remove()
        db.engine.dispose()


@pg
def test_pg_runner_reconnects_after_a_db_restart(monkeypatch):
    monkeypatch.setattr(core, '_wakes', {})
    monkeypatch.setattr(core, 'LISTEN_RETRY_MAX_SECONDS', 1)
    app = _pooled_app(True)
    runner = core.Runner(app)
    listener = threading.Thread(target=runner._listen_loop, daemon=True)
    try:
        assert runner.leader.hold() is True
        listener.start()
        time.sleep(1)
        assert _kill_backends() >= 2

        deadline = time.monotonic() + 10
        while not runner.leader.hold() and time.monotonic() < deadline:
            time.sleep(0.2)
        assert runner.leader.hold() is True

        event = core._wake_event('t.restart')
        woke = False
        while not woke and time.monotonic() < deadline + 10:
            core.pop_wakes('t.restart')
            event.clear()
            with app.app_context():
                sent = core.wake('t.restart', 'back')
            woke = sent and event.wait(0.5)
        assert woke
        assert 'back' in core.pop_wakes('t.restart')
    finally:
        runner.stop_event.set()
        runner.leader.release()
        listener.join(5)
        with app.app_context():
            db.engine.dispose()
