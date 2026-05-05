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
