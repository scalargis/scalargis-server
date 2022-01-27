import json
#import importlib
from datetime import datetime
from flask import request
import sqlalchemy
from sqlalchemy import Integer,cast
from sqlalchemy import sql, or_, and_
from sqlalchemy.exc import IntegrityError
from ..parsers import *
from app.models.domain.portal import *
from app.models.mapas import SiteSettings
from app.utils import constants
from app.utils.security import is_admin_or_manager
from ...endpoints import get_user


def getViewerVisits(request):
    """
    Returns viewer visits
    """

    type_code = request.values['type_code']

    user = get_user(request)

    owner_id = None
    if user and not is_admin_or_manager(user):
        owner_id = user.id

    data = db.session.execute(
        """
        Select * 
        from portal.get_platform_day_stats(:type_code, :owner_id)
        """, {'type_code': type_code, 'owner_id': owner_id})

    return json.loads(data.fetchall()[0][0])


def getViewerOwnerVisits(request):
    """
    Returns viewer visits
    """

    user = get_user(request)

    owner_id = user.id
    data = db.session.execute(
        """
        Select *
        from portal.get_viewer_owner_day_stats(:owner_id)
        """, {'owner_id': owner_id})

    return json.loads(data.fetchall()[0][0])


def getBasicStats(request):
    """
    Returns basic stats
    """

    data = db.session.execute(
        """
        Select portal.get_platform_basic_stats()
        """)
    d = data.fetchall()

    return json.loads(d[0][0])