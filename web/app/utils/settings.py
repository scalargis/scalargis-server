import logging
from flask import current_app
from app.database import db
from app.models.mapas import SiteSettings

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