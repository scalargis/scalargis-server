import logging
from flask import current_app
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


def get_config_value(key):
    config_value = None

    site_settings_db = get_site_settings()

    if key in current_app.config:
        config_value = current_app.config[key]
    if 'SCALARGIS_{0}'.format(key or '') in current_app.config:
        config_value = current_app.config['SCALARGIS_{0}'.format(key or '')]
    if hasattr(settings, 'key'):
        config_value = settings.get(key)
    if key.lower() in site_settings_db:
        config_value = site_settings_db[key.lower()]

    return config_value