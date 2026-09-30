"""Core background runner. Extensions register job types and periodic tasks here."""
from .runner import (
    JOB_CHANNEL,
    LOCAL_QUEUE_PREFIX,
    MODE_EXTERNAL,
    JobContext,
    configure,
    enqueue,
    job_types,
    local_mode,
    periodic_enabled,
    periodic_key,
    register_job_type,
    register_periodic,
    run_forever,
    run_periodic,
    runner_mode,
    runner_queue,
    start_in_process,
    wake,
)
from .requests import REQUEST_KEY, capture_request, job_user, plain_result, replay_request


def init_app(flask_app, start_runner=True):
    """Read the runner settings, then start the in-process runner unless start_runner is False or RUNNER_MODE is external."""
    configure(flask_app)
    if start_runner and runner_mode() != MODE_EXTERNAL:
        start_in_process(flask_app)
