"""Background runner: queued jobs and periodic tasks, woken through PostgreSQL LISTEN/NOTIFY."""
import json
import logging
import os
import select
import shutil
import signal
import socket
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta

from sqlalchemy import text

from app.database import db
from app.utils import utc_now
from app.models.runner import (Job, RunnerHeartbeat, FINISHED_STATUSES,
                               STATUS_DONE, STATUS_FAILED, STATUS_QUEUED, STATUS_RUNNING)

logger = logging.getLogger(__name__)

JOB_CHANNEL = 'scalargis_jobs'
LEADER_LOCK_KEY = 7286337500
MODE_EXTERNAL = 'external'
LISTEN_POLL_SECONDS = 60
LISTEN_RETRY_MAX_SECONDS = 30
RUNNER_KEY_PREFIX = 'runner:'
PERIODIC_KEY_PREFIX = 'periodic:'

_job_types = {}
_periodics = {}
_job_event = threading.Event()
_wake_lock = threading.Lock()
_wakes = {}
_wake_events = {}
_runner = None
_runner_lock = threading.Lock()


def _env_int(name, default):
    """Integer env var, or default when unset or empty."""
    value = os.environ.get(name)
    return int(value) if value else default


def runner_mode():
    """RUNNER_MODE: 'external' keeps the runner out of the web process."""
    return (os.environ.get('RUNNER_MODE') or '').strip().lower()


def runner_queue():
    """RUNNER_QUEUE: a name that keeps the jobs of one app line apart from the other lines on the same database."""
    return (os.environ.get('RUNNER_QUEUE') or '').strip()


def stored_type(name):
    """The job type as the job table stores it: queue/name when RUNNER_QUEUE is set."""
    queue = runner_queue()
    return '{0}/{1}'.format(queue, name) if queue else name


def plain_type(stored):
    """The registered name of a stored job type of this queue."""
    queue = runner_queue()
    prefix = queue + '/' if queue else ''
    return stored[len(prefix):] if prefix and stored.startswith(prefix) else stored


_process_ids = {}


def host_id():
    """Host, pid and a random part of this process, for the heartbeat rows and the job owner."""
    pid = os.getpid()
    if pid not in _process_ids:
        _process_ids[pid] = '{0}/pid{1}/{2}'.format(socket.gethostname(), pid, uuid.uuid4().hex[:8])
    return _process_ids[pid]


class Periodic(object):
    """A task that the leader runner calls every interval seconds and on each wake."""

    def __init__(self, name, fn, interval):
        self.name = name
        self.fn = fn
        self.interval = interval

    def seconds(self):
        """The interval in seconds. A callable interval is read at each run."""
        value = self.interval() if callable(self.interval) else self.interval
        return max(float(value), 1.0)


class JobContext(object):
    """What a job handler gets: the job fields and a folder for its result files."""

    def __init__(self, job):
        self.id = job.id
        self.type = plain_type(job.type)
        self.payload = job.payload or {}
        self.created_by = job.created_by
        self.result_path = None

    def work_dir(self):
        """Folder for this job's files. The cleanup deletes it with the job."""
        path = os.path.join(job_files_root(), str(self.id))
        os.makedirs(path, exist_ok=True)
        return path


def job_files_root():
    """Root folder of the job files, inside the shared tmp volume."""
    from instance import settings
    return os.path.join(settings.APP_TMP_DIR, 'jobs')


def register_job_type(name, fn):
    """Register fn(ctx) as the handler of the job type name. Its return value is the job result."""
    _job_types[name] = fn


def register_periodic(name, fn, interval):
    """Register fn(wakes) to run in the leader runner every interval seconds and on wake(name)."""
    _periodics[name] = Periodic(name, fn, interval)
    _wake_event(name)


def job_types():
    """Names of the registered job types."""
    return sorted(_job_types)


def periodic_key(name):
    """Heartbeat key of a periodic task."""
    return PERIODIC_KEY_PREFIX + name


