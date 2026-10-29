import json

from sqlalchemy import text

from app.database import db
from app import get_db_schema
from app.utils import local_time_zone
from app.utils.security import is_admin_or_manager
from ...endpoints import get_user


db_schema = get_db_schema()


def get_viewer_visits(request):
    """
    Returns viewer visits
    """

    type_code = request.values['type_code']
    viewer_id = request.values.get('viewer_id')

    user = get_user(request)

    owner_id = None
    if user and not is_admin_or_manager(user):
        owner_id = user.id

    rows = db.session.execute(text(
        """
        select timezone(:tz, timezone('UTC', avl.date_ref))::date as dt, count(*) as c
        from {schema}.audit_log avl
        left join {schema}.audit_operation ao on (avl.operation_id = ao.id)
        left join {schema}.viewers vw on (avl.id_viewer = vw.id)
        where ao.code like :type_code
        and (vw.owner_id = :owner_id or cast(:owner_id as integer) is null)
        and (vw.id = :viewer_id or cast(:viewer_id as integer) is null)
        group by 1
        order by 1
        """.format(schema=db_schema)),
        {'tz': local_time_zone().key, 'type_code': type_code, 'owner_id': owner_id, 'viewer_id': viewer_id})

    values = [{'date': dt.isoformat(), 'count': c} for dt, c in rows]
    return {'type': 'collection', 'values': values or None}


def get_viewer_owner_visits(request):
    """
    Returns viewer visits
    """

    user = get_user(request)

    owner_id = user.id
    data = db.session.execute(text(
        """
        Select *
        from {schema}.get_viewer_owner_day_stats(:owner_id)
        """.format(schema=db_schema)), {'owner_id': owner_id})

    return json.loads(data.fetchall()[0][0])


def get_basic_stats(request):
    """
    Returns basic stats
    """

    data = db.session.execute(text("Select {schema}.get_platform_basic_stats()".format(schema=db_schema)))
    d = data.fetchall()

    return json.loads(d[0][0])
