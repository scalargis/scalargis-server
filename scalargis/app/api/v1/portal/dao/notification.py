import os
import json
import uuid
from datetime import datetime, timedelta
from mimetypes import guess_type
import re
import base64

from flask import request, current_app, make_response, send_file
import sqlalchemy
from sqlalchemy import Date, Integer, cast, and_, or_, desc
from sqlalchemy.exc import IntegrityError

from app.database import db
from ..parsers import *
from app.models.portal import Viewer, ContactMessage
from ...endpoints import check_user, get_user
from . import get_record_by_id
from sqlalchemy.exc import IntegrityError
from app.utils.constants import ROLE_ANONYMOUS, ROLE_AUTHENTICATED, ROLE_ADMIN, ROLE_MANAGER
from app.utils.security import is_admin_or_manager
from app.utils.settings import get_config_value
from instance import settings


def get_by_filter(request):
    """
    Returns paged list of Notifications
    """
    args = parser_records_with_page.parse_args(request)
    page = args.get('page', 1)
    per_page = args.get('per_page', 10)
    filter = json.loads(args.get('filter') or '{}')

    sort_fields = {
        'date': 'message_date'
    }

    user = get_user(request)

    if user is None or user.id is None:
        return None

    roles = [r.name for r in user.roles]

    #qy = ContactMessage.query.outerjoin(Viewer, ContactMessage.viewer_id == Viewer.id)
    qy = ContactMessage.query.outerjoin(Viewer)

    if not is_admin_or_manager(user):
        #qy = ContactMessage.query.join(Viewer).filter(Viewer.owner_id == user.id)
        qy = ContactMessage.query.join(Viewer).\
            filter(or_(Viewer.owner_id == user.id, Viewer.notifications_manager_roles.overlap(roles)))


    key = 'id'
    if key in filter:
        qy = qy.filter(cast(ContactMessage.id, sqlalchemy.String).ilike(str(filter[key])))

    key = 'viewer'
    if key in filter:
        values = filter[key] if isinstance(filter[key], list) else [filter[key]]
        if values and len(values):
            qy = qy.filter(ContactMessage.viewer_id.in_(values))

    key = 'author'
    if key in filter:
        qy = qy.filter(or_(ContactMessage.name.ilike(str(filter[key])),
                           ContactMessage.email.ilike(str(filter[key]))))

    key = 'message'
    if key in filter:
        qy = qy.filter(ContactMessage.message.ilike(str(filter[key])))

    key = 'status'
    if key in filter:
        conditions = []
        values = filter[key] if isinstance(filter[key], list) else [filter[key]]
        for val in values:
            if val == 0:
                conditions.append(and_(
                    ContactMessage.checked.op("IS NOT")(True), ContactMessage.closed.op("IS NOT")(True)))
            if val == 1:
                conditions.append(
                    and_(ContactMessage.checked.op("IS")(True), ContactMessage.closed.op("IS NOT")(True)))
            if val == 2:
                conditions.append(ContactMessage.closed.op("IS")(True))

        qy = qy.filter(or_(*conditions))

    if 'start_date' in filter and 'end_date' in filter:
        start_date = datetime.fromisoformat(filter['start_date'].replace('Z',''))
        end_date = datetime.fromisoformat(filter['end_date'].replace('Z','')) + timedelta(days=1)
        qy = qy.filter(ContactMessage.message_date >= start_date). \
            filter(ContactMessage.message_date <= end_date)
    elif 'start_date' in filter:
        start_date = datetime.fromisoformat(filter['start_date'].replace('Z', ''))
        qy = qy.filter(ContactMessage.message_date >= start_date)
    elif 'end_date' in filter:
        end_date = datetime.fromisoformat(filter['end_date'].replace('Z','')) + timedelta(days=1)
        qy = qy.filter(ContactMessage.message_date <= end_date)


    sort = json.loads(args.get('sort') or '[]')
    if len(sort) > 0:
        for i in range(0, len(sort), 2):
            order = None
            if sort[i] == 'viewer':
                s = 1
                order = getattr(getattr(Viewer, 'name'), sort[i + 1].lower())()
                # order = getattr(getattr(EstadoPlano, 'designacao'), sort[i+1].lower())()
            elif sort[i]:
                kf = sort[i]
                if sort[i] in sort_fields:
                    kf = sort_fields.get(sort[i])
                order = getattr(getattr(ContactMessage, kf), sort[i+1].lower())()

            if order is not None:
                qy = qy.order_by(order)

    page = qy.paginate(page=page, per_page=per_page, error_out=False)
    return page