def _wake_event(name):
    with _wake_lock:
        if name not in _wake_events:
            _wake_events[name] = threading.Event()
        return _wake_events[name]


def queue_local_wake(name, payload=None):
    """Queue a wake for the periodic task name in this process."""
    with _wake_lock:
        _wakes.setdefault(name, []).append(payload)
        event = _wake_events.get(name)
    if event is not None:
        event.set()


def pop_wakes(name):
    """Take the queued wake payloads of the periodic task name."""
    with _wake_lock:
        return _wakes.pop(name, [])


def _pg_engine():
    """The bound engine when it is PostgreSQL, else None."""
    try:
        bind = db.session.get_bind()
    except Exception:
        return None
    if getattr(getattr(bind, 'dialect', None), 'name', None) != 'postgresql':
        return None
    return getattr(bind, 'engine', bind)


def _notify(message):
    """Send message on JOB_CHANNEL. True when PostgreSQL took it."""
    engine = _pg_engine()
    if engine is None:
        return False
    try:
        with engine.begin() as conn:
            conn.execute(text('SELECT pg_notify(:c, :p)'), {'c': JOB_CHANNEL, 'p': json.dumps(message)})
        return True
    except Exception as notify_err:
        logger.warning('runner: NOTIFY failed: %s', notify_err)
        return False


def enqueue(name, payload=None, created_by=None):
    """Queue a job of the type name, commit the session and wake the runners. Returns the job id."""
    if name not in _job_types:
        raise ValueError('unknown job type: {0}'.format(name))
    job = Job(id=uuid.uuid4(), type=stored_type(name), payload=payload or {}, status=STATUS_QUEUED, attempts=0,
              created_by=created_by, created_at=utc_now())
    db.session.add(job)
    db.session.commit()
    if not _notify({'job': str(job.id)}):
        _job_event.set()
    return job.id


def wake(name, payload=None):
    """Wake the periodic task name in the leader runner. payload is a short string or None."""
    if _notify({'wake': name, 'p': payload}):
        return True
    queue_local_wake(name, payload)
    return False


def handle_message(payload):
    """Turn one NOTIFY payload into a job wake or a periodic wake."""
    try:
        message = json.loads(payload or '')
    except ValueError:
        return
    if not isinstance(message, dict):
        return
    if 'job' in message:
        _job_event.set()
    elif 'wake' in message:
        queue_local_wake(message['wake'], message.get('p'))


def _write_beat(key, host, error=None, start=False):
    """Write a heartbeat row in its own transaction. Never raises. True on success."""
    try:
        now = utc_now()
        row = db.session.get(RunnerHeartbeat, key)
        if row is None:
            row = RunnerHeartbeat(key=key, beat_count=0, started_at=now)
            db.session.add(row)
        row.host = host
        row.updated_at = now
        if start:
            row.started_at = now
            row.last_beat_at = None
            row.last_error = None
        elif error is not None:
            row.last_error = error
        else:
            row.last_beat_at = now
            row.beat_count = (row.beat_count or 0) + 1
            row.last_error = None
        db.session.commit()
        return True
    except Exception as beat_err:
        db.session.rollback()
        logger.warning('runner: heartbeat %s failed: %s', key, beat_err)
        return False


def touch_beat_file():
    """Touch the file named by RUNNER_BEAT_FILE, for a container health check. Never raises."""
    path = os.environ.get('RUNNER_BEAT_FILE')
    if not path:
        return
    try:
        with open(path, 'a'):
            pass
        os.utime(path, None)
    except OSError as touch_err:
        logger.warning('runner: beat file %s failed: %s', path, touch_err)


