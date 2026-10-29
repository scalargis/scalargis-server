import os
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from flask import current_app, has_app_context
from flask_restx import fields

DEFAULT_TIME_ZONE = 'Europe/Lisbon'


def utc_now():
    # To migrate to timezone-aware datetimes, remove .replace(tzinfo=None)
    return datetime.now(timezone.utc).replace(tzinfo=None)


def local_time_zone():
    """ZoneInfo of SCALARGIS_TIME_ZONE."""
    name = current_app.config.get('SCALARGIS_TIME_ZONE') if has_app_context() else None
    return ZoneInfo(name or DEFAULT_TIME_ZONE)


def local_now():
    """Naive datetime of now in SCALARGIS_TIME_ZONE."""
    return datetime.now(local_time_zone()).replace(tzinfo=None)


def local_today():
    """Date of today in SCALARGIS_TIME_ZONE."""
    return datetime.now(local_time_zone()).date()


def iso_utc(dt):
    """ISO 8601 text with Z of a naive UTC or an aware datetime."""
    if dt is None:
        return None
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt.isoformat() + 'Z'


def to_utc_naive(value):
    """Naive UTC datetime of an ISO 8601 text or a datetime. A value with no offset is UTC."""
    if value is None or value == '':
        return None
    if isinstance(value, str):
        value = datetime.fromisoformat(value)
    if value.tzinfo is not None:
        value = value.astimezone(timezone.utc).replace(tzinfo=None)
    return value


class UtcDateTime(fields.DateTime):
    """DateTime field that sends a naive UTC value as ISO 8601 with Z."""

    def format_iso8601(self, dt):
        return iso_utc(dt)


def to_bool(bool_str):
    """Parse the string and return the boolean value encoded or raise an exception"""
    if isinstance(bool_str, str):
        if bool_str.lower() in ['true', 't', '1']: return True
        elif bool_str.lower() in ['false', 'f', '0']: return False

    return None


def get_file_path(base_path, path, filename):
    filepath = None
    if os.path.isfile(os.path.abspath(filename)):
        filepath = os.path.abspath(filename)
    elif base_path and os.path.isfile(os.path.join(base_path, filename)):
        filepath = os.path.join(base_path, filename)
    elif base_path and path and os.path.isfile(os.path.join(base_path, path, filename)):
        filepath = os.path.join(base_path, path, filename)

    return filepath
