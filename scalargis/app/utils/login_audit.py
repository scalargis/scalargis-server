import logging

from app.database import db
from app.models.login_attempt import LoginAuditLog
from app.utils import constants


def log_login_attempt(ip, username, success, failure_reason=None):
    logger = logging.getLogger(__name__)

    try:
        se = db.session

        record = LoginAuditLog()
        record.ip_address = ip
        record.attempted_username = username
        record.success = success
        record.failure_reason = failure_reason

        se.add(record)
        se.commit()
    except Exception as e:
        se.rollback()
        logger.error(constants.LOGIN_AUDIT_INSERT_ERROR + ': ' + str(e))