def run_periodic(name, wakes=(), beat=True, host=None):
    """Run the periodic task name once in the current context and write its heartbeat. True on success."""
    periodic = _periodics[name]
    try:
        periodic.fn(list(wakes))
    except Exception as run_err:
        db.session.rollback()
        logger.exception('runner: periodic %s failed', name)
        if beat:
            _write_beat(periodic_key(name), host or host_id(), error=str(run_err)[:2000] or 'error')
        return False
    if beat:
        _write_beat(periodic_key(name), host or host_id())
    return True


def claim_job(host):
    """Mark the oldest queued job of a known type as running for host. Returns its id or None."""
    types = [stored_type(name) for name in _job_types]
    if not types:
        return None
    try:
        job = (Job.query
               .filter(Job.status == STATUS_QUEUED, Job.type.in_(types))
               .order_by(Job.created_at)
               .with_for_update(skip_locked=True)
               .limit(1)
               .first())
        if job is None:
            db.session.rollback()
            return None
        job.status = STATUS_RUNNING
        job.started_at = utc_now()
        job.attempts = (job.attempts or 0) + 1
        job.runner = host
        job.error = None
        job_id = job.id
        db.session.commit()
        return job_id
    except Exception as claim_err:
        db.session.rollback()
        logger.warning('runner: job claim failed: %s', claim_err)
        return None


def run_job(job_id):
    """Run one claimed job and store its result or its error. Returns the final status."""
    job = db.session.get(Job, job_id)
    if job is None:
        return None
    ctx = JobContext(job)
    job_type = ctx.type
    fn = _job_types.get(job_type)
    result, status, error = None, STATUS_DONE, None
    try:
        if fn is None:
            raise LookupError('no handler for job type {0}'.format(job_type))
        result = fn(ctx)
    except Exception as job_err:
        db.session.rollback()
        logger.exception('runner: job %s (%s) failed', job_id, job_type)
        result, status, error = None, STATUS_FAILED, str(job_err)[:2000] or job_err.__class__.__name__
    try:
        _finish(job_id, status, result, ctx.result_path, error)
    except Exception as save_err:
        db.session.rollback()
        logger.exception('runner: job %s result not saved', job_id)
        status = STATUS_FAILED
        _finish(job_id, status, None, None, 'result not saved: {0}'.format(save_err)[:2000])
    return status


def _finish(job_id, status, result, result_path, error):
    job = db.session.get(Job, job_id)
    job.status = status
    job.result = result
    job.result_path = result_path
    job.error = error
    job.finished_at = utc_now()
    db.session.commit()


def reap_lost_jobs(wakes=None):
    """Requeue, or fail after the last attempt, running jobs whose runner stopped its heartbeat."""
    stale_before = utc_now() - timedelta(seconds=max(6 * _env_int('RUNNER_POLL_SECONDS', 10), 60))
    live = {row.key[len(RUNNER_KEY_PREFIX):] for row in RunnerHeartbeat.query.filter(
        RunnerHeartbeat.key.like(RUNNER_KEY_PREFIX + '%'), RunnerHeartbeat.last_beat_at >= stale_before)}
    max_attempts = _env_int('RUNNER_JOB_MAX_ATTEMPTS', 2)
    requeued = 0
    for job in Job.query.filter(Job.status == STATUS_RUNNING).with_for_update(skip_locked=True).all():
        if job.runner in live:
            continue
        lost_by = job.runner
        if (job.attempts or 0) < max_attempts:
            job.status = STATUS_QUEUED
            job.runner = None
            job.started_at = None
            requeued += 1
        else:
            job.status = STATUS_FAILED
            job.error = 'the runner stopped during the job'
            job.finished_at = utc_now()
        logger.warning('runner: job %s lost by %s, now %s', job.id, lost_by, job.status)
    db.session.commit()
    if requeued and not _notify({'job': 'requeued'}):
        _job_event.set()
    return requeued


