import json

from flask import url_for
from flask_restx import fields
from app.api.restx import api

from ..serializers import pagination


class NotificationStatus(fields.Raw):
    def output(self, key, obj, *args, **kwargs):
        '''
        try:
            dct = getattr(obj, self.attribute)
        except AttributeError:
            return {}
        return dct or {}
        '''
        if not obj:
            return None

        if not obj.checked and not obj.closed:
            return { "value": 0, "label": "Por abrir", "date": None }
        elif obj.checked and not obj.closed:
            return {"value": 1, "label": "Lida", "date": obj.checked_date.isoformat()}
        elif obj.closed:
            return {"value": 2, "label": "Encerrada", "date": obj.closed_date.isoformat()}
        else:
            return None


class NotificationFiles(fields.Raw):
    def output(self, key, obj, *args, **kwargs):
        data = None
        files = []

        if not obj:
            return None

        if isinstance(obj.message_json, dict):
            data = obj.message_json
        else:
            if obj.message_json is not None and obj.message_json != '':
                data = json.loads(obj.message_json)

        if data and 'files' in data and data['files']:
            for f in data['files']:
                url = url_for('api.portal_notification_file', id=obj.id, filename=f['filename'])
                files.append({"filename": f['filename'], "type": f['type'], "size": f['size'],"url": url})

        return files


notification_api_model = api.model('Notification Simple Model', {
    'id': fields.Integer(readOnly=True, description='Identifier'),
    'viewer': fields.String(required=False, attribute='viewer.name', description='Viewer name'),
    'date': fields.Date(required=True, attribute='message_date', description='Date'),
    'name': fields.String(required=False, attribute='name', description='Author name'),
    'email': fields.String(required=True, attribute='email', description='Author username'),
    'message': fields.String(required=True, attribute='message', description='Message text'),
    'notes': fields.String(required=False, attribute='notes', description='Message notes'),
    'checked': fields.Boolean(required=False, attribute='checked', description='Message checked'),
    'checked_date': fields.Date(required=False, attribute='checked_date', description='Messaged check date'),
    'closed': fields.Boolean(required=False, attribute='closed', description='Message closed'),
    'closed_date': fields.Date(required=False, attribute='closed_date', description='Messaged close date'),
    # 'status': Json(attribute=lambda x: get_notification_status(x), description='Message status'),
    'status': NotificationStatus(),
    'files': NotificationFiles()
})


page_notification = api.inherit('Notification pages', pagination, {
    'items': fields.List(fields.Nested(notification_api_model))
})
