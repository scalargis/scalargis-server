"""Core background runner. Extensions register job types and periodic tasks here."""
from .runner import (
    JOB_CHANNEL,
    MODE_EXTERNAL,
    JobContext,
    enqueue,
    job_types,
    periodic_key,
    register_job_type,
    register_periodic,
    run_forever,
    run_periodic,
    runner_mode,
    start_in_process,
    wake,
)


def init_app(flask_app, start_runner=True):
    """Start the in-process runner unless start_runner is False or RUNNER_MODE is external."""
    if start_runner and runner_mode() != MODE_EXTERNAL:
        start_in_process(flask_app)