def cleanup_jobs(wakes=None):
    """Delete finished jobs and their files after the retention time, and old runner rows."""
    now = utc_now()
    cutoff = now - timedelta(hours=_env_int('RUNNER_JOB_RETENTION_HOURS', 24))
    root = job_files_root()
    removed = 0
    for job in Job.query.filter(Job.status.in_(FINISHED_STATUSES), Job.finished_at < cutoff).limit(500).all():
        shutil.rmtree(os.path.join(root, str(job.id)), ignore_errors=True)
        db.session.delete(job)
        removed += 1
    RunnerHeartbeat.query.filter(
        RunnerHeartbeat.key.like(RUNNER_KEY_PREFIX + '%'),
        RunnerHeartbeat.updated_at < now - timedelta(days=1),
    ).delete(synchronize_session=False)
    db.session.commit()
    return removed


register_periodic('runner.reap', reap_lost_jobs, 60)
register_periodic('runner.cleanup', cleanup_jobs, 3600)


class _Leader(object):
    """The session advisory lock that picks the one runner that runs the periodic tasks."""

    def __init__(self, app):
        self.app = app
        self.conn = None
        self.is_leader = False
        self.lock = threading.Lock()

    def hold(self):
        """True when this process holds the leader lock. Tries to take it when it is free."""
        with self.lock:
            with self.app.app_context():
                engine = _pg_engine()
            if engine is None:
                return True
            try:
                if self.conn is None:
                    proxied = engine.raw_connection()
                    proxied.detach()
                    self.conn = proxied.dbapi_connection
                    self.conn.autocommit = True
                    self.is_leader = False
                with self.conn.cursor() as cur:
                    if self.is_leader:
                        cur.execute('SELECT 1')
                    else:
                        cur.execute('SELECT pg_try_advisory_lock(%s)', (LEADER_LOCK_KEY,))
                        self.is_leader = bool(cur.fetchone()[0])
                        if self.is_leader:
                            logger.info('runner: %s holds the leader lock', host_id())
                return self.is_leader
            except Exception as lock_err:
                logger.warning('runner: leader connection lost: %s', lock_err)
                self.release()
                return False

    def release(self):
        """Close the lock connection, which frees the lock."""
        conn, self.conn, self.is_leader = self.conn, None, False
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass


