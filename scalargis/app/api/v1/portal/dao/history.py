import json

from flask_restx import abort

from app.database import db
from app.models.portal import RecordHistory
from app.models.security import User
from app.utils import utc_now, iso_utc, to_utc_naive


KEEP = 5

ORIGIN_BACKOFFICE = 'backoffice'
ORIGIN_VIEWER = 'visualizador'

VIEWER_FIELDS = (
    'id', 'name', 'title', 'description', 'keywords', 'author', 'lang', 'slug', 'bbox', 'maxbbox',
    'config_version', 'is_active', 'is_shared', 'allow_user_session', 'allow_sharing', 'default_component',
    'show_help', 'show_credits', 'show_contact', 'on_homepage', 'img_homepage', 'img_logo', 'img_logo_alt',
    'img_icon', 'send_email_notifications_admin', 'email_notifications_admin', 'owner_id', 'custom_script',
    'custom_style', 'notifications_manager_roles',
)
VIEWER_JSON_FIELDS = ('config_json', 'styles', 'scripts', 'manifest_json')

SITE_SETTING_FIELDS = ('id', 'code', 'name', 'notes', 'setting_value', 'active', 'read_only')

PRINT_COMMON_FIELDS = (
    'id', 'code', 'name', 'title', 'description', 'is_active', 'form_fields', 'allow_drawing', 'location_marking',
    'draw_location', 'free_printing', 'show_author', 'payment_reference', 'print_purpose', 'restrict_scales',
    'restrict_scales_list', 'free_scale', 'map_scale', 'multi_geom', 'tolerance_filter',
)
PRINT_FIELDS = PRINT_COMMON_FIELDS + ('scale', 'srid', 'format', 'orientation', 'owner_id')
PRINT_GROUP_FIELDS = PRINT_COMMON_FIELDS + ('select_prints', 'group_prints', 'show_all_prints', 'owner_id')

PRINT_ELEMENT_FIELDS = ('id', 'code', 'name', 'config')


def _json(value):
    if value is None or value == '' or not isinstance(value, str):
        return value
    try:
        return json.loads(value)
    except ValueError:
        return value


def _fields(record, names):
    return {name: getattr(record, name, None) for name in names if hasattr(type(record), name)}


def _layouts(record):
    return [{'format': lt.format, 'orientation': lt.orientation, 'config': lt.config} for lt in record.layouts]


def _geometry(record):
    return {'geom_filter': record.geometry_wkt, 'geom_filter_srid': record.geometry_srid}


def _viewer(record):
    data = _fields(record, VIEWER_FIELDS)
    data['keywords'] = list(data['keywords']) if data.get('keywords') is not None else None
    data['notifications_manager_roles'] = list(data['notifications_manager_roles']) \
        if data.get('notifications_manager_roles') is not None else None
    for name in VIEWER_JSON_FIELDS:
        data[name] = _json(getattr(record, name))
    data['roles'] = sorted(role.id for role in record.roles)
    data['prints'] = [link.print_id for link in sorted(record.print_assoc, key=lambda a: a.order or 0)]
    data['print_groups'] = [link.print_group_id
                            for link in sorted(record.print_group_assoc, key=lambda a: a.order or 0)]
    return data


def _site_setting(record):
    return _fields(record, SITE_SETTING_FIELDS)


def _print(record):
    data = _fields(record, PRINT_FIELDS)
    data['config_json'] = _json(record.config_json)
    data['form_fields'] = _json(data.get('form_fields'))
    data.update(_geometry(record))
    data['layouts'] = _layouts(record)
    data['roles'] = sorted(role.id for role in record.roles)
    return data


def _print_group(record):
    data = _fields(record, PRINT_GROUP_FIELDS)
    data['form_fields'] = _json(data.get('form_fields'))
    data.update(_geometry(record))
    data['layouts'] = _layouts(record)
    data['roles'] = sorted(role.id for role in record.roles)
    data['groups'] = [link.print_group_child_id
                      for link in sorted(record.print_group_child_assoc, key=lambda a: a.order or 0)]
    data['prints'] = [link.print_id for link in sorted(record.print_assoc, key=lambda a: a.order or 0)]
    return data


