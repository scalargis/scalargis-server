import logging
from flask import current_app
from sqlalchemy import func

from app.database import db
from instance import settings
from app.models.portal import SiteSettings


def get_site_settings(key=None):
    site_settings = {}

    if key:
        query = SiteSettings.query
        st = query.filter(SiteSettings.code.ilike(key)).all()
    else:
        st = db.session.query(SiteSettings).all()

    for r in st:
        if r.setting_value:
            site_settings[r.code.lower()] = r.setting_value

    return site_settings


def get_site_setting_value(key):
    """Returns the setting_value of the site_settings row whose code is key, with case ignored."""
    rows = db.session.query(SiteSettings.setting_value).filter(func.lower(SiteSettings.code) == key.lower()).all()
    values = [r.setting_value for r in rows if r.setting_value]
    return values[-1] if values else None


def get_config_value(key):
    config_value = None

    if key in current_app.config:
        config_value = current_app.config[key]
    if 'SCALARGIS_{0}'.format(key or '') in current_app.config:
        config_value = current_app.config['SCALARGIS_{0}'.format(key or '')]
    if hasattr(settings, key):
        config_value = getattr(settings, key)
    db_value = get_site_setting_value(key)
    if db_value:
        config_value = db_value

    return config_value


def get_default_locale():
    return current_app.config.get('SCALARGIS_DEFAULT_LOCALE') or ''
