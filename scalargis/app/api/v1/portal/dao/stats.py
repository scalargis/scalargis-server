import json

from sqlalchemy import text

from app.database import db
from app.utils.security import is_admin_or_manager
from ...endpoints import get_user


def get_viewer_visits(request):
    """
    Returns viewer visits
    """

    type_code = request.values['type_code']

    user = get_user(request)

    owner_id = None
    if user and not is_admin_or_manager(user):
        owner_id = user.id

    data = db.session.execute(text(
        """
        Select * 
        from portal.get_platform_day_stats(:type_code, :owner_id)
        """),
        {'type_code': type_code, 'owner_id': owner_id})

    return json.loads(data.fetchall()[0][0])


def get_viewer_owner_visits(request):
    """
    Returns viewer visits
    """

    user = get_user(request)

    owner_id = user.id
    data = db.session.execute(text(
        """
        Select *
        from portal.get_viewer_owner_day_stats(:owner_id)
        """), {'owner_id': owner_id})

    return json.loads(data.fetchall()[0][0])


def get_basic_stats(request):
    """
    Returns basic stats
    """

    data = db.session.execute(text("Select portal.get_platform_basic_stats()"))
    d = data.fetchall()

    return json.loads(d[0][0])