def get_by_id(id):

    user = get_user(request)

    if user is None or user.id is None:
        return None

    data = get_record_by_id(ContactMessage, id)

    if data is None:
        return None

    user_roles = [r.name for r in user.roles]

    if not is_admin_or_manager(user) and data.viewer.owner_id != user.id:
        if not (set(user_roles or []) & set(data.viewer.notifications_manager_roles or [])):
            return None

    return data


def get_new_notifications():
    user = get_user(request)


    if user is None or user.id is None:
        return None

    roles = [r.name for r in user.roles]

    qy = db.session.query(ContactMessage.id).outerjoin(Viewer)
    if not is_admin_or_manager(user):
        qy = db.session.query(ContactMessage.id).join(Viewer).\
            filter(or_(Viewer.owner_id == user.id, Viewer.notifications_manager_roles.overlap(roles)))

    qy = qy.filter(and_(ContactMessage.checked.op("IS NOT")(True), ContactMessage.closed.op("IS NOT")(True)))

    total = qy.count()

    return total


def update(id, data):
    user = get_user(request)

    if user is None or user.id is None:
        return None

    record = ContactMessage.query.filter(ContactMessage.id == id).one_or_none()

    if not record:
        return None

    if record:
        user_roles = [r.name for r in user.roles]

        if not is_admin_or_manager(user) and record.viewer.owner_id != user.id:
            if not (set(user_roles or []) & set(record.viewer.notifications_manager_roles or [])):
                return None

        fields = {
            "checked": "checked",
            "checked_date": "checked_date",
            "closed": "closed",
            "closed_date": "closed_date",
            "notes": "notes"
        }

        for key in data.keys():
            if hasattr(record, fields.get(key)):
                if data.get(key) == '':
                    setattr(record, fields.get(key), None)
                else:
                    setattr(record, fields.get(key), data.get(key))

        db.session.add(record)
        db.session.commit()
        db.session.refresh(record)

    return record


def get_file(id, filename):
    user = get_user(request)

    # TODO
    #if user is None or user.id is None:
    #    return None, None

    record = get_record_by_id(ContactMessage, id)

    if not record:
        return None, None

    # TODO
    #if not is_admin_or_manager(user) and record.viewer.owner_id != user.id:
    #    return None, None

    message_uuid = record.message_uuid

    folder_path = None

    if os.path.exists(get_config_value('EMAIL_NOTIFICATIONS_FOLDER')):
        folder_path = get_config_value('EMAIL_NOTIFICATIONS_FOLDER')
    elif os.path.exists(get_config_value('APP_UPLOADS')):
        folder_path = os.path.join(get_config_value('APP_UPLOADS'), 'notifications')
    elif os.path.exists(get_config_value('APP_TMP_DIR')):
        folder_path = os.path.join(get_config_value('APP_TMP_DIR'), 'notifications')

    if folder_path:
        folder_path = os.path.join(folder_path, message_uuid)

    data = None
    files = []

    if isinstance(record.message_json, dict):
        data = record.message_json
    else:
        if record.message_json is not None and record.message_json != '':
            data = json.loads(record.message_json)

    if folder_path:
        filepath = os.path.join(folder_path, filename)

        if os.path.exists(filepath):
            try:
                response = make_response(send_file(filepath, attachment_filename=os.path.basename(filepath)))
                response.headers['Content-Type'] = guess_type(filename)
                # response.headers['Content-Disposition'] = 'attachment; filename={0}'.format(filename)
                response.headers['Content-Disposition'] = 'filename={0}'.format(filename)

                return response, None
            except Exception as e:
                pass #return {"message": "Internal Server Error"}, 500

    if data and 'files' in data:
        try:
            file = next((f for f in data['files'] if f["filename"] == filename), None)
            if file and file['data']:
                file_data = re.match("data:(?P<type>.*?);(?P<encoding>.*?),(?P<data>.*)",
                                     file.get('data')).groupdict()

                output = base64.b64decode(file_data['data'])

                response = make_response(output)
                response.headers['Content-Type'] = guess_type(filename)
                # response.headers['Content-Disposition'] = 'attachment; filename={0}'.format(filename)
                response.headers['Content-Disposition'] = 'filename={0}'.format(filename)

                return response, None
        except Exception as e:
            return {"message": "Internal Server Error"}, 500

    return None, None


def get_viewers_list(request):
    user = get_user(request)

    if user is None or user.id is None:
        return []

    data = []

    user_roles = [r.name for r in user.roles]

    records = db.session.query(Viewer.id, Viewer.name, Viewer.owner_id, Viewer.notifications_manager_roles).\
        order_by('name').all()

    for r in records:
        if is_admin_or_manager(user) or r.owner_id == user.id:
            data.append({"id": r.id, "name": r.name})
        elif set(user_roles or []) & set(r.notifications_manager_roles or []):
            data.append({"id": r.id, "name": r.name})

    return data
