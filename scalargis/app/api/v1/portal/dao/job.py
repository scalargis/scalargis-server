import uuid

from flask_security import current_user

from app.database import db
from app.models.runner import Job
from app.utils.constants import ROLE_ADMIN
from ...endpoints import get_user


def get_readable_by_id(request, id):
    """The job when the caller made it or is an admin. A job with no user is readable by its id."""
    try:
        job_id = uuid.UUID(str(id))
    except ValueError:
        return None
    job = db.session.get(Job, job_id)
    if job is None or job.created_by is None:
        return job
    user = get_user(request)
    if user is None and current_user and current_user.is_authenticated:
        user = current_user
    if user is None:
        return None
    if user.id == job.created_by or any(r.name == ROLE_ADMIN for r in user.roles):
        return job
    return None