class Runner(object):
    """Threads of one runner: the listener, the job dispatcher and one loop per periodic task."""

    def __init__(self, app):
        self.app = app
        self.host = host_id()
        self.threads = max(_env_int('RUNNER_THREADS', 2), 1)
        self.poll = max(_env_int('RUNNER_POLL_SECONDS', 10), 1)
        self.stop_event = threading.Event()
        self.leader = _Leader(app)
        self.free = threading.Semaphore(self.threads)
        self.pool = ThreadPoolExecutor(self.threads, thread_name_prefix='runner-job')
        self.started_periodics = set()
        self.last_runner_beat = 0.0

    def start(self):
        """Write the start heartbeat and start the threads."""
        with self.app.app_context():
            if _write_beat(RUNNER_KEY_PREFIX + self.host, self.host, start=True):
                touch_beat_file()
        self._thread('runner-listen', self._listen_loop)
        self._thread('runner-dispatch', self._dispatch_loop)
        for periodic in list(_periodics.values()):
            self._thread('runner-' + periodic.name, self._periodic_loop, periodic)
        logger.info('runner: started on %s, %s job threads, job types %s, queue %s, periodic tasks %s',
                    self.host, self.threads, job_types(), runner_queue() or '-', sorted(_periodics))
        return self

    def stop(self, wait=False):
        """Stop the loops. Running jobs finish when wait is True."""
        self.stop_event.set()
        _job_event.set()
        with _wake_lock:
            events = list(_wake_events.values())
        for event in events:
            event.set()
        self.pool.shutdown(wait=wait)
        self.leader.release()

    def _thread(self, name, target, *args):
        thread = threading.Thread(target=target, args=args, name=name, daemon=True)
        thread.start()
        return thread

    def _listen_loop(self):
        delay = 1
        while not self.stop_event.is_set():
            dbapi_conn = None
            try:
                with self.app.app_context():
                    engine = _pg_engine()
                if engine is None:
                    logger.info('runner: no PostgreSQL engine, wakes stay in the process')
                    return
                proxied = engine.raw_connection()
                proxied.detach()
                dbapi_conn = proxied.dbapi_connection
                dbapi_conn.autocommit = True
                with dbapi_conn.cursor() as cur:
                    cur.execute('LISTEN ' + JOB_CHANNEL)
                logger.info('runner: listening on %s (%s)', JOB_CHANNEL, self.host)
                delay = 1
                _job_event.set()
                while not self.stop_event.is_set():
                    ready, _, _ = select.select([dbapi_conn], [], [], LISTEN_POLL_SECONDS)
                    if not ready:
                        with dbapi_conn.cursor() as cur:
                            cur.execute('SELECT 1')
                    dbapi_conn.poll()
                    while dbapi_conn.notifies:
                        handle_message(dbapi_conn.notifies.pop(0).payload)
            except Exception as listen_err:
                logger.warning('runner: LISTEN %s lost (%s), retry in %ss', JOB_CHANNEL, listen_err, delay)
            finally:
                if dbapi_conn is not None:
                    try:
                        dbapi_conn.close()
                    except Exception:
                        pass
            self.stop_event.wait(delay)
            delay = min(delay * 2, LISTEN_RETRY_MAX_SECONDS)

    def _dispatch_loop(self):
        _job_event.set()
        while not self.stop_event.is_set():
            _job_event.wait(self.poll)
            _job_event.clear()
            if self.stop_event.is_set():
                break
            self._beat_runner()
            while not self.stop_event.is_set() and self.free.acquire(blocking=False):
                with self.app.app_context():
                    job_id = claim_job(self.host)
                if job_id is None:
                    self.free.release()
                    break
                self.pool.submit(self._run_job, job_id)

    def _beat_runner(self):
        now = time.monotonic()
        if now - self.last_runner_beat < self.poll:
            return
        self.last_runner_beat = now
        with self.app.app_context():
            if _write_beat(RUNNER_KEY_PREFIX + self.host, self.host):
                touch_beat_file()

    def _run_job(self, job_id):
        try:
            with self.app.test_request_context('/'):
                run_job(job_id)
        except Exception:
            logger.exception('runner: job %s crashed', job_id)
        finally:
            self.free.release()
            _job_event.set()

    def _periodic_loop(self, periodic):
        event = _wake_event(periodic.name)
        next_due = time.monotonic()
        while not self.stop_event.is_set():
            event.wait(max(0.0, next_due - time.monotonic()))
            event.clear()
            if self.stop_event.is_set():
                break
            wakes = pop_wakes(periodic.name)
            due = time.monotonic() >= next_due
            if due:
                with self.app.app_context():
                    next_due = time.monotonic() + periodic.seconds()
            if not (wakes or due) or not self.leader.hold():
                continue
            try:
                with self.app.test_request_context('/'):
                    if periodic.name not in self.started_periodics:
                        self.started_periodics.add(periodic.name)
                        _write_beat(periodic_key(periodic.name), self.host, start=True)
                    if wakes:
                        run_periodic(periodic.name, wakes, beat=False, host=self.host)
                    if due:
                        run_periodic(periodic.name, (), beat=True, host=self.host)
            except Exception:
                logger.exception('runner: periodic loop %s failed', periodic.name)


def start_in_process(app):
    """Start the one runner of this process as threads. Returns it."""
    global _runner
    with _runner_lock:
        if _runner is None:
            _runner = Runner(app).start()
        return _runner


def run_forever(app):
    """Run the runner in the foreground until SIGTERM or SIGINT."""
    runner = start_in_process(app)
    stopping = threading.Event()
    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, lambda *_: stopping.set())
    while not stopping.wait(1):
        pass
    logger.info('runner: stopping')
    runner.stop(wait=False)
