import datetime

from app.database import db
from app import get_db_schema
from .common import PortalTable


db_schema = get_db_schema()


class LoginAttemptIP(db.Model, PortalTable):
    __tablename__ = "login_attempt_ip"

    ip_address = db.Column(db.String(45), primary_key=True)
    failed_count = db.Column(db.Integer, nullable=False, default=0)
    last_failed_at = db.Column(db.DateTime, nullable=True)
    blocked_until = db.Column(db.DateTime, nullable=True)


class LoginAuditLog(db.Model, PortalTable):
    __tablename__ = "login_audit_log"

    id = db.Column(db.Integer(), primary_key=True)
    ip_address = db.Column(db.String(45), nullable=False, index=True)
    attempted_username = db.Column(db.String(255), nullable=False, index=True)
    success = db.Column(db.Boolean(), nullable=False, default=False)
    failure_reason = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime(), nullable=False, default=datetime.datetime.now, index=True)
