from sqlalchemy.dialects.postgresql import JSONB

from app.database import db
from app.utils import utc_now
from .common import PortalTable

JSON_TYPE = db.JSON().with_variant(JSONB(), 'postgresql')

STATUS_QUEUED = 'queued'
STATUS_RUNNING = 'running'
STATUS_DONE = 'done'
STATUS_FAILED = 'failed'
FINISHED_STATUSES = (STATUS_DONE, STATUS_FAILED)


class Job(db.Model, PortalTable):
    """One unit of background work, queued by a request and run by the runner."""
    __tablename__ = 'job'
    __table_args__ = (
        db.Index('ix_job_status_created_at', 'status', 'created_at'),
        PortalTable.__table_args__,
    )

    id = db.Column(db.Uuid(), primary_key=True)
    type = db.Column(db.String(100), nullable=False)
    payload = db.Column(JSON_TYPE)
    status = db.Column(db.String(20), nullable=False, default=STATUS_QUEUED)
    result = db.Column(JSON_TYPE)
    result_path = db.Column(db.Text())
    error = db.Column(db.Text())
    attempts = db.Column(db.Integer(), nullable=False, default=0)
    runner = db.Column(db.String(255))
    created_by = db.Column(db.Integer())
    created_at = db.Column(db.DateTime(), nullable=False, default=utc_now)
    started_at = db.Column(db.DateTime())
    finished_at = db.Column(db.DateTime())


class RunnerHeartbeat(db.Model, PortalTable):
    """Liveness row of a runner process or of a periodic task."""
    __tablename__ = 'runner_heartbeat'

    key = db.Column(db.String(255), primary_key=True)
    host = db.Column(db.String(255))
    started_at = db.Column(db.DateTime())
    last_beat_at = db.Column(db.DateTime())
    beat_count = db.Column(db.BigInteger(), nullable=False, default=0)
    last_error = db.Column(db.Text())
    updated_at = db.Column(db.DateTime(), default=utc_now, onupdate=utc_now)

