"""Core background runner. Extensions register job types and periodic tasks here."""
import logging

from .runner import (
    JOB_CHANNEL,
    LOCAL_QUEUE_PREFIX,
    ENTRY_GUNICORN,
    ENTRY_SERVER,
    ENTRY_SERVICES,
    ENTRY_WORKER,
    MODE_EXTERNAL,
    JobContext,
    RoleError,
    configure,
    enqueue,
    job_types,
    local_mode,
    periodic_enabled,
    periodic_key,
    register_job_type,
    register_periodic,
    role,
    run_forever,
    run_periodic,
    runner_mode,
    runner_queue,
    start_in_process,
    wake,
)
from .requests import REQUEST_KEY, capture_request, job_user, plain_result, replay_request

logger = logging.getLogger(__name__)


def check_role(flask_app, entry):
    """Read the runner settings and return the role of this process. Raises RoleError for a role that orphans jobs."""
    configure(flask_app)
    try:
        name = role(entry)
    except RoleError as role_err:
        logger.error('runner: %s refuses to start: %s', entry, role_err)
        raise
    logger.info('runner: %s starts as %s', entry, name)
    return name


def init_app(flask_app, start_runner=True):
    """Read the runner settings, then start the in-process runner unless start_runner is False or RUNNER_MODE is external."""
    configure(flask_app)
    if start_runner and runner_mode() != MODE_EXTERNAL:
        start_in_process(flask_app)