def _print_element(record):
    return _fields(record, PRINT_ELEMENT_FIELDS)


BUILDERS = {
    'viewer': _viewer,
    'site_setting': _site_setting,
    'print': _print,
    'print_group': _print_group,
    'print_element': _print_element,
}


def snapshot(entity, record):
    """Returns the record state as a JSON text with sorted keys."""
    return json.dumps(BUILDERS[entity](record), sort_keys=True, default=str, ensure_ascii=False)


def keep(entity, record, before, origin, user):
    """Adds a history row with the state before when the save changed the record, and keeps the newest KEEP rows."""
    db.session.flush()
    db.session.expire(record)
    if snapshot(entity, record) == before:
        return False
    db.session.add(RecordHistory(entity=entity, record_id=record.id, snapshot=before, origin=origin,
                                 id_user=user.id if user else None, created_at=utc_now()))
    db.session.flush()
    old = RecordHistory.query.filter(RecordHistory.entity == entity, RecordHistory.record_id == record.id) \
        .order_by(RecordHistory.created_at.desc(), RecordHistory.id.desc()).offset(KEEP).all()
    for row in old:
        db.session.delete(row)
    return True


def forget(entity, record_ids):
    """Deletes the history rows of the given records in the session of the caller."""
    ids = [rid for rid in record_ids if rid is not None]
    if ids:
        RecordHistory.query.filter(RecordHistory.entity == entity, RecordHistory.record_id.in_(ids)) \
            .delete(synchronize_session=False)


def _user_name(user_id):
    if user_id is None:
        return None
    user = db.session.get(User, user_id)
    return user.username if user else None


def check_stale(record, data):
    """Aborts with 409 when data holds an updated_at that differs from the stored one."""
    if not isinstance(data, dict) or 'updated_at' not in data:
        return
    try:
        sent = to_utc_naive(data.get('updated_at'))
    except (TypeError, ValueError):
        abort(400, 'updated_at is not an ISO 8601 date')
    if sent == record.updated_at:
        return
    abort(409, 'The record changed after it was loaded', error='stale_record',
          updated_at=iso_utc(record.updated_at), user=_user_name(record.id_user_update))


def history_list(entity, record_id):
    """Returns the history rows of a record, newest first, with no snapshot."""
    rows = db.session.query(RecordHistory.id, RecordHistory.created_at, RecordHistory.origin, User.username) \
        .outerjoin(User, User.id == RecordHistory.id_user) \
        .filter(RecordHistory.entity == entity, RecordHistory.record_id == record_id) \
        .order_by(RecordHistory.created_at.desc(), RecordHistory.id.desc()).all()
    return [{'id': r.id, 'date': iso_utc(r.created_at), 'user': r.username, 'origin': r.origin} for r in rows]


def history_get(entity, record_id, history_id):
    """Returns one history row of a record with its snapshot, or None."""
    row = RecordHistory.query.filter(RecordHistory.id == history_id, RecordHistory.entity == entity,
                                     RecordHistory.record_id == record_id).one_or_none()
    if row is None:
        return None
    return {'id': row.id, 'date': iso_utc(row.created_at), 'user': _user_name(row.id_user), 'origin': row.origin,
            'snapshot': json.loads(row.snapshot)}


def respond(entity, record, history_id, allowed):
    """Returns the body and the status of a history route: the list, or one row when history_id is set."""
    if record is None:
        return {'message': 'Record not found'}, 404
    if not allowed:
        return {'message': 'Forbidden'}, 403
    if history_id is None:
        return history_list(entity, record.id), 200
    item = history_get(entity, record.id, history_id)
    if item is None:
        return {'message': 'History row not found'}, 404
    return item, 200
