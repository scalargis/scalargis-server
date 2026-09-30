"""The print.planta job: a viewer print that the background runner generates."""
from app import runner

JOB_TYPE = 'print.planta'


def run_print_planta(ctx):
    """Generate the print of the captured request. The result has the body of the synchronous endpoint."""
    from app.modules.print.controllers import viewer_generate_pdf
    user = runner.job_user(ctx.created_by)
    with runner.replay_request(ctx.payload[runner.REQUEST_KEY], user):
        return runner.plain_result(viewer_generate_pdf(ctx.payload['print_code'], user))


def start_print_planta(req, print_code, user):
    """Queue a print.planta job for req. Returns the job id."""
    payload = {'print_code': print_code, runner.REQUEST_KEY: runner.capture_request(req)}
    return runner.enqueue(JOB_TYPE, payload, created_by=user.id if user else None)


def register():
    """Register the print.planta job type with the runner."""
    runner.register_job_type(JOB_TYPE, run_print_planta)
