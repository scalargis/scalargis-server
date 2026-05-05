import ipaddress
import logging
from datetime import datetime, timedelta

from flask import current_app

from app.database import db
from app.models.login_attempt import LoginAttemptIP

logger = logging.getLogger(__name__)

_DEFAULT_WHITELIST = [
    ipaddress.ip_network("127.0.0.1/32"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
]


def _get_threshold():
    return current_app.config.get("SCALARGIS_LOGIN_BLOCK_THRESHOLD", 100)


def _get_block_duration_minutes():
    return current_app.config.get("SCALARGIS_LOGIN_BLOCK_DURATION_MINUTES", 30)


def is_whitelisted(ip):
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        logger.warning("[login_blocking] unparseable IP address: %s", ip)
        return False
    for network in _DEFAULT_WHITELIST:
        if addr in network:
            return True
    return False


def check_ip_blocked(ip):
    """
    Returns (is_blocked, retry_after_seconds).
    If the block has expired, auto-resets the record.
    """
    if is_whitelisted(ip):
        return False, 0

    row = db.session.query(LoginAttemptIP).get(ip)
    if row is None:
        return False, 0

    if row.blocked_until is not None:
        now = datetime.utcnow()
        if row.blocked_until > now:
            seconds_remaining = int((row.blocked_until - now).total_seconds()) + 1
            logger.info(
                "[login_blocking] blocked request from %s — %d seconds remaining",
                ip, seconds_remaining,
            )
            return True, seconds_remaining
        else:
            _reset_row(row)
            return False, 0

    return False, 0


def record_failure(ip):
    if is_whitelisted(ip):
        return

    threshold = _get_threshold()
    block_minutes = _get_block_duration_minutes()
    now = datetime.utcnow()

    row = db.session.query(LoginAttemptIP).get(ip)

    if row is None:
        row = LoginAttemptIP(
            ip_address=ip,
            failed_count=1,
            last_failed_at=now,
            blocked_until=None,
        )
    else:
        row.failed_count = (row.failed_count or 0) + 1
        row.last_failed_at = now

    if row.failed_count >= threshold:
        row.blocked_until = now + timedelta(minutes=block_minutes)
        logger.warning(
            "[login_blocking] IP %s blocked for %d minutes after %d failures",
            ip, block_minutes, row.failed_count,
        )

    db.session.merge(row)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        logger.exception("[login_blocking] DB error recording failure for %s", ip)


def record_success(ip):
    if is_whitelisted(ip):
        return

    row = db.session.query(LoginAttemptIP).get(ip)
    if row is not None and (row.failed_count or 0) > 0:
        _reset_row(row)


def _reset_row(row):
    row.failed_count = 0
    row.last_failed_at = None
    row.blocked_until = None
    db.session.merge(row)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        logger.exception(
            "[login_blocking] DB error resetting record for %s", row.ip_address
        )
